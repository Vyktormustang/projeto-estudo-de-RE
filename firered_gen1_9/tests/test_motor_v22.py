"""Build/data contracts for the twelve-map night expansion; no commercial ROM bundled."""
import os
import struct
import unittest
from pathlib import Path
from scripts import motor_v22 as p
import test_motor_v11 as previous

class MotorV22DataTests(unittest.TestCase):
    def test_payload_policy_and_vectors(self):
        data=p.PAYLOAD_PATH.read_bytes()
        self.assertEqual((len(data),p.digest(data)),(p.PAYLOAD_SIZE,p.PAYLOAD_SHA256))
        self.assertEqual(len(p.policy_rows()),24)
        for i in range(4):
            load,branch,target=struct.unpack_from('<HHI',data,i*8)
            self.assertEqual((load,branch),(0x4B00,0x4718))
            self.assertTrue(target&1)
            self.assertTrue(0x090E2020<=target<0x090E2000+len(data))
        self.assertEqual(data[32:40],p.NATIVE_PROLOGUE)
        with self.assertRaises(p.PatchError):p.policy_rows(p.POLICY_PATH.read_bytes()+b'\n')

    def test_script_preserves_original_message_and_branches_to_valid_texts(self):
        s=p.SCRIPT_BYTES
        self.assertTrue(s.startswith(p.ORIGINAL_MESSAGE))
        self.assertEqual(s[8:13],b'\x23'+struct.pack('<I',p.ENTRY_SIGN))
        self.assertEqual(s[13:18],b'\x21\x0d\x80\x01\x00')
        self.assertEqual(s[18:20],b'\x06\x01')
        dest=struct.unpack_from('<I',s,20)[0]-0x08000000-p.SCRIPT_OFFSET
        self.assertEqual(s[dest:dest+2],b'\x0f\0')
        self.assertEqual(struct.unpack_from('<I',s,dest+2)[0],0x08000000+p.TEXT_OFFSET+len(p.DAY_BYTES))
        self.assertEqual(s[-1],2)
        self.assertEqual(len(p.PATCH_RANGES),6)
        for text in (p.DAY_TEXT,p.NIGHT_TEXT):
            for page in text.split('\f'):
                self.assertEqual(len(page.splitlines()),2)
                self.assertTrue(all(len(line)<=32 for line in page.splitlines()))
        ordered=sorted(p.PATCH_RANGES)
        for (start,n),(next_start,_) in zip(ordered,ordered[1:]):self.assertLessEqual(start+n,next_start)
        self.assertLessEqual(p.TEXT_OFFSET+len(p.TEXT_BYTES),p.RESERVED_LIMIT)

    def test_rejects_wrong_rom(self):
        for data in (b'',bytes(0x2000000)):
            with self.assertRaises(p.PatchError):p.build(data)

    test_exclusive_output=previous.MotorV11DataTests.test_saida_exclusiva_inclusive_symlink_e_hardlink

@unittest.skipUnless(os.environ.get('MOTOR_V22_BASE'),'set MOTOR_V22_BASE')
class MotorV22BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Path(os.environ['MOTOR_V22_BASE']).read_bytes()

    def test_only_six_ranges_and_all_original_wild_tables_preserved(self):
        out=p.build(self.base);self.assertEqual(p.digest(out),p.OUTPUT_SHA256)
        restored=bytearray(out)
        for at,n in p.PATCH_RANGES:restored[at:at+n]=self.base[at:at+n]
        self.assertEqual(bytes(restored),self.base)
        catalog=p.wild.load_species();maps=p.wild.load_maps()
        before=p.wild.parse_tables(self.base,maps,catalog);after=p.wild.parse_tables(out,maps,catalog)
        self.assertEqual(before,after)
        # Full old coverage remains available by day; not just eight new species.
        self.assertEqual(p.wild.covered_species(before),p.wild.covered_species(after))
        block=p.pilot_tables(self.base)
        for i,name in enumerate(p.MAPS):
            old,new,g,m,_=struct.unpack_from('<IIBBH',block,i*12)
            table=next(t for t in before if t.map.symbol==name and t.kind=='land')
            self.assertEqual((old,g,m),(0x08000000+table.info_offset,table.map.group,table.map.number))
            at=new-0x08000000-p.TABLE_OFFSET
            self.assertEqual(block[at],table.encounter_rate)
            row_map={r['slot']:r['night_species'] for r in p.policy_rows() if r['map_symbol']==name}
            for slot in table.slots:
                lo,hi,s=struct.unpack_from('<BBH',block,at+8+slot.index*4)
                self.assertEqual((lo,hi),(slot.min_level,slot.max_level))
                self.assertEqual(s,row_map.get(slot.index,slot.species))

    def test_documented_guide_matches_generated_tables(self):
        text=p.guide_csv(self.base)
        self.assertEqual(text,(p.ROOT/'docs/guia_encontros_horario_v22.csv').read_text())
        self.assertEqual(len(text.splitlines()),289)

    def test_corruption_and_reapplication_rejected(self):
        bad=bytearray(self.base);bad[-1]^=1
        for source in (bytes(bad),p.build(self.base)):
            with self.assertRaises(p.PatchError):p.build(source)
        payload=bytearray(p.PAYLOAD_PATH.read_bytes());payload[-1]^=1
        with self.assertRaises(p.PatchError):p.build(self.base,bytes(payload))

    def test_v21_distribution_policy_slots_and_old_payloads_untouched(self):
        self.assertEqual(p.policy_rows()[:16],p.previous.policy_rows())
        out=p.build(self.base)
        self.assertEqual(out[p.previous.PAYLOAD_OFFSET:p.previous.RESERVED_LIMIT],self.base[p.previous.PAYLOAD_OFFSET:p.previous.RESERVED_LIMIT])
        block=p.pilot_tables(self.base)
        for i in range(8):
            old=struct.unpack_from('<I',self.base,p.previous.TABLE_OFFSET+i*12+4)[0]-0x08000000
            new=struct.unpack_from('<I',block,i*12+4)[0]-0x08000000-p.TABLE_OFFSET
            self.assertEqual(block[new:new+4],self.base[old:old+4])
            self.assertEqual(block[new+8:new+56],self.base[old+8:old+56])
        self.assertEqual(p.guide_csv(self.base).splitlines()[1:193],p.previous.guide_csv(self.base).splitlines()[1:193])
