"""Negativos EXCLUSIVAMENTE na base v17; fixtures próprias dessa ROM."""
import os
import tempfile
from pathlib import Path
import test_motor_v17_blocked_pivots_mgba as previous
from scripts import motor_v18 as patch

BASE=os.environ.get('MOTOR_V18_BASE')
CORE=os.environ.get('MGBA_CORE')

class MotorV18BaseNegativeTests(previous.MotorV17BlockedPivotsTests):
    __unittest_skip__=not(BASE and CORE)
    __unittest_skip_why__='defina MOTOR_V18_BASE e MGBA_CORE'
    test_protect_bloqueia_os_quatro_pivos_nos_dois_bancos=None
    test_absorcao_eletrica_e_agua_impede_troca=None
    test_parting_clear_body_e_dois_atributos_minimos=None
    test_quatro_pivos_sem_reservas_elegiveis=None
    test_ground_sem_reserva_nao_abre_selecao=None
    test_parting_um_atributo_minimo_ainda_permite_troca=None
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(BASE)
        if patch.digest(cls.rom.read_bytes())!=patch.BASE_SHA256:raise ValueError('Base não é v17 exato')
        cls.temp=tempfile.TemporaryDirectory()
        cls.f=previous.old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture=previous.old.route_entry_fixture(cls.f)
        cls.doubles_fixture=cls._make_doubles_fixture()
    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.BASE_SHA256:raise AssertionError('Base alterada')
