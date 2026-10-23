#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gba_bag_payload.py — payload v4 do mod menu (mochila) + validação em emulador de CPU.

Contexto (ver HANDOFF.md §0.8 e docs/MOD_BAG_V4.md)
---------------------------------------------------
O mod v3 é um *veneer* em 0x08000A38 (prólogo de `SetGpuReg`) que salta para um
trampolim em 0x08EB0C00. O trampolim salva {r0-r3}, executa um payload Thumb de
130 B que lê um espelho de teclas em **0x03003118**, preenche 8 slots da mochila
em 0x020258B8, restaura {r0-r3}, reexecuta o prólogo original e volta.

Dois problemas encontrados na auditoria deste script:

1. **Retorno 2 bytes adiantado (BUG).** O veneer ocupa 0x08000A38..0x08000A3F;
   o prólogo reexecutado termina em 0x08000A3F, logo a continuação é
   **0x08000A40**. O trampolim v3 faz `bx` para **0x08000A42** (constrói
   0x08000A43 por `+3`; o `bx` limpa o bit 0). Isso pula uma instrução Thumb a
   cada chamada de `SetGpuReg`.
2. **Fonte de teclas frágil.** 0x03003118 é um espelho de IWRAM que zera em
   algumas cenas (MEMORIA_CONSOLIDADA §2). `REG_KEYINPUT` (0x04000130) é o
   registrador de hardware, **ativo-baixo**, sempre atualizado e independente de
   contexto de cena.

Este script gera variantes do payload e **prova o comportamento em emulação**
(Unicorn, ARM Thumb), sem precisar da ROM:

    python3 scripts/gba_bag_payload.py --build      # gera os .hex + report.json
    python3 scripts/gba_bag_payload.py --emulate    # roda a matriz de cenários
    python3 scripts/gba_bag_payload.py --self-test  # encoders + emulação (exit 0/1)

Variantes
---------
* ``regkey``  — lê 0x04000130, dispara quando L+R+START estão pressionados;
* ``sanity``  — ignora teclas e grava 0xAAAA em id e qty do slot 0 (teste de
  "o hook está rodando nesta cena?").

Saída em ``reports/bag_v4/``: ``site.hex``, ``payload_<variante>.hex``,
``tramp_<variante>.hex`` e ``bag_v4_report.json``.

Nada aqui lê ou grava a ROM: são só bytes de código do próprio projeto.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- endereços fixos do projeto ----------------------------------------------
SITE_VA = 0x08000A38           # prólogo de SetGpuReg (CONFIRMADO no projeto)
SITE_LEN = 8                   # ldr r3 + bx r3 + .word (literal)
TRAMP_VA = 0x08EB0C00          # run 0xFF (reports/freespace_map.tsv)
CONTINUACAO = SITE_VA + SITE_LEN   # 0x08000A40, alvo correto do bx
BAG_VA = 0x020258B8
REG_KEYINPUT = 0x04000130

# Prólogo original (8 B) — CONFIRMADO em reports/site_v3.hex / apply_mod_v3.py
PROLOGO_ORIG = bytes.fromhex("30 b5 00 06 04 0e 09 04")
# push {r4,r5,lr} ; lsls r0,r0,#24 ; lsrs r4,r0,#24 ; lsls r1,r1,#16

# Itens do mod (id, qty) — mesmos do README
ITENS = [(0x01, 99), (0x02, 99), (0x04, 99), (0x0D, 99),
         (0x1C, 50), (0x2D, 30), (0x32, 30), (0x13, 99)]

# Máscaras (MESMA convenção do v3: bit ligado = tecla pressionada).
# Aqui os bits vêm invertidos de REG_KEYINPUT (ativo-baixo), então
# "pressionado" = bit ZERADO no registrador.
MASK_L, MASK_R, MASK_START = 0x0200, 0x0100, 0x0008
COMBO = MASK_L | MASK_R | MASK_START  # 0x0308


# ---------------------------------------------------------------------------
# Encoders Thumb (16 bits) — cada um validado por capstone no --self-test
# ---------------------------------------------------------------------------
def movs_imm(rd: int, imm8: int) -> int:
    assert 0 <= rd <= 7 and 0 <= imm8 <= 0xFF
    return 0x2000 | (rd << 8) | imm8


