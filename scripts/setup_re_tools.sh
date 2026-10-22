#!/usr/bin/env bash
# =============================================================================
# setup_re_tools.sh — prepara o ambiente de engenharia reversa deste projeto
# =============================================================================
# Instala, FORA do repositório (padrão: ~/.local/opt/re-tools):
#
#   * REA 6.7.0 (pacote npm `rea-agents`)       -> CLI + servidor MCP de RE
#   * Ghidra 12.1.4 PUBLIC (release oficial)    -> engine do provider "ghidra"
#   * Eclipse Temurin JDK 21.0.13+9 (Linux x64) -> JDK completo exigido pelos dois
#
# Por que JDK 21 e não 17/25?
#   - Ghidra 12.1.4 declara application.java.min=21 e application.java.max vazio
#     (aceita >= 21). Ele exige um JDK COMPLETO: precisa de `javac` para compilar
#     os scripts Java, incluindo a bridge do REA. Uma JRE é recusada.
#   - O REA aceita "a 64-bit full JDK 21 or newer".
#
# Por que Ghidra 12.1.4 e não 12.2 (mais nova)?
#   - O REA 6.7.0 valida explicitamente a série 12.1.x; 12.2 é rejeitada.
#
# Segurança / proveniência:
#   - Somente URLs oficiais (NationalSecurityAgency/ghidra,
#     adoptium/temurin21-binaries).
#   - Ghidra: SHA-256 fixado abaixo, publicado nas release notes oficiais.
#   - JDK: SHA-256 lido do .sha256.txt publicado junto do asset oficial.
#   - Nada é baixado de mirror de terceiro.
#
# Uso:
#   bash scripts/setup_re_tools.sh                # instala tudo
#   bash scripts/setup_re_tools.sh --dry-run      # só mostra o plano
#   bash scripts/setup_re_tools.sh --verify-only  # não instala, só diagnostica
#   bash scripts/setup_re_tools.sh --help
#
# Depois de instalar:
#   source ~/.local/opt/re-tools/env.sh    # ou: source scripts/re_env.sh
#   bash scripts/re_tools_check.sh         # diagnóstico + rea doctor
#
# Idempotente: rodar de novo não reinstala o que já está válido.
# =============================================================================
set -euo pipefail

# --- versões fixadas ---------------------------------------------------------
readonly REA_VERSION="6.7.0"
readonly GHIDRA_VERSION="12.1.4"
readonly GHIDRA_DIR_NAME="ghidra_${GHIDRA_VERSION}_PUBLIC"
readonly GHIDRA_ZIP_NAME="ghidra_${GHIDRA_VERSION}_PUBLIC_20260921.zip"
readonly GHIDRA_URL="https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VERSION}_build/${GHIDRA_ZIP_NAME}"
readonly GHIDRA_SHA256="ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db"
readonly JDK_VERSION="21.0.13+9"
readonly JDK_TARBALL="OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz"
readonly JDK_URL="https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/${JDK_TARBALL}"

# --- estado / opções ---------------------------------------------------------
TOOLS_DIR="${RE_TOOLS_DIR:-$HOME/.local/opt/re-tools}"
NPM_PREFIX="${RE_NPM_PREFIX:-$HOME/.local}"
DRY_RUN=0
VERIFY_ONLY=0
STRICT=0
DO_REA=1
DO_JDK=1
DO_GHIDRA=1
GHIDRA_ZIP_OVERRIDE=""
JDK_TARBALL_OVERRIDE=""
JDK_SHA256_OVERRIDE=""
GHIDRA_DIR_OVERRIDE=""
JDK_HOME_OVERRIDE=""

# --- helpers -----------------------------------------------------------------
log()  { printf '[setup-re] %s\n' "$*" >&2; }
warn() { printf '[setup-re] AVISO: %s\n' "$*" >&2; }
die()  { printf '[setup-re] ERRO: %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# Aspas seguras para escrever no env.sh (o resultado é lido por bash/zsh).
shq() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }

