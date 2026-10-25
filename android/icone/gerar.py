#!/usr/bin/env python3
"""
Gera os ícones do app (PNG por densidade) sem dependências externas.

Desenho: fundo escuro, círculo verde e um peão branco — o mesmo motivo do
ícone adaptativo (Android 8+), em res/drawable/ic_launcher_foreground.xml.

    python3 android/icone/gerar.py
"""

import pathlib
import struct
import zlib

FUNDO = (20, 22, 26)
VERDE = (129, 182, 76)
BRANCO = (251, 251, 247)

DENSIDADES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

AMOSTRAS = 4  # supersampling por eixo


def dentro_do_pao(x, y):
    """Silhueta do peão em coordenadas normalizadas (0..1)."""
    # cabeça
    if (x - 0.5) ** 2 + (y - 0.37) ** 2 <= 0.098 ** 2:
        return True
    # corpo afunilado
    if 0.44 <= y <= 0.60 and abs(x - 0.5) <= 0.045 + (y - 0.44) * 0.35:
        return True
    # colar
    if 0.58 <= y <= 0.64 and abs(x - 0.5) <= 0.13:
        return True
    # base
    if 0.64 < y <= 0.72 and abs(x - 0.5) <= 0.13 + (y - 0.64) * 0.55:
        return True
    return False


def cor_em(x, y):
    dist = ((x - 0.5) ** 2 + (y - 0.5) ** 2) ** 0.5
    if dentro_do_pao(x, y) and dist <= 0.40:
        return BRANCO
    if dist <= 0.34:
        return VERDE
    return FUNDO


def desenhar(tamanho):
    linhas = []
    passo = 1.0 / (tamanho * AMOSTRAS)
    for py in range(tamanho):
        linhas.append(bytearray([0]))  # filtro "None"
        for px in range(tamanho):
            r = g = b = 0
            for sy in range(AMOSTRAS):
                for sx in range(AMOSTRAS):
                    x = (px * AMOSTRAS + sx + 0.5) * passo
                    y = (py * AMOSTRAS + sy + 0.5) * passo
                    cor = cor_em(x, y)
                    r += cor[0]
                    g += cor[1]
                    b += cor[2]
            total = AMOSTRAS * AMOSTRAS
            linhas[-1] += bytes((r // total, g // total, b // total, 255))
    return b"".join(linhas)


def escrever_png(caminho, tamanho):
    cru = desenhar(tamanho)
    def bloco(tipo, dados):
        return (
            struct.pack(">I", len(dados))
            + tipo
            + dados
            + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", tamanho, tamanho, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + bloco(b"IHDR", ihdr)
        + bloco(b"IDAT", zlib.compress(cru, 9))
        + bloco(b"IEND", b"")
    )
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(png)
    return len(png)


def main():
    raiz = pathlib.Path(__file__).resolve().parent.parent
    for densidade, tamanho in DENSIDADES.items():
        destino = raiz / "res" / f"mipmap-{densidade}" / "ic_launcher.png"
        bytes_ = escrever_png(destino, tamanho)
        print(f"{destino.relative_to(raiz)} — {tamanho}px, {bytes_ // 1024} KB")


if __name__ == "__main__":
    main()
