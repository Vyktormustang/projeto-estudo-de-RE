"""Testes estruturais e de integridade do motor parcial v7 (sem saves pessoais).

Sem ROM: valida catálogo (219 disponíveis / 10 pendentes), matrizes binárias,
learnsets (+59 entradas) e ISA ARM7TDMI Thumb-1 pura do payload.
Com MOTOR_V7_BASE=/caminho/motor_v6.gba: reconstrói em memória e confere SHA-256,
invariantes das tabelas/hooks v7 e preservação byte a byte dos subsistemas anteriores.
"""
from __future__ import annotations

import csv
import hashlib
import os
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import motor_v7 as patch

BASE_ENV = os.environ.get('MOTOR_V7_BASE')

NEW_TMS_V7 = {
    195: (569, 813, 'BURNING JEALOUSY'),
    199: (573, 814, 'LASH OUT'),
    207: (581, 815, 'TEMPER FLARE'),
    213: (587, 816, 'COACHING'),
    220: (594, 817, 'METEOR BEAM'),
    226: (600, 818, 'DRAGON CHEER'),
    227: (601, 819, 'ALLURING VOICE'),
    228: (602, 820, 'PSYCHIC NOISE'),
    229: (603, 821, 'UPPER HAND'),
}

DEFERRED_TMS_V7 = {52, 91, 113, 116, 136, 137, 138, 139, 161, 178}


class MotorV7DataTests(unittest.TestCase):
    def test_hashes_de_insumos_e_payload(self):
        inputs = patch.checked_inputs()
        self.assertEqual(len(inputs), len(patch.INPUTS))

    def test_payload_arm7tdmi_thumb1_puro_e_26_vetores(self):
        payload = (ROOT / 'patches/motor_v7/payload.bin').read_bytes()
        self.assertEqual(len(payload) % 4, 0)
        self.assertLessEqual(len(payload), 0x4000)
        # Os 26 vetores iniciais (+0x00..+0xC8, passo 8) usam ldr r3, [pc, #0] (0x4B00); bx r3 (0x4718); .word dest.
        for vec in range(0, 26 * 8, 8):
            hw0, hw1, dest = struct.unpack_from('<HHI', payload, vec)
            self.assertEqual((hw0, hw1), (0x4B00, 0x4718), f'Vetor +{vec:#x} inesperado')
            self.assertEqual(dest & 1, 1, f'Destino +{vec:#x} deve ter bit Thumb')
            self.assertTrue(0x090C00D0 <= (dest & ~1) < 0x090C0000 + len(payload))

        try:
            from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
        except ImportError:
            return
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        forbidden = {'blx', 'uxth', 'uxtb', 'sxth', 'sxtb', 'rev', 'rev16', 'revsh', 'cbz', 'cbnz'}
        for insn in md.disasm(payload[26 * 8:], patch.ROM + patch.PAYLOAD_V7 + 26 * 8):
            self.assertNotIn(insn.mnemonic, forbidden, f'Instrução incompatível com ARM7TDMI em {insn.address:#x}')

    def test_catalogo_219_disponiveis_e_10_pendentes(self):
        with (ROOT / 'data/tms_motor_v7.csv').open(encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 229)
        avail = [r for r in rows if r['status'] == 'disponivel']
        pend = [r for r in rows if r['status'] != 'disponivel']
        self.assertEqual(len(avail), 219)
        self.assertEqual(len(pend), 10)
        self.assertEqual({int(r['tm']) for r in pend}, DEFERRED_TMS_V7)

        by_tm = {int(r['tm']): r for r in rows}
        for tm_num, (item_id, move_id, name_en) in NEW_TMS_V7.items():
            row = by_tm[tm_num]
            self.assertEqual(row['status'], 'disponivel')
            self.assertEqual(int(row['item_id']), item_id)
            self.assertEqual(int(row['internal_move']), move_id)
            self.assertEqual(row['name'].upper(), name_en)

        # Pivots existentes atualizados com troca pós-dano documentada
        for tm_num, move_id in ((48, 517), (60, 369), (196, 708)):
            self.assertEqual(by_tm[tm_num]['status'], 'disponivel')
            self.assertEqual(int(by_tm[tm_num]['internal_move']), move_id)

    def test_compatibilidade_preserva_v6_e_habilita_9_novas_tms(self):
        prior = (ROOT / 'data/compatibilidade_tms_motor_v6.bin').read_bytes()
        cur = (ROOT / 'data/compatibilidade_tms_motor_v7.bin').read_bytes()
        self.assertEqual(len(cur), 1026 * 29)
        self.assertFalse(any(a & ~b for a, b in zip(prior, cur)))
        for tm_num in NEW_TMS_V7:
            bit_idx = tm_num - 1
            byte_off, mask = bit_idx // 8, 1 << (bit_idx % 8)
            learners = sum(1 for sp in range(1, 1026) if cur[sp * 29 + byte_off] & mask)
            self.assertGreater(learners, 10, f'TM{tm_num:03d} sem aprendizes suficientes')
        for tm_num in DEFERRED_TMS_V7:
            bit_idx = tm_num - 1
            byte_off, mask = bit_idx // 8, 1 << (bit_idx % 8)
            learners = sum(1 for sp in range(1, 1026) if cur[sp * 29 + byte_off] & mask)
            self.assertEqual(learners, 0, f'TM{tm_num:03d} adiada não pode ter compatibilidade ativa')

    def test_learnsets_preservam_14323_entradas_v6_e_adicionam_59(self):
        with (ROOT / 'data/learnsets_motor_v6.csv').open(encoding='utf-8') as fh:
            prior = {(int(r['species']), int(r['level']), int(r['internal_move'])) for r in csv.DictReader(fh)}
        with (ROOT / 'data/learnsets_motor_v7.csv').open(encoding='utf-8') as fh:
            cur_rows = list(csv.DictReader(fh))
        cur = {(int(r['species']), int(r['level']), int(r['internal_move'])) for r in cur_rows}
        self.assertEqual(len(prior), 14323)
        self.assertEqual(len(cur), 14382)
        self.assertTrue(prior.issubset(cur))
        added = cur - prior
        self.assertEqual(len(added), 59)
        self.assertEqual({mid for _sp, _lv, mid in added}, {504, 571, 597, 621, 696})
        self.assertIn((716, 55, 597), added)  # Xerneas Lv. 55 -> Geomancy
        self.assertIn((764, 30, 621), added)  # Comfey Lv. 30 -> Floral Healing


