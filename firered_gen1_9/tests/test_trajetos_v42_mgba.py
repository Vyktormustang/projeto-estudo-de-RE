"""Two continuous native journeys from Vermilion, including captures and return.

Only initial Vermilion arrival/progression/Rainbow Pass/Master Balls are prepared.
After start: buttons, read-only isolated probes and native save/fresh-core Continue.
No island warp injection, encounter injection, forced puzzle counter or rewind.
"""
import json,os,tempfile,unittest
from pathlib import Path
from scripts import motor_v42 as p,auditar_trajetos_v42 as topology
from mgba_treino_harness import Emulator,offset,u32,mon_facts
import test_ilhas_v41_mgba as old
import test_motor_v42_mgba as delivery
from test_eventos_fixos_mgba import route_entry_fixture,active_objects,enemy
from test_estojo_expandido_mgba import add
from test_golpes_gen9_integracao import save_game,load_game
from test_motor_v40_guide_mgba import menu_id
from battle_fixture_helpers import in_battle,main_callback2,BATTLE_OUTCOME
import test_motor_v21_gameplay_mgba as game
ROM=os.environ.get('TRAJETOS_V42_ROM');CORE=os.environ.get('MGBA_CORE')

@unittest.skipUnless(ROM and CORE,'set TRAJETOS_V42_ROM and MGBA_CORE')
class ContinuousIslandJourneys(unittest.TestCase):
    call=old.IslandNativeTests.call
    switch=old.IslandNativeTests.switch
    flag=old.IslandNativeTests.flag
    var=old.IslandNativeTests.var
    shot=old.IslandNativeTests.shot
    qty=delivery.MotorV42NativeTests.qty
    throw_first_ball=game.MotorV21GameplayTests.throw_first_ball
    assert_ball_metadata=game.MotorV21GameplayTests.assert_ball_metadata
    wait_battle=old.IslandNativeTests.wait_battle
    wait_text=delivery.MotorV42NativeTests.wait_text
    assert_pair=delivery.MotorV42NativeTests.assert_pair
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM);cls.source=cls.rom.read_bytes();cls.maps=topology.world(cls.source)
        cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
        cls.f=Emulator(cls.rom,Path(CORE),cls.dir);cls.fixture=route_entry_fixture(cls.f)
        cls.cache={};cls.observations=[];cls.trace=[]
    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if cls.rom.read_bytes()!=cls.source:raise AssertionError('ROM changed')
        if os.environ.get('TRAJETOS_V42_OBSERVATIONS'):
            with Path(os.environ['TRAJETOS_V42_OBSERVATIONS']).open('x') as f:
                json.dump(dict(rom_sha256=p.OUTPUT_SHA256,observations=cls.observations,trace=cls.trace),f,indent=2);f.write('\n')
    def setUp(self):self.live=False;self.case=self._testMethodName;self.caught={};self.events={};self.walks=0;self.warps=0;self.boats=0;self.visited=set()
    def setvar(self,*args):
        self.assertFalse(self.live,'No state edits during the journey');return old.IslandNativeTests.setvar(self,*args)
    def setflag(self,*args):
        self.assertFalse(self.live,'No state edits during the journey');return old.IslandNativeTests.setflag(self,*args)
    def bootstrap(self,*args):
        self.assertFalse(self.live);self.assertEqual(args,(3,5,24,32),'Only Vermilion may be bootstrapped')
        return old.IslandNativeTests.bootstrap(self,*args)
    def record(self,kind,**fields):
        self.observations.append(dict(journey=self.case,kind=kind,**fields));print(f'{self.case}: {kind} {fields}',flush=True)
    def xy(self,st=None):return tuple(n-7 for n in game.coords(self.f.state() if st is None else st))
    def menu(self,want):
        for _ in range(100):
            st=self.f.state()
            if menu_id(st)==want:return st
            self.f.pulse('A',35)
        self.fail(('menu',want,menu_id(self.f.state()),game.location(self.f.state())))
    def begin(self,choice,balls):
        arrived=self.bootstrap(3,5,24,32)
        st=delivery.MotorV42NativeTests.prepared(self,arrived)
        st=self.setvar(st,0x4020,0) # No expiring synthetic Repel mid-journey.
        st=add(self.f,st,1,balls);self.f.restore(bytes(st));self.live=True
        self.record('start',map=[3,5],xy=list(self.xy()),synthetic=['arrival','progress','Rainbow Pass','Master Balls'],tickets_injected=False)
        self.f.run(8,'DOWN');self.f.run(25);self.f.pulse('A',450)
        self.wait_text(0);self.shot(f'{self.case}_MYSTIC.png');self.f.pulse('A',60)
        self.wait_text(2);self.shot(f'{self.case}_AURORA.png');menu=self.menu(56);self.assert_pair(menu)
        self.record('tickets_earned',mystic=1,aurora=1)
        self.sail(choice,(2,59 if choice==1 else 58))
    def sail(self,choice,destination):
        origin=game.location(self.f.state())
        for _ in range(choice):self.f.pulse('DOWN',15)
        self.f.pulse('A',120)
        for _ in range(240):
            st=self.f.state()
            if game.location(st)==destination and main_callback2(st)==main_callback2(self.fixture):break
            self.f.pulse('A',45)
        self.f.run(180);st=self.f.state();self.assertEqual(game.location(st),destination);self.assertFalse(in_battle(st))
        self.assertEqual(main_callback2(st),main_callback2(self.fixture));self.boats+=1;self.visited.add(destination)
        self.record('boat',origin=list(origin),destination=list(destination),xy=list(self.xy(st)))
        self.shot(f'{self.case}_BARCO_{self.boats}.png')
    def move_one(self,button,allow_battle=False):
        before=self.f.state();where=game.location(before);origin=self.xy(before)
        for _ in range(40):
            self.f.run(1,button);now=self.f.state()
            if self.xy(now)!=origin:break
        else:self.fail(('blocked step',where,origin,button,active_objects(now)))
        end=self.xy(now);self.assertEqual(game.location(now),where)
        self.assertEqual(abs(end[0]-origin[0])+abs(end[1]-origin[1]),1)
        self.trace.append(dict(journey=self.case,kind='walk',group=where[0],map=where[1],x=origin[0],y=origin[1],button=button,next_x=end[0],next_y=end[1]))
        self.walks+=1;self.f.run(20)
        if not allow_battle:self.assertFalse(in_battle(self.f.state()))
    def walk(self,goal):
        st=self.f.state();key=game.location(st);m=self.maps[key]
        blocked={tuple(n-7 for n in o[4]) for o in active_objects(st) if o[0]!=255 and o[1:3]==(key[1],key[0])}
        route=topology.cell_route(m,self.xy(st),goal,blocked)
        for button,xy in route:
            self.move_one(button)
            self.assertEqual(self.xy(),xy);self.assertEqual(game.location(self.f.state()),key)
    def cross(self,warp):
        origin=game.location(self.f.state());self.walk(warp.xy)
        if warp.behavior in (0x62,0x63,0x64,0x65):
            direction={0x62:'RIGHT',0x63:'LEFT',0x64:'UP',0x65:'DOWN'}[warp.behavior]
            self.f.run(8,direction)
        self.f.run(240);st=self.f.state()
        self.assertEqual(game.location(st),warp.destination,(origin,warp,self.xy(st)))
        self.assertEqual(main_callback2(st),main_callback2(self.fixture));self.assertFalse(in_battle(st))
        self.visited.add(warp.destination);self.warps+=1
        self.trace.append(dict(journey=self.case,kind='warp',origin=list(origin),warp_id=warp.index,warp_xy=list(warp.xy),destination=list(warp.destination),destination_id=warp.destination_id,arrival_xy=list(self.xy(st))))
        self.record('warp',origin=list(origin),destination=list(warp.destination),arrival=list(self.xy(st)))
    def travel(self,goal):
        for origin,warp in topology.map_route(self.maps,game.location(self.f.state()),goal):
            self.assertEqual(game.location(self.f.state()),origin);self.cross(warp)
        self.assertEqual(game.location(self.f.state()),goal)
    def capture(self,before,species,fought,hidden):
        where=game.location(before);n=before[game.PARTY_COUNT];prior=[game.party_slot(before,i) for i in range(n)]
        balls=self.qty(before,1);self.assertGreater(balls,0);self.throw_first_ball()
        for _ in range(90):
            st=self.f.state()
            if not in_battle(st) and main_callback2(st)==main_callback2(self.fixture):break
            self.f.pulse('B',90)
        self.f.run(120);caught=self.f.state();self.assertFalse(in_battle(caught));self.assertEqual(caught[offset(BATTLE_OUTCOME)],7)
        self.assertEqual(game.location(caught),where);self.assertEqual(caught[game.PARTY_COUNT],n+1)
        for i,data in enumerate(prior):self.assertEqual(game.party_slot(caught,i),data)
        mon=game.party_slot(caught,n);facts=mon_facts(mon);self.assertTrue(facts['valid']);self.assertEqual(facts['species'],species)
        self.assertEqual(mon[:4],before[offset(0x0203A734):offset(0x0203A734)+4]);self.assert_ball_metadata(mon,1)
        self.assertEqual(self.qty(caught,1),balls-1)
        self.caught[species]=(n,mon[:8],facts);self.events[species]=(fought,hidden)
        for flag in (fought,hidden):self.assertEqual(self.flag(caught,flag),1)
        # Only normal flash, loaded into a fresh core of the same exact release.
        flash=save_game(self.f);self.switch(self.rom);loaded=load_game(self.f,flash)
        for i in range(n+1):self.assertEqual(game.party_slot(loaded,i),game.party_slot(caught,i))
        self.assertEqual(game.location(loaded),where);self.check_caught()
        local=2 if species==386 else 1
        self.assertFalse(any(o[:3]==(local,where[1],where[0]) for o in active_objects(loaded)))
        self.shot(f'{self.case}_CAPTURA_{species}.png')
        self.record('capture',species=species,level=facts['level'],map=list(where),party_count=n+1,save_continue=True,personality=mon[:4].hex())
    def check_caught(self):
        st=self.f.state()
        for species,(slot,identity,expected) in self.caught.items():
            data=game.party_slot(st,slot);facts=mon_facts(data);self.assertTrue(facts['valid']);self.assertEqual(data[:8],identity)
            for key in ('species','level','iv','ev'):self.assertEqual(facts[key],expected[key])
            self.assert_ball_metadata(data,1)
            for flag in self.events[species]:self.assertEqual(self.flag(st,flag),1)
        self.assertEqual(st[game.PARTY_COUNT],1+len(self.caught));self.assert_pair(st)
    def return_home(self,harbor):
        self.travel(harbor);self.walk((8,5));self.f.run(8,'DOWN');self.f.run(25);self.f.pulse('A',300)
        self.menu(61);self.shot(f'{self.case}_MENU_RETORNO.png')
        self.f.pulse('B',90);self.assertIsNone(menu_id(self.f.state()));before=self.xy();self.move_one('UP');self.assertNotEqual(self.xy(),before)
        self.walk((8,5));self.f.run(8,'DOWN');self.f.run(25);self.f.pulse('A',300);self.menu(61)
        self.sail(0,(3,5));self.check_caught()
        self.assertEqual(self.qty(self.f.state(),1),0)
        before=self.xy();self.move_one('UP');self.assertNotEqual(self.xy(),before);self.f.run(3600)
        self.assertEqual(game.location(self.f.state()),(3,5));self.assertEqual(main_callback2(self.f.state()),main_callback2(self.fixture))
        data=[game.party_slot(self.f.state(),i) for i in range(1+len(self.caught))]
        flash=save_game(self.f);self.switch(self.rom);loaded=load_game(self.f,flash)
        self.assertEqual(game.location(loaded),(3,5));self.check_caught()
        for i,mon in enumerate(data):self.assertEqual(game.party_slot(loaded,i),mon)
        self.shot(f'{self.case}_VERMILION_CONTINUAR.png')
        self.record('complete',manual_steps=self.walks,warp_transitions=self.warps,boat_trips=self.boats,island_maps=sorted([list(x) for x in self.visited if x[0]==2]),captured=sorted(self.caught),returned_and_saved=True)
    def test_navel_roundtrip_hooh_and_lugia(self):
        self.begin(1,2);self.travel((2,37));self.walk((9,13));self.move_one('UP',allow_battle=True)
        before=self.wait_battle(250,70);self.capture(before,250,0x2F3,0x9C)
        self.travel((2,38));self.walk((10,16));self.f.run(8,'UP');self.f.run(25);self.f.pulse('A',120)
        before=self.wait_battle(249,70);self.capture(before,249,0x2F2,0x9B)
        self.return_home((2,59));self.assertEqual(self.warps,42);self.assertEqual(self.boats,2)
        self.assertEqual(len([x for x in self.visited if x[0]==2]),22)
    def test_birth_roundtrip_full_puzzle_and_deoxys(self):
        self.begin(2,1);self.travel((2,56));self.walk((15,13))
        rocks=((15,12),(11,14),(15,8),(19,14),(12,11),(18,11),(15,14),(11,14),(19,14),(15,15),(15,10))
        stands=((15,13),(12,14),(15,9),(18,14),(13,11),(17,11),(15,13),(12,14),(18,14),(15,14),(15,11))
        caps=(None,4,8,8,8,4,4,4,6,3,3);begin_steps=self.walks
        self.assertEqual(self.var(self.f.state(),0x403E),0)
        for i,((rx,ry),(x,y)) in enumerate(zip(rocks,stands)):
            rock=next(o for o in active_objects(self.f.state()) if o[:3]==(1,56,2));self.assertEqual(rock[4],(rx+7,ry+7))
            cx,cy=self.xy()
            for _ in range(abs(x-cx)):self.move_one('RIGHT' if x>cx else 'LEFT')
            for _ in range(abs(y-cy)):self.move_one('DOWN' if y>cy else 'UP')
            self.assertEqual(self.xy(),(x,y));face='RIGHT' if rx>x else 'LEFT' if rx<x else 'DOWN' if ry>y else 'UP'
            self.f.run(8,face);self.f.run(25);steps=self.var(self.f.state(),0x4026)
            if i:self.assertEqual(steps,caps[i])
            else:self.assertGreater(steps,0) # Real walk from harbor, not the old synthetic-room fixture.
            self.f.pulse('A',180)
            if i<10:self.assertEqual(self.var(self.f.state(),0x403E),i+1)
            self.record('puzzle',interaction=i+1,native_step_counter=steps)
        self.assertEqual(self.walks-begin_steps,52)
        before=self.wait_battle(386,30);self.capture(before,386,0x2E4,0x99)
        self.return_home((2,58));self.assertEqual(self.warps,2);self.assertEqual(self.boats,2)
