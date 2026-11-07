#!/usr/bin/env python3
"""Expande encontros noturnos a oito áreas, sobre v20 exata."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts import motor_v20 as previous, motor_v8 as v8, encontros_selvagens as wild, eventos_fixos as fixed
from scripts.treino_ev import write_new_file

BASE_SHA256=previous.OUTPUT_SHA256
OUTPUT_SHA256='cfbcebd0bf3ab0c1cbcb9872bc400f62d9c807fbd67dd99b4b89ffb16c92a10f'
PAYLOAD_PATH=ROOT/'patches/motor_v21/payload.bin'
PAYLOAD_SHA256='de85b79a1ffd6aab10ae23448fd1805033b49d4416ba02290048720303d75457'
PAYLOAD_SIZE=300
POLICY_PATH=ROOT/'data/encontros_horario_v21.csv'
POLICY_SHA256='f1e6bda06ebc3beb451c758865ad1a2ac641e460067926236852de266fc00ddc'
PAYLOAD_OFFSET=0x10E0000
TABLE_OFFSET=0x10E1000
SCRIPT_OFFSET=0x10E1300
TEXT_OFFSET=0x10E1400
RESERVED_LIMIT=0x10E2000
ENTRY_SELECT=0x090E0001
ENTRY_ENCOUNTER=0x090E0009
ENTRY_NIGHT=0x090E0011
ENTRY_SIGN=0x090E0019
HOOK_OFFSET=0x164340
NATIVE_PROLOGUE=previous.HOOK_BEFORE
HOOK_BEFORE=struct.pack('<HHI',0x4B00,0x4718,previous.ENTRY_ENCOUNTER)
SIGN_POINTER=0x7C20D8
SIGN_BEFORE=0x08000000+previous.SCRIPT_OFFSET
ORIGINAL_MESSAGE=bytes.fromhex('0f0020c21a080903')
MAPS=previous.MAPS+('MAP_ROUTE3','MAP_ROUTE4','MAP_ROUTE24','MAP_ROUTE25')
TABLE_SIZE=len(MAPS)*(12+8+12*4)
COMMON_GUIDE=(
    'Na grama destas oito areas,\nos encontros mudam a noite.\f'
    'Rota 1: Hoothoot / Nickit.\nRota 2: Poochyena / Houndour.\f'
    'Floresta: Spinarak / Morelull.\nRota 22: Murkrow / Greavard.\f'
    'Rota 3: Zubat / Cleffa.\nRota 4: Woobat / Noibat.\f'
    'Rota 24: Purrloin / Drowzee.\nRota 25: Shuppet / Duskull.\f'
    'Chance de cada nova: 1 em 10.\nNiveis e frequencia mantidos.\f'
    'De dia, as tabelas originais.\nA noite: 20:00 a 05:59.'
)
DAY_TEXT='GUIA DE HORARIOS\nAgora: DIA - 06:00 a 19:59.\f'+COMMON_GUIDE
NIGHT_TEXT='GUIA DE HORARIOS\nAgora: NOITE - 20:00 a 05:59.\f'+COMMON_GUIDE

class PatchError(ValueError): pass

def digest(data): return hashlib.sha256(data).hexdigest()

def encode(text):
    # Native paragraph/page delimiter, not an unbounded third text-box line.
    return b'\xfb'.join(v8.encode_ptbr(page)[:-1] for page in text.split('\f'))+b'\xff'

DAY_BYTES=encode(DAY_TEXT)
NIGHT_BYTES=encode(NIGHT_TEXT)
TEXT_BYTES=DAY_BYTES+NIGHT_BYTES

def script_bytes():
    # Preserve original Route 1 label/directions first. Then evaluate time once.
    prefix=ORIGINAL_MESSAGE+b'\x23'+struct.pack('<I',ENTRY_SIGN)+b'\x21'+struct.pack('<HH',0x800D,1)
    def msg(address): return b'\x0f\x00'+struct.pack('<I',address)+b'\x09\x03\x02'
    day=msg(0x08000000+TEXT_OFFSET)
    branch=b'\x06\x01'+struct.pack('<I',0x08000000+SCRIPT_OFFSET+len(prefix)+6+len(day))
    return prefix+branch+day+msg(0x08000000+TEXT_OFFSET+len(DAY_BYTES))

SCRIPT_BYTES=script_bytes()
PATCH_RANGES=((HOOK_OFFSET,8),(SIGN_POINTER,4),(PAYLOAD_OFFSET,PAYLOAD_SIZE),
              (TABLE_OFFSET,TABLE_SIZE),(SCRIPT_OFFSET,len(SCRIPT_BYTES)),(TEXT_OFFSET,len(TEXT_BYTES)))

def policy_rows(data=None):
    raw=POLICY_PATH.read_bytes() if data is None else data
    if digest(raw)!=POLICY_SHA256: raise PatchError('Política de encontros divergente')
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    for r in rows:
        for k in ('group','map','slot','day_species','night_species'): r[k]=int(r[k])
    return rows

def pilot_tables(source):
    catalog=wild.load_species()
    all_tables=wild.parse_tables(source,wild.load_maps(),catalog)
    tables={t.map.symbol:t for t in all_tables if t.kind=='land' and t.map.symbol in MAPS}
    rows=policy_rows()
    if set(tables)!=set(MAPS) or len(rows)!=2*len(MAPS): raise PatchError('Expansão incompleta')
    if rows[:8]!=previous.policy_rows(): raise PatchError('Política anterior alterada')
    for name in MAPS:
        t=tables[name]; subset=[r for r in rows if r['map_symbol']==name]
        if sorted(r['slot'] for r in subset)!=[2,3]: raise PatchError('Slots inesperados')
        for r in subset:
            slot=t.slots[r['slot']]
            if (r['group'],r['map'],r['day_species'])!=(t.map.group,t.map.number,slot.species):
                raise PatchError('Mapa ou espécie diurna divergente')
            if slot.chance!=10 or fixed.category(catalog[r['night_species']])!='comum':
                raise PatchError('Chance ou espécie protegida inválida')
    result=bytearray(12*len(MAPS))
    for i,name in enumerate(MAPS):
        t=tables[name]; at=TABLE_OFFSET+len(result)
        struct.pack_into('<IIBBH',result,i*12,0x08000000+t.info_offset,0x08000000+at,t.map.group,t.map.number,0)
        slots=bytearray(source[t.data_offset:t.data_offset+48])
        for r in rows:
            if r['map_symbol']==name: struct.pack_into('<H',slots,r['slot']*4+2,r['night_species'])
        result+=struct.pack('<B3xI',t.encounter_rate,0x08000000+at+8)+slots
    if len(result)!=TABLE_SIZE: raise PatchError('Tamanho de tabelas inesperado')
    return bytes(result)

def guide_csv(source):
    """Reproducible complete day/night pilot, nominal odds before Repel."""
    data=pilot_tables(source);catalog=wild.load_species()
    tables={t.map.symbol:t for t in wild.parse_tables(source,wild.load_maps(),catalog) if t.kind=='land'}
    stream=io.StringIO(newline='');writer=csv.writer(stream,lineterminator='\n')
    writer.writerow(('mapa','grupo','numero','periodo','slot','especie','nome','nivel_min','nivel_max','chance_nominal_pct'))
    for i,name in enumerate(MAPS):
        table=tables[name]
        _,night,g,m,_=struct.unpack_from('<IIBBH',data,i*12)
        for period in ('dia_06:00_19:59','noite_20:00_05:59'):
            for slot in table.slots:
                if period.startswith('dia'):
                    lo,hi,species=slot.min_level,slot.max_level,slot.species
                else:
                    lo,hi,species=struct.unpack_from('<BBH',data,night-0x08000000-TABLE_OFFSET+8+slot.index*4)
                writer.writerow((name,g,m,period,slot.index,species,catalog[species].name,lo,hi,slot.chance))
    return stream.getvalue()

def changes(source,payload=None):
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256: raise PatchError('Entrada não é motor_v20 exato')
    payload=PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=PAYLOAD_SIZE or digest(payload)!=PAYLOAD_SHA256: raise PatchError('Payload inválido')
    if source[PAYLOAD_OFFSET:RESERVED_LIMIT]!=b'\xff'*(RESERVED_LIMIT-PAYLOAD_OFFSET): raise PatchError('Reserva ocupada')
    if source[HOOK_OFFSET:HOOK_OFFSET+8]!=HOOK_BEFORE: raise PatchError('Hook nativo divergente')
    if struct.unpack_from('<I',source,SIGN_POINTER)[0]!=SIGN_BEFORE: raise PatchError('Placa divergente')
    if source[previous.SCRIPT_OFFSET:previous.SCRIPT_OFFSET+len(previous.SCRIPT_BYTES)]!=previous.SCRIPT_BYTES: raise PatchError('Script da placa divergente')
    if source[previous.SIGN_BEFORE-0x08000000:previous.SIGN_BEFORE-0x08000000+9]!=ORIGINAL_MESSAGE+b'\x02': raise PatchError('Direções originais divergentes')
    if TEXT_OFFSET+len(TEXT_BYTES)>RESERVED_LIMIT or SCRIPT_OFFSET+len(SCRIPT_BYTES)>TEXT_OFFSET: raise PatchError('Reserva excedida')
    return ((HOOK_OFFSET,struct.pack('<HHI',0x4B00,0x4718,ENTRY_ENCOUNTER)),
            (SIGN_POINTER,struct.pack('<I',0x08000000+SCRIPT_OFFSET)),(PAYLOAD_OFFSET,payload),
            (TABLE_OFFSET,pilot_tables(source)),(SCRIPT_OFFSET,SCRIPT_BYTES),(TEXT_OFFSET,TEXT_BYTES))

def build(source,payload=None):
    out=bytearray(source)
    for at,data in changes(source,payload): out[at:at+len(data)]=data
    result=bytes(out)
    if digest(result)!=OUTPUT_SHA256: raise PatchError('Hash final divergente')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--saida',type=Path,required=True)
    args=parser.parse_args()
    result=build(args.rom.read_bytes());write_new_file(args.rom,args.saida,result)
    print(f'{args.saida}: {len(result)} B SHA-256 {digest(result)}')

if __name__=='__main__': main()
