#!/usr/bin/env python3
"""Build the pause-menu item and species selector mod for the Brazilian FireRed ROM.

The ROM is always built from the unmodified base. Existing BAG_MOD_v3 artifacts
are deliberately not used or overwritten.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import struct
import unicodedata
from pathlib import Path

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB, KS_MODE_LITTLE_ENDIAN

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = ROOT / "rom/Pokemon - Fire Red (BR).gba"
DEFAULT_OUT = ROOT / "rom_mod/ANY_ITEM_SELECTOR_v1.4.gba"

ROM_BASE = 0x08000000
BRIDGE_VA = 0x08456734
PAYLOAD_VA = 0x0871A906       # aligned Thumb code entry, within confirmed FF run
TASK_VA = 0x0871AC00          # item-selector task engine
DATA_VA = 0x0871B000          # generated tables/templates/strings
SPECIES_TASK_VA = 0x0871E000  # independent species-selector task engine
SPECIES_LIST_VA = 0x08720000  # 387 individually selectable species entries
ETERNATUS_ASSETS_VA = 0x08730000  # injected battle sprites, palettes, icon and learnset
SPECIES_NAMES_VA = 0x08245EE0 # 11-byte gSpeciesNames slots, including SPECIES_NONE
BASE_STATS_VA = 0x08254784   # 28-byte ROM records indexed by internal species ID
LEVEL_UP_LEARNSETS_VA = 0x0825D7B4
FRONT_PIC_TABLE_VA = 0x082350AC
BACK_PIC_TABLE_VA = 0x0823654C
MON_PALETTE_TABLE_VA = 0x0823730C
SHINY_PALETTE_TABLE_VA = 0x082380CC
FRONT_PIC_COORDS_VA = 0x082349CC
BACK_PIC_COORDS_VA = 0x08235E6C
MON_ICON_TABLE_VA = 0x083D37A0
MON_ICON_PALETTE_INDEX_VA = 0x083D3E80
MON_ICON_PALETTE_TABLE_VA = 0x083D4038
ETERNATUS_SPECIES_ID = 252
ACTION_TABLE_EXIT_LABEL_VA = 0x083A7374
ACTION_TABLE_EXIT_CALLBACK_VA = 0x083A7378
ORIGINAL_EXIT_LABEL = 0x0841629D
ORIGINAL_EXIT_CALLBACK = 0x0806F541
FADE_EXIT_CALLBACK_PTR_VA = 0x0806F3C4
CUSTOM_CALLBACK_VA = BRIDGE_VA + 25
CREATE_MON = 0x0803DA55
GIVE_MON_TO_PLAYER = 0x08040B15
IS_LINK_ACTIVE = 0x0805642D

SETUP_HOOK_VA = 0x0806ED8C
LABEL_HOOK_VA = 0x0806EFAE
DESC_TABLE_HOOK_VA = 0x0806F104
DESC_TABLE_ORIG_VA = 0x083A7394
SAFARI_CALLBACK_VA = 0x0806F554

ORIG_SETUP = bytes.fromhex("00 f0 10 f8")
ORIG_LABEL = bytes.fromhex("01 68 48 46")
ORIG_DESC_TABLE_LOADS = bytes.fromhex("0c 4a 0d 49")
ORIG_CALLBACK = bytes.fromhex(
    "00 b5 ff f7 df fc 88 f0 1d fa 00 f0 9f fc 31 f0 eb fc "
    "01 20 02 bc 08 47"
)


def off(va: int) -> int:
    return va - ROM_BASE


def thumb(src: str, address: int) -> bytes:
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB | KS_MODE_LITTLE_ENDIAN)
    try:
        enc, _ = ks.asm(src, address)
    except Exception as exc:
        raise RuntimeError(f"Thumb assembly error at {address:#x}: {exc}\n{src}") from exc
    return bytes(enc)


def gba_text(text: str) -> bytes:
    out = bytearray()
    for ch in text:
        if ch == " ":
            out.append(0x00)
        elif "A" <= ch <= "Z":
            out.append(0xBB + ord(ch) - ord("A"))
        elif "0" <= ch <= "9":
            out.append(0xA1 + ord(ch) - ord("0"))
        elif ch == "!":
            out.append(0xAB)
        elif ch == "?":
            out.append(0xAC)
        elif ch == ".":
            out.append(0xAD)
        elif ch == "-":
            out.append(0xAE)
        else:
            raise ValueError(f"unsupported Gen3 text character: {ch!r}")
    out.append(0xFF)
    return bytes(out)


def species_ids() -> list[int]:
    # Reuse only internal slot 252 (one OLD_UNOWN placeholder); all other
    # placeholders and the egg remain excluded.
    ids = [*range(1, ETERNATUS_SPECIES_ID), ETERNATUS_SPECIES_ID, *range(277, 412)]
    if len(ids) != 387 or len(set(ids)) != len(ids):
        raise AssertionError("species whitelist must contain exactly 387 unique IDs")
    return ids


def decode_species_name(rom: bytes | bytearray, species_id: int) -> str:
    """Decode the visible name bytes used by the ROM's 11-byte species slots."""
    if species_id == ETERNATUS_SPECIES_ID:
        return "ETERNATUS"  # the base ROM still labels slot 252 as OLD_UNOWN
    start = off(SPECIES_NAMES_VA + species_id * 11)
    chars = []
    for code in rom[start:start + 11]:
        if code == 0xFF:
            break
        if code == 0:
            chars.append(" ")
        elif 0xA1 <= code <= 0xAA:
            chars.append(str(code - 0xA1))
        elif 0xBB <= code <= 0xD4:
            chars.append(chr(ord("A") + code - 0xBB))
        else:
            chars.append({
                0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-",
                0xB4: "'", 0xB5: "♂", 0xB6: "♀", 0xB8: ",", 0xBA: "/",
            }.get(code, ""))
    return "".join(chars).strip()


