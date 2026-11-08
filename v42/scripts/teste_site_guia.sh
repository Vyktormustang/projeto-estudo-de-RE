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
html = pathlib.Path(sys.argv[1], "index.html").read_text()
js = re.search(r"<script>(.*)</script>", html, re.S).group(1)
# remove só o JSON gigante para checar sintaxe do resto
sem = re.sub(r"const DADOS = \{.*?\};\nconst lista", "const DADOS = {};\nconst lista", js, flags=re.S)
pathlib.Path("/tmp/_guia_check.js").write_text(sem)
PY
node --check /tmp/_guia_check.js || exit 1
node "$ROOT/v42/scripts/teste_site_guia.js" "$SITE"
