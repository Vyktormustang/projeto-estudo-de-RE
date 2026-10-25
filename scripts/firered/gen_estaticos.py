#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Distribui os encontros estáticos (inobtíveis "como lendários") nos map.json.

Para cada FAMÍLIA inobtível coloca a FORMA BASE como objeto no overworld
(sprite = ícone, script compartilhado EventScript_EncontroEstatico, flag
virtual 0x5000+SPECIES). O mapjson do build regenera events.inc sozinho.

Regras de colocação:
  - tile alcançável (BFS a partir de warps e bordas no map.bin), colisão 0;
  - longe de bordas (2), warps (raio 1), objetos/eventos existentes;
  - >= 3 vizinhos ortogonais passáveis (não entope corredores);
  - espaçamento Chebyshev >= 4 entre estáticos;
  - todos os estáticos de um mapa usam a MESMA paleta de ícone (dividem o
    slot de paleta NPC_SPECIAL);
  - mapas com Meteorite/Seagallop/SSAnne (usam esse slot) ficam de fora;
  - Rota 1 recebe CHIKORITA (prova fácil) e só tiles com x>=15 (não atrapalha
    o corredor usado pela regressão);
  - idempotente: parte sempre do map.json de HEAD (git show).

Uso:
  gen_estaticos.py --pokefirered /tmp/pokefirered --write|--check
  gen_estaticos.py --self-test
