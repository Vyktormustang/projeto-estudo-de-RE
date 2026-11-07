"""Testes de Hard Press e da TM225: somente estados e saves sintéticos.

MOTOR_TEST_ROM=rom_mod/motor_ampliado_rascunho.gba \
MOTOR_TEST_BASE=rom_mod/estojo_expandido_rascunho.gba \
MGBA_CORE=/tmp/mgba-build/mgba_libretro.so \
python3 -m unittest discover -s tests -p 'test_motor_ampliado*.py' -v
"""
from __future__ import annotations
import ctypes as C
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from mgba_treino_harness import Emulator,PARTY,offset,u32,mon,mon_facts
from test_eventos_fixos_mgba import route_entry_fixture,route_from_entry,enemy
from test_golpes_gen9_mgba import invoke,moves,seed_mon
from test_golpes_gen9_integracao import set_exp_and_test_stats,load_game
from test_atualizacoes_gen9_mgba import PLAYER_BATTLE,FOE_BATTLE
from test_estojo_expandido_mgba import add,get,open_case,page,extension,save1,save2,save_after_case
from scripts import atualizacoes_gen9 as previous
from scripts import motor_ampliado as patch
ROM=os.environ.get('MOTOR_TEST_ROM');BASE=os.environ.get('MOTOR_TEST_BASE');CORE=os.environ.get('MGBA_CORE')
CAN=0x080f8460

def call(f,state,fn,*args):
    return u32(invoke(f,state,fn,{i:a for i,a in enumerate(args)}),0x20)

def stored_quantity(state,item):
    if item>=375:
        data=extension(state);bit=(item-375)*10;pos=4+bit//8
        return ((data[pos]|data[pos+1]<<8)>>(bit%8))&1023
    key=struct.unpack_from('<H',state,offset(save2(state)+0xf24))[0]
    raw=state[offset(save1(state)+0x464):offset(save1(state)+0x54c)]
    return next((count^key for identifier,count in struct.iter_unpack('<HH',raw) if identifier==item),0)

