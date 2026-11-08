"""Transcricao com faster-whisper ("small.en", CPU, int8) + tempos por palavra.

Para que serve no app:
  1. saber QUAIS palavras voce falou (detecta palavra pulada -> vermelho);
  2. saber QUANDO cada palavra foi falada (recorte de audio para o wav2vec2);

O modelo e carregado na primeira analise (lazy) porque leva ~10 s e ~1 GB de
RAM. O download unico (uma vez so) fica em cache no seu PC
(Windows: %LOCALAPPDATA%\\huggingface, Linux/Mac: ~/.cache/huggingface).
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path

from ..config import (
    DISABLE_MODELS,
    WHISPER_BEAM_SIZE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_MODEL,
)
from .errors import ERR_MODELS_DISABLED, ERR_MODELS_LOADING, AnalysisError

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_model = None
_state: str = "nao carregado"      # "nao carregado" | "carregando" | "pronto" | "erro"
_last_error: str | None = None


@dataclass
class ASRWord:
    """Uma palavra transcrita, com tempo em segundos (relativo ao inicio)."""

    text: str
    start: float
    end: float
    probability: float = 1.0


@dataclass
class Transcription:
    text: str
    words: list[ASRWord] = field(default_factory=list)
    language: str = "en"
    confidence: float = 0.0


def state() -> tuple[str, str | None]:
    return _state, _last_error


def get_model():
    """Carrega o WhisperModel uma unica vez (thread-safe)."""
    global _model, _state, _last_error
    if _model is not None:
        return _model
    if DISABLE_MODELS:
        raise ERR_MODELS_DISABLED
    with _lock:
        if _model is not None:
            return _model
        _state = "carregando"
        try:
            from faster_whisper import WhisperModel

            logger.info(
                "Carregando faster-whisper %s (%s, %s)...",
                WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE,
            )
            _model = WhisperModel(
                WHISPER_MODEL,
                device=WHISPER_DEVICE,
                compute_type=WHISPER_COMPUTE_TYPE,
                # 0 threads extras: padrao do ctranslate2 = 1 thread por nucleo
            )
            _state = "pronto"
            _last_error = None
            logger.info("faster-whisper pronto.")
        except AnalysisError:
            _state = "erro"
            raise
        except Exception as exc:
            _state = "erro"
            _last_error = str(exc)
            logger.exception("Falha ao carregar o faster-whisper")
            raise ERR_MODELS_LOADING from exc
    return _model


def transcribe(wav_path: Path) -> Transcription:
    """Transcreve o WAV 16 kHz mono e devolve texto + tempos por palavra."""
    model = get_model()
    try:
        segments, info = model.transcribe(
            str(wav_path),
            language="en",
            beam_size=WHISPER_BEAM_SIZE,
            word_timestamps=True,          # <- necessario para recortar por palavra
            vad_filter=True,               # ignora silencio/ruido, ajuda no ruido de fundo
            vad_parameters={"min_silence_duration_ms": 300},
            condition_on_previous_text=False,
            temperature=0.0,
        )
        words: list[ASRWord] = []
        text_parts: list[str] = []
        for segment in segments:  # generator: o trabalho acontece aqui
            text_parts.append(segment.text)
            for word in getattr(segment, "words", None) or []:
                words.append(
                    ASRWord(
                        text=word.word,
                        start=float(word.start or 0.0),
                        end=float(word.end or 0.0),
                        probability=float(getattr(word, "probability", 1.0) or 1.0),
                    )
                )
        text = "".join(text_parts).strip()
        confidence = sum(w.probability for w in words) / len(words) if words else 0.0
        logger.info(
            "Transcricao (%s, %.1fs de audio): %r",
            getattr(info, "language", "en"),
            getattr(info, "duration", 0.0),
            text[:120],
        )
        return Transcription(
            text=text,
            words=words,
            language=getattr(info, "language", "en") or "en",
            confidence=round(confidence, 3),
        )
    except AnalysisError:
        raise
    except Exception as exc:
        logger.exception("Falha na transcricao")
        raise ERR_MODELS_LOADING from exc
