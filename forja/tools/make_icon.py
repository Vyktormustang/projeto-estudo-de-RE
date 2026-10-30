#!/usr/bin/env python3
"""make_icon.py — gera os ícones do launcher FORJA (PNG RGBA) sem dependências.

Saída: forja/android/res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png
Desenho: fundo escuro + brasa radial + bigorna estilizada (silhueta simples).

Uso:  python3 forja/tools/make_icon.py [--out DIR]
"""
from __future__ import annotations

import argparse
import math
import pathlib
import struct
import zlib

DENSIDADES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}


def png_rgba(w: int, h: int, px: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    linhas = bytearray()
    for y in range(h):
        linhas.append(0)
        linhas += px[y * w * 4:(y + 1) * w * 4]
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(linhas), 9))
            + chunk(b"IEND", b""))


def cor_fundo(u: float, v: float) -> tuple[int, int, int]:
    """Gradiente diagonal escuro (#0b0b0f -> #17171f)."""
    t = (u + v) / 2
    return (int(11 + 12 * t), int(11 + 12 * t), int(15 + 16 * t))


def brasa(u: float, v: float) -> float:
    """Intensidade 0..1 da brasa radial no centro-baixo."""
    dx, dy = (u - 0.5) * 1.15, (v - 0.62) * 1.45
    d = math.sqrt(dx * dx + dy * dy)
    return max(0.0, 1.0 - d / 0.52) ** 1.7


def bigorna(u: float, v: float) -> bool:
    """Silhueta de bigorna: base, cintura e chifre."""
    if 0.20 <= v <= 0.30 and 0.24 <= u <= 0.76:          # mesa/chifre
        if u >= 0.70 and not (v >= 0.245):               # bico do chifre
            return False
        return True
    if 0.30 <= v <= 0.36 and 0.36 <= u <= 0.64:          # cintura
        return True
    if 0.36 <= v <= 0.44 and 0.30 <= u <= 0.70:          # saia
        return True
    if 0.44 <= v <= 0.52 and 0.24 <= u <= 0.76:          # base
        return True
    return False


def desenhar(tam: int) -> bytes:
    px = bytearray()
    for y in range(tam):
        for x in range(tam):
            u, v = (x + 0.5) / tam, (y + 0.5) / tam
            r, g, b = cor_fundo(u, v)
            k = brasa(u, v)
            if k > 0:
                r = min(255, int(r + 245 * k))
                g = min(255, int(g + 128 * k))
                b = min(255, int(b + 24 * k))
            if bigorna(u, v):
                aresta = min(u - 0.24, 0.76 - u, v - 0.20, 0.52 - v)
                tom = 26 + int(120 * max(0.0, min(1.0, aresta * 6)))
                r, g, b = tom, tom - 2, tom - 4
            px += bytes((r, g, b, 255))
    return png_rgba(tam, tam, bytes(px))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent
                                        / "android" / "res"))
    a = ap.parse_args()
    base = pathlib.Path(a.out)
    for dens, tam in DENSIDADES.items():
        destino = base / f"mipmap-{dens}"
        destino.mkdir(parents=True, exist_ok=True)
        dados = desenhar(tam)
        (destino / "ic_launcher.png").write_bytes(dados)
        print(f"[icone] {destino / 'ic_launcher.png'} {tam}x{tam} ({len(dados)} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
