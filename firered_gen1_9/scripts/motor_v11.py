#!/usr/bin/env python3
"""Correção isolada de Eerie Spell sobre motor_v10; entrada SHA exata, saída nova.

Não adiciona aprendizados nem altera a IA. Simple Beam, Ally Switch, Instruct
e Revival Blessing continuam pendentes (21 linhas). Não contém ROM ou saves.
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
from scripts import motor_v10 as v10
from scripts.treino_ev import write_new_file

BASE_SHA256 = v10.OUTPUT_SHA256
OUTPUT_SHA256 = "1a147ee909183cc2e3bbba0599a4d70f0b0185b01d3e4941a1f27e6c4a9eee5b"
PAYLOAD_PATH = ROOT / "patches/motor_v11/payload.bin"
PAYLOAD_SHA256 = "0264257315bfe35e6012808c3d6e21bf98d60e372c81dc5843976b8271940dfc"
PAYLOAD_OFFSET = 0x10D6100
PAYLOAD_LIMIT = 0x10D7000
ENTRY = 0x090D6101
WAIT_OFFSET = 0x10D6000
WAIT_SCRIPT = b"\x3a\x28" + struct.pack("<I", v10.BS_MOVE_END)
CALL_SITE = v10.SUB_STANDARD_HIT + 40

class PatchError(ValueError):
    pass

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build(source: bytes, payload: bytes | None = None) -> bytes:
    if len(source) != 0x2000000 or digest(source) != BASE_SHA256:
        raise PatchError("Entrada não é motor_v10 de SHA-256 esperado")
    payload = PAYLOAD_PATH.read_bytes() if payload is None else payload
    if digest(payload) != PAYLOAD_SHA256 or not 8 <= len(payload) <= PAYLOAD_LIMIT - PAYLOAD_OFFSET:
        raise PatchError("Payload inválido")
    if source[WAIT_OFFSET:PAYLOAD_LIMIT] != b"\xff" * (PAYLOAD_LIMIT - WAIT_OFFSET):
        raise PatchError("Área reservada ocupada")
    expected = v10.callasm(v10.ENTRY_POST_HIT_V10)
    if source[CALL_SITE:CALL_SITE + 5] != expected:
        raise PatchError("Callasm pós-impacto inesperado")
    if struct.unpack_from("<I", source, 0x62A54)[0] != 0x020215D4:
        raise PatchError("Literal gLastMoves de Spite inesperado")
    out = bytearray(source)
    out[CALL_SITE:CALL_SITE + 5] = v10.callasm(ENTRY)
    out[WAIT_OFFSET:WAIT_OFFSET + len(WAIT_SCRIPT)] = WAIT_SCRIPT
    out[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(payload)] = payload
    result = bytes(out)
    if digest(result) != OUTPUT_SHA256:
        raise PatchError("Hash de saída divergente")
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.rom.read_bytes())
    write_new_file(args.rom, args.saida, result)
    print(f"{args.saida}: {len(result)} B SHA-256 {digest(result)}")

if __name__ == "__main__":
    main()
