#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida bytes locais do opcode 0x07 e do handler de ajuste de dano.

Leitura estática somente: não executa batalha e não aplica nomes upstream aos
bytes. O rótulo `Cmd_adjustnormaldamage` é documentado como cross-reference.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
SCRIPT_PTR = 0x081D65A8
SCRIPT_VA = 0x081D6900
SCRIPT_COMMANDS_VA = 0x081D6931
COMMAND_TABLE_VA = 0x0825011C
HANDLER_VA = 0x0801F105
MOVE_TABLE_VA = 0x08250C04


def offset(va: int, size: int, data: bytes) -> int:
    pos = va - ROM_BASE
    if pos < 0 or pos + size > len(data):
        raise SystemExit(f"VA fora da ROM: 0x{va:08X} (+0x{size:X})")
    return pos


def u32(data: bytes, va: int) -> int:
    return struct.unpack_from("<I", data, offset(va, 4, data))[0]


def expect(data: bytes, va: int, wanted_hex: str, label: str) -> None:
    wanted = bytes.fromhex(wanted_hex)
    pos = offset(va, len(wanted), data)
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

    if u32(data, SCRIPT_PTR) != SCRIPT_VA:
        raise SystemExit("ponteiro local do script de efeito 0 divergente")
    if u32(data, COMMAND_TABLE_VA + 7 * 4) != HANDLER_VA:
        raise SystemExit("opcode 0x07 não aponta ao handler local esperado")
    expect(data, SCRIPT_COMMANDS_VA, "05 06 07 09 0a", "bytecode local no recorte")

    expect(data, HANDLER_VA & ~1, "f0 b5 25 f0 df fe 00 04 00 0c 0f 21", "entrada local e chamada inicial")
    expect(data, 0x0801F11E, "00 28 09 d0 48 43 20 60 64 21 c4 f1 76 ff 20 60", "multiplicação/divisão de dano")
    expect(data, 0x0801F142, "c1 19 c8 8d af 28 10 d1", "leitura do halfword do registro do defensor")
    expect(data, 0x0801F18E, "27 2c 18 d1", "comparação local do efeito 0x27")
    expect(data, 0x0801F1D6, "80 20 40 04 01 40 15 1c 00 29", "teste do bit local de status e retorno")
    expect(data, 0x0801F1E2, "1d 4a 1d 48 01 88 48 00 40 18 80 00", "leitura de efeito no registro candidato de move")
    expect(data, 0x0801F216, "18 78 58 24 60 43 40 19 01 8d", "teste de HP e dano")
    expect(data, 0x0801F228, "48 1e 10 60", "gravação local de HP menos um no dano")
    expect(data, 0x0801F294, "06 49 08 68 01 30 08 60 f0 bc 01 bc 00 47", "avanço do cursor e retorno")

    literals = {
        0x0801F15C: 0x02023D50,
        0x0801F160: 0x02023BE4,
        0x0801F164: 0x02023D6C,
        0x0801F168: 0x02023F54,
        0x0801F248: 0x02023D6F,
        0x0801F24C: 0x02023D6C,
        0x0801F250: 0x02023ECC,
        0x0801F254: 0x02023BE4,
        0x0801F258: MOVE_TABLE_VA,
        0x0801F25C: 0x02023D4A,
        0x0801F260: 0x02023E8C,
        0x0801F264: 0x02023D50,
        0x0801F268: 0x02023DCC,
        0x0801F2A4: 0x02023ECC,
        0x0801F2A8: 0x02023DCC,
        0x0801F2AC: 0x02023D68,
        0x0801F2B0: 0x02023D74,
    }
    for address, wanted in literals.items():
        actual = u32(data, address)
        if actual != wanted:
            raise SystemExit(f"literal 0x{address:08X}=0x{actual:08X}, esperado 0x{wanted:08X}")

    print(f"ROM SHA-256: {digest}")
    print(f"bytecode 0x07 @0x081D6933 → 0x{HANDLER_VA:08X}; instruções começam em 0x{HANDLER_VA & ~1:08X}")
    print("validado: fator local 100-(retorno & 0x0F), ajuste do dano, ramos por item/estado/HP e cursor")
    print("Validação estática; nomes upstream e execução dinâmica permanecem separados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
