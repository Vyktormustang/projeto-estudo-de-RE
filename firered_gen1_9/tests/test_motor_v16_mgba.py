"""v16: phazing de treinador, base negativa v15 e controles nativos preservados."""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v15_switch_history_mgba as history
from scripts import motor_v16 as patch
from battle_fixture_helpers import set_level10_starter_test_stats, in_battle

old, h, INDEX = history.old, history.h, history.INDEX
BASE = os.environ.get('MOTOR_V16_BASE')
ROM = os.environ.get('MOTOR_V16_ROM')
CORE = os.environ.get('MGBA_CORE')


def prepare(cls,rom,directory):
    cls.f = old.Emulator(Path(rom),Path(CORE),directory)
    cls.fixture = old.route_entry_fixture(cls.f)
    a = bytearray(old.seed_mon(cls.fixture,1,10,(150,369,720,33)))
    b = bytearray(old.seed_mon(cls.fixture,4,10,(33,369,150,45)))
    for st in (a,b): set_level10_starter_test_stats(st,stat=200)
    pos=old.offset(old.PARTY)
    a[pos+100:pos+200]=b[pos:pos+100]
    a[old.offset(old.PLAYER_PARTY_COUNT)]=2
    cls.battle_fixture=cls._enter_wild_encounter(a)
    cls.trainer_fixture=cls._enter_wild_encounter(a,two_foes=True)


