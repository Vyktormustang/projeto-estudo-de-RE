"""Capture/persistence, escape and short map progression on exact v21.

Fresh synthetic game only. A single test ball and time are prepared before
walking; thereafter capture/escape/save use normal buttons. No test ROM warps.
Master Ball is a deterministic capture-path check, NOT a catch-rate experiment.
"""
import os
import struct
import unittest
from pathlib import Path
from mgba_treino_harness import Emulator, PARTY, offset, mon_facts, u32, decrypted, u16
from test_eventos_fixos_mgba import route_from_entry, enemy, OBJECTS, active_objects
from test_motor_v19_mgba import set_time
from test_estojo_expandido_mgba import add, get, save1
from test_golpes_gen9_integracao import save_game, load_game
from test_motor_v12_mgba import text
from battle_fixture_helpers import in_battle, main_callback2, BATTLE_OUTCOME
import test_motor_v21_mgba as encounters

ROM = os.environ.get('MOTOR_V21_ROM')
CORE = os.environ.get('MGBA_CORE')
PARTY_COUNT = offset(0x0203A731)


def location(state):
    at = offset(save1(state))
    return tuple(state[at + 4:at + 6])


def coords(state):
    return struct.unpack_from('<hh', state, offset(OBJECTS) + 16)


def party_slot(state, slot):
    start = offset(PARTY) + 100 * slot
    return state[start:start + 100]


