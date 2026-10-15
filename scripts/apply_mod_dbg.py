#!/usr/bin/env python3
"""apply_mod_dbg.py — monta ROMs de DIAGNÓSTICO do isolador de gating (HANDOFF §1).

Uso:  python3 scripts/apply_mod_dbg.py [--variant always|regkey] [rom-base] [saida]
  --variant always  (default) tramp escreve 0xAAAA em slot-0 da bolsa SEM checar
                    teclas — isolador decisivo: se nem isso gravar, o trap nunca
                    roda na cena (SetGpuReg não é chamada no bedroom overworld).
  --variant regkey  tramp lê REG_KEYINPUT 0x04000130 (ativo-baixo, fonte robusta
                    de teclas — HANDOFF §1b) e só grava com L+R+START (0x0308).

  rom-base (default: rom/pokemon_firered_bpre_trabalho.gba)
  saida    (default: rom_mod/BAG_MOD_dbg_<variant>.gba)

O que aplica (igual v3):
  * site @0x08000A38 (8 B): ldr r3,[pc,#4]; bx r3; .word TRAMP+1  (veneer).
  * trampolim @0x08EB0C00: push{r0-r3} + payload + pop{r0-r3} + replay do
    prologo + retorno bx → 0x08000A43 (bit0=1, Thumb).
Bytes fonte: reports/site_v3.hex + reports/tramp_always.hex|reports/tramp_regkey.hex
(montagem auditada por capstone — ver progress.md c35; 3 bugs de hand-assembly
pegos pela auditoria: muls≠mvns, bne pulando pop, strh≠str).
Asserts: bytes originais do prologo; run 0xFF no destino do trampolim.
"""
import hashlib
import pathlib
import sys

FO_SITE, FO_TRAMP = 0x0A38, 0xEB0C00
ORIG = bytes.fromhex("30 b5 00 06 04 0e 09 04")
VARIANTES = {
    "always": "reports/tramp_always.hex",
    "regkey": "reports/tramp_regkey.hex",
}


def main():
    argv = sys.argv[1:]
    variante = "always"
    if argv and argv[0] == "--variant":
        variante = argv[1]
        argv = argv[2:]
        if variante not in VARIANTES:
            sys.exit(f"[ERRO] variante desconhecida: {variante} (use {list(VARIANTES)})")
    root = pathlib.Path(__file__).resolve().parent.parent
    base = pathlib.Path(argv[0]) if len(argv) > 0 else root / "rom/pokemon_firered_bpre_trabalho.gba"
    out = pathlib.Path(argv[1]) if len(argv) > 1 else root / f"rom_mod/BAG_MOD_dbg_{variante}.gba"

    site = bytes.fromhex((root / "reports/site_v3.hex").read_text().strip())
    tramp = bytes.fromhex((root / VARIANTES[variante]).read_text().strip())
    if not base.is_file():
        sys.exit(f"[ERRO] ROM-base ausente: {base} (não incluída no repo; use sua cópia)")

    rom = bytearray(base.read_bytes())
    assert rom[FO_SITE:FO_SITE + 8] == ORIG, "prólogo @0xA38 diverge: ROM errada?"
    assert set(rom[FO_TRAMP:FO_TRAMP + len(tramp)]) == {0xFF}, "destino do trampolim não é 0xFF"
    rom[FO_SITE:FO_SITE + 8] = site
    rom[FO_TRAMP:FO_TRAMP + len(tramp)] = tramp
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(rom))
    print(f"[OK] variante={variante} {out} ({len(tramp)} B tramp) "
          f"sha256={hashlib.sha256(bytes(rom)).hexdigest()}")
    print("Teste: python3 scripts/gba_libretro_emu.py --rom", out,
          "--frames 600 --snap 480=dbg.png")
    print("Depois: python3 scripts/gba_state_dump.py <state> --read 0x020258B8:0x04")


if __name__ == "__main__":
    main()