def species_sort_key(name: str) -> str:
    # Ignore spaces/punctuation/sex symbols for natural A-Z ordering; retain
    # digits (e.g. Porygon2) and normalize accents if a localized ROM uses any.
    normalized = unicodedata.normalize("NFKD", name).casefold()
    return "".join(char for char in normalized if char.isalnum())


def species_records(label: int, rom: bytes | bytearray) -> bytes:
    ordered = sorted(
        species_ids(),
        key=lambda species_id: (species_sort_key(decode_species_name(rom, species_id)), species_id),
    )
    records = [list_item(label, -3)]
    records.extend(
        list_item(SPECIES_NAMES_VA + species_id * 11, species_id)
        for species_id in ordered
    )
    return b"".join(records)


def lz77_compress(data: bytes) -> bytes:
    """Compress bytes using the GBA BIOS 0x10 LZ77 format."""
    if len(data) > 0xFFFFFF:
        raise ValueError("GBA LZ77 input exceeds 24-bit length")
    out = bytearray((0x10, len(data) & 0xFF, (len(data) >> 8) & 0xFF, (len(data) >> 16) & 0xFF))
    positions: dict[bytes, list[int]] = {}
    pos = 0
    while pos < len(data):
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(7, -1, -1):
            if pos >= len(data):
                break
            best_len = 0
            best_disp = 0
            key = data[pos:pos + 3]
            for candidate in reversed(positions.get(key, ())[-96:]):
                disp = pos - candidate
                if disp > 0x1000:
                    break
                length = 3
                while length < 18 and pos + length < len(data) and data[candidate + (length % disp)] == data[pos + length]:
                    length += 1
                if length > best_len:
                    best_len, best_disp = length, disp
                    if length == 18:
                        break
            if best_len >= 3:
                flags |= 1 << bit
                token = ((best_len - 3) << 12) | (best_disp - 1)
                out.extend(((token >> 8) & 0xFF, token & 0xFF))
                consumed = best_len
            else:
                out.append(data[pos])
                consumed = 1
            for prior in range(pos, pos + consumed):
                if prior + 2 < len(data):
                    positions.setdefault(data[prior:prior + 3], []).append(prior)
            pos += consumed
        out[flag_pos] = flags
    return bytes(out)


def eternatus_learnset() -> bytes:
    # Gen III-compatible equivalents for Eternatus's later-generation moves.
    # Four level-1 moves are intentional: a level-5 creation starts with these.
    entries = [
        (1, 97),    # Agility
        (1, 109),   # Confuse Ray
        (1, 337),   # Dragon Claw (Dragon Tail equivalent)
        (1, 188),   # Sludge Bomb (Poison Tail equivalent)
        (8, 92),    # Toxic
        (16, 51),   # Acid (Venoshock equivalent)
        (24, 349),  # Dragon Dance
        (32, 139),  # Poison Gas (Cross Poison equivalent)
        (40, 225),  # Dragon Breath (Dragon Pulse equivalent)
        (48, 53),   # Flamethrower
        (56, 82),   # Dragon Rage (Dynamax Cannon equivalent)
        (64, 322),  # Cosmic Power
        (72, 105),  # Recover
        (80, 63),   # Hyper Beam (Eternabeam equivalent)
    ]
    return b"".join(struct.pack("<H", (level << 9) | move) for level, move in entries) + b"\xff\xff"


def make_eternatus_assets() -> tuple[bytes, dict[str, int]]:
    asset_dir = ROOT / "assets/eternatus"
    front_raw = (asset_dir / "front.4bpp").read_bytes()
    back_raw = (asset_dir / "back.4bpp").read_bytes()
    if len(front_raw) != 2048 or len(back_raw) != 2048:
        raise ValueError("Eternatus front/back graphics must each be 2048 bytes before compression")
    files = {
        "front": lz77_compress(front_raw),
        "back": lz77_compress(back_raw),
        "normal_palette": lz77_compress((asset_dir / "normal.pal").read_bytes()),
        "shiny_palette": lz77_compress((asset_dir / "shiny.pal").read_bytes()),
        "icon": (asset_dir / "icon.4bpp").read_bytes(),
        "icon_palette": (asset_dir / "icon.pal").read_bytes(),
        "learnset": eternatus_learnset(),
    }
    expected_lengths = {"front": None, "back": None, "icon": 512,
                        "normal_palette": None, "shiny_palette": None,
                        "icon_palette": 32, "learnset": 30}
    for key, expected in expected_lengths.items():
        if expected is not None and len(files[key]) != expected:
            raise ValueError(f"Eternatus asset {key} has {len(files[key])} bytes; expected {expected}")
    data = bytearray()
    symbols: dict[str, int] = {}
    for name, payload in files.items():
        while (ETERNATUS_ASSETS_VA + len(data)) % 4:
            data.append(0)
        symbols[name] = ETERNATUS_ASSETS_VA + len(data)
        data.extend(payload)
    return bytes(data), symbols


