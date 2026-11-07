#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_bench_rom.py — ROM de bancada (fixture própria) para provar o mod.

POR QUE EXISTE
    A ROM comercial não entra no repositório (regra do projeto). Sem ela, a
    "prova final" do mod ficava sempre pendente de um teste manual do dono.
    Esta ROM sintética — escrita por nós, sem nenhum conteúdo de jogo — reproduz
    **a mesma interface** que o hook usa no FireRed:

        * uma rotina chamada a cada quadro em 0x08000A38 com o prólogo exato
          `push {r4,r5,lr}; lsls r0,r0,#24; lsrs r4,r0,#24; lsls r1,r1,#16`;
        * chamada por `bl` a partir de um laço principal (como a ROM real faz
          1238×);
        * run de 0xFF em 0x08020000 para receber o trampolim;
        * mochila em EWRAM 0x020258B8 (`{id:u16, qty:u16}` × 8), igual à do jogo;
        * um contador em 0x03000100 que sobe 1 a cada chamada — é o "relógio"
          que prova no emulador que o hook está sendo executado por quadro.

    Com ela o mod é validado ponta a ponta **no emulador** (mGBA), com input
    real e leitura da mochila — sem depender de ROM de terceiros.

USO
    python3 tests/fixtures/make_bench_rom.py -o tests/fixtures/bench_hook.gba
    python3 tests/fixtures/make_bench_rom.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
VA_BASE = 0x08000000
TAM = 0x021000            # 132 KiB: 0x20000 (código) + trampolim em 0x08020000? ajustado abaixo
SITE = 0x08000A38
TRAMP = 0x08020000
BAG = 0x020258B8

PROLOGO = bytes.fromhex("30b50006040e0904")

HEADER = {
    "titulo": b"BENCHHOOK",       # 12 B
    "game_code": b"BENH",         # 4 B
    "maker_code": b"01",         # 2 B
    "versao": 0,
}


def _montar(asm: str, base: int, arm: bool = False) -> bytes:
    import keystone
    ks = keystone.Ks(keystone.KS_ARCH_ARM,
                     keystone.KS_MODE_ARM if arm else keystone.KS_MODE_THUMB)
    enc, _ = ks.asm(asm.strip(), addr=base)
    if not enc:
        raise SystemExit(f"[ERRO] assembler falhou: {asm}")
    return bytes(enc)


def gerar() -> bytes:
    rom = bytearray(b"\xff" * TAM)

    # ---- header (0xB2 bytes padrão GBA) ----
    rom[0x000:0x004] = _montar("b #0x080000C0", VA_BASE, arm=True)   # entry ARM
    rom[0x004:0x0A0] = b"\x00" * 0x9C
    rom[0x0A0:0x0AC] = HEADER["titulo"].ljust(12, b"\x00")
    rom[0x0AC:0x0B0] = HEADER["game_code"]
    rom[0x0B0:0x0B2] = HEADER["maker_code"]
    rom[0x0B2] = 0x96
    rom[0x0B3] = 0x00
    rom[0x0BC:0x0C0] = struct.pack("<H", HEADER["versao"]) + b"\x00\x00"

    # ---- entrada ARM (obrigatória) que só troca para Thumb e cai no laço ----
    # A chamada real do jogo é `bl SetGpuReg` a partir de código Thumb; imitar
    # isso é essencial: um `bx` de ARM para Thumb com lr sem bit0 voltava
    # bagunçado (o `pop {..,pc}` mantinha T=1 e desalinhava tudo).
    THUMB_MAIN = 0x080000E0
    stub = _montar(f"""
        ldr   sp, =0x03007F00
        ldr   r4, ={THUMB_MAIN + 1:#x}
        bx    r4
    """, 0x080000C0, arm=True)
    rom[0x0C0:0x0C0 + len(stub)] = stub

    # ---- laço principal (Thumb), uma chamada por volta ----
    main = f"""
        movs r0, #0
        movs r1, #1
        bl   #{SITE:#x}
        b    #{THUMB_MAIN:#x}
    """
    codigo = _montar(main, THUMB_MAIN)
    if THUMB_MAIN + len(codigo) > SITE:
        raise SystemExit("[ERRO] laço principal invade o endereço do site")
    rom[THUMB_MAIN - VA_BASE:THUMB_MAIN - VA_BASE + len(codigo)] = codigo

    # ---- "SetGpuReg" em 0x08000A38, com o prólogo EXATO do jogo ----
    # corpo: incrementa o contador de 0x03000100 (prova de execução por quadro)
    corpo = _montar("""
        movs r2, #3
        lsls r2, r2, #24
        movs r3, #1
        lsls r3, r3, #8
        adds r2, r2, r3
        ldr  r3, [r2]
        adds r3, r3, #1
        str  r3, [r2]
        pop  {r4, r5, pc}
    """, SITE + len(PROLOGO))
    rom[SITE - VA_BASE:SITE - VA_BASE + 8] = PROLOGO
    ini = SITE - VA_BASE + len(PROLOGO)
    rom[ini:ini + len(corpo)] = corpo

    # ---- região do trampolim: preenchida de 0xFF (nenhum byte tocado) ----
    assert set(rom[TRAMP - VA_BASE:TRAMP - VA_BASE + 512]) == {0xFF}

    # checksum do header (soma de 0xA0..0xBC, complemento)
    soma = sum(rom[0xA0:0xBD]) & 0xFF
    rom[0xBD] = (-(soma + 0x19)) & 0xFF
    return bytes(rom)


def self_test() -> int:
    import capstone
    rom = gerar()
    md_arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md_thumb = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    falhas = 0

    def chk(nome, ok, extra=""):
        nonlocal falhas
        print(f"  [{'PASS' if ok else 'FAIL'}] {nome}{(' — ' + extra) if extra else ''}")
        if not ok:
            falhas += 1

    print("make_bench_rom.py — self-test")
    chk("tamanho", len(rom) == TAM, f"{len(rom)} B")
    chk("entry ARM é branch", next(md_arm.disasm(rom[:4], VA_BASE)).mnemonic == "b")
    chk("prólogo do site idêntico ao da ROM real",
        rom[SITE - VA_BASE:SITE - VA_BASE + 8] == PROLOGO,
        rom[SITE - VA_BASE:SITE - VA_BASE + 8].hex())
    chk("site decodifica o prólogo esperado",
        [i.mnemonic for i in md_thumb.disasm(rom[SITE - VA_BASE:SITE - VA_BASE + 8], SITE)]
        == ["push", "lsls", "lsrs", "lsls"])
    chk("região do trampolim é toda 0xFF",
        set(rom[TRAMP - VA_BASE:TRAMP - VA_BASE + 512]) == {0xFF})
    chk("game code no header", rom[0x0AC:0x0B0] == b"BENH")
    chk("determinístico", hashlib.sha256(gerar()).hexdigest() == hashlib.sha256(rom).hexdigest())
    print(f"resumo: {'OK' if falhas == 0 else str(falhas) + ' falha(s)'}")
    return 0 if falhas == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", type=pathlib.Path,
                    default=ROOT / "tests/fixtures/bench_hook.gba")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    rom = gerar()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(rom)
    print(f"[OK] {args.out} ({len(rom)} B) sha256={hashlib.sha256(rom).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
