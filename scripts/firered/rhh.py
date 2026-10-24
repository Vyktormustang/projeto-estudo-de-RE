#!/usr/bin/env python3
"""Leitores do pokeemerald-expansion (RHH) compartilhados pelos geradores.

Por que existe
--------------
O RHH é a fonte de dados (nomes, tipos, efeitos, habilidades, descrições), mas o
formato dele é C "de verdade": o `enum` usa incremento implícito e sentinelas
(`ABILITY_TANGLED_FEET = ABILITIES_COUNT_GEN3`), e cada registro é um bloco com
chaves aninhadas dentro de um `switch`/array.

Duas armadilhas que já custaram tempo neste projeto:

1. **Regex não dá conta das chaves.** Procurar o fecho do bloco com
   `\\n    \\}` corta no primeiro `}` interno e devolve o registro errado.
   Aqui só existe `bloco_balanceado()`, que conta chaves.
2. **`enum` não é lista de `#define`.** Um leitor que ignora o incremento
   implícito devolve IDs errados — e ID errado no RHH vira golpe/habilidade
   trocado na ROM.

Todas as funções são puras (texto → estrutura): o `--self-test` dos geradores
roda sem ROM, sem rede e sem o checkout do RHH.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

__all__ = [
    "sem_comentarios",
    "blocos_balanceados",
    "enum_para_dict",
    "sem_sentinelas",
    "chars_do_charmap",
    "limpar_texto",
    "quebrar_linhas",
]


# --------------------------------------------------------------------------
# C: comentários e blocos
# --------------------------------------------------------------------------
def sem_comentarios(texto: str) -> str:
    """Remove `// ...` e `/* ... */` (o RHH não usa `//` dentro de string)."""
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    return re.sub(r"//[^\n]*", "", texto)


def blocos_balanceados(texto: str) -> dict[str, str]:
    """Mapeia `[CHAVE] = { corpo }` → corpo, contando chaves de verdade.

    Serve para `moves_info.h` (`[MOVE_X] = { ... }`) e para
    `src/data/abilities.h` (`[ABILITY_X] = { ... }`). O corpo devolvido não
    inclui as chaves externas. Registros repetidos: fica o primeiro.
    """
    texto = sem_comentarios(texto)
    saida: dict[str, str] = {}
    for m in re.finditer(r"\[([A-Z][A-Z0-9_]*)\]\s*=\s*\{", texto):
        chave = m.group(1)
        i = m.end() - 1          # posição da '{'
        nivel = 0
        for j in range(i, len(texto)):
            if texto[j] == "{":
                nivel += 1
            elif texto[j] == "}":
                nivel -= 1
                if nivel == 0:
                    saida.setdefault(chave, texto[i + 1 : j])
                    break
        else:
            raise ValueError(f"bloco de {chave} não fecha")
    return saida


# --------------------------------------------------------------------------
# enum com incremento implícito
# --------------------------------------------------------------------------
def enum_para_dict(texto: str, nome_enum: str) -> dict[str, int]:
    """Avalia um `enum` do C, incluindo incremento implícito e sentinelas.

    `nome_enum` é o começo da declaração (ex.: `"enum __attribute__((packed)) Ability"`).
    O valor de cada item é: o número à direita do `=`, o valor de outro item já
    visto, ou `último + 1`. Sentinelas (`ABILITIES_COUNT_GEN3`) entram no dicionário
    e por isso ocupam ID — é assim que o C funciona (o sentinela da Gen 3 e a
    primeira habilidade da Gen 4 compartilham o mesmo número).
    """
    i = texto.index(nome_enum)
    corpo = texto[i:]
    corpo = corpo[corpo.index("{") + 1 :]
    nivel = 1
    fim = len(corpo)
    for j, ch in enumerate(corpo):
        if ch == "{":
            nivel += 1
        elif ch == "}":
            nivel -= 1
            if nivel == 0:
                fim = j
                break
    corpo = sem_comentarios(corpo[:fim])

    ids: dict[str, int] = {}
    atual = 0
    for item in corpo.split(","):
        item = item.strip()
        if not item or "(" in item.split("=")[0]:   # resto de atributo/expressão
            continue
        nome, _, rhs = item.partition("=")
        nome = nome.strip()
        rhs = rhs.strip()
        if not re.fullmatch(r"[A-Za-z_]\w*", nome):
            continue
        if rhs.isdigit():
            valor = int(rhs)
        elif rhs in ids:
            valor = ids[rhs]
        elif re.fullmatch(r"[A-Za-z_]\w*", rhs):
            # constante que não está no enum (ex.: macro): cai no implícito
            valor = atual
        else:
            valor = atual
        ids[nome] = valor
        atual = valor + 1
    return ids


def sem_sentinelas(ids: dict[str, int], prefixo: str) -> dict[str, int]:
    """Só os nomes que começam com `prefixo` (tira `*_COUNT`, `LAST_*` etc.)."""
    return {n: v for n, v in ids.items() if n.startswith(prefixo)}


# --------------------------------------------------------------------------
# texto: charmap do FireRed
# --------------------------------------------------------------------------
# caracteres "bonitos" que não existem no charmap, com substituto ASCII
_SUBSTITUTOS = {
    "\u2019": "'",   # ’
    "\u2018": "'",   # ‘
    "\u2013": "-",   # –
    "\u2014": "-",   # —
    "\u2026": "...",  # …
    "\u00d7": "x",   # ×
    "\u2032": "'",
    "\u02bc": "'",
    "\u00a0": " ",
}


def chars_do_charmap(pf: Path) -> set[str]:
    """Conjunto de caracteres que a ROM sabe desenhar (`charmap.txt`)."""
    texto = (Path(pf) / "charmap.txt").read_text(encoding="utf-8", errors="replace")
    chars: set[str] = set()
    for linha in texto.splitlines():
        m = re.match(r"^'((?:\\.|[^'\\])+)'\s*=", linha)
        if not m:
            continue
        bruto = m.group(1)
        if bruto == "\\'":
            chars.add("'")
        elif bruto.startswith("\\"):
            continue
        elif len(bruto) == 1:
            chars.add(bruto)
    return chars


def limpar_texto(texto: str, permitidos: set[str], *, maiusculas: bool = False) -> tuple[str, list[str]]:
    """Deixa o texto desenhável pelo FireRed. Devolve (texto, caracteres perdidos).

    - troca aspas/travessões tipográficos pelo equivalente ASCII;
    - tenta a letra base (NFKD) quando o acento não existe no charmap;
    - o que sobrar vira `?` e entra na lista de perdidos (o relatório mostra).
    """
    for de, para in _SUBSTITUTOS.items():
        texto = texto.replace(de, para)
    saida: list[str] = []
    perdidos: list[str] = []
    for ch in texto:
        # a ROM não tem aspas retas: usa a curva (B1), que existe no charmap
        if ch == '"' and '"' not in permitidos:
            ch = "\u201c" if "\u201c" in permitidos else ch
        alvo = ch.upper() if maiusculas else ch
        if alvo in permitidos:
            saida.append(alvo)
            continue
        # "é" existe no charmap, "É" não: maiúscula só se a ROM souber desenhar
        if maiusculas and ch in permitidos:
            saida.append(ch)
            continue
        base = unicodedata.normalize("NFKD", ch)
        base = "".join(c for c in base if not unicodedata.combining(c))
        base = base.upper() if maiusculas else base
        if len(base) == 1 and base in permitidos:
            saida.append(base)
        elif ch == " ":
            saida.append(" ")
        else:
            saida.append("?")
            perdidos.append(ch)
    return "".join(saida), perdidos


def quebrar_linhas(texto: str, largura: int, maximo: int) -> tuple[list[str], bool]:
    """Quebra em até `maximo` linhas de `largura`, cortando palavra inteira.

    Devolve (linhas, truncou). Usado nas descrições de golpe (4 × 21 colunas).
    """
    palavras = texto.split()
    linhas: list[str] = []
    atual = ""
    for p in palavras:
        if not atual:
            atual = p
        elif len(atual) + 1 + len(p) <= largura:
            atual += " " + p
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    if len(linhas) > maximo:
        return linhas[:maximo], True
    return linhas, False
