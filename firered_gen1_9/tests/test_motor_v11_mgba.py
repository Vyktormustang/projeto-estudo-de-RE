"""Regressão Eerie Spell em mGBA, somente estados sintéticos gerados por ROM."""
from __future__ import annotations
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v10_mgba as old
from scripts import motor_v11 as patch

BASE = os.environ.get('MOTOR_V11_BASE')
ROM = os.environ.get('MOTOR_V11_ROM')
CORE = os.environ.get('MGBA_CORE')
LAST_MOVES = 0x020215D4


def party_pp(state, slot):
    pos = old.offset(old.ENEMY_PARTY_ADDR)
    block, order, valid = old.decrypted(state[pos:pos+100])
    if not valid:
        raise AssertionError('Checksum da equipe inválido')
    return block[order[1]*12+8+slot]


@unittest.skipUnless(BASE and ROM and CORE, 'defina MOTOR_V11_BASE, MOTOR_V11_ROM e MGBA_CORE')
class MotorV11MGBATests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state
    _run_turn = old.MotorV10MGBATests._run_turn

    @classmethod
    def setUpClass(cls):
        base, rom = Path(BASE), Path(ROM)
        if rom.read_bytes() != patch.build(base.read_bytes()):
            raise ValueError('ROM diverge do build determinístico')
        cls.temp = tempfile.TemporaryDirectory()
        # Reproduz o defeito na base usando fixture própria, nunca um state v11.
        cls.f = old.Emulator(base, Path(CORE), Path(cls.temp.name) / 'base')
        try:
            cls.fixture = old.route_entry_fixture(cls.f)
            cls.battle_fixture = cls._make_singles_fixture()
            test = cls()
            before = test.eerie_state()
            after, _ = test._run_turn(before)
            cls.baseline_pp = list(after[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29])
        finally:
            cls.f.close()
        cls.f = old.Emulator(rom, Path(CORE), Path(cls.temp.name) / 'v11')
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()

    def eerie_state(self, *, last=45, pp=10, status2=0, mimic=False):
        st = bytearray(self._duel_state(720, f_status1=7))
        # Alvo adormecido: nenhuma redução por ação própria durante este turno.
        for s, mid in enumerate((33, 150, 45, 39)):
            old.put16(st, old.FOE_BATTLE+0x0C+2*s, mid)
            st[old.FOE_BATTLE+0x25+s] = 10
        st[old.FOE_BATTLE+0x27] = pp
        old.put16(st, old.offset(LAST_MOVES)+2, last)
        old.put32(st, old.FOE_BATTLE+0x54, status2)
        if mimic:
            st[old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28+0x18] |= 0x40
        return bytes(st)

    def test_defeito_reproduzido_na_base_v10(self):
        self.assertEqual(self.baseline_pp, [7,10,10,10])

    def test_limite_substitute_legado_nao_drena_apos_turno_completo(self):
        # Caracterização de limite, NÃO conformidade Gen 6+: Eerie Spell
        # deveria atravessar Substitute. Não medir enquanto o texto <fb>
        # aguarda confirmação (isso ocorria na primeira versão deste teste).
        st = bytearray(self.eerie_state(status2=0x01000000))
        sub_hp = old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28+10
        st[sub_hp] = 200
        out, _ = self._run_turn(bytes(st))
        for _ in range(8):
            self.f.pulse('B',90)
        out = self.f.state()
        txt = old.decode_gba_str(out[old.offset(old.DISP_STR):old.offset(old.DISP_STR)+80])
        self.assertIn('vai fazer?',txt)
        self.assertLess(out[sub_hp],200)
        self.assertEqual(old.u16(out,old.FOE_BATTLE+0x2A),480)
        self.assertEqual(list(out[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29]), [10]*4)

    def test_ultimo_golpe_slot2_e_checksum_equipe(self):
        st = self.eerie_state()
        before_pp = [party_pp(st,s) for s in range(4)]
        out, _ = self._run_turn(st)
        self.assertEqual(list(out[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29]), [10,10,7,10])
        self.assertEqual([party_pp(out,s) for s in range(4)], [before_pp[0],before_pp[1],7,before_pp[3]])
        self.assertLess(old.u16(out, old.FOE_BATTLE+0x2A), 480)

    def test_sem_fallback_e_sem_underflow(self):
        for last, pp, expected in ((0,10,10),(0xFFFF,10,10),(999,10,10),(44,10,10),(45,0,0),(45,1,0),(45,2,0),(45,3,0)):
            with self.subTest(last=last,pp=pp):
                out, _ = self._run_turn(self.eerie_state(last=last,pp=pp))
                self.assertEqual(list(out[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29]), [10,10,expected,10])

    def test_transform_e_mimic_nao_alteram_pp_originais(self):
        for status2, mimic in ((0x00200000,False),(0,True)):
            with self.subTest(status2=status2,mimic=mimic):
                st = self.eerie_state(status2=status2,mimic=mimic)
                before = [party_pp(st,s) for s in range(4)]
                out, _ = self._run_turn(st)
                self.assertEqual(out[old.FOE_BATTLE+0x27], 7)
                self.assertEqual([party_pp(out,s) for s in range(4)], before)

    def test_protect_e_imunidade_nao_drenam(self):
        for foe_move, f_types in ((182,(0,0)),(150,(17,17))):
            with self.subTest(foe_move=foe_move):
                st = bytearray(self._duel_state(720,foe_move=foe_move,f_types=f_types))
                old.put16(st,old.offset(LAST_MOVES)+2,foe_move)
                out, _ = self._run_turn(bytes(st))
                # Apenas 1 PP gasto pelo golpe próprio do alvo, não 3 adicionais.
                self.assertEqual(sum(out[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29]),159)
                self.assertEqual(old.u16(out,old.FOE_BATTLE+0x2A),480)

    def test_mighty_cleave_ja_atravessa_protect_e_tackle_nao(self):
        for move, hits in ((33,False),(794,True)):
            with self.subTest(move=move):
                out, seen = self._run_turn(self._duel_state(move,foe_move=182))
                self.assertEqual(old.u16(out,old.FOE_BATTLE+0x2A)<480,hits,seen)

    def test_ultimo_golpe_registrado_naturalmente(self):
        # No primeiro turno o alvo usa Splash. No seguinte, Eerie Spell
        # deve reduzir o PP do mesmo golpe, sem escrever gLastMoves no teste.
        st, _ = self._run_turn(self._duel_state(150,move2_id=720))
        self.assertEqual(old.u16(st,old.offset(LAST_MOVES)+2),150)
        before = sum(st[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29])
        out, _ = self._run_turn(st,slot=1)
        self.assertEqual(sum(out[old.FOE_BATTLE+0x25:old.FOE_BATTLE+0x29]),before-4)


class MotorV11InheritedRegressionTests(old.MotorV10MGBATests):
    """As seis famílias v10 executadas sobre v11, fixtures geradas nesta ROM."""
    __unittest_skip__ = not bool(BASE and ROM and CORE)
    __unittest_skip_why__ = 'defina MOTOR_V11_BASE, MOTOR_V11_ROM e MGBA_CORE'

    @classmethod
    def setUpClass(cls):
        cls.rom, cls.base, cls.core = Path(ROM), Path(BASE), Path(CORE)
        if cls.rom.read_bytes() != patch.build(cls.base.read_bytes()):
            raise ValueError('ROM v11 divergente')
        cls.temp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.temp.name)
        cls.f = old.Emulator(cls.rom, cls.core, cls.dir)
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()
        cls.two_party_fixture = cls._make_two_party_singles_fixture()
        cls.two_enemy_fixture = cls._make_two_enemy_trainer_like_fixture()
        cls.doubles_fixture = cls._make_doubles_fixture()
