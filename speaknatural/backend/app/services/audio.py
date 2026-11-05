"""Audio: recebe webm/ogg/m4a/wav, converte para WAV 16 kHz mono e valida.

Por que converter tudo?
-----------------------
O wav2vec2 e o faster-whisper esperam **16 kHz, mono, float32**. O celular grava
webm/opus (Android) ou mp4/aac (iPhone). Quem faz essa conversao e o ffmpeg:

    ffmpeg -i entrada.webm -vn -ac 1 -ar 16000 -f wav -acodec pcm_s16le saida.wav

Se o ffmpeg nao estiver instalado, existe um plano B em Python puro que so
funciona quando o audio ja e WAV (o navegador do PC pode gravar wav em alguns
casos). O /health avisa quando o ffmpeg esta faltando.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import (
    FFMPEG_BIN,
    MAX_AUDIO_SECONDS,
    MIN_AUDIO_SECONDS,
    SILENCE_RMS_THRESHOLD,
    TARGET_SAMPLE_RATE,
)
from .errors import ERR_AUDIO_TOO_LONG, ERR_AUDIO_TOO_SHORT, ERR_CONVERT, ERR_FFMPEG_MISSING, ERR_SILENCE

logger = logging.getLogger(__name__)


@dataclass
class PreparedAudio:
    """Resultado da preparacao: WAV 16 kHz mono pronto para os modelos."""

    wav_path: Path
    duration_seconds: float   # duracao total do arquivo convertido
    speech_seconds: float     # duracao depois de cortar o silencio das pontas
    rms: float                # volume medio (0..1)
    peak: float               # pico (0..1)
    used_ffmpeg: bool


def ffmpeg_available() -> bool:
    """Testa se o ffmpeg responde. Faz cache simples para nao chamar sempre."""
    global _FFMPEG_CHECKED, _FFMPEG_OK
    if _FFMPEG_CHECKED:
        return _FFMPEG_OK
    _FFMPEG_CHECKED = True
    binary = shutil.which(FFMPEG_BIN) or (FFMPEG_BIN if Path(FFMPEG_BIN).exists() else None)
    if not binary:
        _FFMPEG_OK = False
        return False
    try:
        subprocess.run(
            [binary, "-hide_banner", "-version"],
            capture_output=True,
            timeout=15,
            check=True,
        )
        _FFMPEG_OK = True
    except Exception as exc:  # pragma: no cover
        logger.warning("ffmpeg nao executou: %s", exc)
        _FFMPEG_OK = False
    return _FFMPEG_OK


_FFMPEG_CHECKED = False
_FFMPEG_OK = False


def convert_to_wav_ffmpeg(source: Path, destination: Path) -> None:
    """Converte qualquer audio suportado pelo ffmpeg para WAV PCM 16 kHz mono."""
    binary = shutil.which(FFMPEG_BIN) or FFMPEG_BIN
    command = [
        binary,
        "-nostdin",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(source),
        "-vn",                    # ignora video (webm pode ter video)
        "-ac", "1",               # mono
        "-ar", str(TARGET_SAMPLE_RATE),  # 16 kHz
        "-acodec", "pcm_s16le",
        "-f", "wav",
        str(destination),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, timeout=120)
    except FileNotFoundError:
        raise ERR_FFMPEG_MISSING from None
    except subprocess.TimeoutExpired:
        raise ERR_CONVERT from None

    if completed.returncode != 0 or not destination.exists() or destination.stat().st_size < 64:
        detail = (completed.stderr or b"").decode("utf-8", "ignore").strip()[:300]
        logger.warning("ffmpeg falhou: %s", detail)
        raise ERR_CONVERT


def _read_wav_any(path: Path) -> tuple[np.ndarray, int]:
    """Le WAV com soundfile e devolve (mono float32, sample_rate)."""
    import soundfile as sf

    data, sample_rate = sf.read(str(path), dtype="float32", always_2d=True)
    mono = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]
    return np.ascontiguousarray(mono, dtype=np.float32), int(sample_rate)


def _resample_linear(samples: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    """Reamostragem linear simples (plano B, sem ffmpeg)."""
    if from_rate == to_rate or samples.size == 0:
        return samples
    duration = samples.size / float(from_rate)
    target_count = int(round(duration * to_rate))
    if target_count <= 1:
        return samples
    source_positions = np.linspace(0.0, duration, num=samples.size, endpoint=False)
    target_positions = np.linspace(0.0, duration, num=target_count, endpoint=False)
    return np.interp(target_positions, source_positions, samples).astype(np.float32)


def prepare_audio(source: Path, workdir: Path, stem: str = "converted") -> PreparedAudio:
    """Valida e normaliza o audio recebido do app.

    Levanta AnalysisError (mensagem em portugues) quando:
      * o audio nao pode ser convertido  -> ffmpeg ausente / arquivo corrompido
      * duracao < MIN_AUDIO_SECONDS      -> "audio_too_short"
      * duracao > MAX_AUDIO_SECONDS      -> "audio_too_long"
      * volume abaixo do limiar          -> "no_speech"
    """
    destination = workdir / f"{stem}.wav"
    used_ffmpeg = False

    if ffmpeg_available():
        convert_to_wav_ffmpeg(source, destination)
        used_ffmpeg = True
    else:
        # Plano B: sem ffmpeg so aceitamos WAV.
        if source.suffix.lower() not in {".wav", ".wave"}:
            raise ERR_FFMPEG_MISSING
        samples, sample_rate = _read_wav_any(source)
        samples = _resample_linear(samples, sample_rate, TARGET_SAMPLE_RATE)
        import soundfile as sf

        sf.write(str(destination), samples, TARGET_SAMPLE_RATE, subtype="FLOAT")

    samples, sample_rate = _read_wav_any(destination)
    if sample_rate != TARGET_SAMPLE_RATE:  # pragma: no cover - ffmpeg sempre acerta
        samples = _resample_linear(samples, sample_rate, TARGET_SAMPLE_RATE)

    total_seconds = samples.size / float(TARGET_SAMPLE_RATE)
    if total_seconds < MIN_AUDIO_SECONDS:
        raise ERR_AUDIO_TOO_SHORT
    if total_seconds > MAX_AUDIO_SECONDS:
        raise ERR_AUDIO_TOO_LONG

    # Corta o silencio das pontas (melhora o alinhamento dos fonemas) e
    # garante que existe fala de verdade no arquivo.
    trimmed = trim_silence(samples, TARGET_SAMPLE_RATE)
    speech_seconds = trimmed.size / float(TARGET_SAMPLE_RATE)
    if speech_seconds < MIN_AUDIO_SECONDS:
        raise ERR_SILENCE

    rms = float(np.sqrt(np.mean(np.square(trimmed), dtype=np.float64)))
    peak = float(np.max(np.abs(trimmed))) if trimmed.size else 0.0
    if rms < SILENCE_RMS_THRESHOLD:
        raise ERR_SILENCE

    if trimmed.size != samples.size:
        import soundfile as sf

        sf.write(str(destination), trimmed, TARGET_SAMPLE_RATE, subtype="FLOAT")

    return PreparedAudio(
        wav_path=destination,
        duration_seconds=round(total_seconds, 3),
        speech_seconds=round(speech_seconds, 3),
        rms=round(rms, 5),
        peak=round(peak, 5),
        used_ffmpeg=used_ffmpeg,
    )


def trim_silence(
    samples: np.ndarray,
    sample_rate: int = TARGET_SAMPLE_RATE,
    threshold_ratio: float = 0.06,
    pad_seconds: float = 0.12,
) -> np.ndarray:
    """Remove silencio do comeco/fim mantendo 120 ms de folga.

    O limiar e relativo ao pico do proprio arquivo (6%), o que funciona tanto
    para gravacao alta quanto baixa.
    """
    if samples.size == 0:
        return samples
    peak = float(np.max(np.abs(samples)))
    if peak <= 1e-6:
        return samples
    threshold = max(peak * threshold_ratio, SILENCE_RMS_THRESHOLD * 0.5)
    above = np.where(np.abs(samples) > threshold)[0]
    if above.size == 0:
        return samples
    pad = int(pad_seconds * sample_rate)
    start = max(0, int(above[0]) - pad)
    end = min(samples.size, int(above[-1]) + pad)
    return np.ascontiguousarray(samples[start:end], dtype=np.float32)


def load_mono_16k(path: Path) -> np.ndarray:
    """Le o WAV e devolve float32 mono 16 kHz (entrada dos modelos)."""
    samples, sample_rate = _read_wav_any(path)
    if sample_rate != TARGET_SAMPLE_RATE:
        samples = _resample_linear(samples, sample_rate, TARGET_SAMPLE_RATE)
    return np.ascontiguousarray(samples, dtype=np.float32)
