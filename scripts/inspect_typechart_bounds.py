#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revalida o dispatch local e a leitura de índice aleatório do typechart.

Somente leitura. A checagem de opcodes não prova que um script particular seja
executado nem substitui uma validação dinâmica do fluxo.
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
TYPE_CHART_VA = 0x0824F050


def offset(va: int, size: int, data: bytes) -> int:
    pos = va - ROM_BASE
    if pos < 0 or pos + size > len(data):
        raise SystemExit(f"endereço fora da ROM: 0x{va:08X} (+0x{size:X})")
    return pos


def read_u32(data: bytes, va: int) -> int:
    return struct.unpack_from("<I", data, offset(va, 4, data))[0]


def expect(data: bytes, va: int, hex_bytes: str, label: str) -> None:
    wanted = bytes.fromhex(hex_bytes)
    pos = offset(va, len(wanted), data)
    actual = data[pos:pos + len(wanted)]
    if actual != wanted:
        raise SystemExit(f"{label}: {actual.hex(' ')}, esperado {wanted.hex(' ')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    command_4a = read_u32(data, COMMAND_TABLE_VA + 0x4A * 4)
    command_a6 = read_u32(data, COMMAND_TABLE_VA + 0xA6 * 4)
    if command_4a != 0x08023C39 or command_a6 != 0x08029DAD:
        raise SystemExit(
            f"handlers de comando divergentes: 0x4A={command_4a:08X}, "
            f"0xA6={command_a6:08X}"
        )

    # Thumb LCG helper: load state pointer, multiply/add, store, return high 16.
    expect(data, 0x08044EC8, "04 4a 11 68 04 48 48 43 04 49 40 18 10 60 00 0c 70 47", "helper LCG")
    state_address = read_u32(data, 0x08044EDC)
    multiplier = read_u32(data, 0x08044EE0)
    increment = read_u32(data, 0x08044EE4)
    if (state_address, multiplier, increment) != (0x03005000, 0x41C64E6D, 0x6073):
        raise SystemExit("literais LCG divergentes dos observados")
    if increment & 1 != 1 or multiplier % 4 != 1:
        raise SystemExit("constantes não satisfazem condição de período completo para módulo 2^32")

    # The routine masks with 0x7F, accepts <=0x70, then computes 3 * index.
    expect(
        data,
        0x08029E9C,
        "1b f0 14 f8 4c 46 04 40 70 2c f9 d8 60 00 04 19 38 4e a3 19",
        "loop de seleção aleatória",
    )
    if read_u32(data, 0x08029FA8) != 0x14F:
        raise SystemExit("limite do segundo scan não é o literal local 0x14F")
    if data[offset(TYPE_CHART_VA + 112 * 3, 3, data):offset(TYPE_CHART_VA + 112 * 3, 3, data) + 3] != bytes.fromhex("c8 c9 cc"):
        raise SystemExit("bytes imediatamente após os 112 registros divergentes")

    print(f"ROM SHA-256: {digest}")
    print(f"dispatch: opcode 0x4A -> 0x{command_4a:08X}; opcode 0xA6 -> 0x{command_a6:08X}")
    print(
        f"LCG: state 0x{state_address:08X}, a=0x{multiplier:08X}, c=0x{increment:04X}; "
        "condições de período completo mod 2^32 satisfeitas"
    )
    print(
        f"typechart: 112 registros; índice 112 lê 0x{TYPE_CHART_VA + 112 * 3:08X} "
        f"({data[offset(TYPE_CHART_VA + 112 * 3, 3, data):offset(TYPE_CHART_VA + 112 * 3, 3, data) + 3].hex(' ')})"
    )
    print("Verificação estática; script emitido/execução do handler não foram demonstrados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
