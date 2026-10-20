"""Testes da maquinaria de patch (montar, injetar, cabecalho).

Todos usam imagens sinteticas: o que se testa aqui e' a guarda, nao o jogo.
Cada caso corresponde a um defeito que aconteceu de verdade durante o
desenvolvimento:

* escolher o primeiro trecho de 0xFF achou 81 bytes de padding no meio da
  imagem (0x081BA4E6) -- escrever ali corromperia dado;
* a formula do complemento do cabecalho estava errada no projeto (somava
  0x00..0xBC em vez de 0xA0..0xBC) e reprovava uma ROM valida;
* aplicar patch sem conferir o byte esperado nao distingue "nao fez nada" de
  "corrompeu".
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from gbadecomp import patch, rom  # noqa: E402


def _imagem(tamanho: int = 0x2000) -> bytearray:
    """Imagem sintetica: cabecalho plausivel + preenchimento 0x00."""
    dados = bytearray(tamanho)
    # cabecalho inteiro preenchido: com 0x00..0xA0 zerado as duas formulas do
    # complemento coincidem, e o teste da formula errada nao provaria nada
    dados[0x00:0xBD] = bytes(range(0xBD))
    dados[0xB2] = 0
    dados[0xBE:0xC0] = b"BP"
    return dados


def test_complemento_usa_a_formula_oficial():
    dados = _imagem()
    soma = sum(dados[0xA0:0xBD]) & 0xFF
    assert patch.complemento_correto(bytes(dados)) == (0x100 - (soma + 0x19)) & 0xFF


def test_corrigir_cabecalho_muda_so_o_byte_0xbd():
    dados = _imagem()
    dados[0xBD] = 0x00
    saida = patch.corrigir_cabecalho(bytes(dados))
    assert saida[0xBD] == patch.complemento_correto(bytes(dados))
    assert saida[:0xBD] == bytes(dados[:0xBD])
    assert saida[0xBE:] == bytes(dados[0xBE:])


def test_patch_recusa_tamanhos_diferentes():
    with pytest.raises(patch.ErroDePatch, match="mesmo tanto"):
        patch.Patch(0x08000000, b"\x00\x00", b"\x00", "motivo")


def test_patch_recusa_motivo_vazio():
    with pytest.raises(patch.ErroDePatch, match="sem motivo"):
        patch.Patch(0x08000000, b"\x00", b"\x01", "   ")


def test_aplicar_recusa_esperado_divergente_e_nao_escreve_nada():
    dados = bytes(_imagem())
    bom = patch.Patch(rom.to_addr(0x100), b"\x00\x00", b"\xAA\xBB", "teste")
    ruim = patch.Patch(rom.to_addr(0x200), b"\x99", b"\xCC", "esperado errado")
    with pytest.raises(patch.ErroDePatch, match="ROM diferente ou patch ja"):
        patch.aplicar(dados, [bom, ruim])
    assert dados[0x100:0x102] == b"\x00\x00"  # o primeiro nao foi aplicado


def test_aplicar_grava_quando_o_esperado_confere():
    dados = bytes(_imagem())
    saida = patch.aplicar(
        dados, [patch.Patch(rom.to_addr(0x100), b"\x00\x00", b"\xAA\xBB", "teste")])
    assert saida[0x100:0x102] == b"\xAA\xBB"
    assert len(saida) == len(dados)


def test_espaco_livre_ignora_padding_pequeno():
    """81 bytes de 0xFF no meio nao sao espaco livre -- regressao real."""
    dados = _imagem(0x4000)
    dados[0x1000:0x1000 + 81] = b"\xFF" * 81
    with pytest.raises(patch.ErroDePatch, match="pelo menos"):
        patch.achar_espaco_livre(bytes(dados), 16)


def test_espaco_livre_acha_o_primeiro_trecho_grande_e_alinhado():
    dados = _imagem(0x4000)
    dados[0x1000:0x1000 + 0x2000] = b"\xFF" * 0x2000
    endereco = patch.achar_espaco_livre(bytes(dados), 16)
    assert endereco == rom.to_addr(0x1000)
    assert (endereco - rom.ROM_BASE) % 2 == 0


def test_espaco_livre_respeita_alinhamento():
    dados = _imagem(0x4000)
    dados[0x1001:0x3001] = b"\xFF" * 0x2000
    endereco = patch.achar_espaco_livre(bytes(dados), 16, alinhamento=4)
    assert (endereco - rom.ROM_BASE) % 4 == 0


def test_montar_thumb_depende_do_endereco():
    """`bl` e' relativo: o mesmo texto montado para outro endereco muda de byte."""
    perto = patch.montar_thumb("bl 0x0809A2DC", 0x08054B06)
    longe = patch.montar_thumb("bl 0x0809A2DC", 0x08700000)
    assert perto != longe
    assert len(perto) == len(longe) == 4


