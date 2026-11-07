"""Exact v41 contracts and live capture after synthetic arrival/native flash.

No personal saves, no cross-ROM savestates, no edits during walking/capture.
The disposable warp is NOT in the delivered ROM. Full island travel is not tested.
"""
import ctypes as C,json,os,struct,tempfile,unittest
from pathlib import Path
from collections import Counter
from scripts import motor_v41 as p
from mgba_treino_harness import Emulator,offset,u32,put32,mon_facts,VIDEO_CB
from test_motor_v40_encounters_mgba import MotorV40EncounterTests,SEEDS,RNG
from test_auditoria_obtencao_v40_mgba import AcquisitionNativeProbes
from test_motor_v19_mgba import MotorV19ClockTests,set_time
from test_eventos_fixos_mgba import route_entry_fixture,route_from_entry,enemy
from test_estojo_expandido_mgba import save1,add,get
from test_atualizacoes_gen9_mgba import copy_ewram
from test_golpes_gen9_mgba import seed_mon
from test_golpes_gen9_integracao import save_game,load_game
from test_motor_v12_mgba import text
from battle_fixture_helpers import in_battle,main_callback2,BATTLE_OUTCOME
import test_motor_v21_gameplay_mgba as game
ROM=os.environ.get('MOTOR_V41_ROM');BASE=os.environ.get('MOTOR_V41_BASE');CORE=os.environ.get('MGBA_CORE')

