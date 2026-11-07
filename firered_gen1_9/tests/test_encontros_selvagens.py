"""Testes sem ROM distribuída: estruturas sintéticas e, quando disponível, a base local."""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import os
import struct
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import encontros_selvagens as wild  # noqa: E402

HEADERS = 0x100
SOURCE_PATH = ROOT / "google_drive/pokefirered_gen1-9_ptbr.gba"
EXPECTED_OUTPUT_SHA = "3f8cc9e3a52b1bad8a2f22df9a302f79a355e929669c5425ef023017bd4c4e49"


def synthetic_fixture():
    """ROM fictícia: quatro métodos, um mapa excluído e uma câmara Tanoby."""
    species = {
        1: wild.Species(1, "alpha", 1, (1,), 200, None, False, False),
        2: wild.Species(2, "aqua", 1, (11,), 200, None, False, False),
        3: wild.Species(3, "missing-land", 1, (1,), 200, None, False, False),
        4: wild.Species(4, "missing-water", 1, (11,), 200, None, False, False),
        5: wild.Species(5, "legend", 1, (1,), 580, None, True, False),
        6: wild.Species(6, "mythical", 1, (11,), 600, None, False, True),
        7: wild.Species(7, "beta", 1, (1,), 200, None, False, False),
        8: wild.Species(8, "outside-only", 1, (1,), 200, None, False, False),
        9: wild.Species(9, "absent-legend", 1, (1,), 600, None, True, False),
        201: wild.Species(201, "unown", 2, (14,), 336, None, False, False),
    }
    maps = [
        wild.MapSpec(0, 3, 1, "MAP_ROUTE_TEST", "RouteTest", (True, True, True, True)),
        wild.MapSpec(1, 3, 2, "MAP_ROUTE21_SOUTH", "Route21_South", (True, False, False, False)),
        wild.MapSpec(2, 3, 3, "MAP_TANOBY_RUINS_MONEAN_CHAMBER", "MoneanChamber", (True, False, False, False)),
    ]
    rom = bytearray(0x1000)
    for i, m in enumerate(maps):
        struct.pack_into("<BBxx", rom, HEADERS + 20 * i, m.group, m.number)
    rom[HEADERS + 20 * len(maps):HEADERS + 20 * len(maps) + 2] = b"\xff\xff"

    def add(map_i, kind, info, data, ids):
        k = list(wild.SLOTS).index(kind)
        struct.pack_into("<I", rom, HEADERS + map_i * 20 + 4 + k * 4, wild.ROM_START + info)
        rom[info] = 20
        struct.pack_into("<I", rom, info + 4, wild.ROM_START + data)
        assert len(ids) == wild.SLOTS[kind]
        for i, mon in enumerate(ids):
            struct.pack_into("<BBH", rom, data + 4 * i, 3, 5, mon)

    add(0, "land", 0x300, 0x500, [1, 1, 7, 7, 5, 1, 1, 1, 1, 1, 1, 1])
    add(0, "water", 0x320, 0x540, [2, 2, 2, 6, 2])
    add(0, "rock", 0x340, 0x560, [1, 7, 1, 1, 1])
    add(0, "fish", 0x360, 0x580, [1] * 10)
    add(1, "land", 0x380, 0x600, [8] * 12)
    add(2, "land", 0x3A0, 0x640, [201] * 12)
    return bytes(rom), maps, species


