"""Casa as palavras da FRASE com as palavras que o whisper TRANSCREVEU.

Resultado por palavra esperada:
  * presence 1.0 -> a palavra foi transcrita igualzinha
  * presence 0.5 -> veio uma palavra parecida ("think" -> "sink")
  * presence 0.0 -> nao apareceu (pulou a palavra)
  * window (start, end) -> trecho de audio daquela palavra, para recortar os
    fonemas do wav2vec2.

Se o whisper nao devolver tempos (acontece quando o audio e muito curto ou o
modelo cai num segmento sem words), distribuimos o tempo proporcionalmente ao
tamanho das palavras, para a analise nao morrer.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .asr import ASRWord
from .text import normalize_word, similarity_ratio

#: Acima disso consideramos que o aluno falou "uma palavra parecida".
SIMILAR_WORD_RATIO = 0.62


@dataclass
class WordMatch:
    index: int
    text: str
    normalized: str
    presence: float
    window: tuple[float, float] | None = None
    heard_text: str | None = None


def match_words(
    expected_words: list[str],
    asr_words: list[ASRWord],
    speech_duration: float,
) -> tuple[list[WordMatch], list[str]]:
    """Alinha as palavras esperadas com as transcritas.

    Retorna (lista_de_matches, palavras_extras_faladas).
    """
    matches = [
        WordMatch(index=i, text=word, normalized=normalize_word(word), presence=0.0)
        for i, word in enumerate(expected_words)
    ]

    hyp_norm = [normalize_word(w.text) for w in asr_words]
    exp_norm = [m.normalized for m in matches]

    used_hyp: set[int] = set()
    matcher = SequenceMatcher(None, exp_norm, hyp_norm, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(min(i2 - i1, j2 - j1)):
                _attach(matches[i1 + offset], asr_words[j1 + offset], presence=1.0)
                used_hyp.add(j1 + offset)
        elif tag == "replace":
            span = min(i2 - i1, j2 - j1)
            for offset in range(span):
                heard = asr_words[j1 + offset]
                ratio = similarity_ratio(exp_norm[i1 + offset], normalize_word(heard.text))
                if ratio >= SIMILAR_WORD_RATIO:
                    _attach(matches[i1 + offset], heard, presence=0.5)
                    used_hyp.add(j1 + offset)
                elif ratio >= 0.4:
                    # Palavra comecou parecida: presenca minima, fica vermelho.
                    _attach(matches[i1 + offset], heard, presence=0.25)
                    used_hyp.add(j1 + offset)
        # "delete": palavra esperada nao apareceu  -> presence fica 0
        # "insert": palavra extra do aluno           -> listada abaixo

    extra_words = [asr_words[j].text for j in range(len(asr_words)) if j not in used_hyp]

    _ensure_windows(matches, speech_duration)
    return matches, extra_words


def _attach(match: WordMatch, asr_word: ASRWord, presence: float) -> None:
    match.presence = presence
    match.heard_text = asr_word.text
    if asr_word.end > asr_word.start:
        match.window = (max(0.0, float(asr_word.start)), float(asr_word.end))


def _ensure_windows(matches: list[WordMatch], speech_duration: float) -> None:
    """Preenche janelas faltantes com distribuicao proporcional."""
    if not matches:
        return
    usable = [m for m in matches if m.window is not None]
    timestamps_broken = not usable or all((w[1] - w[0]) <= 0.01 for w in (m.window for m in usable))
    if timestamps_broken and speech_duration > 0:
        # Sem tempos confiaveis: divide o audio inteiro na ordem das palavras,
        # dando mais tempo as palavras longas.
        weights = [max(1, len(m.text)) for m in matches]
        total = sum(weights)
        cursor = 0.0
        for match, weight in zip(matches, weights):
            span = speech_duration * (weight / total)
            match.window = (round(cursor, 3), round(cursor + span, 3))
            cursor += span
        return

    # Corrige janelas invertidas/zeradas pontuais.
    for index, match in enumerate(matches):
        if match.window is None:
            continue
        start, end = match.window
        if end <= start:
            neighbors = [m.window for m in matches[max(0, index - 1): index + 2] if m.window]
            end = start + 0.25 if not neighbors else start + 0.25
            match.window = (start, min(end, max(speech_duration, start + 0.05)))
