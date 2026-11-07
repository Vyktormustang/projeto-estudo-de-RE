#!/usr/bin/env python3
"""Aplica o motor_v9 sobre a ROM motor_v8 identificada por SHA-256.

Escopo estrito e auditável sobre o motor_v8:
  1. Instala estado efêmero de batalha do motor_v9 em 0x0203FCA0..0x0203FD5F
     (sem tocar estruturas persistentes ou saves) e encadeia início de batalha
     (0x08051D74), início de turno (0x0805439C), fim de turno (0x08053208) e
     GetHoldEffect (0x080C725C, apenas em batalha sob Magic Room), além de
     relocar gBattleScriptingCommandsTable em 0x090C8800 e gBattleStringsTable
     em 0x090C7000 (+37 mensagens PT-BR).
  2. Restaura 51 golpes não-TM de subida de nível (+378 entradas: 14.627 ->
     15.005 linhas em data/learnsets_motor_v9.csv, preservando 100% das
     entradas anteriores e das 229/229 TMs de Scarlet/Violet) em seis famílias:
       - Modificação de tipo, 3º tipo e eletrificação: Soak (486), Magic Powder
         (675), Reflect Type (512), Trick-or-Treat (563), Forest's Curse (567)
         e Electrify (578).
       - Trocas, divisões, inversões e impulsos compostos de stats: Power Trick
         (379), Power Swap (384), Guard Swap (385), Heart Swap (391), Speed Swap
         (638), Guard Split (469), Power Split (470), Topsy-Turvy (572),
         Acupressure (367), Venom Drench (595), Toxic Thread (627), Tar Shot
         (674), Decorate (684), Spicy Extract (750), No Retreat (673),
         Clangorous Soul (682), Fillet Away (760), Magnetic Flux (598), Gear Up
         (629), Flower Shield (575) e Rototiller (559).
       - Regeneração, drenagem por Atk, sacrifício/substituto e purificação:
         Aqua Ring (392), Strength Sap (623), Healing Wish (361), Lunar Dance
         (460), Shed Tail (770), Psycho Shift (375), Purify (640), Take Heart
         (743), Jungle Healing (710), Lunar Blessing (742) e Dark Void (463).
       - Manipulação de habilidade: Gastro Acid (380), Worry Seed (388),
         Entrainment (493) e Doodle (759).
       - Controle de ordem/cópia, foco crítico, dano fixo por HP e Natural Gift:
         Copycat (383), After You (494), Quash (510), Final Gambit (514),
         Laser Focus (628) e Natural Gift (363).
       - Salas de itens e travas de troca: Magic Room (477), Octolock (678) e
         Fairy Lock (583).

Seis golpes de subida de nível (24 linhas das 729 originais = 3,3%) permanecem
documentadamente fora de escopo por dependerem de habilidades ou UI ausentes na
base Gen 3: Simple Beam (492), Ally Switch (501), Instruct (644), Stuff Cheeks
(672), Teatime (677) e Revival Blessing (755). Não altera saves pessoais; grava
sempre arquivo novo.
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

from scripts import complemento_gen9 as complement
from scripts import golpes_gen9 as level
from scripts import motor_v6 as v6
from scripts import motor_v8 as v8
from scripts.treino_ev import write_new_file

BASE_SHA256 = v8.OUTPUT_SHA256
OUTPUT_SHA256 = "2936a08fc95f40c7788b6136f209ab5cab31aec062d615f2a458f45b123e0e6f"

INPUTS = {
    ROOT / "patches/motor_v9/payload.bin": "0cdc8e30ea289e49b5ea6f7c645078f8bec59f1ebc1f4d8eeeb1c4db93f67749",
    ROOT / "data/learnsets_motor_v9.csv": "de3f00717240a20c513899422789082d20e7e56f911671677c92abbf26ccfeae",
    ROOT / "data/learnsets_motor_v8.csv": "19abc5661267157524b9dcdc9ad769cdf12a20f9f44a3be63f134ae2ec9120f7",
}

ROM = 0x08000000
MOVE_COUNT = v8.MOVE_COUNT

# Hooks encadeados sobre motor_v8 + GetHoldEffect nativo
BATTLE_INIT_LIT = v8.BATTLE_INIT_LIT
TURN_START_LIT = v8.TURN_START_LIT
ENDTURN_CONT_LIT = v8.ENDTURN_CONT_LIT
GET_HOLD_EFFECT_SITE = 0x0C725C
GET_HOLD_EFFECT_ORIG = bytes.fromhex("97 23 00 04 00 0c 9b 00")

# Tabela de strings de batalha relocada (sid 12..419 -> 12..456)
V8_BATTLE_STRINGS_COUNT = v8.ORIG_BATTLE_STRINGS_COUNT + len(v8.NEW_BATTLE_STRINGS)
BATTLE_STRING_CAP_SITE = v8.BATTLE_STRING_CAP_SITE
BATTLE_STRINGS_TABLE_REFS = v8.BATTLE_STRINGS_TABLE_REFS

# Regiões exclusivas do motor_v9 em espaço livre 0xFF (após 0x10C6000)
SCRIPTS_V9 = 0x10C6000
SCRIPTS_V9_END = 0x10C7000
STRINGS_TABLE_V9 = 0x10C7000
STRINGS_TABLE_V9_END = 0x10C7A00
STRINGS_TEXT_V9 = 0x10C7A00
STRINGS_TEXT_V9_END = 0x10C8800
CMD_TABLE_V9 = 0x10C8800
CMD_TABLE_V9_END = 0x10C8C00
PAYLOAD_V9 = 0x10C9000
PAYLOAD_V9_END = 0x10CD000

# Sub-scripts em endereços fixos dentro de SCRIPTS_V9 (sincronizados com motor_v9.c)
SUB_ENDTURN_AQUA_RING = 0x10C6000
SUB_ENDTURN_OCTOLOCK = 0x10C6020
SUB_ENDTURN_MROOM = 0x10C60A0
SUB_SWITCHIN_HWISH = 0x10C60B0
SUB_SWITCHIN_LDANCE = 0x10C60D0
SUB_WORRY_SEED_WAKE = 0x10C60F0
SUB_OCTOLOCK_SET = 0x10C6110
SUB_TOXIC_THREAD_PSN = 0x10C6130
SUB_CLEANSE_CURE_STEP = 0x10C6150
SUB_CLEANSE_HEAL_STEP = 0x10C6170
SUB_PSHIFT_INFLICT = 0x10C6190
SUB_PSHIFT_SELF_CURE = 0x10C61B0
SUB_MSG_TAILS = 0x10C61D0         # 28 slots de 12 B (0x10C61D0..0x10C631F)
DYNAMIC_SCRIPTS_START = 0x10C6340

# Vetores Thumb em patches/motor_v9/entry.s (base 0x090C9001 + 8*i)
PAYLOAD_V9_THUMB = ROM + PAYLOAD_V9 + 1
ENTRY_BATTLE_INIT_V9 = PAYLOAD_V9_THUMB + 0 * 8
ENTRY_TURN_START_V9 = PAYLOAD_V9_THUMB + 1 * 8
ENTRY_ENDTURN_V9 = PAYLOAD_V9_THUMB + 2 * 8
ENTRY_GET_HOLD_EFFECT_V9 = PAYLOAD_V9_THUMB + 3 * 8
ENTRY_ATTACKCANCELER_V9 = PAYLOAD_V9_THUMB + 4 * 8
ENTRY_CRITCALC_V9 = PAYLOAD_V9_THUMB + 5 * 8
ENTRY_DAMAGE_V9 = PAYLOAD_V9_THUMB + 6 * 8
ENTRY_TYPECALC_V9 = PAYLOAD_V9_THUMB + 7 * 8
ENTRY_SWITCHINEFFECTS_V9 = PAYLOAD_V9_THUMB + 8 * 8
ENTRY_ONESHOT_PREP_V9 = PAYLOAD_V9_THUMB + 9 * 8
ENTRY_ONESHOT_APPLY_V9 = PAYLOAD_V9_THUMB + 10 * 8
ENTRY_MULTI_PREP_V9 = PAYLOAD_V9_THUMB + 11 * 8
ENTRY_MULTI_PRE_FX_V9 = PAYLOAD_V9_THUMB + 12 * 8
ENTRY_MULTI_NEXT_STAT_V9 = PAYLOAD_V9_THUMB + 13 * 8
ENTRY_MULTI_POST_FX_V9 = PAYLOAD_V9_THUMB + 14 * 8
ENTRY_STRENGTH_SAP_PREP_V9 = PAYLOAD_V9_THUMB + 15 * 8
ENTRY_STRENGTH_SAP_HEAL_V9 = PAYLOAD_V9_THUMB + 16 * 8
ENTRY_WISH_SAC_PREP_V9 = PAYLOAD_V9_THUMB + 17 * 8
ENTRY_SHED_TAIL_PREP_V9 = PAYLOAD_V9_THUMB + 18 * 8
ENTRY_SHED_TAIL_INSTALL_V9 = PAYLOAD_V9_THUMB + 19 * 8
ENTRY_CLEANSE_PREP_V9 = PAYLOAD_V9_THUMB + 20 * 8
ENTRY_CLEANSE_STEP_V9 = PAYLOAD_V9_THUMB + 21 * 8
ENTRY_TURN_CTRL_EXEC_V9 = PAYLOAD_V9_THUMB + 22 * 8
ENTRY_FINAL_GAMBIT_PREP_V9 = PAYLOAD_V9_THUMB + 23 * 8
ENTRY_FINAL_GAMBIT_DMG_V9 = PAYLOAD_V9_THUMB + 24 * 8
ENTRY_NATURAL_GIFT_PREP_V9 = PAYLOAD_V9_THUMB + 25 * 8
ENTRY_RESTORE_TGT_V9 = PAYLOAD_V9_THUMB + 26 * 8
ENTRY_DARK_VOID_STEP_V9 = PAYLOAD_V9_THUMB + 27 * 8

BS_HIT_CALC_START = 0x081853D8
BS_MOVE_END = 0x081853F6
BS_FINISH_MOVEEND = 0x081853FC
BS_MISS_NO_PP = 0x08185406
BS_MISS_AFTER_PP = 0x08185408
BS_BUT_IT_FAILED = 0x0818689A
STAT_BUFF_ADDR = 0x02021822
MOVE_EFFECT_BYTE_ADDR = 0x020216C3
HIT_MARKER_ADDR = 0x0202160C

EFF_V9_ONESHOT_ACC = 243
EFF_V9_ONESHOT_NOACC = 244
EFF_V9_MULTI_ACC = 245
EFF_V9_MULTI_NOACC = 246
EFF_V9_STRENGTH_SAP = 247
EFF_V9_WISH_SACRIFICE = 248
EFF_V9_SHED_TAIL = 249
EFF_V9_CLEANSE = 250
EFF_V9_DARK_VOID = 251
EFF_V9_COPYCAT = 252
EFF_V9_FINAL_GAMBIT = 253
EFF_V9_NATURAL_GIFT = 254

STR_AQUA_RING_SET = 0x01A4
STR_AQUA_RING_HEAL = 0x01A5
STR_SOAK_WATER = 0x01A6
STR_MAGIC_POWDER_PSY = 0x01A7
STR_REFLECT_TYPE = 0x01A8
STR_TRICK_OR_TREAT = 0x01A9
STR_FORESTS_CURSE = 0x01AA
STR_ELECTRIFY = 0x01AB
STR_POWER_TRICK = 0x01AC
STR_POWER_SWAP = 0x01AD
STR_GUARD_SWAP = 0x01AE
STR_HEART_SWAP = 0x01AF
STR_SPEED_SWAP = 0x01B0
STR_GUARD_SPLIT = 0x01B1
STR_POWER_SPLIT = 0x01B2
STR_TOPSY_TURVY = 0x01B3
STR_GASTRO_ACID = 0x01B4
STR_WORRY_SEED_SET = 0x01B5
STR_ENTRAINMENT = 0x01B6
STR_DOODLE = 0x01B7
STR_LASER_FOCUS = 0x01B8
STR_MAGIC_ROOM_SET = 0x01B9
STR_MAGIC_ROOM_END = 0x01BA
STR_FAIRY_LOCK_SET = 0x01BB
STR_AFTER_YOU = 0x01BC
STR_QUASH = 0x01BD
STR_NO_RETREAT = 0x01BE
STR_TAR_SHOT = 0x01BF
STR_DARK_VOID_CANT = 0x01C0
STR_OCTOLOCK_SET = 0x01C1
STR_HWISH_CAME_TRUE = 0x01C2
STR_LDANCE_CLOAKED = 0x01C3
STR_SHED_TAIL_CREATED = 0x01C4
STR_STATUS_CURED_SCR = 0x01C5
STR_PSHIFT_TRANSFERRED = 0x01C6
STR_STRENGTH_SAP_HEAL = 0x01C7
STR_LIQUID_OOZE_HURT = 0x01C8

NEW_BATTLE_STRINGS_V9: tuple[tuple[int, str], ...] = (
    (STR_AQUA_RING_SET, "{ATK} envolveu-se\nem um véu de água!"),
    (STR_AQUA_RING_HEAL, "O véu de água restaurou\no HP de {SCR}!"),
    (STR_SOAK_WATER, "{TGT} mudou para\no tipo Água!"),
    (STR_MAGIC_POWDER_PSY, "{TGT} mudou para\no tipo Psíquico!"),
    (STR_REFLECT_TYPE, "{ATK} copiou o\ntipo de {TGT}!"),
    (STR_TRICK_OR_TREAT, "O tipo Fantasma foi\nadicionado a {TGT}!"),
    (STR_FORESTS_CURSE, "O tipo Grama foi\nadicionado a {TGT}!"),
    (STR_ELECTRIFY, "Os golpes de {TGT}\nforam eletrificados!"),
    (STR_POWER_TRICK, "{ATK} trocou Ataque\ne Defesa!"),
    (STR_POWER_SWAP, "{ATK} trocou mudanças\nofensivas com {TGT}!"),
    (STR_GUARD_SWAP, "{ATK} trocou mudanças\ndefensivas com {TGT}!"),
    (STR_HEART_SWAP, "{ATK} trocou mudanças\nde stats com {TGT}!"),
    (STR_SPEED_SWAP, "{ATK} trocou a\nVelocidade com {TGT}!"),
    (STR_GUARD_SPLIT, "{ATK} dividiu sua\ndefesa com {TGT}!"),
    (STR_POWER_SPLIT, "{ATK} dividiu sua\nforça com {TGT}!"),
    (STR_TOPSY_TURVY, "As mudanças de stats de\n{TGT} foram invertidas!"),
    (STR_GASTRO_ACID, "A habilidade de {TGT}\nfoi suprimida!"),
    (STR_WORRY_SEED_SET, "A habilidade de {TGT}\nvirou Insônia!"),
    (STR_ENTRAINMENT, "{TGT} adquiriu a\nhabilidade de {ATK}!"),
    (STR_DOODLE, "{ATK} copiou a\nhabilidade de {TGT}!"),
    (STR_LASER_FOCUS, "{ATK} concentrou\nintensamente o foco!"),
    (STR_MAGIC_ROOM_SET, "Criou uma área em que\nitens perdem o efeito!"),
    (STR_MAGIC_ROOM_END, "O efeito de MAGIC ROOM\npassou!"),
    (STR_FAIRY_LOCK_SET, "Ninguém poderá fugir\nno próximo turno!"),
    (STR_AFTER_YOU, "{TGT} aceitou\na gentileza!"),
    (STR_QUASH, "{ATK} atrasou a\nação de {TGT}!"),
    (STR_NO_RETREAT, "{ATK} não pode\nmais recuar!"),
    (STR_TAR_SHOT, "{TGT} ficou mais\nfraco contra Fogo!"),
    (STR_DARK_VOID_CANT, "Mas {ATK} não consegue\nusar o golpe!"),
    (STR_OCTOLOCK_SET, "{TGT} não pode mais\nfugir de OCTOLOCK!"),
    (STR_HWISH_CAME_TRUE, "O desejo de cura se\nrealizou para {SCR}!"),
    (STR_LDANCE_CLOAKED, "{SCR} foi envolvido\npela luz do luar!"),
    (STR_SHED_TAIL_CREATED, "{ATK} criou um\nsubstituto para trocar!"),
    (STR_STATUS_CURED_SCR, "{SCR} foi curado do\nproblema de status!"),
    (STR_PSHIFT_TRANSFERRED, "{ATK} transferiu seu\nproblema de status!"),
    (STR_STRENGTH_SAP_HEAL, "{TGT} teve sua força\ndrenada!"),
    (STR_LIQUID_OOZE_HURT, "{ATK} sugou o\nlodo líquido!"),
)

# Ordem exata dos 28 slots de BS_V9_MSG_TAILS (0..27) sincronizada com motor_v9.c
MSG_TAIL_ORDER_V9: tuple[int, ...] = (
    STR_AQUA_RING_SET,      # 0
    STR_SOAK_WATER,         # 1
    STR_MAGIC_POWDER_PSY,   # 2
    STR_REFLECT_TYPE,       # 3
    STR_TRICK_OR_TREAT,     # 4
    STR_FORESTS_CURSE,      # 5
    STR_ELECTRIFY,          # 6
    STR_POWER_TRICK,        # 7
    STR_POWER_SWAP,         # 8
    STR_GUARD_SWAP,         # 9
    STR_HEART_SWAP,         # 10
    STR_SPEED_SWAP,         # 11
    STR_GUARD_SPLIT,        # 12
    STR_POWER_SPLIT,        # 13
    STR_TOPSY_TURVY,        # 14
    STR_GASTRO_ACID,        # 15
    STR_WORRY_SEED_SET,     # 16
    STR_ENTRAINMENT,        # 17
    STR_DOODLE,             # 18
    STR_LASER_FOCUS,        # 19
    STR_MAGIC_ROOM_SET,     # 20
    STR_MAGIC_ROOM_END,     # 21
    STR_FAIRY_LOCK_SET,     # 22
    STR_AFTER_YOU,          # 23
    STR_QUASH,              # 24
    STR_NO_RETREAT,         # 25
    STR_TAR_SHOT,           # 26
    STR_DARK_VOID_CANT,     # 27
)

MOVE_UPDATES_V9: dict[int, dict[str, int]] = {
    # 243: One-shot com precisão (acc > 0)
    380: {"eff": EFF_V9_ONESHOT_ACC},
    388: {"eff": EFF_V9_ONESHOT_ACC},
    486: {"eff": EFF_V9_ONESHOT_ACC},
    493: {"eff": EFF_V9_ONESHOT_ACC},
    510: {"eff": EFF_V9_ONESHOT_ACC},
    563: {"eff": EFF_V9_ONESHOT_ACC},
    567: {"eff": EFF_V9_ONESHOT_ACC},
    675: {"eff": EFF_V9_ONESHOT_ACC},
    678: {"eff": EFF_V9_ONESHOT_ACC},
    759: {"eff": EFF_V9_ONESHOT_ACC},
    # 244: One-shot sem rolagem de precisão (acc == 0)
    379: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x10},
    384: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    385: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    391: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    392: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x10},
    469: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    470: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    477: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x10, "flags": 0x00},
    494: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    512: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    572: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    578: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    583: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x10, "flags": 0x00},
    628: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x10},
    638: {"eff": EFF_V9_ONESHOT_NOACC, "tgt": 0x00},
    # 245: Fila de stats com precisão (acc > 0)
    595: {"eff": EFF_V9_MULTI_ACC},
    627: {"eff": EFF_V9_MULTI_ACC},
    674: {"eff": EFF_V9_MULTI_ACC},
    # 246: Fila de stats sem rolagem de precisão / auto-alvo
    367: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x10},
    559: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x10, "flags": 0x00},
    575: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x10, "flags": 0x00},
    598: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x10, "flags": 0x08},
    629: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x10, "flags": 0x08},
    673: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x10},
    682: {"eff": EFF_V9_MULTI_NOACC, "acc": 0, "tgt": 0x10},
    684: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x00},
    743: {"eff": EFF_V9_MULTI_NOACC, "pp": 10, "tgt": 0x10},
    750: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x00},
    760: {"eff": EFF_V9_MULTI_NOACC, "tgt": 0x10},
    # 247..254: Famílias especializadas
    623: {"eff": EFF_V9_STRENGTH_SAP},
    361: {"eff": EFF_V9_WISH_SACRIFICE, "tgt": 0x10},
    460: {"eff": EFF_V9_WISH_SACRIFICE, "tgt": 0x10},
    770: {"eff": EFF_V9_SHED_TAIL, "tgt": 0x10},
    375: {"eff": EFF_V9_CLEANSE},
    640: {"eff": EFF_V9_CLEANSE},
    710: {"eff": EFF_V9_CLEANSE, "tgt": 0x10},
    742: {"eff": EFF_V9_CLEANSE, "tgt": 0x10},
    463: {"eff": EFF_V9_DARK_VOID},
    383: {"eff": EFF_V9_COPYCAT, "tgt": 0x10},
    514: {"eff": EFF_V9_FINAL_GAMBIT},
    363: {"eff": EFF_V9_NATURAL_GIFT},
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


def _assert_free(rom: bytearray, start: int, end: int, label: str) -> None:
    if rom[start:end] != b"\xff" * (end - start):
        raise PatchError(f"Região {label} não está limpa (0x{start:X}..0x{end:X})")


def _write_fixed_sub(rom: bytearray, off: int, max_len: int, body: bytes, name: str) -> None:
    if len(body) > max_len:
        raise PatchError(f"Sub-script {name} excedeu {max_len} B ({len(body)} B)")
    rom[off : off + len(body)] = body


def _sub_endturn_octolock(base_off: int) -> bytes:
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_off)
    s.setbyte(0x02021823, 0)
    for i, stat in enumerate((2, 5)):
        s.setbyte(STAT_BUFF_ADDR, stat | (1 << 4) | 0x80)
        s.emit(0x89, 0x01)
        s.ptr(f"nx{i}")
        s.emit(0x29, 0x00)
        s.ptr(0x020216C5)
        s.emit(2)
        s.ptr(f"nx{i}")
        s.emit(0x29, 0x00)
        s.ptr(0x020216C5)
        s.emit(3)
        s.ptr(f"nx{i}")
        s.emit(0x47, 0x45, 0x00, 0x01)
        s.ptr(0x02021818)
        s.emit(0x13)
        s.ptr(0x082085AC)
        s.emit(0x12, 0x40, 0x00)
        s.label(f"nx{i}")
    s.data.extend(callasm(ENTRY_RESTORE_TGT_V9))
    s.emit(0x3F)
    return s.finish()


def _bs_oneshot_acc() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_ONESHOT_PREP_V9)
        + bytes([0x01]) + u32(BS_MISS_AFTER_PP) + bytes([0x00, 0x00])
        + bytes([0x09, 0x0A])
        + callasm(ENTRY_ONESHOT_APPLY_V9)
    )


def _bs_oneshot_noacc() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_ONESHOT_PREP_V9)
        + bytes([0x09, 0x0A])
        + callasm(ENTRY_ONESHOT_APPLY_V9)
    )


def _bs_multi_common(base_off: int, with_acc: bool) -> bytes:
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x02, 0x03)
    s.data.extend(callasm(ENTRY_MULTI_PREP_V9))
    if with_acc:
        s.emit(0x01)
        s.ptr(BS_MISS_AFTER_PP)
        s.data.extend(u16(0))
    s.emit(0x09, 0x0A)
    s.data.extend(callasm(ENTRY_MULTI_PRE_FX_V9))
    s.ptr("hp_cost")
    s.ptr("cure_self")
    s.ptr("stat_loop")

    s.label("hp_cost")
    s.emit(0x35)
    s.ptr(HIT_MARKER_ADDR)
    s.data.extend(u32(0x00000100))
    s.emit(0x0B, 0x01, 0x0C, 0x01)
    s.goto("stat_loop")

    s.label("cure_self")
    s.emit(0x3A, 0x98, 0x01, 0x10)
    s.data.extend(u16(STR_STATUS_CURED_SCR))
    s.emit(0x12, 0x40, 0x00)

    s.label("stat_loop")
    s.data.extend(callasm(ENTRY_MULTI_NEXT_STAT_V9))
    s.ptr("do_up")
    s.ptr("do_down")
    s.ptr("post_fx")

    s.label("do_up")
    s.emit(0x89, 0x01)
    s.ptr("stat_loop")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr("stat_loop")
    s.emit(0x47, 0x45, 0x00, 0x01)
    s.ptr(0x02021818)
    s.emit(0x13)
    s.ptr(0x082085A0)
    s.emit(0x12, 0x40, 0x00)
    s.goto("stat_loop")

    s.label("do_down")
    s.emit(0x89, 0x01)
    s.ptr("stat_loop")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr("stat_loop")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(3)
    s.ptr("stat_loop")
    s.emit(0x47, 0x45, 0x00, 0x01)
    s.ptr(0x02021818)
    s.emit(0x13)
    s.ptr(0x082085AC)
    s.emit(0x12, 0x40, 0x00)
    s.goto("stat_loop")

    s.label("post_fx")
    s.data.extend(callasm(ENTRY_MULTI_POST_FX_V9))
    return s.finish()


def _bs_strength_sap(base_off: int) -> bytes:
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x02, 0x03)
    s.data.extend(callasm(ENTRY_STRENGTH_SAP_PREP_V9))
    s.emit(0x01)
    s.ptr(BS_MISS_AFTER_PP)
    s.data.extend(u16(0))
    s.emit(0x89, 0x01)
    s.ptr(BS_MOVE_END)
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr(BS_BUT_IT_FAILED)
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(3)
    s.ptr(BS_MOVE_END)
    s.emit(0x09, 0x0A)
    s.emit(0x47, 0x45, 0x00, 0x01)
    s.ptr(0x02021818)
    s.emit(0x13)
    s.ptr(0x082085AC)
    s.emit(0x12, 0x40, 0x00)
    s.data.extend(callasm(ENTRY_STRENGTH_SAP_HEAL_V9))
    s.ptr("do_heal")
    s.ptr("do_ooze")

    s.label("do_heal")
    s.emit(0x35)
    s.ptr(HIT_MARKER_ADDR)
    s.data.extend(u32(0x00000100))
    s.emit(0x0B, 0x01, 0x0C, 0x01, 0x10)
    s.data.extend(u16(STR_STRENGTH_SAP_HEAL))
    s.emit(0x12, 0x40, 0x00)
    s.goto(BS_MOVE_END)

    s.label("do_ooze")
    s.emit(0x35)
    s.ptr(HIT_MARKER_ADDR)
    s.data.extend(u32(0x00000100))
    s.emit(0x0B, 0x01, 0x0C, 0x01, 0x10)
    s.data.extend(u16(STR_LIQUID_OOZE_HURT))
    s.emit(0x12, 0x40, 0x00)
    s.emit(0x19, 0x01, 0x00)
    s.data.extend(u32(0))
    s.goto(BS_MOVE_END)
    return s.finish()


def _bs_wish_sacrifice() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + bytes([0x4F, 0x81]) + u32(BS_BUT_IT_FAILED)
        + bytes([0x09, 0x0A])
        + callasm(ENTRY_WISH_SAC_PREP_V9)
        + bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x01, 0x0C, 0x01])
        + bytes([0x19, 0x01, 0x00]) + u32(0)
        + bytes([0x28]) + u32(BS_MOVE_END)
    )


def _bs_shed_tail(base_off: int) -> bytes:
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x02, 0x03)
    s.emit(0x4F, 0x81)
    s.ptr(BS_BUT_IT_FAILED)
    s.data.extend(callasm(ENTRY_SHED_TAIL_PREP_V9))
    s.emit(0x09, 0x0A)
    s.emit(0x35)
    s.ptr(HIT_MARKER_ADDR)
    s.data.extend(u32(0x00000100))
    s.emit(0x0B, 0x01, 0x0C, 0x01, 0x10)
    s.data.extend(u16(STR_SHED_TAIL_CREATED))
    s.emit(0x12, 0x40, 0x00)
    s.setbyte(0x0202181C, 0)
    s.emit(0x49, 0x02, 0x10)
    s.data.extend(callasm(0x090C0061))
    s.emit(0x4F, 0x81)
    s.ptr(BS_FINISH_MOVEEND)
    s.emit(0x50, 0x01)
    s.ptr(BS_FINISH_MOVEEND)
    s.emit(0xE2, 0x01, 0x3A)
    s.emit(0x51, 0x01, 0x02)
    s.emit(0x58, 0x01)
    s.emit(0x4C, 0x01, 0x4D, 0x01)
    s.data.extend(callasm(ENTRY_SHED_TAIL_INSTALL_V9))
    s.emit(0x73, 0x01)
    s.emit(0x10, 0x03, 0x00)
    s.emit(0x4E, 0x01, 0x01, 0x3A)
    s.emit(0x52, 0x01)
    s.goto(BS_FINISH_MOVEEND)
    return s.finish()


def _bs_cleanse(base_off: int) -> bytes:
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x02, 0x03)
    s.data.extend(callasm(ENTRY_CLEANSE_PREP_V9))
    s.ptr("anim_step")
    s.emit(0x01)
    s.ptr(BS_MISS_AFTER_PP)
    s.data.extend(u16(0))
    s.label("anim_step")
    s.emit(0x09, 0x0A)
    s.data.extend(callasm(ENTRY_CLEANSE_STEP_V9))
    return s.finish()


def _bs_dark_void(base_off: int) -> bytes:
    from scripts import efeitos_gen9 as effects

    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x02, 0x03)
    s.setbyte(0x0203FCBC, 0)  # V9_STATE->multi_step = 0 (offset 0x1C verificado por _Static_assert)
    s.label("next_foe")
    s.data.extend(callasm(ENTRY_DARK_VOID_STEP_V9))
    s.ptr("try_foe")
    s.label("try_foe")
    s.emit(0x01)
    s.ptr("miss_foe")
    s.data.extend(u16(0))
    s.emit(0x09, 0x0A)
    s.setbyte(MOVE_EFFECT_BYTE_ADDR, 0x01)
    s.emit(0x16)
    s.goto("next_foe")
    s.label("miss_foe")
    s.emit(0x39, 0x20, 0x00, 0x0F, 0x12, 0x40, 0x00)
    s.goto("next_foe")
    return s.finish()


def _bs_copycat() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + bytes([0x39, 0x20, 0x00, 0x09, 0x0A])
        + bytes([0x2E]) + u32(0x02021820) + bytes([0x00])
        + bytes([0x2E]) + u32(0x02021821) + bytes([0x00])
        + callasm(ENTRY_TURN_CTRL_EXEC_V9)
    )


def _bs_final_gambit() -> bytes:
    return (
        bytes([0x00])
        + bytes([0x01]) + u32(BS_MISS_NO_PP) + bytes([0x00, 0x00])
        + bytes([0x02, 0x03])
        + callasm(ENTRY_FINAL_GAMBIT_PREP_V9)
        + bytes([0x09, 0x0A])
        + bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x01, 0x0C, 0x01])
        + callasm(ENTRY_FINAL_GAMBIT_DMG_V9)
        + bytes([0x5C, 0x00, 0x3A, 0x0B, 0x00, 0x0C, 0x00])
        + bytes([0x19, 0x00, 0x00]) + u32(0)
        + bytes([0x19, 0x01, 0x00]) + u32(0)
        + bytes([0x28]) + u32(BS_MOVE_END)
    )


def _bs_natural_gift() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_NATURAL_GIFT_PREP_V9)
        + bytes([0x3A])
        + bytes([0x01]) + u32(BS_MISS_AFTER_PP) + bytes([0x00, 0x00])
        + bytes([0x28]) + u32(BS_HIT_CALC_START)
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
        raise PatchError("A ROM de entrada não corresponde ao motor_v8 esperado")

    inputs = _load_verified_inputs()
    payload = inputs[ROOT / "patches/motor_v9/payload.bin"]

    out = bytearray(source)
    _assert_free(out, SCRIPTS_V9, SCRIPTS_V9_END, "SCRIPTS_V9")
    _assert_free(out, STRINGS_TABLE_V9, STRINGS_TABLE_V9_END, "STRINGS_TABLE_V9")
    _assert_free(out, STRINGS_TEXT_V9, STRINGS_TEXT_V9_END, "STRINGS_TEXT_V9")
    _assert_free(out, CMD_TABLE_V9, CMD_TABLE_V9_END, "CMD_TABLE_V9")
    _assert_free(out, PAYLOAD_V9, PAYLOAD_V9_END, "PAYLOAD_V9")

    # 1. Reloca gBattleStringsTable (+37 mensagens PT-BR sobre motor_v8).
    str_cursor = STRINGS_TEXT_V9
    new_str_ptrs: list[int] = []
    for idx, (sid, text) in enumerate(NEW_BATTLE_STRINGS_V9):
        expected_sid = 12 + V8_BATTLE_STRINGS_COUNT + idx
        if sid != expected_sid:
            raise PatchError(f"SID fora de ordem: 0x{sid:04X} != 0x{expected_sid:04X}")
        encoded = v8.encode_ptbr(text)
        if str_cursor + len(encoded) > STRINGS_TEXT_V9_END:
            raise PatchError("Estouro em STRINGS_TEXT_V9")
        out[str_cursor : str_cursor + len(encoded)] = encoded
        new_str_ptrs.append(ROM + str_cursor)
        str_cursor += len(encoded)

    v8_str_tbl = bytes(source[v8.STRINGS_TABLE_V8 : v8.STRINGS_TABLE_V8 + V8_BATTLE_STRINGS_COUNT * 4])
    reloc_str_tbl = v8_str_tbl + b"".join(u32(p) for p in new_str_ptrs)
    if len(reloc_str_tbl) > STRINGS_TABLE_V9_END - STRINGS_TABLE_V9:
        raise PatchError("Estouro em STRINGS_TABLE_V9")
    out[STRINGS_TABLE_V9 : STRINGS_TABLE_V9 + len(reloc_str_tbl)] = reloc_str_tbl

    for ref in BATTLE_STRINGS_TABLE_REFS:
        if struct.unpack_from("<I", source, ref)[0] != ROM + v8.STRINGS_TABLE_V8:
            raise PatchError(f"Referência inesperada a gBattleStringsTable em 0x{ref:X}")
        struct.pack_into("<I", out, ref, ROM + STRINGS_TABLE_V9)

    if bytes(source[BATTLE_STRING_CAP_SITE : BATTLE_STRING_CAP_SITE + 4]) != bytes([0xD4, 0x23, 0x5B, 0x00]):
        raise PatchError("Limite inesperado em BufferStringBattle")
    out[BATTLE_STRING_CAP_SITE : BATTLE_STRING_CAP_SITE + 2] = bytes([0xF0, 0x23])  # 0xF0 << 1 = 480 > 456

    # 2. Instala sub-scripts fixos e efeitos 243..254 em SCRIPTS_V9.
    _write_fixed_sub(
        out, SUB_ENDTURN_AQUA_RING, 32,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x0A, 0x0C, 0x0A, 0x10]) + u16(STR_AQUA_RING_HEAL) + bytes([0x12, 0x40, 0x00, 0x3F]),
        "SUB_ENDTURN_AQUA_RING",
    )
    _write_fixed_sub(out, SUB_ENDTURN_OCTOLOCK, 128, _sub_endturn_octolock(SUB_ENDTURN_OCTOLOCK), "SUB_ENDTURN_OCTOLOCK")
    _write_fixed_sub(
        out, SUB_ENDTURN_MROOM, 16,
        bytes([0x10]) + u16(STR_MAGIC_ROOM_END) + bytes([0x12, 0x40, 0x00, 0x3F]),
        "SUB_ENDTURN_MROOM",
    )
    _write_fixed_sub(
        out, SUB_SWITCHIN_HWISH, 32,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x0A, 0x0C, 0x0A, 0x98, 0x0A, 0x10]) + u16(STR_HWISH_CAME_TRUE)
        + bytes([0x12, 0x40, 0x00, 0x3C]),
        "SUB_SWITCHIN_HWISH",
    )
    _write_fixed_sub(
        out, SUB_SWITCHIN_LDANCE, 32,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x0A, 0x0C, 0x0A, 0x98, 0x0A, 0x10]) + u16(STR_LDANCE_CLOAKED)
        + bytes([0x12, 0x40, 0x00, 0x3C]),
        "SUB_SWITCHIN_LDANCE",
    )
    _write_fixed_sub(
        out, SUB_WORRY_SEED_WAKE, 32,
        bytes([0x3A, 0x98, 0x00, 0x10]) + u16(STR_WORRY_SEED_SET)
        + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_WORRY_SEED_WAKE",
    )
    _write_fixed_sub(
        out, SUB_OCTOLOCK_SET, 32,
        bytes([0x2E]) + u32(MOVE_EFFECT_BYTE_ADDR) + bytes([0x20, 0x16, 0x10])
        + u16(STR_OCTOLOCK_SET) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_OCTOLOCK_SET",
    )
    _write_fixed_sub(
        out, SUB_TOXIC_THREAD_PSN, 32,
        bytes([0x2E]) + u32(MOVE_EFFECT_BYTE_ADDR) + bytes([0x02, 0x16, 0x28]) + u32(BS_MOVE_END),
        "SUB_TOXIC_THREAD_PSN",
    )
    _write_fixed_sub(
        out, SUB_CLEANSE_CURE_STEP, 32,
        bytes([0x3A, 0x98, 0x0A, 0x10]) + u16(STR_STATUS_CURED_SCR)
        + bytes([0x12, 0x40, 0x00]) + callasm(ENTRY_CLEANSE_STEP_V9),
        "SUB_CLEANSE_CURE_STEP",
    )
    _write_fixed_sub(
        out, SUB_CLEANSE_HEAL_STEP, 32,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x0A, 0x0C, 0x0A, 0x10]) + u16(v8.STR_GRASSY_HEAL)
        + bytes([0x12, 0x40, 0x00]) + callasm(ENTRY_CLEANSE_STEP_V9),
        "SUB_CLEANSE_HEAL_STEP",
    )
    _write_fixed_sub(
        out, SUB_PSHIFT_INFLICT, 32,
        bytes([0x3A, 0x98, 0x00, 0x10]) + u16(STR_PSHIFT_TRANSFERRED)
        + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_PSHIFT_INFLICT",
    )
    _write_fixed_sub(
        out, SUB_PSHIFT_SELF_CURE, 32,
        bytes([0x3A, 0x98, 0x01]) + callasm(ENTRY_CLEANSE_STEP_V9),
        "SUB_PSHIFT_SELF_CURE",
    )
    for idx, sid in enumerate(MSG_TAIL_ORDER_V9):
        _write_fixed_sub(
            out, SUB_MSG_TAILS + 12 * idx, 12,
            bytes([0x10]) + u16(sid) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END) + bytes([0x00]),
            f"SUB_MSG_TAIL_{idx}",
        )

    sc_cursor = DYNAMIC_SCRIPTS_START
    effect_builders = (
        (EFF_V9_ONESHOT_ACC, lambda at: _bs_oneshot_acc()),
        (EFF_V9_ONESHOT_NOACC, lambda at: _bs_oneshot_noacc()),
        (EFF_V9_MULTI_ACC, lambda at: _bs_multi_common(at, True)),
        (EFF_V9_MULTI_NOACC, lambda at: _bs_multi_common(at, False)),
        (EFF_V9_STRENGTH_SAP, lambda at: _bs_strength_sap(at)),
        (EFF_V9_WISH_SACRIFICE, lambda at: _bs_wish_sacrifice()),
        (EFF_V9_SHED_TAIL, lambda at: _bs_shed_tail(at)),
        (EFF_V9_CLEANSE, lambda at: _bs_cleanse(at)),
        (EFF_V9_DARK_VOID, lambda at: _bs_dark_void(at)),
        (EFF_V9_COPYCAT, lambda at: _bs_copycat()),
        (EFF_V9_FINAL_GAMBIT, lambda at: _bs_final_gambit()),
        (EFF_V9_NATURAL_GIFT, lambda at: _bs_natural_gift()),
    )
    for eff_id, builder in effect_builders:
        cur_ptr = struct.unpack_from("<I", source, complement.SCRIPT_TABLE + eff_id * 4)[0]
        if cur_ptr != 0x081853A8:
            raise PatchError(f"Slot de efeito {eff_id} já ocupado: 0x{cur_ptr:08X}")
        blob = builder(sc_cursor)
        if sc_cursor + len(blob) > SCRIPTS_V9_END:
            raise PatchError(f"Estouro em SCRIPTS_V9 no efeito {eff_id}")
        out[sc_cursor : sc_cursor + len(blob)] = blob
        struct.pack_into("<I", out, complement.SCRIPT_TABLE + eff_id * 4, ROM + sc_cursor)
        sc_cursor = (sc_cursor + len(blob) + 3) & ~3

    # 3. Instala payload Thumb em 0x090C9000, tabela de comandos em 0x090C8800 e hooks.
    if len(payload) > PAYLOAD_V9_END - PAYLOAD_V9:
        raise PatchError("Payload do motor_v9 excede a reserva")
    out[PAYLOAD_V9 : PAYLOAD_V9 + len(payload)] = payload

    cmd_tbl = bytearray(source[v8.CMD_TABLE_V8 : v8.CMD_TABLE_V8 + 256 * 4])
    overrides = {
        0x00: ENTRY_ATTACKCANCELER_V9,
        0x04: ENTRY_CRITCALC_V9,
        0x05: ENTRY_DAMAGE_V9,
        0x06: ENTRY_TYPECALC_V9,
        0x52: ENTRY_SWITCHINEFFECTS_V9,
    }
    for opc, target in overrides.items():
        struct.pack_into("<I", cmd_tbl, opc * 4, target)
    out[CMD_TABLE_V9 : CMD_TABLE_V9 + len(cmd_tbl)] = cmd_tbl

    for site in v6.CMD_TABLE_PTRS:
        if struct.unpack_from("<I", source, site)[0] != ROM + v8.CMD_TABLE_V8:
            raise PatchError(f"Ponteiro inesperado de CMD_TABLE em 0x{site:X}")
        struct.pack_into("<I", out, site, ROM + CMD_TABLE_V9)

    hooks = (
        (BATTLE_INIT_LIT, v8.ENTRY_BATTLE_INIT_V8, ENTRY_BATTLE_INIT_V9),
        (TURN_START_LIT, v8.ENTRY_TURN_START_V8, ENTRY_TURN_START_V9),
        (ENDTURN_CONT_LIT, v8.ENTRY_ENDTURN_V8, ENTRY_ENDTURN_V9),
    )
    for lit_off, expected_old, new_val in hooks:
        if struct.unpack_from("<I", source, lit_off)[0] != expected_old:
            raise PatchError(f"Literal de hook inesperado em 0x{lit_off:X}")
        struct.pack_into("<I", out, lit_off, new_val)

    if bytes(source[GET_HOLD_EFFECT_SITE : GET_HOLD_EFFECT_SITE + 8]) != GET_HOLD_EFFECT_ORIG:
        raise PatchError("Prólogo inesperado em GetHoldEffect (0x080C725C)")
    out[GET_HOLD_EFFECT_SITE : GET_HOLD_EFFECT_SITE + 8] = (
        bytes.fromhex("00 4b 18 47") + u32(ENTRY_GET_HOLD_EFFECT_V9)
    )

    # 4. Atualiza MOVE_TABLE dos 51 golpes restaurados.
    field_offsets = {
        "eff": 0, "pwr": 1, "typ": 2, "acc": 3, "pp": 4,
        "chance": 5, "tgt": 6, "prio": 7, "flags": 8,
    }
    for mid, changes in MOVE_UPDATES_V9.items():
        base = complement.MOVE + 12 * mid
        for key, val in changes.items():
            out[base + field_offsets[key]] = val & 0xFF

    # 5. Recompila learnsets por nível (+378 entradas, preservando 100% das 14.627 do motor_v8).
    prior_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/learnsets_motor_v8.csv"].decode("utf-8"))))
    cur_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/learnsets_motor_v9.csv"].decode("utf-8"))))
    lv_key = lambda r: (int(r["species"]), int(r["level"]), int(r["internal_move"]), int(r["api_move"]))
    if len(cur_lv) != 15005 or not set(map(lv_key, prior_lv)).issubset(set(map(lv_key, cur_lv))):
        raise PatchError("Learnsets anteriores do motor_v8 não foram integralmente preservados")
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
    if OUTPUT_SHA256 and digest(result) != OUTPUT_SHA256:
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
        print("Motor parcial v9: +51 golpes não-TM (+378 learnsets = 15.005) e 229/229 TMs SV preservadas.")
    except (OSError, ValueError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
