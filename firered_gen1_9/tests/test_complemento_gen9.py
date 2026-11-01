"""Verificações estruturais, sem ROMs ou saves distribuídos no repositório."""
from __future__ import annotations
import csv
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from scripts import complemento_gen9 as p, atualizacoes_gen9 as prev, golpes_gen9 as lv
from scripts import encontros_selvagens as wild, eventos_fixos as fixed, treino_ev
from scripts.gerar_complemento_gen9 import NEW_MOVES, DYNAMIC_TMS

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(os.environ.get('COMPLEMENTO_TEST_BASE', ROOT/'google_drive/ptbr_gen1-9_selvagens_treino_tms_gen9.gba'))

class ComplementoCatalogTests(unittest.TestCase):
    def test_catalogos_e_pendencias(self):
        data=p.checked_inputs()
        tms=p._rows(data[ROOT/'data/tms_gen9_complemento.csv'])
        levels=p._rows(data[ROOT/'data/learnsets_gen1_9_complemento.csv'])
        with (ROOT/'docs/golpes_pendentes_complemento.csv').open(encoding='utf-8',newline='') as f:
            missing=list(csv.DictReader(f))
        self.assertEqual(len(tms),229)
        self.assertEqual(sum(r['status']=='disponivel' for r in tms),203)
        self.assertEqual(len(levels),14300)
        self.assertEqual(len(missing),729)
        self.assertEqual(len({r['name'] for r in missing}),81)
        self.assertEqual(len(data[ROOT/'data/pesos_gen1_9.bin']),2052)
        self.assertEqual(len(data[ROOT/'data/compatibilidade_tms_complemento.bin']),1026*29)
    def test_nao_aceita_entrada_ou_saida_invalida(self):
        with self.assertRaises(p.PatchError): p.build(b'rom invalida')
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td)/'entrada.gba', Path(td)/'saida.gba'
            source.write_bytes(b'entrada'); output.write_bytes(b'preservado')
            with mock.patch('sys.argv',['patch','--rom',str(source),'--saida',str(output)]):
                self.assertEqual(p.main(),1)
            self.assertEqual(source.read_bytes(),b'entrada')
            self.assertEqual(output.read_bytes(),b'preservado')