class SyntheticPatchTests(unittest.TestCase):
    def setUp(self):
        self.rom, self.maps, self.species = synthetic_fixture()
        self.before = wild.parse_tables(self.rom, self.maps, self.species, HEADERS)

    def build(self):
        return wild.make_patch(self.rom, self.maps, self.species, HEADERS)

    def test_parse_and_slot_probabilities(self):
        self.assertEqual(len(self.before), 6)
        self.assertEqual([len(t.slots) for t in self.before], [12, 5, 5, 10, 12, 12])
        self.assertEqual(sum(s.chance for s in self.before[0].slots), 100)
        self.assertEqual(sum(s.chance for s in self.before[1].slots), 100)
        self.assertEqual([sum(s.chance for s in self.before[3].slots[a:b])
                          for a, b in ((0, 2), (2, 5), (5, 10))], [100, 100, 100])
        self.assertEqual(self.before[0].encounter_rate, 20)

    def test_coverage_and_no_new_legendaries(self):
        output, after, changes, _ = self.build()
        self.assertEqual({c.new_species for c in changes}, {3, 4, 8})
        self.assertEqual({c.new_species for c in changes if c.table.kind == "water"}, {4})
        self.assertTrue({1, 2, 3, 4, 7, 8, 201} <= wild.covered_species(after))
        self.assertNotIn(9, {s.species for t in after for s in t.slots})
        self.assertEqual(len(output), len(self.rom))

    def test_unchanged_original_species_and_excluded_methods(self):
        output, after, changes, _ = self.build()
        self.assertTrue(wild.covered_species(self.before) <= wild.covered_species(after))
        self.assertTrue(all(c.table.map.eligible and c.table.kind in {"land", "water"} for c in changes))
        for old, new in zip(self.before, after):
            if not old.map.eligible or old.kind in {"rock", "fish"}:
                self.assertEqual(old.slots, new.slots)
            for a, b in zip(old.slots, new.slots):
                if self.species[a.species].protected or a.species == wild.UNOWN:
                    self.assertEqual(a, b)
                self.assertEqual((a.min_level, a.max_level, a.chance),
                                 (b.min_level, b.max_level, b.chance))
        allowed = {c.slot.offset + n for c in changes for n in (2, 3)}
        actual = {i for i, (a, b) in enumerate(zip(self.rom, output)) if a != b}
        self.assertTrue(actual)
        self.assertTrue(actual <= allowed)

    def test_deterministic_output_and_guide(self):
        result1, result2 = self.build(), self.build()
        self.assertEqual(result1[0], result2[0])
        self.assertEqual(result1[2], result2[2])
        self.assertEqual(result1[3], result2[3])
        rows = list(csv.DictReader(io.StringIO(result1[3])))
        self.assertEqual({int(r["pokedex_nacional"]) for r in rows}, {1, 2, 3, 4, 7, 8, 201})
        by_id = {int(r["pokedex_nacional"]): r for r in rows}
        self.assertEqual(by_id[4]["metodo"], "surf")
        self.assertEqual(by_id[201]["simbolo_mapa"], self.maps[2].symbol)
        self.assertEqual(by_id[8]["situacao"], "adicionado")
        self.assertEqual(by_id[1]["situacao"], "ja existente")
        self.assertEqual(by_id[1]["chance_por_encontro_pct"], "50")

    def test_no_tanoby_unown_fails_closed(self):
        rom = bytearray(self.rom)
        for i in range(12):
            struct.pack_into("<H", rom, 0x640 + 4 * i + 2, 1)
        tables = wild.parse_tables(bytes(rom), self.maps, self.species, HEADERS)
        with self.assertRaisesRegex(wild.PatchError, "Unown"):
            wild.plan_changes(tables, self.species)

    def test_no_safe_slot_fails_closed(self):
        species = dict(self.species)
        species[3] = replace(species[3], base_stat_total=600)
        with self.assertRaisesRegex(wild.PatchError, "Não há slot"):
            wild.make_patch(self.rom, self.maps, species, HEADERS)

    def test_protected_or_duplicate_plan_rejected(self):
        land = self.before[0]
        legend = next(s for s in land.slots if s.species == 5)
        common = next(s for s in land.slots if s.species == 1)
        excluded = self.before[4]
        tanoby = self.before[5]
        forbidden = [
            [wild.Change(land, legend, 3)],
            [wild.Change(land, common, 5)],
            [wild.Change(land, common, 201)],
            [wild.Change(excluded, excluded.slots[0], 3)],
            [wild.Change(tanoby, tanoby.slots[0], 3)],
            [wild.Change(land, common, 3), wild.Change(land, common, 8)],
            [wild.Change(self.before[2], self.before[2].slots[0], 3)],
            [wild.Change(self.before[3], self.before[3].slots[0], 3)],
        ]
        for plan in forbidden:
            with self.subTest(plan=plan), self.assertRaises(wild.PatchError):
                wild.apply_changes(self.rom, plan, self.species)

    def test_changed_origin_slot_rejected(self):
        land = self.before[0]
        slot = land.slots[1]
        rom = bytearray(self.rom)
        rom[slot.offset] += 1
        with self.assertRaisesRegex(wild.PatchError, "origem"):
            wild.apply_changes(bytes(rom), [wild.Change(land, slot, 3)], self.species)

    def test_verifier_rejects_lost_or_modified_species(self):
        output, _, changes, _ = self.build()
        bad = bytearray(output)
        legendary = next(s for s in self.before[0].slots if s.species == 5)
        struct.pack_into("<H", bad, legendary.offset + 2, 1)
        with self.assertRaises(wild.PatchError):
            wild.verify_result(self.rom, bytes(bad), self.before, self.maps, self.species, changes, HEADERS)
        bad = bytearray(output)
        struct.pack_into("<H", bad, changes[0].slot.offset + 2, 1)
        with self.assertRaises(wild.PatchError):
            wild.verify_result(self.rom, bytes(bad), self.before, self.maps, self.species, changes, HEADERS)

    def test_verifier_rejects_changed_level(self):
        output, _, changes, _ = self.build()
        bad = bytearray(output)
        bad[changes[0].slot.offset] += 1
        with self.assertRaisesRegex(wild.PatchError, "Níveis"):
            wild.verify_result(self.rom, bytes(bad), self.before, self.maps, self.species, changes, HEADERS)

    def test_out_of_bounds_and_unaligned_pointers(self):
        for addr in (wild.ROM_START - 4, wild.ROM_START + len(self.rom), wild.ROM_START + 0x301):
            rom = bytearray(self.rom)
            struct.pack_into("<I", rom, HEADERS + 4, addr)
            with self.subTest(addr=addr), self.assertRaisesRegex(wild.PatchError, "Ponteiro"):
                wild.parse_tables(bytes(rom), self.maps, self.species, HEADERS)
        with self.assertRaisesRegex(wild.PatchError, "cabeçalhos"):
            wild.parse_tables(self.rom, self.maps, self.species, len(self.rom) - 4)

    def test_alias_and_partial_overlap_rejected(self):
        rom = bytearray(self.rom)
        struct.pack_into("<I", rom, HEADERS + 8, wild.ROM_START + 0x300)
        with self.assertRaisesRegex(wild.PatchError, "compartilhado"):
            wild.parse_tables(bytes(rom), self.maps, self.species, HEADERS)
        rom = bytearray(self.rom)
        struct.pack_into("<I", rom, 0x320 + 4, wild.ROM_START + 0x504)
        with self.assertRaisesRegex(wild.PatchError, "sobrepostas"):
            wild.parse_tables(bytes(rom), self.maps, self.species, HEADERS)

    def test_corrupt_sentinel_map_and_slots_rejected(self):
        mutations = [
            (HEADERS + 20 * len(self.maps), b"\x00"),  # sentinel
            (HEADERS, b"\x7f"),                         # map ID
            (0x500, b"\x00"),                            # minimum level
            (0x502, b"\xff\x03"),                       # unknown species
        ]
        for offset, value in mutations:
            rom = bytearray(self.rom)
            rom[offset:offset + len(value)] = value
            with self.subTest(offset=offset), self.assertRaises(wild.PatchError):
                wild.parse_tables(bytes(rom), self.maps, self.species, HEADERS)

    def test_hash_mismatch_rejected(self):
        with self.assertRaisesRegex(wild.PatchError, "SHA-256"):
            wild.validate_source(self.rom)


class OutputSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.d = Path(self.temp.name)
        self.source = self.d / "source.gba"
        self.source.write_bytes(b"original protected")
        self.output = self.d / "out.gba"
        self.guide = self.d / "guide.csv"

    def run_cli(self, *args):
        with contextlib.redirect_stderr(io.StringIO()):
            return wild.main(list(args))

    def test_force_cannot_overwrite_input_or_use_symlink(self):
        symlink = self.d / "link.gba"
        symlink.symlink_to(self.source)
        for path in (self.source, symlink):
            for field in ("--saida", "--guia"):
                output = path if field == "--saida" else self.output
                guide = path if field == "--guia" else self.guide
                with self.subTest(path=path, field=field):
                    rc = self.run_cli("--rom", str(self.source), "--saida", str(output),
                                      "--guia", str(guide), "--force")
                    self.assertEqual(rc, 1)
                    self.assertEqual(self.source.read_bytes(), b"original protected")

    def test_force_cannot_overwrite_input_via_hardlink(self):
        link = self.d / "hardlink.gba"
        os.link(self.source, link)
        rc = self.run_cli("--rom", str(self.source), "--saida", str(link),
                          "--guia", str(self.guide), "--force")
        self.assertEqual(rc, 1)
        self.assertEqual(self.source.read_bytes(), b"original protected")

    def test_force_rejects_hardlinked_outputs(self):
        self.output.write_bytes(b"keep both")
        os.link(self.output, self.guide)
        rc = self.run_cli("--rom", str(self.source), "--saida", str(self.output),
                          "--guia", str(self.guide), "--force")
        self.assertEqual(rc, 1)
        self.assertEqual(self.output.read_bytes(), b"keep both")
        self.assertEqual(self.guide.read_bytes(), b"keep both")

    def test_existing_output_is_not_overwritten_without_force(self):
        self.output.write_bytes(b"already here")
        rc = self.run_cli("--rom", str(self.source), "--saida", str(self.output), "--guia", str(self.guide))
        self.assertEqual(rc, 1)
        self.assertEqual(self.output.read_bytes(), b"already here")
        self.assertFalse(self.guide.exists())

    def test_self_test_fails_when_no_tests_found(self):
        with mock.patch.object(unittest.defaultTestLoader, "discover", return_value=unittest.TestSuite()):
            self.assertEqual(self.run_cli("--self-test"), 1)


