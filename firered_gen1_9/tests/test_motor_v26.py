"""Exact-v25 builder and original HUD asset contracts; no ROM included."""
import os,struct,unittest
from pathlib import Path
from scripts import motor_v26 as p
import test_motor_v11 as prior

class MotorV26DataTests(unittest.TestCase):
    def test_payload_and_nine_vectors(self):
        b=p.PAYLOAD_PATH.read_bytes()
        self.assertEqual((len(b),p.digest(b)),(p.PAYLOAD_SIZE,p.PAYLOAD_SHA256))
        for i in range(9):
            load,jump,target=struct.unpack_from('<HHI',b,i*8)
            self.assertEqual((load,jump),(0x4B00,0x4718))
            self.assertTrue(target&1)
            self.assertTrue(0x090EA048<=target<0x090EA000+len(b))
        self.assertLessEqual(p.PAYLOAD_OFFSET+len(b),p.RESERVED_LIMIT)
    def test_rejects_wrong_input(self):
        for b in (b'',bytes(0x2000000)):
            with self.assertRaises(p.PatchError):p.build(b)
    test_exclusive_output=prior.MotorV11DataTests.test_saida_exclusiva_inclusive_symlink_e_hardlink

@unittest.skipUnless(os.environ.get('MOTOR_V26_BASE'),'set MOTOR_V26_BASE')
class MotorV26BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Path(os.environ['MOTOR_V26_BASE']).read_bytes()
    def test_only_five_ranges_and_clock_save_encounter_code_preserved(self):
        out=p.build(self.base);restored=bytearray(out)
        for at,n in p.PATCH_RANGES:restored[at:at+n]=self.base[at:at+n]
        self.assertEqual(bytes(restored),self.base)
        self.assertEqual(out[0x10E4000:0x10EA000],self.base[0x10E4000:0x10EA000])
        self.assertEqual(p.digest(out),p.OUTPUT_SHA256)
    def test_corruption_payload_and_reapplication_rejected(self):
        bad=bytearray(self.base);bad[-1]^=1
        for b in (bytes(bad),p.build(self.base)):
            with self.assertRaises(p.PatchError):p.build(b)
        bad=bytearray(p.PAYLOAD_PATH.read_bytes());bad[-1]^=1
        with self.assertRaises(p.PatchError):p.build(self.base,bytes(bad))
