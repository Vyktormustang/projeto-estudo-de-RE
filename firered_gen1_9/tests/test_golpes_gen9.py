"""Testes estruturais do patch de golpes, sem precisar distribuir uma ROM."""
from __future__ import annotations
import csv
import hashlib
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import golpes_gen9 as patch
from scripts import gerar_catalogo_golpes as catalog
from scripts import encontros_selvagens as wild
from scripts import eventos_fixos as fixed
from scripts import treino_ev

ROOT = Path(__file__).resolve().parents[1]
ROM = Path(os.environ.get("GOLPES_TEST_BASE", ROOT / "google_drive/ptbr_gen1-9_selvagens_treino_sem_fixos_comuns.gba"))

class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.CATALOG.open(newline="", encoding="utf-8") as f:
            cls.rows = list(csv.DictReader(f))
        with (ROOT / "docs/golpes_por_nivel_nao_incluidos.csv").open(newline="", encoding="utf-8") as f:
            cls.omitted = list(csv.DictReader(f))

    def test_integridade_e_cobertura(self):
        self.assertEqual(patch.digest(patch.CATALOG.read_bytes()), patch.CATALOG_SHA256)
        self.assertEqual(patch.digest(patch.PAYLOAD.read_bytes()), patch.PAYLOAD_SHA256)
        self.assertEqual(len(self.rows), 14018)
        self.assertEqual({int(r["species"]) for r in self.rows}, set(range(1, 1026)))
        self.assertEqual(len(self.omitted), 1011)
        self.assertEqual({r["reason"] for r in self.omitted},
                         {"efeito_nao_implementado", "poder_dinamico_nao_implementado"})

    def test_charizard_tarountula_e_golpes_acima_de_511(self):
        def m(s, l):
            return {(int(r["internal_move"]), r["name"]) for r in self.rows
                    if int(r["species"]) == s and int(r["level"]) == l}
        self.assertIn((394, "Flare Blitz"), m(6, 62))
        self.assertIn((516, "Inferno"), m(6, 54))
        self.assertIn((403, "Air Slash"), m(6, 0))
        self.assertIn((518, "Struggle Bug"), m(917, 5))
        self.assertNotIn((6, "Pay Day"), m(917, 5))
        self.assertTrue(any(int(r["internal_move"]) > 511 for r in self.rows))
        self.assertTrue(any(r["name"] == "Heat Crash" and r["species"] == "500" for r in self.omitted))
        self.assertTrue(any(r["species"] == "739" and r["name"] == "Bubble" and r["fallback"] == "inicial"
                            for r in self.rows))

    def test_tabela_3_bytes_suporta_niveis_100_e_ids_altos(self):
        lists = {sid: [(1, 33)] for sid in range(1, 1026)}
        lists[6] = [(0, 403), (54, 516), (62, 394), (100, 796)]
        table = patch.build_tables(lists)
        ptr = struct.unpack_from("<I", table, 4 * 6)[0] - patch.ROM_START - patch.TABLE
        a = [struct.unpack_from("<HB", table, ptr + 3 * i) for i in range(5)]
        self.assertEqual(a, [(403, 0), (516, 54), (394, 62), (796, 100), (65535, 255)])
        empty = struct.unpack_from("<I", table, 0)[0] - patch.ROM_START - patch.TABLE
        self.assertEqual(table[empty:empty + 3], patch.TERMINATOR)
        self.assertLess(patch.TABLE + len(table), patch.FREE_END)

    def test_hooks_alinhados_separados_e_vetores_validos(self):
        payload = patch.PAYLOAD.read_bytes()
        self.assertEqual(len(patch.HOOKS), 11)
        self.assertEqual(len({pos for pos, *_ in patch.HOOKS}), len(patch.HOOKS))
        for pos, old, dest, reg in patch.HOOKS:
            self.assertEqual(pos % 4, 0)
            self.assertEqual(len(bytes.fromhex(old)), 8)
            self.assertEqual(len(patch.hook(dest, reg)), 8)
            opcode = b"\x00\x4b\x18\x47" if reg == 3 else b"\x00\x4a\x10\x47"
            self.assertEqual(payload[dest:dest+4], opcode)
            pointer = struct.unpack_from("<I", payload, dest + 4)[0]
            self.assertTrue((pointer & 1) and patch.ROM_START + patch.CODE <= pointer < patch.ROM_START + patch.CODE_END)

    def test_recusa_rom_payload_catalogo_invalidos(self):
        with self.assertRaises(patch.PatchError):
            patch.validate_inputs(b"wrong", patch.PAYLOAD.read_bytes(), patch.CATALOG.read_bytes())
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "orig.gba", Path(td) / "new.gba"
            src.write_bytes(b"invalida")
            self.assertEqual(patch.main(["--rom", str(src), "--saida", str(out)]), 1)
            self.assertEqual(src.read_bytes(), b"invalida")
            self.assertFalse(out.exists())
            out.write_bytes(b"salvo")
            self.assertEqual(patch.main(["--rom", str(src), "--saida", str(out)]), 1)
            self.assertEqual(out.read_bytes(), b"salvo")

