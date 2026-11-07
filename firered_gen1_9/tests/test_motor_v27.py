"""Build/data contracts for the twenty-map night expansion; no commercial ROM bundled."""
import os
import struct
import unittest
from unittest.mock import patch
from pathlib import Path
from scripts import motor_v27 as p
import test_motor_v11 as previous

class MotorV27DataTests(unittest.TestCase):
    def test_payload_policy_and_vectors(self):
        data=p.PAYLOAD_PATH.read_bytes()
        self.assertEqual((len(data),p.digest(data)),(p.PAYLOAD_SIZE,p.PAYLOAD_SHA256))
        self.assertEqual(len(p.policy_rows()),40)
        for i in range(4):
            load,branch,target=struct.unpack_from('<HHI',data,i*8)
            self.assertEqual((load,branch),(0x4B00,0x4718))
            self.assertTrue(target&1)
            self.assertTrue(0x090EC020<=target<0x090EC000+len(data))
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

@unittest.skipUnless(os.environ.get('MOTOR_V27_BASE'),'set MOTOR_V27_BASE')
class MotorV27BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Path(os.environ['MOTOR_V27_BASE']).read_bytes()

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
        self.assertEqual(text,(p.ROOT/'docs/guia_encontros_horario_v27.csv').read_text())
        self.assertEqual(len(text.splitlines()),481)

    def test_corruption_and_reapplication_rejected(self):
        bad=bytearray(self.base);bad[-1]^=1
        for source in (bytes(bad),p.build(self.base)):
            with self.assertRaises(p.PatchError):p.build(source)
        payload=bytearray(p.PAYLOAD_PATH.read_bytes());payload[-1]^=1
        with self.assertRaises(p.PatchError):p.build(self.base,bytes(payload))

    def test_v23_distribution_policy_slots_and_old_payloads_untouched(self):
        self.assertEqual(p.policy_rows()[:32],p.previous.policy_rows())
        out=p.build(self.base)
        self.assertEqual(out[p.previous.PAYLOAD_OFFSET:p.previous.RESERVED_LIMIT],self.base[p.previous.PAYLOAD_OFFSET:p.previous.RESERVED_LIMIT])
        self.assertEqual(out[0x10E6000:0x10EC000],self.base[0x10E6000:0x10EC000])
        block=p.pilot_tables(self.base)
        for i in range(16):
            old=struct.unpack_from('<I',self.base,p.previous.TABLE_OFFSET+i*12+4)[0]-0x08000000
            new=struct.unpack_from('<I',block,i*12+4)[0]-0x08000000-p.TABLE_OFFSET
            self.assertEqual(block[new:new+4],self.base[old:old+4])
            self.assertEqual(block[new+8:new+56],self.base[old+8:old+56])
        self.assertEqual(p.guide_csv(self.base).splitlines()[1:385],p.previous.guide_csv(self.base).splitlines()[1:385])

    def test_protected_poipole_retained_and_protected_replacements_rejected(self):
        tables=p.wild.parse_tables(self.base,p.wild.load_maps(),p.wild.load_species())
        table=next(t for t in tables if t.kind=='land' and t.map.symbol=='MAP_ROUTE9')
        slot=table.slots[5]
        self.assertEqual((slot.species,slot.min_level,slot.max_level,slot.chance),(803,14,14,10))
        data=p.pilot_tables(self.base)
        i=p.MAPS.index('MAP_ROUTE9')
        night=struct.unpack_from('<I',data,12*i+4)[0]-0x08000000-p.TABLE_OFFSET
        self.assertEqual(data[night+8+20:night+8+24],self.base[table.data_offset+20:table.data_offset+24])
        # Focused generator negatives with synthetic metadata. Full build()
        # still rejects any wrong base/hash BEFORE consulting this generator.
        table=next(t for t in tables if t.kind=='land' and t.map.symbol=='MAP_ROUTE13')
        for protected_side in ('day_species','night_species'):
            rows=[dict(row) for row in p.policy_rows()]
            row=next(x for x in rows if x['map_symbol']=='MAP_ROUTE13' and x['slot']==3)
            row[protected_side]=803
            source=bytearray(self.base)
            if protected_side=='day_species':
                struct.pack_into('<H',source,table.data_offset+3*4+2,803)
            with patch.object(p,'policy_rows',return_value=rows):
                with self.assertRaisesRegex(p.PatchError,'protegida'):
                    p.pilot_tables(bytes(source))


    def test_new_routes_special_slots_and_snorlax_preserved(self):
        tables=p.wild.parse_tables(self.base,p.wild.load_maps(),p.wild.load_species())
        block=p.pilot_tables(self.base)
        for name,slot,species,level,chance in (
            ('MAP_ROUTE13',2,804,22,10),('MAP_ROUTE14',7,1006,30,5),
            ('MAP_ROUTE15',4,143,25,10),('MAP_ROUTE9',5,803,14,10)):
            table=next(t for t in tables if t.kind=='land' and t.map.symbol==name)
            item=table.slots[slot]
            self.assertEqual((item.species,item.min_level,item.max_level,item.chance),(species,level,level,chance))
            night=struct.unpack_from('<I',block,p.MAPS.index(name)*12+4)[0]-0x08000000-p.TABLE_OFFSET
            self.assertEqual(block[night+8+slot*4:night+12+slot*4],self.base[table.data_offset+slot*4:table.data_offset+slot*4+4])
        self.assertEqual(p.EXPECTED_SLOTS['MAP_ROUTE13'],(3,4))
        for species in (143,804,1006):
            rows=[dict(row) for row in p.policy_rows()];rows[-1]['night_species']=species
            with patch.object(p,'policy_rows',return_value=rows):
                with self.assertRaisesRegex(p.PatchError,'protegida'):p.pilot_tables(self.base)
        rows=[dict(row) for row in p.policy_rows()];rows[32]['slot']=2
        with patch.object(p,'policy_rows',return_value=rows):
            with self.assertRaisesRegex(p.PatchError,'Slots'):p.pilot_tables(self.base)
