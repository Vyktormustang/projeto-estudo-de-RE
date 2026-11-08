"""Diagnóstico do caminhador da eclosão V42 — por que cada passo custa ~2,4 s.

Hipótese a testar: `step_once` roda até 180 frames por passo e falha quando
`coords` não muda. Se o personagem estiver encostado numa parede (ou a direção
escolhida não for livre), TODO passo queima o orçamento inteiro de 180 frames.

Este script NÃO altera a ROM nem o ovo. Ele só mede tempos e reproduz o
comportamento do caminhador para que o conserto seja baseado em dado, não em
palpite.

    COSMOG_V42_ROM=... MGBA_CORE=... PYTHONPATH=harness:.:tests \\
      python3 -B v42/scripts/diag_hatch_walk.py --steps 24
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = Path(os.environ.get("V42_GEN_DIR", "/tmp/gen19/firered_gen1_9"))
for p in (str(GEN / "tests"), str(GEN)):
    if p not in sys.path:
        sys.path.insert(0, p)

# imports do harness adiados (ver nota em hatch_probe.py): --self-test roda sem
# ROM, sem core e sem o firered_gen1_9/ extraído.
Emulator = offset = None
game = None


def _importar_harness():
    global Emulator, offset, game
    from mgba_treino_harness import Emulator as _E, offset as _o  # noqa: E402
    import test_motor_v21_gameplay_mgba as _g  # noqa: E402
    Emulator, offset, game = _E, _o, _g
    return Emulator, offset, game

ROM = os.environ.get("COSMOG_V42_ROM")
CORE = os.environ.get("MGBA_CORE", "/tmp/mgba-lr/mgba_libretro.so")
def read_ewram(f: Emulator) -> bytes:
    """Lê a EWRAM inteira (128 KB) do core, sem serializar o estado.

    Usado só para diagnóstico de tempo: se isso for muito mais barato que
    `state()`, o caminhador pode ser reescrito sobre esta via.
    """
    import ctypes as C
    lib = f.core.core
    lib.retro_get_memory_data.restype = C.c_void_p
    lib.retro_get_memory_data.argtypes = [C.c_uint]
    lib.retro_get_memory_size.restype = C.c_size_t
    lib.retro_get_memory_size.argtypes = [C.c_uint]
    ptr = lib.retro_get_memory_data(0)
    size = lib.retro_get_memory_size(0)
    return C.string_at(ptr, size)


# Valor REAL medido do motor (game.OBJECTS = 0x02021B24). O fallback anterior
# (0x02020630) estava errado: só apareceu porque o self-test passou a comparar
# com o módulo carregado — é exactamente para isso que a conferência existe.
OBJECTS_MOTOR = 0x02021B24


def coords_ewram(ew: bytes, objects: int | None = None):
    """`game.coords` sobre a EWRAM crua.

    `offset(addr)` = EWRAM_IN_STATE + addr - 0x02000000 no estado serializado;
    na EWRAM lida direto do core o endereço vira só addr - 0x02000000.

    `objects` permite usar o offset da tabela de objetos sem depender do módulo
    `game` (o self-test roda sem o motor extraído).
    """
    if objects is None:
        objects = game.OBJECTS if game is not None else OBJECTS_MOTOR
    return struct.unpack_from("<hh", ew, objects - 0x02000000 + 16)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=24)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        # o self-test roda SEM o motor extraído, então o offset vem de uma
        # constante local (mesmo valor de game.OBJECTS) e não do módulo `game`.
        # Se o motor estiver disponível, confere-se que os dois coincidem.
        OBJECTS_FALLBACK = OBJECTS_MOTOR
        try:
            _importar_harness()
            objects = game.OBJECTS
            if objects != OBJECTS_FALLBACK:
                print(f"[aviso] game.OBJECTS={objects:#x} difere do fallback "
                      f"{OBJECTS_FALLBACK:#x}")
        except Exception:
            objects = OBJECTS_FALLBACK
        print("self-test: coords_ewram sobre buffer sintético")
        buf = bytearray(0x40000)
        struct.pack_into("<hh", buf, objects - 0x02000000 + 16, 7, -3)
        assert coords_ewram(bytes(buf), objects) == (7, -3), coords_ewram(bytes(buf), objects)
        print("self-test OK")
        return 0

    _importar_harness()
    if not ROM:
        print("defina COSMOG_V42_ROM")
        return 2

    f = Emulator(Path(ROM), Path(CORE), Path("/tmp/diag_hatch"))
    f.run(120)

    # custos básicos
    n = 30
    t = time.perf_counter()
    for _ in range(n):
        f.run(1)
    t_run = (time.perf_counter() - t) / n
    t = time.perf_counter()
    for _ in range(n):
        f.state()
    t_state = (time.perf_counter() - t) / n
    t = time.perf_counter()
    for _ in range(n):
        read_ewram(f)
    t_ew = (time.perf_counter() - t) / n
    print(f"custo: run(1)={t_run*1000:.3f} ms  state()={t_state*1000:.3f} ms  "
          f"ewram={t_ew*1000:.3f} ms", flush=True)

    same = 0
    divergencias = 0
    for i in range(a.steps):
        origin_s = game.coords(f.state())
        origin_e = coords_ewram(read_ewram(f))
        if origin_s != origin_e:      # as duas vias devem concordar
            divergencias += 1
        t0 = time.perf_counter()
        frames = 0
        moved = False
        origin = origin_s
        while frames < 180:
            f.run(1)
            frames += 1
            if game.coords(f.state()) != origin:
                moved = True
                break
        dt = time.perf_counter() - t0
        if not moved:
            same += 1
        print(f"passo {i:3d}: mov={str(moved):5s} frames={frames:3d} "
              f"{dt*1000:7.0f} ms  pos={origin}", flush=True)
    print(f"divergencias state x ewram: {divergencias}", flush=True)
    print(f"resumo: {same}/{a.steps} passos travados "
          f"(custo de um travado = 180 frames ≈ {180*t_run*1000:.0f} ms piso)", flush=True)
    f.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
