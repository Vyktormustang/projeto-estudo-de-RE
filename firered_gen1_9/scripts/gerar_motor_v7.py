#!/usr/bin/env python3
"""Gera artefatos determinísticos do motor_v7 a partir do commit fixado do PokéAPI.

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
}
PRIOR_HASHES = {
    ROOT / 'data/tms_motor_v6.csv': 'aece81a00878e6da6e3a4287ee6448ef6885c828a3393a9e2b732a980c493ab0',
    ROOT / 'data/compatibilidade_tms_motor_v6.bin': '649d97ea5e3d45e52ac19c3545a4ec448bfa4b46c21f17c3b41eac8a460c873e',
    ROOT / 'data/learnsets_motor_v6.csv': '9e7fd32c36a9a5e0c81e5eea639d904f534db9b1667308efcdca4078b21871d0',
}

# Nove TMs SV habilitadas neste lote por famílias mecânicas compartilhadas:
# (tm_number -> (internal_move, api_move, expected_name, limite))
ENABLED_TMS = {
    195: (813, 807, 'Burning Jealousy', 'queima se algum estágio do alvo subiu no turno'),
    199: (814, 808, 'Lash Out',         'dobra para 150 BP se algum estágio do usuário caiu no turno'),
    207: (815, 915, 'Temper Flare',     'dobra para 150 BP se o golpe anterior do usuário falhou'),
    213: (816, 811, 'Coaching',         'sobe Atk/Def do aliado em duplas; falha em simples'),
    220: (817, 800, 'Meteor Beam',      'carrega e sobe Sp. Atk no turno 1; sem Power Herb'),
    226: (818, 913, 'Dragon Cheer',     '+1 crítico no aliado (+2 se tipo Dragão) em duplas; sem Soundproof'),
    227: (819, 914, 'Alluring Voice',   'confunde se algum estágio do alvo subiu no turno; sem Soundproof/bypass de Substitute'),
    228: (820, 917, 'Psychic Noise',    'bloqueia cura por 2 turnos; sem Soundproof/bypass de Substitute'),
    229: (821, 918, 'Upper Hand',       'prioridade +3 e flinch contra golpe ofensivo de prioridade >0'),
}

# TMs já disponíveis que ganham mecânica dedicada no motor_v7.
UPGRADED_LIMITES = {
    48:  'troca automática pós-dano; sem Emergency Exit/Eject Button/Red Card',
    60:  'troca automática pós-dano; sem Emergency Exit/Eject Button/Red Card',
    84:  'dobra para 150 BP se o golpe anterior do usuário falhou',
    196: 'troca automática pós-dano; sem Emergency Exit/Eject Button/Red Card',
}

# Cinco golpes de subida de nível antes omitidos que compartilham exatamente as
# famílias implementadas no motor_v7 (pivot, carga em 2 turnos e cura/aliado).
ENABLED_LEVEL_MOVES = {
    505: (504, 'Heal Pulse'),
    575: (571, 'Parting Shot'),
    601: (597, 'Geomancy'),
    666: (621, 'Floral Healing'),
    791: (696, 'Life Dew'),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(csv_dir: Path) -> tuple[bytes, bytes, bytes]:
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
    for api_move, (_mid, exp_name) in ENABLED_LEVEL_MOVES.items():
        if move_names.get(api_move) != exp_name:
            raise ValueError(f'Nome inesperado no PokéAPI para move_id={api_move}')

    levels = list(csv.DictReader((ROOT / 'data/learnsets_motor_v6.csv').open(encoding='utf-8')))
    sources: dict[int, collections.Counter[int]] = collections.defaultdict(collections.Counter)
    for row in levels:
        sources[int(row['species'])][int(row['source_group'])] += 1
    groups = {sid: c.most_common(1)[0][0] for sid, c in sources.items()}
    if len(groups) != 1025:
        raise ValueError('Espécies sem grupo-fonte completo')

    tm_by_api = {api_move: tm for tm, (_mid, api_move, _n, _l) in ENABLED_TMS.items()}
    level_by_api = dict(ENABLED_LEVEL_MOVES)
    for _tm, (mid, api_move, exp_name, _lim) in ENABLED_TMS.items():
        level_by_api[api_move] = (mid, exp_name)

    compat = bytearray((ROOT / 'data/compatibilidade_tms_motor_v6.bin').read_bytes())
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
            elif method == '1' and api_move in level_by_api:
                mid, exp_name = level_by_api[api_move]
                lv = int(row['level'])
                key = (sid, lv, mid, api_move)
                if key not in existing_keys:
                    existing_keys.add(key)
                    added_levels.append({
                        'species': str(sid),
                        'level': str(lv),
                        'internal_move': str(mid),
                        'api_move': str(api_move),
                        'name': exp_name,
                        'source_group': str(groups[sid]),
                        'fallback': '',
                    })

    if len(added_levels) != 59:
        raise ValueError(f'Quantidade inesperada de entradas de nível adicionadas: {len(added_levels)}')

    tm_rows = list(csv.DictReader((ROOT / 'data/tms_motor_v6.csv').open(encoding='utf-8')))
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
        elif tm in UPGRADED_LIMITES:
            row = dict(row, limite=UPGRADED_LIMITES[tm])
        tm_writer.writerow(row)

    merged_levels = levels + added_levels
    merged_levels.sort(key=lambda r: (int(r['species']), int(r['level'])))
    lv_buf = io.StringIO()
    lv_writer = csv.DictWriter(lv_buf, fieldnames=levels[0].keys(), lineterminator='\n')
    lv_writer.writeheader()
    lv_writer.writerows(merged_levels)

    return (
        tm_buf.getvalue().encode('utf-8'),
        bytes(compat),
        lv_buf.getvalue().encode('utf-8'),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pokeapi-csv', type=Path, required=True)
    args = parser.parse_args()
    tm_csv, compat_bin, lv_csv = generate(args.pokeapi_csv)
    outputs = (
        (ROOT / 'data/tms_motor_v7.csv', tm_csv),
        (ROOT / 'data/compatibilidade_tms_motor_v7.bin', compat_bin),
        (ROOT / 'data/learnsets_motor_v7.csv', lv_csv),
    )
    for path, content in outputs:
        path.write_bytes(content)
        print(f'{path.relative_to(ROOT)}: {len(content)} B  sha256={sha256(content)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
