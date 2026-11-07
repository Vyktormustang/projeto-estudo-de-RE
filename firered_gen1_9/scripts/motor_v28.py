#!/usr/bin/env python3
"""Guia consultável por grupo e área; base v27 exata, sem alterar encontros."""
from __future__ import annotations
import argparse,hashlib,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v27 as previous
from scripts.treino_ev import write_new_file
BASE_SHA256=previous.OUTPUT_SHA256
OUTPUT_SHA256='e7d11016a5c17f226ce05bc89142d52daeeee46b90c87b4b0fba29085e50cd16'
MENU_POINTER=0x1393B0
ORIGINAL_MENU_TABLE=0x6CE39C
ORIGINAL_MENU_COUNT=65
TABLE_OFFSET=0x10F0000
SCRIPT_OFFSET=0x10F0400
TEXT_OFFSET=0x10F1000
RESERVED_LIMIT=0x10F3000
SIGN_POINTER=previous.SIGN_POINTER
encode=previous.encode
MAPS=previous.MAPS[:2]+(previous.MAPS[3],previous.MAPS[2])+previous.MAPS[4:]
GROUP_LABELS=('Rotas 1,2,22 / Floresta','Rotas 3,4,24,25','Rotas 5 a 8','Rotas 9 a 12','Rotas 13 a 16')
AREA_LABELS=('Rota 1','Rota 2','Floresta de Viridian','Rota 22','Rota 3','Rota 4','Rota 24','Rota 25','Rota 5','Rota 6','Rota 7','Rota 8','Rota 9','Rota 10','Rota 11','Rota 12','Rota 13','Rota 14','Rota 15','Rota 16')
# Exact night species from the SHA-locked v27 policy, checked against CSV/tests.
NIGHT_NAMES=(('Hoothoot','Nickit'),('Poochyena','Houndour'),('Spinarak','Morelull'),('Murkrow','Greavard'),('Zubat','Cleffa'),('Woobat','Noibat'),('Purrloin','Drowzee'),('Shuppet','Duskull'),('Skitty','Munna'),('Poliwag','Volbeat'),('Misdreavus','Stunky'),('Illumise','Dedenne'),('Sableye','Rockruff'),('Chingling','Joltik'),('Rattata','Scraggy'),('Noctowl','Ariados'),('Drifloon','Murkrow'),('Misdreavus','Sneasel'),('Shuppet','Duskull'),('Meowth','Houndour'))
INTRO_DAY='GUIA NOTURNO - Agora: DIA\nA: escolher / B: voltar ou sair.'
INTRO_NIGHT='GUIA NOTURNO - Agora: NOITE\nA: escolher / B: voltar ou sair.'
RULES='Noite: 20:00 a 05:59.\nDia: 06:00 a 19:59.\fCada nova especie: 1 em 10,\nantes de Repel e outros filtros.\fDemais slots e niveis mantidos.\nFrequencia e dia nao mudam.\fOcultar MUNDO nao pausa o tempo.\nSem RTC ou avanco offline.'
AREA_TEXTS=tuple(f'{label} - NOITE\n{a} / {b}.' for label,(a,b) in zip(AREA_LABELS,NIGHT_NAMES))
MENUS=(GROUP_LABELS+('Horarios / regras','Sair'),)+tuple(AREA_LABELS[i:i+4]+('Voltar',) for i in range(0,20,4))
TEXTS=(INTRO_DAY,INTRO_NIGHT,RULES)+AREA_TEXTS+tuple(label for menu in MENUS for label in menu)
TEXT_BYTES=b'';TEXT_POINTERS=[]
for text in TEXTS:
    TEXT_POINTERS.append(0x08000000+TEXT_OFFSET+len(TEXT_BYTES));TEXT_BYTES+=encode(text)
TABLE_SIZE=(ORIGINAL_MENU_COUNT+len(MENUS))*8+sum(map(len,MENUS))*8

class PatchError(ValueError):pass

def digest(data):return hashlib.sha256(data).hexdigest()

class Script:
    def __init__(self):self.data=bytearray();self.labels={};self.fixups=[]
    def emit(self,data):self.data.extend(data)
    def label(self,name):
        if name in self.labels:raise PatchError('Rótulo duplicado')
        self.labels[name]=len(self.data)
    def jump(self,name,conditional=False):
        self.emit(b'\x06\x01' if conditional else b'\x05');self.fixups.append((len(self.data),name));self.emit(b'\0'*4)
    def case(self,value,target):
        self.emit(b'\x21'+struct.pack('<HH',0x800D,value));self.jump(target,True)
    def message(self,index):
        self.emit(b'\x67'+struct.pack('<I',TEXT_POINTERS[index])+b'\x66\x6d\x68')
    def finish(self):
        for at,name in self.fixups:struct.pack_into('<I',self.data,at,0x08000000+SCRIPT_OFFSET+self.labels[name])
        return bytes(self.data)

