#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida bytes locais do caminho de accuracycheck e do cursor hit/miss.

Somente leitura e sem dependências externas. Os nomes/semântica de campo ou
comando não são necessários para esta validação; eles são cruzados à parte no
relatório, usando uma revisão upstream fixada.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
EFFECT_TABLE_VA = 0x081D65A8
COMMAND_TABLE_VA = 0x0825011C
CURRENT_CURSOR_VA = 0x02023D74
MOVE_CATALOG_VA = 0x08250C04
CURRENT_MOVE_VA = 0x02023D4A
MISS_STATE_VA = 0x02023DCC


def off(va: int, size: int, data: bytes) -> int:
    result = va - ROM_BASE
    if result < 0 or result + size > len(data):
        raise SystemExit(f"VA fora da ROM: 0x{va:08X} (+0x{size:X})")
    return result


def word(data: bytes, va: int) -> int:
    return struct.unpack_from("<I", data, off(va, 4, data))[0]


def expect(data: bytes, va: int, pattern: str, label: str) -> None:
    expected = bytes.fromhex(pattern)
    actual = data[off(va, len(expected), data) : off(va, len(expected), data) + len(expected)]
    if actual != expected:
        raise SystemExit(f"{label}: bytes {actual.hex(' ')}, esperado {expected.hex(' ')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    effect0 = word(data, EFFECT_TABLE_VA)
    if effect0 != 0x081D6900:
        raise SystemExit(f"pointer de efeito 0 divergente: 0x{effect0:08X}")
    command = 0x081D6927
    expect(data, command, "01 5e 69 1d 08 00 00", "bytecode accuracy amostrado")
    branch_target = struct.unpack_from("<I", data, off(command + 1, 4, data))[0]
    move_operand = struct.unpack_from("<H", data, off(command + 5, 2, data))[0]
    if branch_target != 0x081D695E or move_operand != 0:
        raise SystemExit("operands locais do comando em 0x081D6927 divergem")
    expect(data, 0x081D692E, "02 03 04 05 06 07", "sequência local após accuracy")
    expect(data, 0x081D695E, "02 03", "início local do destino de falha")

    handlers = {opcode: word(data, COMMAND_TABLE_VA + opcode * 4) for opcode in range(6)}
    expected_handlers = {
        0: 0x0801D761,
        1: 0x0801DDC5,
        2: 0x0801E1D9,
        3: 0x0801E22D,
        4: 0x0801E409,
        5: 0x0801E59D,
    }
    if handlers != expected_handlers:
        raise SystemExit(f"handlers locais 0..5 divergentes: {handlers}")

    expect(data, 0x0801DF0C, "00 2e 01 d1 06 48 06 88", "fallback local para ID corrente")
    expect(data, 0x0801DF3E, "80 78", "load local do byte +2")
    expect(data, 0x0801DFCA, "fb 78", "load local do byte +3")
    expect(data, 0x0801E150, "26 f0 ba fe", "chamada local ao gerador pseudoaleatório")
    expect(data, 0x0801E15A, "c6 f1 93 fa", "chamada local ao helper aritmético")
    expect(data, 0x0801E168, "0d 4a 10 78 01 21 08 43 10 70", "set local de bit no resultado")
    expect(data, 0x0801E1BA, "07 20 31 1c ff f7 a7 fc", "chamada do helper com avanço 7")

    literals = {
        0x0801DE60: CURRENT_CURSOR_VA,
        0x0801DE68: MOVE_CATALOG_VA,
        0x0801DF2C: CURRENT_MOVE_VA,
        0x0801DF88: MOVE_CATALOG_VA,
        0x0801E100: MOVE_CATALOG_VA,
        0x0801E1A0: MISS_STATE_VA,
        0x0801DB5C: CURRENT_CURSOR_VA,
        0x0801DB60: MISS_STATE_VA,
        0x0801DB9C: CURRENT_CURSOR_VA,
    }
    for address, expected in literals.items():
        actual = word(data, address)
        if actual != expected:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}; esperado 0x{expected:08X}")

    print(f"ROM SHA-256: {digest}")
    print(f"efeito 0 -> script 0x{effect0:08X}; accuracy opcode 0x01 em 0x{command:08X}")
    print(f"operando local: destino de falha=0x{branch_target:08X}, u16=0x{move_operand:04X}")
    print("opcodes 0..5 → handlers:", ", ".join(f"0x{k:02X}→0x{v:08X}" for k, v in handlers.items()))
    print(f"literais locais confirmados: cursor=0x{CURRENT_CURSOR_VA:08X}, moveTable=0x{MOVE_CATALOG_VA:08X}, currentMove=0x{CURRENT_MOVE_VA:08X}, missByte=0x{MISS_STATE_VA:08X}")
    print("Validação estática; não executa batalha nem modifica ROM/save.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
