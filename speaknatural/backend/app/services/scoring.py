"""Formula de pontuacao final (palavra -> frase) e cores.

NOTA DA PALAVRA
---------------
    word_score = 0.75 * phoneme_score + 0.25 * presence

- phoneme_score: vem de align.py (fonemas esperados x ouvidos), 0..1.
- presence: o quanto a palavra apareceu na transcricao do whisper:
      1.0  = transcrita exatamente igual
      0.5  = palavra parecida (ex.: "think" virou "sink") -> provavel troca
      0.0  = nao apareceu (voce pulou a palavra)

Casos especiais (documentados para voce saber o que esperar):

1. Palavra NAO falada (presence = 0): a nota e limitada a 0.25, para ficar
   vermelha mesmo que o modelo de fonemas tenha "alucinado" algo parecido no
   trecho de audio.

2. Palavras MUITO curtas (1 ou 2 fonemas - "a", "of", "to"): o reconhecedor de
   fonemas tem pouco audio para trabalhar e erra muito. Nesses casos damos
   peso igual as duas fontes: 0.5 * phoneme + 0.5 * presence.

3. Se o servidor nao conseguiu gerar fonemas para a palavra (palavra fora do
   dicionario e espeak indisponivel), a nota e apenas `presence`, e uma
   mensagem de aviso explica isso.

NOTA GERAL DA FRASE
-------------------
Media PONDERADA das palavras, com peso = numero de fonemas esperados
(minimo 1). Ou seja: "working" pesa mais que "a". Isso aproxima a nota da
sensacao real de "quao bem eu li a frase", e nao de "quantas palavras
pequenas eu acertei".

    overall = soma(peso * nota_palavra) / soma(peso)

CORES (exatamente as faixas do escopo)
    verde:    nota >= 0.85
    amarelo:  0.50 <= nota < 0.85
    vermelho: nota < 0.50
"""

from __future__ import annotations

from ..config import GREEN_MIN, YELLOW_MIN

PRESENCE_WEIGHT = 0.25
PHONEME_WEIGHT = 0.75
SHORT_WORD_MAX_PHONEMES = 2
MISSING_PENALTY_CAP = 0.25
SHORT_WORD_RECOGNIZED_FLOOR = 0.95  # piso p/ palavra curta reconhecida


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def color_for(score: float) -> str:
    """Verde / amarelo / vermelho conforme as faixas do escopo."""
    if score >= GREEN_MIN:
        return "green"
    if score >= YELLOW_MIN:
        return "yellow"
    return "red"


def word_score(
    phoneme_score: float | None,
    presence: float,
    expected_phoneme_count: int,
) -> float:
    """Combina fonemas + presenca na transcricao (ver comentario do modulo)."""
    presence = clamp(presence)

    # (1) Palavra que o whisper nao ouviu: vermelho garantido.
    if presence <= 0.0:
        base = phoneme_score if phoneme_score is not None else 0.0
        return round(min(MISSING_PENALTY_CAP, MISSING_PENALTY_CAP * base), 4)

    # (3) Sem fonemas esperados: so a transcricao decide.
    if phoneme_score is None:
        return round(clamp(presence), 4)

    # (2) Palavras curtas: peso igual para as duas fontes.
    if expected_phoneme_count <= SHORT_WORD_MAX_PHONEMES:
        score = 0.5 * phoneme_score + 0.5 * presence
        # O modelo de fonemas quase nao tem audio em palavras de 1 som ("a",
        # "of"): se a transcricao reconheceu a palavra, nao punimos por ruido.
        if presence >= 1.0 and expected_phoneme_count <= 1:
            score = max(score, SHORT_WORD_RECOGNIZED_FLOOR)
        elif presence >= 1.0 and phoneme_score >= 0.5:
            score = max(score, SHORT_WORD_RECOGNIZED_FLOOR - 0.05)
        return round(clamp(score), 4)

    score = PHONEME_WEIGHT * phoneme_score + PRESENCE_WEIGHT * presence
    return round(clamp(score), 4)


def overall_score(word_scores: list[tuple[float, int]]) -> float:
    """Media ponderada pelo numero de fonemas de cada palavra.

    `word_scores` = [(nota_da_palavra, qtd_de_fonemas_esperados), ...]
    """
    if not word_scores:
        return 0.0
    total_weight = sum(max(1, count) for _, count in word_scores)
    if total_weight == 0:
        return 0.0
    total = sum(max(1, count) * clamp(score) for score, count in word_scores)
    return round(clamp(total / total_weight), 4)
