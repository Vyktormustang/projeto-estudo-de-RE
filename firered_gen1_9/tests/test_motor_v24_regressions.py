"""Four selected battle regressions on exact v24, not the full v21 audit."""
import test_motor_v21_regressions as previous
import test_motor_v24_mgba as current


def prepare_singles(cls):
    current.prepare(cls)
    cls.battle_fixture = cls._make_singles_fixture()


class MotorV24SoundproofTests(previous.MotorV21SoundproofTests):
    __unittest_skip__ = not (current.ROM and current.CORE)
    __unittest_skip_why__ = 'set MOTOR_V24_ROM and MGBA_CORE'
    setUpClass = classmethod(prepare_singles)
    tearDownClass = classmethod(current.finish)
    test_controles_sem_soundproof_e_golpe_nao_sonoro = None
    test_soundproof_bloqueia_dano_e_dreno_mas_consumo_proprio_permanece = None
    test_soundproof_preserva_substitute_forte_e_fragil = None
    test_turno_seguinte_nao_herda_bloqueio = None


class MotorV24ExperienceTests(previous.MotorV21ExperienceTests):
    __unittest_skip__ = not (current.ROM and current.CORE)
    __unittest_skip_why__ = 'set MOTOR_V24_ROM and MGBA_CORE'
    rom_path = current.ROM
    expected_hash = current.p.OUTPUT_SHA256
    test_fabricas_singles_duplas_e_reservas_tem_exp_coerente = None

    def test_subida_nivel10_para11_e_retorno_ao_mapa(self):
        # Don't assume that natural walking still selected the old fixture's
        # Rattata. Use a same-foe KO control; only encrypted EXP differs.
        import test_battle_experience_fixture as exp
        from mgba_treino_harness import mon,mon_facts
        from battle_fixture_helpers import party_experience,finish_victory,main_callback2
        control=self.ko_state(560)
        exp.old.MotorV10MGBATests._run_turn(self,control)
        low=finish_victory(self.f,main_callback2(self.fixture))
        gained=party_experience(low)-560
        self.assertGreater(gained,0)
        self.assertEqual(mon_facts(mon(low))['level'],10)
        st=self.ko_state(741);before=mon_facts(mon(st))
        exp.old.MotorV10MGBATests._run_turn(self,st)
        out=finish_victory(self.f,main_callback2(self.fixture));after=mon_facts(mon(out))
        self.assertEqual(party_experience(out),741+gained)
        self.assertEqual(after['level'],11)
        self.assertEqual(before['iv'],after['iv']);self.assertTrue(after['valid'])
        self.assertGreater(after['hp'],0);self.assertLessEqual(after['hp'],after['max_hp'])
