#!/usr/bin/env python3
"""E7: estende as 4 ordens da Pokédex (A-Z, tipo, altura, peso) para 1025.

O problema
----------
`src/data/pokemon/pokedex_orders.h` tem quatro arrays de **386** entradas
(`gPokedexOrder_Alphabetical`, `_Type`, `_Height`, `_Weight`), mas
`DexScreen_CountMonsInOrderedList()` percorre `NUM_SPECIES - 1` (1025) e
`NATIONAL_DEX_COUNT` (1025). Ou seja: **lê 639 posições além do fim de cada
array**, ~1,2 KB de memória alheia por array, e usa o que encontrar como número
de dex — que acaba em `gSpeciesNames[]` e em `DexScreen_GetSetPokedexFlag()`.

O compilador avisa e ninguém vê:

    src/pokedex_screen.c:1455: warning: iteration 386 invokes undefined
    behavior [-Waggressive-loop-optimizations]

O bug é da E1 (que subiu `NUM_SPECIES`) e só apareceu na E7 porque o arquivo foi
recompilado. Não trava o jogo na partida, mas abrir a Pokédex nos modos A-Z,
TIPO, MAIS LEVE ou MENOR passa a ler lixo.

A correção
----------
Completar os arrays com as espécies 387-1025, **inserindo cada uma na posição
certa** segundo a chave daquela ordem (nome, tipo, altura, peso). As 386 do
FireRed ficam exatamente onde estavam: a entrada nova entra antes da primeira
entrada vanilla com chave maior.

As chaves saem do RHH (mesma fonte da E2): `.speciesName`, `.types`, `.height`
(decímetros) e `.weight` (hectogramas). Foi conferido que os arrays vanilla do
FireRed estão **perfeitamente ordenados** por essas chaves (0 inversões em 385
comparações, nas quatro ordens) — é isso que torna a inserção válida.

Uso
---
    python3 gen_pokedex_orders.py --self-test
    python3 gen_pokedex_orders.py --pokefirered /tmp/pokefirered --reference /tmp/fre --write
    python3 gen_pokedex_orders.py --pokefirered /tmp/pokefirered --reference /tmp/fre --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import gen_species_data as gen  # noqa: E402

ARQUIVO = "src/data/pokemon/pokedex_orders.h"
PRIMEIRA_NOVA = 387          # 1-386 são FireRed vanilla

# ordem dos tipos no jogo (a mesma do FireRed e do RHH até o 18)
TIPOS = ["NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG", "GHOST",
         "STEEL", "MYSTERY", "FIRE", "WATER", "GRASS", "ELECTRIC", "PSYCHIC", "ICE",
         "DRAGON", "DARK", "FAIRY"]

ORDENS = {
    # array: (prefixo da constante, chave de ordenação)
    "gPokedexOrder_Alphabetical": ("NATIONAL_DEX_", "nome"),
    "gPokedexOrder_Type": ("SPECIES_", "tipo"),
    "gPokedexOrder_Height": ("NATIONAL_DEX_", "altura"),
    "gPokedexOrder_Weight": ("NATIONAL_DEX_", "peso"),
}

MARCA_INI = "// E7: inicio ordens-da-dex (gerado por gen_pokedex_orders.py)"
MARCA_FIM = "// E7: fim ordens-da-dex"


# --------------------------------------------------------------------------- #
# chaves de ordenação (do RHH)
# --------------------------------------------------------------------------- #
RE_NOME_TXT = re.compile(r'_\(\s*"([^"]*)"\s*\)')
RE_MON_TIPOS = re.compile(r"MON_TYPES\(([^)]*)\)")


class Dados:
    """Chaves de ordenação por nome de espécie, com as macros do RHH resolvidas."""

    def __init__(self, ref: Path):
        self.blocos = gen.carregar_referencia(ref)
        self.macros = gen.tabela_macros(ref)
        self._cache: dict[str, dict | None] = {}

    def _expandir(self, valor: str, prof: int = 4) -> str:
        v = valor.strip()
        for _ in range(prof):
            if v in self.macros:
                v = self.macros[v].strip()
            else:
                break
        return v

    def _numero(self, valor: str) -> int | None:
        v = self._expandir(valor)
        return int(v) if v.lstrip("-").isdigit() else None

    def tipos(self, nome: str) -> list[str]:
        b = gen.bloco_da_especie(nome, self.blocos)
        if not b:
            return []
        bruto = self._expandir(b.get("types", ""))
        m = RE_MON_TIPOS.search(bruto)
        dentro = m.group(1) if m else bruto.strip("{} ")
        saida: list[str] = []
        for t in dentro.split(","):
            t = t.strip().replace("TYPE_", "")
            if t and t not in saida:
                saida.append(t)
        return saida

    def chaves(self, nome: str) -> dict | None:
        if nome in self._cache:
            return self._cache[nome]
        b = gen.bloco_da_especie(nome, self.blocos)
        saida = None
        if b:
            m = RE_NOME_TXT.search(b.get("speciesName", ""))
            tipos = self.tipos(nome)
            if m and tipos:
                saida = {
                    "nome": m.group(1),
                    "tipo": (TIPOS.index(tipos[0]) if tipos[0] in TIPOS else len(TIPOS),
                             TIPOS.index(tipos[1]) if len(tipos) > 1 and tipos[1] in TIPOS
                             else len(TIPOS)),
                    "altura": self._numero(b.get("height", "")) or 0,
                    "peso": self._numero(b.get("weight", "")) or 0,
                }
        self._cache[nome] = saida
        return saida


# --------------------------------------------------------------------------- #
# ler / montar / escrever
# --------------------------------------------------------------------------- #
def ids_das_especies(pf: Path) -> dict[str, int]:
    texto = (pf / "include/constants/species.h").read_text(encoding="utf-8")
    return {n[len("SPECIES_"):]: int(v) for n, v in
            re.findall(r"^#define (SPECIES_\w+) (\d+)$", texto, re.M)}


def ler_arrays(texto: str) -> dict[str, list[str]]:
    """`{array: [nome_sem_prefixo, ...]}` na ordem do arquivo (marcadores fora)."""
    saida: dict[str, list[str]] = {}
    for array in ORDENS:
        m = re.search(rf"const u16 {array}\[\]\s*=\s*\{{(.*?)\n\}};", texto, re.S)
        if not m:
            raise SystemExit(f"nao achei o array {array} em {ARQUIVO}")
        corpo = re.sub(r"//[^\n]*", "", m.group(1))
        itens = [v.strip() for v in corpo.split(",") if v.strip()]
        saida[array] = [re.sub(r"^(NATIONAL_DEX_|SPECIES_)", "", v) for v in itens]
    return saida


def montar(vanilla: dict[str, list[str]], dados, novas: list[tuple[int, str]]) -> dict[str, list[str]]:
    """Insere as novas em cada ordem mantendo a ordem relativa das vanilla."""
    saida: dict[str, list[str]] = {}
    for array, (_, chave) in ORDENS.items():
        atual = list(vanilla[array])
        chaves = {nome: dados.chaves(nome) for nome in atual}
        for _, nome in novas:                       # em ordem de dex
            k = dados.chaves(nome)
            if k is None:
                raise SystemExit(f"sem chave de ordenacao para {nome}")
            destino = len(atual)
            for i, existente in enumerate(atual):
                ke = chaves.get(existente)
                if ke is not None and ke[chave] > k[chave]:
                    destino = i
                    break
            atual.insert(destino, nome)
            chaves[nome] = k
        saida[array] = atual
    return saida


def _bloco(array: str, itens: list[str]) -> str:
    prefixo = ORDENS[array][0]
    linhas = "".join(f"    {prefixo}{item},\n" for item in itens)
    return f"{MARCA_INI}\nconst u16 {array}[] =\n{{\n{linhas}}};\n{MARCA_FIM}\n"


def gerar(texto: str, dados, ids: dict[str, int]) -> tuple[str, dict]:
    atual = ler_arrays(texto)

    # Só as vanilla entram na conta: as novas são recalculadas a cada passada,
    # o que torna o gerador idempotente (rodar 2x tem de dar o mesmo arquivo).
    vanilla: dict[str, list[str]] = {}
    for array, itens in atual.items():
        v = [n for n in itens if ids.get(n, 9999) < PRIMEIRA_NOVA]
        if len(v) != 386:
            raise SystemExit(f"{array}: esperava 386 entradas vanilla, achei {len(v)}")
        if {ids.get(n) for n in v} != set(range(1, 387)):
            raise SystemExit(f"{array}: as entradas vanilla nao sao exatamente as 1-386")
        vanilla[array] = v

    novas = sorted(((i, n) for n, i in ids.items() if i >= PRIMEIRA_NOVA))
    completas = montar(vanilla, dados, novas)

    # Troca o bloco inteiro numa passada só: o bloco antigo pode ou não estar
    # marcado (primeira execução vs. execuções seguintes). Remover os marcadores
    # antes de procurar o array apagava o próprio array na 2ª passada.
    for array in ORDENS:
        padrao = (rf"(?:{re.escape(MARCA_INI)}\n)?"
                  rf"const u16 {array}\[\]\s*=\s*\{{.*?\n\}};\n"
                  rf"(?:{re.escape(MARCA_FIM)}\n)?")
        novo, n = re.subn(padrao, lambda _m, a=array: _bloco(a, completas[a]),
                          texto, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"nao achei o array {array} para substituir")
        texto = novo
    return texto, {"por_ordem": {a: len(v) for a, v in completas.items()},
                   "novas": len(novas)}


def aplicar(pf: Path, ref: Path) -> dict:
    p = pf / ARQUIVO
    texto, st = gerar(p.read_text(encoding="utf-8", errors="surrogateescape"),
                      Dados(ref), ids_das_especies(pf))
    p.write_text(texto, encoding="utf-8", errors="surrogateescape")
    return st


def verificar(pf: Path, ref: Path) -> tuple[int, dict]:
    p = pf / ARQUIVO
    atual = p.read_text(encoding="utf-8", errors="surrogateescape")
    esperado, st = gerar(atual, Dados(ref), ids_das_especies(pf))
    return (0 if atual == esperado else 1), st


def conferir_tamanho(pf: Path) -> list[str]:
    """O que o motor realmente exige: nenhuma ordem menor que a dex."""
    texto = (pf / ARQUIVO).read_text(encoding="utf-8", errors="surrogateescape")
    erros = []
    for array, itens in ler_arrays(texto).items():
        if len(itens) != 1025:
            erros.append(f"{array}: {len(itens)} entradas (a dex vai ate 1025)")
    return erros


# --------------------------------------------------------------------------- #
# self-test
# --------------------------------------------------------------------------- #
class DadosFake:
    """Chaves sintéticas: nome 'S###', tipo/altura/peso = um único número."""

    def __init__(self, chaves: dict[str, dict]):
        self._c = chaves

    def chaves(self, nome: str):
        return self._c.get(nome)


def _texto_teste(ordem: list[str], prefixo: str = "NATIONAL_DEX_") -> str:
    corpo = "".join(f"    {prefixo}{nome},\n" for nome in ordem)
    return f"// arquivo de teste\nconst u16 gPokedexOrder_X[] =\n{{\n{corpo}}};\n"


def _arquivo_teste(ordens: dict[str, list[str]]) -> str:
    partes = ["// header de teste\n"]
    for array, (prefixo, _) in ORDENS.items():
        corpo = "".join(f"    {prefixo}{nome},\n" for nome in ordens[array])
        partes.append(f"const u16 {array}[] =\n{{\n{corpo}}};\n")
    return "\n".join(partes)


def self_test() -> int:
    ok = total = 0

    def checa(nome: str, cond: bool):
        nonlocal ok, total
        total += 1
        if cond:
            ok += 1
            print(f"  ok: {nome}")
        else:
            print(f"  FALHA: {nome}")

    ids = {f"S{i:03d}": i for i in range(1, 391)}
    # vanilla 1-386 com chave = id (as quatro ordens ficam iguais, 1..386)
    chaves = {f"S{i:03d}": {"nome": f"S{i:03d}", "tipo": i, "altura": i, "peso": i}
              for i in range(1, 387)}
    # novas com chaves que se intercalam (a inserção tem de respeitar a posição)
    intercaladas = {387: "AA", 388: "ZZZZ", 389: "S100B", 390: "S300B"}
    for i, nome in intercaladas.items():
        chaves[f"S{i:03d}"] = {"nome": nome, "tipo": i, "altura": i, "peso": i}
    dados = DadosFake(chaves)
    vanilla = {a: [f"S{i:03d}" for i in range(1, 387)] for a in ORDENS}
    texto = _arquivo_teste(vanilla)

    texto2, st = gerar(texto, dados, ids)
    arr = ler_arrays(texto2)
    checa("as 4 ordens ficam com 390 entradas",
          all(len(v) == 390 for v in arr.values()))
    checa("z abaixo de 386 (as vanilla foram mantidas em ordem)",
          [n for n in arr["gPokedexOrder_Alphabetical"] if n < "S387"] == vanilla["gPokedexOrder_Alphabetical"])
    checa("A-Z: AA entra antes de S001",
          arr["gPokedexOrder_Alphabetical"][0] == "S387")
    checa("A-Z: ZZZZ vai para o fim",
          arr["gPokedexOrder_Alphabetical"][-1] == "S388")
    checa("A-Z: S100B logo depois de S100",
          arr["gPokedexOrder_Alphabetical"].index("S389")
          == arr["gPokedexOrder_Alphabetical"].index("S100") + 1)
    checa("altura: S390 (390) fica depois de S389",
          arr["gPokedexOrder_Height"].index("S390") > arr["gPokedexOrder_Height"].index("S389"))
    checa("altura: as vanilla continuam 1..386 em ordem",
          [n for n in arr["gPokedexOrder_Height"] if int(n[1:]) < 387]
          == vanilla["gPokedexOrder_Height"])
    checa("idempotente: gerar de novo não muda nada",
          gerar(texto2, dados, ids)[0] == texto2)
    checa("relatorio conta as 4 ordens", st["por_ordem"]["gPokedexOrder_Type"] == 390)
    checa("os marcadores aparecem 2x por array (ini+fim)",
          texto2.count(MARCA_INI) == 4 and texto2.count(MARCA_FIM) == 4)

    # a lista vanilla tem de ser exatamente 1..386
    ruim = _arquivo_teste({a: [f"S{i:03d}" for i in range(1, 386)] for a in ORDENS})
    try:
        gerar(ruim, dados, ids)
        checa("385 vanilla aborta", False)
    except SystemExit:
        checa("385 vanilla aborta", True)
    duplicado = _arquivo_teste({a: [f"S{i:03d}" for i in range(1, 386)] + ["S001"]
                                for a in ORDENS})
    try:
        gerar(duplicado, dados, ids)
        checa("vanilla duplicada aborta", False)
    except SystemExit:
        checa("vanilla duplicada aborta", True)

    # chave ausente é erro, não silêncio
    sem_chave = {k: v for k, v in chaves.items() if k != "S390"}
    try:
        gerar(texto, DadosFake(sem_chave), ids)
        checa("espécie sem chave aborta", False)
    except SystemExit:
        checa("espécie sem chave aborta", True)

    print(f"\n{ok}/{total} casos ok")
    return 0 if ok == total else 1


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pokefirered", type=Path)
    ap.add_argument("--reference", type=Path)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.pokefirered or not a.reference:
        ap.error("informe --pokefirered e --reference")

    if a.write:
        st = aplicar(a.pokefirered, a.reference)
        print(f"ordens da dex: {st['novas']} especies novas inseridas; "
              + ", ".join(f"{k.split('_')[-1]}={v}" for k, v in st["por_ordem"].items()))
        return 0
    if a.check:
        erros = conferir_tamanho(a.pokefirered)
        codigo, st = verificar(a.pokefirered, a.reference)
        if codigo:
            erros.append("o arquivo nao corresponde ao gerado (rode --write)")
        for e in erros:
            print("  - " + e)
        print("ok" if not erros else "FALHOU")
        return 1 if erros else 0

    codigo, st = verificar(a.pokefirered, a.reference)
    print(f"{st['novas']} novas; " + ", ".join(f"{k.split('_')[-1]}={v}"
                                               for k, v in st["por_ordem"].items()))
    print("em dia" if not codigo else "desatualizado")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
