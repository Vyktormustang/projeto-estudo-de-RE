#!/usr/bin/env python3
"""Pivôs sem efeito e Soundproof/Parting Shot sobre v17 exato, sempre saída nova."""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts import motor_v17 as v17
from scripts import motor_v12 as v12
from scripts.treino_ev import write_new_file

BASE_SHA256 = v17.OUTPUT_SHA256
OUTPUT_SHA256 = 'f9a96edec0f070578dfec3d134dcb6decd5b4a5f7c296fef2c8346d7b9f504b2'
PAYLOAD_PATH = ROOT/'patches/motor_v18/payload.bin'
PAYLOAD_SHA256 = '6dd0dc125fe321e4775a587ae494140d611a70061f97e8f28e94e53cf8916147'
PAYLOAD_OFFSET = 0x10DC000
PAYLOAD_LIMIT = 0x10DC100
RESERVED_LIMIT = 0x10DD000
TABLE_OFFSET = 0x10DC100
OLD_MOVES = v12.NEW_MOVES
NEW_MOVES = OLD_MOVES + (571,)
TABLE_BYTES = struct.pack('<13H',*NEW_MOVES,0xFFFF)
COMMANDS = (
    (0x10C0064,0x090C07B5,0x090DC001),  # literal do vetor v7, mantendo a funcao original
    (v12.POINTER_SITE,0x090D7002,0x090DC102),  # lista sonora + 2, Growl tratado separadamente
)
PATCH_RANGES = ((0x10C0064,4),(v12.POINTER_SITE,4),(PAYLOAD_OFFSET,94),(TABLE_OFFSET,26))

class PatchError(ValueError):
    pass

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:
        raise PatchError('Entrada não é motor_v17 exato')
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=94 or digest(payload)!=PAYLOAD_SHA256:
        raise PatchError('Payload inválido')
    if source[v12.TABLE_OFFSET:v12.TABLE_OFFSET+len(v12.TABLE_BYTES)] != v12.TABLE_BYTES:
        raise PatchError('Tabela sonora v12 divergente')
    if source[PAYLOAD_OFFSET:RESERVED_LIMIT] != b'\xff'*(RESERVED_LIMIT-PAYLOAD_OFFSET):
        raise PatchError('Área de payload ocupada')
    out = bytearray(source)
    for offset,previous,entry in COMMANDS:
        if struct.unpack_from('<I',source,offset)[0]!=previous:
            raise PatchError('Comando anterior divergente')
        struct.pack_into('<I',out,offset,entry)
    out[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)] = payload
    out[TABLE_OFFSET:TABLE_OFFSET+len(TABLE_BYTES)] = TABLE_BYTES
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