usage() {
  cat <<'EOF'
Uso: bash scripts/setup_re_tools.sh [opções]

Opções:
  --prefix DIR          Onde instalar as ferramentas (padrão: $RE_TOOLS_DIR
                        ou ~/.local/opt/re-tools). Nada vai para dentro do repo.
  --npm-prefix DIR      Prefixo do npm -g para o REA (padrão: ~/.local).
  --skip-rea            Não instala/atualiza o REA.
  --skip-jdk            Não instala o JDK (use se já tem um JDK 21+ em JAVA_HOME).
  --skip-ghidra         Não instala o Ghidra (use com --ghidra-dir).
  --ghidra-dir DIR      Adota uma instalação Ghidra 12.1.x já extraída (não copia).
  --ghidra-zip ARQ      Usa um zip oficial já baixado (o SHA-256 é conferido).
  --jdk-home DIR        Adota um JDK 21+ já extraído (não copia).
  --jdk-tarball ARQ     Usa um tar.gz oficial do Temurin já baixado.
  --jdk-sha256 HEX      SHA-256 esperado do tar.gz do JDK (padrão: baixa o
                        .sha256.txt oficial que acompanha o asset).
  --verify-only         Não instala nada; só roda as verificações.
  --strict              Sai com código 1 se a verificação final falhar.
  --dry-run             Mostra o plano e sai sem tocar em nada.
  -h, --help            Esta ajuda.

Requisitos: Linux x86_64, curl, tar, unzip, Node.js 22.19+/24.11+/26+ (npm).
Não usa sudo: tudo fica sob o seu HOME.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix)      TOOLS_DIR="${2:?--prefix exige um valor}"; shift 2 ;;
    --npm-prefix)  NPM_PREFIX="${2:?--npm-prefix exige um valor}"; shift 2 ;;
    --skip-rea)    DO_REA=0; shift ;;
    --skip-jdk)    DO_JDK=0; shift ;;
    --skip-ghidra) DO_GHIDRA=0; shift ;;
    --ghidra-dir)  GHIDRA_DIR_OVERRIDE="${2:?--ghidra-dir exige um valor}"; shift 2 ;;
    --ghidra-zip)  GHIDRA_ZIP_OVERRIDE="${2:?--ghidra-zip exige um valor}"; shift 2 ;;
    --jdk-home)    JDK_HOME_OVERRIDE="${2:?--jdk-home exige um valor}"; shift 2 ;;
    --jdk-tarball) JDK_TARBALL_OVERRIDE="${2:?--jdk-tarball exige um valor}"; shift 2 ;;
    --jdk-sha256)  JDK_SHA256_OVERRIDE="${2:?--jdk-sha256 exige um valor}"; shift 2 ;;
    --verify-only) VERIFY_ONLY=1; shift ;;
    --strict)      STRICT=1; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    *)             usage >&2; die "opção desconhecida: $1" ;;
  esac
done

# Resolve o que usar: --*-dir/--*-home > variável de ambiente já válida > padrão.
if [ -n "$JDK_HOME_OVERRIDE" ]; then
  JDK_HOME="$JDK_HOME_OVERRIDE"
elif [ -n "${JAVA_HOME:-}" ] && [ -x "${JAVA_HOME}/bin/javac" ]; then
  JDK_HOME="$JAVA_HOME"
else
  JDK_HOME="$TOOLS_DIR/jdk-$JDK_VERSION"
fi

if [ -n "$GHIDRA_DIR_OVERRIDE" ]; then
  GHIDRA_DIR="$GHIDRA_DIR_OVERRIDE"
elif [ -n "${GHIDRA_INSTALL_DIR:-}" ] && [ -f "${GHIDRA_INSTALL_DIR}/Ghidra/application.properties" ]; then
  GHIDRA_DIR="$GHIDRA_INSTALL_DIR"
else
  GHIDRA_DIR="$TOOLS_DIR/$GHIDRA_DIR_NAME"
fi

CACHE_DIR="$TOOLS_DIR/.cache"

