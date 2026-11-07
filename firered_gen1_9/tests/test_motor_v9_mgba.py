"""Testes de integração em mGBA 0.10.5 do motor parcial v9 (apenas saves/estados sintéticos).

MOTOR_V9_ROM=/tmp/firered_gen1_9_work/roms/motor_v9.gba \
MOTOR_V9_BASE=/tmp/firered_gen1_9_work/roms/motor_v8.gba \
MGBA_CORE=/tmp/mgba-build/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v9*.py' -v
"""
from __future__ import annotations

import os
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(ROOT / "tests"))

from mgba_treino_harness import Emulator, PARTY, decrypted, mon, offset, put16, u16, u32
from test_atualizacoes_gen9_mgba import FOE_BATTLE, PLAYER_BATTLE
from test_estojo_expandido_mgba import add, open_case, page, save_after_case
from test_eventos_fixos_mgba import enemy, route_entry_fixture, route_from_entry
from test_golpes_gen9_integracao import load_game, set_exp_and_test_stats
from test_golpes_gen9_mgba import invoke, moves as get_moves, seed_mon
from test_motor_ampliado_mgba import stored_quantity
from test_motor_v7_mgba import bank_off, decode_gba_str
from scripts import motor_v9 as patch

ROM_ENV = os.environ.get("MOTOR_V9_ROM")
BASE_ENV = os.environ.get("MOTOR_V9_BASE")
CORE_ENV = os.environ.get("MGBA_CORE")

DISP_STR = 0x020201B4
BUFF3 = 0x02020300
BATTLER_BY_TURN_ADDR = 0x02021408
SIDE_STATUSES_ADDR = 0x0202161C
SIDE_TIMERS_ADDR = 0x02021620
STATUSES3_ADDR = 0x02021638
DISABLE_STRUCTS_REAL_ADDR = 0x02021648
BATTLE_WEATHER_ADDR = 0x0202175C
WEATHER_DURATION_ADDR = 0x02021788
ENEMY_PARTY_COUNT = 0x0203A730
PLAYER_PARTY_COUNT = 0x0203A731
ENEMY_PARTY_ADDR = 0x0203A734
V7_STATE_ADDR = 0x0203FC00
V8_STATE_ADDR = 0x0203FC60
V9_STATE_ADDR = 0x0203FCA0

STATUS2_SUBSTITUTE = 0x01000000
STATUS2_ESCAPE_PREVENTION = 0x04000000
STATUS3_GASTRO_ACID = 0x00010000


