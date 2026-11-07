"""Options-only SELECT, owned preference record, synthetic native flash.
All live choices use buttons. RAM edits are initial conditions of ABI/corruption
probes, never repairs during a live save or evolution.
"""
import os,struct,ctypes as C,unittest
from pathlib import Path
import test_motor_v33_hud_mgba as hud
import test_motor_v24_mgba as clock
from mgba_treino_harness import Emulator,offset,u32,put16,put32,mon
from test_golpes_gen9_mgba import invoke
from test_golpes_gen9_integracao import save_game,load_game
from test_estojo_expandido_mgba import save1,add,get
from test_motor_v19_mgba import elapsed,save2,set_time
p=hud.p

def at(st):return offset(save1(st)+p.PREFERENCE_OFFSET)
def pref(st):return struct.unpack_from('<II',st,at(st))
def set_pref(st,hidden=True):
    st=bytearray(st);put32(st,offset(save1(st)+0x34D8),clock.p.T9_MAGIC)
    struct.pack_into('<II',st,at(st),p.PREFERENCE_MAGIC,p.HIDDEN if hidden else p.VISIBLE)
    return st

def ticks(st):
    return clock.progress(st) if elapsed(st)==clock.MAX else elapsed(st)*60+st[save2(st)+18]

def open_options(f):
    # Fresh field fixture or cold-loaded game: the native cursor starts at 0.
    f.pulse('START',60)
    for _ in range(5):f.pulse('DOWN',35)
    f.pulse('A',120)

def close_options(f):f.pulse('B',90);f.pulse('B',90)

def save_after_options(f):
    # Options is immediately below Save in this fixture. Preserve native
    # cursor memory and move UP once, rather than editing the cursor in RAM.
    f.pulse('START',70);f.pulse('UP',35)
    for _ in range(15):f.pulse('A',100)
    size=f.core.core.retro_get_memory_size(0);ptr=f.core.core.retro_get_memory_data(0)
    if size!=131072 or not ptr:raise AssertionError('Invalid synthetic flash')
    return C.string_at(ptr,size)

def prepare(cls):
    hud.prepare(cls);cls.f.restore(cls.fixture);open_options(cls.f)
    cls.options=cls.f.state()
    if u32(cls.options,hud.IW+0x4610)!=0x080EF379:raise AssertionError('Not in native Options')