def test_montar_thumb_recusa_codigo_invalido():
    with pytest.raises(patch.ErroDePatch, match="assembler recusou"):
        patch.montar_thumb("isto nao e' instrucao", 0x08000000)


def test_to_addr_e_to_offset_sao_inversos():
    assert rom.to_offset(rom.to_addr(0x1234)) == 0x1234
    assert rom.to_addr(0) == rom.ROM_BASE


def test_patch_de_verdade_na_imagem_sintetica_troca_um_bl():
    """Fecha o ciclo: montar salto, injetar, reler e decodificar de volta."""
    import capstone

    dados = _imagem(0x4000)
    dados[0x1000:0x3000] = b"\xFF" * 0x2000
    stub = patch.achar_espaco_livre(bytes(dados), 16)
    codigo = patch.montar_thumb("movs r0, #1\nbx lr", stub)
    salto = patch.montar_thumb(f"bl 0x{stub:08X}", rom.to_addr(0x200))
    esperado_hook = bytes(dados[0x200:0x204])
    nova = patch.aplicar(bytes(dados), [
        patch.Patch(rom.to_addr(0x200), esperado_hook, salto, "hook"),
        patch.Patch(stub, b"\xff" * len(codigo), codigo, "stub"),
    ])

    decodificador = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    instrucao = next(decodificador.disasm(nova[0x200:0x204], rom.to_addr(0x200)))
    assert instrucao.mnemonic == "bl"
    assert f"#0x{stub:x}" in instrucao.op_str.lower()


def test_cabecalho_da_rom_real_era_valido_e_o_projeto_reprovava():
    """A formula antiga (0x00..0xBC) reprovava; a oficial aprova."""
    dados = _imagem()
    dados[0xBD] = 0x00
    dados[0xBD] = patch.complemento_correto(bytes(dados))
    assert patch.complemento_correto(bytes(dados)) == dados[0xBD]
    soma_errada = sum(dados[0x00:0xBD]) & 0xFF
    assert (0x100 - (soma_errada + 0x19)) & 0xFF != dados[0xBD]


# --- manifesto declarativo -------------------------------------------------

def test_manifesto_aceita_hex_com_espaco_sem_espaco_e_lista():
    manifesto = {"patches": [
        {"endereco": "0x08000010", "esperado": "c8 00", "novo": "01 00", "motivo": "a"},
        {"endereco": 0x08000020, "esperado": "c800", "novo": [1, 0], "motivo": "b"},
        {"endereco": 0x08000030, "esperado": "0xc8 0x00", "novo": "0x01 0x00", "motivo": "c"},
    ]}
    patches = patch.patches_de_manifesto(manifesto)
    assert [p.esperado for p in patches] == [b"\xc8\x00"] * 3
    assert [p.novo for p in patches] == [b"\x01\x00"] * 3


def test_manifesto_recusa_sobreposicao():
    manifesto = {"patches": [
        {"endereco": 0x08000000, "esperado": "0102", "novo": "0304", "motivo": "a"},
        {"endereco": 0x08000001, "esperado": "05", "novo": "06", "motivo": "b"},
    ]}
    with pytest.raises(patch.ErroDePatch, match="sobrepostos"):
        patch.patches_de_manifesto(manifesto)


def test_manifesto_recusa_campo_faltando():
    with pytest.raises(patch.ErroDePatch, match="motivo"):
        patch.patches_de_manifesto({"patches": [
            {"endereco": 0x08000000, "esperado": "01", "novo": "02"}]})
    with pytest.raises(patch.ErroDePatch, match="patches"):
        patch.patches_de_manifesto({})


