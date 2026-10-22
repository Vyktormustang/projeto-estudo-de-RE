#!/usr/bin/env bash
# =============================================================================
# ghidra_import_gba.sh — importa uma ROM de GBA no Ghidra já configurada
# =============================================================================
# O que faz, em ordem:
#   1. confere o stack (JDK completo + Ghidra 12.1.x + linguagem ARM:LE:32:v4t);
#   2. valida o cabeçalho da ROM *antes* de importar (scripts/gba_rom_header.py);
#   3. importa com BinaryLoader em 0x08000000 usando a linguagem ARMv4T;
#   4. roda o pre-script GbaPrepareProgram.java (mapa de memória, cabeçalho,
#      rótulos e seeds ARM/Thumb) ANTES da auto-análise;
#   5. roda o post-script (contagem de funções, âncoras, evidências JSON);
#   6. compara o cabeçalho lido pelo Python com o lido pelo Ghidra
#      (cross-check de implementação independente).
#
# A ROM NÃO é copiada nem versionada. O projeto Ghidra fica fora do repo
# (~/.local/opt/re-tools/ghidra-projects) e as evidências em reports/ghidra/.
#
# Uso
#   bash scripts/ghidra_import_gba.sh rom/FireRed.gba
#   bash scripts/ghidra_import_gba.sh --rom rom/FireRed.gba --no-analysis
#   bash scripts/ghidra_import_gba.sh --self-test        # não precisa de ROM
#   bash scripts/ghidra_import_gba.sh --rom jogo.gba --dry-run
#
# Códigos de saída: 0 ok · 1 falhou · 2 uso · 3 pré-requisitos ausentes
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)"

ROM=""
PROJECT_DIR="${GHIDRA_PROJECTS_DIR:-$HOME/.local/opt/re-tools/ghidra-projects}"
PROJECT_NAME=""
EVIDENCE_DIR="$REPO_ROOT/reports/ghidra"
ANALYSIS_TIMEOUT=1800
MAX_RUNTIME=""
NO_ANALYSIS=0
MIRRORS=0
REUSE=0
DRY_RUN=0
SELF_TEST=0
ALLOW_INVALID_HEADER=0
LANGUAGE_ID="ARM:LE:32:v4t"
ROM_BASE="0x08000000"
ROM_BLOCK_NAME="GBA_ROM"
KEEP_TEMP=0
SELF_TEST_FAILURES=0

log()  { printf '[ghidra-import] %s\n' "$*" >&2; }
warn() { printf '[ghidra-import] AVISO: %s\n' "$*" >&2; }
die()  { printf '[ghidra-import] ERRO: %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

usage() {
  cat <<'EOF'
Uso: bash scripts/ghidra_import_gba.sh <rom.gba> [opções]
     bash scripts/ghidra_import_gba.sh --self-test

Opções:
  --rom ARQ              ROM de GBA (ou passe como primeiro argumento).
  --project-dir DIR      Onde criar o projeto Ghidra
                         (padrão: $GHIDRA_PROJECTS_DIR ou ~/.local/opt/re-tools/ghidra-projects).
  --project-name NOME    Nome do projeto (padrão: gba_<sha256[:8]>).
  --evidence DIR         Onde gravar JSONs/logs (padrão: reports/ghidra).
  --no-analysis          Importa e roda scripts sem auto-análise (rápido).
  --mirrors              Mapeia também os mirrors de barramento 0x0A/0x0C/0x0E.
  --reuse                Reabre o programa existente (-process) em vez de reimportar.
  --timeout SEG          Timeout de análise por arquivo (padrão: 1800).
  --max-runtime SEG      Mata o processo inteiro depois de SEG (padrão: sem limite).
  --allow-invalid-header Não aborta se o cabeçalho não validar (útil para ROM hack).
  --dry-run              Só mostra o comando que seria executado.
  --self-test            Valida ferramentas + faz um import completo da ROM sintética.
  --keep-temp            Mantém o projeto temporário do self-test.
  -h, --help             Esta ajuda.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --rom)                  ROM="${2:?--rom exige um caminho}"; shift 2 ;;
    --project-dir)          PROJECT_DIR="${2:?}"; shift 2 ;;
    --project-name)         PROJECT_NAME="${2:?}"; shift 2 ;;
    --evidence)             EVIDENCE_DIR="${2:?}"; shift 2 ;;
    --no-analysis)          NO_ANALYSIS=1; shift ;;
    --mirrors)              MIRRORS=1; shift ;;
    --reuse)                REUSE=1; shift ;;
    --timeout)              ANALYSIS_TIMEOUT="${2:?}"; shift 2 ;;
    --max-runtime)          MAX_RUNTIME="${2:?}"; shift 2 ;;
    --allow-invalid-header) ALLOW_INVALID_HEADER=1; shift ;;
    --dry-run)              DRY_RUN=1; shift ;;
    --self-test)            SELF_TEST=1; shift ;;
    --keep-temp)            KEEP_TEMP=1; shift ;;
    -h|--help)              usage; exit 0 ;;
    -*)                     usage >&2; die "opção desconhecida: $1" ;;
    *)
      if [ -z "$ROM" ]; then ROM="$1"; else usage >&2; die "argumento extra: $1"; fi
      shift ;;
  esac
