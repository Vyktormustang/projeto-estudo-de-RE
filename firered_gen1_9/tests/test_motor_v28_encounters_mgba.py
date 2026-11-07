"""Native generation and UI on exact v28, synthetic states only.

Quantile tests cover all 100 slot-selection rolls, not a claim of measured
encounter frequencies from 100 natural walks. Direct contracts and live flows
are named separately. No RAM is edited during a live action.
"""
import os
import struct
import tempfile
import unittest
from pathlib import Path
from collections import Counter
from scripts import motor_v27 as p, motor_v28 as release
from mgba_treino_harness import Emulator,offset,u32,put32,mon,mon_facts,PARTY
from test_golpes_gen9_mgba import set_registers,SENTINEL,seed_mon
from test_eventos_fixos_mgba import route_entry_fixture,route_from_entry,enemy,OBJECTS
from test_motor_v19_mgba import set_time,IW
import test_motor_v19_mgba as clock
from test_estojo_expandido_mgba import save1
from battle_fixture_helpers import in_battle,main_callback2

ROM=os.environ.get('MOTOR_V28_ROM');CORE=os.environ.get('MGBA_CORE')
RNG=IW+0x6FC8
ENEMY=offset(0x0203A734)
RESULT=offset(0x02021AAC)
ORIGINAL=0x090EC020
# One seed per first LCG roll modulo 100. Verify against native outcomes below.
SEEDS={}
for _seed in range(10000):
    _q=(((_seed*0x41C64E6D+0x6073)&0xFFFFFFFF)>>16)%100
    SEEDS.setdefault(_q,_seed)
    if len(SEEDS)==100:break

def prepare(cls):
    cls.rom=Path(ROM)
    cls.source=cls.rom.read_bytes()
    if p.digest(cls.source)!=release.OUTPUT_SHA256:raise ValueError('Not exact v28')
    cls.temp=tempfile.TemporaryDirectory()
    cls.f=Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
    cls.fixture=route_entry_fixture(cls.f)

def finish(cls):
    cls.f.close();cls.temp.cleanup()
    if p.digest(cls.rom.read_bytes())!=release.OUTPUT_SHA256:raise AssertionError('ROM changed')

