#!/usr/bin/env python3
"""Corrige PP extra de Rollout/Ice Ball interrompidos por Protect/Detect.

Entrada v13 exata, saida nova; dois intervalos de escrita, sem RAM/save novo.
"""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts import motor_v13 as v13
from scripts.treino_ev import write_new_file

BASE_SHA256 = v13.OUTPUT_SHA256
OUTPUT_SHA256 = '2302ba1c88194fec190d0da062f91380ba062ee06e5a4a626902767412a9682c'
PAYLOAD_PATH = ROOT / 'patches/motor_v14/payload.bin'
PAYLOAD_SHA256 = 'c8dc9a83f1a57f8d1cf339d6908c8c38d51f1108517700ce5156a006b4d0fe11'
PAYLOAD_OFFSET = 0x10D8000
PAYLOAD_LIMIT = 0x10D9000
ENTRY = 0x090D8001
COMMAND_SITE = 0x10CFC00
PREVIOUS = 0x090D0019
SCRIPT_OFFSET = 0x186348
SCRIPT_PREFIX = bytes.fromhex('00 02 1d 01 00 10 00 00 55 63 18 08 03')

class PatchError(ValueError):
    pass

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source) != 0x2000000 or digest(source) != BASE_SHA256:
        raise PatchError('Entrada não é motor_v13 exato')
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload) != 210 or digest(payload) != PAYLOAD_SHA256:
        raise PatchError('Payload inválido')
    if source[PAYLOAD_OFFSET:PAYLOAD_LIMIT] != b'\xff'*(PAYLOAD_LIMIT-PAYLOAD_OFFSET):
        raise PatchError('Área de payload ocupada')
    if struct.unpack_from('<I',source,COMMAND_SITE)[0] != PREVIOUS:
        raise PatchError('Comando anterior divergente')
    if source[SCRIPT_OFFSET:SCRIPT_OFFSET+len(SCRIPT_PREFIX)] != SCRIPT_PREFIX:
        raise PatchError('Fluxo nativo Rollout divergente')
    if struct.unpack_from('<I',source,0x100A000+117*4)[0] != 0x08000000+SCRIPT_OFFSET:
        raise PatchError('Ponteiro de efeito divergente')
    for move in (205,301):
        if source[0x1000000+12*move:0x1000000+12*move+2] != bytes((117,30)):
            raise PatchError('Dados de golpe divergentes')
    out = bytearray(source)
    struct.pack_into('<I',out,COMMAND_SITE,ENTRY)
    out[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)] = payload
    result = bytes(out)
    if digest(result) != OUTPUT_SHA256:
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

if __name__ == '__main__':
    main()