def script_bytes():
    s=Script();s.emit(previous.ORIGINAL_MESSAGE+b'\x69')
    s.label('intro');s.emit(b'\x23'+struct.pack('<I',previous.ENTRY_SIGN));s.case(1,'night')
    s.message(0);s.jump('top');s.label('night');s.message(1)
    # Two native frames prevent A/B dismissing a message from also choosing
    # or cancelling the newly-created menu in the same input frame.
    s.label('top');s.emit(bytes((0x68,0x28,2,0,0x6f,1,1,65,0)))
    for i in range(5):s.case(i,f'group{i}')
    s.case(5,'rules');s.emit(b'\x6b\x02') # Sair, B/cancel or unexpected result.
    s.label('rules');s.message(2);s.jump('intro') # refresh the period after rules
    for g in range(5):
        s.label(f'group{g}');s.emit(bytes((0x68,0x28,2,0,0x6f,1,1,66+g,0)))
        for j in range(4):s.case(j,f'area{g*4+j}')
        s.jump('top') # Voltar/B; no saved selection or story flag.
        for j in range(4):
            s.label(f'area{g*4+j}');s.message(3+g*4+j);s.jump(f'group{g}')
    return s.finish(),s.labels
SCRIPT_BYTES,SCRIPT_LABELS=script_bytes()
PATCH_RANGES=((MENU_POINTER,4),(SIGN_POINTER,4),(TABLE_OFFSET,TABLE_SIZE),(SCRIPT_OFFSET,len(SCRIPT_BYTES)),(TEXT_OFFSET,len(TEXT_BYTES)))

def menu_table(source):
    data=bytearray(source[ORIGINAL_MENU_TABLE:ORIGINAL_MENU_TABLE+ORIGINAL_MENU_COUNT*8]);data.extend(b'\0'*(8*len(MENUS)))
    label=3+len(AREA_TEXTS)
    for i,menu in enumerate(MENUS):
        struct.pack_into('<IB3x',data,(65+i)*8,0x08000000+TABLE_OFFSET+len(data),len(menu))
        for _ in menu:
            data+=struct.pack('<II',TEXT_POINTERS[label],0);label+=1
    if len(data)!=TABLE_SIZE:raise PatchError('Tamanho de menu divergente')
    return bytes(data)

def changes(source):
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:raise PatchError('Entrada não é motor_v27 exato')
    if source[TABLE_OFFSET:RESERVED_LIMIT]!=b'\xff'*(RESERVED_LIMIT-TABLE_OFFSET):raise PatchError('Reserva ocupada')
    if struct.unpack_from('<I',source,MENU_POINTER)[0]!=0x08000000+ORIGINAL_MENU_TABLE:raise PatchError('Literal de menu divergente')
    if struct.unpack_from('<I',source,SIGN_POINTER)[0]!=0x08000000+previous.SCRIPT_OFFSET:raise PatchError('Placa divergente')
    if TABLE_OFFSET+TABLE_SIZE>SCRIPT_OFFSET or SCRIPT_OFFSET+len(SCRIPT_BYTES)>TEXT_OFFSET or TEXT_OFFSET+len(TEXT_BYTES)>RESERVED_LIMIT:raise PatchError('Reserva excedida')
    return ((MENU_POINTER,struct.pack('<I',0x08000000+TABLE_OFFSET)),(SIGN_POINTER,struct.pack('<I',0x08000000+SCRIPT_OFFSET)),(TABLE_OFFSET,menu_table(source)),(SCRIPT_OFFSET,SCRIPT_BYTES),(TEXT_OFFSET,TEXT_BYTES))

def build(source):
    out=bytearray(source)
    for at,data in changes(source):out[at:at+len(data)]=data
    result=bytes(out)
    if digest(result)!=OUTPUT_SHA256:raise PatchError('Hash final divergente')
    return result

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--rom',type=Path,required=True);a.add_argument('--saida',type=Path,required=True);args=a.parse_args()
    result=build(args.rom.read_bytes());write_new_file(args.rom,args.saida,result);print(f'{args.saida}: {len(result)} B SHA-256 {digest(result)}')
if __name__=='__main__':main()
