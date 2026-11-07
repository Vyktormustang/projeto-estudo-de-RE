#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gba_emu.py — harness de emulação mGBA v0.4.0 (sucessor do libretro headless).

POR QUE ESTE ARQUIVO EXISTE
    O driver anterior (`gba_libretro_emu.py` + core `mgba_libretro.so` do .deb)
    morreu de causa-raiz dupla:
      1. o `.so` do Debian 13 exige GLIBC 2.38; os sandboxes têm 2.36
         → `GLIBC_2.38 not found` (o self-test apontava isso);
      2. o core libretro publica **0 descritores de memória** → sem leitura de
         EWRAM/IWRAM e sem CPU/registradores (era a "rota morta" do ciclo 22).
    Este harness usa o shim próprio `tools/gba_shim` (libmgba compilada no
    próprio sandbox) e fala direto com o barramento do emulador.

O QUE OFERECE
    frames determinísticos, agenda de input, snapshots PNG, save-state binário
    (0x61000 B, layout GBASerializedState), leitura/escrita de qualquer região
    (EWRAM 0x02000000, IWRAM 0x03000000, IO 0x04000000, PAL 0x05000000,
    VRAM 0x06000000, ROM 0x08000000), registradores e **breakpoints de PC**.

USO
    python3 scripts/gba_emu.py --rom jogo.gba --frames 600 --png tela.png
    python3 scripts/gba_emu.py --rom jogo.gba --load-state marco.bin \\
        --input 10:L:60 --input 10:R:60 --input 10:START:60 \\
        --read 0x020258B8:16 --save-state depois.bin
    python3 scripts/gba_emu.py --self-test

