"""Regressões dirigidas, fixtures novas na v17; não importa negativos v15/v16."""
import tempfile
from pathlib import Path
import test_motor_v17_combined_hazards_mgba as current
import test_motor_v16_doubles_endings_mgba as ending
import test_motor_v16_hazards_ko_mgba as singles
import test_motor_v16_mgba as phazing
import test_motor_v8_mgba as v8

ENABLED=bool(current.ROM and current.CORE)

def prepare(cls):
    cls.rom=Path(current.ROM)
    if current.patch.digest(cls.rom.read_bytes())!=current.patch.OUTPUT_SHA256:
        raise ValueError('ROM não é v17 exato')
    cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
    phazing.prepare(cls,current.ROM,cls.dir)

class MotorV17EndingsTests(ending.MotorV16DoublesEndingsTests):
    __unittest_skip__=not ENABLED
    setUpClass=classmethod(current.MotorV17CombinedHazardsTests.setUpClass.__func__)
    tearDownClass=classmethod(current.MotorV17CombinedHazardsTests.tearDownClass.__func__)

class MotorV17SinglesTests(singles.MotorV16HazardsKOTests):
    __unittest_skip__=not ENABLED
    @classmethod
    def setUpClass(cls):prepare(cls)
    tearDownClass=classmethod(current.MotorV17CombinedHazardsTests.tearDownClass.__func__)

class MotorV17PhazingTests(phazing.MotorV16MGBATests):
    __unittest_skip__=not ENABLED
    test_defeito_reproduzido_somente_na_base_v15=None
    test_encontros_selvagens_preservam_resultado_da_base=None
    @classmethod
    def setUpClass(cls):prepare(cls)
    tearDownClass=classmethod(current.MotorV17CombinedHazardsTests.tearDownClass.__func__)

class MotorV17LegacyFieldTests(v8.MotorV8MGBATests):
    __unittest_skip__=not ENABLED
    test_snowscape_chilly_reception_blizzard_weather_ball_aurora_veil_e_quebra_barreira=None
    test_quatro_terrenos_bloqueios_cura_e_sinergias_de_golpes=None
    test_tailwind_trick_room_wonder_room_gravity_magnet_rise_e_shore_up=None
    test_estojo_v2_10_tms_finais_229_completas_save_reload_e_learnsets_v8=None
    test_regressao_cadeia_v6_v7_preservada=None
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(current.ROM)
        if current.patch.digest(cls.rom.read_bytes())!=current.patch.OUTPUT_SHA256:
            raise ValueError('ROM não é v17 exato')
        cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
        cls.f=v8.Emulator(cls.rom,Path(current.CORE),cls.dir)
        cls.fixture=v8.route_entry_fixture(cls.f)
        cls.battle_fixture=cls._make_singles_fixture()
        cls.two_party_battle_fixture=cls._make_two_party_singles_fixture()
        cls.doubles_fixture=cls._make_doubles_fixture()
    tearDownClass=classmethod(current.MotorV17CombinedHazardsTests.tearDownClass.__func__)
