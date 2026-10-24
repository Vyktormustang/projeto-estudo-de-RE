#!/usr/bin/env python3
"""E4: N batalhas com golpes aleatórios das Gen 4-9, sem travar.

Por que isso existe
-------------------
`verificar_rom.py` prova que os 797 golpes estão *bem gravados* no ROM, mas não
prova que a **batalha** sobrevive a um golpe cujo efeito caiu no fallback
(`EFFECT_HIT`/`EFFECT_SPLASH`). Um efeito desconhecido poderia mandar o script
de batalha para um `BattleScript_` que não existe e congelar o jogo — só um
battle de verdade mostra isso.

O teste
-------
Para cada rodada:

1. sorteia **4 golpes** do conjunto novo (IDs 355-796) e grava no time com
   `savestate.py pokemon --moves`;
2. entra na grama da Rota 1 e espera `gBattleTypeFlags != 0` (`nav.py`);
3. no battle, martela A (FIGHT + primeiro golpe) por ~1400 frames lendo
   `gBattleMons` a cada 100;
4. aprova a rodada se, ao fim: a batalha terminou **ou** o HP de alguém mudou.

HP que não muda em 1400 frames com A martelado = o jogo travou no script de
batalha (é exatamente o defeito que o fallback poderia causar).

Uso
---
    python3 scripts/firered/prova_golpes_e4.py --self-test
    python3 scripts/firered/prova_golpes_e4.py --preparar-estado   # cria /tmp/e4estado
    python3 scripts/firered/prova_golpes_e4.py --rodadas 6 --seed 1
"""
from __future__ import annotations

import argparse
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
ROM = Path("/tmp/pokefirered/pokefirered_modern.gba")
MAPA = Path("/tmp/pokefirered/pokefirered_modern.map")
CORE = Path("/tmp/mgba-0.10.5/build/mgba_libretro.so")
ESTADO = Path("/tmp/e4estado")

# espécie 700 = Sylveon (já no ROM desde a E1/E2), com tipo Fada
ESPECIE = 700
NIVEL = 60
# rota na Rota 1 (grupo 3, mapa 19) até a grama; medida na E3/2026-10-23
ROTA_GRAMA = "12,38;12,39;13,39;13,38"


# ------------------------------------------------------------------ leitura
def golpes_novos(poke: Path) -> list[int]:
    """IDs dos golpes das Gen 4-9 (os que a E4 acrescentou)."""
    texto = (poke / "include/constants/moves.h").read_text()
    ids = {n: int(v) for n, v in re.findall(r"^#define (MOVE_[A-Z0-9_]+) (\d+)$", texto, re.M)}
    return sorted(i for i in ids.values() if i >= 355)


def golpes_com_dano(poke: Path) -> set[int]:
    """IDs com poder > 0 na tabela de golpes (garante dano no teste)."""
    texto = (poke / "src/data/battle_moves.h").read_text()
    saida: set[int] = set()
    ids = {n: int(v) for n, v in re.findall(
        r"^#define (MOVE_[A-Z0-9_]+) (\d+)$",
        (poke / "include/constants/moves.h").read_text(), re.M)}
    for nome, corpo in re.findall(r"\[(MOVE_[A-Z0-9_]+)\] =\s*\n\s*\{(.*?)\n    \},", texto, re.S):
        m = re.search(r"\.power = (\d+)", corpo)
        if m and int(m.group(1)) > 0 and nome in ids:
            saida.add(ids[nome])
    return saida


def ler_hp(log: str) -> list[tuple[int, int, int]]:
    """Extrai [(frame, hp_jogador, hp_inimigo)] do log do `nav.py --batalha`."""
    por_frame: dict[int, dict[int, int]] = {}
    for f, i, hp in re.findall(r"^f\s*(\d+) b(\d) esp=.*hp=\s*(\d+)/", log, re.M):
        por_frame.setdefault(int(f), {})[int(i)] = int(hp)
    saida = []
    for f in sorted(por_frame):
        d = por_frame[f]
        if 0 in d and 1 in d:
            saida.append((f, d[0], d[1]))
    return saida


