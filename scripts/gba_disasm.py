#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gba_disasm.py — desassembly evidencial de ROM GBA (boot ARM + censo Thumb)
==========================================================================

OBJETIVO
    1. BOOT TRACE: desassemblar ARM a partir de 0x08000000 seguindo branches
       diretos (incl. resolução de literais `ldr rN, [pc,#i]`) até a PRIMEIRA
       transição ARM→Thumb (BX p/ endereço ímpar) — descobre mecanicamente o
       ponto de entrada principal. Sem suposições: o caminho vem da ROM.
    2. CENSO DE FUNÇÕES: linear-sweep Thumb (capstone) na região de código,
       coletando BL (direto!) e seus alvos. Alvo de BL direto é evidência DURA
       de endereço de função — não é chute. Cada alvo recebe nota de prólogo
       (push {…,lr} = B5xx, sub sp, etc.).
    3. PROVA ARM×THUMB: cada página de 4 KiB é tentada nos DOIS modos; média de
       instruções inválidas decide qual modo é plausível ali. Empírico.
    4. Popula functions.csv apenas com o que tem evidência registrada.

PRÉ-REQUISITOS
    Python 3.9+ E capstone (bash scripts/setup_env.sh). Sem capstone: exit 4.

ENTRADAS      ROM bruta (.gba).
SAÍDAS (-o)   <rom>_disasm_boot.json      — traço do boot, transição, entry Thumb
              <rom>_thumb_census.json     — estatísticas + alvos (funções) + top-chamadas
              functions.csv (--update-functions) — linhas auto (origem=gba_disasm_capstone)
              logs/gba_disasm_runs.jsonl

USO
    python3 gba_disasm.py ROM.gba all -o reports --update-functions ../functions.csv
    python3 gba_disasm.py ROM.gba boot            # só boot trace
    python3 gba_disasm.py ROM.gba census          # só censo Thumb/ARM
    python3 gba_disasm.py --self-test

LIMITAÇÕES DECLARADAS
    1. Linear-sweep NÃO distingue literal pools embutidos no código: páginas com
       muitos "inválidos" em meio a Thumb válido são normais (dados literais).
    2. O censo cobre apenas chamadas DIRETAS (BL). Funções só alcançadas via
       ponteiros/indiretas (tabelas de salto, IRQ) não entram por este método.
    3. Nomes FUN_######## são provisórios mecânicos; renomear SÓ com evidência.
    4. O "modo plausível" por página é estatístico; páginas ambíguas ficam
       marcadas AMBIGUA e exigem olho humano.

CÓDIGO DE SAÍDA: 0 ok | 1 falha self-test | 2 argumentos | 3 arquivo | 4 capstone ausente
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSAO = "1.0.0"
GBA_ROM_BASE = 0x08000000

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
    from capstone.arm_const import ARM_OP_IMM, ARM_OP_MEM, ARM_REG_PC
    CAPSTONE_OK = True
except ImportError:
    CAPSTONE_OK = False


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #

def _md(mode_thumb: bool) -> "Cs":
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if mode_thumb else CS_MODE_ARM)
    md.detail = True   # necessário p/ acessar insn.operands (alvos de BL, literais)
    return md


def ler_literal_arm(data: bytes, addr_instr: int, disp: int) -> tuple[int, int]:
    """Endereço do literal LDR [pc,#disp] (PC = addr+8) e o valor de 32 bits."""
    lit_addr = ((addr_instr + 8) + disp) & 0xFFFFFFFF
    off = lit_addr - GBA_ROM_BASE
    if 0 <= off <= len(data) - 4:
        return lit_addr, int.from_bytes(data[off:off + 4], "little")
    return lit_addr, -1


# Faixa do imediato BL Thumb: 22 bits com sinal em halfwords → bytes
# [-0x400000, +0x3FFFFE]. Fora disso NÃO há encoding — o alvo é inalcançável.
BL_DISP_HALFWORD_MIN = -0x200000
BL_DISP_HALFWORD_MAX = 0x1FFFFF