done

# ---------------------------------------------------------------------------
# Pré-requisitos
# ---------------------------------------------------------------------------
# shellcheck disable=SC1091
. "$SCRIPT_DIR/re_env.sh"

check_stack() { # check_stack <strict:0|1>
  local strict="$1" missing=0

  if [ ! -x "${JAVA_HOME:-/nonexistent}/bin/javac" ]; then
    log "pré-requisito ausente: JDK completo (JAVA_HOME/bin/javac)"
    missing=1
  fi
  if [ ! -x "${JAVA_HOME:-/nonexistent}/bin/java" ]; then
    log "pré-requisito ausente: JAVA_HOME/bin/java"
    missing=1
  fi
  if [ ! -x "${GHIDRA_INSTALL_DIR:-/nonexistent}/support/analyzeHeadless" ]; then
    log "pré-requisito ausente: GHIDRA_INSTALL_DIR/support/analyzeHeadless"
    missing=1
  fi
  if [ -f "${GHIDRA_INSTALL_DIR:-/nonexistent}/Ghidra/application.properties" ]; then
    local version
    version="$(awk -F= '/^application.version=/{print $2}' \
      "$GHIDRA_INSTALL_DIR/Ghidra/application.properties")"
    case "$version" in
      12.1.*) : ;;
      *) log "Ghidra $version não está na série 12.1.x (pin do projeto)"; missing=1 ;;
    esac
  else
    missing=1
  fi

  local ldefs="${GHIDRA_INSTALL_DIR:-/nonexistent}/Ghidra/Processors/ARM/data/languages/ARM.ldefs"
  if [ -f "$ldefs" ]; then
    if ! grep -q "id=\"$LANGUAGE_ID\"" "$ldefs"; then
      log "linguagem $LANGUAGE_ID não existe nesta instalação do Ghidra"
      missing=1
    fi
  else
    warn "ARM.ldefs não encontrado; não foi possível confirmar a linguagem $LANGUAGE_ID"
  fi

  if [ "$missing" -ne 0 ]; then
    log "nada foi importado. Instale/repare com: bash scripts/setup_re_tools.sh"
    log "diagnóstico:                        bash scripts/re_tools_check.sh"
    [ "$strict" = 1 ] && exit 3
    return 3
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Montagem do comando
# ---------------------------------------------------------------------------
build_command() { # build_command <rom> <project_dir> <project_name> <evidence> <out_array_name>
  local rom="$1" proj_dir="$2" proj_name="$3" evidence="$4"
  local -n out="$5"
  local headless="$GHIDRA_INSTALL_DIR/support/analyzeHeadless"
  local program_name
  program_name="$(basename "$rom")"

  out=("$headless" "$proj_dir" "$proj_name")

  if [ "$REUSE" = 1 ]; then
    out+=(-process "$program_name")
  else
    out+=(-import "$rom"
          -processor "$LANGUAGE_ID"
          -loader BinaryLoader
          -loader-baseAddr "$ROM_BASE"
          -loader-blockName "$ROM_BLOCK_NAME")
  fi

  out+=(-scriptPath "$SCRIPT_DIR/ghidra_scripts")

  local pre_args=(pre "$evidence")
  [ "$MIRRORS" = 1 ] && pre_args+=(--mirrors)
  out+=(-preScript "GbaPrepareProgram.java" "${pre_args[@]}")
  out+=(-postScript "GbaPrepareProgram.java" post "$evidence")

  [ "$NO_ANALYSIS" = 1 ] && out+=(-noanalysis)
  [ "$REUSE" = 0 ] && out+=(-overwrite)

  out+=(-analysisTimeoutPerFile "$ANALYSIS_TIMEOUT")
  if have nproc; then
    out+=(-max-cpu "$(nproc)")
  fi
  out+=(-log "$evidence/analyzeHeadless.log")
  out+=(-scriptlog "$evidence/ghidra_scripts.log")
}

