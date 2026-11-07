#!/usr/bin/env python3
"""Relógio acelerado, iluminação externa e evoluções por horário sobre v18 exata."""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import motor_v18 as v18
from scripts.treino_ev import write_new_file

BASE_SHA256 = v18.OUTPUT_SHA256
OUTPUT_SHA256 = 'b7b8b5636e522e1e3502aa59d1f714d36d955a028d9b988b1fe3f97219fffad1'
PAYLOAD_PATH = ROOT / 'patches/motor_v19/payload.bin'
PAYLOAD_SHA256 = '6ed02470ba01143bea8f2cf759b0ea8e05a43960db02dc119d8cf5078d38d10f'
PAYLOAD_SIZE = 776
PAYLOAD_OFFSET = 0x10DD000
RESERVED_LIMIT = 0x10DE000
ENTRY_MINUTES = 0x090DD001
ENTRY_PHASE = 0x090DD009
ENTRY_TINT = 0x090DD011
ENTRY_FIELD = 0x090DD019
ENTRY_EVOLUTION = 0x090DD021
HOOKS = (
    (0xF1E20, bytes.fromhex('00b54ef053fe4ef0'), ENTRY_FIELD),
    (0x10DB44, bytes.fromhex('f0b5de4657464e46'), ENTRY_EVOLUTION),
)
PATCH_RANGES = tuple((at, len(before)) for at, before, _ in HOOKS) + ((PAYLOAD_OFFSET, PAYLOAD_SIZE),)

class PatchError(ValueError):
    pass

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source) != 0x2000000 or digest(source) != BASE_SHA256:
        raise PatchError('Entrada não é motor_v18 exato')
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload) != PAYLOAD_SIZE or digest(payload) != PAYLOAD_SHA256:
        raise PatchError('Payload inválido')
    if source[PAYLOAD_OFFSET:RESERVED_LIMIT] != b'\xff' * (RESERVED_LIMIT - PAYLOAD_OFFSET):
        raise PatchError('Área de payload ocupada')
    out = bytearray(source)
    for at, before, entry in HOOKS:
        if source[at:at + len(before)] != before:
            raise PatchError('Hook anterior divergente')
        out[at:at + 8] = struct.pack('<HHI', 0x4B00, 0x4718, entry)
    out[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(payload)] = payload
    result = bytes(out)
    if digest(result) != OUTPUT_SHA256:
        raise PatchError('Hash de saída divergente')
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.rom.read_bytes())
    write_new_file(args.rom, args.saida, result)
    print(f'{args.saida}: {len(result)} B SHA-256 {digest(result)}')

if __name__ == '__main__':
    main()