@unittest.skipUnless(BASE_ENV, 'defina MOTOR_V7_BASE=/caminho/motor_v6.gba para validar a reconstrução da ROM')
class MotorV7RomBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(BASE_ENV).resolve().read_bytes()
        cls.built = patch.build(cls.source)

    def test_determinismo_e_sha256_esperado(self):
        self.assertEqual(len(self.built), 0x2000000)
        self.assertTrue(patch.OUTPUT_SHA256)
        self.assertEqual(hashlib.sha256(self.built).hexdigest(), patch.OUTPUT_SHA256)
        self.assertEqual(self.built, patch.build(self.source))

    def test_rejeita_rom_invalida(self):
        corrupted = bytearray(self.source)
        corrupted[0x100] ^= 0xFF
        with self.assertRaises(patch.PatchError):
            patch.build(bytes(corrupted))

    def test_tabelas_hooks_sentinelas_e_preservacao_de_subsistemas(self):
        # 1. Teto de nomes em batalha -> 824 (0xCE << 2 -> mov r2, #0xCE = 0x22CE) + sentinelas 822..824
        for site in patch.v6.MOVE_NAME_CAP_SITES:
            self.assertEqual(self.built[site:site + 2], b'\xce\x22')
        for mid in range(813, 825):
            raw_name = self.built[patch.complement.NAMES + 17 * mid : patch.complement.NAMES + 17 * (mid + 1)]
            self.assertIn(0xFF, raw_name, f'Nome do golpe {mid} sem terminador 0xFF em 17 bytes')
            self.assertLessEqual(raw_name.index(0xFF), 16)

        # 2. Hooks de início de batalha e início de turno apontam para payload v7
        self.assertEqual(struct.unpack_from('<I', self.built, patch.BATTLE_INIT_LIT)[0], patch.ENTRY_BATTLE_INIT_V7)
        self.assertEqual(struct.unpack_from('<I', self.built, patch.TURN_START_LIT)[0], patch.ENTRY_TURN_START_V7)

        # 3. Tabela de comandos v7 preserva callasm 0xF8..0xFF da v6 e instala overrides v7
        for site in patch.v6.CMD_TABLE_PTRS:
            self.assertEqual(struct.unpack_from('<I', self.built, site)[0], patch.ROM + patch.CMD_TABLE_V7)
        for op in range(0xF8, 0x100):
            self.assertEqual(
                struct.unpack_from('<I', self.built, patch.CMD_TABLE_V7 + 4 * op)[0],
                patch.v6.ENTRY_CALLASM,
            )
        expected_overrides = {
            0x00: patch.ENTRY_ATTACKCANCELER_V7,
            0x04: patch.ENTRY_CRITCALC_V7,
            0x05: patch.ENTRY_DAMAGE_V7,
            0x0B: patch.ENTRY_HEALTHBAR_V7,
            0x0C: patch.ENTRY_DATAHP_V7,
            0x15: patch.ENTRY_SETEFFECT_CHANCE_V7,
            0x16: patch.ENTRY_SETEFFECT_PRIMARY_V7,
            0x17: patch.ENTRY_SETEFFECT_SEC_V7,
            0x49: patch.ENTRY_MOVEEND_V7,
            0x89: patch.ENTRY_STATBUFFCHANGE_V7,
        }
        for op, addr in expected_overrides.items():
            self.assertEqual(struct.unpack_from('<I', self.built, patch.CMD_TABLE_V7 + 4 * op)[0], addr)

        # 4. Efeitos atualizados nos golpes existentes e novos
        effect_of = lambda mid: self.built[patch.complement.MOVE + 12 * mid]
        for mid in (369, 517, 708):
            self.assertEqual(effect_of(mid), 224)
        self.assertEqual(effect_of(571), 225)
        self.assertEqual(effect_of(597), 227)
        for mid in (504, 621):
            self.assertEqual(effect_of(mid), 234)
        self.assertEqual(effect_of(696), 235)
        self.assertEqual(effect_of(821), 230)
        self.assertEqual(struct.unpack_from('b', self.built, patch.complement.MOVE + 12 * 821 + 7)[0], 3)

        # 5. Loja expandida lista exatamente 219 TMs disponíveis e mantém 10 adiadas bloqueadas
        shop_items = []
        for idx in range(235):
            iid = struct.unpack_from('<H', self.built, patch.previous.SHOP_LIST + 2 * idx)[0]
            if iid == 0:
                break
            shop_items.append(iid)
        self.assertEqual(len(shop_items), 219)
        for _tm, (item_id, move_id, _en) in NEW_TMS_V7.items():
            self.assertIn(item_id, shop_items)
            mapped_move = struct.unpack_from('<H', self.built, patch.previous.NEW_MOVE_TABLE + 2 * (item_id - 289))[0]
            self.assertEqual(mapped_move, move_id)
        for tm_num in DEFERRED_TMS_V7:
            item_id = 374 + tm_num
            self.assertNotIn(item_id, shop_items)
            mapped_move = struct.unpack_from('<H', self.built, patch.previous.NEW_MOVE_TABLE + 2 * (item_id - 289))[0]
            self.assertEqual(mapped_move, 0)

        # 6. Preservação byte a byte: estojo_v2, HMs 339..346, treino_ev (0xF80000..0xF90000), eventos_fixos (0xF90000..0xFA0000) e payload v6 (0x10BE000)
        self.assertEqual(self.built[0xE00000:0xE03100], self.source[0xE00000:0xE03100])
        self.assertEqual(
            self.built[patch.previous.NEW_ITEMS + 44 * 339 : patch.previous.NEW_ITEMS + 44 * 347],
            self.source[patch.previous.NEW_ITEMS + 44 * 339 : patch.previous.NEW_ITEMS + 44 * 347],
        )
        self.assertEqual(self.built[0xF80000:0xFA0000], self.source[0xF80000:0xFA0000])
        self.assertEqual(self.built[patch.v6.PAYLOAD_V6:patch.v6.PAYLOAD_V6 + 0x1000], self.source[patch.v6.PAYLOAD_V6:patch.v6.PAYLOAD_V6 + 0x1000])


if __name__ == '__main__':
    unittest.main()
