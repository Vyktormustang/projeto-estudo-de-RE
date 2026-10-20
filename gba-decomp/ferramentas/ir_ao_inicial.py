"""Do quarto ao primeiro Pokemon: sai de casa, dispara o Oak, escolhe.

Continua o `ir_ao_overworld.py`: desce as escadas, sai da casa, tenta ir
para a Rota 1 (gatilho (12,1) -> o Oak escolta ate' o laboratorio),
escolhe o **Bulbasaur** (bola da esquerda, objeto em (8,4)), da' o apelido
"A" se a tela de nomear abrir (padrao do SIM/NAO e' SIM), vence a batalha
contra o rival apertando A (LUTAR -> Investida) e sai do laboratorio.

Tudo por sinais MEDIDOS nesta ROM, nunca por contagem fixa de passos:

- posicao/mapa: `pos` e `location` do SaveBlock1 via `gSaveBlock1Ptr`
  (`0x03005008`) -- cada `passo` segura a direcao ate' o tile mudar, entao
  solta; se algo bloqueia (NPC andando, ex.: a moca da placa), espera 50
  quadros e tenta de novo;
- warps tem **atraso**: pisar na escada/porta so' troca o mapa alguns
  quadros depois (na escada, durante o passo seguinte) -- `espera_warp`;
- a porta da casa so' dispara descendo A PARTIR do tapete (andar na
  horizontal por cima dele nao sai);
- controle livre vs. cutscene: teste de passo ida-e-volta;
- party: nesta ROM o time NAO esta' no SaveBlock1 durante o jogo
  (SB1+0x34 fica 0; deve ser copiado so' ao salvar no cartucho). Medido:
  contagem em `0x02024029`, estrutura do 1o Pokemon em `0x02024284`
  (apelido@+8, nivel@+84, HP@+86/+88) -- ver §19 das NOTAS;
- batalha: `callback2` sai de `0x080565B5` (overworld) para
  `0x08011101` e volta quando acaba.

Uso:

    # do estado validado no quarto (ver validar_estado_overworld.py)
    python3 ferramentas/ir_ao_inicial.py ROM.gba CORE.so \
        --estado overworld.state --estado-saida /fora/do/repo/com_inicial.state

    # ou do boot, sem estado nenhum
    python3 ferramentas/ir_ao_inicial.py ROM.gba CORE.so --do-boot \
        --estado-saida /fora/do/repo/com_inicial.state

Enderecos/coordenadas MEDIDOS nesta ROM (FireRed BR, BPRE,
md5 4ec27a4b580a5a883ba66f924810cbd7); as coordenadas de warp/gatilho
conferem com os `map.json` do pret/pokefirered.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole  # noqa: E402
from ferramentas.ir_ao_overworld import (  # noqa: E402
    atravessar_titulo, nomear, cb2 as ler_cb2,
    CB2_DIALOGO, CB2_NOMEAR, CONHECIDOS,
)

GSAVEBLOCK1PTR = 0x03005008
PARTY_COUNT = 0x02024029   # medido (0 -> 1 ao pegar o inicial)
PARTY_1 = 0x02024284       # medido: struct do 1o Pokemon (100 bytes)
CB2_OVERWORLD = 0x080565B5  # medido pelo comportamento (andar/menu)
CB2_BATALHA = 0x08011101   # medido durante a batalha do rival

QUARTO, TERREO, PALLET, LAB = (4, 1), (4, 0), (3, 0), (4, 3)


# ---- leituras de estado -------------------------------------------------

def pos(emu: EmuladorConsole):
    return struct.unpack("<2h", emu.ler(emu.ler_u32(GSAVEBLOCK1PTR), 4))


def mapa(emu: EmuladorConsole):
    b = emu.ler(emu.ler_u32(GSAVEBLOCK1PTR) + 4, 2)
    return tuple(v - 256 if v >= 128 else v for v in b)


def party(emu: EmuladorConsole) -> int:
    return emu.ler(PARTY_COUNT, 1)[0]


def onde(emu: EmuladorConsole) -> str:
    return (f"mapa={mapa(emu)} pos={pos(emu)} "
            f"cb2={ler_cb2(emu):#010x} party={party(emu)}")


# ---- primitivas de movimento -------------------------------------------

def apertar(emu, botao, esperar, segurar=6):
    emu.agendar(emu._quadro_atual + 1, botao, segurar=segurar)
    emu.rodar(esperar)


def espera_warp(emu, mapa_antigo, rotulo) -> bool:
    for _ in range(15):
        emu.rodar(10)
        if mapa(emu) != mapa_antigo:
            emu.rodar(120)
            print(f"  [{rotulo}] warp: {onde(emu)}")
            return True
    return False


def passo(emu, direcao) -> bool:
    """Um tile: segura ate' pos/mapa mudar. False se bloqueado."""
    p0, m0 = pos(emu), mapa(emu)
    emu.agendar(emu._quadro_atual + 1, direcao, segurar=200)
    ok = False
    for _ in range(50):
        emu.rodar(2)
        if pos(emu) != p0 or mapa(emu) != m0:
            ok = True
            break
    emu.agendar(emu._quadro_atual - 1, direcao, segurar=0)  # solta
    emu.rodar(8)
    return ok


