"""Regressões dirigidas na v18 exata; não importar negativos de outras ROMs."""
import tempfile
import unittest
from pathlib import Path
import test_motor_v18_mgba as current
import test_motor_v17_switch_pivot_hazards_mgba as switches
import test_motor_v17_lifecycle_mgba as lifecycle
import test_motor_v12_mgba as sound


class MotorV18SwitchHazardsTests(switches.MotorV17SwitchPivotHazardsTests):
    __unittest_skip__=not current.ENABLED
    __unittest_skip_why__='defina MOTOR_V18_ROM e MGBA_CORE'
    setUpClass=classmethod(current.prepare)
    tearDownClass=classmethod(current.finish)


class MotorV18LifecycleTests(lifecycle.MotorV17LifecycleTests):
    __unittest_skip__=not current.ENABLED
    __unittest_skip_why__='defina MOTOR_V18_ROM e MGBA_CORE'
    setUpClass=classmethod(current.prepare)
    tearDownClass=classmethod(current.finish)


@unittest.skipUnless(current.ENABLED,'defina MOTOR_V18_ROM e MGBA_CORE')
class MotorV18SoundproofTests(unittest.TestCase):
    _enter_wild_encounter=classmethod(sound.MotorV12MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture=classmethod(sound.MotorV12MGBATests._make_singles_fixture.__func__)
    _duel_state=sound.MotorV12MGBATests._duel_state
    _run_turn=sound.MotorV12MGBATests._run_turn
    eerie_state=sound.MotorV12MGBATests.eerie_state
    soundproof_state=sound.MotorV12MGBATests.soundproof_state
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(current.ROM)
        if current.patch.digest(cls.rom.read_bytes())!=current.patch.OUTPUT_SHA256:raise ValueError('ROM não é v18 exato')
        cls.temp=tempfile.TemporaryDirectory()
        cls.f=current.old.Emulator(cls.rom,Path(current.CORE),Path(cls.temp.name))
        cls.fixture=current.old.route_entry_fixture(cls.f)
        cls.battle_fixture=cls._make_singles_fixture()
    tearDownClass=classmethod(current.finish)
    test_soundproof_bloqueia_dano_e_dreno_mas_consumo_proprio_permanece=sound.MotorV12MGBATests.test_soundproof_bloqueia_dano_e_dreno_mas_consumo_proprio_permanece
    test_controles_sem_soundproof_e_golpe_nao_sonoro=sound.MotorV12MGBATests.test_controles_sem_soundproof_e_golpe_nao_sonoro
    test_soundproof_preserva_substitute_forte_e_fragil=sound.MotorV12MGBATests.test_soundproof_preserva_substitute_forte_e_fragil
    test_growl_e_hyper_voice_nativos_continuam_bloqueados=sound.MotorV12MGBATests.test_growl_e_hyper_voice_nativos_continuam_bloqueados
    test_turno_seguinte_nao_herda_bloqueio=sound.MotorV12MGBATests.test_turno_seguinte_nao_herda_bloqueio

    def test_historico_soundproof_nativo_e_acao_seguinte(self):
        # Oráculo nativo independente do antigo teste de pivô: a habilidade
        # cancela antes do flag OBEYS, e moveend grava MOVE_UNAVAILABLE.
        for move in (45,304,720,571):
            with self.subTest(move=move):
                st=bytearray(self._duel_state(move,f_ability=43,f_status1=7))
                current.old.put16(st,current.old.PLAYER_BATTLE+0x0E,33)
                out,seen=self._run_turn(bytes(st))
                self.assertTrue(any('SOUNDPROOF' in x for x in seen),seen)
                self.assertEqual(current.old.u16(out,current.h.LAST_MOVES),0xFFFF)
                self.assertEqual(out[current.old.PLAYER_BATTLE+0x25],st[current.old.PLAYER_BATTLE+0x25]-1)
                self.assertEqual(current.old.u16(out,current.old.FOE_BATTLE+0x2A),480)
                for off in (0x19,0x1C):self.assertEqual(out[current.old.FOE_BATTLE+off],6)
                out,_=self._run_turn(out,slot=1)
                self.assertEqual(current.old.u16(out,current.h.LAST_MOVES),33)
                self.assertLess(current.old.u16(out,current.old.FOE_BATTLE+0x2A),480)
