"""Four selected battle regressions on exact v23, not the full v21 audit."""
import test_motor_v21_regressions as previous
import test_motor_v23_mgba as current


def prepare_singles(cls):
    current.prepare(cls)
    cls.battle_fixture = cls._make_singles_fixture()


class MotorV23SoundproofTests(previous.MotorV21SoundproofTests):
    __unittest_skip__ = not (current.ROM and current.CORE)
    __unittest_skip_why__ = 'set MOTOR_V23_ROM and MGBA_CORE'
    setUpClass = classmethod(prepare_singles)
    tearDownClass = classmethod(current.finish)
    test_controles_sem_soundproof_e_golpe_nao_sonoro = None
    test_soundproof_bloqueia_dano_e_dreno_mas_consumo_proprio_permanece = None
    test_soundproof_preserva_substitute_forte_e_fragil = None
    test_turno_seguinte_nao_herda_bloqueio = None


class MotorV23ExperienceTests(previous.MotorV21ExperienceTests):
    __unittest_skip__ = not (current.ROM and current.CORE)
    __unittest_skip_why__ = 'set MOTOR_V23_ROM and MGBA_CORE'
    rom_path = current.ROM
    expected_hash = current.p.OUTPUT_SHA256
    test_fabricas_singles_duplas_e_reservas_tem_exp_coerente = None
