#!/usr/bin/env python3
"""Dois calendários anuais completos, empilhados, com tema bíblico.

Layout: cada ano é um bloco em paisagem (12 meses em grade 4x3), o de cima
sobre o de baixo. Estética: pergaminho, tinta sépia, dourado, capitular
gótica (Cinzel) e serifada clássica (EB Garamond) + versículo em itálico.

Uso:
    python3 scripts/gen_calendario_biblico.py [ano1] [ano2] [saida.png]

Dependências: pillow, numpy (fonte: assets/fonts/*.ttf)
"""

from __future__ import annotations

import calendar
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

SAIDA = Path("images/calendario-biblico-2026-2027.png")
FONTES = Path(__file__).resolve().parent.parent / "assets" / "fonts"

S = 2  # supersampling

LARG, ALT = 1600, 2000
MARGEM_X, MARGEM_Y = 70, 60
GAP_ANOS = 46
ALT_BLOCO = 890
PAD = 26
ALT_ANO = 118
GAP_COL, GAP_LIN = 13, 13

# Paleta "pergaminho + tinta sépia + dourado"
PAPEL = (244, 236, 219)
PAPEL_CLARO = (250, 245, 233)
TINTA = (58, 44, 32)
TINTA_SUAVE = (110, 92, 72)
OURO = (176, 141, 68)
OURO_ESCURO = (142, 112, 50)
VINHO = (128, 46, 40)
BORDA = (216, 202, 176)

MESES = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]
DOW = ["D", "S", "T", "Q", "Q", "S", "S"]
DOW_ROMANO = ["I", "II", "III", "IV", "V", "VI", "VII"]

VERSICULOS = {
    2026: ("“O Senhor é o meu pastor; nada me faltará.”", "SALMOS 23:1"),
    2027: ("“Eis que faço novas todas as coisas.”", "APOCALIPSE 21:5"),
}


def fonte(nome: str, tamanho: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTES / nome), int(round(tamanho * S)))


F_ANO = fonte("Cinzel-Bold.ttf", 88)
F_MES = fonte("Cinzel-SemiBold.ttf", 17)
F_DOW = fonte("EBGaramond-SemiBold.ttf", 15)
F_DIA = fonte("EBGaramond-Regular-LF.ttf", 20)
F_DIA_FDS = fonte("EBGaramond-SemiBold-LF.ttf", 20)
F_VERS = fonte("EBGaramond-Italic.ttf", 21)
F_REF = fonte("EBGaramond-SemiBold-LF.ttf", 13)
F_RODAPE = fonte("Cinzel-SemiBold.ttf", 12)


def px(v: float) -> int:
    return int(round(v * S))


def texto(draw, cx, cy, s, font, fill, anchor="mm", tracking=0.0):
    """Texto centralizado, com espaçamento opcional entre letras (em px)."""
    if not tracking:
        draw.text((px(cx), px(cy)), s, font=font, fill=fill, anchor=anchor)
        return
    largura = sum(draw.textlength(ch, font=font) for ch in s) + tracking * S * (len(s) - 1)
    x = px(cx) - largura / 2
    for ch in s:
        draw.text((x, px(cy)), ch, font=font, fill=fill, anchor="lm")
        x += draw.textlength(ch, font=font) + tracking * S


