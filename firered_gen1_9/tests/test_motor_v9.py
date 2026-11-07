"""Testes estruturais e de integridade do motor parcial v9 (sem saves pessoais).

Sem ROM: valida hashes de insumos, learnsets (+378 entradas -> 15.005,
preservando 100% das 14.627 do motor_v8), contabilidade exata dos 729 registros
omitidos inicialmente (705 restaurados entre v6..v9; restando apenas 6 golpes /
24 linhas com bloqueios estruturais Gen 3) e ISA ARM7TDMI Thumb-1 pura do payload.
Com MOTOR_V9_BASE=/caminho/motor_v8.gba: reconstrói em memória e confere SHA-256,
invariantes das tabelas/hooks/strings v9, auditoria estrita de bytes alterados e
preservação byte a byte de todos os subsistemas anteriores.
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

EXPECTED_RESTORED_V9 = {mid for mid, _name in gen_v9.ENABLED_LEVEL_MOVES.values()}
EXPECTED_DEFERRED = {492, 501, 644, 672, 677, 755}


class MotorV9DataTests(unittest.TestCase):
    def test_hashes_de_insumos_e_payload(self):
        inputs = patch._load_verified_inputs()
        self.assertEqual(len(inputs), len(patch.INPUTS))

    def test_payload_arm7tdmi_thumb1_puro_e_28_vetores(self):
        payload = (ROOT / "patches/motor_v9/payload.bin").read_bytes()
        self.assertEqual(len(payload) % 4, 0)
        self.assertLessEqual(len(payload), 0x4000)
        for vec in range(0, 28 * 8, 8):
            hw0, hw1, dest = struct.unpack_from("<HHI", payload, vec)
            self.assertEqual((hw0, hw1), (0x4B00, 0x4718), f"Vetor +{vec:#x} inesperado")
            self.assertEqual(dest & 1, 1, f"Destino +{vec:#x} deve ter bit Thumb")
            self.assertTrue(0x090C90E0 <= (dest & ~1) < 0x090C9000 + len(payload))

        try:
            from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
        except ImportError:
            return
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        forbidden = {"blx", "uxth", "uxtb", "sxth", "sxtb", "rev", "rev16", "revsh", "cbz", "cbnz"}
        for insn in md.disasm(payload[28 * 8 :], patch.ROM + patch.PAYLOAD_V9 + 28 * 8):
            self.assertNotIn(insn.mnemonic, forbidden, f"Instrução incompatível com ARM7TDMI em {insn.address:#x}")

    def test_learnsets_preservam_14627_entradas_v8_adicionam_378_e_fecham_contabilidade_729(self):
        self.assertEqual(len(EXPECTED_RESTORED_V9), 51)
        self.assertEqual(set(patch.MOVE_UPDATES_V9.keys()), EXPECTED_RESTORED_V9)
        self.assertTrue(EXPECTED_RESTORED_V9.isdisjoint(EXPECTED_DEFERRED))

        with (ROOT / "data/learnsets_motor_v8.csv").open(encoding="utf-8") as fh:
            prior = {(int(r["species"]), int(r["level"]), int(r["internal_move"])) for r in csv.DictReader(fh)}
        with (ROOT / "data/learnsets_motor_v9.csv").open(encoding="utf-8") as fh:
            cur_rows = list(csv.DictReader(fh))
        cur = {(int(r["species"]), int(r["level"]), int(r["internal_move"])) for r in cur_rows}

        self.assertEqual(len(prior), 14627)
        self.assertEqual(len(cur), 15005)
        self.assertTrue(prior.issubset(cur))
        added = cur - prior
        self.assertEqual(len(added), 378)
        self.assertEqual({mid for _sp, _lv, mid in added}, EXPECTED_RESTORED_V9)

        with (ROOT / "docs/golpes_pendentes_complemento.csv").open(encoding="utf-8") as fh:
            orig_pend = list(csv.DictReader(fh))
        deferred_rows = [r for r in orig_pend if int(r["internal_move"]) in EXPECTED_DEFERRED]
        deferred_moves = {int(r["internal_move"]) for r in deferred_rows}
        self.assertEqual(len(orig_pend), 729)
        self.assertEqual(deferred_moves, EXPECTED_DEFERRED)
        self.assertEqual(len(deferred_rows), 24)


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
        corrupted[0x100] ^= 0xFF
        with self.assertRaises(patch.PatchError):
            patch.build(bytes(corrupted))

    def test_tabelas_hooks_strings_efeitos_e_preservacao_de_subsistemas(self):
        # 1. Relocação de gBattleStringsTable (+37 mensagens PT-BR) e teto 480 em BufferStringBattle
        for ref in patch.BATTLE_STRINGS_TABLE_REFS:
            self.assertEqual(struct.unpack_from("<I", self.built, ref)[0], patch.ROM + patch.STRINGS_TABLE_V9)
        self.assertEqual(self.built[patch.BATTLE_STRING_CAP_SITE : patch.BATTLE_STRING_CAP_SITE + 2], b"\xf0\x23")
        for idx in range(len(patch.NEW_BATTLE_STRINGS_V9)):
            ptr = struct.unpack_from(
                "<I", self.built, patch.STRINGS_TABLE_V9 + 4 * (patch.V8_BATTLE_STRINGS_COUNT + idx)
            )[0]
            self.assertTrue(patch.ROM + patch.STRINGS_TEXT_V9 <= ptr < patch.ROM + patch.STRINGS_TEXT_V9_END)

        # 2. Hooks encadeados sobre motor_v8 + GetHoldEffect (0x080C725C)
        self.assertEqual(struct.unpack_from("<I", self.built, patch.BATTLE_INIT_LIT)[0], patch.ENTRY_BATTLE_INIT_V9)
        self.assertEqual(struct.unpack_from("<I", self.built, patch.TURN_START_LIT)[0], patch.ENTRY_TURN_START_V9)
        self.assertEqual(struct.unpack_from("<I", self.built, patch.ENDTURN_CONT_LIT)[0], patch.ENTRY_ENDTURN_V9)
        self.assertEqual(
            self.built[patch.GET_HOLD_EFFECT_SITE : patch.GET_HOLD_EFFECT_SITE + 8],
            bytes.fromhex("00 4b 18 47") + struct.pack("<I", patch.ENTRY_GET_HOLD_EFFECT_V9),
        )

        # 3. CMD_TABLE_V9 preserva callasm v6, hooks v7/v8 não substituídos e aplica overrides v9
        for site in patch.v6.CMD_TABLE_PTRS:
            self.assertEqual(struct.unpack_from("<I", self.built, site)[0], patch.ROM + patch.CMD_TABLE_V9)
        for op in range(0xF8, 0x100):
            self.assertEqual(
                struct.unpack_from("<I", self.built, patch.CMD_TABLE_V9 + 4 * op)[0],
                patch.v6.ENTRY_CALLASM,
            )
        for op, expected in (
            (0x01, patch.v8.ENTRY_ACCURACYCHECK_V8),
            (0x0B, patch.v8.v7.ENTRY_HEALTHBAR_V7),
            (0x0C, patch.v8.v7.ENTRY_DATAHP_V7),
            (0x15, patch.v8.ENTRY_SETEFFECT_CHANCE_V8),
            (0x16, patch.v8.ENTRY_SETEFFECT_PRIMARY_V8),
            (0x17, patch.v8.ENTRY_SETEFFECT_SECONDARY_V8),
            (0x49, patch.v8.v7.ENTRY_MOVEEND_V7),
            (0x84, patch.v8.ENTRY_JUMPIFCANTSLEEP_V8),
            (0x89, patch.v8.v7.ENTRY_STATBUFFCHANGE_V7),
            (0xBE, patch.v8.ENTRY_RAPIDSPINFREE_V8),
            (0xE9, patch.v8.ENTRY_WEATHERBALL_V8),
            (0xEE, patch.v8.ENTRY_BRICKBREAK_V8),
            (0x00, patch.ENTRY_ATTACKCANCELER_V9),
            (0x04, patch.ENTRY_CRITCALC_V9),
            (0x05, patch.ENTRY_DAMAGE_V9),
            (0x06, patch.ENTRY_TYPECALC_V9),
            (0x52, patch.ENTRY_SWITCHINEFFECTS_V9),
        ):
            self.assertEqual(struct.unpack_from("<I", self.built, patch.CMD_TABLE_V9 + 4 * op)[0], expected)

        # 4. Efeitos 243..254 apontam para SCRIPTS_V9 e os 51 golpes usam esses efeitos
        for eff_id in range(243, 255):
            ptr = struct.unpack_from("<I", self.built, patch.complement.SCRIPT_TABLE + eff_id * 4)[0]
            self.assertTrue(patch.ROM + patch.DYNAMIC_SCRIPTS_START <= ptr < patch.ROM + patch.SCRIPTS_V9_END)
        for mid, changes in patch.MOVE_UPDATES_V9.items():
            eff = self.built[patch.complement.MOVE + 12 * mid]
            self.assertEqual(eff, changes["eff"])

        # 5. Preservação byte a byte: estojo_v2, 229 TMs SV + loja + compatibilidade, HMs, treino_ev,
        #    eventos_fixos, payloads v6/v7/v8 e egg terminator 797
        self.assertEqual(self.built[0xE00000:0xE03100], self.source[0xE00000:0xE03100])
        self.assertEqual(
            self.built[patch.v8.previous.SHOP_LIST : patch.v8.previous.SHOP_LIST + 512],
            self.source[patch.v8.previous.SHOP_LIST : patch.v8.previous.SHOP_LIST + 512],
        )
        self.assertEqual(
            self.built[0xE06000 : 0xE06000 + 1026 * 29],
            self.source[0xE06000 : 0xE06000 + 1026 * 29],
        )
        self.assertEqual(
            self.built[patch.v8.previous.NEW_ITEMS + 44 * 339 : patch.v8.previous.NEW_ITEMS + 44 * 347],
            self.source[patch.v8.previous.NEW_ITEMS + 44 * 339 : patch.v8.previous.NEW_ITEMS + 44 * 347],
        )
        self.assertEqual(self.built[0xF80000:0xFA0000], self.source[0xF80000:0xFA0000])
        self.assertEqual(
            self.built[patch.v6.PAYLOAD_V6 : patch.v6.PAYLOAD_V6 + 0x1000],
            self.source[patch.v6.PAYLOAD_V6 : patch.v6.PAYLOAD_V6 + 0x1000],
        )
        self.assertEqual(
            self.built[patch.v8.v7.PAYLOAD_V7 : patch.v8.v7.PAYLOAD_V7 + 0x1800],
            self.source[patch.v8.v7.PAYLOAD_V7 : patch.v8.v7.PAYLOAD_V7 + 0x1800],
        )
        self.assertEqual(
            self.built[patch.v8.PAYLOAD_V8 : patch.v8.PAYLOAD_V8 + 0x3000],
            self.source[patch.v8.PAYLOAD_V8 : patch.v8.PAYLOAD_V8 + 0x3000],
        )
        for egg_site in (0x10AEE6, 0x10AF6C):
            self.assertEqual(self.built[egg_site : egg_site + 4], self.source[egg_site : egg_site + 4])

    def test_auditoria_estrita_de_bytes_alterados_na_rom(self):
        allowed_ranges = [
            (patch.BATTLE_INIT_LIT, patch.BATTLE_INIT_LIT + 4),
            (patch.ENDTURN_CONT_LIT, patch.ENDTURN_CONT_LIT + 4),
            (patch.TURN_START_LIT, patch.TURN_START_LIT + 4),
            (patch.BATTLE_STRING_CAP_SITE, patch.BATTLE_STRING_CAP_SITE + 2),
            (patch.GET_HOLD_EFFECT_SITE, patch.GET_HOLD_EFFECT_SITE + 8),
            (patch.complement.SCRIPT_TABLE + 243 * 4, patch.complement.SCRIPT_TABLE + 255 * 4),
            (patch.level.TABLE, 0xF60000),
            (patch.SCRIPTS_V9, patch.PAYLOAD_V9_END),
        ]
        for ref in patch.BATTLE_STRINGS_TABLE_REFS:
            allowed_ranges.append((ref, ref + 4))
        for site in patch.v6.CMD_TABLE_PTRS:
            allowed_ranges.append((site, site + 4))
        for mid in patch.MOVE_UPDATES_V9:
            allowed_ranges.append((patch.complement.MOVE + 12 * mid, patch.complement.MOVE + 12 * (mid + 1)))

        src_mv = memoryview(self.source)
        dst_mv = memoryview(self.built)
        chunk = 0x10000
        for block in range(0, len(self.source), chunk):
            if src_mv[block : block + chunk] == dst_mv[block : block + chunk]:
                continue
            for off in range(block, min(block + chunk, len(self.source))):
                if src_mv[off] != dst_mv[off]:
                    self.assertTrue(
                        any(lo <= off < hi for lo, hi in allowed_ranges),
                        f"Byte alterado fora das regiões autorizadas em 0x{off:X}",
                    )


if __name__ == "__main__":
    unittest.main()
