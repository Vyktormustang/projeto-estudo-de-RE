#!/usr/bin/env bash
# Monta do zero o ROM "FireRed com os Pokemon novos" (Kanto + Gen 1-9).
#
# O que este script faz, em ordem:
#   1. clona o fork CharonChaos88/FireRedExpansion (pokeemerald-expansion 1.15
#      com os mapas de Kanto/Sevii de FireRed);
#   2. compila as ferramentas (make tools) e corrige a permissao do poryscript;
#   3. aplica os dois patches de build em scripts/firered/patches/;
#   4. mistura Pokemon das Gens 2-9 nas tabelas de encontro selvagem
#      (scripts/firered/misturar_encontros.py);
#   5. regenera os dados de mapa em modo firered e compila (make firered).
#
# Uso:
#   ./buildar_firered_expansion.sh                 # tudo, em ./FireRedExpansion
#   ./buildar_firered_expansion.sh /caminho/alvo   # pasta alternativa
#   ./buildar_firered_expansion.sh --self-test     # so testa o script
#
# Requisitos: git, make, gcc/g++ (nativo), python3, e um toolchain
# arm-none-eabi (o devkitPro/pacman do INSTALL.md do expansion resolve).
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$AQUI/../.." && pwd)"
UPSTREAM="https://github.com/CharonChaos88/FireRedExpansion.git"

uso() { sed -n '2,22p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

self_test() {
    local ok=0 falhas=0
    check() { if eval "$2"; then ok=$((ok+1)); else echo "  FALHOU: $1"; falhas=$((falhas+1)); fi; }
    check "ferramentas basicas" "command -v git >/dev/null && command -v make >/dev/null && command -v python3 >/dev/null"
    check "script de encontros existe" "[ -f '$REPO/scripts/firered/misturar_encontros.py' ]"
    check "patch 0001 existe" "[ -f '$REPO/scripts/firered/patches/0001-hidden-itens-firered.patch' ]"
    check "patch 0002 existe" "[ -f '$REPO/scripts/firered/patches/0002-map-version-firered.patch' ]"
    check "encontros self-test" "python3 '$REPO/scripts/firered/misturar_encontros.py' --self-test >/dev/null"
    echo "self-test: $ok/$((ok+falhas)) OK"
    [ "$falhas" -eq 0 ]
}

if [ "${1:-}" = "--self-test" ]; then self_test; exit $?; fi
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then uso; exit 0; fi

DEST="${1:-$PWD/FireRedExpansion}"

echo "== 1/5 clonando o fork em $DEST"
if [ -d "$DEST/.git" ]; then
    echo "   ja existe, reaproveitando"
else
    git clone --depth 1 "$UPSTREAM" "$DEST"
fi
cd "$DEST"

echo "== 2/5 compilando ferramentas"
make tools -j"$(nproc 2>/dev/null || echo 2)" || make tools
chmod +x tools/poryscript/poryscript tools/*/* 2>/dev/null || true

echo "== 3/5 aplicando patches de build"
for p in "$REPO"/scripts/firered/patches/*.patch; do
    if git apply --check "$p" 2>/dev/null; then
        git apply "$p"; echo "   aplicado: $(basename "$p")"
    else
        echo "   ignorado (ja aplicado?): $(basename "$p")"
    fi
done

echo "== 4/5 misturando encontros Gen 2-9"
python3 "$REPO/scripts/firered/misturar_encontros.py" --aplicar "$DEST"

echo "== 5/5 regenerando mapas e compilando (make firered)"
# Limpa os .inc/.h gerados: se sobraram de uma rodada em modo emerald, o link
# quebra com referencias a tilesets de Hoenn que nao existem no modo firered.
rm -f data/maps/connections.inc data/maps/groups.inc data/maps/events.inc \
      data/maps/headers.inc data/maps/*/events.inc data/maps/*/header.inc \
      data/maps/*/connections.inc data/layouts/layouts.inc \
      data/layouts/layouts_table.inc include/constants/map_groups.h \
      include/constants/layouts.h include/constants/map_event_ids.h \
      src/data/map_group_count.h
make MAP_VERSION=firered generated
make firered -j"$(nproc 2>/dev/null || echo 2)"

echo
echo "== pronto"
ls -la pokefirered.gba
sha256sum pokefirered.gba
echo "Titulo no cabecalho: POKEMON FIRE / BPRE (confira com: xxd -s 0xA0 -l 16 pokefirered.gba)"
