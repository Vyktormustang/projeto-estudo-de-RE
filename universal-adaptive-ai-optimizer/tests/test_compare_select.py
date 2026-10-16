"""Testes de comparacao pareada, estatistica e selecao com protecao contra regressao.

Cobre o requisito: "Regressoes entre versoes".
"""

from __future__ import annotations

import pytest

from uaao.compare import bootstrap_ci, compare, is_improvement_significant, sign_test_p_value
from uaao.config import SelectionCriteria
from uaao.select import accept_candidate, explain_criteria
from uaao.types import CaseResult, EvalResult, utcnow

SUITE_SHA = "s" * 64


def mk_eval(artifact: str, scores: dict[str, float], critical: set[str] | None = None,
            grader: str = "g", split: str = "val", suite_sha: str = SUITE_SHA) -> EvalResult:
    critical = critical or set()
    cases = tuple(
        CaseResult(case_id=cid, output=f"out {cid}", score=sc, passed=sc >= 1.0, grader=grader,
                   critical=cid in critical)
        for cid, sc in scores.items()
    )
    return EvalResult(
        artifact_sha=artifact, suite_sha=suite_sha, split=split, cases=cases,
        executor="policy_reference_v1", seed=1, started_at=utcnow(), duration_ms=1,
        metric_calls=len(cases),
    )


# --------------------------------------------------------------------------
# Estatistica
# --------------------------------------------------------------------------
@pytest.mark.parametrize("k,n,expected", [
    (6, 6, 2 * (2 ** -6)),
    (5, 5, 2 * (2 ** -5)),
    (1, 2, 1.0),
    (2, 6, 2 * (1 + 6 + 15) / 64),
    (0, 0, 1.0),
    (4, 20, 2 * sum(__import__("math").comb(20, i) for i in range(0, 5)) / 2 ** 20),
])
def test_sign_test_exact_values(k, n, expected):
    assert sign_test_p_value(k, n) == pytest.approx(min(1.0, expected))


def test_sign_test_impossible_below_minimum_pairs():
    """Com n<6 nenhum resultado atinge p<0.05: base da guarda de poder estatistico."""
    assert sign_test_p_value(3, 3) == pytest.approx(0.25)
    assert sign_test_p_value(4, 4) == pytest.approx(0.125)
    assert sign_test_p_value(5, 5) == pytest.approx(0.0625)
    assert sign_test_p_value(5, 5) > 0.05


def test_sign_test_is_symmetric():
    assert sign_test_p_value(2, 10) == pytest.approx(sign_test_p_value(8, 10))


def test_bootstrap_ci_is_reproducible_with_fixed_seed():
    """A propriedade exigida e REPRODUTIBILIDADE: mesma semente -> mesmo IC.

    Nao comparamos sementes diferentes por desigualdade: com poucos valores
    distintos os percentis caem nos mesmos estatutos de ordem e o IC pode
    coincidir legitimamente.
    """
    values = [0.0, 0.5, 1.0, 0.25, 0.75]
    a = bootstrap_ci(values, seed=1729)
    b = bootstrap_ci(values, seed=1729)
    assert a == b
    assert a[0] <= a[2] <= a[1]
    assert a[2] == pytest.approx(sum(values) / len(values), abs=1e-9)


def test_bootstrap_ci_degenerate_inputs():
    assert bootstrap_ci([]) == (0.0, 0.0, 0.0)
    assert bootstrap_ci([0.5]) == (0.5, 0.5, 0.5)


# --------------------------------------------------------------------------
# Comparacao pareada
# --------------------------------------------------------------------------
def test_compare_requires_same_suite():
    with pytest.raises(ValueError) as exc:
        compare(mk_eval("a", {"c": 1.0}), mk_eval("b", {"c": 1.0}, suite_sha="t" * 64))
    assert "suites diferentes" in str(exc.value)


def test_compare_classifies_directions():
    base = mk_eval("a", {"c1": 0.0, "c2": 1.0, "c3": 0.5, "c4": 1.0})
    cand = mk_eval("b", {"c1": 1.0, "c2": 1.0, "c3": 0.5, "c4": 0.0})
    comp = compare(base, cand)
    assert [d.case_id for d in comp.improved] == ["c1"]
    assert [d.case_id for d in comp.regressed] == ["c4"]
    assert comp.mean_delta == pytest.approx(0.0)
    assert comp.pass_rate_delta == pytest.approx(0.0)


