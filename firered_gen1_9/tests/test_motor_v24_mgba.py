"""Exact v24: synthetic boundary, corruption, native save and live clock tests.
No personal saves; direct ABI calls are distinct from live button/frame flows.
"""
import os
import struct
import tempfile
import unittest
from pathlib import Path
from scripts import motor_v24 as p
from scripts import motor_v19 as clock_patch
from mgba_treino_harness import Emulator,offset,u32,put32,mon,mon_facts,PARTY
from test_eventos_fixos_mgba import route_entry_fixture
from test_golpes_gen9_mgba import seed_mon
from test_golpes_gen9_integracao import save_game,load_game
import test_motor_v19_mgba as clock
import test_motor_v23_mgba as encounters
import test_estojo_expandido_mgba as bag
from battle_fixture_helpers import in_battle,main_callback2

ROM=os.environ.get('MOTOR_V24_ROM');CORE=os.environ.get('MGBA_CORE')
IW=clock.IW
MODE=IW+0x21D6
MAX=3599999
UPDATE=0x08101665
START=0x08101621
STOP=0x08101659
RESET=0x08101605


def prepare(cls):
    cls.rom=Path(ROM);cls.source=cls.rom.read_bytes()
    if p.digest(cls.source)!=p.OUTPUT_SHA256:raise ValueError('Not exact v24')
    cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
    cls.f=Emulator(cls.rom,Path(CORE),cls.dir)
    cls.fixture=route_entry_fixture(cls.f)


def finish(cls):
    cls.f.close();cls.temp.cleanup()
    if p.digest(cls.rom.read_bytes())!=p.OUTPUT_SHA256:raise AssertionError('ROM changed')


def packed(minute,frame):
    raw=minute|(frame<<11);crc=0x1D0F
    for bit in f'{raw:017b}':
        feedback=bool(crc&0x4000)^bool(int(bit))
        crc=(crc*2)&0x7FFF
        if feedback:crc^=0x4599
    return raw|(crc<<17)


def record_at(st):return offset(bag.save1(st)+p.RECORD_OFFSET)


def record(st):
    magic,word=struct.unpack_from('<II',st,record_at(st))
    m,f=word&2047,(word>>11)&63
    if magic!=p.RECORD_MAGIC or m>=1440 or f>=60 or word!=packed(m,f):
        raise AssertionError(f'Bad clock record {magic:08x} {word:08x}')
    return m,f


def progress(st):
    m,f=record(st);return m*60+f


def saturated(st,minute=None,frame=0,mode=2):
    st=clock.set_elapsed(st,MAX,59);st[MODE]=mode
    if minute is not None:
        # Synthetic initial state, owned extension explicitly initialized.
        put32(st,offset(bag.save1(st)+0x34D8),p.T9_MAGIC)
        struct.pack_into('<II',st,record_at(st),p.RECORD_MAGIC,packed(minute,frame))
    return st


