#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gba_table_probe.py — FASE 3: sonda de tabelas de salto e hubs de outdegree
==========================================================================

OBJETIVO
    1. --table END [--n 34]: lê n ponteiros u32; para cada alvo, decodifica as
       primeiras --insns instruções Thumb e resume: instruções iniciais,
       branch tail (b #dest), calls BL registrados, valor 32-bit "colado"
       possível literal.
    2. --hub END: decodifica --insns instruções no endereço e lista TODOS os
       alvos BL (com nome do functions.csv, se houver) + palavras 32-bit do
       pool de literais que apontem para RAM (0x020/0x030) ou ROM.
    3. Saída textual determinística para relatório + JSON opcional.

USO
    python3 gba_table_probe.py ROM --table 0x0803FC08 --n 34
    python3 gba_table_probe.py ROM --hub 0x0808CFF8 --insns 160
    python3 gba_table_probe.py --self-test     # 3 verificações sintéticas

LIMITAÇÕES
    Sonda estática: segue apenas o início linear de cada handler (não segue
    branches). Pool de literais: heuristic scan na janela após a função.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError:
    print("erro: capstone ausente — rode bash scripts/setup_env.sh", file=sys.stderr)
    raise SystemExit(2)

VERSAO = "1.0.0"


def desasm_thumb(md: Cs, rom: bytes, va: int, n_insns: int) -> list:
    off = va - 0x08000000
    return list(md.disasm(rom[off:off + n_insns * 2], va, count=n_insns))


def resumo_handler(md: Cs, rom: bytes, va: int, n_insns: int) -> dict:
    insns = desasm_thumb(md, rom, va, n_insns)
    txt = [f"{i.mnemonic} {i.op_str}".strip() for i in insns]
    tail = None
    calls = []
    for i in insns:
        op = i.op_str.strip()
        if i.mnemonic == "bl" and op.startswith("#"):
            calls.append(op[1:])
        if i.mnemonic in ("b", "b.n") and op.startswith("#"):
            tail = op[1:]  # último b linear = tail
    return {"va": f"0x{va:08x}", "entrada": " | ".join(txt[:4]),
            "tail_b": tail, "bls": calls, "n_decod": len(insns)}


def sonda_tabela(rom: bytes, tbl_va: int, n: int, n_insns: int) -> dict:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    off = tbl_va - 0x08000000
    if not (0 <= off + 4 * n <= len(rom)):
        raise ValueError(f"tabela {tbl_va:#x}+{4*n} bytes fora da ROM")
    entries = []
    for k in range(n):
        ptr = int.from_bytes(rom[off + 4 * k:off + 4 * k + 4], "little")
        if not (0x08000000 <= ptr < 0x08000000 + len(rom)) and ptr != 0:
            entries.append({"idx": k, "ptr": f"0x{ptr:08x}", "erro": "ponteiro inválido"})
            continue
        h = resumo_handler(md, rom, ptr, n_insns) if ptr else {"va": "0x0", "entrada": "(nulo)"}
        h["idx"] = k
        h["ptr"] = f"0x{ptr:08x}"
        entries.append(h)
    return {"tabela": f"0x{tbl_va:08x}", "n": n, "entries": entries}


def sonda_hub(rom: bytes, hub_va: int, n_insns: int, nomes: dict) -> dict:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    insns = desasm_thumb(md, rom, hub_va, n_insns)
    calls, memw = [], []
    for i in insns:
        t = f"{i.mnemonic} {i.op_str}".strip()
        if i.mnemonic == "bl" and i.op_str.strip().startswith("#"):
            tgt = i.op_str.strip()[1:]
            calls.append({"addr": tgt, "nome": nomes.get(int(tgt, 16), "")})
        # loads stores com símbolo de pool exibidos por capstone como [pc, #..]
    # scan literal pool na janela
    off = hub_va - 0x08000000
    pool = []
    for k in range(off, min(off + 4 * n_insns + 0x80, len(rom) - 3), 2):
        w = int.from_bytes(rom[k:k + 4], "little")
        if 0x02000000 <= w < 0x03008000 or 0x03007F00 <= w < 0x03008000 or \
           0x04000000 <= w < 0x04001000:  # EWRAM / IWRAM(topo) / IO
            pool.append(f"0x{w:08x}")
    return {"hub": f"0x{hub_va:08x}", "n_decod": len(insns),
            "calls": calls, "pool_suspeito": sorted(set(pool))[:24]}


def carregar_nomes(functions_csv: Path) -> dict:
    nomes = {}
    if functions_csv.is_file():
        for l in functions_csv.read_text(encoding="utf-8").splitlines():
            if l.strip() and not l.startswith("#") and not l.startswith("endereco_hex"):
                c = l.split(",")
                nomes[int(c[0], 16)] = c[2]
    return nomes


def _espera_true(nome, ok, verbose, falhas):
    if verbose or not ok:
        print(f"  [{'PASS' if ok else 'FAIL'}] {nome}")
    return falhas + (0 if ok else 1)


def self_test(verbose: bool) -> int:
    # ROM sintética: tabela @0x100 com 2 handlers: stub `movs r0, #3; b #armazem`
    # e stub `bl #callee`. "b +8" = e0 04 — dest = pc+4+8 = handler+12.
    rom = bytearray(b"\x00" * 0x400)
    base = 0x08000000
    h0, h1 = base + 0x180, base + 0x190
    rom[0x100:0x108] = h0.to_bytes(4, "little") + h1.to_bytes(4, "little")
    rom[0x180:0x184] = bytes.fromhex("032006e0")          # movs r0,#3 ; b +12
    rom[0x190:0x19A] = bytes.fromhex("00f003f8fe46")      # bl (hi/lo) + nop alinhado
    dados = sonda_tabela(bytes(rom), base + 0x100, 2, 4)  # noqa: F841 (rom alinhado)
    # obs.: bl fakes acima devem decodificar; apenas verificamos estrutura
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    dec = desasm_thumb(md, bytes(rom), h0, 2)
    falhas = 0
    falhas = _espera_true("stub movs+b decodifica 2 insns",
                          len(dec) == 2 and dec[0].mnemonic == "movs" and dec[1].mnemonic == "b",
                          verbose, falhas)
    falhas = _espera_true("tabela: 2 entradas", len(dados["entries"]) == 2, verbose, falhas)
    falhas = _espera_true("tail_b do handler 0 detectado",
                          dados["entries"][0].get("tail_b") is not None, verbose, falhas)
    print(f"self-test: {3 - falhas}/3 verificações OK")
    return 1 if falhas else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("--table", type=lambda s: int(s, 0))
    ap.add_argument("--hub", type=lambda s: int(s, 0))
    ap.add_argument("--n", type=int, default=34)
    ap.add_argument("--insns", type=int, default=8)
    ap.add_argument("-f", "--functions", type=Path,
                    default=Path(__file__).resolve().parent.parent / "functions.csv")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.verbose)
    if args.rom is None or not args.rom.is_file():
        print("erro: ROM inexistente.", file=sys.stderr)
        return 2
    rom = args.rom.read_bytes()
    nomes = carregar_nomes(args.functions)

    if args.table is not None:
        d = sonda_tabela(rom, args.table, args.n, args.insns)
        print(f"== TABELA {d['tabela']} ({d['n']} entradas; {d['entries'][0] and ''}"
              f" mostra primeiras {args.insns} insns) ==")
        tails = {}
        for e in d["entries"]:
            ptr = e.get("ptr", "?")
            if e.get("erro"):
                print(f"  [{e['idx']:2}] {ptr}  ERRO: {e['erro']}")
                continue
            t = e.get("tail_b") or "-"
            tails[t] = tails.get(t, 0) + 1
            bls = ",".join(e.get("bls", [])) or "-"
            print(f"  [{e['idx']:2}] {ptr}  tail={t:<18} bl={bls:<18} {e.get('entrada', '')}")
        print("  tails mais comuns:", sorted(tails.items(), key=lambda x: -x[1])[:5])
        if args.json:
            args.json.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    elif args.hub is not None:
        d = sonda_hub(rom, args.hub, args.insns, nomes)
        print(f"== HUB {d['hub']} — {d['n_decod']} insns decodificadas ==")
        print(f"  {len(d['calls'])} calls BL na janela:")
        for c in d["calls"]:
            print(f"    {c['addr']:<12} {c['nome']}")
        print("  pool de memória na janela:")
        for p in d["pool_suspeito"]:
            print(f"    {p}")
        if args.json:
            args.json.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print("erro: use --table ou --hub (veja --help).", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