def test_compare_detects_critical_regression():
    base = mk_eval("a", {"seg": 1.0, "x": 0.0}, critical={"seg"})
    cand = mk_eval("b", {"seg": 0.0, "x": 1.0}, critical={"seg"})
    comp = compare(base, cand)
    assert [d.case_id for d in comp.critical_regressions] == ["seg"]


def test_compare_uses_passed_flag_when_scores_tie():
    base = mk_eval("a", {"c": 0.0})
    cand = mk_eval("b", {"c": 0.0})
    # mesmo score, veredito diferente -> conta como mudanca de direcao
    cand = EvalResult(artifact_sha="b", suite_sha=SUITE_SHA, split="val",
                      cases=(CaseResult(case_id="c", output="o", score=0.0, passed=True, grader="g"),),
                      executor="e", seed=1, started_at=utcnow(), duration_ms=1, metric_calls=1)
    comp = compare(base, cand)
    assert comp.improved and not comp.regressed


def test_compare_ignores_unpaired_cases_with_a_note():
    base = mk_eval("a", {"c1": 0.0, "so_no_base": 0.0})
    cand = mk_eval("b", {"c1": 1.0, "so_no_cand": 1.0})
    comp = compare(base, cand)
    assert len(comp.deltas) == 1
    assert any("nao pareados" in n for n in comp.notes)


def test_compare_metric_deltas():
    base = mk_eval("a", {"a1": 0.0, "a2": 0.0}, grader="json_fields")
    cand = mk_eval("b", {"a1": 1.0, "a2": 1.0}, grader="json_fields")
    assert compare(base, cand).metric_deltas() == {"json_fields": 1.0}


def test_compare_serializes():
    comp = compare(mk_eval("a", {"c": 0.0}), mk_eval("b", {"c": 1.0}))
    payload = comp.to_json()
    assert payload["improved"] == 1 and "sign_test_p" in payload


def test_is_improvement_significant_requires_positive_direction():
    base = mk_eval("a", {f"c{i}": 1.0 for i in range(10)})
    cand = mk_eval("b", {f"c{i}": 0.0 for i in range(10)})
    comp = compare(base, cand)
    assert comp.sign_test_p < 0.05
    assert not is_improvement_significant(comp)  # p baixo, mas piorou


# --------------------------------------------------------------------------
# Selecao
# --------------------------------------------------------------------------
def _run_selection(base_scores, cand_scores, critical=None, criteria=None):
    base = mk_eval("base", base_scores, critical=critical)
    cand = mk_eval("cand", cand_scores, critical=critical)
    comp = compare(base, cand)
    return accept_candidate(base, cand, comp, criteria or SelectionCriteria())


def test_clear_improvement_is_accepted():
    n = 10
    dec = _run_selection({f"c{i}": 0.0 for i in range(n)}, {f"c{i}": 1.0 for i in range(n)})
    assert dec.accepted and "ACEITO" in dec.reason


def test_improvement_below_margin_is_rejected():
    dec = _run_selection({"c1": 0.0, "c2": 1.0}, {"c1": 0.01, "c2": 1.0},
                         criteria=SelectionCriteria(require_significance=False))
    assert not dec.accepted and "abaixo do minimo" in dec.reason


def test_critical_regression_blocks_even_with_big_gain():
    """Nenhum ganho medio compra uma falha critica."""
    base_scores = {"crit": 1.0, **{f"x{i}": 0.0 for i in range(10)}}
    cand_scores = {"crit": 0.0, **{f"x{i}": 1.0 for i in range(10)}}
    dec = _run_selection(base_scores, cand_scores, critical={"crit"})
    assert not dec.accepted
    assert "BLOQUEADO" in dec.reason and "crit" in dec.reason
    assert dec.checks["policy"] == "critical_block"


def test_critical_check_can_be_disabled_explicitly():
    base_scores = {"crit": 1.0, **{f"x{i}": 0.0 for i in range(10)}}
    cand_scores = {"crit": 0.0, **{f"x{i}": 1.0 for i in range(10)}}
    crit = SelectionCriteria(block_on_critical_regression=False, require_significance=False,
                             per_case_regression_tolerance=1.0)
    dec = _run_selection(base_scores, cand_scores, critical={"crit"}, criteria=crit)
    assert dec.accepted


def test_per_case_regression_rejected():
    crit = SelectionCriteria(require_significance=False)
    dec = _run_selection({f"c{i}": 0.0 for i in range(10)} | {"piora": 1.0},
                         {f"c{i}": 1.0 for i in range(10)} | {"piora": 0.5}, criteria=crit)
    assert not dec.accepted and "regrediram" in dec.reason


