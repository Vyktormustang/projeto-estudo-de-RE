#!/usr/bin/env python3
"""Diagnostica o hook histórico BAG_MOD_v3 sem modificar ROM ou save do usuário.

Exemplo:
  python3 scripts/diagnostico_hook_v3.py \
    --rom 'google_drive/Pokemon - Fire Red (BR).gba' \
    --core /tmp/mgba-build/mgba_libretro.so

O script cria ROMs instrumentadas somente em um diretório temporário. O contador
(32 bits para evitar overflow por frame) ocupa o último word da EWRAM *apenas*
no emulador. O roteiro joga desde o boot com uma sessão sintética, sem carregar
saves do usuário. Não produz um mod de jogo e não demonstra o combo de teclas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'gba-re_project (1).zip'
BASE_SHA256 = '6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae'
V3_SHA256 = '348025c13828517f3a4ae03cd9fe963df07fcb12ed087933b0d319d4892215a3'
SITE = 0x0A38
TRAMP = 0xEB0C00
SENTINEL = 0x08EB0D00
COUNTER = 0x0203FFFC
ORIGINAL = bytes.fromhex('30 b5 00 06 04 0e 09 04')
BAD_SITE = bytes.fromhex('01 4b 18 47 01 0c eb 08')
GOOD_SITE = bytes.fromhex('00 4b 18 47 01 0c eb 08')
# push {r0-r3}; ldr counter; ++counter; pop {r0-r3}; replay dos 8 bytes;
# ldr r3, retorno; bx r3; literais: COUNTER e 0x08000a41.
DEBUG_TRAMP = bytes.fromhex(
    '0f b4 05 48 01 68 01 31 01 60 0f bc '
    '30 b5 00 06 04 0e 09 04 01 4b 18 47 '
    'fc ff 03 02 41 0a 00 08'
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def literal_address(site: int, imm8: int) -> int:
    return ((site + 4) & ~3) + 4 * imm8


def restore_v3(base: bytes) -> bytes:
    """Reconstrói os bytes exatos do v3 original a partir do ZIP histórico."""
    if sha(base) != BASE_SHA256 or base[SITE:SITE + 8] != ORIGINAL:
        raise ValueError('ROM não corresponde à cópia histórica BPRE registrada.')
    with zipfile.ZipFile(ARCHIVE) as archive:
        site = bytes.fromhex(archive.read('reports/site_v3.hex').decode().strip())
        tramp = bytes.fromhex(archive.read('reports/tramp_v3.hex').decode().strip())
    if site != BAD_SITE or base[TRAMP:TRAMP + len(tramp)] != b'\xff' * len(tramp):
        raise ValueError('Bytes de entrada ou área do trampolim divergentes.')
    result = bytearray(base)
    result[SITE:SITE + 8] = site
    result[TRAMP:TRAMP + len(tramp)] = tramp
    if sha(result) != V3_SHA256:
        raise ValueError('O v3 reproduzido não corresponde ao hash histórico.')
    return bytes(result)


def instrument(base: bytes, fixed: bool) -> bytes:
    """Veneer antigo ou corrigido e contador sem checagem de botões."""
    restore_v3(base)  # também valida a entrada, o arquivo ZIP e o hash
    if base[TRAMP:0xEB0D02] != b'\xff' * (0xEB0D02 - TRAMP):
        raise ValueError('Área temporária de instrumentação não está vazia.')
    result = bytearray(base)
    result[SITE:SITE + 8] = GOOD_SITE if fixed else BAD_SITE
    result[TRAMP:TRAMP + len(DEBUG_TRAMP)] = DEBUG_TRAMP
    result[SENTINEL - 0x08000000:SENTINEL - 0x08000000 + 2] = b'\xfe\xe7'  # b .
    return bytes(result)


def run(rom: Path, core: Path) -> dict:
    sys.path.insert(0, str(ROOT / 'tests'))
    from mgba_treino_harness import Emulator, offset, put32, u32

    base = rom.read_bytes()
    restore_v3(base)
    with tempfile.TemporaryDirectory(prefix='gba-hook-v3-') as directory:
        temp = Path(directory)
        bad = temp / 'veneer_antigo.gba'
        fixed = temp / 'veneer_corrigido.gba'
        bad.write_bytes(instrument(base, False))
        fixed.write_bytes(instrument(base, True))

        f = Emulator(rom.resolve(), core.resolve(), temp)
        try:
            f.run(600)
            baseline = f.state()
            original_counter = u32(baseline, offset(COUNTER))
        finally:
            f.close()

        forced = {}
        for label, path in (('antigo', bad), ('corrigido', fixed)):
            f = Emulator(path, core.resolve(), temp)
            try:
                state = bytearray(baseline)
                put32(state, offset(COUNTER), 0)
                for register, value in {0: 0, 1: 0x1234, 13: 0x03007E00,
                                        14: SENTINEL | 1, 15: 0x08000A3A}.items():
                    put32(state, 0x20 + register * 4, value)
                cpsr = u32(state, 0x60)
                put32(state, 0x60, ((cpsr | 0x20 | 0xC0) & ~0x1F) | 0x1F)
                put32(state, 0x2F8, 0)
                put32(state, 0x2FC, 0)
                f.restore(bytes(state))
                f.run(3)
                state = f.state()
                forced[label] = {'contador': u32(state, offset(COUNTER)),
                                 'pc': f'{u32(state, 0x5C):08x}',
                                 'registrador_gpu': state[0x19000:0x19002].hex()}
            finally:
                f.close()

        f = Emulator(fixed, core.resolve(), temp)
        try:
            f.restore(baseline)
            # Introdução inteiramente sintética: o avatar chega ao quarto.
            for i in range(140):
                if i == 0:
                    f.pulse('START', 90)
                f.pulse('A', 55)
            for _ in range(6):
                f.pulse('B', 80)
            room = bytearray(f.state())
            # Nesta ROM histórica, SaveBlock1 aponta para a localização atual.
            save1 = u32(room, 0x19000 + 0x5008)
            if not 0x02000000 <= save1 <= 0x0203FFF8:
                raise AssertionError('Ponteiro de SaveBlock1 inválido.')
            map_group, map_number = room[offset(save1) + 4:offset(save1) + 6]
            if (map_group, map_number) != (4, 1):
                raise AssertionError('O roteiro sintético não chegou ao quarto de Pallet.')
            put32(room, offset(COUNTER), 0)
            f.restore(bytes(room))
            samples = []
            for _ in range(4):
                f.run(60)
                samples.append(u32(f.state(), offset(COUNTER)))
        finally:
            f.close()

        # Controle: o mesmo estado, na ROM original sem o contador, não deve
        # alterar o word reservado ao diagnóstico no intervalo observado.
        f = Emulator(rom.resolve(), core.resolve(), temp)
        try:
            f.restore(bytes(room))
            f.run(240)
            control = u32(f.state(), offset(COUNTER))
        finally:
            f.close()

    if forced['antigo']['contador'] != 0 or forced['antigo']['pc'] == f'{SENTINEL + 2:08x}':
        raise AssertionError('O veneer antigo se comportou de forma inesperada.')
    if forced['corrigido']['contador'] != 1 or forced['corrigido']['pc'] != f'{SENTINEL + 2:08x}':
        raise AssertionError('O contador corrigido não executou e retornou uma vez.')
    if forced['corrigido']['registrador_gpu'] != '3412':
        raise AssertionError('A execução não preservou o argumento de SetGpuReg.')
    if control != 0 or not (samples[0] > 0 and all(a < b for a, b in zip(samples, samples[1:]))):
        raise AssertionError('Contador/controle não confirmam chamadas durante o quarto.')
    return {
        'base_sha256': BASE_SHA256,
        'v3_sha256': V3_SHA256,
        'literal_ldr_antigo': f'{literal_address(0x08000A38, 1):08x}',
        'literal_ldr_corrigido': f'{literal_address(0x08000A38, 0):08x}',
        'chamadas_forcadas': forced,
        'contador_sem_patch_apos_boot': original_counter,
        'mapa_sintetico': {'grupo': map_group, 'numero': map_number},
        'contadores_em_quarto_a_cada_60_frames': samples,
        'controle_sem_patch_apos_240_frames': control,
        'limites': 'ROM histórica e jogo sintético; combo e ROM Gen 1–9 não foram testados.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--core', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.rom, args.core), indent=2, ensure_ascii=False))
    except (OSError, ValueError, AssertionError) as exc:
        print(f'[ERRO] {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
