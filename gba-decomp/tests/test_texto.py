"""Testes do charset (codificar/decodificar) usado nos patches de texto.

A tabela vem da secao 9.5 do relatorio, medida em quatro strings conhecidas da
ROM. O que se testa aqui: os bytes batem com os da ROM, a ida e volta fecha, e
caractere fora da tabela e' RECUSADO (nao vira '?' em silencio).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from gbadecomp import texto  # noqa: E402

# bytes lidos da ROM em gItems[4].name (0x083DB0D8), item "POKé BOLA"
NOME_NA_ROM = bytes.fromhex("ca c9 c5 1b 00 bc c9 c6 bb ff 00 00 00 00")


def test_decodifica_o_nome_que_esta_na_rom():
    assert texto.decodificar(NOME_NA_ROM) == "POKé BOLA"


def test_codifica_igual_aos_bytes_da_rom():
    assert texto.codificar("POKé BOLA") == NOME_NA_ROM[:10]


def test_ida_e_volta():
    for frase in ("BOLA NOVA", "MASTER BALL", "POKé BOLA", "ola, mundo!"):
        assert texto.decodificar(texto.codificar(frase)) == frase


def test_espaco_e_zero_e_terminador_e_ff():
    assert texto.codificar("A B") == bytes([0xBB, 0x00, 0xBC, 0xFF])


def test_para_no_terminador():
    assert texto.decodificar(b"\xbb\xff\xcc") == "A"


def test_recusa_caractere_fora_da_tabela():
    with pytest.raises(ValueError, match="nao esta' na tabela"):
        texto.codificar("TM01")      # digitos ainda nao foram medidos
    with pytest.raises(ValueError, match="nao esta' na tabela"):
        texto.codificar("Poção")     # 'ç' nao esta' na tabela


def test_caber_preenche_com_ff_e_recusa_quando_nao_cabe():
    cheio = texto.caber("BOLA NOVA", 14)
    assert len(cheio) == 14
    assert texto.decodificar(cheio) == "BOLA NOVA"
    assert cheio[9:] == b"\xff" * 5
    with pytest.raises(ValueError, match="o campo tem 5"):
        texto.caber("BOLA NOVA", 5)
