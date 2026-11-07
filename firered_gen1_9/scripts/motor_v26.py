#!/usr/bin/env python3
"""HUD MUNDO HH:MM e visibilidade em Opções, somente sobre a ROM v25 exata; saída exclusiva."""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v25 as previous
from scripts.treino_ev import write_new_file
BASE_SHA256=previous.OUTPUT_SHA256
OUTPUT_SHA256='ffba283f8d01885f9a8a3d5300135adeae008e6434a7c5c80ec7f695c1445ba7'
PAYLOAD_PATH=ROOT/'patches/motor_v26/payload.bin'
PAYLOAD_SHA256='cca07e6aed6e1c5e0f383ba025d4cbcba9b450e5b46ca25559eb5b8a76e09617'
PAYLOAD_SIZE=2509
PAYLOAD_OFFSET=0x10EA000
RESERVED_LIMIT=0x10EC000
ENTRY_UPDATE=0x090EA001
ENTRY_FIELD=0x090EA009
ENTRY_RENDER=0x090EA011
ENTRY_DIGITS=0x090EA019
ENTRY_PREPARE=0x090EA021
TAG=0xF925
ENTRY_HEADER=0x090EA029
ENTRY_INPUT=0x090EA031
ENTRY_PREFERENCE=0x090EA039
ENTRY_TOGGLE=0x090EA041
PREFERENCE_OFFSET=0x3660
PREFERENCE_MAGIC=0x36445548
VISIBLE=0x26A5FF00
HIDDEN=0x26A5FE01
HOOKS=(
    (0x101664,bytes.fromhex('004b184701800e09'),0x90EA001),
    (0xF1E20,bytes.fromhex('004b184709800e09'),0x90EA009),
    (0xEFB1C,bytes.fromhex('00b5112183b00020'),0x90EA029),
    (0xEF890,bytes.fromhex('10b52c4a138ed906'),0x90EA031),
)
PATCH_RANGES=tuple((at,8) for at,_,_ in HOOKS)+((PAYLOAD_OFFSET,PAYLOAD_SIZE),)
class PatchError(ValueError):pass

def digest(data):return hashlib.sha256(data).hexdigest()

def build(source,payload=None):
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:raise PatchError('Entrada não é motor_v25 exato')
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
