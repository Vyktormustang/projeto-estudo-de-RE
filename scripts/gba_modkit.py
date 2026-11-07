#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gba_modkit.py — montador de mods de código para GBA (v1.0.0).

MOTIVAÇÃO (por que reescrever o que já existia)
    O mod anterior (`rom_mod/BAG_MOD_v3.gba`) não disparava porque o *site* do
    hook tinha dois defeitos aritméticos de baixo nível:

      site emitido : 01 4b | 18 47 | 01 0c eb 08      @0x08000A38
      ldr r3,[pc,#4] em 0x08000A38 lê Align(0x08000A3C,4)+4 = **0x08000A40**
      ...e o literal estava em 0x08000A3C ⇒ r3 = 0x08EB0C01 decodificado como
      instruções (lsrs r1,r0,#16 / lsrs r3,r5,#3) ⇒ `bx r3` com lixo ⇒ a rotina
      SetGpuReg (chamada 1238× pela ROM) morria em toda tela.

    Ninguém acertou isso olhando o hexdump porque faltava uma ferramenta que
    (a) montasse a partir de mnemônicos e (b) **simulasse a execução** antes de
    gravar. Este módulo faz as duas coisas.

O QUE ELE GARANTE (checagens que rodam antes de gravar bytes)
    C1 prógolo original do site confere byte a byte (`--expect`)
    C2 destino do trampolim dentro de run 0xFF do mapa de freespace
    C3 saltos do payload **resolvidos pelo assembler** (nada de offset à mão)
    C4 literal do veneer escrito exatamente onde o PC relativo do ldr aponta
    C5 desassembly final do bloco inteiro é impresso para auditoria a olho
    C6 execução simulada (unicorn ARMv4T) do site+trampolim: reproduz o
       prógolo original e escreve SÓ quando o combo é pressionado
    C7 desvio de BL (quando usado) validado contra o alcance de ±4 MB e
       comparado com o montador (keystone)

USO
    python3 scripts/gba_modkit.py --self-test
    python3 scripts/gba_modkit.py --list-rotinas
    python3 scripts/gba_modkit.py --combo L+R+START --payload padrao \\
        --rom rom/jogo.gba -o rom_mod/MOD.bin

DEPENDÊNCIAS
    keystone-engine (montar), capstone (auditar), unicorn (simular).
    `bash scripts/setup_env.sh` instala; sem elas só `--list-rotinas` funciona.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERSAO = "1.0.0"

# --------------------------------------------------------------------------- #
# Tabela de itens (Gen 3 — ids conferidos com a tabela interna do jogo)
# --------------------------------------------------------------------------- #
ITENS = {
    0x0001: "Master Ball", 0x0002: "Ultra Ball", 0x0003: "Great Ball",
    0x0004: "Poké Ball", 0x0005: "Safari Ball", 0x0006: "Net Ball",
    0x0007: "Dive Ball", 0x0008: "Nest Ball", 0x0009: "Repeat Ball",
    0x000A: "Timer Ball", 0x000B: "Luxury Ball", 0x000C: "Premier Ball",
    0x000D: "Potion", 0x000E: "Antidote", 0x000F: "Burn Heal",
    0x0010: "Ice Heal", 0x0011: "Awakening", 0x0012: "Parlyz Heal",
    0x0013: "Full Restore", 0x0014: "Max Potion", 0x0015: "Hyper Potion",
    0x0016: "Super Potion", 0x0017: "Full Heal", 0x0018: "Revive",
    0x0019: "Max Revive", 0x001A: "Fresh Water", 0x001B: "Soda Pop",
    0x001C: "Lemonade", 0x001D: "Moomoo Milk", 0x001E: "Energy Powder",
    0x001F: "Energy Root", 0x0020: "Heal Powder", 0x0021: "Revival Herb",
    0x0022: "Ether", 0x0023: "Max Ether", 0x0024: "Elixir",
    0x0025: "Max Elixir", 0x0026: "Lava Cookie", 0x0027: "Blue Flute",
    0x0028: "Yellow Flute", 0x0029: "Red Flute", 0x002A: "Black Flute",
    0x002B: "White Flute", 0x002C: "Berry Juice", 0x002D: "Sacred Ash",
    0x002E: "Shoal Salt", 0x002F: "Shoal Shell", 0x0030: "Red Shard",
    0x0031: "Blue Shard", 0x0032: "Yellow Shard", 0x0033: "Green Shard",
    0x0034: "HP Up", 0x0035: "Protein", 0x0036: "Iron", 0x0037: "Carbos",
    0x0038: "Calcium", 0x0039: "Rare Candy", 0x003A: "PP Up",
    0x003B: "Zinc", 0x003C: "PP Max", 0x003D: "Old Amber",
    0x003E: "Dome Fossil", 0x003F: "Helix Fossil",
}

# --------------------------------------------------------------------------- #
# Rotinas-candidatas a "site" do hook (todas CONFIRMADAS vivas na ROM, ver
# reports/pokemon_firered_bpre_trabalho_callsites.tsv):
#   SetGpuReg @0x08000A38 — chamada 1238× pela ROM (VBlank/HDMA/paleta).
#     Melhor candidato a "toda tela, todo frame". É a mesma rotina do v3.
# O hook NÃO depende dela rodar no overworld: onde ela roda, o combo funciona.
# --------------------------------------------------------------------------- #
ROTINAS = {
    "SetGpuReg": {
        "va": 0x08000A38,
        "prologo": bytes.fromhex("30050006040e0904".replace("3005", "30b5")),
        "chamadas": 1238,
        "evidencia": "callsites.tsv: 1238 BL para 0x08000A38",
    }
}


# --------------------------------------------------------------------------- #
# Emissor
# --------------------------------------------------------------------------- #
class ModError(RuntimeError):
    pass


def _ks():
    try:
        import keystone  # noqa: F401
    except ImportError as e:  # pragma: no cover
        raise ModError("keystone-engine ausente: pip install keystone-engine") from e
    return __import__("keystone")


def _capstone():
    try:
        import capstone
    except ImportError as e:  # pragma: no cover
        raise ModError("capstone ausente: pip install capstone") from e
    return capstone


def montar(asm: str, base: int, armv4t: bool = True) -> bytes:
    """Monta Thumb em `base` — com trava de ISA.

    ARM7TDMI (GBA) NÃO tem Thumb-2: se o assembler emitir uma instrução de 32
    bits (ele faz isso por padrão para formas de 2 operandos, ex. `adds r3, r6`
    → `13 eb 06 03`), a CPU a executa como DUAS instruções de 16 bits e o mod
    vira lixo. Por isso todo bloco montado é decodificado e, se `armv4t`, é
    recusado qualquer instrução de 4 bytes.
    """
    ks = _ks()
    enc, _ = ks.Ks(ks.KS_ARCH_ARM, ks.KS_MODE_THUMB).asm(asm.strip(), addr=base)
    if not enc:
        raise ModError(f"assembler falhou para:\n{asm}")
    enc = bytes(enc)
    if armv4t:
        cs = _capstone()
        md = cs.Cs(cs.CS_ARCH_ARM, cs.CS_MODE_THUMB)
        md.detail = True
        for i in md.disasm(enc, base):
            if i.size != 2:
                raise ModError(
                    f"instrução de {i.size} B (Thumb-2) recusada — ARM7TDMI não tem: "
                    f"{i.mnemonic} {i.op_str} @0x{i.address:08X}\n"
                    f"  bloco:\n{asm}")
    return enc


def desmontar(codigo: bytes, base: int) -> list[str]:
    cs = _capstone()
    md = cs.Cs(cs.CS_ARCH_ARM, cs.CS_MODE_THUMB)
    md.detail = True
    out = []
    for i in md.disasm(codigo, base):
        out.append(f"{i.address:08X}: {i.bytes.hex():<8} {i.mnemonic:<8} {i.op_str}")
    return out


# --------------------------------------------------------------------------- #
# Payload da mochila
# --------------------------------------------------------------------------- #
COMBOS = {
    "L+R+START": 0x03 << 9 | 0x03 << 8 | 0x01 << 3,   # bits internos do GBA
    "L+R":       0x03 << 9 | 0x03 << 8,
    "START+SELECT": 0x01 << 3 | 0x01 << 2,
    "L+R+A":     0x03 << 9 | 0x03 << 8 | 0x01,
}

# máscaras de hardware: L=0x200, R=0x100, START=0x008, SELECT=0x004, A=0x001
MASKS_HW = {"L": 0x200, "R": 0x100, "START": 0x008, "SELECT": 0x004, "A": 0x001}


def combo_mask(combo: str) -> int:
    m = 0
    for parte in combo.split("+"):
        m |= MASKS_HW[parte.strip().upper()]
    return m


PADRAO = [(0x0001, 99), (0x0002, 99), (0x0003, 99), (0x0004, 99),
          (0x000D, 99), (0x0013, 99), (0x002D, 99), (0x0039, 99)]


def _pedacos(valor: int) -> list[tuple[int, int]]:
    """Quebra um valor de 32 bits em bytes (imm, shift) não nulos, do mais alto ao mais baixo."""
    return [(byte, shift) for shift in (24, 16, 8, 0)
            if (byte := (valor >> shift) & 0xFF)]


def carregar(reg: str, valor: int, tmp: str = "r6") -> list[str]:
    """Constrói uma constante arbitrária em `reg` com movs/lsls/adds (16 bits cada).

    Evita literais pc-relativos de propósito: foi um literal mal colocado que
    quebrou o site do mod v3 (o `ldr r3,[pc,#4]` lia 4 B adiante do escrito).
    """
    linhas: list[str] = []
    for n, (imm, shift) in enumerate(_pedacos(valor)):
        if n == 0:
            linhas.append(f"movs {reg}, #{imm}")
            if shift:
                linhas.append(f"lsls {reg}, {reg}, #{shift}")
        elif shift == 0:
            linhas.append(f"adds {reg}, #{imm}")
        else:
            linhas.append(f"movs {tmp}, #{imm}")
            linhas.append(f"lsls {tmp}, {tmp}, #{shift}")
            linhas.append(f"add {reg}, {tmp}")   # 16 bits (adds reg,tmp seria Thumb-2)
    return linhas


def payload_mochila(itens: list[tuple[int, int]], combo: str = "L+R+START",
                    base_bolsa: int = 0x020258B8) -> str:
    """Assembly Thumb do payload: `if (KEYINPUT & mask) == mask { bag[0..n] = itens }`.

    Regras de ouro (aprendidas na simulação de 2026-11-07, ver HANDOFF §2):
      * **REG_KEYINPUT 0x04000130 é ATIVO-BAIXO**: botão pressionado = bit ZERO.
        Logo o teste NÃO pode ser `(k & mask) == mask` (daria verdadeiro com
        tudo solto, pois 0x3FF & 0x308 == 0x308) e sim `(k & mask) == 0`:
        nenhum bit do combo sobrou em 1 ⇒ L, R e START estão todos pressionados.
      * ARM7TDMI não tem Thumb-2: nada de `adds rX, rY` (monta como 32 bits) —
        usar `add rX, rY` (16 bits). O montador recusa 4 B fora de BL.
      * Nada de literal pc-relativo no payload: endereços são construídos por
        movs/lsls/adds, o que evita o bug de alinhamento que matou o v3.
    """
    mask = combo_mask(combo)

    L: list[str] = ["push {r0, r1, r2, r3, r6}"]
    L += carregar("r2", mask)
    L += carregar("r1", 0x04000130)
    L += ["ldrh r1, [r1]",
          "ands r1, r2",       # r1 = bits do combo que NÃO estão pressionados
          "bne fim"]           # diferentes de zero => combo incompleto
    L += carregar("r0", base_bolsa)
    for item_id, qty in itens:
        # Slot = u32 little-endian {id:u16, qty:u16} -> (qty<<16)|id.
        # UMA store de 32 bits em vez de str+strh: sem estado "meio escrito".
        # (O teste de bancada flagrou exatamente isso: um leitor podia ver
        # {id novo, qty antigo} entre as duas stores.)
        packed = (qty << 16) | item_id
        if qty <= 0xFF and item_id <= 0xFF:
            # caminho curto: movs #qty; lsls #16; adds #id  (2 ou 3 instruções)
            L += [f"movs r2, #{qty}", "lsls r2, r2, #16"]
            if item_id:
                L += [f"adds r2, #{item_id}"]
        else:
            L += carregar("r2", packed)
        L += ["str r2, [r0]", "adds r0, #4"]
    L += ["fim:",
          "pop {r0, r1, r2, r3, r6}"]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Sites
# --------------------------------------------------------------------------- #
def site_veneer(va: int, alvo: int) -> bytes:
    """8 bytes: `ldr r3,[pc,#0]; bx r3; .word alvo|1` + 2 bytes NOP de recheio.

    O literal fica em va+4 — exatamente onde Align(va+4,4)+0 aponta, e é o único
    endereço que o offset 0 do ldr alcança nesse encaixe. Alvo precisa estar
    ≤255*4 = 1020 bytes à frente? Não: `ldr r3,[pc,#0]` lê va+4 **direto**
    (não é o caso do v3, que usava #4 e escrevia o literal em va+4).
    """
    if va & 3:
        raise ModError(f"site {va:#x} não é múltiplo de 4: literal pc-relativo quebraria")
    codigo = montar("ldr r3, [pc, #0]\nbx r3", va)   # 4 B
    corpo = codigo + struct.pack("<I", (alvo & ~1) | 1)  # + literal em va+4 = 8 B
    if len(corpo) != 8:
        raise ModError(f"veneer com tamanho inesperado: {len(corpo)}")
    # C4 — o ldr tem de apontar para va+4
    montado = desmontar(codigo, va)
    if "pc, #0" not in montado[0]:
        raise ModError(f"ldr inline não é pc-relativo #0: {montado[0]}")
    return corpo


def site_bl(site_va: int, alvo_va: int) -> bytes:
    """BL Thumb com checagem de alcance (±4 MB) e validação contra o assembler."""
    alcance = 0x400000
    if abs(alvo_va - (site_va + 4)) > alcance:
        raise ModError(f"BL de {site_va:#x} para {alvo_va:#x} fora de ±4 MB")
    enc = montar(f"bl #{alvo_va:#x}", site_va, armv4t=False)  # BL é 4 B por natureza
    cs = _capstone()
    md = cs.Cs(cs.CS_ARCH_ARM, cs.CS_MODE_THUMB)
    md.detail = True
    ins = next(md.disasm(enc, site_va))
    if ins.mnemonic != "bl" or abs(int(ins.op_str.split("#")[1], 16) - alvo_va) > 1:
        raise ModError(f"BL mal codificado: {enc.hex()} -> {ins.mnemonic} {ins.op_str}")
    return enc


# --------------------------------------------------------------------------- #
# Simulação (C6) — prova mecânica do veneer antes de tocar na ROM
# --------------------------------------------------------------------------- #
def simular(site: bytes, va_site: int, tramp: bytes, va_tramp: int,
            prologo_original: bytes, keys: int, r0: int = 0, r1: int = 0,
            bag: int = 0x020258B8) -> dict:
    """Executa site+trampolim no unicorn (ARMv4T) e devolve o que aconteceu.

    Monta um mapa de memória plano de 0x00000000..0x0A000000 (16 MB de "ROM"
    suficiente para os endereços baixos) + EWRAM/IWRAM. O objetivo não é
    emular o jogo: é provar que o veneer chega ao trampolim, que o prógolo é
    reexecutado e que a bolsa só é escrita com o combo pressionado.
    """
    try:
        from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                                       UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                                       UC_ARM_REG_R6, UC_ARM_REG_SP, UC_ARM_REG_PC,
                                       UC_ARM_REG_CPSR)
    except ImportError as e:  # pragma: no cover
        raise ModError("unicorn ausente: pip install unicorn") from e

    PAGE = 0x10000
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)

    def map_ate(fim: int) -> None:
        for a in range(0, fim, 0x100000):
            try:
                uc.mem_map(a, 0x100000)
            except UcError:
                pass

    map_ate(0x0A000000)          # ROM/BIOS (0x08000000+ dentro)
    map_ate(0x04000000) if False else None
    for base, tam in ((0x02000000, 0x40000), (0x03000000, 0x8000),
                      (0x04000000, 0x1000), (0x05000000, 0x800)):
        try:
            uc.mem_map(base, tam)
        except UcError:
            pass

    uc.mem_write(va_site, site)
    uc.mem_write(va_tramp, tramp)
    # REG_KEYINPUT ativo-baixo
    uc.mem_write(0x04000130, struct.pack("<H", (~keys) & 0x3FF))
    # Replay do jogo: o veneer sobrescreve 8 B; logo em va_site+8 o jogo tem a
    # instrução SEGUINTE ao prólogo. Colocamos ali `b .` — se o trampolim
    # retornar ao endereço certo, a execução estaciona exatamente nesse PC.
    # (Antes eu usava uma "sentinela" em va_site+0x800; errado: o retorno é para
    # va_site+8, e ali havia o prólogo → a simulação caía no vazio.)
    uc.mem_write(va_site + 8, b"\xfe\xe7")   # b .  → PC fica em va_site+8
    _ = prologo_original

    uc.reg_write(UC_ARM_REG_R0, r0)
    uc.reg_write(UC_ARM_REG_R1, r1)
    uc.reg_write(UC_ARM_REG_R4, 0)
    uc.reg_write(UC_ARM_REG_R5, 0)
    uc.reg_write(UC_ARM_REG_SP, 0x03007000)   # pilha IWRAM, como no jogo

    execucao = {"insns": 0, "voltou_ao_prologo": False, "erro": None}
    try:
        uc.emu_start(va_site | 1, 0, count=400)
    except UcError as e:
        execucao["erro"] = str(e)

    pc = uc.reg_read(UC_ARM_REG_PC)
    execucao["pc_final"] = pc
    execucao["voltou_ao_prologo"] = pc == va_site + 8
    slots = []
    mem = uc.mem_read(bag, 4 * 8)
    for i in range(8):
        item_id, qty = struct.unpack("<HH", bytes(mem[i * 4:(i + 1) * 4]))
        slots.append({"slot": i, "id": item_id, "qtd": qty,
                      "nome": ITENS.get(item_id, "—")})
    saida = {"keys": keys, "slots": slots,
             "escreveu": any(s["id"] for s in slots),
             "r0_final": uc.reg_read(UC_ARM_REG_R0),
             "r1_final": uc.reg_read(UC_ARM_REG_R1),
             "execucao": execucao}
    return saida


