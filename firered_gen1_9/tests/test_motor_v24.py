"""Strict exact-v23 clock patch; no ROM/save bundled."""
import os
import struct
import unittest
from pathlib import Path
from scripts import motor_v24 as p
import test_motor_v11 as old


class MotorV24DataTests(unittest.TestCase):
    def test_payload_vectors_reservation_and_shared_extension_bounds(self):
        b=p.PAYLOAD_PATH.read_bytes()
        self.assertEqual((len(b),p.digest(b)),(p.PAYLOAD_SIZE,p.PAYLOAD_SHA256))
        for i in range(2):
            load,jump,target=struct.unpack_from('<HHI',b,i*8)
            self.assertEqual((load,jump),(0x4B00,0x4718))
            self.assertTrue(target&1)
            self.assertTrue(0x090E6010<=target<0x090E6000+len(b))
        self.assertLessEqual(0x34D8+4+287,p.RECORD_OFFSET)
        self.assertLessEqual(p.RECORD_OFFSET+8,0x34D8+400)
        self.assertEqual(p.RECORD_OFFSET%4,0)
        self.assertLessEqual(p.PAYLOAD_OFFSET+len(b),p.RESERVED_LIMIT)
        # Relocated native update uses literal state/resume addresses, not a
        # raw copy of a PC-relative LDR plus a branch into the overwritten hook.
        self.assertIn(struct.pack('<II',0x030021D6,0x0810166F),b)

    def test_rejects_wrong_rom(self):
        for data in (b'',bytes(0x2000000)):
            with self.assertRaises(p.PatchError):p.build(data)

    test_exclusive_output=old.MotorV11DataTests.test_saida_exclusiva_inclusive_symlink_e_hardlink


@unittest.skipUnless(os.environ.get('MOTOR_V24_BASE'),'set MOTOR_V24_BASE')
class MotorV24BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Path(os.environ['MOTOR_V24_BASE']).read_bytes()

    def test_exact_three_ranges_and_all_v23_encounters_preserved(self):
        out=p.build(self.base);self.assertEqual(p.digest(out),p.OUTPUT_SHA256)
        restored=bytearray(out)
        for at,n in p.PATCH_RANGES:restored[at:at+n]=self.base[at:at+n]
        self.assertEqual(bytes(restored),self.base)
        self.assertEqual(len(p.PATCH_RANGES),3)
        # All v23 code/tables/guide, and old item extension code, stay identical.
        for a,b in ((0x10E4000,0x10E6000),(0x10B8000,0x10BC000)):
            self.assertEqual(out[a:b],self.base[a:b])
        self.assertEqual(p.previous.guide_csv(out),p.previous.guide_csv(self.base))

    def test_corruption_payload_and_reapplication_rejected(self):
        damaged=bytearray(self.base);damaged[-1]^=1
        for source in (bytes(damaged),p.build(self.base)):
            with self.assertRaises(p.PatchError):p.build(source)
        damaged=bytearray(p.PAYLOAD_PATH.read_bytes());damaged[-1]^=1
        with self.assertRaises(p.PatchError):p.build(self.base,bytes(damaged))
