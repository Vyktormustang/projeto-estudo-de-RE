"""The four validated v21 gameplay flows, now run on SHA-locked v24.

Fresh v24 fixtures; no use of a saved state/flash from another ROM version.
"""
import os
import unittest
from pathlib import Path
import test_motor_v21_gameplay_mgba as previous
import test_motor_v24_mgba as current
from test_eventos_fixos_mgba import route_entry_fixture
from test_motor_v19_mgba import elapsed, set_time
from test_estojo_expandido_mgba import add, get
from test_golpes_gen9_integracao import save_game, load_game
from mgba_treino_harness import Emulator
from battle_fixture_helpers import in_battle, main_callback2


class MotorV24GameplayTests(previous.MotorV21GameplayTests):
    __unittest_skip__ = not (current.ROM and current.CORE)
    __unittest_skip_why__ = 'set MOTOR_V24_ROM and MGBA_CORE'
    setUpClass = classmethod(current.prepare)
    tearDownClass = classmethod(current.finish)

    @unittest.skipUnless(os.environ.get('MOTOR_V24_BASE'), 'set MOTOR_V24_BASE')
    def test_synthetic_v23_flash_migrates_party_items_map_and_night_time(self):
        base = Path(os.environ['MOTOR_V24_BASE'])
        self.assertEqual(current.p.digest(base.read_bytes()), current.p.BASE_SHA256)
        # Generate a NEW game in the exact predecessor, never a personal save
        # or a v23 savestate restored into v24. Only native flash crosses versions.
        self.f.close()
        try:
            old = Emulator(base, Path(current.CORE), Path(self.temp.name))
            try:
                state = route_entry_fixture(old)
                state = bytes(set_time(add(old, state, 4, 7), 1320))
                old.restore(state)
                flash = save_game(old)
                self.assertEqual(len(flash), 131072)
            finally:
                old.close()
        finally:
            self.f = Emulator(self.rom, Path(current.CORE), Path(self.temp.name))
            type(self).f = self.f
        loaded = load_game(self.f, flash)
        self.assertFalse(in_battle(loaded))
        self.assertEqual(main_callback2(loaded), main_callback2(state))
        self.assertEqual(previous.location(loaded), previous.location(state))
        self.assertEqual(loaded[previous.PARTY_COUNT], state[previous.PARTY_COUNT])
        self.assertEqual(previous.party_slot(loaded, 0), previous.party_slot(state, 0))
        # 840 played seconds = 22:00 virtual. Saving/loading advances playtime;
        # it must not reset to 08:00, and remains within this night window.
        self.assertTrue(840 <= elapsed(loaded) < 900, elapsed(loaded))
        self.assertEqual(get(self.f, loaded, 4), 7)
        self.assertEqual(current.p.digest(base.read_bytes()), current.p.BASE_SHA256)