# --- utilidades --------------------------------------------------------------
sha256_of() {
  if have sha256sum; then sha256sum "$1" | awk '{print $1}'
  elif have shasum;   then shasum -a 256 "$1" | awk '{print $1}'
  else return 1; fi
}

is_sha256() { printf '%s' "$1" | grep -Eq '^[0-9a-f]{64}$'; }

ghidra_version_of() {
  local props="$1/Ghidra/application.properties"
  if [ -f "$props" ]; then
    awk -F= '/^application.version=/{print $2; found=1} END{if(!found) print "desconhecido"}' "$props"
  else
    printf 'ausente'
  fi
}

require_platform() {
  local os arch
  os="$(uname -s)"; arch="$(uname -m)"
  case "$os/$arch" in
    Linux/x86_64|Linux/amd64) return 0 ;;
    *)
      die "este script cobre Linux x86_64 (encontrado: $os/$arch).
      Para macOS/Windows use a instalação manual descrita em docs/REA_GHIDRA.md."
      ;;
  esac
}

require_tools() {
  local missing=0 c
  for c in curl tar unzip; do
    if ! have "$c"; then warn "falta o comando obrigatório: $c"; missing=1; fi
  done
  if [ "$DO_REA" = 1 ] && ! have npm; then
    warn "falta npm/Node.js (REA exige Node 22.19+/24.11+/26+)"; missing=1
  fi
  if ! have sha256sum && ! have shasum; then
    warn "falta sha256sum (ou shasum) para conferir integridade"; missing=1
  fi
  if [ "$missing" -ne 0 ]; then
    die "instale as dependências acima e rode de novo."
  fi
  return 0
}

download() { # download <url> <destino>
  local url="$1" dest="$2"
  if [ -s "$dest" ]; then
    log "cache: $dest"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  log "baixando: $url"
  if [ "$DRY_RUN" = 1 ]; then
    log "[dry-run] curl -fL --retry 3 -o $dest $url"
    return 0
  fi
  curl -fL --retry 3 --retry-delay 2 --connect-timeout 20 -o "$dest.part" "$url" \
    || die "falha ao baixar $url"
  mv "$dest.part" "$dest"
}

verify_sha256() { # verify_sha256 <arquivo> <sha esperado> <rótulo>
  local file="$1" expected="$2" label="$3" got
  is_sha256 "$expected" || die "$label: SHA-256 esperado inválido ('$expected')."
  got="$(sha256_of "$file")" || die "não foi possível calcular SHA-256 (sha256sum/shasum ausente)."
  if [ "$got" != "$expected" ]; then
    die "$label: SHA-256 divergente.
      esperado: $expected
      obtido:   $got
      arquivo:  $file
    Apague o arquivo e baixe de novo da fonte oficial."
  fi
  log "$label: SHA-256 confere ($got)"
}

# --- instalação do REA -------------------------------------------------------
install_rea() {
  if have rea; then
    local cur
    cur="$(rea --version 2>/dev/null || true)"
    if [ "$cur" = "$REA_VERSION" ]; then
      log "REA já instalado: $cur"
      return 0
    fi
    log "REA encontrado em versão diferente (${cur:-?}); instalando $REA_VERSION"
  fi
  log "instalando rea-agents@$REA_VERSION em $NPM_PREFIX"
  if [ "$DRY_RUN" = 1 ]; then
    log "[dry-run] npm install --global --prefix $NPM_PREFIX rea-agents@$REA_VERSION"
    return 0
  fi
  npm install --global --prefix "$NPM_PREFIX" "rea-agents@$REA_VERSION" \
    || die "npm não conseguiu instalar rea-agents@$REA_VERSION"
  if [ ! -x "$NPM_PREFIX/bin/rea" ]; then
    die "rea não apareceu em $NPM_PREFIX/bin/rea"
  fi
  log "REA instalado: $("$NPM_PREFIX/bin/rea" --version)"
}

