"""Orquestracao da analise: audio -> transcricao -> fonemas -> notas.

Fluxo (o mesmo caminho que o POST /analyze percorre):

    1. audio.prepare_audio()          webm/ogg/wav -> WAV 16 kHz mono, corta silencio
    2. asr.transcribe()               quais palavras foram faladas + tempo de cada uma
    3. g2p.sentence_phonemes()        fonemas esperados (espeak-ng) de cada palavra
    4. phoneme_recognizer.recognize() fonemas ouvidos (wav2vec2) com tempo
    5. word_alignment.match_words()   casa palavra esperada x transcrita
    6. align.align_phonemes()         alinha fonemas dentro do trecho de cada palavra
    7. scoring.word_score()/overall   nota da palavra e nota geral (0..1)
    8. tips.*                         dicas em portugues

Cada etapa e independente e testavel - veja backend/tests/.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import ENGINE_VERSION, FAKE_MODELS
from . import asr, g2p, phoneme_recognizer, scoring, tips
from .align import align_phonemes
from .audio import PreparedAudio
from .errors import ERR_ANALYSIS_FAILED, AnalysisError
from .fake import build_plan, simulate_heard
from .text import normalize_word, split_words
from .word_alignment import match_words

logger = logging.getLogger(__name__)

#: Teto de fonemas considerados por palavra. Sem isso, uma janela de tempo
#: errada pode trazer 50 simbolos e afundar a nota por um motivo que nao e do
#: aluno. 24 sons cobre com folga a palavra mais longa do app.
MAX_HEARD_PHONEMES_PER_WORD = 24


@dataclass
class PhonemeAnalysis:
    expected: str | None
    heard: str | None
    score: float
    tip: str


@dataclass
class WordAnalysis:
    text: str
    normalized: str
    score: float
    color: str
    presence: float
    phonemes: list[PhonemeAnalysis]
    tip: str
    expected_phonemes: list[str] = field(default_factory=list)
    heard_phonemes: list[str] = field(default_factory=list)


@dataclass
class AnalysisOutput:
    transcript: str
    overall_score: float
    overall_color: str
    words: list[WordAnalysis]
    duration_seconds: float
    warnings: list[str]
    engine_version: str = ENGINE_VERSION


def run_analysis(prepared: PreparedAudio, sentence: dict[str, Any]) -> AnalysisOutput:
    """Analisa a leitura da frase e devolve notas por palavra/fonema."""
    sentence_text: str = sentence["text"]
    sentence_id: str = sentence["id"]
    words = split_words(sentence_text)
    if not words:
        raise ERR_ANALYSIS_FAILED

    warnings: list[str] = []

    # --- 3. fonemas esperados (gabarito) ---------------------------------
    expected_phonemes = g2p.sentence_phonemes(words)
    g2p_status, g2p_warning = g2p.engine_status()
    if g2p_warning:
        warnings.append(g2p_warning)

    # --- 2 + 4. o que o aluno falou --------------------------------------
    if FAKE_MODELS:
        plan = build_plan(sentence_id, words, prepared.speech_seconds)
        transcription = plan.transcription
        heard_by_index: dict[int, list[str]] = {}
        import random

        rng = random.Random(0)
        for index, phonemes in enumerate(expected_phonemes):
            heard_by_index[index] = simulate_heard(plan, index, phonemes or [], rng)
        phoneme_confidence = 0.9
        warnings.append(
            "Modo demonstração (SN_FAKE_MODELS=1): as notas são simuladas a partir da frase, "
            "sem analisar o áudio de verdade."
        )
    else:
        transcription = asr.transcribe(prepared.wav_path)
        recognition = phoneme_recognizer.recognize(prepared.wav_path)
        phoneme_confidence = recognition.confidence
        heard_by_index = {}

    matches, extra_words = match_words(words, transcription.words, prepared.speech_seconds)

    if not FAKE_MODELS:
        for match in matches:
            if match.window is None:
                heard_by_index[match.index] = []
                continue
            heard = recognition.in_window(*match.window)
            heard_by_index[match.index] = heard[:MAX_HEARD_PHONEMES_PER_WORD]

    # --- 5/6/7. alinhamento e notas --------------------------------------
    analyzed: list[WordAnalysis] = []
    weighted_scores: list[tuple[float, int]] = []

    for match in matches:
        expected = expected_phonemes[match.index]
        heard = heard_by_index.get(match.index, [])

        # Palavra que nao foi falada: nao inventamos fonemas ouvidos.
        if match.presence <= 0.0:
            heard = []

        pairs, phoneme_score = align_phonemes(expected or [], heard)
        expected_count = len(expected or [])
        word_value = scoring.word_score(
            phoneme_score if expected else None,
            match.presence,
            expected_count,
        )

        details = [
            PhonemeAnalysis(
                expected=pair.expected,
                heard=pair.heard,
                score=round(pair.score, 4),
                tip=tips.phoneme_tip(pair.expected, pair.heard, pair.score),
            )
            for pair in pairs
        ]

        worst = min(
            (p for p in pairs if p.score < 0.999),
            key=lambda p: p.score,
            default=None,
        )
        word_tip = tips.word_tip(
            match.text,
            word_value,
            match.presence,
            (worst.expected, worst.heard) if worst else None,
        )

        analyzed.append(
            WordAnalysis(
                text=match.text,
                normalized=match.normalized,
                score=word_value,
                color=scoring.color_for(word_value),
                presence=round(match.presence, 3),
                phonemes=details,
                tip=word_tip,
                expected_phonemes=expected or [],
                heard_phonemes=heard,
            )
        )
        weighted_scores.append((word_value, max(1, expected_count)))

    overall = scoring.overall_score(weighted_scores)

    # --- avisos (sempre em portugues, sempre uteis) ----------------------
    if not prepared.used_ffmpeg:
        warnings.append(
            "O ffmpeg não foi encontrado no PC do servidor: a conversão de áudio funcionou no "
            "modo de emergência. Instale o ffmpeg para melhores resultados (passo 1.2 do README)."
        )
    if not FAKE_MODELS:
        if not transcription.text.strip():
            warnings.append(
                "Não consegui identificar nenhuma palavra na sua gravação. "
                "Fale mais perto do microfone e um pouco mais alto."
            )
        elif transcription.confidence and transcription.confidence < 0.45:
            warnings.append(
                "O reconhecedor ficou em dúvida em alguns trechos (gravação baixa ou com ruído). "
                "Tente gravar num lugar mais silencioso."
            )
        if phoneme_confidence and phoneme_confidence < 0.35:
            warnings.append(
                "O analisador de sons achou o áudio confuso. Isso pode deixar as notas mais duras "
                "do que a sua pronúncia real."
            )
    if prepared.rms < 0.012:
        warnings.append("Sua gravação ficou baixa. Aproxime-se do microfone para melhorar a análise.")
    if extra_words:
        listed = ", ".join(f"“{w.strip()}”" for w in extra_words[:4])
        warnings.append(f"Você falou palavra(s) a mais: {listed}.")

    return AnalysisOutput(
        transcript=transcription.text.strip(),
        overall_score=overall,
        overall_color=scoring.color_for(overall),
        words=analyzed,
        duration_seconds=prepared.speech_seconds,
        warnings=warnings,
    )


def analyze_file(wav_path: Path, sentence: dict[str, Any]) -> AnalysisOutput:
    """Atalho para testes: recebe um WAV ja convertido."""
    prepared = PreparedAudio(
        wav_path=wav_path,
        duration_seconds=0.0,
        speech_seconds=_wav_duration(wav_path),
        rms=0.05,
        peak=0.5,
        used_ffmpeg=True,
    )
    return run_analysis(prepared, sentence)


def _wav_duration(path: Path) -> float:
    from .audio import load_mono_16k

    return round(load_mono_16k(path).size / 16000.0, 3)


def to_schema_words(analysis: AnalysisOutput) -> list[dict[str, Any]]:
    """Converte para os dicionarios que o Pydantic valida (WordScore)."""
    return [
        {
            "text": word.text,
            "normalized": word.normalized or normalize_word(word.text),
            "score": word.score,
            "color": word.color,
            "presence": word.presence,
            "phonemes": [
                {"expected": p.expected, "heard": p.heard, "score": p.score, "tip": p.tip}
                for p in word.phonemes
            ],
            "tip": word.tip,
        }
        for word in analysis.words
    ]


__all__ = ["AnalysisOutput", "WordAnalysis", "PhonemeAnalysis", "run_analysis", "analyze_file", "to_schema_words", "AnalysisError"]
