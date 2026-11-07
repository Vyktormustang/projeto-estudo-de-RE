"""Invariantes de patch mínimo: nenhuma mudança fora das três regiões aprovadas."""
import os
import struct
import tempfile
import unittest
from pathlib import Path
from scripts import motor_v11 as p
from scripts.treino_ev import write_new_file, PatchError as FileError


class MotorV11DataTests(unittest.TestCase):
    def test_payload_hash_e_vetor_thumb(self):
        data = p.PAYLOAD_PATH.read_bytes()
        self.assertEqual(p.digest(data),p.PAYLOAD_SHA256)
        a,b,dest = struct.unpack_from('<HHI',data)
        self.assertEqual((a,b),(0x4B00,0x4718))
        self.assertEqual(dest & 1,1)
        self.assertTrue(p.PAYLOAD_OFFSET+0x08000008 <= (dest & ~1) < p.PAYLOAD_OFFSET+0x08000000+len(data))
        self.assertEqual(len(data),364)

    def test_rejeita_rom_invalida(self):
        for data in (b'',b'BPRE',b'\x00'*0x2000000):
            with self.assertRaises(p.PatchError):
                p.build(data)

    def test_saida_exclusiva_inclusive_symlink_e_hardlink(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td)/'source'; source.write_bytes(b'original')
            dest = Path(td)/'new'
            write_new_file(source,dest,b'new')
            for existing in (source,dest):
                with self.assertRaises(FileError):
                    write_new_file(source,existing,b'changed')
            symlink = Path(td)/'sym'; symlink.symlink_to(source)
            hardlink = Path(td)/'hard'; hardlink.hardlink_to(source)
            dangling = Path(td)/'dangling'; dangling.symlink_to(Path(td)/'missing')
            for existing in (symlink,hardlink,dangling):
                with self.assertRaises(FileError):
                    write_new_file(source,existing,b'changed')
            self.assertEqual(source.read_bytes(),b'original')
            self.assertEqual(dest.read_bytes(),b'new')


@unittest.skipUnless(os.environ.get('MOTOR_V11_BASE'),'defina MOTOR_V11_BASE')
class MotorV11BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(os.environ['MOTOR_V11_BASE']).read_bytes()

    def test_build_hash_e_preservacao_integral_fora_de_tres_regioes(self):
        out = p.build(self.base)
        self.assertEqual(p.digest(out),p.OUTPUT_SHA256)
        self.assertEqual(len(out),len(self.base))
        expected = bytearray(self.base)
        expected[p.CALL_SITE:p.CALL_SITE+5] = p.v10.callasm(p.ENTRY)
        expected[p.WAIT_OFFSET:p.WAIT_OFFSET+len(p.WAIT_SCRIPT)] = p.WAIT_SCRIPT
        payload = p.PAYLOAD_PATH.read_bytes()
        expected[p.PAYLOAD_OFFSET:p.PAYLOAD_OFFSET+len(payload)] = payload
        self.assertEqual(out,bytes(expected))
        # Removendo precisamente as três escritas, tudo deve ser igual à base:
        restored = bytearray(out)
        for start,size in ((p.CALL_SITE,5),(p.WAIT_OFFSET,len(p.WAIT_SCRIPT)),(p.PAYLOAD_OFFSET,len(payload))):
            restored[start:start+size] = self.base[start:start+size]
        self.assertEqual(bytes(restored),self.base)

    def test_rejeita_payload_ou_base_corrompidos(self):
        with self.assertRaises(p.PatchError):
            p.build(self.base,b'bad')
        damaged = bytearray(self.base); damaged[-1] ^= 1
        with self.assertRaises(p.PatchError):
            p.build(bytes(damaged))
