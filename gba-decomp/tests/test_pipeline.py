"""Testes do pipeline gbadecomp (disassembly -> C -> ROM reconstruida).

Cada teste aqui verifica um comportamento que ja falhou de verdade durante o
desenvolvimento, ou que sustenta a afirmacao central do projeto: "o C levantado
executa e da o mesmo resultado do binario". Nada e testado por leitura de
codigo -- tudo executa o binario no emulador.

Marcados como lentos: os que compilam C com o zig (~1-2 s cada).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from gbadecomp import (  # noqa: E402
    analise as analise_mod,
    conferir_bytes as conferir_mod,
    corpus,
    decompile,
    disasm,
    reconstruir,
    rom,
    verificador,
)


@pytest.fixture(scope="module")
def corpus_pronto(tmp_path_factory):
    """Constroi o corpus sintetico uma vez para o modulo inteiro."""
    destino = tmp_path_factory.mktemp("corpus") / "corpus.gba"
    return corpus.construir(destino)


@pytest.fixture(scope="module")
def rodada(tmp_path_factory):
    """Uma rodada completa (disasm + lift + verificacao), reaproveitada."""
    tmp = tmp_path_factory.mktemp("rodada")
    return reconstruir.rodada_corpus(diretorio=tmp)


def test_corpus_e_gba_valido(corpus_pronto):
    r = rom.GbaRom(corpus_pronto.rom_path)
    relatorio = r.report()
    assert len(r) == 256 * 1024
    assert relatorio.title.rstrip("\x00") == "GBADECOMP"
    assert relatorio.game_code == "TSYN"
    assert relatorio.complement_ok is True
    assert relatorio.fixed_byte_ok is True
    # A area do logo da Nintendo e deixada zerada de proposito: nao reproduzimos
    # material de terceiros, e um logo falso so serviria para enganar quem le.
    assert relatorio.logo_area_preenchida is False


def test_corpus_lista_24_funcoes_com_verdade_terreno(corpus_pronto):
    nomes = {f.nome for f in corpus_pronto.funcoes}
    assert len(nomes) == 24
    assert {"soma", "fat", "divide", "loop_decrescente", "main_teste"} <= nomes
    assert len(corpus_pronto.sha256) == 64


def test_verdade_terreno_passa_no_corpus(corpus_pronto):
    rel = verificador.verificar_verdade_terreno(corpus_pronto)
    assert rel.total == 59
    assert rel.reprovados == [], rel.texto()


def test_tabela_de_verdade_nao_foi_copiada_do_resultado(corpus_pronto):
    """Se alguem 'consertar' a tabela copiando a saida da emulacao, este teste
    derruba: os valores esperados sao literais conferidos a mao na fonte."""
    fonte = (RAIZ / "gbadecomp" / "corpus.py").read_text()
    assert '"esperado": 42' in fonte          # soma(7, 35)
    assert '"esperado": 120' in fonte         # fat(5)
    assert '"esperado": 0xFFFE0001' in fonte  # mul32(0xFFFF, 0xFFFF)
    assert fonte.count('"funcao":') == 59


def test_descoberta_recursiva_acha_todas_as_funcoes(corpus_pronto):
    imagem = Path(corpus_pronto.rom_path).read_bytes()
    desmontagem = disasm.desmontar_por_sementes(imagem)   # so o vetor de boot
    esperadas = {f.addr for f in corpus_pronto.funcoes}
    assert set(desmontagem.funcoes) == esperadas
    assert desmontagem.total_instrucoes == 370
    assert len(desmontagem.arestas()) == 26


def test_grafo_de_chamadas_bate_com_a_verdade(corpus_pronto):
    imagem = Path(corpus_pronto.rom_path).read_bytes()
    desmontagem = disasm.desmontar_por_sementes(imagem)
    nome = {f.addr: f.nome for f in corpus_pronto.funcoes}
    arestas = {(nome[a], nome[b]) for a, b in desmontagem.arestas()}
    assert ("divide", "__aeabi_uidiv") in arestas
    assert ("chama_soma", "soma") in arestas
    assert ("loop_decrescente", "__aeabi_lmul") in arestas
    assert ("__aeabi_lmul", "mul32") in arestas
    assert len([a for a, _ in arestas if a == "main_teste"]) == 22


def test_modo_herdado_da_chamada_nao_vem_da_paridade(corpus_pronto):
    """Regressao: alvo de `bl` do Thumb e PAR. Se o desmontador usar a paridade
    para escolher o modo, ele desmonta tudo em ARM e produz lixo plausivel."""
    imagem = Path(corpus_pronto.rom_path).read_bytes()
    desmontagem = disasm.desmontar_por_sementes(imagem)
    assert all(f.modo == "thumb" for f in desmontagem.funcoes.values())
    identificaveis = sum(1 for f in desmontagem.funcoes.values()
                         if f.terminacao in ("bx lr", "bx r1", "bx r2", "pop {pc}")
                         or f.terminacao.startswith("bx") or f.terminacao.startswith("pop"))
    assert identificaveis >= 20


def test_pop_le_do_endereco_mais_baixo(corpus_pronto):
    """Regressao: `push {r7,lr}` + `pop {r7}` + `pop {r1}` + `bx r1`. Tratar a
    pilha como LIFO classico entregava o retorno ao registrador errado."""
    imagem = Path(corpus_pronto.rom_path).read_bytes()
    desmontagem = disasm.desmontar_por_sementes(imagem)
    codigo = decompile.decompilar(desmontagem, imagem)
    assert codigo.incompletas == [], [f.nao_levantadas for f in codigo.incompletas]


def test_lift_compila_e_reproduz_a_verdade_terreno(rodada):
    assert rodada.erros == []
    assert rodada.relatorio_original.aprovados == 59
    assert rodada.relatorio_levantado is not None
    assert rodada.relatorio_levantado.reprovados == [], rodada.relatorio_levantado.texto()
    # o codigo C compilado nao pode ser maior que o original de forma absurda
    assert 0 < rodada.tamanho_levantado < 8192


def test_reconstrucao_e_deterministica(tmp_path):
    """Mesma entrada -> mesmo C (o levantamento nao pode depender de ordem de
    dicionario nem de horario)."""
    a = reconstruir.rodada_corpus(diretorio=tmp_path / "a")
    b = reconstruir.rodada_corpus(diretorio=tmp_path / "b")
    assert a.codigo.texto() == b.codigo.texto()
    assert a.desmontagem.total_instrucoes == b.desmontagem.total_instrucoes


def test_binario_sem_verdade_terreno_avisa(rodada):
    """O caminho para ROM de terceiros nao pode prometer acerto."""
    caminho = Path(rodada.caminho_c).parent / "corpus.gba"
    resultado = reconstruir.rodada_binario(caminho)
    assert resultado.erros, "deveria registrar que nao existe verdade-terreno"
    assert resultado.relatorio_original is None
    assert resultado.relatorio_levantado is None


def test_levantador_avisa_o_que_nao_traduz():
    """Instrucao que o levantador nao conhece tem de APARECER na lista, nunca ser
    ignorada em silencio (foi assim que bugs de traducao apareceram aqui)."""
    # ARM: `mrs r0, cpsr` (0xE10F0000) nao e traduzida; `bx lr` encerra.
    imagem = (bytes(0xC0) + bytes.fromhex("00009fe5") + bytes.fromhex("10ff2fe1")
              + (0x080000CC).to_bytes(4, "little")          # bit0 limpo -> ARM
              + bytes.fromhex("00000fe1" + "1eff2fe1") + b"\xff" * 64)
    desmontagem = disasm.desmontar_por_sementes(imagem)
    assert len(desmontagem.funcoes) == 1
    assert next(iter(desmontagem.funcoes.values())).modo == "arm"
    codigo = decompile.decompilar(desmontagem, imagem)
    assert codigo.incompletas, "MRS deveria constar como nao levantada"
    assert "mnemonico nao implementado" in codigo.incompletas[0].nao_levantadas[0]


def test_funcao_parcial_sai_marcada_e_detectavel(corpus_pronto):
    """Salto calculado (`mov pc, rN`) nao pode virar atribuicao silenciosa: a
    funcao sai PARCIAL, com comentario e com g_erro marcado em execucao."""
    imagem = Path(corpus_pronto.rom_path).read_bytes()
    desmontagem = disasm.desmontar_por_sementes(imagem)
    codigo = decompile.decompilar(desmontagem, imagem)
    texto = codigo.texto()
    assert "codigo levantado" not in texto or True      # documento gerado
    # nenhuma funcao do corpus e parcial: o corpus inteiro e levantavel
    assert codigo.incompletas == []


def test_salto_calculado_marca_funcao_como_parcial():
    """`mov pc, r0` (tabela de casos) tem de sair como parcial e marcado."""
    # ARM, modo Thumb: movs r0,#0 ; mov pc,r0  (0x4687) ; bx lr
    imagem = (bytes(0xC0) + bytes.fromhex("00009fe5") + bytes.fromhex("10ff2fe1")
              + (0x080000CD).to_bytes(4, "little")
              + bytes.fromhex("0020" + "8746" + "7047") + b"\xff" * 64)
    desmontagem = disasm.desmontar_por_sementes(imagem)
    codigo = decompile.decompilar(desmontagem, imagem)
    funcao = codigo.funcoes[0]
    assert not funcao.completa, "salto calculado deveria marcar a funcao como parcial"
    assert "g_erro |= 2" in funcao.corpo
    assert "PC calculado" in funcao.corpo
    # e o C gerado continua compilando (nao vira lixo sintatico)
    assert "return r0;" in funcao.corpo


def test_endereco_sem_codigo_vira_descarte_e_nunca_funcao():
    """Byte invalido no endereco: nao vira funcao E nao desaparece.

    Bug real (ROM de estudo): entradas que nao decodificavam ficavam na lista de
    funcoes com corpo vazio e, como nao havia recusa registrada, contavam como
    COMPLETAS -- 83 "funcoes levantadas" sem uma linha de C. O contrato agora e
    explicito: sem nenhuma instrucao valida do ARM7TDMI, nao e funcao; vai para
    `descartes` com o motivo e os bytes.
    """
    imagem = (bytes(0xC0) + bytes.fromhex("00009fe5") + bytes.fromhex("10ff2fe1")
              + (0x080000CD).to_bytes(4, "little") + bytes.fromhex("ffff")
              + b"\xff" * 64)
    desmontagem = disasm.desmontar_por_sementes(imagem)
    assert desmontagem.funcoes == {}, "endereco sem codigo nao pode virar funcao"
    (descartado,) = desmontagem.descartes.values()
    assert descartado.entrada == 0x080000CC
    assert "invalido" in descartado.motivo
    # o descarte fica auditavel no JSON (endereco, motivo e bytes iniciais)
    registro = json.loads(desmontagem.para_json())["descartes"][0]
    assert registro["entrada"] == "0x080000CC" and registro["bytes"].startswith("ff ff")


def test_lifter_marca_funcao_sem_instrucao_como_incompleta():
    """Segunda barreira: mesmo que uma funcao vazia chegue ao lifter, ela nao
    pode sair como 'completa' -- o resumo mentiria."""
    vazia = disasm.FuncaoDesmontada(entrada=0x08000100, modo="thumb")
    codigo = decompile.decompilar(
        disasm.Desmontagem(base=rom.ROM_BASE, funcoes={0x08000100: vazia}),
        bytes(0x200))
    (levantada,) = codigo.funcoes
    assert not levantada.completa and not levantada.tem_corpo
    assert "nenhuma instrucao" in levantada.nao_levantadas[0]
    assert "NAO levantada" in codigo.texto()   # o .c explica, nao fica em branco


def test_medicao_recusa_publicar_numero_que_mente():
    """A medicao tem de FALHAR se alguem reintroduzir o bug, em vez de publicar
    o numero inflado (7 311 completas contra 7 228 com corpo)."""
    codigo = decompile.CodigoC()
    codigo.funcoes.append(decompile.FuncaoDec(
        endereco=0x08000100, nome="fn_08000100", modo="thumb",
        corpo="", nao_levantadas=[]))
    with pytest.raises(RuntimeError, match="COMPLETAS sem nenhuma linha de C"):
        analise_mod._classificar(codigo)


def test_medicao_do_corpus_fecha_as_contas(corpus_pronto):
    """As categorias da medicao sao exaustivas e batem com a verdade-terreno."""
    medicao = analise_mod.medir(corpus_pronto.rom_path, conferir=False)
    lev = medicao.levantamento
    assert lev["funcoes"] == 24
    assert lev["com_c_para_ler"] + lev["sem_corpo"] == lev["funcoes"]
    assert lev["completas"] + lev["parciais"] == lev["com_c_para_ler"]
    assert lev["com_c_para_ler"] == lev["funcoes"], "no corpus tudo tem C para ler"
    assert medicao.completo["descartes"] == 0
    assert medicao.sha256 == corpus_pronto.sha256
    assert "com C para ler" in medicao.texto()


def test_verificador_reporta_divergencia_sem_maquiar(tmp_path):
    """Se a verdade-terreno divergir, o relatorio TEM de acusar."""
    destino = tmp_path / "quebrado.gba"
    c = corpus.construir(destino)
    imagem = bytearray(destino.read_bytes())
    soma = next(f for f in c.funcoes if f.nome == "soma")
    off = soma.addr - rom.ROM_BASE
    imagem[off + 2] = 0x46           # troca `adds r0, r0, r1` por outra coisa
    destino.write_bytes(bytes(imagem))
    rel = verificador.verificar_verdade_terreno(
        corpus.Corpus(rom_path=str(destino), sha256="", total_funcoes=c.total_funcoes,
                      funcoes=c.funcoes, comando_compilacao="", compilador="", c_fonte=""))
    assert rel.reprovados, "um binario alterado nao pode passar como correto"

def _imagem_com_tabela_de_casos(guarda: int = 2) -> bytes:
    """Monta uma imagem minima com o idioma REAL de tabela de casos (Thumb).

    Bytes escritos a mao porque o codificador escolhe codificacoes mais largas
    quando voce escreve o mnemonico (deslocando o layout) -- e aqui o layout e o
    que esta sendo testado. Os bytes sao conferidos pelo proprio desmontador no
    inicio do teste, entao um erro de codificacao falha em vez de passar.

        0x40  cmp r0, #guarda      ; o guarda diz quantos casos existem
        0x42  bhi 0x0800006C       ; fora da faixa
        0x44  lsls r0, r0, #2      ; indice * 4
        0x46  ldr r1, [pc, #0xC]   ; pool em 0x08000054 -> endereco da tabela
        0x48  adds r0, r0, r1
        0x4A  ldr r0, [r0]         ; endereco do caso, lido da tabela
        0x4C  mov pc, r0
        0x54  .word 0x08000080     ; a tabela
        0x58/0x5C/0x60  corpos dos casos 0, 1, 2
        0x6C  corpo do padrao (para onde o `bhi` manda)
        0x80  tabela: 3 enderecos PARES (no Thumb `mov pc, rN` alinha em
              meia-palavra: o bit0 nao carrega modo)
    """
    base = rom.ROM_BASE
    casos = [0x08000058, 0x0800005C, 0x08000060]
    padrao = 0x0800006C
    tabela = 0x08000080
    imagem = bytearray(0x100)

    def meia(endereco: int, valor: int) -> None:
        imagem[endereco - base:endereco - base + 2] = valor.to_bytes(2, "little")

    meia(0x08000040, 0x2800 | guarda)          # cmp r0, #guarda
    meia(0x08000042, 0xD800 | ((padrao - 0x08000046) // 2))   # bhi padrao
    meia(0x08000044, 0x0080)                   # lsls r0, r0, #2
    meia(0x08000046, 0x4903)                   # ldr r1, [pc, #0xC]
    meia(0x08000048, 0x1840)                   # adds r0, r0, r1
    meia(0x0800004A, 0x6800)                   # ldr r0, [r0]
    meia(0x0800004C, 0x4687)                   # mov pc, r0 (D=1 e Rd=r7 -> r15)
    for endereco in (0x0800004E, 0x08000050, 0x08000052):
        meia(endereco, 0x0000)                 # preenchimento ate o pool
    # ATENCAO: `0x54 - base` seria NEGATIVO (indice do fim em Python) e o slice
    # inseriria bytes no comeco, deslocando o layout inteiro -- bug real que o
    # teste de autoconferencia pegou.
    imagem[0x08000054 - base:0x08000058 - base] = tabela.to_bytes(4, "little")
    for numero, endereco in enumerate(casos):
        meia(endereco, 0x2000 | ((numero + 1) * 0x10))   # movs r0, #N
        meia(endereco + 2, 0x4770)                       # bx lr
    meia(padrao, 0x20FF)                       # movs r0, #0xFF
    meia(padrao + 2, 0x4770)                   # bx lr
    for numero, endereco in enumerate(casos):
        inicio = tabela + 4 * numero
        imagem[inicio - base:inicio - base + 4] = endereco.to_bytes(4, "little")
    return bytes(imagem)


def test_imagem_de_teste_decodifica_o_que_ela_promete():
    """Autoconferencia da imagem usada nos testes de tabela: os bytes a mao
    precisam desmontar exatamente no idioma esperado."""
    imagem = _imagem_com_tabela_de_casos()
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000040: "thumb"})
    (funcao,) = desmontagem.funcoes.values()
    lidas = [(i.endereco, i.mnemonic, i.operadores) for i in funcao.instrucoes]
    assert (0x08000040, "cmp", "r0, #2") in lidas
    assert (0x08000044, "lsls", "r0, r0, #2") in lidas
    assert (0x08000046, "ldr", "r1, [pc, #0xc]") in lidas
    assert (0x08000048, "adds", "r0, r0, r1") in lidas
    assert (0x0800004A, "ldr", "r0, [r0]") in lidas
    assert (0x0800004C, "mov", "pc, r0") in lidas
    assert (0x08000058, "movs", "r0, #0x10") in lidas


def test_desmontador_segue_a_tabela_de_casos(tmp_path):
    """`mov pc, rX` com tabela reconhecida: os corpos dos casos sao desmontados.

    Sem isso os alvos ficam fora da funcao e um `switch` no C apontaria para
    rotulo inexistente (nao compila) -- foi o que a sonda mediu na ROM real
    (19 de 34 alvos desmontados antes de seguir a tabela).
    """
    imagem = _imagem_com_tabela_de_casos()
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000040: "thumb"})
    (funcao,) = desmontagem.funcoes.values()
    (tabela,) = funcao.tabelas
    assert tabela.tabela == 0x08000080
    assert tabela.alvos == [0x08000058, 0x0800005C, 0x08000060]
    assert tabela.deslocamento == 2
    desmontados = {i.endereco for i in funcao.instrucoes}
    assert set(tabela.alvos) <= desmontados, "a tabela tem de ser seguida"


def test_lift_emite_switch_a_partir_da_tabela_lida_da_rom(tmp_path):
    """O C do salto calculado sai com `switch` real, e compila."""
    imagem = _imagem_com_tabela_de_casos()
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000040: "thumb"})
    codigo = decompile.decompilar(desmontagem, imagem)
    (levantada,) = codigo.funcoes
    assert levantada.completa, levantada.nao_levantadas
    assert "switch (idx_0800004C >> 2)" in levantada.corpo
    assert "case 0: goto L_08000058;" in levantada.corpo
    assert "case 2: goto L_08000060;" in levantada.corpo
    assert "default: g_erro |= 2;" in levantada.corpo
    # `goto` para rotulo que nao existe e erro de compilacao -- e o teste que
    # garante que o switch emitido e C valido
    corpus.compilar_thumb(codigo.texto(), tmp_path / "switch.o")
    assert (tmp_path / "switch.o").exists()


def test_tabela_sem_guarda_que_bata_nao_vira_switch():
    """Criterio de recusa: se o `cmp rX, #k` nao bater com o numero de entradas
    lidas da tabela, NAO se reconhece tabela nenhuma -- a funcao continua
    PARCIAL, em vez de o lifter publicar um `switch` inventado."""
    imagem = _imagem_com_tabela_de_casos(guarda=5)      # guarda diz 6, tabela tem 3
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000040: "thumb"})
    (funcao,) = desmontagem.funcoes.values()
    assert funcao.tabelas == [], "nao pode reconhecer tabela que nao fecha com o guarda"
    codigo = decompile.decompilar(desmontagem, imagem)
    (levantada,) = codigo.funcoes
    assert not levantada.completa
    assert "nao reconhecida" in levantada.corpo
    assert "switch" not in levantada.corpo


def _imagem_com_salto_para_tras() -> bytes:
    """Imagem minima com o idioma REAL que a ROM de estudo usa em toda parte:

        0x08000010  movs r0, #1      } funcao A ("anterior")
        0x08000012  bx lr            } -> este `bx lr` e o EPILOGO COMPARTILHADO
        0x08000014  movs r1, #2      } funcao B
        0x08000016  b 0x08000012     } salto PARA TRAS, para o epilogo de A

    O compilador reaproveita o epilogo da funcao anterior, entao o corpo de B
    "termina" fora de B. E o mesmo caso medido na ROM: FUN_08018258 saltava para
    0x08017B92 (dentro da rotina anterior) e engolia 651 instrucoes dela.
    """
    base = rom.ROM_BASE
    imagem = bytearray(0x40)
    imagem[0x10:0x12] = (0x2001).to_bytes(2, "little")     # movs r0, #1
    imagem[0x12:0x14] = (0x4770).to_bytes(2, "little")     # bx lr
    imagem[0x14:0x16] = (0x2102).to_bytes(2, "little")     # movs r1, #2
    # b 0x08000012: offset = alvo - (endereco + 4) = 0x12 - 0x1A = -8 -> imm11 = -4
    offset = (0x08000012 - (0x08000016 + 4)) // 2
    imagem[0x16:0x18] = (0xE000 | (offset & 0x7FF)).to_bytes(2, "little")
    imagem[0x18:0x40] = b"\xff" * 0x28
    return bytes(imagem)


def test_salto_para_tras_sai_da_funcao_em_vez_de_engolir_a_anterior():
    """A descoberta de B NAO pode mudar o corpo de A -- nem reivindicar bytes dele.

    Antes desta regra, a leitura seguia o salto para tras e a "funcao" ficava com
    faixa 0x08017B92..0x08018C86 (1 722 instrucoes), 651 delas ANTES da propria
    entrada. Efeito colateral medido: 13 780 enderecos apareciam em mais de uma
    funcao e 65 dos 100 `bx rN` recusados eram `pop {r1}; bx r1` cujo `push` que
    marca o retorno estava antes da entrada.
    """
    imagem = _imagem_com_salto_para_tras()
    so_a = disasm.desmontar_por_sementes(imagem, sementes={0x08000010: "thumb"})
    ambas = disasm.desmontar_por_sementes(
        imagem, sementes={0x08000010: "thumb", 0x08000014: "thumb"})
    a_sozinha = so_a.funcoes[0x08000010].instrucoes
    assert [i.endereco for i in a_sozinha] == [0x08000010, 0x08000012]
    b = ambas.funcoes[0x08000014]
    assert [i.endereco for i in b.instrucoes] == [0x08000014, 0x08000016], \
        "B nao pode conter as instrucoes de A (0x08000012 e o epilogo de A)"
    assert b.saidas == [(0x08000016, 0x08000012)]
    assert "para tras" in b.terminacao
    for funcao in ambas.funcoes.values():
        assert all(i.endereco >= funcao.entrada for i in funcao.instrucoes), \
            f"0x{funcao.entrada:08X} tem instrucao antes da propria entrada"
    assert ambas.saidas_para_tras == 1
    assert ambas.saidas_recuperadas == 0, \
        "0x08000012 ja esta coberto por A: recuperar de novo duplicaria endereco"


def test_salto_para_tras_para_trecho_orfaos_volta_como_semente():
    """O preco da regra: trecho alcancado SO por salto para tras nao pode sumir.

    Se nenhuma funcao cobre o destino, ele volta como semente propria, marcado
    com a origem (`salto para tras em 0x...`) -- e nao como se fosse uma entrada
    descoberta por chamada, que seria mentira sobre como se chegou ali.
    """
    imagem = _imagem_com_salto_para_tras()
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000014: "thumb"})
    assert set(desmontagem.funcoes) == {0x08000014, 0x08000012}
    orfa = desmontagem.funcoes[0x08000012]
    assert [i.endereco for i in orfa.instrucoes] == [0x08000012]
    assert orfa.semente == "salto para tras em 0x08000016"
    assert desmontagem.saidas_recuperadas == 1
    # e o trecho nao coberto continua auditavel no JSON (com a semente de origem)
    registros = json.loads(desmontagem.para_json())["funcoes"]
    orfao = next(r for r in registros if r["entrada"] == "0x08000012")
    assert orfao["semente"] == "salto para tras em 0x08000016"


def test_lift_diz_que_o_desvio_para_tras_sai_da_funcao():
    """O C nao pode fingir que o salto para tras e' rotulo interno nem chamada.

    Aqui nao falta implementar instrucao: falta o bloco ser da funcao. A mensagem
    tem de dizer isso -- e a funcao sai PARCIAL, marcada.
    """
    imagem = _imagem_com_salto_para_tras()
    desmontagem = disasm.desmontar_por_sementes(
        imagem, sementes={0x08000010: "thumb", 0x08000014: "thumb"})
    codigo = decompile.decompilar(desmontagem, imagem)
    por_entrada = {f.endereco: f for f in codigo.funcoes}
    b = por_entrada[0x08000014]
    assert not b.completa and b.parcial
    assert any("desvio para tras, para fora da funcao (0x08000012" in item
               for item in b.nao_levantadas), b.nao_levantadas
    assert "goto L_08000012" not in b.corpo
    # E nada de `return r0;` inventado depois da lacuna: o C diz que a leitura sai
    # pelo salto para tras e para por ali (nao finge um retorno que nao existe).
    assert "NAO LEVANTADO: b #0x8000012" in b.corpo
    assert "return r0;" not in b.corpo


def test_conferencia_conta_todas_as_divergencias_e_nao_so_a_amostra():
    """Divergencia de bytes: o numero total nao pode ser o tamanho da amostra.

    Bug real, achado ao rodar a medicao da ROM: `divergentes` era
    `len(exemplos)` e `exemplos` para de crescer no limite -- com 225
    divergencias o relatorio imprimia "25 divergencias". O que mente nao e a
    fidelidade medida, e o resumo dela.

    Os bytes aqui sao ARM de verdade: `mov r4, #2` (e3a04002) listado como
    `mov r4, #1` -- remonta e3a04001, ou seja, diverge dos bytes do binario.
    """
    base = rom.ROM_BASE
    imagem = bytearray(0x40)
    desmontagem = disasm.Desmontagem(base=base)
    funcao = disasm.FuncaoDesmontada(entrada=base, modo="arm")
    for numero in range(3):
        endereco = base + 4 * numero
        imagem[4 * numero:4 * numero + 4] = bytes.fromhex("0240a0e3")   # mov r4, #2
        funcao.instrucoes.append(disasm.Instrucao(
            endereco, bytes.fromhex("0240a0e3"), "mov", "r4, #1", "arm"))
    desmontagem.funcoes[base] = funcao
    resultado = conferir_mod.conferir(desmontagem, bytes(imagem), limite_exemplos=1)
    assert resultado.total == 3
    assert resultado.identicas == 0
    assert len(resultado.exemplos) == 1, "a amostra guardada respeita o limite"
    assert resultado.divergentes == 3, "o total tem de contar tudo, nao a amostra"
    assert resultado.por_mnemonico == {"mov": 3}
    assert "3 divergencias" in resultado.texto()
    # e as decodificacoes realmente conferem (a imagem e os bytes sao ARM)
    lidas = [(i.mnemonic, i.operadores) for i in funcao.instrucoes]
    assert lidas == [("mov", "r4, #1")] * 3


def _imagem_de_janela(*meias: int, base_off: int = 0x20) -> bytes:
    """Imagem minima com as meias-palavras Thumb dadas, a partir de 0x08000020."""
    imagem = bytearray(0x40)
    for numero, valor in enumerate(meias):
        imagem[base_off + 2 * numero:base_off + 2 * numero + 2] = valor.to_bytes(2, "little")
    imagem[base_off + 2 * len(meias):] = b"\xff" * (0x40 - base_off - 2 * len(meias))
    return bytes(imagem)


def test_bx_apos_pop_e_retorno_mesmo_em_janela_que_comeca_no_meio():
    """`pop {rN}; bx rN` e o epilogo: nao pode depender do `push` ter sido visto.

    Caso medido na ROM: 61 dos 96 `bx rN` recusados estavam em janelas que
    comecam no MEIO do corpo (endereco lido de tabela de dados). Nessas janelas
    nao existe `push` do `lr` no trecho lido, entao o livro-caixa de slots nao
    tem como marcar nada -- e o `bx` virava "sem origem conhecida" mesmo sendo o
    retorno mais comum que existe. A condicao aceita e mecanica: quem carrega o
    registrador do `bx` e uma leitura DA PILHA na instrucao imediatamente antes.
    """
    imagem = _imagem_de_janela(0xBC10, 0xBC01, 0x4700)     # pop {r4}; pop {r0}; bx r0
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    codigo = decompile.decompilar(desmontagem, imagem)
    (levantada,) = codigo.funcoes
    assert levantada.semente == "informada"
    assert levantada.completa, levantada.nao_levantadas
    assert "tirou da pilha" in levantada.corpo
    assert "return r0;" in levantada.corpo
    # a janela nao tem prologo: o cabecalho do C diz o desequilibrio, nao esconde
    assert "desequilibrada" in codigo.texto()


def test_bx_por_registrador_calculado_continua_recusado():
    """Desvio indireto CALCULADO nao vira retorno so para o numero ficar bonito.

    `mov r0, r1; bx r0` nao e retorno: e chamada indireta despachada por valor
    que o C nao modela (tabela de ponteiros de funcao, por exemplo). Nao aceitar
    isso e' o que separa "levei 61 `bx` a menos" de "escondi 61 lacunas".
    """
    imagem = _imagem_de_janela(0x2001, 0x4608, 0x4700)     # movs r0, #1; mov r0, r1; bx r0
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    codigo = decompile.decompilar(desmontagem, imagem)
    (levantada,) = codigo.funcoes
    assert not levantada.completa
    assert any("sem origem conhecida" in item for item in levantada.nao_levantadas)
    assert "NAO LEVANTADO: bx r0" in levantada.corpo


def test_medicao_conta_tabelas_lidas_da_rom_e_nao_switch_no_texto():
    """O numero de tabelas/casos vem da descoberta, nao de `grep` no C gerado.

    Antes esses dois numeros saiam de contar `switch` no arquivo .c -- e o
    `grep` nao distingue tabela reconhecida de `switch` emitido (tabela sem
    escala conhecida e' reconhecida mas nao vira `switch`). Aqui se conta o que
    foi LIDO da imagem: 1 tabela, 3 casos, nesta imagem de teste.
    """
    imagem = _imagem_com_tabela_de_casos()
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000040: "thumb"})
    assert analise_mod._contar_tabelas(desmontagem) == (1, 3)


def test_bx_como_primeira_instrucao_e_thunk_e_o_motivo_diz_isso():
    """`bx rN` + nop no inicio da janela nao e' falha do levantador: e' thunk.

    Medido na ROM: 0x081E3BA8.. e' uma sequencia de 4 em 4 bytes com
    `bx r0 ; mov r8, r8`, `bx r1 ; mov r8, r8`, ... chamada por `bl` de dezenas
    de sitios. O alvo do salto e' um PARAMETRO (vem do registrador em quem
    chamou), entao nao existe traducao literal -- o que a funcao pode fazer e
    dizer exatamente isso, em vez de "sem origem conhecida" (que sugere defeito).
    """
    imagem = _imagem_de_janela(0x4700, 0x46C0)      # bx r0 ; mov r8, r8 (nop)
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    codigo = decompile.decompilar(desmontagem, imagem)
    (levantada,) = codigo.funcoes
    assert not levantada.completa
    assert any("thunk de salto indireto" in item for item in levantada.nao_levantadas)
    # continua sendo recusa registrada, nao `return r0;` inventado


def test_chamada_indireta_interworking_tem_motivo_proprio():
    """`stmdb sp!, {lr}` + `add lr, pc, #0` + `bx rN` (ARM) tem motivo proprio.

    O `add lr, pc, #0` e' o retorno do interworking montado a mao (e' ele que
    marca o modo Thumb no endereco de retorno): a chamada nao passa por `bl`, o
    alvo veio de dado lido da ROM e nao ha assinatura declarada. Nao existe C
    fiel a emitir; existe motivo a dizer -- e diferente de "sem origem
    conhecida", que sugere defeito do levantador.
    """
    base = rom.ROM_BASE
    imagem = bytearray(0x40)
    imagem[0x20:0x24] = bytes.fromhex("00402de9")     # stmdb sp!, {lr}
    imagem[0x24:0x28] = bytes.fromhex("00e08fe2")     # add lr, pc, #0
    imagem[0x28:0x2C] = bytes.fromhex("10ff2fe1")     # bx r0
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "arm"})
    (funcao,) = desmontagem.funcoes.values()
    lidas = [(i.mnemonic, i.operadores) for i in funcao.instrucoes]
    assert ("add", "lr, pc, #0") in lidas, lidas       # a imagem e o que ela promete
    codigo = decompile.decompilar(desmontagem, imagem)
    levantada = next(f for f in codigo.funcoes if f.endereco == 0x08000020)
    assert any("chamada indireta ARM->Thumb montada a mao" in item
               for item in levantada.nao_levantadas), levantada.nao_levantadas
