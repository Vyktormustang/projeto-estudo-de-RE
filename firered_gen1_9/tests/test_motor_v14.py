"""Build v14: entrada/saída exatas e preservação fora de dois intervalos."""
import os
import struct
import unittest
from pathlib import Path
from scripts import motor_v14 as p
import test_motor_v11 as previous


class MotorV14DataTests(unittest.TestCase):
    def test_payload_hash_e_vetor_thumb(self):
        data = p.PAYLOAD_PATH.read_bytes()
        self.assertEqual(len(data),210)
        self.assertEqual(p.digest(data),p.PAYLOAD_SHA256)
        a,b,dest = struct.unpack_from('<HHI',data)
        self.assertEqual((a,b),(0x4B00,0x4718))
        self.assertEqual(dest&1,1)
        self.assertTrue(p.ENTRY+8 <= dest < p.ENTRY+len(data))

    def test_rejeita_entrada_invalida(self):
        for data in (b'',b'BPRE',b'\x00'*0x2000000):
            with self.assertRaises(p.PatchError): p.build(data)

    test_saida_exclusiva_inclusive_symlink_e_hardlink = previous.MotorV11DataTests.test_saida_exclusiva_inclusive_symlink_e_hardlink


@unittest.skipUnless(os.environ.get('MOTOR_V14_BASE'),'defina MOTOR_V14_BASE')
class MotorV14BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(os.environ['MOTOR_V14_BASE']).read_bytes()

    def test_build_preserva_todos_bytes_fora_de_dois_intervalos(self):
        out = p.build(self.base)
        self.assertEqual(p.digest(out),p.OUTPUT_SHA256)
        self.assertEqual(len(out),0x2000000)
        expected = bytearray(self.base)
        struct.pack_into('<I',expected,p.COMMAND_SITE,p.ENTRY)
        payload = p.PAYLOAD_PATH.read_bytes()
        expected[p.PAYLOAD_OFFSET:p.PAYLOAD_OFFSET+len(payload)] = payload
        self.assertEqual(out,bytes(expected))
        restored = bytearray(out)
        for start,size in ((p.COMMAND_SITE,4),(p.PAYLOAD_OFFSET,len(payload))):
            restored[start:start+size] = self.base[start:start+size]
        self.assertEqual(restored,self.base)

    def test_rejeita_corrupcao_payload_e_reaplicacao(self):
        for payload in (b'',p.PAYLOAD_PATH.read_bytes()+b'\0'):
            with self.assertRaises(p.PatchError): p.build(self.base,payload)
        corrupt = bytearray(self.base); corrupt[-1] ^= 1
        for data in (bytes(corrupt),p.build(self.base)):
            with self.assertRaises(p.PatchError): p.build(data)
