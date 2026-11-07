"""Shared T9X1 storage: existing bag contracts with an ACTIVE capped clock."""
import unittest
from pathlib import Path
import test_motor_v24_mgba as current
import test_estojo_expandido_mgba as bag
from test_golpes_gen9_integracao import save_game,load_game
from mgba_treino_harness import Emulator,mon


def prepare(cls):
    current.prepare(cls)
    cls.fixture=bytes(current.saturated(cls.fixture,1320))


@unittest.skipUnless(current.ROM and current.CORE,'set MOTOR_V24_ROM and MGBA_CORE')
class MotorV24BagTests(unittest.TestCase):
    expected_taught_tm_quantity=0  # Current SV policy: consume one TM; not old estojo-only policy.
    setUpClass=classmethod(prepare)
    tearDownClass=classmethod(current.finish)
    test_all_58_legacy_and_229_modern=bag.EstojoMGBATests.test_limite_58_removido_58_legadas_mais_229_modernas
    test_quantity_limits_and_neighbors=bag.EstojoMGBATests.test_quantidades_limites_e_operacoes_sem_interferir_nas_vizinhas
    test_live_pages_teaching_and_help_option=bag.EstojoMGBATests.test_paginas_ensino_e_restauracao_da_opcao_ajuda
    test_native_bag_backup_preserves_extension=bag.EstojoMGBATests.test_backup_da_bolsa_para_link_preserva_extensao_quando_nao_modificada

    def setUp(self):self.f.restore(self.fixture)
    def tearDown(self):current.record(self.f.state())

    def test_all_287_tm_hm_counts_and_clock_survive_native_flash(self):
        st=self.fixture
        for item in range(289,347):st=bag.add(self.f,st,item)
        for item in range(375,604):st=bag.add(self.f,st,item,(item*7)%997+1)
        self.assertEqual(current.record(st),(1320,0))
        self.f.restore(st);flash=save_game(self.f)
        before=bag.extension(st)[:291];identity=mon(st)
        self.f.close();type(self).f=self.f=Emulator(self.rom,Path(current.CORE),self.dir)
        out=load_game(self.f,flash)
        self.assertEqual(len(flash),131072)
        self.assertEqual(bag.extension(out)[:291],before)
        self.assertEqual(mon(out),identity)
        self.assertTrue(1320<=current.record(out)[0]<1380)
        for item in range(289,347):self.assertEqual(bag.get(self.f,out,item),1,item)
        for item in range(375,604):self.assertEqual(bag.get(self.f,out,item),(item*7)%997+1,item)
