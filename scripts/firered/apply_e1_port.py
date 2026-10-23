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


def completar_tabela_nacional(s: str, poke: Path) -> str:
    """Reescreve sSpeciesToNationalPokedexNum com as 1025 especies.

    A tabela do FireRed tem 386 inicializadores dentro de um array de
    NUM_SPECIES-1 posicoes. Depois da E1 o array tem 1025 posicoes, e as 639
    restantes ficam zeradas -- NationalPokedexNumToSpecies(n) devolvia 0 para
    todo Gen 4-9 e a lista da Pokedex saia vazia.

    Como a E1 numerou as especies IGUAL a dex nacional (ID = numero nacional),
    a tabela e simplesmente 1..1025.
    """
    ini = s.find("static const u16 sSpeciesToNationalPokedexNum")
    if ini == -1:
        raise SystemExit("nao achei sSpeciesToNationalPokedexNum em pokemon.c")
    fim = s.index("};", ini) + 2
    fontes = list((poke / "include/constants").glob("species.h"))
    nomes = []
    for linha in fontes[0].read_text().splitlines():
        m = re.match(r"#define SPECIES_(\w+)\s+(\d+)\s*$", linha.strip())
        if m and 1 <= int(m.group(2)) <= 1025:
            nomes.append((m.group(1), int(m.group(2))))
    nomes.sort(key=lambda par: par[1])
    if len(nomes) != 1025:
        raise SystemExit(f"esperava 1025 especies, achei {len(nomes)}")
    corpo = "\n".join(f"    [SPECIES_{n} - 1] = {v}," for n, v in nomes)
    nova = ("// TABELA_NACIONAL_COMPLETA: ID de especie == numero da dex nacional\n"
            "static const u16 sSpeciesToNationalPokedexNum[NUM_SPECIES - 1] =\n{\n"
            + corpo + "\n};")
    return s[:ini] + nova + s[fim:]


def busca_binaria_nacional(s: str) -> str:
    """Troca a varredura linear de NationalPokedexNumToSpecies por busca binaria.

    A versao linear percorre ate 1025 posicoes por chamada, e a tela da Pokedex
    chama a funcao uma vez por especie ao montar a lista: O(n^2) = ~1 milhao de
    comparacoes a cada abertura.
    """
    antigo = """u16 NationalPokedexNumToSpecies(u16 nationalNum)
{
    u16 species;

    if (!nationalNum)
        return 0;

    species = 0;

    while (species < NUM_SPECIES - 1 && sSpeciesToNationalPokedexNum[species] != nationalNum)
        species++;

    if (species == NUM_SPECIES - 1)
        return 0;

    return species + 1;
}"""
    novo = """u16 NationalPokedexNumToSpecies(u16 nationalNum)
{
    // Busca binaria: a tabela e crescente (ver TABELA_NACIONAL_COMPLETA).
    s32 lo = 0;
    s32 hi = NUM_SPECIES - 2;

    if (!nationalNum)
        return 0;

    while (lo <= hi)
    {
        s32 mid = (lo + hi) / 2;

        if (sSpeciesToNationalPokedexNum[mid] == nationalNum)
            return mid + 1;
        if (sSpeciesToNationalPokedexNum[mid] < nationalNum)
            lo = mid + 1;
        else
            hi = mid - 1;
    }

    return 0;
}"""
    if antigo not in s:
        if "Busca binaria: a tabela e crescente" in s:
            return s
        raise SystemExit("nao achei NationalPokedexNumToSpecies para trocar")
    return s.replace(antigo, novo)


