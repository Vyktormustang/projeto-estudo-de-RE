"""Previous six audit regressions on exact v36; exact release after native flash bootstrap.

Only the journey is shortened in a disposable warp-only ROM. A native save
is loaded in a fresh core running the exact release before any audited action.
No state crosses ROMs. Synthetic time/preference/one Master Ball are initial
conditions, never repairs during walking/capture/connection/save. No personal
save, RNG edit, encounter injection, progression flag or delivered ROM edit.
"""
import struct
import unittest
from pathlib import Path

from scripts import motor_v36 as release
import test_motor_v36_hud_mgba as hud
import test_motor_v36_encounters_mgba as encounters
import test_motor_v36_preferences_mgba as preference
import test_motor_v21_gameplay_mgba as gameplay
import test_motor_v24_mgba as clock
from mgba_treino_harness import Emulator, offset, u32, mon_facts
from test_estojo_expandido_mgba import save1, add, get
from test_golpes_gen9_integracao import save_game, load_game
from test_motor_v19_mgba import set_time, elapsed
from test_eventos_fixos_mgba import enemy, route_entry_fixture
from battle_fixture_helpers import in_battle, main_callback2, BATTLE_OUTCOME
from test_motor_v12_mgba import text

p = release.previous
NEW_MAPS = p.MAPS[32:36]


