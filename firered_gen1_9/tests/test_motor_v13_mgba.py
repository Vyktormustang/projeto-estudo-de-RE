"""Eerie Spell/Substitute/Shield Dust em mGBA; apenas estados sintéticos."""
from __future__ import annotations
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v12_mgba as v12
from scripts import motor_v13 as patch
from battle_fixture_helpers import finish_victory, main_callback2, party_experience

old = v12.old
v11 = v12.v11
BASE = os.environ.get('MOTOR_V13_BASE')
ROM = os.environ.get('MOTOR_V13_ROM')
CORE = os.environ.get('MGBA_CORE')
SUB_HP = v12.SUB_HP
MARKER = old.offset(0x0202160C)


def snapshot(st):
    return (old.u16(st,old.FOE_BATTLE+0x2A),v12.pp(st),st[SUB_HP],
            bool(old.u32(st,old.FOE_BATTLE+0x54)&0x01000000))


@unittest.skipUnless(BASE and ROM and CORE, 'defina MOTOR_V13_BASE, MOTOR_V13_ROM e MGBA_CORE')
class MotorV13MGBATests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state
    _run_turn = v12.MotorV12MGBATests._run_turn
    eerie_state = v11.MotorV11MGBATests.eerie_state
    soundproof_state = v12.MotorV12MGBATests.soundproof_state

    @classmethod
    def setUpClass(cls):
        base, rom = Path(BASE),Path(ROM)
        if rom.read_bytes() != patch.build(base.read_bytes()):
            raise ValueError('ROM diverge do build determinístico v13')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(base,Path(CORE),Path(cls.temp.name)/'base')
        try:
            cls.fixture = old.route_entry_fixture(cls.f)
            cls.battle_fixture = cls._make_singles_fixture()
            test = cls()
            cls.baseline = {}
            for sub,ability in ((1,4),(200,4),(0,19)):
                out,_ = test._run_turn(test.interaction_state(sub=sub,ability=ability))
                cls.baseline[sub,ability] = snapshot(out)
        finally:
            cls.f.close()
        cls.f = old.Emulator(rom,Path(CORE),Path(cls.temp.name)/'v13')
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    def interaction_state(self, *, sub=0, ability=4):
        st = bytearray(self.eerie_state(status2=0x01000000 if sub else 0))
        st[SUB_HP] = sub
        old.put16(st,old.FOE_BATTLE+0x20,ability)
        return bytes(st)

    def test_defeitos_reproduzidos_na_base_v12_com_turno_completo(self):
        hp,pp,sub,bit = self.baseline[1,4]
        self.assertEqual((hp,pp,sub,bit),(480,[10]*4,0,False))
        hp,pp,sub,bit = self.baseline[200,4]
        self.assertEqual((hp,pp,bit),(480,[10]*4,True))
        self.assertLess(sub,200)
        hp,pp,sub,bit = self.baseline[0,19]
        self.assertLess(hp,480)
        self.assertEqual(pp,[10,10,7,10])

    def test_substitute_forte_e_fragil_sao_preservados_com_dano_e_dreno_no_alvo(self):
        for sub in (1,200):
            with self.subTest(sub=sub):
                st = self.interaction_state(sub=sub)
                out,seen = self._run_turn(st)
                hp,pp,hp_sub,bit = snapshot(out)
                self.assertLess(hp,480)
                self.assertEqual((pp,hp_sub,bit),([10,10,7,10],sub,True))
                self.assertEqual(v11.party_pp(out,2),7)
                self.assertEqual(old.u16(out,old.offset(old.ENEMY_PARTY_ADDR)+86),hp)
                self.assertEqual(old.u32(out,MARKER)&0x100,0)
                self.assertFalse(any('SUBSTITUTO recebeu' in s for s in seen),seen)

    def test_shield_dust_bloqueia_somente_dreno_com_e_sem_substitute(self):
        for sub in (0,1,200):
            with self.subTest(sub=sub):
                st = self.interaction_state(sub=sub,ability=19)
                party_before = [v11.party_pp(st,i) for i in range(4)]
                out,_ = self._run_turn(st)
                hp,pp,hp_sub,bit = snapshot(out)
                self.assertLess(hp,480)
                self.assertEqual((pp,hp_sub,bit),([10]*4,sub,bool(sub)))
                self.assertEqual([v11.party_pp(out,i) for i in range(4)],party_before)
                self.assertEqual(out[old.PLAYER_BATTLE+0x25],19)

    def test_shield_dust_suprimido_nao_bloqueia_dreno(self):
        st = bytearray(self.interaction_state(sub=200,ability=19))
        # Bit de supressão já usado pelos motores v9/v10, não habilidade nova.
        old.put32(st,old.offset(old.STATUSES3_ADDR)+4,0x00010000)
        out,_ = self._run_turn(bytes(st))
        self.assertLess(old.u16(out,old.FOE_BATTLE+0x2A),480)
        self.assertEqual(v12.pp(out),[10,10,7,10])
        self.assertEqual(out[SUB_HP],200)

    def test_bypass_nao_vaza_para_tackle_no_turno_seguinte(self):
        st = bytearray(self.interaction_state(sub=200))
        old.put16(st,old.PLAYER_BATTLE+0x0E,33)
        after_eerie,_ = self._run_turn(bytes(st))
        self.assertEqual(after_eerie[SUB_HP],200)
        after_tackle,_ = self._run_turn(after_eerie,slot=1)
        self.assertEqual(old.u16(after_tackle,old.FOE_BATTLE+0x2A),old.u16(after_eerie,old.FOE_BATTLE+0x2A))
        self.assertLess(after_tackle[SUB_HP],200)
        self.assertEqual(v12.pp(after_tackle),v12.pp(after_eerie))
        self.assertEqual(old.u32(after_tackle,MARKER)&0x100,0)

    def test_tackle_do_oponente_no_mesmo_turno_nao_herda_bypass(self):
        st = bytearray(self._duel_state(720,foe_move=33))
        for bank in (0,1):
            old.put32(st,old.bank_off(bank)+0x54,0x01000000)
            st[old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28*bank+10] = 200
        out,_ = self._run_turn(bytes(st))
        self.assertLess(old.u16(out,old.FOE_BATTLE+0x2A),480)
        self.assertEqual(out[SUB_HP],200)
        self.assertEqual(old.u16(out,old.PLAYER_BATTLE+0x2A),160)
        self.assertLess(out[old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+10],200)
        self.assertEqual(old.u32(out,MARKER)&0x100,0)

    def test_substitute_criado_naturalmente_no_mesmo_turno(self):
        # Alvo mais rápido usa Substitute pela interface normal, sem injetar
        # status2/substituteHP nem gLastMoves. Custo nativo: 480/4 = 120 HP.
        st = self._duel_state(720,foe_move=164,f_speed=400)
        out,seen = self._run_turn(st)
        self.assertLess(old.u16(out,old.FOE_BATTLE+0x2A),360,seen)
        self.assertEqual(out[SUB_HP],120)
        self.assertTrue(old.u32(out,old.FOE_BATTLE+0x54)&0x01000000)
        self.assertEqual(old.u16(out,old.offset(v11.LAST_MOVES)+2),164)
        self.assertEqual(sum(v12.pp(out)),156)

    def test_ko_atras_de_substitute_sem_dreno_com_exp_e_retorno_ao_mapa(self):
        st = bytearray(self.interaction_state(sub=200))
        old.put16(st,old.FOE_BATTLE+0x2A,1)
        old.put16(st,old.offset(old.ENEMY_PARTY_ADDR)+86,1)
        before_pp = [v11.party_pp(st,s) for s in range(4)]
        before_exp = party_experience(st)
        # EXP da fixture agora é coerente com nível 10 (560, não 1).
        self.assertEqual(before_exp,560)
        old.MotorV10MGBATests._run_turn(self,bytes(st))
        out = finish_victory(self.f,main_callback2(self.fixture))
        self.assertEqual(old.u16(out,old.offset(old.ENEMY_PARTY_ADDR)+86),0)
        self.assertEqual([v11.party_pp(out,s) for s in range(4)],before_pp)
        self.assertEqual(party_experience(out),before_exp+21)
        self.assertEqual(old.u32(out,MARKER)&0x100,0)

    def test_endure_preserva_alvo_a_1hp_mesmo_com_substitute(self):
        st = bytearray(self._duel_state(720,foe_move=203,f_hp=1))
        old.put32(st,old.FOE_BATTLE+0x54,0x01000000)
        st[SUB_HP] = 200
        out,seen = self._run_turn(bytes(st))
        self.assertEqual(old.u16(out,old.FOE_BATTLE+0x2A),1,seen)
        self.assertEqual(out[SUB_HP],200)
        self.assertEqual(sum(v12.pp(out)),156)  # Endure próprio + dreno 3

    def test_protect_e_imunidade_preservam_substitute_sem_dano_ou_dreno(self):
        for foe_move,types in ((182,(0,0)),(150,(17,17))):
            with self.subTest(foe_move=foe_move):
                st = bytearray(self._duel_state(720,foe_move=foe_move,f_types=types))
                old.put32(st,old.FOE_BATTLE+0x54,0x01000000)
                st[SUB_HP] = 200
                old.put16(st,old.offset(v11.LAST_MOVES)+2,foe_move)
                out,_ = self._run_turn(bytes(st))
                self.assertEqual(old.u16(out,old.FOE_BATTLE+0x2A),480)
                self.assertEqual(out[SUB_HP],200)
                self.assertEqual(sum(v12.pp(out)),159)
                self.assertEqual(old.u32(out,MARKER)&0x100,0)

    # Asserções positivas v11/v12; não herdar os testes de defeitos agora corrigidos.
    test_soundproof_bloqueia_dano_e_dreno_mas_consumo_proprio_permanece = v12.MotorV12MGBATests.test_soundproof_bloqueia_dano_e_dreno_mas_consumo_proprio_permanece
    test_controles_sem_soundproof_e_golpe_nao_sonoro = v12.MotorV12MGBATests.test_controles_sem_soundproof_e_golpe_nao_sonoro
    test_soundproof_preserva_substitute_forte_e_fragil = v12.MotorV12MGBATests.test_soundproof_preserva_substitute_forte_e_fragil
    test_growl_e_hyper_voice_nativos_continuam_bloqueados = v12.MotorV12MGBATests.test_growl_e_hyper_voice_nativos_continuam_bloqueados
    test_turno_seguinte_nao_herda_bloqueio = v12.MotorV12MGBATests.test_turno_seguinte_nao_herda_bloqueio
    test_ultimo_golpe_slot2_e_checksum_equipe = v11.MotorV11MGBATests.test_ultimo_golpe_slot2_e_checksum_equipe
    test_sem_fallback_e_sem_underflow = v11.MotorV11MGBATests.test_sem_fallback_e_sem_underflow
    test_transform_e_mimic_nao_alteram_pp_originais = v11.MotorV11MGBATests.test_transform_e_mimic_nao_alteram_pp_originais
    test_protect_e_imunidade_nao_drenam = v11.MotorV11MGBATests.test_protect_e_imunidade_nao_drenam
    test_ultimo_golpe_registrado_naturalmente = v11.MotorV11MGBATests.test_ultimo_golpe_registrado_naturalmente
    test_mighty_cleave_ja_atravessa_protect_e_tackle_nao = v11.MotorV11MGBATests.test_mighty_cleave_ja_atravessa_protect_e_tackle_nao


