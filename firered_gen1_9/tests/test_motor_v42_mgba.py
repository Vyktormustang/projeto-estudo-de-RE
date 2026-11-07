"""Exact v42: native sailor delivery, capacity/flags, legacy flash and regressions.

Progress/arrival/Rainbow Pass are synthetic fixtures. Tickets and enable flags in
new-delivery tests come only from the actual sailor interaction. No personal saves.
"""
import json,os,struct,tempfile,unittest
from pathlib import Path
from scripts import motor_v42 as p
from mgba_treino_harness import Emulator,offset,u32
from test_ilhas_v41_mgba import IslandNativeTests
from test_motor_v41_mgba import MotorV41NativeTests
from test_motor_v40_guide_mgba import menu_id,MotorV40GuideTests
from test_eventos_fixos_mgba import route_entry_fixture
from test_estojo_expandido_mgba import add,get,call as bag_call,REMOVE
from test_atualizacoes_gen9_mgba import pocket,pocket_ids
from test_golpes_gen9_integracao import save_game,load_game
from battle_fixture_helpers import main_callback2,in_battle
import test_motor_v21_gameplay_mgba as game
ROM=os.environ.get('MOTOR_V42_ROM');BASE=os.environ.get('MOTOR_V42_BASE');CORE=os.environ.get('MGBA_CORE')
PRESERVED_FLAGS=(0x2F2,0x2F3,0x2E4,0x2F5,0x2F6,0x2F7,0x9B,0x9C,0x99,0x9A,0x2A7,0x2A8)

