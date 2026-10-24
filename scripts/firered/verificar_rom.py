#!/usr/bin/env python3
"""Confere os dados da E2 **no ROM compilado**, não no código-fonte.

Por que isso existe
-------------------
`make` sai com código 0 mesmo quando uma tabela entra deslocada: o compilador
não sabe que `gSpeciesInfo[387]` deveria ser o TURTWIG. Na E1 o mesmo tipo de
erro passou batido (`s1_seen2` medido no ROM era 0x3A64, não o 0x39C4 do
compilador de teste). Então esta etapa lê a ROM final, encontra os símbolos no
`.map` e compara byte a byte com o que o gerador escreveu.

O que é conferido
-----------------
| tabela             | comparação                                              |
|--------------------|---------------------------------------------------------|
| `gSpeciesInfo`     | stats, tipos, catch rate, exp yield de todas as espécies |
| `gPokedexEntries`  | categoria (texto do charmap), altura, peso, ponteiro     |
| `gEvolutionTable`  | primeira evolução (método, parâmetro, alvo)              |
| `gLevelUpLearnsets`| primeiros golpes por nível de cada espécie               |

Uso
---
    python3 scripts/firered/verificar_rom.py --pokefirered /tmp/pokefirered
    python3 scripts/firered/verificar_rom.py --amostras 40 --json
    python3 scripts/firered/verificar_rom.py --self-test      # sem ROM

Sai com código 1 se qualquer valor divergir.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts" / "firered"))

import gen_species_data as gen  # noqa: E402

# ---------------------------------------------------------------------------
# tamanhos medidos NO ROM (o compilador de teste usa outra ABI)
# ---------------------------------------------------------------------------
# `struct SpeciesInfo` tem 26 bytes pela conta dos campos, mas o build usa
# `-mabi=apcs-gnu`, que arredonda o container dos bitfields `u16 evYield_*` para
# 4 bytes: cada entrada ocupa 28. Medido em 2026-10-23 comparando o padrão de
# BULBASAUR/TURTWIG/SPRIGATITO/GROOKEY dentro do ROM (28*índice casa exato).
TAM_ESPECIE = 28
TAM_DEX = 0x24
# `struct Evolution` tem 6 bytes de dados, mas o build alinha cada entrada em 8
# (mesmo efeito do apcs-gnu). Medido: gLevelUpLearnsets - gEvolutionTable =
# 0xA050 = 41040 = 1026 espécies * 5 evoluções * 8 bytes.
TAM_EVOLUCAO = 8
EVOS_POR_ESPECIE = 5

# offsets dentro de struct SpeciesInfo
OFF_STATS = 0
OFF_TIPOS = 6
OFF_CATCH = 8
OFF_EXP = 9
OFF_HABILIDADES = 0x16      # u8 abilities[2]
# offsets dentro de struct PokedexEntry
OFF_CATEGORIA = 0
OFF_ALTURA = 12
OFF_PESO = 14
OFF_DESCRICAO = 16


# ---------------------------------------------------------------------------
# leitura do ROM e do .map
# ---------------------------------------------------------------------------
def ler_simbolos(mapa: Path) -> dict[str, int]:
    """Extrai `endereço nome` do linker map."""
    simbolos: dict[str, int] = {}
    for linha in mapa.read_text(errors="replace").splitlines():
        m = re.match(r"\s*0x0(8[0-9a-fA-F]{6})\s+(\w+)\s*$", linha)
        if m:
            simbolos.setdefault(m.group(2), int("0x" + m.group(1), 16))
    return simbolos


def ler_charmap(poke: Path) -> dict[int, str]:
    """byte -> caractere, a partir de `charmap.txt` do próprio clone."""
    mapa: dict[int, str] = {}
    caminho = poke / "charmap.txt"
    if not caminho.exists():
        return mapa
    for linha in caminho.read_text(errors="replace").splitlines():
        m = re.match(r"'(.)'\s*=\s*([0-9A-Fa-f]{2})\s*$", linha)
        if m and m.group(1) != "\\":
            mapa[int(m.group(2), 16)] = m.group(1)
    return mapa


# alguns bytes do charmap têm glifo japonês no arquivo mas são ASCII no jogo
_ALIAS = {"。": ".", "ー": "-", "　": " ", "’": "'", "“": '"', "”": '"',
          "サ": "%", "×": "x"}


def decodificar(rom: bytes, offset: int, limite: int = 200) -> str:
    """Texto do charmap até o terminador 0xFF (ou 0x00 fora de string)."""
    saida = []
    for i in range(limite):
        b = rom[offset + i]
        if b == 0xFF:
            break
        if b in (0xFA, 0xFB, 0xFE):   # \n, \p, \l
            saida.append("\n")
            continue
        if b == 0x00:
            saida.append(" ")
            continue
        saida.append(_ALIAS.get(CHARMAP.get(b, "?"), CHARMAP.get(b, "?")))
    return "".join(saida).rstrip().replace(" ?", "?")


CHARMAP: dict[int, str] = {}


def ler_constantes(poke: Path) -> dict[str, int]:
    """`#define NOME valor` dos headers de constantes (golpes, espécies, tipos).

    Aceita também alias (`#define MOVE_VISE_GRIP MOVE_VICE_GRIP`), resolvidos em
    cadeia no fim: sem isso os learnsets com o nome novo do RHH davam "esperado
    -1" e a conferência reprovava uma ROM correta.
    """
    valores: dict[str, int] = {}
    aliases: dict[str, str] = {}
    for rel in ("include/constants/moves.h", "include/constants/species.h",
                "include/constants/pokedex.h", "include/constants/pokemon.h",
                "include/constants/abilities.h",
                "include/battle.h"):        # MOVE_TARGET_* moram aqui
        caminho = poke / rel
        if not caminho.exists():
            continue
        for linha in caminho.read_text(errors="replace").splitlines():
            m = re.match(r"\s*#define\s+([A-Z][A-Z0-9_]*)\s+\(?(0x[0-9A-Fa-f]+|\d+)\)?"
                         r"\s*(?://.*)?$", linha)
            if m:
                valores.setdefault(m.group(1), int(m.group(2), 0))
            else:
                # alias: `#define MOVE_VISE_GRIP MOVE_VICE_GRIP` (a E4 criou 4 destes)
                a = re.match(r"\s*#define\s+([A-Z][A-Z0-9_]*)\s+([A-Z][A-Z0-9_]*)\s*(?://.*)?$", linha)
                if a:
                    aliases[a.group(1)] = a.group(2)
    # resolve os aliases em cadeia (MOVE_X -> MOVE_Y -> número)
    for nome in aliases:
        visto: set[str] = set()
        alvo = nome
        while alvo in aliases and alvo not in visto:
            visto.add(alvo)
            alvo = aliases[alvo]
        if alvo in valores:
            valores[nome] = valores[alvo]
    return valores


# ---------------------------------------------------------------------------
# o que o gerador escreveu (fonte da verdade da comparação)
# ---------------------------------------------------------------------------
def esperado_especies(texto: str) -> dict[str, dict]:
    """Lê `species_info_gen4_9.h` -> nome: stats/tipos/catch/exp."""
    dados: dict[str, dict] = {}
    for bloco in re.finditer(r"\[SPECIES_(\w+)\] =\s*\{(.*?)\n    \},", texto, re.S):
        nome, corpo = bloco.group(1), bloco.group(2)

        def campo(chave: str, padrao: str = "0") -> str:
            m = re.search(rf"\.{chave} = ([^,\n]+),", corpo)
            return m.group(1).strip() if m else padrao

        stats = [int(campo(f"base{c}")) for c in
                 ("HP", "Attack", "Defense", "Speed", "SpAttack", "SpDefense")]
        bruto_tipos = re.search(r"\.types = \{([^}]*)\}", corpo)
        tipos = [t.strip() for t in bruto_tipos.group(1).split(",")] if bruto_tipos else []
        dados[nome] = dict(stats=stats, tipos=tipos,
                           catch=int(campo("catchRate")), exp=int(campo("expYield")))
    return dados


def esperado_dex(texto: str) -> dict[str, dict]:
    """Lê `pokedex_entries_gen4_9.h` -> nome: categoria/altura/peso."""
    dados: dict[str, dict] = {}
    for bloco in re.finditer(r"\[NATIONAL_DEX_(\w+)\] =\s*\{(.*?)\n    \},", texto, re.S):
        nome, corpo = bloco.group(1), bloco.group(2)
        cat = re.search(r'\.categoryName = _\("([^"]*)"\)', corpo)
        altura = re.search(r"\.height = (\d+)", corpo)
        peso = re.search(r"\.weight = (\d+)", corpo)
        dados[nome] = dict(categoria=cat.group(1) if cat else "",
                           altura=int(altura.group(1)) if altura else -1,
                           peso=int(peso.group(1)) if peso else -1,
                           texto="")
    # textos: vêm de pokedex_text_gen4_9.h, ligados por sPokedexText_<NOME>
    return dados


def esperado_textos(texto_bruto: str) -> dict[str, str]:
    """`sPokedexText_X[] = _("...")` -> {X: texto}."""
    return {m.group(1): m.group(2).replace(chr(92) + "n", "\n")
            for m in re.finditer(r'static const u8 sPokedexText_(\w+)\[\] = _\("((?:[^"\\]|\\.)*)"\);',
                                 texto_bruto)}


def esperado_learnsets(texto: str, ponteiros: str) -> dict[str, list[tuple[int, str]]]:
    """Lê os learnsets da Gen 4-9 e o bloco de ponteiros.

    O nome do array é `s{nome.title()}LevelUpLearnsetG4`, que não volta para o
    nome da espécie em casos como MR_MIME (`sMr_Mime…`). Por isso o mapa
    espécie -> array vem do próprio bloco `[SPECIES_X] = sYyy…,`.
    """
    arrays: dict[str, list[tuple[int, str]]] = {}
    for bloco in re.finditer(r"static const u16 (s\w+)\[\] = \{(.*?)\n\};", texto, re.S):
        arrays[bloco.group(1)] = [
            (int(n), g) for n, g in
            re.findall(r"LEVEL_UP_MOVE\((\d+),\s*(MOVE_\w+)\)", bloco.group(2))]
    dados: dict[str, list[tuple[int, str]]] = {}
    for m in re.finditer(r"\[SPECIES_(\w+)\] = (s\w+),", ponteiros):
        if m.group(2) in arrays:
            dados[m.group(1)] = arrays[m.group(2)]
    return dados


def esperado_evolucoes(texto: str) -> dict[str, tuple[str, int, str]]:
    """Lê `evolution_gen4_9.h` -> nome: (método, parâmetro, alvo)."""
    dados: dict[str, tuple[str, int, str]] = {}
    for m in re.finditer(r"\[SPECIES_(\w+)\]\s*=\s*\{\{(EVO_\w+),\s*(\d+),\s*SPECIES_(\w+)\}\}",
                         texto):
        dados[m.group(1)] = (m.group(2), int(m.group(3)), m.group(4))
    return dados


# ---------------------------------------------------------------------------
# comparação
# ---------------------------------------------------------------------------
def conferir(rom: bytes, simbolos: dict[str, int], especies: dict[str, dict],
             dex: dict[str, dict], learnsets: dict[str, list[tuple[int, str]]],
             evolucoes: dict[str, tuple[str, int, str]],
             numeros: dict[str, int], constantes: dict[str, int],
             amostras: int = 0, verboso: bool = True) -> dict:
    """Compara o ROM com o esperado. Devolve o relatório (e imprime falhas)."""
    falhas: list[str] = []
    conferidos = dict(especies=0, dex=0, learnset=0, evolucao=0)

    def rom_offset(simbolo: str) -> int:
        return simbolos[simbolo] - 0x08000000

    def nomes() -> list[str]:
        ordem = sorted(especies, key=lambda n: numeros.get(n, 0))
        return ordem[:amostras] if amostras else ordem

    base_esp = rom_offset("gSpeciesInfo")
    for nome in nomes():
        idx = numeros[nome]
        o = base_esp + TAM_ESPECIE * idx
        esperado = especies[nome]
        b = rom[o:o + TAM_ESPECIE]
        stats = list(b[OFF_STATS:OFF_STATS + 6])
        tipos = [constantes.get(t, -1) for t in esperado["tipos"]]
        got = dict(stats=stats, tipos=[b[OFF_TIPOS], b[OFF_TIPOS + 1]],
                   catch=b[OFF_CATCH], exp=b[OFF_EXP])
        if got["stats"] != esperado["stats"]:
            falhas.append(f"{nome}: stats {got['stats']} != {esperado['stats']}")
        if got["tipos"] != tipos:
            falhas.append(f"{nome}: tipos {got['tipos']} != {tipos}")
        if got["catch"] != esperado["catch"]:
            falhas.append(f"{nome}: catch {got['catch']} != {esperado['catch']}")
        if got["exp"] != esperado["exp"]:
            falhas.append(f"{nome}: exp {got['exp']} != {esperado['exp']}")
        conferidos["especies"] += 1

        # --- Pokédex
        if "gPokedexEntries" in simbolos and nome in dex:
            o = rom_offset("gPokedexEntries") + TAM_DEX * idx
            alvo = dex[nome]
            categoria = decodificar(rom, o + OFF_CATEGORIA, 12).strip()
            altura, peso = struct.unpack_from("<HH", rom, o + OFF_ALTURA)
            ponteiro = struct.unpack_from("<I", rom, o + OFF_DESCRICAO)[0]
            if categoria != alvo["categoria"]:
                falhas.append(f"{nome}: categoria {categoria!r} != {alvo['categoria']!r}")
            if (altura, peso) != (alvo["altura"], alvo["peso"]):
                falhas.append(f"{nome}: altura/peso {altura}/{peso} != "
                              f"{alvo['altura']}/{alvo['peso']}")
            if not 0x08000000 <= ponteiro < 0x0A000000:
                falhas.append(f"{nome}: descrição com ponteiro inválido {ponteiro:#x}")
            else:
                texto_rom = decodificar(rom, ponteiro - 0x08000000, 240)
                esperado_txt = alvo.get("texto", "")
                limpar = lambda t: re.sub(r"\s+", "", t)  # noqa: E731
                if limpar(texto_rom) != limpar(esperado_txt):
                    falhas.append(f"{nome}: texto {texto_rom[:40]!r} != "
                                  f"{esperado_txt[:40]!r}")
            conferidos["dex"] += 1

        # --- golpes por nível
        if "gLevelUpLearnsets" in simbolos and nome in learnsets:
            ponteiro = struct.unpack_from("<I", rom, rom_offset("gLevelUpLearnsets")
                                          + 4 * idx)[0]
            if not 0x08000000 <= ponteiro < 0x0A000000:
                falhas.append(f"{nome}: learnset sem ponteiro ({ponteiro:#x})")
            else:
                dados = struct.unpack_from("<6H", rom, ponteiro - 0x08000000)
                for k, (nivel, golpe) in enumerate(learnsets[nome][:3]):
                    esperado_valor = (nivel << 9) | constantes.get(golpe, -1)
                    if dados[k] != esperado_valor:
                        falhas.append(f"{nome}: golpe #{k} {dados[k]:#06x} != "
                                      f"{esperado_valor:#06x} ({nivel} {golpe})")
                conferidos["learnset"] += 1

        # --- evolução
        if "gEvolutionTable" in simbolos and nome in evolucoes:
            o = rom_offset("gEvolutionTable") + TAM_EVOLUCAO * EVOS_POR_ESPECIE * idx
            metodo, param, alvo = struct.unpack_from("<HHH", rom, o)
            esperado_metodo, esperado_param, esperado_alvo = evolucoes[nome]
            got = (metodo, param, alvo)
            esperado = (constantes.get(esperado_metodo, -1), esperado_param,
                        constantes.get("SPECIES_" + esperado_alvo, -1))
            if got != esperado:
                falhas.append(f"{nome}: evolução {got} != {esperado}")
            conferidos["evolucao"] += 1

    if verboso:
        print(f"  espécies conferidas : {conferidos['especies']}")
        print(f"  dex conferidas      : {conferidos['dex']}")
        print(f"  learnsets conferidos: {conferidos['learnset']}")
        print(f"  evoluções conferidas: {conferidos['evolucao']}")
        for falha in falhas[:20]:
            print(f"  FALHA {falha}")
        if len(falhas) > 20:
            print(f"  ... e mais {len(falhas) - 20} falha(s)")
    return dict(falhas=falhas, conferidos=conferidos)


# ---------------------------------------------------------------------------
# self-test (não precisa de ROM nem de toolchain)
# ---------------------------------------------------------------------------
def conferir_e3(rom: bytes, simbolos: dict[str, int], numeros: dict[str, int],
                constantes: dict[str, int], poke: Path) -> list[str]:
    """Confere no ROM: tabela de efetividade, tipos Fada e categorias de golpe."""
    falhas: list[str] = []

    # --- tabela de tipos
    if "gTypeEffectiveness" not in simbolos:
        return ["gTypeEffectiveness fora do .map"]
    tam = 0
    m = re.search(r"#define TYPE_EFFECT_TABLE_SIZE (\d+)",
                  (poke / "include/battle_main.h").read_text())
    if m:
        tam = int(m.group(1))
    if not tam:
        return ["TYPE_EFFECT_TABLE_SIZE nao encontrado"]

    base = simbolos["gTypeEffectiveness"] - 0x08000000
    regras: dict[tuple[int, int], int] = {}
    for i in range(0, tam, 3):
        atk, dfn, mult = rom[base + i], rom[base + i + 1], rom[base + i + 2]
        if atk in (constantes.get("TYPE_ENDTABLE", 0xFF),):
            break
        regras[(atk, dfn)] = mult

    fada = constantes.get("TYPE_FAIRY", 18)
    esperado = {
        (fada, constantes["TYPE_DRAGON"]): 20,
        (fada, constantes["TYPE_FIGHTING"]): 20,
        (fada, constantes["TYPE_DARK"]): 20,
        (fada, constantes["TYPE_STEEL"]): 5,
        (fada, constantes["TYPE_POISON"]): 5,
        (fada, constantes["TYPE_FIRE"]): 5,
        (constantes["TYPE_DRAGON"], fada): 0,
        (constantes["TYPE_POISON"], fada): 20,
        (constantes["TYPE_STEEL"], fada): 20,
        (constantes["TYPE_FIGHTING"], fada): 5,
        (constantes["TYPE_BUG"], fada): 5,
        (constantes["TYPE_DARK"], fada): 5,
    }
    for chave, valor in esperado.items():
        if regras.get(chave) != valor:
            falhas.append(f"efetividade {chave} = {regras.get(chave)}, esperava {valor}")

    # --- especies com tipo Fada
    base_esp = simbolos["gSpeciesInfo"] - 0x08000000
    com_fada = []
    for nome, idx in numeros.items():
        o = base_esp + TAM_ESPECIE * idx
        if rom[o + OFF_TIPOS] == fada or rom[o + OFF_TIPOS + 1] == fada:
            com_fada.append(nome)
    if len(com_fada) < 30:
        falhas.append(f"so {len(com_fada)} especies com TYPE_FAIRY no ROM")

    # --- categorias de golpe
    if "gMoveCategories" in simbolos:
        o = simbolos["gMoveCategories"] - 0x08000000
        categorias = rom[o:o + constantes.get("MOVES_COUNT", 355)]
        esperado_cat = {"MOVE_POUND": 0, "MOVE_BODY_SLAM": 0, "MOVE_FLAMETHROWER": 1,
                        "MOVE_THUNDERBOLT": 1, "MOVE_GROWL": 2, "MOVE_SWORDS_DANCE": 2}
        for golpe, valor in esperado_cat.items():
            if golpe not in constantes:
                falhas.append(f"{golpe} fora de moves.h")
            elif categorias[constantes[golpe]] != valor:
                falhas.append(f"{golpe}: categoria {categorias[constantes[golpe]]} != {valor}")
        fisicos = sum(1 for c in categorias if c == 0)
        esperado_fisicos = (poke / "src/data/battle_moves_category.h").read_text().count(
            "MOVE_CATEGORY_PHYSICAL")
        if fisicos != esperado_fisicos:
            falhas.append(f"{fisicos} golpes fisicos no ROM, {esperado_fisicos} na tabela gerada")
    else:
        falhas.append("gMoveCategories fora do .map")

    if not falhas:
        print(f"  E3 ok: {len(esperado)} regras de Fada, {len(com_fada)} especies com Fada, "
              "categorias de golpe no ROM")
    return falhas




# ---------------------------------------------------------------------------
# E4: golpes das Gen 4-9
# ---------------------------------------------------------------------------
# `struct BattleMove` no FireRed: 9 bytes, todos u8 (priority e' s8).
OFF_GOLPE = {"effect": 0, "power": 1, "type": 2, "accuracy": 3, "pp": 4,
             "secondaryEffectChance": 5, "target": 6, "priority": 7, "flags": 8}
TAM_GOLPE = 9


def esperado_golpes(poke: Path, constantes: dict[str, int] | None = None) -> dict[str, dict]:
    """Le `src/data/battle_moves.h` -> {MOVE_X: {campo: valor}}.

    Campos simbólicos (`TYPE_FIRE`, `MOVE_TARGET_BOTH`) são resolvidos pelos
    `#define`s do próprio jogo; o que não der para resolver fica de fora.
    """
    constantes = constantes or {}
    texto = (poke / "src/data/battle_moves.h").read_text()
    saida: dict[str, dict] = {}
    for nome, corpo in re.findall(r"\[(MOVE_[A-Z0-9_]+)\] =\s*\n\s*\{(.*?)\n    \},",
                                  texto, re.S):
        d = {}
        for campo in OFF_GOLPE:
            m = re.search(r"\." + campo + r"\s*=\s*([^,\n]+)", corpo)
            if not m:
                continue
            bruto = m.group(1).strip()
            if campo == "flags":
                valor = 0
                for bit, nomeflag in enumerate(("FLAG_MAKES_CONTACT", "FLAG_PROTECT_AFFECTED",
                                                "FLAG_MAGIC_COAT_AFFECTED", "FLAG_SNATCH_AFFECTED",
                                                "FLAG_MIRROR_MOVE_AFFECTED",
                                                "FLAG_KINGS_ROCK_AFFECTED")):
                    if nomeflag in bruto:
                        valor |= 1 << bit
                d[campo] = valor
            elif bruto.isdigit() or (bruto.startswith("-") and bruto[1:].isdigit()):
                d[campo] = int(bruto)
            elif bruto in constantes:
                d[campo] = constantes[bruto]
        saida[nome] = d
    return saida


def esperado_nomes_golpe(poke: Path) -> dict[str, str]:
    """Le `src/data/text/move_names.h` -> {MOVE_X: "NOME"}."""
    texto = (poke / "src/data/text/move_names.h").read_text()
    return dict(re.findall(r'\[(MOVE_[A-Z0-9_]+)\] = _\("((?:[^"\\]|\\.)*)"\)', texto))


def _melhor_passo(rom: bytes, base: int, constantes: dict[str, int],
                  golpes: dict[str, dict]) -> tuple[int, int]:
    """Descobre de quantos em quantos bytes as entradas aparecem no ROM.

    O compilador de teste e o `make` usam ABIs diferentes (apcs-gnu x eabi), entao
    o passo e' medido contra golpes conhecidos em vez de suposto.
    """
    amostra = [(constantes[n], d) for n, d in golpes.items()
               if n in constantes and "power" in d and "type" in d][:40]
    melhor, pontos = TAM_GOLPE, -1
    for passo in (8, 9, 10, 12, 16):
        acertos = 0
        for idx, d in amostra:
            o = base + passo * idx
            if rom[o + OFF_GOLPE["power"]] == d["power"] and \
               rom[o + OFF_GOLPE["type"]] == d["type"]:
                acertos += 1
        if acertos > pontos:
            melhor, pontos = passo, acertos
    return melhor, pontos


def conferir_e4(rom: bytes, simbolos: dict[str, int], constantes: dict[str, int],
                poke: Path, verboso: bool = True) -> list[str]:
    """Confere no ROM: tabela de golpes, nomes, descricoes e MOVES_COUNT."""
    falhas: list[str] = []
    if "gBattleMoves" not in simbolos or "gMoveNames" not in simbolos:
        return ["gBattleMoves/gMoveNames fora do .map"]

    golpes = esperado_golpes(poke, constantes)
    nomes = esperado_nomes_golpe(poke)
    total = constantes.get("MOVES_COUNT", 0)
    if not total:
        return ["MOVES_COUNT nao encontrado em moves.h"]
    if len(golpes) != total:
        falhas.append(f"{len(golpes)} golpes em battle_moves.h, MOVES_COUNT {total}")
    if len(nomes) != total:
        falhas.append(f"{len(nomes)} nomes em move_names.h, MOVES_COUNT {total}")

    # --- tabela de golpes
    base = simbolos["gBattleMoves"] - 0x08000000
    passo, pontos = _melhor_passo(rom, base, constantes, golpes)
    amostra = min(40, sum(1 for n, d in golpes.items()
                          if n in constantes and "power" in d and "type" in d))
    if pontos < max(3, amostra):
        falhas.append(f"gBattleMoves: so {pontos}/{amostra} golpes conhecidos casam "
                      f"(passo medido {passo}); campos divergentes abaixo")
    erros = 0
    for nome, d in golpes.items():
        if nome not in constantes:
            continue
        o = base + passo * constantes[nome]
        for campo, valor in d.items():
            lido = rom[o + OFF_GOLPE[campo]]
            if campo == "priority" and lido > 127:
                lido -= 256
            if lido != valor:
                erros += 1
                if erros <= 5:
                    falhas.append(f"{nome}.{campo} no ROM = {lido}, esperava {valor}")
    if erros > 5:
        falhas.append(f"... e mais {erros - 5} campos de golpe divergentes")

    # --- nomes
    base_nomes = simbolos["gMoveNames"] - 0x08000000
    # MOVE_NONE e' "$" (0xFF) — o proprio terminador, nao da' para decodificar
    verificaveis = [(n, t) for n, t in nomes.items() if n in constantes and n != "MOVE_NONE"]
    passo_nome, melhor_pontos = 0, -1
    for candidato in (17, 13, 16, 12, 18):      # MOVE_NAME_LENGTH + 1 = 17 com a E4
        acertos = sum(1 for n, t in verificaveis
                      if decodificar(rom, base_nomes + candidato * constantes[n], 24) == t)
        if acertos > melhor_pontos:
            passo_nome, melhor_pontos = candidato, acertos
    if melhor_pontos < len(verificaveis):
        falhas.append(f"gMoveNames: so {melhor_pontos}/{len(verificaveis)} nomes casam "
                      f"(passo medido {passo_nome}); divergentes abaixo")
    errados = 0
    for nome, texto in verificaveis:
        lido = decodificar(rom, base_nomes + passo_nome * constantes[nome], 24)
        if lido != texto:
            errados += 1
            if errados <= 5:
                falhas.append(f"nome de {nome} no ROM = {lido!r}, esperava {texto!r}")
    if errados > 5:
        falhas.append(f"... e mais {errados - 5} nomes divergentes")

    # --- descricoes (ponteiros por indice [MOVE_X - 1])
    if "gMoveDescriptionPointers" in simbolos:
        base_desc = simbolos["gMoveDescriptionPointers"] - 0x08000000
        vazias = fora = 0
        for nome, idx in constantes.items():
            if not nome.startswith("MOVE_"):
                continue            # SPECIES_*/ITEM_* tambem estao em `constantes`
            # MOVE_UNAVAILABLE = 0xFFFF e MOVE_RANDOM_TEACHABLE nao sao golpes
            if nome == "MOVE_NONE" or idx < 355 or idx >= constantes.get("MOVES_COUNT", 1 << 30):
                continue
            ptr = struct.unpack_from("<I", rom, base_desc + 4 * (idx - 1))[0]
            if not 0x08000000 <= ptr < 0x08000000 + len(rom):
                fora += 1
                continue
            if not decodificar(rom, ptr - 0x08000000, 60).strip():
                vazias += 1
        if fora:
            falhas.append(f"{fora} descricoes com ponteiro invalido")
        if vazias:
            falhas.append(f"{vazias} descricoes vazias")
    else:
        falhas.append("gMoveDescriptionPointers fora do .map")

    # --- animacoes: a tabela em assembly precisa ter TODOS os golpes
    if "gBattleAnims_Moves" in simbolos:
        base_anim = simbolos["gBattleAnims_Moves"] - 0x08000000
        ponteiros = struct.unpack_from(f"<{total}I", rom, base_anim)
        invalidos = [i for i, ptr in enumerate(ponteiros)
                     if not 0x08000000 <= ptr < 0x08000000 + len(rom)]
        if invalidos:
            falhas.append(f"gBattleAnims_Moves: {len(invalidos)} ponteiros fora do ROM "
                          f"(ex.: golpe {invalidos[0]}) — animacao indefinida")
        tackle = constantes.get("MOVE_TACKLE")
        if tackle is not None and tackle < total:
            novos = ponteiros[355:]
            genericos = sum(1 for p in novos if p == ponteiros[tackle])
            if genericos != len(novos):
                falhas.append(f"gBattleAnims_Moves: {len(novos) - genericos}/{len(novos)} "
                              "golpes novos sem a animacao generica (TACKLE)")
    else:
        falhas.append("gBattleAnims_Moves fora do .map")

    if not falhas and verboso:
        print(f"  E4 ok: {total} golpes, passo {passo} B, nomes de {passo_nome} B, "
              "descricoes, categorias e animacoes conferidas")
    return falhas


# ---------------------------------------------------------------------------
# E5: habilidades
# ---------------------------------------------------------------------------
def esperado_habilidades(poke: Path) -> tuple[dict[str, str], dict[str, str]]:
    """`(nomes, descricoes)` de `src/data/text/abilities.h`."""
    texto = (poke / "src/data/text/abilities.h").read_text(encoding="utf-8")
    nomes = {n: t for n, t in re.findall(r'\[(ABILITY_[A-Z0-9_]+)\] = _\("([^"]*)"\),', texto)}
    descricoes: dict[str, str] = {}
    simbolos = {m.group(1): m.group(2) for m in
                re.finditer(r'static const u8 (s[A-Za-z0-9]+Description)\[\] = _\("([^"]*)"\);', texto)}
    for nome, simbolo in re.findall(r"\[(ABILITY_[A-Z0-9_]+)\] = (s[A-Za-z0-9]+Description),", texto):
        if simbolo in simbolos:
            descricoes[nome] = simbolos[simbolo]
    return nomes, descricoes


def conferir_e5(rom: bytes, simbolos: dict[str, int], constantes: dict[str, int],
                poke: Path, numeros: dict[str, int] | None = None,
                verboso: bool = True) -> list[str]:
    """Confere no ROM: nomes, descrições e as habilidades de cada espécie nova."""
    falhas: list[str] = []
    if "gAbilityNames" not in simbolos or "gAbilityDescriptionPointers" not in simbolos:
        return ["gAbilityNames/gAbilityDescriptionPointers fora do .map"]
    total = constantes.get("ABILITIES_COUNT", 0)
    nomes, descricoes = esperado_habilidades(poke)
    if not total:
        return ["ABILITIES_COUNT nao encontrado em abilities.h"]
    if len(nomes) != total:
        falhas.append(f"{len(nomes)} nomes em abilities.h, ABILITIES_COUNT {total}")

    # --- nomes: descobre o passo comparando com o que o gerador escreveu
    base = simbolos["gAbilityNames"] - 0x08000000
    verificaveis = [(constantes[n], t) for n, t in nomes.items() if n in constantes and n != "ABILITY_NONE"]
    passo, melhor = 0, -1
    for candidato in (17, 13, 12, 16, 20, 24):        # ABILITY_NAME_LENGTH + 1 = 17 com a E5
        acertos = sum(1 for i, t in verificaveis if decodificar(rom, base + candidato * i, 24) == t)
        if acertos > melhor:
            passo, melhor = candidato, acertos
    if melhor < len(verificaveis):
        erros = 0
        for i, t in verificaveis:
            lido = decodificar(rom, base + passo * i, 24)
            if lido != t:
                erros += 1
                if erros <= 5:
                    falhas.append(f"gAbilityNames[{i}] = {lido!r}, esperava {t!r}")
        if erros > 5:
            falhas.append(f"... e mais {erros - 5} nomes de habilidade errados")

    # --- descrições: todo ponteiro tem de cair dentro do ROM e ler texto
    base_ptr = simbolos["gAbilityDescriptionPointers"] - 0x08000000
    ruins = 0
    for i in range(total):
        ptr = struct.unpack_from("<I", rom, base_ptr + 4 * i)[0]
        if not 0x08000000 <= ptr < 0x0A000000:
            ruins += 1
            if ruins <= 5:
                falhas.append(f"descrição da habilidade {i}: ponteiro inválido {ptr:#x}")
            continue
        texto = decodificar(rom, ptr - 0x08000000, 80)
        if not texto.strip():
            ruins += 1
            if ruins <= 5:
                falhas.append(f"descrição da habilidade {i}: texto vazio")
    if ruins > 5:
        falhas.append(f"... e mais {ruins - 5} descrições de habilidade com problema")

    # --- habilidades das espécies novas (é o que a E5 destrava: antes era ABILITY_NONE)
    fonte = poke / "src/data/pokemon/species_info_gen4_9.h"
    if "gSpeciesInfo" in simbolos and fonte.exists():
        if numeros is None:
            numeros = gen.numeracao_nacional(poke)
        base_esp = simbolos["gSpeciesInfo"] - 0x08000000
        blocos = gen.blocos_de_especie(fonte.read_text(encoding="utf-8"))
        conferidas = 0
        for nome_curto, corpo in blocos.items():
            if nome_curto not in numeros:
                continue
            # `campos()` devolve o valor já sem o nome do campo: `{ABILITY_X, ABILITY_Y}`
            m = re.search(r"\{\s*([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)",
                          gen.campos(corpo).get("abilities", ""))
            if not m:
                continue
            esperado = [constantes.get(m.group(1), -1), constantes.get(m.group(2), -1)]
            o = base_esp + TAM_ESPECIE * numeros[nome_curto] + OFF_HABILIDADES
            lido = [rom[o], rom[o + 1]]
            if lido != esperado:
                falhas.append(f"{nome_curto}: habilidades {lido} != {esperado}")
            conferidas += 1
        if verboso and falhas:
            print("  exemplos:", "; ".join(f.split(":")[0] for f in falhas[:8]))
        if verboso:
            print(f"  E5 ok: {total} habilidades, {melhor}/{len(verificaveis)} nomes e "
                  f"{total} descrições conferidas; habilidades de {conferidas} espécies novas "
                  f"batem com o gerado")
        if conferidas == 0:
            falhas.append("não conferi a habilidade de nenhuma espécie (numeros vazio?)")
    return falhas


def self_test_e4() -> int:
    """ROM sintetica: confere que o verificador de golpes aprova e reprova."""
    global CHARMAP
    guardado = CHARMAP
    # A-Z em sequência a partir de 0xBB, como no charmap do FireRed
    CHARMAP = {0x00: " ", **{0xBB + i: c for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}}
    falhas = 0
    tmp = Path(tempfile.mkdtemp())
    (tmp / "src/data/text").mkdir(parents=True)
    (tmp / "include/constants").mkdir(parents=True)
    (tmp / "src").mkdir(exist_ok=True)
    (tmp / "include/constants/moves.h").write_text(
        "#define MOVE_NONE 0\n#define MOVE_POUND 1\n#define MOVE_AURA_SPHERE 2\n"
        "#define MOVES_COUNT 3\n")
    (tmp / "src/data/battle_moves.h").write_text(
        "const struct BattleMove gBattleMoves[MOVES_COUNT] =\n{\n"
        "    [MOVE_NONE] =\n    {\n        .effect = EFFECT_HIT,\n        .power = 0,\n"
        "        .type = TYPE_MYSTERY,\n        .accuracy = 0,\n        .pp = 0,\n"
        "        .secondaryEffectChance = 0,\n        .target = MOVE_TARGET_SELECTED,\n"
        "        .priority = 0,\n        .flags = 0,\n    },\n"
        "    [MOVE_POUND] =\n    {\n        .effect = EFFECT_HIT,\n        .power = 40,\n"
        "        .type = TYPE_NORMAL,\n        .accuracy = 100,\n        .pp = 35,\n"
        "        .secondaryEffectChance = 0,\n        .target = MOVE_TARGET_SELECTED,\n"
        "        .priority = 0,\n        .flags = FLAG_MAKES_CONTACT | FLAG_PROTECT_AFFECTED,\n"
        "    },\n"
        "    [MOVE_AURA_SPHERE] =\n    {\n        .effect = EFFECT_HIT,\n        .power = 80,\n"
        "        .type = TYPE_FIGHTING,\n        .accuracy = 0,\n        .pp = 20,\n"
        "        .secondaryEffectChance = 0,\n        .target = MOVE_TARGET_SELECTED,\n"
        "        .priority = 0,\n        .flags = FLAG_PROTECT_AFFECTED,\n    },\n};\n")
    (tmp / "src/data/text/move_names.h").write_text(
        "const u8 gMoveNames[MOVES_COUNT][MOVE_NAME_LENGTH + 1] = {\n"
        '    [MOVE_NONE] = _(""),\n    [MOVE_POUND] = _("POUND"),\n'
        '    [MOVE_AURA_SPHERE] = _("AURA SPHERE"),\n};\n')

    rom = bytearray(0x100000)
    simbolos = dict(gBattleMoves=0x08010000, gMoveNames=0x08020000,
                    gMoveDescriptionPointers=0x08030000, gBattleAnims_Moves=0x08040000)
    constantes = dict(MOVE_NONE=0, MOVE_POUND=1, MOVE_AURA_SPHERE=2, MOVES_COUNT=3,
                      TYPE_NORMAL=0, TYPE_FIGHTING=1, TYPE_MYSTERY=9, MOVE_TACKLE=1)

    def gravar(nome_pound: bytes, power: int) -> None:
        base = 0x10000
        bytes_nome = {v: k for k, v in CHARMAP.items()}
        for idx, (nome, power_v, tipo, pp, acc, flags) in enumerate([
                ("", 0, 9, 0, 0, 0), ("POUND", 40, 0, 35, 100, 0x03),
                ("AURA SPHERE", power, 1, 20, 0, 0x02)]):
            o = base + TAM_GOLPE * idx
            rom[o:o + TAM_GOLPE] = bytes([1, power_v, tipo, acc, pp, 0, 0, 0, flags])
            n = nome_pound if idx == 1 else nome.encode()
            rom[0x20000 + 17 * idx:0x20000 + 17 * idx + len(n)] = bytes(
                bytes_nome.get(c, 0xBB) for c in n.decode())
            rom[0x20000 + 17 * idx + len(n)] = 0xFF
        struct.pack_into("<I", rom, 0x40000, 0x08050000)
        struct.pack_into("<I", rom, 0x40004, 0x08050020)     # Move_POUND/TACKLE
        struct.pack_into("<I", rom, 0x40008, 0x08050020)     # golpe novo: generica

    gravar(b"POUND", 80)
    bom = conferir_e4(bytes(rom), simbolos, constantes, tmp, verboso=False)
    if bom:
        print(f"  FALHA: ROM sintetica correta reprovada: {bom[:2]}")
        falhas += 1
    else:
        print("  ok: golpes/nomes sinteticos aprovados")

    gravar(b"POUND", 60)          # power errado no ROM
    ruim = conferir_e4(bytes(rom), simbolos, constantes, tmp, verboso=False)
    if not any("power" in f for f in ruim):
        print("  FALHA: poder errado nao foi detectado")
        falhas += 1
    else:
        print("  ok: poder errado detectado")

    gravar(b"PAUND", 80)          # nome errado no ROM
    ruim = conferir_e4(bytes(rom), simbolos, constantes, tmp, verboso=False)
    if not any("nome de MOVE_POUND" in f for f in ruim):
        print("  FALHA: nome errado nao foi detectado")
        falhas += 1
    else:
        print("  ok: nome errado detectado")

    gravar(b"POUND", 80)
    struct.pack_into("<I", rom, 0x40008, 0x12345678)         # ponteiro de animacao invalido
    ruim = conferir_e4(bytes(rom), simbolos, constantes, tmp, verboso=False)
    if not any("gBattleAnims_Moves" in f for f in ruim):
        print("  FALHA: animacao invalida nao foi detectada")
        falhas += 1
    else:
        print("  ok: animacao invalida detectada")

    CHARMAP = guardado
    return 1 if falhas else 0


def self_test() -> int:
    """Monta um ROM sintético e confere que o verificador acerta e detecta erro."""
    global CHARMAP
    CHARMAP = {0xBE: "D", 0xBF: "E", 0xC5: "K", 0xCA: "P", 0xCE: "S",
               0xDD: "e", 0xE2: "n", 0xED: "d"}
    simbolos = dict(gSpeciesInfo=0x08010000, gPokedexEntries=0x08020000,
                    gEvolutionTable=0x08030000, gLevelUpLearnsets=0x08040000)
    rom = bytearray(0x50000)
    especies = {"TURTWIG": dict(stats=[55, 68, 64, 31, 45, 55],
                                tipos=["TYPE_GRASS", "TYPE_GRASS"], catch=45, exp=64)}
    dex = {"TURTWIG": dict(categoria="SEED", altura=4, peso=102, texto="SEED")}
    learnsets = {"TURTWIG": [(1, "MOVE_TACKLE"), (5, "MOVE_WITHDRAW")]}
    evolucoes = {"TURTWIG": ("EVO_LEVEL", 18, "GROTLE")}
    numeros = {"TURTWIG": 387}
    constantes = dict(TYPE_GRASS=12, MOVE_TACKLE=33, MOVE_WITHDRAW=110,
                      EVO_LEVEL=1, SPECIES_GROTLE=388)

    def escrever(tabela: bool):
        o = 0x10000 + TAM_ESPECIE * 387
        rom[o:o + 6] = bytes(especies["TURTWIG"]["stats"])
        rom[o + OFF_TIPOS] = 12
        rom[o + OFF_TIPOS + 1] = 12
        rom[o + OFF_CATCH] = 45
        rom[o + OFF_EXP] = 64
        om = 0x20000 + TAM_DEX * 387
        rom[om:om + 4] = bytes([0xCE, 0xBF, 0xBF, 0xBE])
        struct.pack_into("<HH", rom, om + OFF_ALTURA, 4, 102)
        struct.pack_into("<I", rom, om + OFF_DESCRICAO, 0x08045000)
        rom[0x45000:0x45005] = bytes([0xCE, 0xBF, 0xBF, 0xBE, 0xFF])
        oe = 0x30000 + TAM_EVOLUCAO * EVOS_POR_ESPECIE * 387
        struct.pack_into("<HHH", rom, oe, 1, 18, 388)
        struct.pack_into("<I", rom, 0x40000 + 4 * 387, 0x08046000)
        struct.pack_into("<HH", rom, 0x46000, (1 << 9) | 33, (5 << 9) | 110)

    falhas = 0
    escrever(True)
    bom = conferir(bytes(rom), simbolos, especies, dex, learnsets, evolucoes,
                   numeros, constantes, verboso=False)
    if bom["falhas"]:
        print(f"  FALHA: ROM sintética correta reprovada: {bom['falhas'][:3]}")
        falhas += 1
    else:
        print("  ok: ROM sintética correta aprovada")

    rom[0x10000 + TAM_ESPECIE * 387 + 2] = 0  # Defense errado (64 -> 0)
    ruim = conferir(bytes(rom), simbolos, especies, dex, learnsets, evolucoes,
                    numeros, constantes, verboso=False)
    if not any("stats" in f for f in ruim["falhas"]):
        print("  FALHA: defesa errada não foi detectada")
        falhas += 1
    else:
        print("  ok: defesa errada detectada")

    # entradas sintéticas precisam ser lidas de volta
    if esperado_especies(
            "[SPECIES_X] =\n    {\n        .baseHP = 1,\n        .baseAttack = 2,\n"
            "        .baseDefense = 3,\n        .baseSpeed = 4,\n        .baseSpAttack = 5,\n"
            "        .baseSpDefense = 6,\n        .types = {TYPE_FIRE, TYPE_FIRE},\n"
            "        .catchRate = 7,\n        .expYield = 8,\n    },")["X"]["stats"] != [1, 2, 3, 4, 5, 6]:
        print("  FALHA: parser de species_info_gen4_9.h")
        falhas += 1
    else:
        print("  ok: parser do header de espécies")
    return 1 if falhas else 0


# ---------------------------------------------------------------------------
def self_test_e5() -> int:
    """ROM sintética: confere que a conferência de habilidades aprova e reprova."""
    global CHARMAP
    guardado = CHARMAP
    CHARMAP = {0x00: " ", **{0xBB + i: c for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}}
    falhas = 0
    tmp = Path(tempfile.mkdtemp())
    (tmp / "src/data/text").mkdir(parents=True)
    (tmp / "src/data/pokemon").mkdir(parents=True)
    (tmp / "include/constants").mkdir(parents=True)
    (tmp / "include/constants/abilities.h").write_text(
        "#define ABILITY_NONE 0\n#define ABILITY_STENCH 1\n#define ABILITY_EARTH_EATER 2\n"
        "#define ABILITIES_COUNT 3\n")
    (tmp / "src/data/text/abilities.h").write_text(
        'static const u8 sNoneDescription[] = _("No special ability.");\n'
        'static const u8 sStenchDescription[] = _("Moves may cause flinching.");\n'
        'static const u8 sEarthEaterDescription[] = _("Restores HP if hit by a Ground move.");\n'
        "const u8 *const gAbilityDescriptionPointers[ABILITIES_COUNT] =\n{\n"
        "    [ABILITY_NONE] = sNoneDescription,\n"
        "    [ABILITY_STENCH] = sStenchDescription,\n"
        "    [ABILITY_EARTH_EATER] = sEarthEaterDescription,\n};\n"
        "const u8 gAbilityNames[ABILITIES_COUNT][ABILITY_NAME_LENGTH + 1] =\n{\n"
        '    [ABILITY_NONE] = _("-------"),\n'
        '    [ABILITY_STENCH] = _("STENCH"),\n'
        '    [ABILITY_EARTH_EATER] = _("EARTH EATER"),\n};\n')
    (tmp / "src/data/pokemon/species_info_gen4_9.h").write_text(
        "    [SPECIES_ORTHWORM] =\n    {\n        .baseHP        = 70,\n"
        "        .abilities = { ABILITY_EARTH_EATER, ABILITY_NONE },\n    },\n")
    numeros = {"ORTHWORM": 968}   # chave sem o prefixo SPECIES_, como em numeracao_nacional

    rom = bytearray(0x50000)
    simbolos = dict(gAbilityNames=0x08010000, gAbilityDescriptionPointers=0x08020000,
                    gSpeciesInfo=0x08030000)
    const = dict(ABILITY_NONE=0, ABILITY_STENCH=1, ABILITY_EARTH_EATER=2, ABILITIES_COUNT=3)

    def escrever(quebrar: bool = False):
        for i, nome in enumerate(["", "STENCH", "EARTH EATER"]):
            o = 0x10000 + 17 * i
            rom[o:o + 17] = bytes([0xFF]) * 17
            rom[o:o + len(nome)] = bytes([0xBB + ord(c) - 65 if c != " " else 0x00 for c in nome])
        for i in range(3):
            struct.pack_into("<I", rom, 0x20000 + 4 * i, 0x08040000 + 0x40 * i)
            texto = ["No special ability.", "Moves may cause flinching.",
                     "Restores HP if hit by a Ground move."][i]
            if quebrar and i == 2:
                struct.pack_into("<I", rom, 0x20000 + 4 * i, 0x12345678)
            o = 0x40000 + 0x40 * i
            rom[o:o + len(texto)] = bytes([0xBB + ord(c) - 65 if c.isalpha() else (0x00 if c == " " else 0xAD)
                                           for c in texto.upper()])
        o = 0x30000 + TAM_ESPECIE * 968 + OFF_HABILIDADES
        rom[o] = 2 if not quebrar else 0
        rom[o + 1] = 0

    escrever()
    bom = conferir_e5(bytes(rom), simbolos, const, tmp, numeros, verboso=False)
    if bom:
        print(f"  FALHA: ROM de habilidades correta reprovada: {bom[:3]}")
        falhas += 1
    else:
        print("  ok: habilidades corretas aprovadas")

    escrever(quebrar=True)
    ruim = conferir_e5(bytes(rom), simbolos, const, tmp, numeros, verboso=False)
    if not any("ORTHWORM" in f or "ponteiro" in f for f in ruim):
        print(f"  FALHA: habilidade errada não detectada: {ruim[:3]}")
        falhas += 1
    else:
        print("  ok: habilidade errada detectada")
    CHARMAP = guardado
    return 1 if falhas else 0


def main() -> int:
    global CHARMAP
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", type=Path, default=Path("/tmp/pokefirered"))
    ap.add_argument("--rom", type=Path, default=None,
                    help="padrão: <pokefirered>/pokefirered_modern.gba")
    ap.add_argument("--mapa", type=Path, default=None,
                    help="padrão: <pokefirered>/pokefirered_modern.map")
    ap.add_argument("--amostras", type=int, default=0, help="0 = todas as espécies")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        print("self-test: verificador de dados no ROM")
        return self_test() | self_test_e4() | self_test_e5()

    poke = a.pokefirered
    rom_path = a.rom or (poke / "pokefirered_modern.gba")
    mapa = a.mapa or (poke / "pokefirered_modern.map")
    for caminho in (rom_path, mapa):
        if not caminho.exists():
            print(f"não encontrei {caminho}; compile antes (make MODERN=1)")
            return 2

    CHARMAP = ler_charmap(poke)
    if not CHARMAP:
        print("aviso: charmap.txt não encontrado; categorias não serão conferidas",
              file=sys.stderr)

    rom = rom_path.read_bytes()
    simbolos = ler_simbolos(mapa)
    faltando = {"gSpeciesInfo", "gPokedexEntries", "gEvolutionTable",
                "gLevelUpLearnsets"} - set(simbolos)
    if faltando:
        print(f"não achei no .map: {sorted(faltando)}")
        return 2

    destino = poke / "src" / "data" / "pokemon"
    especies = esperado_especies((destino / "species_info_gen4_9.h").read_text())
    dex = esperado_dex((destino / "pokedex_entries_gen4_9.h").read_text())
    textos = esperado_textos((destino / "pokedex_text_gen4_9.h").read_text())
    for nome in dex:
        dex[nome]["texto"] = textos.get(nome, "")
    learnsets = esperado_learnsets(
        (destino / "level_up_learnsets_gen4_9.h").read_text(),
        (destino / "level_up_learnset_pointers.h").read_text())
    evolucoes = esperado_evolucoes((destino / "evolution_gen4_9.h").read_text())
    numeros = gen.numeracao_nacional(poke)
    constantes = ler_constantes(poke)

    print(f"ROM: {rom_path.name} ({len(rom)} B)")
    print(f"esperado: {len(especies)} espécies, {len(learnsets)} learnsets, "
          f"{len(evolucoes)} evoluções")
    rel = conferir(rom, simbolos, especies, dex, learnsets, evolucoes, numeros,
                   constantes, amostras=a.amostras)
    if (poke / "src/data/battle_moves_category.h").exists():
        rel["falhas"] += conferir_e3(rom, simbolos, numeros, constantes, poke)
    if (poke / "src/data/text/move_names.h").exists():
        rel["falhas"] += conferir_e4(rom, simbolos, constantes, poke)
    if (poke / "src/data/text/abilities.h").exists():
        rel["falhas"] += conferir_e5(rom, simbolos, constantes, poke)

    for falha in rel["falhas"]:
        print(f"  FALHA: {falha}")
    if a.json:
        print(json.dumps(dict(falhas=rel["falhas"], conferidos=rel["conferidos"]),
                         indent=2, ensure_ascii=False))
    if rel["falhas"]:
        print(f"REPROVADO: {len(rel['falhas'])} divergência(s)")
        return 1
    print("ok: dados do ROM batem com o gerado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
