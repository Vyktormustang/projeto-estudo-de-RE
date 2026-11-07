#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gba_libretro_emu.py — FASE 4: driver libretro headless (mGBA core) via ctypes
=============================================================================

OBJETIVO
    Executar uma ROM de GBA dentro do sandbox, SEM root/retroarch: carrega
    `emu/x/usr/lib/x86_64-linux-gnu/libretro/mgba_libretro.so` (+libinih),
    implementa os callbacks mínimos da API libretro (environment, video,
    audio, input, log) e oferece: N frames, PNG do framebuffer final,
    leituras de memória (EWRAM etc. via retro_get_memory_data) e log do core.

USO
    python3 gba_libretro_emu.py --rom ROM.gba --frames 600 --png out.png \
        --mem-read 0x02000000:0x40 [--boot-input "300:START,12:none"] [-v]
    python3 gba_libretro_emu.py --self-test   # estrutural (não emula CPU deps.)

    # LD_LIBRARY_PATH necessário se libinih não achar automaticamente:
    LD_LIBRARY_PATH=emu/x/usr/lib/x86_64-linux-gnu python3 ...

SAÍDAS/logs
    --png (opcional), stdout: JSON relatório; logs/gba_libretro_runs.jsonl

LIMITAÇÕES
    - Não é debugger: sem breakpoints PC. Watchpoints de memória: ler memória
      por frame e comparar se necessário (via --mem-read pós-run).
    - HLE-BIOS do mGBA (sem BIOS real): jogo pode divergir sutilmente.
    - Input: padrão tudo solto; esquema de agenda a ser evoluído (cFrames).
"""
from __future__ import annotations

import argparse
import ctypes as C
import json
import os
import struct
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE_DEFAULT = ROOT / "emu/x/usr/lib/x86_64-linux-gnu/libretro/mgba_libretro.so"
LIBS = ROOT / "emu/x/usr/lib/x86_64-linux-gnu"
VERSAO = "0.3.0"

# enums libretro
ENV_SET_PIXEL_FORMAT, ENV_GET_CAN_DUPE = 10, 3
ENV_GET_LOG_INTERFACE, ENV_GET_SYSTEM_DIRECTORY = 27, 9
FMT_CODES = {0: ("0RGB1555", 2), 1: ("XRGB8888", 4), 2: ("RGB565", 2)}
BOTOES = {"B": 0, "Y": 1, "SELECT": 2, "START": 3, "UP": 4,
          "DOWN": 5, "LEFT": 6, "RIGHT": 7, "A": 8, "X": 9, "L": 10, "R": 11}
MEM = {"SAVE_RAM": 0, "RTC": 1, "SYSTEM_RAM(EWRAM)": 2, "VRAM": 3,
       "PALETTE": 4, "IWRAM": 5, "ROM": 7, "IRAM?": 6}

SIMBOLOS = ["retro_init", "retro_deinit", "retro_api_version",
            "retro_get_system_info", "retro_get_system_av_info",
            "retro_set_environment", "retro_set_video_refresh",
            "retro_set_audio_sample", "retro_set_audio_sample_batch",
            "retro_set_input_poll", "retro_set_input_state",
            "retro_set_controller_port_device", "retro_reset", "retro_run",
            "retro_serialize_size", "retro_serialize", "retro_unserialize",
            "retro_unload_game", "retro_load_game", "retro_get_region",
            "retro_get_memory_data", "retro_get_memory_size"]


class GameInfo(C.Structure):
    _fields_ = [("path", C.c_char_p), ("data", C.POINTER(C.c_ubyte)),
                ("size", C.c_size_t), ("meta", C.c_char_p)]


class Geometry(C.Structure):
    _fields_ = [("base_width", C.c_uint), ("base_height", C.c_uint),
                ("max_width", C.c_uint), ("max_height", C.c_uint),
                ("aspect_ratio", C.c_float)]


class Timing(C.Structure):
    _fields_ = [("fps", C.c_double), ("sample_rate", C.c_double)]


class MemDescriptor(C.Structure):
    _fields_ = [("flags", C.c_uint64), ("ptr", C.c_void_p),
                ("offset", C.c_uint64), ("start", C.c_uint64),
                ("select", C.c_uint64), ("disconnect", C.c_uint64),
                ("len", C.c_uint64), ("addrspace", C.c_char_p)]


class MemMap(C.Structure):
    _fields_ = [("descriptors", C.POINTER(MemDescriptor)),
                ("num_descriptors", C.c_uint)]


class AvInfo(C.Structure):
    _fields_ = [("geometry", Geometry), ("timing", Timing)]


ENV_CB = C.CFUNCTYPE(C.c_int, C.c_uint, C.c_void_p)
VIDEO_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUS_CB = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUB_CB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
IPOLL_CB = C.CFUNCTYPE(None)
ISTATE_CB = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
LOG_CB = C.CFUNCTYPE(None, C.c_char_p)


class LogStruct(C.Structure):
    _fields_ = [("log", LOG_CB)]


def png_write(path: Path, w: int, h: int, rgb: bytes) -> None:
    """Grava RGB (w*h*3) como PNG via zlib (stdlib)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    path.write_bytes(png)


