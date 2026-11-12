#!/usr/bin/env bash
# video_env.sh — prepara o que as skills de vídeo precisam NESTE sandbox.
#
# Por que existe: o Python do sistema é PEP 668 (externally-managed), então
# `pip install pillow` falha. E não há ffmpeg no PATH. Solução: venv próprio +
# ffmpeg estático do wheel `imageio-ffmpeg` (nada de sudo, nada de apt).
#
# Uso:
#   bash scripts/video_env.sh            # cria/atualiza .venv-video e imprime o ffmpeg
#   source scripts/video_env.sh --export # exporta FFMPEG=... e PATH no shell atual
#   bash scripts/video_env.sh --self-test
#
# Idempotente: rodar de novo só confere.
set -u
cd "$(dirname "$0")/.." || exit 2
VENV=".venv-video"

achado() { "$VENV/bin/python" -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null; }

preparar() {
  command -v python3 >/dev/null || { echo "[ERRO] python3 ausente"; return 1; }
  if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV" || { echo "[ERRO] não consegui criar venv"; return 1; }
  fi
  if ! "$VENV/bin/python" -c "import PIL, imageio_ffmpeg" 2>/dev/null; then
    "$VENV/bin/pip" install --quiet --disable-pip-version-check pillow imageio-ffmpeg \
      || { echo "[ERRO] pip install falhou"; return 1; }
  fi
  FF=$(achado) || { echo "[ERRO] ffmpeg não resolvido"; return 1; }
  echo "[ok] venv: $VENV"
  echo "[ok] ffmpeg: $FF"
  echo "     use assim:  FFMPEG=$FF   (ou: source scripts/video_env.sh --export)"
}

case "${1:-}" in
  --export)
    preparar >/dev/null 2>&1 || { echo "[ERRO] prepare falhou" >&2; return 1 2>/dev/null || exit 1; }
    FFMPEG=$(achado); export FFMPEG
    PATH="$(dirname "$FFMPEG"):$PATH"; export PATH
    echo "[ok] FFMPEG=$FFMPEG (e no PATH)"
    ;;
  --self-test)
    falhas=0
    preparar || falhas=$((falhas+1))
    FF=$(achado)
    [ -x "$FF" ] && echo "  [ok] ffmpeg executável" || { echo "  [FALHA] ffmpeg não executável"; falhas=$((falhas+1)); }
    "$VENV/bin/python" -c "import PIL" 2>/dev/null && echo "  [ok] PIL importa" || { echo "  [FALHA] PIL"; falhas=$((falhas+1)); }
    # render de prova: 2 frames -> 1s de vídeo
    tmp=$(mktemp -d)
    "$VENV/bin/python" - "$tmp" <<'PY' || falhas=$((falhas+1))
import sys
from PIL import Image
for i, c in enumerate([(10,10,30),(60,20,70)]):
    Image.new("RGB",(64,64),c).save(f"{sys.argv[1]}/f{i}.png")
PY
    "$FF" -y -loglevel error -framerate 1 -i "$tmp/f%d.png" -c:v libx264 -pix_fmt yuv420p -t 2 "$tmp/t.mp4" 2>/dev/null
    if [ -s "$tmp/t.mp4" ]; then echo "  [ok] render de prova ($(wc -c <"$tmp/t.mp4") B)"; else echo "  [FALHA] render"; falhas=$((falhas+1)); fi
    rm -rf "$tmp"
    echo "self-test: $([ "$falhas" -eq 0 ] && echo OK || echo "$falhas falha(s)")"
    [ "$falhas" -eq 0 ] || exit 1
    ;;
  *)
    preparar
    ;;
esac
