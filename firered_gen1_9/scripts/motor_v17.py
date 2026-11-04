#!/usr/bin/env python3
"""Ordem de criação de hazards sobre v16 exato, sempre saída nova."""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts import motor_v16 as v16
from scripts.treino_ev import write_new_file

BASE_SHA256 = v16.OUTPUT_SHA256
OUTPUT_SHA256 = '5db05cbb54add61a6c50e08d3e392ba610e87ca3ef462095de168de5d3e32957'
PAYLOAD_PATH = ROOT/'patches/motor_v17/payload.bin'
PAYLOAD_SHA256 = 'f25e560c02cd3681a508812050e9fd0bed9d4b652d788dffa221d2a10983703f'
PAYLOAD_OFFSET = 0x10DB000
PAYLOAD_LIMIT = 0x10DC000
COMMANDS = (
    (0x10C3004,0x090C30E1,0x090DB001),
    (0x10C305C,0x090C4241,0x090DB009),
    (0x10C306C,0x090C45B5,0x090DB011),
    (0x10C3094,0x090C4991,0x090DB019),
    (0x10C30A4,0x090C4C85,0x090DB021),
    (0x10C30BC,0x090C4E25,0x090DB029),
    (0x10C30CC,0x090C4F81,0x090DB031),
    (0x10CFEC0,0x08062D31,0x090DB039),
)

class PatchError(ValueError):
    pass

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:
        raise PatchError('Entrada não é motor_v16 exato')
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=3148 or digest(payload)!=PAYLOAD_SHA256:
        raise PatchError('Payload inválido')
    if source[PAYLOAD_OFFSET:PAYLOAD_LIMIT] != b'\xff'*(PAYLOAD_LIMIT-PAYLOAD_OFFSET):
        raise PatchError('Área de payload ocupada')
    out = bytearray(source)
    for offset,previous,entry in COMMANDS:
        if struct.unpack_from('<I',source,offset)[0]!=previous:
            raise PatchError('Comando anterior divergente')
        struct.pack_into('<I',out,offset,entry)
    out[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)] = payload
    result = bytes(out)
    if digest(result)!=OUTPUT_SHA256:
        raise PatchError('Hash de saída divergente')
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--saida',type=Path,required=True)
    args = parser.parse_args()
    result = build(args.rom.read_bytes())
    write_new_file(args.rom,args.saida,result)
    print(f'{args.saida}: {len(result)} B SHA-256 {digest(result)}')

if __name__=='__main__':
    main()
