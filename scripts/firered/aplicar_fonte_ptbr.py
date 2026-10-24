#!/usr/bin/env python3
"""T1 da tradução PT-BR: adiciona ã, õ, Ã, Õ às fontes latinas do pokefirered.

O charset Gen 3 ocidental NÃO tem ã/õ (tem á é í ó ú â ê ô ç à ñ, mas nada
com til além do ñ). Todos os 256 códigos estão ocupados, então REAPROVEITAMOS
glifos que o português nunca usa — provado por grep que nenhum texto do jogo
os usa:

    código  era   vira
    0x09    Ì     Ã
    0x10    Œ     Õ
    0x1E    ì     ã
    0x22    ò     õ

O pixel art é composto programaticamente: pega o glifo acentuado base
(Â/Ô/â/ô), apaga o circunflexo (bloco de linhas acima da primeira linha
vazia) e carimba no lugar o til do Ñ/ñ, alinhado pelo centro e pela base do
acento original. Isso é feito nas 4 fontes latinas (normal, male, female,
small — layout: células 16×16, 16 por linha, id do glifo = linha*16+coluna).

Também atualiza: charmap.txt (mapeamento dos chars) e as 5 tabelas de
largura em src/text.c (largura do novo glifo = largura do glifo base).

Uso:
    python3 aplicar_fonte_ptbr.py --pokefirered /tmp/pokefirered --check
    python3 aplicar_fonte_ptbr.py --pokefirered /tmp/pokefirered --write
    python3 aplicar_fonte_ptbr.py --self-test

Windows: rode dentro do WSL (ver docs/FIRERED.md).
Idempotente: --write duas vezes dá no mesmo.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import png_indexado

# (código, char novo, char antigo, código do glifo base, código do til)
TROCAS = [
    (0x09, "Ã", "Ì", 0x03, 0x14),  # base Â, til do Ñ
    (0x10, "Õ", "Œ", 0x0F, 0x14),  # base Ô, til do Ñ
    (0x1E, "ã", "ì", 0x68, 0x29),  # base â, til do ñ
    (0x22, "õ", "ò", 0x24, 0x29),  # base ô, til do ñ
]

# (arquivo, largura da célula em px) — small usa células 8x16, 32 por linha!
FONTES = [
    ("graphics/fonts/latin_normal.png", 16),
    ("graphics/fonts/latin_male.png", 16),
    ("graphics/fonts/latin_female.png", 16),
    ("graphics/fonts/latin_small.png", 8),
]

TABELAS_LARGURA = [
    "sFontSmallLatinGlyphWidths",
    "sFontNormalCopy1LatinGlyphWidths",
    "sFontNormalLatinGlyphWidths",
    "sFontMaleLatinGlyphWidths",
    "sFontFemaleLatinGlyphWidths",
]

CEL = 16  # célula 16×16 px


# ---------------------------------------------------------------- pixels

def _celula(linhas, codigo, cw=16):
    """Matriz cw×16 (lista de listas) da célula do glifo `codigo`."""
    por_linha = 256 // cw
    cx, cy = (codigo % por_linha) * cw, (codigo // por_linha) * CEL
    return [[linhas[cy + y][cx + x] for x in range(cw)] for y in range(CEL)]


def _gravar_celula(linhas, codigo, cel, cw=16):
    por_linha = 256 // cw
    cx, cy = (codigo % por_linha) * cw, (codigo // por_linha) * CEL
    for y in range(CEL):
        for x in range(cw):
            linhas[cy + y][cx + x] = cel[y][x]


# Nas fontes do pokefirered cada célula tem FUNDO índice 3 dentro da caixa do
# glifo (0 = fora da caixa, 1 = tinta, 2 = sombra). Para detectar estrutura,
# "vazio" é {0, 3}; tinta de verdade é {1, 2}.
TINTA = (1, 2)


def _bloco_acento(cel):
    """Linhas do acento: com tinta, do topo até a primeira linha sem tinta."""
    linhas = []
    comecou = False
    for y in range(len(cel)):
        vazia = all(v not in TINTA for v in cel[y])
        if not vazia:
            comecou = True
            linhas.append(y)
        elif comecou:
            break
    if len(linhas) > 5:
        raise ValueError(f"bloco de acento suspeito ({len(linhas)} linhas)")
    return linhas


def _bbox_x(cel, linhas):
    xs = [x for y in linhas for x in range(len(cel[0])) if cel[y][x] in TINTA]
    return (min(xs), max(xs)) if xs else (0, 0)


def compor_glifo(base_cel, tilde_cel):
    """Glifo novo: base sem o acento + til carimbado na posição do acento."""
    acento = _bloco_acento(base_cel)
    til = _bloco_acento(tilde_cel)
    if not acento or not til:
        raise ValueError("não achei bloco de acento/til (fonte inesperada)")
    novo = [linha[:] for linha in base_cel]
    for y in acento:  # apaga o circunflexo (vira fundo, preservando a caixa)
        novo[y] = [3 if v in TINTA else v for v in novo[y]]
    larg = len(novo[0])
    # alinhar: base do til na base do acento; centros horizontais coincidem
    dy = acento[-1] - til[-1]
    a0, a1 = _bbox_x(base_cel, acento)
    t0, t1 = _bbox_x(tilde_cel, til)
    dx = round(((a0 + a1) - (t0 + t1)) / 2)
    for y in til:
        for x in range(len(tilde_cel[0])):
            v = tilde_cel[y][x]
            if v in TINTA:  # só tinta/sombra; fundo fica o da base
                ny, nx = y + dy, x + dx
                if 0 <= ny < len(novo) and 0 <= nx < larg:
                    novo[ny][nx] = v
    return novo


# ---------------------------------------------------------------- arquivos

def patch_png(caminho: Path, escrever: bool, cw: int = 16) -> bool:
    """True se o arquivo já está (ou ficou) correto."""
    png = png_indexado.ler(caminho)
    mudou = False
    for codigo, _novo, _velho, cod_base, cod_til in TROCAS:
        alvo = compor_glifo(
            _celula(png.linhas, cod_base, cw),
            _celula(png.linhas, cod_til, cw),
        )
        if _celula(png.linhas, codigo, cw) != alvo:
            mudou = True
            if escrever:
                _gravar_celula(png.linhas, codigo, alvo, cw)
    if mudou and escrever:
        png_indexado.escrever(png, caminho)
        return True
    return not mudou


def patch_charmap(caminho: Path, escrever: bool) -> bool:
    texto = caminho.read_text(encoding="utf-8")
    ok = True
    for codigo, novo, velho, _b, _t in TROCAS:
        certo = f"'{novo}' = {codigo:02X}"
        if re.search(rf"^'{re.escape(novo)}'\s*=\s*{codigo:02X}\b", texto, re.M):
            continue
        ok = False
        padrao = rf"^'{re.escape(velho)}'(\s*)=\s*{codigo:02X}[ \t]*$"
        if not re.search(padrao, texto, re.M):
            raise ValueError(f"charmap sem a linha esperada {velho}={codigo:02X}")
        texto = re.sub(
            padrao,
            f"'{novo}'\\1= {codigo:02X} @ era '{velho}' — reaproveitado p/ PT-BR",
            texto, flags=re.M,
        )
    if not ok and escrever:
        caminho.write_text(texto, encoding="utf-8")
        return True
    return ok


def patch_larguras(caminho: Path, escrever: bool) -> bool:
    """Copia largura do glifo base para o novo em cada tabela latina."""
    texto = caminho.read_text(encoding="utf-8")
    ok = True
    for nome in TABELAS_LARGURA:
        m = re.search(rf"{nome}\[\]\s*=\s*\n?{{(.*?)}}", texto, re.S)
        if not m:
            raise ValueError(f"não achei a tabela {nome} em {caminho}")
        corpo = m.group(1)
        nums = re.findall(r"\d+", corpo)
        if len(nums) < 0x69:
            raise ValueError(f"{nome}: só {len(nums)} entradas?")
        novos = nums[:]
        for codigo, _n, _v, cod_base, _t in TROCAS:
            novos[codigo] = nums[cod_base]
        if novos != nums:
            ok = False
            if escrever:
                it = iter(novos)
                corpo_novo = re.sub(r"\d+", lambda _m: next(it), corpo)
                texto = texto.replace(corpo, corpo_novo, 1)
    if not ok and escrever:
        caminho.write_text(texto, encoding="utf-8")
        return True
    return ok


def aplicar(raiz: Path, escrever: bool) -> bool:
    tudo_ok = True
    for rel, cw in FONTES:
        ok = patch_png(raiz / rel, escrever, cw)
        print(f"{'ok' if ok else 'PENDENTE'}  {rel}")
        tudo_ok &= ok
    ok = patch_charmap(raiz / "charmap.txt", escrever)
    print(f"{'ok' if ok else 'PENDENTE'}  charmap.txt")
    tudo_ok &= ok
    ok = patch_larguras(raiz / "src/text.c", escrever)
    print(f"{'ok' if ok else 'PENDENTE'}  src/text.c (larguras)")
    tudo_ok &= ok
    return tudo_ok


# ---------------------------------------------------------------- self-test

def self_test() -> int:
    falhas = 0

    def caso(nome, cond):
        nonlocal falhas
        print(f"{'ok' if cond else 'FALHOU'}  {nome}")
        if not cond:
            falhas += 1

    # célula sintética: "letra" nas linhas 6-12, circunflexo nas 1-3
    base = [[0] * CEL for _ in range(CEL)]
    for y in (1, 2):
        base[y][4 + y] = 1  # acento torto qualquer
    for y in range(6, 13):
        for x in range(3, 9):
            base[y][x] = 1
    tilde_src = [[0] * CEL for _ in range(CEL)]
    for x in range(3, 8):
        tilde_src[2][x] = 2  # til na linha 2
    for y in range(5, 13):
        tilde_src[y][5] = 1

    novo = compor_glifo(base, tilde_src)
    caso("acento original apagado", all(novo[1][x] != 1 for x in range(CEL)))
    caso("til presente acima da letra", any(2 in linha for linha in novo[:5]))
    caso("corpo da letra intacto", novo[8][4] == 1)
    caso("linhas da letra sem til", all(2 not in novo[y] for y in range(6, 13)))

    # bloco de acento: para no primeiro vão
    caso("_bloco_acento acha 1-2", _bloco_acento(base) == [1, 2])

    # idempotência de compor (compor de novo dá igual)
    caso("composição determinística", compor_glifo(base, tilde_src) == novo)

    print(f"\nself-test: {'PASS' if falhas == 0 else f'{falhas} FALHA(S)'}")
    return falhas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pokefirered", type=Path, help="raiz do clone pret/pokefirered")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if not args.pokefirered:
        ap.error("--pokefirered é obrigatório (ou use --self-test)")
    ok = aplicar(args.pokefirered, escrever=args.write)
    if args.check and not args.write:
        sys.exit(0 if ok else 1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