def andar_ate(emu, direcao, condicao, maxp=25, rotulo="", tentativas=4) -> bool:
    m0 = mapa(emu)
    travado = 0
    for _ in range(maxp):
        if condicao(pos(emu), mapa(emu)):
            break
        if not passo(emu, direcao):
            travado += 1
            if travado > tentativas:
                print(f"  [{rotulo}] bloqueado: {onde(emu)}")
                break
            emu.rodar(50)  # pode ser NPC; espera sair da frente
            continue
        travado = 0
        if mapa(emu) != m0:
            emu.rodar(120)
            print(f"  [{rotulo}] WARP: {onde(emu)}")
            return True
    print(f"  [{rotulo}] {onde(emu)}")
    return mapa(emu) != m0


def livre(emu) -> bool:
    """Controle livre? Testa com passo ida-e-volta (posicao final igual)."""
    if passo(emu, "LEFT"):
        passo(emu, "RIGHT")
        return True
    if passo(emu, "RIGHT"):
        passo(emu, "LEFT")
        return True
    return False


# ---- fases ---------------------------------------------------------------

def fase_boot_ate_quarto(emu, limite) -> bool:
    """Mesma sequencia do ir_ao_overworld.py, reutilizando as pecas."""
    if not atravessar_titulo(emu, limite):
        return False
    atual, candidato, candidato_desde = ler_cb2(emu), None, 0
    while emu._quadro_atual < limite:
        agora = ler_cb2(emu)
        if agora != atual:
            atual, candidato = agora, None
        if agora == CB2_DIALOGO:
            apertar(emu, "A", 45)
        elif agora == CB2_NOMEAR:
            if not nomear(emu, limite):
                return False
            atual = ler_cb2(emu)
        elif agora in CONHECIDOS:
            emu.rodar(15)
        else:
            if candidato != agora:
                candidato, candidato_desde = agora, emu._quadro_atual
            elif emu._quadro_atual - candidato_desde >= 240:
                break
            emu.rodar(15)
    emu.rodar(120)
    print(f"  [boot] no quarto: {onde(emu)}")
    return mapa(emu) == QUARTO


def fase_sair_de_casa(emu) -> bool:
    apertar(emu, "B", 25)  # fecha texto que tenha ficado aberto
    andar_ate(emu, "RIGHT", lambda p, m: p[0] >= 11, rotulo="quarto-dir")
    andar_ate(emu, "UP", lambda p, m: p[1] <= 2, rotulo="quarto-cima")
    m0 = mapa(emu)  # escada em (10,2); o warp materializa no passo seguinte
    andar_ate(emu, "LEFT", lambda p, m: p[0] <= 10, maxp=2, rotulo="escada")
    if mapa(emu) == m0 and not espera_warp(emu, m0, "escada-lag"):
        passo(emu, "LEFT")
        espera_warp(emu, m0, "escada-lag2")
    if mapa(emu) != TERREO:
        return False
    andar_ate(emu, "DOWN", lambda p, m: p[1] >= 8, rotulo="1f-baixo")
    andar_ate(emu, "LEFT", lambda p, m: p[0] <= 4, rotulo="1f-esq")
    m0 = mapa(emu)  # porta: descer A PARTIR do tapete (4,8) -> warp
    passo(emu, "DOWN")
    if mapa(emu) == m0:
        espera_warp(emu, m0, "1f-porta")
    emu.rodar(60)
    print(f"  [casa] fora: {onde(emu)}")
    return mapa(emu) == PALLET


def fase_gatilho_oak(emu) -> bool:
    andar_ate(emu, "RIGHT", lambda p, m: p[0] >= 11, rotulo="pallet-dir")
    for col in (11, 12, 13, 10, 14):
        if pos(emu)[0] != col:
            andar_ate(emu, "RIGHT" if pos(emu)[0] < col else "LEFT",
                      lambda p, m, c=col: p[0] == c, maxp=5,
                      rotulo=f"pallet-col{col}")
        andar_ate(emu, "UP", lambda p, m: p[1] <= 1, maxp=12,
                  rotulo=f"pallet-norte{col}")
        if mapa(emu) != PALLET or pos(emu)[1] <= 1:
            break
    if pos(emu)[1] > 1:
        return False
    emu.rodar(120)  # a cutscene comeca sozinha: o Oak vem buscar
    for i in range(160):
        apertar(emu, "A", 45)
        if mapa(emu) == LAB and i > 25:
            p0 = pos(emu)
            if passo(emu, "DOWN") and pos(emu) != p0 and mapa(emu) == LAB:
                print(f"  [lab] controle livre: {onde(emu)}")
                return True
        if i == 40 and mapa(emu) == PALLET and livre(emu):
            print("  [lab] SEM cutscene (controle livre em Pallet)")
            return False
    return mapa(emu) == LAB


