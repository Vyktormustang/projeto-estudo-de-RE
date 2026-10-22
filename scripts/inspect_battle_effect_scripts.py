#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida localmente dois scripts de efeito e seus comandos/handlers Thumb.

A leitura é somente de bytes. Nomes de opcodes e scripts são cruzamentos
semânticos externos; o script valida endereços, bytes e ponteiros observados na
ROM, sem depender da árvore upstream nem modificar a ROM/save.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
EFFECT_PTR_TABLE_VA = 0x081D65A8
EFFECTS_CHECKED = {0: 0x081D6900, 125: 0x081D7977}
COMMAND_HANDLER_TABLE_VA = 0x0825011C
COMMAND_COUNT_CANDIDATE = 248
COMMAND_HANDLERS = {
    0x00: 0x0801D761,
    0x01: 0x0801DDC5,
    0x21: 0x08021989,
    0x28: 0x08022651,
    0x2A: 0x08022711,
    0x2E: 0x08022979,
    0x35: 0x08022B1D,
}


def offset(va: int, size: int, data: bytes) -> int:
    result = va - ROM_BASE
    if result < 0 or result + size > len(data):
        raise SystemExit(f"VA fora da ROM: 0x{va:08X} (+0x{size:X})")
    return result


def read_u32(data: bytes, va: int) -> int:
    return struct.unpack_from("<I", data, offset(va, 4, data))[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    for effect_id, expected in EFFECTS_CHECKED.items():
        actual = read_u32(data, EFFECT_PTR_TABLE_VA + effect_id * 4)
        if actual != expected:
            raise SystemExit(f"effect {effect_id}: ponteiro 0x{actual:08X}, esperado 0x{expected:08X}")

    hit_prefix = bytes.fromhex("2a014a3d0202390026691d08")
    hit_off = offset(EFFECTS_CHECKED[0], len(hit_prefix), data)
    if data[hit_off : hit_off + len(hit_prefix)] != hit_prefix:
        raise SystemExit("prefixo local do script de efeito 0 diverge")
    if data[offset(0x081D6926, 2, data) : offset(0x081D6926, 2, data) + 2] != b"\x00\x01":
        raise SystemExit("bytes no alvo local 0x081D6926 divergem")

    thaw_prefix = bytes.fromhex("2e853e0202032800691d08")
    thaw_off = offset(EFFECTS_CHECKED[125], len(thaw_prefix), data)
    if data[thaw_off : thaw_off + len(thaw_prefix)] != thaw_prefix:
        raise SystemExit("prefixo local do script de efeito 125 diverge")

    table_off = offset(COMMAND_HANDLER_TABLE_VA, COMMAND_COUNT_CANDIDATE * 4 + 4, data)
    handlers = list(struct.unpack_from(f"<{COMMAND_COUNT_CANDIDATE}I", data, table_off))
    rom_end = ROM_BASE + len(data)
    if not all(ROM_BASE <= (p & ~1) < rom_end for p in handlers):
        raise SystemExit("nem todos os 248 handlers candidatos apontam para a ROM")
    next_word = struct.unpack_from("<I", data, table_off + COMMAND_COUNT_CANDIDATE * 4)[0]
    if ROM_BASE <= (next_word & ~1) < rom_end:
        raise SystemExit("a palavra seguinte à sequência também parece ponteiro interno à ROM")
    for opcode, expected in COMMAND_HANDLERS.items():
        actual = handlers[opcode]
        if actual != expected:
            raise SystemExit(f"opcode 0x{opcode:02X}: handler 0x{actual:08X}, esperado 0x{expected:08X}")

    # O chamador lê o opcode de [0x02023D74], usa a tabela acima e passa o
    # endereço selecionado ao trampoline local bx r0 em 0x081E3BA8.
    interpreter_literals = (
        read_u32(data, 0x08015A28),
        read_u32(data, 0x08015A2C),
    )
    if interpreter_literals != (COMMAND_HANDLER_TABLE_VA, 0x02023D74):
        raise SystemExit("literais do dispatcher local de comandos divergem")
    if data[offset(0x081E3BA8, 2, data) : offset(0x081E3BA8, 2, data) + 2] != b"\x00\x47":
        raise SystemExit("trampoline local em 0x081E3BA8 não corresponde a bx r0")

    print(f"ROM SHA-256: {digest}")
    print(f"effectId 0 -> script 0x{EFFECTS_CHECKED[0]:08X}; bytes: {hit_prefix.hex(' ')}")
    print(f"effectId 125 -> script 0x{EFFECTS_CHECKED[125]:08X}; bytes: {thaw_prefix.hex(' ')}")
    print(
        f"tabela candidata de comandos: 0x{COMMAND_HANDLER_TABLE_VA:08X}, "
        f"{len(handlers)} ponteiros internos à ROM, palavra seguinte=0x{next_word:08X}"
    )
    print("opcode→handler local:", ", ".join(f"0x{k:02X}→0x{handlers[k]:08X}" for k in COMMAND_HANDLERS))
    print(f"trampoline local 0x081E3BA8: bytes {data[offset(0x081E3BA8, 2, data):offset(0x081E3BA8, 2, data)+2].hex(' ')}")
    print("Validação estática; nomes/semântica dos scripts e opcodes exigem cruzamento separado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
