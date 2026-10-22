#!/usr/bin/env python3
"""Gera uma imagem ARM32 sintética (GBA-like) para o smoke test de REA + Ghidra.

Por que isso existe
-------------------
O repositório NÃO inclui a ROM comercial (regra do projeto). Para validar a
ferramenta sem depender do jogo, este script monta à mão um blob ARM32 pequeno,
posicionado em ``0x08000000`` (a mesma base da ROM de GBA), com três rotinas
ligadas por ``bl`` e uma referência literal ao array da mochila em
``0x020258B8`` (endereço documentado no README deste projeto).

A imagem é 100% sintética: nenhum byte do jogo é usado.

Layout gerado (little-endian, base 0x08000000)
----------------------------------------------
    0x08000000  entry:      push {r4, lr}; mov r0,#1; mov r1,#2; mov r2,#99
                            bl sub_add ; bl sub_bag ; pop {r4, pc}
    0x08000024  sub_add:    add r0, r0, r1 ; bx lr
    0x0800002C  sub_bag:    ldr r0, [pc, #4] ; str r2, [r0] ; bx lr
    0x08000038  .word       0x020258B8          ; array da mochila (EWRAM)
    0x0800003C  padding     zeros até 0x100 bytes

Variante --gba-rom
------------------
Com ``--gba-rom`` o script gera uma ROM de GBA **falsa mas estruturalmente
válida** (32 KB): logo da Nintendo, título/código, `0x96` no offset 0xB2 e
complement checksum corretos, mais:
   0x0000  b 0x080000C0
   0x00C0  ldr r0, [pc, #4] ; bx r0 ; literal 0x08000101  (ponteiro Thumb)
   0x0100  Thumb: push {lr} ; movs r0, #1 ; pop {pc}
   0x0200  ARM: push {r4,lr} ; ldr r0,=0x020258B8 ; str r2,[r0] ; bx lr
Ela existe para exercitar o importador do Ghidra (cabeçalho + seeds ARM/Thumb)
sem tocar na ROM comercial. Não é jogável e não contém asset nenhum.

Uso
---
    python3 scripts/make_synthetic_arm_image.py --out reports/re_tools/synthetic_arm.gba
    python3 scripts/make_synthetic_arm_image.py --gba-rom --out reports/re_tools/synthetic_gba.gba
    python3 scripts/make_synthetic_arm_image.py --self-test

O ``--self-test`` confere as codificações com o Capstone (se instalado) e sai
com código != 0 se qualquer instrução não bater com o esperado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

BASE_ADDRESS = 0x08000000
IMAGE_SIZE = 0x100
GBA_ROM_SIZE = 0x8000  # 32 KB, potência de 2

# (endereço, palavra ARM) na ordem em que aparecem na imagem
WORDS: list[tuple[int, int]] = [
    (0x08000000, 0xE92D4010),  # push {r4, lr}
    (0x08000004, 0xE3A00001),  # mov  r0, #1
    (0x08000008, 0xE3A01002),  # mov  r1, #2
    (0x0800000C, 0xE3A02063),  # mov  r2, #99
    (0x08000010, 0xEB000003),  # bl   sub_add  (0x08000024)
    (0x08000014, 0xEB000004),  # bl   sub_bag  (0x0800002C)
    (0x08000018, 0xE8BD8010),  # pop  {r4, pc}
    (0x0800001C, 0xE1A00000),  # nop  (alinhamento)
    (0x08000020, 0xE1A00000),  # nop  (alinhamento)
    (0x08000024, 0xE0800001),  # sub_add: add r0, r0, r1
    (0x08000028, 0xE12FFF1E),  #          bx  lr
    (0x0800002C, 0xE59F0004),  # sub_bag: ldr r0, [pc, #4]  -> 0x08000038
    (0x08000030, 0xE5802000),  #          str r2, [r0]
    (0x08000034, 0xE12FFF1E),  #          bx  lr
    (0x08000038, 0x020258B8),  # .word 0x020258B8 (mochila, EWRAM)
]

# Mnemônicos aceitos por palavra (na ordem de WORDS). O Capstone 5 decodifica
# o NOP clássico (0xE1A00000) como "mov r0, r0" e o literal 0x020258B8 como
# "andeq"; ambos são aceitos para não depender de aliases da versão.
EXPECTED_MNEMONICS: list[tuple[str, ...]] = [
    ("push",),
    ("mov",),
    ("mov",),
    ("mov",),
    ("bl",),
    ("bl",),
    ("pop",),
    ("mov", "nop"),
    ("mov", "nop"),
    ("add",),
    ("bx",),
    ("ldr",),
    ("str",),
    ("bx",),
    ("andeq", "and"),
]

FUNCTIONS = {
    "entry": 0x08000000,
    "sub_add": 0x08000024,
    "sub_bag": 0x0800002C,
}

# --- ROM de GBA sintética (--gba-rom) ---------------------------------------
NINTENDO_LOGO = bytes([
    0x24, 0xFF, 0xAE, 0x51, 0x69, 0x9A, 0xA2, 0x21, 0x3D, 0x84, 0x82, 0x0A,
    0x84, 0xE4, 0x09, 0xAD, 0x11, 0x24, 0x8B, 0x98, 0xC0, 0x81, 0x7F, 0x21,
    0xA3, 0x52, 0xBE, 0x19, 0x93, 0x09, 0xCE, 0x20, 0x10, 0x46, 0x4A, 0x4A,
    0xF8, 0x27, 0x31, 0xEC, 0x58, 0xC7, 0xE8, 0x33, 0x82, 0xE3, 0xCE, 0xBF,
    0x85, 0xF4, 0xDF, 0x94, 0xCE, 0x4B, 0x09, 0xC1, 0x94, 0x56, 0x8A, 0xC0,
    0x13, 0x72, 0xA7, 0xFC, 0x9F, 0x84, 0x4D, 0x73, 0xA3, 0xCA, 0x9A, 0x61,
    0x58, 0x97, 0xA3, 0x27, 0xFC, 0x03, 0x98, 0x76, 0x23, 0x1D, 0xC7, 0x61,
    0x03, 0x04, 0xAE, 0x56, 0xBF, 0x38, 0x84, 0x00, 0x40, 0xA7, 0x0E, 0xFD,
    0xFF, 0x52, 0xFE, 0x03, 0x6F, 0x95, 0x30, 0xF1, 0x97, 0xFB, 0xC0, 0x85,
    0x60, 0xD6, 0x80, 0x25, 0xA9, 0x63, 0xBE, 0x03, 0x01, 0x4E, 0x38, 0xE2,
    0xF9, 0xA2, 0x34, 0xFF, 0xBB, 0x3E, 0x03, 0x44, 0x78, 0x00, 0x90, 0xCB,
    0x88, 0x11, 0x3A, 0x94, 0x65, 0xC0, 0x7C, 0x63, 0x87, 0xF0, 0x3C, 0xAF,
    0xD6, 0x25, 0xE4, 0x8B, 0x38, 0x0A, 0xAC, 0x72, 0x21, 0xD4, 0xF8, 0x07,
])

GBA_ROM_WORDS: list[tuple[int, int]] = [
    (0x08000000, 0xEA00002E),  # b   0x080000C0
    (0x080000C0, 0xE59F0004),  # ldr r0, [pc, #4]
    (0x080000C4, 0xE12FFF10),  # bx  r0
    (0x080000C8, 0xE1A00000),  # nop (alinhamento do literal)
    (0x080000CC, 0x08000101),  # .word 0x08000101 -> Thumb @ 0x08000100
    (0x08000200, 0xE92D4010),  # push {r4, lr}
    (0x08000204, 0xE59F0004),  # ldr  r0, [pc, #4]  -> literal @ 0x08000210
    (0x08000208, 0xE3A02063),  # mov  r2, #99
    (0x0800020C, 0xE5802000),  # str  r2, [r0]
    (0x08000210, 0x020258B8),  # .word 0x020258B8 (mochila)
    (0x08000214, 0xE12FFF1E),  # bx   lr
]

GBA_ROM_THUMB_BYTES: dict[int, bytes] = {
    # push {lr} ; movs r0, #1 ; pop {pc}
    0x08000100: bytes([0x00, 0xB5, 0x01, 0x20, 0x00, 0xBD]),
}


def _gba_header_checksum(header: bytes) -> int:
    """Complemento GBATEK: -(0x19 + sum(0xA0..0xBC)) & 0xFF."""
    return (-(sum(header[0xA0:0xBD]) + 0x19)) & 0xFF


def build_gba_rom() -> bytes:
    """Monta a ROM de GBA sintética de 32 KB."""
    rom = bytearray(GBA_ROM_SIZE)
    rom[0x04 : 0x04 + len(NINTENDO_LOGO)] = NINTENDO_LOGO
    rom[0xA0:0xA0 + 12] = b"SYNTHETIC 1 "
    rom[0xAC:0xB0] = b"TSTE"
    rom[0xB0:0xB2] = b"00"
    rom[0xB2] = 0x96
    rom[0xBC] = 0x00
    rom[0xBD] = _gba_header_checksum(bytes(rom))
    for address, word in GBA_ROM_WORDS:
        struct.pack_into("<I", rom, address - BASE_ADDRESS, word)
    for address, blob in GBA_ROM_THUMB_BYTES.items():
        offset = address - BASE_ADDRESS
        rom[offset : offset + len(blob)] = blob
    return bytes(rom)


def self_test_gba_rom(rom: bytes) -> tuple[bool, str]:
    """Valida a ROM sintética com a mesma lógica do leitor de cabeçalho."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from gba_rom_header import parse_header  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        return False, f"não foi possível importar gba_rom_header: {exc}"

    header = parse_header(rom)
    problems = []
    for field, expected in (
        ("game_code", "TSTE"),
        ("complement_ok", True),
        ("nintendo_logo_ok", True),
        ("fixed_value_ok", True),
        ("entry_branch_target", "0x080000C0"),
    ):
        if header.get(field) != expected:
            problems.append(f"cabeçalho.{field}: esperado {expected!r}, obtido {header.get(field)!r}")

    word = struct.unpack_from("<I", rom, 0xCC)[0]  # offset de arquivo (base 0x08000000)
    if word != 0x08000101:
        problems.append(f"literal Thumb em 0x080000CC: 0x{word:08X} != 0x08000101")

    if problems:
        return False, "; ".join(problems)
    return True, "ROM sintética: cabeçalho válido + ponteiro Thumb em 0x080000CC"


