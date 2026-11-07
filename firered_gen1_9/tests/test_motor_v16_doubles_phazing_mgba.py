"""Auditoria de phazing em duplas v16: reserva, PP, nível e histórico.

Somente fixtures sintéticas, ROM exata e trocas pela interface/scripts reais.
Não escreve índices de equipe, histórico ou RNG entre turnos.
"""
import os
import tempfile
import unittest
from pathlib import Path
import test_motor_v14_interruptions_mgba as previous
from battle_fixture_helpers import set_party_experience
from scripts import motor_v16 as patch

old, h = previous.old, previous.h
ROM = os.environ.get('MOTOR_V16_ROM')
CORE = os.environ.get('MGBA_CORE')
INDEX = old.offset(old.PARTY_INDEXES_ADDR)
MOVES = (46,18,521,508)


def indexes(st):
    return tuple(old.u16(st,INDEX+2*b) for b in range(4))


def party_for(bank):
    return old.PARTY if bank%2==0 else old.ENEMY_PARTY_ADDR


def eligible(st,side):
    active={indexes(st)[side],indexes(st)[side+2]}
    party=party_for(side)
    valid=set()
    for slot in range(6):
        pos=old.offset(party)+100*slot
        block,order,ok=old.decrypted(st[pos:pos+100])
        if not ok:raise ValueError('Checksum inválido')
        species=old.u16(block,order[0]*12)
        egg=bool(old.u32(block,order[3]*12+4)&(1<<30))
        if species and not egg and old.u16(st,pos+86)>0 and slot not in active:
            valid.add(slot)
    return valid


