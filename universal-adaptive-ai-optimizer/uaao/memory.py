"""Modulo 6 - Memoria persistente local em SQLite.

Guarda, para cada experimento: prompt, versao, suite+hash, metricas, erros,
candidatos aceitos/rejeitados, motivos, data/modelo/configuracao. Permite
consultar historico e reverter para versao anterior (modulo 7).

Decisoes de robustez:
  * ``journal_mode=WAL`` + ``synchronous=FULL`` -> sobrevive a queda do processo
    (testado em tests/test_memory.py::test_recovery_after_crash).
  * Escritas transacionais por operacao logica (nada de estado meio-gravado).
  * Todo texto passa por ``redact()`` antes de tocar o disco: nenhum segredo e
    persistido, mesmo que apareca por acidente numa saida.
  * Reverter NAO apaga nada: apenas move o ponteiro ``active_artifact``.
    O historico e imutavel por design (auditoria).
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import MemoryError_
from .safety import redact
from .types import Decision, EvalResult, PromptArtifact, canonical_json, utcnow

SCHEMA_VERSION = 2

# Migracoes incrementais: (versao_alvo, sql). Aplicadas em ordem, de forma
# idempotente, para que um banco criado por uma versao anterior continue valido.
MIGRATIONS: tuple[tuple[int, str], ...] = (
    (2, "ALTER TABLE case_results ADD COLUMN weight REAL NOT NULL DEFAULT 1.0"),
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id   TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'running',
    suite_id        TEXT,
    suite_version   TEXT,
    suite_sha       TEXT,
    executor        TEXT,
    seed            INTEGER,
    config_json     TEXT,
    safety_fp       TEXT,
    git_commit      TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_sha    TEXT PRIMARY KEY,
    text            TEXT NOT NULL,
    origin          TEXT NOT NULL,
    parent_sha      TEXT,
    notes           TEXT,
    created_at      TEXT NOT NULL,
    experiment_id   TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
);
CREATE INDEX IF NOT EXISTS idx_artifacts_parent ON artifacts(parent_sha);

CREATE TABLE IF NOT EXISTS active_artifact (
    experiment_id   TEXT PRIMARY KEY,
    artifact_sha    TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    reason          TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
);

CREATE TABLE IF NOT EXISTS iterations (
    experiment_id   TEXT NOT NULL,
    iteration       INTEGER NOT NULL,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    diagnosis_json  TEXT,
    proposals_json  TEXT,
    outcome         TEXT,
    PRIMARY KEY (experiment_id, iteration)
);

CREATE TABLE IF NOT EXISTS evaluations (
    eval_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id   TEXT NOT NULL,
    iteration       INTEGER,
    artifact_sha    TEXT NOT NULL,
    suite_id        TEXT,
    suite_sha       TEXT,
    split           TEXT NOT NULL,
    executor        TEXT NOT NULL,
    seed            INTEGER,
    mean_score      REAL NOT NULL,
    pass_rate       REAL NOT NULL,
    error_count     INTEGER NOT NULL DEFAULT 0,
    duration_ms     INTEGER NOT NULL DEFAULT 0,
    metric_calls    INTEGER NOT NULL DEFAULT 0,
    signature       TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eval_exp ON evaluations(experiment_id, iteration);

CREATE TABLE IF NOT EXISTS case_results (
    eval_id         INTEGER NOT NULL,
    case_id         TEXT NOT NULL,
    grader          TEXT NOT NULL,
    score           REAL NOT NULL,
    passed          INTEGER NOT NULL,
    critical        INTEGER NOT NULL DEFAULT 0,
    weight          REAL NOT NULL DEFAULT 1.0,
    error           TEXT,
    output_head     TEXT,
    details_json    TEXT,
    PRIMARY KEY (eval_id, case_id),
    FOREIGN KEY (eval_id) REFERENCES evaluations(eval_id)
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id   TEXT NOT NULL,
    iteration       INTEGER,
    baseline_sha    TEXT NOT NULL,
    candidate_sha   TEXT NOT NULL,
    accepted        INTEGER NOT NULL,
    reason          TEXT NOT NULL,
    checks_json     TEXT,
    split           TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dec_exp ON decisions(experiment_id, iteration);

CREATE TABLE IF NOT EXISTS errors (
    error_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id   TEXT,
    iteration       INTEGER,
    scope           TEXT NOT NULL,
    message         TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    report_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id   TEXT NOT NULL,
    kind            TEXT NOT NULL,
    path            TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class ExperimentRow:
    experiment_id: str
    name: str
    created_at: str
    updated_at: str
    status: str
    suite_id: str | None
    suite_sha: str | None
    suite_version: str | None
    executor: str | None
    seed: int | None

    def to_json(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "suite_id": self.suite_id,
            "suite_sha": self.suite_sha,
            "suite_version": self.suite_version,
            "executor": self.executor,
            "seed": self.seed,
        }


class Memory:
    """Repositorio SQLite. Um objeto por caminho de banco; abre/fecha por operacao."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # -- conexao -----------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = FULL")
        return conn

    def _init_schema(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(_SCHEMA)
                self._migrate(conn)
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        except sqlite3.Error as exc:  # pragma: no cover
            raise MemoryError_(f"falha ao inicializar banco em {self.path}: {exc}") from exc

    @staticmethod
    def _migrate(conn: sqlite3.Connection) -> None:
        """Aplica migracoes pendentes de forma idempotente.

        Bancos criados antes de uma coluna existir precisam sobreviver: memoria
        persistente que perde dados numa atualizacao nao e memoria.
        """
        current = int(conn.execute("PRAGMA user_version").fetchone()[0])
        for target, sql in MIGRATIONS:
            if current >= target:
                continue
            try:
                conn.execute(sql)
            except sqlite3.OperationalError:
                # Coluna ja existe (banco criado pelo schema novo sem user_version
                # atualizado): nada a fazer.
                pass

    # -- experimentos ------------------------------------------------------
    def start_experiment(
        self,
        name: str,
        suite_sha: str,
        suite_id: str,
        suite_version: str,
        executor: str,
        seed: int,
        config: Mapping[str, Any],
        safety_fp: str,
        git_commit: str = "",
        notes: str = "",
        experiment_id: str | None = None,
    ) -> str:
        eid = experiment_id or f"exp-{uuid.uuid4().hex[:12]}"
        now = utcnow()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO experiments
                   (experiment_id, name, created_at, updated_at, status, suite_id,
                    suite_version, suite_sha, executor, seed, config_json, safety_fp,
                    git_commit, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    eid, name, now, now, "running", suite_id, suite_version, suite_sha,
                    executor, int(seed), json.dumps(redact(dict(config)), sort_keys=True),
                    safety_fp, git_commit, notes,
                ),
            )
        return eid

    def finish_experiment(self, experiment_id: str, status: str = "finished", notes: str = "") -> None:
        if status not in ("finished", "failed", "interrupted", "running"):
            raise MemoryError_(f"status invalido: {status!r}")
        with self._connect() as conn:
            conn.execute(
                "UPDATE experiments SET status=?, updated_at=?, notes=COALESCE(NULLIF(?,''), notes) WHERE experiment_id=?",
                (status, utcnow(), notes, experiment_id),
            )

    def get_experiment(self, experiment_id: str) -> ExperimentRow:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
        if row is None:
            raise MemoryError_(f"experimento inexistente: {experiment_id}")
        return ExperimentRow(
            experiment_id=row["experiment_id"], name=row["name"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            status=row["status"], suite_id=row["suite_id"], suite_sha=row["suite_sha"],
            suite_version=row["suite_version"], executor=row["executor"], seed=row["seed"],
        )

    def list_experiments(self, limit: int = 50) -> list[ExperimentRow]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            ExperimentRow(
                experiment_id=r["experiment_id"], name=r["name"], created_at=r["created_at"],
                updated_at=r["updated_at"], status=r["status"], suite_id=r["suite_id"],
                suite_sha=r["suite_sha"], suite_version=r["suite_version"],
                executor=r["executor"], seed=r["seed"],
            )
            for r in rows
        ]

    # -- artefatos ---------------------------------------------------------
    def save_artifact(self, artifact: PromptArtifact, experiment_id: str) -> str:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT text FROM artifacts WHERE artifact_sha=?", (artifact.sha,)
            ).fetchone()
            if existing is not None:
                # Idempotente: mesmo sha == mesmo texto (verificamos para detectar
                # corrupcao de hash).
                if existing["text"] != redact(artifact.text):
                    raise MemoryError_(
                        f"colisao/adulteracao de hash para {artifact.sha[:12]}: "
                        "texto armazenado difere do texto recebido"
                    )
                return artifact.sha
            conn.execute(
                """INSERT INTO artifacts
                   (artifact_sha, text, origin, parent_sha, notes, created_at, experiment_id)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    artifact.sha, redact(artifact.text), artifact.origin,
                    artifact.parent_sha, redact(artifact.notes), utcnow(), experiment_id,
                ),
            )
        return artifact.sha

    def resolve_sha(self, prefix: str) -> str:
        """Resolve um prefixo de sha (>=8 chars) para o sha completo.

        Necessario porque a CLI exibe shas curtos (12 chars) e o usuario os
        reutiliza em comandos como ``diff``/``rollback``. Ambiguidade e erro
        explicito, nunca "escolhe um".
        """
        prefix = prefix.strip()
        if len(prefix) < 8:
            raise MemoryError_(
                f"prefixo curto demais ({len(prefix)} chars): use pelo menos 8 para evitar ambiguidade"
            )
        if len(prefix) == 64:
            return prefix
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT artifact_sha FROM artifacts WHERE artifact_sha LIKE ?",
                (prefix + "%",),
            ).fetchall()
        shas = [r["artifact_sha"] for r in rows]
        if not shas:
            raise MemoryError_(f"artefato nao encontrado para o prefixo {prefix!r}")
        if len(shas) > 1:
            raise MemoryError_(
                f"prefixo ambiguo {prefix!r}: {len(shas)} artefatos correspondem"
            )
        return shas[0]

    def get_artifact(self, artifact_sha: str) -> PromptArtifact:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT a.*, e.experiment_id AS exp FROM artifacts a
                   LEFT JOIN experiments e ON e.experiment_id = a.experiment_id
                   WHERE a.artifact_sha=?""",
                (artifact_sha,),
            ).fetchone()
        if row is None:
            raise MemoryError_(f"artefato inexistente: {artifact_sha[:12]}")
        art = PromptArtifact(
            text=row["text"], origin=row["origin"], parent_sha=row["parent_sha"],
            notes=row["notes"] or "",
        )
        if art.sha != artifact_sha:
            raise MemoryError_(
                f"integridade violada: texto do artefato {artifact_sha[:12]} "
                f"tem hash {art.sha[:12]}"
            )
        return art

    def set_active(self, experiment_id: str, artifact_sha: str, reason: str) -> None:
        """Move o ponteiro da versao ativa (aceitacao OU rollback)."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO active_artifact (experiment_id, artifact_sha, updated_at, reason)
                   VALUES (?,?,?,?)
                   ON CONFLICT(experiment_id) DO UPDATE SET
                     artifact_sha=excluded.artifact_sha,
                     updated_at=excluded.updated_at,
                     reason=excluded.reason""",
                (experiment_id, artifact_sha, utcnow(), redact(reason)),
            )

    def get_active(self, experiment_id: str) -> tuple[str, str] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT artifact_sha, reason FROM active_artifact WHERE experiment_id=?",
                (experiment_id,),
            ).fetchone()
        return (row["artifact_sha"], row["reason"]) if row else None

    def lineage(self, artifact_sha: str, limit: int = 200) -> list[dict[str, Any]]:
        """Cadeia de proveniencia do artefato ate a raiz (seed)."""
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        cur: str | None = artifact_sha
        with self._connect() as conn:
            while cur and cur not in seen and len(out) < limit:
                seen.add(cur)
                row = conn.execute(
                    "SELECT artifact_sha, parent_sha, origin, notes, created_at FROM artifacts WHERE artifact_sha=?",
                    (cur,),
                ).fetchone()
                if row is None:
                    break
                out.append(
                    {
                        "sha": row["artifact_sha"][:12],
                        "full_sha": row["artifact_sha"],
                        "origin": row["origin"],
                        "notes": row["notes"],
                        "created_at": row["created_at"],
                    }
                )
                cur = row["parent_sha"]
        return out

    def list_versions(self, experiment_id: str) -> list[dict[str, Any]]:
        """Todas as versoes conhecidas do experimento, com metricas da ultima avaliacao."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT a.artifact_sha, a.origin, a.notes, a.created_at,
                          (SELECT COUNT(*) FROM evaluations e
                            WHERE e.artifact_sha = a.artifact_sha AND e.split='val') AS n_val,
                          (SELECT e.mean_score FROM evaluations e
                            WHERE e.artifact_sha = a.artifact_sha AND e.split='val'
                            ORDER BY e.eval_id DESC LIMIT 1) AS last_val
                   FROM artifacts a
                   WHERE a.experiment_id = ?
                   ORDER BY a.created_at, a.rowid""",
                (experiment_id,),
            ).fetchall()
            active = conn.execute(
                "SELECT artifact_sha FROM active_artifact WHERE experiment_id=?",
                (experiment_id,),
            ).fetchone()
        active_sha = active["artifact_sha"] if active else None
        return [
            {
                "sha": r["artifact_sha"][:12],
                "full_sha": r["artifact_sha"],
                "origin": r["origin"],
                "notes": r["notes"],
                "created_at": r["created_at"],
                "val_evaluations": r["n_val"],
                "last_val_score": r["last_val"],
                "active": r["artifact_sha"] == active_sha,
            }
            for r in rows
        ]

    # -- avaliacoes --------------------------------------------------------
    def save_evaluation(
        self, experiment_id: str, result: EvalResult, iteration: int | None = None
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO evaluations
                   (experiment_id, iteration, artifact_sha, suite_id, suite_sha, split,
                    executor, seed, mean_score, pass_rate, error_count, duration_ms,
                    metric_calls, signature, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    experiment_id, iteration, result.artifact_sha, None, result.suite_sha,
                    result.split, result.executor, int(result.seed),
                    round(result.mean_score, 6), round(result.pass_rate, 6),
                    result.error_count, result.duration_ms, result.metric_calls,
                    result.deterministic_signature(), utcnow(),
                ),
            )
            eval_id = int(cur.lastrowid)
            conn.executemany(
                """INSERT INTO case_results
                   (eval_id, case_id, grader, score, passed, critical, weight, error, output_head, details_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                [
                    (
                        eval_id, c.case_id, c.grader, round(c.score, 6), int(c.passed),
                        int(c.critical), float(c.weight), redact(c.error) if c.error else None,
                        redact((c.output or "")[:300]),
                        json.dumps(redact(dict(c.details)), sort_keys=True)[:4000],
                    )
                    for c in result.cases
                ],
            )
        return eval_id

    def latest_evaluation(self, experiment_id: str, artifact_sha: str, split: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT * FROM evaluations
                   WHERE experiment_id=? AND artifact_sha=? AND split=?
                   ORDER BY eval_id DESC LIMIT 1""",
                (experiment_id, artifact_sha, split),
            ).fetchone()
        return dict(row) if row else None

    def evaluation_history(self, experiment_id: str, split: str | None = None) -> list[dict[str, Any]]:
        q = "SELECT * FROM evaluations WHERE experiment_id=?"
        args: list[Any] = [experiment_id]
        if split:
            q += " AND split=?"
            args.append(split)
        q += " ORDER BY eval_id"
        with self._connect() as conn:
            rows = conn.execute(q, args).fetchall()
        return [dict(r) for r in rows]

    def case_drilldown(self, experiment_id: str, artifact_sha: str, split: str = "val") -> list[dict[str, Any]]:
        """Detalhe por caso da ultima avaliacao (para auditoria/relatorio)."""
        with self._connect() as conn:
            eval_row = conn.execute(
                """SELECT eval_id FROM evaluations
                   WHERE experiment_id=? AND artifact_sha=? AND split=?
                   ORDER BY eval_id DESC LIMIT 1""",
                (experiment_id, artifact_sha, split),
            ).fetchone()
            if eval_row is None:
                return []
            rows = conn.execute(
                "SELECT * FROM case_results WHERE eval_id=? ORDER BY case_id",
                (eval_row["eval_id"],),
            ).fetchall()
        return [dict(r) for r in rows]

    # -- propostas / decisoes / erros --------------------------------------
    def save_iteration(
        self,
        experiment_id: str,
        iteration: int,
        diagnosis_json: Mapping[str, Any] | None,
        proposals: Sequence[Mapping[str, Any]],
        outcome: str | None = None,
        started_at: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO iterations
                   (experiment_id, iteration, started_at, finished_at, diagnosis_json, proposals_json, outcome)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(experiment_id, iteration) DO UPDATE SET
                     finished_at=excluded.finished_at,
                     diagnosis_json=excluded.diagnosis_json,
                     proposals_json=excluded.proposals_json,
                     outcome=excluded.outcome""",
                (
                    experiment_id, iteration, started_at or utcnow(),
                    utcnow() if outcome else None,
                    json.dumps(redact(dict(diagnosis_json)), sort_keys=True) if diagnosis_json else None,
                    json.dumps(redact(list(proposals)), sort_keys=True),
                    outcome,
                ),
            )

    def list_iterations(self, experiment_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM iterations WHERE experiment_id=? ORDER BY iteration",
                (experiment_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def save_decision(
        self, experiment_id: str, iteration: int | None, baseline_sha: str,
        candidate_sha: str, decision: Decision, split: str = "val",
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO decisions
                   (experiment_id, iteration, baseline_sha, candidate_sha, accepted, reason, checks_json, split, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    experiment_id, iteration, baseline_sha, candidate_sha,
                    int(decision.accepted), redact(decision.reason),
                    json.dumps(redact(dict(decision.checks)), sort_keys=True)[:20000],
                    split, utcnow(),
                ),
            )
            return int(cur.lastrowid)

    def list_decisions(self, experiment_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE experiment_id=? ORDER BY decision_id",
                (experiment_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def record_error(self, experiment_id: str | None, iteration: int | None, scope: str, message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO errors (experiment_id, iteration, scope, message, created_at)
                   VALUES (?,?,?,?,?)""",
                (experiment_id, iteration, scope, redact(message)[:4000], utcnow()),
            )

    def list_errors(self, experiment_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM errors WHERE experiment_id=? ORDER BY error_id", (experiment_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def record_report(self, experiment_id: str, kind: str, path: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO reports (experiment_id, kind, path, created_at) VALUES (?,?,?,?)",
                (experiment_id, kind, path, utcnow()),
            )

    def list_reports(self, experiment_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM reports WHERE experiment_id=? ORDER BY report_id", (experiment_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    # -- manutencao --------------------------------------------------------
    def integrity_check(self) -> tuple[bool, str]:
        with self._connect() as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            ok = row is not None and row[0] == "ok"
        return ok, (row[0] if row else "sem resposta")

    def count(self, table: str) -> int:
        allowed = {
            "experiments", "artifacts", "evaluations", "case_results",
            "decisions", "errors", "iterations", "reports",
        }
        if table not in allowed:
            raise MemoryError_(f"tabela nao permitida: {table!r}")
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        return int(row["n"])

    def export_experiment(self, experiment_id: str) -> dict[str, Any]:
        """Dump completo e legivel do experimento (usado para backup no Drive)."""
        exp = self.get_experiment(experiment_id)
        with self._connect() as conn:
            exp_row = dict(conn.execute(
                "SELECT * FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone())
            artifacts = [dict(r) for r in conn.execute(
                "SELECT * FROM artifacts WHERE experiment_id=? ORDER BY rowid", (experiment_id,)).fetchall()]
            active = conn.execute(
                "SELECT * FROM active_artifact WHERE experiment_id=?", (experiment_id,)).fetchone()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "exported_at": utcnow(),
            "experiment": exp_row,
            "active_artifact": dict(active) if active else None,
            "artifacts": artifacts,
            "evaluations": self.evaluation_history(experiment_id),
            "decisions": self.list_decisions(experiment_id),
            "iterations": self.list_iterations(experiment_id),
            "errors": self.list_errors(experiment_id),
            "versions": self.list_versions(experiment_id),
        }
        payload["digest"] = canonical_json({
            k: len(v) if isinstance(v, (list, dict)) else v
            for k, v in payload.items() if k != "digest"
        })
        return payload


__all__ = ["Memory", "ExperimentRow", "SCHEMA_VERSION"]