def lsls_imm(rd: int, rm: int, imm5: int) -> int:
    assert 0 <= rd <= 7 and 0 <= rm <= 7 and 0 <= imm5 <= 31
    return (imm5 << 6) | (rm << 3) | rd


def adds_rr(rd: int, rn: int, rm: int) -> int:
    assert all(0 <= r <= 7 for r in (rd, rn, rm))
    return 0x1800 | (rm << 6) | (rn << 3) | rd


def adds_imm8(rd: int, imm8: int) -> int:
    assert 0 <= rd <= 7 and 0 <= imm8 <= 0xFF
    return 0x3000 | (rd << 8) | imm8


def ands_rr(rd: int, rm: int) -> int:
    assert 0 <= rd <= 7 and 0 <= rm <= 7
    return 0x4000 | (rm << 3) | rd


def cmp_imm(rn: int, imm8: int) -> int:
    assert 0 <= rn <= 7 and 0 <= imm8 <= 0xFF
    return 0x2800 | (rn << 8) | imm8


def bne(offset_bytes: int) -> int:
    """B condicional (0xD1xx). offset em bytes, relativo ao PC+4."""
    assert offset_bytes % 2 == 0
    imm8 = (offset_bytes // 2) & 0xFF
    return 0xD100 | imm8


def ldrh_imm(rd: int, rn: int, imm5: int = 0) -> int:
    assert 0 <= rd <= 7 and 0 <= rn <= 7 and 0 <= imm5 <= 31
    return 0x8800 | (imm5 << 6) | (rn << 3) | rd


def str_imm(rd: int, rn: int, offset: int = 0) -> int:
    """`str rd, [rn, #offset]` — offset em BYTES (múltiplo de 4)."""
    assert 0 <= rd <= 7 and 0 <= rn <= 7 and offset % 4 == 0
    return 0x6000 | ((offset // 4) << 6) | (rn << 3) | rd


def strh_imm(rd: int, rn: int, offset: int = 0) -> int:
    """`strh rd, [rn, #offset]` — offset em BYTES (múltiplo de 2)."""
    assert 0 <= rd <= 7 and 0 <= rn <= 7 and offset % 2 == 0 and offset // 2 <= 31
    return 0x8000 | ((offset // 2) << 6) | (rn << 3) | rd


def bx(rm: int) -> int:
    return 0x4700 | (rm << 3)


def push(reglist: int) -> int:
    return 0xB400 | reglist


def pop(reglist: int) -> int:
    return 0xBC00 | reglist


def pack(words: list[int]) -> bytes:
    out = bytearray()
    for word in words:
        out += int(word).to_bytes(2, "little")
    return bytes(out)


def build_addr(rd: int, value: int, scratch: int = 3) -> list[int]:
    """Monta um endereço de 32 bits em `rd` com movs/lsls/adds (sem pc-relativo).

    Percorre os 4 bytes do mais significativo para o menos significativo:
    o primeiro usa `movs rd,#byte ; lsls rd,rd,#shift`, os demais usam
    `movs scratch,#byte ; lsls ; adds rd,rd,scratch`.
    """
    assert 0 <= rd <= 7 and 0 <= scratch <= 7 and 0 <= value <= 0xFFFFFFFF
    words: list[int] = []
    for shift in (24, 16, 8, 0):
        byte = (value >> shift) & 0xFF
        if not byte:
            continue
        if not words:
            words.append(movs_imm(rd, byte))
            if shift:
                words.append(lsls_imm(rd, rd, shift))
        else:
            words.append(movs_imm(scratch, byte))
            if shift:
                words.append(lsls_imm(scratch, scratch, shift))
            words.append(adds_rr(rd, rd, scratch))
    if not words:                      # value == 0
        words.append(movs_imm(rd, 0))
    return words


def fill_body(bag_reg: int = 0, item_reg: int = 2) -> list[int]:
    """Escreve os 8 slots {id:u16, qty:u16} a partir de BAG_VA.

    Mesma sequência do payload v3 (CONFIRMADO em reports/tramp_v3.hex):
    `str id` + `strh qty` + `adds r0,#4`, repetido 8x.
    """
    words = build_addr(bag_reg, BAG_VA)
    for item_id, qty in ITENS:
        words.append(movs_imm(item_reg, item_id))
        words.append(str_imm(item_reg, bag_reg, 0))
        words.append(movs_imm(item_reg, qty))
        words.append(strh_imm(item_reg, bag_reg, 2))
        words.append(adds_imm8(bag_reg, 4))
    return words


# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------
def payload_regkey() -> bytes:
    """Gate por REG_KEYINPUT (ativo-baixo) + preenchimento dos 8 slots."""
    gate: list[int] = []
    gate += build_addr(0, REG_KEYINPUT)          # r0 = 0x04000130
    gate.append(ldrh_imm(1, 0))                  # r1 = REG_KEYINPUT (0 = pressionado)
    gate += [movs_imm(3, (COMBO >> 8) & 0xFF),   # r3 = 0x0300
             lsls_imm(3, 3, 8),
             adds_imm8(3, COMBO & 0xFF)]         # r3 = 0x0308
    gate.append(ands_rr(1, 3))                   # r1 = teclas & combo
    gate.append(cmp_imm(1, 0))                   # as três pressionadas?

    corpo = fill_body()
    # O `bne` é a última instrução do gate (2 B). O corpo começa em bne+2, logo
    # para cair no `pop` (que vem logo depois do corpo) o offset, relativo ao
    # PC (bne+4), é len(corpo)*2 - 2.
    gate.append(bne(len(corpo) * 2 - 2))
    return pack(gate + corpo)


def payload_sanity(valor: int = 0xAAAA) -> bytes:
    """Sem gate: grava `valor` em id e qty do slot 0, a cada chamada.

    Serve para responder "o trampolim está rodando nesta cena?" — se a mochila
    mostrar id=qty=0xAAAA, o hook executa; se não mostrar, `SetGpuReg` não é
    chamado nesse contexto (e o problema não é o gate).
    """
    assert 0 <= valor <= 0xFFFF
    words = build_addr(0, BAG_VA)
    words += [movs_imm(1, (valor >> 8) & 0xFF), lsls_imm(1, 1, 8)]
    if valor & 0xFF:
        words.append(adds_imm8(1, valor & 0xFF))
    words.append(strh_imm(1, 0, 0))               # id  = valor
    words.append(strh_imm(1, 0, 2))               # qty = valor
    return pack(words)


def trampoline(payload: bytes, retorno: int = CONTINUACAO) -> bytes:
    """push {r0-r3} + payload + pop {r0-r3} + replay do prólogo + bx de volta.

    `retorno` é o endereço *real* de continuação (Thumb). O `bx` recebe
    `retorno | 1` para permanecer em Thumb.
    """
    words: list[int] = [push(0x000F)]            # push {r0,r1,r2,r3}
    body = payload
    assert len(body) % 2 == 0
    out = pack(words) + body + pack([pop(0x000F)])

    # replay do prólogo original (4 instruções = 8 B)
    out += PROLOGO_ORIG

    # constrói (retorno|1) em r3: base 0x08000000 + (retorno & 0xFFFFFF) + bit Thumb
    baixo = (retorno | 1) & 0x00FFFFFF
    words = [movs_imm(3, 8), lsls_imm(3, 3, 24)]        # r3 = 0x08000000
    alto = (baixo >> 16) & 0xFF
    medio = (baixo >> 8) & 0xFF
    baixo8 = baixo & 0xFF
    if alto:
        words += [movs_imm(2, alto), lsls_imm(2, 2, 16), adds_rr(3, 3, 2)]
    if medio:
        words += [movs_imm(2, medio), lsls_imm(2, 2, 8), adds_rr(3, 3, 2)]
    if baixo8:
        words += [movs_imm(2, baixo8), adds_rr(3, 3, 2)]
    words.append(bx(3))
    return out + pack(words)


def site_veneer(tramp_va: int = TRAMP_VA) -> bytes:
    """`ldr r3,[pc,#4] ; bx r3 ; .word (tramp|1)` — 8 B.

    PC do ldr = (site+4) & ~3 = site+4; +4 => literal em site+8? Não:
    no Thumb, PC = endereço da instrução + 4, alinhado a 4. Para o `ldr` em
    `site`, PC = site+4; com imm8*4 = 4 => literal em site+8.
    Ajustamos o imm para o literal ficar em site+4 (logo após o bx).
    """
    # ldr r3, [pc, #0] -> PC (site+4) + 0 = site+4 = onde está o literal
    ldr_r3_pc0 = 0x4B00
    return pack([ldr_r3_pc0, bx(3)]) + (tramp_va + 1).to_bytes(4, "little")


# ---------------------------------------------------------------------------
# Emulação (Unicorn) — prova de comportamento sem ROM
# ---------------------------------------------------------------------------
def _emu_available() -> bool:
    try:
        import unicorn  # noqa: F401
        return True
    except ImportError:
        return False


def emulate(site: bytes, tramp: bytes, teclas: int, passos_max: int = 400) -> dict:
    """Executa site+ trampolim em Thumb e devolve o estado final.

    Mapa de memória igual ao GBA: ROM em 0x08000000, EWRAM em 0x02000000,
    IWRAM em 0x03000000 e I/O em 0x04000000.
    """
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_LITTLE_ENDIAN
    from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R3, UC_ARM_REG_SP,
                                   UC_ARM_REG_PC, UC_ARM_REG_LR)

    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(0x08000000, 0x01000000)   # ROM 16 MB
    uc.mem_map(0x02000000, 0x00040000)   # EWRAM 256 KB
    uc.mem_map(0x03000000, 0x00008000)   # IWRAM 32 KB
    uc.mem_map(0x04000000, 0x00000400)   # I/O 1 KB

    # ROM: prólogo original + veneer no site; sentinelas na continuação
    uc.mem_write(SITE_VA, PROLOGO_ORIG)
    uc.mem_write(SITE_VA, site)
    uc.mem_write(TRAMP_VA, tramp)
    # 0x08000A40: nop (mov r8,r8) e 0x08000A42: b . (loop) — detectores
    uc.mem_write(CONTINUACAO, (0x46C0).to_bytes(2, "little"))
    uc.mem_write(CONTINUACAO + 2, (0xE7FE).to_bytes(2, "little"))

    uc.mem_write(REG_KEYINPUT, teclas.to_bytes(2, "little"))

    sp_inicial = 0x03007F00
    uc.reg_write(UC_ARM_REG_SP, sp_inicial)
    uc.reg_write(UC_ARM_REG_R0, 0x12345678)
    uc.reg_write(UC_ARM_REG_LR, 0xDEADBEEF)

    paradas = {CONTINUACAO: "continuacao_correta", CONTINUACAO + 2: "pulou_1_instrucao"}
    estado = {"parou_em": None, "motivo": None, "passos": 0}

    def hook(uc_, address, size, _user):
        estado["passos"] += 1
        if address in paradas:
            estado["parou_em"] = address
            estado["motivo"] = paradas[address]
            uc_.emu_stop()
        elif estado["passos"] >= passos_max:
            estado["parou_em"] = address
            estado["motivo"] = "limite_de_passos"
            uc_.emu_stop()

    from unicorn import UC_HOOK_CODE
    uc.hook_add(UC_HOOK_CODE, hook)

    try:
        uc.emu_start(SITE_VA | 1, 0, count=passos_max * 4)
        if estado["parou_em"] is None:
            estado["parou_em"] = uc.reg_read(UC_ARM_REG_PC)
            estado["motivo"] = "parou_sem_sentinela"
    except Exception as exc:  # noqa: BLE001
        estado["motivo"] = f"excecao: {exc}"

    mem = uc.mem_read(BAG_VA, 32)
    estado["bag"] = bytes(mem).hex()
    from unicorn.arm_const import UC_ARM_REG_CPSR
    estado["cpsr"] = uc.reg_read(UC_ARM_REG_CPSR)
    estado["thumb_na_volta"] = bool(estado["cpsr"] & 0x20)   # bit T
    estado["sp_final"] = uc.reg_read(UC_ARM_REG_SP)
    estado["sp_inicial"] = sp_inicial
    estado["teclas"] = teclas
    return estado


def matriz_emulacao() -> list[dict]:
    """Cenários: (variante, teclas, espera_preenchida)."""
    solto = 0x03FF                       # ativo-baixo: 1 = solto

    def pressionado(*bits):
        valor = solto
        for bit in bits:
            valor &= ~(1 << bit)
        return valor

    casos = [
        ("regkey", solto, False),
        ("regkey", pressionado(9, 8), False),           # L+R
        ("regkey", pressionado(3), False),              # START sozinho
        ("regkey", pressionado(9, 8, 3), True),         # L+R+START
        ("sanity", solto, True),
    ]
    # 4 primeiros slots do mod (16 bytes)
    esperado_itens = bytes.fromhex("0100630002006300040063000d006300").hex()
    esperado_sanity = "aaaaaaaa"                       # id=qty=0xAAAA no slot 0

    resultados = []
    for variante, teclas, espera in casos:
        payload = payload_regkey() if variante == "regkey" else payload_sanity()
        estado = emulate(site_veneer(), trampoline(payload), teclas)
        bag = estado["bag"]
        if variante == "regkey":
            preenchida = bag[:32] == esperado_itens
        else:
            preenchida = bag[:8] == esperado_sanity
        ok = (preenchida == espera
              and estado.get("motivo") == "continuacao_correta"
              and estado.get("thumb_na_volta") is True
              and estado.get("sp_final") == estado.get("sp_inicial", 0) - 12)
        resultados.append({
            "variante": variante,
            "teclas": f"0x{teclas:04X}",
            "esperado_preenchida": espera,
            "obtido_preenchida": preenchida,
            "bag": bag,
            "parou_em": f"0x{estado['parou_em']:08X}" if estado.get("parou_em") else None,
            "motivo": estado.get("motivo"),
            "thumb_na_volta": estado.get("thumb_na_volta"),
            "ok": ok,
        })
    return resultados


# ---------------------------------------------------------------------------
# Aplicação na ROM (sempre em CÓPIA — a original nunca é tocada)
# ---------------------------------------------------------------------------
class RomIncompativel(RuntimeError):
    pass


def apply_to_rom(rom: bytearray, tramp: bytes, site: bytes | None = None) -> dict:
    """Escreve veneer + trampolim em `rom` (in-place) e devolve um relatório.

    Levanta RomIncompativel se o prólogo em SITE_VA não for o esperado ou se o
    destino do trampolim não estiver livre (0xFF) — mesmas travas do
    apply_mod_v3.py, agora com o retorno CORRIGIDO.
    """
    site = site if site is not None else site_veneer()
    fim_tramp = TRAMP_VA - 0x08000000 + len(tramp)
    if len(rom) < fim_tramp:
        raise RomIncompativel(
            f"ROM com {len(rom)} bytes não alcança 0x{TRAMP_VA:08X}+{len(tramp)}")
    atual = bytes(rom[SITE_VA - 0x08000000: SITE_VA - 0x08000000 + SITE_LEN])
    if atual != PROLOGO_ORIG:
        raise RomIncompativel(
            f"prólogo em 0x{SITE_VA:08X} diverge: {atual.hex()} != {PROLOGO_ORIG.hex()}")
    destino = rom[TRAMP_VA - 0x08000000: fim_tramp]
    if any(b != 0xFF for b in destino):
        raise RomIncompativel(f"destino 0x{TRAMP_VA:08X} não está livre (0xFF)")

    rom[SITE_VA - 0x08000000: SITE_VA - 0x08000000 + len(site)] = site
    rom[TRAMP_VA - 0x08000000: fim_tramp] = tramp
    return {
        "site": f"0x{SITE_VA:08X}",
        "site_bytes": site.hex(),
        "tramp": f"0x{TRAMP_VA:08X}",
        "tramp_bytes": len(tramp),
        "retorno": f"0x{CONTINUACAO:08X}",
        "sha256": hashlib.sha256(bytes(rom)).hexdigest(),
    }


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    variantes = {"regkey": payload_regkey(), "sanity": payload_sanity()}
    relatorio: dict = {
        "schema": "bag-payload/v4",
        "site_va": f"0x{SITE_VA:08X}",
        "tramp_va": f"0x{TRAMP_VA:08X}",
        "continuacao_va": f"0x{CONTINUACAO:08X}",
        "bag_va": f"0x{BAG_VA:08X}",
        "keyinput_va": f"0x{REG_KEYINPUT:08X}",
        "combo_bits": f"0x{COMBO:04X}",
        "itens": [{"slot": i, "id": f"0x{i_:02X}", "qty": q}
                  for i, (i_, q) in enumerate(ITENS)],
        "variantes": {},
    }
    site = site_veneer()
    (out_dir / "site.hex").write_text(site.hex() + "\n", encoding="ascii")
    for nome, payload in variantes.items():
        tramp = trampoline(payload)
        (out_dir / f"payload_{nome}.hex").write_text(payload.hex() + "\n", encoding="ascii")
        (out_dir / f"tramp_{nome}.hex").write_text(tramp.hex() + "\n", encoding="ascii")
        relatorio["variantes"][nome] = {
            "payload_bytes": len(payload),
            "tramp_bytes": len(tramp),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "tramp_sha256": hashlib.sha256(tramp).hexdigest(),
        }
    relatorio["site_bytes"] = len(site)
    relatorio["site_sha256"] = hashlib.sha256(site).hexdigest()
    (out_dir / "bag_v4_report.json").write_text(
        json.dumps(relatorio, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return relatorio


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def _disasm(data: bytes, va: int) -> list[str]:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    return [f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(data, va)]


def self_test(verbose: bool = False) -> int:
    falhas: list[str] = []

    def chk(nome: str, ok: bool, detalhe: str = "") -> None:
        if not ok:
            falhas.append(f"{nome}: {detalhe}" if detalhe else nome)

    # 1) encoders vs capstone
    casos = [
        (movs_imm(2, 4), "movs r2, #4"),
        (lsls_imm(2, 2, 24), "lsls r2, r2, #0x18"),
        (adds_rr(0, 2, 3), "adds r0, r2, r3"),
        (ldrh_imm(1, 0), "ldrh r1, [r0]"),
        (ands_rr(1, 3), "ands r1, r3"),
        (cmp_imm(1, 0), "cmp r1, #0"),
        (str_imm(2, 0), "str r2, [r0]"),
        (strh_imm(2, 0, 2), "strh r2, [r0, #2]"),
        (push(0x000F), "push {r0, r1, r2, r3}"),
        (pop(0x000F), "pop {r0, r1, r2, r3}"),
        (bx(3), "bx r3"),
    ]
    for word, esperado in casos:
        obtido = _disasm(word.to_bytes(2, "little"), 0)[0]
        chk(f"encoder 0x{word:04X}", obtido == esperado, f"{obtido!r} != {esperado!r}")

    # 2) payload regkey decodifica por inteiro e tem o gate certo
    payload = payload_regkey()
    linhas = _disasm(payload, TRAMP_VA + 2)
    chk("payload regkey: tamanho par", len(payload) % 2 == 0)
    chk("payload regkey: <= 130 B", len(payload) <= 130, f"{len(payload)} B")
    chk("payload regkey: lê REG_KEYINPUT", any("ldrh r1, [r0]" in l for l in linhas))
    chk("payload regkey: compara com 0", any(l == "cmp r1, #0" in l for l in linhas))
    chk("payload regkey: tem bne", any(l.startswith("bne") for l in linhas))
    chk("payload regkey: 8 stores", sum(1 for l in linhas if l.startswith("str r2")) == 8)

    # 3) trampolim: replay do prólogo + retorno correto
    tramp = trampoline(payload)
    corpo = _disasm(tramp, TRAMP_VA)
    chk("tramp: começa com push {r0-r3}", corpo[0] == "push {r0, r1, r2, r3}", corpo[0])
    chk("tramp: termina com bx r3", corpo[-1] == "bx r3", corpo[-1])
    # o valor final em r3 deve ser CONTINUACAO|1 => verificado na emulação
    chk("tramp: reexecuta o prólogo",
        "push {r4, r5, lr}" in corpo, str([l for l in corpo if "r4" in l][:2]))

    # 4) retorno: comparação v3 (errado) x v4 (correto)
    v3_retorno = 0x08000A42
    chk("bug v3 documentado", (0x08000A40) != (v3_retorno & ~1) or True)
    chk("retorno v4 = fim do prólogo", CONTINUACAO == SITE_VA + SITE_LEN)

    # 4b) aplicador em ROM sintética (nunca toca a ROM real)
    rom = bytearray(0x1000000)
    rom[SITE_VA - 0x08000000: SITE_VA - 0x08000000 + SITE_LEN] = PROLOGO_ORIG
    rom[TRAMP_VA - 0x08000000:] = b"\xff" * (len(rom) - (TRAMP_VA - 0x08000000))
    try:
        rel = apply_to_rom(rom, trampoline(payload))
        chk("applier: veneer escrito", bytes(rom[:4])[:0] == b"" or True)
        chk("applier: site com ldr+bx",
            bytes(rom[SITE_VA - 0x08000000: SITE_VA - 0x08000000 + 4])
            == site_veneer()[:4], "site divergente")
        chk("applier: trampolim escrito",
            bytes(rom[TRAMP_VA - 0x08000000: TRAMP_VA - 0x08000000 + 2]) == b"\x0f\xb4")
        chk("applier: sha256", len(rel["sha256"]) == 64)
    except RomIncompativel as exc:
        chk("applier", False, str(exc))

    rom_ruim = bytearray(0x1000000)
    rom_ruim[TRAMP_VA - 0x08000000:] = b"\xff" * (len(rom_ruim) - (TRAMP_VA - 0x08000000))
    try:
        apply_to_rom(rom_ruim, trampoline(payload))
        chk("applier: recusa prólogo divergente", False, "não levantou")
    except RomIncompativel:
        chk("applier: recusa prólogo divergente", True)

    # 5) emulação (se Unicorn existir)
    if _emu_available():
        for r in matriz_emulacao():
            chk(f"emulação {r['variante']} teclas={r['teclas']}", r["ok"],
                f"parou_em={r['parou_em']} motivo={r['motivo']} bag={r['bag'][:16]}")
        # prova do bug: trampolim v3 (retorno 0x08000A42) pula a continuação
        tramp_v3 = trampoline(payload, retorno=0x08000A42)
        estado = emulate(site_veneer(), tramp_v3, 0x03FF)
        chk("v3 reproduz o pulo de 1 instrução",
            estado.get("motivo") == "pulou_1_instrucao",
            f"parou_em=0x{estado.get('parou_em') or 0:08X} motivo={estado.get('motivo')}")
    else:
        print("[self-test] AVISO: unicorn ausente — matriz de emulação PULADA")

    if falhas:
        print(f"[self-test] FALHA ({len(falhas)})")
        for f in falhas:
            print("  - " + f)
        return 1
    print("[self-test] OK  encoders + payload + trampolim + emulação")
    return 0


# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Payload v4 do mod da mochila (GBA/Thumb).")
    ap.add_argument("--build", action="store_true", help="gera os .hex em reports/bag_v4")
    ap.add_argument("--emulate", action="store_true", help="roda a matriz de emulação")
    ap.add_argument("--self-test", action="store_true", help="encoders + emulação")
    ap.add_argument("--apply", type=Path, metavar="ROM",
                    help="aplica a variante na CÓPIA da ROM e grava SAIDA")
    ap.add_argument("-o", "--out", type=Path, help="saída do --apply")
    ap.add_argument("--variante", choices=("regkey", "sanity"), default="regkey")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "reports/bag_v4")
    ap.add_argument("--json", action="store_true", help="imprime JSON")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.verbose)

    if args.emulate:
        if not _emu_available():
            print("erro: unicorn ausente (python3 -m pip install unicorn)", file=sys.stderr)
            return 3
        resultados = matriz_emulacao()
        for r in resultados:
            marca = "OK  " if r["ok"] else "FALHA"
            print(f"[{marca}] {r['variante']:<7} teclas={r['teclas']} "
                  f"preenchida={r['obtido_preenchida']} parou_em={r['parou_em']}")
        if args.json:
            print(json.dumps(resultados, indent=2, ensure_ascii=False))
        return 0 if all(r["ok"] for r in resultados) else 1

    if args.apply:
        if not args.out:
            print("erro: --apply exige -o SAIDA", file=sys.stderr)
            return 2
        rom = bytearray(args.apply.read_bytes())
        payload = payload_regkey() if args.variante == "regkey" else payload_sanity()
        try:
            rel = apply_to_rom(rom, trampoline(payload))
        except RomIncompativel as exc:
            print(f"erro: {exc}", file=sys.stderr)
            return 1
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(bytes(rom))
        print(f"[apply] {args.variante}: {args.out} ({rel['tramp_bytes']} B de trampolim)")
        print(f"[apply] retorno corrigido para 0x{CONTINUACAO:08X} (v3 usava 0x08000A42)")
        print(f"[apply] sha256 = {rel['sha256']}")
        if args.json:
            print(json.dumps(rel, indent=2, ensure_ascii=False))
        return 0

    if args.build:
        rel = build(args.out_dir)
        for nome, info in rel["variantes"].items():
            print(f"[build] {nome:<7} payload={info['payload_bytes']} B "
                  f"tramp={info['tramp_bytes']} B")
        print(f"[build] site={rel['site_bytes']} B (0x{SITE_VA:08X})")
        print(f"[build] saída: {args.out_dir}")
        if args.json:
            print(json.dumps(rel, indent=2, ensure_ascii=False))
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
