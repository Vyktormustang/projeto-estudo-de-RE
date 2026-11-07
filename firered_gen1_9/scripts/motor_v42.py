#!/usr/bin/env python3
"""Native-script ticket delivery by Vermilion's ferry sailor after Rainbow Pass.

Exact v41 input, new output only. No battle, encounter, save-format or event reset.
Per-item delivery is retryable: if only one key-item slot is free, Mystic succeeds
and Aurora remains pending. Existing tickets repair only missing ferry flags.
"""
from __future__ import annotations
import argparse,hashlib,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v41 as base,atualizacoes_gen9 as items
from scripts.treino_ev import write_new_file
BASE_SHA256=base.OUTPUT_SHA256
OUTPUT_SHA256='6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a'
POINTER_OFFSET=0x7C0F3C
OLD_SCRIPT=0x0818F32D
HOOK_OFFSET=OLD_SCRIPT-0x08000000
ORIGINAL_PREFIX=bytes.fromhex('6a 5a 21 7e 40 03 00')
RESUME_SCRIPT=OLD_SCRIPT+len(ORIGINAL_PREFIX)
SCRIPT_OFFSET=0x1135000
TEXT_OFFSET=0x1135400
RESERVED_LIMIT=0x1136000
RAINBOW_PASS=368
TICKETS=((370,0x84A),(371,0x84B))
TEXTS=(
    'Recebeu o MYSTIC TICKET!\nViagem a Navel Rock liberada.',
    'MYSTIC TICKET confirmado.\nViagem a Navel Rock liberada.',
    'Recebeu o AURORA TICKET!\nViagem a Birth Island liberada.',
    'AURORA TICKET confirmado.\nViagem a Birth Island liberada.',
    'Sem espaco para este bilhete.\nLibere espaco e volte a falar.',
)
encode=base.base.encode
TEXT_BYTES=b'';TEXT_POINTERS=[]
for text in TEXTS:
    TEXT_POINTERS.append(0x08000000+TEXT_OFFSET+len(TEXT_BYTES));TEXT_BYTES+=encode(text)

class PatchError(ValueError):pass

def digest(b):return hashlib.sha256(b).hexdigest()
def require(ok,message):
    if not ok:raise PatchError(message)

class Script:
    def __init__(self):self.data=bytearray();self.labels={};self.fixups=[]
    def emit(self,b):self.data.extend(b)
    def label(self,name):
        require(name not in self.labels,'Duplicate label');self.labels[name]=len(self.data)
    def jump(self,name,condition=None):
        self.emit(b'\x05' if condition is None else bytes((6,condition)))
        self.fixups.append((len(self.data),name));self.emit(bytes(4))
    def compare(self,var,value):self.emit(b'\x21'+struct.pack('<HH',var,value))
    def item(self,opcode,item):self.emit(bytes((opcode,))+struct.pack('<HH',item,1))
    def flag(self,opcode,flag):self.emit(bytes((opcode,))+struct.pack('<H',flag))
    def message(self,index):self.emit(b'\x67'+struct.pack('<I',TEXT_POINTERS[index])+b'\x66\x6D\x68')
    def finish(self):
        for at,name in self.fixups:struct.pack_into('<I',self.data,at,0x08000000+SCRIPT_OFFSET+self.labels[name])
        return bytes(self.data)

