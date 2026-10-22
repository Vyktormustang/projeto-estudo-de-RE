#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x3F–0x41."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x3F: 0x08022D05, 0x40: 0x0801DBA1, 0x41: 0x08022D41}


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
        (0x08022D04, "00 b5 f4 f7 31 fc 0b 4b 18 68 c0 68 01 1c 20 31 08 78 00 28 01 d0 01 38 08 70 07 4a 18 68 c1 68 08 1c 20 30 00 78 80 00 09 18 08 68 10 60 01 bc 00 47", "opcode 0x3F: restaura script e seleciona word por contador"),
        (0x0801DB10, "70 b5 81 b0 00 06 00 0e 09 04 0e 0c 0f 49 0d 68 2c 18 0f 48 01 78 29 20 08 40 00 28 20 d0", "helper condicional: testa máscara 0x29"),
        (0x0801DB2E, "0d 49 0d 4b 18 78 40 00 40 18 00 22 02 80 0b 49 18 78 40 00 40 18 02 80 6c 78 a8 78 00 02 04 43 e8 78 00 04 04 43 28 79 00 06 04 43 16 e0", "helper: limpa halfwords indexados e monta destino inline"),
        (0x0801DB8A, "04 48 04 60 01 b0 70 bc 01 bc 00 47", "helper: grava cursor de continuação/destino"),
        (0x0801DBA0, "00 b5 11 49 11 48 00 78 00 01 40 18 00 78 c0 07 00 28 25 d0 0e 4a 0f 48 01 88 48 00 40 18 80 00 80 18 01 7a 02 20 08 40 00 28 19 d0", "opcode 0x40: testes em registro e byte de tabela"),
        (0x0801DBCC, "0a 4a 10 78 01 21 08 43 10 70 05 20 00 21 ff f7 99 ff 07 49 01 20 88 71 10 e0", "opcode 0x40: define bit, chama helper e grava byte"),
        (0x0801DC00, "02 49 08 68 05 30 08 60 01 bc 00 47", "opcode 0x40: ramo sem condição avança cursor +5"),
        (0x08022D40, "10 b5 0a 4c 20 68 05 30 f4 f7 ea fb 22 68 51 78 90 78 00 02 01 43 d0 78 00 04 01 43 10 79 00 06 01 43 21 60 10 bc 01 bc 00 47", "opcode 0x41: empilha retorno e lê destino inline"),
        (0x08017520, "10 b5 07 49 09 68 8b 68 1c 1c 20 34 21 78 4a 1c 22 70 09 06 89 0d 5b 18 18 60 10 bc 01 bc 00 47", "helper: incrementa contador e empilha word"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08022D38: 0x02023FF4,
        0x08022D3C: 0x03004F84,
        0x0801DB5C: 0x02023D74,
        0x0801DB60: 0x02023DCC,
        0x0801DB64: 0x02023DA0,
        0x0801DB68: 0x02023D6C,
        0x0801DB6C: 0x02023DA8,
        0x0801DB98: 0x02023D6C,
        0x0801DB9C: 0x02023D74,
        0x0801DBE8: 0x02023E8C,
        0x0801DBEC: 0x02023D6C,
        0x0801DBF0: 0x08250C04,
        0x0801DBF4: 0x02023D4A,
        0x0801DBF8: 0x02023DCC,
        0x0801DBFC: 0x02023E82,
        0x0801DC0C: 0x02023D74,
        0x08022D6C: 0x02023D74,
        0x08017540: 0x02023FF4,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados end3/callback, testes condicionais, saltos inline e push de retorno locais.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
