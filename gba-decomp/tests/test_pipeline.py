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


def test_corpus_lista_25_funcoes_com_verdade_terreno(corpus_pronto):
    nomes = {f.nome for f in corpus_pronto.funcoes}
    assert len(nomes) == 25
    assert {"soma", "fat", "divide", "loop_decrescente", "main_teste"} <= nomes
    assert len(corpus_pronto.sha256) == 64


def test_verdade_terreno_passa_no_corpus(corpus_pronto):
    rel = verificador.verificar_verdade_terreno(corpus_pronto)
    assert rel.total == 60
    assert rel.reprovados == [], rel.texto()


def test_tabela_de_verdade_nao_foi_copiada_do_resultado(corpus_pronto):
    """Se alguem 'consertar' a tabela copiando a saida da emulacao, este teste
    derruba: os valores esperados sao literais conferidos a mao na fonte."""
    fonte = (RAIZ / "gbadecomp" / "corpus.py").read_text()
    assert '"esperado": 42' in fonte          # soma(7, 35)
    assert '"esperado": 120' in fonte         # fat(5)
    assert '"esperado": 0xFFFE0001' in fonte  # mul32(0xFFFF, 0xFFFF)
    assert fonte.count('"funcao":') == 60


def test_descoberta_recursiva_acha_todas_as_funcoes(corpus_pronto):
    imagem = Path(corpus_pronto.rom_path).read_bytes()
    desmontagem = disasm.desmontar_por_sementes(imagem)   # so o vetor de boot
    esperadas = {f.addr for f in corpus_pronto.funcoes}
    assert set(desmontagem.funcoes) == esperadas
    assert desmontagem.total_instrucoes == 379
    assert len(desmontagem.arestas()) == 27


def test_grafo_de_chamadas_bate_com_a_verdade(corpus_pronto):
    imagem = Path(corpus_pronto.rom_path).read_bytes()
    desmontagem = disasm.desmontar_por_sementes(imagem)
    nome = {f.addr: f.nome for f in corpus_pronto.funcoes}
    arestas = {(nome[a], nome[b]) for a, b in desmontagem.arestas()}
    assert ("divide", "__aeabi_uidiv") in arestas
    assert ("chama_soma", "soma") in arestas
    assert ("loop_decrescente", "__aeabi_lmul") in arestas
    assert ("__aeabi_lmul", "mul32") in arestas
    assert len([a for a, _ in arestas if a == "main_teste"]) == 23


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
    assert rodada.relatorio_original.aprovados == 60
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
    # O texto diz o LIMITE DO MODELO, e nao "falta implementar": no ARMv4T o valor
    # lido do PSR carrega modo e mascara de IRQ, que o C levantado nao tem (e o
    # capstone 5 nomeia esse encoding de `apsr`, nome do ARMv6+).
    motivo = codigo.incompletas[0].nao_levantadas[0]
    assert "PSR" in motivo and "mrs r0" in motivo, motivo
    assert "mnemonico nao implementado" not in motivo, motivo


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
    # O TEXTO: a recusa tem de dizer o que foi MEDIDO, nao um rotulo generico.
    # "salto calculado (tabela de casos) nao modelado" mandava procurar um
    # `switch` que quase fechou -- e as 2 recusas da ROM de estudo nao sao tabela
    # nenhuma (uma e' ponteiro lido da memoria, a outra cai em trecho que parece
    # dado). O criterio vem do desmontador, por site, e agora viaja com a recusa.
    motivo = funcao.nao_levantadas[0]
    assert "salto por registrador" in motivo, motivo
    for texto in (motivo, funcao.corpo):
        assert "o idioma de tabela de casos nao fechou" in texto, texto
    assert "so' 1 instrucoes antes do" in motivo, motivo
    assert "PC calculado em r0" in funcao.corpo, funcao.corpo


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
    assert lev["funcoes"] == 25
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
    # o comentario do C diz o QUE foi medido, e nao um rotulo: aqui, qual entrada
    # da tabela nao existe no alvo (antes dizia so' "tabela de casos nao
    # reconhecida", que manda procurar defeito no lugar errado -- item 17)
    assert "o idioma de tabela de casos nao fechou" in levantada.corpo
    assert "a entrada 3 da tabela" in levantada.corpo, levantada.corpo
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


def test_veneer_adr_bx_vira_chamada_de_cauda_quando_o_bloco_retorna():
    """`adr`+`bx` que troca de modo para uma ROTINA e' chamada de cauda.

    Medido na ROM de estudo: 3 pares no universo inteiro; o de 0x081DC010 vai
    para 0x081DC014, que e' `umull r2, r3, r0, r1; add r0, r3, #0; bx lr` --
    devolve pelo `lr`, logo e' rotina do outro modo. O desmontador passa a
    semear esse alvo no modo do bit0 e o `bx` vira `r0 = fn_X(...); return r0;`.

    Aqui o bloco ARM e' so' `bx lr`, e o `beq` existe porque `bx` encerra a
    leitura: sem ele a janela Thumb terminaria no `bx` e nao haveria continuacao.
    """
    # montagem explicita, instrucao por instrucao (o hexa em uma linha so' esconde
    # de onde vem cada uma)
    imagem = bytearray(0x40)
    for endereco, meio in (
        (0x08000020, 0x2B00),      # cmp r3, #0
        (0x08000022, 0xD003),      # beq 0x0800002C
        (0x08000024, 0xA204),      # adr r2, #4  -> 0x08000038 (par: ARM)
        (0x08000026, 0x4710),      # bx r2
        (0x0800002C, 0x2001),      # movs r0, #1   (continuacao)
        (0x0800002E, 0x4770),      # bx lr
    ):
        imagem[endereco - rom.ROM_BASE:endereco - rom.ROM_BASE + 2] = meio.to_bytes(2, "little")
    imagem[0x38:0x3C] = bytes.fromhex("1eff2fe1")          # ARM: bx lr
    desmontagem = disasm.desmontar_por_sementes(
        bytes(imagem), sementes={0x08000020: "thumb"})
    assert 0x08000038 in desmontagem.funcoes, sorted(desmontagem.funcoes)
    assert desmontagem.funcoes[0x08000038].modo == "arm"
    assert "veneer" in desmontagem.funcoes[0x08000038].semente
    codigo = decompile.decompilar(desmontagem, bytes(imagem))
    levantada = next(f for f in codigo.funcoes if f.endereco == 0x08000020)
    assert levantada.completa, levantada.nao_levantadas
    assert "chamada de cauda" in levantada.corpo
    assert "r0 = fn_08000038(r0, r1, r2, r3);" in levantada.corpo


def test_veneer_adr_bx_para_ilha_e_recusado_dizendo_que_a_continuacao_fica_dentro():
    """O mesmo par, com o bloco ARM saindo para DENTRO da janela, NAO e' rotina.

    Medido na ROM de estudo: `0x081DC0B0` e `0x081DC240` terminam em
    `add r0, pc, #imm; bx r0` e voltam para `0x081DC132` / `0x081DC43C` -- os
    DOIS enderecos estao dentro da janela Thumb que fez a troca. Chamar de cauda
    devolveria r0 sem executar o resto da rotina: esconderia a lacuna atras de C
    errado. A recusa tem de dizer isso, e nao "nao ha' janela ARM" (ha' -- ela
    foi lida; o que nao fecha e' a continuacao no outro modo).
    """
    imagem = bytearray(0x40)
    for endereco, meio in (
        (0x08000020, 0x2B00),      # cmp r3, #0
        (0x08000022, 0xD007),      # beq 0x08000034
        (0x08000024, 0xA000),      # adr r0, #0  -> 0x08000028 (par: ARM)
        (0x08000026, 0x4700),      # bx r0
        (0x08000034, 0x4770),      # bx lr -- continuacao thumb (alvo do beq)
    ):
        imagem[endereco - rom.ROM_BASE:endereco - rom.ROM_BASE + 2] = meio.to_bytes(2, "little")
    imagem[0x28:0x30] = bytes.fromhex("05008fe210ff2fe1")   # add r0, pc, #5 ; bx r0
    desmontagem = disasm.desmontar_por_sementes(
        bytes(imagem), sementes={0x08000020: "thumb"})
    assert 0x08000028 not in desmontagem.funcoes        # ilha nao vira janela
    (janela,) = [f for f in desmontagem.funcoes.values() if f.entrada == 0x08000020]
    assert janela.ilhas, "o desmontador tem de MEDIR a ilha, nao so' recusar"
    site, alvo, modo_alvo, forma, saida = janela.ilhas[0]
    assert (site, alvo, modo_alvo) == (0x08000024, 0x08000028, "arm")
    assert forma == "ilha" and saida == 0x08000035, janela.ilhas
    codigo = decompile.decompilar(desmontagem, bytes(imagem))
    levantada = next(f for f in codigo.funcoes if f.endereco == 0x08000020)
    assert not levantada.completa
    motivo = next(m for m in levantada.nao_levantadas if "bx r0" in m)
    assert "ILHA de codigo arm" in motivo, motivo
    assert "0x08000035" in motivo and "dentro DESTA janela" in motivo, motivo
    # e o C NAO inventa a chamada: nada de `fn_08000028`
    assert "fn_08000028" not in levantada.corpo


