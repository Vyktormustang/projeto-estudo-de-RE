"""Modifica EXP/IVs de um Pokemon do time e sincroniza nivel/HP/atributos.

    python3 ferramentas/modificar_pokemon.py ROM.gba CORE.so ENTRA.state \
        SAI.state --ivs 31,31,31,31,31,31 --exp 560 --nivel 10

As edicoes cifradas passam por gbadecomp.pokemon (XOR + checksum refeitos).
Quando IVs ou nivel mudam, os campos derivados do time (nivel, HP atual/
maximo e os 5 atributos) sao recalculados pelas formulas da ger. 3 e o
Pokemon e' gravado curado. A sincronizacao so' e' feita para especies em
BASES_CONHECIDAS (hoje Bulbasaur) e a EXP/nivel usam a curva medio-lenta.
O estado de ENTRADA nunca e' tocado.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole  # noqa: E402
from gbadecomp.pokemon import (  # noqa: E402
    BASES_CONHECIDAS, END_CONTAGEM, END_TIME, TAMANHO,
    exp_minima_medio_lento, ler_pokemon,
)


def _seis(valores: str) -> tuple[int, ...]:
    partes = tuple(int(p.strip()) for p in valores.split(","))
    if len(partes) != 6:
        raise argparse.ArgumentTypeError("informe 6 valores separados por virgula")
    return partes


def _resumo(rotulo: str, mon) -> None:
    hp, hp_max = mon.hp
    print(f"{rotulo}: especie {mon.especie} nv{mon.nivel} HP {hp}/{hp_max}")
    print(f"    exp={mon.experiencia} IVs={mon.ivs} EVs={mon.evs}")
    print(f"    atributos={mon.atributos} golpes={mon.golpes} "
          f"integro={mon.integro()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("core", type=Path)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--slot", type=int, default=0)
    parser.add_argument("--ivs", type=_seis,
                        help="HP,Atk,Def,Vel,AtkEsp,DefEsp; cada um 0..31")
    parser.add_argument("--exp", type=int, help="experiencia total")
    parser.add_argument("--nivel", type=int, help="nivel final, 1..100")
    args = parser.parse_args()

    if args.entrada.resolve() == args.saida.resolve():
        print("saida deve ser diferente da entrada", file=sys.stderr)
        return 1
    if args.ivs is None and args.exp is None and args.nivel is None:
        print("nada a modificar: use --ivs, --exp e/ou --nivel", file=sys.stderr)
        return 1

    emu = EmuladorConsole(args.rom, args.core)
    emu.carregar_estado(args.entrada)
    emu.rodar(3)
    quantidade = emu.ler(END_CONTAGEM, 1)[0]
    if not 0 <= args.slot < quantidade:
        print(f"slot {args.slot} invalido; time tem {quantidade} Pokemon",
              file=sys.stderr)
        emu.fechar()
        return 1

    endereco = END_TIME + args.slot * TAMANHO
    mon = ler_pokemon(emu.ler(endereco, TAMANHO))
    _resumo("antes", mon)
    if not mon.integro():
        print("Pokemon de entrada nao esta integro; nada foi alterado",
              file=sys.stderr)
        emu.fechar()
        return 1

    nivel_final = args.nivel if args.nivel is not None else mon.nivel
    exp_final = args.exp if args.exp is not None else mon.experiencia
    sincronizar = args.ivs is not None or args.nivel is not None
    bases = BASES_CONHECIDAS.get(mon.especie)
    if sincronizar:
        if bases is None:
            print(f"sem bases conhecidas para especie {mon.especie}; "
                  "nao sincronizo atributos", file=sys.stderr)
            emu.fechar()
            return 1
        # Hoje so' o Bulbasaur e' sincronizavel; valide a curva dele.
        minimo = exp_minima_medio_lento(nivel_final)
        maximo = (exp_minima_medio_lento(nivel_final + 1) - 1
                  if nivel_final < 100 else minimo)
        if not minimo <= exp_final <= maximo:
            print(f"EXP {exp_final} nao pertence ao nivel {nivel_final} "
                  f"(faixa medio-lenta {minimo}..{maximo})", file=sys.stderr)
            emu.fechar()
            return 1

    if args.exp is not None:
        mon.definir_experiencia(args.exp)
    if args.ivs is not None:
        mon.definir_ivs(args.ivs)
    if sincronizar:
        mon.sincronizar_nivel_atributos(nivel_final, bases, curar=True)
    if not mon.integro():
        print("edicao nao ficou integra; nada foi salvo", file=sys.stderr)
        emu.fechar()
        return 1

    emu.escrever(endereco, mon.serializar())
    emu.rodar(10)

    relido = ler_pokemon(emu.ler(endereco, TAMANHO))
    _resumo("depois (relido da RAM)", relido)
    esperado = []
    if args.exp is not None:
        esperado.append(relido.experiencia == args.exp)
    if args.ivs is not None:
        esperado.append(relido.ivs == args.ivs)
    if sincronizar:
        esperado.extend((
            relido.nivel == nivel_final,
            relido.hp[0] == relido.hp[1],
            relido.recalcular(bases) == (relido.hp[1], *relido.atributos),
        ))
    if not relido.integro() or not all(esperado):
        print("a escrita nao pegou como esperado -- nada foi salvo",
              file=sys.stderr)
        emu.fechar()
        return 1

    emu.salvar_estado(args.saida)
    print(f"estado salvo em {args.saida} ({args.saida.stat().st_size} bytes)")
    emu.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
