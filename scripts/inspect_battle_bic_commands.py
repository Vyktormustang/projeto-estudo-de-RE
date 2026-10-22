#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x36–0x38."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x36: 0x08022B61, 0x37: 0x08022B8D, 0x38: 0x08022BC5}


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
        (0x08022B60, "09 4b 1a 68 51 78 90 78 00 02 09 18 d0 78 00 04 09 18 10 79 00 06 09 18", "opcode 0x36: endereço u32 inline"),
        (0x08022B78, "52 79 08 78 90 43 08 70", "opcode 0x36: lê, BIC e grava byte"),
        (0x08022B80, "18 68 06 30 18 60 70 47", "opcode 0x36: cursor +6"),
        (0x08022B8C, "10 b5 0c 4c 23 68 59 78 98 78 00 02 09 18 d8 78 00 04 09 18 18 79 00 06 09 18 5a 79 98 79 00 02 02 43", "opcode 0x37: endereço e máscara u16"),
        (0x08022BAE, "08 88 90 43 08 80", "opcode 0x37: lê, BIC e grava halfword"),
        (0x08022BB4, "20 68 07 30 20 60 10 bc 01 bc 00 47", "opcode 0x37: cursor +7"),
        (0x08022BC4, "10 b5 0f 4c 22 68 53 78 90 78 00 02 1b 18 d0 78 00 04 1b 18 10 79 00 06 1b 18 51 79 90 79 00 02 09 18 d0 79 00 04 09 18 10 7a 00 06 09 18", "opcode 0x38: endereço e máscara u32"),
        (0x08022BF2, "18 68 88 43 18 60", "opcode 0x38: lê, BIC e grava word"),
        (0x08022BF8, "20 68 09 30 20 60 10 bc 01 bc 00 47", "opcode 0x38: cursor +9"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08022B88: 0x02023D74,
        0x08022BC0: 0x02023D74,
        0x08022C04: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, BIC in-place, larguras dos operands e avanços do cursor.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
