#!/usr/bin/env python3
"""gerar_guia_site.py — gera um guia HTML navegável da ROM V42.

Lê os dados DIRETO da ROM (tabelas de encontro) e do motor (política de horário,
eventos fixos, evoluções), e produz um site estático autocontido:

  * busca por Pokémon (nome ou número da Pokédex);
  * onde encontrar, com método, níveis e chance por encontro;
  * variação dia/noite por mapa;
  * como evoluir (método, nível, condição);
  * eventos fixos preservados;
  * filtros: geração, lendário, método.

Nada de CDN: um único arquivo HTML + um JSON, para abrir offline e funcionar no
preview. A ROM não é copiada nem distribuída — só os dados derivados.

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

# Nomes de mapa legíveis (o motor usa simbolos internos)
MAPA_NOMES = {
    "MAP_ROUTE1": "Rota 1", "MAP_ROUTE2": "Rota 2", "MAP_ROUTE3": "Rota 3",
    "MAP_ROUTE4": "Rota 4", "MAP_ROUTE22": "Rota 22", "MAP_ROUTE24": "Rota 24",
    "MAP_ROUTE25": "Rota 25", "MAP_VIRIDIAN_FOREST": "Floresta de Viridian",
    "MAP_ROCK_TUNNEL_1F": "Túnel de Pedra 1F", "MAP_ROCK_TUNNEL_B1F": "Túnel de Pedra B1F",
    "MAP_MT_MOON_1F": "Monte Lua 1F", "MAP_CERULEAN_CAVE_1F": "Caverna de Cerulean 1F",
    "MAP_CERULEAN_CAVE_2F": "Caverna de Cerulean 2F", "MAP_CERULEAN_CAVE_B1F": "Caverna de Cerulean B1F",
    "MAP_POKEMON_MANSION_1F": "Mansão Pokémon 1F", "MAP_SEAFOAM_ISLANDS_1F": "Ilhas Seafoam 1F",
}


def bonito(simbolo: str) -> str:
    """MAP_ROUTE1 -> Rota 1 (ou nome conhecido; senão humaniza)."""
    if simbolo in MAPA_NOMES:
        return MAPA_NOMES[simbolo]
    s = simbolo.replace("MAP_", "").replace("_", " ").title()
    return (s.replace("B1F", "B1F").replace("1F", "1F").replace("2F", "2F")
             .replace("3F", "3F").replace("4F", "4F"))


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
    """Monta o dicionário de dados que o site consome."""
    sys.path[:0] = [str(gen), str(gen / "scripts")]
    import encontros_selvagens as wild
    from scripts import motor_v40_encontros as h40

    cat = wild.load_species()
    mapas_spec = wild.load_maps()
    tabelas = wild.parse_tables(rom, mapas_spec, cat)

    # mapa simbolo -> metodos presentes
    metodos_mapa: dict[str, set[str]] = {}
    for t in tabelas:
        metodos_mapa.setdefault(t.map.symbol, set()).add(t.kind)

    # ---- encontros (dia) ----
    encontros: dict[int, list[dict]] = {}
    for t in tabelas:
        for s in t.slots:
            encontros.setdefault(s.species, []).append({
                "mapa": bonito(t.map.symbol),
                "mapa_id": t.map.symbol,
                "metodo": METODO_KIND.get(t.kind, t.kind),
                "nivel_min": s.min_level,
                "nivel_max": s.max_level,
                "chance": s.chance,
                "periodo": "dia",
            })

    # ---- política dia/noite (68 mapas piloto) ----
    horario: dict[int, list[dict]] = {}
    politica = h40.policy_rows()
    tabelas_land = {t.map.symbol: t for t in tabelas if t.kind == "land"}
    # slots noturnos gravados na V42
    TO, MAPS = h40.TABLE_OFFSET, h40.MAPS
    off = TO + 12 * len(MAPS)
    noturnos: dict[str, dict[int, int]] = {}
    niveis_noturnos: dict[str, dict[int, tuple[int, int]]] = {}
    for i, nome in enumerate(MAPS):
        d = {}
        nv = {}
        for r in [x for x in politica if x["map_symbol"] == nome]:
            lo, hi, sp = struct.unpack_from("<BBH", rom, off + 8 + r["slot"] * 4)
            d[r["slot"]] = sp
            nv[r["slot"]] = (lo, hi)
        noturnos[nome] = d
        niveis_noturnos[nome] = nv
        off += 56

    for nome in MAPS:
        t = tabelas_land.get(nome)
        if not t:
            continue
        for slot, sp in noturnos[nome].items():
            lo, hi = niveis_noturnos[nome][slot]
            chance = t.slots[slot].chance
            horario.setdefault(sp, []).append({
                "mapa": bonito(nome), "mapa_id": nome, "metodo": "grama/caverna",
                "nivel_min": lo, "nivel_max": hi, "chance": chance, "periodo": "noite",
            })
            diurno = t.slots[slot].species
            horario.setdefault(diurno, []).append({
                "mapa": bonito(nome), "mapa_id": nome, "metodo": "grama/caverna",
                "nivel_min": t.slots[slot].min_level, "nivel_max": t.slots[slot].max_level,
                "chance": chance, "periodo": "dia",
            })

    # ---- eventos fixos ----
    fixos: dict[int, list[dict]] = {}
    inv = list(csv.DictReader((gen / "docs/eventos_fixos_inventario.csv").open()))
    for r in inv:
        if "retirado" in r["situacao_fixo"]:
            continue
        sid = int(r["pokedex_nacional"])
        fixos.setdefault(sid, []).append({
            "mapa": r["mapa_fixo"], "nivel": r["nivel_min"], "categoria": r["categoria"],
        })

    # ---- evoluções ----
    evo = list(csv.DictReader((gen / "docs/evolucoes_v40.csv").open()))
    evolui_para: dict[int, list[dict]] = {}
    for r in evo:
        s, t = int(r["source"]), int(r["target"])
        evolui_para.setdefault(s, []).append({
            "para": t, "para_nome": cat[t].name,
            "metodo": METODOS.get(int(r["method"]), f"método {r['method']}"),
            "param": r["param"] or "",
        })

    EVENTO_NATIVO = {144: "Ilhas Seafoam B4F", 145: "Usina Elétrica",
                     146: "Cume do Monte Ember", 150: "Caverna de Cerulean B1F",
                     249: "Navel Rock", 250: "Navel Rock", 386: "Birth Island"}

    pokemon = []
    for sid in sorted(cat):
        sp = cat[sid]
        pokemon.append({
            "id": sid,
            "nome": sp.name,
            "geracao": sp.generation,
            "lendario": bool(sp.legendary),
            "mitico": bool(sp.mythical),
            "bst": sp.base_stat_total,
            "evolui_de": sp.evolves_from,
            "evolui_para": evolui_para.get(sid, []),
            "encontros": encontros.get(sid, []),
            "horario": horario.get(sid, []),
            "fixos": fixos.get(sid, []),
            "evento_nativo": EVENTO_NATIVO.get(sid),
        })

    return {
        "rom_sha256": ROM_ESPERADA,
        "gerado_por": "v42/scripts/gerar_guia_site.py",
        "total": len(pokemon),
        "pokemon": pokemon,
    }


HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Guia — FireRed Gen 1–9 (V42)</title>
<style>
  :root{--bg:#0f1218;--card:#171c26;--card2:#1e2430;--txt:#e7ecf5;--dim:#9aa7bd;
        --acc:#5ac8fa;--dia:#ffd166;--noite:#8b9dff;--ok:#4ade80;--warn:#fbbf24}
  *{box-sizing:border-box}
  body{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
       background:var(--bg);color:var(--txt)}
  header{padding:22px 18px 12px;border-bottom:1px solid #263040;background:#121721;
         position:sticky;top:0;z-index:10}
  h1{margin:0 0 4px;font-size:20px}
  .sub{color:var(--dim);font-size:13px}
  .wrap{max-width:1100px;margin:0 auto;padding:18px}
  .controles{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
  input,select{background:var(--card2);border:1px solid #2d3644;color:var(--txt);
               padding:9px 11px;border-radius:8px;font-size:14px}
  input{flex:1;min-width:220px}
  input:focus,select:focus{outline:2px solid var(--acc);outline-offset:-1px}
  .grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
  .card{background:var(--card);border:1px solid #263040;border-radius:12px;padding:14px}
  .card h3{margin:0 0 2px;font-size:16px;display:flex;gap:8px;align-items:baseline}
  .num{color:var(--dim);font-size:13px;font-weight:400}
  .tags{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
  .tag{font-size:11px;padding:2px 8px;border-radius:999px;background:#232b3a;color:var(--dim)}
  .tag.lend{background:#3a2430;color:#ff9db1}
  .tag.mit{background:#2f2440;color:#c9a6ff}
  .tag.g{background:#1c3340;color:#79d0ef}
  table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
  th,td{text-align:left;padding:5px 6px;border-bottom:1px solid #232b3a}
  th{color:var(--dim);font-weight:600;font-size:12px;text-transform:uppercase;
     letter-spacing:.03em}
  td.n{text-align:right;font-variant-numeric:tabular-nums}
  .dia{color:var(--dia)} .noite{color:var(--noite)}
  .metodo{color:var(--dim);font-size:12px}
  .vazio{color:var(--dim);font-style:italic;font-size:13px}
  .nota{background:#1a2130;border-left:3px solid var(--warn);padding:10px 12px;
        border-radius:6px;color:var(--dim);font-size:13px;margin:14px 0}
  .contador{color:var(--dim);font-size:13px;margin:14px 0 6px}
  details summary{cursor:pointer;color:var(--acc);font-size:13px;margin-top:8px}
  .evo{font-size:13px;color:var(--dim);margin:2px 0}
  .evo b{color:var(--txt);font-weight:600}
  footer{color:var(--dim);font-size:12px;padding:22px 18px;text-align:center;
         border-top:1px solid #263040;margin-top:30px}
  a{color:var(--acc)}
</style>
</head>
<body>
<header>
  <h1>Guia — FireRed Gen 1–9 <span class="sub">V42</span></h1>
  <div class="sub">Dados extraídos da própria ROM: <code>__SHA__</code></div>
  <div class="controles">
    <input id="q" placeholder="Buscar por nome ou nº da Pokédex…" autocomplete="off">
    <select id="metodo">
      <option value="">Todos os métodos</option>
      <option value="grama/caverna">Grama / caverna</option>
      <option value="surf">Surf</option>
      <option value="pesca">Pesca</option>
      <option value="rock smash">Rock Smash</option>
      <option value="evento">Evento fixo</option>
    </select>
    <select id="periodo">
      <option value="">Dia e noite</option>
      <option value="dia">Só dia</option>
      <option value="noite">Só noite</option>
    </select>
    <select id="ger">
      <option value="">Todas as gerações</option>
      <option>1</option><option>2</option><option>3</option><option>4</option>
      <option>5</option><option>6</option><option>7</option><option>8</option>
      <option>9</option>
    </select>
    <select id="raros">
      <option value="">Todos</option>
      <option value="comum">Só comuns</option>
      <option value="lendario">Lendários / míticos</option>
    </select>
  </div>
</header>

<div class="wrap">
  <div class="nota">
    <b>Como ler a chance.</b> <code>chance</code> é o peso do slot
    <i>depois</i> que um encontro acontece naquele mapa — não é chance por passo.
    Valores de 1% exigem paciência. <b>Dia</b> = 06:00–19:59,
    <b>noite</b> = 20:00–05:59, derivados do tempo de jogo.
  </div>
  <div class="contador" id="contador"></div>
  <div class="grid" id="lista"></div>
</div>

<footer>
  Guia gerado a partir da ROM V42 (<code>6997366b…bd99a</code>).
  Cobertura estrutural de tabela: não prova que todo tile é alcançável em toda
  etapa da história, nem que cada espécie foi capturada em jogo.
</footer>

<script>
const DADOS = __DADOS__;
const lista = document.getElementById('lista');
const contador = document.getElementById('contador');
const q = document.getElementById('q');
const fMetodo = document.getElementById('metodo');
const fPeriodo = document.getElementById('periodo');
const fGer = document.getElementById('ger');
const fRaros = document.getElementById('raros');

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const titulo = s => esc(s).replace(/\\b\\w/g, c => c.toUpperCase());

function ocorrencias(p) {
  // junta encontros de dia, noite e eventos fixos numa lista única filtrável
  const out = [];
  for (const e of p.horario) out.push({...e, origem:'horario'});
  const vistos = new Set(p.horario.map(e => e.mapa_id + '|' + e.metodo + '|' + e.periodo));
  for (const e of p.encontros) {
    if (vistos.has(e.mapa_id + '|' + e.metodo + '|' + e.periodo)) continue;
    out.push({...e, origem:'tabela'});
  }
  for (const f of p.fixos) {
    out.push({mapa:f.mapa, mapa_id:f.mapa, metodo:'evento fixo', periodo:'sempre',
              nivel_min:f.nivel, nivel_max:f.nivel, chance:null, origem:'fixo'});
  }
  if (p.evento_nativo) {
    out.push({mapa:p.evento_nativo, mapa_id:'nativo', metodo:'evento nativo',
              periodo:'sempre', nivel_min:null, nivel_max:null, chance:null,
              origem:'nativo'});
  }
  return out;
}

function casa(p, occ) {
  const termo = q.value.trim().toLowerCase();
  if (termo) {
    const porNome = p.nome.toLowerCase().includes(termo);
    const porNum = String(p.id) === termo || String(p.id).padStart(3,'0') === termo;
    if (!porNome && !porNum) return false;
  }
  if (fGer.value && String(p.geracao) !== fGer.value) return false;
  if (fRaros.value === 'lendario' && !(p.lendario || p.mitico)) return false;
  if (fRaros.value === 'comum' && (p.lendario || p.mitico)) return false;
  if (fMetodo.value) {
    const alvo = fMetodo.value;
    if (alvo === 'evento') {
      if (!occ.some(o => o.metodo.startsWith('evento'))) return false;
    } else if (!occ.some(o => o.metodo === alvo)) return false;
  }
  if (fPeriodo.value && !occ.some(o => o.periodo === fPeriodo.value)) return false;
  return true;
}

function tabelaOcorrencias(occ) {
  if (!occ.length) return '<div class="vazio">Sem encontro selvagem nesta ROM — veja evolução ou evento.</div>';
  occ = occ.slice().sort((a,b) => (a.chance ?? 0) < (b.chance ?? 0) ? 1 : -1).slice(0, 14);
  const linhas = occ.map(o => {
    const per = o.periodo === 'noite' ? '<span class="noite">noite</span>'
              : o.periodo === 'dia' ? '<span class="dia">dia</span>'
              : '<span style="color:var(--dim)">sempre</span>';
    const nv = o.nivel_min == null ? '—'
             : (o.nivel_min === o.nivel_max ? o.nivel_min : o.nivel_min + '–' + o.nivel_max);
    const ch = o.chance == null ? '—' : o.chance + '%';
    return `<tr><td>${esc(o.mapa)}<div class="metodo">${esc(o.metodo)}</div></td>
            <td>${per}</td><td class="n">${nv}</td><td class="n">${ch}</td></tr>`;
  }).join('');
  return `<table><thead><tr><th>Onde</th><th>Período</th><th>Nível</th><th>Chance</th></tr></thead>
          <tbody>${linhas}</tbody></table>`;
}

function cardEvolucao(p) {
  const linhas = [];
  if (p.evolui_de) linhas.push(`<div class="evo">vem de <b>#${p.evolui_de}</b></div>`);
  for (const e of p.evolui_para) {
    const cond = e.metodo === 'nível' && e.param ? `nível ${e.param}` : esc(e.metodo);
    linhas.push(`<div class="evo">evolui para <b>${esc(e.para_nome)}</b> (#${e.para}) — ${cond}</div>`);
  }
  if (!linhas.length) return '';
  return `<details><summary>Evolução</summary>${linhas.join('')}</details>`;
}

function render() {
  const frag = [];
  let n = 0;
  for (const p of DADOS.pokemon) {
    const occ = ocorrencias(p);
    if (!casa(p, occ)) continue;
    n++;
    if (frag.length >= 60) continue;   // desenha até 60 por vez (rolagem)
    const tags = [`<span class="tag g">Gen ${p.geracao}</span>`];
    if (p.lendario) tags.push('<span class="tag lend">lendário</span>');
    if (p.mitico) tags.push('<span class="tag mit">mítico</span>');
    frag.push(`<div class="card">
      <h3>${titulo(p.nome)} <span class="num">#${p.id}</span></h3>
      <div class="tags">${tags.join('')}</div>
      ${tabelaOcorrencias(occ)}
      ${cardEvolucao(p)}
    </div>`);
  }
  lista.innerHTML = frag.join('');
  contador.textContent = `${n} de ${DADOS.total} Pokémon` +
    (n > 60 ? ` — mostrando os 60 primeiros; refine a busca` : '');
}

for (const el of [q,fMetodo,fPeriodo,fGer,fRaros]) el.addEventListener('input', render);
render();
</script>
</body>
</html>
"""


def main() -> int:
    if "--self-test" in sys.argv:
        ok = True
        # bonito() não pode devolver vazio nem manter MAP_
        for s in ("MAP_ROUTE1", "MAP_CERULEAN_CAVE_B1F", "MAP_ALGO_NOVO_2F"):
            r = bonito(s)
            bom = bool(r) and "MAP_" not in r
            ok &= bom
            print(f"  [{'PASS' if bom else 'FAIL'}] {s} -> {r}")
        # o HTML precisa conter os marcadores de substituição
        for marca in ("__SHA__", "__DADOS__"):
            bom = marca in HTML
            ok &= bom
            print(f"  [{'PASS' if bom else 'FAIL'}] marcador {marca} presente")
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
    dados = coletar(rom_path.read_bytes(), gen)

    (saida / "dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1))
    html = HTML.replace("__SHA__", ROM_ESPERADA).replace(
        "__DADOS__", json.dumps(dados, ensure_ascii=False, separators=(",", ":")))
    (saida / "index.html").write_text(html, encoding="utf-8")

    print(f"[site] {saida/'index.html'}  ({len(html)/1024:.0f} KB)")
    print(f"[site] {saida/'dados.json'}   ({dados['total']} Pokémon)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
