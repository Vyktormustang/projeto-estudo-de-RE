#!/usr/bin/env python3
"""Gera artefatos determinísticos do motor_v9 a partir do commit fixado do PokéAPI.

Incorpora +368 entradas de subida de nível antes omitidas em 49 golpes das
famílias de alteração de tipos/habilidades, trocas/divisões/inversão de
atributos, sinergias de campo/equipe, sacrifício de HP, clérigo/cura contínua,
crítico garantido, desejo de cura/substituto de pivot e controle de ordem/cópia,
preservando integralmente as 229/229 TMs SV do motor_v8 e documentando os 8
golpes finais (34 entradas) mantidos fora de escopo por dependerem de
subsistemas ausentes na engine GBA Gen 3.

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
    'move_names.csv': '99e23ee38ea53d1473474d463b87651deac3cd4928750f8186feae66da45c147',
    'pokemon_moves.csv': '22a807cef26891eeac0d0c900bd363e66baf421f7ee795bc7bc3e718f23b939e',
}
PRIOR_HASHES = {
    ROOT / 'data/tms_motor_v8.csv': '20eba409d81c459393d6156f5053a3f5bf71e4ac99c7c4574287a39f2b95523c',
    ROOT / 'data/compatibilidade_tms_motor_v8.bin': '358a1b9fa456a23a22f8c3249d5381f75585139a5385690c58a43c1de8eea3ac',
    ROOT / 'data/learnsets_motor_v8.csv': '19abc5661267157524b9dcdc9ad769cdf12a20f9f44a3be63f134ae2ec9120f7',
}

# 49 golpes de subida de nível implementados no motor_v9:
# api_move -> (internal_move, expected_pokeapi_name)
ENABLED_LEVEL_MOVES: dict[int, tuple[int, str]] = {
    # Família 1: Alteração de tipos e vulnerabilidade elemental (6 golpes, 48 entradas)
    487: (486, 'Soak'),
    513: (512, 'Reflect Type'),
    567: (563, 'Trick-or-Treat'),
    571: (567, 'Forest’s Curse'),
    749: (674, 'Tar Shot'),
    750: (675, 'Magic Powder'),
    # Família 2: Manipulação de habilidades e eletrificação (5 golpes, 70 entradas)
    380: (380, 'Gastro Acid'),
    388: (388, 'Worry Seed'),
    494: (493, 'Entrainment'),
    582: (578, 'Electrify'),
    867: (759, 'Doodle'),
    # Família 3: Trocas, divisões, inversão e sinergias de atributos (18 golpes, 100 entradas)
    367: (367, 'Acupressure'),
    379: (379, 'Power Trick'),
    384: (384, 'Power Swap'),
    385: (385, 'Guard Swap'),
    391: (391, 'Heart Swap'),
    470: (469, 'Guard Split'),
    471: (470, 'Power Split'),
    563: (559, 'Rototiller'),
    576: (572, 'Topsy-Turvy'),
    579: (575, 'Flower Shield'),
    599: (595, 'Venom Drench'),
    602: (598, 'Magnetic Flux'),
    668: (623, 'Strength Sap'),
    672: (627, 'Toxic Thread'),
    674: (629, 'Gear Up'),
    683: (638, 'Speed Swap'),
    777: (684, 'Decorate'),
    858: (750, 'Spicy Extract'),
    # Família 4: Sacrifício de HP, clérigo, cura contínua, crítico e pivot (15 golpes, 85 entradas)
    361: (361, 'Healing Wish'),
    375: (375, 'Psycho Shift'),
    392: (392, 'Aqua Ring'),
    461: (460, 'Lunar Dance'),
    464: (463, 'Dark Void'),
    515: (514, 'Final Gambit'),
    673: (628, 'Laser Focus'),
    685: (640, 'Purify'),
    748: (673, 'No Retreat'),
    775: (682, 'Clangorous Soul'),
    816: (710, 'Jungle Healing'),
    849: (742, 'Lunar Blessing'),
    850: (743, 'Take Heart'),
    868: (760, 'Fillet Away'),
    880: (770, 'Shed Tail'),
    # Família 5: Cópia, controle de ordem de ação e prisão (5 golpes, 65 entradas)
    383: (383, 'Copycat'),
    495: (494, 'After You'),
    511: (510, 'Quash'),
    587: (583, 'Fairy Lock'),
    753: (678, 'Octolock'),
}

# 8 golpes mantidos explicitamente fora de escopo (34 entradas de 729 = 4,7%):
# api_move -> (internal_move, expected_name, motivo_tecnico)
OMITTED_LEVEL_MOVES: dict[int, tuple[int, str, str]] = {
    363: (363, 'Natural Gift', 'Tabela completa de tipo/poder por Berry ausente e golpe removido em SV'),
    478: (477, 'Magic Room', 'Supressão transversal de todos os held items exige hooks fora da tabela de script'),
    493: (492, 'Simple Beam', 'Habilidade Simple não existe na tabela nativa de habilidades Gen 3 (0..77)'),
    502: (501, 'Ally Switch', 'Permutação física de bancos ativos/sprites de parceiros em duplas Gen 3'),
    689: (644, 'Instruct', 'Reexecução aninhada de ação completa de outro battler no meio do script'),
    747: (672, 'Stuff Cheeks', 'Consumo forçado de Berry equipada com disparo da rotina de efeito da Berry'),
    752: (677, 'Teatime', 'Consumo simultâneo de Berries em todos os bancos com disparo individual de efeitos'),
    863: (755, 'Revival Blessing', 'Seleção de Pokémon desmaiado (HP == 0) exige patch dedicado na UI de party_menu'),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(csv_dir: Path) -> bytes:
    for path, expected in PRIOR_HASHES.items():
        if sha256(path.read_bytes()) != expected:
            raise ValueError(f'Entrada local divergente: {path.name}')
    for name, expected in CSV_HASHES.items():
        if sha256((csv_dir / name).read_bytes()) != expected:
            raise ValueError(f'CSV do PokéAPI fora do commit esperado ({POKEAPI_COMMIT}): {name}')

    move_names: dict[int, str] = {}
    with open(csv_dir / 'move_names.csv', newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            if row['local_language_id'] == '9':
                move_names[int(row['move_id'])] = row['name']

    if len(ENABLED_LEVEL_MOVES) != 49 or len(OMITTED_LEVEL_MOVES) != 8:
        raise ValueError('Partição de golpes de nível inválida')
    if set(ENABLED_LEVEL_MOVES) & set(OMITTED_LEVEL_MOVES):
        raise ValueError('Sobreposição entre golpes habilitados e omitidos')

    for api_move, (_mid, exp_name) in ENABLED_LEVEL_MOVES.items():
        if move_names.get(api_move) != exp_name:
            raise ValueError(f'Nome inesperado no PokéAPI para move_id={api_move}: {move_names.get(api_move)!r}')
    for api_move, (_mid, exp_name, _why) in OMITTED_LEVEL_MOVES.items():
        if move_names.get(api_move) != exp_name:
            raise ValueError(f'Nome inesperado no PokéAPI para move_id={api_move}: {move_names.get(api_move)!r}')

    levels = list(csv.DictReader((ROOT / 'data/learnsets_motor_v8.csv').open(encoding='utf-8')))
    sources: dict[int, collections.Counter[int]] = collections.defaultdict(collections.Counter)
    for row in levels:
        sources[int(row['species'])][int(row['source_group'])] += 1
    groups = {sid: c.most_common(1)[0][0] for sid, c in sources.items()}
    if len(groups) != 1025:
        raise ValueError('Espécies sem grupo-fonte completo')

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
            if row['pokemon_move_method_id'] != '1':
                continue
            api_move = int(row['move_id'])
            if api_move not in ENABLED_LEVEL_MOVES:
                continue
            mid, exp_name = ENABLED_LEVEL_MOVES[api_move]
            lv = int(row['level'])
            key = (sid, lv, mid, api_move)
            if key not in existing_keys:
                existing_keys.add(key)
                added_levels.append({
                    'species': str(sid),
                    'level': str(lv),
                    'internal_move': str(mid),
                    'api_move': str(api_move),
                    'name': exp_name.replace('’', "'"),
                    'source_group': str(groups[sid]),
                    'fallback': '',
                })

    if len(added_levels) != 368:
        raise ValueError(f'Quantidade inesperada de entradas de nível adicionadas: {len(added_levels)}')

    # Valida partição exata (368 + 34 = 402) contra golpes_pendentes_complemento.csv
    pendentes = list(csv.DictReader((ROOT / 'docs/golpes_pendentes_complemento.csv').open(encoding='utf-8')))
    rem_enabled = 0
    rem_omitted = 0
    v8_triples = {(int(r['species']), int(r['level']), int(r['internal_move'])) for r in levels}
    for row in pendentes:
        triple = (int(row['species']), int(row['level']), int(row['internal_move']))
        if triple in v8_triples:
            continue
        api_m = int(row['api_move'])
        if api_m in ENABLED_LEVEL_MOVES:
            rem_enabled += 1
        elif api_m in OMITTED_LEVEL_MOVES:
            rem_omitted += 1
        else:
            raise ValueError(f'Golpe pendente não classificado: {row}')
    if (rem_enabled, rem_omitted) != (368, 34):
        raise ValueError(f'Partição divergente: {(rem_enabled, rem_omitted)} != (368, 34)')

    merged_levels = levels + added_levels
    merged_levels.sort(key=lambda r: (int(r['species']), int(r['level'])))
    lv_buf = io.StringIO()
    lv_writer = csv.DictWriter(lv_buf, fieldnames=levels[0].keys(), lineterminator='\n')
    lv_writer.writeheader()
    lv_writer.writerows(merged_levels)
    return lv_buf.getvalue().encode('utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pokeapi-csv', type=Path, required=True)
    args = parser.parse_args()
    lv_csv = generate(args.pokeapi_csv)
    out_path = ROOT / 'data/learnsets_motor_v9.csv'
    out_path.write_bytes(lv_csv)
    print(f'{out_path.relative_to(ROOT)}: {len(lv_csv)} B  sha256={sha256(lv_csv)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
