#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x2D–0x2F."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x2D: 0x080228F5, 0x2E: 0x08022979, 0x2F: 0x080229A1}


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
        (0x080228F4, "f0 b5 00 27 1b 4b 19 68 4a 78 88 78 00 02 12 18", "opcode 0x2D: entrada e primeiro endereço inline"),
        (0x08022910, "4a 79 88 79 00 02 12 18 c8 79 00 04 12 18 08 7a 00 06 14 18 4e 7a", "opcode 0x2D: segundo endereço e tamanho"),
        (0x08022926, "8a 7a c8 7a 00 02 12 18 08 7b 00 04 12 18 48 7b 00 06 12 18 94 46", "opcode 0x2D: destino inline u32"),
        (0x0802293C, "00 21 b7 42 0d d2 28 78 22 78 90 42 02 d1", "opcode 0x2D: comparação byte a byte"),
        (0x08022948, "02 d1 78 1c 00 06 07 0e 01 35 01 34", "opcode 0x2D: contador de iguais e avanço das regiões"),
        (0x0802295E, "b7 42 04 d0 60 46 04 e0", "opcode 0x2D: destino se houver diferença"),
        (0x0802296C, "18 68 0e 30 18 60 f0 bc 01 bc 00 47", "opcode 0x2D: cursor +14 se iguais"),
        (0x08022978, "08 4b 1a 68 51 78 90 78 00 02 09 18 d0 78 00 04 09 18 10 79 00 06 09 18 50 79 08 70", "opcode 0x2E: endereço inline e gravação do byte"),
        (0x08022994, "18 68 06 30 18 60 70 47", "opcode 0x2E: cursor +6"),
        (0x080229A0, "09 4b 1a 68 51 78 90 78 00 02 09 18 d0 78 00 04 09 18 10 79 00 06 09 18 50 79", "opcode 0x2F: endereço inline e imediato"),
        (0x080229B8, "50 79 0a 78 80 18 08 70", "opcode 0x2F: soma ao byte apontado e grava"),
        (0x080229C0, "18 68 06 30 18 60 70 47", "opcode 0x2F: cursor +6"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08022968: 0x02023D74,
        0x0802299C: 0x02023D74,
        0x080229C8: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, operands, comparações, escritas e cursor local.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
