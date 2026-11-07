"""Verificações estruturais da TM225 sem distribuir ROMs ou saves."""
from __future__ import annotations
import csv
import os
import struct
import unittest
from pathlib import Path
from scripts import motor_ampliado as p, complemento_gen9 as old, atualizacoes_gen9 as prev
ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('MOTOR_TEST_BASE');ROM=os.environ.get('MOTOR_TEST_ROM')

class MotorCatalogTests(unittest.TestCase):
    def test_catalogo_e_compatibilidade_preservada(self):
        inputs=p.checked_inputs()
        with (ROOT/'data/tms_motor_ampliado.csv').open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),229)
        self.assertEqual(sum(r['status']=='disponivel' for r in rows),204)
        self.assertEqual((rows[224]['name'],rows[224]['internal_move'],rows[224]['status']),('Hard Press','807','disponivel'))
        a=inputs[ROOT/'data/compatibilidade_tms_complemento.bin']
        b=inputs[ROOT/'data/compatibilidade_tms_motor_ampliado.bin']
        changed=[i for i in range(len(a)) if a[i]!=b[i]]
        self.assertEqual(len(changed),43)
        self.assertTrue(all(i%29==28 and a[i]^b[i]==1 for i in changed))
        self.assertTrue(all(a[i]&~b[i]==0 for i in range(len(a))))
        self.assertIn(151,[i//29 for i in changed]);self.assertNotIn(10,[i//29 for i in changed])
    def test_rejeita_entrada_ou_dados_diferentes(self):
        with self.assertRaises(p.PatchError):p.build(b'\0'*0x2000000)
        data=p.checked_inputs();path=ROOT/'patches/motor_ampliado/payload.bin'
        data[path]=data[path][:-1]+bytes((data[path][-1]^1,))
        # Deve verificar a entrada antes dos dados adulterados.
        with self.assertRaises(p.PatchError):p.build(b'\0'*0x2000000,data)

@unittest.skipUnless(BASE and ROM,'defina MOTOR_TEST_BASE e MOTOR_TEST_ROM')
class MotorPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Path(BASE).read_bytes();cls.rom=Path(ROM).read_bytes()
    def test_reproducivel(self):self.assertEqual(self.rom,p.build(self.base))
    def test_tm_move_e_loja(self):
        self.assertEqual(struct.unpack_from('<H',self.rom,prev.NEW_MOVE_TABLE+(599-289)*2)[0],807)
        self.assertEqual(self.rom[old.MOVE+807*12:old.MOVE+808*12],bytes((0,1,8,100,10,0,0,0,0x33,0,0,0)))
        self.assertEqual(self.rom[old.CATEGORY+807],0)
        data=self.rom[prev.SHOP_LIST:prev.SHOP_SCRIPT]
        products=struct.unpack('<'+'H'*(len(data)//2),data)
        products=products[:products.index(0)]
        self.assertEqual(len(products),204);self.assertIn(599,products);self.assertEqual(products[-1],599)
    def test_descricoes_modernas_e_codigo_de_consumo(self):
        with (ROOT/'data/tms_motor_ampliado.csv').open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        for row in rows:
            if row['status']!='disponivel':continue
            at=prev.NEW_ITEMS+int(row['item_id'])*44+20
            ptr=struct.unpack_from('<I',self.rom,at)[0]-p.ROM
            self.assertTrue(p.ITEM_TEXT_START<=ptr<p.ITEM_TEXT_END)
            end=self.rom.index(b'\xff',ptr)
            self.assertTrue(self.rom[ptr:end+1].endswith(prev.text('\nUSO UNICO')))
        for i,(at,code) in enumerate(p.CONSUME_SITES,1):
            new=(ROOT/f'patches/motor_ampliado/consumo{i}.bin').read_bytes()
            self.assertEqual(self.rom[at:at+len(new)],new)
            self.assertEqual(self.base[at:at+len(new)],bytes.fromhex(code))
        for at,name,code in p.ANIM_SITES+p.REG_SITES:
            new=(ROOT/'patches/motor_ampliado'/name).read_bytes()
            self.assertEqual(self.rom[at:at+len(new)],new)
            self.assertEqual(self.base[at:at+len(new)],bytes.fromhex(code))

    def test_modifica_apenas_areas_previstas(self):
        allowed=bytearray(len(self.base))
        def mark(a,b):allowed[a:b]=b'\1'*(b-a)
        for a,b in ((0x100c000,0x100d000),(0xe06000,0xe06000+1026*29),
                    (prev.SHOP_LIST,prev.SHOP_SCRIPT),(prev.NEW_MOVE_TABLE+(599-289)*2,prev.NEW_MOVE_TABLE+(599-289)*2+2),
                    (old.MOVE+807*12,old.MOVE+808*12),(old.NAMES+807*17,old.NAMES+808*17),
                    (old.ANIM+807*4,old.ANIM+808*4),(old.DESC+806*4,old.DESC+807*4),
                    (old.CATEGORY+807,old.CATEGORY+808),(p.TEXT,p.TEXT+0x100),
                    (p.ITEM_TEXT_START,p.ITEM_TEXT_END)):
            mark(a,b)
        for at,code in p.CONSUME_SITES:mark(at,at+len(bytes.fromhex(code)))
        for at,_,code in p.ANIM_SITES+p.REG_SITES:mark(at,at+len(bytes.fromhex(code)))
        with (ROOT/'data/tms_motor_ampliado.csv').open(encoding='utf-8',newline='') as f:
            for row in csv.DictReader(f):
                if row['status']=='disponivel':
                    at=prev.NEW_ITEMS+int(row['item_id'])*44+20;mark(at,at+4)
        bad=[i for i,(a,b) in enumerate(zip(self.base,self.rom)) if a!=b and not allowed[i]]
        self.assertEqual(bad[:10],[])
