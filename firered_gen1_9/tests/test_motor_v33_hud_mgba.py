"""v33: fresh synthetic game, ARM ABI/resource probes and real button flows.
The independent bitmap oracle does not read art.h/payload glyph data.
"""
import os,struct,tempfile,unittest
from pathlib import Path
from scripts import motor_v26 as p, motor_v33 as release
from mgba_treino_harness import Emulator,offset,u32,put16,put32
from test_eventos_fixos_mgba import route_entry_fixture
from test_golpes_gen9_mgba import invoke
import test_motor_v19_mgba as clock
import test_motor_v24_mgba as saved
from test_estojo_expandido_mgba import save1

ROM=os.environ.get('MOTOR_V33_ROM');CORE=os.environ.get('MGBA_CORE')
IW=0x19000; TT=IW+0x2478; PT=IW+0x2778; RANGES=IW+0x24F8
NOAM=IW+0x4A3C; HOAM=0xFF8; LOCK=IW+0x2468; DISABLED=IW+0x4A45
FONT=((14,17,19,21,25,17,14),(4,12,4,4,4,4,14),(14,17,1,2,4,8,31),
      (30,1,1,14,1,1,30),(2,6,10,18,31,2,2),(31,16,16,30,1,1,30),
      (14,16,16,30,17,17,14),(31,1,2,4,8,8,8),(14,17,17,14,17,17,14),
      (14,17,17,15,1,1,14))

def prepare(cls):
    cls.rom=Path(ROM);cls.source=cls.rom.read_bytes()
    if p.digest(cls.source)!=release.OUTPUT_SHA256:raise ValueError('Not exact v33')
    cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
    cls.f=Emulator(cls.rom,Path(CORE),cls.dir)
    cls.fixture=route_entry_fixture(cls.f)

def finish(cls):
    cls.f.close();cls.temp.cleanup()
    if p.digest(cls.rom.read_bytes())!=release.OUTPUT_SHA256:raise AssertionError('ROM changed')

def resource(st,at,count):
    tags=struct.unpack_from(f'<{count}H',st,at)
    return tags.index(p.TAG) if p.TAG in tags else None

def has_hud(st):
    display=struct.unpack_from('<H',st,0x400)[0]
    return display&0x1080==0x1000 and st[HOAM:HOAM+4]==bytes.fromhex('0440cc80')

