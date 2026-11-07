"""Selected battle regressions on EXACT v21; no legacy hash checks bypassed.

MOTOR_V21_ROM and MGBA_CORE (mGBA 0.10.5). Synthetic fixtures only.
These adapters deliberately do not import base-ROM negative test classes.
"""
import os
import tempfile
import unittest
from pathlib import Path
from scripts import motor_v21 as patch
import test_motor_v18_mgba as battle
import test_motor_v18_regressions as previous
import test_battle_experience_fixture as experience

ROM = os.environ.get('MOTOR_V21_ROM')
CORE = os.environ.get('MGBA_CORE')
ENABLED = bool(ROM and CORE)


def prepare(cls, *, singles=False):
    cls.rom = Path(ROM)
    if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
        raise ValueError('Not exact v21')
    cls.temp = tempfile.TemporaryDirectory()
    cls.f = battle.old.Emulator(cls.rom, Path(CORE), Path(cls.temp.name))
    cls.fixture = battle.old.route_entry_fixture(cls.f)
    if singles:
        cls.battle_fixture = cls._make_singles_fixture()
    else:
        cls.doubles_fixture = cls._make_doubles_fixture()


def prepare_singles(cls):
    prepare(cls, singles=True)


def finish(cls):
    cls.f.close()
    cls.temp.cleanup()
    if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
        raise AssertionError('ROM changed')


class MotorV21BlockedPivotsTests(battle.MotorV18BlockedPivotsTests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'set MOTOR_V21_ROM and MGBA_CORE'
    setUpClass = classmethod(prepare)
    tearDownClass = classmethod(finish)


class MotorV21SwitchHazardsTests(previous.MotorV18SwitchHazardsTests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'set MOTOR_V21_ROM and MGBA_CORE'
    setUpClass = classmethod(prepare)
    tearDownClass = classmethod(finish)


class MotorV21LifecycleTests(previous.MotorV18LifecycleTests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'set MOTOR_V21_ROM and MGBA_CORE'
    setUpClass = classmethod(prepare)
    tearDownClass = classmethod(finish)


class MotorV21SoundproofTests(previous.MotorV18SoundproofTests):
    __unittest_skip__ = not ENABLED
    __unittest_skip_why__ = 'set MOTOR_V21_ROM and MGBA_CORE'
    setUpClass = classmethod(prepare_singles)
    tearDownClass = classmethod(finish)


@unittest.skipUnless(ENABLED, 'set MOTOR_V21_ROM and MGBA_CORE')
class MotorV21ExperienceTests(experience.ExperienceCases, unittest.TestCase):
    rom_path = ROM
    expected_hash = patch.OUTPUT_SHA256
    # Historical causal negative intentionally uses incoherent EXP=1/level=10;
    # it is not a gameplay acceptance condition for this validation pass.
    test_causal_exp1_bloqueia_e_controles559_560_encerram = None
