#!/usr/bin/env python3
"""Aplica o motor_v7 sobre a ROM motor_v6 identificada por SHA-256.

Escopo estrito e auditável sobre o motor_v6:
  1. Eleva o teto de nomes de golpe em batalha (0x08055B36, 0x08056350,
     0x08056370: 812 -> 824 = 0xCE << 2, com sentinelas válidas em 822..824),
     preservando intacto o terminador de egg moves 797 (0x0810AEE6, 0x0810AF6C).
  2. Instala estado efêmero de batalha em 0x0203FC00..0x0203FC5F via ponteiros
     literais de início de batalha (0x08051D74) e início de turno (0x0805439C)
     e reloca gBattleScriptingCommandsTable em 0x090BFC00 encadeando sobre o
     motor_v6.
  3. Habilita nove TMs de Scarlet/Violet por famílias mecânicas compartilhadas
     (210 -> 219 de 229): TM195 Burning Jealousy (813), TM199 Lash Out (814),
     TM207 Temper Flare (815), TM213 Coaching (816), TM220 Meteor Beam (817),
     TM226 Dragon Cheer (818), TM227 Alluring Voice (819), TM228 Psychic Noise
     (820) e TM229 Upper Hand (821).
  4. Completa a mecânica de troca automática em TM048 Volt Switch (517), TM060
     U-turn (369) e TM196 Flip Turn (708), dobra TM084 Stomping Tantrum (653)
     após falha anterior e ativa cinco golpes de nível antes omitidos (+59
     entradas): Heal Pulse (504), Parting Shot (571), Geomancy (597), Floral
     Healing (621) e Life Dew (696).

Continua sendo um motor parcial: as 10 TMs SV globais de clima/terreno/campo/
hazards (TM052, TM091, TM113, TM116, TM136..139, TM161 e TM178) e 647 entradas
de nível (75 golpes) permanecem pendentes e documentadas. Não altera saves
pessoais; grava sempre um arquivo novo.
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
from scripts import efeitos_gen9 as effects
from scripts import golpes_gen9 as level
from scripts import motor_v6 as v6
from scripts.treino_ev import write_new_file

BASE_SHA256 = '75d66d3c36e560df29f6c613666b91a6c81ce24663b6a3f76f4dd2ea7d747ce6'
OUTPUT_SHA256 = '6321d8e2900cc44dcaefb2dedfbaf5b0952b2796ca27a4cb9d8dc0875827de09'

INPUTS = {
    ROOT / 'patches/motor_v7/payload.bin': '4b2c1948aa0ac7a46ed976e114445a71242bf1d1c69c0ba59adc22d9181f6843',
    ROOT / 'data/tms_motor_v7.csv': 'ef1fd0c595e644805a3b2722d30ac146807632c925ac5108cae1314cfcc8dace',
    ROOT / 'data/compatibilidade_tms_motor_v7.bin': '618563d9dbc6ead8ecce2ae0f38978ec62ff0da5ebae2e294efaffbb7e1420d7',
    ROOT / 'data/compatibilidade_tms_motor_v6.bin': '649d97ea5e3d45e52ac19c3545a4ec448bfa4b46c21f17c3b41eac8a460c873e',
    ROOT / 'data/learnsets_motor_v7.csv': 'ed8e02a3bb3665a68ed3d53a59c2532d273bf0cbda630ef77aee56e6cbc6c2fe',
    ROOT / 'data/learnsets_motor_v6.csv': '9e7fd32c36a9a5e0c81e5eea639d904f534db9b1667308efcdca4078b21871d0',
}

ROM = 0x08000000
OLD_MOVE_COUNT = 813
MOVE_COUNT = 822      # 0..821 (arredondado em MOVE_NAME_CAP_SITES para 824 = 0xCE << 2)
SENTINEL_CAP = 824

SCRIPTS_V7 = 0x10BF000
DESC_TEXT_V7 = 0x10BF800
CMD_TABLE_V7 = 0x10BFC00
PAYLOAD_V7 = 0x10C0000

BATTLE_INIT_LIT = 0x051D74
TURN_START_LIT = 0x05439C

ENTRY_BATTLE_INIT_V7       = 0x090C0001
ENTRY_TURN_START_V7        = 0x090C0009
ENTRY_ATTACKCANCELER_V7    = 0x090C0011
ENTRY_CRITCALC_V7          = 0x090C0019
ENTRY_DAMAGE_V7            = 0x090C0021
ENTRY_HEALTHBAR_V7         = 0x090C0029
ENTRY_DATAHP_V7            = 0x090C0031
ENTRY_SETEFFECT_CHANCE_V7  = 0x090C0039
ENTRY_SETEFFECT_PRIMARY_V7 = 0x090C0041
ENTRY_SETEFFECT_SEC_V7     = 0x090C0049
ENTRY_MOVEEND_V7           = 0x090C0051
ENTRY_STATBUFFCHANGE_V7    = 0x090C0059
ENTRY_PIVOT_CHECK          = 0x090C0061
ENTRY_PARTING_INIT         = 0x090C0069
ENTRY_PARTING_CHECK        = 0x090C0071
ENTRY_COACHING_CHECK       = 0x090C0079
ENTRY_DRAGON_CHEER_APPLY   = 0x090C0081
ENTRY_RESTORE_ATTACKER     = 0x090C0089
ENTRY_UPPER_HAND_CHECK     = 0x090C0091
ENTRY_BURNING_JEALOUSY_SEC = 0x090C0099
ENTRY_ALLURING_VOICE_SEC   = 0x090C00A1
ENTRY_PSYCHIC_NOISE_APPLY  = 0x090C00A9
ENTRY_TARGET_HEAL_PREP     = 0x090C00B1
ENTRY_LIFE_DEW_CHECK       = 0x090C00B9
ENTRY_LIFE_DEW_SELF        = 0x090C00C1
ENTRY_LIFE_DEW_ALLY        = 0x090C00C9

NEW_MOVES = (
    # (tm, mid, api_move, name, move_bytes_9, category, desc)
    (195, 813, 807, 'BURNING JEALOUSY', (231, 70,  10, 100,  5, 100, 0x08, 0, 0x12), 1, 'QUEIMA QUEM SUBIU\nATRIBUTO NO TURNO.'),
    (199, 814, 808, 'LASH OUT',         (0,   75,  17, 100,  5,   0, 0x00, 0, 0x33), 0, 'DOBRA PODER SE UM\nATRIBUTO CAIU.'),
    (207, 815, 915, 'TEMPER FLARE',     (0,   75,  10, 100, 10,   0, 0x00, 0, 0x33), 0, 'DOBRA PODER APOS\nGOLPE FALHAR.'),
    (213, 816, 811, 'COACHING',         (228,  0,   1,   0, 10,   0, 0x10, 0, 0x00), 2, 'SOBE ATAQUE E DEF.\nDO ALIADO.'),
    (220, 817, 800, 'METEOR BEAM',      (226, 120,  5,  90, 10, 100, 0x00, 0, 0x12), 1, 'SOBE AT. ESP. NO\n1O TURNO E ATACA.'),
    (226, 818, 913, 'DRAGON CHEER',     (229,  0,  16,   0, 15,   0, 0x10, 0, 0x00), 2, 'ELEVA CHANCE CRIT.\nDO ALIADO.'),
    (227, 819, 914, 'ALLURING VOICE',   (232, 80,  18, 100, 10, 100, 0x00, 0, 0x12), 1, 'CONFUNDE SE ALVO\nSUBIU NO TURNO.'),
    (228, 820, 917, 'PSYCHIC NOISE',    (233, 75,  14, 100, 10, 100, 0x00, 0, 0x12), 1, 'CAUSA DANO E IMPEDE\nCURA POR 2 TURNOS.'),
    (229, 821, 918, 'UPPER HAND',       (230, 65,   1, 100, 15, 100, 0x00, 3, 0x13), 0, 'ANTECIPA PRIORIDADE\nE CAUSA HESITACAO.'),
)

# Golpes existentes que ganham efeito dedicado no motor_v7: (mid, old_eff, new_eff)
EXISTING_EFFECT_UPDATES = (
    (369, 0,  224),  # TM060 U-turn
    (517, 0,  224),  # TM048 Volt Switch
    (708, 0,  224),  # TM196 Flip Turn
    (571, 85, 225),  # Parting Shot (level-up)
    (597, 85, 227),  # Geomancy (level-up)
    (504, 85, 234),  # Heal Pulse (level-up)
    (621, 85, 234),  # Floral Healing (level-up)
    (696, 85, 235),  # Life Dew (level-up)
)


class PatchError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_inputs() -> dict[Path, bytes]:
    result = {}
    for path, sha in INPUTS.items():
        data = path.read_bytes()
        if digest(data) != sha:
            raise PatchError(f'Arquivo de dados divergente: {path.name}')
        result[path] = data
    return result


def _emit_callasm(s: effects.BattleScript, fn_thumb: int) -> None:
    s.emit(0xF8)
    s.ptr(fn_thumb)


def _emit_pivot_switch_tail(s: effects.BattleScript) -> None:
    s.setbyte(0x0202181C, 0)         # sBattleScripting.moveendState = 0
    s.emit(0x49, 0x02, 0x10)         # moveend 2, 16 (executa estados 0..15 antes da troca)
    _emit_callasm(s, ENTRY_PIVOT_CHECK)
    s.emit(0x4F, 0x81)               # jumpifcannotswitch BS_ATTACKER | ATK4F_DONT_CHECK_STATUSES
    s.ptr(0x081853FC)
    s.emit(0x50, 0x01)               # openpartyscreen BS_ATTACKER
    s.ptr(0x081853FC)
    s.emit(0xE2, 0x01, 0x3A)         # switchoutabilities BS_ATTACKER; waitstate
    s.emit(0x51, 0x01, 0x02)         # switchhandleorder BS_ATTACKER, 2 (grava escolha de openpartyscreen; Baton Pass só ocorre se gCurrentMove == 226)
    s.emit(0x58, 0x01)               # returntoball BS_ATTACKER
    s.emit(0x4C, 0x01, 0x4D, 0x01)   # getswitchedmondata + switchindataupdate BS_ATTACKER
    s.emit(0x73, 0x01)               # hpthresholds BS_ATTACKER
    s.emit(0x10, 0x03, 0x00)         # printstring 3
    s.emit(0x4E, 0x01, 0x00, 0x3A)   # switchinanim BS_ATTACKER, 0; waitstate
    s.emit(0x52, 0x01)               # switchineffects BS_ATTACKER
    s.goto(0x081853FC)               # finaliza MOVEEND_COUNT (estado 16)


def bs_pivot_hit(source: bytes, base: int) -> bytes:
    s = effects.BattleScript(base)
    chunk = source[0x1853CE:0x1853F6]
    if len(chunk) != 40 or chunk[0] != 0x00:
        raise PatchError('Trecho nativo de EffectHit inesperado')
    s.data.extend(chunk)
    _emit_pivot_switch_tail(s)
    return s.finish()


def bs_parting_shot(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)
    _emit_callasm(s, ENTRY_PARTING_INIT)
    s.jumpifstat(0, 2, 1, 0, 'animate')
    s.jumpifstat(0, 0, 4, 0, 0x08186F41)
    s.label('animate')
    s.emit(0x01)
    s.ptr(0x0818689A)
    s.emit(0x00, 0x00)
    s.emit(0x09, 0x0A)
    s.setbyte(0x02021823, 0)
    s.emit(0x48, 0x00, (1 << 1) | (1 << 4), 5)
    for i, stat in enumerate((1, 4)):
        s.emit(0x48, 0x00, 1 << stat, 1)
        s.setbyte(0x02021822, stat | (1 << 4) | 0x80)
        s.emit(0x89, 0x01)
        s.ptr(f'next{i}')
        s.emit(0x29, 0x00)
        s.ptr(0x020216C5)
        s.emit(2)
        s.ptr(f'next{i}')
        s.emit(0x13)
        s.ptr(0x082085AC)
        s.emit(0x12, 0x40, 0x00)
        s.label(f'next{i}')
    _emit_callasm(s, ENTRY_PARTING_CHECK)
    _emit_pivot_switch_tail(s)
    return s.finish()


def bs_meteor_beam(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x1D, 0x01)               # jumpifstatus2 BS_ATTACKER, STATUS2_MULTIPLETURNS, turn2
    s.ptr(0x00001000)
    s.ptr(0x081859D1)
    s.emit(0x2B, 0x04)               # jumpifword CMP_COMMON_BITS, gHitMarker, 0x200, turn2
    s.ptr(0x0202160C)
    s.ptr(0x00000200)
    s.ptr(0x081859D1)
    s.setbyte(0x02021817, 3)         # chooser 3 -> "{FD:0F} esta brilhando!"
    s.emit(0x41)                     # call BattleScript_FirstTurnOfTwo
    s.ptr(0x08185A00)
    s.setbyte(0x02021822, 0x14)      # Sp. Atk +1 (espelho exato de Skull Bash 0x08186560)
    s.emit(0x89, 0x41)
    s.ptr('done')
    s.emit(0x29, 0x00)
    s.ptr(0x020216C5)
    s.emit(2)
    s.ptr('done')
    s.emit(0x47, 0x45, 0x01, 0x01)
    s.ptr(0x02021818)
    s.emit(0x13)
    s.ptr(0x082085A0)
    s.emit(0x12, 0x40, 0x00)
    s.label('done')
    s.goto(0x081853F6)
    return s.finish()


def bs_geomancy(source: bytes, base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x1D, 0x01)               # jumpifstatus2 BS_ATTACKER, STATUS2_MULTIPLETURNS, turn2
    s.ptr(0x00001000)
    s.ptr('turn2')
    s.emit(0x2B, 0x04)               # jumpifword CMP_COMMON_BITS, gHitMarker, 0x200, turn2
    s.ptr(0x0202160C)
    s.ptr(0x00000200)
    s.ptr('turn2')
    s.setbyte(0x02021817, 3)         # chooser 3 -> "{FD:0F} esta brilhando!"
    s.emit(0x41)
    s.ptr(0x08185A00)
    s.goto(0x081853F6)

    s.label('turn2')
    prefix = source[0x1859D1:0x1859E9]
    if len(prefix) != 24 or prefix[0] != 0x00:
        raise PatchError('Prefixo de TwoTurnMovesSecondTurn inesperado')
    s.data.extend(prefix)            # attackcanceler + limpa MULTIPLETURNS + NO_PPDEDUCT
    s.emit(0x02)                     # attackstring
    for stat in (4, 5):
        s.jumpifstat(1, 3, stat, 12, 'animate')
    s.jumpifstat(1, 0, 3, 12, 0x0818708F)
    s.label('animate')
    s.emit(0x09, 0x0A)
    s.setbyte(0x02021823, 0)
    s.emit(0x48, 0x01, (1 << 4) | (1 << 5) | (1 << 3), 0)
    for i, stat in enumerate((4, 5, 3)):
        s.setbyte(0x02021822, stat | (2 << 4))
        s.emit(0x89, 0x41)
        s.ptr(f'next{i}')
        s.emit(0x29, 0x00)
        s.ptr(0x020216C5)
        s.emit(2)
        s.ptr(f'next{i}')
        s.emit(0x13)
        s.ptr(0x082085A0)
        s.emit(0x12, 0x40, 0x00)
        s.label(f'next{i}')
    s.goto(0x081853F6)
    return s.finish()


def bs_coaching(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)
    _emit_callasm(s, ENTRY_COACHING_CHECK)
    s.emit(0x09, 0x0A)
    s.setbyte(0x02021823, 0)
    s.emit(0x48, 0x00, (1 << 1) | (1 << 2), 0)
    for i, stat in enumerate((1, 2)):
        s.setbyte(0x02021822, stat | (1 << 4))
        s.emit(0x89, 0x01)           # aplica aumento em BS_TARGET (aliado)
        s.ptr(f'next{i}')
        s.emit(0x29, 0x00)
        s.ptr(0x020216C5)
        s.emit(2)
        s.ptr(f'next{i}')
        s.emit(0x13)
        s.ptr(0x082085A0)
        s.emit(0x12, 0x40, 0x00)
        s.label(f'next{i}')
    s.goto(0x081853F6)
    return s.finish()


def bs_dragon_cheer(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)
    _emit_callasm(s, ENTRY_DRAGON_CHEER_APPLY)
    s.emit(0x09, 0x0A)
    _emit_callasm(s, ENTRY_RESTORE_ATTACKER)  # troca ATTACKER <-> TARGET para exibir nome do aliado
    s.emit(0x10, 0x63, 0x00, 0x12, 0x40, 0x00)
    _emit_callasm(s, ENTRY_RESTORE_ATTACKER)  # restaura ATTACKER e TARGET originais
    s.goto(0x081853F6)
    return s.finish()


def bs_upper_hand(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)
    _emit_callasm(s, ENTRY_UPPER_HAND_CHECK)
    s.emit(0x01)
    s.ptr(0x08185408)
    s.emit(0x00, 0x00)
    s.setbyte(0x020216C3, 0x08)      # MOVE_EFFECT_FLINCH (100% via chance=100 em MOVE_TABLE)
    s.goto(0x081853D8)
    return s.finish()


def bs_conditional_sec_hit(source: bytes, base: int, sec_fn_thumb: int) -> bytes:
    s = effects.BattleScript(base)
    chunk = source[0x1853CE:0x1853EE]
    if len(chunk) != 32 or chunk[0] != 0x00:
        raise PatchError('Script nativo de dano inesperado')
    s.data.extend(chunk)
    _emit_callasm(s, sec_fn_thumb)
    s.emit(0x29, 0x00)               # jumpifbyte CMP_EQUAL, MOVE_EFFECT_BYTE, 0, skip_sec
    s.ptr(0x020216C3)
    s.emit(0x00)
    s.ptr('skip_sec')
    s.emit(0x15)                     # seteffectwithchance
    s.label('skip_sec')
    s.data.extend(source[0x1853EF:0x1853F6])
    s.goto(0x081853F6)
    return s.finish()


def bs_psychic_noise(source: bytes, base: int) -> bytes:
    s = effects.BattleScript(base)
    chunk = source[0x1853CE:0x1853EE]
    if len(chunk) != 32 or chunk[0] != 0x00:
        raise PatchError('Script nativo de dano inesperado')
    s.data.extend(chunk)
    _emit_callasm(s, ENTRY_PSYCHIC_NOISE_APPLY)
    s.data.extend(source[0x1853EF:0x1853F6])
    s.goto(0x081853F6)
    return s.finish()


def bs_target_heal(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)
    s.emit(0x01)                     # respeita Protect / semi-invulnerável (sem rolar precisão)
    s.ptr(0x0818689A)
    s.emit(0xFF, 0xFF)
    _emit_callasm(s, ENTRY_TARGET_HEAL_PREP)
    s.emit(0x09, 0x0A)
    s.emit(0x35)                     # HITMARKER_IGNORE_SUBSTITUTE (0x100)
    s.ptr(0x0202160C)
    s.ptr(0x00000100)
    s.emit(0x0B, 0x00, 0x0C, 0x00)   # healthbarupdate + datahpupdate BS_TARGET
    s.emit(0x10, 0x4B, 0x00, 0x12, 0x40, 0x00)  # "{FD:10} recuperou a saude!"
    s.goto(0x081853F6)
    return s.finish()


def bs_life_dew(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)
    _emit_callasm(s, ENTRY_LIFE_DEW_CHECK)
    s.emit(0x09, 0x0A)

    _emit_callasm(s, ENTRY_LIFE_DEW_SELF)
    s.ptr('ally_step')
    s.emit(0x35)
    s.ptr(0x0202160C)
    s.ptr(0x00000100)
    s.emit(0x0B, 0x00, 0x0C, 0x00)
    s.emit(0x10, 0x4B, 0x00, 0x12, 0x40, 0x00)

    s.label('ally_step')
    _emit_callasm(s, ENTRY_LIFE_DEW_ALLY)
    s.emit(0x35)
    s.ptr(0x0202160C)
    s.ptr(0x00000100)
    s.emit(0x0B, 0x00, 0x0C, 0x00)
    s.emit(0x10, 0x4B, 0x00, 0x12, 0x40, 0x00)
    s.goto(0x081853F6)
    return s.finish()


def build(source: bytes, inputs: dict[Path, bytes] | None = None) -> bytes:
    if len(source) != 0x2000000 or source[0xAC:0xB0] != b'BPRE' or digest(source) != BASE_SHA256:
        raise PatchError('A entrada não é a ROM motor_v6 identificada por SHA-256')
    inputs = checked_inputs() if inputs is None else inputs
    for path, sha in INPUTS.items():
        if path not in inputs or digest(inputs[path]) != sha:
            raise PatchError(f'Dados inválidos: {path.name}')

    rows = list(csv.DictReader(io.StringIO(inputs[ROOT / 'data/tms_motor_v7.csv'].decode('utf-8'))))
    if len(rows) != 229:
        raise PatchError('Catálogo de TMs inválido')
    available = {int(r['tm']): int(r['internal_move']) for r in rows if r['status'] == 'disponivel'}
    if len(available) != 219:
        raise PatchError(f'Quantidade inesperada de TMs disponíveis: {len(available)}')

    prior_compat = inputs[ROOT / 'data/compatibilidade_tms_motor_v6.bin']
    compat = inputs[ROOT / 'data/compatibilidade_tms_motor_v7.bin']
    if len(compat) != 1026 * 29 or any(a & ~b for a, b in zip(prior_compat, compat)):
        raise PatchError('Compatibilidade anterior foi removida ou corrompida')
    if source[0xE06000:0xE06000 + len(prior_compat)] != prior_compat:
        raise PatchError('Matriz de compatibilidade na ROM de entrada divergente')

    for site in v6.MOVE_NAME_CAP_SITES:
        if source[site:site + 2] != b'\xcb\x22':
            raise PatchError(f'Teto de nome de golpe inesperado em {site:#x}')
    if struct.unpack_from('<I', source, BATTLE_INIT_LIT)[0] != 0x08052725:
        raise PatchError('Literal BeginBattleIntro inesperado em 0x051D74')
    if struct.unpack_from('<I', source, TURN_START_LIT)[0] != 0x080544B9:
        raise PatchError('Literal CheckFocusPunch inesperado em 0x05439C')
    for site in v6.CMD_TABLE_PTRS:
        if struct.unpack_from('<I', source, site)[0] != ROM + v6.CMD_TABLE_V6:
            raise PatchError(f'Ponteiro de CMD_TABLE_V6 inesperado em {site:#x}')
    if struct.unpack_from('<I', source, v6.CMD_TABLE_V6 + 5 * 4)[0] != v6.ENTRY_DAMAGE_V6:
        raise PatchError('Hook de damagecalc do motor_v6 ausente')

    payload = inputs[ROOT / 'patches/motor_v7/payload.bin']
    free_checks = (
        (SCRIPTS_V7, 0x800),
        (DESC_TEXT_V7, 0x400),
        (CMD_TABLE_V7, 256 * 4),
        (PAYLOAD_V7, len(payload)),
    )
    for at, size in free_checks:
        if source[at:at + size] != b'\xff' * size:
            raise PatchError(f'Área reservada ocupada em {at:#x}')
    for mid in range(OLD_MOVE_COUNT, SENTINEL_CAP + 1):
        for at, size in (
            (complement.MOVE + mid * 12, 12),
            (complement.NAMES + mid * 17, 17),
            (complement.ANIM + mid * 4, 4),
            (complement.DESC + (mid - 1) * 4, 4),
            (complement.CATEGORY + mid, 1),
        ):
            if source[at:at + size] != b'\xff' * size:
                raise PatchError(f'Slot de golpe {mid} ocupado em {at:#x}')

    out = bytearray(source)

    # 1. Eleva o teto de nomes (> 812 -> > 824 = 0xCE << 2) e inicializa sentinelas 822..824.
    for site in v6.MOVE_NAME_CAP_SITES:
        out[site:site + 2] = b'\xce\x22'
    for mid in range(MOVE_COUNT, SENTINEL_CAP + 1):
        out[complement.MOVE + mid * 12:complement.MOVE + (mid + 1) * 12] = out[complement.MOVE:complement.MOVE + 12]
        out[complement.NAMES + mid * 17:complement.NAMES + (mid + 1) * 17] = out[complement.NAMES:complement.NAMES + 17]
        out[complement.CATEGORY + mid] = 2
        struct.pack_into('<I', out, complement.ANIM + mid * 4, 0x08175F3A)
        out[complement.DESC + (mid - 1) * 4:complement.DESC + mid * 4] = out[complement.DESC:complement.DESC + 4]

    # 2. Hooks literais de início de batalha/turno, CMD_TABLE_V7 e payload Thumb-1.
    struct.pack_into('<I', out, BATTLE_INIT_LIT, ENTRY_BATTLE_INIT_V7)
    struct.pack_into('<I', out, TURN_START_LIT, ENTRY_TURN_START_V7)
    out[CMD_TABLE_V7:CMD_TABLE_V7 + 256 * 4] = source[v6.CMD_TABLE_V6:v6.CMD_TABLE_V6 + 256 * 4]
    cmd_overrides = (
        (0x00, ENTRY_ATTACKCANCELER_V7),
        (0x04, ENTRY_CRITCALC_V7),
        (0x05, ENTRY_DAMAGE_V7),
        (0x0B, ENTRY_HEALTHBAR_V7),
        (0x0C, ENTRY_DATAHP_V7),
        (0x15, ENTRY_SETEFFECT_CHANCE_V7),
        (0x16, ENTRY_SETEFFECT_PRIMARY_V7),
        (0x17, ENTRY_SETEFFECT_SEC_V7),
        (0x49, ENTRY_MOVEEND_V7),
        (0x89, ENTRY_STATBUFFCHANGE_V7),
    )
    for op, entry in cmd_overrides:
        struct.pack_into('<I', out, CMD_TABLE_V7 + op * 4, entry)
    for site in v6.CMD_TABLE_PTRS:
        struct.pack_into('<I', out, site, ROM + CMD_TABLE_V7)
    out[PAYLOAD_V7:PAYLOAD_V7 + len(payload)] = payload

    # 3. Script fixo de cancelamento por bloqueio de cura em 0x090BF000 + efeitos 224..235.
    heal_cancel = bytes((0x02, 0x28)) + struct.pack('<I', 0x0818689A)
    out[SCRIPTS_V7:SCRIPTS_V7 + len(heal_cancel)] = heal_cancel
    sc_cursor = SCRIPTS_V7 + 8
    script_defs = (
        (224, lambda at: bs_pivot_hit(source, at)),
        (225, lambda at: bs_parting_shot(at)),
        (226, lambda at: bs_meteor_beam(at)),
        (227, lambda at: bs_geomancy(source, at)),
        (228, lambda at: bs_coaching(at)),
        (229, lambda at: bs_dragon_cheer(at)),
        (230, lambda at: bs_upper_hand(at)),
        (231, lambda at: bs_conditional_sec_hit(source, at, ENTRY_BURNING_JEALOUSY_SEC)),
        (232, lambda at: bs_conditional_sec_hit(source, at, ENTRY_ALLURING_VOICE_SEC)),
        (233, lambda at: bs_psychic_noise(source, at)),
        (234, lambda at: bs_target_heal(at)),
        (235, lambda at: bs_life_dew(at)),
    )
    for eff, make in script_defs:
        if struct.unpack_from('<I', source, complement.SCRIPT_TABLE + eff * 4)[0] != 0x081853A8:
            raise PatchError(f'Slot de efeito {eff} já ocupado')
        code = make(sc_cursor)
        if sc_cursor + len(code) > SCRIPTS_V7 + 0x800:
            raise PatchError('Scripts do motor_v7 excedem a reserva')
        out[sc_cursor:sc_cursor + len(code)] = code
        struct.pack_into('<I', out, complement.SCRIPT_TABLE + eff * 4, ROM + sc_cursor)
        sc_cursor = (sc_cursor + len(code) + 3) & ~3

    # 4. Atualiza efeitos dos golpes existentes (pivots e 5 golpes de nível) e grava golpes 813..821.
    for mid, old_eff, new_eff in EXISTING_EFFECT_UPDATES:
        if source[complement.MOVE + mid * 12] != old_eff:
            raise PatchError(f'Efeito anterior inesperado para golpe {mid}')
        out[complement.MOVE + mid * 12] = new_eff

    desc_cursor = DESC_TEXT_V7
    for tm, mid, _api, name_str, fields9, cat, desc_str in NEW_MOVES:
        out[complement.MOVE + mid * 12:complement.MOVE + (mid + 1) * 12] = bytes(fields9) + b'\x00\x00\x00'
        enc_name = previous.text(name_str)
        if len(enc_name) > 17:
            raise PatchError(f'Nome de golpe excede 17 bytes: {name_str}')
        out[complement.NAMES + mid * 17:complement.NAMES + (mid + 1) * 17] = enc_name + bytes(17 - len(enc_name))
        out[complement.CATEGORY + mid] = cat
        struct.pack_into('<I', out, complement.ANIM + mid * 4, 0x08175F3A)
        enc_desc = previous.text(desc_str)
        if desc_cursor + len(enc_desc) > DESC_TEXT_V7 + 0x400:
            raise PatchError('Descrições de golpes excedem a reserva')
        out[desc_cursor:desc_cursor + len(enc_desc)] = enc_desc
        struct.pack_into('<I', out, complement.DESC + (mid - 1) * 4, ROM + desc_cursor)
        desc_cursor += len(enc_desc)

        move_slot = previous.NEW_MOVE_TABLE + (374 + tm - 289) * 2
        if struct.unpack_from('<H', source, move_slot)[0] != 0:
            raise PatchError(f'TM{tm:03d} já tinha golpe associado')
        struct.pack_into('<H', out, move_slot, mid)

        expected_pal = v6.TYPE_TM_PALETTES[fields9[2]]
        icon_pic, icon_pal = struct.unpack_from('<II', out, v6.ICON_TABLE_V6 + (374 + tm) * 8)
        if (icon_pic, icon_pal) != (v6.TM_DISC_PIC, expected_pal):
            raise PatchError(f'Ícone da TM{tm:03d} divergente da paleta do tipo')

    # 5. Matriz de compatibilidade TM, lista da loja (219 itens) e descrições USO UNICO.
    out[0xE06000:0xE06000 + len(compat)] = compat
    out[v6.ITEM_TEXT_START:v6.ITEM_TEXT_END] = b'\xff' * (v6.ITEM_TEXT_END - v6.ITEM_TEXT_START)
    txt_cursor = v6.ITEM_TEXT_START
    for tm, mid in sorted(available.items()):
        entry = out[complement.NAMES + mid * 17:complement.NAMES + (mid + 1) * 17]
        if 0xFF not in entry:
            raise PatchError(f'Nome do golpe {mid} sem terminador')
        move_name = entry[:entry.index(0xFF)]
        item_desc = previous.text('GOLPE ')[:-1] + move_name + previous.text('\nUSO UNICO')
        if txt_cursor + len(item_desc) > v6.ITEM_TEXT_END:
            raise PatchError('Descrições de itens excedem a área reservada')
        out[txt_cursor:txt_cursor + len(item_desc)] = item_desc
        struct.pack_into('<I', out, previous.NEW_ITEMS + (374 + tm) * previous.ITEM_SIZE + 20, ROM + txt_cursor)
        txt_cursor += len(item_desc)

    products = b''.join(struct.pack('<H', 374 + tm) for tm in sorted(available)) + b'\x00\x00'
    if len(products) > previous.SHOP_SCRIPT - previous.SHOP_LIST:
        raise PatchError('Lista de produtos da loja excedeu o espaço')
    out[previous.SHOP_LIST:previous.SHOP_LIST + (previous.SHOP_SCRIPT - previous.SHOP_LIST)] = (
        products + b'\xff' * ((previous.SHOP_SCRIPT - previous.SHOP_LIST) - len(products))
    )

    # 6. Learnsets por nível atualizados (+59 entradas, preservando 100% das 14.323 do motor_v6).
    prior_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / 'data/learnsets_motor_v6.csv'].decode('utf-8'))))
    cur_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / 'data/learnsets_motor_v7.csv'].decode('utf-8'))))
    lv_key = lambda r: (int(r['species']), int(r['level']), int(r['internal_move']), int(r['api_move']))
    if len(cur_lv) != 14382 or not set(map(lv_key, prior_lv)).issubset(set(map(lv_key, cur_lv))):
        raise PatchError('Learnsets anteriores não foram integralmente preservados')
    lists = {sid: [] for sid in range(1, 1026)}
    for r in cur_lv:
        sid, lv, mid, _api = lv_key(r)
        if sid not in lists or not 0 <= lv <= 100 or not 0 < mid < MOVE_COUNT:
            raise PatchError(f'Entrada de nível inválida: {r}')
        lists[sid].append((lv, mid))
    if any(not vals or len(vals) > 50 or vals != sorted(vals, key=lambda v: v[0]) for vals in lists.values()):
        raise PatchError('Lista de nível fora dos limites do motor')
    lv_blob = level.build_tables(lists)
    if level.TABLE + len(lv_blob) > 0xF60000 or source[0xF5D000:0xF60000] != b'\xff' * 0x3000:
        raise PatchError('Tabelas de nível excederam a reserva 0x08F50000..0x08F60000')
    out[level.TABLE:0xF60000] = lv_blob + b'\xff' * (0xF60000 - level.TABLE - len(lv_blob))

    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.rom.resolve() == args.saida.resolve() or args.saida.exists():
            raise PatchError('A saída precisa ser um arquivo novo')
        src = args.rom.read_bytes()
        out = build(src)
        if OUTPUT_SHA256 and digest(out) != OUTPUT_SHA256:
            raise PatchError('SHA-256 da saída divergente do esperado')
        write_new_file(args.rom, args.saida, out)
        print(f'Entrada preservada: {digest(src)}\nNova cópia: {args.saida}\nSHA-256: {digest(out)}')
        print('Motor parcial v7: 219/229 TMs SV habilitadas + trocas; 10 TMs de campo seguem pendentes.')
    except (OSError, ValueError) as exc:
        print(f'[ERRO] {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
