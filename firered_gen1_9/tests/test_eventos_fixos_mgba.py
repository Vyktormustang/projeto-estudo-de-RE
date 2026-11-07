"""Integração opcional mGBA 0.10.5, somente saves e ROMs temporários.

FIXOS_TEST_BASE=google_drive/ptbr_gen1-9_selvagens_treino.gba \
FIXOS_TEST_ROM=rom_mod/ptbr_gen1-9_selvagens_treino_sem_fixos_comuns.gba \
MGBA_CORE=/caminho/mgba_libretro.so python3 -m unittest discover -s tests \
    -p 'test_eventos_fixos_mgba.py' -v

Para visitar pontos distantes, uma *cópia temporária* de cada ROM recebe um
script de warp no letreiro da Rota 1. Essa instrumentação nunca é entregue nem
altera a ROM testada. Também há testes de transição natural sem instrumentação.
"""
from __future__ import annotations

import ctypes as C
import hashlib
import os
import struct
import tempfile
import unittest
from pathlib import Path

from mgba_treino_harness import Emulator, make_summary_fixture, mon, mon_facts, offset
from scripts import eventos_fixos as fixed, atualizacoes_gen9 as updates, complemento_gen9 as complement

BASE = os.environ.get("FIXOS_TEST_BASE")
ROM = os.environ.get("FIXOS_TEST_ROM")
CORE = os.environ.get("MGBA_CORE")
OBJECTS = 0x02021B24
ENEMY = 0x0203A734


def one_frame(f):
    # O fixture original foi obtido com uma captura neste ponto.
    f.run(1)


def direction(f, button, frames, gap=70):
    f.run(frames, button)
    f.run(gap)
    one_frame(f)


def route_entry_fixture(f):
    """Início real: escolhe inicial, sai do laboratório e chega a Pallet norte."""
    make_summary_fixture(f)
    one_frame(f)
    for _ in range(3):
        f.pulse("B", 90)
        one_frame(f)
    f.pulse("B", 40)
    one_frame(f)
    for button, frames in (("DOWN", 50), ("LEFT", 32), ("DOWN", 72), ("DOWN", 32)):
        direction(f, button, frames, 25)
    # Batalha obrigatória contra o rival; só botões normais, sem editar RAM.
    for _ in range(12):
        for _ in range(15):
            f.pulse("A", 50)
        one_frame(f)
    for button, frames in (("DOWN", 80), ("LEFT", 45), ("DOWN", 24),
                           ("LEFT", 48), ("UP", 60), ("UP", 140),
                           ("LEFT", 60), ("UP", 120), ("UP", 160)):
        direction(f, button, frames)
    f.pulse("B", 30)  # fecha o texto do letreiro, se estiver aberto
    one_frame(f)
    for button, frames in (("RIGHT", 40), ("UP", 160), ("UP", 160), ("RIGHT", 32)):
        direction(f, button, frames)
    state = f.state()
    player = state[offset(OBJECTS):offset(OBJECTS) + 36]
    if tuple(player[8:11]) != (255, 0, 3) or struct.unpack_from("<hh", player, 16) != (20, 9):
        raise RuntimeError("Sequência não chegou à entrada da Rota 1; confira ROM e mGBA.")
    return state


def route_from_entry(f):
    direction(f, "UP", 140)
    direction(f, "UP", 140)


def active_objects(state):
    found = []
    for i in range(16):
        at = offset(OBJECTS + 36 * i)
        b = state[at:at + 36]
        if b[0] & 1:
            found.append((b[8], b[9], b[10], b[5], struct.unpack_from("<hh", b, 16)))
    return found


def route_template_coords(state, source):
    npc = source[0x7C2010:0x7C2010 + 24]
    at = state.find(npc, 0x21000, 0x61000)
    if at < 0:
        raise AssertionError("Não encontrei os modelos da Rota 1 no estado.")
    return [struct.unpack_from("<hh", state, at + 24 * i + 4) for i in range(8)]


def enemy(state):
    at = offset(ENEMY)
    return mon_facts(state[at:at + 100])