class MotorV42NativeTests(IslandNativeTests):
    __unittest_skip__=not bool(ROM and BASE and CORE)
    __unittest_skip_why__='set MOTOR_V42_ROM, MOTOR_V42_BASE and MGBA_CORE'
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM);cls.base=Path(BASE);cls.source=cls.rom.read_bytes()
        if p.digest(cls.source)!=p.OUTPUT_SHA256 or p.digest(cls.base.read_bytes())!=p.BASE_SHA256:raise ValueError('Wrong ROM')
        cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
        cls.f=Emulator(cls.rom,Path(CORE),cls.dir);cls.fixture=route_entry_fixture(cls.f);cls.cache={};cls.observations=[]
    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if p.digest(cls.rom.read_bytes())!=p.OUTPUT_SHA256 or p.digest(cls.base.read_bytes())!=p.BASE_SHA256:raise AssertionError('ROM changed')
        if os.environ.get('MOTOR_V42_OBSERVATIONS'):
            with Path(os.environ['MOTOR_V42_OBSERVATIONS']).open('x') as f:json.dump(cls.observations,f,indent=2);f.write('\n')
    def qty(self,st,item):
        value=get(self.f,st,item);self.f.restore(st);return value
    def prepared(self,arrived,scene=3,stage=5,rainbow=True,owned=(),flags=()):
        st=self.setvar(arrived,0x407E,scene);st=self.setvar(st,0x4076,stage)
        if rainbow:st=add(self.f,st,368,1)
        for item in owned:st=add(self.f,st,item,1)
        for flag in (0x84A,0x84B):st=self.setflag(st,flag,flag in flags)
        return bytes(st)
    def talk(self,st):
        self.f.restore(st);self.f.run(8,'DOWN');self.f.run(25);self.f.pulse('A',450);return self.f.state()
    def finish_menu(self,want=None):
        for _ in range(100):
            st=self.f.state();ident=menu_id(st)
            if ident in (54,55,56,57,255):
                if want is not None:self.assertEqual(ident,want)
                return st
            self.f.pulse('A',35)
        self.fail('No native ferry menu')
    def wait_text(self,index):return MotorV40GuideTests.message_end(self,p.TEXTS[index])
    def assert_pair(self,st,items=(1,1),flags=(1,1)):
        for i in range(2):
            self.assertEqual(self.qty(st,370+i),items[i]);self.assertEqual(self.flag(st,0x84A+i),flags[i])
    def cancel(self):self.f.pulse('B',90);return self.f.state()
    def fill_keys(self,st,free=0):
        capacity=pocket(st,1)[1];initial=set(pocket_ids(st,1));fillers=[]
        for item in range(1,375):
            if sum(bool(x) for x in pocket_ids(st,1))>=capacity-free:break
            at=p.items.NEW_ITEMS+item*p.items.ITEM_SIZE
            if self.source[at+26]!=2 or item in initial or item in (368,370,371):continue
            st=add(self.f,st,item,1);fillers.append(item)
        self.assertEqual(sum(bool(x) for x in pocket_ids(st,1)),capacity-free)
        return bytes(st),fillers

    def test_eligible_receive_both_repeat_and_native_trips(self):
        arrived=self.bootstrap(3,5,24,32);st=self.prepared(arrived)
        self.talk(st);self.wait_text(0);self.shot('V42_MYSTIC_RECEBIDO.png')
        self.f.pulse('A',60);self.wait_text(2);self.shot('V42_AURORA_RECEBIDO.png')
        menu=self.finish_menu(56);self.assert_pair(menu)
        for f in (0x2A7,0x2A8):self.assertEqual(self.flag(menu,f),0,'Do not forge Mystery Gift receipt flags')
        self.shot('V42_DESTINOS_LIBERADOS.png')
        for _ in range(3):
            field=self.cancel();again=self.talk(field);self.assertEqual(menu_id(again),56,'No repeated delivery messages');self.assert_pair(again)
        field=self.cancel();before=game.coords(field);self.f.run(24,'UP')
        self.assertNotEqual(game.coords(self.f.state()),before);self.f.run(3600)
        self.assertFalse(in_battle(self.f.state()));self.assertEqual(main_callback2(self.f.state()),main_callback2(self.fixture))
        for choice,destination in ((1,(2,59)),(2,(2,58))):
            self.f.restore(menu)
            for _ in range(choice):self.f.pulse('DOWN',15)
            self.f.pulse('A',120)
            for _ in range(240):
                if game.location(self.f.state())==destination:break
                self.f.pulse('A',45)
            self.f.run(180);self.assertEqual(game.location(self.f.state()),destination)
            self.shot(f'V42_PORTO_{destination[1]}.png')
            self.observations.append(dict(probe='earned_ticket_trip',destination=list(destination),tickets_injected=False,progress_and_rainbow_synthetic=True))

    def test_native_inventory_flag_matrix_repairs_without_duplicates(self):
        arrived=self.bootstrap(3,5,24,32)
        for item_bits in range(4):
            for flag_bits in range(4):
                st=self.prepared(arrived,owned=[370+i for i in range(2) if item_bits&(1<<i)],flags=[0x84A+i for i in range(2) if flag_bits&(1<<i)])
                self.talk(st);menu=self.finish_menu(56);self.assert_pair(menu)
                self.observations.append(dict(probe='v42_delivery_matrix',items_before=item_bits,flags_before=flag_bits,items_after=[1,1],flags_after=[1,1]))

    def test_native_progress_and_real_rainbow_pass_guards(self):
        arrived=self.bootstrap(3,5,24,32)
        for scene,stage,rainbow,tea,want in ((3,5,False,False,255),(3,5,False,True,255),(3,4,True,False,57),(3,1,True,False,57),(0,5,True,False,None),(4,5,True,False,None),(3,0,True,False,None)):
            st=self.prepared(arrived,scene,stage,rainbow)
            if tea:st=add(self.f,st,369,1)
            self.talk(st)
            if want is None:
                for _ in range(8):self.f.pulse('B',60)
                end=self.f.state();self.assertIsNone(menu_id(end))
            else:end=self.finish_menu(want)
            self.assert_pair(end,(0,0),(0,0))
            self.observations.append(dict(probe='v42_guard',scene=scene,stage=stage,rainbow=rainbow,tea=tea,granted=False))
        self.talk(self.prepared(arrived,stage=6));self.assert_pair(self.finish_menu(56))

    def test_full_key_pocket_partial_delivery_retry_and_capture_flags(self):
        arrived=self.bootstrap(3,5,24,32);st=self.prepared(arrived);st,fillers=self.fill_keys(st)
        self.talk(st);self.wait_text(4);self.shot('V42_BOLSA_CHEIA.png');end=self.finish_menu(255);self.assert_pair(end,(0,0),(0,0))
        self.talk(self.setflag(st,0x84B));self.assert_pair(self.finish_menu(255),(0,0),(0,1))
        self.f.restore(end);field=self.cancel();ok,field=bag_call(self.f,field,REMOVE,fillers[-1],1);self.assertEqual(ok,1)
        self.talk(field);self.wait_text(0);self.f.pulse('A',60);self.wait_text(4);self.shot('V42_ENTREGA_PARCIAL.png')
        end=self.finish_menu(54);self.assert_pair(end,(1,0),(1,0))
        field=self.cancel();ok,field=bag_call(self.f,field,REMOVE,fillers[-2],1);self.assertEqual(ok,1)
        self.talk(field);end=self.finish_menu(56);self.assert_pair(end)
        # Separate full-pocket fixture: already-owned tickets must not need space.
        st=self.prepared(arrived,owned=(370,371));st,_=self.fill_keys(st)
        expected={flag:i%2 for i,flag in enumerate(PRESERVED_FLAGS)}
        for flag,value in expected.items():st=self.setflag(st,flag,bool(value))
        self.talk(st);self.wait_text(1);self.shot('V42_BILHETE_EXISTENTE.png');end=self.finish_menu(56);self.assert_pair(end)
        for flag,value in expected.items():self.assertEqual(self.flag(end,flag),value)
        st=self.prepared(arrived,owned=(371,));st,_=self.fill_keys(st)
        self.talk(st);self.wait_text(3);self.shot('V42_AURORA_EXISTENTE_BOLSA_CHEIA.png')
        self.assert_pair(self.finish_menu(55),(0,1),(0,1))
        self.observations.append(dict(probe='v42_capacity',aurora_repaired_despite_mystic_failure=True,full_no_grant=True,one_free_partial=True,retry_second_only=True,full_owned_repair=True,capture_flags_preserved=True))

    def test_v41_save_upgrade_without_reentry_and_downgrade_roundtrip(self):
        arrived=self.bootstrap(3,5,24,32);st=self.prepared(arrived);self.f.restore(st);flash=save_game(self.f)
        try:
            self.switch(self.base);old=load_game(self.f,flash);self.assert_pair(old,(0,0),(0,0))
            self.f.run(120);old_flash=save_game(self.f);self.assertNotEqual(old_flash,flash)
            self.switch(self.rom);loaded=load_game(self.f,old_flash);self.assertEqual(game.location(loaded),(3,5))
            # No warp/reentry: old NPC template pointers must execute the new script.
            self.talk(loaded);menu=self.finish_menu(56);self.assert_pair(menu);self.cancel();earned_flash=save_game(self.f)
            self.switch(self.base);old=load_game(self.f,earned_flash);self.assert_pair(old)
            self.talk(old);self.finish_menu(56);self.cancel();back=save_game(self.f)
            self.assertNotEqual(back,earned_flash)
            self.switch(self.rom);loaded=load_game(self.f,back);self.assert_pair(loaded)
            self.talk(loaded);self.assert_pair(self.finish_menu(56))
            self.observations.append(dict(probe='v42_legacy_flash',upgraded_from_v41_without_map_reentry=True,earned_items_persist=True,v42_v41_v42=True))
        finally:self.switch(self.rom)

    # Complete Type: Null distribution regression on the exact new ROM.
    state=MotorV41NativeTests.state
    generate=MotorV41NativeTests.generate
    variant=MotorV41NativeTests.variant
    test_all_variants_1800_quantiles_plus_invalid_fallback_day_night=MotorV41NativeTests.test_all_variants_1800_quantiles_plus_invalid_fallback_day_night