@unittest.skipUnless(ROM and CORE,'set MOTOR_V28_ROM and MGBA_CORE')
class MotorV28EncounterTests(unittest.TestCase):
    setUpClass=classmethod(prepare)
    tearDownClass=classmethod(finish)

    def record(self,i):return struct.unpack_from('<IIBBH',self.source,p.TABLE_OFFSET+12*i)
    def state(self,i,t):
        st=set_time(self.fixture,t);_,_,g,m,_=self.record(i)
        st[offset(save1(st))+4:offset(save1(st))+6]=bytes((g,m))
        return st
    def call(self,st,pc,regs=None):
        self.f.restore(set_registers(st,pc&~1,regs or {}));self.f.run(3)
        out=self.f.state()
        # Native high-level mon generation can exceed the older 3-frame budget.
        if u32(out,0x5c)!=SENTINEL+2:self.f.run(30);out=self.f.state()
        self.assertEqual(u32(out,0x5c),SENTINEL+2)
        return out

    def canonical_enemy(self,state):
        data=bytearray(state[ENEMY:ENEMY+600])
        # Native creation leaves nickname bytes AFTER EOS unspecified. Different
        # call-stack depth changes that padding, not the visible name/mon data.
        for i in range(6):
            start=100*i+8;end=start+10
            if 255 in data[start:end]:
                eos=data.index(255,start,end);data[eos+1:end]=bytes(end-eos-1)
        return bytes(data)

    def test_selector_boundaries_maps_area_guards_and_no_rng_or_save_writes(self):
        for i in range(len(p.MAPS)):
            day,night,_,_,_=self.record(i)
            for t in (0,359,360,479,480,1079,1080,1199,1200,1439):
                st=self.state(i,t)
                out=self.call(st,p.ENTRY_SELECT,{0:day,1:0})
                self.assertEqual(u32(out,0x20),night if t<360 or t>=1200 else day)
                self.assertEqual(out[RNG:RNG+4],st[RNG:RNG+4])
                at=offset(save1(st));self.assertEqual(out[at:at+0x3668],st[at:at+0x3668])
            for area in (1,2,3,255):
                self.assertEqual(u32(self.call(self.state(i,1320),p.ENTRY_SELECT,{0:day,1:area}),0x20),day)
            st=self.state(i,1320);st[offset(save1(st))+5]^=1
            self.assertEqual(u32(self.call(st,p.ENTRY_SELECT,{0:day,1:0}),0x20),day)
            self.assertEqual(u32(self.call(self.state(i,1320),p.ENTRY_SELECT,{0:night,1:0}),0x20),night)
        for pointer in (0,0x03000000,0x02000001,0x0203FFFC):
            st=self.state(0,1320);put32(st,IW+0x6F94,pointer)
            day=self.record(0)[0]
            self.assertEqual(u32(self.call(st,p.ENTRY_SELECT,{0:day,1:0}),0x20),day)

    def test_all_100_native_slot_rolls_twenty_maps_day_night_levels_and_checksums(self):
        self.assertEqual(len(SEEDS),100)
        thresholds=(20,40,50,60,70,80,85,90,94,98,99,100)
        for i,name in enumerate(p.MAPS):
            day,night,*_=self.record(i)
            for minute,ptr in ((600,day),(1320,night)):
                slots=struct.unpack_from('<I',self.source,ptr-0x08000000+4)[0]-0x08000000
                counts=Counter()
                for q in range(100):
                    slot=next(j for j,end in enumerate(thresholds) if q<end)
                    lo,hi,species=struct.unpack_from('<BBH',self.source,slots+slot*4)
                    st=self.state(i,minute);put32(st,RNG,SEEDS[q])
                    regs={0:day,1:0,2:0,**{r:0xBAD000+r for r in range(4,12)}}
                    out=self.call(st,0x08000000+p.HOOK_OFFSET,regs)
                    facts=enemy(out)
                    self.assertEqual(u32(out,0x20),1)
                    self.assertTrue(facts['valid'])
                    self.assertEqual(facts['species'],species,(name,minute,q,slot))
                    self.assertTrue(lo<=facts['level']<=hi)
                    for r in range(4,12):self.assertEqual(u32(out,0x20+r*4),regs[r])
                    self.assertEqual(u32(out,0x54),0x03007E00)
                    counts[species]+=1
                    if minute==600:
                        original=self.call(st,ORIGINAL,regs)
                        self.assertEqual(self.canonical_enemy(out),self.canonical_enemy(original))
                        self.assertEqual(out[RNG:RNG+4],original[RNG:RNG+4])
                    elif i<16:
                        prior=self.call(st,p.previous.ENTRY_ENCOUNTER,regs)
                        self.assertEqual(self.canonical_enemy(out),self.canonical_enemy(prior))
                        self.assertEqual(out[RNG:RNG+4],prior[RNG:RNG+4])
                if minute==1320:
                    for row in p.policy_rows():
                        if row['map_symbol']==name:self.assertEqual(counts[row['night_species']],10)

    def test_repel_still_blocks_lower_levels_but_unchecked_generation_works(self):
        for i in range(len(p.MAPS)):
            for t in (600,1320):
                st=self.state(i,t);st=seed_mon(st,1,50,(33,45,0,0))
                st=self.call(st,0x0808EA14,{0:0x4020,1:200})
                day=self.record(i)[0]
                out=self.call(st,0x08000000+p.HOOK_OFFSET,{0:day,1:0,2:1})
                self.assertEqual(u32(out,0x20),0)
                self.assertEqual(out[ENEMY:ENEMY+600],st[ENEMY:ENEMY+600])
                out=self.call(st,0x08000000+p.HOOK_OFFSET,{0:day,1:0,2:0})
                self.assertEqual(u32(out,0x20),1);self.assertTrue(enemy(out)['valid'])

    def test_water_and_nonpilot_cave_generation_identical_to_native_at_night(self):
        tables=p.wild.parse_tables(self.source,p.wild.load_maps(),p.wild.load_species())
        for symbol,kind,area in (('MAP_ROUTE22','water',1),('MAP_ROUTE4','water',1),('MAP_ROUTE24','water',1),('MAP_ROUTE25','water',1),('MAP_ROUTE6','water',1),('MAP_ROUTE10','water',1),('MAP_ROUTE11','water',1),('MAP_ROUTE12','water',1),('MAP_ROUTE17','land',0),('MAP_MT_MOON_1F','land',0)):
            t=next(x for x in tables if x.map.symbol==symbol and x.kind==kind)
            st=set_time(self.fixture,1320)
            st[offset(save1(st))+4:offset(save1(st))+6]=bytes((t.map.group,t.map.number))
            regs={0:0x08000000+t.info_offset,1:area,2:0}
            for seed in (0,1,2,3,200):
                put32(st,RNG,seed)
                out=self.call(st,0x08000000+p.HOOK_OFFSET,regs);old=self.call(st,ORIGINAL,regs)
                self.assertEqual(self.canonical_enemy(out),self.canonical_enemy(old))
                self.assertEqual(out[RNG:RNG+4],old[RNG:RNG+4])

    def test_sign_native_helper_uses_only_transient_result_not_saved_flags(self):
        for t,want in ((359,1),(360,0),(1199,0),(1200,1)):
            st=set_time(self.fixture,t);out=self.call(st,p.ENTRY_SIGN)
            self.assertEqual(struct.unpack_from('<H',out,RESULT)[0],want)
            at=offset(save1(st));self.assertEqual(out[at:at+0x3668],st[at:at+0x3668])
            read=self.call(out,0x0808E9D4,{0:0x800D});self.assertEqual(u32(read,0x20),want)

    def at_sign(self,minute):
        import test_motor_v24_mgba as v24
        return v24.MotorV24EncounterRegressionTests.at_sign(self,minute)

    def test_live_walking_night_encounter_and_native_sweet_scent_on_route1(self):
        # Choose initial delays only; after restore all input is normal buttons.
        found=set();candidates=[]
        for delay in range(0,180,5):
            self.f.restore(bytes(set_time(self.fixture,1320)));self.f.run(delay)
            route_from_entry(self.f)
            for j in range(100):
                st=self.f.state()
                if in_battle(st):break
                if len(candidates)<200:candidates.append(st)
                self.f.run(4,'LEFT' if j%10<5 else 'RIGHT')
            st=self.f.state()
            if in_battle(st):
                self.f.run(300);st=self.f.state();facts=enemy(st)
                if facts['species'] in (163,827):
                    self.assertTrue(facts['valid']);self.assertEqual(facts['level'],3)
                    found.add(facts['species'])
            if found=={163,827} and candidates:break
        self.assertEqual(found,{163,827})
        # Native SweetScent entry, not a complete field-move menu interaction.
        # The walking path includes non-grass tiles; native return 0 is correct
        # there. Try independently recorded field states until reaching grass.
        generated=False
        for original in candidates:
            st=bytearray(original);put32(st,RNG,SEEDS[40])
            out=self.call(st,0x081647A4)
            if u32(out,0x20)==1:
                self.assertEqual(enemy(out)['species'],163)
                self.assertTrue(enemy(out)['valid']);generated=True;break
        self.assertTrue(generated,'No recorded field state reached a grass tile')

    def grass_site(self,group,number):
        """Read this ROM's terrain, not coordinates borrowed from vanilla FR.

        Attribute index 4: mask 07000000, shift 24; LAND=1, WATER=2,
        independently checked by the native MapGridGetMetatileAttributeAt.
        Select a grass line with neighbors for walking, away from NPCs.
        """
        b=self.source
        def ptr(at):return struct.unpack_from('<I',b,at)[0]-0x08000000
        hdr=ptr(ptr(p.fixed.GROUP_TABLE+4*group)+4*number);layout=ptr(hdr)
        self.assertEqual(b[hdr+23],3)
        w,h=struct.unpack_from('<II',b,layout);grid=ptr(layout+12)
        primary=ptr(ptr(layout+16)+20);secondary=ptr(ptr(layout+20)+20)
        grass=set()
        for y in range(1,h-1):
            for x in range(1,w-1):
                tile=struct.unpack_from('<H',b,grid+2*(y*w+x))[0];n=tile&1023
                attr=struct.unpack_from('<I',b,primary+4*n if n<640 else secondary+4*(n-640))[0]
                if ((attr>>24)&7)==1 and not (tile&0xC00):grass.add((x,y))
        ev=ptr(hdr+4);objects=ptr(ev+4);npcs=[]
        for i in range(b[ev]):
            x,y=struct.unpack_from('<hh',b,objects+24*i+4)
            if x>=0 and y>=0:npcs.append((x,y))
        candidates=[]
        for x,y in sorted(grass):
            for dx,dy,buttons in ((1,0,('LEFT','RIGHT')),(0,1,('UP','DOWN'))):
                if (x-dx,y-dy) in grass and (x+dx,y+dy) in grass:
                    score=min((abs(x-nx)+abs(y-ny) for nx,ny in npcs),default=999)
                    candidates.append((-score,y,x,buttons))
        self.assertTrue(candidates,(group,number))
        _,y,x,buttons=min(candidates)
        return x,y,buttons

    def test_live_new_routes_night_species_after_test_only_warps(self):
        # ONLY the journey is shortened: a temporary copy's sign performs a
        # warp. Wild tables, RNG, level and encounter code stay production-exact.
        # No personal save, no injected encounter, no writes during walking.
        try:
            for i,name in enumerate(p.MAPS[16:],start=16):
                with self.subTest(map=name):
                    day,night,group,number,_=self.record(i)
                    x,y,buttons=self.grass_site(group,number)
                    data=bytearray(self.source)
                    self.assertEqual(data[0xF90000:0xF9000A],b'\xff'*10)
                    self.assertEqual(struct.unpack_from('<I',data,p.SIGN_POINTER)[0],0x08000000+release.SCRIPT_OFFSET)
                    struct.pack_into('<I',data,p.SIGN_POINTER,0x08F90000)
                    data[0xF90000:0xF9000A]=struct.pack('<BBBBHHBB',0x39,group,number,255,x,y,0x27,2)
                    restored=bytearray(data)
                    for at,n in ((p.SIGN_POINTER,4),(0xF90000,10)):restored[at:at+n]=self.source[at:at+n]
                    self.assertEqual(bytes(restored),self.source)
                    path=Path(self.temp.name)/f'warp_only_{group}_{number}.gba';path.write_bytes(data)
                    self.f.close();self.f=Emulator(path,Path(CORE),Path(self.temp.name));type(self).f=self.f
                    self.at_sign(1320);self.f.pulse('A',150);self.f.run(150)
                    arrived=self.f.state();saved=offset(save1(arrived))
                    self.assertEqual(arrived[saved+4:saved+6],bytes((group,number)))
                    self.assertFalse(in_battle(arrived))
                    self.assertEqual(struct.unpack_from('<hh',arrived,offset(OBJECTS)+16),(x+7,y+7))
                    terrain=self.call(arrived,0x080BB808,{0:x+7,1:y+7,2:4})
                    self.assertEqual(u32(terrain,0x20),1)
                    targets={r['night_species']:r['slot'] for r in p.policy_rows() if r['map_symbol']==name}
                    seen=set()
                    for delay in range(96):
                        self.f.restore(arrived);self.f.run(delay)
                        for step in range(100):
                            self.f.run(8,buttons[(step//2)%2])
                            if in_battle(self.f.state()):break
                        out=self.f.state()
                        if not in_battle(out):continue
                        self.f.run(300);out=self.f.state()
                        self.assertEqual(u32(out,offset(0x02020374))&8,0,'Unexpected trainer battle')
                        facts=enemy(out)
                        if facts['species'] in targets:
                            slot=targets[facts['species']]
                            array=struct.unpack_from('<I',self.source,day-0x08000000+4)[0]-0x08000000
                            lo,hi=struct.unpack_from('<BB',self.source,array+4*slot)
                            self.assertTrue(facts['valid']);self.assertTrue(lo<=facts['level']<=hi)
                            seen.add(facts['species'])
                        if seen==set(targets):break
                    self.assertEqual(seen,set(targets),(name,x,y,seen))
        finally:
            self.f.close();self.f=Emulator(self.rom,Path(CORE),Path(self.temp.name));type(self).f=self.f



    def test_postcap_twenty_maps_with_panel_shown_and_hidden(self):
        import test_motor_v24_mgba as v24
        from scripts import motor_v26 as ui
        for hidden in (False,True):
            for minute in (0,359,360,479,480,1079,1080,1199,1200,1439):
                st=v24.saturated(self.fixture,minute,17)
                struct.pack_into('<II',st,offset(save1(st)+ui.PREFERENCE_OFFSET),ui.PREFERENCE_MAGIC,ui.HIDDEN if hidden else ui.VISIBLE)
                for i in range(20):
                    day,night,g,m,_=self.record(i);one=offset(save1(st));st[one+4:one+6]=bytes((g,m))
                    out=self.call(st,p.ENTRY_SELECT,{0:day,1:0})
                    self.assertEqual(u32(out,0x20),night if minute<360 or minute>=1200 else day)
                    self.assertEqual(out[one:one+0x3668],st[one:one+0x3668])
