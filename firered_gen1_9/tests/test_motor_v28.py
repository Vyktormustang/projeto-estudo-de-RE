"""Builder, native table relocation and finite script control flow."""
import csv,io,os,struct,tempfile,unittest
from pathlib import Path
from scripts import motor_v28 as p
from scripts.treino_ev import write_new_file

class MotorV28DataTests(unittest.TestCase):
    def test_text_layout_and_all_twenty_species_pairs_match_policy(self):
        self.assertEqual(len(p.AREA_TEXTS),20);self.assertEqual(len(p.MENUS),6)
        self.assertEqual(tuple(map(len,p.MENUS)),(7,5,5,5,5,5))
        names=p.previous.wild.load_species();rows=p.previous.policy_rows()
        for i,name in enumerate(p.MAPS):
            species=[r['night_species'] for r in rows if r['map_symbol']==name]
            self.assertEqual([names[s].name.lower() for s in species],[s.lower() for s in p.NIGHT_NAMES[i]])
        for text in p.TEXTS:
            for page in text.split('\f'):
                self.assertLessEqual(len(page.splitlines()),2)
                for line in page.splitlines():self.assertLessEqual(len(line),32)
        self.assertLess(p.TABLE_OFFSET+p.TABLE_SIZE,p.SCRIPT_OFFSET)
        self.assertLess(p.SCRIPT_OFFSET+len(p.SCRIPT_BYTES),p.TEXT_OFFSET)
        self.assertLess(p.TEXT_OFFSET+len(p.TEXT_BYTES),p.RESERVED_LIMIT)

    def test_script_only_safe_commands_and_internal_branch_targets(self):
        b=p.SCRIPT_BYTES;pc=0;starts=set();targets=[];messages=[];menus=[]
        sizes={0x0f:6,0x09:2,0x69:1,0x23:5,0x21:5,0x06:6,0x05:5,0x67:5,0x66:1,0x6d:1,0x68:1,0x6f:5,0x6b:1,0x02:1,0x28:3}
        while pc<len(b):
            starts.add(pc);op=b[pc];self.assertIn(op,sizes)
            if op==0x23:self.assertEqual(struct.unpack_from('<I',b,pc+1)[0],p.previous.ENTRY_SIGN)
            if op==0x21:self.assertEqual(struct.unpack_from('<H',b,pc+1)[0],0x800D)
            if op in (0x05,0x06):targets.append(struct.unpack_from('<I',b,pc+(2 if op==6 else 1))[0]-0x08000000-p.SCRIPT_OFFSET)
            if op==0x67:messages.append(struct.unpack_from('<I',b,pc+1)[0])
            if op==0x6f:menus.append(b[pc+3]);self.assertEqual(b[pc+4],0)
            pc+=sizes[op]
        self.assertEqual(pc,len(b));self.assertTrue(set(targets)<=starts)
        self.assertEqual(set(messages),set(p.TEXT_POINTERS[:23]));self.assertEqual(menus,list(range(65,71)))
        self.assertEqual(b[:8],p.previous.ORIGINAL_MESSAGE)

    def test_exclusive_output(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b';a.write_bytes(b'base');write_new_file(a,b,b'new')
            with self.assertRaises(Exception):write_new_file(a,b,b'replace')
            with self.assertRaises(Exception):write_new_file(a,a,b'replace')
            self.assertEqual(a.read_bytes(),b'base');self.assertEqual(b.read_bytes(),b'new')

@unittest.skipUnless(os.environ.get('MOTOR_V28_BASE'),'set MOTOR_V28_BASE')
class MotorV28BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Path(os.environ['MOTOR_V28_BASE']).read_bytes();cls.out=p.build(cls.base)
    def test_only_five_ranges_and_previous_gameplay_payloads_untouched(self):
        restored=bytearray(self.out)
        self.assertEqual(len(p.PATCH_RANGES),5)
        for at,size in p.PATCH_RANGES:restored[at:at+size]=self.base[at:at+size]
        self.assertEqual(bytes(restored),self.base)
        self.assertEqual(self.out[0x10E4000:0x10EF000],self.base[0x10E4000:0x10EF000])
        self.assertEqual(self.out[p.previous.HOOK_OFFSET:p.previous.HOOK_OFFSET+8],self.base[p.previous.HOOK_OFFSET:p.previous.HOOK_OFFSET+8])
    def test_old_65_menu_entries_preserved_and_six_new_lists_valid(self):
        table=p.menu_table(self.base)
        self.assertEqual(table[:520],self.base[p.ORIGINAL_MENU_TABLE:p.ORIGINAL_MENU_TABLE+520])
        self.assertEqual(struct.unpack_from('<I',self.out,0x139764)[0],0x08000000+p.ORIGINAL_MENU_TABLE)
        self.assertEqual(self.out[p.ORIGINAL_MENU_TABLE:p.ORIGINAL_MENU_TABLE+520],table[:520])
        for i,labels in enumerate(p.MENUS):
            ptr,count=struct.unpack_from('<IB',table,(65+i)*8);self.assertEqual(count,len(labels))
            for j,label in enumerate(labels):
                text,func=struct.unpack_from('<II',self.out,ptr-0x08000000+8*j);self.assertEqual(func,0)
                encoded=p.encode(label);self.assertEqual(self.out[text-0x08000000:text-0x08000000+len(encoded)],encoded)
    def test_complete_encounter_guide_and_native_tables_unchanged(self):
        self.assertEqual(p.previous.guide_csv(self.base),p.previous.guide_csv(self.out))
        wild=p.previous.wild;maps=wild.load_maps();names=wild.load_species()
        self.assertEqual(wild.parse_tables(self.base,maps,names),wild.parse_tables(self.out,maps,names))
        self.assertEqual(p.previous.guide_csv(self.out),(p.ROOT/'docs/guia_encontros_horario_v27.csv').read_text())
    def test_hash_reproducibility_and_corruption_rejected(self):
        self.assertEqual(p.digest(self.out),p.OUTPUT_SHA256);self.assertEqual(p.build(self.base),self.out)
        for at in (0,p.MENU_POINTER,p.TABLE_OFFSET,p.SIGN_POINTER):
            bad=bytearray(self.base);bad[at]^=1
            with self.assertRaises(p.PatchError):p.build(bytes(bad))
        for data in (self.out,b'',self.base[:-1]):
            with self.assertRaises(p.PatchError):p.build(data)
