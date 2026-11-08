"""Alinhamento de sequencias (Needleman-Wunsch) e pontuacao por fonema.

COMO FUNCIONA (leia antes de mexer nos numeros)
-----------------------------------------------
1. Temos duas sequencias de fonemas:
   - ESPERADO: gerado pelo espeak-ng a partir da palavra (ex.: "speak" -> s p iː k)
   - OUVIDO:   saida CTC do wav2vec2 para o trecho de audio daquela palavra

2. Alinhamos as duas com programacao dinamica, exatamente como no
   alinhamento de sequencias de DNA. Cada celula da matriz pode:
   - casar os dois fonemas  -> ganho = similaridade (0..1)
   - pular um fonema esperado (o aluno NAO falou)   -> penalidade GAP
   - pular um fonema ouvido   (o aluno falou a mais) -> penalidade GAP

   dp[i][j] = max(
       dp[i-1][j-1] + sim(e[i], o[j]),   # casamento
       dp[i-1][j]   + GAP,               # fonema esperado faltando
       dp[i][j-1]   + GAP,               # fonema extra
   )

3. A nota da palavra e a soma das similaridades dos casamentos DIVIDIDA pelo
   tamanho da maior sequencia:

       phoneme_score = soma(sim) / max(len(esperado), len(ouvido))

   Assim: trocar tudo erra, faltar sons erra, falar sons a mais tambem erra
   (o denominador cresce), e acertar tudo da 1.0. O resultado fica em 0..1.

4. A nota final da palavra combina isso com a presenca dela na transcricao
   (ver scoring.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import GAP_PENALTY
from .ipa import phoneme_similarity


@dataclass(frozen=True)
class AlignedPair:
    """Um par do alinhamento. Um dos lados pode ser None (som faltando/extra)."""

    expected: str | None
    heard: str | None
    score: float

    @property
    def is_exact(self) -> bool:
        return self.expected is not None and self.heard is not None and self.expected == self.heard


def align_phonemes(
    expected: list[str],
    heard: list[str],
    gap_penalty: float = GAP_PENALTY,
) -> tuple[list[AlignedPair], float]:
    """Alinha fonemas esperados x ouvidos.

    Retorna (pares_alinhados, nota_dos_fonemas_0_a_1).
    """
    n, m = len(expected), len(heard)
    if n == 0 and m == 0:
        return [], 0.0
    if n == 0 or m == 0:
        # Nada para casar: todos os fonemas de um dos lados estao "faltando".
        pairs = [AlignedPair(e, None, 0.0) for e in expected]
        pairs += [AlignedPair(None, o, 0.0) for o in heard]
        return pairs, 0.0

    # Matriz de pontuacao (n+1) x (m+1), preenchida da borda para dentro.
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap_penalty
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap_penalty

    for i in range(1, n + 1):
        e = expected[i - 1]
        for j in range(1, m + 1):
            sim = phoneme_similarity(e, heard[j - 1])
            dp[i][j] = max(
                dp[i - 1][j - 1] + sim,      # casou
                dp[i - 1][j] + gap_penalty,  # faltou som esperado
                dp[i][j - 1] + gap_penalty,  # som extra
            )

    # Traceback: reconstroi o caminho vencedor.
    pairs_rev: list[AlignedPair] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            sim = phoneme_similarity(expected[i - 1], heard[j - 1])
            if abs(dp[i][j] - (dp[i - 1][j - 1] + sim)) < 1e-9:
                pairs_rev.append(AlignedPair(expected[i - 1], heard[j - 1], round(sim, 4)))
                i, j = i - 1, j - 1
                continue
        if i > 0 and abs(dp[i][j] - (dp[i - 1][j] + gap_penalty)) < 1e-9:
            pairs_rev.append(AlignedPair(expected[i - 1], None, 0.0))
            i -= 1
        else:
            pairs_rev.append(AlignedPair(None, heard[j - 1], 0.0))
            j -= 1

    pairs = list(reversed(pairs_rev))
    matched = sum(p.score for p in pairs if p.expected is not None and p.heard is not None)
    denominator = max(n, m)
    phoneme_score = max(0.0, min(1.0, matched / denominator))
    return pairs, round(phoneme_score, 4)


def sequence_edit_distance(a: list[str], b: list[str]) -> int:
    """Distancia de edicao simples (usada nos testes e em diagnostico)."""
    prev = list(range(len(b) + 1))
    for i, item_a in enumerate(a, start=1):
        cur = [i]
        for j, item_b in enumerate(b, start=1):
            cur.append(min(
                prev[j] + 1,                       # remocao
                cur[j - 1] + 1,                    # insercao
                prev[j - 1] + (item_a != item_b),  # substituicao
            ))
        prev = cur
    return prev[-1]
