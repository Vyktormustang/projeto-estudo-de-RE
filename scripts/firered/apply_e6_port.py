#!/usr/bin/env python3
"""E6, passo 0: alarga o ID de habilidade de `u8` para `u16`.

Por que isso é necessário
-------------------------
Com as 321 habilidades da E5, **229** são usadas por alguma das 639 espécies
novas. Só existem 178 IDs livres abaixo de 256 (0-77 são do FireRed) — não cabe.

Na E5 a saída foi ordenar as IDs **por uso** e deixar as 71 órfãs acima de 255.
Funcionou enquanto o parser não via as espécies montadas por macro; quando ele
passou a ver, o conjunto de "usadas" cresceu e 18 espécies ficaram com o byte
truncado — `PALAFIN` com `ABILITY_ZERO_TO_HERO` (299) virou `ABILITY_...` (43).
Truncar em silêncio é o pior tipo de bug: o jogo roda e a habilidade é outra.

Por que é seguro
----------------
A habilidade **não é gravada no save**: `GetMonAbility()` deriva de
`gSpeciesInfo[species].abilities[abilityNum]`. Então mudar o layout de
`SpeciesInfo` e de `BattlePokemon` não invalida save nenhum.

O que muda
----------
| arquivo                          | mudança                                        |
|----------------------------------|------------------------------------------------|
| `include/pokemon.h`              | `SpeciesInfo.abilities[2]`: u8 -> u16          |
| `include/pokemon.h`              | `BattlePokemon.ability`: u8 -> u16             |
| `include/pokemon.h`              | `GetAbilityBySpecies`/`GetMonAbility` -> u16   |
| `src/pokemon.c`                  | as duas definições                             |
| `src/battle_ai_switch_items.c`   | `monAbility` (2x) -> u16                       |
| `src/battle_script_commands.c`   | `ability` local do Heal Bell -> u16            |
| `src/wild_encounter.c`           | `ability = GetMonAbility(...)` -> u16          |

O `SpeciesInfo` **continua com 28 bytes** (0x16 + 4 = 0x1A para
`safariZoneFleeRate`, 0x1B `bodyColor`, sizeof 0x1C = 28). O `BattlePokemon`
muda de passo (0x58 -> outro) e os offsets depois de `ability` andam 2 bytes:
quem lê a RAM precisa medir com `offsets.py` (o `nav.py` já aceita `PF_OFFSETS`).

Uso
---
    python3 scripts/firered/apply_e6_port.py --self-test
    python3 scripts/firered/apply_e6_port.py --pokefirered /tmp/pokefirered
    python3 scripts/firered/apply_e6_port.py --pokefirered /tmp/pokefirered --check
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MARCA = "E6: habilidade u16"

# (arquivo, texto procurado, texto novo, quantas vezes tem de casar)
MUDANCAS: list[tuple[str, str, str, int]] = [
    ("include/pokemon.h",
     " /* 0x16 */ u8 abilities[2];",
     " /* 0x16 */ u16 abilities[2];",
     1),
    ("include/pokemon.h",
     "    /*0x20*/ u8 ability;",
     "    /*0x20*/ u16 ability;",
     1),
    ("include/pokemon.h",
     "u8 GetAbilityBySpecies(u16 species, bool8 abilityNum);",
     "u16 GetAbilityBySpecies(u16 species, bool8 abilityNum);",
     1),
    ("include/pokemon.h",
     "u8 GetMonAbility(struct Pokemon *mon);",
     "u16 GetMonAbility(struct Pokemon *mon);",
     1),
    ("src/pokemon.c",
     "u8 GetAbilityBySpecies(u16 species, bool8 abilityNum)",
     "u16 GetAbilityBySpecies(u16 species, bool8 abilityNum)",
     1),
    ("src/pokemon.c",
     "u8 GetMonAbility(struct Pokemon *mon)",
     "u16 GetMonAbility(struct Pokemon *mon)",
     1),
    ("src/battle_ai_switch_items.c",
     "        u8 monAbility;",
     "        u16 monAbility;",
     2),
    ("src/battle_script_commands.c",
     "                u8 ability;\n\n                if (gBattlerPartyIndexes[gBattlerAttacker] == i)",
     "                u16 ability;\n\n                if (gBattlerPartyIndexes[gBattlerAttacker] == i)",
     1),
    ("src/wild_encounter.c",
     "        u8 ability = GetMonAbility(&gPlayerParty[0]);",
     "        u16 ability = GetMonAbility(&gPlayerParty[0]);",
     1),
    # `AbilityBattleEffects` recebe a habilidade como 3o parametro. Era u8: com
    # ID 298 (EARTH EATER) ele truncava para 42 e o switch caia em outra
    # habilidade — a prova da E5 passou a REPROVAR depois da E6, e a causa era
    # esta. Alargar aqui cobre tambem as macros ABILITY_ON_FIELD/ON_OPPOSING_FIELD.
    ("include/battle_util.h",
     "u8 AbilityBattleEffects(u8 caseID, u8 battler, u8 ability, u8 special, u16 moveArg);",
     "u8 AbilityBattleEffects(u8 caseID, u8 battler, u16 ability, u8 special, u16 moveArg);",
     1),
    ("src/battle_util.c",
     "u8 AbilityBattleEffects(u8 caseID, u8 battler, u8 ability, u8 special, u16 moveArg)",
     "u8 AbilityBattleEffects(u8 caseID, u8 battler, u16 ability, u8 special, u16 moveArg)",
     1),
    # ---- mais carregadores de ID de habilidade que eram u8.
    # Cada um deles trunca em silêncio: a habilidade "vira" outra e o jogo mostra
    # o nome errado / aplica o efeito errado. Foram descobertos um a um, porque
    # cada um só aparece num caminho diferente do motor:
    #   gLastUsedAbility  -> é o valor que o case ABSORBING lê (foi o que fez a
    #                        prova da E5 REPROVAR depois da E6)
    #   lastAbility/abilities[4] do BattleMsgData -> nome na mensagem de batalha
    #   sBattlerAbilities  -> idem (buffer usado pelo B_TXT_*_ABILITY)
    #   BattleHistory.abilities + RecordAbilityBattle -> AI
    ("include/battle.h",
     "extern u8 gLastUsedAbility;",
     "extern u16 gLastUsedAbility;", 1),
    ("src/battle_main.c",
     "EWRAM_DATA u8 gLastUsedAbility = 0;",
     "EWRAM_DATA u16 gLastUsedAbility = 0;", 1),
    ("include/battle_message.h",
     "    u8 lastAbility;",
     "    u16 lastAbility;", 1),
    ("include/battle_message.h",
     "    u8 abilities[4];",
     "    u16 abilities[4];", 1),
    ("src/battle_message.c",
     "static EWRAM_DATA u8 sBattlerAbilities[MAX_BATTLERS_COUNT] = {};",
     "static EWRAM_DATA u16 sBattlerAbilities[MAX_BATTLERS_COUNT] = {};", 1),
    ("include/battle.h",
     "    /*0x20*/ u8 abilities[MAX_BATTLERS_COUNT / 2];",
     "    /*0x20*/ u16 abilities[MAX_BATTLERS_COUNT / 2];", 1),
    ("include/battle.h",
     "    u8 abilities[MAX_BATTLERS_COUNT];",
     "    u16 abilities[MAX_BATTLERS_COUNT];", 1),
    ("include/battle_ai_script_commands.h",
     "void RecordAbilityBattle(u8 bank, u8 abilityId);",
     "void RecordAbilityBattle(u8 bank, u16 abilityId);", 1),
    ("src/battle_ai_script_commands.c",
     "void RecordAbilityBattle(u8 battlerId, u8 abilityId)",
     "void RecordAbilityBattle(u8 battlerId, u16 abilityId)", 1),
    # Skill Swap/Entrainment (linha ~9012): copia a habilidade para uma variável
    # temporária antes de trocar as duas; se fosse u8, trocaria o byte truncado.
    ("src/battle_script_commands.c",
     "        u8 abilityAtk = gBattleMons[gBattlerAttacker].ability;",
     "        u16 abilityAtk = gBattleMons[gBattlerAttacker].ability;",
     1),
]


def _ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8", errors="surrogateescape")


def _gravar(caminho: Path, texto: str) -> None:
    caminho.write_text(texto, encoding="utf-8", errors="surrogateescape")


def ja_aplicado(pf: Path) -> bool:
    texto = _ler(pf / "include/pokemon.h")
    return "u16 abilities[2]" in texto and "u16 ability;" in texto


def faltando(pf: Path) -> list[str]:
    """Quais mudanças ainda NÃO foram feitas (o texto antigo ainda está lá)."""
    pendentes = []
    for arquivo, antigo, _, vezes in MUDANCAS:
        if _ler(pf / arquivo).count(antigo) == vezes:
            pendentes.append(f"{arquivo}: falta trocar {antigo.strip()!r}")
    return pendentes


def quantidades_erradas(pf: Path) -> list[str]:
    """Texto antigo presente, mas em quantidade inesperada (arquivo mudou)."""
    erros = []
    for arquivo, antigo, _, vezes in MUDANCAS:
        achados = _ler(pf / arquivo).count(antigo)
        if 0 < achados != vezes:
            erros.append(f"{arquivo}: esperava {vezes}x {antigo.strip()!r}, "
                         f"achei {achados}")
    return erros


def aplicar(pf: Path) -> list[str]:
    """Aplica as mudanças que ainda faltam, arquivo por arquivo.

    Idempotência é **por mudança**, não por arquivo: a primeira versão pulava o
    arquivo inteiro ao ver a marca no fim e, quando uma mudança nova entrou na
    lista (`abilityAtk`), ela nunca era aplicada em quem já tinha a marca.
    """
    feitos: list[str] = []
    por_arquivo: dict[str, list[tuple[str, str, int]]] = {}
    for arquivo, antigo, novo, vezes in MUDANCAS:
        por_arquivo.setdefault(arquivo, []).append((antigo, novo, vezes))

    for arquivo, itens in sorted(por_arquivo.items()):
        caminho = pf / arquivo
        texto = _ler(caminho)
        marcado = f"// {MARCA}" in texto
        quantas = 0
        for antigo, novo, vezes in itens:
            achados = texto.count(antigo)
            if achados == 0:
                continue                      # essa já foi
            if achados != vezes:
                raise SystemExit(f"{arquivo}: esperava {vezes} ocorrência(s) de "
                                 f"{antigo.strip()!r}, achei {achados}")
            texto = texto.replace(antigo, novo)
            quantas += 1
        if quantas:
            if not marcado:
                # comentário no fim do arquivo: não mexe em linha nenhuma
                texto += (f"\n// {MARCA}: IDs de habilidade passam de 255 "
                          f"(ver apply_e6_port.py)\n")
            _gravar(caminho, texto)
            feitos.append(f"{arquivo} ({quantas} mudança(s))")
    return feitos


def conferir(pf: Path) -> list[str]:
    """Confere o resultado, incluindo o que NÃO pode ter sobrado."""
    erros: list[str] = []
    texto = _ler(pf / "include/pokemon.h")
    if "u16 abilities[2]" not in texto:
        erros.append("SpeciesInfo.abilities ainda não é u16")
    if "    /*0x20*/ u16 ability;" not in texto:
        erros.append("BattlePokemon.ability ainda não é u16")
    if re.search(r"^u8 GetAbilityBySpecies", texto, re.M):
        erros.append("declaração de GetAbilityBySpecies ainda é u8")
    if re.search(r"^u8 GetAbilityBySpecies", _ler(pf / "src/pokemon.c"), re.M):
        erros.append("definição de GetAbilityBySpecies ainda é u8")
    if re.search(r"AbilityBattleEffects\(u8 caseID, u8 battler, u8 ability", texto):
        erros.append("declaração de AbilityBattleEffects ainda recebe u8")
    if re.search(r"AbilityBattleEffects\(u8 caseID, u8 battler, u8 ability",
                 _ler(pf / "src/battle_util.c")):
        erros.append("definição de AbilityBattleEffects ainda recebe u8")

    # quem recebe `.ability` numa variável u8 trunca de novo, em silêncio
    for arquivo in ("src/battle_script_commands.c", "src/battle_ai_switch_items.c",
                    "src/wild_encounter.c", "src/battle_util.c", "src/pokemon.c"):
        for i, linha in enumerate(_ler(pf / arquivo).splitlines(), 1):
            if re.search(r"^\s*u8 \w+\s*=\s*.*\.ability\b", linha) or \
               re.search(r"^\s*u8 \w+\s*=\s*GetMonAbility", linha):
                erros.append(f"{arquivo}:{i}: variável u8 recebendo habilidade "
                             f"(trunca) -> {linha.strip()}")
    return erros


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
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

    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        for arquivo, antigo, _, vezes in MUDANCAS:
            caminho = raiz / arquivo
            caminho.parent.mkdir(parents=True, exist_ok=True)
            atual = _ler(caminho) if caminho.exists() else ""
            atual += antigo * vezes + "\n"
            _gravar(caminho, atual)
        # um u8 recebendo habilidade: tem de ser pego. APPEND, não overwrite:
        # escrever por cima apagava a assinatura de AbilityBattleEffects que a
        # fixture anterior tinha posto no mesmo arquivo (foi o que quebrou 2 casos).
        _gravar(raiz / "src/battle_util.c",
                _ler(raiz / "src/battle_util.c")
                + "void f(void)\n{\n    u8 x = gBattleMons[0].ability;\n}\n")

        checa("antes: não está aplicado", not ja_aplicado(raiz))
        checa("antes: faltando lista todas", len(faltando(raiz)) == len(MUDANCAS))

        feitos = aplicar(raiz)
        checa("aplicar devolve os arquivos mexidos", len(feitos) == len({m[0] for m in MUDANCAS}))
        checa("depois: marcado como aplicado", ja_aplicado(raiz))
        checa("depois: nada faltando", not faltando(raiz))
        checa("idempotente (2ª passada não mexe)", aplicar(raiz) == [])

        erros = conferir(raiz)
        checa("conferir acusa o u8 que ainda trunca",
              any("battle_util.c" in e for e in erros))

        # sem o u8 solto, passa
        texto_util = _ler(raiz / "src/battle_util.c").replace(
            "u8 x = gBattleMons[0].ability;", "u16 x = gBattleMons[0].ability;")
        _gravar(raiz / "src/battle_util.c", texto_util)
        checa("conferir aceita quando não há truncamento", conferir(raiz) == [])

        # guarda de quantidade: duas ocorrências esperadas, uma encontrada
        with tempfile.TemporaryDirectory() as d2:
            r2 = Path(d2)
            for arquivo, antigo, _, vezes in MUDANCAS:
                caminho = r2 / arquivo
                caminho.parent.mkdir(parents=True, exist_ok=True)
                atual = _ler(caminho) if caminho.exists() else ""
                atual += antigo * vezes + "\n"
                _gravar(caminho, atual)
            cam = r2 / "src/battle_ai_switch_items.c"
            _gravar(cam, _ler(cam).replace("        u8 monAbility;\n", "", 1))
            try:
                aplicar(r2)
                checa("quantidade errada aborta", False)
            except SystemExit:
                checa("quantidade errada aborta", True)

    print(f"\n{ok}/{casos} casos ok")
    return 0 if ok == casos else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    pf = Path(a.pokefirered)
    if a.check:
        if not ja_aplicado(pf):
            print("nada aplicado")
            return 1
        erros = conferir(pf) + faltando(pf) + quantidades_erradas(pf)
        if erros:
            for e in erros:
                print("  - " + e)
            return 1
        print("ok: habilidade é u16 em todos os pontos e nada trunca")
        return 0

    feitos = aplicar(pf)
    if not feitos:
        print("nada a fazer: já aplicado")
        return 0
    print("aplicado: " + "; ".join(feitos))
    erros = conferir(pf)
    if erros:
        for e in erros:
            print("  - " + e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
