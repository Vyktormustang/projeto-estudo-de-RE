"""Testes estruturais e de integridade do motor parcial v8 (sem saves pessoais).

Sem ROM: valida catálogo (229/229 disponíveis, 0 pendentes), matrizes binárias,
learnsets (+245 entradas -> 14.627) e ISA ARM7TDMI Thumb-1 pura do payload.
Com MOTOR_V8_BASE=/caminho/motor_v7.gba: reconstrói em memória e confere SHA-256,
invariantes das tabelas/hooks/strings v8 e preservação byte a byte dos subsistemas anteriores.
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

from scripts import motor_v8 as patch

BASE_ENV = os.environ.get("MOTOR_V8_BASE")

NEW_TMS_V8 = {
    52: (426, 773, "SNOWSCAPE"),
    91: (465, 390, "TOXIC SPIKES"),
    113: (487, 366, "TAILWIND"),
    116: (490, 445, "STEALTH ROCK"),
    136: (510, 599, "ELECTRIC TERRAIN"),
    137: (511, 576, "GRASSY TERRAIN"),
    138: (512, 633, "PSYCHIC TERRAIN"),
    139: (513, 577, "MISTY TERRAIN"),
    161: (535, 433, "TRICK ROOM"),
    178: (552, 356, "GRAVITY"),
}

RESTORED_LEVELUP_MOVES_V8 = {
    356, 366, 390, 393, 432, 433, 445, 471, 560, 576, 577,
    599, 614, 633, 649, 681, 772, 773,
}


class MotorV8DataTests(unittest.TestCase):
    def test_hashes_de_insumos_e_payload(self):
        inputs = patch._load_verified_inputs()
        self.assertEqual(len(inputs), len(patch.INPUTS))

    def test_payload_arm7tdmi_thumb1_puro_e_28_vetores(self):
        payload = (ROOT / "patches/motor_v8/payload.bin").read_bytes()
        self.assertEqual(len(payload) % 4, 0)
        self.assertLessEqual(len(payload), 0x3000)
        for vec in range(0, 28 * 8, 8):
            hw0, hw1, dest = struct.unpack_from("<HHI", payload, vec)
            self.assertEqual((hw0, hw1), (0x4B00, 0x4718), f"Vetor +{vec:#x} inesperado")
            self.assertEqual(dest & 1, 1, f"Destino +{vec:#x} deve ter bit Thumb")
            self.assertTrue(0x090C30E0 <= (dest & ~1) < 0x090C3000 + len(payload))

        try:
            from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
        except ImportError:
            return
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        forbidden = {"blx", "uxth", "uxtb", "sxth", "sxtb", "rev", "rev16", "revsh", "cbz", "cbnz"}
        for insn in md.disasm(payload[28 * 8 :], patch.ROM + patch.PAYLOAD_V8 + 28 * 8):
            self.assertNotIn(insn.mnemonic, forbidden, f"Instrução incompatível com ARM7TDMI em {insn.address:#x}")

    def test_catalogo_229_de_229_disponiveis_zero_pendentes(self):
        with (ROOT / "data/tms_motor_v8.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 229)
        avail = [r for r in rows if r["status"] == "disponivel"]
        pend = [r for r in rows if r["status"] != "disponivel"]
        self.assertEqual(len(avail), 229)
        self.assertEqual(len(pend), 0)

        by_tm = {int(r["tm"]): r for r in rows}
        for tm_num, (item_id, move_id, name_en) in NEW_TMS_V8.items():
            row = by_tm[tm_num]
            self.assertEqual(row["status"], "disponivel")
            self.assertEqual(int(row["item_id"]), item_id)
            self.assertEqual(int(row["internal_move"]), move_id)
            self.assertEqual(row["name"].upper(), name_en)

    def test_compatibilidade_preserva_v7_e_habilita_10_tms_finais(self):
        prior = (ROOT / "data/compatibilidade_tms_motor_v7.bin").read_bytes()
        cur = (ROOT / "data/compatibilidade_tms_motor_v8.bin").read_bytes()
        self.assertEqual(len(cur), 1026 * 29)
        self.assertFalse(any(a & ~b for a, b in zip(prior, cur)))
        for tm_num in NEW_TMS_V8:
            bit_idx = tm_num - 1
            byte_off, mask = bit_idx // 8, 1 << (bit_idx % 8)
            learners = sum(1 for sp in range(1, 1026) if cur[sp * 29 + byte_off] & mask)
            self.assertGreater(learners, 10, f"TM{tm_num:03d} sem aprendizes suficientes")

    def test_learnsets_preservam_14382_entradas_v7_e_adicionam_245(self):
        with (ROOT / "data/learnsets_motor_v7.csv").open(encoding="utf-8") as fh:
            prior = {(int(r["species"]), int(r["level"]), int(r["internal_move"])) for r in csv.DictReader(fh)}
        with (ROOT / "data/learnsets_motor_v8.csv").open(encoding="utf-8") as fh:
            cur_rows = list(csv.DictReader(fh))
        cur = {(int(r["species"]), int(r["level"]), int(r["internal_move"])) for r in cur_rows}
        self.assertEqual(len(prior), 14382)
        self.assertEqual(len(cur), 14627)
        self.assertTrue(prior.issubset(cur))
        added = cur - prior
        self.assertEqual(len(added), 245)
        self.assertEqual({mid for _sp, _lv, mid in added}, RESTORED_LEVELUP_MOVES_V8)


@unittest.skipUnless(BASE_ENV, "defina MOTOR_V8_BASE=/caminho/motor_v7.gba para validar a reconstrução da ROM")
class MotorV8RomBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(BASE_ENV).resolve().read_bytes()
        cls.built = patch.build(cls.source)

    def test_determinismo_e_sha256_esperado(self):
        self.assertEqual(len(self.built), 0x2000000)
        self.assertEqual(len(patch.OUTPUT_SHA256), 64)
        self.assertEqual(hashlib.sha256(self.built).hexdigest(), patch.OUTPUT_SHA256)
        self.assertEqual(self.built, patch.build(self.source))

    def test_rejeita_rom_invalida(self):
        corrupted = bytearray(self.source)
        corrupted[0x100] ^= 0xFF
        with self.assertRaises(patch.PatchError):
            patch.build(bytes(corrupted))

    def test_tabelas_hooks_strings_loja_e_preservacao_de_subsistemas(self):
        # 1. Relocação de gBattleStringsTable (+34 mensagens PT-BR) e teto em BufferStringBattle
        for ref in patch.BATTLE_STRINGS_TABLE_REFS:
            self.assertEqual(struct.unpack_from("<I", self.built, ref)[0], patch.ROM + patch.STRINGS_TABLE_V8)
        self.assertEqual(self.built[patch.BATTLE_STRING_CAP_SITE : patch.BATTLE_STRING_CAP_SITE + 2], b"\xd4\x23")
        for idx in range(len(patch.NEW_BATTLE_STRINGS)):
            ptr = struct.unpack_from(
                "<I", self.built, patch.STRINGS_TABLE_V8 + 4 * (patch.ORIG_BATTLE_STRINGS_COUNT + idx)
            )[0]
            self.assertTrue(patch.ROM + patch.STRINGS_TEXT_V8 <= ptr < patch.ROM + patch.STRINGS_TEXT_V8_END)

        # 2. Hooks encadeados de ciclo de vida, ordem de turno e fim de turno
        self.assertEqual(struct.unpack_from("<I", self.built, patch.BATTLE_INIT_LIT)[0], patch.ENTRY_BATTLE_INIT_V8)
        self.assertEqual(struct.unpack_from("<I", self.built, patch.TURN_START_LIT)[0], patch.ENTRY_TURN_START_V8)
        self.assertEqual(struct.unpack_from("<I", self.built, patch.SET_TURN_ORDER_LIT)[0], patch.ENTRY_SET_TURN_ORDER_V8)
        self.assertEqual(struct.unpack_from("<I", self.built, patch.ENDTURN_CONT_LIT)[0], patch.ENTRY_ENDTURN_V8)

        # 3. CMD_TABLE_V8 preserva callasm v6 (0xF8..0xFF), hooks v7 não substituídos e aplica overrides v8
        for site in patch.v6.CMD_TABLE_PTRS:
            self.assertEqual(struct.unpack_from("<I", self.built, site)[0], patch.ROM + patch.CMD_TABLE_V8)
        for op in range(0xF8, 0x100):
            self.assertEqual(
                struct.unpack_from("<I", self.built, patch.CMD_TABLE_V8 + 4 * op)[0],
                patch.v6.ENTRY_CALLASM,
            )
        for op, expected in (
            (0x04, patch.v7.ENTRY_CRITCALC_V7),
            (0x0B, patch.v7.ENTRY_HEALTHBAR_V7),
            (0x0C, patch.v7.ENTRY_DATAHP_V7),
            (0x49, patch.v7.ENTRY_MOVEEND_V7),
            (0x89, patch.v7.ENTRY_STATBUFFCHANGE_V7),
            (0x00, patch.ENTRY_ATTACKCANCELER_V8),
            (0x01, patch.ENTRY_ACCURACYCHECK_V8),
            (0x05, patch.ENTRY_DAMAGE_V8),
            (0x06, patch.ENTRY_TYPECALC_V8),
            (0x15, patch.ENTRY_SETEFFECT_CHANCE_V8),
            (0x16, patch.ENTRY_SETEFFECT_PRIMARY_V8),
            (0x17, patch.ENTRY_SETEFFECT_SECONDARY_V8),
            (0x52, patch.ENTRY_SWITCHINEFFECTS_V8),
            (0x84, patch.ENTRY_JUMPIFCANTSLEEP_V8),
            (0xBE, patch.ENTRY_RAPIDSPINFREE_V8),
            (0xE9, patch.ENTRY_WEATHERBALL_V8),
            (0xEE, patch.ENTRY_BRICKBREAK_V8),
        ):
            self.assertEqual(struct.unpack_from("<I", self.built, patch.CMD_TABLE_V8 + 4 * op)[0], expected)

        # 4. Loja expandida lista exatamente todas as 229 TMs SV e NEW_MOVE_TABLE mapeia as 10 finais
        shop_items = []
        for idx in range(235):
            iid = struct.unpack_from("<H", self.built, patch.previous.SHOP_LIST + 2 * idx)[0]
            if iid == 0:
                break
            shop_items.append(iid)
        self.assertEqual(len(shop_items), 229)
        for _tm, (item_id, move_id, _en) in NEW_TMS_V8.items():
            self.assertIn(item_id, shop_items)
            mapped_move = struct.unpack_from("<H", self.built, patch.previous.NEW_MOVE_TABLE + 2 * (item_id - 289))[0]
            self.assertEqual(mapped_move, move_id)

        # 5. Preservação byte a byte: estojo_v2, HMs 339..346, treino_ev, eventos_fixos, payload_v6, payload_v7 e egg terminator 797
        self.assertEqual(self.built[0xE00000:0xE03100], self.source[0xE00000:0xE03100])
        self.assertEqual(
            self.built[patch.previous.NEW_ITEMS + 44 * 339 : patch.previous.NEW_ITEMS + 44 * 347],
            self.source[patch.previous.NEW_ITEMS + 44 * 339 : patch.previous.NEW_ITEMS + 44 * 347],
        )
        self.assertEqual(self.built[0xF80000:0xFA0000], self.source[0xF80000:0xFA0000])
        self.assertEqual(
            self.built[patch.v6.PAYLOAD_V6 : patch.v6.PAYLOAD_V6 + 0x1000],
            self.source[patch.v6.PAYLOAD_V6 : patch.v6.PAYLOAD_V6 + 0x1000],
        )
        self.assertEqual(
            self.built[patch.v7.PAYLOAD_V7 : patch.v7.PAYLOAD_V7 + 0x1000],
            self.source[patch.v7.PAYLOAD_V7 : patch.v7.PAYLOAD_V7 + 0x1000],
        )
        for egg_site in (0x10AEE6, 0x10AF6C):
            self.assertEqual(self.built[egg_site : egg_site + 4], self.source[egg_site : egg_site + 4])


if __name__ == "__main__":
    unittest.main()
