#!/usr/bin/env python3
"""Read-only ferry/legendary event evidence on exact v41, not a campaign certificate."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v41 as release,auditar_obtencao_v40 as maps

def require(ok,msg):
    if not ok:raise ValueError(msg)

def audit(b):
    require(len(b)==0x2000000 and release.digest(b)==release.OUTPUT_SHA256,'Not exact v41')
    hdr,ev,_=maps.map_data(b,3,5);obj=maps.pointer(b,ev+4)+5*24
    require(b[obj]==6 and maps.u32(b,obj+16)==0x0818F32D,'Ferry object/root changed')
    require(b[0x18F32D:0x18F33A]==bytes.fromhex('6a 5a 21 7e 40 03 00 06 01 82 f3 18 08'),'Ferry scene branch changed')
    require(b[0x18F382:0x18F392]==bytes.fromhex('16 04 80 00 00 21 76 40 05 00 06 04 a7 f3 18 08'),'Rainbow progress branch changed')
    require(b[0x18F392:0x18F39D]==bytes.fromhex('21 76 40 01 00 06 04 27 f5 18 08'),'Tri-pass branch changed')
    tickets=[]
    for item,flag,root,gift,grant,received in ((370,0x84A,0x18F344,0x8797E1,0x87982A,0x2A8),(371,0x84B,0x18F363,0x879611,0x879651,0x2A7)):
        gate=(b'\x2B'+struct.pack('<H',flag)+bytes.fromhex('06 00 b7 08 1d 08 47')+struct.pack('<HH',item,1)
              +bytes.fromhex('21 0d 80 00 00 06 01 b7 08 1d 08 05 b1 08 1d 08 02'))
        require(b[root:root+len(gate)]==gate,'Ticket AND flag gate changed')
        require(b[gift:gift+7]==b'\xB8'+struct.pack('<I',0x08000000+gift)+b'\x6A\x5A','Mystery Event root changed')
        data=(b'\x1A\x00\x80'+struct.pack('<H',item)+bytes.fromhex('1a 01 80 01 00 09 00 29')
              +struct.pack('<H',flag)+b'\x29'+struct.pack('<H',received))
        require(b[grant:grant+len(data)]==data,'Gift grant changed')
        tickets.append(dict(item=item,name='Mystic Ticket' if item==370 else 'Aurora Ticket',flag=f'{flag:04X}',
            predicate_offset=f'{root:08X}',gift_root=f'{gift:08X}',grant_offset=f'{grant:08X}',received_flag=f'{received:04X}',
            normal_gift_delivery_verified=False))
    # Actual reachable call sites in the Rainbow ferry branch, not raw searches.
    require(b[0x18F3B8:0x18F3BD]==bytes.fromhex('04 44 f3 18 08'),'Mystic predicate call changed')
    require(b[0x18F3C8:0x18F3CD]==bytes.fromhex('04 63 f3 18 08'),'Aurora predicate call changed')
    native=[x for x in maps.native_events(b) if x['species'] in (249,250,386)]
    return dict(version='v41',rom_sha256=release.OUTPUT_SHA256,read_only=True,
        ferry=dict(map='VermilionCity',group=3,number=5,object=6,x=24,y=33,root='0018F32D',
            scene_variable='407E',scene_value=3,islands_variable='4076',special_destinations_minimum=5,
            menus=dict(navel=54,birth=55,both=56,tri_pass=57)),tickets=tickets,native_events=native,
        normal_ticket_acquisition_verified=False,full_campaign_certified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);a=p.parse_args()
    b=a.rom.read_bytes();result=audit(b);a.saida.parent.mkdir(parents=True,exist_ok=True)
    with a.saida.open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
    require(a.rom.read_bytes()==b,'ROM changed')
    print('Exact v41; two ticket+flag predicates, ferry progression branches and three native events verified structurally.')
if __name__=='__main__':main()
