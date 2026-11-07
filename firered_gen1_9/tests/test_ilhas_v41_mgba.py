"""Read-only island audit on exact v41. Synthetic arrival/progression/balls.

Transport and native legendary interactions use normal buttons after preparation.
No injected enemy, puzzle counter, battle result or cross-ROM savestate.
"""
import json,os,struct,tempfile,unittest
from pathlib import Path
from scripts import motor_v41 as p,auditar_ilhas_v41 as audit
from mgba_treino_harness import Emulator,offset,u32,mon_facts
from test_motor_v40_encounters_mgba import MotorV40EncounterTests
from test_motor_v41_mgba import MotorV41NativeTests
from test_motor_v40_guide_mgba import menu_id,TASKS
from test_eventos_fixos_mgba import route_entry_fixture,route_from_entry,enemy,active_objects
from test_atualizacoes_gen9_mgba import copy_ewram
from test_estojo_expandido_mgba import add,get
from test_motor_v19_mgba import set_time
from test_golpes_gen9_integracao import save_game,load_game
from test_motor_v12_mgba import text
from battle_fixture_helpers import in_battle,main_callback2,BATTLE_OUTCOME
import test_motor_v21_gameplay_mgba as game
ROM=os.environ.get('ILHAS_V41_ROM');CORE=os.environ.get('MGBA_CORE')

