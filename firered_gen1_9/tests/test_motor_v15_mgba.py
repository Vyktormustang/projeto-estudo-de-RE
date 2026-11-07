"""Encore/Disable: duração, ordem da ação e interação com travas naturais."""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v10_mgba as old
import test_eerie_history_mgba as h
from scripts import motor_v15 as patch

BASE = os.environ.get('MOTOR_V15_BASE')
ROM = os.environ.get('MOTOR_V15_ROM')
CORE = os.environ.get('MGBA_CORE')
D = old.offset(0x02021648)+28
MARKER = old.offset(0x0202160C)


def status(st,effect):
    field,timer = (4,11) if effect==50 else (6,14)
    return old.u16(st,D+field),st[D+timer]&15,st[D+timer]>>4


@unittest.skipUnless(BASE and ROM and CORE,'defina MOTOR_V15_BASE, MOTOR_V15_ROM e MGBA_CORE')
class MotorV15MGBATests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        if cls.rom.read_bytes()!=patch.build(Path(BASE).read_bytes()):
            raise ValueError('ROM v15 diverge da reconstrução')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(Path(BASE),Path(CORE),Path(cls.temp.name)/'base')
        try:
            cls.fixture = old.route_entry_fixture(cls.f)
            cls.battle_fixture = cls._make_singles_fixture()
            test = cls(); cls.baseline = {}
            for effect,move in ((50,33),(227,205)):
                for fast in (False,True):
                    st = test.scenario(move,effect,fast)
                    st,_,_ = test.turn(st,effect)
                    st,_,_ = test.turn(st,effect,'RIGHT')
                    cls.baseline[effect,fast] = status(st,effect)
        finally:
            cls.f.close()
        cls.f = old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name)/'v15')
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close(); cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada')

    def scenario(self,move,effect,fast=True,pp=20):
        st = bytearray(self._duel_state(33,move2_id=effect,foe_move=move,
            p_atk=30,p_def=100,p_speed=600 if fast else 40,p_hp=4000,p_max=4000,
            f_hp=10000,f_max=10000,f_atk=300,f_speed=400))
        for bank,party,moves,pps in (
            (old.PLAYER_BATTLE,old.PARTY,(33,effect,45,39),(20,5 if effect==227 else 20,0,0)),
            (old.FOE_BATTLE,old.ENEMY_PARTY_ADDR,(move,150,45,39),(pp,0,0,0)),
        ):
            h.set_moves(st,party,0,moves,pps)
            for i,mid in enumerate(moves):
                old.put16(st,bank+12+2*i,mid);st[bank+0x25+i]=pps[i]
            for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98)):
                old.put16(st,old.offset(party)+po,old.u16(st,bank+bo))
        st[old.FOE_BATTLE+0x1E]=12
        self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
        return bytes(st)

    def turn(self,st,effect,direction=None):
        self.f.restore(st)
        prev = status(st,effect)[0]
        hp = old.u16(st,old.PLAYER_BATTLE+0x2A)
        hits,onsets = [],[]
        def run(frames,*buttons):
            nonlocal prev,hp
            for _ in range(frames):
                self.f.run(1,*buttons);state=self.f.state()
                current = status(state,effect)
                if current[0] and not prev: onsets.append(current)
                prev = current[0]
                now = old.u16(state,old.PLAYER_BATTLE+0x2A)
                if now!=hp:
                    hits.append((hp-now,old.u16(state,old.offset(0x02021586)),old.u16(state,old.offset(0x02021864))))
                    hp=now
        run(3,'A');run(25)
        if direction: run(3,direction);run(15)
        run(6,'A');run(1100)
        for _ in range(8):run(3,'B');run(90)
        out=self.f.state()
        self.assertIn('vai fazer?',h.text(out))
        self.assertEqual(old.u32(out,MARKER)&0x800,0)
        self.assertEqual(sum(h.party_pp(out,old.PARTY,0)),sum(h.party_pp(st,old.PARTY,0))-1)
        for bank,party in ((old.PLAYER_BATTLE,old.PARTY),(old.FOE_BATTLE,old.ENEMY_PARTY_ADDR)):
            self.assertEqual(list(out[bank+0x25:bank+0x29]),h.party_pp(out,party,0))
            self.assertEqual(old.u16(out,bank+0x2A),old.u16(out,old.offset(party)+86))
        return out,hits,onsets

    def assert_hit(self,hits,move,power=None):
        self.assertEqual(len(hits),1,hits)
        self.assertGreater(hits[0][0],0)
        self.assertEqual(hits[0][1],move)
        if power is not None:self.assertEqual(hits[0][2],power)

    def test_base_v14_reproduz_duracoes_legadas(self):
        self.assertEqual(self.baseline[50,True],(33,4,5))
        self.assertEqual(self.baseline[50,False],(33,1,2))
        self.assertEqual(self.baseline[227,True],(205,5,6))
        self.assertEqual(self.baseline[227,False],(205,4,5))

    def duration_case(self,effect,move,fast):
        n=(4 if effect==50 else 3)+(0 if fast else 1)
        st=self.scenario(move,effect,fast)
        st,hits,_=self.turn(st,effect)
        self.assert_hit(hits,move,30 if move!=33 else None)
        st,hits,onsets=self.turn(st,effect,'RIGHT')
        self.assertEqual(onsets,[(move,n,n)])
        self.assertEqual(status(st,effect),(move,n-1,n))
        if effect==50 and fast:
            self.assertEqual(hits,[])
            self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
        else:
            self.assert_hit(hits,move,60 if move!=33 else None)
        self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0],
                         19 if (move!=33 or (effect==50 and fast)) else 18)
        for elapsed in range(1,n):
            st,hits,onsets=self.turn(st,effect,'LEFT' if elapsed==1 else None)
            self.assertEqual(onsets,[])
            remaining=n-1-elapsed
            self.assertEqual(status(st,effect),(move if remaining else 0,remaining,n))
            if effect==50:
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0],19 if (fast or move!=33) else 18)
                if not fast and move!=33 and elapsed==1:
                    self.assertEqual(hits,[])
                else:
                    self.assert_hit(hits,165,50)
                self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
            else:
                self.assert_hit(hits,move,(60<<elapsed) if move!=33 else None)
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0],19 if move!=33 else 18-elapsed)
                if move!=33:
                    self.assertEqual(bool(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS),elapsed<3)
        # Voltar a usar o golpe após Disable deve gastar PP e reiniciar a potência.
        if effect==50:
            before=h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0]
            st,hits,_=self.turn(st,effect)
            self.assert_hit(hits,move,30 if move!=33 else None)
            self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0],before-1)
        elif move!=33:
            # Encore termina antes ou junto do quinto impacto, sem cancelar
            # a trava própria de Rollout/Ice Ball nem cobrar PP por continuação.
            # Já ocorreram n+1 impactos: completar exatamente os cinco.
            for impact in range(n+2,6):
                self.assertTrue(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
                st,hits,_=self.turn(st,effect)
                self.assert_hit(hits,move,30<<(impact-1))
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0],19)
            self.assertFalse(old.u32(st,old.FOE_BATTLE+0x54)&h.MULTIPLETURNS)
            st,hits,_=self.turn(st,effect)
            self.assert_hit(hits,move,30)
            self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0)[0],18)

    def test_disable_quatro_acoes_antes_e_depois_do_alvo(self):
        for fast in (True,False):
            with self.subTest(fast=fast):self.duration_case(50,33,fast)

    def test_encore_tres_acoes_antes_e_depois_do_alvo(self):
        for fast in (True,False):
            with self.subTest(fast=fast):self.duration_case(227,33,fast)

    def test_disable_interrompe_rollout_ice_ball_sem_pp_extra(self):
        for move in (205,301):
            for fast in (True,False):
                with self.subTest(move=move,fast=fast):self.duration_case(50,move,fast)

    def test_encore_nao_cancela_rollout_ice_ball_ao_expirar(self):
        for move in (205,301):
            for fast in (True,False):
                with self.subTest(move=move,fast=fast):self.duration_case(227,move,fast)

    def test_reaplicacao_falha_sem_renovar_duracao(self):
        for effect in (50,227):
            st=self.scenario(205,effect)
            st,_,_=self.turn(st,effect)
            st,_,_=self.turn(st,effect,'RIGHT')
            before=status(st,effect)
            st,_,onsets=self.turn(st,effect)
            self.assertEqual(onsets,[])
            self.assertEqual(status(st,effect),(before[0],before[1]-1,before[2]))

    def test_sem_historico_falha_sem_timer(self):
        for effect in (50,227):
            st,hits,onsets=self.turn(self.scenario(205,effect),effect,'RIGHT')
            self.assertEqual(onsets,[])
            self.assertEqual(status(st,effect),(0,0,0))
            self.assert_hit(hits,205,30)

    def test_pp_zero_falha_mas_continuacao_ainda_ocorre(self):
        for effect in (50,227):
            for move in (205,301):
                with self.subTest(effect=effect,move=move):
                    st=self.scenario(move,effect,pp=1)
                    st,_,_=self.turn(st,effect)
                    st,hits,onsets=self.turn(st,effect,'RIGHT')
                    self.assertEqual(onsets,[])
                    self.assertEqual(status(st,effect),(0,0,0))
                    self.assert_hit(hits,move,60)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[0]*4)

    def test_encore_termina_cedo_quando_pp_proprio_acaba(self):
        st=self.scenario(33,227,pp=2)
        st,_,_=self.turn(st,227)
        st,hits,onsets=self.turn(st,227,'RIGHT')
        self.assertEqual(onsets,[(33,3,3)])
        self.assert_hit(hits,33)
        self.assertEqual(status(st,227),(0,0,3))
        self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[0]*4)
        st,hits,_=self.turn(st,227,'LEFT')
        self.assert_hit(hits,165,50)
