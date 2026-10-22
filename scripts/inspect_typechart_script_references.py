#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revalida locais de bytecode de batalha associados a 0x4A e 0xA6.

A checagem é somente leitura. Bytes e ponteiros vêm da ROM BR local. A
classificação dos limites dos comandos dentro do bytecode usa, separadamente,
o cross-reference de macros upstream fixado nos relatórios; este script não
prova que qualquer batalha/handler foi executado.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
MOVE_TABLE_VA = 0x08250C04
MOVE_COUNT_CANDIDATE = 355
MOVE_STRIDE = 12
EFFECT_SCRIPT_TABLE_VA = 0x081D65A8
COMMAND_TABLE_VA = 0x0825011C


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
    actual = data[pos : pos + len(wanted)]
    if actual != wanted:
        raise SystemExit(f"{label}: {actual.hex(' ')}, esperado {wanted.hex(' ')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    data = parser.parse_args().rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    # Local move-record +0 values 0x59 and 0x5D select these effect-table rows.
    move_effects = {}
    for move_index, expected_effect in ((68, 0x59), (176, 0x5D)):
        if not 0 <= move_index < MOVE_COUNT_CANDIDATE:
            raise SystemExit(f"move-record index fora do intervalo candidato: {move_index}")
        va = MOVE_TABLE_VA + move_index * MOVE_STRIDE
        actual = data[offset(va, MOVE_STRIDE, data)]
        if actual != expected_effect:
            raise SystemExit(
                f"move-record index {move_index}: +0=0x{actual:02X}, "
                f"esperado 0x{expected_effect:02X}"
            )
        move_effects[move_index] = actual

    script_59 = read_u32(data, EFFECT_SCRIPT_TABLE_VA + 0x59 * 4)
    script_5d = read_u32(data, EFFECT_SCRIPT_TABLE_VA + 0x5D * 4)
    if (script_59, script_5d) != (0x081D7433, 0x081D74D6):
        raise SystemExit(
            f"destinos de scripts divergentes: 0x59→0x{script_59:08X}, "
            f"0x5D→0x{script_5d:08X}"
        )

    # Bytes localmente armazenados; command boundaries additionally use the
    # upstream macro lengths documented separately from local evidence.
    expect(
        data,
        script_59,
        "00 a1 f0 7d 1d 08 01 5e 69 1d 08 00 00 02 03 4a",
        "script na entrada 0x59",
    )
    expect(
        data,
        script_5d,
        "00 02 03 a6 f2 7d 1d 08 09 0a",
        "script na entrada 0x5D",
    )
    if read_u32(data, script_59 + 2) != 0x081D7DF0:
        raise SystemExit("operando u32 após 0xA1 não é o ponteiro local observado")
    if read_u32(data, script_59 + 7) != 0x081D695E:
        raise SystemExit("operando u32 após 0x01 não é o ponteiro local observado")
    if read_u32(data, script_5d + 4) != 0x081D7DF2:
        raise SystemExit("operando u32 após 0xA6 não é o ponteiro local observado")

    handlers = {0x4A: 0x08023C39, 0xA6: 0x08029DAD}
    for opcode, expected in handlers.items():
        actual = read_u32(data, COMMAND_TABLE_VA + opcode * 4)
        if actual != expected:
            raise SystemExit(
                f"handler local opcode 0x{opcode:02X}: 0x{actual:08X}, "
                f"esperado 0x{expected:08X}"
            )

    print(f"ROM SHA-256: {digest}")
    print("move-record index 68: +0=0x59 -> script 0x081D7433; byte 0x4A no offset +15")
    print("move-record index 176: +0=0x5D -> script 0x081D74D6; byte 0xA6 no offset +3")
    print("dispatch local: opcode 0x4A -> 0x08023C38; opcode 0xA6 -> 0x08029DAC")
    print("Bytes/ponteiros locais conferidos; limites de comandos usam cross-reference e não provam execução.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
