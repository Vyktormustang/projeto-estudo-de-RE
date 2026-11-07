# Makefile — compila o shim (gba_shim.so) + libmgba a partir do fonte do mGBA.
#
# Por que compilar em vez de usar o .so versionado em emu/:
#   o core libretro-mgba 0.10.5 do Debian 13 exige GLIBC 2.38; sandboxes
#   Debian 12 têm 2.36 → `ImportError/GLIBC not found`. Compilar aqui também
#   nos dá acesso ao CPU (breakpoints, registradores) que o core libretro não expõe.
#
# Uso:
#   make            # baixa mGBA 0.10.5, compila libmgba + shim -> build/gba_shim.so
#   make test-shim  # sanidade: carrega o .so e lê o header de uma ROM fixture
#   make clean
#
# Versão do mGBA fixada por tag + sha256 do tarball (reprodutibilidade).
MGBA_VER    := 0.10.5
MGBA_URL    := https://codeload.github.com/mgba-emu/mgba/tar.gz/refs/tags/$(MGBA_VER)
MGBA_SHA256 := $(shell cat mgba_tree.sha256 2>/dev/null)

BUILD   := build
SRC_OUT := $(BUILD)/mgba-src
CMAKEDIR:= $(BUILD)/cmake
PREFIX  := $(abspath $(BUILD)/prefix)
PYTHON_BIN ?= python3

CMAKE ?= cmake
ifneq ($(wildcard $(BUILD)/tools/bin/cmake),)
CMAKE := $(abspath $(BUILD)/tools/bin/cmake)
endif
CMAKE_POLICY := -DCMAKE_POLICY_VERSION_MINIMUM=3.5

# libmgba é compilada como estática com -fPIC (LIBMGBA_ONLY=ON ignora BUILD_SHARED),
# então o .so do shim carrega o emulador dentro de si: um arquivo, zero rpath.
# ordem importa: objetos antes da lib estática (-lmgba resolvido no final)
SHIM_CPPFLAGS := -shared -fPIC -O2 -std=gnu11 -D_GNU_SOURCE -Wall \
  -I$(SRC_OUT)/include -I$(SRC_OUT)
SHIM_LDLIBS := $(PREFIX)/lib/libmgba.a -lm -lpthread

.PHONY: all libmgba shim test-shim clean fetch

all: $(BUILD)/gba_shim.so

fetch:
	@mkdir -p $(BUILD)
	@if [ ! -d "$(SRC_OUT)" ]; then \
	  echo "[fetch] mGBA $(MGBA_VER)"; \
	  curl -sL -o $(BUILD)/mgba.tar.gz "$(MGBA_URL)"; \
	  if [ -f mgba_tree.sha256 ]; then \
	    echo "$$(cat mgba_tree.sha256)  $(BUILD)/mgba.tar.gz" | sha256sum -c - || \
	      { echo "[ERRO] sha256 do tarball diverge"; exit 1; }; \
	  fi; \
	  mkdir -p $(SRC_OUT) && tar xzf $(BUILD)/mgba.tar.gz -C $(SRC_OUT) --strip-components=1; \
	fi

$(PREFIX)/lib/libmgba.a: | fetch
	@if [ ! -f "$(BUILD)/tools/bin/cmake" ] && ! command -v cmake >/dev/null; then \
	  echo "[cmake] instalando cmake em venv local (sem root)"; \
	  $(PYTHON_BIN) -m venv $(BUILD)/tools 2>/dev/null || true; \
	  $(BUILD)/tools/bin/pip install -q cmake || \
	    { echo "[ERRO] instale cmake: apt install cmake  OU  pip install cmake"; exit 1; }; \
	fi
	$(CMAKE) -S $(SRC_OUT) -B $(CMAKEDIR) $(CMAKE_POLICY) \
	  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$(PREFIX) \
	  -DLIBMGBA_ONLY=ON -DBUILD_SHARED=ON -DBUILD_STATIC=OFF \
	  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
	  -DUSE_DEBUGGERS=ON -DUSE_GDB_STUB=OFF -DUSE_ELF=ON -DUSE_EDITLINE=OFF \
	  -DUSE_PNG=OFF -DUSE_ZLIB=ON -DUSE_MINIZIP=OFF -DUSE_FFMPEG=OFF \
	  -DUSE_SQLITE3=OFF -DUSE_LIBZIP=OFF -DUSE_LUA=OFF -DUSE_LZMA=OFF \
	  -DUSE_DISCORD_RPC=OFF -DM_CORE_GB=OFF -DM_CORE_GBA=ON
	$(CMAKE) --build $(CMAKEDIR) -j$(shell nproc)
	$(CMAKE) --install $(CMAKEDIR)
	@test -f $(PREFIX)/lib/libmgba.a || { echo "[ERRO] libmgba.a não instalada"; exit 1; }

libmgba: $(PREFIX)/lib/libmgba.a

shim: $(BUILD)/gba_shim.so

$(BUILD)/gba_shim.so: gba_shim.c $(PREFIX)/lib/libmgba.a
	$(CC) $(SHIM_CPPFLAGS) -o $@ gba_shim.c $(SHIM_LDLIBS)
	@echo "[shim] $@ $$(stat -c %s $@) bytes (libmgba embutida)"

test-shim: $(BUILD)/gba_shim.so
	$(PYTHON_BIN) shim_smoke.py $(BUILD)/gba_shim.so

clean:
	rm -rf $(BUILD)
