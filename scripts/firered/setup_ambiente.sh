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

# ------------------------------- 0. dependencias declaradas x lista do sparse
# Falha em 1 segundo em vez de em 10 minutos. A E5 morreu no passo 3d com
# FileNotFoundError porque `src/data/abilities.h` nao estava no sparse-checkout;
# este cheque pega exatamente esse descompasso entre o que os geradores leem
# (`RH_*` / `ref / "..."`) e o que o setup baixa (`RHH_ARQUIVOS`).
log "0/8 conferindo as dependencias dos geradores"
python3 "$AQUI/checar_dependencias.py" --setup "$AQUI/setup_ambiente.sh" \
  --pokefirered "$PF" --reference /tmp/fre >/tmp/setup_deps.log 2>&1 \
  || { tail -20 /tmp/setup_deps.log; exit 1; }
ok "$(tail -1 /tmp/setup_deps.log)"

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

# O que a referencia do RHH precisa ter. Cada entrada e' consumida por um gerador;
# tirar uma daqui quebra a etapa correspondente (foi assim que a E5 falhou com
# FileNotFoundError em src/data/abilities.h). Mantenha esta lista e os caminhos
# RH_* dos scripts em sincronia.
RHH_ARQUIVOS=(
  '/include/'                              # constantes de especie/golpe/habilidade (E1-E5)
  '/src/data/pokemon/species_info/'        # gSpeciesInfo -> stats/tipos/dex/evolucao (E2)
  '/src/data/pokemon/level_up_learnsets/'  # golpes por nivel (E2)
  '/src/data/moves_info.h'                 # gMovesInfo -> 442 golpes (E4)
  '/src/data/abilities.h'                  # gAbilitiesInfo -> nomes/descricoes (E5)
  '/graphics/pokemon/'                     # sprites, icones, pegadas e paletas (E6)
  '/src/pokemon_icon.c'                    # gMonIconTable / gMonIconPaletteIndices (E6)
)

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
          && git sparse-checkout set --no-cone "${RHH_ARQUIVOS[@]}" >/dev/null 2>&1 ) \
    || { tail -10 /tmp/setup_fre.log; exit 1; }
  ok "referencia em /tmp/fre ($(git -C /tmp/fre rev-parse --short HEAD))"
fi

# clone antigo pode ter so `include` no sparse-checkout: completa sem re-clonar
if [ -d /tmp/fre/.git ] && { [ ! -d /tmp/fre/src/data/pokemon/species_info ] || \
     [ ! -f /tmp/fre/src/data/moves_info.h ] || [ ! -f /tmp/fre/src/data/abilities.h ]; }; then
  log "completando a referencia RHH (species_info + learnsets + moves_info + abilities)"
  ( cd /tmp/fre && git sparse-checkout set --no-cone "${RHH_ARQUIVOS[@]}" \
      >/tmp/setup_fre.log 2>&1 ) \
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

# --------------------------------------- 2e. habilidades das Gen 4-9 (E5)
# Ordem importa e e' circular de proposito:
#   1) a E2 roda antes e grava ABILITY_NONE onde a habilidade nao existe;
#   2) a E5 usa esse arquivo para saber QUAIS habilidades alguma especie usa
#      (elas precisam caber no u8 de `abilities[2]`, i.e. ID < 256);
#   3) a E2 roda de novo e agora resolve os nomes.
log "3d/8 gerando as habilidades das Gen 4-9 (E5)"
python3 "$RAIZ/scripts/firered/gen_ability_data.py" --pokefirered "$PF" \
  --reference /tmp/fre --write >/tmp/setup_e5.log 2>&1 \
  || { tail -20 /tmp/setup_e5.log; exit 1; }
ok "$(grep -E 'habilidades novas' /tmp/setup_e5.log | tail -1)"

log "3e/8 regerando os dados das especies com as habilidades novas (E5)"
python3 "$RAIZ/scripts/firered/gen_species_data.py" --pokefirered "$PF" \
  --reference /tmp/fre --write >/tmp/setup_e5b.log 2>&1 \
  || { tail -20 /tmp/setup_e5b.log; exit 1; }
