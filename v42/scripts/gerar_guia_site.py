#!/usr/bin/env python3
"""gerar_guia_site.py — guia completo, multipágina, gerado da ROM V42.

Produz um site estático (sem CDN, abre offline) com:

  index.html      visão geral, números da ROM e busca global
  pokemon.html    ficha de cada uma das 1025 espécies:
                    tipos, BST, onde encontrar (dia/noite/evento), evolução,
                    golpes por nível e TMs compatíveis;
  mapas.html      todos os mapas com o que aparece em cada período;
  evolucoes.html  a cadeia completa, com método e condição;
  eventos.html    os eventos fixos preservados e os 7 nativos.

Dados lidos da ROM (tabelas de encontro, slots noturnos) e do motor
(política de horário, eventos fixos, evoluções, learnsets, TMs). A ROM não é
copiada nem distribuída: só dados derivados.

Uso:
  python3 v42/scripts/gerar_guia_site.py --self-test
  COSMOG_V42_ROM=... python3 v42/scripts/gerar_guia_site.py --saida site_guia
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
ROM_ESPERADA = "6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a"

METODOS = {
    1: "amizade", 2: "amizade (dia)", 3: "amizade (noite)", 4: "nível",
    5: "item", 6: "troca", 7: "pedra", 8: "nível (gênero)",
    9: "nível (atk/def)", 10: "nível (PID)", 11: "nível (nature)",
    12: "nível (item)", 13: "nível (invertido)", 14: "nível (item 2)",
    15: "nível (amizade)",
}
METODO_KIND = {"land": "grama/caverna", "water": "surf", "fish": "pesca", "rock": "rock smash"}

# Mapa de tipos confirmado empiricamente contra 12 espécies conhecidas
# (ver --self-test e a auditoria da sessão): 12/12 acertos.
TIPOS = {
    1: "Normal", 2: "Lutador", 3: "Voador", 4: "Veneno", 5: "Terrestre",
    6: "Pedra", 7: "Inseto", 8: "Fantasma", 9: "Aço", 10: "Fogo",
    11: "Água", 12: "Planta", 13: "Elétrico", 14: "Psíquico",
    15: "Gelo", 16: "Dragão", 17: "Sombrio", 18: "Fada",
}

MAPA_NOMES = {
    "MAP_ROUTE1": "Rota 1", "MAP_ROUTE2": "Rota 2", "MAP_ROUTE3": "Rota 3",
    "MAP_ROUTE4": "Rota 4", "MAP_ROUTE22": "Rota 22", "MAP_ROUTE24": "Rota 24",
    "MAP_ROUTE25": "Rota 25", "MAP_VIRIDIAN_FOREST": "Floresta de Viridian",
    "MAP_ROCK_TUNNEL_1F": "Túnel de Pedra 1F", "MAP_ROCK_TUNNEL_B1F": "Túnel de Pedra B1F",
    "MAP_MT_MOON_1F": "Monte Lua 1F", "MAP_CERULEAN_CAVE_1F": "Caverna de Cerulean 1F",
    "MAP_CERULEAN_CAVE_2F": "Caverna de Cerulean 2F",
    "MAP_CERULEAN_CAVE_B1F": "Caverna de Cerulean B1F",
    "MAP_POKEMON_MANSION_1F": "Mansão Pokémon 1F",
    "MAP_SEAFOAM_ISLANDS_1F": "Ilhas Seafoam 1F",
}

EVENTO_NATIVO = {
    144: "Ilhas Seafoam B4F", 145: "Usina Elétrica", 146: "Cume do Monte Ember",
    150: "Caverna de Cerulean B1F", 249: "Navel Rock", 250: "Navel Rock",
    386: "Birth Island",
}


def titulo(nome: str) -> str:
    """Capitaliza como o site faz (bulbasaur -> Bulbasaur), sem tocar em nomes
    compostos: 'mr-mime' -> 'Mr-Mime'."""
    return nome[:1].upper() + nome[1:]


def esc(s) -> str:
    """Escapa HTML — o gerador também injeta texto em página estática."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def bonito(simbolo: str) -> str:
    if simbolo in MAPA_NOMES:
        return MAPA_NOMES[simbolo]
    s = simbolo.replace("MAP_", "").replace("_", " ").title()
    return s.replace("B1F", "B1F").replace("B2F", "B2F")


