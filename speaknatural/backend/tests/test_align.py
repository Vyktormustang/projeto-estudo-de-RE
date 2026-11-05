"""Testes do alinhamento Needleman-Wunsch e da formula de nota."""

from __future__ import annotations

from app.services.align import align_phonemes, sequence_edit_distance
from app.services.scoring import color_for, overall_score, word_score


def test_alinhamento_perfeito_da_nota_maxima():
    expected = ["s", "p", "iː", "k"]
    pairs, score = align_phonemes(expected, expected)
    assert score == 1.0
    assert all(pair.is_exact for pair in pairs)


def test_alinhamento_conta_som_faltando():
    # faltou o /k/ final
    pairs, score = align_phonemes(["s", "p", "iː", "k"], ["s", "p", "iː"])
    assert 0.7 <= score < 1.0
    assert any(pair.expected == "k" and pair.heard is None for pair in pairs)


def test_alinhamento_penaliza_som_extra():
    pairs, score = align_phonemes(["s", "p", "iː", "k"], ["s", "p", "iː", "k", "ə"])
    assert score < 1.0
    assert any(pair.expected is None for pair in pairs)


def test_alinhamento_com_som_parecido_da_nota_parcial():
    _, perfeito = align_phonemes(["s", "iː", "t"], ["s", "iː", "t"])
    _, parecido = align_phonemes(["s", "iː", "t"], ["s", "ɪ", "t"])
    assert parecido < perfeito
    assert parecido > 0.5


def test_alinhamento_vazio():
    assert align_phonemes([], []) == ([], 0.0)
    _, score = align_phonemes(["a"], [])
    assert score == 0.0


def test_edit_distance():
    assert sequence_edit_distance(["a", "b"], ["a", "b"]) == 0
    assert sequence_edit_distance(["a", "b"], ["a"]) == 1


def test_cores_nas_faixas_do_escopo():
    assert color_for(1.0) == "green"
    assert color_for(0.85) == "green"
    assert color_for(0.849) == "yellow"
    assert color_for(0.5) == "yellow"
    assert color_for(0.499) == "red"
    assert color_for(0.0) == "red"


def test_nota_da_palavra_palavra_pulada_fica_vermelha():
    assert word_score(1.0, presence=0.0, expected_phoneme_count=5) <= 0.25
    assert color_for(word_score(1.0, presence=0.0, expected_phoneme_count=5)) == "red"


def test_nota_da_palavra_perfeita():
    assert word_score(1.0, presence=1.0, expected_phoneme_count=4) == 1.0


def test_palavra_curta_reconhecida_nao_fica_amarela():
    # "a"/"of": o modelo de fonemas erra muito, mas a transcricao acertou
    assert word_score(0.4, presence=1.0, expected_phoneme_count=1) >= 0.85


def test_media_geral_pondera_pela_quantidade_de_fonemas():
    # palavra longa ruim deve derrubar mais que palavra curta ruim
    longo_ruim = overall_score([(1.0, 1), (0.2, 8)])
    curto_ruim = overall_score([(0.2, 1), (1.0, 8)])
    assert longo_ruim < curto_ruim
