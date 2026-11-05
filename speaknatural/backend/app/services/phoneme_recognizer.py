"""Reconhecimento de FONEMAS (IPA) com wav2vec2 + decodificacao CTC.

Modelo: facebook/wav2vec2-xlsr-53-espeak-cv-ft
  * foi treinado para emitir fonemas no formato do espeak-ng;
  * roda em CPU (mas e o passo mais lento: ~1x o tempo do audio);
  * baixa ~1,2 GB na primeira vez.

Como funciona:
  1. O audio (16 kHz mono) passa pelo modelo e vira uma sequencia de
     distribuicoes de probabilidade, uma por "frame" (~20 ms cada);
  2. Pegamos o simbolo mais provavel de cada frame (argmax);
  3. Decodificacao CTC: repetidos seguidos viram um so e os "blanks" (id 0)
     sao descartados -> sobra a sequencia de fonemas;
  4. Cada fonema fica com um intervalo de tempo, o que permite comparar so o
     trecho de audio daquela palavra.
"""

from __future__ import annotations

import logging
import math
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import DISABLE_MODELS, PHONEME_MODEL, TARGET_SAMPLE_RATE
from . import ipa
from .audio import load_mono_16k
from .errors import ERR_MODELS_DISABLED, ERR_MODELS_LOADING, AnalysisError

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_processor = None
_model = None
_state = "nao carregado"
_last_error: str | None = None
_frame_ratio: int = 320  # amostras por frame do wav2vec2 (xlsr-53: 20 ms a 16 kHz)


@dataclass(frozen=True)
class TimedPhoneme:
    symbol: str
    start: float
    end: float


@dataclass
class Recognition:
    phonemes: list[TimedPhoneme]
    confidence: float

    @property
    def symbols(self) -> list[str]:
        return [p.symbol for p in self.phonemes]

    def in_window(self, start: float, end: float, pad: float = 0.06) -> list[str]:
        """Fonemas cujo centro cai dentro de [start-pad, end+pad]."""
        low = max(0.0, start - pad)
        high = end + pad
        picked: list[str] = []
        for phoneme in self.phonemes:
            center = (phoneme.start + phoneme.end) / 2.0
            if low <= center <= high:
                picked.append(phoneme.symbol)
        return picked


def state() -> tuple[str, str | None]:
    return _state, _last_error


def get_model():
    """Carrega processor + modelo wav2vec2 uma vez (thread-safe)."""
    global _processor, _model, _state, _last_error, _frame_ratio
    if _model is not None:
        return _processor, _model
    if DISABLE_MODELS:
        raise ERR_MODELS_DISABLED
    with _lock:
        if _model is not None:
            return _processor, _model
        _state = "carregando"
        try:
            import torch
            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

            logger.info("Carregando %s (CPU)...", PHONEME_MODEL)
            _processor = Wav2Vec2Processor.from_pretrained(PHONEME_MODEL)
            _model = Wav2Vec2ForCTC.from_pretrained(PHONEME_MODEL)
            _model.eval()
            _model.to("cpu")
            torch.set_num_threads(max(1, (torch.get_num_threads() or 4)))
            strides = getattr(_model.config, "conv_stride", None)
            if strides:
                _frame_ratio = int(math.prod(int(s) for s in strides))
            _state = "pronto"
            _last_error = None
            logger.info("wav2vec2 pronto (frame = %d amostras).", _frame_ratio)
        except AnalysisError:
            _state = "erro"
            raise
        except Exception as exc:
            _state = "erro"
            _last_error = str(exc)
            logger.exception("Falha ao carregar o wav2vec2")
            raise ERR_MODELS_LOADING from exc
    return _processor, _model


def recognize(wav_path: Path) -> Recognition:
    """Reconhece a sequencia de fonemas IPA com tempos."""
    import torch

    processor, model = get_model()
    samples = load_mono_16k(wav_path)
    if samples.size == 0:
        return Recognition(phonemes=[], confidence=0.0)

    try:
        inputs = processor(samples, sampling_rate=TARGET_SAMPLE_RATE, return_tensors="pt")
        with torch.no_grad():
            logits = model(inputs.input_values).logits[0]  # (frames, vocab)
        probabilities = torch.softmax(logits, dim=-1)
        best_ids = torch.argmax(logits, dim=-1).tolist()
        best_probs = probabilities.max(dim=-1).values.tolist()
    except Exception as exc:
        logger.exception("Falha no wav2vec2")
        raise ERR_MODELS_LOADING from exc

    vocabulary: dict[int, str] = {
        idx: token for token, idx in processor.tokenizer.get_vocab().items()
    }
    blank_id = processor.tokenizer.pad_token_id
    if blank_id is None:
        blank_id = 0

    seconds_per_frame = _frame_ratio / float(TARGET_SAMPLE_RATE)
    phonemes: list[TimedPhoneme] = []
    confidences: list[float] = []

    previous_id: int | None = None
    run_start_frame = 0
    for frame_index, token_id in enumerate(best_ids):
        if token_id == previous_id:
            # mesma classe CTC: continua o "run" (nao emite de novo)
            continue
        # fecha o run anterior
        if previous_id is not None and previous_id != blank_id:
            _emit(phonemes, vocabulary, previous_id, run_start_frame, frame_index, seconds_per_frame)
        previous_id = token_id
        run_start_frame = frame_index
        if token_id != blank_id:
            confidences.append(float(best_probs[frame_index]))
    if previous_id is not None and previous_id != blank_id:
        _emit(phonemes, vocabulary, previous_id, run_start_frame, len(best_ids), seconds_per_frame)

    confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
    logger.info("Fonemas reconhecidos: %s", "".join(p.symbol for p in phonemes)[:160])
    return Recognition(phonemes=phonemes, confidence=confidence)


def _emit(
    phonemes: list[TimedPhoneme],
    vocabulary: dict[int, str],
    token_id: int,
    start_frame: int,
    end_frame: int,
    seconds_per_frame: float,
) -> None:
    """Converte um token do vocabulario em um ou mais fonemas IPA com tempo."""
    token = vocabulary.get(token_id, "")
    if not token:
        return
    symbols = ipa.tokenize(token)
    if not symbols:
        return
    start = start_frame * seconds_per_frame
    end = max(end_frame, start_frame + 1) * seconds_per_frame
    if len(symbols) == 1:
        phonemes.append(TimedPhoneme(symbols[0], round(start, 3), round(end, 3)))
        return
    # Token com varios simbolos (ex.: "tʃ"): divide o tempo igualmente.
    step = (end - start) / len(symbols)
    for index, symbol in enumerate(symbols):
        phonemes.append(
            TimedPhoneme(symbol, round(start + index * step, 3), round(start + (index + 1) * step, 3))
        )


def phonemes_to_string(phonemes: list[str]) -> str:
    return " ".join(phonemes)
