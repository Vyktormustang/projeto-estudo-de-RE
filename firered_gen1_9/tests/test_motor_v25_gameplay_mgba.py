"""Four live gameplay flows and native v24 -> v25 -> v24 -> v25 flash.
No states cross ROM versions. Only newly generated, synthetic 128 KiB flash.
"""
import os,unittest
from pathlib import Path
import test_motor_v21_gameplay_mgba as prior
import test_motor_v25_mgba as current
import test_motor_v24_mgba as clock
from mgba_treino_harness import Emulator,mon,offset
from test_eventos_fixos_mgba import route_entry_fixture
from test_estojo_expandido_mgba import add,get,save1
from test_golpes_gen9_integracao import save_game,load_game
from test_motor_v19_mgba import set_time,elapsed

class MotorV25GameplayTests(prior.MotorV21GameplayTests):
    __unittest_skip__=not bool(current.ROM and current.CORE)
    setUpClass=classmethod(current.prepare);tearDownClass=classmethod(current.finish)

    def walking_encounter(self,minute,species,*,ball_item=None):
        st=super().walking_encounter(minute,species,ball_item=ball_item)
        self.assertFalse(current.has_hud(st),'HUD must be absent from an actual battle')
        return st

    @unittest.skipUnless(os.environ.get('MOTOR_V25_BASE'),'set MOTOR_V25_BASE')
    def test_native_v24_v25_flash_pre_and_postcap_and_downgrade_roundtrip(self):
        base=Path(os.environ['MOTOR_V25_BASE'])
        self.assertEqual(current.p.digest(base.read_bytes()),current.p.BASE_SHA256)
        def switch(rom):
            self.f.close();type(self).f=self.f=Emulator(rom,Path(current.CORE),self.dir)
        for capped in (False,True):
            with self.subTest(capped=capped):
                switch(base)
                st=route_entry_fixture(self.f)
                for item,qty in ((4,7),(375,17),(603,999)):st=add(self.f,st,item,qty)
                st=clock.saturated(st,1320,17) if capped else set_time(st,1320)
                self.f.restore(bytes(st));flash=save_game(self.f)
                self.assertEqual(len(flash),131072)
                identity=mon(st);location=prior.location(st)
                for rom,want_hud in ((self.rom,True),(base,False),(self.rom,True)):
                    switch(rom);loaded=load_game(self.f,flash);self.f.run(5);loaded=self.f.state()
                    self.assertEqual(current.has_hud(loaded),want_hud)
                    self.assertEqual(mon(loaded),identity)
                    self.assertEqual(prior.location(loaded),location)
                    for item,qty in ((4,7),(375,17),(603,999)):
                        self.assertEqual(get(self.f,loaded,item),qty)
                    # ABI inventory queries pause at a sentinel: restore the
                    # real live state before subsequent buttons/native save.
                    self.f.restore(loaded)
                    if capped:
                        self.assertEqual(elapsed(loaded),3599999)
                        self.assertTrue(1300<=clock.record(loaded)[0]<1440)
                        at=clock.progress(loaded);self.f.run(120)
                        self.assertEqual((clock.progress(self.f.state())-at)%86400,120)
                    else:self.assertTrue(840<=elapsed(loaded)<960)
                    flash=save_game(self.f);self.assertEqual(len(flash),131072)
        self.assertEqual(current.p.digest(base.read_bytes()),current.p.BASE_SHA256)
