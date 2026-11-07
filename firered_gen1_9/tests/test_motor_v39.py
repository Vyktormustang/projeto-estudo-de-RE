"""Builder, native table relocation and finite script control flow."""
import csv,io,os,struct,tempfile,unittest
from pathlib import Path
from scripts import motor_v39 as p
from scripts.treino_ev import write_new_file

class MotorV39DataTests(unittest.TestCase):
    def test_text_layout_and_all_sixtyfour_species_pairs_match_policy(self):
        self.assertEqual(len(p.AREA_TEXTS),64);self.assertEqual(len(p.MENUS),20)
        self.assertEqual(tuple(map(len,p.MENUS)),(8,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,3,8,7))
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
        self.assertEqual(set(messages),set(p.TEXT_POINTERS[:67]));self.assertEqual(menus,[65,83,84,82,82,82]+list(range(66,82)))
        self.assertEqual(b[:8],p.previous.ORIGINAL_MESSAGE)

    def test_exclusive_output(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b';a.write_bytes(b'base');write_new_file(a,b,b'new')
            with self.assertRaises(Exception):write_new_file(a,b,b'replace')
            with self.assertRaises(Exception):write_new_file(a,a,b'replace')
            self.assertEqual(a.read_bytes(),b'base');self.assertEqual(b.read_bytes(),b'new')

@unittest.skipUnless(os.environ.get('MOTOR_V39_BASE'),'set MOTOR_V39_BASE')
class MotorV39BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Path(os.environ['MOTOR_V39_BASE']).read_bytes();cls.out=p.build(cls.base)
    def test_only_eight_ranges_and_previous_gameplay_payloads_untouched(self):
        restored=bytearray(self.out)
        self.assertEqual(len(p.PATCH_RANGES),8)
        for at,size in p.PATCH_RANGES:restored[at:at+size]=self.base[at:at+size]
        self.assertEqual(bytes(restored),self.base)
        self.assertEqual(self.out[0x10E4000:0x1125000],self.base[0x10E4000:0x1125000])
        self.assertEqual(struct.unpack_from('<I',self.out,p.previous.HOOK_OFFSET+4)[0],p.previous.ENTRY_ENCOUNTER)
    def test_old_65_menu_entries_preserved_and_twenty_lists_valid(self):
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
        self.assertEqual(p.previous.guide_csv(self.out),(p.ROOT/'docs/guia_encontros_horario_v39.csv').read_text())
    def test_hash_reproducibility_and_corruption_rejected(self):
        self.assertEqual(p.digest(self.out),p.OUTPUT_SHA256);self.assertEqual(p.build(self.base),self.out)
        for at in (0,p.MENU_POINTER,p.TABLE_OFFSET,p.SIGN_POINTER):
            bad=bytearray(self.base);bad[at]^=1
            with self.assertRaises(p.PatchError):p.build(bytes(bad))
        for data in (self.out,b'',self.base[:-1]):
            with self.assertRaises(p.PatchError):p.build(data)

    def test_previous_sixty_night_tables_policy_and_guide_prefix_unchanged(self):
        e=p.previous;old=e.previous;new=e.pilot_tables(self.base)
        self.assertEqual(e.policy_rows()[:120],old.policy_rows())
        self.assertEqual(e.guide_csv(self.base).splitlines()[:1441],old.guide_csv(self.base).splitlines())
        for i in range(60):
            ptr=struct.unpack_from('<I',new,i*12+4)[0]-0x08000000-e.TABLE_OFFSET
            previous_ptr=struct.unpack_from('<I',self.base,old.TABLE_OFFSET+i*12+4)[0]-0x08000000
            self.assertEqual(new[ptr:ptr+4],self.base[previous_ptr:previous_ptr+4])
            self.assertEqual(new[ptr+8:ptr+56],self.base[previous_ptr+8:previous_ptr+56])
        self.assertEqual(p.AREA_TEXTS[:60],p.base.AREA_TEXTS)

    def test_protected_slots_retained_and_new_replacements_reject_protected_species(self):
        from unittest.mock import patch
        e=p.previous;catalog=e.wild.load_species();tables=e.wild.parse_tables(self.base,e.wild.load_maps(),catalog);data=e.pilot_tables(self.base)
        for name,index,species in [('MAP_ROUTE23',4,1021),('MAP_ROUTE23',5,197),('MAP_ROUTE13',2,804),('MAP_ROUTE14',7,1006),('MAP_ROUTE15',4,143),('MAP_ROUTE9',5,803),('MAP_ONE_ISLAND_KINDLE_ROAD',4,1000),('MAP_ONE_ISLAND_TREASURE_BEACH',5,887),('MAP_TWO_ISLAND_CAPE_BRINK',5,1018),('MAP_THREE_ISLAND_BOND_BRIDGE',5,784),('MAP_FIVE_ISLAND_MEADOW',5,988),('MAP_SIX_ISLAND_WATER_PATH',5,985),('MAP_SIX_ISLAND_RUIN_VALLEY',5,986),('MAP_THREE_ISLAND_BERRY_FOREST',5,96),('MAP_THREE_ISLAND_BERRY_FOREST',9,97),('MAP_SEVEN_ISLAND_SEVAULT_CANYON_ENTRANCE',5,797),('MAP_SEVEN_ISLAND_SEVAULT_CANYON',5,794),('MAP_MT_MOON_1F',4,479),('MAP_MT_MOON_1F',11,35),('MAP_MT_MOON_B1F',9,1012),('MAP_MT_MOON_B2F',11,885),('MAP_DIGLETTS_CAVE_B1F',0,50),('MAP_DIGLETTS_CAVE_B1F',9,51),('MAP_DIGLETTS_CAVE_B1F',6,442),('MAP_FOUR_ISLAND_ICEFALL_CAVE_ENTRANCE',4,983),('MAP_FOUR_ISLAND_ICEFALL_CAVE_ENTRANCE',0,86),('MAP_FOUR_ISLAND_ICEFALL_CAVE_ENTRANCE',5,87),('MAP_FOUR_ISLAND_ICEFALL_CAVE_1F',0,220),('MAP_FOUR_ISLAND_ICEFALL_CAVE_B1F',6,989),('MAP_FOUR_ISLAND_ICEFALL_CAVE_BACK',5,875),('MAP_FOUR_ISLAND_ICEFALL_CAVE_BACK',11,87),('MAP_POKEMON_MANSION_1F',1,1024),('MAP_POKEMON_MANSION_1F',2,376),('MAP_POKEMON_MANSION_3F',2,149),('MAP_POKEMON_MANSION_B1F',3,132),('MAP_VICTORY_ROAD_1F',5,1023),('MAP_VICTORY_ROAD_2F',5,799),('MAP_VICTORY_ROAD_3F',5,1005),('MAP_VICTORY_ROAD_3F',2,448),('MAP_POWER_PLANT',6,796),('MAP_SEAFOAM_ISLANDS_B1F',7,133),('MAP_SEAFOAM_ISLANDS_B2F',3,984),('MAP_SEAFOAM_ISLANDS_B2F',4,471),('MAP_SEAFOAM_ISLANDS_B3F',3,998),('MAP_SEAFOAM_ISLANDS_B3F',5,196),('MAP_SEAFOAM_ISLANDS_B4F',2,992),('MAP_SEAFOAM_ISLANDS_B4F',5,136),('MAP_MT_EMBER_RUBY_PATH_1F',2,805),('MAP_MT_EMBER_RUBY_PATH_B1F',9,990),('MAP_MT_EMBER_RUBY_PATH_B1F',5,142),('MAP_MT_EMBER_RUBY_PATH_B2F',5,445),('MAP_MT_EMBER_RUBY_PATH_B3F',3,806),('MAP_CERULEAN_CAVE_1F',5,798),('MAP_CERULEAN_CAVE_2F',5,987),('MAP_CERULEAN_CAVE_B1F',4,993),('MAP_SEAFOAM_ISLANDS_1F',2,795)]:
            t=next(t for t in tables if t.map.symbol==name and t.kind=='land');self.assertEqual(t.slots[index].species,species)
            ptr=struct.unpack_from('<I',data,e.MAPS.index(name)*12+4)[0]-0x08000000-e.TABLE_OFFSET
            self.assertEqual(data[ptr+8+index*4:ptr+12+index*4],self.base[t.data_offset+index*4:t.data_offset+index*4+4])
        for species in (143,804,1006,1021):
            rows=[dict(r) for r in e.policy_rows()];rows[-1]['night_species']=species
            with patch.object(e,'policy_rows',return_value=rows):
                with self.assertRaisesRegex(e.PatchError,'protegida'):e.pilot_tables(self.base)

    def test_payload_vectors_hashes_and_corrupt_policy_rejected(self):
        e=p.previous;b=e.PAYLOAD_PATH.read_bytes();self.assertEqual(len(b),e.PAYLOAD_SIZE);self.assertEqual(e.digest(b),e.PAYLOAD_SHA256)
        for at in range(0,32,8):
            self.assertEqual(b[at:at+4],bytes.fromhex('004b1847'))
            ptr=struct.unpack_from('<I',b,at+4)[0];self.assertTrue(ptr&1);self.assertTrue(0x08000000+e.PAYLOAD_OFFSET<=ptr<0x08000000+e.PAYLOAD_OFFSET+len(b))
        for data in (b'',b[:-1],bytes([b[0]^1])+b[1:]):
            with self.assertRaises(e.PatchError):e.changes(self.base,data)
        with self.assertRaises(e.PatchError):e.policy_rows(e.POLICY_PATH.read_bytes()+b'\n')

    def test_slot_exceptions_cannot_target_preserved_slots(self):
        from unittest.mock import patch
        e=p.previous
        expected={'MAP_POKEMON_MANSION_1F':(3,4),'MAP_POKEMON_MANSION_2F':(2,3),'MAP_POKEMON_MANSION_3F':(3,4),'MAP_POKEMON_MANSION_B1F':(2,4),'MAP_VICTORY_ROAD_3F':(3,4),'MAP_SEAFOAM_ISLANDS_B1F':(2,3),'MAP_SEAFOAM_ISLANDS_B2F':(2,5),'MAP_SEAFOAM_ISLANDS_B3F':(2,4),'MAP_SEAFOAM_ISLANDS_B4F':(3,4),'MAP_MT_EMBER_RUBY_PATH_1F':(3,4),'MAP_MT_EMBER_RUBY_PATH_B1F':(2,3),'MAP_MT_EMBER_RUBY_PATH_B2F':(2,3),'MAP_MT_EMBER_RUBY_PATH_B3F':(2,4),'MAP_CERULEAN_CAVE_1F':(2,3),'MAP_CERULEAN_CAVE_2F':(2,3),'MAP_CERULEAN_CAVE_B1F':(2,3),'MAP_SEAFOAM_ISLANDS_1F':(3,4)}
        for name,slots in expected.items():
            self.assertEqual(e.EXPECTED_SLOTS[name],slots)
            self.assertEqual(tuple(r['slot'] for r in e.policy_rows() if r['map_symbol']==name),slots)
        for name,old_slot,forbidden_slot in (('MAP_POKEMON_MANSION_1F',3,2),('MAP_POKEMON_MANSION_3F',3,2),('MAP_POKEMON_MANSION_B1F',4,3),('MAP_VICTORY_ROAD_3F',3,2),('MAP_SEAFOAM_ISLANDS_B2F',2,3),('MAP_SEAFOAM_ISLANDS_B2F',5,4),('MAP_SEAFOAM_ISLANDS_B3F',2,3),('MAP_SEAFOAM_ISLANDS_B4F',3,2),('MAP_MT_EMBER_RUBY_PATH_1F',3,2),('MAP_MT_EMBER_RUBY_PATH_B1F',3,9),('MAP_MT_EMBER_RUBY_PATH_B2F',3,5),('MAP_MT_EMBER_RUBY_PATH_B3F',4,3),('MAP_CERULEAN_CAVE_1F',3,5),('MAP_CERULEAN_CAVE_2F',3,5),('MAP_CERULEAN_CAVE_B1F',3,4),('MAP_SEAFOAM_ISLANDS_1F',3,2)):
            rows=[dict(r) for r in e.policy_rows()]
            row=next(r for r in rows if r['map_symbol']==name and r['slot']==old_slot)
            row['slot']=forbidden_slot
            with patch.object(e,'policy_rows',return_value=rows):
                # Old areas are rejected by immutable-prefix protection; new
                # areas reach the explicit slot-set guard.
                message='Política anterior alterada' if name in e.previous.MAPS else 'Slots inesperados'
                with self.assertRaisesRegex(e.PatchError,message):e.pilot_tables(self.base)

    def test_expanded_encounter_reserve_and_menu_boundaries(self):
        from unittest.mock import patch
        e=p.previous
        self.assertEqual(e.TABLE_SIZE,64*68)
        self.assertGreater(e.TABLE_SIZE,0x1000)
        self.assertEqual(e.RESERVED_LIMIT-e.TABLE_OFFSET,0x2000)
        self.assertLessEqual(e.TABLE_OFFSET+e.TABLE_SIZE,e.RESERVED_LIMIT)
        self.assertEqual(e.RESERVED_LIMIT,p.TABLE_OFFSET)
        self.assertLessEqual(p.TABLE_OFFSET+p.TABLE_SIZE,p.SCRIPT_OFFSET)
        self.assertLessEqual(p.SCRIPT_OFFSET+len(p.SCRIPT_BYTES),p.TEXT_OFFSET)
        self.assertLessEqual(p.TEXT_OFFSET+len(p.TEXT_BYTES),p.RESERVED_LIMIT)
        with patch.object(e,'RESERVED_LIMIT',e.TABLE_OFFSET+0x1000):
            with self.assertRaisesRegex(e.PatchError,'Reserva excedida'):e.changes(self.base)
        with patch.object(p,'SCRIPT_OFFSET',p.TABLE_OFFSET+p.TABLE_SIZE-1):
            with self.assertRaisesRegex(p.PatchError,'Reserva excedida'):p.changes(self.base)
