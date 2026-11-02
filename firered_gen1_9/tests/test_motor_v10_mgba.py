"""Testes de integração em mGBA 0.10.5 do motor parcial v10 (apenas saves/estados sintéticos).

MOTOR_V10_ROM=/tmp/firered_gen1_9_work/roms/motor_v10.gba \
MOTOR_V10_BASE=/tmp/firered_gen1_9_work/roms/motor_v9.gba \
MGBA_CORE=/tmp/mgba-build/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v10*.py' -v
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

from mgba_treino_harness import Emulator, PARTY, decrypted, offset, put16, put32, u16, u32
from test_atualizacoes_gen9_mgba import FOE_BATTLE, PLAYER_BATTLE
from test_estojo_expandido_mgba import add, open_case, page, save_after_case
from test_eventos_fixos_mgba import enemy, route_entry_fixture, route_from_entry
from test_golpes_gen9_integracao import load_game, set_exp_and_test_stats
from test_golpes_gen9_mgba import invoke, moves as get_moves, seed_mon
from test_motor_ampliado_mgba import stored_quantity
from test_motor_v7_mgba import bank_off, decode_gba_str
from scripts import motor_v10 as patch

ROM_ENV = os.environ.get("MOTOR_V10_ROM")
BASE_ENV = os.environ.get("MOTOR_V10_BASE")
CORE_ENV = os.environ.get("MGBA_CORE")

DISP_STR = 0x020201B4
BUFF3 = 0x02020300
PARTY_INDEXES_ADDR = 0x020213F8
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
V10_STATE_ADDR = 0x0203FD60


def _party_held_item(state: bytes, party_addr: int = PARTY, slot: int = 0) -> int:
    pos = offset(party_addr + 100 * slot)
    block, order, valid = decrypted(state[pos : pos + 100])
    if not valid:
        raise ValueError("Pokemon de teste inválido")
    return u16(block, order[0] * 12 + 2)


def _set_party_held_item_raw(state: bytearray, party_addr: int, slot: int, item_id: int) -> None:
    pos = offset(party_addr + 100 * slot)
    data = bytearray(state[pos : pos + 100])
    block, order, valid = decrypted(data)
    if not valid:
        raise ValueError("Pokemon de teste inválido")
    put16(block, order[0] * 12 + 2, item_id)
    put16(data, 28, sum(struct.unpack("<24H", block)) & 0xFFFF)
    key = u32(data, 0) ^ u32(data, 4)
    for i in range(0, 48, 4):
        put32(data, i + 32, u32(block, i) ^ key)
    state[pos : pos + 100] = data


@unittest.skipUnless(ROM_ENV and BASE_ENV and CORE_ENV, "defina MOTOR_V10_ROM, MOTOR_V10_BASE e MGBA_CORE")
class MotorV10MGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM_ENV).resolve()
        cls.base = Path(BASE_ENV).resolve()
        cls.core = Path(CORE_ENV).resolve()
        if cls.rom.read_bytes() != patch.build(cls.base.read_bytes()):
            raise ValueError("ROM motor_v10 diverge da reconstrução determinística")
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        cls.f = Emulator(cls.rom, cls.core, cls.dir)
        cls.fixture = route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()
        cls.two_party_fixture = cls._make_two_party_singles_fixture()
        cls.two_enemy_fixture = cls._make_two_enemy_trainer_like_fixture()
        cls.doubles_fixture = cls._make_doubles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    @classmethod
    def _enter_wild_encounter(cls, state: bytearray, *, doubles: bool = False, two_foes: bool = False) -> bytes:
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

        if doubles or two_foes:
            for _ in range(250):
                st = bytearray(cls.f.state())
                bt = u32(st, offset(0x02020374))
                if bt == 0x04:
                    e1 = bytearray(seed_mon(bytes(st), 6, 10, (150, 150, 150, 150)))
                    set_exp_and_test_stats(e1, 6, 10)
                    put16(e1, offset(PARTY) + 86, 220)
                    put16(e1, offset(PARTY) + 88, 220)
                    st[offset(ENEMY_PARTY_ADDR + 100) : offset(ENEMY_PARTY_ADDR + 200)] = (
                        e1[offset(PARTY) : offset(PARTY) + 100]
                    )
                    st[offset(ENEMY_PARTY_COUNT)] = 2
                    if doubles:
                        struct.pack_into("<I", st, offset(0x02020374), bt | 0x01)
                    else:
                        struct.pack_into("<I", st, offset(0x02020374), bt | 0x08)  # BATTLE_TYPE_TRAINER p/ phaze
                    cls.f.restore(bytes(st))
                    break
                cls.f.run(1)

        cls.f.run(400)
        for _ in range(10 if (doubles or two_foes) else 6):
            cls.f.pulse("B", 45)
        return bytes(cls.f.state())

    @classmethod
    def _make_singles_fixture(cls) -> bytes:
        state = bytearray(seed_mon(cls.fixture, 1, 10, (672, 558, 33, 150)))
        set_exp_and_test_stats(state, 1, 10)
        return cls._enter_wild_encounter(state)

    @classmethod
    def _make_two_party_singles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (746, 150, 150, 150)))
        set_exp_and_test_stats(s1, 1, 10)
        put16(s1, offset(PARTY) + 86, 160)
        put16(s1, offset(PARTY) + 88, 160)
        s2 = bytearray(seed_mon(cls.fixture, 6, 10, (150, 150, 150, 150)))
        set_exp_and_test_stats(s2, 6, 10)
        put16(s2, offset(PARTY) + 86, 0)  # aliado desmaiado no slot 1 da equipe
        put16(s2, offset(PARTY) + 88, 160)
        s1[offset(PARTY + 100) : offset(PARTY + 200)] = s2[offset(PARTY) : offset(PARTY) + 100]
        s1[offset(PLAYER_PARTY_COUNT)] = 2
        return cls._enter_wild_encounter(s1)

    @classmethod
    def _make_two_enemy_trainer_like_fixture(cls) -> bytes:
        state = bytearray(seed_mon(cls.fixture, 1, 10, (521, 150, 150, 150)))
        set_exp_and_test_stats(state, 1, 10)
        return cls._enter_wild_encounter(state, two_foes=True)

    @classmethod
    def _make_doubles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (677, 631, 150, 150)))
        set_exp_and_test_stats(s1, 1, 10)
        s2 = bytearray(seed_mon(cls.fixture, 4, 10, (150, 150, 150, 150)))
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
        _set_party_held_item_raw(st, PARTY, 0, p_item)
        _set_party_held_item_raw(st, ENEMY_PARTY_ADDR, 0, f_item)
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
        put16(st, offset(ENEMY_PARTY_ADDR) + 86, f_hp)
        put16(st, offset(ENEMY_PARTY_ADDR) + 88, f_max)
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
        st[offset(V10_STATE_ADDR) : offset(V10_STATE_ADDR) + 152] = b"\x00" * 152
        st[offset(BUFF3)] = 0xAA
        return bytes(st)

    def _run_turn(self, state: bytes, *, slot: int = 0, frames: int = 1100) -> tuple[bytes, list[str]]:
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

    def test_familia_a_berries_stuff_cheeks_belch_teatime_bug_bite_e_incinerate(self):
        # 1. Subida de nível real p/ Skwovet (#819 -> Stuff Cheeks 672 no nv. 10)
        st_skw = seed_mon(self.fixture, 819, 10, (33, 39, 0, 0))
        out_skw = invoke(self.f, st_skw, 0x08109790, {0: PARTY, 1: 1})
        self.assertEqual(get_moves(out_skw), (33, 39, 672, 0))

        # 2. Stuff Cheeks (672) sem Berry falha; Belch (558) antes de comer Berry também falha
        _, seen_no = self._run_turn(self._duel_state(672, p_item=0))
        self.assertTrue(any("falhou" in s.lower() for s in seen_no), seen_no)
        _, seen_bl_no = self._run_turn(self._duel_state(558, p_item=142))
        self.assertTrue(any("falhou" in s.lower() for s in seen_bl_no), seen_bl_no)

        # 3. Stuff Cheeks (672) com Sitrus Berry (142) em 80/160 HP -> consome Berry, cura +40 HP (=120),
        #    sobe Def em +2 (stage 8) e habilita Belch (558) no turno seguinte!
        sc_t1, _ = self._run_turn(self._duel_state(672, move2_id=558, p_hp=80, p_max=160, p_item=142))
        self.assertEqual(u16(sc_t1, PLAYER_BATTLE + 0x30), 0)
        self.assertEqual(_party_held_item(sc_t1, PARTY, 0), 0)
        self.assertEqual(u16(sc_t1, PLAYER_BATTLE + 0x2A), 120)
        self.assertEqual(sc_t1[PLAYER_BATTLE + 0x18 + 2], 8)  # +2 Def

        sc_t2, _ = self._run_turn(sc_t1, slot=1)  # Belch (558, 120 BP)
        self.assertLess(u16(sc_t2, FOE_BATTLE + 0x2A), 480)

        # 4. Bug Bite (449, TM182) rouba e consome Liechi Berry (168) do alvo -> +1 Atk no usuário;
        #    Incinerate (509) destrói Oran Berry (139) do alvo sem curar o usuário.
        bb_ok, _ = self._run_turn(self._duel_state(449, f_item=168))
        self.assertEqual(u16(bb_ok, FOE_BATTLE + 0x30), 0)
        self.assertEqual(_party_held_item(bb_ok, ENEMY_PARTY_ADDR, 0), 0)
        self.assertEqual(bb_ok[PLAYER_BATTLE + 0x18 + 1], 7)  # +1 Atk da Liechi Berry

        inc_ok, _ = self._run_turn(self._duel_state(509, p_hp=80, p_max=160, f_item=139))
        self.assertEqual(u16(inc_ok, FOE_BATTLE + 0x30), 0)
        self.assertEqual(u16(inc_ok, PLAYER_BATTLE + 0x2A), 80)

        # 5. Duplas: Teatime (677) faz todos os bancos com Berry consumirem suas Berries,
        #    e Pollen Puff (631) cura aliado em 50% do HP máximo!
        st_dbl = bytearray(self.doubles_fixture)
        _set_party_held_item_raw(st_dbl, PARTY, 0, 133)             # Cheri Berry
        _set_party_held_item_raw(st_dbl, ENEMY_PARTY_ADDR, 0, 139)  # Oran Berry
        b0, b1, b2, b3 = (bank_off(i) for i in range(4))
        for b in (b0, b1, b2, b3):
            for s in range(1, 8):
                st_dbl[b + 0x18 + s] = 6
            put16(st_dbl, b + 0x20, 4)
            for mslot in range(4):
                put16(st_dbl, b + 0x0C + 2 * mslot, 150)
                st_dbl[b + 0x25 + mslot] = 20
        put16(st_dbl, b0 + 0x0C, 677)  # Teatime
        put16(st_dbl, b0 + 0x0E, 631)  # Pollen Puff
        put16(st_dbl, b0 + 0x30, 133)  # Cheri Berry (cura paralisia)
        struct.pack_into("<I", st_dbl, b0 + 0x50, 0x40)
        struct.pack_into("<I", st_dbl, offset(PARTY) + 80, 0x40)
        put16(st_dbl, b1 + 0x2A, 100)
        put16(st_dbl, b1 + 0x2E, 200)
        put16(st_dbl, offset(ENEMY_PARTY_ADDR) + 86, 100)
        put16(st_dbl, offset(ENEMY_PARTY_ADDR) + 88, 200)
        put16(st_dbl, b1 + 0x30, 139)  # Oran Berry (+10 HP)
        put16(st_dbl, b2 + 0x2A, 60)
        put16(st_dbl, b2 + 0x2E, 160)
        put16(st_dbl, offset(PARTY + 100) + 86, 60)
        put16(st_dbl, offset(PARTY + 100) + 88, 160)
        st_dbl[offset(V10_STATE_ADDR) : offset(V10_STATE_ADDR) + 152] = b"\x00" * 152

        self.f.restore(bytes(st_dbl))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)  # b0: Teatime (tgt=0x10, sem cursor de alvo)
        self.f.pulse("A", 25)  # b2: Fight
        self.f.pulse("A", 25)  # b2: Splash
        self.f.run(1900)
        tt_end = self.f.state()
        self.assertEqual(u16(tt_end, b0 + 0x30), 0)
        self.assertEqual(u32(tt_end, b0 + 0x50), 0)  # paralisia curada
        self.assertEqual(u16(tt_end, b1 + 0x30), 0)
        self.assertEqual(u16(tt_end, b1 + 0x2A), 110)

        # Pollen Puff (631, slot 1) mirando no aliado b2 (60/160 HP -> +80 HP = 140 HP)
        st_pp = bytearray(st_dbl)
        put16(st_pp, b0 + 0x06, 350)
        put16(st_pp, b0 + 0x30, 0)
        struct.pack_into("<I", st_pp, b0 + 0x50, 0)
        struct.pack_into("<I", st_pp, offset(PARTY) + 80, 0)
        self.f.restore(bytes(st_pp))
        self.f.pulse("A", 25)
        self.f.pulse("RIGHT", 15)
        self.f.pulse("A", 25)
        self.f.pulse("DOWN", 15)  # mira no aliado b2
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(1500)
        pp_end = self.f.state()
        self.assertEqual(u16(pp_end, b2 + 0x2A), 140)

    def test_familia_b_dreno_75_knock_off_scale_shot_population_bomb_e_criticos(self):
        # 1. Draining Kiss (573, TM037) drena 75% do dano causado (vs 50% de Bitter Blade 778)
        dk_res, _ = self._run_turn(
            self._duel_state(573, p_spa=320, f_spd_stat=80, p_hp=60, p_max=200, f_hp=400, f_max=400)
        )
        dealt_dk = 400 - u16(dk_res, FOE_BATTLE + 0x2A)
        healed_dk = u16(dk_res, PLAYER_BATTLE + 0x2A) - 60
        self.assertGreaterEqual(dealt_dk, 16)
        self.assertEqual(healed_dk, max(1, (dealt_dk * 3) // 4))

        # 2. Knock Off (282, TM181) causa ~1.5x dano quando alvo segura item e remove o item
        ko_no, _ = self._run_turn(self._duel_state(282, f_hp=480, f_max=480, f_item=0))
        ko_it, _ = self._run_turn(self._duel_state(282, f_hp=480, f_max=480, f_item=139))
        dmg_no = 480 - u16(ko_no, FOE_BATTLE + 0x2A)
        dmg_it = 480 - u16(ko_it, FOE_BATTLE + 0x2A)
        self.assertGreater(dmg_it, (dmg_no * 13) // 10)
        self.assertEqual(u16(ko_it, FOE_BATTLE + 0x30), 0)

        # 3. Scale Shot (703, TM200): multi-hit + -1 Def (stage 5) e +1 Spe (stage 7) no usuário
        ss_res, _ = self._run_turn(self._duel_state(703, p_atk=120, f_hp=480, f_max=480), frames=1500)
        self.assertLess(u16(ss_res, FOE_BATTLE + 0x2A), 480)
        self.assertEqual(ss_res[PLAYER_BATTLE + 0x18 + 2], 5)  # -1 Def
        self.assertEqual(ss_res[PLAYER_BATTLE + 0x18 + 3], 7)  # +1 Spe

        # 4. Population Bomb (752) com acc_stage=12 acerta 10 vezes; Flower Trick (762) dá crítico garantido
        pb_1, _ = self._run_turn(self._duel_state(1, p_atk=90, f_hp=480, f_max=480))  # Pound 40 BP = 2x20 BP
        pb_10, _ = self._run_turn(self._duel_state(752, p_atk=90, f_hp=480, f_max=480), frames=2300)
        dmg_pound = 480 - u16(pb_1, FOE_BATTLE + 0x2A)
        dmg_pop = 480 - u16(pb_10, FOE_BATTLE + 0x2A)
        self.assertGreater(dmg_pop, dmg_pound * 3)

        ft_ba, _ = self._run_turn(self._duel_state(762, acc_stage=0, eva_stage=12, f_ability=4))
        ft_cr, seen_cr = self._run_turn(self._duel_state(762, acc_stage=0, eva_stage=12, f_ability=65))
        self.assertGreater(480 - u16(ft_ba, FOE_BATTLE + 0x2A), 0)
        self.assertGreater(480 - u16(ft_cr, FOE_BATTLE + 0x2A), 480 - u16(ft_ba, FOE_BATTLE + 0x2A))
        self.assertTrue(any("cr" in s.lower() for s in seen_cr), seen_cr)

    def test_familia_c_aterramento_terreno_telas_freeze_dry_e_photon_geyser(self):
        # 1. Thousand Arrows (606): atinge Grass/Flying (12, 2) com dano neutro no turno 1 e aterra p/ Earthquake (89)
        ta_t1, _ = self._run_turn(self._duel_state(606, move2_id=89, p_atk=120, f_types=(12, 2), f_ability=26))
        dmg_ta = 480 - u16(ta_t1, FOE_BATTLE + 0x2A)
        self.assertGreater(dmg_ta, 0)
        self.assertEqual(u32(ta_t1, offset(STATUSES3_ADDR) + 4) & 0x0400, 0)  # não ligou Ingrain!
        hp_after_t1 = u16(ta_t1, FOE_BATTLE + 0x2A)
        ta_t2, _ = self._run_turn(ta_t1, slot=1, frames=1400)  # Earthquake (89) acerta alvo derrubado
        self.assertLess(u16(ta_t2, FOE_BATTLE + 0x2A), hp_after_t1)

        # 2. Ice Spinner (753) limpa terreno; Steel Roller (702) falha sem terreno e limpa quando há terreno
        _, seen_sr = self._run_turn(self._duel_state(702))
        self.assertTrue(any("falhou" in s.lower() for s in seen_sr), seen_sr)

        st_ter = bytearray(self._duel_state(753))
        st_ter[offset(V8_STATE_ADDR) + 0] = 1  # Electric Terrain
        st_ter[offset(V8_STATE_ADDR) + 1] = 5
        isp_ok, _ = self._run_turn(bytes(st_ter))
        self.assertEqual((isp_ok[offset(V8_STATE_ADDR) + 0], isp_ok[offset(V8_STATE_ADDR) + 1]), (0, 0))

        # 3. Raging Bull (765): tipo Fire (usuário Fire) + quebra Aurora Veil e Reflect!
        st_rb = bytearray(self._duel_state(765, p_types=(10, 10), f_types=(12, 12)))
        put16(st_rb, offset(SIDE_STATUSES_ADDR) + 2, 0x0001)  # Reflect no lado inimigo
        st_rb[offset(SIDE_TIMERS_ADDR) + 12] = 5
        st_rb[offset(V8_STATE_ADDR) + 11] = 5  # Aurora Veil no lado inimigo
        rb_ok, seen_rb = self._run_turn(bytes(st_rb))
        self.assertEqual(u16(rb_ok, offset(SIDE_STATUSES_ADDR) + 2) & 0x0001, 0)
        self.assertEqual(rb_ok[offset(V8_STATE_ADDR) + 11], 0)
        self.assertTrue(any("super" in s.lower() for s in seen_rb), seen_rb)

        # 4. Freeze-Dry (569): super efetivo contra Water/Flying (4x)!
        _, seen_fd = self._run_turn(self._duel_state(569, f_types=(11, 2)))
        self.assertTrue(any("super" in s.lower() for s in seen_fd), seen_fd)

        # 5. Photon Geyser (667): usa Atk físico quando Atk (260) > SpA (60)
        pg_hi, _ = self._run_turn(self._duel_state(667, p_atk=260, p_spa=60, f_def=100, f_spd_stat=280))
        pg_lo, _ = self._run_turn(self._duel_state(667, p_atk=60, p_spa=70, f_def=100, f_spd_stat=280))
        self.assertGreater(480 - u16(pg_hi, FOE_BATTLE + 0x2A), (480 - u16(pg_lo, FOE_BATTLE + 0x2A)) * 3)

    def test_familia_d_prioridade_phazing_residuos_spectral_thief_e_gigaton(self):
        # 1. Thunderclap (793): falha contra Splash (150) e acerta com prioridade +1 contra Tackle (33)
        _, seen_tcf = self._run_turn(self._duel_state(793, foe_move=150, p_speed=40, f_speed=300))
        self.assertTrue(any("falhou" in s.lower() for s in seen_tcf), seen_tcf)
        tc_hit, _ = self._run_turn(self._duel_state(793, foe_move=33, p_speed=40, f_speed=300))
        self.assertLess(u16(tc_hit, FOE_BATTLE + 0x2A), 480)

        # 2. Spectral Thief (658): rouba +3 Atk do alvo antes de atacar
        st_sp = bytearray(self._duel_state(658, p_atk=120))
        st_sp[FOE_BATTLE + 0x18 + 1] = 9  # +3 Atk no alvo
        sp_ok, _ = self._run_turn(bytes(st_sp))
        self.assertEqual(sp_ok[PLAYER_BATTLE + 0x18 + 1], 9)
        self.assertEqual(sp_ok[FOE_BATTLE + 0x18 + 1], 6)

        # 3. Salt Cure (756) em alvo Steel (8): causa 1/4 MaxHP (120 de 480) no fim do turno;
        #    Throat Chop (630) impede Hyper Voice (304) do alvo!
        sc_stl, _ = self._run_turn(
            self._duel_state(756, p_atk=40, f_hp=480, f_max=480, f_def=300, f_types=(8, 8)),
            frames=1500,
        )
        self.assertLessEqual(u16(sc_stl, FOE_BATTLE + 0x2A), 360)

        tc_blk, seen_tc = self._run_turn(self._duel_state(630, foe_move=304, p_atk=80))
        self.assertEqual(u16(tc_blk, PLAYER_BATTLE + 0x2A), 160)  # Hyper Voice bloqueado!
        self.assertTrue(any("som" in s.lower() for s in seen_tc), seen_tc)

        # 4. Gigaton Hammer (780): funciona no turno 1, é bloqueado no turno 2 consecutivo e volta no turno 3
        gh_t1, _ = self._run_turn(self._duel_state(780, p_atk=80, f_hp=480, f_max=480))
        hp_t1 = u16(gh_t1, FOE_BATTLE + 0x2A)
        self.assertLess(hp_t1, 480)
        gh_t2, seen_gh2 = self._run_turn(gh_t1, slot=0)
        self.assertEqual(u16(gh_t2, FOE_BATTLE + 0x2A), hp_t1)
        self.assertTrue(any("repetir" in s.lower() for s in seen_gh2), seen_gh2)
        gh_t3, _ = self._run_turn(gh_t2, slot=0)
        self.assertLess(u16(gh_t3, FOE_BATTLE + 0x2A), hp_t1)

        # 5. Dragon Tail (521) em batalha com 2 oponentes: causa dano e força entrada do slot 1 (#6 Charizard)
        dt_st = self._duel_state(521, p_atk=80, f_hp=480, f_max=480, base_state=self.two_enemy_fixture)
        dt_end, _ = self._run_turn(dt_st, frames=1500)
        self.assertEqual(u16(dt_end, offset(PARTY_INDEXES_ADDR) + 2), 1)

    def test_familia_e_rage_fist_last_respects_bolt_beak_autotomize_e_collision_course(self):
        # 1. Rage Fist (776, Ghost): escala estritamente +1 por impacto recebido (50 -> 100 -> 150 BP, não 350!)
        rf_base = self._duel_state(
            150, move2_id=776, foe_move=33, p_atk=220, p_def=260, f_atk=90, f_def=90,
            f_types=(10, 10), f_hp=480, f_max=480,
        )
        rf_0, _ = self._run_turn(rf_base, slot=1)  # 0 hits recebidos -> 50 BP (age antes do oponente)
        dmg_0 = 480 - u16(rf_0, FOE_BATTLE + 0x2A)

        rf_hit1, _ = self._run_turn(rf_base, slot=0)  # turno 1: usa Splash e recebe 1 Tackle
        self.assertEqual(u32(rf_hit1, offset(V10_STATE_ADDR) + 80) & 0x0F, 1)  # exatamente 1 stack!
        rf_1, _ = self._run_turn(rf_hit1, slot=1)     # turno 2: Rage Fist a 100 BP
        dmg_1 = 480 - u16(rf_1, FOE_BATTLE + 0x2A)

        rf_hit2, _ = self._run_turn(rf_hit1, slot=0)  # turno 2 alternativo: recebe 2º Tackle -> 2 stacks
        self.assertEqual(u32(rf_hit2, offset(V10_STATE_ADDR) + 80) & 0x0F, 2)
        rf_2, _ = self._run_turn(rf_hit2, slot=1)     # Rage Fist a 150 BP
        dmg_2 = 480 - u16(rf_2, FOE_BATTLE + 0x2A)
        self.assertGreater(dmg_0, 0)
        self.assertLess(dmg_0, dmg_1)
        self.assertLess(dmg_1, dmg_2)

        # 2. Last Respects (746, Ghost): 100 BP com 1 aliado desmaiado > 50 BP sem aliados desmaiados
        lr_0, _ = self._run_turn(self._duel_state(746, p_atk=240, f_def=90, f_types=(10, 10)))
        lr_1, _ = self._run_turn(
            self._duel_state(746, p_atk=240, f_def=90, f_types=(10, 10), base_state=self.two_party_fixture)
        )
        self.assertGreater(480 - u16(lr_1, FOE_BATTLE + 0x2A), 480 - u16(lr_0, FOE_BATTLE + 0x2A))

        # 3. Bolt Beak (679): 170 BP agindo primeiro vs 85 BP agindo depois
        bb_fast, _ = self._run_turn(self._duel_state(679, p_atk=220, f_def=100, p_speed=300, f_speed=40))
        bb_slow, _ = self._run_turn(self._duel_state(679, p_atk=220, f_def=100, p_speed=40, f_speed=300))
        self.assertGreater(480 - u16(bb_fast, FOE_BATTLE + 0x2A), (480 - u16(bb_slow, FOE_BATTLE + 0x2A)) * 16 // 10)

        # 4. Collision Course (768, 100 BP Fighting): +33% sobre super efetivo comparado a Cross Chop (238, 100 BP)
        cc_boost, _ = self._run_turn(self._duel_state(768, p_atk=220, f_def=100, f_types=(0, 0)))
        xc_norm, _ = self._run_turn(self._duel_state(238, p_atk=220, f_def=100, f_types=(0, 0)))
        self.assertGreater(480 - u16(cc_boost, FOE_BATTLE + 0x2A), (480 - u16(xc_norm, FOE_BATTLE + 0x2A)) * 115 // 100)

        # 5. Autotomize (474) reduz peso efetivo de Snorlax (#143, 460 kg) e diminui potência de Heavy Slam (483)
        hs_heavy, _ = self._run_turn(
            self._duel_state(483, p_species=143, f_species=133, p_atk=240, f_def=90)
        )
        auto_base = self._duel_state(474, move2_id=483, p_species=143, f_species=133, p_atk=240, f_def=90)
        auto_1, _ = self._run_turn(auto_base, slot=0)
        auto_2, _ = self._run_turn(auto_1, slot=0)
        auto_3, _ = self._run_turn(auto_2, slot=0)
        auto_4, _ = self._run_turn(auto_3, slot=0)  # 460 kg - 400 kg = 60 kg vs Eevee 6.5 kg -> ainda >5x?
        auto_5, _ = self._run_turn(auto_4, slot=0)  # 460 kg - 500 kg -> 0.1 kg (< Eevee 6.5 kg -> 40 BP!)
        hs_light, _ = self._run_turn(auto_5, slot=1)
        self.assertGreater(480 - u16(hs_heavy, FOE_BATTLE + 0x2A), (480 - u16(hs_light, FOE_BATTLE + 0x2A)) * 2)

    def test_regressao_estojo_229_tms_motor_v8_v9_e_save_sintetico(self):
        # 1. Regressão motor_v9 (Soak 486) e motor_v8 (Snowscape 773)
        soak_ok, _ = self._run_turn(self._duel_state(486, f_types=(10, 10)))
        self.assertEqual((soak_ok[FOE_BATTLE + 0x22], soak_ok[FOE_BATTLE + 0x23]), (11, 11))
        snow_ok, _ = self._run_turn(self._duel_state(773))
        self.assertEqual(u16(snow_ok, offset(BATTLE_WEATHER_ADDR)), 0x0100)

        # 2. Estojo v2 com TMs atualizadas no motor_v10 (TM181 Knock Off = 555, TM182 Bug Bite = 556,
        #    TM200 Scale Shot = 574) + HM01 Cut (339) + save sintético e reload
        st = bytes(self.fixture)
        st = add(self.f, st, 339, 1)  # HM01 Cut
        st = add(self.f, st, 555, 1)  # TM181 Knock Off
        st = add(self.f, st, 556, 2)  # TM182 Bug Bite
        st = add(self.f, st, 574, 1)  # TM200 Scale Shot
        self.f.restore(st)
        open_case(self.f)
        self.assertEqual(page(self.f.state()), 0)
        flash = save_after_case(self.f)

        core2 = Path(shutil.copy2(self.core, self.dir / "mgba_reload_v10.so"))
        reloaded = Emulator(self.rom, core2, self.dir)
        try:
            load_game(reloaded, flash)
            s_after = reloaded.state()
            self.assertEqual(stored_quantity(s_after, 339), 1)
            self.assertEqual(stored_quantity(s_after, 555), 1)
            self.assertEqual(stored_quantity(s_after, 556), 2)
            self.assertEqual(stored_quantity(s_after, 574), 1)
        finally:
            reloaded.close()


if __name__ == "__main__":
    unittest.main()