@unittest.skipUnless(ROM and CORE,'defina MOTOR_V16_ROM e MGBA_CORE')
class MotorV16DoublesPhazingTests(unittest.TestCase):
    _enter_wild_encounter=classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_doubles_fixture=classmethod(old.MotorV10MGBATests._make_doubles_fixture.__func__)
    turn=previous.MotorV14DoublesInterruptionTests.turn

    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM)
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:
            raise ValueError('ROM não é v16 exato')
        cls.temp=tempfile.TemporaryDirectory()
        cls.f=old.Emulator(cls.rom,Path(CORE),Path(cls.temp.name))
        cls.fixture=old.route_entry_fixture(cls.f)
        cls.doubles_fixture=cls._make_doubles_fixture()

    @classmethod
    def tearDownClass(cls):
        cls.f.close();cls.temp.cleanup()
        if patch.digest(cls.rom.read_bytes())!=patch.OUTPUT_SHA256:
            raise AssertionError('ROM alterada')

    def scenario(self,actor,move,mode='many'):
        st=bytearray(self.doubles_fixture)
        self.assertEqual(st[old.offset(0x020213F4)],4)
        self.assertEqual(indexes(st),(0,0,1,1))
        # Contexto sintético de treinador em duplas, não batalha link/multi.
        old.put32(st,old.offset(0x02020374),old.u32(st,old.offset(0x02020374))|8)
        for side,party in ((0,old.PARTY),(1,old.ENEMY_PARTY_ADDR)):
            for slot in range(6):
                pos=old.offset(party)+100*slot
                if slot==5 or (mode=='none' and slot==4):
                    st[pos:pos+100]=bytes(100)
                    continue
                bank=side+2*slot if slot<2 else None
                level=5 if bank==actor else 10
                egg=(mode=='mixed' and slot==4) or (mode=='none' and slot==3)
                seed=bytearray(old.seed_mon(self.fixture,4,level,(150,33,45,39),egg=egg))
                # Charmander, curva medium-slow: nível 5=135; nível 10=560.
                set_party_experience(seed,135 if level==5 else 560)
                source=old.offset(old.PARTY)
                st[pos:pos+100]=seed[source:source+100]
                dead=(mode=='mixed' and slot==3) or (mode=='none' and slot==2)
                hp=0 if dead else 4000
                for off,value in ((86,hp),(88,4000),(90,30),(92,200),
                                  (94,600 if bank==actor else 100),(96,30),(98,200)):
                    old.put16(st,pos+off,value)
                old.put32(st,pos+80,0)
                if bank==actor:
                    moves=(move,720,45,39) if side==0 else (33,move,45,39)
                    pps=(20,5,0,0) if side==0 else (0,20,0,0)
                else:
                    moves=(150,33,45,39) if side==0 else (33,150,45,39)
                    pps=(20+slot,0,0,0) if side==0 else (0,20+slot,0,0)
                h.set_moves(st,party,slot,moves,pps)
                # Identidades distintas, mantendo PID % 24 e a ordem dos blocos.
                data=bytearray(st[pos:pos+100])
                block,order,valid=old.decrypted(data)
                self.assertTrue(valid)
                pid=(old.u32(data,0)%24)+24*(100+side*6+slot)
                old.put32(data,0,pid)
                key=pid^old.u32(data,4)
                for off in range(0,48,4):old.put32(data,32+off,old.u32(block,off)^key)
                st[pos:pos+100]=data
                if bank is not None:
                    b=old.bank_off(bank)
                    old.put16(st,b,4)
                    old.put32(st,b+0x14,old.u32(block,order[3]*12+4))
                    old.put32(st,b+0x48,old.u32(block,order[0]*12+4))
                    old.put32(st,b+0x4C,pid)
                    old.put32(st,b+0x58,old.u32(data,4))
                    for i,mid in enumerate(moves):
                        old.put16(st,b+12+2*i,mid);st[b+0x25+i]=pps[i]
                    for bo,po in ((2,90),(4,92),(6,94),(8,96),(10,98),(0x2A,86),(0x2E,88)):
                        old.put16(st,b+bo,old.u16(st,pos+po))
                    st[b+0x2C]=level
                    st[b+0x20]=4
                    st[b+0x22]=st[b+0x23]=0
                    for i in range(1,8):st[b+0x18+i]=6
                    st[b+0x1E]=12
                    old.put16(st,b+0x30,0)
                    old.put32(st,b+0x50,0);old.put32(st,b+0x54,0)
                    self.assertEqual(old.u16(st,h.LAST_MOVES+2*bank),0)
            st[old.offset(old.PLAYER_PARTY_COUNT if side==0 else old.ENEMY_PARTY_COUNT)]=5
        return bytes(st)

    def consistent(self,before,after):
        for side in (0,1):
            party=party_for(side)
            for slot in range(6):
                pos=old.offset(party)+100*slot
                self.assertEqual(after[pos+84],before[pos+84])
                a,oa,va=old.decrypted(before[pos:pos+100])
                b,ob,vb=old.decrypted(after[pos:pos+100])
                self.assertTrue(va and vb)
                self.assertEqual(old.u32(a,oa[0]*12+4),old.u32(b,ob[0]*12+4))
        for bank,slot in enumerate(indexes(after)):
            b=old.bank_off(bank);party=party_for(bank);pos=old.offset(party)+100*slot
            block,order,_=old.decrypted(after[pos:pos+100])
            self.assertEqual(old.u32(after,b+0x4C),old.u32(after,pos))
            self.assertEqual(old.u32(after,b+0x48),old.u32(block,order[0]*12+4))
            self.assertEqual(old.u32(after,b+0x58),old.u32(after,pos+4))
            self.assertEqual(after[b+0x2C],after[pos+84])
            self.assertEqual(list(after[b+0x25:b+0x29]),h.party_pp(after,party,slot))
            self.assertEqual(old.u16(after,b+0x2A),old.u16(after,pos+86))
        self.assertNotEqual(indexes(after)[0],indexes(after)[2])
        self.assertNotEqual(indexes(after)[1],indexes(after)[3])

    def pp_turn(self,before,after,actor,eerie=False,drain=None):
        expected={(side,slot):h.party_pp(before,party_for(side),slot)
                  for side in (0,1) for slot in range(6)}
        for bank,slot in enumerate(indexes(before)):
            move_slot=1 if bank%2 else (1 if bank==actor and eerie else 0)
            expected[bank%2,slot][move_slot]-=1
        if drain is not None:expected[drain%2,indexes(before)[drain]][1]-=3
        for (side,slot),pps in expected.items():
            self.assertEqual(h.party_pp(after,party_for(side),slot),pps,(side,slot))

    def phaze(self,st,actor,move,target=None,success=True):
        before=indexes(st)
        choices=[(None,target if bank==actor else None) for bank in (0,2)]
        out,marks,_=self.turn(st,choices)
        self.assertEqual(marks,[])
        self.consistent(st,out);self.pp_turn(st,out,actor)
        changed=[b for b in range(4) if indexes(out)[b]!=before[b]]
        if success:
            self.assertEqual(len(changed),1)
            victim=changed[0]
            self.assertEqual(victim%2,1-actor%2)
            if target is not None:self.assertEqual(victim,target)
            self.assertIn(indexes(out)[victim],eligible(st,victim%2))
            self.assertEqual(old.u16(out,h.LAST_MOVES+2*victim),0)
        else:
            self.assertEqual(changed,[])
            victim=None
        for bank in range(4):
            if bank!=victim:self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),move if bank==actor else 150)
        return out,victim

    def test_jogadores_0_2_alvos_1_3_com_multiplas_reservas(self):
        for move in MOVES:
            for actor in (0,2):
                for target in (1,3):
                    with self.subTest(move=move,actor=actor,target=target):
                        st=self.scenario(actor,move)
                        self.assertEqual(eligible(st,1),{2,3,4})
                        for _ in range(2):st,_=self.phaze(st,actor,move,target)

    def test_adversarios_1_3_nunca_escolhem_os_dois_ativos(self):
        for move in MOVES:
            for actor in (1,3):
                with self.subTest(move=move,actor=actor):
                    st=self.scenario(actor,move)
                    self.assertEqual(eligible(st,0),{2,3,4})
                    for _ in range(2):st,_=self.phaze(st,actor,move)

    def test_reserva_unica_exclui_desmaiado_ovo_e_slot_vazio(self):
        for move in MOVES:
            for actor in range(4):
                with self.subTest(move=move,actor=actor):
                    st=self.scenario(actor,move,'mixed')
                    self.assertEqual(eligible(st,1-actor%2),{2})
                    out,victim=self.phaze(st,actor,move,1 if actor%2==0 else None)
                    self.assertEqual(indexes(out)[victim],2)

    def test_sem_reserva_elegivel_nao_troca_nem_encerra_batalha(self):
        for move in MOVES:
            for actor in range(4):
                with self.subTest(move=move,actor=actor):
                    st=self.scenario(actor,move,'none')
                    self.assertEqual(eligible(st,1-actor%2),set())
                    st,_=self.phaze(st,actor,move,1 if actor%2==0 else None,success=False)
                    self.assertEqual(st[old.offset(0x020216C8)],0)

    def test_eerie_usa_historico_do_entrante_nao_do_banco_anterior(self):
        for actor in (0,2):
            for target in (1,3):
                with self.subTest(actor=actor,target=target):
                    st=self.scenario(actor,521)
                    st,_=self.phaze(st,actor,521,target)
                    for repeat in range(2):
                        before=st
                        choices=[('RIGHT' if repeat==0 else None,target) if bank==actor else (None,None)
                                 for bank in (0,2)]
                        st,marks,_=self.turn(st,choices)
                        self.assertEqual(marks,[])
                        self.assertEqual(indexes(st),indexes(before))
                        self.consistent(before,st)
                        self.pp_turn(before,st,actor,eerie=True,drain=target if repeat else None)
                        self.assertLess(old.u16(st,old.bank_off(target)+0x2A),old.u16(before,old.bank_off(target)+0x2A))
                        self.assertEqual(old.u16(st,h.LAST_MOVES+2*target),150)
                        self.assertEqual(old.u16(st,h.LAST_MOVES+2*actor),720)