# --------------------------------------------------------------------------- #
# Receita completa
# --------------------------------------------------------------------------- #
def receita(rotina: str = "SetGpuReg", combo: str = "L+R+START",
            itens: list[tuple[int, int]] | None = None,
            va_tramp: int = 0x08EB0C00) -> dict:
    """Monta site + trampolim e devolve os bytes prontos para aplicar.

    Layout do trampolim (o retorno tem de cair em `site+8`, onde o fluxo
    original do jogo continuaria — que é a instrução SEGUINTE ao prólogo
    substituído; o endereço entra por `movs r3,#byte; lsls; adds`, nunca por
    literal pc-relativo):

        tramp+0 : push {r0,r1,r2,r3,r6}
                  ... payload da mochila ...
                  pop {r0,r1,r2,r3,r6}
         replay: push {r4,r5,lr}; lsls r0,#24; lsrs r4,r0,#24; lsls r1,#16
         volta : movs r3,#hi ; lsls r3,#8 ; adds r3,#lo ; bx r3
    """
    itens = itens or PADRAO
    rot = ROTINAS[rotina]
    va_site = rot["va"]
    prologo = rot["prologo"]
    payload = payload_mochila(itens, combo)
    corpo_payload = montar(payload, va_tramp)
    va_replay = va_tramp + len(corpo_payload)
    texto_replay = ("push {r4, r5, lr}\n"
                    "lsls r0, r0, #24\n"
                    "lsrs r4, r0, #24\n"
                    "lsls r1, r1, #16\n")
    replay = montar(texto_replay, va_replay)
    if replay != prologo:
        raise ModError(f"replay do prólogo diverge do original: {replay.hex()} != {prologo.hex()}")
    va_volta = va_replay + len(replay)
    destino = (va_site + 8) | 1        # bit Thumb ligado
    bits = montar("\n".join(carregar("r3", destino)) + "\nbx r3", va_volta)
    tramp = corpo_payload + replay + bits
    site = site_veneer(va_site, va_tramp)
    return {"rotina": rotina, "va_site": va_site, "va_tramp": va_tramp,
            "site": site, "tramp": tramp,
            "payload_asm": payload, "offset_replay": len(corpo_payload),
            "combo": combo, "combo_mask": combo_mask(combo),
            "itens": itens, "va_volta": va_volta, "destino_volta": destino}


