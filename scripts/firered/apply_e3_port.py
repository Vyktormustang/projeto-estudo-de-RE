#!/usr/bin/env python3
"""Aplica o port da E3 (tipo Fada + split fisico/especial) num clone do FireRed.

O que ele muda
--------------
1. `TYPE_FAIRY = 18` e `NUMBER_OF_MON_TYPES` 18 -> 19.
2. `gTypeEffectiveness`: 12 linhas novas (Fada atacando e Fada defendendo).
3. `gTypeNames`, `gText_AFairyMove`/`sATypeMove_Table`: nome do tipo na UI.
4. `sMenuInfoIcons` + placa grafica "FAIRY" (o graphic da dex ganha 16 linhas).
5. Paleta `pokemon_types`: indice 10 (livre) vira rosa de Fada.
6. Split fisico/especial **por golpe**: `gMoveCategories[]` gerada do
   pokeemerald-expansion e as checagens de dano passam a usa-la.

Por que um script
-----------------
Cada passo e' replicavel e idempotente; o clone `/tmp/pokefirered` nao
sobrevive entre sessoes. Rodar de novo nao duplica nada (marcadores `E3`).

Uso
---
    python3 scripts/firered/apply_e3_port.py --pokefirered /tmp/pokefirered
    python3 scripts/firered/apply_e3_port.py --pokefirered /tmp/pokefirered --check
    python3 scripts/firered/apply_e3_port.py --self-test      # sem clone
"""
from __future__ import annotations

import argparse
import re
import struct
import sys
import zlib
from pathlib import Path

# ---------------------------------------------------------------------------
# constantes do port
# ---------------------------------------------------------------------------
MARCA = "// E3"

TIPO_FAIRY = 18
COR_FAIRY = (238, 156, 172)          # rosa oficial ~ #EE99AC, arredondado a 5 bits
INDICE_COR_FAIRY = 10                # entrada livre na paleta pokemon_types
OFFSET_ICONE_FAIRY = 0x100           # tile 256 = y 128 do bitmap de 128 de largura

