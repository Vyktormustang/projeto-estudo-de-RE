"""Fluxos opcionais em mGBA 0.10.5 com ROM própria e saves descartáveis.

ATUALIZACOES_TEST_ROM=/caminho/nova.gba MGBA_CORE=/caminho/mgba_libretro.so \
  python3 -m unittest discover -s tests -p 'test_atualizacoes_gen9_mgba.py' -v
Nenhum save pessoal ou savestate do usuário é aberto ou alterado.
"""
from __future__ import annotations

import ctypes as C
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path

from mgba_treino_harness import Emulator, PARTY, mon, mon_facts, offset, u32
from test_eventos_fixos_mgba import route_entry_fixture, route_from_entry, enemy
from test_golpes_gen9_mgba import invoke, moves, seed_mon
from test_golpes_gen9_integracao import load_game, save_game, set_exp_and_test_stats
from scripts import atualizacoes_gen9 as patch

ROM = os.environ.get('ATUALIZACOES_TEST_ROM')
CORE = os.environ.get('MGBA_CORE')
BASE = Path(os.environ.get('ATUALIZACOES_TEST_BASE',
            Path(__file__).resolve().parents[1] / 'rom_mod/ptbr_gen1-9_selvagens_treino_golpes_nivel.gba'))
POCKETS = 0x0202B79C
PLAYER_BATTLE = offset(0x02021410)
FOE_BATTLE = offset(0x0202146C)


def pocket(state, index=3):
    address = u32(state, offset(POCKETS + index * 8))
    capacity = state[offset(POCKETS + index * 8 + 4)]
    if not 0x02000000 <= address < 0x02040000:
        raise AssertionError(f'Ponteiro de bolso inválido: {address:08x}')
    return address, capacity


def pocket_ids(state, index=3):
    address, capacity = pocket(state, index)
    return [struct.unpack_from('<H', state, offset(address + i * 4))[0] for i in range(capacity)]


def copy_ewram(original, result):
    new = bytearray(original)
    new[0x21000:0x61000] = result[0x21000:0x61000]
    return bytes(new)


def inject_item(f, fixture, item):
    result = invoke(f, fixture, 0x080C69A4, {0: item, 1: 1})
    if u32(result, 0x20) != 1:
        raise AssertionError(f'Não foi possível inserir item sintético {item}')
    return copy_ewram(fixture, result)


def open_single_tm_and_teach(f):
    # Partindo da entrada norte de Pallet com TM Case já existente.
    f.pulse('START', 80)
    f.pulse('DOWN', 35)  # Bolsa
    f.pulse('A', 110)
    f.pulse('RIGHT', 70)  # Itens-chave
    for _ in range(12):
        f.pulse('A', 90)


