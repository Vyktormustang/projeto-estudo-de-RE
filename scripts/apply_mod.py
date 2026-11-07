#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_mod.py — aplica o mod da mochila numa CÓPIA da ROM do usuário.

Substitui `apply_mod_v3.py` (aquele montava hex fixo do v3, cujo site estava
errado: `ldr r3,[pc,#4]` com o literal em va+4 → `bx` para lixo. Ver
`MEMORIA_CONSOLIDADA.md` §8 para o diagnóstico completo).

O que faz, em ordem:
  1. monta a receita com `gba_modkit` (mnemônicos → bytes; nada de hex à mão);
  2. **simula** o payload no unicorn (com e sem combo) — se não passar, aborta;
  3. confere o prólogo original no site (C1) e se o destino do trampolim é um
     run 0xFF de fábrica (C2);
  4. grava a cópia modificada + relatório JSON com SHA-256 de entrada/saída,
     desassembly do site/trampolim e a lista de itens injetados.

Uso:
  python3 scripts/apply_mod.py --rom rom/jogo.gba -o rom_mod/MOD_BAG.gba
  python3 scripts/apply_mod.py --rom rom/jogo.gba -o rom_mod/MOD_BAG.gba \\
      --combo START+SELECT --tramp 0x08EB0C00
  python3 scripts/apply_mod.py --self-test

⚠ A ROM original nunca é modificada: `-o` é obrigatório e não pode ser igual a
  `--rom`. A ROM comercial não é distribuída com este projeto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gba_modkit as mk  # noqa: E402

VA_ROM = 0x08000000


def aplicar(rom_base: pathlib.Path, saida: pathlib.Path, rotina: str = "SetGpuReg",
            combo: str = "L+R+START", va_tramp: int = 0x08EB0C00,
            itens: list[tuple[int, int]] | None = None,
            esticar: bool = False) -> dict:
    dados = rom_base.read_bytes()
    if len(dados) < 0x200:
        raise SystemExit(f"[ERRO] {rom_base} não parece uma ROM (só {len(dados)} B)")
    codigo = dados[0xAC:0xB0].decode("ascii", "replace")
    receita = mk.receita(rotina, combo, itens, va_tramp=va_tramp)

    # 2) simulação obrigatória antes de encostar na ROM
    sim_off = mk.simular(receita["site"], receita["va_site"], receita["tramp"],
                         receita["va_tramp"],
                         receita["tramp"][receita["offset_replay"]:
                                          receita["offset_replay"] + 8],
                         keys=0, r0=0, r1=0)
    sim_on = mk.simular(receita["site"], receita["va_site"], receita["tramp"],
                        receita["va_tramp"],
                        receita["tramp"][receita["offset_replay"]:
                                         receita["offset_replay"] + 8],
                        keys=receita["combo_mask"], r0=0, r1=0)
    if sim_off["escreveu"] or not sim_on["escreveu"]:
        raise SystemExit("[ERRO] simulação reprovou o payload (off=%s on=%s)"
                         % (sim_off["escreveu"], sim_on["escreveu"]))

    # 3+4) aplica com as checagens
    novo = mk.aplicador(dados, receita, rotina, permitir_esticar=esticar)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_bytes(novo)

    rel = {
        "quando_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rom_entrada": {"arquivo": str(rom_base), "bytes": len(dados),
                        "sha256": hashlib.sha256(dados).hexdigest(),
                        "game_code": codigo},
        "rom_saida": {"arquivo": str(saida), "bytes": len(novo),
                      "sha256": hashlib.sha256(novo).hexdigest()},
        "mod": {"rotina": rotina, "site": f"0x{receita['va_site']:08X}",
                "site_bytes": receita["site"].hex(" "),
                "tramp": f"0x{receita['va_tramp']:08X}",
                "tramp_bytes": len(receita["tramp"]),
                "combo": combo,
                "combo_bits_keyinput": f"0x{receita['combo_mask']:03X}",
                "itens": [{"id": f"0x{i:04X}", "nome": mk.ITENS.get(i, "?"),
                           "qtd": q} for i, q in receita["itens"]]},
        "simulacao": {"sem_combo_escreve": sim_off["escreveu"],
                      "com_combo_escreve": sim_on["escreveu"],
                      "slots": sim_on["slots"]},
        "desassembly_site": mk.desmontar(receita["site"][:4], receita["va_site"]),
        "desassembly_tramp": mk.desmontar(receita["tramp"], receita["va_tramp"]),
    }
    return rel


