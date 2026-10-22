#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revalida referências locais a 0x4A e 0xA6 em scripts de efeito.

A checagem é somente leitura. Bytes e ponteiros vêm da ROM BR local. A
classificação dos limites dos comandos usa, em separado, o cross-reference dos
macros upstream fixado nos relatórios; isto não prova que qualquer batalha ou
handler foi executado.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

ROM_SHA256 = "6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae"
ROM_PATH = Path(__file__).resolve().parents[1] / "google_drive" / "Pokemon - Fire Red (BR).gba"
ROM_BASE = 0x08000000
MOVE_TABLE_VA = 0x08250C04
MOVE_COUNT_CANDIDATE = 355
MOVE_STRIDE = 12
EFFECT_SCRIPT_TABLE_VA = 0x081D65A8
COMMAND_TABLE_VA = 0x0825011C
PRIMARY_CALLBACK_TABLE_VA = 0x08250038
PRIMARY_CALLBACK_COUNT_CANDIDATE = 14
SECONDARY_CALLBACK_TABLE_VA = 0x08250070
SECONDARY_CALLBACK_COUNT_CANDIDATE = 9
CALLBACK_DISPATCH_VA = 0x080155E4
CALLBACK_ENTRY0_VA = 0x08015CA0
TRAMPOLINE_VA = 0x081E3BA8
MAIN_CALLBACK_DISPATCH_VA = 0x08000524
MAIN_CALLBACK_SLOT_VA = 0x030030F0
CALLBACK_RUNNER_VA = 0x080123E4
CALLBACK_RUNNER_SLOT_VA = 0x03004F84
CALLBACK_SETUP_VA = 0x080154A0
LEARNSET_POINTER_TABLE_VA = 0x0825D7B4
LEARNSET_POINTER_COUNT = 412
LEARNSET_DATA_START_VA = 0x08257494
LEARNSET_FINAL_SCAN_LIMIT = 0x100

# Record index -> local byte +0 used as the effect-table index.
MOVE_EFFECTS = {
    68: 0x59,
    176: 0x5D,
    205: 0x75,
    301: 0x75,
    243: 0x90,
    280: 0xBA,
}
# Effect-table index -> local script pointer.
SCRIPTS = {
    0x59: 0x081D7433,
    0x5D: 0x081D74D6,
    0x75: 0x081D78A0,
    0x90: 0x081D7A89,
    0xBA: 0x081D81B9,
}


def offset(va: int, size: int, data: bytes) -> int:
    pos = va - ROM_BASE
    if pos < 0 or pos + size > len(data):
        raise SystemExit(f"endereço fora da ROM: 0x{va:08X} (+0x{size:X})")
    return pos


def read_u16(data: bytes, va: int) -> int:
    return struct.unpack_from("<H", data, offset(va, 2, data))[0]


def read_u32(data: bytes, va: int) -> int:
    return struct.unpack_from("<I", data, offset(va, 4, data))[0]


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value & (sign - 1)) - (value & sign)


def thumb_short_branch_target(va: int, insn: int) -> int | None:
    if insn & 0xF800 == 0xE000:  # B imm11
        return va + 4 + (sign_extend(insn & 0x07FF, 11) << 1)
    if insn & 0xF000 == 0xD000 and ((insn >> 8) & 0xF) <= 0xD:  # B<cond> imm8
        return va + 4 + (sign_extend(insn & 0x00FF, 8) << 1)
    return None


def expect(data: bytes, va: int, hex_bytes: str, label: str) -> None:
    wanted = bytes.fromhex(hex_bytes)
    pos = offset(va, len(wanted), data)
    actual = data[pos : pos + len(wanted)]
    if actual != wanted:
        raise SystemExit(f"{label}: {actual.hex(' ')}, esperado {wanted.hex(' ')}")


