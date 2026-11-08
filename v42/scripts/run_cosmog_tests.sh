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
  # O commit do motor NÃO existe em todo clone (vive no branch do PR #9). Sem
  # buscá-lo, `git archive` falha e o tar engole um erro — o script seguia e
  # reportava "3 falhas" como se fosse defeito de código. Buscamos a ref antes.
  if ! git -C "$ROOT" cat-file -e "$REF^{commit}" 2>/dev/null; then
    say "[setup] $REF ausente neste clone — buscando a ref do motor"
    git -C "$ROOT" fetch --depth=1 origin "${GEN19_REF_BRANCH:-arena/8b7d7c0a-projeto-estudo-de-re}" >>"$LOG" 2>&1 \
      || { say "[ERRO] não foi possível buscar o commit do motor ($REF)"; exit 2; }
    git -C "$ROOT" cat-file -e "$REF^{commit}" 2>/dev/null \
      || { say "[ERRO] $REF continua ausente após o fetch"; exit 2; }
  fi
  if ! git -C "$ROOT" archive "$REF" firered_gen1_9 | tar -x -C "$WORK"; then
    say "[ERRO] falha ao extrair firered_gen1_9/ de $REF"; exit 2
  fi
  [ -d "$WORK/firered_gen1_9" ] || { say "[ERRO] extração vazia: $WORK/firered_gen1_9"; exit 2; }
fi
GEN="$WORK/firered_gen1_9"

# testes deste repositório que complementam a suíte do motor
cp "$ROOT/v42/tests/test_cosmog_hatch_v42_mgba.py" "$GEN/tests/" 2>/dev/null || true

# o harness do motor importa gba_libretro_emu, que só existe em legado/
mkdir -p "$WORK/harness"
[ -f "$WORK/harness/gba_libretro_emu.py" ] || \
  cp "$GEN/legado/v3_original/scripts/gba_libretro_emu.py" "$WORK/harness/"

# A eclosão exige ~30.600 passos reais. Com orçamento menor o teste é SKIP, e
# unittest SAI com 0 — ou seja, "0 falhas" com a eclosão nunca executada. Este
# piso garante que a prova não seja silenciosamente desligada.
HATCH_MIN="${COSMOG_HATCH_MAX_STEPS_MIN:-36000}"
if [ -n "${COSMOG_HATCH_MAX_STEPS:-}" ] && [ "${COSMOG_HATCH_MAX_STEPS}" -lt "$HATCH_MIN" ] 2>/dev/null; then
  echo "[ERRO] COSMOG_HATCH_MAX_STEPS=${COSMOG_HATCH_MAX_STEPS} < $HATCH_MIN: a eclosão" \
       "não seria provada e o resultado sairia como verde falso." | tee -a "$LOG"
  exit 2
fi

FALHAS=0
roda() {
  local nome="$1"; shift
  say "=== [$nome] ==="
  if "$@" >>"$LOG" 2>&1; then say "  PASSOU"; else say "  FALHOU"; FALHAS=$((FALHAS+1)); fi
}

# A evidência tem de SOBREVIVER ao ambiente. Os .log ficam fora do Git
# (logs/*.log no .gitignore) e já se perderam num reset de sessão — então, ao
# final, as linhas-prova são extraídas para um arquivo VERSIONADO.
exportar_evidencia() {
  local saida="$ROOT/reports/v42/EVIDENCIA_COSMOG_V42.txt"
  [ -f "$LOG" ] || return 0
  {
    echo "# Evidência da suíte do Cosmog na V42 — gerada por v42/scripts/run_cosmog_tests.sh"
    echo "# data: $(date -Is)"
    echo "# ROM sha256: $(sha256sum "$ROM" 2>/dev/null | cut -d' ' -f1)"
    echo "# log completo (NÃO versionado): $LOG"
    echo
    grep -aE '^(=== \[|  (PASSOU|FALHOU))|^Ran [0-9]+ tests|^OK|^FAILED|HATCH_[A-Z_]+|DAYCARE_SCORE|EGG_CONTRACT|NATIVE_EGG|^resumo:' "$LOG" \
      | tr -d '\000'
  } >"$saida"
  say "[evidência] $saida"
}
trap exportar_evidencia EXIT

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
  # cobertura de encontros selvagens lida da própria V42 (estrutural)
  roda "cosmog:encontros" python3 -B "$ROOT/v42/scripts/auditoria_encontros_v42.py"
  roda "cosmog:horario"   python3 -B "$ROOT/v42/scripts/auditoria_horario_v42.py"
else
  say "[pulado] fonte do mGBA ausente — só estruturais rodaram"
  say "         reconstrua com: make -C tools/gba_shim libmgba"
fi

say "resumo: $FALHAS falha(s) — log: $LOG"
exit "$FALHAS"
