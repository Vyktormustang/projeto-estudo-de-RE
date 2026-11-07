"""Structural evidence and read-only/exclusive-output checks for the island audit."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from scripts import auditar_ilhas_v41 as a
ROM=os.environ.get('ILHAS_V41_ROM')
@unittest.skipUnless(ROM,'set ILHAS_V41_ROM')
class IslandStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.path=Path(ROM).resolve();cls.source=cls.path.read_bytes();cls.evidence=a.audit(cls.source)
    @classmethod
    def tearDownClass(cls):
        if cls.path.read_bytes()!=cls.source:raise AssertionError('ROM changed')
    def test_map_root_progress_and_two_ticket_flag_gates(self):
        x=self.evidence
        self.assertEqual(x['ferry']['root'],'0018F32D');self.assertEqual(x['ferry']['object'],6)
        self.assertEqual((x['ferry']['scene_variable'],x['ferry']['scene_value']),('407E',3))
        self.assertEqual(x['ferry']['special_destinations_minimum'],5)
        self.assertEqual([(t['item'],t['flag']) for t in x['tickets']],[(370,'084A'),(371,'084B')])
        self.assertFalse(x['normal_ticket_acquisition_verified']);self.assertFalse(x['full_campaign_certified'])
    def test_native_event_paths_not_raw_species_matches(self):
        events=self.evidence['native_events'];self.assertEqual({x['species'] for x in events},{249,250,386})
        for x in events:
            self.assertEqual(x['level'],30 if x['species']==386 else 70)
            self.assertEqual(x['path'][0],x['root']);self.assertIn(x['prepare_offset'],x['path'])
            self.assertIn(x['battle_offset'],x['path'])
        self.assertEqual(next(x for x in events if x['species']==250)['trigger'],'coordenada')
    def test_gift_scripts_not_promoted_to_normal_acquisition_and_reject_bad_input(self):
        for t in self.evidence['tickets']:
            self.assertFalse(t['normal_gift_delivery_verified']);self.assertTrue(t['grant_offset'])
        for b in (b'',self.source[:-1],bytes((self.source[0]^1,))+self.source[1:]):
            with self.assertRaises(ValueError):a.audit(b)
    def test_reproducible_cli_exclusive_output_and_unchanged_rom(self):
        self.assertEqual(a.audit(self.source),self.evidence)
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'evidence.json';cmd=[sys.executable,'-B',str(a.ROOT/'scripts/auditar_ilhas_v41.py'),'--rom',str(self.path),'--saida',str(out)]
            r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(out.read_text()),self.evidence);before=out.read_bytes()
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertEqual(out.read_bytes(),before);self.assertEqual(self.path.read_bytes(),self.source)
