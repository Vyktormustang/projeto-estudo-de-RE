#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida dispatch e padrões Thumb locais dos opcodes de batalha 0x18–0x1A."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x18: 0x08021231, 0x19: 0x080212AD, 0x1A: 0x080215A1}


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
        (0x08021230, "00 b5 08 48 00 68 40 78 f5 f7 f4 fd 06 4a 10 70 06 4b d8 78 06 28 0d d8", "opcode 0x18: operand, helper e limite do índice"),
        (0x08021248, "05 49 12 78 58 20 42 43 4c 31 0c e0", "opcode 0x18: caminho de offset +0x4C"),
        (0x08021264, "0c 49 12 78 58 20 42 43 50 31 52 18 0a 49 d8 78 80 00 40 18 01 68 10 68 88 43 10 60", "opcode 0x18: caminho de offset +0x50 e limpeza de bits"),
        (0x08021280, "07 48 00 22 c2 70 07 49 08 68 02 30 08 60 06 48 82 75 01 bc 00 47", "opcode 0x18: limpeza de estado e cursor +2"),
        (0x080212AC, "f0 b5 4f 46 46 46 c0 b4 81 b0 18 48 02 68 91 78 06 1c 00 29 36 d0", "opcode 0x19: entrada e bifurcação por cursor[2]"),
        (0x080212E4, "31 68 cc 78 08 79 00 02 04 43 48 79 00 04 04 43 88 79 00 06 04 43 f6 f7 37 f9 34 60", "opcode 0x19: leitura de pointer inline e chamada"),
        (0x08021330, "50 78 01 28 10 d1", "opcode 0x19: seleção por cursor[1]"),
        (0x0802136A, "1d 48 01 78 1d 4a 47 46 3b 78 98 00 80 18 02 68 11 40 00 29 00 d0 04 e1", "opcode 0x19: máscara de battler e teste de presença"),
        (0x08021382, "19 49 58 20 58 43 40 18 00 8d 00 28 00 d0 fc e0", "opcode 0x19: seleção de registro e teste do halfword +0x28"),
        (0x08021392, "16 4d 11 07 28 68 08 43 28 60 30 68 07 30 f6 f7 be f8 34 60", "opcode 0x19: marcação de estado e push de cursor+7"),
        (0x0802158C, "30 68 07 30 30 60 01 b0 18 bc 98 46 a1 46 f0 bc 01 bc 00 47", "opcode 0x19: cursor +7 e epílogo"),
        (0x080215A0, "30 b5 0b 48 00 68 00 28 0f d1 0a 4d 28 68 40 78 f5 f7 38 fc 08 4c 20 70 00 20 ec f7 bb fd 20 78 f5 f7 42 fe 28 68 02 30 28 60 30 bc 01 bc 00 47", "opcode 0x1A: espera, chamadas e cursor +2"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08021254: 0x02023D74,
        0x08021258: 0x02023BC4,
        0x0802125C: 0x02023E82,
        0x08021260: 0x02023BE4,
        0x0802129C: 0x0825053C,
        0x080212A4: 0x02023D74,
        0x080212A8: 0x02023FC4,
        0x08021318: 0x02023D74,
        0x0802131C: 0x02023BC4,
        0x08021320: 0x02023DD0,
        0x08021324: 0x0825E45C,
        0x0802132C: 0x0000FDFF,
        0x0802134C: 0x02023D6B,
        0x08021350: 0x02023D6C,
        0x08021354: 0x081D8674,
        0x080213D0: 0x02023BC4,
        0x080213D4: 0x02023D6C,
        0x080213D8: 0x02023D6B,
        0x080213E4: 0x0825E45C,
        0x080213E8: 0x02023BE4,
        0x080213EC: 0x02023DD0,
        0x080213F0: 0x03004F90,
        0x08021570: 0x081D8C6C,
        0x08021580: 0x081D8FA3,
        0x080215A0 + 0x30: 0x02023BC8,
        0x080215A0 + 0x34: 0x02023D74,
        0x080215A0 + 0x38: 0x02023BC4,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados padrões Thumb locais, tabelas/flags, ponteiros e avanços/redirecionamentos principais.")
    print("Validação estática; nomes e semântica upstream são cross-reference, não prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