def encode_bl_thumb(site: int, alvo: int) -> bytes:
    """Codifica um BL Thumb de `site` para `alvo`. Usado em testes/fixtures —
    NUNCA montar BL de teste com hex manual (erros de aritmética já morderam).

    Base do PC = site+4 (NÃO alinhada — homologado vs 88.782 callsites reais e
    capstone: 0 divergências dentro da faixa; ver progress.md c35). Levanta
    ValueError fora da faixa ±4 MB (o wrap silencioso já mordeu: contas que
    "validavam o campo" geravam bytes que apontavam para outro lugar)."""
    delta = alvo - (site + 4)
    if delta % 2 != 0:
        raise ValueError(
            f"BL Thumb exige alvo halfword-alinhado: site=0x{site:08X} alvo=0x{alvo:08X}")
    disp = delta // 2
    if not (BL_DISP_HALFWORD_MIN <= disp <= BL_DISP_HALFWORD_MAX):
        raise ValueError(
            f"BL Thumb FORA DE ALCANCE: site=0x{site:08X} alvo=0x{alvo:08X} "
            f"(disp={disp} halfwords; faixa {BL_DISP_HALFWORD_MIN}..{BL_DISP_HALFWORD_MAX})")
    s = (disp >> 22) & 1
    hw1 = 0xF000 | (s << 10) | ((disp >> 11) & 0x3FF)
    hw2 = 0xF800 | (disp & 0x7FF)
    return hw1.to_bytes(2, "little") + hw2.to_bytes(2, "little")


# --------------------------------------------------------------------------- #
# 1) Boot trace ARM
# --------------------------------------------------------------------------- #

def boot_trace(data: bytes, max_insns: int = 256, max_saltos: int = 64) -> dict:
    """Segue o fluxo direto do boot até a 1ª transição Thumb (ou perda do rastro)."""
    md = _md(False)
    regs: dict[str, int] = {}
    pc = GBA_ROM_BASE
    trace: list[dict] = []
    saltos = 0
    transicao = None
    motivo_parada = "limite de instruções"

    for _ in range(max_insns):
        off = pc - GBA_ROM_BASE
        if off < 0 or off > len(data) - 4:
            motivo_parada = f"PC fora da ROM: 0x{pc:08x}"
            break
        ins = next(iter(md.disasm(data[off:off + 4], pc, count=1)), None)
        if ins is None:
            motivo_parada = f"bytes não decodificáveis em 0x{pc:08x}"
            break
        passo = {
            "addr": f"0x{ins.address:08x}", "bytes": ins.bytes.hex(),
            "mn": ins.mnemonic, "op": ins.op_str,
        }
        trace.append(passo)
        mn, ops = ins.mnemonic, ins.operands
        proximo = pc + 4

        if mn in ("b", "beq", "bne", "bcs", "bcc", "bmi", "bpl", "bvs", "bvc",
                  "bhi", "bls", "bge", "blt", "bgt", "ble", "bl", "blx"):
            if ops and ops[-1].type == ARM_OP_IMM:
                alvo = ops[-1].imm & 0xFFFFFFFF
                passo["acao"] = f"salto p/ 0x{alvo:08x}" + (" (call)" if "l" in mn else "")
                if mn.startswith("b") and mn not in ("bl", "blx") and saltos < max_saltos:
                    if mn != "b":
                        passo["acao"] += " [condicional: seguido o NÃO-desvio]"
                    else:
                        pc = alvo
                        saltos += 1
                        continue
            else:
                passo["acao"] = "branch sem imediato? — rastro perdido"
                motivo_parada = "branch indireto não-resolvido"
                break
        elif mn == "bx":
            if ops:
                rn = mn and ins.op_str.split()[0].rstrip(",")
                val = regs.get(rn)
                if val is None:
                    motivo_parada = f"BX {rn} com valor desconhecido (regs rastreados: {regs})"
                    passo["acao"] = "rastro perdido em BX indireto"
                    break
                modo = "THUMB" if val & 1 else "ARM"
                passo["acao"] = f"BX {rn}=0x{val:08x} → modo {modo}"
                if val & 1:
                    transicao = {"addr_thumb_hex": f"0x{val & ~1:08x}",
                                 "via": "BX com literal rastreado",
                                 "instr_boot_arm": len(trace)}
                    motivo_parada = "transição ARM→Thumb localizada"
                    pc = val & ~1
                    break
                pc = val
                saltos += 1
                continue
        elif mn == "mov" and len(ops) == 2 and ops[1].type == ARM_OP_IMM:
            regs[ins.reg_name(ops[0].reg)] = ops[1].imm & 0xFFFFFFFF
        elif mn == "ldr" and len(ops) == 2 and ops[1].type == ARM_OP_MEM and \
                ops[1].mem.base == ARM_REG_PC:
            lit_addr, val = ler_literal_arm(data, ins.address, ops[1].mem.disp)
            passo["literal_de"] = f"0x{lit_addr:08x}"
            if val != -1:
                passo["literal_valor"] = f"0x{val:08x}"
                regs[ins.reg_name(ops[0].reg)] = val
            else:
                passo["literal_valor"] = "FORA_DA_ROM"
        pc = proximo

    return {
        "transicao_thumb": transicao,
        "motivo_parada": motivo_parada,
        "instrucoes_tracadas": len(trace),
        "trace": trace,
    }


