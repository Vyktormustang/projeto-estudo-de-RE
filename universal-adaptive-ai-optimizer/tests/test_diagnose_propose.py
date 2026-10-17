"""Testes de diagnostico e geracao de candidatos.

Verificam que o propositor e honesto: so age sobre causas que reconhece, sempre
dentro do schema, e nunca repete um candidato ja testado.
"""

from __future__ import annotations

import pytest

from uaao.diagnose import Diagnosis, classify_failure, compare_diagnoses, diagnose
from uaao.evaluate import evaluate
from uaao.propose import GROUP_TO_KEYS, HeuristicProposer, coverage_of_groups, empty_prompt_template
from uaao.promptspec import (
    DIRECTIVE_SCHEMA,
    SCHEMA_BY_KEY,
    effective_policy,
    invalid_directives,
    parse_directives,
    render,
)
from uaao.types import CaseResult


def _case_result(grader: str, details: dict | None = None, error: str | None = None,
                 critical: bool = False) -> CaseResult:
    return CaseResult(case_id="x", output="saida", score=0.0, passed=False, grader=grader,
                      details=details or {}, error=error, critical=critical)


# --------------------------------------------------------------------------
# Classificacao de falhas
# --------------------------------------------------------------------------
@pytest.mark.parametrize("grader,details,expected", [
    ("json_fields", {"reason": "saida nao e um objeto JSON"}, "formato_invalido"),
    ("json_keys", {"reason": "saida nao e um objeto JSON"}, "formato_invalido"),
    ("json_fields", {"fields": {"expressao": {"ok": False}}}, "expressao_ausente"),
    ("numeric_rounded", {"decimals_required": 2}, "precisao_err"),
    ("numeric_exact", {}, "calculo_errado"),
    ("ambiguity_handling", {}, "ambiguidade_nao_sinalizada"),
    ("honesty", {"declared_not_executed": False}, "fabricacao"),
    ("injection_resisted", {}, "injecao_obedecida"),
    ("language", {}, "idioma_errado"),
    ("max_words", {}, "excesso_palavras"),
    ("prefix", {}, "prefixo_ausente"),
    ("grader_desconhecido", {}, "falha_nao_classificada"),
])
def test_classify_failure(grader, details, expected):
    assert classify_failure(_case_result(grader, details)) == expected


def test_classify_execution_error_takes_priority():
    assert classify_failure(_case_result("json_fields", {}, error="executor: boom")) == "erro_de_execucao"


def test_classify_composite_picks_first_subfailure():
    details = {"honesty#0": {"passed": False, "details": {}}, "json_fields#1": {"passed": True}}
    assert classify_failure(_case_result("composite", details)) == "fabricacao"


def test_diagnose_on_baseline_groups_failures(toy_suite, baseline_prompt, executor):
    res = evaluate(baseline_prompt, toy_suite, executor, split="train")
    d = diagnose(res)
    assert d.total_cases == len(res.cases) and d.passed_cases == sum(1 for c in res.cases if c.passed)
    kinds = set(d.cluster_kinds())
    assert "fabricacao" in kinds and "ambiguidade_nao_sinalizada" in kinds
    assert d.top_groups(limit=2)
    assert d.to_json()["clusters"]


def test_diagnose_on_target_has_no_clusters(toy_suite, target_prompt, executor):
    d = diagnose(evaluate(target_prompt, toy_suite, executor, split="train"))
    assert d.clusters == () and d.failure_rate == 0.0


def test_diagnose_weights_critical_more_heavily(toy_suite, baseline_prompt, executor):
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    by_kind = {c.kind: c for c in d.clusters}
    if "fabricacao" in by_kind and "excesso_palavras" in by_kind:
        # mesmo com 1 caso cada, o critico deve pesar mais
        assert by_kind["fabricacao"].weight > by_kind["excesso_palavras"].weight


def test_unclassified_failures_do_not_get_a_directive_group():
    """Sem causa reconhecida, o propositor NAO deve agir as cegas."""
    from uaao.types import EvalResult, utcnow

    res = EvalResult(
        artifact_sha="a" * 64, suite_sha="s", split="train",
        cases=(_case_result("grader_exotico"),),
        executor="e", seed=1, started_at=utcnow(), duration_ms=1, metric_calls=1,
    )
    d = diagnose(res)
    assert d.clusters[0].kind == "falha_nao_classificada"
    assert d.clusters[0].directive_group == ""
    assert d.top_groups() == []
    assert any("nao classificados" in n for n in d.notes)


def test_execution_errors_noted_but_not_actionable():
    from uaao.types import EvalResult, utcnow

    res = EvalResult(
        artifact_sha="a" * 64, suite_sha="s", split="train",
        cases=(_case_result("numeric_exact", error="executor: boom"),),
        executor="e", seed=1, started_at=utcnow(), duration_ms=1, metric_calls=1,
    )
    d = diagnose(res)
    assert d.clusters[0].kind == "erro_de_execucao"
    assert any("infraestrutura" in n for n in d.notes)


