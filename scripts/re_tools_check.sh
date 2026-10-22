#!/usr/bin/env bash
# =============================================================================
# re_tools_check.sh — diagnóstico do stack REA + Ghidra (+ JDK) deste projeto
# =============================================================================
# Uso:
#   bash scripts/re_tools_check.sh            # resumo legível; exit 0 = tudo OK
#   bash scripts/re_tools_check.sh --verbose  # inclui o JSON bruto do rea doctor
#   bash scripts/re_tools_check.sh --quiet    # só o resultado final
#
# Códigos de saída:
#   0  tudo pronto (provider ghidra disponível)
#   1  alguma verificação falhou
#   2  uso incorreto
#
# Não instala nada: para instalar use scripts/setup_re_tools.sh.
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)"
VERBOSE=0
QUIET=0

while [ $# -gt 0 ]; do
  case "$1" in
    --verbose|-v) VERBOSE=1; shift ;;
    --quiet|-q)   QUIET=1; shift ;;
    -h|--help)
      sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) printf 'uso: %s [--verbose|--quiet]\n' "$0" >&2; exit 2 ;;
  esac
done

say() { [ "$QUIET" = 1 ] || printf '%s\n' "$*"; }
ok()   { say "  [ OK   ] $*"; }
bad()  { say "  [FALHA ] $*"; }
warn() { say "  [AVISO ] $*"; }

FAILS=0
fail() { FAILS=$((FAILS + 1)); bad "$@"; }

# shellcheck disable=SC1091
. "$SCRIPT_DIR/re_env.sh"

say "== Ferramentas de RE =="
say "   repo:      $REPO_ROOT"
say "   JAVA_HOME: ${JAVA_HOME:-<não encontrado>}"
say "   GHIDRA:    ${GHIDRA_INSTALL_DIR:-<não encontrado>}"
say ""

# --- Node / REA --------------------------------------------------------------
say "-- REA --"
if command -v node >/dev/null 2>&1; then
  node_version="$(node -p 'process.versions.node' 2>/dev/null)"
  case "${node_version%%.*}" in
    22|24) ok "node $node_version" ;;
    *)
      if [ "${node_version%%.*}" -ge 26 ] 2>/dev/null; then
        ok "node $node_version"
      else
        fail "node $node_version (REA exige 22.19+, 24.11+ ou 26+)"
      fi ;;
  esac
else
  fail "node não encontrado no PATH"
fi

if command -v rea >/dev/null 2>&1; then
  ok "rea $(rea --version 2>/dev/null) ($(command -v rea))"
  REA_OK=1
else
  fail "comando rea não encontrado (rode scripts/setup_re_tools.sh)"
  REA_OK=0
fi

# --- JDK ---------------------------------------------------------------------
say ""
say "-- JDK (Ghidra e REA exigem JDK completo, não JRE) --"
if [ -x "${JAVA_HOME:-/nonexistent}/bin/java" ]; then
  ok "java: $("${JAVA_HOME}/bin/java" -version 2>&1 | head -n1)"
else
  fail "java ausente/inválido em JAVA_HOME"
fi
if [ -x "${JAVA_HOME:-/nonexistent}/bin/javac" ]; then
  ok "javac: $("${JAVA_HOME}/bin/javac" -version 2>&1 | head -n1)"
  jmajor="$("${JAVA_HOME}/bin/javac" -version 2>&1 | sed -n 's/^javac \([0-9][0-9]*\).*/\1/p')"
  if [ -n "$jmajor" ] && [ "$jmajor" -ge 21 ]; then
    ok "versão do JDK >= 21"
  else
    fail "JDK reportou versão '${jmajor:-?}' (Ghidra 12.1.4 exige >= 21)"
  fi
else
  fail "javac ausente — Ghidra/REA exigem JDK completo (JRE não serve); use o Temurin JDK 21"
fi

# --- Ghidra ------------------------------------------------------------------
say ""
say "-- Ghidra --"
ghidra_props="${GHIDRA_INSTALL_DIR:-/nonexistent}/Ghidra/application.properties"
if [ -f "$ghidra_props" ]; then
  gversion="$(awk -F= '/^application.version=/{print $2}' "$ghidra_props")"
  gmin="$(awk -F= '/^application.java.min=/{print $2}' "$ghidra_props")"
  grevision="$(awk -F= '/^application.revision.ghidra=/{print $2}' "$ghidra_props")"
  ok "instalação: ${GHIDRA_INSTALL_DIR}"
  ok "versão: ${gversion:-?} (java.min=${gmin:-?})"
  [ -n "$grevision" ] && say "           revision.ghidra=$grevision"
  case "${gversion:-}" in
    12.1.*) ok "série 12.1.x aceita pelo REA 6.7.0" ;;
    *)      fail "versão '$gversion' fora da série 12.1.x aceita pelo REA" ;;
  esac
