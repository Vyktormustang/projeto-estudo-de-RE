"""Diagnóstico causal KO/EXP: v12/v13 exatos, estados sintéticos, nenhuma ROM nova.

EXPERIENCE_BASE=/caminho/motor_v12.gba EXPERIENCE_ROM=/caminho/motor_v13.gba
MGBA_CORE=/caminho/mgba_libretro.so. Sem essas variáveis, só testes estruturais.
"""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v10_mgba as old
from test_motor_v12_mgba import text
from mgba_treino_harness import mon, mon_facts
from battle_fixture_helpers import (
    LEVEL10_EXP, LEVEL11_EXP, party_experience, set_party_experience,
    set_level10_starter_test_stats, finish_victory, main_callback2, in_battle,
)
from scripts import motor_v12, motor_v13

BASE = os.environ.get('EXPERIENCE_BASE')
ROM = os.environ.get('EXPERIENCE_ROM')
CORE = os.environ.get('MGBA_CORE')


def empty_mon_state(species=1,level=10):
    # PID=OTID=0: subestruturas GAEM e XOR=0, sem assets de jogo.
    st = bytearray(0x61000)
    pos = old.offset(old.PARTY)
    old.put16(st,pos+32,species)
    old.put16(st,pos+28,species)
    st[pos+84] = level
    return st


class ExperienceFixtureDataTests(unittest.TestCase):
    def test_limites_medium_slow_niveis10_11(self):
        def medium_slow(n):
            return 6*n**3//5-15*n*n+100*n-140
        self.assertEqual((LEVEL10_EXP,LEVEL11_EXP),(medium_slow(10),medium_slow(11)))
        self.assertEqual((LEVEL10_EXP,LEVEL11_EXP),(560,742))

    def test_helper_restrito_e_experiencia_coerente(self):
        for species in (1,4,6):
            st = empty_mon_state(species)
            set_level10_starter_test_stats(st)
            self.assertEqual(party_experience(st),560)
            self.assertTrue(mon_facts(mon(st))['valid'])
        for species,level in ((25,10),(1,9),(1,11)):
            st = empty_mon_state(species,level)
            before = bytes(st)
            with self.assertRaises(ValueError):
                set_level10_starter_test_stats(st)
            self.assertEqual(bytes(st),before)

    def test_intervencao_altera_so_exp_e_checksum(self):
        st = empty_mon_state()
        before = bytes(st)
        set_party_experience(st,560)
        pos = old.offset(old.PARTY)
        allowed = set(range(pos+28,pos+30)) | set(range(pos+36,pos+40))
        changes = {i for i,(a,b) in enumerate(zip(before,st)) if a!=b}
        self.assertTrue(changes)
        self.assertTrue(changes <= allowed)
        self.assertEqual(mon_facts(mon(st))['level'],10)
        self.assertEqual(party_experience(st),560)

    def test_rejeita_checksum_corrompido_e_exp_fora_uint32(self):
        for exp in (-1,0x100000000):
            with self.assertRaises(ValueError):
                set_party_experience(empty_mon_state(),exp)
        st = empty_mon_state();st[old.offset(old.PARTY)+28] ^= 1
        with self.assertRaises(ValueError):
            set_party_experience(st,560)
        with self.assertRaises(ValueError):
            party_experience(st)


