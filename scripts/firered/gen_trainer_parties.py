#!/usr/bin/env python3
"""Mistura espécies Gen 4-9 nos times de treinadores do FireRed (E7, onda 2b).

Por que
-------
Depois da onda 1 as espécies novas só apareciam na grama. Treinadores
continuavam 100% Gen 1-3. Este gerador troca parte dos times por espécies
novas SEM mudar a dificuldade nem a identidade dos treinadores.

Política (determinística, mesma ideia da mistura de encontros)
--------------------------------------------------------------
* Só times com golpes padrão (`*DefaultMoves`) são tocados: o jogo calcula
  os golpes pelo learnset, então a troca de espécie é segura. Times com
  golpes escolhidos à mão (`*CustomMoves` — líderes de ginásio, Elite 4,
  rival) ficam **intactos**.
* Slot 0 nunca muda (a "cara" do treinador fica).
* Time com 2+ Pokémon: o ÚLTIMO slot vira uma espécie nova.
* Time de 1 Pokémon: troca só quando o hash do nome do time é par
  (metade dos treinadores de 1 Pokémon muda, metade não).
* A espécie nova é a de BST mais próximo entre as que têm o mesmo tipo
  primário do original (fallback: qualquer tipo em comum; fallback final:
  BST mais próximo geral). Espécies com BST >= 570 ficam de fora (nada de
  pseudo-lendário em bug catcher). Nível, IV e item NÃO mudam.
* Desempate por hash(nome do time + slot) → o resultado é estável entre
  execuções e máquinas.

Rotulagem: a escolha de "qual espécie parece certa" é HIPÓTESE (critério de
tipo + BST). Que o jogo aceita a espécie e gera golpes do learnset é
CONFIRMADO pelas provas em jogo da E4/E7.

Uso
---
    python3 gen_trainer_parties.py --self-test
    python3 gen_trainer_parties.py --pokefirered /tmp/pokefirered           # dry-run
    python3 gen_trainer_parties.py --pokefirered /tmp/pokefirered --write
    python3 gen_trainer_parties.py --pokefirered /tmp/pokefirered --check
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

REL_PARTIES = "src/data/trainer_parties.h"
REL_INFO_VANILLA = "src/data/pokemon/species_info.h"
REL_INFO_NOVAS = "src/data/pokemon/species_info_gen4_9.h"
REL_SPECIES_H = "include/constants/species.h"

MARCA = "// GERADO(e7-treinadores):"   # vai no fim da linha .species trocada
BST_TETO = 570                          # nada de pseudo-lendário em treinador comum
PRIMEIRA_NOVA = 387


# ------------------------------------------------------------------ leitura
def ler_numeros_especies(texto: str) -> dict[str, int]:
    """`#define SPECIES_X N` -> {"X": N}."""
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"^#define SPECIES_(\w+) (\d+)$", texto, re.M)}


def ler_info_especies(texto: str) -> dict[str, dict]:
    """De species_info*.h: nome -> {tipos: (t1, t2), bst: int}."""
    saida: dict[str, dict] = {}
    blocos = re.split(r"\[SPECIES_(\w+)\]\s*=", texto)
    # blocos = [prefixo, NOME1, corpo1, NOME2, corpo2, ...]
    for nome, corpo in zip(blocos[1::2], blocos[2::2]):
        tipos = re.search(r"\.types\s*=\s*\{\s*TYPE_(\w+)\s*,\s*TYPE_(\w+)\s*\}", corpo)
        stats = re.findall(
            r"\.base(?:HP|Attack|Defense|Speed|SpAttack|SpDefense)\s*=\s*(\d+)", corpo)
        if not tipos or len(stats) < 6:
            continue
        saida[nome] = {"tipos": (tipos.group(1), tipos.group(2)),
                       "bst": sum(int(s) for s in stats[:6])}
    return saida


RE_PARTY = re.compile(
    r"static const struct TrainerMon(\w+) sParty_(\w+)\[\] = \{(.*?)\};",
    re.S)
RE_SPECIES_LINHA = re.compile(r"(\.species\s*=\s*SPECIES_)(\w+)(\s*,)")


def ler_times(texto: str) -> list[dict]:
    """Todos os sParty_*: nome, tipo do struct, corpo e espécies por slot."""
    times = []
    for m in RE_PARTY.finditer(texto):
        kind, nome, corpo = m.group(1), m.group(2), m.group(3)
        if "DUMMY" in corpo:            # placeholders de classes RS não usadas
            continue
        especies = [x.group(2) for x in RE_SPECIES_LINHA.finditer(corpo)]
        if not especies:
            continue
        times.append({"kind": kind, "nome": nome, "corpo": corpo,
                      "especies": especies, "span": m.span(3)})
    return times


# ------------------------------------------------------------------ escolha
def _hash(txt: str) -> int:
    return int.from_bytes(hashlib.sha256(txt.encode()).digest()[:4], "little")


def escolher_substituta(original: str, slot_chave: str,
                        info: dict[str, dict],
                        novas: list[str]) -> str | None:
    """Espécie nova de tipo parecido e BST mais próximo. Determinística."""
    o = info.get(original)
    if o is None:
        return None
    t1 = o["tipos"][0]
    candidatas = [n for n in novas if info[n]["tipos"][0] == t1]
    if not candidatas:
        candidatas = [n for n in novas if t1 in info[n]["tipos"]]
    if not candidatas:
        candidatas = list(novas)
    if not candidatas:
        return None
    h = _hash(slot_chave)
    # BST mais próximo; empate decidido pelo hash (estável)
    return min(candidatas,
               key=lambda n: (abs(info[n]["bst"] - o["bst"]), _hash(n + slot_chave)))


def planejar(times: list[dict], info: dict[str, dict],
             numeros: dict[str, int]) -> list[tuple[str, int, str, str]]:
    """[(nome_time, slot, especie_antiga, especie_nova), ...]"""
    novas = sorted(n for n, d in info.items()
                   if numeros.get(n, 0) >= PRIMEIRA_NOVA and d["bst"] < BST_TETO)
    plano = []
    for t in times:
        if "DefaultMoves" not in t["kind"]:
            continue                     # golpes à mão: não mexe
        n = len(t["especies"])
        if n >= 2:
            slot = n - 1
        elif _hash(t["nome"]) % 2 == 0:
            slot = 0                     # time de 1: metade muda (hash par)
        else:
            continue
        antiga = t["especies"][slot]
        nova = escolher_substituta(antiga, f"{t['nome']}#{slot}", info, novas)
        if nova is None or nova == antiga:
            continue
        plano.append((t["nome"], slot, antiga, nova))
    return plano


# ------------------------------------------------------------------ escrita
def aplicar(texto: str, plano: list[tuple[str, int, str, str]]) -> str:
    por_time: dict[str, dict[int, tuple[str, str]]] = {}
    for nome, slot, antiga, nova in plano:
        por_time.setdefault(nome, {})[slot] = (antiga, nova)

    def troca_corpo(m: re.Match) -> str:
        kind, nome, corpo = m.group(1), m.group(2), m.group(3)
        trocas = por_time.get(nome)
        if not trocas:
            return m.group(0)
        i = -1

        def troca_linha(lm: re.Match) -> str:
            nonlocal i
            i += 1
            if i in trocas:
                antiga, nova = trocas[i]
                return f"{lm.group(1)}{nova}{lm.group(3)} {MARCA} era SPECIES_{antiga}"
            return lm.group(0)

        corpo_novo = RE_SPECIES_LINHA.sub(troca_linha, corpo)
        return f"static const struct TrainerMon{kind} sParty_{nome}[] = {{{corpo_novo}}};"

    return RE_PARTY.sub(troca_corpo, texto)


def conferir(texto: str, plano: list[tuple[str, int, str, str]]) -> list[str]:
    """O arquivo escrito contém exatamente as trocas do plano?"""
    falhas = []
    times = {t["nome"]: t for t in ler_times(texto)}
    for nome, slot, antiga, nova in plano:
        t = times.get(nome)
        if t is None:
            falhas.append(f"{nome}: time sumiu")
        elif slot >= len(t["especies"]) or t["especies"][slot] != nova:
            tem = t["especies"][slot] if slot < len(t["especies"]) else "?"
            falhas.append(f"{nome}[{slot}]: esperava {nova}, tem {tem}")
    # nenhum time CustomMoves pode ter a marca
    for m in RE_PARTY.finditer(texto):
        if "CustomMoves" in m.group(1) and MARCA in m.group(3):
            falhas.append(f"{m.group(2)}: time de golpes à mão foi tocado")
    return falhas


# ------------------------------------------------------------------ fluxo
def rodar(poke: Path, write: bool, check: bool) -> int:
    arq = poke / REL_PARTIES
    texto = arq.read_text()
    info = ler_info_especies((poke / REL_INFO_VANILLA).read_text())
    info.update(ler_info_especies((poke / REL_INFO_NOVAS).read_text()))
    numeros = ler_numeros_especies((poke / REL_SPECIES_H).read_text())

    # Idempotência: com as marcas no arquivo, replanejar usaria as espécies já
    # trocadas como "originais" e mudaria tudo de novo. Então: arquivo marcado
    # nunca é reescrito — só conferido.
    if MARCA in texto:
        trocadas = len(re.findall(re.escape(MARCA), texto))
        print(f"já aplicado: {trocadas} slots marcados {MARCA!r}")
        if check:
            novas_no_arq = 0
            for t in ler_times(texto):
                novas_no_arq += sum(1 for e in t["especies"]
                                    if numeros.get(e, 0) >= PRIMEIRA_NOVA)
            if novas_no_arq != trocadas:
                print(f"FALHA: {trocadas} marcas mas {novas_no_arq} espécies novas")
                return 1
            print("trainer_parties ok")
        return 0

    plano = planejar(ler_times(texto), info, numeros)
    por_gen = {}
    for _, _, _, nova in plano:
        n = numeros[nova]
        g = (4 if n < 495 else 5 if n < 650 else 6 if n < 722 else
             7 if n < 810 else 8 if n < 906 else 9)
        por_gen[g] = por_gen.get(g, 0) + 1
    print(f"{len(plano)} slots de treinador viram espécie nova "
          f"(de {sum(len(t['especies']) for t in ler_times(texto))} slots)")
    print("por geração: " + ", ".join(f"Gen {g}: {q}" for g, q in sorted(por_gen.items())))
    for nome in ("BugCatcherRick", "BugCatcherDoug", "BugCatcherSammy"):
        itens = [p for p in plano if p[0] == nome]
        for _, slot, antiga, nova in itens:
            print(f"  prova: sParty_{nome}[{slot}] {antiga} -> {nova} (#{numeros[nova]})")

    if check:
        print("nada aplicado ainda; rode --write antes do --check")
        return 1
    if not write:
        print("dry-run: nada escrito (use --write)")
        return 0

    novo = aplicar(texto, plano)
    falhas = conferir(novo, plano)
    if falhas:
        print("FALHA na conferência pós-escrita:")
        for f in falhas[:10]:
            print("  " + f)
        return 1
    arq.write_text(novo)
    print(f"escrito: {arq}")
    return 0


# --------------------------------------------------------------- self-test
TESTE_PARTIES = """
static const struct TrainerMonNoItemDefaultMoves sParty_Um[] = {
    {
        .iv = 0,
        .lvl = 6,
        .species = SPECIES_WEEDLE,
    },
    {
        .iv = 0,
        .lvl = 6,
        .species = SPECIES_CATERPIE,
    },
};

