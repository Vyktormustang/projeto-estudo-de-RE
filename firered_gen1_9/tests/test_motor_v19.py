"""SHA-locked build, exact hooks, protected inputs and exclusive output."""
import os
import struct
import unittest
from pathlib import Path
from scripts import motor_v19 as p
import test_motor_v11 as previous

class MotorV19DataTests(unittest.TestCase):
    def test_payload_vectors_hash_and_reservation(self):
        data = p.PAYLOAD_PATH.read_bytes()
        self.assertEqual(len(data), p.PAYLOAD_SIZE)
        self.assertEqual(p.digest(data), p.PAYLOAD_SHA256)
        for i in range(5):
            load, branch, target = struct.unpack_from('<HHI', data, i * 8)
            self.assertEqual((load, branch), (0x4B00, 0x4718))
            self.assertTrue(target & 1)
            self.assertTrue(0x090DD028 <= target < 0x090DD000 + len(data))
        self.assertLessEqual(p.PAYLOAD_OFFSET + len(data), p.RESERVED_LIMIT)
        self.assertEqual(len(p.PATCH_RANGES), 3)

    def test_rejects_wrong_base(self):
        for data in (b'', b'BPRE', bytes(0x2000000)):
            with self.assertRaises(p.PatchError): p.build(data)

    test_exclusive_output_symlink_hardlink = previous.MotorV11DataTests.test_saida_exclusiva_inclusive_symlink_e_hardlink

@unittest.skipUnless(os.environ.get('MOTOR_V19_BASE'), 'set MOTOR_V19_BASE')
class MotorV19BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.base = Path(os.environ['MOTOR_V19_BASE']).read_bytes()

    def test_exact_output_only_three_ranges_no_battle_or_tables_changed(self):
        out = p.build(self.base)
        self.assertEqual(p.digest(out), p.OUTPUT_SHA256)
        self.assertEqual(len(out), len(self.base))
        restored = bytearray(out)
        for at, before, entry in p.HOOKS:
            self.assertEqual(self.base[at:at+8], before)
            self.assertEqual(out[at:at+8], struct.pack('<HHI', 0x4B00, 0x4718, entry))
        for at, size in p.PATCH_RANGES: restored[at:at+size] = self.base[at:at+size]
        self.assertEqual(bytes(restored), self.base)
        self.assertEqual(out[0x10DC000:0x10DD000], self.base[0x10DC000:0x10DD000])
        self.assertEqual(out[0x6AB6A8:0x6BB7A8], self.base[0x6AB6A8:0x6BB7A8])

    def test_rejects_corruption_and_reapplication(self):
        bad = bytearray(p.PAYLOAD_PATH.read_bytes()); bad[-1] ^= 1
        for payload in (b'', bytes(bad), p.PAYLOAD_PATH.read_bytes()+b'\0'):
            with self.assertRaises(p.PatchError): p.build(self.base, payload)
        bad = bytearray(self.base); bad[-1] ^= 1
        for data in (bytes(bad), p.build(self.base)):
            with self.assertRaises(p.PatchError): p.build(data)
