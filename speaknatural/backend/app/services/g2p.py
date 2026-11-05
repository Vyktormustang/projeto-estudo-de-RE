"""Fonemas ESPERADOS (o "gabarito") de cada palavra.

Motor principal: `phonemizer` falando com o espeak-ng (idioma en-us).
plano B: um dicionario embutido (data/fallback_phonemes.json) gerado a partir do
dicionario CMU, para o app continuar funcionando se o espeak-ng nao estiver
instalado no PC. O plano B e avisado na resposta da API (`warnings`) para voce
saber que a comparacao esta menos precisa.
"""

from __future__ import annotations

import json
import logging
import threading
from functools import lru_cache
from pathlib import Path

import os
import sys

from ..config import ESPEAK_PATH, PHONEMIZER_LANGUAGE
from . import ipa

logger = logging.getLogger(__name__)

_FALLBACK_PATH = Path(__file__).resolve().parent.parent / "data" / "fallback_phonemes.json"

_lock = threading.Lock()
_backend = None                 # instancia do EspeakBackend
_backend_tried = False
_backend_ok = False
_backend_error: str | None = None
_fallback_dict: dict[str, str] | None = None


def _load_fallback() -> dict[str, str]:
    global _fallback_dict
    if _fallback_dict is None:
        try:
            with _FALLBACK_PATH.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            _fallback_dict = {str(k).lower(): str(v) for k, v in data.get("words", {}).items()}
        except Exception as exc:  # pragma: no cover - arquivo ausente/corrompido
            logger.warning("fallback_phonemes.json indisponivel: %s", exc)
            _fallback_dict = {}
    return _fallback_dict


def _configure_espeak_path() -> None:
    """Ajuda o phonemizer a achar o espeak-ng quando ele nao esta no PATH.

    Use SN_ESPEAK_PATH (ex.: C:\\Program Files\\eSpeak NG). O phonemizer le
    PHONEMIZER_ESPEAK_LIBRARY / PHONEMIZER_ESPEAK_PATH, entao apontamos as duas
    coisas e, no Windows, tambem liberamos a DLL da pasta.
    """
    if not ESPEAK_PATH:
        return
    folder = Path(ESPEAK_PATH)
    if not folder.is_dir():
        logger.warning("SN_ESPEAK_PATH aponta para uma pasta inexistente: %s", folder)
        return
    os.environ["PATH"] = f"{folder}{os.pathsep}" + os.environ.get("PATH", "")
    if sys.platform.startswith("win"):
        library = folder / "libespeak-ng.dll"
        executable = folder / "espeak-ng.exe"
        if library.exists():
            os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", str(library))
            if hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(str(folder))
                except OSError:  # pragma: no cover
                    pass
        if executable.exists():
            os.environ.setdefault("PHONEMIZER_ESPEAK_PATH", str(executable))


def _get_backend():
    """Cria (uma vez) o backend espeak-ng. Devolve None se nao for possivel."""
    global _backend, _backend_tried, _backend_ok, _backend_error
    if _backend_tried:
        return _backend
    with _lock:
        if _backend_tried:
            return _backend
        _backend_tried = True
        try:
            _configure_espeak_path()
            from phonemizer.backend import EspeakBackend

            backend = EspeakBackend(
                language=PHONEMIZER_LANGUAGE,
                preserve_punctuation=False,
                with_stress=False,
                tie=False,
            )
            # Teste rapido: se o espeak-ng nao estiver instalado isso explode aqui.
            backend.phonemize(["test"], strip=True, njobs=1)
            _backend = backend
            _backend_ok = True
            logger.info("phonemizer/espeak-ng pronto (%s)", PHONEMIZER_LANGUAGE)
        except Exception as exc:  # libespeak nao encontrada, etc.
            _backend = None
            _backend_ok = False
            _backend_error = str(exc)
            logger.warning(
                "espeak-ng indisponivel (%s). Usando dicionario embutido de fonemas.", exc
            )
    return _backend


@lru_cache(maxsize=4096)
def word_phonemes(word: str) -> tuple[str, ...] | None:
    """Fonemas IPA esperados de UMA palavra. None = desconhecido."""
    normalized = word.strip().lower()
    if not normalized:
        return ()
    backend = _get_backend()
    if backend is not None:
        try:
            result = backend.phonemize([normalized], strip=True, njobs=1)
            tokens = ipa.tokenize(result[0]) if result else []
            if tokens:
                return tuple(tokens)
        except Exception as exc:  # pragma: no cover
            logger.warning("falha ao fonemizar %r: %s", word, exc)

    spelled = _load_fallback().get(normalized)
    if spelled:
        return tuple(ipa.tokenize(spelled))
    return None


def sentence_phonemes(words: list[str]) -> list[list[str] | None]:
    """Fonemas esperados de cada palavra da frase, na ordem."""
    return [list(result) if result is not None else None for result in map(word_phonemes, words)]


def engine_status() -> tuple[str, str | None]:
    """(status_para_o_health, mensagem_de_aviso)"""
    backend = _get_backend()
    if backend is not None:
        return ("espeak-ng", None)
    detail = _backend_error or "libespeak-ng nao encontrada"
    return (
        "fallback-dictionary",
        "O espeak-ng não está instalado no PC do servidor; usando um dicionário embutido de fonemas "
        f"(precisão menor). Detalhe: {detail[:160]}",
    )
