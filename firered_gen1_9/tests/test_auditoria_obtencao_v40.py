"""Read-only structural audit tests. AUDITORIA_V40_ROM must be the exact release."""
import csv,io,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from scripts import auditar_obtencao_v40 as a
ROM=os.environ.get('AUDITORIA_V40_ROM')

@unittest.skipUnless(ROM,'set AUDITORIA_V40_ROM')
class AcquisitionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=Path(ROM);cls.source=cls.path.read_bytes()
        cls.rows,cls.locs,cls.evos,cls.summary=a.audit(cls.source)
        cls.by={r['pokedex']:r for r in cls.rows}
    @classmethod
    def tearDownClass(cls):
        if cls.path.read_bytes()!=cls.source:raise AssertionError('ROM changed')

    def test_1025_unique_species_and_exclusive_structural_categories(self):
        self.assertEqual(set(self.by),set(range(1,1026)));self.assertEqual(len(self.rows),1025)
        self.assertEqual(self.summary['preferred_route_counts'],dict(tabela_elegivel=931,fixo_adicional=81,
            evento_nativo=7,tanoby_condicional=1,tabela_excluida_condicional=2,evolucao_configurada=3))
        self.assertEqual(self.summary['nonlegendary_mythical_covered'],931)
        self.assertEqual(self.summary['no_route'],[]);self.assertEqual(self.summary['capture_certified_species'],0)
        self.assertTrue(all(x['captura_individual_nesta_auditoria']=='nao' for x in self.rows))

    def test_conditional_locations_are_not_promoted_to_ordinary_access(self):
        self.assertEqual(self.by[201]['rota'],'tanoby_condicional')
        for sid in (488,772):self.assertEqual(self.by[sid]['rota'],'tabela_excluida_condicional')
        self.assertIn('4024 = 7',self.by[772]['condicoes_e_pendencias'])
        self.assertIn('0849',self.by[488]['condicoes_e_pendencias'])
        for sid in (249,250,386):self.assertIn('bilhete',self.by[sid]['condicoes_e_pendencias'])

    def test_active_and_parked_shared_objects_are_distinct(self):
        active,parked=a.objects(self.source,a.wild.load_species())
        self.assertEqual((len(active),len(parked)),(110,224))
        events=a.event_rows(self.summary)
        self.assertEqual(len(events),117)
        self.assertEqual(len({x['species'] for x in events}),117)
        self.assertTrue(all(x['root_offset'] and x['trigger_offset'] for x in events))
        self.assertEqual(len({x['species'] for x in active+parked}),334)
        self.assertTrue(all(x['x']==x['y']==-1024 for x in parked))
        bad=bytearray(self.source);struct.pack_into('<I',bad,len(bad)-4,a.fixed.GENERIC_SCRIPT)
        with self.assertRaisesRegex(a.AuditError,'Uncatalogued'):a.objects(bytes(bad),a.wild.load_species())

    def test_native_events_reachable_from_actual_map_roots(self):
        rows=self.summary['native_events'];self.assertEqual({r['species'] for r in rows},{144,145,146,150,249,250,386})
        for x in rows:
            self.assertEqual(x['level'],70 if x['species'] in (150,249,250) else 30 if x['species']==386 else 50)
            self.assertIn(x['prepare_offset'],x['path']);self.assertIn(x['battle_offset'],x['path'])
            self.assertEqual(self.source[x['battle_offset']],0x25)
            self.assertEqual(a.u16(self.source,x['battle_offset']+1),0x138)
        self.assertEqual(next(x for x in rows if x['species']==250)['trigger'],'coordenada')
        self.assertGreater(len(next(x for x in rows if x['species']==386)['path']),20)

    def test_native_decoder_rejects_unknown_and_operand_false_positives(self):
        root=self.summary['native_events'][0]['root'];bad=bytearray(self.source);bad[root]=0xFF
        with self.assertRaisesRegex(a.AuditError,'Unsupported'):a.native_path(bytes(bad),root)
        # A message pointer points at bytes resembling a mon command: not executable.
        synthetic=bytearray(64);synthetic[:6]=bytes((0x67,0x20,0,0,8,2))
        synthetic[32:41]=bytes((0xB6,144,0,50,0,0,0x25,0x38,1))
        with self.assertRaisesRegex(a.AuditError,'No unique'):a.native_path(bytes(synthetic),0)

    def test_cosmog_chain_and_evolution_table_layout(self):
        self.assertEqual(len(self.evos),449)
        for source,target,level in ((789,790,43),(790,791,53),(790,792,54)):
            rows=[x for x in self.evos if x['source']==source and x['target']==target]
            self.assertEqual(len(rows),1);self.assertEqual((rows[0]['method'],rows[0]['param']),(4,level))
        for sid in (790,791,792):self.assertEqual(self.by[sid]['rota'],'evolucao_configurada')
        self.assertEqual(self.by[789]['rota'],'fixo_adicional')
        self.assertIn('nao evoluir no 53',self.by[792]['condicoes_e_pendencias'])

    def test_night_data_and_raw_tables_are_separately_accounted(self):
        night=[x for x in self.locs if x['period']=='noite'];self.assertEqual(len(night),68*12)
        self.assertEqual(len({(x['group'],x['number']) for x in night}),68)
        self.assertEqual(self.summary['all_wild_raw_species'],934)
        self.assertEqual(self.summary['raw_wild_plus_additional'],1015)
        self.assertEqual(self.summary['missing_before_native_and_evolution'],[144,145,146,150,249,250,386,790,791,792])
        self.assertTrue(all(1<=x['species']<=1025 and 1<=x['min_level']<=x['max_level']<=100 for x in self.locs))

    def test_wrong_rom_and_corruption_rejected(self):
        for b in (b'',self.source[:-1],bytes((self.source[0]^1,))+self.source[1:]):
            with self.assertRaisesRegex(a.AuditError,'Not exact'):a.audit(b)

    def test_csv_determinism_and_no_certification_leak(self):
        again=a.audit(self.source);self.assertEqual(again,(self.rows,self.locs,self.evos,self.summary))
        text=a.csv_text(self.rows,list(self.rows[0]));parsed=list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(parsed),1025);self.assertEqual(parsed[0]['pokedex'],'1');self.assertEqual(parsed[-1]['pokedex'],'1025')
        self.assertTrue(all(x['condicoes_e_pendencias'] for x in parsed))

    def test_cli_requires_new_output_and_never_changes_rom(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report';cmd=[sys.executable,'-B',str(a.ROOT/'scripts/auditar_obtencao_v40.py'),'--rom',str(self.path.resolve()),'--saida',str(out)]
            result=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
            before={x.name:x.read_bytes() for x in out.iterdir()}
            result=subprocess.run(cmd,capture_output=True,text=True);self.assertNotEqual(result.returncode,0)
            self.assertEqual(before,{x.name:x.read_bytes() for x in out.iterdir()})
            self.assertEqual(self.path.read_bytes(),self.source)
