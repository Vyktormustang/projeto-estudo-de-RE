"""Da' um golpe a um Pokemon do time, editando a RAM com seguranca.

    python3 ferramentas/dar_golpe.py ROM.gba CORE.so ENTRA.state SAI.state \
        --slot 0 --posicao 2 --golpe 73 --pp 10

Carrega o estado, edita atrave's de gbadecomp.pokemon (que recifra os 48
bytes e recalcula o checksum -- sem isso o jogo marca o Pokemon como
Bad Egg), escreve os 100 bytes de volta em 0x02024284+slot*100, deixa o
jogo rodar alguns quadros e salva o estado de saida. O estado de ENTRADA
nao e' tocado. Confira o resultado com ferramentas/mostrar_time.py e,
antes de confiar, abra o jogo: o Pokemon deve aparecer normal no time.

Advertencia honesta: isto edita a RAM do estado, nao o save do cartucho
-- quem persiste e' o proprio jogo, se voce salvar por ele depois.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole  # noqa: E402
from gbadecomp.pokemon import END_TIME, TAMANHO, ler_pokemon  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("core", type=Path)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--slot", type=int, default=0)
    parser.add_argument("--posicao", type=int, required=True,
                        help="posicao do golpe, 0..3")
    parser.add_argument("--golpe", type=int, required=True,
                        help="id do golpe (ex.: 73)")
    parser.add_argument("--pp", type=int, required=True,
                        help="PP atual a gravar (use o PP base do golpe)")
    args = parser.parse_args()

    endereco = END_TIME + args.slot * TAMANHO
    emu = EmuladorConsole(args.rom, args.core)
    emu.carregar_estado(args.entrada)
    emu.rodar(3)

    mon = ler_pokemon(emu.ler(endereco, TAMANHO))
    print(f"antes: especie {mon.especie} nv{mon.nivel} "
          f"golpes={mon.golpes} pp={mon.pps} integro={mon.integro()}")
    mon.definir_golpe(args.posicao, args.golpe, args.pp)
    assert mon.integro()
    emu.escrever(endereco, mon.serializar())
    emu.rodar(10)

    relido = ler_pokemon(emu.ler(endereco, TAMANHO))
    print(f"depois (relido da RAM): golpes={relido.golpes} pp={relido.pps} "
          f"integro={relido.integro()}")
    if relido.golpes[args.posicao] != args.golpe or not relido.integro():
        print("a escrita NAO pegou -- nada foi salvo", file=sys.stderr)
        return 1
    emu.salvar_estado(args.saida)
    print(f"estado salvo em {args.saida} ({args.saida.stat().st_size} bytes)")
    emu.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