def achar_motor() -> pathlib.Path:
    env = os.environ.get("GEN19_WORK")
    cands = ([pathlib.Path(env) / "firered_gen1_9"] if env else []) + [
        pathlib.Path("/tmp/gen19/firered_gen1_9")]
    for c in cands:
        if (c / "scripts/encontros_selvagens.py").is_file():
            return c
    raise SystemExit("[ERRO] motor ausente: rode antes bash v42/scripts/run_cosmog_tests.sh")


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def coletar(rom: bytes, gen: pathlib.Path) -> dict:
    sys.path[:0] = [str(gen), str(gen / "scripts")]
    import encontros_selvagens as wild
    from scripts import motor_v40_encontros as h40

    cat = wild.load_species()
    tabelas = wild.parse_tables(rom, wild.load_maps(), cat)

    # ---------- encontros (todos os métodos) ----------
    encontros: dict[int, list[dict]] = {}
    mapas: dict[str, dict] = {}
    for t in tabelas:
        nome = bonito(t.map.symbol)
        m = mapas.setdefault(t.map.symbol, {"nome": nome, "id": t.map.symbol,
                                            "metodos": set(), "slots": []})
        m["metodos"].add(t.kind)
        for s in t.slots:
            m["slots"].append({"especie": s.species, "metodo": METODO_KIND.get(t.kind, t.kind),
                               "nivel_min": s.min_level, "nivel_max": s.max_level,
                               "chance": s.chance, "periodo": "dia"})
            encontros.setdefault(s.species, []).append({
                "mapa": nome, "mapa_id": t.map.symbol,
                "metodo": METODO_KIND.get(t.kind, t.kind),
                "nivel_min": s.min_level, "nivel_max": s.max_level,
                "chance": s.chance, "periodo": "dia",
            })

    # ---------- dia/noite (68 mapas piloto) ----------
    horario: dict[int, list[dict]] = {}
    politica = h40.policy_rows()
    land = {t.map.symbol: t for t in tabelas if t.kind == "land"}
    TO, MAPS = h40.TABLE_OFFSET, h40.MAPS
    off = TO + 12 * len(MAPS)
    for i, nome_id in enumerate(MAPS):
        t = land.get(nome_id)
        for r in [x for x in politica if x["map_symbol"] == nome_id]:
            slot = r["slot"]
            lo, hi, sp = struct.unpack_from("<BBH", rom, off + 8 + slot * 4)
            chance = t.slots[slot].chance if t else None
            nome = bonito(nome_id)
            horario.setdefault(sp, []).append({
                "mapa": nome, "mapa_id": nome_id, "metodo": "grama/caverna",
                "nivel_min": lo, "nivel_max": hi, "chance": chance, "periodo": "noite"})
            if t:
                d = t.slots[slot]
                horario.setdefault(d.species, []).append({
                    "mapa": nome, "mapa_id": nome_id, "metodo": "grama/caverna",
                    "nivel_min": d.min_level, "nivel_max": d.max_level,
                    "chance": d.chance, "periodo": "dia"})
            if nome_id in mapas:
                mapas[nome_id]["slots"].append({
                    "especie": sp, "metodo": "grama/caverna", "nivel_min": lo,
                    "nivel_max": hi, "chance": chance, "periodo": "noite"})
        off += 56

    # ---------- eventos fixos ----------
    fixos: dict[int, list[dict]] = {}
    for r in csv.DictReader((gen / "docs/eventos_fixos_inventario.csv").open()):
        if "retirado" in r["situacao_fixo"]:
            continue
        fixos.setdefault(int(r["pokedex_nacional"]), []).append({
            "mapa": r["mapa_fixo"], "nivel": int(r["nivel_min"] or 0),
            "categoria": r["categoria"]})

    # ---------- evoluções ----------
    evolui_para: dict[int, list[dict]] = {}
    evolucoes = []
    for r in csv.DictReader((gen / "docs/evolucoes_v40.csv").open()):
        s, t = int(r["source"]), int(r["target"])
        metodo = METODOS.get(int(r["method"]), f"método {r['method']}")
        item = {"para": t, "para_nome": cat[t].name, "metodo": metodo,
                "param": r["param"] or ""}
        evolui_para.setdefault(s, []).append(item)
        evolucoes.append({"de": s, "de_nome": cat[s].name, "para": t,
                          "para_nome": cat[t].name, "metodo": metodo,
                          "param": r["param"] or ""})

    # ---------- golpes por nível ----------
    golpes: dict[int, list[dict]] = {}
    for r in csv.DictReader((gen / "data/learnsets_gen1_9_atualizados.csv").open()):
        try:
            sid, lvl = int(r["species"]), int(r["level"] or 0)
        except ValueError:
            continue
        golpes.setdefault(sid, []).append({"nivel": lvl, "golpe": r["name"]})
    for sid in golpes:
        golpes[sid].sort(key=lambda x: (x["nivel"], x["golpe"]))

    # ---------- TMs ----------
    tms = [{"numero": r["tm"], "golpe": r["name"], "status": r["status"]}
           for r in csv.DictReader((gen / "data/tms_gen9.csv").open())]

    pokemon = []
    for sid in sorted(cat):
        sp = cat[sid]
        tipos = [TIPOS[t] for t in (sp.types or ()) if t in TIPOS]
        pokemon.append({
            "id": sid, "nome": sp.name, "geracao": sp.generation,
            "tipos": tipos, "bst": sp.base_stat_total,
            "lendario": bool(sp.legendary), "mitico": bool(sp.mythical),
            "evolui_de": sp.evolves_from,
            "evolui_para": evolui_para.get(sid, []),
            "encontros": encontros.get(sid, []),
            "horario": horario.get(sid, []),
            "fixos": fixos.get(sid, []),
            "evento_nativo": EVENTO_NATIVO.get(sid),
            "golpes": golpes.get(sid, [])[:80],
            "n_golpes": len(golpes.get(sid, [])),
        })

    lista_mapas = []
    for m in mapas.values():
        lista_mapas.append({"id": m["id"], "nome": m["nome"],
                            "metodos": sorted(METODO_KIND.get(k, k) for k in m["metodos"]),
                            "slots": m["slots"]})
    lista_mapas.sort(key=lambda x: x["nome"])

    return {
        "rom_sha256": ROM_ESPERADA,
        "gerado_por": "v42/scripts/gerar_guia_site.py",
        "total": len(pokemon),
        "total_mapas": len(lista_mapas),
        "total_golpes": sum(p["n_golpes"] for p in pokemon),
        "pokemon": pokemon,
        "mapas": lista_mapas,
        "evolucoes": evolucoes,
        "tms": tms,
    }


