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

from gbadecomp import corpus, decompile, disasm, reconstruir, rom, verificador  # noqa: E402


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
    # 0xDF00 = SWI (chamada de sistema), que este levantador nao traduz;
    # 0x4770 = bx lr, que encerra a funcao.
    imagem = (bytes(0xC0) + bytes.fromhex("00009fe5") + bytes.fromhex("10ff2fe1")
              + (0x080000CD).to_bytes(4, "little")
              + bytes.fromhex("00df" + "7047") + b"\xff" * 64)
    desmontagem = disasm.desmontar_por_sementes(imagem)
    assert len(desmontagem.funcoes) == 1
    codigo = decompile.decompilar(desmontagem, imagem)
    assert codigo.incompletas, "SWI deveria constar como nao levantada"
    assert "mnemonico nao implementado" in codigo.incompletas[0].nao_levantadas[0]


def test_desmontador_para_em_byte_invalido_sem_inventar():
    """Byte que nao e instrucao valida encerra a varredura e fica registrado --
    o desmontador nao pode 'adivinhar' o que vem depois."""
    imagem = (bytes(0xC0) + bytes.fromhex("00009fe5") + bytes.fromhex("10ff2fe1")
              + (0x080000CD).to_bytes(4, "little") + bytes.fromhex("ffff")
              + b"\xff" * 64)
    desmontagem = disasm.desmontar_por_sementes(imagem)
    funcao = next(iter(desmontagem.funcoes.values()))
    assert funcao.instrucoes == []
    assert "invalido" in funcao.terminacao


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