print_command() {
  local -n __argv_ref="$1"
  printf 'COMANDO:\n  '
  printf '%q ' "${__argv_ref[@]}"
  printf '\n'
}

# ---------------------------------------------------------------------------
# Execução do import
# ---------------------------------------------------------------------------
run_import() { # run_import <rom> <project_dir> <project_name> <evidence> <expect_full:0|1>
  local rom="$1" proj_dir="$2" proj_name="$3" evidence="$4" expect_full="$5"
  local cmd=()

  mkdir -p "$evidence" "$proj_dir" || die "não foi possível criar $evidence / $proj_dir"
  build_command "$rom" "$proj_dir" "$proj_name" "$evidence" cmd

  if [ "$DRY_RUN" = 1 ]; then
    print_command cmd
    return 0
  fi

  log "projeto:    $proj_dir/$proj_name"
  log "evidências: $evidence"
  print_command cmd >&2

  local -a runner=()
  if [ -n "$MAX_RUNTIME" ] && have timeout; then
    runner=(timeout --signal=TERM --kill-after=60 "$MAX_RUNTIME")
  fi

  local start_ts end_ts status
  start_ts="$(date +%s)"
  "${runner[@]}" "${cmd[@]}" 2>&1 | tee "$evidence/analyzeHeadless.console.log"
  status="${PIPESTATUS[0]}"
  end_ts="$(date +%s)"

  if [ "$status" -ne 0 ]; then
    warn "analyzeHeadless terminou com código $status (veja $evidence/analyzeHeadless.console.log)"
    return 1
  fi
  log "analyzeHeadless OK em $((end_ts - start_ts))s"

  # ---- verificações de saída ---------------------------------------------
  local pre_json="$evidence/gba_prepare_pre.json"
  local post_json="$evidence/gba_prepare_post.json"
  local failed=0

  if [ ! -s "$pre_json" ]; then
    warn "pre-script não gerou $pre_json"
    failed=1
  elif ! python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$pre_json" 2>/dev/null; then
    warn "$pre_json não é JSON válido"
    failed=1
  fi

  if [ "$expect_full" = 1 ]; then
    if [ ! -s "$post_json" ]; then
      warn "post-script não gerou $post_json"
      failed=1
    elif ! python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$post_json" 2>/dev/null; then
      warn "$post_json não é JSON válido"
      failed=1
    fi
  fi

  # Rom block presente?
  if [ -s "$pre_json" ]; then
    if ! python3 - "$pre_json" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
block = doc.get("rom_block") or {}
size = block.get("size") or 0
sys.exit(0 if size > 0 else 1)
PY
    then
      warn "o bloco da ROM não foi encontrado no programa (import falhou?)"
      failed=1
    fi
  fi

  # Cross-check Python x Ghidra (cabeçalho)
  if [ -s "$pre_json" ]; then
    log "cross-check do cabeçalho (Python x Ghidra)"
    if ! python3 "$SCRIPT_DIR/gba_rom_header.py" "$rom" --compare "$pre_json"; then
      failed=1
    fi
  fi

  # Resumo do post-script
  if [ -s "$post_json" ]; then
    python3 - "$post_json" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
analysis = doc.get("analysis") or {}
print(f"[ghidra-import] funções: {analysis.get('function_count')} "
      f"| símbolos: {analysis.get('symbol_count')} "
      f"| refs (destino/fonte): {analysis.get('reference_destination_count')}/"
      f"{analysis.get('reference_source_count')}")
found = analysis.get("anchors_found") or []
missing = analysis.get("anchors_missing") or []
print(f"[ghidra-import] âncoras encontradas: {', '.join(found) if found else '(nenhuma)'}")
if missing:
    print(f"[ghidra-import] AVISO âncoras ausentes: {', '.join(missing)}")
PY
  fi

  [ "$failed" -eq 0 ] || return 1
  return 0
}

# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
self_test() {
  log "== self-test offline =="
  if python3 "$SCRIPT_DIR/gba_rom_header.py" --self-test; then
    :
  else
    warn "gba_rom_header.py --self-test falhou"
    SELF_TEST_FAILURES=$((SELF_TEST_FAILURES + 1))
  fi
  if python3 "$SCRIPT_DIR/make_synthetic_arm_image.py" --self-test; then
    :
  else
    warn "make_synthetic_arm_image.py --self-test falhou"
    SELF_TEST_FAILURES=$((SELF_TEST_FAILURES + 1))
  fi

  log "== stack =="
  if ! check_stack 0; then
    warn "stack incompleto: a parte Ghidra do self-test foi PULADA (não é falha)."
    if [ "$SELF_TEST_FAILURES" -eq 0 ]; then
      log "self-test: offline OK, headless PULADO"
      return 0
    fi
    log "self-test: $SELF_TEST_FAILURES falha(s) offline"
    return 1
  fi

  local tmp_root
  tmp_root="$(mktemp -d)"
  local evidence="$tmp_root/evidence"
  local proj="$tmp_root/project"
  local rom="$tmp_root/synthetic_gba.gba"
  mkdir -p "$evidence" "$proj"
  python3 "$SCRIPT_DIR/make_synthetic_arm_image.py" --gba-rom --out "$rom" >/dev/null \
    || { warn "não foi possível gerar a ROM sintética"; return 1; }

  log "== Ghidra: self-test das funções puras =="
  local pure_json="$evidence/gba_prepare_selftest.json"
  local pure_cmd=("$GHIDRA_INSTALL_DIR/support/analyzeHeadless" "$proj" selftest
                  -import "$rom" -processor "$LANGUAGE_ID"
                  -loader BinaryLoader -loader-baseAddr "$ROM_BASE"
                  -loader-blockName "$ROM_BLOCK_NAME"
                  -scriptPath "$SCRIPT_DIR/ghidra_scripts"
                  -preScript GbaPrepareProgram.java self-test "$evidence"
                  -noanalysis -overwrite
                  -log "$evidence/selftest.log" -scriptlog "$evidence/selftest_scripts.log")
  if ! "${pure_cmd[@]}" >"$evidence/selftest.console.log" 2>&1; then
    warn "self-test do GbaPrepareProgram falhou"
    tail -n 30 "$evidence/selftest.console.log" >&2
    SELF_TEST_FAILURES=$((SELF_TEST_FAILURES + 1))
  elif grep -q "self-test.*FALHA" "$evidence/selftest.console.log"; then
    warn "self-test do GbaPrepareProgram reportou falha"
    grep "self-test" "$evidence/selftest.console.log" | tail -n 20 >&2
    SELF_TEST_FAILURES=$((SELF_TEST_FAILURES + 1))
  else
    grep "self-test" "$evidence/selftest.console.log" | tail -n 12 >&2 || true
    log "funções puras do Ghidra: OK"
  fi
  [ -s "$pure_json" ] || true  # modo self-test não escreve JSON; só log

  log "== Ghidra: import completo da ROM sintética =="
  NO_ANALYSIS=0
  REUSE=0
  DRY_RUN=0
  if run_import "$rom" "$proj" selfproj "$evidence" 1; then
    log "import completo: OK"
  else
    warn "import completo: FALHOU"
    SELF_TEST_FAILURES=$((SELF_TEST_FAILURES + 1))
  fi

  if [ "$KEEP_TEMP" = 1 ]; then
    log "artefatos do self-test mantidos em $tmp_root"
  else
    rm -rf "$tmp_root"
  fi

  if [ "$SELF_TEST_FAILURES" -eq 0 ]; then
    log "self-test: TUDO OK"
    return 0
  fi
  log "self-test: $SELF_TEST_FAILURES falha(s)"
  return 1
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
main() {
  if [ "$SELF_TEST" = 1 ]; then
    self_test
    exit $?
  fi

  [ -n "$ROM" ] || { usage >&2; die "informe a ROM (posicional ou --rom)"; }
  [ -f "$ROM" ] || die "ROM não encontrada: $ROM"

  if [ "$DRY_RUN" = 0 ]; then
    check_stack 1
  fi

  local rom_abs size sha project_name
  rom_abs="$(CDPATH='' cd -- "$(dirname -- "$ROM")" && pwd)/$(basename -- "$ROM")"
  size="$(wc -c <"$rom_abs" | tr -d ' ')"
  [ "$size" -gt 0 ] || die "arquivo vazio: $rom_abs"
  sha="$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$rom_abs")"

  project_name="${PROJECT_NAME:-gba_${sha:0:8}}"

  mkdir -p "$EVIDENCE_DIR" || die "não foi possível criar $EVIDENCE_DIR"
  log "rom:      $rom_abs ($size bytes, sha256 ${sha:0:16}…)"
  log "projeto:  ${project_name} (dir: $PROJECT_DIR)"

  # 1) validação do cabeçalho fora do Ghidra
  local header_args=("$rom_abs" --out "$EVIDENCE_DIR/rom_header.json")
  [ "$ALLOW_INVALID_HEADER" = 0 ] && header_args+=(--require-valid)
  if ! python3 "$SCRIPT_DIR/gba_rom_header.py" "${header_args[@]}"; then
    if [ "$ALLOW_INVALID_HEADER" = 0 ]; then
      die "cabeçalho inválido (use --allow-invalid-header se for intencional). Detalhes: $EVIDENCE_DIR/rom_header.json"
    fi
    warn "cabeçalho inválido, seguindo por causa de --allow-invalid-header"
  fi

  # 2) import + scripts
  if run_import "$rom_abs" "$PROJECT_DIR" "$project_name" "$EVIDENCE_DIR" 1; then
    if [ "$DRY_RUN" = 1 ]; then
      log "dry-run: nada foi importado (use sem --dry-run para executar)"
      exit 0
    fi
    log "IMPORT CONCLUÍDO"
    log "abra no Ghidra: $GHIDRA_INSTALL_DIR/ghidraRun → projeto $PROJECT_DIR/$project_name"
    log "evidências:    $EVIDENCE_DIR/{rom_header,gba_prepare_pre,gba_prepare_post}.json"
    exit 0
  fi
  die "import FALHOU (veja $EVIDENCE_DIR/analyzeHeadless.console.log)"
}

main "$@"
