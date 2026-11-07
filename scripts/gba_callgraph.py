#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gba_callgraph.py — FASE 3: grafo de chamadas (BL direto) + métricas de arquitetura
==================================================================================

OBJETIVO
    Construir o callgraph do binário a partir dos callsites de BL direto
    (produzidos por gba_disasm.py) e do universo de funções validadas
    (functions.csv), gerando: DOT (Graphviz), TSV de arestas e métricas
    (hubs de entrada/saída, alcançáveis a partir da entry, componentes
    fortemente conexos — SCC/Tarjan).

ENTRADAS (padrões relativos a gba-re/)
    -f functions.csv                      universo de nós (já filtrado por prova)
    -c reports/<rom>_callsites.tsv        arestas site→alvo
SAÍDAS
    callgraph/callgraph.dot               grafo completo (Graphviz)
    callgraph/edges.tsv                   arestas caller→callee com nomes
    callgraph/callgraph_metrics.json      métricas + rankings
    logs/gba_callgraph_runs.jsonl

USO
    python3 gba_callgraph.py -f functions.csv -c reports/X_callsites.tsv [-o callgraph]
    python3 gba_callgraph.py --self-test

LIMITAÇÕES DECLARADAS (importantes para interpretar)
    1. Só arestas de BL DIRETO. Chamadas indiretas (tabelas de despacho,
       ponteiros de callback, IRQ) NÃO aparecem — os 34 handlers de cada
       dispatcher, por ex., ficam "desconectados" até análise de tabelas.
    2. Atribuição de callsite→caller usa "função válida mais próxima acima"
       (linear sweep). Sites dentro de dados podem ser atribuídos à função
       errada — ruído tolerável para métricas agregadas, não para prova fina.
    3. BFS a partir da entry mostra apenas o que é alcançável por BL direto;
       "inalcançáveis" incluem handlers indiretos reais — não é prova de código morto.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSAO = "1.0.0"
ENTRY_DEFAULT = "0x080003a4"   # ENTRY_THUMB_main (CONFIRMADO no ciclo 4)


# --------------------------------------------------------------------------- #
# Leitura e construção do grafo
# --------------------------------------------------------------------------- #

def ler_nos(functions_csv: Path) -> list[tuple[int, str]]:
    nos = []
    for linha in functions_csv.read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.startswith("#") or linha.startswith("endereco_hex"):
            continue
        cols = linha.split(",")
        nos.append((int(cols[0], 16), cols[2]))
    nos.sort()
    return nos


def ler_callsites(tsv: Path) -> list[tuple[int, int]]:
    pares = []
    with tsv.open(encoding="utf-8") as f:
        r = csv.reader(f, delimiter="\t")
        next(r, None)
        for row in r:
            if len(row) >= 2:
                pares.append((int(row[0], 16), int(row[1], 16)))
    return pares


def construir_grafo(nos: list[tuple[int, str]], callsites: list[tuple[int, int]]):
    addrs = [a for a, _ in nos]
    conj = set(addrs)

    def caller_de(site: int) -> int | None:
        i = bisect_right(addrs, site) - 1
        return addrs[i] if i >= 0 else None

    arestas: Counter = Counter()
    externos = 0
    for site, alvo in callsites:
        if alvo not in conj:
            externos += 1
            continue
        c = caller_de(site)
        if c is None or c == alvo:
            continue
        arestas[(c, alvo)] += 1

    adj: dict[int, set] = defaultdict(set)
    adj_rev: dict[int, set] = defaultdict(set)
    indeg, outdeg = Counter(), Counter()
    for (c, t), n in arestas.items():
        if t not in adj[c]:
            adj[c].add(t)
            adj_rev[t].add(c)
            outdeg[c] += 1
        indeg[t] += n
    nodes_set = set(addrs)
    return {
        "nos": nos, "arestas": arestas, "adj": adj, "adj_rev": adj_rev,
        "indeg": indeg, "outdeg": outdeg, "externos": externos,
        "nodes_set": nodes_set,
    }


