"""Histórico/PP após pivôs e phazing reais sobre v15, sem alterar a ROM.

Inclui uma caracterização NEGATIVA: falha legada de phazing por nível.
Seu sucesso não significa conformidade moderna; veja o relatório da auditoria.
"""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v10_mgba as old
import test_eerie_history_mgba as h
from scripts import motor_v15 as patch
from battle_fixture_helpers import set_level10_starter_test_stats

ROM = os.environ.get('MOTOR_V15_ROM')
CORE = os.environ.get('MGBA_CORE')
INDEX = old.offset(old.PARTY_INDEXES_ADDR)


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V15_ROM e MGBA_CORE')
class MotorV15SwitchHistoryTests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state
    finish_turn = h.EerieHistoryMGBATests.finish_turn
    switch_to_other = h.EerieHistoryMGBATests.switch_to_other

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise ValueError('ROM não é v15 exato')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture = old.route_entry_fixture(cls.f)
        a = bytearray(old.seed_mon(cls.fixture,1,10,(150,369,720,33)))
        b = bytearray(old.seed_mon(cls.fixture,4,10,(33,369,150,45)))
        for st in (a,b): set_level10_starter_test_stats(st,stat=200)
        pos = old.offset(old.PARTY)
        a[pos+100:pos+200] = b[pos:pos+100]
        a[old.offset(old.PLAYER_PARTY_COUNT)] = 2
        cls.battle_fixture = cls._enter_wild_encounter(a)
        cls.trainer_fixture = cls._enter_wild_encounter(a,two_foes=True)

    @classmethod
    def tearDownClass(cls):
        cls.f.close(); cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada')

    def moves(self,st,party,slot,moves,pps,bank=None):
        h.set_moves(st,party,slot,moves,pps)
        if bank is not None:
            for i,move in enumerate(moves):
                old.put16(st,bank+12+2*i,move);st[bank+0x25+i]=pps[i]

    def scenario(self,move,fast=True,forced=False):
        st = bytearray(self._duel_state(150,move2_id=move,foe_move=720,
            p_speed=600 if fast else 40,p_hp=3000,p_max=3000,p_atk=30,p_spa=30,
            f_hp=3000,f_max=3000,f_atk=30,f_spa=30,f_speed=400,
            base_state=self.trainer_fixture if forced else self.battle_fixture))
        self.moves(st,old.PARTY,0,(150,move,720,33),(20,20,20,20),old.PLAYER_BATTLE)
        self.moves(st,old.PARTY,1,(33,move,150,45),(13,12,11,10))
        self.moves(st,old.ENEMY_PARTY_ADDR,0,(720,150,45,39),(20,0,0,0),old.FOE_BATTLE)
        if forced:
            # O entrante também conhece Eerie: histórico antigo seria detectável.
            self.moves(st,old.ENEMY_PARTY_ADDR,1,(150,720,45,39),(20,12,0,0))
        for party,count in ((old.PARTY,2),(old.ENEMY_PARTY_ADDR,2 if forced else 1)):
            for slot in range(count):
                pos = old.offset(party)+100*slot
                old.put16(st,pos+86,3000);old.put16(st,pos+88,3000)
                for field,value in ((90,30),(92,200),(94,600 if party==old.PARTY else 40),(96,30),(98,200)):
                    old.put16(st,pos+field,value)
                old.put32(st,pos+80,0)
            bank=old.PLAYER_BATTLE if party==old.PARTY else old.FOE_BATTLE
            for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98)):
                old.put16(st,old.offset(party)+po,old.u16(st,bank+bo))
        st[old.FOE_BATTLE+0x1E]=12  # Isolar histórico de misses nos golpes com 90% de acurácia.
        self.assertEqual(old.u16(st,h.LAST_MOVES),0)
        self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
        return bytes(st)

    def consistent(self,st):
        for bank,party in ((0,old.PARTY),(1,old.ENEMY_PARTY_ADDR)):
            idx=old.u16(st,INDEX+2*bank);b=old.bank_off(bank)
            self.assertEqual(list(st[b+0x25:b+0x29]),h.party_pp(st,party,idx))
            self.assertEqual(old.u16(st,b+0x2A),old.u16(st,old.offset(party)+100*idx+86))
        self.assertEqual(old.u32(st,old.offset(0x0202160C))&0x800,0)

    def turn(self,st,direction=None,pivot=False):
        self.f.restore(st)
        self.f.pulse('A',25)
        if direction:
            for button in ((direction,) if isinstance(direction,str) else direction):
                self.f.pulse(button,15)
        self.f.run(6,'A');self.f.run(1100)
        if pivot:
            self.f.pulse('DOWN',30)
            self.f.pulse('A',35);self.f.pulse('A',35)
            self.f.run(1100)
        out=self.finish_turn()
        self.consistent(out)
        return out

    def test_pivots_limpam_historico_sem_drenar_pp_do_entrante(self):
        for move in (369,517,708,571):
            for fast in (True,False):
                with self.subTest(move=move,fast=fast):
                    st=self.turn(self.scenario(move,fast))
                    self.assertEqual(old.u16(st,h.LAST_MOVES),150)
                    self.assertEqual(h.party_pp(st,old.PARTY,0),[16 if fast else 19,20,20,20])
                    st=self.turn(st,'RIGHT',pivot=True)
                    self.assertEqual(old.u16(st,INDEX),1)
                    self.assertEqual(old.u16(st,h.LAST_MOVES),0)
                    self.assertEqual(h.party_pp(st,old.PARTY,0),[16,19,20,20])
                    self.assertEqual(h.party_pp(st,old.PARTY,1),[13,12,11,10])
                    if fast:self.assertLess(old.u16(st,old.PLAYER_BATTLE+0x2A),3000)
                    else:self.assertEqual(old.u16(st,old.PLAYER_BATTLE+0x2A),3000)
                    st=self.turn(st)
                    self.assertEqual(old.u16(st,h.LAST_MOVES),33)
                    self.assertEqual(h.party_pp(st,old.PARTY,1),[9,12,11,10])
                    st=self.switch_to_other(st,0)
                    self.consistent(st)
                    self.assertEqual(old.u16(st,h.LAST_MOVES),0)
                    self.assertEqual(h.party_pp(st,old.PARTY,0),[16,19,20,20])
                    self.assertEqual(h.party_pp(st,old.PARTY,1),[9,12,11,10])

    def test_phazing_limpa_historico_inimigo(self):
        for move in (46,18,521,508):
            with self.subTest(move=move):
                st=self.turn(self.scenario(move,forced=True))
                self.assertEqual(old.u16(st,h.LAST_MOVES+2),720)
                st=self.turn(st,'RIGHT')
                self.assertEqual(old.u16(st,INDEX+2),1)
                self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[18,0,0,0])
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[20,12,0,0])
                # Slot 1 -> slot 2 (Eerie Spell), pela interface.
                st=self.turn(st,('LEFT','DOWN'))
                self.assertEqual(old.u16(st,h.LAST_MOVES),720)
                self.assertLess(old.u16(st,old.FOE_BATTLE+0x2A),3000)
                # A IA pode escolher Splash ou Eerie, mas só seu PP próprio.
                pps=h.party_pp(st,old.ENEMY_PARTY_ADDR,1)
                self.assertIn(pps,([19,12,0,0],[20,11,0,0]))
                last=old.u16(st,h.LAST_MOVES+2)
                self.assertIn(last,(150,720))
                self.assertEqual(h.party_pp(st,old.PARTY,0)[2],16 if last==720 else 19)
                st=self.turn(st)
                self.assertEqual(old.u16(st,h.LAST_MOVES),720)
                used=old.u16(st,h.LAST_MOVES+2)
                self.assertIn(used,(150,720))
                expected=pps[:]
                expected[(150,720).index(last)]-=3
                expected[(150,720).index(used)]-=1
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),expected)
                st=self.turn(st,('UP','RIGHT'))
                self.assertEqual(old.u16(st,INDEX+2),0)
                self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[18,0,0,0])
                st=self.turn(st,('LEFT','DOWN'))
                self.assertEqual(old.u16(st,h.LAST_MOVES),720)
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[17,0,0,0])

    def test_suction_cups_impede_phazing_sem_apagar_historico(self):
        for move in (46,18,521,508):
            with self.subTest(move=move):
                st=bytearray(self.scenario(move,forced=True))
                st[old.FOE_BATTLE+0x20]=21  # Suction Cups como condição inicial.
                st=self.turn(bytes(st))
                self.assertEqual(old.u16(st,h.LAST_MOVES+2),720)
                st=self.turn(st,'RIGHT')
                self.assertEqual(old.u16(st,INDEX+2),0)
                self.assertEqual(old.u16(st,h.LAST_MOVES+2),720)
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[18,0,0,0])
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[20,12,0,0])
                st=self.turn(st,('LEFT','DOWN'))
                self.assertEqual(old.u16(st,h.LAST_MOVES),720)
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[14,0,0,0])

    def enemy_phazer_state(self,move,equal_level=False):
        st=bytearray(self.scenario(move,forced=True))
        if equal_level:
            # Controle positivo com atacante nível 10 e EXP coerente, para
            # isolar o histórico do defeito de nível caracterizado abaixo.
            seeded=bytearray(old.seed_mon(self.fixture,4,10,(move,150,45,39)))
            set_level10_starter_test_stats(seeded,stat=200)
            start=old.offset(old.PARTY);dest=old.offset(old.ENEMY_PARTY_ADDR)
            st[dest:dest+100]=seeded[start:start+100]
            old.put16(st,old.FOE_BATTLE,4)
            st[old.FOE_BATTLE+0x2C]=10
            old.put16(st,dest+86,3000);old.put16(st,dest+88,3000)
            for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98)):
                old.put16(st,dest+po,old.u16(st,old.FOE_BATTLE+bo))
        self.moves(st,old.ENEMY_PARTY_ADDR,0,(move,150,45,39),(20,0,0,0),old.FOE_BATTLE)
        return bytes(st)

    def test_phazing_do_jogador_tambem_limpa_historico_na_ida_e_volta(self):
        for move in (46,18,521,508):
            with self.subTest(move=move):
                st=self.enemy_phazer_state(move,equal_level=True)
                self.assertEqual(st[old.FOE_BATTLE+0x2C],10)
                st=self.turn(st)
                self.assertEqual(old.u16(st,INDEX),1)
                self.assertEqual(old.u16(st,h.LAST_MOVES),0)
                self.assertEqual(h.party_pp(st,old.PARTY,0),[19,20,20,20])
                self.assertEqual(h.party_pp(st,old.PARTY,1),[13,12,11,10])
                st=self.turn(st)
                self.assertEqual(old.u16(st,INDEX),0)
                self.assertEqual(old.u16(st,h.LAST_MOVES),0)
                self.assertEqual(h.party_pp(st,old.PARTY,0),[19,20,20,20])
                self.assertEqual(h.party_pp(st,old.PARTY,1),[12,12,11,10])
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[18,0,0,0])

    def test_defeito_v15_phazing_com_dano_ainda_pode_falhar_por_nivel(self):
        # Caracterização negativa v15: NÃO é conformidade moderna. A chance
        # legada em TryDoForceSwitchOut permanece mesmo em batalha de treinador.
        for move,slots in ((521,(0,1,0)),(508,(1,1,0))):
            with self.subTest(move=move):
                st=self.enemy_phazer_state(move)
                self.assertLess(st[old.FOE_BATTLE+0x2C],st[old.PLAYER_BATTLE+0x2C])
                self.assertTrue(old.u32(st,old.offset(0x02020374))&8)
                self.assertEqual(st[old.PLAYER_BATTLE+0x20],4)
                for turn,expected_slot in enumerate(slots,1):
                    previous_slot=old.u16(st,INDEX)
                    before_hp=old.u16(st,old.PLAYER_BATTLE+0x2A)
                    st=self.turn(st)
                    self.assertEqual(old.u16(st,INDEX),expected_slot)
                    self.assertEqual(old.u16(st,h.LAST_MOVES+2),move)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[20-turn,0,0,0])
                    if expected_slot==previous_slot:
                        # Houve impacto: não se trata de miss. Reserva viva,
                        # histórico da ação permanece, troca não aconteceu.
                        self.assertLess(old.u16(st,old.PLAYER_BATTLE+0x2A),before_hp)
                        self.assertGreater(old.u16(st,old.offset(old.PARTY)+100*(1-previous_slot)+86),0)
                        self.assertEqual(old.u16(st,h.LAST_MOVES),150 if previous_slot==0 else 33)
                    else:
                        self.assertEqual(old.u16(st,h.LAST_MOVES),0)