@unittest.skipUnless(ROM and CORE,'set ILHAS_V41_ROM and MGBA_CORE')
class IslandNativeTests(unittest.TestCase):
    call=MotorV40EncounterTests.call
    shot=MotorV41NativeTests.shot
    throw_first_ball=game.MotorV21GameplayTests.throw_first_ball
    assert_ball_metadata=game.MotorV21GameplayTests.assert_ball_metadata
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM);cls.source=cls.rom.read_bytes();audit.audit(cls.source)
        cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
        cls.f=Emulator(cls.rom,Path(CORE),cls.dir);cls.fixture=route_entry_fixture(cls.f);cls.observations=[];cls.cache={}
    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if cls.rom.read_bytes()!=cls.source:raise AssertionError('ROM changed')
        if os.environ.get('ILHAS_V41_OBSERVATIONS'):
            with Path(os.environ['ILHAS_V41_OBSERVATIONS']).open('x') as f:json.dump(cls.observations,f,indent=2);f.write('\n')
    def switch(self,rom):
        self.f.close();type(self).f=self.f=Emulator(rom,Path(CORE),self.dir)
    def var(self,st,var):
        result=u32(self.call(st,0x0808E9D4,{0:var}),0x20);self.f.restore(st);return result
    def flag(self,st,flag):
        result=u32(self.call(st,0x0808EB88,{0:flag}),0x20);self.f.restore(st);return result
    def setvar(self,st,var,value):return copy_ewram(st,self.call(st,0x0808EA14,{0:var,1:value}))
    def setflag(self,st,flag,value=True):return copy_ewram(st,self.call(st,0x0808EB38 if value else 0x0808EB60,{0:flag}))
    def tasks(self,st):return tuple(sorted(u32(st,TASKS+i*40) for i in range(16) if st[TASKS+i*40+4]))

    def bootstrap(self,g,m,x,y):
        key=(g,m,x,y)
        if key in self.cache:return self.cache[key]
        data=bytearray(self.source);sign=p.base.previous.SIGN_POINTER
        self.assertEqual(data[0xF90000:0xF9000A],b'\xff'*10)
        struct.pack_into('<I',data,sign,0x08F90000);data[0xF90000:0xF9000A]=struct.pack('<BBBBHHBB',0x39,g,m,255,x,y,0x27,2)
        restored=bytearray(data)
        for at,n in ((sign,4),(0xF90000,10)):restored[at:at+n]=self.source[at:at+n]
        self.assertEqual(bytes(restored),self.source)
        path=self.dir/f'arrival-{g}-{m}-{x}-{y}.gba';path.write_bytes(data);self.switch(path)
        fresh=route_entry_fixture(self.f);st=set_time(fresh,600);st=self.setvar(st,0x4020,200)
        if (g,m)==(3,5):
            st=self.setvar(st,0x407E,3);st=self.setvar(st,0x4076,5)
        self.f.restore(bytes(st));route_from_entry(self.f)
        self.f.run(64,'LEFT');self.f.run(30);self.f.run(24,'UP');self.f.run(120)
        # The sign may already have warped during approach; avoid talking to
        # a destination NPC with a redundant A press after a fast transition.
        if game.location(self.f.state())!=(g,m):self.f.pulse('A',150)
        self.f.run(150)
        for _ in range(240):
            arrived=self.f.state()
            if game.location(arrived)==(g,m) and main_callback2(arrived)==main_callback2(self.fixture):break
            self.assertFalse(in_battle(arrived));self.f.run(2)
        arrived=self.f.state();self.assertEqual(game.location(arrived),(g,m));self.assertEqual(game.coords(arrived),(x+7,y+7))
        self.assertEqual(main_callback2(arrived),main_callback2(self.fixture))
        flash=save_game(self.f);self.switch(self.rom);loaded=load_game(self.f,flash)
        self.assertEqual(game.location(loaded),(g,m));self.assertEqual(game.coords(loaded),(x+7,y+7))
        self.assertFalse(in_battle(loaded));self.assertEqual(main_callback2(loaded),main_callback2(self.fixture))
        self.cache[key]=loaded;return loaded

    def ferry_state(self,arrived,items,flags,stage=5,scene=3):
        st=self.setvar(arrived,0x407E,scene);st=self.setvar(st,0x4076,stage)
        for i in range(2):
            if items&(1<<i):st=add(self.f,st,370+i,1)
            st=self.setflag(st,0x84A+i,bool(flags&(1<<i)))
            st=self.setflag(st,0x2F0+i) # Suppress previously-shown-ticket greeting in the truth-table fixture.
        self.f.restore(bytes(st));self.f.run(8,'DOWN');self.f.run(25);self.f.pulse('A',450)
        return self.f.state()

    def test_fresh_game_does_not_start_with_tickets_or_enable_flags(self):
        for item,flag in ((370,0x84A),(371,0x84B)):
            self.assertEqual(get(self.f,self.fixture,item),0)
            self.assertEqual(self.flag(self.fixture,flag),0)
            self.observations.append(dict(probe='fresh_game',item=item,quantity=0,flag=f'{flag:04X}',enabled=False))

    def test_ferry_ticket_and_flag_matrix_and_actual_two_destinations(self):
        arrived=self.bootstrap(3,5,24,32);denial_tasks=None;both=None
        for items in range(4):
            for flags in range(4):
                st=self.ferry_state(arrived,items,flags);available=items&flags
                want={0:None,1:54,2:55,3:56}[available]
                self.assertEqual(menu_id(st),want,(items,flags,game.location(st),self.tasks(st)))
                self.assertEqual(game.location(st),(3,5));self.assertFalse(in_battle(st))
                if not available:
                    # Native Rainbow greeting has a paragraph break (FB).
                    # Finish it before asserting the regular destination menu.
                    self.f.pulse('A',450);st=self.f.state()
                    want=255 # Native dynamically-built Seagallop menu.
                    self.assertEqual(menu_id(st),want);self.assertEqual(game.location(st),(3,5))
                    self.assertNotEqual(self.tasks(st),self.tasks(arrived))
                    if denial_tasks is None:denial_tasks=self.tasks(st);self.shot('FERRY_SEM_LIBERACAO.png')
                    self.assertEqual(self.tasks(st),denial_tasks)
                    self.f.pulse('B',90);self.f.run(24,'UP');self.f.run(20)
                    self.assertNotEqual(game.coords(self.f.state()),game.coords(st),'Regular menu did not cancel/release control')
                    self.assertEqual(game.location(self.f.state()),(3,5))
                if available==3:both=st;self.shot('FERRY_DUAS_ILHAS.png')
                self.observations.append(dict(probe='ferry_matrix',item_bits=items,flag_bits=flags,menu=want))
        for stage,want in ((1,57),(4,57)):
            st=self.ferry_state(arrived,3,3,stage=stage)
            for _ in range(60):
                if menu_id(st)==want:break
                self.f.pulse('A',35);st=self.f.state()
            self.shot(f'FERRY_ESTAGIO_{stage}.png');self.assertEqual(menu_id(st),want)
            self.observations.append(dict(probe='ferry_stage',stage=stage,menu=want))
        for choice,label,g,m in ((1,'NAVEL',2,59),(2,'BIRTH',2,58)):
            self.f.restore(both)
            for _ in range(choice):self.f.pulse('DOWN',15)
            self.f.pulse('A',120)
            for _ in range(240):
                st=self.f.state()
                if game.location(st)==(g,m) and main_callback2(st)==main_callback2(self.fixture):break
                self.f.pulse('A',45)
            self.f.run(180);st=self.f.state();self.assertEqual(game.location(st),(g,m),(label,game.location(st)))
            self.assertFalse(in_battle(st));self.shot(f'CHEGADA_{label}.png')
            self.observations.append(dict(probe='native_ferry_trip',destination=label,group=g,map=m,
                synthetic_tickets_and_progress=True,native_buttons_only_after_prepare=True))

    def wait_battle(self,species,level):
        for _ in range(120):
            if in_battle(self.f.state()):break
            self.f.run(30)
        self.assertTrue(in_battle(self.f.state()),(species,game.location(self.f.state()),active_objects(self.f.state())))
        self.f.run(300)
        for _ in range(6):self.f.pulse('B',45)
        st=self.f.state();self.assertIn('vai fazer?',text(st));self.assertEqual((enemy(st)['species'],enemy(st)['level']),(species,level))
        self.assertTrue(enemy(st)['valid']);self.assertEqual(u32(st,offset(0x02020374))&8,0)
        self.shot(f'BATALHA_{species}.png');return self.f.state()

    def capture_and_reload(self,before,species,fought,hidden,location):
        self.throw_first_ball()
        for _ in range(90):
            st=self.f.state()
            if not in_battle(st) and main_callback2(st)==main_callback2(self.fixture):break
            self.f.pulse('B',90)
        self.f.run(120);caught=self.f.state()
        self.assertFalse(in_battle(caught));self.assertEqual(caught[offset(BATTLE_OUTCOME)],7)
        self.assertEqual(game.location(caught),location);self.assertEqual(caught[game.PARTY_COUNT],2)
        data=game.party_slot(caught,1);facts=mon_facts(data)
        self.assertTrue(facts['valid']);self.assertEqual(facts['species'],species)
        self.assertEqual(data[:4],before[offset(0x0203A734):offset(0x0203A734)+4]);self.assert_ball_metadata(data,1)
        self.assertEqual(game.party_slot(caught,0),game.party_slot(before,0));self.assertEqual(get(self.f,caught,1),0)
        self.assertEqual(self.flag(caught,fought),1);self.assertEqual(self.flag(caught,hidden),1)
        self.f.restore(caught);flash=save_game(self.f);self.switch(self.rom);loaded=load_game(self.f,flash)
        self.assertEqual(game.party_slot(loaded,1),data);self.assertEqual(loaded[game.PARTY_COUNT],2)
        self.assertEqual(game.location(loaded),location);self.assertEqual(self.flag(loaded,fought),1);self.assertEqual(self.flag(loaded,hidden),1)
        self.assertEqual(get(self.f,loaded,1),0)
        local_id=2 if species==386 else 1
        self.assertFalse(any(o[:3]==(local_id,location[1],location[0]) for o in active_objects(loaded)))
        self.observations.append(dict(probe='native_event_capture',species=species,level=facts['level'],fought_flag=f'{fought:04X}',
            hidden_flag=f'{hidden:04X}',saved_and_reloaded=True,synthetic_arrival=True,ball='synthetic Master Ball'))

    def test_lugia_native_interaction_capture_and_persistence(self):
        st=self.bootstrap(2,38,10,16);st=add(self.f,st,1,1);self.f.restore(bytes(st))
        self.f.run(8,'UP');self.f.run(30);self.f.pulse('A',120)
        before=self.wait_battle(249,70);self.capture_and_reload(before,249,0x2F2,0x9B,(2,38))

    def step(self,button):
        origin=game.coords(self.f.state())
        for _ in range(40):
            self.f.run(1,button)
            if game.coords(self.f.state())!=origin:break
        else:self.fail(('step blocked',button,origin,active_objects(self.f.state())))
        self.f.run(20)
        now=game.coords(self.f.state());self.assertEqual(abs(now[0]-origin[0])+abs(now[1]-origin[1]),1)

    def test_hooh_coordinate_trigger_capture_and_persistence(self):
        st=self.bootstrap(2,37,9,13);st=add(self.f,st,1,1);self.f.restore(bytes(st));self.step('UP')
        before=self.wait_battle(250,70);self.capture_and_reload(before,250,0x2F3,0x9C,(2,37))

    def test_deoxys_full_triangle_puzzle_capture_and_persistence(self):
        st=self.bootstrap(2,56,15,13);st=add(self.f,st,1,1);self.f.restore(bytes(st))
        rocks=((15,12),(11,14),(15,8),(19,14),(12,11),(18,11),(15,14),(11,14),(19,14),(15,15),(15,10))
        stands=((15,13),(12,14),(15,9),(18,14),(13,11),(17,11),(15,13),(12,14),(18,14),(15,14),(15,11))
        caps=(0,4,8,8,8,4,4,4,6,3,3)
        for i,((rx,ry),(x,y)) in enumerate(zip(rocks,stands)):
            # Coordinates are confirmed against the actual moving object at every stage.
            state=self.f.state();rock=next(o for o in active_objects(state) if o[:3]==(1,56,2))
            self.assertEqual(rock[4],(rx+7,ry+7))
            cx,cy=game.coords(state);cx-=7;cy-=7
            for _ in range(abs(x-cx)):self.step('RIGHT' if x>cx else 'LEFT')
            for _ in range(abs(y-cy)):self.step('DOWN' if y>cy else 'UP')
            self.assertEqual(game.coords(self.f.state()),(x+7,y+7))
            facing='RIGHT' if rx>x else 'LEFT' if rx<x else 'DOWN' if ry>y else 'UP'
            self.f.run(8,facing);self.f.run(25)
            steps=self.var(self.f.state(),0x4026);self.assertEqual(steps,caps[i])
            self.f.pulse('A',180)
            state=self.f.state()
            if i<10:
                self.assertEqual(self.var(state,0x403E),i+1)
                self.observations.append(dict(probe='deoxys_puzzle_stage',interaction=i+1,player=[x,y],steps=steps,next_stage=i+1))
            else:self.observations.append(dict(probe='deoxys_puzzle_solved',interaction=11,steps=steps,total_steps=52))
        before=self.wait_battle(386,30);self.capture_and_reload(before,386,0x2E4,0x99,(2,56))
