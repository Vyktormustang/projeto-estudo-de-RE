#!/usr/bin/env python3
"""Phazing de treinador sem falha por nível sobre v15 exato, sempre saída nova."""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts import motor_v15 as v15
from scripts.treino_ev import write_new_file

BASE_SHA256 = v15.OUTPUT_SHA256
OUTPUT_SHA256 = '644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc'
PAYLOAD_PATH = ROOT/'patches/motor_v16/payload.bin'
PAYLOAD_SHA256 = 'f1946a84a7932215b83e6d01e4d6794e4b1dbab334fb49c2236b48ad185c0ceb'
PAYLOAD_OFFSET = 0x10DA000
PAYLOAD_LIMIT = 0x10DB000
COMMANDS = ((0x10CFE3C,0x08060DD1,0x090DA001),)

class PatchError(ValueError):
    pass

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:
        raise PatchError('Entrada não é motor_v15 exato')
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=300 or digest(payload)!=PAYLOAD_SHA256:
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
