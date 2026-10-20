"""Atravessa Pallet e a Rota 1 ate' Viridian -- e para ao chegar.

Parte de um estado ja' com o Pokemon inicial (o de
`ferramentas/ir_ao_inicial.py`, fora do lab em Pallet). O objetivo e'
unico: cruzar a conexao norte da Rota 1 e parar assim que o jogo trocar
para Viridian. Nao pega o pacote do Oak, nao entra em predios e nao
continua para a Rota 2/22.

O que foi medido no caminho:

- depois do inicial, a senhora da placa fica sobre `(12,2)` em Pallet:
  o atalho lateral usado antes do inicial nao funciona mais. A saida
  e' `(12,3) -> (13,3) -> (13,2)` (gatilho/cena dela) e depois norte;
- a Rota 1 e' o mapa `(3,19)` e Viridian e' `(3,1)` (pret
  `data/maps/map_groups.json`, conferido em jogo);
- encontros selvagens usam o `callback2 0x08011101`. Com o menu aberto,
  `RIGHT` e `DOWN` colocam o cursor em **SAIR** (fotografado); fugir
  evita o desgaste que, lutando em todo encontro, levou a whiteout nas
  sondas anteriores;
- um passo aqui significa segurar a direcao ate' `SaveBlock1.pos` mudar
  (`passo` de `ir_ao_inicial.py`). A Rota 1 e' atravessada por um
  explorador on-line: vizinho de menor `y`, com penalidade por visitas
  repetidas e paredes aprendidas quando um passo e' recusado. A
  penalidade importa: sem ela, um beco na mesma linha `y` faz o
  algoritmo ir e voltar sem nunca aceitar recuar um tile ao sul;
- se houver whiteout mesmo assim, o laco externo reconhece a casa
  `(4,0)/(4,1)`, sai dela e tenta a travessia de novo (EXP/nivel
  permanecem; o jogo cura o time).

Uso:

    python3 ferramentas/ir_a_viridian.py ROM.gba CORE.so \
        --estado /fora/do/repo/com_inicial_boot.state \
        --estado-saida /fora/do/repo/viridian.state \
        --png-prefixo evidencias/viridian

ROM/estados nao vao para o Git. Como sempre: valide o estado salvo num
processo novo antes de trata-lo como ponto de partida.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, AbstractSet

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import EmuladorConsole  # noqa: E402
from gbadecomp.pokemon import END_TIME, ler_pokemon  # noqa: E402
from ferramentas.ir_ao_inicial import (  # noqa: E402
    CB2_BATALHA,
    CB2_OVERWORLD,
    apertar,
    espera_warp,
    fase_sair_de_casa,
    livre,
    mapa,
    onde,
    party,
    passo,
    pos,
)
from ferramentas.ir_ao_overworld import cb2 as ler_cb2  # noqa: E402

PALLET = (3, 0)
VIRIDIAN = (3, 1)
ROTA1 = (3, 19)
TERREO = (4, 0)
QUARTO = (4, 1)
LAB = (4, 3)
CASA = frozenset({TERREO, QUARTO})

DELTA = (
    ("UP", (0, -1)),
    ("LEFT", (-1, 0)),
    ("RIGHT", (1, 0)),
    ("DOWN", (0, 1)),
)
PESO_CUSTO = 4
PESO_VISITA = 3


def ordenar_candidatos(
    posicao: tuple[int, int],
    custo: Callable[[int, int], int],
    visitados: Mapping[tuple[int, int], int],
    paredes: AbstractSet[tuple[int, int]],
) -> list[tuple[tuple[int, int, int], str, tuple[int, int]]]:
    """Ordena os quatro vizinhos para o explorador on-line.

    A chave principal mistura o custo geografico com visitas repetidas:
    um tile visitado demais pode ficar pior que recuar na direcao
    contraria ao objetivo. Sem isso, o explorador fica oscilando num
    beco horizontal (o destino ao norte ganha sempre no custo puro).
    A ordem de `DELTA` so' desempata.
    """
    candidatos = []
    for preferencia, (direcao, (dx, dy)) in enumerate(DELTA):
        alvo = (posicao[0] + dx, posicao[1] + dy)
        if alvo in paredes:
            continue
        visitas = visitados.get(alvo, 0)
        chave = (PESO_CUSTO * custo(*alvo) + PESO_VISITA * visitas,
                 visitas, preferencia)
        candidatos.append((chave, direcao, alvo))
    candidatos.sort(key=lambda item: item[0])
    return candidatos


def primeiro_pokemon(emu: EmuladorConsole):
    return ler_pokemon(emu.ler(END_TIME, 100))


def resumo_time(emu: EmuladorConsole) -> str:
    if party(emu) < 1:
        return "sem Pokemon no time"
    mon = primeiro_pokemon(emu)
    hp, hp_max = mon.hp
    return (f"especie={mon.especie} nv{mon.nivel} HP {hp}/{hp_max} "
            f"exp={mon.experiencia} golpes={mon.golpes}")


def esperar_cb2(emu: EmuladorConsole, alvo: int, max_quadros: int) -> bool:
    rodados = 0
    while rodados < max_quadros:
        if ler_cb2(emu) == alvo:
            return True
        emu.rodar(15)
        rodados += 15
    return ler_cb2(emu) == alvo


def overworld_estavel(emu: EmuladorConsole, quadros: int = 90) -> bool:
    if ler_cb2(emu) != CB2_OVERWORLD:
        return False
    if quadros:
        emu.rodar(quadros)
    return ler_cb2(emu) == CB2_OVERWORLD


@dataclass
class Travessia:
    emu: EmuladorConsole
    foto: Callable[[str], None] | None = None
    checkpoint: Path | None = None
    max_passos_rota: int = 1400
    batalhas: int = 0
    fugas: int = 0
    lutas: int = 0
    whiteouts: int = 0
    _menor_y_rota: int | None = field(default=None, init=False)

    # -- batalha selvagem ---------------------------------------------------
    def _classificar_fim_batalha(self, exp_antes: int) -> str:
        if mapa(self.emu) in CASA:
            self.whiteouts += 1
            return "whiteout"
        mon = primeiro_pokemon(self.emu)
        if mon.hp[0] == 0:
            self.whiteouts += 1
            return "whiteout"
        if mon.experiencia != exp_antes:
            self.lutas += 1
            return "lutou"
        self.fugas += 1
        return "fugiu"

    def resolver_batalha_selvagem(self) -> str:
        """Foge por SAIR (RIGHT, DOWN, A); lutar fica como ultimo recurso."""
        emu = self.emu
        if ler_cb2(emu) == CB2_OVERWORLD:
            return "sem_batalha"
        antes = primeiro_pokemon(emu)
        exp_antes = antes.experiencia

        if not esperar_cb2(emu, CB2_BATALHA, 900):
            # Warps tambem trocam o callback por alguns quadros
            # (ex.: 0x0805674d ao entrar no lab). Isso nao e' encontro:
            # nao contar como batalha nem como fuga.
            if overworld_estavel(emu):
                return "sem_batalha"
            print("  [batalha] callback de batalha nao estabilizou")
            return "falha"

        self.batalhas += 1
        numero = self.batalhas
        print(f"  [batalha {numero}] encontro em {onde(emu)}; {resumo_time(emu)}")

        # A intro inteira anda sozinha. Apertar as setas antes da hora as
        # desperdiça (medido: aos 220q ainda era a animacao de entrada).
        emu.rodar(700)
        for tentativa in range(6):
            if overworld_estavel(emu, 0):
                break
            if tentativa:
                # Uma fuga recusada devolve o menu depois do ataque
                # inimigo. O B tambem fecha um submenu aberto por engano
                # e nao tem efeito no menu principal.
                emu.rodar(350)
                apertar(emu, "B", 100)
                emu.rodar(160)
            apertar(emu, "RIGHT", 40)   # LUTAR -> BOLSA
            apertar(emu, "DOWN", 40)    # BOLSA -> SAIR
            if self.foto and tentativa == 0:
                self.foto("batalha_sair")
            apertar(emu, "A", 340)
            for _ in range(60):  # ate' ~900q para fuga ou ataque inimigo
                if ler_cb2(emu) == CB2_OVERWORLD and overworld_estavel(emu):
                    resultado = self._classificar_fim_batalha(exp_antes)
                    print(f"  [batalha {numero}] fim: {resultado}; "
                          f"{onde(emu)}; {resumo_time(emu)}")
                    return resultado
                emu.rodar(15)
            print(f"  [batalha {numero}] fuga {tentativa + 1} nao encerrou")

        # Ultimo recurso: voltar ao menu principal e lutar com A
        # (LUTAR -> primeiro golpe), como na batalha do rival.
        print(f"  [batalha {numero}] fugir falhou; lutando")
        apertar(emu, "B", 100)
        for _ in range(260):
            if ler_cb2(emu) == CB2_OVERWORLD and overworld_estavel(emu):
                resultado = self._classificar_fim_batalha(exp_antes)
                print(f"  [batalha {numero}] fim: {resultado}; "
                      f"{onde(emu)}; {resumo_time(emu)}")
                return resultado
            apertar(emu, "A", 70)
        print(f"  [batalha {numero}] nao terminou: {onde(emu)}")
        return "falha"

    def checar_encontro(self) -> str | None:
        for _ in range(5):
            if ler_cb2(self.emu) != CB2_OVERWORLD:
                return self.resolver_batalha_selvagem()
            self.emu.rodar(3)
        return None

    # -- dialogo / controle ---------------------------------------------------
    def destravar_dialogo(self, max_pulsos: int = 80,
                          testar_antes: bool = True) -> bool:
        """Avanca textos/scripts com A ate' um passo responder de novo."""
        for pulso in range(max_pulsos):
            if ler_cb2(self.emu) != CB2_OVERWORLD:
                return self.resolver_batalha_selvagem() != "falha"
            if (testar_antes or pulso) and livre(self.emu):
                return True
            apertar(self.emu, "A", 45)
        return livre(self.emu)

    # -- movimento --------------------------------------------------------------
    def caminhar(self, direcao, condicao, maxp=40, rotulo="") -> bool:
        """Seguir uma direcao ate' a condicao, tratando encontros no meio."""
        travado = 0
        tentou_destravar = False
        for _ in range(maxp):
            if ler_cb2(self.emu) != CB2_OVERWORLD:
                self.resolver_batalha_selvagem()
            if condicao(pos(self.emu), mapa(self.emu)):
                return True
            if passo(self.emu, direcao):
                travado = 0
                self.checar_encontro()
                continue
            travado += 1
            if travado >= 2 and not tentou_destravar:
                tentou_destravar = True
                if self.destravar_dialogo(24):
                    continue
            if travado >= 3:
                print(f"  [{rotulo}] bloqueado: {onde(self.emu)}")
                return False
            self.emu.rodar(40)  # NPC pode sair da frente
        ok = condicao(pos(self.emu), mapa(self.emu))
        if not ok:
            print(f"  [{rotulo}] limite de passos: {onde(self.emu)}")
        return ok

    def explorador(
        self,
        *,
        criterio_fim,
        custo,
        rotulo: str,
        max_passos: int = 1200,
        mapas_interrupcao=CASA,
        ao_andar=None,
        parar_se_mudar_mapa: bool = False,
        paredes_iniciais=frozenset(),
    ) -> str:
        """Explora tile a tile; devolve chegou/whiteout/interrompido/falha."""
        emu = self.emu
        visitados: Counter[tuple[int, int]] = Counter()
        paredes: set[tuple[int, int]] = set(paredes_iniciais)
        mapa_segmento = mapa(emu)
        sem_saida = 0

        for numero in range(max_passos):
            if numero and numero % 120 == 0:
                # Um NPC parado nao e' parede eterna; as proibicoes
                # explicitas (portas/warps) continuam valendo.
                paredes = set(paredes_iniciais)
            if mapa(emu) != mapa_segmento:
                mapa_segmento = mapa(emu)
                visitados.clear()
                paredes = set(paredes_iniciais)
                if (parar_se_mudar_mapa
                        and not criterio_fim(pos(emu), mapa(emu))):
                    print(f"  [{rotulo}] mudou de mapa sem chegar: {onde(emu)}")
                    return "interrompido"
            if ler_cb2(emu) != CB2_OVERWORLD:
                self.resolver_batalha_selvagem()
                paredes = set(paredes_iniciais)
                if mapa(emu) in mapas_interrupcao:
                    return "whiteout" if mapa(emu) in CASA else "interrompido"
            if criterio_fim(pos(emu), mapa(emu)):
                print(f"  [{rotulo}] chegou em {numero} passos: {onde(emu)}")
                return "chegou"
            if mapa(emu) in mapas_interrupcao:
                return "whiteout" if mapa(emu) in CASA else "interrompido"

            atual = pos(emu)
            visitados[atual] += 1
            andou = False
            for _chave, direcao, alvo in ordenar_candidatos(
                    atual, custo, visitados, paredes):
                if passo(emu, direcao):
                    andou = True
                    self.checar_encontro()
                    if ao_andar:
                        ao_andar()
                    break
                paredes.add(alvo)

            if andou:
                sem_saida = 0
                continue
            sem_saida += 1
            print(f"  [{rotulo}] sem saida em {onde(emu)} (x{sem_saida})")
            if sem_saida >= 3:
                return "falha"
            self.destravar_dialogo(24)
            paredes = set(paredes_iniciais)

        ok = criterio_fim(pos(emu), mapa(emu))
        print(f"  [{rotulo}] {'chegou no limite' if ok else 'limite de passos'}"
              f": {onde(emu)}")
        return "chegou" if ok else "falha"

    def ir_para(self, alvo, mapa_esperado, rotulo: str,
                evitar=frozenset()) -> bool:
        resultado = self.explorador(
            criterio_fim=lambda p, m: m == mapa_esperado and p == alvo,
            custo=lambda x, y: abs(x - alvo[0]) + abs(y - alvo[1]),
            rotulo=rotulo,
            max_passos=360,
            mapas_interrupcao=(frozenset() if mapa_esperado in CASA else CASA),
            parar_se_mudar_mapa=True,
            paredes_iniciais=evitar,
        )
        return resultado == "chegou"

    # -- trechos ------------------------------------------------------------------
    def sair_do_terreo(self) -> bool:
        if not self.destravar_dialogo(100):
            return False
        if not self.ir_para((4, 8), TERREO, "casa-tapete"):
            return False
        mapa_antes = mapa(self.emu)
        passo(self.emu, "DOWN")  # a porta dispara descendo a partir do tapete
        if mapa(self.emu) == mapa_antes:
            espera_warp(self.emu, mapa_antes, "casa-porta")
        self.emu.rodar(60)
        print(f"  [casa] fora: {onde(self.emu)}")
        return mapa(self.emu) == PALLET

    def sair_do_lab(self) -> bool:
        """Recuperacao se um desvio entrar no lab sem querer: sair ao sul."""
        resultado = self.explorador(
            criterio_fim=lambda p, m: m == PALLET,
            custo=lambda x, y: -y,
            rotulo="lab-sair",
            max_passos=400,
        )
        self.emu.rodar(90)
        return resultado == "chegou" and mapa(self.emu) == PALLET

    def sair_de_pallet(self) -> bool:
        # Primeiro a horizontal MEDIDA ate' a coluna 12. Um Manhattan puro
        # a partir da frente do lab (16,14) empata LEFT/UP -- e UP e' a
        # porta/warp do lab (16,13). So' depois subir pela coluna 12.
        x_atual = pos(self.emu)[0]
        if x_atual > 12:
            self.caminhar("LEFT", lambda p, m: p[0] <= 12,
                          maxp=10, rotulo="pallet-oeste12")
        elif x_atual < 12:
            self.caminhar("RIGHT", lambda p, m: p[0] >= 12,
                          maxp=10, rotulo="pallet-leste12")
        if pos(self.emu)[0] == 12 and pos(self.emu)[1] > 3:
            self.caminhar("UP", lambda p, m: p[1] <= 3,
                          maxp=16, rotulo="pallet-norte12")
        if pos(self.emu) != (12, 3):
            portas = frozenset({(6, 7), (15, 7), (16, 13)})
            if not self.ir_para((12, 3), PALLET, "pallet-col12",
                                evitar=portas):
                return False
        if not self.caminhar("RIGHT", lambda p, m: p[0] >= 13,
                              maxp=2, rotulo="pallet-col13"):
            return False
        if not self.caminhar("UP", lambda p, m: p[1] <= 2,
                              maxp=2, rotulo="pallet-gatilho"):
            return False
        self.emu.rodar(60)  # a cena da senhora da placa comeca sozinha
        if not self.destravar_dialogo(80, testar_antes=False):
            return False
        if self.foto:
            self.foto("pallet_saida")
        if mapa(self.emu) == ROTA1:
            return True
        return self.caminhar("UP", lambda p, m: m == ROTA1,
                              maxp=5, rotulo="pallet-fora")

    def atravessar_rota1(self) -> str:
        self._menor_y_rota = pos(self.emu)[1]

        def progresso():
            if mapa(self.emu) != ROTA1:
                return
            y = pos(self.emu)[1]
            if self._menor_y_rota is None or y <= self._menor_y_rota - 8:
                self._menor_y_rota = y
                if self.checkpoint:
                    self.emu.salvar_estado(self.checkpoint)
                if self.foto:
                    self.foto(f"rota1_y{y}")
                print(f"  [rota1] marco y={y}: {onde(self.emu)}; "
                      f"{resumo_time(self.emu)}")

        return self.explorador(
            criterio_fim=lambda p, m: m == VIRIDIAN,
            custo=lambda x, y: y,
            rotulo="rota1",
            max_passos=self.max_passos_rota,
            mapas_interrupcao=CASA | {PALLET},
            ao_andar=progresso,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("core", type=Path)
    parser.add_argument("--estado", type=Path, required=True,
                        help="estado com o inicial (normalmente em Pallet)")
    parser.add_argument("--estado-saida", type=Path,
                        help="onde salvar o estado ao entrar em Viridian")
    parser.add_argument("--checkpoint", type=Path,
                        help="estado sobrescrito na entrada/marcos da Rota 1")
    parser.add_argument("--png-prefixo", type=Path)
    parser.add_argument("--max-tentativas", type=int, default=6,
                        help="trechos/retentativas apos whiteout (padrao 6)")
    parser.add_argument("--max-passos-rota", type=int, default=1400)
    args = parser.parse_args()

    emu = EmuladorConsole(args.rom, args.core)
    emu.carregar_estado(args.estado)
    emu.rodar(60)

    def foto(nome: str):
        if args.png_prefixo:
            destino = args.png_prefixo.with_name(
                f"{args.png_prefixo.name}_{nome}.png")
            emu.salvar_png(destino)
            print(f"  foto {destino.name}: {onde(emu)}")

    travessia = Travessia(
        emu,
        foto=foto if args.png_prefixo else None,
        checkpoint=args.checkpoint,
        max_passos_rota=args.max_passos_rota,
    )

    print(f"INICIO: {onde(emu)}; {resumo_time(emu)}")
    if party(emu) < 1 or primeiro_pokemon(emu).hp[0] <= 0:
        print("o estado nao tem um Pokemon vivo no time", file=sys.stderr)
        emu.fechar()
        return 1

    for tentativa in range(1, args.max_tentativas + 1):
        atual = mapa(emu)
        if atual == VIRIDIAN:
            break
        print(f"--- trecho {tentativa}: {onde(emu)}")
        if atual == QUARTO:
            fase_sair_de_casa(emu)
        elif atual == TERREO:
            travessia.sair_do_terreo()
        elif atual == LAB:
            travessia.sair_do_lab()
        elif atual == PALLET:
            if travessia.sair_de_pallet():
                print(f"NA ROTA 1: {onde(emu)}; {resumo_time(emu)}")
                if args.checkpoint:
                    emu.salvar_estado(args.checkpoint)
                foto("rota1_entrada")
        elif atual == ROTA1:
            travessia.atravessar_rota1()
        else:
            print(f"mapa inicial nao suportado: {onde(emu)}", file=sys.stderr)
            emu.fechar()
            return 1
    else:
        if mapa(emu) != VIRIDIAN:
            print(f"NAO chegou a Viridian: {onde(emu)}", file=sys.stderr)
            foto("falha")
            emu.fechar()
            return 1

    emu.rodar(150)  # assenta a conexao de mapa; nenhum passo a mais
    mon = primeiro_pokemon(emu)
    if mapa(emu) != VIRIDIAN or mon.hp[0] <= 0:
        print(f"chegada nao confirmada: {onde(emu)}; {resumo_time(emu)}",
              file=sys.stderr)
        emu.fechar()
        return 1

    print(f"CHEGOU A VIRIDIAN: {onde(emu)}; {resumo_time(emu)}")
    print(f"batalhas={travessia.batalhas} fugas={travessia.fugas} "
          f"lutas={travessia.lutas} whiteouts={travessia.whiteouts}")
    foto("chegada")
    if args.estado_saida:
        emu.salvar_estado(args.estado_saida)
        print(f"estado salvo em {args.estado_saida} "
              f"({args.estado_saida.stat().st_size} bytes) -- "
              "VALIDE num processo novo")
    emu.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
