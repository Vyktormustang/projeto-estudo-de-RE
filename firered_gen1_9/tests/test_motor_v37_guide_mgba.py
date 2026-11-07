"""Native menu buttons and guide, SHA-locked ROM; synthetic games only."""
import struct,tempfile,unittest
from pathlib import Path
from scripts import motor_v37 as p
import test_motor_v37_hud_mgba as hud
import test_motor_v24_mgba as clock
from mgba_treino_harness import Emulator,offset,u32
from test_golpes_gen9_mgba import invoke
from test_estojo_expandido_mgba import save1
from test_motor_v19_mgba import set_time
from test_eventos_fixos_mgba import OBJECTS
from battle_fixture_helpers import in_battle
TASKS=0x19000+0x7078;HANDLER=0x08139451
TEXT=offset(0x0203E6C4);PRINTER=offset(0x0203EAF0)

def menu_id(st):
    for i in range(16):
        at=TASKS+40*i
        if u32(st,at)==HANDLER and st[at+4]:return struct.unpack_from('<H',st,at+22)[0]
    return None

@unittest.skipUnless(hud.ROM and hud.CORE,'set MOTOR_V37_ROM and MGBA_CORE')
class MotorV37GuideTests(unittest.TestCase):
    setUpClass=classmethod(hud.prepare);tearDownClass=classmethod(hud.finish)
    def call(self,st,entry,regs=None):return invoke(self.f,st,entry&~1,regs or {})
    def at_sign(self,minute):return clock.MotorV24EncounterRegressionTests.at_sign(self,minute)
    def wait_menu(self,want):
        for _ in range(90):
            st=self.f.state()
            if menu_id(st)==want:
                self.assertFalse(hud.has_hud(st));return st
            self.f.pulse('A',35)
        self.fail(('menu not reached',want,menu_id(st)))
    def open_top(self,minute=600):
        self.at_sign(minute)
        original=p.encode('ROTA 1\nPALLET TOWN - VIRIDIAN CITY')
        self.assertIn(original,self.f.state()[0x21000:0x61000])
        return self.wait_menu(65)
    def select(self,index):
        for _ in range(index):self.f.pulse('DOWN',15)
        self.f.pulse('A',100)
    def message_end(self,text):
        encoded=p.encode(text)
        for _ in range(160):
            st=self.f.state()
            if st[TEXT:TEXT+len(encoded)]==encoded and u32(st,PRINTER)==0x0203E6C4+len(encoded) and st[PRINTER+27]==0:
                self.assertFalse(hud.has_hud(st))
                # Native field-message task finishes one frame after EOS.
                # Let waitmessage reach waitbuttonpress, without input.
                self.f.run(2);return self.f.state()
            self.f.pulse('A',25)
        self.fail(('text not finished',text,hex(u32(st,PRINTER))))
    def assert_exit(self):
        self.f.run(12);st=self.f.state();self.assertIsNone(menu_id(st));self.assertFalse(in_battle(st));self.assertTrue(hud.has_hud(st))
        before=st[offset(OBJECTS)+16:offset(OBJECTS)+20]
        self.f.run(24,'DOWN');self.f.run(10)
        self.assertNotEqual(self.f.state()[offset(OBJECTS)+16:offset(OBJECTS)+20],before)

    def open_group(self,g):
        if g>=6:
            self.select(6);self.assertEqual(menu_id(self.f.state()),p.ISLANDS_MENU_ID)
            if g>=11:
                self.select(5);self.assertEqual(menu_id(self.f.state()),p.MORE_MENU_ID)
                self.select(g-11)
            else:self.select(g-6)
        else:self.select(g)
        return self.wait_menu(p.GROUP_MENU_IDS[g])

    def test_all_fiftysix_area_choices_both_periods_and_no_saved_flags(self):
        for minute in (600,1320):
            top=self.open_top(minute)
            for g in range(14):
                self.f.restore(top);sub=self.open_group(g)
                for j in range(4):
                    self.f.restore(sub);self.select(j);out=self.message_end(p.AREA_TEXTS[4*g+j])
                    at=offset(save1(out));self.assertEqual(out[at:at+0x3668],sub[at:at+0x3668])
                    self.f.pulse('A' if j%2 else 'B',40)
                    self.assertEqual(menu_id(self.f.state()),p.GROUP_MENU_IDS[g],(minute,g,j))

    def test_b_returns_submenu_to_correct_parent_and_exits_top(self):
        for g in (0,5,6,7,8,9,10,11,12,13):
            self.open_top();self.open_group(g);self.f.pulse('B',40)
            self.assertEqual(menu_id(self.f.state()),p.MORE_MENU_ID if g>=11 else p.ISLANDS_MENU_ID if g>=6 else 65)
            if g>=11:self.f.pulse('B',40);self.assertEqual(menu_id(self.f.state()),p.ISLANDS_MENU_ID)
            if g>=6:self.f.pulse('B',40);self.assertEqual(menu_id(self.f.state()),65)
            self.f.pulse('B',60);self.assert_exit()

    def test_explicit_voltar_and_sair_options(self):
        for g in (2,7,8,9,10,11,12,13):
            self.open_top();self.open_group(g);self.select(4)
            self.assertEqual(menu_id(self.f.state()),p.MORE_MENU_ID if g>=11 else p.ISLANDS_MENU_ID if g>=6 else 65)
            if g>=11:self.select(3);self.assertEqual(menu_id(self.f.state()),p.ISLANDS_MENU_ID)
            if g>=6:self.select(6);self.assertEqual(menu_id(self.f.state()),65)
            self.select(7);self.assertEqual(menu_id(self.f.state()),p.UTILITY_MENU_ID);self.select(2);self.assert_exit()

    def test_rules_complete_and_period_snapshot_refresh(self):
        self.at_sign(600);st=set_time(self.f.state(),1198);self.f.restore(bytes(st))
        self.f.pulse('A',3);self.message_end(p.INTRO_DAY)
        self.wait_menu(65);self.select(7);self.select(0);self.message_end(p.RULES)
        self.f.pulse('B',40);self.message_end(p.INTRO_NIGHT)
        self.wait_menu(65);self.f.pulse('B',60);self.assert_exit()

    def test_menu_wrap_and_repeated_open_close_without_stuck_tasks(self):
        top=self.open_top();self.f.pulse('UP',20);self.f.pulse('A',60)
        self.assertEqual(menu_id(self.f.state()),p.UTILITY_MENU_ID);self.select(2);self.assert_exit()
        for _ in range(12):
            self.f.restore(top);self.open_group(13)
            for _ in range(4):
                self.select(3);self.message_end(p.AREA_TEXTS[55]);self.f.pulse('B',40)
            self.f.pulse('B',40);self.assertEqual(menu_id(self.f.state()),p.MORE_MENU_ID)
            self.f.pulse('B',40);self.assertEqual(menu_id(self.f.state()),p.ISLANDS_MENU_ID)
            self.f.pulse('B',40);self.f.pulse('B',60);self.assert_exit()

    def test_hidden_preference_and_postcap_clock_continue_inside_guide(self):
        import test_motor_v37_preferences_mgba as pref
        self.at_sign(600);st=clock.saturated(self.f.state(),1320,17);st=pref.set_pref(st)
        self.f.restore(bytes(st));self.wait_menu(65);self.open_group(13)
        before=clock.progress(self.f.state());self.f.run(120)
        self.assertEqual((clock.progress(self.f.state())-before)%86400,120)
        self.assertEqual(pref.pref(self.f.state()),(hud.p.PREFERENCE_MAGIC,hud.p.HIDDEN))
        self.select(0);self.message_end(p.AREA_TEXTS[52])
        for _ in range(5):self.f.pulse('B',60)
        self.assertIsNone(menu_id(self.f.state()));self.assertFalse(hud.has_hud(self.f.state()))

    def test_existing_native_menu_ids_render_and_cancel(self):
        self.f.close()
        try:
            with tempfile.TemporaryDirectory() as directory:
                for ident in (0,15,31,39,64):
                    data=bytearray(self.source);script=p.previous.ORIGINAL_MESSAGE+bytes((0x69,0x6f,1,1,ident,0,0x6b,0x02))
                    data[p.SCRIPT_OFFSET:p.SCRIPT_OFFSET+len(script)]=script
                    rom=Path(directory)/f'menu-{ident}.gba';rom.write_bytes(data)
                    self.f=Emulator(rom,Path(hud.CORE),Path(directory))
                    try:
                        self.at_sign(600);self.wait_menu(ident);self.f.pulse('B',60);self.assert_exit()
                    finally:self.f.close()
        finally:type(self).f=self.f=Emulator(self.rom,Path(hud.CORE),self.dir)

    def test_utilities_cancel_and_explicit_voltar_return_to_origin(self):
        pages=(65,p.ISLANDS_MENU_ID,p.MORE_MENU_ID)
        for page in range(3):
            for button in ('B','A'):
                self.open_top()
                if page>=1:self.select(6)
                if page==2:self.select(5)
                self.select(4 if page==2 else 7);self.assertEqual(menu_id(self.f.state()),p.UTILITY_MENU_ID)
                if button=='A':self.select(1)
                else:self.f.pulse('B',40)
                self.assertEqual(menu_id(self.f.state()),pages[page])
                for _ in range(page):self.f.pulse('B',40)
                self.f.pulse('B',60);self.assert_exit()

    def test_second_page_wrap_and_sair(self):
        self.open_top();self.select(6);self.f.pulse('UP',20);self.f.pulse('A',60)
        self.assertEqual(menu_id(self.f.state()),p.UTILITY_MENU_ID);self.select(2);self.assert_exit()

    def test_rules_from_second_page_refresh_and_return_to_first(self):
        self.open_top(1320);self.select(6);self.select(7);self.select(0)
        self.message_end(p.RULES);self.f.pulse('B',40);self.message_end(p.INTRO_NIGHT)
        self.wait_menu(65);self.f.pulse('B',60);self.assert_exit()

    def test_third_page_back_voltar_wrap_and_sair(self):
        for button in ('B','A'):
            self.open_top();self.select(6);self.select(5)
            self.assertEqual(menu_id(self.f.state()),p.MORE_MENU_ID)
            if button=='A':self.select(3)
            else:self.f.pulse('B',40)
            self.assertEqual(menu_id(self.f.state()),p.ISLANDS_MENU_ID)
            self.select(6);self.assertEqual(menu_id(self.f.state()),65)
            self.f.pulse('B',60);self.assert_exit()
        self.open_top();self.select(6);self.select(5)
        self.f.pulse('UP',20);self.f.pulse('A',60)
        self.assertEqual(menu_id(self.f.state()),p.UTILITY_MENU_ID)
        self.select(2);self.assert_exit()

    def test_rules_from_third_page_refresh_and_return_to_first(self):
        self.open_top(1320);self.select(6);self.select(5);self.select(4);self.select(0)
        self.message_end(p.RULES);self.f.pulse('B',40);self.message_end(p.INTRO_NIGHT)
        self.wait_menu(65);self.f.pulse('B',60);self.assert_exit()
