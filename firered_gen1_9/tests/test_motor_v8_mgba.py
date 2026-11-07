"""Testes de integração em mGBA 0.10.5 do motor parcial v8 (apenas saves/estados sintéticos).

MOTOR_V8_ROM=/tmp/firered_gen1_9_work/roms/motor_v8.gba \
MOTOR_V8_BASE=/tmp/firered_gen1_9_work/roms/motor_v7.gba \
MGBA_CORE=/tmp/mgba-build/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v8*.py' -v
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

from mgba_treino_harness import Emulator, PARTY, mon, mon_facts, offset, put16, u16, u32
from test_atualizacoes_gen9_mgba import FOE_BATTLE, PLAYER_BATTLE
from test_estojo_expandido_mgba import add, get, open_case, page, save_after_case
from test_eventos_fixos_mgba import enemy, route_entry_fixture, route_from_entry
from test_golpes_gen9_integracao import load_game, set_exp_and_test_stats
from test_golpes_gen9_mgba import invoke, moves as get_moves, seed_mon
from test_motor_ampliado_mgba import stored_quantity
from test_motor_v7_mgba import decode_gba_str, bank_off
from scripts import motor_v8 as patch

ROM_ENV = os.environ.get("MOTOR_V8_ROM")
BASE_ENV = os.environ.get("MOTOR_V8_BASE")
CORE_ENV = os.environ.get("MGBA_CORE")

DISP_STR = 0x020201B4
BUFF3 = 0x02020300
PARTY_INDEXES_ADDR = 0x020213F8
SIDE_STATUSES_ADDR = 0x0202161C
SIDE_TIMERS_ADDR = 0x02021620
STATUSES3_ADDR = 0x02021638
BATTLE_WEATHER_ADDR = 0x0202175C
WEATHER_DURATION_ADDR = 0x02021788
DISABLE_STRUCTS_ADDR = 0x02021798
ENEMY_PARTY_COUNT = 0x0203A730
PLAYER_PARTY_COUNT = 0x0203A731
ENEMY_PARTY_ADDR = 0x0203A734
V7_STATE_ADDR = 0x0203FC00
V8_STATE_ADDR = 0x0203FC60

# Offsets dentro de struct V8BattleState (0x0203FC60)
V8_TERRAIN_TYPE = V8_STATE_ADDR + 0
V8_TERRAIN_TURNS = V8_STATE_ADDR + 1
V8_TRICK_ROOM_TURNS = V8_STATE_ADDR + 2
V8_WONDER_ROOM_TURNS = V8_STATE_ADDR + 3
V8_GRAVITY_TURNS = V8_STATE_ADDR + 4
V8_TAILWIND_0 = V8_STATE_ADDR + 8
V8_TAILWIND_1 = V8_STATE_ADDR + 9
V8_AURORA_VEIL_0 = V8_STATE_ADDR + 10
V8_AURORA_VEIL_1 = V8_STATE_ADDR + 11
V8_STEALTH_ROCK_0 = V8_STATE_ADDR + 12
V8_STEALTH_ROCK_1 = V8_STATE_ADDR + 13
V8_TOXIC_SPIKES_0 = V8_STATE_ADDR + 14
V8_TOXIC_SPIKES_1 = V8_STATE_ADDR + 15
V8_STICKY_WEB_0 = V8_STATE_ADDR + 16
V8_STICKY_WEB_1 = V8_STATE_ADDR + 17
V8_MAGNET_RISE = V8_STATE_ADDR + 18  # 4 bytes


@unittest.skipUnless(ROM_ENV and BASE_ENV and CORE_ENV, "defina MOTOR_V8_ROM, MOTOR_V8_BASE e MGBA_CORE")
class MotorV8MGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM_ENV).resolve()
        cls.base = Path(BASE_ENV).resolve()
        cls.core = Path(CORE_ENV).resolve()
        if cls.rom.read_bytes() != patch.build(cls.base.read_bytes()):
            raise ValueError("ROM motor_v8 diverge da reconstrução determinística")
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
        state = bytearray(seed_mon(cls.fixture, 1, 10, (773, 599, 576, 445)))
        set_exp_and_test_stats(state, 1, 10)
        return cls._enter_wild_encounter(state)

    @classmethod
    def _make_two_party_singles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (771, 369, 445, 390)))
        set_exp_and_test_stats(s1, 1, 10)
        # Slot 1: Charizard (6, Fire/Flying, 4x fraco a Rock) com 160 HP p/ testar Stealth Rock e imunidade de solo
        s2 = bytearray(seed_mon(cls.fixture, 6, 10, (33, 52, 150, 150)))
        set_exp_and_test_stats(s2, 6, 10)
        put16(s2, offset(PARTY) + 86, 160)
        put16(s2, offset(PARTY) + 88, 160)
        s1[offset(PARTY + 100) : offset(PARTY + 200)] = s2[offset(PARTY) : offset(PARTY) + 100]
        s1[offset(PLAYER_PARTY_COUNT)] = 2
        return cls._enter_wild_encounter(s1)

    @classmethod
    def _make_doubles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (621, 576, 758, 150)))
        set_exp_and_test_stats(s1, 1, 10)
        s2 = bytearray(seed_mon(cls.fixture, 4, 10, (150, 33, 150, 150)))
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
        p_hp: int = 160,
        p_max: int = 160,
        p_atk: int = 200,
        p_def: int = 130,
        p_spa: int = 200,
        p_spd_stat: int = 130,
        p_speed: int = 300,
        p_types: tuple[int, int] = (0, 0),
        p_ability: int = 4,
        f_hp: int = 480,
        f_max: int = 480,
        f_atk: int = 180,
        f_def: int = 140,
        f_spa: int = 180,
        f_spd_stat: int = 140,
        f_speed: int = 40,
        f_types: tuple[int, int] = (0, 0),
        f_ability: int = 4,
        acc_stage: int = 12,
        eva_stage: int = 6,
        weather: int = 0,
        weather_dur: int = 0,
        base_state: bytes | None = None,
    ) -> bytes:
        st = bytearray(self.battle_fixture if base_state is None else base_state)
        put16(st, PLAYER_BATTLE + 0x0C, move_id)
        put16(st, PLAYER_BATTLE + 0x0E, move2_id)
        st[PLAYER_BATTLE + 0x25] = 20
        st[PLAYER_BATTLE + 0x26] = 20
        put16(st, PLAYER_BATTLE + 0x2A, p_hp)
        put16(st, PLAYER_BATTLE + 0x2E, p_max)
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
        st[PLAYER_BATTLE + 0x20] = p_ability
        st[PLAYER_BATTLE + 0x22], st[PLAYER_BATTLE + 0x23] = p_types
        st[PLAYER_BATTLE + 0x2C] = 10
        st[PLAYER_BATTLE + 0x50 : PLAYER_BATTLE + 0x58] = b"\x00" * 8

        for mslot in range(4):
            put16(st, FOE_BATTLE + 0x0C + 2 * mslot, foe_move)
            st[FOE_BATTLE + 0x25 + mslot] = 40
        put16(st, FOE_BATTLE + 0x02, f_atk)
        put16(st, FOE_BATTLE + 0x04, f_def)
        put16(st, FOE_BATTLE + 0x06, f_speed)
        put16(st, FOE_BATTLE + 0x08, f_spa)
        put16(st, FOE_BATTLE + 0x0A, f_spd_stat)
        st[FOE_BATTLE + 0x20] = f_ability
        st[FOE_BATTLE + 0x22], st[FOE_BATTLE + 0x23] = f_types
        put16(st, FOE_BATTLE + 0x2A, f_hp)
        put16(st, FOE_BATTLE + 0x2E, f_max)
        st[FOE_BATTLE + 0x50 : FOE_BATTLE + 0x58] = b"\x00" * 8

        st[offset(SIDE_STATUSES_ADDR) : offset(SIDE_STATUSES_ADDR) + 4] = b"\x00" * 4
        st[offset(SIDE_TIMERS_ADDR) : offset(SIDE_TIMERS_ADDR) + 24] = b"\x00" * 24
        st[offset(STATUSES3_ADDR) : offset(STATUSES3_ADDR) + 16] = b"\x00" * 16
        put16(st, offset(BATTLE_WEATHER_ADDR), weather)
        st[offset(WEATHER_DURATION_ADDR)] = weather_dur
        st[offset(V7_STATE_ADDR) : offset(V7_STATE_ADDR) + 96] = b"\x00" * 96
        st[offset(V8_STATE_ADDR) : offset(V8_STATE_ADDR) + 64] = b"\x00" * 64
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

    def test_snowscape_chilly_reception_blizzard_weather_ball_aurora_veil_e_quebra_barreira(self):
        # 1. Snowscape (773): liga WEATHER_SNOW_BIT (0x0100), decai 5 -> 4 no fim do turno e nao causa dano residual
        end_snow, seen_snow = self._run_turn(self._duel_state(773, p_types=(10, 10), f_types=(12, 12)))
        self.assertEqual(u16(end_snow, offset(BATTLE_WEATHER_ADDR)), 0x0100)
        self.assertEqual(end_snow[offset(WEATHER_DURATION_ADDR)], 4)
        self.assertEqual(u16(end_snow, PLAYER_BATTLE + 0x2A), 160)
        self.assertEqual(u16(end_snow, FOE_BATTLE + 0x2A), 480)
        self.assertTrue(any("nevar" in s for s in seen_snow), seen_snow)

        # 2. Defesa fisica +50% para tipo Gelo (15) em Snow vs sem clima
        no_snow_res, _ = self._run_turn(self._duel_state(33, p_atk=400, f_types=(15, 15), f_def=100))
        in_snow_res, _ = self._run_turn(
            self._duel_state(33, p_atk=400, f_types=(15, 15), f_def=100, weather=0x0100, weather_dur=4)
        )
        dmg_no_snow = 480 - u16(no_snow_res, FOE_BATTLE + 0x2A)
        dmg_in_snow = 480 - u16(in_snow_res, FOE_BATTLE + 0x2A)
        self.assertGreater(dmg_no_snow, dmg_in_snow + 4, (dmg_no_snow, dmg_in_snow))

        # 3. Blizzard (59) infalivel em Snow mesmo com Acc -6 / Eva +6; Weather Ball (311) vira Gelo 100 BP
        bliz_res, _ = self._run_turn(
            self._duel_state(59, acc_stage=0, eva_stage=12, weather=0x0100, weather_dur=4)
        )
        self.assertLess(u16(bliz_res, FOE_BATTLE + 0x2A), 480)

        wb_base, _ = self._run_turn(self._duel_state(311, f_types=(12, 12)))
        wb_snow, _ = self._run_turn(self._duel_state(311, f_types=(12, 12), weather=0x0100, weather_dur=4))
        self.assertGreater(480 - u16(wb_snow, FOE_BATTLE + 0x2A), (480 - u16(wb_base, FOE_BATTLE + 0x2A)) * 2)

        # 4. Aurora Veil (649): falha sem neve, funciona em Snow, reduz dano e e quebrado por Psychic Fangs (652)
        av_fail, _ = self._run_turn(self._duel_state(649))
        self.assertEqual(av_fail[offset(V8_AURORA_VEIL_0)], 0)
        av_ok, _ = self._run_turn(self._duel_state(649, weather=0x0100, weather_dur=4))
        self.assertEqual(av_ok[offset(V8_AURORA_VEIL_0)], 4)

        st_veil_foe = bytearray(self._duel_state(33, p_atk=400, f_types=(15, 15), f_def=100))
        st_veil_foe[offset(V8_AURORA_VEIL_1)] = 4
        veil_hit, _ = self._run_turn(bytes(st_veil_foe))
        self.assertLess(480 - u16(veil_hit, FOE_BATTLE + 0x2A), dmg_no_snow)

        st_pf = bytearray(self._duel_state(652))
        st_pf[offset(V8_AURORA_VEIL_1)] = 4
        pf_res, _ = self._run_turn(bytes(st_pf))
        self.assertEqual(pf_res[offset(V8_AURORA_VEIL_1)], 0)
        self.assertLess(u16(pf_res, FOE_BATTLE + 0x2A), 480)

        # 5. Chilly Reception (771): invoca Snow e faz pivot switch p/ slot 1 sem herdar estagios
        st_cr = bytearray(self._duel_state(771, base_state=self.two_party_battle_fixture))
        st_cr[PLAYER_BATTLE + 0x18 + 1] = 8
        self.f.restore(bytes(st_cr))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(680)
        self.f.pulse("DOWN", 30)
        self.f.pulse("A", 35)
        self.f.pulse("A", 35)
        self.f.run(620)
        after_cr = self.f.state()
        self.assertEqual(u16(after_cr, offset(BATTLE_WEATHER_ADDR)), 0x0100)
        self.assertEqual(u16(after_cr, offset(PARTY_INDEXES_ADDR)), 1)
        self.assertEqual(after_cr[PLAYER_BATTLE + 0x18 + 1], 6)

    def test_quatro_terrenos_bloqueios_cura_e_sinergias_de_golpes(self):
        # 1. Electric Terrain (599): +30% Electric aterrado, Rising Voltage (705) dobrado, bloqueia Spore (147) aterrado
        et_set, _ = self._run_turn(self._duel_state(599))
        self.assertEqual(et_set[offset(V8_TERRAIN_TYPE)], 1)
        self.assertEqual(et_set[offset(V8_TERRAIN_TURNS)], 4)

        rv_plain, _ = self._run_turn(self._duel_state(705))
        st_rv_et = bytearray(self._duel_state(705))
        st_rv_et[offset(V8_TERRAIN_TYPE)] = 1
        st_rv_et[offset(V8_TERRAIN_TURNS)] = 4
        rv_et, _ = self._run_turn(bytes(st_rv_et))
        self.assertGreater(480 - u16(rv_et, FOE_BATTLE + 0x2A), (480 - u16(rv_plain, FOE_BATTLE + 0x2A)) * 2)

        st_spore = bytearray(self._duel_state(147))
        st_spore[offset(V8_TERRAIN_TYPE)] = 1
        st_spore[offset(V8_TERRAIN_TURNS)] = 4
        spore_grounded, _ = self._run_turn(bytes(st_spore))
        self.assertEqual(u32(spore_grounded, FOE_BATTLE + 0x50) & 0x07, 0)

        st_spore_fly = bytearray(st_spore)
        st_spore_fly[FOE_BATTLE + 0x22] = 2  # Flying nao aterrado pode adormecer
        spore_fly, _ = self._run_turn(bytes(st_spore_fly))
        self.assertNotEqual(u32(spore_fly, FOE_BATTLE + 0x50) & 0x07, 0)

        # 2. Grassy Terrain (576): cura 1/16 no fim do turno, reduz Earthquake (89) pela metade e Grassy Glide (805) +1 prio
        st_gt_heal = bytearray(self._duel_state(150, p_hp=100, p_max=160))
        st_gt_heal[offset(V8_TERRAIN_TYPE)] = 2
        st_gt_heal[offset(V8_TERRAIN_TURNS)] = 4
        gt_healed, _ = self._run_turn(bytes(st_gt_heal))
        self.assertEqual(u16(gt_healed, PLAYER_BATTLE + 0x2A), 110)

        eq_plain, _ = self._run_turn(self._duel_state(89))
        st_eq_gt = bytearray(self._duel_state(89))
        st_eq_gt[offset(V8_TERRAIN_TYPE)] = 2
        st_eq_gt[offset(V8_TERRAIN_TURNS)] = 4
        eq_gt, _ = self._run_turn(bytes(st_eq_gt))
        self.assertLess(480 - u16(eq_gt, FOE_BATTLE + 0x2A), (480 - u16(eq_plain, FOE_BATTLE + 0x2A)) * 2 // 3)

        # Grassy Glide (805) com p_speed=40 contra f_speed=300 nocauteia o inimigo antes que ele ataque
        st_gg = bytearray(self._duel_state(805, foe_move=33, p_speed=40, f_speed=300, f_hp=5, f_max=200))
        st_gg[offset(V8_TERRAIN_TYPE)] = 2
        st_gg[offset(V8_TERRAIN_TURNS)] = 4
        gg_res, _ = self._run_turn(bytes(st_gg))
        self.assertEqual(u16(gg_res, FOE_BATTLE + 0x2A), 0)
        self.assertEqual(u16(gg_res, PLAYER_BATTLE + 0x2A), 160)

        # 3. Psychic Terrain (633): bloqueia Quick Attack (98, prio +1) contra oponente aterrado e turbina Expanding Force (701)
        st_qa = bytearray(self._duel_state(98))
        st_qa[offset(V8_TERRAIN_TYPE)] = 3
        st_qa[offset(V8_TERRAIN_TURNS)] = 4
        qa_blocked, seen_qa = self._run_turn(bytes(st_qa))
        self.assertEqual(u16(qa_blocked, FOE_BATTLE + 0x2A), 480)
        self.assertTrue(any("protegido" in s for s in seen_qa), seen_qa)

        ef_plain, _ = self._run_turn(self._duel_state(701))
        st_ef_pt = bytearray(self._duel_state(701))
        st_ef_pt[offset(V8_TERRAIN_TYPE)] = 3
        st_ef_pt[offset(V8_TERRAIN_TURNS)] = 4
        ef_pt, _ = self._run_turn(bytes(st_ef_pt))
        self.assertGreater(480 - u16(ef_pt, FOE_BATTLE + 0x2A), (480 - u16(ef_plain, FOE_BATTLE + 0x2A)) * 3 // 2)

        # 4. Misty Terrain (577): reduz Dragon Claw (337) pela metade e bloqueia Toxic (92) aterrado
        dc_plain, _ = self._run_turn(self._duel_state(337))
        st_dc_mt = bytearray(self._duel_state(337))
        st_dc_mt[offset(V8_TERRAIN_TYPE)] = 4
        st_dc_mt[offset(V8_TERRAIN_TURNS)] = 4
        dc_mt, _ = self._run_turn(bytes(st_dc_mt))
        self.assertLess(480 - u16(dc_mt, FOE_BATTLE + 0x2A), (480 - u16(dc_plain, FOE_BATTLE + 0x2A)) * 2 // 3)

        st_tox = bytearray(self._duel_state(92))
        st_tox[offset(V8_TERRAIN_TYPE)] = 4
        st_tox[offset(V8_TERRAIN_TURNS)] = 4
        tox_blocked, _ = self._run_turn(bytes(st_tox))
        self.assertEqual(u32(tox_blocked, FOE_BATTLE + 0x50), 0)

        # 5. Floral Healing (621) em duplas: cura 2/3 (120 de 180) em Grassy Terrain vs 1/2 (90 de 180) fora
        st_fh = bytearray(self.doubles_fixture)
        b0, b1, b2, b3 = bank_off(0), bank_off(1), bank_off(2), bank_off(3)
        put16(st_fh, b0 + 0x0C, 621)
        st_fh[b0 + 0x25] = 10
        put16(st_fh, b2 + 0x2A, 30)
        put16(st_fh, b2 + 0x2E, 180)
        for bx in (b1, b3):
            for mslot in range(4):
                put16(st_fh, bx + 0x0C + 2 * mslot, 150)
        put16(st_fh, b0 + 0x06, 300)
        put16(st_fh, b2 + 0x06, 200)
        put16(st_fh, b1 + 0x06, 40)
        put16(st_fh, b3 + 0x06, 30)
        st_fh[offset(V7_STATE_ADDR) : offset(V7_STATE_ADDR) + 96] = b"\x00" * 96
        st_fh[offset(V8_STATE_ADDR) : offset(V8_STATE_ADDR) + 64] = b"\x00" * 64
        st_fh[offset(V8_TERRAIN_TYPE)] = 2
        st_fh[offset(V8_TERRAIN_TURNS)] = 4

        self.f.restore(bytes(st_fh))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("DOWN", 18)  # seleciona aliado bank 2 como alvo de Floral Healing
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(1050)
        after_fh = self.f.state()
        self.assertEqual(u16(after_fh, b2 + 0x2A), 150)  # 30 + (180*2//3 = 120) = 150

    def test_hazards_entrada_absorcao_stone_axe_ceaseless_edge_mortal_spin_defog_tidy_up_e_court_change(self):
        # 1. Stone Axe (723) causa dano + planta Stealth Rock; Ceaseless Edge (738) causa dano + empilha Spikes
        sa_res, _ = self._run_turn(self._duel_state(723))
        self.assertLess(u16(sa_res, FOE_BATTLE + 0x2A), 480)
        self.assertEqual(sa_res[offset(V8_STEALTH_ROCK_1)], 1)

        ce_res, _ = self._run_turn(self._duel_state(738))
        self.assertLess(u16(ce_res, FOE_BATTLE + 0x2A), 480)
        self.assertTrue(u16(ce_res, offset(SIDE_STATUSES_ADDR) + 2) & 0x0010)
        self.assertEqual(ce_res[offset(SIDE_TIMERS_ADDR) + 12 + 0x0A], 1)

        # 2. Switch-in de Charizard (slot 1, Fire/Flying, 160 HP) sob Stealth Rock sofre 50% (80) mas ignora Sticky Web!
        st_sw = bytearray(self._duel_state(369, foe_move=150, base_state=self.two_party_battle_fixture))
        st_sw[offset(V8_STEALTH_ROCK_0)] = 1
        st_sw[offset(V8_STICKY_WEB_0)] = 1
        st_sw[offset(V8_TOXIC_SPIKES_0)] = 2
        self.f.restore(bytes(st_sw))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(480)
        self.f.pulse("DOWN", 30)
        self.f.pulse("A", 35)
        self.f.pulse("A", 35)
        self.f.run(1120)
        after_char = self.f.state()
        self.assertEqual(u16(after_char, PLAYER_BATTLE), 6)
        self.assertEqual(u16(after_char, PLAYER_BATTLE + 0x2A), 80)  # 160 - 80 (4x Rock)
        self.assertEqual(after_char[PLAYER_BATTLE + 0x18 + 3], 6)    # Flying imune a Sticky Web
        self.assertEqual(u32(after_char, PLAYER_BATTLE + 0x50), 0)   # Flying imune a Toxic Spikes

        # 3. Switch-in de Bulbasaur (slot 1, Grass/Poison, aterrado): absorve Toxic Spikes + toma SR (1/8) + Sticky Web (-1 Spd)!
        b1 = bytearray(seed_mon(self.fixture, 6, 10, (369, 150, 150, 150)))
        set_exp_and_test_stats(b1, 6, 10)
        b2 = bytearray(seed_mon(self.fixture, 1, 10, (33, 22, 150, 150)))
        set_exp_and_test_stats(b2, 1, 10)
        b1[offset(PARTY + 100) : offset(PARTY + 200)] = b2[offset(PARTY) : offset(PARTY) + 100]
        b1[offset(PLAYER_PARTY_COUNT)] = 2
        bulb_fix = self._enter_wild_encounter(b1)
        st_back = bytearray(self._duel_state(369, foe_move=150, base_state=bulb_fix))
        st_back[offset(V8_STEALTH_ROCK_0)] = 1
        st_back[offset(V8_STICKY_WEB_0)] = 1
        st_back[offset(V8_TOXIC_SPIKES_0)] = 2
        self.f.restore(bytes(st_back))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(480)
        self.f.pulse("DOWN", 30)
        self.f.pulse("A", 35)
        self.f.pulse("A", 35)
        self.f.run(1120)
        after_bulb = self.f.state()
        self.assertEqual(u16(after_bulb, PLAYER_BATTLE), 1)
        self.assertEqual(after_bulb[offset(V8_TOXIC_SPIKES_0)], 0)   # Poison aterrado absorveu Toxic Spikes!
        self.assertEqual(u32(after_bulb, PLAYER_BATTLE + 0x50), 0)   # nao foi envenenado
        self.assertEqual(after_bulb[PLAYER_BATTLE + 0x18 + 3], 5)    # Sticky Web baixou Speed para -1

        # 4. Toxic Spikes (2 camadas) envenena gravemente (0x80) um switch-in aterrado nao-Poison (Charmander, especie 4)
        s1 = bytearray(seed_mon(self.fixture, 1, 10, (369, 150, 150, 150)))
        set_exp_and_test_stats(s1, 1, 10)
        s2 = bytearray(seed_mon(self.fixture, 4, 10, (33, 52, 150, 150)))
        set_exp_and_test_stats(s2, 4, 10)
        s1[offset(PARTY + 100) : offset(PARTY + 200)] = s2[offset(PARTY) : offset(PARTY) + 100]
        s1[offset(PLAYER_PARTY_COUNT)] = 2
        charm_fix = self._enter_wild_encounter(s1)
        st_tsp = bytearray(self._duel_state(369, foe_move=150, base_state=charm_fix))
        st_tsp[offset(V8_TOXIC_SPIKES_0)] = 2
        self.f.restore(bytes(st_tsp))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(480)
        self.f.pulse("DOWN", 30)
        self.f.pulse("A", 35)
        self.f.pulse("A", 35)
        self.f.run(1050)
        after_charm = self.f.state()
        self.assertEqual(u16(after_charm, PLAYER_BATTLE), 4)
        self.assertTrue(u32(after_charm, PLAYER_BATTLE + 0x50) & 0x80)

        # 5. Mortal Spin (758): causa dano, envenena o alvo e limpa SR + TSpikes + Sticky Web + Spikes do usuario
        st_ms = bytearray(self._duel_state(758))
        st_ms[offset(V8_STEALTH_ROCK_0)] = 1
        st_ms[offset(V8_TOXIC_SPIKES_0)] = 2
        st_ms[offset(V8_STICKY_WEB_0)] = 1
        put16(st_ms, offset(SIDE_STATUSES_ADDR), 0x0010)
        st_ms[offset(SIDE_TIMERS_ADDR) + 0x0A] = 2
        ms_res, _ = self._run_turn(bytes(st_ms), frames=1050)
        self.assertLess(u16(ms_res, FOE_BATTLE + 0x2A), 480)
        self.assertTrue(u32(ms_res, FOE_BATTLE + 0x50) & 0x08)
        self.assertEqual(ms_res[offset(V8_STEALTH_ROCK_0)], 0)
        self.assertEqual(ms_res[offset(V8_TOXIC_SPIKES_0)], 0)
        self.assertEqual(ms_res[offset(V8_STICKY_WEB_0)], 0)
        self.assertEqual(u16(ms_res, offset(SIDE_STATUSES_ADDR)) & 0x0010, 0)

        # 6. Defog (432): -1 evasao, limpa Aurora Veil inimigo, limpa hazards dos 2 lados e limpa terreno
        st_df = bytearray(self._duel_state(432))
        st_df[offset(V8_AURORA_VEIL_1)] = 4
        st_df[offset(V8_STEALTH_ROCK_0)] = 1
        st_df[offset(V8_STEALTH_ROCK_1)] = 1
        st_df[offset(V8_TERRAIN_TYPE)] = 1
        st_df[offset(V8_TERRAIN_TURNS)] = 4
        df_res, _ = self._run_turn(bytes(st_df), frames=1050)
        self.assertEqual(df_res[FOE_BATTLE + 0x1F], 5)
        self.assertEqual(df_res[offset(V8_AURORA_VEIL_1)], 0)
        self.assertEqual(df_res[offset(V8_STEALTH_ROCK_0)], 0)
        self.assertEqual(df_res[offset(V8_STEALTH_ROCK_1)], 0)
        self.assertEqual(df_res[offset(V8_TERRAIN_TYPE)], 0)
        self.assertEqual(df_res[offset(V8_TERRAIN_TURNS)], 0)

        # 7. Tidy Up (772): limpa hazards + Substitute do oponente e sobe Atk +1 e Spd +1 do usuario
        st_tu = bytearray(self._duel_state(772))
        st_tu[offset(V8_STEALTH_ROCK_0)] = 1
        st_tu[offset(V8_STICKY_WEB_1)] = 1
        struct.pack_into("<I", st_tu, FOE_BATTLE + 0x54, 0x01000000)
        st_tu[offset(DISABLE_STRUCTS_ADDR) + 28 + 0x0A] = 40
        tu_res, _ = self._run_turn(bytes(st_tu), frames=1150)
        self.assertEqual(tu_res[offset(V8_STEALTH_ROCK_0)], 0)
        self.assertEqual(tu_res[offset(V8_STICKY_WEB_1)], 0)
        self.assertEqual(u32(tu_res, FOE_BATTLE + 0x54) & 0x01000000, 0)
        self.assertEqual(tu_res[offset(DISABLE_STRUCTS_ADDR) + 28 + 0x0A], 0)
        self.assertEqual(tu_res[PLAYER_BATTLE + 0x18 + 1], 7)
        self.assertEqual(tu_res[PLAYER_BATTLE + 0x18 + 3], 7)

        # 8. Court Change (681): troca hazards, Tailwind e barreiras entre os dois lados
        st_cc = bytearray(self._duel_state(681))
        st_cc[offset(V8_STEALTH_ROCK_0)] = 1
        st_cc[offset(V8_TOXIC_SPIKES_0)] = 2
        st_cc[offset(V8_TAILWIND_1)] = 3
        st_cc[offset(V8_AURORA_VEIL_1)] = 4
        cc_res, _ = self._run_turn(bytes(st_cc))
        self.assertEqual(cc_res[offset(V8_STEALTH_ROCK_0)], 0)
        self.assertEqual(cc_res[offset(V8_STEALTH_ROCK_1)], 1)
        self.assertEqual(cc_res[offset(V8_TOXIC_SPIKES_0)], 0)
        self.assertEqual(cc_res[offset(V8_TOXIC_SPIKES_1)], 2)
        self.assertEqual(cc_res[offset(V8_TAILWIND_0)], 2)     # 3 -> trocou p/ side 0 -> decaiu p/ 2 no fim do turno
        self.assertEqual(cc_res[offset(V8_AURORA_VEIL_0)], 3)  # 4 -> trocou p/ side 0 -> decaiu p/ 3 no fim do turno

    def test_tailwind_trick_room_wonder_room_gravity_magnet_rise_e_shore_up(self):
        # 1. Tailwind (366): dobra velocidade do lado (100*2=200 > f_speed=150), agindo primeiro e nocauteando
        st_tw = bytearray(self._duel_state(33, foe_move=33, p_speed=100, f_speed=150, f_hp=5, f_max=200))
        st_tw[offset(V8_TAILWIND_0)] = 3
        tw_res, _ = self._run_turn(bytes(st_tw))
        self.assertEqual(u16(tw_res, FOE_BATTLE + 0x2A), 0)
        self.assertEqual(u16(tw_res, PLAYER_BATTLE + 0x2A), 160)

        # 2. Trick Room (433): liga (5 -> 4), inverte ordem (p_speed=40 age antes de f_speed=300) e desliga no 2o uso
        tr_on, _ = self._run_turn(self._duel_state(433))
        self.assertEqual(tr_on[offset(V8_TRICK_ROOM_TURNS)], 4)

        st_tr_fight = bytearray(self._duel_state(33, foe_move=33, p_speed=40, f_speed=300, f_hp=5, f_max=200))
        st_tr_fight[offset(V8_TRICK_ROOM_TURNS)] = 4
        tr_fight, _ = self._run_turn(bytes(st_tr_fight))
        self.assertEqual(u16(tr_fight, FOE_BATTLE + 0x2A), 0)
        self.assertEqual(u16(tr_fight, PLAYER_BATTLE + 0x2A), 160)

        st_tr_off = bytearray(self._duel_state(433))
        st_tr_off[offset(V8_TRICK_ROOM_TURNS)] = 3
        tr_off, _ = self._run_turn(bytes(st_tr_off))
        self.assertEqual(tr_off[offset(V8_TRICK_ROOM_TURNS)], 0)

        # 3. Wonder Room (471): troca Defesa (60) e Def. Esp. (260) durante o calculo de dano fisico
        wr_plain, _ = self._run_turn(self._duel_state(33, f_def=60, f_spd_stat=260))
        st_wr = bytearray(self._duel_state(33, f_def=60, f_spd_stat=260))
        st_wr[offset(V8_WONDER_ROOM_TURNS)] = 4
        wr_swapped, _ = self._run_turn(bytes(st_wr))
        self.assertGreater(480 - u16(wr_plain, FOE_BATTLE + 0x2A), (480 - u16(wr_swapped, FOE_BATTLE + 0x2A)) * 2)

        # 4. Magnet Rise (393) concede imunidade a Earthquake (89); Gravity (356) derruba Magnet Rise/Flying/Levitate e bloqueia Fly (19)
        mr_set, _ = self._run_turn(self._duel_state(393))
        self.assertEqual(mr_set[offset(V8_MAGNET_RISE)], 4)

        st_mr_eq = bytearray(mr_set)
        put16(st_mr_eq, PLAYER_BATTLE + 0x0C, 150)
        for mslot in range(4):
            put16(st_mr_eq, FOE_BATTLE + 0x0C + 2 * mslot, 89)
        mr_eq_res, _ = self._run_turn(bytes(st_mr_eq))
        self.assertEqual(u16(mr_eq_res, PLAYER_BATTLE + 0x2A), 160)  # imune a Ground!

        # Sob Gravity: Earthquake acerta Flying + Levitate, e Fly (19) e cancelado
        st_grav_eq = bytearray(self._duel_state(89, f_types=(2, 2), f_ability=26))
        st_grav_eq[offset(V8_GRAVITY_TURNS)] = 4
        grav_eq, _ = self._run_turn(bytes(st_grav_eq))
        self.assertLess(u16(grav_eq, FOE_BATTLE + 0x2A), 480)

        st_grav_fly = bytearray(self._duel_state(19))
        st_grav_fly[offset(V8_GRAVITY_TURNS)] = 4
        grav_fly, seen_gfly = self._run_turn(bytes(st_grav_fly))
        self.assertEqual(u16(grav_fly, FOE_BATTLE + 0x2A), 480)
        self.assertTrue(any("gravidade" in s for s in seen_gfly), seen_gfly)

        # 5. Shore Up (614): cura 1/2 (90 de 180) normalmente e 2/3 (120 de 180) em Sandstorm (0x08)
        su_plain, _ = self._run_turn(self._duel_state(614, p_hp=20, p_max=180))
        self.assertEqual(u16(su_plain, PLAYER_BATTLE + 0x2A), 110)
        su_sand, _ = self._run_turn(
            self._duel_state(614, p_hp=20, p_max=180, p_types=(4, 4), f_types=(4, 4), weather=0x0008, weather_dur=4)
        )
        self.assertEqual(u16(su_sand, PLAYER_BATTLE + 0x2A), 140)

    def test_estojo_v2_10_tms_finais_229_completas_save_reload_e_learnsets_v8(self):
        # 1. Mew (151) compativel com todas as 10 TMs finais via CanPokemonLearnTMHM (0x080F8460)
        final_tms = (
            (426, 773), (465, 390), (487, 366), (490, 445), (510, 599),
            (511, 576), (512, 633), (513, 577), (535, 433), (552, 356),
        )
        for item_id, move_id in final_tms:
            with self.subTest(item_id=item_id, move_id=move_id):
                st = seed_mon(self.fixture, 151, 5, (33, 45, 0, 0))
                out = invoke(self.f, st, 0x080F8460, {0: PARTY, 1: item_id, 2: 0})
                self.assertEqual(u32(out, 0x20), 0)

        # 2. Ensino real nas 3 paginas do estojo_v2: Pag 0 HM01 (339), Pag 1 TM052 Snowscape (426), Pag 2 TM161 Trick Room (535)
        state = seed_mon(self.fixture, 151, 20, (33, 0, 0, 0))
        state = add(self.f, state, 339, 1)  # HM01 Cut (infinita: 1 -> 1)
        state = add(self.f, state, 426, 2)  # TM052 Snowscape (uso unico: 2 -> 1)
        state = add(self.f, state, 535, 1)  # TM161 Trick Room (uso unico: 1 -> 0)

        self.f.restore(bytes(state))
        open_case(self.f)
        for target_page, item_id, move_id, want_qty in (
            (0, 339, 15, 1),
            (1, 426, 773, 1),
            (2, 535, 433, 0),
        ):
            for _ in range(10):
                if page(self.f.state()) == target_page:
                    break
                self.f.pulse("A", 70)
                self.f.pulse("R", 90)
            self.assertEqual(page(self.f.state()), target_page)
            for _ in range(20):
                self.f.pulse("A", 90)
                if move_id in get_moves(self.f.state()):
                    break
            self.assertIn(move_id, get_moves(self.f.state()))
            for _ in range(8):
                self.f.pulse("A", 100)
                if item_id >= 375 and stored_quantity(self.f.state(), item_id) == want_qty:
                    break
            self.assertEqual(stored_quantity(self.f.state(), item_id), want_qty)

        after_tm = self.f.state()
        self.assertEqual(get_moves(after_tm), (33, 15, 773, 433))
        self.assertTrue(mon_facts(mon(after_tm))["valid"])

        flash = save_after_case(self.f)
        core_copy = self.dir / "core_reload_v8.so"
        if not core_copy.exists():
            shutil.copyfile(self.core, core_copy)
        reloaded = Emulator(self.rom, core_copy, self.dir)
        try:
            loaded_state = load_game(reloaded, flash)
            self.assertEqual(get_moves(loaded_state), (33, 15, 773, 433))
            self.assertEqual(get(reloaded, loaded_state, 339), 1)
            self.assertEqual(get(reloaded, loaded_state, 426), 1)
            self.assertEqual(get(reloaded, loaded_state, 535), 0)
            self.assertTrue(mon_facts(mon(loaded_state))["valid"])
        finally:
            reloaded.close()

        # 3. Learnsets de subida de nivel e Move Relearner para golpes restaurados no motor_v8
        out_buf = 0x02001200
        cases = (
            (137, 10, 393),  # Porygon -> Magnet Rise
            (163, 15, 432),  # Hoothoot -> Defog
            (493, 10, 356),  # Arceus -> Gravity
            (524, 8, 445),   # Roggenrola -> Stealth Rock
            (29, 20, 390),   # Nidoran F -> Toxic Spikes
            (380, 20, 366),  # Latias -> Tailwind
        )
        for species, lv, want in cases:
            with self.subTest(species=species, level=lv, want=want):
                st_lv = seed_mon(self.fixture, species, lv, (33, 45, 0, 0))
                res = invoke(self.f, st_lv, 0x08109790, {0: PARTY, 1: 1})
                self.assertIn(want, get_moves(res))
                self.assertTrue(mon_facts(mon(res))["valid"])

                st_rel = bytearray(seed_mon(self.fixture, species, 100, (33, 45, 10, 22)))
                st_rel[offset(out_buf) : offset(out_buf) + 64] = b"\x00" * 64
                got = invoke(self.f, st_rel, 0x0810E808, {0: PARTY, 1: out_buf})
                cnt = u32(got, 0x20)
                relearn_moves = struct.unpack_from(f"<{cnt}H", got, offset(out_buf))
                self.assertIn(want, relearn_moves)

    def test_regressao_cadeia_v6_v7_preservada(self):
        # Meteor Beam (817, v7): +1 Sp. Atk no turno 1 + dano no turno 2
        mb_res, _ = self._run_turn(self._duel_state(817), frames=1400)
        self.assertEqual(mb_res[PLAYER_BATTLE + 0x18 + 4], 7)
        self.assertLess(u16(mb_res, FOE_BATTLE + 0x2A), 480)

        # Psychic Noise (820, v7) bloqueia a cura de 1/16 do Grassy Terrain no fim do turno!
        st_pn = bytearray(self._duel_state(820, f_hp=300, f_max=480))
        st_pn[offset(V8_TERRAIN_TYPE)] = 2
        st_pn[offset(V8_TERRAIN_TURNS)] = 4
        pn_res, _ = self._run_turn(bytes(st_pn), frames=1050)
        hp_after_hit = u16(pn_res, FOE_BATTLE + 0x2A)
        self.assertLess(hp_after_hit, 300)
        self.assertEqual(pn_res[offset(V7_STATE_ADDR) + 8 + 1], 2)  # heal_block_turns[1] ativo

        # Triple Axel (812, v6): 20 -> 40 -> 60 BP continua encadeando hook_damage_v8 -> v7 -> v6
        self.f.restore(self._duel_state(812))
        self.f.pulse("A", 25)
        self.f.run(6, "A")
        seen_powers: set[int] = set()
        for _ in range(1900):
            self.f.run(1)
            pwr = u16(self.f.state(), offset(0x02021792))
            if pwr:
                seen_powers.add(pwr)
        self.assertEqual(seen_powers, {20, 40, 60})
        self.assertEqual(self.f.state()[offset(BUFF3)], 0xAA)


if __name__ == "__main__":
    unittest.main()
