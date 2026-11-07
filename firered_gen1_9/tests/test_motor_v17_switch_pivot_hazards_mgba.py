"""Trocas voluntárias e pivôs com aliado ativo sob hazards combinados v17."""
import test_motor_v17_player_combined_hazards_mgba as previous
from battle_fixture_helpers import main_callback2

old,h,ending,doubles=previous.old,previous.h,previous.ending,previous.doubles
ORDER=previous.ORDER
PIVOTS=(369,517,708,571)  # U-turn, Volt Switch, Flip Turn, Parting Shot (IDs locais)


def entry_oracle(order,health,poison=False,toxic=True):
    hp=health;status=0;speed=6;details=[];losses=[];messages=[];queue=list(order)
    for hazard in order:
        if hp==0:break
        if hazard in (1,2):
            damage=50 if hazard==1 or poison else 100
            after=max(0,hp-damage);losses.append((hp,after));details.append(('hp',hp-after));hp=after
            messages.append('spikes' if hazard==1 else 'rock')
        elif hazard==3 and toxic:
            if poison:toxic=False;queue[queue.index(3)]=0;details.append(('absorb',0))
            else:status=8;details.append(('status',8))
        elif hazard==4:speed=5;details.append(('speed',5))
    return dict(hp=hp,status=status,speed=speed,details=details,losses=losses,messages=messages,queue=queue,toxic=toxic)


