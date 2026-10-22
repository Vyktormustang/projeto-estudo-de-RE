#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere localmente dispatch e padrões Thumb dos opcodes de batalha 0x27–0x29."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x27: 0x08022609, 0x28: 0x08022651, 0x29: 0x08022671}


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
        (0x08022608, "00 b5 06 49 08 78 01 38 08 70 00 06 00 28 09 d1", "opcode 0x27: decrementa e testa o byte local"),
        (0x08022618, "03 49 08 68 05 30 08 60 11 e0", "opcode 0x27: cursor +5 se o byte decrementado zerar"),
        (0x0802262C, "07 4b 1a 68 51 78 90 78 00 02 09 18 d0 78 00 04 09 18 10 79 00 06 09 18 19 60", "opcode 0x27: destino u32 inline little-endian"),
        (0x08022650, "06 4b 1a 68 51 78 90 78 00 02 09 18 d0 78 00 04 09 18 10 79 00 06 09 18 19 60 70 47", "opcode 0x28: lê destino inline e substitui cursor"),
        (0x08022670, "70 b5 10 4b 19 68 4e 78 8a 78 c8 78 00 02 12 18 08 79 00 04 12 18 48 79 00 06 15 18", "opcode 0x29: cabeçalho e montagem do primeiro u32 inline"),
        (0x0802268C, "8c 79 ca 79 08 7a 00 02 12 18 48 7a 00 04 12 18 88 7a 00 06 12 18 0b 31 19 60", "opcode 0x29: lê valor e destino, avança cursor +11"),
        (0x080226A6, "05 2e 2e d8 b0 00 02 49 40 18 00 68 87 46", "opcode 0x29: rejeita seletor >5 e dispatch indireto"),
        (0x080226D4, "28 78 a0 42 16 d1 14 e0", "opcode 0x29: condição de igualdade"),
        (0x080226DC, "28 78 a0 42 12 d0 10 e0", "opcode 0x29: condição de desigualdade"),
        (0x080226E4, "28 78 a0 42 0e d9 0c e0", "opcode 0x29: condição unsigned maior que"),
        (0x080226EC, "28 78 a0 42 0a d2 08 e0", "opcode 0x29: condição unsigned menor que"),
        (0x080226F4, "28 78 04 40 00 2c 05 d0 03 e0", "opcode 0x29: condição de bits comuns"),
        (0x080226FE, "28 78 04 40 00 2c 00 d1", "opcode 0x29: condição de ausência de bits comuns"),
        (0x08022706, "1a 60 70 bc 01 bc 00 47", "opcode 0x29: grava destino condicional ou retorna cursor padrão"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08022624: 0x02023D72,
        0x08022628: 0x02023D74,
        0x0802264C: 0x02023D74,
        0x0802266C: 0x02023D74,
        0x080226B4: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    comparison_targets = [
        0x080226BC,
        0x080226D4,
        0x080226DC,
        0x080226E4,
        0x080226EC,
        0x080226F4,
        0x080226FE,
    ]
    for index, wanted in enumerate(comparison_targets):
        actual = read32(rom, 0x080226B8 + index * 4)
        if actual != wanted:
            raise SystemExit(f"jump table local[{index}]: 0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, operands, ramos de comparação, literais e jump table local.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
