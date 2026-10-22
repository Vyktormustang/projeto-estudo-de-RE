#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida dispatch local e trechos Thumb dos opcodes 0x09–0x0C.

Leitura estática da ROM; rótulos semânticos são referências upstream separadas.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
SCRIPT_VA = 0x081D6931
EXPECTED_HANDLERS = {
    0x09: 0x0801F441,
    0x0A: 0x0801F589,
    0x0B: 0x0801F5A9,
    0x0C: 0x0801F685,
}


def off(va: int, size: int, rom: bytes) -> int:
    pos = va - ROM_BASE
    if pos < 0 or pos + size > len(rom):
        raise SystemExit(f"VA fora da ROM: 0x{va:08X} (+0x{size:X})")
    return pos


def read32(rom: bytes, va: int) -> int:
    return struct.unpack_from("<I", rom, off(va, 4, rom))[0]


def expect(rom: bytes, va: int, hex_bytes: str, label: str) -> None:
    wanted = bytes.fromhex(hex_bytes)
    pos = off(va, len(wanted), rom)
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

    expect(rom, SCRIPT_VA, "05 06 07 09 0a", "sequência local amostrada")
    for opcode, handler in EXPECTED_HANDLERS.items():
        actual = read32(rom, COMMAND_TABLE_VA + opcode * 4)
        if actual != handler:
            raise SystemExit(f"opcode 0x{opcode:02X}: handler 0x{actual:08X}, esperado 0x{handler:08X}")

    signatures = [
        (0x0801F440, "70 b5 46 46 40 b4 83 b0", "entrada do handler 0x09"),
        (0x0801F448, "0f 48 00 68 00 28 00 d0", "espera local de controller exec"),
        (0x0801F530, "0b 49 08 68 01 30 08 60", "avanço de um byte no handler 0x09"),
        (0x0801F588, "00 b5 05 48 00 68 00 28 03 d1", "entrada e espera do handler 0x0A"),
        (0x0801F592, "04 49 08 68 01 30 08 60", "avanço de um byte no handler 0x0A"),
        (0x0801F5A8, "10 b5 18 48 00 68 00 28", "entrada do handler 0x0B"),
        (0x0801F62C, "11 49 88 42 01 dc", "comparação do dano com o limite local"),
        (0x0801F662, "07 49 08 68 02 30 08 60", "avanço de dois bytes no handler 0x0B"),
        (0x0801F684, "f0 b5 81 b0 08 48 00 68 00 28", "entrada do handler 0x0C"),
        (0x0801F6C4, "24 48 01 78 29 20 08 40", "teste local do byte de resultado no handler 0x0C"),
        (0x0801F7C0, "07 4c 20 68 02 30 20 60", "ramo de cursor/retorno após sub-HP zerado"),
        (0x0801FA5A, "04 49 08 68 02 30 08 60", "avanço de dois bytes no handler 0x0C"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x0801F488: 0x02023BC8,
        0x0801F490: 0x02023D4A,
        0x0801F494: 0x02023D74,
        0x0801F498: 0x081D89F1,
        0x0801F53C: 0x08250C04,
        0x0801F544: 0x02023DCC,
        0x0801F5A0: 0x02023BC8,
        0x0801F5A4: 0x02023D74,
        0x0801F60C: 0x02023BC8,
        0x0801F610: 0x02023DCC,
        0x0801F614: 0x02023D74,
        0x0801F61C: 0x02023BE4,
        0x0801F620: 0x02023E0C,
        0x0801F624: 0x02023DD0,
        0x0801F670: 0x02023D50,
        0x0801F674: 10000,
        0x0801F6AC: 0x02023BC8,
        0x0801F6B0: 0x02023FE8,
        0x0801F750: 0x08250C04,
        0x0801F754: 0x02023D4A,
        0x0801F758: 0x02023DCC,
        0x0801F75C: 0x02023D74,
        0x0801F764: 0x02023BE4,
        0x0801F768: 0x02023E0C,
        0x0801F76C: 0x02023DD0,
        0x0801F770: 0x02023D50,
        0x0801F774: 0x02023ECC,
        0x0801F7E4: 0x081D9526,
        0x0801F828: 0x02023DD0,
        0x0801F830: 0x02023D50,
        0x0801F834: 0x02023BE4,
        0x0801FA2C: 0xFFEFFFFF,
        0x0801FA6C: 0x02023D74,
        0x0801FA70: 0x02023BC4,
        0x0801FA74: 0x02023ECC,
        0x0801FA78: 0x0000FFFF,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in EXPECTED_HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados bytes locais de espera, resultados, cursores, limites HP e script de substitute fade.")
    print("Validação estática; sem execução dinâmica e sem nomes upstream embutidos como prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
