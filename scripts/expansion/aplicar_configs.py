#!/usr/bin/env python3
"""Ajusta as configurações da pokeemerald-expansion para o objetivo do projeto.

O que faz (idempotente, seguro para rodar várias vezes):

  1. Confere que as gerações 1 a 9 de Pokémon estão ligadas
     (`include/config/species_enabled.h`). Se alguma estiver FALSE, liga.
  2. Liga o menu de debug no overworld (`include/config/debug.h`), que permite
     dar qualquer Pokémon/item/golpe no jogo — necessário para "ter todos os
     Pokémon" sem esperar encontro selvagem.

Não mexe em balanceamento, encontros selvagens ou textos: isso muda o jogo de
forma que o projeto ainda não decidiu.

Uso:
    python3 scripts/expansion/aplicar_configs.py --raiz /caminho/pokeemerald-expansion
    python3 scripts/expansion/aplicar_configs.py --raiz . --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

GERACOES = [f"P_GEN_{n}_POKEMON" for n in range(1, 10)]


def _ler(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="surrogateescape")


def ligar_geracoes(texto: str) -> tuple[str, list[str]]:
    """Garante P_GEN_n_POKEMON como TRUE. Retorna (texto, mudanças)."""
    mudancas: list[str] = []
    for nome in GERACOES:
        padrao = re.compile(rf"^(\s*#define\s+{nome}\s+)(FALSE|TRUE)(.*)$", re.M)
        m = padrao.search(texto)
        if not m:
            mudancas.append(f"{nome}: ausente (não alterado)")
            continue
        if m.group(2) == "FALSE":
            texto = padrao.sub(rf"\g<1>TRUE\g<3>", texto, count=1)
            mudancas.append(f"{nome}: FALSE -> TRUE")
    return texto, mudancas


def ligar_debug(texto: str) -> tuple[str, list[str]]:
    """Liga DEBUG_OVERWORLD_MENU (e o menu de debug geral, se existir)."""
    mudancas: list[str] = []
    for nome in ("DEBUG_OVERWORLD_MENU", "DEBUG_MENU"):
        padrao = re.compile(rf"^(\s*#define\s+{nome}\s+)(FALSE)(.*)$", re.M)
        if padrao.search(texto):
            texto = padrao.sub(rf"\g<1>TRUE\g<3>", texto)
            mudancas.append(f"{nome}: FALSE -> TRUE")
        elif not re.search(rf"#define\s+{nome}\b", texto):
            texto += f"\n#define {nome} TRUE\n"
            mudancas.append(f"{nome}: adicionado como TRUE")
    return texto, mudancas


def aplicar(raiz: Path, seco: bool = False) -> int:
    species = raiz / "include" / "config" / "species_enabled.h"
    debug = raiz / "include" / "config" / "debug.h"
    if not species.is_file():
        print(f"[erro] não parece a expansion: {species} não existe", file=sys.stderr)
        return 2

    total = 0
    alvos = [(species, ligar_geracoes)]
    if debug.is_file():
        alvos.append((debug, ligar_debug))
    else:
        print("[aviso] include/config/debug.h ausente — menu de debug não configurado")

    for caminho, funcao in alvos:
        original = _ler(caminho)
        novo, mudancas = funcao(original)
        reais = [m for m in mudancas if "->" in m or "adicionado" in m]
        print(f"\n{caminho.relative_to(raiz)}")
        for m in mudancas:
            print(f"   {m}")
        if reais:
            if seco:
                print("   (dry-run: não gravado)")
            else:
                caminho.write_text(novo, encoding="utf-8", errors="surrogateescape")
        total += len(reais)

    print(f"\n{total} mudança(s) aplicada(s).")
    return 0


def self_test() -> int:
    """Testa as funções com um arquivo sintético (sem precisar do repo)."""
    falhas = 0

    def chk(nome: str, ok: bool) -> None:
        nonlocal falhas
        print(f"  [{'OK' if ok else 'FALHA'}] {nome}")
        falhas += 0 if ok else 1

    amostra = "#define P_GEN_1_POKEMON TRUE\n#define P_GEN_9_POKEMON FALSE\n"
    novo, mud = ligar_geracoes(amostra)
    chk("liga P_GEN_9 FALSE->TRUE", "TRUE" in novo.split("P_GEN_9_POKEMON")[1].split("\n")[0])
    chk("não mexe no que já é TRUE", novo.count("P_GEN_1_POKEMON TRUE") == 1)
    chk("registra a mudança", any("P_GEN_9" in m for m in mud))
    chk("idempotente", ligar_geracoes(novo)[1] == [] or
        all("FALSE" not in m for m in ligar_geracoes(novo)[1]))

    dbg, mud2 = ligar_debug("#define DEBUG_OVERWORLD_MENU FALSE\n")
    chk("liga o menu de debug", "DEBUG_OVERWORLD_MENU TRUE" in dbg)
    dbg2, mud3 = ligar_debug("#define OUTRA_COISA 1\n")
    chk("adiciona DEBUG_MENU quando ausente", "DEBUG_MENU TRUE" in dbg2)

    with tempfile.TemporaryDirectory() as td:
        raiz = Path(td)
        (raiz / "include" / "config").mkdir(parents=True)
        (raiz / "include" / "config" / "species_enabled.h").write_text(amostra)
        (raiz / "include" / "config" / "debug.h").write_text("#define DEBUG_OVERWORLD_MENU FALSE\n")
        rc = aplicar(raiz)
        chk("aplicar() retorna 0", rc == 0)
        chk("arquivo foi gravado",
            "P_GEN_9_POKEMON TRUE" in (raiz / "include" / "config" / "species_enabled.h").read_text())

    print(f"\n[self-test] {'OK' if falhas == 0 else f'{falhas} falha(s)'}")
    return 0 if falhas == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", type=Path, default=Path("."),
                    help="raiz do checkout da pokeemerald-expansion")
    ap.add_argument("--dry-run", action="store_true", help="mostra sem gravar")
    ap.add_argument("--self-test", action="store_true", help="testa sem o repositório")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return aplicar(args.raiz, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
