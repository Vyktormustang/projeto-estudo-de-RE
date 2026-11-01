#!/usr/bin/env python3
"""Gera catálogos de TMs e níveis a partir da PokéAPI fixada e da ROM pessoal.

Não inclui nem baixa ROMs. Campos 'internal_move' usam nomes verificados na
ROM (os IDs da PokéAPI não coincidem sempre com os IDs internos do hack).
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import efeitos_gen9 as effects, gerar_catalogo_golpes as catalog  # noqa: E402

BASE_SHA = '412bcd89214d4126d92f6c2256a56227c6f30fa138e0b262ef287f5b12b3997b'
CSV_HASHES = {
    'machines.csv': 'f9df7faaf0a60896fa344abd2b639f83f79c2a24e1fd4bb3560ca7da76e9a6ad',
    'move_names.csv': '99e23ee38ea53d1473474d463b87651deac3cd4928750f8186feae66da45c147',
    'pokemon_moves.csv': '22a807cef26891eeac0d0c900bd363e66baf421f7ee795bc7bc3e718f23b939e',
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(base: bytes, directory: Path):
    if len(base) != 0x1000000 or digest(base) != BASE_SHA:
        raise ValueError('ROM de entrada não é a versão de golpes por nível reconhecida')
    for name, expected in CSV_HASHES.items():
        if digest((directory / name).read_bytes()) != expected:
            raise ValueError(f'CSV da PokéAPI alterado ou de outro commit: {name}')
    rom = effects.apply_effects(base)
    previous = catalog.ROM_SHA256
    try:
        catalog.ROM_SHA256 = digest(rom)
        selected, omitted = catalog.build(rom, directory)
    finally:
        catalog.ROM_SHA256 = previous

    english = {int(x['move_id']): x['name'] for x in catalog.read_csv(directory / 'move_names.csv')
               if x['local_language_id'] == '9'}
    names = {catalog.normalize(catalog.move_name(rom, i)): i for i in range(1, catalog.NAMES_COUNT)}
    if len(names) != catalog.NAMES_COUNT - 1:
        raise ValueError('Nomes internos vazios ou duplicados')
    machines = {int(r['machine_number']): int(r['move_id'])
                for r in catalog.read_csv(directory / 'machines.csv') if r['version_group_id'] == '25'}
    if sorted(machines) != list(range(1, 230)):
        raise ValueError('Catálogo SV de TMs não contém os 229 números esperados')

    rows = []
    by_api = collections.defaultdict(list)
    for number, api in sorted(machines.items()):
        internal = catalog.ALIASES.get(api, names.get(catalog.normalize(english[api]), 0))
        reason = catalog.usable(rom, internal)
        row = {'tm': number, 'item_id': 374 + number, 'api_move': api,
               'internal_move': internal, 'name': english[api],
               'status': 'disponivel' if not reason else 'nao_disponivel', 'motivo': reason}
        rows.append(row)
        if not reason:
            by_api[api].append(number)

    groups = collections.defaultdict(collections.Counter)
    for row in selected:
        groups[int(row['species'])][int(row['source_group'])] += 1
    if set(groups) != set(range(1, 1026)):
        raise ValueError('Fontes de espécies incompletas')
    # O fallback de nível 1 do Crabrawler vem de USUM; sua fonte principal
    # continua sendo Scarlet/Violet. Não usar simplesmente a primeira linha.
    source = {sid: counts.most_common(1)[0][0] for sid, counts in groups.items()}
    compat = bytearray(1026 * 29)  # espécie 0 vazia; bits de TM001 a TM229
    with (directory / 'pokemon_moves.csv').open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['pokemon_move_method_id'] != '4':
                continue
            sid = int(row['pokemon_id'])
            if not 1 <= sid <= 1025 or int(row['version_group_id']) != source[sid]:
                continue
            for number in by_api.get(int(row['move_id']), ()):
                compat[sid * 29 + (number - 1) // 8] |= 1 << ((number - 1) % 8)
    return selected, omitted, rows, bytes(compat)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--pokeapi-csv', type=Path, required=True)
    args = p.parse_args()
    selected, omitted, machines, compat = generate(args.rom.read_bytes(), args.pokeapi_csv)
    fields = ['species', 'level', 'internal_move', 'api_move', 'name', 'source_group']
    catalog.write_csv(ROOT / 'data/learnsets_gen1_9_atualizados.csv', selected, fields + ['fallback'])
    catalog.write_csv(ROOT / 'docs/golpes_ainda_nao_incluidos.csv', omitted, fields + ['reason'])
    catalog.write_csv(ROOT / 'data/tms_gen9.csv', machines,
                      ['tm', 'item_id', 'api_move', 'internal_move', 'name', 'status', 'motivo'])
    (ROOT / 'data/compatibilidade_tms_gen9.bin').write_bytes(compat)
    print(f'Níveis: {len(selected)} entradas; ainda omitidas: {len(omitted)}')
    print(f'TMs: {sum(r["status"] == "disponivel" for r in machines)}/229; '
          f'{sum(b.bit_count() for b in compat)} compatibilidades')


if __name__ == '__main__':
    main()
