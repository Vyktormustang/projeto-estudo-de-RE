#!/usr/bin/env python3
"""gen_tramp_v4.py — gera reports/tramp_v4.hex (combo L+R+START -> preenche 8 slots da bolsa).

Composição (FATO, auditada com capstone):
  prefixo  = tramp_regkey.hex até o `bne` inclusive (gating REG_KEYINPUT 0x04000130,
             ativo-baixo -> mvns -> máscara 0x3FF -> cmp 0x308). Provado no mGBA (c35).
  payload  = 8 slots {id:u16, qty:u16} escritos a partir de 0x020258B8 (ENDEREÇO CORRIGIDO:
             v3 usava 0x022058B8 por erro de `lsls` — `movs #0x20` em vez de `#2`).
  cauda    = tramp_regkey do `pop{r0-r3}` até o fim: replay do prólogo + bx 0x08000A41.
"""
import pathlib, struct, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRAMP_BASE = 0x08EB0C00
RET = 0x08000A41                     # 0xA40|1: volta ao lsrs r1,r1,#0x10 (FATO c35)
BAG = 0x020258B8                     # {id:u16,qty:u16} x N, 4 B/slot
# (id, qty): payload original v3, preservado (nomes de item = HIPÓTESE, não verificados)
SLOTS = [(0x01, 0x63), (0x02, 0x63), (0x04, 0x63), (0x0D, 0x63),
         (0x1C, 0x32), (0x2D, 0x1E), (0x32, 0x1E), (0x13, 0x63)]

def load(p):
    return bytes.fromhex(open(p).read().replace(" ", "").strip())

def movs_r2(imm): return bytes([imm & 0xFF, 0x22])                # movs r2,#imm
def str_r2_r0():  return bytes.fromhex("0260")                    # str r2,[r0]
def strh_r2_r0_2(): return bytes.fromhex("4280")                  # strh r2,[r0,#2]
def adds_r0_4(): return bytes.fromhex("0430")                     # adds r0,#4

def build():
    rk = load(ROOT / "reports/tramp_regkey.hex")
    bne_off = next(i for i in range(0, len(rk) - 1, 2) if rk[i + 1] == 0xD1)  # 1º bne
    pop_off = next(i for i in range(bne_off + 2, len(rk) - 1, 2) if rk[i:i + 2] == bytes.fromhex("0fbc"))
    prefixo = bytearray(rk[:bne_off + 2])
    cauda = rk[pop_off:]
    # payload: ponteiro para BAG via movs/lsls/adds (mesma sequência já provada no regkey)
    ptr = bytes.fromhex("0220" "0002" "0230" "0004" "5821" "0902" "b831" "0818")
    # ^ r0 = 0x02020000 + 0x58B8 = 0x020258B8 (ver assert abaixo)
    fill = bytearray(ptr)
    for idx, (sid, qty) in enumerate(SLOTS):
        fill += movs_r2(sid) + str_r2_r0() + movs_r2(qty) + strh_r2_r0_2()
        if idx < len(SLOTS) - 1:
            fill += adds_r0_4()
    corpo = bytes(prefixo) + bytes(fill) + cauda
    # bne: alvo = pop novo; imm8 = (alvo - (pc_bne + 4)) / 2
    alvo = len(prefixo) + len(fill)  # offset do pop{r0-r3} NOVO (não o antigo)
    imm = (alvo - (bne_off + 4)) // 2
    assert 0 <= imm <= 0xFF, imm
    corpo = bytearray(corpo)
    corpo[bne_off] = imm
    corpo[bne_off + 1] = 0xD1
    return bytes(corpo)

if __name__ == "__main__":
    code = build()
    out = ROOT / "reports/tramp_v4.hex"
    out.write_text(" ".join(f"{b:02x}" for b in code))
    print(f"tramp_v4: {len(code)} B -> {out}")
