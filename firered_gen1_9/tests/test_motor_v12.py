"""Patch Soundproof: apenas 4 bytes de literal e 24 bytes de tabela."""
import os
import struct
import tempfile
import unittest
from pathlib import Path
from scripts import motor_v12 as p
from scripts.treino_ev import write_new_file, PatchError as FileError


class MotorV12DataTests(unittest.TestCase):
    def test_tabela_nativa_preservada_com_um_unico_id_novo(self):
        self.assertEqual(p.NEW_MOVES[:-1], p.OLD_MOVES)
        self.assertEqual(p.NEW_MOVES[-1],720)
        self.assertEqual(len(set(p.NEW_MOVES)),len(p.NEW_MOVES))
        self.assertEqual(p.TABLE_BYTES, p.OLD_TABLE_BYTES[:-2]+struct.pack('<HH',720,0xFFFF))
        self.assertEqual(len(p.TABLE_BYTES),24)
        self.assertEqual(p.TABLE_OFFSET & 3,0)

    def test_rejeita_rom_invalida(self):
        for data in (b'',b'BPRE',b'\x00'*0x2000000):
            with self.assertRaises(p.PatchError):
                p.build(data)

    def test_saida_exclusiva_inclusive_symlink_e_hardlink(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td)/'source'; source.write_bytes(b'original')
            dest = Path(td)/'new'
            write_new_file(source,dest,b'new')
            symlink = Path(td)/'sym'; symlink.symlink_to(source)
            hardlink = Path(td)/'hard'; hardlink.hardlink_to(source)
            dangling = Path(td)/'dangling'; dangling.symlink_to(Path(td)/'missing')
            for existing in (source,dest,symlink,hardlink,dangling):
                with self.assertRaises(FileError):
                    write_new_file(source,existing,b'changed')
            self.assertEqual(source.read_bytes(),b'original')
            self.assertEqual(dest.read_bytes(),b'new')


@unittest.skipUnless(os.environ.get('MOTOR_V12_BASE'),'defina MOTOR_V12_BASE')
class MotorV12BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(os.environ['MOTOR_V12_BASE']).read_bytes()

    def test_build_hash_e_preservacao_integral_fora_de_duas_regioes(self):
        out = p.build(self.base)
        self.assertEqual(p.digest(out),p.OUTPUT_SHA256)
        self.assertEqual(len(out),0x2000000)
        self.assertEqual(struct.unpack_from('<I',out,p.POINTER_SITE)[0],p.ROM+p.TABLE_OFFSET+2)
        self.assertEqual(out[p.TABLE_OFFSET:p.TABLE_OFFSET+24],p.TABLE_BYTES)
        restored = bytearray(out)
        for start,size in ((p.POINTER_SITE,4),(p.TABLE_OFFSET,24)):
            restored[start:start+size] = self.base[start:start+size]
        self.assertEqual(bytes(restored),self.base)

    def test_rejeita_base_corrompida_e_aplicacao_repetida(self):
        damaged = bytearray(self.base); damaged[-1] ^= 1
        for data in (bytes(damaged),p.build(self.base)):
            with self.assertRaises(p.PatchError):
                p.build(data)
