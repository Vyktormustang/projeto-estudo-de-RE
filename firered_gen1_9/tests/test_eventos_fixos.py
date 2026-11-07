"""Testes sem distribuir ROM; integração extra se a cópia do usuário existir."""
from __future__ import annotations

import hashlib
import io
import csv
import os
import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from scripts import eventos_fixos as fixed
from scripts import encontros_selvagens as wild
from scripts import treino_ev

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "google_drive/ptbr_gen1-9_selvagens_treino.gba"


def synthetic_fixture():
    """Um grupo com dois mapas, NPC, clones simulados e quatro fixos."""
    rom = bytearray(0x1000)
    ptr = lambda p: fixed.ROM_START + p
    put = lambda at, v: struct.pack_into("<I", rom, at, v)
    # Ponteiros de grupo/headers e estruturas sem qualquer alias.
    group_table = 0x88
    put(group_table, ptr(0x80))
    for i, (header, layout, events, obj, count) in enumerate(
        ((0x100, 0x160, 0x200, 0x300, 4), (0x120, 0x180, 0x214, 0x380, 2))
    ):
        put(0x80 + 4 * i, ptr(header))
        put(header, ptr(layout)); put(header + 4, ptr(events))
        struct.pack_into("<II", rom, layout, 24, 40)
        rom[events] = count
        put(events + 4, ptr(obj))
    def event(at, local, species, x, y, script=fixed.GENERIC_SCRIPT, kind=0, gfx=0x98):
        rom[at:at + 3] = bytes((local, gfx, kind))
        struct.pack_into("<hh", rom, at + 4, x, y)
        rom[at + 8:at + 12] = bytes((3, 8, 0x11, 0))
        struct.pack_into("<HHIH", rom, at + 12, 0, species, script, 0x5000 + species)
    event(0x300, 1, 917, 17, 9)            # Tarountula, comum
    event(0x318, 2, 151, 10, 9)            # Mew, mítico
    event(0x330, 3, 793, 9, 9)             # Nihilego, Ultra Beast
    event(0x348, 4, 987, 8, 9)             # Flutter Mane, Paradox
    event(0x380, 1, 1, 3, 8)               # Bulbasaur, comum
    event(0x398, 2, 2, 4, 8, script=0x08000801, gfx=4)  # NPC não elegível
    maps = [fixed.MapRef(0, 0, "A"), fixed.MapRef(0, 1, "B")]
    def sp(i, name, legendary=False, mythical=False):
        return wild.Species(i, name, 1, (1,), 300, None, legendary, mythical)
    species = {1: sp(1, "bulbasaur"), 151: sp(151, "mew", mythical=True),
               793: sp(793, "nihilego"), 917: sp(917, "tarountula"),
               987: sp(987, "flutter-mane")}
    return bytes(rom), maps, group_table, species


