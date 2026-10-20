"""Do boot ate' o overworld: titulo -> intro do Oak -> quarto do jogador.

Estende `ir_ao_menu.py`: depois de sair do titulo, atravessa a sequencia
inteira de novo jogo (paginas de CONTROLE, fala do professor, escolha de
sexo, nomear jogador, nomear rival) ate' o controle voltar ao jogador no
quarto em Pallet. O objetivo e' ter um **ponto de partida reutilizavel**
para os testes de modificacao (bolsa, batalha, scripts) sem depender de
save state alheio.

Como navega, por fase (tudo por sinais MEDIDOS nesta ROM, nao por tempo):

- **Titulo**: espera a cena RUN da tarefa `0x08078C25` e aperta A uma vez
  (ver `ir_ao_menu.py` para a historia completa dos offsets).
- **Dialogos** (`callback2 == 0x0812EB11`): pulso de A a cada 45 quadros
  -- avanca texto, confirma o item ja' selecionado (ex.: MENINO).
- **tela de nomear** (`callback2 == 0x0809FB71`): digita uma letra (A),
  START leva o cursor ao botao OK e A confirma. Acontece 2x: jogador e
  rival.
- **Overworld**: primeiro `callback2` fora do conjunto conhecido que
  **persiste** por 240 quadros. A confirmacao de verdade e' externa:
  ler `pos`/`location` do SaveBlock1 e olhar o PNG.

Com `--estado CAMINHO`, salva um estado do emulador ao chegar. Atencao a`
licao da §16.3: estado salvo so' vale depois de **validado** (carregar
num processo novo e responder a botao) -- esta ferramenta salva, quem
usar o estado precisa validar.

Uso:

    python3 ferramentas/ir_ao_overworld.py ROM.gba CORE.so \
        --png-overworld evidencias/overworld_quarto.png \
        --estado /caminho/fora/do/repo/overworld.state

Enderecos MEDIDOS nesta ROM (FireRed BR, BPRE,
md5 4ec27a4b580a5a883ba66f924810cbd7).
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole  # noqa: E402
from ferramentas.ir_ao_menu import cena_do_titulo, CENA_RUN, CB2_TITULO_RUN  # noqa: E402

GMAIN = 0x030030F0
GSAVEBLOCK1PTR = 0x03005008  # gSaveBlock1Ptr: SEMPRE ler o SaveBlock1 por aqui

CB2_DIALOGO = 0x0812EB11   # paginas de controle + fala do professor
CB2_NOMEAR = 0x0809FB71    # tela de teclado (jogador e rival)
CB2_TRANSITORIO = 0x0800C301  # visto por poucos quadros apos o titulo

CONHECIDOS = {CB2_TITULO_RUN, CB2_DIALOGO, CB2_NOMEAR, CB2_TRANSITORIO}


def cb2(emu: EmuladorConsole) -> int:
    return emu.ler_u32(GMAIN + 0x04)


def posicao(emu: EmuladorConsole):
    """pos (Coords16) e location (WarpData) no inicio do SaveBlock1.

    Lidos atraves de `gSaveBlock1Ptr`, nunca por endereco fixo: nesta
    medicao o ponteiro vale `0x0202557C` (spawn (6,6), grupo 4, mapa 1),
    enquanto o endereco fixo `0x02025544` usado em sessoes anteriores
    esta' zerado aqui (+0x38 de diferenca nos dois ponteiros de save) --
    o buffer muda conforme o contexto (Quest Log etc.).
    """
    base = emu.ler_u32(GSAVEBLOCK1PTR)
    bruto = emu.ler(base, 12)
    x, y = struct.unpack_from("<2h", bruto, 0)
    grupo, numero, warp = struct.unpack_from("<3b", bruto, 4)
    return (x, y), (grupo, numero, warp)


def apertar(emu: EmuladorConsole, botao: str, esperar: int, segurar: int = 6):
    emu.agendar(emu._quadro_atual + 1, botao, segurar=segurar)
    emu.rodar(esperar)


def atravessar_titulo(emu: EmuladorConsole, limite: int) -> bool:
    anterior = None
    while emu._quadro_atual < limite:
        emu.rodar(10)
        cena = cena_do_titulo(emu)
        if cena != anterior:
            print(f"[{emu._quadro_atual:6d}] titulo: cena={cena}")
            anterior = cena
        if cena and cena[0] == CENA_RUN:
            break
    else:
        return False
    apertar(emu, "A", esperar=30)
    while emu._quadro_atual < limite:
        emu.rodar(10)
        if cena_do_titulo(emu) is None and cb2(emu) != CB2_TITULO_RUN:
            print(f"[{emu._quadro_atual:6d}] titulo: saiu "
                  f"(callback2={cb2(emu):#010x})")
            return True
    return False


def nomear(emu: EmuladorConsole, limite: int) -> bool:
    """Digita uma letra e confirma: START move o cursor ao OK; A aperta o OK.

    (Conferido no pret/pokefirered, naming_screen.c: `INPUT_START` chama
    apenas `MoveCursorToOKButton()` -- a primeira versao desta funcao
    esperava a saida so' com o START e travou ate' o limite.)
    """
    emu.rodar(60)                        # deixa a tela montar
    apertar(emu, "A", esperar=45)        # digita 'A'
    for _ in range(3):
        apertar(emu, "START", esperar=30)  # cursor -> botao OK
        apertar(emu, "A", esperar=60)      # confirma o OK
        for _ in range(20):                # ate' 300 quadros por tentativa
            if cb2(emu) != CB2_NOMEAR:
                return True
            if emu._quadro_atual >= limite:
                return False
            emu.rodar(15)
    return cb2(emu) != CB2_NOMEAR


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("core", type=Path)
    parser.add_argument("--png-overworld", type=Path)
    parser.add_argument("--png-prefixo", type=Path,
                        help="salva um PNG a cada troca de callback2")
    parser.add_argument("--estado", type=Path,
                        help="salva o estado do emulador ao chegar")
    parser.add_argument("--limite", type=int, default=40000,
                        help="quadros maximos no total (padrao 40000)")
    args = parser.parse_args()

    emu = EmuladorConsole(args.rom, args.core)

    if not atravessar_titulo(emu, args.limite):
        print("NAO saiu do titulo", file=sys.stderr)
        return 1

    atual = cb2(emu)
    candidato = None        # callback2 desconhecido sob observacao
    candidato_desde = 0
    telas_de_nome = 0
    pulsos_a = 0
    while emu._quadro_atual < args.limite:
        agora = cb2(emu)
        if agora != atual:
            print(f"[{emu._quadro_atual:6d}] callback2 "
                  f"{atual:#010x} -> {agora:#010x}")
            if args.png_prefixo:
                destino = args.png_prefixo.with_name(
                    f"{args.png_prefixo.name}{emu._quadro_atual}.png")
                emu.salvar_png(destino)
            atual = agora
            candidato = None

        if agora == CB2_DIALOGO:
            apertar(emu, "A", esperar=45)
            pulsos_a += 1
        elif agora == CB2_NOMEAR:
            telas_de_nome += 1
            print(f"[{emu._quadro_atual:6d}] tela de nomear #{telas_de_nome}")
            if not nomear(emu, args.limite):
                print("NAO saiu da tela de nomear", file=sys.stderr)
                return 1
            atual = cb2(emu)
        elif agora in CONHECIDOS:
            emu.rodar(15)
        else:
            if candidato != agora:
                candidato, candidato_desde = agora, emu._quadro_atual
            elif emu._quadro_atual - candidato_desde >= 240:
                print(f"[{emu._quadro_atual:6d}] callback2 estavel fora da "
                      f"intro: {agora:#010x} (candidato a overworld)")
                break
            emu.rodar(15)
    else:
        print("NAO chegou ao overworld dentro do limite", file=sys.stderr)
        return 1

    emu.rodar(120)  # deixa o mapa assentar, sem botao
    (x, y), (grupo, numero, warp) = posicao(emu)
    print(f"chegou: quadro {emu._quadro_atual}, callback2={cb2(emu):#010x}, "
          f"pulsos de A={pulsos_a}, telas de nomear={telas_de_nome}")
    print(f"SaveBlock1.pos=({x},{y}) location=(grupo {grupo}, mapa {numero}, "
          f"warp {warp}) -- confira no PNG antes de chamar de overworld")
    if args.png_overworld:
        emu.salvar_png(args.png_overworld)
    if args.estado:
        emu.salvar_estado(args.estado)
        print(f"estado salvo em {args.estado} "
              f"({args.estado.stat().st_size} bytes) -- VALIDE antes de usar")
    emu.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
