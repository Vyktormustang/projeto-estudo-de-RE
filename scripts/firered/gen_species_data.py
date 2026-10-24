#!/usr/bin/env python3
"""Gera os dados das espécies 387-1025 (Gen 4-9) no formato do FireRed.

Por que existe
--------------
As 639 espécies novas criadas na E1 existem como constante e nome, mas **não têm
dados**: `gSpeciesInfo[]` é dimensionado pelo último inicializador, então consultar
`gSpeciesInfo[QUALQUER_GEN_4_9]` lê memória fora do array. O mesmo vale para
`gPokedexEntries`, `gEvolutionTable` e `gLevelUpLearnsets`.

Este script lê os dados do RHH pokeemerald-expansion (derivados dos jogos oficiais)
e emite os headers que o port inclui no clone do pokefirered:

    src/data/pokemon/species_info_gen4_9.h          stats, tipos, itens, etc.
    src/data/pokemon/pokedex_entries_gen4_9.h       categoria, altura, peso, texto
    src/data/pokemon/evolution_gen4_9.h             evoluções
    src/data/pokemon/level_up_learnsets_gen4_9.h    golpes por nível

Regras de conversão (e o que é perdido de propósito)
----------------------------------------------------
- Tipos: o RHH numera a partir de 1 e tem Fada/Estelar. O FireRed numera a partir
  de 0 e não tem Fada até a E3. `TYPE_FAIRY` e `TYPE_STELLAR` viram `TYPE_NORMAL`
  por enquanto; a E3 troca pelo tipo real.
- Habilidades: o FireRed só tem as 77 da Gen 3. Habilidade desconhecida vira
  `ABILITY_NONE`; a E5 traz as demais.
- `expYield` é u8 no FireRed: valores acima de 255 são limitados a 255 (o RHH usa
  até 300 nas lendárias). O relatório conta quantas foram limitadas.
- Evoluções com método que o FireRed não tem (gênero, clima, item de troca
  especial, EVO_SPIN/THRESHOLD/SCRIPT_TRIGGER) são puladas e contadas.
- Golpes que não existem no FireRed são filtrados do learnset; a E4 acrescenta os
  golpes novos.

Uso
---
    python3 scripts/firered/gen_species_data.py --self-test
    python3 scripts/firered/gen_species_data.py --pokefirered /tmp/pokefirered \\
        --reference /tmp/fre --write
    python3 scripts/firered/gen_species_data.py --pokefirered /tmp/pokefirered \\
        --reference /tmp/fre --check      # falha se o gerado divergir do clone

O `--check` é o que garante que ninguém editou o gerado à mão.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------------
# constantes do FireRed (mesmos nomes usados no jogo)
# ----------------------------------------------------------------------------
TIPOS_FIRERED = {
    "TYPE_NONE", "TYPE_NORMAL", "TYPE_FIGHTING", "TYPE_FLYING", "TYPE_POISON",
    "TYPE_GROUND", "TYPE_ROCK", "TYPE_BUG", "TYPE_GHOST", "TYPE_STEEL",
    "TYPE_MYSTERY", "TYPE_FIRE", "TYPE_WATER", "TYPE_GRASS", "TYPE_ELECTRIC",
    "TYPE_PSYCHIC", "TYPE_ICE", "TYPE_DRAGON", "TYPE_DARK",
    "TYPE_FAIRY",      # E3: existe no motor a partir do port da E3
}
# tipos que o FireRed (nem com a E3) tem: STELLAR é exclusivo do Terapagos
TIPOS_SUBSTITUTOS = {"TYPE_STELLAR": "TYPE_NORMAL"}

EVO_SUPORTADAS = {
    "EVO_FRIENDSHIP", "EVO_FRIENDSHIP_DAY", "EVO_FRIENDSHIP_NIGHT",
    "EVO_LEVEL", "EVO_TRADE", "EVO_TRADE_ITEM", "EVO_ITEM",
    "EVO_LEVEL_ATK_GT_DEF", "EVO_LEVEL_ATK_EQ_DEF", "EVO_LEVEL_ATK_LT_DEF",
}

PRIMEIRA_GEN4 = 387          # Turtwig

# cache das macros (#define) do RHH, por diretório de referência
_MACROS: dict[str, dict[str, str]] = {}


def tabela_macros(ref: Path) -> dict[str, str]:
    """Todos os `#define NOME valor` simples do RHH (sem macro de função).

    Alguns campos usam constantes nomeadas — `GIRATINA_EXP_YIELD`, por exemplo —
    em vez do número. Sem expandir, o parser não consegue avaliar.
    """
    chave = str(ref.resolve())
    if chave in _MACROS:
        return _MACROS[chave]
    tabela: dict[str, str] = {}
    for arq in (ref / "include").rglob("*.h"):
        for m in re.finditer(r"^#define\s+([A-Za-z_]\w*)\s+(.+)$",
                             arq.read_text(errors="replace"), re.M):
            nome, valor = m.group(1), m.group(2)
            if "(" in nome:
                continue
            valor = valor.split("//")[0].strip()
            if valor:
                tabela[nome] = valor

    # Os arquivos de espécie definem constantes locais dentro de blocos `#if`
    # (ex.: GIRATINA_EXP_YIELD muda por geração). O primeiro `#define` é o da
    # geração mais alta, que é o valor que queremos.
    for arq in (ref / "src" / "data" / "pokemon" / "species_info").glob("gen_*_families.h"):
        for m in re.finditer(r"^\s*#define\s+([A-Za-z_]\w*)\s+(.+)$",
                             arq.read_text(errors="replace"), re.M):
            nome, valor = m.group(1), m.group(2)
            if "(" in nome:
                continue
            valor = valor.split("//")[0].strip()
            if valor and nome not in tabela:
                tabela[nome] = valor
    # amizade base: o RHH calcula 50 (padrão das gens >= 8). O FireRed usa 70,
    # e é esse valor que mantém as evoluções por amizade com o mesmo limiar.
    for nome_macro in ("STANDARD_FRIENDSHIP", "HIGH_FRIENDSHIP"):
        tabela.pop(nome_macro, None)
    _MACROS[chave] = tabela
    return tabela
ULTIMA_ESPECIE = 1025        # Pecharunt


# ----------------------------------------------------------------------------
# leitura do FireRed: quais nomes existem lá
# ----------------------------------------------------------------------------
def nomes_do_firered(poke: Path) -> dict[str, set[str]]:
    """Conjunto de nomes de constante que o FireRed conhece."""
    inc = poke / "include" / "constants"
    def nomes(arquivo: str, prefixo: str) -> set[str]:
        texto = (inc / arquivo).read_text(errors="replace")
        return set(re.findall(rf"\b({prefixo}[A-Z0-9_]+)\b", texto))

    return {
        "moves": nomes("moves.h", "MOVE_"),
        "abilities": nomes("abilities.h", "ABILITY_"),
        "items": nomes("items.h", "ITEM_"),
        "growth": nomes("pokemon.h", "GROWTH_"),
        "body": nomes("pokemon.h", "BODY_COLOR_"),
        "egg": nomes("pokemon.h", "EGG_GROUP_"),
        "species": nomes("species.h", "SPECIES_"),
    }


# ----------------------------------------------------------------------------
# parser do RHH
# ----------------------------------------------------------------------------
_LINHA_MACRO = re.compile(r"^[ \t]*([A-Za-z_]\w*)\(([^()]*)\),?[ \t]*$", re.M)


def _expandir_chamadas(texto: str, fn: dict[str, tuple[list[str], str]],
                       max_iter: int = 3) -> str:
    """Expande macros usadas como fragmento de corpo, uma linha de cada vez.

    Algumas espécies montam o corpo em pedaços:
        [SPECIES_FLORGES_RED] = { FLORGES_MISC_INFO(Red, 0), .description = ... }

    A expansão é conservadora de propósito: só troca uma linha inteira que seja
    exatamente `MACRO(args),`. A primeira versão expandia qualquer ocorrência e
    estourou a memória (macros que se referenciam cresciam a cada passada).
    """
    if not fn:
        return texto
    for _ in range(max_iter):
        # as macros de corpo-fragmento (>= 3 linhas) são as que interessam;
        # trocar as pequenas (`PERCENT_FEMALE(50)`) quebraria os valores.
        def troca(m):
            nome, args_txt = m.group(1), m.group(2)
            if nome not in fn:
                return m.group(0)
            params, corpo = fn[nome]
            if corpo.count("\n") < 2:
                return m.group(0)
            args = separar_args(args_txt)
            for param, arg in zip(params, args):
                corpo = re.sub(rf"\b{re.escape(param)}\b", arg.strip(), corpo)
            # a macro termina sem vírgula (`.bodyColor = color`); a vírgula vem
            # do uso (`MISC_INFO(color),`). Sem repor, o último campo se cola no
            # campo seguinte e o parser perde os dois.
            if m.group(0).rstrip().endswith(",") and not corpo.rstrip().endswith(","):
                corpo = corpo.rstrip() + ","
            return corpo
        novo = _LINHA_MACRO.sub(troca, texto)
        if novo == texto:
            break
        texto = novo
    return texto


def blocos_de_especie(texto: str) -> dict[str, str]:
    """Separa `[SPECIES_X] = { ... },` ou `[SPECIES_X] = MACRO(...),` em nome -> corpo.

    Muitas espécies não têm corpo literal: usam macro de corpo inteiro. Há dois
    tipos no RHH, e os dois são resolvidos aqui:
      - sem parâmetros: `[SPECIES_MOTHIM_PLANT] = MOTHIM_SPECIES_INFO,`
      - com parâmetros: `[SPECIES_ARCEUS_FIRE] = ARCEUS_SPECIES_INFO(TYPE_FIRE, Fire, 2),`
    """
    # `\` no fim da linha: mantém a quebra, tira só o caractere
    texto = texto.replace("\\\n", "\n")

    obj: dict[str, str] = {}
    fn: dict[str, tuple[list[str], str]] = {}
    padrao = re.compile(r"^#define[ \t]+([A-Za-z_]\w*)(\([^)]*\))?[ \t]+(.*?)(?=\n\S|\n#|\Z)",
                        re.M | re.S)
    for m in padrao.finditer(texto):
        nome, params, corpo = m.group(1), m.group(2), m.group(3)
        if params is None:
            obj[nome] = corpo
        else:
            fn[nome] = ([x.strip() for x in params.strip("()").split(",") if x.strip()], corpo)

    marcas = list(re.finditer(r"^    \[SPECIES_([A-Z0-9_]+)\]\s*=\s*(.*)$", texto, re.M))
    saida: dict[str, str] = {}
    for i, m in enumerate(marcas):
        nome = m.group(1)
        resto = m.group(2).strip()
        if resto.startswith("{") or resto == "":
            fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
            trecho = texto[m.start():fim]
            # `#define` no meio do trecho é a definição de uma macro da PRÓXIMA
            # espécie (o FireRed/RHH define macros entre blocos). Sem cortar aqui,
            # o corpo da macro entra no bloco anterior e o `campos()` lê o
            # `.abilities`/`.natDexNum` dela: foi assim que Fezandipiti virou
            # Ogerpon (ABILITY_NONE + dex errada).
            corte = trecho.find("\n#define")
            if corte != -1:
                trecho = trecho[:corte]
            # expande só o bloco (pequeno): fragmentos tipo FLORGES_MISC_INFO(...)
            saida[nome] = _expandir_chamadas(trecho, fn)
            continue
        alvo = resto.rstrip(",").strip()
        if alvo in obj:
            # o corpo pode conter fragmentos do tipo MISC_INFO(...) dentro
            saida[nome] = _expandir_chamadas(obj[alvo], fn)
            continue
        chamada = re.match(r"^([A-Za-z_]\w*)\((.*)\)$", alvo, re.S)
        if chamada and chamada.group(1) in fn:
            params, corpo = fn[chamada.group(1)]
            args = separar_args(chamada.group(2))
            corpo = corpo
            for param, arg in zip(params, args):
                corpo = re.sub(rf"\b{re.escape(param)}\b", arg.strip(), corpo)
            corpo = re.sub(r"\s*##\s*", "", corpo)   # cola de token
            saida[nome] = _expandir_chamadas(corpo, fn)
    return saida


def campos(bloco: str) -> dict[str, str]:
    """Extrai `.campo = valor` respeitando parênteses, chaves e strings."""
    saida: dict[str, str] = {}
    i, n = 0, len(bloco)
    while True:
        j = bloco.find("\n        .", i)
        if j == -1:
            break
        j += len("\n        .")
        k = j
        while k < n and (bloco[k].isalnum() or bloco[k] == "_"):
            k += 1
        nome = bloco[j:k]
        # os campos vem alinhados: `.baseHP        = 45,` (espaços antes do =)
        while k < n and bloco[k] in " \t":
            k += 1
        if not bloco.startswith("= ", k):
            i = k
            continue
        k += 2
        ini = k
        prof = 0
        em_str = False
        esc = False
        while k < n:
            c = bloco[k]
            if em_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    em_str = False
            elif c == '"':
                em_str = True
            elif c in "([{":
                prof += 1
            elif c in ")]}":
                prof -= 1
            elif c == "," and prof == 0:
                break
            k += 1
        saida[nome] = bloco[ini:k].strip()
        i = k
    return saida


def _tirar_parens_externos(txt: str) -> str:
    """Remove parênteses que envolvem a expressão inteira: `(a >= b)` -> `a >= b`."""
    txt = txt.strip()
    while txt.startswith("(") and txt.endswith(")"):
        prof = 0
        fecha_antes = False
        for i, c in enumerate(txt):
            if c == "(":
                prof += 1
            elif c == ")":
                prof -= 1
                if prof == 0 and i < len(txt) - 1:
                    fecha_antes = True
                    break
        if fecha_antes:
            break
        txt = txt[1:-1].strip()
    return txt


def _sem_ternario(txt: str) -> str:
    """Converte `cond ? a : b` (C) em `a if cond else b` (Python)."""
    txt = _tirar_parens_externos(txt)
    prof = 0
    em_str = False
    q = -1
    for i, c in enumerate(txt):
        if em_str:
            if c == '"':
                em_str = False
            continue
        if c == '"':
            em_str = True
        elif c in "([{":
            prof += 1
        elif c in ")]}":
            prof -= 1
        elif c == "?" and prof == 0:
            q = i
            break
    if q == -1:
        return txt
    # acha o ':' correspondente no mesmo nível
    prof = 0
    em_str = False
    for i in range(q + 1, len(txt)):
        c = txt[i]
        if em_str:
            if c == '"':
                em_str = False
            continue
        if c == '"':
            em_str = True
        elif c in "([{":
            prof += 1
        elif c in ")]}":
            prof -= 1
        elif c == ":" and prof == 0:
            cond = _sem_ternario(_tirar_parens_externos(txt[:q]))
            a = _sem_ternario(txt[q + 1:i])
            b = _sem_ternario(txt[i + 1:])
            return f"({a}) if ({cond}) else ({b})"
    raise ValueError(f"ternário sem ':' em {txt!r}")


def avaliar(txt: str, env: dict[str, int]) -> int:
    """Avalia uma expressão aritmética do RHH.

    Ordem importa: primeiro expandimos as macros (`STANDARD_FRIENDSHIP` vira
    `((P_UPDATED_FRIENDSHIP >= GEN_8) ? 50 : 70)`), só depois traduzimos o
    ternário — expandir depois deixaria ternários sem tradução.
    """
    expr = txt.strip()
    macros = env.get("__macros__", {})
    for _ in range(12):
        novo = re.sub(r"\b([A-Za-z_]\w*)\b",
                      lambda m: macros.get(m.group(1), m.group(1)), expr)
        if novo == expr:
            break
        expr = novo
    expr = re.sub(r"\b[PB]_[A-Z0-9_]+\b", lambda m: str(env.get(m.group(0), 9)), expr)
    expr = _sem_ternario(expr)
    expr = re.sub(r"\((?:u8|u16|u32|s8|s16|s32)\)", "", expr)
    expr = expr.replace("&&", " and ").replace("||", " or ")
    try:
        return int(eval(expr, {"__builtins__": {}}, env))  # noqa: S307 (texto do repo, sem entrada externa)
    except Exception as e:  # pragma: no cover - mensagem clara
        raise ValueError(f"não consegui avaliar {txt!r} (virou {expr!r}): {e}") from e


def separar_args(txt: str) -> list[str]:
    """Separa argumentos de macro por vírgula no nível 0."""
    saida, atual, prof, em_str = [], "", 0, False
    for c in txt:
        if em_str:
            atual += c
            if c == '"':
                em_str = False
            continue
        if c == '"':
            em_str = True
            atual += c
        elif c in "([{":
            prof += 1
            atual += c
        elif c in ")]}":
            prof -= 1
            atual += c
        elif c == "," and prof == 0:
            saida.append(atual.strip())
            atual = ""
        else:
            atual += c
    if atual.strip():
        saida.append(atual.strip())
    return saida


def corpo_macro(valor: str, nome: str) -> str | None:
    """Devolve o interior de `NOME(...)`, ou None se não for essa macro."""
    m = re.match(rf"^{nome}\s*\((.*)\)\s*$", valor.strip(), re.S)
    return m.group(1) if m else None


def tipo_para_firered(nome: str) -> str:
    if nome in TIPOS_FIRERED:
        return nome
    return TIPOS_SUBSTITUTOS.get(nome, "TYPE_NORMAL")


def genero(valor: str) -> int:
    v = valor.strip()
    if v == "MON_MALE":
        return 0
    if v == "MON_FEMALE":
        return 254
    if v == "MON_GENDERLESS":
        return 255
    dentro = corpo_macro(v, "PERCENT_FEMALE")
    if dentro is not None:
        pct = float(dentro)
        return min(254, int(pct * 255 / 100))
    try:
        return int(v)
    except ValueError:
        return 127


def lista_de_abilities(valor: str, conhecidas: set[str], rel: dict) -> tuple[str, str]:
    dentro = valor.strip()
    if dentro.startswith("{") and dentro.endswith("}"):
        dentro = dentro[1:-1]
    itens = [x.strip() for x in separar_args(dentro) if x.strip()]
    saida = []
    for x in itens[:2]:
        if x in conhecidas:
            saida.append(x)
        else:
            rel["habilidades_ausentes"] += 1
            saida.append("ABILITY_NONE")
    while len(saida) < 2:
        saida.append("ABILITY_NONE")
    return saida[0], saida[1]


# ----------------------------------------------------------------------------
# aprendizado de golpes
# ----------------------------------------------------------------------------
def aprender_learnsets(ref: Path) -> dict[str, list[tuple[int, str]]]:
    """nome de learnset -> [(nível, MOVE_X), ...] do arquivo da gen mais alta."""
    pasta = ref / "src" / "data" / "pokemon" / "level_up_learnsets"
    arquivos = sorted(pasta.glob("gen_*.h"))
    if not arquivos:
        raise SystemExit(f"não achei os learnsets do RHH em {pasta}")
    saida: dict[str, list[tuple[int, str]]] = {}
    for arquivo in arquivos:          # ordem crescente: a última gen vence
        texto = arquivo.read_text(errors="replace")
        for m in re.finditer(r"static const struct LevelUpMove (s\w+LevelUpLearnset)\[\] = \{(.*?)\};",
                             texto, re.S):
            nome, corpo = m.group(1), m.group(2)
            itens = []
            for lvl, mov in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_[A-Z0-9_]+)\s*\)", corpo):
                itens.append((int(lvl), mov))
            saida[nome] = itens
    return saida


# ----------------------------------------------------------------------------
# geração
# ----------------------------------------------------------------------------
def carregar_referencia(ref: Path) -> dict[str, dict[str, str]]:
    pasta = ref / "src" / "data" / "pokemon" / "species_info"
    tudo: dict[str, dict[str, str]] = {}
    for arquivo in sorted(pasta.glob("gen_*_families.h")):
        for nome, bloco in blocos_de_especie(arquivo.read_text(errors="replace")).items():
            tudo[nome] = campos(bloco)
    return tudo


def bloco_da_especie(nome: str, dados: dict[str, dict[str, str]]) -> dict[str, str] | None:
    """Bloco da espécie, resolvendo formas.

    A dex nacional tem um nome por espécie (MIMIKYU), mas o RHH dá nomes por
    forma (MIMIKYU_DISGUISED). Quando o nome exato não existe, usa a forma base:
    a de sufixo mais curto e, em empate, a primeira em ordem alfabética — para a
    escolha ser determinística.
    """
    if nome in dados:
        return dados[nome]
    candidatos = [k for k in dados if k.startswith(nome + "_")]
    if not candidatos:
        return None
    return dados[min(candidatos, key=lambda k: (len(k), k))]


def gerar(ref: Path, poke: Path) -> tuple[dict[str, str], str, dict[str, int]]:
    """Devolve (arquivos gerados, relatório)."""
    conhecidas = nomes_do_firered(poke)
    dados = carregar_referencia(ref)
    learnsets = aprender_learnsets(ref)

    rel = {
        "especies": 0, "habilidades_ausentes": 0, "exp_limitado": 0,
        "evos_puladas": 0, "golpes_filtrados": 0, "categoria_truncada": 0,
        "tipos_substituidos": 0,
    }

    # ordem numérica = ordem nacional (a E1 fixou isso). O número vem do
    # pokedex.h do próprio clone: o RHH só tem o nome, não o índice.
    numeracao = numeracao_nacional(poke)
    ordens = sorted((num, nome) for nome, num in numeracao.items())
    if len(ordens) < ULTIMA_ESPECIE:
        raise SystemExit(f"só {len(ordens)} espécies casaram com a numeração; "
                         "o pokedex.h do clone está incompleto?")

    env = {f"GEN_{n}": n for n in range(1, 10)}
    env["__macros__"] = tabela_macros(ref)
    for chave in ("P_UPDATED_EXP_YIELDS", "P_UPDATED_LEARNSETS", "P_LEVEL_UP_LEARNSETS",
                  "P_UPDATED_EVOLUTIONS", "P_EVOLUTIONS", "P_FRIENDSHIP_EVO_THRESHOLD"):
        env[chave] = 9
    # amizade base: o FireRed segue a mecânica da Gen 3, em que o padrão é 70.
    # (o RHH usa 50 nas gens >= 8; aqui mantemos 70 para as evoluções por
    # amizade continuarem com o mesmo limiar do jogo)
    env["STANDARD_FRIENDSHIP"] = 70
    env["HIGH_FRIENDSHIP"] = 100

    linhas_species = []
    linhas_texto = []      # arrays de texto: ficam fora do inicializador
    linhas_dex = []
    linhas_evo = []
    linhas_learn = []
    linhas_ponteiros = []

    for ndex, nome in ordens:
        if ndex < PRIMEIRA_GEN4 or ndex > ULTIMA_ESPECIE:
            continue
        c = bloco_da_especie(nome, dados)
        if c is None:
            print(f"aviso: sem dados para {nome} (#{ndex})", file=sys.stderr)
            continue
        rel["especies"] += 1

        def num(campo: str, padrao: int = 0) -> int:
            v = c.get(campo)
            if v is None:
                return padrao
            return avaliar(v, env)

        stats = [num(x) for x in ("baseHP", "baseAttack", "baseDefense",
                                  "baseSpeed", "baseSpAttack", "baseSpDefense")]
        if not all(1 <= s <= 255 for s in stats):
            print(f"aviso: {nome} com stats fora de faixa: {stats}", file=sys.stderr)

        # tipos
        tipos = []
        bruto = c.get("types", "MON_TYPES(TYPE_NORMAL)")
        dentro = corpo_macro(bruto, "MON_TYPES")
        if dentro is None:
            dentro = bruto.strip("{} ")
        for t in separar_args(dentro):
            if not t:
                continue
            ft = tipo_para_firered(t.strip())
            if ft != t.strip():
                rel["tipos_substituidos"] += 1
            tipos.append(ft)
        if not tipos:
            tipos = ["TYPE_NORMAL"]
        while len(tipos) < 2:
            tipos.append(tipos[0])

        # EV yields
        evs = [num("evYield_HP"), num("evYield_Attack"), num("evYield_Defense"),
               num("evYield_Speed"), num("evYield_SpAttack"), num("evYield_SpDefense")]
        evs = [max(0, min(3, v)) for v in evs]   # campo de 2 bits

        exp = num("expYield", 100)
        if exp > 255:
            exp = 255
            rel["exp_limitado"] += 1

        # itens
        def item(campo: str) -> str:
            v = c.get(campo, "ITEM_NONE").strip()
            if v in conhecidas["items"]:
                return v
            if v in ("ITEM_NONE", "ITEM_NONE_2"):
                return "ITEM_NONE"
            return "ITEM_NONE"

        # habilidades
        ab1, ab2 = lista_de_abilities(c.get("abilities", "{ABILITY_NONE, ABILITY_NONE}"),
                                      conhecidas["abilities"], rel)

        # grupos de ovo
        bruto_egg = c.get("eggGroups", "MON_EGG_GROUPS(EGG_GROUP_NONE)")
        dentro = corpo_macro(bruto_egg, "MON_EGG_GROUPS")
        if dentro is None:
            dentro = bruto_egg.strip("{} ")
        grupos = [g.strip() for g in separar_args(dentro) if g.strip()]
        grupos = [g if g in conhecidas["egg"] else "EGG_GROUP_NONE" for g in grupos]
        while len(grupos) < 2:
            grupos.append(grupos[0] if grupos else "EGG_GROUP_NONE")

        crescimento = c.get("growthRate", "GROWTH_MEDIUM_FAST").strip()
        if crescimento not in conhecidas["growth"]:
            crescimento = "GROWTH_MEDIUM_FAST"

        cor = c.get("bodyColor", "BODY_COLOR_GRAY").strip()
        if cor not in conhecidas["body"]:
            cor = "BODY_COLOR_GRAY"

        linhas_species.append(
            f"    [SPECIES_{nome}] =\n"
            "    {\n"
            f"        .baseHP = {stats[0]},\n"
            f"        .baseAttack = {stats[1]},\n"
            f"        .baseDefense = {stats[2]},\n"
            f"        .baseSpeed = {stats[3]},\n"
            f"        .baseSpAttack = {stats[4]},\n"
            f"        .baseSpDefense = {stats[5]},\n"
            f"        .types = {{{tipos[0]}, {tipos[1]}}},\n"
            f"        .catchRate = {max(0, min(255, num('catchRate', 45)))},\n"
            f"        .expYield = {exp},\n"
            f"        .evYield_HP = {evs[0]},\n"
            f"        .evYield_Attack = {evs[1]},\n"
            f"        .evYield_Defense = {evs[2]},\n"
            f"        .evYield_Speed = {evs[3]},\n"
            f"        .evYield_SpAttack = {evs[4]},\n"
            f"        .evYield_SpDefense = {evs[5]},\n"
            f"        .itemCommon = {item('itemCommon')},\n"
            f"        .itemRare = {item('itemRare')},\n"
            f"        .genderRatio = {genero(c.get('genderRatio', 'PERCENT_FEMALE(50)'))},\n"
            f"        .eggCycles = {max(0, min(255, num('eggCycles', 20)))},\n"
            f"        .friendship = {max(0, min(255, num('friendship', 70)))},\n"
            f"        .growthRate = {crescimento},\n"
            f"        .eggGroups = {{{grupos[0]}, {grupos[1]}}},\n"
            f"        .abilities = {{{ab1}, {ab2}}},\n"
            "        .safariZoneFleeRate = 0,\n"
            f"        .bodyColor = {cor},\n"
            "        .noFlip = FALSE,\n"
            "    },\n"
        )

        # ---------------- Pokédex ----------------
        categoria = _texto_simples(c.get("categoryName", '""')) or ""
        categoria = _sanitizar_texto(categoria, largura=11, max_linhas=1)
        if len(categoria) > 11:
            categoria = categoria[:11]
            rel["categoria_truncada"] += 1
        altura = num("height", 10)
        peso = num("weight", 100)
        descricao = _texto_simples(c.get("description", '""'), preservar_quebras=True,
                                   estrito=True)
        if descricao is None:
            # RHH usa expressão C em alguns casos (SILVALLY/MINIOR): escrevemos
            # um texto neutro em vez de vazar código para dentro do literal.
            rel["descricao_substituida"] = rel.get("descricao_substituida", 0) + 1
            descricao = (f"{nome.replace('_', ' ').title()} lives in a distant "
                         "region. Its ecology is still being studied.")
        descricao = _sanitizar_texto(descricao)
        linhas_dex.append(
            f"    [NATIONAL_DEX_{nome}] =\n"
            "    {\n"
            f'        .categoryName = _("{_literal_c(categoria)}"),\n'
            f"        .height = {altura},\n"
            f"        .weight = {peso},\n"
            f"        .description = sPokedexText_{nome},\n"
            f"        .unusedDescription = sPokedexText_{nome},\n"
            f"        .pokemonScale = {max(0, min(65535, num('pokemonScale', 256)))},\n"
            f"        .pokemonOffset = {max(0, min(65535, num('pokemonOffset', 0)))},\n"
            f"        .trainerScale = {max(0, min(65535, num('trainerScale', 256)))},\n"
            f"        .trainerOffset = {max(0, min(65535, num('trainerOffset', 0)))},\n"
            "    },\n"
        )
        linhas_texto.append(
            f'static const u8 sPokedexText_{nome}[] = _("{_literal_c(descricao)}");\n')

        # ---------------- evoluções ----------------
        bruto_evo = c.get("evolutions")
        if bruto_evo:
            dentro = corpo_macro(bruto_evo, "EVOLUTION")
            if dentro:
                entradas = []
                for arg in separar_args(dentro):
                    m = re.match(r"^\{(.*)\}$", arg.strip(), re.S)
                    if not m:
                        continue
                    partes = separar_args(m.group(1))
                    if len(partes) < 3:
                        continue
                    metodo, param, alvo = partes[0].strip(), partes[1].strip(), partes[2].strip()
                    if metodo not in EVO_SUPORTADAS:
                        rel["evos_puladas"] += 1
                        continue
                    if alvo not in conhecidas["species"]:
                        rel["evos_puladas"] += 1
                        continue
                    try:
                        p = avaliar(param, env)
                    except ValueError:
                        p = 0
                    if metodo == "EVO_ITEM" and param not in conhecidas["items"]:
                        rel["evos_puladas"] += 1
                        continue
                    entradas.append(f"{{{metodo}, {p}, {alvo}}}")
                if entradas:
                    linhas_evo.append(f"    [SPECIES_{nome}] = {{{', '.join(entradas)}}},\n")

        # ---------------- learnset ----------------
        nome_ls = (c.get("levelUpLearnset") or "").strip()
        if nome_ls and nome_ls in learnsets:
            golpes = []
            for nivel, mov in learnsets[nome_ls]:
                if mov in conhecidas["moves"]:
                    golpes.append((min(100, nivel), mov))
                else:
                    rel["golpes_filtrados"] += 1
            if not golpes:
                golpes = [(1, "MOVE_TACKLE")]
            linhas_learn.append(
                f"static const u16 s{nome.title()}LevelUpLearnsetG4[] = {{\n"
                + "".join(f"    LEVEL_UP_MOVE({lvl}, {mov}),\n" for lvl, mov in golpes)
                + "    LEVEL_UP_END,\n};\n\n"
            )
            linhas_ponteiros.append(
                f"    [SPECIES_{nome}] = s{nome.title()}LevelUpLearnsetG4,\n")

    arquivos = {
        "species_info_gen4_9.h": (
            "// Gerado por scripts/firered/gen_species_data.py -- nao editar a mao.\n"
            "// Dados de stats/tipos/itens das espécies 387-1025 (Gen 4-9).\n"
            "// Fonte: RHH pokeemerald-expansion (dados oficiais).\n" + "".join(linhas_species)
        ),
        "pokedex_text_gen4_9.h": (
            "// Gerado por scripts/firered/gen_species_data.py -- nao editar a mao.\n"
            "// Textos de Pokedex das especies 387-1025 (Gen 4-9).\n"
            + "".join(linhas_texto)
        ),
        "pokedex_entries_gen4_9.h": (
            "// Gerado por scripts/firered/gen_species_data.py -- nao editar a mao.\n"
            "// Entradas de Pokédex das espécies 387-1025 (Gen 4-9).\n"
            + "".join(linhas_dex)
        ),
        "evolution_gen4_9.h": (
            "// Gerado por scripts/firered/gen_species_data.py -- nao editar a mao.\n"
            "// Evoluções das espécies 387-1025 (Gen 4-9).\n"
            + "".join(linhas_evo)
        ),
        "level_up_learnsets_gen4_9.h": (
            "// Gerado por scripts/firered/gen_species_data.py -- nao editar a mao.\n"
            "// Golpes por nível das espécies 387-1025, filtrados para os que o\n"
            "// FireRed conhece (os novos entram na E4).\n"
            + "".join(linhas_learn)
        ),
    }
    ponteiros = ("    // gen 4-9 (gerados)\n" + "".join(linhas_ponteiros))
    return arquivos, ponteiros, rel


def numeracao_nacional(poke: Path) -> dict[str, int]:
    """nome da espécie -> número da dex nacional, lido do enum do clone."""
    texto = (poke / "include" / "constants" / "pokedex.h").read_text()
    m = re.search(r"enum \{\s*NATIONAL_DEX_NONE,(.*?)\};", texto, re.S)
    if not m:
        raise SystemExit("não achei o enum NATIONAL_DEX_* no clone")
    nomes = re.findall(r"NATIONAL_DEX_([A-Z0-9_]+)", m.group(1))
    return {nome: i + 1 for i, nome in enumerate(nomes)}


def _texto_simples(bruto: str, preservar_quebras: bool = False,
                   estrito: bool = False):
    """Extrai o conteúdo de `COMPOUND_STRING("...")` ou `_("...")` como texto C.

    `estrito=True` devolve None quando o campo **não** é um literal de string
    (o RHH usa expressões C como `(type == TYPE_NORMAL ? gSilvallyNormal… : …)`
    em alguns Pokédex; sem isso o texto entra cru no `_("...")` e não compila).
    """
    b = bruto.strip()
    for macro in ("COMPOUND_STRING", "_"):
        dentro = corpo_macro(b, macro)
        if dentro is not None:
            b = dentro.strip()
            break
    if estrito and not re.fullmatch(r'"(?:[^"\\]|\\.)*"(?:\s*"(?:[^"\\]|\\.)*")*', b, re.S):
        return None
    if b.startswith('"') and b.endswith('"'):
        b = b[1:-1]
    # junta literais adjacentes: "abc" "def" -> abcdef
    b = re.sub(r'"\s*"', "", b)
    if not preservar_quebras:
        b = b.replace("\\n", " ").replace("\\p", " ")
    return b.strip()


def _literal_c(texto: str) -> str:
    """Conteúdo pronto para dentro de `_("...")`.

    `_sanitizar_texto` já deixou só `\n` como escape e nenhuma aspa (o charmap
    do FireRed não tem `"`); aqui é só uma rede de segurança.
    """
    assert chr(92) not in texto.replace(chr(92) + "n", ""), "escape inesperado no texto"
    assert '"' not in texto, "aspa dupla nao tem no charmap"
    return texto


_ACENTOS = str.maketrans({
    "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "í": "i", "ì": "i", "î": "i", "ï": "i",
    "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o",
    "ú": "u", "ù": "u", "û": "u", "ü": "u",
    "ç": "c", "ñ": "n",
    "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ç": "C", "Ñ": "N",
    "♀": "F", "♂": "M", "’": "'", "‘": "'", "“": '"', "”": '"',
    "…": "...", "×": "x", "·": "-", "—": "-", "–": "-",
})


# O charmap do FireRed (inglês) não cobre todo o ASCII -- `"` dá
# "no mapping exists for double quote". Fica só o que o jogo sabe desenhar.
_SEGUROS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
               " .,!?'-:/()%&+*=;<>")


def _sanitizar_texto(texto: str, largura: int = 38, max_linhas: int = 4) -> str:
    """Deixa o texto seguro para `_("...")` do FireRed: ASCII, sem quebras
    literais, re-quebrado em `\n` e limitado ao que a caixa do Pokedex mostra."""
    t = texto.replace(r"\p", "\n").replace(r"\l", "\n")
    t = t.replace(r"\n", "\n")
    t = t.replace(chr(92), "")          # escapes restantes (é, x) somem
    t = t.translate(_ACENTOS).replace('"', "'")
    t = "".join(c if c == "\n" or c in _SEGUROS else " " for c in t)
    t = t.replace("\t", " ")
    linhas = []
    atual = ""
    for paragrafo in t.split("\n"):
        for palavra in paragrafo.split():
            if atual and len(atual) + 1 + len(palavra) > largura:
                linhas.append(atual)
                atual = palavra
            else:
                atual = palavra if not atual else f"{atual} {palavra}"
        if atual:                      # quebra de linha do texto original é mantida
            linhas.append(atual)
            atual = ""
    if atual:
        linhas.append(atual)
    if len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]
        linhas[-1] = linhas[-1][: largura - 3].rstrip() + "..."
    return r"\n".join(linhas)


# ----------------------------------------------------------------------------
# integração no clone
# ----------------------------------------------------------------------------
MARCA_BASE = "// === GERADO: gen 4-9 (scripts/firered/gen_species_data.py)"

# (id, arquivo que recebe, linha a inserir antes do `};` final)
INCLUDES = [
    ("species_info", "src/data/pokemon/species_info.h", '#include "species_info_gen4_9.h"'),
    ("pokedex_entries", "src/data/pokemon/pokedex_entries.h", '#include "pokedex_entries_gen4_9.h"'),
    ("evolution", "src/data/pokemon/evolution.h", '#include "evolution_gen4_9.h"'),
    # learnsets: as entradas terminam em `LEVEL_UP_END` SEM vírgula, então o
    # include não pode ir antes do `};` final (cairia dentro do inicializador).
    # Vai logo depois dos #define do topo.
    ("learnsets", "src/data/pokemon/level_up_learnsets.h", '#include "level_up_learnsets_gen4_9.h"'),
]


# (id do bloco, arquivo onde ele NAO pode ficar) — limpeza de versoes antigas
BLOCOS_OBSOLETOS = [
    ("pokedex_text", "src/data/pokemon/pokedex_entries.h"),
]

# (id, arquivo que recebe, linha a anexar no FIM do arquivo)
INCLUDES_FIM = [
    ("pokedex_text", "src/data/pokemon/pokedex_text.h", '#include "pokedex_text_gen4_9.h"'),
]


def _marcas(marca_id: str) -> tuple[str, str]:
    return f"{MARCA_BASE} [{marca_id}] ===", f"// === FIM DO GERADO [{marca_id}] ==="


def _bloco(conteudo: str, marca_id: str) -> str:
    ini, fim = _marcas(marca_id)
    return f"{ini}\n{conteudo}\n{fim}\n"


def _remover_bloco(texto: str, marca_id: str) -> tuple[str, bool]:
    """Tira um bloco gerado (de qualquer posicao). Devolve (texto, removeu)."""
    ini_marca, fim_marca = _marcas(marca_id)
    if ini_marca not in texto:
        return texto, False
    ini = texto.index(ini_marca)
    fim = texto.index(fim_marca) + len(fim_marca)
    while fim < len(texto) and texto[fim] == "\n":
        fim += 1
    return texto[:ini] + texto[fim:], True


def _anexar_fim(texto: str, conteudo: str, marca_id: str) -> str:
    """Anexa o bloco no fim do arquivo (declarações de escopo de arquivo)."""
    ini_marca, fim_marca = _marcas(marca_id)
    if ini_marca in texto:
        ini = texto.index(ini_marca)
        fim = texto.index(fim_marca) + len(fim_marca)
        while fim < len(texto) and texto[fim] == "\n":
            fim += 1
        texto = texto[:ini] + texto[fim:]
    if texto and not texto.endswith("\n"):
        texto += "\n"
    return texto + _bloco(conteudo, marca_id)


def _inserir_apos_defines(texto: str, conteudo: str, marca_id: str) -> str:
    """Insere o bloco logo depois do preâmbulo de #define (e #include) do topo.

    `level_up_learnsets.h` fecha cada entrada com `LEVEL_UP_END` **sem vírgula**:
    inserir antes do `};` final colocaria declarações dentro do inicializador.
    """
    ini_marca, fim_marca = _marcas(marca_id)
    if ini_marca in texto:
        ini = texto.index(ini_marca)
        fim = texto.index(fim_marca) + len(fim_marca)
        while fim < len(texto) and texto[fim] == "\n":
            fim += 1
        texto = texto[:ini] + texto[fim:]
    linhas = texto.splitlines(keepends=True)
    corte = 0
    for i, linha in enumerate(linhas):
        crua = linha.strip()
        if not crua or crua.startswith("//") or crua.startswith("#define") or crua.startswith("#include"):
            corte = i + 1
            continue
        break
    return "".join(linhas[:corte]) + _bloco(conteudo, marca_id) + "".join(linhas[corte:])


def _inserir_topo(texto: str, conteudo: str, marca_id: str) -> str:
    """Põe o bloco no começo do arquivo (para declarações, não inicializadores).

    Se o bloco já existir no meio (de uma execução anterior), ele é removido:
    declaração dentro do inicializador do array não compila.
    """
    ini_marca, fim_marca = _marcas(marca_id)
    if ini_marca in texto:
        ini = texto.index(ini_marca)
        fim = texto.index(fim_marca) + len(fim_marca)
        while fim < len(texto) and texto[fim] == "\n":
            fim += 1
        texto = texto[:ini] + texto[fim:]
    return _bloco(conteudo, marca_id) + texto


def _inserir(texto: str, conteudo: str, marca_id: str) -> str:
    """Insere (ou substitui) o bloco gerado, sempre antes do `};` final."""
    ini_marca, fim_marca = _marcas(marca_id)
    bloco = _bloco(conteudo, marca_id)
    if ini_marca in texto:
        ini = texto.index(ini_marca)
        fim = texto.index(fim_marca) + len(fim_marca)
        while fim < len(texto) and texto[fim] == "\n":
            fim += 1
        return texto[:ini] + bloco + texto[fim:]
    fim = texto.rstrip().rfind("\n};")
    if fim == -1:
        raise SystemExit("não achei o fim do array para inserir o bloco gerado")
    return texto[:fim] + "\n" + bloco + texto[fim:]


def aplicar(poke: Path, arquivos: dict[str, str], ponteiros: str) -> list[str]:
    """Grava os headers e insere os `#include` / ponteiros (idempotente)."""
    destino = poke / "src" / "data" / "pokemon"
    mudancas = []
    for nome, conteudo in arquivos.items():
        p = destino / nome
        if not p.exists() or p.read_text() != conteudo:
            p.write_text(conteudo)
            mudancas.append(f"gerado {nome}")

    for marca_id, rel, linha in INCLUDES:
        p = poke / rel
        s = p.read_text()
        ini_marca, _ = _marcas(marca_id)
        if ini_marca in s and linha in s:
            continue
        if marca_id == "learnsets":
            p.write_text(_inserir_apos_defines(s, linha, marca_id))
        else:
            p.write_text(_inserir(s, linha, marca_id))
        mudancas.append(f"include em {rel}")

    for marca_id, rel, linha in INCLUDES_FIM:
        p = poke / rel
        s = p.read_text()
        ini_marca, _ = _marcas(marca_id)
        if ini_marca in s and linha in s:
            continue
        p.write_text(_anexar_fim(s, linha, marca_id))
        mudancas.append(f"include no fim de {rel}")

    # blocos deixados em arquivo errado por versoes antigas do gerador
    # (os textos ja moraram no topo de pokedex_entries.h)
    for marca_id, rel in BLOCOS_OBSOLETOS:
        p = poke / rel
        s = p.read_text()
        limpo, removeu = _remover_bloco(s, marca_id)
        if removeu:
            p.write_text(limpo)
            mudancas.append(f"bloco {marca_id} removido de {rel}")

    p = destino / "level_up_learnset_pointers.h"
    s = p.read_text()
    ini_marca, _ = _marcas("ponteiros")
    if ini_marca not in s:
        p.write_text(_inserir(s, ponteiros, "ponteiros"))
        mudancas.append("ponteiros de learnset da Gen 4-9")
    return mudancas


def verificar(poke: Path, arquivos: dict[str, str], ponteiros: str) -> int:
    destino = poke / "src" / "data" / "pokemon"
    falhas = 0
    for nome, conteudo in arquivos.items():
        p = destino / nome
        if not p.exists():
            print(f"FALTA: {nome}")
            falhas += 1
        elif p.read_text() != conteudo:
            print(f"DIVERGE: {nome} (rode --write)")
            falhas += 1
    for marca_id, rel, linha in INCLUDES + INCLUDES_FIM:
        s = (poke / rel).read_text()
        ini_marca, _ = _marcas(marca_id)
        if ini_marca not in s or linha not in s:
            print(f"FALTA: include de {linha} em {rel}")
            falhas += 1
    for marca_id, rel in BLOCOS_OBSOLETOS:
        ini_marca, _ = _marcas(marca_id)
        if ini_marca in (poke / rel).read_text():
            print(f"SOBRA: bloco {marca_id} em {rel}")
            falhas += 1
    s = (destino / "level_up_learnset_pointers.h").read_text()
    ini_marca, _ = _marcas("ponteiros")
    if ini_marca not in s or ponteiros.splitlines()[0].strip() not in s:
        print("FALTA: ponteiros de learnset da Gen 4-9")
        falhas += 1
    return falhas


# ----------------------------------------------------------------------------
# self-test
# ----------------------------------------------------------------------------
# Valores conferidos contra a Pokédex oficial (stats base, tipos, capture rate,
# exp yield da geração atual, EVs, ciclos de ovo e cor). Onde o FireRed ainda não
# tem o tipo (Fada), o esperado é o substituto temporário.
AMOSTRAS = {
    "TREECKO": dict(stats=(40, 45, 35, 70, 65, 55), types=("TYPE_GRASS", "TYPE_GRASS"),
                    catch=45, exp=62, evs={"Speed": 1}, egg=20, color="BODY_COLOR_GREEN"),
    "TURTWIG": dict(stats=(55, 68, 64, 31, 45, 55), types=("TYPE_GRASS", "TYPE_GRASS"),
                    catch=45, exp=64, evs={"Attack": 1}, egg=20, color="BODY_COLOR_GREEN"),
    "CHIMCHAR": dict(stats=(44, 58, 44, 61, 58, 44), types=("TYPE_FIRE", "TYPE_FIRE"),
                     catch=45, exp=62, evs={"Speed": 1}, egg=20, color="BODY_COLOR_BROWN"),
    "PIPLUP": dict(stats=(53, 51, 53, 40, 61, 56), types=("TYPE_WATER", "TYPE_WATER"),
                   catch=45, exp=63, evs={"SpAttack": 1}, egg=20, color="BODY_COLOR_BLUE"),
    "RIOLU": dict(stats=(40, 70, 40, 60, 35, 40), types=("TYPE_FIGHTING", "TYPE_FIGHTING"),
                  catch=75, exp=57, evs={"Attack": 1}, egg=25, color="BODY_COLOR_BLUE"),
    "LUCARIO": dict(stats=(70, 110, 70, 90, 115, 70), types=("TYPE_FIGHTING", "TYPE_STEEL"),
                    catch=45, exp=184, evs={"Attack": 1, "SpAttack": 1}, egg=25,
                    color="BODY_COLOR_BLUE"),
    "GARCHOMP": dict(stats=(108, 130, 95, 102, 80, 85), types=("TYPE_DRAGON", "TYPE_GROUND"),
                     catch=45, exp=218, evs={"Attack": 3}, egg=40, color="BODY_COLOR_BLUE"),
    "SNIVY": dict(stats=(45, 45, 55, 63, 45, 55), types=("TYPE_GRASS", "TYPE_GRASS"),
                  catch=45, exp=62, evs={"Speed": 1}, egg=20, color="BODY_COLOR_GREEN"),
    "ZOROARK": dict(stats=(60, 105, 60, 105, 120, 60), types=("TYPE_DARK", "TYPE_DARK"),
                    catch=45, exp=179, evs={"SpAttack": 2}, egg=20, color="BODY_COLOR_GRAY"),
    "FROAKIE": dict(stats=(41, 56, 40, 71, 62, 44), types=("TYPE_WATER", "TYPE_WATER"),
                    catch=45, exp=63, evs={"Speed": 1}, egg=20, color="BODY_COLOR_BLUE"),
    "GRENINJA": dict(stats=(72, 95, 67, 122, 103, 71), types=("TYPE_WATER", "TYPE_DARK"),
                     catch=45, exp=265, evs={"Speed": 3}, egg=20, color="BODY_COLOR_BLUE"),
    "ROWLET": dict(stats=(68, 55, 55, 42, 50, 50), types=("TYPE_GRASS", "TYPE_FLYING"),
                   catch=45, exp=64, evs={"HP": 1}, egg=15, color="BODY_COLOR_BROWN"),
    "DECIDUEYE": dict(stats=(78, 107, 75, 70, 100, 100), types=("TYPE_GRASS", "TYPE_GHOST"),
                      catch=45, exp=265, evs={"Attack": 3}, egg=15, color="BODY_COLOR_BROWN"),
    "MIMIKYU": dict(stats=(55, 90, 80, 96, 50, 105), types=("TYPE_GHOST", "TYPE_FAIRY"),
                    catch=45, exp=167, evs={"SpDefense": 2}, egg=20, color="BODY_COLOR_YELLOW"),
    "GROOKEY": dict(stats=(50, 65, 50, 65, 40, 40), types=("TYPE_GRASS", "TYPE_GRASS"),
                    catch=45, exp=62, evs={"Attack": 1}, egg=20, color="BODY_COLOR_GREEN"),
    "CINDERACE": dict(stats=(80, 116, 75, 119, 65, 75), types=("TYPE_FIRE", "TYPE_FIRE"),
                      catch=45, exp=265, evs={"Speed": 3}, egg=20, color="BODY_COLOR_WHITE"),
    "DRAGAPULT": dict(stats=(88, 120, 75, 142, 100, 75), types=("TYPE_DRAGON", "TYPE_GHOST"),
                      catch=45, exp=300, evs={"Speed": 3}, egg=40, color="BODY_COLOR_GREEN"),
    "SPRIGATITO": dict(stats=(40, 61, 54, 65, 45, 45), types=("TYPE_GRASS", "TYPE_GRASS"),
                       catch=45, exp=62, evs={"Speed": 1}, egg=20, color="BODY_COLOR_GREEN"),
    "MEOWSCARADA": dict(stats=(76, 110, 70, 123, 81, 70), types=("TYPE_GRASS", "TYPE_DARK"),
                        catch=45, exp=265, evs={"Speed": 3}, egg=20, color="BODY_COLOR_GREEN"),
    # E3: Fada deixou de ser substituida por Normal
    "FLORGES_RED": dict(stats=(78, 65, 68, 75, 112, 154), types=("TYPE_FAIRY", "TYPE_FAIRY"),
                        catch=45, exp=276, evs={"SpDefense": 3}, egg=20,
                        color="BODY_COLOR_WHITE"),
    "PECHARUNT": dict(stats=(88, 88, 160, 88, 88, 88), types=("TYPE_POISON", "TYPE_GHOST"),
                      catch=3, exp=300, evs={"Defense": 3}, egg=20, color="BODY_COLOR_PURPLE"),
}


def self_test(ref: Path, poke: Path) -> int:
    falhas = 0
    print(f"self-test: {ref} -> {poke}")
    dados = carregar_referencia(ref)
    if len(dados) < ULTIMA_ESPECIE:
        print(f"  FALHA: só {len(dados)} espécies na referência")
        return 1
    print(f"  ok: {len(dados)} espécies lidas da referência")

    conhecidas = nomes_do_firered(poke)
    if len(conhecidas["moves"]) < 350:
        print(f"  FALHA: só {len(conhecidas['moves'])} golpes no FireRed")
        falhas += 1
    print(f"  ok: FireRed conhece {len(conhecidas['moves'])} golpes, "
          f"{len(conhecidas['abilities'])} habilidades, {len(conhecidas['species'])} espécies")

    env = {f"GEN_{n}": n for n in range(1, 10)}
    env["P_UPDATED_EXP_YIELDS"] = 9
    env["__macros__"] = tabela_macros(ref)

    def campos_de(nome: str) -> dict[str, str]:
        c = bloco_da_especie(nome, dados)
        if c is None:
            raise KeyError(nome)
        return c

    for nome, esp in AMOSTRAS.items():
        c = campos_de(nome)
        stats = tuple(avaliar(c[x], env) for x in
                      ("baseHP", "baseAttack", "baseDefense", "baseSpeed",
                       "baseSpAttack", "baseSpDefense"))
        dentro = corpo_macro(c["types"], "MON_TYPES") or c["types"].strip("{} ")
        tipos = [tipo_para_firered(t.strip()) for t in separar_args(dentro)]
        while len(tipos) < 2:
            tipos.append(tipos[0])
        evs = {k[len("evYield_"):]: avaliar(c.get(k, "0"), env)
               for k in ("evYield_HP", "evYield_Attack", "evYield_Defense",
                         "evYield_Speed", "evYield_SpAttack", "evYield_SpDefense")
               if k in c}
        got = dict(stats=stats, types=tuple(tipos[:2]),
                   catch=avaliar(c["catchRate"], env),
                   exp=avaliar(c["expYield"], env), evs=evs,
                   egg=avaliar(c.get("eggCycles", "20"), env),
                   color=c.get("bodyColor", "").strip())
        # expYield é u8 no FireRed: o gerador limita a 255
        got["exp"] = min(255, got["exp"])
        esperado = dict(esp)
        esperado["exp"] = min(255, esperado["exp"])
        if got != esperado:
            print(f"  FALHA {nome}:")
            for chave in esperado:
                if got[chave] != esperado[chave]:
                    print(f"     {chave}: {got[chave]!r} != {esperado[chave]!r}")
            falhas += 1
        else:
            print(f"  ok: {nome}")

    # textos de Pokedex: sentinela de regressao (SILVALLY/MINIOR usam expressao C
    # no RHH; sem o modo estrito o texto vaza codigo para dentro do literal)
    casos = [
        ("a\\nb\\nc\\nd", "a\\nb\\nc\\nd"),            # quebras preservadas
        ("It is said to\\nemerge from\\nanother world.", "It is said to\\nemerge from\\nanother world."),
        ("Pokémon é ótimo", "Pokemon e otimo"),         # ASCII puro
    ]
    for entrada, esperado in casos:
        saida = _sanitizar_texto(entrada)
        if saida != esperado:
            print(f"  FALHA texto: {entrada!r} -> {saida!r} (esperava {esperado!r})")
            falhas += 1
    if _texto_simples("(type == TYPE_NORMAL ? a : b)", preservar_quebras=True,
                      estrito=True) is not None:
        print("  FALHA: expressao C aceita como texto de Pokedex")
        falhas += 1
    if _texto_simples('COMPOUND_STRING("ok")', estrito=True) != "ok":
        print("  FALHA: literal simples recusado pelo modo estrito")
        falhas += 1
    print("  ok: textos de Pokedex sanitizados")

    # determinismo + cobertura
    arqs1, pont1, rel = gerar(ref, poke)
    arqs2, pont2, _ = gerar(ref, poke)
    if (arqs1, pont1) != (arqs2, pont2):
        print("  FALHA: geração não é determinística"); falhas += 1
    else:
        print("  ok: geração determinística")
    textos = arqs1["pokedex_text_gen4_9.h"].splitlines()
    ruins = [t for t in textos
             if "static const u8" in t
             and (not t.rstrip().endswith(");")
                  or any(ord(c) > 126 for c in t)
                  or "\n" in t.rstrip()[:-1])]
    if ruins:
        print(f"  FALHA: {len(ruins)} texto(s) de Pokedex invalidos: {ruins[0][:80]!r}")
        falhas += 1
    else:
        print(f"  ok: {len(textos)} linhas de texto de Pokedex validas")

    n = rel["especies"]
    if n != ULTIMA_ESPECIE - PRIMEIRA_GEN4 + 1:
        print(f"  FALHA: gerou {n} espécies, esperava {ULTIMA_ESPECIE - PRIMEIRA_GEN4 + 1}")
        falhas += 1
    else:
        print(f"  ok: {n} espécies geradas")
    print(f"  relatório: {rel}")
    return 1 if falhas else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", type=Path, default=Path("/tmp/pokefirered"))
    ap.add_argument("--reference", type=Path, default=Path("/tmp/fre"))
    ap.add_argument("--write", action="store_true", help="grava os headers no clone")
    ap.add_argument("--check", action="store_true", help="falha se o clone divergir do gerado")
    ap.add_argument("--self-test", action="store_true", help="testa o parser com amostras conhecidas")
    ap.add_argument("--json", action="store_true", help="imprime o relatório em JSON")
    a = ap.parse_args()

    if a.self_test:
        return self_test(a.reference, a.pokefirered)

    arquivos, ponteiros, rel = gerar(a.reference, a.pokefirered)

    if a.json:
        import json
        print(json.dumps(rel, indent=2, ensure_ascii=False))

    if a.check:
        falhas = verificar(a.pokefirered, arquivos, ponteiros)
        if falhas:
            print(f"{falhas} divergência(s)")
            return 1
        print("ok: gerado bate com o clone")
        return 0

    if a.write:
        mudancas = aplicar(a.pokefirered, arquivos, ponteiros)
        for m in mudancas:
            print(" ", m)
        print(f"{len(mudancas)} mudança(s) | {rel}")
        return 0

    print("nada a fazer: use --write, --check ou --self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
