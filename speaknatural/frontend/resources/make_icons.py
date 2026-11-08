"""Gera ícones e telas de abertura do APK a partir de resources/icon.png.

Uso (na pasta frontend/):
    python resources/make_icons.py          # precisa de Pillow: pip install pillow

O que ele escreve (tudo dentro de android/app/src/main/res):
    mipmap-*/ic_launcher.png            ícone quadrado (Android antigo)
    mipmap-*/ic_launcher_round.png      ícone redondo (launchers que pedem)
    mipmap-*/ic_launcher_foreground.png ícone adaptativo (Android 8+)
    drawable*/splash.png                tela de abertura

Rode de novo só se trocar a arte em resources/icon.png.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

RES = Path(__file__).resolve().parent.parent / "android" / "app" / "src" / "main" / "res"
SOURCE = Path(__file__).resolve().parent / "icon.png"

#: Tamanhos oficiais (dp) -> px por densidade
LAUNCHER_SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
FOREGROUND_SIZES = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}

#: Telas de abertura (px), iguais às do template do Capacitor
SPLASHES = {
    "drawable/splash.png": (480, 320),
    "drawable-land-mdpi/splash.png": (480, 320),
    "drawable-land-hdpi/splash.png": (800, 480),
    "drawable-land-xhdpi/splash.png": (1280, 720),
    "drawable-land-xxhdpi/splash.png": (1600, 960),
    "drawable-land-xxxhdpi/splash.png": (1920, 1280),
    "drawable-port-mdpi/splash.png": (320, 480),
    "drawable-port-hdpi/splash.png": (480, 800),
    "drawable-port-xhdpi/splash.png": (720, 1280),
    "drawable-port-xxhdpi/splash.png": (960, 1600),
    "drawable-port-xxxhdpi/splash.png": (1280, 1920),
}

GRADIENT_START = (60, 42, 210)
GRADIENT_END = (124, 58, 237)


def gradient(size: tuple[int, int]) -> Image.Image:
    """Fundo em degradê diagonal (indigo -> violeta)."""
    width, height = size
    base = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(base)
    steps = max(width, height)
    for index in range(steps):
        ratio = index / max(1, steps - 1)
        color = tuple(
            int(GRADIENT_START[channel] + (GRADIENT_END[channel] - GRADIENT_START[channel]) * ratio)
            for channel in range(3)
        )
        draw.line([(0, index), (width, index)], fill=color)
    return base.rotate(0)


def square_icon(size: int) -> Image.Image:
    return SOURCE_IMAGE.resize((size, size), Image.LANCZOS).convert("RGBA")


def round_icon(size: int) -> Image.Image:
    icon = square_icon(size)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    icon.putalpha(mask)
    return icon


def main() -> int:
    global SOURCE_IMAGE
    if not SOURCE.exists():
        print(f"[erro] arte não encontrada: {SOURCE}")
        return 1
    SOURCE_IMAGE = Image.open(SOURCE).convert("RGB")
    size = min(SOURCE_IMAGE.size)
    SOURCE_IMAGE = SOURCE_IMAGE.crop((0, 0, size, size))

    for density, px in LAUNCHER_SIZES.items():
        folder = RES / f"mipmap-{density}"
        folder.mkdir(parents=True, exist_ok=True)
        square_icon(px).save(folder / "ic_launcher.png")
        round_icon(px).save(folder / "ic_launcher_round.png")
        print(f"mipmap-{density}/ic_launcher.png + round ({px}px)")

    for density, px in FOREGROUND_SIZES.items():
        folder = RES / f"mipmap-{density}"
        square_icon(px).save(folder / "ic_launcher_foreground.png")
        print(f"mipmap-{density}/ic_launcher_foreground.png ({px}px)")

    for relative, (width, height) in SPLASHES.items():
        target = RES / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas = gradient((width, height))
        glyph_size = int(min(width, height) * 0.34)
        glyph = square_icon(glyph_size)
        canvas.paste(glyph, ((width - glyph_size) // 2, (height - glyph_size) // 2), glyph)
        canvas.save(target)
        print(f"{relative} ({width}x{height})")

    print("\nPronto. Agora rode:  npx cap sync android")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