class MotorV17SwitchPivotHazardsTests(previous.MotorV17PlayerCombinedHazardsTests):
    test_spikes_primeiro_camadas_e_ko_durante_selecao=None
    test_stealth_rock_primeiro_camadas_e_ko_durante_selecao=None
    test_limites_ator_3_e_escolha_inversa_dos_reservas=None
    test_quatro_hazards_absorcao_nos_dois_bancos_e_interrupcao_por_ko=None
    test_ator_3_nao_aplica_web_ou_status_ao_entrante_desmaiado=None

    def scenario(self,move,actor,order,health,fast,poison):
        st=bytearray(doubles.MotorV16DoublesPhazingTests.scenario(self,-1,150,'mixed'))
        self.actor=actor;self.ally=actor^2;self.move=move;self.fast=fast
        self.ally_watch=None
        actor_moves=(move or 33,150,390,560);ally_moves=(191,445,681,150)
        for bank,moves in ((actor,actor_moves),(self.ally,ally_moves)):
            self.moves(st,old.PARTY,bank//2,moves,(20,20,20,20),old.bank_off(bank))
            speed=(600 if fast else 40) if bank==actor else 200
            old.put16(st,old.bank_off(bank)+6,speed)
            old.put16(st,old.offset(old.PARTY)+100*(bank//2)+94,speed)
        st[old.bank_off(actor)+0x19]=8  # não pode ser herdado como Baton Pass
        for bank in (1,3):
            self.moves(st,old.ENEMY_PARTY_ADDR,bank//2,(33,150,45,39),(0,40,0,0),old.bank_off(bank))
        for slot,hp in ((2,health),(3,400)):
            pos=old.offset(old.PARTY)+100*slot
            old.put16(st,pos+86,hp);old.put16(st,pos+88,400)
            self.moves(st,old.PARTY,slot,(150,move or 33,45,39),(13+slot,12+slot,11+slot,10+slot))
        if poison:
            pos=old.offset(old.PARTY)+200
            data=bytearray(st[pos:pos+100]);block,blocks,valid=old.decrypted(data)
            self.assertTrue(valid);block=bytearray(block);old.put16(block,blocks[0]*12,1)
            old.put16(data,28,sum(old.u16(block,i) for i in range(0,48,2))&0xffff)
            key=old.u32(data,0)^old.u32(data,4)
            for i in range(0,48,4):old.put32(data,32+i,old.u32(block,i)^key)
            st[pos:pos+100]=data
        self.cursors=[0,0];self.guard_dead_stats=True
        self.assertEqual(doubles.indexes(st),(0,0,1,1))
        self.assertEqual(doubles.eligible(st,0),{2,3})
        return bytes(st)

    def ally_signature(self,st):
        b=old.bank_off(self.ally)
        return (doubles.indexes(st)[self.ally],bytes(st[b:b+12]),
                bytes(st[b+0x19:b+0x25]),old.u16(st,b+0x2A),
                old.u16(st,b+0x2E),bytes(st[b+0x48:b+0x58]))

    def advance(self,frames,*buttons):
        if not getattr(self,'ally_watch',None):
            return super().advance(frames,*buttons)
        for _ in range(frames):
            super().advance(1,*buttons)
            st=self.f.state()
            self.assertEqual(self.ally_signature(st),self.ally_watch)
            last=old.u16(st,h.LAST_MOVES+2*self.ally)
            self.assertIn(last,(681,150))
            if self.ally_acted:self.assertEqual(last,150)
            if last==150:self.ally_acted=True

    def slots(self,actor_slot,ally_slot):
        return (actor_slot,ally_slot) if self.actor==0 else (ally_slot,actor_slot)

    def plant(self,initial,order):
        st=initial
        for hazard in (*order,0):
            a,b={1:(1,0),2:(1,1),3:(2,3),4:(3,3),0:(1,2)}[hazard]
            slots=self.slots(a,b);before=st;st=self.pair(st,slots)
            self.consistent(st);self.check_pp(before,st,[(0,slots[0]),(2,slots[1]),(1,1),(3,1)])
            self.identities_and_exp(initial,st)
            self.assertEqual(self.losses,[]);self.assertEqual(self.transitions,[])
        self.field(st,list(order)+[0]*(4-len(order)),1,3 in order,4 in order)
        self.assertEqual(old.u16(st,h.LAST_MOVES+2*self.actor),150)
        self.assertEqual(old.u16(st,h.LAST_MOVES+2*self.ally),681)
        return st

    def fight(self,bank,slot,target=None):
        cursor=self.cursors[bank//2]
        self.pulse('A')
        if (cursor&1)!=(slot&1):self.pulse('RIGHT' if slot&1 else 'LEFT',15)
        if (cursor>>1)!=(slot>>1):self.pulse('DOWN' if slot>>1 else 'UP',15)
        self.pulse('A')
        if target is not None:
            if target==3:self.pulse('LEFT',15)
            self.pulse('A')
        self.cursors[bank//2]=slot

    def reject_ally(self):
        if self.actor==0:self.pulse('DOWN')
        menu=self.f.state();self.reject_current(menu,True)
        if self.actor==0:self.pulse('UP')

    def select_bench(self,slot,frames=2000):
        self.pulse('RIGHT')
        if slot==3:self.pulse('DOWN')
        self.pulse('A',35);self.pulse('A',35);self.advance(frames)

    def switch_turn(self,st):
        self.ally_watch=self.ally_signature(st);self.ally_acted=False
        self.begin(st)
        if not self.move:
            for bank in (0,2):
                if bank==self.actor:
                    self.pulse('DOWN');self.pulse('A',80)
                    self.assertNotEqual(main_callback2(self.f.state()),self.battle_callback)
                    self.reject_ally();self.select_bench(2,120)
                else:self.fight(bank,3)
            self.advance(1500)
        else:
            for bank in (0,2):self.fight(bank,0 if bank==self.actor else 3,1 if bank==self.actor else None)
            self.advance(1500)
            menu=self.settle(False)
            self.assertNotEqual(main_callback2(menu),self.battle_callback,self.seen)
            self.assertEqual(self.transitions,[])
            self.assertEqual(old.u16(menu,h.LAST_MOVES+2*self.ally),681 if self.fast else 150)
            pp=h.party_pp(st,old.PARTY,self.ally//2)
            if not self.fast:pp[3]-=1
            self.assertEqual(list(menu[old.bank_off(self.ally)+0x25:old.bank_off(self.ally)+0x29]),pp)
            self.reject_ally();self.select_bench(2)
        out=self.settle(False)
        return out

    def verify(self,move,actor,order,health=400,fast=True,poison=False):
        initial=self.scenario(move,actor,order,health,fast,poison)
        before=self.plant(initial,order)
        expected={2:entry_oracle(order,health,poison,3 in order)}
        out=self.switch_turn(before)
        ko=expected[2]['hp']==0
        if ko:
            self.assertNotEqual(main_callback2(out),self.battle_callback,self.seen)
            self.assertEqual(self.transitions,[(actor,actor//2,2)])
            self.select_bench(3)
            out=self.settle(False)
            next_order=[x for x in expected[2]['queue'] if x]
            expected[3]=entry_oracle(next_order,400,False,expected[2]['toxic'])
        self.assertEqual(main_callback2(out),self.battle_callback,self.seen)
        if ko:self.assertGreater(self.dead_checks,0)
        self.consistent(out)
        self.assertEqual(self.transitions,[(actor,actor//2,2)]+([(actor,2,3)] if ko else []))
        indexes=[0,0,1,1];indexes[actor]=3 if ko else 2
        self.assertEqual(doubles.indexes(out),tuple(indexes));self.assertEqual(out[ending.ABSENT],0)
        expected_losses=[];messages=[]
        for slot,data in expected.items():
            expected_losses.extend((0,slot,a,b) for a,b in data['losses'])
            messages.extend(data['messages'])
            if data['hp'] and data['status']:
                after=data['hp']-50
                expected_losses.append((0,slot,data['hp'],after))
                data['details'].append(('hp',50));data['hp']=after
            self.assertEqual(self.details[slot],data['details'],(slot,self.seen))
            self.assertEqual(ending.hp(out,0,slot),data['hp'])
            self.assertEqual(old.u32(out,old.offset(old.PARTY)+100*slot+80),data['status'])
        self.assertEqual([x for x in self.losses if x[0]==0],expected_losses)
        observed=['spikes' if 'sofre\ncom os ESPINHOS!' in text else 'rock' for text in self.seen
                  if 'sofre\ncom os ESPINHOS!' in text or text.startswith('Pedras pontiagudas feriram')]
        self.assertEqual(observed,messages,self.seen)
        foe_losses=[x for x in self.losses if x[0]==1]
        if move and move!=571:
            self.assertEqual(len(foe_losses),1);self.assertEqual(foe_losses[0][:3],(1,0,4000))
            self.assertGreater(foe_losses[0][3],0);self.assertLess(foe_losses[0][3],4000)
        else:self.assertEqual(foe_losses,[])
        for off in (0x19,0x1C):self.assertEqual(out[old.bank_off(1)+off],5 if move==571 else 6)
        final_slot=3 if ko else 2;data=expected[final_slot]
        self.assertEqual(out[old.bank_off(actor)+0x19],6)
        self.assertEqual(out[old.bank_off(actor)+0x1B],data['speed'])
        self.assertEqual(ending.hp(out,0,actor//2),4000)  # o retirado permanece vivo
        self.assertEqual(ending.hp(out,0,self.ally//2),4000)
        self.assertEqual(old.u16(out,h.LAST_MOVES+2*actor),0)
        self.assertEqual(old.u16(out,h.LAST_MOVES+2*self.ally),150)
        uses=[(self.ally,3),(1,1),(3,1)]+([(actor,0)] if move else [])
        self.check_pp(before,out,uses);self.identities_and_exp(initial,out)
        queue=data['queue']+[0]*(4-len(data['queue']))
        self.field(out,queue,1,data['toxic'],4 in order)
        # Mais um turno: Splash próprio do entrante, aliado inalterado e
        # somente poison residual quando aplicável, sem reaplicar hazards.
        before_next=out;self.cursors[actor//2]=0
        out=self.pair(out,self.slots(0,3))
        self.consistent(out);self.assertEqual(self.transitions,[])
        self.assertEqual(self.losses,[(0,final_slot,data['hp'],data['hp']-50)] if data['status'] else [])
        self.check_pp(before_next,out,[(actor,0),(self.ally,3),(1,1),(3,1)])
        self.identities_and_exp(initial,out)
        for bank in (0,1,2,3):self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),150)
        self.assertEqual(ending.hp(out,0,self.ally//2),4000)
        self.field(out,queue,1,data['toxic'],4 in order)
        return expected_losses,observed

    def test_troca_voluntaria_nos_dois_bancos_ordens_e_ko(self):
        for actor in (0,2):
            for order in ((1,2),(2,1)):
                for health in (400,50 if order[0]==1 else 100,150):
                    with self.subTest(actor=actor,order=order,health=health):self.verify(0,actor,order,health)

    def test_quatro_pivos_sobrevivem_preservando_aliado(self):
        for move in PIVOTS:
            for actor in (0,2):
                with self.subTest(move=move,actor=actor):
                    self.verify(move,actor,(2,1) if actor==0 else (1,2),fast=actor==0)

    def test_quatro_pivos_ko_do_entrante_e_segunda_selecao(self):
        for move in PIVOTS:
            for actor in (0,2):
                with self.subTest(move=move,actor=actor):
                    self.verify(move,actor,(2,1) if actor==0 else (1,2),100 if actor==0 else 50,fast=actor==0)

    def test_quatro_hazards_absorcao_status_e_ko(self):
        cases=((0,0,(2,3,4,1),400,True),(0,2,(3,1,4,2),50,True),
               (369,0,(2,3,4,1),50,True),(571,2,(3,1,4,2),400,False))
        for move,actor,order,health,poison in cases:
            with self.subTest(move=move,actor=actor,health=health):
                self.verify(move,actor,order,health,actor==0,poison)
