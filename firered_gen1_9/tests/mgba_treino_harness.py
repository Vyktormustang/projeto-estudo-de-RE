"""Apoio opcional para testes mGBA. Usa ROM fornecida pelo usuário, sem saves reais.

O layout de estado é da versão mGBA libretro 0.10.5; não é um formato de save
GBA. Estados e Pokémon sintéticos ficam só na memória do processo de teste.
"""
from __future__ import annotations

import ctypes as C
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# O driver é parte do material histórico do próprio projeto (sem ROMs).
sys.path.insert(0, str(ROOT / "gba-re_project (1).zip") + "/scripts")
from gba_libretro_emu import BOTOES, VIDEO_CB, Core  # noqa: E402


class Emulator:
    def __init__(self, rom: Path, core: Path, temp: Path):
        self.core = Core(core, temp)
        self.core.carregar(rom)
        # Não capturamos telas nos testes. A API pede um callback válido.
        @VIDEO_CB
        def video(_data, _w, _h, _pitch):
            pass
        self.video = video
        self.core.core.retro_set_video_refresh(video)

    def run(self, frames: int, *buttons: str):
        self.core.inputs = {(0, 1, 0, BOTOES[b]): 1 for b in buttons}
        for _ in range(frames):
            self.core.core.retro_run()

    def pulse(self, button: str = "A", gap: int = 30):
        self.run(3, button)
        self.run(gap)

    def state(self) -> bytes:
        size = self.core.core.retro_serialize_size()
        buf = C.create_string_buffer(size)
        if not self.core.core.retro_serialize(C.cast(buf, C.c_void_p), size):
            raise RuntimeError("mGBA não serializou o estado de teste")
        return buf.raw

    def restore(self, data: bytes):
        buf = C.create_string_buffer(data)
        if not self.core.core.retro_unserialize(C.cast(buf, C.c_void_p), len(data)):
            raise RuntimeError("mGBA não restaurou o estado de teste")

    def close(self):
        self.core.core.retro_unload_game()
        self.core.core.retro_deinit()


def make_summary_fixture(f: Emulator) -> bytes:
    """Joga uma introdução determinística até o resumo do inicial (sem cheats)."""
    def r(n=1): f.run(n)
    def p(button="A", gap=60): f.pulse(button, gap)
    def loop(n, gap, checkpoints=()):
        for i in range(n):
            p("A", gap)
            if i in checkpoints: r()

    f.run(480); r(); p("START", 90); r(); loop(30, 55, {2, 5, 10, 15, 20, 25, 29})
    loop(40, 55, {4, 9, 14, 19, 24, 29, 34, 39})
    p("START", 90); loop(40, 60, {4, 9, 14, 19, 24, 29, 34, 39})
    loop(4, 60); r(); f.run(28, "RIGHT"); r(15); r(); f.run(55, "UP"); r(80); r()
    f.run(40, "UP"); r(70); r(); f.run(12, "RIGHT"); r(8); f.run(32, "UP"); r(80); r()
    f.run(9, "RIGHT"); r(7); f.run(40, "UP"); r(80); r(); f.run(8, "LEFT"); r(24); r(); r(100); r()
    f.run(40, "LEFT"); r(10); r(); f.run(60, "DOWN"); r(100); r()
    f.run(48, "LEFT"); r(8); f.run(96, "DOWN"); r(100); r()
    f.run(96, "RIGHT"); r(10); r(); f.run(160, "UP"); r(60); r()
    loop(32, 60, {5, 10, 15, 20, 25, 31}); loop(20, 60, {4, 9, 14, 19})
    f.run(16, "DOWN"); r(7); f.run(32, "RIGHT"); r(7); f.run(8, "UP"); r(10); r(); p("A", 70); r()
    loop(20, 60); r(); loop(18, 75); r(); p("A", 50)
    f.run(24, "DOWN"); r(10); r(); f.run(32, "RIGHT"); r(10); r(); f.run(6, "UP"); r(10); p("A", 60); r()
    loop(8, 70, set(range(8))); loop(10, 70, set(range(10))); p("A", 35); p("START", 100); loop(15, 70); r()
    p("START", 40); r(); p("A", 100); r(); p("A", 40); r(); p("A", 100); r(); p("RIGHT", 90); r()
    state = f.state()
    address = u32(state, offset(SUMMARY_POINTER))
    if not (0x02000000 <= address < 0x0203CC00 and state[offset(address + 0x322C)] == 1
            and state[offset(address + 0x3288)] == 2 and mon_facts(mon(state))["species"] == 1):
        raise RuntimeError("A sequência inicial não chegou ao resumo esperado; confira ROM/core mGBA 0.10.5.")
    return state