class Core:
    def __init__(self, core_path: Path, work_dir: Path, verbose=False):
        # resilience: snapshots podem perder o symlink libinih.so.1 → re-materializar
        l1, l58 = LIBS / "libinih.so.1", LIBS / "libinih.so.58"
        if not l1.exists() and l58.exists():
            import shutil
            shutil.copyfile(l58, l1)
        # LD_LIBRARY_PATH só vale se setado ANTES do processo; preload absoluto
        # com RTLD_GLOBAL resolve a dep do core independentemente de env:
        if l1.exists():
            C.CDLL(str(l1), mode=C.RTLD_GLOBAL)
        self.core = C.CDLL(str(core_path))
        # restypes críticos (sem isso ctypes trunca ponteiro 64-bit → segfault):
        self.core.retro_get_memory_data.restype = C.c_void_p
        self.core.retro_get_memory_size.restype = C.c_size_t
        self.work, self.verbose = work_dir, verbose
        self.fmt_code, self.fmt = None, None
        self.last_rgb, self.w, self.h = None, 0, 0
        self.frames_capturados, self.logs = 0, []
        self.inputs: dict = {}
        self.agenda: dict = {}   # frame → (button_id, até_frame)
        self.mmaps: list = []

        def _env(cmd, data):
            nonlocal_self = self
            try:
                if cmd == ENV_SET_PIXEL_FORMAT and data:
                    v = C.cast(data, C.POINTER(C.c_int)).contents.value
                    if v in FMT_CODES:
                        self.fmt_code = v
                        self.fmt = FMT_CODES[v]
                        if self.verbose:
                            print(f"[env] pixel_format={self.fmt[0]}")
                        return 1
                    return 0
                if cmd == ENV_GET_CAN_DUPE and data:
                    C.cast(data, C.POINTER(C.c_int))[0] = 1
                    return 1
                if cmd == ENV_GET_LOG_INTERFACE and data:
                    # logprintf_t do libretro é VARIADIC — ctypes não modela
                    # ABI variádurso; negar (evita corrupção/segfault).
                    return 0
                if cmd == ENV_GET_SYSTEM_DIRECTORY and data:
                    C.cast(data, C.POINTER(C.c_char_p))[0] = str(self.work).encode()
                    return 1
                return 0
            except Exception as e:  # noqa: BLE001
                if self.verbose:
                    print(f"[env erro] {e}")
                return 0

        def _video(data, w, h, pitch):
            if not data:
                return
            cod, bpp = self.fmt
            stride = w * bpp
            pixels = bytearray()
            if pitch == stride:
                pixels = bytearray(C.string_at(data, stride * h))
            else:
                for y in range(h):
                    pixels += C.string_at(data + y * pitch, stride)
            rgb = bytearray(w * h * 3)
            if self.fmt_code == 1:  # XRGB8888
                for i in range(0, stride * h, 4):
                    b, g, r = pixels[i], pixels[i + 1], pixels[i + 2]
                    o = (i // 4) * 3
                    rgb[o:o + 3] = bytes((r, g, b))
            elif self.fmt_code == 2:  # RGB565
                for i in range(0, stride * h, 2):
                    v = pixels[i] | (pixels[i + 1] << 8)
                    r = ((v >> 11) & 31) * 255 // 31
                    g = ((v >> 5) & 63) * 255 // 63
                    b = (v & 31) * 255 // 31
                    o = (i // 2) * 3
                    rgb[o:o + 3] = bytes((r, g, b))
            else:  # 0RGB1555
                for i in range(0, stride * h, 2):
                    v = pixels[i] | (pixels[i + 1] << 8)
                    r = ((v >> 10) & 31) * 255 // 31
                    g = ((v >> 5) & 31) * 255 // 31
                    b = (v & 31) * 255 // 31
                    o = (i // 2) * 3
                    rgb[o:o + 3] = bytes((r, g, b))
            self.last_rgb, self.w, self.h = bytes(rgb), w, h
            self.frames_capturados += 1

        def _aus(l, r):
            return None

        def _aub(data, frames):
            return frames

        def _ipoll():
            return None

        def _istate(port, dev, idx, iid):
            return self.inputs.get((port, dev, idx, iid), 0)

        def _log(fmt):
            if fmt:
                msg = fmt.decode(errors="replace").rstrip()
                self.logs.append(msg)
                if self.verbose and len(self.logs) < 60:
                    print(f"[core] {msg}")

        self._env_cb = ENV_CB(_env)
        self._video_cb = VIDEO_CB(_video)
        self._aus_cb = AUS_CB(_aus)
        self._aub_cb = AUB_CB(_aub)
        self._ipoll_cb = IPOLL_CB(_ipoll)
        self._istate_cb = ISTATE_CB(_istate)
        self._log_cb = LOG_CB(_log)

        c = self.core
        c.retro_set_environment(self._env_cb)
        c.retro_set_video_refresh(self._video_cb)
        c.retro_set_audio_sample(self._aus_cb)
        c.retro_set_audio_sample_batch(self._aub_cb)
        c.retro_set_input_poll(self._ipoll_cb)
        c.retro_set_input_state(self._istate_cb)
        c.retro_init()
        self.av = None  # av_info só é válido APÓS load_game (chamá-lo antes = crash)

    def carregar(self, rom: Path) -> None:
        gi = GameInfo(str(rom.resolve()).encode(), None, 0, None)
        if not self.core.retro_load_game(C.byref(gi)):
            raise RuntimeError("retro_load_game retornou falso — ROM inválida/NES?/core incompatível")
        self.av = AvInfo()
        self.core.retro_get_system_av_info(C.byref(self.av))

    def rodar(self, frames: int, snaps: dict | None = None) -> int:
        for i in range(frames):
            self.inputs = {}
            for b, (ini, ate) in list(self.agenda.items()):
                if i < ini:
                    continue
                if ate is not None and i > ate:
                    del self.agenda[b]
                    continue
                self.inputs[(0, 1, 0, b)] = 1
            self.core.retro_run()
            if snaps and i in snaps and self.last_rgb:
                png_write(snaps[i], self.w, self.h, self.last_rgb)
        return self.frames_capturados

    def map_read(self, addr: int, n: int) -> bytes | None:
        for d in self.mmaps:
            if d["ptr"] and d["start"] <= addr < d["start"] + d["len"]:
                return C.string_at(d["ptr"] + d["offset"] + (addr - d["start"]), n)
        return None

    def memoria(self, regiao: int, off: int, n: int) -> bytes:
        total = self.core.retro_get_memory_size(regiao)
        base = self.core.retro_get_memory_data(regiao)
        if not base or off + n > total:
            return b""
        return bytes(C.string_at(base + off, n))


def self_test(verbose: bool, core: Path) -> int:
    falhas = 0

    def chk(nome, ok):
        nonlocal falhas
        if verbose or not ok:
            print(f"  [{'PASS' if ok else 'FAIL'}] {nome}")
        falhas += 0 if ok else 1

    chk("core .so existe", core.is_file())
    try:
        # mesma rota do Core.__init__: preload de libinih antes do CDLL
        l1 = core.parent.parent / "libinih.so.1"
        if l1.exists():
            C.CDLL(str(l1), mode=C.RTLD_GLOBAL)
        lib = C.CDLL(str(core))
        todos = all(hasattr(lib, s) for s in SIMBOLOS)
        chk(f"{len(SIMBOLOS)} símbolos libretro exportados", todos)
        chk("retro_api_version==1", lib.retro_api_version() == 1)
    except OSError as e:
        chk(f"core carrega via CDLL ({e})", False)
    chk("FMT_CODES mapeia os 3 formats libretro", set(FMT_CODES) == {0, 1, 2})
    tmp = Path("/tmp/_png_smoke.png")
    png_write(tmp, 2, 2, bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0]))
    chk("encoder PNG produz assinatura PNG", tmp.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n")
    print(f"self-test: {5 - falhas}/5 verificações OK")
    return 1 if falhas else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--core", type=Path, default=CORE_DEFAULT)
    ap.add_argument("--frames", type=int, default=600)
    ap.add_argument("--png", type=Path)
    ap.add_argument("--mem-read", action="append", default=[],
                    help="0xOFF:0xN (repetível); ver --mem-region")
    ap.add_argument("--mem-region", type=int, default=0,
                    help="0=SAVE_RAM (única exposta por este mGBA; 131072 B)")
    ap.add_argument("--workdir", type=Path, default=ROOT / "emu/run")
    ap.add_argument("--input", action="append", default=[],
                    help="agenda: FRAME:BOTAO[:SEGURAR]; ex.: 900:START:15 (repetível)")
    ap.add_argument("--snap", action="append", default=[],
                    help="FRAME:out.png — captura nesse frame (repetível)")
    ap.add_argument("--save-state", type=Path, default=None,
                    help="serializa o estado final neste arquivo")
    ap.add_argument("--load-state", type=Path, default=None,
                    help="restaura estado antes de rodar --frames")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.verbose or True, args.core)
    if args.rom is None or not args.rom.is_file():
        print("erro: informe --rom existente.", file=sys.stderr)
        return 2
    if not args.core.is_file():
        print("erro: core libretro ausente (emu/.../.so).", file=sys.stderr)
        return 2

    args.workdir.mkdir(parents=True, exist_ok=True)
    core = Core(args.core, args.workdir, args.verbose)
    try:
        core.carregar(args.rom)
    except RuntimeError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 3
    for item in args.input:
        f, b, *hold = item.split(":")
        core.agenda[BOTOES[b.upper()]] = (int(f), int(f) + (int(hold[0]) if hold else 8))
    snaps = {}
    for item in args.snap:
        f, png = item.split("=", 1)
        snaps[int(f)] = Path(png)
    inicio_frames = core.frames_capturados  # load_game pode desenhar
    if args.load_state and args.load_state.is_file():
        buf = args.load_state.read_bytes()
        dbuf = C.create_string_buffer(buf)
        if core.core.retro_unserialize(C.cast(dbuf, C.c_void_p), len(buf)):
            pass
        else:
            print("aviso: unserialize falso (estado incompatível?)", flush=True)
    core.rodar(args.frames, snaps)
    if args.save_state:
        sz = core.core.retro_serialize_size()
        out = C.create_string_buffer(sz)
        if core.core.retro_serialize(C.cast(out, C.c_void_p), sz):
            args.save_state.write_bytes(out.raw)
        else:
            print("aviso: serialize falso.", flush=True)
    av = core.av

    rel = {"rom": str(args.rom), "frames_pedidos": args.frames,
           "frames_video": core.frames_capturados,
           "av_base": f"{av.geometry.base_width}x{av.geometry.base_height}",
           "fps_core": round(av.timing.fps, 3),
           "pixel_fmt": core.fmt and core.fmt[0],
           "n_logs_core": len(core.logs)}
    if args.png and core.last_rgb:
        png_write(args.png, core.w, core.h, core.last_rgb)
        rel["png"] = str(args.png)
    leituras = []
    for spec in args.mem_read:
        off_s, n_s = spec.split(":")
        off, n = int(off_s, 16), int(n_s, 16)
        data = core.memoria(args.mem_region, off, n)
        leituras.append({"off": off_s, "n": n, "hex": data.hex(" ")})
    rel["mem_reads"] = leituras
    print(json.dumps(rel, indent=2, ensure_ascii=False))
    if args.verbose and core.logs:
        print("--- últimos logs do core ---")
        for m in core.logs[-12:]:
            print(" ", m)
    logs = ROOT / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "gba_libretro_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "versao": VERSAO, "rom": str(args.rom),
                            "frames": args.frames, "video": core.frames_capturados},
                           ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