def tarjan_scc(nodes: set, adj: dict[int, set]) -> list[list[int]]:
    """Tarjan iterativo — lista de componentes fortemente conexos."""
    index, low, stack, on_stack = {}, {}, [], set()
    contador = [0]
    sccs: list[list[int]] = []

    def strongconnect(v0):
        trabalho = [(v0, iter(sorted(adj.get(v0, ()))))]
        index[v0] = low[v0] = contador[0]
        contador[0] += 1
        stack.append(v0)
        on_stack.add(v0)
        while trabalho:
            v, it = trabalho[-1]
            avancou = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = contador[0]
                    contador[0] += 1
                    stack.append(w)
                    on_stack.add(w)
                    trabalho.append((w, iter(sorted(adj.get(w, ())))))
                    avancou = True
                    break
                elif w in on_stack:
                    low[v] = min(low[v], index[w])
            if avancou:
                continue
            trabalho.pop()
            if trabalho:
                p = trabalho[-1][0]
                low[p] = min(low[p], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                sccs.append(comp)

    for v in sorted(nodes):
        if v not in index:
            strongconnect(v)
    return sccs


def bfs(origem: int, adj: dict[int, set]) -> set:
    vistos, fila = set(), [origem]
    while fila:
        n = fila.pop()
        if n in vistos:
            continue
        vistos.add(n)
        fila.extend(x for x in adj.get(n, ()) if x not in vistos)
    return vistos


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #

def self_test(verbose: bool, tmp: Path) -> int:
    tmp.mkdir(parents=True, exist_ok=True)
    csvf = tmp / "functions.csv"
    csvf.write_text(
        "endereco_hex,tamanho_hex,nome,modo_cpu,confianca,origem,evidencia,historico_renomeacao\n"
        "0x08000100,-,MAIN,THUMB,CONFIRMADO,teste,e,e\n"
        "0x08000140,-,FUN_B,THUMB,CONFIRMADO,teste,e,e\n"
        "0x08000180,-,FUN_C,THUMB,CONFIRMADO,teste,e,e\n"
        "0x080001c0,-,FUN_D,THUMB,CONFIRMADO,teste,e,e\n", encoding="utf-8")
    tsv = tmp / "callsites.tsv"
    tsv.write_text(
        "site_hex\talvo_hex\n"
        "0x08000104\t0x08000140\n"  # MAIN→B
        "0x08000108\t0x08000180\n"  # MAIN→C
        "0x08000144\t0x080001c0\n"  # B→D
        "0x08000148\t0x080001c0\n"  # B→D (2ª vez)
        "0x080001c4\t0x08000140\n"  # D→B   (ciclo B-D)
        "0x08000184\t0x08000140\n"  # C→B
        "0x08000188\t0x08009000\n"  # C→externo (ignorar)
        , encoding="utf-8")
    g = construir_grafo(ler_nos(csvf), ler_callsites(tsv))
    MAIN, B, C, D = 0x08000100, 0x08000140, 0x08000180, 0x080001C0
    sccs = [sorted(c) for c in tarjan_scc(g["nodes_set"], g["adj"]) if len(c) > 1]
    alc = bfs(MAIN, g["adj"])
    checks = [
        ("arestas córtex correto", set(g["arestas"]) == {(MAIN, B), (MAIN, C), (B, D), (C, B), (D, B)}),
        ("peso da aresta B→D == 2", g["arestas"][(B, D)] == 2),
        ("indeg B == 4 (MAIN, C, D×1peso? pesos: MAIN1+C1+D1)", g["indeg"][B] == 3),
        ("outdeg MAIN == 2", g["outdeg"][MAIN] == 2),
        ("externo contado == 1", g["externos"] == 1),
        ("SCC == {B,D}", sccs == [[B, D]]),
        ("alcançáveis de MAIN == 4", alc == {MAIN, B, C, D}),
    ]
    falhas = 0
    for nome, ok in checks:
        if verbose or not ok:
            print(f"  [{'PASS' if ok else 'FAIL'}] {nome}")
        falhas += 0 if ok else 1
    print(f"self-test: {len(checks) - falhas}/{len(checks)} verificações OK")
    return 1 if falhas else 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    script_dir = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-f", "--functions", type=Path,
                    default=script_dir.parent / "functions.csv")
    ap.add_argument("-c", "--callsites", type=Path, default=None)
    ap.add_argument("-o", "--outdir", type=Path, default=script_dir.parent / "callgraph")
    ap.add_argument("--entry", type=lambda s: int(s, 0), default=int(ENTRY_DEFAULT, 16))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.verbose, script_dir.parent / "tests")
    if args.callsites is None or not args.callsites.is_file():
        print("erro: informe o TSV de callsites (-c).", file=sys.stderr)
        return 2
    if not args.functions.is_file():
        print("erro: functions.csv não encontrado (-f).", file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    nos = ler_nos(args.functions)
    pares = ler_callsites(args.callsites)
    g = construir_grafo(nos, pares)
    nome_de = dict(nos)

    sccs = sorted(tarjan_scc(g["nodes_set"], g["adj"]), key=len, reverse=True)
    alc = bfs(args.entry, g["adj"]) if args.entry in g["nodes_set"] else set()

    args.outdir.mkdir(parents=True, exist_ok=True)
    # DOT
    dot_path = args.outdir / "callgraph.dot"
    with dot_path.open("w", encoding="utf-8") as f:
        f.write("digraph callgraph {\n  rankdir=LR; node [fontsize=9];\n")
        for a, nome in nos:
            if nome.startswith("FUN_"):
                f.write(f'  "0x{a:08x}";\n')
            else:
                f.write(f'  "0x{a:08x}" [label="{nome}", style=filled, fillcolor="#ffe9b3"];\n')
        for (c, t), n in g["arestas"].items():
            f.write(f'  "0x{c:08x}" -> "0x{t:08x}" [label="{n}"];\n'
                    if n > 1 else f'  "0x{c:08x}" -> "0x{t:08x}";\n')
        f.write("}\n")
    # arestas TSV
    edges_path = args.outdir / "edges.tsv"
    with edges_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["caller_hex", "caller_nome", "callee_hex", "callee_nome", "peso"])
        for (c, t), n in sorted(g["arestas"].items(), key=lambda kv: -kv[1]):
            w.writerow([f"0x{c:08x}", nome_de.get(c, "?"), f"0x{t:08x}",
                        nome_de.get(t, "?"), n])
    # métricas
    metricas = {
        "versao": VERSAO,
        "nos": len(nos),
        "arestas_diretas_bl": sum(g["arestas"].values()),
        "arestas_unicas": len(g["arestas"]),
        "callsites_para_fora_do_universo": g["externos"],
        "entry_bfs_alcancaveis": len(alc),
        "entry_bfs_pct": round(100 * len(alc) / len(nos), 2) if nos else 0,
        "scc_total": len(sccs),
        "scc_maior_tamanho": len(sccs[0]) if sccs else 0,
        "scc_maior_membros_amostra": [f"0x{a:08x}" for a in sccs[0][:10]] if sccs else [],
        "top_indegree": [
            {"addr": f"0x{a:08x}", "nome": nome_de.get(a, "?"), "chamadas": n}
            for a, n in g["indeg"].most_common(20)],
        "top_outdegree": [
            {"addr": f"0x{a:08x}", "nome": nome_de.get(a, "?"), "callees": n}
            for a, n in g["outdeg"].most_common(20)],
        "AVISO": ("Apenas BL direto. Handlers por tabela/callback/IRQ estão "
                  "sub-representados. BFS≠prova de código morto."),
    }
    mpath = args.outdir / "callgraph_metrics.json"
    mpath.write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"== CALLGRAPH == nós={len(nos)} arestas ÚNICAS={len(g['arestas'])} "
          f"(tot={sum(g['arestas'].values())}) externos_ignorados={g['externos']}")
    print(f"  BFS da entry {hex(args.entry)}: {len(alc)} alcançáveis "
          f"({metricas['entry_bfs_pct']}%) — só BL direto, ver AVISO")
    print(f"  SCCs: {len(sccs)} (maior: {len(sccs[0]) if sccs else 0} nós)")
    print("  top 5 indegree (mais chamadas):")
    for e in metricas["top_indegree"][:5]:
        print(f"    {e['addr']} ×{e['chamadas']:<6} {e['nome']}")
    print("  top 5 outdegree (maiores hubs):")
    for e in metricas["top_outdegree"][:5]:
        print(f"    {e['addr']} →{e['callees']:<6} {e['nome']}")

    logs = script_dir.parent / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "gba_callgraph_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ferramenta": "gba_callgraph.py", "versao": VERSAO,
            "duracao_s": round(time.perf_counter() - t0, 3),
            "saidas": {"dot": str(dot_path), "edges": str(edges_path),
                       "metrics": str(mpath)}}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
