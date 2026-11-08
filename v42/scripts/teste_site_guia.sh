#!/usr/bin/env bash
# Valida o site do guia: sintaxe do JS + render real com DOM simulado.
# Uso: bash v42/scripts/teste_site_guia.sh [caminho_do_site]
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SITE="${1:-$ROOT/site_guia}"
[ -f "$SITE/index.html" ] || { echo "[ERRO] site ausente; gere com gerar_guia_site.py"; exit 2; }
command -v node >/dev/null || { echo "[ERRO] node ausente"; exit 2; }
python3 - "$SITE" <<'PY'
import re, pathlib, sys
# checa a sintaxe de cada <script> de cada página, removendo só o JSON gigante
for nome in ("index", "pokemon", "mapas", "evolucoes", "eventos"):
    html = pathlib.Path(sys.argv[1], f"{nome}.html").read_text()
    for i, js in enumerate(re.findall(r"<script>(.*?)</script>", html, re.S)):
        if js.strip().startswith("const DADOS"):
            js = re.sub(r"^const DADOS\s*=.*?;\s*", "", js, count=1, flags=re.S)
        pathlib.Path(f"/tmp/_guia_{nome}_{i}.js").write_text(js)
PY
for f in /tmp/_guia_*.js; do node --check "$f" || exit 1; done
node "$ROOT/v42/scripts/teste_site_guia.js" "$SITE"
