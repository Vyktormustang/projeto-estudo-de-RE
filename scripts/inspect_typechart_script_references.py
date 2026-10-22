#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revalida referências locais a 0x4A e 0xA6 em scripts de efeito.

A checagem é somente leitura. Bytes e ponteiros vêm da ROM BR local. A
classificação dos limites dos comandos usa, em separado, o cross-reference dos
macros upstream fixado nos relatórios; isto não prova que qualquer batalha ou
handler foi executado.
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
LEARNSET_POINTER_TABLE_VA = 0x0825D7B4
LEARNSET_POINTER_COUNT = 412
LEARNSET_DATA_START_VA = 0x08257494
LEARNSET_FINAL_SCAN_LIMIT = 0x100

# Record index -> local byte +0 used as the effect-table index.
MOVE_EFFECTS = {
    68: 0x59,
    176: 0x5D,
    205: 0x75,
    301: 0x75,
    243: 0x90,
    280: 0xBA,
}
# Effect-table index -> local script pointer.
SCRIPTS = {
    0x59: 0x081D7433,
    0x5D: 0x081D74D6,
    0x75: 0x081D78A0,
    0x90: 0x081D7A89,
    0xBA: 0x081D81B9,
}


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


def scan_learnset_references(data: bytes, move_ids: set[int]) -> dict[int, list[tuple[int, int]]]:
    """Read the documented pointer table and collect matching low-9-bit IDs."""
    table_off = offset(LEARNSET_POINTER_TABLE_VA, LEARNSET_POINTER_COUNT * 4, data)
    pointers = list(struct.unpack_from(f"<{LEARNSET_POINTER_COUNT}I", data, table_off))
    rom_end = ROM_BASE + len(data)
    if pointers[0] != LEARNSET_DATA_START_VA or any(
        not LEARNSET_DATA_START_VA <= p < rom_end for p in pointers
    ) or any(a > b for a, b in zip(pointers, pointers[1:])):
        raise SystemExit("tabela local de learnsets não satisfaz os limites/ordem esperados")

    unique = sorted(set(pointers))
    parsed: dict[int, list[int]] = {}
    for i, pointer in enumerate(unique):
        start = offset(pointer, 2, data)
        limit = (
            unique[i + 1] - ROM_BASE
            if i + 1 < len(unique)
            else min(len(data), start + LEARNSET_FINAL_SCAN_LIMIT)
        )
        words = []
        for pos in range(start, limit - 1, 2):
            word = struct.unpack_from("<H", data, pos)[0]
            if word == 0xFFFF:
                break
            words.append(word)
        else:
            raise SystemExit(f"learnset sem 0xFFFF antes do limite: 0x{pointer:08X}")
        parsed[pointer] = words

    hits = {move_id: [] for move_id in sorted(move_ids)}
    for table_index, pointer in enumerate(pointers):
        for word in parsed[pointer]:
            move_id = word & 0x01FF
            if move_id in hits:
                hits[move_id].append((table_index, (word & 0xFE00) >> 9))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    data = parser.parse_args().rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    for move_index, expected_effect in MOVE_EFFECTS.items():
        if not 0 <= move_index < MOVE_COUNT_CANDIDATE:
            raise SystemExit(f"move-record index fora do intervalo candidato: {move_index}")
        va = MOVE_TABLE_VA + move_index * MOVE_STRIDE
        actual = data[offset(va, MOVE_STRIDE, data)]
        if actual != expected_effect:
            raise SystemExit(
                f"move-record index {move_index}: +0=0x{actual:02X}, "
                f"esperado 0x{expected_effect:02X}"
            )

    for effect_index, expected_script in SCRIPTS.items():
        actual = read_u32(data, EFFECT_SCRIPT_TABLE_VA + effect_index * 4)
        if actual != expected_script:
            raise SystemExit(
                f"script table index 0x{effect_index:02X}: 0x{actual:08X}, "
                f"esperado 0x{expected_script:08X}"
            )

    # Local byte sequences. Command boundaries are cross-referenced to the
    # pinned upstream macros; this verifier itself checks bytes and pointers.
    expect(
        data, SCRIPTS[0x59],
        "00 a1 f0 7d 1d 08 01 5e 69 1d 08 00 00 02 03 4a",
        "script na entrada 0x59 (0x4A em +15)",
    )
    expect(
        data, SCRIPTS[0x5D],
        "00 02 03 a6 f2 7d 1d 08 09 0a",
        "script na entrada 0x5D (0xA6 em +3)",
    )
    expect(
        data, SCRIPTS[0x75],
        "00 02 1d 01 00 10 00 00 ad 78 1d 08 03 01 b4 78 1d 08 00 00 4a",
        "script na entrada 0x75 (0x4A em +20)",
    )
    expect(
        data, SCRIPTS[0x90],
        "00 a2 f0 7d 1d 08 01 5e 69 1d 08 00 00 02 03 4a",
        "script na entrada 0x90 (0x4A em +15)",
    )
    expect(
        data, SCRIPTS[0xBA],
        "00 01 5e 69 1d 08 00 00 02 03 ee 04 05 06 07 29 00 dc 3f 02 02 00 d9 81 1d 08 36 cc 3d 02 02 09 09 0a 29 03 dc 3f 02 02 02 ec 81 1d 08 10 62 01 12 40 00 4a",
        "script na entrada 0xBA (0x4A em +51)",
    )

    # Check local inline pointer operands in those streams.
    inline_pointers = {
        SCRIPTS[0x59] + 2: 0x081D7DF0,  # after opcode 0xA1
        SCRIPTS[0x59] + 7: 0x081D695E,  # after opcode 0x01
        SCRIPTS[0x5D] + 4: 0x081D7DF2,  # after opcode 0xA6
        SCRIPTS[0x75] + 8: 0x081D78AD,  # branch operand after opcode 0x1D
        SCRIPTS[0x75] + 14: 0x081D78B4, # branch operand after opcode 0x01
        SCRIPTS[0x90] + 2: 0x081D7DF0,  # after opcode 0xA2
        SCRIPTS[0x90] + 7: 0x081D695E,  # after opcode 0x01
        SCRIPTS[0xBA] + 2: 0x081D695E,  # after opcode 0x01
    }
    for va, expected in inline_pointers.items():
        actual = read_u32(data, va)
        if actual != expected:
            raise SystemExit(f"ponteiro inline em 0x{va:08X}: 0x{actual:08X}, esperado 0x{expected:08X}")

    handlers = {0x4A: 0x08023C39, 0xA6: 0x08029DAD}
    for opcode, expected in handlers.items():
        actual = read_u32(data, COMMAND_TABLE_VA + opcode * 4)
        if actual != expected:
            raise SystemExit(
                f"handler local opcode 0x{opcode:02X}: 0x{actual:08X}, "
                f"esperado 0x{expected:08X}"
            )

    learnset_hits = scan_learnset_references(data, set(MOVE_EFFECTS))

    print(f"ROM SHA-256: {digest}")
    print("0x4A local em entradas 0x59 (+15), 0x75 (+20), 0x90 (+15) e 0xBA (+51)")
    print("0xA6 local em entrada 0x5D (+3); operand aponta para 0x081D7DF2")
    print("registros candidatos +0: 68→0x59, 176→0x5D, 205/301→0x75, 243→0x90, 280→0xBA")
    print("dispatch local: 0x4A→0x08023C38; 0xA6→0x08029DAC")
    for move_id, occurrences in learnset_hits.items():
        indices = sorted({index for index, _level in occurrences})
        print(f"learnset local: ID numérico {move_id} aparece {len(occurrences)} vez(es), tabela indices {indices}")
    print("Bytes/ponteiros locais conferidos; alinhamento não prova execução em batalha.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
