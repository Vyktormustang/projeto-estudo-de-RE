#!/usr/bin/env python3
"""E5: prova em batalha que uma habilidade de Gen 9 funciona (Earth Eater).

Por que isso existe
-------------------
`verificar_rom.py` prova que as 321 habilidades estão *gravadas* e que cada
espécie nova aponta para a habilidade certa — mas não prova que o motor **usa**
a habilidade. Habilidade sem `case` no `battle_util.c` não trava e não avisa:
simplesmente não acontece nada. Só uma batalha de verdade separa as duas coisas.

Como o teste funciona
---------------------
O selvagem da Rota 1 é trocado por **um Orthworm** (No968, habilidade Earth
Eater) — não no jogo entregue, e sim numa **cópia da ROM** com 2 bytes mudados
no `gWildMonHeaders`. Depois:

| batalha | golpe do jogador | Orthworm tem Earth Eater? | esperado       |
|---------|------------------|---------------------------|----------------|
| A       | TACKLE (Normal)  | sim                       | HP do inimigo **cai** |
| B       | BULLDOZE (Terra) | sim                       | HP do inimigo **não cai** |

A é o **controle**: sem ela, "HP parado" poderia ser só "a batalha não rodou".
É o mesmo desenho diferencial da E3 (29 vs 38 de dano), que funcionou.

O `savestate.py` grava o time do jogador (golpes no slot 1) e o `nav.py` entra
na grama da Rota 1 e martela A até o fim da luta, lendo `gBattleMons` a cada
100 frames.

Como o encontro é achado no ROM (sem chutar endereço)
-----------------------------------------------------
`gWildMonHeaders` vem do `.map`; o passo da struct (20 B) é **medido** tentando
16/20/24 e escolhendo o que faz a entrada `mapGroup=3, mapNum=19` apontar para
um `WildPokemonInfo` com `encounterRate=21` e 12 slots de nível 2-5 — os
números que estão em `src/data/wild_encounters.h`. Se não bater, o script para
em vez de escrever em endereço errado.

Uso
---
    python3 scripts/firered/prova_habilidades_e5.py --self-test
    python3 scripts/firered/prova_habilidades_e5.py --prova
    python3 scripts/firered/prova_habilidades_e5.py --prova --shots /tmp/e5shots
"""
from __future__ import annotations

import argparse
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
PADRAO_PF = Path("/tmp/pokefirered")
CORE = Path("/tmp/mgba-0.10.5/build/mgba_libretro.so")
ESTADO = Path("/tmp/e4estado/rota1.bin")      # Rota 1, em cima da grama (E4)
GRUPO_ROTA1, MAPA_ROTA1 = 3, 19
TAXA_ROTA1 = 21                                # sRoute1_FireRed_LandMonsInfo.encounterRate

SPECIES_ORTHWORM = 968
SPECIES_RATTATA = 19
MOVE_TACKLE = 33
MOVE_BULLDOZE = 519
NIVEL_SELVAGEM = 30
# medidos no ROM (ver verificar_rom.py): struct SpeciesInfo = 28 B, abilities em 0x16
TAM_ESPECIE = 28
OFF_HABILIDADES = 0x16
# o ID da habilidade vem do header (a E5 ordena as usadas para caber em u8)
ABILITY_EARTH_EATER = 0
NIVEL_JOGADOR = 60
ESPECIE_JOGADOR = 700                          # Sylveon (Fada) — não tem Earth Eater


# --------------------------------------------------------------------------
# encontro no ROM
# --------------------------------------------------------------------------
def ler_simbolos(mapa: Path) -> dict[str, int]:
    saida: dict[str, int] = {}
    for linha in Path(mapa).read_text(errors="replace").splitlines():
        m = re.match(r"\s+0x([0-9a-fA-F]{8})\s+(\w+)$", linha.rstrip())
        if m:
            saida[m.group(2)] = int(m.group(1), 16)
    return saida


