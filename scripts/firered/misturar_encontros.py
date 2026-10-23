#!/usr/bin/env python3
"""Mistura Pokémon das Gens 2-9 nas tabelas de encontro selvagem de Kanto.

Contexto: a base `CharonChaos88/FireRedExpansion` (pokeemerald-expansion 1.15 +
mapas de Kanto/Sevii) traz todos os dados das Gens 1-9, mas as tabelas de
encontro selvagem continuam sendo as originais de FireRed: só Gen 1. Sem esta
etapa, o jogador NAO encontra nenhum Pokémon novo andando normalmente.

Regra aplicada (deterministica, reproduzivel):

1. Cada tabela (land_mons / water_mons / fishing_mons) de cada mapa e tratada
   separadamente. O slot 0 (o mais comum) NUNCA e trocado: preserva a
   identidade da rota (Pidgey/Rattata continuam existindo).
2. A partir do slot 1, troca-se slots ate somar ~40% da probabilidade da
   tabela, usando os pesos de Gen 3 (20/20/10/10/10/10/5/5/4/4/1/1 na grama,
   60/30/5/4/1 na agua, 40/40/15/4/1 na pesca).
3. O substituto e sorteado de forma deterministica (sha256 de mapa+tabela+slot)
   entre especies de Gen 2-9 que:
     - sao a forma base (nome da constante == nome do National Dex, o que
       exclui Mega/Alolan/Galarian/Hisuian/Paldeano e outras formas);
     - nao sao miticas (`.isMythical = TRUE`);
     - tem BST dentro de +-120 do Pokémon que sai (isso barra lendarios em
       rotas iniciais e mantem a curva de dificuldade);
     - tem o MESMO tipo primario, se existir candidato (senao qualquer tipo).
4. Os niveis (min_level/max_level) do slot sao preservados.

Uso:
    python3 misturar_encontros.py --self-test
    python3 misturar_encontros.py --aplicar /caminho/para/FireRedExpansion
    python3 misturar_encontros.py --relatorio /caminho/para/FireRedExpansion
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

PESOS = {
    "land_mons": [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1],
    "water_mons": [60, 30, 5, 4, 1],
    "fishing_mons": [40, 40, 15, 4, 1, 40, 40, 15, 4, 1],
}
ALVO = 40  # % da probabilidade da tabela que pode virar Gen 2-9

RE_ENTRADA = re.compile(r"\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{")
RE_TIPOS = re.compile(r"\.types\s*=\s*MON_TYPES\(([^)]*)\)")
RE_NATDEX = re.compile(r"\.natDexNum\s*=\s*NATIONAL_DEX_([A-Z0-9_]+)")
RE_STAT = re.compile(r"\.base(HP|Attack|Defense|Speed|SpAttack|SpDefense)\s*=\s*(\d+)")
RE_MITICA = re.compile(r"\.isMythical\s*=\s*TRUE")


def pesos_da_tabela(nome, n_slots):
    """Pesos de Gen 3 para a tabela; uniforme se o tamanho nao bater."""
    p = PESOS.get(nome)
    if p and len(p) == n_slots:
        return p
    return [100 // max(n_slots, 1)] * n_slots


def slots_a_trocar(nome, n_slots, alvo=ALVO):
    """Indices que serao substituidos: comeca no 1, para ao somar ~alvo%."""
    pesos = pesos_da_tabela(nome, n_slots)
    total = sum(pesos) or 1
    acc, out = 0, []
    for i in range(1, n_slots):
        if acc * 100.0 / total >= alvo:
            break
        out.append(i)
        acc += pesos[i]
    return out


def faixa_bst(bst, margem=120):
    return (bst - margem, bst + margem)


def escolher(candidatos, mapa, tabela, slot, tipo):
    """Sorteio deterministico dentro dos candidatos."""
    chave = f"{mapa}|{tabela}|{slot}".encode()
    h = int.from_bytes(hashlib.sha256(chave).digest()[:8], "big")
    if tipo:
        iguais = [c for c in candidatos if c["tipos"] and c["tipos"][0] == tipo]
        if iguais:
            candidatos = iguais
    return candidatos[h % len(candidatos)]


def parse_especies(species_dir):
    """Le os headers de species_info e devolve dict nome -> dados."""
    especies = {}
    for arq in sorted(Path(species_dir).glob("gen_*_families.h")):
        gen = int(re.search(r"gen_(\d+)_", arq.name).group(1))
        txt = arq.read_text(encoding="utf-8", errors="replace")
        marcas = list(RE_ENTRADA.finditer(txt))
        for i, m in enumerate(marcas):
            nome = m.group(1)
            fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(txt)
            bloco = txt[m.end():fim]
            nat = RE_NATDEX.search(bloco)
            tipos = RE_TIPOS.search(bloco)
            stats = {k: int(v) for k, v in RE_STAT.findall(bloco)}
            if not nat or not tipos:
                continue
            bst = sum(stats.get(k, 0) for k in
                      ("HP", "Attack", "Defense", "Speed", "SpAttack", "SpDefense"))
            especies[nome] = {
                "gen": gen,
                "natdex": nat.group(1),
                "tipos": [t.strip().replace("TYPE_", "") for t in tipos.group(1).split(",")],
                "bst": bst,
                "mitica": bool(RE_MITICA.search(bloco)),
            }
    return especies


def eh_forma_base(nome, dados):
    """SPECIES_X e forma base <=> o natDex se chama X."""
    return nome.replace("SPECIES_", "") == dados["natdex"]


def pool_moderno(especies, gen_min=2):
    return [dict(nome=n, **d) for n, d in especies.items()
            if d["gen"] >= gen_min and eh_forma_base(n, d) and not d["mitica"] and d["bst"] > 0]


def candidatos_para(pool, bst_original, tipo, uso):
    """Candidatos em ordem de preferencia (do mais estrito ao mais frouxo).

    Repetir especie na mesma tabela e normal no jogo, entao "ja usado" apenas
    rebaixa a prioridade — nunca impede a substituicao.
    """
    lo, hi = faixa_bst(bst_original)

    def filtro(mesmo_tipo, na_faixa, novo):
        return [c for c in pool
                if (not mesmo_tipo or (c["tipos"] and c["tipos"][0] == tipo))
                and (not na_faixa or lo <= c["bst"] <= hi)
                and (not novo or c["nome"] not in uso)]

    for mesmo_tipo, na_faixa, novo in ((True, True, True), (True, True, False),
                                       (True, False, True), (True, False, False),
                                       (False, True, True), (False, True, False),
                                       (False, False, True), (False, False, False)):
        cands = filtro(mesmo_tipo, na_faixa, novo)
        if cands:
            return cands
    return list(pool)


def misturar(dados, especies, semente_pool=None, alvo=ALVO):
    """Aplica a regra em um dict de wild_encounters e devolve estatisticas."""
    pool = pool_moderno(especies)
    if not pool:
        raise SystemExit("pool moderno vazio: species_info nao encontrado?")
    stats = {"tabelas": 0, "trocados": 0, "mapas": 0, "por_gen": {}, "exemplos": []}
    for grupo in dados["wild_encounter_groups"]:
        if not grupo.get("for_maps"):
            continue
        for enc in grupo["encounters"]:
            mapa = enc["map"]
            mudou = False
            for tabela in ("land_mons", "water_mons", "fishing_mons"):
                if tabela not in enc:
                    continue
                mons = enc[tabela]["mons"]
                stats["tabelas"] += 1
                usados = set()
                for idx in slots_a_trocar(tabela, len(mons), alvo):
                    atual = mons[idx]
                    orig = especies.get(atual["species"])
                    if not orig:
                        continue
                    cands = candidatos_para(pool, orig["bst"], orig["tipos"][0], usados)
                    if not cands:
                        continue
                    novo = escolher(cands, mapa, tabela, idx, orig["tipos"][0])
                    usados.add(novo["nome"])
                    if stats["exemplos"] and len(stats["exemplos"]) < 15:
                        stats["exemplos"].append(
                            f"{mapa} {tabela}[{idx}]: {atual['species']} -> {novo['nome']}")
                    elif not stats["exemplos"]:
                        stats["exemplos"].append(
                            f"{mapa} {tabela}[{idx}]: {atual['species']} -> {novo['nome']}")
                    mons[idx]["species"] = novo["nome"]
                    stats["trocados"] += 1
                    stats["por_gen"][novo["gen"]] = stats["por_gen"].get(novo["gen"], 0) + 1
                    mudou = True
            if mudou:
                stats["mapas"] += 1
    return stats


# --------------------------------------------------------------------------- #
# self-test
# --------------------------------------------------------------------------- #
def self_test():
    ok = 0
    falhas = []

    def check(nome, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            falhas.append(nome)

    # 1. pesos conhecidos
    check("pesos land", pesos_da_tabela("land_mons", 12)[0] == 20)
    check("pesos fallback", len(pesos_da_tabela("land_mons", 3)) == 3)

    # 2. grama: nunca troca o slot 0; soma ~40%
    s = slots_a_trocar("land_mons", 12)
    check("land nao troca slot0", 0 not in s)
    check("land alvo ~40%", 35 <= sum(pesos_da_tabela("land_mons", 12)[i] for i in s) <= 45)
    check("agua troca algo", len(slots_a_trocar("water_mons", 5)) >= 2)
    check("pesca troca algo", len(slots_a_trocar("fishing_mons", 10)) >= 2)

    # 3. parse de especies sintetico
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "gen_9_families.h"
        p.write_text("""
    [SPECIES_SPRIGATITO] =
    {
        .natDexNum = NATIONAL_DEX_SPRIGATITO,
        .baseHP = 40, .baseAttack = 61, .baseDefense = 54,
        .baseSpeed = 65, .baseSpAttack = 45, .baseSpDefense = 45,
        .types = MON_TYPES(TYPE_GRASS),
    },
    [SPECIES_SPRIGATITO_MEGA] =
    {
        .natDexNum = NATIONAL_DEX_SPRIGATITO,
        .types = MON_TYPES(TYPE_GRASS, TYPE_DARK),
    },
