#!/usr/bin/env python3
"""Extrai offsets de struct do build **ARM real**, não do compilador do host.

Por que isso existe
-------------------
Os comentários de offset no `include/global.h` do pokefirered estão desatualizados,
e compilar o mesmo header com o gcc do host dá um layout **diferente** do ARM
(enums, alinhamento e `-fshort-enums` mudam o empacotamento). Nesta sessão isso
custou caro: o host dizia `SaveBlock1.flags = 0x1130` e `seen2 = 0x3BC8`, mas o
ARM real usa `0xF2C` e `0x39C4` — 516 bytes de diferença, o que fez o anticheat
da Pokédex rejeitar tudo e a tela não abrir.

Como funciona
-------------
Gera um `.c` com uma função por campo (`int f(void){ return offsetof(...); }`),
compila com o toolchain ARM em `-O0 -S` — que é rápido (~0,3 s) porque o wrapper
usa zig/LLVM — e lê o imediato do assembly (`movw`/`movs`).

Uso
---
    python3 scripts/firered/offsets.py --pokefirered /tmp/pokefirered
    python3 scripts/firered/offsets.py --pokefirered /tmp/pokefirered --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# campo -> (struct, membro)
CAMPOS = {
    "saveblock1_size": ("struct SaveBlock1", None),
    "saveblock2_size": ("struct SaveBlock2", None),
    "s1_pos": ("struct SaveBlock1", "pos"),
    "s1_location": ("struct SaveBlock1", "location"),
    "s1_playerPartyCount": ("struct SaveBlock1", "playerPartyCount"),
    "s1_playerParty": ("struct SaveBlock1", "playerParty"),
    "s1_flags": ("struct SaveBlock1", "flags"),
    "s1_vars": ("struct SaveBlock1", "vars"),
    "s1_seen1": ("struct SaveBlock1", "seen1"),
    "s1_seen2": ("struct SaveBlock1", "seen2"),
    "s2_pokedex": ("struct SaveBlock2", "pokedex"),
    "s2_playerName": ("struct SaveBlock2", "playerName"),
    "s2_playerTrainerId": ("struct SaveBlock2", "playerTrainerId"),
    "dex_owned": ("struct Pokedex", "owned"),
    "dex_seen": ("struct Pokedex", "seen"),
    "pokemon_size": ("struct Pokemon", None),
    # E2: tabelas de espécie (usadas por verificar_rom.py)
    "speciesinfo_size": ("struct SpeciesInfo", None),
    "pokedexentry_size": ("struct PokedexEntry", None),
    "evolution_size": ("struct Evolution", None),
    "si_baseHP": ("struct SpeciesInfo", "baseHP"),
    "si_types": ("struct SpeciesInfo", "types"),
    "si_catchRate": ("struct SpeciesInfo", "catchRate"),
    "si_expYield": ("struct SpeciesInfo", "expYield"),
    "si_abilities": ("struct SpeciesInfo", "abilities"),
    "pe_categoryName": ("struct PokedexEntry", "categoryName"),
    "pe_height": ("struct PokedexEntry", "height"),
    "pe_description": ("struct PokedexEntry", "description"),
    # E6: layout de batalha. `ability` virou u16 (ID de habilidade > 255), o que
    # empurra type1/type2/pp/hp/level/maxHP e muda o passo de `gBattleMons`.
    # Quem lê a RAM (nav.py, provas) tem de usar ESTES números, não os de antes.
    "battlemon_size": ("struct BattlePokemon", None),
    "bm_species": ("struct BattlePokemon", "species"),
    "bm_ability": ("struct BattlePokemon", "ability"),
    "bm_type1": ("struct BattlePokemon", "type1"),
    "bm_type2": ("struct BattlePokemon", "type2"),
    "bm_hp": ("struct BattlePokemon", "hp"),
    "bm_level": ("struct BattlePokemon", "level"),
    "bm_maxHP": ("struct BattlePokemon", "maxHP"),
    # E6: layout das tabelas de sprite (quem lê o ROM precisa do passo certo)
    "moncoords_size": ("struct MonCoords", None),
    "compressed_spritesheet_size": ("struct CompressedSpriteSheet", None),
    "compressed_spritepalette_size": ("struct CompressedSpritePalette", None),
    "speciesname_len": ("struct SpeciesInfo", "baseHP"),   # só p/ ancorar o include
}

TEMPLATE = """#include "global.h"
#include "pokedex.h"
#include "data.h"
{corpo}
"""


def montar_fonte() -> str:
    linhas = []
    for nome, (tipo, membro) in CAMPOS.items():
        if membro is None:
            linhas.append(f"int c_{nome}(void) {{ return sizeof({tipo}); }}")
        else:
            linhas.append(f"int c_{nome}(void) {{ return offsetof({tipo}, {membro}); }}")
    return "".join(l + "\n" for l in linhas)


# Offsets que o probe NAO acerta: o build usa `-mabi=apcs-gnu` (ABI ARM antiga),
# que empacota structs de um jeito que o gcc do probe (ABI EABI) nao reproduz.
# Cada valor abaixo foi medido DENTRO do ROM em execucao: um trecho de
# diagnostico grava, em 0x0203FFF0, o endereco relativo de cada campo
# (`(u8*)&gSaveBlock1Ptr->seen2 - (u8*)gSaveBlock1Ptr`). Ver docs/FIRERED.md.
#
# Historico: `s1_seen2` saia 0x39C4 quando o valor real e 0x3A64 (160 bytes de
# diferenca). O anticheat da Pokedex compara SaveBlock2.pokedex.seen com
# SaveBlock1.seen1 e seen2; escrever no lugar errado zerava a contagem e a
# lista da Pokedex aparecia VAZIA (sem crash) -- foi o que travou a E1.
VERIFICADOS_NO_ROM = {
    "s1_seen2": 0x3A64,   # medido em 2026-10-23, ROM da E1 (1025 especies)
}


def extrair(poke: Path, toolchain: Path | None) -> dict[str, int]:
    env = dict(os.environ)
    if toolchain:
        env["PATH"] = f"{toolchain}:{env['PATH']}"
    fonte = Path(tempfile.mkdtemp()) / "offsets.c"
    fonte.write_text(TEMPLATE.format(corpo=montar_fonte()))
    saida = fonte.with_suffix(".s")
    # `-mabi=apcs-gnu` é o que o build do pokefirered usa (ver CFLAGS do Makefile).
    # Sem ele o probe mede com a ABI EABI, que **não** arredonda struct para
    # múltiplo de 4: `struct MonCoords` (2x u8) sai 2 no probe e 4 no ROM, e o
    # array de coordenadas de sprite é lido com o passo errado. A regra do APCS
    # é "todo struct ocupa múltiplo de 4 bytes".
    cmd = ["arm-none-eabi-gcc", "-mthumb", "-mabi=apcs-gnu", "-O0", "-S", "-o", str(saida),
           "-iquote", "include", "-iquote", "gflib",
           "-D", "FIRERED=1", "-D", "ENGLISH=1", "-D", "MODERN=1", str(fonte)]
    r = subprocess.run(cmd, cwd=poke, env=env, capture_output=True, text=True)
    if not saida.exists():
        raise SystemExit(f"compilação falhou:\n{r.stderr[-2000:]}")

    valores = _valores_do_assembly(saida.read_text())
    faltando = set(CAMPOS) - set(valores)
    if faltando:
        raise SystemExit(f"não consegui extrair: {sorted(faltando)}")
    for k, v in VERIFICADOS_NO_ROM.items():
        if valores.get(k) != v:
            print(f"aviso: {k} medido no ROM = 0x{v:X}; probe dizia 0x{valores[k]:X}"
                  " -- usando o valor do ROM", file=sys.stderr)
            valores[k] = v
    return valores


def _valores_do_assembly(texto: str) -> dict[str, int]:
    """Le `movw/movs r0, #N` de cada função `c_<campo>` do .s do gcc."""
    valores: dict[str, int] = {}
    for m in re.finditer(r"^c_(\w+):.*?$(.*?)(?=^c_\w+:|\Z)", texto, re.M | re.S):
        nome, corpo = m.group(1), m.group(2)
        v = re.search(r"mov[wst]?\s+r0,\s*#(\d+)", corpo)
        if v:
            valores[nome] = int(v.group(1))
    return valores


def self_test() -> int:
    """Garante que o parser entende as três formas que o gcc emite."""
    fake = """
    .text
