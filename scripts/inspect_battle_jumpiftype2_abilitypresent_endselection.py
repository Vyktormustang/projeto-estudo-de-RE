#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x42–0x44."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x42: 0x08022D71, 0x43: 0x08022DCD, 0x44: 0x08022E19}


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
        (0x08022D70, "10 b5 11 4c 20 68 40 78 f4 f7 54 f8 00 06 00 0e 23 68 0e 4a 58 21 48 43 80 18 01 1c 21 31 9a 78 09 78 8a 42 03 d0 22 30 00 78 82 42 10 d1", "opcode 0x42: mapeia seletor e compara dois bytes"),
        (0x08022D9E, "d9 78 18 79 00 02 01 43 58 79 00 04 01 43 98 79 00 06 01 43 21 60 06 e0", "opcode 0x42: lê destino inline se houver igualdade"),
        (0x08022DC0, "d8 1d 20 60 10 bc 01 bc 00 47", "opcode 0x42: ramo falso cursor +7"),
        (0x08022DCC, "10 b5 81 b0 0c 4c 20 68 42 78 00 20 00 90 13 20 00 21 00 23 f7 f7 9a f8 00 06 00 28 0e d0", "opcode 0x43: chama helper e testa retorno"),
        (0x08022DEA, "22 68 91 78 d0 78 00 02 01 43 10 79 00 04 01 43 50 79 00 06 01 43 21 60 04 e0", "opcode 0x43: retorno não-zero lê destino inline"),
        (0x08022E08, "20 68 06 30 20 60 01 b0 10 bc 01 bc 00 47", "opcode 0x43: retorno zero cursor +6"),
        (0x08022E18, "04 48 00 78 04 49 09 68 40 18 54 30 01 21 01 70 70 47", "opcode 0x44: calcula endereço e grava byte 1"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08022DB8: 0x02023D74,
        0x08022DBC: 0x02023BE4,
        0x08022E04: 0x02023D74,
        0x08022E2C: 0x02023D6B,
        0x08022E30: 0x02023FE8,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, comparações tipo, helper/ramificação e gravação local de 0x44.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
