"""Testes puros da ordenacao de candidatos do explorador da Rota 1.

O comportamento em jogo foi medido nas sondas de 2026-10-20; aqui fica
so' a regra que fez diferenca: penalidade por visita repetida. Sem ela,
num beco horizontal sob uma borda/ledge, todo vizinho lateral (mesmo y)
continua vencendo o recuo ao sul no custo geografico e o explorador
oscila. Nenhum destes testes precisa de emulador.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ferramentas.ir_a_viridian import ordenar_candidatos  # noqa: E402


def _direcoes(posicao, visitados=None, paredes=()):
    return [
        direcao
        for _chave, direcao, _alvo in ordenar_candidatos(
            posicao, lambda x, y: y, visitados or {}, set(paredes))
    ]


def test_sem_visitas_prefere_o_norte():
    assert _direcoes((10, 10))[0] == "UP"


def test_tile_muito_visitado_perde_para_desvio_lateral():
    visitados = {(10, 9): 3}  # 4*9 + 3*3 = 45 > 4*10 do lateral virgem
    assert _direcoes((10, 10), visitados)[0] == "LEFT"


def test_paredes_aprendidas_sao_excluidas():
    direcoes = _direcoes((10, 10), paredes={(10, 9), (9, 10), (11, 10)})
    assert direcoes == ["DOWN"]


def test_recuo_vence_quando_todas_as_outras_visitas_estao_altas():
    visitados = {(10, 9): 9, (9, 10): 9, (11, 10): 9, (10, 11): 0}
    assert _direcoes((10, 10), visitados)[0] == "DOWN"
