"""Eerie Spell: histórico após troca e PP zero durante sequências já iniciadas.

EERIE_HISTORY_ROM=/caminho/motor_v13.gba MGBA_CORE=/caminho/mgba_libretro.so
Somente fixtures sintéticas, SHA exato; não modifica a ROM nem saves pessoais.
"""
from __future__ import annotations
import os
import struct
import tempfile
import unittest
from pathlib import Path
import test_motor_v10_mgba as old
from test_motor_v12_mgba import text
from scripts import motor_v13 as patch
from battle_fixture_helpers import set_level10_starter_test_stats

ROM = os.environ.get('EERIE_HISTORY_ROM')
CORE = os.environ.get('MGBA_CORE')
LAST_MOVES = old.offset(0x020215D4)
MULTIPLETURNS = 0x1000


def party_pp(st,party,slot):
    pos = old.offset(party)+100*slot
    block,order,valid = old.decrypted(st[pos:pos+100])
    if not valid:
        raise ValueError('Checksum de Pokémon sintético inválido')
    return list(block[order[1]*12+8:order[1]*12+12])


def set_moves(st,party,slot,moves,pps):
    """Moveset de teste coerente na equipe; não duplica o mesmo golpe nos slots."""
    if len(moves)!=4 or len(pps)!=4 or not 0<=slot<6:
        raise ValueError('Moveset/slot sintético inválido')
    pos = old.offset(party)+100*slot
    data = bytearray(st[pos:pos+100])
    block,order,valid = old.decrypted(data)
    if not valid:
        raise ValueError('Checksum de Pokémon sintético inválido')
    struct.pack_into('<4H',block,order[1]*12,*moves)
    block[order[1]*12+8:order[1]*12+12] = bytes(pps)
    old.put16(data,28,sum(struct.unpack('<24H',block))&0xFFFF)
    key = old.u32(data,0)^old.u32(data,4)
    for i in range(0,48,4):
        old.put32(data,32+i,old.u32(block,i)^key)
    st[pos:pos+100] = data


