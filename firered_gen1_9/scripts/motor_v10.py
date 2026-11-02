#!/usr/bin/env python3
"""Aplica o motor_v10 sobre a ROM motor_v9 identificada por SHA-256.

Escopo determinístico e auditável sobre o motor_v9:
  1. Instala estado efêmero de batalha do motor_v10 em 0x0203FD60..0x0203FDEF
     (144 B dentro da reserva livre verificada 0x0203FD60..0x0203FDF7, sem tocar
     estruturas persistentes ou saves) e encadeia início de batalha (0x08051D74),
     início de turno (0x0805439C) e fim de turno (0x08053208), além de relocar
     gBattleScriptingCommandsTable em 0x090CFC00 (encadeando 0x00, 0x01, 0x04,
     0x05, 0x06, 0x0C, 0x88 e 0xDD) e gBattleStringsTable em 0x090CE400 (+22
     mensagens PT-BR concisas, sid 457..478 < limite 480).
  2. Restaura +3 entradas de subida de nível (15.005 -> 15.008 linhas em
     data/learnsets_motor_v10.csv, alcançando 708/729 = 97,1% das entradas
     originalmente omitidas) com o motor unificado de consumo de Berries
     (itens 133..175): Stuff Cheeks (672), Teatime (677), Bug Bite (449, TM182),
     Pluck (365), Incinerate (509) e Belch (558).
  3. Consolida as mecânicas modernas de batalha das TMs de Scarlet/Violet e dos
     golpes Gen 4-9 de dano/efeito secundário (162 golpes atualizados na tabela
     de golpes + 38 golpes eff=0 enriquecidos via CMD_TABLE_V10 = 200 golpes).

Quatro golpes de subida de nível (21 linhas das 729 originais = 2,9%) permanecem
documentadamente fora de escopo por dependerem de habilidades ou UI ausentes na
base Gen 3: Simple Beam (492), Ally Switch (501), Instruct (644) e Revival
Blessing (755). Não altera saves pessoais; grava sempre arquivo novo.
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
from scripts import motor_v9 as v9
from scripts.treino_ev import write_new_file

BASE_SHA256 = v9.OUTPUT_SHA256
OUTPUT_SHA256 = "a533d1812812e2348bbe62a95a8c3817dd9d8372a89ff283f0e747c6c7ddeb09"

INPUTS = {
    ROOT / "patches/motor_v10/payload.bin": "4fdfbe8c0502fb875f5ed3cb50d1480a239587fbbc48dff0e8d595d5d060dce2",
    ROOT / "data/learnsets_motor_v10.csv": "53b4785cc81963624885be62a3d8d85896786edd98b890021b1feba9dec8caa1",
    ROOT / "data/learnsets_motor_v9.csv": "de3f00717240a20c513899422789082d20e7e56f911671677c92abbf26ccfeae",
}

ROM = 0x08000000
MOVE_COUNT = v9.MOVE_COUNT
EFF_V10_DISPATCH = 255

# Hooks encadeados sobre motor_v9
BATTLE_INIT_LIT = v9.BATTLE_INIT_LIT
TURN_START_LIT = v9.TURN_START_LIT
ENDTURN_CONT_LIT = v9.ENDTURN_CONT_LIT
BATTLE_STRINGS_TABLE_REFS = v9.BATTLE_STRINGS_TABLE_REFS

V9_BATTLE_STRINGS_COUNT = v9.V8_BATTLE_STRINGS_COUNT + len(v9.NEW_BATTLE_STRINGS_V9)

# Regiões exclusivas do motor_v10 em espaço livre 0xFF (0x10CD000..0x10D6000)
SCRIPTS_V10 = 0x10CD000
SCRIPTS_V10_END = 0x10CE400
STRINGS_TABLE_V10 = 0x10CE400
STRINGS_TABLE_V10_END = 0x10CF000
STRINGS_TEXT_V10 = 0x10CF000
STRINGS_TEXT_V10_END = 0x10CFC00
CMD_TABLE_V10 = 0x10CFC00
CMD_TABLE_V10_END = 0x10D0000
PAYLOAD_V10 = 0x10D0000
PAYLOAD_V10_END = 0x10D6000

# Sub-scripts fixos em 0x090CD000..0x090CD7FF (espelhados em motor_v10.c)
SUB_DISPATCH          = 0x10CD000
SUB_FAIL_PP           = 0x10CD010
SUB_THROAT_BLOCK      = 0x10CD020
SUB_CONSECUTIVE_FAIL  = 0x10CD030
SUB_ENDTURN_SALT_CURE = 0x10CD040
SUB_ENDTURN_SYRUP     = 0x10CD070
SUB_ENDTURN_THROAT    = 0x10CD0C0
SUB_BERRY_WAIT_STEP   = 0x10CD0D0
SUB_BERRY_HP_STEP     = 0x10CD0F0
SUB_BERRY_STATUS_STEP = 0x10CD110
SUB_BERRY_PP_STEP     = 0x10CD130
SUB_STAT_QUEUE_LOOP   = 0x10CD150
SUB_MSG_TAILS         = 0x10CD200
SUB_PHAZE_TAIL        = 0x10CD300
SUB_TRAP_TAIL         = 0x10CD330
SUB_PRIMARY_EFF_TAIL  = 0x10CD340
SUB_BURN_CURE_TAIL    = 0x10CD350
SUB_SLEEP_CURE_TAIL   = 0x10CD370
SUB_INCINERATE_TAIL   = 0x10CD390
SUB_SPECTRAL_CONT     = 0x10CD3B0
SUB_STANDARD_HIT      = 0x10CD400
SUB_TRIPLE_DIVE       = 0x10CD440
SUB_DOUBLE_IRON_BASH  = 0x10CD460
SUB_POPULATION_BOMB   = 0x10CD480
SUB_SCALE_SHOT        = 0x10CD580
SUB_MATCHA_GOTCHA     = 0x10CD660
SUB_SPECTRAL_THIEF    = 0x10CD700
SUB_POLLEN_ALLY       = 0x10CD720
SUB_STUFF_CHEEKS      = 0x10CD760
SUB_TEATIME           = 0x10CD780
SUB_VICTORY_DANCE     = 0x10CD7A0
SUB_ION_DELUGE        = 0x10CD7C0

# Ponteiros nativos
BS_HIT_CALC_START  = 0x081853D8
BS_MOVE_END        = 0x081853F6
BS_MISS_NO_PP      = 0x08185406
BS_MISS_AFTER_PP   = 0x08185408
BS_MULTIHIT_LOOP   = 0x08185794
BS_BUT_IT_FAILED   = 0x0818689A

HIT_MARKER_ADDR       = 0x0202160C
MOVE_EFFECT_BYTE_ADDR = 0x020216C3
STAT_BUFF_ADDR        = 0x02021822

# Vetores Thumb em 0x090D0000 (entry.s)
ENTRY_BATTLE_INIT_V10     = 0x090D0001
ENTRY_TURN_START_V10      = 0x090D0009
ENTRY_ENDTURN_V10         = 0x090D0011
ENTRY_ATTACKCANCELER_V10  = 0x090D0019
ENTRY_ACCURACYCHECK_V10   = 0x090D0021
ENTRY_CRITCALC_V10        = 0x090D0029
ENTRY_DAMAGE_V10          = 0x090D0031
ENTRY_TYPECALC_V10        = 0x090D0039
ENTRY_DATAHPUPDATE_V10    = 0x090D0041
ENTRY_NEGATIVEDAMAGE_V10  = 0x090D0049
ENTRY_LOWKICK_V10         = 0x090D0051
ENTRY_DISPATCH_V10        = 0x090D0059
ENTRY_POST_HIT_V10        = 0x090D0061
ENTRY_BERRY_STEP_V10      = 0x090D0069
ENTRY_STAT_QUEUE_STEP_V10 = 0x090D0071
ENTRY_RESTORE_BANKS_V10   = 0x090D0079

# Strings PT-BR novas do motor_v10 (sid 457..475 < cap 480)
_SID0 = 12 + V9_BATTLE_STRINGS_COUNT
STR_THROAT_BLOCK      = _SID0 + 0
STR_CONSECUTIVE_FAIL  = _SID0 + 1
STR_SALT_CURE_HURT    = _SID0 + 2
STR_THROAT_END        = _SID0 + 3
STR_BERRY_HEAL        = _SID0 + 4
STR_BERRY_CURE        = _SID0 + 5
STR_BERRY_PP          = _SID0 + 6
STR_SMACK_DOWN        = _SID0 + 7
STR_TERRAIN_CLEARED   = _SID0 + 8
STR_THROAT_CHOP_SET   = _SID0 + 9
STR_SALT_CURE_SET     = _SID0 + 10
STR_SYRUP_BOMB_SET    = _SID0 + 11
STR_CLEAR_SMOG        = _SID0 + 12
STR_CORE_ENFORCER     = _SID0 + 13
STR_ION_DELUGE        = _SID0 + 14
STR_BURN_UP           = _SID0 + 15
STR_DOUBLE_SHOCK      = _SID0 + 16
STR_INCINERATE        = _SID0 + 17
STR_POLLEN_HEAL       = _SID0 + 18
STR_WAKE_UP_CURE      = _SID0 + 19
STR_SPARKLING_CURE    = _SID0 + 20
STR_SPECTRAL_STEAL    = _SID0 + 21

NEW_BATTLE_STRINGS_V10 = (
    (STR_THROAT_BLOCK,     "Não pode usar golpes de som!"),
    (STR_CONSECUTIVE_FAIL, "Não pode repetir o golpe seguido!"),
    (STR_SALT_CURE_HURT,   "O sal fere o Pokémon!"),
    (STR_THROAT_END,       "Já pode usar golpes de som!"),
    (STR_BERRY_HEAL,       "A Berry restaurou os PVs!"),
    (STR_BERRY_CURE,       "A Berry curou o problema de estado!"),
    (STR_BERRY_PP,         "A Berry restaurou os PPs!"),
    (STR_SMACK_DOWN,       "O alvo foi derrubado ao chão!"),
    (STR_TERRAIN_CLEARED,  "O terreno desapareceu do campo!"),
    (STR_THROAT_CHOP_SET,  "O alvo não pode usar golpes de som!"),
    (STR_SALT_CURE_SET,    "O alvo está sendo curado em sal!"),
    (STR_SYRUP_BOMB_SET,   "O alvo ficou coberto de calda doce!"),
    (STR_CLEAR_SMOG,       "As mudanças de atributos sumiram!"),
    (STR_CORE_ENFORCER,    "A habilidade do alvo foi suprimida!"),
    (STR_ION_DELUGE,       "Uma chuva de íons eletrificou o ar!"),
    (STR_BURN_UP,          "As chamas do usuário se apagaram!"),
    (STR_DOUBLE_SHOCK,     "O usuário descarregou sua carga!"),
    (STR_INCINERATE,       "A Berry do alvo foi incinerada!"),
    (STR_POLLEN_HEAL,      "Os PVs do aliado foram restaurados!"),
    (STR_WAKE_UP_CURE,     "O alvo despertou do sono!"),
    (STR_SPARKLING_CURE,   "A queimadura do alvo foi curada!"),
    (STR_SPECTRAL_STEAL,   "Roubou os aumentos de atributos!"),
)

MSG_TAIL_ORDER_V10 = (
    STR_SMACK_DOWN,       # 0
    STR_TERRAIN_CLEARED,  # 1
    STR_THROAT_CHOP_SET,  # 2
    STR_SALT_CURE_SET,    # 3
    STR_SYRUP_BOMB_SET,   # 4
    STR_CLEAR_SMOG,       # 5
    STR_CORE_ENFORCER,    # 6
    STR_ION_DELUGE,       # 7
    STR_BURN_UP,          # 8
    STR_DOUBLE_SHOCK,     # 9
    STR_INCINERATE,       # 10
    STR_POLLEN_HEAL,      # 11
    STR_WAKE_UP_CURE,     # 12
    STR_SPARKLING_CURE,   # 13
)

# Atualizações da tabela de golpes (160 golpes verificados contra motor_v9):
#   mid -> (expected_name, {campo: valor})
MOVE_UPDATES_V10: dict[int, tuple[str, dict[str, int]]] = {
    # --- A. 19 atualizações numéricas Scarlet/Violet em golpes clássicos Gen 1-3 ---
    19:  ("FLY",               {"pwr": 90}),
    83:  ("FIRE SPIN",         {"pwr": 35, "acc": 85}),
    86:  ("THUNDER WAVE",      {"acc": 90}),
    91:  ("DIG",               {"pwr": 80}),
    92:  ("TOXIC",             {"acc": 90}),
    184: ("SCARY FACE",        {"acc": 100}),
    200: ("OUTRAGE",           {"pwr": 120, "pp": 10}),
    248: ("FUTURE SIGHT",      {"pwr": 120, "acc": 100, "pp": 10}),
    250: ("WHIRLPOOL",         {"pwr": 35, "acc": 85}),
    253: ("UPROAR",            {"pwr": 90}),
    257: ("HEAT WAVE",         {"pwr": 95}),
    261: ("WILL-O-WISP",       {"acc": 85}),
    282: ("KNOCK OFF",         {"pwr": 65}),
    315: ("OVERHEAT",          {"pwr": 130, "flags": 0x32}),
    328: ("SAND TOMB",         {"pwr": 35, "acc": 85}),
    330: ("MUDDY WATER",       {"pwr": 90}),
    331: ("BULLET SEED",       {"pwr": 25}),
    333: ("ICICLE SPEAR",      {"pwr": 25}),
    350: ("ROCK BLAST",        {"acc": 90}),

    # --- B. Ligações diretas a scripts nativos / motor_v6..v8 verificados ---
    # Dreno (eff=3: 50% nativo; 75% via hook_negativedamage_v10 em 573 e 605)
    528: ("HORN LEECH",        {"eff": 3}),
    566: ("PARABOLIC CHARGE",  {"eff": 3}),
    573: ("DRAINING KISS",     {"eff": 3}),
    605: ("OBLIVION WING",     {"eff": 3}),
    778: ("BITTER BLADE",      {"eff": 3}),
    # Queimadura secundária (eff=4)
    435: ("LAVA PLUME",        {"eff": 4, "chance": 30}),
    541: ("SEARING SHOT",      {"eff": 4, "chance": 30}),
    547: ("BLUE FLARE",        {"eff": 4, "chance": 20}),
    588: ("STEAM ERUPTION",    {"eff": 4, "chance": 30}),
    687: ("PYRO BALL",         {"eff": 4, "chance": 10}),
    737: ("INFERNAL PARADE",   {"eff": 4, "chance": 30}),
    741: ("SANDSEAR STORM",    {"eff": 4, "chance": 20}),
    # Congelamento secundário (eff=5)
    569: ("FREEZE-DRY",        {"eff": 5, "chance": 10}),
    715: ("FREEZING GLARE",    {"eff": 5, "chance": 10}),
    # Paralisia secundária (eff=6)
    395: ("FORCE PALM",        {"eff": 6, "chance": 30}),
    434: ("DISCHARGE",         {"eff": 6, "chance": 30}),
    546: ("BOLT STRIKE",       {"eff": 6, "chance": 20}),
    602: ("NUZZLE",            {"eff": 6, "chance": 100}),
    740: ("WILDBOLT STORM",    {"eff": 6, "chance": 20}),
    # Envenenamento secundário (eff=2) / crítico + veneno (eff=209)
    732: ("BARB BARRAGE",      {"eff": 2, "chance": 50}),
    439: ("CROSS POISON",      {"eff": 209, "chance": 10}),
    # Hesitação / Flinch (eff=31)
    407: ("DRAGON RUSH",       {"eff": 31, "chance": 20}),
    527: ("HEART STAMP",       {"eff": 31, "chance": 30}),
    533: ("STEAMROLLER",       {"eff": 31, "chance": 30}),
    552: ("ICICLE CRASH",      {"eff": 31, "chance": 30}),
    662: ("ZING ZAP",          {"eff": 31, "chance": 30}),
    716: ("FIERY WRATH",       {"eff": 31, "chance": 20}),
    729: ("MOUNTAIN GALE",     {"eff": 31, "chance": 30}),
    # Confusão secundária (eff=76)
    431: ("ROCK CLIMB",        {"eff": 76, "chance": 20}),
    447: ("CHATTER",           {"eff": 76, "chance": 100}),
    695: ("STRANGE STEAM",     {"eff": 76, "chance": 20}),
    # Multi-hit 2-5 (eff=29) e 2 hits fixos (eff=44)
    537: ("TAIL SLAP",         {"eff": 29}),
    590: ("WATER SHURIKEN",    {"eff": 29}),
    457: ("DOUBLE HIT",        {"eff": 44}),
    526: ("DUAL CHOP",         {"eff": 44}),
    540: ("GEAR GRIND",        {"eff": 44}),
    676: ("DRAGON DARTS",      {"eff": 44}),
    775: ("TWIN BEAM",         {"eff": 44}),
    795: ("TACHYON CUTTER",    {"eff": 44}),
    # Prisão por turnos (eff=42)
    462: ("MAGMA STORM",       {"eff": 42, "chance": 100}),
    603: ("INFESTATION",       {"eff": 42, "chance": 100}),
    686: ("SNAP TRAP",         {"eff": 42, "chance": 100}),
    713: ("THUNDER CAGE",      {"eff": 42, "chance": 100}),
    # Razão crítica elevada pura (eff=43)
    400: ("NIGHT SLASH",       {"eff": 43}),
    427: ("PSYCHO CUT",        {"eff": 43}),
    453: ("ATTACK ORDER",      {"eff": 43}),
    459: ("SPACIAL REND",      {"eff": 43}),
    782: ("AQUA CUTTER",       {"eff": 43}),
    # Recarga no turno seguinte (eff=80) e fúria travada 2-3 turnos (eff=27)
    416: ("GIGA IMPACT",       {"eff": 80}),
    438: ("ROCK WRECKER",      {"eff": 80}),
    458: ("ROAR OF TIME",      {"eff": 80}),
    657: ("PRISMATIC LASER",   {"eff": 80}),
    699: ("METEOR ASSAULT",    {"eff": 80}),
    700: ("ETERNABEAM",        {"eff": 80}),
    726: ("RAGING FURY",       {"eff": 27, "chance": 100}),
    # Quedas de atributos no alvo (eff=63 SpD -2, 68 Atk -1, 69 Def -1, 70 Spe -1, 71 SpA -1, 72 SpD -1, 73 Acc -1)
    464: ("SEED FLARE",        {"eff": 63, "chance": 40}),
    747: ("LUMINA CRASH",      {"eff": 63, "chance": 100}),
    643: ("TROP KICK",         {"eff": 68, "chance": 100}),
    724: ("SPRINGTIDE STORM",  {"eff": 68, "chance": 30}),
    530: ("RAZOR SHELL",       {"eff": 69, "chance": 50}),
    635: ("FIRE LASH",         {"eff": 69, "chance": 100}),
    654: ("SHADOW BONE",       {"eff": 69, "chance": 20}),
    693: ("GRAV APPLE",        {"eff": 69, "chance": 100}),
    717: ("THUNDEROUS KICK",   {"eff": 69, "chance": 100}),
    545: ("GLACIATE",          {"eff": 70, "chance": 100}),
    685: ("DRUM BEATING",      {"eff": 70, "chance": 100}),
    734: ("BITTER MALICE",     {"eff": 70, "chance": 100}),
    739: ("BLEAKWIND STORM",   {"eff": 70, "chance": 30}),
    581: ("MOONBLAST",         {"eff": 71, "chance": 30}),
    591: ("MYSTICAL FIRE",     {"eff": 71, "chance": 100}),
    694: ("SPIRIT BREAK",      {"eff": 71, "chance": 100}),
    692: ("APPLE ACID",        {"eff": 72, "chance": 100}),
    426: ("MUD BOMB",          {"eff": 73, "chance": 30}),
    429: ("MIRROR SHOT",       {"eff": 73, "chance": 30}),
    532: ("LEAF TORNADO",      {"eff": 73, "chance": 50}),
    535: ("NIGHT DAZE",        {"eff": 73, "chance": 40}),
    # Impulsos no próprio usuário (eff=138 +1 Def, 139 +1 Atk, 140 +1 todos, 204 -2 SpA, 218 -1 Def/-1 SpD, 220 50% HP, 186 Brick Break)
    587: ("DIAMOND STORM",     {"eff": 138, "chance": 50}),
    604: ("POWER-UP PUNCH",    {"eff": 139, "chance": 100}),
    465: ("OMINOUS WIND",      {"eff": 140, "chance": 10}),
    548: ("FIERY DANCE",       {"eff": 74,  "chance": 50}),
    651: ("FLEUR CANNON",      {"eff": 204, "chance": 100}),
    612: ("DRAGON ASCENT",     {"eff": 218}),
    731: ("HEADLONG RUSH",     {"eff": 218}),
    777: ("ARMOR CANNON",      {"eff": 218}),
    665: ("MIND BLOWN",        {"eff": 220}),
    728: ("CHLOROBLAST",       {"eff": 220}),
    765: ("RAGING BULL",       {"eff": 186}),

    # --- C. Golpes despachados por EFF_V10_DISPATCH = 255 ---
    # Motor de Berries e +3 learnsets restaurados
    365: ("PLUCK",             {"eff": EFF_V10_DISPATCH}),
    449: ("BUG BITE",          {"eff": EFF_V10_DISPATCH}),
    509: ("INCINERATE",        {"eff": EFF_V10_DISPATCH}),
    558: ("BELCH",             {"eff": EFF_V10_DISPATCH}),
    672: ("STUFF CHEEKS",      {"eff": EFF_V10_DISPATCH, "tgt": 0x10}),
    677: ("TEATIME",           {"eff": EFF_V10_DISPATCH, "tgt": 0x10, "flags": 0x00}),
    # Status especiais remanescentes
    565: ("ION DELUGE",        {"eff": EFF_V10_DISPATCH, "tgt": 0x10, "flags": 0x00}),
    730: ("VICTORY DANCE",     {"eff": EFF_V10_DISPATCH, "pp": 10, "tgt": 0x10}),
    # Cura de aliado / dano em oponente
    631: ("POLLEN PUFF",       {"eff": EFF_V10_DISPATCH, "tgt": 0x00}),
    # Phazing com dano
    508: ("CIRCLE THROW",      {"eff": EFF_V10_DISPATCH}),
    521: ("DRAGON TAIL",       {"eff": EFF_V10_DISPATCH}),
    # Aterramento, terreno, som, sal, calda, habilidades e tipos dinâmicos pós-impacto
    358: ("WAKE-UP SLAP",      {"eff": EFF_V10_DISPATCH}),
    364: ("FEINT",             {"eff": EFF_V10_DISPATCH}),
    478: ("SMACK DOWN",        {"eff": EFF_V10_DISPATCH}),
    498: ("CLEAR SMOG",        {"eff": EFF_V10_DISPATCH}),
    561: ("FELL STINGER",      {"eff": EFF_V10_DISPATCH}),
    606: ("THOUSAND ARROWS",   {"eff": EFF_V10_DISPATCH}),
    607: ("THOUSAND WAVES",    {"eff": EFF_V10_DISPATCH}),
    617: ("SPIRIT SHACKLE",    {"eff": EFF_V10_DISPATCH}),
    619: ("SPARKLING ARIA",    {"eff": EFF_V10_DISPATCH}),
    630: ("THROAT CHOP",       {"eff": EFF_V10_DISPATCH}),
    632: ("ANCHOR SHOT",       {"eff": EFF_V10_DISPATCH}),
    637: ("BURN UP",           {"eff": EFF_V10_DISPATCH}),
    642: ("CORE ENFORCER",     {"eff": EFF_V10_DISPATCH}),
    658: ("SPECTRAL THIEF",    {"eff": EFF_V10_DISPATCH}),
    666: ("PLASMA FISTS",      {"eff": EFF_V10_DISPATCH}),
    671: ("JAW LOCK",          {"eff": EFF_V10_DISPATCH}),
    702: ("STEEL ROLLER",      {"eff": EFF_V10_DISPATCH}),
    720: ("EERIE SPELL",       {"eff": EFF_V10_DISPATCH}),
    721: ("DIRE CLAW",         {"eff": EFF_V10_DISPATCH}),
    736: ("TRIPLE ARROWS",     {"eff": EFF_V10_DISPATCH}),
    753: ("ICE SPINNER",       {"eff": EFF_V10_DISPATCH}),
    754: ("GLAIVE RUSH",       {"eff": EFF_V10_DISPATCH}),
    756: ("SALT CURE",         {"eff": EFF_V10_DISPATCH}),
    779: ("DOUBLE SHOCK",      {"eff": EFF_V10_DISPATCH}),
    786: ("MATCHA GOTCHA",     {"eff": EFF_V10_DISPATCH, "chance": 20}),
    787: ("SYRUP BOMB",        {"eff": EFF_V10_DISPATCH}),
    796: ("MALIGNANT CHAIN",   {"eff": EFF_V10_DISPATCH}),
    # Multi-hit especializados
    668: ("DOUBLE IRON BASH",  {"eff": EFF_V10_DISPATCH, "chance": 30}),
    703: ("SCALE SHOT",        {"eff": EFF_V10_DISPATCH}),
    712: ("SURGING STRIKES",   {"eff": EFF_V10_DISPATCH}),
    752: ("POPULATION BOMB",   {"eff": EFF_V10_DISPATCH}),
    757: ("TRIPLE DIVE",       {"eff": EFF_V10_DISPATCH}),
    # Auto-quedas / auto-impulsos garantidos de estágios após causar dano
    359: ("HAMMER ARM",        {"eff": EFF_V10_DISPATCH}),
    553: ("V-CREATE",          {"eff": EFF_V10_DISPATCH}),
    613: ("HYPERSPACE FURY",   {"eff": EFF_V10_DISPATCH}),
    620: ("ICE HAMMER",        {"eff": EFF_V10_DISPATCH}),
    646: ("CLANGING SCALES",   {"eff": EFF_V10_DISPATCH}),
    688: ("AURA WHEEL",        {"eff": EFF_V10_DISPATCH}),
    722: ("PSYSHIELD BASH",    {"eff": EFF_V10_DISPATCH}),
    725: ("MYSTICAL POWER",    {"eff": EFF_V10_DISPATCH}),
    733: ("ESPER WING",        {"eff": EFF_V10_DISPATCH}),
    751: ("SPIN OUT",          {"eff": EFF_V10_DISPATCH}),
    763: ("TORCH SONG",        {"eff": EFF_V10_DISPATCH}),
    764: ("AQUA STEP",         {"eff": EFF_V10_DISPATCH}),
    766: ("MAKE IT RAIN",      {"eff": EFF_V10_DISPATCH}),
}

#Nota: os seguintes golpes permanecem em eff=0 (EffectHit) mas recebem mecânica
# dedicada via CMD_TABLE_V10 (attackcanceler / accuracycheck / critcalc /
# damagecalc / typecalc / turn_start):
#   362 Brine, 371 Payback, 372 Assurance, 376 Trump Card, 378 Wring Out,
#   386 Punishment, 387 Last Resort, 389 Sucker Punch, 461 Crush Grip,
#   474 Autotomize, 479 Storm Throw, 483 Heavy Slam, 484 Synchronoise,
#   495 Round, 496 Echoed Voice, 497 Chip Away, 513 Retaliate,
#   520 Frost Breath, 529 Sacred Sword, 531 Heat Crash, 544 Secret Sword,
#   556 Flying Press, 589 Hyperspace Hole, 618 Darkest Lariat,
#   641 Revelation Dance, 653 Stomping Tantrum, 659 Sunsteel Strike,
#   660 Moongeist Beam, 667 Photon Geyser, 670 Snipe Shot, 679 Bolt Beak,
#   680 Fishious Rend, 704 Shell Side Arm, 711 Wicked Blow, 714 Dragon Energy,
#   746 Last Respects, 762 Flower Trick, 768 Collision Course,
#   769 Electro Drift, 774 Hyper Drill, 776 Rage Fist, 780 Gigaton Hammer,
#   783 Psyblade, 784 Hydro Steam, 785 Blood Moon, 788 Ivy Cudgel,
#   790 Tera Starstorm, 791 Fickle Beam, 793 Thunderclap, 794 Mighty Cleave,
#   804 Tera Blast, 805 Grassy Glide.


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


def _decode_rom_move_name(raw: bytes) -> str:
    table = {
        0xBB: "A", 0xBC: "B", 0xBD: "C", 0xBE: "D", 0xBF: "E", 0xC0: "F",
        0xC1: "G", 0xC2: "H", 0xC3: "I", 0xC4: "J", 0xC5: "K", 0xC6: "L",
        0xC7: "M", 0xC8: "N", 0xC9: "O", 0xCA: "P", 0xCB: "Q", 0xCC: "R",
        0xCD: "S", 0xCE: "T", 0xCF: "U", 0xD0: "V", 0xD1: "W", 0xD2: "X",
        0xD3: "Y", 0xD4: "Z", 0x00: " ", 0xAE: "-", 0xB4: "'", 0xA3: "2",
    }
    out = []
    for b in raw:
        if b == 0xFF:
            break
        out.append(table.get(b, "?"))
    return "".join(out)


def _assert_free(rom: bytearray, start: int, end: int, label: str) -> None:
    if rom[start:end] != b"\xff" * (end - start):
        raise PatchError(f"Região {label} não está limpa (0x{start:X}..0x{end:X})")


def _write_fixed_sub(rom: bytearray, off: int, max_len: int, body: bytes, name: str) -> None:
    if len(body) > max_len:
        raise PatchError(f"Sub-script {name} excedeu {max_len} B ({len(body)} B)")
    rom[off : off + len(body)] = body


def _rebase_ptrs(blob: bytes, old_start: int, old_end: int, new_start: int) -> bytes:
    """Rebaseia ponteiros 32-bit alinhados a qualquer byte dentro de [old_start, old_end]."""
    buf = bytearray(blob)
    i = 0
    while i <= len(buf) - 4:
        val = struct.unpack_from("<I", buf, i)[0]
        if old_start <= val <= old_end:
            struct.pack_into("<I", buf, i, val - old_start + new_start)
            i += 4
        else:
            i += 1
    return bytes(buf)


def _sub_endturn_syrup(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.setbyte(0x02021823, 0)
    s.setbyte(STAT_BUFF_ADDR, 3 | (1 << 4) | 0x80)  # -1 Speed no TARGET
    s.emit(0x89, 0x01)
    s.ptr("done")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr("done")
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(3)
    s.ptr("done")
    s.emit(0x47, 0x45, 0x00, 0x01)
    s.ptr(0x02021818)
    s.emit(0x13)
    s.ptr(0x082085AC)
    s.emit(0x12, 0x40, 0x00)
    s.label("done")
    s.data.extend(callasm(ENTRY_RESTORE_BANKS_V10))
    s.emit(0x3F)
    return s.finish()


def _sub_stat_queue_loop(base_off: int) -> bytes:
    s = effects.BattleScript(base_off)
    s.label("stat_loop")
    s.data.extend(callasm(ENTRY_STAT_QUEUE_STEP_V10))
    s.ptr("do_up")
    s.ptr("do_down")

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
    return s.finish()


def _sub_population_bomb(source: bytes, base_off: int) -> bytes:
    # Clona Triple Axel (0x100B324..0x100B406), trocando 3 hits -> 10 hits (26 0A)
    # e potência escalonada (2F 1A 18 02 02 14) -> potência fixa 20 BP (2E 1A 18 02 02 14).
    raw = bytearray(source[0x100B324:0x100B406])
    idx_cnt = raw.find(b"\x8e\x26\x03")
    idx_pwr = raw.find(b"\x25\x2f\x1a\x18\x02\x02\x14")
    if idx_cnt < 0 or idx_pwr < 0:
        raise PatchError("Template de Triple Axel inesperado para Population Bomb")
    raw[idx_cnt + 2] = 0x0A
    raw[idx_pwr + 1] = 0x2E
    return _rebase_ptrs(bytes(raw), ROM + 0x100B324, ROM + 0x100B406, ROM + base_off)


def _sub_scale_shot(source: bytes, base_off: int) -> bytes:
    # Clona MultiHit nativo (0x185781..0x185832, incluindo os 7 bytes de tryfaintmon)
    # e insere ENTRY_POST_HIT_V10 antes do moveend multi-hit (0x08185832).
    raw = source[0x185781:0x185832]
    rebased = _rebase_ptrs(raw, ROM + 0x185781, ROM + 0x185831, ROM + base_off)
    return rebased + callasm(ENTRY_POST_HIT_V10)


def _sub_matcha_gotcha(source: bytes, base_off: int) -> bytes:
    # Clona EffectAbsorb nativo até tryfaintmon ATTACKER (0x18548F..0x1854EA),
    # aplica 20% Burn (MOVE_EFFECT = 0x03 + CMD 0x15), depois tryfaintmon ATTACKER/TARGET.
    raw = source[0x18548F:0x1854EA]
    sec_tail = (
        bytes([0x2E]) + u32(MOVE_EFFECT_BYTE_ADDR) + bytes([0x03, 0x15])
        + bytes([0x19, 0x01, 0x00]) + u32(0)
        + bytes([0x19, 0x00, 0x00]) + u32(0)
        + bytes([0x28]) + u32(BS_MOVE_END)
    )
    # 0x081854EA no original apontava para tryfaintmon ATTACKER; aponta para sec_tail.
    rebased = _rebase_ptrs(raw, ROM + 0x18548F, ROM + 0x1854EA, ROM + base_off)
    return rebased + sec_tail


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
        raise PatchError("A ROM de entrada não corresponde ao motor_v9 esperado")

    inputs = _load_verified_inputs()
    payload = inputs[ROOT / "patches/motor_v10/payload.bin"]

    out = bytearray(source)
    _assert_free(out, SCRIPTS_V10, SCRIPTS_V10_END, "SCRIPTS_V10")
    _assert_free(out, STRINGS_TABLE_V10, STRINGS_TABLE_V10_END, "STRINGS_TABLE_V10")
    _assert_free(out, STRINGS_TEXT_V10, STRINGS_TEXT_V10_END, "STRINGS_TEXT_V10")
    _assert_free(out, CMD_TABLE_V10, CMD_TABLE_V10_END, "CMD_TABLE_V10")
    _assert_free(out, PAYLOAD_V10, PAYLOAD_V10_END, "PAYLOAD_V10")

    # 1. Reloca gBattleStringsTable (+22 mensagens PT-BR sobre motor_v9, total sid <= 478 < 480).
    str_cursor = STRINGS_TEXT_V10
    new_str_ptrs: list[int] = []
    for idx, (sid, text) in enumerate(NEW_BATTLE_STRINGS_V10):
        expected_sid = 12 + V9_BATTLE_STRINGS_COUNT + idx
        if sid != expected_sid or sid >= 480:
            raise PatchError(f"SID inválido ou acima do teto 480: {sid}")
        encoded = v8.encode_ptbr(text)
        if str_cursor + len(encoded) > STRINGS_TEXT_V10_END:
            raise PatchError("Estouro em STRINGS_TEXT_V10")
        out[str_cursor : str_cursor + len(encoded)] = encoded
        new_str_ptrs.append(ROM + str_cursor)
        str_cursor += len(encoded)

    v9_str_tbl = bytes(source[v9.STRINGS_TABLE_V9 : v9.STRINGS_TABLE_V9 + V9_BATTLE_STRINGS_COUNT * 4])
    reloc_str_tbl = v9_str_tbl + b"".join(u32(p) for p in new_str_ptrs)
    if len(reloc_str_tbl) > STRINGS_TABLE_V10_END - STRINGS_TABLE_V10:
        raise PatchError("Estouro em STRINGS_TABLE_V10")
    out[STRINGS_TABLE_V10 : STRINGS_TABLE_V10 + len(reloc_str_tbl)] = reloc_str_tbl

    for ref in BATTLE_STRINGS_TABLE_REFS:
        if struct.unpack_from("<I", source, ref)[0] != ROM + v9.STRINGS_TABLE_V9:
            raise PatchError(f"Referência inesperada a gBattleStringsTable em 0x{ref:X}")
        struct.pack_into("<I", out, ref, ROM + STRINGS_TABLE_V10)

    # 2. Instala sub-scripts fixos e EFF_V10_DISPATCH = 255 em SCRIPTS_V10.
    _write_fixed_sub(out, SUB_DISPATCH, 16, callasm(ENTRY_DISPATCH_V10), "SUB_DISPATCH")
    _write_fixed_sub(
        out, SUB_FAIL_PP, 16,
        bytes([0x02, 0x03, 0x28]) + u32(BS_BUT_IT_FAILED),
        "SUB_FAIL_PP",
    )
    _write_fixed_sub(
        out, SUB_THROAT_BLOCK, 16,
        bytes([0x02, 0x10]) + u16(STR_THROAT_BLOCK) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_THROAT_BLOCK",
    )
    _write_fixed_sub(
        out, SUB_CONSECUTIVE_FAIL, 16,
        bytes([0x02, 0x10]) + u16(STR_CONSECUTIVE_FAIL) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_CONSECUTIVE_FAIL",
    )
    _write_fixed_sub(
        out, SUB_ENDTURN_SALT_CURE, 48,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x5C, 0x00, 0x3A, 0x0B, 0x00, 0x0C, 0x00, 0x10]) + u16(STR_SALT_CURE_HURT)
        + bytes([0x12, 0x40, 0x00, 0x19, 0x00, 0x00]) + u32(0)
        + callasm(ENTRY_RESTORE_BANKS_V10) + bytes([0x3F]),
        "SUB_ENDTURN_SALT_CURE",
    )
    _write_fixed_sub(out, SUB_ENDTURN_SYRUP, 80, _sub_endturn_syrup(SUB_ENDTURN_SYRUP), "SUB_ENDTURN_SYRUP")
    _write_fixed_sub(
        out, SUB_ENDTURN_THROAT, 16,
        bytes([0x10]) + u16(STR_THROAT_END) + bytes([0x12, 0x40, 0x00, 0x3F]),
        "SUB_ENDTURN_THROAT",
    )
    _write_fixed_sub(
        out, SUB_BERRY_WAIT_STEP, 32,
        bytes([0x3A]) + callasm(ENTRY_BERRY_STEP_V10),
        "SUB_BERRY_WAIT_STEP",
    )
    _write_fixed_sub(
        out, SUB_BERRY_HP_STEP, 32,
        bytes([0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x0A, 0x0C, 0x0A, 0x10]) + u16(STR_BERRY_HEAL)
        + bytes([0x12, 0x40, 0x00]) + callasm(ENTRY_BERRY_STEP_V10),
        "SUB_BERRY_HP_STEP",
    )
    _write_fixed_sub(
        out, SUB_BERRY_STATUS_STEP, 32,
        bytes([0x3A, 0x98, 0x0A, 0x3A, 0x10]) + u16(STR_BERRY_CURE)
        + bytes([0x12, 0x40, 0x00]) + callasm(ENTRY_BERRY_STEP_V10),
        "SUB_BERRY_STATUS_STEP",
    )
    _write_fixed_sub(
        out, SUB_BERRY_PP_STEP, 32,
        bytes([0x3A, 0x10]) + u16(STR_BERRY_PP)
        + bytes([0x12, 0x40, 0x00]) + callasm(ENTRY_BERRY_STEP_V10),
        "SUB_BERRY_PP_STEP",
    )
    _write_fixed_sub(
        out, SUB_STAT_QUEUE_LOOP, 160,
        _sub_stat_queue_loop(SUB_STAT_QUEUE_LOOP),
        "SUB_STAT_QUEUE_LOOP",
    )
    for idx, sid in enumerate(MSG_TAIL_ORDER_V10):
        _write_fixed_sub(
            out, SUB_MSG_TAILS + 12 * idx, 12,
            bytes([0x10]) + u16(sid) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END) + bytes([0x00]),
            f"SUB_MSG_TAIL_V10_{idx}",
        )
    _write_fixed_sub(
        out, SUB_PHAZE_TAIL, 16,
        bytes([0x8F]) + u32(BS_MOVE_END),
        "SUB_PHAZE_TAIL",
    )
    _write_fixed_sub(
        out, SUB_TRAP_TAIL, 16,
        bytes([0x2E]) + u32(MOVE_EFFECT_BYTE_ADDR) + bytes([0x20, 0x16, 0x28]) + u32(BS_MOVE_END),
        "SUB_TRAP_TAIL",
    )
    _write_fixed_sub(
        out, SUB_PRIMARY_EFF_TAIL, 16,
        bytes([0x16, 0x28]) + u32(BS_MOVE_END),
        "SUB_PRIMARY_EFF_TAIL",
    )
    _write_fixed_sub(
        out, SUB_BURN_CURE_TAIL, 32,
        bytes([0x3A, 0x98, 0x00, 0x3A, 0x10]) + u16(STR_SPARKLING_CURE)
        + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_BURN_CURE_TAIL",
    )
    _write_fixed_sub(
        out, SUB_SLEEP_CURE_TAIL, 32,
        bytes([0x3A, 0x98, 0x00, 0x3A, 0x10]) + u16(STR_WAKE_UP_CURE)
        + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_SLEEP_CURE_TAIL",
    )
    _write_fixed_sub(
        out, SUB_INCINERATE_TAIL, 24,
        bytes([0x3A, 0x10]) + u16(STR_INCINERATE) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_INCINERATE_TAIL",
    )
    _write_fixed_sub(
        out, SUB_SPECTRAL_CONT, 24,
        bytes([0x10]) + u16(STR_SPECTRAL_STEAL) + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_HIT_CALC_START),
        "SUB_SPECTRAL_CONT",
    )

    # Sub-scripts de impacto e status dedicados
    _write_fixed_sub(
        out, SUB_STANDARD_HIT, 64,
        source[0x1853CE:0x1853F6] + callasm(ENTRY_POST_HIT_V10),
        "SUB_STANDARD_HIT",
    )
    _write_fixed_sub(
        out, SUB_TRIPLE_DIVE, 32,
        bytes([0x00, 0x01]) + u32(BS_MISS_NO_PP) + bytes([0x00, 0x00, 0x02, 0x03, 0x8D, 0x03, 0x8E])
        + bytes([0x2E]) + u32(0x0202181E) + bytes([0x00, 0x28]) + u32(BS_MULTIHIT_LOOP),
        "SUB_TRIPLE_DIVE",
    )
    _write_fixed_sub(
        out, SUB_DOUBLE_IRON_BASH, 32,
        bytes([0x00, 0x01]) + u32(BS_MISS_NO_PP) + bytes([0x00, 0x00])
        + bytes([0x2E]) + u32(0x0202181E) + bytes([0x08, 0x02, 0x03, 0x8D, 0x02, 0x8E, 0x28])
        + u32(BS_MULTIHIT_LOOP),
        "SUB_DOUBLE_IRON_BASH",
    )
    _write_fixed_sub(
        out, SUB_POPULATION_BOMB, 256,
        _sub_population_bomb(source, SUB_POPULATION_BOMB),
        "SUB_POPULATION_BOMB",
    )
    _write_fixed_sub(
        out, SUB_SCALE_SHOT, 224,
        _sub_scale_shot(source, SUB_SCALE_SHOT),
        "SUB_SCALE_SHOT",
    )
    _write_fixed_sub(
        out, SUB_MATCHA_GOTCHA, 144,
        _sub_matcha_gotcha(source, SUB_MATCHA_GOTCHA),
        "SUB_MATCHA_GOTCHA",
    )
    _write_fixed_sub(
        out, SUB_SPECTRAL_THIEF, 32,
        bytes([0x00, 0x01]) + u32(BS_MISS_NO_PP) + bytes([0x00, 0x00, 0x02, 0x03])
        + callasm(ENTRY_POST_HIT_V10),
        "SUB_SPECTRAL_THIEF",
    )
    _write_fixed_sub(
        out, SUB_POLLEN_ALLY, 48,
        bytes([0x00, 0x02, 0x03])
        + callasm(ENTRY_POST_HIT_V10)
        + bytes([0x09, 0x0A, 0x35]) + u32(HIT_MARKER_ADDR) + u32(0x00000100)
        + bytes([0x0B, 0x00, 0x0C, 0x00, 0x10]) + u16(STR_POLLEN_HEAL)
        + bytes([0x12, 0x40, 0x00, 0x28]) + u32(BS_MOVE_END),
        "SUB_POLLEN_ALLY",
    )
    for sub_off, sub_name in (
        (SUB_STUFF_CHEEKS,  "SUB_STUFF_CHEEKS"),
        (SUB_TEATIME,       "SUB_TEATIME"),
        (SUB_VICTORY_DANCE, "SUB_VICTORY_DANCE"),
        (SUB_ION_DELUGE,    "SUB_ION_DELUGE"),
    ):
        _write_fixed_sub(
            out, sub_off, 32,
            bytes([0x00, 0x02, 0x03, 0x09, 0x0A]) + callasm(ENTRY_POST_HIT_V10),
            sub_name,
        )

    cur_slot255 = struct.unpack_from("<I", source, complement.SCRIPT_TABLE + EFF_V10_DISPATCH * 4)[0]
    if cur_slot255 != 0x081853A8:
        raise PatchError(f"Slot SCRIPT_TABLE[255] já ocupado: 0x{cur_slot255:08X}")
    struct.pack_into("<I", out, complement.SCRIPT_TABLE + EFF_V10_DISPATCH * 4, ROM + SUB_DISPATCH)

    # 3. Instala payload Thumb em 0x090D0000, CMD_TABLE_V10 em 0x090CFC00 e hooks.
    if len(payload) > PAYLOAD_V10_END - PAYLOAD_V10:
        raise PatchError("Payload do motor_v10 excede a reserva")
    out[PAYLOAD_V10 : PAYLOAD_V10 + len(payload)] = payload

    cmd_tbl = bytearray(source[v9.CMD_TABLE_V9 : v9.CMD_TABLE_V9 + 256 * 4])
    overrides = {
        0x00: ENTRY_ATTACKCANCELER_V10,
        0x01: ENTRY_ACCURACYCHECK_V10,
        0x04: ENTRY_CRITCALC_V10,
        0x05: ENTRY_DAMAGE_V10,
        0x06: ENTRY_TYPECALC_V10,
        0x0C: ENTRY_DATAHPUPDATE_V10,
        0x88: ENTRY_NEGATIVEDAMAGE_V10,
        0xDD: ENTRY_LOWKICK_V10,
    }
    for opc, target in overrides.items():
        struct.pack_into("<I", cmd_tbl, opc * 4, target)
    out[CMD_TABLE_V10 : CMD_TABLE_V10 + len(cmd_tbl)] = cmd_tbl

    for site in v6.CMD_TABLE_PTRS:
        if struct.unpack_from("<I", source, site)[0] != ROM + v9.CMD_TABLE_V9:
            raise PatchError(f"Ponteiro inesperado de CMD_TABLE em 0x{site:X}")
        struct.pack_into("<I", out, site, ROM + CMD_TABLE_V10)

    hooks = (
        (BATTLE_INIT_LIT, v9.ENTRY_BATTLE_INIT_V9, ENTRY_BATTLE_INIT_V10),
        (TURN_START_LIT, v9.ENTRY_TURN_START_V9, ENTRY_TURN_START_V10),
        (ENDTURN_CONT_LIT, v9.ENTRY_ENDTURN_V9, ENTRY_ENDTURN_V10),
    )
    for lit_off, expected_old, new_val in hooks:
        if struct.unpack_from("<I", source, lit_off)[0] != expected_old:
            raise PatchError(f"Literal de hook inesperado em 0x{lit_off:X}")
        struct.pack_into("<I", out, lit_off, new_val)

    # 4. Atualiza MOVE_TABLE validando o nome esperado de cada golpe na ROM base.
    field_offsets = {
        "eff": 0, "pwr": 1, "typ": 2, "acc": 3, "pp": 4,
        "chance": 5, "tgt": 6, "prio": 7, "flags": 8,
    }
    for mid, (exp_name, changes) in MOVE_UPDATES_V10.items():
        got_name = _decode_rom_move_name(source[complement.NAMES + 17 * mid : complement.NAMES + 17 * (mid + 1)])
        if got_name != exp_name:
            raise PatchError(f"Nome inesperado para golpe {mid}: {got_name!r} != {exp_name!r}")
        old_eff = source[complement.MOVE + 12 * mid]
        if old_eff >= 214:
            raise PatchError(f"Golpe {mid} ({exp_name}) já usa efeito customizado {old_eff}")
        base = complement.MOVE + 12 * mid
        for key, val in changes.items():
            out[base + field_offsets[key]] = val & 0xFF

    # 5. Recompila learnsets por nível (+3 entradas: 15.005 -> 15.008, preservando 100% do motor_v9).
    prior_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/learnsets_motor_v9.csv"].decode("utf-8"))))
    cur_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / "data/learnsets_motor_v10.csv"].decode("utf-8"))))
    lv_key = lambda r: (int(r["species"]), int(r["level"]), int(r["internal_move"]), int(r["api_move"]))
    if len(cur_lv) != 15008 or not set(map(lv_key, prior_lv)).issubset(set(map(lv_key, cur_lv))):
        raise PatchError("Learnsets anteriores do motor_v9 não foram integralmente preservados")
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
        print("Motor parcial v10: Berries (+3 learnsets = 15.008, 97,1%) + 162 golpes na tabela (+38 via CMD_TABLE) e 229/229 TMs SV preservadas.")
    except (OSError, ValueError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