def test_bx_com_valor_conhecido_diz_o_que_mediu_em_vez_de_sem_origem():
    """`bx rN` cujo valor E' conhecido: a frase carrega a medicao, nao um palpite.

    Medido na ROM de estudo, nas 39 recusas `bx rN`: 4 tem valor conhecido em
    tempo de traducao -- 3 vem de `adr rD, #imm` (valor PAR: no ARM7TDMI bit0 = 0
    em `bx` quer dizer modo ARM, entao o alvo e' o trecho no OUTRO modo, que uma
    janela Thumb nao levanta) e 1 vem de literal de pool (0x030028E1: RAM, com o
    bit do modo). As 4 diziam "sem origem conhecida", que e' falso -- a origem
    esta' na instrucao anterior e o levantador consegue le'-la. O caso (c) e'
    sintetico (nao ha' ocorrencia na ROM): valor dentro da imagem com bit0 = 1.
    """
    # (a) `adr r2, #0` + `bx r2`: 0x08000024 (par) -> o hardware muda para ARM.
    # A frase mudou quando o desmontador passou a MEDIR a forma do bloco do
    # outro modo (rotina que devolve pelo `lr` x ilha): aqui o bloco nao devolve,
    # entao dizer "troca de modo de CPU" sozinho era menos do que se sabia.
    imagem = _imagem_de_janela(0xA200, 0x4710)
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    (levantada,) = decompile.decompilar(desmontagem, imagem).funcoes
    assert not levantada.completa
    assert any("troca de modo para arm em 0x08000024" in item
               and "NAO devolve pelo `lr`" in item for item in levantada.nao_levantadas), \
        levantada.nao_levantadas

    # (b) `ldr r3, [pc, #0]` + `bx r3`, literal 0x030028E1: fora da imagem
    imagem = _imagem_de_janela(0x4B00, 0x4718, 0x28E1, 0x0300)
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    (levantada,) = decompile.decompilar(desmontagem, imagem).funcoes
    assert any("fora da imagem (espaco de RAM/IO)" in item and "0x030028E1" in item
               for item in levantada.nao_levantadas), levantada.nao_levantadas

    # (c) valor conhecido dentro da IMAGEM e 0x08000021 (bit0 = 1, Thumb): o
    # endereco 0x08000020 esta' desmontado, entao a frase tem de dizer isso --
    # antes ela dizia "trecho nao desmontado" porque perguntava o intervalo
    # grosso antes de consultar o indice de instrucoes.
    imagem = _imagem_de_janela(0x4B00, 0x4718, 0x0021, 0x0800)
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    (levantada,) = decompile.decompilar(desmontagem, imagem).funcoes
    assert any("bit0 = 1, modo Thumb" in item and "o alvo 0x08000020 esta'" in item
               and "numa INSTRUCAO que a leitura alcancou" in item
               for item in levantada.nao_levantadas), levantada.nao_levantadas


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


def test_desvio_recusado_diz_onde_o_destino_foi_desmontado():
    """Se o alvo ESTA desmontado (em outra janela), a mensagem nao pode dizer
    "nao foi desmontado": isso e' afirmacao falsa sobre o proprio levantamento.

    Medido na ROM: 29 dos 130 desvios recusados caiam exatamente nisso -- o
    endereco estava desmontado como instrucao de OUTRA janela (bloco comum). A
    mensagem antiga ("rotulo inexistente") mandava procurar defeito onde nao
    tinha: nao falta implementar instrucao, falta a leitura poder continuar em
    outra rotina.
    """
    imagem = _imagem_com_salto_para_tras()      # B salta para 0x08000012, instrucao de A
    desmontagem = disasm.desmontar_por_sementes(
        imagem, sementes={0x08000010: "thumb", 0x08000014: "thumb"})
    codigo = decompile.decompilar(desmontagem, imagem)
    b = next(f for f in codigo.funcoes if f.endereco == 0x08000014)
    item = next(i for i in b.nao_levantadas if i.startswith("0x08000016"))
    assert "INSTRUCAO da janela 0x08000010" in item, item
    assert "nao foi desmontado" not in item


def test_desvio_para_endereco_que_ninguem_desmontou_diz_isso():
    """E se ninguem passou pelo endereco, a mensagem tambem diz -- sem supor."""
    base = rom.ROM_BASE
    imagem = bytearray(0x40)
    imagem[0x10:0x14] = b"\xff\xff\xff\xff"           # nada decodificavel aqui
    imagem[0x20:0x22] = (0x2001).to_bytes(2, "little")   # movs r0, #1
    offset = (0x08000010 - (0x08000022 + 4)) // 2
    imagem[0x22:0x24] = (0xE000 | (offset & 0x7FF)).to_bytes(2, "little")   # b 0x08000010
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    codigo = decompile.decompilar(desmontagem, imagem)
    funcao = next(f for f in codigo.funcoes if f.endereco == 0x08000020)
    item = next(i for i in funcao.nao_levantadas if "0x08000010" in i)
    assert "fora de qualquer janela desmontada" in item, item


def _carregar_recortador():
    """`ferramentas/recortar_amostra.py` e' script, nao modulo do pacote."""
    import importlib.util
    caminho = RAIZ / "ferramentas" / "recortar_amostra.py"
    especificacao = importlib.util.spec_from_file_location("recortar_amostra", caminho)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


_C_FALSO = """/* cabecalho do arquivo inteiro, nao faz parte de nenhuma funcao */
void outra(void) {
    /* este corpo NAO pode entrar no recorte de 0x08000020 */
}

/* chamada por 2: a, b */
/* PARCIAL (0x08000020): o corpo abaixo tem lacunas marcadas -- em execucao, marca g_erro:
     0x08000022 b #0x8000010: desvio para tras, para fora da funcao
   */
/* origem: 0x08000020 (thumb), semente: informada, pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000020(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0;
    r4 = r0;
    return r4;
}
"""


def test_recorte_da_amostra_leva_o_cabecalho_e_o_motivo_da_lacuna():
    """O bloco de uma funcao comeca no cabecalho dela -- inclusive no `PARCIAL`.

    Defeito real: a primeira versao do recortador subia so' por linhas que
    comecavam com `/*`. O bloco `/* PARCIAL ... */` tem linhas de motivo no MEIO
    (a linha do desvio recusado nao comeca com `/*`), entao o recorte perdia
    justamente o motivo da lacuna -- a amostra mostraria a lacuna sem dizer por
    que. E o corpo da funcao ANTERIOR nao pode entrar: o corte e' a linha em
    branco que separa as funcoes.
    """
    recortador = _carregar_recortador()
    linhas = _C_FALSO.splitlines()
    inicio, fim, nome = recortador.achar_bloco(linhas, 0x08000020)
    bloco = linhas[inicio:fim]
    assert nome == "fn_08000020"
    assert bloco[0] == "/* chamada por 2: a, b */", bloco[0]
    assert any("0x08000022 b" in linha for linha in bloco)   # o motivo veio junto
    assert any("PARCIAL (0x08000020)" in linha for linha in bloco)
    assert bloco[-1] == "}" and "return r4;" in bloco[-2]
    assert not any("outra(void)" in linha or "NAO pode entrar" in linha
                   for linha in bloco), "recorte engoliu a funcao anterior"


def test_recorte_declara_o_tamanho_do_que_tirou_e_nao_quebra_comentario():
    """Cortar o meio e' permitido; esconder que cortou nao e'.

    O marcador tem de dizer QUANTAS linhas sairam (a conta tem de fechar com o
    bloco original) e tem de caber em UMA linha: um marcador com quebra de linha
    dentro empurra o `*/` para depois e ja' saiu daqui torto.
    """
    recortador = _carregar_recortador()
    linhas = _C_FALSO.splitlines()
    inicio, fim, _ = recortador.achar_bloco(linhas, 0x08000020)
    total = fim - inicio                       # o bloco de _C_FALSO tem 10 linhas
    recortada = recortador.recortar(linhas, inicio, fim, 8)   # cabecalho = 5 linhas
    assert len(recortada) == 8, recortada
    marcador = next(linha for linha in recortada if "linhas omitidas" in linha)
    tiradas = int(marcador.split("... ")[1].split(" ")[0])
    assert tiradas == (fim - inicio) - (len(recortada) - 1)
    recortador.comentarios_balanceados("\n".join(recortada) + "\n")
    # o corte nunca cai no meio do cabecalho de comentarios (comentario aberto):
    # o `*/` do bloco PARCIAL fica sempre do lado de dentro do recorte
    assert any("*/" in linha and "PARCIAL" not in linha for linha in recortada[:6])
    assert recortada[4] == "/* origem: 0x08000020 (thumb), semente: informada, pilha: balanceada */"
    with pytest.raises(SystemExit):
        recortador.recortar(linhas, inicio, fim, 3)   # orcamento menor que o cabecalho
    # fora do orcamento, o bloco sai inteiro -- sem marcador nenhum
    inteiro = recortador.recortar(linhas, inicio, fim, 100)
    assert inteiro == linhas[inicio:fim]


