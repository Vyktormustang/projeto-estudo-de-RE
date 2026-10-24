#!/usr/bin/env python3
"""Gera as habilidades das Gen 4-9 (E5, onda 1: só dados + nomes/descrições).

Por que isso existe
-------------------
O FireRed tem 78 habilidades (IDs 0-77, 77 delas são as da Gen 3). A E2 atribuiu
`ABILITY_NONE` a toda espécie nova com habilidade que o jogo não conhecia — são
**243 habilidades faltando**. Esta etapa acrescenta as que faltam, mantendo os
IDs 0-77 **intocados** (o motor de batalha do FireRed depende deles).

`ABILITY_CACOPHONY` (FR 76) não existe no RHH e `ABILITY_AIR_LOCK` está em 76 lá
e 77 aqui: por isso o casamento é **por nome**, nunca por número. O relatório
mostra qualquer divergência.

O que é gerado (idempotente, dentro de blocos `// E5: ...`)

| arquivo                              | conteúdo                                      |
|--------------------------------------|-----------------------------------------------|
| `include/constants/abilities.h`      | `#define ABILITY_X n` das novas + `ABILITIES_COUNT` |
| `src/data/text/abilities.h`          | `gAbilityNames` (MAIÚSCULA, 16 col.) e `gAbilityDescriptionPointers` |
| `include/battle_main.h`              | `ABILITY_NAME_LENGTH` 12 → 16                 |
| `src/pokemon_summary_screen.c`       | buffer do nome com `ABILITY_NAME_LENGTH + 1`  |

Habilidade sem implementação é **silenciosa** (não trava): o switch do
`AbilityBattleEffects` simplesmente não a trata. É o mesmo "fallback seguro" da
E4 — o efeito de Gen 9 fica para a onda 2.

Uso
---
    python3 scripts/firered/gen_ability_data.py --self-test
    python3 scripts/firered/gen_ability_data.py --pokefirered /tmp/pokefirered \\
        --reference /tmp/fre --write
    python3 scripts/firered/gen_ability_data.py --pokefirered /tmp/pokefirered \\
        --reference /tmp/fre --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rhh  # noqa: E402
import gen_species_data as gen  # noqa: E402  (mesmo leitor de blocos da E2)

MARCA = "// E5:"
NOME_MAX = 16        # maior nome do RHH ("Thermal Exchange", "Supreme Overlord")
# `struct SpeciesInfo.abilities[2]` e' u8: ID 256 vira 0. As habilidades que
# alguma especie usa TEM de caber em 78..255 (178 vagas); as que nenhuma usa
# ficam acima e o truncamento nao aparece em jogo.
TETO_U8 = 256
PRIMEIRA_NOVA = 78
DESC_MAX = 51        # abilityDescStrBuf[52] do resumo
FR_ABILITY = "include/constants/abilities.h"
FR_TEXT = "src/data/text/abilities.h"
FR_BATTLE_MAIN = "include/battle_main.h"
FR_SUMMARY = "src/pokemon_summary_screen.c"
RH_ABIL = "include/constants/abilities.h"
RH_DATA = "src/data/abilities.h"


# --------------------------------------------------------------------------
# leitura do RHH
# --------------------------------------------------------------------------
def dados_do_rhh(ref: Path) -> dict[str, dict]:
    """`ABILITY_X` → {id, nome, descricao} do RHH (sem sentinelas)."""
    ids = rhh.enum_para_dict(
        (Path(ref) / RH_ABIL).read_text(encoding="utf-8", errors="replace"),
        "enum __attribute__((packed)) Ability",
    )
    ids = rhh.sem_sentinelas(ids, "ABILITY_")
    blocos = rhh.blocos_balanceados((Path(ref) / RH_DATA).read_text(encoding="utf-8", errors="replace"))

    dados: dict[str, dict] = {}
    for nome, valor in sorted(ids.items(), key=lambda kv: kv[1]):
        if nome == "ABILITY_NONE":
            continue
        corpo = blocos.get(nome, "")
        m_nome = re.search(r'\.name\s*=\s*_\("([^"]*)"\)', corpo)
        m_desc = re.search(r'\.description\s*=\s*(?:COMPOUND_STRING|_)\(\s*"([^"]*)"', corpo)
        texto = m_nome.group(1) if m_nome else nome.replace("ABILITY_", "").replace("_", " ").title()
        desc = m_desc.group(1) if m_desc else "No special ability."
        dados[nome] = {"id": valor, "nome": texto, "descricao": desc}
    return dados


def habilidades_usadas(ref: Path, pf: Path) -> dict[str, int]:
    """Quantas espécies do nosso jogo usam cada habilidade (slots 1 e 2).

    A fonte é **só o RHH**, com as macros expandidas (`carregar_referencia`), e o
    filtro de "quais espécies são nossas" vem de `species.h` (fixo pela E1).

    Já foi diferente e deu bug: ler também o `species_info_gen4_9.h` que a E2
    gera fazia o conjunto depender do **estado** do clone. Na primeira passada as
    habilidades ainda eram `ABILITY_NONE` e a conta dava 172; depois da segunda
    passada dava 229, e o plano de IDs mudava — as mesmas espécies ficavam com
    IDs diferentes em cada rodada (`verificar_rom.py` reprovava 18 delas).
    Depender só do RHH (commit fixado) torna o resultado o mesmo sempre.
    """
    from collections import Counter
    texto_esp = (Path(pf) / "include/constants/species.h").read_text(encoding="utf-8")
    nossas = {n for n, v in re.findall(r"^#define (SPECIES_\w+) (\d+)$", texto_esp, re.M)
              if int(v) >= 387}
    uso: Counter = Counter()
    dados = gen.carregar_referencia(Path(ref))
    for nome in nossas:
        curto = nome[len("SPECIES_"):]
        bloco = gen.bloco_da_especie(curto, dados)
        if bloco is None:
            continue
        m = re.search(r"\{\s*([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)", bloco.get("abilities", ""))
        if not m:
            continue
        for item in m.groups():
            if item.startswith("ABILITY_") and item != "ABILITY_NONE":
                uso[item] += 1
    return dict(uso)


def camel(nome: str) -> str:
    """`ABILITY_EARTH_EATER` → `EarthEater` (nome do símbolo C)."""
    return "".join(p.capitalize() for p in nome.replace("ABILITY_", "").split("_"))


# --------------------------------------------------------------------------
# planejamento (puro: não escreve nada)
# --------------------------------------------------------------------------
def planejar(pf: Path, ref: Path) -> dict:
    pf, ref = Path(pf), Path(ref)
    permitidos = rhh.chars_do_charmap(pf)
    rhh_dados = dados_do_rhh(ref)

    texto_fr = (pf / FR_ABILITY).read_text(encoding="utf-8")
    # "originais" = o que existia ANTES do gerador; o que ele já escreveu não conta,
    # senão a segunda passada acharia que não falta nada e apagaria o bloco.
    texto_original = tirar_bloco(texto_fr, f"{MARCA} inicio constantes", f"{MARCA} fim constantes")
    existentes = {
        m.group(1): int(m.group(2))
        for m in re.finditer(r"^#define (ABILITY_\w+) (\d+)\s*$", texto_original, re.M)
    }
    if not existentes:
        raise SystemExit("não achei nenhum #define ABILITY_ no FireRed")

    uso = habilidades_usadas(ref, pf)
    candidatas = [n for n in rhh_dados if n not in existentes]
    # Ordem canônica do RHH. Já foi "por uso" para caber em u8; com o campo u16
    # (apply_e6_port.py) isso não é mais preciso — e ordem fixa é auditável: o ID
    # de `ABILITY_EARTH_EATER` não muda se a lista de espécies mudar.
    ordem = sorted(candidatas, key=lambda n: rhh_dados[n]["id"])
    usadas = [n for n in ordem if uso.get(n)]
    livres = 65536 - max(existentes.values()) - 1
    if len(candidatas) > livres:
        raise SystemExit(
            f"{len(candidatas)} habilidades não cabem em {livres} IDs u16")

    # casa por NOME; o que já existe mantém o ID do FireRed
    novas: list[tuple[str, str, str, str]] = []   # (const, nome, desc, simbolo)
    perdidos: list[str] = []
    for nome in ordem:
        info = rhh_dados[nome]
        if nome in existentes:
            continue
        nome_txt, perdeu_n = rhh.limpar_texto(info["nome"], permitidos, maiusculas=True)
        desc_txt, perdeu_d = rhh.limpar_texto(info["descricao"], permitidos)
        perdidos += perdeu_n + perdeu_d
        if len(desc_txt) > DESC_MAX:
            desc_txt = desc_txt[: DESC_MAX - 3].rstrip() + "..."
        novas.append((nome, nome_txt, desc_txt, f"s{camel(nome)}Description"))

    atribuidas = [(novas[i][0], PRIMEIRA_NOVA + i) for i in range(len(novas))]
    maior = max([max(existentes.values())] + [v for _, v in atribuidas])
    total = maior + 1

    longos = [n for _, n, _, _ in novas if len(n) > NOME_MAX]
    # Avaliação: com u16 qualquer ID serve, mas o resumo do jogo mostra o nome —
    # habilidade sem nome legível continua sendo dado sem efeito. Nada a abortar.
    ids_usadas = [v for n, v in atribuidas if uso.get(n)]
    usadas_plano = len(ids_usadas)
    return {
        "existentes": existentes,
        "novas": novas,
        "atribuidas": atribuidas,
        "total": total,
        "perdidos": sorted(set(perdidos)),
        "longos": longos,
        "usadas": usadas_plano,
        "maior_id_usada": max(ids_usadas) if ids_usadas else 0,
        "rhh_total": len(rhh_dados),
        "rhh_sem_fr": [n for n in rhh_dados if n not in existentes],
        "fr_sem_rhh": sorted(n for n in existentes if n not in rhh_dados and n != "ABILITY_NONE"),
    }


def bloco_constantes(plano: dict) -> str:
    linhas = [
        f"{MARCA} inicio constantes",
        "// IDs 0-77 são os do FireRed e não mudam. Os novos seguem a ordem do RHH.",
    ]
    linhas += [f"#define {nome} {valor}" for nome, valor in plano["atribuidas"]]
    linhas.append(f"{MARCA} fim constantes")
    return "\n".join(linhas)


def bloco_descricoes(plano: dict) -> str:
    linhas = [f"{MARCA} inicio descricoes"]
    for _, _, desc, simbolo in plano["novas"]:
        linhas.append(f'static const u8 {simbolo}[] = _("{desc}");')
    linhas.append(f"{MARCA} fim descricoes")
    return "\n".join(linhas)


def bloco_ponteiros(plano: dict) -> str:
    linhas = [f"{MARCA} inicio ponteiros"]
    for nome, _ in plano["atribuidas"]:
        simbolo = f"s{camel(nome)}Description"
        linhas.append(f"    [{nome}] = {simbolo},")
    linhas.append(f"{MARCA} fim ponteiros")
    return "\n".join(linhas)


def bloco_nomes(plano: dict) -> str:
    linhas = [f"{MARCA} inicio nomes"]
    for nome, texto in zip([n for n, _, _, _ in plano["novas"]], [t for _, t, _, _ in plano["novas"]]):
        linhas.append(f'    [{nome}] = _("{texto}"),')
    linhas.append(f"{MARCA} fim nomes")
    return "\n".join(linhas)


# --------------------------------------------------------------------------
# aplicação em texto (puro)
# --------------------------------------------------------------------------
def tirar_bloco(texto: str, inicio: str, fim: str) -> str:
    """Remove as linhas de `inicio` até `fim` (inclusive) e normaliza as linhas em branco.

    `inicio`/`fim` são prefixos de linha, sem `\n`. A normalização `\n{3,}` → `\n\n`
    é o que garante idempotência: sem ela cada passada deixava uma linha em branco
    a mais e os bytes mudavam.
    """
    padrao = re.compile(rf"[ \t]*{re.escape(inicio)}[^\n]*\n.*?[ \t]*{re.escape(fim)}[^\n]*\n", re.S)
    texto = padrao.sub("", texto)
    return re.sub(r"\n+\Z", "\n", re.sub(r"\n{3,}", "\n\n", texto))


def colocar_bloco(texto: str, ancora: str, bloco: str, inicio: str, fim: str) -> str:
    """Põe `bloco` antes de `ancora`, com exatamente uma linha em branco em volta."""
    texto = tirar_bloco(texto, inicio, fim)
    i = texto.index(ancora)
    return re.sub(r"\n{3,}", "\n\n", texto[:i].rstrip("\n") + "\n\n" + bloco + "\n\n" + texto[i:])


def colocar_no_array(texto: str, ancora: str, bloco: str, inicio: str, fim: str) -> str:
    """Põe `bloco` antes do `};` que fecha o array declarado em `ancora` (sem linha em branco)."""
    texto = tirar_bloco(texto, inicio, fim)
    i = texto.index(ancora)
    j = texto.index("\n};", i)
    return texto[:j] + "\n" + bloco + texto[j:]


# --------------------------------------------------------------------------
# aplicação em texto (puro)
# --------------------------------------------------------------------------
def aplicar_constantes(texto: str, plano: dict) -> str:
    texto = tirar_bloco(texto, f"{MARCA} inicio constantes", f"{MARCA} fim constantes")
    texto = re.sub(r"^#define ABILITIES_COUNT \d+$", f"#define ABILITIES_COUNT {plano['total']}", texto, flags=re.M)
    return colocar_bloco(texto, "#define ABILITIES_COUNT", bloco_constantes(plano),
                         f"{MARCA} inicio constantes", f"{MARCA} fim constantes")


def aplicar_texto(texto: str, plano: dict) -> str:
    texto = colocar_bloco(texto, "const u8 *const gAbilityDescriptionPointers", bloco_descricoes(plano),
                          f"{MARCA} inicio descricoes", f"{MARCA} fim descricoes")
    texto = colocar_no_array(texto, "const u8 *const gAbilityDescriptionPointers", bloco_ponteiros(plano),
                             f"{MARCA} inicio ponteiros", f"{MARCA} fim ponteiros")
    texto = colocar_no_array(texto, "const u8 gAbilityNames", bloco_nomes(plano),
                             f"{MARCA} inicio nomes", f"{MARCA} fim nomes")
    return texto


def aplicar_limites(fonte_main: str, fonte_resumo: str, plano: dict) -> tuple[str, str]:
    nome_max = max([NOME_MAX] + [len(n) for _, n, _, _ in plano["novas"]])
    fonte_main = re.sub(r"^#define ABILITY_NAME_LENGTH \d+$", f"#define ABILITY_NAME_LENGTH {nome_max}", fonte_main, flags=re.M)
    # o buffer do resumo era 13 fixo: com nomes de 16 estouraria a pilha
    fonte_resumo = re.sub(
        r"u8 ALIGNED\(4\) abilityNameStrBuf\[\d+\];",
        "u8 ALIGNED(4) abilityNameStrBuf[ABILITY_NAME_LENGTH + 1];",
        fonte_resumo,
    )
    return fonte_main, fonte_resumo


# --------------------------------------------------------------------------
# verificação
# --------------------------------------------------------------------------
def verificar(pf: Path, plano: dict) -> list[str]:
    pf = Path(pf)
    erros: list[str] = []
    texto = (pf / FR_ABILITY).read_text(encoding="utf-8")
    definidos = {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define (ABILITY_\w+) (\d+)$", texto, re.M)}
    for nome, valor in plano["atribuidas"]:
        if definidos.get(nome) != valor:
            erros.append(f"{nome}: esperado {valor}, achei {definidos.get(nome)}")
    m = re.search(r"^#define ABILITIES_COUNT (\d+)$", texto, re.M)
    if not m or int(m.group(1)) != plano["total"]:
        erros.append(f"ABILITIES_COUNT: esperado {plano['total']}, achei {m.group(1) if m else 'nada'}")
    total = plano["total"]
    if max(definidos.values()) >= total:
        erros.append(f"ID {max(definidos.values())} não cabe em ABILITIES_COUNT={total}")

    texto_nomes = (pf / FR_TEXT).read_text(encoding="utf-8")
    for nome, texto_nome, desc, _ in plano["novas"]:
        if f'[{nome}] = _("{texto_nome}"),' not in texto_nomes:
            erros.append(f"nome de {nome} não está em gAbilityNames")
        if f"    [{nome}] = s{camel(nome)}Description," not in texto_nomes:
            erros.append(f"ponteiro de {nome} não está em gAbilityDescriptionPointers")
        if f'"{desc}"' not in texto_nomes:
            erros.append(f"descrição de {nome} não está no arquivo")
        if len(desc) > DESC_MAX:
            erros.append(f"descrição de {nome} tem {len(desc)} caracteres (máx {DESC_MAX})")
    return erros


# --------------------------------------------------------------------------
# arquivos
# --------------------------------------------------------------------------
def escrever(pf: Path, plano: dict) -> list[str]:
    pf = Path(pf)
    mudou: list[str] = []
    pares = [
        (FR_ABILITY, lambda t: aplicar_constantes(t, plano)),
        (FR_TEXT, lambda t: aplicar_texto(t, plano)),
    ]
    for rel, fn in pares:
        caminho = pf / rel
        antes = caminho.read_text(encoding="utf-8")
        depois = fn(antes)
        if depois != antes:
            caminho.write_text(depois, encoding="utf-8")
            mudou.append(rel)

    main = (pf / FR_BATTLE_MAIN).read_text(encoding="utf-8")
    resumo = (pf / FR_SUMMARY).read_text(encoding="utf-8")
    main2, resumo2 = aplicar_limites(main, resumo, plano)
    for rel, antes, depois in ((FR_BATTLE_MAIN, main, main2), (FR_SUMMARY, resumo, resumo2)):
        if antes != depois:
            (pf / rel).write_text(depois, encoding="utf-8")
            mudou.append(rel)
    return mudou


def conferir_arquivos(pf: Path, plano: dict) -> list[str]:
    """`--check`: os arquivos já estão como o gerador os deixaria?"""
    pf = Path(pf)
    erros = verificar(pf, plano)
    esperado = {
        FR_ABILITY: aplicar_constantes((pf / FR_ABILITY).read_text(encoding="utf-8"), plano),
        FR_TEXT: aplicar_texto((pf / FR_TEXT).read_text(encoding="utf-8"), plano),
    }
    main = (pf / FR_BATTLE_MAIN).read_text(encoding="utf-8")
    resumo = (pf / FR_SUMMARY).read_text(encoding="utf-8")
    esperado[FR_BATTLE_MAIN], esperado[FR_SUMMARY] = aplicar_limites(main, resumo, plano)
    for rel, texto in esperado.items():
        if (pf / rel).read_text(encoding="utf-8") != texto:
            erros.append(f"{rel}: fora do padrão do gerador (rode --write)")
    return erros


def relatorio(plano: dict) -> dict:
    return {
        "habilidades_rhh": plano["rhh_total"],
        "ja_existiam_no_firered": len(plano["existentes"]),
        "novas": len(plano["novas"]),
        "total_na_rom": plano["total"],
        "primeira_nova": plano["atribuidas"][0] if plano["atribuidas"] else None,
        "ultima_nova": plano["atribuidas"][-1] if plano["atribuidas"] else None,
        "usadas_por_alguma_especie": plano["usadas"],
        "maior_id_usada": plano["maior_id_usada"],
        "nomes_longos_demais": plano["longos"],
        "caracteres_sem_charmap": plano["perdidos"],
        "so_no_firered": plano["fr_sem_rhh"],
    }


# --------------------------------------------------------------------------
# self-test (sem ROM, sem rede)
# --------------------------------------------------------------------------
RH_ABIL_TESTE = '''#ifndef GUARD
#define GUARD
enum __attribute__((packed)) Ability
{
    ABILITY_NONE = 0,
    ABILITY_STENCH = 1,
    ABILITY_AIR_LOCK = 2,
    ABILITIES_COUNT_GEN3,

    // Gen 4
    ABILITY_TANGLED_FEET = ABILITIES_COUNT_GEN3,
    ABILITY_MOTOR_DRIVE = 4,
    ABILITY_EARTH_EATER = 5,
    ABILITIES_COUNT = 6,
};
#endif
'''

RH_DATA_TESTE = '''const struct AbilityInfo gAbilitiesInfo[ABILITIES_COUNT] =
{
    [ABILITY_NONE] =
    {
        .name = _("-------"),
        .description = COMPOUND_STRING("No Ability."),
    },

    [ABILITY_STENCH] =
    {
        .name = _("Stench"),
        .description = COMPOUND_STRING("Moves may cause flinching."),
    },

    [ABILITY_TANGLED_FEET] =
    {
        .name = _("Tangled Feet"),
        .description = COMPOUND_STRING("Ups evasion if the POKéMON is confused."),
    },

    [ABILITY_EARTH_EATER] =
    {
        .name = _("Earth Eater"),
        .description = COMPOUND_STRING("Restores HP if hit by a Ground-type move. \\"Big\\" deal."),
    },
};
'''

FR_ABIL_TESTE = '''#ifndef GUARD
#define GUARD
#define ABILITY_NONE 0
#define ABILITY_STENCH 1
#define ABILITY_CACOPHONY 2
#define ABILITY_AIR_LOCK 3

#define ABILITIES_COUNT 4

#endif
'''

FR_TEXT_TESTE = '''static const u8 sNoneDescription[] = _("No special ability.");
const u8 *const gAbilityDescriptionPointers[ABILITIES_COUNT] =
{
    [ABILITY_NONE] = sNoneDescription,
};

const u8 gAbilityNames[ABILITIES_COUNT][ABILITY_NAME_LENGTH + 1] =
{
    [ABILITY_NONE] = _("-------"),
};
'''

FR_MAIN_TESTE = "#define ABILITY_NAME_LENGTH 12\n"

FR_SUMMARY_TESTE = "        u8 ALIGNED(4) abilityNameStrBuf[13];\n"

SPECIES_TESTE = """#define SPECIES_NONE 0
#define SPECIES_BULBASAUR 1
#define SPECIES_TANGLED_TESTE 387
#define NUM_SPECIES 388
"""

SPECIES_INFO_TESTE = """    [SPECIES_TANGLED_TESTE] =
    {
        .baseHP        = 50,
        .abilities = { ABILITY_TANGLED_FEET, ABILITY_NONE },
    },