ok "$(tail -1 /tmp/setup_e5b.log)"

log "3f/8 aplicando o gancho de motor da E5 (Earth Eater)"
python3 "$RAIZ/scripts/firered/apply_e5_port.py" --pokefirered "$PF" \
  >/tmp/setup_e5c.log 2>&1 \
  || { tail -20 /tmp/setup_e5c.log; exit 1; }
ok "$(grep -E 'aplicado|nada a fazer' /tmp/setup_e5c.log | tail -1)"

# ------------------------------------------------ 3g. ID de habilidade u16 (E6)
# ordem: o port do u16 vem ANTES dos geradores? não precisa — ele só muda o
# tipo do campo; mas tem de vir antes do build.
log "3g/8 alargando o ID de habilidade para u16 (E6)"
python3 "$RAIZ/scripts/firered/apply_e6_port.py" --pokefirered "$PF" \
  >/tmp/setup_e6a.log 2>&1 \
  || { tail -20 /tmp/setup_e6a.log; exit 1; }
ok "$(tail -1 /tmp/setup_e6a.log)"

log "3h/8 copiando sprites, icones, pegadas e cries das 639 novas (E6)"
python3 "$RAIZ/scripts/firered/gen_sprite_data.py" --pokefirered "$PF" \
  --reference /tmp/fre --write >/tmp/setup_e6b.log 2>&1 \
  || { tail -20 /tmp/setup_e6b.log; exit 1; }
ok "$(tail -1 /tmp/setup_e6b.log)"

# ------------------------------------------------------- 3i. encontros (E7)
# Precisa da species.h da E1 (ja aplicada) e do RHH. Fica ANTES do build: o
# `wild_encounters.json` vira `src/data/wild_encounters.h` em tempo de build.
log "3i/8 misturando as Gen 4-9 nas tabelas de encontro (E7)"
python3 "$RAIZ/scripts/firered/gen_wild_encounters.py" --pokefirered "$PF" \
  --reference /tmp/fre --write >/tmp/setup_e7a.log 2>&1 \
  || { tail -20 /tmp/setup_e7a.log; exit 1; }
ok "$(tail -1 /tmp/setup_e7a.log)"

log "3j/8 Pokedex nacional desde o inicio + numeros de 4 digitos (E7)"
python3 "$RAIZ/scripts/firered/apply_e7_port.py" --pokefirered "$PF" \
  >/tmp/setup_e7b.log 2>&1 \
  || { tail -20 /tmp/setup_e7b.log; exit 1; }
ok "$(tail -1 /tmp/setup_e7b.log)"

log "3k/8 ordens da Pokedex (A-Z, tipo, altura, peso) ate #1025 (E7)"
python3 "$RAIZ/scripts/firered/gen_pokedex_orders.py" --pokefirered "$PF" \
  --reference /tmp/fre --write >/tmp/setup_e7c.log 2>&1 \
  || { tail -20 /tmp/setup_e7c.log; exit 1; }
ok "$(tail -1 /tmp/setup_e7c.log)"

# As paginas de habitat da dex (`gDexCategories`) continuavam com as 386
# vanilla: a ficha pos-captura de uma especie Gen 4-9 abria em outra especie
# ("No800"/"???"). Este gerador NAO precisa do RHH: aprende o criterio das 386
# vanilla e distribui as novas por tipo.
log "3l/8 paginas de habitat da Pokedex ate #1025 (E7)"
python3 "$RAIZ/scripts/firered/gen_pokedex_categories.py" --pokefirered "$PF" --write \
  >/tmp/setup_e7d.log 2>&1 \
  || { tail -20 /tmp/setup_e7d.log; exit 1; }
ok "$(grep -c . /tmp/setup_e7d.log) linhas: $(sed -n '2p' /tmp/setup_e7d.log | sed 's/^ *//')"

# Treinadores: sem isso os times sao 100% Gen 1-3. So os times de golpes
# padrao mudam (lideres/rival/Elite 4 usam golpes a mao e ficam intactos).
log "3m/8 espécies Gen 4-9 nos times de treinadores (E7 onda 2b)"
python3 "$RAIZ/scripts/firered/gen_trainer_parties.py" --pokefirered "$PF" --write \
  >/tmp/setup_e7e.log 2>&1 \
  || { tail -20 /tmp/setup_e7e.log; exit 1; }
