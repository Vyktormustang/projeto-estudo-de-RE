#!/usr/bin/env bash
# =============================================================================
# re_env.sh — carrega o ambiente de RE deste projeto (JAVA_HOME + GHIDRA_INSTALL_DIR)
# =============================================================================
# Uso:
#   source scripts/re_env.sh
#
# O que faz (sem sobrescrever o que você já configurou corretamente):
#   1. JAVA_HOME          -> primeiro JDK 21+ COMPLETO (com bin/javac) encontrado
#   2. GHIDRA_INSTALL_DIR -> primeira instalação Ghidra 12.1.x encontrada
#   3. PATH               -> inclui $JAVA_HOME/bin, $GHIDRA_INSTALL_DIR/support
#                            e ~/.local/bin (onde o npm instala o `rea`)
#
# Ordem de busca:
#   $RE_TOOLS_DIR (se definido) -> <repo>/.re-tools -> ~/.local/opt/re-tools
#   -> ~/opt/* -> ~/.local/opt/* -> ~/ghidra_*_PUBLIC
#
# Variáveis de controle:
#   RE_ENV_VERBOSE=1   imprime um resumo do que foi carregado
#   RE_TOOLS_DIR=...   aponta para outra raiz de ferramentas
#
# Este arquivo é pensado para ser "sourced"; não execute direto.
# =============================================================================

# Não usa `set -e` de propósito: é carregado dentro do shell do usuário.

_re_env_repo_root() {
  # .../scripts/re_env.sh -> .../
  printf '%s\n' "$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")/.." 2>/dev/null && pwd)"
}

_re_env_has_javac() {
  [ -n "${1:-}" ] && [ -x "$1/bin/javac" ] && [ -x "$1/bin/java" ]
}

_re_env_is_ghidra() {
  [ -n "${1:-}" ] && [ -f "$1/Ghidra/application.properties" ] && [ -x "$1/support/analyzeHeadless" ]
}

_re_env_prepend() {
  case ":${PATH}:" in
    *":$1:"*) : ;;
    *) PATH="$1:${PATH}" ;;
  esac
}

_re_env_root="$( _re_env_repo_root )"
_re_env_candidates=""
if [ -n "${RE_TOOLS_DIR:-}" ]; then
  _re_env_candidates="$_re_env_candidates $RE_TOOLS_DIR"
fi
_re_env_candidates="$_re_env_candidates $_re_env_root/.re-tools $HOME/.local/opt/re-tools"
for _d in "$HOME"/opt/* "$HOME"/.local/opt/* "$HOME"/ghidra_*_PUBLIC; do
  [ -e "$_d" ] && _re_env_candidates="$_re_env_candidates $_d"
done

# 1) JAVA_HOME (só troca se o atual não for um JDK completo)
if ! _re_env_has_javac "${JAVA_HOME:-}"; then
  for _d in $_re_env_candidates; do
    if _re_env_has_javac "$_d"; then JAVA_HOME="$_d"; break; fi
    for _j in "$_d"/jdk-* "$_d"/jdk*; do
      if _re_env_has_javac "$_j"; then JAVA_HOME="$_j"; break 2; fi
    done
  done
fi

# 2) GHIDRA_INSTALL_DIR
if ! _re_env_is_ghidra "${GHIDRA_INSTALL_DIR:-}"; then
  for _d in $_re_env_candidates; do
    if _re_env_is_ghidra "$_d"; then GHIDRA_INSTALL_DIR="$_d"; break; fi
    for _g in "$_d"/ghidra_*_PUBLIC "$_d"/ghidra_*; do
      if _re_env_is_ghidra "$_g"; then GHIDRA_INSTALL_DIR="$_g"; break 2; fi
    done
  done
fi

# 3) exports + PATH
if [ -n "${JAVA_HOME:-}" ] && _re_env_has_javac "$JAVA_HOME"; then
  export JAVA_HOME
  _re_env_prepend "$JAVA_HOME/bin"
fi
if [ -n "${GHIDRA_INSTALL_DIR:-}" ] && _re_env_is_ghidra "$GHIDRA_INSTALL_DIR"; then
  export GHIDRA_INSTALL_DIR
  _re_env_prepend "$GHIDRA_INSTALL_DIR/support"
fi
_re_env_prepend "$HOME/.local/bin"
export PATH

if [ "${RE_ENV_VERBOSE:-0}" = "1" ]; then
  printf '[re_env] JAVA_HOME=%s\n' "${JAVA_HOME:-<não encontrado>}"
  printf '[re_env] GHIDRA_INSTALL_DIR=%s\n' "${GHIDRA_INSTALL_DIR:-<não encontrado>}"
  if command -v rea >/dev/null 2>&1; then
    printf '[re_env] rea=%s\n' "$(rea --version 2>/dev/null || echo '?')"
  else
    printf '[re_env] rea=<não encontrado no PATH>\n'
  fi
  if [ -z "${JAVA_HOME:-}" ] || [ -z "${GHIDRA_INSTALL_DIR:-}" ]; then
    printf '[re_env] dica: rode "bash scripts/setup_re_tools.sh" para instalar o que falta.\n'
  fi
fi

unset -f _re_env_repo_root _re_env_has_javac _re_env_is_ghidra _re_env_prepend 2>/dev/null || true
unset _re_env_root _re_env_candidates _d _j _g 2>/dev/null || true
