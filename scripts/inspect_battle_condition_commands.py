#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida dispatch e padrões Thumb locais dos opcodes de batalha 0x1E–0x20."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x1E: 0x08021731, 0x1F: 0x08021819, 0x20: 0x08021891}


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
        (0x08021730, "f0 b5 47 46 80 b4 81 b0 12 4e 32 68 95 78 a8 46 d1 78 10 79 00 02 09 18 50 79 00 04 09 18 90 79 00 06 0f 18", "opcode 0x1E: seletor, operand byte e destino inline"),
        (0x08021754, "50 78 08 28 1a d1 0b 48 01 78 00 20 00 90 0d 20 2a 1c 00 23 f8 f7 d6 fb", "opcode 0x1E: ramo seletor 8 / chamada auxiliar"),
        (0x08021790, "09 28 19 d1 0a 48 01 78 00 20 00 90 0c 20 2a 1c 00 23 f8 f7 b9 fb", "opcode 0x1E: ramo seletor 9 / chamada auxiliar"),
        (0x080217C8, "50 78 f5 f7 2b fb 00 06 04 0e 09 49 58 20 60 43 40 18 20 30 01 78 41 45 10 d1", "opcode 0x1E: comparação direta de byte"),
        (0x080217E2, "06 48 01 70 37 60 01 78 20 1c a5 f0 f0 fc 03 48 44 75", "opcode 0x1E: gravação de estado, cursor e chamada"),
        (0x08021804, "30 68 07 30 30 60", "opcode 0x1E: cursor +7 alternativo"),
        (0x08021818, "70 b5 05 48 00 68 44 78 01 2c 09 d1", "opcode 0x1F: seletor lateral"),
        (0x08021824, "03 48 00 78 53 f0 d6 fc", "opcode 0x1F: helper do primeiro battler"),
        (0x08021838, "0f 48 00 78 53 f0 cc fc 01 24 04 40", "opcode 0x1F: helper alternativo e bit de retorno"),
        (0x08021842, "04 40 0d 4e 33 68 9a 78 d8 78 00 02 02 43 19 79 58 79 00 02 09 18 98 79 00 04 09 18 d8 79 00 06 0d 18", "opcode 0x1F: flags u16 e destino u32 inline"),
        (0x08021864, "06 49 60 00 40 18 00 88 02 40 00 2a 08 d0 35 60 09 e0", "opcode 0x1F: teste de máscara e redirecionamento"),
        (0x08021884, "18 1c 08 30 30 60", "opcode 0x1F: cursor +8 alternativo"),
        (0x08021890, "30 b5 00 25 0b 4c 20 68 40 78 f5 f7 c3 fa", "opcode 0x20: mapeamento do battler"),
        (0x080218A2, "09 4a 23 68 58 21 48 43 d9 78 40 18 18 32 80 18 02 78 98 78 05 28 49 d8", "opcode 0x20: byte por índice e seleção do modo"),
        (0x080218BA, "80 00 03 49 40 18 00 68 87 46", "opcode 0x20: dispatch por tabela de seis modos"),
        (0x080218E8, "02 48 00 68 00 79 82 42 2d d1 29 e0", "opcode 0x20: comparação de igualdade"),
        (0x08021928, "03 48 00 68 00 79 02 40 00 2a 0c d0 08 e0", "opcode 0x20: comparação de bits"),
        (0x08021948, "68 1c 00 06 05 0e 00 2d 10 d0 07 4b 1a 68 51 79 90 79 00 02 09 18 d0 79 00 04 09 18 10 7a 00 06 09 18 19 60 06 e0", "opcode 0x20: destino inline ou falha"),
        (0x08021974, "03 49 08 68 09 30 08 60", "opcode 0x20: cursor +9 alternativo"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08021784: 0x02023D74,
        0x08021788: 0x02023D6B,
        0x0802178C: 0x02023D6A,
        0x080217C0: 0x02023D6B,
        0x080217C4: 0x02023D6A,
        0x080217F8: 0x02023BE4,
        0x080217FC: 0x02023D6A,
        0x08021800: 0x02023FC4,
        0x08021830: 0x02023D74,
        0x08021834: 0x02023D6B,
        0x08021878: 0x02023D6C,
        0x0802187C: 0x02023D74,
        0x08021880: 0x02023DDE,
        0x080218C4: 0x02023D74,
        0x080218C8: 0x02023BE4,
        0x080218CC: 0x080218D0,
        0x08021970: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    compare_targets = [0x080218E8, 0x080218F8, 0x08021908, 0x08021918, 0x08021928, 0x0802193C]
    for index, wanted in enumerate(compare_targets):
        actual = read32(rom, 0x080218D0 + index * 4)
        if actual != wanted:
            raise SystemExit(f"destino de comparação {index}: 0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados padrões Thumb, operands, tabelas locais, chamadas e avanços/redirecionamentos de cursor.")
    print("Validação estática; nomes e semântica upstream são cross-reference, não prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
