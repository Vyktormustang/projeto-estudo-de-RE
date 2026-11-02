"""Potência de Rollout/Ice Ball no v13 exato, observada em batalha sintética.

ROLLOUT_POWER_ROM=/caminho/motor_v13.gba MGBA_CORE=/caminho/mgba_libretro.so
Não modifica ROM/saves. Defense Curl e travas são criados pelo fluxo de batalha.
"""
from __future__ import annotations

import os
import struct
import tempfile
import unittest
from pathlib import Path

import test_motor_v10_mgba as old
import test_eerie_history_mgba as history
from scripts import motor_v13 as patch

ROM = os.environ.get('ROLLOUT_POWER_ROM')
CORE = os.environ.get('MGBA_CORE')
MOVE_POWER = old.offset(0x02021864)
CURRENT_MOVE = old.offset(0x02021586)
DEFENSE_CURL = 0x40000000


def neutral_damage_values(level, attack, defense, power):
    """Oráculo restrito: fórmula física FR, neutro, sem STAB/crítico/modificadores.

    Usa divisões inteiras nativas e os 16 fatores 85..100. Não é oráculo geral
    de dano moderno e não exige que o dano dobre literalmente entre turnos.
    """
    if not all(isinstance(x,int) and x > 0 for x in (level,attack,defense,power)):
        raise ValueError('Atributos e potência positivos obrigatórios')
    base = max(1,attack*power*(2*level//5+2)//defense//50)+2
    return {max(1,base*r//100) for r in range(85,101)}


class RolloutDamageOracleTests(unittest.TestCase):
    def test_faixas_e_arredondamento_em_dano_baixo(self):
        self.assertEqual(neutral_damage_values(10,300,100,30),{10,11,12})
        for power in (30,60,120):
            self.assertEqual(neutral_damage_values(3,100,500,power),{2,3})
        self.assertEqual(neutral_damage_values(3,100,500,240),{3,4})
        self.assertEqual(neutral_damage_values(3,100,500,480),{5,6,7})

    def test_oraculo_recusa_atributos_invalidos(self):
        for args in ((0,300,100,30),(3,300,0,30),(3,-1,100,30),(3,300,100,0)):
            with self.assertRaises(ValueError):
                neutral_damage_values(*args)


@unittest.skipUnless(ROM and CORE,'defina ROLLOUT_POWER_ROM e MGBA_CORE')
class RolloutPowerMGBATests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        data = cls.rom.read_bytes()
        if patch.digest(data) != patch.OUTPUT_SHA256:
            raise ValueError('ROM não é motor_v13 exato')
        # Tabela expandida de golpes: mesma potência e mesmo efeito nativo.
        rollout = data[0x1000000+205*12:0x1000000+206*12]
        iceball = data[0x1000000+301*12:0x1000000+302*12]
        if rollout[:2] != iceball[:2] or rollout[:2] != bytes((117,30)):
            raise ValueError('Contrato de dados Rollout/Ice Ball divergente')
        if struct.unpack_from('<I',data,0x100A000+117*4)[0] != 0x08186348:
            raise ValueError('Script nativo Rollout divergente')
        # attackcanceler; attackstring; teste de trava; ppreduce.
        if data[0x186348:0x186355] != bytes.fromhex('00 02 1d 01 00 10 00 00 55 63 18 08 03'):
            raise ValueError('Ordem dos comandos Rollout divergente')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada durante os testes')

    def scenario(self,move=205,*,drain=False,curl=False):
        st = bytearray(self._duel_state(720 if drain else 150,foe_move=move,
            p_def=100,p_speed=40,p_hp=4000,p_max=4000,
            f_hp=10000,f_max=10000,f_atk=300,f_speed=400))
        # Tipos normais para neutralidade e ausência de STAB. Battle Armor no
        # defensor impede críticos; acurácia alta evita erro neste cenário.
        self.assertEqual(tuple(st[old.PLAYER_BATTLE+0x22:old.PLAYER_BATTLE+0x24]),(0,0))
        self.assertEqual(tuple(st[old.FOE_BATTLE+0x22:old.FOE_BATTLE+0x24]),(0,0))
        self.assertEqual(st[old.PLAYER_BATTLE+0x20],4)
        st[old.FOE_BATTLE+0x1E] = 12
        foe_moves = (111,move,45,39) if curl else (move,150,45,39)
        foe_pp = (1,4,0,0) if curl else (4,0,0,0)
        player_moves = (720 if drain else 150,182,45,39)
        for bank,party,moves,pps in (
            (old.FOE_BATTLE,old.ENEMY_PARTY_ADDR,foe_moves,foe_pp),
            (old.PLAYER_BATTLE,old.PARTY,player_moves,(20,20,0,0)),
        ):
            history.set_moves(st,party,0,moves,pps)
            for i,mid in enumerate(moves):
                old.put16(st,bank+12+2*i,mid)
                st[bank+0x25+i] = pps[i]
            # Atributos não criptografados também coerentes com a equipe.
            for battle_delta,party_delta in ((2,90),(4,92),(6,94),(8,96),(10,98)):
                old.put16(st,old.offset(party)+party_delta,old.u16(st,bank+battle_delta))
        self.assertEqual(old.u16(st,history.LAST_MOVES+2),0)
        self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&(history.MULTIPLETURNS|DEFENSE_CURL))
        return bytes(st)

    def turn(self,st,*,direction=None):
        """Observa cada frame, inclusive confirmação de mensagens, sem escrever RAM.

        Captura potência/corrente no momento em que o HP real do defensor
        muda, antes de outro golpe sobrescrever as variáveis globais.
        """
        self.f.restore(st)
        hp = old.u16(st,old.PLAYER_BATTLE+0x2A)
        events = []
        def run(frames,*buttons):
            nonlocal hp
            for _ in range(frames):
                self.f.run(1,*buttons)
                state = self.f.state()
                now = old.u16(state,old.PLAYER_BATTLE+0x2A)
                if now != hp:
                    events.append((hp-now,old.u16(state,MOVE_POWER),old.u16(state,CURRENT_MOVE)))
                    hp = now
        run(3,'A'); run(25)
        if direction:
            run(3,direction); run(15)
        run(6,'A'); run(1100)
        for _ in range(8):
            run(3,'B'); run(90)
        out = self.f.state()
        self.assertIn('vai fazer?',history.text(out))
        self.assertEqual(old.u16(out,old.offset(old.PARTY)+86),hp)
        # Confere checksum inclusive nos turnos em que os PPs não mudam.
        history.party_pp(out,old.PARTY,0)
        history.party_pp(out,old.ENEMY_PARTY_ADDR,0)
        return out,events

    def assert_hit(self,st,events,move,power):
        self.assertEqual(len(events),1,events)
        damage,observed_power,observed_move = events[0]
        self.assertEqual((observed_move,observed_power),(move,power))
        self.assertIn(damage,neutral_damage_values(
            st[old.FOE_BATTLE+0x2C],old.u16(st,old.FOE_BATTLE+2),
            old.u16(st,old.PLAYER_BATTLE+4),power))
        self.assertEqual(old.u16(st,history.LAST_MOVES+2),move)

    def assert_pp(self,st,expected):
        self.assertEqual(history.party_pp(st,old.ENEMY_PARTY_ADDR,0),expected)
        self.assertEqual(list(st[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29]),expected)

    def prepare_curl(self,st):
        st,events = self.turn(st)
        self.assertEqual(events,[])
        self.assertEqual(old.u16(st,history.LAST_MOVES+2),111)
        self.assertTrue(old.u32(st,old.FOE_BATTLE+0x54)&DEFENSE_CURL)
        self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&history.MULTIPLETURNS)
        self.assertEqual(st[old.FOE_BATTLE+0x1A],7)
        self.assert_pp(st,[0,4,0,0])
        return st

    def sequence(self,move,*,drain,curl):
        st = self.scenario(move,drain=drain,curl=curl)
        if curl:
            st = self.prepare_curl(st)
        for turn,power in enumerate((30,60,120,240,480),1):
            st,events = self.turn(st)
            self.assert_hit(st,events,move,power*(2 if curl else 1))
            self.assertEqual(bool(old.u32(st,old.FOE_BATTLE+0x54)&history.MULTIPLETURNS),turn<5)
            expected = [0]*4
            expected[1 if curl else 0] = 0 if drain else 3
            self.assert_pp(st,expected)
        st,events = self.turn(st)
        if drain:
            self.assert_hit(st,events,165,50)
            self.assert_pp(st,[0]*4)
            self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&history.MULTIPLETURNS)
        else:
            self.assert_hit(st,events,move,60 if curl else 30)
            self.assertTrue(old.u32(st,old.FOE_BATTLE+0x54)&history.MULTIPLETURNS)
            expected[1 if curl else 0] = 2
            self.assert_pp(st,expected)

    def test_rollout_progressao_e_reinicio_sem_dreno(self):
        self.sequence(205,drain=False,curl=False)

    def test_rollout_progressao_com_pp_zero_e_struggle(self):
        self.sequence(205,drain=True,curl=False)

    def test_defense_curl_dobra_rollout_ate_960_e_preserva_bonus_no_reinicio(self):
        self.sequence(205,drain=False,curl=True)

    def test_defense_curl_e_rollout_com_pp_zero(self):
        self.sequence(205,drain=True,curl=True)

    def test_ice_ball_compartilha_progressao_e_reinicio(self):
        self.sequence(301,drain=False,curl=False)

    def test_ice_ball_com_defense_curl_e_pp_zero(self):
        self.sequence(301,drain=True,curl=True)

    def test_reproduz_pp_extra_v13_em_protect_mas_potencia_reinicia(self):
        # CARACTERIZAÇÃO DE DEFEITO, não expectativa moderna: no v13 a trava
        # é cancelada antes do teste que deveria dispensar ppreduce. A ROM é
        # fixada por SHA; não reutilizar esta expectativa em versão corrigida.
        for move in (205,301):
            for curl in (False,True):
                with self.subTest(move=move,curl=curl):
                    st = self.scenario(move,curl=curl)
                    if curl:
                        st = self.prepare_curl(st)
                    factor = 2 if curl else 1
                    for power in (30,60):
                        st,events = self.turn(st)
                        self.assert_hit(st,events,move,power*factor)
                    expected_modern = [0]*4
                    slot = 1 if curl else 0
                    expected_modern[slot] = 3
                    self.assert_pp(st,expected_modern)
                    self.assertTrue(old.u32(st,old.FOE_BATTLE+0x54)&history.MULTIPLETURNS)
                    st,events = self.turn(st,direction='RIGHT')  # Protect natural
                    self.assertEqual(events,[])
                    self.assertEqual(old.u16(st,history.LAST_MOVES),182)
                    self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&history.MULTIPLETURNS)
                    self.assertEqual(bool(old.u32(st,old.FOE_BATTLE+0x54)&DEFENSE_CURL),curl)
                    # A expectativa moderna era 3; a execução inicial falhou
                    # exatamente aqui. Registramos o defeito, não o ocultamos.
                    self.assertNotEqual(history.party_pp(st,old.ENEMY_PARTY_ADDR,0),expected_modern)
                    observed_v13 = expected_modern.copy()
                    observed_v13[slot] = 2
                    self.assert_pp(st,observed_v13)
                    st,events = self.turn(st,direction='LEFT')  # Splash novamente
                    self.assert_hit(st,events,move,30*factor)
                    observed_v13[slot] = 1
                    self.assert_pp(st,observed_v13)

    def test_protect_com_pp_zero_encerra_trava_sem_underflow(self):
        for move in (205,301):
            with self.subTest(move=move):
                st = self.scenario(move,drain=True)
                for power in (30,60):
                    st,events = self.turn(st)
                    self.assert_hit(st,events,move,power)
                    self.assert_pp(st,[0]*4)
                st,events = self.turn(st,direction='RIGHT')
                self.assertEqual(events,[])
                self.assertEqual(old.u16(st,history.LAST_MOVES),182)
                self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&history.MULTIPLETURNS)
                self.assert_pp(st,[0]*4)
                st,events = self.turn(st,direction='LEFT')
                self.assert_hit(st,events,165,50)
                self.assert_pp(st,[0]*4)
