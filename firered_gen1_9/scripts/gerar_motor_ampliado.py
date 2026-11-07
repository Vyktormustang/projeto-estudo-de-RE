#!/usr/bin/env python3
"""Reproduz catálogo/compatibilidade da TM225 usando PokéAPI fixada.

Esta adição não implementa as demais mecânicas modernas pendentes.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MOVES_SHA='22a807cef26891eeac0d0c900bd363e66baf421f7ee795bc7bc3e718f23b939e'
LEVELS_SHA='a6c08fe9c4cbfd6dfa9e36b09a5a11b9744f3904ce3a3dabad0d5f695b3e742c'
COMPAT_SHA='23de53c08991baa31623eb184f277420e743770965b920294615e01e61d278d3'
MACHINES_SHA='074ccc0865d2fc2d0f298859ad721cbbd0fd4ba99da2aebc119dd85033edf394'

def read_verified(path,sha):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError(f'Fonte inesperada: {path}')
    return raw

def generate(directory: Path):
    from io import StringIO
    moves=read_verified(directory/'pokemon_moves.csv',MOVES_SHA)
    levels=read_verified(ROOT/'data/learnsets_gen1_9_complemento.csv',LEVELS_SHA)
    compat=bytearray(read_verified(ROOT/'data/compatibilidade_tms_complemento.bin',COMPAT_SHA))
    machines=read_verified(ROOT/'data/tms_gen9_complemento.csv',MACHINES_SHA)
    sources=collections.defaultdict(collections.Counter)
    for r in csv.DictReader(StringIO(levels.decode())):
        sources[int(r['species'])][int(r['source_group'])]+=1
    groups={sid:c.most_common(1)[0][0] for sid,c in sources.items()}
    compatible=set()
    for r in csv.DictReader(StringIO(moves.decode())):
        if r['move_id']!='912' or r['pokemon_move_method_id']!='4':continue
        sid,group=int(r['pokemon_id']),int(r['version_group_id'])
        if groups.get(sid)==group: compatible.add(sid)
    if len(compatible)!=43:raise ValueError('Compatibilidade esperada de Hard Press divergente')
    for sid in compatible:compat[sid*29+(225-1)//8] |= 1 << ((225-1)%8)
    reader=csv.DictReader(StringIO(machines.decode()))
    fields=reader.fieldnames;rows=list(reader)
    row=rows[224]
    if (row['tm'],row['item_id'],row['api_move'],row['name'],row['status']) != ('225','599','912','Hard Press','nao_disponivel'):
        raise ValueError('Linha de Hard Press divergente')
    row.update(internal_move='807',status='disponivel',motivo='',
               limite='poder pelo HP; demais regras seguem parcialmente o motor anterior')
    return rows,fields,bytes(compat)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pokeapi-csv',type=Path,required=True)
    args=parser.parse_args();rows,fields,compat=generate(args.pokeapi_csv)
    with (ROOT/'data/tms_motor_ampliado.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
    (ROOT/'data/compatibilidade_tms_motor_ampliado.bin').write_bytes(compat)
    print('TM225: 43 espécies; loja: 204 das 229 TMs')
if __name__=='__main__':main()