def self_test() -> int:
    """Aplica na ROM de bancada e valida o relatório (sem tocar na ROM do usuário)."""
    import subprocess
    import tempfile
    falhas = 0

    def chk(nome, ok, extra=""):
        nonlocal falhas
        print(f"  [{'PASS' if ok else 'FAIL'}] {nome}{(' — ' + extra) if extra else ''}")
        if not ok:
            falhas += 1

    print("apply_mod.py — self-test (ROM de bancada)")
    bench = ROOT / "tests/fixtures/bench_hook.gba"
    if not bench.is_file():
        print("  [SKIP] gere a bancada: python3 tests/fixtures/make_bench_rom.py")
        return falhas
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / "mod.gba"
        rel = aplicar(bench, out, va_tramp=0x08020000)
        chk("aplica na bancada", out.is_file() and out.stat().st_size == bench.stat().st_size)
        chk("relatório tem sha256 de entrada e saída",
            len(rel["rom_entrada"]["sha256"]) == 64 and len(rel["rom_saida"]["sha256"]) == 64)
        chk("simulação: sem combo não escreve", rel["simulacao"]["sem_combo_escreve"] is False)
        chk("simulação: com combo escreve", rel["simulacao"]["com_combo_escreve"] is True)
        chk("itens do relatório batem com o payload",
            [(int(i["id"], 16), i["qtd"]) for i in rel["mod"]["itens"]] == mk.PADRAO)
        chk("site modificado na saída",
            out.read_bytes()[0xA38:0xA40].hex() == rel["mod"]["site_bytes"].replace(" ", ""))
        # rodar a ROM modificada no emulador
        r = subprocess.run([sys.executable, str(ROOT / "tests/teste_mod_bench.py")],
                           capture_output=True, text=True)
        chk("bateria de emulação do mod continua verde", r.returncode == 0,
            (r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "")
    print(f"resumo: {'OK' if falhas == 0 else str(falhas) + ' falha(s)'}")
    return 0 if falhas == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", type=pathlib.Path)
    ap.add_argument("-o", "--out", type=pathlib.Path)
    ap.add_argument("--rotina", default="SetGpuReg", choices=sorted(mk.ROTINAS))
    ap.add_argument("--combo", default="L+R+START", choices=sorted(mk.COMBOS))
    ap.add_argument("--tramp", type=lambda v: int(v, 0), default=0x08EB0C00)
    ap.add_argument("--report", type=pathlib.Path, default=None)
    ap.add_argument("--esticar", action="store_true",
                    help="permite crescer a ROM se o trampolim cair além do fim")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.rom or not args.out:
        ap.error("--rom e -o são obrigatórios")
    if args.rom.resolve() == args.out.resolve():
        ap.error("-o não pode ser igual a --rom (a original nunca é modificada)")

    rel = aplicar(args.rom, args.out, args.rotina, args.combo, args.tramp,
                  esticar=args.esticar)
    rep = args.report or (ROOT / "reports" / f"mod_{args.out.stem}.json")
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(rel, indent=2, ensure_ascii=False))

    print(f"[OK] {args.out} ({rel['rom_saida']['bytes']} B)")
    print(f"     sha256 entrada {rel['rom_entrada']['sha256']}")
    print(f"     sha256 saída   {rel['rom_saida']['sha256']}")
    print(f"     site  {rel['mod']['site']}  {rel['mod']['site_bytes']}")
    print(f"     tramp {rel['mod']['tramp']}  ({rel['mod']['tramp_bytes']} B)")
    print(f"     combo {rel['mod']['combo']} (KEYINPUT bits {rel['mod']['combo_bits_keyinput']})")
    print(f"     relatório: {rep}")
    print("\nPRÓXIMO PASSO (obrigatório antes de chamar de pronto):")
    print("  1) boot no emulador até o overworld;")
    print("  2) segurar o combo;")
    print("  3) abrir a mochila e conferir os 8 itens (screenshot).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
