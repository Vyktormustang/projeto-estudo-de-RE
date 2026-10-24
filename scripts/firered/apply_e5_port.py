#!/usr/bin/env python3
"""Aplica o gancho de motor da E5: habilidade de Gen 9 funcionando de verdade.

O que ele muda
--------------
Só `src/battle_util.c`: um `case ABILITY_EARTH_EATER` dentro do
`switch (gLastUsedAbility)` de `ABILITYEFFECT_ABSORBING`, colado nos de
Volt Absorb / Water Absorb (que já existiam). Efeito: golpe de tipo Terrestre
não faz dano e cura 1/4 do HP máximo, com a mensagem genérica
`STRINGID_PKMNRESTOREDHPUSING` — que já imprime o nome da habilidade, então
sai "ORTHWORM restored HP using its EARTH EATER!" sem texto novo.

Por que Earth Eater
-------------------
É Gen 9 de verdade, tem espécie no jogo (Orthworm, No968), é verificável em
batalha sem inventar nada e cai num `case` que o FireRed já usa — ou seja, é o
modelo mais barato para as outras 242 habilidades da onda 2.

O resto das habilidades novas **não faz nada** (o `switch` não as trata): é o
mesmo fallback silencioso e seguro da E4, não trava a batalha.

Uso
---
    python3 scripts/firered/apply_e5_port.py --pokefirered /tmp/pokefirered
    python3 scripts/firered/apply_e5_port.py --pokefirered /tmp/pokefirered --check
    python3 scripts/firered/apply_e5_port.py --self-test      # sem clone
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MARCA = "// E5:"
ARQUIVO = "src/battle_util.c"
ANCORA = "                case ABILITY_WATER_ABSORB:"

CASO = """                case ABILITY_EARTH_EATER:
                    // E5: Gen 9. Mesma mecanica do Volt Absorb, mas contra Terrestre.
                    if (moveType == TYPE_GROUND && gBattleMoves[move].power != 0)
                    {
                        if (gProtectStructs[gBattlerAttacker].notFirstStrike)
                            gBattlescriptCurrInstr = BattleScript_MoveHPDrain;
                        else
                            gBattlescriptCurrInstr = BattleScript_MoveHPDrain_PPLoss;

                        effect = 1;
                    }
                    break;
"""


def tirar(texto: str) -> str:
    padrao = re.compile(rf"[ \t]*{re.escape(MARCA)} inicio[^\n]*\n.*?[ \t]*{re.escape(MARCA)} fim[^\n]*\n", re.S)
    return padrao.sub("", texto)


def aplicar(texto: str) -> str:
    texto = tirar(texto)
    if texto.count(ANCORA) != 1:
        raise SystemExit(f"esperava 1 âncora '{ANCORA.strip()}', achei {texto.count(ANCORA)}")
    bloco = f"{MARCA} inicio earth_eater (gerado por apply_e5_port.py)\n" + CASO + f"{MARCA} fim earth_eater\n"
    i = texto.index(ANCORA)
    return texto[:i] + bloco + texto[i:]


def verificar(texto: str) -> list[str]:
    erros = []
    if "case ABILITY_EARTH_EATER:" not in texto:
        erros.append("falta o case ABILITY_EARTH_EATER")
    if texto.count("case ABILITY_EARTH_EATER:") != 1:
        erros.append("case ABILITY_EARTH_EATER duplicado")
    if "moveType == TYPE_GROUND" not in texto:
        erros.append("o case não checa TYPE_GROUND")
    if texto.count("case ABILITY_WATER_ABSORB:") != 1:
        erros.append("o case de Water Absorb sumiu/duplicou")
    return erros


def self_test() -> int:
    base = (
        "void f(void)\n{\n    switch (gLastUsedAbility)\n    {\n"
        "                case ABILITY_VOLT_ABSORB:\n                    break;\n"
        + ANCORA
        + "\n                    if (moveType == TYPE_WATER) { }\n                    break;\n"
        "                }\n}\n"
    )
    ok = 0
    t1 = aplicar(base)
    assert t1.count("case ABILITY_EARTH_EATER:") == 1
    assert t1.index("case ABILITY_EARTH_EATER:") < t1.index(ANCORA)
    ok += 1
    t2 = aplicar(t1)
    assert t1 == t2, "não é idempotente"
    ok += 1
    assert verificar(t2) == [], verificar(t2)
    ok += 1
    assert verificar(base) != []          # sem o case, o verificador acusa
    ok += 1
    assert tirar(t1) == base, "não volta ao original"
    ok += 1
    print(f"self-test ok: {ok} casos (aplicar, idempotência, verificar, reverter)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="E5: gancho de motor (Earth Eater)")
    ap.add_argument("--pokefirered", default="")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.pokefirered:
        ap.error("precisa de --pokefirered (ou --self-test)")
    caminho = Path(a.pokefirered) / ARQUIVO
    original = caminho.read_text(encoding="utf-8")

    if a.check:
        erros = verificar(original)
        for e in erros:
            print("ERRO:", e)
        if erros:
            return 1
        if aplicar(original) != original:
            print("ERRO: arquivo fora do padrão do gerador (rode sem --check)")
            return 1
        print("ok: gancho da E5 aplicado e sem duplicata")
        return 0

    novo = aplicar(original)
    if novo == original:
        print("nada a fazer: gancho já estava aplicado")
    else:
        caminho.write_text(novo, encoding="utf-8")
        print(f"aplicado: {ARQUIVO} (+{len(novo) - len(original)} bytes)")
    erros = verificar(novo)
    for e in erros:
        print("ERRO:", e)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
