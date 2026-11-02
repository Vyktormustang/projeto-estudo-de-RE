#!/usr/bin/env python3
"""Gera o catálogo determinístico de learnsets do motor_v9 a partir do PokéAPI.

Restaura +378 entradas de subida de nível antes omitidas em 51 golpes não-TM
distribuídos em seis famílias mecânicas compartilhadas sobre o motor_v8
(14.627 -> 15.005 linhas, preservando 100% das entradas anteriores e das 229
TMs de Scarlet/Violet já habilitadas em motor_v8).

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
    ROOT / "data/learnsets_motor_v8.csv": "19abc5661267157524b9dcdc9ad769cdf12a20f9f44a3be63f134ae2ec9120f7",
}

# 51 golpes de subida de nível restaurados no motor_v9:
# api_move -> (internal_move, expected_name)
ENABLED_LEVEL_MOVES: dict[int, tuple[int, str]] = {
    # Família A: modificação de tipo, terceiro tipo e eletrificação (50 linhas)
    487: (486, "Soak"),
    513: (512, "Reflect Type"),
    567: (563, "Trick-or-Treat"),
    571: (567, "Forest\u2019s Curse"),
    582: (578, "Electrify"),
    750: (675, "Magic Powder"),
    # Família B: trocas/divisões/inversões e impulsos compostos de atributos (101 linhas)
    367: (367, "Acupressure"),
    379: (379, "Power Trick"),
    384: (384, "Power Swap"),
    385: (385, "Guard Swap"),
    391: (391, "Heart Swap"),
    470: (469, "Guard Split"),
    471: (470, "Power Split"),
    563: (559, "Rototiller"),
    576: (572, "Topsy-Turvy"),
    579: (575, "Flower Shield"),
    599: (595, "Venom Drench"),
    602: (598, "Magnetic Flux"),
    672: (627, "Toxic Thread"),
    674: (629, "Gear Up"),
    683: (638, "Speed Swap"),
    748: (673, "No Retreat"),
    749: (674, "Tar Shot"),
    775: (682, "Clangorous Soul"),
    777: (684, "Decorate"),
    858: (750, "Spicy Extract"),
    868: (760, "Fillet Away"),
    # Família C: regeneração, drenagem por Atk, sacrifício/substituto e purificação (65 linhas)
    361: (361, "Healing Wish"),
    375: (375, "Psycho Shift"),
    392: (392, "Aqua Ring"),
    461: (460, "Lunar Dance"),
    464: (463, "Dark Void"),
    668: (623, "Strength Sap"),
    685: (640, "Purify"),
    816: (710, "Jungle Healing"),
    849: (742, "Lunar Blessing"),
    850: (743, "Take Heart"),
    880: (770, "Shed Tail"),
    # Família D: manipulação de habilidade em batalha (67 linhas)
    380: (380, "Gastro Acid"),
    388: (388, "Worry Seed"),
    494: (493, "Entrainment"),
    867: (759, "Doodle"),
    # Família E: controle de ordem/cópia, foco crítico, sacrifício de HP e Natural Gift (85 linhas)
    363: (363, "Natural Gift"),
    383: (383, "Copycat"),
    495: (494, "After You"),
    511: (510, "Quash"),
    515: (514, "Final Gambit"),
    673: (628, "Laser Focus"),
    # Família F: salas de itens e travas de troca (10 linhas)
    478: (477, "Magic Room"),
    587: (583, "Fairy Lock"),
    753: (678, "Octolock"),
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

    if len(ENABLED_LEVEL_MOVES) != 51:
        raise ValueError(f"Contagem inesperada de golpes habilitados: {len(ENABLED_LEVEL_MOVES)}")
    for api_move, (_mid, exp_name) in ENABLED_LEVEL_MOVES.items():
        if move_names.get(api_move) != exp_name:
            raise ValueError(f"Nome inesperado no PokéAPI para move_id={api_move}: {move_names.get(api_move)!r}")

    levels = list(csv.DictReader((ROOT / "data/learnsets_motor_v8.csv").open(encoding="utf-8")))
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

    if len(added_levels) != 378:
        raise ValueError(f"Quantidade inesperada de entradas de nível adicionadas: {len(added_levels)}")

    merged_levels = levels + added_levels
    merged_levels.sort(key=lambda r: (int(r["species"]), int(r["level"])))
    if len(merged_levels) != 15005:
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
    out = ROOT / "data/learnsets_motor_v9.csv"
    out.write_bytes(lv_csv)
    print(f"{out.relative_to(ROOT)}: {len(lv_csv)} B  sha256={sha256(lv_csv)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
