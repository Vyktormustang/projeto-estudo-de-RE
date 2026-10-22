#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeciona a região local de SpeciesInfo candidata na ROM GBA.

A contagem de 412 registros é uma hipótese evidencial do ciclo 19, não uma
constante universal. O script confere hash, stride/padding e resume a quebra
estrutural após os registros; não altera ROM nem prova todos os usos da tabela.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
TABLE_VA = 0x08254784
STRIDE = 0x1C
CANDIDATE_RECORDS = 412


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")
    start = TABLE_VA - ROM_BASE
    end = start + CANDIDATE_RECORDS * STRIDE
    if end > len(data):
        raise SystemExit("região candidata fora dos limites da ROM")

    records = [data[start + n * STRIDE : start + (n + 1) * STRIDE]
               for n in range(CANDIDATE_RECORDS)]
    padding_after_zero = sum(row[0x1A:0x1C] == b"\0\0" for row in records[1:])
    print(f"ROM: {args.rom} ({len(data)} bytes; SHA-256 {digest})")
    print(f"base candidata: VA 0x{TABLE_VA:08X}, offset 0x{start:X}")
    print(f"stride: 0x{STRIDE:X}; registros examinados: {CANDIDATE_RECORDS}")
    print(f"registro 0 totalmente zero: {not any(records[0])}")
    print(f"registros 1..{CANDIDATE_RECORDS - 1} com padding +0x1A..+0x1B zero: "
          f"{padding_after_zero}/{CANDIDATE_RECORDS - 1}")
    print(f"fim exclusivo candidato: VA 0x{ROM_BASE + end:08X}, offset 0x{end:X}")
    print(f"próximos 32 bytes: {data[end:end + 32].hex(' ')}")
    words = struct.unpack_from("<16H", data, end)
    print("próximos 16 u16 little-endian: " + " ".join(f"{word:04X}" for word in words))
    print("Nota: o padrão após o limite é compatível com outra estrutura; "
          "a classificação requer xrefs/consumidores locais.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
