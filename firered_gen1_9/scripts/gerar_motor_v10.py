#!/usr/bin/env python3
"""Gera o catálogo determinístico de learnsets do motor_v10 a partir do PokéAPI.

Restaura +3 entradas de subida de nível das 2 mecânicas de consumo ativo de
Berry em batalha — Stuff Cheeks (672 / api 747) e Teatime (677 / api 752) —
sobre o motor_v9 (15.005 -> 15.008 linhas, alcançando 708/729 = 97,1% das
entradas originalmente omitidas e preservando 100% das entradas anteriores e
das 229/229 TMs de Scarlet/Violet).

Não lê nem grava arquivos .gba ou saves pessoais.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POKEAPI_COMMIT = "6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce"
CSV_HASHES = {
    "move_names.csv": "99e23ee38ea53d1473474d463b87651deac3cd4928750f8186feae66da45c147",
    "pokemon_moves.csv": "22a807cef26891eeac0d0c900bd363e66baf421f7ee795bc7bc3e718f23b939e",
}
PRIOR_HASHES = {
    ROOT / "data/learnsets_motor_v9.csv": "de3f00717240a20c513899422789082d20e7e56f911671677c92abbf26ccfeae",
}

# 2 golpes não-TM de consumo ativo de Berry restaurados no motor_v10:
# api_move -> (internal_move, expected_name)
ENABLED_LEVEL_MOVES: dict[int, tuple[int, str]] = {
    747: (672, "Stuff Cheeks"),
    752: (677, "Teatime"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(csv_dir: Path) -> bytes:
    for path, expected in PRIOR_HASHES.items():
        if sha256(path.read_bytes()) != expected:
            raise ValueError(f"Entrada local divergente: {path.name}")
    for name, expected in CSV_HASHES.items():
        if sha256((csv_dir / name).read_bytes()) != expected:
            raise ValueError(f"CSV do PokéAPI fora do commit esperado ({POKEAPI_COMMIT}): {name}")

    move_names: dict[int, str] = {}
    with open(csv_dir / "move_names.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["local_language_id"] == "9":
                move_names[int(row["move_id"])] = row["name"]

    if len(ENABLED_LEVEL_MOVES) != 2:
        raise ValueError(f"Contagem inesperada de golpes habilitados: {len(ENABLED_LEVEL_MOVES)}")
    for api_move, (_mid, exp_name) in ENABLED_LEVEL_MOVES.items():
        if move_names.get(api_move) != exp_name:
            raise ValueError(f"Nome inesperado no PokéAPI para move_id={api_move}: {move_names.get(api_move)!r}")

    levels = list(csv.DictReader((ROOT / "data/learnsets_motor_v9.csv").open(encoding="utf-8")))
    sources: dict[int, collections.Counter[int]] = collections.defaultdict(collections.Counter)
    for row in levels:
        sources[int(row["species"])][int(row["source_group"])] += 1
    groups = {sid: c.most_common(1)[0][0] for sid, c in sources.items()}
    if len(groups) != 1025:
        raise ValueError("Espécies sem grupo-fonte completo")

    existing_keys = {
        (int(r["species"]), int(r["level"]), int(r["internal_move"]), int(r["api_move"]))
        for r in levels
    }
    added_levels: list[dict[str, str]] = []

    with open(csv_dir / "pokemon_moves.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sid = int(row["pokemon_id"])
            if not 1 <= sid <= 1025 or int(row["version_group_id"]) != groups[sid]:
                continue
            if row["pokemon_move_method_id"] != "1":
                continue
            api_move = int(row["move_id"])
            if api_move not in ENABLED_LEVEL_MOVES:
                continue
            mid, exp_name = ENABLED_LEVEL_MOVES[api_move]
            lv = int(row["level"])
            key = (sid, lv, mid, api_move)
            if key not in existing_keys:
                existing_keys.add(key)
                added_levels.append({
                    "species": str(sid),
                    "level": str(lv),
                    "internal_move": str(mid),
                    "api_move": str(api_move),
                    "name": exp_name,
                    "source_group": str(groups[sid]),
                    "fallback": "",
                })

    if len(added_levels) != 3:
        raise ValueError(f"Quantidade inesperada de entradas de nível adicionadas: {len(added_levels)}")

    merged_levels = levels + added_levels
    merged_levels.sort(key=lambda r: (int(r["species"]), int(r["level"])))
    if len(merged_levels) != 15008:
        raise ValueError(f"Total de learnsets inesperado: {len(merged_levels)}")

    lv_buf = io.StringIO()
    lv_writer = csv.DictWriter(lv_buf, fieldnames=levels[0].keys(), lineterminator="\n")
    lv_writer.writeheader()
    lv_writer.writerows(merged_levels)
    return lv_buf.getvalue().encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pokeapi-csv", type=Path, required=True)
    args = parser.parse_args()
    lv_csv = generate(args.pokeapi_csv)
    out = ROOT / "data/learnsets_motor_v10.csv"
    out.write_bytes(lv_csv)
    print(f"{out.relative_to(ROOT)}: {len(lv_csv)} B  sha256={sha256(lv_csv)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
