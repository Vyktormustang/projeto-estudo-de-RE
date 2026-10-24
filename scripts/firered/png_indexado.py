#!/usr/bin/env python3
"""Ler, recortar e recolorir PNG indexado (paleta), sem dependencia nenhuma.

Por que isso existe
-------------------
Os gráficos do RHH (pokeemerald-expansion) são PNG **indexados** — 4 ou 8 bits
por pixel, com a paleta embutida no chunk `PLTE`. O FireRed espera 64×64 no
sprite de frente, mas **419 das 639 espécies novas** do RHH só têm
`anim_front.png`, que é 64×**128** (dois quadros de animação). O FireRed não
sabe lidar com dois quadros: ele lê 64×64.

Converter com `gbagfx` e cortar os bytes depois *quase* funciona (o dump é
linear), mas o build do FireRed converte o PNG na hora (`%.4bpp: %.png`), então
o que precisa ser recortado é o **PNG**, não o `.4bpp`. Daí este módulo.

Também serve para o caso dos ícones: o RHH usa 6 paletas de ícone
(`iconPalIndex` 0-5) e o FireRed só tem 3 (que são idênticas às 0-2 do RHH).
Para as 17 espécies com índice 3-5 é preciso **remapear as cores** para a
paleta mais próxima — `remapear()` faz isso escolhendo, cor a cor, o índice
mais próximo em RGB.

Escopo: só o que esses sprites usam — PNG indexado (color type 3), 4 ou 8 bits,
sem entrelaçamento. Qualquer outra coisa levanta `ValueError` em vez de gerar
um arquivo torto em silêncio.

Uso
---
    from png_indexado import ler, escrever, recortar_altura, remapear

    python3 scripts/firered/png_indexado.py --self-test
"""
from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

ASSINATURA = b"\x89PNG\r\n\x1a\n"


class Png:
    """PNG indexado em memória: largura, altura, índices por linha e paleta."""

    def __init__(self, largura: int, altura: int, linhas: list[list[int]],
                 paleta: list[tuple[int, int, int]], transparencia: bytes | None,
                 profundidade: int = 8):
        self.largura = largura
        self.altura = altura
        self.linhas = linhas
        self.paleta = paleta
        self.transparencia = transparencia
        self.profundidade = profundidade

    def __eq__(self, outro: object) -> bool:
        return (isinstance(outro, Png) and self.largura == outro.largura
                and self.altura == outro.altura and self.linhas == outro.linhas
                and self.paleta == outro.paleta
                and self.transparencia == outro.transparencia)

    def __repr__(self) -> str:
        return (f"Png({self.largura}x{self.altura}, {self.profundidade}bpp, "
                f"{len(self.paleta)} cores)")


# --------------------------------------------------------------------------- #
# Decodificação
# --------------------------------------------------------------------------- #
def _chunks(dados: bytes):
    if dados[:8] != ASSINATURA:
        raise ValueError("nao e' um PNG")
    i = 8
    while i < len(dados):
        (tam,) = struct.unpack(">I", dados[i:i + 4])
        tipo = dados[i + 4:i + 8]
        corpo = dados[i + 8:i + 8 + tam]
        yield tipo, corpo
        i += 12 + tam


def _pixels_da_linha(bruta: bytes, profundidade: int, largura: int) -> list[int]:
    if profundidade == 8:
        return list(bruta[:largura])
    if profundidade == 4:
        saida = []
        for b in bruta:
            saida.append(b >> 4)
            saida.append(b & 0xF)
        return saida[:largura]
    if profundidade == 2:  # fontes do pokefirered (latin_*.png) são 2 bpp
        saida = []
        for b in bruta:
            saida += [(b >> 6) & 3, (b >> 4) & 3, (b >> 2) & 3, b & 3]
        return saida[:largura]
    raise ValueError(f"profundidade {profundidade} nao suportada (so 2, 4 e 8)")