static const struct TrainerMonNoItemDefaultMoves sParty_Solo[] = {
    {
        .iv = 0,
        .lvl = 9,
        .species = SPECIES_WEEDLE,
    },
};

static const struct TrainerMonItemCustomMoves sParty_Chefe[] = {
    {
        .iv = 255,
        .lvl = 43,
        .species = SPECIES_PIDGEOT,
        .heldItem = ITEM_NONE,
        .moves = {MOVE_TACKLE, MOVE_TACKLE, MOVE_TACKLE, MOVE_TACKLE},
    },
};

static const struct TrainerMonNoItemDefaultMoves sParty_Falso[] = {DUMMY_TRAINER_MON};
"""

TESTE_INFO = """
const struct SpeciesInfo gSpeciesInfo[] = {
    [SPECIES_WEEDLE] = {
        .baseHP = 40, .baseAttack = 35, .baseDefense = 30,
        .baseSpeed = 50, .baseSpAttack = 20, .baseSpDefense = 20,
        .types = {TYPE_BUG, TYPE_POISON},
    },
    [SPECIES_CATERPIE] = {
        .baseHP = 45, .baseAttack = 30, .baseDefense = 35,
        .baseSpeed = 45, .baseSpAttack = 20, .baseSpDefense = 20,
        .types = {TYPE_BUG, TYPE_BUG},
    },
    [SPECIES_PIDGEOT] = {
        .baseHP = 83, .baseAttack = 80, .baseDefense = 75,
        .baseSpeed = 101, .baseSpAttack = 70, .baseSpDefense = 70,
        .types = {TYPE_NORMAL, TYPE_FLYING},
    },
    [SPECIES_TAROUNTULA] = {
        .baseHP = 35, .baseAttack = 41, .baseDefense = 45,
        .baseSpeed = 20, .baseSpAttack = 29, .baseSpDefense = 40,
        .types = {TYPE_BUG, TYPE_BUG},
    },
    [SPECIES_MIRAIDON] = {
        .baseHP = 100, .baseAttack = 85, .baseDefense = 100,
        .baseSpeed = 135, .baseSpAttack = 135, .baseSpDefense = 115,
        .types = {TYPE_BUG, TYPE_BUG},
    },
};
"""

TESTE_NUMEROS = {"WEEDLE": 13, "CATERPIE": 10, "PIDGEOT": 18,
                 "TAROUNTULA": 917, "MIRAIDON": 1008}


def self_test() -> int:
    ok = 0

    info = ler_info_especies(TESTE_INFO)
    assert info["WEEDLE"]["bst"] == 195 and info["WEEDLE"]["tipos"] == ("BUG", "POISON")
    ok += 1  # 1. parser do species_info

    times = ler_times(TESTE_PARTIES)
    assert [t["nome"] for t in times] == ["Um", "Solo", "Chefe"], times
    assert times[0]["especies"] == ["WEEDLE", "CATERPIE"]
    ok += 1  # 2. parser dos times (DUMMY fora)

    plano = planejar(times, info, TESTE_NUMEROS)
    nomes = {p[0] for p in plano}
    assert "Chefe" not in nomes, "CustomMoves não pode entrar no plano"
    assert ("Um", 1, "CATERPIE", "TAROUNTULA") in plano, plano
    ok += 1  # 3. política: último slot, tipo primário igual, BST próximo

    for p in plano:
        assert p[3] != "MIRAIDON", "BST 670 tinha de ficar fora"
    ok += 1  # 4. teto de BST

    assert planejar(times, info, TESTE_NUMEROS) == plano
    ok += 1  # 5. determinismo

    novo = aplicar(TESTE_PARTIES, plano)
    assert conferir(novo, plano) == []
    assert "era SPECIES_CATERPIE" in novo
    assert novo.count(MARCA) == len(plano)
    ok += 1  # 6. aplicar + conferir

    quebrado = novo.replace("SPECIES_TAROUNTULA", "SPECIES_CATERPIE")
    assert conferir(quebrado, plano) != []
    ok += 1  # 7. conferir pega regressão

    print(f"self-test ok: {ok} casos (parsers, política, teto de BST, "
          f"determinismo, aplicar/conferir)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pokefirered", type=Path)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.pokefirered:
        ap.error("--pokefirered ou --self-test")
    return rodar(a.pokefirered, a.write, a.check)


if __name__ == "__main__":
    sys.exit(main())
