#!/usr/bin/env python3
"""Aplica correções de auditoria e seis novas TMs SV sobre motor_v5 (motor_v6).

Escopo estrito e auditável sobre o motor_v5 identificado por SHA-256:
  1. Corrige o teto fixo 796 de nomes de golpe em batalha (0x08055B36,
     0x08056350, 0x08056370 -> 812 = MOVE_COUNT - 1), preservando intacto o
     terminador de egg moves 797 (0x0810AEE6, 0x0810AF6C).
  2. Corrige o overflow de 1 byte de gBattleTextBuff2 sobre gBattleTextBuff3[0]
     (0x08E030BA: 15 -> 14 bytes antes de '!' + 0xFF).
  3. Reloca sItemIconTable (0..604) em 0x090BC000 atribuindo disco de TM com
     paleta por tipo para 375..603 e movendo o ícone ReturnToFieldArrow para
     604 nos quatro chamadores (Bag, ItemPC, Shop, BerryPouch).
  4. Habilita seis TMs de Scarlet/Violet por mecanismos autocontidos (204 ->
     210 de 229): TM043 Fling (move 374 + 23 entradas de nível), TM170 Steel
     Beam (808), TM198 Poltergeist (809), TM201 Misty Explosion (810), TM210
     Supercell Slam (811) e TM212 Triple Axel (812).

Continua sendo um motor parcial: 19 TMs SV, trocas automáticas (U-turn/Volt
Switch/Flip Turn) e 706 entradas de nível permanecem pendentes e documentadas.
Não altera saves pessoais; grava sempre um arquivo novo.
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
from scripts.treino_ev import write_new_file

BASE_SHA256 = 'cf1de0e237feefcfda6789bc81c726ed13d91d512b85c54b9f857520a7a4fc87'
OUTPUT_SHA256 = '75d66d3c36e560df29f6c613666b91a6c81ce24663b6a3f76f4dd2ea7d747ce6'

INPUTS = {
    ROOT / 'patches/motor_v6/payload.bin': '7d0fbcc8d1344d5ced74bbb4775a17e70ec42b562bfbf95cf50a8face4d44736',
    ROOT / 'data/tms_motor_v6.csv': 'aece81a00878e6da6e3a4287ee6448ef6885c828a3393a9e2b732a980c493ab0',
    ROOT / 'data/compatibilidade_tms_motor_v6.bin': '649d97ea5e3d45e52ac19c3545a4ec448bfa4b46c21f17c3b41eac8a460c873e',
    ROOT / 'data/compatibilidade_tms_motor_ampliado.bin': '484244b19b9bb30ac5dee089beb3d28f4a4fdbf25f27bf625275797ac19c3c71',
    ROOT / 'data/learnsets_motor_v6.csv': '9e7fd32c36a9a5e0c81e5eea639d904f534db9b1667308efcdca4078b21871d0',
    ROOT / 'data/learnsets_gen1_9_complemento.csv': 'a6c08fe9c4cbfd6dfa9e36b09a5a11b9744f3904ce3a3dabad0d5f695b3e742c',
    ROOT / 'data/fling_itens_motor_v6.bin': '50b4f285764945c3d0798fc383150b629b7c82176d769e22cb642b0ad7df57ab',
}

ROM = 0x08000000
OLD_MOVE_COUNT = 808
MOVE_COUNT = 813  # 0..812 (812 = 0xCB << 2)
SCRIPTS_V6 = 0x100B200
DESC_TEXT_V6 = 0x10BB040
ITEM_TEXT_START, ITEM_TEXT_END = 0x10B9000, 0x10BB000
ICON_TABLE_V6 = 0x10BC000
CMD_TABLE_V6 = 0x10BD400
FLING_TABLE_V6 = 0x10BD800
PAYLOAD_V6 = 0x10BE000

ENTRY_DAMAGE_V6 = 0x090BE001
ENTRY_CALLASM = 0x090BE009
ENTRY_FLING_CHECK = 0x090BE011
ENTRY_FLING_SECONDARY = 0x090BE019
ENTRY_POLTERGEIST_CHECK = 0x090BE021
ENTRY_STEEL_BEAM_DMG = 0x090BE029
ENTRY_SUPERCELL_DMG = 0x090BE031

ORIG_ICON_TABLE = 0x62FC74
ORIG_CMD_TABLE = 0x2097F0
CMD_TABLE_PTRS = (0x0538D4, 0x0549B4, 0x054BE8, 0x054C1C, 0x071DDC)
MOVE_NAME_CAP_SITES = (0x055B36, 0x056350, 0x056370)
ICON_CLAMP_SITES = (0x0CB1BE, 0x0CB2D8)
ICON_TABLE_PTRS = (0x0CB288, 0x0CB3A4)
RETURN_ARROW_CALLERS = (
    (0x0C7C0A, 0x0C7C12),  # Bag
    (0x0CBA1A, 0x0CBA1C),  # ItemPC
    (0x13BA86, 0x13BA8E),  # Shop
    (0x0766A6, 0x0766AA),  # BerryPouch
)

TM_DISC_PIC = 0x085F8080
TYPE_TM_PALETTES = {
    0:  0x085F821C,  # Normal
    1:  0x085F817C,  # Fighting
    2:  0x085F83D4,  # Flying
    3:  0x085F8244,  # Poison
    4:  0x085F835C,  # Ground
    5:  0x085F83AC,  # Rock
    6:  0x085F8294,  # Bug (paleta TMHM verde existente na ROM)
    7:  0x085F8384,  # Ghost
    8:  0x085F830C,  # Steel
    9:  0x085F8384,  # TYPE_MYSTERY (Curse em FireRed -> paleta Ghost para TM224)
    10: 0x085F82BC,  # Fire
    11: 0x085F81CC,  # Water
    12: 0x085F8294,  # Grass
    13: 0x085F8334,  # Electric
    14: 0x085F81F4,  # Psychic
    15: 0x085F826C,  # Ice
    16: 0x085F81A4,  # Dragon
    17: 0x085F82E4,  # Dark
    18: 0x085F81F4,  # Fairy (paleta TMHM rosa existente na ROM)
}
# Tipos das 8 TMs SV reservadas que ainda têm internal_move == 0 em tms_motor_v6.csv.
RESERVED_TM_TYPES = {
    195: 10,  # Burning Jealousy (Fire)
    199: 17,  # Lash Out (Dark)
    207: 10,  # Temper Flare (Fire)
    213: 1,   # Coaching (Fighting)
    220: 5,   # Meteor Beam (Rock)
    226: 16,  # Dragon Cheer (Dragon)
    227: 18,  # Alluring Voice (Fairy)
    228: 14,  # Psychic Noise (Psychic)
    229: 1,   # Upper Hand (Fighting)
}

NEW_MOVES = (
    # (tm, mid, api_move, name, move_bytes_9, category, desc)
    (170, 808, 796, 'STEEL BEAM',      (220, 140, 8,  95,  5, 0, 0x00, 0, 0x12), 1, 'DISPARA ACO MAS\nCUSTA METADE HP.'),
    (198, 809, 809, 'POLTERGEIST',     (221, 110, 7,  90,  5, 0, 0x00, 0, 0x12), 0, 'ATACA USANDO O\nITEM DO ALVO.'),
    (201, 810, 802, 'MISTY EXPLOSION', (7,   100, 18, 100, 5, 0, 0x20, 0, 0x12), 1, 'EXPLODE NEVOA E\nDESMAIA USUARIO.'),
    (210, 811, 916, 'SUPERCELL SLAM',  (222, 100, 13, 95, 15, 0, 0x00, 0, 0x33), 0, 'SE ERRAR. SOFRE\nMETADE DO HP.'),
    (212, 812, 813, 'TRIPLE AXEL',     (223, 20,  15, 90, 10, 0, 0x00, 0, 0x33), 0, 'ATE 3 CHUTES DE\nPODER CRESCENTE.'),
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


def _emit_self_hp_loss(s: effects.BattleScript, dmg_fn_thumb: int) -> None:
    _emit_callasm(s, dmg_fn_thumb)
    # Limpa MOVE_RESULT_NO_EFFECT (0x29 = MISSED|DOESNT_AFFECT|FAILED) para que
    # healthbarupdate/datahpupdate não ignorem o dano próprio após erro/imunidade.
    s.emit(0x36, 0x08, 0x16, 0x02, 0x02, 0x29)
    s.emit(0x35)  # orword gHitMarker, HITMARKER_IGNORE_SUBSTITUTE (0x100)
    s.ptr(0x0202160C)
    s.ptr(0x00000100)
    s.emit(0x0B, 0x01, 0x0C, 0x01)  # healthbarupdate + datahpupdate BS_ATTACKER
    s.emit(0x19, 0x01, 0, 0, 0, 0, 0)  # faintpokemon BS_ATTACKER
    s.goto(0x081853F6)


def bs_fling(source: bytes, base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)  # attackcanceler, attackstring, ppreduce
    _emit_callasm(s, ENTRY_FLING_CHECK)
    s.emit(0x01)  # accuracycheck missed, 0
    s.ptr('missed')
    s.emit(0x00, 0x00)
    s.emit(0x04, 0x05, 0x06, 0x07)  # atk4, critcalc, damagecalc, typecalc
    _emit_callasm(s, ENTRY_FLING_SECONDARY)
    s.emit(0x6A, 0x01)  # removeitem BS_ATTACKER
    s.emit(0x29, 0x04)  # jumpifbyte CMP_COMMON_BITS, gMoveResultFlags, 0x29, MoveMissedPause
    s.ptr(0x02021608)
    s.emit(0x29)
    s.ptr(0x08185408)
    s.data.extend(source[0x1853DC:0x1853EE])  # anim + barra HP + mensagens de dano
    s.emit(0x29, 0x00)  # jumpifbyte CMP_EQUAL, MOVE_EFFECT_BYTE, 0, after_eff
    s.ptr(0x020216C3)
    s.emit(0x00)
    s.ptr('after_eff')
    s.emit(0x15)  # seteffectwithchance (chance=100 em MOVE_TABLE[374])
    s.label('after_eff')
    s.data.extend(source[0x1853EF:0x1853F6])  # faintpokemon TARGET
    s.goto(0x081853F6)
    s.label('missed')
    s.emit(0x6A, 0x01)  # removeitem BS_ATTACKER mesmo em erro/Protect
    s.goto(0x08185408)
    return s.finish()


def bs_steel_beam(source: bytes, base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)
    s.emit(0x01)
    s.ptr('missed')
    s.emit(0x00, 0x00)
    s.emit(0x04, 0x05, 0x06, 0x07)
    s.emit(0x29, 0x04)
    s.ptr(0x02021608)
    s.emit(0x29)
    s.ptr('missed')
    s.data.extend(source[0x1853DC:0x1853EE])
    s.data.extend(source[0x1853EF:0x1853F6])
    s.label('self_loss')
    _emit_self_hp_loss(s, ENTRY_STEEL_BEAM_DMG)
    s.label('missed')
    s.emit(0x39, 0x20, 0x00, 0x0E, 0x0F, 0x12, 0x40, 0x00)
    s.emit(0x28)
    s.ptr('self_loss')
    return s.finish()


def bs_poltergeist(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)
    _emit_callasm(s, ENTRY_POLTERGEIST_CHECK)
    s.emit(0x01)
    s.ptr(0x08185408)
    s.emit(0x00, 0x00)
    s.goto(0x081853D8)
    return s.finish()


def bs_supercell_slam(base: int) -> bytes:
    s = effects.BattleScript(base)
    s.emit(0x00)
    s.emit(0x01)
    s.ptr('miss_acc')
    s.emit(0x00, 0x00)
    s.emit(0x02, 0x03, 0x04, 0x05, 0x06, 0x07)
    s.emit(0x29, 0x04)
    s.ptr(0x02021608)
    s.emit(0x29)
    s.ptr('crash')
    s.goto(0x081853DC)
    s.label('miss_acc')
    s.emit(0x02, 0x03)
    s.label('crash')
    s.emit(0x39, 0x20, 0x00, 0x0E, 0x0F, 0x12, 0x40, 0x00)
    s.emit(0x10, 0x60, 0x00, 0x12, 0x40, 0x00)  # "continuou e caiu!"
    _emit_self_hp_loss(s, ENTRY_SUPERCELL_DMG)
    return s.finish()


def bs_triple_axel(source: bytes, base: int) -> bytes:
    orig_start, orig_end = 0x18608E, 0x186171
    code = bytearray(source[orig_start:orig_end])
    if code[30:38] != bytes.fromhex('2a 00 88 15 02 02 d6 00'):
        raise PatchError('Checagem de ID de Triple Kick inesperada')
    if code[60:66] != bytes.fromhex('2f 1a 18 02 02 0a'):
        raise PatchError('Incremento de potência de Triple Kick inesperado')
    struct.pack_into('<H', code, 36, 812)  # MOVE_TRIPLE_AXEL (812)
    code[65] = 20  # +20 por acerto -> 20 / 40 / 60 BP
    relocated = 0
    for idx in range(len(code) - 3):
        val = struct.unpack_from('<I', code, idx)[0]
        if (ROM + orig_start) <= val < (ROM + orig_end):
            struct.pack_into('<I', code, idx, ROM + base + (val - (ROM + orig_start)))
            relocated += 1
    if relocated != 12:
        raise PatchError(f'Quantidade inesperada de ponteiros internos em Triple Kick: {relocated}')
    return bytes(code)


def build(source: bytes, inputs: dict[Path, bytes] | None = None) -> bytes:
    if len(source) != 0x2000000 or source[0xAC:0xB0] != b'BPRE' or digest(source) != BASE_SHA256:
        raise PatchError('A entrada não é a ROM motor_v5 identificada por SHA-256')
    inputs = checked_inputs() if inputs is None else inputs
    for path, sha in INPUTS.items():
        if path not in inputs or digest(inputs[path]) != sha:
            raise PatchError(f'Dados inválidos: {path.name}')

    rows = list(csv.DictReader(io.StringIO(inputs[ROOT / 'data/tms_motor_v6.csv'].decode('utf-8'))))
    if len(rows) != 229:
        raise PatchError('Catálogo de TMs inválido')
    available = {int(r['tm']): int(r['internal_move']) for r in rows if r['status'] == 'disponivel'}
    if len(available) != 210:
        raise PatchError(f'Quantidade inesperada de TMs disponíveis: {len(available)}')

    prior_compat = inputs[ROOT / 'data/compatibilidade_tms_motor_ampliado.bin']
    compat = inputs[ROOT / 'data/compatibilidade_tms_motor_v6.bin']
    if len(compat) != 1026 * 29 or any(a & ~b for a, b in zip(prior_compat, compat)):
        raise PatchError('Compatibilidade anterior foi removida ou corrompida')
    if source[0xE06000:0xE06000 + len(prior_compat)] != prior_compat:
        raise PatchError('Matriz de compatibilidade na ROM de entrada divergente')

    # Verificações estritas dos sítios de correção antes de escrever.
    for site in MOVE_NAME_CAP_SITES:
        if source[site:site + 2] != b'\xc7\x22':
            raise PatchError(f'Teto de nome de golpe inesperado em {site:#x}')
    if source[0xE030BA:0xE030BC] != b'\x0f\x22':
        raise PatchError('Comprimento de cópia de gBattleTextBuff2 inesperado')
    for site in ICON_CLAMP_SITES:
        if source[site:site + 8] != bytes.fromhex('bc 23 5b 00 9c 42 52 d2'):
            raise PatchError(f'Clamp de ícone inesperado em {site:#x}')
    for site in ICON_TABLE_PTRS:
        if struct.unpack_from('<I', source, site)[0] != ROM + ORIG_ICON_TABLE:
            raise PatchError(f'Ponteiro de sItemIconTable inesperado em {site:#x}')
    for mov_at, add_at in RETURN_ARROW_CALLERS:
        if source[mov_at:mov_at + 2] != b'\x78\x20' or source[add_at:add_at + 2] != b'\xff\x30':
            raise PatchError(f'Chamador RETURN_TO_FIELD inesperado em {mov_at:#x}')

    found_cmd_ptrs = []
    pos = 0
    needle = struct.pack('<I', ROM + ORIG_CMD_TABLE)
    while True:
        idx = source.find(needle, pos, 0x1000000)
        if idx < 0:
            break
        if idx % 4 == 0:
            found_cmd_ptrs.append(idx)
        pos = idx + 4
    if tuple(found_cmd_ptrs) != CMD_TABLE_PTRS:
        raise PatchError(f'Referências a gBattleScriptingCommandsTable inesperadas: {found_cmd_ptrs}')
    if struct.unpack_from('<I', source, ORIG_CMD_TABLE + 5 * 4)[0] != 0x0900C001:
        raise PatchError('Hook anterior de damagecalc inesperado')

    payload = inputs[ROOT / 'patches/motor_v6/payload.bin']
    fling_table = inputs[ROOT / 'data/fling_itens_motor_v6.bin']
    free_checks = (
        (SCRIPTS_V6, 0x400),
        (DESC_TEXT_V6, 0x200),
        (ICON_TABLE_V6, 605 * 8),
        (CMD_TABLE_V6, 256 * 4),
        (FLING_TABLE_V6, len(fling_table)),
        (PAYLOAD_V6, len(payload)),
    )
    for at, size in free_checks:
        if source[at:at + size] != b'\xff' * size:
            raise PatchError(f'Área reservada ocupada em {at:#x}')
    for _tm, mid, *_rest in NEW_MOVES:
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

    # 1. Correções de teto de nomes (> 796 -> > 812) e truncamento seguro de gBattleTextBuff2.
    for site in MOVE_NAME_CAP_SITES:
        out[site:site + 2] = b'\xcb\x22'  # movs r2, #0xcb; lsls r2, #2 -> 812
    out[0xE030BA:0xE030BC] = b'\x0e\x22'  # 14 chars + '!' + 0xFF = 16 B (sem invadir Buff3)

    # 2. Tabela relocada de comandos de BattleScript + opcode 0xF8 (callasm) + payload/tabela Fling.
    out[CMD_TABLE_V6:CMD_TABLE_V6 + 248 * 4] = source[ORIG_CMD_TABLE:ORIG_CMD_TABLE + 248 * 4]
    struct.pack_into('<I', out, CMD_TABLE_V6 + 5 * 4, ENTRY_DAMAGE_V6)
    for op in range(248, 256):
        struct.pack_into('<I', out, CMD_TABLE_V6 + op * 4, ENTRY_CALLASM)
    for site in CMD_TABLE_PTRS:
        struct.pack_into('<I', out, site, ROM + CMD_TABLE_V6)
    out[FLING_TABLE_V6:FLING_TABLE_V6 + len(fling_table)] = fling_table
    out[PAYLOAD_V6:PAYLOAD_V6 + len(payload)] = payload

    # 3. Scripts de batalha customizados (efeitos 219..223) e Fling (move 374).
    script_defs = (
        (219, lambda at: bs_fling(source, at)),
        (220, lambda at: bs_steel_beam(source, at)),
        (221, lambda at: bs_poltergeist(at)),
        (222, lambda at: bs_supercell_slam(at)),
        (223, lambda at: bs_triple_axel(source, at)),
    )
    sc_cursor = SCRIPTS_V6
    for eff, make in script_defs:
        if struct.unpack_from('<I', source, complement.SCRIPT_TABLE + eff * 4)[0] != 0x081853A8:
            raise PatchError(f'Slot de efeito {eff} já ocupado')
        code = make(sc_cursor)
        if sc_cursor + len(code) > SCRIPTS_V6 + 0x400:
            raise PatchError('Scripts do motor_v6 excedem a reserva')
        out[sc_cursor:sc_cursor + len(code)] = code
        struct.pack_into('<I', out, complement.SCRIPT_TABLE + eff * 4, ROM + sc_cursor)
        sc_cursor = (sc_cursor + len(code) + 3) & ~3

    if source[complement.MOVE + 374 * 12:complement.MOVE + 375 * 12] != bytes((0, 1, 17, 100, 10, 0, 0, 0, 50, 0, 0, 0)):
        raise PatchError('Registro anterior de Fling (374) divergente')
    out[complement.MOVE + 374 * 12:complement.MOVE + 375 * 12] = bytes((219, 1, 17, 100, 10, 100, 0, 0, 0x32, 0, 0, 0))
    struct.pack_into('<H', out, previous.NEW_MOVE_TABLE + (417 - 289) * 2, 374)

    # 4. Novos golpes 808..812 e ligação em NEW_MOVE_TABLE.
    desc_cursor = DESC_TEXT_V6
    for tm, mid, _api, name_str, fields9, cat, desc_str in NEW_MOVES:
        out[complement.MOVE + mid * 12:complement.MOVE + (mid + 1) * 12] = bytes(fields9) + b'\x00\x00\x00'
        enc_name = previous.text(name_str)
        if len(enc_name) > 17:
            raise PatchError(f'Nome de golpe excede 17 bytes: {name_str}')
        out[complement.NAMES + mid * 17:complement.NAMES + (mid + 1) * 17] = enc_name + bytes(17 - len(enc_name))
        out[complement.CATEGORY + mid] = cat
        struct.pack_into('<I', out, complement.ANIM + mid * 4, 0x08175F3A)
        enc_desc = previous.text(desc_str)
        if desc_cursor + len(enc_desc) > DESC_TEXT_V6 + 0x200:
            raise PatchError('Descrições de golpes excedem a reserva')
        out[desc_cursor:desc_cursor + len(enc_desc)] = enc_desc
        struct.pack_into('<I', out, complement.DESC + (mid - 1) * 4, ROM + desc_cursor)
        desc_cursor += len(enc_desc)

        move_slot = previous.NEW_MOVE_TABLE + (374 + tm - 289) * 2
        if struct.unpack_from('<H', source, move_slot)[0] != 0:
            raise PatchError(f'TM{tm:03d} já tinha golpe associado')
        struct.pack_into('<H', out, move_slot, mid)

    # 5. Matriz de compatibilidade TM, lista da loja (210 itens) e descrições USO UNICO.
    out[0xE06000:0xE06000 + len(compat)] = compat
    out[ITEM_TEXT_START:ITEM_TEXT_END] = b'\xff' * (ITEM_TEXT_END - ITEM_TEXT_START)
    txt_cursor = ITEM_TEXT_START
    for tm, mid in sorted(available.items()):
        entry = out[complement.NAMES + mid * 17:complement.NAMES + (mid + 1) * 17]
        if 0xFF not in entry:
            raise PatchError(f'Nome do golpe {mid} sem terminador')
        move_name = entry[:entry.index(0xFF)]
        item_desc = previous.text('GOLPE ')[:-1] + move_name + previous.text('\nUSO UNICO')
        if txt_cursor + len(item_desc) > ITEM_TEXT_END:
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

    # 6. Learnsets por nível atualizados (+23 entradas de Fling, preservando 100% das anteriores).
    prior_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / 'data/learnsets_gen1_9_complemento.csv'].decode('utf-8'))))
    cur_lv = list(csv.DictReader(io.StringIO(inputs[ROOT / 'data/learnsets_motor_v6.csv'].decode('utf-8'))))
    lv_key = lambda r: (int(r['species']), int(r['level']), int(r['internal_move']), int(r['api_move']))
    if len(cur_lv) != 14323 or not set(map(lv_key, prior_lv)).issubset(set(map(lv_key, cur_lv))):
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

    # 7. Ícones de itens para 375..603 (disco TM + paleta por tipo) e seta RETURN_TO_FIELD em 604.
    out[ICON_TABLE_V6:ICON_TABLE_V6 + 375 * 8] = source[ORIG_ICON_TABLE:ORIG_ICON_TABLE + 375 * 8]
    for row in rows:
        tm = int(row['tm'])
        item_id = 374 + tm
        mid = int(row['internal_move'])
        mtype = out[complement.MOVE + mid * 12 + 2] if mid > 0 else RESERVED_TM_TYPES[tm]
        pal = TYPE_TM_PALETTES[mtype]
        struct.pack_into('<II', out, ICON_TABLE_V6 + item_id * 8, TM_DISC_PIC, pal)
    out[ICON_TABLE_V6 + 604 * 8:ICON_TABLE_V6 + 605 * 8] = source[ORIG_ICON_TABLE + 375 * 8:ORIG_ICON_TABLE + 376 * 8]

    for site in ICON_CLAMP_SITES:
        out[site:site + 8] = bytes.fromhex('97 23 9b 00 9c 42 52 d8')  # r4 > 604 -> clamp 0
    for site in ICON_TABLE_PTRS:
        struct.pack_into('<I', out, site, ROM + ICON_TABLE_V6)
    for mov_at, add_at in RETURN_ARROW_CALLERS:
        out[mov_at:mov_at + 2] = b'\x97\x20'  # movs r0, #0x97
        out[add_at:add_at + 2] = b'\x80\x00'  # lsls r0, r0, #2 (= 604)

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
        print('Motor parcial v6: 210/229 TMs SV habilitadas; 19 TMs e trocas seguem pendentes.')
    except (OSError, ValueError) as exc:
        print(f'[ERRO] {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
