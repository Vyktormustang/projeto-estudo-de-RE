"""Testes da codificacao da mochila, com os valores MEDIDOS em jogo.

Nao precisam de emulador: a cifra e' aritmetica pura. Os numeros abaixo foram
lidos de um jogo em execucao, nao inventados:

  - mochila vazia -> slots com `00 00 04 85` (itemId 0, quantidade 0x8504)
  - chave em SaveBlock2+0xF20 = 0x0E078504
  - depois de dar 99 Poke Balls, o slot lido foi `04 00 67 85`

Ou seja: 0 ^ 0x8504 = 0x8504 e 99 ^ 0x8504 = 0x8567.
"""
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ferramentas.da_pokebolas import cifrar_quantidade  # noqa: E402

CHAVE_MEDIDA = 0x0E078504


def test_slot_vazio_nao_e_zero():
    """O achado que evita gravar quantidade errada."""
    assert cifrar_quantidade(0, CHAVE_MEDIDA) == 0x8504


def test_99_bolas_da_o_byte_medido():
    assert cifrar_quantidade(99, CHAVE_MEDIDA) == 0x8567
    assert struct.pack("<HH", 4, cifrar_quantidade(99, CHAVE_MEDIDA)) == bytes.fromhex("04006785")


def test_ida_e_volta_para_todas_as_quantidades():
    for qtd in (0, 1, 12, 99, 255, 999, 0xFFFF):
        guardado = cifrar_quantidade(qtd, CHAVE_MEDIDA)
        assert 0 <= guardado <= 0xFFFF
        assert cifrar_quantidade(guardado, CHAVE_MEDIDA) == qtd


def test_so_a_metade_baixa_da_chave_entra():
    for chave in (0x12345678, 0xFFFFFFFF, 0x00000000):
        assert cifrar_quantidade(7, chave) == cifrar_quantidade(7, chave & 0xFFFF)
