"""Testes estruturais; ROM é opcional e nunca é incluída no repositório."""
from __future__ import annotations
import csv
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import atualizacoes_gen9 as patch, efeitos_gen9 as effects, golpes_gen9 as levels
from scripts import encontros_selvagens as wild, eventos_fixos as fixed, treino_ev

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(os.environ.get('ATUALIZACOES_TEST_BASE', ROOT / 'rom_mod/ptbr_gen1-9_selvagens_treino_golpes_nivel.gba'))


class CatalogoAtualizadoTests(unittest.TestCase):
    def test_catalogos_verificados_e_limites(self):
        inputs = patch.read_checked_inputs()
        with (ROOT / 'data/tms_gen9.csv').open(newline='', encoding='utf-8') as f:
            machines = list(csv.DictReader(f))
        with (ROOT / 'docs/golpes_ainda_nao_incluidos.csv').open(newline='', encoding='utf-8') as f:
            omitted = list(csv.DictReader(f))
        self.assertEqual(len(machines), 229)
        self.assertEqual(sum(r['status'] == 'disponivel' for r in machines), 189)
        self.assertEqual(len(omitted), 845)
        self.assertEqual(len({r['name'] for r in omitted}), 87)
        self.assertEqual(len(inputs[ROOT / 'data/compatibilidade_tms_gen9.bin']), 1026 * 29)
        self.assertTrue(any(r['name'] == 'Heat Crash' for r in omitted))
        self.assertEqual(machines[0]['name'], 'Take Down')
        self.assertEqual(machines[0]['item_id'], '375')
        self.assertNotEqual(machines[0]['name'], 'Focus Punch')

    def test_nao_aceita_rom_ou_destino_invalidos(self):
        with self.assertRaises(patch.PatchError):
            patch.build(b'not a rom')
        with tempfile.TemporaryDirectory() as td:
            source, dest = Path(td) / 'base.gba', Path(td) / 'new.gba'
            source.write_bytes(b'original')
            dest.write_bytes(b'preservar')
            with mock.patch('sys.argv', ['patch', '--rom', str(source), '--saida', str(dest)]):
                self.assertEqual(patch.main(), 1)
            self.assertEqual(source.read_bytes(), b'original')
            self.assertEqual(dest.read_bytes(), b'preservar')

    def test_vetores_thumb_e_codificacao(self):
        payload = patch.read_checked_inputs()[ROOT / 'patches/atualizacoes_gen9/payload.bin']
        self.assertLessEqual(len(payload), 0xC00)
        for at, original, vector in patch.HOOKS:
            self.assertEqual(at % 4, 0)
            self.assertEqual(len(bytes.fromhex(original)), 8)
            self.assertEqual(payload[vector:vector + 4], bytes.fromhex('00 4b 18 47'))
            target = struct.unpack_from('<I', payload, vector + 4)[0]
            self.assertTrue(0x08E04400 <= target < 0x08E05000 and target & 1)
        self.assertEqual(patch.text('TM9-001'), bytes.fromhex('ce c7 aa ae a1 a1 a2 ff'))
        with self.assertRaises(patch.PatchError):
            patch.text('á')


