#!/usr/bin/env bash
# run_all_tests.sh — bateria única: self-tests de TODOS os scripts + prova de mod.
# Uso:    bash scripts/run_all_tests.sh
# Saída:  logs/tests_YYYYMMDD_HHMMSS.log + exit agregado (0 = tudo OK).
#
# Pré-requisitos (uma vez):  bash scripts/setup_env.sh
#                            make -C tools/gba_shim -j$(nproc)
set -u
cd "$(dirname "$0")/.."

# As dependências (capstone, keystone-engine, unicorn) NÃO podem ser instaladas
# no Python do sistema (PEP 668), então vivem em .venv. Sem pôr .venv no PATH,
# oito baterias caem com "No module named 'capstone'/'keystone'" e o resultado
# parece regressão de código quando é ambiente faltando.
if [ -x .venv/bin/python3 ]; then
  PATH="$PWD/.venv/bin:$PATH"
  export PATH
else
  echo "[AVISO] .venv ausente: as baterias que usam capstone/keystone/unicorn"
  echo "        vão falhar por dependência, não por defeito. Crie com:"
  echo "        python3 -m venv .venv && .venv/bin/pip install capstone keystone-engine unicorn"
fi

mkdir -p logs
LOG="logs/tests_$(date +%Y%m%d_%H%M%S).log"
: >"$LOG"
FALHAS=0
TOTAL=0
INCOMPLETOS=0

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

# sondas do plano de eclosão da V42: rodam SEM ROM/core/motor extraído, só a
# aritmética de cada instrumento. A execução real fica em v42/scripts/run_cosmog_tests.sh.
for s in v42/scripts/probe_shim_rom.py v42/scripts/hatch_probe.py \
         v42/scripts/hatch_calibra.py v42/scripts/diag_hatch_walk.py; do
  roda "v42:$(basename "$s" .py)" python3 "$s" --self-test
done

# auditoria da V42 (motor Gen 1-9): estruturais sempre; nativas se houver ROM e
# core. Sem a ROM (não versionada) o script sai em 2 — isso NÃO derruba a bateria.
if bash v42/scripts/run_cosmog_tests.sh >>"$LOG" 2>&1; then
  echo "=== [v42:cosmog] ===" | tee -a "$LOG"; echo "  PASSOU" | tee -a "$LOG"
else
  rc=$?
  echo "=== [v42:cosmog] ===" | tee -a "$LOG"
  if [ "$rc" -eq 2 ]; then
    # código 2 = ambiente incompleto (sem ROM ou sem core/shim). Não conta como
    # falha de código, mas TAMBÉM não pode ser anunciado como sucesso: a prova
    # nativa e a eclosão não rodaram. Marca-se como incompleto no resumo.
    echo "  INCOMPLETO (sem ROM/core/shim) — prova nativa NAO executada" | tee -a "$LOG"
    INCOMPLETOS=$((INCOMPLETOS + 1))
  else
    echo "  FALHOU" | tee -a "$LOG"; FALHAS=$((FALHAS + 1))
  fi
fi

echo "===============================" | tee -a "$LOG"
echo "resumo: $FALHAS de $TOTAL falharam — log: $LOG" | tee -a "$LOG"
if [ "$INCOMPLETOS" -gt 0 ]; then
  echo "ATENCAO: $INCOMPLETOS bateria(s) INCOMPLETA(s) — ambiente faltando, nao prova" | tee -a "$LOG"
fi
exit "$FALHAS"
