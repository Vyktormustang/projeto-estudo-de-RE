#!/usr/bin/env bash
# setup_env.sh — FASE 0: instala as dependências MÍNIMAS do projeto gba-re.
#
# Objetivo:      garantir o toolchain Python mínimo para as Fases 1 e 5.
# Pré-requisito: Python 3.9+ com pip. (Windows: use "py -m pip install capstone")
# Entradas:      nenhuma.  Saídas: pacotes pip instalados no ambiente atual.
# Uso:           bash gba-re/scripts/setup_env.sh
# Idempotente:   pode rodar várias vezes sem efeitos colaterais.
set -euo pipefail

echo "[setup_env] Python: $(python3 --version 2>&1)"
echo "[setup_env] Instalando capstone (desassemblador ARM/Thumb)..."
python3 -m pip install --quiet capstone

python3 - <<'PY'
import capstone
print("[setup_env] OK — capstone", capstone.__version__)
PY

echo "[setup_env] Nada mais a instalar por ora (regra: configuração mínima)."
echo "[setup_env] Fase 2 (Ghidra) e Fase 4 (mGBA) serão decididas quando a ROM existir."