CSS = """
:root{--bg:#0f1218;--card:#171c26;--card2:#1e2430;--txt:#e7ecf5;--dim:#9aa7bd;
      --acc:#5ac8fa;--dia:#ffd166;--noite:#8b9dff;--ok:#4ade80;--warn:#fbbf24}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
     background:var(--bg);color:var(--txt)}
header{padding:16px 18px;border-bottom:1px solid #263040;background:#121721;
       position:sticky;top:0;z-index:10}
h1{margin:0 0 2px;font-size:19px}
h1 small{color:var(--dim);font-weight:400;font-size:13px}
nav{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
nav a{color:var(--dim);text-decoration:none;padding:6px 12px;border-radius:8px;
      background:var(--card2);font-size:13px}
nav a:hover{color:var(--txt)}
nav a.on{background:var(--acc);color:#06222e;font-weight:600}
.wrap{max-width:1150px;margin:0 auto;padding:18px}
.sub{color:var(--dim);font-size:13px}
.controles{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
input,select{background:var(--card2);border:1px solid #2d3644;color:var(--txt);
             padding:9px 11px;border-radius:8px;font-size:14px}
input{flex:1;min-width:220px}
input:focus,select:focus{outline:2px solid var(--acc);outline-offset:-1px}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.card{background:var(--card);border:1px solid #263040;border-radius:12px;padding:14px}
.card h3{margin:0 0 2px;font-size:16px;display:flex;gap:8px;align-items:baseline;
         flex-wrap:wrap}
.num{color:var(--dim);font-size:13px;font-weight:400}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.tag{font-size:11px;padding:2px 8px;border-radius:999px;background:#232b3a;color:var(--dim)}
.tag.lend{background:#3a2430;color:#ff9db1}
.tag.mit{background:#2f2440;color:#c9a6ff}
.tag.g{background:#1c3340;color:#79d0ef}
.tag.t{background:#22303c;color:#9fd8ff}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
th,td{text-align:left;padding:5px 6px;border-bottom:1px solid #232b3a;vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:12px;text-transform:uppercase;
   letter-spacing:.03em}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.dia{color:var(--dia)} .noite{color:var(--noite)}
.metodo{color:var(--dim);font-size:12px}
.vazio{color:var(--dim);font-style:italic;font-size:13px}
.nota{background:#1a2130;border-left:3px solid var(--warn);padding:10px 12px;
      border-radius:6px;color:var(--dim);font-size:13px;margin:14px 0}
.contador{color:var(--dim);font-size:13px;margin:14px 0 6px}
details summary{cursor:pointer;color:var(--acc);font-size:13px;margin-top:8px}
.evo{font-size:13px;color:var(--dim);margin:2px 0}
.evo b{color:var(--txt);font-weight:600}
.golpes{max-height:190px;overflow:auto;margin-top:6px;font-size:12.5px;color:var(--dim)}
.golpes span{display:inline-block;margin:2px 4px 2px 0;padding:1px 7px;
             background:#202836;border-radius:6px}
.kpis{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
      margin:16px 0}
.kpi{background:var(--card);border:1px solid #263040;border-radius:12px;padding:14px}
.kpi b{display:block;font-size:24px;line-height:1.1}
.kpi span{color:var(--dim);font-size:12px}
footer{color:var(--dim);font-size:12px;padding:22px 18px;text-align:center;
       border-top:1px solid #263040;margin-top:30px}
a{color:var(--acc)}
code{background:#202836;padding:1px 5px;border-radius:4px;font-size:12px}
"""

