#!/usr/bin/env python3
"""Expansão para 52 áreas; guia consultável preservado; base v35 exata."""
from __future__ import annotations
import argparse,hashlib,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v36_encontros as previous, motor_v35 as base
from scripts.treino_ev import write_new_file
BASE_SHA256=base.OUTPUT_SHA256
OUTPUT_SHA256='88afd471b59e9b27dcd1e42e7b5cab6068975098b9a58361a3dd251e3b075ad0'
MENU_POINTER=0x1393B0
ORIGINAL_MENU_TABLE=0x6CE39C
ORIGINAL_MENU_COUNT=65
TABLE_OFFSET=0x1118000
SCRIPT_OFFSET=0x1118600
TEXT_OFFSET=0x1119000
RESERVED_LIMIT=0x111B000
SIGN_POINTER=previous.SIGN_POINTER
encode=base.encode
MAPS=previous.MAPS[:2]+(previous.MAPS[3],previous.MAPS[2])+previous.MAPS[4:]
GROUP_LABELS=('Rotas 1,2,22 / Floresta','Rotas 3,4,24,25','Rotas 5 a 8','Rotas 9 a 12','Rotas 13 a 16','Rotas 17,18,21N,23','Ilhas 1,2,3','Ilhas 5,6','Bosques / Ilha 7','Grutas de Kanto','Icefall - Ilha 4','Mansao Pokemon','Liga / Usina')
AREA_LABELS=('Rota 1','Rota 2','Floresta de Viridian','Rota 22','Rota 3','Rota 4','Rota 24','Rota 25','Rota 5','Rota 6','Rota 7','Rota 8','Rota 9','Rota 10','Rota 11','Rota 12','Rota 13','Rota 14','Rota 15','Rota 16','Rota 17','Rota 18','Rota 21 Norte','Rota 23','Kindle Road - Ilha 1','Treasure Beach - Ilha 1','Cape Brink - Ilha 2','Bond Bridge - Ilha 3','Five Island Meadow','Memorial Pillar - Ilha 5','Water Path - Ilha 6','Ruin Valley - Ilha 6','Berry Forest - Ilha 3','Pattern Bush - Ilha 6','Entrada Sevault - Ilha 7','Sevault Canyon - Ilha 7','Mt. Moon - 1F','Mt. Moon - B1F','Mt. Moon - B2F','Digletts Cave - B1F','Icefall - Entrada','Icefall - 1F','Icefall - B1F','Icefall - Fundos','Mansao Pokemon - 1F','Mansao Pokemon - 2F','Mansao Pokemon - 3F','Mansao Pokemon - B1F','Victory Road - 1F','Victory Road - 2F','Victory Road - 3F','Power Plant')
# Exact night species from the SHA-locked v36 policy, checked against CSV/tests.
NIGHT_NAMES=(('Hoothoot','Nickit'),('Poochyena','Houndour'),('Spinarak','Morelull'),('Murkrow','Greavard'),('Zubat','Cleffa'),('Woobat','Noibat'),('Purrloin','Drowzee'),('Shuppet','Duskull'),('Skitty','Munna'),('Poliwag','Volbeat'),('Misdreavus','Stunky'),('Illumise','Dedenne'),('Sableye','Rockruff'),('Chingling','Joltik'),('Rattata','Scraggy'),('Noctowl','Ariados'),('Drifloon','Murkrow'),('Misdreavus','Sneasel'),('Shuppet','Duskull'),('Meowth','Houndour'),('Raticate','Mightyena'),('Noctowl','Liepard'),('Shiinotic','Phantump'),('Honchkrow','Houndoom'),('Lampent','Numel'),('Sandygast','Krabby'),('Natu','Banette'),('Duskull','Greavard'),('Liepard','Purrloin'),('Gastly','Litwick'),('Noctowl','Misdreavus'),('Golett','Duskull'),('Phantump','Shiinotic'),('Venonat','Ariados'),('Houndour','Murkrow'),('Houndoom','Honchkrow'),('Cleffa','Noibat'),('Woobat','Morelull'),('Mawile','Lunatone'),('Sandshrew','Drilbur'),('Snorunt','Cryogonal'),('Sneasel','Froslass'),('Bergmite','Glalie'),('Jynx','Frosmoth'),('Shuppet','Litwick'),('Gastly','Misdreavus'),('Haunter','Banette'),('Yamask','Duskull'),('Golbat','Noivern'),('Sableye','Mawile'),('Zweilous','Absol'),('Joltik','Tynamo'))
INTRO_DAY='GUIA NOTURNO - Agora: DIA\nA: escolher / B: voltar ou sair.'
INTRO_NIGHT='GUIA NOTURNO - Agora: NOITE\nA: escolher / B: voltar ou sair.'
RULES='Noite: 20:00 a 05:59.\nDia: 06:00 a 19:59.\fCada nova especie: 1 em 10,\nantes de Repel e outros filtros.\fDemais slots e niveis mantidos.\nFrequencia e dia nao mudam.\fOcultar MUNDO nao pausa o tempo.\nSem RTC ou avanco offline.'
AREA_TEXTS=tuple(f'{label} - NOITE\n{a} / {b}.' for label,(a,b) in zip(AREA_LABELS,NIGHT_NAMES))
# Three group pages, native menus only; each origin has its own return path.
MAIN_MENU_ID=65
GROUP_MENU_IDS=tuple(range(66,79))
UTILITY_MENU_ID=79
ISLANDS_MENU_ID=80
MORE_MENU_ID=81
MENUS=(GROUP_LABELS[:6]+('Mais areas / ilhas','Horarios / sair'),)+tuple(AREA_LABELS[i:i+4]+('Voltar',) for i in range(0,52,4))+(('Horarios / regras','Voltar','Sair'),GROUP_LABELS[6:11]+('Mais areas','Voltar','Horarios / sair'),GROUP_LABELS[11:]+('Voltar','Horarios / sair'))
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
    def menu(label,ident):
        s.label(label);s.emit(bytes((0x68,0x28,2,0,0x6f,1,1,ident,0)))
    menu('top',MAIN_MENU_ID)
    for i in range(6):s.case(i,f'group{i}')
    s.case(6,'islands');s.case(7,'utilities_top')
    s.label('exit');s.emit(b'\x6b\x02')
    menu('islands',ISLANDS_MENU_ID)
    for i in range(5):s.case(i,f'group{i+6}')
    s.case(5,'more');s.case(7,'utilities_islands');s.jump('top')
    menu('more',MORE_MENU_ID)
    s.case(0,'group11');s.case(1,'group12');s.case(3,'utilities_more');s.jump('islands')
    s.label('rules');s.message(2);s.jump('intro')
    for origin in ('top','islands','more'):
        menu('utilities_'+origin,UTILITY_MENU_ID)
        s.case(0,'rules');s.case(2,'exit');s.jump(origin)
    for g in range(13):
        menu(f'group{g}',GROUP_MENU_IDS[g])
        for j in range(4):s.case(j,f'area{g*4+j}')
        s.jump('top' if g<6 else 'islands' if g<11 else 'more')
        for j in range(4):
            s.label(f'area{g*4+j}');s.message(3+g*4+j);s.jump(f'group{g}')
    return s.finish(),s.labels