class MotorV13InheritedRegressionTests(old.MotorV10MGBATests):
    """Seis famílias v10 em fixtures novas da ROM v13."""
    __unittest_skip__ = not bool(BASE and ROM and CORE)
    __unittest_skip_why__ = 'defina MOTOR_V13_BASE, MOTOR_V13_ROM e MGBA_CORE'

    @classmethod
    def setUpClass(cls):
        cls.rom,cls.base,cls.core = Path(ROM),Path(BASE),Path(CORE)
        if cls.rom.read_bytes() != patch.build(cls.base.read_bytes()):
            raise ValueError('ROM v13 divergente')
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        cls.f = old.Emulator(cls.rom,cls.core,cls.dir)
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()
        cls.two_party_fixture = cls._make_two_party_singles_fixture()
        cls.two_enemy_fixture = cls._make_two_enemy_trainer_like_fixture()
        cls.doubles_fixture = cls._make_doubles_fixture()

    def test_eerie_duplas_selecao_bancos1_3_shield_dust_soundproof_e_checksum(self):
        for target,ability in ((1,4),(3,4),(3,19),(3,43)):
            with self.subTest(target=target,ability=ability):
                st = bytearray(self._duel_state(720,base_state=self.doubles_fixture,f_status1=7))
                for bank in range(4):
                    b = old.bank_off(bank)
                    party = old.ENEMY_PARTY_ADDR if bank%2 else old.PARTY
                    idx = old.u16(st,old.offset(old.PARTY_INDEXES_ADDR)+2*bank)
                    hp = 480 if bank%2 else 160
                    for s in range(4):
                        move = (45 if s==2 else 150) if bank%2 else 150
                        old.put16(st,b+12+2*s,move)
                        st[b+0x25+s] = 10 if bank%2 else 40
                    for s in range(1,8):
                        st[b+0x18+s] = 6
                    old.put16(st,b+0x20,ability if bank==target else 4)
                    st[b+0x22] = st[b+0x23] = 0
                    old.put16(st,b+0x30,0)
                    old.put16(st,b+0x2A,hp); old.put16(st,b+0x2E,hp)
                    old.put16(st,old.offset(party)+idx*100+86,hp)
                    old.put16(st,old.offset(party)+idx*100+88,hp)
                    status = 7 if bank%2 else 0
                    old.put32(st,b+0x50,status)
                    old.put32(st,old.offset(party)+idx*100+80,status)
                    old.put32(st,b+0x54,0x01000000 if bank%2 else 0)
                    st[old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28*bank+10] = 200 if bank%2 else 0
                    old.put16(st,old.offset(v11.LAST_MOVES)+2*bank,45 if bank%2 else 0)
                old.put16(st,old.PLAYER_BATTLE+12,720)
                self.f.restore(bytes(st))
                self.f.pulse('A',25)  # Fight b0
                self.f.pulse('A',25)  # Eerie Spell
                if target==3:
                    # LEFT muda do inimigo b1 para b3; RIGHT escolheria aliado b2.
                    self.f.pulse('LEFT',15)
                self.f.pulse('A',25)  # confirma alvo
                self.f.pulse('A',25)  # Fight b2
                self.f.pulse('A',25)  # Splash b2 (sem cursor de alvo)
                self.f.run(1900)
                for _ in range(8):
                    self.f.pulse('B',90)
                out = self.f.state()
                self.assertIn('vai fazer?',v12.text(out))
                self.assertEqual(out[old.PLAYER_BATTLE+0x25],39)
                self.assertEqual(old.u32(out,MARKER)&0x100,0)
                for bank in (0,2):
                    self.assertEqual(old.u16(out,old.bank_off(bank)+0x2A),160)
                for bank in (1,3):
                    b = old.bank_off(bank)
                    hp = old.u16(out,b+0x2A)
                    hit = bank==target and ability!=43
                    drain = hit and ability!=19
                    self.assertEqual(hp<480,hit)
                    self.assertEqual(list(out[b+0x25:b+0x29]),[10,10,7 if drain else 10,10])
                    self.assertEqual(out[old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28*bank+10],200)
                    self.assertTrue(old.u32(out,b+0x54)&0x01000000)
                    idx = old.u16(st,old.offset(old.PARTY_INDEXES_ADDR)+2*bank)
                    pos = old.offset(old.ENEMY_PARTY_ADDR)+100*idx
                    before,order,valid = old.decrypted(st[pos:pos+100])
                    self.assertTrue(valid)
                    after,order2,valid2 = old.decrypted(out[pos:pos+100])
                    self.assertTrue(valid2)
                    expected = list(before[order[1]*12+8:order[1]*12+12])
                    if drain:
                        expected[2] = 7
                    self.assertEqual(list(after[order2[1]*12+8:order2[1]*12+12]),expected)
                    self.assertEqual(old.u16(out,pos+86),hp)