class MotorV16MGBATests(history.MotorV15SwitchHistoryTests):
    __unittest_skip__ = not (BASE and ROM and CORE)
    __unittest_skip_why__ = 'defina MOTOR_V16_BASE, MOTOR_V16_ROM e MGBA_CORE'
    test_defeito_v15_phazing_com_dano_ainda_pode_falhar_por_nivel = None

    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM)
        if cls.rom.read_bytes()!=patch.build(Path(BASE).read_bytes()):
            raise ValueError('ROM v16 diverge da reconstrução')
        cls.temp=tempfile.TemporaryDirectory()
        prepare(cls,BASE,Path(cls.temp.name)/'base')
        try:
            test=cls()
            history.MotorV15SwitchHistoryTests.test_defeito_v15_phazing_com_dano_ainda_pode_falhar_por_nivel(test)
            cls.base_negative=True
            cls.wild_baseline={}
            for move in (46,18,521,508):
                for enemy in (False,True):
                    cls.wild_baseline[move,enemy]=test.wild_result(move,enemy)
        finally:cls.f.close()
        prepare(cls,ROM,Path(cls.temp.name)/'v16')

    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada')

    def turn(self,st,direction=None,pivot=False):
        # Nenhum nível temporário usado pelo wrapper pode sobreviver ao comando.
        levels={(party,slot):st[old.offset(party)+100*slot+84]
                for party in (old.PARTY,old.ENEMY_PARTY_ADDR) for slot in (0,1)}
        out=super().turn(st,direction,pivot)
        for (party,slot),level in levels.items():
            self.assertEqual(out[old.offset(party)+100*slot+84],level)
        for bank,party in ((0,old.PARTY),(1,old.ENEMY_PARTY_ADDR)):
            slot=old.u16(out,INDEX+2*bank)
            self.assertEqual(out[old.bank_off(bank)+0x2C],levels[party,slot])
        return out

    def test_defeito_reproduzido_somente_na_base_v15(self):
        self.assertTrue(self.base_negative)

    def test_nivel_inferior_troca_em_todos_os_turnos_de_treinador(self):
        for move in (46,18,521,508):
            with self.subTest(move=move):
                st=self.enemy_phazer_state(move)
                before=st[old.FOE_BATTLE+0x2C]
                self.assertLess(before,st[old.PLAYER_BATTLE+0x2C])
                for turn,slot in enumerate((1,0,1),1):
                    st=self.turn(st)
                    self.assertEqual(old.u16(st,INDEX),slot)
                    self.assertEqual(old.u16(st,h.LAST_MOVES),0)
                    self.assertEqual(st[old.FOE_BATTLE+0x2C],before)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[20-turn,0,0,0])
                self.assertEqual(h.party_pp(st,old.PARTY,0),[18,20,20,20])
                self.assertEqual(h.party_pp(st,old.PARTY,1),[12,12,11,10])

    def test_sem_reserva_viva_continua_falhando(self):
        for move in (46,18,521,508):
            with self.subTest(move=move):
                st=bytearray(self.enemy_phazer_state(move))
                old.put16(st,old.offset(old.PARTY)+100+86,0)
                st=self.turn(bytes(st))
                self.assertEqual(old.u16(st,INDEX),0)
                self.assertEqual(old.u16(st,h.LAST_MOVES),150)
                self.assertEqual(h.party_pp(st,old.PARTY,0),[19,20,20,20])
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[19,0,0,0])
                self.assertEqual(st[old.offset(0x020216C8)],0)

    def test_suction_cups_e_ingrain_preservados_contra_nivel_inferior(self):
        for move in (46,18,521,508):
            for rooted in (False,True):
                with self.subTest(move=move,rooted=rooted):
                    st=bytearray(self.enemy_phazer_state(move))
                    if rooted:
                        self.moves(st,old.PARTY,0,(275,move,720,33),(20,20,20,20),old.PLAYER_BATTLE)
                    else:st[old.PLAYER_BATTLE+0x20]=21
                    st=self.turn(bytes(st))
                    self.assertEqual(old.u16(st,INDEX),0)
                    self.assertEqual(old.u16(st,h.LAST_MOVES),275 if rooted else 150)
                    if rooted:self.assertTrue(old.u32(st,old.offset(old.STATUSES3_ADDR))&0x400)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[19,0,0,0])

    def test_protect_e_imunidade_bloqueiam_phazing_com_dano(self):
        for move,immune in ((521,18),(508,7)):
            for protect in (False,True):
                with self.subTest(move=move,protect=protect):
                    st=bytearray(self.enemy_phazer_state(move))
                    if protect:self.moves(st,old.PARTY,0,(182,move,720,33),(20,20,20,20),old.PLAYER_BATTLE)
                    else:st[old.PLAYER_BATTLE+0x22:old.PLAYER_BATTLE+0x24]=bytes([immune,immune])
                    st=self.turn(bytes(st))
                    self.assertEqual(old.u16(st,INDEX),0)
                    self.assertEqual(old.u16(st,old.PLAYER_BATTLE+0x2A),3000)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[19,0,0,0])

    def wild_result(self,move,enemy):
        st=bytearray(self.scenario(move))
        if enemy:self.moves(st,old.ENEMY_PARTY_ADDR,0,(move,150,45,39),(20,0,0,0),old.FOE_BATTLE)
        self.assertFalse(old.u32(st,old.offset(0x02020374))&8)
        self.f.restore(bytes(st));self.f.pulse('A',25)
        if not enemy:self.f.pulse('RIGHT',15)
        self.f.run(6,'A');self.f.run(1100)
        for _ in range(8):self.f.pulse('B',90)
        out=self.f.state()
        return (out[old.offset(0x020216C8)],in_battle(out),
                tuple(h.party_pp(out,old.PARTY,0)),tuple(h.party_pp(out,old.ENEMY_PARTY_ADDR,0)),
                old.u16(out,INDEX),old.u16(out,INDEX+2),
                old.u16(out,old.offset(old.PARTY)+86),old.u16(out,old.offset(old.ENEMY_PARTY_ADDR)+86))

    def test_encontros_selvagens_preservam_resultado_da_base(self):
        for key,expected in self.wild_baseline.items():
            with self.subTest(move=key[0],enemy=key[1]):
                actual=self.wild_result(*key)
                self.assertEqual(actual,expected)
                if not key[1]:self.assertFalse(actual[1],'Phazing do jogador deve encerrar encontro selvagem')