# --------------------------------------------------------------------------- #
# 2/3) Censo Thumb + prova de modo por página
# --------------------------------------------------------------------------- #

BRANCH_MNEMONICOS = {
    "b", "bl", "beq", "bne", "bhs", "blo", "bcs", "bcc", "bmi", "bpl",
    "bvs", "bvc", "bhi", "bls", "bge", "blt", "bgt", "ble", "blx",
}


def sweep_pagina(md: "Cs", buf: bytes, base: int, passo_invalid: int) -> dict:
    """Linear sweep de uma página; retorna insns, bytes não decodificados e
    alvos de branch (B/BL diretos) — usados na prova de LOCALIDADE de fluxo.

    REGRESSÃO COBERTA: avanco é deslocamento a partir de `base` (início da página)
    — atribuir com `i = avanco`. (Bug histórico: `i += avanco` dobrava o cursor e
    varria só ~16% da página; detectado por saneamento de insns/página.)
    """
    insns, invalid, alvos_branch = [], 0, []
    i = 0
    while i < len(buf) - 1:
        dec = list(md.disasm(buf[i:], base + i, count=64))
        if not dec:
            invalid += passo_invalid
            i += passo_invalid
            continue
        insns.extend(dec)
        for ins in dec:
            if ins.mnemonic in BRANCH_MNEMONICOS and ins.operands and \
                    ins.operands[-1].type == ARM_OP_IMM:
                alvos_branch.append(ins.operands[-1].imm & 0xFFFFFFFF)
        avanco = (dec[-1].address + dec[-1].size) - base
        i = avanco if avanco > i else i + passo_invalid  # garante progresso
    return {"insns": insns, "invalid_bytes": invalid,
            "branch_targets": alvos_branch}


def nota_prologo_thumb(data: bytes, alvo: int) -> str:
    off = alvo - GBA_ROM_BASE
    if off < 0 or off + 2 > len(data):
        return "fora_da_rom"
    hw = data[off] | (data[off + 1] << 8)
    hi = hw >> 8
    if hi == 0xB5:
        return "push_regs_lr (B5)"
    if hi == 0xB4:
        return "push_regs (B4)"
    if (hw & 0xFF80) == 0xB080:
        return "sub_sp (B08x)"
    if hi in (0x46, 0x47):
        return "mov/add hi-reg (46/47)"
    return "outro"


