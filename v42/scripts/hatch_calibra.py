"""Calibração da incubação V42: quantos passos a ROM aceita por segundo.

Mede, sobre o dump real do teste de eclosão (ovo já recebido, jogador no
corredor interno da creche em (23,22), location (3,15)):

  1. tiles efetivamente andados por segundo com um padrão de vaivém;
  2. se o bit 30 do IV32 (marcador de ovo) muda durante o percurso;
  3. a projeção de tempo para os ~30.600 passos do ovo de 120 ciclos.

Nada aqui edita o contador de passos, o ovo ou a ROM: só caminha e lê.

    python3 -B v42/scripts/hatch_calibra.py --dump /tmp/hatch/pos_ovo.bin --seconds 60
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import time
from pathlib import Path

GEN = Path(os.environ.get("V42_GEN_DIR", "/tmp/gen19/firered_gen1_9"))
for p in (str(GEN / "tests"), str(GEN)):
    if p not in sys.path:
        sys.path.insert(0, p)

# imports do harness adiados (ver nota em hatch_probe.py): --self-test roda sem
# ROM, sem core e sem o firered_gen1_9/ extraído.
Emulator = decrypted = u32 = None
game = None


def _importar_harness():
    global Emulator, decrypted, u32, game
    from mgba_treino_harness import (  # noqa: E402
        Emulator as _E, decrypted as _d, u32 as _u,
    )
    import test_motor_v21_gameplay_mgba as _g  # noqa: E402
    Emulator, decrypted, u32, game = _E, _d, _u, _g
    return Emulator, decrypted, u32, game

ROM = os.environ.get("COSMOG_V42_ROM")
CORE = os.environ.get("MGBA_CORE", "/tmp/mgba-lr/mgba_libretro.so")
SAMPLE = 8      # frames entre amostras de coordenada (1 tile ≈ 16 frames)
BURST = 64      # frames por rajada


def eh_ovo(mon: bytes) -> bool:
    """Marcador de ovo = bit 30 do IV32 (critério já provado na suíte)."""
    bloco, ordem, ok = decrypted(mon)
    if not ok:
        raise AssertionError("mon não decifrou")
    return bool(u32(bloco, ordem[3] * 12 + 4) & (1 << 30))


def burst(f: Emulator, button: str, frames: int = BURST, sample: int = SAMPLE):
    """Segura `button` e devolve tiles andados (por delta de coordenada)."""
    last = game.coords(f.state())
    tiles = 0
    f.run(sample, button)
    for _ in range(frames // sample - 1):
        pos = game.coords(f.state())
        tiles += abs(pos[0] - last[0]) + abs(pos[1] - last[1])
        last = pos
        f.run(sample, button)
    pos = game.coords(f.state())
    tiles += abs(pos[0] - last[0]) + abs(pos[1] - last[1])
    return tiles, pos


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        # o contador de tiles tem de somar deltas, não posições absolutas
        last, tiles = (5, 5), 0
        for pos in ((6, 5), (7, 5), (6, 5)):
            tiles += abs(pos[0] - last[0]) + abs(pos[1] - last[1])
            last = pos
        assert tiles == 3, tiles
        print("self-test OK")
        return 0

    _importar_harness()
    if not a.dump:
        print("informe --dump")
        return 2
    if not ROM:
        print("defina COSMOG_V42_ROM")
        return 2

    data = Path(a.dump).read_bytes()
    f = Emulator(Path(ROM), Path(CORE), Path("/tmp/calibra_hatch"))
    f.restore(data)

    mon = game.party_slot(f.state(), 1)
    assert eh_ovo(mon), "o dump não começa com ovo no slot 1"
    print(f"inicio: coords={game.coords(f.state())} "
          f"location={game.location(f.state())} ovo=1", flush=True)

    total = 0
    t0 = time.perf_counter()
    phase = 0
    hatched = False
    while time.perf_counter() - t0 < a.seconds:
        direction = "RIGHT" if phase % 2 == 0 else "LEFT"
        tiles, _pos = burst(f, direction)
        total += tiles
        phase += 1
        if phase % 8 == 0:
            st = f.state()
            if not eh_ovo(game.party_slot(st, 1)):
                hatched = True
                break
            dt = time.perf_counter() - t0
            print(f"t={dt:6.1f}s tiles={total:6d} taxa={total/dt:6.1f} tiles/s "
                  f"coords={game.coords(st)}", flush=True)

    dt = time.perf_counter() - t0
    taxa = total / dt if dt else 0
    print(f"\nresultado: {total} tiles em {dt:.1f}s = {taxa:.1f} tiles/s", flush=True)
    print(f"eclodiu? {hatched}", flush=True)
    if taxa:
        print(f"projecao para 30600 passos: {30600/taxa/60:.1f} min", flush=True)
    f.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
