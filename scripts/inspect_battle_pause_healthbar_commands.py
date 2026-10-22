#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere dispatch e padrões Thumb locais dos opcodes de batalha 0x39–0x3B."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x39: 0x08022C09, 0x3A: 0x08022C49, 0x3B: 0x08022C69}


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
        (0x08022C08, "30 b5 0c 48 04 68 00 2c 10 d1", "opcode 0x39: espera pela word de controle"),
        (0x08022C12, "0b 4d 2a 68 51 78 90 78 00 02 01 43 09 4b 18 88 01 30 18 80", "opcode 0x39: lê limite e incrementa contador halfword"),
        (0x08022C26, "00 04 00 0c 88 42 02 d3 1c 80 d0 1c 28 60", "opcode 0x39: aguarda limite, limpa contador e avança cursor"),
        (0x08022C34, "30 bc 01 bc 00 47", "opcode 0x39: retorno"),
        (0x08022C48, "00 b5 05 48 00 68 00 28 03 d1 04 49 08 68 01 30 08 60 01 bc 00 47", "opcode 0x3A: aguarda zero e avança cursor +1"),
        (0x08022C68, "00 b5 04 48 00 68 40 78 00 28 09 d1", "opcode 0x3B: lê seletor inline"),
        (0x08022C74, "02 48 03 49 08 e0", "opcode 0x3B: caminho seletor zero"),
        (0x08022C88, "09 48 0a 49 09 78 01 70", "opcode 0x3B: caminho não-zero e grava byte selecionado"),
        (0x08022C90, "09 48 01 88 00 20 eb f7 a9 fc", "opcode 0x3B: obtém halfword e chama 0x0800E5EC"),
        (0x08022C9A, "05 48 00 78 f4 f7 d3 fa", "opcode 0x3B: chama 0x08017248 com byte selecionado"),
        (0x08022CA2, "06 49 08 68 02 30 08 60 01 bc 00 47", "opcode 0x3B: cursor +2"),
        (0x0800E5EC, "10 b5 00 06 00 0e 09 04 09 0c 0a 4b 00 24 18 22 1a 70 5c 70 99 70", "helper local: cria packet de quatro bytes"),
        (0x0800E600, "99 70 09 04 09 14 ff 22 12 02 11 40 09 12 d9 70 19 1c 04 22 ff f7 4c f9", "helper local: grava metade alta e chama 0x0800D8B0"),
        (0x0800D8B0, "70 b5 0c 1c 00 06 03 0e 1d 1c 12 04 12 0c 06 48 00 68 02 21 08 40 00 28 08 d0", "0x0800D8B0: roteia conforme bit local 0x02"),
        (0x0800D8CA, "18 1c 11 1c 22 1c 00 f0 8c f8", "0x0800D8B0: ramo que chama 0x0800D9EC"),
        (0x0800D8E6, "00 23 93 42 20 da 06 4e 07 4d 28 78 40 02 18 18 80 19 21 78 01 70", "0x0800D8B0: cópia ao buffer por battler"),
        (0x08017248, "00 b5 00 06 03 0e 08 48 00 68 02 21 08 40 00 28 10 d0", "0x08017248: consulta bit local 0x02"),
        (0x0801725A, "06 4a 06 49 98 00 40 18 01 68 09 07 10 68 08 43 10 60", "0x08017248: OR máscara alta em 0x02023BC8"),
        (0x0801727C, "04 4a 05 49 98 00 40 18 11 68 00 68 01 43 11 60", "0x08017248: OR máscara simples em 0x02023BC8"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x08022C3C: 0x02023BC8,
        0x08022C40: 0x02023D74,
        0x08022C44: 0x02023E7C,
        0x08022C60: 0x02023BC8,
        0x08022C64: 0x02023D74,
        0x08022C7C: 0x02023D74,
        0x08022C80: 0x02023BC4,
        0x08022C84: 0x02023D6C,
        0x08022CB0: 0x02023BC4,
        0x08022CB4: 0x02023D6B,
        0x08022CB8: 0x02023D50,
        0x08022CBC: 0x02023D74,
        0x0800E620: 0x02022874,
        0x0800D8D8: 0x02022B4C,
        0x0800D908: 0x02022BC4,
        0x0800D90C: 0x02023BC4,
        0x08017270: 0x02022B4C,
        0x08017274: 0x02023BC8,
        0x08017278: 0x0825E45C,
        0x08017290: 0x02023BC8,
        0x08017294: 0x0825E45C,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    for index, wanted in enumerate((1, 2, 4, 8)):
        actual = read32(rom, 0x0825E45C + 4 * index)
        if actual != wanted:
            raise SystemExit(f"tabela de máscara [{index}]=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados dispatch, cursor, chamadas diretas, helpers locais e máscaras de battler.")
    print("Validação estática; nomes e interpretação upstream não são prova local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
