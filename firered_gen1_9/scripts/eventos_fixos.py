#!/usr/bin/env python3
"""Retira Pokémon comuns do sistema de encontros fixos desta ROM específica.

Os objetos identificados são colocados fora dos mapas, sem mudar a ordem dos
objetos, scripts, flags ou tabelas selvagens. Lendários, míticos, Ultra Beasts,
Paradox e eventos de história ficam intactos. Exige a ROM exata com treino;
nunca edita a entrada nem substitui uma saída já existente.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import encontros_selvagens as wild  # noqa: E402
from scripts import treino_ev  # noqa: E402

BASE_SHA256 = "1123e7995b37008a75c818f09fb852bfd4910e1f074ae2e630cbd9c8af994abc"
# O hash da saída fixa também protege contra mudanças acidentais no plano.
OUTPUT_SHA256 = "c563d43a8f15976314ad5fb271ad44a83cdf3143749389311f261ffd506a466b"
ROM_SIZE = 0x1000000
ROM_START = 0x08000000
GROUP_TABLE = 0x8493E8
GENERIC_SCRIPT = 0x081EF400
PARKED_COORD = -1024
OBJECT_SIZE = 24
MAP_CATALOG = ROOT / "data/firered_map_groups.csv"
SPECIES_CATALOG = ROOT / "data/species_gen1_9.csv"
WILD_CATALOG = ROOT / "data/firered_wild_maps.csv"
CATALOG_HASHES = {
    MAP_CATALOG: "810b45f50d07c903366c9b1c1cedacd31e0e2853d2a710fdf398c8f78dc97cab",
    SPECIES_CATALOG: "2d73a8d75ca94a71cebc8e3ec3d7a2e9624c63b2ecac78caa7515107319ce94e",
    WILD_CATALOG: "04ec91c9eadbc6f199b5c1a1043def0bf0184e70c0c2f9362d32eb0560d71257",
}
# Embora não tenham as flags de lendário da PokéAPI, são especiais/ambíguos.
# Preferimos preservá-los como estavam no mapa a decidir que são "comuns".
ULTRA_BEASTS = frozenset(range(793, 800)) | frozenset(range(803, 807))
PARADOX = frozenset(range(984, 996)) | frozenset({1005, 1006, 1009, 1010, 1020, 1021, 1022, 1023})


class PatchError(ValueError):
    """Uma pré-condição ou verificação de segurança não foi cumprida."""


@dataclass(frozen=True)
class MapRef:
    group: int
    number: int
    label: str


@dataclass(frozen=True)
class StaticEvent:
    map: MapRef
    index: int
    local_id: int
    offset: int
    species: int
    x: int
    y: int
    flag: int
    original: bytes


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_catalogs() -> None:
    for path, expected in CATALOG_HASHES.items():
        if digest(path.read_bytes()) != expected:
            raise PatchError(f"Catálogo alterado ou incompatível: {path.name}")


def load_map_catalog(path: Path = MAP_CATALOG) -> list[MapRef]:
    with path.open(newline="", encoding="utf-8") as f:
        maps = [MapRef(int(r["group"]), int(r["map"]), r["label"]) for r in csv.DictReader(f)]
    if len(maps) != 425 or len({(m.group, m.number) for m in maps}) != len(maps):
        raise PatchError("Catálogo de mapas incompleto ou duplicado.")
    return maps


def validate_source(rom: bytes) -> None:
    sha = digest(rom)
    if len(rom) != ROM_SIZE or sha != BASE_SHA256:
        raise PatchError("ROM incompatível: use a cópia de selvagens + treino identificada. "
                         f"Esperado {BASE_SHA256}; recebido {sha}, {len(rom)} bytes.")
    if rom[0xAC:0xB0] != b"BPRE":
        raise PatchError("Cabeçalho da ROM inesperado.")
    # Dados extraídos da Route 1: cabeçalho, eventos, 2 NPCs + 6 eventos fixos.
    if rom[0x7C20DC:0x7C20E0] != b"\x08\x00\x00\x01":
        raise PatchError("Estrutura da Rota 1 inesperada.")


def _u16(data: bytes, at: int) -> int:
    if at < 0 or at + 2 > len(data):
        raise PatchError(f"Leitura fora da ROM: 0x{at:X}")
    return struct.unpack_from("<H", data, at)[0]


def _u32(data: bytes, at: int) -> int:
    if at < 0 or at + 4 > len(data):
        raise PatchError(f"Leitura fora da ROM: 0x{at:X}")
    return struct.unpack_from("<I", data, at)[0]


def _ptr(data: bytes, at: int, length: int) -> int:
    val = _u32(data, at)
    off = val - ROM_START
    if off < 0 or off % 4 or off + length > len(data):
        raise PatchError(f"Ponteiro inválido 0x{val:08X} em 0x{at:X}.")
    return off


def parse_static_events(rom: bytes, maps: Sequence[MapRef],
                        group_table: int = GROUP_TABLE) -> tuple[list[StaticEvent], int]:
    """Percorre todos os mapas e só reconhece o sistema de script compartilhado.

    Nenhum outro tipo de evento é convertido; tanto os índices/IDs quanto os
    clones entre mapas permanecem iguais. Faixas duplicadas são rejeitadas.
    """
    groups: dict[int, list[MapRef]] = {}
    for m in maps:
        groups.setdefault(m.group, []).append(m)
    if sorted(groups) != list(range(len(groups))):
        raise PatchError("Grupos de mapas não são contíguos.")
    candidates: list[StaticEvent] = []
    intervals: list[tuple[int, int, str]] = []
    event_headers: set[int] = set()
    objects_count = 0
    for gi in sorted(groups):
        entries = groups[gi]
        if [m.number for m in entries] != list(range(len(entries))):
            raise PatchError(f"Numeração inesperada no grupo {gi}.")
        array = _ptr(rom, group_table + 4 * gi, len(entries) * 4)
        # O dump desta ROM armazena os grupos adjacentes imediatamente antes
        # da tabela principal. Não inferimos comprimentos de outra ROM.
        next_array = _ptr(rom, group_table + 4 * (gi + 1), 4) if gi + 1 < len(groups) else group_table
        if array + 4 * len(entries) != next_array:
            raise PatchError(f"Comprimento inesperado para o grupo {gi}.")
        for m in entries:
            header = _ptr(rom, array + 4 * m.number, 28)
            layout = _ptr(rom, header, 8)
            width, height = struct.unpack_from("<II", rom, layout)
            if not (1 <= width <= 1024 and 1 <= height <= 1024):
                raise PatchError(f"Dimensões inválidas: {m.label}.")
            events = _ptr(rom, header + 4, 20)
            if events in event_headers:
                raise PatchError(f"Cabeçalho de eventos compartilhado: {m.label}.")
            event_headers.add(events)
            count = rom[events]
            if count > 64:
                raise PatchError(f"Número inesperado de objetos: {m.label}.")
            if not count:
                continue
            obj = _ptr(rom, events + 4, count * OBJECT_SIZE)
            intervals.append((obj, obj + count * OBJECT_SIZE, m.label))
            objects_count += count
            for i in range(count):
                at = obj + i * OBJECT_SIZE
                local, gfx, kind = rom[at:at + 3]
                if local != i + 1:
                    raise PatchError(f"ID ou ordem inesperada em {m.label}, objeto {i}.")
                if _u32(rom, at + 16) != GENERIC_SCRIPT:
                    continue
                x, y = struct.unpack_from("<hh", rom, at + 4)
                movement = rom[at + 9]
                trainer_type, species, flag = _u16(rom, at + 12), _u16(rom, at + 14), _u16(rom, at + 20)
                if not (gfx == 0x98 and kind == 0 and movement == 8 and trainer_type == 0
                        and flag == 0x5000 + species and 1 <= species <= 1025
                        and 0 <= x < width and 0 <= y < height):
                    raise PatchError(f"Evento fixo não reconhecido: {m.label}, objeto {local}.")
                candidates.append(StaticEvent(m, i, local, at, species, x, y, flag,
                                              rom[at:at + OBJECT_SIZE]))
    intervals.sort()
    for a, b in zip(intervals, intervals[1:]):
        if a[1] > b[0]:
            raise PatchError(f"Objetos sobrepostos nos mapas {a[2]} e {b[2]}.")
    return candidates, objects_count


def category(species: wild.Species) -> str:
    if species.protected:
        return "lendario/mitico"
    if species.id in ULTRA_BEASTS:
        return "ultra beast"
    if species.id in PARADOX:
        return "paradox"
    return "comum"


def audit_shared_script(rom: bytes, events: Sequence[StaticEvent]) -> None:
    """Não deixar de fora uma referência direta ao script que não reconhecemos."""
    signature = struct.pack("<I", GENERIC_SCRIPT)
    references: set[int] = set()
    at = 0
    while True:
        at = rom.find(signature, at)
        if at < 0:
            break
        references.add(at)
        at += 1
    expected = {event.offset + 16 for event in events}
    if references != expected:
        raise PatchError("Há referências ao script fixo fora dos objetos reconhecidos.")


def reject_clone_targets(rom: bytes, maps: Sequence[MapRef], selected: Sequence[StaticEvent],
                         group_table: int = GROUP_TABLE) -> None:
    """Recusa mover qualquer objeto usado como alvo por um clone de outro mapa."""
    targets = {(e.map.group, e.map.number, e.local_id) for e in selected}
    for m in maps:
        array = _ptr(rom, group_table + 4 * m.group, 4 * (m.number + 1))
        header = _ptr(rom, array + 4 * m.number, 28)
        events = _ptr(rom, header + 4, 20)
        count = rom[events]
        if not count:
            continue
        obj = _ptr(rom, events + 4, count * OBJECT_SIZE)
        for i in range(count):
            at = obj + i * OBJECT_SIZE
            if rom[at + 2] == 0xFF:  # OBJ_KIND_CLONE
                target = (_u16(rom, at + 14), _u16(rom, at + 12), rom[at + 8])
                if target in targets:
                    raise PatchError(f"Objeto selecionado é alvo de clone em {m.label}.")


def plan_events(events: Sequence[StaticEvent], species: Mapping[int, wild.Species],
                covered: set[int]) -> list[StaticEvent]:
    """Somente comuns que já têm encontro selvagem estrutural elegível."""
    ids = [event.species for event in events]
    offsets = [event.offset for event in events]
    if len(ids) != len(set(ids)) or len(offsets) != len(set(offsets)):
        raise PatchError("Espécie ou objeto duplicado no inventário.")
    if any(i not in species for i in ids):
        raise PatchError("Espécie do evento ausente do catálogo.")
    selected = [event for event in events if category(species[event.species]) == "comum"]
    missing = {event.species for event in selected} - covered
    if missing:
        raise PatchError(f"Comuns sem encontro selvagem elegível: {sorted(missing)}")
    return selected


def apply_plan(rom: bytes, selected: Sequence[StaticEvent]) -> bytes:
    """Muda apenas x/y de cada objeto; falha se o registro foi modificado."""
    output = bytearray(rom)
    seen: set[int] = set()
    for event in selected:
        at = event.offset
        if at < 0 or at + OBJECT_SIZE > len(rom) or at in seen:
            raise PatchError("Objeto duplicado ou fora da ROM.")
        seen.add(at)
        if rom[at:at + OBJECT_SIZE] != event.original:
            raise PatchError("O objeto de origem não corresponde ao inventário.")
        struct.pack_into("<hh", output, at + 4, PARKED_COORD, PARKED_COORD)
    return bytes(output)


def verify_output(source: bytes, output: bytes, selected: Sequence[StaticEvent]) -> None:
    if len(source) != len(output):
        raise PatchError("Tamanho da ROM alterado.")
    expected = apply_plan(source, selected)
    if output != expected:
        raise PatchError("Diferença fora das coordenadas autorizadas.")


def prepare(rom: bytes) -> tuple[bytes, list[StaticEvent], list[StaticEvent], dict[int, wild.Species], list[wild.Table]]:
    validate_source(rom)
    checked_catalogs()
    maps = load_map_catalog()
    species = wild.load_species()
    wild_maps = wild.load_maps()
    events, count = parse_static_events(rom, maps)
    if count != 1982 or len(events) != 334:
        raise PatchError(f"Inventário inesperado: {count} objetos, {len(events)} eventos fixos.")
    audit_shared_script(rom, events)
    tables = wild.parse_tables(rom, wild_maps, species)
    selected = plan_events(events, species, wild.covered_species(tables))
    reject_clone_targets(rom, maps, selected)
    categories = Counter(category(species[e.species]) for e in events)
    if categories != {"lendario/mitico": 81, "ultra beast": 9, "paradox": 20, "comum": 224}:
        raise PatchError(f"Categorias inesperadas no inventário: {categories}.")
    output = apply_plan(rom, selected)
    verify_output(rom, output, selected)
    if OUTPUT_SHA256 and digest(output) != OUTPUT_SHA256:
        raise PatchError("A saída não corresponde ao hash da versão validada.")
    return output, events, selected, species, tables


def inventory_csv(events: Sequence[StaticEvent], selected: Sequence[StaticEvent],
                  species: Mapping[int, wild.Species], tables: Sequence[wild.Table]) -> str:
    """Lista o evento fixo e uma localização selvagem elegível quando existe."""
    guide = csv.DictReader(io.StringIO(wild.guide_csv(tables, species, [])))
    wild_by_id = {int(row["pokedex_nacional"]): row for row in guide}
    selected_offsets = {e.offset for e in selected}
    text = io.StringIO(newline="")
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(("mapa_fixo", "grupo", "mapa_id", "objeto_id", "pokedex_nacional", "pokemon",
                     "categoria", "situacao_fixo", "x_original", "y_original", "mapa_selvagem",
                     "metodo", "nivel_min", "nivel_max", "chance_por_encontro_pct"))
    for event in events:
        sp = species[event.species]
        guide_row = wild_by_id.get(event.species, {})
        writer.writerow((wild.readable_map(event.map.label), event.map.group, event.map.number, event.local_id,
                         sp.id, sp.name, category(sp),
                         "retirado do mapa" if event.offset in selected_offsets else "preservado",
                         event.x, event.y, guide_row.get("mapa", ""), guide_row.get("metodo", ""),
                         guide_row.get("nivel_min", ""), guide_row.get("nivel_max", ""),
                         guide_row.get("chance_por_encontro_pct", "")))
    return text.getvalue()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, help="ROM com selvagens e treino (será preservada)")
    parser.add_argument("--saida", type=Path, help="nova ROM .gba; não pode existir")
    parser.add_argument("--self-test", action="store_true", help="executa testes do patch")
    args = parser.parse_args(argv)
    if args.self_test:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_eventos_fixos.py")
        if not suite.countTestCases():
            print("[ERRO] Nenhum teste encontrado.", file=sys.stderr)
            return 1
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if not args.rom or not args.saida:
        parser.error("informe --rom e --saida, ou use --self-test")
    try:
        source = args.rom.read_bytes()
        output, events, selected, _, _ = prepare(source)
        treino_ev.write_new_file(args.rom, args.saida, output)
        print(f"Entrada preservada: SHA-256 {digest(source)}")
        print(f"Nova ROM: {args.saida} | SHA-256 {digest(output)}")
        print(f"Fixos comuns retirados: {len(selected)}; fixos especiais preservados: {len(events)-len(selected)}.")
        return 0
    except (OSError, PatchError, wild.PatchError, treino_ev.PatchError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
