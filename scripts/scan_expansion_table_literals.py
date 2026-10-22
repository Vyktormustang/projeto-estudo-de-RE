#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Indexa palavras ROM iguais às bases candidatas de tabelas de expansão.

Isto conta ocorrências brutas de u32 little-endian; não classifica uma ocorrência
como literal de código, referência efetiva ou consumidor da tabela.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
TARGETS = {
    "species_info": (0x08254784, 56),
    "experience_tables": (0x08253AE4, 18),
    "learnset_pointer_table": (0x0825D7B4, 6),
    "move_catalog": (0x08250C04, 137),
    "move_effect_script_table": (0x081D65A8, 6),
    "type_effectiveness_table": (0x0824F050, 9),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    print(f"ROM: {len(rom)} bytes; SHA-256 {digest}")
    for label, (value, expected_count) in TARGETS.items():
        needle = struct.pack("<I", value)
        hits: list[int] = []
        pos = 0
        while True:
            pos = rom.find(needle, pos)
            if pos < 0:
                break
            hits.append(ROM_BASE + pos)
            pos += 1
        if len(hits) != expected_count:
            raise SystemExit(
                f"{label}: {len(hits)} ocorrências de 0x{value:08X}; "
                f"esperadas {expected_count} para este hash"
            )
        print(f"{label}: alvo 0x{value:08X}; ocorrências brutas={len(hits)}")
        print("  " + " ".join(f"0x{address:08X}" for address in hits))
    print("Aviso: padrões u32 não são xrefs validados; classifique cada ocorrência antes de inferir consumidores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
