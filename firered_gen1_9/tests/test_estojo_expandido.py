"""Testes estruturais do rascunho de estojo, sem distribuir ROM ou saves."""
from __future__ import annotations
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from scripts import estojo_expandido as p
from scripts import atualizacoes_gen9 as old, complemento_gen9 as complement

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(os.environ.get('ESTOJO_TEST_BASE', ROOT/'rom_mod/ptbr_gen1-9_complemento_parcial_32mb.gba'))

class PatchTests(unittest.TestCase):
    def test_payload_e_trampolins(self):
        payload = p.PAYLOAD_PATH.read_bytes()
        self.assertEqual(p.digest(payload),p.PAYLOAD_SHA256)
        self.assertLessEqual(len(payload),p.PAYLOAD_END-p.PAYLOAD_START)
        for _,_,index in p.HOOKS:
            self.assertEqual(payload[index:index+4],bytes.fromhex('00 4b 18 47'))
            target=struct.unpack_from('<I',payload,index+4)[0]
            self.assertTrue((p.ROM_START+p.PAYLOAD_START) < target < (p.ROM_START+p.PAYLOAD_START+len(payload)))
            self.assertEqual(target&1,1)
    def test_rejeita_entradas_e_nunca_sobrescreve(self):
        with self.assertRaises(p.PatchError):p.build(b'entrada incorreta')
        with tempfile.TemporaryDirectory() as t:
            src,dst=Path(t)/'origem.gba',Path(t)/'destino.gba'
            src.write_bytes(b'original'); dst.write_bytes(b'existente')
            with mock.patch('sys.argv',['app','--rom',str(src),'--saida',str(dst)]): self.assertEqual(p.main(),1)
            self.assertEqual(src.read_bytes(),b'original');self.assertEqual(dst.read_bytes(),b'existente')

@unittest.skipUnless(BASE.exists(),'ROM privada parcial não fornecida')
class ROMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=BASE.read_bytes();cls.out=p.build(cls.source)
    def test_somente_codigo_previsto_alterado(self):
        src,out=self.source,self.out
        allowed=bytearray(len(src));allowed[p.PAYLOAD_START:p.PAYLOAD_END]=b'\1'*(p.PAYLOAD_END-p.PAYLOAD_START)
        for off,_,index in p.HOOKS:
            allowed[off:off+8]=b'\1'*8
            self.assertEqual(out[off:off+4],bytes.fromhex('00 4b 18 47'))
            self.assertEqual(struct.unpack_from('<I',out,off+4)[0],p.ROM_START+p.PAYLOAD_START+index+1)
        for i,(a,b) in enumerate(zip(src,out)):
            if a!=b and not allowed[i]:self.fail(f'Alteração inesperada em {i:#x}')
    def test_catalogos_eventos_golpes_e_itens_nao_sao_substituidos(self):
        for start,size in ((old.NEW_ITEMS,604*44),(old.NEW_MOVE_TABLE,315*2),
                           (old.SHOP_LIST,0x200),(complement.MOVE,807*12),
                           (complement.CATEGORY,807),(complement.ANIM,807*4)):
            self.assertEqual(self.out[start:start+size],self.source[start:start+size])
    def test_payload_adulterado_rejeitado(self):
        data=bytearray(p.PAYLOAD_PATH.read_bytes());data[-1]^=1
        with self.assertRaises(p.PatchError):p.build(self.source,bytes(data))

if __name__=='__main__':unittest.main()
