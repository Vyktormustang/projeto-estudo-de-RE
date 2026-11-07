"""SHA-locked structural checks; no emulator or whole-campaign claim."""
import os,unittest
from pathlib import Path
from scripts import auditar_cosmog_v42 as a
ROM=os.environ.get('COSMOG_V42_ROM')

@unittest.skipUnless(ROM,'set COSMOG_V42_ROM')
class CosmogStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=Path(ROM).read_bytes();cls.report=a.audit(cls.source)
    def test_sources_and_level_rules(self):
        x=self.report
        self.assertEqual((x['wild_slots_inspected'],x['night_slots_inspected']),(2176,816))
        self.assertEqual(x['wild_line_locations'],[])
        self.assertEqual(len(x['active_line_events']),1)
        obj=x['active_line_events'][0]
        self.assertEqual(tuple(obj[k] for k in ('species','group','number','object','x','y','flag')),(789,1,81,11,12,12,0x5315))
        self.assertEqual([(e['source'],e['target'],e['method'],e['param']) for e in x['evolutions']],[(789,790,4,43),(790,791,4,53),(790,792,4,54)])
        self.assertEqual({r['map'] for r in x['ditto_table_locations']},{'Route14','PokemonMansion_B1F'})
    def test_native_breeding_table_is_not_undiscovered(self):
        stats={r['species']:r for r in self.report['species_info']}
        for sid in (789,790,791,792):
            self.assertEqual(stats[sid]['egg_groups'],[0,0]);self.assertEqual(stats[sid]['gender'],255)
        self.assertEqual(stats[132]['egg_groups'],[13,13]);self.assertEqual(stats[151]['egg_groups'],[15,15])
        self.assertEqual(stats[789]['egg_cycles'],120)
    def test_rejects_nonexact_rom_and_keeps_input(self):
        other=bytearray(self.source);other[-1]^=1
        with self.assertRaises(ValueError):a.audit(bytes(other))
        self.assertEqual(Path(ROM).read_bytes(),self.source)
