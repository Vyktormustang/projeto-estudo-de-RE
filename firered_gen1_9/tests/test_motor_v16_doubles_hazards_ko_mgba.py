"""Hazards/KO adversário em duplas e seleção após dois desmaios do jogador."""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v16_player_hazards_mgba as player
from battle_fixture_helpers import main_callback2, in_battle

old,h,patch=player.old,player.h,player.patch
doubles=player.doubles
ROM=os.environ.get('MOTOR_V16_ROM')
CORE=os.environ.get('MGBA_CORE')


def experience(st,side,slot):
    pos=old.offset(doubles.party_for(side))+100*slot
    block,order,valid=old.decrypted(st[pos:pos+100])
    if not valid:raise ValueError('Checksum inválido')
    return old.u32(block,order[0]*12+4)


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V16_ROM e MGBA_CORE')
class MotorV16DoublesHazardsKOTests(unittest.TestCase):
    _enter_wild_encounter=classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_doubles_fixture=classmethod(old.MotorV10MGBATests._make_doubles_fixture.__func__)
    moves=player.MotorV16PlayerHazardsTests.moves
    begin=player.MotorV16PlayerHazardsTests.begin
    advance=player.MotorV16PlayerHazardsTests.advance
    pulse=player.MotorV16PlayerHazardsTests.pulse
    settle=player.MotorV16PlayerHazardsTests.settle

    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM)
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise ValueError('ROM não é v16 exato')
        cls.temp=tempfile.TemporaryDirectory()
        cls.f=old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture=old.route_entry_fixture(cls.f)
        cls.doubles_fixture=cls._make_doubles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:raise AssertionError('ROM alterada')

    def scenario(self,hazard,phazer=46,actor=0,ko=True,two_faints=False):
        # Sem ator no construtor anterior: todos começam no nível 10/EXP 560.
        # Evita uma subida artificial de nível no controle de um KO adversário.
        st=bytearray(doubles.MotorV16DoublesPhazingTests.scenario(self,-1,150,'mixed'))
        side=actor%2;party=doubles.party_for(side);b=old.bank_off(actor)
        if two_faints:
            self.assertEqual(side,1)
            self.moves(st,party,actor//2,(157,hazard,45,39),(20,1,0,0),b)
            for bank in (0,2):
                old.put16(st,old.bank_off(bank)+0x2A,1)
                old.put16(st,old.offset(old.PARTY)+100*(bank//2)+86,1)
            for slot in (2,3):
                pos=old.offset(old.PARTY)+100*slot
                old.put16(st,pos+86,400);old.put16(st,pos+88,400)
                # Primeiro Protect no turno seguinte isola a continuação
                # do flinch aleatório de Rock Slide contra os novos membros.
                self.moves(st,old.PARTY,slot,(182,150,45,39),(20+slot,0,0,0))
        else:
            self.assertEqual(side,0)
            self.moves(st,party,actor//2,(hazard,phazer,720,150),(20,20,20,20),b)
            pos=old.offset(old.ENEMY_PARTY_ADDR)+200
            old.put16(st,pos+88,400)
            old.put16(st,pos+86,(50 if hazard==191 else 100) if ko else 400)
        # O ator age primeiro, exceto pela prioridade negativa do phazing.
        old.put16(st,b+6,600);old.put16(st,old.offset(party)+100*(actor//2)+94,600)
        self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+12+(1-side)],0)
        self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+12*(1-side)+10],0)
        self.assertEqual(doubles.eligible(st,1-side),{2,3} if two_faints else {2})
        return bytes(st)

    def turn(self,st,choices=None,require_menu=True):
        self.begin(st)
        for directions,target in choices or [((),None),((),None)]:
            self.pulse('A')
            for direction in directions:self.pulse(direction,15)
            self.pulse('A')
            if target is not None:
                if target==3:self.pulse('LEFT',15)
                self.pulse('A')
        self.advance(2000)
        return self.settle(require_menu)

    def consistent(self,st):
        player.MotorV16PlayerHazardsTests.consistent(self,st,True)
        for bank,slot in enumerate(doubles.indexes(st)):
            b=old.bank_off(bank);pos=old.offset(doubles.party_for(bank))+100*slot
            # O cache de EXP do BattlePokemon não é atualizado por getexp;
            # a EXP persistente é conferida separadamente, com checksum.
            self.assertEqual(old.u32(st,b+0x48),560)
            self.assertEqual(old.u32(st,b+0x58),old.u32(st,pos+4))
            self.assertEqual(st[b+0x2C],st[pos+84])

    def plant(self,st,hazard,actor):
        out=self.turn(st);self.consistent(out)
        self.assertEqual(self.transitions,[]);self.assertEqual(self.losses,[])
        side=1-actor%2
        self.assertEqual(out[old.offset(old.V8_STATE_ADDR)+12+side],int(hazard==445))
        self.assertEqual(out[old.offset(old.SIDE_TIMERS_ADDR)+12*side+10],int(hazard==191))
        return out

    def check_pp(self,before,out,uses,drain=None):
        expected={(side,slot):h.party_pp(before,doubles.party_for(side),slot)
                  for side in (0,1) for slot in range(6)}
        for bank,move_slot in uses:expected[bank%2,doubles.indexes(before)[bank]][move_slot]-=1
        if drain is not None:
            bank,move_slot,amount=drain
            expected[bank%2,doubles.indexes(before)[bank]][move_slot]-=amount
        for (side,slot),pps in expected.items():
            self.assertEqual(h.party_pp(out,doubles.party_for(side),slot),pps,(side,slot))

    def check_identities(self,before,out,exp_delta=0):
        for side in (0,1):
            for slot in range(6):
                pos=old.offset(doubles.party_for(side))+100*slot
                self.assertEqual(out[pos:pos+8],before[pos:pos+8])
                self.assertEqual(out[pos+84],before[pos+84])
                self.assertEqual(experience(out,side,slot),experience(before,side,slot)+(exp_delta if side==0 and slot<2 else 0))

    def enemy_entry(self,hazard,phazer,actor,target,ko):
        initial=self.scenario(hazard,phazer,actor,ko)
        st=self.plant(initial,hazard,actor)
        self.check_pp(initial,st,[(bank,1 if bank%2 else 0) for bank in range(4)])
        self.check_identities(initial,st)
        before=st;original=doubles.indexes(st)[target];damage=50 if hazard==191 else 100
        st=self.turn(st,[(('RIGHT',),target) if b==actor else ((),None) for b in (0,2)])
        self.consistent(st)
        changes=[(target,original,2)]+([(target,2,original)] if ko else [])
        self.assertEqual(self.transitions,changes)
        self.assertEqual(player.hp(st,1,2),0 if ko else 400-damage)
        hazard_events=[(1,2,damage,0),(1,original,self.losses[-1][2],self.losses[-1][2]-damage*10)] if ko else [(1,2,400,400-damage)]
        if phazer in (46,18):self.assertEqual(self.losses,hazard_events)
        else:
            self.assertEqual(self.losses[0][:3],(1,original,4000))
            self.assertLess(self.losses[0][3],4000)
            self.assertEqual(self.losses[1:],hazard_events)
        self.check_pp(before,st,[(bank,1 if bank%2 or bank==actor else 0) for bank in range(4)])
        self.check_identities(initial,st,69 if ko else 0)
        self.assertEqual(player.hp(st,1,doubles.indexes(st)[target^2]),4000)
        for bank in range(4):
            self.assertEqual(old.u16(st,h.LAST_MOVES+2*bank),0 if bank==target else phazer if bank==actor else 150)
        # O primeiro Eerie não herda Splash do ocupante anterior; no segundo,
        # o entrante já usou Splash e sofre o dreno de três PP além do uso.
        for repeat in range(2):
            before=st
            st=self.turn(st,[(('LEFT','DOWN') if not repeat else (),target) if b==actor else ((),None) for b in (0,2)])
            self.consistent(st)
            self.assertEqual(self.transitions,[])
            self.check_pp(before,st,[(bank,2 if bank==actor else 1 if bank%2 else 0) for bank in range(4)],(target,1,3) if repeat else None)
            self.assertEqual(old.u16(st,h.LAST_MOVES+2*target),150)
            self.assertEqual(old.u16(st,h.LAST_MOVES+2*actor),720)
            self.check_identities(initial,st,69 if ko else 0)
            self.assertEqual(player.hp(st,1,doubles.indexes(st)[target^2]),4000)
        return st

    def test_entrada_adversaria_sem_ko_e_eerie_nos_dois_bancos(self):
        for hazard in (191,445):
            for actor in (0,2):
                for target in (1,3):
                    with self.subTest(hazard=hazard,actor=actor,target=target):
                        self.enemy_entry(hazard,46,actor,target,False)

    def test_ko_adversario_reposicao_exp_e_historico(self):
        for hazard in (191,445):
            for phazer in doubles.MOVES:
                for actor in (0,2):
                    for target in (1,3):
                        with self.subTest(hazard=hazard,phazer=phazer,actor=actor,target=target):
                            self.enemy_entry(hazard,phazer,actor,target,True)

    def two_replacements(self,hazard,actor,first):
        from test_motor_v7_mgba import GBA_DECODE
        encode={v:k for k,v in GBA_DECODE.items()}
        damage=50 if hazard==191 else 100;second=5-first
        initial=self.scenario(hazard,actor=actor,two_faints=True)
        before=self.plant(initial,hazard,actor);callback=main_callback2(before)
        self.check_pp(initial,before,[(bank,1 if bank%2 else 0) for bank in range(4)])
        st=self.turn(before,require_menu=False)
        menu_callback=main_callback2(st)
        self.assertNotEqual(menu_callback,callback)
        self.assertEqual(self.transitions,[])
        self.assertEqual(self.losses,[(0,0,1,0),(0,1,1,0)])
        self.assertTrue(any('ROCK SLIDE' in text for text in self.seen),self.seen)
        self.pulse('RIGHT')
        if first==3:self.pulse('DOWN')
        self.pulse('A',35);self.pulse('A',35);self.advance(1800)
        second_menu=self.f.state()
        self.assertEqual(main_callback2(second_menu),menu_callback)
        self.assertEqual(self.transitions,[(0,0,first)])
        self.assertEqual(self.losses,[(0,0,1,0),(0,1,1,0),(0,first,400,400-damage)])
        # A primeira entrada já terminou antes da segunda escolha. Tentar
        # enviar de novo o mesmo membro deve produzir a rejeição nativa.
        self.pulse('A',35);self.pulse('A',35);self.advance(120)
        rejected=self.f.state()
        needle=bytes(encode[c] for c in 'em batalha!')
        self.assertNotIn(needle,second_menu[old.offset(0x02000000):old.offset(0x02040000)])
        self.assertIn(needle,rejected[old.offset(0x02000000):old.offset(0x02040000)])
        self.assertEqual(main_callback2(rejected),menu_callback)
        self.assertEqual(doubles.indexes(rejected),doubles.indexes(second_menu))
        for side in (0,1):
            pos=old.offset(doubles.party_for(side))
            self.assertEqual(rejected[pos:pos+600],second_menu[pos:pos+600])
        self.pulse('B',35);self.pulse('RIGHT')
        if second==3:self.pulse('DOWN')
        self.pulse('A',35);self.pulse('A',35);self.advance(2000)
        out=self.settle();self.consistent(out)
        self.assertEqual(main_callback2(out),callback)
        self.assertEqual(self.transitions,[(0,0,first),(2,1,second)])
        self.assertEqual(self.losses,[(0,0,1,0),(0,1,1,0),(0,first,400,400-damage),(0,second,400,400-damage)])
        self.assertEqual(doubles.indexes(out),(first,0,second,1))
        self.check_pp(before,out,[(actor,0),(actor^2,1)])
        self.check_identities(initial,out)
        for bank in range(4):
            self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),0 if bank%2==0 else 157 if bank==actor else 150)
        # Os dois entrantes não herdam a ação escolhida pelos dois mortos.
        # No próximo turno, ambos executam seu próprio Protect pela UI.
        before_next=out
        out=self.turn(out);self.consistent(out)
        self.assertEqual(self.transitions,[]);self.assertEqual(self.losses,[])
        self.assertEqual(doubles.indexes(out),doubles.indexes(before_next))
        self.check_pp(before_next,out,[(bank,0 if bank%2==0 or bank==actor else 1) for bank in range(4)])
        self.check_identities(initial,out)
        for bank in (0,2):self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),182)
        return out

    def test_dois_kos_por_golpe_de_area_selecao_distinta_e_hazard_nas_duas_entradas(self):
        for hazard in (191,445):
            for actor in (1,3):
                for first in (2,3):
                    with self.subTest(hazard=hazard,actor=actor,first=first):
                        self.two_replacements(hazard,actor,first)

    def two_enemy_replacements(self,hazard,actor):
        st=bytearray(self.scenario(hazard,157,actor,False))
        for bank in (1,3):
            old.put16(st,old.bank_off(bank)+0x2A,1)
            old.put16(st,old.offset(old.ENEMY_PARTY_ADDR)+100*(bank//2)+86,1)
        pos=old.offset(old.ENEMY_PARTY_ADDR)+300
        old.put16(st,pos+86,400);old.put16(st,pos+88,400)
        self.assertEqual(doubles.eligible(st,1),{2,3})
        initial=bytes(st);before=self.plant(initial,hazard,actor)
        self.check_pp(initial,before,[(bank,1 if bank%2 else 0) for bank in range(4)])
        out=self.turn(before,[(('RIGHT',),None) if bank==actor else ((),None) for bank in (0,2)])
        self.consistent(out)
        self.assertEqual(len(self.transitions),2)
        self.assertEqual({(bank,old_slot) for bank,old_slot,_ in self.transitions},{(1,0),(3,1)})
        self.assertEqual({new_slot for _,_,new_slot in self.transitions},{2,3})
        damage=50 if hazard==191 else 100
        self.assertEqual(len(self.losses),4)
        self.assertEqual(set(self.losses[:2]),{(1,0,1,0),(1,1,1,0)})
        self.assertEqual(set(self.losses[2:]),{(1,2,400,400-damage),(1,3,400,400-damage)})
        self.check_pp(before,out,[(actor,1),(actor^2,0)])
        self.check_identities(initial,out,138)
        for bank in (1,3):self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),0)
        for slot in (0,1):
            self.assertEqual(player.hp(out,1,slot),0)
            self.assertEqual(player.hp(out,0,slot),4000)
        target=1 if actor==0 else 3
        for repeat in range(2):
            before=out
            out=self.turn(out,[(('LEFT','DOWN') if not repeat else (),target) if bank==actor else ((),None) for bank in (0,2)])
            self.consistent(out);self.assertEqual(self.transitions,[])
            self.check_pp(before,out,[(bank,2 if bank==actor else 1 if bank%2 else 0) for bank in range(4)],(target,1,3) if repeat else None)
            self.check_identities(initial,out,138)
            for bank in (1,3):self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),150)
            self.assertEqual(player.hp(out,1,doubles.indexes(out)[target^2]),400-damage)
        return out

    def test_dois_kos_adversarios_reposicao_distinta_exp_e_dano_de_entrada(self):
        for hazard in (191,445):
            for actor in (0,2):
                with self.subTest(hazard=hazard,actor=actor):
                    self.two_enemy_replacements(hazard,actor)
