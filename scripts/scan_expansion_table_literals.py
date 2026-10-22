#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Indexa ocorrências e candidatos Thumb LDR literal para bases de tabelas.

A detecção LDR reconhece somente o padrão de opcode Thumb 01001; ela não prova
que os bytes sejam instruções alcançáveis, nem que o carregamento seja consumidor.
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
    "species_info": (0x08254784, 56, 55),
    "experience_tables": (0x08253AE4, 18, 18),
    "learnset_pointer_table": (0x0825D7B4, 6, 6),
    "move_catalog": (0x08250C04, 137, 136),
    "move_effect_script_table": (0x081D65A8, 6, 6),
    "type_effectiveness_table": (0x0824F050, 9, 9),
}


def find_word_offsets(rom: bytes, value: int) -> list[int]:
    needle = struct.pack("<I", value)
    offsets: list[int] = []
    pos = 0
    while True:
        pos = rom.find(needle, pos)
        if pos < 0:
            return offsets
        offsets.append(pos)
        pos += 1


def thumb_ldr_literal_sites(rom: bytes, literal_offset: int) -> list[int]:
    """Return ROM VAs of halfwords matching Thumb LDR literal to this word."""
    sites: list[int] = []
    start = max(0, literal_offset - 1024)
    start += start & 1  # keep instruction address halfword-aligned
    for instruction_offset in range(start, literal_offset, 2):
        if instruction_offset + 2 > len(rom):
            break
        halfword = int.from_bytes(rom[instruction_offset:instruction_offset + 2], "little")
        if (halfword & 0xF800) != 0x4800:  # Thumb LDR Rd, [PC, #imm8*4]
            continue
        pc_offset = (instruction_offset + 4) & ~3
        target_offset = pc_offset + ((halfword & 0xFF) << 2)
        if target_offset == literal_offset:
            sites.append(ROM_BASE + instruction_offset)
    return sites


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    parser.add_argument(
        "--list-candidates", action="store_true",
        help="print each matching word and its candidate Thumb LDR site(s)",
    )
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    print(f"ROM: {len(rom)} bytes; SHA-256 {digest}")
    for label, (value, expected_raw, expected_ldr_words) in TARGETS.items():
        offsets = find_word_offsets(rom, value)
        if len(offsets) != expected_raw:
            raise SystemExit(
                f"{label}: {len(offsets)} ocorrências de 0x{value:08X}; "
                f"esperadas {expected_raw} para este hash"
            )

        candidate_rows = [(offset, thumb_ldr_literal_sites(rom, offset)) for offset in offsets]
        with_sites = sum(bool(sites) for _, sites in candidate_rows)
        if with_sites != expected_ldr_words:
            raise SystemExit(
                f"{label}: {with_sites} palavras com padrão Thumb LDR candidato; "
                f"esperadas {expected_ldr_words} para este hash"
            )
        print(
            f"{label}: base 0x{value:08X}; ocorrências u32 brutas={len(offsets)}; "
            f"palavras com candidato Thumb LDR literal={with_sites}"
        )
        if args.list_candidates:
            for offset, sites in candidate_rows:
                if sites:
                    print(
                        f"  word=0x{ROM_BASE + offset:08X} sites="
                        + ",".join(f"0x{site:08X}" for site in sites)
                    )
    print(
        "Aviso: ocorrências u32 e padrões LDR são candidatos estáticos; confirme modo, "
        "alcançabilidade, contexto e uso antes de afirmar xrefs/consumidores."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
