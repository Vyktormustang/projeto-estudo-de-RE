#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revalida os domínios numéricos locais de species, moves, learnsets e tipos.

Somente leitura; os valores impressos são IDs/bytes locais, sem rótulos de tipo
ou nomes upstream. Os limites de tabela são hipóteses já documentadas nos ciclos
18–21 e 25, não autorização para ampliar estruturas.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
SPECIES_VA, SPECIES_COUNT, SPECIES_STRIDE = 0x08254784, 412, 0x1C
MOVE_VA, MOVE_COUNT, MOVE_STRIDE = 0x08250C04, 355, 12
LEARNSET_POINTERS_VA, LEARNSET_POINTER_COUNT = 0x0825D7B4, 412
TYPE_CHART_VA, TYPE_CHART_ROWS, TYPE_CHART_STRIDE = 0x0824F050, 112, 3


def slice_va(data: bytes, va: int, size: int) -> bytes:
    offset = va - ROM_BASE
    if offset < 0 or offset + size > len(data):
        raise SystemExit(f"região fora da ROM: 0x{va:08X} (+0x{size:X})")
    return data[offset:offset + size]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    species = slice_va(data, SPECIES_VA, SPECIES_COUNT * SPECIES_STRIDE)
    species_types = {
        species[i * SPECIES_STRIDE + field]
        for i in range(1, SPECIES_COUNT)
        for field in (6, 7)
    }

    moves = slice_va(data, MOVE_VA, MOVE_COUNT * MOVE_STRIDE)
    move_types = {moves[i * MOVE_STRIDE + 2] for i in range(MOVE_COUNT)}
    effect_ids = {moves[i * MOVE_STRIDE] for i in range(MOVE_COUNT)}

    chart = slice_va(data, TYPE_CHART_VA, TYPE_CHART_ROWS * TYPE_CHART_STRIDE)
    chart_types = {
        chart[i * TYPE_CHART_STRIDE + field]
        for i in range(TYPE_CHART_ROWS)
        if chart[i * TYPE_CHART_STRIDE] not in (0xFE, 0xFF)
        for field in (0, 1)
    }
    if chart[108 * 3:109 * 3] != bytes.fromhex("fe fe 00"):
        raise SystemExit("marcador 0xFE do typechart diverge do observado")
    if chart[111 * 3:112 * 3] != bytes.fromhex("ff ff 00"):
        raise SystemExit("terminador 0xFF do typechart diverge do observado")

    pointers_raw = slice_va(data, LEARNSET_POINTERS_VA, LEARNSET_POINTER_COUNT * 4)
    pointers = list(struct.unpack(f"<{LEARNSET_POINTER_COUNT}I", pointers_raw))
    unique_pointers = list(dict.fromkeys(pointers))
    if pointers[0] != pointers[1] or any(a > b for a, b in zip(pointers, pointers[1:])):
        raise SystemExit("ordem/duplicação da tabela de learnsets diverge do observado")

    learnset_words: list[int] = []
    for index, pointer in enumerate(unique_pointers):
        offset = pointer - ROM_BASE
        if offset < 0 or offset + 2 > len(data):
            raise SystemExit(f"destino learnset fora da ROM: 0x{pointer:08X}")
        next_offset = (unique_pointers[index + 1] - ROM_BASE
                       if index + 1 < len(unique_pointers) else min(len(data), offset + 0x100))
        terminated = False
        for pos in range(offset, next_offset - 1, 2):
            word = struct.unpack_from("<H", data, pos)[0]
            if word == 0xFFFF:
                terminated = True
                break
            learnset_words.append(word)
        if not terminated:
            raise SystemExit(f"learnset sem terminador no limite local: 0x{pointer:08X}")

    packed_move_ids = [word & 0x01FF for word in learnset_words]
    packed_levels = [word >> 9 for word in learnset_words]
    max_effect = max(effect_ids)

    print(f"ROM: {len(data)} bytes; SHA-256 {digest}")
    print(f"species candidate: {SPECIES_COUNT} × 0x{SPECIES_STRIDE:X}; type-byte values={sorted(species_types)}")
    print(f"move candidate: {MOVE_COUNT} × {MOVE_STRIDE}; +2 values={sorted(move_types)}; +0 max={max_effect}")
    print(f"learnsets: {len(pointers)} pointers / {len(unique_pointers)} distinct lists; entries={len(learnset_words)}")
    print(f"  packed lower 9 bits: move ID max={max(packed_move_ids)} (format ceiling 0x01FF=511); level max={max(packed_levels)}")
    print(f"typechart: {TYPE_CHART_ROWS} × {TYPE_CHART_STRIDE}; active +0/+1 values={sorted(chart_types)}")
    print("Aviso: são domínios numéricos observados na ROM-base; IDs e semânticas não são nomes, e estes achados não validam consumidores não examinados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
