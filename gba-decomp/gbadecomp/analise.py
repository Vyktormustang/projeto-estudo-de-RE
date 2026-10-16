"""Medicao reproduzivel de um levantamento: todo numero afirmado sai daqui.

Por que este modulo existe: os numeros publicados (README, evidencias) vinham de
um script descartavel, fora do repositorio. Medicao que ninguem pode repetir nao
e medicao -- e foi exatamente essa falta que deixou passar, numa rodada inteira,
83 enderecos contados como "funcoes levantadas" sem uma linha de C: o resumo
dizia 7 634 com C e as listas diziam 7 311 completas + 406 parciais, e ninguem
viu a diferenca porque a conta nao estava escrita em lugar nenhum.

Aqui cada numero tem UMA definicao, no codigo:

  com corpo .......... o C da funcao tem pelo menos uma linha
  completa ........... nenhuma instrucao ficou de fora
  parcial ............ tem C, mas com lacuna marcada dentro do proprio C
  sem corpo .......... so prototipo: nao ha C para ler
  descartado ......... tentou-se como funcao e nao havia instrucao valida do
                       ARM7TDMI ali (nao entra na conta de funcoes)

As categorias sao exaustivas e mutuamente exclusivas, e o codigo RECUSA devolver
o resultado se a soma nao fechar (ver `_classificar`). Sem isso, a proxima
inconsistencia passa do mesmo jeito.
"""

from __future__ import annotations

import collections
import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import conferir_bytes as conferir_mod
from . import decompile as decompile_mod
from . import disasm as disasm_mod
from . import rom as rom_mod


def achar_zig(explicito: str | None = None) -> str | None:
    """zig cc: caminho dado, no PATH, ou o pacote ziglang do ambiente virtual."""
    if explicito:
        return explicito
    achado = shutil.which("zig")
    if achado:
        return achado
    try:
        import ziglang  # type: ignore
    except ImportError:
        return None
    candidato = Path(ziglang.__file__).parent / "zig"
    return str(candidato) if candidato.exists() else None


def compilar(caminho_c: Path, zig: str | None) -> dict:
    """Compila o C levantado para ARM7TDMI e devolve o que aconteceu.

    Isto NAO prova semantica: prova que o C gerado e C valido para o alvo e que
    nenhuma funcao ficou sem declaracao. E o unico teste que pega rotulo
    inexistente, alvo de chamada sem prototipo e erro de sintaxe no C levantado.
    """
    if not zig:
        return {"compila": None, "motivo": "zig nao encontrado: compilacao nao testada"}
    with tempfile.TemporaryDirectory() as tmp:
        objeto = Path(tmp) / "levantado.o"
        proc = subprocess.run(
            [zig, "cc", "-target", "thumb-freestanding-eabi", "-mcpu=arm7tdmi",
             "-Os", "-nostdlib", "-ffreestanding", "-c", str(caminho_c), "-o", str(objeto)],
            capture_output=True, text=True, timeout=1800)
        erros = [l for l in proc.stderr.splitlines() if "error:" in l]
        return {
            "compila": proc.returncode == 0,
            "codigo_de_saida": proc.returncode,
            "n_erros": len(erros),
            "primeiros_erros": erros[:10],
            "bytes_objeto": objeto.stat().st_size if objeto.exists() else 0,
            "comando": f"{zig} cc -target thumb-freestanding-eabi -mcpu=arm7tdmi "
                       f"-Os -nostdlib -ffreestanding -c",
        }


def _classificar(codigo: decompile_mod.CodigoC) -> dict:
    """Categorias exaustivas. Recusa devolver numero que nao fecha."""
    com_corpo = [f for f in codigo.funcoes if f.tem_corpo]
    sem_corpo = [f for f in codigo.funcoes if not f.tem_corpo]
    completas = [f for f in codigo.funcoes if f.completa]
    parciais = [f for f in com_corpo if not f.completa]

    total = len(codigo.funcoes)
    if len(com_corpo) + len(sem_corpo) != total:
        raise RuntimeError("contagem inconsistente: corpo + sem corpo != total")
    if len(parciais) + len([f for f in completas if f.tem_corpo]) != len(com_corpo):
        raise RuntimeError("contagem inconsistente: completas + parciais != com corpo")

    # INVARIANTE DE HONESTIDADE: funcao dita completa e sem corpo nenhum seria
    # um numero inflado no resumo -- foi o bug das 83 entradas fantasma.
    mentirosas = [f for f in codigo.funcoes if f.completa and not f.tem_corpo]
    if mentirosas:
        raise RuntimeError(
            f"{len(mentirosas)} funcoes saem como COMPLETAS sem nenhuma linha de C "
            f"(ex.: 0x{mentirosas[0].endereco:08X}) -- o resumo mentiria")

    return {
        "funcoes": total,
        "com_c_para_ler": len(com_corpo),
        "completas": len([f for f in completas if f.tem_corpo]),
        "parciais": len(parciais),
        "sem_corpo": len(sem_corpo),
        "percentual_com_c": round(100.0 * len(com_corpo) / total, 2) if total else 0.0,
        "funcoes_com_lacuna": len([f for f in codigo.funcoes
                                   if not f.completa and f.tem_corpo]),
    }


