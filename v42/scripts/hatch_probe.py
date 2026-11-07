"""Sonda da eclosão V42: onde o jogador está e como sair da casa da creche.

Contexto (dado, não suposição): no teste de eclosão, depois de receber o ovo, o
jogador fica em `location == (3, 15)`, `coords == (23, 22)` — interior da casa da
creche. O caminhador antigo alternava RIGHT/LEFT ali dentro, batendo na parede e
queimando 180 frames por passo (a origem dos ~2,4 s/passo).

Esta sonda NÃO altera a ROM, o ovo nem o contador de ciclos. Ela só restaura um
dump de estado já obtido (`COSMOG_HATCH_DUMP` do teste de eclosão) e mede:
  1. quantos passos cada direção rende antes de travar;
  2. se dá para sair para o mapa aberto e qual a taxa de passo lá fora.

    python3 -B v42/scripts/hatch_probe.py --dump /tmp/hatch/pos_ovo.bin
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

GEN = Path(os.environ.get("V42_GEN_DIR", "/tmp/gen19/firered_gen1_9"))
for p in (str(GEN / "tests"), str(GEN)):
    if p not in sys.path:
        sys.path.insert(0, p)

# imports do harness adiados: sem eles (fora de um checkout do motor, ex.:
# --self-test no CI deste repo) o módulo nem carrega. `--self-test` valida a
# aritmética sem precisar de ROM, core ou do firered_gen1_9/ extraído.
Emulator = None
game = None


def _importar_harness():
    global Emulator, game
    from mgba_treino_harness import Emulator as _E  # noqa: E402
    import test_motor_v21_gameplay_mgba as _g  # noqa: E402
    Emulator, game = _E, _g
    return Emulator, game

ROM = os.environ.get("COSMOG_V42_ROM")
CORE = os.environ.get("MGBA_CORE", "/tmp/mgba-lr/mgba_libretro.so")
SAMPLE = 8          # frames entre amostragens (1 tile ≈ 16 frames andando)
BUCKET = 64         # frames por rajada de uma direção
BOTOES = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}


def burst(f: Emulator, button: str, frames: int = BUCKET, sample: int = SAMPLE):
    """Segura `button` por `frames` e devolve (tiles_andados, pos_final, custo_s).

    Conta tiles pela variação de coordenada amostrada; não serializa o estado
    inteiro, só chama `state()` a cada `sample` frames para ler `coords`.
    """
    t0 = time.perf_counter()
    pos0 = game.coords(f.state())
    last = pos0
    tiles = 0
    f.run(sample, button)
    for _ in range(frames // sample - 1):
        pos = game.coords(f.state())
        tiles += abs(pos[0] - last[0]) + abs(pos[1] - last[1])
        last = pos
        f.run(sample, button)
    pos = game.coords(f.state())
    tiles += abs(pos[0] - last[0]) + abs(pos[1] - last[1])
    return tiles, pos, time.perf_counter() - t0


def console(f: Emulator, label: str) -> None:
    st = f.state()
    print(f"  {label}: coords={game.coords(st)} location={game.location(st)}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--bursts", type=int, default=6)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        # valida a aritmética do contador sem ROM
        tiles = 0
        last = (10, 10)
        for pos in ((11, 10), (12, 10), (12, 11)):
            tiles += abs(pos[0] - last[0]) + abs(pos[1] - last[1])
            last = pos
        assert tiles == 3, tiles
        assert DELTA["DOWN"] == (0, 1)
        print("self-test OK")
        return 0

    _importar_harness()
    if not a.dump:
        print("informe --dump (estado salvo por COSMOG_HATCH_DUMP)")
        return 2
    if not ROM:
        print("defina COSMOG_V42_ROM")
        return 2

    data = Path(a.dump).read_bytes()
    f = Emulator(Path(ROM), Path(CORE), Path("/tmp/probe_hatch"))
    f.restore(data)
    print(f"dump restaurado: {len(data)} bytes", flush=True)
    console(f, "inicio")

    # 1) taxa de passo por direção, no estado atual (interior da casa)
    print("-- rajadas dentro da casa --", flush=True)
    for b in BOTOES:
        tiles, pos, dt = burst(f, b)
        print(f"  {b:5s}: tiles={tiles} pos={pos} {dt*1000:6.0f} ms "
              f"({dt/max(tiles,1)*1000:5.0f} ms/tile)", flush=True)
        f.restore(data)

    # 2) tentar sair: DOWN repetido até a locação mudar (porta no sul)
    print("-- tentando sair para o mapa aberto --", flush=True)
    for i in range(a.bursts):
        tiles, pos, _dt = burst(f, "DOWN")
        st = f.state()
        print(f"  rajada DOWN {i}: tiles={tiles} coords={game.coords(st)} "
              f"location={game.location(st)}", flush=True)
        if tiles == 0:
            print("  -> travou indo DOWN", flush=True)
            break

    print("-- taxa de passo no estado atual (pós-tentativa) --", flush=True)
    for b in BOTOES:
        tiles, pos, dt = burst(f, b)
        print(f"  {b:5s}: tiles={tiles} pos={pos} {dt*1000:6.0f} ms "
              f"({dt/max(tiles,1)*1000:5.0f} ms/tile)", flush=True)

    f.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