ok "$(head -1 /tmp/setup_e7e.log)"

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
      # `make` (todos os alvos) falha em `epoxy/gl.h`: o alvo `mgba` (Qt/SDL
      # desligados, mas o frontend de terminal pede OpenGL) nao compila no
      # sandbox. O que importa e' o core libretro, que e' construido ANTES e nao
      # depende de GL. Por isso: compila o alvo especifico e confere o arquivo.
      make -j2 mgba_libretro >/tmp/setup_mgba_make.log 2>&1 \
        || { tail -20 /tmp/setup_mgba_make.log 2>/dev/null; exit 1; }
    ) || exit 1
    [ -s /tmp/mgba-0.10.5/build/mgba_libretro.so ] \
      || { echo "o core nao foi gerado"; exit 1; }
    ok "core em /tmp/mgba-0.10.5/build/mgba_libretro.so"
  fi
fi

# ------------------------------------- 7b. o sparse baixou tudo que falta?
# Segundo cheque: agora com os dois clones no disco, confirma que nenhum arquivo
# declarado ficou de fora (pegadinha do sparse ja' existente de sessao anterior).
if python3 "$AQUI/checar_dependencias.py" --pokefirered "$PF" --reference /tmp/fre \
     >/tmp/setup_deps2.log 2>&1; then
  ok "dependencias presentes no disco"
else
  tail -20 /tmp/setup_deps2.log; exit 1
fi

# --------------------------------------------------------------- 6. offsets
log "8/8 gerando os offsets de struct do build ARM (0,3 s)"
python3 "$RAIZ/scripts/firered/offsets.py" --pokefirered "$PF" --json >/tmp/pf_offsets.json 2>/tmp/setup_offsets.log
ok "offsets em /tmp/pf_offsets.json"
[ -s /tmp/setup_offsets.log ] && sed 's/^/    /' /tmp/setup_offsets.log

# ------------------------------------------------- 9. tradução PT-BR (T1-T7)
# Sem isto, um clone recém-religado fica em inglês e o aplicar_traducao.py
# aborta com "char fora do charmap: ã" (a fonte T1 ainda não existe no clone).
# Ordem obrigatória: fonte (T1) ANTES do dicionário, depois rebuild.
log "9/9 aplicando fonte PT-BR (T1) + dicionários de tradução + rebuild"
python3 "$RAIZ/scripts/firered/aplicar_fonte_ptbr.py" --pokefirered "$PF" --write \
  >/tmp/setup_fonte.log 2>&1 || { tail -10 /tmp/setup_fonte.log; exit 1; }
python3 "$RAIZ/scripts/firered/apply_t8_varredura.py" --pokefirered "$PF" \
  >/tmp/setup_t8.log 2>&1 || { tail -10 /tmp/setup_t8.log; exit 1; }
python3 "$RAIZ/scripts/firered/aplicar_traducao.py" --pokefirered "$PF" --write \
  >/tmp/setup_trad.log 2>&1 || { tail -20 /tmp/setup_trad.log; exit 1; }
grep -E 'ERRO' /tmp/setup_trad.log && { echo "tradução com ERROs acima"; exit 1; }
python3 "$RAIZ/scripts/firered/aplicar_ficha.py" --pokefirered "$PF" --write \
  >/tmp/setup_ficha.log 2>&1 || { tail -10 /tmp/setup_ficha.log; exit 1; }
( cd "$PF" && make -j2 MODERN=1 CC1_DAEMONS=2 >/tmp/setup_rebuild.log 2>&1 ) \
  || { tail -10 /tmp/setup_rebuild.log; exit 1; }
ok "ROM PT-BR: $(md5sum "$PF/pokefirered_modern.gba" | cut -d' ' -f1)"

cat <<'FIM'

Ambiente pronto. Exporte antes de usar as ferramentas:

    export PATH=/tmp/tc/bin:$PATH
    export MGBA_CORE=/tmp/mgba-0.10.5/build/mgba_libretro.so

FIM