@unittest.skipUnless(BASE and ROM and CORE, "defina FIXOS_TEST_BASE, FIXOS_TEST_ROM e MGBA_CORE")
class FixedMGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(BASE).resolve()
        cls.rom = Path(ROM).resolve()
        cls.core = Path(CORE).resolve()
        cls.src = cls.base.read_bytes()
        if (fixed.digest(cls.src) != fixed.BASE_SHA256 or
                fixed.digest(cls.rom.read_bytes()) not in {fixed.OUTPUT_SHA256, updates.OUTPUT_SHA256, complement.OUTPUT_SHA256}):
            raise ValueError("ROMs não correspondem às versões testadas.")
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        f = Emulator(cls.base, cls.core, cls.dir)
        try:
            cls.fixture = route_entry_fixture(f)
        finally:
            f.close()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def launch(self, rom):
        f = Emulator(rom, self.core, self.dir)
        f.restore(self.fixture)
        return f

    def instrument(self, original, group, number, x, y):
        """Muda só uma cópia descartável para o letreiro teleportar no teste."""
        data = bytearray(original.read_bytes())
        self.assertEqual(data[0xF90000:0xF9000A], b"\xff" * 10)
        self.assertEqual(struct.unpack_from("<I", data, 0x7C20D8)[0], 0x08190947)
        struct.pack_into("<I", data, 0x7C20D8, 0x08F90000)
        data[0xF90000:0xF9000A] = struct.pack("<BBBBHHBB", 0x39, group, number, 0xFF, x, y, 0x27, 0x02)
        file = self.dir / f"test_{original.stem}_{group}_{number}_{x}_{y}.gba"
        file.write_bytes(data)
        return file

    def warp_from_sign(self, f):
        route_from_entry(f)
        f.run(64, "LEFT")
        f.run(30)
        f.run(5, "UP")
        f.run(25)
        f.pulse("A", 150)
        f.run(150)
        one_frame(f)

    def interact_up(self, f):
        f.run(5, "UP")
        f.run(25)
        f.pulse("A", 80)
        for _ in range(20):
            f.pulse("A", 50)
        one_frame(f)

    def test_transicao_natural_carrega_modelos_sem_fixos_mantendo_npcs(self):
        observed = []
        for path in (self.base, self.rom):
            f = self.launch(path)
            try:
                route_from_entry(f)
                observed.append((route_template_coords(f.state(), self.src), active_objects(f.state())))
            finally:
                f.close()
        old, new = observed
        self.assertEqual(old[0][:2], new[0][:2])
        self.assertEqual(old[0][5], (17, 9))
        self.assertTrue(all(x == (-1024, -1024) for x in new[0][2:]))
        # Ralts (objeto 5) aparece diante da câmera na versão anterior; não na nova.
        self.assertTrue(any(o[0] == 5 and o[3] == 0x98 for o in old[1]))
        self.assertFalse(any(o[0] == 5 and o[3] == 0x98 for o in new[1]))
        self.assertTrue(any(o[0] == 1 and o[3] != 0x98 for o in new[1]))

    def test_tarountula_nao_esta_mais_no_mapa(self):
        result = []
        for path in (self.base, self.rom):
            instrumented = self.instrument(path, 3, 19, 17, 10)
            f = self.launch(instrumented)
            try:
                self.warp_from_sign(f)
                objects = active_objects(f.state())
                self.interact_up(f)
                result.append((objects, enemy(f.state())))
            finally:
                f.close()
        self.assertTrue(any(o[:4] == (6, 19, 3, 0x98) for o in result[0][0]))
        self.assertFalse(any(o[:4] == (6, 19, 3, 0x98) for o in result[1][0]))
        self.assertEqual((result[0][1]["species"], result[0][1]["level"]), (917, 25))
        self.assertNotEqual(result[1][1]["species"], 917)

    def test_phione_e_moltres_continuam_com_batalhas(self):
        for group, number, x, y, local, species, level in (
            (1, 37, 38, 37, 4, 489, 55),  # Phione, sistema do hack
            (1, 101, 9, 7, 1, 146, 50),  # Moltres, evento original
        ):
            with self.subTest(species=species):
                f = self.launch(self.instrument(self.rom, group, number, x, y))
                try:
                    self.warp_from_sign(f)
                    self.assertTrue(any(o[:3] == (local, number, group) for o in active_objects(f.state())))
                    self.interact_up(f)
                    found = enemy(f.state())
                    self.assertTrue(found["valid"])
                    self.assertEqual((found["species"], found["level"]), (species, level))
                finally:
                    f.close()

    def test_tarountula_selvagem_no_mt_ember(self):
        # Um warp descartável leva ao gramado; o encontro é feito pelo código
        # selvagem normal da ROM, com passos reais e sem editar a RAM/RNG.
        f = self.launch(self.instrument(self.rom, 1, 97, 20, 41))
        try:
            self.warp_from_sign(f)
            initial = f.state()
            prior_species = enemy(initial)["species"]  # rival da introdução
            self.assertEqual(prior_species, 390)
            found = None
            # Repetir de um estado de teste e variar o tempo de espera é
            # necessário porque o slot do Tarountula tem chance de apenas 1%.
            for attempt in range(150):
                f.restore(initial)
                f.run(attempt * 2)
                for _ in range(28):
                    f.run(20, "LEFT")
                    f.run(20, "RIGHT")
                    candidate = enemy(f.state())
                    if candidate["valid"] and candidate["species"] != prior_species:
                        if candidate["species"] == 917:
                            f.run(350)
                            found = enemy(f.state())
                        break
                if found is not None:
                    break
            self.assertIsNotNone(found, "Encontro de 1% não apareceu na sequência determinística")
            self.assertTrue(found["valid"])
            self.assertEqual((found["species"], found["level"]), (917, 42))
        finally:
            f.close()

    def test_save_antigo_na_rota_e_reentrada_na_nova_rom(self):
        f = self.launch(self.base)
        try:
            route_from_entry(f)
            f.pulse("START", 70)
            for _ in range(4):
                f.pulse("DOWN", 35)
            for _ in range(10):
                f.pulse("A", 100)
            before = mon(f.state())
            ptr = f.core.core.retro_get_memory_data(0)
            size = f.core.core.retro_get_memory_size(0)
            self.assertTrue(ptr and size == 131072)
            save = C.string_at(ptr, size)
            self.assertGreater(len(set(save)), 2)
        finally:
            f.close()

        f = Emulator(self.rom, self.core, self.dir)
        try:
            ptr = f.core.core.retro_get_memory_data(0)
            self.assertEqual(f.core.core.retro_get_memory_size(0), len(save))
            C.memmove(ptr, save, len(save))  # apenas RAM da emulação de teste
            f.run(480)
            f.pulse("START", 100)
            for _ in range(8):
                f.pulse("A", 100)
            loaded = f.state()
            self.assertEqual(mon(loaded), before)
            # Save antigo no próprio mapa ainda mantém modelos antigos na RAM.
            self.assertEqual(route_template_coords(loaded, self.src)[5], (17, 9))
            f.run(150, "DOWN")
            f.run(120)
            f.run(180, "UP")
            f.run(100)
            returned = f.state()
            self.assertEqual(mon(returned), before)
            self.assertEqual(route_template_coords(returned, self.src)[5], (-1024, -1024))
            # Salva novamente já na ROM nova e confirma a leitura desse save.
            f.pulse("START", 70)
            for _ in range(4):
                f.pulse("DOWN", 35)
            for _ in range(20):
                f.pulse("A", 100)
            ptr = f.core.core.retro_get_memory_data(0)
            new_save = C.string_at(ptr, f.core.core.retro_get_memory_size(0))
            self.assertNotEqual(new_save, save)
        finally:
            f.close()
        f = Emulator(self.rom, self.core, self.dir)
        try:
            ptr = f.core.core.retro_get_memory_data(0)
            C.memmove(ptr, new_save, len(new_save))
            f.run(480)
            f.pulse("START", 100)
            for _ in range(8):
                f.pulse("A", 100)
            state = f.state()
            self.assertEqual(mon(state), before)
            self.assertEqual(route_template_coords(state, self.src)[5], (-1024, -1024))
        finally:
            f.close()


if __name__ == "__main__":
    unittest.main()