c_s1_pos:
    movs r0, #0
    bx lr
c_s1_flags:
    movw r0, #3884
    bx lr
c_s2_pokedex:
    movw r0, #24
    movw r3, #999
    bx lr
c_zero:
    movs r0, #0
    bx lr
"""
    v = _valores_do_assembly(fake)
    assert v == {"s1_pos": 0, "s1_flags": 3884, "s2_pokedex": 24, "zero": 0}, v
    # todo campo declarado tem de caber num único `movw` (0..65535)
    assert all(0 <= valor <= 0xFFFF for valor in v.values())
    # e o VERIFICADOS_NO_ROM tem de ser subconjunto de CAMPOS (senão nunca é usado)
    orfaos = set(VERIFICADOS_NO_ROM) - set(CAMPOS)
    assert not orfaos, f"VERIFICADOS_NO_ROM com campo inexistente: {orfaos}"
    print(f"self-test ok: parser de .s em 3 formas; {len(CAMPOS)} campos, "
          f"{len(VERIFICADOS_NO_ROM)} conferidos no ROM")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--toolchain", default="/tmp/tc/bin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gravar", default="", help="grava o JSON neste caminho")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    val = extrair(Path(a.pokefirered), Path(a.toolchain) if Path(a.toolchain).exists() else None)
    if a.json:
        print(json.dumps(val, indent=2))
    else:
        largura = max(len(k) for k in val)
        for k, v in val.items():
            print(f"{k:<{largura}}  {v:>6}  0x{v:04X}")
    if a.gravar:
        Path(a.gravar).write_text(json.dumps(val, indent=2) + "\n")
        print(f"\ngravado em {a.gravar}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
