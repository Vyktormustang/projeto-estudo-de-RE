"""Modo de demonstracao (SN_FAKE_MODELS=1): simula os modelos de IA.

Serve para testar a API, o frontend e o APK em um PC fraco (ou em CI) sem
baixar 2 GB de modelos. NUNCA use no treino de verdade: os scores sao
inventados a partir da propria frase, sem ouvir o audio.

A simulacao e deterministica (mesma frase -> mesmo resultado), o que ajuda a
testar a interface.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from .asr import ASRWord, Transcription


@dataclass
class FakePlan:
    """O que "aconteceu" na leitura simulada."""

    transcription: Transcription
    missing: set[int]          # indices de palavras que o "aluno" pulou
    weak: set[int]             # indices de palavras com um fonema trocado


def _seed_for(sentence_id: str) -> int:
    digest = hashlib.sha256(sentence_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def build_plan(sentence_id: str, words: list[str], speech_seconds: float) -> FakePlan:
    """Cria um plano de leitura imperfeita (mas estavel) para a frase."""
    rng = random.Random(_seed_for(sentence_id))
    total_weight = sum(max(1, len(w)) for w in words) or 1
    cursor = 0.0
    asr_words: list[ASRWord] = []
    missing: set[int] = set()
    weak: set[int] = set()

    for index, word in enumerate(words):
        span = speech_seconds * (max(1, len(word)) / total_weight)
        start, end = cursor, cursor + span
        cursor = end
        is_last_content_word = index == len(words) - 1
        # Uma palavra (nunca a primeira) e "pulada"; as palavras mais longas
        # podem ficar "fracas" -> cores diferentes na tela para voce testar a UI.
        if len(words) > 3 and index == len(words) - 2 and len(word) > 3 and not is_last_content_word:
            missing.add(index)
            continue
        if len(word) >= 6 and rng.random() < 0.45:
            weak.add(index)
        spoken = word if index not in weak else word[:-1] + "s"
        asr_words.append(ASRWord(text=spoken, start=round(start, 3), end=round(end, 3), probability=0.9))

    text = " ".join(w.text for w in asr_words)
    return FakePlan(
        transcription=Transcription(text=text, words=asr_words, language="en", confidence=0.9),
        missing=missing,
        weak=weak,
    )


def simulate_heard(plan: FakePlan, index: int, expected: list[str], rng: random.Random) -> list[str]:
    """Devolve a sequencia de fonemas "ouvida" para uma palavra."""
    if index in plan.missing:
        return []
    if index in plan.weak and expected:
        mutated = list(expected)
        position = len(mutated) // 2
        mutated[position] = _confuse(mutated[position], rng)
        return mutated
    return list(expected)


_CONFUSIONS = {
    "iː": "ɪ", "ɪ": "iː", "ə": "ʌ", "ʌ": "ə", "θ": "t", "ð": "d", "ɹ": "ɾ",
    "æ": "ɛ", "ɛ": "æ", "ŋ": "n", "v": "w", "w": "v", "z": "s", "s": "z",
}


def _confuse(symbol: str, rng: random.Random) -> str:
    return _CONFUSIONS.get(symbol) or rng.choice(["ə", "ɪ", "t", "d"])
