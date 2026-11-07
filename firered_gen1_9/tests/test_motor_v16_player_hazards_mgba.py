"""Entrada/KO por hazards no jogador, em singles e duplas; fixtures sintéticas."""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v16_hazards_ko_mgba as singles
import test_motor_v16_doubles_phazing_mgba as doubles
from battle_fixture_helpers import in_battle, main_callback2

v16=singles.v16
old,h,INDEX,patch=singles.old,singles.h,singles.INDEX,singles.patch
ROM=os.environ.get('MOTOR_V16_ROM')
CORE=os.environ.get('MGBA_CORE')


def hp(st,side,slot):
    return old.u16(st,old.offset(doubles.party_for(side))+100*slot+86)


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V16_ROM e MGBA_CORE')
class MotorV16PlayerHazardsTests(unittest.TestCase):
    _enter_wild_encounter=classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_doubles_fixture=classmethod(old.MotorV10MGBATests._make_doubles_fixture.__func__)
    _duel_state=old.MotorV10MGBATests._duel_state
    moves=v16.history.MotorV15SwitchHistoryTests.moves

    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM)
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise ValueError('ROM não é v16 exato')
        cls.temp=tempfile.TemporaryDirectory()
        v16.prepare(cls,ROM,Path(cls.temp.name))
        cls.doubles_fixture=cls._make_doubles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise AssertionError('ROM alterada')

    def scenario(self,hazard,phazer,double=False,actor=1,ko=False):
        if double:
            st=bytearray(doubles.MotorV16DoublesPhazingTests.scenario(self,actor,hazard,'mixed'))
            bench=2
            # A seleção inicial da IA usa slot 1; esgotado o único PP do
            # hazard, só o phazer no slot 0 está disponível nos turnos seguintes.
            self.moves(st,old.ENEMY_PARTY_ADDR,actor//2,(phazer,hazard,45,39),(20,1,0,0),old.bank_off(actor))
        else:
            st=bytearray(singles.MotorV16HazardsKOTests.scenario(self,hazard,phazer))
            bench=1
            for slot in (0,1):
                src=old.offset(old.ENEMY_PARTY_ADDR)+100*slot
                dst=old.offset(old.PARTY)+100*slot
                st[dst:dst+100]=st[src:src+100]
                self.moves(st,old.PARTY,slot,(150,33,45,39),(20+slot,0,0,0),old.PLAYER_BATTLE if slot==0 else None)
            b=old.PLAYER_BATTLE;p=old.offset(old.PARTY)
            block,order,valid=old.decrypted(st[p:p+100]);self.assertTrue(valid)
            old.put16(st,b,4);st[b+0x2C]=10
            for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98),(0x2A,86),(0x2E,88)):
                old.put16(st,b+bo,old.u16(st,p+po))
            old.put32(st,b+0x48,560);old.put32(st,b+0x4C,old.u32(st,p));old.put32(st,b+0x58,old.u32(st,p+4))
            old.put32(st,b+0x14,old.u32(block,order[3]*12+4))
            self.moves(st,old.ENEMY_PARTY_ADDR,0,(hazard,phazer,45,39),(1,20,0,0),old.FOE_BATTLE)
        p=old.offset(old.PARTY)+100*bench
        old.put16(st,p+88,400)
        old.put16(st,p+86,(50 if hazard==191 else 100) if ko else 400)
        for b in (0,2) if double else (0,):
            # Garantir que Splash acontece antes do phazing (prioridade -6).
            st[old.bank_off(b)+0x20]=4
        self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+12],0)
        self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+10],0)
        if not double:
            # PID único por membro: a UI de equipe reordena temporariamente
            # os registros. HP deve ser observado por identidade, não posição.
            for side in (0,1):
                for slot in (0,1):
                    pos=old.offset(doubles.party_for(side))+100*slot
                    data=bytearray(st[pos:pos+100]);block,order,valid=old.decrypted(data)
                    self.assertTrue(valid)
                    pid=old.u32(data,0)%24+24*(100+side*6+slot)
                    old.put32(data,0,pid);key=pid^old.u32(data,4)
                    for off in range(0,48,4):old.put32(data,32+off,old.u32(block,off)^key)
                    st[pos:pos+100]=data
                    if slot==0:old.put32(st,old.bank_off(side)+0x4C,pid)
        return bytes(st)

    def begin(self,st):
        self.f.restore(st)
        self.seen=[];self.transitions=[];self.losses=[]
        self.previous_indexes=list(doubles.indexes(st))
        self.battle_callback=main_callback2(st)
        self.identities={}
        self.health={}
        for side in (0,1):
            for slot in range(6):
                pos=old.offset(doubles.party_for(side))+100*slot
                pid=old.u32(st,pos)
                if not pid:continue
                key=(side,pid)
                self.assertNotIn(key,self.identities)
                self.identities[key]=slot;self.health[key]=hp(st,side,slot)

    def advance(self,frames,*buttons):
        for _ in range(frames):
            self.f.run(1,*buttons);st=self.f.state();text=h.text(st)
            if text and (not self.seen or self.seen[-1]!=text):self.seen.append(text)
            for bank,idx in enumerate(doubles.indexes(st)):
                if idx!=self.previous_indexes[bank]:
                    self.transitions.append((bank,self.previous_indexes[bank],idx));self.previous_indexes[bank]=idx
            for side in (0,1):
                for slot in range(6):
                    pid=old.u32(st,old.offset(doubles.party_for(side))+100*slot)
                    key=(side,pid)
                    if key not in self.health:continue
                    prev=self.health[key];now=hp(st,side,slot)
                    if now!=prev:
                        self.losses.append((side,self.identities[key],prev,now));self.health[key]=now

    def pulse(self,button,gap=25):
        self.advance(3,button);self.advance(gap)

    def settle(self,require_menu=True):
        for _ in range(64):
            self.pulse('B',90)
            if not require_menu and main_callback2(self.f.state())!=self.battle_callback:
                self.advance(120);break
            if 'vai fazer?' in h.text(self.f.state()):
                self.advance(120);break
        out=self.f.state()
        if require_menu:self.assertIn('vai fazer?',h.text(out),self.seen)
        return out

    def turn(self,st,double=False,require_menu=True):
        self.begin(st)
        for _ in range(2 if double else 1):
            self.pulse('A');self.pulse('A')
        self.advance(1800)
        return self.settle(require_menu)

    def consistent(self,st,double=False):
        for bank in range(4 if double else 2):
            idx=old.u16(st,INDEX+2*bank);b=old.bank_off(bank)
            party=doubles.party_for(bank);pos=old.offset(party)+100*idx
            self.assertEqual(list(st[b+0x25:b+0x29]),h.party_pp(st,party,idx))
            self.assertEqual(old.u16(st,b+0x2A),hp(st,bank%2,idx))
            self.assertEqual(old.u32(st,b+0x4C),old.u32(st,pos))
        self.assertTrue(in_battle(st));self.assertEqual(st[old.offset(0x020216C8)],0)
        self.assertEqual(old.u32(st,old.offset(0x0202160C))&0x800,0)
        if double:
            self.assertNotEqual(doubles.indexes(st)[0],doubles.indexes(st)[2])
            self.assertNotEqual(doubles.indexes(st)[1],doubles.indexes(st)[3])

    def plant(self,st,hazard,double=False,actor=1):
        out=self.turn(st,double);self.consistent(out,double)
        self.assertEqual(self.transitions,[]);self.assertEqual(self.losses,[])
        self.assertEqual(out[old.offset(old.V8_STATE_ADDR)+12],int(hazard==445))
        self.assertEqual(out[old.offset(old.SIDE_TIMERS_ADDR)+10],int(hazard==191))
        self.assertEqual(h.party_pp(out,old.ENEMY_PARTY_ADDR,actor//2),[20,0,0,0] if double else [0,20,0,0])
        return out

    def verify_pp(self,before,out,double,actor):
        for side in (0,1):
            for slot in range(6):
                expected=h.party_pp(before,doubles.party_for(side),slot)
                active=slot<(2 if double else 1)
                if active:
                    move_slot=(0 if double else 1) if side and slot==actor//2 else (1 if double and side else 0)
                    expected[move_slot]-=1
                self.assertEqual(h.party_pp(out,doubles.party_for(side),slot),expected,(side,slot))

    def verify_entry(self,hazard,phazer,double=False,actor=1,ko=False):
        bench=2 if double else 1;damage=50 if hazard==191 else 100
        initial=self.scenario(hazard,phazer,double,actor,ko)
        st=self.plant(initial,hazard,double,actor)
        before=st;callback=main_callback2(st)
        st=self.turn(st,double,not ko)
        self.assertEqual(len(self.transitions),1)
        victim,previous,next_slot=self.transitions[0]
        self.assertIn(victim,(0,2) if double else (0,))
        self.assertEqual(next_slot,bench)
        if ko:
            # Não confundir a ordenação visual temporária com HP perdido.
            self.assertNotEqual(main_callback2(st),callback)
            self.assertTrue(any('desmaiou' in text for text in self.seen),self.seen)
            self.assertIn((0,bench,damage,0),self.losses)
            # Cursor começa na primeira posição da tela. O membro retirado
            # pelo phazing está à direita (duplas) / abaixo (singles).
            self.pulse('RIGHT' if double else 'DOWN')
            self.pulse('A',35);self.pulse('A',35);self.advance(1800)
            st=self.settle()
            self.assertEqual(self.transitions,[(victim,previous,bench),(victim,bench,previous)])
            self.assertEqual(hp(st,0,bench),0)
            self.assertEqual(self.losses[-1][0:2],(0,previous))
            self.assertEqual(self.losses[-1][2]-self.losses[-1][3],damage*10)
        else:
            self.assertEqual(hp(st,0,bench),400-damage)
            self.assertEqual(self.losses[-1],(0,bench,400,400-damage))
        self.assertEqual(main_callback2(st),callback)
        self.consistent(st,double);self.verify_pp(before,st,double,actor)
        self.assertEqual(old.u16(st,h.LAST_MOVES+2*victim),0)
        for bank in range(4 if double else 2):
            if bank!=victim:self.assertEqual(old.u16(st,h.LAST_MOVES+2*bank),phazer if bank==actor else 150)
        for side in (0,1):
            for slot in range(6):
                pos=old.offset(doubles.party_for(side))+100*slot
                a,oa,va=old.decrypted(before[pos:pos+100]);b,ob,vb=old.decrypted(st[pos:pos+100])
                self.assertTrue(va and vb)
                self.assertEqual(st[pos:pos+8],before[pos:pos+8])
                self.assertEqual(st[pos+84],before[pos+84])
                self.assertEqual(old.u32(a,oa[0]*12+4),old.u32(b,ob[0]*12+4))
        if double:
            ally=victim^2
            self.assertEqual(doubles.indexes(st)[ally],doubles.indexes(before)[ally])
            self.assertEqual(hp(st,0,doubles.indexes(st)[ally]),4000)
        if ko:
            # Com o único reserva elegível desmaiado, jogar mais um turno
            # deve continuar a batalha sem nova troca ou PP do membro morto.
            before_next=st
            st=self.turn(st,double)
            self.consistent(st,double);self.verify_pp(before_next,st,double,actor)
            self.assertEqual(self.transitions,[])
            self.assertEqual(doubles.indexes(st),doubles.indexes(before_next))
            self.assertEqual(hp(st,0,bench),0)
            for bank in range(4 if double else 2):
                self.assertEqual(old.u16(st,h.LAST_MOVES+2*bank),phazer if bank==actor else 150)
        return st,victim

    def test_singles_entrada_sobre_hazards_sem_ko(self):
        for hazard in (191,445):
            for phazer in doubles.MOVES:
                with self.subTest(hazard=hazard,phazer=phazer):self.verify_entry(hazard,phazer)

    def test_singles_ko_selecao_e_hazard_no_substituto(self):
        for hazard in (191,445):
            for phazer in doubles.MOVES:
                with self.subTest(hazard=hazard,phazer=phazer):self.verify_entry(hazard,phazer,ko=True)

    def test_duplas_entrada_preserva_aliado(self):
        for hazard in (191,445):
            for actor in (1,3):
                for phazer in doubles.MOVES:
                    with self.subTest(hazard=hazard,actor=actor,phazer=phazer):
                        self.verify_entry(hazard,phazer,True,actor)

    def test_duplas_ko_selecao_preserva_aliado(self):
        for hazard in (191,445):
            for actor in (1,3):
                for phazer in doubles.MOVES:
                    with self.subTest(hazard=hazard,actor=actor,phazer=phazer):
                        self.verify_entry(hazard,phazer,True,actor,True)

    def test_duplas_selecao_rejeita_aliado_ativo_e_reserva_desmaiado(self):
        from test_motor_v7_mgba import GBA_DECODE
        encode={v:k for k,v in GBA_DECODE.items()}
        covered=set()
        for hazard in (191,445):
            for actor in (1,3):
                with self.subTest(hazard=hazard,actor=actor):
                    initial=self.scenario(hazard,46,True,actor,True)
                    before=self.plant(initial,hazard,True,actor)
                    callback=main_callback2(before)
                    menu=self.turn(before,True,False)
                    self.assertEqual(len(self.transitions),1)
                    victim,previous,bench=self.transitions[0]
                    self.assertIn(victim,(0,2));self.assertEqual(previous,victim//2)
                    self.assertEqual(bench,2);covered.add(victim)
                    self.assertNotEqual(main_callback2(menu),callback)
                    self.assertEqual(self.losses,[(0,2,50 if hazard==191 else 100,0)])
                    menu_callback=main_callback2(menu)
                    ally_keys=('DOWN',) if victim==0 else ()
                    dead_keys=('UP','RIGHT','DOWN') if victim==0 else ('RIGHT','DOWN')
                    for directions,message in ((ally_keys,'em batalha!'),(dead_keys,'para batalhar!')):
                        for key in directions:self.pulse(key)
                        self.pulse('A',35);self.pulse('A',35);self.advance(120)
                        out=self.f.state()
                        self.assertEqual(main_callback2(out),menu_callback)
                        self.assertEqual(doubles.indexes(out),doubles.indexes(menu))
                        # Mensagem efetivamente produzida pela UI; não basta
                        # continuar no menu para afirmar que houve rejeição.
                        needle=bytes(encode[c] for c in message)
                        self.assertNotIn(needle,menu[old.offset(0x02000000):old.offset(0x02040000)])
                        self.assertIn(needle,out[old.offset(0x02000000):old.offset(0x02040000)])
                        for side in (0,1):
                            pos=old.offset(doubles.party_for(side))
                            self.assertEqual(out[pos:pos+600],menu[pos:pos+600])
                        self.pulse('B',35)
                    self.pulse('UP');self.pulse('A',35);self.pulse('A',35);self.advance(1800)
                    out=self.settle()
                    self.assertEqual(main_callback2(out),callback)
                    self.assertEqual(self.transitions,[(victim,previous,2),(victim,2,previous)])
                    damage=500 if hazard==191 else 1000
                    self.assertEqual(self.losses,[(0,2,damage//10,0),(0,previous,4000,4000-damage)])
                    self.consistent(out,True);self.verify_pp(before,out,True,actor)
                    self.assertEqual(old.u16(out,h.LAST_MOVES+2*victim),0)
                    self.assertEqual(hp(out,0,1-previous),4000)
                    self.assertEqual(hp(out,0,2),0)
        self.assertEqual(covered,{0,2})
