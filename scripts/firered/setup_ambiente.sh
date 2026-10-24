#!/usr/bin/env bash
# Reconstroi TODO o ambiente de trabalho do port FireRed Gen 1-9.
#
# Por que existe
# -------------
# /tmp nao sobrevive entre sessoes (e as vezes some no meio de uma). Sem isso,
# cada vez que o /tmp zera eram ~20 minutos de trabalho manual repetido:
# toolchain, clone do pokefirered, port E1, `make tools`, mGBA. Este script faz
# tudo de uma vez, com verificacao no fim.
#
# Uso
# ---
#   bash scripts/firered/setup_ambiente.sh            # tudo
#   bash scripts/firered/setup_ambiente.sh --sem-mgba # pula o mGBA (mais rapido)
#   bash scripts/firered/setup_ambiente.sh --so-build # so reaplica o port e compila
#
# O que ele deixa pronto
# ----------------------
#   /tmp/tc/bin                      toolchain ARM (via wasm/node)
#   /tmp/pokefirered                 clone limpo + port E1 aplicado
#   /tmp/pokefirered/pokefirered_modern.gba   ROM compilada
#   /tmp/mgba-0.10.5/build/mgba_libretro.so   core do emulador p/ nav.py
#   /tmp/local                       shim de headers libpng/zlib p/ `make tools`
#
# Depois: export PATH=/tmp/tc/bin:$PATH MGBA_CORE=/tmp/mgba-0.10.5/build/mgba_libretro.so
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(cd "$AQUI/../.." && pwd)"
PF=/tmp/pokefirered
# Commits fixos: o RHH muda todo dia e isso muda a ROM (dados de especie/golpe).
# Sem o pino, dois builds "iguais" davam hashes diferentes.
PF_COMMIT=ce6406d8c2eaf46d543c8a2606de0c3cb1951982   # pret/pokefirered 2026-10-20
RHH_COMMIT=f594a462d7e756b25727d676e34829f63c053d13  # rh-hideout/pokeemerald-expansion 2026-10-23
SEM_MGBA=0
SO_BUILD=0
for arg in "$@"; do
  case "$arg" in
    --sem-mgba) SEM_MGBA=1 ;;
    --so-build) SO_BUILD=1 ;;
    *) echo "argumento desconhecido: $arg"; exit 2 ;;
  esac
done

log() { printf '\033[1m==> %s\033[0m\n' "$*"; }
ok()  { printf '    ok: %s\n' "$*"; }

# ---------------------------------------------------------------- 1. toolchain
if [ "$SO_BUILD" -eq 0 ]; then
  if [ -x /tmp/tc/bin/arm-none-eabi-as ] && [ -x /tmp/tc/bin/arm-fake-cc1 ]; then
    ok "toolchain ARM ja existe em /tmp/tc/bin"
  else
    log "1/8 toolchain ARM (wasm) ~2 min"
    bash "$RAIZ/scripts/expansion/setup_wasm_toolchain.sh" >/tmp/setup_tc.log 2>&1 \
      || { tail -20 /tmp/setup_tc.log; exit 1; }
    ok "toolchain em /tmp/tc/bin"
  fi
fi
export PATH=/tmp/tc/bin:$PATH

# ------------------------------------------------------- 2. clone + port E1
if [ -d "$PF/.git" ]; then
  ok "clone ja existe em $PF"
else
  log "2/8 clonando pret/pokefirered ~30 s"
  rm -rf "$PF"
  git clone --depth 1 https://github.com/pret/pokefirered "$PF" >/tmp/setup_clone.log 2>&1
  git -C "$PF" fetch --depth 1 origin "$PF_COMMIT" >>/tmp/setup_clone.log 2>&1 \
    && git -C "$PF" checkout -q "$PF_COMMIT" \
    || { tail -10 /tmp/setup_clone.log; exit 1; }
  ok "clone em $PF ($(git -C "$PF" rev-parse --short HEAD))"
fi

# referencia: so os headers de constantes do RHH (fonte dos nomes 387-1025)
if [ -f /tmp/fre/include/constants/pokedex.h ]; then
  ok "referencia RHH ja existe em /tmp/fre"
