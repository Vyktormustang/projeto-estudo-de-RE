#!/usr/bin/env python3
"""Teste de boot Gen 1-9: carrega a ROM no mGBA (libretro) e mede o que aparece na tela.

Saida: relatorio de cores por bloco de frames + PNG de cada marco.
Uso: python3 boot_test.py <rom.gba> [frames]
"""
import ctypes as C
import os
import struct
import sys
import zlib
from pathlib import Path

CORE = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(os.environ.get("MGBA_CORE", "/tmp/mgba/mgba-0.10.5/build/mgba_libretro.so"))
ROM = Path(sys.argv[1])
TOTAL = int(sys.argv[2]) if len(sys.argv) > 2 else 1200


def png_write(path, w, h, rgb):
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    path.write_bytes(png)


ENV_CB = C.CFUNCTYPE(None, C.c_uint, C.c_char_p)
VID_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD_S = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUD_B = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
ISTATE = C.CFUNCTYPE(None, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
LOG = C.CFUNCTYPE(None, C.c_int)


class Core:
    def __init__(self, so):
        self.lib = C.CDLL(str(so))
        self.lib.retro_set_environment.argtypes = [C.c_void_p]
        self.lib.retro_set_video_refresh.argtypes = [C.c_void_p]
        self.lib.retro_set_audio_sample.argtypes = [C.c_void_p]
        self.lib.retro_set_audio_sample_batch.argtypes = [C.c_void_p]
        self.lib.retro_set_input_poll.argtypes = [C.c_void_p]
        self.lib.retro_set_input_state.argtypes = [C.c_void_p]
        self.lib.retro_init.argtypes = []
        self.lib.retro_load_game.argtypes = [C.c_void_p]
        self.lib.retro_run.argtypes = []
        self.lib.retro_deinit.argtypes = []
        self.last = None
        self.w = self.h = 0
        self.frames = 0
        self._cb = []
        self._env()

    def _keep(self, cb):
        self._cb.append(cb)
        return cb

    def _env(self):
        def env(cmd, data):
            if cmd == 10:  # SET_PIXEL_FORMAT
                self.fmt = C.cast(data, C.POINTER(C.c_int))[0]
                return True
            if cmd == 3:   # GET_SYSTEM_DIRECTORY
                return True
            return True
        self.cb_env = self._keep(ENV_CB(env))

        def video(data, w, h, pitch):
            if not data:
                return
            stride = w * 2
            buf = C.string_at(data, pitch * h)
            rgb = bytearray(w * h * 3)
            for y in range(h):
                base = y * pitch
                for x in range(w):
                    v = buf[base + x * 2] | (buf[base + x * 2 + 1] << 8)
                    r = ((v >> 11) & 31) * 255 // 31
                    g = ((v >> 5) & 63) * 255 // 63
                    b = (v & 31) * 255 // 31
                    o = (y * w + x) * 3
                    rgb[o] = r
                    rgb[o + 1] = g
                    rgb[o + 2] = b
            self.last = bytes(rgb)
            self.w, self.h = w, h
            self.frames += 1
        self.cb_video = self._keep(VID_CB(video))
        self.cb_aud = self._keep(AUD_S(lambda l, r: None))
        self.cb_audb = self._keep(AUD_B(lambda d, f: f))
        self.cb_poll = self._keep(POLL(lambda: None))
        def istate(port, device, index, bid):
            # botao pressionado conforme a agenda self.plano[frame]
            return 1 if bid in self.apertados else 0
        self.apertados = set()
        self.cb_istate = self._keep(ISTATE(istate))
        self.cb_log = self._keep(LOG(lambda l: None))

        self.lib.retro_set_environment(C.cast(self.cb_env, C.c_void_p))
        self.lib.retro_set_video_refresh(C.cast(self.cb_video, C.c_void_p))
        self.lib.retro_set_audio_sample(C.cast(self.cb_aud, C.c_void_p))
        self.lib.retro_set_audio_sample_batch(C.cast(self.cb_audb, C.c_void_p))
        self.lib.retro_set_input_poll(C.cast(self.cb_poll, C.c_void_p))
        self.lib.retro_set_input_state(C.cast(self.cb_istate, C.c_void_p))

    def load(self, rom: Path):
        data = rom.read_bytes()

        class GameInfo(C.Structure):
            _fields_ = [("path", C.c_char_p), ("data", C.c_void_p),
                        ("size", C.c_size_t), ("meta", C.c_char_p)]

        self.buf = C.create_string_buffer(data)
        gi = GameInfo(str(rom).encode(), C.cast(self.buf, C.c_void_p), len(data), None)
        self.lib.retro_init()
        ok = self.lib.retro_load_game(C.byref(gi))
        return ok


def analisa(rgb):
    cores = {}
    for i in range(0, len(rgb), 3):
        c = rgb[i:i + 3]
        cores[c] = cores.get(c, 0) + 1
    return cores


def main():
    core = Core(CORE)
    ok = core.load(ROM)
    print(f"retro_load_game = {ok} (1 = ok)")
    if not ok:
        return 1
    marcos = {120: "01_120f", 600: "02_600f", 1200: "03_1200f", 1800: "04_1800f",
              2400: "05_2400f", 3600: "06_3600f", 4800: "07_4800f", 6000: "08_6000f",
              7200: "09_7200f", 8400: "10_8400f"}
    saida = Path("/tmp/boot_shots")
    saida.mkdir(exist_ok=True)
    # A = 8 (RETRO_DEVICE_ID_JOYPAD_A). aperta A periodicamente para passar a intro
    for f in range(1, TOTAL + 1):
        core.apertados = {8} if (f % 90) < 6 else set()
        core.lib.retro_run()
        if f in marcos or f == TOTAL:
            cores = analisa(core.last) if core.last else {}
            top = sorted(cores.items(), key=lambda kv: -kv[1])[:3]
            print(f"frame {f:5d} | {len(cores):5d} cores | top: "
                  + ", ".join(f"#{c.hex()}x{n}" for c, n in top))
            if core.last:
                nome = marcos.get(f, f"z_{f}")
                png_write(saida / f"{nome}.png", core.w, core.h, core.last)
    print("PNGs em", saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
