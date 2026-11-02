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

from mgba_treino_harness import Emulator, PARTY, mon, mon_facts, offset, put16, u16, u32
from test_atualizacoes_gen9_mgba import FOE_BATTLE, PLAYER_BATTLE
from test_estojo_expandido_mgba import add, get, open_case, page, save_after_case
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

# Offsets dentro de struct V9BattleState (0x0203FCA0, 100 B)
V9_LAST_USED_MOVE = V9_STATE_ADDR + 0x20
V9_AQUA_RING_MASK = V9_STATE_ADDR + 0x24
V9_TAR_SHOT_MASK = V9_STATE_ADDR + 0x25
V9_NO_RETREAT_MASK = V9_STATE_ADDR + 0x26
V9_GASTRO_ACID_MASK = V9_STATE_ADDR + 0x27
V9_ELECTRIFIED_MASK = V9_STATE_ADDR + 0x28
V9_EXTRA_TYPE = V9_STATE_ADDR + 0x29          # 4 B
V9_LASER_FOCUS_TURNS = V9_STATE_ADDR + 0x2D   # 4 B
V9_OCTOLOCK_ACTIVE = V9_STATE_ADDR + 0x31     # 4 B
V9_FAIRY_LOCK_TURNS = V9_STATE_ADDR + 0x39
V9_HEALING_WISH_PENDING = V9_STATE_ADDR + 0x3B  # 2 B


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
        state = bytearray(seed_mon(cls.fixture, 1, 10, (486, 563, 380, 150)))
        set_exp_and_test_stats(state, 1, 10)
        return cls._enter_wild_encounter(state)

    @classmethod
    def _make_two_party_singles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (770, 361, 460, 150)))
        set_exp_and_test_stats(s1, 1, 10)
        # Slot 1: Charmander (4) ferido (40/160 HP), paralisado e com PP reduzido p/ testar Healing Wish / Lunar Dance / Shed Tail
        s2 = bytearray(seed_mon(cls.fixture, 4, 10, (52, 33, 150, 150)))
        set_exp_and_test_stats(s2, 4, 10)
        put16(s2, offset(PARTY) + 86, 40)
        put16(s2, offset(PARTY) + 88, 160)
        s1[offset(PARTY + 100) : offset(PARTY + 200)] = s2[offset(PARTY) : offset(PARTY) + 100]
        s1[offset(PLAYER_PARTY_COUNT)] = 2
        return cls._enter_wild_encounter(s1)

    @classmethod
    def _make_doubles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (494, 510, 710, 150)))
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
        p_status1: int = 0,
        f_hp: int = 480,
        f_max: int = 480,
        f_atk: int = 180,
        f_def: int = 140,
        f_spa: int = 180,
        f_spd_stat: int = 140,
        f_speed: int = 40,
        f_types: tuple[int, int] = (0, 0),
        f_ability: int = 4,
        f_status1: int = 0,
        acc_stage: int = 12,
        eva_stage: int = 6,
        base_state: bytes | None = None,
    ) -> bytes:
        st = bytearray(self.battle_fixture if base_state is None else base_state)
        if p_species is not None:
            put16(st, PLAYER_BATTLE, p_species)
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
        put16(st, PLAYER_BATTLE + 0x20, p_ability)
        st[PLAYER_BATTLE + 0x22], st[PLAYER_BATTLE + 0x23] = p_types
        st[PLAYER_BATTLE + 0x2C] = 10
        struct.pack_into("<II", st, PLAYER_BATTLE + 0x50, p_status1, 0)

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
        struct.pack_into("<II", st, FOE_BATTLE + 0x50, f_status1, 0)

        st[offset(SIDE_STATUSES_ADDR) : offset(SIDE_STATUSES_ADDR) + 4] = b"\x00" * 4
        st[offset(SIDE_TIMERS_ADDR) : offset(SIDE_TIMERS_ADDR) + 24] = b"\x00" * 24
        st[offset(STATUSES3_ADDR) : offset(STATUSES3_ADDR) + 16] = b"\x00" * 16
        put16(st, offset(BATTLE_WEATHER_ADDR), 0)
        st[offset(WEATHER_DURATION_ADDR)] = 0
        st[offset(V7_STATE_ADDR) : offset(V7_STATE_ADDR) + 96] = b"\x00" * 96
        st[offset(V8_STATE_ADDR) : offset(V8_STATE_ADDR) + 64] = b"\x00" * 64
        st[offset(V9_STATE_ADDR) : offset(V9_STATE_ADDR) + 100] = b"\x00" * 100
        # Preenche active_tag inicial p/ preservar estados V9 pre-configurados quando necessario
        for b_idx, b_off in ((0, PLAYER_BATTLE), (1, FOE_BATTLE)):
            pid = u32(st, b_off + 0x4C)
            slot = u16(st, offset(0x020213F8 + 2 * b_idx))
            tag = 0x80000000 | ((slot & 7) << 28) | (pid & 0x0FFFFFFF)
            struct.pack_into("<I", st, offset(V9_STATE_ADDR + 4 * b_idx), tag)
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

    def test_familia1_tipos_soak_magic_powder_reflect_type_terceiro_tipo_e_tar_shot(self):
        # 1. Soak (486): transforma alvo em puro Agua (11, 11)
        soak_res, seen_soak = self._run_turn(self._duel_state(486, f_types=(10, 2)))
        self.assertEqual((soak_res[FOE_BATTLE + 0x22], soak_res[FOE_BATTLE + 0x23]), (11, 11))
        self.assertTrue(any("gua" in s for s in seen_soak), seen_soak)

        # 2. Magic Powder (675): transforma Normal em Psiquico (14, 14), mas falha em Planta (12)
        mp_ok, _ = self._run_turn(self._duel_state(675, f_types=(0, 0)))
        self.assertEqual((mp_ok[FOE_BATTLE + 0x22], mp_ok[FOE_BATTLE + 0x23]), (14, 14))
        mp_grass, _ = self._run_turn(self._duel_state(675, f_types=(12, 12)))
        self.assertEqual((mp_grass[FOE_BATTLE + 0x22], mp_grass[FOE_BATTLE + 0x23]), (12, 12))

        # 3. Trick-or-Treat (563) adiciona 3o tipo Fantasma (7): imune (0x) a Fighting (280) e 2x fraco a Dark (242)!
        tot_res, _ = self._run_turn(self._duel_state(563, f_types=(0, 0)))
        self.assertEqual(tot_res[offset(V9_EXTRA_TYPE) + 1], 7)

        cr_plain, _ = self._run_turn(self._duel_state(242, f_types=(0, 0)))
        st_cr_tot = bytearray(self._duel_state(242, f_types=(0, 0)))
        st_cr_tot[offset(V9_EXTRA_TYPE) + 1] = 7
        cr_tot, _ = self._run_turn(bytes(st_cr_tot))
        self.assertGreaterEqual(480 - u16(cr_tot, FOE_BATTLE + 0x2A), int((480 - u16(cr_plain, FOE_BATTLE + 0x2A)) * 1.8))

        st_bb_tot = bytearray(self._duel_state(280, f_types=(0, 0)))
        st_bb_tot[offset(V9_EXTRA_TYPE) + 1] = 7
        bb_tot, _ = self._run_turn(bytes(st_bb_tot))
        self.assertEqual(u16(bb_tot, FOE_BATTLE + 0x2A), 480)

        # Reflect Type (512) copia tipos primarios e tambem o 3o tipo extra_type do alvo
        st_rt = bytearray(self._duel_state(512, p_types=(0, 0), f_types=(10, 2)))
        st_rt[offset(V9_EXTRA_TYPE) + 1] = 12  # Forest's Curse Grass no alvo
        rt_res, _ = self._run_turn(bytes(st_rt))
        self.assertEqual((rt_res[PLAYER_BATTLE + 0x22], rt_res[PLAYER_BATTLE + 0x23]), (10, 2))
        self.assertEqual(rt_res[offset(V9_EXTRA_TYPE)], 12)

        # 4. Tar Shot (674): reduz Speed -1, liga tar_shot_mask e dobra dano de Flamethrower (53, Fogo)
        ts_res, _ = self._run_turn(self._duel_state(674))
        self.assertEqual(ts_res[FOE_BATTLE + 0x1B], 5)
        self.assertTrue(ts_res[offset(V9_TAR_SHOT_MASK)] & 0x02)

        ft_plain, _ = self._run_turn(self._duel_state(53, p_spa=180, f_spd_stat=180))
        st_ft_tar = bytearray(self._duel_state(53, p_spa=180, f_spd_stat=180))
        st_ft_tar[offset(V9_TAR_SHOT_MASK)] = 0x02
        ft_tar, _ = self._run_turn(bytes(st_ft_tar))
        dmg_plain = 480 - u16(ft_plain, FOE_BATTLE + 0x2A)
        dmg_tar = 480 - u16(ft_tar, FOE_BATTLE + 0x2A)
        self.assertGreaterEqual(dmg_tar, int(dmg_plain * 1.8))

    def test_familia2_habilidades_gastro_acid_worry_seed_entrainment_doodle_e_electrify(self):
        # 1. Gastro Acid (380) suprime Levitate (26 -> 0), permitindo Earthquake (89) acertar no turno seguinte
        ga_res, _ = self._run_turn(self._duel_state(380, move2_id=89, f_ability=26))
        self.assertEqual(u16(ga_res, FOE_BATTLE + 0x20), 0)
        eq_after_ga, _ = self._run_turn(ga_res, slot=1)
        self.assertLess(u16(eq_after_ga, FOE_BATTLE + 0x2A), 480)

        # 2. Worry Seed (388): define Insomnia (15) e acorda imediatamente alvo adormecido (status1=3 -> 0)
        ws_res, seen_ws = self._run_turn(self._duel_state(388, f_ability=4, f_status1=3))
        self.assertEqual(u16(ws_res, FOE_BATTLE + 0x20), 15)
        self.assertEqual(u32(ws_res, FOE_BATTLE + 0x50), 0)
        self.assertTrue(any("acordou" in s for s in seen_ws), seen_ws)

        # 3. Entrainment (493) copia habilidade do usuario para o alvo, mas falha contra Truant (54)
        ent_ok, _ = self._run_turn(self._duel_state(493, p_ability=26, f_ability=4))
        self.assertEqual(u16(ent_ok, FOE_BATTLE + 0x20), 26)
        ent_fail, _ = self._run_turn(self._duel_state(493, p_ability=26, f_ability=54))
        self.assertEqual(u16(ent_fail, FOE_BATTLE + 0x20), 54)

        # 4. Doodle (759) copia habilidade do alvo (Levitate 26) para o usuario
        doo_res, _ = self._run_turn(self._duel_state(759, p_ability=4, f_ability=26))
        self.assertEqual(u16(doo_res, PLAYER_BATTLE + 0x20), 26)

        # 5. Electrify (578): converte Tackle (33, Normal) do oponente em Eletrico (13), dando 0 dano em usuario Terra (4)!
        elec_res, _ = self._run_turn(self._duel_state(578, foe_move=33, p_types=(4, 4)))
        self.assertEqual(u16(elec_res, PLAYER_BATTLE + 0x2A), 160)

    def test_familia3_trocas_divisoes_inversao_buffs_e_strength_sap(self):
        # 1. Power Trick (379) permuta Atk e Def do usuario; Speed Swap (638) permuta Speed; Power Split (470) tira media
        pt_res, _ = self._run_turn(self._duel_state(379, p_atk=90, p_def=250))
        self.assertEqual((u16(pt_res, PLAYER_BATTLE + 0x02), u16(pt_res, PLAYER_BATTLE + 0x04)), (250, 90))

        ss_res, _ = self._run_turn(self._duel_state(638, p_speed=310, f_speed=50))
        self.assertEqual((u16(ss_res, PLAYER_BATTLE + 0x06), u16(ss_res, FOE_BATTLE + 0x06)), (50, 310))

        ps_res, _ = self._run_turn(self._duel_state(470, p_atk=100, f_atk=300, p_spa=80, f_spa=200))
        self.assertEqual((u16(ps_res, PLAYER_BATTLE + 0x02), u16(ps_res, FOE_BATTLE + 0x02)), (200, 200))
        self.assertEqual((u16(ps_res, PLAYER_BATTLE + 0x08), u16(ps_res, FOE_BATTLE + 0x08)), (140, 140))

        # 2. Heart Swap (391) e Topsy-Turvy (572)
        st_tt = bytearray(self._duel_state(572))
        st_tt[FOE_BATTLE + 0x19] = 10   # +4 Atk -> -4 (2)
        st_tt[FOE_BATTLE + 0x1A] = 4    # -2 Def -> +2 (8)
        tt_res, _ = self._run_turn(bytes(st_tt))
        self.assertEqual((tt_res[FOE_BATTLE + 0x19], tt_res[FOE_BATTLE + 0x1A]), (2, 8))

        # 3. Spicy Extract (750): +2 Atk (8) e -2 Def (4); Decorate (684): +2 Atk/SpAtk; Venom Drench (595); Toxic Thread (627)
        se_res, _ = self._run_turn(self._duel_state(750))
        self.assertEqual((se_res[FOE_BATTLE + 0x19], se_res[FOE_BATTLE + 0x1A]), (8, 4))

        dec_res, _ = self._run_turn(self._duel_state(684), frames=1100)
        self.assertEqual((dec_res[FOE_BATTLE + 0x19], dec_res[FOE_BATTLE + 0x1C]), (8, 8))

        vd_res, _ = self._run_turn(self._duel_state(595, f_status1=0x08), frames=1200)
        self.assertEqual((vd_res[FOE_BATTLE + 0x19], vd_res[FOE_BATTLE + 0x1C], vd_res[FOE_BATTLE + 0x1B]), (5, 5, 5))

        acu_res, _ = self._run_turn(self._duel_state(367), frames=1050)
        self.assertIn(8, [acu_res[PLAYER_BATTLE + 0x18 + s] for s in range(1, 8)])

        rot_res, _ = self._run_turn(self._duel_state(559, p_types=(12, 12), f_types=(12, 2)), frames=1100)
        self.assertEqual((rot_res[PLAYER_BATTLE + 0x19], rot_res[PLAYER_BATTLE + 0x1C]), (7, 7))
        self.assertEqual((rot_res[FOE_BATTLE + 0x19], rot_res[FOE_BATTLE + 0x1C]), (6, 6))  # Flying nao esta aterrado

        mf_res, _ = self._run_turn(self._duel_state(598, p_ability=57), frames=1100)
        self.assertEqual((mf_res[PLAYER_BATTLE + 0x1A], mf_res[PLAYER_BATTLE + 0x1D]), (7, 7))

        tth_res, _ = self._run_turn(self._duel_state(627), frames=1100)
        self.assertEqual(tth_res[FOE_BATTLE + 0x1B], 5)
        self.assertEqual(u32(tth_res, FOE_BATTLE + 0x50), 0x08)

        # 4. Strength Sap (623): cura HP pelo Ataque efetivo do alvo (100) e reduz Atk -1; Liquid Ooze (64) fere em vez de curar!
        sap_ok, _ = self._run_turn(self._duel_state(623, p_hp=40, p_max=160, f_atk=100), frames=1100)
        self.assertEqual(sap_ok[FOE_BATTLE + 0x19], 5)
        self.assertEqual(u16(sap_ok, PLAYER_BATTLE + 0x2A), 140)

        sap_ooze, seen_ooze = self._run_turn(
            self._duel_state(623, p_hp=150, p_max=160, f_atk=60, f_ability=64), frames=1100
        )
        self.assertEqual(u16(sap_ooze, PLAYER_BATTLE + 0x2A), 90)
        self.assertTrue(any("lodo" in s for s in seen_ooze), seen_ooze)

    def test_familia4_sacrificio_clerigo_aqua_ring_laser_focus_final_gambit_e_dark_void(self):
        # 1. Fillet Away (760) e Clangorous Soul (682)
        fa_res, _ = self._run_turn(self._duel_state(760, p_hp=160, p_max=160), frames=1250)
        self.assertEqual(u16(fa_res, PLAYER_BATTLE + 0x2A), 80)
        self.assertEqual(
            (fa_res[PLAYER_BATTLE + 0x19], fa_res[PLAYER_BATTLE + 0x1C], fa_res[PLAYER_BATTLE + 0x1B]),
            (8, 8, 8),
        )

        cs_res, _ = self._run_turn(self._duel_state(682, p_hp=150, p_max=150), frames=1400)
        self.assertEqual(u16(cs_res, PLAYER_BATTLE + 0x2A), 100)
        for s in range(1, 6):
            self.assertEqual(cs_res[PLAYER_BATTLE + 0x18 + s], 7)

        # Take Heart (743): cura status1 e sobe SpAtk +1 e SpDef +1
        th_res, _ = self._run_turn(self._duel_state(743, p_status1=0x08), frames=1200)
        self.assertEqual(u32(th_res, PLAYER_BATTLE + 0x50), 0)
        self.assertEqual((th_res[PLAYER_BATTLE + 0x1C], th_res[PLAYER_BATTLE + 0x1D]), (7, 7))

        # 2. No Retreat (673): sobe os 5 atributos +1 (7), prende o usuario (0x04000000) e falha se repetido!
        nr_res, _ = self._run_turn(self._duel_state(673), frames=1450)
        for s in range(1, 6):
            self.assertEqual(nr_res[PLAYER_BATTLE + 0x18 + s], 7)
        self.assertTrue(u32(nr_res, PLAYER_BATTLE + 0x54) & 0x04000000)
        nr_again, _ = self._run_turn(nr_res, frames=980)
        self.assertEqual(nr_again[PLAYER_BATTLE + 0x19], 7)

        # 3. Aqua Ring (392) cura 1/16 (10 de 160) no fim do turno; Laser Focus (628) garante critico no turno seguinte
        ar_res, _ = self._run_turn(self._duel_state(392, p_hp=100, p_max=160), frames=1100)
        self.assertEqual(u16(ar_res, PLAYER_BATTLE + 0x2A), 110)

        lf_t1, _ = self._run_turn(self._duel_state(628, move2_id=33, f_ability=0, p_atk=220, f_def=160))
        self.assertEqual(lf_t1[offset(V9_LASER_FOCUS_TURNS)], 2)
        lf_t2, seen_lf2 = self._run_turn(lf_t1, slot=1)
        self.assertTrue(any("cr" in s.lower() for s in seen_lf2), seen_lf2)
        self.assertLess(u16(lf_t2, FOE_BATTLE + 0x2A), 480)

        # 4. Psycho Shift (375) transfere Burn (0x10 -> alvo 0x10, usuario 0); Purify (640) cura alvo e restaura 50% HP
        psh_res, _ = self._run_turn(self._duel_state(375, p_status1=0x10, f_types=(0, 0)), frames=1200)
        self.assertEqual(u32(psh_res, PLAYER_BATTLE + 0x50), 0)
        self.assertEqual(u32(psh_res, FOE_BATTLE + 0x50), 0x10)

        pur_res, _ = self._run_turn(self._duel_state(640, p_hp=50, p_max=160, f_status1=0x40), frames=1200)
        self.assertEqual(u32(pur_res, FOE_BATTLE + 0x50), 0)
        self.assertEqual(u16(pur_res, PLAYER_BATTLE + 0x2A), 130)

        # 5. Final Gambit (514): causa dano exato igual ao HP atual do usuario (123) e desmaia usuario; falha em Ghost (7)!
        fg_ghost, _ = self._run_turn(self._duel_state(514, p_hp=123, p_max=160, f_types=(7, 7)))
        self.assertEqual(u16(fg_ghost, FOE_BATTLE + 0x2A), 480)
        self.assertEqual(u16(fg_ghost, PLAYER_BATTLE + 0x2A), 123)

        fg_hit, _ = self._run_turn(
            self._duel_state(514, p_hp=123, p_max=160, f_types=(0, 0), base_state=self.two_party_battle_fixture),
            frames=700,
        )
        self.assertEqual(u16(fg_hit, FOE_BATTLE + 0x2A), 480 - 123)
        self.assertEqual(u16(fg_hit, PLAYER_BATTLE + 0x2A), 0)

        # 6. Dark Void (463): bloqueado para Smeargle (235), mas permitido para Darkrai (491) com Compound Eyes (14) + Acc +6
        dv_smeargle, seen_dvs = self._run_turn(self._duel_state(463, p_species=235))
        self.assertEqual(u32(dv_smeargle, FOE_BATTLE + 0x50), 0)
        self.assertTrue(any("consegue usar" in s for s in seen_dvs), seen_dvs)

        dv_darkrai, _ = self._run_turn(self._duel_state(463, p_species=491, p_ability=14, acc_stage=12, eva_stage=0))
        self.assertTrue(u32(dv_darkrai, FOE_BATTLE + 0x50) & 0x07)

    def test_shed_tail_healing_wish_e_lunar_dance_com_troca_real(self):
        # 1. Shed Tail (770): consome 50% HP (80/160), cria Substitute (40 HP) e transfere para Charmander (slot 1)!
        st_shed = bytearray(self._duel_state(770, p_hp=160, p_max=160, base_state=self.two_party_battle_fixture))
        self.f.restore(bytes(st_shed))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(480)
        self.f.pulse("DOWN", 30)
        self.f.pulse("A", 35)
        self.f.pulse("A", 35)
        self.f.run(1050)
        after_shed = self.f.state()
        self.assertEqual(u16(after_shed, PLAYER_BATTLE), 4)
        self.assertTrue(u32(after_shed, PLAYER_BATTLE + 0x54) & 0x01000000)
        self.assertEqual(after_shed[offset(DISABLE_STRUCTS_REAL_ADDR) + 0x0A], 40)
        # Bulbasaur na party ficou com 80/160 HP
        self.assertEqual(u16(after_shed, offset(PARTY) + 86), 80)

        # 2. Lunar Dance (460): usuario desmaia e Charmander ferido (40/160 HP, paralisado) entra sob Stealth Rock:
        # cura primeiro para 160/160 + status1=0 e sobrevive ao Stealth Rock (160 - 40 = 120 HP)!
        st_ld = bytearray(self._duel_state(460, p_hp=120, p_max=160, base_state=self.two_party_battle_fixture))
        struct.pack_into("<I", st_ld, offset(PARTY + 100) + 80, 0x40)
        st_ld[offset(V8_STATE_ADDR + 12)] = 1  # Stealth Rock ativo no lado 0
        self.f.restore(bytes(st_ld))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(400)
        self.f.pulse("A", 40)   # confirma desmaio do usuario
        self.f.run(280)
        self.f.pulse("A", 80)   # confirma 'Usar proximo POKeMON? -> SIM'
        self.f.run(120)
        self.f.pulse("DOWN", 30)
        self.f.pulse("A", 35)
        self.f.pulse("A", 35)
        self.f.run(1350)
        after_ld = self.f.state()
        self.assertEqual(u16(after_ld, PLAYER_BATTLE), 4)
        self.assertEqual(u16(after_ld, PLAYER_BATTLE + 0x2A), 120)  # 40 -> 160 (Lunar Dance) -> 120 (Stealth Rock)
        self.assertEqual(u32(after_ld, PLAYER_BATTLE + 0x50), 0)
        self.assertEqual(after_ld[offset(V9_HEALING_WISH_PENDING)], 0)

    def test_familia5_copycat_octolock_fairy_lock_e_duplas_after_you_quash_jungle_healing(self):
        # 1. Copycat (383): copia Flamethrower (53) usado pelo oponente quando usuario age depois
        st_cc = self._duel_state(383, foe_move=53, p_speed=40, f_speed=300, p_hp=160, p_max=160, f_spa=60)
        cc_res, _ = self._run_turn(st_cc, frames=1250)
        self.assertEqual(u16(cc_res, offset(V9_LAST_USED_MOVE)), 53)
        self.assertLess(u16(cc_res, FOE_BATTLE + 0x2A), 480)

        # 2. Octolock (678) prende alvo e reduz Def -1 e Sp. Def -1 ja no fim do turno; Fairy Lock (583) decai 2 -> 1 -> 0
        oct_res, _ = self._run_turn(self._duel_state(678), frames=1250)
        self.assertEqual(oct_res[offset(V9_OCTOLOCK_ACTIVE) + 1], 1)
        self.assertTrue(u32(oct_res, FOE_BATTLE + 0x54) & 0x04000000)
        self.assertEqual((oct_res[FOE_BATTLE + 0x1A], oct_res[FOE_BATTLE + 0x1D]), (5, 5))

        fl_t1, _ = self._run_turn(self._duel_state(583, move2_id=150))
        self.assertEqual(fl_t1[offset(V9_FAIRY_LOCK_TURNS)], 1)
        self.assertTrue(u32(fl_t1, FOE_BATTLE + 0x54) & 0x04000000)
        fl_t2, _ = self._run_turn(fl_t1, slot=1)
        self.assertEqual(fl_t2[offset(V9_FAIRY_LOCK_TURNS)], 0)
        self.assertEqual(u32(fl_t2, FOE_BATTLE + 0x54) & 0x04000000, 0)

        # 3. Duplas: After You (494) faz aliado lento (speed=20) agir antes dos oponentes (speed=180) e nocautear!
        st_ay = bytearray(self.doubles_fixture)
        b0, b1, b2, b3 = bank_off(0), bank_off(1), bank_off(2), bank_off(3)
        put16(st_ay, b0 + 0x0C, 494)   # Bank 0: After You (speed=320)
        st_ay[b0 + 0x25] = 15
        put16(st_ay, b2 + 0x0C, 53)    # Bank 2: Flamethrower (speed=20, lento!)
        st_ay[b2 + 0x25] = 15
        put16(st_ay, b2 + 0x08, 400)
        for bx in (b1, b3):
            for mslot in range(4):
                put16(st_ay, bx + 0x0C + 2 * mslot, 53 if bx == b1 else 150)
            put16(st_ay, bx + 0x08, 400)
        put16(st_ay, b1 + 0x2A, 10)    # Bank 1 com 10 HP: se Bank 2 agir antes de Bank 1, Bank 1 desmaia sem atacar!
        put16(st_ay, b1 + 0x2E, 200)
        put16(st_ay, b2 + 0x2A, 160)
        put16(st_ay, b2 + 0x2E, 160)
        put16(st_ay, b0 + 0x06, 320)
        put16(st_ay, b1 + 0x06, 180)
        put16(st_ay, b3 + 0x06, 100)
        put16(st_ay, b2 + 0x06, 20)
        st_ay[offset(V9_STATE_ADDR) : offset(V9_STATE_ADDR) + 100] = b"\x00" * 100

        self.f.restore(bytes(st_ay))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("DOWN", 18)       # seleciona aliado bank 2 para After You
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)          # bank 2 escolhe Flamethrower no alvo padrao (bank 1)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.run(1250)
        after_ay = self.f.state()
        self.assertEqual(u16(after_ay, b1 + 0x2A), 0)
        self.assertEqual(u16(after_ay, b2 + 0x2A), 160)  # Bank 1 nunca chegou a atacar!

        # Quash (510): atrasa bank 1 rapido (speed=260) para depois de bank 2 lento (speed=40), nocauteando-o sem agir!
        st_qu = bytearray(st_ay)
        put16(st_qu, b0 + 0x0C, 510)   # Bank 0: Quash (speed=320) no alvo padrao (bank 1)
        put16(st_qu, b1 + 0x06, 260)   # Bank 1 rapido (speed=260 > bank 2 speed=40)
        put16(st_qu, b2 + 0x06, 40)
        put16(st_qu, b3 + 0x06, 20)
        self.f.restore(bytes(st_qu))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)          # alvo padrao bank 1 para Quash
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)          # bank 2 escolhe Flamethrower em bank 1
        self.f.run(1250)
        after_qu = self.f.state()
        self.assertEqual(u16(after_qu, b1 + 0x2A), 0)
        self.assertEqual(u16(after_qu, b2 + 0x2A), 160)

        # 4. Duplas: Jungle Healing (710) cura 25% HP e limpa status1 tanto do usuario (b0) quanto do aliado (b2)
        st_jh = bytearray(self.doubles_fixture)
        put16(st_jh, b0 + 0x0C, 710)
        st_jh[b0 + 0x25] = 10
        put16(st_jh, b2 + 0x0C, 150)
        st_jh[b2 + 0x25] = 10
        for bx in (b1, b3):
            for mslot in range(4):
                put16(st_jh, bx + 0x0C + 2 * mslot, 150)
        put16(st_jh, b0 + 0x2A, 60)
        put16(st_jh, b0 + 0x2E, 160)
        struct.pack_into("<I", st_jh, b0 + 0x50, 0x08)
        put16(st_jh, b2 + 0x2A, 80)
        put16(st_jh, b2 + 0x2E, 160)
        struct.pack_into("<I", st_jh, b2 + 0x50, 0x40)
        put16(st_jh, b0 + 0x06, 300)
        put16(st_jh, b2 + 0x06, 200)
        put16(st_jh, b1 + 0x06, 40)
        put16(st_jh, b3 + 0x06, 30)
        st_jh[offset(V7_STATE_ADDR) : offset(V7_STATE_ADDR) + 96] = b"\x00" * 96
        st_jh[offset(V9_STATE_ADDR) : offset(V9_STATE_ADDR) + 100] = b"\x00" * 100

        self.f.restore(bytes(st_jh))
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)          # Jungle Healing tem tgt=0x10 (sem cursor de alvo)
        self.f.pulse("A", 25)
        self.f.pulse("A", 25)          # Bank 2 usa Splash
        self.f.run(1350)
        after_jh = self.f.state()
        self.assertEqual(u16(after_jh, b0 + 0x2A), 100)
        self.assertEqual(u32(after_jh, b0 + 0x50), 0)
        self.assertEqual(u16(after_jh, b2 + 0x2A), 120)
        self.assertEqual(u32(after_jh, b2 + 0x50), 0)

    def test_learnsets_v9_move_relearner_estojo_229_tms_save_reload_e_regressao_v6_v7_v8(self):
        # 1. Learnsets de subida de nivel e Move Relearner para golpes restaurados nas 5 familias do motor_v9
        out_buf = 0x02001200
        cases = (
            (55, 27, 486),   # Golduck -> Soak
            (491, 66, 463),  # Darkrai -> Darkrai's Dark Void (nivel 66)
            (488, 72, 460),  # Cresselia -> Lunar Dance
            (976, 30, 760),  # Veluza -> Fillet Away
            (967, 31, 770),  # Cyclizar -> Shed Tail
            (853, 1, 678),   # Grapploct -> Octolock
        )
        for species, lv, want in cases:
            with self.subTest(species=species, level=lv, want=want):
                st_lv = seed_mon(self.fixture, species, lv, (33, 45, 0, 0))
                res = invoke(self.f, st_lv, 0x08109790, {0: PARTY, 1: 1})
                self.assertTrue(mon_facts(mon(res))["valid"])
                if lv > 1:
                    self.assertIn(want, get_moves(res))

                st_rel = bytearray(seed_mon(self.fixture, species, 100, (33, 45, 10, 22)))
                st_rel[offset(out_buf) : offset(out_buf) + 64] = b"\x00" * 64
                got = invoke(self.f, st_rel, 0x0810E808, {0: PARTY, 1: out_buf})
                cnt = u32(got, 0x20)
                relearn_moves = struct.unpack_from(f"<{cnt}H", got, offset(out_buf))
                self.assertIn(want, relearn_moves)

        # 2. Preservacao do estojo_v2 paginavel (3 paginas: HM01 + TM052 + TM229) + save/reload sintetico
        state = seed_mon(self.fixture, 151, 20, (33, 0, 0, 0))
        state = add(self.f, state, 339, 1)  # HM01 Cut (infinita: 1 -> 1)
        state = add(self.f, state, 426, 2)  # TM052 Snowscape (uso unico: 2 -> 1)
        state = add(self.f, state, 603, 1)  # TM229 Upper Hand (uso unico: 1 -> 0)
        self.f.restore(bytes(state))
        open_case(self.f)
        for target_page, item_id, move_id, want_qty in (
            (0, 339, 15, 1),
            (1, 426, 773, 1),
            (2, 603, 821, 0),
        ):
            for _ in range(10):
                if page(self.f.state()) == target_page:
                    break
                self.f.pulse("A", 70)
                self.f.pulse("R", 90)
            self.assertEqual(page(self.f.state()), target_page)
            for _ in range(25):
                self.f.pulse("A", 90)
                if move_id in get_moves(self.f.state()):
                    break
            self.assertIn(move_id, get_moves(self.f.state()))
            for _ in range(8):
                self.f.pulse("A", 100)
                if item_id >= 375 and stored_quantity(self.f.state(), item_id) == want_qty:
                    break
            self.assertEqual(stored_quantity(self.f.state(), item_id), want_qty)

        flash = save_after_case(self.f)
        core_copy = self.dir / "core_reload_v9.so"
        if not core_copy.exists():
            shutil.copyfile(self.core, core_copy)
        reloaded = Emulator(self.rom, core_copy, self.dir)
        try:
            loaded_state = load_game(reloaded, flash)
            self.assertEqual(get_moves(loaded_state), (33, 15, 773, 821))
            self.assertEqual(get(reloaded, loaded_state, 339), 1)
            self.assertEqual(get(reloaded, loaded_state, 426), 1)
            self.assertEqual(get(reloaded, loaded_state, 603), 0)
            self.assertTrue(mon_facts(mon(loaded_state))["valid"])
        finally:
            reloaded.close()

        # 3. Regressao cruzada v6 + v7 + v8 + v9: Psychic Noise (820, v7) bloqueia Aqua Ring (v9) E Grassy Terrain (v8)!
        st_cross = bytearray(self._duel_state(820, f_hp=300, f_max=480))
        st_cross[offset(V8_STATE_ADDR)] = 2       # Grassy Terrain
        st_cross[offset(V8_STATE_ADDR + 1)] = 4
        st_cross[offset(V9_AQUA_RING_MASK)] = 0x02  # Aqua Ring no oponente tambem ativo!
        cross_res, _ = self._run_turn(bytes(st_cross), frames=1100)
        self.assertLess(u16(cross_res, FOE_BATTLE + 0x2A), 300)
        self.assertEqual(cross_res[offset(V7_STATE_ADDR) + 8 + 1], 2)
        self.assertEqual(cross_res[offset(BUFF3)], 0xAA)


if __name__ == "__main__":
    unittest.main()