NAV = """<nav>
<a href="index.html" __ON_index>Visão geral</a>
<a href="pokemon.html" __ON_pokemon>Pokémon</a>
<a href="mapas.html" __ON_mapas>Mapas</a>
<a href="evolucoes.html" __ON_evolucoes>Evoluções</a>
<a href="eventos.html" __ON_eventos>Eventos</a>
</nav>"""


def pagina(titulo: str, ativo: str, corpo: str, extra_js: str = "", dados: str = "null",
           sha: str = ROM_ESPERADA) -> str:
    nav = NAV
    for p in ("index", "pokemon", "mapas", "evolucoes", "eventos"):
        nav = nav.replace(f"__ON_{p}", 'class="on"' if p == ativo else "")
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} — Guia FireRed Gen 1–9 (V42)</title>
<style>{CSS}</style></head>
<body>
<header><h1>{titulo} <small>FireRed Gen 1–9 · V42</small></h1>{nav}</header>
<div class="wrap">
{corpo}
</div>
<footer>
Gerado de <code>{sha}</code> por <code>v42/scripts/gerar_guia_site.py</code>.<br>
Cobertura estrutural: não prova que todo tile é alcançável em toda etapa da
história, nem que cada espécie foi capturada em jogo.
</footer>
<script>const DADOS = {dados};</script>
<script>{extra_js}</script>
</body></html>"""


JS_COMUM = """
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const titulo = s => esc(s).replace(/\\b\\w/g, c => c.toUpperCase());
const POR_ID = new Map(DADOS.pokemon.map(p => [p.id, p]));
const perTag = p => p === 'noite' ? '<span class="noite">noite</span>'
  : p === 'dia' ? '<span class="dia">dia</span>'
  : '<span style="color:var(--dim)">sempre</span>';
"""


def gerar_index(d: dict) -> str:
    vivos = sum(1 for p in d["pokemon"] if p["encontros"] or p["horario"])
    fixos = sum(1 for p in d["pokemon"] if p["fixos"])
    nat = sum(1 for p in d["pokemon"] if p["evento_nativo"])
    corpo = f"""
<div class="kpis">
  <div class="kpi"><b>{d['total']}</b><span>espécies</span></div>
  <div class="kpi"><b>{d['total_mapas']}</b><span>mapas com tabela</span></div>
  <div class="kpi"><b>{d['total_golpes']}</b><span>golpes por nível</span></div>
  <div class="kpi"><b>{len(d['evolucoes'])}</b><span>ligações de evolução</span></div>
  <div class="kpi"><b>{len(d['tms'])}</b><span>TMs mapeadas</span></div>
</div>
<div class="nota">
  <b>Como as espécies são obtidas.</b> {vivos} aparecem em tabela de encontro,
  {fixos} em evento fixo e {nat} em evento nativo (lendários de história).
  Somando os caminhos, as 1025 têm pelo menos uma forma de obtenção.
</div>
<div class="controles">
  <input id="q" placeholder="Buscar espécie por nome ou nº…" autocomplete="off">
</div>
<div class="contador" id="contador"></div>
<div class="grid" id="lista"></div>
"""
    js = JS_COMUM + """
const lista = document.getElementById('lista');
const q = document.getElementById('q');
const contador = document.getElementById('contador');

function resumo(p) {
  const o = [...p.horario, ...p.encontros];
  if (o.length) {
    const n = new Set(o.map(x => x.mapa)).size;
    return `aparece em ${n} mapa${n > 1 ? 's' : ''}`;
  }
  if (p.fixos.length) return `evento fixo em ${esc(p.fixos[0].mapa)}`;
  if (p.evento_nativo) return `evento nativo — ${esc(p.evento_nativo)}`;
  if (p.evolui_de) return `evolui de #${p.evolui_de}`;
  return 'caminho especial';
}

function card(p) {
  const tags = [`<span class="tag g">Gen ${p.geracao}</span>`];
  for (const t of p.tipos) tags.push(`<span class="tag t">${esc(t)}</span>`);
  if (p.lendario) tags.push('<span class="tag lend">lendário</span>');
  if (p.mitico) tags.push('<span class="tag mit">mítico</span>');
  return `<div class="card"><h3>${titulo(p.nome)} <span class="num">#${p.id}</span></h3>
    <div class="tags">${tags.join('')}</div>
    <div class="sub">${resumo(p)}</div></div>`;
}

