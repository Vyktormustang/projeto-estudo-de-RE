#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida dispatch e padrões Thumb locais dos opcodes de batalha 0x1B–0x1D."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x1B: 0x080215DD, 0x1C: 0x08021641, 0x1D: 0x080216B9}


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
        (0x080215DC, "70 b5 81 b0 13 48 06 68 00 2e 1f d1", "opcode 0x1B: gate pelo word de controle"),
        (0x080215E8, "12 4d 28 68 40 78 f5 f7 19 fc 11 4c 20 70", "opcode 0x1B: seletor e battler mapeado"),
        (0x080215F6, "11 49 20 78 58 22 50 43 4c 31 40 18 06 60 20 78 50 43 40 18 00 90", "opcode 0x1B: endereço por stride 0x58 e zera word"),
        (0x0802160C, "00 20 28 21 00 22 04 23 ec f7 ec fc 20 78 f5 f7 15 fe f1 f7 d3 fa", "opcode 0x1B: chamadas auxiliares"),
        (0x08021622, "28 68 02 30 28 60", "opcode 0x1B: cursor +2"),
        (0x08021640, "30 b5 16 4d 28 68 40 78 f5 f7 ec fb", "opcode 0x1C: entrada e mapeamento do seletor"),
        (0x08021650, "2a 68 94 78 d1 78 09 02 64 18 11 79 09 04 64 18 51 79 09 06 64 18 93 79 d1 79 09 02 5b 18 11 7a 09 04 5b 18 51 7a 09 06 5b 18", "opcode 0x1C: operands u32 little-endian"),
        (0x0802167A, "09 4a 58 21 41 43 10 1c 4c 30 08 18 00 68 20 40 00 28 0a d0", "opcode 0x1C: word +0x4C e teste da máscara"),
        (0x0802168E, "88 18 00 8d 00 28 06 d0 2b 60 08 e0", "opcode 0x1C: HP e cursor redirecionado"),
        (0x080216A4, "03 49 08 68 0a 30 08 60", "opcode 0x1C: cursor +10 alternativo"),
        (0x080216B8, "30 b5 16 4d 28 68 40 78 f5 f7 b0 fb", "opcode 0x1D: entrada e mapeamento do seletor"),
        (0x080216C8, "2a 68 94 78 d1 78 09 02 64 18 11 79 09 04 64 18 51 79 09 06 64 18 93 79 d1 79 09 02 5b 18 11 7a 09 04 5b 18 51 7a 09 06 5b 18", "opcode 0x1D: operands u32 little-endian"),
        (0x080216F2, "09 4a 58 21 41 43 10 1c 50 30 08 18 00 68 20 40 00 28 0a d0", "opcode 0x1D: word +0x50 e teste da máscara"),
        (0x08021706, "88 18 00 8d 00 28 06 d0 2b 60 08 e0", "opcode 0x1D: HP e cursor redirecionado"),
        (0x0802171C, "03 49 08 68 0a 30 08 60", "opcode 0x1D: cursor +10 alternativo"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08021630: 0x02023BC8,
        0x08021634: 0x02023D74,
        0x08021638: 0x02023BC4,
        0x0802163C: 0x02023BE4,
        0x0802169C: 0x02023D74,
        0x080216A0: 0x02023BE4,
        0x080216B4: 0x02023D74,
        0x08021714: 0x02023D74,
        0x08021718: 0x02023BE4,
        0x0802172C: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados padrões Thumb locais, leitura de operands, campos e cursor.")
    print("Validação estática; nomes/semântica upstream são cross-reference, não prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