def _desfiltrar(tipo: int, linha: bytes, anterior: bytes, bpp: int) -> bytes:
    """Desfaz o filtro PNG (0-4). `bpp` = bytes por pixel (1 para indexado)."""
    if tipo == 0:
        return bytes(linha)
    saida = bytearray(len(linha))
    if tipo == 1:      # Sub
        for i, v in enumerate(linha):
            esq = saida[i - bpp] if i >= bpp else 0
            saida[i] = (v + esq) & 0xFF
    elif tipo == 2:    # Up
        for i, v in enumerate(linha):
            saida[i] = (v + anterior[i]) & 0xFF
    elif tipo == 3:    # Average
        for i, v in enumerate(linha):
            esq = saida[i - bpp] if i >= bpp else 0
            saida[i] = (v + ((esq + anterior[i]) >> 1)) & 0xFF
    elif tipo == 4:    # Paeth
        for i, v in enumerate(linha):
            a = saida[i - bpp] if i >= bpp else 0
            b = anterior[i]
            c = anterior[i - bpp] if i >= bpp else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            saida[i] = (v + pr) & 0xFF
    else:
        raise ValueError(f"filtro PNG {tipo} desconhecido")
    return bytes(saida)


def ler(caminho: str | Path) -> Png:
    dados = Path(caminho).read_bytes()
    ihdr = None
    paleta: list[tuple[int, int, int]] = []
    trns = None
    idat = b""
    for tipo, corpo in _chunks(dados):
        if tipo == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", corpo)
        elif tipo == b"PLTE":
            paleta = [tuple(corpo[i:i + 3]) for i in range(0, len(corpo), 3)]
        elif tipo == b"tRNS":
            trns = corpo
        elif tipo == b"IDAT":
            idat += corpo
        elif tipo == b"IEND":
            break
    if ihdr is None:
        raise ValueError("PNG sem IHDR")
    largura, altura, prof, cor, comp, filtro, entrel = ihdr
    if cor != 3:
        raise ValueError(f"color type {cor}: so' indexado (3) e' suportado")
    if entrel != 0:
        raise ValueError("PNG entrelacado nao suportado")
    if comp != 0 or filtro != 0:
        raise ValueError("compressao/filtro de PNG inesperados")

    cru = zlib.decompress(idat)
    bpl = (largura * prof + 7) // 8           # bytes por linha
    linhas: list[list[int]] = []
    anterior = bytes(bpl)
    pos = 0
    for _ in range(altura):
        tipo_filtro = cru[pos]
        bruta = cru[pos + 1:pos + 1 + bpl]
        pos += 1 + bpl
        linha = _desfiltrar(tipo_filtro, bruta, anterior, 1)
        anterior = linha
        linhas.append(_pixels_da_linha(linha, prof, largura))
    return Png(largura, altura, linhas, paleta, trns, prof)


