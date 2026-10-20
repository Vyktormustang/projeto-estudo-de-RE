"""Testes da ABI libretro do `emulador_console`, sem precisar de core nem ROM.

Os dois comportamentos aqui sao os que a revisao do `libretro_port.py` do
projeto gba-harness (2026-10-17) mostrou errados no nosso harness:

- `GET_CAN_DUPE` escreve um `bool` (1 byte); a versao anterior escrevia um
  `c_int` (4 bytes) por cima de memoria vizinha do core.
- `GET_VARIABLE` recebe `struct retro_variable { key; value; }`; a versao
  anterior tratava o endereco como buffer de texto e escrevia zeros sobre
  o PONTEIRO da chave, devolvendo 1 sempre.
"""

from __future__ import annotations

import ctypes as C
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp.emulador_console import (  # noqa: E402
    VariavelRetro,
    escrever_bool_retro,
    responder_get_variable,
)


def test_escrever_bool_e_um_byte_so():
    """So' o primeiro byte muda; os vizinhos ficam intactos."""
    buf = (C.c_ubyte * 4)(0xAA, 0xAA, 0xAA, 0xAA)
    escrever_bool_retro(C.addressof(buf), True)
    assert bytes(buf) == b"\x01\xaa\xaa\xaa"
    escrever_bool_retro(C.addressof(buf), False)
    assert bytes(buf) == b"\x00\xaa\xaa\xaa"


def test_get_variable_existente_nao_toca_na_chave():
    variavel = VariavelRetro(b"mgba_use_bios", None)
    reservatorio: dict = {}
    r = responder_get_variable(
        C.addressof(variavel), {"mgba_use_bios": "OFF"}, reservatorio)
    assert r == 1
    # a regressao antiga era exatamente isto aqui mudar:
    assert variavel.key == b"mgba_use_bios"
    assert variavel.value == b"OFF"
    # e o buffer do valor precisa continuar vivo depois da chamada
    assert reservatorio["mgba_use_bios"].value == b"OFF"


def test_get_variable_ausente_deixa_o_core_usar_o_padrao():
    variavel = VariavelRetro(b"nao_existe", None)
    r = responder_get_variable(C.addressof(variavel), {}, {})
    assert r == 0
    assert variavel.value is None


def test_get_variable_sem_chave():
    variavel = VariavelRetro(None, None)
    assert responder_get_variable(C.addressof(variavel), {"x": "y"}, {}) == 0