def numero_dex_4_digitos(s: str) -> str:
    """Faz o numero da dex caber em 4 digitos (#1025).

    `DexScreen_PrintNum3LeadingZeroes` monta o buffer com exatamente 3 digitos,
    entao a partir da especie 1000 o texto saia truncado. A funcao nova decide o
    numero de digitos em tempo de execucao e mantem os zeros a esquerda.
    """
    antigo = """static void DexScreen_PrintNum3LeadingZeroes(u8 windowId, u8 fontId, u16 num, u8 x, u8 y, u8 colorIdx)
{
    u8 buff[4];
    buff[0] = (num / 100) + CHAR_0;
    buff[1] = ((num %= 100) / 10) + CHAR_0;
    buff[2] = (num % 10) + CHAR_0;
    buff[3] = EOS;
    DexScreen_AddTextPrinterParameterized(windowId, fontId, buff, x, y, colorIdx);
}"""
    novo = """static void DexScreen_PrintNum3LeadingZeroes(u8 windowId, u8 fontId, u16 num, u8 x, u8 y, u8 colorIdx)
{
    // DexScreen_PrintNum4: a Pokédex vai até 1025, então o número pode ter
    // 4 dígitos. Mantém os zeros à esquerda e o alinhamento das colunas.
    u8 buff[5];
    u8 n = 0;

    if (num >= 1000)
        buff[n++] = (num / 1000) + CHAR_0;
    buff[n++] = ((num / 100) % 10) + CHAR_0;
    buff[n++] = ((num / 10) % 10) + CHAR_0;
    buff[n++] = (num % 10) + CHAR_0;
    buff[n] = EOS;
    DexScreen_AddTextPrinterParameterized(windowId, fontId, buff, x, y, colorIdx);
}"""
    if antigo not in s:
        raise SystemExit("nao achei DexScreen_PrintNum3LeadingZeroes")
    return s.replace(antigo, novo)


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

    # 4) menu2.c — formas do Unown: reusa SPECIES_UNOWN_* (nome trocado, valor mantido
    #    relativo a NUM_SPECIES) e remove os dois #define locais, que agora conflitariam
    #    com os de species.h.
    p = poke / "src/menu2.c"
    s = ler(p)
    s = s.replace(
        '// Not actually "old" given these were introduced in Gen 3,\n'
        "// but they're used as equivalents here alongside the other OLD_UNOWN\n", "")
    s, _ = remover_linhas(s, "#define SPECIES_UNOWN_EMARK")
    s, _ = remover_linhas(s, "#define SPECIES_UNOWN_QMARK")
    s = s.replace("SPECIES_OLD_UNOWN_", "SPECIES_UNOWN_")
    if gravar(p, s):
        mudancas.append("menu2.c: formas do Unown em SPECIES_UNOWN_* (defines locais removidos)")

    # 5) demais tabelas — a linha do placeholder sai
    for nome in DADOS_COM_OLD_UNOWN:
        p = poke / nome
        s, n = remover_linhas(ler(p), "OLD_UNOWN")
        if gravar(p, s):
            mudancas.append(f"{nome}: -{n} linhas OLD_UNOWN")

    # 6b) pokemon.c — tabela nacional completa e busca binaria.
    #     A tabela original do FireRed cobre so as 386 primeiras especies; sem
    #     preencher as 639 restantes, NationalPokedexNumToSpecies devolve 0 para
    #     qualquer Gen 4-9 e a Pokedex desenha linhas vazias.
    p = poke / "src/pokemon.c"
    s = ler(p)
    if "TABELA_NACIONAL_COMPLETA" not in s:
        s = completar_tabela_nacional(s, poke)
        s = busca_binaria_nacional(s)
        if gravar(p, s):
            mudancas.append("pokemon.c: tabela nacional 1..1025 + busca binaria")

    # 6c) pokedex_screen.c — numero da dex com 4 digitos
    #     DexScreen_PrintNum3LeadingZeroes escreve exatamente 3 digitos; a partir
    #     da especie 1000 o numero saia cortado ("No!25" em vez de "No1025").
    p = poke / "src/pokedex_screen.c"
    s = ler(p)
    if "DexScreen_PrintNum4" not in s:
        s = numero_dex_4_digitos(s)
        if gravar(p, s):
            mudancas.append("pokedex_screen.c: numero da dex com 4 digitos")

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


def self_test() -> int:
    """Testa as três transformações de texto puras (sem tocar no clone)."""
    # 1) OLD_UNOWN: o bloco macro inteiro sai, o resto fica
    entrada = (
        "[SPECIES_UNOWN] =\n"
        "{\n"
        "#if P_FAMILY_UNOWN\n"
        "    .foo = 1,\n"
        "#endif\n"
        "},\n"
        "#define OLD_UNOWN_SPECIES_INFO \\\n"
        "    [SPECIES_UNOWN_A] = { .bar = 2 },\n"
        "    [SPECIES_UNOWN_B] = { .bar = 3 }\n"
        "#define OUTRA_COISA 1\n"
        "fim\n")
    saida = remover_macro_old_unown(entrada)
    assert "OLD_UNOWN" not in saida, saida
    assert "[SPECIES_UNOWN] =" in saida and "fim" in saida, saida
    assert "#define OUTRA_COISA 1" in saida, "comeu a linha seguinte ao bloco"
    assert saida.count("[SPECIES_UNOWN_A]") == 0

    # 2) remover_linhas conta o que removeu
    texto, n = remover_linhas("a\nREMOVER_ME\nb\nREMOVER_ME\nc", "REMOVER_ME")
    assert n == 2 and texto == "a\nb\nc", (n, texto)
    texto, n = remover_linhas("a\nb", "NAO_EXISTE")
    assert n == 0 and texto == "a\nb"

    # 3) dex de 4 dígitos: a função antiga sai e a nova formata 1025 certo
    fonte = (
        "static void DexScreen_PrintNum3LeadingZeroes(u8 windowId, u8 fontId, u16 num, u8 x, u8 y, u8 colorIdx)\n"
        "{\n"
        "    u8 buff[4];\n"
        "    buff[0] = (num / 100) + CHAR_0;\n"
        "    buff[1] = ((num %= 100) / 10) + CHAR_0;\n"
        "    buff[2] = (num % 10) + CHAR_0;\n"
        "    buff[3] = EOS;\n"
        "    DexScreen_AddTextPrinterParameterized(windowId, fontId, buff, x, y, colorIdx);\n"
        "}\n")
    nova = numero_dex_4_digitos(fonte)
    assert "num >= 1000" in nova and "buff[5]" in nova
    # mesma conta do C novo: abaixo de 1000 tem de dar EXATAMENTE o que a função
    # antiga dava (3 dígitos com zeros à esquerda); a partir de 1000 ganha o 4º
    def formata(num):
        b = []
        if num >= 1000:
            b.append(num // 1000)
        b += [(num // 100) % 10, (num // 10) % 10, num % 10]
        return "".join(str(d) for d in b)

    def formata_antiga(num):
        return f"{num % 1000:03d}"

    for n in (1, 25, 99, 100, 386, 999):
        assert formata(n) == formata_antiga(n), (n, formata(n), formata_antiga(n))
    assert formata(1000) == "1000" and formata(1025) == "1025", formata(1025)

    print("self-test ok: OLD_UNOWN, remover_linhas e número de dex com 4 dígitos")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--check", action="store_true", help="falha se sobrar referência a OLD_UNOWN")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    poke = Path(a.pokefirered)
    if not (poke / "Makefile").exists():
        print(f"não parece um clone do pokefirered: {poke}")
        return 1
    return aplicar(poke, a.check)


if __name__ == "__main__":
    sys.exit(main())
