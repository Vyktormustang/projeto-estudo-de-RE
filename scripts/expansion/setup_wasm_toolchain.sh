#!/usr/bin/env bash
# Prepara o toolchain ARM (GCC 14.2 + binutils) que roda como WebAssembly via Node.
# Nao precisa de root, nem de devkitPro: tudo fica em /tmp e vem do npm/pip.
#
#   bash scripts/expansion/setup_wasm_toolchain.sh [--self-test]
#
# Depois disso:  export PATH=/tmp/tc/bin:$PATH   e   make modern -j2
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TC=/tmp/tc/bin
PKG=/tmp/pkg
ZIG_VERSION=0.17.0

log() { printf '\033[1m==> %s\033[0m\n' "$*"; }

baixa_pacote() {
  log "baixando o toolchain GBA (npm romdev-platform-gba, ~11 MB)"
  mkdir -p "$PKG"
  curl -sSL -o /tmp/gba.tgz \
    "https://registry.npmjs.org/romdev-platform-gba/-/romdev-platform-gba-0.14.1.tgz"
  tar xzf /tmp/gba.tgz -C "$PKG"
  test -f "$PKG/package/wasm/cc1-arm.wasm"
}

instala_node_zig() {
  command -v node >/dev/null || { echo "ERRO: precisa de Node.js 18+"; exit 1; }
  log "instalando ziglang (traz o clang/LLVM que faz o papel de pre-processador)"
  python3 -m pip install --break-system-packages -q "ziglang==$ZIG_VERSION"
}

instala_wrappers() {
  log "instalando os wrappers em $TC"
  mkdir -p "$TC"
  cp "$AQUI/toolchain_wasm/"* "$TC"/
  chmod +x "$TC"/arm-* "$TC"/pkg-config
}

self_test() {
  log "self-test"
  export PATH="$TC:$PATH"
  local falhas=0
  chk() { if eval "$2"; then echo "  OK   $1"; else echo "  FALHA $1"; falhas=$((falhas+1)); fi; }

  chk "gcc responde --version" "arm-none-eabi-gcc --version | grep -q GCC"
  chk "gcc acha libgcc.a"      "test -f \"\$(arm-none-eabi-gcc -mthumb -print-file-name=libgcc.a)\""
  printf 'int f(int a){return a*2;}\n' > /tmp/st.c
  chk "cc1 compila C -> .s"    "arm-fake-cc1 -mthumb -O2 -o /tmp/st.s - < /tmp/st.c >/dev/null 2>&1 && grep -q 'mul\|lsl' /tmp/st.s"
  printf '.text\n.global g\ng:\n mov r0, r0\n' > /tmp/st2.s
  chk "as monta .s -> .o"      "arm-none-eabi-as -mcpu=arm7tdmi -o /tmp/st2.o /tmp/st2.s && test -s /tmp/st2.o"
  chk "ld roda (versao)"       "arm-none-eabi-ld --version 2>&1 | grep -qiE 'GNU ld|LLD'"
  echo
  if [ "$falhas" -eq 0 ]; then echo "SELF-TEST: tudo OK"; return 0; fi
  echo "SELF-TEST: $falhas falha(s)"; return 1
}

if [ "${1:-}" = "--self-test" ]; then self_test; exit $?; fi

baixa_pacote
instala_node_zig
instala_wrappers
self_test
cat <<'FIM'

Pronto. Para compilar a ROM:
  export PATH=/tmp/tc/bin:$PATH
  make modern -j2

Aviso: as ferramentas vivem em /tmp (nao persistem apos reiniciar a maquina).
Rode este script de novo depois de reiniciar.
FIM