SCRIPT_BYTES,SCRIPT_LABELS=script_bytes()
PATCH_RANGES=previous.PATCH_RANGES+((MENU_POINTER,4),(SIGN_POINTER,4),(TABLE_OFFSET,TABLE_SIZE),(SCRIPT_OFFSET,len(SCRIPT_BYTES)),(TEXT_OFFSET,len(TEXT_BYTES)))

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
    if len(source)!=0x2000000 or digest(source)!=BASE_SHA256:raise PatchError('Entrada não é motor_v35 exato')
    if source[TABLE_OFFSET:RESERVED_LIMIT]!=b'\xff'*(RESERVED_LIMIT-TABLE_OFFSET):raise PatchError('Reserva ocupada')
    if struct.unpack_from('<I',source,MENU_POINTER)[0]!=0x08000000+base.TABLE_OFFSET:raise PatchError('Literal de menu divergente')
    if struct.unpack_from('<I',source,SIGN_POINTER)[0]!=0x08000000+base.SCRIPT_OFFSET:raise PatchError('Placa divergente')
    if TABLE_OFFSET+TABLE_SIZE>SCRIPT_OFFSET or SCRIPT_OFFSET+len(SCRIPT_BYTES)>TEXT_OFFSET or TEXT_OFFSET+len(TEXT_BYTES)>RESERVED_LIMIT:raise PatchError('Reserva excedida')
    return previous.changes(source)+((MENU_POINTER,struct.pack('<I',0x08000000+TABLE_OFFSET)),(SIGN_POINTER,struct.pack('<I',0x08000000+SCRIPT_OFFSET)),(TABLE_OFFSET,menu_table(source)),(SCRIPT_OFFSET,SCRIPT_BYTES),(TEXT_OFFSET,TEXT_BYTES))

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