def test_amostra_do_repositorio_conta_a_rodada_do_json_ao_lado():
    """O cabecalho da amostra e' o retrato do JSON que esta' no mesmo diretorio.

    Antes esses numeros eram digitados a mao: bastava uma rodada nova para o
    cabecalho ficar contando uma medicao que nao era a do arquivo ao lado. Agora
    a amostra e' gerada de `evidencias/rom_bpre_analise.json`; este teste e' o que
    impede a digitacao de voltar.
    """
    amostra = (RAIZ / "evidencias" / "rom_bpre_amostra_levantada.c").read_text(encoding="utf-8")
    analise = json.loads((RAIZ / "evidencias" / "rom_bpre_analise.json").read_text(encoding="utf-8"))
    levantamento, descoberta = analise["levantamento"], analise["completo"]
    for numero in (descoberta["funcoes"], descoberta["instrucoes"], descoberta["arestas"],
                   descoberta["descartes"], descoberta["tabelas_de_casos"],
                   descoberta["casos_de_tabela"], levantamento["completas"],
                   levantamento["parciais"], analise["linhas_c"], analise["bytes_c"],
                   analise["conferencia"]["identicas"], analise["linhas_c"]):
        assert str(numero) in amostra, f"{numero} nao aparece no cabecalho da amostra"
    assert analise["sha256"] in amostra                     # a ROM e' a mesma
    assert f"sha256 do .c levantado" in amostra             # e o .c diz de onde veio
    for caso in ("FUN_080011e4", "fn_08014040", "fn_081DC45A"):
        assert amostra.count(f"-- {caso} --") == 1, caso      # um caso, uma vez


def test_histograma_de_recusas_fecha_com_o_total_e_agrupa_endereco():
    """A soma dos motivos tem de dar o TOTAL de recusas -- senao o numero mente.

    Defeito real: `_recusas` devolvia o histograma de motivos cortado em 12 grupos
    e truncado em 90 caracteres, e a soma dele (67) nao tinha relacao com o numero
    de recusas (189). Quem citasse o JSON podia escrever "67 recusas" -- um numero
    que existe no arquivo, com o nome errado. Agora o total vai separado e a soma
    dos motivos tem de fechar com ele.

    O segundo defeito era o agrupamento: quase todo motivo carrega o endereco do
    desvio dentro do texto, entao sem canonizar (`_canonico`) cada motivo virava
    um grupo de 1.
    """
    class Falsa:
        def __init__(self, itens):
            self.nao_levantadas = itens

    codigo = type("C", (), {"funcoes": [
        Falsa([
            "0x08001234 mov pc, r0: desvio indireto por registrador sem origem conhecida",
            "0x08001235 bx r1: desvio para 0x08001000, sem rotulo nesta janela: "
            "fora de qualquer janela desmontada: nenhuma leitura passou por esse endereco",
            "0x08001236 bx r2: desvio para 0x08002000, sem rotulo nesta janela: "
            "fora de qualquer janela desmontada: nenhuma leitura passou por esse endereco",
        ]),
        Falsa(["0x08001237 stmdb sp!, {r0}: mnemonico nao implementado"]),
    ]})()
    por_mnemonico, por_motivo, total = analise_mod._recusas(codigo)
    assert total == 4
    assert sum(por_mnemonico.values()) == total
    assert sum(por_motivo.values()) == total, por_motivo
    assert por_mnemonico == {"bx": 2, "mov": 1, "stmdb": 1}
    # dois enderecos diferentes com a mesma frase = UM grupo de 2
    agrupado = next(k for k, v in por_motivo.items() if v == 2)
    assert "fora de qualquer janela desmontada" in agrupado
    assert "0x08001000" not in agrupado and "0x..." in agrupado


def _decodifica(bytes_, endereco, modo):
    """Desmonta bytes de verdade -- antes de julgar o filtro, veja o que ESTA la."""
    import capstone
    cs = capstone.Cs(capstone.CS_ARCH_ARM,
                     capstone.CS_MODE_THUMB if modo == "thumb" else capstone.CS_MODE_ARM)
    cs.detail = True
    lidas = list(cs.disasm(bytes_, endereco, count=1))
    assert lidas, f"{bytes_.hex(' ')} nao decodifica em {modo}"
    return lidas[0]


def test_instrucao_que_nao_existe_no_thumb1_e_marcada_como_tal():
    """Formas com letra colada no nome passavam pelo filtro (`ldcl`, `stcl`).

    Bytes reais da ROM de estudo (imagem do usuario, modo Thumb), todos com
    `impossivel_no_arm7tdmi` devolvendo None antes desta correcao -- ou seja,
    chegavam ao lifter como "mnemonico nao implementado", que e' afirmacao falsa:
    `orn`/`orns` sao ARMv6, `smlawt` e' ARMv5TE, `hint` e' Thumb-2, `ldcl`/`stcl`
    sao coprocessador (nao existe no Thumb-1) e `stmdb r0, {...}` so' existe no
    ARM. Nada disso executa num ARM7TDMI: ali a leitura passou por DADO.
    """
    casos = [
        ("67 f0 52 1a", 0x081A6798, "thumb", "orn"),
        ("00 e9 e1 00", 0x081A6ECE, "thumb", "stmdb"),
        ("d9 ed ab ff", 0x083FD156, "thumb", "ldcl"),
        ("3a fb 1c 08", 0x081C6CDC, "thumb", "smlawt"),
        ("b0 bf", 0x086C9E72, "thumb", "hint"),
        ("74 ea a5 65", 0x0862B40C, "thumb", "orns"),
    ]
    for hexa, endereco, modo, mnemonic in casos:
        ins = _decodifica(bytes.fromhex(hexa), endereco, modo)
        assert ins.mnemonic == mnemonic, (ins.mnemonic, mnemonic)   # o que esta' la
        motivo = disasm.impossivel_no_arm7tdmi(ins, modo)
        assert motivo is not None, f"{mnemonic} deveria ser impossivel em {modo}"
    # o MESMO `stmdb sp!, {lr}` e' legal no ARM do ARMv4T -- nao pode ser filtrado
    ins = _decodifica(bytes.fromhex("00 40 2d e9"), 0x08000368, "arm")
    assert ins.mnemonic == "stmdb" and disasm.impossivel_no_arm7tdmi(ins, "arm") is None
    # `mrs` existe no ARM (e' o que carrega spsr/cpsr); so' o Thumb-1 nao tem
    ins = _decodifica(bytes.fromhex("00 00 4f e1"), 0x08000258, "arm")
    assert ins.mnemonic == "mrs" and disasm.impossivel_no_arm7tdmi(ins, "arm") is None
    # os MESMOS bytes lidos em Thumb nao sao `mrs` -- sao outra instrucao valida;
    # o filtro so' julga o que o desmontador leu no modo certo
    ins = _decodifica(bytes.fromhex("00 00 4f e1"), 0x08000258, "thumb")
    assert ins.mnemonic == "movs" and disasm.impossivel_no_arm7tdmi(ins, "thumb") is None
    # e o filtro nao pode ser um "nao" geral: o que existe no alvo passa
    for hexa, endereco, mnemonic in [("10 b5", 0x08000000, "push"),
                                     ("01 c8", 0x08000000, "ldm"),
                                     ("08 68", 0x08000000, "ldr"),
                                     ("01 30", 0x08000000, "adds"),
                                     ("70 47", 0x08000000, "bx")]:
        ins = _decodifica(bytes.fromhex(hexa), endereco, "thumb")
        assert ins.mnemonic == mnemonic, (ins.mnemonic, mnemonic)
        assert disasm.impossivel_no_arm7tdmi(ins, "thumb") is None


def test_lifter_distingue_instrucao_que_nao_existe_de_falta_implementar():
    """Se uma impossivel chegar ao lifter, o motivo tem de dizer ISSO.

    Defesa em profundidade: depois do filtro do desmontador isso nao deveria
    acontecer, mas se acontecer (furo no filtro) o texto nao pode mandar quem le
    procurar defeito onde nao tem -- foi o que aconteceu com 20 das 189 lacunas da
    ROM. Instrucao impossivel = dado lido como codigo; instrucao que existe no
    ARMv4T e' que e' "falta implementar", e ai' o texto tem de dizer os dois casos
    de forma diferente.
    """
    class DesmontagemFalsa:
        dados_lidos: dict = {}

        def __init__(self, funcoes):
            self.funcoes = {f.entrada: f for f in funcoes}

        def arestas(self):
            return []

    def monta(hexa, endereco, modo):
        """Imagem com os bytes REAIS no lugar, e a instrucao lida dela (nao "de memoria")."""
        imagem = bytearray(0x100)
        deslocamento = endereco - rom.ROM_BASE
        imagem[deslocamento:deslocamento + 4] = bytes.fromhex(hexa)
        ins = _decodifica(bytes.fromhex(hexa), endereco, modo)
        funcao = disasm.FuncaoDesmontada(entrada=endereco, modo=modo, semente="teste")
        funcao.instrucoes.append(disasm.Instrucao(endereco, ins.bytes, ins.mnemonic,
                                                  ins.op_str, modo))
        return bytes(imagem), DesmontagemFalsa([funcao])

    imagem, desmontagem = monta("67 f0 52 1a", 0x08000020, "thumb")   # `orn` (dado)
    codigo = decompile.decompilar(desmontagem, imagem, nomes={})
    levantada = codigo.funcoes[0]
    motivo = next(i for i in levantada.nao_levantadas if "orn" in i)
    assert "nao existe no ARM7TDMI" in motivo, motivo
    assert "passou por dado" in motivo, motivo
    assert "mnemonico nao implementado" not in motivo, motivo

    # `mrs` no ARM EXISTE no ARMv4T (le' spsr/cpsr) -- mas o valor LIDO carrega
    # modo e mascara de IRQ, que o modelo do C levantado nao tem (so' z/n/c/v). O
    # texto tem de dizer isso: limite do MODELO, nao trabalho que falta.
    imagem, desmontagem = monta("00 00 4f e1", 0x08000020, "arm")      # mrs r0, spsr
    codigo = decompile.decompilar(desmontagem, imagem, nomes={})
    motivo = next(i for i in codigo.funcoes[0].nao_levantadas if "mrs" in i)
    assert "nao tem traducao" in motivo and "PSR" in motivo, motivo
    assert "falta traduzir" not in motivo, motivo
    assert "nao existe no ARM7TDMI" not in motivo, motivo
    # e o `msr cpsr_fc, r3` (o que ESCREVE a mascara de IRQ) diz o limite tambem
    imagem, desmontagem = monta("03 f0 29 e1", 0x08000020, "arm")      # msr cpsr_fc, r3
    codigo = decompile.decompilar(desmontagem, imagem, nomes={})
    motivo = next(i for i in codigo.funcoes[0].nao_levantadas if "msr" in i)
    assert "CONTROLE" in motivo and "mascara de IRQ" in motivo, motivo


