"""Mostra o time decifrado de um estado salvo (somente leitura).

    python3 ferramentas/mostrar_time.py ROM.gba CORE.so ESTADO.state

Le' a contagem em 0x02024029 e as estruturas em 0x02024284 (medidos,
§19.2) e decifra cada Pokemon com gbadecomp.pokemon -- incluindo a prova
cruzada de atributos quando a especie esta' em BASES_CONHECIDAS.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole  # noqa: E402
from gbadecomp.pokemon import (  # noqa: E402
    BASES_CONHECIDAS, END_CONTAGEM, END_TIME, MAX_TIME, TAMANHO, ler_pokemon,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("core", type=Path)
    parser.add_argument("estado", type=Path)
    args = parser.parse_args()

    emu = EmuladorConsole(args.rom, args.core)
    emu.carregar_estado(args.estado)
    emu.rodar(3)
    quantidade = emu.ler(END_CONTAGEM, 1)[0]
    print(f"Pokemon no time: {quantidade}")
    for i in range(min(quantidade, MAX_TIME)):
        mon = ler_pokemon(emu.ler(END_TIME + i * TAMANHO, TAMANHO))
        hp, hp_max = mon.hp
        print(f"\n[{i}] especie {mon.especie} nv{mon.nivel} HP {hp}/{hp_max} "
              f"integro={mon.integro()}")
        print(f"    personalidade={mon.personalidade:#010x} otId={mon.ot_id:#010x} "
              f"natureza={mon.natureza}")
        print(f"    exp={mon.experiencia} amizade={mon.amizade} "
              f"item={mon.item_segurado} golpes={mon.golpes} pp={mon.pps}")
        print(f"    IVs (HP,Atk,Def,Vel,AtkEsp,DefEsp)={mon.ivs} EVs={mon.evs}")
        print(f"    atributos gravados={mon.atributos}")
        if mon.especie in BASES_CONHECIDAS:
            calc = mon.recalcular(BASES_CONHECIDAS[mon.especie])
            ok = calc[0] == hp_max and calc[1:] == mon.atributos
            print(f"    recalculados dos IVs={calc} -> "
                  f"{'BATE com o jogo' if ok else 'DIVERGE'}")
    emu.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
