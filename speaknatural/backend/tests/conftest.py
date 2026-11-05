"""Configuracao dos testes: banco temporario + modo demonstracao (sem IA).

Rodar:
    cd backend
    python -m pytest -q
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TEMP_DIR = Path(tempfile.mkdtemp(prefix="speaknatural-tests-"))

# Variaveis de ambiente precisam existir ANTES de importar app.*
os.environ.setdefault("SN_DATA_DIR", str(_TEMP_DIR))
os.environ.setdefault("SN_DATABASE_URL", f"sqlite:///{_TEMP_DIR / 'test.db'}")
os.environ.setdefault("SN_FAKE_MODELS", "1")
os.environ.setdefault("SN_DISABLE_MODELS", "0")


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def wav_file(tmp_path: Path) -> Path:
    """Gera um WAV sintetico de 2 s (voz simulada) para o upload."""
    import numpy as np
    import soundfile as sf

    sample_rate = 16_000
    seconds = 2.0
    t = np.linspace(0, seconds, int(sample_rate * seconds), endpoint=False)
    # "fala" de mentira: tom modulado, com envelope, para passar nos testes de
    # silencio/duracao.
    signal = 0.25 * np.sin(2 * np.pi * 180 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))
    path = tmp_path / "audio.wav"
    sf.write(str(path), signal.astype("float32"), sample_rate, subtype="PCM_16")
    return path
