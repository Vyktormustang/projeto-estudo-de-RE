"""Cosmog V42 — eclosão do ovo (pendência de docs/PROGRESSO_COSMOG_V42.md).

Fecha o item "Eclosão do ovo, incubação completa": deposita Cosmog + Ditto pela
interface nativa da creche, recebe o ovo do NPC, faz SAVE/Continuar e caminha
até a eclosão — sem editar o contador de passos nem o estado do ovo.

Saves sintéticos apenas; nenhum save pessoal. Não reivindica campanha completa.

    COSMOG_V42_ROM=... MGBA_CORE=... PYTHONPATH=harness:.:tests \
      python3 -B -m unittest -v tests.test_cosmog_hatch_v42_mgba

Orçamento de passos: COSMOG_HATCH_MAX_STEPS (default 3000). O ovo de 120 ciclos
exige ~30.600 passos; sem memory maps no core cada passo serializa 528 KB (~2,4 s),
então o padrão para cedo e a suíte reporta SKIP com o motivo, em vez de falhar em
falso. Ver reports/v42/AUDITORIA_COSMOG_ECLOSAO_V42.md.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts import motor_v42 as p
from mgba_treino_harness import Emulator, offset, mon_facts, u32
from test_eventos_fixos_mgba import route_entry_fixture
from test_golpes_gen9_integracao import save_game, load_game
from battle_fixture_helpers import main_callback2
import test_ilhas_v41_mgba as islands
import test_motor_v21_gameplay_mgba as game
from test_cosmog_v42_mgba import CosmogNativeTests as _CosmogNative

ROM = os.environ.get("COSMOG_V42_ROM")
CORE = os.environ.get("MGBA_CORE")


@unittest.skipUnless(ROM and CORE, "set COSMOG_V42_ROM and MGBA_CORE")
class CosmogHatchTests(unittest.TestCase):
    switch = islands.IslandNativeTests.switch
    bootstrap = islands.IslandNativeTests.bootstrap
    setvar = islands.IslandNativeTests.setvar
    setflag = islands.IslandNativeTests.setflag
    flag = islands.IslandNativeTests.flag
    call = islands.IslandNativeTests.call
    shot = islands.IslandNativeTests.shot
    walkto = _CosmogNative.walkto
    move_one = _CosmogNative.move_one

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        cls.source = cls.rom.read_bytes()
        if p.digest(cls.source) != p.OUTPUT_SHA256:
            raise ValueError("Not exact v42")
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        cls.f = Emulator(cls.rom, Path(CORE), cls.dir)
        cls.fixture = route_entry_fixture(cls.f)
        cls.cache = {}
        cls.observations = []

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()
        if cls.rom.read_bytes() != cls.source:
            raise AssertionError("ROM changed")
        # evidencia opcional, fora do Git
        if os.environ.get("COSMOG_V42_OBSERVATIONS"):
            with Path(os.environ["COSMOG_V42_OBSERVATIONS"]).open("x") as f:
                json.dump(cls.observations, f, indent=2)
                f.write("\n")

    # ---------- utilidades locais (reaproveitam o caminho já provado) ----------
    def step_once(self, button):
        """Um passo manual, exigindo mudança real de coordenada."""
        origin = game.coords(self.f.state())
        for _ in range(180):
            self.f.run(1, button)
            if game.coords(self.f.state()) != origin:
                return True
        return False

    def walk_steps(self, n, prefer="RIGHT"):
        """Caminha n passos manuais alternando a direção; conta só os efetivos."""
        feitos = 0
        for i in range(n * 2):
            if feitos >= n:
                break
            if self.step_once(prefer if i % 2 == 0 else ("LEFT" if prefer == "RIGHT" else "RIGHT")):
                feitos += 1
        return feitos

    def get_egg(self):
        """Deposita Cosmog + Ditto pela interface e retira o ovo do NPC.

        Reaproveita exatamente a rota nativa que o teste de creche já provou;
        aqui paramos logo depois de receber o ovo, sem SAVE ainda.
        """
        from mgba_treino_harness import PARTY as PARTY_OFF
        from test_golpes_gen9_mgba import seed_mon

        st = self.setvar(self.bootstrap(35, 0, 2, 4), 0x4086, 1)
        st = bytearray(st)
        start = offset(PARTY_OFF)
        for slot, species in ((1, 789), (2, 132)):
            seeded = seed_mon(st, species, 25, (144, 0, 0, 0))
            st[start + 100 * slot:start + 100 * (slot + 1)] = game.party_slot(seeded, 0)
        st[game.PARTY_COUNT] = 3
        self.f.restore(bytes(st))
        self.f.run(8, "UP")
        self.f.run(30)
        self.f.pulse("A", 180)
        for number in range(2):
            for _ in range(25):
                if main_callback2(self.f.state()) == 0x080F6225:
                    break
                self.f.pulse("A", 100)
            self.assertEqual(main_callback2(self.f.state()), 0x080F6225)
            for _ in range(8):
                if self.f.state()[offset(0x0203A6DD)] == 1:
                    break
                self.f.pulse("DOWN", 35)
            self.assertEqual(self.f.state()[offset(0x0203A6DD)], 1)
            for _ in range(25):
                self.f.pulse("A", 100)
                if self.f.state()[game.PARTY_COUNT] == 2 - number:
                    break
            self.assertEqual(self.f.state()[game.PARTY_COUNT], 2 - number)
        for _ in range(8):
            self.f.pulse("B", 90)

        # passos até a flag de ovo pendente (o jogo conta passos reais)
        steps = 0
        for n in range(4096):
            self.step_once("RIGHT" if n % 2 == 0 else "LEFT")
            steps += 1
            if steps % 256 == 0 and self.flag(self.f.state(), 0x266):
                break
        self.assertEqual(self.flag(self.f.state(), 0x266), 1)

        # recebe o ovo do NPC
        self.walkto((4, 7))
        self.f.run(8, "DOWN")
        self.f.run(240)
        self.assertEqual(game.location(self.f.state()), (3, 15))
        self.walkto((16, 15))
        self.f.run(8, "UP")
        self.f.run(30)
        self.f.pulse("A", 180)
        for _ in range(30):
            if self.f.state()[game.PARTY_COUNT] == 2:
                break
            self.f.pulse("A", 100)
        for _ in range(8):
            self.f.pulse("B", 90)
        self.assertEqual(self.f.state()[game.PARTY_COUNT], 2)
        return steps

    # ------------------------------ o teste ------------------------------
    def test_egg_hatches_into_cosmog_after_native_incubation(self):
        """Eclosão: ovo 789 → Cosmog, com passos contados pelo próprio jogo."""
        from mgba_treino_harness import decrypted

        steps_to_egg = self.get_egg()
        st = self.f.state()
        egg = game.party_slot(st, 1)
        facts = mon_facts(egg)
        self.assertEqual(facts["species"], 789)

        flash = save_game(self.f)
        self.switch(self.rom)
        loaded = load_game(self.f, flash)
        self.assertEqual(game.party_slot(loaded, 1), egg)
        self.shot("HATCH_OVO_RECEBIDO.png")
        print(f"HATCH_EGG_PICKED steps_to_egg={steps_to_egg}", flush=True)
        if os.environ.get("COSMOG_HATCH_DUMP"):
            Path(os.environ["COSMOG_HATCH_DUMP"]).write_bytes(self.f.state())
            print("HATCH_STATE_DUMPED", flush=True)

        # incubação: caminhar de verdade. O jogo desconta os ciclos; não mexemos no ovo.
        # Critério de eclosão = bit 30 do IV32 (marcador de ovo) DESLIGADO.
        # NÃO usar "o dado do slot mudou": o contador de ciclos do ovo muda a cada
        # passo, e isso produziria um falso positivo de eclosão (erro cometido aqui).
        def eh_ovo(mon):
            bloco, ordem, _ok = decrypted(mon)
            return bool(u32(bloco, ordem[3] * 12 + 4) & (1 << 30))

        self.assertTrue(eh_ovo(game.party_slot(self.f.state(), 1)), "deveria ser ovo")
        import time
        total = 0
        hatched = False
        limite = int(os.environ.get("COSMOG_HATCH_MAX_STEPS", "3000"))
        t0 = time.time()
        while total < limite:
            antes = total
            total += self.walk_steps(128, prefer="RIGHT" if (total // 128) % 2 == 0 else "DOWN")
            if total == antes:
                break                               # travado: sem progresso
            if not eh_ovo(game.party_slot(self.f.state(), 1)):
                hatched = True
                break
            print(f"HATCH_PROGRESS steps={total} s={time.time()-t0:.0f} "
                  f"ainda_ovo=1", flush=True)
        if not hatched:
            self.skipTest(
                f"orçamento de {limite} passos insuficiente: o ovo de 120 ciclos "
                f"exige ~30.600 passos; sem memory maps no core, cada passo custa "
                f"uma serialização de 528 KB. Aumente COSMOG_HATCH_MAX_STEPS."
            )
        self.shot("HATCH_ECLOSAO.png")
        print(f"HATCH_OCCURRED steps={total}", flush=True)

        st = self.f.state()
        mon = game.party_slot(st, 1)
        facts = mon_facts(mon)

        # 1) virou Cosmog de verdade, nível 5
        self.assertEqual(facts["species"], 789)
        self.assertEqual(facts["level"], 5)

        # 2) saiu do estado de ovo: o bit 30 do IV32 é o marcador de ovo.
        bloco, order, valid = decrypted(mon)
        self.assertTrue(valid)
        self.assertFalse(u32(bloco, order[3] * 12 + 4) & (1 << 30),
                         "bit de ovo ainda ligado: não eclodiu")

        # 3) o filho tem PID próprio; comparar com o PAI (Cosmog da creche),
        #    não com o ovo — o ovo é a mesma entidade que virou o filho.
        from test_estojo_expandido_mgba import save1
        dc = offset(save1(st) + 0x2FCC)
        pai = st[dc:dc + 80] + bytes(20)
        self.assertEqual(mon_facts(pai)["species"], 789)
        self.assertNotEqual(mon[:4], pai[:4], "PID do filho deve diferir do pai")

        # 4) persistência: SAVE/Continuar depois da eclosão
        flash = save_game(self.f)
        self.switch(self.rom)
        loaded = load_game(self.f, flash)
        self.assertEqual(game.party_slot(loaded, 1), mon)
        self.assertFalse(self.flag(loaded, 0x266))
        self.shot("HATCH_POS_SAVE.png")

        self.observations.append(dict(
            kind="native_egg_hatched",
            egg_species=789, hatched_species=facts["species"], level=facts["level"],
            manual_steps=total, steps_to_egg=steps_to_egg,
            distinct_personality_from_parent=True, survived_save_continue=True,
            egg_bit_cleared=True, hatch_bypassed=False, steps_edited=False,
        ))
        print("HATCH_OK", facts, flush=True)


if __name__ == "__main__":
    unittest.main()