def fase_escolher(emu, limite) -> bool:
    andar_ate(emu, "UP", lambda p, m: p[1] <= 5, rotulo="lab-cima")
    for _ in range(80):  # aproximar do Oak abre o dialogo da escolha
        apertar(emu, "A", 45)
        if ler_cb2(emu) == CB2_OVERWORLD and livre(emu):
            break
    andar_ate(emu, "DOWN", lambda p, m: p[1] >= 5, maxp=3, rotulo="lab-5")
    andar_ate(emu, "RIGHT", lambda p, m: p[0] >= 8, rotulo="lab-dir")
    passo(emu, "UP")  # a mesa bloqueia: fica de frente para a bola (8,4)
    if pos(emu) != (8, 5):
        print(f"  [bola] posicao inesperada: {onde(emu)}")
        return False
    apertar(emu, "A", 60)
    for _ in range(150):
        if ler_cb2(emu) == CB2_NOMEAR:  # apelido (o padrao e' SIM)
            if not nomear(emu, limite):
                return False
            continue
        if party(emu) >= 1 and ler_cb2(emu) == CB2_OVERWORLD and livre(emu):
            mon = emu.ler(PARTY_1, 100)
            hp, hpmax = struct.unpack_from("<2H", mon, 86)
            print(f"  [bola] inicial pego: nivel {mon[84]}, HP {hp}/{hpmax}")
            return True
        apertar(emu, "A", 50)
    return False


def fase_batalha_e_saida(emu, foto=None) -> bool:
    andar_ate(emu, "LEFT", lambda p, m: p[0] <= 6, rotulo="sai-esq")
    andar_ate(emu, "DOWN", lambda p, m: p[1] >= 8, rotulo="sai-baixo")
    emu.rodar(60)  # gatilhos (5..7,8): o rival chama para a batalha
    em_batalha = False
    for _ in range(260):
        c = ler_cb2(emu)
        if c != CB2_OVERWORLD:
            if not em_batalha and c == CB2_BATALHA and foto:
                emu.rodar(150)
                foto("embatalha")
            em_batalha = True
        elif em_batalha:
            print(f"  [rival] batalha terminou: {onde(emu)}")
            break
        apertar(emu, "A", 60)  # dialogos e, na batalha, LUTAR->1o golpe
    if not em_batalha:
        return False
    for _ in range(40):  # falas finais do rival
        apertar(emu, "A", 45)
        if livre(emu):
            break
    andar_ate(emu, "LEFT" if pos(emu)[0] > 6 else "RIGHT",
              lambda p, m: p[0] == 6, maxp=4, rotulo="fim-col")
    andar_ate(emu, "DOWN", lambda p, m: m != LAB, maxp=8, rotulo="fim-porta")
    emu.rodar(150)
    return mapa(emu) == PALLET


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("core", type=Path)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--estado", type=Path,
                       help="estado validado no quarto (mapa 4,1)")
    grupo.add_argument("--do-boot", action="store_true",
                       help="comeca do boot (intro completa)")
    parser.add_argument("--estado-saida", type=Path)
    parser.add_argument("--png-prefixo", type=Path)
    parser.add_argument("--limite", type=int, default=40000)
    args = parser.parse_args()

    def foto(nome):
        if args.png_prefixo:
            destino = args.png_prefixo.with_name(
                f"{args.png_prefixo.name}_{nome}.png")
            emu.salvar_png(destino)
            print(f"  foto {destino.name}: {onde(emu)}")

    emu = EmuladorConsole(args.rom, args.core)
    if args.estado:
        emu.carregar_estado(args.estado)
        emu.rodar(30)
        print(f"estado carregado: {onde(emu)}")
        if mapa(emu) != QUARTO:
            print("o estado nao esta' no quarto (mapa 4,1)", file=sys.stderr)
            return 1
    elif not fase_boot_ate_quarto(emu, args.limite):
        print("NAO chegou ao quarto a partir do boot", file=sys.stderr)
        return 1

    etapas = [
        ("sair de casa", lambda: fase_sair_de_casa(emu)),
        ("gatilho do Oak", lambda: fase_gatilho_oak(emu)),
        ("escolher o Bulbasaur", lambda: fase_escolher(emu, args.limite)),
        ("batalha e saida", lambda: fase_batalha_e_saida(emu, foto)),
    ]
    for nome, fase in etapas:
        if not fase():
            print(f"FALHOU na etapa: {nome} ({onde(emu)})", file=sys.stderr)
            foto("falha")
            return 1
        foto(nome.split()[0].lower())

    mon = emu.ler(PARTY_1, 100)
    hp, hpmax = struct.unpack_from("<2H", mon, 86)
    print(f"FINAL: {onde(emu)} -- 1o Pokemon nv{mon[84]} HP {hp}/{hpmax} "
          f"(apelido byte0={mon[8]:#04x})")
    foto("final")
    if args.estado_saida:
        emu.salvar_estado(args.estado_saida)
        print(f"estado salvo em {args.estado_saida} "
              f"({args.estado_saida.stat().st_size} bytes) -- VALIDE antes de usar")
    emu.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
