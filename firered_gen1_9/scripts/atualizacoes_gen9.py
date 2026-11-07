#!/usr/bin/env python3
"""Acrescenta TMs selecionadas e efeitos testados a uma nova cópia de ROM.

Aceita somente a versão exata de golpes por nível deste projeto. A entrada e
os saves não são modificados. Não garante regras completas de Gen 9.
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
from scripts import efeitos_gen9 as effects, gerar_catalogo_golpes as catalog, golpes_gen9 as level  # noqa: E402
from scripts.treino_ev import write_new_file  # noqa: E402

BASE_SHA256 = '412bcd89214d4126d92f6c2256a56227c6f30fa138e0b262ef287f5b12b3997b'
OUTPUT_SHA256 = '36cf2355789eca9273c2e4110606872fff8ab8ece82dae9ee090cd3bfa0546db'
INPUTS = {
    ROOT / 'patches/atualizacoes_gen9/payload.bin': '9b0ff4c61e7f5ecfe0fdcb7c07e0ecda1b5c07b845d48ed68e812d162b427b5c',
    ROOT / 'data/learnsets_gen1_9_atualizados.csv': 'afa56c74cc17df17c5c20d804d2bd063e75cebe422b7397cb0a3efdaeb8e5b59',
    ROOT / 'data/compatibilidade_tms_gen9.bin': 'd4e18ba8db7394306e3d6fce0f539f142a2323192a4dd28b6460778682364fb4',
    ROOT / 'data/tms_gen9.csv': '92d0d7940ee29e15a6d0c21499ab162086db2f61df97d326ea8a9340bb5926b5',
    ROOT / 'data/learnsets_gen1_9.csv': level.CATALOG_SHA256,
}
ROM_START = 0x08000000
FREE_REGIONS = ((0xE03FD0, 0xE05000), (0xE06000, 0xE0F000), (0xE11000, 0xE19000))
HOOKS = ((0x0F8460, '09 04 70 b5 12 06 0c 0c', 0),
         (0x14B670, 'f0 b5 22 4c 0d 04 06 00', 8),
         (0x13BB98, '2a 4e 21 39 02 23 02 22', 16),
         (0x14D2E4, '27 00 06 01 11 4b 21 3f', 24),
         (0x14D484, '22 3b ff 3b 1b 04 1b 0c', 32))
ITEM_BASE = 0x62B708
NEW_ITEMS = 0xE11000
ITEM_SIZE = 44
NEW_MOVE_TABLE = 0xE18000
SHOP_LIST = 0xE18300
SHOP_SCRIPT = 0xE18700
ITEM_POINTERS = (0x1C8, 0xC67D4, 0xC68B0, 0xC6994, 0xC6B24, 0xC6BB8, 0xC6BE4, 0xC7158,
                 0xC7218, 0xC7238, 0xC7258, 0xC7278, 0xC7298, 0xC72B8, 0xC72DC, 0xC72FC,
                 0xC731C, 0xC733C, 0xC735C, 0xC73A0)
MOVE_POINTERS = (0xF84F8, 0xFCCE0, 0xFCDA8, 0xFD9C8, 0xFDC20)
THRESHOLDS = ((0xC679C, 0xC679E), (0xC6848, 0xC6850), (0xC68FC, 0xC6904),
              (0xC69A4, 0xC69AC), (0xC6B38, 0xC6B40), (0xC6BC8, 0xC6BCE),
              (0xC7100, 0xC7108), (0xC71E8, 0xC71F0), (0xC71FC, 0xC7202),
              (0xC721C, 0xC7222), (0xC723C, 0xC7242), (0xC725C, 0xC7262),
              (0xC727C, 0xC7282), (0xC729C, 0xC72A2), (0xC72C0, 0xC72C6),
              (0xC72E0, 0xC72E6), (0xC7300, 0xC7306), (0xC7320, 0xC7326),
              (0xC7340, 0xC7346), (0xC7364, 0xC736A), (0xC7384, 0xC738A),
              (0xC73A4, 0xC73AA))


class PatchError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text(message: str) -> bytes:
    result = bytearray()
    specials = {' ': 0, '-': 0xAE, '.': 0xAD, '?': 0xAC, '!': 0xAB, '\n': 0xFE}
    for c in message:
        if 'A' <= c <= 'Z':
            result.append(0xBB + ord(c) - ord('A'))
        elif '0' <= c <= '9':
            result.append(0xA1 + ord(c) - ord('0'))
        elif c in specials:
            result.append(specials[c])
        else:
            raise PatchError(f'Caractere não suportado no texto: {c!r}')
    return bytes(result) + b'\xff'


def read_checked_inputs() -> dict[Path, bytes]:
    data = {}
    for path, expected in INPUTS.items():
        content = path.read_bytes()
        if digest(content) != expected:
            raise PatchError(f'Dados alterados ou incompatíveis: {path.name}')
        data[path] = content
    return data


def validate_rom(rom: bytes):
    if len(rom) != 0x1000000 or rom[0xAC:0xB0] != b'BPRE' or digest(rom) != BASE_SHA256:
        raise PatchError('ROM incompatível: use a cópia anterior de golpes por nível identificada')
    for lo, hi in FREE_REGIONS:
        if rom[lo:hi] != b'\xff' * (hi - lo):
            raise PatchError(f'Região reservada ocupada: {lo:#x}..{hi:#x}')
    for i, (value,) in enumerate(struct.iter_unpack('<I', rom)):
        if any(ROM_START + lo <= value < ROM_START + hi for lo, hi in FREE_REGIONS):
            raise PatchError(f'Referência alinhada a área reservada em {4*i:#x}')
    for at, original, _ in HOOKS:
        if rom[at:at + 8] != bytes.fromhex(original):
            raise PatchError(f'Trecho original inesperado em {at:#x}')
    for at in ITEM_POINTERS:
        if rom[at:at + 4] != struct.pack('<I', ROM_START + ITEM_BASE):
            raise PatchError(f'Referência inesperada à tabela de itens em {at:#x}')
    if rom[0xC7380:0xC7384] != struct.pack('<I', ROM_START + ITEM_BASE + 32):
        raise PatchError('Referência a campo de itens inesperada')
    for at in MOVE_POINTERS:
        if rom[at:at + 4] != struct.pack('<I', 0x08669894):
            raise PatchError(f'Referência a movimentos de TMs inesperada: {at:#x}')
    if rom[0x7C082C:0x7C0830] != struct.pack('<I', 0x0818E23C):
        raise PatchError('Placa da casa em Pallet não corresponde')


def parse_machines(data: bytes, rom: bytes):
    rows = list(csv.DictReader(io.StringIO(data.decode('utf-8'), newline='')))
    if len(rows) != 229:
        raise PatchError('Catálogo de TMs incompleto')
    available = {}
    for number, row in enumerate(rows, 1):
        mid, api = int(row['internal_move']), int(row['api_move'])
        if int(row['tm']) != number or int(row['item_id']) != 374 + number:
            raise PatchError(f'Numeração inválida da TM{number:03}')
        reason = catalog.usable(rom, mid)
        if row['motivo'] != reason or row['status'] != ('nao_disponivel' if reason else 'disponivel'):
            raise PatchError(f'Classificação inconsistente da TM{number:03}')
        if mid and api not in catalog.ALIASES and catalog.normalize(row['name']) != catalog.normalize(catalog.move_name(rom, mid)):
            raise PatchError(f'Nome ou ID interno errado na TM{number:03}')
        if not reason:
            available[number] = mid
    if len(available) != 189:
        raise PatchError('Quantidade inesperada de TMs disponibilizadas')
    return available


def parse_levels(data: bytes, old_data: bytes, rom: bytes):
    rows = list(csv.DictReader(io.StringIO(data.decode('utf-8'), newline='')))
    old_rows = list(csv.DictReader(io.StringIO(old_data.decode('utf-8'), newline='')))
    lists = {sid: [] for sid in range(1, 1026)}
    seen = set()
    for row in rows:
        sid, lv, mid = int(row['species']), int(row['level']), int(row['internal_move'])
        api = int(row['api_move'])
        key = (sid, lv, mid, api)
        if sid not in lists or not 0 <= lv <= 100 or catalog.usable(rom, mid):
            raise PatchError(f'Aprendizado inválido: {key}')
        if key in seen or (lists[sid] and lv < lists[sid][-1][0]):
            raise PatchError(f'Aprendizado duplicado ou fora de ordem: {key}')
        if api not in catalog.ALIASES and catalog.normalize(row['name']) != catalog.normalize(catalog.move_name(rom, mid)):
            raise PatchError(f'Nome de movimento inválido: {key}')
        seen.add(key)
        lists[sid].append((lv, mid))
    previous = {(int(r['species']), int(r['level']), int(r['internal_move']), int(r['api_move'])) for r in old_rows}
    if len(rows) != 14184 or len(seen - previous) != 166 or previous - seen:
        raise PatchError('A atualização não preserva os aprendizados anteriores')
    for sid, entries in lists.items():
        if not entries or len(entries) > 50 or not any(lv <= 1 for lv, _ in entries):
            raise PatchError(f'Lista de espécie {sid} inválida')
    return lists


def validate_compat(data: bytes, available: dict[int, int]):
    if len(data) != 1026 * 29 or any(data[:29]):
        raise PatchError('Matriz de compatibilidade incompleta')
    for species in range(1, 1026):
        row = data[species * 29:(species + 1) * 29]
        if row[28] & 0xE0:
            raise PatchError('Bits reservados de compatibilidade definidos')
        for tm in range(1, 230):
            if tm not in available and row[(tm - 1) // 8] & (1 << ((tm - 1) % 8)):
                raise PatchError(f'TM indisponível {tm} com compatibilidade')


def build(rom: bytes, inputs: dict[Path, bytes] | None = None) -> bytes:
    validate_rom(rom)
    inputs = read_checked_inputs() if inputs is None else inputs
    for path, expected in INPUTS.items():
        if path not in inputs or digest(inputs[path]) != expected:
            raise PatchError(f'Dados alterados ou ausentes: {path.name}')
    out = bytearray(effects.apply_effects(rom))
    payload = inputs[ROOT / 'patches/atualizacoes_gen9/payload.bin']
    machines = parse_machines(inputs[ROOT / 'data/tms_gen9.csv'], bytes(out))
    compat = inputs[ROOT / 'data/compatibilidade_tms_gen9.bin']
    validate_compat(compat, machines)
    lists = parse_levels(inputs[ROOT / 'data/learnsets_gen1_9_atualizados.csv'],
                         inputs[ROOT / 'data/learnsets_gen1_9.csv'], bytes(out))
    if not 0 < len(payload) <= 0xC00:
        raise PatchError('Payload de TMs excede área reservada')
    out[0xE04400:0xE04400 + len(payload)] = payload
    out[0xE06000:0xE06000 + len(compat)] = compat
    for at, _original, vector in HOOKS:
        out[at:at + 8] = bytes.fromhex('00 4b 18 47') + struct.pack('<I', 0x08E04401 + vector)

    for at in ITEM_POINTERS:
        struct.pack_into('<I', out, at, ROM_START + NEW_ITEMS)
    struct.pack_into('<I', out, 0xC7380, ROM_START + NEW_ITEMS + 32)
    for at, shift_at in THRESHOLDS:
        reg = rom[at + 1]
        shifts = {0x21: (b'\x49\x00', b'\x89\x00'), 0x22: (b'\x52\x00', b'\x92\x00'),
                  0x23: (b'\x5b\x00', b'\x9b\x00')}
        if rom[at] != 0xBB or reg not in shifts or rom[shift_at:shift_at + 2] != shifts[reg][0]:
            raise PatchError(f'Limite de item inesperado em {at:#x}')
        out[at] = 0x97  # 151 << 2 = 604, último item (604 é dummy)
        out[shift_at:shift_at + 2] = shifts[reg][1]
    for at in (0xC7370, 0xC73B0):
        if rom[at:at + 4] != bytes.fromhex('4b 3b ff 3b'):
            raise PatchError('Cálculo do tamanho de item inesperado')
        out[at:at + 4] = bytes.fromhex('2c 23 c0 46')  # movs r3,44; nop

    out[NEW_ITEMS:NEW_ITEMS + 375 * ITEM_SIZE] = rom[ITEM_BASE:ITEM_BASE + 375 * ITEM_SIZE]
    # Descrição individual permite saber o golpe ANTES de comprar, mesmo na
    # loja normal, cuja lista só mostra o número da TM. Fica após o bitset.
    desc_cursor = (0xE06000 + len(compat) + 3) & ~3
    unavailable_at = 0xE18A00
    unavailable = text('TM NAO DISPONIVEL.')
    out[unavailable_at:unavailable_at + len(unavailable)] = unavailable
    for number in range(1, 230):
        item = 374 + number
        at = NEW_ITEMS + item * ITEM_SIZE
        record = bytearray(rom[ITEM_BASE + 289 * ITEM_SIZE:ITEM_BASE + 290 * ITEM_SIZE])
        name = text(f'TM9-{number:03}')
        record[:14] = name + bytes(14 - len(name))
        struct.pack_into('<HH', record, 14, item, 3000)
        if number in machines:
            move = machines[number]
            name_bytes = rom[0x235930 + move * 17:0x235930 + (move + 1) * 17]
            try:
                move_name = name_bytes[:name_bytes.index(0xff)]
            except ValueError as exc:
                raise PatchError(f'Nome de golpe sem terminador: {move}') from exc
            description = text('GOLPE ')[:-1] + move_name + text('\nREUTILIZAVEL')
            if desc_cursor + len(description) > 0xE0F000:
                raise PatchError('Descrições de TMs excedem a região reservada')
            out[desc_cursor:desc_cursor + len(description)] = description
            ptr = desc_cursor
            desc_cursor += len(description)
        else:
            ptr = unavailable_at
        struct.pack_into('<I', record, 20, ROM_START + ptr)
        out[at:at + ITEM_SIZE] = record
    out[NEW_ITEMS + 604 * ITEM_SIZE:NEW_ITEMS + 605 * ITEM_SIZE] = out[NEW_ITEMS:NEW_ITEMS + ITEM_SIZE]

    # A tabela é indexada por item - TM01, inclusive nos chamadores que o
    # compilador antigo incorporou por inline. As primeiras 58 entradas são
    # copiadas literalmente; as HMs conservam seus números e movimentos.
    out[NEW_MOVE_TABLE:NEW_MOVE_TABLE + 116] = rom[0x669894:0x669894 + 116]
    for number in range(1, 230):
        at = NEW_MOVE_TABLE + (374 + number - 289) * 2
        struct.pack_into('<H', out, at, machines.get(number, 0))
    for at in MOVE_POINTERS:
        struct.pack_into('<I', out, at, ROM_START + NEW_MOVE_TABLE)
    products = b''.join(struct.pack('<H', 374 + n) for n in sorted(machines)) + b'\x00\x00'
    out[SHOP_LIST:SHOP_LIST + len(products)] = products
    prompt = text('VER A LOJA DE TMS DA\nNOVA GERACAO?')
    hello = text('LOJA DE TMS MODERNAS.')
    out[0xE18800:0xE18800 + len(prompt)] = prompt
    out[0xE18840:0xE18840 + len(hello)] = hello
    # A placa original continua exibindo seu texto; somente se o jogador
    # confirmar SIM, abre a loja. Não altera objetos nem scripts da história.
    event = bytearray((0x69, 0x0F, 0))  # lockall; loadword
    event.extend(struct.pack('<I', 0x081A6671))  # texto original da placa
    event.extend((0x09, 0x03, 0x0F, 0))  # msgbox sign; loadword
    event.extend(struct.pack('<I', 0x08E18800))
    event.extend((0x09, 0x05, 0x21))  # yes/no; compare
    event.extend(struct.pack('<HH', 0x800D, 1))
    event.extend((0x06, 0x05))  # goto if not equal
    fixup = len(event)
    event.extend(bytes(4))
    event.extend((0x68, 0x67))  # closemessage; message
    event.extend(struct.pack('<I', 0x08E18840))
    event.extend((0x66, 0x86))  # waitmessage; pokemart
    event.extend(struct.pack('<I', ROM_START + SHOP_LIST))
    struct.pack_into('<I', event, fixup, ROM_START + SHOP_SCRIPT + len(event))
    event.extend((0x6B, 0x02))  # releaseall; end
    out[SHOP_SCRIPT:SHOP_SCRIPT + len(event)] = event
    struct.pack_into('<I', out, 0x7C082C, ROM_START + SHOP_SCRIPT)

    tables = level.build_tables(lists)
    out[level.TABLE:level.TABLE + len(tables)] = tables
    if out[NEW_ITEMS:NEW_ITEMS + 375 * ITEM_SIZE] != rom[ITEM_BASE:ITEM_BASE + 375 * ITEM_SIZE]:
        raise PatchError('Itens antigos não foram preservados')
    if out[NEW_MOVE_TABLE:NEW_MOVE_TABLE + 116] != rom[0x669894:0x669894 + 116]:
        raise PatchError('TMs/HMs antigas não foram preservadas')
    return bytes(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--saida', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.rom.resolve() == args.saida.resolve() or args.saida.exists():
            raise PatchError('A saída deve ser um arquivo novo, diferente da entrada')
        source = args.rom.read_bytes()
        result = build(source)
        if OUTPUT_SHA256 and digest(result) != OUTPUT_SHA256:
            raise PatchError('Hash da saída não corresponde à versão testada')
        write_new_file(args.rom, args.saida, result)
        print(f'Entrada preservada: {digest(source)}')
        print(f'Nova ROM: {args.saida} | SHA-256 {digest(result)}')
        print('189 TMs modernas; 40 ainda indisponíveis. Estojo mantém capacidade de 58.')
        return 0
    except (OSError, PatchError, ValueError) as exc:
        print(f'[ERRO] {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
