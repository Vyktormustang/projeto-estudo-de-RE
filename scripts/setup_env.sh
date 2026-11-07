#!/usr/bin/env bash
# setup_env.sh — FASE 0: dependências Python do toolkit gba-re.
#
# Uso:        bash scripts/setup_env.sh
# Idempotente: pode rodar quantas vezes quiser.
# Windows:    py -m pip install capstone keystone-engine unicorn
set -euo pipefail

echo "[setup_env] Python: $(python3 --version 2>&1)"
echo "[setup_env] Instalando capstone (desassemblador), keystone-engine (montador)"
echo "[setup_env] e unicorn (simulação do payload ANTES de gravar na ROM)..."
python3 -m pip install --quiet --break-system-packages capstone keystone-engine unicorn 2>/dev/null \
  || python3 -m pip install --quiet capstone keystone-engine unicorn

python3 - <<'PY'
import capstone, keystone, unicorn
print("[setup_env] OK - capstone", capstone.__version__,
      "| keystone", keystone.__version__, "| unicorn", unicorn.__version__)
PY

echo
echo "[setup_env] Emulador (mGBA): o core libretro do .deb NAO e mais usado"
echo "            (exige GLIBC 2.38 e nao expoe CPU/memoria). Compile o shim"
echo "            proprio uma vez (~2 min, precisa gcc + make):"
echo "              make -C tools/gba_shim -j\$(nproc)"
echo "              make -C tools/gba_shim test-shim"
echo "            ROM de bancada (fixture propria, sem conteudo de jogo):"
echo "              python3 tests/fixtures/make_bench_rom.py"
