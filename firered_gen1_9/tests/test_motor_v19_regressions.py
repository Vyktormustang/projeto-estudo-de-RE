"""Selected v18 battle contracts run on SHA-locked v19, not a hash bypass."""
import os
import tempfile
from pathlib import Path
import test_motor_v18_mgba as v18
from scripts import motor_v19 as patch

ROM = os.environ.get('MOTOR_V19_ROM')
CORE = os.environ.get('MGBA_CORE')

def prepare(cls):
    cls.rom=Path(ROM)
    if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise ValueError('Not exact v19')
    cls.temp=tempfile.TemporaryDirectory()
    cls.f=v18.old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
    cls.fixture=v18.old.route_entry_fixture(cls.f)
    cls.doubles_fixture=cls._make_doubles_fixture()

def finish(cls):
    cls.f.close();cls.temp.cleanup()
    if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise AssertionError('ROM changed')

class MotorV19BlockedPivotsTests(v18.MotorV18BlockedPivotsTests):
    __unittest_skip__=not (ROM and CORE)
    __unittest_skip_why__='set MOTOR_V19_ROM and MGBA_CORE'
    setUpClass=classmethod(prepare)
    tearDownClass=classmethod(finish)
