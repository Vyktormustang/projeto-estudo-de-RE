#!/usr/bin/env python3
"""Aplica o motor_v8 sobre a ROM motor_v7 identificada por SHA-256.

Escopo estrito e auditável sobre o motor_v7:
  1. Instala estado efêmero de batalha do motor_v8 em 0x0203FC60..0x0203FC9F
     (sem tocar estruturas persistentes ou saves) e encadeia início de batalha
     (0x08051D74), início de turno (0x0805439C), ordem de turno (0x080538E0) e
     fim de turno (0x08204CBC), além de relocar gBattleScriptingCommandsTable em
     0x090C2800 e gBattleStringsTable em 0x090C1800 (+34 mensagens PT-BR).
  2. Habilita as 10 TMs finais de Scarlet/Violet (219 -> 229 de 229):
     TM052 Snowscape (773), TM091 Toxic Spikes (390), TM113 Tailwind (366),
     TM116 Stealth Rock (445), TM136 Electric Terrain (599), TM137 Grassy
     Terrain (576), TM138 Psychic Terrain (633), TM139 Misty Terrain (577),
     TM161 Trick Room (433) e TM178 Gravity (356).
  3. Ativa os golpes de subida de nível das mesmas famílias de clima, terreno,
     salas, gravidade, barreiras e hazards — Magnet Rise (393), Defog (432),
     Wonder Room (471), Sticky Web (560), Shore Up (614), Aurora Veil (649),
     Court Change (681), Stone Axe (723), Ceaseless Edge (738), Chilly Reception
     (771) e Tidy Up (772) — além de Psychic Fangs (652), Mortal Spin (758) e
     das sinergias de Weather Ball (311), Blizzard (59), Rapid Spin (229),
     Brick Break (280), Floral Healing (621), Expanding Force (701), Rising
     Voltage (705), Terrain Pulse (706), Psyblade (783), Grassy Glide (805) e
     Misty Explosion (810), recompilando learnsets com +245 entradas antes
     omitidas (14.382 -> 14.627 linhas, preservando 100% das anteriores).

Continua sendo um motor parcial quanto a mecânicas fora deste escopo (itens e
habilidades modernos ausentes na base Gen 3 e 402 entradas de nível de outros
57 golpes documentados). Não altera saves pessoais; grava sempre arquivo novo.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import atualizacoes_gen9 as previous
from scripts import complemento_gen9 as complement
from scripts import golpes_gen9 as level
from scripts import motor_v6 as v6
from scripts import motor_v7 as v7
from scripts.treino_ev import write_new_file

BASE_SHA256 = v7.OUTPUT_SHA256
OUTPUT_SHA256 = "32fd47c87b581952f54f05656f590c5f7da55d5cc3d186d81951508899ec54f0"

INPUTS = {
    ROOT / "patches/motor_v8/payload.bin": "fc2d75763a5611f0fb5cf4bcd7e48966e088ecce6bb18b25b05859e2ef098131",
    ROOT / "data/tms_motor_v8.csv": "20eba409d81c459393d6156f5053a3f5bf71e4ac99c7c4574287a39f2b95523c",
    ROOT / "data/compatibilidade_tms_motor_v8.bin": "358a1b9fa456a23a22f8c3249d5381f75585139a5385690c58a43c1de8eea3ac",
    ROOT / "data/compatibilidade_tms_motor_v7.bin": "618563d9dbc6ead8ecce2ae0f38978ec62ff0da5ebae2e294efaffbb7e1420d7",
    ROOT / "data/learnsets_motor_v8.csv": "19abc5661267157524b9dcdc9ad769cdf12a20f9f44a3be63f134ae2ec9120f7",
    ROOT / "data/learnsets_motor_v7.csv": "ed8e02a3bb3665a68ed3d53a59c2532d273bf0cbda630ef77aee56e6cbc6c2fe",
}

ROM = 0x08000000
MOVE_COUNT = v7.MOVE_COUNT

# Hooks de ciclo de vida / ordem / fim de turno
BATTLE_INIT_LIT = v7.BATTLE_INIT_LIT
TURN_START_LIT = v7.TURN_START_LIT
SET_TURN_ORDER_LIT = 0x0538E0
ENDTURN_CONT_LIT = 0x053208

# Tabela de strings de batalha relocada (sid 12..385 -> 12..419)
ORIG_BATTLE_STRINGS_TABLE = 0x207F54
ORIG_BATTLE_STRINGS_COUNT = 374
BATTLE_STRING_CAP_SITE = 0x055C5A
BATTLE_STRINGS_TABLE_REFS = (
    0x055E00,
    0x056ADC,
    0x0A0B38,
    0x0A0EBC,
    0x0A10EC,
    0x0A14A0,
    0x0A1868,
    0x0A1948,
)

# Regioes exclusivas do motor_v8 em espaco livre 0xFF (apos 0x10C0D30 do motor_v7)
SCRIPTS_V8 = 0x10C1000
SCRIPTS_V8_END = 0x10C1800
STRINGS_TABLE_V8 = 0x10C1800
STRINGS_TABLE_V8_END = 0x10C2000
STRINGS_TEXT_V8 = 0x10C2000
STRINGS_TEXT_V8_END = 0x10C2800
CMD_TABLE_V8 = 0x10C2800
CMD_TABLE_V8_END = 0x10C2C00
PAYLOAD_V8 = 0x10C3000
PAYLOAD_V8_END = 0x10C6000

# Sub-scripts em enderecos fixos dentro de SCRIPTS_V8 (sincronizados com motor_v8.c)
SUB_GRAVITY_CANCEL = 0x10C1000
SUB_PTERRAIN_CANCEL = 0x10C1010
SUB_TERRAIN_BLOCK = 0x10C1020
SUB_ENDTURN_MSGS = 0x10C1030     # 8 slots de 8 B (0x1030..0x106F)
SUB_ENDTURN_GRASSY = 0x10C1070
SUB_HAZARD_SPIKES_G = 0x10C1090
SUB_HAZARD_SROCK = 0x10C10D0
SUB_TSPIKES_ABSORB = 0x10C1110
SUB_STICKY_WEB_DROP = 0x10C1120
SUB_SUBSTITUTE_FADE = 0x10C1160
SUB_RAPIDSPIN_CLEAR = 0x10C1170
SUB_STATUS_TAILS = 0x10C1180     # 17 slots de 12 B (0x1180..0x124B)
DYNAMIC_SCRIPTS_START = 0x10C1250

# Vetores Thumb em patches/motor_v8/entry.s (base 0x090C3001 + 8*i)
PAYLOAD_V8_THUMB = ROM + PAYLOAD_V8 + 1
ENTRY_BATTLE_INIT_V8 = PAYLOAD_V8_THUMB + 0 * 8
ENTRY_TURN_START_V8 = PAYLOAD_V8_THUMB + 1 * 8
ENTRY_SET_TURN_ORDER_V8 = PAYLOAD_V8_THUMB + 2 * 8
ENTRY_ENDTURN_V8 = PAYLOAD_V8_THUMB + 3 * 8
ENTRY_ATTACKCANCELER_V8 = PAYLOAD_V8_THUMB + 4 * 8
ENTRY_ACCURACYCHECK_V8 = PAYLOAD_V8_THUMB + 5 * 8
ENTRY_DAMAGE_V8 = PAYLOAD_V8_THUMB + 6 * 8
ENTRY_TYPECALC_V8 = PAYLOAD_V8_THUMB + 7 * 8
ENTRY_SETEFFECT_CHANCE_V8 = PAYLOAD_V8_THUMB + 8 * 8
ENTRY_SETEFFECT_PRIMARY_V8 = PAYLOAD_V8_THUMB + 9 * 8
ENTRY_SETEFFECT_SECONDARY_V8 = PAYLOAD_V8_THUMB + 10 * 8
ENTRY_SWITCHINEFFECTS_V8 = PAYLOAD_V8_THUMB + 11 * 8
ENTRY_JUMPIFCANTSLEEP_V8 = PAYLOAD_V8_THUMB + 12 * 8
ENTRY_RAPIDSPINFREE_V8 = PAYLOAD_V8_THUMB + 13 * 8
ENTRY_WEATHERBALL_V8 = PAYLOAD_V8_THUMB + 14 * 8
ENTRY_BRICKBREAK_V8 = PAYLOAD_V8_THUMB + 15 * 8
ENTRY_TARGET_HEAL_PREP_V8 = PAYLOAD_V8_THUMB + 16 * 8
ENTRY_FIELD_STATUS_PREP_V8 = PAYLOAD_V8_THUMB + 17 * 8
ENTRY_FIELD_STATUS_APPLY_V8 = PAYLOAD_V8_THUMB + 18 * 8
ENTRY_DEFOG_EVA_CHECK_V8 = PAYLOAD_V8_THUMB + 19 * 8
ENTRY_DEFOG_CLEAR_V8 = PAYLOAD_V8_THUMB + 20 * 8
ENTRY_SHORE_UP_PREP_V8 = PAYLOAD_V8_THUMB + 21 * 8
ENTRY_TIDY_UP_CHECK_V8 = PAYLOAD_V8_THUMB + 22 * 8
ENTRY_TIDY_UP_CLEAR_V8 = PAYLOAD_V8_THUMB + 23 * 8
ENTRY_CHILLY_SNOW_V8 = PAYLOAD_V8_THUMB + 24 * 8
ENTRY_HAZARD_HIT_APPLY_V8 = PAYLOAD_V8_THUMB + 25 * 8
ENTRY_STICKY_WEB_RESTORE_V8 = PAYLOAD_V8_THUMB + 26 * 8
ENTRY_MORTAL_SPIN_CHECK_V8 = PAYLOAD_V8_THUMB + 27 * 8

BS_MOVE_END = 0x081853F6
BS_BUT_IT_FAILED = 0x0818689A
BS_SPIKES_FAINT_TAIL = 0x081877BE
STAT_BUFF_ADDR = 0x02021822
MOVE_EFFECT_BYTE_ADDR = 0x020216C3
HIT_MARKER_ADDR = 0x0202160C

EFF_TARGET_HEAL = 234       # upgrade sobre motor_v7: Floral Healing cura 2/3 em Grassy Terrain
EFF_V8_FIELD_STATUS = 236   # Snowscape, Tailwind, Aurora Veil, 4 Terrains, Rooms, Gravity, Hazards, Magnet Rise, Court Change
EFF_DEFOG = 237             # Defog (432)
EFF_SHORE_UP = 238          # Shore Up (614)
EFF_TIDY_UP = 239           # Tidy Up (772)
EFF_CHILLY_RECEPTION = 240  # Chilly Reception (771)
EFF_HAZARD_HIT = 241        # Stone Axe (723), Ceaseless Edge (738)
EFF_MORTAL_SPIN = 242       # Mortal Spin (758)

STR_SNOW_STARTED = 0x0182
STR_SNOW_STOPPED = 0x0183
STR_TAILWIND_BLEW = 0x0184
STR_TAILWIND_ENDED = 0x0185
STR_AURORA_VEIL_SET = 0x0186
STR_AURORA_VEIL_END = 0x0187
STR_ELECTRIC_TERRAIN = 0x0188
STR_GRASSY_TERRAIN = 0x0189
STR_PSYCHIC_TERRAIN = 0x018A
STR_MISTY_TERRAIN = 0x018B
STR_TERRAIN_FADED = 0x018C
STR_TRICK_ROOM_SET = 0x018D
STR_TRICK_ROOM_ENDED = 0x018E
STR_WONDER_ROOM_SET = 0x018F
STR_WONDER_ROOM_ENDED = 0x0190
STR_GRAVITY_SET = 0x0191
STR_GRAVITY_ENDED = 0x0192
STR_GRAVITY_BLOCK = 0x0193
STR_PSYCHIC_BLOCK = 0x0194
STR_TERRAIN_PROTECT = 0x0195
STR_STEALTH_ROCK_SET = 0x0196
STR_STEALTH_ROCK_HURT = 0x0197
STR_TOXIC_SPIKES_SET = 0x0198
STR_TSPIKES_ABSORB = 0x0199
STR_STICKY_WEB_SET = 0x019A
STR_STICKY_WEB_CAUGHT = 0x019B
STR_MAGNET_RISE_SET = 0x019C
STR_MAGNET_RISE_END = 0x019D
STR_COURT_CHANGE = 0x019E
STR_DEFOG_CLEARED = 0x019F
STR_TIDY_UP_CLEARED = 0x01A0
STR_CHILLY_JOKE = 0x01A1
STR_GRASSY_HEAL = 0x01A2
STR_HAZARDS_CLEARED = 0x01A3

NEW_BATTLE_STRINGS: tuple[tuple[int, str], ...] = (
    (STR_SNOW_STARTED, "Começou a nevar!"),
    (STR_SNOW_STOPPED, "A neve parou."),
    (STR_TAILWIND_BLEW, "O vento soprou a favor\ndo time de {ATK}!"),
    (STR_TAILWIND_ENDED, "O vento a favor cessou!"),
    (STR_AURORA_VEIL_SET, "O Véu de Aurora fortaleceu\no time de {ATK}!"),
    (STR_AURORA_VEIL_END, "O Véu de Aurora se dissipou!"),
    (STR_ELECTRIC_TERRAIN, "Uma corrente elétrica correu\npelo campo de batalha!"),
    (STR_GRASSY_TERRAIN, "Grama cresceu cobrindo\no campo de batalha!"),
    (STR_PSYCHIC_TERRAIN, "O campo de batalha ficou\nestranho!"),
    (STR_MISTY_TERRAIN, "Névoa rodopiou pelo\ncampo de batalha!"),
    (STR_TERRAIN_FADED, "O terreno voltou ao normal!"),
    (STR_TRICK_ROOM_SET, "{ATK} distorceu\nas dimensões!"),
    (STR_TRICK_ROOM_ENDED, "As dimensões distorcidas\nvoltaram ao normal!"),
    (STR_WONDER_ROOM_SET, "Criou uma área bizarra que\ntrocou Defesa e Def. Esp.!"),
    (STR_WONDER_ROOM_ENDED, "O efeito de WONDER ROOM\npassou!"),
    (STR_GRAVITY_SET, "A gravidade se intensificou!"),
    (STR_GRAVITY_ENDED, "A gravidade voltou ao normal!"),
    (STR_GRAVITY_BLOCK, "{ATK} não pode usar o\ngolpe sob a gravidade!"),
    (STR_PSYCHIC_BLOCK, "{TGT} está protegido\npelo Terreno Psíquico!"),
    (STR_TERRAIN_PROTECT, "O terreno protege\n{TGT}!"),
    (STR_STEALTH_ROCK_SET, "Pedras pontiagudas flutuam\nno ar inimigo!"),
    (STR_STEALTH_ROCK_HURT, "Pedras pontiagudas feriram\n{SCR}!"),
    (STR_TOXIC_SPIKES_SET, "Espinhos venenosos cobriram\no chão inimigo!"),
    (STR_TSPIKES_ABSORB, "Os espinhos venenosos\ndesapareceram do chão!"),
    (STR_STICKY_WEB_SET, "Uma teia pegajosa cobriu\no chão inimigo!"),
    (STR_STICKY_WEB_CAUGHT, "{SCR} caiu na\nteia pegajosa!"),
    (STR_MAGNET_RISE_SET, "{ATK} levitou com\neletromagnetismo!"),
    (STR_MAGNET_RISE_END, "O eletromagnetismo de\n{SCR} passou!"),
    (STR_COURT_CHANGE, "{ATK} trocou os\nefeitos de campo!"),
    (STR_DEFOG_CLEARED, "{ATK} dissipou os\nobstáculos do campo!"),
    (STR_TIDY_UP_CLEARED, "A arrumação foi concluída!"),
    (STR_CHILLY_JOKE, "{ATK} prepara uma\npiada de arrepiar!"),
    (STR_GRASSY_HEAL, "O HP de {SCR}\nfoi restaurado!"),
    (STR_HAZARDS_CLEARED, "As armadilhas ao redor de\n{ATK} sumiram!"),
)

ENDTURN_MSG_ORDER: tuple[int, ...] = (
    STR_SNOW_STOPPED,
    STR_TAILWIND_ENDED,
    STR_AURORA_VEIL_END,
    STR_TERRAIN_FADED,
    STR_GRAVITY_ENDED,
    STR_TRICK_ROOM_ENDED,
    STR_WONDER_ROOM_ENDED,
    STR_MAGNET_RISE_END,
)

STATUS_TAIL_ORDER: tuple[int, ...] = (
    STR_SNOW_STARTED,
    STR_TAILWIND_BLEW,
    STR_AURORA_VEIL_SET,
    STR_ELECTRIC_TERRAIN,
    STR_GRASSY_TERRAIN,
    STR_PSYCHIC_TERRAIN,
    STR_MISTY_TERRAIN,
    STR_TRICK_ROOM_SET,
    STR_TRICK_ROOM_ENDED,
    STR_WONDER_ROOM_SET,
    STR_WONDER_ROOM_ENDED,
    STR_GRAVITY_SET,
    STR_STEALTH_ROCK_SET,
    STR_TOXIC_SPIKES_SET,
    STR_STICKY_WEB_SET,
    STR_MAGNET_RISE_SET,
    STR_COURT_CHANGE,
)

UPDATED_MOVE_DESCRIPTIONS: dict[int, str] = {
    771: "Piada ruim invoca\nneve. O usuário\ntroca de lugar.",
    773: "Invoca neve por 5\nturnos. Sobe a Def.\nde tipos Gelo.",
    805: "Ataque deslizante.\nTem prioridade em\nTerreno de Grama.",
}

NEWLY_AVAILABLE_TMS_V8: dict[int, int] = {
    52: 773,   # Snowscape
    91: 390,   # Toxic Spikes
    113: 366,  # Tailwind
    116: 445,  # Stealth Rock
    136: 599,  # Electric Terrain
    137: 576,  # Grassy Terrain
    138: 633,  # Psychic Terrain
    139: 577,  # Misty Terrain
    161: 433,  # Trick Room
    178: 356,  # Gravity
}

MOVE_UPDATES_V8: dict[int, dict[str, int]] = {
    # 10 TMs finais de Scarlet/Violet
    356: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x00},  # Gravity (TM178)
    366: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x08},  # Tailwind (TM113)
    390: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x40, "flags": 0x04},  # Toxic Spikes (TM091)
    433: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x00},  # Trick Room (TM161, prio -7 preservada)
    445: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x40, "flags": 0x04},  # Stealth Rock (TM116)
    576: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x00},  # Grassy Terrain (TM137)
    577: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x00},  # Misty Terrain (TM139)
    599: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x00},  # Electric Terrain (TM136)
    633: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x00},  # Psychic Terrain (TM138)
    773: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x00},  # Snowscape (TM052)
    # Golpes de subida de nivel das mesmas familias + Psychic Fangs + Mortal Spin
    393: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x08},  # Magnet Rise
    432: {"eff": EFF_DEFOG, "tgt": 0x00, "flags": 0x16},            # Defog
    471: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x00},  # Wonder Room
    560: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x40, "flags": 0x04},  # Sticky Web
    614: {"eff": EFF_SHORE_UP, "tgt": 0x10, "flags": 0x08},         # Shore Up
    649: {"eff": EFF_V8_FIELD_STATUS, "tgt": 0x10, "flags": 0x08},  # Aurora Veil
    652: {"eff": 186},                                              # Psychic Fangs -> EFFECT_BRICK_BREAK
    681: {"eff": EFF_V8_FIELD_STATUS, "acc": 0, "tgt": 0x10, "flags": 0x00},  # Court Change
    723: {"eff": EFF_HAZARD_HIT},                                   # Stone Axe
    738: {"eff": EFF_HAZARD_HIT},                                   # Ceaseless Edge
    758: {"eff": EFF_MORTAL_SPIN, "chance": 100},                   # Mortal Spin
    771: {"eff": EFF_CHILLY_RECEPTION, "tgt": 0x10, "flags": 0x00}, # Chilly Reception
    772: {"eff": EFF_TIDY_UP, "tgt": 0x10, "flags": 0x08},          # Tidy Up
}

PTBR_CHAR_MAP: dict[str, int] = {
    " ": 0x00,
    "À": 0x01,
    "Á": 0x02,
    "Ç": 0x04,
    "É": 0x06,
    "à": 0x16,
    "á": 0x17,
    "ç": 0x19,
    "é": 0x1B,
    "ê": 0x1C,
    "ã": 0x1E,
    "õ": 0x22,
    "ó": 0x23,
    "ô": 0x24,
    "ú": 0x27,
    ";": 0x36,
    "â": 0x68,
    "í": 0x6F,
    "!": 0xAB,
    "?": 0xAC,
    ".": 0xAD,
    "-": 0xAE,
    "'": 0xB4,
    ",": 0xB8,
    "/": 0xBA,
    ":": 0xF0,
    "\n": 0xFE,
}
for _i in range(10):
    PTBR_CHAR_MAP[str(_i)] = 0xA1 + _i
for _i in range(26):
    PTBR_CHAR_MAP[chr(ord("A") + _i)] = 0xBB + _i
    PTBR_CHAR_MAP[chr(ord("a") + _i)] = 0xD5 + _i

PLACEHOLDERS: dict[str, bytes] = {
    "{ATK}": bytes([0xFD, 0x0F]),
    "{TGT}": bytes([0xFD, 0x10]),
    "{SCR}": bytes([0xFD, 0x13]),
}


class PatchError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(val: int) -> bytes:
    return struct.pack("<H", val)


def u32(val: int) -> bytes:
    return struct.pack("<I", val)


def callasm(addr_thumb: int) -> bytes:
    return bytes([0xF8]) + u32(addr_thumb)


def encode_ptbr(s: str) -> bytes:
    out = bytearray()
    i = 0
    while i < len(s):
        matched = False
        for token, raw in PLACEHOLDERS.items():
            if s.startswith(token, i):
                out += raw
                i += len(token)
                matched = True
                break
        if matched:
            continue
        ch = s[i]
        if ch not in PTBR_CHAR_MAP:
            raise PatchError(f"Caractere sem mapeamento PT-BR GBA: {ch!r} em {s!r}")
        out.append(PTBR_CHAR_MAP[ch])
        i += 1
    out.append(0xFF)
    return bytes(out)


def _assert_free(rom: bytearray, start: int, end: int, label: str) -> None:
    if rom[start:end] != b"\xff" * (end - start):
        raise PatchError(f"Região {label} não está limpa (0x{start:X}..0x{end:X})")


def _write_fixed_sub(rom: bytearray, off: int, max_len: int, body: bytes, name: str) -> None:
    if len(body) > max_len:
        raise PatchError(f"Sub-script {name} excedeu {max_len} B ({len(body)} B)")
    rom[off : off + len(body)] = body


def _hazard_damage_sub(sid: int) -> bytes:
    return (
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00100100)
        + bytes([0x0B, 0x03, 0x0C, 0x03])
        + bytes([0x10]) + u16(sid) + bytes([0x12, 0x40, 0x00])
        + bytes([0x19, 0x03, 0x00]) + u32(0)
        + bytes([0x19, 0x03, 0x01]) + u32(BS_SPIKES_FAINT_TAIL)
        + bytes([0x3C])
    )


def _bs_target_heal_v8() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + bytes([0x01]) + u32(BS_BUT_IT_FAILED) + bytes([0xFF, 0xFF])
        + callasm(ENTRY_TARGET_HEAL_PREP_V8)
        + bytes([0x09, 0x0A])
        + bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x00, 0x0C, 0x00])
        + bytes([0x10, 0x4B, 0x00, 0x12, 0x40, 0x00])
        + bytes([0x28]) + u32(BS_MOVE_END)
    )


def _bs_v8_field_status() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_FIELD_STATUS_PREP_V8)
        + bytes([0x09, 0x0A])
        + callasm(ENTRY_FIELD_STATUS_APPLY_V8)
    )


def _bs_defog(base_addr: int) -> bytes:
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_addr - ROM)
    s.emit(0x00, 0x01)
    s.ptr(BS_BUT_IT_FAILED)
    s.data.extend(u16(0xFFFF))
    s.emit(0x02, 0x03, 0x09, 0x0A)
    s.data.extend(callasm(ENTRY_DEFOG_EVA_CHECK_V8))
    s.ptr("clear_step")
    s.setbyte(0x02021823, 0)
    s.setbyte(STAT_BUFF_ADDR, 7 | (1 << 4) | 0x80)
    s.emit(0x89, 0x01)
    s.ptr("clear_step")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr("clear_step")
    s.emit(0x48, 0x00, 1 << 7, 1)
    s.emit(0x13)
    s.ptr(0x082085AC)
    s.emit(0x12, 0x40, 0x00)
    s.label("clear_step")
    s.data.extend(callasm(ENTRY_DEFOG_CLEAR_V8))
    s.emit(0x10)
    s.data.extend(u16(STR_DEFOG_CLEARED))
    s.emit(0x12, 0x40, 0x00)
    s.goto(BS_MOVE_END)
    return s.finish()


def _bs_shore_up() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_SHORE_UP_PREP_V8)
        + bytes([0x09, 0x0A])
        + bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x00, 0x0C, 0x00])
        + bytes([0x10, 0x4B, 0x00, 0x12, 0x40, 0x00])
        + bytes([0x28]) + u32(BS_MOVE_END)
    )


def _bs_tidy_up(base_addr: int) -> bytes:
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_addr - ROM)
    s.emit(0x00, 0x02, 0x03)
    s.data.extend(callasm(ENTRY_TIDY_UP_CHECK_V8))
    s.emit(0x09, 0x0A)
    s.data.extend(callasm(ENTRY_TIDY_UP_CLEAR_V8))
    s.ptr("boost_step")
    s.emit(0x10)
    s.data.extend(u16(STR_TIDY_UP_CLEARED))
    s.emit(0x12, 0x40, 0x00)
    s.label("boost_step")
    s.setbyte(0x02021823, 0)
    s.emit(0x48, 0x01, (1 << 1) | (1 << 3), 0)
    for i, stat in enumerate((1, 3)):
        s.setbyte(STAT_BUFF_ADDR, stat | (1 << 4))
        s.emit(0x89, 0x41)
        s.ptr(f"next{i}")
        s.emit(0x29, 0x00)
        s.ptr(0x020216C5)
        s.emit(2)
        s.ptr(f"next{i}")
        s.emit(0x13)
        s.ptr(0x082085A0)
        s.emit(0x12, 0x40, 0x00)
        s.label(f"next{i}")
    s.goto(BS_MOVE_END)
    return s.finish()


def _bs_chilly_reception(base_addr: int) -> bytes:
    """Chilly Reception: anuncia piada + invoca Snow + pivot switch."""
    head = (
        bytes([0x00, 0x02, 0x03])
        + bytes([0x10]) + u16(STR_CHILLY_JOKE) + bytes([0x12, 0x40, 0x00])
        + bytes([0x09, 0x0A])
    )
    snow_call_len = 5 + 4
    snow_msg = bytes([0x10]) + u16(STR_SNOW_STARTED) + bytes([0x12, 0x40, 0x00])
    pivot_rel_off = (base_addr - ROM) + len(head) + snow_call_len + len(snow_msg)
    pivot_step_addr = ROM + pivot_rel_off

    # Reutiliza a sequencia canonica de troca pos-golpe do motor_v7 (bs_parting_shot / bs_pivot_hit)
    # 81 <failed_or_end> + 49 02 10 + 50 01 <fainted> + 51 01 02 + 4E 01 00 + ...
    pivot_tail = _build_pivot_switch_tail(pivot_step_addr)
    return (
        head
        + callasm(ENTRY_CHILLY_SNOW_V8) + u32(pivot_step_addr)
        + snow_msg
        + pivot_tail
    )


def _build_pivot_switch_tail(base_addr: int) -> bytes:
    """Sequencia canonica de troca pos-golpe (identica a _emit_pivot_switch_tail do motor_v7)."""
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_addr - ROM)
    s.setbyte(0x0202181C, 0)              # sBattleScripting.moveendState = 0
    s.emit(0x49, 0x02, 0x10)              # moveend 2, 16 (estados 0..15 antes da troca)
    s.data.extend(callasm(0x090C0061))    # ENTRY_PIVOT_CHECK (motor_v7)
    s.emit(0x4F, 0x81)                    # jumpifcannotswitch BS_ATTACKER | ATK4F_DONT_CHECK_STATUSES
    s.ptr(0x081853FC)
    s.emit(0x50, 0x01)                    # openpartyscreen BS_ATTACKER
    s.ptr(0x081853FC)
    s.emit(0xE2, 0x01, 0x3A)              # switchoutabilities BS_ATTACKER; waitstate
    s.emit(0x51, 0x01, 0x02)              # switchhandleorder BS_ATTACKER, 2
    s.emit(0x58, 0x01)                    # returntoball BS_ATTACKER
    s.emit(0x4C, 0x01, 0x4D, 0x01)        # getswitchedmondata + switchindataupdate BS_ATTACKER
    s.emit(0x73, 0x01)                    # hpthresholds BS_ATTACKER
    s.emit(0x10, 0x03, 0x00)              # printstring 3 ("Vai, ...!")
    s.emit(0x4E, 0x01, 0x00, 0x3A)        # switchinanim BS_ATTACKER, 0; waitstate
    s.emit(0x52, 0x01)                    # switchineffects BS_ATTACKER
    s.goto(0x081853FC)                    # finaliza MOVEEND_COUNT (estado 16)
    return s.finish()


def _bs_hazard_hit(source: bytes) -> bytes:
    chunk = source[0x1853CE:0x1853EE]
    faint_tgt = source[0x1853EF:0x1853F6]
    return (
        chunk
        + faint_tgt
        + callasm(ENTRY_HAZARD_HIT_APPLY_V8)
        + bytes([0x10]) + u16(0x0094) + bytes([0x12, 0x40, 0x00])
        + bytes([0x28]) + u32(BS_MOVE_END)
    )


def _bs_mortal_spin(source: bytes) -> bytes:
    chunk = source[0x1853CE:0x1853EE]
    faint_tgt = source[0x1853EF:0x1853F6]
    return (
        chunk
        + bytes([0x2E]) + u32(MOVE_EFFECT_BYTE_ADDR) + bytes([0x02])
        + bytes([0x15])
        + faint_tgt
        + callasm(ENTRY_MORTAL_SPIN_CHECK_V8)
        + bytes([0xBE])
        + bytes([0x28]) + u32(BS_MOVE_END)
    )


def _load_verified_inputs() -> dict[Path, bytes]:
    loaded: dict[Path, bytes] = {}
    for path, expected in INPUTS.items():
        raw = path.read_bytes()
        got = digest(raw)
        if got != expected:
            raise PatchError(f"SHA-256 inválido em {path.name}: {got} != {expected}")
        loaded[path] = raw
    return loaded


def build(source: bytes) -> bytes:
    if len(source) != 33554432 or digest(source) != BASE_SHA256:
        raise PatchError("A ROM de entrada não corresponde ao motor_v7 esperado")

    inputs = _load_verified_inputs()
    payload = inputs[ROOT / "patches/motor_v8/payload.bin"]
    compat = inputs[ROOT / "data/compatibilidade_tms_motor_v8.bin"]
    prior_compat = inputs[ROOT / "data/compatibilidade_tms_motor_v7.bin"]
    if len(compat) != 1026 * 29 or any((a & b) != a for a, b in zip(prior_compat, compat)):
        raise PatchError("Matriz de compatibilidade v8 não é superconjunto estrito da v7")

    out = bytearray(source)
    _assert_free(out, SCRIPTS_V8, SCRIPTS_V8_END, "SCRIPTS_V8")
    _assert_free(out, STRINGS_TABLE_V8, STRINGS_TABLE_V8_END, "STRINGS_TABLE_V8")
    _assert_free(out, STRINGS_TEXT_V8, STRINGS_TEXT_V8_END, "STRINGS_TEXT_V8")
    _assert_free(out, CMD_TABLE_V8, CMD_TABLE_V8_END, "CMD_TABLE_V8")
    _assert_free(out, PAYLOAD_V8, PAYLOAD_V8_END, "PAYLOAD_V8")

    # 1. Reloca gBattleStringsTable (+34 mensagens PT-BR) e atualiza 3 descricoes de golpes.
    str_cursor = STRINGS_TEXT_V8
    new_str_ptrs: list[int] = []
    for idx, (sid, text) in enumerate(NEW_BATTLE_STRINGS):
        expected_sid = 12 + ORIG_BATTLE_STRINGS_COUNT + idx
        if sid != expected_sid:
            raise PatchError(f"SID fora de ordem: 0x{sid:04X} != 0x{expected_sid:04X}")
        encoded = encode_ptbr(text)
        if str_cursor + len(encoded) > STRINGS_TEXT_V8_END:
            raise PatchError("Estouro em STRINGS_TEXT_V8")
        out[str_cursor : str_cursor + len(encoded)] = encoded
        new_str_ptrs.append(ROM + str_cursor)
        str_cursor += len(encoded)

    for mid, desc in sorted(UPDATED_MOVE_DESCRIPTIONS.items()):
        encoded = encode_ptbr(desc)
        if str_cursor + len(encoded) > STRINGS_TEXT_V8_END:
            raise PatchError("Estouro em STRINGS_TEXT_V8 (descrições)")
        out[str_cursor : str_cursor + len(encoded)] = encoded
        struct.pack_into("<I", out, complement.DESC + (mid - 1) * 4, ROM + str_cursor)
        str_cursor += len(encoded)

    orig_str_tbl = bytes(out[ORIG_BATTLE_STRINGS_TABLE : ORIG_BATTLE_STRINGS_TABLE + ORIG_BATTLE_STRINGS_COUNT * 4])
    reloc_str_tbl = orig_str_tbl + b"".join(u32(p) for p in new_str_ptrs)
    out[STRINGS_TABLE_V8 : STRINGS_TABLE_V8 + len(reloc_str_tbl)] = reloc_str_tbl

    for ref in BATTLE_STRINGS_TABLE_REFS:
        if struct.unpack_from("<I", out, ref)[0] != ROM + ORIG_BATTLE_STRINGS_TABLE:
            raise PatchError(f"Referência inesperada a gBattleStringsTable em 0x{ref:X}")
        struct.pack_into("<I", out, ref, ROM + STRINGS_TABLE_V8)

    if bytes(out[BATTLE_STRING_CAP_SITE : BATTLE_STRING_CAP_SITE + 4]) != bytes([0xC1, 0x23, 0x5B, 0x00]):
        raise PatchError("Limite inesperado em BufferStringBattle")
    out[BATTLE_STRING_CAP_SITE : BATTLE_STRING_CAP_SITE + 2] = bytes([0xD4, 0x23])  # 0xD4 << 1 = 424 > 419

    # 2. Instala sub-scripts fixos e efeitos 234 + 236..242 em SCRIPTS_V8.
    _write_fixed_sub(
        out, SUB_GRAVITY_CANCEL, 16,
        bytes([0x10]) + u16(STR_GRAVITY_BLOCK) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_GRAVITY_CANCEL",
    )
    _write_fixed_sub(
        out, SUB_PTERRAIN_CANCEL, 16,
        bytes([0x10]) + u16(STR_PSYCHIC_BLOCK) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_PTERRAIN_CANCEL",
    )
    _write_fixed_sub(
        out, SUB_TERRAIN_BLOCK, 16,
        bytes([0x10]) + u16(STR_TERRAIN_PROTECT) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_TERRAIN_BLOCK",
    )
    for k, sid in enumerate(ENDTURN_MSG_ORDER):
        _write_fixed_sub(
            out, SUB_ENDTURN_MSGS + 8 * k, 8,
            bytes([0x10]) + u16(sid) + bytes([0x12, 0x40, 0x00, 0x3F, 0x00]),
            f"SUB_ENDTURN_MSG_{k}",
        )
    _write_fixed_sub(
        out, SUB_ENDTURN_GRASSY, 32,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x0A, 0x0C, 0x0A, 0x10]) + u16(STR_GRASSY_HEAL) + bytes([0x12, 0x40, 0x00, 0x3F]),
        "SUB_ENDTURN_GRASSY",
    )
    _write_fixed_sub(out, SUB_HAZARD_SPIKES_G, 64, _hazard_damage_sub(0x0095), "SUB_HAZARD_SPIKES_G")
    _write_fixed_sub(out, SUB_HAZARD_SROCK, 64, _hazard_damage_sub(STR_STEALTH_ROCK_HURT), "SUB_HAZARD_SROCK")
    _write_fixed_sub(
        out, SUB_TSPIKES_ABSORB, 16,
        bytes([0x10]) + u16(STR_TSPIKES_ABSORB) + bytes([0x12, 0x40, 0x00, 0x3C]),
        "SUB_TSPIKES_ABSORB",
    )

    from scripts import efeitos_gen9 as effects

    s_sw = effects.BattleScript(SUB_STICKY_WEB_DROP)
    s_sw.emit(0x10)
    s_sw.data.extend(u16(STR_STICKY_WEB_CAUGHT))
    s_sw.emit(0x12, 0x40, 0x00)
    s_sw.setbyte(0x02021823, 0)
    s_sw.setbyte(STAT_BUFF_ADDR, 3 | (1 << 4) | 0x80)
    s_sw.emit(0x89, 0x01)
    s_sw.ptr("restore")
    s_sw.emit(0x29, 0x00)
    s_sw.ptr(0x020216C5)
    s_sw.emit(2)
    s_sw.ptr("restore")
    s_sw.emit(0x48, 0x00, 1 << 3, 1)
    s_sw.emit(0x13)
    s_sw.ptr(0x082085AC)
    s_sw.emit(0x12, 0x40, 0x00)
    s_sw.label("restore")
    s_sw.data.extend(callasm(ENTRY_STICKY_WEB_RESTORE_V8))
    s_sw.emit(0x3C)
    _write_fixed_sub(out, SUB_STICKY_WEB_DROP, 64, s_sw.finish(), "SUB_STICKY_WEB_DROP")
    _write_fixed_sub(
        out, SUB_SUBSTITUTE_FADE, 16,
        bytes([0x45, 0x0A, 0x02]) + u32(0) + bytes([0x3C]),
        "SUB_SUBSTITUTE_FADE",
    )
    _write_fixed_sub(
        out, SUB_RAPIDSPIN_CLEAR, 16,
        bytes([0x10]) + u16(STR_HAZARDS_CLEARED) + bytes([0x12, 0x40, 0x00, 0x3C]),
        "SUB_RAPIDSPIN_CLEAR",
    )
    for idx, sid in enumerate(STATUS_TAIL_ORDER):
        _write_fixed_sub(
            out, SUB_STATUS_TAILS + 12 * idx, 12,
            bytes([0x10]) + u16(sid) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END) + bytes([0x00]),
            f"SUB_STATUS_TAIL_{idx}",
        )

    sc_cursor = DYNAMIC_SCRIPTS_START
    effect_builders = (
        (EFF_TARGET_HEAL, False, lambda at: _bs_target_heal_v8()),
        (EFF_V8_FIELD_STATUS, True, lambda at: _bs_v8_field_status()),
        (EFF_DEFOG, True, lambda at: _bs_defog(ROM + at)),
        (EFF_SHORE_UP, True, lambda at: _bs_shore_up()),
        (EFF_TIDY_UP, True, lambda at: _bs_tidy_up(ROM + at)),
        (EFF_CHILLY_RECEPTION, True, lambda at: _bs_chilly_reception(ROM + at)),
        (EFF_HAZARD_HIT, True, lambda at: _bs_hazard_hit(source)),
        (EFF_MORTAL_SPIN, True, lambda at: _bs_mortal_spin(source)),
    )
    for eff_id, must_be_free, builder in effect_builders:
        cur_ptr = struct.unpack_from("<I", source, complement.SCRIPT_TABLE + eff_id * 4)[0]
        if must_be_free and cur_ptr != 0x081853A8:
            raise PatchError(f"Slot de efeito {eff_id} já ocupado: 0x{cur_ptr:08X}")
        blob = builder(sc_cursor)
        if sc_cursor + len(blob) > SCRIPTS_V8_END:
            raise PatchError(f"Estouro em SCRIPTS_V8 no efeito {eff_id}")
        out[sc_cursor : sc_cursor + len(blob)] = blob
        struct.pack_into("<I", out, complement.SCRIPT_TABLE + eff_id * 4, ROM + sc_cursor)
        sc_cursor = (sc_cursor + len(blob) + 3) & ~3

    # 3. Instala payload Thumb em 0x090C3000, tabela de comandos em 0x090C2800 e hooks.
    if len(payload) > PAYLOAD_V8_END - PAYLOAD_V8:
        raise PatchError("Payload do motor_v8 excede a reserva")
    out[PAYLOAD_V8 : PAYLOAD_V8 + len(payload)] = payload

    cmd_tbl = bytearray(source[v7.CMD_TABLE_V7 : v7.CMD_TABLE_V7 + 256 * 4])
    overrides = {
        0x00: ENTRY_ATTACKCANCELER_V8,
        0x01: ENTRY_ACCURACYCHECK_V8,
        0x05: ENTRY_DAMAGE_V8,
        0x06: ENTRY_TYPECALC_V8,
        0x15: ENTRY_SETEFFECT_CHANCE_V8,
        0x16: ENTRY_SETEFFECT_PRIMARY_V8,
        0x17: ENTRY_SETEFFECT_SECONDARY_V8,
        0x52: ENTRY_SWITCHINEFFECTS_V8,
        0x84: ENTRY_JUMPIFCANTSLEEP_V8,
        0xBE: ENTRY_RAPIDSPINFREE_V8,
        0xE9: ENTRY_WEATHERBALL_V8,
        0xEE: ENTRY_BRICKBREAK_V8,
    }
    for opc, target in overrides.items():
        struct.pack_into("<I", cmd_tbl, opc * 4, target)
    out[CMD_TABLE_V8 : CMD_TABLE_V8 + len(cmd_tbl)] = cmd_tbl

    for site in v6.CMD_TABLE_PTRS:
        if struct.unpack_from("<I", source, site)[0] != ROM + v7.CMD_TABLE_V7:
            raise PatchError(f"Ponteiro inesperado de CMD_TABLE em 0x{site:X}")
        struct.pack_into("<I", out, site, ROM + CMD_TABLE_V8)

    hooks = (
        (BATTLE_INIT_LIT, v7.ENTRY_BATTLE_INIT_V7, ENTRY_BATTLE_INIT_V8),
        (TURN_START_LIT, v7.ENTRY_TURN_START_V7, ENTRY_TURN_START_V8),
        (SET_TURN_ORDER_LIT, 0x080541A5, ENTRY_SET_TURN_ORDER_V8),
        (ENDTURN_CONT_LIT, 0x08053221, ENTRY_ENDTURN_V8),
    )
    for lit_off, expected_old, new_val in hooks:
        if struct.unpack_from("<I", source, lit_off)[0] != expected_old:
            raise PatchError(f"Literal de hook inesperado em 0x{lit_off:X}")
        struct.pack_into("<I", out, lit_off, new_val)

    # 4. Atualiza MOVE_TABLE, NEW_MOVE_TABLE das 10 TMs, descricoes USO UNICO e loja (229 TMs).
    field_offsets = {
        "eff": 0, "pwr": 1, "typ": 2, "acc": 3, "pp": 4,
        "chance": 5, "tgt": 6, "prio": 7, "flags": 8,
    }
    for mid, changes in MOVE_UPDATES_V8.items():
        base = complement.MOVE + 12 * mid
        for key, val in changes.items():
            out[base + field_offsets[key]] = val & 0xFF

    tm_rows = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/tms_motor_v8.csv"].decode("utf-8"))))
    if len(tm_rows) != 229:
        raise PatchError(f"Esperadas 229 TMs em tms_motor_v8.csv, obtidas {len(tm_rows)}")

    available: dict[int, int] = {}
    for row in tm_rows:
        tm = int(row["tm"])
        mid = int(row["internal_move"])
        if row["status"] != "disponivel" or mid <= 0:
            raise PatchError(f"TM{tm:03d} deveria estar disponível no motor_v8: {row}")
        available[tm] = mid

    for tm, mid in sorted(NEWLY_AVAILABLE_TMS_V8.items()):
        if available.get(tm) != mid:
            raise PatchError(f"Mapeamento divergente para TM{tm:03d}")
        move_slot = previous.NEW_MOVE_TABLE + (374 + tm - 289) * 2
        if struct.unpack_from("<H", source, move_slot)[0] != 0:
            raise PatchError(f"TM{tm:03d} já tinha golpe associado na ROM de entrada")
        struct.pack_into("<H", out, move_slot, mid)

        mtype = out[complement.MOVE + mid * 12 + 2]
        expected_pal = v6.TYPE_TM_PALETTES[mtype]
        icon_pic, icon_pal = struct.unpack_from("<II", out, v6.ICON_TABLE_V6 + (374 + tm) * 8)
        if (icon_pic, icon_pal) != (v6.TM_DISC_PIC, expected_pal):
            raise PatchError(f"Ícone da TM{tm:03d} divergente da paleta esperada para tipo {mtype}")

    out[0xE06000 : 0xE06000 + len(compat)] = compat
    out[v6.ITEM_TEXT_START : v6.ITEM_TEXT_END] = b"\xff" * (v6.ITEM_TEXT_END - v6.ITEM_TEXT_START)
    txt_cursor = v6.ITEM_TEXT_START
    for tm, mid in sorted(available.items()):
        entry = out[complement.NAMES + mid * 17 : complement.NAMES + (mid + 1) * 17]
        if 0xFF not in entry:
            raise PatchError(f"Nome do golpe {mid} sem terminador")
        move_name = entry[: entry.index(0xFF)]
        item_desc = previous.text("GOLPE ")[:-1] + move_name + previous.text("\nUSO UNICO")
        if txt_cursor + len(item_desc) > v6.ITEM_TEXT_END:
            raise PatchError("Descrições de itens excedem a área reservada")
        out[txt_cursor : txt_cursor + len(item_desc)] = item_desc
        struct.pack_into("<I", out, previous.NEW_ITEMS + (374 + tm) * previous.ITEM_SIZE + 20, ROM + txt_cursor)
        txt_cursor += len(item_desc)

    products = b"".join(struct.pack("<H", 374 + tm) for tm in sorted(available)) + b"\x00\x00"
    shop_cap = previous.SHOP_SCRIPT - previous.SHOP_LIST
    if len(products) > shop_cap:
        raise PatchError("Lista de produtos da loja excedeu o espaço")
    out[previous.SHOP_LIST : previous.SHOP_SCRIPT] = products + b"\xff" * (shop_cap - len(products))

    # 5. Recompila learnsets por nível (+245 entradas, preservando 100% das 14.382 do motor_v7).
    prior_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/learnsets_motor_v7.csv"].decode("utf-8"))))
    cur_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/learnsets_motor_v8.csv"].decode("utf-8"))))
    lv_key = lambda r: (int(r["species"]), int(r["level"]), int(r["internal_move"]), int(r["api_move"]))
    if len(cur_lv) != 14627 or not set(map(lv_key, prior_lv)).issubset(set(map(lv_key, cur_lv))):
        raise PatchError("Learnsets anteriores do motor_v7 não foram integralmente preservados")
    lists: dict[int, list[tuple[int, int]]] = {sid: [] for sid in range(1, 1026)}
    for r in cur_lv:
        sid, lv, mid, _api = lv_key(r)
        if sid not in lists or not 0 <= lv <= 100 or not 0 < mid < MOVE_COUNT:
            raise PatchError(f"Entrada de nível inválida: {r}")
        lists[sid].append((lv, mid))
    if any(not vals or len(vals) > 50 or vals != sorted(vals, key=lambda v: v[0]) for vals in lists.values()):
        raise PatchError("Lista de nível fora dos limites do motor")
    lv_blob = level.build_tables(lists)
    if level.TABLE + len(lv_blob) > 0xF60000:
        raise PatchError("Tabelas de nível excederam a reserva 0x08F50000..0x08F60000")
    out[level.TABLE:0xF60000] = lv_blob + b"\xff" * (0xF60000 - level.TABLE - len(lv_blob))

    result = bytes(out)
    if digest(result) != OUTPUT_SHA256:
        raise PatchError(f"SHA-256 divergente do esperado: {digest(result)} != {OUTPUT_SHA256}")
    return result


apply = build


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", "--input", dest="rom", type=Path, required=True)
    parser.add_argument("--saida", "--output", dest="saida", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.rom.resolve() == args.saida.resolve() or args.saida.exists():
            raise PatchError("A saída precisa ser um arquivo novo")
        src = args.rom.read_bytes()
        out = build(src)
        if OUTPUT_SHA256 and digest(out) != OUTPUT_SHA256:
            raise PatchError("SHA-256 da saída divergente do esperado")
        write_new_file(args.rom, args.saida, out)
        print(f"Entrada preservada: {digest(src)}\nNova cópia: {args.saida}\nSHA-256: {digest(out)}")
        print("Motor parcial v8: 229/229 TMs SV habilitadas + clima Snow, 4 terrenos, salas, gravidade e hazards.")
    except (OSError, ValueError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
