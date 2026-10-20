"""Da' itens a um jogo em execucao, escrevendo direto na pocket da mochila.

Este script faz a coisa que esta' PROVADA: com o jogo rodando no emulador de
console do projeto, escreve `itemId` e `quantidade` no slot certo de
`SaveBlock1` e confere lendo de volta. Nao e' patch de ROM -- e' escrita em RAM
de um jogo que ja' chegou ao overworld (a bag so' existe depois que o
SaveBlock e' inicializado).

O que este script NAO faz: gerar ROM que ja' nasce com os itens. Esse caminho
continua aberto -- ver NOTAS_DE_TRABALHO.md secao 14.

Layout (medido em jogo, ver RELATORIO secao 15):

    gBagPockets = 0x0203988C        ; array de 5 entradas de 8 bytes
    entrada n   = { u32 itemSlots; u8 capacity; u8 pad[3] }
    slot m      = itemSlots + 4*m   = { u16 itemId; u16 quantidade_cifrada }
    quantidade_cifrada = qtd ^ (*(u32*)(SaveBlock2 + 0xF20) & 0xFFFF)

Por que o XOR importa: slot vazio guarda `0 ^ (chave & 0xFFFF)`, nao zero.
Gravar a quantidade "crua" faz o jogo ler um numero absurdo. Medido: com a
mochila vazia os slots liam `00 00 04 85` e a chave era `0x0E078504`.

Uso:
    python ferramentas/da_pokebolas.py ROM.gba ESTADO.state --pocket 2 --quantidade 99
    python ferramentas/da_pokebolas.py ROM.gba ESTADO.state --pocket 2 --slot 1
    python ferramentas/da_pokebolas.py ROM.gba ESTADO.state --item 1 \
        --quantidade 1 --saida NOVO.state   # persiste num estado NOVO

Sem `--slot`, o slot e' escolhido com seguranca: empilha no slot que ja'
tem o item ou usa o primeiro slot livre -- nunca sobrescreve outro item.

O estado pode ser criado com `emulador_console.salvar_estado` (ver
NOTAS_DE_TRABALHO secao 13). Sem estado, nao ha' como pular a navegacao.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole, ErroDeEmulacao  # noqa: E402

G_BAG_POCKETS = 0x0203988C
G_SAVE_BLOCK1 = 0x03005008
G_SAVE_BLOCK2 = 0x0300500C
CHAVE_EM_S2 = 0xF20
TAMANHO_ENTRADA = 8

# Nomes das pockets, na ordem do array. Medido: as cinco batem com
# SaveBlock1+0x310/0x3B8/0x430/0x464/0x54C e capacities 42/30/13/58/43.
POCKETS = {
    0: ("ITENS", 42),
    1: ("ITEM CHAVE", 30),
    2: ("POKE BOLAS", 13),
    3: ("TM/HM", 58),
    4: ("BAGAS", 43),
}


def endereco_da_pocket(emu, indice: int) -> tuple[int, int]:
    """(endereco_dos_slots, capacity) da pocket `indice`, lidos do jogo."""
    bruto = emu.ler(G_BAG_POCKETS + indice * TAMANHO_ENTRADA, TAMANHO_ENTRADA)
    slots, capacidade = struct.unpack_from("<IB", bruto, 0)
    if not 0x02000000 <= slots < 0x02040000:
        raise ErroDeEmulacao(
            f"pocket {indice}: itemSlots=0x{slots:08X} nao parece EWRAM -- "
            "o jogo chegou ao overworld?")
    return slots, capacidade


def cifrar_quantidade(quantidade: int, chave: int) -> int:
    """Quantidade como o jogo guarda: `qtd ^ (chave & 0xFFFF)`.

    Medido: com a mochila vazia os slots liam `0x8504` e a chave era
    `0x0E078504` -- `0 ^ 0x8504`. Dar 99 com essa chave grava `0x8567`.
    """
    return quantidade ^ (chave & 0xFFFF)


def chave_de_cifra(emu) -> int:
    return emu.ler_u32(emu.ler_u32(G_SAVE_BLOCK2) + CHAVE_EM_S2)


# Limite de pilha por slot na ger. 3.
MAX_QTD = 999


def ler_pocket(emu, indice: int) -> list[tuple[int, int]]:
    """Todos os slots da pocket como (itemId, quantidade) JA decifrados."""
    slots, capacidade = endereco_da_pocket(emu, indice)
    chave = chave_de_cifra(emu)
    bruto = emu.ler(slots, 4 * capacidade)
    return [(item, cifrar_quantidade(qtd_cifrada, chave))
            for item, qtd_cifrada in struct.iter_unpack("<HH", bruto)]


def decidir_slot(slots: list[tuple[int, int]], item: int,
                 quantidade: int) -> tuple[int, int]:
    """(slot, nova_quantidade_total) para ADICIONAR `quantidade` de `item`.

    Empilha no slot que ja' tem o item; senao usa o primeiro slot livre
    (itemId == 0). Nunca sobrescreve um item diferente.
    """
    if quantidade < 1:
        raise ErroDeEmulacao("quantidade a adicionar deve ser >= 1")
    for i, (item_slot, qtd_slot) in enumerate(slots):
        if item_slot == item:
            total = qtd_slot + quantidade
            if total > MAX_QTD:
                raise ErroDeEmulacao(
                    f"slot {i} ja' tem {qtd_slot}; +{quantidade} passa de {MAX_QTD}")
            return i, total
    for i, (item_slot, _) in enumerate(slots):
        if item_slot == 0:
            if quantidade > MAX_QTD:
                raise ErroDeEmulacao(f"quantidade {quantidade} passa de {MAX_QTD}")
            return i, quantidade
    raise ErroDeEmulacao("pocket cheia: nenhum slot livre nem pilha do item")


def dar_item(emu, indice_pocket: int, item: int, quantidade: int,
             slot: int = 0) -> dict:
    """Escreve o item na pocket e devolve o que foi lido de volta."""
    slots, capacidade = endereco_da_pocket(emu, indice_pocket)
    if not 0 <= slot < capacidade:
        raise ErroDeEmulacao(f"slot {slot} fora da capacidade {capacidade}")
    chave = chave_de_cifra(emu)
    cifrada = cifrar_quantidade(quantidade, chave)
    endereco = slots + 4 * slot
    emu.escrever(endereco, struct.pack("<HH", item, cifrada))
    eco = emu.ler(endereco, 4)
    item_lido, qtd_cifrada = struct.unpack("<HH", eco)
    return {
        "endereco": endereco,
        "capacidade": capacidade,
        "chave": chave,
        "item": item_lido,
        "quantidade": cifrar_quantidade(qtd_cifrada, chave),
        "bruto": eco.hex(" "),
    }


def principal(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("estado", type=Path, help="arquivo de estado do emulador")
    parser.add_argument("--rom", type=Path, required=True,
                        help="a ROM que gerou o estado (o core precisa dela para subir)")
    parser.add_argument("--core", type=Path,
                        default=Path("/home/user/gba-re/emu_patch/mgba_libretro.so"))
    parser.add_argument("--pocket", type=int, default=2, choices=sorted(POCKETS))
    parser.add_argument("--item", type=int, default=4,
                        help="1 = MASTER BALL, 4 = POKe BOLA")
    parser.add_argument("--quantidade", type=int, default=99,
                        help="sem --slot: quanto ADICIONAR; com --slot: total do slot")
    parser.add_argument("--slot", type=int, default=-1,
                        help="-1 (padrao) = empilha ou primeiro slot livre")
    parser.add_argument("--saida", type=Path,
                        help="salva o resultado neste estado NOVO (entrada intocada)")
    args = parser.parse_args(argv)

    if args.saida is not None and args.estado.resolve() == args.saida.resolve():
        print("saida deve ser diferente da entrada", file=sys.stderr)
        return 1

    emu = EmuladorConsole(args.rom, args.core, Path("/tmp/mgba-da-itens"))
    try:
        emu.carregar_estado(args.estado)
    except ErroDeEmulacao as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    nome = POCKETS[args.pocket][0]
    antes = ler_pocket(emu, args.pocket)
    print(f"antes: pocket {args.pocket} ({nome}) = "
          f"{[(i, q) for i, q in antes if i != 0] or 'vazia'}")
    if args.slot < 0:
        try:
            slot, total = decidir_slot(antes, args.item, args.quantidade)
        except ErroDeEmulacao as exc:
            print(f"erro: {exc}", file=sys.stderr)
            emu.fechar()
            return 1
    else:
        slot, total = args.slot, args.quantidade
    resultado = dar_item(emu, args.pocket, args.item, total, slot)
    print(f"pocket {args.pocket} ({nome}), slot {slot}")
    print(f"  endereco  = 0x{resultado['endereco']:08X}")
    print(f"  chave     = 0x{resultado['chave']:08X}")
    print(f"  gravado   = {resultado['bruto']}")
    print(f"  lido     -> item {resultado['item']}, quantidade {resultado['quantidade']}")
    ok = (resultado["item"] == args.item
          and resultado["quantidade"] == total)
    print("  conferencia:", "OK" if ok else "FALHOU")
    if ok and args.saida is not None:
        emu.rodar(10)
        relido = ler_pocket(emu, args.pocket)
        if relido[slot] != (args.item, total):
            print("a escrita nao pegou apos rodar -- nada foi salvo",
                  file=sys.stderr)
            emu.fechar()
            return 2
        print(f"depois (relido da RAM): "
              f"{[(i, q) for i, q in relido if i != 0]}")
        emu.salvar_estado(args.saida)
        print(f"estado salvo em {args.saida} ({args.saida.stat().st_size} bytes)")
    emu.fechar()
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(principal())
