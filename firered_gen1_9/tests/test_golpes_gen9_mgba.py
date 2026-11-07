"""Testes em mGBA 0.10.5; ROM privada, Pokémon sintéticos e cópias descartáveis.

GOLPES_TEST_ROM=/caminho/patch.gba MGBA_CORE=/caminho/mgba_libretro.so \
  python3 -m unittest discover -s tests -p test_golpes_gen9_mgba.py -v
"""
from __future__ import annotations
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path

from mgba_treino_harness import (
    Emulator, PARTY, decrypted, make_summary_fixture, mon, mon_facts, offset,
    put16, put32, put_mon, u32,
)
from scripts import golpes_gen9 as patch

ROM = os.environ.get("GOLPES_TEST_ROM")
CORE = os.environ.get("MGBA_CORE")
SCRATCH = 0x02001000
TASK = 0x02001100
OUT = 0x02001200
SENTINEL = 0x08056AAE  # instrução Thumb 'b .' existente na ROM


def seed_mon(state, species, level, moves, egg=False):
    state = bytearray(state)
    data = mon(state)
    block, order, valid = decrypted(data)
    if not valid:
        raise AssertionError("Pokémon inicial inválido")
    put16(block, order[0] * 12, species)
    struct.pack_into("<4H", block, order[1] * 12, *moves)
    block[order[1] * 12 + 8:order[1] * 12 + 12] = bytes(20 if x else 0 for x in moves)
    if egg:
        flags = u32(block, order[3] * 12 + 4)
        put32(block, order[3] * 12 + 4, flags | (1 << 30))
    put16(data, 28, sum(struct.unpack("<24H", block)) & 0xffff)
    key = u32(data, 0) ^ u32(data, 4)
    for n in range(0, 48, 4):
        put32(data, n + 32, u32(block, n) ^ key)
    data[84] = level
    put_mon(state, data)
    return state


def moves(state):
    block, order, valid = decrypted(mon(state))
    if not valid: raise AssertionError("Checksum de Pokémon inválido")
    return struct.unpack_from("<4H", block, order[1] * 12)


def set_registers(state, pc, regs):
    state = bytearray(state)
    for n, value in regs.items():
        put32(state, 0x20 + n * 4, value)
    put32(state, 0x20 + 13 * 4, 0x03007E00)
    put32(state, 0x20 + 14 * 4, SENTINEL | 1)
    put32(state, 0x20 + 15 * 4, pc + 2)  # pipeline Thumb do mGBA
    cpsr = u32(state, 0x60)
    put32(state, 0x60, ((cpsr | 0x20 | 0xc0) & ~0x1f) | 0x1f)
    put32(state, 0x2f8, 0); put32(state, 0x2fc, 0)
    return bytes(state)


def invoke(f, state, pc, regs, expected=SENTINEL):
    f.restore(set_registers(state, pc, regs))
    f.run(3)
    result = f.state()
    if u32(result, 0x5c) != expected + 2:
        raise AssertionError(f"Rotina não retornou ao ponto esperado: PC={u32(result, 0x5c):08x} esperado={expected + 2:08x}")
    return result


