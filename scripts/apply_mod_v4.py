#!/usr/bin/env python3
"""apply_mod_v4.py — monta rom_mod/BAG_MOD_v4.gba a partir dos .hex do repo.

Uso:  python3 scripts/apply_mod_v4.py [rom-base] [saida]
  rom-base (default: rom/pokemon_firered_bpre_trabalho.gba)
  saida    (default: rom_mod/BAG_MOD_v4.gba)

O que aplica:
  * site @0x08000A38 (8 B): ldr r3,[pc,#4]; bx r3; .word TRAMP+1  (veneer, pois
    BL Thumb so alcanca ±4 MB — ver HANDOFF.md/MEMORIA_CONSOLIDADA.md)
  * trampolim @0x08EB0C00: push{r0-r3} + payload (combo L+R+START -> preencher
    8 slots da mochila em 0x020258B8) + pop + replay do prologo + retorno bx.
Bytes fonte: reports/site_v3.hex, reports/tramp_v4.hex (auditoria capstone em
MEMORIA_CONSOLIDADA.md §5 / gerador em progress.md c34).
Asserts: bytes originais do prologo, run 0xFF no destino do trampolim.
"""
import sys, pathlib

FO_SITE, FO_TRAMP = 0x0A38, 0xEB0C00
ORIG = bytes.fromhex("30 b5 00 06 04 0e 09 04")


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    base = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "rom/pokemon_firered_bpre_trabalho.gba"
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else root / "rom_mod/BAG_MOD_v4.gba"
    site = bytes.fromhex((root / "reports/site_v3.hex").read_text().strip())
    tramp = bytes.fromhex((root / "reports/tramp_v4.hex").read_text().strip())
    if not base.is_file():
        sys.exit(f"[ERRO] ROM-base ausente: {base} (não incluída no repo; use sua cópia)")
    rom = bytearray(base.read_bytes())
    assert rom[FO_SITE:FO_SITE + 8] == ORIG, "prólogo @0xA38 diverge: ROM errada?"
    assert set(rom[FO_TRAMP:FO_TRAMP + len(tramp)]) == {0xFF}, "destino do trampolim não é 0xFF"
    rom[FO_SITE:FO_SITE + 8] = site
    rom[FO_TRAMP:FO_TRAMP + len(tramp)] = tramp
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(rom))
    import hashlib
    print(f"[OK] {out} ({len(tramp)} B tramp; site {site.hex()}) sha256={hashlib.sha256(bytes(rom)).hexdigest()}")
    print("Teste: python3 scripts/gba_libretro_emu.py --rom", out, "--frames 600 --snap 480=repro.png")


if __name__ == "__main__":
    main()