# --- instalação do JDK -------------------------------------------------------
jdk_expected_sha() {
  if [ -n "$JDK_SHA256_OVERRIDE" ]; then
    printf '%s\n' "$JDK_SHA256_OVERRIDE"
    return 0
  fi
  local txt="$CACHE_DIR/${JDK_TARBALL}.sha256.txt"
  if [ "$DRY_RUN" = 1 ]; then
    log "[dry-run] baixaria ${JDK_URL}.sha256.txt para conferir o JDK"
    printf '%s\n' "0000000000000000000000000000000000000000000000000000000000000000"
    return 0
  fi
  download "${JDK_URL}.sha256.txt" "$txt"
  awk 'NR==1{print $1}' "$txt"
}

install_jdk() {
  if [ -n "$JDK_HOME_OVERRIDE" ]; then
    if [ ! -x "$JDK_HOME_OVERRIDE/bin/javac" ]; then
      die "--jdk-home $JDK_HOME_OVERRIDE não tem bin/javac (precisa ser um JDK completo, não JRE)"
    fi
    log "usando JDK externo: $JDK_HOME_OVERRIDE"
    return 0
  fi
  if [ -x "$JDK_HOME/bin/javac" ]; then
    log "JDK já instalado: $JDK_HOME"
    return 0
  fi
  log "instalando Temurin JDK $JDK_VERSION em $JDK_HOME"
  local tarball="$JDK_TARBALL_OVERRIDE"
  if [ -z "$tarball" ]; then
    tarball="$CACHE_DIR/$JDK_TARBALL"
    download "$JDK_URL" "$tarball"
  fi
  if [ "$DRY_RUN" = 1 ]; then
    log "[dry-run] conferiria SHA-256 e extrairia $tarball em $JDK_HOME"
    return 0
  fi
  local expected
  expected="$(jdk_expected_sha)"
  verify_sha256 "$tarball" "$expected" "Temurin JDK $JDK_VERSION"

  local tmp inner
  tmp="$(mktemp -d)"
  if ! tar -xzf "$tarball" -C "$tmp"; then
    rm -rf "$tmp"
    die "falha ao extrair $tarball"
  fi
  inner="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  if [ -z "$inner" ]; then
    rm -rf "$tmp"
    die "tar.gz do JDK não contém um diretório raiz"
  fi
  rm -rf "$JDK_HOME"
  mkdir -p "$(dirname "$JDK_HOME")"
  mv "$inner" "$JDK_HOME"
  rm -rf "$tmp"
  if [ ! -x "$JDK_HOME/bin/javac" ]; then
    die "JDK extraído sem bin/javac — pacote inesperado"
  fi
  log "JDK instalado: $("$JDK_HOME/bin/java" -version 2>&1 | head -n1)"
}

# --- instalação do Ghidra ----------------------------------------------------
install_ghidra() {
  if [ -n "$GHIDRA_DIR_OVERRIDE" ]; then
    if [ ! -f "$GHIDRA_DIR_OVERRIDE/Ghidra/application.properties" ]; then
      die "--ghidra-dir $GHIDRA_DIR_OVERRIDE não parece uma instalação Ghidra (falta Ghidra/application.properties)"
    fi
    log "usando Ghidra externo: $GHIDRA_DIR_OVERRIDE ($(ghidra_version_of "$GHIDRA_DIR_OVERRIDE"))"
    return 0
  fi
  if [ -f "$GHIDRA_DIR/Ghidra/application.properties" ]; then
    log "Ghidra já instalado: $GHIDRA_DIR ($(ghidra_version_of "$GHIDRA_DIR"))"
    return 0
  fi
  log "instalando Ghidra $GHIDRA_VERSION em $TOOLS_DIR"
  local zip="$GHIDRA_ZIP_OVERRIDE"
  if [ -z "$zip" ]; then
    zip="$CACHE_DIR/$GHIDRA_ZIP_NAME"
    download "$GHIDRA_URL" "$zip"
  fi
  if [ "$DRY_RUN" = 1 ]; then
    log "[dry-run] conferiria SHA-256 de $zip e extrairia em $TOOLS_DIR"
    return 0
  fi
  verify_sha256 "$zip" "$GHIDRA_SHA256" "Ghidra $GHIDRA_VERSION"
  mkdir -p "$TOOLS_DIR"
  unzip -q -o "$zip" -d "$TOOLS_DIR" || die "falha ao extrair $zip"
  if [ ! -f "$GHIDRA_DIR/Ghidra/application.properties" ]; then
    die "extração não produziu $GHIDRA_DIR/Ghidra/application.properties"
  fi
  log "Ghidra instalado: $GHIDRA_DIR ($(ghidra_version_of "$GHIDRA_DIR"))"
}

