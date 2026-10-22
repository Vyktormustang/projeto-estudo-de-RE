#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida dispatch e padrões Thumb locais dos opcodes de texto 0x10–0x12."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x10: 0x0801FD51, 0x11: 0x0801FD91, 0x12: 0x0801FDD5}


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
        (0x0801FD50, "10 b5 0b 48 00 68 00 28 0f d1", "entrada/espera local do opcode 0x10"),
        (0x0801FD5C, "21 68 48 78 89 78 09 02 08 43", "leitura e combinação do operand de dois bytes"),
        (0x0801FD6A, "f7 f7 1f fb", "chamada local do opcode 0x10"),
        (0x0801FD6E, "20 68 03 30 20 60", "avanço de três bytes no opcode 0x10"),
        (0x0801FD74, "05 49 01 20 c8 71", "definição de flag local após mensagem"),
        (0x0801FD90, "30 b5 0c 4d 0c 48 00 78 28 70", "entrada e battler no opcode 0x11"),
        (0x0801FD9C, "20 68 41 78 80 78 00 02 01 43", "leitura/combinação local do operand"),
        (0x0801FDA6, "00 20 ee f7 20 fb", "chamada local do opcode 0x11"),
        (0x0801FDB2, "20 68 03 30 20 60", "avanço de três bytes no opcode 0x11"),
        (0x0801FDD4, "70 b5 06 48 04 68 00 2c 21 d1", "entrada/espera do opcode 0x12"),
        (0x0801FDE0, "f0 79 00 28 0a d1", "teste local da flag de exibição"),
        (0x0801FDE6, "04 49 08 68 03 30 08 60", "avanço de três bytes quando não há exibição"),
        (0x0801FDFC, "0a 4d 2a 68 51 78 90 78 00 02 01 43", "leitura local de operand e contador"),
        (0x0801FE0A, "18 88 01 30 18 80", "incremento local do contador halfword"),
        (0x0801FE18, "00 21 1c 80 d0 1c 28 60 f1 71", "reset/avanço/limpeza de flag"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x0801FD80: 0x02023BC8,
        0x0801FD84: 0x02023D74,
        0x0801FD88: 0x02023D6B,
        0x0801FD8C: 0x02023E82,
        0x0801FDC4: 0x02023BC4,
        0x0801FDC8: 0x02023D6B,
        0x0801FDCC: 0x02023D74,
        0x0801FDD0: 0x02023E82,
        0x0801FDF0: 0x02023BC8,
        0x0801FDF4: 0x02023E82,
        0x0801FDF8: 0x02023D74,
        0x0801FE28: 0x02023D74,
        0x0801FE2C: 0x02023E7C,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados operandos de dois bytes, esperas locais, flag de exibição e cursor +3.")
    print("Validação estática; nomenclatura upstream e execução permanecem separadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