def build_image() -> bytes:
    """Monta os bytes da imagem (0x100 bytes, base 0x08000000)."""
    image = bytearray(b"\x00" * IMAGE_SIZE)
    for address, word in WORDS:
        offset = address - BASE_ADDRESS
        struct.pack_into("<I", image, offset, word)
    return bytes(image)


def self_test_with_capstone(image: bytes) -> tuple[bool, str]:
    """Decodifica a imagem com Capstone e compara com o esperado."""
    try:
        import capstone  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 - capstone é opcional
        return False, "capstone não instalado (pip install capstone)"

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md.detail = True
    decoded = list(md.disasm(image[: 4 * len(WORDS)], BASE_ADDRESS))
    if len(decoded) != len(WORDS):
        return False, f"esperava {len(WORDS)} instruções, decodifiquei {len(decoded)}"

    problems: list[str] = []
    for index, (insn, (address, word)) in enumerate(zip(decoded, WORDS)):
        expected = EXPECTED_MNEMONICS[index]
        if insn.mnemonic not in expected:
            problems.append(
                f"0x{address:08X}: mnemônico {insn.mnemonic!r} não está em {expected!r} "
                f"(palavra 0x{word:08X})"
            )
        if insn.address != address:
            problems.append(f"endereço decodificado 0x{insn.address:08X} != 0x{address:08X}")

    # Confere os alvos dos BL (sub_add em 0x08000024 e sub_bag em 0x0800002C)
    bl_targets = [insn.op_str for insn in decoded if insn.mnemonic == "bl"]
    expected_targets = ["#0x8000024", "#0x800002c"]
    if [t.lower() for t in bl_targets] != expected_targets:
        problems.append(f"alvos de bl {bl_targets} != {expected_targets}")

    if problems:
        return False, "; ".join(problems)
    return True, f"capstone: {len(decoded)} instruções conferem (mnemônicos + alvos de bl)"