def _recusas(codigo: decompile_mod.CodigoC) -> tuple[dict, dict]:
    """Histograma do que ficou de fora, por mnemonico e por motivo."""
    por_mnemonico: collections.Counter = collections.Counter()
    por_motivo: collections.Counter = collections.Counter()
    for f in codigo.funcoes:
        for item in f.nao_levantadas:
            # formato: "0x08001234 mov pc, r0: <motivo>"
            corpo, _, motivo = item.partition(": ")
            partes = corpo.split(" ", 1)
            if len(partes) == 2:
                por_mnemonico[partes[1].split(",")[0].split(" ")[0]] += 1
            por_motivo[motivo[:90]] += 1
    return (dict(por_mnemonico.most_common()),
            {k: v for k, v in por_motivo.most_common(12)})


@dataclass
class Medicao:
    """Tudo o que se afirma em numero sobre uma rodada, com a origem de cada um."""

    rom: str = ""
    sha256: str = ""
    bytes_rom: int = 0
    censo: str | None = None
    censo_funcoes: int = 0
    boot: dict = field(default_factory=dict)
    completo: dict = field(default_factory=dict)
    levantamento: dict = field(default_factory=dict)
    recusas_mnemonico: dict = field(default_factory=dict)
    recusas_motivo: dict = field(default_factory=dict)
    descartes_por_semente: dict = field(default_factory=dict)
    descartes: list = field(default_factory=list)
    linhas_c: int = 0
    bytes_c: int = 0
    conferencia: dict = field(default_factory=dict)
    compilacao: dict | None = None
    caminho_c: str | None = None

    def texto(self) -> str:
        linhas = [
            f"ROM .......: {self.rom}",
            f"sha256 .....: {self.sha256}",
            f"censo ......: {self.censo or '(nenhum)'} -- {self.censo_funcoes} funcoes",
            "",
        ]
        if self.boot:
            linhas.append("descoberta so a partir do vetor de reset:")
            linhas.append(f"  {self.boot.get('funcoes')} funcoes, "
                          f"{self.boot.get('instrucoes')} instrucoes, "
                          f"{self.boot.get('arestas')} arestas, "
                          f"{self.boot.get('descartes')} descartes")
            linhas.append(f"  no censo: {self.boot.get('no_censo')} | "
                          f"fora do censo: {self.boot.get('fora_do_censo')}")
        if self.completo:
            linhas.append("descoberta com o censo como semente:")
            linhas.append(f"  {self.completo.get('funcoes')} funcoes, "
                          f"{self.completo.get('instrucoes')} instrucoes, "
                          f"{self.completo.get('arestas')} arestas, "
                          f"{self.completo.get('descartes')} descartes")
            linhas.append(f"  censo coberto: {self.completo.get('no_censo')}/"
                          f"{self.censo_funcoes} | fora do censo: "
                          f"{self.completo.get('fora_do_censo')}")
        if self.levantamento:
            lev = self.levantamento
            linhas += [
                "",
                "levantamento (categorias exaustivas, conferidas por assercao):",
                f"  com C para ler .: {lev.get('com_c_para_ler')}/{lev.get('funcoes')} "
                f"({lev.get('percentual_com_c')}%)",
                f"     completas ...: {lev.get('completas')}",
                f"     parciais ....: {lev.get('parciais')} (lacuna marcada dentro do C)",
                f"  sem corpo ......: {lev.get('sem_corpo')}",
                f"  C ..............: {self.linhas_c} linhas / {self.bytes_c} bytes",
            ]
        if self.descartes_por_semente:
            linhas += ["", f"descartes ({len(self.descartes)} enderecos tentados como "
                           f"funcao que nao tinham codigo do ARM7TDMI):"]
            for semente, n in sorted(self.descartes_por_semente.items(),
                                     key=lambda x: -x[1]):
                linhas.append(f"  {n:5d}  vindos de {semente}")
        if self.recusas_mnemonico:
            linhas += ["", "instrucoes recusadas (o lifter nao inventa traducao):"]
            for mnemonico, n in list(self.recusas_mnemonico.items())[:12]:
                linhas.append(f"  {n:5d}  {mnemonico}")
        if self.conferencia:
            c = self.conferencia
            linhas += ["", f"conferencia byte a byte: {c.get('identicas')}/{c.get('total')} "
                           f"({c.get('taxa')}%) remontam identicas"]
        if self.compilacao:
            cp = self.compilacao
            if cp.get("compila") is None:
                linhas.append(f"compilacao: NAO testada -- {cp.get('motivo')}")
            else:
                linhas.append(f"compilacao: {'OK' if cp['compila'] else 'FALHOU'} "
                              f"({cp.get('n_erros')} erros, objeto de "
                              f"{cp.get('bytes_objeto')} bytes)")
        return "\n".join(linhas)

    def para_json(self) -> str:
        return json.dumps(self.__dict__, indent=2, ensure_ascii=False, sort_keys=False)

    def resumo_json(self) -> dict:
        return self.__dict__


