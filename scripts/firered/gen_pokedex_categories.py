#!/usr/bin/env python3
"""Gera as páginas de *habitat* da Pokédex (`gDexCategories`) para as 1025 espécies.

Por que existe
--------------
A ficha da Pokédex do FireRed é aberta por **categoria de habitat** — as nove
páginas de `src/data/pokemon/pokedex_categories.h` (Grassland, Forest, Waters
Edge, Sea, Cave, Mountain, Rough Terrain, Urban, Rare). Cada página guarda até
4 espécies e a lista de páginas de cada categoria é fixa no código.

Essa tabela continuou com as **386 espécies vanilla** depois da E1, e isso tem
consequência visível: ao capturar uma espécie Gen 4-9 o jogo chama
`DexScreen_LookUpCategoryBySpecies(915)`; ela percorre a tabela, não encontra a
espécie e devolve "não achei" **sem** tocar em `category`/`pageNum`/
`categoryCursorPosInPage`. A tela então desenha outra espécie (na captura do
Lechonk apareceu `No800`, nome `??????????` e `HT/WT ???`).

O conserto é gerar as páginas que faltam. **As 386 vanilla não mudam de página
nem de ordem** — as novas entram no fim, em páginas novas de até 4.

De onde vem o habitat das espécies novas
---------------------------------------
Não existe habitat oficial depois da Gen 3 (o campo da PokéAPI é nulo de #387 em
diante). Então o gerador **aprende o critério do próprio FireRed**: conta, entre
as 386 espécies vanilla, com que frequência cada tipo aparece em cada categoria
e usa um classificador ingênuo (Naive Bayes com suavização de Laplace) para
escolher a categoria das novas. É uma **HIPÓTESE** — reproduz o estilo da dex
original, não um dado oficial:

    P(categoria) x P(tipo1 | categoria) x P(tipo2 | categoria)

Empate é desfeito pela ordem das categorias (Grassland primeiro), então a saída
é determinística.

Uso
---
    python3 scripts/firered/gen_pokedex_categories.py --self-test
    python3 scripts/firered/gen_pokedex_categories.py --pokefirered /tmp/pokefirered --write
    python3 scripts/firered/gen_pokedex_categories.py --pokefirered /tmp/pokefirered --check

O `--check` falha se o clone divergir do gerado (ninguém editou à mão).
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import tempfile
from pathlib import Path

CATEGORIAS = [
    "GrasslandPkmn", "ForestPkmn", "WatersEdgePkmn", "SeaPkmn", "CavePkmn",
    "MountainPkmn", "RoughTerrainPkmn", "UrbanPkmn", "RarePkmn",
]

MARCA = "pokedex_categories"
INICIO = f"// === GERADO: gen 4-9 (scripts/firered/gen_pokedex_categories.py) [{MARCA}] ==="
FIM = f"// === FIM DO GERADO [{MARCA}] ==="

REL_CATS = "src/data/pokemon/pokedex_categories.h"
REL_GERADO = "src/data/pokemon/pokedex_categories_gen4_9.h"
REL_SPECIES = "include/constants/species.h"
REL_INFO = "src/data/pokemon/species_info.h"
REL_INFO_G49 = "src/data/pokemon/species_info_gen4_9.h"

PRIMEIRA_NOVA = 387
ULTIMA = 1025
TAM_PAGINA = 4

# --------------------------------------------------------------------------- #
# leitura do clone
# --------------------------------------------------------------------------- #


def ler_species(pf: Path) -> dict[int, str]:
    """número da dex nacional -> constante (`SPECIES_LECHONK`)."""
    texto = (pf / REL_SPECIES).read_text(errors="replace")
    saida: dict[int, str] = {}
    for nome, num in re.findall(r"^#define\s+(SPECIES_\w+)\s+(\d+)\s*$", texto, re.M):
        n = int(num)
        if n and n not in saida:
            saida[n] = nome
    return saida


def ler_tipos(pf: Path) -> dict[str, tuple[str, ...]]:
    """constante da espécie -> tipos, lendo os dois `species_info`.

    O FireRed guarda `.types = {TYPE_GRASS, TYPE_POISON}`; o segundo tipo pode
    ser `TYPE_NONE` (espécie de um tipo só).
    """
    tipos: dict[str, tuple[str, ...]] = {}
    for rel in (REL_INFO, REL_INFO_G49):
        texto = (pf / rel).read_text(errors="replace")
        for bloco in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*\{(.*?)\n    \},", texto, re.S):
            m = re.search(r"\.types\s*=\s*\{([^}]*)\}", bloco.group(2))
            if not m:
                continue
            lista = tuple(t.strip() for t in m.group(1).split(",") if t.strip())
            tipos[bloco.group(1)] = tuple(t for t in lista if t != "TYPE_NONE")
    return tipos


def paginas_vanilla(texto: str) -> dict[str, list[list[str]]]:
    """Categoria -> lista de páginas (cada página é a lista de espécies).

    Só olha o que está **antes** do primeiro marcador gerado: rodar o gerador
    duas vezes parte sempre da mesma tabela vanilla.
    """
    if INICIO in texto:
        texto = texto[:texto.index(INICIO)]
    paginas: dict[str, list[list[str]]] = {}
    for m in re.finditer(r"static const u16 sDexCategory_(\w+)\[\] = \{(.*?)\};", texto, re.S):
        # `sDexCategory_GrasslandPkmn_Page3` -> categoria `GrasslandPkmn`
        nome = re.sub(r"_Page\d+$", "", m.group(1))
        corpo = m.group(2)
        spp = re.findall(r"(SPECIES_\w+)", corpo)
        if spp:
            paginas.setdefault(nome, []).append(spp)
    return paginas


def paginas_por_categoria(texto: str) -> dict[str, list[str]]:
    """Categoria -> nomes das páginas na ordem em que a tabela as lista."""
    saida: dict[str, list[str]] = {}
    for m in re.finditer(r"static const struct PokedexCategoryPage sDexCategory_(\w+)\[\] = \{(.*?)\};", texto, re.S):
        saida[m.group(1)] = re.findall(r"DEX_CATEGORY\((\w+)\)", m.group(2))
    return saida


# --------------------------------------------------------------------------- #
# classificação (Naive Bayes sobre as 386 vanilla)
# --------------------------------------------------------------------------- #


def treinar(paginas: dict[str, list[list[str]]], tipos: dict[str, tuple[str, ...]],
            categorias: list[str]) -> dict:
    """Conta P(categoria) e P(tipo | categoria) nas espécies vanilla."""
    total_por_cat = {c: 0 for c in categorias}
    por_tipo = {c: {} for c in categorias}
    for cat in categorias:
        for pagina in paginas.get(cat, []):
            for sp in pagina:
                total_por_cat[cat] += 1
                for t in tipos.get(sp, ()):
                    por_tipo[cat][t] = por_tipo[cat].get(t, 0) + 1
    n_total = sum(total_por_cat.values())
    return {"total": total_por_cat, "por_tipo": por_tipo, "n": n_total,
            "tipos": sorted({t for c in categorias for t in por_tipo[c]})}


def classificar(modelo: dict, tipos_sp: tuple[str, ...], categorias: list[str]) -> str:
    """argmax de log P(cat) + soma log P(tipo | cat), com Laplace."""
    melhor, melhor_nota = categorias[0], -math.inf
    alfa = 1.0
    n_tipos = max(1, len(modelo["tipos"]))
    for cat in categorias:
        n_cat = modelo["total"][cat]
        # Laplace também na prior: categoria vazia (acontece no self-test) não
        # pode virar log(0)
        nota = math.log((n_cat + 1.0) / (modelo["n"] + len(categorias)))
        for t in tipos_sp:
            conta = modelo["por_tipo"][cat].get(t, 0)
            nota += math.log((conta + alfa) / (n_cat + alfa * n_tipos))
        if nota > melhor_nota + 1e-12:
            melhor, melhor_nota = cat, nota
    return melhor


def atribuir(tipos: dict[str, tuple[str, ...]], species: dict[int, str],
             vanilla: dict[str, list[list[str]]], categorias: list[str]) -> dict[str, list[str]]:
    """Categoria -> espécies novas (da #387 até #1025, em ordem de dex)."""
    modelo = treinar(vanilla, tipos, categorias)
    novas: dict[str, list[str]] = {c: [] for c in categorias}
    for num in range(PRIMEIRA_NOVA, ULTIMA + 1):
        sp = species.get(num)
        if not sp:
            continue
        novas[classificar(modelo, tipos.get(sp, ()), categorias)].append(sp)
    return novas


# --------------------------------------------------------------------------- #
# páginas novas
# --------------------------------------------------------------------------- #


def dividir(especies: list[str], tamanho: int = TAM_PAGINA) -> list[list[str]]:
    return [especies[i:i + tamanho] for i in range(0, len(especies), tamanho)]


def novas_paginas(vanilla: dict[str, list[list[str]]], novas: dict[str, list[str]],
                  categorias: list[str]) -> dict[str, list[tuple[str, list[str]]]]:
    """Categoria -> [(nome da página, espécies)] só das páginas criadas agora.

    A numeração continua a do vanilla (`_Page18`, `_Page19`, ...) para ninguém
    precisar procurar onde a página nova entrou.
    """
    saida: dict[str, list[tuple[str, list[str]]]] = {}
    for cat in categorias:
        inicio = len(vanilla.get(cat, [])) + 1
        paginas = dividir(novas.get(cat, []))
        saida[cat] = [(f"{cat}_Page{inicio + i}", p) for i, p in enumerate(paginas)]
    return saida


def render_gerado(saida: dict[str, list[tuple[str, list[str]]]]) -> str:
    linhas = [INICIO,
              "/* Páginas de habitat das espécies Gen 4-9 (#387-#1025).",
              " * As páginas vanilla ficam no arquivo principal, intocadas; estas",
              " * entram no fim de cada categoria. Habitat = HIPÓTESE derivada dos",
              " * tipos com o critério aprendido das 386 espécies vanilla.",
              " * Gerado por scripts/firered/gen_pokedex_categories.py — não editar. */",
              ""]
    for cat in CATEGORIAS:
        for nome, spp in saida.get(cat, []):
            linhas.append(f"static const u16 sDexCategory_{nome}[] = {{")
            linhas.extend(f"    {s}," for s in spp)
            linhas.append("};")
            linhas.append("")
    linhas.append(FIM)
    return "\n".join(linhas) + "\n"


def aplicar(texto: str, saida: dict[str, list[tuple[str, list[str]]]]) -> str:
    """Devolve o `pokedex_categories.h` com o include e as páginas novas.

    Idempotente: remove o bloco gerado antigo antes de inserir o novo.
    """
    if INICIO in texto:
        ini = texto.index(INICIO)
        fim = texto.index(FIM, ini) + len(FIM)
        texto = texto[:ini] + texto[fim:].lstrip("\n")
        texto = re.sub(r"\n{3,}", "\n\n", texto)

    # as linhas `DEX_CATEGORY(alguma_PageN)` geradas ficam marcadas com um
    # comentário no fim da linha; some com elas antes de reinserir.
    texto = re.sub(r"\n *DEX_CATEGORY\(\w+_Page\d+\), *// GERADO", "", texto)

    # 1. include do arquivo gerado, antes do macro DEX_CATEGORY
    alvo = "#define DEX_CATEGORY(name)"
    if alvo not in texto:
        raise SystemExit("não achei o macro DEX_CATEGORY")
    # include relativo ao próprio arquivo: o Makefile só passa `-iquote include`
    texto = texto.replace(alvo, f'{INICIO}\n#include "{Path(REL_GERADO).name}"\n{FIM}\n\n{alvo}', 1)

    # 2. uma linha DEX_CATEGORY por página nova, no fim da lista da categoria
    for cat in CATEGORIAS:
        paginas = saida.get(cat, [])
        if not paginas:
            continue
        m = re.search(r"(static const struct PokedexCategoryPage sDexCategory_" + cat + r"\[\] = \{\n)((?:.*\n)*?)\};", texto)
        if not m:
            raise SystemExit(f"não achei a lista de páginas de {cat}")
        extra = "".join(f"    DEX_CATEGORY({nome}), // GERADO\n" for nome, _ in paginas)
        bloco = m.group(1) + m.group(2) + extra
        texto = texto[:m.start()] + bloco + "};" + texto[m.end():]
    return texto


# --------------------------------------------------------------------------- #
# conferência
# --------------------------------------------------------------------------- #


def contar_paginas(texto: str) -> dict[str, int]:
    return {c: len(p) for c, p in paginas_por_categoria(texto).items()}


def especies_no_gerado(texto_gerado: str) -> list[str]:
    return re.findall(r"^\s+(SPECIES_\w+),", texto_gerado, re.M)


def conferir(pf: Path) -> list[str]:
    """Lista de divergências entre o clone e o que o gerador produziria."""
    erros: list[str] = []
    cats = pf / REL_CATS
    gerado = pf / REL_GERADO
    if not gerado.exists():
        return [f"{REL_GERADO} não existe"]
    texto = cats.read_text(errors="replace")
    if INICIO not in texto:
        return [f"{REL_CATS} não tem o bloco gerado"]
    vanilla = paginas_vanilla(texto)
    species = ler_species(pf)
    tipos = ler_tipos(pf)
    novas = atribuir(tipos, species, vanilla, CATEGORIAS)
    saida = novas_paginas(vanilla, novas, CATEGORIAS)
    if gerado.read_text(errors="replace") != render_gerado(saida):
        erros.append(f"{REL_GERADO} diverge do gerado")
    if aplicar(texto, saida) != texto:
        erros.append(f"{REL_CATS} diverge do gerado")

    # cobertura: cada espécie 1..1025 aparece exatamente uma vez
    tudo = [s for cat in CATEGORIAS for p in paginas_por_categoria(texto).get(cat, [])
            for s in []]
    del tudo
    vistas: list[str] = []
    for m in re.finditer(r"static const u16 sDexCategory_\w+\[\] = \{(.*?)\};",
                         texto + "\n" + gerado.read_text(errors="replace"), re.S):
        vistas.extend(re.findall(r"SPECIES_\w+", m.group(1)))
    esperado = [species[n] for n in range(1, ULTIMA + 1) if n in species]
    faltando = [s for s in esperado if s not in vistas]
    repetida = sorted({s for s in vistas if vistas.count(s) > 1})
    if faltando:
        erros.append(f"{len(faltando)} espécies fora de qualquer página (ex.: {faltando[:4]})")
    if repetida:
        erros.append(f"espécies repetidas: {repetida[:4]}")
    return erros


# --------------------------------------------------------------------------- #
# self-test
# --------------------------------------------------------------------------- #

CATS_TOY = """static const u16 sDexCategory_GrasslandPkmn_Page1[] = {
    SPECIES_RATTATA,
    SPECIES_RATICATE,
};
static const u16 sDexCategory_WatersEdgePkmn_Page1[] = {
    SPECIES_PSYDUCK,
};
static const struct PokedexCategoryPage sDexCategory_GrasslandPkmn[] = {
    DEX_CATEGORY(GrasslandPkmn_Page1),
};
static const struct PokedexCategoryPage sDexCategory_WatersEdgePkmn[] = {
    DEX_CATEGORY(WatersEdgePkmn_Page1),
};
#define DEX_CATEGORY(name){sDexCategory_##name, NELEMS(sDexCategory_##name)}
"""


def self_test() -> int:
    ok = 0
    # 1. páginas vanilla são lidas na ordem
    v = paginas_vanilla(CATS_TOY)
    assert v["GrasslandPkmn"] == [["SPECIES_RATTATA", "SPECIES_RATICATE"]], v
    assert v["WatersEdgePkmn"] == [["SPECIES_PSYDUCK"]], v
    ok += 1

    # 2. Naive Bayes aprende o óbvio: tipo Água vai para WatersEdge
    tipos = {"SPECIES_RATTATA": ("TYPE_NORMAL",), "SPECIES_RATICATE": ("TYPE_NORMAL",),
             "SPECIES_PSYDUCK": ("TYPE_WATER",), "SPECIES_NOVO": ("TYPE_WATER",)}
    modelo = treinar(v, tipos, CATEGORIAS)
    assert classificar(modelo, ("TYPE_WATER",), CATEGORIAS) == "WatersEdgePkmn"
    assert classificar(modelo, ("TYPE_NORMAL",), CATEGORIAS) == "GrasslandPkmn"
    ok += 1

    # 3. divisão em páginas de 4
    p = dividir([f"S{i}" for i in range(9)])
    assert [len(x) for x in p] == [4, 4, 1], p
    ok += 1

    # 4. página nova continua a numeração
    npg = novas_paginas(v, {"GrasslandPkmn": ["SPECIES_A", "SPECIES_B"]}, CATEGORIAS)
    assert [n for n, _ in npg["GrasslandPkmn"]] == ["GrasslandPkmn_Page2"], npg
    ok += 1

    # 5. aplicar duas vezes dá o mesmo texto (idempotente)
    saida = render_gerado(npg)
    uma = aplicar(CATS_TOY, npg)
    duas = aplicar(uma, npg)
    assert uma == duas, "aplicar não é idempotente"
    assert saida.count("SPECIES_A") == 1
    ok += 1

    # 6. as páginas vanilla sobrevivem intactas
    assert paginas_vanilla(uma) == v, paginas_vanilla(uma)
    assert uma.count("DEX_CATEGORY(GrasslandPkmn_Page2),") == 1, uma
    ok += 1

    # 7. `--check` acusa divergência
    with tempfile.TemporaryDirectory() as d:
        pf = Path(d)
        (pf / "src/data/pokemon").mkdir(parents=True)
        (pf / "include/constants").mkdir(parents=True)
        (pf / REL_CATS).write_text(uma)
        (pf / REL_GERADO).write_text(saida)
        (pf / REL_SPECIES).write_text("#define SPECIES_RATTATA 19\n#define SPECIES_A 900\n")
        (pf / REL_INFO).write_text("")
        (pf / REL_INFO_G49).write_text("")
        assert conferir(pf), "conferir() não acusou nada num clone sem nothing"
    ok += 1

    print(f"self-test ok: {ok} casos (leitura, Naive Bayes, páginas, idempotência, "
          f"vanilla intacta, conferência)")
    return ok


# --------------------------------------------------------------------------- #


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", type=Path)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        self_test()
        return 0
    if not a.pokefirered:
        ap.error("informe --pokefirered ou --self-test")
    pf: Path = a.pokefirered
    if not (pf / REL_CATS).exists():
        raise SystemExit(f"{pf} não parece um clone do pokefirered")

    if a.check:
        erros = conferir(pf)
        for e in erros:
            print("ERRO:", e)
        print("pokedex_categories ok" if not erros else f"{len(erros)} divergência(s)")
        return 1 if erros else 0

    texto = (pf / REL_CATS).read_text(errors="replace")
    vanilla = paginas_vanilla(texto)
    species = ler_species(pf)
    tipos = ler_tipos(pf)
    novas = atribuir(tipos, species, vanilla, CATEGORIAS)
    saida = novas_paginas(vanilla, novas, CATEGORIAS)

    total = sum(len(spp) for c in CATEGORIAS for _, spp in saida[c])
    print(f"espécies novas distribuídas: {total}")
    for cat in CATEGORIAS:
        print(f"  {cat:20s} {len(novas[cat]):4d} espécies, "
              f"{len(saida[cat]):3d} páginas novas (vanilla tinha {len(vanilla.get(cat, []))})")

    novo_texto = aplicar(texto, saida)
    conteudo_gerado = render_gerado(saida)
    if a.write:
        (pf / REL_GERADO).write_text(conteudo_gerado)
        if novo_texto != texto:
            (pf / REL_CATS).write_text(novo_texto)
        print(f"escrito: {REL_GERADO} e {REL_CATS}")
        return 0

    iguais = ((pf / REL_GERADO).exists() and (pf / REL_GERADO).read_text() == conteudo_gerado
              and novo_texto == texto)
    print("clone já está igual ao gerado" if iguais else "clone DIFERE do gerado (use --write)")
    return 0 if iguais else 1


if __name__ == "__main__":
    sys.exit(main())
