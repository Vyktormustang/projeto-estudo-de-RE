#!/usr/bin/env python3
"""Cria cópia expandida, com complementos PARCIAIS de movimentos/TMs.

Só aceita a última ROM deste projeto pelo SHA-256. Nunca modifica a entrada
nem arquivos de save. Não afirma implementar todas as regras de Scarlet/Violet.
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
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts import efeitos_gen9 as effects, golpes_gen9 as level, atualizacoes_gen9 as prev  # noqa: E402
from scripts.gerar_complemento_gen9 import NEW_MOVES, DYNAMIC_TMS  # noqa: E402
from scripts.treino_ev import write_new_file  # noqa: E402

BASE_SHA256 = '36cf2355789eca9273c2e4110606872fff8ab8ece82dae9ee090cd3bfa0546db'
OUTPUT_SHA256 = '6155b6a5fe62528b7b67836d3a47f32b1cb3b1a71c1f2b59bfa7a68af0100d67'
INPUTS = {
    ROOT / 'data/learnsets_gen1_9_complemento.csv': 'a6c08fe9c4cbfd6dfa9e36b09a5a11b9744f3904ce3a3dabad0d5f695b3e742c',
    ROOT / 'data/compatibilidade_tms_complemento.bin': '23de53c08991baa31623eb184f277420e743770965b920294615e01e61d278d3',
    ROOT / 'data/tms_gen9_complemento.csv': '074ccc0865d2fc2d0f298859ad721cbbd0fd4ba99da2aebc119dd85033edf394',
    ROOT / 'data/pesos_gen1_9.bin': 'b1459c11aefd1e73c0584ab4c3557c94943d5739cf269506a9c3667b6093a7b9',
    ROOT / 'patches/complemento_gen9/payload.bin': '3e54b4263b312584f11a7809b39093c590848cb1a2b35c6668cc9427752b22c4',
    ROOT / 'data/learnsets_gen1_9_atualizados.csv': prev.INPUTS[ROOT / 'data/learnsets_gen1_9_atualizados.csv'],
    ROOT / 'data/compatibilidade_tms_gen9.bin': prev.INPUTS[ROOT / 'data/compatibilidade_tms_gen9.bin'],
}
ROM = 0x08000000
ORIG_MOVE = 0x696F70
ORIG_NAMES = 0x235930
ORIG_ANIM = 0x174CB4
ORIG_DESC = 0x661668  # pointers para movimentos 1..796
ORIG_CATEGORY = 0x6994CC  # 0 físico, 1 especial, 2 status
ORIG_SCRIPT = 0x185050
OLD_COUNT = 797
COUNT = OLD_COUNT + len(NEW_MOVES)
MOVE = 0x1000000
NAMES = 0x1003000
ANIM = 0x1007000
DESC = 0x1008000
DESC_TEXT = 0x1009000
SCRIPT_TABLE = 0x100A000
SCRIPTS = 0x100B000
CATEGORY = 0x100E000
SIZE = 0x2000000

# TM -> (efeito, poder, tipo interno, precisão, PP, chance, alvo, prioridade,
# flags); as categorias físico/especial ficam em tabela separada.
NEW_DATA = {
    20:  (64, 50, 12, 100, 20,100, 0, 0,0x33),  # Trailblaze, Vel +1
    21:  (70, 50,  6, 100, 20,100, 0, 0,0x33),  # Pounce, Vel alvo -1
    22:  (68, 50, 11, 100, 20,100, 0, 0,0x12),  # Chilling Water, Atq alvo -1
    144: ( 0, 80, 10, 100, 10,  0, 0, 0,0x12),  # Pledges sem combinação
    145: ( 0, 80, 11, 100, 10,  0, 0, 0,0x12),
    146: ( 0, 80, 12, 100, 10,  0, 0, 0,0x12),
    169: (204,130,16,  90,  5,100, 0, 0,0x12), # Draco Meteor, SpA -2
    171: ( 0, 80,  0, 100, 10,  0, 0, 0,0x12), # Tera Blast sem Tera
    194: ( 0, 55, 12, 100, 20,  0, 0, 0,0x33), # Grassy Glide sem terreno
    215: ( 4, 70,  4, 100, 10, 30, 0, 0,0x12), # Scorching Sands
}
NEW_CATEGORY = {20: 0, 21: 0, 22: 1, 144: 1, 145: 1, 146: 1,
                169: 1, 171: 1, 194: 0, 215: 1}
DESC_STRINGS = {
    20: 'DANO E AUMENTA\nVELOCIDADE.',
    21: 'DANO E REDUZ\nVELOCIDADE DO ALVO.',
    22: 'DANO E REDUZ\nATAQUE DO ALVO.',
    144: 'DANO DE FOGO.\nSEM COMBINACAO.',
    145: 'DANO DE AGUA.\nSEM COMBINACAO.',
    146: 'DANO DE GRAMA.\nSEM COMBINACAO.',
    169: 'DANO FORTE. REDUZ\nATAQUE ESPECIAL.',
    171: 'DANO NORMAL.\nSEM TERA.',
    194: 'DANO DE GRAMA.\nSEM PRIORIDADE.',
    215: 'DANO. PODE CAUSAR\nQUEIMADURA.',
}

class PatchError(ValueError): pass


def digest(data: bytes) -> str: return hashlib.sha256(data).hexdigest()


def checked_inputs():
    data = {}
    for path, expected in INPUTS.items():
        raw = path.read_bytes()
        if digest(raw) != expected: raise PatchError(f'Arquivo de dados incompatível: {path.name}')
        data[path] = raw
    return data


def shell_smash(base: int) -> bytes:
    """-1 Def/SpDef e +2 Atk/SpAtk/Speed, com limites e mensagens."""
    s = effects.BattleScript(base)
    s.emit(0x00, 0x02, 0x03)  # cancela, nome, PP
    for stat in (1, 4): s.jumpifstat(1, 3, stat, 12, 'animate')
    s.jumpifstat(1, 0, 3, 12, 0x0818708F)  # todos os aumentos no limite
    s.label('animate')
    s.emit(0x09, 0x0A)
    s.setbyte(0x02021823, 0)
    for i, (stat, delta, lower) in enumerate(((2,1,True),(5,1,True),
                                              (1,2,False),(4,2,False),(3,2,False))):
        s.emit(0x48, 1, 1 << stat, 1 if lower else 0)
        s.setbyte(0x02021822, stat | delta << 4 | (0x80 if lower else 0))
        s.emit(0x89, 0x41)
        s.ptr(f'next{i}')
        s.emit(0x29, 0x00)
        s.ptr(0x020216C5)
        s.emit(2)
        s.ptr(f'next{i}')
        s.emit(0x13)
        s.ptr(0x082085AC if lower else 0x082085A0)
        s.emit(0x12, 0x40, 0)
        s.label(f'next{i}')
    s.goto(0x081853F6)
    return s.finish()


def _replace_pointers(data: bytearray, original: int, replacement: int, expected: int):
    needle = struct.pack('<I', original)
    # Apenas a ROM de entrada. Não examinar dados recém-copiados ou tabelas.
    sites = []
    start = 0
    while True:
        pos = data.find(needle, start, 0x1000000)
        if pos < 0: break
        if pos % 4: raise PatchError(f'Ponteiro não alinhado inesperado em {pos:#x}')
        sites.append(pos); start = pos + 4
    if len(sites) != expected: raise PatchError(f'{original:#x}: {len(sites)} referências, esperadas {expected}')
    for pos in sites: struct.pack_into('<I', data, pos, replacement)
    return sites


def _rows(raw: bytes): return list(csv.DictReader(io.StringIO(raw.decode('utf-8'), newline='')))


def build(source: bytes, inputs=None) -> bytes:
    if len(source) != 0x1000000 or source[0xAC:0xB0] != b'BPRE' or digest(source) != BASE_SHA256:
        raise PatchError('A entrada não é a ROM anterior identificada; nada foi alterado')
    inputs = checked_inputs() if inputs is None else inputs
    for path, expected in INPUTS.items():
        if path not in inputs or digest(inputs[path]) != expected: raise PatchError(f'Dado inválido: {path.name}')
    out = bytearray(source) + b'\xff' * (SIZE - len(source))
    # Primeiro copiar; ponteiros antigos serão alterados depois.
    out[MOVE:MOVE + OLD_COUNT * 12] = source[ORIG_MOVE:ORIG_MOVE + OLD_COUNT * 12]
    out[NAMES:NAMES + OLD_COUNT * 17] = source[ORIG_NAMES:ORIG_NAMES + OLD_COUNT * 17]
    out[ANIM:ANIM + OLD_COUNT * 4] = source[ORIG_ANIM:ORIG_ANIM + OLD_COUNT * 4]
    out[DESC:DESC + (OLD_COUNT - 1) * 4] = source[ORIG_DESC:ORIG_DESC + (OLD_COUNT - 1) * 4]
    out[CATEGORY:CATEGORY + OLD_COUNT] = source[ORIG_CATEGORY:ORIG_CATEGORY + OLD_COUNT]
    out[SCRIPT_TABLE:SCRIPT_TABLE + 214 * 4] = source[ORIG_SCRIPT:ORIG_SCRIPT + 214 * 4]
    for effect in range(214, 256): struct.pack_into('<I', out, SCRIPT_TABLE + effect * 4, 0x081853A8)

    cursor = SCRIPTS
    definitions = (
        (214, 503, lambda at: shell_smash(at)),
        (215, 474, lambda at: effects.stages(at, ((3, 2),))),
        (216, 423, lambda at: effects.damage_with_effects(source, at, (4, 8))),
        (217, 422, lambda at: effects.damage_with_effects(source, at, (5, 8))),
        (218, 370, lambda at: effects.damage_with_effects(source, at, (0xD7, 0xDA))),
    )
    for eff, mid, make in definitions:
        code = make(cursor)
        if cursor + len(code) > 0x100C000: raise PatchError('Scripts excedem o espaço')
        out[cursor:cursor+len(code)] = code
        struct.pack_into('<I', out, SCRIPT_TABLE + eff * 4, ROM + cursor)
        out[MOVE + mid*12] = eff
        if mid in (422, 423): out[MOVE + mid*12 + 5] = 10
        if mid == 370: out[MOVE + mid*12 + 5] = 100
        cursor = (cursor + len(code) + 3) & ~3
    # Dual Wingbeat possui dois acertos, reutilizando a rotina testada do jogo.
    out[MOVE + 709*12] = 44

    # O opcode damagecalc passa por uma rotina que trata os poderes e
    # atributos de alguns golpes específicos; os demais seguem o original.
    payload = inputs[ROOT / 'patches/complemento_gen9/payload.bin']
    weights = inputs[ROOT / 'data/pesos_gen1_9.bin']
    if not 0 < len(payload) < 0x1000 or len(weights) != 1026 * 2:
        raise PatchError('Código ou pesos fora dos limites')
    if struct.unpack_from('<I', source, 0x209804)[0] != 0x0805861D:
        raise PatchError('Comando de cálculo de dano inesperado')
    out[0x100C000:0x100C000+len(payload)] = payload
    out[0x100D000:0x100D000+len(weights)] = weights
    struct.pack_into('<I', out, 0x209804, 0x0900C001)

    text_cursor = DESC_TEXT
    for tm, mid, _api, name, _note in NEW_MOVES:
        if mid != OLD_COUNT + list(x[1] for x in NEW_MOVES).index(mid): raise PatchError('IDs não sequenciais')
        encoded = prev.text(name.upper())
        if len(encoded) > 17: raise PatchError(f'Nome não cabe: {name}')
        out[NAMES + mid*17:NAMES + (mid+1)*17] = encoded + bytes(17-len(encoded))
        fields = NEW_DATA[tm]
        out[MOVE + mid*12:MOVE + (mid+1)*12] = bytes(fields) + b'\x00\x00\x00'
        out[CATEGORY + mid] = NEW_CATEGORY[tm]
        # Animação genérica já usada pela ROM para movimentos pós-Gen III.
        struct.pack_into('<I', out, ANIM + mid*4, 0x08175F3A)
        description = prev.text(DESC_STRINGS[tm])
        if text_cursor + len(description) > 0x100A000: raise PatchError('Descrições excedem a região')
        out[text_cursor:text_cursor+len(description)] = description
        struct.pack_into('<I', out, DESC + (mid-1)*4, ROM + text_cursor)
        text_cursor += len(description)

    # Todos os pontos identificados de acesso às quatro tabelas (inclusive o
    # cabeçalho e os hooks anteriores de nomes/PP). Referências a elementos
    # individuais permanecem na tabela anterior, cujos registros não mudam.
    _replace_pointers(out, ROM + ORIG_MOVE, ROM + MOVE, 101)
    _replace_pointers(out, ROM + ORIG_MOVE + 4, ROM + MOVE + 4, 2)
    _replace_pointers(out, ROM + ORIG_NAMES, ROM + NAMES, 38)
    _replace_pointers(out, ROM + ORIG_ANIM, ROM + ANIM, 1)
    _replace_pointers(out, ROM + ORIG_DESC, ROM + DESC, 2)
    _replace_pointers(out, ROM + ORIG_CATEGORY, ROM + CATEGORY, 3)
    _replace_pointers(out, ROM + ORIG_SCRIPT, ROM + SCRIPT_TABLE, 6)

    old_rows = _rows(inputs[ROOT / 'data/learnsets_gen1_9_atualizados.csv'])
    rows = _rows(inputs[ROOT / 'data/learnsets_gen1_9_complemento.csv'])
    keys = lambda r: (int(r['species']), int(r['level']), int(r['internal_move']), int(r['api_move']))
    if len(rows) != 14300 or not set(map(keys, old_rows)).issubset(map(keys, rows)):
        raise PatchError('Aprendizados anteriores não foram preservados')
    lists = {sid: [] for sid in range(1, 1026)}
    for row in rows:
        sid, lv, mid, _api = keys(row)
        if sid not in lists or not 0 <= lv <= 100 or not 0 < mid < COUNT:
            raise PatchError(f'Entrada de nível inválida: {row}')
        lists[sid].append((lv, mid))
    if any(not vals or len(vals) > 50 or vals != sorted(vals, key=lambda v:v[0]) for vals in lists.values()):
        raise PatchError('Listas de nível fora dos limites')
    tables = level.build_tables(lists)
    out[level.TABLE:level.TABLE + len(tables)] = tables

    compat = inputs[ROOT / 'data/compatibilidade_tms_complemento.bin']
    old_compat = inputs[ROOT / 'data/compatibilidade_tms_gen9.bin']
    if len(compat) != 1026*29 or any(a & ~b for a,b in zip(old_compat, compat)):
        raise PatchError('Compatibilidade anterior foi removida')
    out[0xE06000:0xE06000+len(compat)] = compat
    machines = _rows(inputs[ROOT / 'data/tms_gen9_complemento.csv'])
    if len(machines) != 229: raise PatchError('Catálogo de TMs inválido')
    available = {int(r['tm']): int(r['internal_move']) for r in machines if r['status'] == 'disponivel'}
    if len(available) != 203: raise PatchError('Quantidade inesperada de TMs')
    additions = [(tm, mid, name) for tm, mid, _api, name, _note in NEW_MOVES]
    additions += [(tm, mid, name) for tm, (mid, name, _note) in DYNAMIC_TMS.items()]
    for tm, mid, name in additions:
        if available.get(tm) != mid: raise PatchError('TM nova mapeada incorretamente')
        at = prev.NEW_MOVE_TABLE + (374 + tm - 289)*2
        if struct.unpack_from('<H', source, at)[0] != 0: raise PatchError('TM já era ocupada')
        struct.pack_into('<H', out, at, mid)
        name_bytes = prev.text(name.upper())[:-1]
        desc = prev.text('GOLPE ')[:-1] + name_bytes + prev.text('\nREUTILIZAVEL')
        if text_cursor + len(desc) > 0x100A000: raise PatchError('Descrições de itens excedem região')
        out[text_cursor:text_cursor+len(desc)] = desc
        item_at = prev.NEW_ITEMS + (374+tm)*prev.ITEM_SIZE
        struct.pack_into('<I', out, item_at + 20, ROM + text_cursor)
        text_cursor += len(desc)
    products = b''.join(struct.pack('<H', 374+tm) for tm in sorted(available)) + b'\0\0'
    if len(products) > prev.SHOP_SCRIPT-prev.SHOP_LIST: raise PatchError('Lista da loja excedeu região')
    out[prev.SHOP_LIST:prev.SHOP_LIST+len(products)] = products
    # Checks críticos: HMs/TMs antigas, script e objetos de mapas não mudam.
    if out[prev.NEW_MOVE_TABLE:prev.NEW_MOVE_TABLE+116] != source[prev.NEW_MOVE_TABLE:prev.NEW_MOVE_TABLE+116]:
        raise PatchError('HMs/TMs anteriores alteradas')
    return bytes(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--saida', type=Path, required=True)
    a = p.parse_args()
    try:
        if a.rom.resolve() == a.saida.resolve() or a.saida.exists():
            raise PatchError('A saída precisa ser um arquivo novo')
        source = a.rom.read_bytes()
        result = build(source)
        if OUTPUT_SHA256 and digest(result) != OUTPUT_SHA256: raise PatchError('SHA da saída divergente')
        write_new_file(a.rom, a.saida, result)
        print(f'Entrada preservada: {digest(source)}')
        print(f'Nova ROM: {a.saida} | SHA-256 {digest(result)}')
        print('Complemento parcial: veja limites e instruções na documentação.')
    except (OSError, ValueError) as e:
        print(f'[ERRO] {e}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__': raise SystemExit(main())