"""
import argparse
import collections
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
LISTA_INOBTIVEIS = os.path.join(AQUI, "estaticos", "inobtiveis.json")

GFX_PROIBIDOS = {"OBJ_EVENT_GFX_METEORITE", "OBJ_EVENT_GFX_SEAGALLOP", "OBJ_EVENT_GFX_SS_ANNE"}
CAP_POR_MAPA = 6
ESPACO = 4

# Ordem de progressão (prefixo curado; o resto entra em ordem alfabética).
ORDEM_MAPAS = [
    "Route1", "Route2", "ViridianForest", "Route22", "Route3", "MtMoon_1F",
    "MtMoon_B1F", "MtMoon_B2F", "Route4", "Route24", "Route25", "Route5",
    "Route6", "Route11", "DiglettsCave_B1F", "Route9", "Route10",
    "RockTunnel_1F", "RockTunnel_B1F", "Route8", "Route7", "Route16", "Route18", "Route12", "Route13", "Route14", "Route15",
    "SafariZone_Center", "SafariZone_East", "SafariZone_North",
    "SafariZone_West", "Route19", "Route20", "SeafoamIslands_1F",
    "SeafoamIslands_B1F", "SeafoamIslands_B2F", "SeafoamIslands_B3F",
    "Route21_North", "Route21_South", "PokemonTower_3F", "PokemonTower_4F",
    "PokemonTower_5F", "PokemonTower_6F", "Route23", "VictoryRoad_1F",
    "VictoryRoad_2F", "VictoryRoad_3F", "CeruleanCave_1F", "CeruleanCave_2F",
]
PADRAO_EXTRA = re.compile(
    r"^(Route\d+\w*|(One|Two|Three|Four|Five|Six|Seven)Island_[A-Z]\w*)$")
EXTRA_VETADOS = re.compile(
    r"(Room|House|Mart|Center|Harbor|Gate|Lab|Game|Hotel|Cave_B4F|Tower|Lighthouse|Entrance|DayCare|Warehouse|EmberSpa|Route17)")


def falar(*a):
    print(*a, flush=True)


def git_show(raiz, caminho):
    return subprocess.run(["git", "-C", raiz, "show", f"HEAD:{caminho}"],
                          capture_output=True, text=True, check=True).stdout


# ---------- dados de espécies ----------

def ler_parentes(raiz):
    """child -> pai, a partir das tabelas de evolução."""
    pai = {}
    for arq in ("src/data/pokemon/evolution.h", "src/data/pokemon/evolution_gen4_9.h"):
        texto = open(os.path.join(raiz, arq), encoding="utf-8").read()
        for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*(\{.*?\}\})", texto, re.S):
            origem, corpo = m.group(1), m.group(2)
            for t in re.finditer(r"\{\s*(EVO_\w+)\s*,\s*([^,}]+)\s*,\s*(SPECIES_\w+)", corpo):
                pai.setdefault(t.group(3), origem)
    return pai


def ler_bst(raiz):
    bst = {}
    for arq in ("src/data/pokemon/species_info.h", "src/data/pokemon/species_info_gen4_9.h"):
        texto = open(os.path.join(raiz, arq), encoding="utf-8").read()
        for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*\n?\s*\{(.*?)\n\s{4}\},", texto, re.S):
            esp, corpo = m.group(1), m.group(2)
            soma = 0
            for campo in ("baseHP", "baseAttack", "baseDefense",
                          "baseSpeed", "baseSpAttack", "baseSpDefense"):
                mm = re.search(r"\." + campo + r"\s*=\s*(\d+)", corpo)
                soma += int(mm.group(1)) if mm else 0
            bst[esp] = soma
    return bst


def ler_icones(raiz):
    """espécies com ícone + índice de paleta do ícone."""
    texto = open(os.path.join(raiz, "src/pokemon_icon.c"), encoding="utf-8").read()
    tabela = texto.split("gMonIconTable[]")[1].split("};")[0]
    com_icone = set(re.findall(r"\[(SPECIES_\w+)\]", tabela))
    pal = {}
    indices = texto.split("gMonIconPaletteIndices[]")[1].split("};")[0]
    for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*(\d+)", indices):
        pal[m.group(1)] = int(m.group(2))
    return com_icone, pal


def formas_base(inobtiveis, pai):
    conjunto = set(inobtiveis)
    bases = []
    for esp in inobtiveis:  # mantém ordem por id interno
        atual, passos = esp, 0
        while pai.get(atual) in conjunto and passos < 30:
            atual, passos = pai[atual], passos + 1
        if atual == esp:
            bases.append(esp)
    return bases


# ---------- mapas ----------

def ler_layouts(raiz):
    dados = json.loads(git_show(raiz, "data/layouts/layouts.json"))
    return {l["id"]: l for l in dados["layouts"] if l and l.get("id")}


def carregar_colisao(raiz, layout):
    w, h = int(layout["width"]), int(layout["height"])
    bruto = open(os.path.join(raiz, layout["blockdata_filepath"]), "rb").read()
    tiles = struct.unpack_from(f"<{w * h}H", bruto)
    return w, h, tiles


def achar_pontos(raiz, nome, mapa, layout, quantos):
    w, h, tiles = carregar_colisao(raiz, layout)

    def passavel(x, y):
        return 0 <= x < w and 0 <= y < h and ((tiles[y * w + x] >> 10) & 3) == 0

    sementes = []
    for wp in mapa.get("warp_events", []):
        if passavel(wp["x"], wp["y"]):
            sementes.append((wp["x"], wp["y"]))
    for x in range(w):
        for y in (0, h - 1):
            if passavel(x, y):
                sementes.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if passavel(x, y):
                sementes.append((x, y))

    visto = set(sementes)
    fila = collections.deque(sementes)
    while fila:
        x, y = fila.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p not in visto and passavel(*p):
                visto.add(p)
                fila.append(p)

    ocupado = set()
    for o in mapa.get("object_events", []):
        rx = int(str(o.get("movement_range_x", 0)) or 0)
        ry = int(str(o.get("movement_range_y", 0)) or 0)
        for dx in range(-rx, rx + 1):
            for dy in range(-ry, ry + 1):
                ocupado.add((o["x"] + dx, o["y"] + dy))
    for wp in mapa.get("warp_events", []):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                ocupado.add((wp["x"] + dx, wp["y"] + dy))
    for ev in mapa.get("coord_events", []) + mapa.get("bg_events", []):
        ocupado.add((ev["x"], ev["y"]))

    candidatos = []
    for (x, y) in visto:
        if x < 2 or y < 2 or x > w - 3 or y > h - 3:
            continue
        if (x, y) in ocupado:
            continue
        if nome == "Route1" and x < 15:
            continue  # protege o corredor usado pela regressão
        vizinhos = sum(passavel(x + dx, y + dy)
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if vizinhos < 3:
            continue
        candidatos.append((x, y))

    candidatos.sort(key=lambda p: hashlib.sha1(f"{nome}:{p[0]}:{p[1]}".encode()).hexdigest())
    escolhidos = []
    for p in candidatos:
        if all(max(abs(p[0] - q[0]), abs(p[1] - q[1])) >= ESPACO for q in escolhidos):
            escolhidos.append(p)
            if len(escolhidos) == quantos:
                break
    elevs = []
    for (x, y) in escolhidos:
        e = tiles[y * w + x] >> 12
        elevs.append(e if e else 3)
    return escolhidos, elevs


def mapas_elegiveis(raiz):
    base = os.path.join(raiz, "data/maps")
    todos = sorted(os.listdir(base))
    extras = [m for m in todos
              if m not in ORDEM_MAPAS and PADRAO_EXTRA.match(m)
              and not EXTRA_VETADOS.search(m)]
    nomes = [m for m in ORDEM_MAPAS if os.path.isdir(os.path.join(base, m))] + extras
    aceitos = []
    for nome in nomes:
        try:
            mapa = json.loads(git_show(raiz, f"data/maps/{nome}/map.json"))
        except subprocess.CalledProcessError:
            continue
        gfx = {o.get("graphics_id") for o in mapa.get("object_events", [])}
        if gfx & GFX_PROIBIDOS:
            continue
        aceitos.append((nome, mapa))
    return aceitos


# ---------- montagem ----------

def novo_objeto(especie, x, y, elev):
    return {
        "graphics_id": "OBJ_EVENT_GFX_MON_ESTATICO",
        "x": x,
        "y": y,
        "elevation": elev,
        "movement_type": "MOVEMENT_TYPE_FACE_DOWN",
        "movement_range_x": 1,
        "movement_range_y": 1,
        "trainer_type": "TRAINER_TYPE_NONE",
        "trainer_sight_or_berry_tree_id": especie,
        "script": "EventScript_EncontroEstatico",
        "flag": f"0x5000+{especie}",
    }


def gerar(raiz, escrever):
    inobtiveis = json.load(open(LISTA_INOBTIVEIS, encoding="utf-8"))
    pai = ler_parentes(raiz)
    bst = ler_bst(raiz)
    com_icone, pal = ler_icones(raiz)
    bases = formas_base(inobtiveis, pai)
    sem_icone = [b for b in bases if b not in com_icone]
    bases = [b for b in bases if b in com_icone]
    falar(f"inobtíveis={len(inobtiveis)} famílias/bases={len(bases)} sem_icone={len(sem_icone)}")
    if sem_icone:
        falar("  sem ícone (fora):", ", ".join(sem_icone))

    grupos = collections.defaultdict(list)  # paleta -> [espécies]
    for b in bases:
        grupos[pal.get(b, 0)].append(b)
    for g in grupos.values():
        g.sort(key=lambda e: (bst.get(e, 0), e))
    pal_chikorita = pal.get("SPECIES_CHIKORITA", 0)
    if "SPECIES_CHIKORITA" in grupos.get(pal_chikorita, []):
        grupos[pal_chikorita].remove("SPECIES_CHIKORITA")
        grupos[pal_chikorita].insert(0, "SPECIES_CHIKORITA")

    layouts = ler_layouts(raiz)
    total, usados = 0, []
    for nome, mapa in mapas_elegiveis(raiz):
        if not any(grupos.values()):
            break
        layout = layouts.get(mapa.get("layout"))
        if not layout or not layout.get("blockdata_filepath"):
            continue
        if nome == "Route1":
            escolha = pal_chikorita
        else:
            escolha = max(grupos, key=lambda k: len(grupos[k]))
        if not grupos[escolha]:
            continue
        quantos = min(CAP_POR_MAPA, len(grupos[escolha]))
        pontos, elevs = achar_pontos(raiz, nome, mapa, layout, quantos)
        if not pontos:
            continue
        especies = grupos[escolha][:len(pontos)]
        del grupos[escolha][:len(pontos)]
        for (x, y), elev, esp in zip(pontos, elevs, especies):
            mapa.setdefault("object_events", []).append(novo_objeto(esp, x, y, elev))
        total += len(especies)
        usados.append((nome, especies, pontos))
        falar(f"{nome:32s} pal={escolha} " +
              " ".join(f"{e.replace('SPECIES_', '')}@{p}" for e, p in zip(especies, pontos)))
        if escrever:
            destino = os.path.join(raiz, "data/maps", nome, "map.json")
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(mapa, f, indent=2, ensure_ascii=False)
                f.write("\n")
    sobras = sum(len(g) for g in grupos.values())
    falar(f"TOTAL colocados={total} sobras={sobras} mapas={len(usados)}")
    if sobras:
        for k, g in grupos.items():
            if g:
                falar(f"  sobra pal={k}: {len(g)}: {', '.join(x.replace('SPECIES_', '') for x in g[:8])}…")
    return 0 if total and not sobras else (0 if total and sobras == 0 else 1 if not total else 2)


def self_test():
    assert os.path.exists(LISTA_INOBTIVEIS)
    dados = json.load(open(LISTA_INOBTIVEIS, encoding="utf-8"))
    assert len(dados) == 500 and all(d.startswith("SPECIES_") for d in dados)
    o = novo_objeto("SPECIES_MEW", 3, 4, 3)
    assert o["flag"] == "0x5000+SPECIES_MEW" and " " not in o["flag"]
    pai = {"SPECIES_B": "SPECIES_A", "SPECIES_C": "SPECIES_B", "SPECIES_E": "SPECIES_D"}
    bases = formas_base(["SPECIES_A", "SPECIES_B", "SPECIES_C", "SPECIES_E"], pai)
    assert bases == ["SPECIES_A", "SPECIES_E"], bases  # E fica: pai D não está no conjunto
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.pokefirered or not (args.check or args.write):
        ap.error("use --pokefirered PATH com --check ou --write")
    sys.exit(gerar(args.pokefirered, args.write))


if __name__ == "__main__":
    main()
