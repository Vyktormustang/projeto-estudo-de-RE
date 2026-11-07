"""Actual-ROM graph contracts; native route execution is tested separately."""
import os,unittest
from pathlib import Path
from scripts import auditar_trajetos_v42 as a,motor_v42 as p
ROM=os.environ.get('TRAJETOS_V42_ROM');BASE=os.environ.get('TRAJETOS_V42_BASE')

class PathAlgorithmTests(unittest.TestCase):
    def test_path_respects_collision_and_unselected_warps(self):
        m=a.Map((0,0),'synthetic',3,3,0,(0x3000,)*9,())
        self.assertEqual(len(a.cell_route(m,(0,0),(2,2))),4)
        m.cells=(0x3000,0x3400,0x3000)*3
        with self.assertRaises(ValueError):a.cell_route(m,(0,0),(2,2))
        m.cells=(0x3000,)*9;m.warps=(a.Warp(0,1,0,3,0,(0,0),0x61),)
        self.assertEqual(len(a.cell_route(m,(0,0),(2,0))),4)
        with self.assertRaises(ValueError):a.cell_route(m,(0,0),(2,0),blocked={(0,1)})

@unittest.skipUnless(ROM and BASE,'set TRAJETOS_V42_ROM and TRAJETOS_V42_BASE')
class IslandTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.b=Path(ROM).read_bytes();cls.maps=a.world(cls.b)
    def test_reciprocal_graph_and_complete_routes(self):
        report=a.audit(self.b);self.assertEqual(len(report['maps']),24)
        self.assertEqual([x['transitions'] for x in report['journeys']],[9,17,16,1,1])
        visited=set()
        for x in report['journeys']:
            for key,warp in a.map_route(self.maps,tuple(x['start']),tuple(x['goal'])):visited.update((key,warp.destination))
        self.assertEqual(visited,set(self.maps))
    def test_each_pair_of_exits_has_collision_free_path(self):
        for m in self.maps.values():
            for first in m.warps:
                for last in m.warps:
                    for _,xy in a.cell_route(m,first.xy,last.xy):self.assertTrue(m.walkable(xy))
    def test_v41_geometry_unchanged_and_wrong_input_rejected(self):
        old=Path(BASE).read_bytes();self.assertEqual(p.digest(old),p.BASE_SHA256)
        self.assertEqual(a.world(old,strict=False),self.maps)
        for data in (b'',old,self.b[:-1]):
            with self.assertRaises(ValueError):a.world(data)
