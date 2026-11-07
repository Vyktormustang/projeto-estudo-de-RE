"""Ciclo de vida da fila v17, por golpes reais e apenas preparo sintético."""
import test_motor_v17_combined_hazards_mgba as c

old,h,doubles=c.old,c.h,c.doubles
ORDER=old.offset(0x0203FC90)

class MotorV17LifecycleTests(c.MotorV17CombinedHazardsTests):
    test_spikes_primeiro_camadas_e_ko_no_primeiro_ou_segundo_hazard=None
    test_stealth_rock_primeiro_camadas_e_ko=None
    test_quarta_camada_e_sr_repetido_nao_aumentam_dano=None
    test_ordem_inversa_persiste_apos_tentativas_repetidas=None

    def setup_moves(self,first,second,*,durable=False,bench_hp=400,species=None):
        st=bytearray(self.scenario(bench_hp))
        for bank,moves in ((0,first),(2,second)):
            self.moves(st,old.PARTY,bank//2,moves,(20,20,20,20),old.bank_off(bank))
            if durable:
                for bo,po in ((2,90),(8,96)):
                    old.put16(st,old.bank_off(bank)+bo,1)
                    old.put16(st,old.offset(old.PARTY)+100*(bank//2)+po,1)
        if durable:
            for bank in (1,3):
                for off in (0x2A,0x2E):old.put16(st,old.bank_off(bank)+off,4000)
                for off in (86,88):old.put16(st,old.offset(old.ENEMY_PARTY_ADDR)+100*(bank//2)+off,4000)
        if species is not None:
            pos=old.offset(old.ENEMY_PARTY_ADDR)+200
            data=bytearray(st[pos:pos+100]);block,order,valid=old.decrypted(data)
            self.assertTrue(valid);block=bytearray(block);old.put16(block,order[0]*12,species)
            old.put16(data,28,sum(old.u16(block,i) for i in range(0,48,2))&0xffff)
            key=old.u32(data,0)^old.u32(data,4)
            for i in range(0,48,4):old.put32(data,32+i,old.u32(block,i)^key)
            st[pos:pos+100]=data
        self.cursors=[0,0]
        return bytes(st)

    def pair(self,st,slots,*,damaging=False,targeted=False,primary_target=False):
        choices=[]
        for actor,slot in enumerate(slots):
            cursor=self.cursors[actor];directions=[]
            if (cursor&1)!=(slot&1):directions.append('RIGHT' if slot&1 else 'LEFT')
            if (cursor>>1)!=(slot>>1):directions.append('DOWN' if slot>>1 else 'UP')
            choices.append((tuple(directions),1 if (targeted and actor==1) or (primary_target and actor==0) else None))
        out=self.turn(st,choices);self.cursors=list(slots)
        self.consistent(out)
        if not damaging:
            self.check_pp(st,out,[(0,slots[0]),(2,slots[1]),(1,1),(3,1)])
            self.identities_and_exp(st,out)
            self.assertEqual(self.transitions,[])
        return out

    def identities_and_exp(self,initial,out,exp_gain=0):
        # Os dois participantes começam em EXP 560; a curva Medium Slow
        # alcança nível 11 em 742. Ekans dá 66 por participante, não os 69
        # do Charmander: 138+66=204 ainda cruza esse limiar.
        for side in (0,1):
            for slot in range(6):
                pos=old.offset(doubles.party_for(side))+100*slot
                self.assertEqual(out[pos:pos+8],initial[pos:pos+8])
                gain=exp_gain if side==0 and slot<2 else 0
                before=c.ending.previous.experience(initial,side,slot)
                self.assertEqual(c.ending.previous.experience(out,side,slot),before+gain)
                self.assertEqual(out[pos+84],11 if gain and before+gain>=742 else initial[pos+84])
                h.party_pp(out,doubles.party_for(side),slot)

    def queue(self,st,side):return list(st[ORDER+4*side:ORDER+4*side+4])

    def test_nova_batalha_limpa_fila_sem_tocar_guardas(self):
        st=bytearray(old.seed_mon(self.fixture,1,10,(150,45,33,39)))
        st[ORDER:ORDER+8]=bytes([4,3,2,1,2,4,1,3])
        st[ORDER-4:ORDER]=b'GARD';st[ORDER+8:ORDER+16]=b'AFTER123'
        out=self._enter_wild_encounter(st)
        self.assertEqual(out[ORDER:ORDER+8],bytes(8))
        self.assertEqual(out[ORDER-4:ORDER],b'GARD')
        self.assertEqual(out[ORDER+8:ORDER+16],b'AFTER123')

    def test_court_change_camadas_intercaladas_limpeza_e_recriacao(self):
        for cleaner in (432,772):
            with self.subTest(cleaner=cleaner):
                st=self.setup_moves((445,191,681,150),(cleaner,150,150,150))
                st=self.pair(st,(1,1));st=self.pair(st,(0,1))
                st=self.pair(st,(1,1));st=self.pair(st,(1,1))
                self.assertEqual(self.queue(st,1),[1,2,0,0])
                self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+22],3)
                for sides in (([1,2,0,0],[0,0,0,0]),([0,0,0,0],[1,2,0,0])):
                    st=self.pair(st,(2,1))
                    self.assertEqual((self.queue(st,0),self.queue(st,1)),sides)
                st=self.pair(st,(3,0),targeted=cleaner==432)
                self.assertEqual(st[ORDER:ORDER+8],bytes(8))
                self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+22],0)
                self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+13],0)
                st=self.pair(st,(0,1));st=self.pair(st,(1,1))
                self.assertEqual(self.queue(st,1),[2,1,0,0])

    def test_rapid_e_mortal_spin_limpam_so_proprio_lado(self):
        for cleaner in (229,758):
            with self.subTest(cleaner=cleaner):
                st=self.setup_moves((445,191,681,150),(cleaner,150,150,150),durable=True)
                st=self.pair(st,(0,1));st=self.pair(st,(1,1));st=self.pair(st,(2,1))
                st=self.pair(st,(1,1));st=self.pair(st,(0,1))
                self.assertEqual((self.queue(st,0),self.queue(st,1)),([2,1,0,0],[1,2,0,0]))
                st=self.pair(st,(3,0),targeted=cleaner==229)
                self.assertEqual((self.queue(st,0),self.queue(st,1)),([0,0,0,0],[1,2,0,0]))
                self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+10],0)
                self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+12],0)
                st=self.pair(st,(2,1));st=self.pair(st,(0,1));st=self.pair(st,(1,1))
                self.assertEqual((self.queue(st,0),self.queue(st,1)),([1,2,0,0],[2,1,0,0]))

    def test_stone_axe_ceaseless_edge_ordem_e_limites(self):
        for reverse in (False,True):
            with self.subTest(reverse=reverse):
                st=self.setup_moves((723,738,150,150),(150,150,150,150),durable=True)
                sequence=([0,1] if reverse else [1,0])+[1,1,1,0]
                expected=[2,1,0,0] if reverse else [1,2,0,0]
                for idx,slot in enumerate(sequence):
                    # A precisão continua real. Uma falha não deve criar hazard;
                    # permitir tentativas limitadas até observar o acerto necessário.
                    for attempt in range(6):
                        before=st;st=self.pair(st,(slot,0),damaging=False,primary_target=True)
                        succeeded=(st[old.offset(old.V8_STATE_ADDR)+13] if slot==0 else
                                   st[old.offset(old.SIDE_TIMERS_ADDR)+22] > before[old.offset(old.SIDE_TIMERS_ADDR)+22])
                        if succeeded:break
                        if idx>=4:break  # tentativas além do limite não podem aumentar a fila
                    if idx>=1:self.assertEqual(self.queue(st,1),expected)
                self.assertEqual(st[old.offset(old.SIDE_TIMERS_ADDR)+22],3)
                self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+13],1)

    def begin(self,st):
        super().begin(st)
        self.detail={};self.status_speed={}
        for slot in (2,3):
            pos=old.offset(old.ENEMY_PARTY_ADDR)+100*slot
            pid=old.u32(st,pos)
            self.detail[pid]=[];self.status_speed[pid]=(0,6)

    def advance(self,frames,*buttons):
        for _ in range(frames):
            n=len(self.losses);super().advance(1,*buttons);st=self.f.state()
            for side,slot,before,after in self.losses[n:]:
                if side==1 and slot in (2,3):
                    pid=old.u32(st,old.offset(old.ENEMY_PARTY_ADDR)+100*slot)
                    self.detail[pid].append(('hp',before-after))
            for bank in (1,3):
                b=old.bank_off(bank);pid=old.u32(st,b+0x4C)
                if pid not in self.status_speed:continue
                status,speed=old.u32(st,b+0x50),st[b+0x1B]
                previous=self.status_speed[pid]
                if status!=previous[0]:self.detail[pid].append(('status',status))
                if speed!=previous[1]:self.detail[pid].append(('speed',speed))
                self.status_speed[pid]=(status,speed)

    def test_quatro_hazards_ordenados_absorcao_e_ko_antes_de_habilidade(self):
        # Espécie 23: Ekans/Intimidate; Poison absorve Toxic Spikes. Ao morrer
        # em SR, não deve absorver os espinhos nem executar Intimidate/Web.
        cases=((False,400,None),(True,400,None),(False,400,23),(False,50,23))
        for reverse,health,species in cases:
            with self.subTest(reverse=reverse,health=health,species=species):
                st=self.setup_moves((445,191,157,150),(390,560,150,150),bench_hp=health,species=species)
                sequence=((3,0),(1,2),(3,1),(0,2)) if reverse else ((0,2),(3,0),(3,1),(1,2))
                order=[3,1,4,2] if reverse else [2,3,4,1]
                for pair in sequence:st=self.pair(st,pair)
                self.assertEqual(self.queue(st,1),order)
                before=st;st=self.pair(st,(2,2),damaging=True)
                pid=old.u32(st,old.offset(old.ENEMY_PARTY_ADDR)+200)
                if health==50:
                    self.assertEqual(self.detail[pid],[('hp',50)])
                    self.assertEqual(self.queue(st,1),order)
                    for bank in (0,2):self.assertEqual(st[old.bank_off(bank)+0x19],6)
                else:
                    expected={1:('hp',50),2:('hp',50 if species==23 else 100),
                              3:('status',8),4:('speed',5)}
                    labels=[expected[x] for x in order if not(species==23 and x==3)]
                    self.assertEqual(self.detail[pid][:len(labels)],labels,self.seen)
                    if species==23:
                        self.assertEqual(self.queue(st,1),[2,4,1,0])
                        self.assertEqual(st[old.offset(old.V8_STATE_ADDR)+15],0)
                        for bank in (0,2):self.assertEqual(st[old.bank_off(bank)+0x19],5)
                self.check_pp(before,st,[(0,2),(2,2)])
                self.identities_and_exp(before,st,204 if health==50 else 138)

    def test_recriacao_apos_limpeza_muda_dano_real_na_entrada(self):
        for cleaner in (432,772):
            with self.subTest(cleaner=cleaner):
                st=self.setup_moves((445,191,150,157),(cleaner,150,150,150))
                st=self.pair(st,(1,1));st=self.pair(st,(0,1))
                self.assertEqual(self.queue(st,1),[1,2,0,0])
                st=self.pair(st,(2,0),targeted=cleaner==432)
                self.assertEqual(st[ORDER:ORDER+8],bytes(8))
                st=self.pair(st,(0,1));st=self.pair(st,(1,1))
                self.assertEqual(self.queue(st,1),[2,1,0,0])
                before=st;st=self.pair(st,(3,1),damaging=True)
                expected=c.entry_events(2,400,1,True)+c.entry_events(3,400,1,True)
                self.assertEqual([x for x in self.losses if x[0]==1][2:],expected)
                self.assertEqual(self.hazard_messages(),['rock','spikes','rock','spikes'])
                self.assertEqual(self.transitions,[(1,0,2),(3,1,3)])
                self.check_pp(before,st,[(0,3),(2,1)])
                self.identities_and_exp(before,st,138)
                st=self.pair(st,(2,1))
                self.assertEqual(self.losses,[])
