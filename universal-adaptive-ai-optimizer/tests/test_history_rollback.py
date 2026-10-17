"""Testes de historico, versionamento e reversao.

Cobre o requisito: "Reversao de alteracoes" e "Permita consultar o historico e
reverter para uma versao anterior".
"""

from __future__ import annotations

import pytest

from uaao.history import History
from uaao.memory import Memory
from uaao.optimizer import Optimizer
from uaao.promptspec import set_directive
from uaao.safety import AuditLog
from uaao.types import PromptArtifact


@pytest.fixture
def hist(tmp_path, cfg):
    mem = Memory(cfg.db_path)
    audit = AuditLog(cfg.audit_path)
    return History(mem, audit=audit), mem, audit, cfg


def _seed_experiment(mem: Memory, texts: list[str]) -> tuple[str, list[PromptArtifact]]:
    eid = mem.start_experiment(name="h", suite_sha="s", suite_id="toy", suite_version="1",
                               executor="e", seed=1, config={}, safety_fp="f")
    arts = []
    parent = None
    for i, t in enumerate(texts):
        art = PromptArtifact(text=t, origin="seed" if i == 0 else "mutation", parent_sha=parent)
        mem.save_artifact(art, eid)
        arts.append(art)
        parent = art.sha
    mem.set_active(eid, arts[-1].sha, "versao final")
    return eid, arts


def test_versions_listed_in_order_with_active_flag(hist):
    h, mem, _, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n", "A = 3\n"])
    versions = h.versions(eid)
    assert [v.sha for v in versions] == [a.sha for a in arts]
    assert versions[-1].active is True
    assert sum(1 for v in versions if v.active) == 1


def test_lineage_walks_back_to_seed(hist):
    h, mem, _, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n", "A = 3\n"])
    chain = mem.lineage(arts[-1].sha)
    assert [c["full_sha"] for c in chain] == [a.sha for a in reversed(arts)]
    assert chain[-1]["origin"] == "seed"


def test_rollback_to_previous_moves_active_and_preserves_history(hist):
    h, mem, audit, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n", "A = 3\n"])
    result = h.rollback(eid, "previous", reason="teste")
    assert result.ok
    assert result.to_sha == arts[-2].sha
    assert mem.get_active(eid)[0] == arts[-2].sha
    # NADA foi apagado: as 3 versoes continuam existindo
    assert len(h.versions(eid)) == 3
    assert "ROLLBACK" in mem.get_active(eid)[1]


def test_rollback_by_short_sha(hist):
    h, mem, _, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n", "A = 3\n"])
    result = h.rollback(eid, arts[0].sha[:10], reason="voltar ao inicio")
    assert result.ok and mem.get_active(eid)[0] == arts[0].sha


def test_rollback_by_full_sha(hist):
    h, mem, _, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n"])
    assert h.rollback(eid, arts[0].sha, reason="x").ok
    assert mem.get_active(eid)[0] == arts[0].sha


def test_rollback_records_audit_entry(hist):
    h, mem, audit, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n"])
    h.rollback(eid, "previous", reason="motivo registrado")
    ok, msg = audit.verify()
    assert ok, msg
    entry = [e for e in audit.entries() if e["event"] == "rollback"][0]
    assert entry["data"]["reason"] == "motivo registrado"
    assert entry["data"]["to"] == arts[0].sha[:12]


def test_rollback_to_unknown_target_fails_cleanly(hist):
    h, mem, _, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n"])
    result = h.rollback(eid, "deadbeef")
    assert not result.ok and "nao encontrada" in result.message
    assert mem.get_active(eid)[0] == arts[-1].sha  # nada mudou


def test_rollback_to_active_is_noop(hist):
    h, mem, _, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n"])
    result = h.rollback(eid, arts[-1].sha)
    assert not result.ok and "ja e a ativa" in result.message


def test_rollback_previous_at_oldest_fails(hist):
    h, mem, _, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n"])
    result = h.rollback(eid, "previous")
    assert not result.ok and "nao existe versao anterior" in result.message


def test_diff_between_versions_shows_directive_changes(hist):
    h, mem, _, _ = hist
    base = "PROSE: nada\n"
    v2 = set_directive(base, "OUTPUT_FORMAT", "json_object")
    eid, arts = _seed_experiment(mem, [base, v2])
    d = h.diff(arts[0].sha, arts[1].sha)
    assert d["directive_changes"]["OUTPUT_FORMAT"] == {"before": None, "after": "json_object"}


def test_best_version_picks_highest_val_score(hist):
    from uaao.types import CaseResult, EvalResult, utcnow

    h, mem, _, _ = hist
    eid, arts = _seed_experiment(mem, ["A = 1\n", "A = 2\n"])
    for art, score in zip(arts, (0.2, 0.9)):
        mem.save_evaluation(eid, EvalResult(
            artifact_sha=art.sha, suite_sha="s", split="val",
            cases=(CaseResult(case_id="c", output="o", score=score, passed=score > 0.5, grader="g"),),
            executor="e", seed=1, started_at=utcnow(), duration_ms=1, metric_calls=1,
        ))
    assert h.best_version(eid, "val") == arts[1].sha


# --------------------------------------------------------------------------
# Integracao: rollback apos um ciclo real
# --------------------------------------------------------------------------
def test_rollback_after_real_optimization(cfg, toy_suite, baseline_prompt, executor, tmp_path):
    memory = Memory(cfg.db_path)
    audit = AuditLog(cfg.audit_path)
    opt = Optimizer(cfg, toy_suite, executor, memory, audit=audit)
    run = opt.run(baseline_prompt, name="com-rollback")

    h = History(memory, audit=audit)
    versions = h.versions(run.experiment_id)
    assert len(versions) >= 2, "o ciclo precisa ter gerado mais de uma versao"

    # volta para a semente
    result = h.rollback(run.experiment_id, run.seed_artifact.sha, reason="descartar otimizacao")
    assert result.ok
    active_sha, _ = memory.get_active(run.experiment_id)
    assert active_sha == run.seed_artifact.sha

    # e a semente ainda e legivel byte a byte
    restored = memory.get_artifact(active_sha)
    assert restored.text == baseline_prompt.text

    # o historico de decisoes permanece intacto
    assert len(memory.list_decisions(run.experiment_id)) >= 1
    ok, msg = audit.verify()
    assert ok, msg


def test_rollback_does_not_delete_reports(cfg, toy_suite, baseline_prompt, executor):
    from uaao.report import write_reports

    memory = Memory(cfg.db_path)
    audit = AuditLog(cfg.audit_path)
    opt = Optimizer(cfg, toy_suite, executor, memory, audit=audit)
    run = opt.run(baseline_prompt, name="rel")
    h = History(memory, audit=audit)
    paths = write_reports(run, toy_suite.suite_id, toy_suite.sha, cfg, memory, h, cfg.reports_dir)
    assert paths["markdown"].exists()
    h.rollback(run.experiment_id, run.seed_artifact.sha, reason="x")
    assert paths["markdown"].exists()  # reversao nao apaga artefatos de relatorio
