"""Utilidades de texto: tokenizacao das frases e normalizacao de palavras."""

from __future__ import annotations

import re

#: Palavras = letras + apostrofo interno (don't, I've, should've).
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")

#: Contracoes com apostrofo tipografico (’) sao normalizadas para (').
_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "`": "'"})


def normalize_word(word: str) -> str:
    """Minusculas, sem pontuacao, apostrofo padrao. Base das comparacoes."""
    cleaned = word.translate(_APOSTROPHES).strip().lower()
    cleaned = cleaned.strip(".,!?;:\"()[]…-–—")
    return cleaned


def split_words(text: str) -> list[str]:
    """Quebra a frase em palavras preservando a forma escrita (para exibir).

    "I've been working, right?" -> ["I've", "been", "working", "right"]
    """
    return [m.group(0).replace("’", "'") for m in _WORD_RE.finditer(text.translate(_APOSTROPHES))]


def words_with_punctuation(text: str) -> list[tuple[str, str]]:
    """Devolve (palavra, pontuacao_seguinte) para montar a frase colorida.

    Ex.: "I'm fine, thanks!" -> [("I'm", ""), ("fine", ","), ("thanks", "!")]
    """
    result: list[tuple[str, str]] = []
    for match in _WORD_RE.finditer(text.translate(_APOSTROPHES)):
        tail = text[match.end():]
        punct = ""
        for char in tail:
            if char in ".,!?;:…":
                punct += char
            else:
                break
        result.append((match.group(0).replace("’", "'"), punct))
    return result


def similarity_ratio(a: str, b: str) -> float:
    """Similaridade 0..1 entre duas palavras (difflib), usada para 'quase certo'."""
    from difflib import SequenceMatcher

    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()