# Fada -> outros e outros -> Fada (Gen 6+). Multiplicadores do FireRed:
# 20 = 2x, 10 = 1x, 5 = 0,5x, 0 = 0x.
EFETIVIDADE = [
    ("TYPE_FAIRY", "TYPE_FIGHTING", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_DRAGON", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_DARK", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_POISON", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_FIRE", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_FIGHTING", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_BUG", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_DARK", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_DRAGON", "TYPE_FAIRY", "TYPE_MUL_NO_EFFECT"),
    ("TYPE_POISON", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_STEEL", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
]

# nomes de golpe que mudaram depois da Gen 3
ALIAS_GOLPE = {
    "MOVE_VICE_GRIP": "MOVE_VISE_GRIP",
    "MOVE_HI_JUMP_KICK": "MOVE_HIGH_JUMP_KICK",
    "MOVE_FAINT_ATTACK": "MOVE_FEINT_ATTACK",
    "MOVE_SMELLING_SALT": "MOVE_SMELLING_SALTS",
}


# ---------------------------------------------------------------------------
# PNG indexado (8 bits, color type 3) - suficiente para o menu_info.png
# ---------------------------------------------------------------------------
def ler_png(caminho: Path) -> tuple[int, int, list[int], bytes]:
    """-> (largura, altura, indices por pixel, PLTE)."""
    d = caminho.read_bytes()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{caminho}: nao e' PNG")
    pos, idat, plte = 8, b"", b""
    w = h = bits = tipo = 0
    while pos < len(d):
        tam = struct.unpack(">I", d[pos:pos + 4])[0]
        tag = d[pos + 4:pos + 8]
        dados = d[pos + 8:pos + 8 + tam]
        if tag == b"IHDR":
            w, h, bits, tipo = struct.unpack(">IIBB", dados[:10])
        elif tag == b"PLTE":
            plte = dados
        elif tag == b"IDAT":
            idat += dados
        pos += 12 + tam
    if bits != 8 or tipo != 3:
        raise SystemExit(f"{caminho}: esperava PNG indexado de 8 bits (bits={bits}, tipo={tipo})")
    cru = zlib.decompress(idat)
    linhas, anterior, p = [], bytearray(w), 0
    for _ in range(h):
        filtro = cru[p]
        p += 1
        linha = bytearray(cru[p:p + w])
        p += w
        if filtro == 1:
            for i in range(1, w):
                linha[i] = (linha[i] + linha[i - 1]) & 0xFF
        elif filtro == 2:
            for i in range(w):
                linha[i] = (linha[i] + anterior[i]) & 0xFF
        elif filtro == 3:
            for i in range(w):
                a = linha[i - 1] if i else 0
                linha[i] = (linha[i] + ((a + anterior[i]) >> 1)) & 0xFF
        elif filtro == 4:
            for i in range(w):
                a = linha[i - 1] if i else 0
                b = anterior[i]
                c = anterior[i - 1] if i else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                linha[i] = (linha[i] + pr) & 0xFF
        linhas.append(linha)
        anterior = linha
    return w, h, [v for linha in linhas for v in linha], plte


def gravar_png(caminho: Path, w: int, h: int, pixels: list[int], plte: bytes) -> None:
    def chunk(tag: bytes, dados: bytes) -> bytes:
        c = tag + dados
        return struct.pack(">I", len(dados)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    cru = b"".join(b"\x00" + bytes(pixels[y * w:(y + 1) * w]) for y in range(h))
    caminho.write_bytes(b"\x89PNG\r\n\x1a\n"
                        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
                        + chunk(b"PLTE", plte)
                        + chunk(b"IDAT", zlib.compress(cru, 9))
                        + chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# placa "FAIRY" no bitmap de icones (128 px de largura, 4bpp depois)
# ---------------------------------------------------------------------------
# cada celula e' 4x8: 3 colunas de glifo + 1 de sombra, 7 linhas + 1 de sombra
GLIFOS = {
    "F": ["###", "#..", "##.", "#..", "#.."],
    "A": [".##", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "R": ["###", "#.#", "##.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
}
# letras reais extraidas das placas do jogo (mesma fonte) - usadas quando existem
GLIFOS_DO_JOGO = {
    "F": ["###", "#..", "##.", "#..", "#.."],   # FIGHT
    "A": [".##", "#.#", "###", "#.#", "#.#"],   # DARK
    "I": ["###", ".#.", ".#.", ".#.", "###"],   # ICE
    "R": ["###", "#.#", "##.", "#.#", "#.#"],   # ROCK
}


def desenhar_placa(pixels: list[int], w: int, x0: int, y0: int, texto: str,
                   cor_fundo: int, texto_fill: int = 15, sombra: int = 14,
                   cor_transparente: int = 0) -> None:
    """Desenha uma placa 32x12 em `pixels` (indices de paleta)."""
    def por(x: int, y: int, v: int) -> None:
        if 0 <= x0 + x < w:
            pixels[(y0 + y) * w + x0 + x] = v

    for y in range(12):
        for x in range(32):
            por(x, y, cor_fundo)
    por(0, 0, cor_transparente)
    por(31, 0, cor_transparente)
    por(0, 11, cor_transparente)
    por(31, 11, cor_transparente)

    passo = 5
    inicio = 16 - (len(texto) * passo) // 2 - 1
    for i, letra in enumerate(texto):
        glifo = GLIFOS_DO_JOGO.get(letra) or GLIFOS[letra]
        gx = inicio + i * passo
        gy = 2
        for gy_i, linha in enumerate(glifo):
            for gx_i, c in enumerate(linha):
                if c == "#":
                    por(gx + gx_i, gy + gy_i, texto_fill)
        # sombra em (+1,+1) onde nao ha preenchimento
        for gy_i, linha in enumerate(glifo):
            for gx_i, c in enumerate(linha):
                if c == "#" and not (gy_i + 1 < len(glifo)
                                     and gx_i + 1 < len(glifo[gy_i + 1])
                                     and glifo[gy_i + 1][gx_i + 1] == "#"):
                    por(gx + gx_i + 1, gy + gy_i + 1, sombra)


def adicionar_placa_fairy(poke: Path) -> bool:
    """Acrescenta 16 linhas ao menu_info.png e desenha a placa FAIRY em y=128."""
    png = poke / "graphics/interface/menu_info.png"
    w, h, pixels, plte = ler_png(png)
    if h >= 144 and all(pixels[128 * w + x] == 16 + INDICE_COR_FAIRY
                        for x in range(1, 8)):
        return False                          # ja feito
    if w != 128:
        raise SystemExit(f"menu_info.png tem {w} px de largura; esperava 128")
    novo = pixels + [0] * (w * 16)
    # a paleta do PNG tem 32 cores: 16..31 = paleta de tipos (o gbagfx desconta 16)
    idx_fundo = 16 + INDICE_COR_FAIRY
    desenhar_placa(novo, w, 0, 128, "FAIRY", idx_fundo)
    gravar_png(png, w, 144, novo, plte)
    return True


def ajustar_paleta_fairy(poke: Path) -> bool:
    """Coloca o rosa de Fada no indice livre da paleta de tipos (.pal e .gbapal)."""
    mudou = False
    pal = poke / "graphics/interface/pokemon_types.pal"
    if pal.exists():
        linhas = pal.read_text().splitlines()
        # JASC-PAL: 3 primeiras linhas sao cabecalho
        alvo = 3 + INDICE_COR_FAIRY
        if alvo < len(linhas):
            nova = f"{COR_FAIRY[0]} {COR_FAIRY[1]} {COR_FAIRY[2]}"
            if linhas[alvo].strip() != nova:
                linhas[alvo] = nova
                pal.write_text("\n".join(linhas) + "\n")
                mudou = True
    gbapal = poke / "graphics/interface/pokemon_types.gbapal"
    if gbapal.exists():
        d = bytearray(gbapal.read_bytes())
        r = round(COR_FAIRY[0] * 31 / 255)
        g = round(COR_FAIRY[1] * 31 / 255)
        b = round(COR_FAIRY[2] * 31 / 255)
        valor = r | (g << 5) | (b << 10)
        off = INDICE_COR_FAIRY * 2
        if struct.unpack_from("<H", d, off)[0] != valor:
            struct.pack_into("<H", d, off, valor)
            gbapal.write_bytes(bytes(d))
            mudou = True
    return mudou


# ---------------------------------------------------------------------------
# edicoes no codigo C
# ---------------------------------------------------------------------------
def trocar(texto: str, velho: str, novo: str, arquivo: str) -> str:
    if velho not in texto:
        if novo in texto:
            return texto
        raise SystemExit(f"{arquivo}: nao achei o trecho esperado:\n{velho[:200]}")
    return texto.replace(velho, novo, 1)


def aplicar_tipo_fairy(poke: Path) -> list[str]:
    mudancas = []

    # 1) constantes
    p = poke / "include/constants/pokemon.h"
    s = p.read_text()
    novo = s
    if "TYPE_FAIRY" not in s:
        novo = trocar(novo, "#define TYPE_DARK           17\n",
                      "#define TYPE_DARK           17\n"
                      f"#define TYPE_FAIRY          {TIPO_FAIRY}  {MARCA}: tipo Fada\n",
                      "constants/pokemon.h")
    novo = re.sub(r"#define NUMBER_OF_MON_TYPES 18\b",
                  "#define NUMBER_OF_MON_TYPES 19  // E3: + Fada", novo)
    if re.search(r"#define NUMBER_OF_MON_TYPES (?:18|19)\b", novo):
        pass
    if novo != s:
        p.write_text(novo)
        mudancas.append("constants/pokemon.h: TYPE_FAIRY=18, NUMBER_OF_MON_TYPES=19")

    # 2) tamanho da tabela de efetividade no header (sizeof depende dele)
    total = (112 + len(EFETIVIDADE)) * 3
    p = poke / "include/battle_main.h"
    s = p.read_text()
    if "TYPE_EFFECT_TABLE_SIZE" not in s:
        novo = re.sub(r"extern const u8 gTypeEffectiveness\[\d*\];",
                      f"#define TYPE_EFFECT_TABLE_SIZE {total}  {MARCA}: 112 + {len(EFETIVIDADE)}\n"
                      "extern const u8 gTypeEffectiveness[TYPE_EFFECT_TABLE_SIZE];", s)
        if novo == s:
            raise SystemExit("battle_main.h: nao achei o extern de gTypeEffectiveness")
        p.write_text(novo)
        mudancas.append(f"battle_main.h: tabela de efetividade com {total} bytes")

    # 3) tabela + nomes
    p = poke / "src/battle_main.c"
    s = p.read_text()
    if "TYPE_EFFECT_TABLE_SIZE" not in s:
        novo = re.sub(r"const u8 gTypeEffectiveness\[\d*\] =",
                      "const u8 gTypeEffectiveness[TYPE_EFFECT_TABLE_SIZE] =", s)
        if novo == s:
            raise SystemExit("battle_main.c: nao achei a definicao de gTypeEffectiveness")
        p.write_text(novo)
        s = novo
        mudancas.append("battle_main.c: definicao usa TYPE_EFFECT_TABLE_SIZE")
    if "TYPE_FAIRY" not in s:
        linhas = "".join(f"    {a}, {b}, {c},\n" for a, b, c in EFETIVIDADE)
        novo = trocar(s, "    TYPE_ENDTABLE, TYPE_ENDTABLE, TYPE_MUL_NO_EFFECT\n",
                      f"    {MARCA}: Fada atacando e Fada defendendo\n"
                      + linhas
                      + "    TYPE_ENDTABLE, TYPE_ENDTABLE, TYPE_MUL_NO_EFFECT\n",
                      "battle_main.c")
        novo = trocar(novo, '    [TYPE_DARK] = _("DARK"),\n',
                      '    [TYPE_DARK] = _("DARK"),\n'
                      f'    [TYPE_FAIRY] = _("FAIRY"),  {MARCA}\n',
                      "battle_main.c")
        p.write_text(novo)
        mudancas.append(f"battle_main.c: +{len(EFETIVIDADE)} linhas de efetividade e nome FAIRY")

    # 3b) sorteio da Conversion 2: usa o tamanho real da tabela
    p = poke / "src/battle_script_commands.c"
    s = p.read_text()
    if "E3: sorteio" not in s:
        novo = trocar(s, "            while (((i = Random() % 128) > sizeof(gTypeEffectiveness) / 3));",
                      f"            // {MARCA}: sorteio dentro do tamanho real da tabela\n"
                      "            i = Random() % (sizeof(gTypeEffectiveness) / 3);",
                      "battle_script_commands.c")
        p.write_text(novo)
        mudancas.append("battle_script_commands.c: sorteio da Conversion 2 dentro da tabela")

    # 4) mensagem "a FAIRY move!"
    p = poke / "src/battle_message.c"
    s = p.read_text()
    if "gText_AFairyMove" not in s:
        novo = trocar(s, 'const u8 gText_ADarkMove[] = _("a DARK move");\n',
                      'const u8 gText_ADarkMove[] = _("a DARK move");\n'
                      f'const u8 gText_AFairyMove[] = _("a FAIRY move");  {MARCA}\n',
                      "battle_message.c")
        novo = trocar(novo, "    [TYPE_DARK]     = gText_ADarkMove\n",
                      "    [TYPE_DARK]     = gText_ADarkMove,\n"
                      f"    [TYPE_FAIRY]    = gText_AFairyMove  {MARCA}\n",
                      "battle_message.c")
        p.write_text(novo)
        mudancas.append("battle_message.c: gText_AFairyMove + tabela de mensagens")

    # 5) icone na Pokédex/lista
    p = poke / "src/list_menu.c"
    s = p.read_text()
    if "[TYPE_FAIRY + 1]" not in s:
        novo = trocar(s, "    [TYPE_DARK + 1]     = { 32, 12, 0x8C },\n",
                      "    [TYPE_DARK + 1]     = { 32, 12, 0x8C },\n"
                      f"    [TYPE_FAIRY + 1]    = {{ 32, 12, 0x{OFFSET_ICONE_FAIRY:03X} }},  {MARCA}\n",
                      "list_menu.c")
        p.write_text(novo)
        mudancas.append("list_menu.c: icone FAIRY (32x12 em 0x100)")

    # 6) paleta dos discos de TM
    p = poke / "src/tm_case.c"
    s = p.read_text()
    if "[TYPE_FAIRY]" not in s:
        novo = trocar(s, "    [TYPE_DRAGON]   = 0x100\n};\n",
                      "    [TYPE_DRAGON]   = 0x100,\n"
                      f"    [TYPE_FAIRY]    = 0x100  {MARCA}: nao existe TM de Fada no Kanto\n}};\n",
                      "tm_case.c")
        p.write_text(novo)
        mudancas.append("tm_case.c: entrada de paleta para TYPE_FAIRY")

    # 7) grafico + paleta
    if ajustar_paleta_fairy(poke):
        mudancas.append("pokemon_types.pal/.gbapal: indice 10 = rosa de Fada")
    if adicionar_placa_fairy(poke):
        mudancas.append("menu_info.png: 128x144 + placa FAIRY")

    return mudancas


# ---------------------------------------------------------------------------
# split fisico/especial por golpe
# ---------------------------------------------------------------------------
def categorias_do_rhh(ref: Path) -> dict[str, str]:
    """-> {MOVE_X: DAMAGE_CATEGORY_*} lido do moves_info.h do expansion."""
    arq = ref / "src" / "data" / "moves_info.h"
    if not arq.exists():
        raise SystemExit(f"nao achei {arq} (sparse-checkout da referencia RHH?)")
    texto = arq.read_text(errors="replace")
    saida: dict[str, str] = {}
    for nome, corpo in re.findall(r"\[(MOVE_[A-Z0-9_]+)\]\s*=\s*\n\s*\{(.*?)\n    \}",
                                  texto, re.S):
        m = re.search(r"\.category = (DAMAGE_CATEGORY_\w+)", corpo)
        if m:
            saida[nome] = m.group(1)
    # alguns golpes tem nome antigo no FireRed
    for velho, novo in ALIAS_GOLPE.items():
        if novo in saida and velho not in saida:
            saida[velho] = saida[novo]
    return saida


def golpes_do_firered(poke: Path) -> list[tuple[str, int, str]]:
    """-> [(MOVE_X, id, TYPE_Y)] na ordem de include/constants/moves.h."""
    texto = (poke / "include/constants/moves.h").read_text()
    nomes = re.findall(r"^#define (MOVE_[A-Z0-9_]+) (\d+)$", texto, re.M)
    tipos: dict[str, str] = {}
    for bloco in re.findall(r"\[(MOVE_[A-Z0-9_]+)\] =\s*\n\s*\{(.*?)\n    \},",
                            (poke / "src/data/battle_moves.h").read_text(), re.S):
        m = re.search(r"\.type = (TYPE_\w+)", bloco[1])
        if m:
            tipos[bloco[0]] = m.group(1)
    return [(nome, int(num), tipos.get(nome, "TYPE_NORMAL")) for nome, num in nomes]


def gerar_categorias(poke: Path, ref: Path) -> str:
    """Emite `src/data/battle_moves_category.h`."""
    cats = categorias_do_rhh(ref)
    linhas = [
        f"{MARCA}: categoria de cada golpe (fisico/especial/status).",
        "// Gerado por scripts/firered/apply_e3_port.py -- nao editar a mao.",
        "// Fonte: src/data/moves_info.h do rh-hideout/pokeemerald-expansion.",
        "const u8 gMoveCategories[MOVES_COUNT] =",
        "{",
    ]
    faltando = []
    for nome, _num, tipo in golpes_do_firered(poke):
        cat = cats.get(nome)
        if nome == "MOVE_NONE":
            cat = "DAMAGE_CATEGORY_STATUS"
        elif cat is None:
            faltando.append(nome)
            # sem dado moderno: regra da Gen 3 (tipo < MYSTERY = fisico)
            cat = ("DAMAGE_CATEGORY_PHYSICAL" if tipo not in ("TYPE_MYSTERY",)
                   and _e_fisico(tipo) else "DAMAGE_CATEGORY_SPECIAL")
        valor = {"DAMAGE_CATEGORY_PHYSICAL": "MOVE_CATEGORY_PHYSICAL",
                 "DAMAGE_CATEGORY_SPECIAL": "MOVE_CATEGORY_SPECIAL",
                 "DAMAGE_CATEGORY_STATUS": "MOVE_CATEGORY_STATUS"}[cat]
        linhas.append(f"    [{nome}] = {valor},")
    linhas.append("};")
    if faltando:
        linhas.insert(4, f"// sem categoria no RHH ({len(faltando)}): {', '.join(faltando)}")
    return "\n".join(linhas) + "\n"


def _e_fisico(tipo: str) -> bool:
    especiais = {"TYPE_FIRE", "TYPE_WATER", "TYPE_GRASS", "TYPE_ELECTRIC",
                 "TYPE_PSYCHIC", "TYPE_ICE", "TYPE_DRAGON", "TYPE_DARK", "TYPE_FAIRY"}
    return tipo not in especiais


def aplicar_split(poke: Path, ref: Path) -> list[str]:
    mudancas = []

    # 1) macros + extern
    p = poke / "include/battle.h"
    s = p.read_text()
    if "MOVE_CATEGORY_PHYSICAL" not in s:
        novo = trocar(s, "#define IS_TYPE_PHYSICAL(moveType)(moveType < TYPE_MYSTERY)\n",
                      "#define IS_TYPE_PHYSICAL(moveType)(moveType < TYPE_MYSTERY)\n",
                      "battle.h")
        novo = trocar(novo, "#define IS_TYPE_SPECIAL(moveType)(moveType > TYPE_MYSTERY)\n",
                      "#define IS_TYPE_SPECIAL(moveType)(moveType > TYPE_MYSTERY)\n"
                      f"\n{MARCA}: fisico/especial vem da categoria do golpe (Gen 4+), nao do tipo.\n"
                      "#define MOVE_CATEGORY_PHYSICAL 0\n"
                      "#define MOVE_CATEGORY_SPECIAL  1\n"
                      "#define MOVE_CATEGORY_STATUS   2\n"
                      "#define IS_MOVE_PHYSICAL(move)(gMoveCategories[move] == MOVE_CATEGORY_PHYSICAL)\n"
                      "#define IS_MOVE_SPECIAL(move)(gMoveCategories[move] == MOVE_CATEGORY_SPECIAL)\n"
                      "extern const u8 gMoveCategories[MOVES_COUNT];\n",
                      "battle.h")
        p.write_text(novo)
        mudancas.append("battle.h: macros IS_MOVE_PHYSICAL/IS_MOVE_SPECIAL")

    # MOVES_COUNT precisa estar visivel em battle.h
    if '#include "constants/moves.h"' not in s:
        s2 = p.read_text()
        s2 = trocar(s2, '#include "constants/battle.h"\n',
                    '#include "constants/battle.h"\n#include "constants/moves.h"  ' + MARCA + "\n",
                    "battle.h")
        p.write_text(s2)
        mudancas.append("battle.h: include de constants/moves.h")

    # 2) tabela gerada
    conteudo = gerar_categorias(poke, ref)
    destino = poke / "src/data/battle_moves_category.h"
    if not destino.exists() or destino.read_text() != conteudo:
        destino.write_text(conteudo)
        mudancas.append("data/battle_moves_category.h gerado")

    # 3) incluir a tabela onde gBattleMoves e' definido
    p = poke / "src/pokemon.c"
    s = p.read_text()
    if "battle_moves_category.h" not in s:
        s = trocar(s, '#include "data/battle_moves.h"\n',
                   '#include "data/battle_moves.h"\n'
                   f'#include "data/battle_moves_category.h"  {MARCA}\n', "pokemon.c")
        mudancas.append("pokemon.c: include da tabela de categorias")

    # 4) calculo de dano usa a categoria
    trocas = [
        ("    // Apply type-bonus hold item\n", None),   # marcador de contexto
    ]
    antes = s
    s = s.replace("""            if (IS_TYPE_PHYSICAL(type))
                attack = (attack * (attackerHoldEffectParam + 100)) / 100;
            else
                spAttack = (spAttack * (attackerHoldEffectParam + 100)) / 100;""",
                  """            if (IS_MOVE_PHYSICAL(move))
                attack = (attack * (attackerHoldEffectParam + 100)) / 100;
            else
                spAttack = (spAttack * (attackerHoldEffectParam + 100)) / 100;""", 1)
    s = s.replace("    if (IS_TYPE_PHYSICAL(type))\n    {\n        if (gCritMultiplier == 2)",
                  "    if (IS_MOVE_PHYSICAL(move))  " + MARCA + "\n    {\n        if (gCritMultiplier == 2)", 1)
    s = s.replace("    if (IS_TYPE_SPECIAL(type))\n    {\n        if (gCritMultiplier == 2)",
                  "    if (IS_MOVE_SPECIAL(move))  " + MARCA + "\n    {\n        if (gCritMultiplier == 2)", 1)
    if s != antes:
        p.write_text(s)
        mudancas.append("pokemon.c: dano fisico/especial pela categoria do golpe")

    # 5) batalha: Hustle e rastreio de dano fisico/especial
    p = poke / "src/battle_script_commands.c"
    s = p.read_text()
    antes = s
    s = s.replace("if (gBattleMons[gBattlerAttacker].ability == ABILITY_HUSTLE && IS_TYPE_PHYSICAL(type))",
                  "if (gBattleMons[gBattlerAttacker].ability == ABILITY_HUSTLE && IS_MOVE_PHYSICAL(gCurrentMove))  " + MARCA, 1)
    s = s.replace("if (IS_TYPE_PHYSICAL(moveType) && !(gHitMarker & HITMARKER_PASSIVE_DAMAGE) && gCurrentMove != MOVE_PAIN_SPLIT)",
                  "if (IS_MOVE_PHYSICAL(gCurrentMove) && !(gHitMarker & HITMARKER_PASSIVE_DAMAGE) && gCurrentMove != MOVE_PAIN_SPLIT)  " + MARCA, 1)
    s = s.replace("else if (!IS_TYPE_PHYSICAL(moveType) && !(gHitMarker & HITMARKER_PASSIVE_DAMAGE))",
                  "else if (IS_MOVE_SPECIAL(gCurrentMove) && !(gHitMarker & HITMARKER_PASSIVE_DAMAGE))  " + MARCA, 1)
    if s != antes:
        p.write_text(s)
        mudancas.append("battle_script_commands.c: Hustle e dano fisico/especial pela categoria")

    return mudancas


# ---------------------------------------------------------------------------
# verificacao
# ---------------------------------------------------------------------------
def verificar(poke: Path) -> int:
    problemas = []
    fontes = {
        "include/constants/pokemon.h": ["#define TYPE_FAIRY"],
        "include/battle_main.h": ["TYPE_EFFECT_TABLE_SIZE",
                                  "gTypeEffectiveness[TYPE_EFFECT_TABLE_SIZE]"],
        "src/battle_main.c": ["TYPE_FAIRY, TYPE_DRAGON, TYPE_MUL_SUPER_EFFECTIVE",
                              "TYPE_DRAGON, TYPE_FAIRY, TYPE_MUL_NO_EFFECT",
                              '[TYPE_FAIRY] = _("FAIRY")'],
        "src/battle_message.c": ["gText_AFairyMove", "[TYPE_FAIRY]"],
        "src/list_menu.c": ["[TYPE_FAIRY + 1]"],
        "src/tm_case.c": ["[TYPE_FAIRY]"],
        "include/battle.h": ["IS_MOVE_PHYSICAL", "gMoveCategories"],
        "src/pokemon.c": ["IS_MOVE_PHYSICAL(move)", "IS_MOVE_SPECIAL(move)",
                          "battle_moves_category.h"],
        "src/battle_script_commands.c": ["IS_MOVE_PHYSICAL(gCurrentMove)"],
        "src/data/battle_moves_category.h": ["const u8 gMoveCategories[MOVES_COUNT]"],
    }
    for rel, marcas in fontes.items():
        p = poke / rel
        if not p.exists():
            problemas.append(f"{rel}: nao existe")
            continue
        s = p.read_text()
        for m in marcas:
            if m not in s:
                problemas.append(f"{rel}: falta {m}")

    # tabela de tipos: 12 linhas de Fada e os dois sentinelas intactos
    s = (poke / "src/battle_main.c").read_text()
    bloco = s[s.find("const u8 gTypeEffectiveness"):s.find("const u8 gTypeNames")]
    entradas = len([l for l in bloco.splitlines() if l.strip().startswith("TYPE_")])
    if entradas != 112 + len(EFETIVIDADE):
        problemas.append(f"gTypeEffectiveness com {entradas} entradas; esperava "
                         f"{112 + len(EFETIVIDADE)}")

    # categorias
    cat = (poke / "src/data/battle_moves_category.h").read_text()
    esperado = {"MOVE_POUND": "PHYSICAL", "MOVE_FLAMETHROWER": "SPECIAL",
                "MOVE_GROWL": "STATUS", "MOVE_BODY_SLAM": "PHYSICAL"}
    for golpe, valor in esperado.items():
        if f"[{golpe}] = MOVE_CATEGORY_{valor}" not in cat:
            problemas.append(f"categoria de {golpe} != {valor}")

    # grafico
    w, h, pixels, _ = ler_png(poke / "graphics/interface/menu_info.png")
    if h != 144:
        problemas.append(f"menu_info.png com {h} px de altura; esperava 144")
    elif pixels[128 * w + 5] != 16 + INDICE_COR_FAIRY:
        problemas.append("menu_info.png: placa FAIRY nao esta em y=128")

    if problemas:
        for p in problemas:
            print("FALHA:", p)
        return 1
    print("ok: port da E3 aplicado e consistente")
    return 0


# ---------------------------------------------------------------------------
# self-test (nao precisa de clone)
# ---------------------------------------------------------------------------
def self_test() -> int:
    import tempfile

    falhas = 0

    # 1) PNG ida e volta
    tmp = Path(tempfile.mkdtemp())
    plte = bytes([0, 0, 0] * 31 + [255, 255, 255])
    pixels = [(x * y) % 32 for y in range(24) for x in range(16)]
    gravar_png(tmp / "t.png", 16, 24, pixels, plte)
    w, h, volta, plte2 = ler_png(tmp / "t.png")
    if (w, h, volta, plte2) != (16, 24, pixels, plte):
        print("  FALHA: PNG nao fez ida e volta")
        falhas += 1
    else:
        print("  ok: PNG indexado ida e volta")

    # 2) placa
    pix = [1] * (128 * 144)
    desenhar_placa(pix, 128, 0, 128, "FAIRY", 26)
    if pix[128 * 128] != 0 or pix[128 * 128 + 5] != 26:
        print("  FALHA: canto/plano de fundo da placa")
        falhas += 1
    tinta = sum(1 for y in range(128, 140) for x in range(32) if pix[y * 128 + x] == 15)
    if not 20 <= tinta <= 90:
        print(f"  FALHA: placa com {tinta} pixels de texto (esperava 20..90)")
        falhas += 1
    else:
        print(f"  ok: placa FAIRY com {tinta} pixels de tinta")

    # 3) tabela de efetividade
    regras = {(a, b): c for a, b, c in EFETIVIDADE}
    esperado = {
        ("TYPE_FAIRY", "TYPE_DRAGON"): "TYPE_MUL_SUPER_EFFECTIVE",
        ("TYPE_FAIRY", "TYPE_STEEL"): "TYPE_MUL_NOT_EFFECTIVE",
        ("TYPE_DRAGON", "TYPE_FAIRY"): "TYPE_MUL_NO_EFFECT",
        ("TYPE_POISON", "TYPE_FAIRY"): "TYPE_MUL_SUPER_EFFECTIVE",
        ("TYPE_FIGHTING", "TYPE_FAIRY"): "TYPE_MUL_NOT_EFFECTIVE",
    }
    for chave, valor in esperado.items():
        if regras.get(chave) != valor:
            print(f"  FALHA: efetividade {chave} = {regras.get(chave)}, esperava {valor}")
            falhas += 1
    if any(a == b for a, b in regras):
        print("  FALHA: regra de tipo contra ele mesmo")
        falhas += 1
    else:
        print(f"  ok: {len(regras)} regras de Fada coerentes")

    # 4) nomes de golpe antigos
    if ALIAS_GOLPE["MOVE_VICE_GRIP"] != "MOVE_VISE_GRIP":
        print("  FALHA: alias de golpe")
        falhas += 1
    else:
        print("  ok: aliases de golpe")

    # 5) regra de fallback Gen 3
    if not _e_fisico("TYPE_NORMAL") or _e_fisico("TYPE_FIRE"):
        print("  FALHA: fallback fisico/especial da Gen 3")
        falhas += 1
    else:
        print("  ok: fallback Gen 3 (Normal fisico, Fire especial)")

    return 1 if falhas else 0


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--reference", default="/tmp/fre")
    ap.add_argument("--check", action="store_true", help="so confere")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        print("self-test: port da E3 (tipo Fada + split)")
        return self_test()

    poke = Path(a.pokefirered)
    if not (poke / "include/constants/pokemon.h").exists():
        print(f"{poke} nao parece um clone do pokefirered")
        return 2

    if a.check:
        return verificar(poke)

    mudancas = aplicar_tipo_fairy(poke) + aplicar_split(poke, Path(a.reference))
    if mudancas:
        print(f"{len(mudancas)} mudanca(s):")
        for m in mudancas:
            print("  -", m)
    else:
        print("nada a fazer: port da E3 ja aplicado")
    return verificar(poke)


if __name__ == "__main__":
    sys.exit(main())
