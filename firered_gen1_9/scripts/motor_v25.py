#!/usr/bin/env python3
"""HUD HH:MM do mundo, somente sobre a ROM v24 exata; saída exclusiva."""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v24 as previous
from scripts.treino_ev import write_new_file
BASE_SHA256=previous.OUTPUT_SHA256
OUTPUT_SHA256='1ef4e7235a95d20b12c7f281284febbf5ff8f0b59a8886968e46c225aa43a01d'
PAYLOAD_PATH=ROOT/'patches/motor_v25/payload.bin'
PAYLOAD_SHA256='6e3bb325c44681b743550185d477ba3a1d8179c9c9fb440ac3b729b98a10582c'
PAYLOAD_SIZE=1542
PAYLOAD_OFFSET=0x10E8000
RESERVED_LIMIT=0x10EA000
ENTRY_UPDATE=0x090E8001
ENTRY_FIELD=0x090E8009
ENTRY_RENDER=0x090E8011
ENTRY_DIGITS=0x090E8019
ENTRY_PREPARE=0x090E8021
TAG=0xF925
HOOKS=((0x101664,bytes.fromhex('004b184709600e09'),ENTRY_UPDATE),
       (0xF1E20,bytes.fromhex('004b184719d00d09'),ENTRY_FIELD))
PATCH_RANGES=tuple((at,8) for at,_,_ in HOOKS)+((PAYLOAD_OFFSET,PAYLOAD_SIZE),)
class PatchError(ValueError):pass

def digest(data):return hashlib.sha256(data).hexdigest()

def build(source,payload=None):
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:raise PatchError('Entrada não é motor_v24 exato')
    payload=PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=PAYLOAD_SIZE or digest(payload)!=PAYLOAD_SHA256:raise PatchError('Payload inválido')
    if source[PAYLOAD_OFFSET:RESERVED_LIMIT]!=b'\xff'*(RESERVED_LIMIT-PAYLOAD_OFFSET):raise PatchError('Reserva ocupada')
    out=bytearray(source)
    for at,before,target in HOOKS:
        if source[at:at+8]!=before:raise PatchError('Hook divergente')
        out[at:at+8]=struct.pack('<HHI',0x4B00,0x4718,target)
    out[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)]=payload
    result=bytes(out)
    if digest(result)!=OUTPUT_SHA256:raise PatchError('Hash final divergente')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--saida',type=Path,required=True)
    a=parser.parse_args();result=build(a.rom.read_bytes());write_new_file(a.rom,a.saida,result)
    print(f'{a.saida}: {len(result)} B SHA-256 {digest(result)}')
if __name__=='__main__':main()
