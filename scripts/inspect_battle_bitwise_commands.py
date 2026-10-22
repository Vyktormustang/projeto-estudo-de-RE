#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x33–0x35."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x33: 0x08022AB9, 0x34: 0x08022AE5, 0x35: 0x08022B1D}


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
        (0x08022AB8, "09 4b 1a 68 51 78 90 78 00 02 09 18 d0 78 00 04 09 18 10 79 00 06 09 18 08 78 52 79 10 43 08 70", "opcode 0x33: OR byte in-place"),
        (0x08022AD8, "18 68 06 30 18 60 70 47", "opcode 0x33: cursor +6"),
        (0x08022AE4, "10 b5 0c 4c 23 68 5a 78 98 78 00 02 12 18 d8 78 00 04 12 18 18 79 00 06 12 18 59 79 98 79 00 02 01 43", "opcode 0x34: OR halfword operands"),
        (0x08022B06, "10 88 01 43 11 80", "opcode 0x34: lê, OR e grava halfword"),
        (0x08022B0C, "20 68 07 30 20 60 10 bc 01 bc 00 47", "opcode 0x34: cursor +7"),
        (0x08022B1C, "10 b5 0f 4c 22 68 53 78 90 78 00 02 1b 18 d0 78 00 04 1b 18 10 79 00 06 1b 18 51 79 90 79 00 02 09 18 d0 79 00 04 09 18 10 7a 00 06 09 18", "opcode 0x35: monta endereço e imediato u32"),
        (0x08022B4A, "18 68 08 43 18 60", "opcode 0x35: OR word in-place"),
        (0x08022B50, "20 68 09 30 20 60 10 bc 01 bc 00 47", "opcode 0x35: cursor +9"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08022AE0: 0x02023D74,
        0x08022B18: 0x02023D74,
        0x08022B5C: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, ORs in-place, larguras dos operands e avanços do cursor.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
