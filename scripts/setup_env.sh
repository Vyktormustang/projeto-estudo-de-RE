#!/usr/bin/env bash
# setup_env.sh — cria um ambiente Python isolado e instala as dependências mínimas.
# Uso: bash scripts/setup_env.sh
# Requer Python 3.9+ com suporte a venv; não altera os pacotes do sistema.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT}/.venv"

if [[ ! -x "${VENV}/bin/python" ]]; then
  echo "[setup_env] Criando ambiente virtual em ${VENV}"
  python3 -m venv "${VENV}"
fi

PYTHON="${VENV}/bin/python"
echo "[setup_env] Python: $(${PYTHON} --version 2>&1)"
echo "[setup_env] Instalando Capstone, CMake, Keystone e Pillow no ambiente virtual..."
"${PYTHON}" -m pip install --quiet capstone cmake keystone-engine pillow
"${PYTHON}" - <<'PY'
import capstone
print("[setup_env] OK — capstone", capstone.__version__)
PY
"${VENV}/bin/cmake" --version | sed -n '1p'

echo "[setup_env] Ambiente pronto. Para ativá-lo: source .venv/bin/activate"
echo "[setup_env] Core mGBA local: verifique emu/BUILD_INFO.md (não requer atualizar GLIBC)."
