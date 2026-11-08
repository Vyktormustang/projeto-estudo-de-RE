#!/usr/bin/env python3
"""obtencao_total_v42.py — "é possível encontrar TODOS os Pokémon?" na V42.

A pergunta só tem resposta honesta se juntar TODOS os caminhos de obtenção, e
não apenas a tabela de encontros. Este script une:

  1. TABELA     — slots de encontro lidos da ROM (terra, água, pesca, rock smash);
  2. FIXO       — eventos estáticos preservados no mapa (inventário do motor);
  3. EVOLUÇÃO   — espécies que nascem de outra (`evolves_from` preenchido);
  4. NATIVO     — eventos originais do FireRed (lendários/míticos de história).

Depois responde três coisas diferentes, que costumam ser confundidas:

  (a) existe ALGUM caminho no dado?          -> cobertura estrutural
  (b) quantos dependem de UM ÚNICO caminho?  -> risco (um bug derruba a espécie)
  (c) quantos dependem de LOCAL CONDICIONADO?-> Tanoby / Altering Cave / evento

E registra o que NÃO está provado: alcançabilidade de cada tile, cada etapa da
história e captura em jogo.

Só aceita a V42 exata. Não escreve na ROM.

Uso:
  python3 v42/scripts/obtencao_total_v42.py --self-test
  COSMOG_V42_ROM=... python3 v42/scripts/obtencao_total_v42.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
ROM_ESPERADA = "6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a"

# Eventos originais do FireRed (não são tabela nem evento adicionado pelo motor).
EVENTO_NATIVO = {
    144: "Articuno — Seafoam B4F",
    145: "Zapdos — Power Plant",
    146: "Moltres — Mt. Ember Summit",
    150: "Mewtwo — Cerulean Cave B1F",
    249: "Lugia — Navel Rock",
    250: "Ho-Oh — Navel Rock",
    386: "Deoxys — Birth Island",
}
# Mapas que o motor trata como condicionais/excluídos para cobertura simples.
CONDICIONAIS = {
    201: "Unown — somente câmaras Tanoby (forma depende de código das ruínas)",
    488: "Cresselia — Tanoby Dilford (mapa excluído do critério)",
    772: "Type: Null — Altering Cave (variantes condicionais)",
}


def achar_motor() -> pathlib.Path:
    env = os.environ.get("GEN19_WORK")
    cands = ([pathlib.Path(env) / "firered_gen1_9"] if env else []) + [
        pathlib.Path("/tmp/gen19/firered_gen1_9")
    ]
    for c in cands:
        if (c / "docs/cobertura_1025_v40.csv").is_file():
            return c
    raise SystemExit("[ERRO] motor ausente: rode antes bash v42/scripts/run_cosmog_tests.sh")


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def unir_caminhos(em_tabela, fixos, evoluiveis, todas, nativos=EVENTO_NATIVO):
    """Função pura — testável sem ROM. Devolve {espécie: [caminhos]}."""
    nativos = set(nativos)
    out = {}
    for i in todas:
        c = []
        if i in em_tabela:
            c.append("tabela")
        if i in fixos:
            c.append("fixo")
        if i in evoluiveis:
            c.append("evolucao")
        if i in nativos:
            c.append("evento_nativo")
        out[i] = c
    return out


def main() -> int:
    if "--self-test" in sys.argv:
        # lógica pura, sem ROM: uma espécie por caminho, mais uma órfã
        r = unir_caminhos({1}, {2}, {3}, {1, 2, 3, 4})
        ok = True
        casos = [(1, ["tabela"]), (2, ["fixo"]), (3, ["evolucao"]), (4, [])]
        for sid, esperado in casos:
            bom = r[sid] == esperado
            ok &= bom
            print(f"  [{'PASS' if bom else 'FAIL'}] #{sid} -> {r[sid]} (esperado {esperado})")
        # eventos nativos entram como caminho
        r2 = unir_caminhos(set(), set(), set(), {144})
        bom = r2[144] == ["evento_nativo"]
        ok &= bom
        print(f"  [{'PASS' if bom else 'FAIL'}] #144 evento nativo -> {r2[144]}")
        print(f"\nresumo: {'OK' if ok else '1 falha(s)'}")
        return 0 if ok else 1

    rom_path = os.environ.get("COSMOG_V42_ROM", "")
    if not rom_path or not pathlib.Path(rom_path).is_file():
        print("[ERRO] defina COSMOG_V42_ROM com a ROM V42")
        return 2
    rom_path = pathlib.Path(rom_path)
    digest = sha256(rom_path)
    if digest != ROM_ESPERADA:
        print(f"[ERRO] não é a V42 exata\n  esperado {ROM_ESPERADA}\n  obtido   {digest}")
        return 2

    gen = achar_motor()
    sys.path[:0] = [str(gen), str(gen / "scripts")]
    import encontros_selvagens as wild  # noqa: E402

    rom = rom_path.read_bytes()
    cat = wild.load_species()
    todas = set(cat)

    tabs = wild.parse_tables(rom, wild.load_maps(), cat)
    em_tabela = {s.species for t in tabs for s in t.slots}

    inv = list(csv.DictReader((gen / "docs/eventos_fixos_inventario.csv").open()))
    fixos = {int(r["pokedex_nacional"]) for r in inv if "retirado" not in r["situacao_fixo"]}
    retirados = {int(r["pokedex_nacional"]) for r in inv if "retirado" in r["situacao_fixo"]}

    evoluiveis = {i for i, s in cat.items() if s.evolves_from is not None}

    print("=" * 70)
    print("É POSSÍVEL ENCONTRAR TODOS? — ROM V42 exata")
    print(f"  sha256 {digest[:16]}…{digest[-8:]}")
    print("=" * 70)

    print("\n[1] Caminhos de obtenção (fontes somadas)")
    print(f"    em tabela de encontro ......... {len(em_tabela)}")
    print(f"    evento fixo preservado ........ {len(fixos)}")
    print(f"    nascem por evolução ........... {len(evoluiveis)}")
    print(f"    evento nativo do FireRed ...... {len(EVENTO_NATIVO)}")
    print(f"    eventos fixos RETIRADOS ....... {len(retirados)} "
          f"(espécies reacomodadas em outro caminho)")

    caminhos = unir_caminhos(em_tabela, fixos, evoluiveis, todas)
    sem = sorted(i for i in todas if not caminhos[i])
    print(f"\n[2] Cobertura estrutural: {len(todas) - len(sem)} / {len(todas)} espécies "
          f"com pelo menos um caminho")
    if sem:
        print(f"    SEM caminho: {len(sem)}")
        for i in sem:
            print(f"      #{i:>4} {cat[i].name}")

    orfas = sorted(i for i in retirados if not caminhos[i])
    print(f"\n[3] Espécies que perderam o evento fixo e ficaram órfãs: {len(orfas)}")
    print("    → nenhuma" if not orfas else "    → " + ", ".join(cat[i].name for i in orfas))

    deps: dict[str, int] = {}
    for i in todas:
        c = caminhos[i]
        chave = "unico:" + c[0] if len(c) == 1 else ("multi" if c else "nenhum")
        deps[chave] = deps.get(chave, 0) + 1
    print("\n[4] Dependência (risco: um bug derruba a espécie)")
    for k in sorted(deps, key=lambda x: -deps[x]):
        print(f"    {k:<20} {deps[k]}")

    print("\n[5] Casos que dependem de LOCAL CONDICIONADO ou evento (não de tabela simples)")
    for i, nota in sorted(CONDICIONAIS.items()):
        print(f"      #{i:>4} {cat[i].name:<12} {nota}")
    for i, nota in sorted(EVENTO_NATIVO.items()):
        print(f"      #{i:>4} {cat[i].name:<12} {nota}")

    print("\n[6] O que NÃO está provado aqui")
    print("    - que cada tile de encontro é alcançável em cada etapa da história;")
    print("    - que cada evento fixo dispara (só inventário + amostra em jogo);")
    print("    - captura individual das 934 espécies de tabela;")
    print("    - sprites/golpes/habilidades corretos para todas as espécies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