class SyntheticFixedTests(unittest.TestCase):
    def setUp(self):
        self.rom, self.maps, self.group_table, self.species = synthetic_fixture()
        self.events, self.objects = fixed.parse_static_events(self.rom, self.maps, self.group_table)

    def plan(self):
        return fixed.plan_events(self.events, self.species, {1, 917})

    def test_inventario_reconhece_apenas_script_e_campos_esperados(self):
        self.assertEqual(self.objects, 6)
        self.assertEqual([e.species for e in self.events], [917, 151, 793, 987, 1])
        self.assertEqual(self.events[0].local_id, 1)
        fixed.audit_shared_script(self.rom, self.events)

    def test_protegidos_e_ambiguos_ficam_intactos(self):
        selected = self.plan()
        self.assertEqual({e.species for e in selected}, {1, 917})
        result = fixed.apply_plan(self.rom, selected)
        for event in self.events:
            current = result[event.offset:event.offset + fixed.OBJECT_SIZE]
            if event.species in {151, 793, 987}:
                self.assertEqual(current, event.original)
            else:
                self.assertEqual(struct.unpack_from("<hh", current, 4), (-1024, -1024))
                self.assertEqual(current[:4], event.original[:4])
                self.assertEqual(current[8:], event.original[8:])
        fixed.verify_output(self.rom, result, selected)

    def test_falha_se_comum_nao_tem_cobertura_selvagem(self):
        with self.assertRaisesRegex(fixed.PatchError, "selvagem"):
            fixed.plan_events(self.events, self.species, {1})

    def test_rejeita_duplicatas_e_especies_ausentes(self):
        with self.assertRaisesRegex(fixed.PatchError, "duplicado"):
            fixed.plan_events(self.events + self.events[:1], self.species, {1, 917})
        with self.assertRaisesRegex(fixed.PatchError, "ausente"):
            fixed.plan_events(self.events, {1: self.species[1]}, {1, 917})
        with self.assertRaisesRegex(fixed.PatchError, "duplicado"):
            fixed.apply_plan(self.rom, self.plan() * 2)

    def test_rejeita_objeto_de_origem_modificado_e_diferencas_extras(self):
        selected = self.plan()
        result = fixed.apply_plan(self.rom, selected)
        altered = bytearray(self.rom); altered[selected[0].offset + 8] ^= 1
        with self.assertRaisesRegex(fixed.PatchError, "origem"):
            fixed.apply_plan(bytes(altered), selected)
        for off in (0x30, selected[0].offset + 4, selected[0].offset + 16,
                    self.events[1].offset + 4):
            bad = bytearray(result); bad[off] ^= 1
            with self.subTest(off=off), self.assertRaises(fixed.PatchError):
                fixed.verify_output(self.rom, bytes(bad), selected)

    def test_rejeita_objeto_alvo_de_clone(self):
        selected = self.plan()
        fixed.reject_clone_targets(self.rom, self.maps, selected, self.group_table)
        bad = bytearray(self.rom)
        # O segundo objeto do mapa B passa a ser clone do objeto 1 do mapa A.
        at = 0x398
        bad[at + 2] = 0xff
        bad[at + 8] = 1  # target local ID
        struct.pack_into("<HH", bad, at + 12, 0, 0)  # mapa 0, grupo 0
        with self.assertRaisesRegex(fixed.PatchError, "clone"):
            fixed.reject_clone_targets(bytes(bad), self.maps, selected, self.group_table)

    def test_rejeita_campos_flag_coordenada_ordem_e_ponteiro_estranhos(self):
        examples = [(0x300 + 20, b"\x00\x00"),
                    (0x300 + 4, struct.pack("<h", -1)),
                    (0x300, b"\x05"), (0x100 + 4, b"\xff\xff\xff\xff")]
        for off, value in examples:
            bad = bytearray(self.rom); bad[off:off+len(value)] = value
            with self.subTest(off=off), self.assertRaises(fixed.PatchError):
                fixed.parse_static_events(bytes(bad), self.maps, self.group_table)

    def test_rejeita_arrays_compartilhados_e_referencias_externas(self):
        bad = bytearray(self.rom)
        struct.pack_into("<I", bad, 0x214 + 4, fixed.ROM_START + 0x300)
        # Primeiro a ordem de IDs também pode detectar o alias, de todo modo deve falhar.
        with self.assertRaises(fixed.PatchError):
            fixed.parse_static_events(bytes(bad), self.maps, self.group_table)
        bad = bytearray(self.rom)
        struct.pack_into("<I", bad, 0x500, fixed.GENERIC_SCRIPT)
        with self.assertRaisesRegex(fixed.PatchError, "referências"):
            fixed.audit_shared_script(bytes(bad), self.events)

    def test_falha_em_catalogo_ou_hash_incompativel(self):
        with self.assertRaises(fixed.PatchError):
            fixed.validate_source(self.rom)
        with tempfile.TemporaryDirectory() as td:
            catalog = Path(td) / "alterado.csv"; catalog.write_bytes(b"errado")
            with mock.patch.object(fixed, "CATALOG_HASHES", {catalog: "0" * 64}):
                with self.assertRaisesRegex(fixed.PatchError, "Catálogo"):
                    fixed.checked_catalogs()

    def test_saida_nunca_sobrescreve_entrada_ou_links(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td); src = d / "src.gba"; dst = d / "out.gba"
            src.write_bytes(b"src")
            treino_ev.write_new_file(src, dst, b"out")
            self.assertEqual(src.read_bytes(), b"src")
            self.assertEqual(dst.read_bytes(), b"out")
            hard = d / "hard.gba"; os.link(src, hard)
            sym = d / "sym.gba"; sym.symlink_to(src)
            dangling = d / "dangling.gba"; dangling.symlink_to(d / "missing")
            for target in (src, dst, hard, sym, dangling):
                with self.subTest(target=target), self.assertRaises(treino_ev.PatchError):
                    treino_ev.write_new_file(src, target, b"bad")
            self.assertEqual(src.read_bytes(), b"src")

    def test_erro_da_rom_nao_cria_saida(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td)/"src.gba", Path(td)/"out.gba"
            src.write_bytes(b"incompativel")
            self.assertEqual(fixed.main(["--rom", str(src), "--saida", str(out)]), 1)
            self.assertFalse(out.exists())


