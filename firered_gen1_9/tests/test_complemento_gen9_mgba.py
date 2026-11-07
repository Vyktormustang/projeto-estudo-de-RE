"""Teste mGBA da cópia expandida: ROM privada, apenas saves sintéticos.

COMPLEMENTO_TEST_ROM=rom_mod/complemento_gen9_rascunho.gba \
COMPLEMENTO_TEST_BASE=google_drive/ptbr_gen1-9_selvagens_treino_tms_gen9.gba \
MGBA_CORE=/tmp/mgba-build/mgba_libretro.so \
python3 -m unittest discover -s tests -p test_complemento_gen9_mgba.py -v
"""
from __future__ import annotations
import ctypes as C
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from mgba_treino_harness import Emulator, PARTY, mon, mon_facts, offset, u32
from test_eventos_fixos_mgba import route_entry_fixture, route_from_entry, enemy
from test_golpes_gen9_mgba import invoke, moves, seed_mon
from test_golpes_gen9_integracao import load_game, save_game, set_exp_and_test_stats
from test_atualizacoes_gen9_mgba import (PLAYER_BATTLE, FOE_BATTLE, pocket_ids,
                                        inject_item, open_single_tm_and_teach)
from scripts import complemento_gen9 as patch

ROM = os.environ.get('COMPLEMENTO_TEST_ROM')
BASE = os.environ.get('COMPLEMENTO_TEST_BASE')
CORE = os.environ.get('MGBA_CORE')

