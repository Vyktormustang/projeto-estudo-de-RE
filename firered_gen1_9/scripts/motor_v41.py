#!/usr/bin/env python3
"""Make Type: Null available in every Altering Cave variant; exact v40 input.

Eight redundant common slots become Type: Null Lv20 (10% each). Variant 7,
all other slots, map scripts, progression, clock, guide and save code stay intact.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v40 as base,encontros_selvagens as wild,eventos_fixos as fixed
from scripts.treino_ev import write_new_file
BASE_SHA256=base.OUTPUT_SHA256
OUTPUT_SHA256='662225325c50af5aeb568da97a10110cff300aff55e1a6ec87f0d11c1a5f5d50'
SPECIES=772
LEVEL=20
VARIANT_HEADERS=tuple(range(123,132))
ORIGINAL_VARIANT=7
NEW_SLOT=3
OLD_SPECIES=(41,179,204,228,216,190,213,234,235)
OLD_LEVELS=(14,11,27,20,26,26,26,26,26)
PATCH_RANGES=tuple((0x7B7660+56*v,4) for v in range(9) if v!=ORIGINAL_VARIANT)

class PatchError(ValueError):pass

def digest(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok:raise PatchError(msg)

def tables(b):
    fixed.checked_catalogs()
    ts=wild.parse_tables(b,wild.load_maps(),wild.load_species())
    return [t for t in ts if t.kind=='land' and t.map.symbol=='MAP_SIX_ISLAND_ALTERING_CAVE']

def validate_tables(b,patched=False):
    ts=tables(b);require(tuple(t.map.index for t in ts)==VARIANT_HEADERS,'Unexpected cave headers')
    for v,t in enumerate(ts):
        require((t.map.group,t.map.number,t.encounter_rate)==(1,122,5),'Unexpected map/rate')
        slot=t.slots[NEW_SLOT]
        require(slot.offset==0x7B7660+56*v and slot.chance==10,'Unexpected slot')
        expected=(SPECIES,LEVEL,LEVEL) if patched and v!=7 else (OLD_SPECIES[v],OLD_LEVELS[v],OLD_LEVELS[v])
        require((slot.species,slot.min_level,slot.max_level)==expected,'Unexpected slot contents')
        require(any(s.species==OLD_SPECIES[v] for s in t.slots if s.index!=NEW_SLOT),'Would remove common species')
        targets=[s for s in t.slots if s.species==SPECIES]
        if patched or v==7:
            require(len(targets)==1 and (targets[0].min_level,targets[0].max_level,targets[0].chance)==(20,20,10),'Wrong Type: Null distribution')
        else:require(not targets,'Unexpected existing Type: Null')
    return ts

def trace_variant_mechanism(b):
    """Verify actual command boundaries of the relocatable Mystery Event script.

    A script present in ROM does NOT establish normal access to its delivery.
    The cave has no objects/coordinate/background events, only an exit warp.
    """
    from scripts.auditar_obtencao_v40 import map_data,u32
    hdr,ev,_=map_data(b,1,122)
    require(tuple(b[ev:ev+4])==(0,1,0,0),'Cave event layout changed')
    scripts=u32(b,hdr+8)-0x08000000
    require(scripts==0x18D090 and b[scripts:scripts+10]==bytes.fromhex('03 96 d0 18 08 00 d0 be 08 02'),
            'Unexpected cave map script (only on-transition world-map flag expected)')
    at=0x8799BA
    expected=(b'\xB8'+struct.pack('<I',0x08000000+at)+b'\x17\x24\x40\x01\x00'
              +b'\x21\x24\x40\x0A\x00'+b'\xBB\x00'+struct.pack('<I',0x088799D4)
              +b'\x16\x24\x40\x00\x00\x6A\x5A\xBD'+struct.pack('<I',0x088799DF)+b'\x66\x6D\x6C\x02')
    require(b[at:at+len(expected)]==expected,'Mystery Event script differs')
    return dict(script_offset=f'{at:08X}',variable='4024',increment=1,reset_at=10,
                cave_objects=0,cave_coordinate_events=0,cave_background_events=0,
                normal_delivery_verified=False)

def build(source):
    require(len(source)==0x2000000 and digest(source)==BASE_SHA256,'Not exact v40')
    validate_tables(source);trace_variant_mechanism(source)
    result=bytearray(source)
    for at,n in PATCH_RANGES:struct.pack_into('<BBH',result,at,LEVEL,LEVEL,SPECIES)
    result=bytes(result);validate_tables(result,True)
    restored=bytearray(result)
    for at,n in PATCH_RANGES:restored[at:at+n]=source[at:at+n]
    require(bytes(restored)==source,'Unexpected changed bytes')
    require(digest(result)==OUTPUT_SHA256,'Output hash mismatch')
    return result

def guide_csv(b):
    ts=validate_tables(b,True);catalog=wild.load_species();out=io.StringIO(newline='');w=csv.writer(out,lineterminator='\n')
    w.writerow(('variante','header','mapa','grupo','numero','periodo','slot','especie','nome','nivel_min','nivel_max','chance_nominal_pct','offset'))
    for v,t in enumerate(ts):
        for s in t.slots:w.writerow((v,t.map.index,t.map.label,1,122,'dia_e_noite',s.index,s.species,catalog[s.species].name,s.min_level,s.max_level,s.chance,f'{s.offset:08X}'))
    return out.getvalue()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',required=True,type=Path);p.add_argument('--saida',required=True,type=Path);a=p.parse_args()
    source=a.rom.read_bytes();out=build(source);write_new_file(a.rom,a.saida,out)
    require(a.rom.read_bytes()==source,'Input changed')
    print(f'v41: {len(out)} bytes; SHA-256 {digest(out)}; eight 4-byte records, no code/save changes')
if __name__=='__main__':main()
