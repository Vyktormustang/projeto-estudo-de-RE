#!/usr/bin/env python3
"""Gera apenas os catálogos adicionais, usando a mesma fonte PokéAPI fixada.

A ROM, saves e os CSVs de origem da PokéAPI não são redistribuídos por este
programa. O status 'parcial' não equivale a uma implementação fiel de Gen 9.
"""
from __future__ import annotations
import collections
import csv
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts import gerar_atualizacoes_gen9 as previous  # noqa: E402
from scripts import gerar_catalogo_golpes as catalog  # noqa: E402

# TM, ID interno novo, API, nome. A coluna último campo descreve os limites.
NEW_MOVES = (
    (20, 797, 885, 'Trailblaze', 'interações seguem parcialmente o motor antigo'),
    (21, 798, 884, 'Pounce', 'interações seguem parcialmente o motor antigo'),
    (22, 799, 886, 'Chilling Water', 'interações seguem parcialmente o motor antigo'),
    (144, 800, 519, 'Fire Pledge', 'sem combinação entre Pledges'),
    (145, 801, 518, 'Water Pledge', 'sem combinação entre Pledges'),
    (146, 802, 520, 'Grass Pledge', 'sem combinação entre Pledges'),
    (169, 803, 434, 'Draco Meteor', 'interações seguem parcialmente o motor antigo'),
    (171, 804, 851, 'Tera Blast', 'sem Terastalização'),
    (194, 805, 803, 'Grassy Glide', 'sem prioridade de terreno'),
    (215, 806, 815, 'Scorching Sands', 'interações seguem parcialmente o motor antigo'),
)
# Autotomize não reduz peso; os quatro ataques dinâmicos ignoram alguns
# modificadores de peso/velocidade da geração moderna.
RESTORED_LEVEL_MOVES = {503, 474, 360, 485, 483, 531}
POKEMON_CSV_SHA256 = '16c81c33188b0eac403aa2f759fcbe9e42c611f722d263f5b5a6a5bff9f8ce6b'
DYNAMIC_TMS = {
    72: (485, 'Electro Ball', 'velocidade parcial, sem todas habilidades/itens'),
    121: (483, 'Heavy Slam', 'peso base da espécie, sem todos modificadores'),
    180: (360, 'Gyro Ball', 'velocidade parcial, sem todas habilidades/itens'),
    189: (531, 'Heat Crash', 'peso base da espécie, sem todos modificadores'),
}


def generate(directory: Path):
    for name, expected in (previous.CSV_HASHES | {'pokemon.csv': POKEMON_CSV_SHA256}).items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'CSV PokéAPI não corresponde ao commit fixado: {name}')
    weights = [0] * 1026
    for row in catalog.read_csv(directory / 'pokemon.csv'):
        sid = int(row['id'])
        if 1 <= sid <= 1025 and row['is_default'] == '1':
            weights[sid] = int(row['weight'])  # décimos de kg
    if not all(weights[1:]):
        raise ValueError('Pesos das espécies incompletos')
    weight_data = struct.pack('<1026H', *weights)
    selected = catalog.read_csv(ROOT / 'data/learnsets_gen1_9_atualizados.csv')
    omissions = catalog.read_csv(ROOT / 'docs/golpes_ainda_nao_incluidos.csv')
    restored, remaining = [], []
    for row in omissions:
        if int(row['internal_move']) in RESTORED_LEVEL_MOVES:
            restored.append({k: row[k] for k in ('species','level','internal_move','api_move','name','source_group')} | {'fallback': ''})
        else:
            remaining.append(row)
    if len(restored) != 116:
        raise ValueError('Registros de níveis esperados mudaram')
    combined = selected + restored
    # Mantém a ordem dos golpes que já estavam na ROM. Na ausência de ordem
    # explícita por nível, os recém-ativados vêm depois dos já existentes.
    combined.sort(key=lambda r: (int(r['species']), int(r['level'])))
    counts = collections.Counter(int(r['species']) for r in combined)
    if len(counts) != 1025 or max(counts.values()) > 50:
        raise ValueError('Lista de espécies inválida ou excede o limite')

    machines = catalog.read_csv(ROOT / 'data/tms_gen9.csv')
    new_by_tm = {tm: (mid, api, name, note) for tm, mid, api, name, note in NEW_MOVES}
    for row in machines:
        tm = int(row['tm'])
        row['limite'] = ''
        if tm in new_by_tm:
            mid, api, name, note = new_by_tm[tm]
            if row['name'] != name or int(row['api_move']) != api or row['status'] != 'nao_disponivel':
                raise ValueError(f'TM{tm} diverge do catálogo anterior')
            row.update(internal_move=str(mid), status='disponivel', motivo='', limite=note)
        elif tm in DYNAMIC_TMS:
            mid, name, note = DYNAMIC_TMS[tm]
            if row['name'] != name or int(row['internal_move']) != mid or row['status'] != 'nao_disponivel':
                raise ValueError(f'TM dinâmica {tm} diverge do catálogo anterior')
            row.update(status='disponivel', motivo='', limite=note)

    sources = collections.defaultdict(collections.Counter)
    for row in selected:
        sources[int(row['species'])][int(row['source_group'])] += 1
    source = {sid: counter.most_common(1)[0][0] for sid, counter in sources.items()}
    compat = bytearray((ROOT / 'data/compatibilidade_tms_gen9.bin').read_bytes())
    if len(compat) != 1026 * 29: raise ValueError('Matriz anterior inválida')
    by_api = {api: tm for tm, _mid, api, _name, _note in NEW_MOVES}
    by_api.update({int(row['api_move']): int(row['tm']) for row in machines
                   if int(row['tm']) in DYNAMIC_TMS})
    with (directory / 'pokemon_moves.csv').open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['pokemon_move_method_id'] != '4': continue
            sid = int(row['pokemon_id'])
            tm = by_api.get(int(row['move_id']))
            if tm and 1 <= sid <= 1025 and int(row['version_group_id']) == source[sid]:
                compat[sid * 29 + (tm - 1)//8] |= 1 << ((tm - 1)%8)
    return combined, remaining, machines, bytes(compat), weight_data


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pokeapi-csv', type=Path, required=True)
    a = p.parse_args()
    selected, omitted, machines, compat, weights = generate(a.pokeapi_csv)
    fields = ['species','level','internal_move','api_move','name','source_group']
    catalog.write_csv(ROOT / 'data/learnsets_gen1_9_complemento.csv', selected, fields + ['fallback'])
    catalog.write_csv(ROOT / 'docs/golpes_pendentes_complemento.csv', omitted, fields + ['reason'])
    catalog.write_csv(ROOT / 'data/tms_gen9_complemento.csv', machines,
                      ['tm','item_id','api_move','internal_move','name','status','motivo','limite'])
    (ROOT / 'data/compatibilidade_tms_complemento.bin').write_bytes(compat)
    (ROOT / 'data/pesos_gen1_9.bin').write_bytes(weights)
    print(f'Níveis: {len(selected)}; ainda omitidos: {len(omitted)}')
    print(f'TMs disponíveis: {sum(r["status"] == "disponivel" for r in machines)}; compatibilidades: {sum(b.bit_count() for b in compat)}')

if __name__ == '__main__': main()
