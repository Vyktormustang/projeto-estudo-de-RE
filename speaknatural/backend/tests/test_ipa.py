"""Testes do inventario IPA e da tabela de sons parecidos."""

from __future__ import annotations

from app.services import ipa


def test_tokenize_separa_ditongos_e_africadas():
    assert ipa.tokenize("tʃɪld") == ["tʃ", "ɪ", "l", "d"]
    assert ipa.tokenize("ˈbaɪ") == ["b", "aɪ"]
    assert ipa.tokenize("koʊld") == ["k", "oʊ", "l", "d"]
    assert ipa.tokenize("iː") == ["iː"]


def test_tokenize_ignora_tonicidade_e_pontuacao():
    assert ipa.tokenize("ˈwɔɾɚ") == ["w", "ɔː", "ɾ", "ɚ"]  # ɔ e ɔː sao o mesmo som
    assert ipa.tokenize("") == []


def test_canonicaliza_g_e_r():
    assert ipa.tokenize("gɑ") == ipa.tokenize("ɡɑ")
    assert ipa.tokenize("rɛd") == ipa.tokenize("ɹɛd")


def test_canonicaliza_vogais_sem_marca_de_duracao():
    # eng_to_ipa (dicionario CMU) escreve /i/, /u/, /ɔ/; o espeak usa iː, uː, ɔː
    assert ipa.tokenize("spik") == ipa.tokenize("spiːk")
    assert ipa.tokenize("ju") == ipa.tokenize("juː")


def test_similaridade_exata_e_parcial():
    assert ipa.phoneme_similarity("iː", "iː") == 1.0
    # ɪ x iː e confusao tipica -> nota parcial, nunca zero
    parcial = ipa.phoneme_similarity("iː", "ɪ")
    assert 0.5 <= parcial < 1.0
    assert ipa.phoneme_similarity("θ", "t") > 0
    # vogal x consoante = nada a ver
    assert ipa.phoneme_similarity("a", "p") == 0.0


def test_vogais_diferentes_ganham_credito_pequeno():
    score = ipa.phoneme_similarity("ɛ", "ɔː")
    assert 0.0 < score < 0.35
