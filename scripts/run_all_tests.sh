#!/usr/bin/env bash
# run_all_tests.sh — bateria única: self-tests de TODOS os scripts + prova de mod.
# Uso:    bash scripts/run_all_tests.sh
# Saída:  logs/tests_YYYYMMDD_HHMMSS.log + exit agregado (0 = tudo OK).
#
# Pré-requisitos (uma vez):  bash scripts/setup_env.sh
#                            make -C tools/gba_shim -j$(nproc)
set -u
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/tests_$(date +%Y%m%d_%H%M%S).log"
: >"$LOG"
FALHAS=0
TOTAL=0

roda() {                      # roda <descrição> <comando...>
  local desc="$1"; shift
  TOTAL=$((TOTAL + 1))
  echo "=== [$desc] ===" | tee -a "$LOG"
  if "$@" >>"$LOG" 2>&1; then
    echo "  PASSOU" | tee -a "$LOG"
  else
    echo "  FALHOU" | tee -a "$LOG"
    FALHAS=$((FALHAS + 1))
  fi
}

for s in scripts/gba_*.py; do
  roda "$(basename "$s" .py)" python3 "$s" --self-test
done

roda "fixture:make_bench_rom" python3 tests/fixtures/make_bench_rom.py --self-test
roda "shim:smoke"             python3 tools/gba_shim/shim_smoke.py
roda "mod:bench (emulador)"   python3 tests/teste_mod_bench.py
roda "mod:apply (relatório)"  python3 scripts/apply_mod.py --self-test

# auditorias do plano do Linear (VYK-58/59/60): ver docs/VYK59_AUDITORIA_HOOK_V3.md
roda "vyk59:auditoria-v42"    python3 scripts/auditoria_vyk59.py --self-test
roda "vyk59:auditoria-v3"     python3 scripts/auditoria_vyk59_v3.py --self-test
roda "vyk60:sempre-escreve"   python3 scripts/teste_vyk60_sempre_escreve.py --self-test
roda "skills:auditor"         python3 scripts/skills_audit.py --self-test

echo "===============================" | tee -a "$LOG"
echo "resumo: $FALHAS de $TOTAL falharam — log: $LOG" | tee -a "$LOG"
exit "$FALHAS"