else
  log "clonando a referencia RHH (pokeemerald-expansion) ~60 s"
  rm -rf /tmp/fre
  git clone --depth 1 --filter=blob:none --sparse \
      https://github.com/rh-hideout/pokeemerald-expansion /tmp/fre >/tmp/setup_fre.log 2>&1 \
    && ( cd /tmp/fre && git fetch --depth 1 origin "$RHH_COMMIT" >>/tmp/setup_fre.log 2>&1 \
          && git checkout -q "$RHH_COMMIT" \
          && git sparse-checkout set --no-cone '/include/' \
          '/src/data/pokemon/species_info/' '/src/data/pokemon/level_up_learnsets/' \
          '/src/data/moves_info.h' >/dev/null 2>&1 ) \
    || { tail -10 /tmp/setup_fre.log; exit 1; }
  ok "referencia em /tmp/fre ($(git -C /tmp/fre rev-parse --short HEAD))"
fi

# clone antigo pode ter so `include` no sparse-checkout: completa sem re-clonar
if [ -d /tmp/fre/.git ] && { [ ! -d /tmp/fre/src/data/pokemon/species_info ] || \
     [ ! -f /tmp/fre/src/data/moves_info.h ]; }; then
  log "completando a referencia RHH (species_info + learnsets + moves_info.h)"
  ( cd /tmp/fre && git sparse-checkout set --no-cone '/include/' \
      '/src/data/pokemon/species_info/' '/src/data/pokemon/level_up_learnsets/' \
      '/src/data/moves_info.h' >/tmp/setup_fre.log 2>&1 ) \
    || { tail -10 /tmp/setup_fre.log; exit 1; }
fi

log "aplicando o port E1 (1025 especies)"
python3 "$RAIZ/scripts/firered/apply_e1_port.py" --pokefirered "$PF" >/tmp/setup_port.log 2>&1 \
  || { tail -20 /tmp/setup_port.log; exit 1; }
ok "port aplicado"

# ------------------------------------------------- 2b. dados das especies (E2)
log "3/8 gerando os dados das especies 387-1025 (E2)"
python3 "$RAIZ/scripts/firered/gen_species_data.py" --pokefirered "$PF" \
  --reference /tmp/fre --write >/tmp/setup_e2.log 2>&1 \
  || { tail -20 /tmp/setup_e2.log; exit 1; }
ok "$(tail -1 /tmp/setup_e2.log)"

# --------------------------------------- 2c. tipo Fada + split por golpe (E3)
log "3b/8 aplicando o port da E3 (tipo Fada + split fisico/especial)"
python3 "$RAIZ/scripts/firered/apply_e3_port.py" --pokefirered "$PF" \
  >/tmp/setup_e3.log 2>&1 \
  || { tail -20 /tmp/setup_e3.log; exit 1; }
ok "$(grep -E 'aplicado|nada a fazer' /tmp/setup_e3.log | tail -1)"

# ---------------------------------------- 2d. golpes das Gen 4-9 (E4)
log "3c/8 gerando os golpes das Gen 4-9 (E4)"
python3 "$RAIZ/scripts/firered/gen_move_data.py" --pokefirered "$PF" \
  --reference /tmp/fre --write >/tmp/setup_e4.log 2>&1 \
  || { tail -20 /tmp/setup_e4.log; exit 1; }
ok "$(tail -1 /tmp/setup_e4.log)"

# --------------------------------------------------- 3. shim p/ `make tools`
if [ ! -f /tmp/local/include/png.h ]; then
  log "4/8 headers libpng/zlib p/ compilar as ferramentas ~1 min"
  mkdir -p /tmp/local/include /tmp/local/lib
  ( cd /tmp/local
    curl -sSL -o png.tgz https://github.com/pnggroup/libpng/archive/refs/tags/v1.6.39.tar.gz
    tar xzf png.tgz
    cp -r libpng-1.6.39/*.h include/
    # pnglibconf.h vem do script configure; geramos o minimo via cmake-like default
    cp libpng-1.6.39/scripts/pnglibconf.h.prebuilt include/pnglibconf.h
    curl -sSL -o zlib.tgz https://github.com/madler/zlib/archive/refs/tags/v1.3.1.tar.gz
    tar xzf zlib.tgz
    cp zlib-1.3.1/zlib.h zlib-1.3.1/zconf.h include/
    # libpng aqui so existe como libpng16.so.16 (sem o .so de desenvolvimento),
    # entao procuramos o arquivo real e criamos o symlink com o nome esperado.
    # Cuidado com `set -e`: um glob sem resultado derrubaria o script.
    for par in "png:/usr/lib/*/libpng16.so.16*" "z:/usr/lib/*/libz.so.1*"; do
      nome="${par%%:*}"; padrao="${par#*:}"
      so=$(ls $padrao /usr/lib/${padrao#/usr/lib/*/} 2>/dev/null | head -1) || true
      if [ -n "${so:-}" ]; then
        ln -sf "$so" "lib/lib$nome.so"
      else
        echo "aviso: nao achei $padrao (gbagfx pode falhar no link)" >&2
      fi
    done
  ) >/tmp/setup_local.log 2>&1 || { tail -20 /tmp/setup_local.log; exit 1; }
  ok "shim em /tmp/local"