def scan_learnset_references(data: bytes, move_ids: set[int]) -> dict[int, list[tuple[int, int]]]:
    """Read the documented pointer table and collect matching low-9-bit IDs."""
    table_off = offset(LEARNSET_POINTER_TABLE_VA, LEARNSET_POINTER_COUNT * 4, data)
    pointers = list(struct.unpack_from(f"<{LEARNSET_POINTER_COUNT}I", data, table_off))
    rom_end = ROM_BASE + len(data)
    if pointers[0] != LEARNSET_DATA_START_VA or any(
        not LEARNSET_DATA_START_VA <= p < rom_end for p in pointers
    ) or any(a > b for a, b in zip(pointers, pointers[1:])):
        raise SystemExit("tabela local de learnsets não satisfaz os limites/ordem esperados")

    unique = sorted(set(pointers))
    parsed: dict[int, list[int]] = {}
    for i, pointer in enumerate(unique):
        start = offset(pointer, 2, data)
        limit = (
            unique[i + 1] - ROM_BASE
            if i + 1 < len(unique)
            else min(len(data), start + LEARNSET_FINAL_SCAN_LIMIT)
        )
        words = []
        for pos in range(start, limit - 1, 2):
            word = struct.unpack_from("<H", data, pos)[0]
            if word == 0xFFFF:
                break
            words.append(word)
        else:
            raise SystemExit(f"learnset sem 0xFFFF antes do limite: 0x{pointer:08X}")
        parsed[pointer] = words

    hits = {move_id: [] for move_id in sorted(move_ids)}
    for table_index, pointer in enumerate(pointers):
        for word in parsed[pointer]:
            move_id = word & 0x01FF
            if move_id in hits:
                hits[move_id].append((table_index, (word & 0xFE00) >> 9))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path, default=ROM_PATH)
    data = parser.parse_args().rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != ROM_SHA256:
        raise SystemExit(f"SHA-256 inesperado: {digest} (esperado {ROM_SHA256})")

    for move_index, expected_effect in MOVE_EFFECTS.items():
        if not 0 <= move_index < MOVE_COUNT_CANDIDATE:
            raise SystemExit(f"move-record index fora do intervalo candidato: {move_index}")
        va = MOVE_TABLE_VA + move_index * MOVE_STRIDE
        actual = data[offset(va, MOVE_STRIDE, data)]
        if actual != expected_effect:
            raise SystemExit(
                f"move-record index {move_index}: +0=0x{actual:02X}, "
                f"esperado 0x{expected_effect:02X}"
            )

    for effect_index, expected_script in SCRIPTS.items():
        actual = read_u32(data, EFFECT_SCRIPT_TABLE_VA + effect_index * 4)
        if actual != expected_script:
            raise SystemExit(
                f"script table index 0x{effect_index:02X}: 0x{actual:08X}, "
                f"esperado 0x{expected_script:08X}"
            )

    # Local byte sequences. Command boundaries are cross-referenced to the
    # pinned upstream macros; this verifier itself checks bytes and pointers.
    expect(
        data, SCRIPTS[0x59],
        "00 a1 f0 7d 1d 08 01 5e 69 1d 08 00 00 02 03 4a",
        "script na entrada 0x59 (0x4A em +15)",
    )
    expect(
        data, SCRIPTS[0x5D],
        "00 02 03 a6 f2 7d 1d 08 09 0a",
        "script na entrada 0x5D (0xA6 em +3)",
    )
    expect(
        data, SCRIPTS[0x75],
        "00 02 1d 01 00 10 00 00 ad 78 1d 08 03 01 b4 78 1d 08 00 00 4a",
        "script na entrada 0x75 (0x4A em +20)",
    )
    expect(
        data, SCRIPTS[0x90],
        "00 a2 f0 7d 1d 08 01 5e 69 1d 08 00 00 02 03 4a",
        "script na entrada 0x90 (0x4A em +15)",
    )
    expect(
        data, SCRIPTS[0xBA],
        "00 01 5e 69 1d 08 00 00 02 03 ee 04 05 06 07 29 00 dc 3f 02 02 00 d9 81 1d 08 36 cc 3d 02 02 09 09 0a 29 03 dc 3f 02 02 02 ec 81 1d 08 10 62 01 12 40 00 4a",
        "script na entrada 0xBA (0x4A em +51)",
    )

    # Check local inline pointer operands in those streams.
    inline_pointers = {
        SCRIPTS[0x59] + 2: 0x081D7DF0,  # after opcode 0xA1
        SCRIPTS[0x59] + 7: 0x081D695E,  # after opcode 0x01
        SCRIPTS[0x5D] + 4: 0x081D7DF2,  # after opcode 0xA6
        SCRIPTS[0x75] + 8: 0x081D78AD,  # branch operand after opcode 0x1D
        SCRIPTS[0x75] + 14: 0x081D78B4, # branch operand after opcode 0x01
        SCRIPTS[0x90] + 2: 0x081D7DF0,  # after opcode 0xA2
        SCRIPTS[0x90] + 7: 0x081D695E,  # after opcode 0x01
        SCRIPTS[0xBA] + 2: 0x081D695E,  # after opcode 0x01
    }
    for va, expected in inline_pointers.items():
        actual = read_u32(data, va)
        if actual != expected:
            raise SystemExit(f"ponteiro inline em 0x{va:08X}: 0x{actual:08X}, esperado 0x{expected:08X}")

    handlers = {0x4A: 0x08023C39, 0xA6: 0x08029DAD}
    for opcode, expected in handlers.items():
        actual = read_u32(data, COMMAND_TABLE_VA + opcode * 4)
        if actual != expected:
            raise SystemExit(
                f"handler local opcode 0x{opcode:02X}: 0x{actual:08X}, "
                f"esperado 0x{expected:08X}"
            )

    # Local callback path: main loop -> runner -> slot 154A0 -> slot 155C8.
    expect(
        data, MAIN_CALLBACK_DISPATCH_VA,
        "06 4c 20 68 00 28 01 d0 e3 f1 3c fb 60 68 00 28 01 d0 e3 f1 37 fb 10 bc 01 bc 00 47",
        "dispatcher principal de callbacks via trampoline",
    )
    if read_u32(data, 0x08000540) != MAIN_CALLBACK_SLOT_VA:
        raise SystemExit("base de callbacks principal divergente")
    expect(
        data, 0x0801085A,
        "0a 4a 0a 49 08 68 10 60 0a 48 08 60",
        "instalação local do runner na callback principal",
    )
    if (
        read_u32(data, 0x08010884) != 0x03004F80
        or read_u32(data, 0x08010888) != MAIN_CALLBACK_SLOT_VA
        or read_u32(data, 0x0801088C) != (CALLBACK_RUNNER_VA | 1)
    ):
        raise SystemExit("ponteiros da instalação do runner divergentes")
    expect(
        data, CALLBACK_RUNNER_VA,
        "30 b5 0f 48 00 68 d1 f1 dd fb 0e 49 00 20 08 70",
        "runner que chama a callback em 0x03004F84",
    )
    if read_u32(data, 0x08012424) != CALLBACK_RUNNER_SLOT_VA:
        raise SystemExit("slot de callback lido pelo runner divergente")
    expect(
        data, 0x08015192,
        "15 4f ba 46 15 48 84 46 15 49 89 46",
        "preparação local do callback 0x080154A0",
    )
    expect(data, 0x080151CC, "62 46 53 46 1a 60", "gravação do callback 0x080154A0")
    if read_u32(data, 0x080151E8) != CALLBACK_RUNNER_SLOT_VA or read_u32(data, 0x080151EC) != (CALLBACK_SETUP_VA | 1):
        raise SystemExit("ponteiros do callback 0x080154A0 divergentes")
    expect(data, 0x080152FA, "0a 49 0a 48 08 60", "segunda gravação do callback 0x080154A0")
    if read_u32(data, 0x08015324) != CALLBACK_RUNNER_SLOT_VA or read_u32(data, 0x08015328) != (CALLBACK_SETUP_VA | 1):
        raise SystemExit("segundo par de ponteiros do callback 0x080154A0 divergente")
    expect(data, 0x08015562, "0f 49 00 20 08 70", "zera temporariamente o índice callback")
    expect(data, 0x08015568, "0e 49 0f 48 00 23 00 78 08 70", "copia byte de 0x02023BDA sobre o índice")
    expect(data, 0x0801557E, "0d 49 0d 48 08 60", "troca o callback para 0x080155C8")
    if (
        read_u32(data, 0x080155A4) != 0x02023BE3
        or read_u32(data, 0x080155A8) != 0x02023BDA
        or read_u32(data, 0x080155B4) != CALLBACK_RUNNER_SLOT_VA
        or read_u32(data, 0x080155B8) != (0x080155C8 | 1)
    ):
        raise SystemExit("ponteiros da transição para o callback 0x080155C8 divergentes")

    # Local writers confirm that the guard byte at 0x02023E8A is stateful.
    for va, sequence, pool_va, label in (
        (0x08016886, "06 49 04 20 08 70", 0x080168A0, "write 4 to guard byte"),
        (0x080169D2, "04 49 06 20 08 70", 0x080169E4, "write 6 to guard byte"),
        (0x08016C7C, "06 49 04 20 08 70", 0x08016C98, "second write 4 to guard byte"),
    ):
        expect(data, va, sequence, label)
        if read_u32(data, pool_va) != 0x02023E8A:
            raise SystemExit(f"literal da {label} diverge")
    expect(data, 0x08015686, "0b 4c", "carregamento do guard byte no primeiro clear")
    expect(data, 0x0801569C, "21 78 7f 20 08 40 20 70", "clear bit 7 do guard byte")
    expect(data, 0x080157A4, "0a 4c", "carregamento do guard byte no segundo clear")
    expect(data, 0x080157BA, "21 78 7f 20 08 40 20 70", "segundo clear bit 7 do guard byte")
    if read_u32(data, 0x080156B4) != 0x02023E8A or read_u32(data, 0x080157D0) != 0x02023E8A:
        raise SystemExit("literais do guard byte nos clears divergentes")
    expect(data, 0x08016374, "10 b5", "entry primário slot 2")
    expect(data, 0x0801687A, "00 2e 06 d0", "ramo condicional antes do write 4")
    expect(data, 0x0801688C, "30 1c f0 bc 02 bc 08 47", "epílogo primário slot 2")
    expect(data, 0x080168A4, "70 b5", "entry primário slot 3")
    expect(data, 0x080169D8, "70 bc 01 bc 00 47", "epílogo primário slot 3")
    expect(data, 0x08016C60, "10 b5", "entry primário slot 8")
    expect(data, 0x08016C82, "10 bc 01 bc 00 47", "epílogo primário slot 8")

    # Adjacent local callback tables select the primary and follow-up handlers.
    expect(
        data, 0x080155C8,
        "70 b5 14 4e 30 78 14 4a 00 28 01 d0 0c 20 10 70",
        "leitura e condicional de inicialização do índice callback",
    )
    expect(
        data, CALLBACK_DISPATCH_VA,
        "11 49 10 78 80 00 40 18 00 68 ce f1 db fa",
        "dispatch primário indireto da tabela callback",
    )
    expect(
        data, 0x08015606,
        "0d 4b 0d 4a 31 78 7f 20 08 40 80 00 80 18 00 68 18 60 20 e0",
        "dispatch secundário via 0x02023E8A e gravação do callback seguinte",
    )
    if (
        read_u32(data, 0x0801561C) != 0x02023E8A
        or read_u32(data, 0x08015620) != 0x02023BE3
        or read_u32(data, 0x0801562C) != PRIMARY_CALLBACK_TABLE_VA
        or read_u32(data, 0x08015640) != SECONDARY_CALLBACK_TABLE_VA
    ):
        raise SystemExit("ponteiros dos índices/bases das tabelas callback divergentes")
    primary_off = offset(
        PRIMARY_CALLBACK_TABLE_VA, PRIMARY_CALLBACK_COUNT_CANDIDATE * 4, data
    )
    primary_callbacks = list(
        struct.unpack_from(f"<{PRIMARY_CALLBACK_COUNT_CANDIDATE}I", data, primary_off)
    )
    secondary_off = offset(
        SECONDARY_CALLBACK_TABLE_VA, SECONDARY_CALLBACK_COUNT_CANDIDATE * 4 + 4, data
    )
    secondary_callbacks = list(
        struct.unpack_from(f"<{SECONDARY_CALLBACK_COUNT_CANDIDATE}I", data, secondary_off)
    )
    rom_end = ROM_BASE + len(data)
    if (
        primary_callbacks[0] != 0x08015CA1
        or primary_callbacks[2] != 0x08016375
        or primary_callbacks[3] != 0x080168A5
        or primary_callbacks[8] != 0x08016C61
        or secondary_callbacks[4] != 0x08015851
        or secondary_callbacks[6] != 0x080158BD
        or not all(ROM_BASE <= (p & ~1) < rom_end for p in primary_callbacks + secondary_callbacks)
    ):
        raise SystemExit("slots ou ponteiros das duas tabelas callback candidatas divergentes")
    next_callback_word = struct.unpack_from(
        "<I", data, secondary_off + SECONDARY_CALLBACK_COUNT_CANDIDATE * 4
    )[0]
    if ROM_BASE <= (next_callback_word & ~1) < rom_end:
        raise SystemExit("word seguinte à tabela callback secundária também parece ponteiro")
    expect(
        data, CALLBACK_ENTRY0_VA, "f0 b5 57 46 4e 46 45 46 e0 b4 82 b0",
        "prólogo do callback slot 0",
    )
    expect(
        data, 0x08016350, "38 bc 98 46 a1 46 aa 46 f0 bc 01 bc 00 47",
        "epílogo do callback slot 0",
    )
    expect(data, TRAMPOLINE_VA, "00 47", "trampoline local BX r0")

    # These short direct branches converge on a basic block, not a function
    # entry. Verify the local instruction halfwords and their decoded targets.
    branch_sites = {
        0x08015FA8: 0xE1C0,
        0x08016158: 0xE0E8,
        0x080161E2: 0xE0A3,
        0x08016272: 0xD05B,
        0x0801628A: 0xD04F,
        0x080162C2: 0xD033,
        0x08016316: 0xD009,
    }
    for va, expected_insn in branch_sites.items():
        insn = read_u16(data, va)
        target = thumb_short_branch_target(va, insn)
        if insn != expected_insn or target != 0x0801632C:
            raise SystemExit(
                f"branch local em 0x{va:08X}: insn=0x{insn:04X}, target={target!r}"
            )

    learnset_hits = scan_learnset_references(data, set(MOVE_EFFECTS))

    print(f"ROM SHA-256: {digest}")
    print("0x4A local em entradas 0x59 (+15), 0x75 (+20), 0x90 (+15) e 0xBA (+51)")
    print("0xA6 local em entrada 0x5D (+3); operand aponta para 0x081D7DF2")
    print("registros candidatos +0: 68→0x59, 176→0x5D, 205/301→0x75, 243→0x90, 280→0xBA")
    print("dispatch local: 0x4A→0x08023C38; 0xA6→0x08029DAC")
    print(
        "rota estática: 0x030030F0→runner 0x080123E4→callback 0x03004F84; "
        "0x08015562 zera 0x02023BE3, mas 0x08015568 copia 0x02023BDA sobre ele"
    )
    print(
        "tabela primária candidata 0x08250038 (14 slots): slot 0→0x08015CA0; "
        "0x080155C8 grava 0x0C se 0x02023E8A != 0; caso contrário mantém o valor copiado"
    )
    print(
        "tabela secundária candidata 0x08250070 (9 slots) é usada no caminho "
        "0x02023BE2 >= 0x02023BCC; 0x02023E8A & 0x7F seleciona o slot"
    )
    print("predicados combinados, semântica e runtime não testados")
    print("bloco 0x0801632C no primário slot 0: 7 branches locais convergem")
    for move_id, occurrences in learnset_hits.items():
        indices = sorted({index for index, _level in occurrences})
        print(f"learnset local: ID numérico {move_id} aparece {len(occurrences)} vez(es), tabela indices {indices}")
    print("Bytes/ponteiros locais conferidos; alinhamento não prova execução em batalha.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