@unittest.skipUnless(SOURCE.exists(), "ROM com treino não está no workspace")
class RealRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = SOURCE.read_bytes()
        if fixed.digest(cls.rom) != fixed.BASE_SHA256:
            raise ValueError("A ROM local não é a versão esperada; não altere sua ROM.")
        cls.out, cls.events, cls.selected, cls.species, cls.tables = fixed.prepare(cls.rom)

    def test_hashes_contagens_e_areas_autorizadas(self):
        self.assertEqual(fixed.digest(self.out), fixed.OUTPUT_SHA256)
        self.assertEqual((len(self.events), len(self.selected)), (334, 224))
        allowed = {e.offset + i for e in self.selected for i in range(4, 8)}
        changed = {i for i, (a, b) in enumerate(zip(self.rom, self.out)) if a != b}
        self.assertEqual(changed, allowed)
        self.assertEqual(len(changed), 896)
        fixed.verify_output(self.rom, self.out, self.selected)

    def test_fixos_especiais_npc_clones_eventos_historia_e_treino_preservados(self):
        selected = {e.offset for e in self.selected}
        counts = {"lendario/mitico": 0, "ultra beast": 0, "paradox": 0}
        for e in self.events:
            cat = fixed.category(self.species[e.species])
            if cat != "comum":
                counts[cat] += 1
                self.assertNotIn(e.offset, selected)
                self.assertEqual(self.rom[e.offset:e.offset+fixed.OBJECT_SIZE],
                                 self.out[e.offset:e.offset+fixed.OBJECT_SIZE])
        self.assertEqual(counts, {"lendario/mitico": 81, "ultra beast": 9, "paradox": 20})
        self.assertEqual(self.rom[treino_ev.HOOK_OFFSET:treino_ev.HOOK_OFFSET+8],
                         self.out[treino_ev.HOOK_OFFSET:treino_ev.HOOK_OFFSET+8])
        self.assertEqual(self.rom[treino_ev.PAYLOAD_OFFSET:treino_ev.PAYLOAD_OFFSET+treino_ev.PAYLOAD_SPACE],
                         self.out[treino_ev.PAYLOAD_OFFSET:treino_ev.PAYLOAD_OFFSET+treino_ev.PAYLOAD_SPACE])
        # Nenhum código/script de batalha/história foi mudado.
        self.assertEqual(self.rom[:0x7B0000], self.out[:0x7B0000])

    def test_especies_retiradas_ainda_estao_nas_tabelas_selvagens(self):
        maps = wild.load_maps()
        after = wild.parse_tables(self.out, maps, self.species)
        self.assertEqual(self.tables, after)
        self.assertTrue({e.species for e in self.selected} <= wild.covered_species(after))
        tar = next(e for e in self.selected if e.species == 917)
        self.assertEqual((tar.map.label, tar.local_id, tar.x, tar.y), ("Route1", 6, 17, 9))
        self.assertEqual(self.out[tar.offset+4:tar.offset+8], struct.pack("<hh", -1024, -1024))

    def test_inventario_exportado_e_deterministico(self):
        generated = fixed.inventory_csv(self.events, self.selected, self.species, self.tables)
        self.assertEqual(generated, (ROOT / "docs/eventos_fixos_inventario.csv").read_text(encoding="utf-8"))
        rows = list(csv.DictReader(io.StringIO(generated)))
        self.assertEqual(len(rows), 334)
        self.assertEqual(sum(r["situacao_fixo"] == "retirado do mapa" for r in rows), 224)
        row = next(r for r in rows if r["pokemon"] == "tarountula")
        self.assertEqual((row["mapa_selvagem"], row["metodo"], row["chance_por_encontro_pct"]),
                         ("Mt Ember Exterior", "grama/caverna", "1"))
        for row in rows:
            if row["situacao_fixo"] == "retirado do mapa":
                self.assertTrue(row["mapa_selvagem"], row)


if __name__ == "__main__":
    unittest.main()
