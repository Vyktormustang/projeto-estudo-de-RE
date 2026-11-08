#!/usr/bin/env python3
"""auditoria_encontros_v42.py — "temos encontro selvagem para todos os Pokémon?"

Responde com dado lido da ROM V42, não com impressão nem com a documentação de
outra edição do motor.

Método (tudo estrutural, nada de captura):
  1. carrega a lista de espécies (`data/species_gen1_9.csv` do motor);
  2. localiza a tabela de cabeçalhos de encontro (`WILD_HEADERS`) e lê, mapa a
     mapa, os 4 métodos (terra / água / pesca / rock smash);
  3. para cada slot, registra espécie, níveis e método;
  4. responde três perguntas SEPARADAS, porque "ter encontro" não é a mesma coisa
     que "ser capturável":
       (a) a espécie aparece em ALGUMA tabela (inclui pesca e rock smash)?
       (b) aparece especificamente em terra/água (o critério conservador)?
       (c) está na lista de protegidas (lendário/mítico)?

Só a V42 é aceita: o SHA-256 é conferido antes de qualquer leitura.
Nada é escrito na ROM; nenhum save é tocado.

Uso:
  python3 v42/scripts/auditoria_encontros_v42.py --self-test
  COSMOG_V42_ROM=/caminho/v42.gba python3 v42/scripts/auditoria_encontros_v42.py
  ... --csv /tmp/encontros.csv        # despeja pares espécie×mapa
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

# caminho do motor extraído do PR #9 (não vive neste branch)
GEN_CANDIDATOS = [pathlib.Path("/tmp/gen19/firered_gen1_9")]


def achar_motor() -> pathlib.Path:
    env = os.environ.get("GEN19_WORK")
    candidatos = ([pathlib.Path(env) / "firered_gen1_9"] if env else []) + GEN_CANDIDATOS
    for c in candidatos:
        if (c / "scripts/encontros_selvagens.py").is_file():
            return c
    raise SystemExit(
        "[ERRO] motor firered_gen1_9/ não encontrado.\n"
        "       rode antes: bash v42/scripts/run_cosmog_tests.sh\n"
        "       (ele extrai o motor de 345efac para /tmp/gen19)"
    )


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    if "--self-test" in sys.argv:
        # lógica pura: classificação e formatação, sem ROM nem motor
        casos = [
            ({"land"}, True, "terra"),
            ({"water"}, True, "agua"),
            ({"fish"}, False, "so_pesca"),
            (set(), False, "ausente"),
        ]
        ok = True
        for metodos, esperado_terra, rotulo in casos:
            obtido = bool(metodos & {"land", "water"})
            if obtido != esperado_terra:
                ok = False
                print(f"  [FAIL] {rotulo}: esperado {esperado_terra}, obtido {obtido}")
            else:
                print(f"  [PASS] {rotulo}: terra/agua={obtido}")
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
    sys.path.insert(0, str(gen))
    sys.path.insert(0, str(gen / "scripts"))
    import encontros_selvagens as e  # noqa: E402

    rom = rom_path.read_bytes()
    # `e.validate_source` recusa tudo que não seja a base PT-BR original
    # (`ecd157aa…`), e a V42 não é essa base. Pulamos APENAS essa checagem de
    # origem: o hash da V42 já foi conferido acima, e `parse_tables` continua
    # aplicando todas as validações estruturais (sentinela da tabela, coerência
    # de ponteiros, taxa em 1..100, espécie no catálogo, ausência de
    # sobreposição/alias). Se o layout tivesse mudado, ele levantaria PatchError.
    species = e.load_species()
    maps = e.load_maps()
    tables = e.parse_tables(rom, maps, species)

    # ---- agregação -----------------------------------------------------------
    metodos: dict[int, set[str]] = {}
    ocorrencias: dict[int, list[tuple[str, str, int, int, float]]] = {}
    total_slots = 0
    for t in tables:
        for s in t.slots:
            total_slots += 1
            metodos.setdefault(s.species, set()).add(t.kind)
            ocorrencias.setdefault(s.species, []).append(
                (t.map.symbol, t.kind, s.min_level, s.max_level, s.chance)
            )

    todas = set(species)
    protegidas = {i for i, sp in species.items() if sp.protected}
    nao_protegidas = todas - protegidas
    com_terra = {i for i, m in metodos.items() if m & {"land", "water"}}
    com_qualquer = set(metodos)

    print("=" * 68)
    print("ENCONTROS SELVAGENS — ROM V42 exata")
    print(f"  sha256 {digest[:16]}…{digest[-8:]}")
    print("=" * 68)
    print(f"tabelas lidas ......... {len(tables)}")
    print(f"mapas ................. {len(maps)}")
    print(f"slots de encontro ..... {total_slots}")
    print(f"espécies no catálogo .. {len(todas)}")
    print()
    print(f"[A] aparecem em TERRA/ÁGUA ......... {len(com_terra):>4} / {len(nao_protegidas)} "
          f"não protegidas")
    print(f"[B] aparecem em QUALQUER método .... {len(com_qualquer):>4} / {len(nao_protegidas)}")
    print(f"[C] protegidas (lendário/mítico) ... {len(protegidas):>4} "
          f"(fora do critério de cobertura)")

    faltam_terra = sorted(nao_protegidas - com_terra)
    faltam_qualquer = sorted(nao_protegidas - com_qualquer)
    print()
    print(f"não protegidas SEM terra/água ...... {len(faltam_terra)}")
    print(f"não protegidas SEM método algum .... {len(faltam_qualquer)}")
    for rotulo, faltando in (("sem terra/água", faltam_terra),
                             ("sem método algum", faltam_qualquer)):
        if faltando:
            nomes = ", ".join(
                f"{species[i].name}(#{i})" if hasattr(species[i], "name") else f"#{i}"
                for i in faltando[:25]
            )
            print(f"  {rotulo}: {nomes}{' …' if len(faltando) > 25 else ''}")

    # ---- lendários que JÁ têm slot (não foram removidos) ---------------------
    prot_com_slot = sorted(protegidas & com_qualquer)
    print()
    print(f"protegidas COM slot original preservado ... {len(prot_com_slot)} / {len(protegidas)}")
    prot_sem_slot = sorted(protegidas - com_qualquer)
    if prot_sem_slot:
        nomes = ", ".join(
            f"{species[i].name}(#{i})" if hasattr(species[i], "name") else f"#{i}"
            for i in prot_sem_slot[:20]
        )
        print(f"  protegidas SEM slot (dependem de evento/pesca/etc): {len(prot_sem_slot)}")
        print(f"  {nomes}{' …' if len(prot_sem_slot) > 20 else ''}")

    # ---- CSV opcional --------------------------------------------------------
    if "--csv" in sys.argv:
        destino = pathlib.Path(sys.argv[sys.argv.index("--csv") + 1])
        with destino.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["pokedex_nacional", "pokemon", "mapa", "metodo",
                        "nivel_min", "nivel_max", "chance_por_encontro_pct", "protegida"])
            for sid in sorted(ocorrencias):
                nome = getattr(species[sid], "name", "")
                for simbolo, kind, lo, hi, chance in sorted(ocorrencias[sid]):
                    w.writerow([sid, nome, simbolo, kind, lo, hi, chance,
                                int(sid in protegidas)])
        print(f"\n[csv] {destino} ({len(ocorrencias)} espécies)")

    print()
    print("Lembrete de escopo: isto é cobertura ESTRUTURAL de tabela.")
    print("Não prova que cada tile é alcançável, nem que cada espécie foi")
    print("capturada em jogo. Isso exige teste por mapa, que é outro trabalho.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
