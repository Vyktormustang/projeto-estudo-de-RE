#!/usr/bin/env python3
"""Eerie Spell: bypass de Substitute e Shield Dust sobre motor_v12 exato.

Saída nova, sem novos aprendizados, itens, habilidades ou estado de RAM.
Os demais golpes sonoros não são modernizados por este patch.
"""
from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import motor_v10 as v10, motor_v11 as v11, motor_v12 as v12
from scripts.treino_ev import write_new_file

BASE_SHA256 = v12.OUTPUT_SHA256
OUTPUT_SHA256 = '71756c820ebb71c0c64735b0e8f36cf420da29ac419f8ee09a39109d9cb4951c'
PAYLOAD_PATH = ROOT / 'patches/motor_v13/payload.bin'
PAYLOAD_SHA256 = '158d2d621bfb6d977a9014c411ac2eaff8fe3701cafc4f834624cb1785c95355'
PAYLOAD_OFFSET = 0x10D7100
PAYLOAD_LIMIT = 0x10D8000
ENTRY_ADJUST = 0x090D7101
ENTRY_HEALTHBAR = 0x090D7109
ENTRY_DATAHP = 0x090D7111
ENTRY_POST = 0x090D7119
CALL_SITE = v11.CALL_SITE
COMMANDS = (
    (0x07, 0x08058FED, ENTRY_ADJUST),
    (0x0B, 0x090C0029, ENTRY_HEALTHBAR),
    (0x0C, 0x090D0041, ENTRY_DATAHP),
)
# Instruções cujo endereço é verificado nos wrappers C.
SCRIPT_SITES = ((13,b'\x07'), (20,b'\x0b\x00'), (22,b'\x0c\x00'))

class PatchError(ValueError):
    pass

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source) != 0x2000000 or digest(source) != BASE_SHA256:
        raise PatchError('Entrada não é motor_v12 de SHA-256 esperado')
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if digest(payload) != PAYLOAD_SHA256 or not 32 <= len(payload) <= PAYLOAD_LIMIT-PAYLOAD_OFFSET:
        raise PatchError('Payload inválido')
    if source[PAYLOAD_OFFSET:PAYLOAD_LIMIT] != b'\xff' * (PAYLOAD_LIMIT-PAYLOAD_OFFSET):
        raise PatchError('Área do payload ocupada')
    if source[CALL_SITE:CALL_SITE+5] != v10.callasm(v11.ENTRY):
        raise PatchError('Callasm v11 inesperado')
    for delta, code in SCRIPT_SITES:
        site = v10.SUB_STANDARD_HIT + delta
        if source[site:site+len(code)] != code:
            raise PatchError('Comando do script padrão inesperado')
    out = bytearray(source)
    for opcode, expected, entry in COMMANDS:
        site = v10.CMD_TABLE_V10 + 4*opcode
        if struct.unpack_from('<I',source,site)[0] != expected:
            raise PatchError(f'Comando {opcode:02X} divergente')
        struct.pack_into('<I',out,site,entry)
    out[CALL_SITE:CALL_SITE+5] = v10.callasm(ENTRY_POST)
    out[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)] = payload
    result = bytes(out)
    if digest(result) != OUTPUT_SHA256:
        raise PatchError('Hash de saída divergente')
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--saida',type=Path,required=True)
    args = parser.parse_args()
    result = build(args.rom.read_bytes())
    write_new_file(args.rom,args.saida,result)
    print(f'{args.saida}: {len(result)} B SHA-256 {digest(result)}')

if __name__ == '__main__':
    main()