else
  ok "shim /tmp/local ja existe"
fi
export CPATH=/tmp/local/include
export LIBRARY_PATH=/tmp/local/lib

log "5/8 compilando as ferramentas do pokefirered (make tools) ~1 min"
if [ ! -x "$PF/tools/gbagfx/gbagfx" ]; then
  ( cd "$PF" && make tools -j2 >/tmp/setup_tools.log 2>&1 ) \
    || { tail -30 /tmp/setup_tools.log; exit 1; }
fi
ok "ferramentas prontas"

# ------------------------------------------------------------------ 4. build
log "6/8 compilando a ROM (primeira vez ~9 min, incremental ~10 s)"
( cd "$PF" && make -j2 MODERN=1 CC1_DAEMONS=2 >/tmp/setup_build.log 2>&1 ) \
  || { grep -m5 "error:" /tmp/setup_build.log; exit 1; }
ok "ROM: $(sha256sum "$PF/pokefirered_modern.gba" | cut -c1-16) ($(stat -c%s "$PF/pokefirered_modern.gba") B)"

log "6b/8 conferindo os dados da E2 dentro do ROM (nao confia no compilador)"
python3 "$RAIZ/scripts/firered/verificar_rom.py" --pokefirered "$PF" \
  >/tmp/setup_verif.log 2>&1 \
  || { tail -20 /tmp/setup_verif.log; exit 1; }
ok "$(tail -1 /tmp/setup_verif.log)"

# -------------------------------------------------------------------- 5. mGBA
if [ "$SEM_MGBA" -eq 0 ]; then
  if [ -f /tmp/mgba-0.10.5/build/mgba_libretro.so ]; then
    ok "core do mGBA ja existe"
  else
    log "7/8 compilando o core libretro do mGBA ~4 min"
    python3 -m pip install --break-system-packages -q cmake
    ( cd /tmp
      [ -d mgba-0.10.5 ] || curl -sSL -o mgba.tgz https://github.com/mgba-emu/mgba/archive/refs/tags/0.10.5.tar.gz
      [ -d mgba-0.10.5 ] || tar xzf mgba.tgz
      cd mgba-0.10.5 && mkdir -p build && cd build
      # BUILD_QT/BUILD_SDL=OFF: sem Qt e sem SDL o cmake nao procura SDL_INCLUDE_DIR.
      # USE_ELF/USE_LIBZIP=OFF: libelf e libzip nao existem no sandbox e o core
      # libretro nao precisa delas (so o updater-stub usa).
      cmake .. -DBUILD_LIBRETRO=ON -DBUILD_QT=OFF -DBUILD_SDL=OFF \
               -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
               -DUSE_LIBZIP=OFF -DUSE_ELF=OFF -DUSE_PNG=OFF -DUSE_ZLIB=OFF \
               -DUSE_SQLITE3=OFF -DUSE_FFMPEG=OFF -DUSE_MINIZIP=OFF \
               >/tmp/setup_mgba_cmake.log 2>&1
      make -j2 >/tmp/setup_mgba_make.log 2>&1
    ) || { tail -20 /tmp/setup_mgba_make.log 2>/dev/null; exit 1; }
    ok "core em /tmp/mgba-0.10.5/build/mgba_libretro.so"
  fi
fi

# --------------------------------------------------------------- 6. offsets
log "8/8 gerando os offsets de struct do build ARM (0,3 s)"
python3 "$RAIZ/scripts/firered/offsets.py" --pokefirered "$PF" --json >/tmp/pf_offsets.json 2>/tmp/setup_offsets.log
ok "offsets em /tmp/pf_offsets.json"
[ -s /tmp/setup_offsets.log ] && sed 's/^/    /' /tmp/setup_offsets.log

cat <<'FIM'

Ambiente pronto. Exporte antes de usar as ferramentas:

    export PATH=/tmp/tc/bin:$PATH
    export MGBA_CORE=/tmp/mgba-0.10.5/build/mgba_libretro.so

FIM
