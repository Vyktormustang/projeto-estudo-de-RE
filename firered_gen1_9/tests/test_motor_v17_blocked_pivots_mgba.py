"""Pivôs bloqueados/sem reserva e duas caracterizações NEGATIVAS da v17.

Os métodos test_defeito_* provam divergências, NÃO conformidade moderna.
Só a fixture inicial é escrita; preparo, ações e seleção usam a UI real.
"""
import test_motor_v17_switch_pivot_hazards_mgba as previous
from battle_fixture_helpers import main_callback2

old,h,ending,doubles=previous.old,previous.h,previous.ending,previous.doubles
RESULT=old.offset(0x02021608)


def signature(st,bank):
    b=old.bank_off(bank)
    return (doubles.indexes(st)[bank],bytes(st[b:b+12]),bytes(st[b+0x19:b+0x25]),
            old.u16(st,b+0x2A),old.u16(st,b+0x2E),bytes(st[b+0x48:b+0x58]))


class MotorV17BlockedPivotsTests(previous.MotorV17SwitchPivotHazardsTests):
    test_troca_voluntaria_nos_dois_bancos_ordens_e_ko=None
    test_quatro_pivos_sobrevivem_preservando_aliado=None
    test_quatro_pivos_ko_do_entrante_e_segunda_selecao=None
    test_quatro_hazards_absorcao_status_e_ko=None

    def setup_case(self,move,actor,mode,order):
        self.stay_watch=None
        st=bytearray(super().scenario(move,actor,order,400,actor==0,False))
        b=old.bank_off(1)
        if mode in ('ground','ground_no_bench'):
            st[b+0x22]=st[b+0x23]=4  # tipo Ground sintético do alvo ativo
        abilities={'volt_absorb':10,'water_absorb':11,'clear_body':29,'soundproof':43}
        if mode in abilities:st[b+0x20]=abilities[mode]
        if mode in ('min_stats','min_attack'):st[b+0x19]=0
        if mode in ('min_stats','min_special'):st[b+0x1C]=0
        if mode in ('no_bench','ground_no_bench'):
            for slot in (2,3):old.put16(st,old.offset(old.PARTY)+100*slot+86,0)
            self.assertEqual(doubles.eligible(st,0),set())  # aliado/ovo/vazio não são reservas
        if mode=='protect':
            count=len(order)+1
            self.moves(st,old.ENEMY_PARTY_ADDR,0,(182,150,45,39),(20,count,0,0),b)
            gate=old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28
            old.put16(st,gate+4,182);st[gate+11]=count*0x11
        initial=bytes(st);before=self.plant(initial,order)
        if mode=='protect':
            gate=old.offset(old.DISABLE_STRUCTS_REAL_ADDR)+28
            self.assertEqual(old.u16(before,gate+4),0)
            self.assertEqual(before[gate+11]&15,0)
            self.assertEqual(h.party_pp(before,old.ENEMY_PARTY_ADDR,0),[20,0,0,0])
        return initial,before

    def watch_actor(self,st,destination):
        self.stay_watch=signature(st,self.actor)
        self.allowed_history=(old.u16(st,h.LAST_MOVES+2*self.actor),destination)
        self.reached_history=False;self.actor_frames=0

    def advance(self,frames,*buttons):
        if not getattr(self,'stay_watch',None):return super().advance(frames,*buttons)
        for _ in range(frames):
            super().advance(1,*buttons);st=self.f.state()
            self.assertEqual(signature(st,self.actor),self.stay_watch)
            last=old.u16(st,h.LAST_MOVES+2*self.actor)
            self.assertIn(last,self.allowed_history)
            if self.reached_history:self.assertEqual(last,self.allowed_history[1])
            if last==self.allowed_history[1]:self.reached_history=True
            self.actor_frames+=1

    def attempt(self,before):
        self.ally_watch=self.ally_signature(before);self.ally_acted=False
        self.watch_actor(before,self.move);self.begin(before)
        for bank in (0,2):self.fight(bank,0 if bank==self.actor else 3,1 if bank==self.actor else None)
        self.advance(1500)
        return self.settle(False)

    def stable_field(self,st,order):
        self.field(st,list(order)+[0]*(4-len(order)),1,3 in order,4 in order)
        self.assertEqual(st[ending.ABSENT],0)
        self.assertEqual(self.absent_changes,[])

    def stages(self,st,mode):
        expected={'min_stats':(0,0),'min_attack':(0,5),'min_special':(5,0),
                  'soundproof':(5,5),'no_bench':(5,5)}.get(mode,(6,6))
        if self.move!=571:expected=(6,6)
        self.assertEqual(tuple(st[old.bank_off(1)+i] for i in (0x19,0x1C)),expected)

    def followup(self,initial,st,order,actor_slot,poison=False,protect=False):
        self.cursors[self.actor//2]=0 if actor_slot==0 else self.cursors[self.actor//2]
        self.watch_actor(st,150)
        # No caso de veneno o HP do entrante deve cair; observar apenas o
        # aliado nesse turno, sem fingir que o residual é um novo hazard.
        if poison:self.stay_watch=None
        hp=ending.hp(st,0,doubles.indexes(st)[self.actor])
        before=st;out=self.pair(st,self.slots(actor_slot,3))
        self.consistent(out);self.assertEqual(self.transitions,[])
        self.assertEqual(self.losses,[(0,2,hp,hp-50)] if poison else [])
        self.check_pp(before,out,[(self.actor,actor_slot),(self.ally,3),(1,0 if protect else 1),(3,1)])
        self.identities_and_exp(initial,out);self.stable_field(out,order)
        for bank in (0,2,3):self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),150)
        self.assertEqual(old.u16(out,h.LAST_MOVES+2),182 if protect else 150)
        return out

    def verify_stays(self,move,actor,mode):
        order=(2,1) if actor==0 else (1,2)
        initial,before=self.setup_case(move,actor,mode,order)
        out=self.attempt(before)
        self.assertEqual(main_callback2(out),self.battle_callback,self.seen)
        self.assertIn('vai fazer?',h.text(out),self.seen)
        self.assertGreater(self.actor_frames,0);self.assertTrue(self.reached_history)
        self.consistent(out);self.assertEqual(doubles.indexes(out),doubles.indexes(before))
        self.assertEqual(self.transitions,[]);self.stable_field(out,order)
        damage=mode=='no_bench' and move!=571
        if damage:
            self.assertEqual(len(self.losses),1);side,slot,start,end=self.losses[0]
            self.assertEqual((side,slot,start),(1,0,4000));self.assertTrue(0<end<start)
        else:self.assertEqual(self.losses,[])
        self.assertEqual(self.details,{2:[],3:[]})
        self.stages(out,mode)
        if mode=='protect':self.assertTrue(any('se protegeu!' in s for s in self.seen),self.seen)
        for mode_name,word in (('volt_absorb','VOLT ABSORB'),('water_absorb','WATER ABSORB'),('clear_body','CLEAR BODY')):
            if mode==mode_name:self.assertTrue(any(word in s for s in self.seen),self.seen)
        if mode=='ground_no_bench':self.assertTrue(any('afeta' in s for s in self.seen),self.seen)
        self.check_pp(before,out,[(actor,0),(self.ally,3),(1,0 if mode=='protect' else 1),(3,1)])
        self.identities_and_exp(initial,out)
        for bank in (0,2):
            self.assertEqual(ending.hp(out,0,bank//2),4000)
            self.assertEqual(old.u16(out,h.LAST_MOVES+2*bank),move if bank==actor else 150)
        self.assertEqual(out[old.bank_off(actor)+0x19],8)
        self.followup(initial,out,order,1,protect=mode=='protect')

    def verify_switch(self,move,actor,mode,four=False):
        # Ground/Soundproof: EXPECTATIVA MODERNA = não trocar. Aqui exige-se
        # deliberadamente a divergência observada, para caracterizar a base.
        # min_attack/min_special são controles positivos: um atributo cai.
        order=((2,3,4,1) if actor==0 else (3,1,4,2)) if four else ((2,1) if actor==0 else (1,2))
        initial,before=self.setup_case(move,actor,mode,order)
        menu=self.attempt(before)
        self.assertNotEqual(main_callback2(menu),self.battle_callback,self.seen)
        self.assertEqual(self.transitions,[]);self.assertEqual(self.losses,[])
        self.assertGreater(self.actor_frames,0);self.assertTrue(self.reached_history)
        self.assertEqual(old.u16(menu,h.LAST_MOVES+2*actor),move)
        self.assertEqual(old.u16(menu,h.LAST_MOVES+2*self.ally),681 if actor==0 else 150)
        if mode=='ground':
            self.assertTrue(any('afeta' in s for s in self.seen),self.seen)
            self.assertEqual(menu[RESULT]&8,8)  # imunidade reconhecida antes da seleção indevida
        self.stages(menu,mode)
        if mode=='soundproof':self.assertEqual(menu[old.bank_off(1)+0x20],43)
        self.stay_watch=None;self.select_bench(2);out=self.settle(False)
        self.assertEqual(main_callback2(out),self.battle_callback,self.seen)
        self.consistent(out);self.assertEqual(self.transitions,[(actor,actor//2,2)])
        expected=previous.entry_oracle(order,400,False,four)
        losses=[(0,2,a,b) for a,b in expected['losses']]
        if four:
            losses.append((0,2,250,200));expected['details'].append(('hp',50))
        self.assertEqual(self.losses,losses)
        self.assertEqual(self.details,{2:expected['details'],3:[]})
        observed=['spikes' if 'sofre\ncom os ESPINHOS!' in text else 'rock' for text in self.seen
                  if 'sofre\ncom os ESPINHOS!' in text or text.startswith('Pedras pontiagudas feriram')]
        self.assertEqual(observed,expected['messages'])
        self.assertEqual(ending.hp(out,0,2),200 if four else 250)
        self.assertEqual(old.u16(out,h.LAST_MOVES+2*actor),0)
        self.assertEqual(out[old.bank_off(actor)+0x19],6)
        self.assertEqual(out[old.bank_off(actor)+0x1B],5 if four else 6)
        self.assertEqual(old.u32(out,old.bank_off(actor)+0x50),8 if four else 0)
        self.assertEqual(old.u16(out,h.LAST_MOVES+2*self.ally),150)
        self.check_pp(before,out,[(actor,0),(self.ally,3),(1,1),(3,1)])
        self.identities_and_exp(initial,out);self.stable_field(out,order)
        self.stages(out,mode)
        self.followup(initial,out,order,0,poison=four)

    def test_protect_bloqueia_os_quatro_pivos_nos_dois_bancos(self):
        for move in previous.PIVOTS:
            for actor in (0,2):
                with self.subTest(move=move,actor=actor):self.verify_stays(move,actor,'protect')

    def test_absorcao_eletrica_e_agua_impede_troca(self):
        for move,mode in ((517,'volt_absorb'),(708,'water_absorb')):
            for actor in (0,2):
                with self.subTest(mode=mode,actor=actor):self.verify_stays(move,actor,mode)

    def test_parting_clear_body_e_dois_atributos_minimos(self):
        for mode in ('clear_body','min_stats'):
            for actor in (0,2):
                with self.subTest(mode=mode,actor=actor):self.verify_stays(571,actor,mode)

    def test_quatro_pivos_sem_reservas_elegiveis(self):
        for move in previous.PIVOTS:
            for actor in (0,2):
                with self.subTest(move=move,actor=actor):self.verify_stays(move,actor,'no_bench')

    def test_ground_sem_reserva_nao_abre_selecao(self):
        for actor in (0,2):
            with self.subTest(actor=actor):self.verify_stays(517,actor,'ground_no_bench')

    def test_parting_um_atributo_minimo_ainda_permite_troca(self):
        for mode in ('min_attack','min_special'):
            for actor in (0,2):
                with self.subTest(mode=mode,actor=actor):self.verify_switch(571,actor,mode)

    def test_defeito_v17_volt_switch_ground_troca_apesar_da_imunidade(self):
        for actor,four in ((0,False),(2,False),(0,True)):
            with self.subTest(actor=actor,four=four):self.verify_switch(517,actor,'ground',four)

    def test_defeito_v17_parting_ignora_soundproof(self):
        for actor,four in ((0,False),(2,False),(2,True)):
            with self.subTest(actor=actor,four=four):self.verify_switch(571,actor,'soundproof',four)