def classificar(hps: list[tuple[int, int, int]], texto: str) -> tuple[bool, str]:
    """-> (passou, motivo). Sem mudança de HP e sem fim de batalha = travou."""
    if not hps:
        return False, "nao li gBattleMons (batalha nao abriu?)"
    f0, j0, i0 = hps[0]
    _, jf, inf = hps[-1]
    if (jf, inf) != (j0, i0):
        return True, f"HP mudou: jogador {j0}->{jf}, inimigo {i0}->{inf}"
    if "condicao gBattleTypeFlags" in texto and len(hps) < 3:
        # batalha curta: terminou antes da primeira leitura cheia
        return True, "batalha terminou antes da leitura"
    return False, f"HP parado em jogador {j0} / inimigo {i0} ({len(hps)} leituras)"


# --------------------------------------------------------------- execução
def rodar(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def entrar_na_batalha(entrada: Path, saida: Path, outdir: Path) -> tuple[bool, str]:
    """Sobe e desce na grama até o RNG sortear um encontro.

    `--rota` não serve aqui: a entrada sul da Rota 1 é um corredor de 2 tiles
    entre cercas, e o roteador (que anda um eixo por vez) trava na cerca. Indo
    e voltando em linha reta o jogador pisa na grama toda hora.
    """
    passos = []
    for i in range(14):
        inicio = 50 + i * 220
        passos.append(f"{inicio}-{inicio + 150}:{'UP' if i % 2 == 0 else 'DOWN'}")
    r = rodar([sys.executable, str(AQUI / "nav.py"), "--rom", str(ROM), "--map", str(MAPA),
               "--outdir", str(outdir), "--in", str(entrada), "--out", str(saida),
               "--frames", "3400", "--script", ";".join(passos),
               "--parar-quando", "gBattleTypeFlags"])
    return "condicao gBattleTypeFlags" in r.stdout, r.stdout + r.stderr


def lutar(entrada: Path, outdir: Path, frames: int = 3200) -> str:
    # A a cada 40 frames: ~20 frames por letra na caixa de texto do FireRed,
    # entao pulsos de 55+ frames deixavam a batalha parada no "Wild X used Y!"
    pulsos = ",".join(f"{f}:A:6" for f in range(200, frames, 40))
    r = rodar([sys.executable, str(AQUI / "nav.py"), "--rom", str(ROM), "--map", str(MAPA),
               "--outdir", str(outdir), "--in", str(entrada), "--frames", str(frames),
               "--pulsos", pulsos, "--batalha", "100"])
    return r.stdout + r.stderr


def preparar_estado() -> int:
    """Cria `/tmp/e4estado/rota1.bin` (jogador na Rota 1, andando na grama).

    Receita (coordenadas tiradas de `data/maps/*/map.json`, não chutadas):

    | passo | de -> para                  | comando                                   |
    |-------|-----------------------------|-------------------------------------------|
    | 1     | título / menu / quarto 4:1  | A em pulsos (intro + fala do Oak + nome)   |
    | 2     | quarto (2,5) -> (11,2)      | `--ir-ate` UP e depois RIGHT               |
    | 3     | 4:1 -> 4:0 (escada em 10,2) | anda LEFT para dentro do tile de warp      |
    | 4     | 4:0 -> 3:0 (porta em 4,8)   | anda DOWN                                  |
    | 5     | 3:0 -> 3:19 (Rota 1)        | injeta o time (Oak não bloqueia mais) e sobe|
    | 6     | 3:19 -> grama (12,38)       | `--rota` com realimentação de posição      |
    """
    ESTADO.mkdir(parents=True, exist_ok=True)
    base = ESTADO / "passo"
    base.mkdir(exist_ok=True)

    def nav(nome: str, entrada: Path | None, saida: Path, frames: int,
            script: str = "", extra: list[str] | None = None) -> tuple[str, str]:
        cmd = [sys.executable, str(AQUI / "nav.py"), "--rom", str(ROM), "--map", str(MAPA),
               "--outdir", str(base / nome), "--frames", str(frames), "--out", str(saida),
               "--pos", "60",
               # `--shots -1` impede o `break` quando a rota termina: sem isso o
               # estado era salvo no instante da chegada (as vezes no meio do
               # passo/transicao) e o jogador ficava congelado ao carregar.
               "--shots", "-1"]
        if entrada:
            cmd += ["--in", str(entrada)]
        if script:
            cmd += ["--script", script]
        if extra:
            cmd += extra
        r = rodar(cmd)
        log = r.stdout + r.stderr
        if not saida.exists():
            raise SystemExit(f"falhou em {nome}:\n{log[-2000:]}")
        mapa = re.findall(r"mapa=(\d+:\d+)", log)
        pos = re.findall(r"pos=\((\d+),(\d+)\)", log)
        print(f"  {nome}: mapa {mapa[-1] if mapa else '?'} pos {pos[-1] if pos else '?'}")
        return (mapa[-1] if mapa else ""), (pos[-1] if pos else "")

    def exigir(obtido: tuple[str, str], mapa: str) -> None:
        if obtido[0] != mapa:
            raise SystemExit(f"esperava o mapa {mapa}, cheguei em {obtido[0]}")

    print("1/6 titulo -> menu -> quarto (4:1)")
    nav("titulo", None, ESTADO / "titulo.bin", 1800)
    nav("menu", ESTADO / "titulo.bin", ESTADO / "menu.bin", 2000, "20-40:START;60-70:A")
    script = ";".join(f"{i}-{i + 7}:A" for i in range(20, 4000, 24))
    exigir(nav("quarto", ESTADO / "menu.bin", ESTADO / "quarto.bin", 4200, script), "4:1")

    print("2/6 quarto -> (11,2) [anda pela direita e sobe]")
    nav("dir2f", ESTADO / "quarto.bin", ESTADO / "quarto_a.bin", 700,
        extra=["--ir-ate", "11,6,RIGHT"])
    nav("sobe2f", ESTADO / "quarto_a.bin", ESTADO / "quarto_b.bin", 700,
        extra=["--ir-ate", "11,2,UP"])

    print("3/6 escada 4:1 -> 4:0 (LEFT no tile 10,2)")
    exigir(nav("um_andar", ESTADO / "quarto_b.bin", ESTADO / "um_andar.bin", 700,
               "45-75:LEFT"), "4:0")

    print("4/6 porta 4:0 -> 3:0 (DOWN em 4,7)")
    nav("desce1f", ESTADO / "um_andar.bin", ESTADO / "um_andar_b.bin", 700,
        extra=["--ir-ate", "10,7,DOWN"])
    nav("esquerda1f", ESTADO / "um_andar_b.bin", ESTADO / "um_andar_c.bin", 700,
        extra=["--ir-ate", "4,7,LEFT"])
    exigir(nav("pallet", ESTADO / "um_andar_c.bin", ESTADO / "pallet.bin", 700,
               "60-90:DOWN"), "3:0")

    print("5/6 injetando time + dex + FLAG_SYS_POKEMON_GET")
    offsets = ESTADO / "offsets.json"
    if not offsets.exists():
        rodar([sys.executable, str(AQUI / "offsets.py"), "--pokefirered", "/tmp/pokefirered",
               "--gravar", str(offsets)])
    args = ["--map", str(MAPA), "--offsets", str(offsets), "--rom", str(ROM)]
    passo = ESTADO / "pallet.bin"
    for cmd in (
        ["pokemon", "--slot", "0", "--species", str(ESPECIE), "--level", str(NIVEL),
         "--moves", "355", "356", "357", "358"],
        ["dex", str(ESPECIE)],
        ["flag", "--set", "0x828"],          # FLAG_SYS_POKEMON_GET
        # VAR_MAP_SCENE_PALLET_TOWN_OAK != 0 desliga o script do Oak na saida
        # norte de Pallet (o gatilho fica em 12,1 e 13,1)
        ["var", "--id", "0x4050", "--valor", "1"],
    ):
        r = rodar([sys.executable, str(AQUI / "savestate.py"), *args,
                   "--in", str(passo), "--out", str(ESTADO / "pallet_time.bin"), *cmd])
        if not (ESTADO / "pallet_time.bin").exists():
            print(r.stdout, r.stderr)
            raise SystemExit(f"savestate.py {cmd[0]} falhou")
        passo = ESTADO / "pallet_time.bin"

    print("6/6 Pallet (3:0) -> Rota 1 (3:19) -> grama")
    nav("pallet_x12", ESTADO / "pallet_time.bin", ESTADO / "pallet_x12.bin", 900,
        extra=["--ir-ate", "12,7,RIGHT"])
    mapa, _ = nav("rota1_entrada", ESTADO / "pallet_x12.bin", ESTADO / "rota1_entrada.bin",
                  1600, "10-1200:UP")
    exigir((mapa, ""), "3:19")
    nav("grama", ESTADO / "rota1_entrada.bin", ESTADO / "rota1.bin", 1800,
        extra=["--rota", ROTA_GRAMA])

    # controle: o estado tem de aceitar comando depois de carregado. Savestate
    # tirado de outra build (mesmo que so' tenha mudado o .s das animacoes)
    # restaura com ponteiros de ROM que nao existem mais e congela o jogador.
    print("controle: o estado responde a comando?")
    if not estado_responde(ESTADO / "rota1.bin"):
        raise SystemExit("estado congelado: gere de novo com a ROM atual")
    print(f"estado pronto: {ESTADO / 'rota1.bin'}")
    return 0


def estado_responde(entrada: Path) -> bool:
    """Anda 120 frames para a esquerda e ve se a posicao mudou."""
    tmp = Path(tempfile.mkdtemp(prefix="e4ctrl_"))
    r = rodar([sys.executable, str(AQUI / "nav.py"), "--rom", str(ROM), "--map", str(MAPA),
               "--outdir", str(tmp), "--in", str(entrada), "--frames", "200",
               "--script", "10-160:UP", "--pos", "60"])
    pos = re.findall(r"pos=\((\d+),(\d+)\)", r.stdout)
    if len(pos) < 2:
        return False
    return pos[0] != pos[-1]


def rodadas(n: int, seed: int) -> int:
    if not (ESTADO / "rota1.bin").exists():
        print(f"falta {ESTADO / 'rota1.bin'}; rode --preparar-estado")
        return 2
    poke = Path("/tmp/pokefirered")
    novos = golpes_novos(poke)
    com_dano = golpes_com_dano(poke)
    novo_com_dano = [i for i in novos if i in com_dano]
    if len(novo_com_dano) < 8:
        print("poucos golpes novos com dano; a E4 foi aplicada?")
        return 2
    if not estado_responde(ESTADO / "rota1.bin"):
        print("estado congelado (savestate de outra build?): rode --preparar-estado")
        return 2
    offsets = ESTADO / "offsets.json"
    rng = random.Random(seed)
    falhas = 0
    for i in range(1, n + 1):
        # o primeiro slot e' sempre um golpe de dano (o teste martela A, entao e'
        # ele que executa); os outros 3 sao aleatorios e servem para o menu
        dano = rng.choice(novo_com_dano)
        time = [dano] + rng.sample([m for m in novos if m != dano], 3)
        tmp = Path(tempfile.mkdtemp(prefix=f"e4b{i}_"))
        entrada = tmp / "entrada.bin"
        r = rodar([sys.executable, str(AQUI / "savestate.py"), "--map", str(MAPA),
                   "--offsets", str(offsets), "--rom", str(ROM),
                   "--in", str(ESTADO / "rota1.bin"), "--out", str(entrada),
                   "pokemon", "--slot", "0", "--species", str(ESPECIE),
                   "--level", str(NIVEL), "--moves", *map(str, time)])
        if not entrada.exists():
            print(f"rodada {i}: savestate falhou\n{r.stdout}\n{r.stderr}")
            falhas += 1
            continue
        ok, log = entrar_na_batalha(entrada, tmp / "batalha.bin", tmp / "nav1")
        if not ok:
            print(f"rodada {i}: nao entrou em batalha\n  {log.strip().splitlines()[-1][:160]}")
            falhas += 1
            continue
        # duas tentativas: golpe que erra + inimigo que usa status no mesmo turno
        # nao muda HP nenhum e nao e' travamento
        passou, motivo = False, ""
        for tentativa in (1, 2):
            log = lutar(tmp / "batalha.bin", tmp / f"nav2_{tentativa}")
            hps = ler_hp(log)
            passou, motivo = classificar(hps, log)
            if passou:
                break
        extra = "" if tentativa == 1 else " [2a tentativa]"
        print(f"rodada {i}: golpes {time} -> {'ok' if passou else 'TRAVOU'} ({motivo}){extra}")
        if not passou:
            falhas += 1
            print(f"  log: {tmp}")
    print(f"\n{ n - falhas }/{n} rodadas ok")
    return 0 if falhas == 0 else 1


# --------------------------------------------------------------- self-test
def self_test() -> int:
    """Testa o parser de HP e a classificação, sem emulador."""
    log = (
        "f  100 b0 esp= 700 nv= 60 hp= 180/180 atk= 65 def= 65 spa=110 spd=130 tipos=[18, 10]\n"
        "f  100 b1 esp= 400 nv=  50 hp= 108/108 atk= 53 def= 60 spa= 50 spd= 68 tipos=[16, 9]\n"
        "f  200 b0 esp= 700 nv= 60 hp= 180/180 atk= 65 def= 65 spa=110 spd=130 tipos=[18, 10]\n"
        "f  200 b1 esp= 400 nv=  50 hp=  79/108 atk= 53 def= 60 spa= 50 spd= 68 tipos=[16, 9]\n"
    )
    hps = ler_hp(log)
    assert hps == [(100, 180, 108), (200, 180, 79)], hps
    ok, motivo = classificar(hps, "")
    assert ok and "inimigo 108->79" in motivo, motivo

    parado = [(100, 180, 108), (200, 180, 108), (300, 180, 108)]
    ok, motivo = classificar(parado, "")
    assert not ok and "HP parado" in motivo, motivo

    ok, motivo = classificar([], "")
    assert not ok and "nao li" in motivo, motivo

    # batalha que acaba antes da primeira leitura completa conta como ok
    ok, motivo = classificar([(100, 180, 108)], "condicao gBattleTypeFlags != 0 no frame 400")
    assert ok, motivo

    # golpes novos: ids >= 355 e sem MOVE_NONE
    fake = Path(tempfile.mkdtemp())
    (fake / "include/constants").mkdir(parents=True)
    (fake / "src/data").mkdir(parents=True)
    (fake / "include/constants/moves.h").write_text(
        "#define MOVE_NONE 0\n#define MOVE_POUND 1\n#define MOVE_ROOST 355\n"
        "#define MOVE_GRAVITY 356\n#define MOVES_COUNT 357\n")
    (fake / "src/data/battle_moves.h").write_text(
        "    [MOVE_ROOST] =\n    {\n        .power = 0,\n        .type = TYPE_FLYING,\n    },\n"
        "    [MOVE_GRAVITY] =\n    {\n        .power = 60,\n        .type = TYPE_PSYCHIC,\n    },\n")
    assert golpes_novos(fake) == [355, 356], golpes_novos(fake)
    assert golpes_com_dano(fake) == {356}, golpes_com_dano(fake)

    print("self-test ok: parser de HP, classificação de travamento e seleção de golpes")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rodadas", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--preparar-estado", action="store_true")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.preparar_estado:
        return preparar_estado()
    if not shutil.which("python3"):
        print("python3 fora do PATH")
        return 2
    return rodadas(a.rodadas, a.seed)


if __name__ == "__main__":
    sys.exit(main())
