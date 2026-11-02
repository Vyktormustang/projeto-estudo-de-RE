"""Testes estruturais e de integridade do motor parcial v9 (sem saves pessoais).

Sem ROM: valida partição exata dos golpes de nível (49 habilitados / +368 entradas ->
14.995 linhas totais; 8 golpes / 34 entradas retidos e documentados), hashes de
insumos e ISA ARM7TDMI Thumb-1 pura dos 32 vetores do payload.
Com MOTOR_V9_BASE=/caminho/motor_v8.gba: reconstrói em memória e confere SHA-256,
invariantes das tabelas/hooks/strings v9 (slots 243..255, strings 0x01A4..0x01C5)
e preservação byte a byte das 229/229 TMs SV e subsistemas anteriores.
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

from scripts import gerar_motor_v9 as gen_v9
from scripts import motor_v9 as patch

BASE_ENV = os.environ.get("MOTOR_V9_BASE")

EXPECTED_V9_MOVES = {mid for mid, _name in gen_v9.ENABLED_LEVEL_MOVES.values()}
EXPECTED_OMITTED_MOVES = {mid for mid, _name, _why in gen_v9.OMITTED_LEVEL_MOVES.values()}


class MotorV9DataTests(unittest.TestCase):
    def test_hashes_de_insumos_e_payload(self):
        inputs = patch._load_verified_inputs()
        self.assertEqual(len(inputs), len(patch.INPUTS))

    def test_payload_arm7tdmi_thumb1_puro_e_32_vetores(self):
        payload = (ROOT / "patches/motor_v9/payload.bin").read_bytes()
        self.assertEqual(len(payload) % 4, 0)
        self.assertLessEqual(len(payload), patch.PAYLOAD_V9_END - patch.PAYLOAD_V9)
        for vec in range(0, 32 * 8, 8):
            hw0, hw1, dest = struct.unpack_from("<HHI", payload, vec)
            self.assertEqual((hw0, hw1), (0x4B00, 0x4718), f"Vetor +{vec:#x} inesperado")
            self.assertEqual(dest & 1, 1, f"Destino +{vec:#x} deve ter bit Thumb")
            self.assertTrue(0x090C9100 <= (dest & ~1) < 0x090C9000 + len(payload))

        try:
            from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
        except ImportError:
            return
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        forbidden = {"blx", "uxth", "uxtb", "sxth", "sxtb", "rev", "rev16", "revsh", "cbz", "cbnz"}
        for insn in md.disasm(payload[32 * 8 :], patch.ROM + patch.PAYLOAD_V9 + 32 * 8):
            self.assertNotIn(insn.mnemonic, forbidden, f"Instrução incompatível com ARM7TDMI em {insn.address:#x}")

    def test_particao_49_habilitados_8_retidos_e_learnsets_14995(self):
        self.assertEqual(len(EXPECTED_V9_MOVES), 49)
        self.assertEqual(len(EXPECTED_OMITTED_MOVES), 8)
        self.assertFalse(EXPECTED_V9_MOVES & EXPECTED_OMITTED_MOVES)
        self.assertEqual(set(patch.MOVE_UPDATES_V9), EXPECTED_V9_MOVES)

        with (ROOT / "data/learnsets_motor_v8.csv").open(encoding="utf-8") as fh:
            prior = {(int(r["species"]), int(r["level"]), int(r["internal_move"])) for r in csv.DictReader(fh)}
        with (ROOT / "data/learnsets_motor_v9.csv").open(encoding="utf-8") as fh:
            cur_rows = list(csv.DictReader(fh))
        cur = {(int(r["species"]), int(r["level"]), int(r["internal_move"])) for r in cur_rows}
        self.assertEqual(len(prior), 14627)
        self.assertEqual(len(cur_rows), 14995)
        self.assertEqual(len(cur), 14995)
        self.assertTrue(prior.issubset(cur))

        added = cur - prior
        self.assertEqual(len(added), 368)
        self.assertEqual({mid for _sp, _lv, mid in added}, EXPECTED_V9_MOVES)

        with (ROOT / "docs/golpes_pendentes_complemento.csv").open(encoding="utf-8") as fh:
            pend_rows = list(csv.DictReader(fh))
        self.assertEqual(len(pend_rows), 729)
        restored = [r for r in pend_rows if (int(r["species"]), int(r["level"]), int(r["internal_move"])) in cur]
        held_back = [r for r in pend_rows if (int(r["species"]), int(r["level"]), int(r["internal_move"])) not in cur]
        self.assertEqual(len(restored), 695)
        self.assertEqual(len(held_back), 34)
        self.assertEqual({int(r["internal_move"]) for r in held_back}, EXPECTED_OMITTED_MOVES)


@unittest.skipUnless(BASE_ENV, "defina MOTOR_V9_BASE=/caminho/motor_v8.gba para validar a reconstrução da ROM")
class MotorV9RomBuildTests(unittest.TestCase):
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
        corrupted[0x120] ^= 0xFF
        with self.assertRaises(patch.PatchError):
            patch.build(bytes(corrupted))

    def test_tabelas_hooks_strings_efeitos_243_255_e_preservacao_v8(self):
        # 1. Relocação de gBattleStringsTable (408 -> 442 ponteiros: 0x000C..0x01C5) e teto 0xEB,0x23
        for ref in patch.BATTLE_STRINGS_TABLE_REFS:
            self.assertEqual(struct.unpack_from("<I", self.built, ref)[0], patch.ROM + patch.STRINGS_TABLE_V9)
        self.assertEqual(self.built[patch.BATTLE_STRING_CAP_SITE : patch.BATTLE_STRING_CAP_SITE + 2], b"\xeb\x23")
        self.assertEqual(
            self.built[patch.STRINGS_TABLE_V9 : patch.STRINGS_TABLE_V9 + 4 * patch.V8_BATTLE_STRINGS_COUNT],
            self.source[patch.v8.STRINGS_TABLE_V8 : patch.v8.STRINGS_TABLE_V8 + 4 * patch.V8_BATTLE_STRINGS_COUNT],
        )
        for idx in range(len(patch.NEW_BATTLE_STRINGS_V9)):
            ptr = struct.unpack_from(
                "<I", self.built, patch.STRINGS_TABLE_V9 + 4 * (patch.V8_BATTLE_STRINGS_COUNT + idx)
            )[0]
            self.assertTrue(patch.ROM + patch.STRINGS_TEXT_V9 <= ptr < patch.ROM + patch.STRINGS_TEXT_V9_END)

        # 2. Hooks encadeados sobre motor_v8
        self.assertEqual(struct.unpack_from("<I", self.built, patch.BATTLE_INIT_LIT)[0], patch.ENTRY_BATTLE_INIT_V9)
        self.assertEqual(struct.unpack_from("<I", self.built, patch.TURN_START_LIT)[0], patch.ENTRY_TURN_START_V9)
        self.assertEqual(struct.unpack_from("<I", self.built, patch.ENDTURN_CONT_LIT)[0], patch.ENTRY_ENDTURN_V9)
        # SetTurnOrder permanece intacto no motor_v8
        self.assertEqual(
            struct.unpack_from("<I", self.built, patch.v8.SET_TURN_ORDER_LIT)[0],
            patch.v8.ENTRY_SET_TURN_ORDER_V8,
        )

        # 3. CMD_TABLE_V9 encadeia 0x00, 0x04, 0x06 e 0x52 preservando todos os demais opcodes v6/v7/v8
        for site in patch.v6.CMD_TABLE_PTRS:
            self.assertEqual(struct.unpack_from("<I", self.built, site)[0], patch.ROM + patch.CMD_TABLE_V9)
        expected_overrides = {
            0x00: patch.ENTRY_ATTACKCANCELER_V9,
            0x04: patch.ENTRY_CRITCALC_V9,
            0x06: patch.ENTRY_TYPECALC_V9,
            0x52: patch.ENTRY_SWITCHINEFFECTS_V9,
        }
        for op in range(256):
            got = struct.unpack_from("<I", self.built, patch.CMD_TABLE_V9 + 4 * op)[0]
            if op in expected_overrides:
                self.assertEqual(got, expected_overrides[op])
            else:
                prev = struct.unpack_from("<I", self.source, patch.v8.CMD_TABLE_V8 + 4 * op)[0]
                self.assertEqual(got, prev, f"Opcode {op:#x} alterado inesperadamente")

        # 4. Todos os 13 slots finais 243..255 apontam para SCRIPTS_V9; slots 0..242 intactos
        for eff_id in range(243):
            self.assertEqual(
                struct.unpack_from("<I", self.built, patch.complement.SCRIPT_TABLE + 4 * eff_id)[0],
                struct.unpack_from("<I", self.source, patch.complement.SCRIPT_TABLE + 4 * eff_id)[0],
            )
        for eff_id in range(243, 256):
            ptr = struct.unpack_from("<I", self.built, patch.complement.SCRIPT_TABLE + 4 * eff_id)[0]
            self.assertTrue(patch.ROM + patch.DYNAMIC_SCRIPTS_START_V9 <= ptr < patch.ROM + patch.SCRIPTS_V9_END)

        # 5. Os 8 golpes fora de escopo permanecem sem regressão e toda a infraestrutura de TMs/loja/EV/rotas é idêntica à v8
        for mid in EXPECTED_OMITTED_MOVES:
            self.assertEqual(
                self.built[patch.complement.MOVE + 12 * mid : patch.complement.MOVE + 12 * (mid + 1)],
                self.source[patch.complement.MOVE + 12 * mid : patch.complement.MOVE + 12 * (mid + 1)],
            )
        unchanged_slices = (
            (0xE06000, 0xE06000 + 1026 * 29),   # compatibilidade das 229/229 TMs SV
            (0xE12000, 0xE13000),               # NEW_ITEMS / NEW_MOVE_TABLE / SHOP_LIST
            (0x10B2000, 0x10C6000),             # estojo_v2 + motor_v6 + motor_v7 + motor_v8 intactos
            (0x10B0000, 0x10B1000),             # treino_ev intacto
        )
        for start, end in unchanged_slices:
            self.assertEqual(self.built[start:end], self.source[start:end], f"Região 0x{start:X}..0x{end:X} alterada")


if __name__ == "__main__":
    unittest.main()