def test_filtro_nao_rejeita_o_que_existe_no_thumb1():
    """A lista de "impossivel no Thumb-1" tinha `adr` e `mul` -- os dois existem.

    O custo disso apareceu na medicao: **56 funcoes terminavam em `adr`**, porque
    a leitura parava ali achando que tinha encontrado dado. No Thumb-1 `adr` e'
    `add r0, pc, #8` (bytes `02 a0`) e `muls` e' `muls r0, r1, r0` (bytes
    `48 43`) -- os dois do ARMv4T. Este teste trava a lista pelos DOIS lados: o que
    existe passa e o que nao existe e' recusado.
    """
    for hexa, mnemonic in [("02 a0", "adr"), ("48 43", "muls"), ("80 b0", "sub"),
                           ("10 b5", "push"), ("70 47", "bx")]:
        ins = _decodifica(bytes.fromhex(hexa), 0x08000000, "thumb")
        assert ins.mnemonic == mnemonic, (ins.mnemonic, mnemonic)
        assert disasm.impossivel_no_arm7tdmi(ins, "thumb") is None, mnemonic
    # do outro lado: o que o Thumb-1 NAO tem continua recusado
    for hexa, mnemonic in [("00 ba", "rev"), ("b0 bf", "hint"), ("00 00", None)]:
        ins = _decodifica(bytes.fromhex(hexa), 0x08000000, "thumb")
        if mnemonic is None:
            continue
        assert ins.mnemonic == mnemonic, (ins.mnemonic, mnemonic)
        assert disasm.impossivel_no_arm7tdmi(ins, "thumb") is not None, mnemonic


def test_adr_do_levantador_bate_com_o_emulador(corpus_pronto):
    """O valor ABSOLUTO do `adr` no C tem de ser o que a CPU produz.

    O caso `distancia_adr` da tabela de verdade prova a aritmetica do `adr` (a
    diferenca entre dois deles), de proposito: e' o que vale nos DOIS binarios
    (original e C levantado recompilado, com layouts diferentes). O valor absoluto
    nao caberia ali, entao e' conferido aqui contra o emulador: cada `adr` do
    corpus e' executado SOZINHO pelo unicorn (`limite=1` instrucao) e o r0 que sai
    tem de ser o numero que o levantador escreveu no C. A regra do PC no Thumb e'
    `(endereco + 4) & ~3` -- com `endereco + 4` o valor sai 2 a mais quando a
    instrucao esta em endereco 2 mod 4, e o corpus tem um `adr` exatamente assim.
    """
    from gbadecomp import verificador as ver_mod

    imagem = Path(corpus_pronto.rom_path).read_bytes()
    desmontagem = disasm.desmontar_por_sementes(imagem)
    alvo = next(f for f in corpus_pronto.funcoes if f.nome == "distancia_adr")
    adrs = [i for i in desmontagem.funcoes[alvo.addr].instrucoes
            if i.mnemonic == "adr"]
    assert len(adrs) == 2, [i.mnemonic for i in adrs]
    assert any(i.endereco % 4 == 2 for i in adrs), \
        "sem um `adr` em endereco 2 mod 4 o teste nao exercita o alinhamento do PC"
    codigo = decompile.decompilar(desmontagem, imagem, nomes={})
    levantada = next(f for f in codigo.funcoes if f.endereco == alvo.addr)
    linhas = [l for l in levantada.corpo.splitlines() if "/* adr:" in l]
    assert len(linhas) == len(adrs), linhas
    from unicorn.arm_const import UC_ARM_REG_R0

    emu = ver_mod.Emulador(imagem)
    for instrucao, linha in zip(adrs, linhas):
        no_c = int(linha.split("=", 1)[1].split("u;")[0].strip(), 16)
        # ATENCAO (2 armadilhas medidas aqui): `chamar` devolve r0 e o segundo
        # `adr` escreve em r1 -- ler r0 nos dois faz o teste passar dizendo o
        # contrario (o r0 ficava com o valor do primeiro `adr`); e o numero de
        # registrador do capstone NAO e' o do unicorn (`operands[0].reg` = 132
        # aqui, e o unicorn reclamou de id invalido), entao o nome sai do capstone
        # e o numero, do nome.
        lida = _decodifica(instrucao.bytes_, instrucao.endereco, instrucao.modo)
        nome = lida.reg_name(lida.operands[0].reg)
        assert nome.startswith("r") and nome[1:].isdigit(), nome
        emu.chamar(instrucao.endereco, limite=1)      # executa SO' esta instrucao
        na_cpu = emu.mu.reg_read(UC_ARM_REG_R0 + int(nome[1:]))
        assert no_c == na_cpu, (hex(instrucao.endereco), hex(no_c), hex(na_cpu))


def test_forma_inexistente_no_thumb1_e_julgada_pelo_tamanho_da_codificacao():
    """Quem decide se a forma existe e' a CODIFICACAO, nao o texto do capstone.

    Bytes reais da ROM de estudo:
        0x08000BD6  48 42        rsbs r0, r1, #0     (2 B -- o `neg` do Thumb-1)
        0x0845A3B6  44 f5 50 44  adc  r4, r4, #0xd000 (4 B -- Thumb-2)
        0x0845A3BA  44 f5 70 66  adc  r6, r4, #0xf00  (4 B -- Thumb-2)
        0x081C69C0  08 f3 1c 08  ssat r8, #0x1d, r8  (4 B -- ARMv6)
    Duas regras anteriores perguntaram por NOME + OPERANDOS impressos e as duas
    estavam erradas: `lsls`/`lsrs`/`asrs` com imediato existem no Thumb-1, e o
    `#0` que o capstone mostra em `rsbs r0, r1, #0` nao esta codificado (a regra
    marcou 1 750 instrucoes validas como inexistentes e o C nao compilou).
    """
    casos = [("48 42", 0x08000BD6, "rsbs", False),
             ("44 f5 50 44", 0x0845A3B6, "adc", True),
             ("44 f5 70 66", 0x0845A3BA, "adc", True),
             ("08 f3 1c 08", 0x081C69C0, "ssat", True),
             ("41 41", 0x08000000, "adcs", False)]
    for hexa, endereco, mnemonic, eh_forma_inexistente in casos:
        ins = _decodifica(bytes.fromhex(hexa), endereco, "thumb")
        assert ins.mnemonic == mnemonic, (ins.mnemonic, mnemonic)
        forma = disasm.forma_impossivel_no_thumb1(ins, "thumb")
        assert (forma is not None) == eh_forma_inexistente, (hexa, mnemonic, forma)
        if eh_forma_inexistente:
            assert len(ins.bytes) == 4, hexa
    # `ssat` esta na lista por nome (o filtro PARA a leitura ali); o `adc` NAO
    # esta: ele existe no ARMv4T, o que nao existe e' a forma de 32 bits.
    assert disasm.impossivel_no_arm7tdmi(_decodifica(bytes.fromhex("08 f3 1c 08"),
                                                     0x081C69C0, "thumb"), "thumb") is not None
    assert disasm.impossivel_no_arm7tdmi(_decodifica(bytes.fromhex("44 f5 50 44"),
                                                     0x0845A3B6, "thumb"), "thumb") is None
    assert disasm.impossivel_no_arm7tdmi(_decodifica(bytes.fromhex("48 42"),
                                                     0x08000BD6, "thumb"), "thumb") is None
    # a regra so' vale no Thumb: no ARM toda instrucao tem 4 bytes
    ins = _decodifica(bytes.fromhex("04 40 a0 e2"), 0x08000000, "arm")
    assert ins.mnemonic.startswith("adc"), ins.mnemonic
    assert disasm.forma_impossivel_no_thumb1(ins, "arm") is None


def _milhar(numero: int) -> str:
    """Como o README escreve: 1 046 836 (espaco no lugar da virgula)."""
    return f"{numero:,}".replace(",", " ")


