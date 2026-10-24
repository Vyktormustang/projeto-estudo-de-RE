#!/usr/bin/env python3
"""Gera os dados dos golpes das Gen 4-9 (E4, onda 1: só dados).

Por que isso existe
-------------------
O FireRed tem 355 golpes (Gen 1-3, IDs 0-354). As espécies novas da E2 tiveram
**3123 referências de golpe filtradas** porque o motor não conhecia o `MOVE_*`.
Esta etapa devolve os **446 golpes** que alguma espécie realmente aprende (442
novos + 4 que só mudaram de nome), mantendo congelados os IDs 0-354.

O que é gerado (idempotente, tudo dentro de blocos `// E4: inicio`/`// E4: fim`)

| arquivo                            | conteúdo                                   |
|------------------------------------|--------------------------------------------|
| `include/constants/moves.h`        | `MOVE_X n`, aliases e `MOVES_COUNT` 355→801 |
| `src/data/battle_moves.h`          | `gBattleMoves[]`: efeito/poder/tipo/precisão/PP/alvo/flags |
| `src/data/text/move_names.h`       | `gMoveNames[][]` regerada (MAIÚSCULA, 16 col.) |
| `src/move_descriptions.c`          | texto em até 4 linhas de 21 colunas         |
| `include/constants/global.h`       | `MOVE_NAME_LENGTH` 12 → 16                  |
| `src/data/battle_moves_category.h` | físico/especial (mesmo gerador da E3)       |

Mapeamento de efeito (o ponto delicado)
---------------------------------------
O RHH tem 281 efeitos; o FireRed, 214. Nome igual → mesmo efeito. `EFFECT_STAT_CHANGE`
(que o FireRed não tem) é inferido do bloco `ADDITIONAL_EFFECTS` (stat + estágio +
sinal) para os efeitos granulares `EFFECT_ATTACK_DOWN` / `EFFECT_SPECIAL_ATTACK_UP_2`
etc. O resto cai em **fallback seguro**: golpe de dano vira `EFFECT_HIT` (dano
neutro); golpe de status vira `EFFECT_SPLASH` (nada acontece) — nunca trava a
batalha, e o relatório diz quantos caíram em cada caso.

Uso
---
    python3 scripts/firered/gen_move_data.py --self-test
    python3 scripts/firered/gen_move_data.py --pokefirered /tmp/pokefirered \\
        --reference /tmp/fre --write
    python3 scripts/firered/gen_move_data.py --pokefirered /tmp/pokefirered \\
        --reference /tmp/fre --check
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MARCA = "// E4:"
NOME_MAX = 16          # MOVE_NAME_LENGTH: o maior nome do conjunto tem 16 ("Collision Course")
LINHA_MAX = 21         # maior linha das descrições originais do FireRed
LINHAS_MAX = 4
PODER_MAX = 255        # .power do FireRed é u8

# Efeitos do RHH que têm um equivalente direto no FireRed (mesma semântica).
MAPA_EFEITOS = {
    "EFFECT_TWO_TURNS_ATTACK": "EFFECT_RAZOR_WIND",   # carga genérica do Gen 3
    "EFFECT_FIRST_TURN_ONLY": "EFFECT_FAKE_OUT",
    "EFFECT_REFLECT_DAMAGE": "EFFECT_COUNTER",
    "EFFECT_DO_NOTHING": "EFFECT_SPLASH",
    "EFFECT_ROOST": "EFFECT_RESTORE_HP",          # cura 50% igual a Recover
    "EFFECT_HOLD_HANDS": "EFFECT_SPLASH",
    "EFFECT_CELEBRATE": "EFFECT_SPLASH",
    "EFFECT_HAPPY_HOUR": "EFFECT_SPLASH",
}

# nomes dos campos em `ADDITIONAL_EFFECTS` do RHH -> nome usado no EFFECT_* do FireRed
STAT_PARA_EFEITO = {
    "attack": "ATTACK", "defense": "DEFENSE", "speed": "SPEED",
    "spAtk": "SPECIAL_ATTACK", "spDef": "SPECIAL_DEFENSE",
    "accuracy": "ACCURACY", "evasion": "EVASION",
}

# combinações de +1/+1 que já existem como efeito próprio no FireRed
COMBOS_UP = {
    frozenset({"ATTACK", "DEFENSE"}): "EFFECT_BULK_UP",
    frozenset({"SPECIAL_ATTACK", "SPECIAL_DEFENSE"}): "EFFECT_CALM_MIND",
    frozenset({"ATTACK", "SPEED"}): "EFFECT_DRAGON_DANCE",
    frozenset({"DEFENSE", "SPECIAL_DEFENSE"}): "EFFECT_COSMIC_POWER",
}

ALVO_RHH = {
    "TARGET_SELECTED": "MOVE_TARGET_SELECTED",
    "TARGET_DEPENDS": "MOVE_TARGET_DEPENDS",
    "TARGET_USER": "MOVE_TARGET_USER",
    "TARGET_USER_OR_SELECTED": "MOVE_TARGET_USER_OR_SELECTED",
    "TARGET_RANDOM": "MOVE_TARGET_RANDOM",
    "TARGET_BOTH": "MOVE_TARGET_BOTH",
    "TARGET_ALL_OTHERS": "MOVE_TARGET_BOTH",
    "TARGET_FOES_AND_ALLY": "MOVE_TARGET_FOES_AND_ALLY",
    "TARGET_OPPONENTS_FIELD": "MOVE_TARGET_OPPONENTS_FIELD",
    "TARGET_USER_OR_ALLY": "MOVE_TARGET_USER",
    "TARGET_ALLY": "MOVE_TARGET_USER",
    "TARGET_SIDE": "MOVE_TARGET_USER",
}


# ------------------------------------------------------------------ parsing
def blocos_do_rhh(texto: str) -> dict[str, str]:
    """{MOVE_X: corpo} com casamento de chaves (aceita blocos aninhados).

    O regex `\\[(MOVE_\\w+)\\].*?\\n    \\}` usado antes estourava em golpes com
    chaves internas (MOVE_STONE_AXE, ADDITIONAL_EFFECTS) — daí o contador.
    """
    saida: dict[str, str] = {}
    for m in re.finditer(r"\[(MOVE_[A-Z0-9_]+)\]\s*=\s*\n\s*\{", texto):
        inicio = texto.index("{", m.end() - 1)
        prof, j = 0, inicio
        while j < len(texto):
            if texto[j] == "{":
                prof += 1
            elif texto[j] == "}":
                prof -= 1
                if prof == 0:
                    break
            j += 1
        saida[m.group(1)] = texto[inicio + 1:j]
    return saida


def campo(corpo: str, nome: str, padrao: str = "") -> str:
    m = re.search(r"\." + nome + r"\s*=\s*([^,\n]+)", corpo)
    return m.group(1).strip() if m else padrao


class Config:
    """Configuracao do RHH (`B_UPDATED_MOVE_DATA`, `GEN_x`) para resolver ternárias.

    O RHH escreve `.power = B_UPDATED_MOVE_DATA >= GEN_6 ? 90 : 70` e
    `.type = B_UPDATED_MOVE_TYPES >= GEN_CHAMPIONS ? TYPE_STEEL : TYPE_GRASS`.
    O padrão do RHH é `GEN_LATEST = GEN_9` (valor 8) e `GEN_CHAMPIONS = 9`, então
    `>= GEN_6` pega o primeiro ramo e `>= GEN_CHAMPIONS` pega o **segundo** —
    por isso não basta "pegar o primeiro ramo", tem que comparar de verdade.
    """

    def __init__(self, valores: dict[str, int]):
        self.valores = valores

    @classmethod
    def padrao(cls) -> "Config":
        valores = {f"GEN_{i}": i - 1 for i in range(1, 10)}
        valores["GEN_CHAMPIONS"] = 9
        valores["GEN_LATEST"] = 8
        valores["B_UPDATED_MOVE_DATA"] = 8
        valores["B_UPDATED_MOVE_TYPES"] = 8
        return cls(valores)

    @classmethod
    def do_rhh(cls, ref: Path) -> "Config":
        cfg = cls.padrao()
        for nome in ("include/config/general.h", "include/config/battle.h"):
            arq = ref / nome
            if not arq.exists():
                continue
            for chave, valor in re.findall(r"^#define\s+([A-Z0-9_]+)\s+(.+?)\s*(?://.*)?$",
                                           arq.read_text(errors="replace"), re.M):
                if chave in cfg.valores or chave.startswith("B_UPDATED_MOVE"):
                    avaliado = cfg._expr(valor)
                    if avaliado is not None:
                        cfg.valores[chave] = avaliado
        return cfg

    def _expr(self, expr: str) -> int | None:
        """Avalia uma expressão booleana/aritmética simples do RHH."""
        expr = expr.strip()
        while expr.startswith("(") and expr.endswith(")"):
            expr = expr[1:-1].strip()
        for op in ("||", "&&"):
            if op in expr:
                partes = [self._expr(p) for p in expr.split(op)]
                if any(v is None for v in partes):
                    return None
                return int(any(partes)) if op == "||" else int(all(partes))
        m = re.fullmatch(r"(\w+)\s*(>=|<=|==|!=|>|<)\s*(\w+)", expr)
        if m:
            a, b = self._nome(m.group(1)), self._nome(m.group(3))
            if a is None or b is None:
                return None
            return int({">=": a >= b, "<=": a <= b, "==": a == b,
                        "!=": a != b, ">": a > b, "<": a < b}[m.group(2)])
        return self._nome(expr)

    def _nome(self, token: str) -> int | None:
        token = token.strip()
        if token.isdigit():
            return int(token)
        if token in self.valores:
            return self.valores[token]
        m = re.fullmatch(r"(\w+)\s*([+-])\s*(\d+)", token)
        if m and m.group(1) in self.valores:
            base = self.valores[m.group(1)]
            return base + int(m.group(3)) if m.group(2) == "+" else base - int(m.group(3))
        return None

    def escolher(self, expr: str) -> str:
        """Resolve `COND ? A : B` com a configuração do RHH."""
        if "?" not in expr:
            return expr.strip()
        cond, resto = expr.split("?", 1)
        a, b = resto.rsplit(":", 1)
        resultado = self._expr(cond)
        if resultado is None:
            return a.strip()            # não deu para avaliar: ramo moderno
        return (a if resultado else b).strip()

    def numero(self, expr: str, padrao: int = 0) -> int:
        bruto = self.escolher(expr)
        m = re.fullmatch(r"\(?\s*(-?\d+)\s*\)?", bruto.strip())
        return int(m.group(1)) if m else padrao

    def simbolo(self, expr: str, padrao: str = "") -> str:
        bruto = self.escolher(expr).strip()
        return bruto if re.fullmatch(r"[A-Z][A-Z0-9_]*", bruto) else padrao


def texto_compound(corpo: str, nome: str) -> str:
    """Le `.nome = COMPOUND_STRING("a" "b")` e devolve o texto colado."""
    m = re.search(r"\." + nome + r"\s*=\s*COMPOUND_STRING\((.*?)\),\s*\n", corpo, re.S)
    if not m:
        return ""
    return "".join(re.findall(r'"([^"]*)"', m.group(1)))


def efeito_dos_stats(corpo: str, fisico: bool) -> str | None:
    """Deduz EFFECT_*STAT*_UP/DOWN a partir do bloco ADDITIONAL_EFFECTS."""
    m = re.search(r"\.additionalEffects = ADDITIONAL_EFFECTS\(\{(.*?)\}\)", corpo, re.S)
    if not m:
        return None
    bloco = m.group(1)
    sinal = "DOWN" if "STAT_CHANGE_EFFECT_MINUS" in bloco else "UP"
    alvos = []
    for chave, stat in STAT_PARA_EFEITO.items():
        v = re.search(r"\." + chave + r"\s*=\s*(\d+)", bloco)
        if v:
            alvos.append((stat, int(v.group(1))))
    if len(alvos) == 2 and sinal == "UP" and all(e == 1 for _, e in alvos):
        return COMBOS_UP.get(frozenset(s for s, _ in alvos))
    if len(alvos) != 1:
        return None
    stat, estagio = alvos[0]
    if estagio not in (1, 2):
        return None
    if fisico:
        # o FireRed só tem "baixar stat + dano" para os 7 stats; "subir" só
        # para ATTACK/DEFENSE (EFFECT_ALL_STATS_UP_HIT é exclusivo de AncientPower)
        if sinal == "DOWN":
            return f"EFFECT_{stat}_DOWN_HIT"
        if stat in ("ATTACK", "DEFENSE"):
            return f"EFFECT_{stat}_UP_HIT"
        return None
    sufixo = "_2" if estagio == 2 else ""
    return f"EFFECT_{stat}_{sinal}{sufixo}"


def escolher_efeito(corpo: str, efeitos_fre: set[str]) -> tuple[str, str]:
    """-> (efeito, como foi decidido). Sempre devolve um efeito que existe."""
    bruto = campo(corpo, "effect", "EFFECT_HIT")
    if bruto in efeitos_fre:
        return bruto, "direto"
    fisico = campo(corpo, "category", "DAMAGE_CATEGORY_STATUS") != "DAMAGE_CATEGORY_STATUS"
    if bruto == "EFFECT_STAT_CHANGE":
        efeito = efeito_dos_stats(corpo, fisico)
        if efeito and efeito in efeitos_fre:
            return efeito, "stat"
    if bruto == "EFFECT_FIXED_PERCENT_DAMAGE" and "damagePercentage = 50" in corpo:
        # Nature's Madness / Ruination = metade do HP atual = Super Fang
        if "EFFECT_SUPER_FANG" in efeitos_fre:
            return "EFFECT_SUPER_FANG", "equivalente"
    if bruto in MAPA_EFEITOS and MAPA_EFEITOS[bruto] in efeitos_fre:
        return MAPA_EFEITOS[bruto], "equivalente"
    if not fisico:
        return "EFFECT_SPLASH", "fallback-status"
    return "EFFECT_HIT", "fallback-dano"


# ------------------------------------------------------------- texto do GBA
def _sem_acento(texto: str) -> str:
    """O charmap do FireRed (inglês) não tem acento nem apóstrofo."""
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c))


def nome_para_gba(nome: str) -> str:
    """MAIÚSCULA, sem apóstrofo e com no máximo NOME_MAX colunas."""
    limpo = _sem_acento(nome.upper()).replace("'", "").replace("’", "")
    limpo = re.sub(r"[^A-Z0-9 \-.,!/?:()]", "", limpo)
    limpo = re.sub(r"\s+", " ", limpo).strip()
    return limpo[:NOME_MAX].rstrip()


def _limpar(texto: str) -> str:
    t = texto.replace("\\n", " ").replace("\\p", " ").replace("\\l", " ")
    t = _sem_acento(t.replace("'", "").replace("’", ""))
    t = re.sub(r"[^A-Za-z0-9 \-.,!:;?/()%+]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def descricao_para_gba(texto: str) -> str:
    """Quebra em até 4 linhas de 21 colunas, como as descrições originais."""
    palavras = _limpar(texto).split()
    linhas: list[str] = []
    atual = ""
    cortou = False
    for p in palavras:
        if not atual:
            atual = p[:LINHA_MAX]
        elif len(atual) + 1 + len(p) <= LINHA_MAX:
            atual += " " + p
        else:
            linhas.append(atual)
            if len(linhas) == LINHAS_MAX:
                cortou = True
                atual = ""
                break
            atual = p[:LINHA_MAX]
    if atual and len(linhas) < LINHAS_MAX:
        linhas.append(atual)
    if not linhas:
        linhas = ["No description."]
    if cortou and not linhas[-1].endswith((".", "!", "?")):
        linhas[-1] = linhas[-1][:LINHA_MAX - 1] + "."
    return "\\n".join(linhas)


# ------------------------------------------- IDs do RHH (enum, não #define)
def ids_do_rhh(ref: Path) -> dict[str, int]:
    """Avalia `enum Move` do RHH: incremento implícito + constantes GENx.

    O RHH declara os golpes em `enum`, com `MOVE_ROOST = MOVES_COUNT_GEN3` e
    sentinelas no meio (`MOVES_COUNT_GEN1`). Sem avaliar isso, 5 golpes ficam
    sem ID e os aliases (`MOVE_VISE_GRIP = MOVE_VICE_GRIP`) colidem.
    """
    texto = (ref / "include/constants/moves.h").read_text()
    corpo = texto[texto.index("enum __attribute__((packed)) Move"):]
    corpo = corpo[corpo.index("{") + 1:corpo.index("};")]
    corpo = re.sub(r"//[^\n]*", "", corpo)
    ids: dict[str, int] = {}
    atual = 0
    for item in (x.strip() for x in corpo.split(",")):
        if not item:
            continue
        if "=" in item:
            nome, rhs = (p.strip() for p in item.split("=", 1))
            if rhs.isdigit():
                valor = int(rhs)
            elif rhs in ids:
                valor = ids[rhs]
            else:
                continue        # constante desconhecida: não inventa ID
        else:
            nome, valor = item, atual
        ids[nome] = valor
        atual = valor + 1
    return ids


def ordem_do_rhh(ref: Path) -> list[str]:
    """Nomes canônicos em ordem de ID (o primeiro nome de cada ID vence)."""
    por_id: dict[int, str] = {}
    for nome, i in ids_do_rhh(ref).items():
        if nome.startswith("MOVE_"):     # MOVES_COUNT_GENx / LAST_MAX_MOVE fora
            por_id.setdefault(i, nome)
    return [por_id[i] for i in sorted(por_id)]


def efeitos_do_firered(poke: Path) -> set[str]:
    txt = (poke / "include/constants/battle_move_effects.h").read_text()
    return set(re.findall(r"^\s*#define\s+(EFFECT_\w+)", txt, re.M))


def golpes_existentes(poke: Path) -> dict[str, int]:
    """IDs do FireRed **original** (0-354).

    Descarta o bloco da E4 antes de ler: se a lista de "golpes novos" fosse
    calculada sobre um moves.h ja' aplicado, ela viria vazia e o `--write`
    apagaria os 442 golpes (foi o que aconteceu no primeiro `--write` repetido).
    """
    txt = sem_bloco((poke / "include/constants/moves.h").read_text())
    return {n: int(v) for n, v in re.findall(r"^#define (MOVE_[A-Z0-9_]+) (\d+)$", txt, re.M)}


def golpes_dos_learnsets(ref: Path) -> set[str]:
    usados: set[str] = set()
    for arq in (ref / "src/data/pokemon/level_up_learnsets").glob("*.h"):
        usados |= set(re.findall(r"LEVEL_UP_MOVE\(\s*\d+\s*,\s*(MOVE_[A-Z0-9_]+)\s*\)",
                                 arq.read_text(errors="replace")))
    return usados


def alias_e3() -> dict[str, str]:
    """`ALIAS_GOLPE` da E3: {nome antigo do FireRed: nome moderno do RHH}."""
    sys.path.insert(0, str(AQUI))
    import apply_e3_port
    return apply_e3_port.ALIAS_GOLPE


def classificar(ref: Path, existentes: dict[str, int]) -> tuple[list[str], list[tuple[str, str]]]:
    """-> (golpes realmente novos, [(nome RHH, nome FireRed)] só renomeados)."""
    usados = golpes_dos_learnsets(ref)
    antigos = {novo: velho for velho, novo in alias_e3().items()}
    novos, aliases = [], []
    for nome in ordem_do_rhh(ref):
        if nome not in usados:
            continue
        if nome in existentes:
            continue
        if nome in antigos and antigos[nome] in existentes:
            aliases.append((nome, antigos[nome]))
        else:
            novos.append(nome)
    return novos, aliases


def dados_do_golpe(corpo: str, efeitos: set[str], move: str,
                   cfg: Config | None = None) -> dict:
    cfg = cfg or Config.padrao()
    efeito, como = escolher_efeito(corpo, efeitos)
    alvo = ALVO_RHH.get(campo(corpo, "target", "TARGET_SELECTED"), "MOVE_TARGET_SELECTED")
    flags = []
    if "TRUE" in campo(corpo, "makesContact"):
        flags.append("FLAG_MAKES_CONTACT")
    if "TRUE" not in campo(corpo, "ignoresProtect"):
        flags.append("FLAG_PROTECT_AFFECTED")
    if "TRUE" in campo(corpo, "magicCoatAffected"):
        flags.append("FLAG_MAGIC_COAT_AFFECTED")
    if "TRUE" in campo(corpo, "snatchAffected"):
        flags.append("FLAG_SNATCH_AFFECTED")
    if "TRUE" not in campo(corpo, "mirrorMoveBanned"):
        flags.append("FLAG_MIRROR_MOVE_AFFECTED")
    if "TRUE" not in campo(corpo, "ignoresKingsRock"):
        flags.append("FLAG_KINGS_ROCK_AFFECTED")
    poder = cfg.numero(campo(corpo, "power", "0"), 0)
    return {
        "move": move,
        "nome": nome_para_gba(texto_compound(corpo, "name") or move[5:].replace("_", " ")),
        "descricao": descricao_para_gba(texto_compound(corpo, "description")),
        "efeito": efeito,
        "como": como,
        "poder": min(poder, PODER_MAX),
        "poder_bruto": poder,
        "tipo": cfg.simbolo(campo(corpo, "type", "TYPE_NORMAL"), "TYPE_NORMAL"),
        "precisao": cfg.numero(campo(corpo, "accuracy", "0"), 0),
        "pp": max(1, min(255, cfg.numero(campo(corpo, "pp", "10"), 10))),
        "alvo": alvo,
        "prioridade": max(-128, min(127, cfg.numero(campo(corpo, "priority", "0"), 0))),
        "categoria": campo(corpo, "category", "DAMAGE_CATEGORY_STATUS"),
        "flags": flags,
    }


def montar_tudo(poke: Path, ref: Path) -> dict:
    efeitos = efeitos_do_firered(poke)
    existentes = golpes_existentes(poke)
    novos, aliases = classificar(ref, existentes)
    corpos = blocos_do_rhh((ref / "src/data/moves_info.h").read_text(errors="replace"))
    cfg = Config.do_rhh(ref)
    base = max(existentes.values()) + 1
    golpes = []
    for i, move in enumerate(novos, start=base):
        if move not in corpos:
            raise SystemExit(f"{move} nao esta em moves_info.h")
        d = dados_do_golpe(corpos[move], efeitos, move, cfg)
        d["id"] = i
        golpes.append(d)
    relatorio = {"novos": len(novos), "total": base + len(novos),
                 "aliases": len(aliases)}
    for chave in ("direto", "stat", "equivalente", "fallback-dano", "fallback-status"):
        relatorio[chave] = sum(1 for g in golpes if g["como"] == chave)
    relatorio["poder_estourado"] = [g["move"] for g in golpes if g["poder_bruto"] > PODER_MAX]
    return {"golpes": golpes, "relatorio": relatorio, "existentes": existentes,
            "aliases": aliases}


# --------------------------------------------------------------- escrita
def sem_bloco(texto: str) -> str:
    """Remove um bloco anterior `// E4: inicio` ... `// E4: fim`."""
    return re.sub(r"\n?" + re.escape(MARCA) + r" inicio.*?" + re.escape(MARCA) +
                  r" fim\n?", "\n", texto, flags=re.S)


def aplicar_nome_longo(poke: Path) -> str:
    p = poke / "include/constants/global.h"
    s = p.read_text()
    s2 = re.sub(r"#define MOVE_NAME_LENGTH \d+", f"#define MOVE_NAME_LENGTH {NOME_MAX}", s)
    if s2 != s:
        p.write_text(s2)
        return f"global.h: MOVE_NAME_LENGTH {NOME_MAX}"
    return "global.h: ja em MOVE_NAME_LENGTH " + str(NOME_MAX)


def aplicar_constantes(poke: Path, dados: dict) -> str:
    p = poke / "include/constants/moves.h"
    s = sem_bloco(p.read_text())
    total = dados["relatorio"]["total"]
    linhas = [f"{MARCA} inicio — golpes das Gen 4-9 (gerado por gen_move_data.py)",
              "// IDs 0-354 sao os do FireRed original e nao mudam."]
    linhas += [f"#define {g['move']} {g['id']}" for g in dados["golpes"]]
    if dados["aliases"]:
        linhas.append("// nomes antigos do FireRed -> mesmo golpe (Gen 3 renomeou)")
        linhas += [f"#define {novo} {velho}" for novo, velho in dados["aliases"]]
    linhas.append(f"{MARCA} fim")
    s = re.sub(r"#define MOVES_COUNT \d+",
               "\n".join(linhas) + f"\n\n#define MOVES_COUNT {total}", s, count=1)
    p.write_text(s)
    return f"moves.h: {len(dados['golpes'])} golpes novos, {len(dados['aliases'])} aliases, MOVES_COUNT {total}"


def aplicar_battle_moves(poke: Path, dados: dict) -> str:
    p = poke / "src/data/battle_moves.h"
    s = sem_bloco(p.read_text())
    linhas = [f"    {MARCA} inicio — golpes das Gen 4-9 (gerado por gen_move_data.py)"]
    for g in dados["golpes"]:
        flags = " | ".join(g["flags"]) if g["flags"] else "0"
        linhas += [
            f"    [{g['move']}] =",
            "    {",
            f"        .effect = {g['efeito']},",
            f"        .power = {g['poder']},",
            f"        .type = {g['tipo']},",
            f"        .accuracy = {g['precisao']},",
            f"        .pp = {g['pp']},",
            "        .secondaryEffectChance = 0,",
            f"        .target = {g['alvo']},",
            f"        .priority = {g['prioridade']},",
            f"        .flags = {flags},",
            "    },",
        ]
    linhas.append(f"    {MARCA} fim")
    fim = s.rindex("};")
    s = s[:fim] + "\n".join(linhas) + "\n" + s[fim:]
    p.write_text(s)
    return f"battle_moves.h: +{len(dados['golpes'])} entradas"


def aplicar_nomes(poke: Path, dados: dict) -> str:
    p = poke / "src/data/text/move_names.h"
    antigos = re.findall(r'\[(MOVE_[A-Z0-9_]+)\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\)',
                         p.read_text())
    linhas = ["const u8 gMoveNames[MOVES_COUNT][MOVE_NAME_LENGTH + 1] = {",
              f"    {MARCA} inicio — regerado por gen_move_data.py"]
    linhas += [f'    [{m}] = _("{n}"),' for m, n in antigos]
    linhas += [f'    [{g["move"]}] = _("{g["nome"]}"),' for g in dados["golpes"]]
    linhas += [f"    {MARCA} fim", "};", ""]
    p.write_text("\n".join(linhas))
    return f"move_names.h: {len(antigos)} originais + {len(dados['golpes'])} novos"


def aplicar_descricoes(poke: Path, dados: dict) -> str:
    p = poke / "src/move_descriptions.c"
    s = sem_bloco(p.read_text())
    strs, ptrs = [], []
    for g in dados["golpes"]:
        ident = "gMoveDescription_E4_" + g["move"][5:].title().replace("_", "")
        strs.append(f'const u8 {ident}[] = _("{g["descricao"]}");')
        ptrs.append(f"    [{g['move']} - 1] = {ident},")
    bloco_str = (f"{MARCA} inicio — descricoes das Gen 4-9 (gerado por gen_move_data.py)\n"
                 + "\n".join(strs) + f"\n{MARCA} fim")
    i = s.index("const u8 *const gMoveDescriptionPointers")
    s = s[:i] + bloco_str + "\n\n" + s[i:]
    fim = s.rindex("};")
    bloco_ptr = (f"    {MARCA} inicio — ponteiros das Gen 4-9\n"
                 + "\n".join(ptrs) + f"\n    {MARCA} fim\n")
    s = s[:fim] + bloco_ptr + s[fim:]
    p.write_text(s)
    return f"move_descriptions.c: +{len(dados['golpes'])} descrições"


def aplicar_animacoes(poke: Path, dados: dict) -> str:
    """Completa `gBattleAnims_Moves` (tabela em assembly) ate o ultimo golpe.

    Sem isso, `LaunchBattleAnimation(gBattleAnims_Moves, move, TRUE)` le um
    ponteiro **fora da tabela** para qualquer golpe novo e o jogo executa um
    script de animacao aleatorio — foi o que travou a primeira batalha da E4.
    Todos os golpes novos usam a animacao generica de TACKLE (impacto + shake).
    """
    p = poke / "data/battle_anim_scripts.s"
    s = p.read_text()
    s = re.sub(r"\n?@ E4: inicio.*?@ E4: fim\n?", "\n", s, flags=re.S)
    inicio = s.index("gBattleAnims_Moves::")
    corpo = s.index("\n", inicio) + 1          # depois do rotulo, nunca no meio dele
    prox = re.search(r"^\w+::$", s[corpo:], re.M)
    fim = corpo + prox.start() if prox else len(s)
    ultimo = None
    for m in re.finditer(r"^\t\.4byte Move_\w+$", s[inicio:fim], re.M):
        ultimo = inicio + m.end()
    if ultimo is None:
        raise SystemExit("gBattleAnims_Moves sem entradas .4byte Move_*")
    bloco = ("\n@ E4: inicio — golpes das Gen 4-9 (animacao generica de TACKLE)\n"
             + "\n".join("\t.4byte Move_TACKLE" for _ in dados["golpes"])
             + "\n@ E4: fim")
    s = s[:ultimo] + bloco + s[ultimo:]
    p.write_text(s)
    return f"battle_anim_scripts.s: +{len(dados['golpes'])} animacoes (TACKLE)"


def aplicar(poke: Path, ref: Path) -> list[str]:
    dados = montar_tudo(poke, ref)
    mudancas = [
        aplicar_nome_longo(poke),
        aplicar_constantes(poke, dados),
        aplicar_battle_moves(poke, dados),
        aplicar_nomes(poke, dados),
        aplicar_descricoes(poke, dados),
        aplicar_animacoes(poke, dados),
    ]
    # categorias (físico/especial) — mesmo gerador da E3, agora com 801 golpes
    sys.path.insert(0, str(AQUI))
    import apply_e3_port
    destino = poke / "src/data/battle_moves_category.h"
    conteudo = apply_e3_port.gerar_categorias(poke, ref)
    if not destino.exists() or destino.read_text() != conteudo:
        destino.write_text(conteudo)
        mudancas.append("battle_moves_category.h regerada (todos os golpes)")
    return mudancas


# ------------------------------------------------------------ verificação
def verificar(poke: Path, originais: int = 355) -> list[str]:
    problemas: list[str] = []
    const = (poke / "include/constants/moves.h").read_text()
    battle = (poke / "src/data/battle_moves.h").read_text()
    nomes = (poke / "src/data/text/move_names.h").read_text()
    desc = (poke / "src/move_descriptions.c").read_text()
    cats = (poke / "src/data/battle_moves_category.h").read_text()
    total = int(re.search(r"#define MOVES_COUNT (\d+)", const).group(1))
    ids = {n: int(v) for n, v in re.findall(r"^#define (MOVE_[A-Z0-9_]+) (\d+)$", const, re.M)}
    if sorted(ids.values()) != list(range(total)):
        problemas.append(f"IDs de golpe nao sao 0..{total - 1} sem buracos ({len(ids)} defines)")
    for move, i in ids.items():
        if f"[{move}] =" not in battle:
            problemas.append(f"battle_moves.h sem {move}")
        if f"[{move}]" not in nomes:
            problemas.append(f"move_names.h sem {move}")
        if i >= originais and f"[{move} - 1]" not in desc:
            problemas.append(f"move_descriptions sem {move}")
        if f"[{move}]" not in cats:
            problemas.append(f"categorias sem {move}")
        if len(problemas) > 12:
            problemas.append("(parando: muitos problemas)")
            break
    # um identificador por descrição nova: `MOVE_A_B` e `MOVE_AB` colidiriam
    identificadores = re.findall(r"const u8 (gMoveDescription_E4_\w+)\[\]", desc)
    repetidos = {i for i in identificadores if identificadores.count(i) > 1}
    if repetidos:
        problemas.append(f"identificadores de descrição repetidos: {sorted(repetidos)[:3]}")
    if len(identificadores) != total - originais:
        problemas.append(f"{len(identificadores)} descrições novas, esperava {total - originais}")
    asm = (poke / "data/battle_anim_scripts.s").read_text()
    inicio = asm.index("gBattleAnims_Moves::")
    corpo = asm.index("\n", inicio) + 1
    prox = re.search(r"^\w+::$", asm[corpo:], re.M)
    trecho = asm[inicio:corpo + prox.start() if prox else len(asm)]
    animacoes = len(re.findall(r"^\t\.4byte Move_\w+$", trecho, re.M))
    if animacoes != total:
        problemas.append(f"gBattleAnims_Moves com {animacoes} animacoes, esperava {total}")
    if "#define MOVE_NAME_LENGTH 16" not in (poke / "include/constants/global.h").read_text():
        problemas.append("MOVE_NAME_LENGTH diferente de 16")
    return problemas


# --------------------------------------------------------------- self-test
def self_test() -> int:
    """Testa parser, numeração do enum, mapeamento de efeito e textos."""
    ref_txt = '''
enum __attribute__((packed)) Move
{
    MOVE_NONE = 0,
    MOVE_POUND = 1,
    MOVE_DOUBLE_SLAP = 3,
    MOVE_DOUBLESLAP = MOVE_DOUBLE_SLAP, // Pre-Gen VI name
    MOVES_COUNT_GEN3,
    MOVE_TESTE_HIT = MOVES_COUNT_GEN3,
    MOVE_TESTE_DOWN,
};

const struct MoveInfo gMovesInfo[] = {
    [MOVE_TESTE_HIT] =
    {
        .name = COMPOUND_STRING("Test Hit"),
        .description = COMPOUND_STRING(
            "Hits the foe\\n"
            "really hard."),
        .effect = EFFECT_HIT,
        .power = B_UPDATED_MOVE_DATA >= GEN_6 ? 60 : 40,
        .type = TYPE_FAIRY,
        .accuracy = 100,
        .pp = 15,
        .target = TARGET_SELECTED,
        .priority = 0,
        .category = DAMAGE_CATEGORY_PHYSICAL,
        .makesContact = TRUE,
        .mirrorMoveBanned = TRUE,
        .ignoresKingsRock = TRUE,
    },

    [MOVE_TESTE_DOWN] =
    {
        .name = COMPOUND_STRING("Test Down"),
        .description = COMPOUND_STRING("Lowers the foe's Defense."),
        .effect = EFFECT_STAT_CHANGE,
        .power = 0,
        .type = TYPE_NORMAL,
        .accuracy = 100,
        .pp = 20,
        .target = TARGET_SELECTED,
        .priority = 0,
        .category = DAMAGE_CATEGORY_STATUS,
        .additionalEffects = ADDITIONAL_EFFECTS({
            .moveEffect = STAT_CHANGE_EFFECT_MINUS,
            .defense = 1,
        }),
    },

    [MOVE_TESTE_RARO] =
    {
        .name = COMPOUND_STRING("Test Rare"),
        .description = COMPOUND_STRING(
            "An effect the FireRed\\n"
            "does not have at all, in any way, shape or form."),
        .effect = EFFECT_TERRAIN,
        .power = 0,
        .type = TYPE_PSYCHIC,
        .accuracy = 0,
        .pp = 10,
        .target = TARGET_ALL_OTHERS,
        .priority = -1,
        .category = DAMAGE_CATEGORY_STATUS,
    },
};
'''
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    (tmp / "include/constants").mkdir(parents=True)
    (tmp / "include/constants/moves.h").write_text(ref_txt)

    # 1) enum: incremento implícito, sentinela e alias resolvem para o mesmo ID
    ids = ids_do_rhh(tmp)
    assert ids["MOVE_DOUBLE_SLAP"] == 3 and ids["MOVE_DOUBLESLAP"] == 3, ids
    assert ids["MOVES_COUNT_GEN3"] == 4, ids          # sentinela pegou o 4
    assert ids["MOVE_TESTE_HIT"] == 4, ids            # primeiro da Gen 4
    assert ids["MOVE_TESTE_DOWN"] == 5, ids           # implícito +1
    assert ordem_do_rhh(tmp)[:3] == ["MOVE_NONE", "MOVE_POUND", "MOVE_DOUBLE_SLAP"], ordem_do_rhh(tmp)

    corpos = blocos_do_rhh(ref_txt)
    assert len(corpos) == 3, corpos.keys()            # não engoliu chaves do ADDITIONAL_EFFECTS

    efeitos = {"EFFECT_HIT", "EFFECT_DEFENSE_DOWN", "EFFECT_RAZOR_WIND",
               "EFFECT_SPLASH", "EFFECT_ATTACK_DOWN_HIT", "EFFECT_COUNTER", "EFFECT_FAKE_OUT"}

    a = dados_do_golpe(corpos["MOVE_TESTE_HIT"], efeitos, "MOVE_TESTE_HIT")
    assert a["efeito"] == "EFFECT_HIT" and a["como"] == "direto", a
    assert a["nome"] == "TEST HIT", a["nome"]
    assert a["poder"] == 60 and a["tipo"] == "TYPE_FAIRY" and a["pp"] == 15, a
    assert "FLAG_MAKES_CONTACT" in a["flags"] and "FLAG_PROTECT_AFFECTED" in a["flags"]
    assert "FLAG_MIRROR_MOVE_AFFECTED" not in a["flags"], a["flags"]
    assert "FLAG_KINGS_ROCK_AFFECTED" not in a["flags"], a["flags"]

    b = dados_do_golpe(corpos["MOVE_TESTE_DOWN"], efeitos, "MOVE_TESTE_DOWN")
    assert b["efeito"] == "EFFECT_DEFENSE_DOWN" and b["como"] == "stat", b
    assert b["alvo"] == "MOVE_TARGET_SELECTED"

    c = dados_do_golpe(corpos["MOVE_TESTE_RARO"], efeitos, "MOVE_TESTE_RARO")
    assert c["efeito"] == "EFFECT_SPLASH" and c["como"] == "fallback-status", c
    assert c["alvo"] == "MOVE_TARGET_BOTH" and c["prioridade"] == -1, c

    # fallback de dano: efeito desconhecido em golpe com categoria de dano
    corpo_dano = corpos["MOVE_TESTE_RARO"].replace(
        "DAMAGE_CATEGORY_STATUS", "DAMAGE_CATEGORY_SPECIAL").replace(".power = 0", ".power = 90")
    d = dados_do_golpe(corpo_dano, efeitos, "MOVE_TESTE_RARO")
    assert d["efeito"] == "EFFECT_HIT" and d["como"] == "fallback-dano", d

    # RHH escreve .spAtk/.spDef; +1/+1 de dois stats vira efeito composto do Gen 3
    assert efeito_dos_stats(".additionalEffects = ADDITIONAL_EFFECTS({\n"
                            "    .moveEffect = STAT_CHANGE_EFFECT_PLUS,\n"
                            "    .spAtk = 2,\n})", False) == "EFFECT_SPECIAL_ATTACK_UP_2"
    assert efeito_dos_stats(".additionalEffects = ADDITIONAL_EFFECTS({\n"
                            "    .moveEffect = STAT_CHANGE_EFFECT_PLUS,\n"
                            "    .attack = 1, .defense = 1,\n})", False) == "EFFECT_BULK_UP"
    assert efeito_dos_stats(".additionalEffects = ADDITIONAL_EFFECTS({\n"
                            "    .moveEffect = STAT_CHANGE_EFFECT_PLUS,\n"
                            "    .attack = 1, .spAtk = 1,\n})", False) is None
    assert escolher_efeito(".effect = EFFECT_ROOST,", efeitos) == ("EFFECT_RESTORE_HP", "equivalente") \
        if "EFFECT_RESTORE_HP" in efeitos else True
    efeitos_reais = efeitos | {"EFFECT_RESTORE_HP", "EFFECT_SUPER_FANG"}
    assert escolher_efeito(".effect = EFFECT_ROOST, .category = DAMAGE_CATEGORY_STATUS",
                           efeitos_reais) == ("EFFECT_RESTORE_HP", "equivalente")
    assert escolher_efeito(".effect = EFFECT_FIXED_PERCENT_DAMAGE, "
                           ".category = DAMAGE_CATEGORY_SPECIAL, "
                           ".argument = { .damagePercentage = 50 },",
                           efeitos_reais) == ("EFFECT_SUPER_FANG", "equivalente")
    assert escolher_efeito(".effect = EFFECT_FIXED_PERCENT_DAMAGE, "
                           ".category = DAMAGE_CATEGORY_SPECIAL, "
                           ".argument = { .damagePercentage = 20 },",
                           efeitos_reais) == ("EFFECT_HIT", "fallback-dano")

    # ternárias: compara de verdade (GEN_CHAMPIONS=9 > GEN_LATEST=8 -> segundo ramo)
    cfg = Config.padrao()
    assert cfg.numero("B_UPDATED_MOVE_DATA >= GEN_6 ? 90 : 70") == 90
    assert cfg.numero("B_UPDATED_MOVE_DATA >= GEN_CHAMPIONS ? 130 : 120") == 120
    assert cfg.numero("B_UPDATED_MOVE_DATA >= GEN_CHAMPIONS ? 130 : 120", 0) == 120
    assert cfg.simbolo("B_UPDATED_MOVE_TYPES >= GEN_CHAMPIONS ? TYPE_STEEL : TYPE_GRASS") == "TYPE_GRASS"
    assert cfg.simbolo("B_UPDATED_MOVE_TYPES >= GEN_4 ? TYPE_FAIRY : TYPE_NORMAL") == "TYPE_FAIRY"
    assert cfg.numero("-1") == -1 and cfg.numero("(B_UPDATED_MOVE_DATA >= GEN_2 || B_UPDATED_MOVE_DATA == GEN_2) ? 85 : 80") == 85
    # configuração desconhecida: fica com o ramo moderno (o primeiro)
    assert cfg.numero("B_HIDDEN_POWER_DMG >= GEN_6 ? 60 : 70") == 60
    # poder acima de 255 é cortado (o campo do FireRed é u8)
    assert dados_do_golpe(".power = 300, .category = DAMAGE_CATEGORY_PHYSICAL",
                          efeitos, "MOVE_X")["poder"] == 255

    # nomes: maiúscula, apóstrofo removido (não existe no charmap), corte em 16
    assert nome_para_gba("King's Shield") == "KINGS SHIELD"
    assert nome_para_gba("Collision Course") == "COLLISION COURSE"
    assert nome_para_gba("Trick-or-Treat") == "TRICK-OR-TREAT"
    assert nome_para_gba("Pokémon Café") == "POKEMON CAFE"
    assert len(nome_para_gba("A" * 30)) == NOME_MAX

    # descrições: ≤ 4 linhas, ≤ 21 colunas, sem apóstrofo/barra invertida
    for texto in ("Short one.", "A " * 60, "", "It lowers the foe's Sp. Def. a lot"):
        d = descricao_para_gba(texto)
        linhas = d.split("\\n")
        assert 1 <= len(linhas) <= LINHAS_MAX, (texto, d)
        assert all(len(l) <= LINHA_MAX for l in linhas), (texto, d)
        assert "\\" not in d.replace("\\n", "") and "'" not in d, d
    assert descricao_para_gba("Hits the foe\\nhard.") == "Hits the foe hard."
    assert descricao_para_gba("Hits the foe\\nreally hard.") == "Hits the foe really\\nhard."
    assert len(descricao_para_gba("word " * 40).split("\\n")) == LINHAS_MAX

    # 7) tabela de animacoes em assembly: insere no fim de gBattleAnims_Moves
    tmp2 = Path(tempfile.mkdtemp())
    (tmp2 / "data").mkdir()
    tab = "\t"      # o .s de verdade usa TAB, nao espacos
    (tmp2 / "data/battle_anim_scripts.s").write_text(
        f"{tab}.align 2\ngBattleAnims_Moves::\n{tab}.4byte Move_NONE\n"
        f"{tab}.4byte Move_POUND\n\n{tab}.align 2\ngBattleAnims_Statuses::\n"
        f"{tab}.4byte Status_SLEEP\n")
    dados = {"golpes": [{"move": "MOVE_A"}, {"move": "MOVE_B"}]}
    assert aplicar_animacoes(tmp2, dados).startswith("battle_anim_scripts.s: +2")
    texto = (tmp2 / "data/battle_anim_scripts.s").read_text()
    tabela = texto[texto.index("gBattleAnims_Moves::"):texto.index("gBattleAnims_Statuses::")]
    assert tabela.count(".4byte Move_") == 4, tabela
    assert tabela.count("Move_TACKLE") == 2, tabela
    # idempotente: aplicar de novo nao duplica
    aplicar_animacoes(tmp2, dados)
    texto2 = (tmp2 / "data/battle_anim_scripts.s").read_text()
    assert texto2.count("Move_TACKLE") == 2, texto2

    # 8) idempotencia: aplicar duas vezes no mesmo clone nao pode apagar nada
    raiz = Path(tempfile.mkdtemp())
    poke2, ref2 = raiz / "poke", raiz / "ref"
    for d in ("include/constants", "src/data/text", "src/data/pokemon/level_up_learnsets"):
        (poke2 / d).mkdir(parents=True)
        (ref2 / d).mkdir(parents=True)
    (poke2 / "include/constants/moves.h").write_text(
        "#define MOVE_NONE 0\n#define MOVE_POUND 1\n\n#define MOVES_COUNT 2\n")
    (poke2 / "include/constants/battle_move_effects.h").write_text(
        "#define EFFECT_HIT 0\n#define EFFECT_SPLASH 1\n#define EFFECT_ATTACK_DOWN 2\n")
    (poke2 / "include/constants/global.h").write_text("#define MOVE_NAME_LENGTH 12\n")
    (poke2 / "src/data/battle_moves.h").write_text(
        "const struct BattleMove gBattleMoves[MOVES_COUNT] =\n{\n"
        "    [MOVE_NONE] =\n    {\n        .power = 0,\n        .type = TYPE_MYSTERY,\n    },\n"
        "    [MOVE_POUND] =\n    {\n        .power = 40,\n        .type = TYPE_NORMAL,\n    },\n};\n")
    (poke2 / "src/data/text/move_names.h").write_text(
        'const u8 gMoveNames[MOVES_COUNT][MOVE_NAME_LENGTH + 1] = {\n'
        '    [MOVE_NONE] = _("$"),\n    [MOVE_POUND] = _("POUND"),\n};\n')
    (poke2 / "src/move_descriptions.c").write_text(
        'const u8 gMoveDescription_Pound[] = _("Pounds the foe.");\n\n'
        "const u8 *const gMoveDescriptionPointers[MOVES_COUNT - 1] =\n{\n"
        "    gMoveDescription_Pound,\n};\n")
    (ref2 / "include/constants/moves.h").write_text(
        "enum __attribute__((packed)) Move\n{\n    MOVE_NONE = 0,\n    MOVE_POUND = 1,\n"
        "    MOVES_COUNT_GEN3,\n    MOVE_NOVO_A = MOVES_COUNT_GEN3,\n    MOVE_NOVO_B,\n};\n")
    (ref2 / "include/config").mkdir(parents=True)
    tab = "\t"
    (poke2 / "data").mkdir()
    (poke2 / "data/battle_anim_scripts.s").write_text(
        f"{tab}.align 2\ngBattleAnims_Moves::\n{tab}.4byte Move_NONE\n{tab}.4byte Move_POUND\n\n"
        f"gBattleAnims_Statuses::\n{tab}.4byte Status_SLEEP\n")
    (ref2 / "src/data/pokemon/level_up_learnsets/gen_1.h").write_text(
        "LEVEL_UP_MOVE(1, MOVE_POUND), LEVEL_UP_MOVE(9, MOVE_NOVO_A), "
        "LEVEL_UP_MOVE(9, MOVE_NOVO_B)")
    (ref2 / "src/data/moves_info.h").write_text(
        "const struct MoveInfo gMovesInfo[] = {\n"
        "    [MOVE_NOVO_A] =\n    {\n        .name = COMPOUND_STRING(\"New A\"),\n"
        "        .description = COMPOUND_STRING(\"Does a thing.\"),\n"
        "        .effect = EFFECT_HIT,\n        .power = 70,\n        .type = TYPE_FIRE,\n"
        "        .accuracy = 100,\n        .pp = 10,\n        .target = TARGET_SELECTED,\n"
        "        .priority = 0,\n        .category = DAMAGE_CATEGORY_PHYSICAL,\n    },\n"
        "    [MOVE_NOVO_B] =\n    {\n        .name = COMPOUND_STRING(\"New B\"),\n"
        "        .description = COMPOUND_STRING(\"Lowers the foes Attack.\"),\n"
        "        .effect = EFFECT_STAT_CHANGE,\n        .power = 0,\n"
        "        .type = TYPE_NORMAL,\n        .accuracy = 100,\n        .pp = 20,\n"
        "        .target = TARGET_SELECTED,\n        .priority = 0,\n"
        "        .category = DAMAGE_CATEGORY_STATUS,\n"
        "        .additionalEffects = ADDITIONAL_EFFECTS({\n"
        "            .moveEffect = STAT_CHANGE_EFFECT_MINUS,\n            .attack = 1,\n"
        "        }),\n    },\n};\n")

    primeira = montar_tudo(poke2, ref2)["relatorio"]
    assert primeira["novos"] == 2 and primeira["total"] == 4, primeira
    aplicar(poke2, ref2)
    depois_do_primeiro = (poke2 / "include/constants/moves.h").read_text()
    assert "#define MOVE_NOVO_A 2" in depois_do_primeiro, depois_do_primeiro
    assert "#define MOVES_COUNT 4" in depois_do_primeiro, depois_do_primeiro
    # segunda passada: nao pode virar "0 novos" nem apagar os blocos
    segunda = montar_tudo(poke2, ref2)["relatorio"]
    assert segunda["novos"] == 2, segunda
    aplicar(poke2, ref2)
    final = (poke2 / "include/constants/moves.h").read_text()
    assert final.count("MOVE_NOVO_A") == 1 and "#define MOVES_COUNT 4" in final, final
    assert verificar(poke2, originais=2) == [], verificar(poke2, originais=2)

    print(f"self-test ok: enum (aliases/incremento), efeito direto/stat/fallback, "
          f"corte de poder, nomes ≤{NOME_MAX}, descrições {LINHAS_MAX}x{LINHA_MAX} "
          "e animações")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--reference", default="/tmp/fre")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    poke, ref = Path(a.pokefirered), Path(a.reference)
    if a.check:
        problemas = verificar(poke)
        if problemas:
            print("dados dos golpes INCONSISTENTES:")
            for p in problemas:
                print("  -", p)
            return 1
        dados = montar_tudo(poke, ref)
        r = dados["relatorio"]
        print(f"ok: {r['total']} golpes ({len(dados['existentes'])} originais + "
              f"{r['novos']} novos), todos com dados, nome, descrição e categoria")
        return 0

    dados = montar_tudo(poke, ref)
    if not a.write:
        print(f"simulação: {dados['relatorio']}")
        return 0
    for m in aplicar(poke, ref):
        print("aplicado:", m)
    print("relatório:", dados["relatorio"])
    problemas = verificar(poke)
    if problemas:
        for p in problemas:
            print("FALTA:", p)
        return 1
    print("dados dos golpes aplicados e conferidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
