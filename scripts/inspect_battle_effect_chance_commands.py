#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida dispatch e padrões Thumb locais dos opcodes de efeito 0x15–0x17."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x15: 0x08021125, 0x16: 0x08021211, 0x17: 0x08021221}


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
        (0x08021124, "10 b5 0a 4a 0a 48 01 78 58 20 48 43 80 18 20 30 00 78 20 28 12 d1", "opcode 0x15: índice de battler, stride 0x58 e teste +0x20"),
        (0x0802113A, "07 4a 07 48 01 88 48 00 40 18 80 00 80 18 40 79 44 00 10 e0", "opcode 0x15: registro ×12, byte +5 e dobra condicional"),
        (0x08021160, "0b 4a 0c 48 01 88 48 00 40 18 80 00 80 18 44 79", "opcode 0x15: leitura da chance sem dobra"),
        (0x08021172, "da 78 80 20 10 40 00 28 11 d0", "opcode 0x15: testa bit 0x80 do estado local"),
        (0x0802117C, "07 48 01 78 29 20 08 40 00 28 0b d1 7f 20 10 40 d8 70 1e e0", "opcode 0x15: máscara 0x29 e limpeza de bit"),
        (0x080211A0, "23 f0 92 fe 00 04 00 0c 64 21 c3 f1 6b fa 00 04 00 0c a0 42", "opcode 0x15: chamadas locais RNG/divisão e comparação"),
        (0x080211B6, "08 48 c0 78 00 28 15 d0 07 48 01 78 29 20 08 40 00 28 0f d1 63 2c 08 d9", "opcode 0x15: estado não-zero, máscara e limite 99"),
        (0x080211CE, "00 20 80 21 fe f7 a5 fe", "opcode 0x15: chamada do helper com argumento 0x80"),
        (0x080211E0, "00 20 00 21 fe f7 9c fe", "opcode 0x15: chamada do helper com argumento zero"),
        (0x080211EA, "06 49 08 68 01 30 08 60 05 48 00 21 c1 70 04 48 81 75 10 bc 01 bc 00 47", "opcode 0x15: cursor +1, limpeza e retorno"),
        (0x08021210, "00 b5 01 20 00 21 fe f7 83 fe 01 bc 00 47", "opcode 0x16: helper(1, 0)"),
        (0x08021220, "00 b5 00 20 00 21 fe f7 7b fe 01 bc 00 47", "opcode 0x17: helper(0, 0)"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08021150: 0x02023BE4,
        0x08021154: 0x02023D6B,
        0x08021158: 0x08250C04,
        0x0802115C: 0x02023D4A,
        0x08021190: 0x08250C04,
        0x08021194: 0x02023D4A,
        0x08021198: 0x02023E82,
        0x0802119C: 0x02023DCC,
        0x080211D8: 0x02023E82,
        0x080211DC: 0x02023DCC,
        0x08021204: 0x02023D74,
        0x08021208: 0x02023E82,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados padrões dos opcodes 0x15–0x17, chamadas, cursor e literais locais.")
    print("Validação estática; rótulos semânticos upstream não são evidência local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
