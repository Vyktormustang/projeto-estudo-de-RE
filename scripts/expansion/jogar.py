#!/usr/bin/env python3
"""Leva a ROM do titulo ate o mundo do jogo, apertando botoes em sequencia.

Objetivo: provar que a ROM nao trava no titulo — passa pelo menu inicial,
escolhe "NEW GAME" e chega ao overworld.

Uso: python3 jogar.py <rom.gba> [frames_totais]
"""
import ctypes as C
import struct
import sys
import zlib
from pathlib import Path

CORE = None
ROM = Path(sys.argv[1])
TOTAL = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
SHOTS = Path("/tmp/play_shots")

# RETRO_DEVICE_ID_JOYPAD_*
B, Y, SELECT, START, UP, DOWN, LEFT, RIGHT, A = 0, 1, 2, 3, 4, 5, 6, 7, 8


def png_write(path, w, h, rgb):
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 6))
                     + chunk(b"IEND", b""))


ENV_CB = C.CFUNCTYPE(None, C.c_uint, C.c_void_p)
VID_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD_S = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUD_B = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
ISTATE = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)


def main():
    lib = C.CDLL(CORE)
    lib.retro_set_environment.argtypes = [C.c_void_p]
    lib.retro_set_video_refresh.argtypes = [C.c_void_p]
    lib.retro_set_audio_sample.argtypes = [C.c_void_p]
    lib.retro_set_audio_sample_batch.argtypes = [C.c_void_p]
    lib.retro_set_input_poll.argtypes = [C.c_void_p]
    lib.retro_set_input_state.argtypes = [C.c_void_p]
    lib.retro_init.argtypes = []
    lib.retro_load_game.argtypes = [C.c_void_p]
    lib.retro_run.argtypes = []

    estado = {"botoes": set(), "frame": 0, "rgb": None, "w": 0, "h": 0}

    def env(cmd, data):
        return None

    def video(data, w, h, pitch):
        if not data:
            return
        buf = C.string_at(data, pitch * h)
        rgb = bytearray(w * h * 3)
        for y in range(h):
            base = y * pitch
            for x in range(w):
                v = buf[base + x * 2] | (buf[base + x * 2 + 1] << 8)
                o = (y * w + x) * 3
                rgb[o] = ((v >> 11) & 31) * 255 // 31
                rgb[o + 1] = ((v >> 5) & 63) * 255 // 63
                rgb[o + 2] = (v & 31) * 255 // 31
        estado["rgb"] = bytes(rgb)
        estado["w"], estado["h"] = w, h

    def istate(port, device, index, bid):
        return 1 if bid in estado["botoes"] else 0

    cbs = [ENV_CB(env), VID_CB(video), AUD_S(lambda l, r: None),
           AUD_B(lambda d, f: f), POLL(lambda: None), ISTATE(istate)]
    lib.retro_set_environment(C.cast(cbs[0], C.c_void_p))
    lib.retro_set_video_refresh(C.cast(cbs[1], C.c_void_p))
    lib.retro_set_audio_sample(C.cast(cbs[2], C.c_void_p))
    lib.retro_set_audio_sample_batch(C.cast(cbs[3], C.c_void_p))
    lib.retro_set_input_poll(C.cast(cbs[4], C.c_void_p))
    lib.retro_set_input_state(C.cast(cbs[5], C.c_void_p))
    _ = cbs

    dados = ROM.read_bytes()

    class GameInfo(C.Structure):
        _fields_ = [("path", C.c_char_p), ("data", C.c_void_p),
                    ("size", C.c_size_t), ("meta", C.c_char_p)]

    buf = C.create_string_buffer(dados)
    gi = GameInfo(str(ROM).encode(), C.cast(buf, C.c_void_p), len(dados), None)
    lib.retro_init()
    if not lib.retro_load_game(C.byref(gi)):
        print("falha ao carregar")
        return 1

    SHOTS.mkdir(exist_ok=True)

    # agenda: (frame, botoes) - aperta por 4 frames
    agenda = []
    for f in range(1200, 9000, 240):        # passa a intro apertando A
        agenda.append((f, {A}))
    agenda += [
        (9000, {START}),                     # menu principal
        (9200, {START}),
        (9400, {A}),
        (9600, {A}),
        (9800, {A}),
        (10000, {A}),                        # "NEW GAME" / continuar
        (10400, {A}),
        (10800, {A}),
    ]
    mapa = {}
    for f, b in agenda:
        mapa[f] = b

    marcos = {1200, 3000, 6000, 9000, 9600, 10400, 12000, 15000, 18000, 20000}
    for f in range(1, TOTAL + 1):
        estado["botoes"] = mapa.get(f, set())
        lib.retro_run()
        if f in marcos and estado["rgb"]:
            cores = len(set(estado["rgb"][i:i + 3] for i in range(0, len(estado["rgb"]), 3)))
            png_write(SHOTS / f"{f:06d}.png", estado["w"], estado["h"], estado["rgb"])
            print(f"frame {f:6d} | {cores:4d} cores")
    print("PNGs em", SHOTS)
    return 0


if __name__ == "__main__":
    CORE = sys.argv[3] if len(sys.argv) > 3 else __import__("os").environ.get("MGBA_CORE", "/tmp/mgba/mgba-0.10.5/build/mgba_libretro.so")
    sys.exit(main())