@unittest.skipUnless(ROM and BASE and CORE,'defina MOTOR_TEST_ROM, MOTOR_TEST_BASE e MGBA_CORE')
class MotorMGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM).resolve();cls.base=Path(BASE).resolve();cls.core=Path(CORE).resolve()
        if cls.rom.read_bytes()!=patch.build(cls.base.read_bytes()):raise ValueError('ROM diverge da reconstrução')
        cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
        cls.f=Emulator(cls.rom,cls.core,cls.dir);cls.fixture=route_entry_fixture(cls.f)
    @classmethod
    def tearDownClass(cls):cls.f.close();cls.temp.cleanup()
    def setUp(self):self.f.restore(self.fixture)
    def extra_core(self,tag):
        path=self.dir/f'{tag}.so'
        if not path.exists():shutil.copyfile(self.core,path)
        return path
    def battle(self):
        state=seed_mon(self.fixture,917,5,(807,0,0,0));set_exp_and_test_stats(state,179,12)
        self.f.restore(bytes(state));route_from_entry(self.f)
        for _ in range(120):
            self.f.run(20,'LEFT');self.f.run(20,'RIGHT');wild=enemy(self.f.state())
            if wild['valid'] and wild['species']!=390:
                self.f.run(350);return bytearray(self.f.state())
        self.fail('Sem encontro no teste')
    def test_compatibilidade_tecnica_e_legados(self):
        for species,known,egg,expected in ((151,0,False,0),(75,0,False,0),(10,0,False,1),
                                           (151,807,False,2),(151,0,True,3)):
            with self.subTest(species=species,known=known,egg=egg):
                state=seed_mon(self.fixture,species,5,(33,45,known,0),egg)
                out=invoke(self.f,state,0x080f8460,{0:PARTY,1:599,2:0})
                self.assertEqual(u32(out,0x20),expected)
        state=seed_mon(self.fixture,1,5,(33,45,0,0))
        for item in (294,342,394):
            out=invoke(self.f,state,0x080f8460,{0:PARTY,1:item,2:0})
            self.assertEqual(u32(out,0x20),0)
    def test_hard_press_poder_arredondamento_limites_e_categoria(self):
        saved=self.battle();saved[offset(0x020215a8)]=0;saved[offset(0x020215a9)]=1
        for who in (PLAYER_BATTLE,FOE_BATTLE):
            for i in range(1,8):saved[who+0x18+i]=6
            struct.pack_into('<H',saved,who+0x20,0);struct.pack_into('<H',saved,who+0x30,0)
            struct.pack_into('<I',saved,who+0x50,0)
        def calc(hp,maximum,atk=100,spa=100):
            state=bytearray(saved)
            struct.pack_into('<H',state,offset(0x02021586),807)
            struct.pack_into('<H',state,offset(0x02021792),0)
            struct.pack_into('<HH',state,FOE_BATTLE+0x2a,hp,0)
            struct.pack_into('<H',state,FOE_BATTLE+0x2e,maximum)
            struct.pack_into('<H',state,PLAYER_BATTLE+2,atk);struct.pack_into('<H',state,PLAYER_BATTLE+8,spa)
            struct.pack_into('<H',state,FOE_BATTLE+4,100);struct.pack_into('<H',state,FOE_BATTLE+10,100)
            out=invoke(self.f,state,0x0900c000,{})
            return struct.unpack_from('<H',out,offset(0x02021792))[0],struct.unpack_from('<i',out,offset(0x0202158c))[0]
        cases=((200,200,100),(199,200,99),(100,200,50),(69,200,34),(68,200,34),
               (67,200,33),(1,500,1),(0,200,1),(0,0,1),(201,200,100))
        for hp,maximum,want in cases:
            with self.subTest(hp=hp,maximum=maximum):self.assertEqual(calc(hp,maximum)[0],want)
        self.assertGreater(calc(200,200)[1],calc(100,200)[1])
        self.assertGreater(calc(200,200,300,10)[1],calc(200,200,10,300)[1])
    def test_animacao_classifica_itens_sem_incluir_ids_intermediarios(self):
        # Confere as duas implementações: a inline e a função independente.
        data=bytearray(self.rom.read_bytes());data[0x114a00:0x114a02]=b'\xfe\xe7'
        path=self.dir/'animacao_instrumentada.gba';path.write_bytes(data)
        f=Emulator(path,self.extra_core('animation'),self.dir)
        try:
            for item in (*range(604),604,65535):
                expected=1 if item==13 else 4 if 289<=item<=346 or 375<=item<=603 else 0
                with self.subTest(item=item):
                    out=invoke(f,self.fixture,0x081149e4,{5:item},expected=0x08114a00)
                    self.assertEqual(u32(out,0x20+3*4),expected)
                    self.assertEqual(call(f,self.fixture,0x08115344,item),expected)
        finally:f.close()

    def test_registro_de_aventuras_distingue_tm_e_hm(self):
        for item in (294,339,340,341,342,343,344,345,346,394,599):
            for replaced in (0xffff,33):
                with self.subTest(item=item,replaced=replaced):
                    s=bytearray(self.fixture)
                    struct.pack_into('<H',s,offset(0x0203af1e),0)
                    struct.pack_into('<HHHHH',s,offset(0x02001000),0,0,item,1,replaced)
                    out=invoke(self.f,s,0x0812c310,{0:0x02001000})
                    raw=out[offset(0x0203e6c4):offset(0x0203e6c4)+512]
                    message=raw[:raw.index(b'\xff')]
                    want='HM' if 339<=item<=346 else 'TM'
                    other='TM' if want=='HM' else 'HM'
                    self.assertIn(previous.text(want)[:-1],message)
                    self.assertNotIn(previous.text(other)[:-1],message)

    def test_tres_caminhos_de_consumo_todas_as_hms_e_tms(self):
        # Instrumenta somente os finais de três blocos em uma cópia de teste,
        # sem alterar as instruções reais de classificação/remoção. Assim cada
        # caminho roda na CPU ARM com IDs de fronteira e volta a um laço local.
        data=bytearray(self.rom.read_bytes())
        traps=(0x0fccd0,0x0fcd96,0x0fdd0e)
        for at in traps:data[at:at+2]=b'\xfe\xe7'  # b .
        data[0x0fdd04:0x0fdd06]=b'\x03\xd9'      # bls ao laço local
        path=self.dir/'consumo_instrumentado.gba';path.write_bytes(data)
        f=Emulator(path,self.extra_core('consumption'),self.dir)
        try:
            scratch=0x02001000
            for site,trap in zip((0x080fccb8,0x080fcd7c,0x080fdcfc),traps):
                for item in (289,294,338,*range(339,347),375,394,599,603):
                    with self.subTest(site=hex(site),item=item):
                        state=add(f,self.fixture,item,2)
                        state=bytearray(state)
                        struct.pack_into('<H',state,offset(scratch),item)
                        struct.pack_into('<I',state,offset(scratch+4),0x08056aaf)
                        if site==0x080fccb8:regs={4:scratch,6:scratch+4}
                        elif site==0x080fcd7c:regs={8:scratch,4:scratch+4}
                        else:regs={7:item}
                        out=invoke(f,state,site,regs,expected=0x08000000+trap)
                        self.assertEqual(get(f,out,item),2 if 339<=item<=346 else 1)
        finally:f.close()

    def test_ensino_por_interface_consumo_e_hm_preservada(self):
        for item,move,count,expected in ((394,797,2,1),(294,92,2,1),(342,70,1,1)):
            with self.subTest(item=item):
                s=add(self.f,self.fixture,item,count);self.f.restore(s);open_case(self.f)
                if item>=375:self.f.pulse('R',100)
                for _ in range(18):
                    self.f.pulse('A',90)
                    if move in moves(self.f.state()):break
                self.assertIn(move,moves(self.f.state()))
                # A notificação e o consumo acontecem após gravar o golpe.
                for _ in range(8):
                    self.f.pulse('A',100)
                    if stored_quantity(self.f.state(),item)==expected:break
                out=self.f.state()
                self.assertEqual(get(self.f,out,item),expected)
                self.assertTrue(mon_facts(mon(out))['valid'])

    def test_substituir_um_dos_quatro_golpes_consume_uma_tm(self):
        s=seed_mon(self.fixture,1,5,(33,45,22,73))
        s=add(self.f,s,394,2);self.f.restore(s);open_case(self.f);self.f.pulse('R',100)
        for _ in range(40):
            self.f.pulse('A',90)
            out=self.f.state()
            if 797 in moves(out) and stored_quantity(out,394)==1:break
        self.assertIn(797,moves(out));self.assertEqual(stored_quantity(out,394),1)
        self.assertTrue(mon_facts(mon(out))['valid'])

    def test_nomes_longos_na_animacao_sem_corromper_pokemon(self):
        # Stomping Tantrum tem 16 caracteres; teste-o tanto como golpe novo
        # quanto como golpe esquecido, em que há dois buffers lado a lado.
        for item,new_move,initial in ((458,653,(33,45,22,73)),(394,797,(653,45,22,73))):
            with self.subTest(item=item):
                s=seed_mon(self.fixture,151,5,initial)
                self.assertEqual(call(self.f,s,CAN,PARTY,item,0),0)
                s=add(self.f,s,item,1);self.f.restore(s);open_case(self.f);self.f.pulse('R',100)
                for _ in range(50):
                    self.f.pulse('A',90);out=self.f.state()
                    self.assertTrue(mon_facts(mon(out))['valid'])
                    if new_move in moves(out) and stored_quantity(out,item)==0:break
                self.assertIn(new_move,moves(out));self.assertEqual(stored_quantity(out,item),0)

    def test_nao_consume_tm_se_golpe_ja_conhecido(self):
        s=seed_mon(self.fixture,1,5,(797,45,22,0))
        s=add(self.f,s,394,1);self.f.restore(s);open_case(self.f);self.f.pulse('R',100)
        for _ in range(12):self.f.pulse('A',90)
        out=self.f.state()
        self.assertEqual(moves(out),(797,45,22,0))
        self.assertEqual(stored_quantity(out,394),1)

    def test_nao_consume_tm_se_pokemon_incompativel(self):
        s=seed_mon(self.fixture,10,5,(33,45,22,0))
        s=add(self.f,s,394,1);self.f.restore(s);open_case(self.f);self.f.pulse('R',100)
        for _ in range(12):self.f.pulse('A',90)
        out=self.f.state()
        self.assertEqual(moves(out),(33,45,22,0))
        self.assertEqual(get(self.f,out,394),1)

    def test_hard_press_batalha_real(self):
        state=self.battle()
        struct.pack_into('<H',state,FOE_BATTLE+0x2a,250)
        struct.pack_into('<H',state,FOE_BATTLE+0x2e,500)
        state[FOE_BATTLE+0x22:FOE_BATTLE+0x24]=b'\0\0'
        self.f.restore(bytes(state));seen=False;damage=False
        for i in range(2200):
            self.f.run(1)
            if i%35==0:self.f.pulse('A',1)
            out=self.f.state()
            if struct.unpack_from('<H',out,offset(0x02021792))[0]==50:seen=True
            hp=struct.unpack_from('<H',out,FOE_BATTLE+0x2a)[0]
            if seen and hp<250:damage=True;break
        self.assertTrue(seen,'Poder 50 não observado durante o ataque')
        self.assertTrue(damage,'HP do alvo não diminuiu')
    def test_loja_compra_ensina_consume_e_salva_tm225(self):
        # Placa de teste teletransporta à loja; todo o restante é original.
        data=bytearray(self.rom.read_bytes());self.assertEqual(data[0xf90000:0xf9000a],b'\xff'*10)
        struct.pack_into('<I',data,0x7c20d8,0x08f90000)
        data[0xf90000:0xf9000a]=struct.pack('<BBBBHHBB',0x39,3,0,0xff,4,8,0x27,0x02)
        path=self.dir/'loja_motor.gba';path.write_bytes(data)
        f=Emulator(path,self.extra_core('shop'),self.dir)
        try:
            f.restore(bytes(seed_mon(self.fixture,151,5,(33,45,22,0))));route_from_entry(f)
            f.run(64,'LEFT');f.run(30);f.run(5,'UP');f.run(25)
            f.pulse('A',150);f.run(150);f.run(4,'UP');f.run(20);f.pulse('A',100)
            for _ in range(20):
                f.pulse('A',60)
                if struct.pack('<I',0x08e18300) in f.state()[0x21000:0x61000]:break
            else:self.fail('Loja não abriu')
            f.pulse('A',120)
            f.run(3000,'DOWN');f.run(40)
            # A última TM oferecida é a TM225; depois vem Cancelar.
            f.pulse('UP',80)
            for _ in range(8):f.pulse('A',90)
            after_buy=f.state()
            self.assertEqual(get(f,after_buy,599),1)
            f.restore(after_buy)  # invocar a função desloca o PC; restaura antes da UI
            for _ in range(5):f.pulse('B',90)
            open_case(f);self.assertEqual(page(f.state()),0)
            f.pulse('R',80);f.pulse('R',80);self.assertEqual(page(f.state()),2)
            for _ in range(15):
                f.pulse('A',90)
                if moves(f.state())[-1]==807:break
            # A rotina primeiro grava o golpe e, algumas telas depois, retira
            # a TM. Ler os bits diretamente evita deslocar o PC ao consultar.
            for _ in range(8):
                f.pulse('A',90)
                current=f.state();packed=extension(current)
                bit=(599-375)*10;pos=4+bit//8
                quantity=((packed[pos]|packed[pos+1]<<8)>>(bit%8))&1023
                if quantity==0:break
            after_teach=f.state()
            self.assertEqual(moves(after_teach),(33,45,22,807))
            self.assertEqual(quantity,0)
            self.assertEqual(get(f,after_teach,599),0);self.assertTrue(mon_facts(mon(after_teach))['valid'])
            f.restore(after_teach)
            flash=save_after_case(f)
        finally:f.close()
        loaded=Emulator(self.rom,self.extra_core('reload'),self.dir)
        try:
            state=load_game(loaded,flash)
            self.assertEqual(moves(state),(33,45,22,807))
            self.assertEqual(get(loaded,state,599),0)
        finally:loaded.close()
