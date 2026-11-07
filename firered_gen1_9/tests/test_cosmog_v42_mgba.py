"""WIP: read-only Cosmog audit; see docs/PROGRESSO_COSMOG_V42.md.

The current expanded suite still needs a consolidated native run.
Synthetic saves only; no claim of egg hatching or simultaneous final forms.
"""
import json,os,tempfile,unittest
from pathlib import Path
from scripts import motor_v42 as p
from mgba_treino_harness import Emulator,offset,mon_facts
from test_eventos_fixos_mgba import route_entry_fixture,active_objects,enemy
from test_estojo_expandido_mgba import add
from test_golpes_gen9_integracao import save_game,load_game
from battle_fixture_helpers import in_battle,main_callback2,BATTLE_OUTCOME
import test_ilhas_v41_mgba as islands
import test_motor_v42_mgba as tickets
import test_motor_v21_gameplay_mgba as game
ROM=os.environ.get('COSMOG_V42_ROM');CORE=os.environ.get('MGBA_CORE')

@unittest.skipUnless(ROM and CORE,'set COSMOG_V42_ROM and MGBA_CORE')
class CosmogNativeTests(unittest.TestCase):
    call=islands.IslandNativeTests.call
    switch=islands.IslandNativeTests.switch
    bootstrap=islands.IslandNativeTests.bootstrap
    setvar=islands.IslandNativeTests.setvar
    setflag=islands.IslandNativeTests.setflag
    flag=islands.IslandNativeTests.flag
    var=islands.IslandNativeTests.var
    tasks=islands.IslandNativeTests.tasks
    shot=islands.IslandNativeTests.shot
    qty=tickets.MotorV42NativeTests.qty
    throw_first_ball=game.MotorV21GameplayTests.throw_first_ball
    assert_ball_metadata=game.MotorV21GameplayTests.assert_ball_metadata
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM);cls.source=cls.rom.read_bytes()
        if p.digest(cls.source)!=p.OUTPUT_SHA256:raise ValueError('Not exact v42')
        cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name);cls.f=Emulator(cls.rom,Path(CORE),cls.dir)
        cls.fixture=route_entry_fixture(cls.f);cls.cache={};cls.observations=[]
    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if cls.rom.read_bytes()!=cls.source:raise AssertionError('ROM changed')
        if os.environ.get('COSMOG_V42_OBSERVATIONS'):
            with Path(os.environ['COSMOG_V42_OBSERVATIONS']).open('x') as f:json.dump(cls.observations,f,indent=2);f.write('\n')
    def test_capture_persistence_and_full_evolution_branches(self):
        st=self.bootstrap(1,81,12,13);st=add(self.f,st,1,2);st=add(self.f,st,68,40);self.f.restore(bytes(st))
        self.assertTrue(any(o[:3]==(11,81,1) for o in active_objects(st)))
        self.f.run(8,'UP');self.f.run(30);self.f.pulse('A',450)
        for _ in range(180):
            if in_battle(self.f.state()):break
            self.f.pulse('A',60)
        self.assertTrue(in_battle(self.f.state()));self.f.run(300)
        for _ in range(6):self.f.pulse('B',45)
        before=self.f.state();facts=enemy(before);print('ENEMY',facts,flush=True);self.assertEqual(facts['species'],789);self.shot('COSMOG_ENCONTRO.png')
        self.throw_first_ball()
        for _ in range(90):
            st=self.f.state()
            if not in_battle(st) and main_callback2(st)==main_callback2(self.fixture):break
            self.f.pulse('B',90)
        self.f.run(120);caught=self.f.state();self.assertEqual(caught[offset(BATTLE_OUTCOME)],7)
        self.assertEqual(caught[game.PARTY_COUNT],2);mon=game.party_slot(caught,1);self.assertEqual(mon[:4],before[offset(0x0203A734):offset(0x0203A734)+4]);self.assert_ball_metadata(mon,1)
        self.assertEqual(mon_facts(mon)['level'],25);self.assertTrue(mon_facts(mon)['valid'])
        self.assertEqual(self.flag(caught,0x5315),1);self.assertFalse(any(o[:3]==(11,81,1) for o in active_objects(caught)))
        print('CAPTURE',mon_facts(mon),'flag',self.flag(caught,0x5315),'objects',active_objects(caught),flush=True)
        self.shot('COSMOG_CAPTURADO.png');flash=save_game(self.f);self.switch(self.rom);loaded=load_game(self.f,flash)
        self.assertEqual(game.party_slot(loaded,1),mon)
        print('RELOADED','flag',self.flag(loaded,0x5315),'objects',active_objects(loaded),flush=True)
        self.assertEqual(self.flag(loaded,0x5315),1);self.assertFalse(any(o[:3]==(11,81,1) for o in active_objects(loaded)))
        self.f.pulse('A',120);self.assertFalse(in_battle(self.f.state()));self.assertEqual(self.f.state()[game.PARTY_COUNT],2)
        self.observations.append(dict(kind='native_capture_save_continue_repeat_interaction',facts=mon_facts(mon),flag='5315',flag_value=1,object_absent=True,identity=mon[:8].hex()))
        self.shot('COSMOG_CONTINUAR.png')
        self.f.pulse('START',80);self.f.pulse('DOWN',35);self.f.pulse('A',120)
        self.bag_callback=main_callback2(self.f.state())
        self.field_callback=main_callback2(loaded)
        for level in range(26,53):self.candy(1,790 if level>=43 else 789)
        self.shot('COSMOEM_52.png')
        for _ in range(8):
            if main_callback2(self.f.state())==self.field_callback:break
            self.f.pulse('B',120)
        self.assertEqual(main_callback2(self.f.state()),self.field_callback)
        self.f.pulse('B',90);self.f.pulse('START',80);self.f.pulse('UP',35);self.f.pulse('B',80)
        flash52=save_game(self.f)
        self.switch(self.rom);loaded=load_game(self.f,flash52);self.assertEqual(mon_facts(game.party_slot(loaded,1))['level'],52)
        self.f.pulse('START',80);self.f.pulse('DOWN',35);self.f.pulse('A',120);self.bag_callback=main_callback2(self.f.state())
        self.candy(1,791);self.shot('SOLGALEO_53.png');self.save_evolved(791)
        self.switch(self.rom);load_game(self.f,flash52)
        self.f.pulse('START',80);self.f.pulse('DOWN',35);self.f.pulse('A',120);self.bag_callback=main_callback2(self.f.state())
        self.candy(1,790,cancel=True);self.shot('COSMOEM_53_CANCELADO.png')
        self.candy(1,792);self.shot('LUNALA_54.png');self.save_evolved(792)

    def candy(self,slot,want,cancel=False):
        old=self.f.state();prior=game.party_slot(old,slot);facts=mon_facts(prior);quantity=self.qty(old,68)
        if not hasattr(self,'party_callback'):
            self.f.pulse('A',90);self.f.pulse('A',120);self.party_callback=main_callback2(self.f.state())
        else:
            for _ in range(5):
                if main_callback2(self.f.state())==self.party_callback:break
                self.f.pulse('A',120)
            self.assertEqual(main_callback2(self.f.state()),self.party_callback)
        party_callback=self.party_callback
        for _ in range(8):
            if self.f.state()[offset(0x0203A6DD)]==slot:break
            self.f.pulse('DOWN',35)
        self.assertEqual(self.f.state()[offset(0x0203A6DD)],slot)
        self.f.pulse('A',120);saw_scene=False;callbacks=set();outside=0
        for _ in range(150):
            st=self.f.state();cb=main_callback2(st);callbacks.add(cb)
            if cb==self.bag_callback:break
            if cb!=party_callback:
                saw_scene=True;outside+=1
                if outside==4 and facts['level'] in (42,52,53):self.shot(f'EVOLUCAO_{facts["species"]}_{facts["level"]+1}_{int(cancel)}.png')
                if cancel:self.f.run(60,'B');self.f.run(1)
                else:self.f.pulse('A',60)
            else:self.f.pulse('A',60)
        else:
            self.shot('CANDY_TIMEOUT.png');self.fail(('candy timeout',hex(cb),hex(self.bag_callback)))
        self.f.run(120);end=self.f.state();mon=game.party_slot(end,slot);out=mon_facts(mon)
        saw_scene=0x080A0609 in callbacks
        print('CANDY',facts['level'],'->',out['species'],out['level'],'scene',saw_scene,'cancel',cancel,'callbacks',sorted(hex(x) for x in callbacks),flush=True)
        self.assertEqual((out['species'],out['level'],out['valid']),(want,facts['level']+1,True))
        self.assertEqual(mon[:8],prior[:8]);self.assertEqual(self.qty(end,68),quantity-1)
        self.assertEqual(saw_scene,(want!=facts['species']) or cancel)
        self.observations.append(dict(kind='native_candy_evolution_flow',before=facts,after=out,cancel=cancel,evolution_callback_seen=saw_scene,callbacks=sorted(hex(x) for x in callbacks),identity=mon[:8].hex(),quantity_before=quantity,quantity_after=self.qty(end,68)))

    def save_evolved(self,species):
        prior=game.party_slot(self.f.state(),1)
        for _ in range(8):
            if main_callback2(self.f.state())==self.field_callback:break
            self.f.pulse('B',120)
        self.f.pulse('B',90);self.f.pulse('START',80);self.f.pulse('UP',35);self.f.pulse('B',80)
        flash=save_game(self.f);self.switch(self.rom);loaded=load_game(self.f,flash)
        self.assertEqual(game.party_slot(loaded,1),prior);self.assertEqual(mon_facts(prior)['species'],species)
        self.assertEqual(self.flag(loaded,0x5315),1)
        self.observations.append(dict(kind='native_final_evolution_save_continue',species=species,identity=prior[:8].hex(),independent_checkpoint_branch=True))

    def test_evolution_boundary_clock_and_everstone_contracts(self):
        from test_motor_v19_mgba import MotorV19ClockTests
        for minute in (600,1320):
            for species,cases in ((789,((42,0),(43,790),(44,790),(100,790))), (790,((52,0),(53,791),(54,792),(55,792),(100,792)))):
                for level,want in cases:
                    got=MotorV19ClockTests.evolution(self,species=species,level=level,minute=minute)
                    self.assertEqual(got,want)
                    self.observations.append(dict(kind='evolution_target_contract',species=species,level=level,minute=minute,item=0,target=got))
                level=43 if species==789 else 53
                got=MotorV19ClockTests.evolution(self,species=species,level=level,minute=minute,item=195)
                self.assertEqual(got,0)
                self.observations.append(dict(kind='evolution_target_contract',species=species,level=level,minute=minute,item=195,target=got))

    def test_native_daycare_contracts(self):
        """Synthetic parent records; direct native calls, NOT a deposit/hatch journey."""
        import struct
        from mgba_treino_harness import u32
        from test_estojo_expandido_mgba import save1
        from test_golpes_gen9_mgba import seed_mon
        self.assertEqual(struct.unpack_from('<I',self.source,0x7F578)[0],0x0869D0C8)
        self.assertEqual(struct.unpack_from('<I',self.source,0x7F5D4)[0],0x2FCC)
        for a,b,want in ((789,132,20),(132,789,20),(789,789,0),(132,132,0),(151,132,0),(1,132,20)):
            st=bytearray(self.fixture);dc=offset(save1(st)+0x2FCC);st[dc:dc+0x11C]=bytes(0x11C)
            for slot,species in enumerate((a,b)):
                seeded=seed_mon(self.fixture,species,25,(144,0,0,0))
                st[dc+slot*0x8C:dc+slot*0x8C+80]=game.party_slot(seeded,0)[:80]
            score=u32(self.call(st,0x0807F57C),0x20)
            self.assertEqual(score,want);print('DAYCARE_SCORE',a,b,score,flush=True)
            self.observations.append(dict(kind='daycare_compatibility_contract',parents=[a,b],same_ot=True,score=score))
            if (a,b)==(789,132):
                struct.pack_into('<H',st,dc+0x118,0x1234)
                out=self.call(st,0x0807F150)
                print('EGG_CONTRACT',out[game.PARTY_COUNT],mon_facts(game.party_slot(out,1)),flush=True)
                self.assertEqual(out[game.PARTY_COUNT],2)
                egg=game.party_slot(out,1);facts=mon_facts(egg)
                self.assertEqual((facts['species'],facts['valid']),(789,True))
                self.observations.append(dict(kind='daycare_give_egg_contract',facts=facts,availability_bypassed=True))

    def test_native_daycare_deposit_and_egg(self):
        from mgba_treino_harness import PARTY
        from test_golpes_gen9_mgba import seed_mon
        from test_estojo_expandido_mgba import save1
        st=self.setvar(self.bootstrap(35,0,2,4),0x4086,1);st=bytearray(st);start=offset(PARTY)
        for slot,species in ((1,789),(2,132)):
            seeded=seed_mon(st,species,25,(144,0,0,0))
            st[start+100*slot:start+100*(slot+1)]=game.party_slot(seeded,0)
        st[game.PARTY_COUNT]=3;self.f.restore(bytes(st))
        self.f.run(8,'UP');self.f.run(30);self.f.pulse('A',180)
        for number in range(2):
            for n in range(25):
                if main_callback2(self.f.state())==0x080F6225:break
                self.f.pulse('A',100)
            self.shot(f'DAYCARE_PARTY_{number}.png')
            self.assertEqual(main_callback2(self.f.state()),0x080F6225)
            for _ in range(8):
                if self.f.state()[offset(0x0203A6DD)]==1:break
                self.f.pulse('DOWN',35)
            self.assertEqual(self.f.state()[offset(0x0203A6DD)],1)
            for n in range(25):
                self.f.pulse('A',100)
                if self.f.state()[game.PARTY_COUNT]==2-number:break
            self.assertEqual(self.f.state()[game.PARTY_COUNT],2-number)
            print('DEPOSIT',number,flush=True)
        for _ in range(8):self.f.pulse('B',90)
        st=self.f.state();dc=offset(save1(st)+0x2FCC)
        parents=[mon_facts(st[dc+i*0x8C:dc+i*0x8C+80]+bytes(20)) for i in range(2)]
        self.assertEqual([x['species'] for x in parents],[789,132]);self.assertTrue(all(x['valid'] for x in parents))
        self.shot('DAYCARE_DEPOSITADOS.png');print('DEPOSITED',parents,game.coords(st),active_objects(st),hex(main_callback2(st)),self.tasks(st),flush=True)
        startxy=game.coords(st);steps=0
        for n in range(4096):
            self.move_one('RIGHT' if n%2==0 else 'LEFT');steps+=1
            expected=(startxy[0]+(1 if n%2==0 else 0),startxy[1])
            self.assertEqual(game.coords(self.f.state()),expected)
            if steps%256==0 and self.flag(self.f.state(),0x266):break
        self.assertEqual(self.flag(self.f.state(),0x266),1)
        print('NATIVE_EGG_PENDING_AFTER_STEPS',steps,flush=True)
        self.observations.append(dict(kind='native_daycare_deposit_and_egg_pending',synthetic_parents=[789,132],manual_steps=steps,flag='0266',value=1))
        self.walkto((4,7));self.f.run(8,'DOWN');self.f.run(240)
        self.assertEqual(game.location(self.f.state()),(3,15))
        self.walkto((16,15));self.f.run(8,'UP');self.f.run(30);self.f.pulse('A',180)
        for _ in range(30):
            if self.f.state()[game.PARTY_COUNT]==2:break
            self.f.pulse('A',100)
        self.shot('DAYCARE_OVO_RECEBIDO.png')
        self.assertEqual(self.f.state()[game.PARTY_COUNT],2)
        for _ in range(8):self.f.pulse('B',90)
        st=self.f.state();egg=game.party_slot(st,1);facts=mon_facts(egg)
        from mgba_treino_harness import decrypted,u32
        block,order,valid=decrypted(egg)
        self.assertTrue(valid);self.assertEqual(facts['species'],789)
        self.assertTrue(u32(block,order[3]*12+4)&(1<<30))
        self.assertEqual(self.flag(st,0x266),0)
        flash=save_game(self.f);self.switch(self.rom);loaded=load_game(self.f,flash)
        self.assertEqual(game.party_slot(loaded,1),egg)
        dc=offset(save1(loaded)+0x2FCC)
        parent=loaded[dc:dc+80]+bytes(20)
        self.assertEqual(mon_facts(parent)['species'],789);self.assertNotEqual(parent[:4],egg[:4])
        self.observations.append(dict(kind='native_daycare_egg_pickup_save_continue',egg=facts,egg_flag=True,parent_retained=True,distinct_personality=True,synthetic_parents=True,hatching_tested=False))
        print('NATIVE_EGG_PICKED_SAVED',facts,flush=True)

    def move_one(self,button):
        origin=game.coords(self.f.state())
        for _ in range(180):
            self.f.run(1,button)
            if game.coords(self.f.state())!=origin:break
        else:
            self.shot('DAYCARE_BLOCKED.png');self.fail(('blocked',origin,button,active_objects(self.f.state()),hex(main_callback2(self.f.state())),self.tasks(self.f.state())))
        self.f.run(20)

    def walkto(self,goal):
        from scripts import auditar_trajetos_v42 as topology
        st=self.f.state();g,m=game.location(st);mapdata=topology.read_map(self.source,g,m,'Day Care audit')
        xy=tuple(n-7 for n in game.coords(st))
        blocked={tuple(n-7 for n in o[4]) for o in active_objects(st) if o[0]!=255}
        route=topology.cell_route(mapdata,xy,goal,blocked)
        for button,want in route:
            self.move_one(button)
            if game.location(self.f.state())!=(g,m):break
            self.assertEqual(tuple(n-7 for n in game.coords(self.f.state())),want)
        self.f.run(240)