@unittest.skipUnless(hud.ROM and hud.CORE, 'set MOTOR_V36_ROM and MGBA_CORE')
class MotorV36AuditTests(unittest.TestCase):
    setUpClass = classmethod(hud.prepare)
    tearDownClass = classmethod(hud.finish)
    grass_site = encounters.MotorV36EncounterTests.grass_site
    call = encounters.MotorV36EncounterTests.call
    at_sign = encounters.MotorV36EncounterTests.at_sign
    throw_first_ball = gameplay.MotorV21GameplayTests.throw_first_ball
    assert_ball_metadata = gameplay.MotorV21GameplayTests.assert_ball_metadata

    def switch(self, rom):
        self.f.close()
        type(self).f = self.f = Emulator(rom, Path(hud.CORE), self.dir)

    def header(self, group, number):
        def pointer(at):
            return struct.unpack_from('<I', self.source, at)[0] - 0x08000000
        return pointer(pointer(p.fixed.GROUP_TABLE + 4 * group) + 4 * number)

    def record(self, name):
        return struct.unpack_from('<IIBBH', self.source, p.TABLE_OFFSET + 12 * p.MAPS.index(name))

    def bootstrap(self, name, *, site=None):
        """Native flash is the ONLY bridge from warp copy to exact release."""
        day, night, group, number, _ = self.record(name)
        x, y, buttons = site or self.grass_site(group, number)
        data = bytearray(self.source)
        self.assertEqual(data[0xF90000:0xF9000A], b'\xff' * 10)
        self.assertEqual(struct.unpack_from('<I', data, p.SIGN_POINTER)[0], 0x08000000 + release.SCRIPT_OFFSET)
        struct.pack_into('<I', data, p.SIGN_POINTER, 0x08F90000)
        data[0xF90000:0xF9000A] = struct.pack('<BBBBHHBB', 0x39, group, number, 255, x, y, 0x27, 2)
        restored = bytearray(data)
        for at, size in ((p.SIGN_POINTER, 4), (0xF90000, 10)):
            restored[at:at + size] = self.source[at:at + size]
        self.assertEqual(bytes(restored), self.source)
        path = self.dir / f'audit-bootstrap-{group}-{number}-{self._testMethodName}.gba'
        with path.open('xb') as stream:
            stream.write(data)
        self.switch(path)
        # Start the disposable ROM from its own boot: even preparation must
        # not restore a savestate serialized by a different ROM image.
        original_fixture = self.fixture
        try:
            self.fixture = route_entry_fixture(self.f)
            self.at_sign(600)
        finally:
            self.fixture = original_fixture
        self.f.pulse('A', 150)
        self.f.run(150)
        arrived = self.f.state()
        self.assertEqual(gameplay.location(arrived), (group, number))
        self.assertEqual(gameplay.coords(arrived), (x + 7, y + 7))
        self.assertFalse(in_battle(arrived))
        flash = save_game(self.f)
        self.assertEqual(len(flash), 131072)
        self.switch(self.rom)
        loaded = load_game(self.f, flash)
        self.assertEqual(release.digest(self.rom.read_bytes()), release.OUTPUT_SHA256)
        self.assertEqual(gameplay.location(loaded), (group, number))
        self.assertEqual(gameplay.coords(loaded), (x + 7, y + 7))
        self.assertFalse(in_battle(loaded))
        self.assertEqual(main_callback2(loaded), main_callback2(self.fixture))
        self.assertEqual(gameplay.party_slot(loaded, 0), gameplay.party_slot(arrived, 0))
        return loaded, buttons

    def prepared(self, start, minute, *, hidden=False, capped=False):
        # Before the audited action only. Party, enemy and RNG are untouched.
        st = add(self.f, start, 1, 1)
        st = clock.saturated(st, minute, 0) if capped else set_time(st, minute)
        return bytes(preference.set_pref(st, hidden=hidden))

    def walking_target(self, initial, buttons, species):
        for delay in range(128):
            self.f.restore(initial)
            self.f.run(delay)
            for step in range(100):
                self.f.run(8, buttons[(step // 2) % 2])
                if in_battle(self.f.state()):
                    break
            if not in_battle(self.f.state()):
                continue
            self.f.run(300)
            out = self.f.state()
            if enemy(out)['species'] != species:
                continue
            self.assertEqual(u32(out, offset(0x02020374)) & 8, 0, 'Unexpected trainer battle')
            self.assertTrue(enemy(out)['valid'])
            for _ in range(8):
                if 'vai fazer?' in text(self.f.state()):
                    break
                self.f.pulse('B', 45)
            out = self.f.state()
            self.assertIn('vai fazer?', text(out))
            self.assertFalse(hud.has_hud(out))
            self.assertEqual(gameplay.location(out), gameplay.location(initial))
            return out
        self.fail(f'No natural encounter with species {species} within idle budget')

    def wait_caught(self, before):
        for _ in range(90):
            out = self.f.state()
            if not in_battle(out) and main_callback2(out) == main_callback2(self.fixture):
                self.assertEqual(out[offset(BATTLE_OUTCOME)], 7)
                self.assertEqual(gameplay.location(out), gameplay.location(before))
                return out
            self.f.pulse('B', 90)
        self.fail(f'No capture return; text={text(self.f.state())!r}')

    def capture_and_reload(self, initial, buttons, species, level):
        before = self.walking_target(initial, buttons, species)
        wild = enemy(before)
        self.assertEqual(wild['level'], level)
        pid = before[offset(0x0203A734):offset(0x0203A734) + 4]
        self.throw_first_ball()
        caught = self.wait_caught(before)
        self.assertEqual(caught[gameplay.PARTY_COUNT], 2)
        self.assertEqual(gameplay.party_slot(caught, 0), gameplay.party_slot(before, 0))
        data = gameplay.party_slot(caught, 1)
        self.assertEqual(data[:4], pid)
        facts = mon_facts(data)
        self.assertTrue(facts['valid'])
        for key in ('species', 'level', 'iv', 'hp', 'max_hp'):
            self.assertEqual(facts[key], wild[key])
        self.assert_ball_metadata(data, 1)
        self.assertEqual(get(self.f, caught, 1), 0)
        self.f.restore(caught)  # get() is an isolated ABI observation
        saved_pref = preference.pref(caught)
        identity = gameplay.party_slot(caught, 0)
        flash = save_game(self.f)
        self.switch(self.rom)
        loaded = load_game(self.f, flash)
        self.assertFalse(in_battle(loaded))
        self.assertEqual(main_callback2(loaded), main_callback2(self.fixture))
        self.assertEqual(gameplay.location(loaded), gameplay.location(caught))
        self.assertEqual(loaded[gameplay.PARTY_COUNT], 2)
        self.assertEqual(gameplay.party_slot(loaded, 0), identity)
        self.assertEqual(gameplay.party_slot(loaded, 1), data)
        self.assertEqual(preference.pref(loaded), saved_pref)
        hidden = saved_pref[1] == hud.p.HIDDEN
        self.assertEqual(hud.has_hud(loaded), not hidden)
        if elapsed(initial) == clock.MAX:
            self.assertEqual(elapsed(loaded), clock.MAX)
            self.assertNotEqual(clock.progress(loaded), clock.progress(initial))
        else:
            self.assertGreater(elapsed(loaded), elapsed(initial))
        self.assertEqual(get(self.f, loaded, 1), 0)
        self.f.restore(loaded)
        position = gameplay.coords(loaded)
        self.f.run(16, buttons[0])
        self.assertNotEqual(gameplay.coords(self.f.state()), position)

    def audit_area(self, name):
        start, buttons = self.bootstrap(name)
        rows = [row for row in p.policy_rows() if row['map_symbol'] == name]
        day = self.record(name)[0] - 0x08000000
        slots = struct.unpack_from('<I', self.source, day + 4)[0] - 0x08000000
        cases = ((600, rows[0]['day_species'], rows[0]['slot'], False, False),
                 (1320, rows[0]['night_species'], rows[0]['slot'], True, False),
                 (1320, rows[1]['night_species'], rows[1]['slot'], False, True))
        for minute, species, slot, hidden, capped in cases:
            with self.subTest(map=name, species=species, hidden=hidden, capped=capped):
                level = self.source[slots + 4 * slot]
                self.assertEqual(level, self.source[slots + 4 * slot + 1])
                self.capture_and_reload(self.prepared(start, minute, hidden=hidden, capped=capped), buttons, species, level)

    def test_berry_forest_day_night_capture_and_cold_flash(self):
        self.audit_area(NEW_MAPS[0])

    def test_pattern_bush_day_night_capture_and_cold_flash(self):
        self.audit_area(NEW_MAPS[1])

    def test_sevault_entrance_day_night_capture_and_cold_flash(self):
        self.audit_area(NEW_MAPS[2])

    def test_sevault_canyon_day_night_capture_and_cold_flash(self):
        self.audit_area(NEW_MAPS[3])

    def test_live_dawn_dusk_before_natural_encounter_visible_and_hidden(self):
        start, buttons = self.bootstrap(NEW_MAPS[0])
        for hidden in (False, True):
            for minute, target, night in ((359, 858, False), (1199, 708, True)):
                with self.subTest(hidden=hidden, minute=minute):
                    initial = self.prepared(start, minute, hidden=hidden, capped=True)
                    self.f.restore(initial)
                    self.f.run(120)
                    crossed = self.f.state()
                    self.assertFalse(in_battle(crossed))
                    self.assertEqual((clock.progress(crossed) - clock.progress(initial)) % 86400, 120)
                    self.assertEqual(hud.has_hud(crossed), not hidden)
                    self.assertEqual(clock.record(crossed)[0], minute + 2)
                    before = self.walking_target(crossed, buttons, target)
                    current = clock.record(before)[0]
                    self.assertEqual(current < 360 or current >= 1200, night)
                    self.assertEqual(preference.pref(before), preference.pref(initial))

    def test_sevault_native_connection_roundtrip_day_night_and_flash(self):
        # Native ROM connections: east +20 from entrance; west -20 return.
        def connections(group, number):
            at = struct.unpack_from('<I', self.source, self.header(group, number) + 12)[0] - 0x08000000
            count, ptr = struct.unpack_from('<II', self.source, at)
            return [struct.unpack_from('<IiBBH', self.source, ptr - 0x08000000 + 12 * i)[:4] for i in range(count)]
        self.assertIn((4, 20, 3, 64), connections(3, 63))
        self.assertIn((3, -20, 3, 63), connections(3, 64))
        start, _ = self.bootstrap(NEW_MAPS[2], site=(22, 28, ('LEFT', 'RIGHT')))
        for minute, hidden in ((600, False), (1320, True)):
            with self.subTest(minute=minute, hidden=hidden):
                initial = self.prepared(start, minute, hidden=hidden)
                self.f.restore(initial)
                for button, destination in (('RIGHT', (3, 64)), ('LEFT', (3, 63))):
                    for _ in range(12):
                        self.f.run(8, button)
                        self.assertFalse(in_battle(self.f.state()))
                        if gameplay.location(self.f.state()) == destination:
                            break
                    self.f.run(40)
                    out = self.f.state()
                    self.assertEqual(gameplay.location(out), destination)
                    self.assertEqual(main_callback2(out), main_callback2(self.fixture))
                    self.assertEqual(gameplay.party_slot(out, 0), gameplay.party_slot(initial, 0))
                    self.assertEqual(out[gameplay.PARTY_COUNT], 1)
                    self.assertEqual(preference.pref(out), preference.pref(initial))
                    self.assertEqual(hud.has_hud(out), not hidden)
                flash = save_game(self.f)
                self.switch(self.rom)
                loaded = load_game(self.f, flash)
                self.assertEqual(gameplay.location(loaded), (3, 63))
                self.assertFalse(in_battle(loaded))
                self.assertEqual(preference.pref(loaded), preference.pref(initial))
                self.assertEqual(gameplay.party_slot(loaded, 0), gameplay.party_slot(initial, 0))
