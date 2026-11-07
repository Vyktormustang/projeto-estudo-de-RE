"""Testes de integração em mGBA 0.10.5 do motor parcial v7 (apenas saves/estados sintéticos).

MOTOR_V7_ROM=/tmp/firered_gen1_9_work/roms/motor_v7.gba \
MOTOR_V7_BASE=/tmp/firered_gen1_9_work/roms/motor_v6.gba \
MGBA_CORE=/tmp/mgba-build/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v7*.py' -v
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
if str(ROOT / 'tests') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tests'))

from mgba_treino_harness import Emulator, PARTY, mon, mon_facts, offset, put16, u16, u32
from test_atualizacoes_gen9_mgba import FOE_BATTLE, PLAYER_BATTLE
from test_estojo_expandido_mgba import add, get, open_case, page, save_after_case
from test_eventos_fixos_mgba import enemy, route_entry_fixture, route_from_entry
from test_golpes_gen9_integracao import load_game, set_exp_and_test_stats
from test_golpes_gen9_mgba import invoke, moves as get_moves, seed_mon
from test_motor_ampliado_mgba import stored_quantity
from scripts import motor_v7 as patch

ROM_ENV = os.environ.get('MOTOR_V7_ROM')
BASE_ENV = os.environ.get('MOTOR_V7_BASE')
CORE_ENV = os.environ.get('MGBA_CORE')

DISP_STR = 0x020201B4
BUFF3 = 0x02020300
BATTLE_MONS_BASE = 0x02021410
PARTY_INDEXES_ADDR = 0x020213F8
ENEMY_PARTY_COUNT = 0x0203A730
PLAYER_PARTY_COUNT = 0x0203A731
ENEMY_PARTY_ADDR = 0x0203A734
V7_STATE_ADDR = 0x0203FC00

GBA_DECODE = {0x00: ' ', 0xAB: '!', 0xAC: '?', 0xAD: '.', 0xAE: '-', 0xFE: '\n'}
for _i in range(26):
    GBA_DECODE[0xBB + _i] = chr(ord('A') + _i)
    GBA_DECODE[0xD5 + _i] = chr(ord('a') + _i)
for _i in range(10):
    GBA_DECODE[0xA1 + _i] = chr(ord('0') + _i)


def decode_gba_str(raw: bytes) -> str:
    out = []
    for b in raw:
        if b == 0xFF:
            break
        out.append(GBA_DECODE.get(b, f'<{b:02x}>'))
    return ''.join(out)


def bank_off(bank: int) -> int:
    return offset(BATTLE_MONS_BASE + 0x5C * bank)


@unittest.skipUnless(ROM_ENV and BASE_ENV and CORE_ENV, 'defina MOTOR_V7_ROM, MOTOR_V7_BASE e MGBA_CORE')
class MotorV7MGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM_ENV).resolve()
        cls.base = Path(BASE_ENV).resolve()
        cls.core = Path(CORE_ENV).resolve()
        if cls.rom.read_bytes() != patch.build(cls.base.read_bytes()):
            raise ValueError('ROM motor_v7 diverge da reconstrução determinística')
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
            for btn in ('LEFT', 'RIGHT'):
                for _step in range(20):
                    cls.f.run(1, btn)
                    st = bytearray(cls.f.state())
                    if enemy(st)['valid'] and enemy(st)['species'] != 390:
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            raise AssertionError('Sem encontro selvagem para fixture de batalha')

        if doubles:
            for _ in range(250):
                st = bytearray(cls.f.state())
                bt = u32(st, offset(0x02020374))
                if bt == 0x04:
                    e0 = bytes(st[offset(ENEMY_PARTY_ADDR):offset(ENEMY_PARTY_ADDR) + 100])
                    st[offset(ENEMY_PARTY_ADDR + 100):offset(ENEMY_PARTY_ADDR + 200)] = e0
                    st[offset(ENEMY_PARTY_COUNT)] = 2
                    struct.pack_into('<I', st, offset(0x02020374), bt | 0x01)
                    cls.f.restore(bytes(st))
                    break
                cls.f.run(1)

        cls.f.run(400)
        for _ in range(10 if doubles else 6):
            cls.f.pulse('B', 45)
        return bytes(cls.f.state())

    @classmethod
    def _make_singles_fixture(cls) -> bytes:
        state = bytearray(seed_mon(cls.fixture, 1, 10, (813, 814, 815, 817)))
        set_exp_and_test_stats(state, 1, 10)
        return cls._enter_wild_encounter(state)

    @classmethod
    def _make_two_party_singles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (369, 517, 708, 571)))
        set_exp_and_test_stats(s1, 1, 10)
        s2 = bytearray(seed_mon(cls.fixture, 4, 10, (33, 52, 150, 150)))
        set_exp_and_test_stats(s2, 4, 10)
        s1[offset(PARTY + 100):offset(PARTY + 200)] = s2[offset(PARTY):offset(PARTY) + 100]
        s1[offset(PLAYER_PARTY_COUNT)] = 2
        return cls._enter_wild_encounter(s1)

    @classmethod
    def _make_doubles_fixture(cls) -> bytes:
        s1 = bytearray(seed_mon(cls.fixture, 1, 10, (816, 818, 696, 813)))
        set_exp_and_test_stats(s1, 1, 10)
        s2 = bytearray(seed_mon(cls.fixture, 4, 10, (150, 33, 150, 150)))
        set_exp_and_test_stats(s2, 4, 10)
        s1[offset(PARTY + 100):offset(PARTY + 200)] = s2[offset(PARTY):offset(PARTY) + 100]
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
        p_hp: int = 120,
        p_max: int = 120,
        p_atk: int = 130,
        p_spd: int = 300,
        f_spd: int = 40,
        f_types: tuple[int, int] = (0, 0),
        f_hp: int = 450,
        f_max: int = 450,
        f_ability: int = 0,
        acc_stage: int = 12,
        eva_stage: int = 6,
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
        put16(st, PLAYER_BATTLE + 0x04, 130)
        put16(st, PLAYER_BATTLE + 0x06, p_spd)
        put16(st, PLAYER_BATTLE + 0x08, 130)
        put16(st, PLAYER_BATTLE + 0x0A, 130)
        st[PLAYER_BATTLE + 0x2C] = 10
        st[PLAYER_BATTLE + 0x50:PLAYER_BATTLE + 0x58] = b'\x00' * 8

        for mslot in range(4):
            put16(st, FOE_BATTLE + 0x0C + 2 * mslot, foe_move)
            st[FOE_BATTLE + 0x25 + mslot] = 40
        put16(st, FOE_BATTLE + 0x02, 90)
        put16(st, FOE_BATTLE + 0x04, 140)
        put16(st, FOE_BATTLE + 0x06, f_spd)
        put16(st, FOE_BATTLE + 0x08, 90)
        put16(st, FOE_BATTLE + 0x0A, 140)
        st[FOE_BATTLE + 0x20] = f_ability
        put16(st, FOE_BATTLE + 0x2A, f_hp)
        put16(st, FOE_BATTLE + 0x2E, f_max)
        st[FOE_BATTLE + 0x50:FOE_BATTLE + 0x58] = b'\x00' * 8
        st[FOE_BATTLE + 0x22], st[FOE_BATTLE + 0x23] = f_types
        st[offset(V7_STATE_ADDR):offset(V7_STATE_ADDR) + 96] = b'\x00' * 96
        st[offset(BUFF3)] = 0xAA
        return bytes(st)

    def _run_turn(self, state: bytes, *, slot: int = 0, frames: int = 820) -> tuple[bytes, list[str]]:
        self.f.restore(state)
        seen: list[str] = []
        self.f.pulse('A', 25)
        if slot == 1:
            self.f.pulse('RIGHT', 15)
        self.f.run(6, 'A')
        for _ in range(frames):
            self.f.run(1)
            cur = self.f.state()
            txt = decode_gba_str(cur[offset(DISP_STR):offset(DISP_STR) + 80])
            if txt and (not seen or seen[-1] != txt):
                seen.append(txt)
        return self.f.state(), seen

    def test_nomes_813_a_821_e_truncamento_16_chars_sem_invadir_buff3(self):
        for move_id, label in (
            (813, 'BURNING JEALOU!'),  # 16 caracteres truncados com segurança em 14 + '!' + 0xFF
            (814, 'LASH OUT!'),
            (815, 'TEMPER FLARE!'),
            (816, 'COACHING!'),
            (818, 'DRAGON CHEER!'),
            (819, 'ALLURING VOICE!'),
            (820, 'PSYCHIC NOISE!'),
            (821, 'UPPER HAND!'),
        ):
            with self.subTest(move_id=move_id):
                end, seen = self._run_turn(self._duel_state(move_id), frames=520)
                self.assertTrue(any(label in s for s in seen), f'{move_id}: {seen}')
                self.assertEqual(end[offset(BUFF3)], 0xAA)

    def test_pivots_uturn_volt_switch_flip_turn_e_parting_shot_trocam_sem_baton_pass(self):
        for move_id in (369, 517, 708, 571):
            with self.subTest(move_id=move_id):
                st = bytearray(self._duel_state(move_id, base_state=self.two_party_battle_fixture))
                st[PLAYER_BATTLE + 0x18 + 1] = 8  # +2 Attack antes da troca (não pode ser herdado!)
                self.f.restore(bytes(st))
                self.f.pulse('A', 25)
                self.f.pulse('A', 25)
                # Parting Shot exibe duas quedas de estágio antes de abrir a tela de equipe
                self.f.run(680 if move_id == 571 else 480)
                self.f.pulse('DOWN', 30)
                self.f.pulse('A', 35)
                self.f.pulse('A', 35)
                self.f.run(540)
                end = self.f.state()
                self.assertEqual(u16(end, offset(PARTY_INDEXES_ADDR)), 1, f'Golpe {move_id} não trocou para o slot 1')
                self.assertEqual(u16(end, PLAYER_BATTLE), 4)
                self.assertEqual(end[PLAYER_BATTLE + 0x18 + 1], 6, 'Estágio de ataque não deve ser herdado como Baton Pass')
                if move_id == 571:
                    self.assertEqual(end[FOE_BATTLE + 0x18 + 1], 5)
                    self.assertEqual(end[FOE_BATTLE + 0x18 + 4], 5)
                else:
                    self.assertLess(u16(end, FOE_BATTLE + 0x2A), 450)

        # Parting Shot bloqueado por Clear Body (ability=29) NÃO deve forçar troca
        st_cb = self._duel_state(571, f_ability=29, base_state=self.two_party_battle_fixture)
        end_cb, _ = self._run_turn(st_cb, frames=780)
        self.assertEqual(u16(end_cb, offset(PARTY_INDEXES_ADDR)), 0)
        self.assertEqual(end_cb[FOE_BATTLE + 0x18 + 1], 6)

    def test_tm220_meteor_beam_e_geomancy_dois_turnos_completos(self):
        # Meteor Beam (817): turno 1 brilha + Sp. Atk +1 (sem dano); turno 2 automático causa dano Rock e limpa MULTIPLETURNS
        st_mb = self._duel_state(817, f_ability=4)
        t1, seen1 = self._run_turn(st_mb, frames=500)
        self.assertTrue(any('brilhando!' in s for s in seen1), seen1)
        self.assertEqual(t1[PLAYER_BATTLE + 0x18 + 4], 7)
        self.assertEqual(u16(t1, FOE_BATTLE + 0x2A), 450)
        self.assertTrue(u32(t1, PLAYER_BATTLE + 0x54) & 0x1000)

        self.f.restore(t1)
        self.f.run(850)
        t2 = self.f.state()
        self.assertLess(u16(t2, FOE_BATTLE + 0x2A), 450)
        self.assertEqual(u32(t2, PLAYER_BATTLE + 0x54) & 0x1000, 0)
        self.assertEqual(t2[PLAYER_BATTLE + 0x25], 19)

        # Geomancy (597): turno 1 brilha; turno 2 automático eleva SpA/SpD/Spe em +2 e limpa MULTIPLETURNS
        st_geo = self._duel_state(597)
        g1, seen_g1 = self._run_turn(st_geo, frames=420)
        self.assertTrue(any('brilhando!' in s for s in seen_g1), seen_g1)
        self.assertTrue(u32(g1, PLAYER_BATTLE + 0x54) & 0x1000)
        self.f.restore(g1)
        self.f.run(950)
        g2 = self.f.state()
        self.assertEqual(g2[PLAYER_BATTLE + 0x18 + 4], 8)
        self.assertEqual(g2[PLAYER_BATTLE + 0x18 + 5], 8)
        self.assertEqual(g2[PLAYER_BATTLE + 0x18 + 3], 8)
        self.assertEqual(u32(g2, PLAYER_BATTLE + 0x54) & 0x1000, 0)

    def test_burning_jealousy_alluring_voice_e_lash_out_historico_do_turno(self):
        # Burning Jealousy (813): queima apenas se o alvo subiu estágio no turno (Swords Dance=14 rápido)
        end_no_up, _ = self._run_turn(self._duel_state(813, foe_move=150, p_spd=80, f_spd=300, f_ability=4), frames=960)
        end_up, _ = self._run_turn(self._duel_state(813, foe_move=14, p_spd=80, f_spd=300, f_ability=4), frames=1080)
        self.assertEqual(u32(end_no_up, FOE_BATTLE + 0x50) & 0x10, 0)
        self.assertTrue(u32(end_up, FOE_BATTLE + 0x50) & 0x10)

        # Alluring Voice (819): confunde apenas se o alvo subiu estágio no turno
        end_av0, _ = self._run_turn(self._duel_state(819, foe_move=150, p_spd=80, f_spd=300, f_ability=4), frames=960)
        end_av1, _ = self._run_turn(self._duel_state(819, foe_move=14, p_spd=80, f_spd=300, f_ability=4), frames=1080)
        self.assertEqual(u32(end_av0, FOE_BATTLE + 0x54) & 0x07, 0)
        self.assertNotEqual(u32(end_av1, FOE_BATTLE + 0x54) & 0x07, 0)

        # Lash Out (814): dobra para 150 BP se estágio do usuário caiu neste turno (Tail Whip=39 do oponente rápido)
        end_lo_base, _ = self._run_turn(
            self._duel_state(814, foe_move=150, p_atk=220, p_spd=80, f_spd=300, f_ability=4),
            frames=960,
        )
        end_lo_drop, _ = self._run_turn(
            self._duel_state(814, foe_move=39, p_atk=220, p_spd=80, f_spd=300, f_ability=4),
            frames=1080,
        )
        self.assertEqual(end_lo_base[offset(V7_STATE_ADDR) + 1], 0)
        self.assertEqual(end_lo_drop[offset(V7_STATE_ADDR) + 1], 1)
        dmg_base = 450 - u16(end_lo_base, FOE_BATTLE + 0x2A)
        dmg_drop = 450 - u16(end_lo_drop, FOE_BATTLE + 0x2A)
        self.assertGreater(dmg_drop, int(dmg_base * 1.65), f'{dmg_base=} vs {dmg_drop=}')

    def test_temper_flare_e_stomping_tantrum_dobram_apos_falha_ou_flinch(self):
        for finisher in (815, 653):
            with self.subTest(finisher=finisher):
                # Battle Armor (f_ability=4) evita variação por crítico aleatório
                end_base, _ = self._run_turn(self._duel_state(finisher, f_ability=4), frames=780)
                dmg_base = 450 - u16(end_base, FOE_BATTLE + 0x2A)

                # Turno 1: Coaching (816) falha em batalha simples -> Turno 2: finisher dobra (150 BP)
                t1, _ = self._run_turn(self._duel_state(816, move2_id=finisher, f_ability=4), slot=0, frames=820)
                self.assertEqual(u16(t1, FOE_BATTLE + 0x2A), 450)
                t2, _ = self._run_turn(t1, slot=1, frames=820)
                dmg_after_fail = 450 - u16(t2, FOE_BATTLE + 0x2A)
                self.assertGreater(dmg_after_fail, int(dmg_base * 1.75), f'{dmg_base=} vs {dmg_after_fail=}')

                # Turno 3 consecutivo após acerto volta ao dano normal (75 BP)
                hp_before_t3 = u16(t2, FOE_BATTLE + 0x2A)
                t3, _ = self._run_turn(t2, slot=1, frames=820)
                dmg_t3 = hp_before_t3 - u16(t3, FOE_BATTLE + 0x2A)
                self.assertLess(dmg_t3, int(dmg_after_fail * 0.72), f'{dmg_t3=} vs {dmg_after_fail=}')

        # Cancelamento por Flinch (Fake Out=252 do oponente rápido no turno 1) também dobra Temper Flare no turno 2
        f1, _ = self._run_turn(self._duel_state(815, foe_move=252, p_spd=80, f_spd=300, f_ability=4), frames=820)
        self.assertEqual(u16(f1, FOE_BATTLE + 0x2A), 450)
        st_f2 = bytearray(f1)
        for mslot in range(4):
            put16(st_f2, FOE_BATTLE + 0x0C + 2 * mslot, 150)
        f2, _ = self._run_turn(bytes(st_f2), frames=820)
        dmg_flinch = 450 - u16(f2, FOE_BATTLE + 0x2A)
        dmg_norm = 450 - u16(self._run_turn(self._duel_state(815, f_ability=4), frames=780)[0], FOE_BATTLE + 0x2A)
        self.assertGreater(dmg_flinch, int(dmg_norm * 1.75))

    def test_tm229_upper_hand_prioridade_e_hesitacao(self):
        end_qa, _ = self._run_turn(self._duel_state(821, foe_move=98, p_spd=120, f_spd=350), frames=800)
        self.assertLess(u16(end_qa, FOE_BATTLE + 0x2A), 450)
        self.assertEqual(u16(end_qa, PLAYER_BATTLE + 0x2A), 120)

        end_tackle, _ = self._run_turn(self._duel_state(821, foe_move=33, p_spd=120, f_spd=350), frames=800)
        self.assertEqual(u16(end_tackle, FOE_BATTLE + 0x2A), 450)
        end_bde, _ = self._run_turn(self._duel_state(821, foe_move=577, p_spd=120, f_spd=350), frames=800)
        self.assertEqual(u16(end_bde, FOE_BATTLE + 0x2A), 450)

    def test_psychic_noise_heal_pulse_floral_healing_e_life_dew(self):
        # Psychic Noise (820) bloqueia Recover (105) neste turno e no próximo, expirando no 3º turno
        t1, _ = self._run_turn(
            self._duel_state(820, move2_id=150, foe_move=105, p_spd=300, f_spd=60, f_hp=300, f_max=450),
            slot=0,
            frames=860,
        )
        hp_after_pn = u16(t1, FOE_BATTLE + 0x2A)
        self.assertLess(hp_after_pn, 300)
        self.assertEqual(t1[offset(V7_STATE_ADDR) + 8 + 1], 2)

        t2, _ = self._run_turn(t1, slot=1, frames=860)
        self.assertEqual(u16(t2, FOE_BATTLE + 0x2A), hp_after_pn)
        self.assertEqual(t2[offset(V7_STATE_ADDR) + 8 + 1], 1)

        t3, _ = self._run_turn(t2, slot=1, frames=900)
        self.assertGreater(u16(t3, FOE_BATTLE + 0x2A), hp_after_pn)
        self.assertEqual(t3[offset(V7_STATE_ADDR) + 8 + 1], 0)

        # Psychic Noise impede absorção de HP de Mega Drain (72), mantendo apenas o dano no jogador
        md1, _ = self._run_turn(
            self._duel_state(820, foe_move=72, p_spd=300, f_spd=60, f_hp=250, f_max=450),
            frames=880,
        )
        self.assertLess(u16(md1, PLAYER_BATTLE + 0x2A), 120)
        self.assertLess(u16(md1, FOE_BATTLE + 0x2A), 250)

        # Heal Pulse (504) e Floral Healing (621) curam ceil(maxHP/2) do alvo e falham em HP cheio
        for heal_mid in (504, 621):
            with self.subTest(heal_mid=heal_mid):
                healed, _ = self._run_turn(self._duel_state(heal_mid, f_hp=100, f_max=401), frames=800)
                self.assertEqual(u16(healed, FOE_BATTLE + 0x2A), 301)
                full_fail, _ = self._run_turn(self._duel_state(heal_mid, f_hp=401, f_max=401), frames=780)
                self.assertEqual(u16(full_fail, FOE_BATTLE + 0x2A), 401)

    def test_duplas_coaching_dragon_cheer_life_dew_e_burning_jealousy_spread(self):
        st = bytearray(self.doubles_fixture)
        b0, b1, b2, b3 = (bank_off(i) for i in range(4))
        put16(st, b0 + 0x0C, 816)  # Coaching
        put16(st, b0 + 0x0E, 818)  # Dragon Cheer
        put16(st, b0 + 0x10, 696)  # Life Dew
        put16(st, b0 + 0x12, 813)  # Burning Jealousy (spread 0x08)
        for m in range(4):
            st[b0 + 0x25 + m] = 15
            put16(st, b2 + 0x0C + 2 * m, 150)
            st[b2 + 0x25 + m] = 20
            put16(st, b1 + 0x0C + 2 * m, 150)
            st[b1 + 0x25 + m] = 20
            put16(st, b3 + 0x0C + 2 * m, 150)
            st[b3 + 0x25 + m] = 20
        put16(st, b0 + 0x2A, 80)
        put16(st, b0 + 0x2E, 160)
        put16(st, b2 + 0x2A, 50)
        put16(st, b2 + 0x2E, 200)
        put16(st, b1 + 0x2A, 300)
        put16(st, b1 + 0x2E, 300)
        put16(st, b3 + 0x2A, 300)
        put16(st, b3 + 0x2E, 300)
        st[b2 + 0x22], st[b2 + 0x23] = 16, 16  # aliado Dragão (+2 crítico em Dragon Cheer)
        for bx in (b0, b1, b2, b3):
            for s_idx in range(1, 8):
                st[bx + 0x18 + s_idx] = 6
            st[bx + 0x50:bx + 0x58] = b'\x00' * 8
        st[b0 + 0x18 + 6] = 12
        put16(st, b0 + 0x06, 300)
        put16(st, b2 + 0x06, 250)
        put16(st, b1 + 0x06, 40)
        put16(st, b3 + 0x06, 30)
        st[offset(V7_STATE_ADDR):offset(V7_STATE_ADDR) + 96] = b'\x00' * 96

        # 1) Coaching: sobe Atk e Def do aliado bank 2 para 7
        self.f.restore(bytes(st))
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.run(950)
        after_coach = self.f.state()
        self.assertEqual(after_coach[b2 + 0x18 + 1], 7)
        self.assertEqual(after_coach[b2 + 0x18 + 2], 7)

        # 2) Dragon Cheer em aliado Dragão vs não-Dragão
        self.f.restore(bytes(st))
        self.f.pulse('A', 25)
        self.f.pulse('RIGHT', 15)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.run(900)
        after_dc_dragon = self.f.state()
        self.assertTrue(u32(after_dc_dragon, b2 + 0x54) & 0x00100000)
        self.assertEqual(u32(after_dc_dragon, offset(V7_STATE_ADDR) + 76 + 4 * 2), 0)

        st_nondrag = bytearray(st)
        st_nondrag[b2 + 0x22], st_nondrag[b2 + 0x23] = 10, 10
        self.f.restore(bytes(st_nondrag))
        self.f.pulse('A', 25)
        self.f.pulse('RIGHT', 15)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.run(900)
        after_dc_fire = self.f.state()
        self.assertTrue(u32(after_dc_fire, b2 + 0x54) & 0x00100000)
        self.assertNotEqual(u32(after_dc_fire, offset(V7_STATE_ADDR) + 76 + 4 * 2), 0)

        # 3) Life Dew: cura 25% de bank 0 (80 -> 120) e 25% de bank 2 (50 -> 100)
        self.f.restore(bytes(st))
        self.f.pulse('A', 25)
        self.f.pulse('DOWN', 15)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.run(980)
        after_ld = self.f.state()
        self.assertEqual(u16(after_ld, b0 + 0x2A), 120)
        self.assertEqual(u16(after_ld, b2 + 0x2A), 100)

        # 4) Burning Jealousy em duplas (alvo 0x08): b1 usa Swords Dance (queima!) e b3 usa Splash (só sofre dano!)
        st_bj = bytearray(st)
        put16(st_bj, b1 + 0x06, 400)  # b1 age antes de b0
        for m in range(4):
            put16(st_bj, b1 + 0x0C + 2 * m, 14)  # Swords Dance
        self.f.restore(bytes(st_bj))
        self.f.pulse('A', 25)
        self.f.pulse('DOWN', 15)
        self.f.pulse('RIGHT', 15)
        self.f.pulse('A', 25)  # slot 3 = Burning Jealousy (alvo 0x08 não pede cursor de alvo)
        self.f.pulse('A', 25)
        self.f.pulse('A', 25)
        self.f.run(1150)
        after_bj = self.f.state()
        self.assertLess(u16(after_bj, b1 + 0x2A), 300)
        self.assertLess(u16(after_bj, b3 + 0x2A), 300)
        self.assertTrue(u32(after_bj, b1 + 0x50) & 0x10)
        self.assertEqual(u32(after_bj, b3 + 0x50) & 0x10, 0)

    def test_estojo_v2_ensino_3_paginas_consumo_unico_hm_infinito_e_persistencia_save(self):
        # Mew (151) compatível com todas as TMs ativadas em motor_v7 via CanPokemonLearnTMHM (0x080F8460)
        new_tms_v7 = (
            (422, 517), (434, 369), (449, 113), (569, 813),
            (570, 708), (573, 814), (581, 815), (587, 816),
            (594, 817), (600, 818), (601, 819), (602, 820), (603, 821),
        )
        for item_id, move_id in new_tms_v7:
            with self.subTest(item_id=item_id, move_id=move_id):
                st = seed_mon(self.fixture, 151, 5, (33, 45, 0, 0))
                out = invoke(self.f, st, 0x080F8460, {0: PARTY, 1: item_id, 2: 0})
                self.assertEqual(u32(out, 0x20), 0)

        # Fluxo real nas 3 páginas do estojo_v2: Pág. 0 HM01 infinito, Pág. 1 TM060 U-turn, Pág. 2 TM229 Upper Hand
        state = seed_mon(self.fixture, 151, 20, (33, 0, 0, 0))
        state = add(self.f, state, 339, 1)  # HM01 Cut (infinita, página 0: 1 -> 1)
        state = add(self.f, state, 434, 2)  # TM060 U-turn (página 1: 2 -> 1)
        state = add(self.f, state, 603, 1)  # TM229 Upper Hand (página 2: 1 -> 0)

        self.f.restore(bytes(state))
        open_case(self.f)
        for target_page, item_id, move_id, want_qty in (
            (0, 339, 15, 1),
            (1, 434, 369, 1),
            (2, 603, 821, 0),
        ):
            for _ in range(10):
                if page(self.f.state()) == target_page:
                    break
                self.f.pulse('A', 70)
                self.f.pulse('R', 90)
            self.assertEqual(page(self.f.state()), target_page)
            for _ in range(20):
                self.f.pulse('A', 90)
                if move_id in get_moves(self.f.state()):
                    break
            self.assertIn(move_id, get_moves(self.f.state()))
            for _ in range(8):
                self.f.pulse('A', 100)
                if item_id >= 375 and stored_quantity(self.f.state(), item_id) == want_qty:
                    break
            self.assertEqual(stored_quantity(self.f.state(), item_id), want_qty)

        after_tm = self.f.state()
        self.assertEqual(get_moves(after_tm), (33, 15, 369, 821))
        self.assertEqual(stored_quantity(after_tm, 339), 1)
        self.assertEqual(stored_quantity(after_tm, 434), 1)
        self.assertEqual(stored_quantity(after_tm, 603), 0)
        self.assertTrue(mon_facts(mon(after_tm))['valid'])

        flash = save_after_case(self.f)
        core_copy = self.dir / 'core_reload_v7.so'
        if not core_copy.exists():
            shutil.copyfile(self.core, core_copy)
        reloaded = Emulator(self.rom, core_copy, self.dir)
        try:
            loaded_state = load_game(reloaded, flash)
            self.assertEqual(get_moves(loaded_state), (33, 15, 369, 821))
            self.assertEqual(get(reloaded, loaded_state, 339), 1)
            self.assertEqual(get(reloaded, loaded_state, 434), 1)
            self.assertEqual(get(reloaded, loaded_state, 603), 0)
            self.assertTrue(mon_facts(mon(loaded_state))['valid'])
        finally:
            reloaded.close()

    def test_learnsets_nivel_e_relembrador_novos_golpes_motor_v7(self):
        out_buf = 0x02001200
        cases = (
            (79, 45, 504),   # Slowpoke -> Heal Pulse
            (674, 40, 571),  # Pancham -> Parting Shot
            (716, 55, 597),  # Xerneas -> Geomancy
            (764, 30, 621),  # Comfey -> Floral Healing
            (35, 16, 696),   # Clefairy -> Life Dew
        )
        for species, level, want in cases:
            with self.subTest(species=species, level=level, want=want):
                st = seed_mon(self.fixture, species, level, (33, 45, 0, 0))
                res = invoke(self.f, st, 0x08109790, {0: PARTY, 1: 1})
                self.assertIn(want, get_moves(res))
                self.assertTrue(mon_facts(mon(res))['valid'])

                st_relearn = bytearray(seed_mon(self.fixture, species, 100, (33, 45, 10, 22)))
                st_relearn[offset(out_buf):offset(out_buf) + 64] = b'\x00' * 64
                got = invoke(self.f, st_relearn, 0x0810E808, {0: PARTY, 1: out_buf})
                count = u32(got, 0x20)
                relearn_moves = struct.unpack_from(f'<{count}H', got, offset(out_buf))
                self.assertIn(want, relearn_moves)

    def test_regressao_cadeia_v5_v6_hard_press_fling_steel_beam_poltergeist_triple_axel(self):
        # Hard Press (807, v5): proporcional ao HP do alvo (450/450 -> 100 BP)
        hp_res, _ = self._run_turn(self._duel_state(807, f_hp=450, f_max=450, f_ability=4), frames=820)
        self.assertLess(u16(hp_res, FOE_BATTLE + 0x2A), 450)

        # Fling (374, v6): Poison Barb (211) causa dano + envenena e consome item segurado (+0x30)
        st_fling = bytearray(self._duel_state(374, f_ability=4))
        put16(st_fling, PLAYER_BATTLE + 0x30, 211)
        fl_res, _ = self._run_turn(bytes(st_fling), frames=960)
        self.assertLess(u16(fl_res, FOE_BATTLE + 0x2A), 450)
        self.assertEqual(u16(fl_res, PLAYER_BATTLE + 0x30), 0)
        self.assertTrue(u32(fl_res, FOE_BATTLE + 0x50) & 0x08)

        # Steel Beam (808, v6): perde ceil(maxHP/2) mesmo contra alvo imune? Steel não tem imune, mas perde 61 de 121 HP
        sb_res, _ = self._run_turn(self._duel_state(808, p_hp=121, p_max=121, f_ability=4), frames=920)
        self.assertLess(u16(sb_res, FOE_BATTLE + 0x2A), 450)
        self.assertEqual(u16(sb_res, PLAYER_BATTLE + 0x2A), 60)

        # Poltergeist (809, v6): falha sem item no alvo; acerta com Potion (13)
        pg_fail, _ = self._run_turn(self._duel_state(809, f_types=(11, 11), f_ability=4), frames=800)
        self.assertEqual(u16(pg_fail, FOE_BATTLE + 0x2A), 450)
        st_pg = bytearray(self._duel_state(809, f_types=(11, 11), f_ability=4))
        put16(st_pg, FOE_BATTLE + 0x30, 13)
        pg_hit, _ = self._run_turn(bytes(st_pg), frames=860)
        self.assertLess(u16(pg_hit, FOE_BATTLE + 0x2A), 450)

        # Triple Axel (812, v6): 3 golpes escalonados 20 -> 40 -> 60 BP via hook_damage_v7 -> hook_damage_v6
        self.f.restore(self._duel_state(812, f_ability=4))
        self.f.pulse('A', 25)
        self.f.run(6, 'A')
        seen_powers: set[int] = set()
        for _ in range(1900):
            self.f.run(1)
            pwr = u16(self.f.state(), offset(0x02021792))
            if pwr:
                seen_powers.add(pwr)
        self.assertEqual(seen_powers, {20, 40, 60})


if __name__ == '__main__':
    unittest.main()
