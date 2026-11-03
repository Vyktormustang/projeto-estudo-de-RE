#!/usr/bin/env python3
"""Disable/Encore: durações modernas sobre v14 exato, sempre saída nova."""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts import motor_v14 as v14
from scripts.treino_ev import write_new_file

BASE_SHA256 = v14.OUTPUT_SHA256
OUTPUT_SHA256 = 'a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147'
PAYLOAD_PATH = ROOT/'patches/motor_v15/payload.bin'
PAYLOAD_SHA256 = 'fc5fe98249fe3e4b7e3d2ac044ee077542ab2ea67a7e0873518cb0eaae6b9d8e'
PAYLOAD_OFFSET = 0x10D9000
PAYLOAD_LIMIT = 0x10DA000
COMMANDS = ((0x10CFE8C,0x080620A9,0x090D9001),(0x10CFE90,0x08062169,0x090D9009))

class PatchError(ValueError):
    pass

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:
        raise PatchError('Entrada não é motor_v14 exato')
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=304 or digest(payload)!=PAYLOAD_SHA256:
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
