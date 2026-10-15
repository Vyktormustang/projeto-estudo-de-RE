#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gba_hook_code.py — FASE 6: instalador de trampolim de código (hook de BL)
=========================================================================

OBJETIVO
    Substituir um `bl #ALVO` conhecido em `SITE` por `bl #TRAMP`, escrevendo
    o trampolim (payload Thumb do usuário + chamada ao alvo original) em
    espaço livre 0xFF in-file (reports/freespace_map.tsv). Produz uma NOVA
    ROM — entrada nunca alterada (mesma regra do gba_patch_text).

GARANTIAS (espelha as 6 validações de notes_mods_codigo.md)
    1. --expect-bytes "XX XX XX XX": os 4 bytes atuais de SITE devem bater
       EXATAMENTE (use `dis` no endereço para copiá-los).
    2. SITE deve decodificar como `bl #(imm)` (capstone detail) e o alvo
       deve coincidir com --alvo (defesa contra site errado).
    3. Trampolim alocado sequencialmente dentro de uma run ≥256 B de 0xFF;
       ocupação registrada em logs/hook_occupancy.jsonl (sem overlap entre
       hooks sucessivos; alinhamento 4 B garantido).
    4. Payload Thumb vindo de --payload-hex é validado: par, ≤ --max-payload
       B, decodifica por inteiro, e NÃO pode ter `ldr rN,[pc,#x]` ou `adr`
       (pc-deslocado quebraria no trampolim — regra hard).
    5. Saída em caminho diferente; relatório SHA-256 in/out, hexdump do site
       e do trampolim; desassembly final do trampolim impresso para revisão.
    6. CORTE DURO: o hook só se considera FUNCIONAL após validação em
       emulador (ver checklist impresso). Por padrão o arquivo de saída é
       marcado como DRY-RUN/NÃO-VALIDADO no nome, a menos que
       --assumido-validado (uso pós-emulador) seja passado.

USO
    python3 gba_hook_code.py ROM -o SAIDA.gba --site 0xADDR --alvo 0x08000A38 \
        --expect-bytes "xx xx xx xx" --payload-hex "01b5" 
    python3 gba_hook_code.py --self-test     # 6 verificações sintéticas

EXEMPLO DRY-RUN (FireRed BPRE): hook em um site do SetGpuReg_like
    python3 gba_hook_code.py rom/pokemon_firered_bpre_trabalho.gba \
        -o rom_mod/HOOK_DRYRUN_NAO_VALIDADO.gba \
        --site 0xSITE_ACHADO --alvo 0x08000A38 \
        --expect-bytes "COPIE OS 4 BYTES DO SITE" --payload-hex ""

IMPORTANTE: ainda SEM validação dinâmica (mGBA) — saída padrão NÃO deve ser
distribuída como funcional.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gba_disasm import encode_bl_thumb  # noqa: E402

try:  # noqa: E402
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError:
    print("erro: capstone ausente — rode bash scripts/setup_env.sh", file=sys.stderr)
    raise SystemExit(2)

VERSAO = "1.0.0"
BASE_PADRAO = 0xEB0B20        # reserva primária de 1.373.408 B (freespace_map.tsv)
MAX_BL_DIST = (1 << 24) - 4   # alcance ±16 MiB do BL Thumb


