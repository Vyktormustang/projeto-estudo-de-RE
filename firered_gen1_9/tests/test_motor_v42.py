"""Strict builder checks + independent interpreter of emitted native bytecode.

The interpreter checks control flow, NOT native engine behavior; mGBA is separate.
"""
import os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from scripts import motor_v42 as p,auditar_obtencao_v40 as audit
BASE=os.environ.get('MOTOR_V42_BASE');ROM=os.environ.get('MOTOR_V42_ROM')

def simulate(scene=3,stage=5,rainbow=True,owned=(),flags=(),free=2,questlog=0):
    inventory={i:1 for i in owned}
    if rainbow:inventory[368]=1
    flags=set(flags);variables={0x407E:scene,0x4076:stage,0x800D:0};pc=0;comparison=0;messages=[];adds=[]
    b=p.SCRIPT_BYTES
    for _ in range(200):
        op=b[pc]
        if op in (5,6):
            condition=b[pc+1] if op==6 else None;target=struct.unpack_from('<I',b,pc+(2 if op==6 else 1))[0]
            take=op==5 or (comparison<0,comparison==0,comparison>0,comparison<=0,comparison>=0,comparison!=0)[condition]
            pc+=6 if op==6 else 5
            if take:
                if target==p.RESUME_SCRIPT:return inventory,flags,messages,adds
                pc=target-(0x08000000+p.SCRIPT_OFFSET)
            continue
        if op==0x16:
            var,value=struct.unpack_from('<HH',b,pc+1);assert var==0x8000;variables[var]=value;pc+=5
        elif op==0x21:
            var,value=struct.unpack_from('<HH',b,pc+1);actual=variables[var];comparison=(actual>value)-(actual<value);pc+=5
        elif op in (0x44,0x47):
            item,qty=struct.unpack_from('<HH',b,pc+1);assert qty==1
            if op==0x47:variables[0x800D]=int(inventory.get(item,0)>=qty)
            else:
                variables[0x800D]=int(free>0)
                if free>0:free-=1;inventory[item]=inventory.get(item,0)+1;adds.append(item)
            pc+=5
        elif op in (0x29,0x2B):
            flag=struct.unpack_from('<H',b,pc+1)[0]
            if op==0x29:flags.add(flag)
            else:comparison=0 if flag in flags else -1
            pc+=3
        elif op==0x25:
            assert struct.unpack_from('<H',b,pc+1)[0]==0x187;variables[0x800D]=questlog;pc+=3
        elif op==0x67:
            ptr=struct.unpack_from('<I',b,pc+1)[0];messages.append(p.TEXT_POINTERS.index(ptr));pc+=5
        elif op in (0x6A,0x5A,0x66,0x6D,0x68,0x6C):pc+=1
        else:raise AssertionError((pc,op))
    raise AssertionError('Script did not delegate to original')

