#!/usr/bin/env python3
"""Read-only inventory of Cosmog's sources and native evolution/breeding data."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v42 as release,auditar_obtencao_v40 as old

SPECIES_INFO=0x69D0C8
SPECIALS=0x188744

def audit(b):
    old.require(len(b)==0x2000000 and release.digest(b)==release.OUTPUT_SHA256,'Not exact V42')
    cat=old.wild.load_species();tables=old.wild.parse_tables(b,old.wild.load_maps(),cat)
    active,parked=old.objects(b,cat)
    wild=[];ditto=[];slots=0
    for t in tables:
        for s in t.slots:
            slots+=1
            row=dict(species=s.species,map=t.map.label,kind=t.kind,offset=s.offset)
            if 789<=s.species<=792:wild.append(row)
            if s.species==132:ditto.append(row)
    night=old.release.previous
    night_slots=0
    for i,name in enumerate(night.MAPS):
        info=old.pointer(b,night.TABLE_OFFSET+i*12+4);table=old.pointer(b,info+4)
        for slot in range(12):
            at=table+4*slot;sid=struct.unpack_from('<H',b,at+2)[0];night_slots+=1
            if 789<=sid<=792:wild.append(dict(species=sid,map=name,kind='night_land',offset=at))
    evos=[x for x in old.evolutions(b) if x['source'] in (789,790,791,792)]
    stats=[]
    for sid in (1,132,151,789,790,791,792):
        at=SPECIES_INFO+sid*28
        stats.append(dict(species=sid,offset=at,gender=b[at+16],egg_cycles=b[at+17],growth=b[at+19],egg_groups=list(b[at+20:at+22])))
    # Literal loaded by native compatibility function 0807F460, not a guessed vanilla table.
    old.require(old.u32(b,0x7F578)==0x08000000+SPECIES_INFO,'Breeding table reference changed')
    old.require(old.u32(b,0x7F5D4)==0x2FCC,'Day Care save layout changed')
    for idx,pointer in ((0xB4,0x080B4819),(0xB6,0x0807F3A1),(0xB8,0x0807F151),(0xB9,0x0807F599),(0xBB,0x0807E39D)):
        old.require(old.u32(b,SPECIALS+idx*4)==pointer,'Special dispatch changed')
    return dict(version='v42',rom_sha256=release.OUTPUT_SHA256,read_only=True,
        wild_slots_inspected=slots,night_slots_inspected=night_slots,wild_line_locations=wild,ditto_table_locations=ditto,
        active_line_events=[x for x in active if 789<=x['species']<=792],
        parked_line_events=[x for x in parked if 789<=x['species']<=792],
        selected_native_line_events=[x for x in old.native_events(b) if 789<=x['species']<=792],
        evolutions=evos,species_info=stats,
        native=dict(special_table=hex(SPECIALS),compatibility=hex(0x0807F460),compatibility_wrapper=hex(0x0807F57C),
            compatibility_table_literal=hex(0x0807F578),daycare_save_offset=hex(0x2FCC),give_egg=hex(0x0807F150),party_cursor=hex(0x0203A6DD)),
        limitations=['Not an exhaustive gift/trade/reset script search','Table inventory does not prove map access','Native contracts are not deposit/egg pickup/hatching journeys'])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);a=p.parse_args()
    b=a.rom.read_bytes();data=audit(b);a.saida.parent.mkdir(parents=True,exist_ok=True)
    with a.saida.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
    old.require(a.rom.read_bytes()==b,'ROM changed')
if __name__=='__main__':main()