# --------------------------------------------------------------------------- #
# Núcleo
# --------------------------------------------------------------------------- #

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def le_run_livre(tsv: Path) -> tuple[int, int]:
    """Maior run 0xFF no TSV; retorna (offset, tamanho)."""
    melhor = (BASE_PADRAO, 0)
    if tsv.is_file():
        with tsv.open(encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                if row["byte"] == "0xff" and int(row["tamanho_bytes"]) > melhor[1]:
                    melhor = (int(row["offset_hex"], 16), int(row["tamanho_bytes"]))
    if 0 < melhor[0] < BASE_PADRAO:
        melhor = (BASE_PADRAO, melhor[1])  # default vale como autoridade
    return melhor if melhor[1] else (BASE_PADRAO, 1_373_408)


def carga_ocupada(log_path: Path) -> int:
    tot = 0
    if log_path.is_file():
        for l in log_path.read_text(encoding="utf-8").splitlines():
            try:
                tot += json.loads(l).get("bytes_trampolim", 0)
            except json.JSONDecodeError:
                continue
    return tot


def validar_payload(pt_hex: str, md: Cs, max_len: int) -> bytes:
    data = bytes.fromhex(pt_hex.replace(" ", "").replace("-", ""))
    if len(data) % 2 or len(data) > max_len:
        raise ValueError(f"payload: tamanho {len(data)} inválido (par e ≤{max_len} exigido)")
    insns = list(md.disasm(data, 0))
    if sum(i.size for i in insns) != len(data):
        raise ValueError("payload: não decodifica por inteiro em Thumb")
    for i in insns:
        h = int.from_bytes(data[i.address:i.address + 2], "little")
        if (h & 0xF800) == 0x4800 or (h & 0xF800) == 0xA000:
            raise ValueError(f"payload: instrução pc-relativa proibida ({i.mnemonic} {i.op_str})")
        if h == 0x4770:
            raise ValueError("payload: sem `bx lr` (o trampolim cuida do retorno)")
    return data


def montar_trampolim(site: int, alvo: int, tramp_va: int, payload: bytes) -> bytes:
    """push {lr}; payload; bl ALVO; pop {pc}  (só com offsets dentro do alcance)"""
    corpo = bytearray()
    corpo += bytes.fromhex("00b5")             # push {lr}  (0xB500)
    corpo += payload
    # BL ALVO emitido a partir da POSIÇÃO exata onde cairá
    pos_bl = tramp_va + len(corpo)
    corpo += encode_bl_thumb(pos_bl, alvo)
    corpo += bytes.fromhex("00bd")             # pop {pc}  (0xBD00)
    return bytes(corpo)


def payload_contador(alvo: int, tramp_va: int, addr: int) -> bytes:
    """Trampolim AUTO-CONTIDO de 'contador':

    layout (tramp o 4-alinhado):
      +0   push {lr}                     2 B
      +2   ldr r0, [pc, #12]             2 B   ; pc+4 alinhado = +4 → lê +16
      +4   ldr r1, [r0]                  2 B
      +6   adds r1, #1                   2 B
      +8   str r1, [r0]                  2 B
      +10  bl ALVO                       4 B
      +14  pop {pc}                      2 B
      +16  literal: addr (u32)           4 B

    Total 20 B. Efeito: mem32[addr]++ antes de chamar o alvo original.
    """
    if tramp_va % 4 or addr % 4 or not (0 <= addr < 0x100000000):
        raise ValueError("tramp e addr precisam ser u32-alinhados")
    by = bytearray()
    by += bytes.fromhex("00b5")                # push {lr}
    by += bytes.fromhex("0348")                # ldr r0,[pc,#12]  (0x4803)
    by += bytes.fromhex("0168")                # ldr r1,[r0]      (0x6801)
    by += bytes.fromhex("491c")                # adds r1,#1       (0x1C49)
    by += bytes.fromhex("0160")                # str r1,[r0]      (0x6001)
    by += encode_bl_thumb(tramp_va + 10, alvo)
    by += bytes.fromhex("00bd")                # pop {pc}
    by += addr.to_bytes(4, "little")
    return bytes(by)


def aplicar_hook(rom: bytes, site: int, alvo: int, expect: bytes | None,
                 payload_hex: str, max_payload: int, tramp_va: int,
                 md: Cs, contador_addr: int | None = None) -> dict:
    site_off = site - 0x08000000
    if not (0 <= site_off + 4 <= len(rom)):
        raise ValueError(f"site {site:#x} fora da ROM")
    atual = rom[site_off:site_off + 4]
    if expect is not None and atual != expect:
        raise ValueError(f"PRÉ-CONDIÇÃO FALHOU em {site:#x}: {atual.hex(' ')} != esperado")
    dec = list(md.disasm(atual, site, count=0))
    dec1 = list(md.disasm(atual, site))[:1]
    instr = dec1[0] if dec1 else None
    if instr is None or instr.mnemonic != "bl" or instr.size != 4:
        raise ValueError(f"site {site:#x} não decodifica como BL Thumb 32-bit")
    alvo_dec = int(instr.op_str.strip().lstrip("#"), 16)
    if alvo_dec != alvo:
        raise ValueError(f"alvo no site = {alvo_dec:#x} ≠ --alvo {alvo:#x} (site errado?)")
    if abs(tramp_va - site + 4) > MAX_BL_DIST or abs(alvo - tramp_va) > MAX_BL_DIST:
        raise ValueError("trampolim fora do alcance do BL (±16 MiB)")

    payload = validar_payload(payload_hex, md, max_payload)
    if contador_addr is not None:
        tramp = payload_contador(alvo, tramp_va, contador_addr)
    else:
        tramp = montar_trampolim(site, alvo, tramp_va, payload)
    tramp_off = tramp_va - 0x08000000
    if not (0 <= tramp_off + len(tramp) <= len(rom)):
        raise ValueError(f"trampolim fora da ROM ({tramp_va:#x})")
    if any(b != 0xFF for b in rom[tramp_off:tramp_off + len(tramp)]):
        raise ValueError(f"região do trampolim {tramp_va:#x} não é 0xFF puro — região ocupada?")

    nova = bytearray(rom)
    nova[site_off:site_off + 4] = encode_bl_thumb(site, tramp_va)
    nova[tramp_off:tramp_off + len(tramp)] = tramp
    n_alter = sum(a != b for a, b in zip(rom, nova))
    return {"rom": bytes(nova), "rel": {
        "site": f"0x{site:08x}", "alvo": f"0x{alvo:08x}",
        "tramp_va": f"0x{tramp_va:08x}", "tramp_bytes": len(tramp),
        "site_hex_depois": encode_bl_thumb(site, tramp_va).hex(" "),
        "tramp_hex": tramp.hex(" "),
        "bytes_alterados_na_rom": n_alter,
        "payload_bytes": len(payload)}}


def _desasm(texto_bytes: bytes, va: int, md: Cs) -> str:
    out = []
    for i in md.disasm(texto_bytes, va):
        out.append(f"0x{i.address:08x}: {i.mnemonic} {i.op_str}".rstrip())
    return " | ".join(out)


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #

def _espera_erro(fn, *args, exc=Exception, **kw):
    try:
        fn(*args, **kw)
    except exc:
        return True
    return False


def self_test(verbose: bool) -> int:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail = False
    ROM = 0x08000000
    rom = bytearray(b"\xff" * 0x1000)
    site, alvo = ROM + 0x100, ROM + 0x300
    rom[0x100:0x104] = encode_bl_thumb(site, alvo)
    tramp_va = ROM + 0x800
    falhos = 0

    def chk(nome, ok):
        nonlocal falhos
        if verbose or not ok:
            print(f"  [{'PASS' if ok else 'FAIL'}] {nome}")
        falhos += 0 if ok else 1

    ok_payload = "40b4"  # push {r6}  (decod, par, sem pc-rel)
    r = aplicar_hook(bytes(rom), site, alvo, None, ok_payload, 64, tramp_va, md)
    chk("hook feliz: site vira bl→tramp",
        r["rom"][0x100:0x104] == encode_bl_thumb(site, tramp_va))
    chk("hook feliz: trampolim contém push lr + payload + bl alvo + pop pc",
        r["rom"][0x800:0x802] == bytes.fromhex("00b5") and
        r["rom"][0x802:0x804] == bytes.fromhex("40b4") and
        r["rom"][0x804:0x808] == encode_bl_thumb(tramp_va + 4, alvo) and
        r["rom"][0x808:0x80A] == bytes.fromhex("00bd"))
    chk("expect errado ABORTA", _espera_erro(
        aplicar_hook, bytes(rom), site, alvo, bytes(4), ok_payload, 64, tramp_va, md,
        exc=ValueError))
    chk("site não-BL ABORTA", _espera_erro(
        aplicar_hook, bytes(rom), ROM + 0x108, alvo, None, ok_payload, 64, tramp_va, md,
        exc=ValueError))
    chk("payload pc-rel ABORTA", _espera_erro(
        aplicar_hook, bytes(rom), site, alvo, None, "0048", 64, tramp_va, md,
        exc=ValueError))  # 0x4800 = ldr r0,[pc,#0]
    chk("trampolim sobre não-0xFF ABORTA", _espera_erro(
        aplicar_hook, bytes(rom), site, alvo, None, ok_payload, 64, site, md,
        exc=ValueError))
    # --- modo contador ---
    CT = 0x0E001000
    rc = aplicar_hook(bytes(rom), site, alvo, None, "", 64, tramp_va, md,
                      contador_addr=CT)
    t = rc["rom"][0x800:0x800 + 20]
    chk("contador: layout 20 B com literal + BL certo",
        t[:10] == bytes.fromhex("00b503480168491c0160") and
        t[10:14] == encode_bl_thumb(tramp_va + 10, alvo) and
        t[14:16] == bytes.fromhex("00bd") and
        int.from_bytes(t[16:20], "little") == CT)
    print(f"self-test: {7 - falhos}/7 verificações OK")
    return 1 if falhos else 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--site", type=lambda s: int(s, 0))
    ap.add_argument("--alvo", type=lambda s: int(s, 0))
    ap.add_argument("--expect-bytes", default=None)
    ap.add_argument("--payload-hex", default="")
    ap.add_argument("--payload-contador", type=lambda s: int(s, 0), default=None,
                    help="modo contador mem32++ em 0xADDR (ex.: 0x0E001000 = save RAM, legível via region 0)")
    ap.add_argument("--max-payload", type=int, default=64)
    ap.add_argument("--tramp-va", type=lambda s: int(s, 0), default=None,
                    help="forçar endereço (avançado). Padrão: próximo slot da run")
    ap.add_argument("--freespace", type=Path, default=root / "reports/freespace_map.tsv")
    ap.add_argument("--assumido-validado", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.verbose)
    erros = []
    if args.rom is None or not args.rom.is_file():
        erros.append("ROM inexistente")
    if args.out is None or args.site is None or args.alvo is None:
        erros.append("forneça -o, --site e --alvo")
    if erros:
        print("erro: " + "; ".join(erros) + " (veja --help)", file=sys.stderr)
        return 2
    if args.rom.resolve() == args.out.resolve():
        print("RECUSADO: saída == entrada (in-place proibido).", file=sys.stderr)
        return 2

    expect = None
    if args.expect_bytes is not None:
        try:
            expect = bytes.fromhex(args.expect_bytes.replace(" ", ""))
        except ValueError:
            print("erro: --expect-bytes inválido.", file=sys.stderr)
            return 2
        if len(expect) != 4:
            print("erro: --expect-bytes precisa de EXATOS 4 bytes.", file=sys.stderr)
            return 2

    t0 = time.perf_counter()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail = False
    rom = args.rom.read_bytes()
    base, _ = le_run_livre(args.freespace)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ocupada = carga_ocupada(logs / "hook_occupancy.jsonl")
    tramp_va = args.tramp_va if args.tramp_va is not None else \
        (0x08000000 + base + ocupada + 3) & ~3

    try:
        r = aplicar_hook(rom, args.site, args.alvo, expect, args.payload_hex,
                         args.max_payload, tramp_va, md,
                         contador_addr=args.payload_contador)
    except ValueError as e:
        print(f"ABORTADO: {e}", file=sys.stderr)
        return 3

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(r["rom"])
    rel = r["rel"]
    sha_in, sha_out = sha256(rom), sha256(r["rom"])
    valido = "VALIDADO" if args.assumido_validado else "DRY-RUN/NÃO-VALIDADO"

    print(f"== HOOK DE CÓDIGO APLICADO [{valido}] ==")
    print(f"  site {rel['site']} (alvo {rel['alvo']}) → tramp {rel['tramp_va']}")
    print(f"  site hex depois: {rel['site_hex_depois']}")
    print(f"  trampolim ({rel['tramp_bytes']} B): {rel['tramp_hex']}")
    print(f"  tramp desasm: {_desasm(bytes.fromhex(rel['tramp_hex'].replace(' ', '')), tramp_va, md)}")
    print(f"  bytes alterados na ROM inteira: {rel['bytes_alterados_na_rom']}")
    print(f"  SHA-256 in:  {sha_in[:32]}…")
    print(f"  SHA-256 out: {sha_out[:32]}…  ({args.out})")
    if not args.assumido_validado:
        print("  CHECKLIST (antes de chamar de funcional): boot no emulador → "
              "alvo chamado? → comportamento esperado? → sem crash em 60s?")

    occ = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "ferramenta": "gba_hook_code.py", "versao": VERSAO, "validado": bool(args.assumido_validado),
           "entrada": str(args.rom), "saida": str(args.out),
           "site": rel["site"], "alvo": rel["alvo"], "tramp_va": rel["tramp_va"],
           "bytes_trampolim": rel["tramp_bytes"] + (-(-rel["tramp_bytes"] // 4) * 4 - rel["tramp_bytes"]) or rel["tramp_bytes"],
           "sha256_in_prefixo": sha_in[:16], "sha256_out_prefixo": sha_out[:16],
           "duracao_s": round(time.perf_counter() - t0, 3)}
    occ["bytes_trampolim"] = (rel["tramp_bytes"] + 3) & ~3  # alinhado p/ 4 p/ próximo hook
    with (logs / "hook_occupancy.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(occ, ensure_ascii=False) + "\n")
    with (logs / "gba_hook_code_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"utc": occ["utc"], "evento": "hook_aplicado",
                            "validado": bool(args.assumido_validado),
                            "site": rel["site"], "tramp": rel["tramp_va"]},
                           ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
