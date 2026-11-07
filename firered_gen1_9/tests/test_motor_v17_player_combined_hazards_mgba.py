"""Hazards combinados na seleção do jogador em duplas, ROM v17 exata.

Colocação real + Court Change, Rock Slide real e escolhas/rejeições pela UI.
Nenhuma escrita de RAM depois do preparo; dano/status acompanhados por PID.
"""
import unittest
import test_motor_v17_combined_hazards_mgba as current
from battle_fixture_helpers import main_callback2, in_battle

old,h,ending,doubles=current.old,current.h,current.ending,current.doubles
ORDER=old.offset(0x0203FC90)
TSP=old.offset(old.V8_STATE_ADDR)+14


def oracle(order,layers,first,health,poison_slot=None):
    """Regra independente: estado de campo compartilhado entre as entradas."""
    queue=list(order)+[0]*(4-len(order));toxic=3 in order
    result={};messages=[]
    for slot in (first,5-first):
        queue=[x for x in queue if x]+[0]*queue.count(0)
        hp=health if slot==first else 400
        status=0;speed=6;events=[];details=[]
        for hazard in queue[:]:
            if hp==0:break
            if hazard in (1,2):
                damage=400//(8,6,4)[layers-1] if hazard==1 else 50 if slot==poison_slot else 100
                after=max(0,hp-damage)
                events.append((0,slot,hp,after));details.append(('hp',hp-after));hp=after
                messages.append('spikes' if hazard==1 else 'rock')
            elif hazard==3 and toxic:
                if slot==poison_slot:
                    toxic=False;queue[queue.index(3)]=0;details.append(('absorb',0))
                else:status=8;details.append(('status',8))
            elif hazard==4:speed=5;details.append(('speed',5))
        result[slot]={'hp':hp,'status':status,'speed':speed,'events':events,'details':details}
    # Poison residual é separado do dano de entrada e ocorre após as escolhas.
    for slot,data in result.items():
        data['entry_hp']=data['hp']
        if data['hp'] and data['status']:
            after=max(0,data['hp']-50)
            data['details'].append(('hp',data['hp']-after));data['hp']=after
    return result,messages,queue,toxic