@unittest.skipUnless(ROM and CORE, "defina GOLPES_TEST_ROM e MGBA_CORE para os testes mGBA")
class GolpesMGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.core = Path(ROM).resolve(), Path(CORE).resolve()
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = Emulator(cls.path, cls.core, Path(cls.temp.name))
        cls.fixture = make_summary_fixture(cls.f)

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    def call_level(self, state, first=1):
        return invoke(self.f, state, 0x08109790, {0: PARTY, 1: first})

    def test_ids_acima_de_511_e_charizard(self):
        for species, level, before, want, pp in (
            (917, 5, (33, 81, 0, 0), 518, 20),
            (6, 54, (10, 45, 52, 0), 516, 5),
            (6, 62, (10, 45, 52, 0), 394, 15),
        ):
            with self.subTest(species=species, level=level):
                state = seed_mon(self.fixture, species, level, before)
                facts_before = mon_facts(mon(state))
                out = self.call_level(state)
                slot = before.index(0)
                expected_moves = list(before)
                expected_moves[slot] = want
                self.assertEqual(moves(out), tuple(expected_moves))
                self.assertEqual(u32(out, 0x20), want)
                self.assertEqual(struct.unpack_from("<H", out, offset(0x02021866))[0], want)
                block, order, _ = decrypted(mon(out))
                self.assertEqual(block[order[1] * 12 + 8 + slot], pp)
                facts_after = mon_facts(mon(out))
                self.assertEqual(facts_before["iv"], facts_after["iv"])
                self.assertEqual(facts_before["ev"], facts_after["ev"])
                self.assertEqual(facts_before["species"], facts_after["species"])
                self.assertTrue(facts_after["valid"])

    def test_equipes_cheias_e_continuacao_mesmo_nivel(self):
        state = seed_mon(self.fixture, 6, 62, (10, 45, 52, 108))
        out = self.call_level(state)
        self.assertEqual(u32(out, 0x20), 0xffff)
        self.assertEqual(struct.unpack_from("<H", out, offset(0x02021866))[0], 394)
        self.assertEqual(moves(out), (10, 45, 52, 108))
        state = seed_mon(self.fixture, 1, 15, (33, 22, 0, 0))
        a = self.call_level(state, 1)
        self.assertEqual(moves(a), (33, 22, 77, 0))
        b = self.call_level(a, 0)
        self.assertEqual(moves(b), (33, 22, 77, 79))
        c = self.call_level(b, 0)
        self.assertEqual(u32(c, 0x20), 0)
        self.assertEqual(moves(c), moves(b))
        # Se o primeiro já era conhecido, o jogo recebe ALREADY e continua.
        state = seed_mon(self.fixture, 1, 15, (33, 22, 77, 0))
        a = self.call_level(state, 1)
        self.assertEqual(u32(a, 0x20), 0xfffe)
        b = self.call_level(a, 0)
        self.assertEqual(moves(b), (33, 22, 77, 79))

    def test_relembrador_limites_e_especies_invalidas(self):
        def check(species, level, before):
            state = seed_mon(self.fixture, species, level, before)
            state[offset(OUT):offset(OUT)+64] = b"\x66" * 64
            got = invoke(self.f, state, 0x0810e808, {0: PARTY, 1: OUT})
            count = u32(got, 0x20)
            values = struct.unpack_from("<" + str(count) + "H", got, offset(OUT))
            counted = invoke(self.f, state, 0x0810e904, {0: PARTY})
            self.assertEqual(u32(counted, 0x20), count)
            self.assertEqual(got[offset(OUT)+48:offset(OUT)+64], b"\x66" * 16)
            self.assertEqual(len(values), len(set(values)))
            self.assertTrue(set(values).isdisjoint(set(before)))
            return count, values
        n, result = check(6, 62, (10, 45, 52, 108))
        self.assertGreater(n, 0)
        self.assertTrue({403, 516, 394}.issubset(result))
        _, lower = check(6, 40, (10, 45, 52, 108))
        self.assertNotIn(516, lower); self.assertNotIn(394, lower)
        n, result = check(475, 100, (33, 45, 52, 108))
        self.assertLessEqual(n, 24)
        self.assertEqual(n, 24)  # 31 entradas totais, interface cabe 24+Cancelar.
        self.assertEqual(check(1027, 100, (33, 45, 52, 108))[0], 0)
        egg = seed_mon(self.fixture, 1, 15, (33, 45, 0, 0), egg=True)
        out = invoke(self.f, egg, 0x0810e904, {0: PARTY})
        self.assertEqual(u32(out, 0x20), 0)

    def test_lista_de_ovos_aceita_todos_e_nao_ultrapassa_50(self):
        state = bytearray(self.fixture)
        state[offset(OUT):offset(OUT)+116] = b"\x66" * 116
        out = invoke(self.f, state, 0x0810e8cc, {0: 475, 1: OUT})
        count = u32(out, 0x20)
        self.assertEqual(count, 31)
        self.assertEqual(out[offset(OUT)+100:offset(OUT)+116], b"\x66" * 16)
        other = invoke(self.f, state, 0x0810e8cc, {0: 1026, 1: OUT})
        self.assertEqual(u32(other, 0x20), 0)

    def instrument(self, offsets):
        data = bytearray(self.path.read_bytes())
        for at in offsets:
            data[at:at + 2] = b"\xfe\xe7"  # pára ao chegar no retorno do hook
        path = Path(self.temp.name) / "instrumentada.gba"
        path.write_bytes(data)
        return path

    def test_golpe_de_evolucao_nas_duas_cenas_e_cancelamento(self):
        path = self.instrument((0x0A0C78, 0x0A135C))
        separate_core = Path(self.temp.name) / "evolucao_core.so"
        shutil.copyfile(self.core, separate_core)
        f = Emulator(path, separate_core, Path(self.temp.name))
        try:
            for addr, cont, trade in ((0x080a0c70, 0x080a0c78, False),
                                      (0x080a1354, 0x080a135c, True)):
                for canceled in (0, 1):
                    with self.subTest(trade=trade, canceled=canceled):
                        st = seed_mon(self.fixture, 6, 36, (10, 45, 52, 0))
                        st[offset(TASK)+0x10] = 1
                        put16(st, offset(TASK)+0x1a, canceled)
                        # Cena normal usa r0; cena de troca copia r9 (sb) para r0.
                        regs = {0: PARTY, 4: TASK, 9: PARTY}
                        result = invoke(f, st, addr, regs, cont)
                        if canceled:
                            self.assertEqual(moves(result), (10, 45, 52, 0))
                            self.assertEqual(u32(result, 0x20), 0)
                        else:
                            self.assertEqual(moves(result), (10, 45, 52, 403))
                            self.assertEqual(u32(result, 0x20), 403)
        finally:
            f.close()

    def test_buffers_de_nomes_com_guarda(self):
        # Uma cópia temporária pára antes de retomar o contexto do jogo; o
        # corpo dos quatro hooks é exatamente o da ROM testada.
        path = self.instrument((0x0CF7FC, 0x1148D4, 0x114A6C, 0x055B58))
        separate_core = Path(self.temp.name) / "nomes_core.so"
        shutil.copyfile(self.core, separate_core)
        f = Emulator(path, separate_core, Path(self.temp.name))
        try:
            move = 566  # PARABOLIC CHARGE, 16 caracteres na ROM
            text = self.path.read_bytes()[catalog_move_name(move):catalog_move_name(move)+16]
            for addr, cont, limit, regs in (
                (0x080cf7f4, 0x080cf7fc, 12, {0: OUT, 1: move * 17, 7: SCRATCH, 8: 0x08235930}),
                (0x081148cc, 0x081148d4, 12, {0: OUT - 0x77, 1: move * 17, 3: 0x08235930}),
                (0x08114a64, 0x08114a6c, 12, {0: OUT - 0x84, 1: move * 17, 3: 0x08235930}),
                (0x08055c94, 0x08055b58, 15, {0: OUT, 1: move * 17, 3: 0x08235930}),
            ):
                with self.subTest(hook=hex(addr)):
                    st = bytearray(self.fixture)
                    st[offset(OUT):offset(OUT)+32] = b"\x66" * 32
                    put32(st, offset(SCRATCH), 0x02001500)
                    result = invoke(f, st, addr, regs, cont)
                    actual = result[offset(OUT):offset(OUT)+32]
                    self.assertEqual(actual[:limit], text[:limit])
                    self.assertEqual(actual[limit], 0xff)
                    self.assertEqual(actual[limit+1:], b"\x66" * (31 - limit))
        finally:
            f.close()


def catalog_move_name(move):
    return 0x235930 + 17 * move

if __name__ == "__main__":
    unittest.main()
