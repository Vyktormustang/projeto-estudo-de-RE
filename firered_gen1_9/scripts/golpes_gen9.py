#!/usr/bin/env python3
"""Atualiza golpes por nível numa nova cópia da ROM específica deste projeto.

Não inclui ou obtém ROMs/saves e não altera a entrada. Exige a variante com
selvagens, treino EV e fixos comuns removidos identificada pelo SHA-256. Os
IDs de golpes passam a ser armazenados em 16 bits, sem mudar o formato do save.
Os TMs/HMs e golpes com efeitos inexistentes NÃO são atualizados por este patch.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import os
import struct
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import gerar_catalogo_golpes as catalog  # noqa: E402
from scripts.treino_ev import write_new_file  # noqa: E402

BASE_SHA256 = "c563d43a8f15976314ad5fb271ad44a83cdf3143749389311f261ffd506a466b"
OUTPUT_SHA256 = "412bcd89214d4126d92f6c2256a56227c6f30fa138e0b262ef287f5b12b3997b"
PAYLOAD_SHA256 = "ba1a62f59a259e23441871da058728c3a7563e60f8c849c0ff47aa60b06d73af"
CATALOG_SHA256 = "ee0d43b87f0146c1702068b03c437371052469e1438511c074d32d336870b1cf"
PAYLOAD = ROOT / "patches/golpes_gen9/payload.bin"
CATALOG = ROOT / "data/learnsets_gen1_9.csv"
ROM_START = 0x08000000
ROM_SIZE = 0x1000000
CODE = 0xE03000
CODE_END = 0xE04000
TABLE = 0xF50000
LISTS = 0xF51010
FREE_END = 0xF5E000
TERMINATOR = struct.pack("<HB", 0xffff, 0xff)
# (offset, prólogo/trecho esperado, offset do vetor, registrador do veneer)
HOOKS = (
    (0x109718, "f0 b5 c6 46 0b 21 00 22", 0x00, 3),
    (0x109790, "f0 b5 c6 46 00 22 0d 06", 0x08, 3),
    (0x10E808, "f0 b5 ce 46 47 46 80 b5", 0x10, 3),
    (0x10E8CC, "0b 4b 00 04 80 0b 30 b5", 0x18, 3),
    (0x10E904, "f0 b5 47 46 ce 46 80 b5", 0x20, 3),
    (0x0A0C70, "21 7c 68 f0 8d fd 80 46", 0x28, 3),
    (0x0A1354, "48 46 21 7c 68 f0 1a fa", 0x30, 3),
    (0x0CF7F4, "41 44 74 f0 cf fb 38 68", 0x38, 3),
    (0x1148CC, "c9 18 77 30 2f f0 62 fb", 0x40, 2),
    (0x114A64, "84 30 c9 18 2f f0 96 fa", 0x48, 2),
    (0x055C94, "c9 18 ee f0 7f f9 5d e7", 0x50, 2),
)
# Dados de batalha, incluindo efeitos e animações, permanecem como na ROM de
# entrada. Não se deve confundir a presença do nome com mecânica Gen 9 fiel.

class PatchError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_inputs(rom: bytes, payload: bytes, cat: bytes) -> None:
    if len(rom) != ROM_SIZE or digest(rom) != BASE_SHA256 or rom[0xAC:0xB0] != b"BPRE":
        raise PatchError("ROM incompatível: use a variante anterior exata; a entrada não foi alterada.")
    if digest(payload) != PAYLOAD_SHA256 or not 0 < len(payload) <= CODE_END - CODE:
        raise PatchError("Payload de código não corresponde à versão validada.")
    if digest(cat) != CATALOG_SHA256:
        raise PatchError("Catálogo ausente, alterado ou incompatível.")
    regions = ((CODE, CODE_END), (TABLE, FREE_END))
    for lo, hi in regions:
        if rom[lo:hi] != b"\xff" * (hi - lo):
            raise PatchError("Uma região reservada não está livre.")
    for i, (value,) in enumerate(struct.iter_unpack("<I", rom)):
        if any(ROM_START + lo <= value < ROM_START + hi for lo, hi in regions):
            raise PatchError(f"Referência alinhada à área livre em {i * 4:#x}.")
    for pos, original, _, _ in HOOKS:
        if rom[pos:pos + 8] != bytes.fromhex(original):
            raise PatchError(f"Trecho inesperado em {pos:#x}.")


def read_catalog(data: bytes, rom: bytes) -> dict[int, list[tuple[int, int]]]:
    import io
    rows = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
    lists = {i: [] for i in range(1, 1026)}
    seen = set()
    for row in rows:
        try:
            sid, level, mid = int(row["species"]), int(row["level"]), int(row["internal_move"])
            api_id, source = int(row["api_move"]), int(row["source_group"])
        except (ValueError, KeyError) as exc:
            raise PatchError("Linha inválida no catálogo.") from exc
        if sid not in lists or not 0 <= level <= 100 or not 1 <= mid < catalog.NAMES_COUNT:
            raise PatchError(f"Espécie, nível ou golpe fora da faixa: {sid}/{level}/{mid}.")
        if source not in catalog.SOURCES or catalog.usable(rom, mid):
            raise PatchError(f"Golpe não verificável ou sem efeito seguro: {mid}.")
        expected_name = catalog.normalize(row["name"])
        internal_name = catalog.normalize(catalog.move_name(rom, mid))
        if api_id not in catalog.ALIASES and internal_name != expected_name:
            raise PatchError(f"Nome mapeado incorretamente para o golpe {mid}.")
        if api_id in catalog.ALIASES and catalog.ALIASES[api_id] != mid:
            raise PatchError(f"Alias inesperado para golpe {api_id}.")
        if (sid, level, mid) in seen:
            raise PatchError("Golpe duplicado no mesmo nível.")
        seen.add((sid, level, mid))
        if lists[sid] and level < lists[sid][-1][0]:
            raise PatchError(f"Níveis fora de ordem: espécie {sid}.")
        lists[sid].append((level, mid))
    if sum(map(len, lists.values())) != 14018:
        raise PatchError("Número inesperado de movimentos.")
    for sid, entries in lists.items():
        if not entries or len(entries) > 50 or not any(lv <= 1 for lv, _ in entries):
            raise PatchError(f"Lista inicial ausente ou longa demais: espécie {sid}.")
    return lists


def build_tables(lists: dict[int, list[tuple[int, int]]]) -> bytes:
    """Tabela de 1.026 ponteiros mais listas de 3 bytes; nenhum dado de ROM."""
    table_size = LISTS - TABLE
    out = bytearray(table_size)
    out.extend(TERMINATOR)  # espécie 0: lista vazia
    struct.pack_into("<I", out, 0, ROM_START + LISTS)
    for sid in range(1, 1026):
        struct.pack_into("<I", out, 4 * sid, ROM_START + TABLE + len(out))
        for level, mid in lists[sid]:
            out.extend(struct.pack("<HB", mid, level))
        out.extend(TERMINATOR)
    if TABLE + len(out) > FREE_END:
        raise PatchError("Tabelas excederam o espaço reservado.")
    return bytes(out)


def hook(target_offset: int, reg: int) -> bytes:
    if reg == 3:
        return bytes.fromhex("00 4b 18 47") + struct.pack("<I", ROM_START + CODE + target_offset + 1)
    if reg == 2:
        return bytes.fromhex("00 4a 10 47") + struct.pack("<I", ROM_START + CODE + target_offset + 1)
    raise PatchError("Registrador de hook inválido.")


def make_plan(rom: bytes, payload: bytes, cat: bytes) -> list[tuple[int, bytes]]:
    validate_inputs(rom, payload, cat)
    lists = read_catalog(cat, rom)
    plan = [(CODE, payload), (TABLE, build_tables(lists))]
    plan.extend((pos, hook(target, reg)) for pos, _old, target, reg in HOOKS)
    plan.sort()
    for (start, data), (next_start, _) in zip(plan, plan[1:]):
        if start + len(data) > next_start:
            raise PatchError("Áreas do patch se sobrepõem.")
    return plan


def apply_patch(rom: bytes, payload: bytes, cat: bytes) -> bytes:
    plan = make_plan(rom, payload, cat)
    out = bytearray(rom)
    for start, data in plan:
        out[start:start + len(data)] = data
    verify_output(rom, bytes(out), plan)
    return bytes(out)


def verify_output(source: bytes, result: bytes, plan: list[tuple[int, bytes]]) -> None:
    if len(result) != len(source):
        raise PatchError("Tamanho de ROM alterado.")
    last = 0
    for start, data in sorted(plan):
        if source[last:start] != result[last:start] or result[start:start + len(data)] != data:
            raise PatchError(f"Diferença inesperada perto de {start:#x}.")
        last = start + len(data)
    if result[last:] != source[last:]:
        raise PatchError("Diferença inesperada após o último trecho.")
    if OUTPUT_SHA256 and digest(result) != OUTPUT_SHA256:
        raise PatchError("O hash de saída não confere com a build verificada.")


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom", type=Path)
    p.add_argument("--saida", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_golpes_gen9.py")
        return 0 if suite.countTestCases() and unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if not args.rom or not args.saida:
        p.error("informe --rom e --saida, ou use --self-test")
    try:
        if args.rom.resolve() == args.saida.resolve() or args.saida.exists():
            raise PatchError("A saída não pode ser a entrada nem um arquivo existente.")
        source = args.rom.read_bytes()
        result = apply_patch(source, PAYLOAD.read_bytes(), CATALOG.read_bytes())
        write_new_file(args.rom, args.saida, result)
        print(f"Entrada preservada: {digest(source)}")
        print(f"Nova ROM: {args.saida} | SHA-256 {digest(result)}")
        print("TM/HM não foram atualizados; veja a documentação para limites.")
        return 0
    except (OSError, PatchError, ValueError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
