#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida o caminho local do opcode 0x05 ao helper de dano base.

O script verifica bytes e literais da ROM, somente leitura. Nomes de globais,
campos e rotinas são cruzamentos semânticos separados; não há execução dinâmica.
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
EFFECT_TABLE_VA = 0x081D65A8
COMMAND_TABLE_VA = 0x0825011C
MOVE_TABLE_VA = 0x08250C04
DAMAGE_HANDLER_VA = 0x0801E59D
BASE_DAMAGE_HELPER_VA = 0x0803ECEC


def offset(va: int, length: int, data: bytes) -> int:
    result = va - ROM_BASE
    if result < 0 or result + length > len(data):
        raise SystemExit(f"VA fora da ROM: 0x{va:08X} (+0x{length:X})")
    return result


def read_u32(data: bytes, va: int) -> int:
    return struct.unpack_from("<I", data, offset(va, 4, data))[0]


def expect(data: bytes, va: int, pattern: str, label: str) -> None:
    wanted = bytes.fromhex(pattern)
    pos = offset(va, len(wanted), data)
    actual = data[pos : pos + len(wanted)]
    if actual != wanted:
        raise SystemExit(f"{label}: bytes {actual.hex(' ')}, esperado {wanted.hex(' ')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    if read_u32(data, EFFECT_TABLE_VA) != SCRIPT_VA:
        raise SystemExit("índice 0 da tabela de efeitos não aponta ao script amostrado")
    if read_u32(data, COMMAND_TABLE_VA + 5 * 4) != DAMAGE_HANDLER_VA:
        raise SystemExit("opcode 0x05 não aponta ao handler local esperado")
    if read_u32(data, COMMAND_TABLE_VA + 6 * 4) != 0x0801E849:
        raise SystemExit("opcode 0x06 não aponta ao handler local esperado")
    expect(data, 0x081D6931, "05 06", "sequência script dano→tipo")

    expect(data, DAMAGE_HANDLER_VA & ~1, "f0 b5 84 b0", "entrada do handler local")
    expect(data, 0x0801E5E0, "20 f0 84 fb", "chamada local ao helper de dano")
    expect(data, 0x0801E5E6, "23 49 09 78 41 43", "multiplicação do retorno por byte local")
    expect(data, 0x0801E5EC, "22 48 80 7b 0b 1c 43 43 23 60", "segunda multiplicação e gravação")
    expect(data, 0x0801E616, "80 78 0d 28 01 d1 58 00 20 60", "teste de tipo e dobro condicional")
    expect(data, 0x0801E63A, "0a 21 c5 f1 ec fc 20 60", "multiplicação/divisão condicional")
    expect(data, 0x0801E642, "11 49 08 68 01 30 08 60", "avanço local do cursor")

    literals = {
        0x0801E658: 0x02023D6C,
        0x0801E65C: 0x02023D6B,
        0x0801E660: 0x02023BE4,
        0x0801E664: 0x02023D4A,
        0x0801E668: 0x02023F50,
        0x0801E66C: 0x02023FE8,
        0x0801E670: 0x02023D50,
        0x0801E674: 0x02023D71,
        0x0801E678: 0x02023FC4,
        0x0801E67C: 0x02023DFC,
        0x0801E680: MOVE_TABLE_VA,
        0x0801E684: 0x02023E8C,
        0x0801E688: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = read_u32(data, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}; esperado 0x{wanted:08X}")

    expect(data, BASE_DAMAGE_HELPER_VA, "f0 b5", "entrada do helper local de dano base")
    expect(data, 0x0803ED32, "40 78 10 80", "leitura local de byte +1 do catálogo")
    expect(data, 0x0803ED54, "80 78 81 46", "leitura local de byte +2 do catálogo")
    expect(data, 0x0803ED6E, "77 88", "leitura halfword em argumento de atacante")
    expect(data, 0x0803ED72, "92 88", "leitura halfword em argumento de defensor")

    print(f"ROM SHA-256: {digest}")
    print(f"opcode 0x05 @0x081D6931 → 0x{DAMAGE_HANDLER_VA:08X} → helper 0x{BASE_DAMAGE_HELPER_VA:08X}")
    print(f"catálogo move local: 0x{MOVE_TABLE_VA:08X}, stride calculado no handler: 12 bytes")
    print("literais de estado/estruturas do handler:", ", ".join(f"0x{v:08X}" for v in literals.values()))
    print("Verificação estática; fórmula completa, ramos raros e comportamento dinâmico permanecem fora do script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