@unittest.skipUnless(ROM and CORE,'defina EERIE_HISTORY_ROM e MGBA_CORE')
class EerieHistoryMGBATests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise ValueError('ROM não é motor_v13 exato')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()
        a = bytearray(old.seed_mon(cls.fixture,1,10,(150,45,33,39)))
        b = bytearray(old.seed_mon(cls.fixture,4,10,(45,150,33,39)))
        for st in (a,b):
            set_level10_starter_test_stats(st,stat=200)
        pos = old.offset(old.PARTY)
        a[pos+100:pos+200] = b[pos:pos+100]
        a[old.offset(old.PLAYER_PARTY_COUNT)] = 2
        cls.switch_fixture = cls._enter_wild_encounter(a)

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada durante os testes')

    def finish_turn(self):
        for _ in range(8):
            self.f.pulse('B',90)
        st = self.f.state()
        self.assertIn('vai fazer?',text(st))
        return st

    def turn(self,st):
        _,seen = old.MotorV10MGBATests._run_turn(self,st)
        return self.finish_turn(),seen

    def locked_state(self,move,*,foe_speed=400):
        st = bytearray(self._duel_state(720,foe_move=move,f_speed=foe_speed,
            p_hp=4000,p_max=4000,p_def=500,p_spd_stat=500,f_atk=100,f_spa=100))
        moves,pps = (move,150,45,39),(4,0,0,0)
        for i,mid in enumerate(moves):
            old.put16(st,old.FOE_BATTLE+12+i*2,mid)
            st[old.FOE_BATTLE+0x25+i] = pps[i]
        st[old.FOE_BATTLE+0x1E] = 12  # acurácia alta para o teste de sequência
        set_moves(st,old.ENEMY_PARTY_ADDR,0,moves,pps)
        self.assertEqual(old.u16(st,LAST_MOVES+2),0)
        return bytes(st)

    def assert_pp_zero(self,st):
        self.assertEqual(list(st[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29]),[0]*4)
        self.assertEqual(party_pp(st,old.ENEMY_PARTY_ADDR,0),[0]*4)

    def assert_used(self,seen,move):
        self.assertTrue(any(f'usou\n{move}!' in s for s in seen),seen)

    def test_thrash_continua_com_zero_pp_termina_e_depois_usa_struggle(self):
        st,seen = self.turn(self.locked_state(37))
        self.assert_used(seen,'THRASH')
        self.assert_pp_zero(st)
        self.assertTrue(old.u32(st,old.FOE_BATTLE+0x54)&MULTIPLETURNS)
        hp = old.u16(st,old.PLAYER_BATTLE+0x2A)
        st,seen = self.turn(st)
        self.assert_used(seen,'THRASH')
        self.assert_pp_zero(st)
        self.assertLess(old.u16(st,old.PLAYER_BATTLE+0x2A),hp)
        self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&MULTIPLETURNS)
        self.assertTrue(old.u32(st,old.FOE_BATTLE+0x54)&7)  # confusão ao fim normal
        # Não forçar limpeza da confusão: esperar uma ação válida naturalmente.
        for _ in range(8):
            st,seen = self.turn(st)
            self.assert_pp_zero(st)
            if any('usou\nSTRUGGLE!' in s for s in seen):
                break
        else:
            self.fail('Struggle não observado após término de Thrash/confusão')
        self.assertEqual(old.u16(st,LAST_MOVES+2),165)

    def test_rollout_completa_cinco_turnos_com_zero_pp_e_entao_struggle(self):
        st = self.locked_state(205)
        hp = 4000
        for turn in range(1,6):
            st,seen = self.turn(st)
            self.assert_used(seen,'ROLLOUT')
            self.assert_pp_zero(st)
            self.assertEqual(bool(old.u32(st,old.FOE_BATTLE+0x54)&MULTIPLETURNS),turn<5)
            new_hp = old.u16(st,old.PLAYER_BATTLE+0x2A)
            self.assertLess(new_hp,hp)
            hp = new_hp
        st,seen = self.turn(st)
        self.assert_used(seen,'STRUGGLE')
        self.assert_pp_zero(st)
        self.assertEqual(old.u16(st,LAST_MOVES+2),165)
        # Não afirma fidelidade da progressão de potência de Rollout.

    def test_solarbeam_conclui_carga_apos_pp_zero_e_entao_struggle(self):
        st,seen = self.turn(self.locked_state(76))
        self.assertEqual(old.u16(st,old.PLAYER_BATTLE+0x2A),4000)
        self.assertEqual(old.u16(st,LAST_MOVES+2),76)
        self.assert_pp_zero(st)
        self.assertTrue(old.u32(st,old.FOE_BATTLE+0x54)&MULTIPLETURNS)
        st,seen = self.turn(st)
        self.assert_used(seen,'SOLARBEAM')
        self.assertLess(old.u16(st,old.PLAYER_BATTLE+0x2A),4000)
        self.assert_pp_zero(st)
        self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&MULTIPLETURNS)
        st,seen = self.turn(st)
        self.assert_used(seen,'STRUGGLE')
        self.assert_pp_zero(st)

    def test_eerie_mais_rapido_sem_historico_e_dreno_antes_da_continuacao(self):
        for move,name in ((37,'THRASH'),(205,'ROLLOUT'),(76,'SOLARBEAM')):
            with self.subTest(move=move):
                st,seen = self.turn(self.locked_state(move,foe_speed=40))
                # Eerie age antes de existir histórico: só o PP próprio do alvo.
                self.assertEqual(list(st[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29]),[3,0,0,0])
                self.assertEqual(party_pp(st,old.ENEMY_PARTY_ADDR,0),[3,0,0,0])
                self.assertEqual(old.u16(st,LAST_MOVES+2),move)
                self.assertTrue(old.u32(st,old.FOE_BATTLE+0x54)&MULTIPLETURNS)
                hp = old.u16(st,old.PLAYER_BATTLE+0x2A)
                st,seen = self.turn(st)
                self.assert_pp_zero(st)
                self.assert_used(seen,name)
                self.assertLess(old.u16(st,old.PLAYER_BATTLE+0x2A),hp)
                eerie_idx = next(i for i,s in enumerate(seen) if 'usou\nEERIE SPELL!' in s)
                foe_idx = next(i for i,s in enumerate(seen) if f'usou\n{name}!' in s)
                self.assertLess(eerie_idx,foe_idx)

    def switch_state(self):
        st = bytearray(self._duel_state(150,foe_move=720,base_state=self.switch_fixture))
        sets = (
            (old.PARTY,0,(150,45,33,39),(10,10,10,10),old.PLAYER_BATTLE),
            (old.PARTY,1,(45,150,33,39),(12,11,13,14),None),
            (old.ENEMY_PARTY_ADDR,0,(720,150,45,39),(20,0,0,0),old.FOE_BATTLE),
        )
        for party,slot,moves,pps,bank in sets:
            set_moves(st,party,slot,moves,pps)
            if bank is not None:
                for i,move in enumerate(moves):
                    old.put16(st,bank+12+2*i,move)
                    st[bank+0x25+i] = pps[i]
        self.assertEqual(old.u16(st,LAST_MOVES),0)
        return bytes(st)

    def switch_to_other(self,st,expected_slot):
        self.f.restore(st)
        self.f.pulse('DOWN',25)  # Pokémon, na grade de ações
        self.f.pulse('A',80)
        # A equipe visual põe o ativo na frente; DOWN escolhe o reserva
        # tanto na ida (slot físico 1) quanto na volta (slot físico 0).
        self.f.pulse('DOWN',25)
        self.f.pulse('A',35)
        self.f.pulse('A',35)
        self.f.run(1100)
        out = self.finish_turn()
        self.assertEqual(old.u16(out,old.offset(old.PARTY_INDEXES_ADDR)),expected_slot)
        return out

    def test_troca_limpa_historico_novo_golpe_registra_e_retorno_tambem_limpa(self):
        st,seen = self.turn(self.switch_state())
        self.assertEqual(old.u16(st,LAST_MOVES),150)
        self.assertEqual(party_pp(st,old.PARTY,0),[6,10,10,10])
        st = self.switch_to_other(st,1)
        self.assertEqual(old.u16(st,LAST_MOVES),0)
        self.assertEqual(party_pp(st,old.PARTY,1),[12,11,13,14])
        self.assertEqual(list(st[old.PLAYER_BATTLE+0x25:old.PLAYER_BATTLE+0x29]),[12,11,13,14])
        self.assertEqual(party_pp(st,old.PARTY,0),[6,10,10,10])
        self.assertLess(old.u16(st,old.PLAYER_BATTLE+0x2A),170)  # Eerie acertou o entrante
        st,seen = self.turn(st)
        self.assert_used(seen,'GROWL')
        self.assertEqual(old.u16(st,LAST_MOVES),45)
        self.assertEqual(party_pp(st,old.PARTY,1),[8,11,13,14])  # uso + dreno
        st = self.switch_to_other(st,0)
        self.assertEqual(old.u16(st,LAST_MOVES),0)
        self.assertEqual(party_pp(st,old.PARTY,0),[6,10,10,10])
        self.assertEqual(list(st[old.PLAYER_BATTLE+0x25:old.PLAYER_BATTLE+0x29]),[6,10,10,10])
        self.assertEqual(party_pp(st,old.PARTY,1),[8,11,13,14])
        st,seen = self.turn(st)
        self.assert_used(seen,'SPLASH')
        self.assertEqual(old.u16(st,LAST_MOVES),150)
        self.assertEqual(party_pp(st,old.PARTY,0),[2,10,10,10])

    def test_cancelar_menu_de_troca_preserva_historico_e_pp(self):
        st,_ = self.turn(self.switch_state())
        self.f.restore(st)
        self.f.pulse('DOWN',25)
        self.f.pulse('A',80)
        self.f.pulse('B',120)  # cancela antes de escolher um Pokémon
        self.f.pulse('UP',25)  # volta o cursor a Fight, sem executar ação
        cancelled = self.f.state()
        self.assertIn('vai fazer?',text(cancelled))
        self.assertEqual(old.u16(cancelled,old.offset(old.PARTY_INDEXES_ADDR)),0)
        self.assertEqual(old.u16(cancelled,LAST_MOVES),150)
        self.assertEqual(party_pp(cancelled,old.PARTY,0),[6,10,10,10])
        self.assertEqual(party_pp(cancelled,old.ENEMY_PARTY_ADDR,0),party_pp(st,old.ENEMY_PARTY_ADDR,0))
        out,seen = self.turn(cancelled)
        self.assert_used(seen,'SPLASH')
        self.assertEqual(party_pp(out,old.PARTY,0),[2,10,10,10])


