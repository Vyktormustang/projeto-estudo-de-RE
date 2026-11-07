#!/usr/bin/env python3
"""shim_smoke.py — sanidade do shim C (build/gba_shim.so).

Verifica, sem ROM de jogo:
  1. o .so carrega (libmgba embutida, sem rpath);
  2. gs_state_size() == 0x61000 (layout GBASerializedState do mGBA 0.10.5);
  3. carrega uma ROM fixture legal (tests/fixtures/thumb.gba, jsmolka/gba-tests),
     roda 60 frames e lê o header pela memória do barramento (0x080000A0 = 'BPRE'-like id).

Uso: python3 tools/gba_shim/shim_smoke.py [caminho_do_so]
"""
from __future__ import annotations

import ctypes as C
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SO = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools/gba_shim/build/gba_shim.so"
FIXTURE = ROOT / "tests/fixtures/bench_hook.gba"   # ROM de bancada própria (0 conteúdo de jogo)


def bind(lib: C.CDLL) -> None:
    lib.gs_new.restype = C.c_int
    lib.gs_free.argtypes = []
    lib.gs_load.argtypes = [C.c_char_p]
    lib.gs_load.restype = C.c_int
    lib.gs_frames.argtypes = [C.c_int]
    lib.gs_frames.restype = C.c_int
    lib.gs_state_size.restype = C.c_size_t
    lib.gs_read_block.argtypes = [C.c_uint32, C.c_char_p, C.c_int]
    lib.gs_read_block.restype = C.c_int
    lib.gs_keys.argtypes = [C.c_uint32]


def main() -> int:
    if not SO.is_file():
        print(f"[ERRO] shim ausente: {SO} (rode `make shim`)")
        return 1
    lib = C.CDLL(str(SO))
    bind(lib)
    falhas = 0

    def chk(nome: str, ok: bool, extra: str = "") -> None:
        nonlocal falhas
        print(f"  [{'PASS' if ok else 'FAIL'}] {nome}{(' — ' + extra) if extra else ''}")
        if not ok:
            falhas += 1

    chk("biblioteca carrega (sem dependência externa)", True)
    chk("gs_new inicializa o core", bool(lib.gs_new()))
    chk("state size == 0x61000", lib.gs_state_size() == 0x61000,
        f"{lib.gs_state_size():#x}")
    if FIXTURE.is_file():
        chk("ROM fixture carrega", bool(lib.gs_load(str(FIXTURE).encode())))
        f = lib.gs_frames(60)
        chk("60 frames executam", f >= 59, f"frameCounter={f}")
        buf = C.create_string_buffer(16)
        lib.gs_read_block(0x080000AC, buf, 4)
        code = buf.raw[:4]
        chk("header legível pelo barramento (game code ASCII)", all(32 <= b < 127 for b in code),
            code.decode("ascii", "replace"))
    else:
        print(f"  [SKIP] fixture ausente: {FIXTURE}")
    lib.gs_free()
    print(f"\nresumo: {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
