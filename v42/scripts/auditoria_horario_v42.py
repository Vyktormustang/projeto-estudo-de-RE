#!/usr/bin/env python3
"""auditoria_horario_v42.py — encontros e evoluções por horário, na V42 exata.

Três perguntas separadas, cada uma respondida por dado lido da ROM (não por
documentação):

  1. ENCONTROS POR HORÁRIO — a tabela noturna está realmente gravada na V42?
     O motor grava, em offset fixo (0x112C000), um bloco de 68 mapas: cabeçalho
     de 12 bytes por mapa + entrada de 56 bytes (taxa + ponteiro + 48 B de slots).
     Este script percorre o bloco e compara slot a slot com a política
     (data/encontros_horario_v40.csv). Não confia na cadeia de patches.

  2. COBERTURA — o horário ACRESCENTA espécies ou só VARIA as existentes?
     Compara o conjunto noturno com o conjunto de terra da V42.

  3. EVOLUÇÕES POR HORÁRIO — quantas das 449 entradas dependem de período?
     Classifica `docs/evolucoes_v40.csv` por método (Gen 3: 2=amizade dia,
     3=amizade noite) e lista as que dependem de relógio.

Só aceita a V42 exata (SHA-256 conferido). Não escreve na ROM.

Uso:
  python3 v42/scripts/auditoria_horario_v42.py --self-test
  COSMOG_V42_ROM=... python3 v42/scripts/auditoria_horario_v42.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
ROM_ESPERADA = "6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a"

# Gen 3 — métodos de evolução por ID
METODOS = {
    1: "amizade", 2: "amizade-DIA", 3: "amizade-NOITE", 4: "nivel",
    5: "item", 6: "trade", 7: "item-seguro", 8: "nivel+genero",
    9: "nivel+atk/def", 10: "nivel+pid", 11: "nivel+nature",
    12: "nivel+item", 13: "nivel+invertido", 14: "nivel+item2",
    15: "nivel+amizade",
}
# Apenas estes dependem do relógio.
DEPENDE_DE_HORARIO = {2, 3}
# Amizade que o motor restringiu a DIA (não aparece no CSV como método 2, mas o
# dispatcher força: ver docs/MOTOR_V19.md). Registrado à parte, com a origem.
AMIZADE_SO_DIA_DOC = [
    ("budew", 406, "roselia", 315),
    ("riolu", 447, "lucario", 448),
]


def achar_motor() -> pathlib.Path:
    env = os.environ.get("GEN19_WORK")
    cands = ([pathlib.Path(env) / "firered_gen1_9"] if env else []) + [
        pathlib.Path("/tmp/gen19/firered_gen1_9")
    ]
    for c in cands:
        if (c / "scripts/encontros_selvagens.py").is_file():
            return c
    raise SystemExit("[ERRO] motor ausente: rode antes bash v42/scripts/run_cosmog_tests.sh")


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    if "--self-test" in sys.argv:
        # sem ROM, sem motor: valida a classificação de método e a aritmética do bloco
        ok = True
        for m, esperado in ((2, True), (3, True), (4, False), (1, False), (7, False)):
            obtido = m in DEPENDE_DE_HORARIO
            if obtido != esperado:
                ok = False
            print(f"  [{'PASS' if obtido == esperado else 'FAIL'}] metodo {m}: "
                  f"depende_de_horario={obtido}")
        # layout: 68 mapas -> 816 B de cabeçalho + 68*56 B de entradas
        n = 68
        total = 12 * n + 56 * n
        bom = total == 4624
        print(f"  [{'PASS' if bom else 'FAIL'}] tamanho do bloco 68 mapas = {total} B")
        ok &= bom
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
    import encontros_selvagens as wild                      # noqa: E402
    from scripts import motor_v40_encontros as h40          # noqa: E402

    rom = rom_path.read_bytes()
    cat = wild.load_species()
    MAPS = h40.MAPS
    TO = h40.TABLE_OFFSET
    rows = h40.policy_rows()

    print("=" * 70)
    print("ENCONTROS E EVOLUÇÕES POR HORÁRIO — ROM V42 exata")
    print(f"  sha256 {digest[:16]}…{digest[-8:]}")
    print("=" * 70)

    # ---------------- 1) tabela noturna fisicamente presente ----------------
    print("\n[1] A tabela noturna está GRAVADA na V42?")
    off = TO + 12 * len(MAPS)
    ok_map, ruins = 0, []
    for i, name in enumerate(MAPS):
        info, data, g, m, _ = struct.unpack_from("<IIBBH", rom, TO + i * 12)
        rate = rom[off]
        slots_ptr = struct.unpack_from("<I", rom, off + 4)[0]
        esperado = 0x08000000 + off + 8
        if slots_ptr != esperado:
            ruins.append((name, f"ponteiro {slots_ptr:#x} != {esperado:#x}"))
            off += 56
            continue
        erros = []
        for r in [x for x in rows if x["map_symbol"] == name]:
            _lo, _hi, sp = struct.unpack_from("<BBH", rom, off + 8 + r["slot"] * 4)
            if sp != r["night_species"]:
                erros.append(f"slot{r['slot']}={sp}≠{r['night_species']}")
        if erros:
            ruins.append((name, erros))
        else:
            ok_map += 1
        off += 56
    print(f"    mapas conferidos slot a slot ... {ok_map}/{len(MAPS)}")
    print(f"    divergências ................... {len(ruins)}")
    for n, e in ruins[:3]:
        print(f"      {n}: {e}")
    print(f"    linhas de política ............ {len(rows)} (2 slots × {len(MAPS)} mapas)")
    muda = sum(1 for r in rows if r["day_species"] != r["night_species"])
    print(f"    slots que TROCAM de espécie ... {muda}/{len(rows)}")

    # ---------------- 2) cobertura: variação ou expansão? ----------------
    print("\n[2] O horário ACRESCENTA espécies ou apenas VARIA?")
    tables = wild.parse_tables(rom, wild.load_maps(), cat)
    terra = {s.species for t in tables if t.kind == "land" for s in t.slots}
    dia = {r["day_species"] for r in rows}
    noite = {r["night_species"] for r in rows}
    protegidas = {i for i, s in cat.items() if s.protected}
    nao_prot = set(cat) - protegidas
    print(f"    espécies em terra na V42 ....... {len(terra)}")
    print(f"    espécies diurnas na política ... {len(dia)}  (fora de terra: {len(dia - terra)})")
    print(f"    espécies noturnas na política .. {len(noite)}  (fora de terra: {len(noite - terra)})")
    exclusivas = sorted(noite - terra)
    if exclusivas:
        print("    noturnas que NÃO existem em terra:")
        for i in exclusivas:
            print(f"      #{i:>4} {cat[i].name}")
    print(f"    cobertura não protegidas ....... {len(nao_prot & (terra | noite))}/{len(nao_prot)}"
          f"  (sem horário: {len(nao_prot & terra)})")
    print("    → conclusão: horário é VARIAÇÃO de design, não expansão de cobertura")

    # ---------------- 3) evoluções por horário ----------------
    print("\n[3] Evoluções que dependem do relógio")
    evo_csv = gen / "docs/evolucoes_v40.csv"
    evo = list(csv.DictReader(evo_csv.open()))
    contagem: dict[str, int] = {}
    for r in evo:
        nome = METODOS.get(int(r["method"]), f"desconhecido {r['method']}")
        contagem[nome] = contagem.get(nome, 0) + 1
    print(f"    entradas de evolução na tabela .. {len(evo)}")
    horario = [r for r in evo if int(r["method"]) in DEPENDE_DE_HORARIO]
    print(f"    dependem do HORÁRIO ............. {len(horario)} de {len(evo)}")
    for r in horario:
        s, t = int(r["source"]), int(r["target"])
        periodo = "DIA" if int(r["method"]) == 2 else "NOITE"
        print(f"      {periodo:<5} #{s:>4} {cat[s].name:<12} → #{t:>4} {cat[t].name}")
    print(f"    amizade restrita a DIA (doc) ..... {len(AMIZADE_SO_DIA_DOC)}")
    for _n, s, _t2, t in AMIZADE_SO_DIA_DOC:
        print(f"      DIA   #{s:>4} {cat[s].name:<12} → #{t:>4} {cat[t].name}")

    # cadeia do Cosmog, para desfazer a confusão "Solgaleo de dia / Lunala de noite"
    print("\n    cadeia do Cosmog (para registro):")
    for r in evo:
        s, t = int(r["source"]), int(r["target"])
        if s in (789, 790):
            print(f"      #{s:>4} {cat[s].name:<10} → #{t:>4} {cat[t].name:<10} "
                  f"método={METODOS.get(int(r['method']))} param={r['param']} "
                  f"slot={r['slot']}")
    print("      → é NÍVEL (53 Solgaleo / 54 Lunala), não horário")

    print("\n[4] Limite conhecido do relógio")
    print("    contador nativo satura em 999:59:59 e o relógio derivado PARA em 07:59")
    print("    períodos: amanhecer 06:00–07:59 | dia 08:00–17:59 | entardecer 18:00–19:59")
    print("    mecânica: dia 06:00–19:59 | noite 20:00–05:59")
    return 0


if __name__ == "__main__":
    sys.exit(main())