def censo_codigo(data: bytes, regioes: list[tuple[int, int]],
                 pagina: int = 4096) -> dict:
    md_t, md_a = _md(True), _md(False)
    paginas = []
    alvos_bl: Counter = Counter()
    callsites_bl: list[dict] = []
    tot_t = tot_a = 0

    for (ini, fim) in regioes:
        p = ini
        while p < fim:
            buf = data[p:min(p + pagina, fim)]
            base = GBA_ROM_BASE + p
            res_t = sweep_pagina(md_t, buf, base, 2)
            res_a = sweep_pagina(md_a, buf, base, 4)
            n_t, n_a = len(res_t["insns"]), len(res_a["insns"])
            inv_t, inv_a = res_t["invalid_bytes"], res_a["invalid_bytes"]
            # PROVA DE PRÓLOGO-ALVO: no modo correto, alvos de BL/B caem em
            # prólogos canônicos (Thumb: byte alto 0xB5 = push {…,lr}; ARM:
            # STMFD = 0xE92D). No modo errado, isso acontece por acaso ~1/256.
            # (Localidade de endereço foi descartada: o alcance de B/BL é
            # ±4 MiB/±32 MiB e a ROM tem 16 MiB — alvos de lixo caem dentro.)
            def hitrate_prologo(alvos):
                if len(alvos) < 8:
                    return None
                ok_t = ok_a = 0
                for a in alvos:
                    off = a - GBA_ROM_BASE
                    if 0 <= off <= len(data) - 4:
                        if data[off + 1] == 0xB5:
                            ok_t += 1
                        if data[off + 3] == 0xE9 and data[off + 2] == 0x2D:
                            ok_a += 1
                return ok_t / len(alvos), ok_a / len(alvos)

            br_t, br_a = res_t["branch_targets"], res_a["branch_targets"]
            par_t = hitrate_prologo(br_t)
            par_a = hitrate_prologo(br_a)
            hit_t = par_t[0] if par_t else None   # alvos de branch-THUMB em prólogo thumb
            hit_a = par_a[1] if par_a else None   # alvos de branch-ARM em prólogo arm
            if hit_t is not None and hit_t >= 0.35 and hit_t >= 5 * (hit_a or 0):
                veredito = "THUMB(verificado: alvos em prólogos)"
            elif hit_a is not None and hit_a >= 0.35 and hit_a >= 5 * (hit_t or 0):
                veredito = "ARM(verificado: alvos em prólogos)"
            elif len(br_t) < 8 and len(br_a) < 8:
                veredito = "DADOS(pouco/nenhum fluxo)"
            else:
                veredito = "AMBIGUA(revisar manualmente)"
            cov_t = min(1.0, (n_t * 2) / len(buf))
            cov_a = min(1.0, (n_a * 4) / len(buf))
            for ins in res_t["insns"]:
                if ins.mnemonic == "bl" and ins.operands:
                    alvo = ins.operands[-1].imm & 0xFFFFFFFF
                    alvos_bl[alvo] += 1
                    callsites_bl.append({"site": f"0x{ins.address:08x}",
                                         "alvo": f"0x{alvo:08x}"})
            paginas.append({
                "offset_hex": f"0x{p:08x}", "modo_plausivel": veredito,
                "thumb": {"insns": n_t, "invalid": inv_t, "cobertura": round(cov_t, 4),
                          "branches": len(br_t),
                          "hit_prologo_thumb": None if hit_t is None else round(hit_t, 4)},
                "arm": {"insns": n_a, "invalid": inv_a, "cobertura": round(cov_a, 4),
                        "branches": len(br_a),
                        "hit_prologo_arm": None if hit_a is None else round(hit_a, 4)},
            })
            tot_t += n_t
            tot_a += n_a
            p += pagina

    funcoes = []
    for alvo, chamadas in alvos_bl.items():
        funcoes.append({
            "endereco_hex": f"0x{alvo:08x}",
            "chamadas_bl_diretas": chamadas,
            "prologo_thumb": nota_prologo_thumb(data, alvo),
            "regiao": ("ROM" if GBA_ROM_BASE <= alvo < GBA_ROM_BASE + len(data)
                       else ("IWRAM/WRAM" if alvo in range(0x02000000, 0x04000000)
                             else "fora_do_mapa")),
        })
    funcoes.sort(key=lambda f: -f["chamadas_bl_diretas"])

    v_thumb = sum(1 for x in paginas if x["modo_plausivel"].startswith("THUMB"))
    v_arm = sum(1 for x in paginas if x["modo_plausivel"].startswith("ARM"))
    v_dados = sum(1 for x in paginas if x["modo_plausivel"].startswith("DADOS"))
    return {
        "regioes_analisadas": [f"0x{a:08x}-0x{b:08x}" for a, b in regioes],
        "insns_decodificadas_thumb": tot_t,
        "insns_decodificadas_arm": tot_a,
        "paginas_thumb_plausivel": v_thumb,
        "paginas_arm_plausivel": v_arm,
        "paginas_dados_sem_fluxo": v_dados,
        "paginas_total": len(paginas),
        "bl_encontrados": len(callsites_bl),
        "alvos_unicos": len(alvos_bl),
        "callsites": callsites_bl,
        "dist_prologos": dict(Counter(f["prologo_thumb"] for f in funcoes)),
        "top_chamadas": funcoes[:40],
        "funcoes": funcoes,
        "paginas": paginas,
    }


def dualcheck_bl(data: bytes, amostra: list[dict], n: int = 100) -> dict:
    """Validação dupla: decodificação manual dos BL vs. capstone (integridade)."""
    conferidos, divergencias = 0, []
    for cs in amostra[:n]:
        site = int(cs["site"], 16)
        off = site - GBA_ROM_BASE
        if off < 0 or off + 4 > len(data):
            continue
        hw1 = data[off] | (data[off + 1] << 8)
        # segunda metade: [15:11]=11111, [10:0]=imm_lo
        hw2 = data[off + 2] | (data[off + 3] << 8)
        # imediato 22 bits (imm_hi 11 bits : imm_lo 11 bits), sinal no bit 21
        imm = ((hw1 & 0x7FF) << 11) | (hw2 & 0x7FF)
        if imm & (1 << 21):
            imm -= 1 << 22
        alvo_manual = (site + 4 + (imm << 1)) & 0xFFFFFFFF
        conferidos += 1
        if alvo_manual != int(cs["alvo"], 16):
            divergencias.append({"site": cs["site"],
                                 "capstone": cs["alvo"],
                                 "manual": f"0x{alvo_manual:08x}"})
    return {"conferidos": conferidos, "divergencias": divergencias}


