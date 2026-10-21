#!/usr/bin/env python3
"""Inspect one local GBA MapHeader -> MapEvents pointer graph.

Addresses are GBA ROM addresses. This tool reports bytes/fields without assigning
upstream names to them. Structure offsets are the FireRed formats cross-checked in
reports/ciclo_12_map_headers_events_obj_templates.md.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any


def parse_int(value: str) -> int:
    return int(value, 0)


class Rom:
    def __init__(self, path: Path, gba_base: int) -> None:
        self.path = path
        self.data = path.read_bytes()
        self.base = gba_base

    def offset(self, address: int, size: int = 1) -> int:
        off = address - self.base
        if off < 0 or off + size > len(self.data):
            raise ValueError(
                f"GBA address 0x{address:08X} (+0x{size:X}) outside ROM "
                f"[0x{self.base:08X}, 0x{self.base + len(self.data):08X})"
            )
        return off

    def bytes(self, address: int, size: int) -> bytes:
        off = self.offset(address, size)
        return self.data[off : off + size]

    def u8(self, address: int) -> int:
        return self.bytes(address, 1)[0]

    def u16(self, address: int) -> int:
        return struct.unpack("<H", self.bytes(address, 2))[0]

    def s16(self, address: int) -> int:
        return struct.unpack("<h", self.bytes(address, 2))[0]

    def u32(self, address: int) -> int:
        return struct.unpack("<I", self.bytes(address, 4))[0]

    @staticmethod
    def addr(value: int) -> str:
        return f"0x{value:08X}"


def pointer(rom: Rom, address: int) -> int:
    return rom.u32(address)


def inspect(rom: Rom, group_table: int, group: int, map_num: int) -> dict[str, Any]:
    group_ptr_address = group_table + 4 * group
    group_ptr = pointer(rom, group_ptr_address)
    header_ptr_address = group_ptr + 4 * map_num
    header = pointer(rom, header_ptr_address)

    layout = pointer(rom, header)
    events = pointer(rom, header + 4)
    map_scripts = pointer(rom, header + 8)
    connections = pointer(rom, header + 12)
    header_fields = rom.bytes(header + 16, 12)

    layout_fields = None
    if layout:
        layout_fields = {
            "width": struct.unpack("<i", rom.bytes(layout, 4))[0],
            "height": struct.unpack("<i", rom.bytes(layout + 4, 4))[0],
            "border": pointer(rom, layout + 8),
            "map": pointer(rom, layout + 12),
            "primary_tileset": pointer(rom, layout + 16),
            "secondary_tileset": pointer(rom, layout + 20),
            "tail_hex": rom.bytes(layout + 24, 8).hex(),
        }

    event_counts = list(rom.bytes(events, 4)) if events else [0, 0, 0, 0]
    event_ptrs = [pointer(rom, events + 4 + 4 * i) for i in range(4)] if events else [0] * 4
    obj_count, warp_count, coord_count, bg_count = event_counts
    obj_ptr, warp_ptr, coord_ptr, bg_ptr = event_ptrs

    objects: list[dict[str, Any]] = []
    for i in range(obj_count):
        a = obj_ptr + 0x18 * i
        kind = rom.u8(a + 2)
        row: dict[str, Any] = {
            "address": rom.addr(a),
            "local_id": rom.u8(a),
            "graphics_id": rom.u8(a + 1),
            "kind": kind,
            "x": rom.s16(a + 4),
            "y": rom.s16(a + 6),
            "union_hex": rom.bytes(a + 8, 8).hex(),
            "script": rom.addr(rom.u32(a + 16)),
            "flag": f"0x{rom.u16(a + 20):04X}",
            "raw_hex": rom.bytes(a, 0x18).hex(),
        }
        if kind == 0:
            ranges = rom.u16(a + 10)
            row["normal"] = {
                "elevation": rom.u8(a + 8),
                "movement_type": rom.u8(a + 9),
                "range_x": ranges & 0xF,
                "range_y": (ranges >> 4) & 0xF,
                "trainer_type": rom.u16(a + 12),
                "trainer_range_or_berry_id": rom.u16(a + 14),
            }
        objects.append(row)

    warps = []
    for i in range(warp_count):
        a = warp_ptr + 8 * i
        warps.append({
            "address": rom.addr(a),
            "x": rom.s16(a), "y": rom.s16(a + 2),
            "elevation": rom.u8(a + 4), "warp_id": rom.u8(a + 5),
            "map_num": rom.u8(a + 6), "map_group": rom.u8(a + 7),
            "raw_hex": rom.bytes(a, 8).hex(),
        })

    coords = []
    for i in range(coord_count):
        a = coord_ptr + 0x10 * i
        coords.append({
            "address": rom.addr(a),
            "x": rom.u16(a), "y": rom.u16(a + 2),
            "elevation": rom.u8(a + 4), "var": f"0x{rom.u16(a + 6):04X}",
            "value": f"0x{rom.u16(a + 8):04X}",
            "script": rom.addr(rom.u32(a + 12)),
            "raw_hex": rom.bytes(a, 0x10).hex(),
        })

    backgrounds = []
    for i in range(bg_count):
        a = bg_ptr + 0x0C * i
        backgrounds.append({
            "address": rom.addr(a),
            "x": rom.u16(a), "y": rom.u16(a + 2),
            "elevation": rom.u8(a + 4), "kind": rom.u8(a + 5),
            "payload_hex": rom.bytes(a + 6, 6).hex(),
            "raw_hex": rom.bytes(a, 0x0C).hex(),
        })

    return {
        "rom": str(rom.path),
        "rom_size": len(rom.data),
        "indices": {"group": group, "map_num": map_num},
        "lookup": {
            "group_table": rom.addr(group_table),
            "group_pointer_address": rom.addr(group_ptr_address),
            "group_pointer": rom.addr(group_ptr),
            "header_pointer_address": rom.addr(header_ptr_address),
            "map_header": rom.addr(header),
        },
        "map_header": {
            "layout": rom.addr(layout), "events": rom.addr(events),
            "map_scripts": rom.addr(map_scripts), "connections": rom.addr(connections),
            "tail_0x10_to_0x1B_hex": header_fields.hex(),
        },
        "layout": layout_fields,
        "map_events": {
            "counts": {
                "objects": obj_count, "warps": warp_count,
                "coord_events": coord_count, "background_events": bg_count,
            },
            "pointers": {
                "objects": rom.addr(obj_ptr), "warps": rom.addr(warp_ptr),
                "coord_events": rom.addr(coord_ptr), "background_events": rom.addr(bg_ptr),
            },
            "objects": objects, "warps": warps,
            "coord_events": coords, "background_events": backgrounds,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="ROM .gba path")
    parser.add_argument("--group-table", type=parse_int, required=True, help="GBA address of the group pointer table")
    parser.add_argument("--group", type=int, required=True, help="map group index")
    parser.add_argument("--map-num", type=int, required=True, help="map number within group")
    parser.add_argument("--gba-base", type=parse_int, default=0x08000000, help="GBA base address (default: 0x08000000)")
    args = parser.parse_args()
    result = inspect(Rom(args.rom, args.gba_base), args.group_table, args.group, args.map_num)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