@unittest.skipUnless(ROM and CORE and BASE.exists(), 'defina ATUALIZACOES_TEST_ROM, ATUALIZACOES_TEST_BASE e MGBA_CORE')
class AtualizacoesMGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.core = Path(ROM).resolve(), Path(CORE).resolve()
        if patch.OUTPUT_SHA256 and patch.digest(cls.path.read_bytes()) != patch.OUTPUT_SHA256:
            raise ValueError('ROM de teste não corresponde à versão final')
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        cls.f = Emulator(cls.path, cls.core, cls.dir)
        cls.fixture = route_entry_fixture(cls.f)

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    def setUp(self):
        self.f.restore(self.fixture)

    def extra_core(self, suffix):
        path = self.dir / f'core_{suffix}.so'
        if not path.exists():
            shutil.copyfile(self.core, path)
        return path

    def test_compatibilidade_ovos_repetidos_tm_alta_e_legadas(self):
        for species, known, item, egg, expected in (
            (1, 0, 375, False, 0),     # SV TM001: Bulbasaur pode
            (10, 0, 375, False, 1),    # Caterpie não pode
            (1, 36, 375, False, 2),    # já sabe Take Down
            (1, 0, 375, True, 3),      # ovo
            (1, 0, 598, False, 0),     # SV TM224: sem truncar item > 544
            (1, 0, 294, False, 0),     # TM06 antiga: Toxic
            (1, 0, 342, False, 0),     # HM04 antiga: Strength
            (10, 0, 294, False, 1),
        ):
            with self.subTest(species=species, item=item, egg=egg, known=known):
                state = seed_mon(self.fixture, species, 5, (known, 0, 0, 0), egg)
                result = invoke(self.f, state, 0x080F8460, {0: PARTY, 1: item, 2: 0})
                self.assertEqual(u32(result, 0x20), expected)

    def test_estojo_cheio_recusa_sem_apagar_items(self):
        state = inject_item(self.f, self.fixture, 375)  # cria automaticamente o estojo
        p, size = pocket(state)
        self.assertEqual(size, 58)
        data = bytearray(state)
        # O jogo guarda quantidade criptografada; o slot vazio contém a chave.
        empty_quantity = struct.unpack_from('<H', data, offset(p + 4 + 2))[0]
        for i in range(size):
            struct.pack_into('<HH', data, offset(p + 4 * i), 289 + i, empty_quantity ^ 1)
        before = bytes(data[offset(p):offset(p) + size * 4])
        result = invoke(self.f, data, 0x080C69A4, {0: 375, 1: 1})
        self.assertEqual(u32(result, 0x20), 0)
        self.assertEqual(result[offset(p):offset(p) + size * 4], before)
        self.assertEqual([struct.unpack_from('<H', before, i * 4)[0] for i in range(size)], list(range(289, 347)))

    def test_reaprendizados_reintroduzidos_preservam_ids_16bits(self):
        for species, lv, expected in ((128, 5, 522), (215, 36, 467), (179, 36, 534)):
            with self.subTest(species=species, level=lv):
                state = seed_mon(self.fixture, species, lv, (33, 45, 0, 0))
                result = invoke(self.f, state, 0x08109790, {0: PARTY, 1: 1})
                self.assertEqual(u32(result, 0x20), expected)
                self.assertIn(expected, moves(result))

    def test_tela_itens_ensina_tm_antiga_hm_e_tm_alta(self):
        for item, learned, reusable in ((294, 92, False), (342, 70, True), (598, 174, True)):
            with self.subTest(item=item):
                state = inject_item(self.f, self.fixture, item)
                self.f.restore(state)
                open_single_tm_and_teach(self.f)
                result = self.f.state()
                self.assertEqual(moves(result), (33, 45, 22, learned))
                self.assertEqual(item in pocket_ids(result), reusable)
                self.assertTrue(mon_facts(mon(result))['valid'])

    def test_migracao_save_antigo_sintetico(self):
        # São dois cores separados porque uma mesma .so compartilha estado global.
        old = Emulator(BASE, self.extra_core('antigo'), self.dir)
        try:
            before_state = route_entry_fixture(old)
            before = mon(before_state)
            flash = save_game(old)
        finally:
            old.close()
        new = Emulator(self.path, self.extra_core('migracao'), self.dir)
        try:
            loaded = load_game(new, flash)
            self.assertEqual(mon(loaded), before)
            self.assertEqual(moves(loaded), (33, 45, 22, 0))
            self.assertTrue(mon_facts(mon(loaded))['valid'])
        finally:
            new.close()

    def test_loja_compra_ensina_reutiliza_e_salva(self):
        # Teleporte de teste na placa da Rota 1, em cópia efêmera. A placa
        # da casa, loja, mochila, compra e menus são os da ROM de produção.
        data = bytearray(self.path.read_bytes())
        self.assertEqual(data[0xF90000:0xF9000A], b'\xff' * 10)
        self.assertEqual(struct.unpack_from('<I', data, 0x7C20D8)[0], 0x08190947)
        struct.pack_into('<I', data, 0x7C20D8, 0x08F90000)
        data[0xF90000:0xF9000A] = struct.pack('<BBBBHHBB', 0x39, 3, 0, 0xFF, 4, 8, 0x27, 0x02)
        instrumented = self.dir / 'instrumentada.gba'
        instrumented.write_bytes(data)
        f = Emulator(instrumented, self.extra_core('loja'), self.dir)
        try:
            f.restore(self.fixture)
            route_from_entry(f)
            f.run(64, 'LEFT'); f.run(30); f.run(5, 'UP'); f.run(25)
            f.pulse('A', 150); f.run(150)  # warp de teste
            f.run(4, 'UP'); f.run(20); f.pulse('A', 100)  # placa real
            for _ in range(20):
                f.pulse('A', 60)
                if struct.pack('<I', 0x08E18300) in f.state()[0x21000:0x61000]:
                    break
            else:
                self.fail('Loja de TMs não abriu')
            for _ in range(7): f.pulse('A', 90)
            self.assertIn(375, pocket_ids(f.state()))
            for _ in range(5): f.pulse('B', 90)
            open_single_tm_and_teach(f)
            self.assertEqual(moves(f.state()), (33, 45, 22, 36))
            self.assertIn(375, pocket_ids(f.state()))  # reutilizável
            for _ in range(6): f.pulse('B', 80)
            f.pulse('START', 80)
            for _ in range(3): f.pulse('DOWN', 35)  # cursor lembrava Bolsa
            for _ in range(15): f.pulse('A', 100)
            ptr = f.core.core.retro_get_memory_data(0)
            size = f.core.core.retro_get_memory_size(0)
            self.assertEqual(size, 131072)
            flash = C.string_at(ptr, size)
            self.assertGreater(len(set(flash)), 2)
        finally:
            f.close()
        new = Emulator(self.path, self.extra_core('recarregar'), self.dir)
        try:
            state = load_game(new, flash)
            self.assertEqual(moves(state), (33, 45, 22, 36))
            self.assertIn(375, pocket_ids(state))
            self.assertTrue(mon_facts(mon(state))['valid'])
        finally:
            new.close()

    def test_loja_chega_ao_ultimo_produto_tm224(self):
        data = bytearray(self.path.read_bytes())
        struct.pack_into('<I', data, 0x7C20D8, 0x08F90000)
        data[0xF90000:0xF9000A] = struct.pack('<BBBBHHBB', 0x39, 3, 0, 0xFF, 4, 8, 0x27, 0x02)
        instrumented = self.dir / 'loja_ultima.gba'
        instrumented.write_bytes(data)
        f = Emulator(instrumented, self.extra_core('loja_ultima'), self.dir)
        try:
            f.restore(self.fixture)
            route_from_entry(f)
            f.run(64, 'LEFT'); f.run(30); f.run(5, 'UP'); f.run(25)
            f.pulse('A', 150); f.run(150)
            f.run(4, 'UP'); f.run(20); f.pulse('A', 100)
            for _ in range(20):
                f.pulse('A', 60)
                if struct.pack('<I', 0x08E18300) in f.state()[0x21000:0x61000]: break
            else: self.fail('Loja de TMs não abriu')
            f.pulse('A', 120)  # lista dos 189 produtos
            f.run(3000, 'DOWN'); f.run(40)  # chega em Sair
            f.pulse('UP', 100)  # último produto, TM9-224
            for _ in range(8): f.pulse('A', 90)
            self.assertIn(598, pocket_ids(f.state()))
            self.assertNotIn(375, pocket_ids(f.state()))
        finally:
            f.close()

    def battle(self, f, move):
        state = seed_mon(self.fixture, 917, 5, (move, 0, 0, 0))
        set_exp_and_test_stats(state, 179, 12)
        f.restore(bytes(state))
        route_from_entry(f)
        for _ in range(120):
            f.run(20, 'LEFT'); f.run(20, 'RIGHT')
            wild = enemy(f.state())
            if wild['valid'] and wild['species'] != 390:
                f.run(350)
                return
        self.fail('Não houve encontro selvagem no teste de batalha')

    def test_efeitos_de_estagios_em_batalha(self):
        cases = ((467, PLAYER_BATTLE, {1: 7, 6: 7}),
                 (522, PLAYER_BATTLE, {1: 7, 4: 7}),
                 (564, FOE_BATTLE, {1: 5, 4: 5}),
                 (661, FOE_BATTLE, {1: 5, 4: 5}),
                 (482, PLAYER_BATTLE, {3: 7, 4: 7, 5: 7}),
                 (488, PLAYER_BATTLE, {1: 7, 2: 7, 6: 7}),
                 (534, PLAYER_BATTLE, {2: 9}),
                 (507, PLAYER_BATTLE, {1: 7, 3: 8}),
                 (518, FOE_BATTLE, {4: 5}),
                 (490, FOE_BATTLE, {5: 4}),       # Acid Spray
                 (487, PLAYER_BATTLE, {3: 7}),    # Flame Charge
                 (489, FOE_BATTLE, {3: 5}),       # Low Sweep
                 (551, FOE_BATTLE, {4: 5}),       # Snarl
                 (634, FOE_BATTLE, {1: 5}),       # Lunge
                 (523, FOE_BATTLE, {3: 5}),       # Electroweb
                 (707, FOE_BATTLE, {4: 5}),       # Skitter Smack
                 (689, FOE_BATTLE, {1: 5}),       # Breaking Swipe
                 (436, PLAYER_BATTLE, {4: 4}))    # Leaf Storm
        for move, battler, expected in cases:
            with self.subTest(move=move):
                self.battle(self.f, move)
                s = bytearray(self.f.state())
                struct.pack_into('<H', s, FOE_BATTLE + 0x2A, 500)
                struct.pack_into('<H', s, FOE_BATTLE + 0x2E, 500)
                self.f.restore(bytes(s))
                for _ in range(120):
                    self.f.pulse('A', 35)
                    stages = self.f.state()[battler + 0x18:battler + 0x20]
                    if all(stages[i] == value for i, value in expected.items()): break
                else: self.fail(f'Golpe {move} não aplicou estágios esperados: {list(stages)}')

    def test_limites_e_golpe_sem_precisao(self):
        cases = (
            # Ataque no máximo não impede aumento da precisão.
            (467, PLAYER_BATTLE, {1: 12, 6: 6}, PLAYER_BATTLE, {1: 12, 6: 7}),
            # O aumento de +3 satura em +6.
            (534, PLAYER_BATTLE, {2: 11}, PLAYER_BATTLE, {2: 12}),
            # Sp. Atk ainda pode cair quando Ataque já está no mínimo.
            (661, FOE_BATTLE, {1: 0, 4: 6}, FOE_BATTLE, {1: 0, 4: 5}),
        )
        for move, who, initial, target, expected in cases:
            with self.subTest(move=move, initial=initial):
                self.battle(self.f, move)
                s = bytearray(self.f.state())
                for i, stage in initial.items(): s[who + 0x18 + i] = stage
                self.f.restore(bytes(s))
                for _ in range(80):
                    self.f.pulse('A', 35)
                    stages = self.f.state()[target + 0x18:target + 0x20]
                    if all(stages[i] == stage for i, stage in expected.items()): break
                else: self.fail(f'Limites não respeitados: {move}, {list(stages)}')
        self.battle(self.f, 661)
        s = bytearray(self.f.state())
        s[PLAYER_BATTLE + 0x18 + 6] = 0   # menor precisão possível
        s[FOE_BATTLE + 0x18 + 7] = 12     # maior evasão possível
        self.f.restore(bytes(s))
        for _ in range(80):
            self.f.pulse('A', 35)
            stages = self.f.state()[FOE_BATTLE + 0x18:FOE_BATTLE + 0x20]
            if stages[1] == 5 and stages[4] == 5: break
        else: self.fail('Tearful Look deve ignorar precisão/evasão')

    def test_aura_sphere_ignora_precisao_e_leech_life_recupera(self):
        self.battle(self.f, 396)
        s = bytearray(self.f.state())
        s[PLAYER_BATTLE + 0x18 + 6] = 0
        s[FOE_BATTLE + 0x18 + 7] = 12
        struct.pack_into('<H', s, FOE_BATTLE + 0x2A, 500)  # HP atual
        struct.pack_into('<H', s, FOE_BATTLE + 0x2E, 500)
        self.f.restore(bytes(s))
        for _ in range(80):
            self.f.pulse('A', 35)
            if struct.unpack_from('<H', self.f.state(), FOE_BATTLE + 0x2A)[0] < 500: break
        else: self.fail('Aura Sphere deve ignorar precisão/evasão')

        self.battle(self.f, 141)
        s = bytearray(self.f.state())
        struct.pack_into('<H', s, PLAYER_BATTLE + 0x2A, 100)
        struct.pack_into('<H', s, FOE_BATTLE + 0x2A, 500)
        struct.pack_into('<H', s, FOE_BATTLE + 0x2E, 500)
        self.f.restore(bytes(s))
        for _ in range(100):
            self.f.pulse('A', 35)
            state = self.f.state()
            player_hp = struct.unpack_from('<H', state, PLAYER_BATTLE + 0x2A)[0]
            foe_hp = struct.unpack_from('<H', state, FOE_BATTLE + 0x2A)[0]
            if player_hp > 100: break
        else: self.fail('Leech Life não recuperou HP')
        self.assertEqual(player_hp - 100, max(1, (500 - foe_hp) // 2))

    def test_charge_beam_efeito_com_chance_forcada(self):
        data = bytearray(self.path.read_bytes())
        data[0x696F70 + 450 * 12 + 5] = 100  # cópia descartável
        path = self.dir / 'beam_chance_cem.gba'
        path.write_bytes(data)
        f = Emulator(path, self.extra_core('beam'), self.dir)
        try:
            self.battle(f, 450)
            for _ in range(80):
                f.pulse('A', 35)
                if f.state()[PLAYER_BATTLE + 0x18 + 4] == 7: break
            else: self.fail('Charge Beam não aumentou Sp. Atk')
        finally:
            f.close()

    def test_chance_zero_limites_serene_grace_e_garantida(self):
        # Rotina real de efeitos, RNG determinístico e chances de teste em
        # cópia efêmera. O resto da ROM e o comando de chance não são alterados.
        data = bytearray(self.path.read_bytes())
        self.assertEqual(data[0x12E9C4:0x12E9D0], bytes.fromhex('04 4b 1a 68 04 48 50 43 04 4a 94 46'))
        data[0x12E9C4:0x12E9D0] = bytes.fromhex('01 4b 18 88 70 47 00 46') + struct.pack('<I', 0x0203BFFC)
        for move, chance in ((400, 0), (401, 10), (402, 100)):
            data[0x696F70 + move * 12 + 5] = chance
        instrumented = self.dir / 'chance_deterministica.gba'
        instrumented.write_bytes(data)
        self.battle(self.f, 394)
        battle = self.f.state()
        f = Emulator(instrumented, self.extra_core('chance'), self.dir)
        try:
            cases = (
                (400, 0, 0, 3, 0, False),      # 0% com sorteio 0
                (401, 9, 0, 3, 0, True),       # 9 < 10
                (401, 10, 0, 3, 0, False),     # 10 não < 10
                (401, 19, 32, 3, 0, True),     # Serene Grace: 19 < 20
                (401, 20, 32, 3, 0, False),    # 20 não < 20
                (402, 99, 0, 3, 0, True),      # 100% com sorteio 99
                (400, 99, 0, 0x83, 0, True),   # efeito CERTAIN ignora chance
                (400, 99, 0, 0x83, 1, False),  # CERTAIN não ultrapassa miss
            )
            for move, rng, ability, effect, flags, expected in cases:
                with self.subTest(move=move, rng=rng, ability=ability, effect=effect, flags=flags):
                    s = bytearray(battle)
                    struct.pack_into('<H', s, offset(0x02021586), move)  # gCurrentMove
                    struct.pack_into('<H', s, PLAYER_BATTLE + 0x20, ability)
                    s[offset(0x020216C0) + 3] = effect  # gBattleCommunication
                    s[offset(0x02021608)] = flags
                    struct.pack_into('<I', s, PLAYER_BATTLE + 0x50, 0)
                    struct.pack_into('<H', s, offset(0x0203BFFC), rng)
                    result = invoke(f, bytes(s), 0x0805A8CC, {})
                    self.assertEqual(bool(result[PLAYER_BATTLE + 0x50] & 0x10), expected)
        finally:
            f.close()

    def test_efeitos_mistos_queimadura_recuo_e_flinch(self):
        # Chance/precisão 100 apenas na ROM efêmera; o script de dano/efeito é
        # o de produção. Assim testamos os dois ramos sem depender de sorte.
        data = bytearray(self.path.read_bytes())
        for move in (394, 424): data[0x696F70 + move * 12 + 5] = 100
        tmp = self.dir / 'chance_cem.gba'; tmp.write_bytes(data)
        f = Emulator(tmp, self.extra_core('efeitos'), self.dir)
        try:
            for move in (394, 424):
                with self.subTest(move=move):
                    self.battle(f, move)
                    for _ in range(5): f.pulse('A', 35)
                    state = bytearray(f.state())
                    struct.pack_into('<H', state, FOE_BATTLE + 0x2A, 500)
                    struct.pack_into('<H', state, FOE_BATTLE + 0x2E, 500)
                    f.restore(bytes(state))
                    flinched = False
                    for _ in range(2200):
                        f.run(1)
                        # Pressões espaçadas para atravessar as mensagens.
                        if _ % 35 == 0: f.pulse('A', 1)
                        s = f.state()
                        player_hp = struct.unpack_from('<H', s, PLAYER_BATTLE + 0x2A)[0]
                        foe_hp = struct.unpack_from('<H', s, FOE_BATTLE + 0x2A)[0]
                        burned = bool(s[FOE_BATTLE + 0x50] & 0x10)
                        flinched |= bool(s[FOE_BATTLE + 0x54] & 0x08)
                        if burned and foe_hp < 500 and ((move == 394 and player_hp < 170) or (move == 424 and flinched)):
                            break
                    else:
                        self.fail(f'Efeitos mistos não observados: {move}, burn={burned}, flinch={flinched}')
                    if move == 394:
                        self.assertEqual(170 - player_hp, max(1, (500 - foe_hp) // 3))
                    else:
                        self.assertTrue(flinched)
        finally:
            f.close()


if __name__ == '__main__':
    unittest.main()