@unittest.skipUnless(current.ROM and current.CORE,'defina MOTOR_V17_ROM e MGBA_CORE')
class MotorV17PlayerCombinedHazardsTests(unittest.TestCase):
    _enter_wild_encounter=classmethod(old.MotorV10MGBATests._enter_wild_encounter.__func__)
    _make_doubles_fixture=classmethod(old.MotorV10MGBATests._make_doubles_fixture.__func__)
    setUpClass=classmethod(current.MotorV17CombinedHazardsTests.setUpClass.__func__)
    tearDownClass=classmethod(current.MotorV17CombinedHazardsTests.tearDownClass.__func__)
    moves=ending.MotorV16DoublesEndingsTests.moves
    pulse=ending.MotorV16DoublesEndingsTests.pulse
    settle=ending.MotorV16DoublesEndingsTests.settle
    turn=ending.MotorV16DoublesEndingsTests.turn
    consistent=ending.MotorV16DoublesEndingsTests.consistent
    check_pp=ending.MotorV16DoublesEndingsTests.check_pp
    identities_and_exp=ending.MotorV16DoublesEndingsTests.identities_and_exp

    def scenario(self,order,layers,first,health,actor,caps,poison_slot):
        bench=[400,400];bench[first-2]=health
        st=bytearray(ending.MotorV16DoublesEndingsTests.scenario(self,191,actor,bench))
        self.moves(st,old.PARTY,0,(191,445,681,150),(20,20,20,20),old.bank_off(0))
        self.moves(st,old.PARTY,1,(390,560,150,182),(20,20,20,20),old.bank_off(2))
        self.sequence=[]
        for hazard in order:
            self.sequence.extend({1:[(0,2)]*layers,2:[(1,2)],3:[(3,0)],4:[(3,1)]}[hazard])
        if caps:self.sequence.extend(((0,2),(1,2)))
        self.sequence.append((2,2))  # Court Change leva a fila para o jogador
        self.moves(st,old.ENEMY_PARTY_ADDR,actor//2,(157,150,45,39),
                   (20,len(self.sequence),0,0),old.bank_off(actor))
        # Gate sintético ANTES da execução: Rock Slide começa desabilitado
        # durante os turnos de preparo. Splash é a única ação elegível e tem
        # exatamente esses PP; ao expirar Disable, só Rock Slide tem PP.
        # Não depende da preferência aleatória da IA por um slot.
        gate=old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28*actor
        old.put16(st,gate+4,157)
        st[gate+11]=len(self.sequence)*0x11
        if poison_slot is not None:
            pos=old.offset(old.PARTY)+100*poison_slot
            data=bytearray(st[pos:pos+100]);block,blocks,valid=old.decrypted(data)
            self.assertTrue(valid);block=bytearray(block)
            old.put16(block,blocks[0]*12,1)  # Bulbasaur Grass/Poison aterrado
            old.put16(data,28,sum(old.u16(block,i) for i in range(0,48,2))&0xffff)
            key=old.u32(data,0)^old.u32(data,4)
            for i in range(0,48,4):old.put32(data,32+i,old.u32(block,i)^key)
            st[pos:pos+100]=data
        self.cursors=[0,0]
        self.assertEqual(st[ORDER:ORDER+8],bytes(8))
        return bytes(st)

    def begin(self,st):
        ending.MotorV16DoublesEndingsTests.begin(self,st)
        self.details={2:[],3:[]};self.status_speed={}
        for bank in (0,2):
            b=old.bank_off(bank);pid=old.u32(st,b+0x4C)
            self.status_speed[pid]=(old.u32(st,b+0x50),st[b+0x1B])
        self.previous_toxic=st[TSP]
        self.dead_checks=0

    def advance(self,frames,*buttons):
        for _ in range(frames):
            self.f.run(1,*buttons);st=self.f.state();text=h.text(st)
            if text and (not self.seen or self.seen[-1]!=text):self.seen.append(text)
            for bank,idx in enumerate(doubles.indexes(st)):
                if idx!=self.previous_indexes[bank]:
                    self.transitions.append((bank,self.previous_indexes[bank],idx));self.previous_indexes[bank]=idx
            if st[ending.ABSENT]!=self.last_absent:
                self.absent_changes.append((self.last_absent,st[ending.ABSENT]));self.last_absent=st[ending.ABSENT]
            for side in (0,1):
                for slot in range(6):
                    pid=old.u32(st,old.offset(doubles.party_for(side))+100*slot);key=(side,pid)
                    if key not in self.health:continue
                    before=self.health[key];after=ending.hp(st,side,slot)
                    if after!=before:
                        identity=self.identities[key]
                        self.losses.append((side,identity,before,after));self.health[key]=after
                        if side==0 and identity in self.details:self.details[identity].append(('hp',before-after))
            for bank in (0,2):
                b=old.bank_off(bank);pid=old.u32(st,b+0x4C);slot=self.identities.get((0,pid))
                if slot not in self.details:continue
                status,speed=old.u32(st,b+0x50),st[b+0x1B]
                before=self.status_speed.get(pid,(0,6))
                if old.u16(st,b+0x2A)==0:
                    if getattr(self,'guard_dead_stats',False):
                        # Não esconder Web/status posteriores ao KO ao excluir
                        # a limpeza nativa dos atributos do trace de entrada.
                        self.dead_checks+=1
                        self.assertEqual(status,0)
                        self.assertGreaterEqual(speed,before[1])
                    continue
                if status!=before[0]:self.details[slot].append(('status',status))
                if speed!=before[1]:self.details[slot].append(('speed',speed))
                self.status_speed[pid]=(status,speed)
            if self.previous_toxic and st[TSP]==0:
                bank=st[old.offset(0x0202181F)]&3
                pid=old.u32(st,old.bank_off(bank)+0x4C);slot=self.identities.get((0,pid))
                if slot in self.details:self.details[slot].append(('absorb',0))
            self.previous_toxic=st[TSP]
            if st[ending.OUTCOME] and self.terminal_state is None:
                self.terminal_state=st;self.terminal_losses=list(self.losses)

    def pair(self,st,slots,require_menu=True):
        choices=[]
        for actor,slot in enumerate(slots):
            cursor=self.cursors[actor];directions=[]
            if (cursor&1)!=(slot&1):directions.append('RIGHT' if slot&1 else 'LEFT')
            if (cursor>>1)!=(slot>>1):directions.append('DOWN' if slot>>1 else 'UP')
            choices.append((tuple(directions),None))
        out=self.turn(st,choices,require_menu);self.cursors=list(slots)
        return out

    def field(self,st,queue,layers,toxic,web):
        self.assertEqual(list(st[ORDER:ORDER+4]),queue)
        self.assertEqual(st[ORDER+4:ORDER+8],bytes(4))
        self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+10],layers)
        self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+22],0)
        for offset,pair in ((12,(1,0)),(14,(int(toxic),0)),(16,(int(web),0))):
            self.assertEqual(tuple(st[old.offset(old.V8_STATE_ADDR)+offset:old.offset(old.V8_STATE_ADDR)+offset+2]),pair)

    def plant(self,initial,order,layers,actor):
        st=initial
        for index,slots in enumerate(self.sequence):
            before=st;st=self.pair(st,slots)
            gate=old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28*actor
            remaining=len(self.sequence)-index-1
            self.assertEqual(st[gate+11]&15,remaining)
            self.assertEqual(old.u16(st,gate+4),157 if remaining else 0)
            self.consistent(st);self.check_pp(before,st,[(0,slots[0]),(2,slots[1]),(1,1),(3,1)])
            self.identities_and_exp(initial,st)
            self.assertEqual(self.losses,[]);self.assertEqual(self.transitions,[])
        self.assertEqual(h.party_pp(st,old.ENEMY_PARTY_ADDR,actor//2),[20,0,0,0])
        self.field(st,list(order)+[0]*(4-len(order)),layers,3 in order,4 in order)
        return st

    def choose(self,slot):
        self.pulse('RIGHT')
        if slot==3:self.pulse('DOWN')
        self.pulse('A',35);self.pulse('A',35);self.advance(2000)
        return self.settle(False)

    def reject_current(self,menu,alive):
        from test_motor_v7_mgba import GBA_DECODE
        encode={v:k for k,v in GBA_DECODE.items()}
        message='em batalha!' if alive else 'para batalhar!'
        needle=bytes(encode[c] for c in message)
        transitions=list(self.transitions);losses=list(self.losses)
        self.pulse('A',35);self.pulse('A',35);self.advance(120)
        out=self.f.state()
        self.assertEqual(main_callback2(out),main_callback2(menu))
        self.assertEqual(self.transitions,transitions);self.assertEqual(self.losses,losses)
        self.assertNotIn(needle,menu[old.offset(0x02000000):old.offset(0x02040000)])
        self.assertIn(needle,out[old.offset(0x02000000):old.offset(0x02040000)])
        for side in (0,1):
            p=old.offset(doubles.party_for(side));self.assertEqual(out[p:p+600],menu[p:p+600])
        self.pulse('B',35)

    def verify(self,order,layers=1,first=2,health=400,actor=1,caps=False,poison_slot=None):
        initial=self.scenario(order,layers,first,health,actor,caps,poison_slot)
        before=self.plant(initial,order,layers,actor)
        expected,messages,queue,toxic=oracle(order,layers,first,health,poison_slot)
        menu=self.pair(before,(3,2),False)
        self.assertNotEqual(main_callback2(menu),self.battle_callback)
        self.assertTrue(in_battle(menu));self.assertEqual(self.transitions,[])
        self.assertCountEqual(self.losses,[(0,0,1,0),(0,1,1,0)])
        menu_callback=main_callback2(menu)
        menu=self.choose(first)
        self.assertEqual(main_callback2(menu),menu_callback)
        self.assertEqual(self.transitions,[(0,0,first)])
        self.reject_current(menu,expected[first]['entry_hp']>0)
        out=self.choose(5-first)
        self.assertEqual(main_callback2(out),self.battle_callback)
        self.consistent(out)
        ko=expected[first]['entry_hp']==0
        self.assertEqual(self.transitions,[(0,0,first),(0,first,5-first)] if ko else [(0,0,first),(2,1,5-first)])
        self.assertEqual(out[ending.ABSENT],4 if ko else 0)
        events=[event for event in self.losses if event[0]==0]
        self.assertCountEqual(events[:2],[(0,0,1,0),(0,1,1,0)])
        entry_events=expected[first]['events']+expected[5-first]['events']
        self.assertEqual(events[2:2+len(entry_events)],entry_events)
        residual=[(0,slot,data['entry_hp'],data['hp']) for slot,data in expected.items()
                  if data['entry_hp']!=data['hp']]
        self.assertCountEqual(events[2+len(entry_events):],residual)
        observed=['spikes' if 'sofre\ncom os ESPINHOS!' in text else 'rock' for text in self.seen
                  if 'sofre\ncom os ESPINHOS!' in text or text.startswith('Pedras pontiagudas feriram')]
        self.assertEqual(observed,messages,self.seen)
        for slot,data in expected.items():
            self.assertEqual(self.details[slot],data['details'],(slot,self.seen))
            self.assertEqual(ending.hp(out,0,slot),data['hp'])
            self.assertEqual(old.u32(out,old.offset(old.PARTY)+100*slot+80),data['status'])
        for bank in (0,2):
            if not out[ending.ABSENT]&(1<<bank):
                self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),0)
                self.assertEqual(out[old.bank_off(bank)+0x1B],expected[doubles.indexes(out)[bank]]['speed'])
        self.identities_and_exp(initial,out)
        self.check_pp(before,out,[(actor,0),(actor^2,1)])
        self.field(out,queue,layers,toxic,4 in order)
        if getattr(self,'guard_dead_stats',False):self.assertGreater(self.dead_checks,0)
        # Novos ocupantes executam Protect, não a ação Splash dos mortos.
        before_next=out;absent_history=old.u16(out,h.LAST_MOVES+4)
        out=self.turn(out,[((),None)]*(1 if ko else 2))
        self.consistent(out);self.assertEqual(self.transitions,[])
        self.assertEqual(out[ending.ABSENT],4 if ko else 0)
        uses=[(bank,0) for bank in (0,2) if not out[ending.ABSENT]&(1<<bank)]+[(actor,0),(actor^2,1)]
        self.check_pp(before_next,out,uses);self.identities_and_exp(initial,out)
        poison_losses=[(0,slot,data['hp'],data['hp']-50) for slot,data in expected.items() if data['hp'] and data['status']]
        self.assertCountEqual(self.losses,poison_losses)
        for bank in (0,2):
            self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),absent_history if bank==2 and ko else 182)
        if ko:
            self.assertEqual(out[old.bank_off(2)+0x25:old.bank_off(2)+0x29],before_next[old.bank_off(2)+0x25:old.bank_off(2)+0x29])
        self.field(out,queue,layers,toxic,4 in order)
        return events,observed,expected

    def test_spikes_primeiro_camadas_e_ko_durante_selecao(self):
        for layers in (1,2,3):
            damage=400//(8,6,4)[layers-1]
            for hp in (400,damage,damage+100):
                with self.subTest(layers=layers,hp=hp):self.verify((1,2),layers,health=hp)

    def test_stealth_rock_primeiro_camadas_e_ko_durante_selecao(self):
        for layers in (1,2,3):
            damage=400//(8,6,4)[layers-1]
            for hp in (400,100,damage+100):
                with self.subTest(layers=layers,hp=hp):self.verify((2,1),layers,health=hp)

    def test_limites_ator_3_e_escolha_inversa_dos_reservas(self):
        for order in ((1,2),(2,1)):
            with self.subTest(order=order):self.verify(order,3,first=3,actor=3,caps=True)

    def test_quatro_hazards_absorcao_nos_dois_bancos_e_interrupcao_por_ko(self):
        for order in ((2,3,4,1),(3,1,4,2)):
            for first,health in ((2,400),(3,400),(2,50),(2,100)):
                with self.subTest(order=order,first=first,health=health):
                    self.verify(order,first=first,health=health,actor=3 if first==3 else 1,poison_slot=2)

    def test_ator_3_nao_aplica_web_ou_status_ao_entrante_desmaiado(self):
        self.guard_dead_stats=True
        try:
            for order in ((2,3,4,1),(3,1,4,2)):
                with self.subTest(order=order):
                    self.verify(order,health=50,actor=3,poison_slot=2)
        finally:self.guard_dead_stats=False
