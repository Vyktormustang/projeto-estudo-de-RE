#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida dispatch e padrões locais dos opcodes de batalha 0x21–0x23."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x21: 0x08021989, 0x22: 0x08021A0D, 0x23: 0x08021A69}


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
        (0x08021988, "70 b5 14 4c 20 68 40 78 f5 f7 48 fa 12 4d 28 70", "opcode 0x21: seletor mapeado e armazenado"),
        (0x08021998, "22 68 91 78 d0 78 00 02 09 18 10 79 00 04 09 18 50 79 00 06 0e 18 d1 79 10 7a 00 02 09 18 50 7a 00 04 09 18 90 7a 00 06 0b 18", "opcode 0x21: máscara e destino little-endian"),
        (0x080219C2, "90 79 00 28 0f d0 06 48 29 78 89 00 09 18 08 68 30 40 00 28 13 d1", "opcode 0x21: ramo de inversão e teste"),
        (0x080219E8, "04 48 29 78 89 00 09 18 08 68 30 40 00 28 03 d0 23 60 04 e0", "opcode 0x21: teste inverso, destino ou cursor +11"),
        (0x08021A00, "10 1c 0b 30 20 60", "opcode 0x21: avanço de cursor +11"),
        (0x08021A0C, "70 b5 11 4c 20 68 40 78 f5 f7 06 fa", "opcode 0x22: entrada e seletor mapeado"),
        (0x08021A1C, "23 68 9d 78 da 78 19 79 09 02 52 18 59 79 09 04 52 18 99 79 09 06 56 18", "opcode 0x22: byte e destino inline u32"),
        (0x08021A34, "08 4a 58 21 48 43 81 18 08 1c 21 30 00 78 a8 42 04 d0", "opcode 0x22: campos +0x21/+0x22"),
        (0x08021A50, "26 60 05 e0", "opcode 0x22: redirecionamento do cursor"),
        (0x08021A5C, "d8 1d 20 60", "opcode 0x22: cursor +7 alternativo"),
        (0x08021A68, "f0 b5 4f 46 46 46 c0 b4 00 26 0f 48 00 68 50 30 81 46 0e 48 00 68 40 78 f5 f7 d0 f9", "opcode 0x23: entrada, cursor e seletor"),
        (0x08021A84, "0c 49 08 70 0c 4a 02 21 01 40 09 06 49 0e 89 18 09 78 88 46", "opcode 0x23: salva índice e seleciona byte associado"),
        (0x08021A98, "09 48 00 7f 06 28 01 d9 00 f0 9b fc 80 00 07 49 40 18 00 68 87 46", "opcode 0x23: estado até 6 e jump table"),
        (0x080223B0, "0d 48 05 68 00 2d 10 d1 0c 4c 0d 4a 10 78 58 21 48 43 00 19 00 23 c5 85 10 78 48 43 00 19 20 30 03 70 08 49 08 68 02 30 08 60", "opcode 0x23: saída terminal, limpeza e cursor +2"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x080219DC: 0x02023D74,
        0x080219E0: 0x02023BC4,
        0x080219E4: 0x02023DFC,
        0x080219FC: 0x02023DFC,
        0x08021A54: 0x02023D74,
        0x08021A58: 0x02023BE4,
        0x08021AB0: 0x02023FE8,
        0x08021AB4: 0x02023D74,
        0x08021AB8: 0x02023D6D,
        0x08021ABC: 0x02023F4E,
        0x08021AC0: 0x02023FC4,
        0x08021AC4: 0x08021AC8,
        0x080223E8: 0x02023BC8,
        0x080223EC: 0x02023BE4,
        0x080223F0: 0x02023D6D,
        0x080223F4: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    state_targets = [
        0x08021AE4,
        0x08021B50,
        0x08021C6A,
        0x08021F78,
        0x0802207C,
        0x08022368,
        0x080223B0,
    ]
    for index, wanted in enumerate(state_targets):
        actual = read32(rom, 0x08021AC8 + index * 4)
        if actual != wanted:
            raise SystemExit(f"estado {index}: destino 0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados operands, ramos, campos locais e dispatch de sete estados.")
    print("Validação estática; interpretação upstream não é prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
