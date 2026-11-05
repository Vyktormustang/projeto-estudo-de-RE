"""GET /health - o app usa isso na tela "Servidor" ("Testar conexão")."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from .. import __version__
from ..config import DISABLE_MODELS, FAKE_MODELS, WHISPER_MODEL, PHONEME_MODEL
from ..schemas import HealthResponse
from ..services import asr, audio, g2p, phoneme_recognizer

router = APIRouter(tags=["sistema"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Testa se o servidor está no ar e se os modelos estão prontos",
)
def health() -> HealthResponse:
    messages: list[str] = []
    ffmpeg_ok = audio.ffmpeg_available()
    if not ffmpeg_ok:
        messages.append(
            "ffmpeg não encontrado no PC do servidor. Instale o ffmpeg (passo 1.2 do README)."
        )

    whisper_state, whisper_error = asr.state()
    phoneme_state, phoneme_error = phoneme_recognizer.state()
    g2p_status, g2p_warning = g2p.engine_status()
    if g2p_warning:
        messages.append(g2p_warning)

    if DISABLE_MODELS:
        messages.append("Servidor em modo somente API (SN_DISABLE_MODELS=1): /analyze vai responder 503.")
        whisper_state = "desativado"
        phoneme_state = "desativado"
    elif FAKE_MODELS:
        messages.append("Servidor em modo demonstração (SN_FAKE_MODELS=1): as notas são simuladas.")

    if whisper_error:
        messages.append(f"Erro no modelo de transcrição: {whisper_error[:200]}")
    if phoneme_error:
        messages.append(f"Erro no modelo de fonemas: {phoneme_error[:200]}")

    # "degraded" nao significa quebrado: significa que falta algo (ffmpeg ou
    # algum modelo falhou ao carregar). Modelos "nao carregado" e normal: eles
    # carregam na primeira analise.
    status = "ok" if ffmpeg_ok and not whisper_error and not phoneme_error else "degraded"

    return HealthResponse(
        status=status,
        version=__version__,
        database="sqlite",
        ffmpeg=ffmpeg_ok,
        whisper=f"{WHISPER_MODEL}: {whisper_state}",
        phonemes=f"{PHONEME_MODEL.split('/')[-1]}: {phoneme_state} | esperado: {g2p_status}",
        fake_models=FAKE_MODELS,
        messages=messages,
        server_time=datetime.now(timezone.utc),
    )
