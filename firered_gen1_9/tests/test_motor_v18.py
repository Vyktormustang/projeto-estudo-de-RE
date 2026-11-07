"""Build v18: base exata, 4 intervalos, tabela sonora v12 preservada."""
import os
import struct
import unittest
from pathlib import Path
from scripts import motor_v18 as p
import test_motor_v11 as previous


class MotorV18DataTests(unittest.TestCase):
    def test_payload_hash_vetor_thumb_e_limites(self):
        data=p.PAYLOAD_PATH.read_bytes()
        self.assertEqual(len(data),94);self.assertEqual(p.digest(data),p.PAYLOAD_SHA256)
        self.assertEqual(struct.unpack_from('<HHI',data),(0x4B00,0x4718,0x090DC009))
        self.assertLessEqual(p.PAYLOAD_OFFSET+len(data),p.PAYLOAD_LIMIT)
        self.assertEqual(p.TABLE_OFFSET,p.PAYLOAD_LIMIT)
        self.assertLessEqual(p.TABLE_OFFSET+len(p.TABLE_BYTES),p.RESERVED_LIMIT)
        self.assertEqual(len(p.PATCH_RANGES),4)

    def test_lista_preserva_growl_e_eerie_acrescenta_so_parting(self):
        self.assertEqual(p.NEW_MOVES[:-1],p.v12.NEW_MOVES)
        self.assertEqual(p.NEW_MOVES[-1],571)
        self.assertEqual(p.NEW_MOVES[0],45);self.assertIn(720,p.NEW_MOVES)
        self.assertEqual(len(set(p.NEW_MOVES)),len(p.NEW_MOVES))
        self.assertEqual(p.TABLE_BYTES,p.v12.TABLE_BYTES[:-2]+struct.pack('<HH',571,65535))
        self.assertEqual(len(p.TABLE_BYTES),26)
        self.assertEqual(p.COMMANDS[1][2],0x08000000+p.TABLE_OFFSET+2)

    def test_rejeita_entrada_invalida(self):
        for data in (b'',b'BPRE',b'\x00'*0x2000000):
            with self.assertRaises(p.PatchError):p.build(data)

    test_saida_exclusiva_inclusive_symlink_e_hardlink=previous.MotorV11DataTests.test_saida_exclusiva_inclusive_symlink_e_hardlink


@unittest.skipUnless(os.environ.get('MOTOR_V18_BASE'),'defina MOTOR_V18_BASE')
class MotorV18BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Path(os.environ['MOTOR_V18_BASE']).read_bytes()

    def test_build_preserva_todos_bytes_fora_de_quatro_intervalos(self):
        out=p.build(self.base)
        self.assertEqual(len(out),0x2000000);self.assertEqual(p.digest(out),p.OUTPUT_SHA256)
        expected=bytearray(self.base)
        for offset,before,after in p.COMMANDS:
            self.assertEqual(struct.unpack_from('<I',self.base,offset)[0],before)
            struct.pack_into('<I',expected,offset,after)
        data=p.PAYLOAD_PATH.read_bytes()
        expected[p.PAYLOAD_OFFSET:p.PAYLOAD_OFFSET+len(data)]=data
        expected[p.TABLE_OFFSET:p.TABLE_OFFSET+len(p.TABLE_BYTES)]=p.TABLE_BYTES
        self.assertEqual(out,bytes(expected))
        restored=bytearray(out)
        for start,size in p.PATCH_RANGES:restored[start:start+size]=self.base[start:start+size]
        self.assertEqual(bytes(restored),self.base)
        self.assertEqual(out[p.v12.TABLE_OFFSET:p.v12.TABLE_OFFSET+24],p.v12.TABLE_BYTES)
        self.assertEqual(out[p.v12.OLD_TABLE:p.v12.OLD_TABLE+22],p.v12.OLD_TABLE_BYTES)

    def test_rejeita_corrupcao_payload_e_reaplicacao(self):
        payload=bytearray(p.PAYLOAD_PATH.read_bytes());payload[-1]^=1
        for data in (b'',bytes(payload),p.PAYLOAD_PATH.read_bytes()+b'\0'):
            with self.assertRaises(p.PatchError):p.build(self.base,data)
        damaged=bytearray(self.base);damaged[-1]^=1
        for data in (bytes(damaged),p.build(self.base)):
            with self.assertRaises(p.PatchError):p.build(data)