function render() {
  const t = q.value.trim().toLowerCase();
  const out = [];
  let n = 0;
  for (const p of DADOS.pokemon) {
    if (t && !(p.nome.toLowerCase().includes(t) || String(p.id) === t ||
               String(p.id).padStart(3,'0') === t)) continue;
    n++;
    if (out.length < 60) out.push(card(p));
  }
  lista.innerHTML = out.join('');
  contador.textContent = `${n} de ${DADOS.total} espécies` +
    (n > 60 ? ' — mostrando 60; refine a busca' : '');
}
q.addEventListener('input', render);
render();
"""
    return pagina("Visão geral", "index", corpo, js, json.dumps(
        {"total": d["total"], "pokemon": [
            {"id": p["id"], "nome": p["nome"], "geracao": p["geracao"],
             "tipos": p["tipos"], "lendario": p["lendario"], "mitico": p["mitico"],
             "encontros": p["encontros"][:1], "horario": p["horario"][:1],
             "fixos": p["fixos"][:1], "evento_nativo": p["evento_nativo"],
             "evolui_de": p["evolui_de"], "evolui_para": p["evolui_para"]}
            for p in d["pokemon"]]}, ensure_ascii=False, separators=(",", ":")))


JS_POKEMON = JS_COMUM + """
const lista = document.getElementById('lista');
const contador = document.getElementById('contador');
const q = document.getElementById('q');
const fGer = document.getElementById('ger');
const fRaros = document.getElementById('raros');
const fMet = document.getElementById('metodo');

function ocorrencias(p) {
  const out = [];
  const vistos = new Set();
  for (const e of p.horario) { out.push(e); vistos.add(e.mapa_id + e.metodo + e.periodo); }
  for (const e of p.encontros) {
    if (vistos.has(e.mapa_id + e.metodo + e.periodo)) continue;
    out.push(e);
  }
  for (const f of p.fixos) out.push({mapa: f.mapa, mapa_id: f.mapa,
    metodo: 'evento fixo', periodo: 'sempre', nivel_min: f.nivel,
    nivel_max: f.nivel, chance: null});
  if (p.evento_nativo) out.push({mapa: p.evento_nativo, mapa_id: 'nativo',
    metodo: 'evento nativo', periodo: 'sempre', nivel_min: null,
    nivel_max: null, chance: null});
  return out;
}

function tabelaOcorrencias(occ) {
  if (!occ.length) return '<div class="vazio">Sem encontro selvagem.</div>';
  const ord = occ.slice().sort((a,b) => (b.chance ?? 0) - (a.chance ?? 0)).slice(0, 12);
  const linhas = ord.map(o => {
    const nv = o.nivel_min == null ? '—'
      : (o.nivel_min === o.nivel_max ? o.nivel_min : o.nivel_min + '–' + o.nivel_max);
    const ch = o.chance == null ? '—' : o.chance + '%';
    return `<tr><td>${esc(o.mapa)}<div class="metodo">${esc(o.metodo)}</div></td>
      <td>${perTag(o.periodo)}</td><td class="n">${nv}</td><td class="n">${ch}</td></tr>`;
  }).join('');
  return `<table><thead><tr><th>Onde</th><th>Período</th><th>Nível</th><th>Chance</th></tr></thead>
    <tbody>${linhas}</tbody></table>`;
}

function blocoEvolucao(p) {
  const l = [];
  if (p.evolui_de) {
    const de = POR_ID.get(p.evolui_de);
    l.push(`<div class="evo">vem de <b>${de ? esc(de.nome) : '#' + p.evolui_de}</b></div>`);
  }
  for (const e of p.evolui_para) {
    const cond = (e.metodo === 'nível' && e.param) ? `nível ${e.param}` : esc(e.metodo);
    l.push(`<div class="evo">evolui para <b>${esc(e.para_nome)}</b> — ${cond}</div>`);
  }
  return l.length ? `<details><summary>Evolução</summary>${l.join('')}</details>` : '';
}

function blocoGolpes(p) {
  if (!p.golpes || !p.golpes.length) return '';
  const chips = p.golpes.map(g => `<span>${esc(g.golpe)} <b>${g.nivel}</b></span>`).join('');
  return `<details><summary>Golpes por nível (${p.n_golpes})</summary>
    <div class="golpes">${chips}</div></details>`;
}

