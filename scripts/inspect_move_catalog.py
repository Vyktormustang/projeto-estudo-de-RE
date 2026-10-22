#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida a região candidata de moves e o dispatch local por byte de efeito.

Somente leitura. As conclusões sobre offsets/limites vêm dos bytes e do Thumb
local da ROM; correspondências com nomes de structs/efeitos upstream são
interpretações separadas e não são necessárias para executar esta verificação.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
MOVE_TABLE_VA = 0x08250C04
MOVE_COUNT_CANDIDATE = 355
MOVE_STRIDE = 12
DISPATCH_CODE_VA = 0x0801632C
DISPATCH_POOL_VA = 0x08016360
EFFECT_SCRIPT_TABLE_VA = 0x081D65A8
EFFECT_TABLE_COUNT_CANDIDATE = 214


def file_offset(va: int, length: int, rom_size: int) -> int:
    offset = va - ROM_BASE
    if offset < 0 or offset + length > rom_size:
        raise SystemExit(f"VA fora da ROM: 0x{va:08X} (+0x{length:X})")
    return offset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    move_off = file_offset(MOVE_TABLE_VA, MOVE_COUNT_CANDIDATE * MOVE_STRIDE + MOVE_STRIDE, len(data))
    records = [
        data[move_off + i * MOVE_STRIDE : move_off + (i + 1) * MOVE_STRIDE]
        for i in range(MOVE_COUNT_CANDIDATE)
    ]
    if any(record[9:12] != b"\0\0\0" for record in records):
        raise SystemExit("bytes +9..+11 não são zero em todos os registros candidatos")
    if any(records[0]):
        raise SystemExit("o registro candidato de índice 0 não é todo zero")

    effects = collections.Counter(record[0] for record in records)
    max_effect = max(effects)
    if max_effect >= EFFECT_TABLE_COUNT_CANDIDATE:
        raise SystemExit("há valor de efeito fora do intervalo candidato da tabela")

    pool_off = file_offset(DISPATCH_POOL_VA, 16, len(data))
    output_global, script_table, move_base, current_move = struct.unpack_from("<4I", data, pool_off)
    if (output_global, script_table, move_base, current_move) != (
        0x02023D74,
        EFFECT_SCRIPT_TABLE_VA,
        MOVE_TABLE_VA,
        0x02023D4A,
    ):
        raise SystemExit("pool de literais do dispatcher diverge do observado")

    dispatch_off = file_offset(DISPATCH_CODE_VA, 0x2C, len(data))
    dispatch_bytes = data[dispatch_off : dispatch_off + 0x2C]
    expected_dispatch = bytes.fromhex(
        "0c4c0d4b0d4a0e480188480040188000801800788000c0180068206009490a200870"
    )
    if not dispatch_bytes.startswith(expected_dispatch):
        raise SystemExit("bytes de instrução do dispatcher divergem do observado")

    effect_off = file_offset(EFFECT_SCRIPT_TABLE_VA, EFFECT_TABLE_COUNT_CANDIDATE * 4 + 4, len(data))
    pointers = list(struct.unpack_from(f"<{EFFECT_TABLE_COUNT_CANDIDATE}I", data, effect_off))
    pointer_limit = ROM_BASE + len(data)
    if not all(ROM_BASE <= (pointer & ~1) < pointer_limit for pointer in pointers):
        raise SystemExit("algum dos 214 destinos candidatos está fora da ROM")
    following_word = struct.unpack_from("<I", data, effect_off + EFFECT_TABLE_COUNT_CANDIDATE * 4)[0]
    if ROM_BASE <= (following_word & ~1) < pointer_limit:
        raise SystemExit("a palavra seguinte também parece um ponteiro interno à ROM")

    transition_off = move_off + MOVE_COUNT_CANDIDATE * MOVE_STRIDE
    tail = data[transition_off : transition_off + MOVE_STRIDE]
    print(f"ROM SHA-256: {digest}")
    print(
        f"catálogo candidato: VA 0x{MOVE_TABLE_VA:08X}, stride {MOVE_STRIDE}, "
        f"{len(records)} registros, intervalo [0x{MOVE_TABLE_VA:08X}, "
        f"0x{MOVE_TABLE_VA + len(records) * MOVE_STRIDE:08X})"
    )
    print(f"índice 0 todo zero: sim; +9..+11 zero: {len(records)}/{len(records)}")
    print(
        f"byte +0 observado: {len(effects)} valores distintos, "
        f"min={min(effects)}, max={max_effect}; valor 0 ocorre {effects[0]} vezes"
    )
    print(f"registro seguinte, índice {len(records)}, primeiros 12 bytes: {tail.hex(' ')}")
    print(
        f"pool local do dispatcher 0x{DISPATCH_POOL_VA:08X}: "
        f"destino=0x{output_global:08X}, tabela=0x{script_table:08X}, "
        f"catálogo=0x{move_base:08X}, ID atual=0x{current_move:08X}"
    )
    print(
        f"tabela candidata de scripts: VA 0x{EFFECT_SCRIPT_TABLE_VA:08X}, "
        f"{len(pointers)} ponteiros internos à ROM; {len(set(pointers))} destinos únicos; "
        f"palavra seguinte=0x{following_word:08X}"
    )
    print(f"amostras effectId→destino: {[(i, f'0x{pointers[i]:08X}') for i in (0, 1, 125, 213)]}")
    print("Validação estática; não modifica ROM/save nem demonstra comportamento dinâmico.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