def _descoberta(rom: rom_mod.GbaRom, sementes: dict[int, str],
                enderecos_censo: set[int]) -> tuple[dict, object]:
    desmontagem = disasm_mod.desmontar_por_sementes(rom.data, sementes=sementes or None)
    dentro = [a for a in desmontagem.funcoes if a in enderecos_censo]
    return {
        "funcoes": len(desmontagem.funcoes),
        "instrucoes": desmontagem.total_instrucoes,
        "arestas": len(desmontagem.arestas()),
        "descartes": len(desmontagem.descartes),
        "no_censo": len(dentro) if enderecos_censo else None,
        "fora_do_censo": (len(desmontagem.funcoes) - len(dentro)) if enderecos_censo else None,
    }, desmontagem


def medir(caminho_rom: str | Path, censo: str | Path | None = None,
          caminho_c: str | Path | None = None, zig: str | None = None,
          conferir: bool = True) -> Medicao:
    """Mede uma rodada inteira na ROM indicada. Sem atalho e sem estimativa."""
    caminho_rom = Path(caminho_rom)
    rom = rom_mod.GbaRom(caminho_rom)
    dados = rom.data
    medicao = Medicao(
        rom=str(caminho_rom),
        sha256=hashlib.sha256(dados).hexdigest(),
        bytes_rom=len(dados),
        censo=str(censo) if censo else None,
    )

    enderecos_censo: set[int] = set()
    sementes: dict[int, str] = {}
    nomes: dict[int, str] = {}
    if censo:
        spans = rom_mod.carregar_funcoes_csv(censo)
        medicao.censo_funcoes = len(spans)
        for span in spans:
            enderecos_censo.add(span.addr)
            sementes.setdefault(span.addr, span.mode or "thumb")
            if span.name:
                nomes[span.addr] = span.name

    medicao.boot, _ = _descoberta(rom, {}, enderecos_censo)
    medicao.completo, desmontagem = _descoberta(rom, sementes, enderecos_censo)

    codigo = decompile_mod.decompilar(desmontagem, dados, nomes=nomes or None)
    medicao.levantamento = _classificar(codigo)
    medicao.recusas_mnemonico, medicao.recusas_motivo = _recusas(codigo)

    # Descartes: quantos vieram de ponteiro de pool, de chamada ou de semente.
    contagem: collections.Counter = collections.Counter()
    for d in desmontagem.descartes.values():
        if d.semente.startswith("ponteiro de pool"):
            contagem["ponteiro de pool"] += 1
        elif d.semente.startswith("chamada"):
            contagem["chamada (bl)"] += 1
        elif d.semente.startswith("salto"):
            contagem["salto"] += 1
        else:
            contagem[d.semente.split(" ")[0] or "?"] += 1
    medicao.descartes_por_semente = dict(contagem.most_common())
    medicao.descartes = [
        {"entrada": f"0x{d.entrada:08X}", "modo": d.modo, "semente": d.semente,
         "motivo": d.motivo, "bytes": d.bytes_.hex(" ")}
        for d in sorted(desmontagem.descartes.values(), key=lambda x: x.entrada)]

    texto_c = codigo.texto()
    medicao.linhas_c = len(texto_c.splitlines())
    medicao.bytes_c = len(texto_c.encode("utf-8"))
    if caminho_c:
        destino = Path(caminho_c)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto_c, encoding="utf-8")
        medicao.caminho_c = str(destino)
        medicao.compilacao = compilar(destino, achar_zig(zig))

    if conferir:
        resultado = conferir_mod.conferir(desmontagem, dados)
        medicao.conferencia = {
            "total": resultado.total,
            "identicas": resultado.identicas,
            "taxa": round(resultado.taxa, 3),
            "divergentes": len(resultado.divergentes),
            "nao_remontadas": len(resultado.falhas_de_sintaxe),
            "divergentes_exemplos": [
                {"endereco": f"0x{e:08X}", "asm": asm, "binario": orig, "remontado": novo}
                for e, asm, orig, novo in resultado.divergentes[:5]],
        }
    return medicao
