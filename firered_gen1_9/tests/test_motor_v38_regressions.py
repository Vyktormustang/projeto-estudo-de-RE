"""Selected prior contracts on SHA-locked v38, fresh synthetic fixtures.
Clock ABI-only probes use the preserved v24 vector; LIVE main-loop flows use
the preserved v26 wrapper. The wrapper/save-byte equivalence has its own HUD test.
Old v23 cross-version cases are replaced by v37/v38 native-flash coverage.
"""
import unittest
from pathlib import Path
import test_motor_v38_hud_mgba as current
import test_motor_v24_mgba as previous
import test_motor_v24_regressions as battle
import test_motor_v24_estojo_mgba as bag
from test_golpes_gen9_mgba import invoke

ENABLED=bool(current.ROM and current.CORE)

class MotorV38ClockTests(previous.MotorV24ClockTests):
    __unittest_skip__=not ENABLED
    setUpClass=classmethod(current.prepare);tearDownClass=classmethod(current.finish)
    def test_postcap_real_battle_eevee_evolutions_day_and_night(self):
        evolution_flow(self,capped=True)
    test_postcap_all_sixteen_encounter_maps_and_phase_boundaries=None
    test_native_flash_v23_saturated_to_v24_and_v24_roundtrip=None
    test_native_v24_v23_v24_downgrade_preserves_but_does_not_advance_record=None
    def call(self,state,entry,regs=None):
        if entry==previous.UPDATE:entry=previous.p.ENTRY_UPDATE
        return invoke(self.f,state,entry&~1,regs or {})

class MotorV38PriorClockTests(previous.MotorV24ClockRegressionTests):
    def test_real_battle_evolution_day_night_and_clock_progress(self):
        evolution_flow(self,capped=False)
    __unittest_skip__=not ENABLED
    setUpClass=classmethod(current.prepare);tearDownClass=classmethod(current.finish)

def prepare_singles(cls):
    current.prepare(cls);cls.battle_fixture=cls._make_singles_fixture()

class MotorV38SoundproofTests(battle.MotorV24SoundproofTests):
    __unittest_skip__=not ENABLED
    setUpClass=classmethod(prepare_singles);tearDownClass=classmethod(current.finish)

class MotorV38ExperienceTests(battle.MotorV24ExperienceTests):
    __unittest_skip__=not ENABLED
    rom_path=current.ROM;expected_hash=current.release.OUTPUT_SHA256

    def test_batalha_natural_sem_editar_hp_atributos_nivel_ou_exp(self):
        # A smoke test of victory must not assume every natural foe is
        # beatable by an untouched level-5 starter. Vary ONLY initial waiting
        # frames, then walk normally; select a level <=3 foe neutral to Tackle.
        # No RNG, species, HP, stats, level, moves or EXP are edited.
        from test_golpes_gen9_mgba import moves
        from test_eventos_fixos_mgba import enemy
        from test_atualizacoes_gen9_mgba import FOE_BATTLE
        from battle_fixture_helpers import party_experience,in_battle,main_callback2,finish_victory
        from mgba_treino_harness import mon,mon_facts
        found=False
        for delay in range(0,180,5):
            self.f.restore(self.fixture);self.f.run(delay)
            st=self._enter_wild_encounter(bytearray(self.f.state()))
            types=st[FOE_BATTLE+0x22:FOE_BATTLE+0x24]
            if enemy(st)['level']<=3 and not any(t in (5,7,8) for t in types):
                found=True;break
        self.assertTrue(found,'No suitable natural encounter within delay budget')
        self.assertEqual(moves(st)[0],33)
        before=party_experience(st)
        self.assertFalse(current.has_hud(st))
        for _ in range(12):
            for button in ('UP','LEFT','A','UP','LEFT','A'):
                self.f.pulse(button,25)
            self.f.run(1100)
            for _ in range(8):self.f.pulse('B',90)
            if not in_battle(self.f.state()):break
        out=finish_victory(self.f,main_callback2(self.fixture))
        self.assertGreater(party_experience(out),before)
        self.assertTrue(mon_facts(mon(out))['valid'])
        self.assertGreater(mon_facts(mon(out))['hp'],0)

def prepare_bag(cls):
    current.prepare(cls)
    st=previous.saturated(cls.fixture,1320)
    import struct
    at=previous.offset(previous.bag.save1(st)+current.p.PREFERENCE_OFFSET)
    struct.pack_into('<II',st,at,current.p.PREFERENCE_MAGIC,current.p.HIDDEN)
    cls.fixture=bytes(st)

class MotorV38BagTests(bag.MotorV24BagTests):
    def tearDown(self):
        super().tearDown()
        st=self.f.state();at=previous.offset(previous.bag.save1(st)+current.p.PREFERENCE_OFFSET)
        import struct
        self.assertEqual(struct.unpack_from('<II',st,at),(current.p.PREFERENCE_MAGIC,current.p.HIDDEN))
    __unittest_skip__=not ENABLED
    setUpClass=classmethod(prepare_bag);tearDownClass=classmethod(current.finish)


def evolution_flow(self,*,capped):
    from test_golpes_gen9_mgba import seed_mon
    from test_golpes_gen9_integracao import GolpesIntegracaoMGBATests,set_exp_and_test_stats
    from mgba_treino_harness import mon,mon_facts
    from battle_fixture_helpers import in_battle,main_callback2
    for minute,target in ((600,196),(1320,197)):
        with self.subTest(minute=minute,target=target,capped=capped):
            # Controlled synthetic Eevee, not a learnset-legality claim.
            # Bite is Dark: it can hit the naturally selected Ghost foe,
            # unlike Tackle, and cannot trigger Sylveon's Fairy-move priority.
            st=seed_mon(self.fixture,133,10,(44,45,0,0));set_exp_and_test_stats(st,1330)
            st=previous.clock.set_friendship_item(st,255)
            st=previous.saturated(st,minute) if capped else previous.clock.set_time(st,minute)
            self.f.restore(bytes(st));GolpesIntegracaoMGBATests.enter_route_battle(self,self.f)
            before=self.f.state();self.assertTrue(in_battle(before))
            self.assertFalse(current.has_hud(before));self.f.run(120)
            if capped:self.assertEqual((previous.progress(self.f.state())-previous.progress(before))%86400,120)
            else:self.assertEqual(previous.clock.elapsed(self.f.state())-previous.clock.elapsed(before),2)
            for _ in range(150):
                self.f.pulse('A',60);out=self.f.state()
                if (mon_facts(mon(out))['species']==target and not in_battle(out)
                    and main_callback2(out)==main_callback2(st)):break
            facts=mon_facts(mon(out))
            self.assertEqual((facts['species'],facts['level'],facts['valid']),(target,11,True))
            self.assertFalse(in_battle(out));self.assertEqual(main_callback2(out),main_callback2(st))
            if capped:self.assertEqual(previous.clock.elapsed(out),previous.MAX)
