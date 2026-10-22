#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere a tabela de ponteiros e os registros u16 de learnset candidatos.

Tudo é somente leitura e limitado à ROM/hashes/endereço desta investigação.
O nome "learnset" é uma interpretação cruzada; a rotina local e a estrutura
local são verificadas, mas o script não edita a ROM nem prova equivalência com
qualquer árvore de código-fonte.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
PTR_TABLE_VA = 0x0825D7B4
PTR_COUNT = 412
DATA_START_VA = 0x08257494
FINAL_SCAN_LIMIT = 0x100


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    table_off = PTR_TABLE_VA - ROM_BASE
    ptrs = list(struct.unpack_from(f"<{PTR_COUNT}I", data, table_off))
    valid = [DATA_START_VA <= p < ROM_BASE + len(data) for p in ptrs]
    if not all(valid):
        raise SystemExit("há ponteiro fora dos limites da ROM")
    if not all(a <= b for a, b in zip(ptrs, ptrs[1:])):
        raise SystemExit("a sequência de ponteiros não é não-decrescente")
    if ptrs[0] != DATA_START_VA:
        raise SystemExit("primeiro ponteiro não corresponde ao início observado")

    unique = list(dict.fromkeys(ptrs))
    lengths: list[int] = []
    max_level = 0
    max_move = 0
    for i, pointer in enumerate(unique):
        start = pointer - ROM_BASE
        if i + 1 < len(unique):
            limit = unique[i + 1] - ROM_BASE
        else:
            limit = min(len(data), start + FINAL_SCAN_LIMIT)
        if start & 1:
            raise SystemExit(f"ponteiro não alinhado: 0x{pointer:08X}")
        words = []
        for offset in range(start, limit, 2):
            word = struct.unpack_from("<H", data, offset)[0]
            if word == 0xFFFF:
                break
            words.append(word)
        else:
            raise SystemExit(f"sem terminador antes do limite para 0x{pointer:08X}")
        lengths.append(len(words))
        for word in words:
            max_level = max(max_level, (word & 0xFE00) >> 9)
            max_move = max(max_move, word & 0x01FF)

    next_word = struct.unpack_from("<I", data, table_off + PTR_COUNT * 4)[0]
    print(f"ROM SHA-256: {digest}")
    print(f"tabela: VA 0x{PTR_TABLE_VA:08X}, offset 0x{table_off:X}")
    print(f"ponteiros: {len(ptrs)}; fim exclusivo 0x{PTR_TABLE_VA + PTR_COUNT * 4:08X}")
    print(f"destinos: 0x{min(ptrs):08X}..0x{max(ptrs):08X}; monotônicos: sim")
    print(f"destinos únicos: {len(unique)}; índices 0 e 1 iguais: {ptrs[0] == ptrs[1]}")
    print(f"word u32 imediatamente após a tabela: 0x{next_word:08X}")
    print(f"listas únicas terminadas em 0xFFFF: {len(lengths)}/{len(unique)}")
    print(f"palavras antes do terminador: min={min(lengths)}, max={max(lengths)}")
    print(f"máximo decodificado por máscara local: nível={max_level}, id={max_move}")
    for index in (0, 1, 2, 411):
        pointer = ptrs[index]
        print(f"índice {index}: ponteiro 0x{pointer:08X}")
    print("Nota: índices são posições da tabela local; nomes de espécies e semântica "
          "dependem de cruzamento separado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
