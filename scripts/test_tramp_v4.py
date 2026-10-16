#!/usr/bin/env python3
"""Prova semântica do tramp_v4 (mini-emulador Thumb, subset usado pelo tramp). FATO se passar.
Checa: escrita só no combo exato; endereço e conteúdo dos 8 slots; pilha/r5/lr/prólogo; retorno 0x08000A41."""
import pathlib, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from capstone.arm_const import ARM_OP_REG
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from gen_tramp_v4 import SLOTS, BAG

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail = True
code = bytes.fromhex((ROOT / "reports/tramp_v4.hex").read_text().replace(" ", ""))
insns = list(md.disasm(code, 0x08EB0C00))
assert sum(i.size for i in insns) == len(code), "decodificação incompleta"

def ci(r):  # capstone -> índice 0..15
    from capstone.arm_const import ARM_REG_SP, ARM_REG_LR, ARM_REG_PC
    return {ARM_REG_SP: 13, ARM_REG_LR: 14, ARM_REG_PC: 15}.get(r, r - 66 if r >= 66 else r)

def run(keys):
    R = {i: 0 for i in range(16)}
    R.update({0: 0x0102, 1: 0x12345678, 2: 0xCAFEBABE, 3: 0xDEADBEEF, 4: 0x44, 5: 0x55,
              6: 0x66, 7: 0x77, 13: 0x03007F00, 14: 0x0800ABCD, 15: 0x08EB0C00})
    mem = {0x04000130: keys}
    mem.update({BAG + 4 * k: 0xFFFFFFFF for k in range(len(SLOTS))})  # sentinela
    z = False
    def v(o): return R[ci(o.reg)] if o.type == ARM_OP_REG else o.imm & 0xFFFFFFFF
    for _ in range(400):
        pc = R[15]
        ins = next((i for i in insns if i.address == pc), None)
        if ins is None: return "FAULT", pc, mem, R
        m, ops = ins.mnemonic, ins.operands
        if m == "push":
            R[13] -= 4 * len(ops)
            for k, o in enumerate(ops): mem[R[13] + 4 * k] = R[ci(o.reg)]
        elif m == "pop":
            for o in ops: R[ci(o.reg)] = mem.get(R[13], 0); R[13] += 4
        elif m == "movs": R[ci(ops[0].reg)] = v(ops[1]); z = R[ci(ops[0].reg)] == 0
        elif m == "lsls": R[ci(ops[0].reg)] = (v(ops[1]) << v(ops[2])) & 0xFFFFFFFF; z = R[ci(ops[0].reg)] == 0
        elif m == "lsrs": R[ci(ops[0].reg)] = (v(ops[1]) >> v(ops[2])) & 0xFFFFFFFF
        elif m == "adds":
            R[ci(ops[0].reg)] = ((R[ci(ops[0].reg)] + v(ops[1])) if len(ops) == 2 else (v(ops[1]) + v(ops[2]))) & 0xFFFFFFFF
        elif m == "orrs": R[ci(ops[0].reg)] |= v(ops[1]); z = R[ci(ops[0].reg)] == 0
        elif m == "ands": R[ci(ops[0].reg)] &= v(ops[1]); z = R[ci(ops[0].reg)] == 0
        elif m == "mvns": R[ci(ops[0].reg)] = (~v(ops[1])) & 0xFFFFFFFF
        elif m == "cmp": z = v(ops[0]) == v(ops[1])
        elif m == "bne":
            if not z: R[15] = ops[0].imm; continue
        elif m == "ldrh":
            b = ops[1].mem; a = R[ci(b.base)] + (R[ci(b.index)] if b.index else 0) + b.disp
            R[ci(ops[0].reg)] = mem.get(a & ~1, 0) & 0xFFFF
        elif m == "str":
            b = ops[1].mem; a = R[ci(b.base)] + (R[ci(b.index)] if b.index else 0) + b.disp
            mem[a] = v(ops[0]) & 0xFFFFFFFF
        elif m == "strh":
            b = ops[1].mem; a = R[ci(b.base)] + (R[ci(b.index)] if b.index else 0) + b.disp
            old = mem.get(a & ~3, 0); sh = (a & 2) * 8
            mem[a & ~3] = (old & ~(0xFFFF << sh) | ((v(ops[0]) & 0xFFFF) << sh)) & 0xFFFFFFFF
        elif m == "bx": return "BX", v(ops[0]), mem, R
        else: return "UNSUP:" + m, pc, mem, R
        R[15] = pc + ins.size
    return "LOOP", 0, mem, R

def bolsa_ok(mem):
    for k, (sid, qty) in enumerate(SLOTS):
        w = mem.get(BAG + 4 * k, 0)
        if (w & 0xFFFF) != sid or ((w >> 16) & 0xFFFF) != qty:
            return False, k, w
    return True, None, None

B = dict(START=3, A=1, L=8, R=9)
def keyin(pressed):
    v = 0x3FF
    for b in pressed: v &= ~(1 << b)
    return v

casos = [
    ("L+R+START (combo)",     [B["L"], B["R"], B["START"]], True),
    ("sem teclas",            [], False),
    ("L+R sem START",         [B["L"], B["R"]], False),
    ("L+R+START+A (extra)",   [B["L"], B["R"], B["START"], B["A"]], False),
    ("START sozinho",         [B["START"]], False),
]
ok = True
for nome, pr, espero in casos:
    st, t, mem, R = run(keyin(pr))
    bolsa, k_ruim, w_ruim = bolsa_ok(mem) if espero else (True, None, None)
    if not espero:  # sem combo: bolsa intocada
        bolsa = all(mem.get(BAG + 4 * k) == 0xFFFFFFFF for k in range(len(SLOTS)))
    # contrato: prólogo original replayado sobre os args (r0=(r0<<24), r1=(r1<<16), r4=r0&0xFF)
    regs_ok = R[0] == (0x0102 << 24) & 0xFFFFFFFF and R[1] == (0x12345678 << 16) & 0xFFFFFFFF and R[4] == 0x02
    lr_ok = R[5] == 0x55 and R[14] == 0x0800ABCD
    ret_ok = st == "BX" and t == 0x08000A41
    res = bolsa and regs_ok and lr_ok and ret_ok
    ok &= res
    extra = "" if bolsa or not espero else f" slot{k_ruim}={w_ruim:08x}"
    print(f"  [{'OK ' if res else 'FALHA'}] {nome:22s} bolsa_ok={bolsa}{extra} regs={regs_ok} lr={lr_ok} ret=0x{t:08x} ({st})")
print("\nPROVA SEMÂNTICA tramp_v4:", "TODOS OS CASOS OK" if ok else "FALHAS")
sys.exit(0 if ok else 1)