@unittest.skipUnless(ROM and BASE and CORE,'set MOTOR_V41_ROM, MOTOR_V41_BASE, MGBA_CORE')
class MotorV41NativeTests(unittest.TestCase):
    call=MotorV40EncounterTests.call
    grass_site=MotorV40EncounterTests.grass_site
    evolution=MotorV19ClockTests.evolution
    state=AcquisitionNativeProbes.state
    generate=AcquisitionNativeProbes.generate
    test_cosmog_threshold_and_everstone_day_and_night=AcquisitionNativeProbes.test_cosmog_threshold_and_everstone_day_and_night
    test_cosmoem_level_priority_not_time_branch_and_everstone=AcquisitionNativeProbes.test_cosmoem_level_priority_not_time_branch_and_everstone
    test_tanoby_flag_gate_and_cresselia_native_generation=AcquisitionNativeProbes.test_tanoby_flag_gate_and_cresselia_native_generation
    throw_first_ball=game.MotorV21GameplayTests.throw_first_ball
    assert_ball_metadata=game.MotorV21GameplayTests.assert_ball_metadata
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM);cls.base=Path(BASE);cls.source=cls.rom.read_bytes()
        if p.digest(cls.source)!=p.OUTPUT_SHA256 or p.digest(cls.base.read_bytes())!=p.BASE_SHA256:raise ValueError('Wrong ROM')
        cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
        cls.f=Emulator(cls.rom,Path(CORE),cls.dir);cls.fixture=route_entry_fixture(cls.f);cls.observations=[]
    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if p.digest(cls.rom.read_bytes())!=p.OUTPUT_SHA256 or p.digest(cls.base.read_bytes())!=p.BASE_SHA256:raise AssertionError('ROM changed')
        dest=os.environ.get('MOTOR_V41_OBSERVATIONS')
        if dest:
            with Path(dest).open('x') as f:json.dump(cls.observations,f,indent=2);f.write('\n')
    def switch(self,rom):
        self.f.close();type(self).f=self.f=Emulator(rom,Path(CORE),self.dir)
    def variant(self,minute,value):return self.call(self.state(1,122,minute),0x0808EA14,{0:0x4024,1:value})

    def test_all_variants_1800_quantiles_plus_invalid_fallback_day_night(self):
        tables=p.validate_tables(self.source,True)
        for minute in (600,1320):
            for value in (*range(9),9,65535):
                st=self.variant(minute,value);header=u32(self.call(st,0x08164160),0x20)
                self.assertEqual(header,123+(value if value<9 else 0));table=tables[header-123]
                counts=Counter()
                for q in range(100):
                    facts=self.generate(st,header,q);limit=0
                    for slot in table.slots:
                        limit+=slot.chance
                        if q<limit:break
                    self.assertEqual((facts['species'],facts['level']),(slot.species,slot.min_level));counts[facts['species']]+=1
                self.assertEqual(counts[772],10)
                self.observations.append(dict(probe='variant_quantiles',minute=minute,value=value,header=header,rolls=100,type_null_rolls=10))

    def test_repel_blocks_type_null_and_unchecked_generation_works(self):
        for minute in (600,1320):
            for v in range(9):
                st=seed_mon(self.variant(minute,v),1,100,(33,45,0,0))
                st=self.call(st,0x0808EA14,{0:0x4020,1:200});st=bytearray(st);put32(st,RNG,SEEDS[40 if v==7 else 50])
                info=0x08000000+p.tables(self.source)[v].info_offset
                before=st[offset(0x0203A734):offset(0x0203A734)+600]
                blocked=self.call(st,0x08000000+p.base.previous.HOOK_OFFSET,{0:info,1:0,2:1})
                self.assertEqual(u32(blocked,0x20),0);self.assertEqual(blocked[offset(0x0203A734):offset(0x0203A734)+600],before)
                out=self.call(st,0x08000000+p.base.previous.HOOK_OFFSET,{0:info,1:0,2:0})
                self.assertEqual(u32(out,0x20),1);self.assertEqual(enemy(out)['species'],772)

    def test_68_existing_night_selectors_preserved_at_boundaries(self):
        enc=p.base.previous
        for i in range(68):
            day,night,g,m,_=struct.unpack_from('<IIBBH',self.source,enc.TABLE_OFFSET+12*i)
            for minute in (359,360,1199,1200):
                st=self.state(g,m,minute);out=self.call(st,enc.ENTRY_SELECT,{0:day,1:0})
                self.assertEqual(u32(out,0x20),night if minute<360 or minute>=1200 else day)
                self.assertEqual(out[RNG:RNG+4],st[RNG:RNG+4])
                at=offset(save1(st));self.assertEqual(out[at:at+0x3668],st[at:at+0x3668])

    def bootstrap(self):
        x,y,buttons=self.grass_site(1,122);data=bytearray(self.source);sign=p.base.previous.SIGN_POINTER
        self.assertEqual(data[0xF90000:0xF9000A],b'\xff'*10)
        self.assertEqual(struct.unpack_from('<I',data,sign)[0],0x08000000+p.base.SCRIPT_OFFSET)
        struct.pack_into('<I',data,sign,0x08F90000)
        data[0xF90000:0xF9000A]=struct.pack('<BBBBHHBB',0x39,1,122,255,x,y,0x27,2)
        restored=bytearray(data)
        for at,n in ((sign,4),(0xF90000,10)):restored[at:at+n]=self.source[at:at+n]
        self.assertEqual(bytes(restored),self.source)
        copy=self.dir/'arrival-only.gba';copy.write_bytes(data);self.switch(copy)
        original=self.fixture
        try:
            self.fixture=route_entry_fixture(self.f)
            st=set_time(self.fixture,600);effect=self.call(st,0x0808EA14,{0:0x4020,1:200})
            self.f.restore(bytes(copy_ewram(st,effect)));route_from_entry(self.f)
            self.f.run(64,'LEFT');self.f.run(30);self.f.run(24,'UP');self.f.run(120)
        finally:self.fixture=original
        self.f.pulse('A',150);self.f.run(150)
        for _ in range(180):
            st=self.f.state()
            if game.location(st)==(1,122) and main_callback2(st)==main_callback2(original):break
            self.assertFalse(in_battle(st));self.f.run(2)
        arrived=self.f.state();self.assertEqual(game.location(arrived),(1,122))
        self.assertEqual(game.coords(arrived),(x+7,y+7));self.assertEqual(main_callback2(arrived),main_callback2(original))
        flash=save_game(self.f);self.assertEqual(len(flash),131072)
        self.switch(self.rom);loaded=load_game(self.f,flash)
        self.assertEqual(game.location(loaded),(1,122));self.assertEqual(game.coords(loaded),(x+7,y+7))
        self.assertFalse(in_battle(loaded));self.assertEqual(main_callback2(loaded),main_callback2(original))
        return loaded,buttons

    def shot(self,name):
        dest=os.environ.get('MOTOR_V41_SCREENS')
        if not dest:return
        from PIL import Image
        frames=[]
        @VIDEO_CB
        def video(data,w,h,pitch):
            if data:frames[:]=[(C.string_at(data,pitch*h),w,h,pitch)]
        self.f.video=video;self.f.core.core.retro_set_video_refresh(video);self.f.run(2)
        raw,w,h,pitch=frames[0];fmt=self.f.core.fmt_code;bpp=4 if fmt==1 else 2
        raw=b''.join(raw[y*pitch:y*pitch+w*bpp] for y in range(h))
        if fmt==1:img=Image.frombytes('RGB',(w,h),raw,'raw','BGRX')
        else:
            self.assertEqual(fmt,2);rgb=bytearray()
            for i in range(0,len(raw),2):
                v=raw[i]|raw[i+1]<<8;rgb.extend((((v>>11)&31)*255//31,((v>>5)&63)*255//63,(v&31)*255//31))
            img=Image.frombytes('RGB',(w,h),bytes(rgb))
        path=Path(dest);path.mkdir(parents=True,exist_ok=True);img.save(path/name)

    def wait_field(self):
        for _ in range(60):
            st=self.f.state()
            if not in_battle(st) and main_callback2(st)==main_callback2(self.fixture):
                self.assertEqual(st[offset(BATTLE_OUTCOME)],7);self.assertEqual(game.location(st),(1,122));return st
            self.f.pulse('B',90)
        self.fail(f'No captured field return: {text(self.f.state())}')

    def test_live_walk_capture_day_night_flash_and_v40_roundtrip(self):
        arrived,buttons=self.bootstrap()
        self.assertEqual(u32(self.call(arrived,0x0808E9D4,{0:0x4024}),0x20),0)
        for minute in (600,1320):
            start=set_time(arrived,minute)
            effect=self.call(start,0x0808EA14,{0:0x4020,1:0});start=copy_ewram(start,effect)
            start=bytes(add(self.f,start,1,1)) # One synthetic Master Ball, not catch-rate validation.
            self.assertEqual(start[game.PARTY_COUNT],1)
            for delay in range(192):
                self.f.restore(start);self.f.run(delay)
                for step in range(160):
                    self.f.run(8,buttons[(step//2)%2])
                    if in_battle(self.f.state()):break
                if not in_battle(self.f.state()):continue
                self.f.run(300)
                if enemy(self.f.state())['species']!=772:continue
                for _ in range(6):self.f.pulse('B',45)
                before=self.f.state();self.assertIn('vai fazer?',text(before));break
            else:self.fail('No walking Type: Null encounter')
            self.assertEqual((enemy(before)['species'],enemy(before)['level']),(772,20))
            self.assertTrue(enemy(before)['valid']);self.assertEqual(u32(before,offset(0x02020374))&8,0)
            self.shot(f'TYPE_NULL_{minute}_BATALHA.png');self.throw_first_ball();caught=self.wait_field()
            self.assertEqual(caught[game.PARTY_COUNT],2);data=game.party_slot(caught,1)
            self.assertEqual(data[:4],before[offset(0x0203A734):offset(0x0203A734)+4])
            self.assertEqual(game.party_slot(caught,0),game.party_slot(before,0))
            facts=mon_facts(data);self.assertTrue(facts['valid']);self.assertEqual((facts['species'],facts['level']),(772,20))
            self.assert_ball_metadata(data,1);self.assertEqual(get(self.f,caught,1),0)
            self.f.restore(caught);flash=save_game(self.f)
            # Fresh cores and native flash only, v41 -> v40 -> v41.
            self.switch(self.base);old=load_game(self.f,flash)
            self.assertEqual(game.party_slot(old,1),data);self.assertEqual(game.location(old),(1,122))
            # load_game ends with a field A press; normalize START menu position through B.
            flash_back=save_game(self.f)
            def save_counter(data):
                counters=[struct.unpack_from('<I',data,i*4096+0xFFC)[0] for i in range(28)
                    if struct.unpack_from('<I',data,i*4096+0xFF8)[0]==0x08012025
                    and struct.unpack_from('<H',data,i*4096+0xFF4)[0]<14]
                self.assertTrue(counters,'No native save sectors');return max(counters)
            self.assertNotEqual(flash_back,flash)
            old_counter,new_counter=save_counter(flash),save_counter(flash_back)
            self.assertEqual(new_counter,old_counter+1,'V40 must actually write a new save')
            self.switch(self.rom);loaded=load_game(self.f,flash_back)
            self.assertEqual(game.party_slot(loaded,1),data);self.assertEqual(loaded[game.PARTY_COUNT],2)
            self.assertEqual(game.location(loaded),(1,122));self.assertFalse(in_battle(loaded))
            self.assertEqual(get(self.f,loaded,1),0)
            self.observations.append(dict(probe='walking_capture_flash_roundtrip',minute=minute,variant=0,species=772,level=20,
                ball='synthetic Master Ball',natural_island_travel=False,delay=delay,party_preserved=True,
                v41_save_counter=old_counter,v40_resave_counter=new_counter))
