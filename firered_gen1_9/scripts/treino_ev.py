#!/usr/bin/env python3
"""Instala o treino de EV em uma nova cópia da ROM de encontros deste projeto.

Não inclui nem obtém ROMs ou saves. A entrada deve ser a build de encontros
identificada pelo SHA-256 exato abaixo. Nunca modifica a entrada e não
sobrescreve uma saída existente. Os offsets NÃO servem para outras ROMs.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import struct
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD_PATH = ROOT / "patches/treino_ev/payload.bin"
BASE_SHA256 = "3f8cc9e3a52b1bad8a2f22df9a302f79a355e929669c5425ef023017bd4c4e49"
PAYLOAD_SHA256 = "cdf2238a72f00298a7b5a06721d266b6e9ff9826f5174006b64ea6e07c28f6fb"
ROM_SIZE = 0x1000000
ROM_START = 0x08000000
HOOK_OFFSET = 0x1222E0
ORIGINAL_HOOK = bytes.fromhex("f0 b5 ce 46 47 46 80 b5")
PAYLOAD_OFFSET = 0xF81000
PAYLOAD_SPACE = 0x1000
# ldr r3, [pc, #0]; bx r3; .word 0x08f81001 (Thumb)
HOOK = bytes.fromhex("00 4b 18 47 01 10 f8 08")


class PatchError(ValueError):
    """A origem, o payload ou a saída não cumpriram as pré-condições."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_payload(payload: bytes) -> None:
    if not payload or len(payload) > PAYLOAD_SPACE or digest(payload) != PAYLOAD_SHA256:
        raise PatchError("Payload ausente, diferente da versão testada ou grande demais.")
    # O primeiro push e o BL fazem parte do entrypoint compilado em Thumb.
    if payload[:2] != bytes.fromhex("1f b5"):
        raise PatchError("Entrada Thumb do payload inesperada.")


def validate_source(rom: bytes) -> None:
    sha = digest(rom)
    if len(rom) != ROM_SIZE or sha != BASE_SHA256:
        raise PatchError(
            "ROM incompatível: use a variante de encontros indicada na documentação. "
            f"Esperado SHA-256 {BASE_SHA256}; recebido {sha}, {len(rom)} bytes."
        )
    if rom[0xAC:0xB0] != b"BPRE" or rom[HOOK_OFFSET:HOOK_OFFSET + len(ORIGINAL_HOOK)] != ORIGINAL_HOOK:
        raise PatchError("Cabeçalho ou prólogo do resumo não correspondem à ROM esperada.")
    if rom[PAYLOAD_OFFSET:PAYLOAD_OFFSET + PAYLOAD_SPACE] != b"\xff" * PAYLOAD_SPACE:
        raise PatchError("A área de código reservada não está inteiramente vazia.")
    # Ponteiros GBA normalmente são alinhados. Essa verificação não é uma prova
    # absoluta de espaço livre, mas impede instalação com referências diretas.
    low = ROM_START + PAYLOAD_OFFSET
    high = low + PAYLOAD_SPACE
    for index, (address,) in enumerate(struct.iter_unpack("<I", rom)):
        if low <= address < high:
            raise PatchError(f"Referência alinhada à área reservada em 0x{index * 4:X}.")


def verify_output(source: bytes, output: bytes, payload: bytes) -> None:
    """Garante que apenas o hook e o payload foram alterados."""
    if len(source) != len(output):
        raise PatchError("O tamanho da ROM mudou.")
    hook_end = HOOK_OFFSET + len(HOOK)
    payload_end = PAYLOAD_OFFSET + len(payload)
    if (
        output[:HOOK_OFFSET] != source[:HOOK_OFFSET]
        or output[HOOK_OFFSET:hook_end] != HOOK
        or output[hook_end:PAYLOAD_OFFSET] != source[hook_end:PAYLOAD_OFFSET]
        or output[PAYLOAD_OFFSET:payload_end] != payload
        or output[payload_end:] != source[payload_end:]
    ):
        raise PatchError("Diferença fora do hook e da área de payload aprovada.")


def apply_patch(rom: bytes, payload: bytes) -> bytes:
    validate_source(rom)
    validate_payload(payload)
    result = bytearray(rom)
    result[HOOK_OFFSET:HOOK_OFFSET + len(HOOK)] = HOOK
    result[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(payload)] = payload
    output = bytes(result)
    verify_output(rom, output, payload)
    return output


def write_new_file(source: Path, destination: Path, data: bytes) -> None:
    """Nunca sobrescreve destino, link simbólico ou hard link para a entrada."""
    if source.resolve() == destination.resolve():
        raise PatchError("A saída não pode ser a ROM de entrada.")
    if destination.exists() and os.path.samefile(source, destination):
        raise PatchError("A saída aponta para a ROM de entrada.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        # 'x' usa O_EXCL e também rejeita links simbólicos preexistentes.
        with destination.open("xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise PatchError(f"A saída já existe: {destination}. Escolha outro nome.") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, help="ROM de encontros existente (será preservada)")
    parser.add_argument("--saida", type=Path, help="nova ROM .gba, que não pode existir")
    parser.add_argument("--self-test", action="store_true", help="roda os testes sintéticos do patcher")
    args = parser.parse_args(argv)
    if args.self_test:
        import unittest
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_treino_ev_patcher.py")
        if not suite.countTestCases():
            print("[ERRO] Nenhum teste encontrado.", file=sys.stderr)
            return 1
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if not args.rom or not args.saida:
        parser.error("informe --rom e --saida, ou use --self-test")
    try:
        if args.rom.resolve() == args.saida.resolve():
            raise PatchError("A saída não pode ser a ROM de entrada.")
        if args.saida.exists():
            if os.path.samefile(args.rom, args.saida):
                raise PatchError("A saída aponta para a ROM de entrada.")
            raise PatchError(f"A saída já existe: {args.saida}. Escolha outro nome.")
        source = args.rom.read_bytes()
        payload = PAYLOAD_PATH.read_bytes()
        output = apply_patch(source, payload)
        write_new_file(args.rom, args.saida, output)
        print(f"Entrada preservada: SHA-256 {digest(source)}")
        print(f"Nova ROM: {args.saida} | SHA-256 {digest(output)}")
        print("Treino usa apenas EVs existentes; IVs são somente leitura.")
        return 0
    except (OSError, PatchError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
