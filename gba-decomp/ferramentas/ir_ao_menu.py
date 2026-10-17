"""Sai da tela-titulo e chega ao menu/intro, apertando o botao NA CENA CERTA.

Por que isto existe: passamos uma sessao inteira achando que "o jogo nao
sai do titulo no nosso harness". Medindo direito (2026-10-17), eram tres
erros NOSSOS, nao do emulador:

1. **Offsets errados do `gMain`.** O que liamos como `callback2`
   (`0x030030FC`, +0x0C) e' o `vblankCallback`; o `callback2` de verdade
   fica em +0x04 (`0x030030F4`). E o `newKeys` que `JOY_NEW` testa fica
   em +0x2E (`0x0300311E`) -- forcar +0x28/+0x2C (heldKeysRaw/heldKeys)
   nao gera aperto nenhum. Layout conferido com o `include/main.h` do
   pret/pokefirered e com o comportamento medido quadro a quadro.
2. **Um aperto so' nao basta -- e tem hora certa.** A maquina do titulo
   (`Task_TitleScreenMain`, cenas INIT=0..CRY=5): apertar A/B/START nas
   cenas 0-2 apenas PULA para a cena RUN (3, o "PRESS START" piscando).
   So' um segundo aperto, ja' na RUN, vai para CRY e dai para o menu.
   Apertar START uma vez aos ~1500 quadros cai na cena 2 (FADEIN).
3. **Hash de VRAM nao ve a tela.** Na cena RUN a VRAM nao muda (quem muda
   e' paleta/sprite: o "PRESS START" piscando e as chamas animadas), e
   fade e' paleta pura. O criterio antigo dizia "congelado" de uma tela
   animada e saudavel -- inclusive com o loop de atracao (2700 quadros
   sem aperto -> RESTART -> copyright -> intro -> titulo...) funcionando.

Esta ferramenta roda desde o boot, espera a cena RUN olhando os dados da
tarefa do titulo, aperta A uma vez e confirma a saida pelo `callback2`.

Uso (o core precisa ser um `mgba_libretro.so` carregavel neste sistema):

    python3 ferramentas/ir_ao_menu.py ROM.gba CORE.so \
        --png-pressstart evidencias/titulo_press_start.png \
        --png-menu evidencias/apos_titulo.png

Os enderecos abaixo foram MEDIDOS nesta ROM (FireRed BR, BPRE, md5
4ec27a4b580a5a883ba66f924810cbd7); numa ROM diferente, confira antes.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole  # noqa: E402

GMAIN = 0x030030F0
GTASKS = 0x03005090
NUM_TASKS = 16
TAM_TASK = 40  # struct Task: func+flags (8) + s16 data[16] (32)

# medidos em 2026-10-17 nesta ROM:
TASK_TITULO_MAIN = 0x08078C25   # Task_TitleScreenMain
CB2_TITULO_RUN = 0x08078B9D     # CB2_TitleScreenRun

# cenas de Task_TitleScreenMain (enum do pret/pokefirered)
CENA_RUN = 3
CENA_CRY = 5


def cena_do_titulo(emu: EmuladorConsole):
    """(cena, estado) da tarefa do titulo, ou None se ela nao existe(mais)."""
    bruto = emu.ler(GTASKS, NUM_TASKS * TAM_TASK)
    for i in range(NUM_TASKS):
        tarefa = bruto[i * TAM_TASK:(i + 1) * TAM_TASK]
        func, ativa = struct.unpack_from("<IB", tarefa, 0)
        if ativa and func == TASK_TITULO_MAIN:
            cena, estado = struct.unpack_from("<2h", tarefa, 8)
            return cena, estado
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("core", type=Path)
    parser.add_argument("--png-pressstart", type=Path)
    parser.add_argument("--png-menu", type=Path)
    parser.add_argument("--limite", type=int, default=8000,
                        help="quadros maximos ate' desistir (padrao 8000)")
    args = parser.parse_args()

    emu = EmuladorConsole(args.rom, args.core)

    # Fase 1: esperar a cena RUN (o "PRESS START" aguardando aperto).
    anterior = None
    while emu._quadro_atual < args.limite:
        emu.rodar(10)
        cena = cena_do_titulo(emu)
        if cena != anterior:
            print(f"quadro {emu._quadro_atual}: cena do titulo = {cena}")
            anterior = cena
        if cena and cena[0] == CENA_RUN:
            break
    else:
        print("NAO chegou a cena RUN dentro do limite", file=sys.stderr)
        return 1

    if args.png_pressstart:
        emu.salvar_png(args.png_pressstart)
    print(f">>> cena RUN no quadro {emu._quadro_atual}; apertando A")

    # Fase 2: um aperto de A (8 quadros). O `newKeys` so' existe no primeiro.
    emu.agendar(emu._quadro_atual + 2, "A", segurar=8)
    for _ in range(20):
        emu.rodar(1)
        held_raw, new_raw, held, new = struct.unpack(
            "<4H", emu.ler(GMAIN + 0x28, 8))
        if held_raw or new:
            print(f"  quadro {emu._quadro_atual}: heldKeysRaw={held_raw:#x} "
                  f"newKeys={new:#x} cena={cena_do_titulo(emu)}")

    # Fase 3: esperar a tarefa do titulo morrer e o callback2 trocar.
    while emu._quadro_atual < args.limite:
        emu.rodar(10)
        cena = cena_do_titulo(emu)
        cb2 = emu.ler_u32(GMAIN + 0x04)
        if cena != anterior:
            print(f"quadro {emu._quadro_atual}: cena do titulo = {cena} "
                  f"callback2 = {cb2:#010x}")
            anterior = cena
        if cena is None and cb2 != CB2_TITULO_RUN:
            print(f">>> saiu do titulo no quadro {emu._quadro_atual}; "
                  f"callback2 novo = {cb2:#010x}")
            break
    else:
        print("NAO saiu do titulo dentro do limite", file=sys.stderr)
        return 1

    emu.rodar(60)
    if args.png_menu:
        emu.salvar_png(args.png_menu)
    print(f"callback2 final = {emu.ler_u32(GMAIN + 0x04):#010x}")
    emu.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