""", encoding="utf-8")
        sp = parse_especies(td)
        check("parse achou 2", len(sp) == 2)
        check("bst somado", sp["SPECIES_SPRIGATITO"]["bst"] == 310)
        check("forma base ok", eh_forma_base("SPECIES_SPRIGATITO", sp["SPECIES_SPRIGATITO"]))
        check("forma nao-base", not eh_forma_base("SPECIES_SPRIGATITO_MEGA", sp["SPECIES_SPRIGATITO_MEGA"]))
        pool = pool_moderno(sp)
        check("pool so base", len(pool) == 1)

    # 4. determinismo + nao repete + preserva nivel
    esp = {
        "SPECIES_PIDGEY": {"gen": 1, "natdex": "PIDGEY", "tipos": ["NORMAL"], "bst": 251, "mitica": False},
        "SPECIES_A": {"gen": 9, "natdex": "A", "tipos": ["NORMAL"], "bst": 260, "mitica": False},
        "SPECIES_B": {"gen": 8, "natdex": "B", "tipos": ["NORMAL"], "bst": 280, "mitica": False},
        "SPECIES_C": {"gen": 7, "natdex": "C", "tipos": ["WATER"], "bst": 300, "mitica": False},
    }
    base = {
        "wild_encounter_groups": [{
            "for_maps": True,
            "encounters": [{
                "map": "MAP_TESTE",
                "land_mons": {"encounter_rate": 20, "mons": [
                    {"min_level": 2, "max_level": 3, "species": "SPECIES_PIDGEY"} for _ in range(12)]},
            }],
        }]
    }
    d1 = json.loads(json.dumps(base))
    d2 = json.loads(json.dumps(base))
    st1 = misturar(d1, esp)
    st2 = misturar(d2, esp)
    check("deterministico", d1 == d2)
    mons = d1["wild_encounter_groups"][0]["encounters"][0]["land_mons"]["mons"]
    check("slot0 preservado", mons[0]["species"] == "SPECIES_PIDGEY")
    check("trocou >0", st1["trocados"] > 0)
    check("nivel preservado", all(m["min_level"] == 2 and m["max_level"] == 3 for m in mons))
    check("so tipos compativeis", all(m["species"] in ("SPECIES_PIDGEY", "SPECIES_A", "SPECIES_B") for m in mons))
    trocados = [mons[i]["species"] for i in slots_a_trocar("land_mons", 12)]
    check("sem repeticao enquanto ha livre", len(set(trocados)) == 2)
    check("mesma stat duas vezes", st1["trocados"] == st2["trocados"])

    print(f"self-test: {ok}/{ok + len(falhas)} OK")
    for f in falhas:
        print("  FALHOU:", f)
    return 0 if not falhas else 1


def conta_modernos(dados, especies):
    """Quantas especies Gen 2+ aparecem no total de encontros."""
    vistos = set()
    for grupo in dados["wild_encounter_groups"]:
        if not grupo.get("for_maps"):
            continue
        for enc in grupo["encounters"]:
            for t in ("land_mons", "water_mons", "fishing_mons"):
                for m in enc.get(t, {}).get("mons", []):
                    e = especies.get(m["species"])
                    if e and e["gen"] >= 2:
                        vistos.add(m["species"])
    return len(vistos)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--aplicar", metavar="REPO")
    ap.add_argument("--relatorio", metavar="REPO")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    alvo = a.aplicar or a.relatorio
    if not alvo:
        ap.print_help()
        return 2

    repo = Path(alvo)
    esppath = repo / "src/data/pokemon/species_info"
    js = repo / "src/data/wild_encounters.json"
    if not esppath.is_dir() or not js.is_file():
        print(f"ERRO: {repo} nao parece ser o repo (faltam species_info/ ou wild_encounters.json)")
        return 2

    especies = parse_especies(esppath)
    dados = json.loads(js.read_text(encoding="utf-8"))
    print(f"especies lidas: {len(especies)} | pool Gen2+ base: {len(pool_moderno(especies))}")
    print(f"Gen 2+ nos encontros ANTES: {conta_modernos(dados, especies)}")

    if a.relatorio:
        print("(modo --relatorio: nada foi escrito)")
        return 0

    stats = misturar(dados, especies)
    shutil.copy2(js, js.with_suffix(".json.bak"))
    js.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"tabelas tratadas: {stats['tabelas']} | slots trocados: {stats['trocados']} "
          f"| mapas alterados: {stats['mapas']}")
    print("novos por geracao:", dict(sorted(stats["por_gen"].items())))
    print(f"Gen 2+ nos encontros DEPOIS: {conta_modernos(dados, especies)}")
    print("exemplos:")
    for e in stats["exemplos"][:10]:
        print("  ", e)
    print(f"backup: {js.with_suffix('.json.bak')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
