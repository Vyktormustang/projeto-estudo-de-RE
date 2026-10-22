#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere localmente o dispatch e os padrões dos opcodes de batalha 0x24–0x26."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x24: 0x080223F9, 0x25: 0x080225D9, 0x26: 0x080225F1}


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
        (0x080223F8, "f0 b5 47 46 80 b4 00 26 4c 48 00 68 00 28 00 d0 bf e0", "opcode 0x24: prólogo e saída sem avanço quando word != 0"),
        (0x0802240A, "00 25 64 20 29 1c 41 43 49 48 0c 18 20 1c 0b 21", "opcode 0x24: loop de seis registros, stride 0x64 e seletor inicial"),
        (0x08022442, "00 2e 04 d1 3d 48 01 78 02 22 11 43 01 70", "opcode 0x24: bit 0x02 no byte de resultado se soma zero"),
        (0x0802248A, "2c 4a 00 2e 03 d1 10 78 01 21 08 43 10 70 10 78 00 28", "opcode 0x24: base segunda varredura e bit 0x01"),
        (0x080224AC, "00 23 00 25 25 48 01 78 84 46 25 4f 8b 42 13 da", "opcode 0x24: contagem e base dos dados consultados"),
        (0x0802251E, "41 46 08 68 40 21 08 40 00 28 16 d0 d0 18 01 28 17 dc", "opcode 0x24: teste do bit 0x40 e limiar dos contadores"),
        (0x08022560, "3a 68 51 78 90 78 00 02 09 18 d0 78 00 04 09 18 10 79 00 06 09 18 39 60", "opcode 0x24: leitura u32 inline e armazenamento como cursor"),
        (0x0802257A, "38 68 05 30 38 60 03 e0", "opcode 0x24: cursor +5"),
        (0x08022598, "09 49 00 20 08 70 09 48 00 22 01 21 81 73 08 48 01 70 08 48 c2 70 82 71", "helper de 0x25: writes de bytes locais"),
        (0x080225B0, "07 4a 10 68 42 39 08 40 06 49 08 40 10 60", "helper de 0x25: mascara e gravação da word"),
        (0x080225D8, "00 b5 ff f7 dd ff 03 49 08 68 01 30 08 60 01 bc 00 47", "opcode 0x25: chamada local e cursor +1"),
        (0x080225F0, "03 4b 04 4a 10 68 41 78 19 70 02 30 10 60 70 47", "opcode 0x26: byte inline e cursor +2"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08022534: 0x02023BC8,
        0x08022538: 0x02024284,
        0x0802253C: 0x02023E8A,
        0x08022540: 0x0202402C,
        0x08022544: 0x02022B4C,
        0x08022548: 0x02023BCC,
        0x0802254C: 0x02023D74,
        0x08022550: 0x02023DD0,
        0x08022554: 0x02023ECC,
        0x080225C0: 0x02023DCC,
        0x080225C4: 0x02023FC4,
        0x080225C8: 0x02023D71,
        0x080225CC: 0x02023E82,
        0x080225D0: 0x02023DD0,
        0x080225D4: 0xFFFFBFFF,
        0x080225EC: 0x02023D74,
        0x08022600: 0x02023D72,
        0x08022604: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, ramos, inline operands, chamadas, endereços e máscaras locais.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
