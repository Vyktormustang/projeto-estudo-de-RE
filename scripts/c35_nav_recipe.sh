#!/usr/bin/env bash
# c35 — receita REPRODUZÍVEL da navegação até o tutorial/intro do Pikachu (ver RETOMADA.md §6).
# Requer rom/pokemon_firered_bpre_trabalho.gba (cópia do usuário; NÃO versionada).
# Estado ABERTO: a intro do Pikachu não avança com A. Este script só reproduz o que foi provado.
set -euo pipefail
cd "$(dirname "$0")/.."
export LD_LIBRARY_PATH=emu/x/usr/lib/x86_64-linux-gnu
OUT=${OUT:-/tmp/c35_nav}; mkdir -p "$OUT"
ROM=rom/pokemon_firered_bpre_trabalho.gba

# 1) boot -> título -> tutorial CONTROLE; A alterna páginas 1<->2 (verificado 2000/3500/4150)
ARGS="--input 880:START:8 --input 1750:START:8 --input 1900:A:8"
for f in 2100 2250 2400 2550 2700 2850 3000 3150 3300 3450 3600; do ARGS="$ARGS --input $f:A:8"; done
python3 scripts/gba_libretro_emu.py --rom "$ROM" --frames 4200 $ARGS \
  --save-state "$OUT/s4200.bin" --snap 2000=$OUT/tutorial2000.png >/dev/null

# 2) patch do estágio do tutorial: [0x0203B108]+0x12 = 0x02000022 -> 2 (aventura do Pikachu)
python3 scripts/gba_state_dump.py "$OUT/s4200.bin" --read 0x02000022:0x02
python3 scripts/gba_state_dump.py "$OUT/s4200.bin" --patch 0x02000022=0200 -o "$OUT/s4200_st2.bin" >/dev/null

# 3) carrega o patch e pressiona A: intro do Pikachu (ABERTO: A não avança depois)
python3 scripts/gba_libretro_emu.py --rom "$ROM" --load-state "$OUT/s4200_st2.bin" \
  --frames 300 --input 60:A:8 --snap 200=$OUT/pikaintro200.png >/dev/null
echo "capturas em $OUT (tutorial2000.png, pikaintro200.png)"
