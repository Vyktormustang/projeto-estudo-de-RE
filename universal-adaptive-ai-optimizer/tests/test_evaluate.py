"""Testes do motor de avaliacao: agregacao, erros, determinismo, orcamento."""

from __future__ import annotations

import pytest

from uaao.evaluate import check_determinism, evaluate, evaluate_all_splits, evaluate_case, metric_table
from uaao.errors import BudgetExceeded
from uaao.safety import BudgetLedger
from uaao.types import PromptArtifact, TaskCase


def _ledger(n=10_000):
    return BudgetLedger(max_metric_calls=n, max_retries=0, max_wall_seconds=300, max_cost_units=1000)


def test_evaluate_charges_budget(toy_suite, baseline_prompt, executor):
    led = _ledger()
    res = evaluate(baseline_prompt, toy_suite, executor, split="val", ledger=led)
    assert led.metric_calls == len(res.cases) == res.metric_calls
    assert res.split == "val" and res.executor == "policy_reference_v1"


def test_evaluate_budget_exceeded_is_raised(toy_suite, baseline_prompt, executor):
    led = _ledger(n=1)
    with pytest.raises(BudgetExceeded):
        evaluate(baseline_prompt, toy_suite, executor, split="val", ledger=led)


def test_evaluate_without_ledger_has_no_limit(toy_suite, baseline_prompt, executor):
    res = evaluate(toy_suite and baseline_prompt, toy_suite, executor, split="train", ledger=None)
    assert res.cases


def test_scores_are_within_unit_interval(toy_suite, target_prompt, executor):
    for split in ("train", "val", "holdout"):
        res = evaluate(target_prompt, toy_suite, executor, split=split)
        if not res.cases:
            continue
        assert 0.0 <= res.mean_score <= 1.0
        assert all(0.0 <= c.score <= 1.0 for c in res.cases)


def test_target_scores_one_by_split(toy_suite, target_prompt, executor):
    for split in ("train", "val", "holdout"):
        res = evaluate(target_prompt, toy_suite, executor, split=split)
        if res.cases:
            assert res.mean_score == pytest.approx(1.0), (split, [c.case_id for c in res.failures()])


def test_critical_failures_listed(toy_suite, baseline_prompt, executor):
    res = evaluate(baseline_prompt, toy_suite, executor, split="val")
    crit = res.critical_failures()
    assert crit, "o baseline deve falhar casos criticos (honestidade/ambiguidade/seguranca)"
    assert "c-hon-2" in crit


def test_metric_table_columns(toy_suite, baseline_prompt, executor):
    res = evaluate(baseline_prompt, toy_suite, executor, split="val")
    rows = metric_table(res)
    assert rows and all({"metric", "cases", "mean_score", "pass_rate", "errors"} <= set(r) for r in rows)


def test_evaluate_all_splits_covers_three_splits(toy_suite, baseline_prompt, executor):
    out = evaluate_all_splits(baseline_prompt, toy_suite, executor)
    assert set(out) == {"train", "val", "holdout"}


def test_determinism_is_confirmed_for_reference_executor(toy_suite, target_prompt, executor):
    ok, sigs = check_determinism(target_prompt, toy_suite, executor, split="val", repeats=3)
    assert ok and len(set(sigs)) == 1 and len(sigs) == 3


def test_signature_changes_when_output_changes(toy_suite, baseline_prompt, target_prompt, executor):
    a = evaluate(baseline_prompt, toy_suite, executor, split="val")
    b = evaluate(target_prompt, toy_suite, executor, split="val")
    assert a.deterministic_signature() != b.deterministic_signature()


# --------------------------------------------------------------------------
# Tratamento de erro: erro vira resultado, nunca excecao silenciosa
# --------------------------------------------------------------------------
def test_executor_error_becomes_zero_score_case(executor, baseline_prompt):
    case = TaskCase(case_id="sem-expr", input="kind=calc", expected=1, grader="numeric_exact")
    res = evaluate_case(executor, baseline_prompt, case)
    assert res.score == 0.0 and res.passed is False
    assert res.error and "executor" in res.error


def test_grader_error_becomes_zero_score_case(executor, baseline_prompt):
    # Em g_regex o PADRAO vem de 'expected' (nao de params); "[" e um regex invalido.
    case = TaskCase(case_id="x", input="kind=calc\nexpr=1+1", expected="[", grader="regex")
    res = evaluate_case(executor, baseline_prompt, case)
    assert res.score == 0.0 and res.error and "grader" in res.error


def test_errors_counted_in_aggregate(executor, baseline_prompt):
    from uaao.types import TaskSuite

    suite = TaskSuite(suite_id="s", version="1", cases=(
        TaskCase(case_id="ok", input="kind=calc\nexpr=1+1", expected=2, grader="numeric_exact",
                 tags=("split:val",)),
        TaskCase(case_id="ruim", input="kind=calc", expected=2, grader="numeric_exact",
                 tags=("split:val",)),
    ))
    res = evaluate(baseline_prompt, suite, executor, split="val")
    assert res.error_count == 1
    assert res.failures()[0].case_id == "ruim"


def test_evaluation_is_read_only_wrt_prompt(toy_suite, baseline_prompt, executor):
    """Avaliar NUNCA modifica o artefato: baseline permanece intacto."""
    before = baseline_prompt.text
    sha_before = baseline_prompt.sha
    evaluate(baseline_prompt, toy_suite, executor, split="val")
    assert baseline_prompt.text == before and baseline_prompt.sha == sha_before


def test_paired_evaluation_order_is_stable(toy_suite, baseline_prompt, executor):
    r1 = evaluate(baseline_prompt, toy_suite, executor, split="val")
    r2 = evaluate(baseline_prompt, toy_suite, executor, split="val")
    assert [c.case_id for c in r1.cases] == [c.case_id for c in r2.cases]