def item_records() -> list[tuple[int, int]]:
    result = []
    with (ROOT / "reports/item_ids_firered_ptbr.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["classificacao"] != "nomeado":
                continue
            item_id = int(row["id"], 10)
            record_id = int(row["id_guardado_no_registro"], 10)
            if item_id != record_id or item_id == 0:
                raise ValueError(f"item CSV record mismatch at ID {item_id}")
            name_va = ROM_BASE + int(row["offset_rom"], 16)
            result.append((name_va, item_id))
    if len(result) != 307:
        raise ValueError(f"expected 307 named items, got {len(result)}")
    return result


def list_item(label: int, index: int) -> bytes:
    return struct.pack("<Ii", label, index)


def menu_template(items: int, total: int, max_showed: int = 6) -> bytes:
    # ListMenuTemplate, 0x18 bytes. windowId is patched into a stack copy at runtime.
    return struct.pack(
        "<IIIHH8B",
        items, 0, 0, total, max_showed,
        0, 0, 9, 1, 0x22, 0x31, 0x10, 0x01,
    )


def make_data(desc_pointers: tuple[int, ...], rom: bytes | bytearray) -> tuple[bytes, bytes, dict[str, int]]:
    p = DATA_VA
    data = bytearray()
    symbols: dict[str, int] = {}

    def reserve(name: str, payload: bytes, alignment: int = 4) -> int:
        nonlocal p, data
        while p % alignment:
            data.append(0)
            p += 1
        symbols[name] = p
        data.extend(payload)
        p += len(payload)
        return symbols[name]

    labels = {
        "label_mod_menu": reserve("label_mod_menu", gba_text("MODS")),
        "label_items": reserve("label_items", gba_text("ITENS")),
        "label_species": reserve("label_species", gba_text("POKEMON")),
        "label_exit": reserve("label_exit", gba_text("SAIR")),
        "label_qty": reserve("label_qty", gba_text("QUANTIDADE")),

        "label_result": reserve("label_result", gba_text("RESULTADO")),
        "label_success": reserve("label_success", gba_text("ADICIONADO")),
        "label_failure": reserve("label_failure", gba_text("NAO FOI POSSIVEL")),
        "label_species_added": reserve("label_species_added", gba_text("POKEMON ADICIONADO")),
        "label_species_pc": reserve("label_species_pc", gba_text("ENVIADO AO PC")),
        "label_species_full": reserve("label_species_full", gba_text("PC CHEIO")),
        "label_desc": reserve("label_desc", gba_text("ESCOLHA UMA OPCAO")),
    }
    if len(desc_pointers) != 9:
        raise ValueError(f"expected nine native description pointers, got {len(desc_pointers)}")
    custom_desc_pointers = (*desc_pointers[:6], symbols["label_desc"], *desc_pointers[7:])
    reserve("custom_desc_table", struct.pack("<9I", *custom_desc_pointers))
    number_labels = []
    for n in range(1, 100):
        number_labels.append(reserve(f"num_{n}", gba_text(f"{n}")))

    items = item_records()
    entries = [list_item(labels["label_items"], -3)]
    entries.extend(list_item(name_va, item_id) for name_va, item_id in items)
    items_va = reserve("items", b"".join(entries))

    mode_entries = [
        list_item(labels["label_mod_menu"], -3),
        list_item(labels["label_items"], 1),
        list_item(labels["label_species"], 2),
        list_item(labels["label_exit"], 3),
    ]
    modes_va = reserve("modes", b"".join(mode_entries))

    qty_entries = [list_item(labels["label_qty"], -3)]
    qty_entries.extend(list_item(number_labels[n - 1], n) for n in range(1, 100))
    qty99_va = reserve("qty99", b"".join(qty_entries))
    qty1_va = reserve("qty1", list_item(labels["label_qty"], -3) + list_item(number_labels[0], 1))
    success_va = reserve("success", list_item(labels["label_result"], -3) + list_item(labels["label_success"], 0))
    failure_va = reserve("failure", list_item(labels["label_result"], -3) + list_item(labels["label_failure"], 0))
    species_added_va = reserve("species_added", list_item(labels["label_result"], -3) + list_item(labels["label_species_added"], 0))
    species_pc_va = reserve("species_pc", list_item(labels["label_result"], -3) + list_item(labels["label_species_pc"], 0))
    species_full_va = reserve("species_full", list_item(labels["label_result"], -3) + list_item(labels["label_species_full"], 0))

    template_items_va = reserve("template_items", menu_template(items_va, len(entries) - 1))
    template_modes_va = reserve("template_modes", menu_template(modes_va, len(mode_entries) - 1))
    template_qty99_va = reserve("template_qty99", menu_template(qty99_va, len(qty_entries) - 1))
    template_qty1_va = reserve("template_qty1", menu_template(qty1_va, 1))
    template_success_va = reserve("template_success", menu_template(success_va, 1))
    template_failure_va = reserve("template_failure", menu_template(failure_va, 1))
    template_species_va = reserve("template_species", menu_template(SPECIES_LIST_VA, 387))
    template_species_added_va = reserve("template_species_added", menu_template(species_added_va, 1))
    template_species_pc_va = reserve("template_species_pc", menu_template(species_pc_va, 1))
    template_species_full_va = reserve("template_species_full", menu_template(species_full_va, 1))

    # BG0 window at the native start-menu allocation. Its 15x13 tile buffer
    # ends at tile 0x200, avoiding corruption of the overworld tile graphics.
    window_va = reserve("window", struct.pack("<BBBBBBH", 0, 14, 1, 15, 13, 15, 0x13D))
    symbols.update({
        "items": items_va,
        "modes": modes_va,
        "qty99": qty99_va,
        "qty1": qty1_va,
        "success": success_va,
        "failure": failure_va,
        "species_added": species_added_va,
        "species_pc": species_pc_va,
        "species_full": species_full_va,
        "template_items": template_items_va,
        "template_modes": template_modes_va,
        "template_qty99": template_qty99_va,
        "template_qty1": template_qty1_va,
        "template_success": template_success_va,
        "template_failure": template_failure_va,
        "template_species": template_species_va,
        "template_species_added": template_species_added_va,
        "template_species_pc": template_species_pc_va,
        "template_species_full": template_species_full_va,
        "window": window_va,
    })
    species_data = species_records(labels["label_species"], rom)
    assert DATA_VA + len(data) < SPECIES_TASK_VA
    assert SPECIES_LIST_VA + len(species_data) < 0x08722000
    return bytes(data), species_data, symbols


DISPATCH_ASM = r"""
entry:
    cmp r2, #1
    beq label_handler
    cmp r2, #2
    beq callback_handler
    cmp r2, #3
    beq desc_handler

setup_handler:
    push {lr}
    ldr r3, =0x0806edb1
    bl long_call
    pop {pc}

label_handler:
    push {lr}
    ldrb r1, [r4]
    cmp r1, #7
    bne label_original
    ldr r1, =0x020370f5
    ldrb r1, [r1]
    subs r1, #1
    cmp r5, r1
    bne label_original
    ldr r1, =CUSTOM_LABEL
    b label_output
label_original:
    ldr r1, [r0]
label_output:
    mov r0, sb
    pop {pc}

desc_handler:
    push {lr}
    ldr r3, =0x080a0e91
    bl long_call
    cmp r0, #0
    bne desc_original
    ldr r3, =IS_LINK_ACTIVE
    bl long_call
    cmp r0, #0
    bne desc_original
    ldr r3, =0x0811b0d1
    bl long_call
    cmp r0, #0
    bne desc_original
    ldr r2, =CUSTOM_DESC_TABLE
    b desc_table_ready
desc_original:
    ldr r2, =0x083a7394
desc_table_ready:
    ldr r1, =0x020370f6
    pop {pc}

callback_handler:
    push {r4, lr}
    ldr r3, =0x080a0e91
    bl long_call
    cmp r0, #0
    bne original_exit_callback
    ldr r3, =IS_LINK_ACTIVE
    bl long_call
    cmp r0, #0
    bne original_exit_callback
    ldr r3, =0x0811b0d1
    bl long_call
    cmp r0, #0
    bne original_exit_callback

    ldr r3, =0x0807b005
    bl long_call
    ldr r3, =0x0806ef19
    bl long_call
    ldr r3, =0x080f7999
    bl long_call

    ldr r3, =0x080f793d
    bl long_call
    movs r1, #1
    ldr r3, =0x080f6f9d
    bl long_call
    ldr r3, =0x080f7949
    bl long_call

    ldr r0, =TASK_ITEM_MAIN_PTR
    movs r1, #0
    ldr r3, =0x0807741d
    bl long_call
    movs r0, #1
    pop {r4, pc}

original_exit_callback:
    ldr r3, =0x0806ef19
    bl long_call
    ldr r3, =0x080f7999
    bl long_call
    ldr r3, =0x0806fea1
    bl long_call
    movs r0, #1
    pop {r4, pc}

long_call:
    push {r4, lr}
    mov r4, r3
    mov r3, pc
    adds r3, #5
    mov lr, r3
    bx r4
    pop {r4, pc}
"""

TASK_ASM = r"""
task_main:
    push {r4-r7, lr}
    mov r4, r0
    mov r1, r0
    lsls r1, r1, #5
    mov r2, r0
    lsls r2, r2, #3
    adds r1, r1, r2
    mov r2, r0
    lsls r2, r2, #2
    adds r1, r1, r2
    ldr r5, =0x03005098
    adds r5, r5, r1

    ldrh r0, [r5, #8]
    cmp r0, #0
    bne task_process

    ldr r3, =0x080f6e9d
    bl long_call
    ldr r0, =WINDOW_TEMPLATE
    ldr r3, =0x08003ce5
    bl long_call
    strh r0, [r5, #2]
    ldr r3, =0x080f77b9
    bl long_call
    ldrh r0, [r5, #2]
    movs r1, #1
    ldr r3, =0x080f6f1d
    bl long_call

    ldr r0, =TPL_MODES
    mov r1, r5
    bl init_list
    ldrh r0, [r5, #2]
    movs r1, #3
    ldr r3, =0x08003f21
    bl long_call
    movs r0, #1
    strh r0, [r5, #8]
    movs r0, #3
    strh r0, [r5, #4]
    b task_return

task_process:
    ldrb r0, [r5]
    ldr r3, =0x08107079
    bl long_call
    movs r1, #1
    negs r1, r1
    cmp r0, r1
    beq task_return
    movs r1, #2
    negs r1, r1
    cmp r0, r1
    beq task_cancel
    mov r6, r0
    ldrh r0, [r5, #4]
    cmp r0, #0
    beq selected_item
    cmp r0, #1
    beq selected_quantity
    cmp r0, #3
    beq selected_mode
    b result_ack

task_cancel:
    ldrh r0, [r5, #4]
    cmp r0, #0
    beq exit_selector
    cmp r0, #3
    beq exit_selector
    b return_to_items

selected_mode:
    cmp r6, #1
    beq mode_items
    cmp r6, #2
    beq mode_species
    cmp r6, #3
    beq exit_selector
    b task_return

mode_items:
    bl destroy_list
    ldr r0, =TPL_ITEMS
    mov r1, r5
    bl init_list
    movs r0, #0
    strh r0, [r5, #4]
    b task_return

mode_species:
    bl destroy_list
    ldr r0, =TPL_SPECIES
    mov r1, r5
    bl init_list
    movs r0, #1
    strh r0, [r5, #8]
    movs r0, #0
    strh r0, [r5, #4]
    mov r0, r4
    lsls r0, r0, #5
    mov r1, r4
    lsls r1, r1, #3
    adds r0, r0, r1
    ldr r1, =0x03005090
    adds r0, r0, r1
    ldr r1, =SPECIES_TASK_MAIN_PTR
    str r1, [r0]
    b task_return

selected_item:
    cmp r6, #0
    ble task_return
    strh r6, [r5, #6]
    bl destroy_list
    ldrh r0, [r5, #6]
    ldr r3, =0x0809a991
    bl long_call
    cmp r0, #0
    bne unique_quantity
    ldrh r0, [r5, #6]
    ldr r3, =0x0809a9d9
    bl long_call
    cmp r0, #2
    beq unique_quantity
    ldr r0, =TPL_QTY99
    b quantity_start
unique_quantity:
    ldr r0, =TPL_QTY1
quantity_start:
    mov r1, r5
    bl init_list
    movs r0, #1
    strh r0, [r5, #4]
    b task_return

selected_quantity:
    cmp r6, #0
    ble task_return
    bl destroy_list
    ldrh r0, [r5, #6]
    mov r1, r6
    ldr r3, =0x0809a085
    bl long_call
    cmp r0, #0
    beq add_failed
    ldr r0, =TPL_SUCCESS
    b result_start
add_failed:
    ldr r0, =TPL_FAILURE
result_start:
    mov r1, r5
    bl init_list
    movs r0, #2
    strh r0, [r5, #4]
    b task_return

result_ack:
    b return_to_items

return_to_items:
    bl destroy_list
    ldr r0, =TPL_ITEMS
    mov r1, r5
    bl init_list
    movs r0, #0
    strh r0, [r5, #4]
    b task_return

exit_selector:
    bl destroy_list
    ldrh r0, [r5, #2]
    movs r1, #1
    ldr r3, =0x080f6f9d
    bl long_call
    ldrh r0, [r5, #2]
    ldr r3, =0x08003e3d
    bl long_call
    mov r0, r4
    ldr r3, =0x08077509
    bl long_call
    ldr r0, =0x080568a9
    ldr r3, =0x08000545
    bl long_call
    b task_return

destroy_list:
    push {lr}
    ldrb r0, [r5]
    movs r1, #0
    movs r2, #0
    ldr r3, =0x0810713d
    bl long_call
    pop {pc}

init_list:
    push {r4-r7, lr}
    sub sp, #24
    mov r4, r0
    mov r5, r1
    mov r0, sp
    mov r1, r4
    movs r2, #6
copy_template:
    ldr r3, [r1]
    str r3, [r0]
    adds r0, #4
    adds r1, #4
    subs r2, #1
    bne copy_template
    mov r0, sp
    ldrb r1, [r5, #2]
    mov r2, r0
    adds r2, #16
    strb r1, [r2]
    mov r0, sp
    movs r1, #1
    movs r2, #0
    ldr r3, =0x08106ff9
    bl long_call
    strb r0, [r5]
    add sp, #24
    pop {r4-r7, pc}

task_return:
    pop {r4-r7, pc}

long_call:
    push {r4, lr}
    mov r4, r3
    mov r3, pc
    adds r3, #5
    mov lr, r3
    bx r4
    pop {r4, pc}
"""


SPECIES_TASK_ASM = r"""
species_task_main:
    push {r4-r7, lr}
    mov r4, r0
    mov r1, r0
    lsls r1, r1, #5
    mov r2, r0
    lsls r2, r2, #3
    adds r1, r1, r2
    mov r2, r0
    lsls r2, r2, #2
    adds r1, r1, r2
    ldr r5, =0x03005098
    adds r5, r5, r1

    ldrh r0, [r5, #8]
    cmp r0, #0
    bne species_process

    ldr r3, =0x080f6e9d
    bl long_call
    ldr r0, =WINDOW_TEMPLATE
    ldr r3, =0x08003ce5
    bl long_call
    strh r0, [r5, #2]
    ldr r3, =0x080f77b9
    bl long_call
    ldrh r0, [r5, #2]
    movs r1, #1
    ldr r3, =0x080f6f1d
    bl long_call

    ldr r0, =TPL_SPECIES
    mov r1, r5
    bl init_species_list
    ldrh r0, [r5, #2]
    movs r1, #3
    ldr r3, =0x08003f21
    bl long_call
    movs r0, #1
    strh r0, [r5, #8]
    movs r0, #0
    strh r0, [r5, #4]
    b species_return

species_process:
    ldrb r0, [r5]
    ldr r3, =0x08107079
    bl long_call
    movs r1, #1
    negs r1, r1
    cmp r0, r1
    beq species_return
    movs r1, #2
    negs r1, r1
    cmp r0, r1
    beq species_cancel
    mov r6, r0
    ldrh r0, [r5, #4]
    cmp r0, #0
    beq species_selected
    b species_result_ack

species_cancel:
    ldrh r0, [r5, #4]
    cmp r0, #0
    beq species_exit
    b species_return_to_list

species_selected:
    cmp r6, #0
    ble species_return
    strh r6, [r5, #6]
    bl destroy_species_list

    sub sp, #100
    sub sp, #16
    mov r0, sp
    adds r0, #16
    ldrh r1, [r5, #6]
    movs r2, #5
    movs r3, #32
    movs r7, #0
    str r7, [sp, #0]
    str r7, [sp, #4]
    str r7, [sp, #8]
    str r7, [sp, #12]
    mov r7, r4
    ldr r4, =CREATE_MON
    mov r6, r3
    mov r3, pc
    adds r3, #7
    mov lr, r3
    movs r3, #32
    bx r4
    mov r4, r7
    add sp, #16
    mov r0, sp
    ldr r3, =GIVE_MON_TO_PLAYER
    bl long_call
    add sp, #100
    cmp r0, #0
    beq species_added
    cmp r0, #1
    beq species_sent_pc
    ldr r0, =TPL_SPECIES_FULL
    b species_show_result
species_added:
    ldr r0, =TPL_SPECIES_ADDED
    b species_show_result
species_sent_pc:
    ldr r0, =TPL_SPECIES_PC
species_show_result:
    mov r1, r5
    bl init_species_list
    movs r0, #1
    strh r0, [r5, #4]
    b species_return

species_result_ack:
    b species_return_to_list

species_return_to_list:
    bl destroy_species_list
    ldr r0, =TPL_SPECIES
    mov r1, r5
    bl init_species_list
    movs r0, #0
    strh r0, [r5, #4]
    b species_return

species_exit:
    bl destroy_species_list
    ldrh r0, [r5, #2]
    movs r1, #1
    ldr r3, =0x080f6f9d
    bl long_call
    ldrh r0, [r5, #2]
    ldr r3, =0x08003e3d
    bl long_call
    mov r0, r4
    ldr r3, =0x08077509
    bl long_call
    ldr r0, =0x080568a9
    ldr r3, =0x08000545
    bl long_call
    b species_return

destroy_species_list:
    push {lr}
    ldrb r0, [r5]
    movs r1, #0
    movs r2, #0
    ldr r3, =0x0810713d
    bl long_call
    pop {pc}

init_species_list:
    push {r4-r7, lr}
    sub sp, #24
    mov r4, r0
    mov r5, r1
    mov r0, sp
    mov r1, r4
    movs r2, #6
copy_species_template:
    ldr r3, [r1]
    str r3, [r0]
    adds r0, #4
    adds r1, #4
    subs r2, #1
    bne copy_species_template
    mov r0, sp
    ldrb r1, [r5, #2]
    mov r2, r0
    adds r2, #16
    strb r1, [r2]
    mov r0, sp
    movs r1, #1
    movs r2, #0
    ldr r3, =0x08106ff9
    bl long_call
    strb r0, [r5]
    add sp, #24
    pop {r4-r7, pc}

species_return:
    pop {r4-r7, pc}

long_call:
    push {r4, lr}
    mov r4, r3
    mov r3, pc
    adds r3, #5
    mov lr, r3
    bx r4
    pop {r4, pc}
"""


def build(base: Path, out: Path) -> None:
    if not base.is_file():
        raise SystemExit(f"base ROM not found: {base}")
    rom = bytearray(base.read_bytes())
    if len(rom) != 16 * 1024 * 1024:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")

    for va, expected, label in (
        (SETUP_HOOK_VA, ORIG_SETUP, "normal start-menu setup call"),
        (LABEL_HOOK_VA, ORIG_LABEL, "start-menu action label load"),
        (DESC_TABLE_HOOK_VA, ORIG_DESC_TABLE_LOADS, "start-menu description table loads"),
        (SAFARI_CALLBACK_VA, ORIG_CALLBACK, "Safari retire callback"),
    ):
        at = off(va)
        if rom[at:at + len(expected)] != expected:
            raise SystemExit(f"base mismatch at {va:#010x} ({label}); refusing patch")

    desc_bytes = rom[off(DESC_TABLE_ORIG_VA):off(DESC_TABLE_ORIG_VA) + 36]
    if len(desc_bytes) != 36:
        raise SystemExit("native description pointer table is truncated")
    desc_pointers = struct.unpack("<9I", desc_bytes)
    if any(not ROM_BASE <= ptr < ROM_BASE + len(rom) for ptr in desc_pointers):
        raise SystemExit("native description pointer table contains out-of-ROM entries")
    data, species_data, symbols = make_data(desc_pointers, rom)
    eternatus_assets, asset_symbols = make_eternatus_assets()
    if len(species_data) != (387 + 1) * 8:
        raise SystemExit(f"unexpected species selector record count: {len(species_data) // 8 - 1}")

    exit_label = struct.unpack_from("<I", rom, off(ACTION_TABLE_EXIT_LABEL_VA))[0]
    exit_callback = struct.unpack_from("<I", rom, off(ACTION_TABLE_EXIT_CALLBACK_VA))[0]
    if (exit_label, exit_callback) != (ORIGINAL_EXIT_LABEL, ORIGINAL_EXIT_CALLBACK):
        raise SystemExit(
            "native Exit action-table entry differs from expected bytes; refusing patch"
        )
    fade_exit_pointer = struct.unpack_from("<I", rom, off(FADE_EXIT_CALLBACK_PTR_VA))[0]
    if fade_exit_pointer != ORIGINAL_EXIT_CALLBACK:
        raise SystemExit("start-menu fade callback literal mismatch; refusing patch")

    dispatch_src = DISPATCH_ASM.replace("CUSTOM_LABEL", f"0x{symbols['label_mod_menu']:08x}")
    dispatch_src = dispatch_src.replace("CUSTOM_DESC_TABLE", f"0x{symbols['custom_desc_table']:08x}")
    dispatch_src = dispatch_src.replace("TASK_ITEM_MAIN_PTR", f"0x{TASK_VA+1:08x}")
    dispatch_src = dispatch_src.replace("IS_LINK_ACTIVE", f"0x{IS_LINK_ACTIVE:08x}")
    dispatch = thumb(dispatch_src, PAYLOAD_VA)

    task_src = TASK_ASM
    for token, key in (
        ("WINDOW_TEMPLATE", "window"),
        ("TPL_MODES", "template_modes"),
        ("TPL_SPECIES", "template_species"),
        ("TPL_ITEMS", "template_items"),
        ("TPL_QTY99", "template_qty99"),
        ("TPL_QTY1", "template_qty1"),
        ("TPL_SUCCESS", "template_success"),
        ("TPL_FAILURE", "template_failure"),
    ):
        task_src = task_src.replace(token, f"0x{symbols[key]:08x}")
    task_src = task_src.replace("SPECIES_TASK_MAIN_PTR", f"0x{SPECIES_TASK_VA+1:08x}")
    task = thumb(task_src, TASK_VA)

    species_task_src = SPECIES_TASK_ASM
    for token, key in (
        ("WINDOW_TEMPLATE", "window"),
        ("TPL_SPECIES_ADDED", "template_species_added"),
        ("TPL_SPECIES_PC", "template_species_pc"),
        ("TPL_SPECIES_FULL", "template_species_full"),
        ("TPL_SPECIES", "template_species"),
        ("CREATE_MON", "CREATE_MON"),
        ("GIVE_MON_TO_PLAYER", "GIVE_MON_TO_PLAYER"),
    ):
        value = f"0x{symbols[key]:08x}" if key in symbols else f"0x{globals()[key]:08x}"
        species_task_src = species_task_src.replace(token, value)
    species_task = thumb(species_task_src, SPECIES_TASK_VA)

    if len(dispatch) > TASK_VA - PAYLOAD_VA:
        raise SystemExit(f"dispatch collides with item task code ({len(dispatch)} bytes)")
    if TASK_VA + len(task) > DATA_VA:
        raise SystemExit(f"item task code collides with data ({len(task)} bytes)")
    if DATA_VA + len(data) > SPECIES_TASK_VA:
        raise SystemExit(f"data collides with species task ({len(data)} bytes)")
    if SPECIES_TASK_VA + len(species_task) > SPECIES_LIST_VA:
        raise SystemExit(f"species task collides with species list ({len(species_task)} bytes)")
    if SPECIES_LIST_VA + len(species_data) > ETERNATUS_ASSETS_VA:
        raise SystemExit("species list collides with Eternatus assets")
    if ETERNATUS_ASSETS_VA + len(eternatus_assets) > 0x08740000:
        raise SystemExit(f"Eternatus assets exceed reserved free space ({len(eternatus_assets)} bytes)")

    # Verify every payload destination is erased in this exact base ROM.
    for va, payload_len, label in (
        (BRIDGE_VA, 0x30, "bridge"),
        (PAYLOAD_VA, len(dispatch), "dispatch code"),
        (TASK_VA, len(task), "item task code"),
        (DATA_VA, len(data), "tables and UI data"),
        (SPECIES_TASK_VA, len(species_task), "species task code"),
        (SPECIES_LIST_VA, len(species_data), "species list"),
        (ETERNATUS_ASSETS_VA, len(eternatus_assets), "Eternatus assets"),
    ):
        at = off(va)
        if rom[at:at + payload_len] != b"\xff" * payload_len:
            raise SystemExit(f"{label} destination {va:#010x} is not all 0xFF")

    # Near Thumb bridge: modes 0=setup, 1=label, 2=callback, 3=description.
    bridge_src = f"""
        push {{lr}}\n        movs r2, #0\n        bl 0x{PAYLOAD_VA:08x}\n        pop {{pc}}\n        nop\n        push {{lr}}\n        movs r2, #1\n        bl 0x{PAYLOAD_VA:08x}\n        pop {{pc}}\n        nop\n        push {{lr}}\n        movs r2, #2\n        bl 0x{PAYLOAD_VA:08x}\n        pop {{pc}}\n        nop\n        push {{lr}}\n        movs r2, #3\n        bl 0x{PAYLOAD_VA:08x}\n        pop {{pc}}\n        nop\n    """
    bridge = thumb(bridge_src, BRIDGE_VA)
    if len(bridge) != 48:
        raise SystemExit(f"unexpected bridge size: {len(bridge)}")

    # Apply patches into a new ROM image only after all checks/assembly succeeded.
    rom[off(BRIDGE_VA):off(BRIDGE_VA) + len(bridge)] = bridge
    rom[off(PAYLOAD_VA):off(PAYLOAD_VA) + len(dispatch)] = dispatch
    rom[off(TASK_VA):off(TASK_VA) + len(task)] = task
    rom[off(DATA_VA):off(DATA_VA) + len(data)] = data
    rom[off(SPECIES_TASK_VA):off(SPECIES_TASK_VA) + len(species_task)] = species_task
    rom[off(SPECIES_LIST_VA):off(SPECIES_LIST_VA) + len(species_data)] = species_data
    rom[off(ETERNATUS_ASSETS_VA):off(ETERNATUS_ASSETS_VA) + len(eternatus_assets)] = eternatus_assets

    # Turn internal placeholder 252 into standard-form Eternatus. The two
    # trailing bytes are the original ROM's per-record alignment padding.
    species_info = (
        bytes((140, 85, 95, 130, 145, 95, 3, 16, 3, 255))
        + struct.pack("<HHH", 3 << 8, 0, 0)
        + bytes((255, 120, 35, 5, 15, 15, 46, 0, 0, 6, 0, 0))
    )
    if len(species_info) != 28:
        raise SystemExit(f"internal error: Eternatus species record is {len(species_info)} bytes")
    stats_va = BASE_STATS_VA + ETERNATUS_SPECIES_ID * 28
    rom[off(stats_va):off(stats_va) + 28] = species_info

    name = gba_text("ETERNATUS")
    name_va = SPECIES_NAMES_VA + ETERNATUS_SPECIES_ID * 11
    rom[off(name_va):off(name_va) + 11] = name.ljust(11, b"\x00")

    # Battle graphics and palette descriptors use standard BPRE table layouts.
    rom[off(FRONT_PIC_TABLE_VA + ETERNATUS_SPECIES_ID * 8):off(FRONT_PIC_TABLE_VA + (ETERNATUS_SPECIES_ID + 1) * 8)] = struct.pack("<IHH", asset_symbols["front"], 2048, ETERNATUS_SPECIES_ID)
    rom[off(BACK_PIC_TABLE_VA + ETERNATUS_SPECIES_ID * 8):off(BACK_PIC_TABLE_VA + (ETERNATUS_SPECIES_ID + 1) * 8)] = struct.pack("<IHH", asset_symbols["back"], 2048, ETERNATUS_SPECIES_ID)
    rom[off(MON_PALETTE_TABLE_VA + ETERNATUS_SPECIES_ID * 8):off(MON_PALETTE_TABLE_VA + (ETERNATUS_SPECIES_ID + 1) * 8)] = struct.pack("<IHH", asset_symbols["normal_palette"], ETERNATUS_SPECIES_ID, 0)
    rom[off(SHINY_PALETTE_TABLE_VA + ETERNATUS_SPECIES_ID * 8):off(SHINY_PALETTE_TABLE_VA + (ETERNATUS_SPECIES_ID + 1) * 8)] = struct.pack("<IHH", asset_symbols["shiny_palette"], 500 + ETERNATUS_SPECIES_ID, 0)
    rom[off(FRONT_PIC_COORDS_VA + ETERNATUS_SPECIES_ID * 2):off(FRONT_PIC_COORDS_VA + (ETERNATUS_SPECIES_ID + 1) * 2)] = bytes((0x88, 0))
    rom[off(BACK_PIC_COORDS_VA + ETERNATUS_SPECIES_ID * 2):off(BACK_PIC_COORDS_VA + (ETERNATUS_SPECIES_ID + 1) * 2)] = bytes((0x88, 0))
    rom[off(MON_ICON_TABLE_VA + ETERNATUS_SPECIES_ID * 4):off(MON_ICON_TABLE_VA + (ETERNATUS_SPECIES_ID + 1) * 4)] = struct.pack("<I", asset_symbols["icon"])
    rom[off(MON_ICON_PALETTE_INDEX_VA + ETERNATUS_SPECIES_ID)] = 3
    # Palette slot 3 is unused by the 386 original species; give Eternatus its
    # own icon palette instead of changing colors for any existing Pokémon.
    palette3 = MON_ICON_PALETTE_TABLE_VA + 3 * 8
    rom[off(palette3):off(palette3) + 8] = struct.pack("<IHH", asset_symbols["icon_palette"], 0xDAC3, 0)
    rom[off(LEVEL_UP_LEARNSETS_VA + ETERNATUS_SPECIES_ID * 4):off(LEVEL_UP_LEARNSETS_VA + (ETERNATUS_SPECIES_ID + 1) * 4)] = struct.pack("<I", asset_symbols["learnset"])

    rom[off(ACTION_TABLE_EXIT_LABEL_VA):off(ACTION_TABLE_EXIT_LABEL_VA) + 4] = struct.pack("<I", symbols["label_mod_menu"])
    rom[off(ACTION_TABLE_EXIT_CALLBACK_VA):off(ACTION_TABLE_EXIT_CALLBACK_VA) + 4] = struct.pack("<I", CUSTOM_CALLBACK_VA)
    rom[off(FADE_EXIT_CALLBACK_PTR_VA):off(FADE_EXIT_CALLBACK_PTR_VA) + 4] = struct.pack("<I", CUSTOM_CALLBACK_VA)

    if len(rom) != 16 * 1024 * 1024:
        raise SystemExit(f"internal error: patched ROM length changed to {len(rom)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(rom)
    digest = hashlib.sha256(rom).hexdigest()
    print(f"[OK] {out} ({len(rom)} bytes), sha256={digest}")
    print(f"dispatch={len(dispatch)} B task={len(task)} B data={len(data)} B bridge={len(bridge)} B")
    print(f"item list: {len(item_records())} named IDs; tables at {DATA_VA:#010x}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build(args.base, args.out)


if __name__ == "__main__":
    main()