# --- env.sh ------------------------------------------------------------------
write_env() {
  local env_file="$TOOLS_DIR/env.sh"
  if [ "$DRY_RUN" = 1 ]; then
    log "[dry-run] escreveria $env_file"
    return 0
  fi
  mkdir -p "$TOOLS_DIR"
  {
    printf '# Gerado por scripts/setup_re_tools.sh — não edite à mão.\n'
    printf '# Uso: source %s\n' "$env_file"
    printf 'export RE_TOOLS_DIR=%s\n' "$(shq "$TOOLS_DIR")"
    if [ -x "$JDK_HOME/bin/javac" ]; then
      printf 'export JAVA_HOME=%s\n' "$(shq "$JDK_HOME")"
      # shellcheck disable=SC2016  # $PATH é literal: vai para o env.sh
      printf 'case ":$PATH:" in *":%s/bin:"*) ;; *) PATH="%s/bin:$PATH" ;; esac\n' \
        "$JDK_HOME" "$JDK_HOME"
    fi
    if [ -f "$GHIDRA_DIR/Ghidra/application.properties" ]; then
      printf 'export GHIDRA_INSTALL_DIR=%s\n' "$(shq "$GHIDRA_DIR")"
      # shellcheck disable=SC2016  # $PATH é literal: vai para o env.sh
      printf 'case ":$PATH:" in *":%s/support:"*) ;; *) PATH="%s/support:$PATH" ;; esac\n' \
        "$GHIDRA_DIR" "$GHIDRA_DIR"
    fi
    # shellcheck disable=SC2016  # $PATH é literal: vai para o env.sh
    printf 'case ":$PATH:" in *":%s/bin:"*) ;; *) PATH="%s/bin:$PATH" ;; esac\n' \
      "$NPM_PREFIX" "$NPM_PREFIX"
    printf 'export PATH\n'
  } >"$env_file"
  chmod 644 "$env_file"
  log "ambiente gravado em $env_file"
}

# --- verificação -------------------------------------------------------------
provider_available() { # provider_available <json>
  local json="$1"
  if have python3; then
    python3 - "$json" <<'PY'
import json, sys
try:
    doc = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    raise SystemExit(2)
prov = next((p for p in doc.get("providerInspections", []) if p.get("id") == "ghidra"), {})
raise SystemExit(0 if prov.get("available") else 1)
PY
  else
    grep -q '"id":"ghidra"[^}]*"available":true' "$json"
  fi
}

doctor_summary() { # doctor_summary <json>
  local json="$1"
  if have python3; then
    python3 - "$json" <<'PY'
import json, sys
try:
    doc = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception as exc:  # noqa: BLE001
    print(f"  não foi possível ler o JSON do rea doctor: {exc}")
    raise SystemExit(0)
checks = {c["name"]: c for c in doc.get("checks", [])}
prov = next((p for p in doc.get("providerInspections", []) if p.get("id") == "ghidra"), {})
print(f"  rea doctor: healthy={doc.get('healthy')} provider_ghidra_available={prov.get('available')}")
for name in ("node", "ghidra", "ghidra-version", "ghidra-headless",
             "ghidra-native_decompiler", "ghidra-java", "skill:identity"):
    check = checks.get(name)
    if check is None:
        continue
    mark = "OK   " if check.get("ok") else "FALHA"
    print(f"  [{mark}] {name}: {check.get('detail', '')}")
PY
  else
    printf '  rea doctor: (python3 ausente — JSON bruto em %s)\n' "$json"
  fi
}