class EerieHistoryFixtureDataTests(unittest.TestCase):
    def test_moveset_tem_checksum_valido_e_preserva_demais_bytes(self):
        from test_battle_experience_fixture import empty_mon_state
        st = empty_mon_state()
        before = bytes(st)
        set_moves(st,old.PARTY,0,(205,150,45,39),(4,0,0,0))
        self.assertEqual(party_pp(st,old.PARTY,0),[4,0,0,0])
        pos = old.offset(old.PARTY)
        # PID=0 na fixture mínima: ataques no segundo bloco (12 B).
        allowed = set(range(pos+28,pos+30)) | set(range(pos+44,pos+56))
        changed = {i for i,(a,b) in enumerate(zip(before,st)) if a!=b}
        self.assertTrue(changed <= allowed)
        self.assertEqual(st[pos+84],10)

    def test_recusa_moveset_slot_ou_checksum_invalido(self):
        from test_battle_experience_fixture import empty_mon_state
        for moves,pps,slot in (((33,),(10,),0),((33,0,0,0),(10,0,0,0),6)):
            with self.assertRaises(ValueError):
                set_moves(empty_mon_state(),old.PARTY,slot,moves,pps)
        st = empty_mon_state()
        st[old.offset(old.PARTY)+28] ^= 1
        with self.assertRaises(ValueError):
            set_moves(st,old.PARTY,0,(33,0,0,0),(10,0,0,0))
        with self.assertRaises(ValueError):
            party_pp(st,old.PARTY,0)