def ler_rgb(caminho: str | Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    """Lê PNG truecolor (RGB/RGBA, 8 bits) para `(largura, altura, pixels)`.

    Os PNG do RHH são indexados (o `ler()` cuida deles); as capturas de tela do
    emulador saem em truecolor. Para medir sprite em screenshot (contar quantos
    pixels não são do fundo) é preciso deste caminho.
    """
    dados = Path(caminho).read_bytes()
    ihdr = None
    idat = b""
    for tipo, corpo in _chunks(dados):
        if tipo == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", corpo)
        elif tipo == b"IDAT":
            idat += corpo
        elif tipo == b"IEND":
            break
    if ihdr is None:
        raise ValueError("PNG sem IHDR")
    largura, altura, prof, cor, comp, filtro, entrel = ihdr
    if cor not in (2, 6) or prof != 8 or entrel != 0:
        raise ValueError(f"ler_rgb: esperava RGB/RGBA 8 bits sem entrelacar "
                         f"(veio color={cor} prof={prof} entrel={entrel})")
    canais = 3 if cor == 2 else 4
    cru = zlib.decompress(idat)
    bpl = largura * canais
    pixels: list[tuple[int, int, int]] = []
    anterior = bytes(bpl)
    pos = 0
    for _ in range(altura):
        tipo_filtro = cru[pos]
        bruta = cru[pos + 1:pos + 1 + bpl]
        pos += 1 + bpl
        linha = _desfiltrar(tipo_filtro, bruta, anterior, canais)
        anterior = linha
        for x in range(largura):
            i = x * canais
            pixels.append((linha[i], linha[i + 1], linha[i + 2]))
    return largura, altura, pixels


# --------------------------------------------------------------------------- #
# Codificação
# --------------------------------------------------------------------------- #
def _chunk(tipo: bytes, corpo: bytes) -> bytes:
    return (struct.pack(">I", len(corpo)) + tipo + corpo
            + struct.pack(">I", zlib.crc32(tipo + corpo) & 0xFFFFFFFF))


def escrever(png: Png, caminho: str | Path) -> None:
    prof = png.profundidade
    if prof not in (2, 4, 8):
        raise ValueError("so' grava 2, 4 ou 8 bits")
    linhas = bytearray()
    for linha in png.linhas:
        linhas.append(0)                      # filtro None: previsível e estável
        if prof == 8:
            linhas += bytes(linha)
        elif prof == 4:
            for i in range(0, png.largura, 2):
                alto = linha[i] & 0xF
                baixo = (linha[i + 1] & 0xF) if i + 1 < png.largura else 0
                linhas.append((alto << 4) | baixo)
        else:  # 2 bpp (4 pixels por byte)
            for i in range(0, png.largura, 4):
                b = 0
                for j in range(4):
                    v = (linha[i + j] & 3) if i + j < png.largura else 0
                    b |= v << (6 - 2 * j)
                linhas.append(b)
    ihdr = struct.pack(">IIBBBBB", png.largura, png.altura, prof, 3, 0, 0, 0)
    plte = b"".join(bytes(c) for c in png.paleta)
    saida = [ASSINATURA, _chunk(b"IHDR", ihdr), _chunk(b"PLTE", plte)]
    if png.transparencia:
        saida.append(_chunk(b"tRNS", png.transparencia))
    saida.append(_chunk(b"IDAT", zlib.compress(bytes(linhas), 9)))
    saida.append(_chunk(b"IEND", b""))
    Path(caminho).write_bytes(b"".join(saida))


# --------------------------------------------------------------------------- #
# Operações
# --------------------------------------------------------------------------- #
def recortar_altura(png: Png, altura: int) -> Png:
    """Mantém só as primeiras `altura` linhas (primeiro quadro de uma animação)."""
    if altura > png.altura:
        raise ValueError(f"pediu {altura} linhas de um PNG com {png.altura}")
    return Png(png.largura, altura, [list(l) for l in png.linhas[:altura]],
               list(png.paleta), png.transparencia, png.profundidade)


def _dist2(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def mapa_de_cores(origem: list[tuple[int, int, int]],
                  destino: list[tuple[int, int, int]]) -> list[int]:
    """Para cada cor da paleta de origem, o índice mais próximo no destino.

    O índice 0 é transparente nas duas pontas (convenção do Gen 3): fica fixo em
    0 para não furar o sprite.
    """
    mapa = [0]
    for cor in origem[1:]:
        melhor, melhor_d = 0, None
        for i, cand in enumerate(destino):
            if i == 0:
                continue
            d = _dist2(cor, cand)
            if melhor_d is None or d < melhor_d:
                melhor, melhor_d = i, d
        mapa.append(melhor)
    return mapa


def remapear(png: Png, destino: list[tuple[int, int, int]]) -> Png:
    """Reescreve o PNG com a paleta `destino` (cores mais próximas)."""
    if len(destino) < 2:
        raise ValueError("paleta de destino vazia")
    mapa = mapa_de_cores(png.paleta, destino)
    linhas = [[mapa[i] if i < len(mapa) else 0 for i in l] for l in png.linhas]
    # transparência do índice 0 continua valendo
    trns = b"\x00" if png.transparencia is not None else None
    return Png(png.largura, png.altura, linhas, list(destino), trns, png.profundidade)


def ler_pal(caminho: str | Path) -> list[tuple[int, int, int]]:
    """Lê `.pal` JASC (o formato de texto que o RHH usa)."""
    linhas = Path(caminho).read_text(encoding="utf-8", errors="replace").splitlines()
    if not linhas or linhas[0].strip() != "JASC-PAL":
        raise ValueError(f"{caminho}: nao parece JASC-PAL")
    corpo = [ln.strip() for ln in linhas[3:] if ln.strip()]
    cores = []
    for ln in corpo:
        partes = ln.split()
        if len(partes) != 3:
            raise ValueError(f"{caminho}: linha de cor invalida: {ln!r}")
        cores.append(tuple(int(p) for p in partes))
    return cores


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
def _escrever_rgb(caminho: Path, largura: int, altura: int,
                  pixels: list[tuple[int, int, int]]) -> None:
    """Grava PNG RGB 8 bits sem filtro (para o self-test)."""
    linhas = bytearray()
    for y in range(altura):
        linhas.append(0)
        for x in range(largura):
            linhas += bytes(pixels[y * largura + x])
    ihdr = struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)
    Path(caminho).write_bytes(ASSINATURA + _chunk(b"IHDR", ihdr)
                              + _chunk(b"IDAT", zlib.compress(bytes(linhas), 9))
                              + _chunk(b"IEND", b""))


def self_test() -> int:
    import tempfile

    casos = ok = 0

    def checa(nome: str, cond: bool):
        nonlocal casos, ok
        casos += 1
        if cond:
            ok += 1
            print(f"  ok: {nome}")
        else:
            print(f"  FALHA: {nome}")

    paleta = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
    linhas = [[i % 4 for i in range(8)] for _ in range(4)]

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "a.png"
        original = Png(8, 4, linhas, paleta, b"\x00", 8)
        escrever(original, p)
        lido = ler(p)
        checa("ida e volta preserva pixels e paleta", lido == original)

        # 4 bits
        p4 = Path(d) / "b.png"
        q = Png(4, 2, [[0, 1, 2, 3], [3, 2, 1, 0]], paleta, None, 4)
        escrever(q, p4)
        checa("ida e volta em 4 bits", ler(p4) == q)

        # recorte: 64x128 -> 64x64 (primeiro quadro)
        grande = Png(2, 4, [[0, 1], [1, 2], [2, 3], [3, 0]], paleta, None, 8)
        corte = recortar_altura(grande, 2)
        checa("recorte pega as primeiras linhas",
              corte.altura == 2 and corte.linhas == [[0, 1], [1, 2]])
        checa("recorte nao altera a paleta", corte.paleta == paleta)

        # mapa de cores: paleta igual -> identidade
        checa("paleta igual mapeia na identidade",
              mapa_de_cores(paleta, paleta) == [0, 1, 2, 3])

        # cor laranja cai no vermelho, nao no azul
        origem = [(0, 0, 0), (250, 40, 10)]
        destino = [(0, 0, 0), (255, 0, 0), (0, 0, 255)]
        checa("cor proxima vai para o vizinho certo",
              mapa_de_cores(origem, destino) == [0, 1])

        # transparência do índice 0 fica em 0 mesmo com cor "distante"
        origem_t = [(9, 9, 9), (0, 0, 255)]
        checa("indice 0 nunca muda", mapa_de_cores(origem_t, destino)[0] == 0)

        # remapear de verdade
        r = remapear(Png(2, 1, [[1, 2]], [(0, 0, 0), (250, 40, 10), (0, 0, 250)],
                         None, 8), destino)
        checa("remapear troca indice e paleta",
              r.linhas == [[1, 2]] and r.paleta == destino)

        # leitura de JASC-PAL
        pal = Path(d) / "x.pal"
        pal.write_text("JASC-PAL\r\n0100\r\n2\r\n0 0 0\r\n255 0 0\r\n", encoding="utf-8")
        checa("le .pal JASC", ler_pal(pal) == [(0, 0, 0), (255, 0, 0)])

        # truecolor (o formato das capturas do emulador)
        rgb = Path(d) / "rgb.png"
        _escrever_rgb(rgb, 2, 2, [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)])
        w, h, px = ler_rgb(rgb)
        checa("le PNG truecolor",
              (w, h) == (2, 2) and px[0] == (1, 2, 3) and px[3] == (10, 11, 12))

        # erros honestos em vez de arquivo torto
        ruim = Path(d) / "ruim.png"
        ruim.write_bytes(b"nao e png")
        try:
            ler(ruim)
            checa("arquivo invalido levanta erro", False)
        except ValueError:
            checa("arquivo invalido levanta erro", True)

    print(f"\n{ok}/{casos} casos ok")
    return 0 if ok == casos else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--info", help="mostra largura/altura/paleta de um PNG")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.info:
        png = ler(a.info)
        print(f"{a.info}: {png.largura}x{png.altura}, {png.profundidade} bits, "
              f"{len(png.paleta)} cores")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