def test_per_case_regression_tolerance_allows_small_drop():
    crit = SelectionCriteria(require_significance=False, per_case_regression_tolerance=0.5)
    dec = _run_selection({f"c{i}": 0.0 for i in range(10)} | {"piora": 1.0},
                         {f"c{i}": 1.0 for i in range(10)} | {"piora": 0.6}, criteria=crit)
    assert dec.accepted


def test_metric_regression_rejected():
    base = mk_eval("base", {"a": 0.0}, grader="metrica_a")
    cand = mk_eval("cand", {"a": 0.0}, grader="metrica_a")
    b2 = EvalResult(artifact_sha="base", suite_sha=SUITE_SHA, split="val", cases=(
        CaseResult(case_id="a", output="o", score=1.0, passed=True, grader="metrica_a"),
        CaseResult(case_id="b", output="o", score=0.0, passed=False, grader="metrica_b"),
    ), executor="e", seed=1, started_at=utcnow(), duration_ms=1, metric_calls=2)
    c2 = EvalResult(artifact_sha="cand", suite_sha=SUITE_SHA, split="val", cases=(
        CaseResult(case_id="a", output="o", score=0.6, passed=False, grader="metrica_a"),
        CaseResult(case_id="b", output="o", score=1.0, passed=True, grader="metrica_b"),
    ), executor="e", seed=1, started_at=utcnow(), duration_ms=1, metric_calls=2)
    dec = accept_candidate(b2, c2, compare(b2, c2), SelectionCriteria(require_significance=False))
    assert not dec.accepted and "metric" in dec.reason.lower()


def test_significance_gate_is_skipped_when_underpowered():
    """Com poucos pares decididos, o teste nao bloqueia -- mas REGISTRA que nao avaliou."""
    crit = SelectionCriteria(min_decided_pairs=8)
    dec = _run_selection({"a": 0.0, "b": 0.0}, {"a": 1.0, "b": 1.0}, criteria=crit)
    sig = dec.checks["significance"]
    assert sig["status"] == "nao_avaliado_poder_insuficiente"
    assert sig["decided_pairs"] == 2 and sig["ok"] is True
    assert "poder" in sig["note"]
    assert dec.accepted


def test_significance_gate_blocks_when_adequately_powered():
    """Com pares suficientes e evidencia FRACA, o candidato e rejeitado.

    Cenario construido de proposito: 7 casos melhoram muito e 5 perdem pouco,
    de modo que a media sobe (+0.5625) mas a DIRECAO e mista (p ~ 0.77). Sem
    esta guarda, o candidato passaria so pela media.
    """
    base = {**{f"ganha{i}": 0.0 for i in range(7)}, **{f"perde{i}": 1.0 for i in range(5)}}
    cand = {**{f"ganha{i}": 1.0 for i in range(7)}, **{f"perde{i}": 0.95 for i in range(5)}}
    crit = SelectionCriteria(min_decided_pairs=8, per_case_regression_tolerance=0.1)
    dec = _run_selection(base, cand, criteria=crit)
    sig = dec.checks["significance"]
    assert sig["status"] == "avaliado"
    assert sig["decided_pairs"] == 12 and sig["ok"] is False
    assert dec.checks["improvement"]["ok"] is True, "a media SOBE neste cenario"
    assert not dec.accepted
    assert "sem evidencia estatistica" in dec.reason


def test_no_decided_pairs_is_rejected():
    dec = _run_selection({"a": 1.0, "b": 1.0}, {"a": 1.0, "b": 1.0})
    assert not dec.accepted and "nenhum par decidiu" in dec.reason


def test_min_improved_fraction_enforced():
    n = 20
    base = {f"c{i}": 0.0 for i in range(n)}
    cand = {f"c{i}": (0.5 if i == 0 else 0.0) for i in range(n)}
    crit = SelectionCriteria(require_significance=False, min_improved_fraction=0.5)
    dec = _run_selection(base, cand, criteria=crit)
    assert not dec.accepted and "fracao de casos melhorados" in dec.reason


def test_decision_carries_full_check_evidence():
    dec = _run_selection({f"c{i}": 0.0 for i in range(10)}, {f"c{i}": 1.0 for i in range(10)})
    for key in ("critical", "improvement", "metric_regression", "per_case_regression",
                "significance", "improved_fraction", "regression_evidence"):
        assert key in dec.checks


def test_explain_criteria_is_human_readable():
    lines = explain_criteria(SelectionCriteria())
    assert len(lines) >= 6
    assert any("holdout" in line for line in lines)