@unittest.skipUnless(ROM and CORE,'set MOTOR_V24_ROM and MGBA_CORE')
class MotorV24ClockTests(unittest.TestCase):
    setUpClass=classmethod(prepare)
    tearDownClass=classmethod(finish)
    call=encounters.MotorV23EncounterTests.call
    minutes=clock.MotorV19ClockTests.minutes

    def test_precap_native_frames_seconds_hours_and_exact_transition(self):
        for seconds in (0,59,959,3599,7199,MAX-1):
            for frame in (0,58,59):
                st=clock.set_elapsed(self.fixture,seconds,frame);st[MODE]=1
                out=self.call(st,UPDATE)
                self.assertEqual(clock.elapsed(out),seconds+(frame==59))
                self.assertEqual(out[clock.save2(out)+18],(frame+1)%60)
                self.assertEqual(bag.extension(out),bag.extension(st))
        st=clock.set_elapsed(self.fixture,MAX,58);st[MODE]=1
        out=self.call(st,UPDATE)
        self.assertEqual(out[clock.save2(out)+18],59)
        self.assertEqual(self.minutes(out),479)
        self.assertEqual(bag.extension(out),bag.extension(st))
        out=self.call(out,UPDATE)
        self.assertEqual((record(out),self.minutes(out),out[MODE]),((480,0),480,2))
        self.assertEqual(clock.elapsed(out),MAX)
        self.assertEqual(out[clock.save2(out)+18],59)
        for i in range(1,61):
            out=self.call(out,UPDATE)
            self.assertEqual(record(out),(480+i//60,i%60))

    def test_cycles_boundaries_native_stop_start_reset_and_unknown_mode(self):
        for minute,frame,want in ((359,59,(360,0)),(479,59,(480,0)),(1199,59,(1200,0)),(1439,59,(0,0)),(0,0,(0,1))):
            out=self.call(saturated(self.fixture,minute,frame),UPDATE)
            self.assertEqual(record(out),want)
            self.assertEqual(clock.elapsed(out),MAX)
        st=saturated(self.fixture,1320,17)
        stopped=self.call(st,STOP);self.assertEqual(stopped[MODE],0)
        out=self.call(stopped,UPDATE);self.assertEqual(record(out),(1320,17))
        started=self.call(out,START);self.assertEqual(started[MODE],1)
        out=self.call(started,UPDATE);self.assertEqual(record(out),(1320,18))
        reset=self.call(out,RESET)
        self.assertEqual((clock.elapsed(reset),reset[clock.save2(reset)+18],reset[MODE]),(0,0,0))
        self.assertEqual(self.minutes(reset),480)
        reset=self.call(self.call(reset,START),UPDATE)
        self.assertEqual(reset[record_at(reset):record_at(reset)+8],bytes(8))
        self.assertEqual(reset[clock.save2(reset)+18],1)
        for mode in (0,3,255):
            st=saturated(self.fixture,1320,17,mode);out=self.call(st,UPDATE)
            self.assertEqual(out[MODE],mode);self.assertEqual(bag.extension(out),bag.extension(st))
        # A stopped old saturated save must not initialize anything either.
        st=saturated(self.fixture,mode=0);out=self.call(st,UPDATE)
        self.assertEqual(bag.extension(out),bag.extension(st))

    def test_lazy_existing_migration_precedes_clock_and_preserves_legacy_tms(self):
        st=saturated(self.fixture,mode=1);one=offset(bag.save1(st));two=clock.save2(st)
        st[one+0x34D8:one+0x3668]=bytes(400)
        key=u32(st,two+0xF24)&65535
        for i in range(58):struct.pack_into('<HH',st,one+0x464+4*i,0,key)
        for i,(item,qty) in enumerate(((375,777),(394,17),(603,999),(294,3))):
            struct.pack_into('<HH',st,one+0x464+4*i,item,qty^key)
        out=self.call(st,UPDATE)
        self.assertEqual(record(out),(480,0));self.assertEqual(bag.extension(out)[:4],b'T9X1')
        for item,qty in ((375,777),(394,17),(603,999),(294,3)):
            self.assertEqual(bag.get(self.f,out,item),qty)
        self.assertEqual(mon(out),mon(st))
        self.assertEqual(out[one:one+0x464],st[one:one+0x464])
        self.assertEqual(out[one+0x54C:one+0x34D8],st[one+0x54C:one+0x34D8])
        self.assertEqual(bag.extension(out)[291:384],bytes(93))
        self.assertEqual(bag.extension(out)[392:],bytes(8))

    def test_cold_migration_deferred_outside_normal_outdoor_field(self):
        cold=saturated(self.fixture)
        one=offset(bag.save1(cold));cold[one+0x34D8:one+0x3668]=bytes(400)
        for callback,typ in ((0,1),(0x0814B251,1),(0x08050CC5,3),(0x080F172D,7),(0x080F172D,4)):
            st=bytearray(cold);put32(st,IW+0x4610,callback);st[clock.MAP_TYPE]=typ
            out=self.call(st,UPDATE)
            self.assertEqual(bag.extension(out),bytes(400))
            # Already initialized storage needs NO field-only restriction.
            put32(st,one+0x34D8,p.T9_MAGIC)
            self.assertEqual(record(self.call(st,UPDATE)),(480,0))
        for typ in (1,2,3,6):
            st=bytearray(cold);put32(st,IW+0x4610,0x080F172D);st[clock.MAP_TYPE]=typ
            self.assertEqual(record(self.call(st,UPDATE)),(480,0))

    def test_native_pokedude_temporary_pocket_cannot_initialize_clock(self):
        from test_golpes_gen9_mgba import invoke
        st=saturated(self.fixture);one=offset(bag.save1(st))
        st[one+0x34D8:one+0x3668]=bytes(400)
        key=u32(st,clock.save2(st)+0xF24)&65535
        for i in range(58):struct.pack_into('<HH',st,one+0x464+4*i,0,key)
        for i,(item,n) in enumerate(((375,17),(394,9),(294,3))):
            struct.pack_into('<HH',st,one+0x464+4*i,item,n^key)
        original_ids=bag.pocket_ids(st)
        opened=invoke(self.f,bytes(st),0x0814CAB8,{})
        self.assertEqual(bag.pocket_ids(opened)[:4],[289,291,297,323])
        self.assertEqual(bag.extension(opened),bytes(400))
        out=self.call(opened,UPDATE)
        self.assertEqual(bag.extension(out),bytes(400))
        self.assertEqual(bag.pocket_ids(out),bag.pocket_ids(opened))
        # Resume the actual demo/cancel path with its new callbacks and RAM.
        resumed=bytearray(opened);resumed[:0x1000]=st[:0x1000]
        self.f.restore(bytes(resumed));self.f.run(400)
        self.assertEqual(bag.extension(self.f.state()),bytes(400))
        self.f.pulse('B',120);self.f.run(200);restored=self.f.state()
        self.assertEqual(bag.pocket_ids(restored),original_ids)
        for item,n in ((375,17),(394,9),(294,3)):
            self.assertEqual(bag.get(self.f,restored,item),n)

    def test_corrupt_foreign_and_out_of_range_records_fail_closed(self):
        normal=saturated(self.fixture,1320,17)
        cases=[]
        for bit in range(64):
            st=bytearray(normal);st[record_at(st)+bit//8]^=1<<(bit%8);cases.append(st)
        for minute,frame in ((1440,0),(2047,0),(0,60),(0,63)):
            st=saturated(self.fixture,minute,frame);cases.append(st)
        # Foreign extension with an empty record: migration must not overwrite it.
        st=saturated(self.fixture);at=offset(bag.save1(st)+0x34D8)
        st[at:at+400]=bytes(400);st[at+123]=0x5A;cases.append(st)
        for st in cases:
            with self.subTest(record=st[record_at(st):record_at(st)+8].hex()):
                self.assertEqual(self.minutes(st),479)
                out=self.call(st,UPDATE)
                self.assertEqual(bag.extension(out),bag.extension(st))
                self.assertEqual(mon(out),mon(st))
                self.assertEqual(clock.elapsed(out),MAX)
        # A CRC-valid owned record is cleared on an active pre-cap reset only;
        # unknown bytes must never be 'repaired' as if owned by the clock.
        st=clock.set_elapsed(cases[0],0);st[MODE]=1
        self.assertEqual(bag.extension(self.call(st,UPDATE)),bag.extension(st))

    def test_unsafe_pointers_fields_and_getter_read_only_abi(self):
        for which in (0x6F94,0x6F98):
            for addr in (0,0x01000000,0x02000001,0x0203FFF0,0x03000000):
                st=saturated(self.fixture,1320);put32(st,IW+which,addr)
                out=self.call(st,UPDATE)
                self.assertEqual(out[0x21000:0x61000],st[0x21000:0x61000])
                self.assertEqual(self.minutes(st),479 if which==0x6F94 else 480)
        for at,value in ((16,60),(17,60),(18,60)):
            st=saturated(self.fixture,1320);st[clock.save2(st)+at]=value
            out=self.call(st,UPDATE)
            self.assertEqual(out[0x21000:0x61000],st[0x21000:0x61000])
        for entry in (p.ENTRY_MINUTES,clock_patch.ENTRY_MINUTES):
            st=saturated(self.fixture,1320,17);regs={r:0xBAD000+r for r in range(4,12)}
            out=self.call(st,entry,regs)
            self.assertEqual(u32(out,0x20),1320)
            self.assertEqual(out[0x21000:0x61000],st[0x21000:0x61000])
            for r in range(4,12):self.assertEqual(u32(out,0x20+4*r),regs[r])
            self.assertEqual(u32(out,0x54),0x03007E00)

        for entry in (UPDATE,p.ENTRY_UPDATE):
            for st in (clock.set_elapsed(self.fixture,59,59),saturated(self.fixture,1320,17)):
                st[MODE]=1;regs={r:0xBAD000+r for r in range(4,12)}
                out=self.call(st,entry,regs)
                for r in range(4,12):self.assertEqual(u32(out,0x20+4*r),regs[r])
                self.assertEqual(u32(out,0x54),0x03007E00)

    def test_live_two_complete_world_days_and_paused_time(self):
        st=saturated(self.fixture,480,0);self.f.restore(bytes(st))
        for _ in range(2):
            self.f.run(1440*60)
            out=self.f.state()
            self.assertEqual(record(out),(480,0))
            self.assertEqual(clock.elapsed(out),MAX)
            self.assertEqual(out[clock.save2(out)+18],59)
            self.assertEqual(main_callback2(out),main_callback2(st))
        st=saturated(self.fixture,600,17,0);self.f.restore(bytes(st));self.f.run(120)
        self.assertEqual(record(self.f.state()),(600,17))
        self.f.restore(bytes(saturated(self.fixture,600,17)));self.f.run(120)
        self.assertEqual(record(self.f.state()),(602,17))

    def test_postcap_all_sixteen_encounter_maps_and_phase_boundaries(self):
        for minute,phase in ((0,0),(359,0),(360,1),(479,1),(480,2),(1079,2),(1080,3),(1199,3),(1200,0),(1439,0)):
            st=saturated(self.fixture,minute)
            self.assertEqual(u32(self.call(st,clock_patch.ENTRY_PHASE),0x20),phase)
            sign=self.call(st,p.previous.ENTRY_SIGN)
            self.assertEqual(struct.unpack_from('<H',sign,encounters.RESULT)[0],int(minute<360 or minute>=1200))
            for i in range(len(p.previous.MAPS)):
                day,night,g,m,_=struct.unpack_from('<IIBBH',self.source,p.previous.TABLE_OFFSET+12*i)
                at=offset(bag.save1(st));st[at+4:at+6]=bytes((g,m))
                out=self.call(st,p.previous.ENTRY_SELECT,{0:day,1:0})
                self.assertEqual(u32(out,0x20),night if minute<360 or minute>=1200 else day)
                self.assertEqual(out[at:at+0x3668],st[at:at+0x3668])

    def test_postcap_live_night_palette_party_menu_and_return(self):
        self.f.restore(bytes(saturated(self.fixture,1320)));self.f.run(2)
        initial=self.f.state()
        def check(st,night):
            src=struct.unpack_from('<512H',st,clock.FADED)
            want=struct.pack('<512H',*[clock.tint(c,0) if night and i<208 else c for i,c in enumerate(src)])
            self.assertEqual(st[clock.PRAM:clock.PRAM+1024],want)
        check(initial,True)
        self.f.pulse('START',60);self.f.pulse('A',100)
        menu=self.f.state();self.assertNotEqual(main_callback2(menu),main_callback2(initial));check(menu,False)
        self.f.run(120);self.assertEqual((progress(self.f.state())-progress(menu))%86400,120)
        for _ in range(3):self.f.pulse('B',80)
        self.assertEqual(main_callback2(self.f.state()),main_callback2(initial));check(self.f.state(),True)

    def test_postcap_real_battle_eevee_evolutions_day_and_night(self):
        from test_golpes_gen9_integracao import GolpesIntegracaoMGBATests,set_exp_and_test_stats
        for minute,target in ((600,196),(1320,197)):
            st=seed_mon(self.fixture,133,10,(33,45,0,0));set_exp_and_test_stats(st,1330)
            st=saturated(clock.set_friendship_item(st,255),minute)
            self.f.restore(bytes(st));GolpesIntegracaoMGBATests.enter_route_battle(self,self.f)
            before=self.f.state();self.assertTrue(in_battle(before));self.f.run(120)
            self.assertEqual((progress(self.f.state())-progress(before))%86400,120)
            for _ in range(150):
                self.f.pulse('A',60);out=self.f.state()
                if mon_facts(mon(out))['species']==target and not in_battle(out) and main_callback2(out)==main_callback2(st):break
            facts=mon_facts(mon(out));self.assertEqual((facts['species'],facts['level'],facts['valid']),(target,11,True))
            self.assertFalse(in_battle(out));self.assertEqual(main_callback2(out),main_callback2(st))
            self.assertEqual(clock.elapsed(out),MAX)

    def test_native_flash_v23_saturated_to_v24_and_v24_roundtrip(self):
        base=Path(os.environ['MOTOR_V24_BASE'])
        self.assertEqual(p.digest(base.read_bytes()),p.BASE_SHA256)
        self.f.close();type(self).f=self.f=Emulator(base,Path(CORE),self.dir)
        try:
            st=route_entry_fixture(self.f)
            for item,qty in ((4,7),(375,17),(603,999)):st=bag.add(self.f,st,item,qty)
            st=saturated(st,mode=2);self.f.restore(bytes(st))
            flash=save_game(self.f);before=self.f.state()
            self.assertEqual(len(flash),131072)
            self.assertEqual(before[record_at(before):record_at(before)+8],bytes(8))
            identity=mon(before);location=before[offset(bag.save1(before)):offset(bag.save1(before))+6]
            self.f.close();type(self).f=self.f=Emulator(self.rom,Path(CORE),self.dir)
            loaded=load_game(self.f,flash)
            self.assertEqual(clock.elapsed(loaded),MAX)
            self.assertTrue(480*60<=progress(loaded)<510*60)
            self.assertEqual(mon(loaded),identity)
            self.assertEqual(loaded[offset(bag.save1(loaded)):offset(bag.save1(loaded))+6],location)
            for item,qty in ((4,7),(375,17),(603,999)):self.assertEqual(bag.get(self.f,loaded,item),qty)
            # Disjoint night phase proves reload doesn't reinitialize at 08:00.
            st=saturated(loaded,1320,17);self.f.restore(bytes(st))
            flash=save_game(self.f);saved=self.f.state();self.assertEqual(len(flash),131072)
            self.f.close();type(self).f=self.f=Emulator(self.rom,Path(CORE),self.dir)
            loaded=load_game(self.f,flash)
            self.assertLess(abs(progress(loaded)-progress(saved)),35*60)
            self.assertGreater(record(loaded)[0],1300)
            self.assertEqual(mon(loaded),identity)
            for item,qty in ((4,7),(375,17),(603,999)):self.assertEqual(bag.get(self.f,loaded,item),qty)
            self.f.restore(bytes(loaded));at=progress(loaded);self.f.run(120)
            self.assertEqual((progress(self.f.state())-at)%86400,120)
        finally:
            self.f.close();type(self).f=self.f=Emulator(self.rom,Path(CORE),self.dir)


    def test_native_v24_v23_v24_downgrade_preserves_but_does_not_advance_record(self):
        base=Path(os.environ['MOTOR_V24_BASE'])
        self.assertEqual(p.digest(base.read_bytes()),p.BASE_SHA256)
        st=bag.add(self.f,self.fixture,375,17)
        self.f.restore(bytes(saturated(st,1320)))
        flash=save_game(self.f)
        self.f.close();type(self).f=self.f=Emulator(base,Path(CORE),self.dir)
        try:
            old=load_game(self.f,flash);frozen=record(old)
            self.assertEqual(self.minutes(old),479)  # v23 ignores CK24
            self.f.restore(bytes(old));self.f.run(120)
            self.assertEqual(record(self.f.state()),frozen)
            flash=save_game(self.f);old_saved=self.f.state()
            self.assertEqual(record(old_saved),frozen)
        finally:
            self.f.close();type(self).f=self.f=Emulator(self.rom,Path(CORE),self.dir)
        loaded=load_game(self.f,flash)
        self.assertTrue(0<=(progress(loaded)-(frozen[0]*60+frozen[1]))%86400<35*60)
        self.assertEqual(mon(loaded),mon(old_saved))
        self.assertEqual(bag.get(self.f,loaded,375),17)


class MotorV24ClockRegressionTests(clock.MotorV19ClockTests):
    __unittest_skip__=not bool(ROM and CORE)
    setUpClass=classmethod(prepare)
    tearDownClass=classmethod(finish)
    # Replaced with explicit continuation/boundary tests above, not a skipped
    # assertion that silently continues to require the old frozen clock.
    test_native_tick_59_to_60_frames_and_max_limit_is_explicit=None


class MotorV24EncounterRegressionTests(encounters.MotorV23EncounterTests):
    __unittest_skip__=not bool(ROM and CORE)
    setUpClass=classmethod(prepare)
    tearDownClass=classmethod(finish)

    def at_sign(self,minute):
        # Synthetic initial Repel status, then only normal movement/buttons.
        # This protects the journey to the sign; it doesn't force an encounter
        # or change a wild table. All R9-R12 test levels exceed this starter.
        from test_eventos_fixos_mgba import route_from_entry
        from test_atualizacoes_gen9_mgba import copy_ewram
        st=clock.set_time(self.fixture,minute)
        effect=self.call(st,0x0808EA14,{0:0x4020,1:200})
        prepared=copy_ewram(st,effect)
        self.f.restore(bytes(prepared));route_from_entry(self.f)
        self.f.run(64,'LEFT');self.f.run(30);self.f.run(24,'UP');self.f.run(120)
        out=self.f.state()
        self.assertFalse(in_battle(out))
        self.assertEqual(main_callback2(out),main_callback2(self.fixture))
        # FireRed can auto-read a sign when walking into it. The temporary
        # warp script may therefore already have transported the player; the
        # caller checks its exact destination. No additional RAM edits here.
        if out[offset(bag.save1(out))+4:offset(bag.save1(out))+6]==bytes((3,19)):
            self.assertEqual(struct.unpack_from('<hh',out,offset(encounters.OBJECTS)+16),(16,39))
        self.assertLess(mon_facts(mon(out))['level'],11)