@unittest.skipUnless(ROM.exists(), "ROM privada de entrada não fornecida")
class RealRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ROM.read_bytes()
        if patch.digest(cls.source) != patch.BASE_SHA256:
            raise ValueError("ROM diferente da versão identificada")
        cls.payload = patch.PAYLOAD.read_bytes()
        cls.csv = patch.CATALOG.read_bytes()
        cls.plan = patch.make_plan(cls.source, cls.payload, cls.csv)
        cls.output = patch.apply_patch(cls.source, cls.payload, cls.csv)

    def test_saidas_sao_exclusivamente_areas_aprovadas(self):
        patch.verify_output(self.source, self.output, self.plan)
        for pos in (0x1222E0, 0xF81000, 0x8493E8, 0x7C2010, 0x6BB728):
            self.assertEqual(self.source[pos:pos + 32], self.output[pos:pos + 32])
        altered = bytearray(self.output); altered[0x100000] ^= 1
        with self.assertRaises(patch.PatchError):
            patch.verify_output(self.source, bytes(altered), self.plan)

    def test_dados_de_batalha_permanecem_inalterados(self):
        # Atualizar as listas não autoriza mudanças globais de poder ou efeitos.
        lo = catalog.MOVE_DATA
        hi = lo + catalog.NAMES_COUNT * catalog.MOVE_STRIDE
        self.assertEqual(self.output[lo:hi], self.source[lo:hi])
        for mid in (394, 403, 424, 516, 518):
            at = lo + mid * catalog.MOVE_STRIDE
            self.assertEqual(self.output[at:at + catalog.MOVE_STRIDE],
                             self.source[at:at + catalog.MOVE_STRIDE])

    def test_encontros_objetos_e_treino_permanecem_inalterados(self):
        species, wild_maps = wild.load_species(), wild.load_maps()
        before = wild.parse_tables(self.source, wild_maps, species)
        after = wild.parse_tables(self.output, wild_maps, species)
        self.assertEqual(before, after)
        required = {sid for sid, info in species.items() if not info.protected}
        self.assertEqual(len(required), 931)
        self.assertTrue(required <= wild.covered_species(after))
        self.assertEqual(self.source[treino_ev.HOOK_OFFSET:treino_ev.HOOK_OFFSET + len(treino_ev.HOOK)],
                         self.output[treino_ev.HOOK_OFFSET:treino_ev.HOOK_OFFSET + len(treino_ev.HOOK)])
        start, end = treino_ev.PAYLOAD_OFFSET, treino_ev.PAYLOAD_OFFSET + treino_ev.PAYLOAD_SPACE
        self.assertEqual(self.source[start:end], self.output[start:end])
        # Todos os 1.982 modelos de objetos, inclusive os 224 estacionados fora
        # do mapa e os 110 especiais, permanecem byte a byte iguais à entrada.
        count = 0
        for m in fixed.load_map_catalog():
            array = fixed._ptr(self.source, fixed.GROUP_TABLE + 4 * m.group, 4 * (m.number + 1))
            header = fixed._ptr(self.source, array + 4 * m.number, 28)
            events = fixed._ptr(self.source, header + 4, 20)
            n = self.source[events]
            self.assertEqual(self.output[events:events + 20], self.source[events:events + 20])
            if n:
                objects = fixed._ptr(self.source, events + 4, n * fixed.OBJECT_SIZE)
                end = objects + n * fixed.OBJECT_SIZE
                self.assertEqual(self.source[objects:end], self.output[objects:end])
            count += n
        self.assertEqual(count, 1982)

    def test_todas_as_listas_do_rom_equivalem_ao_catalogo(self):
        lists = patch.read_catalog(self.csv, self.source)
        for sid in range(1, 1026):
            off = struct.unpack_from("<I", self.output, patch.TABLE + 4 * sid)[0] - patch.ROM_START
            data = []
            for _ in range(51):
                move, level = struct.unpack_from("<HB", self.output, off)
                off += 3
                if move == 0xffff: break
                data.append((level, move))
            else: self.fail(f"Lista {sid} sem terminador")
            self.assertEqual(data, lists[sid])

    def test_bloqueia_payload_catalogo_e_hook_alterados(self):
        with self.assertRaises(patch.PatchError):
            patch.make_plan(self.source, self.payload + b"x", self.csv)
        with self.assertRaises(patch.PatchError):
            patch.make_plan(self.source, self.payload, self.csv + b"x")
        altered = bytearray(self.source); altered[patch.HOOKS[0][0]] ^= 1
        with mock.patch.object(patch, "BASE_SHA256", patch.digest(altered)):
            with self.assertRaises(patch.PatchError):
                patch.make_plan(bytes(altered), self.payload, self.csv)

if __name__ == "__main__":
    unittest.main()