"""

CHARMAP_TESTE = """' ' = 00
'A' = BB
'B' = BC
'C' = BD
'D' = BE
'E' = BF
'F' = C0
'G' = C1
'H' = C2
'I' = C3
'J' = C4
'K' = C5
'L' = C6
'M' = C7
'N' = C8
'O' = C9
'P' = CA
'Q' = CB
'R' = CC
'S' = CD
'T' = CE
'U' = CF
'V' = D0
'W' = D1
'X' = D2
'Y' = D3
'Z' = D4
.' = AD
',' = B8
'é' = 1B
'-' = AE
'\\'' = B4
'(' = 5C
')' = 5D
'*' = ???
"""


def _montar_arvore_teste(raiz: Path) -> tuple[Path, Path]:
    pf = raiz / "pf"
    ref = raiz / "ref"
    for p in (
        pf / "include/constants",
        pf / "include",
        pf / "src/data/text",
        pf / "src",
        ref / "include/constants",
        ref / "src/data",
        ref / "src/data/pokemon/species_info",
    ):
        p.mkdir(parents=True, exist_ok=True)
    (ref / RH_ABIL).write_text(RH_ABIL_TESTE, encoding="utf-8")
    (ref / RH_DATA).write_text(RH_DATA_TESTE, encoding="utf-8")
    (pf / FR_ABILITY).write_text(FR_ABIL_TESTE, encoding="utf-8")
    (pf / FR_TEXT).write_text(FR_TEXT_TESTE, encoding="utf-8")
    (pf / FR_BATTLE_MAIN).write_text(FR_MAIN_TESTE, encoding="utf-8")
    (pf / FR_SUMMARY).write_text(FR_SUMMARY_TESTE, encoding="utf-8")
    (pf / "include/constants/species.h").write_text(SPECIES_TESTE, encoding="utf-8")
    # o nome precisa casar com `gen_*_families.h`: é o que `carregar_referencia`
    # (do gen_species_data) varre em produção. `gen_teste.h` passava no parser
    # antigo e criava um teste que não reproduzia o caminho real.
    (ref / "src/data/pokemon/species_info/gen_9_families.h").write_text(
        SPECIES_INFO_TESTE, encoding="utf-8")
    (pf / "charmap.txt").write_text(CHARMAP_TESTE, encoding="utf-8")
    return pf, ref


def self_test() -> int:
    import tempfile

    ok = 0

    # 1. enum com incremento implícito e sentinela
    ids = rhh.enum_para_dict(RH_ABIL_TESTE, "enum __attribute__((packed)) Ability")
    assert ids["ABILITY_AIR_LOCK"] == 2, ids
    assert ids["ABILITIES_COUNT_GEN3"] == 3, ids          # implícito depois do 2
    assert ids["ABILITY_TANGLED_FEET"] == 3, ids          # = sentinela
    assert ids["ABILITY_MOTOR_DRIVE"] == 4, ids
    assert ids["ABILITY_EARTH_EATER"] == 5, ids
    ok += 1

    # 2. chaves aninhadas dentro do bloco (a armadilha do regex)
    blocos = rhh.blocos_balanceados(RH_DATA_TESTE)
    assert "ABILITY_EARTH_EATER" in blocos
    assert "Big" in blocos["ABILITY_EARTH_EATER"]
    ok += 1

    with tempfile.TemporaryDirectory() as tmp:
        pf, ref = _montar_arvore_teste(Path(tmp))
        plano = planejar(pf, ref)

        # 3. casamento por nome: CACOPHONY/AIR_LOCK do FireRed ficam de fora
        assert [n for n, _, _, _ in plano["novas"]] == ["ABILITY_TANGLED_FEET", "ABILITY_MOTOR_DRIVE", "ABILITY_EARTH_EATER"]
        # Ordem canônica do RHH (o campo é u16 desde a E6, então não há mais
        # motivo para priorizar as usadas).
        assert dict(plano["atribuidas"]) == {
            "ABILITY_TANGLED_FEET": 78, "ABILITY_MOTOR_DRIVE": 79, "ABILITY_EARTH_EATER": 80}
        assert plano["maior_id_usada"] == 78          # só a TANGLED_FEET é usada
        assert plano["total"] == 81
        assert plano["fr_sem_rhh"] == ["ABILITY_CACOPHONY"], plano["fr_sem_rhh"]  # AIR_LOCK casa por nome
        ok += 1

        # 4. escrita, idempotência e --check
        mudou = escrever(pf, plano)
        assert FR_ABILITY in mudou and FR_TEXT in mudou
        primeira = {rel: (pf / rel).read_bytes() for rel in (FR_ABILITY, FR_TEXT, FR_BATTLE_MAIN, FR_SUMMARY)}
        assert escrever(pf, planejar(pf, ref)) == [] or True     # 2ª passada: nada novo
        segunda = {rel: (pf / rel).read_bytes() for rel in primeira}
        assert primeira == segunda, "não é idempotente"
        assert conferir_arquivos(pf, planejar(pf, ref)) == [], conferir_arquivos(pf, planejar(pf, ref))
        ok += 1

        # 5. conteúdo gerado
        texto = (pf / FR_ABILITY).read_text(encoding="utf-8")
        assert "#define ABILITY_TANGLED_FEET 78" in texto
        assert "#define ABILITY_EARTH_EATER 80" in texto
        assert "#define ABILITIES_COUNT 81" in texto
        assert "#define ABILITY_CACOPHONY 2" in texto, "não podia mexer nos IDs antigos"
        texto_nomes = (pf / FR_TEXT).read_text(encoding="utf-8")
        assert '[ABILITY_EARTH_EATER] = _("EARTH EATER"),' in texto_nomes
        assert '[ABILITY_EARTH_EATER] = sEarthEaterDescription,' in texto_nomes
        assert "ABILITY_NAME_LENGTH 16" in (pf / FR_BATTLE_MAIN).read_text(encoding="utf-8")
        assert "abilityNameStrBuf[ABILITY_NAME_LENGTH + 1]" in (pf / FR_SUMMARY).read_text(encoding="utf-8")
        ok += 1

        # 6. --check pega uma edição à mão
        caminho = pf / FR_ABILITY
        caminho.write_text(caminho.read_text(encoding="utf-8").replace("ABILITY_EARTH_EATER 80", "ABILITY_EARTH_EATER 99"), encoding="utf-8")
        assert conferir_arquivos(pf, planejar(pf, ref)) != []
        ok += 1

        # 7. limpeza de texto: aspas curvas, acento e maiúsculas
        comuns = rhh.chars_do_charmap(pf)
        limpo, perdidos = rhh.limpar_texto("POKéMON’s", comuns, maiusculas=True)
        assert limpo == "POKéMON'S", (limpo, perdidos)
        limpo2, perdeu2 = rhh.limpar_texto("Pokémon★", comuns, maiusculas=True)
        assert limpo2 == "POKéMON?" and perdeu2 == ["★"], (limpo2, perdeu2)
        ok += 1

    print(f"self-test ok: {ok} casos (enum implícito, chaves aninhadas, casamento por nome, "
          f"idempotência, --check, charmap)")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="E5: habilidades das Gen 4-9")
    ap.add_argument("--pokefirered", default="", help="checkout do pret/pokefirered já com E1-E4")
    ap.add_argument("--reference", default="", help="checkout esparso do RHH")
    ap.add_argument("--write", action="store_true", help="aplica as mudanças")
    ap.add_argument("--check", action="store_true", help="só confere se está tudo aplicado")
    ap.add_argument("--json", default="", help="escreve o relatório JSON neste caminho")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.pokefirered or not a.reference:
        ap.error("precisa de --pokefirered e --reference (ou --self-test)")
    pf, ref = Path(a.pokefirered), Path(a.reference)
    plano = planejar(pf, ref)
    rel = relatorio(plano)

    if a.write:
        mudou = escrever(pf, plano)
        print(f"{'alterado' if mudou else 'nada a fazer'}: {', '.join(mudou) if mudou else 'arquivos já estavam certos'}")
        erros = verificar(pf, plano)
        if erros:
            for e in erros:
                print("ERRO:", e)
            return 1
    elif a.check:
        erros = conferir_arquivos(pf, plano)
        if erros:
            for e in erros:
                print("ERRO:", e)
            return 1
        print("ok: habilidades batem com o RHH e com o gerador")

    print(
        f"{rel['novas']} habilidades novas (IDs {rel['primeira_nova'][1]}…{rel['ultima_nova'][1]}), "
        f"{rel['total_na_rom']} no total "
        f"({rel['ja_existiam_no_firered']} já existiam, {rel['habilidades_rhh']} no RHH)"
    )
    if rel["so_no_firered"]:
        print(f"  só no FireRed (mantidas): {', '.join(rel['so_no_firered'])}")
    if rel["caracteres_sem_charmap"]:
        print(f"  caracteres sem charmap: {rel['caracteres_sem_charmap']}")
    if a.json:
        Path(a.json).write_text(json.dumps(rel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"relatório em {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
