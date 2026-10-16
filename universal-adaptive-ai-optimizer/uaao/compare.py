"""Modulo 4 - Comparacao entre versoes.

Comparacao **pareada por caso** (mesmo conjunto, mesma ordem, mesmo executor):
isso remove a variancia entre conjuntos e isola o efeito do prompt.

Testes usados:
  * teste de sinais exato (binomial) sobre a direcao das mudancas de score;
  * IC bootstrap percentil da melhoria media, com semente FIXA (reproduzivel).

Nenhum desses testes "prova" melhoria geral: eles quantificam a evidencia
disponivel no conjunto de validacao. A conclusao final vem do holdout.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from .types import EvalResult


@dataclass(frozen=True)
class CaseDelta:
    case_id: str
    baseline_score: float
    candidate_score: float
    baseline_passed: bool
    candidate_passed: bool
    grader: str
    critical: bool
    weight: float

    @property
    def delta(self) -> float:
        return round(self.candidate_score - self.baseline_score, 6)

    @property
    def direction(self) -> str:
        d = self.delta
        if d > 1e-9:
            return "improved"
        if d < -1e-9:
            return "regressed"
        if self.candidate_passed and not self.baseline_passed:
            return "improved"
        if self.baseline_passed and not self.candidate_passed:
            return "regressed"
        return "unchanged"


@dataclass(frozen=True)
class Comparison:
    baseline_sha: str
    candidate_sha: str
    split: str
    deltas: tuple[CaseDelta, ...]
    sign_test_p: float
    bootstrap_ci: tuple[float, float]
    bootstrap_mean: float
    notes: tuple[str, ...] = ()

    # -- selecoes ----------------------------------------------------------
    @property
    def improved(self) -> tuple[CaseDelta, ...]:
        return tuple(d for d in self.deltas if d.direction == "improved")

    @property
    def regressed(self) -> tuple[CaseDelta, ...]:
        return tuple(d for d in self.deltas if d.direction == "regressed")

    @property
    def critical_regressions(self) -> tuple[CaseDelta, ...]:
        return tuple(d for d in self.regressed if d.critical)

    @property
    def mean_delta(self) -> float:
        if not self.deltas:
            return 0.0
        total_w = sum(d.weight for d in self.deltas) or 1.0
        return round(sum(d.delta * d.weight for d in self.deltas) / total_w, 6)

    @property
    def pass_rate_delta(self) -> float:
        if not self.deltas:
            return 0.0
        b = sum(1 for d in self.deltas if d.baseline_passed) / len(self.deltas)
        c = sum(1 for d in self.deltas if d.candidate_passed) / len(self.deltas)
        return round(c - b, 6)

    def metric_deltas(self) -> dict[str, float]:
        """Delta medio por metrica (grader), ponderado."""
        buckets: dict[str, list[CaseDelta]] = {}
        for d in self.deltas:
            buckets.setdefault(d.grader, []).append(d)
        out = {}
        for name, items in sorted(buckets.items()):
            out[name] = round(sum(i.delta for i in items) / len(items), 6)
        return out

    def to_json(self) -> dict[str, Any]:
        return {
            "baseline_sha": self.baseline_sha[:12],
            "candidate_sha": self.candidate_sha[:12],
            "split": self.split,
            "cases": len(self.deltas),
            "improved": len(self.improved),
            "regressed": len(self.regressed),
            "critical_regressions": [d.case_id for d in self.critical_regressions],
            "mean_delta": self.mean_delta,
            "pass_rate_delta": self.pass_rate_delta,
            "sign_test_p": round(self.sign_test_p, 6),
            "bootstrap_ci95": [round(x, 6) for x in self.bootstrap_ci],
            "metric_deltas": self.metric_deltas(),
            "notes": list(self.notes),
        }


# --------------------------------------------------------------------------
# Estatistica (deterministica)
# --------------------------------------------------------------------------
def sign_test_p_value(k: int, n: int) -> float:
    """Teste de sinais exato, bicaudal.

    k = numero de melhorias, n = numero de pares NAO empatados.
    p = 2 * P(X <= min(k, n-k)), X ~ Binomial(n, 0.5).
    """
    if n <= 0:
        return 1.0
    k = max(0, min(k, n))
    tail = min(k, n - k)
    prob = sum(math.comb(n, i) for i in range(0, tail + 1)) / (2 ** n)
    return float(min(1.0, 2.0 * prob))


def bootstrap_ci(
    values: list[float], seed: int = 1729, resamples: int = 1000, alpha: float = 0.05
) -> tuple[float, float, float]:
    """IC percentil bootstrap da media. Semente fixa -> resultado reproduzivel."""
    if not values:
        return 0.0, 0.0, 0.0
    mean = sum(values) / len(values)
    if len(values) == 1:
        return mean, mean, mean
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(resamples):
        s = 0.0
        for _ in range(n):
            s += values[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    lo = means[max(0, int((alpha / 2) * resamples) - 1)]
    hi = means[min(resamples - 1, int((1 - alpha / 2) * resamples))]
    return round(lo, 6), round(hi, 6), round(mean, 6)


# --------------------------------------------------------------------------
# Comparacao
# --------------------------------------------------------------------------
def compare(
    baseline: EvalResult,
    candidate: EvalResult,
    seed: int = 1729,
    bootstrap_resamples: int = 1000,
) -> Comparison:
    """Comparacao pareada por case_id."""
    if baseline.suite_sha != candidate.suite_sha:
        raise ValueError(
            "Comparacao invalida: as execucoes usam suites diferentes "
            f"({baseline.suite_sha[:12]} vs {candidate.suite_sha[:12]}). "
            "Sem suite identica nao existe comparacao pareada honesta."
        )

    base_map = {c.case_id: c for c in baseline.cases}
    cand_map = {c.case_id: c for c in candidate.cases}
    common = sorted(set(base_map) & set(cand_map))
    notes: list[str] = []
    only_base = set(base_map) - set(cand_map)
    only_cand = set(cand_map) - set(base_map)
    if only_base or only_cand:
        notes.append(
            f"casos nao pareados ignorados: {len(only_base)} so no baseline, "
            f"{len(only_cand)} so no candidato"
        )

    deltas: list[CaseDelta] = []
    for cid in common:
        b, c = base_map[cid], cand_map[cid]
        deltas.append(
            CaseDelta(
                case_id=cid,
                baseline_score=b.score,
                candidate_score=c.score,
                baseline_passed=b.passed,
                candidate_passed=c.passed,
                grader=c.grader,
                critical=c.critical or b.critical,
                weight=c.weight,
            )
        )

    improved = sum(1 for d in deltas if d.direction == "improved")
    regressed = sum(1 for d in deltas if d.direction == "regressed")
    decided = improved + regressed
    p_value = sign_test_p_value(improved, decided)

    weighted = [d.delta for d in deltas for _ in range(1)]  # um par por caso
    lo, hi, mean = bootstrap_ci(weighted, seed=seed, resamples=bootstrap_resamples)

    if decided == 0 and deltas:
        notes.append("nenhum par decidiu: ganho/perda so em casos empatados ou identicos")

    return Comparison(
        baseline_sha=baseline.artifact_sha,
        candidate_sha=candidate.artifact_sha,
        split=baseline.split,
        deltas=tuple(deltas),
        sign_test_p=p_value,
        bootstrap_ci=(lo, hi),
        bootstrap_mean=mean,
        notes=tuple(notes),
    )


def is_improvement_significant(comp: Comparison, alpha: float = 0.05) -> bool:
    """Significancia E direcao positiva (evita aceitar p baixo com sinal negativo)."""
    return comp.sign_test_p < alpha and comp.mean_delta > 0


def regression_evidence(comp: Comparison, limit: int = 10) -> list[dict[str, Any]]:
    """Lista de regressoes com evidencia, para o relatorio e para o motivo da recusa."""
    out = []
    for d in comp.regressed[:limit]:
        out.append(
            {
                "case_id": d.case_id,
                "grader": d.grader,
                "critical": d.critical,
                "baseline": d.baseline_score,
                "candidate": d.candidate_score,
                "delta": d.delta,
            }
        )
    return out


__all__ = [
    "CaseDelta",
    "Comparison",
    "compare",
    "sign_test_p_value",
    "bootstrap_ci",
    "is_improvement_significant",
    "regression_evidence",
]
