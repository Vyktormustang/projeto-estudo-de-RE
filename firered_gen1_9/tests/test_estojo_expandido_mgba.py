"""mGBA 0.10.5, exclusivamente dados/saves sintéticos.

ESTOJO_TEST_ROM=rom_mod/estojo_expandido_rascunho.gba \
ESTOJO_TEST_BASE=rom_mod/ptbr_gen1-9_complemento_parcial_32mb.gba \
MGBA_CORE=/tmp/mgba-build/mgba_libretro.so \
python3 -m unittest discover -s tests -p 'test_estojo_expandido_mgba.py' -v
"""
from __future__ import annotations
import ctypes as C
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from mgba_treino_harness import Emulator, offset, u16, u32, put16, mon, mon_facts
from test_eventos_fixos_mgba import route_entry_fixture, route_from_entry
from test_golpes_gen9_mgba import invoke, moves
from test_golpes_gen9_integracao import save_game, load_game
from test_atualizacoes_gen9_mgba import pocket,pocket_ids,copy_ewram
from scripts import estojo_expandido as p

ROM=os.environ.get('ESTOJO_TEST_ROM');BASE=os.environ.get('ESTOJO_TEST_BASE');CORE=os.environ.get('MGBA_CORE')
ADD=0x080C69A4; REMOVE=0x080C6B38; HAS=0x080C6848; SPACE=0x080C68FC; QTY=0x080C7100
STATIC=0x0203F06C

def save1(state):
    # IWRAM serializada pelo mGBA 0.10.5 começa em 0x19000.
    return u32(state,0x19000+0x6f94)

def save2(state):return u32(state,0x19000+0x6f98)

def extension(state):return state[offset(save1(state)+0x34d8):offset(save1(state)+0x3668)]

def call(f,state,addr,item,count=None):
    args={0:item}
    if count is not None:args[1]=count
    out=invoke(f,bytes(state),addr,args)
    return u32(out,0x20),copy_ewram(state,out)

def add(f,state,item,count=1):
    result,out=call(f,state,ADD,item,count)
    if result!=1:raise AssertionError(f'Não inseriu item {item} x{count}')
    return out

def get(f,state,item):return call(f,state,QTY,item)[0]

def open_case(f):
    f.pulse('START',80);f.pulse('DOWN',35);f.pulse('A',110);f.pulse('RIGHT',70)
    f.pulse('A',90);f.pulse('A',120)

def page(state):return state[offset(STATIC+6)]

def save_after_case(f):
    for _ in range(6):f.pulse('B',80)
    f.pulse('START',80)
    # o cursor ficou em Bolsa depois do estojo
    for _ in range(3):f.pulse('DOWN',35)
    for _ in range(15):f.pulse('A',100)
    ptr=f.core.core.retro_get_memory_data(0);size=f.core.core.retro_get_memory_size(0)
    if not ptr or size!=131072:raise AssertionError('Flash sintética indisponível')
    data=C.string_at(ptr,size)
    if len(set(data))<=2:raise AssertionError('Jogo não salvou')
    return data

