#!/usr/bin/env python3
"""Gera um catálogo pequeno de aprendizados a partir da PokéAPI e ROM pessoal.

Não inclui nem baixa qualquer ROM. A referência de dados é a PokéAPI no commit
6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce (licença em data/POKEAPI_LICENSE.txt).
Este gerador não aplica patches; explica quais golpes ficaram de fora por serem
placeholders perigosos ou ausentes. Os CSVs gerados são inspecionáveis.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA256 = "c563d43a8f15976314ad5fb271ad44a83cdf3143749389311f261ffd506a466b"
POKEAPI_COMMIT = "6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce"
MOVE_NAMES = 0x235930
MOVE_DATA = 0x696F70
NAMES_COUNT = 797
NAME_STRIDE = 17
MOVE_STRIDE = 12
# Scarlet/Violet; Sword/Shield para não disponíveis ali; depois BDSP e USUM.
# BDSP tem listas de Gen 4 reequilibradas; preferimos Sw/Sh quando ambos existem.
SOURCES = (25, 20, 23, 18)
ALIASES = {11: 11, 136: 136}  # Vise Grip -> VICEGRIP; High Jump Kick -> HI JUMP KICK.
CATALOG = ROOT / "data/learnsets_gen1_9.csv"
OMITTED = ROOT / "docs/golpes_por_nivel_nao_incluidos.csv"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize(name):
    name = unicodedata.normalize("NFKD", name).lower()
    return "".join(c for c in name if c.isascii() and c.isalnum())


def move_name(rom, index):
    raw = rom[MOVE_NAMES + NAME_STRIDE * index:MOVE_NAMES + NAME_STRIDE * (index + 1)].split(b"\xff", 1)[0]
    chars = []
    for value in raw:
        if 0xBB <= value <= 0xD4:
            chars.append(chr(value - 0xBB + ord("A")))
        elif 0xA1 <= value <= 0xAA:
            chars.append(chr(value - 0xA1 + ord("0")))
        else:
            chars.append({0x00: " ", 0xAE: "-", 0xB4: "'"}.get(value, " "))
    return "".join(chars).strip()


def usable(rom, index):
    if not (1 <= index < NAMES_COUNT):
        return "ausente"
    effect, power, _type, _accuracy, pp = rom[MOVE_DATA + index * MOVE_STRIDE:MOVE_DATA + index * MOVE_STRIDE + 5]
    if pp == 0 or pp > 64 or effect > 213:
        return "dados_invalidos"
    # Splash é intencionalmente sem efeito; outros EFFECT_SPLASH encontrados
    # nos dados de golpes modernos são placeholders da ROM de origem.
    if effect == 85 and index != 150:
        return "efeito_nao_implementado"
    # Golpes dinâmicos modernos gravados como EFFECT_HIT + poder 1 causariam
    # dano mínimo em vez de seu efeito; não tratar como implementados.
    if effect == 0 and power <= 1:
        return "poder_dinamico_nao_implementado"
    return ""


def build(rom, directory):
    if len(rom) != 0x1000000 or hashlib.sha256(rom).hexdigest() != ROM_SHA256:
        raise ValueError("A ROM não é a variante de entrada reconhecida.")
    names = {}
    for i in range(1, NAMES_COUNT):
        key = normalize(move_name(rom, i))
        if not key or key in names:
            raise ValueError(f"Nome interno de golpe vazio ou duplicado: {i}")
        names[key] = i
    english = {int(x["move_id"]): x["name"] for x in read_csv(directory / "move_names.csv")
               if x["local_language_id"] == "9"}
    by_species = defaultdict(lambda: defaultdict(list))
    for row in read_csv(directory / "pokemon_moves.csv"):
        sid, group = int(row["pokemon_id"]), int(row["version_group_id"])
        if 1 <= sid <= 1025 and group in SOURCES and row["pokemon_move_method_id"] == "1":
            by_species[sid][group].append(row)
    selected, omitted = [], []
    for sid in range(1, 1026):
        source = next((group for group in SOURCES if by_species[sid][group]), None)
        if source is None:
            raise ValueError(f"Não há dados de referência para a espécie {sid}")
        # A PokéAPI não registra golpe no nível 1 do Crabrawler em Scarlet/Violet.
        # Sem um fallback, um recém-nascido poderia começar sem ataque algum.
        rows = list(by_species[sid][source])
        if not any(int(x["level"]) <= 1 for x in rows):
            fallback = next((x for group in SOURCES for x in by_species[sid][group]
                             if int(x["level"]) == 1 and int(x["move_id"]) in english
                             and (idx := ALIASES.get(int(x["move_id"]), names.get(normalize(english[int(x["move_id"])]))))
                             and not usable(rom, idx)), None)
            if fallback is None:
                raise ValueError(f"Nenhum golpe inicial seguro para a espécie {sid}")
            rows.append(dict(fallback, fallback="inicial"))
        # Mantém a ordem dos registros quando a PokéAPI não informa 'order'.
        rows.sort(key=lambda x: (int(x["level"]), int(x["order"]) if x["order"] else 999))
        before = len(selected)
        for row in rows:
            api_id, level = int(row["move_id"]), int(row["level"])
            name = english[api_id]
            internal = ALIASES.get(api_id, names.get(normalize(name)))
            reason = "ausente" if internal is None else usable(rom, internal)
            info = {
                "species": sid, "level": level, "internal_move": internal or "",
                "api_move": api_id, "name": name,
                "source_group": int(row["version_group_id"]),
            }
            if reason:
                omitted.append(dict(info, reason=reason))
            else:
                selected.append(dict(info, fallback=row.get("fallback", "")))
        own = selected[before:]
        if not own or not any(int(r["level"]) <= 1 for r in own):
            raise ValueError(f"Espécie {sid} ficou sem golpe no início")
        if len(own) > 50:
            raise ValueError(f"Espécie {sid} ultrapassa o limite de 50 movimentos")
    return selected, omitted


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--pokeapi-csv", type=Path, required=True)
    args = p.parse_args()
    selected, omitted = build(args.rom.read_bytes(), args.pokeapi_csv)
    common = ["species", "level", "internal_move", "api_move", "name", "source_group"]
    write_csv(CATALOG, selected, common + ["fallback"])
    write_csv(OMITTED, omitted, common + ["reason"])
    print(f"Catálogo: {len(selected)} entradas em 1.025 espécies -> {CATALOG}")
    print(f"Omitidos: {len(omitted)} entradas -> {OMITTED}; "
          f"motivos: {dict(Counter(x['reason'] for x in omitted))}")
    print("Fontes:", dict(Counter(r["source_group"] for r in selected)))


if __name__ == "__main__":
    main()