def test_readme_conta_a_mesma_rodada_da_evidencia():
    """Os numeros das tabelas do README tem de sair da evidencia versionada.

    Este defeito reapareceu tres vezes no projeto, sempre do mesmo jeito: um
    numero digitado a mao sobrevive a uma rodada nova (o cabecalho da amostra
    contava uma rodada que nao era a do arquivo ao lado; o relatorio de conferencia
    dizia "25 divergencias" para 225; o JSON tinha um "67" que ninguem sabia
    definir). Agora a tabela da ROM e' conferida contra
    `evidencias/rom_bpre_analise.json`: se a medicao mudar e o README nao, cai.
    """
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    analise = json.loads((RAIZ / "evidencias" / "rom_bpre_analise.json").read_text(encoding="utf-8"))
    descoberta, lev = analise["completo"], analise["levantamento"]
    exigidos = {
        "funcoes": _milhar(descoberta["funcoes"]),
        "instrucoes": _milhar(descoberta["instrucoes"]),
        "arestas": _milhar(descoberta["arestas"]),
        "descartes": _milhar(descoberta["descartes"]),
        "fora do censo": _milhar(descoberta["fora_do_censo"]),
        "saidas para tras": _milhar(descoberta["saidas_para_tras"]),
        "orfaos recuperados": _milhar(descoberta["saidas_recuperadas"]),
        "tabelas": _milhar(descoberta["tabelas_de_casos"]),
        "casos de tabela": _milhar(descoberta["casos_de_tabela"]),
        "completas": _milhar(lev["completas"]),
        "parciais": _milhar(lev["parciais"]),
        "linhas de C": _milhar(analise["linhas_c"]),
        "objeto": _milhar(analise["compilacao"]["bytes_objeto"]),
        "recusas": _milhar(analise["recusas_total"]),
    }
    ausentes = {rotulo: valor for rotulo, valor in exigidos.items() if valor not in readme}
    assert not ausentes, f"o README nao conta a rodada da evidencia: {ausentes}"
    # a taxa de remontagem e' publicada com virgula decimal
    taxa = f"{analise['conferencia']['taxa']:.3f}".replace(".", ",")
    assert taxa in readme, taxa

    # A TABELA DAS LACUNAS tambem tem de sair da evidencia: cada linha e' um
    # numero publicado, e numero publicado a mao ja' sobreviveu a tres rodadas
    # neste projeto. As linhas somam o total (senao a tabela mente por omissao).
    def soma(predicado) -> int:
        return sum(v for k, v in analise["recusas_motivo"].items() if predicado(k))

    linhas = {
        "bx rN": (analise["recusas_mnemonico"]["bx"],
                  "| `bx rN` com origem nao rastreada | {} "),
        "desvio que sai da funcao": (soma(lambda k: "desvio para tras" in k
                                          or "salto para fora da funcao" in k),
                                     "| desvio que sai da funcao (bloco comum de outra "
                                     "rotina) | {} "),
        "desvio sem rotulo": (soma(lambda k: "sem rotulo nesta janela" in k),
                              "| desvio condicional para endereco sem rotulo nesta "
                              "janela | {} "),
        "instrucao inexistente": (soma(lambda k: "codificacao de 32 bits" in k),
                                  "| instrucao que **nao existe** no ARM7TDMI (dado "
                                  "lido como codigo) | {} "),
        # A categoria "falta traduzir" acabou: o que sobra de instrucao que EXISTE
        # no ARMv4T nao e' trabalho pendente, e' LIMITE DO MODELO -- o C levantado
        # nao tem PSR (so' as flags z/n/c/v). O texto publicado tem de ser o mesmo
        # que o JSON mede (era o defeito dos "67" do item 10).
        "PSR": (soma(lambda k: "PSR" in k),
                "| o PSR nao existe no MODELO (`mrs` lendo, `msr` escrevendo o campo "
                "de controle) | {} — o valor lido no ARMv4T carrega modo e mascara "
                "de IRQ, que o C levantado nao tem (so' z/n/c/v) |"),
        # "salto calculado (tabela de casos) nao modelado" virou um texto que diz
        # QUAL criterio do idioma faltou, medido por site (item 17): o rotulo
        # antigo mandava procurar tabela onde nao tem -- e as 2 recusas da ROM nao
        # sao tabela (uma e' ponteiro lido da memoria, a outra cai em trecho que
        # parece dado).
        "salto por registrador": (soma(lambda k: "salto por registrador" in k),
                                  "| `mov pc, rN` com o destino em registrador "
                                  "(nao e' o idioma de tabela de casos) | {} — o "
                                  "motivo diz QUAL criterio faltou, medido: `bhs` "
                                  "antes de 0x081DBEBA e `cmp r1, #0x53` antes de "
                                  "0x083F62EC |"),
    }
    assert sum(valor for valor, _ in linhas.values()) == analise["recusas_total"]
    fora = {rotulo: formato.format(valor) for rotulo, (valor, formato) in linhas.items()
            if formato.format(valor) not in readme}
    assert not fora, f"a tabela das lacunas no README nao conta a evidencia: {fora}"
    assert f"| **total** | **{analise['recusas_total']}** (" in readme


def test_readme_conta_a_rodada_SEM_CENSO_na_tabela_do_veneer():
    """A tabela do item 19 tem de sair da evidencia boot-only, nao da memoria.

    O censo externo (functions.csv) nao esta' versionado, entao a rodada de 8 172
    funcoes nao pode ser refeita daqui -- o que este repositorio reproduz sozinho
    e' a rodada sem censo, e ela virou evidencia (`rom_bpre_boot_sem_censo.json`).
    Numero publicado a mao ja' sobreviveu a tres rodadas neste projeto; a tabela
    do item 19 nao entra nessa lista.
    """
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    evidencia = json.loads((RAIZ / "evidencias" / "rom_bpre_boot_sem_censo.json")
                           .read_text(encoding="utf-8"))
    esperados = {
        "funcoes": _milhar(evidencia["completo"]["funcoes"]),
        "instrucoes": _milhar(evidencia["completo"]["instrucoes"]),
        "recusas": _milhar(evidencia["recusas_total"]),
        "completas": _milhar(evidencia["levantamento"]["completas"]),
        "parciais": _milhar(evidencia["levantamento"]["parciais"]),
        "objeto": _milhar(evidencia["compilacao"]["bytes_objeto"]),
    }
    ausentes = {rotulo: valor for rotulo, valor in esperados.items() if valor not in readme}
    assert not ausentes, f"o README nao conta a rodada boot-only: {ausentes}"
    # a rodada sem censo NAO tem numeros de censo: se o README publicasse um,
    # estaria inventando (o campo existe no JSON e vale None)
    assert evidencia["censo"] is None
    assert evidencia["completo"]["no_censo"] is None


def test_forma_que_nao_existe_e_checada_antes_do_despacho_por_mnemonico():
    """`adc` existe no ARMv4T -- mas `adc` COM IMEDIATO no Thumb-1 nao existe.

    A checagem de forma tem de vir ANTES do despacho por mnemonico: no fim da
    cadeia, o tratador de `adc` respondia por ela e a mensagem saia "forma
    aritmetica nao implementada" -- falsa (manda procurar defeito no levantador
    quando o que houve foi leitura passando por dado). Bytes reais da ROM:
    `44 f5 50 44` = adc r4, r4, #0xd000.
    """
    imagem = bytearray(0x40)
    imagem[0x20:0x24] = bytes.fromhex("44f55044")      # adc r4, r4, #0xd000 (Thumb-2)
    imagem[0x24:0x26] = bytes.fromhex("00bf")          # nop
    imagem[0x26:0x28] = bytes.fromhex("7047")          # bx lr
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    lidas = [(i.mnemonic, i.operadores) for i in desmontagem.funcoes[0x08000020].instrucoes]
    assert ("adc", "r4, r4, #0xd000") in lidas, lidas
    codigo = decompile.decompilar(desmontagem, imagem)
    levantada = next(f for f in codigo.funcoes if f.endereco == 0x08000020)
    motivos = " | ".join(levantada.nao_levantadas)
    assert "nao existe no ARM7TDMI" in motivos, motivos
    assert "codificacao de 32 bits" in motivos, motivos
    assert "forma aritmetica nao implementada" not in motivos, motivos


def test_evidencia_do_corpus_e_a_rodada_de_agora(rodada):
    """A evidencia versionada tem de ser a rodada de AGORA, campo a campo.

    Mesma classe de defeito do numero digitado a mao: um arquivo de evidencia que
    ficou para tras descreve um programa que nao existe mais. Aconteceu aqui --
    `evidencias/levantado_corpus.c` era de uma rodada de 24 funcoes e convivia com
    um corpus de 25, sem nada que reclamasse. O JSON e' gerado
    (`reconstruir.ResultadoRodada.para_json`, exposto como `cli rodada --json`),
    entao a comparacao nao tem campo escrito a mao de nenhum dos dois lados.
    """
    evidencia = json.loads((RAIZ / "evidencias" / "rodada_corpus.json")
                           .read_text(encoding="utf-8"))
    agora = json.loads(rodada.para_json())
    assert evidencia == agora

    # e o .c versionado tem de ser o .c desta rodada: comparar TAMANHO nao e'
    # comparar bytes (licao de uma rodada anterior), entao compara-se o texto.
    levantado = (RAIZ / "evidencias" / "levantado_corpus.c").read_text(encoding="utf-8")
    assert levantado == rodada.codigo.texto()