@lru_cache(maxsize=8)
def textura_papel(larg: int, alt: int, semente: int) -> Image.Image:
    """Textura sutil de pergaminho: ruído suave + vinheta quente."""
    rng = np.random.default_rng(semente)
    base = rng.normal(0, 1, (alt // 4, larg // 4))
    img = Image.fromarray(((base - base.min()) / (base.max() - base.min()) * 255).astype("uint8"))
    img = img.resize((larg, alt), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    n = np.asarray(img, dtype=np.float32) / 255.0
    n = (n - 0.5) * 2.0

    yy, xx = np.mgrid[0:alt, 0:larg]
    cx, cy = larg / 2, alt / 2
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / 1.35
    vinheta = np.clip(r, 0, 1)[..., None]

    papel = np.array(PAPEL, dtype=np.float32)
    tons_escuro = np.array((226, 212, 182), dtype=np.float32)
    campo = papel * (1 - vinheta * 0.55) + tons_escuro * (vinheta * 0.55)
    campo = campo + n[..., None] * 7.0
    return Image.fromarray(np.clip(campo, 0, 255).astype("uint8"))


def ornamento(draw, cx, cy, largura, cor, florao=True):
    """Linha dupla com losango central e, opcionalmente, florão."""
    if florao:
        meio = largura * 0.36
        y = px(cy)
        draw.line([px(cx - largura / 2), y, px(cx - meio), y], fill=cor, width=px(1.1))
        draw.line([px(cx + meio), y, px(cx + largura / 2), y], fill=cor, width=px(1.1))
        # losango
        d = 5.2
        draw.polygon(
            [(px(cx), px(cy - d)), (px(cx + d * 0.62), px(cy)), (px(cx), px(cy + d)), (px(cx - d * 0.62), px(cy))],
            fill=cor,
        )
        # pontinhos
        for side in (-1, 1):
            for k in (0.30, 0.44):
                draw.ellipse(
                    [px(cx + side * largura * k - 1.4), px(cy - 1.4),
                     px(cx + side * largura * k + 1.4), px(cy + 1.4)],
                    fill=cor,
                )
    else:
        y = px(cy)
        draw.line([px(cx - largura / 2), y, px(cx + largura / 2), y], fill=cor, width=px(1.0))


def cruz(draw, cx, cy, h, cor, esp=5.0):
    """Cruz latina discreta, desenhada (as fontes não têm o glifo)."""
    topo, base = cy - h / 2, cy + h / 2
    braco = cy - h * 0.16
    draw.rectangle([px(cx - esp / 2), px(topo), px(cx + esp / 2), px(base)], fill=cor)
    draw.rectangle([px(cx - h * 0.30), px(braco - esp / 2), px(cx + h * 0.30), px(braco + esp / 2)], fill=cor)


def cantos(draw, x0, y0, x1, y1, cor, tam=20):
    """Cantos ornamentados: dois filetes em L."""
    w = px(1.4)
    t = px(tam)
    for (x, y, dx, dy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        draw.line([px(x), px(y + dy * 4), px(x), px(y + dy * t)], fill=cor, width=w)
        draw.line([px(x + dx * 4), px(y), px(x + dx * t), px(y)], fill=cor, width=w)
        d = 3.4
        draw.polygon(
            [(px(x), px(y - d)), (px(x + d), px(y)), (px(x), px(y + d)), (px(x - d), px(y))], fill=cor
        )


def desenha_ano(draw, ano: int, topo: float) -> None:
    ano = int(ano)
    painel = [px(MARGEM_X), px(topo), px(LARG - MARGEM_X), px(topo + ALT_BLOCO)]
    draw.rounded_rectangle(painel, radius=px(10), fill=PAPEL_CLARO, outline=BORDA, width=px(1.4))
    draw.rounded_rectangle(
        [painel[0] + px(6), painel[1] + px(6), painel[2] - px(6), painel[3] - px(6)],
        radius=px(6), outline=OURO, width=px(1),
    )
    cantos(draw, MARGEM_X + 6, topo + 6, LARG - MARGEM_X - 6, topo + ALT_BLOCO - 6, OURO_ESCURO, tam=18)

    cx = LARG / 2
    # cruz + ano
    cruz(draw, cx, topo + 26, 20, OURO_ESCURO, esp=3.8)
    texto(draw, cx, topo + 68, str(ano), F_ANO, TINTA, tracking=9)

    # ornamento + versículo
    ornamento(draw, cx, topo + 114, 320, OURO_ESCURO, florao=False)
    vers, ref = VERSICULOS.get(ano, ("", ""))
    if vers:
        texto(draw, cx, topo + 140, vers, F_VERS, TINTA_SUAVE)
        texto(draw, cx, topo + 164, ref, F_REF, OURO_ESCURO, tracking=1.6)

    largura_util = LARG - 2 * MARGEM_X - 2 * PAD
    largura_mes = (largura_util - 3 * GAP_COL) / 4
    topo_meses = topo + 190
    altura_util = ALT_BLOCO - (topo_meses - topo) - PAD
    altura_mes = (altura_util - 2 * GAP_LIN) / 3

    for i, nome in enumerate(MESES):
        col, lin = i % 4, i // 4
        x = MARGEM_X + PAD + col * (largura_mes + GAP_COL)
        y = topo_meses + lin * (altura_mes + GAP_LIN)

        draw.rounded_rectangle(
            [px(x), px(y), px(x + largura_mes), px(y + altura_mes)],
            radius=px(5), fill=PAPEL, outline=BORDA, width=px(1),
        )

        texto(draw, x + largura_mes / 2, y + 21, nome, F_MES, TINTA, tracking=1.5)
        ornamento(draw, x + largura_mes / 2, y + 36, largura_mes * 0.42, OURO, florao=False)

        col_w = largura_mes / 7
        base = y + 48
        for d, sigla in enumerate(DOW):
            texto(draw, x + col_w * (d + 0.5), base, sigla, F_DOW, VINHO if d in (0, 6) else TINTA_SUAVE)

        primeiro, dias_no_mes = calendar.monthrange(ano, i + 1)
        desloc = (primeiro + 1) % 7          # domingo = 0
        y0 = base + 14
        passo = (y + altura_mes - 8 - y0) / 6
        for n in range(dias_no_mes):
            pos = desloc + n
            c, l = pos % 7, pos // 7
            if l >= 6:
                continue
            fds = c in (0, 6)
            texto(
                draw,
                x + col_w * (c + 0.5),
                y0 + passo * l + passo / 2,
                str(n + 1),
                F_DIA_FDS if fds else F_DIA,
                VINHO if fds else TINTA,
            )


def main() -> None:
    ano1 = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    ano2 = int(sys.argv[2]) if len(sys.argv) > 2 else 2027
    saida = Path(sys.argv[3]) if len(sys.argv) > 3 else SAIDA

    img = textura_papel(LARG * S, ALT * S, 20261116).convert("RGB")
    draw = ImageDraw.Draw(img)

    desenha_ano(draw, ano1, MARGEM_Y)
    desenha_ano(draw, ano2, MARGEM_Y + ALT_BLOCO + GAP_ANOS)

    # filete central separando os dois anos
    meio = MARGEM_Y + ALT_BLOCO + GAP_ANOS / 2
    y = px(meio)
    for lado in (-1, 1):
        draw.line([px(LARG / 2 + lado * 26), y, px(LARG / 2 + lado * 250), y], fill=OURO, width=px(1.1))
        draw.ellipse([px(LARG / 2 + lado * 16 - 2.2), y - px(2.2),
                      px(LARG / 2 + lado * 16 + 2.2), y + px(2.2)], fill=OURO_ESCURO)
    d = 6.0
    draw.polygon([(px(LARG / 2), px(meio - d)), (px(LARG / 2 + d * 0.65), y),
                  (px(LARG / 2), px(meio + d)), (px(LARG / 2 - d * 0.65), y)], fill=OURO_ESCURO)

    # rodapé
    texto(
        draw, LARG / 2, ALT - 26,
        "LÂMPADA PARA OS MEUS PÉS É A TUA PALAVRA · SALMOS 119:105",
        F_RODAPE, TINTA_SUAVE, tracking=2.2,
    )

    img = img.resize((LARG, ALT), Image.LANCZOS)
    saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(saida, optimize=True)
    print(f"ok: {saida} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
