#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida bytes locais dos handlers de som de efetividade e mensagem de resultado."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
COMMAND_TABLE_VA = 0x0825011C
HANDLERS = {0x0E: 0x0801FAD1, 0x0F: 0x0801FBA1}


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

    expect(rom, 0x081D6931, "05 06 07 09 0a 0e", "sequência de bytecode local")
    for opcode, handler in HANDLERS.items():
        actual = read32(rom, COMMAND_TABLE_VA + opcode * 4)
        if actual != handler:
            raise SystemExit(f"opcode 0x{opcode:02X}: 0x{actual:08X}, esperado 0x{handler:08X}")

    signatures = [
        (0x0801FAD0, "10 b5 0d 48 00 68 00 28 5a d1", "entrada/espera do opcode 0x0E"),
        (0x0801FADA, "0c 4c 0c 48 00 78 20 70", "cópia local do battler selecionado"),
        (0x0801FAE2, "0c 49 0a 78 01 20 10 40 00 28", "teste local do byte de resultado"),
        (0x0801FB2C, "00 20 0e 21 01 e0 00 20 0c 21", "IDs imediatos passados ao helper de som"),
        (0x0801FB88, "04 49 08 68 01 30 08 60", "avanço de um byte do opcode 0x0E"),
        (0x0801FBA0, "f0 b5 00 23 0d 48 00 68 00 28", "entrada/espera do opcode 0x0F"),
        (0x0801FBC8, "b8 79 02 28 0e d9", "consulta local ao miss type"),
        (0x0801FC28, "de 23 80 e0 dd 23 7e e0 da 23", "imediatos locais de mensagens"),
        (0x0801FC84, "1b 23 52 e0", "ramo local de mensagem 0x1B"),
        (0x0801FCB0, "40 20 28 40 00 28 0b d0", "ramo de flags e redirecionamento"),
        (0x0801FD24, "e5 23 02 e0", "imediato local de mensagem 0xE5"),
        (0x0801FD38, "04 49 08 68 01 30 08 60", "avanço comum de um byte do opcode 0x0F"),
    ]
    for va, byte_string, label in signatures:
        expect(rom, va, byte_string, label)

    literals = {
        0x0801FB08: 0x02023BC8,
        0x0801FB0C: 0x02023BC4,
        0x0801FB10: 0x02023D6C,
        0x0801FB14: 0x02023DCC,
        0x0801FB98: 0x02023BC4,
        0x0801FB9C: 0x02023D74,
        0x0801FBDC: 0x02023BC8,
        0x0801FBE0: 0x02023DCC,
        0x0801FBE4: 0x02023E82,
        0x0801FBE8: 0x083FE514,
        0x0801FC60: 0x02023D68,
        0x0801FC64: 0x02023BE4,
        0x0801FC68: 0x02023D6C,
        0x0801FC6C: 0x02023D6F,
        0x0801FC70: 0x02023D74,
        0x0801FC74: 0x081D9641,
        0x0801FCAC: 0x081D8FE4,
        0x0801FCCC: 0x081D8FDD,
        0x0801FD14: 0x081D9641,
        0x0801FD48: 0x02023D6B,
        0x0801FD4C: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read32(rom, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    for opcode, handler in HANDLERS.items():
        print(f"opcode 0x{opcode:02X} → 0x{handler:08X}")
    print("Verificados testes locais de flags, chamadas/IDs, cursores, tabela candidata e destinos de script.")
    print("Validação estática; nomes de sons/mensagens e execução permanecem separados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