def aplicador(rom_base: bytes, r: dict, rotina: str = "SetGpuReg",
              permitir_esticar: bool = True) -> bytes:
    """Aplica a receita numa cópia da ROM, com as checagens C1/C2 e a de TAMANHO.

    LACUNA ENCONTRADA (2026-11-07): o trampolim documentado do v3 fica em
    0x08EB0C00, que **está além do fim de uma ROM de 16 MiB** (0x08FFFFFF é o
    último byte endereçável de uma ROM de 16 MiB; 0x08EB0C00 = offset 0xEB0C00
    está DENTRO de 0x1000000, ok — mas ROMs de 8 MiB terminam em 0x08800000).
    Escrever fora do arquivo poria o trampolim em "terra de ninguém" (o cartucho
    lê 0xFF/aberto). Aqui isso vira erro explícito, a menos que se peça para
    esticar o arquivo (preenchendo com 0xFF, o que preserva a semântica de
    leitura aberta).
    """
    rom = bytearray(rom_base)
    fo_site = r["va_site"] - 0x08000000
    fo_tramp = r["va_tramp"] - 0x08000000
    orig = ROTINAS[rotina]["prologo"]
    if rom[fo_site:fo_site + 8] != orig:                              # C1
        raise ModError(f"prólogo em {r['va_site']:#x} não confere: "
                       f"{rom[fo_site:fo_site + 8].hex()} != {orig.hex()}")
    fim_tramp = fo_tramp + len(r["tramp"])
    if fim_tramp > len(rom):
        if not permitir_esticar:
            raise ModError(
                f"trampolim em {r['va_tramp']:#x} cai fora da ROM "
                f"({len(rom)} B; precisa de {fim_tramp} B) — escolha outro run 0xFF "
                f"com --tramp, ou permita esticar")
        rom.extend(b"\xff" * (fim_tramp - len(rom)))
    if set(rom[fo_tramp:fim_tramp]) != {0xFF}:                        # C2
        raise ModError(f"destino do trampolim {r['va_tramp']:#x} não é run 0xFF")
    rom[fo_site:fo_site + 8] = r["site"]
    rom[fo_tramp:fim_tramp] = r["tramp"]
    return bytes(rom)