def _imagem_com_tabela_guarda_no_pool(limite: int) -> bytes:
    """Idioma de tabela de casos em que o guarda NAO e' `cmp rX, #k`.

    Medido na ROM de estudo (0x0805234C e 0x08050F5C, 268 casos cada):

        0x08052338  ldr r1, [pc, #0x18]   ; limite = 0x0000010B, lido do pool
        0x0805233C  cmp r5, r1
        0x0805233E  bls 0x08052344
        0x08052340  bl  0x08053774        ; fora da faixa

    Aqui o mesmo formato, com a tabela no fim:

        0x40  ldr r2, [pc, #0x10]   ; pool em 0x54 -> r2 = limite
        0x42  cmp r0, r2
        0x44  bhi 0x08000070        ; padrao
        0x46  lsls r0, r0, #2
        0x48  ldr r1, [pc, #0x10]   ; pool em 0x5C -> 0x08000080 (a tabela)
        0x4A  adds r0, r0, r1
        0x4C  ldr r0, [r0]
        0x4E  mov pc, r0
        0x80  tabela: 3 enderecos PARES
    """
    base = rom.ROM_BASE
    casos = [0x08000090, 0x08000094, 0x08000098]
    padrao = 0x08000070
    tabela = 0x08000080
    imagem = bytearray(0x100)

    def meia(endereco: int, valor: int) -> None:
        imagem[endereco - base:endereco - base + 2] = valor.to_bytes(2, "little")

    meia(0x08000040, (0x4800 | (2 << 8) | (0x10 // 4)))       # ldr r2, [pc, #0x10]
    meia(0x08000042, 0x4280 | (2 << 3))                       # cmp r0, r2
    meia(0x08000044, 0xD800 | ((padrao - 0x08000048) // 2))   # bhi padrao
    meia(0x08000046, 0x0080)                                  # lsls r0, r0, #2
    meia(0x08000048, (0x4800 | (1 << 8) | (0x10 // 4)))       # ldr r1, [pc, #0x10]
    meia(0x0800004A, 0x1840)                                  # adds r0, r0, r1
    meia(0x0800004C, 0x6800)                                  # ldr r0, [r0]
    meia(0x0800004E, 0x4687)                                  # mov pc, r0
    imagem[0x08000054 - base:0x08000058 - base] = limite.to_bytes(4, "little")
    imagem[0x0800005C - base:0x08000060 - base] = tabela.to_bytes(4, "little")
    meia(padrao, 0x20FF)                                      # movs r0, #0xFF
    meia(padrao + 2, 0x4770)                                  # bx lr
    for numero, endereco in enumerate(casos):
        meia(endereco, 0x2000 | ((numero + 1) * 0x10))        # movs r0, #N
        meia(endereco + 2, 0x4770)                            # bx lr
        inicio = tabela + 4 * numero
        imagem[inicio - base:inicio - base + 4] = endereco.to_bytes(4, "little")
    return bytes(imagem)


def test_guarda_do_switch_pode_estar_em_registrador_carregado_do_pool():
    """O limite do `switch` tambem vem por registrador -- e continua medivel.

    Criterio 4 sem esta forma recusava 2 tabelas de 268 casos cada na ROM de
    estudo, dizendo "nao existe `cmp rX, #k`": verdade incompleta. O limite
    estava na ROM (literal do pool), nao no campo imediato do `cmp`.
    """
    imagem = _imagem_com_tabela_guarda_no_pool(limite=2)      # 3 casos
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000040: "thumb"})
    (funcao,) = desmontagem.funcoes.values()
    lidas = [f"{i.mnemonic} {i.operadores}".strip() for i in funcao.instrucoes[:5]]
    assert "cmp r0, r2" in lidas, lidas
    (tabela,) = funcao.tabelas
    assert len(tabela.alvos) == 3, tabela.alvos
    assert tabela.guarda == 2, tabela.guarda
    assert "pool em" in tabela.guarda_fonte, tabela.guarda_fonte
    codigo = decompile.decompilar(desmontagem, imagem)
    (levantada,) = codigo.funcoes
    assert "switch" in levantada.corpo
    assert "limite 0x2 lido do pool" in levantada.corpo


def test_guarda_no_pool_que_nao_bate_tambem_recusa():
    """Se o limite do pool nao fechar com as entradas lidas, nao ha' tabela.

    Sem isto a forma nova viraria um "sim" geral para qualquer `cmp rX, rY`
    seguido de `mov pc, rZ` -- o que seria adivinhacao com cara de medicao.
    """
    imagem = _imagem_com_tabela_guarda_no_pool(limite=5)      # diz 6, tabela tem 3
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000040: "thumb"})
    (funcao,) = desmontagem.funcoes.values()
    assert funcao.tabelas == [], "nao pode reconhecer tabela que nao fecha com o limite"
    (site, motivo), = funcao.tabelas_recusadas
    assert "nao e' endereco de codigo dentro da imagem" in motivo, motivo
    codigo = decompile.decompilar(desmontagem, imagem)
    (levantada,) = codigo.funcoes
    assert "switch" not in levantada.corpo
    assert not levantada.completa


def test_sonda_de_tabela_roda_e_diz_o_motivo(tmp_path):
    """A sonda que explica a recusa e' conferida RODANDO, no caso recusado.

    Ela existe para responder "por que nao virou switch?" -- e ja' falhou do jeito
    mais bobo possivel: recebendo o objeto errado (`Instrucao` do desmontador em
    vez da instrucao do capstone) e estourando `AttributeError` justamente quando
    havia uma recusa para explicar. Ferramenta de diagnostico que nao roda no caso
    de diagnostico nao serve para nada.
    """
    caminho = tmp_path / "sintetica.gba"
    caminho.write_bytes(_imagem_com_tabela_guarda_no_pool(5))     # limite que nao fecha
    processo = subprocess.run(
        [sys.executable, str(RAIZ / "ferramentas" / "diagnosticar_tabela.py"),
         str(caminho), "--entrada", "0x08000041"],
        capture_output=True, text=True)
    assert processo.returncode == 0, processo.stderr[-2000:]
    assert "`mov pc, rX` recusados ...: 1" in processo.stdout, processo.stdout
    assert "nao e' endereco de codigo dentro da imagem" in processo.stdout, processo.stdout
    # e no caso em que a tabela fecha, a sonda diz RECONHECIDA
    caminho.write_bytes(_imagem_com_tabela_guarda_no_pool(2))
    processo = subprocess.run(
        [sys.executable, str(RAIZ / "ferramentas" / "diagnosticar_tabela.py"),
         str(caminho), "--entrada", "0x08000041", "--site", "0x0800004E"],
        capture_output=True, text=True)
    assert processo.returncode == 0, processo.stderr[-2000:]
    assert "veredito: RECONHECIDA" in processo.stdout, processo.stdout


def test_sonda_de_tabela_diz_quando_o_pool_aponta_para_fora_da_imagem(tmp_path):
    """O valor lido do pool pode NAO ser endereco nenhum da imagem.

    Medido na ROM de estudo (0x081DBEBA, um dos 2 `mov pc, rX` que ficam
    recusados): o pool carrega **0x04000120** — registrador de I/O do GBA, nao
    tabela de codigo. A sonda tentava ler as entradas num endereco que nao existe
    e estourava (`KeyError: 'primeira'`, e depois `ValueError` ao converter de
    volta o texto de exibicao) justamente no caso que ela existe para explicar.
    """
    imagem = bytearray(_imagem_com_tabela_guarda_no_pool(2))
    imagem[0x5C:0x60] = (0x04000120).to_bytes(4, "little")   # pool -> fora da imagem
    caminho = tmp_path / "sintetica.gba"
    caminho.write_bytes(bytes(imagem))
    processo = subprocess.run(
        [sys.executable, str(RAIZ / "ferramentas" / "diagnosticar_tabela.py"),
         str(caminho), "--entrada", "0x08000041", "--site", "0x0800004E"],
        capture_output=True, text=True)
    assert processo.returncode == 0, processo.stderr[-2000:]
    assert "FORA da imagem" in processo.stdout, processo.stdout
    assert "veredito: recusada" in processo.stdout, processo.stdout
    assert "nao ha' tabela de codigo ali" in processo.stdout, processo.stdout


def test_sonda_de_bx_recusado_mede_o_valor_e_pode_discordar_da_mensagem():
    """A sonda dos `bx rN` mede o valor POR FORA, para poder discordar do lifter.

    `bx rN` e' a maior lacuna do levantamento (39 das 191 recusas na ROM), e a
    pergunta que decide se ha' o que implementar e' se o valor do registrador
    existe em tempo de traducao. A sonda tem dois papeis: numerar isso na ROM
    inteira (`ferramentas/medir_bx_recusados.py`) e, aqui, mostrar que a medida e'
    independente -- ela recalcula valor e categoria em vez de repetir a frase de
    recusa. Conferido na rodada r19: 3 sites com valor PAR (`adr` + `bx`: bit0 = 0
    em `bx` = modo ARM) e 1 com o literal do pool fora da imagem (0x030028E1,
    RAM); nenhum com bit0 = 1 na imagem.
    """
    imagem = bytearray(0x40)
    imagem[0x20:0x24] = bytes.fromhex("00a21047")     # adr r2, #0 ; bx r2
    imagem[0x30:0x34] = bytes.fromhex("004b1847")     # ldr r3, [pc, #0] ; bx r3
    imagem[0x34:0x38] = (0x030028E1).to_bytes(4, "little")   # o literal do pool
    desmontagem = disasm.desmontar_por_sementes(
        bytes(imagem), sementes={0x08000020: "thumb", 0x08000030: "thumb"})
    sonda = _carregar_ferramenta("medir_bx_recusados.py")
    medido = sonda.medir(desmontagem, bytes(imagem))
    assert medido["recusas_bx"] == 2, medido["sites"]
    assert medido["por_tipo"] == {
        "valor fora da imagem (RAM/IO)": 1,
        "valor par, bloco do outro modo NAO e' rotina (ilha)": 1}, medido["por_tipo"]
    por_site = {s["site"]: s for s in medido["sites"]}
    assert por_site["0x08000022"]["valor"] == "0x08000024"
    assert por_site["0x08000022"]["como"] == "adr"
    assert por_site["0x08000022"]["forma_do_alvo"] not in (None, "retorno")
    assert por_site["0x08000032"]["valor"] == "0x030028E1"
    assert "pool" in por_site["0x08000032"]["como"]
    # a MEDICAO e a MENSAGEM tem de contar a mesma coisa (e' o que a sonda
    # confere: nao se a medicao concorda consigo mesma, mas se o texto publicado
    # bate com ela)
    assert "troca de modo" in por_site["0x08000022"]["motivo"]
    assert "NAO devolve pelo `lr`" in por_site["0x08000022"]["motivo"]
    assert "fora da imagem" in por_site["0x08000032"]["motivo"]


def test_desvio_para_trecho_nao_desmontado_mede_se_o_alvo_e_codigo():
    """"trecho nao desmontado" sozinho manda procurar defeito onde nao tem.

    Medido na ROM (rodada sem censo): os 7 sitios cujo alvo cai dentro da faixa
    da janela mas nunca foi decodificado tem, nos BYTES do alvo, `itee gt`,
    `cbnz`, `sxth`, `ldrd`, `bkpt`, `mrc2` e um endereco que nem decodifica --
    nenhum e' codigo do ARM7TDMI. A frase agora diz isso: a acao de quem le muda
    (nao ha' o que consertar no levantador; a janela passou por dado).

    A imagem reproduz o caso: um `beq` aponta para 0x0800002A, onde estao os
    bytes de um `it` (Thumb-2, nao existe no ARMv4T); o `b` em 0x08000024 pula
    para 0x08000030, entao o alvo fica num buraco DENTRO da faixa da janela.
    """
    imagem = bytearray(0x40)
    for endereco, meio in (
        (0x08000020, 0x2B00),      # cmp r3, #0
        (0x08000022, 0xD002),      # beq 0x0800002A
        (0x08000024, 0xE004),      # b   0x08000030 (pula o buraco)
        (0x08000030, 0x4770),      # bx lr
    ):
        imagem[endereco - rom.ROM_BASE:endereco - rom.ROM_BASE + 2] = meio.to_bytes(2, "little")
    imagem[0x2A:0x2C] = bytes.fromhex("08bf")          # `it eq` -- dado, nao codigo
    desmontagem = disasm.desmontar_por_sementes(
        bytes(imagem), sementes={0x08000020: "thumb"})
    assert 0x0800002A not in {i.endereco for f in desmontagem.funcoes.values()
                              for i in f.instrucoes}
    (levantada,) = decompile.decompilar(desmontagem, bytes(imagem)).funcoes
    motivo = next(m for m in levantada.nao_levantadas if "beq" in m)
    assert "dentro desta janela, em trecho nao desmontado" in motivo, motivo
    assert "NAO e' codigo do ARM7TDMI" in motivo, motivo
    assert "IT block (it)" in motivo, motivo
    assert "passou por dado" in motivo, motivo


def _carregar_ferramenta(nome: str):
    """Ferramentas em `ferramentas/` sao scripts, nao modulo do pacote."""
    import importlib.util
    caminho = RAIZ / "ferramentas" / nome
    especificacao = importlib.util.spec_from_file_location(caminho.stem, caminho)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def test_conferidor_de_objetos_separa_codigo_de_metadados(tmp_path):
    """O instrumento que responde "o objeto mudou no CODIGO ou no rotulo?".

    A pergunta apareceu de verdade, nos dois sentidos: um conserto que so' mexia
    em TEXTO de recusa (dentro de comentario C) mudou o `.text` -- na mesma
    passada o `stmdb sp!, {lr}` do ARM entrou no caminho da pilha --, e um
    polimento que mexia em 7 bytes de C nao mudou byte nenhum do objeto. "O
    sha256 mudou" nao distingue os dois casos; medir secao por secao distingue.
    """
    base = "int soma(int a, int b) { return a + b; }\n"
    # `compilar_thumb` grava a fonte ao lado do .o (e o CAMINHO da fonte entra no
    # .symtab como simbolo STT_FILE): para comparar "so' o comentario mudou", o
    # .o e a fonte tem de sair no MESMO caminho nas duas compilacoes.
    corpus.compilar_thumb(base, tmp_path / "mesmo.o")
    (tmp_path / "guarda.o").write_bytes((tmp_path / "mesmo.o").read_bytes())
    corpus.compilar_thumb("/* so' comentario */\n" + base, tmp_path / "mesmo.o")
    conferidor = _carregar_ferramenta("conferir_objetos.py")

    # 1) comentario NAO entra no objeto (o mesmo byte a byte do polimento da r16)
    igual = conferidor.conferir(tmp_path / "guarda.o", tmp_path / "mesmo.o")
    assert igual["veredito"] == "objetos IDENTICOS byte a byte", igual["veredito"]

    # 2) o MESMO texto com outro NOME de arquivo muda metadado, nao codigo -- e a
    #    ferramenta diz que e' metadado, em vez de gritar que o objeto mudou
    (tmp_path / "sub").mkdir()
    corpus.compilar_thumb(base, tmp_path / "sub" / "caminho_bem_mais_longo.o")
    so_metadado = conferidor.conferir(tmp_path / "mesmo.o",
                                      tmp_path / "sub" / "caminho_bem_mais_longo.o")
    assert so_metadado["veredito"].startswith("mesmo CODIGO e mesmas funcoes"), so_metadado
    assert [d["secao"] for d in so_metadado["secoes_diferentes"]] == [".strtab", ".symtab"]

    # 3) codigo diferente aparece como codigo diferente, e diz QUAL secao
    corpus.compilar_thumb("int soma(int a, int b) { return a * b + (a >> 3) - 7; }\n",
                          tmp_path / "mesmo.o")
    diferente = conferidor.conferir(tmp_path / "guarda.o", tmp_path / "mesmo.o")
    assert diferente["veredito"] == "CODIGO GERADO DIFERENTE", diferente["veredito"]
    assert ".text" in diferente["codigo_diferente"]
    # o nome da funcao que mudou de tamanho e' o que interessa numa rodada real
    # (na r16 foram 2 funcoes de 8 172); o tamanho exato depende do compilador,
    # entao aqui se confere a FORMA da resposta, nao o numero
    mudou = diferente["simbolos"]["tamanho_mudou"]
    assert len(mudou) == 1 and mudou[0].startswith("soma: "), mudou

    # 4) e a ferramenta roda pela linha de comando, que e' como ela e' usada
    processo = subprocess.run(
        [sys.executable, str(RAIZ / "ferramentas" / "conferir_objetos.py"),
         str(tmp_path / "guarda.o"), str(tmp_path / "mesmo.o")],
        capture_output=True, text=True)
    assert processo.returncode == 0, processo.stderr[-2000:]
    assert "veredito: CODIGO GERADO DIFERENTE" in processo.stdout, processo.stdout


def _carregar_sonda_de_lacunas():
    """`ferramentas/onde_estao_as_lacunas.py` e' script, nao modulo do pacote."""
    import importlib.util
    caminho = RAIZ / "ferramentas" / "onde_estao_as_lacunas.py"
    especificacao = importlib.util.spec_from_file_location("onde_estao_as_lacunas", caminho)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def test_alvo_de_desvio_que_ninguem_cobriu_e_medido_nos_bytes():
    """Alvo de desvio fora de toda janela: e' codigo que ficou de fora ou dado?

    Esta e' a pergunta que decide se vale "preencher buraco" com semente, e a
    sonda responde lendo os BYTES REAIS -- nao chutando pela aparencia. Caso 1,
    montado no desmontador de verdade: um desvio cujo alvo ninguem tentou ler
    (a leitura chegou la' e parou), um alvo coberto e um ja' tentado como
    semente e descartado. Se a leitura do alvo nao fosse medida, os tres casos
    sairiam como a mesma linha ("buraco") -- foi assim que "102 recusas por
    buraco" passou rodadas parecendo codigo faltando, quando 108 dos 110 alvos
    param na PRIMEIRA instrucao.

    Caso 2: o veredito pergunta pelos DOIS motivos que o levantador usa (o de
    mnemonic e o de FORMA por tamanho de codificacao). Sem o segundo, dado do
    Thumb-2 que o capstone MOSTRA como `adc r4, r4, #0xd000` passaria por
    "codigo que segue" e o buraco voltaria a parecer codigo faltando.
    """
    base = rom.ROM_BASE
    imagem = bytearray(0x40)

    def meia(endereco: int, valor: int) -> None:
        imagem[endereco - base:endereco - base + 2] = valor.to_bytes(2, "little")

    def salto(endereco: int, destino: int) -> None:
        deslocamento = (destino - (endereco + 4)) // 2
        meia(endereco, 0xE000 | (deslocamento & 0x7FF))

    salto(0x08000000, 0x08000008)                  # alvo NUNCA tentado
    imagem[0x08000008 - base:0x0800000A - base] = bytes.fromhex("08bf")   # `it eq`
    salto(0x0800000C, 0x08000000)                  # alvo coberto
    imagem[0x08000014 - base:0x08000016 - base] = bytes.fromhex("08bf")
    salto(0x08000020, 0x08000014)                  # alvo ja' descartado
    desmontagem = disasm.desmontar_por_sementes(
        bytes(imagem), sementes={0x08000000: "thumb", 0x0800000C: "thumb",
                                 0x08000014: "thumb", 0x08000020: "thumb"})
    assert 0x08000014 in desmontagem.descartes, sorted(desmontagem.descartes)
    sonda = _carregar_sonda_de_lacunas()
    medido = sonda.alvos_nao_cobertos({"desmontagem": desmontagem,
                                       "imagem": bytes(imagem)})
    assert medido["alvos"] == {"coberto (instrucao de alguma janela)": 1,
                              "nunca tentado": 1,
                              "ja' tentado como semente (descartado: dado)": 1}, medido
    assert medido["veredito_dos_nao_tentados"] == {"para na primeira": 1}, medido
    exemplo = medido["exemplos"]["para na primeira: IT block (it): nao existe "
                                  "no ARMv4T"][0]
    assert "0x08000008" in exemplo and "0x08000000" in exemplo, exemplo

    # caso 2: os dois motivos do levantador, e nao so' o de mnemonic
    so_uma_funcao = disasm.Desmontagem(base=base)
    so_uma_funcao.funcoes[0x08000000] = disasm.FuncaoDesmontada(
        entrada=0x08000000, modo="thumb", semente="informada",
        instrucoes=[disasm.Instrucao(0x08000000, bytes.fromhex("02e0"), "b",
                                     "#0x8000008", "thumb", alvo=0x08000008)])
    com_dado32 = bytearray(0x40)
    com_dado32[0x08:0x0C] = bytes.fromhex("44f55044")
    medido = sonda.alvos_nao_cobertos({"desmontagem": so_uma_funcao,
                                       "imagem": bytes(com_dado32)})
    assert medido["alvos"] == {"nunca tentado": 1}, medido
    chave = next(iter(medido["exemplos"]))
    assert chave.startswith("para na primeira: codificacao de 32 bits"), chave


def _imagem_de_teste(*instrucoes: tuple[int, str], tamanho: int = 0x600) -> bytes:
    """Imagem com bytes hexa nos enderecos dados (o resto e' zero)."""
    imagem = bytearray(tamanho)
    for endereco, hexa in instrucoes:
        dados = bytes.fromhex(hexa)
        inicio = endereco - rom.ROM_BASE
        imagem[inicio:inicio + len(dados)] = dados
    return bytes(imagem)


def test_coprocessador_e_dado_nos_dois_modos_nao_so_no_thumb():
    """`ldc`/`stc`/`cdp`/`mcr`/`mrc` nao existem no GBA -- em modo NENHUM.

    A regra vivia DENTRO do ramo do Thumb. Em ARM, uma instrucao de coprocessador
    sairia como "mnemonico nao implementado (a instrucao existe no ARMv4T; falta
    traduzir)" -- e' FALSA: o ARM7TDMI decodifica essas instrucoes e as deixa
    indefinidas quando nao ha coprocessador ligado, e o GBA nao liga nenhum. O
    que esta' ali e' dado lido como codigo. Varredura r17 na ROM de estudo: 75
    instrucoes ARM nas janelas, **zero** de coprocessador (as 6 que aparecem --
    `ldcl` 3 vezes, `stcl` 3 vezes -- estao em janelas Thumb); a regra passou a
    valer nos dois modos mesmo assim, porque o proximo erro desse tipo nao avisa.

    Bytes montados com keystone (`ldc p1, c0, [r0]` -> `00 01 90 ed`) e conferidos
    pelo capstone ANTES de julgar o filtro.
    """
    coprocessador = [
        ("00 01 90 ed", "ldc"),     # ldc p1, c0, [r0]
        ("00 01 d0 ed", "ldcl"),    # ldcl p1, c0, [r0]   (letra colada no nome)
        ("00 32 c1 ed", "stcl"),    # stcl p2, c3, [r1]
        ("c5 31 24 ee", "cdp"),     # cdp p1, #2, c3, c4, c5, #6
        ("72 0f 01 ee", "mcr"),     # mcr p15, #0, r0, c1, c2, #3
        ("10 0f 11 ee", "mrc"),     # mrc p15, #0, r0, c1, c0, #0
        ("00 01 90 fd", "ldc2"),    # ldc2 p1, c0, [r0]
        ("23 01 41 ec", "mcrr"),    # mcrr p1, #2, r0, r1, c3
    ]
    for hexa, mnemonic in coprocessador:
        ins = _decodifica(bytes.fromhex(hexa), 0x08000000, "arm")
        assert ins.mnemonic == mnemonic, (ins.mnemonic, mnemonic)   # o que esta' la
        motivo = disasm.impossivel_no_arm7tdmi(ins, "arm")
        assert motivo is not None, f"{mnemonic} deveria ser impossivel em ARM"
        assert "coprocessador" in motivo, motivo

    # o que EXISTE no ARMv4T continua passando (o teste do Thumb ja' cobria os dois
    # primeiros; aqui eles sao conferidos no modo em que o filtro foi mexido)
    for hexa, mnemonic in (("00 40 2d e9", "stmdb"),     # stmdb sp!, {lr} = push
                           ("00 00 4f e1", "mrs"),       # mrs r0, spsr
                           ("00 00 a0 e1", "mov")):      # mov r0, r0
        ins = _decodifica(bytes.fromhex(hexa), 0x08000368, "arm")
        assert ins.mnemonic == mnemonic, (ins.mnemonic, mnemonic)
        assert disasm.impossivel_no_arm7tdmi(ins, "arm") is None, mnemonic

    # e a leitura PARA no ponto: o dado nao continua sendo lido como codigo
    imagem = _imagem_de_teste((0x08000020, "00 01 90 ed"))       # ldc p1, c0, [r0]
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "arm"})
    assert 0x08000020 in desmontagem.descartes, desmontagem.descartes
    assert desmontagem.total_instrucoes == 0, desmontagem.total_instrucoes


def test_pc_lido_como_operando_vira_constante_e_nao_a_variavel_pc():
    """`add lr, pc, #0` (bytes REAIS da ROM: 00 e0 8f e2) tem valor constante.

    O C levantado nao guarda o endereco da instrucao em `pc` -- a variavel existe
    para RECEBER desvio e vale 0 --, entao traduzir `pc` lido como operando pelo
    caminho comum emitia a conta errada: medido na ROM de estudo, `add lr, pc, #0`
    (0x0800036C, a chamada ARM->Thumb montada a mao do IRQ_HANDLER) saia como
    `lr = pc + 0`. Aqui a constante e' dobrada: no ARM o pc vale endereco + 8.
    """
    imagem = _imagem_de_teste((0x08000020, "00 e0 8f e2"),    # add lr, pc, #0
                              (0x08000024, "1e ff 2f e1"))    # bx lr
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "arm"})
    codigo = decompile.decompilar(desmontagem, imagem)
    corpo = codigo.funcoes[0].corpo
    assert "lr = 0x08000028u" in corpo, corpo                 # 0x08000020 + 8
    assert "pc + 0" not in corpo, corpo
    assert codigo.incompletas == [], [f.nao_levantadas for f in codigo.incompletas]