@unittest.skipUnless(ROM and CORE and BASE, 'defina COMPLEMENTO_TEST_ROM, COMPLEMENTO_TEST_BASE e MGBA_CORE')
class ComplementoMGBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = Path(ROM).resolve(); cls.base = Path(BASE).resolve(); cls.core = Path(CORE).resolve()
        if patch.digest(cls.base.read_bytes()) != patch.BASE_SHA256: raise ValueError('Entrada incorreta')
        cls.temp = tempfile.TemporaryDirectory(); cls.dir = Path(cls.temp.name)
        cls.f = Emulator(cls.rom, cls.core, cls.dir)
        cls.fixture = route_entry_fixture(cls.f)
    @classmethod
    def tearDownClass(cls):
        cls.f.close(); cls.temp.cleanup()
    def setUp(self): self.f.restore(self.fixture)
    def extra_core(self, tag):
        c = self.dir / f'core_{tag}.so'
        if not c.exists(): shutil.copyfile(self.core, c)
        return c
    def battle(self, f, move):
        state = seed_mon(self.fixture, 917, 5, (move, 0, 0, 0))
        set_exp_and_test_stats(state, 179, 12)
        f.restore(bytes(state)); route_from_entry(f)
        for _ in range(120):
            f.run(20, 'LEFT'); f.run(20, 'RIGHT')
            wild = enemy(f.state())
            if wild['valid'] and wild['species'] != 390:
                f.run(350); return
        self.fail('Não houve encontro no teste')
    def test_aprendizado_por_nivel_reintroduzido_e_legado(self):
        for species, lv, move in ((7,27,503), (208,8,474), (6,62,394)):
            with self.subTest(move=move):
                s = seed_mon(self.fixture, species, lv, (33,45,0,0))
                out = invoke(self.f, s, 0x08109790, {0: PARTY, 1: 1})
                self.assertEqual(u32(out, 0x20), move)
                self.assertIn(move, moves(out))
                self.assertTrue(mon_facts(mon(out))['valid'])
    def test_compatibilidade_tms_novas_antigas_e_ovos(self):
        cases = ((1,394,0), (10,394,1), (48,395,0), (7,396,0), (4,518,0),
                 (7,519,0), (1,520,0), (147,543,0), (1,545,0), (1,568,0),
                 (6,589,0), (25,446,0), (66,495,0), (7,554,0), (6,563,0),
                 (1,294,0), (1,342,0))
        for species,item,expected in cases:
            with self.subTest(species=species,item=item):
                s = seed_mon(self.fixture, species,5,(33,45,0,0))
                out = invoke(self.f,s,0x080F8460,{0:PARTY,1:item,2:0})
                self.assertEqual(u32(out,0x20), expected)
        s = seed_mon(self.fixture,1,5,(33,45,0,0),True)
        self.assertEqual(u32(invoke(self.f,s,0x080F8460,{0:PARTY,1:394,2:0}),0x20),3)
        s = seed_mon(self.fixture,1,5,(33,45,797,0))
        self.assertEqual(u32(invoke(self.f,s,0x080F8460,{0:PARTY,1:394,2:0}),0x20),2)
    def test_loja_compra_tm_nova_ensina_e_permite_chegar_ao_fim(self):
        # Letreiro de warp somente em cópia descartável para chegar à loja
        # real de Pallet sem modificar o arquivo que será entregue.
        data=bytearray(self.rom.read_bytes())
        self.assertEqual(data[0xF90000:0xF9000A],b'\xff'*10)
        struct.pack_into('<I',data,0x7C20D8,0x08F90000)
        data[0xF90000:0xF9000A]=struct.pack('<BBBBHHBB',0x39,3,0,0xFF,4,8,0x27,0x02)
        path=self.dir/'loja_instrumentada.gba';path.write_bytes(data)
        f=Emulator(path,self.extra_core('shop'),self.dir)
        try:
            f.restore(self.fixture);route_from_entry(f)
            f.run(64,'LEFT');f.run(30);f.run(5,'UP');f.run(25)
            f.pulse('A',150);f.run(150)
            f.run(4,'UP');f.run(20);f.pulse('A',100)
            for _ in range(20):
                f.pulse('A',60)
                if struct.pack('<I',0x08E18300) in f.state()[0x21000:0x61000]:break
            else:self.fail('Loja de TMs não abriu')
            f.pulse('A',120)  # primeira posição da lista
            for _ in range(19):f.pulse('DOWN',20)
            for _ in range(8):f.pulse('A',90)
            self.assertIn(394,pocket_ids(f.state()))  # TM9-020 Trailblaze
            for _ in range(5):f.pulse('B',90)
            open_single_tm_and_teach(f)
            self.assertEqual(moves(f.state())[-1],797)
            self.assertIn(394,pocket_ids(f.state()))
        finally:f.close()
        # Em outra instância, percorre os 203 produtos até a última TM.
        f=Emulator(path,self.extra_core('shop_last'),self.dir)
        try:
            f.restore(self.fixture);route_from_entry(f)
            f.run(64,'LEFT');f.run(30);f.run(5,'UP');f.run(25)
            f.pulse('A',150);f.run(150)
            f.run(4,'UP');f.run(20);f.pulse('A',100)
            for _ in range(20):
                f.pulse('A',60)
                if struct.pack('<I',0x08E18300) in f.state()[0x21000:0x61000]:break
            else:self.fail('Loja não abriu na segunda visita')
            f.pulse('A',120);f.run(3000,'DOWN');f.run(40);f.pulse('UP',100)
            for _ in range(8):f.pulse('A',90)
            self.assertIn(598,pocket_ids(f.state()))  # última: TM9-224
        finally:f.close()

    def test_ensino_por_interface_de_tm_nova_e_legada(self):
        for item, move, reusable in ((394,797,True),(294,92,False),(342,70,True)):
            with self.subTest(item=item):
                s = inject_item(self.f, self.fixture, item)
                self.f.restore(s); open_single_tm_and_teach(self.f)
                out = self.f.state()
                self.assertEqual(moves(out),(33,45,22,move))
                self.assertEqual(item in pocket_ids(out),reusable)
                self.assertTrue(mon_facts(mon(out))['valid'])
    def test_estagios_e_dano_dos_novos_golpes(self):
        cases = ((503, PLAYER_BATTLE, {1:8,2:5,3:8,4:8,5:5}),
                 (474, PLAYER_BATTLE, {3:8}),
                 (797, PLAYER_BATTLE, {3:7}),
                 (798, FOE_BATTLE, {3:5}),
                 (799, FOE_BATTLE, {1:5}),
                 (803, PLAYER_BATTLE, {4:4}),
                 (370, PLAYER_BATTLE, {2:5,5:5}))
        for move, who, want in cases:
            with self.subTest(move=move):
                self.battle(self.f,move)
                st = bytearray(self.f.state())
                struct.pack_into('<H',st,FOE_BATTLE+0x2A,500)
                struct.pack_into('<H',st,FOE_BATTLE+0x2E,500)
                self.f.restore(bytes(st))
                for _ in range(200):
                    self.f.pulse('A',35)
                    out = self.f.state()
                    stages = out[who+0x18:who+0x20]
                    if all(stages[k] == v for k,v in want.items()): break
                else: self.fail(f'{move}: estágios={list(stages)} esperados={want}, PC={u32(out,0x5c):08x}')
                if move not in (503,474):
                    self.assertLess(struct.unpack_from('<H',out,FOE_BATTLE+0x2A)[0],500)
    def test_batalha_real_golpes_de_poder_dinamico(self):
        for mid in (360,485,483,531):
            with self.subTest(move=mid):
                self.battle(self.f,mid)
                st=bytearray(self.f.state())
                struct.pack_into('<H',st,PLAYER_BATTLE,143)  # Snorlax, 460 kg
                struct.pack_into('<H',st,FOE_BATTLE,25)       # Pikachu, 6 kg
                struct.pack_into('<H',st,PLAYER_BATTLE+6,10 if mid==360 else 100)
                struct.pack_into('<H',st,FOE_BATTLE+6,100 if mid==360 else 25)
                for who in (PLAYER_BATTLE,FOE_BATTLE):
                    st[who+0x1B]=6
                    struct.pack_into('<I',st,who+0x50,0)
                    struct.pack_into('<H',st,who+0x20,0)
                    struct.pack_into('<H',st,who+0x30,0)
                st[FOE_BATTLE+0x22:FOE_BATTLE+0x24]=b'\x00\x00'
                struct.pack_into('<H',st,FOE_BATTLE+0x2A,500)
                struct.pack_into('<H',st,FOE_BATTLE+0x2E,500)
                self.f.restore(bytes(st)); observed=False
                for i in range(2000):
                    self.f.run(1)
                    if i%35==0:self.f.pulse('A',1)
                    out=self.f.state()
                    power=struct.unpack_from('<H',out,offset(0x02021792))[0]
                    if power==(150 if mid in (360,485) else 120): observed=True
                    hp=struct.unpack_from('<H',out,FOE_BATTLE+0x2A)[0]
                    if observed and hp<500: break
                else:self.fail(f'Golpe {mid}: potência esperada/dano não observados')

    def test_limites_de_shell_smash(self):
        # Quando uma estatística está no limite, as demais ainda mudam.
        self.battle(self.f,503)
        st = bytearray(self.f.state())
        st[PLAYER_BATTLE+0x18+1] = 12
        st[PLAYER_BATTLE+0x18+2] = 0
        self.f.restore(bytes(st))
        for _ in range(200):
            self.f.pulse('A',35)
            stages = self.f.state()[PLAYER_BATTLE+0x18:PLAYER_BATTLE+0x20]
            if stages[4] == 8 and stages[3] == 8: break
        else: self.fail(f'Shell Smash não respeitou limites: {list(stages)}')
        self.assertEqual(stages[1],12); self.assertEqual(stages[2],0)
        self.assertEqual(stages[5],5)

    def test_presas_com_dois_efeitos_e_chance_forcada(self):
        # Instrumentação apenas na cópia efêmera: chance 100%. A produção
        # conserva 10% para cada efeito independente.
        data = bytearray(self.rom.read_bytes())
        for mid in (422,423): data[patch.MOVE+mid*12+5] = 100
        path = self.dir/'presas_forcadas.gba'; path.write_bytes(data)
        f = Emulator(path,self.extra_core('presas'),self.dir)
        try:
            for mid, status in ((422,0x40),(423,0x20)):
                with self.subTest(move=mid):
                    self.battle(f,mid)
                    st = bytearray(f.state())
                    struct.pack_into('<H',st,FOE_BATTLE+0x2A,500)
                    struct.pack_into('<H',st,FOE_BATTLE+0x2E,500)
                    struct.pack_into('<H',st,FOE_BATTLE+0x20,0)  # nenhuma habilidade
                    st[FOE_BATTLE+0x22:FOE_BATTLE+0x24] = b'\x00\x00'  # tipos normais
                    f.restore(bytes(st)); seen_flinch = False
                    for i in range(2400):
                        f.run(1)
                        if i % 35 == 0: f.pulse('A',1)
                        out = f.state()
                        seen_flinch |= bool(out[FOE_BATTLE+0x54] & 8)
                        if seen_flinch and (out[FOE_BATTLE+0x50] & status): break
                    else: self.fail(f'presa {mid}: status={out[FOE_BATTLE+0x50]:02x}, flinch={seen_flinch}')
        finally: f.close()

    def test_dual_wingbeat_da_dois_golpes(self):
        # Precisão 100% apenas para eliminar sorte no teste dos dois hits.
        data = bytearray(self.rom.read_bytes()); data[patch.MOVE+709*12+3] = 100
        path = self.dir/'duplo_forcado.gba'; path.write_bytes(data)
        f = Emulator(path,self.extra_core('duplo'),self.dir)
        try:
            self.battle(f,709)
            st = bytearray(f.state())
            struct.pack_into('<H',st,FOE_BATTLE+0x2A,500)
            struct.pack_into('<H',st,FOE_BATTLE+0x2E,500)
            f.restore(bytes(st)); values=[]; last=500
            for i in range(3000):
                f.run(1)
                if i % 35 == 0: f.pulse('A',1)
                hp = struct.unpack_from('<H',f.state(),FOE_BATTLE+0x2A)[0]
                if hp < last: values.append(hp); last = hp
                if len(values) >= 2: break
            self.assertGreaterEqual(len(values),2, f'HP após hits: {values}')
        finally: f.close()

    def test_categorias_de_todos_os_novos_golpes(self):
        self.battle(self.f,797)
        source=bytearray(self.f.state())
        source[offset(0x020215A8)]=0; source[offset(0x020215A9)]=1
        for who in (PLAYER_BATTLE,FOE_BATTLE):
            for i in range(1,8): source[who+0x18+i]=6
            struct.pack_into('<H',source,who+0x20,0)
            struct.pack_into('<I',source,who+0x50,0)
            struct.pack_into('<H',source,who+0x30,0)
        def damage(mid,atk,spa):
            st=bytearray(source)
            struct.pack_into('<H',st,offset(0x02021586),mid)
            struct.pack_into('<H',st,offset(0x02021792),0)
            struct.pack_into('<H',st,PLAYER_BATTLE+2,atk)
            struct.pack_into('<H',st,PLAYER_BATTLE+8,spa)
            struct.pack_into('<H',st,FOE_BATTLE+4,100)
            struct.pack_into('<H',st,FOE_BATTLE+10,100)
            out=invoke(self.f,bytes(st),0x0900C000,{})
            return struct.unpack_from('<i',out,offset(0x0202158C))[0]
        for mid,physical in ((797,True),(798,True),(799,False),(800,False),
                             (801,False),(802,False),(803,False),(804,False),
                             (805,True),(806,False)):
            with self.subTest(move=mid):
                phys=damage(mid,300,10); special=damage(mid,10,300)
                self.assertGreater(phys,special) if physical else self.assertGreater(special,phys)

    def test_poderes_dinamicos_basicos_e_limites(self):
        self.battle(self.f,360)
        saved = bytearray(self.f.state())
        saved[offset(0x020215A8)] = 0
        saved[offset(0x020215A9)] = 1
        for who in (PLAYER_BATTLE, FOE_BATTLE):
            saved[who+0x1B] = 6
            struct.pack_into('<I',saved,who+0x50,0)
            struct.pack_into('<H',saved,who+0x30,0)
        cases = (
            # movimento, velocidades, espécies, estágios, status, item, potência
            (360,100,100,1,25,6,6,0,0,26),
            (360,10,100,1,25,6,6,0,0,150),
            (360,100,100,1,25,6,6,0x40,0,101),
            (360,100,100,1,25,6,6,0,181,51),
            (485,100,25,1,25,6,6,0,0,150),
            (485,100,30,1,25,6,6,0,0,120),
            (485,100,50,1,25,6,6,0,0,80),
            (485,100,100,1,25,6,6,0,0,60),
            (485,99,100,1,25,6,6,0,0,40),
            (483,100,100,1,25,6,6,0,0,40),
            (483,100,100,143,25,6,6,0,0,120),
            (531,100,100,143,25,6,6,0,0,120),
        )
        for mid,us,them,sp1,sp2,stage1,stage2,status,item,want in cases:
            with self.subTest(move=mid,speeds=(us,them),species=(sp1,sp2),item=item,status=status):
                st = bytearray(saved)
                struct.pack_into('<H',st,offset(0x02021586),mid)
                struct.pack_into('<H',st,PLAYER_BATTLE,sp1); struct.pack_into('<H',st,FOE_BATTLE,sp2)
                struct.pack_into('<H',st,PLAYER_BATTLE+6,us); struct.pack_into('<H',st,FOE_BATTLE+6,them)
                st[PLAYER_BATTLE+0x1B]=stage1; st[FOE_BATTLE+0x1B]=stage2
                struct.pack_into('<I',st,PLAYER_BATTLE+0x50,status)
                struct.pack_into('<H',st,PLAYER_BATTLE+0x30,item)
                out = invoke(self.f,bytes(st),0x0900C000,{})
                got = struct.unpack_from('<H',out,offset(0x02021792))[0]
                self.assertEqual(got,want)

    def test_poder_adicional_e_estatisticas_usadas_no_dano(self):
        self.battle(self.f,683)
        original = bytearray(self.f.state())
        original[offset(0x020215A8)] = 0; original[offset(0x020215A9)] = 1
        for who in (PLAYER_BATTLE,FOE_BATTLE):
            for i in range(1,8): original[who+0x18+i] = 6
            struct.pack_into('<H',original,who+0x20,0)
            struct.pack_into('<I',original,who+0x50,0)
            struct.pack_into('<H',original,who+0x30,0)
        def calculate(move, attack=100, defense=100, spatk=100, spdef=100,
                      target_attack=100,target_def=100,target_spdef=100,status=0,item=0,boosts=()):
            st=bytearray(original)
            struct.pack_into('<H',st,offset(0x02021586),move)
            struct.pack_into('<H',st,offset(0x02021792),0)
            for off,val in ((2,attack),(4,defense),(8,spatk),(10,spdef)):
                struct.pack_into('<H',st,PLAYER_BATTLE+off,val)
            for off,val in ((2,target_attack),(4,target_def),(10,target_spdef)):
                struct.pack_into('<H',st,FOE_BATTLE+off,val)
            struct.pack_into('<I',st,FOE_BATTLE+0x50,status)
            struct.pack_into('<H',st,PLAYER_BATTLE+0x30,item)
            for stat,stage in boosts: st[PLAYER_BATTLE+0x18+stat]=stage
            out=invoke(self.f,bytes(st),0x0900C000,{})
            self.assertEqual(struct.unpack_from('<H',out,PLAYER_BATTLE+2)[0],attack)
            self.assertEqual(struct.unpack_from('<H',out,FOE_BATTLE+10)[0],target_spdef)
            self.assertEqual(out[PLAYER_BATTLE+0x19],st[PLAYER_BATTLE+0x19])
            self.assertEqual(out[FOE_BATTLE+0x1D],st[FOE_BATTLE+0x1D])
            return (struct.unpack_from('<H',out,offset(0x02021792))[0],
                    struct.unpack_from('<i',out,offset(0x0202158C))[0])
        for mid,item,want in ((511,0,110),(511,181,55)):
            self.assertEqual(calculate(mid,item=item)[0],want)
        for mid in (499,636):
            self.assertEqual(calculate(mid,boosts=((1,8),(2,5),(6,7)))[0],80)
            self.assertEqual(calculate(mid,boosts=tuple((i,12) for i in range(1,8)))[0],860)
        for mid,status,want in ((473,8,130),(473,0x80,130),(473,0x10,65),
                                (505,0x10,130),(505,0,65)):
            self.assertEqual(calculate(mid,status=status)[0],want)
        # Mudanças no atributo que não deve ser usado não alteram o dano;
        # alterar o atributo correto altera-o. Dados são restaurados.
        body_low = calculate(683,attack=10,defense=100)[1]
        self.assertEqual(body_low,calculate(683,attack=500,defense=100)[1])
        self.assertGreater(calculate(683,attack=10,defense=300)[1],body_low)
        foul_low = calculate(491,attack=10,target_attack=100)[1]
        self.assertEqual(foul_low,calculate(491,attack=500,target_attack=100)[1])
        self.assertGreater(calculate(491,attack=10,target_attack=300)[1],foul_low)
        for mid in (472,536):
            psy_low = calculate(mid,target_def=100,target_spdef=20)[1]
            self.assertEqual(psy_low,calculate(mid,target_def=100,target_spdef=500)[1])
            self.assertGreater(calculate(mid,target_def=20,target_spdef=20)[1],psy_low)

    def test_dano_dos_demais_movimentos_novos(self):
        for mid in (800,801,802,804,805,806):
            with self.subTest(move=mid):
                self.battle(self.f,mid)
                st = bytearray(self.f.state())
                struct.pack_into('<H',st,FOE_BATTLE+0x2A,500)
                struct.pack_into('<H',st,FOE_BATTLE+0x2E,500)
                st[FOE_BATTLE+0x22:FOE_BATTLE+0x24] = b'\x00\x00'
                self.f.restore(bytes(st))
                for _ in range(100):
                    self.f.pulse('A',35)
                    if struct.unpack_from('<H',self.f.state(),FOE_BATTLE+0x2A)[0] < 500: break
                else: self.fail(f'movimento {mid} não causou dano')

    def test_salva_e_recarrega_com_golpe_acima_de_796(self):
        state = inject_item(self.f,self.fixture,394)
        self.f.restore(state); open_single_tm_and_teach(self.f)
        self.assertEqual(moves(self.f.state())[-1],797)
        for _ in range(6): self.f.pulse('B',80)
        # O cursor do menu inicial ficou em Bolsa; SALVAR fica três posições abaixo.
        self.f.pulse('START',80)
        for _ in range(3): self.f.pulse('DOWN',35)
        for _ in range(15): self.f.pulse('A',100)
        ptr = self.f.core.core.retro_get_memory_data(0)
        size = self.f.core.core.retro_get_memory_size(0)
        self.assertEqual(size,131072)
        flash = C.string_at(ptr,size)
        self.assertGreater(len(set(flash)),2)
        new = Emulator(self.rom,self.extra_core('reload'),self.dir)
        try:
            out = load_game(new,flash)
            self.assertEqual(moves(out)[-1],797)
            self.assertIn(394,pocket_ids(out)); self.assertTrue(mon_facts(mon(out))['valid'])
        finally: new.close()
    def test_migracao_de_save_sintetico_da_versao_anterior(self):
        old = Emulator(self.base,self.extra_core('old'),self.dir)
        try:
            before = route_entry_fixture(old); before_mon = mon(before)
            flash = save_game(old)
        finally: old.close()
        new = Emulator(self.rom,self.extra_core('migration'),self.dir)
        try:
            out = load_game(new,flash)
            self.assertEqual(mon(out),before_mon); self.assertTrue(mon_facts(mon(out))['valid'])
        finally: new.close()

if __name__ == '__main__': unittest.main()
