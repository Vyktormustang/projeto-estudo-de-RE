#!/usr/bin/env python3
"""Gera uma imagem com dois calendários anuais completos, em paisagem,
empilhados (um em cima, outro embaixo), com os dias corretamente alinhados.

Uso:
    python3 scripts/gen_calendario_dois_anos.py [ano1] [ano2] [saida.png]

Dependência: Pillow (pip install pillow)
"""

from __future__ import annotations

import calendar
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

ANOS = (2026, 2027)
SAIDA = Path("images/calendarios-2026-2027.png")

S = 2  # supersampling (renderiza em 2x e reduz depois)

LARG, ALT = 1600, 2000          # dimensões finais da imagem
MARGEM_X = 80
MARGEM_Y = 70
GAP_ANOS = 60
ALT_BLOCO = 900

PAD = 28
ALT_ANO = 100
GAP_COL = 14
GAP_LIN = 14

FONTE_DIR = Path("/usr/share/fonts/truetype/dejavu")

# Paleta
BRANCO = (255, 255, 255)
PAINEL = (243, 244, 246)
BORDA_CELULA = (214, 217, 222)
TINTA = (17, 20, 24)
CINZA = (110, 116, 124)
ACCENT = (190, 62, 44)          # fim de semana

MESES = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]
DIAS_SEMANA = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB"]


def fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    nome = "DejaVuSans-Bold.ttf" if negrito else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONTE_DIR / nome), tamanho * S)


F_ANO = fonte(84, True)
F_MES = fonte(21, True)
F_DOW = fonte(13, True)
F_DIA = fonte(19)
F_DIA_FDS = fonte(19, True)


def px(v: float) -> int:
    return int(round(v * S))


def texto_central(draw, cx, cy, texto, font, fill):
    draw.text((px(cx), px(cy)), texto, font=font, fill=fill, anchor="mm")


def desenha_bloco(img, draw, ano: int, topo: float) -> None:
    # painel do ano
    draw.rounded_rectangle(
        [px(MARGEM_X), px(topo), px(MARGEM_X + LARG - 2 * MARGEM_X), px(topo + ALT_BLOCO)],
        radius=px(18), fill=PAINEL,
    )

    cx = LARG / 2
    # ano
    texto_central(draw, cx, topo + 24 + ALT_ANO / 2 - 6, str(ano), F_ANO, TINTA)
    draw.line(
        [px(MARGEM_X + PAD), px(topo + 24 + ALT_ANO - 14),
         px(LARG - MARGEM_X - PAD), px(topo + 24 + ALT_ANO - 14)],
        fill=(226, 229, 234), width=px(1),
    )

    largura_util = LARG - 2 * MARGEM_X - 2 * PAD
    largura_mes = (largura_util - 3 * GAP_COL) / 4
    topo_meses = topo + 24 + ALT_ANO
    altura_util = ALT_BLOCO - (topo_meses - topo) - PAD / 2
    altura_mes = (altura_util - 2 * GAP_LIN) / 3

    for i, nome in enumerate(MESES):
        col, lin = i % 4, i // 4
        x = MARGEM_X + PAD + col * (largura_mes + GAP_COL)
        y = topo_meses + lin * (altura_mes + GAP_LIN)

        draw.rounded_rectangle(
            [px(x), px(y), px(x + largura_mes), px(y + altura_mes)],
            radius=px(8), fill=BRANCO, outline=BORDA_CELULA, width=px(1),
        )

        texto_central(draw, x + largura_mes / 2, y + 24, nome, F_MES, TINTA)

        col_w = largura_mes / 7
        base = y + 44
        for d, sigla in enumerate(DIAS_SEMANA):
            cor = ACCENT if d in (0, 6) else CINZA
            texto_central(draw, x + col_w * (d + 0.5), base + 8, sigla, F_DOW, cor)

        # dias
        primeiro_dia, dias_no_mes = calendar.monthrange(ano, i + 1)
        # monthrange: segunda=0 ... domingo=6 -> converter para domingo=0
        deslocamento = (primeiro_dia + 1) % 7
        y0 = base + 22
        passo = (y + altura_mes - 8 - y0) / 6
        for n in range(dias_no_mes):
            pos = deslocamento + n
            c, l = pos % 7, pos // 7
            if l >= 6:
                continue
            fds = c in (0, 6)
            texto_central(
                draw,
                x + col_w * (c + 0.5),
                y0 + passo * l + passo / 2,
                str(n + 1),
                F_DIA_FDS if fds else F_DIA,
                ACCENT if fds else TINTA,
            )


def main() -> None:
    ano1 = int(sys.argv[1]) if len(sys.argv) > 1 else ANOS[0]
    ano2 = int(sys.argv[2]) if len(sys.argv) > 2 else ANOS[1]
    saida = Path(sys.argv[3]) if len(sys.argv) > 3 else SAIDA

    img = Image.new("RGB", (LARG * S, ALT * S), BRANCO)
    draw = ImageDraw.Draw(img)

    desenha_bloco(img, draw, ano1, MARGEM_Y)
    desenha_bloco(img, draw, ano2, MARGEM_Y + ALT_BLOCO + GAP_ANOS)

    img = img.resize((LARG, ALT), Image.LANCZOS)

    saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(saida, optimize=True)
    print(f"ok: {saida} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
