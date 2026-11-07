"""Diagnóstico histórico: dados públicos e, opcionalmente, sessão sintética no mGBA."""
from __future__ import annotations
import importlib.util
import os
import unittest
import zipfile
from pathlib import Path
from scripts import diagnostico_hook_v3 as p


class HookV3StaticTests(unittest.TestCase):
    def test_calculo_dos_literais_e_retorno(self):
        self.assertEqual(p.literal_address(0x08000A38, 1), 0x08000A40)
        self.assertEqual(p.literal_address(0x08000A38, 0), 0x08000A3C)
        self.assertEqual(p.GOOD_SITE, b'\x00' + p.BAD_SITE[1:])
        self.assertEqual(p.DEBUG_TRAMP[-8:], bytes.fromhex('fc ff 03 02 41 0a 00 08'))
        with zipfile.ZipFile(p.ARCHIVE) as archive:
            site = bytes.fromhex(archive.read('reports/site_v3.hex').decode())
            tramp = bytes.fromhex(archive.read('reports/tramp_v3.hex').decode())
        self.assertEqual(site, p.BAD_SITE)
        self.assertTrue(tramp.endswith(bytes.fromhex('08 23 1b 06 a4 22 12 01 9b 18 03 22 9b 18 18 47')))

    def test_rejeita_entrada_desconhecida(self):
        with self.assertRaises(ValueError):
            p.restore_v3(b'\0' * 32)
        with self.assertRaises(ValueError):
            p.instrument(b'\0' * 32, True)

    @unittest.skipUnless(importlib.util.find_spec('capstone'), 'capstone não instalado')
    def test_desmontagem_capstone_site_e_trampolim_de_teste(self):
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
        d = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        site = [(i.mnemonic, i.op_str) for i in d.disasm(p.BAD_SITE[:4], 0x08000A38)]
        self.assertEqual(site, [('ldr', 'r3, [pc, #4]'), ('bx', 'r3')])
        good = list(d.disasm(p.GOOD_SITE[:4], 0x08000A38))
        self.assertEqual((good[0].mnemonic, good[0].op_str), ('ldr', 'r3, [pc, #0]'))
        code = list(d.disasm(p.DEBUG_TRAMP[:24], 0x08EB0C00))
        self.assertEqual((code[1].mnemonic, code[1].op_str), ('ldr', 'r0, [pc, #0x14]'))
        self.assertEqual((code[-1].mnemonic, code[-1].op_str), ('bx', 'r3'))


@unittest.skipUnless(os.getenv('HOOK_TEST_ROM') and os.getenv('MGBA_CORE'),
                     'defina HOOK_TEST_ROM e MGBA_CORE para a integração mGBA')
class HookV3MGBATests(unittest.TestCase):
    def test_contador_na_chamada_forcada_e_no_quarto(self):
        result = p.run(Path(os.environ['HOOK_TEST_ROM']), Path(os.environ['MGBA_CORE']))
        self.assertEqual(result['chamadas_forcadas']['antigo']['contador'], 0)
        self.assertEqual(result['chamadas_forcadas']['corrigido']['contador'], 1)
        self.assertEqual(result['mapa_sintetico'], {'grupo': 4, 'numero': 1})
        self.assertGreater(result['contadores_em_quarto_a_cada_60_frames'][0], 0)
        self.assertEqual(result['controle_sem_patch_apos_240_frames'], 0)
