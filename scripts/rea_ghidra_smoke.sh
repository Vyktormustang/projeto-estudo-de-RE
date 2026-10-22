#!/usr/bin/env bash
# =============================================================================
# rea_ghidra_smoke.sh — teste ponta-a-ponta REA + Ghidra, sem a ROM comercial
# =============================================================================
# Gera uma imagem ARM32 sintética em 0x08000000 (scripts/make_synthetic_arm_image.py)
# e pede ao REA para analisá-la com o provider Ghidra em modo raw-binary:
#
#   rea inspect  <img> --target-format raw-binary --architecture arm --entry-point 0x8000000
#   rea function <img> 0x8000000 ...  (entry)
#   rea function <img> 0x800002c ...  (rotina que escreve na mochila)
#
# Evidências vão para reports/re_tools/ (JSON do REA + sha256 da imagem).
#
# Códigos de saída:
#   0  smoke test passou
#   1  smoke test rodou e falhou
#   3  pré-requisitos ausentes (JDK/Ghidra/REA) — nada foi executado
#
# Uso: bash scripts/rea_ghidra_smoke.sh
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$REPO_ROOT/reports/re_tools"
IMG="$OUT_DIR/synthetic_arm.gba"

log() { printf '[smoke] %s\n' "$*" >&2; }

# shellcheck disable=SC1091
. "$SCRIPT_DIR/re_env.sh"

missing=0
if ! command -v rea >/dev/null 2>&1; then
  log "pré-requisito ausente: comando rea"; missing=1
fi
if [ ! -x "${JAVA_HOME:-/nonexistent}/bin/javac" ]; then
  log "pré-requisito ausente: JDK completo (JAVA_HOME/bin/javac)"; missing=1
fi
if [ ! -f "${GHIDRA_INSTALL_DIR:-/nonexistent}/Ghidra/application.properties" ]; then
  log "pré-requisito ausente: GHIDRA_INSTALL_DIR (Ghidra 12.1.x)"; missing=1
fi
if [ "$missing" -ne 0 ]; then
  log "nada foi executado. Rode: bash scripts/setup_re_tools.sh"
  log "diagnóstico:                bash scripts/re_tools_check.sh"
  exit 3
fi

log "JAVA_HOME=$JAVA_HOME"
log "GHIDRA_INSTALL_DIR=$GHIDRA_INSTALL_DIR"
log "rea=$(rea --version)"

mkdir -p "$OUT_DIR"

log "gerando imagem ARM sintética"
python3 "$SCRIPT_DIR/make_synthetic_arm_image.py" --out "$IMG" --json \
  >"$OUT_DIR/synthetic_arm.json" || { log "falha ao gerar a imagem"; exit 1; }
cat "$OUT_DIR/synthetic_arm.json"

# O entry point precisa ser 4-byte aligned (0x08000000) e o arquivo é mapeado
# inteiro a partir dele (REA raw-binary / Ghidra BinaryLoader).
run_rea() { # run_rea <saida.json> <comando...>
  local out="$1"; shift
  log "rea $*"
  if ! rea "$@" >"$out" 2>"$out.err"; then
    log "comando falhou; últimas linhas do erro:"
    tail -n 20 "$out.err" >&2 || true
    return 1
  fi
  return 0
}

STATUS=0

if run_rea "$OUT_DIR/rea_inspect.json" inspect "$IMG" \
      --target-format raw-binary --architecture arm --entry-point 0x8000000 \
      --provider ghidra --format json; then
  log "inspect OK ($(wc -c <"$OUT_DIR/rea_inspect.json") bytes de evidência)"
else
  STATUS=1
fi

if run_rea "$OUT_DIR/rea_function_entry.json" function "$IMG" 0x8000000 \
      --target-format raw-binary --architecture arm --entry-point 0x8000000 \
      --provider ghidra --format json; then
  log "function entry OK"
else
  STATUS=1
fi

if run_rea "$OUT_DIR/rea_function_bag.json" function "$IMG" 0x800002c \
      --target-format raw-binary --architecture arm --entry-point 0x8000000 \
      --provider ghidra --format json; then
  log "function sub_bag OK"
else
  STATUS=1
fi

# --- verificação das evidências ---------------------------------------------
if [ "$STATUS" -eq 0 ]; then
  python3 - "$OUT_DIR" <<'PY' || STATUS=1
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
problems = []

inspect_path = out / "rea_inspect.json"
try:
    inspect_doc = json.loads(inspect_path.read_text(encoding="utf-8"))
except Exception as exc:  # noqa: BLE001
    problems.append(f"inspect: JSON inválido ({exc})")
    inspect_doc = None

for name in ("rea_function_entry.json", "rea_function_bag.json"):
    path = out / name
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        problems.append(f"{name}: JSON inválido ({exc})")
        continue
    raw = path.read_text(encoding="utf-8").lower()
    if "0x80000" not in raw:
        problems.append(f"{name}: não cita nenhum endereço 0x80000xxx")
    if not any(key in raw for key in ("c_code", "pseudo", "decompil", "c_code", "instructions")):
        problems.append(f"{name}: sem campo de código/instruções reconhecível")

if inspect_doc is not None and not inspect_doc:
    problems.append("inspect: documento vazio")

if problems:
    print("[smoke] FALHA nas evidências:")
    for item in problems:
        print(f"  - {item}")
    raise SystemExit(1)

print("[smoke] evidências OK: JSON válido com endereços e código/instruções")
PY
fi

if [ "$STATUS" -eq 0 ]; then
  log "SMOKE TEST PASSOU — evidências em $OUT_DIR"
else
  log "SMOKE TEST FALHOU — veja $OUT_DIR/*.err e o diagnóstico em scripts/re_tools_check.sh"
fi
exit "$STATUS"
