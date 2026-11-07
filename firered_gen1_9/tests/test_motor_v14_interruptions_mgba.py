"""Duplas e interrupções naturais sobre v14 exato; nenhum patch de ROM.

MOTOR_V14_ROM=/caminho/motor_v14.gba MGBA_CORE=/caminho/mgba_libretro.so
Não injeta trava, histórico, flinch, confusão, paralisia nem marcador de PP.
"""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v10_mgba as old
import test_eerie_history_mgba as h
from scripts import motor_v14 as patch

ROM = os.environ.get('MOTOR_V14_ROM')
CORE = os.environ.get('MGBA_CORE')
MARKER = old.offset(0x0202160C)
ATTACKER = old.offset(0x020215A8)
TARGET = old.offset(0x020215A9)
MOVE = old.offset(0x02021586)
POWER = old.offset(0x02021864)
CURSOR = old.offset(0x020215B0)
PROTECT = old.offset(0x020216CC)


def pp(st,bank):
    party = old.PARTY if bank%2==0 else old.ENEMY_PARTY_ADDR
    idx = old.u16(st,old.offset(old.PARTY_INDEXES_ADDR)+2*bank)
    return h.party_pp(st,party,idx)


def locked(st,bank):
    return bool(old.u32(st,old.bank_off(bank)+0x54)&h.MULTIPLETURNS)


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V14_ROM e MGBA_CORE')
class MotorV14DoublesInterruptionTests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_doubles_fixture = classmethod(old.MotorV10MGBATests._make_doubles_fixture.__func__)

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise ValueError('ROM não é motor_v14 exato')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.doubles_fixture = cls._make_doubles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close(); cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada')

    def scenario(self,actor,move,initial_pp=10):
        st = bytearray(self.doubles_fixture)
        self.assertEqual(st[old.offset(0x020213F4)],4)
        for bank in range(4):
            b = old.bank_off(bank)
            party = old.PARTY if bank%2==0 else old.ENEMY_PARTY_ADDR
            idx = old.u16(st,old.offset(old.PARTY_INDEXES_ADDR)+2*bank)
            if bank==actor:
                if bank%2:
                    # A primeira ação inimiga desta fixture usa o slot 1.
                    # Mantê-lo válido evita um NoPP artificial na preparação.
                    moves,pps = (33,move,45,39),(0,initial_pp,0,0)
                else:
                    moves,pps = (move,33,45,39),(initial_pp,10,0,0)
            elif actor%2==0 and bank%2:
                moves,pps = (150,182,45,39),(1,20,0,0)
            elif actor%2 and bank%2==0:
                moves,pps = (150,182,45,39),(20,20,0,0)
            else:
                moves,pps = ((33,150,45,39),(0,20,0,0)) if bank%2 else ((150,33,45,39),(20,0,0,0))
            h.set_moves(st,party,idx,moves,pps)
            for i,mid in enumerate(moves):
                old.put16(st,b+12+2*i,mid); st[b+0x25+i] = pps[i]
            for i in range(1,8): st[b+0x18+i] = 6
            st[b+0x1E] = 12
            st[b+0x20] = 4  # Battle Armor, sem críticos
            st[b+0x22] = st[b+0x23] = 0
            for off,val in ((2,200),(4,100),(6,400 if bank==actor else 40),
                            (8,100),(10,100),(0x2A,4000),(0x2E,4000),(0x30,0)):
                old.put16(st,b+off,val)
            for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98),(0x2A,86),(0x2E,88)):
                old.put16(st,old.offset(party)+idx*100+po,old.u16(st,b+bo))
            old.put32(st,b+0x50,0); old.put32(st,b+0x54,0)
            old.put32(st,old.offset(party)+idx*100+80,0)
            self.assertEqual(old.u16(st,h.LAST_MOVES+2*bank),0)
        self.assertEqual(old.u32(st,MARKER)&0x800,0)
        return bytes(st)

    def turn(self,st,choices):
        """choices: (direção do slot, alvo opcional) dos jogadores não travados.

        O alvo é selecionado pela interface, nunca por escrita em gBattlerTarget.
        Observa também as confirmações B, não só a janela inicial de animação.
        """
        self.f.restore(st)
        previous_marker = old.u32(st,MARKER)&0x800
        hp = [old.u16(st,old.bank_off(b)+0x2A) for b in range(4)]
        marks,hits = [],[]
        def run(frames,*buttons):
            nonlocal previous_marker
            for _ in range(frames):
                self.f.run(1,*buttons)
                state = self.f.state()
                marker = old.u32(state,MARKER)&0x800
                a,t,move = state[ATTACKER],state[TARGET],old.u16(state,MOVE)
                if marker and not previous_marker:
                    marks.append((a,t,move,old.u32(state,CURSOR)))
                previous_marker = marker
                for bank in range(4):
                    now = old.u16(state,old.bank_off(bank)+0x2A)
                    if now!=hp[bank]:
                        hits.append((bank,hp[bank]-now,a,t,move,old.u16(state,POWER)))
                        hp[bank] = now
        def pulse(button,gap=25):
            run(3,button); run(gap)
        for direction,target in choices:
            pulse('A')
            if direction: pulse(direction,15)
            pulse('A')
            if target is not None:
                if target==3: pulse('LEFT',15)
                pulse('A')
        run(2200)
        for _ in range(8): pulse('B',90)
        out = self.f.state()
        self.assertIn('vai fazer?',h.text(out))
        self.assertEqual(old.u32(out,MARKER)&0x800,0)
        for bank in range(4):
            b = old.bank_off(bank)
            self.assertEqual(list(out[b+0x25:b+0x29]),pp(out,bank))
            party = old.PARTY if bank%2==0 else old.ENEMY_PARTY_ADDR
            idx = old.u16(out,old.offset(old.PARTY_INDEXES_ADDR)+2*bank)
            self.assertEqual(old.u16(out,old.offset(party)+idx*100+86),hp[bank])
        return out,marks,hits

    def player_matrix(self,move):
        for actor in (0,2):
            for target in (1,3):
                with self.subTest(actor=actor,target=target,move=move):
                    st = self.scenario(actor,move)
                    for _ in range(10):
                        was_locked = locked(st,actor)
                        before = [pp(st,b) for b in range(4)]
                        choices = [(None,target if b==actor else None)
                                   for b in (0,2) if not locked(st,b)]
                        out,marks,hits = self.turn(st,choices)
                        self.assertEqual(pp(out,actor)[0],before[actor][0]-(0 if was_locked else 1))
                        for b in range(4):
                            if b!=actor: self.assertEqual(sum(pp(out,b)),sum(before[b])-1)
                        for victim,damage,a,t,mid,power in hits:
                            self.assertEqual((victim,a,t,mid),(target,actor,target,move))
                            self.assertGreater(damage,0)
                        st = out
                        if marks:
                            self.assertTrue(was_locked)
                            self.assertEqual(marks,[(actor,target,move,0x08186349)])
                            self.assertEqual(hits,[])
                            self.assertFalse(locked(st,actor))
                            break
                    else:
                        self.fail('AI não produziu Protect numa continuação dentro do limite')
                    # O aliado lento age DEPOIS do usuário bloqueado, gastando
                    # seu próprio Splash; o próximo Tackle também deve gastar.
                    before = [pp(st,b) for b in range(4)]
                    choices = [('RIGHT',target) if b==actor else (None,None) for b in (0,2)]
                    st,marks,_ = self.turn(st,choices)
                    self.assertEqual(marks,[])
                    self.assertEqual(pp(st,actor),[before[actor][0],9,0,0])
                    self.assertEqual(old.u16(st,h.LAST_MOVES+2*actor),33)
                    for b in range(4):
                        if b!=actor: self.assertEqual(sum(pp(st,b)),sum(before[b])-1)

    def enemy_matrix(self,move):
        for actor in (1,3):
            for initial in (10,1):
                with self.subTest(actor=actor,move=move,initial=initial):
                    st = self.scenario(actor,move,initial_pp=initial)
                    st,marks,hits = self.turn(st,[(None,None),(None,None)])
                    self.assertEqual(marks,[])
                    self.assertEqual(len(hits),1)
                    victim,damage,a,t,mid,power = hits[0]
                    self.assertIn(victim,(0,2))
                    self.assertEqual((a,t,mid,power),(actor,victim,move,30))
                    self.assertTrue(locked(st,actor))
                    self.assertEqual(pp(st,actor)[1],initial-1)
                    before = [pp(st,b) for b in range(4)]
                    st,marks,hits = self.turn(st,[('RIGHT',None),('RIGHT',None)])
                    self.assertEqual(hits,[])
                    self.assertEqual(len(marks),1)
                    a,t,mid,cursor = marks[0]
                    self.assertEqual((a,mid,cursor),(actor,move,0x08186349))
                    self.assertIn(t,(0,2))  # alvo da AI observado, não escolhido pelo teste
                    self.assertFalse(locked(st,actor))
                    self.assertEqual(pp(st,actor)[1],initial-1)
                    for b in range(4):
                        if b!=actor: self.assertEqual(sum(pp(st,b)),sum(before[b])-1)
                    before = [pp(st,b) for b in range(4)]
                    st,_,hits = self.turn(st,[('LEFT',None),('LEFT',None)])
                    if initial>1:
                        self.assertEqual(pp(st,actor)[1],initial-2)
                        self.assertTrue(any(e[2]==actor and e[4:]==(move,30) for e in hits))
                    else:
                        self.assertEqual(pp(st,actor),[0]*4)
                        self.assertEqual(old.u16(st,h.LAST_MOVES+2*actor),165)
                        self.assertFalse(locked(st,actor))
                    for b in range(4):
                        if b!=actor: self.assertEqual(sum(pp(st,b)),sum(before[b])-1)

    def test_rollout_jogadores_0_2_alvos_1_3_sem_vazar_pp(self):
        self.player_matrix(205)

    def test_ice_ball_jogadores_0_2_alvos_1_3_sem_vazar_pp(self):
        self.player_matrix(301)

    def test_rollout_inimigos_1_3_pp_positivo_zero_e_reinicio(self):
        self.enemy_matrix(205)

    def test_ice_ball_inimigos_1_3_pp_positivo_zero_e_reinicio(self):
        self.enemy_matrix(301)


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V14_ROM e MGBA_CORE')
class MotorV14NaturalInterruptionTests(unittest.TestCase):
    _enter_wild_encounter = classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_singles_fixture = classmethod(old.MotorV10MGBATests._make_singles_fixture.__func__)
    _duel_state = old.MotorV10MGBATests._duel_state

    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM)
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise ValueError('ROM não é motor_v14 exato')
        cls.temp = tempfile.TemporaryDirectory()
        cls.f = old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture = old.route_entry_fixture(cls.f)
        cls.battle_fixture = cls._make_singles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close(); cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes()) != patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada')

    def scenario(self,move,interrupt):
        st = bytearray(self._duel_state(33,move2_id=interrupt,foe_move=move,
            p_atk=30,p_def=100,p_speed=600,p_hp=4000,p_max=4000,
            f_hp=10000,f_max=10000,f_atk=300,f_speed=400))
        for bank,party,moves in (
            (0,old.PARTY,(33,interrupt,45,39)),
            (1,old.ENEMY_PARTY_ADDR,(move,150,45,39)),
        ):
            b = old.bank_off(bank)
            pps = (20,20,0,0) if bank==0 else (20,0,0,0)
            h.set_moves(st,party,0,moves,pps)
            for i,mid in enumerate(moves):
                old.put16(st,b+12+2*i,mid); st[b+0x25+i] = pps[i]
            for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98)):
                old.put16(st,old.offset(party)+po,old.u16(st,b+bo))
        st[old.FOE_BATTLE+0x1E] = 12
        self.assertFalse(locked(st,1))
        self.assertEqual(old.u32(st,old.FOE_BATTLE+0x50),0)
        return bytes(st)

    def turn(self,st,direction=None):
        self.f.restore(st)
        flags = set()
        markers = []
        powers = []
        hp = old.u16(st,old.PLAYER_BATTLE+0x2A)
        def run(frames,*buttons):
            nonlocal hp
            for _ in range(frames):
                self.f.run(1,*buttons)
                state = self.f.state()
                if state[PROTECT+16]&0x80: flags.add('paralysis')
                if state[PROTECT+17]&1: flags.add('confusion')
                if state[PROTECT+18]&4: flags.add('flinch')
                if old.u32(state,MARKER)&0x800:
                    markers.append((state[ATTACKER],old.u16(state,MOVE),old.u32(state,CURSOR)))
                now = old.u16(state,old.PLAYER_BATTLE+0x2A)
                if now!=hp:
                    powers.append((hp-now,old.u16(state,MOVE),old.u16(state,POWER)))
                    hp = now
        run(3,'A'); run(25)
        if direction: run(3,direction); run(15)
        run(6,'A'); run(1100)
        for _ in range(8): run(3,'B'); run(90)
        out = self.f.state()
        self.assertIn('vai fazer?',h.text(out))
        self.assertEqual(markers,[],'Wrapper não deve armar isenção nesses desvios')
        self.assertEqual(old.u32(out,MARKER)&0x800,0)
        self.assertEqual(sum(pp(out,0)),sum(pp(st,0))-1)
        for bank in (0,1):
            b = old.bank_off(bank)
            self.assertEqual(list(out[b+0x25:b+0x29]),pp(out,bank))
            party = old.PARTY if bank==0 else old.ENEMY_PARTY_ADDR
            self.assertEqual(old.u16(out,b+0x2A),old.u16(out,old.offset(party)+86))
        return out,flags,powers

    def interrupted(self,interrupt,kind):
        for move in (205,301):
            with self.subTest(move=move,interrupt=interrupt):
                st = self.scenario(move,interrupt)
                st,flags,powers = self.turn(st)
                self.assertEqual(flags,set())
                self.assertEqual(len(powers),1)
                self.assertEqual(powers[0][1:],(move,30))
                self.assertTrue(locked(st,1))
                self.assertEqual(pp(st,1),[19,0,0,0])
                for turn in range(12):
                    was_locked = locked(st,1)
                    before = pp(st,1)[0]
                    foe_hp = old.u16(st,old.FOE_BATTLE+0x2A)
                    st,flags,powers = self.turn(st,'RIGHT' if turn==0 else None)
                    if kind in flags:
                        self.assertEqual(pp(st,1)[0],before)
                        self.assertEqual(powers,[])
                        self.assertFalse(locked(st,1))
                        if kind=='confusion':
                            self.assertLess(old.u16(st,old.FOE_BATTLE+0x2A),foe_hp)
                        if kind=='paralysis':
                            self.assertTrue(old.u32(st,old.FOE_BATTLE+0x50)&0x40)
                        if was_locked: break
                    else:
                        self.assertEqual(pp(st,1)[0],before-(0 if was_locked else 1))
                else:
                    self.fail(f'{kind} durante continuação não observado dentro do limite')
                # Após a interrupção, o próximo impacto executado deve ser um
                # novo uso a potência 30. Confusão/paralisia podem impedir mais
                # ações: não se limpam artificialmente os estados para testar.
                for turn in range(12):
                    before = pp(st,1)[0]
                    st,flags,powers = self.turn(st,'LEFT' if turn==0 else None)
                    self.assertEqual(old.u16(st,h.LAST_MOVES),33)  # Tackle real
                    if powers:
                        self.assertEqual(len(powers),1)
                        self.assertEqual(powers[0][1:],(move,30))
                        self.assertEqual(pp(st,1)[0],before-1)
                        break
                    self.assertEqual(pp(st,1)[0],before)
                else:
                    self.fail('Nenhum impacto de reinício dentro do limite')

    def test_flinch_por_stomp_cancela_sem_pp_extra_e_reinicia(self):
        self.interrupted(23,'flinch')

    def test_autoataque_por_confuse_ray_cancela_sem_pp_extra_e_reinicia(self):
        self.interrupted(109,'confusion')

    def test_imobilidade_por_thunder_wave_cancela_sem_pp_extra_e_reinicia(self):
        self.interrupted(86,'paralysis')
