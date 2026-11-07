#!/usr/bin/env bash
# Suíte de auditoria do Cosmog na V42 — roda o que é possível neste ambiente.
#
# 1) estruturais (só ROM, sem emulador)  -> não precisa de core
# 2) nativas (core mGBA libretro)        -> compila o core se preciso
#
# A fonte do motor Gen 1–9 não vive neste branch: ela vem do PR #9. Este script
# extrai firered_gen1_9/ de uma ref git para um diretório temporário, roda, e não
# versiona nada dela.
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
REF="${GEN19_REF:-345efac}"          # commit do PR #9 com o motor até a V42
WORK="${GEN19_WORK:-/tmp/gen19}"
ROM="${COSMOG_V42_ROM:-$ROOT/google_drive/FireRed_Gen1-9_motor_v42.gba}"
LOG="$ROOT/logs/cosmog_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$ROOT/logs"

say() { echo "$@" | tee -a "$LOG"; }

[ -f "$ROM" ] || { say "ROM ausente: $ROM (não versionada — coloque sua cópia)"; exit 2; }

if [ ! -d "$WORK/firered_gen1_9" ]; then
  say "[setup] extraindo firered_gen1_9/ de $REF"
  mkdir -p "$WORK"
  git -C "$ROOT" archive "$REF" firered_gen1_9 | tar -x -C "$WORK"
fi
GEN="$WORK/firered_gen1_9"

# testes deste repositório que complementam a suíte do motor
cp "$ROOT/v42/tests/test_cosmog_hatch_v42_mgba.py" "$GEN/tests/" 2>/dev/null || true

# o harness do motor importa gba_libretro_emu, que só existe em legado/
mkdir -p "$WORK/harness"
[ -f "$WORK/harness/gba_libretro_emu.py" ] || \
  cp "$GEN/legado/v3_original/scripts/gba_libretro_emu.py" "$WORK/harness/"

FALHAS=0
roda() {
  local nome="$1"; shift
  say "=== [$nome] ==="
  if "$@" >>"$LOG" 2>&1; then say "  PASSOU"; else say "  FALHOU"; FALHAS=$((FALHAS+1)); fi
}

cd "$GEN"
export PYTHONPATH="$WORK/harness:$GEN:$GEN/tests"
export COSMOG_V42_ROM="$ROM"

roda "cosmog:estruturais" python3 -B -m unittest -v tests.test_cosmog_v42

# nativas: só se a fonte do mGBA estiver vendorizada
if [ -d "$ROOT/tools/gba_shim/build/mgba-src" ]; then
  CORE="${MGBA_CORE:-/tmp/mgba-lr/mgba_libretro.so}"
  if [ ! -f "$CORE" ]; then
    say "[setup] compilando core libretro (uma vez, ~25 s)"
    CORE=$(bash "$ROOT/v42/scripts/build_libretro_core.sh" 2>>"$LOG" | tail -1)
  fi
  export MGBA_CORE="$CORE"
  say "[core] $CORE"
  roda "cosmog:nativos"   python3 -B -m unittest -v tests.test_cosmog_v42_mgba
  roda "cosmog:eclosao"   python3 -B -m unittest -v tests.test_cosmog_hatch_v42_mgba
  # sonda do shim próprio: prova que o .so abre a V42 e que a leitura de memória
  # pelo barramento custa microssegundos (é a razão de existir do shim)
  if [ -f "$ROOT/tools/gba_shim/build/gba_shim.so" ]; then
    roda "cosmog:shim"    python3 -B "$ROOT/v42/scripts/probe_shim_rom.py"
  else
    say "[pulado] shim ausente — rode: make -C tools/gba_shim shim"
  fi
else
  say "[pulado] fonte do mGBA ausente — só estruturais rodaram"
  say "         reconstrua com: make -C tools/gba_shim libmgba"
fi

say "resumo: $FALHAS falha(s) — log: $LOG"
exit "$FALHAS"
