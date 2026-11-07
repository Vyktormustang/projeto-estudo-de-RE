#!/usr/bin/env python3
"""Piloto de encontros noturnos e placa informativa, sobre v19 exata."""
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
from scripts import motor_v19 as v19, motor_v8 as v8, encontros_selvagens as wild, eventos_fixos as fixed
from scripts.treino_ev import write_new_file

BASE_SHA256=v19.OUTPUT_SHA256
OUTPUT_SHA256='6f22c85769de8fc083b72edd491e185c2baee9ef0fc23f174c25f31d3200ee23'
PAYLOAD_PATH=ROOT/'patches/motor_v20/payload.bin'
PAYLOAD_SHA256='2ca3afe13ff00cb601727ea8a6c83091cec8d6a7a324689edee8cfdb44a639e1'
PAYLOAD_SIZE=300
POLICY_PATH=ROOT/'data/encontros_horario_v20.csv'
POLICY_SHA256='dda1acd41ce3a2c4c6dae418205e1970c0e524f856eb93962d90d3b3ed15bd7d'
PAYLOAD_OFFSET=0x10DE000
TABLE_OFFSET=0x10DF000
SCRIPT_OFFSET=0x10DF200
TEXT_OFFSET=0x10DF400
RESERVED_LIMIT=0x10E0000
ENTRY_SELECT=0x090DE001
ENTRY_ENCOUNTER=0x090DE009
ENTRY_NIGHT=0x090DE011
ENTRY_SIGN=0x090DE019
HOOK_OFFSET=0x164340
HOOK_BEFORE=bytes.fromhex('f0b54746ce460906')
SIGN_POINTER=0x7C20D8
SIGN_BEFORE=0x08190947
ORIGINAL_MESSAGE=bytes.fromhex('0f0020c21a080903')
MAPS=('MAP_ROUTE1','MAP_ROUTE2','MAP_ROUTE22','MAP_VIRIDIAN_FOREST')
COMMON_GUIDE=(
    'Na grama destas quatro areas,\nos encontros mudam a noite.\f'
    'Rota 1: Hoothoot / Nickit.\nRota 2: Poochyena / Houndour.\f'
    'Floresta: Spinarak / Morelull.\nRota 22: Murkrow / Greavard.\f'
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
              (TABLE_OFFSET,272),(SCRIPT_OFFSET,len(SCRIPT_BYTES)),(TEXT_OFFSET,len(TEXT_BYTES)))

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
    if set(tables)!=set(MAPS) or len(rows)!=8: raise PatchError('Piloto incompleto')
    for name in MAPS:
        t=tables[name]; subset=[r for r in rows if r['map_symbol']==name]
        if sorted(r['slot'] for r in subset)!=[2,3]: raise PatchError('Slots inesperados')
        for r in subset:
            slot=t.slots[r['slot']]
            if (r['group'],r['map'],r['day_species'])!=(t.map.group,t.map.number,slot.species):
                raise PatchError('Mapa ou espécie diurna divergente')
            if slot.chance!=10 or fixed.category(catalog[r['night_species']])!='comum':
                raise PatchError('Chance ou espécie protegida inválida')
    result=bytearray(48)
    for i,name in enumerate(MAPS):
        t=tables[name]; at=TABLE_OFFSET+len(result)
        struct.pack_into('<IIBBH',result,i*12,0x08000000+t.info_offset,0x08000000+at,t.map.group,t.map.number,0)
        slots=bytearray(source[t.data_offset:t.data_offset+48])
        for r in rows:
            if r['map_symbol']==name: struct.pack_into('<H',slots,r['slot']*4+2,r['night_species'])
        result+=struct.pack('<B3xI',t.encounter_rate,0x08000000+at+8)+slots
    if len(result)!=272: raise PatchError('Tamanho de tabelas inesperado')
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
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256: raise PatchError('Entrada não é motor_v19 exato')
    payload=PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=PAYLOAD_SIZE or digest(payload)!=PAYLOAD_SHA256: raise PatchError('Payload inválido')
    if source[PAYLOAD_OFFSET:RESERVED_LIMIT]!=b'\xff'*(RESERVED_LIMIT-PAYLOAD_OFFSET): raise PatchError('Reserva ocupada')
    if source[HOOK_OFFSET:HOOK_OFFSET+8]!=HOOK_BEFORE: raise PatchError('Hook nativo divergente')
    if struct.unpack_from('<I',source,SIGN_POINTER)[0]!=SIGN_BEFORE: raise PatchError('Placa divergente')
    if source[SIGN_BEFORE-0x08000000:SIGN_BEFORE-0x08000000+9]!=ORIGINAL_MESSAGE+b'\x02': raise PatchError('Script da placa divergente')
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
