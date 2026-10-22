#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x30–0x32."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x30: 0x080229CD, 0x31: 0x080229F9, 0x32: 0x08022A4D}


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
        (0x080229CC, "09 4b 1a 68 51 78 90 78 00 02 09 18 d0 78 00 04 09 18 10 79 00 06 09 18", "opcode 0x30: endereço u32 inline"),
        (0x080229E4, "08 78 52 79 80 1a 08 70", "opcode 0x30: lê, subtrai e grava byte"),
        (0x080229EC, "18 68 06 30 18 60 70 47", "opcode 0x30: cursor +6"),
        (0x080229F8, "70 b5 13 4b 19 68 4a 78 88 78 00 02 12 18 c8 78", "opcode 0x31: entrada e endereço de destino"),
        (0x08022A10, "16 18 4a 79 88 79 00 02 12 18 c8 79 00 04 12 18 08 7a 00 06 15 18 4c 7a", "opcode 0x31: endereço de origem e tamanho"),
        (0x08022A28, "00 22 a2 42 06 da b0 18 a9 18 09 78 01 70 01 32 a2 42 f8 db", "opcode 0x31: loop sequencial de cópia byte a byte"),
        (0x08022A3C, "18 68 0a 30 18 60 70 bc 01 bc 00 47", "opcode 0x31: cursor +10"),
        (0x08022A4C, "f0 b5 19 4b 19 68 4a 78 88 78 00 02 12 18 c8 78", "opcode 0x32: entrada e endereço de destino"),
        (0x08022A64, "17 18 4a 79 88 79 00 02 12 18 c8 79 00 04 12 18 08 7a 00 06 16 18", "opcode 0x32: origem e ponteiro do índice-base"),
        (0x08022A7A, "4a 7a 88 7a 00 02 12 18 c8 7a 00 04 12 18 08 7b 00 06 15 18 4c 7b", "opcode 0x32: termina endereço do índice e lê comprimento"),
        (0x08022A90, "00 22 a2 42 08 da b8 18 29 78 51 18 71 18 09 78 01 70 01 32 a2 42 f6 db", "opcode 0x32: indexa origem e copia bytes"),
        (0x08022AA8, "18 68 0e 30 18 60 f0 bc 01 bc 00 47", "opcode 0x32: cursor +14"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x080229F4: 0x02023D74,
        0x08022A48: 0x02023D74,
        0x08022AB4: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, operands, leituras/escritas byte a byte e avanço do cursor.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