# --------------------------------------------------------------------------- #
# functions.csv
# --------------------------------------------------------------------------- #

ORIGEM_AUTO = "gba_disasm_capstone"


def atualizar_functions_csv(caminho: Path, funcoes: list[dict],
                            data: bytes, entry_thumb: int | None,
                            registry_path: Path | None = None) -> dict:
    """Regrava as linhas auto; preserva manuais e APLICA o names_registry.json.

    Linhas auto (origem=gba_disasm_capstone) são regeneradas; se o endereço tem
    nome registrado, a linha nasce JÁ renomeada (origem=registro), preservando
    evidência e histórico entre regenerações.
    """
    registry: dict = {}
    if registry_path and registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

    existentes: list[str] = []
    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            if not linha.strip() or linha.startswith("#") or \
               ORIGEM_AUTO in linha or linha.startswith("endereco_hex"):
                continue
            if linha.split(",", 1)[0] in registry:
                continue  # registry é autoridade: a linha renasce fresca abaixo
            existentes.append(linha)

    GRADES_CSV = {"push_regs_lr (B5)", "push_regs (B4)", "sub_sp (B08x)"}
    linhas, aplicados, descartados_baixa_prova = [], 0, 0
    for f in funcoes:
        addr = f["endereco_hex"]
        if addr in registry:
            r = registry[addr]
            aplicados += 1
            linhas.append(",".join([
                addr, "-", r["nome"], "THUMB",
                r["confianca"], r["origem"], r["evidencia"],
                r.get("historico", "registrado"),
            ]))
            continue
        if f["prologo_thumb"] not in GRADES_CSV:
            # alvo sem evidência de prólogo real (falso BL de dados/desync):
            # permanece no TSV de funções, mas NUNCA ganha linha de função no CSV
            descartados_baixa_prova += 1
            continue
        nome = (f"FUN_{addr[2:]}"
                if not (entry_thumb and int(addr, 16) == entry_thumb)
                else f"ENTRY_THUMB_boot_{addr[2:]}")
        linhas.append(",".join([
            addr, "-", nome, "THUMB",
            "CONFIRMADO(alvo_BL_direto)", ORIGEM_AUTO,
            f"alvo de BL direto x{f['chamadas_bl_diretas']}; prologo={f['prologo_thumb']}",
            "auto-gerado",
        ]))
    header = ("endereco_hex,tamanho_hex,nome,modo_cpu,confianca,origem,evidencia,"
              "historico_renomeacao")
    comentario = ("# endereco no espaco do GBA. Linhas com origem gba_disasm_capstone sao "
                  "regeneradas a cada execucao; nomes de names_registry.json sao reaplicados; "
                  "edicoes manuais sao preservadas.")
    caminho.write_text("\n".join([header, comentario] + existentes + linhas) + "\n",
                       encoding="utf-8")
    return {"linhas_auto": len(linhas), "linhas_manuais_preservadas": len(existentes),
            "nomes_registrados_aplicados": aplicados,
            "descartados_baixa_prova_ficam_no_tsv": descartados_baixa_prova}


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #

def self_test(verbose: bool) -> int:
    checks = []
    if not CAPSTONE_OK:
        print("  [SKIP] capstone ausente — self-test impossível")
        return 1

    # ROM sintética: boot ARM que carrega literal p/ Thumb + trecho Thumb c/ BL
    buf = bytearray(0x400)
    # 0x08000000: b 0x08000010          (EA000002)
    buf[0x0:0x4] = bytes.fromhex("020000ea")
    # 0x08000010: ldr r0, [pc, #0] → literal em 0x08000018
    buf[0x10:0x14] = bytes.fromhex("00009fe5")
    # 0x08000014: bx r0
    buf[0x14:0x18] = bytes.fromhex("10ff2fe1")
    # 0x08000018: literal 0x08000041 (Thumb)
    buf[0x18:0x1C] = (0x08000041).to_bytes(4, "little")
    # 0x08000040 (Thumb): push {r4,lr} ; bl 0x08000054 ; bx lr
    buf[0x40:0x42] = bytes([0x10, 0xB5])
    buf[0x42:0x46] = encode_bl_thumb(GBA_ROM_BASE + 0x42, GBA_ROM_BASE + 0x54)
    buf[0x46:0x48] = bytes([0x70, 0x47])              # bx lr
    buf[0x54:0x56] = bytes([0x08, 0xB5])              # push {r3,lr} (alvo do BL)

    tr = boot_trace(bytes(buf))
    checks.append(("transição Thumb @0x08000040",
                   tr["transicao_thumb"] is not None and
                   tr["transicao_thumb"]["addr_thumb_hex"] == "0x08000040"))
    checks.append(("literal rastreado no trace",
                   any("literal_valor" in p for p in tr["trace"])))

    res = censo_codigo(bytes(buf), [(0x40, 0x60)], pagina=4096)
    alvos = {f["endereco_hex"] for f in res["funcoes"]}
    checks.append(("censo acha alvo BL 0x08000054", "0x08000054" in alvos))
    f54 = next((f for f in res["funcoes"] if f["endereco_hex"] == "0x08000054"), None)
    checks.append(("prólogo do alvo = push_regs_lr",
                   f54 is not None and f54["prologo_thumb"].startswith("push_regs_lr")))
    # página com 1 BL só não rende veredito (amostra insuficiente) — e isso é honesto
    checks.append(("classificador: 1 branch → sem veredito forçado",
                   res["paginas"][0]["modo_plausivel"].startswith("DADOS")))

    # página com 8 BLs apontando para prólogos → veredito THUMB verificado
    buf3 = bytearray(0x400)
    for k in range(8):
        site = 0x40 + k * 8
        buf3[site:site + 4] = encode_bl_thumb(GBA_ROM_BASE + site, GBA_ROM_BASE + 0x200)
    buf3[0x200:0x202] = bytes([0xF0, 0xB5])  # push {r4-r7,lr}
    res3 = censo_codigo(bytes(buf3), [(0x40, 0x240)], pagina=4096)
    checks.append(("classificador: 8 BLs→prólogo marca THUMB (verificado)",
                   res3["paginas"][0]["modo_plausivel"].startswith("THUMB")))

    chk = dualcheck_bl(bytes(buf), [{"site": "0x08000042", "alvo": "0x08000054"}])
    checks.append(("dual-check BL manual×capstone sem divergência",
                   chk["conferidos"] == 1 and not chk["divergencias"]))

    # regressão: BL PARA TRÁS — sinal no bit 21 (bug histórico: sinal no bit 22
    # divergia do capstone em saltos negativos; só aparecia em código real)
    buf2 = bytearray(0x800)
    buf2[0x100:0x104] = encode_bl_thumb(GBA_ROM_BASE + 0x100, GBA_ROM_BASE + 0x030)
    chk2 = dualcheck_bl(bytes(buf2), [{"site": "0x08000100", "alvo": "0x08000030"}])
    checks.append(("BL para trás: manual == capstone",
                   chk2["conferidos"] == 1 and not chk2["divergencias"]))

    # regressão c35: guarda de alcance — o wrap silencioso p/ |off| fora de ±4 MB
    # gerava bytes que NÃO apontavam para o alvo (1.579 pares reais em +0x400000).
    def _espera_fora(site, alvo):
        try:
            encode_bl_thumb(site, alvo)
            return False
        except ValueError:
            return True

    s0 = GBA_ROM_BASE + 0x1000
    # vetores expressos em halfwords (disp): válidos = [-0x200000, +0x1FFFFF]
    # alvo = site+4 + 2*disp
    def _alvo(disp_hw):
        return s0 + 4 + 2 * disp_hw

    checks.append(("fora-de-alcance disp=+0x200000 rejeitado",
                   _espera_fora(s0, _alvo(0x200000))))
    checks.append(("fora-de-alcance disp=-0x200002 rejeitado",
                   _espera_fora(s0, _alvo(-0x200002))))
    try:
        b_lim_pos = encode_bl_thumb(s0, _alvo(0x1FFFFF))
        b_lim_neg = encode_bl_thumb(s0, _alvo(-0x200000))
        lim_ok = len(b_lim_pos) == 4 and len(b_lim_neg) == 4
    except ValueError:
        lim_ok = False
    checks.append(("limites exatos +0x1FFFFF/-0x200000 halfwords aceitos", lim_ok))
    # extremos precisam decodificar de volta ao alvo (capstone = árbitro)
    md_t = _md(True)
    extremos_ok = True
    for disp_hw in (0x1FFFFF, -0x200000):
        enc_lim = encode_bl_thumb(s0, _alvo(disp_hw))
        ins_lim = next(iter(md_t.disasm(enc_lim, s0, count=1)), None)
        if ins_lim is None or ins_lim.mnemonic != "bl" or ins_lim.operands[0].imm != _alvo(disp_hw):
            extremos_ok = False
    checks.append(("extremos de faixa decodificam ao alvo (capstone)", extremos_ok))
    checks.append(("alvo ímpar rejeitado",
                   _espera_fora(s0, s0 + 3)))

    # regressão: sweep deve cobrir a página INTEIRA (bug histórico:
    # `i += avanco` dobrava o cursor; detectado por insns/página baixos)
    res_pg = sweep_pagina(_md(True), bytes(0x1000), GBA_ROM_BASE, 2)
    checks.append(("sweep cobre página inteira (2048 insns de movs em 4 KiB)",
                   len(res_pg["insns"]) == 2048))

    falhas = 0
    for nome, ok in checks:
        if verbose or not ok:
            print(f"  [{'PASS' if ok else 'FAIL'}] {nome}")
        falhas += 0 if ok else 1
    print(f"self-test: {len(checks) - falhas}/{len(checks)} verificações OK")
    return 1 if falhas else 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    script_dir = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(
        description="Boot trace ARM + censo de funções Thumb (capstone) — evidencial.")
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("cmd", nargs="?", default="all",
                    choices=["all", "boot", "census", "dis"])
    ap.add_argument("offset", type=lambda s: int(s, 0), nargs="?", default=None,
                    help="endereço GBA p/ cmd=dis (ex.: 0x0803fbe8)")
    ap.add_argument("-n", "--num", type=int, default=28,
                    help="nº de instruções no cmd=dis [28]")
    ap.add_argument("--mode", choices=["thumb", "arm"], default="thumb")
    ap.add_argument("-o", "--outdir", type=Path, default=script_dir.parent / "reports")
    ap.add_argument("--code-start", type=lambda s: int(s, 0), default=0x0)
    ap.add_argument("--code-end", type=lambda s: int(s, 0), default=0x160000)
    ap.add_argument("--islands", action="store_true", default=False,
                    help="inclui ilhas 0x1E0000/0x4B0000 (use só com --code-end pequeno)")
    ap.add_argument("--update-functions", type=Path, default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.verbose)
    if not CAPSTONE_OK:
        print("erro: capstone ausente — rode: bash scripts/setup_env.sh", file=sys.stderr)
        return 4
    if not args.rom or not args.rom.is_file():
        print("erro: informe uma ROM válida (ou --self-test).", file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    data = args.rom.read_bytes()
    args.outdir.mkdir(parents=True, exist_ok=True)
    stem = args.rom.stem
    feitos: dict[str, str] = {}
    entry_thumb = None

    if args.cmd == "dis":
        if args.offset is None:
            print("erro: cmd=dis requer offset (endereço GBA).", file=sys.stderr)
            return 2
        md = _md(args.mode == "thumb")
        off = args.offset - GBA_ROM_BASE
        if off < 0 or off >= len(data):
            print(f"erro: endereço 0x{args.offset:08x} fora da ROM.", file=sys.stderr)
            return 2
        print(f"== DIS {args.mode.upper()} @0x{args.offset:08x} (offset arquivo 0x{off:08x}) ==")
        for ins in md.disasm(data[off:off + args.num * 4], args.offset):
            com = ""
            if ins.mnemonic in BRANCH_MNEMONICOS and ins.operands and \
                    ins.operands[-1].type == ARM_OP_IMM:
                com = f"  ; → 0x{ins.operands[-1].imm & 0xFFFFFFFF:08x}"
            elif ins.mnemonic == "swi":
                com = f"  ; SWI 0x{ins.operands[0].imm & 0xFF:02X}" if ins.operands else ""
            elif ins.mnemonic == "ldr" and ins.operands and \
                    ins.operands[-1].type == ARM_OP_MEM and \
                    ins.operands[-1].mem.base == ARM_REG_PC:
                disp = ins.operands[-1].mem.disp
                if args.mode == "thumb":   # THUMB: EA = align(PC+4,4)+disp
                    ea = ((ins.address + 4) & ~3) + disp
                else:                      # ARM: EA = (PC+8)+disp
                    ea = (ins.address + 8) + disp
                o = ea - GBA_ROM_BASE
                if 0 <= o <= len(data) - 4:
                    val = int.from_bytes(data[o:o + 4], "little")
                    com = f"  ; [0x{ea:08x}] = 0x{val:08x}"
                else:
                    com = f"  ; [0x{ea:08x}] fora da ROM"
            print(f"  0x{ins.address:08x}: {ins.bytes.hex():<8} {ins.mnemonic:<10} {ins.op_str}{com}")
        return 0

    if args.cmd in ("all", "boot"):
        tr = boot_trace(data)
        p = args.outdir / f"{stem}_disasm_boot.json"
        p.write_text(json.dumps(tr, indent=2, ensure_ascii=False), encoding="utf-8")
        feitos["boot"] = str(p)
        print(f"== BOOT TRACE == ({tr['instrucoes_tracadas']} instruções ARM)")
        for passo in tr["trace"][:26]:
            extra = " | " + passo.get("acao", "")
            print(f"  {passo['addr']}: {passo['bytes']:<8} {passo['mn']:<6} {passo['op']:<24}{extra}")
        print(f"  motivo de parada: {tr['motivo_parada']}")
        if tr["transicao_thumb"]:
            entry_thumb = int(tr["transicao_thumb"]["addr_thumb_hex"], 16)
            print(f"  >> TRANSIÇÃO ARM→Thumb em {tr['transicao_thumb']['addr_thumb_hex']} "
                  f"(após {tr['transicao_thumb']['instr_boot_arm']} instr. ARM)")

    if args.cmd in ("all", "census"):
        regioes = [(args.code_start, min(args.code_end, len(data)))]
        if args.islands:
            regioes += [(0x1E0000, 0x1F0000), (0x4B0000, 0x4C0000)]
        res = censo_codigo(data, regioes)
        # dual-check (integridade): amostra dos callsites reais — primeiros 200 +
        # outros 100 espaçados uniformemente, re-decodificados manualmente
        sites = res["callsites"]
        amostra = sites[:200]
        if len(sites) > 300:
            passo = max(1, len(sites) // 100)
            amostra += sites[200::passo][:100]
        chk = dualcheck_bl(data, amostra)
        res["dualcheck_bl_manual_x_capstone"] = chk

        p = args.outdir / f"{stem}_thumb_census.json"
        slim = dict(res)
        slim["funcoes"] = f"{len(res['funcoes'])} no TSV"
        slim.pop("callsites", None)  # volumoso; alvos únicos já bastam no JSON
        p3 = args.outdir / f"{stem}_callsites.tsv"
        with p3.open("w", encoding="utf-8", newline="") as fcs:
            w = csv.writer(fcs, delimiter="\t")
            w.writerow(["site_hex", "alvo_hex"])
            for cs in res["callsites"]:
                w.writerow([cs["site"], cs["alvo"]])
        feitos["callsites_tsv"] = str(p3)

        p2 = args.outdir / f"{stem}_functions_auto.tsv"
        with p2.open("w", encoding="utf-8", newline="") as fcsv:
            w = csv.writer(fcsv, delimiter="\t")
            w.writerow(["endereco_hex", "chamadas_bl_diretas", "prologo_thumb", "regiao"])
            for f_ in res["funcoes"]:
                w.writerow([f_["endereco_hex"], f_["chamadas_bl_diretas"],
                            f_["prologo_thumb"], f_["regiao"]])
        p.write_text(json.dumps(slim, indent=2, ensure_ascii=False), encoding="utf-8")
        feitos.update({"census_json": str(p), "functions_tsv": str(p2)})

        print("\n== CENSO THUMB (prova empírica de modo) ==")
        print(f"  regiões: {res['regioes_analisadas']}")
        print(f"  insns decodificadas: Thumb {res['insns_decodificadas_thumb']:,} | ARM {res['insns_decodificadas_arm']:,}")
        print(f"  páginas THUMB plausível: {res['paginas_thumb_plausivel']} | ARM plausível: {res['paginas_arm_plausivel']} | total: {res['paginas_total']}")
        print(f"  BL diretos: {res['bl_encontrados']:,} | alvos únicos: {res['alvos_unicos']:,}")
        print(f"  prólogos dos alvos: {json.dumps(res['dist_prologos'], ensure_ascii=False)}")
        print(f"  dual-check manual×capstone: {chk['conferidos']} conferidos, {len(chk['divergencias'])} divergências")
        print("  top 8 mais chamadas:")
        for f_ in res["top_chamadas"][:8]:
            print(f"    {f_['endereco_hex']}  ×{f_['chamadas_bl_diretas']}  {f_['prologo_thumb']}")

        if args.update_functions:
            st = atualizar_functions_csv(args.update_functions, res["funcoes"],
                                         data, entry_thumb,
                                         script_dir.parent / "names_registry.json")
            print(f"\n  functions.csv: {st['linhas_auto']} linhas auto; "
                  f"{st['linhas_manuais_preservadas']} manuais preservadas; "
                  f"{st.get('nomes_registrados_aplicados', 0)} nomes do registry aplicados")

    logs = script_dir.parent / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "gba_disasm_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ferramenta": "gba_disasm.py", "versao": VERSAO,
            "rom_sha256": hashlib.sha256(data).hexdigest(),
            "cmd": args.cmd, "duracao_s": round(time.perf_counter() - t0, 3),
            "saidas": feitos}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
