"""Testes estruturais e de integridade do motor parcial v6 (sem saves pessoais).

Sem ROM: valida catálogo, matrizes binárias, tabela Fling e ISA ARM7TDMI do payload.
Com MOTOR_V6_BASE=/caminho/motor_v5.gba: reconstrói em memória e confere SHA-256,
invariantes de correção da auditoria e preservação dos subsistemas anteriores.
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

from scripts import motor_v6 as patch

BASE_ENV = os.environ.get('MOTOR_V6_BASE')
NEW_TMS = {
    43: (417, 374, 'FLING'),
    170: (544, 808, 'STEEL BEAM'),
    198: (572, 809, 'POLTERGEIST'),
    201: (575, 810, 'MISTY EXPLOSION'),
    210: (584, 811, 'SUPERCELL SLAM'),
    212: (586, 812, 'TRIPLE AXEL'),
}


class MotorV6DataTests(unittest.TestCase):
    def test_hashes_de_insumos_e_payload(self):
        inputs = patch.checked_inputs()
        self.assertEqual(len(inputs), len(patch.INPUTS))

    def test_payload_arm7tdmi_thumb1_puro(self):
        payload = (ROOT / 'patches/motor_v6/payload.bin').read_bytes()
        self.assertEqual(len(payload) % 4, 0)
        self.assertLessEqual(len(payload), 0x1000)
        # Os 7 vetores iniciais (+0x00..+0x30, passo 8) são: ldr r3, [pc, #0] (0x4B00); bx r3 (0x4718); .word dest.
        for vec in range(0, 7 * 8, 8):
            hw0, hw1, dest = struct.unpack_from('<HHI', payload, vec)
            self.assertEqual((hw0, hw1), (0x4B00, 0x4718), f'Vetor +{vec:#x} inesperado')
            self.assertEqual(dest & 1, 1, f'Destino +{vec:#x} deve ter bit Thumb')
            self.assertTrue(0x090BE038 <= (dest & ~1) < 0x090BE000 + len(payload))

        try:
            from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
        except ImportError:
            return
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        forbidden = {'blx', 'uxth', 'uxtb', 'sxth', 'sxtb', 'rev', 'rev16', 'revsh', 'cbz', 'cbnz'}
        for insn in md.disasm(payload[7 * 8:], patch.ROM + patch.PAYLOAD_V6 + 7 * 8):
            self.assertNotIn(insn.mnemonic, forbidden, f'Instrução incompatível com ARM7TDMI em {insn.address:#x}')

    def test_catalogo_210_disponiveis_e_19_pendentes(self):
        with (ROOT / 'data/tms_motor_v6.csv').open(encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 229)
        avail = [r for r in rows if r['status'] == 'disponivel']
        pend = [r for r in rows if r['status'] != 'disponivel']
        self.assertEqual(len(avail), 210)
        self.assertEqual(len(pend), 19)
        by_tm = {int(r['tm']): r for r in rows}
        for tm_num, (item_id, move_id, name_en) in NEW_TMS.items():
            row = by_tm[tm_num]
            self.assertEqual(row['status'], 'disponivel')
            self.assertEqual(int(row['item_id']), item_id)
            self.assertEqual(int(row['internal_move']), move_id)
            self.assertEqual(row['name'].upper(), name_en)

    def test_compatibilidade_preserva_bits_anteriores_e_habilita_6_novas_tms(self):
        prior = (ROOT / 'data/compatibilidade_tms_motor_ampliado.bin').read_bytes()
        cur = (ROOT / 'data/compatibilidade_tms_motor_v6.bin').read_bytes()
        self.assertEqual(len(cur), 1026 * 29)
        self.assertFalse(any(a & ~b for a, b in zip(prior, cur)))
        for tm_num in NEW_TMS:
            bit_idx = tm_num - 1
            byte_off, mask = bit_idx // 8, 1 << (bit_idx % 8)
            learners = sum(1 for sp in range(1, 1026) if cur[sp * 29 + byte_off] & mask)
            self.assertGreater(learners, 10, f'TM{tm_num:03d} sem aprendizes suficientes')

    def test_learnsets_preservam_14300_entradas_e_adicionam_fling(self):
        with (ROOT / 'data/learnsets_gen1_9_complemento.csv').open(encoding='utf-8') as fh:
            prior = {(int(r['species']), int(r['level']), int(r['internal_move'])) for r in csv.DictReader(fh)}
        with (ROOT / 'data/learnsets_motor_v6.csv').open(encoding='utf-8') as fh:
            cur_rows = list(csv.DictReader(fh))
        cur = {(int(r['species']), int(r['level']), int(r['internal_move'])) for r in cur_rows}
        self.assertEqual(len(prior), 14300)
        self.assertEqual(len(cur), 14323)
        self.assertTrue(prior.issubset(cur))
        added = cur - prior
        self.assertEqual(len(added), 23)
        self.assertTrue(all(mid == 374 for _sp, _lv, mid in added))
        self.assertIn((104, 20, 374), added)  # Cubone Lv. 20 -> Fling

    def test_tabela_fling_bloqueia_bolas_chaves_fosseis_tms_hms(self):
        raw = (ROOT / 'data/fling_itens_motor_v6.bin').read_bytes()
        self.assertEqual(len(raw), 605 * 2)
        entry = lambda idx: (raw[2 * idx], raw[2 * idx + 1])
        self.assertEqual(entry(0), (0, 0))
        for ball in range(1, 13):
            self.assertEqual(entry(ball), (0, 0))
        for key_id in (*range(259, 289), *range(349, 375)):
            self.assertEqual(entry(key_id), (0, 0), f'Key Item/fóssil {key_id} não pode ser arremessável')
        for tm_hm in (*range(289, 347), *range(375, 605)):
            self.assertEqual(entry(tm_hm), (0, 0))
        self.assertEqual(entry(211), (70, 2))   # Poison Barb -> PSN
        self.assertEqual(entry(202), (30, 5))   # Light Ball -> PAR
        self.assertEqual(entry(187), (30, 8))   # King's Rock -> Flinch
        self.assertEqual(entry(218), (30, 0))   # Miracle Seed -> 30 BP


@unittest.skipUnless(BASE_ENV, 'defina MOTOR_V6_BASE=/caminho/motor_v5.gba para validar a reconstrução da ROM')
class MotorV6RomBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(BASE_ENV).resolve().read_bytes()
        cls.built = patch.build(cls.source)

    def test_determinismo_e_sha256_esperado(self):
        self.assertEqual(len(self.built), 0x2000000)
        self.assertEqual(hashlib.sha256(self.built).hexdigest(), patch.OUTPUT_SHA256)
        self.assertEqual(self.built, patch.build(self.source))

    def test_rejeita_rom_invalida(self):
        corrupted = bytearray(self.source)
        corrupted[0x100] ^= 0xFF
        with self.assertRaises(patch.PatchError):
            patch.build(bytes(corrupted))

    def test_correcoes_de_auditoria_aplicadas_sem_afetar_egg_moves_nem_treino_ev(self):
        # 1. Teto de nomes em batalha -> 812 (0x22CB), sentinelas de Egg Moves intactos em 797 (0x29FD / 0x031D)
        for site in patch.MOVE_NAME_CAP_SITES:
            self.assertEqual(self.built[site:site + 2], b'\xcb\x22')
        self.assertEqual(self.built[0x10AEE6:0x10AEE8], self.source[0x10AEE6:0x10AEE8])
        self.assertEqual(self.built[0x10AF6C:0x10AF6E], self.source[0x10AF6C:0x10AF6E])

        # 2. Overflow de 1 byte em gBattleTextBuff2 corrigido para 14 caracteres + 0xFF
        self.assertEqual(self.built[0xE030BA:0xE030BC], b'\x0e\x22')

        # 3. Tabela de ícones expandida (0..604) e RETURN_TO_FIELD em 604
        for site in patch.ICON_TABLE_PTRS:
            self.assertEqual(struct.unpack_from('<I', self.built, site)[0], patch.ROM + patch.ICON_TABLE_V6)
        # Ícone 375..603 = disco TM (0x085F8080) e paleta válida na ROM; 604 = seta original (375 da base)
        arrow_orig = self.source[patch.ORIG_ICON_TABLE + 375 * 8 : patch.ORIG_ICON_TABLE + 376 * 8]
        self.assertEqual(self.built[patch.ICON_TABLE_V6 + 604 * 8 : patch.ICON_TABLE_V6 + 605 * 8], arrow_orig)
        for item_id in range(375, 604):
            pic, pal = struct.unpack_from('<II', self.built, patch.ICON_TABLE_V6 + item_id * 8)
            self.assertEqual(pic, patch.TM_DISC_PIC)
            self.assertGreaterEqual(pal, 0x085F8000)
            self.assertLess(pal, 0x09100000)

        # 4. Tabela de comandos de batalha realocada: opcode 5 = damage_v6, 0xF8..0xFF = callasm
        self.assertEqual(struct.unpack_from('<I', self.built, patch.CMD_TABLE_V6 + 5 * 4)[0], patch.ENTRY_DAMAGE_V6)
        self.assertEqual(
            struct.unpack_from('<I', self.built, patch.CMD_TABLE_V6 + 6 * 4)[0],
            struct.unpack_from('<I', self.source, patch.ORIG_CMD_TABLE + 6 * 4)[0],
        )
        for op in range(0xF8, 0x100):
            self.assertEqual(struct.unpack_from('<I', self.built, patch.CMD_TABLE_V6 + op * 4)[0], patch.ENTRY_CALLASM)

        # 5. Subsistemas treino_ev (0xF80000..0xF90000) e eventos_fixos (0xF90000..0xFA0000) preservados byte a byte
        self.assertEqual(self.built[0xF80000:0xFA0000], self.source[0xF80000:0xFA0000])
        # Código do estojo_v2 (0xE00000..0xE03000) preservado byte a byte
        self.assertEqual(self.built[0xE00000:0xE03000], self.source[0xE00000:0xE03000])

    def test_loja_e_novos_golpes_configurados(self):
        # 210 TMs disponíveis na loja expandida (terminada em 0x0000)
        shop_items = []
        for idx in range(235):
            iid = struct.unpack_from('<H', self.built, patch.previous.SHOP_LIST + 2 * idx)[0]
            if iid == 0:
                break
            shop_items.append(iid)
        self.assertEqual(len(shop_items), 210)
        for _tm, (item_id, move_id, _en) in NEW_TMS.items():
            self.assertIn(item_id, shop_items)
            mapped_move = struct.unpack_from('<H', self.built, patch.previous.NEW_MOVE_TABLE + 2 * (item_id - 289))[0]
            self.assertEqual(mapped_move, move_id)
            price = struct.unpack_from('<H', self.built, patch.previous.NEW_ITEMS + 44 * item_id + 16)[0]
            self.assertGreater(price, 0)


if __name__ == '__main__':
    unittest.main()