class ExperienceCases:
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _make_two_party_singles_fixture = classmethod(old.MotorV10MGBATests._make_two_party_singles_fixture.__func__)
    _make_two_enemy_trainer_like_fixture = classmethod(old.MotorV10MGBATests._make_two_enemy_trainer_like_fixture.__func__)
    _make_doubles_fixture = classmethod(old.MotorV10MGBATests._make_doubles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(cls.rom_path)
        rom_data = cls.rom.read_bytes()
        if motor_v13.digest(rom_data) != cls.expected_hash:
            raise ValueError('ROM não corresponde à versão esperada')
        # Tabela medium-slow identificada na ROM exata; níveis 10 e 11.
        if (old.u32(rom_data,0x69C90C),old.u32(rom_data,0x69C910)) != (560,742):
            raise AssertionError('Limites de EXP da ROM divergentes')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture = old.route_entry_fixture(cls.f)
        if in_battle(cls.fixture) or main_callback2(cls.fixture) != 0x080F172D:
            raise AssertionError('Fixture não chegou ao campo na base identificada')
        cls.battle_fixture = cls._make_singles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()
        if motor_v13.digest(cls.rom.read_bytes()) != cls.expected_hash:
            raise AssertionError('ROM foi alterada durante o teste')

    def ko_state(self,experience):
        # Única variável entre os braços causais: EXP criptografada/checksum.
        st = bytearray(self._duel_state(720,f_hp=1,f_status1=7))
        set_party_experience(st,experience)
        return bytes(st)

    def test_causal_exp1_bloqueia_e_controles559_560_encerram(self):
        for experience in (1,559,560):
            with self.subTest(experience=experience):
                st = self.ko_state(experience)
                old.MotorV10MGBATests._run_turn(self,st)
                if experience == 1:
                    # Reprodução negativa DELIBERADA de estado contraditório.
                    for _ in range(20):
                        self.f.pulse('B',90)
                    out = self.f.state()
                    self.assertTrue(in_battle(out))
                    self.assertEqual(out[old.offset(0x020216C8)],0)
                    self.assertEqual(old.u32(out,old.offset(0x020215B0)),0x08187142)
                    self.assertIn('EXP.',text(out))
                    self.assertEqual(party_experience(out),experience)
                else:
                    out = finish_victory(self.f,main_callback2(self.fixture))
                    self.assertEqual(party_experience(out),experience+21)
                    self.assertEqual(mon_facts(mon(out))['level'],10)

    def test_subida_nivel10_para11_e_retorno_ao_mapa(self):
        st = self.ko_state(741)  # 1 ponto antes do próximo nível
        before = mon_facts(mon(st))
        old.MotorV10MGBATests._run_turn(self,st)
        out = finish_victory(self.f,main_callback2(self.fixture))
        after = mon_facts(mon(out))
        self.assertEqual(party_experience(out),762)
        self.assertEqual(after['level'],11)
        self.assertEqual(before['iv'],after['iv'])
        self.assertTrue(after['valid'])
        self.assertGreater(after['max_hp'],0)
        self.assertGreater(after['hp'],0)
        self.assertLessEqual(after['hp'],after['max_hp'])

    def test_batalha_natural_sem_editar_hp_atributos_nivel_ou_exp(self):
        # Starter e inimigo naturais; não usa seed_mon/_duel_state nem setters.
        st = self._enter_wild_encounter(bytearray(self.fixture))
        before_exp = party_experience(st)
        for _ in range(12):
            old.MotorV10MGBATests._run_turn(self,st)
            for _ in range(8):
                self.f.pulse('B',90)
            st = self.f.state()
            if not in_battle(st):
                break
            self.assertIn('vai fazer?',text(st))
        out = finish_victory(self.f,main_callback2(self.fixture))
        self.assertGreater(party_experience(out),before_exp)
        self.assertTrue(mon_facts(mon(out))['valid'])

    def test_fabricas_singles_duplas_e_reservas_tem_exp_coerente(self):
        fixtures = (
            (self.battle_fixture,((old.PARTY,0),)),
            (self._make_two_party_singles_fixture(),((old.PARTY,0),(old.PARTY,1))),
            (self._make_two_enemy_trainer_like_fixture(),((old.PARTY,0),(old.ENEMY_PARTY_ADDR,1))),
            (self._make_doubles_fixture(),((old.PARTY,0),(old.PARTY,1),(old.ENEMY_PARTY_ADDR,1))),
        )
        for st,slots in fixtures:
            for party,slot in slots:
                pos = old.offset(party)+100*slot
                data = st[pos:pos+100]
                block,order,valid = old.decrypted(data)
                self.assertTrue(valid)
                self.assertEqual(data[84],10)
                self.assertEqual(old.u32(block,order[0]*12+4),560)


@unittest.skipUnless(BASE and CORE,'defina EXPERIENCE_BASE e MGBA_CORE')
class MotorV12ExperienceTests(ExperienceCases,unittest.TestCase):
    rom_path = BASE
    expected_hash = motor_v12.OUTPUT_SHA256


@unittest.skipUnless(ROM and CORE,'defina EXPERIENCE_ROM e MGBA_CORE')
class MotorV13ExperienceTests(ExperienceCases,unittest.TestCase):
    rom_path = ROM
    expected_hash = motor_v13.OUTPUT_SHA256
