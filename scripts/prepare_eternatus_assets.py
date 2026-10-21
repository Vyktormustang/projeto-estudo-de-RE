#!/usr/bin/env python3
"""Convert the PokeAPI Eternatus battle sprites to FireRed 4bpp assets.

Requires Pillow. The ROM builder consumes the small binary files produced here,
so rebuilding a ROM does not require Pillow once these assets are present.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets/eternatus/source"
OUT = ROOT / "assets/eternatus"


def resize_rgba(path: Path, size: tuple[int, int]) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    return im.resize(size, Image.Resampling.NEAREST)


def nearest_index(rgb: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> int:
    return min(range(len(palette)), key=lambda i: sum((rgb[c] - palette[i][c]) ** 2 for c in range(3))) + 1


def make_palette(images: list[Image.Image]) -> list[tuple[int, int, int]]:
    pixels = [pixel[:3] for im in images for pixel in im.getdata() if pixel[3] >= 128]
    sample = Image.new("RGB", (len(pixels), 1))
    sample.putdata(pixels)
    quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    raw = quantized.getpalette() or []
    palette = [tuple(raw[i:i + 3]) for i in range(0, 45, 3)]
    # Pillow returns exactly 15 RGB entries with colors=15; guard malformed input.
    if len(palette) != 15:
        raise ValueError(f"expected 15 opaque colors, got {len(palette)}")
    return palette


def index_image(im: Image.Image, palette: list[tuple[int, int, int]]) -> list[list[int]]:
    result = []
    for y in range(im.height):
        row = []
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            row.append(0 if a < 128 else nearest_index((r, g, b), palette))
        result.append(row)
    return result


def tiles_4bpp(pixels: list[list[int]]) -> bytes:
    height, width = len(pixels), len(pixels[0])
    if width % 8 or height % 8:
        raise ValueError("4bpp image dimensions must be multiples of 8")
    out = bytearray()
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    lo = pixels[tile_y + y][tile_x + x]
                    hi = pixels[tile_y + y][tile_x + x + 1]
                    out.append(lo | (hi << 4))
    return bytes(out)


def gba_palette(colors: list[tuple[int, int, int]]) -> bytes:
    values = [0]
    values.extend((r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10) for r, g, b in colors)
    return b"".join(value.to_bytes(2, "little") for value in values)


def main() -> None:
    normal_front = resize_rgba(SOURCE / "front.png", (64, 64))
    normal_back = resize_rgba(SOURCE / "back.png", (64, 64))
    shiny_front = resize_rgba(SOURCE / "front_shiny.png", (64, 64))
    shiny_back = resize_rgba(SOURCE / "back_shiny.png", (64, 64))

    normal_palette = make_palette([normal_front, normal_back])
    normal_front_idx = index_image(normal_front, normal_palette)
    normal_back_idx = index_image(normal_back, normal_palette)
    shiny_front_idx = index_image(shiny_front, normal_palette)
    shiny_back_idx = index_image(shiny_back, normal_palette)

    # Derive a shiny color for each normal color index by matching the same
    # source pixels in the front/back normal and shiny renders.
    corresponding: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for normal, shiny in ((normal_front_idx, shiny_front), (normal_back_idx, shiny_back)):
        for y in range(64):
            for x in range(64):
                idx = normal[y][x]
                r, g, b, a = shiny.getpixel((x, y))
                if idx and a >= 128:
                    corresponding[idx].append((r, g, b))
    shiny_palette = []
    for idx, normal_rgb in enumerate(normal_palette, start=1):
        samples = corresponding.get(idx)
        if samples:
            shiny_palette.append(tuple(sum(p[c] for p in samples) // len(samples) for c in range(3)))
        else:
            shiny_palette.append(normal_rgb)

    icon = resize_rgba(SOURCE / "front.png", (32, 32))
    icon_idx = index_image(icon, normal_palette)
    outputs = {
        "front.4bpp": tiles_4bpp(normal_front_idx),
        "back.4bpp": tiles_4bpp(normal_back_idx),
        "icon.4bpp": tiles_4bpp(icon_idx),
        "normal.pal": gba_palette(normal_palette),
        "shiny.pal": gba_palette(shiny_palette),
        "icon.pal": gba_palette(normal_palette),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        (OUT / name).write_bytes(data)
        print(f"{OUT / name}: {len(data)} bytes")
    print(f"normal opaque colors: {len(set(normal_palette))}; shiny palette entries: {len(shiny_palette)}")


if __name__ == "__main__":
    main()