else
  fail "Ghidra não encontrado (GHIDRA_INSTALL_DIR ausente ou inválido)"
fi

headless="${GHIDRA_INSTALL_DIR:-/nonexistent}/support/analyzeHeadless"
if [ -x "$headless" ]; then
  ok "analyzeHeadless executável"
else
  fail "support/analyzeHeadless ausente ou não executável"
fi

decompiler=""
for cand in "$GHIDRA_INSTALL_DIR"/Ghidra/Features/Decompiler/os/linux_x86_64/decompile \
            "$GHIDRA_INSTALL_DIR"/Ghidra/Features/Decompiler/os/linux_arm_64/decompile \
            "$GHIDRA_INSTALL_DIR"/Ghidra/Features/Decompiler/os/mac_x86_64/decompile \
            "$GHIDRA_INSTALL_DIR"/Ghidra/Features/Decompiler/os/mac_arm_64/decompile; do
  if [ -x "$cand" ]; then decompiler="$cand"; break; fi
done
if [ -n "$decompiler" ]; then
  ok "decompilador nativo: $decompiler"
  if command -v python3 >/dev/null 2>&1; then
    elf_info="$(python3 - "$decompiler" <<'PY'
import struct, sys
path = sys.argv[1]
with open(path, "rb") as fh:
    head = fh.read(20)
if len(head) < 20 or head[:4] != b"\x7fELF":
    print("não-ELF")
    raise SystemExit(0)
cls = {1: "32", 2: "64"}.get(head[4], "?")
machine = struct.unpack("<H", head[18:20])[0]
names = {62: "x86-64", 183: "aarch64"}
print(f"ELF {cls}-bit {names.get(machine, f'machine={machine}')}")
PY
)"
    ok "formato do binário: ${elf_info:-desconhecido}"
  fi
else
  fail "decompilador nativo não encontrado (a instalação pode estar incompleta)"
fi

# --- rea doctor --------------------------------------------------------------
say ""
say "-- rea doctor (provider ghidra) --"
if [ "${REA_OK:-0}" = 1 ]; then
  doctor_json="$(mktemp)"
  rea doctor --provider ghidra --json >"$doctor_json" 2>/dev/null
  if [ "$VERBOSE" = 1 ]; then
    say "   JSON bruto: $doctor_json"
    cat "$doctor_json"
    say ""
  fi
  if command -v python3 >/dev/null 2>&1; then
    summary="$(python3 - "$doctor_json" <<'PY'
import json, sys
try:
    doc = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception as exc:  # noqa: BLE001
    print(f"FALHA ao ler JSON: {exc}")
    raise SystemExit(0)
checks = {c["name"]: c for c in doc.get("checks", [])}
prov = next((p for p in doc.get("providerInspections", []) if p.get("id") == "ghidra"), {})
print(f"healthy={doc.get('healthy')} provider_ghidra_available={prov.get('available')} "
      f"version={prov.get('providerVersion')}")
for name in ("ghidra", "ghidra-version", "ghidra-headless",
             "ghidra-native_decompiler", "ghidra-java"):
    c = checks.get(name)
    if c is None:
        continue
    mark = "OK   " if c.get("ok") else "FALHA"
    print(f"  [{mark}] {name}: {c.get('detail', '')}")
PY
)"
    say "$summary"
    if printf '%s' "$summary" | grep -q 'provider_ghidra_available=True'; then
      ok "provider ghidra disponível"
    else
      fail "provider ghidra indisponível (veja as linhas acima)"
    fi
  else
    if grep -q '"id":"ghidra"[^}]*"available":true' "$doctor_json"; then
      ok "provider ghidra disponível"
    else
      fail "provider ghidra indisponível"
    fi
  fi
  [ "$VERBOSE" = 1 ] || rm -f "$doctor_json"
else
  warn "rea doctor não executado (REA ausente)"
  FAILS=$((FAILS + 1))
fi

say ""
if [ "$FAILS" -eq 0 ]; then
  say "RESULTADO: stack RE pronto (REA + Ghidra + JDK)."
  exit 0
fi
say "RESULTADO: $FAILS verificação(ões) falharam."
say "           Instale/repare com: bash scripts/setup_re_tools.sh"
say "           Guia: docs/REA_GHIDRA.md"
exit 1