@unittest.skipUnless(BASE.exists(),'ROM privada de entrada não fornecida')
class ComplementoROMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=BASE.read_bytes(); cls.out=p.build(cls.base); cls.inputs=p.checked_inputs()
    def test_tamanho_sha_e_tabelas_relocadas(self):
        self.assertEqual(len(self.out),0x2000000)
        if p.OUTPUT_SHA256: self.assertEqual(p.digest(self.out),p.OUTPUT_SHA256)
        categories=self.out[p.CATEGORY:p.CATEGORY+p.OLD_COUNT]
        self.assertEqual(categories,self.base[p.ORIG_CATEGORY:p.ORIG_CATEGORY+p.OLD_COUNT])
        self.assertEqual(self.out[p.ANIM:p.ANIM+p.OLD_COUNT*4],self.base[p.ORIG_ANIM:p.ORIG_ANIM+p.OLD_COUNT*4])
        self.assertEqual(self.out[p.DESC:p.DESC+(p.OLD_COUNT-1)*4],self.base[p.ORIG_DESC:p.ORIG_DESC+(p.OLD_COUNT-1)*4])
        self.assertEqual(self.out[p.NAMES:p.NAMES+p.OLD_COUNT*17],self.base[p.ORIG_NAMES:p.ORIG_NAMES+p.OLD_COUNT*17])
        self.assertEqual(self.out[p.SCRIPT_TABLE:p.SCRIPT_TABLE+214*4],self.base[p.ORIG_SCRIPT:p.ORIG_SCRIPT+214*4])
        self.assertEqual(struct.unpack_from('<I',self.out,0x209804)[0],0x0900C001)
        for tm,mid,_,_,_ in NEW_MOVES:
            self.assertEqual(self.out[p.CATEGORY+mid],p.NEW_CATEGORY[tm])
            self.assertEqual(self.out[p.MOVE+mid*12:p.MOVE+mid*12+9],bytes(p.NEW_DATA[tm]))
            ptr=struct.unpack_from('<I',self.out,p.DESC+(mid-1)*4)[0]
            self.assertTrue(0x09009000<=ptr<0x0900A000)
    def test_itens_hms_loja_e_compatibilidade(self):
        self.assertEqual(self.out[prev.NEW_ITEMS:prev.NEW_ITEMS+375*prev.ITEM_SIZE],
                         self.base[prev.NEW_ITEMS:prev.NEW_ITEMS+375*prev.ITEM_SIZE])
        self.assertEqual(self.out[prev.NEW_MOVE_TABLE:prev.NEW_MOVE_TABLE+116],
                         self.base[prev.NEW_MOVE_TABLE:prev.NEW_MOVE_TABLE+116])
        rows=p._rows(self.inputs[ROOT/'data/tms_gen9_complemento.csv'])
        for row in rows:
            tm=int(row['tm']); mid=int(row['internal_move'])
            addr=prev.NEW_MOVE_TABLE+(374+tm-289)*2
            self.assertEqual(struct.unpack_from('<H',self.out,addr)[0],mid if row['status']=='disponivel' else 0)
        products=struct.unpack_from('<204H',self.out,prev.SHOP_LIST)
        self.assertEqual(list(products),[374+int(r['tm']) for r in rows if r['status']=='disponivel']+[0])
        prior=self.inputs[ROOT/'data/compatibilidade_tms_gen9.bin']
        new=self.inputs[ROOT/'data/compatibilidade_tms_complemento.bin']
        self.assertTrue(all(a & ~b==0 for a,b in zip(prior,new)))
    def test_todas_as_listas_sao_iguais_ao_catalogo(self):
        rows=p._rows(self.inputs[ROOT/'data/learnsets_gen1_9_complemento.csv'])
        expected={sid:[] for sid in range(1,1026)}
        for r in rows: expected[int(r['species'])].append((int(r['level']),int(r['internal_move'])))
        for sid,want in expected.items():
            ptr=struct.unpack_from('<I',self.out,lv.TABLE+4*sid)[0]-0x08000000
            got=[]
            for _ in range(51):
                move,level=struct.unpack_from('<HB',self.out,ptr);ptr+=3
                if move==0xffff: break
                got.append((level,move))
            else: self.fail(f'Espécie {sid} sem terminador')
            self.assertEqual(got,want)
    def test_selvagens_objetos_eventos_e_treino(self):
        species,maps=wild.load_species(),wild.load_maps()
        self.assertEqual(wild.parse_tables(self.base,maps,species),wild.parse_tables(self.out,maps,species))
        self.assertEqual(self.base[treino_ev.HOOK_OFFSET:treino_ev.HOOK_OFFSET+len(treino_ev.HOOK)],
                         self.out[treino_ev.HOOK_OFFSET:treino_ev.HOOK_OFFSET+len(treino_ev.HOOK)])
        lo=treino_ev.PAYLOAD_OFFSET;hi=lo+treino_ev.PAYLOAD_SPACE
        self.assertEqual(self.base[lo:hi],self.out[lo:hi])
        count=0
        for m in fixed.load_map_catalog():
            array=fixed._ptr(self.base,fixed.GROUP_TABLE+4*m.group,4*(m.number+1))
            header=fixed._ptr(self.base,array+4*m.number,28)
            events=fixed._ptr(self.base,header+4,20)
            n=self.base[events]
            self.assertEqual(self.out[events:events+20],self.base[events:events+20])
            if n:
                objects=fixed._ptr(self.base,events+4,n*fixed.OBJECT_SIZE)
                self.assertEqual(self.out[objects:objects+n*fixed.OBJECT_SIZE],self.base[objects:objects+n*fixed.OBJECT_SIZE])
                count+=n
        self.assertEqual(count,1982)
    def test_mudancas_limitadas_a_areas_planejadas(self):
        allowed=bytearray(len(self.base))
        def mark(lo,hi):allowed[lo:hi]=b'\1'*(hi-lo)
        mark(lv.TABLE,lv.FREE_END);mark(0xE06000,0xE06000+1026*29)
        mark(prev.SHOP_LIST,prev.SHOP_SCRIPT)
        mark(prev.NEW_MOVE_TABLE+116,prev.NEW_MOVE_TABLE+(603-289+1)*2)
        for tm,_,_,_,_ in NEW_MOVES:
            item=374+tm;mark(prev.NEW_ITEMS+item*44+20,prev.NEW_ITEMS+item*44+24)
        for tm in DYNAMIC_TMS:
            item=374+tm;mark(prev.NEW_ITEMS+item*44+20,prev.NEW_ITEMS+item*44+24)
        mark(0x209804,0x209808)
        for addr in (0x08696F70,0x08696F74,0x08235930,0x08174CB4,0x08661668,0x086994CC,0x08185050):
            needle=struct.pack('<I',addr);start=0
            while True:
                pos=self.base.find(needle,start)
                if pos<0:break
                mark(pos,pos+4);start=pos+4
        bad=[i for i,(x,y) in enumerate(zip(self.base,self.out)) if x!=y and not allowed[i]]
        self.assertEqual(bad[:10],[])

if __name__=='__main__':unittest.main()
