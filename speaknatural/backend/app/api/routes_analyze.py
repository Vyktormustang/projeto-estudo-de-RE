"""POST /analyze - recebe o audio + sentence_id e devolve a analise completa."""

from __future__ import annotations

import logging
import shutil
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ..config import MAX_UPLOAD_BYTES, TMP_DIR
from ..data.sentences import get_sentence
from ..db import get_db
from ..schemas import AnalyzeResponse
from ..services import analyzer, history
from ..services.audio import prepare_audio
from ..services.errors import (
    ERR_AUDIO_TOO_SHORT,
    ERR_EMPTY_AUDIO,
    ERR_NO_SENTENCE,
    ERR_UPLOAD_TOO_BIG,
    AnalysisError,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["análise"])

#: Um modelo de IA por vez. O wav2vec2 usa ~1,5 GB de RAM; dois pedidos
#: simultâneos derrubariam um PC de 8 GB. Os pedidos esperam na fila.
_ANALYSIS_LOCK = threading.Lock()

_ALLOWED_EXTENSIONS = {".webm", ".ogg", ".oga", ".wav", ".wave", ".mp3", ".m4a", ".aac", ".mp4", ".opus", ".caf", ".3gp"}


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analisa a pronúncia de uma frase",
    responses={
        400: {"description": "Áudio vazio ou frase inexistente"},
        413: {"description": "Áudio grande demais"},
        422: {"description": "Áudio curto demais ou sem fala"},
        503: {"description": "Modelos de IA ainda não prontos"},
    },
)
def analyze(
    audio: UploadFile = File(..., description="Gravação da sua voz (webm, ogg, wav, m4a...)"),
    sentence_id: str = Form(..., description="id da frase, ex.: m07 (vem de GET /sentences)"),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    sentence = get_sentence(sentence_id)
    if sentence is None:
        raise ERR_NO_SENTENCE

    if audio is None or not audio.filename:
        raise ERR_EMPTY_AUDIO

    suffix = Path(audio.filename).suffix.lower() or ".webm"
    if suffix not in _ALLOWED_EXTENSIONS:
        suffix = ".webm"  # o ffmpeg descobre o formato pelo conteudo

    token = uuid.uuid4().hex[:12]
    source = TMP_DIR / f"upload-{token}{suffix}"
    workdir = TMP_DIR / f"work-{token}"
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        written = _save_upload(audio, source)
        if written == 0:
            raise ERR_EMPTY_AUDIO
        if written > MAX_UPLOAD_BYTES:
            raise ERR_UPLOAD_TOO_BIG

        prepared = prepare_audio(source, workdir, stem=f"audio-{token}")
        if prepared.speech_seconds <= 0:
            raise ERR_AUDIO_TOO_SHORT

        with _ANALYSIS_LOCK:
            output = analyzer.run_analysis(prepared, sentence)

        attempt = history.save_attempt(db, sentence, output, output.transcript)

        return AnalyzeResponse(
            attempt_id=attempt.id,
            sentence_id=sentence["id"],
            sentence_text=sentence["text"],
            level=sentence["level"],
            transcript=output.transcript,
            overall_score=output.overall_score,
            overall_color=output.overall_color,
            words=analyzer.to_schema_words(output),
            duration_seconds=output.duration_seconds,
            created_at=attempt.created_at,
            warnings=output.warnings,
        )
    finally:
        # Nada de audio do usuario fica no disco: apagamos sempre.
        _cleanup(source, workdir)


def _save_upload(upload: UploadFile, destination: Path) -> int:
    """Grava o upload em disco, com teto de tamanho. Devolve bytes gravados."""
    size = 0
    with destination.open("wb") as handle:
        while True:
            chunk = upload.file.read(1024 * 256)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                break
            handle.write(chunk)
    return size


def _cleanup(*paths: Path) -> None:
    for path in paths:
        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            elif path.exists():
                path.unlink()
        except OSError:  # pragma: no cover
            logger.warning("Nao consegui apagar %s", path)


__all__ = ["router", "AnalysisError"]
