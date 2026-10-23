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
    "dex_owned": ("struct Pokedex", "owned"),
    "dex_seen": ("struct Pokedex", "seen"),
    "pokemon_size": ("struct Pokemon", None),
}

TEMPLATE = """#include "global.h"
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


def extrair(poke: Path, toolchain: Path | None) -> dict[str, int]:
    env = dict(os.environ)
    if toolchain:
        env["PATH"] = f"{toolchain}:{env['PATH']}"
    fonte = Path(tempfile.mkdtemp()) / "offsets.c"
    fonte.write_text(TEMPLATE.format(corpo=montar_fonte()))
    saida = fonte.with_suffix(".s")
    cmd = ["arm-none-eabi-gcc", "-mthumb", "-O0", "-S", "-o", str(saida),
           "-iquote", "include", "-iquote", "gflib",
           "-D", "FIRERED=1", "-D", "ENGLISH=1", "-D", "MODERN=1", str(fonte)]
    r = subprocess.run(cmd, cwd=poke, env=env, capture_output=True, text=True)
    if not saida.exists():
        raise SystemExit(f"compilação falhou:\n{r.stderr[-2000:]}")

    texto = saida.read_text()
    valores: dict[str, int] = {}
    # cada função sai como "c_nome:" seguida de movw/movs r0, #N
    for m in re.finditer(r"^c_(\w+):.*?$(.*?)(?=^c_\w+:|\Z)", texto, re.M | re.S):
        nome, corpo = m.group(1), m.group(2)
        v = re.search(r"mov[wst]?\s+r0,\s*#(\d+)", corpo)
        if v:
            valores[nome] = int(v.group(1))
    faltando = set(CAMPOS) - set(valores)
    if faltando:
        raise SystemExit(f"não consegui extrair: {sorted(faltando)}")
    return valores


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--toolchain", default="/tmp/tc/bin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gravar", default="", help="grava o JSON neste caminho")
    a = ap.parse_args()

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
