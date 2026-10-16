#!/usr/bin/env python3
"""Localiza o sprite do jogador (touca vermelha) num PNG 240x160 do GBA."""
import sys
from PIL import Image

def find_player(png):
    im = Image.open(png).convert("RGB")
    px = im.load()
    best = 0
    bx = by = 0
    # procura quadrante 8x8 com maior densidade de vermelho (touca do Red)
    for y0 in range(0, 152, 2):
        for x0 in range(0, 232, 2):
            n = 0
            for dy in range(8):
                for dx in range(8):
                    r, g, b = px[x0 + dx, y0 + dy]
                    if r > 200 and g < 90 and b < 110:
                        n += 1
            if n > best:
                best, bx, by = n, x0, y0
    return bx, by, best

if __name__ == "__main__":
    for p in sys.argv[1:]:
        x, y, n = find_player(p)
        print(f"{p.split('/')[-1]:24}: x={x:3} y={y:3} (vermelhos={n})")
