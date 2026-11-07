"""Duplas com reservas insuficientes, KO na reposição e fim de batalha v16."""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v16_doubles_hazards_ko_mgba as previous
from battle_fixture_helpers import main_callback2, in_battle

old,h,patch=previous.old,previous.h,previous.patch
doubles=previous.doubles
ROM=os.environ.get('MOTOR_V16_ROM')
CORE=os.environ.get('MGBA_CORE')
ABSENT=old.offset(0x020215AD)
OUTCOME=old.offset(0x020216C8)


def hp(st,side,slot):return previous.player.hp(st,side,slot)


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V16_ROM e MGBA_CORE')
class MotorV16DoublesEndingsTests(unittest.TestCase):
    _enter_wild_encounter=classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_doubles_fixture=classmethod(old.MotorV10MGBATests._make_doubles_fixture.__func__)
    moves=previous.MotorV16DoublesHazardsKOTests.moves
    pulse=previous.MotorV16DoublesHazardsKOTests.pulse
    turn=previous.MotorV16DoublesHazardsKOTests.turn
    check_pp=previous.MotorV16DoublesHazardsKOTests.check_pp

    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM)
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise ValueError('ROM não é v16 exato')
        cls.temp=tempfile.TemporaryDirectory()
        cls.f=old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture=old.route_entry_fixture(cls.f)
        cls.doubles_fixture=cls._make_doubles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise AssertionError('ROM alterada')

    def scenario(self,hazard,actor,bench):
        side=1-actor%2
        st=bytearray(previous.MotorV16DoublesHazardsKOTests.scenario(
            self,hazard,157,actor,False,two_faints=bool(actor%2)))
        for bank in (side,side+2):
            old.put16(st,old.bank_off(bank)+0x2A,1)
            old.put16(st,old.offset(doubles.party_for(side))+100*(bank//2)+86,1)
        for slot,value in zip((2,3),bench):
            pos=old.offset(doubles.party_for(side))+100*slot
            old.put16(st,pos+86,value);old.put16(st,pos+88,400)
        if side==1:
            # Três/quatro KOs cruzam o nível 11. HP plausível no jogador
            # evita overflow artificial ao recalcular atributos nativamente.
            for bank in (0,2):
                pos=old.offset(old.PARTY)+100*(bank//2)
                for off in (86,88):old.put16(st,pos+off,32)
                for off in (0x2A,0x2E):old.put16(st,old.bank_off(bank)+off,32)
        self.assertEqual(st[ABSENT],0)
        self.assertEqual(st[OUTCOME],0)
        self.assertEqual(doubles.eligible(st,side),{slot for slot,value in zip((2,3),bench) if value})
        return bytes(st)

    def begin(self,st):
        previous.MotorV16DoublesHazardsKOTests.begin(self,st)
        self.terminal_state=None;self.terminal_losses=None
        self.absent_changes=[];self.last_absent=st[ABSENT]

    def advance(self,frames,*buttons):
        for _ in range(frames):
            self.f.run(1,*buttons);st=self.f.state();text=h.text(st)
            if text and (not self.seen or self.seen[-1]!=text):self.seen.append(text)
            for bank,idx in enumerate(doubles.indexes(st)):
                if idx!=self.previous_indexes[bank]:
                    self.transitions.append((bank,self.previous_indexes[bank],idx));self.previous_indexes[bank]=idx
            if st[ABSENT]!=self.last_absent:
                self.absent_changes.append((self.last_absent,st[ABSENT]));self.last_absent=st[ABSENT]
            for side in (0,1):
                for slot in range(6):
                    pid=old.u32(st,old.offset(doubles.party_for(side))+100*slot);key=(side,pid)
                    if key not in self.health:continue
                    prev=self.health[key];now=hp(st,side,slot)
                    if now!=prev:
                        self.losses.append((side,self.identities[key],prev,now));self.health[key]=now
            if st[OUTCOME] and self.terminal_state is None:
                self.terminal_state=st;self.terminal_losses=list(self.losses)

    def settle(self,require_menu=True):
        for _ in range(128):
            st=self.f.state()
            if not require_menu and (st[OUTCOME] or main_callback2(st)!=self.battle_callback):
                self.advance(120);break
            if not require_menu and 'Usar o pr' in h.text(st):
                self.pulse('A',90)  # aceitar o próximo; nunca escolher fuga
            else:
                self.pulse('B',90)
            st=self.f.state()
            if main_callback2(st)==self.battle_callback and 'vai fazer?' in h.text(st):
                self.advance(120);break
        st=self.f.state()
        if require_menu:
            self.assertIn('vai fazer?',h.text(st),self.seen)
            self.assertEqual(main_callback2(st),self.battle_callback)
            self.assertTrue(in_battle(st));self.assertEqual(st[OUTCOME],0)
        return st

    def consistent(self,st):
        self.assertTrue(in_battle(st));self.assertEqual(st[OUTCOME],0)
        for bank,slot in enumerate(doubles.indexes(st)):
            if st[ABSENT]&(1<<bank):continue
            b=old.bank_off(bank);party=doubles.party_for(bank);pos=old.offset(party)+100*slot
            self.assertGreater(hp(st,bank%2,slot),0)
            self.assertEqual(old.u16(st,b+0x2A),hp(st,bank%2,slot))
            self.assertEqual(list(st[b+0x25:b+0x29]),h.party_pp(st,party,slot))
            self.assertEqual(old.u32(st,b+0x4C),old.u32(st,pos))
            self.assertEqual(old.u32(st,b+0x58),old.u32(st,pos+4))
            self.assertEqual(st[b+0x2C],st[pos+84])
        self.assertEqual(old.u32(st,old.offset(0x0202160C))&0x800,0)

    def plant(self,st,hazard,actor):
        out=previous.MotorV16DoublesHazardsKOTests.plant(self,st,hazard,actor)
        self.check_pp(st,out,[(bank,1 if bank%2 else 0) for bank in range(4)])
        return out

    def strike(self,st,actor):
        choices=[(('RIGHT',),None) if bank==actor else ((),None) for bank in (0,2)]
        return self.turn(st,choices,False)

    def finish(self,outcome):
        for _ in range(160):
            st=self.f.state()
            if st[OUTCOME]==outcome and not in_battle(st) and main_callback2(st)==main_callback2(self.fixture):
                self.advance(120)
                st=self.f.state()
                self.assertEqual(st[OUTCOME],outcome)
                self.assertFalse(in_battle(st))
                self.assertEqual(main_callback2(st),main_callback2(self.fixture))
                return st
            self.pulse('B',90)
        self.fail(('fim de batalha não observado',outcome,hex(main_callback2(self.f.state())),self.seen))

    def identities_and_exp(self,initial,out,exp_gain=0):
        for side in (0,1):
            for slot in range(6):
                pos=old.offset(doubles.party_for(side))+100*slot
                self.assertEqual(out[pos:pos+8],initial[pos:pos+8])
                gain=exp_gain if side==0 and slot<2 else 0
                self.assertEqual(previous.experience(out,side,slot),previous.experience(initial,side,slot)+gain)
                self.assertEqual(out[pos+84],11 if gain>=207 else initial[pos+84])
                h.party_pp(out,doubles.party_for(side),slot)  # valida checksum

    def bench_values(self,hazard,mode):
        damage=50 if hazard==191 else 100
        return {'one':(400,0),'chain':(damage,400),'empty':(0,0),
                'last_faints':(damage,0),'both_faint':(damage,damage)}[mode]

    def enemy_case(self,hazard,actor,mode):
        bench=self.bench_values(hazard,mode);damage=50 if hazard==191 else 100
        alive=mode in ('one','chain');n_faints=2+sum(0<value<=damage for value in bench)
        initial=self.scenario(hazard,actor,bench)
        before=self.plant(initial,hazard,actor)
        out=self.strike(before,actor)
        if not alive:out=self.finish(1)
        else:self.consistent(out)
        events=[event for event in (self.losses if alive else self.terminal_losses) if event[0]==1]
        expected=[(1,0,1,0),(1,1,1,0)]
        expected.extend((1,slot,value,max(0,value-damage)) for slot,value in zip((2,3),bench) if value)
        self.assertEqual(events,expected)
        expected_transitions=[];old_slot=0
        for slot,value in zip((2,3),bench):
            if value:expected_transitions.append((1,old_slot,slot));old_slot=slot
        self.assertEqual(self.transitions,expected_transitions)
        self.identities_and_exp(initial,out,69*n_faints)
        uses=[(actor,1)]+([(actor^2,0)] if alive else [])
        self.check_pp(before,out,uses)
        if alive:
            survivor=2 if mode=='one' else 3
            self.assertEqual(out[ABSENT],1<<3)
            self.assertEqual(doubles.indexes(out),(0,survivor,1,1))
            self.assertEqual(hp(out,1,survivor),400-damage)
            self.assertEqual(old.u16(out,h.LAST_MOVES+2),0)
            absent_pp=list(out[old.bank_off(3)+0x25:old.bank_off(3)+0x29])
            absent_history=old.u16(out,h.LAST_MOVES+6)
            before_next=out
            # Slot 1 -> slot 3: Splash do ator; parceiro já usa Splash.
            out=self.turn(out,[(('DOWN',),None) if bank==actor else ((),None) for bank in (0,2)])
            self.consistent(out)
            self.assertEqual(out[ABSENT],1<<3)
            self.assertEqual(self.transitions,[]);self.assertEqual(self.losses,[])
            self.check_pp(before_next,out,[(actor,3),(actor^2,0),(1,1)])
            self.assertEqual(list(out[old.bank_off(3)+0x25:old.bank_off(3)+0x29]),absent_pp)
            self.assertEqual(old.u16(out,h.LAST_MOVES+6),absent_history)
            self.assertEqual(old.u16(out,h.LAST_MOVES+2),150)
            self.identities_and_exp(initial,out,69*n_faints)
        else:
            self.assertIsNotNone(self.terminal_state)
            self.assertEqual(self.terminal_state[OUTCOME],1)
            for slot in range(4):self.assertEqual(hp(out,1,slot),0)
        for slot in (0,1):
            pos=old.offset(old.PARTY)+100*slot
            self.assertGreater(hp(out,0,slot),0)
            self.assertLessEqual(hp(out,0,slot),old.u16(out,pos+88))
        return out

    def player_case(self,hazard,actor,mode,wild=False):
        bench=self.bench_values(hazard,mode);damage=50 if hazard==191 else 100
        alive=mode in ('one','chain')
        initial=bytearray(self.scenario(hazard,actor,bench))
        if wild:
            old.put32(initial,old.offset(0x02020374),old.u32(initial,old.offset(0x02020374))&~8)
            self.assertEqual(old.u32(initial,old.offset(0x02020374)),5)
        initial=bytes(initial);before=self.plant(initial,hazard,actor)
        out=self.strike(before,actor)
        for slot,value in zip((2,3),bench):
            if not value:continue
            self.assertEqual(out[OUTCOME],0)
            self.assertNotEqual(main_callback2(out),self.battle_callback)
            self.assertTrue(in_battle(out))
            self.pulse('RIGHT')
            if slot==3:self.pulse('DOWN')
            self.pulse('A',35);self.pulse('A',35);self.advance(2000)
            out=self.settle(False)
        if alive:self.consistent(out)
        else:
            out=self.finish(2)
            self.assertIsNotNone(self.terminal_state)
            self.assertEqual(self.terminal_state[OUTCOME],2)
        terminal=out if alive else self.terminal_state
        expected=[(0,0,1,0),(0,1,1,0)]
        expected.extend((0,slot,value,max(0,value-damage)) for slot,value in zip((2,3),bench) if value)
        events=self.losses if alive else self.terminal_losses
        if wild:
            # Rock Slide pode começar em qualquer um dos dois alvos.
            # Exigir os dois KOs antes dos hazards, sem impor ordem entre eles.
            self.assertCountEqual(events[:2],expected[:2])
            self.assertEqual(events[2:],expected[2:])
        else:
            self.assertEqual(events,expected)
        changes=[];old_slot=0
        for slot,value in zip((2,3),bench):
            if value:changes.append((0,old_slot,slot));old_slot=slot
        self.assertEqual(self.transitions,changes)
        self.identities_and_exp(initial,terminal)
        self.check_pp(before,terminal,[(actor,0)]+([(actor^2,1)] if alive else []))
        if alive:
            survivor=2 if mode=='one' else 3
            self.assertEqual(out[ABSENT],1<<2)
            self.assertEqual(doubles.indexes(out),(survivor,0,1,1))
            self.assertEqual(hp(out,0,survivor),400-damage)
            self.assertEqual(old.u16(out,h.LAST_MOVES),0)
            before_next=out
            out=self.turn(out,[((),None)])  # somente o jogador do banco 0
            self.consistent(out)
            self.assertEqual(out[ABSENT],1<<2)
            self.assertEqual(self.transitions,[]);self.assertEqual(self.losses,[])
            self.check_pp(before_next,out,[(0,0),(actor,0),(actor^2,1)])
            self.assertEqual(old.u16(out,h.LAST_MOVES),182)
            self.assertEqual(old.u16(out,h.LAST_MOVES+4),old.u16(before_next,h.LAST_MOVES+4))
            self.assertEqual(out[old.bank_off(2)+0x25:old.bank_off(2)+0x29],before_next[old.bank_off(2)+0x25:old.bank_off(2)+0x29])
            self.identities_and_exp(initial,out)
        else:
            for slot in range(4):self.assertEqual(hp(terminal,0,slot),0)
            # A cura depois da derrota é separada do instante do KO.
            # PP curado vem da tabela da própria ROM, não dos PP artificiais.
            from scripts import complemento_gen9
            rom=self.rom.read_bytes()
            for slot in range(5):
                pos=old.offset(old.PARTY)+100*slot
                self.assertEqual(hp(out,0,slot),old.u16(out,pos+88))
                block,order,valid=old.decrypted(out[pos:pos+100]);self.assertTrue(valid)
                self.assertEqual(block[order[0]*12+8],0)  # sem PP Ups
                moves=[old.u16(block,order[1]*12+2*i) for i in range(4)]
                self.assertEqual(h.party_pp(out,old.PARTY,slot),[rom[complemento_gen9.MOVE+12*move+4] for move in moves])
            self.identities_and_exp(initial,out)
            if wild:
                self.assertTrue(any('apagou!' in text for text in self.seen),self.seen)
                self.assertFalse(any('escapar' in text for text in self.seen),self.seen)
        return out

    def test_inimigo_com_uma_reserva_ou_ko_seguido_de_sobrevivente(self):
        for hazard in (191,445):
            for actor in (0,2):
                for mode in ('one','chain'):
                    with self.subTest(hazard=hazard,actor=actor,mode=mode):self.enemy_case(hazard,actor,mode)

    def test_vitoria_sem_reserva_ou_apos_kos_durante_reposicao(self):
        for hazard in (191,445):
            for actor in (0,2):
                for mode in ('empty','last_faints','both_faint'):
                    with self.subTest(hazard=hazard,actor=actor,mode=mode):self.enemy_case(hazard,actor,mode)

    def test_jogador_com_uma_reserva_ou_ko_seguido_de_sobrevivente(self):
        for hazard in (191,445):
            for actor in (1,3):
                for mode in ('one','chain'):
                    with self.subTest(hazard=hazard,actor=actor,mode=mode):self.player_case(hazard,actor,mode)

    def test_derrota_sem_reserva_ou_apos_kos_durante_reposicao(self):
        for hazard in (191,445):
            for actor in (1,3):
                for mode in ('empty','last_faints','both_faint'):
                    with self.subTest(hazard=hazard,actor=actor,mode=mode):self.player_case(hazard,actor,mode)

    def test_whiteout_em_dupla_selvagem_sem_escolher_fuga(self):
        for hazard in (191,445):
            for actor in (1,3):
                with self.subTest(hazard=hazard,actor=actor):self.player_case(hazard,actor,'last_faints',wild=True)
