#!/usr/bin/env python3
"""Aplica o motor_v9 sobre a ROM motor_v8 identificada por SHA-256.

Escopo estrito e auditável sobre o motor_v8:
  1. Instala estado efêmero de batalha do motor_v9 em 0x0203FCA0..0x0203FD1F
     (sem tocar estruturas persistentes ou saves) e encadeia início de batalha
     (0x08051D74), início de turno (0x0805439C) e fim de turno (0x08053208),
     além de relocar gBattleScriptingCommandsTable em 0x090C8800 e
     gBattleStringsTable em 0x090C7000 (+34 mensagens PT-BR: 0x01A4..0x01C5).
  2. Implementa os 13 slots livres remanescentes da tabela de efeitos (243..255)
     cobrindo 49 golpes de subida de nível antes omitidos:
       - Família 1 (Tipos e vulnerabilidade): Soak (486), Magic Powder (675),
         Reflect Type (512), Trick-or-Treat (563), Forest's Curse (567) e Tar
         Shot (674).
       - Família 2 (Habilidades nativas Gen 3 e eletrificação): Gastro Acid
         (380), Worry Seed (388), Entrainment (493), Doodle (759) e Electrify
         (578).
       - Família 3 (Trocas, divisões, inversão e sinergias de atributos):
         Power Trick (379), Speed Swap (638), Power Split (470), Guard Split
         (469), Power Swap (384), Guard Swap (385), Heart Swap (391),
         Topsy-Turvy (572), Acupressure (367), Decorate (684), Spicy Extract
         (750), Venom Drench (595), Toxic Thread (627), Rototiller (559),
         Flower Shield (575), Magnetic Flux (598), Gear Up (629) e Strength
         Sap (623).
       - Família 4 (Sacrifício de HP, clérigo, cura contínua, crítico e pivot):
         Final Gambit (514), Fillet Away (760), Clangorous Soul (682), No
         Retreat (673), Shed Tail (770), Aqua Ring (392), Laser Focus (628),
         Psycho Shift (375), Purify (640), Take Heart (743), Jungle Healing
         (710), Lunar Blessing (742), Healing Wish (361), Lunar Dance (460) e
         Dark Void (463, restrito a Darkrai #491).
       - Família 5 (Cópia, controle de ordem de ação e prisão): Copycat (383),
         After You (494), Quash (510), Octolock (678) e Fairy Lock (583).
  3. Recompila as tabelas de subida de nível com +368 entradas antes omitidas
     (14.627 -> 14.995 linhas, preservando 100% das anteriores e das 229/229
     TMs de Scarlet/Violet), totalizando 695/729 (95,3%) entradas históricas
     restauradas; documenta os 8 golpes finais (34 entradas = 4,7%) mantidos
     fora de escopo.

Não altera saves pessoais; grava sempre arquivo novo.
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
from scripts import efeitos_gen9 as effects
from scripts import golpes_gen9 as level
from scripts import motor_v6 as v6
from scripts import motor_v8 as v8
from scripts.treino_ev import write_new_file

BASE_SHA256 = v8.OUTPUT_SHA256
OUTPUT_SHA256 = "ad911117b4e1072f614ae51d1d6b1b99643562d2b9cdf7701fbcd04baab3a297"

INPUTS = {
    ROOT / "patches/motor_v9/payload.bin": "71283bda3341ad5b55e7cd0b9fecf40bf53e49a26737ed20d2a05484d9553f24",
    ROOT / "data/learnsets_motor_v9.csv": "a9fee458d097a83a6dde27af745bb3efc3bb603b84208b960c1c9dcb424ce4d8",
    ROOT / "data/learnsets_motor_v8.csv": "19abc5661267157524b9dcdc9ad769cdf12a20f9f44a3be63f134ae2ec9120f7",
}

ROM = 0x08000000
MOVE_COUNT = v8.MOVE_COUNT

# Hooks encadeados sobre motor_v8
BATTLE_INIT_LIT = v8.BATTLE_INIT_LIT
TURN_START_LIT = v8.TURN_START_LIT
ENDTURN_CONT_LIT = v8.ENDTURN_CONT_LIT

# Tabela de strings de batalha relocada sobre a do motor_v8 (408 -> 442 ponteiros: 0x000C..0x01C5)
V8_BATTLE_STRINGS_COUNT = 408
BATTLE_STRING_CAP_SITE = v8.BATTLE_STRING_CAP_SITE
BATTLE_STRINGS_TABLE_REFS = v8.BATTLE_STRINGS_TABLE_REFS

# Regioes exclusivas do motor_v9 em espaco livre 0xFF (apos 0x10C6000)
SCRIPTS_V9 = 0x10C6000
SCRIPTS_V9_END = 0x10C7000
STRINGS_TABLE_V9 = 0x10C7000
STRINGS_TABLE_V9_END = 0x10C7800
STRINGS_TEXT_V9 = 0x10C7800
STRINGS_TEXT_V9_END = 0x10C8800
CMD_TABLE_V9 = 0x10C8800
CMD_TABLE_V9_END = 0x10C8C00
PAYLOAD_V9 = 0x10C9000
PAYLOAD_V9_END = 0x10CD000

# Sub-scripts em enderecos fixos dentro de SCRIPTS_V9 (sincronizados com motor_v9.c)
SUB_ENDTURN_AQUA_RING = 0x10C6000
SUB_ENDTURN_OCTOLOCK = 0x10C6020
SUB_STAT_QUEUE = 0x10C6080
SUB_HEALING_WISH_IN = 0x10C6100
SUB_LUNAR_DANCE_IN = 0x10C6140
SUB_WORRY_SEED_WOKE = 0x10C6180
SUB_CANT_ESCAPE_END = 0x10C61A0
SUB_LIQUID_OOZE_TAIL = 0x10C61C0
SUB_SLEEP_EFF = 0x10C61E0
SUB_STR_TAILS = 0x10C6200          # 34 slots de 12 B (0x10C6200..0x10C6397)
DYNAMIC_SCRIPTS_START_V9 = 0x10C63A0

# Vetores Thumb em patches/motor_v9/entry.s (base 0x090C9001 + 8*i)
PAYLOAD_V9_THUMB = ROM + PAYLOAD_V9 + 1
ENTRY_BATTLE_INIT_V9 = PAYLOAD_V9_THUMB + 0 * 8
ENTRY_TURN_START_V9 = PAYLOAD_V9_THUMB + 1 * 8
ENTRY_ENDTURN_V9 = PAYLOAD_V9_THUMB + 2 * 8
ENTRY_ATTACKCANCELER_V9 = PAYLOAD_V9_THUMB + 3 * 8
ENTRY_CRITCALC_V9 = PAYLOAD_V9_THUMB + 4 * 8
ENTRY_TYPECALC_V9 = PAYLOAD_V9_THUMB + 5 * 8
ENTRY_SWITCHINEFFECTS_V9 = PAYLOAD_V9_THUMB + 6 * 8
ENTRY_STAT_QUEUE_STEP_V9 = PAYLOAD_V9_THUMB + 7 * 8
ENTRY_STAT_QUEUE_AFTER_V9 = PAYLOAD_V9_THUMB + 8 * 8
ENTRY_OCTOLOCK_RESTORE_V9 = PAYLOAD_V9_THUMB + 9 * 8
ENTRY_FINAL_GAMBIT_CALC_V9 = PAYLOAD_V9_THUMB + 10 * 8
ENTRY_FINAL_GAMBIT_SELF_KO_V9 = PAYLOAD_V9_THUMB + 11 * 8
ENTRY_TYPE_ABILITY_ACC_V9 = PAYLOAD_V9_THUMB + 12 * 8
ENTRY_TYPE_ABILITY_PREP_V9 = PAYLOAD_V9_THUMB + 13 * 8
ENTRY_TYPE_ABILITY_APPLY_V9 = PAYLOAD_V9_THUMB + 14 * 8
ENTRY_RAW_SWAP_APPLY_V9 = PAYLOAD_V9_THUMB + 15 * 8
ENTRY_TARGET_BUFF_PREP_V9 = PAYLOAD_V9_THUMB + 16 * 8
ENTRY_FIELD_TEAM_PREP_V9 = PAYLOAD_V9_THUMB + 17 * 8
ENTRY_SACRIFICE_PREP_V9 = PAYLOAD_V9_THUMB + 18 * 8
ENTRY_SELF_VOLATILE_APPLY_V9 = PAYLOAD_V9_THUMB + 19 * 8
ENTRY_STRENGTH_SAP_PREP_V9 = PAYLOAD_V9_THUMB + 20 * 8
ENTRY_STRENGTH_SAP_HEAL_V9 = PAYLOAD_V9_THUMB + 21 * 8
ENTRY_CLERIC_PREP_V9 = PAYLOAD_V9_THUMB + 22 * 8
ENTRY_CLERIC_STEP_V9 = PAYLOAD_V9_THUMB + 23 * 8
ENTRY_DARK_VOID_STEP_V9 = PAYLOAD_V9_THUMB + 24 * 8
ENTRY_HEALING_WISH_PREP_V9 = PAYLOAD_V9_THUMB + 25 * 8
ENTRY_HWISH_CURE_STATUS_V9 = PAYLOAD_V9_THUMB + 26 * 8
ENTRY_HWISH_RESTORE_PP_V9 = PAYLOAD_V9_THUMB + 27 * 8
ENTRY_HWISH_PREP_HP_V9 = PAYLOAD_V9_THUMB + 28 * 8
ENTRY_SHED_TAIL_PREP_V9 = PAYLOAD_V9_THUMB + 29 * 8
ENTRY_SHED_TAIL_POST_SWITCH_V9 = PAYLOAD_V9_THUMB + 30 * 8
ENTRY_TURN_COPY_CTRL_V9 = PAYLOAD_V9_THUMB + 31 * 8

BS_MOVE_END = 0x081853F6
BS_PRINT_MOVE_MISSED = 0x08185406
BS_BUT_IT_FAILED = 0x0818689A
STAT_BUFF_ADDR = 0x02021822
HIT_MARKER_ADDR = 0x0202160C

# 13 slots livres finais da tabela de efeitos (243..255)
EFF_FINAL_GAMBIT = 243
EFF_TYPE_ABILITY = 244
EFF_RAW_STAGE_SWAP = 245
EFF_TARGET_BUFF_TRAP = 246
EFF_FIELD_TEAM_V9 = 247
EFF_SELF_SACRIFICE_BOOST = 248
EFF_SELF_VOLATILE = 249
EFF_STRENGTH_SAP = 250
EFF_CLERIC_STATUS = 251
EFF_DARK_VOID = 252
EFF_HEALING_WISH = 253
EFF_SHED_TAIL = 254
EFF_TURN_COPY_CTRL = 255

# 34 novas strings PT-BR (0x01A4..0x01C5), sincronizadas 1-para-1 com TAIL_* em motor_v9.c
STR_SOAK = 0x01A4
STR_MAGIC_POWDER = 0x01A5
STR_REFLECT_TYPE = 0x01A6
STR_TRICK_OR_TREAT = 0x01A7
STR_FORESTS_CURSE = 0x01A8
STR_GASTRO_ACID = 0x01A9
STR_WORRY_SEED = 0x01AA
STR_ENTRAINMENT = 0x01AB
STR_DOODLE = 0x01AC
STR_ELECTRIFY = 0x01AD
STR_POWER_TRICK = 0x01AE
STR_SPEED_SWAP = 0x01AF
STR_POWER_SPLIT = 0x01B0
STR_GUARD_SPLIT = 0x01B1
STR_POWER_SWAP = 0x01B2
STR_GUARD_SWAP = 0x01B3
STR_HEART_SWAP = 0x01B4
STR_TOPSY_TURVY = 0x01B5
STR_TAR_SHOT = 0x01B6
STR_FAIRY_LOCK = 0x01B7
STR_AQUA_RING_SET = 0x01B8
STR_AQUA_RING_HEAL = 0x01B9
STR_LASER_FOCUS = 0x01BA
STR_ATK_HEALED = 0x01BB
STR_SCR_HEALED = 0x01BC
STR_SCR_CURED = 0x01BD
STR_DARK_VOID_BLOCK = 0x01BE
STR_HEALING_WISH_CAME = 0x01BF
STR_LUNAR_DANCE_CAME = 0x01C0
STR_AFTER_YOU = 0x01C1
STR_QUASH = 0x01C2
STR_LIQUID_OOZE = 0x01C3
STR_TGT_WOKE_UP = 0x01C4
STR_ATK_CANT_ESCAPE = 0x01C5

NEW_BATTLE_STRINGS_V9: tuple[tuple[int, str], ...] = (
    (STR_SOAK, "{TGT} virou do\ntipo Água!"),
    (STR_MAGIC_POWDER, "{TGT} virou do\ntipo Psíquico!"),
    (STR_REFLECT_TYPE, "{ATK} copiou o\ntipo de {TGT}!"),
    (STR_TRICK_OR_TREAT, "O tipo Fantasma foi\nadicionado a {TGT}!"),
    (STR_FORESTS_CURSE, "O tipo Planta foi\nadicionado a {TGT}!"),
    (STR_GASTRO_ACID, "A habilidade de {TGT}\nfoi suprimida!"),
    (STR_WORRY_SEED, "A habilidade de {TGT}\nvirou Insônia!"),
    (STR_ENTRAINMENT, "{TGT} recebeu a\nhabilidade de {ATK}!"),
    (STR_DOODLE, "{ATK} copiou a\nhabilidade de {TGT}!"),
    (STR_ELECTRIFY, "Os golpes de {TGT}\nforam eletrificados!"),
    (STR_POWER_TRICK, "{ATK} trocou seu\nAtaque e Defesa!"),
    (STR_SPEED_SWAP, "{ATK} trocou a\nVelocidade com o alvo!"),
    (STR_POWER_SPLIT, "{ATK} dividiu sua\nforça com o alvo!"),
    (STR_GUARD_SPLIT, "{ATK} dividiu sua\ndefesa com o alvo!"),
    (STR_POWER_SWAP, "{ATK} trocou mudanças\nde Ataque com o alvo!"),
    (STR_GUARD_SWAP, "{ATK} trocou mudanças\nde Defesa com o alvo!"),
    (STR_HEART_SWAP, "{ATK} trocou mudanças\nde atributos com o alvo!"),
    (STR_TOPSY_TURVY, "As mudanças de atributos de\n{TGT} foram invertidas!"),
    (STR_TAR_SHOT, "{TGT} ficou mais\nfraco contra Fogo!"),
    (STR_FAIRY_LOCK, "Ninguém poderá fugir\nno próximo turno!"),
    (STR_AQUA_RING_SET, "{ATK} cercou-se\ncom um véu de água!"),
    (STR_AQUA_RING_HEAL, "O véu de água curou\n{SCR}!"),
    (STR_LASER_FOCUS, "{ATK} concentrou\nintensamente o foco!"),
    (STR_ATK_HEALED, "O HP de {ATK}\nfoi restaurado!"),
    (STR_SCR_HEALED, "O HP de {SCR}\nfoi restaurado!"),
    (STR_SCR_CURED, "O problema de estado de\n{SCR} foi curado!"),
    (STR_DARK_VOID_BLOCK, "Mas {ATK} não\nconsegue usar o golpe!"),
    (STR_HEALING_WISH_CAME, "O desejo de cura alcançou\n{SCR}!"),
    (STR_LUNAR_DANCE_CAME, "{SCR} foi envolvido\npelo luar místico!"),
    (STR_AFTER_YOU, "{TGT} aceitou a\ngentileza!"),
    (STR_QUASH, "{ATK} atrasou a\nvez de {TGT}!"),
    (STR_LIQUID_OOZE, "{ATK} sugou o\nlodo nocivo!"),
    (STR_TGT_WOKE_UP, "{TGT} acordou!"),
    (STR_ATK_CANT_ESCAPE, "{ATK} não pode mais\nescapar!"),
)

MOVE_UPDATES_V9: dict[int, dict[str, int]] = {
    # Efeito 243: Final Gambit
    514: {"eff": EFF_FINAL_GAMBIT},
    # Efeito 244: Tipos, habilidades e Electrify
    380: {"eff": EFF_TYPE_ABILITY},
    388: {"eff": EFF_TYPE_ABILITY},
    486: {"eff": EFF_TYPE_ABILITY},
    493: {"eff": EFF_TYPE_ABILITY},
    512: {"eff": EFF_TYPE_ABILITY},
    563: {"eff": EFF_TYPE_ABILITY},
    567: {"eff": EFF_TYPE_ABILITY},
    578: {"eff": EFF_TYPE_ABILITY},
    675: {"eff": EFF_TYPE_ABILITY},
    759: {"eff": EFF_TYPE_ABILITY, "acc": 100},
    # Efeito 245: Trocas, divisões e inversão de atributos
    379: {"eff": EFF_RAW_STAGE_SWAP},
    384: {"eff": EFF_RAW_STAGE_SWAP},
    385: {"eff": EFF_RAW_STAGE_SWAP},
    391: {"eff": EFF_RAW_STAGE_SWAP},
    469: {"eff": EFF_RAW_STAGE_SWAP},
    470: {"eff": EFF_RAW_STAGE_SWAP},
    572: {"eff": EFF_RAW_STAGE_SWAP},
    638: {"eff": EFF_RAW_STAGE_SWAP},
    # Efeito 246: Buffs/debuffs direcionados e Octolock
    367: {"eff": EFF_TARGET_BUFF_TRAP},
    595: {"eff": EFF_TARGET_BUFF_TRAP},
    627: {"eff": EFF_TARGET_BUFF_TRAP},
    674: {"eff": EFF_TARGET_BUFF_TRAP},
    678: {"eff": EFF_TARGET_BUFF_TRAP},
    684: {"eff": EFF_TARGET_BUFF_TRAP},
    750: {"eff": EFF_TARGET_BUFF_TRAP},
    # Efeito 247: Sinergias de campo/equipe e Fairy Lock
    559: {"eff": EFF_FIELD_TEAM_V9, "tgt": 0x10},
    575: {"eff": EFF_FIELD_TEAM_V9, "tgt": 0x10},
    583: {"eff": EFF_FIELD_TEAM_V9, "tgt": 0x10},
    598: {"eff": EFF_FIELD_TEAM_V9, "tgt": 0x10},
    629: {"eff": EFF_FIELD_TEAM_V9, "tgt": 0x10},
    # Efeito 248: Fillet Away, Clangorous Soul e No Retreat
    673: {"eff": EFF_SELF_SACRIFICE_BOOST},
    682: {"eff": EFF_SELF_SACRIFICE_BOOST, "acc": 0},
    760: {"eff": EFF_SELF_SACRIFICE_BOOST},
    # Efeito 249: Aqua Ring e Laser Focus
    392: {"eff": EFF_SELF_VOLATILE},
    628: {"eff": EFF_SELF_VOLATILE},
    # Efeito 250: Strength Sap
    623: {"eff": EFF_STRENGTH_SAP},
    # Efeito 251: Clérigo (Psycho Shift, Purify, Jungle Healing, Lunar Blessing, Take Heart)
    375: {"eff": EFF_CLERIC_STATUS},
    640: {"eff": EFF_CLERIC_STATUS},
    710: {"eff": EFF_CLERIC_STATUS},
    742: {"eff": EFF_CLERIC_STATUS},
    743: {"eff": EFF_CLERIC_STATUS, "pp": 10},
    # Efeito 252: Dark Void
    463: {"eff": EFF_DARK_VOID},
    # Efeito 253: Healing Wish e Lunar Dance
    361: {"eff": EFF_HEALING_WISH},
    460: {"eff": EFF_HEALING_WISH},
    # Efeito 254: Shed Tail
    770: {"eff": EFF_SHED_TAIL},
    # Efeito 255: Copycat, After You e Quash
    383: {"eff": EFF_TURN_COPY_CTRL, "tgt": 0x10},
    494: {"eff": EFF_TURN_COPY_CTRL},
    510: {"eff": EFF_TURN_COPY_CTRL, "acc": 100},
}


class PatchError(ValueError):
    pass


digest = v8.digest
u16 = v8.u16
u32 = v8.u32
callasm = v8.callasm
encode_ptbr = v8.encode_ptbr


def _assert_free(rom: bytearray, start: int, end: int, label: str) -> None:
    if rom[start:end] != b"\xff" * (end - start):
        raise PatchError(f"Região {label} não está limpa (0x{start:X}..0x{end:X})")


def _write_fixed_sub(rom: bytearray, off: int, max_len: int, body: bytes, name: str) -> None:
    if len(body) > max_len:
        raise PatchError(f"Sub-script {name} excedeu {max_len} B ({len(body)} B)")
    rom[off : off + len(body)] = body


def _build_sub_endturn_octolock() -> bytes:
    s = effects.BattleScript(SUB_ENDTURN_OCTOLOCK)
    for idx, stat in enumerate((2, 5)):
        s.setbyte(0x02021823, 0)
        s.setbyte(STAT_BUFF_ADDR, stat | (1 << 4) | 0x80)
        s.emit(0x89, 0x01)
        s.ptr(f"next{idx}")
        s.emit(0x29, 0x00)
        s.ptr(0x020216C5)
        s.emit(2)
        s.ptr(f"next{idx}")
        s.emit(0x48, 0x00, 1 << stat, 1)
        s.emit(0x13)
        s.ptr(0x082085AC)
        s.emit(0x12, 0x40, 0x00)
        s.label(f"next{idx}")
    s.data.extend(callasm(ENTRY_OCTOLOCK_RESTORE_V9))
    s.emit(0x3F)
    return s.finish()


def _build_sub_stat_queue() -> bytes:
    s = effects.BattleScript(SUB_STAT_QUEUE)
    s.label("loop")
    s.data.extend(callasm(ENTRY_STAT_QUEUE_STEP_V9))
    s.ptr("down_branch")
    s.ptr("done_branch")
    # Ramo de subida (STAT_CHANGER_BYTE sem 0x80)
    s.emit(0x89, 0x01)
    s.ptr("loop")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr("loop")
    s.emit(0x47, 0x45, 0x00, 0x01, 0x18, 0x18, 0x02, 0x02)
    s.emit(0x13)
    s.ptr(0x082085A0)
    s.emit(0x12, 0x40, 0x00)
    s.goto("loop")
    # Ramo de queda (STAT_CHANGER_BYTE com 0x80)
    s.label("down_branch")
    s.emit(0x89, 0x01)
    s.ptr("loop")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr("loop")
    s.emit(0x47, 0x45, 0x00, 0x01, 0x18, 0x18, 0x02, 0x02)
    s.emit(0x13)
    s.ptr(0x082085AC)
    s.emit(0x12, 0x40, 0x00)
    s.goto("loop")
    s.label("done_branch")
    s.data.extend(callasm(ENTRY_STAT_QUEUE_AFTER_V9))
    return s.finish()


def _build_sub_hwish_in(base_off: int, sid: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x10)
    s.data.extend(u16(sid))
    s.emit(0x12, 0x40, 0x00)
    s.data.extend(callasm(ENTRY_HWISH_CURE_STATUS_V9))
    s.ptr("pp_step")
    s.emit(0x98, 0x02, 0x3A)
    s.label("pp_step")
    s.data.extend(callasm(ENTRY_HWISH_RESTORE_PP_V9))
    s.ptr("hp_step")
    s.label("hp_step")
    s.data.extend(callasm(ENTRY_HWISH_PREP_HP_V9))
    s.ptr("ret_step")
    s.emit(0x0B, 0x0A, 0x0C, 0x0A)
    s.label("ret_step")
    s.emit(0x3C)
    return s.finish()


def _bs_final_gambit(source: bytes) -> bytes:
    hit_apply = source[0x1853DC:0x1853EE]
    faint_tgt = source[0x1853EF:0x1853F6]
    return (
        bytes([0x00, 0x01]) + u32(BS_PRINT_MOVE_MISSED) + bytes([0x00, 0x00])
        + bytes([0x02, 0x03])
        + callasm(ENTRY_FINAL_GAMBIT_CALC_V9)
        + bytes([0x69])
        + hit_apply
        + faint_tgt
        + callasm(ENTRY_FINAL_GAMBIT_SELF_KO_V9)
        + bytes([0x0B, 0x01, 0x0C, 0x01])
        + bytes([0x19, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        + bytes([0x28]) + u32(BS_MOVE_END)
    )


def _bs_type_ability(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00)
    s.data.extend(callasm(ENTRY_TYPE_ABILITY_ACC_V9))
    s.ptr("acc_100")
    s.emit(0x01)
    s.ptr(BS_BUT_IT_FAILED)
    s.data.extend(u16(0xFFFF))
    s.goto("after_acc")
    s.label("acc_100")
    s.emit(0x01)
    s.ptr(BS_PRINT_MOVE_MISSED)
    s.data.extend(u16(0))
    s.label("after_acc")
    s.emit(0x02, 0x03)
    s.data.extend(callasm(ENTRY_TYPE_ABILITY_PREP_V9))
    s.emit(0x09, 0x0A)
    s.data.extend(callasm(ENTRY_TYPE_ABILITY_APPLY_V9))
    return s.finish()


def _bs_raw_stage_swap(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x01)
    s.ptr(BS_BUT_IT_FAILED)
    s.data.extend(u16(0xFFFF))
    s.emit(0x02, 0x03)
    s.data.extend(callasm(ENTRY_RAW_SWAP_APPLY_V9))
    s.emit(0x00, 0x09, 0x0A)
    s.data.extend(callasm(ENTRY_RAW_SWAP_APPLY_V9))
    s.emit(0x01)
    return s.finish()


def _bs_target_buff_trap(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00)
    s.data.extend(callasm(ENTRY_TYPE_ABILITY_ACC_V9))
    s.ptr("acc_100")
    s.emit(0x01)
    s.ptr(BS_BUT_IT_FAILED)
    s.data.extend(u16(0xFFFF))
    s.goto("after_acc")
    s.label("acc_100")
    s.emit(0x01)
    s.ptr(BS_PRINT_MOVE_MISSED)
    s.data.extend(u16(0))
    s.label("after_acc")
    s.emit(0x02, 0x03)
    s.data.extend(callasm(ENTRY_TARGET_BUFF_PREP_V9))
    s.emit(0x09, 0x0A)
    s.goto(ROM + SUB_STAT_QUEUE)
    return s.finish()


def _bs_field_team_v9() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_FIELD_TEAM_PREP_V9)
        + bytes([0x09, 0x0A, 0x28]) + u32(ROM + SUB_STAT_QUEUE)
    )


def _bs_self_sacrifice_boost(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x02, 0x03)
    s.data.extend(callasm(ENTRY_SACRIFICE_PREP_V9))
    s.ptr("anim_only")
    s.emit(0x09, 0x0A)
    s.data.extend(bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100))
    s.emit(0x0B, 0x01, 0x0C, 0x01)
    s.goto(ROM + SUB_STAT_QUEUE)
    s.label("anim_only")
    s.emit(0x09, 0x0A)
    s.goto(ROM + SUB_STAT_QUEUE)
    return s.finish()


def _bs_self_volatile() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_SELF_VOLATILE_APPLY_V9) + bytes([0x00])
        + bytes([0x09, 0x0A])
        + callasm(ENTRY_SELF_VOLATILE_APPLY_V9) + bytes([0x01])
    )


def _bs_strength_sap(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x01)
    s.ptr(BS_PRINT_MOVE_MISSED)
    s.data.extend(u16(0))
    s.emit(0x02, 0x03)
    s.data.extend(callasm(ENTRY_STRENGTH_SAP_PREP_V9))
    s.emit(0x09, 0x0A)
    s.setbyte(0x02021823, 0)
    s.setbyte(STAT_BUFF_ADDR, 1 | (1 << 4) | 0x80)
    s.emit(0x89, 0x01)
    s.ptr("heal_step")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr("heal_step")
    s.emit(0x48, 0x00, 1 << 1, 1)
    s.emit(0x13)
    s.ptr(0x082085AC)
    s.emit(0x12, 0x40, 0x00)
    s.label("heal_step")
    s.data.extend(callasm(ENTRY_STRENGTH_SAP_HEAL_V9))
    s.data.extend(bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100))
    s.emit(0x0B, 0x01, 0x0C, 0x01)
    s.emit(0x10)
    s.data.extend(u16(STR_ATK_HEALED))
    s.emit(0x12, 0x40, 0x00)
    s.goto(BS_MOVE_END)
    return s.finish()


def _bs_cleric_status(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00)
    s.data.extend(callasm(ENTRY_TYPE_ABILITY_ACC_V9))
    s.ptr("acc_100")
    s.emit(0x01)
    s.ptr(BS_BUT_IT_FAILED)
    s.data.extend(u16(0xFFFF))
    s.goto("after_acc")
    s.label("acc_100")
    s.emit(0x01)
    s.ptr(BS_PRINT_MOVE_MISSED)
    s.data.extend(u16(0))
    s.label("after_acc")
    s.emit(0x02, 0x03)
    s.data.extend(callasm(ENTRY_CLERIC_PREP_V9))
    s.emit(0x09, 0x0A)
    s.label("step_loop")
    s.data.extend(callasm(ENTRY_CLERIC_STEP_V9))
    s.ptr("cure_ui")
    s.ptr("heal_hp")
    s.label("cure_ui")
    s.emit(0x98, 0x02, 0x3A)
    s.emit(0x10)
    s.data.extend(u16(STR_SCR_CURED))
    s.emit(0x12, 0x40, 0x00)
    s.goto("step_loop")
    s.label("heal_hp")
    s.data.extend(bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100))
    s.emit(0x0B, 0x0A, 0x0C, 0x0A)
    s.emit(0x10)
    s.data.extend(u16(STR_SCR_HEALED))
    s.emit(0x12, 0x40, 0x00)
    s.goto("step_loop")
    return s.finish()


def _bs_dark_void(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x02, 0x03)
    s.label("step_loop")
    s.data.extend(callasm(ENTRY_DARK_VOID_STEP_V9))
    s.ptr("anim_branch")
    s.label("anim_branch")
    s.emit(0x09, 0x0A)
    s.goto("step_loop")
    return s.finish()


def _bs_healing_wish() -> bytes:
    return (
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_HEALING_WISH_PREP_V9)
        + bytes([0x09, 0x0A])
        + bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x01, 0x0C, 0x01])
        + bytes([0x19, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        + bytes([0x28]) + u32(BS_MOVE_END)
    )


def _bs_shed_tail(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00, 0x02, 0x03)
    s.emit(0x4F, 0x81)
    s.ptr(BS_BUT_IT_FAILED)
    s.data.extend(callasm(ENTRY_SHED_TAIL_PREP_V9))
    s.ptr("already_sub")
    s.ptr("too_weak")
    s.emit(0x09, 0x0A)
    s.data.extend(bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100))
    s.emit(0x0B, 0x01, 0x0C, 0x01)
    s.emit(0x10, 0x7E, 0x00, 0x12, 0x40, 0x00)
    s.emit(0x50, 0x01)
    s.ptr(BS_MOVE_END)
    s.emit(0xE2, 0x01, 0x3A)
    s.emit(0x51, 0x01, 0x02)
    s.emit(0x58, 0x01)
    s.emit(0x4C, 0x01, 0x4D, 0x01)
    s.data.extend(callasm(ENTRY_SHED_TAIL_POST_SWITCH_V9))
    s.emit(0x73, 0x01)
    s.emit(0x10, 0x03, 0x00)
    s.emit(0x4E, 0x01, 0x01, 0x3A)
    s.emit(0x52, 0x01)
    s.goto(BS_MOVE_END)
    s.label("already_sub")
    s.emit(0x10, 0x7F, 0x00, 0x12, 0x40, 0x00)
    s.goto(BS_MOVE_END)
    s.label("too_weak")
    s.emit(0x10, 0xFB, 0x00, 0x12, 0x40, 0x00)
    s.goto(BS_MOVE_END)
    return s.finish()


def _bs_turn_copy_ctrl(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.emit(0x00)
    s.data.extend(callasm(ENTRY_TYPE_ABILITY_ACC_V9))
    s.ptr("acc_100")
    s.emit(0x01)
    s.ptr(BS_BUT_IT_FAILED)
    s.data.extend(u16(0xFFFF))
    s.goto("after_acc")
    s.label("acc_100")
    s.emit(0x01)
    s.ptr(BS_PRINT_MOVE_MISSED)
    s.data.extend(u16(0))
    s.label("after_acc")
    s.emit(0x02, 0x03)
    s.data.extend(callasm(ENTRY_TURN_COPY_CTRL_V9))
    s.emit(0x00, 0x09, 0x0A)
    s.data.extend(callasm(ENTRY_TURN_COPY_CTRL_V9))
    s.emit(0x01)
    return s.finish()


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

    # 1. Reloca gBattleStringsTable sobre a do motor_v8 (+34 strings PT-BR: 0x01A4..0x01C5).
    str_cursor = STRINGS_TEXT_V9
    new_str_ptrs: list[int] = []
    for idx, (sid, text) in enumerate(NEW_BATTLE_STRINGS_V9):
        expected_sid = 12 + V8_BATTLE_STRINGS_COUNT + idx
        if sid != expected_sid:
            raise PatchError(f"SID fora de ordem: 0x{sid:04X} != 0x{expected_sid:04X}")
        encoded = encode_ptbr(text)
        if str_cursor + len(encoded) > STRINGS_TEXT_V9_END:
            raise PatchError("Estouro em STRINGS_TEXT_V9")
        out[str_cursor : str_cursor + len(encoded)] = encoded
        new_str_ptrs.append(ROM + str_cursor)
        str_cursor += len(encoded)

    v8_str_tbl = bytes(out[v8.STRINGS_TABLE_V8 : v8.STRINGS_TABLE_V8 + V8_BATTLE_STRINGS_COUNT * 4])
    reloc_str_tbl = v8_str_tbl + b"".join(u32(p) for p in new_str_ptrs)
    out[STRINGS_TABLE_V9 : STRINGS_TABLE_V9 + len(reloc_str_tbl)] = reloc_str_tbl

    for ref in BATTLE_STRINGS_TABLE_REFS:
        if struct.unpack_from("<I", out, ref)[0] != ROM + v8.STRINGS_TABLE_V8:
            raise PatchError(f"Referência inesperada a gBattleStringsTable em 0x{ref:X}")
        struct.pack_into("<I", out, ref, ROM + STRINGS_TABLE_V9)

    if bytes(out[BATTLE_STRING_CAP_SITE : BATTLE_STRING_CAP_SITE + 4]) != bytes([0xD4, 0x23, 0x5B, 0x00]):
        raise PatchError("Limite inesperado em BufferStringBattle (esperado motor_v8)")
    out[BATTLE_STRING_CAP_SITE : BATTLE_STRING_CAP_SITE + 2] = bytes([0xEB, 0x23])  # 0xEB << 1 = 470 > 453

    # 2. Instala sub-scripts fixos e os 13 efeitos finais (243..255) em SCRIPTS_V9.
    _write_fixed_sub(
        out, SUB_ENDTURN_AQUA_RING, 32,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x0A, 0x0C, 0x0A, 0x10]) + u16(STR_AQUA_RING_HEAL) + bytes([0x12, 0x40, 0x00, 0x3F]),
        "SUB_ENDTURN_AQUA_RING",
    )
    _write_fixed_sub(out, SUB_ENDTURN_OCTOLOCK, 96, _build_sub_endturn_octolock(), "SUB_ENDTURN_OCTOLOCK")
    _write_fixed_sub(out, SUB_STAT_QUEUE, 128, _build_sub_stat_queue(), "SUB_STAT_QUEUE")
    _write_fixed_sub(out, SUB_HEALING_WISH_IN, 64, _build_sub_hwish_in(SUB_HEALING_WISH_IN, STR_HEALING_WISH_CAME), "SUB_HEALING_WISH_IN")
    _write_fixed_sub(out, SUB_LUNAR_DANCE_IN, 64, _build_sub_hwish_in(SUB_LUNAR_DANCE_IN, STR_LUNAR_DANCE_CAME), "SUB_LUNAR_DANCE_IN")
    _write_fixed_sub(
        out, SUB_WORRY_SEED_WOKE, 32,
        bytes([0x98, 0x00, 0x3A, 0x10]) + u16(STR_WORRY_SEED) + bytes([0x12, 0x40, 0x00, 0x10])
        + u16(STR_TGT_WOKE_UP) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_WORRY_SEED_WOKE",
    )
    _write_fixed_sub(
        out, SUB_CANT_ESCAPE_END, 32,
        bytes([0x10, 0x8F, 0x00, 0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_CANT_ESCAPE_END",
    )
    _write_fixed_sub(
        out, SUB_LIQUID_OOZE_TAIL, 32,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x01, 0x0C, 0x01, 0x10]) + u16(STR_LIQUID_OOZE) + bytes([0x12, 0x40, 0x00])
        + bytes([0x19, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_LIQUID_OOZE_TAIL",
    )
    _write_fixed_sub(
        out, SUB_SLEEP_EFF, 32,
        bytes([0x64, 0x02, 0x10, 0x23, 0x00, 0x12, 0x40, 0x00, 0x98, 0x02, 0x3A, 0x6F, 0x02, 0x3C]),
        "SUB_SLEEP_EFF",
    )
    for idx, (sid, _txt) in enumerate(NEW_BATTLE_STRINGS_V9):
        _write_fixed_sub(
            out, SUB_STR_TAILS + 12 * idx, 12,
            bytes([0x10]) + u16(sid) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END) + bytes([0x00]),
            f"SUB_STR_TAIL_{idx}",
        )

    sc_cursor = DYNAMIC_SCRIPTS_START_V9
    effect_builders = (
        (EFF_FINAL_GAMBIT, lambda at: _bs_final_gambit(source)),
        (EFF_TYPE_ABILITY, lambda at: _bs_type_ability(at)),
        (EFF_RAW_STAGE_SWAP, lambda at: _bs_raw_stage_swap(at)),
        (EFF_TARGET_BUFF_TRAP, lambda at: _bs_target_buff_trap(at)),
        (EFF_FIELD_TEAM_V9, lambda at: _bs_field_team_v9()),
        (EFF_SELF_SACRIFICE_BOOST, lambda at: _bs_self_sacrifice_boost(at)),
        (EFF_SELF_VOLATILE, lambda at: _bs_self_volatile()),
        (EFF_STRENGTH_SAP, lambda at: _bs_strength_sap(at)),
        (EFF_CLERIC_STATUS, lambda at: _bs_cleric_status(at)),
        (EFF_DARK_VOID, lambda at: _bs_dark_void(at)),
        (EFF_HEALING_WISH, lambda at: _bs_healing_wish()),
        (EFF_SHED_TAIL, lambda at: _bs_shed_tail(at)),
        (EFF_TURN_COPY_CTRL, lambda at: _bs_turn_copy_ctrl(at)),
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

    # 4. Atualiza MOVE_TABLE nos 49 golpes de subida de nível implementados no motor_v9.
    field_offsets = {
        "eff": 0, "pwr": 1, "typ": 2, "acc": 3, "pp": 4,
        "chance": 5, "tgt": 6, "prio": 7, "flags": 8,
    }
    for mid, changes in MOVE_UPDATES_V9.items():
        base = complement.MOVE + 12 * mid
        for key, val in changes.items():
            out[base + field_offsets[key]] = val & 0xFF

    # 5. Recompila learnsets por nível (+368 entradas -> 14.995 linhas, 100% superconjunto de v8).
    prior_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/learnsets_motor_v8.csv"].decode("utf-8"))))
    cur_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/learnsets_motor_v9.csv"].decode("utf-8"))))
    lv_key = lambda r: (int(r["species"]), int(r["level"]), int(r["internal_move"]), int(r["api_move"]))
    if len(cur_lv) != 14995 or not set(map(lv_key, prior_lv)).issubset(set(map(lv_key, cur_lv))):
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
        print("Motor parcial v9: +49 golpes / +368 entradas de nível (695/729 = 95,3% restauradas) + 229/229 TMs SV.")
    except (OSError, ValueError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