function card(p) {
  const tags = [`<span class="tag g">Gen ${p.geracao}</span>`];
  for (const t of p.tipos) tags.push(`<span class="tag t">${esc(t)}</span>`);
  if (p.lendario) tags.push('<span class="tag lend">lendário</span>');
  if (p.mitico) tags.push('<span class="tag mit">mítico</span>');
  return `<div class="card"><h3>${titulo(p.nome)} <span class="num">#${p.id}</span>
      <span class="num">BST ${p.bst}</span></h3>
    <div class="tags">${tags.join('')}</div>
    ${tabelaOcorrencias(ocorrencias(p))}
    ${blocoEvolucao(p)}${blocoGolpes(p)}</div>`;
}

function casa(p, occ) {
  const t = q.value.trim().toLowerCase();
  if (t && !(p.nome.toLowerCase().includes(t) || String(p.id) === t ||
             String(p.id).padStart(3,'0') === t)) return false;
  if (fGer.value && String(p.geracao) !== fGer.value) return false;
  if (fRaros.value === 'lendario' && !(p.lendario || p.mitico)) return false;
  if (fRaros.value === 'comum' && (p.lendario || p.mitico)) return false;
  if (fMet.value && !occ.some(o => o.metodo === fMet.value)) return false;
  return true;
}

function render() {
  const out = [];
  let n = 0;
  for (const p of DADOS.pokemon) {
    const occ = ocorrencias(p);
    if (!casa(p, occ)) continue;
    n++;
    if (out.length < 40) out.push(card(p));
  }
  lista.innerHTML = out.join('');
  contador.textContent = `${n} de ${DADOS.total} espécies` +
    (n > 40 ? ' — mostrando 40; refine a busca' : '');
}
for (const el of [q, fGer, fRaros, fMet]) el.addEventListener('input', render);
render();
"""


def gerar_pokemon(d: dict) -> str:
    corpo = """
<div class="nota">
  <code>chance</code> é o peso do slot depois que um encontro acontece — não é
  chance por passo. <b>Dia</b> 06:00–19:59, <b>noite</b> 20:00–05:59.
</div>
<div class="controles">
  <input id="q" placeholder="Buscar por nome ou nº da Pokédex…" autocomplete="off">
  <select id="metodo">
    <option value="">Todos os métodos</option>
    <option value="grama/caverna">Grama / caverna</option>
    <option value="surf">Surf</option>
    <option value="pesca">Pesca</option>
    <option value="rock smash">Rock Smash</option>
    <option value="evento fixo">Evento fixo</option>
    <option value="evento nativo">Evento nativo</option>
  </select>
  <select id="ger"><option value="">Todas as gerações</option>
    <option>1</option><option>2</option><option>3</option><option>4</option>
    <option>5</option><option>6</option><option>7</option><option>8</option>
    <option>9</option></select>
  <select id="raros"><option value="">Todos</option>
    <option value="comum">Só comuns</option>
    <option value="lendario">Lendários / míticos</option></select>
</div>
<div class="contador" id="contador"></div>
<div class="grid" id="lista"></div>
"""
    # DADOS PRECISA ser um objeto com .pokemon: o JS usa DADOS.pokemon e
    # DADOS.total. A primeira versão passava a lista crua e a página ficava em
    # branco ('Cannot read properties of undefined') — o teste de render pegou.
    dados = {"total": d["total"], "pokemon": d["pokemon"]}
    return pagina("Pokémon", "pokemon", corpo, JS_POKEMON,
                  json.dumps(dados, ensure_ascii=False, separators=(",", ":")))


JS_MAPAS = JS_COMUM + """
const lista = document.getElementById('lista');
const contador = document.getElementById('contador');
const q = document.getElementById('q');
const fPer = document.getElementById('per');

function render() {
  const t = q.value.trim().toLowerCase();
  const out = [];
  let n = 0;
  for (const m of DADOS.mapas) {
    if (t && !m.nome.toLowerCase().includes(t)) continue;
    n++;
    if (out.length >= 40) continue;
    let slots = m.slots;
    if (fPer.value) slots = slots.filter(s => s.periodo === fPer.value);
    const ord = slots.slice().sort((a,b) => (b.chance ?? 0) - (a.chance ?? 0));
    const linhas = ord.slice(0, 30).map(s => {
      const p = POR_ID.get(s.especie);
      const nv = s.nivel_min === s.nivel_max ? s.nivel_min : s.nivel_min + '–' + s.nivel_max;
      return `<tr><td>${p ? titulo(p.nome) : '#' + s.especie}</td>
        <td>${perTag(s.periodo)}</td>
        <td class="metodo">${esc(s.metodo)}</td>
        <td class="n">${nv}</td><td class="n">${s.chance ?? '—'}%</td></tr>`;
    }).join('');
    out.push(`<div class="card"><h3>${esc(m.nome)}</h3>
      <div class="tags">${m.metodos.map(x => `<span class="tag">${esc(x)}</span>`).join('')}</div>
      <table><thead><tr><th>Espécie</th><th>Período</th><th>Método</th>
      <th>Nível</th><th>Chance</th></tr></thead><tbody>${linhas}</tbody></table></div>`);
  }
  lista.innerHTML = out.join('');
  contador.textContent = `${n} mapas` + (n > 40 ? ' — mostrando 40; refine' : '');
}
for (const el of [q, fPer]) el.addEventListener('input', render);
render();
"""


def gerar_mapas(d: dict) -> str:
    corpo = """