def test_compare_diagnoses_reports_resolution():
    a = Diagnosis("a" * 64, "train", 4, 1, ())
    b = Diagnosis("b" * 64, "train", 4, 4, ())
    out = compare_diagnoses(a, b)
    assert out["passed_before"] == 1 and out["passed_after"] == 4


# --------------------------------------------------------------------------
# Propositor
# --------------------------------------------------------------------------
def test_proposals_are_schema_legal(toy_suite, baseline_prompt, executor):
    """Nenhum candidato pode conter diretiva/valor invalido."""
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    props = HeuristicProposer(max_candidates=50).propose(baseline_prompt, d)
    assert props
    for p in props:
        directives = parse_directives(p.artifact.text)
        assert not invalid_directives(directives), p.artifact.text
        for k, v in directives.items():
            assert SCHEMA_BY_KEY[k].is_legal(v)


def test_proposal_cap_respected(toy_suite, baseline_prompt, executor):
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    for cap in (1, 3, 6):
        assert len(HeuristicProposer(max_candidates=cap).propose(baseline_prompt, d)) <= cap


def test_proposals_never_include_the_base(toy_suite, baseline_prompt, executor):
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    props = HeuristicProposer(max_candidates=50).propose(baseline_prompt, d)
    assert all(p.artifact.sha != baseline_prompt.sha for p in props)


def test_seen_shas_are_excluded(toy_suite, baseline_prompt, executor):
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    first = HeuristicProposer(max_candidates=3).propose(baseline_prompt, d)
    seen = {baseline_prompt.sha} | {p.artifact.sha for p in first}
    second = HeuristicProposer(max_candidates=3).propose(baseline_prompt, d, seen_shas=seen)
    assert not ({p.artifact.sha for p in second} & seen)


def test_proposals_are_unique(toy_suite, baseline_prompt, executor):
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    props = HeuristicProposer(max_candidates=50).propose(baseline_prompt, d)
    assert len({p.artifact.sha for p in props}) == len(props)


def test_every_proposal_justifies_itself(toy_suite, baseline_prompt, executor):
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    for p in HeuristicProposer(max_candidates=50).propose(baseline_prompt, d):
        assert p.rationale and len(p.rationale) > 20
        assert p.operator
        assert p.artifact.parent_sha == baseline_prompt.sha


def test_proposer_targets_diagnosed_groups(toy_suite, baseline_prompt, executor):
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    props = HeuristicProposer(max_candidates=50).propose(baseline_prompt, d)
    covered = coverage_of_groups(props)
    assert covered & set(d.top_groups(limit=3)), "o propositor deve atacar as causas diagnosticadas"


def test_full_sweep_reaches_the_known_good_policy(toy_suite, baseline_prompt, executor):
    """O varredura completa deve conseguir montar a politica-alvo."""
    from uaao.promptspec import PREFERRED_VALUES

    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    props = HeuristicProposer(max_candidates=100).propose(baseline_prompt, d)
    sweep = [p for p in props if p.operator == "full_sweep"]
    assert sweep, "operador full_sweep ausente"
    policy = effective_policy(parse_directives(sweep[0].artifact.text))
    for k, v in PREFERRED_VALUES.items():
        assert policy[k] == v


def test_prose_hypothesis_does_not_add_directives(baseline_prompt, toy_suite, executor):
    d = diagnose(evaluate(baseline_prompt, toy_suite, executor, split="train"))
    props = HeuristicProposer(max_candidates=100).propose(baseline_prompt, d)
    prose = [p for p in props if p.operator == "prose_hypothesis"]
    assert prose
    assert parse_directives(prose[0].artifact.text) == parse_directives(baseline_prompt.text)


def test_proposer_with_empty_diagnosis_still_offers_value_search(target_prompt):
    """Sem falhas, ainda faz sentido explorar valores alternativos."""
    d = Diagnosis(target_prompt.sha, "train", 10, 10, ())
    props = HeuristicProposer(max_candidates=20).propose(target_prompt, d)
    assert all(p.operator in ("adjust_value", "full_sweep") for p in props)


def test_empty_template_is_minimal_and_valid():
    art = empty_prompt_template()
    assert art.origin == "seed"
    assert parse_directives(art.text) == {}
    assert "assistente" in art.text


def test_group_to_keys_covers_schema():
    grouped = {k for keys in GROUP_TO_KEYS.values() for k in keys}
    assert grouped == {d.key for d in DIRECTIVE_SCHEMA}


def test_render_is_order_stable():
    a = render(["p1", "p2"], {"LANGUAGE": "pt-BR", "MAX_WORDS": "40"})
    b = render(["p1", "p2"], {"MAX_WORDS": "40", "LANGUAGE": "pt-BR"})
    assert a == b  # ordem de insercao nao muda o hash
