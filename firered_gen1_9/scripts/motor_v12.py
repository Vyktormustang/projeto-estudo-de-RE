#!/usr/bin/env python3
"""Eerie Spell + Soundproof: extensão isolada da lista nativa sobre motor_v11.

Entrada SHA exata e saída nova. Não moderniza Substitute, Shield Dust nem
os demais golpes sonoros. Não modifica código Thumb, RAM ou aprendizados.
"""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import motor_v11 as v11
from scripts.treino_ev import write_new_file

BASE_SHA256 = v11.OUTPUT_SHA256
OUTPUT_SHA256 = "fb28ad767a11add187d0fa69dec0164b3de73a9887a0c5834c5feccc675725c1"
ROM = 0x08000000
OLD_TABLE = 0x20F4E8
TABLE_OFFSET = 0x10D7000
POINTER_SITE = 0x6F840
# O compilador trata Growl (45) separadamente e usa um literal para tabela+2.
# Não remover/reordenar a primeira entrada; conservar todos os sons Gen 3.
OLD_MOVES = (45, 46, 47, 48, 103, 173, 253, 319, 320, 304)
NEW_MOVES = OLD_MOVES + (720,)
OLD_TABLE_BYTES = struct.pack('<11H', *OLD_MOVES, 0xFFFF)
TABLE_BYTES = struct.pack('<12H', *NEW_MOVES, 0xFFFF)

class PatchError(ValueError):
    pass

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build(source: bytes) -> bytes:
    if len(source) != 0x2000000 or digest(source) != BASE_SHA256:
        raise PatchError('Entrada não é motor_v11 de SHA-256 esperado')
    if source[OLD_TABLE:OLD_TABLE + len(OLD_TABLE_BYTES)] != OLD_TABLE_BYTES:
        raise PatchError('Tabela nativa inesperada')
    if struct.unpack_from('<I', source, POINTER_SITE)[0] != ROM + OLD_TABLE + 2:
        raise PatchError('Literal Soundproof inesperado')
    if source[TABLE_OFFSET:TABLE_OFFSET + len(TABLE_BYTES)] != b'\xff' * len(TABLE_BYTES):
        raise PatchError('Área da nova tabela ocupada')
    out = bytearray(source)
    out[TABLE_OFFSET:TABLE_OFFSET + len(TABLE_BYTES)] = TABLE_BYTES
    struct.pack_into('<I', out, POINTER_SITE, ROM + TABLE_OFFSET + 2)
    result = bytes(out)
    if digest(result) != OUTPUT_SHA256:
        raise PatchError('Hash de saída divergente')
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.rom.read_bytes())
    write_new_file(args.rom, args.saida, result)
    print(f'{args.saida}: {len(result)} B SHA-256 {digest(result)}')

if __name__ == '__main__':
    main()
