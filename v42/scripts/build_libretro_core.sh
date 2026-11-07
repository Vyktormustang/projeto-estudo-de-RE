#!/usr/bin/env bash
# Compila o core mGBA libretro a partir da fonte já vendorizada no repositório.
#
# Por que: a suíte nativa do motor Gen 1–9 (tests/*_mgba.py) exige
# MGBA_CORE=<libretro .so>. O .deb do Debian exige GLIBC 2.38 e quebra aqui.
# A fonte em tools/gba_shim/build/mgba-src é a MESMA que gera o shim.
#
# Uso:  bash v42/scripts/build_libretro_core.sh [saida.so]
#       MGBA_CORE=$(bash v42/scripts/build_libretro_core.sh) python3 -m unittest ...
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SRC="$ROOT/tools/gba_shim/build/mgba-src"
OUT="${1:-/tmp/mgba-lr/mgba_libretro.so}"
CMAKE="$ROOT/tools/gba_shim/build/tools/bin/cmake"
[ -x "$CMAKE" ] || CMAKE=$(command -v cmake)

[ -d "$SRC" ] || { echo "[ERRO] fonte ausente: $SRC"; exit 1; }

# CMAKE_POLICY_VERSION_MINIMUM: cmake novo recusa o CMakeLists histórico do mGBA.
"$CMAKE" -S "$SRC" -B "$(dirname "$OUT")" \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_LIBRETRO=ON -DLIBMGBA_ONLY=ON -DBUILD_SHARED=OFF -DBUILD_STATIC=ON \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DUSE_PNG=OFF -DUSE_ZLIB=ON -DUSE_MINIZIP=OFF -DUSE_FFMPEG=OFF \
  -DUSE_SQLITE3=OFF -DUSE_LIBZIP=OFF -DUSE_LUA=OFF -DUSE_LZMA=OFF \
  -DUSE_ELF=OFF -DUSE_DEBUGGERS=OFF -DUSE_DISCORD_RPC=OFF \
  -DM_CORE_GB=OFF -DM_CORE_GBA=ON >/dev/null

"$CMAKE" --build "$(dirname "$OUT")" -j"$(nproc)" >/dev/null
test -f "$OUT" || { echo "[ERRO] não gerou $OUT"; exit 1; }
echo "$OUT"
