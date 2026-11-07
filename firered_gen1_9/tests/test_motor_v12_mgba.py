"""Soundproof em v12 + auditoria explícita de limites; só estados sintéticos.

As duas verificações `test_limite_*` caracterizam defeitos NÃO corrigidos.
Não são testes de conformidade moderna de Substitute/Shield Dust.
"""
from __future__ import annotations
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v11_mgba as v11
from scripts import motor_v12 as patch

old = v11.old
BASE = os.environ.get('MOTOR_V12_BASE')
ROM = os.environ.get('MOTOR_V12_ROM')
CORE = os.environ.get('MGBA_CORE')
SUB_HP = old.offset(old.DISABLE_STRUCTS_REAL_ADDR) + 28 + 10


def pp(state):
    return list(state[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29])


def text(state):
    return old.decode_gba_str(state[old.offset(old.DISP_STR):old.offset(old.DISP_STR)+80])


@unittest.skipUnless(BASE and ROM and CORE, 'defina MOTOR_V12_BASE, MOTOR_V12_ROM e MGBA_CORE')
class MotorV12MGBATests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state
    eerie_state = v11.MotorV11MGBATests.eerie_state

    def _run_turn(self, state, *, slot=0, frames=1100):
        out, seen = old.MotorV10MGBATests._run_turn(self, state, slot=slot, frames=frames)
        # O teste v11 de Substitute parava no texto <fb>, antes de datahpupdate.
        # B confirma a mensagem sem selecionar uma nova ação no menu de batalha.
        for _ in range(8):
            self.f.pulse('B', 90)
        out = self.f.state()
        final = text(out)
        self.assertIn('vai fazer?', final, (final, seen))
        # No menu o controller do jogador fica ativo aguardando a escolha;
        # não exigir execFlags == 0 (isso rejeitaria o menu legítimo).
        return out, seen

    @classmethod
    def setUpClass(cls):
        base, rom = Path(BASE), Path(ROM)
        if rom.read_bytes() != patch.build(base.read_bytes()):
            raise ValueError('ROM diverge do build determinístico v12')
        cls.temp = tempfile.TemporaryDirectory()
        # Fixture gerada em cada ROM. Nenhum state é transferido entre versões.
        cls.f = old.Emulator(base, Path(CORE), Path(cls.temp.name)/'base')
        try:
            cls.fixture = old.route_entry_fixture(cls.f)
            cls.battle_fixture = cls._make_singles_fixture()
            test = cls()
            st = bytearray(test.eerie_state())
            old.put16(st, old.FOE_BATTLE+0x20, 43)
            out, _ = test._run_turn(bytes(st))
            cls.baseline_hp = old.u16(out, old.FOE_BATTLE+0x2A)
            cls.baseline_pp = pp(out)
        finally:
            cls.f.close()
        cls.f = old.Emulator(rom, Path(CORE), Path(cls.temp.name)/'v12')
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    def soundproof_state(self, *, sub=0):
        st = bytearray(self.eerie_state(status2=0x01000000 if sub else 0))
        old.put16(st, old.FOE_BATTLE+0x20, 43)
        st[SUB_HP] = sub
        return bytes(st)

    def test_defeito_soundproof_reproduzido_na_base_v11(self):
        self.assertLess(self.baseline_hp, 480)
        self.assertEqual(self.baseline_pp, [10,10,7,10])

    def test_soundproof_bloqueia_dano_e_dreno_mas_consumo_proprio_permanece(self):
        st = self.soundproof_state()
        party_before = [v11.party_pp(st,s) for s in range(4)]
        out, seen = self._run_turn(st)
        self.assertEqual(old.u16(out, old.FOE_BATTLE+0x2A), 480)
        self.assertEqual(pp(out), [10]*4)
        self.assertEqual([v11.party_pp(out,s) for s in range(4)], party_before)
        self.assertEqual(out[old.PLAYER_BATTLE+0x25], st[old.PLAYER_BATTLE+0x25]-1)
        # Confirma o fluxo de mensagem nativo, não apenas HP intacto.
        self.assertTrue(any('SOUNDPROOF' in s.upper() for s in seen), seen)

    def test_controles_sem_soundproof_e_golpe_nao_sonoro(self):
        out, _ = self._run_turn(self.eerie_state())
        self.assertLess(old.u16(out, old.FOE_BATTLE+0x2A), 480)
        self.assertEqual(pp(out), [10,10,7,10])
        out, _ = self._run_turn(self._duel_state(33, f_ability=43, f_status1=7))
        self.assertLess(old.u16(out, old.FOE_BATTLE+0x2A), 480)
        self.assertEqual(pp(out), [40]*4)

    def test_soundproof_preserva_substitute_forte_e_fragil(self):
        for sub in (1,200):
            with self.subTest(sub=sub):
                out, _ = self._run_turn(self.soundproof_state(sub=sub))
                self.assertEqual(old.u16(out, old.FOE_BATTLE+0x2A),480)
                self.assertEqual(pp(out), [10]*4)
                self.assertEqual(out[SUB_HP],sub)
                self.assertTrue(old.u32(out,old.FOE_BATTLE+0x54) & 0x01000000)

    def test_growl_e_hyper_voice_nativos_continuam_bloqueados(self):
        # Growl é o primeiro ID (tratado separadamente pelo compilador);
        # Hyper Voice era o último antes do terminador da lista antiga.
        for move in (45,304):
            with self.subTest(move=move):
                st = self._duel_state(move,f_ability=43,f_status1=7)
                out, seen = self._run_turn(st)
                self.assertEqual(old.u16(out,old.FOE_BATTLE+0x2A),480)
                self.assertEqual(out[old.FOE_BATTLE+0x19],6)
                self.assertTrue(any('SOUNDPROOF' in s.upper() for s in seen),seen)

    def test_turno_seguinte_nao_herda_bloqueio(self):
        st = bytearray(self.soundproof_state())
        old.put16(st,old.PLAYER_BATTLE+0x0E,33)
        out, _ = self._run_turn(bytes(st))
        out, _ = self._run_turn(out,slot=1)
        self.assertLess(old.u16(out,old.FOE_BATTLE+0x2A),480)
        self.assertEqual(pp(out),[10]*4)

    def test_limite_substitute_ainda_intercepta_eerie_sem_soundproof(self):
        # Caracterização de desvio conhecido, NÃO expectativa moderna correta.
        for sub in (1,200):
            with self.subTest(sub=sub):
                st = bytearray(self.eerie_state(status2=0x01000000))
                st[SUB_HP] = sub
                out, _ = self._run_turn(bytes(st))
                self.assertEqual(old.u16(out,old.FOE_BATTLE+0x2A),480)
                self.assertEqual(pp(out),[10]*4)
                self.assertLess(out[SUB_HP],sub)
                self.assertEqual(bool(old.u32(out,old.FOE_BATTLE+0x54)&0x01000000),sub>1)

    def test_limite_shield_dust_ainda_permite_dreno(self):
        # Shield Dust deveria impedir o efeito adicional, não o dano.
        st = bytearray(self.eerie_state())
        old.put16(st,old.FOE_BATTLE+0x20,19)
        out, _ = self._run_turn(bytes(st))
        self.assertLess(old.u16(out,old.FOE_BATTLE+0x2A),480)
        self.assertEqual(pp(out),[10,10,7,10])  # defeito caracterizado

    # Regressões da correção de PP v11, agora exigindo término de turno.
    test_ultimo_golpe_slot2_e_checksum_equipe = v11.MotorV11MGBATests.test_ultimo_golpe_slot2_e_checksum_equipe
    test_sem_fallback_e_sem_underflow = v11.MotorV11MGBATests.test_sem_fallback_e_sem_underflow
    test_transform_e_mimic_nao_alteram_pp_originais = v11.MotorV11MGBATests.test_transform_e_mimic_nao_alteram_pp_originais
    test_protect_e_imunidade_nao_drenam = v11.MotorV11MGBATests.test_protect_e_imunidade_nao_drenam
    test_ultimo_golpe_registrado_naturalmente = v11.MotorV11MGBATests.test_ultimo_golpe_registrado_naturalmente
    test_mighty_cleave_ja_atravessa_protect_e_tackle_nao = v11.MotorV11MGBATests.test_mighty_cleave_ja_atravessa_protect_e_tackle_nao


class MotorV12InheritedRegressionTests(old.MotorV10MGBATests):
    """Seis famílias v10 executadas em fixtures novas da ROM v12."""
    __unittest_skip__ = not bool(BASE and ROM and CORE)
    __unittest_skip_why__ = 'defina MOTOR_V12_BASE, MOTOR_V12_ROM e MGBA_CORE'

    @classmethod
    def setUpClass(cls):
        cls.rom, cls.base, cls.core = Path(ROM), Path(BASE), Path(CORE)
        if cls.rom.read_bytes() != patch.build(cls.base.read_bytes()):
            raise ValueError('ROM v12 divergente')
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        cls.f = old.Emulator(cls.rom,cls.core,cls.dir)
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()
        cls.two_party_fixture = cls._make_two_party_singles_fixture()
        cls.two_enemy_fixture = cls._make_two_enemy_trainer_like_fixture()
        cls.doubles_fixture = cls._make_doubles_fixture()
