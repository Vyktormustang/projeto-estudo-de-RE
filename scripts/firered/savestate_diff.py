#!/usr/bin/env python3
"""Compara dois savestates e mostra os bytes que mudaram (com filtro por região).

Serve para descobrir **o que o jogo realmente fez** entre dois pontos, sem
adivinhar. Foi assim que descobri o offset de `SaveBlock1.flags` e o lugar onde
o contador de estatísticas é incrementado.

Uso
---
    savestate_diff.py --map X.map --offsets o.json ANTES.bin DEPOIS.bin
    savestate_diff.py --map X.map --offsets o.json A.bin B.bin --regiao saveblock2
    savestate_diff.py --map X.map --offsets o.json A.bin B.bin --max 40
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from savestate import Estado  # noqa: E402

REGIOES = {
    "saveblock1": lambda e: (e.s1, e.s1 + 0x4000),
    "saveblock2": lambda e: (e.s2, e.s2 + 0x1000),
    "iwram": lambda e: (0x19000, 0x21000),
    "ewram": lambda e: (0x21000, 0x61000),
    "tudo": lambda e: (0, min(len(e.d), 0x61000)),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("antes")
    ap.add_argument("depois")
    ap.add_argument("--map", required=True)
    ap.add_argument("--offsets", required=True)
    ap.add_argument("--regiao", default="tudo", choices=sorted(REGIOES))
    ap.add_argument("--max", type=int, default=60)
    a = ap.parse_args()

    off = json.loads(Path(a.offsets).read_text())
    ea = Estado(Path(a.antes).read_bytes(), Path(a.map))
    eb = Estado(Path(a.depois).read_bytes(), Path(a.map))

    ini, fim = REGIOES[a.regiao](eb)
    print(f"região {a.regiao}: 0x{ini:X}..0x{fim:X}")
    print(f"SaveBlock1=0x{eb.s1:X} SaveBlock2=0x{eb.s2:X}")
    for chave in ("s1_flags", "s1_seen1", "s1_seen2", "s2_pokedex"):
        print(f"  {chave:12} = 0x{off[chave]:04X}")

    n = 0
    for i in range(ini, min(fim, len(ea.d), len(eb.d))):
        x, y = ea.d[i], eb.d[i]
        if x == y:
            continue
        # descobre em qual campo caiu
        onde = []
        for chave, valor in off.items():
            if chave.endswith("_size") or chave in ("s1_pos", "s2_pokedex", "dex_owned", "dex_seen"):
                continue
            if chave.startswith("s1_"):
                base = eb.s1 + valor
                if base <= i < base + 129:
                    onde.append(f"{chave}+0x{i-base:03X}")
            elif chave.startswith("s2_") or chave == "s2_pokedex":
                base = eb.s2 + valor
                if base <= i < base + 300:
                    onde.append(f"{chave}+0x{i-base:03X}")
        print(f"  0x{i:06X}  {x:02x} -> {y:02x}  ({x ^ y:02x})  {' '.join(onde)}")
        n += 1
        if n >= a.max:
            print(f"  ... (parou em {a.max}; use --max para ver mais)")
            break
    print(f"\n{n} byte(s) diferentes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
