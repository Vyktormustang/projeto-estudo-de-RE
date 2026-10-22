#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida bytes locais do handler typecalc e do lookup da tabela de tipos.

Somente leitura. Labels semânticos e nomes de campos são cruzamentos externos;
o script confere endereços, instruções e registros u8 observados na ROM.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
SCRIPT_VA = 0x081D6900
COMMAND_TABLE_VA = 0x0825011C
MOVE_TABLE_VA = 0x08250C04
TYPE_CHART_VA = 0x0824F050
TYPE_CHART_ROWS = 112
TYPECALC_VA = 0x0801E849
MODULATE_VA = 0x0801E771


def off(va: int, length: int, data: bytes) -> int:
    result = va - ROM_BASE
    if result < 0 or result + length > len(data):
        raise SystemExit(f"VA fora da ROM: 0x{va:08X} (+0x{length:X})")
    return result


def u32(data: bytes, va: int) -> int:
    return struct.unpack_from("<I", data, off(va, 4, data))[0]


def expect(data: bytes, va: int, hex_bytes: str, label: str) -> None:
    wanted = bytes.fromhex(hex_bytes)
    pos = off(va, len(wanted), data)
    actual = data[pos : pos + len(wanted)]
    if actual != wanted:
        raise SystemExit(f"{label}: {actual.hex(' ')}, esperado {wanted.hex(' ')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    if u32(data, 0x081D65A8) != SCRIPT_VA:
        raise SystemExit("effectId 0 não aponta ao script local esperado")
    if u32(data, COMMAND_TABLE_VA + 6 * 4) != TYPECALC_VA:
        raise SystemExit("opcode 0x06 não aponta ao handler local esperado")
    expect(data, 0x081D6932, "06 07 09 0a", "sequência de bytecode após damagecalc")

    expect(data, TYPECALC_VA & ~1, "f0 b5 47 46 80 b4 82 b0", "entrada local do handler")
    expect(data, 0x0801E878, "25 4a 09 88 48 00 40 18 80 00 80 18 80 78", "lookup do tipo no registro de move")
    expect(data, 0x0801E8AA, "1c 4c 21 68 08 01 40 1a", "caminho STAB / multiplicador")
    expect(data, 0x0801E938, "02 49 58 18 00 78", "início do scan da tabela candidata")
    expect(data, 0x0801E9B4, "ff 28 0d d0 fe 28", "marcador de fim e sentinela")
    expect(data, MODULATE_VA & ~1, "30 b5 00 06 04 0e", "entrada do helper local de modulação")
    expect(data, 0x0801E77A, "60 43 0a 21 c5 f1 4b fc", "multiplicação e divisão locais")
    expect(data, 0x0801E7AA, "04 4a 10 78 08 21 08 43 fb 21", "atualização local de flags")
    expect(data, 0x0801EA70, "10 49 08 68 01 30 08 60", "avanço local do cursor")

    table_off = off(TYPE_CHART_VA, TYPE_CHART_ROWS * 3, data)
    rows = [data[table_off + i * 3 : table_off + (i + 1) * 3] for i in range(TYPE_CHART_ROWS)]
    if rows[108] != bytes.fromhex("fe fe 00") or rows[111] != bytes.fromhex("ff ff 00"):
        raise SystemExit("sentinelas locais do scan da tabela de tipos divergentes")
    if any(row[0] == 0xFF for row in rows[:-1]):
        raise SystemExit("terminador 0xFF inesperado antes da posição observada")

    literals = {
        0x0801E870: 0x02023D4A,
        0x0801E874: 0x02023FE8,
        0x0801E910: MOVE_TABLE_VA,
        0x0801E914: 0x02023BE4,
        0x0801E918: 0x02023D6B,
        0x0801E91C: 0x02023D50,
        0x0801E920: 0x02023D6C,
        0x0801E928: 0x02023DCC,
        0x0801E944: TYPE_CHART_VA,
        0x0801EA84: TYPE_CHART_VA,
        0x0801EA88: 0x02023BE4,
        0x0801EA8C: 0x02023D6C,
        0x0801EA98: 0x02023DCC,
        0x0801EAB4: 0x02023D74,
        0x0801E7A0: 0x02023D50,
        0x0801E7F0: MOVE_TABLE_VA,
        0x0801E7F4: 0x02023D4A,
        0x0801E7BC: 0x02023DCC,
    }
    for address, wanted in literals.items():
        actual = u32(data, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    end_va = TYPE_CHART_VA + TYPE_CHART_ROWS * 3
    print(f"ROM SHA-256: {digest}")
    print(f"opcode 0x06 @0x081D6932 → 0x{TYPECALC_VA:08X}; helper de multiplicador 0x{MODULATE_VA:08X}")
    print(f"tabela candidata local: 0x{TYPE_CHART_VA:08X}, {len(rows)} registros × 3 bytes, fim exclusivo 0x{end_va:08X}")
    print(f"sentinela 0xFE em índice 108; terminador 0xFF em índice 111; exemplos 0={rows[0].hex(' ')}, 108={rows[108].hex(' ')}, 111={rows[111].hex(' ')}")
    print(f"catálogo de moves usado pelo handler: 0x{MOVE_TABLE_VA:08X}; cursor local: 0x02023D74")
    print("Validação estática; nomes/campos semânticos e execução em batalha continuam separados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
