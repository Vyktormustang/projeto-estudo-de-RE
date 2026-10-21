#!/usr/bin/env python3
"""Structural checks for the Eternatus species patch in a built FireRed ROM."""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

ROM_BASE = 0x08000000
SPECIES = 252
SPECIES_NAMES = 0x08245EE0
BASE_STATS = 0x08254784
LEVEL_UP_TABLE = 0x0825D7B4
FRONT_TABLE = 0x082350AC
BACK_TABLE = 0x0823654C
PALETTE_TABLE = 0x0823730C
SHINY_TABLE = 0x082380CC
FRONT_COORDS = 0x082349CC
BACK_COORDS = 0x08235E6C
ICON_TABLE = 0x083D37A0
ICON_PALETTE_INDEX = 0x083D3E80
ICON_PALETTE_TABLE = 0x083D4038
SPECIES_LIST = 0x08720000
ASSET_BASE = 0x08730000


def off(va: int) -> int:
    return va - ROM_BASE


def decompress_lz77(blob: bytes) -> bytes:
    if len(blob) < 4 or blob[0] != 0x10:
        raise ValueError("missing GBA LZ77 header")
    size = int.from_bytes(blob[1:4], "little")
    out = bytearray()
    i = 4
    while len(out) < size:
        flags = blob[i]
        i += 1
        for bit in range(7, -1, -1):
            if len(out) >= size:
                break
            if flags & (1 << bit):
                a, b = blob[i], blob[i + 1]
                i += 2
                length = (a >> 4) + 3
                disp = (((a & 0x0F) << 8) | b) + 1
                if disp > len(out):
                    raise ValueError("invalid LZ77 displacement")
                for _ in range(length):
                    out.append(out[-disp])
                    if len(out) == size:
                        break
            else:
                out.append(blob[i])
                i += 1
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path, nargs="?", default=Path("rom_mod/ANY_ITEM_SELECTOR_v1.3.gba"))
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    if len(rom) != 16 * 1024 * 1024:
        raise SystemExit(f"bad ROM length: {len(rom)}")

    def u32(va: int) -> int:
        return struct.unpack_from("<I", rom, off(va))[0]

    def row(va: int, index: int, stride: int = 8) -> bytes:
        at = off(va + index * stride)
        return rom[at:at + stride]

    name = rom[off(SPECIES_NAMES + SPECIES * 11):off(SPECIES_NAMES + (SPECIES + 1) * 11)]
    if name.split(b"\xff", 1)[0] != bytes((0xBB + ord(c) - ord("A")) for c in "ETERNATUS"):
        raise SystemExit("species name slot 252 is not ETERNATUS")

    stats = rom[off(BASE_STATS + SPECIES * 28):off(BASE_STATS + (SPECIES + 1) * 28)]
    if stats[:10] != bytes((140, 85, 95, 130, 145, 95, 3, 16, 3, 255)):
        raise SystemExit("base stats/types/catch/experience fields do not match Eternatus")
    if stats[16:26] != bytes((255, 120, 35, 5, 15, 15, 46, 0, 0, 6)):
        raise SystemExit("gender/growth/egg/ability fields do not match Eternatus")

    for table, expected_size in ((FRONT_TABLE, 2048), (BACK_TABLE, 2048)):
        ptr, size, tag = struct.unpack("<IHH", row(table, SPECIES))
        if size != expected_size or tag != SPECIES:
            raise SystemExit(f"bad battle sprite descriptor at {table:#x}")
        if len(decompress_lz77(rom[off(ptr):off(ptr) + 4096])) != expected_size:
            raise SystemExit(f"bad compressed battle sprite at {ptr:#x}")
    for table, tag in ((PALETTE_TABLE, SPECIES), (SHINY_TABLE, 500 + SPECIES)):
        ptr, got_tag, _ = struct.unpack("<IHH", row(table, SPECIES))
        if got_tag != tag or len(decompress_lz77(rom[off(ptr):off(ptr) + 128])) != 32:
            raise SystemExit(f"bad palette descriptor at {table:#x}")

    learnset_ptr = u32(LEVEL_UP_TABLE + SPECIES * 4)
    moves = []
    cursor = off(learnset_ptr)
    while True:
        word = struct.unpack_from("<H", rom, cursor)[0]
        cursor += 2
        if word == 0xFFFF:
            break
        moves.append((word >> 9, word & 0x1FF))
    if len(moves) != 14 or moves[:4] != [(1, 97), (1, 109), (1, 337), (1, 188)]:
        raise SystemExit(f"unexpected Eternatus learnset: {moves}")

    for table in (FRONT_COORDS, BACK_COORDS):
        if row(table, SPECIES, 2) != bytes((0x88, 0)):
            raise SystemExit(f"bad 64x64 sprite coordinates at {table:#x}")
    icon_ptr = struct.unpack_from("<I", rom, off(ICON_TABLE + SPECIES * 4))[0]
    if rom[off(icon_ptr):off(icon_ptr) + 512] == b"\xff" * 512:
        raise SystemExit("Eternatus icon is empty")
    if rom[off(ICON_PALETTE_INDEX + SPECIES)] != 3:
        raise SystemExit("Eternatus icon does not use the dedicated palette slot")
    pal_ptr, pal_tag, _ = struct.unpack("<IHH", row(ICON_PALETTE_TABLE, 3))
    if pal_tag != 0xDAC3 or len(rom[off(pal_ptr):off(pal_ptr) + 32]) != 32:
        raise SystemExit("dedicated icon palette slot is invalid")

    entries = [struct.unpack_from("<Ii", rom, off(SPECIES_LIST + i * 8)) for i in range(1, 388)]
    ids = [record_id for _, record_id in entries]
    expected_ids = [*range(1, 252), 252, *range(277, 412)]
    if ids != expected_ids:
        raise SystemExit("selector species list is not 386 originals plus Eternatus")
    print(f"PASS: {args.rom} contains Eternatus (internal species {SPECIES}), 387 selectable species, valid battle assets and learnset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
