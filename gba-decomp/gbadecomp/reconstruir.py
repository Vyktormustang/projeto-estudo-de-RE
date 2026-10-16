"""Pipeline completo de ida e volta: ROM -> C levantado -> ROM reconstruida.

A ideia que da valor a este modulo: um disassembler ou um decompilador so
merece confianca se o que ele produz puder ser COMPILADO E EXECUTADO e der o
mesmo resultado do original. Entao o caminho aqui e sempre o mesmo:

    binario  --disasm-->  funcoes e grafo de chamadas
             --decompile-->  C (uma instrucao por linha)
             --zig cc-->  objeto -> ELF linkado -> blob
             --empacota-->  imagem GBA
             --unicorn-->  mesma tabela de verdade contra a ROM RECONSTRUIDA

No corpus sintetico (codigo autoral com resultado conhecido) isso fecha 100%.
Num binario de terceiros sem verdade-terreno, o melhor que se pode afirmar e
"executa e produz X" -- nao "esta correto".
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import corpus as corpus_mod
from . import decompile as decompile_mod
from . import disasm as disasm_mod
from . import rom as rom_mod
from . import verificador as verificador_mod

STUB_BOOT = bytes.fromhex("00009fe5") + bytes.fromhex("10ff2fe1")


@dataclass
class ResultadoRodada:
    """Tudo o que uma rodada produziu, sem maquiagem."""

    desmontagem: disasm_mod.Desmontagem
    codigo: decompile_mod.CodigoC
    relatorio_original: verificador_mod.RelatorioEmulacao | None = None
    relatorio_levantado: verificador_mod.RelatorioEmulacao | None = None
    caminho_c: str | None = None
    caminho_rom_levantado: str | None = None
    tamanho_levantado: int | None = None
    erros: list[str] = field(default_factory=list)

    def resumo(self) -> str:
        linhas = ["=== rodada de engenharia reversa ==="]
        linhas.append(f"funcoes descobertas .....: {len(self.desmontagem.funcoes)}")
        linhas.append(f"instrucoes desmontadas ..: {self.desmontagem.total_instrucoes}")
        linhas.append(f"arestas de chamada ......: {len(self.desmontagem.arestas())}")
        linhas.append(f"funcoes levantadas p/ C .: {len(self.codigo.completas)}"
                      f" (incompletas: {len(self.codigo.incompletas)})")
        if self.tamanho_levantado:
            linhas.append(f"codigo C compilado ......: {self.tamanho_levantado} bytes")
        if self.relatorio_original:
            r = self.relatorio_original
            linhas.append(f"verdade-terreno no original ....: {r.aprovados}/{r.total}")
        if self.relatorio_levantado:
            r = self.relatorio_levantado
            linhas.append(f"verdade-terreno no levantado ...: {r.aprovados}/{r.total}")
        if self.codigo.incompletas:
            linhas.append("funcoes que ficaram de fora do levantamento:")
            for f in self.codigo.incompletas:
                linhas.append(f"  0x{f.endereco:08X}: {'; '.join(f.nao_levantadas[:2])}")
        if self.erros:
            linhas.append("erros:")
            linhas.extend(f"  {e}" for e in self.erros)
        for aviso in self.desmontagem.avisos + self.codigo.avisos:
            linhas.append(f"aviso: {aviso}")
        return "\n".join(linhas)


def rodada_corpus(caminho_rom: str | Path | None = None,
                  diretorio: str | Path | None = None,
                  zig: str | None = None) -> ResultadoRodada:
    """Corpus sintetico: verdade-terreno conhecida nas duas pontas."""
    tmp = Path(diretorio) if diretorio else Path(tempfile.mkdtemp(prefix="gbadecomp-"))
    tmp.mkdir(parents=True, exist_ok=True)
    caminho_rom = Path(caminho_rom) if caminho_rom else tmp / "corpus.gba"

    corpus = corpus_mod.construir(caminho_rom, zig=zig)
    imagem = caminho_rom.read_bytes()
    resultado = _rodada_comum(imagem, tmp, zig=zig, nomes={
        f.addr: f"f_{f.nome}" for f in corpus.funcoes})
    resultado.relatorio_original = verificador_mod.verificar_verdade_terreno(corpus)
    resultado.caminho_rom_levantado = _verificar_levantado(
        resultado, tmp, corpus, zig=zig)
    return resultado


def rodada_binario(caminho_rom: str | Path, diretorio: str | Path | None = None,
                   sementes: dict[int, str] | None = None,
                   zig: str | None = None) -> ResultadoRodada:
    """ROM de terceiros: sem verdade-terreno, entao nao ha como afirmar acerto."""
    tmp = Path(diretorio) if diretorio else Path(tempfile.mkdtemp(prefix="gbadecomp-"))
    tmp.mkdir(parents=True, exist_ok=True)
    rom = rom_mod.GbaRom(caminho_rom)
    if sementes is None:
        sementes = {rom_mod.ROM_BASE: "arm"}   # vetor de boot: 0x08000000 executa em ARM
    imagem = Path(caminho_rom).read_bytes()
    resultado = _rodada_comum(imagem, tmp, sementes=sementes, zig=zig)
    resultado.erros.append(
        "ROM de terceiros: nao existe verdade-terreno conhecida, entao NAO foi "
        "possivel afirmar se o C levantado esta correto -- so foi possivel "
        "compila-lo e registrar o que ele executa")
    return resultado


def _rodada_comum(imagem: bytes, tmp: Path, sementes: dict[int, str] | None = None,
                  nomes: dict[int, str] | None = None,
                  zig: str | None = None) -> ResultadoRodada:
    desmontagem = disasm_mod.desmontar_por_sementes(imagem, sementes=sementes)
    codigo = decompile_mod.decompilar(desmontagem, imagem, nomes=nomes)
    caminho_c = tmp / "levantado.c"
    caminho_c.write_text(codigo.texto(), encoding="utf-8")
    return ResultadoRodada(desmontagem=desmontagem, codigo=codigo,
                           caminho_c=str(caminho_c))


def _verificar_levantado(resultado: ResultadoRodada, tmp: Path, corpus,
                         zig: str | None = None) -> str | None:
    """Compila o C levantado, empacota como ROM e roda a verdade-terreno nele."""
    obj, elf, binario = tmp / "levantado.o", tmp / "levantado.elf", tmp / "levantado.bin"
    try:
        corpus_mod.compilar_thumb(Path(resultado.caminho_c).read_text(), obj,
                                  opt="-Os", zig=zig)
        corpus_mod.linkar_thumb(obj, elf, base=corpus_mod.CODE_BASE, zig=zig)
        proc = subprocess.run([zig or corpus_mod.achar_zig(), "objcopy", "-O", "binary",
                               str(elf), str(binario)], capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"objcopy: {proc.stderr[-800:]}")
    except RuntimeError as exc:
        resultado.erros.append(f"o C levantado nao compilou/linkou: {exc}")
        return None

    blob = binario.read_bytes()
    resultado.tamanho_levantado = len(blob)
    imagem = (bytes(0xC0) + STUB_BOOT + (corpus_mod.CODE_BASE | 1).to_bytes(4, "little")
              + blob + b"\xFF" * 0x1000)
    destino = tmp / "levantado.gba"
    destino.write_bytes(imagem)

    # a verdade-terreno e a MESMA: o que muda e a imagem onde ela roda
    funcoes = [
        corpus_mod.FuncaoCorpus(nome=nome[2:], addr=valor & ~1, tamanho=tamanho,
                                modo="thumb", fonte_linha=0)
        for nome, valor, tamanho in corpus_mod._simbolos_funcao(elf)
        if nome.startswith("f_")
    ]
    espelho = corpus_mod.Corpus(rom_path=str(destino), sha256="", total_funcoes=len(funcoes),
                                funcoes=funcoes, comando_compilacao="", compilador="",
                                c_fonte="")
    resultado.relatorio_levantado = verificador_mod.verificar_verdade_terreno(espelho)
    return str(destino)
