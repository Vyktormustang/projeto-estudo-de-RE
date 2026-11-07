"""v14: comparação v13 e batalhas sintéticas completas, sem transferir estados."""
from __future__ import annotations
import os
import tempfile
import unittest
from pathlib import Path
import test_rollout_power_mgba as r
from scripts import motor_v14 as patch

old = r.old
h = r.history
BASE = os.environ.get('MOTOR_V14_BASE')
ROM = os.environ.get('MOTOR_V14_ROM')
CORE = os.environ.get('MGBA_CORE')
MARKER = old.offset(0x0202160C)


@unittest.skipUnless(BASE and ROM and CORE,'defina MOTOR_V14_BASE, MOTOR_V14_ROM e MGBA_CORE')
class MotorV14MGBATests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state
    scenario = r.RolloutPowerMGBATests.scenario
    assert_hit = r.RolloutPowerMGBATests.assert_hit
    assert_pp = r.RolloutPowerMGBATests.assert_pp
    prepare_curl = r.RolloutPowerMGBATests.prepare_curl
    sequence = r.RolloutPowerMGBATests.sequence

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        if cls.rom.read_bytes() != patch.build(Path(BASE).read_bytes()):
            raise ValueError('ROM v14 diverge da reconstrução')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(Path(BASE),Path(CORE),Path(cls.temp.name)/'base')
        try:
            cls.fixture = old.route_entry_fixture(cls.f)
            cls.battle_fixture = cls._make_singles_fixture()
            case = cls()
            cls.baseline = {}
            for move in (205,301):
                for curl in (False,True):
                    st = case.scenario(move,curl=curl)
                    if curl:
                        st = case.prepare_curl(st)
                    for _ in range(2):
                        st,_ = case.turn(st)
                    st,_ = case.turn(st,direction='RIGHT')
                    cls.baseline[move,curl] = h.party_pp(st,old.ENEMY_PARTY_ADDR,0)
        finally:
            cls.f.close()
        cls.f = old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name)/'v14')
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada')

    def turn(self,st,**kwargs):
        before = sum(h.party_pp(st,old.PARTY,0))
        out,events = r.RolloutPowerMGBATests.turn(self,st,**kwargs)
        self.assertEqual(old.u32(out,MARKER)&0x800,0,'Isenção de PP vazou ao menu')
        self.assertEqual(sum(h.party_pp(out,old.PARTY,0)),before-1,'PP próprio do outro banco')
        return out,events

    def replace_player_move(self,st,slot,move):
        st = bytearray(st)
        moves = [old.u16(st,old.PLAYER_BATTLE+12+2*i) for i in range(4)]
        pps = list(st[old.PLAYER_BATTLE+0x25:old.PLAYER_BATTLE+0x29])
        moves[slot] = move
        h.set_moves(st,old.PARTY,0,moves,pps)
        old.put16(st,old.PLAYER_BATTLE+12+2*slot,move)
        return bytes(st)

    def test_defeito_reproduzido_no_v13_com_fixtures_proprias(self):
        for move in (205,301):
            self.assertEqual(self.baseline[move,False],[2,0,0,0])
            self.assertEqual(self.baseline[move,True],[0,2,0,0])

    def test_protect_detect_na_continuacao_preservam_pp_e_reinicio_gasta(self):
        for move in (205,301):
            for curl in (False,True):
                for protect in (182,197):
                    with self.subTest(move=move,curl=curl,protect=protect):
                        st = self.replace_player_move(self.scenario(move,curl=curl),1,protect)
                        if curl:
                            st = self.prepare_curl(st)
                        for power in (30,60):
                            st,events = self.turn(st)
                            self.assert_hit(st,events,move,power*(2 if curl else 1))
                        st,events = self.turn(st,direction='RIGHT')
                        self.assertEqual(events,[])
                        self.assertEqual(old.u16(st,h.LAST_MOVES),protect)
                        self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
                        self.assertEqual(bool(old.u32(st,old.FOE_BATTLE+0x54)&r.DEFENSE_CURL),curl)
                        expected = [0]*4; slot = int(curl); expected[slot] = 3
                        self.assert_pp(st,expected)
                        st,events = self.turn(st,direction='LEFT')
                        self.assert_hit(st,events,move,60 if curl else 30)
                        expected[slot] = 2
                        self.assert_pp(st,expected)

    def test_primeiro_uso_protegido_ainda_gasta_pp(self):
        for move in (205,301):
            for protect in (182,197):
                with self.subTest(move=move,protect=protect):
                    st = self.replace_player_move(self.scenario(move),1,protect)
                    st,events = self.turn(st,direction='RIGHT')
                    self.assertEqual(events,[])
                    self.assert_pp(st,[3,0,0,0])
                    self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
                    st,events = self.turn(st,direction='LEFT')
                    self.assert_hit(st,events,move,30)
                    self.assert_pp(st,[2,0,0,0])

    def test_pressure_so_cobra_no_inicio_e_reinicio(self):
        for move in (205,301):
            with self.subTest(move=move):
                st = bytearray(self.scenario(move))
                st[old.PLAYER_BATTLE+0x20] = 46  # Pressure, em vez de Battle Armor
                st = bytes(st)
                for _ in range(2):
                    st,_ = self.turn(st)
                    self.assert_pp(st,[2,0,0,0])
                st,events = self.turn(st,direction='RIGHT')
                self.assertEqual(events,[])
                self.assert_pp(st,[2,0,0,0])
                st,_ = self.turn(st,direction='LEFT')
                self.assert_pp(st,[0,0,0,0])

    test_rollout_progressao_e_reinicio_sem_dreno = r.RolloutPowerMGBATests.test_rollout_progressao_e_reinicio_sem_dreno
    test_rollout_progressao_com_pp_zero_e_struggle = r.RolloutPowerMGBATests.test_rollout_progressao_com_pp_zero_e_struggle
    test_defense_curl_dobra_rollout_ate_960_e_preserva_bonus_no_reinicio = r.RolloutPowerMGBATests.test_defense_curl_dobra_rollout_ate_960_e_preserva_bonus_no_reinicio
    test_defense_curl_e_rollout_com_pp_zero = r.RolloutPowerMGBATests.test_defense_curl_e_rollout_com_pp_zero
    test_ice_ball_compartilha_progressao_e_reinicio = r.RolloutPowerMGBATests.test_ice_ball_compartilha_progressao_e_reinicio
    test_ice_ball_com_defense_curl_e_pp_zero = r.RolloutPowerMGBATests.test_ice_ball_com_defense_curl_e_pp_zero
    test_protect_com_pp_zero_encerra_trava_sem_underflow = r.RolloutPowerMGBATests.test_protect_com_pp_zero_encerra_trava_sem_underflow

    def test_sono_na_continuacao_desvia_sem_armar_isencao_de_pp(self):
        st = bytearray(self.replace_player_move(self.scenario(),1,95))  # Hypnosis
        old.put16(st,old.PLAYER_BATTLE+6,600)
        old.put16(st,old.offset(old.PARTY)+94,600)
        st,events = self.turn(bytes(st))
        self.assert_hit(st,events,205,30)
        st,events = self.turn(st,direction='RIGHT')
        self.assertEqual(events,[])
        self.assertTrue(old.u32(st,old.FOE_BATTLE+0x50)&7)
        self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
        self.assert_pp(st,[3,0,0,0])
        st,_ = self.turn(st,direction='LEFT')
        self.assertEqual(old.u32(st,MARKER)&0x800,0)

    def test_miss_natural_por_sand_attack_reinicia_sem_pp_extra(self):
        for move in (205,301):
            with self.subTest(move=move):
                st = bytearray(self.replace_player_move(self.scenario(move),0,28))
                st[old.FOE_BATTLE+0x1E] = 6  # acurácia neutra, reduzida naturalmente
                st[old.FOE_BATTLE+0x25] = 20
                h.set_moves(st,old.ENEMY_PARTY_ADDR,0,(move,150,45,39),(20,0,0,0))
                st = bytes(st)
                interrupted = False
                for _ in range(12):
                    was_locked = bool(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
                    before = h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0]
                    st,events = self.turn(st)
                    after = h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0]
                    self.assertEqual(after,before-(0 if was_locked else 1))
                    if interrupted and events:
                        self.assert_hit(st,events,move,30)
                        break
                    if was_locked and not events:
                        self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
                        interrupted = True
                else:
                    self.fail('Miss durante trava e novo impacto não observados no limite')

    def test_usuario_banco0_e_tackle_seguinte_nao_herda_isencao(self):
        for move in (205,301):
            with self.subTest(move=move):
                st = bytearray(self._duel_state(move,foe_move=150,
                    p_hp=4000,p_max=4000,f_hp=10000,f_max=10000,p_atk=300,f_def=100))
                for bank,party,moves,pps in (
                    (old.PLAYER_BATTLE,old.PARTY,(move,33,45,39),(4,4,0,0)),
                    (old.FOE_BATTLE,old.ENEMY_PARTY_ADDR,(150,182,45,39),(1,20,0,0)),
                ):
                    h.set_moves(st,party,0,moves,pps)
                    for i,mid in enumerate(moves):
                        old.put16(st,bank+12+2*i,mid)
                        st[bank+0x25+i] = pps[i]
                self.f.restore(bytes(st))
                self.f.pulse('A',25); self.f.run(6,'A')
                # Com o jogador travado, os turnos continuam automaticamente.
                # O inimigo gasta seu único Splash, depois só tem Protect.
                for frame in range(9000):
                    self.f.run(1,*(['B'] if frame%93<3 else []))
                    st = self.f.state()
                    if old.u16(st,h.LAST_MOVES+2)==182 and 'vai fazer?' in h.text(st):
                        break
                else:
                    self.fail('Interrupção natural do jogador não observada')
                self.assertEqual(h.party_pp(st,old.PARTY,0),[3,4,0,0])
                self.assertEqual(list(st[old.PLAYER_BATTLE+0x25:old.PLAYER_BATTLE+0x29]),[3,4,0,0])
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[0,19,0,0])
                self.assertLess(old.u16(st,old.FOE_BATTLE+0x2A),10000)
                self.assertFalse(old.u32(st,old.PLAYER_BATTLE+0x54)&h.MULTIPLETURNS)
                self.assertEqual(old.u32(st,MARKER)&0x800,0)
                # Texto do menu aparece antes de aceitar entrada: aguardar a
                # conclusão da transição, sem escrever callbacks/registradores.
                self.f.run(120)
                _,seen = old.MotorV10MGBATests._run_turn(self,self.f.state(),slot=1)
                for _ in range(8): self.f.pulse('B',90)
                st = self.f.state()
                self.assertTrue(any('usou\nTACKLE!' in s for s in seen),seen)
                self.assertIn('vai fazer?',h.text(st))
                self.assertEqual(h.party_pp(st,old.PARTY,0),[3,3,0,0])
                self.assertEqual(old.u32(st,MARKER)&0x800,0)
