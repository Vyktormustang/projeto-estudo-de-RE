#!/usr/bin/env python3
"""Read-only structural acquisition inventory of the exact v40. Not a capture certificate.

No ROM writes, no game saves. Output directory must not exist.
Native event opcodes are decoded from actual map roots, never by raw byte matches.
Reference semantics: pret/pokefirered ce6406d8c2eaf46d543c8a2606de0c3cb1951982.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,struct,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v40 as release, encontros_selvagens as wild, eventos_fixos as fixed

EVO_TABLE=0x6AB6A8
EVO_LITERAL=0x10DDA8
# National species, map group/number, object or coordinate-trigger index (1-based).
NATIVE=((144,1,87,'objeto',3),(145,1,95,'objeto',6),(146,1,101,'objeto',1),
        (150,1,74,'objeto',3),(249,2,38,'objeto',1),(250,2,37,'coordenada',1),
        (386,2,56,'objeto',1))
SIZES={0x02:1,0x03:1,0x04:5,0x05:5,0x06:6,0x07:6,0x16:5,0x19:5,
       0x21:5,0x25:3,0x26:5,0x27:1,0x28:3,0x29:3,0x2A:3,0x2B:3,
       0x2F:3,0x30:1,0x33:4,0x4F:7,0x51:3,0x55:3,0x5A:1,0x66:1,0x67:5,
       0x69:1,0x6A:1,0x6B:1,0x6C:1,0x6D:1,0x9C:3,0x9D:4,0x9E:3,
       0xA1:5,0xA4:3,0xA5:1,0xB6:6,0xC5:1}

class AuditError(ValueError):pass

def require(ok,msg):
    if not ok:raise AuditError(msg)

def u16(b,at):return struct.unpack_from('<H',b,at)[0]
def u32(b,at):return struct.unpack_from('<I',b,at)[0]
def pointer(b,at,size=1):
    n=u32(b,at)-0x08000000
    require(0<=n<=len(b)-size,f'Invalid pointer at {at:X}')
    return n

def map_data(b,g,m):
    hdr=pointer(b,pointer(b,fixed.GROUP_TABLE+4*g)+4*m,28)
    ev=pointer(b,hdr+4,20);layout=pointer(b,hdr,8)
    return hdr,ev,struct.unpack_from('<II',b,layout)

def objects(b,cat):
    active=[];parked=[];total=0;refs=set()
    for m in fixed.load_map_catalog():
        _,ev,(w,h)=map_data(b,m.group,m.number)
        count=b[ev];total+=count
        if not count:continue
        base=pointer(b,ev+4,count*24)
        for i in range(count):
            at=base+i*24
            require(b[at]==i+1,'Object order changed')
            if u32(b,at+16)!=fixed.GENERIC_SCRIPT:continue
            refs.add(at+16);sid=u16(b,at+14);x,y=struct.unpack_from('<hh',b,at+4)
            require(sid in cat and b[at+1:at+3]==bytes((0x98,0)) and b[at+9]==8
                    and u16(b,at+12)==0 and u16(b,at+20)==0x5000+sid,'Unknown shared object')
            entry=dict(species=sid,map=m.label,group=m.group,number=m.number,object=i+1,
                       offset=at,x=x,y=y,flag=u16(b,at+20),script=fixed.GENERIC_SCRIPT-0x08000000)
            if (x,y)==(-1024,-1024):
                require(fixed.category(cat[sid])=='comum','Parked special');parked.append(entry)
            else:
                require(0<=x<w and 0<=y<h and fixed.category(cat[sid])!='comum','Unexpected active object')
                active.append(entry)
    actual=set();at=0;sig=struct.pack('<I',fixed.GENERIC_SCRIPT)
    while True:
        at=b.find(sig,at)
        if at<0:break
        actual.add(at);at+=1
    require(refs==actual,'Uncatalogued shared script reference')
    require((total,len(active),len(parked))==(1982,110,224),'Object census changed')
    require(len({x['species'] for x in active+parked})==334,'Duplicate shared species')
    return active,parked

def native_path(b,root):
    """Explore possible branches to preparation + legendary battle. Conditions not solved.

    Fail closed on unknown opcodes. Track constant special variables and a call stack;
    do not treat speech, movement, or operand bytes as executable instructions.
    """
    work=[(root,(),(),None,())];seen=set();found=[]
    while work:
        pc,stack,env_items,pending,path=work.pop();key=(pc,stack,env_items,pending)
        if key in seen:continue
        seen.add(key);require(len(seen)<=4096 and len(stack)<=16,'Unbounded script')
        require(0<=pc<len(b),'Script pointer outside ROM');op=b[pc]
        require(op in SIZES,f'Unsupported native opcode {op:02X} at {pc:X}')
        nxt=pc+SIZES[op];require(nxt<=len(b),'Truncated script');env=dict(env_items);path=path+(pc,)
        if op==0x02:continue
        if op==0x03:
            if stack:work.append((stack[-1],stack[:-1],env_items,pending,path))
            continue
        if op in (4,5,6,7):
            target=pointer(b,pc+(2 if op in (6,7) else 1))
            work.append((target,stack+(nxt,) if op in (4,7) else stack,env_items,pending,path))
            if op in (6,7):work.append((nxt,stack,env_items,pending,path))
            continue
        if op==0x16:env[u16(b,pc+1)]=u16(b,pc+3)
        if op==0x19:env.pop(u16(b,pc+1),None)
        if op==0xB6:pending=(u16(b,pc+1),b[pc+3],u16(b,pc+4),pc,'setwildbattle')
        if op==0x25:
            special=u16(b,pc+1)
            if special==0x1BB:
                require(all(v in env for v in (0x8004,0x8005,0x8006)),'Nonconstant event mon')
                pending=(env[0x8004],env[0x8005],env[0x8006],pc,'CreateEnemyEventMon')
            if special==0x138 and pending:
                sid,level,item,prepare,method=pending
                found.append(dict(species=sid,level=level,item=item,prepare_offset=prepare,
                                  battle_offset=pc,method=method,path=list(path)))
                continue
        work.append((nxt,stack,tuple(sorted(env.items())),pending,path))
    unique={(x['species'],x['level'],x['prepare_offset'],x['battle_offset']):x for x in found}
    require(len(unique)==1,'No unique native legendary path')
    return next(iter(unique.values()))

def native_events(b):
    names={(m.group,m.number):m.label for m in fixed.load_map_catalog()};result=[]
    for sid,g,m,kind,index in NATIVE:
        _,ev,_=map_data(b,g,m)
        if kind=='objeto':
            require(index<=b[ev],'Native object missing');at=pointer(b,ev+4)+24*(index-1)
            root=pointer(b,at+16);coords=struct.unpack_from('<hh',b,at+4)
            condition=f'flag de ocultacao {u16(b,at+20):04X}; condicoes do evento'
        else:
            require(index<=b[ev+2],'Native coordinate trigger missing');at=pointer(b,ev+12)+16*(index-1)
            root=pointer(b,at+12);coords=struct.unpack_from('<HH',b,at)
            condition=f'variavel {u16(b,at+6):04X} = {u16(b,at+8)}; gatilho de coordenada'
        event=native_path(b,root);require(event['species']==sid,'Native species mismatch')
        event.update(map=names[g,m],group=g,number=m,root=root,trigger=kind,trigger_offset=at,
                     x=coords[0],y=coords[1],condition=condition)
        result.append(event)
    return result

def evolutions(b):
    # Derived from actual Thumb loads at 0810DBF0 / 0810DC32 / 0810DC66:
    # species stride 64, entry stride 8, eight entries. No vanilla addresses imported.
    require(pointer(b,EVO_LITERAL)==EVO_TABLE,'Evolution table literal changed')
    rows=[]
    for sid in range(1,1026):
        for slot in range(8):
            at=EVO_TABLE+sid*64+slot*8;method,param,target,pad=struct.unpack_from('<4H',b,at)
            if not method:
                require((param,target,pad)==(0,0,0),'Nonempty absent evolution');continue
            require(1<=target<=1025 and pad==0,'Invalid evolution record')
            rows.append(dict(source=sid,target=target,method=method,param=param,slot=slot,offset=at))
    for pair,level in (((789,790),43),((790,791),53),((790,792),54)):
        require(any((x['source'],x['target'],x['method'],x['param'])==(*pair,4,level) for x in rows),'Cosmog chain changed')
    return rows

def csv_text(rows,fields):
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
    return s.getvalue()

def audit(b):
    require(release.digest(b)==release.OUTPUT_SHA256 and len(b)==0x2000000,'Not exact v40')
    fixed.checked_catalogs();cat=wild.load_species();require(set(cat)==set(range(1,1026)),'Catalog incomplete')
    tables=wild.parse_tables(b,wild.load_maps(),cat)
    night=release.previous.pilot_tables(b)
    require(night==b[release.previous.TABLE_OFFSET:release.previous.TABLE_OFFSET+len(night)],'Night tables differ')
    night_index={name:i for i,name in enumerate(release.previous.MAPS)}
    locations=[]
    for t in tables:
        for period in (('dia','noite') if t.kind=='land' and t.map.symbol in night_index else ('ambos',)):
            for s in t.slots:
                sid,lo,hi=s.species,s.min_level,s.max_level;at=s.offset
                if period=='noite':
                    index=night_index[t.map.symbol];info=pointer(b,release.previous.TABLE_OFFSET+index*12+4)
                    at=pointer(b,info+4)+s.index*4;lo,hi,sid=struct.unpack_from('<BBH',b,at)
                eligible=t.map.eligible and t.kind in ('land','water')
                condition='Acesso ao mapa/metodo e filtros de encontro nao certificados'
                if t.map.is_tanoby_chamber:condition='Tanoby: desbloqueio por FLAG 0849; puzzle/acesso nao certificados'
                if 'ALTERING_CAVE' in t.map.symbol:condition=f'Altering Cave: VAR 4024 = {t.map.index-123}; selecao/acesso nao certificados'
                locations.append(dict(species=sid,name=cat[sid].name,map=t.map.label,group=t.map.group,
                    number=t.map.number,header_index=t.map.index,kind=t.kind,period=period,slot=s.index,
                    min_level=lo,max_level=hi,nominal_percent=s.chance,eligible=int(eligible),condition=condition,offset=f'{at:08X}'))
    active,parked=objects(b,cat);natives=native_events(b);evos=evolutions(b)
    by=defaultdict(list)
    for loc in locations:by[loc['species']].append(loc)
    fixed_by={x['species']:x for x in active};native_by={x['species']:x for x in natives}
    covered=wild.covered_species(tables);all_wild={s.species for t in tables for s in t.slots}
    preferred=[]
    for sid,species in cat.items():
        regular=[x for x in by[sid] if x['eligible']]
        condition='Acesso natural e captura individual nao certificados nesta auditoria'
        level=chance=period='';reference=''
        if regular or sid==201:
            candidates=regular or [x for x in by[sid] if 'Tanoby' in x['map']]
            loc=min(candidates,key=lambda x:(-x['nominal_percent'],x['min_level'],x['header_index'],x['slot'],x['period']))
            route='tabela_elegivel' if regular else 'tanoby_condicional'
            place=loc['map'];condition=loc['condition'];period=loc['period']
            level=f"{loc['min_level']}-{loc['max_level']}";chance=str(loc['nominal_percent']);reference=loc['offset']
        elif sid in fixed_by:
            x=fixed_by[sid];route='fixo_adicional';place=x['map'];reference=f"{x['offset']:08X}"
            condition=f"Objeto {x['object']}; flag {x['flag']:04X}; acesso/acionamento/captura nao certificados"
        elif sid in native_by:
            x=native_by[sid];route='evento_nativo';place=x['map'];level=str(x['level']);reference=f"{x['root']:08X}"
            condition=x['condition']+'; acesso/captura nao certificados'
            if sid in (249,250,386):condition+='; verificar bilhete/evento de acesso a ilha'
        elif sid in (790,791,792):
            route='evolucao_configurada';place='Cosmog -> Cosmoem' if sid==790 else 'Cosmoem -> '+species.name
            level=str({790:43,791:53,792:54}[sid]);period='qualquer (regra simplificada da base)'
            condition='Obter Cosmog; validar evolucao completa e disponibilidade de copias'
            if sid==792:condition+='; manter Cosmoem ate nivel 54 (nao evoluir no 53)'
            reference=','.join(f"{x['offset']:08X}" for x in evos if x['target']==sid)
        elif by[sid]:
            loc=by[sid][0];route='tabela_excluida_condicional';place=loc['map'];condition=loc['condition']
            level=f"{loc['min_level']}-{loc['max_level']}";chance=str(loc['nominal_percent']);period=loc['period'];reference=loc['offset']
        else:route='sem_rota_identificada';place='';condition='Investigar antes de afirmar disponibilidade'
        preferred.append(dict(pokedex=sid,pokemon=species.name,geracao=species.generation,categoria=fixed.category(species),
            rota=route,local=place,periodo=period,nivel=level,chance_nominal_slot_pct=chance,
            referencia_offset=reference,ocorrencias_tabelas=len(by[sid]),condicoes_e_pendencias=condition,
            captura_individual_nesta_auditoria='nao'))
    summary=dict(version='v40',rom_sha256=release.OUTPUT_SHA256,read_only=True,catalog_species=len(cat),
        nonlegendary_mythical=931,nonlegendary_mythical_covered=len({i for i in covered if not cat[i].protected}),
        eligible_plus_tanoby_species=len(covered),all_wild_raw_species=len(all_wild),
        active_additional_objects=len(active),parked_additional_objects=len(parked),
        additional_unique_species=len(fixed_by),active_additional_events=active,native_events=natives,
        raw_wild_plus_additional=len(all_wild|set(fixed_by)),
        missing_before_native_and_evolution=sorted(set(cat)-(all_wild|set(fixed_by))),
        preferred_route_counts=dict(Counter(x['rota'] for x in preferred)),
        no_route=[x['pokedex'] for x in preferred if x['rota']=='sem_rota_identificada'],
        evolution_records=len(evos),evolution_methods=dict(Counter(x['method'] for x in evos)),
        capture_certified_species=0,scope='Structural data and targeted script paths, not all-game reachability or captures')
    return preferred,locations,evos,summary

def event_rows(summary):
    """All 117 active event locations, including alternatives to ordinary tables."""
    names=wild.load_species();rows=[]
    for kind,key in (('fixo_adicional','active_additional_events'),('evento_nativo','native_events')):
        for x in summary[key]:
            rows.append(dict(species=x['species'],name=names[x['species']].name,kind=kind,
                map=x['map'],group=x['group'],number=x['number'],x=x['x'],y=x['y'],
                object=x.get('object',''),level=x.get('level',''),flag=x.get('flag',''),
                root_offset=f"{x.get('root',x.get('script')):08X}",
                trigger_offset=f"{x.get('trigger_offset',x.get('offset')):08X}",
                trigger=x.get('trigger','objeto'),condition=x.get('condition','Flag de ocultacao; acesso/acionamento/captura nao certificados')))
    return sorted(rows,key=lambda x:(x['species'],x['kind']))


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--rom',type=Path,required=True);a.add_argument('--saida',type=Path,required=True);args=a.parse_args()
    source=args.rom.read_bytes();rows,locs,evos,summary=audit(source)
    args.saida.mkdir(parents=True,exist_ok=False)
    for name,data in (('cobertura_1025_v40.csv',rows),('locais_obtencao_v40.csv',locs),('evolucoes_v40.csv',evos),('eventos_obtencao_v40.csv',event_rows(summary))):
        with (args.saida/name).open('x',encoding='utf-8',newline='') as out:out.write(csv_text(data,list(data[0])))
    with (args.saida/'auditoria_obtencao_v40.json').open('x',encoding='utf-8') as out:json.dump(summary,out,ensure_ascii=False,indent=2);out.write('\n')
    require(args.rom.read_bytes()==source,'Input changed')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('native_events','active_additional_events')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
