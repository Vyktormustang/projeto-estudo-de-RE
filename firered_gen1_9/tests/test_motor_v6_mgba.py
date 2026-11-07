"""Testes de integração em mGBA 0.10.5 do motor parcial v6 (apenas saves/estados sintéticos).

MOTOR_V6_ROM=/tmp/firered_gen1_9_work/roms/motor_v6.gba \
MOTOR_V6_BASE=/tmp/firered_gen1_9_work/roms/motor_v5.gba \
MGBA_CORE=/tmp/mgba-build/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v6*.py' -v
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

from mgba_treino_harness import Emulator, PARTY, mon, offset, put16, u16, u32, decrypted
from test_atualizacoes_gen9_mgba import FOE_BATTLE, PLAYER_BATTLE
from test_estojo_expandido_mgba import add, get, open_case, page, save_after_case
from test_eventos_fixos_mgba import enemy, route_entry_fixture, route_from_entry
from test_golpes_gen9_integracao import load_game, set_exp_and_test_stats
from test_golpes_gen9_mgba import invoke, moves as get_moves, seed_mon
from test_motor_ampliado_mgba import stored_quantity
from scripts import motor_v6 as patch

ROM_ENV = os.environ.get('MOTOR_V6_ROM')
BASE_ENV = os.environ.get('MOTOR_V6_BASE')
CORE_ENV = os.environ.get('MGBA_CORE')

DISP_STR = 0x020201B4
BUFF3 = 0x02020300

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


@unittest.skipUnless(ROM_ENV and BASE_ENV and CORE_ENV, 'defina MOTOR_V6_ROM, MOTOR_V6_BASE e MGBA_CORE')
class MotorV6MGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM_ENV).resolve()
        cls.base = Path(BASE_ENV).resolve()
        cls.core = Path(CORE_ENV).resolve()
        if cls.rom.read_bytes() != patch.build(cls.base.read_bytes()):
            raise ValueError('ROM motor_v6 diverge da reconstrução determinística')
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        cls.f = Emulator(cls.rom, cls.core, cls.dir)
        cls.fixture = route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_battle_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    @classmethod
    def _make_battle_fixture(cls) -> bytes:
        state = seed_mon(cls.fixture, 1, 10, (807, 566, 808, 809))
        set_exp_and_test_stats(state, 1, 10)
        cls.f.restore(bytes(state))
        route_from_entry(cls.f)
        for _ in range(120):
            cls.f.run(20, 'LEFT')
            cls.f.run(20, 'RIGHT')
            wild = enemy(cls.f.state())
            if wild['valid'] and wild['species'] != 390:
                cls.f.run(350)
                break
        else:
            raise AssertionError('Sem encontro selvagem para fixture de batalha')
        for _ in range(6):
            cls.f.pulse('B', 45)
        return bytes(cls.f.state())

    def setUp(self):
        self.f.restore(self.fixture)

    def _duel_state(
        self,
        move_id: int,
        *,
        p_hp: int = 101,
        p_max: int = 101,
        p_item: int = 0,
        f_types: tuple[int, int] = (0, 0),
        f_hp: int = 400,
        f_max: int = 400,
        f_item: int = 0,
        acc_stage: int = 12,
        eva_stage: int = 6,
    ) -> bytes:
        st = bytearray(self.battle_fixture)
        put16(st, PLAYER_BATTLE + 0x0C, move_id)
        st[PLAYER_BATTLE + 0x25] = 20
        put16(st, PLAYER_BATTLE + 0x2A, p_hp)
        put16(st, PLAYER_BATTLE + 0x2E, p_max)
        put16(st, PLAYER_BATTLE + 0x30, p_item)
        for i in range(1, 8):
            st[PLAYER_BATTLE + 0x18 + i] = 6
            st[FOE_BATTLE + 0x18 + i] = 6
        st[PLAYER_BATTLE + 0x1E] = acc_stage
        st[FOE_BATTLE + 0x1F] = eva_stage
        put16(st, PLAYER_BATTLE + 0x06, 300)
        put16(st, PLAYER_BATTLE + 0x02, 120)
        put16(st, PLAYER_BATTLE + 0x08, 120)
        st[PLAYER_BATTLE + 0x2C] = 10
        st[PLAYER_BATTLE + 0x50:PLAYER_BATTLE + 0x58] = b'\x00' * 8
        for mslot in range(4):
            put16(st, FOE_BATTLE + 0x0C + 2 * mslot, 150)  # Splash
            st[FOE_BATTLE + 0x25 + mslot] = 40
        put16(st, FOE_BATTLE + 0x04, 150)
        put16(st, FOE_BATTLE + 0x0A, 150)
        put16(st, FOE_BATTLE + 0x06, 20)
        put16(st, FOE_BATTLE + 0x2A, f_hp)
        put16(st, FOE_BATTLE + 0x2E, f_max)
        put16(st, FOE_BATTLE + 0x30, f_item)
        st[FOE_BATTLE + 0x50:FOE_BATTLE + 0x58] = b'\x00' * 8
        st[FOE_BATTLE + 0x22], st[FOE_BATTLE + 0x23] = f_types
        st[offset(BUFF3)] = 0xAA
        return bytes(st)

    def _run_turn(self, state: bytes, frames: int = 520) -> tuple[bytes, list[str]]:
        self.f.restore(state)
        seen: list[str] = []
        self.f.pulse('A', 25)
        self.f.run(6, 'A')
        for _ in range(frames):
            self.f.run(1)
            cur = self.f.state()
            txt = decode_gba_str(cur[offset(DISP_STR):offset(DISP_STR) + 80])
            if txt and (not seen or seen[-1] != txt):
                seen.append(txt)
        return self.f.state(), seen

    def test_nomes_de_golpes_797_a_812_e_sentinela_ewram_sem_overflow(self):
        for move_id, label in (
            (797, 'TRAILBLAZE!'),
            (807, 'HARD PRESS!'),
            (808, 'STEEL BEAM!'),
            (809, 'POLTERGEIST!'),
            (811, 'SUPERCELL SLAM!'),
            (812, 'TRIPLE AXEL!'),
        ):
            with self.subTest(move_id=move_id):
                end, seen = self._run_turn(self._duel_state(move_id, f_item=13), frames=440)
                self.assertTrue(any(label in s for s in seen), f'{move_id}: {seen}')
                self.assertEqual(end[offset(BUFF3)], 0xAA)

        # Golpe de 16 caracteres (566 = PARABOLIC CHARGE) não invade gBattleTextBuff3
        end566, seen566 = self._run_turn(self._duel_state(566), frames=440)
        self.assertTrue(any('PARABOLIC CHAR!' in s for s in seen566))
        self.assertEqual(end566[offset(BUFF3)], 0xAA)

    def test_icones_de_itens_375_a_604_carregam_sprites_validos(self):
        for tag_idx, item_id in enumerate((289, 375, 417, 544, 598, 599, 603, 604, 605), start=0x1300):
            with self.subTest(item_id=item_id):
                out = invoke(self.f, self.fixture, 0x080CB17C, {0: tag_idx, 1: tag_idx, 2: item_id})
                sprite_id = u32(out, 0x20) & 0xFF
                self.assertLess(sprite_id, 64, f'AddItemIconSprite falhou para item {item_id}')

    def test_tm043_fling_potencia_efeitos_consumo_e_bloqueios(self):
        for blocked_item in (0, 1, 357, 417):
            with self.subTest(blocked_item=blocked_item):
                end, _ = self._run_turn(self._duel_state(374, p_item=blocked_item), frames=420)
                self.assertEqual(u16(end, FOE_BATTLE + 0x2A), 400)
                self.assertEqual(u16(end, PLAYER_BATTLE + 0x30), blocked_item)

        # Poison Barb (211): 70 BP + envenenamento + consumo em BattlePokemon e Party
        st_pb = bytearray(self._duel_state(374, p_item=211))
        # Grava item também na estrutura criptografada da equipe para validar sincronização
        party_mon = mon(st_pb)
        blk, order, _ = decrypted(party_mon)
        put16(blk, order[0] * 12 + 2, 211)
        put16(party_mon, 28, sum(struct.unpack('<24H', blk)) & 0xFFFF)
        key = u32(party_mon, 0) ^ u32(party_mon, 4)
        for w in range(12):
            struct.pack_into('<I', party_mon, 32 + w * 4, u32(blk, w * 4) ^ key)
        st_pb[offset(PARTY):offset(PARTY) + 100] = party_mon

        end_pb, _ = self._run_turn(bytes(st_pb), frames=520)
        end_lb, _ = self._run_turn(self._duel_state(374, p_item=202), frames=520)
        dmg_pb = 400 - u16(end_pb, FOE_BATTLE + 0x2A)
        dmg_lb = 400 - u16(end_lb, FOE_BATTLE + 0x2A)
        self.assertGreater(dmg_pb, dmg_lb)
        self.assertGreater(dmg_lb, 0)
        self.assertTrue(u32(end_pb, FOE_BATTLE + 0x50) & 0x08)  # PSN
        self.assertTrue(u32(end_lb, FOE_BATTLE + 0x50) & 0x40)  # PAR
        self.assertEqual(u16(end_pb, PLAYER_BATTLE + 0x30), 0)
        blk_after, order_after, valid_after = decrypted(mon(end_pb))
        self.assertTrue(valid_after)
        self.assertEqual(u16(blk_after, order_after[0] * 12 + 2), 0)

    def test_tm170_steel_beam_custo_ceil_metade_em_acerto_erro_e_autonocaute(self):
        end_hit, _ = self._run_turn(self._duel_state(808, p_hp=101, p_max=101, acc_stage=12), frames=540)
        self.assertEqual(u16(end_hit, PLAYER_BATTLE + 0x2A), 50)
        self.assertLess(u16(end_hit, FOE_BATTLE + 0x2A), 400)

        end_miss, _ = self._run_turn(self._duel_state(808, p_hp=101, p_max=101, acc_stage=0, eva_stage=12), frames=560)
        self.assertEqual(u16(end_miss, PLAYER_BATTLE + 0x2A), 50)

        end_ko, _ = self._run_turn(self._duel_state(808, p_hp=40, p_max=101, acc_stage=12), frames=620)
        self.assertEqual(u16(end_ko, PLAYER_BATTLE + 0x2A), 0)

    def test_tm198_poltergeist_exige_item_no_alvo_sem_consumir(self):
        end_empty, _ = self._run_turn(self._duel_state(809, f_item=0, f_types=(14, 14)), frames=440)
        self.assertEqual(u16(end_empty, FOE_BATTLE + 0x2A), 400)

        end_item, _ = self._run_turn(self._duel_state(809, f_item=13, f_types=(14, 14)), frames=480)
        self.assertLess(u16(end_item, FOE_BATTLE + 0x2A), 400)
        self.assertEqual(u16(end_item, FOE_BATTLE + 0x30), 13)

    def test_tm201_misty_explosion_dano_fada_e_autonocaute(self):
        end_me, _ = self._run_turn(self._duel_state(810, p_hp=101, p_max=101, f_types=(16, 16)), frames=580)
        self.assertEqual(u16(end_me, PLAYER_BATTLE + 0x2A), 0)
        self.assertLess(u16(end_me, FOE_BATTLE + 0x2A), 400)
        self.assertEqual(end_me[offset(BUFF3)], 0xAA)

        # Contra Steel (17? Não: em FireRed Steel é tipo 8), dano deve ser menor que contra Dragon (16)
        end_steel, _ = self._run_turn(self._duel_state(810, p_hp=101, p_max=101, f_types=(8, 8)), frames=580)
        self.assertGreater(400 - u16(end_me, FOE_BATTLE + 0x2A), 400 - u16(end_steel, FOE_BATTLE + 0x2A))

    def test_tm210_supercell_slam_sem_recuo_no_acerto_e_crash_em_imunidade_ou_erro(self):
        end_hit, _ = self._run_turn(self._duel_state(811, p_hp=101, p_max=101, f_types=(0, 0)), frames=520)
        self.assertEqual(u16(end_hit, PLAYER_BATTLE + 0x2A), 101)
        self.assertLess(u16(end_hit, FOE_BATTLE + 0x2A), 400)

        end_ground, _ = self._run_turn(self._duel_state(811, p_hp=101, p_max=101, f_types=(4, 4)), frames=760)
        self.assertEqual(u16(end_ground, FOE_BATTLE + 0x2A), 400)
        self.assertEqual(u16(end_ground, PLAYER_BATTLE + 0x2A), 51)

        end_miss, _ = self._run_turn(self._duel_state(811, p_hp=101, p_max=101, acc_stage=0, eva_stage=12), frames=760)
        self.assertEqual(u16(end_miss, FOE_BATTLE + 0x2A), 400)
        self.assertEqual(u16(end_miss, PLAYER_BATTLE + 0x2A), 51)

    def test_tm212_triple_axel_escala_20_40_60(self):
        self.f.restore(self._duel_state(812, f_types=(12, 12), acc_stage=12, eva_stage=6))
        self.f.pulse('A', 25)
        self.f.run(6, 'A')
        seen_powers: set[int] = set()
        for _ in range(42):
            self.f.run(45)
            cur = self.f.state()
            pwr = cur[offset(0x0202181A)]
            if pwr:
                seen_powers.add(pwr)
        self.assertEqual(seen_powers, {20, 40, 60})
        self.assertLess(u16(self.f.state(), FOE_BATTLE + 0x2A), 400)

    def test_ensino_consumo_save_flash_e_learnset_de_nivel(self):
        # Mew (151) compatível com todas as 6 novas TMs; HM01 (339) continua infinito.
        for item_id, move_id in ((417, 374), (544, 808), (572, 809), (575, 810), (584, 811), (586, 812)):
            with self.subTest(item_id=item_id, move_id=move_id):
                st = seed_mon(self.fixture, 151, 5, (33, 45, 0, 0))
                out = invoke(self.f, st, 0x080F8460, {0: PARTY, 1: item_id, 2: 0})
                self.assertEqual(u32(out, 0x20), 0)

        # Fluxo real nas 3 páginas do estojo (pág. 0 HM01 infinito, pág. 1 TM043, pág. 2 TM170) + Flash save/reload
        st = seed_mon(self.fixture, 151, 5, (33, 0, 0, 0))
        st = add(self.f, st, 339, 1)  # Pág. 0: HM01 Cut (golpe 15, infinito)
        st = add(self.f, st, 417, 2)  # Pág. 1: TM043 Fling (golpe 374, uso único)
        st = add(self.f, st, 544, 2)  # Pág. 2: TM170 Steel Beam (golpe 808, uso único)
        self.f.restore(bytes(st))

        open_case(self.f)
        for target_page, item_id, move_id, want_qty in (
            (0, 339, 15, 1),
            (1, 417, 374, 1),
            (2, 544, 808, 1),
        ):
            for _ in range(10):
                if page(self.f.state()) == target_page:
                    break
                self.f.pulse('A', 70)
                self.f.pulse('R', 90)
            self.assertEqual(page(self.f.state()), target_page)
            for _ in range(18):
                self.f.pulse('A', 90)
                if move_id in get_moves(self.f.state()):
                    break
            self.assertIn(move_id, get_moves(self.f.state()))
            for _ in range(8):
                self.f.pulse('A', 100)
                if item_id >= 375 and stored_quantity(self.f.state(), item_id) == want_qty:
                    break
            self.assertEqual(stored_quantity(self.f.state(), item_id), want_qty)

        after = self.f.state()
        self.assertEqual(get_moves(after), (33, 15, 374, 808))
        self.assertEqual(stored_quantity(after, 339), 1)
        self.assertEqual(stored_quantity(after, 417), 1)
        self.assertEqual(stored_quantity(after, 544), 1)
        flash = save_after_case(self.f)

        reload_core = self.dir / 'reload_v6.so'
        if not reload_core.exists():
            shutil.copyfile(self.core, reload_core)
        loaded = Emulator(self.rom, reload_core, self.dir)
        try:
            reloaded = load_game(loaded, flash)
            self.assertEqual(get_moves(reloaded), (33, 15, 374, 808))
            self.assertEqual(get(loaded, reloaded, 339), 1)
            self.assertEqual(get(loaded, reloaded, 417), 1)
            self.assertEqual(get(loaded, reloaded, 544), 1)
        finally:
            loaded.close()

        # Learnset de nível: Cubone (104) aprende Fling (374) no nível 20
        cub = seed_mon(self.fixture, 104, 20, (33, 45, 0, 0))
        cub_out = invoke(self.f, cub, 0x08109790, {0: PARTY, 1: 1})
        self.assertEqual(get_moves(cub_out), (33, 45, 374, 0))


if __name__ == '__main__':
    unittest.main()
