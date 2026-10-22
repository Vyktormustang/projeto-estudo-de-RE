#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x3C–0x3E."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x3C: 0x08022CC1, 0x3D: 0x08022CCD, 0x3E: 0x08022CED}


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
        (0x08022CC0, "00 b5 f4 f7 53 fc 01 bc 00 47", "opcode 0x3C: chama helper de retorno"),
        (0x0801756C, "07 4b 08 48 00 68 81 68 0a 1c 20 32 10 78 01 38 10 70 00 06 80 0d 09 18 08 68 18 60 70 47", "helper: decrementa contador, obtém ponteiro e atualiza cursor"),
        (0x08022CCC, "04 48 00 21 01 70 04 48 01 70 04 49 0b 20 08 70 70 47", "opcode 0x3D: limpa dois bytes, grava 0x0B e retorna"),
        (0x08022CEC, "03 49 00 20 08 70 03 49 0b 20 08 70 70 47", "opcode 0x3E: limpa um byte, grava 0x0B e retorna"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x0801758C: 0x02023D74,
        0x08017590: 0x02023FF4,
        0x08022CE0: 0x02023DCC,
        0x08022CE4: 0x02023BC4,
        0x08022CE8: 0x02023BE3,
        0x08022CFC: 0x02023BC4,
        0x08022D00: 0x02023BE3,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, helper chamado por 0x3C, gravações dos handlers e literais locais.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