TECLAS (aceitas em --input): A B SELECT START UP DOWN LEFT RIGHT L R
"""
from __future__ import annotations

import argparse
import ctypes as C
import json
import pathlib
import struct
import sys
import zlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHIM_DEFAULT = ROOT / "tools/gba_shim/build/gba_shim.so"
VERSAO = "0.4.0"

# máscara libretro clássica (mesma usada pelo core antigo: --input continua válido)
BOTOES = {"B": 1, "Y": 2, "SELECT": 4, "START": 8, "UP": 16, "DOWN": 32,
          "LEFT": 64, "RIGHT": 128, "A": 256, "X": 512, "L": 1024, "R": 2048}

STATE_SIZE = 0x61000
# offsets dentro do GBASerializedState (mGBA 0.10.5) — usados por gba_state_dump
STATE_OFF = {"IW RAM": 0x19000, "EW RAM": 0x21000}
REGIAO = {"EWRAM": 0x02000000, "IWRAM": 0x03000000, "IO": 0x04000000,
          "PAL": 0x05000000, "VRAM": 0x06000000, "OAM": 0x07000000,
          "ROM": 0x08000000}


class Emu:
    """Wrapper fino sobre o shim C. Uma instância = um core mGBA."""

    def __init__(self, shim: pathlib.Path | str = SHIM_DEFAULT):
        shim = pathlib.Path(shim)
        if not shim.is_file():
            raise FileNotFoundError(
                f"shim ausente: {shim}\n  compile com: make -C tools/gba_shim")
        self.lib = C.CDLL(str(shim))
        L = self.lib
        L.gs_new.restype = C.c_int
        L.gs_load.argtypes = [C.c_char_p]
        L.gs_load.restype = C.c_int
        L.gs_frames.argtypes = [C.c_int]
        L.gs_frames.restype = C.c_int
        L.gs_steps.argtypes = [C.c_int]
        L.gs_steps.restype = C.c_int
        L.gs_frames_bp.argtypes = [C.c_int]
        L.gs_frames_bp.restype = C.c_int
        L.gs_keys.argtypes = [C.c_uint32]
        for f in ("gs_read8", "gs_read16", "gs_read32"):
            getattr(L, f).argtypes = [C.c_uint32]
            getattr(L, f).restype = C.c_uint32
        L.gs_write8.argtypes = [C.c_uint32, C.c_uint32]
        L.gs_write16.argtypes = [C.c_uint32, C.c_uint32]
        L.gs_write32.argtypes = [C.c_uint32, C.c_uint32]
        L.gs_read_block.argtypes = [C.c_uint32, C.c_char_p, C.c_int]
        L.gs_write_block.argtypes = [C.c_uint32, C.c_char_p, C.c_int]
        L.gs_state_size.restype = C.c_size_t
        L.gs_state_save.argtypes = [C.c_char_p]
        L.gs_state_load.argtypes = [C.c_char_p]
        L.gs_bp_add.argtypes = [C.c_uint32]
        L.gs_bp_add.restype = C.c_int
        L.gs_bp_hits.argtypes = [C.c_int]
        L.gs_bp_hits.restype = C.c_uint32
        L.gs_video.argtypes = [C.c_char_p]
        L.gs_pc.restype = C.c_uint32
        L.gs_reg.argtypes = [C.c_int]
        L.gs_reg.restype = C.c_int32
        L.gs_cpsr.restype = C.c_uint32
        L.gs_frame_counter.restype = C.c_int
        L.gs_keys_active.restype = C.c_uint32
        if not L.gs_new():
            raise RuntimeError("gs_new() falhou: core mGBA não inicializou")
        self._rom = None
        self.frames_total = 0
        self._agenda: list[tuple[int, int, int]] = []   # (inicio, hold, mask)
        self._bps: list[int] = []
        self._stride_state = L.gs_state_size()

    # ---------------- ciclo de vida ----------------
    def load(self, rom: pathlib.Path | str) -> "Emu":
        if not self.lib.gs_load(str(rom).encode()):
            raise RuntimeError(f"mCoreLoadFile falhou: {rom}")
        self._rom = str(rom)
        self.frames_total = 0
        self._bps.clear()
        self.lib.gs_bp_clear()
        return self

    def close(self) -> None:
        self.lib.gs_free()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    # ---------------- execução ----------------
    def keys(self, mask: int) -> None:
        self.lib.gs_keys(mask)

    def hold(self, *nomes: str) -> None:
        m = 0
        for n in nomes:
            m |= BOTOES[n.upper()]
        self.keys(m)

    def release(self) -> None:
        self.keys(0)

    def schedule(self, frame: int, botoes: str, hold: int = 2) -> None:
        """Agenda um toque: a partir de `frame`, segura `hold` frames."""
        mask = 0
        for n in botoes.replace("+", " ").replace(",", " ").split():
            mask |= BOTOES[n.upper()]
        self._agenda.append((frame, hold, mask))

    def _aplicar_agenda(self) -> None:
        """Se houver agenda, ela manda no keypad; senão respeita hold()/release()."""
        if not self._agenda:
            return
        t = self.frames_total
        mask = 0
        for inicio, hold, m in self._agenda:
            if inicio <= t < inicio + hold:
                mask |= m
        self.lib.gs_keys(mask)

    def frames(self, n: int) -> int:
        """Roda n frames (respeitando a agenda de input). Retorna frameCounter."""
        for _ in range(n):
            self._aplicar_agenda()
            self.lib.gs_frames(1)
            self.frames_total += 1
        return self.lib.gs_frame_counter()

    def steps(self, n: int) -> int:
        """Executa n instruções. Retorna índice do breakpoint atingido (-1 = nenhum)."""
        return self.lib.gs_steps(n)

    # ---------------- memória ----------------
    def read8(self, a: int) -> int:
        return self.lib.gs_read8(a)

    def read16(self, a: int) -> int:
        return self.lib.gs_read16(a)

    def read32(self, a: int) -> int:
        return self.lib.gs_read32(a)

    def read(self, a: int, n: int) -> bytes:
        buf = C.create_string_buffer(n)
        self.lib.gs_read_block(a, buf, n)
        return buf.raw[:n]

    def write(self, a: int, dados: bytes) -> None:
        buf = C.create_string_buffer(dados, len(dados))
        self.lib.gs_write_block(a, buf, len(dados))

    def write16(self, a: int, v: int) -> None:
        self.lib.gs_write16(a, v)

    def keys_raw(self) -> int:
        """REG_KEYINPUT (0x04000130), ativo-baixo.

        ATENÇÃO: é o espelho de IO — o mGBA só o atualiza quando o jogo lê o
        registrador. Para saber o que está realmente pressionado use keys_held().
        """
        return self.read16(0x04000130) & 0x3FF

    def keys_held(self) -> int:
        """Bits ativos dos botões segurados, direto do keypad do emulador."""
        return self.lib.gs_keys_active() & 0x3FF

    def keys_held_nomes(self) -> list[str]:
        nomes = {1: "A", 2: "B", 4: "SELECT", 8: "START", 16: "RIGHT",
                 32: "LEFT", 64: "UP", 128: "DOWN", 256: "R", 512: "L"}
        k = self.keys_held()
        return [n for bit, n in nomes.items() if k & bit]

    # ---------------- CPU ----------------
    def pc(self) -> int:
        return self.lib.gs_pc()

    def reg(self, i: int) -> int:
        return self.lib.gs_reg(i) & 0xFFFFFFFF

    def thumb(self) -> bool:
        return bool(self.lib.gs_cpsr() & 0x20)

    # ---------------- breakpoints ----------------
    def bp_add(self, addr: int) -> int:
        i = self.lib.gs_bp_add(addr)
        self._bps.append(addr & ~1)
        return i

    def bp_clear(self) -> None:
        self.lib.gs_bp_clear()
        self._bps.clear()

    def bp_hits(self) -> list[int]:
        return [self.lib.gs_bp_hits(i) for i in range(len(self._bps))]

    def run_to_bp(self, max_frames: int = 600) -> int:
        """Roda até um breakpoint. Retorna índice do BP ou -1 se estourou frames."""
        for _ in range(max_frames):
            self._aplicar_agenda()
            r = self.lib.gs_frames_bp(1)
            self.frames_total += 1
            if r < 0:
                return -1 - r
        return -1

    # ---------------- estado ----------------
    def save_state(self, caminho: pathlib.Path | str) -> None:
        buf = C.create_string_buffer(self._stride_state)
        if not self.lib.gs_state_save(buf):
            raise RuntimeError("gs_state_save falhou")
        pathlib.Path(caminho).write_bytes(buf.raw[: self._stride_state])

    def load_state(self, caminho: pathlib.Path | str) -> None:
        dados = pathlib.Path(caminho).read_bytes()
        if len(dados) < self._stride_state:
            raise ValueError(f"save-state curto: {len(dados)} < {self._stride_state}")
        self.lib.gs_state_load(C.create_string_buffer(dados, len(dados)))

    # ---------------- vídeo ----------------
    def png(self, caminho: pathlib.Path | str) -> pathlib.Path:
        buf = C.create_string_buffer(240 * 160 * 2)
        if not self.lib.gs_video(buf):
            raise RuntimeError("gs_video falhou")
        px = struct.unpack("<38400H", buf.raw[: 240 * 160 * 2])
        rgb = bytearray()
        for c in px:
            r = (c >> 11) & 0x1F
            g = (c >> 5) & 0x3F
            b = c & 0x1F
            rgb += bytes(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)))
        out = pathlib.Path(caminho)
        out.parent.mkdir(parents=True, exist_ok=True)
        _png_write(out, 240, 160, bytes(rgb))
        return out

    def md5_tela(self) -> str:
        import hashlib
        buf = C.create_string_buffer(240 * 160 * 2)
        self.lib.gs_video(buf)
        return hashlib.md5(buf.raw).hexdigest()


def _png_write(path: pathlib.Path, w: int, h: int, rgb: bytes) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    linhas = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
           chunk(b"IDAT", zlib.compress(linhas, 9)) + chunk(b"IEND", b""))
    path.write_bytes(png)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _parse_read(s: str) -> tuple[int, int]:
    a, _, n = s.partition(":")
    return int(a, 0), int(n or "4", 0)


def _log(entrada: dict) -> None:
    d = ROOT / "logs"
    d.mkdir(exist_ok=True)
    entrada["quando_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with (d / "gba_emu_runs.jsonl").open("a") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def self_test(shim: pathlib.Path) -> int:
    """Testes estruturais do harness com ROM fixture legal (jsmolka/gba-tests)."""
    falhas = 0

    def chk(nome: str, ok: bool, extra: str = "") -> None:
        nonlocal falhas
        print(f"  [{'PASS' if ok else 'FAIL'}] {nome}{(' — ' + extra) if extra else ''}")
        if not ok:
            falhas += 1

    print(f"gba_emu.py {VERSAO} — self-test")
    try:
        emu = Emu(shim)
    except Exception as e:  # noqa: BLE001
        print(f"  [FAIL] shim não carrega: {e}")
        return 1
    chk("shim carrega", True)
    chk("state size 0x61000", emu._stride_state == STATE_SIZE, f"{emu._stride_state:#x}")

    fix = ROOT / "tests/fixtures/bench_hook.gba"
    if not fix.is_file():
        print(f"  [SKIP] fixture ausente: {fix} (gere com tests/fixtures/make_bench_rom.py)")
        emu.close()
        return falhas
    emu.load(fix)
    chk("ROM fixture carrega", True)
    emu.frames(30)
    f0 = emu.frames(30)
    chk("frames avançam", f0 >= 59, f"frameCounter={f0}")
    hdr = emu.read(0x080000AC, 4).decode("ascii", "replace")
    chk("game code legível (0x080000AC)", hdr.isprintable(), hdr)
    # determinismo: mesmo ponto do estado => mesmo PC
    st = ROOT / "emu/run/selftest_state.bin"
    st.parent.mkdir(parents=True, exist_ok=True)
    emu.save_state(st)
    pc1 = emu.pc()
    emu.frames(10)
    emu.load_state(st)
    chk("save/load-state restaura o PC", emu.pc() == pc1, f"{pc1:#010x}")
    # teclas: segurar e ler REG_KEYINPUT
    emu.hold("A")
    emu.frames(2)
    botoes = emu.keys_held()
    chk("keypad reflete A (bit 0)", bool(botoes & 1), f"0x{botoes:03x}")
    emu.release()
    emu.frames(2)
    chk("soltar zera as teclas", emu.keys_held() == 0, f"0x{emu.keys_held():03x}")
    # breakpoint
    alvo = emu.pc()
    emu.bp_add(alvo)
    r = emu.run_to_bp(30)
    chk("breakpoint de PC dispara", r >= 0 and emu.bp_hits()[0] >= 1,
        f"r={r} hits={emu.bp_hits()}")
    emu.close()
    print(f"resumo: {'OK' if falhas == 0 else str(falhas) + ' falha(s)'}")
    return 0 if falhas == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", type=pathlib.Path)
    ap.add_argument("--shim", type=pathlib.Path, default=SHIM_DEFAULT)
    ap.add_argument("--frames", type=int, default=600)
    ap.add_argument("--input", action="append", default=[],
                    help="FRAME:BOTAO[:HOLD]  (ex.: 100:L:60)")
    ap.add_argument("--snap", action="append", default=[],
                    help="FRAME=arquivo.png")
    ap.add_argument("--png", type=pathlib.Path)
    ap.add_argument("--save-state", type=pathlib.Path)
    ap.add_argument("--load-state", type=pathlib.Path)
    ap.add_argument("--read", action="append", default=[],
                    help="VA:tamanho (ex.: 0x020258B8:16)")
    ap.add_argument("--probe-keys", action="store_true",
                    help="imprime REG_KEYINPUT por frame (debug de input)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.shim)
    if not args.rom:
        ap.error("--rom é obrigatório (ou use --self-test)")

    emu = Emu(args.shim).load(args.rom)
    if args.load_state:
        emu.load_state(args.load_state)
    for item in args.input:
        p = item.split(":")
        emu.schedule(int(p[0]), p[1], int(p[2]) if len(p) > 2 else 2)
    snaps = {}
    for s in args.snap:
        f, _, arq = s.partition("=")
        snaps[int(f)] = arq

    rel: dict = {"rom": str(args.rom), "versao": VERSAO}
    prog = 0
    for alvo in sorted(snaps):
        if alvo > prog:
            if args.probe_keys:
                while prog < alvo:
                    emu.frames(1)
                    prog += 1
                    print(f"frame {prog}: KEYINPUT=0x{emu.read16(0x04000130) & 0x3FF:03x}")
            else:
                emu.frames(alvo - prog)
                prog = alvo
        emu.png(snaps[alvo])
        rel.setdefault("snaps", []).append({"frame": alvo, "arquivo": snaps[alvo],
                                            "md5": emu.md5_tela()})
    if args.frames > prog:
        emu.frames(args.frames - prog)
        prog = args.frames
    if args.png:
        emu.png(args.png)
    if args.save_state:
        args.save_state.parent.mkdir(parents=True, exist_ok=True)
        emu.save_state(args.save_state)
    leituras = {}
    for r in args.read:
        va, n = _parse_read(r)
        leituras[f"0x{va:08X}:{n}"] = emu.read(va, n).hex()
    rel.update({"frames": prog, "frame_counter": emu.lib.gs_frame_counter(),
                "pc": f"0x{emu.pc():08X}", "thumb": emu.thumb(),
                "keyinput": f"0x{emu.read16(0x04000130) & 0x3FF:03x}",
                "leituras": leituras})
    if args.verbose:
        for k, v in leituras.items():
            print(f"  {k} = {v}")
    print(json.dumps(rel, ensure_ascii=False, indent=2))
    _log(rel)
    emu.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