@unittest.skipUnless(hud.ROM and hud.CORE,'set MOTOR_V33_ROM and MGBA_CORE')
class MotorV33PreferenceTests(unittest.TestCase):
    setUpClass=classmethod(prepare);tearDownClass=classmethod(hud.finish)
    def call(self,st,entry,regs=None):return invoke(self.f,st,entry&~1,regs or {})
    def state_value(self,st):return u32(self.call(st,p.ENTRY_PREFERENCE),0x20)
    def assert_save_equal(self,a,b):
        for start,size in ((offset(save1(a)),0x3668),(save2(a),0xF2C)):
            self.assertEqual(a[start:start+size],b[start:start+size])

    def test_default_shown_and_read_only_no_automatic_bag_migration(self):
        self.assertEqual(pref(self.fixture),(0,0));self.assertEqual(self.state_value(self.fixture),0)
        out=self.call(self.fixture,p.ENTRY_PREFERENCE)
        self.assertEqual(out[0x21000:0x61000],self.fixture[0x21000:0x61000])
        self.f.restore(self.fixture);self.f.run(180)
        self.assertTrue(hud.has_hud(self.f.state()))
        self.assertEqual(pref(self.f.state()),(0,0))
        self.assertEqual(self.f.state()[offset(save1(self.f.state())+0x34D8):offset(save1(self.f.state())+0x3668)],
                         self.fixture[offset(save1(self.fixture)+0x34D8):offset(save1(self.fixture)+0x3668)])

    def test_live_select_hold_once_and_show_hide_without_changing_native_options(self):
        self.f.restore(self.options);native=self.options[save2(self.options)+0x13:save2(self.options)+0x16]
        self.f.run(120,'SELECT');out=self.f.state()
        self.assertEqual(pref(out),(p.PREFERENCE_MAGIC,p.HIDDEN))
        opts=offset(u32(out,offset(0x020399B0)))
        self.assertEqual(out[opts:opts+14],self.options[opts:opts+14])
        close_options(self.f);out=self.f.state()
        self.assertFalse(hud.has_hud(out));self.assertIsNone(hud.resource(out,hud.TT,64));self.assertIsNone(hud.resource(out,hud.PT,16))
        self.assertEqual(out[save2(out)+0x13:save2(out)+0x16],native)
        before=ticks(out);self.f.run(120);self.assertEqual(ticks(self.f.state())-before,120)
        self.f.pulse('START',60);self.f.pulse('A',120) # remembers Options
        self.f.pulse('SELECT',60);close_options(self.f)
        out=self.f.state();self.assertEqual(pref(out),(p.PREFERENCE_MAGIC,p.VISIBLE));self.assertTrue(hud.has_hud(out))

    def test_native_navigation_chords_and_abi_pass_through(self):
        opts=offset(u32(self.options,offset(0x020399B0)))
        for key,cursor,value,want_ret,want_cursor,want_value in (
            (0x10,0,1,4,0,2),(0x20,0,1,4,0,0),(0x40,0,1,3,6,1),
            (0x80,0,1,3,1,1),(1,0,1,1,0,1),(2,0,1,1,0,1),(0,0,1,0,0,1),
            (0x10,5,9,2,5,0),(0x20,5,0,2,5,9),(0x14,0,1,4,0,2)):
            st=bytearray(self.options);put16(st,opts+14,cursor);put16(st,opts+cursor*2,value)
            for off in (0x2C,0x2E,0x30):put16(st,hud.IW+0x460C+off,key)
            regs={r:0xBAD000+r for r in range(4,12)}
            out=self.call(st,p.ENTRY_INPUT,regs)
            self.assertEqual(u32(out,0x20),want_ret)
            self.assertEqual(struct.unpack_from('<H',out,opts+14)[0],want_cursor)
            self.assertEqual(struct.unpack_from('<H',out,opts+cursor*2)[0],want_value)
            self.assertEqual(pref(out),pref(st))
            for r in range(4,12):self.assertEqual(u32(out,0x20+4*r),regs[r])
            self.assertEqual(u32(out,0x54),0x03007E00)

    def test_live_native_settings_button_modes_and_select_remain_independent(self):
        for mode in (0,1,2):
            self.f.restore(self.options)
            for _ in range(4):self.f.pulse('DOWN',25)
            for _ in range(mode):self.f.pulse('RIGHT',25)
            self.f.pulse('SELECT',60);close_options(self.f)
            out=self.f.state();self.assertEqual(out[save2(out)+0x13],mode)
            self.assertEqual(pref(out),(p.PREFERENCE_MAGIC,p.HIDDEN))
        self.f.restore(self.fixture);before=pref(self.fixture)
        self.f.pulse('SELECT',60) # native registered-item action, NOT HUD toggle
        self.assertEqual(pref(self.f.state()),before)

    def test_owned_preference_toggle_only_eight_save_bytes_and_clock_unchanged(self):
        for hidden in (False,True):
            st=set_pref(clock.saturated(self.options,1320,17),hidden)
            out=self.call(st,p.ENTRY_TOGGLE)
            self.assertEqual(u32(out,0x20),1)
            self.assertEqual(pref(out),(p.PREFERENCE_MAGIC,p.VISIBLE if hidden else p.HIDDEN))
            self.assertEqual(clock.record(out),(1320,17))
            patched=bytearray(out);patched[at(st):at(st)+8]=st[at(st):at(st)+8]
            self.assert_save_equal(st,patched)

    def test_all_64_single_bit_errors_foreign_records_and_invalid_pointers_refused(self):
        base=set_pref(self.options)
        for bit in range(64):
            st=bytearray(base);st[at(st)+bit//8]^=1<<(bit%8)
            self.assertEqual(self.state_value(st),3,bit)
            out=self.call(st,p.ENTRY_TOGGLE);self.assertEqual(u32(out,0x20),0)
            self.assert_save_equal(st,out)
        for record in ((0,1),(123,456),(p.PREFERENCE_MAGIC,0)):
            st=bytearray(base);struct.pack_into('<II',st,at(st),*record)
            out=self.call(st,p.ENTRY_TOGGLE);self.assertEqual(u32(out,0x20),0);self.assert_save_equal(st,out)
        for ptr_at in (hud.IW+0x6F94,hud.IW+0x6F98,offset(0x020399B0)):
            for pointer in (0,0x02000001,0x0203FFF0):
                st=bytearray(base);put32(st,ptr_at,pointer)
                out=self.call(st,p.ENTRY_TOGGLE);self.assertEqual(u32(out,0x20),0)
                self.assertEqual(out[0x21000:0x61000],st[0x21000:0x61000])

    def test_cold_migration_uses_real_legacy_pocket_and_refuses_foreign_extension(self):
        st=bytearray(self.options);one=offset(save1(st));two=save2(st)
        st[one+0x34D8:one+0x3668]=bytes(400);key=u32(st,two+0xF24)&65535
        for i in range(58):struct.pack_into('<HH',st,one+0x464+4*i,0,key)
        for i,(item,qty) in enumerate(((375,777),(394,17),(603,999),(294,3))):
            struct.pack_into('<HH',st,one+0x464+4*i,item,qty^key)
        out=self.call(st,p.ENTRY_TOGGLE);self.assertEqual(u32(out,0x20),1)
        self.assertEqual(pref(out),(p.PREFERENCE_MAGIC,p.HIDDEN))
        for item,qty in ((375,777),(394,17),(603,999),(294,3)):self.assertEqual(get(self.f,out,item),qty)
        self.assertEqual(out[one+0x3658:one+0x3660],bytes(8))
        for bad in (0x34D8,0x35FC,0x3658):
            corrupt=bytearray(st);corrupt[one+bad]=0xA5
            out=self.call(corrupt,p.ENTRY_TOGGLE);self.assertEqual(u32(out,0x20),0);self.assert_save_equal(corrupt,out)
        corrupt=bytearray(st);struct.pack_into('<HH',corrupt,one+0x464+16,375,500^key)
        out=self.call(corrupt,p.ENTRY_TOGGLE);self.assertEqual(u32(out,0x20),0);self.assert_save_equal(corrupt,out)

    def test_title_temporary_screens_fades_and_inactive_options_cannot_toggle(self):
        opts=offset(u32(self.options,offset(0x020399B0)))
        cases=[(hud.IW+0x4610,0x080F172D,4),(hud.IW+0x4610,0x0814CAB9,4),
               (hud.IW+0x4614,0,4),(hud.IW+0x4614,0x08000595,4),
               (clock.clock.FADE+7,0x80,1)]
        cases += [(opts+0x10,value,1) for value in (0,1,3,4,5)]
        for pos,value,size in cases:
            st=bytearray(self.options);st[pos:pos+size]=value.to_bytes(size,'little')
            out=self.call(st,p.ENTRY_TOGGLE);self.assertEqual(u32(out,0x20),0);self.assert_save_equal(st,out)

    def test_hidden_keeps_pre_and_postcap_world_clock_running_and_releases_resources(self):
        for capped in (False,True):
            st=clock.saturated(self.fixture,1439,0) if capped else set_time(self.fixture,1439)
            st=set_pref(st);self.f.restore(bytes(st));before=ticks(st);self.f.run(120)
            out=self.f.state();self.assertEqual((ticks(out)-before)%86400,120)
            self.assertFalse(hud.has_hud(out));self.assertIsNone(hud.resource(out,hud.TT,64));self.assertIsNone(hud.resource(out,hud.PT,16))
            if capped:self.assertEqual(elapsed(out),clock.MAX)
            self.assertEqual(pref(out),(p.PREFERENCE_MAGIC,p.HIDDEN))

    @unittest.skipUnless(os.environ.get('MOTOR_V33_BASE'),'set MOTOR_V33_BASE')
    def test_native_hidden_flash_reload_and_v32_downgrade_preserves_setting(self):
        old=Path(os.environ['MOTOR_V33_BASE']);self.assertEqual(p.digest(old.read_bytes()),hud.release.BASE_SHA256)
        def switch(rom):
            self.f.close();type(self).f=self.f=Emulator(rom,Path(hud.CORE),self.dir)
        for capped in (False,True):
            st=self.fixture
            for item,qty in ((4,7),(375,17),(603,999)):st=add(self.f,st,item,qty)
            st=clock.saturated(st,1320,17) if capped else set_time(st,1320)
            self.f.restore(bytes(st));open_options(self.f);self.f.pulse('SELECT',60);close_options(self.f)
            self.assertEqual(pref(self.f.state()),(p.PREFERENCE_MAGIC,p.HIDDEN))
            identity=mon(st);flash=save_after_options(self.f)
            for rom,visible in ((self.rom,False),(old,False),(self.rom,False)):
                switch(rom);loaded=load_game(self.f,flash);self.f.run(4);loaded=self.f.state()
                self.assertEqual(pref(loaded),(p.PREFERENCE_MAGIC,p.HIDDEN))
                self.assertEqual(hud.has_hud(loaded),visible);self.assertEqual(mon(loaded),identity)
                for item,qty in ((4,7),(375,17),(603,999)):self.assertEqual(get(self.f,loaded,item),qty)
                self.f.restore(loaded);before=ticks(loaded);self.f.run(120)
                self.assertEqual((ticks(self.f.state())-before)%86400,120)
                if capped:self.assertEqual(elapsed(self.f.state()),clock.MAX)
                flash=save_game(self.f)
