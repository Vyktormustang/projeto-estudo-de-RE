#!/usr/bin/env python3
"""Rascunho verificável de estojo paginado, sobre a ROM parcial de 32 MiB.

Preserva o arquivo de entrada. Este módulo não garante mecânicas de batalha
modernas; não use com a única cópia de um save pessoal.
"""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts.treino_ev import write_new_file

BASE_SHA256 = '6155b6a5fe62528b7b67836d3a47f32b1cb3b1a71c1f2b59bfa7a68af0100d67'
OUTPUT_SHA256 = ''  # preenchido somente depois dos testes
PAYLOAD_SHA256 = 'b1a7cc5435dd4b134d81d63942b7aece63c9c0502063888946744553f38cc842'
PAYLOAD_PATH = ROOT / 'patches/estojo_expandido/payload.bin'
PAYLOAD_START, PAYLOAD_END = 0x10B8000, 0x10BC000
ROM_START = 0x08000000
HOOKS = (
    (0x0C6848, '97 23 00 04 09 04 30 b5', 0),  # CheckBagHasItem
    (0x0C68FC, '97 23 00 04 09 04 70 b5', 8),  # CheckBagHasSpace
    (0x0C69A4, '97 23 00 04 09 04 f0 b5', 16), # AddBagItem
    (0x0C6B38, '97 23 00 04 09 04 30 b5', 24), # RemoveBagItem
    (0x0C7100, '97 23 00 04 10 b5 00 0c', 32), # BagGetQuantityByItemId
    (0x14B194, 'f0 b5 00 24 c6 46 19 4b', 40), # InitTMCase
    (0x14BA7C, '11 4b 18 68 00 b5 00 28', 48), # DestroyTMCaseBuffers
    (0x14BB7C, 'f0 b5 d6 46 4f 46 46 46', 56), # Task_HandleListInput
    (0x14D008, '10 b5 0c 4c 83 b0 21 00', 64), # PrintTitle
)

class PatchError(ValueError): pass

def digest(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source) != 0x2000000 or source[0xAC:0xB0] != b'BPRE' or digest(source) != BASE_SHA256:
        raise PatchError('Entrada diferente da ROM parcial identificada; nada foi alterado')
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if digest(payload) != PAYLOAD_SHA256 or not 0 < len(payload) <= PAYLOAD_END-PAYLOAD_START:
        raise PatchError('Payload alterado ou maior que a área reservada')
    if source[PAYLOAD_START:PAYLOAD_END] != b'\xff'*(PAYLOAD_END-PAYLOAD_START):
        raise PatchError('Área de código não está vazia')
    for i, (value,) in enumerate(struct.iter_unpack('<I', source)):
        if ROM_START + PAYLOAD_START <= value < ROM_START + PAYLOAD_END:
            raise PatchError(f'Área já referenciada por palavra alinhada em {4*i:#x}')
    for at, original, _ in HOOKS:
        if source[at:at+8] != bytes.fromhex(original): raise PatchError(f'Hook inesperado em {at:#x}')
    out = bytearray(source)
    out[PAYLOAD_START:PAYLOAD_START+len(payload)] = payload
    for at, _, vector in HOOKS:
        out[at:at+8] = b'\x00\x4b\x18\x47' + struct.pack('<I', ROM_START+PAYLOAD_START+vector+1)
    return bytes(out)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True); p.add_argument('--saida',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.rom.resolve()==a.saida.resolve() or a.saida.exists(): raise PatchError('A saída deve ser um arquivo novo')
        source=a.rom.read_bytes(); result=build(source)
        if OUTPUT_SHA256 and digest(result)!=OUTPUT_SHA256: raise PatchError('SHA da saída divergente')
        write_new_file(a.rom,a.saida,result)
        print(f'Entrada preservada: {digest(source)}\nNova cópia: {a.saida}\nSHA-256: {digest(result)}')
        print('Rascunho: use somente com saves sintéticos ou com backup independente.')
    except (OSError,ValueError) as exc:
        print(f'[ERRO] {exc}',file=sys.stderr); return 1
    return 0
if __name__ == '__main__': raise SystemExit(main())
