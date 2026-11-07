"""Isolated native contracts, not island/puzzle access or capture tests.

Fresh synthetic Route 1 fixture on exact v40; only state copies get flags,
variables, map ids and RNG set. No personal save or cross-version state.
"""
import hashlib,json,os,struct,tempfile,unittest
from pathlib import Path
from scripts import auditar_obtencao_v40 as a
from mgba_treino_harness import Emulator,offset,u32,put32
from test_eventos_fixos_mgba import route_entry_fixture,enemy
from test_estojo_expandido_mgba import save1
from test_motor_v19_mgba import MotorV19ClockTests,set_time
from test_motor_v40_encounters_mgba import MotorV40EncounterTests,SEEDS,RNG
ROM=os.environ.get('AUDITORIA_V40_ROM');CORE=os.environ.get('MGBA_CORE')

@unittest.skipUnless(ROM and CORE,'set AUDITORIA_V40_ROM and MGBA_CORE')
class AcquisitionNativeProbes(unittest.TestCase):
    call=MotorV40EncounterTests.call
    evolution=MotorV19ClockTests.evolution
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM);cls.source=cls.rom.read_bytes()
        if a.release.digest(cls.source)!=a.release.OUTPUT_SHA256:raise ValueError('Not exact v40')
        cls.temp=tempfile.TemporaryDirectory();cls.f=Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture=route_entry_fixture(cls.f);cls.observations=[]
    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if cls.rom.read_bytes()!=cls.source:raise AssertionError('ROM changed')
        dest=os.environ.get('AUDITORIA_V40_PROBES')
        if dest:
            with Path(dest).open('x',encoding='utf-8') as f:
                json.dump(dict(rom_sha256=a.release.OUTPUT_SHA256,core_sha256=hashlib.sha256(Path(CORE).read_bytes()).hexdigest(),
                    scope='Isolated direct calls with synthetic state, no live captures, map travel or evolution scenes',
                    observations=cls.observations),f,indent=2,ensure_ascii=False);f.write('\n')

    def state(self,g,m,minute):
        st=set_time(self.fixture,minute);at=offset(save1(st));st[at+4:at+6]=bytes((g,m));return st

    def generate(self,st,header,q):
        info=a.u32(self.source,a.wild.WILD_HEADERS+header*20+4)
        st=bytearray(st);put32(st,RNG,SEEDS[q])
        out=self.call(st,0x08000000+a.release.previous.HOOK_OFFSET,{0:info,1:0,2:0})
        self.assertEqual(u32(out,0x20),1);facts=enemy(out);self.assertTrue(facts['valid'])
        return facts

    def test_cosmog_threshold_and_everstone_day_and_night(self):
        for minute in (600,1320):
            for level,want in ((42,0),(43,790),(44,790),(100,790)):
                got=self.evolution(species=789,level=level,minute=minute);self.assertEqual(got,want)
                self.observations.append(dict(probe='evolution',source=789,level=level,minute=minute,item=0,target=got))
            self.assertEqual(self.evolution(species=789,level=43,minute=minute,item=195),0)
            self.observations.append(dict(probe='evolution',source=789,level=43,minute=minute,item=195,target=0))

    def test_cosmoem_level_priority_not_time_branch_and_everstone(self):
        for minute in (600,1320):
            for level,want in ((52,0),(53,791),(54,792),(55,792),(100,792)):
                got=self.evolution(species=790,level=level,minute=minute);self.assertEqual(got,want)
                self.observations.append(dict(probe='evolution',source=790,level=level,minute=minute,item=0,target=got))
            self.assertEqual(self.evolution(species=790,level=54,minute=minute,item=195),0)
            self.observations.append(dict(probe='evolution',source=790,level=54,minute=minute,item=195,target=0))

    def test_tanoby_flag_gate_and_cresselia_native_generation(self):
        table=next(t for t in a.wild.parse_tables(self.source,a.wild.load_maps(),a.wild.load_species())
                   if (t.map.group,t.map.number,t.kind)==(2,30,'land'))
        for minute in (600,1320):
            st=self.state(2,30,minute)
            locked=self.call(st,0x0808EB60,{0:0x849}) # FlagClear, verified actual native routine
            self.assertEqual(u32(self.call(locked,0x08164160),0x20),0xFFFF)
            unlocked=self.call(locked,0x0808EB38,{0:0x849}) # FlagSet
            header=u32(self.call(unlocked,0x08164160),0x20);self.assertEqual(header,table.map.index)
            facts=self.generate(unlocked,header,20)
            self.assertEqual((facts['species'],facts['level']),(488,25))
            self.observations.append(dict(probe='tanoby_header_and_generation',minute=minute,
                flag='0849',locked_header=65535,unlocked_header=header,species=facts['species'],level=facts['level'],quantile=20))

    def test_altering_all_variants_and_invalid_fallback_type_null_only_at_seven(self):
        for minute in (600,1320):
            for variant in (*range(9),9,65535):
                st=self.call(self.state(1,122,minute),0x0808EA14,{0:0x4024,1:variant})
                header=u32(self.call(st,0x08164160),0x20)
                self.assertEqual(header,123+(variant if variant<=8 else 0))
                facts=self.generate(st,header,40)
                info=a.pointer(self.source,a.wild.WILD_HEADERS+header*20+4)
                slot=a.pointer(self.source,info+4)+2*4;lo,hi,want=struct.unpack_from('<BBH',self.source,slot)
                self.assertEqual(facts['species'],want);self.assertTrue(lo<=facts['level']<=hi)
                self.assertEqual(facts['species']==772,variant==7)
                self.observations.append(dict(probe='altering_header_and_generation',minute=minute,
                    variable='4024',value=variant,header=header,species=facts['species'],level=facts['level'],quantile=40))
