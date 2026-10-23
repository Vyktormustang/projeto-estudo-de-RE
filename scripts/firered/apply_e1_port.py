#!/usr/bin/env python3
"""Aplica o port da E1 (1025 espécies) num clone limpo do pret/pokefirered.

A E1 não acrescenta dados de espécie — só abre espaço: renumera as constantes pela
Pokédex Nacional, remove os 25 buracos `OLD_UNOWN` que existiam só para ocupar
posição, e reacomoda o save (Pokédex maior).

Idempotente: rodar duas vezes não estraga nada.

Uso
---
    git clone --depth 1 https://github.com/pret/pokefirered /tmp/pokefirered
    python3 scripts/firered/apply_e1_port.py --pokefirered /tmp/pokefirered
    python3 scripts/firered/apply_e1_port.py --pokefirered /tmp/pokefirered --check

Depois:
    cd /tmp/pokefirered && make -j2 MODERN=1 CC1_DAEMONS=2
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# Arquivos de dados que têm uma linha por espécie (a entrada vira lixo quando o
# buraco OLD_UNOWN deixa de existir, então a linha é removida).
DADOS_COM_OLD_UNOWN = [
    "src/data/pokemon/pokedex_orders.h",
    "src/data/pokemon/species_info.h",
    "src/data/pokemon/level_up_learnset_pointers.h",
    "src/data/pokemon/tmhm_learnsets.h",
    "src/data/pokemon_graphics/back_pic_coordinates.h",
    "src/data/pokemon_graphics/front_pic_coordinates.h",
    "src/data/pokemon_graphics/back_pic_table.h",
    "src/data/pokemon_graphics/front_pic_table.h",
    "src/data/pokemon_graphics/palette_table.h",
    "src/data/pokemon_graphics/shiny_palette_table.h",
    "src/data/pokemon_graphics/footprint_table.h",
    "src/data/text/species_names.h",
    "src/pokemon_icon.c",
    "src/pokemon.c",
]

CRY_NOVO = """u16 SpeciesToCryId(u16 species)
{
    // 1..251 (Kanto + Johto): o id de cry acompanha o id de especie.
    if (species < SPECIES_TREECKO)
        return species;
    // 252..386 (Hoenn): tabela propria, indexada a partir de Treecko.
    if (species < NUM_SPECIES)
        return sHoennSpeciesIdToCryId[species - SPECIES_TREECKO];
    // Formas (Unown etc.) usam o cry do Unown.
    return SPECIES_UNOWN - 1;
}
"""


def ler(p: Path) -> str:
    return p.read_text()


def gravar(p: Path, s: str) -> bool:
    """Grava só se mudou. Devolve True se mudou."""
    atual = ler(p)
    if atual == s:
        return False
    p.write_text(s)
    return True


def remover_macro_old_unown(texto: str) -> str:
    """Remove o bloco `#define OLD_UNOWN_SPECIES_INFO \\ ... }` inteiro."""
    linhas = texto.split("\n")
    saida, dentro = [], False
    for linha in linhas:
        if linha.startswith("#define OLD_UNOWN_SPECIES_INFO"):
            dentro = True
            continue
        if dentro:
            # o bloco termina na primeira linha que não é continuação
            if not linha.rstrip().endswith("\\"):
                dentro = False
            continue
        saida.append(linha)
    return "\n".join(saida)


def remover_linhas(texto: str, padrao: str) -> tuple[str, int]:
    novas, n = [], 0
    for linha in texto.split("\n"):
        if padrao in linha:
            n += 1
            continue
        novas.append(linha)
    return "\n".join(novas), n


def aplicar(poke: Path, check: bool) -> int:
    mudancas: list[str] = []

    def rel(p: Path) -> str:
        return str(p.relative_to(poke))

    # 1) constantes reescritas pelo gerador
    cmd = [sys.executable, str(AQUI / "gen_species_constants.py"),
           "--pokefirered", str(poke), "--write"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        return 1
    mudancas.append("constantes: species.h / pokedex.h / species_names.h")

    # 2) species_info.h — o macro do Unown falso sai inteiro
    p = poke / "src/data/pokemon/species_info.h"
    s = remover_macro_old_unown(ler(p))
    s, n = remover_linhas(s, "OLD_UNOWN")
    if gravar(p, s):
        mudancas.append(f"species_info.h: macro OLD_UNOWN removido (+{n} linhas)")

    # 3) pokemon.c — SpeciesToCryId antes de apagar as linhas de dados
    p = poke / "src/pokemon.c"
    s = ler(p)
    ini = s.find("u16 SpeciesToCryId(u16 species)")
    if ini != -1 and CRY_NOVO not in s:
        fim = s.index("// Spots can be drawn on Spinda", ini)
        s = s[:ini] + CRY_NOVO + "\n" + s[fim:]
        if gravar(p, s):
            mudancas.append("pokemon.c: SpeciesToCryId reescrito para a nova numeração")

    # 4) menu2.c — as formas do Unown passam a usar as constantes de forma
    p = poke / "src/menu2.c"
    s = ler(p)
    s = s.replace("species = SPECIES_OLD_UNOWN_EMARK;", "species = SPECIES_UNOWN_EMARK;")
    s = s.replace("species = SPECIES_OLD_UNOWN_QMARK;", "species = SPECIES_UNOWN_QMARK;")
    s = s.replace(
        '// Not actually "old" given these were introduced in Gen 3,\n'
        "// but they're used as equivalents here alongside the other OLD_UNOWN\n", "")
    if gravar(p, s):
        mudancas.append("menu2.c: formas do Unown apontam para SPECIES_UNOWN_*")

    # 5) demais tabelas — a linha do placeholder sai
    for nome in DADOS_COM_OLD_UNOWN:
        p = poke / nome
        s, n = remover_linhas(ler(p), "OLD_UNOWN")
        if gravar(p, s):
            mudancas.append(f"{nome}: -{n} linhas OLD_UNOWN")

    # 6) cry de Hoenn: o bloco agora começa em 252, não em 277
    p = poke / "src/data/pokemon/cry_ids.h"
    s = ler(p).replace("#define HOENN_MON_SPECIES_START 277", "#define HOENN_MON_SPECIES_START 252")
    if gravar(p, s):
        mudancas.append("cry_ids.h: HOENN_MON_SPECIES_START 277 -> 252")

    # 7) save: a Pokédex cresce 154 B; o espaço sai dos fillers
    p = poke / "include/global.h"
    s = ler(p)
    antes = s
    s = s.replace("    /*0xB20*/ u8 filler_B20[0x400];",
                  "    /*0xB20*/ u8 filler_B20[0x400 - 154]; // -154: Pokedex de 412 -> 1025 especies")
    s = s.replace("    /*0x3A94*/ u8 unused_3A94[64];",
                  "    /*0x3A94*/ u8 unused_3A94[60]; // -4: seen1/seen2 cresceram junto com a Pokedex")
    if s != antes:
        gravar(p, s)
        mudancas.append("global.h: filler_B20 -154 B, unused_3A94 -4 B (save comporta a Pokedex nova)")

    # 8) checagem final
    if check:
        sobrou = subprocess.run(
            ["grep", "-rl", "OLD_UNOWN", "src/", "include/constants/"],
            cwd=poke, capture_output=True, text=True).stdout.split()
        # pokedex.h ainda tem as constantes HOENN_DEX_OLD_UNOWN_* (são de Hoenn, ficam)
        sobrou = [x for x in sobrou if "pokedex.h" not in x]
        if sobrou:
            print("AINDA COM OLD_UNOWN:", sobrou)
            return 1

    if not mudancas:
        print("nada a fazer: port já aplicado")
    else:
        print(f"{len(mudancas)} mudanças:")
        for m in mudancas:
            print("  -", m)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--check", action="store_true", help="falha se sobrar referência a OLD_UNOWN")
    a = ap.parse_args()
    poke = Path(a.pokefirered)
    if not (poke / "Makefile").exists():
        print(f"não parece um clone do pokefirered: {poke}")
        return 1
    return aplicar(poke, a.check)


if __name__ == "__main__":
    sys.exit(main())