@unittest.skipUnless(ROM and BASE and CORE,'defina ESTOJO_TEST_ROM, ESTOJO_TEST_BASE e MGBA_CORE')
class EstojoMGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=Path(ROM).resolve();cls.base=Path(BASE).resolve();cls.core=Path(CORE).resolve()
        if p.digest(cls.base.read_bytes())!=p.BASE_SHA256:raise ValueError('ROM de entrada incompatível')
        if cls.rom.read_bytes()!=p.build(cls.base.read_bytes()):raise ValueError('ROM de saída diverge do patch')
        cls.temp=tempfile.TemporaryDirectory();cls.dir=Path(cls.temp.name)
        cls.f=Emulator(cls.rom,cls.core,cls.dir);cls.fixture=route_entry_fixture(cls.f)
    @classmethod
    def tearDownClass(cls):cls.f.close();cls.temp.cleanup()
    def setUp(self):self.f.restore(self.fixture)
    def extra_core(self,tag):
        path=self.dir/f'{tag}.so'
        if not path.exists():shutil.copyfile(self.core,path)
        return path
    def launch(self,path,tag):return Emulator(path,self.extra_core(tag),self.dir)

    def test_limite_58_removido_58_legadas_mais_229_modernas(self):
        s=self.fixture
        # Todas as 50 TMs e 8 HMs antigas, e também 229 novos IDs (inclusive
        # os 26 reservados ainda não oferecidos, para testar o armazenamento).
        for item in range(289,347):s=add(self.f,s,item)
        berry_before=s[offset(save1(s)+0x54c):offset(save1(s)+0x5f8)]
        for item in range(375,604):s=add(self.f,s,item,(item*7)%997+1)
        self.assertEqual(extension(s)[:4],b'T9X1')
        self.assertEqual(set(pocket_ids(s)),set(range(289,347)))
        self.assertEqual(s[offset(save1(s)+0x54c):offset(save1(s)+0x5f8)],berry_before)
        for item in range(289,347):self.assertEqual(get(self.f,s,item),1)
        for item in range(375,604):self.assertEqual(get(self.f,s,item),(item*7)%997+1)
        result,s2=call(self.f,s,ADD,375,1000)
        self.assertEqual(result,0);self.assertEqual(get(self.f,s2,375),get(self.f,s,375))

    def test_quantidades_limites_e_operacoes_sem_interferir_nas_vizinhas(self):
        s=add(self.f,self.fixture,394,998);s=add(self.f,s,395,17);s=add(self.f,s,396,777)
        for op,item,n,want in ((HAS,394,998,1),(HAS,394,999,0),(SPACE,394,1,1),
                               (SPACE,394,2,0),(ADD,394,1,1),(ADD,394,1,0),
                               (REMOVE,394,1000,0),(REMOVE,394,999,1),(REMOVE,394,1,0)):
            result,s=call(self.f,s,op,item,n);self.assertEqual(result,want,(hex(op),item,n))
        self.assertEqual(get(self.f,s,394),0);self.assertEqual(get(self.f,s,395),17)
        self.assertEqual(get(self.f,s,396),777)
        self.assertEqual(call(self.f,s,REMOVE,395,7)[0],1)

    def test_migracao_de_58_slots_antigos_e_espaco_desconhecido(self):
        # Usa as rotinas reais da ROM anterior para produzir uma mochila antiga.
        old=self.launch(self.base,'old_slots')
        try:
            s=self.fixture
            for item,count in ((294,3),(342,1),(394,9),(598,4),(375,999),(139,2),(13,2)):
                s=add(old,s,item,count)
            before=s
        finally:old.close()
        self.assertIn(394,pocket_ids(before));self.assertEqual(extension(before),b'\0'*400)
        val,after=call(self.f,before,HAS,394,9)
        self.assertEqual(val,1);self.assertEqual(extension(after)[:4],b'T9X1')
        self.assertEqual(get(self.f,after,394),9);self.assertEqual(get(self.f,after,598),4)
        self.assertEqual(get(self.f,after,375),999);self.assertEqual(get(self.f,after,294),3)
        self.assertEqual(get(self.f,after,342),1);self.assertEqual(get(self.f,after,139),2)
        self.assertNotIn(394,pocket_ids(after));self.assertIn(342,pocket_ids(after))
        self.assertEqual(mon(after),mon(before))
        # Trecho não reconhecido não pode ser sobrescrito. A rotina antiga
        # continua atendendo itens que já estavam nos 58 slots físicos.
        unknown=bytearray(before);unknown[offset(save1(unknown)+0x34d8+123)]=0x5a
        val,out=call(self.f,unknown,HAS,394,9)
        self.assertEqual(val,1);self.assertEqual(extension(out),extension(unknown))
        self.assertEqual(pocket_ids(out),pocket_ids(unknown))
        result,out=call(self.f,unknown,ADD,395,2)
        self.assertEqual(result,1);self.assertEqual(extension(out),extension(unknown))
        self.assertIn(395,pocket_ids(out))

    def test_paginas_ensino_e_restauracao_da_opcao_ajuda(self):
        s=self.fixture
        for item in (294,342,394,598):s=add(self.f,s,item)
        self.f.restore(s);self.assertEqual(self.f.state()[offset(save2(s)+0x13)],0)
        open_case(self.f);out=self.f.state()
        self.assertEqual(page(out),0);self.assertEqual(out[offset(save2(out)+0x13)],1)
        self.assertEqual(set(x for x in pocket_ids(out) if x),{294,342})
        self.f.pulse('R',150);out=self.f.state()
        self.assertEqual(page(out),1);self.assertEqual([i for i in pocket_ids(out) if i],[394])
        self.f.pulse('R',150);out=self.f.state()
        self.assertEqual(page(out),2);self.assertEqual([i for i in pocket_ids(out) if i],[598])
        self.f.pulse('L',150);out=self.f.state()
        self.assertEqual(page(out),1);self.assertEqual([i for i in pocket_ids(out) if i],[394])
        # Usa a TM pela interface real, sem atalhos na rotina de ensino.
        # Four known moves require the native forget/summary prompts too.
        for _ in range(30):
            self.f.pulse('A',90);out=self.f.state()
            if 797 in moves(out): break
        else: self.fail('TM não ensinou Trailblaze')
        # A full moveset may already return to the case after forgetting a
        # move. Close normally before asserting restored help/pocket state.
        from battle_fixture_helpers import main_callback2
        for _ in range(8):
            self.f.pulse('B',80);out=self.f.state()
            if main_callback2(out)==main_callback2(self.fixture):break
        self.assertEqual(main_callback2(out),main_callback2(self.fixture))
        self.assertEqual(out[offset(save2(out)+0x13)],0)
        self.assertEqual(pocket(out)[0],save1(out)+0x464)
        self.assertEqual(get(self.f,out,394),getattr(self,'expected_taught_tm_quantity',1))  # legado reutilizável; adaptador SV consome
        self.assertIn(294,pocket_ids(out));self.assertIn(342,pocket_ids(out))
        self.assertTrue(mon_facts(mon(out))['valid'])

    def test_todas_as_paginas_cheias_e_ligacao_l_igual_a(self):
        s=self.fixture
        for item in range(289,347):s=add(self.f,s,item)
        for item in range(375,604):s=add(self.f,s,item)
        # Caso de botão L=A, que continua funcionando fora do estojo.
        mod=bytearray(s);mod[offset(save2(mod)+0x13)]=2
        self.f.restore(bytes(mod));open_case(self.f)
        out=self.f.state();self.assertEqual(len([i for i in pocket_ids(out) if i]),58)
        self.f.pulse('R',180);out=self.f.state()
        self.assertEqual(page(out),1);self.assertEqual(len([i for i in pocket_ids(out) if i]),115)
        self.assertEqual(out[offset(save2(out)+0x13)],2)
        self.f.run(3500,'DOWN');self.f.run(60)
        out=self.f.state();self.assertEqual(page(out),1)
        self.assertTrue(out[offset(STATIC+10)] > 0, 'lista cheia não rolou')
        self.f.pulse('R',180);out=self.f.state()
        self.assertEqual(page(out),2);self.assertEqual(len([i for i in pocket_ids(out) if i]),114)
        self.f.pulse('L',180);out=self.f.state()
        self.assertEqual(page(out),1);self.assertEqual(len([i for i in pocket_ids(out) if i]),115)
        # L não confirmou uma TM apesar da opção L=A.
        self.assertEqual(moves(out),(33,45,22,0))
        self.f.pulse('B',150);out=self.f.state()
        self.assertEqual(pocket(out)[0],save1(out)+0x464)
        self.assertEqual(out[offset(save2(out)+0x13)],2)

    def test_pokedude_nao_interpreta_bytes_privados_como_pagina_ou_opcao(self):
        # Pokedude constrói a tela em código próprio, sem passar pelo nosso
        # init: os oito bytes 'unused' da estrutura não são inicializados.
        # Alocações sintéticas tornam o lixo válido como ponteiro para testar
        # o destrutor sem usar saves pessoais ou corromper o emulador.
        s=add(self.f,self.fixture,394,3)
        before=extension(s)
        allocated=invoke(self.f,s,0x080de848,{0:28});dyn=u32(allocated,0x20)
        s=copy_ewram(s,allocated)
        other=invoke(self.f,s,0x080de848,{0:8});fake=u32(other,0x20)
        s=bytearray(copy_ewram(s,other))
        self.assertTrue(0x02000000<=dyn<0x02040000 and 0x02000000<=fake<0x02040000)
        struct.pack_into('<I',s,offset(0x0203f078),dyn)
        struct.pack_into('<I',s,offset(dyn+20),fake)
        s[offset(dyn+24)]=0xff;s[offset(dyn+25)]=1
        s[offset(STATIC+4)]=4 # TMCASE_POKEDUDE
        s[offset(save2(s)+0x13)]=0
        out=invoke(self.f,bytes(s),0x0814ba7c,{})
        self.assertEqual(out[offset(save2(out)+0x13)],0)
        self.assertEqual(extension(out),before)
        self.assertEqual(pocket(out)[0],save1(out)+0x464)

    def test_pokedude_real_abre_e_restaura_bolsa_ao_cancelar(self):
        s=self.fixture
        for item,n in ((294,2),(342,1),(394,3),(598,4)):s=add(self.f,s,item,n)
        previous=extension(s);old_slots=pocket_ids(s)
        before_option=s[offset(save2(s)+0x13)]
        # Chama a inicialização real do Pokedude e devolve o PC ao loop de
        # jogo, preservando os callbacks e a RAM modificados pela função.
        opened=invoke(self.f,s,0x0814cab8,{})
        self.assertEqual(opened[offset(STATIC+4)],4)
        self.assertEqual(pocket_ids(opened)[:4],[289,291,297,323])
        resumed=bytearray(opened);resumed[:0x1000]=s[:0x1000]
        dyn=u32(resumed,offset(0x0203f078))
        resumed[offset(dyn+24)]=0xff;resumed[offset(dyn+25)]=1
        self.f.restore(bytes(resumed));self.f.run(400);self.f.pulse('B',120);self.f.run(200)
        out=self.f.state()
        self.assertEqual(pocket_ids(out),old_slots)
        self.assertEqual(extension(out),previous)
        self.assertEqual(out[offset(save2(out)+0x13)],before_option)

    def test_backup_da_bolsa_para_link_preserva_extensao_quando_nao_modificada(self):
        s=self.fixture
        for item,n in ((294,2),(342,1),(394,3),(598,4),(139,2)):s=add(self.f,s,item,n)
        before=extension(s)
        saved=invoke(self.f,s,0x080dc604,{})  # LoadPlayerBag copia as bolsas
        s=copy_ewram(s,saved)
        ok,s=call(self.f,s,REMOVE,294,1);self.assertEqual(ok,1)
        ok,s=call(self.f,s,REMOVE,139,1);self.assertEqual(ok,1)
        restored=invoke(self.f,s,0x080dc6e0,{})  # SavePlayerBag restaura legado
        self.assertEqual(extension(restored),before)
        for item,n in ((294,2),(342,1),(394,3),(598,4),(139,2)):
            self.assertEqual(get(self.f,restored,item),n,item)
        # O teste não simula dois jogadores nem alterações de TMs modernas
        # dentro da batalha de link, onde itens normalmente não são utilizáveis.

    def test_loja_venda_tm_moderna_por_interface_real(self):
        data=bytearray(self.rom.read_bytes())
        self.assertEqual(data[0xF90000:0xF9000A],b'\xff'*10)
        struct.pack_into('<I',data,0x7C20D8,0x08F90000)
        data[0xF90000:0xF9000A]=struct.pack('<BBBBHHBB',0x39,3,0,0xFF,4,8,0x27,0x02)
        path=self.dir/'venda_instrumentada.gba';path.write_bytes(data)
        f=self.launch(path,'sell')
        try:
            s=self.fixture
            for item in (294,342,394,598):s=add(f,s,item)
            f.restore(s);route_from_entry(f)
            f.run(64,'LEFT');f.run(30);f.run(5,'UP');f.run(25)
            f.pulse('A',150);f.run(150);f.run(4,'UP');f.run(20)
            for _ in range(5):f.pulse('A',70)
            f.pulse('DOWN',150);f.pulse('A',150)  # vender
            f.pulse('RIGHT',150);f.pulse('A',150) # estojo de TMs
            out=f.state();self.assertEqual(out[offset(STATIC+4)],2)
            f.pulse('R',150);out=f.state()
            self.assertEqual(page(out),1);self.assertEqual([i for i in pocket_ids(out) if i],[394])
            for _ in range(4):f.pulse('A',100)
            out=f.state();self.assertEqual(get(f,out,394),0)
            self.assertEqual(get(f,out,598),1)
            self.assertNotIn(394,pocket_ids(out))
            # A página 0 ainda mostra a HM e TM antigas após a venda.
            f.restore(out);f.pulse('A',120);f.pulse('L',150);out=f.state()
            self.assertEqual(set(i for i in pocket_ids(out) if i),{294,342})
        finally:f.close()

    def test_colecao_inteira_58_mais_229_persiste_no_save(self):
        s=self.fixture
        for item in range(289,347):s=add(self.f,s,item)
        for item in range(375,604):s=add(self.f,s,item,(item*7)%997+1)
        self.f.restore(s);before=extension(s);before_mon=mon(s)
        flash=save_game(self.f)
        new=self.launch(self.rom,'reload_complete')
        try:
            out=load_game(new,flash)
            self.assertEqual(extension(out),before);self.assertEqual(mon(out),before_mon)
            for item in range(289,347):self.assertEqual(get(new,out,item),1,item)
            for item in range(375,604):self.assertEqual(get(new,out,item),(item*7)%997+1,item)
        finally:new.close()

    def test_comprar_tm_com_58_legadas_ocupadas_na_loja_real(self):
        data=bytearray(self.rom.read_bytes())
        self.assertEqual(data[0xf90000:0xf9000a],b'\xff'*10)
        struct.pack_into('<I',data,0x7c20d8,0x08f90000)
        data[0xf90000:0xf9000a]=struct.pack('<BBBBHHBB',0x39,3,0,0xff,4,8,0x27,0x02)
        path=self.dir/'loja_legadas_cheias.gba';path.write_bytes(data)
        f=self.launch(path,'shop_full')
        try:
            s=self.fixture
            for item in range(289,347):s=add(f,s,item)
            def decoded_slots(state):
                key=u16(state,offset(save2(state)+0xf24))
                raw=state[offset(save1(state)+0x464):offset(save1(state)+0x54c)]
                return [(item,quantity^key) for item,quantity in struct.iter_unpack('<HH',raw)]
            before=decoded_slots(s)
            f.restore(s);route_from_entry(f)
            f.run(64,'LEFT');f.run(30);f.run(5,'UP');f.run(25)
            f.pulse('A',150);f.run(150);f.run(4,'UP');f.run(20);f.pulse('A',100)
            for _ in range(20):
                f.pulse('A',60)
                if struct.pack('<I',0x08e18300) in f.state()[0x21000:0x61000]:break
            else:self.fail('Loja não abriu')
            f.pulse('A',120)
            for _ in range(8):f.pulse('A',90)
            out=f.state()
            self.assertEqual(get(f,out,375),1)
            # O warp pode trocar a chave de criptografia; compare conteúdo lógico.
            self.assertEqual(decoded_slots(out),before)
            for item in range(289,347):self.assertEqual(get(f,out,item),1,item)
        finally:f.close()

    def test_salvar_recarregar_e_preservar_varias_paginas(self):
        s=self.fixture
        for item,count in ((294,2),(342,1),(375,7),(394,9),(489,8),(598,3)):
            s=add(self.f,s,item,count)
        self.f.restore(s);flash=save_game(self.f);before=mon(s)
        new=self.launch(self.rom,'reload_many')
        try:
            out=load_game(new,flash)
            self.assertEqual(mon(out),before);self.assertTrue(mon_facts(mon(out))['valid'])
            self.assertEqual(extension(out)[:4],b'T9X1')
            for item,count in ((294,2),(342,1),(375,7),(394,9),(489,8),(598,3)):
                self.assertEqual(get(new,out,item),count,(item,count))
            self.assertEqual(pocket(out)[0],save1(out)+0x464)
        finally:new.close()

    def test_salvar_na_rom_antiga_carregar_migrar_e_recarregar(self):
        old=self.launch(self.base,'old_save')
        try:
            s=self.fixture
            for item,count in ((294,2),(342,1),(394,3),(598,4),(139,2)):
                s=add(old,s,item,count)
            old.restore(s);flash=save_game(old);before=mon(s)
        finally:old.close()
        new=self.launch(self.rom,'new_migrated')
        try:
            out=load_game(new,flash)
            self.assertEqual(mon(out),before);self.assertIn(394,pocket_ids(out))
            # A migração só ocorre quando um item novo é consultado ou o
            # estojo é aberto; usa a tela para registrar a mudança real.
            open_case(new);out=new.state()
            self.assertEqual(extension(out)[:4],b'T9X1')
            self.assertNotIn(394,pocket_ids(out))
            new.pulse('R',120);self.assertIn(394,pocket_ids(new.state()))
            flash2=save_after_case(new)
        finally:new.close()
        reload=self.launch(self.rom,'reload_migrated')
        try:
            out=load_game(reload,flash2);self.assertEqual(mon(out),before)
            for item,count in ((294,2),(342,1),(394,3),(598,4),(139,2)):
                self.assertEqual(get(reload,out,item),count)
        finally:reload.close()

if __name__=='__main__':unittest.main()
