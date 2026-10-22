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

Uso
---
    python3 scripts/make_synthetic_arm_image.py --out reports/re_tools/synthetic_arm.gba
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
        "--self-test",
        action="store_true",
        help="não escreve nada; valida as codificações e sai 0/1",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="imprime um resumo em JSON (útil para scripts)",
    )
    args = parser.parse_args(argv)

    image = build_image()
    digest = hashlib.sha256(image).hexdigest()

    if args.self_test:
        ok, detail = self_test_with_capstone(image)
        if not ok and detail.startswith("capstone não instalado"):
            ok, detail = self_test_without_capstone(image)
        print(("[self-test] OK  " if ok else "[self-test] FALHA ") + detail)
        return 0 if ok else 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(image)

    summary = {
        "path": str(args.out),
        "base_address": f"0x{BASE_ADDRESS:08X}",
        "size": len(image),
        "sha256": digest,
        "functions": {name: f"0x{addr:08X}" for name, addr in FUNCTIONS.items()},
        "bag_array_literal": "0x020258B8",
        "synthetic": True,
    }
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"imagem:    {args.out} ({len(image)} bytes)")
        print(f"base:      0x{BASE_ADDRESS:08X}")
        print(f"sha256:    {digest}")
        for name, address in FUNCTIONS.items():
            print(f"  {name:<10} 0x{address:08X}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