@unittest.skipUnless(BASE.exists(), 'ROM privada de entrada não fornecida')
class RomAtualizadaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = BASE.read_bytes()
        cls.output = patch.build(cls.base)
        cls.inputs = patch.read_checked_inputs()

    def test_digest_e_antigos_itens_tm_hm(self):
        self.assertEqual(patch.digest(self.base), patch.BASE_SHA256)
        if patch.OUTPUT_SHA256:
            self.assertEqual(patch.digest(self.output), patch.OUTPUT_SHA256)
        self.assertEqual(self.output[patch.NEW_ITEMS:patch.NEW_ITEMS + 375 * 44],
                         self.base[patch.ITEM_BASE:patch.ITEM_BASE + 375 * 44])
        self.assertEqual(self.output[patch.NEW_MOVE_TABLE:patch.NEW_MOVE_TABLE + 116],
                         self.base[0x669894:0x669894 + 116])
        # Primeira TM antiga continua Focus Punch; nova TM001 é Take Down.
        self.assertEqual(struct.unpack_from('<H', self.output, patch.NEW_MOVE_TABLE)[0], 264)
        self.assertEqual(struct.unpack_from('<H', self.output, patch.NEW_MOVE_TABLE + (375 - 289) * 2)[0], 36)
        # HMs originais não mudam de ID, importância, uso ou movimento.
        for item in range(339, 347):
            a, b = patch.ITEM_BASE + item * 44, patch.NEW_ITEMS + item * 44
            self.assertEqual(self.output[b:b + 44], self.base[a:a + 44])
        for at in patch.MOVE_POINTERS:
            self.assertEqual(struct.unpack_from('<I', self.output, at)[0], 0x08E18000)

    def test_descricao_antes_da_compra_tem_golpe_correto(self):
        machines = patch.parse_machines(self.inputs[ROOT / 'data/tms_gen9.csv'], self.output)
        for number in range(1, 230):
            item = 374 + number
            ptr = struct.unpack_from('<I', self.output, patch.NEW_ITEMS + 44 * item + 20)[0] - 0x08000000
            if number not in machines:
                self.assertEqual(ptr, 0xE18A00)
                continue
            self.assertTrue(0xE0D43A <= ptr < 0xE0F000)
            move = machines[number]
            name = self.output[0x235930 + move * 17:0x235930 + (move + 1) * 17].split(b'\xff', 1)[0]
            expected = patch.text('GOLPE ')[:-1] + name + patch.text('\nREUTILIZAVEL')
            self.assertEqual(self.output[ptr:ptr + len(expected)], expected)

    def test_apenas_areas_permitidas_foram_modificadas(self):
        allowed = bytearray(len(self.base))
        def mark(lo, hi): allowed[lo:hi] = b'\1' * (hi - lo)
        for lo, hi in patch.FREE_REGIONS: mark(lo, hi)
        mark(0x5A914, 0x5A916)
        for effect in (96, 110, 131, 141, 163, 12, 15, 22, 55, 56, 63, 64, 74):
            mark(effects.SCRIPT_TABLE + 4 * effect, effects.SCRIPT_TABLE + 4 * effect + 4)
        moves_changed = {467, 522, 564, 661, 482, 488, 534, 507, 394, 424, 403, 516, 518, 490, 487, 450}
        moves_changed.update(row[0] for row in effects.NATIVE_EFFECTS + effects.POWER_CHANGES)
        for move in moves_changed:
            mark(effects.MOVE_TABLE + 12 * move, effects.MOVE_TABLE + 12 * move + 6)
        for at, _, _ in patch.HOOKS: mark(at, at + 8)
        for at in patch.ITEM_POINTERS + patch.MOVE_POINTERS + (0xC7380, 0x7C082C): mark(at, at + 4)
        for at, shift in patch.THRESHOLDS: mark(at, at + 2); mark(shift, shift + 2)
        for at in (0xC7370, 0xC73B0): mark(at, at + 4)
        mark(levels.TABLE, levels.FREE_END)
        bad = [i for i, (a, b) in enumerate(zip(self.base, self.output)) if a != b and not allowed[i]]
        self.assertEqual(bad[:10], [])

    def test_lista_inteira_igual_ao_catalogo_e_antigos_preservados(self):
        lists = patch.parse_levels(self.inputs[ROOT / 'data/learnsets_gen1_9_atualizados.csv'],
                                   self.inputs[ROOT / 'data/learnsets_gen1_9.csv'], self.output)
        for sid, expected in lists.items():
            ptr = struct.unpack_from('<I', self.output, levels.TABLE + 4 * sid)[0] - 0x08000000
            actual = []
            for _ in range(51):
                move, lv = struct.unpack_from('<HB', self.output, ptr)
                ptr += 3
                if move == 0xffff: break
                actual.append((lv, move))
            else: self.fail(f'Lista {sid} sem terminador')
            self.assertEqual(actual, expected)

    def test_efeitos_base_de_scripts_e_probabilidade(self):
        # Antes de especializar os atributos, nossos geradores devem produzir
        # byte a byte os scripts nativos de Bulk Up e Tickle.
        self.assertEqual(effects.stages(0x186FC7, ((1, 1), (2, 1))), self.base[0x186FC7:0x18702B])
        self.assertEqual(effects.stages(0x186ECE, ((1, 1), (2, 1)), True), self.base[0x186ECE:0x186F41])
        self.assertEqual(self.base[0x5A914:0x5A916], b'\x0e\xd8')  # Random <= chance
        self.assertEqual(self.output[0x5A914:0x5A916], b'\x0e\xd2')  # Random < chance
        for effect in (96, 110, 131, 141, 163, 12, 15, 22, 55, 56, 63, 64, 74):
            ptr = struct.unpack_from('<I', self.output, effects.SCRIPT_TABLE + 4 * effect)[0]
            self.assertTrue(0x08000000 + effects.SCRIPT_START <= ptr < 0x08000000 + effects.SCRIPT_END)
        for move in (394, 424):
            self.assertEqual(self.output[effects.MOVE_TABLE + move * 12 + 5], 10)
        for move, effect, chance in effects.NATIVE_EFFECTS:
            at = effects.MOVE_TABLE + move * 12
            self.assertEqual((self.output[at], self.output[at + 5]), (effect, chance))
        for move, _, power, _, accuracy in effects.POWER_CHANGES:
            at = effects.MOVE_TABLE + move * 12
            self.assertEqual((self.output[at + 1], self.output[at + 3]), (power, accuracy))
            self.assertEqual(self.output[at + 4], self.base[at + 4])

    def test_selvagens_fixos_treino_e_historias_preservados(self):
        species, wild_maps = wild.load_species(), wild.load_maps()
        self.assertEqual(wild.parse_tables(self.base, wild_maps, species),
                         wild.parse_tables(self.output, wild_maps, species))
        self.assertEqual(self.base[treino_ev.HOOK_OFFSET:treino_ev.HOOK_OFFSET + len(treino_ev.HOOK)],
                         self.output[treino_ev.HOOK_OFFSET:treino_ev.HOOK_OFFSET + len(treino_ev.HOOK)])
        start, end = treino_ev.PAYLOAD_OFFSET, treino_ev.PAYLOAD_OFFSET + treino_ev.PAYLOAD_SPACE
        self.assertEqual(self.base[start:end], self.output[start:end])
        count = 0
        for m in fixed.load_map_catalog():
            array = fixed._ptr(self.base, fixed.GROUP_TABLE + 4 * m.group, 4 * (m.number + 1))
            header = fixed._ptr(self.base, array + 4 * m.number, 28)
            events = fixed._ptr(self.base, header + 4, 20)
            n = self.base[events]
            self.assertEqual(self.output[events:events + 20], self.base[events:events + 20])
            if n:
                objects = fixed._ptr(self.base, events + 4, n * fixed.OBJECT_SIZE)
                self.assertEqual(self.output[objects:objects + n * fixed.OBJECT_SIZE],
                                 self.base[objects:objects + n * fixed.OBJECT_SIZE])
            count += n
        self.assertEqual(count, 1982)
        # Única mudança em sinal de mapa é o ponteiro de fundo à placa da casa.
        self.assertEqual(self.output[0x7C0824:0x7C082C], self.base[0x7C0824:0x7C082C])
        self.assertEqual(struct.unpack_from('<I', self.output, 0x7C082C)[0], 0x08E18700)
        self.assertEqual(self.output[0x18E23C:0x18E245], self.base[0x18E23C:0x18E245])

    def test_rom_catalogo_hooks_e_espaco_recusados(self):
        bad = dict(self.inputs)
        key = ROOT / 'data/tms_gen9.csv'
        bad[key] += b'bad'
        with self.assertRaises(patch.PatchError): patch.build(self.base, bad)
        for at in (patch.HOOKS[0][0], patch.FREE_REGIONS[0][0]):
            changed = bytearray(self.base); changed[at] ^= 1
            with mock.patch.object(patch, 'BASE_SHA256', patch.digest(changed)):
                with self.assertRaises(patch.PatchError): patch.build(bytes(changed), self.inputs)


if __name__ == '__main__':
    unittest.main()
