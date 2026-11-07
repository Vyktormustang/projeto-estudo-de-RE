#!/usr/bin/env python3
"""Continua o relógio do mundo após a saturação nativa, sobre v23 exata."""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts import motor_v23 as previous
from scripts.treino_ev import write_new_file
BASE_SHA256=previous.OUTPUT_SHA256
OUTPUT_SHA256='5fe26a76ee13a85a8dbccecc61ce3f89ed7f44a49d221b8621acb4a0966e36d2'
PAYLOAD_PATH=ROOT/'patches/motor_v24/payload.bin'
PAYLOAD_SHA256='d13a59fe1ba0a04b24a344d8f0f185033ea9ca3e06052b6d3435d8db007610fc'
PAYLOAD_SIZE=870
PAYLOAD_OFFSET=0x10E6000
RESERVED_LIMIT=0x10E8000
ENTRY_MINUTES=0x090E6001
ENTRY_UPDATE=0x090E6009
RECORD_OFFSET=0x3658
RECORD_MAGIC=0x34324B43
T9_MAGIC=0x31583954
HOOKS=(
    (0x101664,bytes.fromhex('194a1378012b00d0'),ENTRY_UPDATE),
    (0x10DD038,bytes.fromhex('10b51a4802680f20'),ENTRY_MINUTES),
)
PATCH_RANGES=tuple((at,len(before)) for at,before,_ in HOOKS)+((PAYLOAD_OFFSET,PAYLOAD_SIZE),)
class PatchError(ValueError): pass

def digest(data):return hashlib.sha256(data).hexdigest()

def changes(source,payload=None):
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:raise PatchError('Entrada não é motor_v23 exato')
    payload=PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=PAYLOAD_SIZE or digest(payload)!=PAYLOAD_SHA256:raise PatchError('Payload inválido')
    if source[PAYLOAD_OFFSET:RESERVED_LIMIT]!=b'\xff'*(RESERVED_LIMIT-PAYLOAD_OFFSET):raise PatchError('Reserva ocupada')
    if struct.unpack_from('<I',source,0x10DD004)[0]!=0x090DD039:raise PatchError('Entrada do relógio divergente')
    if source[0x10166C:0x101670]!=bytes.fromhex('7047184b'):raise PatchError('Retorno/retomada nativa divergente')
    out=[]
    for at,before,target in HOOKS:
        if source[at:at+len(before)]!=before:raise PatchError('Hook anterior divergente')
        out.append((at,struct.pack('<HHI',0x4B00,0x4718,target)))
    out.append((PAYLOAD_OFFSET,payload))
    return out

def build(source,payload=None):
    out=bytearray(source)
    for at,data in changes(source,payload):out[at:at+len(data)]=data
    result=bytes(out)
    if digest(result)!=OUTPUT_SHA256:raise PatchError('Hash final divergente')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--saida',type=Path,required=True)
    a=parser.parse_args();out=build(a.rom.read_bytes());write_new_file(a.rom,a.saida,out)
    print(f'{a.saida}: {len(out)} B SHA-256 {digest(out)}')
if __name__=='__main__':main()
