#!/usr/bin/env bash
# run_all_tests.sh — bateria única de self-tests de TODOS os scripts do toolkit.
# Uso:   bash scripts/run_all_tests.sh
# Saída: logs/tests_YYYYMMDD_HHMMSS.log + código de saída agregado (0=tudo OK).
set -u
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/tests_$(date +%Y%m%d_%H%M%S).log"
: >"$LOG"
FALHAS=0
for s in scripts/gba_*.py; do
  nome=$(basename "$s" .py)
  echo "=== [$nome] ===" | tee -a "$LOG"
  if python3 "$s" --self-test >>"$LOG" 2>&1; then
    echo "  self-test: PASSOU" | tee -a "$LOG"
  else
    echo "  self-test: FALHOU" | tee -a "$LOG"
    FALHAS=$((FALHAS + 1))
  fi
done
echo "===============================" | tee -a "$LOG"
echo "resumo: $FALHAS script(s) com self-test falho — log: $LOG" | tee -a "$LOG"
exit "$FALHAS"
