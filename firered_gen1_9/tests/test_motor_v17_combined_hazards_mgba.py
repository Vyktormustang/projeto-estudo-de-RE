"""Ordem moderna de hazards na v17, fixtures novas e SHA exato."""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v16_doubles_endings_mgba as ending
from battle_fixture_helpers import main_callback2

from scripts import motor_v17 as patch
old,h=ending.old,ending.h
doubles=ending.doubles
ROM=os.environ.get('MOTOR_V17_ROM')
CORE=os.environ.get('MGBA_CORE')


def entry_events(slot,hp,layers,rock_first):
    spikes=400//(8,6,4)[layers-1]
    order=(100,spikes) if rock_first else (spikes,100)
    events=[]
    for damage in order:
        if hp==0:break
        after=max(0,hp-damage);events.append((1,slot,hp,after));hp=after
    return events


def messages_for(hp,layers,rock_first):
    spikes=400//(8,6,4)[layers-1]
    order=(('rock',100),('spikes',spikes)) if rock_first else (('spikes',spikes),('rock',100))
    labels=[]
    for label,damage in order:
        if hp<=0:break
        labels.append(label);hp=max(0,hp-damage)
    return labels


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V17_ROM e MGBA_CORE')
class MotorV17CombinedHazardsTests(unittest.TestCase):
    _enter_wild_encounter=classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_doubles_fixture=classmethod(old.MotorV10MGBATests._make_doubles_fixture.__func__)
    moves=ending.MotorV16DoublesEndingsTests.moves
    begin=ending.MotorV16DoublesEndingsTests.begin
    advance=ending.MotorV16DoublesEndingsTests.advance
    pulse=ending.MotorV16DoublesEndingsTests.pulse
    settle=ending.MotorV16DoublesEndingsTests.settle
    turn=ending.MotorV16DoublesEndingsTests.turn
    consistent=ending.MotorV16DoublesEndingsTests.consistent
    check_pp=ending.MotorV16DoublesEndingsTests.check_pp
    identities_and_exp=ending.MotorV16DoublesEndingsTests.identities_and_exp

    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM)
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise ValueError('ROM não é v17 exato')
        cls.temp=tempfile.TemporaryDirectory()
        cls.f=old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture=old.route_entry_fixture(cls.f)
        cls.doubles_fixture=cls._make_doubles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise AssertionError('ROM alterada')

    def scenario(self,bench_hp,actor=0):
        st=bytearray(ending.MotorV16DoublesEndingsTests.scenario(self,191,actor,(bench_hp,400)))
        self.moves(st,old.PARTY,actor//2,(191,445,157,150),(20,20,20,20),old.bank_off(actor))
        self.cursor=0
        return bytes(st)

    def action(self,st,actor,slot):
        directions=[]
        if (self.cursor&1)!=(slot&1):directions.append('RIGHT' if slot&1 else 'LEFT')
        if (self.cursor>>1)!=(slot>>1):directions.append('DOWN' if slot>>1 else 'UP')
        out=self.turn(st,[(tuple(directions),None) if bank==actor else ((),None) for bank in (0,2)])
        self.cursor=slot
        self.consistent(out)
        return out

    def plant(self,st,layers,rock_first,actor=0,caps=False):
        sequence=([1] if rock_first else [])+[0]*layers+([] if rock_first else [1])
        if caps:sequence += [0,1]  # quarta camada e segundo Stealth Rock
        spikes=rock=0
        for slot in sequence:
            before=st;st=self.action(st,actor,slot)
            spikes=min(3,spikes+1) if slot==0 else spikes
            rock=1 if slot==1 else rock
            self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+12+10],spikes)
            self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+13],rock)
            self.assertEqual(self.losses,[]);self.assertEqual(self.transitions,[])
            self.check_pp(before,st,[(bank,slot if bank==actor else 1 if bank%2 else 0) for bank in range(4)])
            self.identities_and_exp(before,st)
            self.assertEqual(old.u16(st,h.LAST_MOVES+2*actor),191 if slot==0 else 445)
        return st

    def hazard_messages(self):
        out=[]
        for text in self.seen:
            if text=='Inimigo A sofre\ncom os ESPINHOS!':out.append('spikes')
            elif text.startswith('Pedras pontiagudas feriram'):out.append('rock')
        return out

    def verify(self,layers,rock_first,bench_hp,actor=0,caps=False):
        initial=self.scenario(bench_hp,actor)
        before=self.plant(initial,layers,rock_first,actor,caps)
        out=self.action(before,actor,2)
        events=[event for event in self.losses if event[0]==1]
        observed_messages=self.hazard_messages()
        self.assertCountEqual(events[:2],[(1,0,1,0),(1,1,1,0)])
        modern=entry_events(2,bench_hp,layers,rock_first)+entry_events(3,400,layers,rock_first)
        modern_messages=messages_for(bench_hp,layers,rock_first)+messages_for(400,layers,rock_first)
        self.assertEqual(events[2:],modern)
        self.assertEqual(observed_messages,modern_messages,self.seen)
        ko=bench_hp<=400//(8,6,4)[layers-1]+100
        self.assertEqual(self.transitions,[(1,0,2),(1,2,3)] if ko else [(1,0,2),(3,1,3)])
        self.assertEqual(out[ending.ABSENT],8 if ko else 0)
        self.assertEqual(ending.hp(out,1,2),entry_events(2,bench_hp,layers,rock_first)[-1][3])
        self.assertEqual(ending.hp(out,1,3),400-400//(8,6,4)[layers-1]-100)
        self.check_pp(before,out,[(actor,2),(actor^2,0)])
        self.identities_and_exp(initial,out,207 if ko else 138)
        for bank in (1,3):
            if not out[ending.ABSENT]&(1<<bank):self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),0)
        self.assertEqual(list(out[old.offset(0x0203FC94):old.offset(0x0203FC98)]),
                         [2,1,0,0] if rock_first else [1,2,0,0])
        self.assertEqual(out[old.offset(old.SIDE_TIMERS_ADDR)+22],layers)
        self.assertEqual(out[old.offset(old.V8_STATE_ADDR)+13],1)
        absent_history=old.u16(out,h.LAST_MOVES+6)
        before_next=out
        out=self.action(out,actor,3)
        self.assertEqual(self.transitions,[]);self.assertEqual(self.losses,[])
        uses=[(actor,3),(actor^2,0)]+[(bank,1) for bank in (1,3) if not out[ending.ABSENT]&(1<<bank)]
        self.check_pp(before_next,out,uses)
        self.identities_and_exp(initial,out,207 if ko else 138)
        if ko:self.assertEqual(old.u16(out,h.LAST_MOVES+6),absent_history)
        self.assertEqual(out[ending.ABSENT],8 if ko else 0)
        self.assertEqual(out[old.offset(old.SIDE_TIMERS_ADDR)+22],layers)
        self.assertEqual(out[old.offset(old.V8_STATE_ADDR)+13],1)
        self.assertEqual(main_callback2(out),main_callback2(initial))
        return events,observed_messages,modern,modern_messages

    def test_spikes_primeiro_camadas_e_ko_no_primeiro_ou_segundo_hazard(self):
        for layers in (1,2,3):
            damage=400//(8,6,4)[layers-1]
            for bench_hp in (400,damage,damage+100):
                with self.subTest(layers=layers,bench_hp=bench_hp):self.verify(layers,False,bench_hp)

    def test_stealth_rock_primeiro_camadas_e_ko(self):
        for layers in (1,2,3):
            damage=400//(8,6,4)[layers-1]
            for bench_hp in (400,100,damage+100):
                with self.subTest(layers=layers,bench_hp=bench_hp):self.verify(layers,True,bench_hp)

    def test_quarta_camada_e_sr_repetido_nao_aumentam_dano(self):
        self.verify(3,False,400,actor=2,caps=True)

    def test_ordem_inversa_persiste_apos_tentativas_repetidas(self):
        self.verify(3,True,400,actor=2,caps=True)