def test_manifesto_aplica_e_recalcula_o_cabecalho():
    dados = bytearray(_imagem())
    dados[0xBD] = 0x00
    manifesto = {"patches": [
        {"endereco": rom.to_addr(0x100), "esperado": "0000",
         "novo": "c800", "motivo": "preco"}]}
    nova, patches = patch.aplicar_manifesto(bytes(dados), manifesto)
    assert nova[0x100:0x102] == b"\xc8\x00"
    assert nova[0xBD] == patch.complemento_correto(bytes(dados))
    assert len(patches) == 1


# --- montar_thumb_literais: o bug do pool de literais do keystone ---------
#
# Historia, porque o teste sozinho nao conta: o keystone 0.9.2 monta
# `ldr rX, =VALOR` com o deslocamento errado quando ha' mais de um literal no
# mesmo bloco. O primeiro aponta certo e do segundo em diante o `ldr` carrega
# o valor do literal SEGUINTE. Isso nao da' erro de montagem, o `bl` do hook
# aponta certo, a ROM boota -- e o stub escreve no lugar errado. Foi assim que
# um contador de depuracao marcou zero num ponto que rodava de fato.
#
# Por isso os testes abaixo desmontam o resultado em vez de comparar bytes:
# comparar com o que o proprio keystone produziria seria tautologico.

def _literal_carregado(codigo, endereco, indice_da_instrucao):
    """Valor que o `ldr rX, [pc, #N]` em `indice_da_instrucao` carrega."""
    metade = codigo[indice_da_instrucao] | (codigo[indice_da_instrucao + 1] << 8)
    assert (metade & 0xF800) == 0x4800, "nao e' ldr pc-relativo"
    base = (endereco + indice_da_instrucao + 4) & ~3
    alvo = base - endereco + (metade & 0xFF) * 4
    return int.from_bytes(codigo[alvo:alvo + 4], "little")


def test_montar_thumb_literais_um_literal():
    codigo = patch.montar_thumb_literais(
        "ldr r0, =0x02037F00\nbx lr\n", 0x0871A906)
    assert _literal_carregado(codigo, 0x0871A906, 0) == 0x02037F00


def test_montar_thumb_literais_varios_literais_cadam_um_no_seu():
    """O caso que o keystone erra: 3 literais no mesmo bloco."""
    codigo = patch.montar_thumb_literais(
        "push {r4, lr}\n"
        "ldr r0, =0x03005008\n"
        "ldr r1, =0x00000430\n"
        "ldr r2, =0x0300500C\n"
        "pop {r4, pc}\n", 0x0871A906)
    assert _literal_carregado(codigo, 0x0871A906, 2) == 0x03005008
    assert _literal_carregado(codigo, 0x0871A906, 4) == 0x00000430
    assert _literal_carregado(codigo, 0x0871A906, 6) == 0x0300500C


def test_montar_thumb_literais_endereco_impar_desloca_o_pool():
    """Stub em endereco 2-mod-4: o pool tem de ficar alinhado em 4 absoluto."""
    for base in (0x0871A906, 0x0871A908, 0x0871A90A):
        codigo = patch.montar_thumb_literais(
            "ldr r0, =0x02037F00\nldr r1, =0xCAFEBABE\nbx lr\n", base)
        assert _literal_carregado(codigo, base, 0) == 0x02037F00, hex(base)
        assert _literal_carregado(codigo, base, 2) == 0xCAFEBABE, hex(base)
        assert (base + len(codigo) - 8) % 4 == 0


def test_montar_thumb_literais_sem_literal_nao_muda_nada():
    puro = patch.montar_thumb("movs r0, #1\nbx lr", 0x0871A906)
    assert patch.montar_thumb_literais("movs r0, #1\nbx lr", 0x0871A906) == puro


def test_montar_thumb_literais_com_bl_preserva_o_desvio():
    """O `bl` de 4 bytes nao pode ser confundido com um marcador de literal."""
    codigo = patch.montar_thumb_literais(
        "push {r4, lr}\nbl 0x0809A2DC\nldr r0, =0x02037F00\n"
        "pop {r4, pc}\n", 0x0871A906)
    import capstone
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    saltos = [i for i in cs.disasm(codigo, 0x0871A906) if i.mnemonic == "bl"]
    assert len(saltos) == 1
    assert saltos[0].op_str == "#0x809a2dc"
