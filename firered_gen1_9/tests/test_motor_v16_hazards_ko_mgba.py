"""Hazards criados por golpes reais, phazing e KO em fixtures sintéticas v16."""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v16_mgba as v16
from battle_fixture_helpers import set_level10_starter_test_stats, party_experience, in_battle, main_callback2, finish_victory

old,h,INDEX,patch=v16.old,v16.h,v16.INDEX,v16.patch
ROM=os.environ.get('MOTOR_V16_ROM')
CORE=os.environ.get('MGBA_CORE')


def hp(st,slot):return old.u16(st,old.offset(old.ENEMY_PARTY_ADDR)+100*slot+86)


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V16_ROM e MGBA_CORE')
class MotorV16HazardsKOTests(unittest.TestCase):
    _enter_wild_encounter=classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _duel_state=old.MotorV10MGBATests._duel_state
    moves=v16.history.MotorV15SwitchHistoryTests.moves

    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM)
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise ValueError('ROM não é v16 exato')
        cls.temp=tempfile.TemporaryDirectory()
        v16.prepare(cls,ROM,Path(cls.temp.name))

    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise AssertionError('ROM alterada')

    def scenario(self,hazard,phazer,bench_hp=400,bench_species=4,active_hp=4000):
        st=bytearray(self._duel_state(hazard,move2_id=phazer,foe_move=150,
            p_hp=4000,p_max=4000,p_atk=30,p_spa=30,p_speed=600,
            f_hp=active_hp,f_max=4000,f_atk=30,f_spa=30,f_speed=400,
            base_state=self.trainer_fixture))
        self.moves(st,old.PARTY,0,(hazard,phazer,720,33),(20,20,20,20),old.PLAYER_BATTLE)
        for slot,species in ((0,4),(1,bench_species)):
            seed=bytearray(old.seed_mon(self.fixture,species,10,(150,33,45,39)))
            set_level10_starter_test_stats(seed,stat=200)
            a=old.offset(old.PARTY);pos=old.offset(old.ENEMY_PARTY_ADDR)+slot*100
            st[pos:pos+100]=seed[a:a+100]
            for off,value in ((86,active_hp if slot==0 else bench_hp),(88,4000 if slot==0 else 400),
                              (90,30),(92,200),(94,400 if slot==0 else 100),(96,30),(98,200)):
                old.put16(st,pos+off,value)
            self.moves(st,old.ENEMY_PARTY_ADDR,slot,(150,33,45,39),(40 if slot==0 else 31,0,0,0),
                       old.FOE_BATTLE if slot==0 else None)
            if slot==0:
                b=old.FOE_BATTLE
                old.put16(st,b,species);st[b+0x2C]=10
                old.put32(st,b+0x48,560);old.put32(st,b+0x4C,old.u32(st,pos))
                old.put32(st,b+0x58,old.u32(st,pos+4))
                for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98)):
                    old.put16(st,b+bo,old.u16(st,pos+po))
        for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98)):
            old.put16(st,old.offset(old.PARTY)+po,old.u16(st,old.PLAYER_BATTLE+bo))
        self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
        self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+13],0)
        return bytes(st)

    def turn(self,st,directions=(),require_menu=True):
        self.f.restore(st)
        self.seen=[];self.transitions=[];self.losses=[]
        prev_index=old.u16(st,INDEX+2);health=[hp(st,i) for i in range(2)]
        def run(frames,*buttons):
            nonlocal prev_index
            for _ in range(frames):
                self.f.run(1,*buttons);now=self.f.state();txt=h.text(now)
                if txt and (not self.seen or self.seen[-1]!=txt):self.seen.append(txt)
                idx=old.u16(now,INDEX+2)
                if idx!=prev_index:self.transitions.append((prev_index,idx));prev_index=idx
                for i in range(2):
                    value=hp(now,i)
                    if value!=health[i]:self.losses.append((i,health[i],value));health[i]=value
        run(3,'A');run(25)
        for button in directions:run(3,button);run(15)
        run(6,'A');run(1600)
        for _ in range(64):
            run(3,'B');run(90)
            if 'vai fazer?' in h.text(self.f.state()):
                run(120)  # permitir que a transição do menu termine
                break
        out=self.f.state()
        if require_menu:self.assertIn('vai fazer?',h.text(out),self.seen)
        return out

    def consistent(self,st):
        for bank,party in ((0,old.PARTY),(1,old.ENEMY_PARTY_ADDR)):
            idx=old.u16(st,INDEX+2*bank);b=old.bank_off(bank)
            self.assertEqual(list(st[b+0x25:b+0x29]),h.party_pp(st,party,idx))
            self.assertEqual(old.u16(st,b+0x2A),old.u16(st,old.offset(party)+100*idx+86))
        self.assertEqual(old.u32(st,old.offset(0x0202160C))&0x800,0)
        self.assertTrue(in_battle(st))

    def plant(self,st,hazard):
        out=self.turn(st)
        self.consistent(out)
        self.assertEqual(hp(out,0),hp(st,0))
        self.assertEqual(h.party_pp(out,old.PARTY,0),[19,20,20,20])
        if hazard==445:self.assertEqual(out[old.offset(old.V8_STATE_ADDR)+13],1)
        else:self.assertEqual(out[old.offset(old.SIDE_TIMERS_ADDR)+12+10],1)
        self.assertEqual(old.u16(out,h.LAST_MOVES+2),150)
        return out

    def test_entrada_sobre_spikes_e_stealth_rock_sem_ko(self):
        for hazard,damage in ((191,50),(445,100)):
            for phazer in (46,18,521,508):
                with self.subTest(hazard=hazard,phazer=phazer):
                    st=self.plant(self.scenario(hazard,phazer),hazard)
                    st=self.turn(st,('RIGHT',))
                    self.consistent(st)
                    self.assertEqual(self.transitions,[(0,1)])
                    self.assertEqual(hp(st,1),400-damage)
                    self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
                    self.assertEqual(h.party_pp(st,old.PARTY,0),[19,19,20,20])
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[38,0,0,0])
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[31,0,0,0])
                    st=self.turn(st,('LEFT','DOWN'))
                    self.consistent(st)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[30,0,0,0])
                    st=self.turn(st)
                    self.consistent(st)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[26,0,0,0])

    def test_ko_na_entrada_concede_exp_e_substituto_recebe_hazard(self):
        for hazard,damage in ((191,50),(445,100)):
            for phazer in (46,18,521,508):
                with self.subTest(hazard=hazard,phazer=phazer):
                    st=self.plant(self.scenario(hazard,phazer,bench_hp=damage),hazard)
                    exp=party_experience(st)
                    st=self.turn(st,('RIGHT',))
                    self.consistent(st)
                    self.assertEqual(self.transitions,[(0,1),(1,0)])
                    self.assertIn((1,damage,0),self.losses)
                    # O último dano no slot 0 é o hazard da reentrada, não
                    # outro golpe. Dano de Dragon Tail/Circle Throw é anterior.
                    self.assertEqual(self.losses[-1][0],0)
                    self.assertEqual(self.losses[-1][1]-self.losses[-1][2],damage*10)
                    self.assertEqual(hp(st,1),0)
                    self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
                    self.assertEqual(party_experience(st),exp+138)
                    self.assertEqual(h.party_pp(st,old.PARTY,0),[19,19,20,20])
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[38,0,0,0])
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[31,0,0,0])
                    st=self.turn(st,('LEFT','DOWN'))
                    self.consistent(st)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[37,0,0,0])
                    self.assertEqual(hp(st,1),0)

    def test_flying_ignora_spikes_mas_recebe_stealth_rock_quadruplicado(self):
        for hazard,damage in ((191,0),(445,200)):
            with self.subTest(hazard=hazard):
                st=self.plant(self.scenario(hazard,46,bench_species=6),hazard)
                st=self.turn(st,('RIGHT',));self.consistent(st)
                self.assertEqual(self.transitions,[(0,1)])
                self.assertEqual(hp(st,1),400-damage)
                self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[31,0,0,0])

    def test_spikes_e_stealth_rock_na_mesma_entrada_sem_repetir_etapas(self):
        for bench_hp in (400,100):
            with self.subTest(bench_hp=bench_hp):
                st=bytearray(self.scenario(191,46,bench_hp=bench_hp))
                self.moves(st,old.PARTY,0,(191,445,46,720),(20,20,20,20),old.PLAYER_BATTLE)
                st=self.plant(bytes(st),191)
                st=self.turn(st,('RIGHT',));self.consistent(st)
                self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+13],1)
                self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+12+10],1)
                st=self.turn(st,('LEFT','DOWN'));self.consistent(st)
                self.assertEqual(h.party_pp(st,old.PARTY,0),[19,19,19,20])
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[37,0,0,0])
                self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[31,0,0,0])
                self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
                if bench_hp==400:
                    self.assertEqual(self.transitions,[(0,1)])
                    self.assertEqual(self.losses,[(1,400,350),(1,350,250)])
                    self.assertEqual(party_experience(st),560)
                else:
                    self.assertEqual(self.transitions,[(0,1),(1,0)])
                    self.assertEqual(self.losses,[(1,100,50),(1,50,0),(0,4000,3500),(0,3500,2500)])
                    self.assertEqual(party_experience(st),698)

    def test_ko_pelo_golpe_nao_faz_phazing_adicional(self):
        for hazard,damage in ((191,50),(445,100)):
            for phazer in (521,508):
                with self.subTest(hazard=hazard,phazer=phazer):
                    st=self.plant(self.scenario(hazard,phazer,active_hp=1),hazard)
                    st=self.turn(st,('RIGHT',));self.consistent(st)
                    self.assertEqual(self.transitions,[(0,1)])
                    self.assertEqual(hp(st,0),0)
                    self.assertEqual(hp(st,1),400-damage)
                    self.assertEqual(self.losses,[(0,1,0),(1,400,400-damage)])
                    self.assertFalse(any('arrastado' in text for text in self.seen),self.seen)
                    self.assertTrue(any('desmaiou' in text for text in self.seen),self.seen)
                    self.assertEqual(party_experience(st),698)
                    self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
                    self.assertEqual(h.party_pp(st,old.PARTY,0),[19,19,20,20])
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[31,0,0,0])
                    st=self.turn(st,('LEFT','DOWN'));self.consistent(st)
                    self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[30,0,0,0])

    def test_ko_em_cadeia_pelos_hazards_finaliza_vitoria_e_volta_ao_mapa(self):
        for hazard,damage in ((191,50),(445,100)):
            with self.subTest(hazard=hazard):
                st=bytearray(self.scenario(hazard,46,bench_hp=damage,active_hp=damage*10))
                # HP pequeno e plausível para o jogador: a segunda concessão
                # de EXP cruza o nível 11 e recalcula atributos nativamente.
                for pos in (old.PLAYER_BATTLE+0x2A,old.PLAYER_BATTLE+0x2E,
                            old.offset(old.PARTY)+86,old.offset(old.PARTY)+88):
                    old.put16(st,pos,32)
                st=self.plant(bytes(st),hazard)
                st=self.turn(st,('RIGHT',),require_menu=False)
                self.assertEqual(self.transitions,[(0,1),(1,0)])
                self.assertEqual(self.losses,[(1,damage,0),(0,damage*10,0)])
                # Terminar EXP, quadro de atributos e texto de vitória; não
                # basta observar desmaio ou texto antigo de menu em RAM.
                out=finish_victory(self.f,main_callback2(self.fixture))
                self.assertEqual([hp(out,i) for i in range(2)],[0,0])
                self.assertEqual(party_experience(out),836)
                pos=old.offset(old.PARTY)
                self.assertEqual(out[pos+84],11)
                self.assertGreater(old.u16(out,pos+86),0)
                self.assertLessEqual(old.u16(out,pos+86),old.u16(out,pos+88))
                self.assertEqual(h.party_pp(out,old.PARTY,0),[19,19,20,20])
                self.assertEqual(h.party_pp(out,old.ENEMY_PARTY_ADDR,0),[38,0,0,0])
                self.assertEqual(h.party_pp(out,old.ENEMY_PARTY_ADDR,1),[31,0,0,0])

    def test_ko_por_spikes_nao_aplica_stealth_rock_ao_membro_ja_desmaiado(self):
        st=bytearray(self.scenario(191,46,bench_hp=50))
        self.moves(st,old.PARTY,0,(191,445,46,720),(20,20,20,20),old.PLAYER_BATTLE)
        st=self.plant(bytes(st),191)
        st=self.turn(st,('RIGHT',));self.consistent(st)
        self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+13],1)
        st=self.turn(st,('LEFT','DOWN'));self.consistent(st)
        self.assertEqual(self.transitions,[(0,1),(1,0)])
        self.assertEqual(self.losses,[(1,50,0),(0,4000,3500),(0,3500,2500)])
        self.assertEqual(sum('Pedras pontiagudas feriram' in text for text in self.seen),1)
        self.assertEqual(party_experience(st),698)
        self.assertEqual(old.u16(st,h.LAST_MOVES+2),0)
        self.assertEqual(h.party_pp(st,old.PARTY,0),[19,19,19,20])
        self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,0),[37,0,0,0])
        self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,1),[31,0,0,0])