<div class="nota">Cada mapa lista os slots gravados na ROM. O mesmo mapa pode ter
períodos diferentes: a noite substitui apenas dois slots.</div>
<div class="controles">
  <input id="q" placeholder="Buscar mapa…" autocomplete="off">
  <select id="per"><option value="">Dia e noite</option>
    <option value="dia">Só dia</option><option value="noite">Só noite</option></select>
</div>
<div class="contador" id="contador"></div>
<div class="grid" id="lista"></div>
"""
    dados = {"mapas": d["mapas"],
             "pokemon": [{"id": p["id"], "nome": p["nome"]} for p in d["pokemon"]]}
    return pagina("Mapas", "mapas", corpo, JS_MAPAS,
                  json.dumps(dados, ensure_ascii=False, separators=(",", ":")))


JS_EVOLUCOES = JS_COMUM + """
const lista = document.getElementById('lista');
const contador = document.getElementById('contador');
const q = document.getElementById('q');

function render() {
  const t = q.value.trim().toLowerCase();
  const grupos = new Map();
  for (const e of DADOS.evolucoes) {
    if (t && !(e.de_nome.toLowerCase().includes(t) || e.para_nome.toLowerCase().includes(t))) continue;
    if (!grupos.has(e.de)) grupos.set(e.de, []);
    grupos.get(e.de).push(e);
  }
  const out = [];
  for (const [de, itens] of grupos) {
    const linhas = itens.map(e => {
      const cond = (e.metodo === 'nível' && e.param) ? `nível ${e.param}` : esc(e.metodo);
      return `<tr><td>${titulo(e.para_nome)} <span class="num">#${e.para}</span></td>
        <td>${cond}</td></tr>`;
    }).join('');
    out.push(`<div class="card"><h3>${titulo(itens[0].de_nome)}
      <span class="num">#${de}</span></h3>
      <table><thead><tr><th>Evolui para</th><th>Condição</th></tr></thead>
      <tbody>${linhas}</tbody></table></div>`);
  }
  lista.innerHTML = out.join('');
  contador.textContent = `${grupos.size} espécies que evoluem · ${DADOS.evolucoes.length} ligações`;
}
q.addEventListener('input', render);
render();
"""


def gerar_evolucoes(d: dict) -> str:
    corpo = """
<div class="nota">Inclui as duas únicas evoluções por horário da ROM:
Eevee → Espeon (dia) e Eevee → Umbreon (noite), ambas com amizade ≥ 220.</div>
<div class="controles">
  <input id="q" placeholder="Buscar por espécie (origem ou destino)…" autocomplete="off">
</div>
<div class="contador" id="contador"></div>
<div class="grid" id="lista"></div>
"""
    dados = {"evolucoes": d["evolucoes"],
             "pokemon": [{"id": p["id"], "nome": p["nome"]} for p in d["pokemon"]]}
    return pagina("Evoluções", "evolucoes", corpo, JS_EVOLUCOES,
                  json.dumps(dados, ensure_ascii=False, separators=(",", ":")))


def gerar_eventos(d: dict) -> str:
    fixos = [p for p in d["pokemon"] if p["fixos"]]
    fixos.sort(key=lambda p: p["fixos"][0]["mapa"])
    linhas = "".join(
        f"<tr><td>{titulo(p['nome'])} <span class='num'>#{p['id']}</span></td>"
        f"<td>{esc(p['fixos'][0]['mapa'])}</td>"
        f"<td class='n'>{p['fixos'][0]['nivel']}</td>"
        f"<td class='metodo'>{esc(p['fixos'][0]['categoria'])}</td></tr>"
        for p in fixos)
    nativos = [p for p in d["pokemon"] if p["evento_nativo"]]
    lin_nat = "".join(
        f"<tr><td>{titulo(p['nome'])} <span class='num'>#{p['id']}</span></td>"
        f"<td>{esc(p['evento_nativo'])}</td>"
        f"<td class='metodo'>{'mítico' if p['mitico'] else 'lendário'}</td></tr>"
        for p in nativos)
    corpo = f"""
