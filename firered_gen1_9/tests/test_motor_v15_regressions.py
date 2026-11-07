"""Regressões positivas v13/v14/histórico com fixtures novas sobre v15 verificado.

Não herda a caracterização do defeito antigo nem compartilha estados entre ROMs.
"""
import tempfile
from pathlib import Path
import test_motor_v13_mgba as v13
import test_eerie_history_mgba as history
import test_motor_v15_mgba as current
import test_motor_v14_mgba as protect
import test_motor_v14_interruptions_mgba as interruptions
from battle_fixture_helpers import set_level10_starter_test_stats

old = current.old
ENABLED = bool(current.BASE and current.ROM and current.CORE)


def prepare(cls,*,families=False,switch=False,doubles_only=False):
    cls.rom,cls.base,cls.core = Path(current.ROM),Path(current.BASE),Path(current.CORE)
    if cls.rom.read_bytes() != current.patch.build(cls.base.read_bytes()):
        raise ValueError('ROM v15 divergente')
    cls.temp = tempfile.TemporaryDirectory()
    cls.dir = Path(cls.temp.name)
    cls.f = old.Emulator(cls.rom,cls.core,cls.dir)
    cls.fixture = old.route_entry_fixture(cls.f)
    if doubles_only:
        cls.doubles_fixture = cls._make_doubles_fixture()
    else:
        cls.battle_fixture = cls._make_singles_fixture()
    if families:
        cls.two_party_fixture = cls._make_two_party_singles_fixture()
        cls.two_enemy_fixture = cls._make_two_enemy_trainer_like_fixture()
        cls.doubles_fixture = cls._make_doubles_fixture()
    if switch:
        a = bytearray(old.seed_mon(cls.fixture,1,10,(150,45,33,39)))
        b = bytearray(old.seed_mon(cls.fixture,4,10,(45,150,33,39)))
        for st in (a,b): set_level10_starter_test_stats(st,stat=200)
        pos = old.offset(old.PARTY)
        a[pos+100:pos+200] = b[pos:pos+100]
        a[old.offset(old.PLAYER_PARTY_COUNT)] = 2
        cls.switch_fixture = cls._enter_wild_encounter(a)


def finish(cls):
    cls.f.close()
    cls.temp.cleanup()
    if current.patch.digest(cls.rom.read_bytes()) != current.patch.OUTPUT_SHA256:
        raise AssertionError('ROM alterada')


class MotorV15EerieTests(v13.MotorV13MGBATests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'defina MOTOR_V15_BASE, MOTOR_V15_ROM e MGBA_CORE'
    # O contrafactual v12 não é uma propriedade da saída v15. Os positivos
    # Substitute/Shield Dust/Soundproof/KO continuam sendo herdados.
    test_defeitos_reproduzidos_na_base_v12_com_turno_completo = None

    @classmethod
    def setUpClass(cls): prepare(cls)
    @classmethod
    def tearDownClass(cls): finish(cls)


class MotorV15FamiliesTests(v13.MotorV13InheritedRegressionTests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'defina MOTOR_V15_BASE, MOTOR_V15_ROM e MGBA_CORE'
    @classmethod
    def setUpClass(cls): prepare(cls,families=True)
    @classmethod
    def tearDownClass(cls): finish(cls)


class MotorV15HistoryTests(history.EerieHistoryMGBATests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'defina MOTOR_V15_BASE, MOTOR_V15_ROM e MGBA_CORE'
    @classmethod
    def setUpClass(cls): prepare(cls,switch=True)
    @classmethod
    def tearDownClass(cls): finish(cls)


class MotorV15ProtectTests(protect.MotorV14MGBATests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'defina MOTOR_V15_BASE, MOTOR_V15_ROM e MGBA_CORE'
    test_defeito_reproduzido_no_v13_com_fixtures_proprias = None

    @classmethod
    def setUpClass(cls): prepare(cls)
    @classmethod
    def tearDownClass(cls): finish(cls)


class MotorV15DoublesTests(interruptions.MotorV14DoublesInterruptionTests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'defina MOTOR_V15_BASE, MOTOR_V15_ROM e MGBA_CORE'

    @classmethod
    def setUpClass(cls): prepare(cls,doubles_only=True)
    @classmethod
    def tearDownClass(cls): finish(cls)


class MotorV15NaturalInterruptionTests(interruptions.MotorV14NaturalInterruptionTests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'defina MOTOR_V15_BASE, MOTOR_V15_ROM e MGBA_CORE'

    @classmethod
    def setUpClass(cls): prepare(cls)
    @classmethod
    def tearDownClass(cls): finish(cls)
