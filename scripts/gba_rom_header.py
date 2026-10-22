#!/usr/bin/env python3
"""Lê o cabeçalho de uma ROM de GBA e valida o que o GBATEK define (seção 9.2).

Existe por dois motivos:

1. **Validar antes do Ghidra.** O importador (`scripts/ghidra_import_gba.sh`)
   roda este script primeiro para saber, sem depender do Ghidra, se o arquivo
   parece mesmo uma ROM de GBA (logo fixo, byte 0x96, complement checksum).
2. **Cross-check independente.** O script Ghidra (`GbaPrepareProgram.java`)
   reimplementa o mesmo parsing em Java. Comparando os dois JSONs
   (`--compare`) detectamos divergência de implementação (ex.: extensão de
   sinal no `B`, soma do complemento).

Nada aqui lê assets do jogo: são só os 0xC0 bytes públicos do cabeçalho.

Uso
---
    python3 scripts/gba_rom_header.py rom.gba --json
    python3 scripts/gba_rom_header.py rom.gba --compare reports/ghidra/gba_prepare_pre.json
    python3 scripts/gba_rom_header.py --self-test

Códigos de saída:
    0  cabeçalho válido (ou self-test/compare OK)
    1  cabeçalho inválido
    2  erro de uso/IO
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROM_BASE = 0x08000000
HEADER_LENGTH = 0xC0
NINTENDO_LOGO_OFFSET = 0x04
NINTENDO_LOGO_LENGTH = 0x9C  # 156 bytes


def read_int_le(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def arm_branch_target(pc: int, word: int) -> int | None:
    """Alvo de um `B` ARM (opcode 0xEA) ou None se não for B.

    ARM B: cond=1110 (0xE), opcode 1010, imm24 com sinal, alvo = PC + 8 + imm*4.
    """
    if (word >> 24) & 0xFF != 0xEA:
        return None
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return (pc + 8 + (imm << 2)) & 0xFFFFFFFF


def header_complement(data: bytes) -> tuple[int, int]:
    """Retorna (complemento esperado, complemento gravado) para bytes 0xA0..0xBC."""
    total = sum(data[0xA0:0xBD]) & 0xFF
    return (-(total + 0x19)) & 0xFF, data[0xBD] & 0xFF


def ascii_trimmed(data: bytes, offset: int, length: int) -> str:
    chunk = data[offset : offset + length]
    out = []
    for byte in chunk:
        if byte == 0:
            break
        out.append(chr(byte) if 0x20 <= byte < 0x7F else ".")
    return "".join(out).strip()


def nintendo_logo_bytes() -> bytes:
    """Logo fixo da Nintendo tal como o GBATEK documenta (156 bytes)."""
    return bytes(
        [
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
        ]
    )


def parse_header(data: bytes) -> dict:
    """Extrai e valida os campos do cabeçalho. Retorna um dict serializável."""
    if len(data) < HEADER_LENGTH:
        return {"available": False, "reason": f"arquivo menor que 0x{HEADER_LENGTH:X} bytes"}

    expected_complement, stored_complement = header_complement(data)
    entry_word = read_int_le(data, 0)
    target = arm_branch_target(ROM_BASE, entry_word)
    logo_expected = nintendo_logo_bytes()
    logo_actual = data[NINTENDO_LOGO_OFFSET : NINTENDO_LOGO_OFFSET + NINTENDO_LOGO_LENGTH]

    result = {
        "available": True,
        "title": ascii_trimmed(data, 0xA0, 12),
        "game_code": ascii_trimmed(data, 0xAC, 4),
        "maker_code": ascii_trimmed(data, 0xB0, 2),
        "fixed_value_0xB2": f"0x{data[0xB2]:02X}",
        "fixed_value_ok": data[0xB2] == 0x96,
        "main_unit_code": f"0x{data[0xB3]:02X}",
        "device_type": f"0x{data[0xB4]:02X}",
        "software_version": data[0xBC],
        "complement_byte": f"0x{stored_complement:02X}",
        "complement_sum": f"0x{sum(data[0xA0:0xBD]) & 0xFF:02X}",
        "complement_expected": f"0x{expected_complement:02X}",
        "complement_ok": expected_complement == stored_complement,
        "nintendo_logo_ok": logo_actual == logo_expected,
        "entry_branch_word": f"0x{entry_word:08X}",
        "entry_branch_target": None if target is None else f"0x{target:08X}",
        "word_at_0xC0": f"0x{read_int_le(data, 0xC0):08X}"
        if len(data) >= 0xC4
        else None,
    }
    result["is_gba_rom"] = bool(
        result["fixed_value_ok"] and result["complement_ok"] and result["entry_branch_target"]
    )
    return result


def inspect_file(path: Path) -> dict:
    data = path.read_bytes()
    header = parse_header(data)
    info = {
        "path": str(path),
        "size": len(data),
        "size_hex": f"0x{len(data):X}",
        "sha256": hashlib.sha256(data).hexdigest(),
        "base_address": f"0x{ROM_BASE:08X}",
        "header": header,
        "warnings": [],
    }
    size = len(data)
    if size == 0:
        info["warnings"].append("arquivo vazio")
    elif size & (size - 1) != 0:
        info["warnings"].append(
            f"tamanho {size} não é potência de 2 (ROM possivelmente aparada/padded)"
        )
    if size > 0x02000000:
        info["warnings"].append("arquivo maior que 32 MB (fora do espaço de ROM do GBA)")
    if header.get("available") and not header.get("nintendo_logo_ok"):
        info["warnings"].append("logo da Nintendo não confere (ROM hack/trim ou não-GBA)")
    return info


# --- self-test ---------------------------------------------------------------
def _build_fixture_header() -> bytes:
    header = bytearray(HEADER_LENGTH)
    header[0x04 : 0x04 + NINTENDO_LOGO_LENGTH] = nintendo_logo_bytes()
    header[0xA0:0xA0 + 12] = b"POKEMON FIRE"
    header[0xAC:0xB0] = b"BPRE"
    header[0xB0:0xB2] = b"01"
    header[0xB2] = 0x96
    header[0xBC] = 0
    expected, _ = header_complement(bytes(header))
    header[0xBD] = expected
    return bytes(header)


def self_test() -> int:
    failures: list[str] = []

    fixture = _build_fixture_header()
    parsed = parse_header(fixture)
    checks = {
        "title": ("POKEMON FIRE", parsed.get("title")),
        "game_code": ("BPRE", parsed.get("game_code")),
        "maker_code": ("01", parsed.get("maker_code")),
        "complement_sum": ("0x7F", parsed.get("complement_sum")),
        "complement_byte": ("0x68", parsed.get("complement_byte")),
        "complement_ok": (True, parsed.get("complement_ok")),
        "nintendo_logo_ok": (True, parsed.get("nintendo_logo_ok")),
        "fixed_value_ok": (True, parsed.get("fixed_value_ok")),
    }
    for name, (expected, actual) in checks.items():
        if expected != actual:
            failures.append(f"fixture.{name}: esperado {expected!r}, obtido {actual!r}")

    corrupt = bytearray(fixture)
    corrupt[0xBD] = (corrupt[0xBD] + 1) & 0xFF
    if parse_header(bytes(corrupt)).get("complement_ok") is not False:
        failures.append("fixture.complement_ok_corrupt: deveria ser False")

    branch_vectors = [
        (0x08000000, 0xEA00002E, 0x080000C0),
        (0x08000000, 0xEAFFFFFE, 0x08000000),
        (0x08000000, 0xEA000000, 0x08000008),
        (0x08000000, 0xE92D4010, None),
    ]
    for pc, word, expected in branch_vectors:
        actual = arm_branch_target(pc, word)
        if actual != expected:
            failures.append(
                f"branch(0x{word:08X}): esperado {expected!r}, obtido {actual!r}"
            )

    if failures:
        print("[self-test] FALHA")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("[self-test] OK  cabecalho + decodificacao de B ARM conferem com os vetores fixos")
    return 0


# --- comparação com o JSON do Ghidra ----------------------------------------
def compare_with_ghidra(python_info: dict, ghidra_json: Path) -> int:
    try:
        ghidra = json.loads(ghidra_json.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"[compare] não foi possível ler {ghidra_json}: {exc}", file=sys.stderr)
        return 2

    ghidra_header = ghidra.get("header") or {}
    py_header = python_info["header"]
    fields = (
        "title",
        "game_code",
        "maker_code",
        "complement_sum",
        "complement_byte",
        "complement_expected",
        "complement_ok",
        "fixed_value_ok",
        "entry_branch_word",
        "entry_branch_target",
        "word_at_0xC0",
    )
    problems = []
    for field in fields:
        if field not in ghidra_header:
            problems.append(f"{field}: ausente no JSON do Ghidra")
            continue
        if py_header.get(field) != ghidra_header.get(field):
            problems.append(
                f"{field}: python={py_header.get(field)!r} ghidra={ghidra_header.get(field)!r}"
            )

    language = ghidra.get("language_id", "")
    if language and "v4t" not in language.lower():
        problems.append(f"language_id: esperado ARMv4T, obtido {language!r}")

    if problems:
        print("[compare] DIVERGÊNCIA entre Python e Ghidra:")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(f"[compare] OK  Python e Ghidra concordam em {len(fields)} campos do cabeçalho")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lê/valida o cabeçalho de uma ROM de GBA.")
    parser.add_argument("rom", nargs="?", type=Path, help="caminho da ROM (.gba)")
    parser.add_argument("--json", action="store_true", help="imprime JSON completo")
    parser.add_argument("--out", type=Path, help="grava o JSON nesse arquivo")
    parser.add_argument(
        "--compare",
        type=Path,
        metavar="GHIDRA_JSON",
        help="compara com o gba_prepare_pre.json gerado pelo script do Ghidra",
    )
    parser.add_argument("--self-test", action="store_true", help="valida com vetores fixos")
    parser.add_argument(
        "--require-valid",
        action="store_true",
        help="sai 1 se o cabeçalho não passar nas verificações (logo/complemento/entrada)",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.rom is None:
        parser.print_usage(sys.stderr)
        print("erro: informe a ROM ou use --self-test", file=sys.stderr)
        return 2
    if not args.rom.is_file():
        print(f"erro: arquivo não encontrado: {args.rom}", file=sys.stderr)
        return 2

    info = inspect_file(args.rom)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.compare:
        return compare_with_ghidra(info, args.compare)

    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        header = info["header"]
        print(f"arquivo:   {info['path']} ({info['size']} bytes)")
        print(f"sha256:    {info['sha256']}")
        if not header.get("available"):
            print(f"cabeçalho: indisponível ({header.get('reason')})")
        else:
            print(f"título:    {header['title']!r}  código: {header['game_code']!r}  "
                  f"maker: {header['maker_code']!r}  versão: {header['software_version']}")
            print(f"logo:      {'OK' if header['nintendo_logo_ok'] else 'DIVERGENTE'}")
            print(f"complemento: {header['complement_byte']} "
                  f"(esperado {header['complement_expected']}) -> "
                  f"{'OK' if header['complement_ok'] else 'FALHA'}")
            print(f"entrada:   {header['entry_branch_word']} -> {header['entry_branch_target']}")
            print(f"parece ROM de GBA: {'sim' if header['is_gba_rom'] else 'NÃO'}")
        for warning in info["warnings"]:
            print(f"AVISO: {warning}")

    header = info["header"]
    valid = bool(header.get("available")) and bool(header.get("is_gba_rom"))
    if args.require_valid and not valid:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
