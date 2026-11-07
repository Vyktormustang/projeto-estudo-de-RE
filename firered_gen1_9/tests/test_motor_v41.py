"""Strict build and preservation checks; commercial input stays private."""
import csv,io,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from scripts import motor_v41 as p,auditar_obtencao_v40 as audit
BASE=os.environ.get('MOTOR_V41_BASE');ROM=os.environ.get('MOTOR_V41_ROM')
@unittest.skipUnless(BASE and ROM,'set MOTOR_V41_BASE and MOTOR_V41_ROM')
class MotorV41BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Path(BASE).read_bytes();cls.out=Path(ROM).read_bytes()
    def test_exact_hash_rebuild_and_only_30_changed_bytes(self):
        self.assertEqual(p.digest(self.base),p.BASE_SHA256);self.assertEqual(p.digest(self.out),p.OUTPUT_SHA256)
        self.assertEqual(p.build(self.base),self.out)
        changes={i for i,(a,b) in enumerate(zip(self.base,self.out)) if a!=b}
        allowed={i for at,n in p.PATCH_RANGES for i in range(at,at+n)}
        self.assertEqual(len(changes),30);self.assertTrue(changes<=allowed);self.assertEqual(len(allowed),32)
        restored=bytearray(self.out)
        for at,n in p.PATCH_RANGES:restored[at:at+n]=self.base[at:at+n]
        self.assertEqual(bytes(restored),self.base)
    def test_all_nine_variants_one_type_null_no_species_removed(self):
        for old,new in zip(p.validate_tables(self.base),p.validate_tables(self.out,True)):
            self.assertEqual({s.species for s in old.slots}-{s.species for s in new.slots},set())
            target=[s for s in new.slots if s.species==772];self.assertEqual(len(target),1)
            self.assertEqual((target[0].min_level,target[0].max_level,target[0].chance),(20,20,10))
            self.assertEqual(old.encounter_rate,new.encounter_rate)
            for a,b in zip(old.slots,new.slots):
                if a.index!=3 or old.map.index==130:self.assertEqual(a,b)
    def test_original_variant7_and_all_other_maps_unchanged(self):
        old=p.tables(self.base)[7];self.assertEqual(self.base[old.data_offset:old.info_offset+8],self.out[old.data_offset:old.info_offset+8])
        cat=p.wild.load_species();before=p.wild.parse_tables(self.base,p.wild.load_maps(),cat);after=p.wild.parse_tables(self.out,p.wild.load_maps(),cat)
        for a,b in zip(before,after):
            if a.map.number!=122 or a.map.group!=1:self.assertEqual(a,b)
        self.assertEqual(p.wild.covered_species(before),p.wild.covered_species(after))
        self.assertEqual(len({s for s in p.wild.covered_species(after) if not cat[s].protected}),931)
    def test_fixed_native_events_and_evolutions_identical(self):
        cat=p.wild.load_species();self.assertEqual(audit.objects(self.base,cat),audit.objects(self.out,cat))
        self.assertEqual(audit.native_events(self.base),audit.native_events(self.out))
        self.assertEqual(audit.evolutions(self.base),audit.evolutions(self.out))
    def test_night_tables_and_guide_preserved(self):
        n=p.base.previous;self.assertEqual(n.pilot_tables(self.base),n.pilot_tables(self.out))
        self.assertEqual(n.guide_csv(self.base),n.guide_csv(self.out));self.assertEqual(len(n.MAPS),68)
        for at,size in p.base.PATCH_RANGES:self.assertEqual(self.base[at:at+size],self.out[at:at+size])
    def test_mystery_event_script_and_no_local_selector(self):
        before=p.trace_variant_mechanism(self.base);self.assertEqual(before,p.trace_variant_mechanism(self.out))
        self.assertFalse(before['normal_delivery_verified']);self.assertEqual(before['script_offset'],'008799BA')
        bad=bytearray(self.base);bad[0x8799BF]=0x16
        with self.assertRaises(p.PatchError):p.trace_variant_mechanism(bytes(bad))
    def test_reject_wrong_input_existing_output_and_links(self):
        for b in (self.out,self.base[:-1],b'',bytes([self.base[0]^1])+self.base[1:]):
            with self.assertRaises(p.PatchError):p.build(b)
        with tempfile.TemporaryDirectory() as td:
            src=Path(BASE).resolve();target=Path(td)/'new.gba'
            cmd=[sys.executable,'-B',str(p.ROOT/'scripts/motor_v41.py'),'--rom',str(src),'--saida',str(target)]
            result=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(target.read_bytes(),self.out)
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            link=Path(td)/'alias.gba';link.symlink_to(src)
            for dest in (src,link):
                with self.assertRaises(ValueError):p.write_new_file(src,dest,self.out)
            self.assertEqual(src.read_bytes(),self.base)
    def test_complete_reproducible_csv(self):
        text=p.guide_csv(self.out);rows=list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(rows),108);self.assertEqual(sum(r['especie']=='772' for r in rows),9)
        self.assertEqual(text,p.guide_csv(p.build(self.base)))