def script_bytes():
    s=Script()
    # Native comparison codes: 0 less-than, 1 equal, 5 not-equal.
    s.compare(0x407E,3);s.jump('original',5)
    s.compare(0x4076,5);s.jump('original',0)
    s.item(0x47,RAINBOW_PASS);s.compare(0x800D,0);s.jump('original',1)
    # Native quest-log convention: 2 means playback. Do not grant during replay.
    s.emit(bytes.fromhex('25 87 01'));s.compare(0x800D,2);s.jump('original',1)
    s.emit(b'\x6A\x5A') # lock, faceplayer
    s.emit(bytes.fromhex('16 00 80 00 00')) # temporary VAR_8000: any addition failed
    for i,(item,flag) in enumerate(TICKETS):
        s.label(f'item{i}');s.item(0x47,item);s.compare(0x800D,1);s.jump(f'owned{i}',1)
        s.item(0x44,item);s.compare(0x800D,0);s.jump(f'failed{i}',1)
        s.flag(0x29,flag);s.message(2*i);s.jump(f'next{i}')
        s.label(f'owned{i}');s.flag(0x2B,flag);s.jump(f'next{i}',1)
        s.flag(0x29,flag);s.message(2*i+1);s.jump(f'next{i}')
        s.label(f'failed{i}');s.emit(bytes.fromhex('16 00 80 01 00'))
        s.label(f'next{i}')
    s.compare(0x8000,0);s.jump('resume',1)
    s.label('full');s.message(4)
    s.label('resume');s.emit(b'\x6C') # release before original lock/faceplayer
    s.label('original');s.emit(ORIGINAL_PREFIX+b'\x05'+struct.pack('<I',RESUME_SCRIPT))
    return s.finish(),s.labels

SCRIPT_BYTES,SCRIPT_LABELS=script_bytes()
HOOK_BYTES=b'\x05'+struct.pack('<I',0x08000000+SCRIPT_OFFSET)+b'\x00\x00'
PATCH_RANGES=((HOOK_OFFSET,len(HOOK_BYTES)),(SCRIPT_OFFSET,len(SCRIPT_BYTES)),(TEXT_OFFSET,len(TEXT_BYTES)))

def validate_source(b):
    require(len(b)==0x2000000 and digest(b)==BASE_SHA256,'Not exact v41')
    require(struct.unpack_from('<I',b,POINTER_OFFSET)[0]==OLD_SCRIPT,'Wrong sailor script pointer')
    require(b[HOOK_OFFSET:HOOK_OFFSET+7]==ORIGINAL_PREFIX,'Wrong original script prefix')
    require(SCRIPT_OFFSET>=base.base.RESERVED_LIMIT,'Reservation overlaps previous release')
    require(b[SCRIPT_OFFSET:RESERVED_LIMIT]==b'\xff'*(RESERVED_LIMIT-SCRIPT_OFFSET),'Reserved space is not empty')
    require(SCRIPT_OFFSET+len(SCRIPT_BYTES)<=TEXT_OFFSET and TEXT_OFFSET+len(TEXT_BYTES)<=RESERVED_LIMIT,'Reservation overflow')
    for at,(value,) in enumerate(struct.iter_unpack('<I',b)):
        require(not 0x08000000+SCRIPT_OFFSET<=value<0x08000000+RESERVED_LIMIT,f'Reserved reference at {4*at:X}')
    for item,name in ((368,'RAINBOW PASS'),(370,'MYSTICTICKET'),(371,'AURORATICKET')):
        at=items.NEW_ITEMS+item*items.ITEM_SIZE
        require(b[at:at+14].split(b'\xff')[0]==encode(name)[:-1] and b[at+26]==2,'Unexpected key item definition')

def build(source):
    validate_source(source);out=bytearray(source)
    out[HOOK_OFFSET:HOOK_OFFSET+len(HOOK_BYTES)]=HOOK_BYTES
    out[SCRIPT_OFFSET:SCRIPT_OFFSET+len(SCRIPT_BYTES)]=SCRIPT_BYTES
    out[TEXT_OFFSET:TEXT_OFFSET+len(TEXT_BYTES)]=TEXT_BYTES
    result=bytes(out);restored=bytearray(result)
    for at,n in PATCH_RANGES:restored[at:at+n]=source[at:at+n]
    require(bytes(restored)==source,'Changed bytes outside declared ranges')
    require(digest(result)==OUTPUT_SHA256,'Wrong output hash')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);a=p.parse_args()
    source=a.rom.read_bytes();out=build(source);write_new_file(a.rom,a.saida,out)
    require(a.rom.read_bytes()==source,'Input changed');print(f'v42: {digest(out)}; {len(SCRIPT_BYTES)} B script + {len(TEXT_BYTES)} B text; three ranges')
if __name__=='__main__':main()
