"""Saída v18 exata: correções positivas + controles da auditoria v17."""
import os
import tempfile
from pathlib import Path
import test_motor_v17_blocked_pivots_mgba as previous
from scripts import motor_v18 as patch

old,h,ending,doubles=previous.old,previous.h,previous.ending,previous.doubles
ROM=os.environ.get('MOTOR_V18_ROM')
CORE=os.environ.get('MGBA_CORE')
ENABLED=bool(ROM and CORE)


def prepare(cls):
    cls.rom=Path(ROM)
    if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise ValueError('ROM não é v18 exato')
    cls.temp=tempfile.TemporaryDirectory()
    cls.f=old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
    cls.fixture=old.route_entry_fixture(cls.f)
    cls.doubles_fixture=cls._make_doubles_fixture()


def finish(cls):
    cls.f.close();cls.temp.cleanup()
    if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise AssertionError('ROM alterada')


class MotorV18BlockedPivotsTests(previous.MotorV17BlockedPivotsTests):
    __unittest_skip__=not ENABLED
    __unittest_skip_why__='defina MOTOR_V18_ROM e MGBA_CORE'
    setUpClass=classmethod(prepare)
    tearDownClass=classmethod(finish)
    test_defeito_v17_volt_switch_ground_troca_apesar_da_imunidade=None
    test_defeito_v17_parting_ignora_soundproof=None

    def setup_case(self,move,actor,mode,order):
        self.native_soundproof=(mode=='soundproof')
        return super().setup_case(move,actor,mode,order)

    def watch_actor(self,st,destination):
        # Soundproof cancela antes de HITMARKER_OBEYS. O encerramento nativo
        # grava MOVE_UNAVAILABLE (FFFF), inclusive em Growl/Hyper Voice/Eerie
        # na v17. Não é o zero de uma troca, nem prova de lastMove moderno.
        if destination==571 and self.native_soundproof:destination=0xFFFF
        super().watch_actor(st,destination)

    def corrected(self,move,actor,mode,four):
        order=((2,3,4,1) if actor==0 else (3,1,4,2)) if four else ((2,1) if actor==0 else (1,2))
        initial,before=self.setup_case(move,actor,mode,order)
        out=self.attempt(before)
        self.assertEqual(previous.main_callback2(out),self.battle_callback,self.seen)
        self.assertIn('vai fazer?',h.text(out),self.seen)
        self.assertTrue(any(('afeta' if mode=='ground' else 'SOUNDPROOF') in s for s in self.seen),self.seen)
        self.assertGreater(self.actor_frames,0);self.assertTrue(self.reached_history)
        self.consistent(out);self.stable_field(out,order)
        self.assertEqual(doubles.indexes(out),doubles.indexes(before))
        self.assertEqual(self.transitions,[]);self.assertEqual(self.losses,[])
        self.assertEqual(self.details,{2:[],3:[]})
        for off in (0x19,0x1C):self.assertEqual(out[old.bank_off(1)+off],6)
        if mode=='soundproof':self.assertEqual(out[old.bank_off(1)+0x20],43)
        self.check_pp(before,out,[(actor,0),(self.ally,3),(1,1),(3,1)])
        self.identities_and_exp(initial,out)
        self.assertEqual(old.u16(out,h.LAST_MOVES+2*actor),0xFFFF if mode=='soundproof' else move)
        self.assertEqual(old.u16(out,h.LAST_MOVES+2*self.ally),150)
        self.assertEqual(out[old.bank_off(actor)+0x19],8)
        for slot in (0,1):self.assertEqual(ending.hp(out,0,slot),4000)
        for slot in (2,3):self.assertEqual(ending.hp(out,0,slot),400)
        # Sem troca não há poison residual: ambos os ativos já estavam em campo.
        self.followup(initial,out,order,1)

    def test_volt_switch_ground_nao_troca_nem_aplica_hazards(self):
        for actor,four in ((0,False),(2,False),(0,True)):
            with self.subTest(actor=actor,four=four):self.corrected(517,actor,'ground',four)

    def test_soundproof_bloqueia_parting_antes_dos_atributos(self):
        for actor,four in ((0,False),(2,False),(2,True)):
            with self.subTest(actor=actor,four=four):self.corrected(571,actor,'soundproof',four)