def self_test_without_capstone(image: bytes) -> tuple[bool, str]:
    """Validação mínima sem Capstone: bytes esperados palavra a palavra."""
    for address, word in WORDS:
        offset = address - BASE_ADDRESS
        got = struct.unpack_from("<I", image, offset)[0]
        if got != word:
            return False, f"0x{address:08X}: 0x{got:08X} != 0x{word:08X}"
    return True, "sem capstone: palavras conferem byte a byte"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera a imagem ARM32 sintética usada no smoke test REA + Ghidra.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/re_tools/synthetic_arm.gba"),
        help="arquivo de saída (padrão: reports/re_tools/synthetic_arm.gba)",
    )
    parser.add_argument(
        "--gba-rom",
        action="store_true",
        help="gera uma ROM de GBA sintética (32 KB, cabeçalho válido) em vez do blob ARM",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="não escreve nada; valida as codificações (blob ARM + ROM GBA) e sai 0/1",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="imprime um resumo em JSON (útil para scripts)",
    )
    args = parser.parse_args(argv)

    if args.gba_rom:
        image = build_gba_rom()
        kind = "gba-rom"
    else:
        image = build_image()
        kind = "arm-blob"
    digest = hashlib.sha256(image).hexdigest()

    if args.self_test:
        failures = 0
        ok, detail = self_test_with_capstone(build_image())
        if not ok and detail.startswith("capstone não instalado"):
            ok, detail = self_test_without_capstone(build_image())
        print(("[self-test] OK  " if ok else "[self-test] FALHA ") + detail)
        failures += 0 if ok else 1

        ok_rom, detail_rom = self_test_gba_rom(build_gba_rom())
        print(("[self-test] OK  " if ok_rom else "[self-test] FALHA ") + detail_rom)
        failures += 0 if ok_rom else 1
        return 0 if failures == 0 else 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(image)

    summary = {
        "path": str(args.out),
        "kind": kind,
        "base_address": f"0x{BASE_ADDRESS:08X}",
        "size": len(image),
        "sha256": digest,
        "synthetic": True,
    }
    if args.gba_rom:
        summary["game_code"] = "TSTE"
        summary["thumb_pointer"] = "0x08000101"
        summary["arm_function"] = "0x08000200 (usa 0x020258B8)"
    else:
        summary["functions"] = {name: f"0x{addr:08X}" for name, addr in FUNCTIONS.items()}
        summary["bag_array_literal"] = "0x020258B8"
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"imagem:    {args.out} ({len(image)} bytes, {kind})")
        print(f"base:      0x{BASE_ADDRESS:08X}")
        print(f"sha256:    {digest}")
        if args.gba_rom:
            print("  header   SYNTHETIC 1 / TSTE (válido)")
            print("  entry    b 0x080000C0 -> ldr -> Thumb 0x08000100")
            print("  func ARM 0x08000200 (usa 0x020258B8)")
        else:
            for name, address in FUNCTIONS.items():
                print(f"  {name:<10} 0x{address:08X}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
