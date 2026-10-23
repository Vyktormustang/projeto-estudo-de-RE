#!/usr/bin/env python3
"""ROM de prova da E3: dois golpes de Fada + Dratini selvagem na Rota 1.

Por que isso existe
-------------------
A E3 entrega o **tipo Fada** e o **split físico/especial**, mas o FireRed
vanilla não tem nenhum golpe de Fada: os golpes das Gen 4-9 chegam na E4.
Sem um golpe de Fada não há como provar em batalha nem a efetividade nem a
stat usada no dano. Este script monta uma **ROM de prova** (não a entregue):

| arquivo                             | mudança                                   |
|-------------------------------------|-------------------------------------------|
| `src/data/battle_moves.h`           | `MOVE_SPLASH` → PLAY ROUGH (Fada, físico) |
|                                     | `MOVE_PSYCH_UP` → MOONBLAST (Fada, especial) |
| `src/data/battle_moves_category.h`  | as duas entradas viram PHYSICAL/SPECIAL   |
| `src/data/text/move_names.h`        | nomes "PLAY ROUGH"/"MOONBLAST"            |
| `src/data/wild_encounters.json`     | Rota 1 slot 0 → DRATINI nível 30          |

Os dois golpes têm o **mesmo poder (40)**: contra o mesmo alvo, a diferença de
dano só pode vir da stat usada (Attack×Defense vs SpAttack×SpDefense), que é
exatamente o que o split da E3 muda.

`--reverter` restaura os backups `*.e3prova.bak`; depois é só rebuildar e o hash
volta ao da ROM de referência (o build é reprodutível).

Uso
---
    python3 scripts/firered/prova_batalha_e3.py --self-test
    python3 scripts/firered/prova_batalha_e3.py --pokefirered /tmp/pokefirered --aplicar
    python3 scripts/firered/prova_batalha_e3.py --pokefirered /tmp/pokefirered --check
    python3 scripts/firered/prova_batalha_e3.py --pokefirered /tmp/pokefirered --reverter
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

GOLPES = [
    # (constante, novo nome, categoria, efeito)
    ("MOVE_SPLASH", "PLAY ROUGH", "MOVE_CATEGORY_PHYSICAL"),
    ("MOVE_PSYCH_UP", "MOONBLAST", "MOVE_CATEGORY_SPECIAL"),
]

ARQUIVOS = [
    "src/data/battle_moves.h",
    "src/data/battle_moves_category.h",
    "src/data/text/move_names.h",
    "src/data/wild_encounters.json",
]

SUFIXO_BACKUP = ".e3prova.bak"

# Nível 50: com Sylveon nível 30 os dois golpes (40 BP) deixam o Dratini vivo,
# então dá para medir o dano do físico e do especial no MESMO alvo.
NIVEL_DRATINI = 50


def _bloco_golpe(texto: str, constante: str) -> re.Match:
    padrao = re.compile(r"(\[" + constante + r"\] =\n    \{\n)(.*?)(\n    \},)", re.S)
    m = padrao.search(texto)
    if not m:
        raise SystemExit(f"bloco de {constante} não achado")
    return m


def _encontro_rota1(grupos: list[dict]) -> dict | None:
    """A Rota 1 do **FireRed** (o json tem FireRed e LeafGreen no mesmo grupo).

    Pegar o último MAP_ROUTE1 sem olhar o `base_label` altera a LeafGreen e o
    build (FIRERED) continua com Pidgey — foi o erro da primeira tentativa.
    """
    achados = [enc for grupo in grupos for enc in grupo.get("encounters", [])
               if enc.get("map") == "MAP_ROUTE1"]
    for enc in achados:
        if "FireRed" in enc.get("base_label", ""):
            return enc
    return achados[0] if achados else None


def aplicar(raiz: Path) -> list[str]:
    for rel in ARQUIVOS:
        origem = raiz / rel
        if not origem.exists():
            raise SystemExit(f"falta {origem}")
        backup = origem.with_suffix(origem.suffix + SUFIXO_BACKUP)
        if not backup.exists():
            shutil.copy2(origem, backup)

    mudancas: list[str] = []

    # 1) tabela de golpes: efeito de dano, tipo Fada, poder 40
    p = raiz / "src/data/battle_moves.h"
    texto = p.read_text()
    for constante, _nome, _cat in GOLPES:
        m = _bloco_golpe(texto, constante)
        novo = (
            "        .effect = EFFECT_HIT,\n"
            "        .power = 40,\n"
            "        .type = TYPE_FAIRY,\n"
            "        .accuracy = 100,\n"
            "        .pp = 20,\n"
            "        .secondaryEffectChance = 0,\n"
            "        .target = MOVE_TARGET_SELECTED,\n"
            "        .priority = 0,\n"
            "        .flags = 0,"
        )
        texto = texto[:m.start(2)] + novo + texto[m.end(2):]
        mudancas.append(f"{constante}: EFFECT_HIT 40 BP TYPE_FAIRY")
    p.write_text(texto)

    # 2) categoria do golpe (arquivo gerado pela E3)
    p = raiz / "src/data/battle_moves_category.h"
    texto = p.read_text()
    for constante, _nome, cat in GOLPES:
        antes = re.search(r"^    \[" + constante + r"\] = MOVE_CATEGORY_\w+,$", texto, re.M)
        if not antes:
            raise SystemExit(f"categoria de {constante} não achada")
        texto = texto[:antes.start()] + f"    [{constante}] = {cat}," + texto[antes.end():]
        mudancas.append(f"{constante}: {cat}")
    p.write_text(texto)

    # 3) nomes visíveis
    p = raiz / "src/data/text/move_names.h"
    texto = p.read_text()
    for constante, nome, _cat in GOLPES:
        antes = re.search(r"^    \[" + constante + r"\]\s*= _\(\"[^\"]*\"\),$", texto, re.M)
        if not antes:
            raise SystemExit(f"nome de {constante} não achado")
        texto = texto[:antes.start()] + f'    [{constante}] = _("{nome}"),' + texto[antes.end():]
        mudancas.append(f"{constante}: {nome}")
    p.write_text(texto)

    # 4) encontro: Dratini nível 30 no primeiro slot de grama da Rota 1
    p = raiz / "src/data/wild_encounters.json"
    dados = json.loads(p.read_text())
    grupos = dados["wild_encounter_groups"]
    rota1 = _encontro_rota1(grupos)
    if rota1 is None:
        raise SystemExit("MAP_ROUTE1 (FireRed) não está em wild_encounters.json")
    # todos os 12 slots: qualquer passo na grama tem de dar Dratini, senão o
    # teste depende de sorte (o slot 0 tem só 20% de chance)
    rota1["land_mons"]["mons"] = [{"min_level": NIVEL_DRATINI,
                                   "max_level": NIVEL_DRATINI,
                                   "species": "SPECIES_DRATINI"}] * 12
    p.write_text(json.dumps(dados, indent=2) + "\n")
    mudancas.append(f"Rota 1 (12 slots): DRATINI nível {NIVEL_DRATINI}")
    return mudancas


def verificar(raiz: Path) -> list[str]:
    """Confere as quatro mudanças sem escrever nada."""
    faltas: list[str] = []
    texto = (raiz / "src/data/battle_moves.h").read_text()
    for constante, _nome, _cat in GOLPES:
        bloco = _bloco_golpe(texto, constante).group(2)
        if ".type = TYPE_FAIRY" not in bloco or ".power = 40" not in bloco:
            faltas.append(f"battle_moves.h: {constante} sem TYPE_FAIRY/40 BP")
    texto = (raiz / "src/data/battle_moves_category.h").read_text()
    for constante, _nome, cat in GOLPES:
        if not re.search(r"^    \[" + constante + r"\] = " + cat + r",$", texto, re.M):
            faltas.append(f"battle_moves_category.h: {constante} != {cat}")
    texto = (raiz / "src/data/text/move_names.h").read_text()
    for constante, nome, _cat in GOLPES:
        if not re.search(r'^    \[' + constante + r'\] = _\("' + nome + r'"\),$', texto, re.M):
            faltas.append(f"move_names.h: {constante} != {nome}")
    dados = json.loads((raiz / "src/data/wild_encounters.json").read_text())
    enc = _encontro_rota1(dados["wild_encounter_groups"])
    mons = enc["land_mons"]["mons"] if enc else []
    if len(mons) != 12 or any(m.get("species") != "SPECIES_DRATINI"
                              or m.get("min_level") != NIVEL_DRATINI for m in mons):
        faltas.append("wild_encounters.json: a Rota 1 (12 slots) não é toda "
                      f"DRATINI nível {NIVEL_DRATINI}")
    return faltas


def reverter(raiz: Path) -> list[str]:
    restaurados: list[str] = []
    for rel in ARQUIVOS:
        origem = raiz / rel
        backup = origem.with_suffix(origem.suffix + SUFIXO_BACKUP)
        if backup.exists():
            shutil.copy2(backup, origem)
            # copy2 preserva o mtime ANTIGO: o make acha que o .o está atualizado
            # e não recompila (a ROM continuava com a prova aplicada)
            origem.touch()
            backup.unlink()
            restaurados.append(rel)
    return restaurados


def self_test() -> int:
    """Aplica num diretório temporário, confere, reverte e compara bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "src/data/text").mkdir(parents=True)
        (raiz / "src/data/battle_moves.h").write_text(
            "const struct BattleMove gBattleMoves[] = {\n"
            "    [MOVE_SPLASH] =\n    {\n        .effect = EFFECT_SPLASH,\n"
            "        .power = 0,\n        .type = TYPE_NORMAL,\n    },\n"
            "    [MOVE_PSYCH_UP] =\n    {\n        .effect = EFFECT_PSYCH_UP,\n"
            "        .power = 0,\n        .type = TYPE_NORMAL,\n    },\n};\n")
        (raiz / "src/data/battle_moves_category.h").write_text(
            "const u8 gMoveCategories[MOVES_COUNT] =\n{\n"
            "    [MOVE_SPLASH] = MOVE_CATEGORY_STATUS,\n"
            "    [MOVE_PSYCH_UP] = MOVE_CATEGORY_STATUS,\n};\n")
        (raiz / "src/data/text/move_names.h").write_text(
            'const u8 gMoveNames[][13] = {\n'
            '    [MOVE_SPLASH]        = _("SPLASH"),\n'
            '    [MOVE_PSYCH_UP]      = _("PSYCH UP"),\n};\n')
        (raiz / "src/data/wild_encounters.json").write_text(json.dumps({
            "wild_encounter_groups": [{
                "label": "gWildMonHeaders",
                "encounters": [{
                    "map": "MAP_ROUTE1",
                    "land_mons": {"encounter_rate": 21, "mons": [
                        {"min_level": 3, "max_level": 3, "species": "SPECIES_PIDGEY"}]},
                }],
            }],
        }, indent=2) + "\n")

        originais = {rel: (raiz / rel).read_bytes() for rel in ARQUIVOS}
        antes = verificar(raiz)
        assert antes, "o diretório de teste já devia estar sem os patches"
        mudancas = aplicar(raiz)
        assert len(mudancas) == 7, mudancas
        assert not verificar(raiz), verificar(raiz)
        faltas = verificar(raiz)
        assert not faltas, faltas
        restaurados = reverter(raiz)
        assert len(restaurados) == len(ARQUIVOS), restaurados
        for rel in ARQUIVOS:
            assert (raiz / rel).read_bytes() == originais[rel], f"reversão de {rel} não bateu"
        assert verificar(raiz), "depois de reverter ainda havia patch"
    print("self-test ok: aplicar/verificar/reverter em 4 arquivos, ida-e-volta byte a byte")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--reverter", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    raiz = Path(a.pokefirered)
    if a.reverter:
        feitos = reverter(raiz)
        if not feitos:
            print("nada a reverter (sem backups)")
        for rel in feitos:
            print(f"restaurado: {rel}")
        return 0
    if a.check:
        faltas = verificar(raiz)
        if faltas:
            print("prova NÃO está aplicada:")
            for f in faltas:
                print("  -", f)
            return 1
        print("prova aplicada: 2 golpes Fada + Dratini na Rota 1")
        return 0
    for m in aplicar(raiz):
        print("aplicado:", m)
    faltas = verificar(raiz)
    if faltas:
        for f in faltas:
            print("FALTA:", f)
        return 1
    print("prova aplicada e conferida")
    return 0


if __name__ == "__main__":
    sys.exit(main())
