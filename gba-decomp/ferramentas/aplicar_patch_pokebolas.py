"""Patch de exemplo: começar o jogo novo com 99 Poke Balls.

Este script existe para provar que o caminho "mudar o jogo e jogar" funciona de
ponta a ponta, e para servir de molde a outros patches:

 1. monta um stub Thumb em espaco livre da ROM;
 2. troca UMA instrucao em `NewGameInitData` (`0x08054B06`) por um `bl` para o
    stub -- o `bl ResetBag` original passa a ser a primeira coisa que o stub
    chama, entao a bag e' zerada e SO' DEPOIS recebe as bolas;
 3. confere o cabecalho;
 4. roda o stub no emulador (unicorn) sobre a ROM ja' patcheada, com ponteiros
    de SaveBlock1/SaveBlock2 e a chave de cifra montados a mao, e verifica que a
    pocket de Poke Balls fica com item 4 e quantidade 99 (lida com XOR da
    chave), e que as outras quatro pockets ficam vazias.

O que fica PROVADO: o stub, executado de verdade, escreve o slot no formato do
jogo (itemId + quantidade cifrada) e nao encosta nas outras pockets; o `bl` do
hook aponta para o stub; o cabecalho continua valido.

O que NAO fica provado: que o boot real do GBA chega nesse ponto com
`gBagPockets[2].itemSlots` apontando para `SaveBlock1+0x430` -- isso e'
inferencia a partir de `SetBagPocketsPointers`, que roda no boot, mas nao foi
observado num GBA nem em emulador de console. Tambem nao foi jogado.

Uso:
    python ferramentas/aplicar_patch_pokebolas.py ROM.gba -o ROM_patch.gba
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp import patch, rom as rom_mod  # noqa: E402
from gbadecomp.verificador import Emulador  # noqa: E402

# Enderecos medidos nesta ROM (ver RELATORIO, secoes 9.6 e 10).
HOOK = 0x08054B06        # `bl ResetBag` dentro de NewGameInitData
RESET_BAG = 0x0809A2DC
ADD_BAG_ITEM = 0x0809A084
GET_BAG_QUANTITY = 0x08099DA0   # GetBagItemQuantity(u16 *ptr)
ITEM_ID_GET_POCKET = 0x0809A9D8  # ItemId_GetPocket(u16 itemId)
G_BAG_POCKETS = 0x0203988C
G_SAVE_BLOCK1_PTR = 0x03005008
G_SAVE_BLOCK2_PTR = 0x0300500C
CHAVE_EM_S2 = 0xF20       # offset de `encryptionKey` em SaveBlock2
POCKET_POKE_BALLS = 2     # indice 0-based: 3 - 1
ITEM_POKE_BALL = 4
QUANTIDADE = 99

# Dois caminhos, porque o emulador de console mostrou que a diferenca importa:
#
#  - "saveblock" (PADRAO): escreve em `[gSaveBlock1Ptr] + 0x430`, que e' o
#    endereco da pocket de Poke Balls. `gSaveBlock1Ptr` e' valido desde o boot.
#  - "pockets": chama `AddBagItem`, que e' mais elegante mas depende de
#    `gBagPockets[]` ja' estar apontado -- e nao estava quando o hook rodou
#    (medido: as 5 pockets so' aparecem preenchidas ~4 000 quadros depois).
STUB_SAVEBLOCK = f"""
push {{r4, lr}}
bl 0x{RESET_BAG:08X}
ldr r0, =0x{G_SAVE_BLOCK1_PTR:08X}
ldr r0, [r0]
ldr r1, =0x00000430
adds r0, r0, r1
movs r1, #{ITEM_POKE_BALL}
strh r1, [r0]
ldr r2, =0x{G_SAVE_BLOCK2_PTR:08X}
ldr r2, [r2]
movs r3, #0xF2
lsls r3, r3, #4
ldr r2, [r2, r3]
movs r1, #{QUANTIDADE}
eors r1, r2
strh r1, [r0, #2]
pop {{r4, pc}}
"""

STUB_POCKETS = f"""
push {{r4, lr}}
bl 0x{RESET_BAG:08X}
movs r0, #{ITEM_POKE_BALL}
movs r1, #{QUANTIDADE}
bl 0x{ADD_BAG_ITEM:08X}
pop {{r4, pc}}
"""


def aplicar_na_rom(imagem: bytes, via: str = "saveblock") -> tuple[bytes, int, list[patch.Patch]]:
    """Monta e injeta o patch; devolve (imagem nova, endereco do stub, patches)."""
    if via not in ("saveblock", "pockets"):
        raise patch.ErroDePatch(f"via desconhecida: {via}")
    texto_stub = STUB_SAVEBLOCK if via == "saveblock" else STUB_POCKETS
    endereco_stub = patch.achar_espaco_livre(imagem, 64)
    codigo = patch.montar_thumb_literais(texto_stub, endereco_stub)
    salto = patch.montar_thumb(f"bl 0x{endereco_stub:08X}", HOOK)
    if len(salto) != 4:
        raise patch.ErroDePatch(f"o bl do hook saiu com {len(salto)} bytes, esperado 4")

    # O `esperado` do hook e' o `bl ResetBag` ORIGINAL, montado aqui -- nao o
    # byte que esta' na imagem. Ler da imagem tornaria a conferencia
    # tautologica: a segunda aplicacao "conferiria" o proprio resultado e
    # injetaria um segundo stub sem erro.
    esperado_hook = patch.montar_thumb(f"bl 0x{RESET_BAG:08X}", HOOK)
    patches = [
        patch.Patch(
            endereco=HOOK,
            esperado=esperado_hook,
            novo=salto,
            motivo="troca o bl ResetBag por bl para o stub do patch",
        ),
        patch.Patch(
            endereco=endereco_stub,
            esperado=b"\xff" * len(codigo),
            novo=codigo,
            motivo="corpo do stub, em espaco livre",
        ),
    ]
    return patch.corrigir_cabecalho(patch.aplicar(imagem, patches)), endereco_stub, patches


def verificar_por_emulacao(imagem: bytes, endereco_stub: int) -> dict:
    """Executa o stub real sobre a ROM patcheada e confere o efeito na bag."""
    save1 = 0x02025000
    save2 = 0x02026000
    chave = 0x12345678
    bags = [(0x310, 42), (0x3B8, 30), (0x430, 13), (0x464, 58), (0x54C, 43)]

    emu = Emulador(imagem)
    # lixo nas duas estruturas, para provar que ResetBag limpa de fato
    emu.escrever(save1, b"\xAA" * 0x800)
    emu.escrever(save2, b"\xBB" * 0x1000)
    emu.escrever(save2 + CHAVE_EM_S2, struct.pack("<I", chave))
    emu.escrever(G_SAVE_BLOCK1_PTR, struct.pack("<I", save1))
    emu.escrever(G_SAVE_BLOCK2_PTR, struct.pack("<I", save2))
    for indice, (deslocamento, capacidade) in enumerate(bags):
        emu.escrever(G_BAG_POCKETS + indice * 8,
                     struct.pack("<IBxxx", save1 + deslocamento, capacidade))

    emu.chamar(endereco_stub, zerar=False)

    resultado = {"chave": f"0x{chave:08X}", "pockets": []}
    for indice, (deslocamento, capacidade) in enumerate(bags):
        lixo = emu.ler(save1 + deslocamento, capacidade * 4)
        # slot = {u16 itemId; u16 quantity}, 4 bytes cada
        itens = [struct.unpack_from("<H", lixo, slot * 4)[0]
                 for slot in range(capacidade)]
        resultado["pockets"].append({
            "pocket": indice,
            "offset": f"0x{deslocamento:03X}",
            "capacidade": capacidade,
            "ids_nao_nulos": sum(1 for v in itens if v != 0),
        })

    item_id, quantidade_cifrada = struct.unpack(
        "<HH", emu.ler(save1 + 0x430, 4))
    quantidade = quantidade_cifrada ^ (chave & 0xFFFF)
    # a leitura que o JOGO faz: GetBagItemQuantity (0x08099DA0), nao o nosso XOR
    quantidade_pelo_jogo = emu.chamar(
        GET_BAG_QUANTITY, save1 + 0x430 + 2, zerar=False) & 0xFFFF
    pocket_do_item = emu.chamar(ITEM_ID_GET_POCKET, ITEM_POKE_BALL, zerar=False)
    resultado.update({
        "quantidade_por_GetBagItemQuantity": quantidade_pelo_jogo,
        "pocket_de_ITEM_POKE_BALL": pocket_do_item,
        "slot0_itemId": item_id,
        "slot0_quantidade_cifrada": f"0x{quantidade_cifrada:04X}",
        "slot0_quantidade_lida": quantidade,
        "item_esperado": ITEM_POKE_BALL,
        "quantidade_esperada": QUANTIDADE,
        "ok": (item_id == ITEM_POKE_BALL
               and quantidade == QUANTIDADE
               and quantidade_pelo_jogo == QUANTIDADE
               and pocket_do_item == POCKET_POKE_BALLS + 1
               and all(p["ids_nao_nulos"] == (1 if p["pocket"] == POCKET_POKE_BALLS else 0)
                       for p in resultado["pockets"])),
    })
    return resultado


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("-o", "--saida", type=Path, required=True)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.saida.resolve() == args.rom.resolve():
        # a ROM de entrada e' de terceiros e nao esta no repositorio: sobrescrever
        # apagaria a unica copia local sem volta
        print("recuso sobrescrever a ROM de entrada; use outro caminho de saida",
              file=sys.stderr)
        return 2

    original = args.rom.read_bytes()
    if not rom_mod.looks_like_rom(original):
        print(f"{args.rom}: nao parece uma ROM GBA", file=sys.stderr)
        return 2

    nova, endereco_stub, patches = aplicar_na_rom(original)
    verificacao = verificar_por_emulacao(nova, endereco_stub)

    args.saida.write_bytes(nova)
    relatorio = {
        "rom_entrada": str(args.rom),
        "rom_saida": str(args.saida),
        "bytes": len(nova),
        "stub_em": f"0x{endereco_stub:08X}",
        "hook": f"0x{HOOK:08X}",
        "patches": [
            {"endereco": f"0x{p.endereco:08X}", "esperado": p.esperado.hex(),
             "novo": p.novo.hex(), "motivo": p.motivo}
            for p in patches
        ],
        "cabecalho": {
            "complemento": f"0x{nova[0xBD]:02X}",
            "correto": f"0x{patch.complemento_correto(nova):02X}",
            "confere": nova[0xBD] == patch.complemento_correto(nova),
        },
        "verificacao_por_emulacao": verificacao,
        "nao_provado": [
            "o boot real do GBA chegar em 0x08054B06 com gBagPockets apontado",
            "execucao em emulador de console ou em hardware",
            "que a tela da bag exibe 99 (a leitura segue o formato do jogo)",
        ],
    }
    if args.json:
        args.json.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")

    print(patch.relatar(original, patches))
    print(f"\nstub em 0x{endereco_stub:08X} ({len(patches[1].novo)} bytes)")
    print(f"cabecalho: 0x{nova[0xBD]:02X} "
          + ("(confere)" if relatorio["cabecalho"]["confere"] else "(NAO CONFERE)"))
    print("\nverificacao por emulacao do stub sobre a ROM patcheada:")
    for p in verificacao["pockets"]:
        print(f"  pocket {p['pocket']} (+0x{p['offset'][2:]}): "
              f"{p['ids_nao_nulos']} slot(s) com item")
    print(f"  slot 0 da pocket de Poke Balls: itemId={verificacao['slot0_itemId']} "
          f"quantidade={verificacao['slot0_quantidade_lida']} "
          f"(cifrada {verificacao['slot0_quantidade_cifrada']})")
    print(f"  lida por GetBagItemQuantity (0x08099DA0): "
          f"{verificacao['quantidade_por_GetBagItemQuantity']}")
    print(f"  ItemId_GetPocket(4) = {verificacao['pocket_de_ITEM_POKE_BALL']} "
          f"(pocket de Poke Balls)")
    print(f"  resultado: {'OK' if verificacao['ok'] else 'FALHOU'}")
    print(f"\nROM gravada: {args.saida}")
    return 0 if verificacao["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