class TicketScriptTests(unittest.TestCase):
    def test_progress_pass_and_questlog_guards(self):
        for scene in range(5):
            for stage in range(7):
                for rainbow in (False,True):
                    inv,flags,msg,adds=simulate(scene,stage,rainbow)
                    eligible=scene==3 and stage>=5 and rainbow
                    self.assertEqual(adds,[370,371] if eligible else [])
                    self.assertEqual(flags,{0x84A,0x84B} if eligible else set())
        self.assertEqual(simulate(questlog=2)[2:],([],[]))
    def test_all_inventory_flag_combinations_idempotent_and_no_capture_reset(self):
        preserved={0x2F2,0x2F3,0x2E4,0x2F5,0x2F6,0x2F7,0x9B,0x9C,0x99,0x9A,0x2A7,0x2A8}
        for items in range(4):
            for bits in range(4):
                owned=[370+i for i in range(2) if items&(1<<i)];flags=preserved|{0x84A+i for i in range(2) if bits&(1<<i)}
                inv,new,msg,adds=simulate(owned=owned,flags=flags)
                self.assertEqual((inv[370],inv[371]),(1,1));self.assertEqual(new,flags|{0x84A,0x84B})
                self.assertEqual(adds,[i for i in (370,371) if i not in owned])
                full=simulate(owned=owned,flags=flags,free=0)
                self.assertEqual(full[3],[]);self.assertEqual(full[1],flags|{0x84A+i for i in range(2) if items&(1<<i)})
                for item in (370,371):self.assertEqual(full[0].get(item,0),int(item in owned))
                again=simulate(owned=(370,371),flags=new,free=0);self.assertEqual(again[2:],([],[]));self.assertEqual(again[1],new)
    def test_full_bag_partial_delivery_retry_and_repair_without_room(self):
        inv,flags,msg,adds=simulate(free=0);self.assertEqual((flags,msg,adds),(set(),[4],[]))
        inv,flags,msg,adds=simulate(free=1);self.assertEqual((flags,msg,adds),({0x84A},[0,4],[370]))
        inv,flags,msg,adds=simulate(owned=(370,),flags=flags,free=1);self.assertEqual((flags,msg,adds),({0x84A,0x84B},[2],[371]))
        inv,flags,msg,adds=simulate(owned=(370,371),free=0);self.assertEqual((flags,msg,adds),({0x84A,0x84B},[1,3],[]))
        self.assertEqual(simulate(flags=(0x84B,),free=0)[1],{0x84B})
    def test_text_bounds_and_reservations(self):
        self.assertLessEqual(p.SCRIPT_OFFSET+len(p.SCRIPT_BYTES),p.TEXT_OFFSET)
        self.assertLessEqual(p.TEXT_OFFSET+len(p.TEXT_BYTES),p.RESERVED_LIMIT)
        for t in p.TEXTS:self.assertTrue(all(len(line)<=32 for line in t.split('\n')))
        self.assertEqual(len(p.SCRIPT_BYTES),247);self.assertEqual(len(p.TEXT_BYTES),287)

@unittest.skipUnless(BASE and ROM,'set MOTOR_V42_BASE and MOTOR_V42_ROM')
class MotorV42BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.path=Path(BASE).resolve();cls.before=cls.path.read_bytes();cls.after=Path(ROM).read_bytes()
    def test_exact_rebuild_and_only_declared_three_ranges(self):
        self.assertEqual(p.digest(self.before),p.BASE_SHA256);self.assertEqual(p.digest(self.after),p.OUTPUT_SHA256)
        self.assertEqual(p.build(self.before),self.after);restored=bytearray(self.after)
        for at,n in p.PATCH_RANGES:restored[at:at+n]=self.before[at:at+n]
        self.assertEqual(bytes(restored),self.before)
        self.assertEqual(self.after[p.HOOK_OFFSET:p.HOOK_OFFSET+7],p.HOOK_BYTES)
        self.assertEqual(struct.unpack_from('<I',self.after,p.POINTER_OFFSET)[0],p.OLD_SCRIPT)
    def test_previous_encounters_guide_events_and_evolutions_identical(self):
        cat=p.base.wild.load_species();maps=p.base.wild.load_maps()
        self.assertEqual(p.base.wild.parse_tables(self.before,maps,cat),p.base.wild.parse_tables(self.after,maps,cat))
        self.assertEqual(p.base.guide_csv(self.before),p.base.guide_csv(self.after))
        self.assertEqual(p.base.base.previous.pilot_tables(self.before),p.base.base.previous.pilot_tables(self.after))
        self.assertEqual(audit.objects(self.before,cat),audit.objects(self.after,cat))
        self.assertEqual(audit.native_events(self.before),audit.native_events(self.after))
        self.assertEqual(audit.evolutions(self.before),audit.evolutions(self.after))
        for at,n in p.base.base.PATCH_RANGES:self.assertEqual(self.before[at:at+n],self.after[at:at+n])
    def test_bad_input_rejected_and_item_ids_are_actual_rainbow_not_tea(self):
        self.assertEqual(p.RAINBOW_PASS,368)
        for b in (b'',self.before[:-1],self.after,bytes((self.before[0]^1,))+self.before[1:]):
            with self.assertRaises(p.PatchError):p.build(b)
    def test_cli_new_output_only_and_input_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'v42.gba';cmd=[sys.executable,'-B',str(p.ROOT/'scripts/motor_v42.py'),'--rom',str(self.path),'--saida',str(out)]
            done=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(done.returncode,0,done.stderr)
            self.assertEqual(out.read_bytes(),self.after);self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            alias=Path(td)/'alias.gba';alias.symlink_to(self.path)
            for dest in (self.path,alias):
                with self.assertRaises(ValueError):p.write_new_file(self.path,dest,self.after)
            self.assertEqual(self.path.read_bytes(),self.before)
