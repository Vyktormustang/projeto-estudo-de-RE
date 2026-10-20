"""Valida um estado salvo no overworld: ele RESPONDE depois de carregar?

A §16.3 registrou estados que carregavam **inertes** (nenhum botao fazia
efeito). Entao estado salvo nao e' ponto de partida confiavel ate' passar
neste teste, num processo novo:

    python3 ferramentas/validar_estado_overworld.py ROM.gba CORE.so ESTADO.state

O teste, nesta ordem: carrega o estado, anda para BAIXO, anda para a
DIREITA, abre o menu START e fecha com B -- conferindo a cada passo o
`pos` do SaveBlock1 (lido por `gSaveBlock1Ptr` em `0x03005008`!) e o hash
do framebuffer. Sai 0 se a posicao andou nos dois eixos e o quadro apos
fechar o menu e' byte-identico ao de antes de abrir.

Medido em 2026-10-17 com o estado gerado por `ir_ao_overworld.py`:
spawn (6,6) no grupo 4/mapa 1 (quarto do jogador), BAIXO -> (6,8),
DIREITA -> (9,8), menu abre (BOLSA/SALVAR/OPCOES/SAIR) e fecha voltando
ao mesmo hash de tela.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole  # noqa: E402

GSAVEBLOCK1PTR = 0x03005008


def pos(emu: EmuladorConsole):
    return struct.unpack("<2h", emu.ler(emu.ler_u32(GSAVEBLOCK1PTR), 4))


def hash_tela(emu: EmuladorConsole) -> str:
    return hashlib.md5(emu.quadro).hexdigest()[:8]


def segurar(emu: EmuladorConsole, botao: str, quadros: int):
    emu.agendar(emu._quadro_atual + 1, botao, segurar=quadros)
    emu.rodar(quadros + 40)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("core", type=Path)
    parser.add_argument("estado", type=Path)
    parser.add_argument("--png-prefixo", type=Path,
                        help="salva PNGs PREFIXO_{carregado,baixo,direita,menu}.png")
    args = parser.parse_args()

    emu = EmuladorConsole(args.rom, args.core)
    emu.carregar_estado(args.estado)
    emu.rodar(30)

    def foto(nome: str):
        if args.png_prefixo:
            emu.salvar_png(args.png_prefixo.with_name(
                f"{args.png_prefixo.name}_{nome}.png"))

    ok = True
    p0 = pos(emu)
    print(f"carregado: pos={p0} tela={hash_tela(emu)}")
    foto("carregado")

    segurar(emu, "DOWN", 50)
    p1 = pos(emu)
    print(f"BAIXO:     pos={p1} tela={hash_tela(emu)}")
    foto("baixo")
    ok &= p1[1] > p0[1]

    segurar(emu, "RIGHT", 50)
    p2 = pos(emu)
    tela_andando = hash_tela(emu)
    print(f"DIREITA:   pos={p2} tela={tela_andando}")
    foto("direita")
    ok &= p2[0] > p1[0]

    segurar(emu, "START", 8)
    tela_menu = hash_tela(emu)
    print(f"START:     pos={pos(emu)} tela={tela_menu} (menu aberto?)")
    foto("menu")
    ok &= tela_menu != tela_andando

    segurar(emu, "B", 8)
    tela_fechou = hash_tela(emu)
    print(f"B:         pos={pos(emu)} tela={tela_fechou}")
    ok &= tela_fechou == tela_andando

    print("ESTADO VIVO" if ok else "ESTADO INERTE/SUSPEITO")
    emu.fechar()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
