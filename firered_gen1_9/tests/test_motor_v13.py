"""Invariantes v13: três ponteiros de comando, um callasm e payload."""
import os
import struct
import unittest
from pathlib import Path
import test_motor_v11 as v11tests
from scripts import motor_v13 as p


class MotorV13DataTests(unittest.TestCase):
    def test_payload_hash_e_quatro_vetores_thumb(self):
        data = p.PAYLOAD_PATH.read_bytes()
        self.assertEqual(p.digest(data),p.PAYLOAD_SHA256)
        self.assertEqual(len(data),454)
        for offset in range(0,32,8):
            a,b,dest = struct.unpack_from('<HHI',data,offset)
            self.assertEqual((a,b),(0x4B00,0x4718))
            self.assertEqual(dest & 1,1)
            self.assertTrue(0x08000000+p.PAYLOAD_OFFSET+32 <= (dest & ~1)
                            < 0x08000000+p.PAYLOAD_OFFSET+len(data))
        self.assertEqual((p.ENTRY_ADJUST,p.ENTRY_HEALTHBAR,p.ENTRY_DATAHP,p.ENTRY_POST),
                         tuple(0x08000001+p.PAYLOAD_OFFSET+i for i in range(0,32,8)))

    def test_rejeita_rom_invalida(self):
        for data in (b'',b'BPRE',b'\x00'*0x2000000):
            with self.assertRaises(p.PatchError):
                p.build(data)

    test_saida_exclusiva_inclusive_symlink_e_hardlink = v11tests.MotorV11DataTests.test_saida_exclusiva_inclusive_symlink_e_hardlink


@unittest.skipUnless(os.environ.get('MOTOR_V13_BASE'),'defina MOTOR_V13_BASE')
class MotorV13BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(os.environ['MOTOR_V13_BASE']).read_bytes()

    def test_build_hash_e_preservacao_integral_fora_de_cinco_regioes(self):
        out = p.build(self.base)
        self.assertEqual(p.digest(out),p.OUTPUT_SHA256)
        self.assertEqual(len(out),len(self.base))
        expected = bytearray(self.base)
        regions = []
        for opcode,previous,entry in p.COMMANDS:
            site = p.v10.CMD_TABLE_V10 + 4*opcode
            self.assertEqual(struct.unpack_from('<I',self.base,site)[0],previous)
            struct.pack_into('<I',expected,site,entry)
            regions.append((site,4))
        expected[p.CALL_SITE:p.CALL_SITE+5] = p.v10.callasm(p.ENTRY_POST)
        payload = p.PAYLOAD_PATH.read_bytes()
        expected[p.PAYLOAD_OFFSET:p.PAYLOAD_OFFSET+len(payload)] = payload
        regions.extend(((p.CALL_SITE,5),(p.PAYLOAD_OFFSET,len(payload))))
        self.assertEqual(out,bytes(expected))
        restored = bytearray(out)
        for start,size in regions:
            restored[start:start+size] = self.base[start:start+size]
        self.assertEqual(bytes(restored),self.base)
        # Soundproof v12 e payload de PP v11 continuam exatamente iguais.
        self.assertEqual(out[p.v12.TABLE_OFFSET:p.v12.TABLE_OFFSET+24],p.v12.TABLE_BYTES)
        v11size = len(p.v11.PAYLOAD_PATH.read_bytes())
        self.assertEqual(out[p.v11.PAYLOAD_OFFSET:p.v11.PAYLOAD_OFFSET+v11size],p.v11.PAYLOAD_PATH.read_bytes())

    def test_rejeita_payload_base_corrompidos_e_aplicacao_repetida(self):
        with self.assertRaises(p.PatchError):
            p.build(self.base,b'bad')
        damaged = bytearray(self.base); damaged[-1] ^= 1
        for data in (bytes(damaged),p.build(self.base)):
            with self.assertRaises(p.PatchError):
                p.build(data)
