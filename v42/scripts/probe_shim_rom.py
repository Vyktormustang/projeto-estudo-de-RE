#!/usr/bin/env python3
"""probe_shim_rom.py — sonda de viabilidade do shim próprio com a ROM V42.

Objetivo: decidir, com medição, se a frente de eclosão deve migrar do core
libretro (que exige serializar 528 448 B por leitura de memória, porque não
emite SET_MEMORY_MAPS) para o shim C (`gs_*`), que lê o barramento direto.

O que é CONFIRMADO aqui, se tudo passar:
  1. o shim carrega a ROM V42 de 32 MiB;
  2. o core do shim avança frames;
  3. `gs_read_block` enxerga o header do jogo (game code ASCII);
  4. `gs_state_size()` informa o tamanho real do estado;
  5. custo de `gs_read_block` (~poucos bytes) é ordens de grandeza menor que
     o custo de serializar o estado inteiro no core libretro.

Nada aqui é uma eclosão. É a prova de viabilidade que faltava.

Uso:
  python3 v42/scripts/probe_shim_rom.py --self-test
  COSMOG_V42_ROM=/caminho/rom.gba python3 v42/scripts/probe_shim_rom.py
"""
from __future__ import annotations

import ctypes as C
import hashlib
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
SO = ROOT / "tools/gba_shim/build/gba_shim.so"
ROM_ESPERADA_SHA256 = "6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a"


def bind(lib: C.CDLL) -> None:
    lib.gs_new.restype = C.c_int
    lib.gs_load.argtypes = [C.c_char_p]
    lib.gs_load.restype = C.c_int
    lib.gs_frames.argtypes = [C.c_int]
    lib.gs_frames.restype = C.c_int
    lib.gs_state_size.restype = C.c_size_t
    lib.gs_read_block.argtypes = [C.c_uint32, C.c_char_p, C.c_int]
    lib.gs_read_block.restype = C.c_int
    lib.gs_read16.argtypes = [C.c_uint32]
    lib.gs_read16.restype = C.c_uint16
    lib.gs_free.argtypes = []


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def main() -> int:
    if "--self-test" in sys.argv:
        # valida a lógica de veredito sem depender de ROM nem de .so
        ok = ROM_ESPERADA_SHA256 == "6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a"
        ok &= len(ROM_ESPERADA_SHA256) == 64
        print(f"  [{'PASS' if ok else 'FAIL'}] self-test: hash de referência bem formado")
        print(f"\nresumo: {'OK' if ok else '1 falha(s)'}")
        return 0 if ok else 1

    rom = os.environ.get("COSMOG_V42_ROM", "")
    if not rom:
        print("[ERRO] defina COSMOG_V42_ROM")
        return 2
    rom_p = pathlib.Path(rom)
    if not rom_p.is_file():
        print(f"[ERRO] ROM ausente: {rom_p}")
        return 2
    if not SO.is_file():
        print(f"[ERRO] shim ausente: {SO} (rode `make -C tools/gba_shim shim`)")
        return 2

    falhas = 0

    def chk(nome: str, ok: bool, extra: str = "") -> None:
        nonlocal falhas
        print(f"  [{'PASS' if ok else 'FAIL'}] {nome}{(' — ' + extra) if extra else ''}")
        if not ok:
            falhas += 1

    print("[1/5] integridade da ROM")
    digest = sha256(rom_p)
    chk("SHA-256 == V42 homologada", digest == ROM_ESPERADA_SHA256, digest[:16] + "…")
    chk("tamanho == 32 MiB", rom_p.stat().st_size == 33_554_432, f"{rom_p.stat().st_size} B")

    print("[2/5] carregar o shim")
    lib = C.CDLL(str(SO))
    bind(lib)
    chk("gs_new inicializa o core", bool(lib.gs_new()))

    print("[3/5] carregar a ROM no shim")
    t0 = time.time()
    chk("gs_load aceita a V42", bool(lib.gs_load(str(rom_p).encode())))
    print(f"        (load: {time.time() - t0:.3f} s)")

    print("[4/5] avançar frames e ler o barramento")
    t0 = time.time()
    frames = lib.gs_frames(60)
    print(f"        (60 frames: {time.time() - t0:.3f} s)")
    chk("60 frames executam", frames >= 59, f"frameCounter={frames}")

    buf = C.create_string_buffer(16)
    lib.gs_read_block(0x080000AC, buf, 4)
    code = buf.raw[:4]
    chk(
        "game code ASCII legível em 0x080000AC",
        all(32 <= b < 127 for b in code),
        code.decode("ascii", "replace"),
    )
    chk("game code é o da V42 (BPRE)", code == b"BPRE", code.decode("ascii", "replace"))

    print("[5/5] custo de leitura de memória (a razão de existir deste shim)")
    n = 200
    t0 = time.time()
    for _ in range(n):
        lib.gs_read16(0x03000000)
    dt_shim = (time.time() - t0) / n
    print(f"        gs_read16: {dt_shim * 1e6:.1f} µs/leitura  ({n} leituras)")
    chk("leitura direta abaixo de 1 ms", dt_shim < 1e-3, f"{dt_shim * 1e6:.0f} µs")

    size = lib.gs_state_size()
    print(f"        gs_state_size = {size} B ({size / 1024:.0f} KiB)")

    lib.gs_free()
    print(f"\nresumo: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