def self_test() -> int:
    falhas = 0

    def chk(nome: str, ok: bool, extra: str = "") -> None:
        nonlocal falhas
        print(f"  [{'PASS' if ok else 'FAIL'}] {nome}{(' — ' + extra) if extra else ''}")
        if not ok:
            falhas += 1

    print(f"gba_modkit.py {VERSAO} — self-test")
    try:
        r = receita()
    except ModError as e:
        print(f"  [FAIL] dependências: {e}")
        return 1

    # C5 — desassembly auditável
    site_dis = desmontar(r["site"][:4], r["va_site"])
    chk("site: ldr r3,[pc,#0] + bx r3", "pc, #0" in site_dis[0] and "bx" in site_dis[1])
    chk("site tem 8 B", len(r["site"]) == 8, f"{len(r['site'])}")
    chk("literal do site == tramp|1",
        struct.unpack("<I", r["site"][4:8])[0] == (r["va_tramp"] | 1),
        r["site"][4:8].hex())
    chk("trampolim começa em endereço par", r["va_tramp"] % 2 == 0)
    chk("trampolim ≤ 480 B (cabe em qualquer run grande)",
        len(r["tramp"]) <= 480, f"{len(r['tramp'])} B")
    try:
        montar("adds r3, r6", 0x08000000)
        chk("instrução Thumb-2 é recusada (ARM7TDMI)", False)
    except ModError:
        chk("instrução Thumb-2 é recusada (ARM7TDMI)", True)
    # C7 — BL fora de alcance deve falhar de forma explícita (a lição do v2)
    try:
        site_bl(0x08000B08, 0x08EB0C00)
        chk("BL fora de ±4 MB é recusado", False)
    except ModError:
        chk("BL fora de ±4 MB é recusado", True)
    chk("BL dentro do alcance monta e decodifica",
        len(site_bl(0x08000B08, 0x08000A38)) == 4)

    # C6 — simulação: combo pressionado escreve, sem combo não escreve
    sem = simular(r["site"], r["va_site"], r["tramp"], r["va_tramp"],
                  r["tramp"][r["offset_replay"]:r["offset_replay"] + 8],
                  keys=0, r0=0x11223344, r1=0x55667788)
    com = simular(r["site"], r["va_site"], r["tramp"], r["va_tramp"],
                  r["tramp"][r["offset_replay"]:r["offset_replay"] + 8],
                  keys=r["combo_mask"], r0=0x11223344, r1=0x55667788)
    chk("simulação sem combo NÃO escreve na mochila", not sem["escreveu"],
        str(sem["slots"][0]))
    chk("simulação com combo escreve Master Ball ×99",
        com["slots"][0]["id"] == 0x0001 and com["slots"][0]["qtd"] == 99,
        f"{com['slots'][0]}")
    chk("simulação com combo preenche os 8 slots",
        all(s["id"] for s in com["slots"]),
        " ".join(f"{s['id']:02x}x{s['qtd']}" for s in com["slots"]))
    chk("fluxo volta ao prólogo (site+8) sem erro de execução",
        sem["execucao"]["erro"] is None and sem["execucao"]["voltou_ao_prologo"],
        f"pc=0x{sem['execucao']['pc_final']:08x}")
    # o próprio SetGpuReg original "poda" r0/r1 nas 4 primeiras instruções
    # (lsls/lsrs); o payload precisa devolver os registradores EXATAMENTE como
    # se ele não existisse, e é isso que o push/pop garante.
    chk("payload preserva r0/r1 do chamador (sem poda extra)",
        sem["r0_final"] == (0x11223344 << 24) & 0xFFFFFFFF
        and sem["r1_final"] == (0x55667788 << 16) & 0xFFFFFFFF,
        f"r0=0x{sem['r0_final']:08x} r1=0x{sem['r1_final']:08x}")
    # aplicador: ROM sintética de 8 MiB com trampolim em 0x08EB0C00 (fora do fim)
    fixt = ROOT / "tests/fixtures/bench_hook.gba"
    if fixt.is_file():
        base = fixt.read_bytes()
        try:
            aplicador(base, r, permitir_esticar=False)
            chk("trampolim fora do arquivo é recusado", False)
        except ModError:
            chk("trampolim fora do arquivo é recusado", True)
        esticada = aplicador(base, r, permitir_esticar=True)
        chk("esticar a ROM põe o trampolim no fim", len(esticada) > len(base),
            f"{len(base)} -> {len(esticada)} B")

    print(f"resumo: {'OK' if falhas == 0 else str(falhas) + ' falha(s)'}")
    return 0 if falhas == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list-rotinas", action="store_true")
    ap.add_argument("--list-itens", action="store_true")
    ap.add_argument("--rotina", default="SetGpuReg", choices=sorted(ROTINAS))
    ap.add_argument("--combo", default="L+R+START", choices=sorted(COMBOS))
    ap.add_argument("--payload", default="padrao", choices=["padrao", "tudo"])
    ap.add_argument("--rom", type=pathlib.Path)
    ap.add_argument("-o", "--out", type=pathlib.Path)
    ap.add_argument("--dump", type=pathlib.Path, help="grava JSON da receita")
    ap.add_argument("--tramp", type=lambda v: int(v, 0), default=0x08EB0C00,
                    help="VA do trampolim (0x08EB0C00 na ROM real; escolha um run 0xFF)")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.list_rotinas:
        for nome, d in ROTINAS.items():
            print(f"{nome:<14} 0x{d['va']:08X}  prólogo={d['prologo'].hex()}  {d['chamadas']} chamadas")
        return 0
    if args.list_itens:
        for i, n in sorted(ITENS.items()):
            print(f"0x{i:04X}  {n}")
        return 0

    itens = PADRAO if args.payload == "padrao" else list(ITENS.items())[:8]
    r = receita(args.rotina, args.combo, itens, va_tramp=args.tramp)
    print(f"== receita {VERSAO}: {args.rotina} + combo {args.combo} ==")
    print(f"site  0x{r['va_site']:08X}: {r['site'].hex(' ')}")
    for l in desmontar(r["site"][:4], r["va_site"]):
        print("   ", l)
    print(f"tramp 0x{r['va_tramp']:08X} ({len(r['tramp'])} B)")
    for l in desmontar(r["tramp"], r["va_tramp"]):
        print("   ", l)
    sim = simular(r["site"], r["va_site"], r["tramp"], r["va_tramp"],
                  r["tramp"][r["offset_replay"]:r["offset_replay"] + 8],
                  keys=r["combo_mask"])
    print("simulação (combo pressionado):",
          " ".join(f"{s['id']:04X}×{s['qtd']}" for s in sim["slots"]))
    if args.dump:
        args.dump.write_text(json.dumps(
            {"site_hex": r["site"].hex(), "tramp_hex": r["tramp"].hex(),
             "va_site": r["va_site"], "va_tramp": r["va_tramp"],
             "combo": r["combo"], "itens": r["itens"],
             "desasm": desmontar(r["tramp"], r["va_tramp"])},
            indent=2, ensure_ascii=False))
    if args.rom and args.out:
        rom = aplicador(args.rom.read_bytes(), r, args.rotina)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(rom)
        print(f"[OK] {args.out} ({len(rom)} B) sha256={hashlib.sha256(rom).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
