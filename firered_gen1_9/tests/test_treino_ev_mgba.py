"""Integração opcional: ROM própria + mGBA 0.10.5, sem tocar saves do usuário.

TREINO_TEST_ROM=/caminho/nova.gba MGBA_CORE=/caminho/mgba_libretro.so \
    python3 -m unittest discover -s tests -p 'test_treino_ev_mgba.py' -v
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from mgba_treino_harness import (
    Emulator, PARTY, SELECTED, SUMMARY_POINTER, decrypted, make_summary_fixture,
    meta, mon, mon_facts, offset, put16, put_mon, seed, set_ev, u32,
)

ROM = os.environ.get("TREINO_TEST_ROM")
CORE = os.environ.get("MGBA_CORE")
EXPECTED_ROMS = {
    "1123e7995b37008a75c818f09fb852bfd4910e1f074ae2e630cbd9c8af994abc",  # treino
    "c563d43a8f15976314ad5fb271ad44a83cdf3143749389311f261ffd506a466b",  # treino + fixos comuns retirados
    "412bcd89214d4126d92f6c2256a56227c6f30fa138e0b262ef287f5b12b3997b",  # com listas de golpes
    "36cf2355789eca9273c2e4110606872fff8ab8ece82dae9ee090cd3bfa0546db",  # TMs modernas
    "6155b6a5fe62528b7b67836d3a47752b1cb3b1a71c1f2b59bfa7a68af0100d67",  # complemento parcial expandido
    "93dc62e86cfa3dc70c8057fa4ea25031761d48fc5ce4f7615a5a66d4fc280907",  # estojo expandido v2
    "cf1de0e237feefcfda6789bc81c726ed13d91d512b85c54b9f857520a7a4fc87",  # motor ampliado v5
    "75d66d3c36e560df29f6c613666b91a6c81ce24663b6a3f76f4dd2ea7d747ce6",  # motor parcial v6
    "6321d8e2900cc44dcaefb2dedfbaf5b0952b2796ca27a4cb9d8dc0875827de09",  # motor parcial v7
    "32fd47c87b581952f54f05656f590c5f7da55d5cc3d186d81951508899ec54f0",  # motor parcial v8
    "2936a08fc95f40c7788b6136f209ab5cab31aec062d615f2a458f45b123e0e6f",  # motor parcial v9
    "a533d1812812e2348bbe62a95a8c3817dd9d8372a89ff283f0e747c6c7ddeb09",  # motor parcial v10
    "1a147ee909183cc2e3bbba0599a4d70f0b0185b01d3e4941a1f27e6c4a9eee5b",  # motor parcial v11
    "fb28ad767a11add187d0fa69dec0164b3de73a9887a0c5834c5feccc675725c1",  # motor parcial v12
}


@unittest.skipUnless(ROM and CORE, "defina TREINO_TEST_ROM e MGBA_CORE para executar mGBA")
class TreinoMGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, core = Path(ROM).resolve(), Path(CORE).resolve()
        if hashlib.sha256(rom.read_bytes()).hexdigest() not in EXPECTED_ROMS:
            raise ValueError("A ROM indicada não é uma build de treino identificada nos testes")
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = Emulator(rom, core, Path(cls.temp.name))
        cls.fixture = make_summary_fixture(cls.f)

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    def start(self, evs=(10, 20, 0, 0, 0, 0), hp=None, max_hp=None):
        self.f.restore(seed(self.fixture, evs, hp, max_hp))
        self.f.run(20)
        self.f.pulse("SELECT")
        self.f.pulse("A")

    def info(self):
        state = self.f.state()
        return state, mon(state), mon(state, work=True), meta(state)

    def test_confirmar_so_redistribui_pontos_e_preserva_outros_dados(self):
        self.start()
        _, before, _, _ = self.info()
        self.f.pulse("LEFT")
        _, real, draft, mode = self.info()
        self.assertEqual(real, before)
        self.assertEqual(mon_facts(draft)["ev"], [6, 20, 0, 0, 0, 0])
        self.f.pulse("A")  # saldo 4: não confirma
        _, real, _, mode = self.info()
        self.assertEqual(real, before)
        self.assertEqual(mode & 3, 3)
        self.f.pulse("DOWN"); self.f.pulse("RIGHT"); self.f.pulse("A", 80)
        _, after, draft, mode = self.info()
        a, b = mon_facts(before), mon_facts(after)
        self.assertEqual(b["ev"], [6, 24, 0, 0, 0, 0])
        self.assertEqual(sum(a["ev"]), sum(b["ev"]))
        self.assertEqual(a["iv"], b["iv"])
        self.assertEqual(after, draft)
        self.assertTrue(b["valid"])
        self.assertFalse(mode & 0x80)
        old, old_order, _ = decrypted(before)
        new, new_order, _ = decrypted(after)
        self.assertEqual(old_order, new_order)
        i = old_order[2] * 12
        old[i:i + 6] = new[i:i + 6]
        self.assertEqual(old, new)  # secure fields other than EVs unchanged
        self.assertEqual(before[:28], after[:28])
        self.assertEqual(before[30:32], after[30:32])
        self.assertEqual(before[80:86], after[80:86])  # status, level and mail

    def test_cancelar_descarta_rascunho(self):
        self.start()
        _, before, _, _ = self.info()
        self.f.pulse("LEFT"); self.f.pulse("B", 80)
        _, real, draft, mode = self.info()
        self.assertEqual(before, real)
        self.assertEqual(real, draft)
        self.assertFalse(mode & 0x80)

    def test_limite_255_transferencia_parcial_e_saldo(self):
        self.start((4, 254, 0, 0, 0, 0))
        _, before, _, _ = self.info()
        self.f.pulse("LEFT"); self.f.pulse("DOWN"); self.f.pulse("RIGHT")
        _, real, draft, mode = self.info()
        self.assertEqual(before, real)
        self.assertEqual(mon_facts(draft)["ev"], [0, 255, 0, 0, 0, 0])
        self.f.pulse("RIGHT"); self.f.pulse("A")
        _, real, draft, mode = self.info()
        self.assertEqual(before, real)
        self.assertEqual(mode & 3, 3)  # ainda restam 3 EVs
        self.f.pulse("DOWN"); self.f.pulse("RIGHT"); self.f.pulse("A", 80)
        _, real, _, _ = self.info()
        self.assertEqual(mon_facts(real)["ev"], [0, 255, 3, 0, 0, 0])

    def test_510_e_evs_253_255_sao_preservados(self):
        self.start((255, 253, 2, 0, 0, 0))
        _, before, _, _ = self.info()
        self.f.pulse("DOWN"); self.f.pulse("LEFT"); self.f.pulse("UP"); self.f.pulse("RIGHT")
        _, real, draft, _ = self.info()
        self.assertEqual(real, before)
        self.assertEqual(mon_facts(draft)["ev"], [255, 249, 2, 0, 0, 0])
        self.f.pulse("A")  # atributo de HP já está no teto
        self.assertEqual(self.info()[1], before)
        self.f.pulse("DOWN"); self.f.pulse("RIGHT"); self.f.pulse("A", 80)
        self.assertEqual(mon_facts(self.info()[1])["ev"], [255, 253, 2, 0, 0, 0])

    def test_hp_desmaiado_ferido_e_underflow(self):
        # HP máximo sintético maior que o calculado força o caso de underflow.
        for hp in (0, 1, 15):
            with self.subTest(hp=hp):
                self.start((20, 20, 0, 0, 0, 0), hp=hp, max_hp=30)
                self.f.pulse("LEFT"); self.f.pulse("DOWN"); self.f.pulse("RIGHT"); self.f.pulse("A", 80)
                facts = mon_facts(self.info()[1])
                expected = 0 if hp == 0 else max(1, min(facts["max_hp"], hp + facts["max_hp"] - 30))
                self.assertEqual(facts["hp"], expected)
                self.assertEqual(facts["ev"], [16, 24, 0, 0, 0, 0])
                self.assertTrue(facts["valid"])

    def test_seis_slots_e_troca_na_tela(self):
        state = bytearray(self.fixture)
        prototype = mon(state)
        for index in range(6):
            data = bytearray(prototype)
            set_ev(data, [4 + index, 10 + index, 0, 0, 0, 0])
            put_mon(state, data, slot=index)
        put_mon(state, mon(state), work=True)
        summary = u32(state, offset(SUMMARY_POINTER))
        state[offset(summary + 0x3228)] = 5
        self.f.restore(bytes(state)); self.f.run(20)
        for index in range(6):
            if index: self.f.pulse("DOWN", 110)
            state = self.f.state()
            self.assertEqual(state[offset(SELECTED)], index)
            originals = [mon(state, slot) for slot in range(6)]
            self.f.pulse("SELECT"); self.f.pulse("A"); self.f.pulse("LEFT")
            self.f.pulse("DOWN"); self.f.pulse("RIGHT"); self.f.pulse("A", 80)
            state = self.f.state()
            actual = [mon(state, slot) for slot in range(6)]
            self.assertEqual(mon_facts(actual[index])["ev"], [index, 14 + index, 0, 0, 0, 0])
            self.assertTrue(all(mon_facts(x)["valid"] for x in actual))
            for other in range(6):
                if other != index: self.assertEqual(actual[other], originals[other])

    def test_contextos_inseguros_e_checksum_invalido_nao_editam(self):
        # Flags são simuladas no estado; batalha real foi exercitada à parte.
        for field, value in ((0x3220, 5), (0x3220, 4), (0x3218, 1), (0x3234, 1)):
            with self.subTest(field=hex(field), value=value):
                state = bytearray(seed(self.fixture, (10, 20, 0, 0, 0, 0)))
                summary = u32(state, offset(SUMMARY_POINTER))
                state[offset(summary + field)] = value
                original = mon(state)
                self.f.restore(bytes(state)); self.f.pulse("SELECT"); self.f.pulse("A")
                actual = self.f.state()
                self.assertEqual(mon(actual), original)
                self.assertFalse(meta(actual) & 0x80)
        state = bytearray(seed(self.fixture, (10, 20, 0, 0, 0, 0)))
        state[offset(PARTY) + 32] ^= 1
        original = mon(state)
        self.f.restore(bytes(state)); self.f.pulse("SELECT"); self.f.pulse("A")
        self.assertEqual(mon(self.f.state()), original)

    def test_copia_desatualizada_nao_sobrescreve_equipe(self):
        self.start()
        self.f.pulse("LEFT")
        state = bytearray(self.f.state())
        other = mon(state)
        put16(other, 86, 7)  # Mudança externa simulada, fora do bloco criptografado.
        put_mon(state, other)
        self.f.restore(bytes(state)); self.f.pulse("RIGHT")
        _, real, draft, mode = self.info()
        self.assertEqual(real, other)
        self.assertEqual(draft, other)
        self.assertFalse(mode & 0x80)

    def test_60_segundos_com_rascunho_nao_alteram_equipe(self):
        self.start()
        self.f.pulse("LEFT")
        _, before, draft_before, _ = self.info()
        self.f.run(3600)
        _, after, draft_after, _ = self.info()
        self.assertEqual(before, after)
        self.assertEqual(draft_before, draft_after)


if __name__ == "__main__":
    unittest.main()
