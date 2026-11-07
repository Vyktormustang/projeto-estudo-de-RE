"""Encounter data/payload for v39. The complete release is motor_v39.py."""
from __future__ import annotations
import csv,hashlib,io,struct
from pathlib import Path
from scripts import motor_v38_encontros as previous, motor_v38 as base, encontros_selvagens as wild, eventos_fixos as fixed
ROOT=Path(__file__).resolve().parents[1]
BASE_SHA256=base.OUTPUT_SHA256
PAYLOAD_PATH=ROOT/'patches/motor_v39/payload.bin'
PAYLOAD_SHA256='3be6658a6340b27a7b2070dedf61f75e8fa85bce131ec63a9a9b0d449e2de327'
PAYLOAD_SIZE=296
POLICY_PATH=ROOT/'data/encontros_horario_v39.csv'
POLICY_SHA256='d8a12087ec21492fc29f32eeffcff6577748fb271467997ccb81531283039c95'
PAYLOAD_OFFSET=0x1125000
TABLE_OFFSET=0x1126000
RESERVED_LIMIT=0x1128000
ENTRY_SELECT=0x09125001
ENTRY_ENCOUNTER=0x09125009
ENTRY_NIGHT=0x09125011
ENTRY_SIGN=0x09125019
HOOK_OFFSET=previous.HOOK_OFFSET
SIGN_POINTER=previous.SIGN_POINTER
NATIVE_PROLOGUE=previous.NATIVE_PROLOGUE
ORIGINAL_MESSAGE=previous.ORIGINAL_MESSAGE
HOOK_BEFORE=struct.pack('<HHI',0x4B00,0x4718,previous.ENTRY_ENCOUNTER)
MAPS=previous.MAPS+('MAP_CERULEAN_CAVE_1F', 'MAP_CERULEAN_CAVE_2F', 'MAP_CERULEAN_CAVE_B1F', 'MAP_SEAFOAM_ISLANDS_1F')
TABLE_SIZE=len(MAPS)*68
SLOT_EXCEPTIONS={'MAP_ROUTE13':(3,4),'MAP_POKEMON_MANSION_1F':(3,4),'MAP_POKEMON_MANSION_3F':(3,4),'MAP_POKEMON_MANSION_B1F':(2,4),'MAP_VICTORY_ROAD_3F':(3,4),'MAP_SEAFOAM_ISLANDS_B2F':(2,5),'MAP_SEAFOAM_ISLANDS_B3F':(2,4),'MAP_SEAFOAM_ISLANDS_B4F':(3,4),'MAP_MT_EMBER_RUBY_PATH_1F':(3,4),'MAP_MT_EMBER_RUBY_PATH_B3F':(2,4),'MAP_SEAFOAM_ISLANDS_1F':(3,4)}
EXPECTED_SLOTS={name:SLOT_EXCEPTIONS.get(name,(2,3)) for name in MAPS}
class PatchError(ValueError):pass

def digest(data): return hashlib.sha256(data).hexdigest()

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
    if rows[:2*len(previous.MAPS)]!=previous.policy_rows(): raise PatchError('Política anterior alterada')
    for name in MAPS:
        t=tables[name]; subset=[r for r in rows if r['map_symbol']==name]
        if sorted(r['slot'] for r in subset)!=list(EXPECTED_SLOTS[name]): raise PatchError('Slots inesperados')
        for r in subset:
            slot=t.slots[r['slot']]
            if (r['group'],r['map'],r['day_species'])!=(t.map.group,t.map.number,slot.species):
                raise PatchError('Mapa ou espécie diurna divergente')
            if slot.chance!=10 or any((r[k]==143 or fixed.category(catalog[r[k]])!='comum') for k in ('day_species','night_species')):
                raise PatchError('Chance ou espécie protegida inválida')
        replacements={r['night_species'] for r in subset}
        retained={slot.species for slot in t.slots if slot.index not in EXPECTED_SLOTS[name]}
        if len(replacements)!=2 or replacements & retained:
            raise PatchError('Espécie noturna duplicada em slots mantidos')
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
    """Reproducible complete day/night distribution, nominal odds before Repel."""
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

PATCH_RANGES=((HOOK_OFFSET,8),(PAYLOAD_OFFSET,PAYLOAD_SIZE),(TABLE_OFFSET,TABLE_SIZE))
def changes(source,payload=None):
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:raise PatchError('Entrada não é motor_v38 exato')
    payload=PAYLOAD_PATH.read_bytes() if payload is None else payload
    if len(payload)!=PAYLOAD_SIZE or digest(payload)!=PAYLOAD_SHA256:raise PatchError('Payload divergente')
    if source[PAYLOAD_OFFSET:RESERVED_LIMIT]!=b'\xff'*(RESERVED_LIMIT-PAYLOAD_OFFSET):raise PatchError('Reserva ocupada')
    if source[HOOK_OFFSET:HOOK_OFFSET+8]!=HOOK_BEFORE:raise PatchError('Hook divergente')
    if PAYLOAD_OFFSET+len(payload)>TABLE_OFFSET or TABLE_OFFSET+TABLE_SIZE>RESERVED_LIMIT:raise PatchError('Reserva excedida')
    return ((HOOK_OFFSET,struct.pack('<HHI',0x4B00,0x4718,ENTRY_ENCOUNTER)),(PAYLOAD_OFFSET,payload),(TABLE_OFFSET,pilot_tables(source)))
