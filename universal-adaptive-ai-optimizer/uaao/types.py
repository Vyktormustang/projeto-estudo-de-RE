"""Tipos de dominio do UA AO (dataclasses imutaveis sempre que possivel).

Fluxo de dados:

    PromptArtifact --(executor)--> CaseResult --(grader)--> score
    TaskSuite (train/val/holdout) + PromptArtifact --(evaluate)--> EvalResult
    EvalResult --(compare/diagnose)--> Diagnostico --> Proposer --> candidatos
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

# Conjuntos de divisao de dados. 'holdout' nunca participa da selecao: e
# reservado para confirmacao final e deteccao de overfitting.
SPLITS = ("train", "val", "holdout")


def utcnow() -> str:
    """Timestamp ISO-8601 em UTC, granularidade de segundo."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(obj: Any) -> str:
    """JSON canonico (chaves ordenadas, sem espacos) para hashing estavel."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Artefato otimizado (o "prompt")
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PromptArtifact:
    """Um texto de instrucao/direcionamento versionado.

    ``text`` e a fonte da verdade. ``directives`` e derivado do texto pelo
    parser (nao o contrario), garantindo que o hash do texto identifique
    univocamente o comportamento.
    """

    text: str
    origin: str = "seed"          # seed | mutation | manual | rollback
    parent_sha: str | None = None  # proveniencia (de qual versao derivou)
    notes: str = ""

    @property
    def sha(self) -> str:
        return sha256_text(self.text)

    @property
    def sha_short(self) -> str:
        return self.sha[:12]

    def directives(self) -> dict[str, str]:
        """Extrai ``CHAVE = valor`` de linhas de diretiva (parser tolerante)."""
        from .promptspec import parse_directives

        return parse_directives(self.text)

    def with_text(self, new_text: str, origin: str, notes: str = "") -> "PromptArtifact":
        return PromptArtifact(
            text=new_text, origin=origin, parent_sha=self.sha, notes=notes
        )


# ---------------------------------------------------------------------------
# Tarefas e suites
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TaskCase:
    """Um caso de teste com resposta verificavel.

    ``critical=True`` marca casos que NAO podem regredir sob nenhuma hipotese
    (ex.: seguranca, honestidade). Esses casos barram a aceitacao de candidatos.
    """

    case_id: str
    input: str
    expected: Any
    grader: str
    params: Mapping[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    critical: bool = False
    weight: float = 1.0
    note: str = ""

    def digest(self) -> str:
        return hashlib.sha256(
            canonical_json(
                {
                    "case_id": self.case_id,
                    "input": self.input,
                    "expected": self.expected,
                    "grader": self.grader,
                    "params": self.params,
                    "critical": self.critical,
                    "weight": self.weight,
                }
            ).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class TaskSuite:
    """Colecao versionada e *pinada por hash* de casos de teste."""

    suite_id: str
    version: str
    cases: tuple[TaskCase, ...]
    description: str = ""
    # peso relativo de cada metrica no score agregado (opcional)
    metric_weights: Mapping[str, float] = field(default_factory=dict)

    def by_split(self, split: str) -> tuple[TaskCase, ...]:
        # O split fica nas tags com o prefixo "split:<nome>" para manter o
        # JSON da suite legivel e um unico formato de caso.
        out = []
        for c in self.cases:
            tags = set(c.tags)
            if f"split:{split}" in tags:
                out.append(c)
        return tuple(out)

    @property
    def sha(self) -> str:
        return hashlib.sha256(
            canonical_json(
                {
                    "suite_id": self.suite_id,
                    "version": self.version,
                    "cases": [c.digest() for c in self.cases],
                }
            ).encode("utf-8")
        ).hexdigest()

    @property
    def sha_short(self) -> str:
        return self.sha[:12]


# ---------------------------------------------------------------------------
# Resultados de avaliacao
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CaseResult:
    """Resultado de um caso: saida bruta + veredito objetivo."""

    case_id: str
    output: str
    score: float
    passed: bool
    grader: str
    details: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None
    critical: bool = False
    weight: float = 1.0
    tags: tuple[str, ...] = ()

    @property
    def is_error(self) -> bool:
        return self.error is not None


@dataclass(frozen=True)
class EvalResult:
    """Agregado de uma avaliacao de UM artefato sobre UMA divisao de dados."""

    artifact_sha: str
    suite_sha: str
    split: str
    cases: tuple[CaseResult, ...]
    executor: str
    seed: int
    started_at: str
    duration_ms: int
    metric_calls: int = 0

    # -- agregados ---------------------------------------------------------
    @property
    def mean_score(self) -> float:
        if not self.cases:
            return 0.0
        total_w = sum(c.weight for c in self.cases) or 1.0
        return sum(c.score * c.weight for c in self.cases) / total_w

    @property
    def pass_rate(self) -> float:
        if not self.cases:
            return 0.0
        return sum(1 for c in self.cases if c.passed) / len(self.cases)

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.cases if c.is_error)

    def critical_failures(self) -> tuple[str, ...]:
        return tuple(c.case_id for c in self.cases if c.critical and not c.passed)

    def by_metric(self) -> dict[str, float]:
        """Score medio por nome de grader (metrica)."""
        buckets: dict[str, list[float]] = {}
        for c in self.cases:
            buckets.setdefault(c.grader, []).append(c.score)
        return {k: sum(v) / len(v) for k, v in sorted(buckets.items())}

    def scores_by_case(self) -> dict[str, float]:
        return {c.case_id: c.score for c in self.cases}

    def failures(self) -> tuple[CaseResult, ...]:
        return tuple(c for c in self.cases if not c.passed)

    def deterministic_signature(self) -> str:
        """Assinatura estavel do resultado: permite detectar nao-determinismo.

        Se duas execucoes do mesmo (artefato, suite, seed) produzem assinaturas
        diferentes, o executor NAO e deterministico -- o que invalida a
        comparacao. Testado em tests/test_determinism.py.
        """
        payload = [
            {
                "case_id": c.case_id,
                "output": c.output,
                "score": c.score,
                "passed": c.passed,
                "error": c.error,
            }
            for c in self.cases
        ]
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    @property
    def signature_short(self) -> str:
        return self.deterministic_signature()[:12]


# ---------------------------------------------------------------------------
# Decisoes de selecao
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Decision:
    """Veredito auditavel sobre um candidato."""

    accepted: bool
    reason: str
    checks: Mapping[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "reason": self.reason, "checks": dict(self.checks)}


__all__ = [
    "SPLITS",
    "utcnow",
    "canonical_json",
    "sha256_text",
    "PromptArtifact",
    "TaskCase",
    "TaskSuite",
    "CaseResult",
    "EvalResult",
    "Decision",
]
