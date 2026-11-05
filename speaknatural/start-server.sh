#!/usr/bin/env bash
# ============================================================================
#  SpeakNatural - inicia o servidor local no Linux / macOS
#
#  Uso:
#      chmod +x start-server.sh     (só na primeira vez)
#      ./start-server.sh
#
#  O script:
#    1. confere se o Python 3.11+ existe
#    2. cria o ambiente virtual (backend/.venv) na primeira vez
#    3. instala as dependências (a primeira vez baixa ~2,5 GB)
#    4. avisa se o ffmpeg / espeak-ng estiverem faltando
#    5. mostra o IP do PC na rede local
#    6. sobe o servidor em http://0.0.0.0:8000
# ============================================================================
set -euo pipefail
cd "$(dirname "$0")"

echo
echo "=================================================="
echo "   SpeakNatural — servidor local de pronúncia"
echo "=================================================="
echo

# ------------------------------ 1. Python -----------------------------------
PYTHON_BIN=""
for candidate in python3.12 python3.11 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "[ERRO] Python 3.11 ou mais novo não encontrado."
  echo
  echo "  macOS:  brew install python@3.12"
  echo "  Ubuntu: sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip"
  echo "  Fedora: sudo dnf install python3.11 python3-pip"
  echo
  exit 1
fi
echo "[ok] $($PYTHON_BIN --version)"

# --------------------------- 2. Ambiente virtual ----------------------------
cd backend
if [ ! -x ".venv/bin/python" ]; then
  echo "[..] Criando o ambiente virtual pela primeira vez..."
  "$PYTHON_BIN" -m venv .venv
fi
VENV_PY=".venv/bin/python"

# ---------------------------- 3. Dependências -------------------------------
STAMP=".venv/requirements-instaladas.txt"
if [ ! -f "$STAMP" ] || ! cmp -s requirements.txt "$STAMP"; then
  echo
  echo "[..] Instalando as dependências do Python."
  echo "     AVISO: a primeira vez baixa cerca de 2,5 GB (PyTorch, faster-whisper...)."
  echo "     Pode levar de 5 a 30 minutos. Tenha paciência."
  echo
  "$VENV_PY" -m pip install --upgrade pip --quiet
  "$VENV_PY" -m pip install -r requirements.txt
  cp requirements.txt "$STAMP"
fi
echo "[ok] Dependências prontas."

# ------------------ 4. Programas externos (ffmpeg/espeak) -------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo
  echo "[AVISO] ffmpeg não encontrado. A conversão de áudio fica limitada."
  echo "        macOS:  brew install ffmpeg"
  echo "        Ubuntu: sudo apt install ffmpeg"
fi
if ! command -v espeak-ng >/dev/null 2>&1; then
  echo
  echo "[AVISO] espeak-ng não encontrado. O app usa um dicionário interno de fonemas."
  echo "        macOS:  brew install espeak-ng"
  echo "        Ubuntu: sudo apt install espeak-ng"
fi

# ------------------------------- 5. IP --------------------------------------
echo
# (os "|| true" evitam que o `set -e` derrube o script quando não há IP)
if command -v ip >/dev/null 2>&1; then
  IPS=$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | paste -sd' ' - || true)
elif command -v ifconfig >/dev/null 2>&1; then
  IPS=$( (ifconfig 2>/dev/null | awk '/inet /{print $2}' | grep -v '^127\.' | paste -sd' ' -) || true)
else
  IPS=""
fi
if [ -n "${IPS:-}" ]; then
  echo "[info] IP deste PC na rede: $IPS"
else
  echo "[info] Não consegui detectar o IP. Rode 'ip addr' ou 'ifconfig' para ver."
fi
echo "[info] No celular, use: http://IP-ACIMA:8000  (tela \"Servidor\" do app)"
echo

# ----------------------------- 6. Servidor ----------------------------------
echo "=================================================="
echo "   Servidor no ar. NÃO FECHE ESTA JANELA."
echo "   No PC, abra:  http://localhost:8000"
echo "   Documentação: http://localhost:8000/docs"
echo "   Para parar:   Ctrl+C"
echo "=================================================="
echo
exec "$VENV_PY" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
