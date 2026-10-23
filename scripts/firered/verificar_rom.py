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
    """`#define NOME valor` dos headers de constantes (golpes, espécies, tipos)."""
    valores: dict[str, int] = {}
    for rel in ("include/constants/moves.h", "include/constants/species.h",
                "include/constants/pokedex.h", "include/constants/pokemon.h"):
        caminho = poke / rel
        if not caminho.exists():
            continue
        for linha in caminho.read_text(errors="replace").splitlines():
            m = re.match(r"\s*#define\s+([A-Z][A-Z0-9_]*)\s+\(?(0x[0-9A-Fa-f]+|\d+)\)?"
                         r"\s*(?://.*)?$", linha)
            if m:
                valores.setdefault(m.group(1), int(m.group(2), 0))
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
        return self_test()

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
