#!/usr/bin/env python3
"""Gera artefatos determinísticos do motor_v6 a partir do commit fixado do PokéAPI.

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
POKEAPI_COMMIT = '6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce'
CSV_HASHES = {
    'machines.csv': 'f9df7faaf0a60896fa344abd2b639f83f79c2a24e1fd4bb3560ca7da76e9a6ad',
    'move_names.csv': '99e23ee38ea53d1473474d463b87651deac3cd4928750f8186feae66da45c147',
    'pokemon_moves.csv': '22a807cef26891eeac0d0c900bd363e66baf421f7ee795bc7bc3e718f23b939e',
    'items.csv': 'f08cd6dc30b447cb91cbe9232c79052e8521f32f6105bb1489b5bfabf4ca3241',
    'item_game_indices.csv': 'ad7576a23dea4e136ea887f5f04b680abc4f72131812fa011bdddeb54760c653',
}
PRIOR_HASHES = {
    ROOT / 'data/tms_motor_ampliado.csv': 'b1d9110d08e06314a731609647629bc64a40708bc62e830ed35864b71a1aad79',
    ROOT / 'data/compatibilidade_tms_motor_ampliado.bin': '484244b19b9bb30ac5dee089beb3d28f4a4fdbf25f27bf625275797ac19c3c71',
    ROOT / 'data/learnsets_gen1_9_complemento.csv': 'a6c08fe9c4cbfd6dfa9e36b09a5a11b9744f3904ce3a3dabad0d5f695b3e742c',
}

# Seis TMs SV habilitadas neste lote por mecanismos compartilhados autocontidos:
# (tm_number, internal_move, api_move, expected_name, limite)
ENABLED_TMS = {
    43:  (374, 374, 'Fling',           'poder e consumo por item; sem ativar Berries/Herbs no alvo nem Klutz/Magic Room'),
    170: (808, 796, 'Steel Beam',      'custo de ceil(HP max/2); sem Magic Guard'),
    198: (809, 809, 'Poltergeist',     'exige item segurado no alvo; sem Klutz/Magic Room'),
    201: (810, 802, 'Misty Explosion', 'sem bônus de Misty Terrain'),
    210: (811, 916, 'Supercell Slam',  'queda de floor(HP max/2) em erro/Protect/imunidade; sem Magic Guard'),
    212: (812, 813, 'Triple Axel',     '20/40/60 com 3 checagens; sem Loaded Dice/Skill Link moderno'),
}

# Em FireRed (Gen III), estes cinco fósseis pertencem ao bolso Key Items (2) e
# não podem ser segurados nem arremessados por Fling.
GEN3_KEY_FOSSILS = {286, 287, 354, 357, 358}

# Mapeamento de item_fling_effect_id do PokéAPI para MOVE_EFFECT_* nativos da FireRed.
# Efeitos 3 (Berry) e 4 (Herb) causam o dano base correto (10 BP) e consomem o item,
# mas ainda não forçam ativação imediata da Berry/Herb no alvo (documentado em limite).
FLING_EFFECT_MAP = {
    1: 6,  # Badly poisons -> MOVE_EFFECT_TOXIC
    2: 3,  # Burns         -> MOVE_EFFECT_BURN
    3: 0,  # Berry (pendente ativação no alvo)
    4: 0,  # Herb  (pendente ativação no alvo)
    5: 5,  # Paralyzes     -> MOVE_EFFECT_PARALYSIS
    6: 2,  # Poisons       -> MOVE_EFFECT_POISON
    7: 8,  # Flinches      -> MOVE_EFFECT_FLINCH
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(csv_dir: Path) -> tuple[bytes, bytes, bytes, bytes]:
    for path, expected in PRIOR_HASHES.items():
        if sha256(path.read_bytes()) != expected:
            raise ValueError(f'Entrada local divergente: {path.name}')
    for name, expected in CSV_HASHES.items():
        if sha256((csv_dir / name).read_bytes()) != expected:
            raise ValueError(f'CSV do PokéAPI fora do commit esperado ({POKEAPI_COMMIT}): {name}')

    sv_machines = {}
    with open(csv_dir / 'machines.csv', newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            if row['version_group_id'] == '25':
                sv_machines[int(row['machine_number'])] = int(row['move_id'])
    move_names = {}
    with open(csv_dir / 'move_names.csv', newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            if row['local_language_id'] == '9':
                move_names[int(row['move_id'])] = row['name']

    for tm, (_mid, api_move, exp_name, _lim) in ENABLED_TMS.items():
        if sv_machines.get(tm) != api_move or move_names.get(api_move) != exp_name:
            raise ValueError(f'Metadados inesperados no PokéAPI para TM{tm:03d}')

    levels = list(csv.DictReader((ROOT / 'data/learnsets_gen1_9_complemento.csv').open(encoding='utf-8')))
    sources: dict[int, collections.Counter[int]] = collections.defaultdict(collections.Counter)
    for row in levels:
        sources[int(row['species'])][int(row['source_group'])] += 1
    groups = {sid: c.most_common(1)[0][0] for sid, c in sources.items()}
    if len(groups) != 1025:
        raise ValueError('Espécies sem grupo-fonte completo')

    # 1. Compatibilidade das 6 novas TMs SV + entradas de nível de Fling (api_move=374).
    tm_by_api = {api_move: tm for tm, (_mid, api_move, _n, _l) in ENABLED_TMS.items()}
    compat = bytearray((ROOT / 'data/compatibilidade_tms_motor_ampliado.bin').read_bytes())
    existing_keys = {
        (int(r['species']), int(r['level']), int(r['internal_move']), int(r['api_move']))
        for r in levels
    }
    added_levels: list[dict[str, str]] = []

    with open(csv_dir / 'pokemon_moves.csv', newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            sid = int(row['pokemon_id'])
            if not 1 <= sid <= 1025 or int(row['version_group_id']) != groups[sid]:
                continue
            api_move = int(row['move_id'])
            method = row['pokemon_move_method_id']
            if method == '4' and api_move in tm_by_api:
                tm = tm_by_api[api_move]
                compat[sid * 29 + (tm - 1) // 8] |= 1 << ((tm - 1) % 8)
            elif method == '1' and api_move == 374:
                lv = int(row['level'])
                key = (sid, lv, 374, 374)
                if key not in existing_keys:
                    existing_keys.add(key)
                    added_levels.append({
                        'species': str(sid),
                        'level': str(lv),
                        'internal_move': '374',
                        'api_move': '374',
                        'name': 'Fling',
                        'source_group': str(groups[sid]),
                        'fallback': '',
                    })

    if len(added_levels) != 23:
        raise ValueError(f'Quantidade inesperada de entradas de nível de Fling: {len(added_levels)}')

    # 2. Catálogo atualizado de TMs SV (210/229 disponíveis).
    tm_rows = list(csv.DictReader((ROOT / 'data/tms_motor_ampliado.csv').open(encoding='utf-8')))
    tm_buf = io.StringIO()
    tm_writer = csv.DictWriter(tm_buf, fieldnames=tm_rows[0].keys(), lineterminator='\n')
    tm_writer.writeheader()
    for row in tm_rows:
        tm = int(row['tm'])
        if tm in ENABLED_TMS:
            mid, api_move, exp_name, lim = ENABLED_TMS[tm]
            if int(row['api_move']) != api_move or row['name'] != exp_name:
                raise ValueError(f'Linha anterior divergente para TM{tm:03d}')
            row = dict(row, internal_move=str(mid), status='disponivel', motivo='', limite=lim)
        tm_writer.writerow(row)

    # 3. Tabela de learnsets por nível (14.300 + 23 = 14.323 linhas, ordenadas estavelmente).
    merged_levels = levels + added_levels
    merged_levels.sort(key=lambda r: (int(r['species']), int(r['level'])))
    lv_buf = io.StringIO()
    lv_writer = csv.DictWriter(lv_buf, fieldnames=levels[0].keys(), lineterminator='\n')
    lv_writer.writeheader()
    lv_writer.writerows(merged_levels)

    # 4. Tabela compacta de Fling (605 * 2 bytes: [potência, move_effect_byte]).
    api_items = {}
    with open(csv_dir / 'items.csv', newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            pwr = int(row['fling_power']) if row['fling_power'] else 0
            eff = int(row['fling_effect_id']) if row['fling_effect_id'] else 0
            api_items[int(row['id'])] = (pwr, FLING_EFFECT_MAP.get(eff, 0))

    fling = bytearray(605 * 2)
    with open(csv_dir / 'item_game_indices.csv', newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            if row['generation_id'] != '3':
                continue
            gidx = int(row['game_index'])
            if 1 <= gidx <= 374 and gidx not in GEN3_KEY_FOSSILS and not (289 <= gidx <= 346):
                pwr, mveff = api_items[int(row['item_id'])]
                fling[2 * gidx] = pwr
                fling[2 * gidx + 1] = mveff if pwr else 0

    return (
        tm_buf.getvalue().encode('utf-8'),
        bytes(compat),
        lv_buf.getvalue().encode('utf-8'),
        bytes(fling),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pokeapi-csv', type=Path, required=True)
    args = parser.parse_args()
    tm_csv, compat_bin, lv_csv, fling_bin = generate(args.pokeapi_csv)
    outputs = (
        (ROOT / 'data/tms_motor_v6.csv', tm_csv),
        (ROOT / 'data/compatibilidade_tms_motor_v6.bin', compat_bin),
        (ROOT / 'data/learnsets_motor_v6.csv', lv_csv),
        (ROOT / 'data/fling_itens_motor_v6.bin', fling_bin),
    )
    for path, content in outputs:
        path.write_bytes(content)
        print(f'{path.relative_to(ROOT)}: {len(content)} B  sha256={sha256(content)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
