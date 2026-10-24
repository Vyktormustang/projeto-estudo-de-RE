#!/usr/bin/env python3
"""Mistura as espécies das Gen 4-9 nas tabelas de encontro selvagem de Kanto.

Sem esta etapa o jogo tem 1025 espécies, sprites e mecânicas, mas **nenhuma
espécie nova aparece jogando** — as tabelas de encontro do FireRed são as
originais (só Gen 1). É o item de aceite da E7: um Pokémon de Gen 9 selvagem na
Rota 1, capturável.

Nota de escopo: o pokefirered **já tem** as Gen 1-3 (IDs 1-386, dados da
vanilla). O que este projeto acrescentou são as Gen 4-9 (IDs 387-1025), e é só
esse conjunto que entra na mistura — mexer nas Gen 1-3 não é necessário.

## Regra (determinística e reprodutível)

1. Cada tabela (`land_mons`/`water_mons`/`rock_smash_mons`/`fishing_mons`) é
   tratada separadamente, e **as duas versões** (FireRed e LeafGreen) recebem a
   mesma mistura — a semente é `mapa|tabela|slot`, não o `base_label`. Motivo:
   `MAP_ROUTE1` aparece duas vezes no JSON e escolher "a última" alteraria só a
   LeafGreen (erro já cometido na tentativa anterior deste projeto).
2. O **slot 0 nunca muda**: é o mais comum (20% na grama) e é o que dá
   identidade à rota (Pidgey/Rattata continuam sendo o normal da Rota 1).
3. A partir do slot 1, trocam-se **no máximo 2 slots na grama e 1 nas outras
   tabelas**, e só enquanto a soma de probabilidade não passar de **40%** da
   tabela. Na grama: 20% + 10% = 30%; na água: 30%; rock smash: 40%; pesca: 40%.
   Trocar mais que isso descaracteriza a rota sem necessidade (a água e a pesca
   têm 5 e 10 slots, que na prática são duas varas).
4. O substituto é sorteado por `sha256(mapa|tabela|slot)` entre as espécies da
   **nossa lista** que:
     - são **forma base** (o `natDexNum` do RHH tem o mesmo nome da espécie, o
       que exclui Mega/Alolan/Hisuian/Paldeano e qualquer outra forma);
     - não são **míticas**;
      - têm **BST a ±120** do Pokémon que sai — barra lendário em rota inicial e
       mantém a curva de dificuldade (a janela abre para ±180 e depois para
       qualquer valor só se não houver candidato);
     - têm o **mesmo tipo primário**, se houver candidato (senão, qualquer um).
5. Os níveis do slot são preservados.
6. **Rota 1**: o primeiro slot trocado da grama é obrigatoriamente de **Gen 9**.
   Não é capricho: é o critério de aceite e não pode depender do sorteio.

## Uso

    python3 gen_wild_encounters.py --self-test
    python3 gen_wild_encounters.py --pokefirered /tmp/pokefirered --reference /tmp/fre --write
    python3 gen_wild_encounters.py --pokefirered /tmp/pokefirered --reference /tmp/fre --check
    python3 gen_wild_encounters.py --pokefirered /tmp/pokefirered --reference /tmp/fre --relatorio
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import gen_species_data as gen  # noqa: E402  (mesmo leitor de blocos da E2)

ARQUIVO = "src/data/wild_encounters.json"
ALVO_PCT = 40             # % máximo da tabela que pode virar Gen 4-9
# Quantos slots cada tipo de tabela pode trocar. Na grama 2 slots = 20% + 10%
# (30% da tabela); nas outras, 1 slot já entrega 30-40%. A água e a pesca têm
# 5 e 10 slots (dois grupos de vara), então trocar 2 estragaria metade delas.
MAX_POR_CAMPO = {"land_mons": 2, "water_mons": 1,
                 "rock_smash_mons": 1, "fishing_mons": 1}
MAX_SLOTS = 2             # teto global (usado nos testes da função pura)
BST_TOLERANCIA = 120
PRIMEIRA_GEN_NOVA = 387   # IDs abaixo disto já são vanilla (Gen 1-3)
GEN_9_INICIO = 906        # #0906 = Nacli; daí para cima é Gen 9

CAMPOS = ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons")

# O json.dumps do Python reproduz o arquivo do pret byte a byte (conferido em
# `aplicar`): indent=2 e newline no fim. Se isso deixar de valer, o gravador
# recusa-se a escrever em vez de reescrever 700 KB de diff.
JSON_KW = dict(indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# leitura dos dados
# --------------------------------------------------------------------------- #
def especies_nossas(pf: Path) -> dict[str, int]:
    texto = (pf / "include/constants/species.h").read_text(encoding="utf-8")
    return {n: int(v) for n, v in
            re.findall(r"^#define (SPECIES_\w+) (\d+)$", texto, re.M)}


RE_NATDEX = re.compile(r"NATIONAL_DEX_([A-Z0-9_]+)$")
RE_TIPOS = re.compile(r"MON_TYPES\(([^)]*)\)")
CAMPOS_BST = ("baseHP", "baseAttack", "baseDefense", "baseSpeed",
              "baseSpAttack", "baseSpDefense")


def _tipos(campos: dict[str, str]) -> list[str]:
    m = RE_TIPOS.search(campos.get("types", ""))
    if not m:
        return []
    return [t.strip().replace("TYPE_", "") for t in m.group(1).split(",") if t.strip()]


def _bst(campos: dict[str, str]) -> int:
    total = 0
    for c in CAMPOS_BST:
        v = campos.get(c, "").strip()
        if v.isdigit():
            total += int(v)
    return total


def catalogo(pf: Path, ref: Path) -> dict[str, dict]:
    """Dados de cada espécie da nossa lista, lidos do RHH.

    Devolve `{nome_sem_SPECIES: {id, tipos, bst, mitica, base}}`. O número da
    dex nacional **é o ID** (decisão da E1: `SPECIES_X == #X`). Espécie sem
    bloco no RHH é omitida e contada pelo chamador.
    """
    dados = gen.carregar_referencia(ref)
    saida: dict[str, dict] = {}
    for nome, ident in especies_nossas(pf).items():
        curto = nome[len("SPECIES_"):]
        bloco = gen.bloco_da_especie(curto, dados)
        if bloco is None:
            continue
        m = RE_NATDEX.search(bloco.get("natDexNum", "").strip())
        saida[curto] = {
            "id": ident,
            "tipos": _tipos(bloco),
            "bst": _bst(bloco),
            "mitica": bloco.get("isMythical", "").strip() == "TRUE",
            # forma base: o NATDEX do bloco tem o mesmo nome da espécie. É o que
            # exclui MIMIKYU_DISGUISED, CHARIZARD_MEGA_X, OGERPON_WELLSPRING...
            "base": bool(m) and m.group(1) == curto,
        }
    return saida


def pool_de_candidatos(cat: dict[str, dict]) -> list[dict]:
    """Formas base e não míticas das Gen 4-9 — em ordem de ID."""
    itens = [{"nome": nome, **info} for nome, info in cat.items()
             if info["id"] >= PRIMEIRA_GEN_NOVA and info["base"] and not info["mitica"]]
    itens.sort(key=lambda c: c["id"])
    return itens


# --------------------------------------------------------------------------- #
# a mistura
# --------------------------------------------------------------------------- #
def pesos(grupo: dict, campo: str, n: int) -> list[int]:
    for f in grupo["fields"]:
        if f["type"] == campo:
            r = f["encounter_rates"]
            if len(r) == n:
                return list(r)
    return [100 // max(n, 1)] * n


def slots_a_trocar(pesos_tabela: list[int], alvo_pct: int = ALVO_PCT,
                   max_slots: int = MAX_SLOTS) -> list[int]:
    """Índices a trocar: do 1 em diante, no máximo `max_slots`, sem passar do alvo.

    Guloso: um slot que estouraria o alvo é pulado, mas continua valendo tentar
    os seguintes (na água, 30+5+4 já passa de 40; troca-se 30 e 5).
    """
    total = sum(pesos_tabela)
    if total <= 0:
        return []
    limite = total * alvo_pct // 100
    escolhidos: list[int] = []
    soma = 0
    for i in range(1, len(pesos_tabela)):
        if len(escolhidos) >= max_slots:
            break
        if soma + pesos_tabela[i] <= limite:
            escolhidos.append(i)
            soma += pesos_tabela[i]
    return escolhidos


def _semente(mapa: str, campo: str, slot: int) -> int:
    h = hashlib.sha256(f"{mapa}|{campo}|{slot}".encode()).hexdigest()
    return int(h[:16], 16)


def escolher_substituto(mapa: str, campo: str, slot: int, original: dict,
                        candidatos: list[dict], ja_usados: set[str],
                        forcar_gen9: bool = False) -> dict:
    semente = _semente(mapa, campo, slot)
    bst = original.get("bst") or 0
    tipos = original.get("tipos") or []
    pool = candidatos
    if forcar_gen9:
        pool = [c for c in pool if c["id"] >= GEN_9_INICIO]
        if not pool:
            raise SystemExit("nao ha especie de Gen 9 no pool — lista de especies mudou?")
    if bst:
        # a janela de BST abre até haver candidato: ±120 -> ±180 -> qualquer
        for tol in (BST_TOLERANCIA, 180, 10_000):
            janela = [c for c in pool if not c["bst"] or abs(c["bst"] - bst) <= tol]
            if janela:
                pool = janela
                break
    if tipos:
        mesmo_tipo = [c for c in pool if c["tipos"] and c["tipos"][0] == tipos[0]]
        if mesmo_tipo:
            pool = mesmo_tipo
    # evita repetir dentro da mesma tabela (se houver como)
    livres = [c for c in pool if c["nome"] not in ja_usados]
    return (livres or pool)[semente % len(livres or pool)]


def misturar(doc: dict, cat: dict[str, dict], alvo_pct: int = ALVO_PCT) -> dict:
    """Aplica a mistura no documento JSON (in place) e devolve as estatísticas."""
    grupo = doc["wild_encounter_groups"][0]
    candidatos = pool_de_candidatos(cat)
    if not candidatos:
        raise SystemExit("pool de candidatos vazio")
    st = {"trocados": 0, "ja_misturados": 0, "tabelas": 0, "por_gen": {}, "rota1": [],
          "candidatos": len(candidatos),
          "com_bst": sum(1 for c in candidatos if c["bst"])}
    for entrada in grupo["encounters"]:
        mapa = entrada["map"]
        for campo in CAMPOS:
            tabela = entrada.get(campo)
            if not tabela or not tabela.get("mons"):
                continue
            mons = tabela["mons"]
            st["tabelas"] += 1
            p = pesos(grupo, campo, len(mons))
            usados = {m["species"][len("SPECIES_"):] for m in mons}
            for n, i in enumerate(slots_a_trocar(p, alvo_pct, MAX_POR_CAMPO[campo])):
                atual = mons[i]["species"][len("SPECIES_"):]
                # Idempotência: slot que já tem espécie das Gen 4-9 é deixado
                # como está. Sem isso, rodar o setup duas vezes re-sortearia em
                # cima do resultado anterior (a semente depende do original) e o
                # arquivo nunca estabilizaria.
                if atual in cat and cat[atual]["id"] >= PRIMEIRA_GEN_NOVA:
                    st["ja_misturados"] += 1
                    if mapa == "MAP_ROUTE1" and campo == "land_mons":
                        st["rota1"].append(atual)
                    continue
                original = cat.get(atual, {})
                forcar = mapa == "MAP_ROUTE1" and campo == "land_mons" and n == 0
                novo = escolher_substituto(mapa, campo, i, original, candidatos,
                                           usados, forcar_gen9=forcar)
                # o nível do slot é preservado; só a espécie muda
                mons[i]["species"] = "SPECIES_" + novo["nome"]
                usados.add(novo["nome"])
                st["trocados"] += 1
                g = geracao(novo["id"])
                st["por_gen"][g] = st["por_gen"].get(g, 0) + 1
                if mapa == "MAP_ROUTE1" and campo == "land_mons":
                    st["rota1"].append(novo["nome"])
    st["por_gen"] = dict(sorted(st["por_gen"].items()))
    return st


def geracao(numero: int) -> int:
    for g, fim in enumerate((151, 251, 386, 493, 649, 721, 809, 905, 1025), start=1):
        if numero <= fim:
            return g
    return 0


# --------------------------------------------------------------------------- #
# aplicar / verificar
# --------------------------------------------------------------------------- #
def _texto(doc: dict) -> str:
    return json.dumps(doc, **JSON_KW) + "\n"


def aplicar(pf: Path, ref: Path) -> dict:
    p = pf / ARQUIVO
    texto_original = p.read_text(encoding="utf-8")
    doc = json.loads(texto_original)
    if _texto(doc) != texto_original:
        raise SystemExit(
            "o JSON nao volta identico com json.dumps(indent=2): a mistura "
            "reescreveria o arquivo inteiro. Nao gravar.")
    st = misturar(doc, catalogo(pf, ref))
    p.write_text(_texto(doc), encoding="utf-8")
    return st


def conferir_invariantes(doc: dict, cat: dict[str, dict], alvo_pct: int = ALVO_PCT) -> list[str]:
    """O que tem de valer em qualquer versão do arquivo misturado.

    Não dá para exigir igualdade byte a byte com "o que o gerador produziria":
    o sorteio depende da espécie original, e depois da primeira passada ela já
    não está mais lá. O que se exige é o **formato** da mistura:
      - slot 0 vanilla (a rota continua sendo a rota);
      - exatamente os slots previstos trocados, todos com espécie das Gen 4-9;
      - nenhum slot fora deles com espécie nova;
      - Rota 1 com Gen 9 no primeiro slot trocado.
    """
    grupo = doc["wild_encounter_groups"][0]
    erros: list[str] = []
    for entrada in grupo["encounters"]:
        mapa = entrada["map"]
        for campo in CAMPOS:
            tabela = entrada.get(campo)
            if not tabela or not tabela.get("mons"):
                continue
            mons = tabela["mons"]
            esperado = set(slots_a_trocar(pesos(grupo, campo, len(mons)), alvo_pct,
                                          MAX_POR_CAMPO[campo]))
            for i, m in enumerate(mons):
                nome = m["species"][len("SPECIES_"):]
                info = cat.get(nome)
                nova = bool(info) and info["id"] >= PRIMEIRA_GEN_NOVA
                if i in esperado and not nova:
                    erros.append(f"{mapa}/{campo}[{i}]: {nome} deveria ser Gen 4-9")
                if i not in esperado and nova:
                    erros.append(f"{mapa}/{campo}[{i}]: {nome} nao deveria ter sido trocado")
            if mapa == "MAP_ROUTE1" and campo == "land_mons" and esperado:
                i = min(esperado)
                nome = mons[i]["species"][len("SPECIES_"):]
                if not (nome in cat and cat[nome]["id"] >= GEN_9_INICIO):
                    erros.append(f"Rota 1: slot {i} deveria ser Gen 9, e' {nome}")
    return erros


def verificar(pf: Path, ref: Path) -> tuple[int, dict, list[str]]:
    p = pf / ARQUIVO
    doc = json.loads(p.read_text(encoding="utf-8"))
    cat = catalogo(pf, ref)
    erros = conferir_invariantes(doc, cat)
    st = misturar(doc, cat)       # só para o relatório (não grava)
    return (1 if erros else 0), st, erros


# --------------------------------------------------------------------------- #
# self-test
# --------------------------------------------------------------------------- #
GRUPO_TESTE = {
    "wild_encounter_groups": [{
        "label": "gWildMonHeaders",
        "for_maps": True,
        "fields": [
            {"type": "land_mons", "encounter_rates": [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1]},
            {"type": "water_mons", "encounter_rates": [60, 30, 5, 4, 1]},
            {"type": "rock_smash_mons", "encounter_rates": [60, 40]},
            {"type": "fishing_mons", "encounter_rates": [40, 40, 15, 4, 1, 40, 40, 15, 4, 1]},
        ],
        "encounters": [
            {"map": "MAP_ROUTE1", "base_label": "sRoute1_FireRed",
             "land_mons": {"encounter_rate": 21, "mons": [
                 {"min_level": 3, "max_level": 3, "species": "SPECIES_PIDGEY"}] * 12}},
            {"map": "MAP_ROUTE1", "base_label": "sRoute1_LeafGreen",
             "land_mons": {"encounter_rate": 21, "mons": [
                 {"min_level": 3, "max_level": 3, "species": "SPECIES_PIDGEY"}] * 12}},
            {"map": "MAP_ROUTE10", "base_label": "sRoute10_FireRed",
             "land_mons": {"encounter_rate": 21, "mons": [
                 {"min_level": 16, "max_level": 16, "species": "SPECIES_SPEAROW"}] * 12},
             "water_mons": {"encounter_rate": 2, "mons": [
                 {"min_level": 5, "max_level": 5, "species": "SPECIES_TENTACOOL"}] * 5},
             "rock_smash_mons": {"encounter_rate": 1, "mons": [
                 {"min_level": 10, "max_level": 10, "species": "SPECIES_GEODUDE"}] * 2},
             "fishing_mons": {"encounter_rate": 2, "mons": [
                 {"min_level": 5, "max_level": 5, "species": "SPECIES_MAGIKARP"}] * 10}},
        ],
    }]
}


def catalogo_teste() -> dict[str, dict]:
    """Catálogo sintético: Gen 1 (origem), Gen 4 (candidatos) e Gen 9.

    Os números são os reais da dex nacional — o corte de "espécie nova" é o
    ID 387 (Turtwig), então as Gen 2-3 (IDs 152-386) **não** entram no pool,
    mesmo tendo sido lançadas depois da Gen 1: a vanilla já as tem.
    """
    def e(i, tipos, bst, mitica=False, base=True):
        return {"id": i, "tipos": tipos, "bst": bst, "mitica": mitica, "base": base}
    return {
        "PIDGEY": e(16, ["NORMAL", "FLYING"], 251),
        "SPEAROW": e(21, ["NORMAL", "FLYING"], 262),
        "TENTACOOL": e(72, ["WATER", "POISON"], 335),
        "GEODUDE": e(74, ["ROCK", "GROUND"], 300),
        "MAGIKARP": e(129, ["WATER"], 200),
        "STARLY": e(396, ["NORMAL", "FLYING"], 245),
        "KRICKETOT": e(401, ["BUG"], 194),
        "SHELLOS": e(422, ["WATER"], 325),
        "FINNEON": e(456, ["WATER"], 330),
        "PHIONE": e(489, ["WATER"], 480, mitica=True),
        "NACLI": e(932, ["ROCK"], 330),
        "ORTHWORM": e(968, ["STEEL"], 480),
        "TATSUGIRI_CURLY": e(978, ["DRAGON", "WATER"], 475, base=False),
    }


def self_test() -> int:
    grupo = GRUPO_TESTE["wild_encounter_groups"][0]
    ok = 0

    # 1. ajuste guloso por tabela
    assert slots_a_trocar(pesos(grupo, "land_mons", 12),
                          max_slots=MAX_POR_CAMPO["land_mons"]) == [1, 2]
    for campo, n in (("water_mons", 5), ("rock_smash_mons", 2), ("fishing_mons", 10)):
        assert slots_a_trocar(pesos(grupo, campo, n),
                              max_slots=MAX_POR_CAMPO[campo]) == [1], campo
    ok += 1

    # 2. o alvo manda; o slot que estouraria é pulado, não aborta a tabela
    assert slots_a_trocar([40, 40, 20]) == [1]         # o segundo 40 passaria de 40%
    assert slots_a_trocar([50, 30, 20]) == [1]         # 30 entra, 30+50 não
    assert slots_a_trocar([50, 20, 20]) == [1]         # limite 36: 20 entra, 20+20 não
    assert slots_a_trocar([50, 45, 5]) == [2]          # 45 é pulado, o 5 entra
    ok += 1

    # 3. teto de slots: nunca passa de MAX_SLOTS nem quando caberia mais
    assert slots_a_trocar([20, 10, 10, 10, 10, 10, 10, 10, 10]) == [1, 2]
    ok += 1

    # 4. tabela de um slot só não é tocada (nada além do slot 0)
    assert slots_a_trocar([100]) == []
    ok += 1

    # 5. catálogo: só forma base, não mítica, da Gen 2 em diante, em ordem de ID
    cat = catalogo_teste()
    pool = pool_de_candidatos(cat)
    nomes = [c["nome"] for c in pool]
    assert "PHIONE" not in nomes and "TATSUGIRI_CURLY" not in nomes and "PIDGEY" not in nomes
    assert "SPEAROW" not in nomes                     # Gen 1, já é vanilla
    assert "ORTHWORM" in nomes and "NACLI" in nomes
    assert nomes == sorted(nomes, key=lambda n: cat[n]["id"])
    ok += 1

    # 6. mesmo tipo primário quando existe (PIDGEY NORMAL -> STARLY, BST 245)
    novo = escolher_substituto("MAP_X", "land_mons", 1, cat["PIDGEY"], pool, set())
    assert novo["nome"] == "STARLY", novo
    ok += 1

    # 7. sem candidato do mesmo tipo, escolhe outro qualquer do pool
    fantasma = {"bst": 300, "tipos": ["GHOST"]}   # nenhum candidato é GHOST
    novo = escolher_substituto("MAP_X", "land_mons", 1, fantasma, pool, set())
    assert novo["nome"] in nomes, novo
    ok += 1

    # 8. evita repetir: com todos menos um marcados como usados, sobra ele
    todos = {c["nome"] for c in pool}
    novo = escolher_substituto("MAP_X", "land_mons", 1, fantasma, pool, todos - {"SHELLOS"})
    assert novo["nome"] == "SHELLOS", novo
    # e se TODOS estiverem usados, ainda devolve alguém (não trava)
    assert escolher_substituto("MAP_X", "land_mons", 1, fantasma, pool, todos)["nome"] in nomes
    ok += 1

    # 9. determinismo: mesma entrada -> mesmo resultado
    a = escolher_substituto("MAP_ROUTE9", "water_mons", 3, cat["TENTACOOL"], pool, set())
    b = escolher_substituto("MAP_ROUTE9", "water_mons", 3, cat["TENTACOOL"], pool, set())
    assert a["nome"] == b["nome"]
    ok += 1

    # 10. a mistura completa: Rota 1 com Gen 9 no primeiro slot trocado
    doc = json.loads(json.dumps(GRUPO_TESTE))
    st = misturar(doc, cat)
    enc = doc["wild_encounter_groups"][0]["encounters"]
    fr = [e for e in enc if e["map"] == "MAP_ROUTE1" and e["base_label"] == "sRoute1_FireRed"][0]
    mons = fr["land_mons"]["mons"]
    assert mons[0]["species"] == "SPECIES_PIDGEY"            # slot 0 intacto
    escolhido = mons[1]["species"][len("SPECIES_"):]
    assert cat[escolhido]["id"] >= GEN_9_INICIO, escolhido   # Gen 9 de verdade
    ok += 1

    # 11. FireRed e LeafGreen recebem a MESMA mistura (semente sem base_label)
    lg = [e for e in enc if e["map"] == "MAP_ROUTE1" and e["base_label"] == "sRoute1_LeafGreen"][0]
    assert [m["species"] for m in lg["land_mons"]["mons"]] == [m["species"] for m in mons]
    ok += 1

    # 12. níveis preservados
    for e in enc:
        for campo in CAMPOS:
            if campo in e:
                for m in e[campo]["mons"]:
                    assert m["min_level"] in (3, 5, 10, 16), m
    ok += 1

    # 13. idempotência: a segunda passada não muda nada e só contabiliza
    antes = json.dumps(doc, sort_keys=True)
    st2 = misturar(doc, cat)
    assert json.dumps(doc, sort_keys=True) == antes
    assert st2["trocados"] == 0 and st2["ja_misturados"] == st["trocados"], st2
    ok += 1

    # 13b. invariantes: o resultado passa, e um slot 0 trocado à mão reprova
    assert conferir_invariantes(doc, cat) == []
    quebrado = json.loads(json.dumps(doc))
    quebrado["wild_encounter_groups"][0]["encounters"][2]["land_mons"]["mons"][0]["species"] = "SPECIES_NACLI"
    assert conferir_invariantes(quebrado, cat), "slot 0 trocado deveria reprovar"
    ok += 1

    # 14. contagens: 6 tabelas; 2 slots em cada tabela de 12/5 slots, 1 em cada
    #     tabela de 2/10 slots; Rota 1 FR + LG = 4 trocas
    assert st["tabelas"] == 6, st
    assert st["trocados"] == 2 + 2 + 2 + 1 + 1 + 1, st
    assert len(st["rota1"]) == 4, st          # 2 slots x (FireRed + LeafGreen)
    assert st["por_gen"][9] >= 2, st
    ok += 1

    # 15. geração a partir do número
    assert [geracao(n) for n in (1, 151, 152, 251, 386, 387, 493, 649, 721, 809, 905, 906, 1025)] \
        == [1, 1, 2, 2, 3, 4, 4, 5, 6, 7, 8, 9, 9]
    ok += 1

    # 16. JSON redondo
    assert json.loads(json.dumps(doc, **JSON_KW)) == doc
    ok += 1

    print(f"self-test: {ok}/17 ok")
    return 0 if ok == 17 else 1


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pokefirered", type=Path)
    ap.add_argument("--reference", type=Path)
    ap.add_argument("--write", action="store_true", help="aplica a mistura")
    ap.add_argument("--check", action="store_true", help="falha se o arquivo divergir")
    ap.add_argument("--relatorio", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.pokefirered or not a.reference:
        ap.error("informe --pokefirered e --reference")

    p = a.pokefirered / ARQUIVO
    if a.write:
        st = aplicar(a.pokefirered, a.reference)
        print(f"mistura aplicada: {st['trocados']} slots em {st['tabelas']} tabelas; "
              f"Rota 1 = {', '.join(st['rota1'])}")
        if a.relatorio:
            _imprimir(st)
        return 0
    if a.check:
        codigo, st, erros = verificar(a.pokefirered, a.reference)
        if codigo:
            print("FALHOU: o wild_encounters.json nao tem o formato da mistura "
                  "(rode --write):", file=sys.stderr)
            for e in erros[:20]:
                print("  " + e, file=sys.stderr)
            if len(erros) > 20:
                print(f"  ... e mais {len(erros) - 20}", file=sys.stderr)
        else:
            print(f"ok: {st['trocados']} slots misturados em {st['tabelas']} tabelas; "
                  f"Rota 1 = {', '.join(st['rota1'])}")
        return codigo

    st = misturar(json.loads(p.read_text(encoding="utf-8")),
                  catalogo(a.pokefirered, a.reference))
    _imprimir(st)
    return 0


def _imprimir(st: dict) -> None:
    print(f"candidatos (forma base, Gen 4-9, não mítica): {st['candidatos']} "
          f"(com BST medido: {st['com_bst']})")
    print(f"tabelas tratadas: {st['tabelas']} · slots trocados: {st['trocados']}")
    print("por geração: " + ", ".join(f"Gen {g} = {n}" for g, n in st["por_gen"].items()))
    print("Rota 1 (grama): " + ", ".join(dict.fromkeys(st["rota1"])) + "  [FR + LG]")


if __name__ == "__main__":
    sys.exit(main())
