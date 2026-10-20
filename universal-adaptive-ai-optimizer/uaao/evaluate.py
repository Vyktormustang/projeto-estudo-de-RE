"""Modulo 2 - Avaliacao com metricas especificas por tarefa.

Contrato:
  * cada caso e executado pelo executor escolhido;
  * a saida e julgada pelo grader declarado NA SUITE (nao pelo candidato);
  * erros de execucao/avaliacao viram ``CaseResult`` com score 0 e ``error``
    preenchido -- nunca excecao silenciosa, nunca escore inventado;
  * toda chamada de metrica passa pelo ``BudgetLedger`` (limite de chamadas);
  * o resultado carrega uma assinatura deterministica, permitindo provar que
    duas execucoes identicas produziram saidas identicas.
"""

from __future__ import annotations

import time
from typing import Any

from .errors import BudgetExceeded, ExecutorError, GraderError
from .executors import Executor, run_case
from .graders import run_grader
from .safety import BudgetLedger
from .types import CaseResult, EvalResult, PromptArtifact, TaskCase, TaskSuite, utcnow


def evaluate_case(
    executor: Executor,
    artifact: PromptArtifact,
    case: TaskCase,
    max_output_chars: int = 4000,
) -> CaseResult:
    """Executa + julga UM caso. Nunca levanta: erros viram resultado."""
    output = ""
    error: str | None = None
    score, passed, details = 0.0, False, {}
    try:
        output = run_case(executor, artifact, case, max_output_chars=max_output_chars)
    except ExecutorError as exc:
        error = f"executor: {exc}"
    except Exception as exc:  # pragma: no cover - defensivo
        error = f"executor inesperado: {type(exc).__name__}: {exc}"
    else:
        try:
            score, passed, details = run_grader(case.grader, output, case.expected, case.params)
        except GraderError as exc:
            error = f"grader: {exc}"
        except Exception as exc:  # pragma: no cover - defensivo
            error = f"grader inesperado: {type(exc).__name__}: {exc}"

    if error is not None:
        score, passed = 0.0, False

    return CaseResult(
        case_id=case.case_id,
        output=output,
        score=round(float(score), 6),
        passed=bool(passed),
        grader=case.grader,
        details=details,
        error=error,
        critical=case.critical,
        weight=case.weight,
        tags=case.tags,
    )


def evaluate(
    artifact: PromptArtifact,
    suite: TaskSuite,
    executor: Executor,
    split: str = "val",
    seed: int = 0,
    ledger: BudgetLedger | None = None,
    max_output_chars: int = 4000,
    case_ids: list[str] | None = None,
) -> EvalResult:
    """Avalia um artefato sobre uma divisao da suite.

    ``ledger`` e obrigatorio para execucoes controladas: sem ele, nao ha limite.
    Preferimos exigir o ledger explicitamente a ter um limite implicito.
    """
    t0 = time.perf_counter()
    started = utcnow()
    cases = list(suite.by_split(split))
    if case_ids is not None:
        wanted = set(case_ids)
        cases = [c for c in cases if c.case_id in wanted]

    results: list[CaseResult] = []
    for case in cases:
        if ledger is not None:
            ledger.charge_call(f"eval:{split}:{case.case_id}")
            ledger.check_wall_clock()
        results.append(
            evaluate_case(executor, artifact, case, max_output_chars=max_output_chars)
        )

    duration_ms = int((time.perf_counter() - t0) * 1000)
    return EvalResult(
        artifact_sha=artifact.sha,
        suite_sha=suite.sha,
        split=split,
        cases=tuple(results),
        executor=executor.name,
        seed=seed,
        started_at=started,
        duration_ms=duration_ms,
        metric_calls=len(results),
    )


def evaluate_all_splits(
    artifact: PromptArtifact,
    suite: TaskSuite,
    executor: Executor,
    seed: int = 0,
    ledger: BudgetLedger | None = None,
    max_output_chars: int = 4000,
) -> dict[str, EvalResult]:
    """Avalia train/val/holdout. O holdout e medido, mas nao usado na selecao."""
    return {
        split: evaluate(
            artifact, suite, executor, split=split, seed=seed,
            ledger=ledger, max_output_chars=max_output_chars,
        )
        for split in ("train", "val", "holdout")
        if suite.by_split(split)
    }


def check_determinism(
    artifact: PromptArtifact,
    suite: TaskSuite,
    executor: Executor,
    split: str = "val",
    repeats: int = 2,
    max_output_chars: int = 4000,
) -> tuple[bool, list[str]]:
    """Executa N vezes e compara as assinaturas.

    Retorna (deterministico, assinaturas). Sem ledger: e uma verificacao
    metodologica, nao uma busca.
    """
    sigs: list[str] = []
    for _ in range(max(2, repeats)):
        res = evaluate(
            artifact, suite, executor, split=split, seed=0,
            ledger=None, max_output_chars=max_output_chars,
        )
        sigs.append(res.deterministic_signature())
    return len(set(sigs)) == 1, sigs


def metric_table(result: EvalResult) -> list[dict[str, Any]]:
    """Tabela por metrica (grader) para relatorios."""
    buckets: dict[str, list[CaseResult]] = {}
    for c in result.cases:
        buckets.setdefault(c.grader, []).append(c)
    rows = []
    for name, items in sorted(buckets.items()):
        rows.append(
            {
                "metric": name,
                "cases": len(items),
                "mean_score": round(sum(i.score for i in items) / len(items), 4),
                "pass_rate": round(sum(1 for i in items if i.passed) / len(items), 4),
                "errors": sum(1 for i in items if i.is_error),
            }
        )
    return rows


__all__ = [
    "evaluate",
    "evaluate_case",
    "evaluate_all_splits",
    "check_determinism",
    "metric_table",
    "BudgetExceeded",
]
