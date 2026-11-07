"""Real ARM code on mGBA 0.10.5, exclusively synthetic initial states.

Direct calls test contracts, not full evolution scenes. Live field/save/menu
flows are separate tests. No ROM or personal save supplied by a test fixture.
"""
import os
import struct
import tempfile
import unittest
from pathlib import Path
from scripts import motor_v19 as p
from mgba_treino_harness import Emulator, offset, u32, put16, put32, mon, put_mon, decrypted, PARTY
from test_golpes_gen9_mgba import invoke, seed_mon
from test_eventos_fixos_mgba import route_entry_fixture
from test_golpes_gen9_integracao import save_game, load_game

ROM = os.environ.get('MOTOR_V19_ROM')
CORE = os.environ.get('MGBA_CORE')
IW = 0x19000
PRAM = 0x800
FADED = offset(0x02039DFC)
UNFADED = offset(0x020399FC)
FADE = offset(0x0203A2BC)
MAP_TYPE = offset(0x02027523)


def save2(st): return offset(u32(st, IW + 0x6F98))

def elapsed(st):
    at = save2(st)
    h = struct.unpack_from('<H', st, at+14)[0]
    return h*3600 + st[at+16]*60 + st[at+17]

def set_elapsed(st, seconds, frames=0):
    st = bytearray(st); at = save2(st)
    hours, rem = divmod(seconds, 3600); minutes, seconds = divmod(rem, 60)
    struct.pack_into('<HBBB', st, at+14, hours, minutes, seconds, frames)
    return st

def set_time(st, minute, frames=0): return set_elapsed(st, (minute-480) % 1440, frames)

def set_friendship_item(st, friendship=220, item=0):
    st = bytearray(st); data = mon(st); block, order, valid = decrypted(data)
    if not valid: raise AssertionError('Invalid synthetic mon')
    block[order[0]*12+9] = friendship
    put16(block, order[0]*12+2, item)
    put16(data, 28, sum(struct.unpack('<24H', block)) & 65535)
    key = u32(data, 0) ^ u32(data, 4)
    for i in range(0,48,4): put32(data, i+32, u32(block,i)^key)
    put_mon(st, data)
    return st