EWRAM_IN_STATE = 0x21000
PARTY = 0x0203A98C
SUMMARY_POINTER = 0x0203AC9C
SELECTED = 0x0203ACC8
CURRENT_MON = 0x32A8
# Para cada personality % 24, posições das subestruturas 0,1,2,3.
ORDER = (
    (0,1,2,3), (0,1,3,2), (0,2,1,3), (0,3,1,2), (0,2,3,1), (0,3,2,1),
    (1,0,2,3), (1,0,3,2), (2,0,1,3), (3,0,1,2), (2,0,3,1), (3,0,2,1),
    (1,2,0,3), (1,3,0,2), (2,1,0,3), (3,1,0,2), (2,3,0,1), (3,2,0,1),
    (1,2,3,0), (1,3,2,0), (2,1,3,0), (3,1,2,0), (2,3,1,0), (3,2,1,0),
)


def offset(address): return EWRAM_IN_STATE + address - 0x02000000

def u32(data, i): return struct.unpack_from("<I", data, i)[0]

def u16(data, i): return struct.unpack_from("<H", data, i)[0]

def put16(data, i, value): struct.pack_into("<H", data, i, value)

def put32(data, i, value): struct.pack_into("<I", data, i, value)


def mon(state, slot=0, work=False):
    start = offset(u32(state, offset(SUMMARY_POINTER)) + CURRENT_MON) if work else offset(PARTY + slot * 100)
    return bytearray(state[start:start + 100])


def put_mon(state, data, slot=0, work=False):
    start = offset(u32(state, offset(SUMMARY_POINTER)) + CURRENT_MON) if work else offset(PARTY + slot * 100)
    state[start:start + 100] = data


def decrypted(data):
    personality = u32(data, 0)
    key = personality ^ u32(data, 4)
    block = bytearray(48)
    for i in range(0, 48, 4): put32(block, i, u32(data, i + 32) ^ key)
    valid = (sum(struct.unpack("<24H", block)) & 0xFFFF) == u16(data, 28)
    return block, ORDER[personality % 24], valid


def mon_facts(data):
    block, order, valid = decrypted(data)
    ivbits = u32(block, order[3] * 12 + 4)
    return {
        "valid": valid, "species": u16(block, order[0] * 12),
        # ordem interna: hp, ataque, defesa, velocidade, ataque esp., defesa esp.
        "ev": list(block[order[2] * 12:order[2] * 12 + 6]),
        "iv": [(ivbits >> (5 * i)) & 31 for i in range(6)],
        "hp": u16(data, 86), "max_hp": u16(data, 88), "level": data[84],
    }


def set_ev(data, evs):
    block, order, valid = decrypted(data)
    if not valid or len(evs) != 6: raise ValueError("Pokemon de teste inválido")
    block[order[2] * 12:order[2] * 12 + 6] = bytes(evs)
    put16(data, 28, sum(struct.unpack("<24H", block)) & 0xFFFF)
    key = u32(data, 0) ^ u32(data, 4)
    for i in range(0, 48, 4): put32(data, i + 32, u32(block, i) ^ key)


def seed(fixture, evs, hp=None, max_hp=None):
    """Altera somente um estado sintético; não grava um save nem a ROM."""
    state = bytearray(fixture)
    data = mon(state)
    set_ev(data, evs)
    if hp is not None: put16(data, 86, hp)
    if max_hp is not None: put16(data, 88, max_hp)
    put_mon(state, data)
    put_mon(state, data, work=True)
    return bytes(state)


def meta(state):
    address = u32(state, offset(SUMMARY_POINTER))
    return state[offset(address + 0x3221)]
