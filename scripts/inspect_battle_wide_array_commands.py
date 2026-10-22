#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x2A–0x2C."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x2A: 0x08022711, 0x2B: 0x080227B9, 0x2C: 0x0802286D}


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


def verify_table(rom: bytes, address: int, targets: list[int], label: str) -> None:
    for index, wanted in enumerate(targets):
        actual = read32(rom, address + index * 4)
        if actual != wanted:
            raise SystemExit(
                f"{label}[{index}]=0x{actual:08X}, esperado 0x{wanted:08X}"
            )


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
        (0x08022710, "70 b5 12 4b 19 68 4e 78 8a 78 c8 78 00 02 12 18", "opcode 0x2A: entrada e address operand"),
        (0x08022726, "48 79 00 06 15 18 8c 79 c8 79 00 02 04 43", "opcode 0x2A: halfword imediato e leitura do seletor"),
        (0x08022734, "0a 7a 48 7a 00 02 12 18 88 7a 00 04 12 18 c8 7a 00 06 12 18 0c 31 19 60", "opcode 0x2A: destino u32 e cursor +12"),
        (0x0802274C, "05 2e 2f d8 b0 00 03 49 40 18 00 68 87 46", "opcode 0x2A: valida seletor e dispatch indireto"),
        (0x0802277C, "28 88 a0 42 16 d1 14 e0", "opcode 0x2A: igualdade"),
        (0x08022784, "28 88 a0 42 12 d0 10 e0", "opcode 0x2A: desigualdade"),
        (0x0802278C, "28 88 a0 42 0e d9 0c e0", "opcode 0x2A: unsigned maior que"),
        (0x08022794, "28 88 a0 42 0a d2 08 e0", "opcode 0x2A: unsigned menor que"),
        (0x0802279C, "28 88 04 40 00 2c 05 d0 03 e0", "opcode 0x2A: bits comuns"),
        (0x080227A6, "28 88 04 40 00 2c 00 d1 1a 60", "opcode 0x2A: sem bits comuns e grava destino"),
        (0x080227B8, "70 b5 15 4b 19 68 4e 78 8a 78 c8 78 00 02 12 18", "opcode 0x2B: entrada e address operand"),
        (0x080227CE, "48 79 00 06 15 18 8c 79 c8 79 00 02 04 43 08 7a", "opcode 0x2B: imediato u32"),
        (0x080227E8, "8a 7a c8 7a 00 02 12 18 08 7b 00 04 12 18 48 7b 00 06 12 18 0e 31 19 60", "opcode 0x2B: destino u32 e cursor +14"),
        (0x08022800, "05 2e 2f d8 b0 00 03 49 40 18 00 68 87 46", "opcode 0x2B: valida seletor e dispatch indireto"),
        (0x08022830, "28 68 a0 42 16 d1 14 e0", "opcode 0x2B: igualdade"),
        (0x08022838, "28 68 a0 42 12 d0 10 e0", "opcode 0x2B: desigualdade"),
        (0x08022840, "28 68 a0 42 0e d9 0c e0", "opcode 0x2B: unsigned maior que"),
        (0x08022848, "28 68 a0 42 0a d2 08 e0", "opcode 0x2B: unsigned menor que"),
        (0x08022850, "28 68 20 40 00 28 05 d0 03 e0", "opcode 0x2B: bits comuns"),
        (0x0802285A, "28 68 20 40 00 28 00 d1 1a 60", "opcode 0x2B: sem bits comuns e grava destino"),
        (0x0802286C, "f0 b5 15 4a 13 68 59 78 98 78 00 02 09 18 d8 78", "opcode 0x2C: entrada e endereço do array 1"),
        (0x08022884, "0d 18 59 79 98 79 00 02 09 18 d8 79 00 04 09 18 18 7a 00 06 0c 18", "opcode 0x2C: endereço do array 2"),
        (0x0802289A, "5e 7a 99 7a d8 7a 00 02 09 18 18 7b 00 04 09 18 58 7b 00 06 09 18 8c 46", "opcode 0x2C: tamanho u8, destino e init"),
        (0x080228B2, "00 21 b1 42 15 d2 28 78 27 78 b8 42 03 d0", "opcode 0x2C: loop compara bytes e trata divergência"),
        (0x080228C8, "01 35 01 34 48 1c 00 06 01 0e b1 42 06 d2", "opcode 0x2C: avança arrays e índice"),
        (0x080228DE, "10 68 0e 30 10 60 b1 42 01 d1 67 46 17 60", "opcode 0x2C: cursor +14 em mismatch ou destino em igualdade"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x0802275C: 0x02023D74,
        0x08022760: 0x08022764,
        0x08022810: 0x02023D74,
        0x08022814: 0x08022818,
        0x080228C4: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    verify_table(
        rom,
        0x08022760,
        [0x08022764, 0x0802277C, 0x08022784, 0x0802278C, 0x08022794, 0x0802279C, 0x080227A6],
        "jump table 0x2A",
    )
    verify_table(
        rom,
        0x08022814,
        [0x08022818, 0x08022830, 0x08022838, 0x08022840, 0x08022848, 0x08022850, 0x0802285A],
        "jump table 0x2B",
    )

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, operands, condições, cursor, literais e jump tables locais.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
