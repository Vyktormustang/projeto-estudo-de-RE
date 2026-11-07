"""Fluxos em mGBA 0.10.5 com saves de teste, nunca com saves do usuário.

GOLPES_TEST_BASE=google_drive/ptbr_gen1-9_selvagens_treino_sem_fixos_comuns.gba \
GOLPES_TEST_ROM=/caminho/patch.gba MGBA_CORE=/caminho/mgba_libretro.so \
  python3 -m unittest discover -s tests -p test_golpes_gen9_integracao.py -v

O início, as batalhas, menus e salvamentos são executados pelo jogo. Alguns
Pokémon são preparados sinteticamente para alcançar níveis específicos. Para
visitar mapas distantes e fornecer um cogumelo, um letreiro de uma *cópia
instrumentada descartável* recebe um script de teste; essas alterações nunca
são entregues. Cada core é fechado antes de abrir outro com a mesma biblioteca.
"""
from __future__ import annotations

import contextlib
import ctypes as C
import os
import struct
import tempfile
import unittest
from pathlib import Path

from mgba_treino_harness import (
    Emulator, decrypted, mon, mon_facts, offset, put16, put32, put_mon, u32,
)
from test_eventos_fixos_mgba import (
    ENEMY, active_objects, enemy, one_frame, route_entry_fixture, route_from_entry,
)
from test_golpes_gen9_mgba import moves, seed_mon
from scripts import golpes_gen9 as patch, atualizacoes_gen9 as updates, complemento_gen9 as complement

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(os.environ.get("GOLPES_TEST_BASE", ROOT / "google_drive/ptbr_gen1-9_selvagens_treino_sem_fixos_comuns.gba"))
ROM = os.environ.get("GOLPES_TEST_ROM")
CORE = os.environ.get("MGBA_CORE")


def enemy_moves(state):
    data = state[offset(ENEMY):offset(ENEMY) + 100]
    block, order, valid = decrypted(data)
    if not valid:
        raise AssertionError("Checksum do Pokémon encontrado é inválido")
    return struct.unpack_from("<4H", block, order[1] * 12)


def set_exp_and_test_stats(state, experience, stat=135):
    """Só no estado sintético; mantém personalidade, IVs e checksum corretos."""
    data = mon(state)
    block, order, valid = decrypted(data)
    if not valid:
        raise AssertionError("Pokémon de teste inválido")
    put32(block, order[0] * 12 + 4, experience)
    put16(data, 28, sum(struct.unpack("<24H", block)) & 0xFFFF)
    key = u32(data, 0) ^ u32(data, 4)
    for i in range(0, 48, 4):
        put32(data, i + 32, u32(block, i) ^ key)
    put16(data, 86, 170)
    put16(data, 88, 170)
    for i in range(90, 100, 2):
        put16(data, i, stat)
    put_mon(state, data)


def save_game(f):
    f.pulse("START", 70)
    for _ in range(4):
        f.pulse("DOWN", 35)
    for _ in range(15):
        f.pulse("A", 100)
    ptr = f.core.core.retro_get_memory_data(0)
    size = f.core.core.retro_get_memory_size(0)
    if not ptr or size != 131072:
        raise AssertionError("Memória flash de teste não disponível")
    data = C.string_at(ptr, size)
    if len(set(data)) <= 2:
        raise AssertionError("O jogo não gerou o save de teste")
    return data


def load_game(f, data):
    ptr = f.core.core.retro_get_memory_data(0)
    if not ptr or f.core.core.retro_get_memory_size(0) != len(data):
        raise AssertionError("Memória flash de teste incompatível")
    C.memmove(ptr, data, len(data))  # somente o core e save descartáveis
    f.run(480)
    f.pulse("START", 100)
    for _ in range(8):
        f.pulse("A", 100)
    return f.state()


