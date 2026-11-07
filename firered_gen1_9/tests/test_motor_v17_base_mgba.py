"""Contrafactual separado: o defeito permanece reproduzível na entrada v16."""
import os
import tempfile
from pathlib import Path
import test_motor_v16_combined_hazards_mgba as previous

BASE=os.environ.get('MOTOR_V17_BASE')

class MotorV17BaseNegativeTests(previous.MotorV16CombinedHazardsTests):
    __unittest_skip__=not(BASE and previous.CORE)
    __unittest_skip_why__='defina MOTOR_V17_BASE e MGBA_CORE'
    test_spikes_primeiro_camadas_e_ko_no_primeiro_ou_segundo_hazard=None
    test_caracterizacao_negativa_stealth_rock_primeiro_nao_define_ordem_da_v16=None
    test_quarta_camada_e_sr_repetido_nao_aumentam_dano=None
    test_caracterizacao_negativa_ordem_inversa_persiste_apos_tentativas_repetidas=None
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(BASE)
        if previous.patch.digest(cls.rom.read_bytes())!=previous.patch.OUTPUT_SHA256:
            raise ValueError('Entrada não é v16 exato')
        cls.temp=tempfile.TemporaryDirectory()
        cls.f=previous.old.Emulator(cls.rom,Path(previous.CORE),Path(cls.temp.name))
        cls.fixture=previous.old.route_entry_fixture(cls.f)
        cls.doubles_fixture=cls._make_doubles_fixture()
    def test_base_v16_mantem_ordem_errada_com_danos_diferentes_e_iguais(self):
        for layers in (1,3):
            with self.subTest(layers=layers):self.verify(layers,True,100)