@unittest.skipUnless(SOURCE_PATH.is_file(), "ROM base privada não está disponível neste checkout")
class LocalSourceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = SOURCE_PATH.read_bytes()
        wild.validate_source(cls.rom)
        cls.species, cls.maps = wild.load_species(), wild.load_maps()
        cls.before = wild.parse_tables(cls.rom, cls.maps, cls.species)
        cls.output, cls.after, cls.changes, cls.guide = wild.make_patch(cls.rom, cls.maps, cls.species)

    def test_expected_sha_and_reproducibility(self):
        self.assertEqual(hashlib.sha256(self.output).hexdigest(), EXPECTED_OUTPUT_SHA)
        self.assertEqual(len(self.changes), 730)
        self.assertEqual(len(self.after), 227)
        self.assertEqual(hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(), wild.BASE_SHA256)

    def test_coverage_and_original_legendary_slots(self):
        expected = {s.id for s in self.species.values() if not s.protected}
        self.assertEqual(len(expected), 931)
        self.assertTrue(expected <= wild.covered_species(self.after))
        self.assertEqual(len(list(csv.DictReader(io.StringIO(self.guide)))), 931)
        for old, new in zip(self.before, self.after):
            for a, b in zip(old.slots, new.slots):
                if self.species[a.species].protected or a.species == wild.UNOWN:
                    self.assertEqual(a, b)
                if old.kind in {"rock", "fish"} or not old.map.eligible:
                    self.assertEqual(a, b)

    def test_actual_diff_is_confined_to_species_fields(self):
        allowed = {c.slot.offset + n for c in self.changes for n in (2, 3)}
        changed = {i for i, (a, b) in enumerate(zip(self.rom, self.output)) if a != b}
        self.assertTrue(changed)
        self.assertLessEqual(changed, allowed)


if __name__ == "__main__":
    unittest.main()
