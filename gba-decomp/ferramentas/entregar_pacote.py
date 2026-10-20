"""Busca o pacote do Oak no Mercado de Viridian e o entrega -- para com a Pokedex.

Parte do estado da secao 23 (`viridian_masterball.state`, fora do Git):
jogador em Viridian `(3,1)` em `(25,39)`, Bulbasaur modificado nv10 com
IVs 31 e a Master Ball (item 1) sozinha na pocket POKE BOLAS. O roteiro
e' o do jogo, sem nenhuma escrita em RAM:

1. Viridian ate' a frente do Mercado `(36,20)` e porta `(36,19)`;
2. a cena do Mercado e' automatica ao entrar (script ON_FRAME); o
   jogador termina em `(4,3)` e o pacote aparece na pocket ITEM CHAVE;
3. volta pela Rota 1 ate' Pallet, entra no laboratorio `(4,3)` e fala
   com Oak `(6,3)` parado em `(6,4)`;
4. a cena de entrega remove o pacote e da' 5 Poke Balls (item 4);
5. sai do laboratorio e salva um estado NOVO em Pallet `(16,14)`.

O que foi medido no caminho (secao 26 das NOTAS):

- o explorador Manhattan puro de `(25,39)` a `(36,20)` NAO basta em
  Viridian: ele vai para o sudeste e fica preso entre canteiros e
  desniveis (parou em `(35,33)` no limite de 360 passos). O caminho
  que funciona segue as ruas: norte ate' `y<=32`, esquerda ate'
  `x<=22` (avenida a oeste do Centro Pokemon), norte ate' `y<=21`,
  direita ate' `x>=36` e um passo ao norte ate' `(36,20)`;
- o interior do Mercado e' o mapa `(5,3)`; entra-se em `(4,7)` e a
  saida e' o tapete ao sul de `(4,6)`;
- `ITEM_OAKS_PARCEL = 349`, lido da propria bolsa depois da cena
  (pocket ITEM CHAVE `{349: 1}`), nao apenas da tabela do pret;
- cruzar ao sul de `(25,39)` cai na Rota 1 `(3,19)` em `(13,0)`; o
  explorador com custo `-y` chega a Pallet `(3,0)` em `(12,0)`;
- na execucao medida nao houve batalha na volta; se houver, vale a
  politica de fuga ja' embutida em `passo`/`Travessia`.

Uso:

    python3 ferramentas/entregar_pacote.py ROM.gba CORE.so \
        --estado /fora/do/repo/viridian_masterball.state \
        --estado-saida /fora/do/repo/pacote_entregue.state \
        --png-prefixo /fora/do/repo/pacote

ROM/estados/PNGs nao vao para o Git. Valide o estado salvo num
processo novo (menu START com a opcao POKEdex) antes de usa-lo como
ponto de partida.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole, ErroDeEmulacao  # noqa: E402
from gbadecomp.pokemon import END_TIME, TAMANHO, ler_pokemon  # noqa: E402
from ferramentas.da_pokebolas import ler_pocket  # noqa: E402
from ferramentas.ir_ao_inicial import (  # noqa: E402
    espera_warp, livre, mapa, onde, passo, pos,
)
from ferramentas.ir_a_viridian import LAB, PALLET, ROTA1, VIRIDIAN, Travessia  # noqa: E402

MERCADO = (5, 3)          # medido ao cruzar a porta (36,19)
ITEM_MASTER_BALL = 1
ITEM_POKE_BALL = 4
ITEM_PACOTE_OAK = 349     # ITEM_OAKS_PARCEL, confirmado pela bolsa

# Warps/gatilhos de Viridian a evitar (pret map.json, conferidos no mapa):
# Centro Pokemon, casa, ginasio, escola, Mercado, RoadBlocked,
# GymDoorLocked e os dois tiles do tutorial do velho.
PORTAS_VIRIDIAN = frozenset({
    (26, 26), (25, 11), (36, 10), (25, 18), (36, 19),
    (22, 11), (36, 11), (20, 8), (22, 8),
})
PORTAS_PALLET = frozenset({(6, 7), (15, 7), (16, 13)})
SAIDAS_LAB = frozenset({(5, 12), (6, 12), (7, 12)})


class ErroEntrega(Exception):
    pass


def itens(emu, indice):
    return {item: qtd for item, qtd in ler_pocket(emu, indice) if item != 0}


def resumo(emu, rotulo):
    mon = ler_pokemon(emu.ler(END_TIME, TAMANHO))
    print(f'[{rotulo}] {onde(emu)}')
    print(f'  Pokemon: esp={mon.especie} nv={mon.nivel} exp={mon.experiencia} '
          f'HP={mon.hp} IVs={mon.ivs} integro={mon.integro()}')
    print(f'  chave={itens(emu, 1)} bolas={itens(emu, 2)}')
    return mon


def exigir(condicao, mensagem):
    if not condicao:
        raise ErroEntrega(mensagem)


def executar(emu, foto, checkpoint, estado_saida):
    trav = Travessia(emu, foto=foto)

    resumo(emu, 'inicio')
    exigir(mapa(emu) == VIRIDIAN and pos(emu) == (25, 39),
           f'estado inicial fora do esperado: {onde(emu)}')
    exigir(ITEM_PACOTE_OAK not in itens(emu, 1),
           'o pacote ja esta na bolsa; nada a buscar')
    bolas_inicio = itens(emu, 2)
    exigir(bolas_inicio.get(ITEM_MASTER_BALL) == 1,
           f'Master Ball ausente no inicio: {bolas_inicio}')
    pokebolas_inicio = bolas_inicio.get(ITEM_POKE_BALL, 0)

    # --- Viridian -> frente do Mercado (pernas cardeais nas ruas) ---
    def perna(direcao, condicao, maxp, rotulo, waypoint):
        ok = trav.caminhar(direcao, condicao, maxp=maxp, rotulo=rotulo)
        if not ok:
            print(f'  [{rotulo}] rua bloqueada; tentando explorador ate '
                  f'{waypoint}: {onde(emu)}')
            ok = trav.ir_para(waypoint, VIRIDIAN, rotulo,
                              evitar=PORTAS_VIRIDIAN)
        foto(rotulo)
        print(f'  [{rotulo}] ok={ok}: {onde(emu)}')
        return ok

    exigir(perna('UP', lambda p, m: p[1] <= 32, 12,
                 'viridian-entrada', (24, 32)), onde(emu))
    exigir(perna('LEFT', lambda p, m: p[0] <= 22, 6,
                 'viridian-avenida', (22, 32)), onde(emu))
    exigir(perna('UP', lambda p, m: p[1] <= 21, 15,
                 'viridian-norte', (22, 21)), onde(emu))
    exigir(perna('RIGHT', lambda p, m: p[0] >= 36, 18,
                 'viridian-transversal', (36, 21)), onde(emu))
    if pos(emu) != (36, 20):
        exigir(perna('UP', lambda p, m: p == (36, 20), 3,
                     'mercado_frente', (36, 20)), onde(emu))
    checkpoint('mercado_frente')

    # --- Entrar no Mercado; a cena do pacote e' automatica ---
    passo(emu, 'UP')
    if mapa(emu) == VIRIDIAN:
        espera_warp(emu, VIRIDIAN, 'mercado-porta')
    if mapa(emu) == VIRIDIAN:
        passo(emu, 'UP')
        espera_warp(emu, VIRIDIAN, 'mercado-porta-2')
    exigir(mapa(emu) == MERCADO, f'nao entrou no mercado: {onde(emu)}')
    print(f'dentro do mercado: {onde(emu)}')
    emu.rodar(300)
    for rodada in range(6):
        trav.destravar_dialogo(160, testar_antes=False)
        chave = itens(emu, 1)
        print(f'  [mercado rodada {rodada}] chave={chave} {onde(emu)}')
        if ITEM_PACOTE_OAK in chave:
            break
    exigir(itens(emu, 1).get(ITEM_PACOTE_OAK) == 1,
           f'pacote nao recebido: {itens(emu, 1)}')
    foto('mercado_pacote')
    checkpoint('mercado')
    resumo(emu, 'com pacote')

    # --- Sair do Mercado e voltar a Pallet ---
    exigir(trav.ir_para((4, 6), MERCADO, 'mercado-saida'), onde(emu))
    exigir(trav.caminhar('DOWN', lambda p, m: m == VIRIDIAN, maxp=3,
                         rotulo='mercado-fora'), onde(emu))
    emu.rodar(150)
    foto('viridian_volta')
    exigir(trav.ir_para((25, 39), VIRIDIAN, 'viridian-sul',
                        evitar=PORTAS_VIRIDIAN), onde(emu))
    exigir(trav.caminhar('DOWN', lambda p, m: m == ROTA1, maxp=3,
                         rotulo='viridian-rota1'), onde(emu))
    emu.rodar(120)
    checkpoint('rota1')
    resumo(emu, 'rota1 volta')

    resultado = trav.explorador(
        criterio_fim=lambda p, m: m == PALLET,
        custo=lambda x, y: -y,
        rotulo='rota1-sul',
        max_passos=1400,
    )
    exigir(resultado == 'chegou' and mapa(emu) == PALLET, onde(emu))
    emu.rodar(150)
    foto('pallet_volta')
    checkpoint('pallet')
    resumo(emu, 'pallet')

    # --- Pallet: reverso do caminho medido ate' a frente do lab ---
    if pos(emu)[1] < 3:
        trav.caminhar('DOWN', lambda p, m: p[1] >= 3, maxp=3,
                      rotulo='pallet-y3')
    if pos(emu) != (13, 3):
        trav.ir_para((13, 3), PALLET, 'pallet-col13', evitar=PORTAS_PALLET)
    trav.caminhar('LEFT', lambda p, m: p[0] <= 12, maxp=3, rotulo='pallet-x12')
    trav.caminhar('DOWN', lambda p, m: p[1] >= 14, maxp=14,
                  rotulo='pallet-sul12')
    trav.caminhar('RIGHT', lambda p, m: p[0] >= 16, maxp=6, rotulo='pallet-lab')
    if pos(emu) != (16, 14):
        exigir(trav.ir_para((16, 14), PALLET, 'pallet-lab-final',
                            evitar=PORTAS_PALLET), onde(emu))
    foto('lab_frente')

    for _ in range(3):
        if mapa(emu) == LAB:
            break
        passo(emu, 'UP')
        espera_warp(emu, PALLET, 'lab-porta')
    exigir(mapa(emu) == LAB, f'nao entrou no lab: {onde(emu)}')
    emu.rodar(150)
    foto('lab_dentro')
    checkpoint('lab')

    # --- Falar com Oak em (6,3), parado em (6,4) olhando ao norte ---
    exigir(trav.ir_para((6, 4), LAB, 'lab-oak', evitar=SAIDAS_LAB), onde(emu))
    passo(emu, 'UP')  # bloqueado pelo Oak/mesa: so' vira para o norte
    foto('lab_antes_fala')
    meta_bolas = pokebolas_inicio + 5
    for rodada in range(10):
        trav.destravar_dialogo(200, testar_antes=False)
        chave, bolas = itens(emu, 1), itens(emu, 2)
        print(f'  [entrega rodada {rodada}] chave={chave} bolas={bolas} '
              f'{onde(emu)}')
        if ITEM_PACOTE_OAK not in chave and bolas.get(ITEM_POKE_BALL, 0) >= meta_bolas:
            emu.rodar(240)
            if livre(emu):
                break
    chave, bolas = itens(emu, 1), itens(emu, 2)
    exigir(ITEM_PACOTE_OAK not in chave, f'pacote ainda na bolsa: {chave}')
    exigir(bolas.get(ITEM_MASTER_BALL) == 1
           and bolas.get(ITEM_POKE_BALL, 0) >= meta_bolas,
           f'bolas inesperadas apos a entrega: {bolas}')
    foto('lab_entregue')

    exigir(trav.sair_do_lab(), onde(emu))
    emu.rodar(180)
    mon = resumo(emu, 'final')
    exigir(mapa(emu) == PALLET, onde(emu))
    exigir(mon.integro() and mon.especie == 1 and mon.nivel == 10
           and mon.ivs == (31, 31, 31, 31, 31, 31),
           f'Pokemon final inesperado: {mon}')
    foto('pallet_pokedex')
    emu.salvar_estado(estado_saida)
    return estado_saida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('rom', type=Path)
    parser.add_argument('core', type=Path)
    parser.add_argument('--estado', type=Path, required=True,
                        help='estado em Viridian (25,39) com a Master Ball')
    parser.add_argument('--estado-saida', type=Path, required=True,
                        help='estado NOVO salvo em Pallet apos a entrega')
    parser.add_argument('--png-prefixo', type=Path,
                        help='prefixo das fotos de evidencia')
    parser.add_argument('--checkpoints', type=Path,
                        help='pasta para pacote_checkpoint_*.state')
    parser.add_argument('--dir-trabalho', type=Path,
                        help='pasta de trabalho do core (padrao do emulador)')
    args = parser.parse_args()

    if args.estado_saida.resolve() == args.estado.resolve():
        print('a saida nao pode sobrescrever o estado de entrada',
              file=sys.stderr)
        return 1
    args.estado_saida.parent.mkdir(parents=True, exist_ok=True)
    if args.checkpoints:
        args.checkpoints.mkdir(parents=True, exist_ok=True)

    emu = (EmuladorConsole(args.rom, args.core, args.dir_trabalho)
           if args.dir_trabalho else EmuladorConsole(args.rom, args.core))
    try:
        emu.carregar_estado(args.estado)
        emu.rodar(90)

        def foto(nome):
            if args.png_prefixo:
                destino = args.png_prefixo.with_name(
                    f'{args.png_prefixo.name}_{nome}.png')
                destino.parent.mkdir(parents=True, exist_ok=True)
                emu.salvar_png(destino)
                md5 = hashlib.md5(emu.quadro).hexdigest()[:8]
                print(f'foto {destino.name} {md5}: {onde(emu)}')

        def checkpoint(nome):
            if args.checkpoints:
                emu.salvar_estado(args.checkpoints
                                  / f'pacote_checkpoint_{nome}.state')

        saida = executar(emu, foto, checkpoint, args.estado_saida)
    except (ErroEntrega, ErroDeEmulacao) as erro:
        print(f'FALHA: {erro}; {onde(emu)}', file=sys.stderr)
        return 1
    finally:
        emu.fechar()

    dados = saida.read_bytes()
    print(f'OK: {saida} ({len(dados)} bytes) '
          f'sha256={hashlib.sha256(dados).hexdigest()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