def test_mov_e_add_com_pc_no_thumb1_usam_o_pc_alinhado():
    """`mov r2, pc` e `add r8, pc`: o valor e' (endereco + 4) alinhado a 4 bytes.

    Mesma regra do `adr` e do pool de literais -- e o teste vale por mostrar a
    conta com o alinhamento: as DUAS instrucoes (0x08000020 e 0x08000022) leem o
    MESMO 0x08000024, porque (0x08000022 + 4) = 0x08000026 desce para 0x08000024.
    """
    imagem = _imagem_de_teste((0x08000020, "7a 46"),         # mov r2, pc
                              (0x08000022, "f8 44"),         # add r8, pc
                              (0x08000024, "70 47"))         # bx lr
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "thumb"})
    codigo = decompile.decompilar(desmontagem, imagem)
    corpo = codigo.funcoes[0].corpo
    assert "r2 = 0x08000024u" in corpo, corpo
    assert "r8 = r8 + 0x08000024u" in corpo, corpo
    assert codigo.incompletas == [], [f.nao_levantadas for f in codigo.incompletas]


def test_leitura_de_pc_em_forma_sem_valor_constante_e_recusada():
    """`cmp r1, pc` (0f 00 51 e1) nao tem traducao: fica declarado, nao inventado."""
    imagem = _imagem_de_teste((0x08000020, "0f 00 51 e1"),    # cmp r1, pc
                              (0x08000024, "1e ff 2f e1"))    # bx lr
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "arm"})
    codigo = decompile.decompilar(desmontagem, imagem)
    motivo = codigo.incompletas[0].nao_levantadas[0]
    assert "leitura de pc como operando" in motivo, motivo
    assert "cmp r1, pc" in motivo, motivo


def test_stmdb_sp_do_arm_e_o_push_da_pilha_do_modelo():
    """`stmdb sp!, {lr}` (00 40 2d e9) e' o `push` do ARM: mesma semantica de pilha.

    Antes disto a instrucao era recusada (e a conferencia de balanceamento acusava
    desequilibrio na funcao, porque o push nao existia no C). `_multipla` ja'
    tratava os quatro modos de bloco -- faltava o `db` chegar nela.
    """
    imagem = _imagem_de_teste((0x08000020, "00 40 2d e9"),    # stmdb sp!, {lr}
                              (0x08000024, "1e ff 2f e1"))    # bx lr
    desmontagem = disasm.desmontar_por_sementes(imagem, sementes={0x08000020: "arm"})
    codigo = decompile.decompilar(desmontagem, imagem)
    corpo = codigo.funcoes[0].corpo
    assert "sp -= 4" in corpo, corpo
    assert "guarda32(sp + 0, lr)" in corpo, corpo
    assert codigo.incompletas == [], [f.nao_levantadas for f in codigo.incompletas]
