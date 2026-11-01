#!/usr/bin/env python3
"""Gera artefatos determinísticos do motor_v8 a partir do commit fixado do PokéAPI.

Habilita as 10 últimas TMs de Scarlet/Violet (219 -> 229/229) por famílias de
clima/terreno/campo/armadilhas compartilhadas e incorpora +245 entradas de
subida de nível antes omitidas em 18 golpes das mesmas famílias.

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
    ROOT / 'data/tms_motor_v7.csv': 'ef1fd0c595e644805a3b2722d30ac146807632c925ac5108cae1314cfcc8dace',
    ROOT / 'data/compatibilidade_tms_motor_v7.bin': '618563d9dbc6ead8ecce2ae0f38978ec62ff0da5ebae2e294efaffbb7e1420d7',
    ROOT / 'data/learnsets_motor_v7.csv': 'ed8e02a3bb3665a68ed3d53a59c2532d273bf0cbda630ef77aee56e6cbc6c2fe',
}

# Dez TMs SV finais habilitadas no motor_v8 (219 -> 229 de 229):
# (tm_number -> (internal_move, api_move, expected_name, limite))
ENABLED_TMS = {
    52:  (773, 883, 'Snowscape',        '5 turnos sem dano residual e +50% Def Gelo; sem Icy Rock/Slush Rush/Snow Cloak'),
    91:  (390, 390, 'Toxic Spikes',     'até 2 camadas (veneno/veneno grave) e absorção por Veneno aterrado; sem Heavy-Duty Boots'),
    113: (366, 366, 'Tailwind',         'dobra Velocidade do lado por 4 turnos; sem Wind Rider/Wind Power'),
    116: (445, 446, 'Stealth Rock',     'dano por efetividade de Pedra na entrada; sem Heavy-Duty Boots/Magic Guard'),
    136: (599, 604, 'Electric Terrain', '5 turnos: +30% Elétrico aterrado e bloqueia sono; sem Terrain Extender/Quark Drive'),
    137: (576, 580, 'Grassy Terrain',   '5 turnos: +30% Grama, cura 1/16 e 0.5x EQ/Bulldoze/Magnitude; sem Terrain Extender/Grassy Seed'),
    138: (633, 678, 'Psychic Terrain',  '5 turnos: +30% Psíquico aterrado e bloqueia prioridade >0; sem Terrain Extender/Psychic Seed'),
    139: (577, 581, 'Misty Terrain',    '5 turnos: 0.5x Dragão em alvo aterrado e bloqueia status/confusão; sem Terrain Extender/Misty Seed'),
    161: (433, 433, 'Trick Room',       '5 turnos: inverte ordem de Velocidade dentro de cada faixa de prioridade; sem Room Service'),
    178: (356, 356, 'Gravity',          '5 turnos: aterra todos, precisão 5/3 e bloqueia golpes aéreos'),
}

# TMs já disponíveis que recebem sinergia de clima/terreno/barreiras no motor_v8.
UPGRADED_LIMITES = {
    28:  '0.5x contra alvo aterrado em Grassy Terrain',
    58:  'quebra Reflect, Light Screen e Aurora Veil',
    63:  'quebra Reflect, Light Screen e Aurora Veil',
    143: 'precisão infalível em Snow/Hail',
    149: '0.5x contra alvo aterrado em Grassy Terrain',
    193: '100 BP tipo Gelo em Snow',
    194: 'prioridade +1 para usuário aterrado em Grassy Terrain',
    201: '150 BP para usuário aterrado em Misty Terrain',
    218: '120 BP para usuário aterrado em Psychic Terrain; alvo único no menu em duplas',
}

# Oito golpes adicionais de subida de nível antes omitidos que pertencem às
# mesmas famílias de campo/salas/barreiras/armadilhas/clima do motor_v8.
ENABLED_LEVEL_MOVES = {
    393: (393, 'Magnet Rise'),
    432: (432, 'Defog'),
    472: (471, 'Wonder Room'),
    564: (560, 'Sticky Web'),
    659: (614, 'Shore Up'),
    694: (649, 'Aurora Veil'),
    756: (681, 'Court Change'),
    882: (772, 'Tidy Up'),
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
            if row['version_group_id'] in ('25', '26', '27'):
                tm_num = int(row['machine_number'])
                if 1 <= tm_num <= 229:
                    sv_machines[tm_num] = int(row['move_id'])
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

    levels = list(csv.DictReader((ROOT / 'data/learnsets_motor_v7.csv').open(encoding='utf-8')))
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

    compat = bytearray((ROOT / 'data/compatibilidade_tms_motor_v7.bin').read_bytes())
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

    if len(added_levels) != 245:
        raise ValueError(f'Quantidade inesperada de entradas de nível adicionadas: {len(added_levels)}')

    tm_rows = list(csv.DictReader((ROOT / 'data/tms_motor_v7.csv').open(encoding='utf-8')))
    tm_buf = io.StringIO()
    tm_writer = csv.DictWriter(tm_buf, fieldnames=tm_rows[0].keys(), lineterminator='\n')
    tm_writer.writeheader()
    avail_count = 0
    for row in tm_rows:
        tm = int(row['tm'])
        if tm in ENABLED_TMS:
            mid, api_move, exp_name, lim = ENABLED_TMS[tm]
            if int(row['internal_move']) != mid or int(row['api_move']) != api_move or row['name'] != exp_name:
                raise ValueError(f'Linha anterior divergente para TM{tm:03d}')
            row = dict(row, status='disponivel', motivo='', limite=lim)
        elif tm in UPGRADED_LIMITES:
            row = dict(row, limite=UPGRADED_LIMITES[tm])
        if row['status'] == 'disponivel':
            avail_count += 1
        tm_writer.writerow(row)
    if avail_count != 229:
        raise ValueError(f'Total de TMs disponíveis inesperado: {avail_count}')

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
        (ROOT / 'data/tms_motor_v8.csv', tm_csv),
        (ROOT / 'data/compatibilidade_tms_motor_v8.bin', compat_bin),
        (ROOT / 'data/learnsets_motor_v8.csv', lv_csv),
    )
    for path, content in outputs:
        path.write_bytes(content)
        print(f'{path.relative_to(ROOT)}: {len(content)} B  sha256={sha256(content)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
