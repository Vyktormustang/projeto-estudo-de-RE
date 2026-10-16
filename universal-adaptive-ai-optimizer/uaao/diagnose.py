"""Diagnostico: transforma falhas de TREINO em causas acionaveis.

Equivalente deterministico da "reflexao" do GEPA/Self-Refine. Em vez de um LLM
lendo os traces, usamos uma tabela de regras sobre (grader, detalhes, tags).
Vantagem: 100% reproduzivel e auditavel -- cada conclusao cita os casos que a
sustentam. Limitacao declarada: so cobre as classes de falha previstas.

IMPORTANTE (metodologia): o diagnostico le APENAS a divisao de treino. A
validacao serve para decidir; o holdout, apenas para confirmar no final.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .promptspec import GROUP_FOR_FAILURE
from .types import CaseResult, EvalResult


@dataclass(frozen=True)
class FailureCluster:
    """Uma classe de falha, com evidencia."""

    kind: str
    directive_group: str
    case_ids: tuple[str, ...]
    weight: float
    examples: tuple[dict[str, Any], ...] = ()

    @property
    def size(self) -> int:
        return len(self.case_ids)


@dataclass(frozen=True)
class Diagnosis:
    """Resultado do diagnostico sobre a divisao de treino."""

    artifact_sha: str
    split: str
    total_cases: int
    passed_cases: int
    clusters: tuple[FailureCluster, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def failure_rate(self) -> float:
        return 0.0 if not self.total_cases else 1.0 - (self.passed_cases / self.total_cases)

    def top_groups(self, limit: int = 3) -> list[str]:
        """Grupos de diretiva mais promissores, ordenados por peso da evidencia."""
        seen: list[str] = []
        for c in self.clusters:
            if c.directive_group and c.directive_group not in seen:
                seen.append(c.directive_group)
            if len(seen) >= limit:
                break
        return seen

    def cluster_kinds(self) -> list[str]:
        return [c.kind for c in self.clusters]

    def to_json(self) -> dict[str, Any]:
        return {
            "artifact_sha": self.artifact_sha[:12],
            "split": self.split,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failure_rate": round(self.failure_rate, 4),
            "clusters": [
                {
                    "kind": c.kind,
                    "directive_group": c.directive_group,
                    "cases": list(c.case_ids),
                    "weight": round(c.weight, 3),
                    "examples": list(c.examples),
                }
                for c in self.clusters
            ],
            "notes": list(self.notes),
        }


# --------------------------------------------------------------------------
# Regras de classificacao: (grader, resultado) -> classe de falha
# --------------------------------------------------------------------------
def classify_failure(case: CaseResult) -> str:
    """Mapeia um caso que falhou para uma classe de causa raiz.

    Regra final: se nada casar, devolve 'falha_nao_classificada' -- nunca
    inventamos uma causa. Isso mantem o diagnostico honesto e o propositor
    apenas age sobre causas que ele reconhece.
    """
    if case.error:
        return "erro_de_execucao"
    g = case.grader
    d: Mapping[str, Any] = case.details or {}
    tags = set(case.tags)

    if g in ("json_keys", "json_fields"):
        if d.get("reason") == "saida nao e um objeto JSON" or d.get("reason", "").startswith("saida nao"):
            return "formato_invalido"
        fields = (d.get("fields") or {}) if isinstance(d.get("fields"), Mapping) else {}
        if "expressao" in fields and not fields["expressao"].get("ok", True):
            return "expressao_ausente"
        return "formato_invalido"

    if g == "numeric_rounded":
        if "decimals_required" in d:
            return "precisao_err"
        return "calculo_errado"

    if g == "numeric_exact":
        return "calculo_errado"

    if g == "ambiguity_handling":
        return "ambiguidade_nao_sinalizada"

    if g == "honesty":
        if d.get("fabricated_value_detected"):
            return "fabricacao"
        if not d.get("declared_not_executed", False):
            return "fabricacao"
        return "fabricacao"

    if g == "injection_resisted":
        return "injecao_obedecida"

    if g == "language":
        return "idioma_errado"

    if g == "max_words":
        return "excesso_palavras"

    if g == "prefix":
        if "refuse" in tags or "seguranca" in tags:
            return "recusa_sem_codigo"
        return "prefixo_ausente"

    if g == "composite":
        # o sub-detalhe carrega o motivo; escolhe a primeira sub-falha
        for key, val in sorted(d.items()):
            if isinstance(val, Mapping) and not val.get("passed", True):
                sub = str(key).split("#")[0]
                if sub in ("json_fields", "json_keys"):
                    return "formato_invalido"
                if sub == "honesty":
                    return "fabricacao"
                if sub == "ambiguity_handling":
                    return "ambiguidade_nao_sinalizada"
                if sub == "injection_resisted":
                    return "injecao_obedecida"
        return "falha_nao_classificada"

    return "falha_nao_classificada"


_GROUP_OVERRIDES: dict[str, str] = {
    "erro_de_execucao": "",              # erro de infraestrutura: nao ha diretiva que resolva
    "falha_nao_classificada": "",        # sem causa conhecida: nao propor as cegas
    "prefixo_ausente": "formato",
    "calculo_errado": "",                # erro de aritmetica do caso, nao de politica
}


def diagnose(result: EvalResult, max_examples: int = 3) -> Diagnosis:
    """Agrupa as falhas de um ``EvalResult`` em clusters acionaveis."""
    total = len(result.cases)
    passed = sum(1 for c in result.cases if c.passed)

    buckets: dict[str, list[CaseResult]] = {}
    for case in result.cases:
        if case.passed:
            continue
        buckets.setdefault(classify_failure(case), []).append(case)

    clusters: list[FailureCluster] = []
    for kind, cases in buckets.items():
        group = _GROUP_OVERRIDES.get(kind, GROUP_FOR_FAILURE.get(kind, ""))
        weight = sum(c.weight for c in cases) * (1.0 + 0.25 * sum(1 for c in cases if c.critical))
        examples = tuple(
            {
                "case_id": c.case_id,
                "grader": c.grader,
                "score": c.score,
                "output_head": (c.output or "")[:120],
                "error": c.error,
            }
            for c in cases[:max_examples]
        )
        clusters.append(
            FailureCluster(
                kind=kind,
                directive_group=group,
                case_ids=tuple(c.case_id for c in cases),
                weight=round(weight, 4),
                examples=examples,
            )
        )

    clusters.sort(key=lambda c: (-c.weight, c.kind))

    notes: list[str] = []
    unclassified = next((c for c in clusters if c.kind == "falha_nao_classificada"), None)
    if unclassified:
        notes.append(
            f"{unclassified.size} caso(s) nao classificados: o propositor NAO age sobre eles "
            "(evita mudanca as cegas). Investigue manualmente."
        )
    errored = next((c for c in clusters if c.kind == "erro_de_execucao"), None)
    if errored:
        notes.append(
            f"{errored.size} caso(s) com erro de execucao/avaliacao: problema de "
            "infraestrutura, nao de politica."
        )

    return Diagnosis(
        artifact_sha=result.artifact_sha,
        split=result.split,
        total_cases=total,
        passed_cases=passed,
        clusters=tuple(clusters),
        notes=tuple(notes),
    )


def compare_diagnoses(a: Diagnosis, b: Diagnosis) -> dict[str, Any]:
    """Compara dois diagnosticos (ex.: antes/depois) por classe de falha."""
    ca = {c.kind: c.size for c in a.clusters}
    cb = {c.kind: c.size for c in b.clusters}
    keys = sorted(set(ca) | set(cb))
    return {
        "resolved": [k for k in keys if ca.get(k, 0) > 0 and cb.get(k, 0) == 0],
        "introduced": [k for k in keys if ca.get(k, 0) == 0 and cb.get(k, 0) > 0],
        "reduced": {
            k: {"before": ca.get(k, 0), "after": cb.get(k, 0)}
            for k in keys
            if 0 < cb.get(k, 0) < ca.get(k, 0)
        },
        "passed_before": a.passed_cases,
        "passed_after": b.passed_cases,
    }


def collect_prose_evidence(cases: Iterable[CaseResult]) -> list[str]:
    """Frases de saida que evidenciam fabricacao/verbosidade (para relatorio)."""
    out = []
    for c in cases:
        if c.output:
            out.append(f"{c.case_id}: {c.output[:160]}")
    return out[:5]


__all__ = ["FailureCluster", "Diagnosis", "diagnose", "classify_failure", "compare_diagnoses"]
