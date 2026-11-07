#!/usr/bin/env python3
"""Acrescenta encontros selvagens à edição PT-BR Gen 1–9 deste projeto.

A ROM de entrada deve ser a build exata identificada abaixo. Somente IDs de
espécie em tabelas de encontros são alterados; níveis, chances, código,
objetos/eventos estáticos e encontros lendários existentes são preservados.
Não recebe nem baixa ROMs. Use --self-test para testar com dados sintéticos.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
import struct
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
BASE_SHA256 = "ecd157aa7eb642ee81ffbe7397d222981866c407d02643b6a83dd47bbbf8c27d"
ROM_SIZE = 0x1000000
ROM_START = 0x08000000
WILD_HEADERS = 0x7B784C
NAMES_TABLE = 0x232D18  # slot 0, seguido de 1025 nomes de 11 bytes
NAME_LENGTH = 11
UNOWN = 201
WATER_TYPE = 11  # ID da PokéAPI, usado apenas para distribuir habitats.

SLOTS = {"land": 12, "water": 5, "rock": 5, "fish": 10}
SLOT_CHANCES = {
    "land": (20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1),
    "water": (60, 30, 5, 4, 1),
    "rock": (60, 30, 5, 4, 1),
    # Cada grupo da pesca soma 100% separadamente; ver rod_group().
    "fish": (70, 30, 60, 20, 20, 40, 40, 15, 4, 1),
}
METHODS = {
    "land": "grama/caverna",
    "water": "surf",
    "rock": "Rock Smash",
    "old_rod": "vara velha",
    "good_rod": "vara boa",
    "super_rod": "supervara",
}
# Estes mapas não são usados para colocar ou contar novas espécies: há mapas
# temporários, estados de evento, batalhas especiais ou navegação insegura.
EXCLUDED_MAP_PARTS = (
    "SSANNE", "ALTERING_CAVE", "SAFARI_ZONE", "LOST_CAVE", "TANOBY_RUINS_",
    # A tabela existe, mas o mapa Route 21 South não tem tile de encontro terrestre.
    "MAP_ROUTE21_SOUTH",
)
TRAPPING_SPECIES = {50, 51, 202, 328, 360, 574, 575, 576}


class PatchError(ValueError):
    """Entrada incompatível ou uma garantia do patch não pôde ser cumprida."""


@dataclass(frozen=True)
class Species:
    id: int
    name: str
    generation: int
    types: tuple[int, ...]
    base_stat_total: int
    evolves_from: int | None
    legendary: bool
    mythical: bool

    @property
    def protected(self) -> bool:
        return self.legendary or self.mythical

    @property
    def water(self) -> bool:
        return WATER_TYPE in self.types


@dataclass(frozen=True)
class MapSpec:
    index: int
    group: int
    number: int
    symbol: str
    label: str
    present: tuple[bool, bool, bool, bool]

    @property
    def is_tanoby_chamber(self) -> bool:
        return "TANOBY_RUINS_" in self.symbol

    @property
    def eligible(self) -> bool:
        return not any(part in self.symbol for part in EXCLUDED_MAP_PARTS)


@dataclass(frozen=True)
class Slot:
    index: int
    offset: int  # endereço do struct, não do campo species
    min_level: int
    max_level: int
    species: int
    chance: int


@dataclass(frozen=True)
class Table:
    map: MapSpec
    kind: str
    info_offset: int
    data_offset: int
    encounter_rate: int
    slots: tuple[Slot, ...]


@dataclass(frozen=True)
class Change:
    table: Table
    slot: Slot
    new_species: int


def load_species(path: Path = ROOT / "data/species_gen1_9.csv") -> dict[int, Species]:
    result: dict[int, Species] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            i = int(row["id"])
            if i in result:
                raise PatchError(f"Espécie duplicada no catálogo: {i}")
            types = tuple(int(x) for x in (row["type1"], row["type2"]) if x)
            result[i] = Species(
                i, row["identifier"], int(row["generation"]), types,
                int(row["base_stat_total"]),
                int(row["evolves_from"]) if row["evolves_from"] else None,
                row["legendary"] == "1", row["mythical"] == "1",
            )
    if set(result) != set(range(1, 1026)) or sum(s.protected for s in result.values()) != 94:
        raise PatchError("Catálogo de espécies incompleto ou alterado")
    if not result[UNOWN].name == "unown":
        raise PatchError("O catálogo não usa os IDs nacionais esperados")
    return result


def load_maps(path: Path = ROOT / "data/firered_wild_maps.csv") -> list[MapSpec]:
    result = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result.append(MapSpec(
                int(row["index"]), int(row["group"]), int(row["map"]),
                row["symbol"], row["label"],
                tuple(row[k] == "1" for k in SLOTS),
            ))
    if len(result) != 132 or [m.index for m in result] != list(range(132)):
        raise PatchError("Catálogo de mapas incompleto ou alterado")
    return result


def _read_name(rom: bytes, species_id: int) -> str:
    start = NAMES_TABLE + species_id * NAME_LENGTH
    raw = rom[start : start + NAME_LENGTH].split(b"\xff", 1)[0]
    chars = []
    for c in raw:
        if 0xBB <= c <= 0xD4:
            chars.append(chr(c - 0xBB + ord("A")))
        elif c == 0:
            chars.append(" ")
        else:
            chars.append("?")
    return "".join(chars).strip()


def validate_source(rom: bytes) -> None:
    """A identificação por SHA evita aplicar offsets em outra ROM/hack."""
    sha = hashlib.sha256(rom).hexdigest()
    if len(rom) != ROM_SIZE or sha != BASE_SHA256:
        raise PatchError(
            "ROM incompatível. Use pokefirered_gen1-9_ptbr.gba (SHA-256 "
            f"{BASE_SHA256}); arquivo recebido: {sha}, {len(rom)} bytes."
        )
    if rom[0xAC:0xB0] != b"BPRE":
        raise PatchError("Cabeçalho de jogo inesperado")
    anchors = {
        1: "BULBASAUR", 4: "CHARMANDER", 25: "PIKACHU", 151: "MEW",
        201: "UNOWN", 251: "CELEBI", 252: "TREECKO", 387: "TURTWIG",
        570: "ZORUA", 650: "CHESPIN", 722: "ROWLET", 810: "GROOKEY",
        906: "SPRIGATITO", 1025: "PECHARUNT",
    }
    for i, expected in anchors.items():
        got = _read_name(rom, i)
        if got != expected:
            raise PatchError(f"Tabela de nomes inesperada: #{i} = {got!r}, não {expected!r}")


def _pointer(rom: bytes, location: int, length: int) -> int:
    if location < 0 or location + 4 > len(rom):
        raise PatchError(f"Leitura de ponteiro fora da ROM: 0x{location:X}")
    address = struct.unpack_from("<I", rom, location)[0]
    offset = address - ROM_START
    if offset < 0 or offset % 4 or offset + length > len(rom):
        raise PatchError(f"Ponteiro inválido 0x{address:08X} em 0x{location:X}")
    return offset


def parse_tables(
    rom: bytes, maps: Sequence[MapSpec], species: Mapping[int, Species],
    headers: int = WILD_HEADERS,
) -> list[Table]:
    """Lê as estruturas GBA e rejeita ponteiros e sobreposições suspeitas."""
    header_end = headers + (len(maps) + 1) * 20
    if headers < 0 or header_end > len(rom):
        raise PatchError("Tabela de cabeçalhos fora da ROM")
    if rom[header_end - 20 : header_end] != b"\xff\xff" + b"\x00" * 18:
        raise PatchError("Sentinela da tabela de encontros não corresponde")
    tables: list[Table] = []
    intervals = [(headers, header_end, "cabeçalhos")]
    infos: set[int] = set()
    for index, spec in enumerate(maps):
        start = headers + index * 20
        if spec.index != index or rom[start:start + 4] != bytes((spec.group, spec.number, 0, 0)):
            raise PatchError(f"Mapa inesperado no cabeçalho {index} @ 0x{start:X}")
        for k, kind in enumerate(SLOTS):
            location = start + 4 + 4 * k
            ptr = struct.unpack_from("<I", rom, location)[0]
            if bool(ptr) != spec.present[k]:
                raise PatchError(f"Método {kind} inesperado em {spec.symbol}")
            if ptr == 0:
                continue
            info = _pointer(rom, location, 8)
            # Não inferir como tratar ponteiros compartilhados por mapas/métodos.
            if info in infos:
                raise PatchError(f"Ponteiro de informações compartilhado em 0x{info:X}")
            infos.add(info)
            if rom[info + 1:info + 4] != b"\x00\x00\x00":
                raise PatchError(f"Preenchimento de informações inesperado em 0x{info:X}")
            rate = rom[info]
            if not 1 <= rate <= 100:
                raise PatchError(f"Taxa inválida em 0x{info:X}: {rate}")
            data = _pointer(rom, info + 4, 4 * SLOTS[kind])
            slots: list[Slot] = []
            for i in range(SLOTS[kind]):
                slot_off = data + i * 4
                lo, hi, s = struct.unpack_from("<BBH", rom, slot_off)
                if not (1 <= lo <= hi <= 100) or s not in species:
                    raise PatchError(f"Slot inválido em 0x{slot_off:X}: {lo}, {hi}, espécie {s}")
                slots.append(Slot(i, slot_off, lo, hi, s, SLOT_CHANCES[kind][i]))
            intervals.extend(((info, info + 8, f"informações {spec.symbol}/{kind}"),
                              (data, data + SLOTS[kind] * 4, f"slots {spec.symbol}/{kind}")))
            tables.append(Table(spec, kind, info, data, rate, tuple(slots)))
    # Recusar qualquer alias, inclusive slots compartilhados parcialmente ou
    # um array que aponte para cabeçalhos/outras informações.
    intervals.sort()
    for left, right in zip(intervals, intervals[1:]):
        if left[1] > right[0]:
            raise PatchError(f"Estruturas sobrepostas: {left[2]} e {right[2]}")
    return tables


def rod_group(kind: str, slot: int) -> str:
    if kind != "fish":
        return kind
    if slot < 2:
        return "old_rod"
    if slot < 5:
        return "good_rod"
    return "super_rod"


def covered_species(tables: Sequence[Table], allow_unown: bool = True) -> set[int]:
    """Espécies em grama/caverna ou surf; Unown somente nas câmaras Tanoby.

    Pesca e Rock Smash permanecem intactos, mas não são contados como única
    forma de obtenção para evitar depender de rochas ou pontos de pesca incertos.
    """
    seen = {
        slot.species for table in tables
        if table.map.eligible and table.kind in {"land", "water"} for slot in table.slots
    }
    if allow_unown and any(
        slot.species == UNOWN for table in tables if table.map.is_tanoby_chamber
        for slot in table.slots
    ):
        seen.add(UNOWN)
    return seen


def required_level(species: Species) -> int:
    """Heurística conservadora de progressão; não altera níveis do jogo."""
    bst = species.base_stat_total
    level = 30 if bst >= 550 else 22 if bst >= 500 else 16 if bst >= 450 else 10 if bst >= 400 else 2
    if species.evolves_from is not None:
        level = max(level, 8)
    if species.id in TRAPPING_SPECIES:
        level = max(level, 15)
    return level


def _theme_penalty(species: Species, symbol: str) -> int:
    """Preferência, não restrição, por áreas com temas apropriados."""
    types = set(species.types)
    if "POWER_PLANT" in symbol:
        preferred = {9, 13}
    elif "POKEMON_TOWER" in symbol or "LOST_CAVE" in symbol:
        preferred = {8, 14, 17}
    elif "FOREST" in symbol or "PATTERN_BUSH" in symbol:
        preferred = {3, 7, 12, 18}
    elif "ICE" in symbol or "SEAFOAM" in symbol:
        preferred = {11, 15}
    elif "EMBER" in symbol:
        preferred = {5, 6, 10}
    elif any(part in symbol for part in ("CAVE", "MOON", "TUNNEL", "VICTORY_ROAD")):
        preferred = {5, 6, 8, 9, 17}
    else:
        return 0
    return 0 if types & preferred else 1


def _stable_tiebreak(species_id: int, slot_offset: int) -> int:
    data = struct.pack("<II", species_id, slot_offset)
    return int.from_bytes(hashlib.blake2s(data, digest_size=4, person=b"wild-v1").digest(), "little")


def protected_slots(tables: Sequence[Table], species: Mapping[int, Species]) -> set[int]:
    """Preserva diversidade local, métodos de pesca e todas as espécies existentes."""
    protected: set[int] = set()
    occurrences: dict[int, list[tuple[Table, Slot]]] = defaultdict(list)
    for table in tables:
        for slot in table.slots:
            if species[slot.species].protected or slot.species == UNOWN:
                protected.add(slot.offset)
        if not table.map.eligible:
            protected.update(slot.offset for slot in table.slots)
            continue
        groups: dict[str, list[Slot]] = defaultdict(list)
        for slot in table.slots:
            groups[rod_group(table.kind, slot.index)].append(slot)
            if table.kind in {"land", "water"}:
                occurrences[slot.species].append((table, slot))
        for group in groups.values():
            # Manter as duas espécies mais prováveis por tabela terrestre, uma
            # por tabela de água/rocha e uma por tipo de vara em cada mapa.
            max_by_species: dict[int, Slot] = {}
            for slot in group:
                old = max_by_species.get(slot.species)
                if old is None or (slot.chance, -slot.index) > (old.chance, -old.index):
                    max_by_species[slot.species] = slot
            count = 2 if table.kind == "land" else 1
            representatives = sorted(max_by_species.values(), key=lambda s: (-s.chance, s.index))
            protected.update(slot.offset for slot in representatives[:count])
    # Além dos representantes locais, garantir pelo menos uma ocorrência
    # em tabelas elegíveis para cada espécie que já existia nesses métodos.
    # A acessibilidade por eventos e caminhos não pode ser inferida daqui.
    for entries in occurrences.values():
        if not any(slot.offset in protected for _, slot in entries):
            _, best = min(entries, key=lambda p: (-p[1].chance, p[0].map.index, p[1].index))
            protected.add(best.offset)
    return protected


def plan_changes(tables: Sequence[Table], species: Mapping[int, Species]) -> list[Change]:
    current = covered_species(tables)
    if UNOWN in species and UNOWN not in current:
        raise PatchError("Unown não está disponível nas câmaras Tanoby; patch cancelado")
    targets = {s.id for s in species.values() if not s.protected}
    missing = targets - current
    if UNOWN in missing:
        raise PatchError("Unown não pode ser adicionado fora das câmaras Tanoby")
    protected = protected_slots(tables, species)
    available: dict[str, list[tuple[Table, Slot]]] = {"land": [], "water": []}
    for table in tables:
        if not table.map.eligible or table.kind not in available:
            continue
        available[table.kind].extend((table, slot) for slot in table.slots if slot.offset not in protected)
    # Mais exigentes primeiro: evita reservar todos os slots tardios para as
    # formas iniciais. O hash é estável entre execuções e versões de Python.
    order = sorted(missing, key=lambda i: (
        -required_level(species[i]), -species[i].base_stat_total, _stable_tiebreak(i, 0)
    ))
    assigned_per_table: Counter[int] = Counter()
    changes: list[Change] = []
    for i in order:
        mon = species[i]
        method = "water" if mon.water else "land"
        level = required_level(mon)
        options = [(table, slot) for table, slot in available[method] if slot.min_level >= level]
        if not options:
            raise PatchError(
                f"Não há slot {method} seguro, nível >= {level}, para #{i} {mon.name}. "
                "Nenhuma ROM foi gravada."
            )
        def score(entry: tuple[Table, Slot]) -> tuple[int, ...]:
            table, slot = entry
            return (
                int(slot.chance < 4),
                assigned_per_table[table.data_offset],
                _theme_penalty(mon, table.map.symbol),
                (slot.min_level - level) // 10,
                -slot.chance,
                abs(slot.min_level - level),
                _stable_tiebreak(i, slot.offset),
            )
        table, slot = min(options, key=score)
        available[method].remove((table, slot))
        assigned_per_table[table.data_offset] += 1
        changes.append(Change(table, slot, i))
    return changes


def apply_changes(rom: bytes, changes: Sequence[Change], species: Mapping[int, Species]) -> bytes:
    output = bytearray(rom)
    seen: set[int] = set()
    for change in changes:
        slot = change.slot
        if (slot.offset in seen or not change.table.map.eligible or change.table.kind not in {"land", "water"}
                or species[slot.species].protected or slot.species == UNOWN
                or species[change.new_species].protected or change.new_species == UNOWN):
            raise PatchError("Plano contém alteração proibida ou duplicada")
        if rom[slot.offset:slot.offset + 4] != struct.pack("<BBH", slot.min_level, slot.max_level, slot.species):
            raise PatchError(f"Slot de origem foi alterado em 0x{slot.offset:X}")
        seen.add(slot.offset)
        struct.pack_into("<H", output, slot.offset + 2, change.new_species)
    # A lista de bytes alteráveis não inclui níveis, taxas, ponteiros, eventos,
    # sprites, código ou qualquer encontro lendário existente.
    allowed = {slot_offset + d for slot_offset in seen for d in (2, 3)}
    if any(i not in allowed for i, (before, after) in enumerate(zip(rom, output)) if before != after):
        raise PatchError("Diferença detectada fora dos campos de espécie aprovados")
    return bytes(output)


def verify_result(
    original: bytes, output: bytes, before: Sequence[Table], maps: Sequence[MapSpec],
    species: Mapping[int, Species], changes: Sequence[Change], headers: int = WILD_HEADERS,
) -> list[Table]:
    if len(original) != len(output):
        raise PatchError("O tamanho da ROM foi alterado")
    after = parse_tables(output, maps, species, headers)
    old_covered, new_covered = covered_species(before), covered_species(after)
    missing = {s.id for s in species.values() if not s.protected} - new_covered
    if missing:
        raise PatchError(f"Espécies não lendárias sem encontro normal: {sorted(missing)}")
    if old_covered - new_covered:
        raise PatchError(f"Espécies preexistentes perdidas: {sorted(old_covered - new_covered)}")
    for old, new in zip(before, after):
        if (old.map != new.map or old.kind != new.kind or old.info_offset != new.info_offset
                or old.data_offset != new.data_offset or old.encounter_rate != new.encounter_rate):
            raise PatchError("Metadados de encontro foram alterados")
        for a, b in zip(old.slots, new.slots):
            if (a.offset, a.min_level, a.max_level, a.chance) != (b.offset, b.min_level, b.max_level, b.chance):
                raise PatchError("Níveis ou estrutura dos encontros foram alterados")
            if (species[a.species].protected or a.species == UNOWN or not old.map.eligible) and a.species != b.species:
                raise PatchError("Encontro lendário, Unown ou mapa protegido foi alterado")
    if len({c.new_species for c in changes}) != len(changes):
        raise PatchError("O plano distribuiu uma espécie mais de uma vez")
    return after


def readable_map(label: str) -> str:
    import re
    s = label.replace("_", " ")
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", s)
    return s.replace("Ssanne", "S.S. Anne")


def guide_csv(
    after: Sequence[Table], species: Mapping[int, Species], changes: Sequence[Change]
) -> str:
    """Uma localização elegível (a mais provável) por espécie não lendária.

    Os mapas não são uma prova de acessibilidade por eventos ou caminhos.
    """
    choices: dict[int, list[dict]] = defaultdict(list)
    new_ids = {change.new_species for change in changes}
    for table in after:
        # Unown depende de código especial das câmaras. Não listá-lo fora delas.
        if not table.map.eligible and not table.map.is_tanoby_chamber:
            continue
        if table.kind not in {"land", "water"}:
            continue
        grouped: dict[tuple[int, str], list[Slot]] = defaultdict(list)
        for slot in table.slots:
            if species[slot.species].protected:
                continue
            if table.map.is_tanoby_chamber and slot.species != UNOWN:
                continue
            grouped[(slot.species, rod_group(table.kind, slot.index))].append(slot)
        for (mon, method), slots in grouped.items():
            choices[mon].append({
                "mapa": readable_map(table.map.label), "simbolo_mapa": table.map.symbol,
                "metodo": METHODS[method], "nivel_min": min(s.min_level for s in slots),
                "nivel_max": max(s.max_level for s in slots),
                "chance_por_encontro_pct": sum(s.chance for s in slots),
                "ordem": table.map.index,
            })
    out = io.StringIO(newline="")
    fields = ["pokedex_nacional", "pokemon", "mapa", "simbolo_mapa", "metodo",
              "nivel_min", "nivel_max", "chance_por_encontro_pct", "situacao"]
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for i, mon in sorted(species.items()):
        if mon.protected:
            continue
        if not choices[i]:
            raise PatchError(f"Sem localização para o guia: #{i} {mon.name}")
        best = min(choices[i], key=lambda v: (-v["chance_por_encontro_pct"], v["ordem"], v["metodo"]))
        writer.writerow({
            "pokedex_nacional": i, "pokemon": mon.name,
            **{k: v for k, v in best.items() if k != "ordem"},
            "situacao": "adicionado" if i in new_ids else "ja existente",
        })
    return out.getvalue()


def make_patch(rom: bytes, maps: Sequence[MapSpec], species: Mapping[int, Species],
               headers: int = WILD_HEADERS) -> tuple[bytes, list[Table], list[Change], str]:
    before = parse_tables(rom, maps, species, headers)
    changes = plan_changes(before, species)
    output = apply_changes(rom, changes, species)
    after = verify_result(rom, output, before, maps, species, changes, headers)
    return output, after, changes, guide_csv(after, species, changes)


def _write_output(path: Path, data: bytes, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("wb" if force else "xb") as f:
            f.write(data)
    except FileExistsError as exc:
        raise PatchError(f"Arquivo já existe: {path}. Use --force para substituí-lo.") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, help="ROM PT-BR Gen 1–9 de origem (não é alterada)")
    parser.add_argument("--saida", type=Path, help="caminho de uma nova ROM .gba")
    parser.add_argument("--guia", type=Path, help="CSV de localização de cada espécie não lendária")
    parser.add_argument("--force", action="store_true", help="substitui saídas existentes, nunca a ROM de entrada")
    parser.add_argument("--self-test", action="store_true", help="executa testes com ROMs sintéticas")
    args = parser.parse_args(argv)
    if args.self_test:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
        if suite.countTestCases() == 0:
            print("[ERRO] Nenhum teste foi encontrado; validação não executada.", file=sys.stderr)
            return 1
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if not args.rom or not args.saida or not args.guia:
        parser.error("informe --rom, --saida e --guia, ou use --self-test")
    try:
        source = args.rom.resolve()
        destinations = [args.saida.resolve(), args.guia.resolve()]
        if source in destinations or destinations[0] == destinations[1]:
            raise PatchError("ROM de entrada, saída e guia precisam ser arquivos diferentes")
        # resolve() cobre links simbólicos; samefile() cobre hard links.
        if args.saida.exists() and args.guia.exists() and os.path.samefile(args.saida, args.guia):
            raise PatchError("A ROM de saída e o guia apontam para o mesmo arquivo")
        for path in (args.saida, args.guia):
            if path.exists() and os.path.samefile(args.rom, path):
                raise PatchError("Uma saída aponta para a ROM de entrada")
            if path.exists() and not args.force:
                raise PatchError(f"Arquivo já existe: {path}. Use --force para substituí-lo.")
        rom = args.rom.read_bytes()
        validate_source(rom)
        species, maps = load_species(), load_maps()
        output, tables, changes, guide = make_patch(rom, maps, species)
        _write_output(args.saida, output, args.force)
        _write_output(args.guia, guide.encode("utf-8"), args.force)
        print(f"ROM de entrada: SHA-256 {hashlib.sha256(rom).hexdigest()}")
        print(f"Nova ROM: {args.saida} (SHA-256 {hashlib.sha256(output).hexdigest()})")
        print(f"Guia: {args.guia} ({sum(not s.protected for s in species.values())} espécies)")
        print(f"Espécies acrescentadas: {len(changes)}; tabelas lidas: {len(tables)}")
        print("Lendários/míticos e eventos estáticos existentes: preservados.")
        return 0
    except (OSError, PatchError, ValueError, KeyError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