@unittest.skipUnless(ROM and CORE and BASE.exists(), "defina GOLPES_TEST_ROM, GOLPES_TEST_BASE e MGBA_CORE")
class GolpesIntegracaoMGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, cls.base, cls.core = Path(ROM).resolve(), BASE.resolve(), Path(CORE).resolve()
        if patch.digest(cls.base.read_bytes()) != patch.BASE_SHA256:
            raise ValueError("ROM anterior não corresponde à versão identificada")
        if patch.digest(cls.rom.read_bytes()) not in {patch.OUTPUT_SHA256, updates.OUTPUT_SHA256, complement.OUTPUT_SHA256}:
            raise ValueError("ROM de golpes não corresponde às versões validadas")
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        f = Emulator(cls.rom, cls.core, cls.dir)
        try:
            cls.fixture = route_entry_fixture(f)
        finally:
            f.close()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @contextlib.contextmanager
    def launch(self, path=None, state=None):
        f = Emulator(path or self.rom, self.core, self.dir)
        try:
            if state is not None:
                f.restore(bytes(state))
            yield f
        finally:
            f.close()

    def instrument_warp(self, group, number, x, y, give_mushroom=False):
        """Altera uma cópia para o letreiro levar a um ponto de teste."""
        data = bytearray(self.rom.read_bytes())
        self.assertEqual(data[0xF90000:0xF90020], b"\xff" * 32)
        self.assertEqual(struct.unpack_from("<I", data, 0x7C20D8)[0], 0x08190947)
        struct.pack_into("<I", data, 0x7C20D8, 0x08F90000)
        give = struct.pack("<BHH", 0x44, 104, 1) if give_mushroom else b""
        warp = struct.pack("<BBBBHHBB", 0x39, group, number, 0xFF, x, y, 0x27, 0x02)
        script = give + warp
        data[0xF90000:0xF90000 + len(script)] = script
        path = self.dir / f"instrumentada_{group}_{number}_{x}_{y}_{int(give_mushroom)}.gba"
        path.write_bytes(data)
        return path

    def warp_from_sign(self, f):
        route_from_entry(f)
        f.run(64, "LEFT")
        f.run(30)
        f.run(5, "UP")
        f.run(25)
        f.pulse("A", 150)
        f.run(150)
        one_frame(f)

    def enter_route_battle(self, f, enter=True):
        from battle_fixture_helpers import in_battle
        if enter:
            route_from_entry(f)
        # Walking INTO the route may already start the encounter. Comparing
        # species only after that walk misses it (and also misses repeats).
        # Observe native battle state instead; do not edit RAM to force a fight.
        for _ in range(120):
            if in_battle(f.state()):
                f.run(350)
                found = enemy(f.state())
                self.assertTrue(found["valid"])
                return found
            f.run(20, "LEFT")
            f.run(20, "RIGHT")
        self.fail("Não ocorreu encontro selvagem na rota de teste")

    def advance_until_move(self, f, wanted, limit=100):
        for _ in range(limit):
            f.pulse("A", 50)
            state = f.state()
            if wanted in moves(state):
                return state
        self.fail(f"O golpe {wanted} não foi aprendido na sequência real")

    def test_inicial_e_tarountula_selvagem_sao_criados_com_novas_listas(self):
        initial = self.fixture
        self.assertEqual((mon_facts(mon(initial))["species"], mon_facts(mon(initial))["level"]), (1, 5))
        self.assertEqual(moves(initial), (33, 45, 22, 0))  # Bulbasaur inicial normal
        path = self.instrument_warp(1, 97, 20, 41)  # Mt. Ember: único auxílio é o warp
        with self.launch(path, initial) as f:
            self.warp_from_sign(f)
            start = f.state()
            self.assertEqual(enemy(start)["species"], 390)
            found = None
            for attempt in range(150):  # slot de 1%; variar tempo, sem editar o RNG
                f.restore(start)
                f.run(attempt * 2)
                for _ in range(28):
                    f.run(20, "LEFT")
                    f.run(20, "RIGHT")
                    candidate = enemy(f.state())
                    if candidate["valid"] and candidate["species"] != 390:
                        if candidate["species"] == 917:
                            f.run(350)
                            found = f.state()
                        break
                if found is not None:
                    break
            self.assertIsNotNone(found, "Tarountula selvagem de 1% não apareceu")
            facts = enemy(found)
            self.assertEqual((facts["species"], facts["level"]), (917, 42))
            self.assertEqual(enemy_moves(found), (68, 29, 508, 630))

    def test_batalha_real_substitui_golpe_com_id_acima_de_511(self):
        state = seed_mon(self.fixture, 917, 4, (33, 81, 45, 52))
        set_exp_and_test_stats(state, 236)  # 1 XP antes do nível 5
        with self.launch(state=state) as f:
            self.assertEqual(self.enter_route_battle(f)["species"], 915)
            result = self.advance_until_move(f, 518)
            self.assertEqual(mon_facts(mon(result))["level"], 5)
            self.assertEqual(moves(result), (518, 81, 45, 52))
            self.assertTrue(mon_facts(mon(result))["valid"])

    def test_evolucao_real_para_charizard_ensina_air_slash(self):
        state = seed_mon(self.fixture, 5, 35, (52, 45, 108, 0))
        set_exp_and_test_stats(state, 40006)  # 1 XP antes do nível 36
        with self.launch(state=state) as f:
            self.enter_route_battle(f)
            result = self.advance_until_move(f, 403)
            facts = mon_facts(mon(result))
            self.assertEqual((facts["species"], facts["level"]), (6, 36))
            self.assertEqual(moves(result), (52, 45, 108, 403))
            self.assertTrue(facts["valid"])

    def test_relembrador_real_ensina_struggle_bug(self):
        state = seed_mon(self.fixture, 917, 5, (33, 81, 0, 0))
        path = self.instrument_warp(33, 1, 7, 6, give_mushroom=True)
        with self.launch(path, state) as f:
            self.warp_from_sign(f)
            self.assertTrue(any(o[:3] == (1, 1, 33) for o in active_objects(f.state())))
            f.run(5, "UP")
            f.run(25)
            result = self.advance_until_move(f, 518)
            self.assertEqual(moves(result), (33, 81, 518, 0))
            self.assertTrue(mon_facts(mon(result))["valid"])

    def test_fixos_especiais_continuam_e_comum_nao_aparece(self):
        # A instrumentação só transporta o jogador: encontros usam scripts da ROM.
        for group, number, x, y, local, species, level in (
            (1, 37, 38, 37, 4, 489, 55),  # Phione
            (1, 101, 9, 7, 1, 146, 50),   # Moltres
        ):
            with self.subTest(species=species):
                with self.launch(self.instrument_warp(group, number, x, y), self.fixture) as f:
                    self.warp_from_sign(f)
                    self.assertTrue(any(o[:3] == (local, number, group) for o in active_objects(f.state())))
                    f.run(5, "UP")
                    f.run(25)
                    for _ in range(21):
                        f.pulse("A", 50)
                    found = enemy(f.state())
                    self.assertTrue(found["valid"])
                    self.assertEqual((found["species"], found["level"]), (species, level))
        with self.launch(self.instrument_warp(3, 19, 17, 10), self.fixture) as f:
            self.warp_from_sign(f)
            self.assertFalse(any(o[:4] == (6, 19, 3, 0x98) for o in active_objects(f.state())))
            f.run(5, "UP")
            f.run(25)
            for _ in range(21):
                f.pulse("A", 50)
            self.assertNotEqual(enemy(f.state())["species"], 917)

    def test_save_antigo_sobe_nivel_salva_e_recarrega(self):
        # Save gerado no jogo anterior, sem abrir arquivos de save pessoais.
        with self.launch(self.base) as old:
            original = route_entry_fixture(old)
            state = seed_mon(original, 6, 61, (518, 45, 108, 0))
            set_exp_and_test_stats(state, 234392)  # 1 XP antes do nível 62
            old.restore(bytes(state))
            route_from_entry(old)
            before = mon(old.state())
            old_save = save_game(old)

        with self.launch() as new:
            loaded = load_game(new, old_save)
            self.assertEqual(mon(loaded), before)
            self.assertEqual(moves(loaded), (518, 45, 108, 0))
            self.assertEqual(self.enter_route_battle(new, enter=False)["species"], 915)
            learned = self.advance_until_move(new, 394)
            facts_before, facts_after = mon_facts(before), mon_facts(mon(learned))
            self.assertEqual((facts_after["species"], facts_after["level"]), (6, 62))
            self.assertEqual(facts_after["iv"], facts_before["iv"])
            self.assertEqual(facts_after["ev"], [1, 0, 0, 0, 0, 0])  # EV ganho na batalha
            self.assertEqual(moves(learned), (518, 45, 108, 394))
            for _ in range(18):
                new.pulse("A", 50)  # terminar diálogos e sair da batalha
            after = mon(new.state())
            new_save = save_game(new)
            self.assertNotEqual(new_save, old_save)

        with self.launch() as check:
            reloaded = load_game(check, new_save)
            self.assertEqual(mon(reloaded), after)
            self.assertEqual(moves(reloaded), (518, 45, 108, 394))
            self.assertTrue(mon_facts(mon(reloaded))["valid"])


if __name__ == "__main__":
    unittest.main()