def oracle(minute):
    pixels=[[2 if x in (0,31) or y in (0,15) else 1 for x in range(32)] for y in range(16)]
    for y in (0,15):
        for x in (0,31):pixels[y][x]=0
    digits=f'{minute//60:02d}{minute%60:02d}'
    for char,left in zip(digits,(3,9,18,24)):
        for y,row in enumerate(FONT[int(char)]):
            for x in range(5):
                if row & (16>>x):pixels[y+7][left+x]=3
    pixels[9][15]=pixels[12][15]=4
    caption=((17,27,21,17,17),(17,17,17,17,14),(17,25,21,19,17),(30,17,17,17,30),(14,17,17,17,14))
    for d,rows in enumerate(caption):
        for y,row in enumerate(rows):
            for x in range(5):
                if row&(16>>x):pixels[y+1][2+d*6+x]=4
    b=bytearray(256)
    for y,row in enumerate(pixels):
        for x,v in enumerate(row):b[((y//8)*4+x//8)*32+(y%8)*4+x%8//2]|=v<<(4*(x%2))
    return bytes(b)

@unittest.skipUnless(ROM and CORE,'set MOTOR_V33_ROM and MGBA_CORE')
class MotorV33HudTests(unittest.TestCase):
    setUpClass=classmethod(prepare);tearDownClass=classmethod(finish)
    def call(self,st,entry,regs=None):return invoke(self.f,st,entry&~1,regs or {})
    def field(self,minute=600):
        self.f.restore(bytes(clock.set_time(self.fixture,minute)));self.f.run(4)
        st=self.f.state();self.assertTrue(has_hud(st));return st
    def assert_pixels(self,st,minute):
        i=resource(st,TT,64);pal=resource(st,PT,16)
        self.assertIsNotNone(i);self.assertIsNotNone(pal)
        tile,count=struct.unpack_from('<HH',st,RANGES+4*i)
        self.assertEqual(count,8)
        self.assertEqual(st[0x11000+tile*32:0x11000+(tile+8)*32],oracle(minute))
        self.assertEqual(struct.unpack_from('<H',st,HOAM+4)[0],tile|(pal<<12))
        return tile,pal

    def test_all_1440_minutes_leading_zeroes_and_invalid_values(self):
        for minute in range(1440):
            out=self.call(self.fixture,p.ENTRY_DIGITS,{0:minute})
            self.assertEqual(u32(out,0x20),int(f'{minute//60:02d}{minute%60:02d}',16),minute)
        for minute in (1440,1441,65535,0xFFFFFFFF):
            self.assertEqual(u32(self.call(self.fixture,p.ENTRY_DIGITS,{0:minute}),0x20),0xFFFFFFFF)

    def test_exact_pixels_and_only_owned_vram_palette_oam_modified(self):
        baseline=self.field()
        for minute in range(1440):
            st=clock.set_time(baseline,minute);out=self.call(st,p.ENTRY_RENDER)
            tile,pal=self.assert_pixels(out,minute)
            fixed=bytearray(out)
            for at,n in ((0x11000+tile*32,256),(0xA00+pal*32,32),(HOAM,6)):
                fixed[at:at+n]=st[at:at+n]
            self.assertEqual(fixed[0x800:0x19000],st[0x800:0x19000])
            self.assertEqual(out[0x21000:0x61000],st[0x21000:0x61000])
            self.assertEqual(out[IW+0x4644:IW+0x4A44],st[IW+0x4644:IW+0x4A44])

    def test_context_fade_script_invalid_save_and_oam_disabled_hide_release(self):
        baseline=self.field()
        cases=[(LOCK,1,1),(DISABLED,1,1),(clock.FADE+7,0x80,1),
               (clock.FADE+8,0x80,1),(clock.MAP_TYPE,0,1),(clock.MAP_TYPE,10,1),
               (IW+0x4610,0x080F16FD,4),(IW+0x4610,0,4),
               (IW+0x6F98,0,4),(IW+0x6F98,0x02000001,4)]
        for at,value,size in cases:
            with self.subTest(at=hex(at),value=hex(value)):
                st=bytearray(baseline);st[at:at+size]=value.to_bytes(size,'little')
                out=self.call(st,p.ENTRY_RENDER)
                self.assertFalse(has_hud(out))
                self.assertEqual(out[0x800:0xC00],st[0x800:0xC00])
                self.assertEqual(out[0x1000:0x19000],st[0x1000:0x19000])
                self.assertEqual(out[HOAM:HOAM+6],st[NOAM:NOAM+6])
                self.assertEqual(out[HOAM+6:HOAM+8],st[HOAM+6:HOAM+8])
                freed=self.call(st,p.ENTRY_PREPARE)
                self.assertIsNone(resource(freed,TT,64));self.assertIsNone(resource(freed,PT,16))

    def test_busy_native_oam_and_affine_matrix_are_never_borrowed(self):
        baseline=self.field()
        for attr0 in (0,0x0100,0x0300):
            st=bytearray(baseline)
            struct.pack_into('<4H',st,NOAM,attr0,72,33,0x55AA)
            struct.pack_into('<4H',st,HOAM,40,72,33,0xA55A)
            out=self.call(st,p.ENTRY_RENDER)
            self.assertEqual(out[0x800:0x19000],st[0x800:0x19000])
        st=bytearray(baseline);put16(st,NOAM,0x0200);put16(st,HOAM+6,0xA55A)
        out=self.call(st,p.ENTRY_RENDER);self.assertTrue(has_hud(out))
        self.assertEqual(out[HOAM+6:HOAM+8],b'\x5a\xa5')

    def test_suppressed_native_oam_transfer_cleans_old_hud_without_affine_write(self):
        st=bytearray(self.field());st[DISABLED]|=1;put16(st,HOAM+6,0xA55A)
        out=self.call(st,p.ENTRY_FIELD)
        self.assertFalse(has_hud(out));self.assertEqual(out[HOAM:HOAM+6],st[NOAM:NOAM+6])
        self.assertEqual(out[0xC00:HOAM],st[0xC00:HOAM])
        self.assertEqual(out[HOAM+6:HOAM+8],b'\x5a\xa5')

    def test_resource_exhaustion_tiles_metadata_and_palettes_fail_closed(self):
        st=bytearray(self.field());st[LOCK]=1
        st=bytearray(self.call(st,p.ENTRY_PREPARE));st[LOCK]=0
        for kind in ('tags','tiles','palettes'):
            with self.subTest(kind=kind):
                case=bytearray(st)
                if kind=='tags':struct.pack_into('<64H',case,TT,*range(1,65))
                if kind=='tiles':case[offset(0x0203E4D8):offset(0x0203E4D8)+128]=b'\xff'*128
                if kind=='palettes':struct.pack_into('<16H',case,PT,*range(100,116))
                out=self.call(case,p.ENTRY_PREPARE)
                self.assertIsNone(resource(out,TT,64));self.assertIsNone(resource(out,PT,16))
                self.assertEqual(out[TT:TT+128],case[TT:TT+128])
                self.assertEqual(out[PT:PT+32],case[PT:PT+32])
                self.assertFalse(has_hud(self.call(out,p.ENTRY_RENDER)))

    def test_repeated_release_reacquire_and_separate_native_resets_no_leaks(self):
        st=self.field()
        for _ in range(20):
            st=bytearray(st);st[LOCK]=1;st=self.call(st,p.ENTRY_PREPARE)
            self.assertIsNone(resource(st,TT,64));self.assertIsNone(resource(st,PT,16))
            st=bytearray(st);st[LOCK]=0;st=self.call(st,p.ENTRY_PREPARE)
            self.assertEqual(struct.unpack_from('<64H',st,TT).count(p.TAG),1)
            self.assertEqual(struct.unpack_from('<16H',st,PT).count(p.TAG),1)
        for free in (0x0814208D,0x08142379):
            st=self.call(st,free,{0:p.TAG});st=self.call(st,p.ENTRY_PREPARE)
            self.assertIsNotNone(resource(st,TT,64));self.assertIsNotNone(resource(st,PT,16))

    def test_new_wrapper_matches_v24_clock_and_save_bytes_and_preserves_abi(self):
        for st in (clock.set_elapsed(self.fixture,59,59),saved.saturated(self.fixture,1439,59),
                   saved.saturated(self.fixture,1320,17,mode=0)):
            before=self.call(st,0x090E6009);after=self.call(st,p.ENTRY_UPDATE)
            for at,n in ((offset(save1(st)),0x3668),(clock.save2(st),0xF2C)):
                self.assertEqual(after[at:at+n],before[at:at+n])
        for entry in (p.ENTRY_UPDATE,p.ENTRY_FIELD,p.ENTRY_RENDER,p.ENTRY_DIGITS,p.ENTRY_PREPARE):
            regs={r:0xBAD000+r for r in range(4,12)};regs[0]=480
            out=self.call(self.fixture,entry,regs)
            for r in range(4,12):self.assertEqual(u32(out,0x20+r*4),regs[r])
            self.assertEqual(u32(out,0x54),0x03007E00)

    def test_live_rollovers_and_saturated_native_play_time_remains_separate(self):
        for minute,want in ((359,360),(1199,1200),(1439,0)):
            st=saved.saturated(self.fixture,minute,59);self.f.restore(bytes(st));self.f.run(1)
            out=self.f.state();self.assertEqual(saved.record(out),(want,0))
            self.assertEqual(clock.elapsed(out),3599999);self.assertTrue(has_hud(out))
            # libretro serializes at frame boundary, before pending VBlank.
            # The changed minute must be visible by the NEXT frame.
            self.f.run(1);self.assertEqual(saved.record(self.f.state()),(want,1))
            self.assert_pixels(self.f.state(),want)
        st=saved.saturated(self.fixture,1439,0);self.f.restore(bytes(st));self.f.run(60)
        out=self.f.state();self.assertEqual(saved.record(out),(0,0))
        self.f.run(1);self.assert_pixels(self.f.state(),0)

    def test_live_start_party_help_and_return_without_overlay(self):
        self.field();self.f.pulse('START',60);self.assertFalse(has_hud(self.f.state()))
        self.f.pulse('A',100);self.assertFalse(has_hud(self.f.state()))
        for _ in range(3):self.f.pulse('B',80)
        self.assertTrue(has_hud(self.f.state()))
        # Native help keeps callback2 unchanged but disables OBJ rendering.
        self.f.pulse('L',90);self.assertFalse(has_hud(self.f.state()))
        self.f.pulse('A',60)  # First-use welcome explicitly requires A, not B.
        for _ in range(4):self.f.pulse('B',60)
        self.assertTrue(has_hud(self.f.state()))

    def test_unsupported_display_modes_hide_without_vram_or_palette_writes(self):
        baseline=self.field()
        for display in (0x1000,0x1043,0x1044,0x1045,0x10C0):
            st=bytearray(baseline);put16(st,0x400,display)
            out=self.call(st,p.ENTRY_RENDER)
            self.assertFalse(has_hud(out))
            self.assertEqual(out[0x800:0xC00],st[0x800:0xC00])
            self.assertEqual(out[0x1000:0x19000],st[0x1000:0x19000])