@unittest.skipUnless(ROM and CORE, 'set MOTOR_V21_ROM and MGBA_CORE')
class MotorV21GameplayTests(unittest.TestCase):
    setUpClass = classmethod(encounters.prepare)
    tearDownClass = classmethod(encounters.finish)

    def walking_encounter(self, minute, species, *, ball_item=None):
        self.assertIn(ball_item, (None, 1, 4))
        prepared = add(self.f, self.fixture, ball_item, 1) if ball_item else self.fixture
        prepared = bytes(set_time(prepared, minute))
        self.assertEqual(prepared[PARTY_COUNT], 1)
        for delay in range(0, 180, 5):
            self.f.restore(prepared)
            self.f.run(delay)
            route_from_entry(self.f)
            for step in range(100):
                if in_battle(self.f.state()):
                    break
                self.f.run(4, 'LEFT' if step % 10 < 5 else 'RIGHT')
            if not in_battle(self.f.state()):
                continue
            self.f.run(300)
            state = self.f.state()
            if enemy(state)['species'] != species:
                continue
            for _ in range(6):
                self.f.pulse('B', 45)
            state = self.f.state()
            self.assertTrue(in_battle(state))
            self.assertEqual(u32(state, offset(0x02020374)) & 8, 0)
            self.assertEqual(location(state), (3, 19))
            self.assertIn('vai fazer?', text(state))
            self.assertTrue(enemy(state)['valid'])
            self.assertEqual(enemy(state)['level'], 3)
            return state
        self.fail(f'No natural encounter with species {species}')

    def wait_field(self, outcome):
        for _ in range(60):
            state = self.f.state()
            if not in_battle(state) and main_callback2(state) == main_callback2(self.fixture):
                self.assertEqual(state[offset(BATTLE_OUTCOME)], outcome)
                self.assertEqual(location(state), (3, 19))
                return state
            self.f.pulse('B', 90)
        self.fail(f'No field return for outcome {outcome}; text={text(self.f.state())!r}')

    def throw_first_ball(self):
        # Fight -> Bag -> Poké Balls -> first ball -> Use. Inventory was empty
        # before the ONE test ball was added in the field fixture.
        for key, gap in (('RIGHT', 40), ('A', 150), ('RIGHT', 80),
                         ('RIGHT', 80), ('A', 100), ('A', 400)):
            self.f.pulse(key, gap)

    def assert_ball_metadata(self, data, item):
        block, order, valid = decrypted(data)
        self.assertTrue(valid)
        # Native 12-byte Misc substructure: caught-ball is bits 11..14 of +2.
        self.assertEqual((u16(block, order[3] * 12 + 2) >> 11) & 15, item)

    def test_poke_ball_capture_consumption_and_native_ball_metadata(self):
        # Single deterministic ordinary-ball control, NOT a frequency estimate.
        before = self.walking_encounter(1320, 827, ball_item=4)
        wild = enemy(before)
        self.throw_first_ball()
        caught = self.wait_field(7)
        self.assertEqual(caught[PARTY_COUNT], 2)
        self.assertEqual(party_slot(caught, 0), party_slot(before, 0))
        data = party_slot(caught, 1)
        facts = mon_facts(data)
        self.assertTrue(facts['valid'])
        self.assertEqual(data[:4], before[offset(0x0203A734):offset(0x0203A734) + 4])
        for key in ('species', 'level', 'iv', 'hp', 'max_hp'):
            self.assertEqual(facts[key], wild[key])
        self.assertEqual(get(self.f, caught, 4), 0)
        self.assert_ball_metadata(data, 4)

    def test_capture_day_and_night_identity_ball_consumption_and_flash_reload(self):
        # Natural day control + both night substitutions, including Gen 8 ID.
        for minute, species in ((600, 240), (1320, 163), (1320, 827)):
            with self.subTest(minute=minute, species=species):
                before = self.walking_encounter(minute, species, ball_item=1)
                wild = enemy(before)
                pid = before[offset(0x0203A734):offset(0x0203A734) + 4]
                self.throw_first_ball()
                caught = self.wait_field(7)  # B_OUTCOME_CAUGHT, not text alone
                self.assertEqual(caught[PARTY_COUNT], 2)
                self.assertEqual(party_slot(caught, 0), party_slot(before, 0))
                data = party_slot(caught, 1)
                facts = mon_facts(data)
                self.assertTrue(facts['valid'])
                self.assertEqual(data[:4], pid)
                for key in ('species', 'level', 'iv', 'hp', 'max_hp'):
                    self.assertEqual(facts[key], wild[key])
                self.assertEqual(get(self.f, caught, 1), 0)
                self.assert_ball_metadata(data, 1)
                # get() is a separate native-call observation: restore the
                # recorded field state before pressing buttons to save.
                self.f.restore(caught)
                flash = save_game(self.f)
                self.assertEqual(len(flash), 131072)
                self.f.close()
                self.f = Emulator(self.rom, Path(CORE), Path(self.temp.name))
                type(self).f = self.f
                loaded = load_game(self.f, flash)  # NO savestate in fresh core
                self.assertFalse(in_battle(loaded))
                self.assertEqual(main_callback2(loaded), main_callback2(self.fixture))
                self.assertEqual(location(loaded), (3, 19))
                self.assertEqual(loaded[PARTY_COUNT], 2)
                self.assertEqual(party_slot(loaded, 1), data)
                self.assertEqual(get(self.f, loaded, 1), 0)

    def escape_live(self):
        # Canonicalize the native action cursor with buttons, not RAM writes.
        # No changes to HP/speed/RNG; if native escape fails, try again.
        for key in ('LEFT', 'UP', 'RIGHT', 'DOWN'):
            self.f.pulse(key, 35)
        for _ in range(12):
            self.f.pulse('A', 120)
            for _ in range(8):
                self.f.pulse('B', 45)
                if not in_battle(self.f.state()):
                    break
            if not in_battle(self.f.state()):
                break
        return self.wait_field(4)

    def test_night_escape_returns_control_without_adding_pokemon(self):
        before = self.walking_encounter(1320, 827)
        self.escape_live()
        out = self.wait_field(4)  # B_OUTCOME_RAN
        self.assertEqual(out[PARTY_COUNT], 1)
        self.assertEqual(party_slot(out, 1), party_slot(before, 1))
        self.assertTrue(mon_facts(party_slot(out, 0))['valid'])
        pos = coords(out)
        self.f.run(16, 'DOWN')
        self.assertFalse(in_battle(self.f.state()))
        self.assertNotEqual(coords(self.f.state()), pos)

    def test_natural_pallet_route1_roundtrip_day_and_night(self):
        # fixture itself plays intro/starter/rival by buttons. This explicitly
        # checks a short connection roundtrip, not the whole campaign.
        for minute in (600, 1320):
            with self.subTest(minute=minute):
                start = bytes(set_time(self.fixture, minute))
                self.assertEqual(location(start), (3, 0))
                self.f.restore(start)
                route_from_entry(self.f)
                # The outbound walk can also encounter a wild Pokemon (or
                # be in its fade-in before the native battle flag is set).
                self.f.run(400)
                if in_battle(self.f.state()):
                    for _ in range(6):self.f.pulse('B',45)
                    self.escape_live()
                # An encounter may stop the initial UP walk before its intended
                # tile. Finish the short approach so the NPC visibility check
                # doesn't assume an object outside the current camera window.
                for _ in range(32):
                    if coords(self.f.state())[1]<=39:break
                    self.f.run(16,'UP');self.f.run(120)
                    if in_battle(self.f.state()):
                        self.f.run(400)
                        for _ in range(6):self.f.pulse('B',45)
                        self.escape_live()
                self.f.run(120)
                route = self.f.state()
                self.assertFalse(in_battle(route))
                self.assertEqual(location(route), (3, 19))
                self.assertTrue(any(o[0] == 1 and o[3] != 0x98 for o in active_objects(route)))
                # Random encounters can interrupt the return journey. Handle
                # them through Run; absence of encounters is not an invariant.
                for _ in range(160):
                    self.f.run(8, 'DOWN')
                    state = self.f.state()
                    if in_battle(state):
                        self.f.run(400)
                        for _ in range(6):
                            self.f.pulse('B', 45)
                        self.escape_live()
                    if location(self.f.state()) == (3, 0):
                        break
                self.f.run(70)
                returned = self.f.state()
                self.assertFalse(in_battle(returned))
                self.assertEqual(location(returned), (3, 0))
                self.assertEqual(main_callback2(returned), main_callback2(start))
                self.assertEqual(returned[PARTY_COUNT], start[PARTY_COUNT])
                # Escaping may cost HP if a native attempt fails; it must not
                # grant EXP/change identity or add a party member.
                self.assertEqual(party_slot(returned, 0)[:80], party_slot(start, 0)[:80])
                self.assertTrue(mon_facts(party_slot(returned, 0))['valid'])
