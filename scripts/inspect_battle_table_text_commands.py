#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida dispatch e padrões Thumb locais dos opcodes 0x13/0x14."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x13: 0x0801FE31, 0x14: 0x0801FE85}


def offset(va: int, size: int, rom: bytes) -> int:
    pos = va - ROM_BASE
    if pos < 0 or pos + size > len(rom):
        raise SystemExit(f"VA fora da ROM: 0x{va:08X} (+0x{size:X})")
    return pos


def read32(rom: bytes, va: int) -> int:
    return struct.unpack_from("<I", rom, offset(va, 4, rom))[0]


def expect(rom: bytes, va: int, wanted_hex: str, label: str) -> None:
    wanted = bytes.fromhex(wanted_hex)
    pos = offset(va, len(wanted), rom)
    actual = rom[pos : pos + len(wanted)]
    if actual != wanted:
        raise SystemExit(f"{label}: {actual.hex(' ')}, esperado {wanted.hex(' ')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    for opcode, handler in HANDLERS.items():
        actual = read32(rom, COMMAND_TABLE_VA + opcode * 4)
        if actual != handler:
            raise SystemExit(f"opcode 0x{opcode:02X}: 0x{actual:08X}, esperado 0x{handler:08X}")

    signatures = [
        (0x0801FE30, "30 b5 10 48 00 68 00 28 19 d1", "entrada/espera do opcode 0x13"),
        (0x0801FE3C, "22 68 51 78 90 78 00 02 01 43 d0 78", "leitura dos primeiros bytes do pointer inline"),
        (0x0801FE46, "d0 78 00 04 01 43 10 79 00 06 01 43", "montagem local do pointer de quatro bytes"),
        (0x0801FE52, "0a 4d 68 79 40 00 09 18 08 88", "seleção u16 por byte local e stride 2"),
        (0x0801FE5C, "08 49 09 78 f7 f7 a4 fa", "helper local de texto"),
        (0x0801FE64, "20 68 05 30 20 60", "avanço de cinco bytes do opcode 0x13"),
        (0x0801FE6A, "01 20 e8 71", "flag local de exibição do opcode 0x13"),
        (0x0801FE84, "70 b5 13 48 00 68 00 28 1f d1", "entrada/espera do opcode 0x14"),
        (0x0801FE8E, "12 4d 2a 68 51 78 90 78 00 02 01 43", "leitura do pointer inline no opcode 0x14"),
        (0x0801FEA6, "0d 4e 70 79 40 00 09 18", "seleção u16 no opcode 0x14"),
        (0x0801FEAE, "0c 4c 0c 48 00 78 20 70 09 88", "battler e argumento de string"),
        (0x0801FEB8, "00 20 ee f7 97 fa", "emissão local de string de seleção"),
        (0x0801FEC4, "28 68 05 30 28 60", "avanço de cinco bytes do opcode 0x14"),
        (0x0801FECA, "01 20 f0 71", "flag local de exibição do opcode 0x14"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x0801FE74: 0x02023BC8,
        0x0801FE78: 0x02023D74,
        0x0801FE7C: 0x02023E82,
        0x0801FE80: 0x02023D6B,
        0x0801FED4: 0x02023BC8,
        0x0801FED8: 0x02023D74,
        0x0801FEDC: 0x02023E82,
        0x0801FEE0: 0x02023BC4,
        0x0801FEE4: 0x02023D6B,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados pointer inline u32, seleção local por halfword, flags e cursor +5.")
    print("Validação estática; sem nomes upstream embutidos como evidência local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
