#!/usr/bin/env python3
"""Gera as constantes de espécie do FireRed renumeradas pela Pokédex Nacional.

Contexto
--------
O FireRed original usa uma numeração interna própria: 1–251 são Kanto + Johto, e
252–276 são buracos ocupados por `SPECIES_OLD_UNOWN_*`; só então começa Hoenn
(`SPECIES_TREECKO = 277`). Ou seja, o ID interno não é o número da Pokédex.

Como todas as tabelas por espécie do FireRed usam inicializador designado
(`[SPECIES_BULBASAUR] = ...`), mudar o número da constante não desalinha dado
nenhum — a tabela se reorganiza na compilação. Então renumeramos tudo para
`ID == número da Pokédex Nacional (1…1025)`.

Regras
------
* Nomes de constante do pokefirered são preservados (dado e código apontam por nome).
* Nomes das espécies 387–1025 vêm do repositório de referência (RHH expansion).
* `SPECIES_EGG` continua sendo `NUM_SPECIES`, como no FireRed.
* `SPECIES_OLD_UNOWN_*` deixa de existir (eram buracos na numeração).

Uso
---
    python3 scripts/firered/gen_species_constants.py --self-test
    python3 scripts/firered/gen_species_constants.py \
        --pokefirered /tmp/pokefirered --reference /tmp/fre --write
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SPECIES_HEADER = "include/constants/species.h"
POKEDEX_HEADER = "include/constants/pokedex.h"
NAMES_HEADER = "src/data/text/species_names.h"

NACIONAL_MAX = 1025


# ----------------------------------------------------------------- leitura ---
def parse_defines_species(texto: str) -> dict[str, int]:
    """`#define SPECIES_X 123` -> {'X': 123}."""
    d = {}
    for m in re.finditer(r"^#define\s+SPECIES_(\w+)\s+(\d+)\s*$", texto, re.M):
        d[m.group(1)] = int(m.group(2))
    return d


def parse_enum_nacional(texto: str) -> list[str]:
    """Lê o enum NatDex e devolve os nomes em ordem (índice = número nacional)."""
    marca = "enum"
    i = texto.index(marca)
    corpo = texto[i:texto.index("};", i)]
    corpo = re.sub(r"//[^\n]*", "", corpo)
    corpo = re.sub(r"/\*.*?\*/", "", corpo, flags=re.S)
    return re.findall(r"NATIONAL_DEX_(\w+)", corpo)


# ------------------------------------------------------------------ montar ---
def montar_tabela(poke_species: dict[str, int], natdex: list[str]) -> list[tuple[int, str]]:
    """Devolve [(numero_nacional, nome_da_constante)] de 1 a 1025.

    O nome da constante é o do pokefirered quando a espécie já existe lá (assim
    nenhum dado ou script do FireRed precisa ser tocado); para as novas (Gen 4-9)
    usa o nome do repositório de referência.
    """
    indice = {nome: i for i, nome in enumerate(natdex)}
    por_nacional: dict[int, str] = {}
    for nome in poke_species:
        if nome == "NONE" or "OLD_UNOWN" in nome:
            continue
        nacional = indice.get(nome)
        if nacional is not None:
            por_nacional[nacional] = nome
    return [(n, por_nacional.get(n, natdex[n])) for n in range(1, NACIONAL_MAX + 1)]


def nacional_por_nome(natdex: list[str]) -> dict[str, int]:
    return {nome: i for i, nome in enumerate(natdex)}


# ------------------------------------------------------------------ emitir ---
def emitir_species_h(tabela: list[tuple[int, str]], origem_fr: str) -> str:
    cabeca = _cabecalho_species(origem_fr)
    linhas = [cabeca, "", "// Numeração: ID == número da Pokédex Nacional (1-1025).", "",
              "#define SPECIES_NONE 0", "",
        "// Fim dos blocos regionais (usado por IsNationalPokedexEnabled e pela troca)",
        "#define KANTO_SPECIES_END SPECIES_MEW",
        "#define JOHTO_SPECIES_END SPECIES_CELEBI",
        "#define HOENN_SPECIES_END SPECIES_CHIMECHO",
        ""]
    for numero, nome in tabela:
        linhas.append(f"#define SPECIES_{nome} {numero}")
    linhas += [
        "",
        f"#define NUM_SPECIES {NACIONAL_MAX + 1}",
        "#define SPECIES_EGG NUM_SPECIES",
        "",
        "// Formas (ficam acima de NUM_SPECIES, como no FireRed original)",
    ]
    for i, letra in enumerate("BCDEFGHIJKLMNOPQRSTUVWXYZ", start=1):
        linhas.append(f"#define SPECIES_UNOWN_{letra} (NUM_SPECIES + {i})")
    linhas += [
        f"#define SPECIES_UNOWN_QMARK (NUM_SPECIES + {27})",
        f"#define SPECIES_UNOWN_EMARK (NUM_SPECIES + {28})",
        "",
        "#endif  // GUARD_CONSTANTS_SPECIES_H",
    ]
    return "\n".join(linhas) + "\n"


def _cabecalho_species(origem: str) -> str:
    return (
        "// Gerado por scripts/firered/gen_species_constants.py -- não editar à mão.\n"
        "// Fonte: pokefirered (nomes) + RHH pokeemerald-expansion (ordem nacional).\n"
        "#ifndef GUARD_CONSTANTS_SPECIES_H\n"
        "#define GUARD_CONSTANTS_SPECIES_H\n"
    )


def emitir_pokedex_h(natdex: list[str], original: str) -> str:
    """Reescreve o enum nacional (1..1025) preservando o resto do arquivo."""
    inicio = original.index("enum")
    fim = original.index("};", inicio) + 2
    corpo = ["enum {", "    NATIONAL_DEX_NONE,"]
    for numero in range(1, NACIONAL_MAX + 1):
        corpo.append(f"    NATIONAL_DEX_{natdex[numero]},")
    corpo.append("};")
    novo_enum = "\n".join(corpo)

    resto = original[fim:]
    resto = resto.replace(
        "#define NATIONAL_DEX_COUNT  NATIONAL_DEX_DEOXYS",
        f"#define NATIONAL_DEX_COUNT  NATIONAL_DEX_{natdex[NACIONAL_MAX]}",
    )
    return original[:inicio] + novo_enum + resto


def emitir_nomes(natdex: list[str], tabela: list[tuple[int, str]], original: str) -> str:
    """Acrescenta entradas de nome para as espécies que ainda não têm."""
    existentes = set(re.findall(r"\[SPECIES_(\w+)\]", original))
    novas = []
    for numero, nome in tabela:
        if nome in existentes:
            continue
        # sem `ljust(10)`: o espaço de enchimento ia para dentro do jogo e a
        # caixa de batalha mostrava "Go! SYLVEON   !" (o array já tem 11 colunas)
        legivel = natdex[numero].replace("_", " ")[:10].rstrip()
        novas.append(f'    [SPECIES_{nome}] = _("{legivel}"),')
    # entradas antigas foram gravadas com espaço de enchimento: limpa
    original = re.sub(r'(\[SPECIES_\w+\] = _\("[^"]*?) +"\)', r'\1")', original)
    if not novas:
        return original
    return original.replace("};", "\n".join(novas) + "\n};", 1) if original.rstrip().endswith("};") else original


# --------------------------------------------------------------- self-test ---
def ler_species_original(poke_dir: Path) -> str:
    """Lê o species.h *pristine*, mesmo depois que o gerador já reescreveu o arquivo."""
    texto = (poke_dir / SPECIES_HEADER).read_text()
    if texto.startswith("// Gerado por"):
        import subprocess
        return subprocess.run(
            ["git", "-C", str(poke_dir), "show", f"HEAD:{SPECIES_HEADER}"],
            capture_output=True, text=True, check=True).stdout
    return texto


def self_test(poke_dir: Path, ref_dir: Path) -> int:
    fr = parse_defines_species(ler_species_original(poke_dir))
    natdex = parse_enum_nacional((ref_dir / "include/constants/pokedex.h").read_text())

    falhas = []
    if len(natdex) != NACIONAL_MAX + 1:
        falhas.append(f"enum nacional tem {len(natdex)} entradas, esperado {NACIONAL_MAX + 1}")
    if natdex[0] != "NONE":
        falhas.append(f"primeira entrada do enum é {natdex[0]!r}, esperado NONE")
    if natdex[1] != "BULBASAUR" or natdex[NACIONAL_MAX] != "PECHARUNT":
        falhas.append("extremos do enum nacional inesperados")

    base = {k: v for k, v in fr.items() if v <= 411 and "OLD_UNOWN" not in k and k != "NONE"}
    if len(base) != 386:
        falhas.append(f"pokefirered tem {len(base)} espécies base (esperado 386)")

    indice = {n: i for i, n in enumerate(natdex)}
    sem_nacional = [k for k in base if k not in indice]
    if sem_nacional:
        falhas.append(f"espécies sem número nacional: {sem_nacional[:5]}")

    tabela = montar_tabela(fr, natdex)
    if len(tabela) != NACIONAL_MAX:
        falhas.append(f"tabela tem {len(tabela)} linhas")
    numeros = [n for n, _ in tabela]
    if numeros != list(range(1, NACIONAL_MAX + 1)):
        falhas.append("numeração não é 1..1025 contínua")
    nomes = [k for _, k in tabela]
    if len(set(nomes)) != len(nomes):
        dup = [k for k in set(nomes) if nomes.count(k) > 1]
        falhas.append(f"nomes duplicados: {dup[:5]}")

    # 1..386 têm que manter exatamente os nomes do pokefirered (compatibilidade)
    for numero, nome in tabela[:386]:
        if nome not in fr:
            falhas.append(f"#{numero} {nome} não existe no pokefirered")
            break

    for f in falhas:
        print(f"FALHA: {f}")
    print(f"self-test: {len(tabela)} espécies, {len(base)} reaproveitadas, "
          f"{len(tabela) - len(base)} novas -> {'OK' if not falhas else 'FALHOU'}")
    return 0 if not falhas else 1


# -------------------------------------------------------------------- main ---
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--reference", default="/tmp/fre")
    ap.add_argument("--write", action="store_true", help="grava os arquivos no pokefirered")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    poke = Path(a.pokefirered)
    ref = Path(a.reference)
    if a.self_test:
        return self_test(poke, ref)

    fr = parse_defines_species((poke / SPECIES_HEADER).read_text())
    natdex = parse_enum_nacional((ref / "include/constants/pokedex.h").read_text())
    tabela = montar_tabela(fr, natdex)

    species_h = emitir_species_h(tabela, str(poke / SPECIES_HEADER))
    pokedex_original = (poke / POKEDEX_HEADER).read_text()
    pokedex_h = emitir_pokedex_h(natdex, pokedex_original)
    nomes_h = emitir_nomes(natdex, tabela, (poke / NAMES_HEADER).read_text())

    print(f"tabela: {len(tabela)} espécies (1..{NACIONAL_MAX})")
    print(f"  reaproveitadas do pokefirered: {sum(1 for n, k in tabela if k in fr)}")
    print(f"  novas (Gen 4-9):              {sum(1 for n, k in tabela if k not in fr)}")

    if not a.write:
        print("\n--write não passado: nada foi gravado.")
        return 0

    (poke / SPECIES_HEADER).write_text(species_h)
    (poke / POKEDEX_HEADER).write_text(pokedex_h)
    (poke / NAMES_HEADER).write_text(nomes_h)
    print(f"\ngravado: {SPECIES_HEADER}, {POKEDEX_HEADER}, {NAMES_HEADER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