verify_all() {
  local failures=0 json
  log "verificando instalação"
  if [ "$DRY_RUN" = 1 ]; then
    log "[dry-run] pulando verificação real"
    return 0
  fi

  if [ -f "$TOOLS_DIR/env.sh" ]; then
    # shellcheck disable=SC1090,SC1091
    . "$TOOLS_DIR/env.sh"
  else
    warn "env.sh ainda não existe (nada instalado?)"
    failures=$((failures + 1))
  fi

  if [ -x "${JAVA_HOME:-/nonexistent}/bin/java" ]; then
    log "java:  $("${JAVA_HOME}/bin/java" -version 2>&1 | head -n1)"
  else
    warn "JAVA_HOME ausente ou inválido"; failures=$((failures + 1))
  fi
  if [ -x "${JAVA_HOME:-/nonexistent}/bin/javac" ]; then
    log "javac: $("${JAVA_HOME}/bin/javac" -version 2>&1 | head -n1)"
  else
    warn "javac ausente — Ghidra e REA exigem JDK completo (JRE não serve)"; failures=$((failures + 1))
  fi
  if [ -f "${GHIDRA_INSTALL_DIR:-/nonexistent}/Ghidra/application.properties" ]; then
    log "ghidra: $(ghidra_version_of "${GHIDRA_INSTALL_DIR}")"
  else
    warn "GHIDRA_INSTALL_DIR ausente ou inválido"; failures=$((failures + 1))
  fi
  if have rea; then
    log "rea:   $(rea --version)"
  else
    warn "comando rea não está no PATH (esperado: $NPM_PREFIX/bin)"; failures=$((failures + 1))
  fi

  if [ "$failures" -eq 0 ] && have rea; then
    json="$(mktemp)"
    rea doctor --provider ghidra --json >"$json" 2>/dev/null || true
    doctor_summary "$json"
    if ! provider_available "$json"; then
      warn "provider ghidra indisponível — veja o resumo acima"
      failures=$((failures + 1))
    fi
    rm -f "$json"
  fi

  if [ "$failures" -gt 0 ]; then
    warn "verificação com $failures pendência(s); detalhes: bash scripts/re_tools_check.sh"
    if [ "$STRICT" = 1 ]; then return 1; fi
    return 0
  fi
  log "tudo pronto."
  return 0
}

# --- main --------------------------------------------------------------------
main() {
  log "plano: REA=$([ "$DO_REA" = 1 ] && echo "$REA_VERSION" || echo skip) JDK=$([ "$DO_JDK" = 1 ] && echo "$JDK_VERSION" || echo skip) Ghidra=$([ "$DO_GHIDRA" = 1 ] && echo "$GHIDRA_VERSION" || echo skip)"
  log "destino: $TOOLS_DIR (npm prefix: $NPM_PREFIX)"
  log "JDK:     $JDK_HOME"
  log "Ghidra:  $GHIDRA_DIR"
  if [ "$DRY_RUN" = 1 ]; then
    log "modo dry-run: nada será baixado/instalado"
  fi

  require_platform
  if [ "$VERIFY_ONLY" -eq 0 ]; then
    require_tools
    if [ "$DO_REA" -eq 1 ]; then install_rea; fi
    if [ "$DO_JDK" -eq 1 ]; then install_jdk; fi
    if [ "$DO_GHIDRA" -eq 1 ]; then install_ghidra; fi
  fi
  write_env
  verify_all

  cat <<EOF

Próximos passos:
  1) source $TOOLS_DIR/env.sh          # (ou: source scripts/re_env.sh)
  2) bash scripts/re_tools_check.sh    # diagnóstico completo
  3) bash scripts/rea_ghidra_smoke.sh  # teste ponta-a-ponta com imagem ARM sintética
  4) rea setup                         # (opcional) registra o MCP no seu agente
EOF
}

main "$@"
