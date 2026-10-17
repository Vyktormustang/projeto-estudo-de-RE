"""Testes da memoria persistente SQLite.

Cobre o requisito: "Persistencia da memoria" e "Recuperacao apos falhas".
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from uaao.errors import MemoryError_
from uaao.memory import Memory
from uaao.types import PromptArtifact, TaskCase, TaskSuite, utcnow


def _eval_result(artifact_sha: str, suite_sha: str, split: str, score: float = 1.0):
    from uaao.types import CaseResult, EvalResult

    cases = (
        CaseResult(case_id="a", output="saida a", score=score, passed=score == 1.0,
                   grader="exact_match", details={"k": "v"}),
        CaseResult(case_id="b", output="saida b", score=0.0, passed=False,
                   grader="numeric_exact", error="grader: falhou"),
    )
    return EvalResult(
        artifact_sha=artifact_sha, suite_sha=suite_sha, split=split, cases=cases,
        executor="policy_reference_v1", seed=1, started_at=utcnow(), duration_ms=5,
        metric_calls=2,
    )


@pytest.fixture
def seeded(memory):
    eid = memory.start_experiment(
        name="t", suite_sha="s" * 64, suite_id="toy", suite_version="1", executor="policy_reference_v1",
        seed=1, config={"limits": {"max_iterations": 1}}, safety_fp="abc",
    )
    art = PromptArtifact(text="A = 1\n", origin="seed", notes="semente")
    memory.save_artifact(art, eid)
    memory.set_active(eid, art.sha, "baseline")
    memory.save_evaluation(eid, _eval_result(art.sha, "s" * 64, "val", 0.5), iteration=0)
    return eid, art


# --------------------------------------------------------------------------
# Persistencia basica
# --------------------------------------------------------------------------
def test_schema_created_and_integrity_ok(cfg):
    m = Memory(cfg.db_path)
    ok, msg = m.integrity_check()
    assert ok and msg == "ok"
    assert Path(cfg.db_path).exists()


def test_experiment_lifecycle(memory):
    eid = memory.start_experiment(
        name="exp", suite_sha="x" * 64, suite_id="s", suite_version="1",
        executor="policy_reference_v1", seed=7, config={}, safety_fp="fp",
    )
    row = memory.get_experiment(eid)
    assert row.name == "exp" and row.status == "running" and row.seed == 7
    memory.finish_experiment(eid, status="finished")
    assert memory.get_experiment(eid).status == "finished"
    assert any(e.experiment_id == eid for e in memory.list_experiments())


def test_artifact_roundtrip_and_integrity(memory, seeded):
    eid, art = seeded
    back = memory.get_artifact(art.sha)
    assert back.text == art.text
    assert back.sha == art.sha
    assert back.notes == "semente"


def test_artifact_save_is_idempotent(seeded, memory):
    eid, art = seeded
    assert memory.save_artifact(art, eid) == art.sha
    assert memory.count("artifacts") == 1


def test_artifact_corruption_detected(memory, seeded):
    """Se o texto no banco nao casar com o hash, a leitura FALHA (nunca silencia)."""
    eid, art = seeded
    with sqlite3.connect(str(memory.path)) as conn:
        conn.execute("UPDATE artifacts SET text=? WHERE artifact_sha=?", ("adulterado\n", art.sha))
    with pytest.raises(MemoryError_) as exc:
        memory.get_artifact(art.sha)
    assert "integridade violada" in str(exc.value)


def test_evaluation_and_case_drilldown_persisted(memory, seeded):
    eid, art = seeded
    hist = memory.evaluation_history(eid, split="val")
    assert len(hist) == 1 and hist[0]["mean_score"] == 0.25
    rows = memory.case_drilldown(eid, art.sha, "val")
    assert {r["case_id"] for r in rows} == {"a", "b"}
    assert next(r for r in rows if r["case_id"] == "b")["error"].startswith("grader")


def test_decisions_iterations_errors_persisted(memory, seeded):
    from uaao.types import Decision

    eid, art = seeded
    memory.save_decision(eid, 0, art.sha, "b" * 64,
                         Decision(accepted=False, reason="motivo", checks={"x": 1}))
    memory.save_iteration(eid, 0, {"clusters": []}, [{"sha": "b" * 64}], outcome="rejeitado")
    memory.record_error(eid, 0, "executor", "algo falhou")
    assert memory.list_decisions(eid)[0]["reason"] == "motivo"
    assert memory.list_iterations(eid)[0]["outcome"] == "rejeitado"
    assert memory.list_errors(eid)[0]["scope"] == "executor"


def test_secrets_are_redacted_before_persisting(memory):
    eid = memory.start_experiment(
        name="t", suite_sha="s", suite_id="s", suite_version="1",
        executor="e", seed=1, config={"token": "sk-" + "z" * 24}, safety_fp="f",
    )
    from uaao.types import CaseResult, EvalResult

    art = PromptArtifact(text="texto", origin="seed")
    memory.save_artifact(art, eid)
    res = EvalResult(
        artifact_sha=art.sha, suite_sha="s", split="val",
        cases=(CaseResult(case_id="k", output="usando sk-" + "z" * 24,
                          score=1.0, passed=True, grader="g"),),
        executor="e", seed=1, started_at=utcnow(), duration_ms=1, metric_calls=1,
    )
    memory.save_evaluation(eid, res)

    # ATENCAO: em WAL os escritos recentes ficam no arquivo -wal, nao no .db.
    # Inspecionar apenas o .db daria um falso "esta limpo" -- foi assim que este
    # teste passou por engano antes. Verificamos os dois arquivos.
    leak_bytes = (b"sk-" + b"z" * 24)
    blob = b"".join(
        p.read_bytes() for p in (memory.path, Path(str(memory.path) + "-wal")) if p.exists()
    )
    assert leak_bytes not in blob, "segredo persistido em claro"
    assert b"[REDACTED]" in blob or b"[REDACTED]" in memory.path.read_bytes()

    # e confirmando pelo proprio banco (nao apenas pelos bytes do arquivo)
    rows = memory.case_drilldown(eid, art.sha, "val")
    assert all("sk-" not in (r["output_head"] or "") for r in rows)


# --------------------------------------------------------------------------
# Recuperacao apos falhas
# --------------------------------------------------------------------------
def test_recovery_after_hard_crash(tmp_path):
    """Encerra sem fechar 'limpo' e reabre: dados e integridade preservados (WAL)."""
    path = tmp_path / "crash.sqlite3"
    m1 = Memory(path)
    eid = m1.start_experiment(name="crash", suite_sha="s", suite_id="s", suite_version="1",
                              executor="e", seed=1, config={}, safety_fp="f")
    art = PromptArtifact(text="A = 1\n", origin="seed")
    m1.save_artifact(art, eid)
    m1.set_active(eid, art.sha, "baseline")
    m1.save_evaluation(eid, _eval_result(art.sha, "s", "val", 0.25))
    del m1  # simula processo encerrado abruptamente (sem close explicito)

    m2 = Memory(path)
    ok, msg = m2.integrity_check()
    assert ok, msg
    assert m2.get_experiment(eid).status == "running"  # marcado como interrompido, nao perdido
    assert m2.get_active(eid)[0] == art.sha
    assert m2.count("evaluations") == 1


def test_interrupted_status_can_be_recorded(tmp_path):
    m = Memory(tmp_path / "m.sqlite3")
    eid = m.start_experiment(name="i", suite_sha="s", suite_id="s", suite_version="1",
                             executor="e", seed=1, config={}, safety_fp="f")
    m.finish_experiment(eid, status="interrupted", notes="orcamento esgotado")
    row = m.get_experiment(eid)
    assert row.status == "interrupted"


def test_invalid_status_rejected(memory):
    eid = memory.start_experiment(name="x", suite_sha="s", suite_id="s", suite_version="1",
                                  executor="e", seed=1, config={}, safety_fp="f")
    with pytest.raises(MemoryError_):
        memory.finish_experiment(eid, status="qualquer_coisa")


def test_missing_artifact_raises(memory):
    with pytest.raises(MemoryError_):
        memory.get_artifact("0" * 64)


def test_count_rejects_unlisted_table(memory):
    with pytest.raises(MemoryError_):
        memory.count("sqlite_master")


def test_export_experiment_is_serializable(memory, seeded):
    import json

    eid, _ = seeded
    payload = memory.export_experiment(eid)
    text = json.dumps(payload, ensure_ascii=False)
    assert eid in text and payload["digest"]
    assert payload["versions"]