<div class="nota">Os <b>{len(fixos)}</b> eventos fixos abaixo foram preservados
pelo motor; outros 224 foram <b>retirados do mapa</b>, com as espécies
reacomodadas em tabelas de encontro (nenhuma ficou órfã).</div>
<div class="card"><h3>Eventos fixos preservados ({len(fixos)})</h3>
<table><thead><tr><th>Espécie</th><th>Mapa</th><th>Nível</th><th>Categoria</th></tr></thead>
<tbody>{linhas}</tbody></table></div>
<div class="card" style="margin-top:12px"><h3>Eventos nativos do FireRed ({len(nativos)})</h3>
<table><thead><tr><th>Espécie</th><th>Local</th><th>Tipo</th></tr></thead>
<tbody>{lin_nat}</tbody></table></div>
"""
    return pagina("Eventos", "eventos", corpo, "", "null",
                  ROM_ESPERADA)


def main() -> int:
    if "--self-test" in sys.argv:
        ok = True
        # 1) mapa de tipos: 12 espécies conhecidas
        sys.path[:0] = [str(ROOT / "v42/scripts")]
        esperado = {"bulbasaur": (12, 4), "charmander": (10, 0), "squirtle": (11, 0),
                    "pikachu": (13, 0), "gengar": (8, 4), "onix": (6, 5),
                    "scyther": (7, 3), "gyarados": (11, 3), "dratini": (16, 0),
                    "umbreon": (17, 0), "magnemite": (13, 9), "snubbull": (18, 0)}
        nomes = {"bulbasaur": ("Planta", "Veneno"), "charmander": ("Fogo", None),
                 "squirtle": ("Água", None), "pikachu": ("Elétrico", None),
                 "gengar": ("Fantasma", "Veneno"), "onix": ("Pedra", "Terrestre"),
                 "scyther": ("Inseto", "Voador"), "gyarados": ("Água", "Voador"),
                 "dratini": ("Dragão", None), "umbreon": ("Sombrio", None),
                 "magnemite": ("Elétrico", "Aço"), "snubbull": ("Fada", None)}
        for nome, (t1, t2) in esperado.items():
            obtido = (TIPOS[t1], TIPOS[t2] if t2 else None)
            bom = obtido == nomes[nome]
            ok &= bom
            print(f"  [{'PASS' if bom else 'FAIL'}] {nome}: {obtido} (esperado {nomes[nome]})")
        # 2) bonito()
        for s in ("MAP_ROUTE1", "MAP_CERULEAN_CAVE_B1F", "MAP_ALGO_NOVO_2F"):
            r = bonito(s)
            bom = bool(r) and "MAP_" not in r
            ok &= bom
            print(f"  [{'PASS' if bom else 'FAIL'}] {s} -> {r}")
        print(f"\nresumo: {'OK' if ok else '1 falha(s)'}")
        return 0 if ok else 1

    rom_env = os.environ.get("COSMOG_V42_ROM", "")
    if not rom_env or not pathlib.Path(rom_env).is_file():
        print("[ERRO] defina COSMOG_V42_ROM")
        return 2
    rom_path = pathlib.Path(rom_env)
    if sha256(rom_path) != ROM_ESPERADA:
        print("[ERRO] não é a V42 exata")
        return 2

    saida = pathlib.Path(sys.argv[sys.argv.index("--saida") + 1]) if "--saida" in sys.argv \
        else ROOT / "site_guia"
    saida.mkdir(parents=True, exist_ok=True)

    gen = achar_motor()
    d = coletar(rom_path.read_bytes(), gen)

    paginas = {
        "index.html": gerar_index(d),
        "pokemon.html": gerar_pokemon(d),
        "mapas.html": gerar_mapas(d),
        "evolucoes.html": gerar_evolucoes(d),
        "eventos.html": gerar_eventos(d),
    }
    for nome, html in paginas.items():
        (saida / nome).write_text(html, encoding="utf-8")
        print(f"[site] {nome:<16} {len(html)/1024:6.0f} KB")

    (saida / "dados.json").write_text(json.dumps(
        {k: d[k] for k in ("rom_sha256", "gerado_por", "total", "total_mapas",
                           "total_golpes", "pokemon", "mapas", "evolucoes", "tms")},
        ensure_ascii=False))
    print(f"[site] dados.json       {(saida/'dados.json').stat().st_size/1024:6.0f} KB")
    print(f"[site] {d['total']} espécies · {d['total_mapas']} mapas · "
          f"{d['total_golpes']} golpes · {len(d['evolucoes'])} evoluções")
    return 0


if __name__ == "__main__":
    sys.exit(main())
