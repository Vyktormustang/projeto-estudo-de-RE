#!/usr/bin/env python3
"""Acrescenta Hard Press e consumo de TMs ao estojo paginado.

É uma melhoria parcial, não um motor Gen 9 completo. Aceita somente a ROM
exata do estojo; cria outro arquivo e não edita saves pessoais.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import complemento_gen9 as complement, atualizacoes_gen9 as previous
from scripts.treino_ev import write_new_file

BASE_SHA256='93dc62e86cfa3dc70c8057fa4ea25031761d48fc5ce4f7615a5a66d4fc280907'
OUTPUT_SHA256=''
INPUTS={
    ROOT/'patches/motor_ampliado/payload.bin':'25adb4046b042f23da6d3427c66e94cfa85ec57ff4b49f8ba325b7c0a47ccdd8',
    ROOT/'patches/motor_ampliado/consumo1.bin':'9f50f3fde936052b681ae04ddb7454458c7a07ef5b5a8f8675749fed2e527898',
    ROOT/'patches/motor_ampliado/consumo2.bin':'384ce907a0338454b03cb8656166cc1d548185d2672ce4092eff8aefb3192f8f',
    ROOT/'patches/motor_ampliado/consumo3.bin':'3b15dbabd8d885a03804c4de7ec2da6fd99cdd47da5c4bca51cb3400b7c2b225',
    ROOT/'patches/motor_ampliado/animacao_inline.bin':'a30b116efbde05294b9daaa5549f896ad2552ca91bb65c882fc86f23494d25cc',
    ROOT/'patches/motor_ampliado/animacao_func.bin':'f4d5d0b8cd86bfb711d25ca028f5396e1a0e5680006ade9e7277eb9774039290',
    ROOT/'patches/motor_ampliado/registro_substituiu.bin':'c4e2d898baf27563951155f7b2375d2ef2437a93b342667326ea09f4aaf0e0ba',
    ROOT/'patches/motor_ampliado/registro_aprendeu.bin':'323158247c51cfc10e06f02d2f097a5b18a77be28d573d1be56810db34d04f99',
    ROOT/'patches/complemento_gen9/payload.bin':'3e54b4263b312584f11a7809b39093c590848cb1a2b35c6668cc9427752b22c4',
    ROOT/'data/tms_motor_ampliado.csv':'b1d9110d08e06314a731609647629bc64a40708bc62e830ed35864b71a1aad79',
    ROOT/'data/compatibilidade_tms_motor_ampliado.bin':'484244b19b9bb30ac5dee089beb3d28f4a4fdbf25f27bf625275797ac19c3c71',
    ROOT/'data/compatibilidade_tms_complemento.bin':'23de53c08991baa31623eb184f277420e743770965b920294615e01e61d278d3',
}
MOVE=807; API_MOVE=912; TM=225; ITEM=599; TEXT=0x10BB000
ITEM_TEXT_START,ITEM_TEXT_END=0x10B9000,0x10BB000
CONSUME_SITES=(
    (0x0fccb8,'a9 23 20 88 5b 00 98 42 03 d9 30 68 03 f7 66 fc d7 e7 01 21 c9 f7 34 ff f7 e7 c0 46'),
    (0x0fcd7c,'43 46 18 88 a9 23 5b 00 98 42 03 d9 20 68 03 f7 03 fc c5 e7 01 21 c9 f7 d1 fe f7 e7'),
    (0x0fdcfc,'a9 23 5b 00 9f 42 c5 d8 01 21 38 00 c8 f7 16 ff c0 e7 c0 46'),
)
ANIM_SITES=(
    (0x1149e4,'animacao_inline.bin','44 2d 42 d0 0d 2d 42 d0 2a 00 00 23 39 21 22 3a ff 3a 12 04 12 0c 91 42 5b 41 9b 00'),
    (0x115344,'animacao_func.bin','00 04 00 0c 44 28 0b d0 0d 28 0b d0 22 38 ff 38 03 04 39 22 00 20 1b 0c 9a 42 40 41 80 00 70 47 00 20 fc e7'),
)
REG_SITES=(
    (0x12c3bc,'registro_substituiu.bin','a9 23 22 88 5b 00 9a 42 26 d9'),
    (0x12c3ec,'registro_aprendeu.bin','a9 23 22 88 5b 00 9a 42 09 d9'),
)
ROM=0x08000000
class PatchError(ValueError):pass

def digest(data):return hashlib.sha256(data).hexdigest()

def checked_inputs():
    result={}
    for path,sha in INPUTS.items():
        data=path.read_bytes()
        if digest(data)!=sha:raise PatchError(f'Arquivo de dados divergente: {path.name}')
        result[path]=data
    return result

def build(source:bytes,inputs=None)->bytes:
    if len(source)!=0x2000000 or source[0xAC:0xB0]!=b'BPRE' or digest(source)!=BASE_SHA256:
        raise PatchError('Entrada não é o rascunho de estojo identificado')
    inputs=checked_inputs() if inputs is None else inputs
    for path,sha in INPUTS.items():
        if path not in inputs or digest(inputs[path])!=sha:raise PatchError(f'Dados inválidos: {path.name}')
    rows=list(csv.DictReader(io.StringIO(inputs[ROOT/'data/tms_motor_ampliado.csv'].decode())))
    if len(rows)!=229:raise PatchError('Catálogo de TMs incompleto')
    available={int(r['tm']):int(r['internal_move']) for r in rows if r['status']=='disponivel'}
    if len(available)!=204 or available.get(TM)!=MOVE:raise PatchError('Catálogo de TMs inconsistente')
    prior=inputs[ROOT/'data/compatibilidade_tms_complemento.bin']
    compat=inputs[ROOT/'data/compatibilidade_tms_motor_ampliado.bin']
    if len(prior)!=1026*29 or len(compat)!=len(prior):raise PatchError('Matriz inválida')
    changes=[]
    for i,(a,b) in enumerate(zip(prior,compat)):
        if a!=b:
            if i%29 != (TM-1)//8 or (a^b)!=(1<<((TM-1)%8)) or a&~b:
                raise PatchError('Compatibilidade anterior foi alterada')
            changes.append(i//29)
    if len(changes)!=43 or 0 in changes:raise PatchError('Compatibilidade nova divergente')
    payload=inputs[ROOT/'patches/motor_ampliado/payload.bin']
    original=inputs[ROOT/'patches/complemento_gen9/payload.bin']
    if len(payload)>0x1000 or source[0x100c000:0x100c000+len(original)]!=original:
        raise PatchError('Código anterior de dano divergente')
    if source[0x100c000+len(original):0x100c000+len(payload)]!=b'\xff'*max(0,len(payload)-len(original)):
        raise PatchError('Área de dano ocupada')
    checks=((complement.MOVE+MOVE*12,12),(complement.NAMES+MOVE*17,17),
            (complement.ANIM+MOVE*4,4),(complement.DESC+(MOVE-1)*4,4),
            (complement.CATEGORY+MOVE,1),(TEXT,0x100),
            (ITEM_TEXT_START,ITEM_TEXT_END-ITEM_TEXT_START))
    for at,size in checks:
        if source[at:at+size]!=b'\xff'*size:raise PatchError(f'Área reservada ocupada: {at:#x}')
    move_slot=previous.NEW_MOVE_TABLE+(ITEM-289)*2
    if struct.unpack_from('<H',source,move_slot)[0]!=0:raise PatchError('TM225 já ocupada')
    item_slot=previous.NEW_ITEMS+ITEM*previous.ITEM_SIZE
    if struct.unpack_from('<I',source,item_slot+20)[0]!=0x08e18a00:raise PatchError('Descrição anterior mudou')
    if source[0xe06000:0xe06000+len(prior)]!=prior:raise PatchError('Matriz da ROM divergente')
    for i,(at,old_code) in enumerate(CONSUME_SITES,1):
        old=bytes.fromhex(old_code);new=inputs[ROOT/f'patches/motor_ampliado/consumo{i}.bin']
        if source[at:at+len(old)]!=old or len(new)!=len(old):
            raise PatchError(f'Trecho de consumo inesperado: {at:#x}')
    for at,name,old_code in ANIM_SITES+REG_SITES:
        old=bytes.fromhex(old_code);new=inputs[ROOT/'patches/motor_ampliado'/name]
        if source[at:at+len(old)]!=old or len(new)!=len(old):
            raise PatchError(f'Trecho de código inesperado: {at:#x}')
    out=bytearray(source)
    for at,name,_ in ANIM_SITES+REG_SITES:
        new=inputs[ROOT/'patches/motor_ampliado'/name]
        out[at:at+len(new)]=new
    for i,(at,old_code) in enumerate(CONSUME_SITES,1):
        new=inputs[ROOT/f'patches/motor_ampliado/consumo{i}.bin']
        out[at:at+len(new)]=new
    out[0x100c000:0x100c000+len(payload)]=payload
    out[complement.MOVE+MOVE*12:complement.MOVE+(MOVE+1)*12]=bytes((0,1,8,100,10,0,0,0,0x33,0,0,0))
    name=previous.text('HARD PRESS')
    out[complement.NAMES+MOVE*17:complement.NAMES+(MOVE+1)*17]=name+bytes(17-len(name))
    out[complement.CATEGORY+MOVE]=0
    struct.pack_into('<I',out,complement.ANIM+MOVE*4,0x08175F3A)  # animação genérica
    desc=previous.text('PODER AUMENTA\nCOM HP DO ALVO.')
    out[TEXT:TEXT+len(desc)]=desc
    struct.pack_into('<I',out,complement.DESC+(MOVE-1)*4,ROM+TEXT)
    struct.pack_into('<H',out,move_slot,MOVE)
    out[0xe06000:0xe06000+len(compat)]=compat
    # Atualizar TODAS as descrições da loja: as TMs SV agora são de uso único.
    # HMs e itens antigos conservam seus ponteiros e a regra original.
    cursor=ITEM_TEXT_START
    for tm,mid in sorted(available.items()):
        entry=out[complement.NAMES+mid*17:complement.NAMES+(mid+1)*17]
        if 0xff not in entry:raise PatchError(f'Nome do golpe {mid} sem terminador')
        move_name=entry[:entry.index(0xff)]
        text=previous.text('GOLPE ')[:-1]+move_name+previous.text('\nUSO UNICO')
        if cursor+len(text)>ITEM_TEXT_END:raise PatchError('Descrições excedem a área reservada')
        out[cursor:cursor+len(text)]=text
        struct.pack_into('<I',out,previous.NEW_ITEMS+(374+tm)*previous.ITEM_SIZE+20,ROM+cursor)
        cursor+=len(text)
    products=b''.join(struct.pack('<H',374+tm) for tm in sorted(available))+b'\0\0'
    if len(products)>previous.SHOP_SCRIPT-previous.SHOP_LIST:raise PatchError('Lista de loja excedeu o espaço')
    out[previous.SHOP_LIST:previous.SHOP_LIST+len(products)]=products
    return bytes(out)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True);parser.add_argument('--saida',type=Path,required=True)
    a=parser.parse_args()
    try:
        if a.rom.resolve()==a.saida.resolve() or a.saida.exists():raise PatchError('A saída precisa ser um arquivo novo')
        src=a.rom.read_bytes();out=build(src)
        if OUTPUT_SHA256 and digest(out)!=OUTPUT_SHA256:raise PatchError('SHA da saída divergente')
        write_new_file(a.rom,a.saida,out)
        print(f'Entrada preservada: {digest(src)}\nNova cópia: {a.saida}\nSHA-256: {digest(out)}')
        print('Rascunho parcial: outras TMs e várias mecânicas continuam pendentes.')
    except (OSError,ValueError) as exc:
        print(f'[ERRO] {exc}',file=sys.stderr);return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