def tint(c, phase):
    gain = ((18,20,28), (29,27,28), (32,32,32), (30,25,25))[phase]
    return sum((((c >> (i*5)) & 31)*gain[i]//32) << (i*5) for i in range(3))


@unittest.skipUnless(ROM and CORE, 'set MOTOR_V19_ROM and MGBA_CORE')
class MotorV19ClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        if p.digest(cls.rom.read_bytes()) != p.OUTPUT_SHA256: raise ValueError('Not exact v19')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = Emulator(cls.rom, Path(CORE), Path(cls.temp.name))
        cls.fixture = route_entry_fixture(cls.f)

    @classmethod
    def tearDownClass(cls):
        cls.f.close(); cls.temp.cleanup()
        if p.digest(cls.rom.read_bytes()) != p.OUTPUT_SHA256: raise AssertionError('ROM changed')

    def call(self, state, entry, regs=None): return invoke(self.f, state, entry & ~1, regs or {})
    def minutes(self, state): return u32(self.call(state, p.ENTRY_MINUTES), 0x20)

    def test_clock_start_hour_day_rollovers_and_saved_old_playtime(self):
        for seconds in (0,1,59,60,719,720,959,960,1439,1440,3599,3600,7199,7200,86400,3599999):
            with self.subTest(seconds=seconds):
                st = set_elapsed(self.fixture, seconds)
                out = self.call(st, p.ENTRY_MINUTES)
                self.assertEqual(u32(out,0x20), (480+seconds)%1440)
                self.assertEqual(out[save2(st):save2(st)+0xF24], st[save2(st):save2(st)+0xF24])
        for h in (0,1,2,23,24,997,998,999):
            for m in (0,23,24,47,48,59):
                sec=h*3600+m*60+59
                self.assertEqual(self.minutes(set_elapsed(self.fixture,sec)), (480+sec)%1440)

    def test_phases_boundaries(self):
        for t, phase in ((0,0),(359,0),(360,1),(479,1),(480,2),(1079,2),(1080,3),(1199,3),(1200,0),(1439,0)):
            self.assertEqual(u32(self.call(set_time(self.fixture,t),p.ENTRY_PHASE),0x20),phase)

    def test_native_tick_59_to_60_frames_and_max_limit_is_explicit(self):
        st = set_elapsed(self.fixture, 959, 59); st[IW+0x21D6]=1
        out = self.call(st,0x08101665)
        self.assertEqual(elapsed(out),960); self.assertEqual(out[save2(out)+18],0)
        self.assertEqual(self.minutes(out),0)
        for seconds in (3599,7199):
            st=set_elapsed(self.fixture,seconds,59); st[IW+0x21D6]=1
            out=self.call(st,0x08101665)
            self.assertEqual(elapsed(out),seconds+1)
        st=set_elapsed(self.fixture,3599999,59); st[IW+0x21D6]=1
        out=self.call(st,0x08101665)
        self.assertEqual(elapsed(out),3599999); self.assertEqual(out[IW+0x21D6],2)
        self.assertEqual(self.minutes(out),479)
        self.assertEqual(self.call(out,0x08101665)[save2(out)+14:save2(out)+19],out[save2(out)+14:save2(out)+19])

    def test_invalid_pointer_and_fields_safe_default(self):
        for addr in (0,0x01000000,0x0203FFF0,0x02000001,0x03000000):
            st=bytearray(self.fixture);put32(st,IW+0x6F98,addr)
            self.assertEqual(self.minutes(st),480)
        for at,value in ((16,60),(17,60)):
            st=set_elapsed(self.fixture,0);st[save2(st)+at]=value
            self.assertEqual(self.minutes(st),480)

    def palette_state(self, minute, map_type=1):
        st=set_time(self.fixture,minute);st[MAP_TYPE]=map_type
        st[FADE+7]&=0x7F;st[FADE+8]&=0x7F
        colors=[(i*67)&0x7FFF for i in range(512)]
        data=struct.pack('<512H',*colors)
        st[PRAM:PRAM+1024]=data;st[FADED:FADED+1024]=data
        return st,colors

    def test_tint_terrain_only_all_four_phases_preserves_source_ui_obj(self):
        for t,phase in ((0,0),(360,1),(600,2),(1080,3)):
            st,colors=self.palette_state(t)
            out=self.call(st,p.ENTRY_FIELD)
            expected=struct.pack('<512H',*[tint(c,phase) if i<208 else c for i,c in enumerate(colors)])
            self.assertEqual(out[PRAM:PRAM+1024],expected)
            self.assertEqual(out[UNFADED:UNFADED+2048],st[UNFADED:UNFADED+2048])
            # A second VBlank must re-copy the source, not tint the tinted output.
            again=self.call(out,p.ENTRY_FIELD)
            self.assertEqual(again[PRAM:PRAM+1024],expected)
            self.assertEqual(again[FADED:FADED+1024],st[FADED:FADED+1024])

    def test_indoor_cave_underwater_fade_and_disabled_transfer_not_tinted(self):
        for typ in (0,4,5,7,8,9):
            st,_=self.palette_state(0,typ)
            out=self.call(st,p.ENTRY_FIELD)
            self.assertEqual(out[PRAM:PRAM+1024],st[PRAM:PRAM+1024])
        for flag in (7,8):
            st,_=self.palette_state(0);st[FADE+flag]|=0x80
            out=self.call(st,p.ENTRY_FIELD)
            self.assertEqual(out[PRAM:PRAM+1024],st[PRAM:PRAM+1024])
        for typ in (1,2,3,6):
            st,colors=self.palette_state(0,typ)
            out=self.call(st,p.ENTRY_FIELD)
            self.assertEqual(struct.unpack_from('<H',out,PRAM+20)[0],tint(colors[10],0))

    def evolution(self, species=133, minute=600, friendship=220, item=0, moves=(33,45,0,0), mode=0, stone=0, level=25, egg=False, enigma_effect=None):
        st=seed_mon(self.fixture,species,level,moves,egg=egg)
        st=set_time(set_friendship_item(st,friendship,item),minute)
        if enigma_effect is not None:
            st[offset(u32(st,IW+0x6F94))+0x3166]=enigma_effect
        regs={0:PARTY,1:mode,2:stone,**{i:0xBAD000+i for i in range(4,12)}}
        out=self.call(st,0x0810DB45,regs)
        for i in range(4,12): self.assertEqual(u32(out,0x20+4*i),regs[i])
        self.assertEqual(mon(out),mon(st))
        self.assertEqual(u32(out,0x20+13*4),0x03007E00)
        return u32(out,0x20)

    def test_eevee_day_night_thresholds_everstone_and_sylveon_priority(self):
        for t,want in ((0,197),(359,197),(360,196),(479,196),(480,196),(1199,196),(1200,197),(1439,197)):
            self.assertEqual(self.evolution(minute=t),want)
        for t in (600,1320):
            self.assertEqual(self.evolution(minute=t,friendship=219),0)
            self.assertEqual(self.evolution(minute=t,item=195),0)  # Everstone
            self.assertEqual(self.evolution(minute=t,item=175,enigma_effect=38),0)  # native Enigma hold-effect override
            self.assertEqual(self.evolution(minute=t,moves=(581,33,45,0)),700)  # Moonblast, internal ID
            self.assertEqual(self.evolution(minute=t,moves=(601,33,45,0)),700)  # Baby-Doll Eyes, internal ID
            self.assertEqual(self.evolution(minute=t,egg=True),0)
        self.assertEqual(self.evolution(minute=1320,level=50),197)

    def test_budew_riolu_day_only_other_evolutions_and_item_modes_unchanged(self):
        for species,target in ((406,315),(447,448)):
            self.assertEqual(self.evolution(species=species,minute=600),target)
            self.assertEqual(self.evolution(species=species,minute=1320),0)
            self.assertEqual(self.evolution(species=species,friendship=219),0)
            self.assertEqual(self.evolution(species=species,item=195),0)
        for t in (600,1320):
            self.assertEqual(self.evolution(species=1,level=16,minute=t),2)
            self.assertEqual(self.evolution(species=172,minute=t),25)
            self.assertEqual(self.evolution(mode=2,stone=95,minute=t),136)
            self.assertEqual(self.evolution(mode=3,stone=97,minute=t),134)
            self.assertEqual(self.evolution(mode=1,minute=t),0)
            self.assertEqual(self.evolution(friendship=100,level=36,minute=t),471) # legacy simplified Glaceon, NOT certified modern

    def test_live_field_menu_progress_and_restore_without_writes_during_play(self):
        self.f.restore(bytes(set_elapsed(self.fixture,0)));self.f.run(120)
        before=self.f.state();self.assertEqual(elapsed(before),2)
        self.f.pulse('START',60);menu=self.f.state();self.f.run(120)
        after=self.f.state();self.assertEqual(elapsed(after)-elapsed(menu),2)
        self.f.restore(before);self.assertEqual(elapsed(self.f.state()),elapsed(before))
        self.f.run(60);self.assertEqual(elapsed(self.f.state()),3)

    def test_flash_save_reload_keeps_clock_phase_and_native_format(self):
        self.f.restore(bytes(set_time(self.fixture,1320)))
        flash=save_game(self.f); before=self.f.state(); seconds=elapsed(before)
        self.assertEqual(len(flash),131072)
        # Fresh core: no savestate imported, only synthetic flash written by game.
        self.f.close();self.f=Emulator(self.rom,Path(CORE),Path(self.temp.name))
        type(self).f=self.f
        out=load_game(self.f,flash)
        self.assertGreaterEqual(elapsed(out),seconds-35)
        self.assertLessEqual(elapsed(out),seconds+35)
        self.assertEqual(self.minutes(out),(480+elapsed(out))%1440)

    def test_real_battle_evolution_day_night_and_clock_progress(self):
        from test_golpes_gen9_integracao import GolpesIntegracaoMGBATests, set_exp_and_test_stats
        from mgba_treino_harness import mon_facts
        from battle_fixture_helpers import in_battle, main_callback2
        for minute, target in ((600,196),(1320,197)):
            with self.subTest(minute=minute, target=target):
                st=seed_mon(self.fixture,133,10,(33,45,0,0))
                set_exp_and_test_stats(st,1330) # Medium Fast: 1 XP before level 11
                st=set_time(set_friendship_item(st,255),minute)
                self.f.restore(bytes(st))
                GolpesIntegracaoMGBATests.enter_route_battle(self,self.f)
                before=self.f.state(); self.assertTrue(in_battle(before))
                self.f.run(120); after=self.f.state()
                self.assertEqual(elapsed(after)-elapsed(before),2)
                for _ in range(150):
                    self.f.pulse('A',60)
                    out=self.f.state()
                    if mon_facts(mon(out))['species']==target and not in_battle(out) and main_callback2(out)==main_callback2(st):break
                facts=mon_facts(mon(out))
                self.assertEqual(facts['species'],target)
                self.assertEqual(facts['level'],11)
                self.assertTrue(facts['valid'])
                self.assertFalse(in_battle(out))
                self.assertEqual(main_callback2(out),main_callback2(st))

    def test_live_night_palette_field_party_and_return(self):
        # Existing outdoor fixture -> menu -> party -> field. Native palette
        # transfer in party must NOT run the field tint, despite outdoor mapType.
        from battle_fixture_helpers import main_callback2
        self.f.restore(bytes(set_time(self.fixture,1320)));self.f.run(2)
        st=self.f.state();self.assertEqual(st[MAP_TYPE],1)
        def assert_palette(state, night):
            src=struct.unpack_from('<512H',state,FADED)
            expected=struct.pack('<512H',*[tint(c,0) if night and i<208 else c for i,c in enumerate(src)])
            self.assertEqual(state[PRAM:PRAM+1024],expected)
        assert_palette(st,True)
        self.f.pulse('START',60);self.f.pulse('A',100)
        menu=self.f.state()
        self.assertNotEqual(main_callback2(menu),main_callback2(st))
        assert_palette(menu,False)
        for _ in range(3):self.f.pulse('B',80)
        self.assertEqual(main_callback2(self.f.state()),main_callback2(st))
        assert_palette(self.f.state(),True)