def achar_encontro(rom: bytes, simbolos: dict[str, int]) -> tuple[int, int, int]:
    """-> (offset do array de slots, offset do WildPokemonInfo, passo medido)."""
    if "gWildMonHeaders" not in simbolos:
        raise SystemExit("gWildMonHeaders fora do .map")
    base = simbolos["gWildMonHeaders"] - 0x08000000
    for passo in (20, 16, 24):
        for k in range(0, 400):
            o = base + passo * k
            if o + passo > len(rom):
                break
            if rom[o] != GRUPO_ROTA1 or rom[o + 1] != MAPA_ROTA1:
                continue
            info = struct.unpack_from("<I", rom, o + 4)[0]
            if not 0x08000000 <= info < 0x0A000000:
                continue
            oi = info - 0x08000000
            if rom[oi] != TAXA_ROTA1:
                continue
            arr = struct.unpack_from("<I", rom, oi + 4)[0]
            if not 0x08000000 <= arr < 0x0A000000:
                continue
            oa = arr - 0x08000000
            niveis = [rom[oa + 4 * i] for i in range(12)]
            especies = [struct.unpack_from("<H", rom, oa + 4 * i + 2)[0] for i in range(12)]
            if not all(1 <= n <= 10 for n in niveis):
                continue
            if not all(1 <= e <= 386 for e in especies):
                continue
            return oa, oi, passo
    raise SystemExit("não achei a tabela de encontros da Rota 1 (não vou chutar endereço)")


def rom_com_selvagem(origem: Path, destino: Path, especie: int, nivel: int,
                     simbolos: dict[str, int], *,
                     sem_habilidade: bool = False,
                     poke: Path | None = None) -> Path:
    """Copia a ROM e troca **os 12 slots** da grama da Rota 1 por `especie`/`nivel`.

    Trocar só o slot 0 não serve: o jogo sorteia entre os 12, e a batalha de
    controle abriu com um Rattata nível 3 (HP 15) em vez do Orthworm nível 30.
    """
    rom = bytearray(origem.read_bytes())
    oa, _, _ = achar_encontro(rom, simbolos)
    for i in range(12):
        struct.pack_into("<BBH", rom, oa + 4 * i, nivel, nivel, especie)
    if sem_habilidade:
        # prova negativa: o MESMO Orthworm sem habilidade tem de levar dano
        if "gSpeciesInfo" not in simbolos:
            raise SystemExit("gSpeciesInfo fora do .map")
        o = simbolos["gSpeciesInfo"] - 0x08000000 + TAM_ESPECIE * especie + OFF_HABILIDADES
        poke = poke or origem.parent
        e_u16 = "u16 abilities[2]" in (poke / "include/pokemon.h").read_text(errors="replace")
        if e_u16:
            lido = struct.unpack_from("<2H", rom, o)[0]
        else:
            lido = rom[o]
        if lido != ABILITY_EARTH_EATER:
            raise SystemExit(f"espécie {especie}: habilidade {lido}, esperava "
                             f"{ABILITY_EARTH_EATER} (layout mudou? não vou zerar no escuro)")
        # zera os dois slots no layout ATUAL (u8: 2 bytes; u16: 4 bytes)
        rom[o:o + (4 if e_u16 else 2)] = b"\x00" * (4 if e_u16 else 2)
    destino.write_bytes(rom)
    return destino