@unittest.skipUnless(ROM_ENV and BASE_ENV and CORE_ENV, "defina MOTOR_V9_ROM, MOTOR_V9_BASE e MGBA_CORE")
class MotorV9MGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM_ENV).resolve()
        cls.base = Path(BASE_ENV).resolve()
        cls.core = Path(CORE_ENV).resolve()
        if cls.rom.read_bytes() != patch.build(cls.base.read_bytes()):
            raise ValueError("ROM motor_v9 diverge da reconstrução determinística")
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        cls.f = Emulator(cls.rom, cls.core, cls.dir)
        cls.fixture = route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()
        cls.two_party_battle_fixture = cls._make_two_party_singles_fixture()
        cls.doubles_fixture = cls._make_doubles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    @classmethod
    def _enter_wild_encounter(cls, state: bytearray, *, doubles: bool = False) -> bytes:
        cls.f.restore(bytes(state))
        route_from_entry(cls.f)
        found = False
        for _ in range(120):
            for btn in ("LEFT", "RIGHT"):
                for _step in range(20):
                    cls.f.run(1, btn)
                    st = bytearray(cls.f.state())
                    if enemy(st)["valid"] and enemy(st)["species"] != 390:
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            raise AssertionError("Sem encontro selvagem para fixture de batalha")

        if doubles:
            for _ in range(250):
                st = bytearray(cls.f.state())
                bt = u32(st, offset(0x02020374))
                if bt == 0x04:
                    e0 = bytes(st[offset(ENEMY_PARTY_ADDR) : offset(ENEMY_PARTY_ADDR) + 100])
                    st[offset(ENEMY_PARTY_ADDR + 100) : offset(ENEMY_PARTY_ADDR + 200)] = e0
                    st[offset(ENEMY_PARTY_COUNT)] = 2
                    struct.pack_into("<I", st, offset(0x02020374), bt | 0x01)
                    cls.f.restore(bytes(st))
                    break
                cls.f.run(1)

        cls.f.run(400)
        for _ in range(10 if doubles else 6):
            cls.f.pulse("B", 45)
        return bytes(cls.f.state())

    @classmethod
    def _make_singles_fixture(cls) -> bytes:
        state = bytearray(seed_mon(cls.fixture, 1, 10, (486, 33, 52, 150)))
        set_exp_and_test_stats(state, 1, 10)
        return cls._enter_wild_encounter(state)

    @classmethod
    def _make_two_party_singles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (460, 770, 361, 150)))
        set_exp_and_test_stats(s1, 1, 10)
        put16(s1, offset(PARTY) + 86, 160)
        put16(s1, offset(PARTY) + 88, 160)
        s2 = bytearray(seed_mon(cls.fixture, 6, 10, (33, 52, 150, 150)))
        set_exp_and_test_stats(s2, 6, 10)
        put16(s2, offset(PARTY) + 86, 160)
        put16(s2, offset(PARTY) + 88, 160)
        s1[offset(PARTY + 100) : offset(PARTY + 200)] = s2[offset(PARTY) : offset(PARTY) + 100]
        s1[offset(PLAYER_PARTY_COUNT)] = 2
        return cls._enter_wild_encounter(s1)

    @classmethod
    def _make_doubles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (684, 494, 510, 759)))
        set_exp_and_test_stats(s1, 1, 10)
        s2 = bytearray(seed_mon(cls.fixture, 4, 10, (33, 150, 150, 150)))
        set_exp_and_test_stats(s2, 4, 10)
        s1[offset(PARTY + 100) : offset(PARTY + 200)] = s2[offset(PARTY) : offset(PARTY) + 100]
        s1[offset(PLAYER_PARTY_COUNT)] = 2
        return cls._enter_wild_encounter(s1, doubles=True)

    def setUp(self):
        self.f.restore(self.fixture)

    def _duel_state(
        self,
        move_id: int,
        *,
        move2_id: int = 150,
        foe_move: int = 150,
        p_species: int | None = None,
        p_hp: int = 160,
        p_max: int = 160,
        p_atk: int = 200,
        p_def: int = 130,
        p_spa: int = 200,
        p_spd_stat: int = 130,
        p_speed: int = 300,
        p_types: tuple[int, int] = (0, 0),
        p_ability: int = 4,
        p_item: int = 0,
        p_status1: int = 0,
        f_species: int | None = None,
        f_hp: int = 480,
        f_max: int = 480,
        f_atk: int = 180,
        f_def: int = 140,
        f_spa: int = 180,
        f_spd_stat: int = 140,
        f_speed: int = 40,
        f_types: tuple[int, int] = (0, 0),
        f_ability: int = 4,
        f_item: int = 0,
        f_status1: int = 0,
        acc_stage: int = 12,
        eva_stage: int = 6,
        base_state: bytes | None = None,
    ) -> bytes:
        st = bytearray(self.battle_fixture if base_state is None else base_state)
        if p_species is not None:
            put16(st, PLAYER_BATTLE + 0x00, p_species)
        if f_species is not None:
            put16(st, FOE_BATTLE + 0x00, f_species)
        put16(st, PLAYER_BATTLE + 0x0C, move_id)
        put16(st, PLAYER_BATTLE + 0x0E, move2_id)
        st[PLAYER_BATTLE + 0x25] = 20
        st[PLAYER_BATTLE + 0x26] = 20
        put16(st, PLAYER_BATTLE + 0x2A, p_hp)
        put16(st, PLAYER_BATTLE + 0x2E, p_max)
        put16(st, offset(PARTY) + 86, p_hp)
        put16(st, offset(PARTY) + 88, p_max)
        for i in range(1, 8):
            st[PLAYER_BATTLE + 0x18 + i] = 6
            st[FOE_BATTLE + 0x18 + i] = 6
        st[PLAYER_BATTLE + 0x1E] = acc_stage
        st[FOE_BATTLE + 0x1F] = eva_stage
        put16(st, PLAYER_BATTLE + 0x02, p_atk)
        put16(st, PLAYER_BATTLE + 0x04, p_def)
        put16(st, PLAYER_BATTLE + 0x06, p_speed)
        put16(st, PLAYER_BATTLE + 0x08, p_spa)
        put16(st, PLAYER_BATTLE + 0x0A, p_spd_stat)
        put16(st, PLAYER_BATTLE + 0x20, p_ability)
        st[PLAYER_BATTLE + 0x22], st[PLAYER_BATTLE + 0x23] = p_types
        st[PLAYER_BATTLE + 0x2C] = 10
        put16(st, PLAYER_BATTLE + 0x30, p_item)
        struct.pack_into("<I", st, PLAYER_BATTLE + 0x50, p_status1)
        struct.pack_into("<I", st, PLAYER_BATTLE + 0x54, 0)
        struct.pack_into("<I", st, offset(PARTY) + 80, p_status1)

        for mslot in range(4):
            put16(st, FOE_BATTLE + 0x0C + 2 * mslot, foe_move)
            st[FOE_BATTLE + 0x25 + mslot] = 40
        put16(st, FOE_BATTLE + 0x02, f_atk)
        put16(st, FOE_BATTLE + 0x04, f_def)
        put16(st, FOE_BATTLE + 0x06, f_speed)
        put16(st, FOE_BATTLE + 0x08, f_spa)
        put16(st, FOE_BATTLE + 0x0A, f_spd_stat)
        put16(st, FOE_BATTLE + 0x20, f_ability)
        st[FOE_BATTLE + 0x22], st[FOE_BATTLE + 0x23] = f_types
        put16(st, FOE_BATTLE + 0x2A, f_hp)
        put16(st, FOE_BATTLE + 0x2E, f_max)
        put16(st, FOE_BATTLE + 0x30, f_item)
        struct.pack_into("<I", st, FOE_BATTLE + 0x50, f_status1)
        struct.pack_into("<I", st, FOE_BATTLE + 0x54, 0)
        struct.pack_into("<I", st, offset(ENEMY_PARTY_ADDR) + 80, f_status1)

        st[offset(SIDE_STATUSES_ADDR) : offset(SIDE_STATUSES_ADDR) + 4] = b"\x00" * 4
        st[offset(SIDE_TIMERS_ADDR) : offset(SIDE_TIMERS_ADDR) + 24] = b"\x00" * 24
        st[offset(STATUSES3_ADDR) : offset(STATUSES3_ADDR) + 16] = b"\x00" * 16
        st[offset(DISABLE_STRUCTS_REAL_ADDR) : offset(DISABLE_STRUCTS_REAL_ADDR) + 112] = b"\x00" * 112
        put16(st, offset(BATTLE_WEATHER_ADDR), 0)
        st[offset(WEATHER_DURATION_ADDR)] = 0
        st[offset(V7_STATE_ADDR) : offset(V7_STATE_ADDR) + 96] = b"\x00" * 96
        st[offset(V8_STATE_ADDR) : offset(V8_STATE_ADDR) + 64] = b"\x00" * 64
        st[offset(V9_STATE_ADDR) : offset(V9_STATE_ADDR) + 192] = b"\x00" * 192
        st[offset(BUFF3)] = 0xAA
        return bytes(st)

    def _run_turn(self, state: bytes, *, slot: int = 0, frames: int = 980) -> tuple[bytes, list[str]]:
        self.f.restore(state)
        seen: list[str] = []
        self.f.pulse("A", 25)
        if slot == 1:
            self.f.pulse("RIGHT", 15)
        self.f.run(6, "A")
        for _ in range(frames):
            self.f.run(1)
            cur = self.f.state()
            txt = decode_gba_str(cur[offset(DISP_STR) : offset(DISP_STR) + 80])
            if txt and (not seen or seen[-1] != txt):
                seen.append(txt)
        return self.f.state(), seen

    def test_familia_a_tipos_terceiro_tipo_tar_shot_e_electrify(self):
        # 1. Soak (486) muda Fire -> Water puro e falha se ja for Water puro; Magic Powder (675) -> Psychic puro
        soak_ok, seen = self._run_turn(self._duel_state(486, f_types=(10, 10)))
        self.assertEqual((soak_ok[FOE_BATTLE + 0x22], soak_ok[FOE_BATTLE + 0x23]), (11, 11))
        self.assertTrue(any("gua!" in s for s in seen), seen)

        soak_fail, seen_f = self._run_turn(self._duel_state(486, f_types=(11, 11)))
        self.assertTrue(any("falhou" in s.lower() for s in seen_f), seen_f)

        mp_ok, _ = self._run_turn(self._duel_state(675, f_types=(0, 0)))
        self.assertEqual((mp_ok[FOE_BATTLE + 0x22], mp_ok[FOE_BATTLE + 0x23]), (14, 14))

        # 2. Reflect Type (512): usuario copia os dois tipos do alvo (Fire/Flying = 10, 2)
        rt_ok, _ = self._run_turn(self._duel_state(512, p_types=(0, 0), f_types=(10, 2)))
        self.assertEqual((rt_ok[PLAYER_BATTLE + 0x22], rt_ok[PLAYER_BATTLE + 0x23]), (10, 2))

        # 3. Trick-or-Treat (563): adiciona Ghost ao alvo Grass -> Tackle (33, Normal) no turno 2 causa 0 dano
        tot_t1, _ = self._run_turn(self._duel_state(563, move2_id=33, f_types=(12, 12)))
        tot_t2, seen_t2 = self._run_turn(tot_t1, slot=1)
        self.assertEqual(u16(tot_t2, FOE_BATTLE + 0x2A), 480)
        self.assertTrue(any("afeta" in s.lower() for s in seen_t2), seen_t2)

        # 4. Forest's Curse (567) e Tar Shot (674): dobram o dano de Ember (52, Fire) sobre alvo Normal
        ember_base, _ = self._run_turn(self._duel_state(52, p_types=(10, 10), f_types=(0, 0)))
        base_dmg = 480 - u16(ember_base, FOE_BATTLE + 0x2A)

        fc_t1, _ = self._run_turn(self._duel_state(567, move2_id=52, p_types=(10, 10), f_types=(0, 0)))
        fc_t2, _ = self._run_turn(fc_t1, slot=1)
        self.assertGreaterEqual(480 - u16(fc_t2, FOE_BATTLE + 0x2A), base_dmg * 2 - 2)

        ts_t1, _ = self._run_turn(
            self._duel_state(674, move2_id=52, p_types=(10, 10), f_types=(0, 0)),
            frames=1300,
        )
        self.assertEqual(ts_t1[FOE_BATTLE + 0x18 + 3], 5)
        ts_t2, _ = self._run_turn(ts_t1, slot=1, frames=1100)
        self.assertGreaterEqual(480 - u16(ts_t2, FOE_BATTLE + 0x2A), base_dmg * 2 - 2)

        # 5. Electrify (578): eletrifica o Tackle (33) do oponente mais lento -> 0 dano contra usuario Ground (4, 4)
        el_res, _ = self._run_turn(
            self._duel_state(578, foe_move=33, p_types=(4, 4), p_speed=300, f_speed=40)
        )
        self.assertEqual(u16(el_res, PLAYER_BATTLE + 0x2A), 160)

    def test_familia_b_swaps_splits_topsy_turvy_e_boosts_compostos(self):
        # 1. Power Trick (379) e Speed Swap (638)
        pt_res, _ = self._run_turn(self._duel_state(379, p_atk=240, p_def=90))
        self.assertEqual((u16(pt_res, PLAYER_BATTLE + 0x02), u16(pt_res, PLAYER_BATTLE + 0x04)), (90, 240))

        ss_res, _ = self._run_turn(self._duel_state(638, p_speed=300, f_speed=40))
        self.assertEqual((u16(ss_res, PLAYER_BATTLE + 0x06), u16(ss_res, FOE_BATTLE + 0x06)), (40, 300))

        # 2. Power Swap (384), Guard Swap (385), Heart Swap (391) e Topsy-Turvy (572)
        st_ps = bytearray(self._duel_state(384))
        st_ps[PLAYER_BATTLE + 0x18 + 1] = 9
        st_ps[PLAYER_BATTLE + 0x18 + 4] = 4
        st_ps[FOE_BATTLE + 0x18 + 1] = 3
        st_ps[FOE_BATTLE + 0x18 + 4] = 8
        ps_res, _ = self._run_turn(bytes(st_ps))
        self.assertEqual((ps_res[PLAYER_BATTLE + 0x18 + 1], ps_res[PLAYER_BATTLE + 0x18 + 4]), (3, 8))
        self.assertEqual((ps_res[FOE_BATTLE + 0x18 + 1], ps_res[FOE_BATTLE + 0x18 + 4]), (9, 4))

        st_tt = bytearray(self._duel_state(572))
        st_tt[FOE_BATTLE + 0x18 + 1] = 9   # +3 -> -3 (3)
        st_tt[FOE_BATTLE + 0x18 + 2] = 4   # -2 -> +2 (8)
        tt_res, _ = self._run_turn(bytes(st_tt))
        self.assertEqual((tt_res[FOE_BATTLE + 0x18 + 1], tt_res[FOE_BATTLE + 0x18 + 2]), (3, 8))

        # 3. Guard Split (469) e Power Split (470): media inteira entre usuario e alvo
        gs_res, _ = self._run_turn(self._duel_state(469, p_def=240, f_def=100, p_spd_stat=200, f_spd_stat=80))
        self.assertEqual((u16(gs_res, PLAYER_BATTLE + 0x04), u16(gs_res, FOE_BATTLE + 0x04)), (170, 170))
        self.assertEqual((u16(gs_res, PLAYER_BATTLE + 0x0A), u16(gs_res, FOE_BATTLE + 0x0A)), (140, 140))

        # 4. Toxic Thread (627) + Venom Drench (595)
        tx_res, _ = self._run_turn(self._duel_state(627, move2_id=595, f_types=(0, 0)), frames=1600)
        self.assertEqual(tx_res[FOE_BATTLE + 0x18 + 3], 5)
        self.assertEqual(u32(tx_res, FOE_BATTLE + 0x50) & 0x08, 0x08)
        vd_res, _ = self._run_turn(tx_res, slot=1, frames=1600)
        self.assertEqual(
            (vd_res[FOE_BATTLE + 0x18 + 1], vd_res[FOE_BATTLE + 0x18 + 4], vd_res[FOE_BATTLE + 0x18 + 3]),
            (5, 5, 4),
        )

        # 5. No Retreat (673), Clangorous Soul (682), Fillet Away (760), Take Heart (743), Spicy Extract (750) e Acupressure (367)
        nr_t1, _ = self._run_turn(self._duel_state(673), frames=1950)
        for s in range(1, 6):
            self.assertEqual(nr_t1[PLAYER_BATTLE + 0x18 + s], 7)
        self.assertTrue(u32(nr_t1, PLAYER_BATTLE + 0x54) & STATUS2_ESCAPE_PREVENTION)
        nr_t2, seen_nr2 = self._run_turn(nr_t1)
        self.assertTrue(any("falhou" in s.lower() for s in seen_nr2), seen_nr2)

        cs_ok, _ = self._run_turn(self._duel_state(682, p_hp=180, p_max=180), frames=1950)
        self.assertEqual(u16(cs_ok, PLAYER_BATTLE + 0x2A), 120)
        for s in range(1, 6):
            self.assertEqual(cs_ok[PLAYER_BATTLE + 0x18 + s], 7)
        cs_fail, _ = self._run_turn(self._duel_state(682, p_hp=60, p_max=180))
        self.assertEqual(u16(cs_fail, PLAYER_BATTLE + 0x2A), 60)

        fa_ok, _ = self._run_turn(self._duel_state(760, p_hp=180, p_max=180), frames=1500)
        self.assertEqual(u16(fa_ok, PLAYER_BATTLE + 0x2A), 90)
        self.assertEqual(
            (fa_ok[PLAYER_BATTLE + 0x18 + 1], fa_ok[PLAYER_BATTLE + 0x18 + 4], fa_ok[PLAYER_BATTLE + 0x18 + 3]),
            (8, 8, 8),
        )

        th_ok, _ = self._run_turn(self._duel_state(743, p_status1=0x10), frames=1350)
        self.assertEqual(u32(th_ok, PLAYER_BATTLE + 0x50), 0)
        self.assertEqual((th_ok[PLAYER_BATTLE + 0x18 + 4], th_ok[PLAYER_BATTLE + 0x18 + 5]), (7, 7))

        se_ok, _ = self._run_turn(self._duel_state(750), frames=1350)
        self.assertEqual((se_ok[FOE_BATTLE + 0x18 + 1], se_ok[FOE_BATTLE + 0x18 + 2]), (8, 4))

        ac_ok, _ = self._run_turn(self._duel_state(367, acc_stage=6))
        self.assertEqual(sum(ac_ok[PLAYER_BATTLE + 0x18 + i] for i in range(1, 8)), 44)

        # 6. Flower Shield (575), Rototiller (559) e Gear Up (629) c/ Plus (57)
        fs_ok, _ = self._run_turn(self._duel_state(575, p_types=(12, 12), f_types=(12, 2)), frames=1350)
        self.assertEqual((fs_ok[PLAYER_BATTLE + 0x18 + 2], fs_ok[FOE_BATTLE + 0x18 + 2]), (7, 7))

        ro_ok, _ = self._run_turn(self._duel_state(559, p_types=(12, 12), f_types=(12, 2)), frames=1350)
        self.assertEqual((ro_ok[PLAYER_BATTLE + 0x18 + 1], ro_ok[FOE_BATTLE + 0x18 + 1]), (7, 6))

        gu_ok, _ = self._run_turn(self._duel_state(629, p_ability=57), frames=1350)
        self.assertEqual((gu_ok[PLAYER_BATTLE + 0x18 + 1], gu_ok[PLAYER_BATTLE + 0x18 + 4]), (7, 7))

    def test_familia_c_aqua_ring_strength_sap_purify_psycho_shift_jungle_dark_void(self):
        # 1. Aqua Ring (392): cura 1/16 max HP (10 em 160) no fim do turno
        ar_res, _ = self._run_turn(self._duel_state(392, p_hp=100, p_max=160))
        self.assertEqual(u16(ar_res, PLAYER_BATTLE + 0x2A), 110)

        # 2. Strength Sap (623): reduz Atk do alvo (-1) e cura pelo Atk efetivo anterior (80); Liquid Ooze (64) fere
        ss_heal, _ = self._run_turn(self._duel_state(623, p_hp=50, p_max=160, f_atk=80))
        self.assertEqual(ss_heal[FOE_BATTLE + 0x18 + 1], 5)
        self.assertEqual(u16(ss_heal, PLAYER_BATTLE + 0x2A), 130)

        ss_ooze, _ = self._run_turn(self._duel_state(623, p_hp=130, p_max=160, f_atk=80, f_ability=64))
        self.assertEqual(u16(ss_ooze, PLAYER_BATTLE + 0x2A), 50)

        # 3. Psycho Shift (375): transfere Burn (0x10) do usuario para o oponente e limpa o usuario
        ps_res, _ = self._run_turn(self._duel_state(375, p_status1=0x10, f_status1=0))
        self.assertEqual(u32(ps_res, PLAYER_BATTLE + 0x50), 0)
        self.assertEqual(u32(ps_res, FOE_BATTLE + 0x50), 0x10)

        # 4. Purify (640) e Jungle Healing (710)
        pu_ok, _ = self._run_turn(self._duel_state(640, p_hp=60, p_max=160, f_status1=0x08))
        self.assertEqual(u32(pu_ok, FOE_BATTLE + 0x50), 0)
        self.assertEqual(u16(pu_ok, PLAYER_BATTLE + 0x2A), 140)

        jh_ok, _ = self._run_turn(self._duel_state(710, p_hp=80, p_max=160, p_status1=0x40))
        self.assertEqual(u32(jh_ok, PLAYER_BATTLE + 0x50), 0)
        self.assertEqual(u16(jh_ok, PLAYER_BATTLE + 0x2A), 120)

        # 5. Dark Void (463): falha fora de Darkrai (491) e adormece quando usado por Darkrai (491)
        dv_fail, seen_dv = self._run_turn(self._duel_state(463, p_species=1))
        self.assertEqual(u32(dv_fail, FOE_BATTLE + 0x50), 0)
        self.assertTrue(any("consegue" in s.lower() for s in seen_dv), seen_dv)

        dv_ok, _ = self._run_turn(self._duel_state(463, p_species=491, acc_stage=12, eva_stage=0))
        self.assertTrue(u32(dv_ok, FOE_BATTLE + 0x50) & 0x07)

    def test_familia_c2_lunar_dance_e_shed_tail_troca_real(self):
        # 1. Lunar Dance (460): sacrifica slot 0 e ao entrar slot 1 restaura HP total, cura status e restaura PP!
        st_ld = bytearray(self._duel_state(460, base_state=self.two_party_battle_fixture))
        put16(st_ld, offset(PARTY + 100) + 86, 40)
        put16(st_ld, offset(PARTY + 100) + 88, 160)
        struct.pack_into("<I", st_ld, offset(PARTY + 100) + 80, 0x10)  # Burn no slot 1
        # Reduz PP do slot 0 de golpes do aliado reserva usando SetMonData p/ checksum valido
        s2_low = bytearray(seed_mon(self.fixture, 6, 10, (33, 52, 150, 150)))
        set_exp_and_test_stats(s2_low, 6, 10)
        put16(s2_low, offset(PARTY) + 86, 40)
        put16(s2_low, offset(PARTY) + 88, 160)
        struct.pack_into("<I", s2_low, offset(PARTY) + 80, 0x10)
        s2_low[offset(BUFF3)] = 2
        s2_low = bytearray(invoke(self.f, bytes(s2_low), 0x0810AF78, {0: PARTY, 1: 0x11, 2: BUFF3}))
        st_ld[offset(PARTY + 100) : offset(PARTY + 200)] = s2_low[offset(PARTY) : offset(PARTY) + 100]

        self.f.restore(bytes(st_ld))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        # Em batalha selvagem: dispensa "A desmaiou!<fb>", confirma "Usar próximo POKéMON?" e escolhe slot 1
        self.f.run(420)
        self.f.pulse("A", 40)
        self.f.run(120)
        self.f.pulse("A", 40)
        self.f.run(220)
        self.f.pulse("DOWN", 35)
        self.f.pulse("A", 40)
        self.f.pulse("A", 40)
        self.f.run(750)
        after_ld = self.f.state()
        self.assertEqual(u16(after_ld, PLAYER_BATTLE + 0x00), 6)
        self.assertEqual(u16(after_ld, PLAYER_BATTLE + 0x2A), 160)
        self.assertEqual(u32(after_ld, PLAYER_BATTLE + 0x50), 0)
        self.assertEqual(after_ld[PLAYER_BATTLE + 0x25], 56)  # 35 base PP + 3 PP Ups = 56
        self.assertEqual(u16(after_ld, offset(PARTY + 100) + 86), 160)
        self.assertEqual(u32(after_ld, offset(PARTY + 100) + 80), 0)
        ld_blk, ld_ord, ld_valid = decrypted(mon(after_ld, slot=1))
        self.assertTrue(ld_valid)
        self.assertEqual(ld_blk[ld_ord[1] * 12 + 8], 56)

        # 2. Shed Tail (770): consome 50% do HP (160 -> 80), faz pivot p/ slot 1 e transfere Substitute (40 HP)
        st_sh = bytearray(self._duel_state(770, move2_id=770, base_state=self.two_party_battle_fixture))
        self.f.restore(bytes(st_sh))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(680)
        self.f.pulse("DOWN", 30)
        self.f.pulse("A", 35)
        self.f.pulse("A", 35)
        self.f.run(680)
        after_sh = self.f.state()
        self.assertEqual(u16(after_sh, PLAYER_BATTLE + 0x00), 6)
        self.assertEqual(u16(after_sh, offset(PARTY) + 86), 80)
        self.assertTrue(u32(after_sh, PLAYER_BATTLE + 0x54) & STATUS2_SUBSTITUTE)
        self.assertEqual(after_sh[offset(DISABLE_STRUCTS_REAL_ADDR) + 0x0A], 40)

    def test_familia_d_e_f_habilidades_copycat_laser_final_gambit_natural_gift_salas_e_duplas(self):
        # 1. Gastro Acid (380), Worry Seed (388) e Entrainment (493)
        ga_res, _ = self._run_turn(self._duel_state(380, f_ability=26))
        self.assertEqual(ga_res[FOE_BATTLE + 0x20], 0)
        self.assertTrue(u32(ga_res, offset(STATUSES3_ADDR) + 4) & STATUS3_GASTRO_ACID)

        ws_res, _ = self._run_turn(self._duel_state(388, f_ability=26, f_status1=3))
        self.assertEqual(ws_res[FOE_BATTLE + 0x20], 15)  # Insomnia
        self.assertEqual(u32(ws_res, FOE_BATTLE + 0x50), 0)

        en_res, _ = self._run_turn(self._duel_state(493, p_ability=22, f_ability=26))
        self.assertEqual(en_res[FOE_BATTLE + 0x20], 22)

        # 2. Copycat (383): oponente mais rapido usa Tackle (33) -> usuario mais lento copia Tackle contra ele
        cc_res, _ = self._run_turn(
            self._duel_state(383, foe_move=33, p_speed=40, f_speed=300, p_atk=220, f_def=120)
        )
        self.assertLess(u16(cc_res, FOE_BATTLE + 0x2A), 480)

        # 3. Laser Focus (628): garante golpe critico no turno seguinte contra alvo sem Battle Armor (f_ability=1)
        norm_hit, _ = self._run_turn(self._duel_state(33, f_ability=1, p_atk=200, f_def=140))
        norm_dmg = 480 - u16(norm_hit, FOE_BATTLE + 0x2A)
        lf_t1, _ = self._run_turn(self._duel_state(628, move2_id=33, f_ability=1, p_atk=200, f_def=140))
        lf_t2, seen_lf = self._run_turn(lf_t1, slot=1)
        crit_dmg = 480 - u16(lf_t2, FOE_BATTLE + 0x2A)
        self.assertGreaterEqual(crit_dmg, int(norm_dmg * 1.7))

        # 4. Final Gambit (514): causa dano exato igual ao HP do usuario (135) e desmaia; falha vs Ghost sem desmaiar
        fg_ok, _ = self._run_turn(self._duel_state(514, p_hp=135, p_max=160, f_hp=480, f_max=480))
        self.assertEqual(u16(fg_ok, PLAYER_BATTLE + 0x2A), 0)
        self.assertEqual(u16(fg_ok, FOE_BATTLE + 0x2A), 480 - 135)

        fg_ghost, _ = self._run_turn(self._duel_state(514, p_hp=135, p_max=160, f_types=(7, 7)))
        self.assertEqual(u16(fg_ghost, PLAYER_BATTLE + 0x2A), 135)
        self.assertEqual(u16(fg_ghost, FOE_BATTLE + 0x2A), 480)

        # 5. Natural Gift (363) c/ Cheri Berry (133 -> Fire 80 BP): consome Berry e causa dano super efetivo em Grass
        st_ng = bytearray(seed_mon(self.fixture, 1, 10, (363, 33, 150, 150)))
        set_exp_and_test_stats(st_ng, 1, 10)
        put16(st_ng, offset(BUFF3), 133)
        st_ng = bytearray(invoke(self.f, bytes(st_ng), 0x0810AF78, {0: PARTY, 1: 0x0C, 2: BUFF3}))
        ng_battle = bytearray(self._duel_state(363, p_item=133, f_types=(12, 12)))
        ng_battle[offset(PARTY) : offset(PARTY) + 100] = st_ng[offset(PARTY) : offset(PARTY) + 100]
        ng_res, _ = self._run_turn(bytes(ng_battle))
        self.assertLess(u16(ng_res, FOE_BATTLE + 0x2A), 460)
        self.assertEqual(u16(ng_res, PLAYER_BATTLE + 0x30), 0)
        ng_blk, ng_ord, ng_valid = decrypted(mon(ng_res, slot=0))
        self.assertTrue(ng_valid)
        self.assertEqual(u16(ng_blk, ng_ord[0] * 12 + 2), 0)

        # 6. Magic Room (477) suprime Choice Band (186), Octolock (678) reduz Def/SpD e Fairy Lock (583) trava proximo turno
        cb_no_mr, _ = self._run_turn(self._duel_state(33, p_item=186, p_atk=240, f_def=120))
        st_mr = bytearray(self._duel_state(477, move2_id=33, p_item=186, p_atk=240, f_def=120))
        mr_t1, _ = self._run_turn(bytes(st_mr))
        self.assertEqual(mr_t1[offset(V9_STATE_ADDR) + 8], 4)  # magic_room_turns apos decremento do turno 1
        mr_t2, _ = self._run_turn(mr_t1, slot=1)
        self.assertGreater(480 - u16(cb_no_mr, FOE_BATTLE + 0x2A), 480 - u16(mr_t2, FOE_BATTLE + 0x2A) + 4)

        oct_res, _ = self._run_turn(self._duel_state(678), frames=1500)
        self.assertTrue(u32(oct_res, FOE_BATTLE + 0x54) & STATUS2_ESCAPE_PREVENTION)
        self.assertEqual((oct_res[FOE_BATTLE + 0x18 + 2], oct_res[FOE_BATTLE + 0x18 + 5]), (5, 5))

        fl_t1, _ = self._run_turn(self._duel_state(583, move2_id=150))
        self.assertEqual(fl_t1[offset(V9_STATE_ADDR) + 9], 2)  # fairy_lock_turns ativo p/ o proximo turno
        fl_t2, _ = self._run_turn(fl_t1, slot=1)
        self.assertTrue(u32(fl_t2, PLAYER_BATTLE + 0x54) & STATUS2_ESCAPE_PREVENTION)
        self.assertTrue(u32(fl_t2, FOE_BATTLE + 0x54) & STATUS2_ESCAPE_PREVENTION)

        # 7. Duplas: Decorate (684), Quash (510), After You (494) e Doodle (759)
        st_dbl = bytearray(self.doubles_fixture)
        b0, b1, b2, b3 = (bank_off(i) for i in range(4))
        for b in (b0, b1, b2, b3):
            for s in range(1, 8):
                st_dbl[b + 0x18 + s] = 6
            put16(st_dbl, b + 0x20, 4)
            for mslot in range(4):
                put16(st_dbl, b + 0x0C + 2 * mslot, 150)
                st_dbl[b + 0x25 + mslot] = 20
        put16(st_dbl, b0 + 0x0C, 684)  # slot 0: Decorate
        put16(st_dbl, b0 + 0x0E, 510)  # slot 1: Quash
        put16(st_dbl, b0 + 0x10, 494)  # slot 2: After You
        put16(st_dbl, b0 + 0x12, 759)  # slot 3: Doodle
        put16(st_dbl, b1 + 0x20, 3)    # oponente b1 com Speed Boost (3)
        put16(st_dbl, b0 + 0x06, 350)
        put16(st_dbl, b2 + 0x06, 60)
        put16(st_dbl, b1 + 0x06, 280)
        put16(st_dbl, b3 + 0x06, 120)
        st_dbl[offset(V9_STATE_ADDR) : offset(V9_STATE_ADDR) + 192] = b"\x00" * 192

        # Decorate mirando no aliado (DOWN na selecao de alvo em Duplas mira no parceiro b2)
        self.f.restore(bytes(st_dbl))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("DOWN", 15)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(1250)
        dec_end = self.f.state()
        self.assertEqual((dec_end[b2 + 0x18 + 1], dec_end[b2 + 0x18 + 4]), (8, 8))

        # Quash (slot 1 -> RIGHT) mirando no oponente b1 (Speed 280) empurra b1 p/ ultimo em gBattlerByTurnOrder
        self.f.restore(bytes(st_dbl))
        self.f.pulse("A", 25)
        self.f.pulse("RIGHT", 15)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(1100)
        quash_end = self.f.state()
        order = list(quash_end[offset(BATTLER_BY_TURN_ADDR) : offset(BATTLER_BY_TURN_ADDR) + 4])
        self.assertEqual(order[-1], 1, order)

        # After You (slot 2 -> DOWN) mirando no aliado b2 (Speed 60) adianta b2 p/ segundo lugar antes de b1 (280) e b3 (120)
        self.f.restore(bytes(st_dbl))
        self.f.pulse("A", 25)
        self.f.pulse("DOWN", 15)
        self.f.pulse("A", 25)
        self.f.pulse("DOWN", 15)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(1100)
        ay_end = self.f.state()
        ay_order = list(ay_end[offset(BATTLER_BY_TURN_ADDR) : offset(BATTLER_BY_TURN_ADDR) + 4])
        self.assertEqual(ay_order[:2], [0, 2], ay_order)

        # Doodle (slot 3 -> DOWN + RIGHT) mirando em b1 copia Speed Boost (3) p/ b0 e aliado b2
        self.f.restore(bytes(st_dbl))
        self.f.pulse("A", 25)
        self.f.pulse("DOWN", 15)
        self.f.pulse("RIGHT", 15)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(1100)
        dd_end = self.f.state()
        self.assertEqual((u16(dd_end, b0 + 0x20), u16(dd_end, b2 + 0x20)), (3, 3))

    def test_regressao_estojo_229_tms_hms_motor_v8_e_save_sintetico(self):
        # 0. Subida de nivel real (MonTryLearningNewMove @ 0x08109790) nos golpes restaurados pelo motor_v9
        for species, lv, want_moves in (
            (1, 30, (388,)),        # Bulbasaur -> Worry Seed
            (488, 72, (460, 742)),  # Cresselia -> Lunar Dance + Lunar Blessing no nv. 72!
            (491, 66, (463,)),      # Darkrai -> Dark Void
            (967, 31, (770,)),      # Cyclizar -> Shed Tail
            (976, 30, (760,)),      # Veluza -> Fillet Away
        ):
            st_lv = seed_mon(self.fixture, species, lv, (33, 45, 0, 0))
            out_lv = invoke(self.f, st_lv, 0x08109790, {0: PARTY, 1: 1})
            if len(want_moves) == 2:
                out_lv = invoke(self.f, out_lv, 0x08109790, {0: PARTY, 1: 0})
                self.assertEqual(get_moves(out_lv), (33, 45, want_moves[0], want_moves[1]))
            else:
                self.assertEqual(get_moves(out_lv), (33, 45, want_moves[0], 0))

        # 1. Regressão motor_v8 encadeado: Snowscape (773) continua ativando neve sem dano residual
        snow_res, _ = self._run_turn(self._duel_state(773, p_types=(10, 10), f_types=(12, 12)))
        self.assertEqual(u16(snow_res, offset(BATTLE_WEATHER_ADDR)), 0x0100)
        self.assertEqual(snow_res[offset(WEATHER_DURATION_ADDR)], 4)

        # 2. Estojo v2 com 229 TMs SV + HM01 infinito + persistencia em save sintetico
        st = bytes(self.fixture)
        st = add(self.f, st, 339, 1)   # HM01 Cut
        st = add(self.f, st, 426, 2)   # TM052 Snowscape
        st = add(self.f, st, 552, 1)   # TM178 Gravity
        self.f.restore(st)
        open_case(self.f)
        self.assertEqual(page(self.f.state()), 0)
        flash = save_after_case(self.f)

        core2 = Path(shutil.copy2(self.core, self.dir / "mgba_reload.so"))
        reloaded = Emulator(self.rom, core2, self.dir)
        try:
            load_game(reloaded, flash)
            s_after = reloaded.state()
            self.assertEqual(stored_quantity(s_after, 339), 1)
            self.assertEqual(stored_quantity(s_after, 426), 2)
            self.assertEqual(stored_quantity(s_after, 552), 1)
        finally:
            reloaded.close()


if __name__ == "__main__":
    unittest.main()
