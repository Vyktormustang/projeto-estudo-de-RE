#!/usr/bin/env python3
"""E7: prova em jogo que uma espécie de Gen 9 aparece selvagem na Rota 1.

Por que isso existe
-------------------
`verificar_rom.py` prova que a tabela de encontros **dentro do ROM** tem
Lechonk/Skwovet na grama da Rota 1. Isso não prova que o jogo **sorteia** essas
posições: um `wild_encounters.h` gerado errado, um `NUM_SPECIES` fora de lugar ou
uma tabela deslocada continuam "certos" no arquivo e nunca aparecem na tela.

Esta prova **não altera a ROM**. Ela carrega o savestate da Rota 1, anda na
grama e lê a espécie do inimigo direto de `gBattleMons[1]` (via `nav.py
--batalha`). É a diferença em relação às provas da E4/E5: lá um byte da ROM de
prova era trocado para forçar o selvagem; aqui o selvagem tem de sair da tabela
do jogo entregue.

Como o sorteio é vencido sem trapaça
------------------------------------
O encontro depende de `gRngValue`, que avança a cada passo. Carregar o mesmo
savestate e andar sempre igual daria **sempre a mesma** espécie. Por isso cada
tentativa usa um roteiro de passos diferente (fase do padrão sobe/deseja), o que
consome um número diferente de draws: em ~30 tentativas a distribuição da
tabela aparece (20% Lechonk + 10% Skwovet = 30% de espécie nova).

Critério de aprovação
---------------------
1. apareceu **alguma** espécie >= 387 (as Gen 4-9 do projeto);
2. apareceu **alguma** de Gen 9 (>= 906, que é Nacli);
3. com `--capturar`, a Poké Ball pega um dos selvagens novos e o time do jogador
   cresce de 1 para 2 — o estado final é lido pelo `savestate.py`, não pela tela.

Uso
---
    python3 scripts/firered/prova_encontros_e7.py --self-test
    python3 scripts/firered/prova_encontros_e7.py --prova
    python3 scripts/firered/prova_encontros_e7.py --prova --capturar --shots /tmp/e7shots
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PADRAO_PF = Path("/tmp/pokefirered")
CORE = Path("/tmp/mgba-0.10.5/build/mgba_libretro.so")
ESTADO = Path("/tmp/e4estado/rota1.bin")
OFFSETS = Path("/tmp/pf_offsets.json")

SPECIES_NOVAS = 387      # Gen 4-9 neste projeto
SPECIES_GEN9 = 906       # Nacli
ITEM_POKE_BALL = 4       # ITEM_POKE_BALL do FireRed (constantes de item)
MAX_TENTATIVAS = 30


# --------------------------------------------------------------------------- #
# nav / savestate
# --------------------------------------------------------------------------- #
def rodar(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout + r.stderr


def nav(rom: Path, mapa: Path, *, entrada: Path | None = None, saida: Path | None = None,
        outdir: Path, frames: int, script: str = "", pulsos: str = "",
        parar_quando: str = "", batalha: int = 0, every: int = 0,
        offsets: Path | None = None, shots: str = "") -> str:
    cmd = [sys.executable, str(AQUI / "nav.py"), "--rom", str(rom), "--map", str(mapa),
           "--outdir", str(outdir), "--frames", str(frames)]
    if CORE.exists():
        cmd += ["--core", str(CORE)]
    if entrada:
        cmd += ["--in", str(entrada)]
    if saida:
        cmd += ["--out", str(saida)]
    if script:
        cmd += ["--script", script]
    if pulsos:
        cmd += ["--pulsos", pulsos]
    if parar_quando:
        cmd += ["--parar-quando", parar_quando]
    if batalha:
        cmd += ["--batalha", str(batalha)]
    if every:
        cmd += ["--every", str(every)]
    if shots:
        cmd += ["--shots", shots]
    if offsets:
        cmd += ["--offsets", str(offsets)]
    return rodar(cmd)


def ler_especie_inimiga(log: str) -> int | None:
    """Última espécie lida do battler 1 (`b1 esp=`) — o selvagem."""
    achados = re.findall(r"b1 esp=\s*(\d+)", log)
    return int(achados[-1]) if achados else None


def roteiro(tentativa: int) -> str:
    """Passos UP/DOWN com fase diferente: muda quantos draws de RNG acontecem."""
    fases = [3, 5, 4, 6, 2, 7, 3, 5]      # passos por bloco
    passos = fases[tentativa % len(fases)]
    ini = 40 + (tentativa % 5) * 9         # desloca o começo no tempo
    blocos = []
    for i in range(16):
        a = ini + i * (passos * 20)
        blocos.append(f"{a}-{a + passos * 16}:{'UP' if i % 2 == 0 else 'DOWN'}")
    return ";".join(blocos)


# --------------------------------------------------------------------------- #
# preparar o estado da Rota 1
# --------------------------------------------------------------------------- #
def preparar_estado(pf: Path, forcar: bool = False) -> None:
    if ESTADO.exists() and not forcar:
        return
    log = rodar([sys.executable, str(AQUI / "prova_golpes_e4.py"), "--preparar-estado"])
    if not ESTADO.exists():
        raise SystemExit("nao consegui preparar o estado da Rota 1:\n" + log[-3000:])


def offsets_json(pf: Path) -> Path:
    if OFFSETS.exists():
        return OFFSETS
    log = rodar([sys.executable, str(AQUI / "offsets.py"), "--pokefirered", str(pf), "--json"])
    # o --json escreve em stdout junto com o log; pega o último bloco {...}
    m = re.search(r"\{.*\}\s*$", log, re.S)
    if not m:
        raise SystemExit("offsets.py --json nao devolveu JSON:\n" + log[-1500:])
    OFFSETS.write_text(m.group(0))
    return OFFSETS


# --------------------------------------------------------------------------- #
# a prova
# --------------------------------------------------------------------------- #
def encontrar(pf: Path, tentativas: int, outdir: Path, shots: Path | None) -> dict:
    """Anda na grama até ver um selvagem novo; devolve o resultado por tentativa."""
    rom = pf / "pokefirered_modern.gba"
    mapa = pf / "pokefirered_modern.map"
    off = offsets_json(pf)
    outdir.mkdir(parents=True, exist_ok=True)
    vistas: list[dict] = []
    for t in range(tentativas):
        d = outdir / f"t{t:02d}"
        d.mkdir(parents=True, exist_ok=True)
        estado = d / "batalha.bin"
        log = nav(rom, mapa, entrada=ESTADO, saida=estado, outdir=d, frames=1500,
                  script=roteiro(t), parar_quando="gBattleTypeFlags", batalha=50,
                  offsets=off)
        if not estado.exists() or "condicao gBattleTypeFlags" not in log:
            vistas.append({"t": t, "esp": None, "log": log[-400:]})
            continue
        # lê 3 vezes dentro da batalha: a primeira leitura pode pegar a transição
        log += nav(rom, mapa, entrada=estado, saida=d / "dentro.bin", outdir=d,
                   frames=180, batalha=40, offsets=off,
                   pulsos="" if not shots else "")
        esp = ler_especie_inimiga(log)
        vistas.append({"t": t, "esp": esp, "estado": str(estado), "log": log[-600:]})
        if esp is not None and esp >= SPECIES_NOVAS:
            print(f"  tentativa {t}: selvagem {esp} (nova)")
            if shots and esp >= SPECIES_GEN9:
                (d / "gen9.bin").write_bytes(estado.read_bytes())
                break
        else:
            print(f"  tentativa {t}: selvagem {esp}" if esp else f"  tentativa {t}: sem batalha")
    return {"vistas": vistas}


def capturar(pf: Path, estado: Path, outdir: Path, max_bolas: int = 1) -> dict:
    """Tenta pegar o selvagem com Poké Ball, lendo o time do estado final.

    O time do jogador é a fonte da verdade: se o selvagem foi capturado, o
    `gPlayerPartyCount` do savestate sobe de 1 para 2 (e o `savestate.py party`
    mostra a espécie nova). Nada de julgar por mensagem na tela.
    """
    rom = pf / "pokefirered_modern.gba"
    mapa = pf / "pokefirered_modern.map"
    off = offsets_json(pf)
    outdir.mkdir(parents=True, exist_ok=True)
    # Poké Bolas na bolsa: 20 na primeira posição da pocket de bolas. Sem isso o
    # menu BAG abre vazio e a prova de captura não teria como acontecer.
    com_bolas = outdir / "com_bolas.bin"
    if estado != com_bolas:
        com_bolas.write_bytes(estado.read_bytes())
        rodar([sys.executable, str(AQUI / "savestate.py"), "--map", str(mapa),
               "--offsets", str(off), "--in", str(com_bolas), "--out", str(com_bolas),
               "item", "--pocket", "pokeballs", "--slot", "0",
               "--id", str(ITEM_POKE_BALL), "--qtd", "20"])
    antes = contar_time(pf, mapa, off, com_bolas)
    # A introdução da batalha ("Wild X appeared!") come sozinha ~700 frames: os
    # pulsos têm de começar DEPOIS dela. Sequência por bola:
    #   RIGHT (cursor FIGHT -> BAG), A (abre a bolsa), RIGHT (pocket ITEMS ->
    #   POKé BALLS), A (escolhe a bola), A (usa no selvagem).
    # Sequência medida lendo a tela a cada 100 frames (cada erro custou uma rodada):
    #   600-780  A x4  -> a abertura "Wild X appeared! / Go! Y!" termina (4 caixas)
    #   850      RIGHT -> cursor FIGHT -> BAG
    #   950      A     -> a bolsa abre em KEY ITEMS (a pocket fica memorizada)
    #   1080/1180 RIGHT x2 -> POKé BALLS
    #   1300     A     -> "POKé BALL is selected" (USE)
    #   1500     A     -> "AAAAAAA used POKé BALL!"
    #   2400     ~     -> "Gotcha! X was caught!"
    #   3300     ~     -> teclado de apelido ("X's nickname?") -> A x8 e o time
    #                     passa de 1 para 2 (lido em gPlayerPartyCount)
    INICIO = 600
    pulsos = ["600:A", "660:A", "720:A", "780:A", "850:RIGHT", "950:A",
              "1080:RIGHT", "1180:RIGHT", "1300:A", "1500:A"]
    # fim do fluxo: fecha o teclado do apelido e as mensagens
    # Depois do "Gotcha! X was caught!" o jogo abre o teclado de apelido
    # ("X's nickname?") por volta do frame 3000. A tecla que conclui é
    # **START** (o rodapé mostra "START ▶" e depois o OK) seguida de A —
    # medido na tela: com A sozinho o teclado fica aberto para sempre e o
    # time nunca cresce. O corte com START é o que fecha.
    for f in range(1700, 3400, 150):
        pulsos.append(f"{f}:A")
    # O frame em que o teclado abre DESLIZA (nº de balançadas da bola e das
    # caixas de texto varia com o RNG) — um único START em 3500 já perdeu o
    # teclado numa regressão. START repetido + A cobre a janela 3500..5900;
    # os extras caem no overworld/menu e não mudam gPlayerPartyCount.
    for inicio_start in (3500, 4400, 5300):
        pulsos.append(f"{inicio_start}:START")
        for f in range(inicio_start + 150, inicio_start + 900, 150):
            pulsos.append(f"{f}:A")
    log = nav(rom, mapa, entrada=com_bolas, saida=outdir / "depois.bin", outdir=outdir,
              frames=6400, pulsos=",".join(pulsos),
              every=100, offsets=off)
    depois = contar_time(pf, mapa, off, outdir / "depois.bin")
    return {"antes": antes, "depois": depois,
            "capturado": depois is not None and antes is not None and depois > antes,
            "log": log[-1500:]}


# `gPlayerPartyCount` é a fonte da verdade DURANTE o jogo (o `savestate.py party`
# lê o SaveBlock1, que só é preenchido ao salvar — usá-lo aqui dava sempre 1).
GPLAYERPARTYCOUNT = 0x0203A6AD
EWRAM_BASE = 0x21000


def simb_em_memoria(mapa: Path, nome: str) -> int | None:
    texto = Path(mapa).read_text(errors="replace")
    m = re.search(rf"\s0x(02[0-9a-f]{{6}})\s+{nome}", texto)
    return int(m.group(1), 16) if m else None


def contar_time(pf: Path, mapa: Path, off: Path, estado: Path) -> int | None:
    """Nº de Pokémon do time, lido do savestate (EWRAM global)."""
    if not estado.exists():
        return None
    addr = simb_em_memoria(mapa, "gPlayerPartyCount") or GPLAYERPARTYCOUNT
    d = estado.read_bytes()
    o = EWRAM_BASE + (addr - 0x02000000)
    return d[o] if 0 <= o < len(d) else None


def especies_no_time(pf: Path, mapa: Path, off: Path, estado: Path) -> list[int]:
    """Espécies do time lidas direto de `gPlayerParty` (EWRAM).

    O `savestate.py party` lê o SaveBlock1, que só é preenchido ao SALVAR — por
    isso ele dizia "1 mon" mesmo com o Pokémon capturado. Aqui leio a variável
    global `gPlayerParty` e reuso `savestate.ler_pokemon`, que já decripta o
    bloco de 48 B e reordena os 4 substructs pelo `personality % 24`
    (implementar isso à mão deu espécie 25856 no lugar de 915).
    """
    if not estado.exists():
        return []
    m = re.search(r"\s0x(02[0-9a-f]{6})\s+gPlayerParty\s*$",
                  Path(mapa).read_text(errors="replace"), re.M)
    if not m:
        return []
    o = EWRAM_BASE + (int(m.group(1), 16) - 0x02000000)
    d = estado.read_bytes()
    qtd = contar_time(pf, mapa, off, estado) or 0
    sys.path.insert(0, str(AQUI))
    import savestate as ss   # mesma decriptação e ordem de substructs do jogo
    saida = []
    for slot in range(qtd):
        base = o + slot * ss.TAMANHO_POKEMON
        if base + ss.TAMANHO_POKEMON > len(d):
            break
        saida.append(ss.ler_pokemon(d[base:base + ss.TAMANHO_POKEMON])["especie"])
    return saida


def self_test() -> int:
    ok = 0

    # 1. leitura da espécie: pega a última, que é a que vale
    log = "f 100 b0 esp= 700 nv= 60\nf 100 b1 esp=  915 nv=  3\n"
    assert ler_especie_inimiga(log) == 915
    log += "f 140 b1 esp=  819 nv=  4\n"
    assert ler_especie_inimiga(log) == 819
    assert ler_especie_inimiga("nada aqui") is None
    ok += 1

    # 2. os limiares: 386 é Gen 3 (vanilla), 387 é novo, 906 é Gen 9
    assert 386 < SPECIES_NOVAS and 905 < SPECIES_GEN9 and SPECIES_GEN9 <= 1025
    ok += 1

    # 3. o roteiro muda de fase a cada tentativa (senão o RNG não muda)
    # o período é lcm(len(fases)=8, 5 deslocamentos) = 40 tentativas
    r0, r1 = roteiro(0), roteiro(1)
    assert r0 != r1 and r0 == roteiro(40), "roteiro tem de variar e repetir com periodo 40"
    assert all(re.fullmatch(r"\d+-\d+:(UP|DOWN)", p) for p in r0.split(";"))
    ok += 1

    # 4. o roteiro cobre o tempo todo (blocos em ordem crescente, sem sobrepor)
    inicios = [int(p.split("-")[0]) for p in roteiro(3).split(";")]
    assert inicios == sorted(inicios) and len(set(inicios)) == len(inicios)
    ok += 1

    # 5. contagem do time no log do savestate
    falso = "time: 2 mon(s)\n  slot 0: especie 700 nivel 60\n  slot 1: especie 915 nivel 3\n"
    assert re.search(r"time:\s*(\d+)", falso).group(1) == "2"
    assert [int(x) for x in re.findall(r"esp[eé]cie\s+(\d+)", falso)] == [700, 915]
    ok += 1

    # 6. contagem do time lida do savestate: gPlayerPartyCount na EWRAM
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    mapa = tmp / "x.map"
    mapa.write_text("                0x0203a6ad                gPlayerPartyCount\n"
                    "                0x0203a908                gPlayerParty\n")
    d = bytearray(EWRAM_BASE + (0x0203A908 - 0x02000000) + 200)
    d[EWRAM_BASE + (0x0203A6AD - 0x02000000)] = 2
    (tmp / "e.bin").write_bytes(bytes(d))
    assert contar_time(tmp, mapa, tmp / "o.json", tmp / "e.bin") == 2
    ok += 1

    # 7. espécies do time: usa a decriptação do savestate (ordem de substructs
    #    pelo personality % 24). Monta um mon com o próprio savestate e lê de volta.
    sys.path.insert(0, str(AQUI))
    import savestate as ss
    base = EWRAM_BASE + (0x0203A908 - 0x02000000)
    (tmp / "e2.bin").write_bytes(bytes(d))
    d2 = bytearray((tmp / "e2.bin").read_bytes())
    mon = ss.montar_pokemon(915, 3, [33, 39], (70, 85, 145, 65, 60, 55), b"LECHONK",
                            pid=0x0FCD3D3F, otid=0x5B74DF39, ot=b"AAAAAAA")
    d2[base:base + len(mon)] = mon
    d2[EWRAM_BASE + (0x0203A6AD - 0x02000000)] = 1
    (tmp / "e2.bin").write_bytes(bytes(d2))
    assert especies_no_time(tmp, mapa, tmp / "o.json", tmp / "e2.bin") == [915], \
        especies_no_time(tmp, mapa, tmp / "o.json", tmp / "e2.bin")
    ok += 1

    print(f"self-test ok: {ok} casos (leitura do selvagem, limiares, fase do roteiro, "
          f"contagem do time, especies do time)")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="E7: selvagem de Gen 9 na Rota 1")
    ap.add_argument("--pokefirered", type=Path, default=PADRAO_PF)
    ap.add_argument("--prova", action="store_true")
    ap.add_argument("--capturar", action="store_true")
    ap.add_argument("--preparar", action="store_true", help="refaz o savestate da Rota 1")
    ap.add_argument("--tentativas", type=int, default=MAX_TENTATIVAS)
    ap.add_argument("--shots", type=Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.prova:
        ap.error("use --prova (ou --self-test)")

    pf = a.pokefirered
    for c in (pf / "pokefirered_modern.gba", pf / "pokefirered_modern.map"):
        if not c.exists():
            raise SystemExit(f"nao achei {c}; compile antes")

    preparar_estado(pf, forcar=a.preparar)
    tmp = Path(tempfile.mkdtemp(prefix="e7prova_"))
    out = a.shots or tmp

    print(f"procurando selvagem novo na Rota 1 ({a.tentativas} tentativas)...")
    r = encontrar(pf, a.tentativas, out / "encontros", a.shots)
    vistas = [v["esp"] for v in r["vistas"] if v.get("esp")]
    novas = [e for e in vistas if e >= SPECIES_NOVAS]
    gen9 = [e for e in novas if e >= SPECIES_GEN9]
    print(f"encontros: {len(vistas)} batalhas, especies {sorted(set(vistas))}")
    print(f"  novas (>= {SPECIES_NOVAS}): {sorted(set(novas))}")
    print(f"  Gen 9 (>= {SPECIES_GEN9}): {sorted(set(gen9))}")

    falhas = []
    if not vistas:
        falhas.append("nenhuma batalha aconteceu — a prova nao vale")
    if not novas:
        falhas.append("nenhuma especie das Gen 4-9 apareceu na Rota 1")
    if not gen9:
        falhas.append("nenhuma especie de Gen 9 apareceu na Rota 1")

    if a.capturar and gen9:
        alvo = next(v for v in r["vistas"] if v.get("esp") in gen9)
        print(f"tentando capturar a especie {alvo['esp']}...")
        c = capturar(pf, Path(alvo["estado"]), out / "captura")
        print(f"  time antes: {c['antes']} -> depois: {c['depois']}")
        if not c["capturado"]:
            falhas.append("a captura nao aconteceu (time nao cresceu)")
        else:
            mons = especies_no_time(pf, pf / "pokefirered_modern.map",
                                    offsets_json(pf), out / "captura" / "depois.bin")
            print(f"  time final: {mons}")
            if alvo["esp"] not in mons:
                falhas.append(f"o time cresceu mas sem a especie {alvo['esp']}: {mons}")

    for f in falhas:
        print("  FALHA: " + f)
    print("APROVADO" if not falhas else "REPROVADO")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