# --------------------------------------------------------------------------
# batalha
# --------------------------------------------------------------------------
def rodar(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def nav(**kw) -> str:
    cmd = [sys.executable, str(AQUI / "nav.py")]
    if CORE.exists():
        cmd += ["--core", str(CORE)]
    for chave, valor in kw.items():
        if valor is None:
            continue
        cmd += [f"--{chave.rstrip('_').replace('_', '-')}", str(valor)]
    r = rodar(cmd)
    return r.stdout + r.stderr


def ler_hp(log: str) -> list[tuple[int, int, int]]:
    """[(frame, hp_jogador, hp_inimigo)] do log do `nav.py --batalha`."""
    por_frame: dict[int, dict[int, int]] = {}
    for f, i, hp in re.findall(r"^f\s*(\d+) b(\d) esp=.*hp=\s*(\d+)/", log, re.M):
        por_frame.setdefault(int(f), {})[int(i)] = int(hp)
    return [(f, d[0], d[1]) for f, d in sorted(por_frame.items()) if 0 in d and 1 in d]


def lutar(rom: Path, mapa: Path, estado: Path, outdir: Path, frames: int = 3200,
          shots: int = 40, offsets: Path | None = None) -> str:
    """`offsets` é obrigatório na prática desde a E6: `ability` virou u16 e o
    passo de `BattlePokemon` mudou — sem o JSON o nav lê o HP no lugar errado."""
    """Entra na grama (sobe/desce), depois martela A para lutar."""
    passos = []
    for i in range(14):
        ini = 50 + i * 220
        passos.append(f"{ini}-{ini + 150}:{'UP' if i % 2 == 0 else 'DOWN'}")
    saida = outdir / "batalha.bin"
    log = nav(rom=rom, map=mapa, in_=estado, out=saida, outdir=outdir,
              frames=3400, script=";".join(passos), parar_quando="gBattleTypeFlags",
              offsets=offsets)
    if "condicao gBattleTypeFlags" not in log:
        return "SEM_BATALHA\n" + log[-3000:]
    pulsos = ",".join(f"{f}:A:6" for f in range(200, frames, 40))
    log += nav(rom=rom, map=mapa, in_=saida, outdir=outdir, frames=frames,
               pulsos=pulsos, batalha=100, every=shots, offsets=offsets)
    return log


def preparar_time(rom: Path, mapa: Path, offset_json: Path, golpe: int,
                  destino: Path) -> bool:
    """Grava o time do jogador (golpe no slot 1) no estado da Rota 1."""
    if not ESTADO.exists():
        raise SystemExit(f"não achei {ESTADO}; rode prova_golpes_e4.py --preparar-estado")
    r = rodar([sys.executable, str(AQUI / "savestate.py"), "--map", str(mapa),
               "--offsets", str(offset_json), "--rom", str(rom),
               "--in", str(ESTADO), "--out", str(destino), "pokemon",
               "--slot", "0", "--species", str(ESPECIE_JOGADOR),
               "--level", str(NIVEL_JOGADOR),
               "--moves", str(golpe), str(MOVE_TACKLE), str(MOVE_TACKLE), str(MOVE_TACKLE)])
    return destino.exists()


def batalha(pf: Path, golpe: int, especie: int, temporario: Path,
            offsets: Path, *, sem_habilidade: bool = False) -> dict:
    """Roda uma batalha e devolve {inimigo_final, inimigo_inicial, leituras, log}."""
    rom_original = pf / "pokefirered_modern.gba"
    mapa = pf / "pokefirered_modern.map"
    temporario.mkdir(parents=True, exist_ok=True)
    (temporario / "shots").mkdir(exist_ok=True)
    simbolos = ler_simbolos(mapa)
    global ABILITY_EARTH_EATER
    if not ABILITY_EARTH_EATER:
        texto = (pf / "include/constants/abilities.h").read_text(encoding="utf-8")
        m = re.search(r"^#define ABILITY_EARTH_EATER (\d+)$", texto, re.M)
        if not m:
            raise SystemExit("ABILITY_EARTH_EATER não está em abilities.h")
        ABILITY_EARTH_EATER = int(m.group(1))
        if ABILITY_EARTH_EATER > 255 and "u16 abilities[2]" not in \
                (pf / "include/pokemon.h").read_text(errors="replace"):
            raise SystemExit(f"ABILITY_EARTH_EATER = {ABILITY_EARTH_EATER} não cabe no u8 "
                             f"de abilities[2] (rode apply_e6_port.py)")
    rom = rom_com_selvagem(rom_original, temporario / "rom_prova.gba", especie,
                           NIVEL_SELVAGEM, simbolos, sem_habilidade=sem_habilidade,
                           poke=pf)
    estado = temporario / "jogador.bin"
    if not preparar_time(rom, mapa, offsets, golpe, estado):
        raise SystemExit("savestate.py pokemon falhou")
    log = lutar(rom, mapa, estado, temporario / "shots", offsets=offsets)
    hps = ler_hp(log)
    if not hps:
        return dict(ok=False, motivo="sem leitura de HP (batalha não abriu?)", log=log, hps=[])
    return dict(ok=True, hps=hps, inicial=hps[0], final=hps[-1], log=log)


# --------------------------------------------------------------------------
# self-test (sem ROM)
# --------------------------------------------------------------------------
def self_test() -> int:
    ok = 0
    rom = bytearray(0x1000)
    base = 0x200
    # duas entradas de 20 B: uma de outro mapa e a da Rota 1
    rom[base + 20] = GRUPO_ROTA1
    rom[base + 21] = MAPA_ROTA1
    struct.pack_into("<I", rom, base + 24, 0x08000500)          # landMonsInfo
    rom[0x500] = TAXA_ROTA1
    struct.pack_into("<I", rom, 0x504, 0x08000600)              # array de 12 slots
    for i in range(12):
        struct.pack_into("<BBH", rom, 0x600 + 4 * i, 2 + i % 4, 2 + i % 4, SPECIES_RATTATA)
    oa, oi, passo = achar_encontro(bytes(rom), {"gWildMonHeaders": 0x08000000 + base})
    assert (oa, oi, passo) == (0x600, 0x500, 20), (hex(oa), hex(oi), passo)
    ok += 1

    # patch escreve min/max/species nos 12 slots (o jogo sorteia entre eles)
    rom2 = bytearray(rom)
    for i in range(12):
        struct.pack_into("<BBH", rom2, oa + 4 * i, 30, 30, SPECIES_ORTHWORM)
    assert all(struct.unpack_from("<BBH", rom2, oa + 4 * i) == (30, 30, SPECIES_ORTHWORM)
               for i in range(12))
    ok += 1

    # taxa errada -> não aceita (não escreve em endereço chutado)
    rom3 = bytearray(rom)
    rom3[0x500] = 99
    try:
        achar_encontro(bytes(rom3), {"gWildMonHeaders": 0x08000000 + base})
        falhou = True
    except SystemExit:
        falhou = False
    assert not falhou, "aceitou uma tabela com encounterRate errado"
    ok += 1

    # leitura de HP do log do nav.py
    log = ("f  200 b0 esp= 700 hp= 202/202\nf  200 b1 esp= 968 hp=  90/90\n"
           "f  300 b0 esp= 700 hp= 202/202\nf  300 b1 esp= 968 hp=  67/90\n")
    hps = ler_hp(log)
    assert hps == [(200, 202, 90), (300, 202, 67)], hps
    ok += 1
    print(f"self-test ok: {ok} casos (achar encontro, patch do slot, recusa de endereço "
          f"errado, leitura de HP)")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="E5: Earth Eater em batalha")
    ap.add_argument("--pokefirered", type=Path, default=PADRAO_PF)
    ap.add_argument("--prova", action="store_true", help="roda as batalhas de controle e de teste")
    ap.add_argument("--shots", type=Path, default=None, help="copia as capturas para cá")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.prova:
        ap.error("use --prova ou --self-test")

    pf = a.pokefirered
    temporario = Path(tempfile.mkdtemp(prefix="e5prova_"))
    if not (temporario / "offsets.json").exists():
        rodar([sys.executable, str(AQUI / "offsets.py"), "--pokefirered", str(pf),
               "--gravar", str(temporario / "offsets.json")])

    print("1/3 controle: Orthworm selvagem x TACKLE (Normal) — o HP tem de cair")
    controle = batalha(pf, MOVE_TACKLE, SPECIES_ORTHWORM, temporario / "controle",
                       temporario / "offsets.json")
    print("2/3 Earth Eater: Orthworm selvagem x BULLDOZE (Terra) — o HP NÃO pode cair")
    teste = batalha(pf, MOVE_BULLDOZE, SPECIES_ORTHWORM, temporario / "teste",
                    temporario / "offsets.json")
    print("3/3 prova negativa: o MESMO Orthworm sem habilidade x BULLDOZE — tem de cair")
    negativo = batalha(pf, MOVE_BULLDOZE, SPECIES_ORTHWORM, temporario / "negativo",
                       temporario / "offsets.json", sem_habilidade=True)

    for nome, r in (("controle", controle), ("earth eter", teste), ("sem habilidade", negativo)):
        if r.get("ok"):
            _, j0, i0 = r["inicial"]
            _, jf, inf = r["final"]
            print(f"  {nome}: inimigo {i0} -> {inf} HP | jogador {j0} -> {jf} "
                  f"({len(r['hps'])} leituras)")
        else:
            print(f"  {nome}: {r['motivo']}")

    if a.shots:
        a.shots.mkdir(parents=True, exist_ok=True)
        for pasta in ("controle", "teste", "negativo"):
            origem = temporario / pasta / "shots"
            if origem.is_dir():
                for png in sorted(origem.glob("*.png")):
                    shutil.copy(png, a.shots / f"{pasta}_{png.name}")

    if not (controle.get("ok") and teste.get("ok") and negativo.get("ok")):
        print("REPROVADO: uma das batalhas não abriu")
        return 1
    caiu_controle = controle["final"][2] < controle["inicial"][2]
    manteve = teste["final"][2] >= teste["inicial"][2]
    caiu_negativo = negativo["final"][2] < negativo["inicial"][2]
    if caiu_controle and manteve and caiu_negativo:
        print("ok: Buldoze não afeta o Orthworm com Earth Eater, fere o mesmo Orthworm "
              "sem a habilidade, e o Tackle do controle fere")
        return 0
    if not caiu_negativo:
        print("REPROVADO: sem a habilidade o Buldoze também não feriu — a imunidade "
              "não é da habilidade (tipo/tabela?)")
    if not manteve:
        print(f"REPROVADO: Buldoze feriu o Orthworm ({teste['inicial'][2]} -> "
              f"{teste['final'][2]}) — Earth Eater não está sendo usado")
    if not caiu_controle:
        print("REPROVADO: o controle (Tackle) não feriu — a batalha não provou nada")
    if not manteve:
        print(f"REPROVADO: Buldoze feriu o Orthworm ({teste['inicial'][2]} -> "
              f"{teste['final'][2]}) — Earth Eater não está sendo usado")
    return 1


if __name__ == "__main__":
    sys.exit(main())
