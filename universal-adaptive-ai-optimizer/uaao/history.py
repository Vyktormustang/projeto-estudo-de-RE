"""Modulo 7 - Historico e versionamento de experimentos + reversao.

Regras de ouro:
  * O historico e **append-only**: nada e apagado nem sobrescrito.
  * "Reverter" significa mover o ponteiro ``active_artifact`` para uma versao
    anterior e registrar o motivo. A versao revertida continua existindo.
  * Toda reversao gera entrada na trilha de auditoria (hash-encadeada) e, se
    houver memorias de decisao, uma decisao explicita de rollback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import MemoryError_
from .memory import Memory
from .promptspec import directive_diff
from .safety import AuditLog


@dataclass(frozen=True)
class VersionEntry:
    sha: str
    short: str
    origin: str
    notes: str
    created_at: str
    val_evaluations: int
    last_val_score: float | None
    active: bool


@dataclass(frozen=True)
class RollbackResult:
    experiment_id: str
    from_sha: str
    to_sha: str
    reason: str
    ok: bool
    message: str


class History:
    """Fachada de consulta/versionamento sobre a ``Memory``."""

    def __init__(self, memory: Memory, audit: AuditLog | None = None) -> None:
        self.memory = memory
        self.audit = audit

    # -- consulta ----------------------------------------------------------
    def versions(self, experiment_id: str) -> list[VersionEntry]:
        raw = self.memory.list_versions(experiment_id)
        return [
            VersionEntry(
                sha=r["full_sha"], short=r["sha"], origin=r["origin"], notes=r["notes"],
                created_at=r["created_at"], val_evaluations=r["val_evaluations"],
                last_val_score=r["last_val_score"], active=r["active"],
            )
            for r in raw
        ]

    def timeline(self, experiment_id: str) -> list[dict[str, Any]]:
        """Linha do tempo unificada: iteracoes, decisoes e avaliacoes em ordem."""
        events: list[dict[str, Any]] = []
        for it in self.memory.list_iterations(experiment_id):
            events.append(
                {
                    "type": "iteration",
                    "at": it["started_at"],
                    "iteration": it["iteration"],
                    "outcome": it["outcome"],
                }
            )
        for d in self.memory.list_decisions(experiment_id):
            events.append(
                {
                    "type": "decision",
                    "at": d["created_at"],
                    "iteration": d["iteration"],
                    "accepted": bool(d["accepted"]),
                    "candidate": d["candidate_sha"][:12],
                    "baseline": d["baseline_sha"][:12],
                    "reason": d["reason"],
                    "split": d["split"],
                }
            )
        for e in self.memory.evaluation_history(experiment_id):
            events.append(
                {
                    "type": "evaluation",
                    "at": e["created_at"],
                    "iteration": e["iteration"],
                    "artifact": e["artifact_sha"][:12],
                    "split": e["split"],
                    "mean_score": e["mean_score"],
                    "pass_rate": e["pass_rate"],
                    "signature": (e["signature"] or "")[:12],
                }
            )
        for err in self.memory.list_errors(experiment_id):
            events.append(
                {
                    "type": "error",
                    "at": err["created_at"],
                    "iteration": err["iteration"],
                    "scope": err["scope"],
                    "message": err["message"][:200],
                }
            )
        return sorted(events, key=lambda e: (e.get("at") or "", e["type"]))

    def best_version(self, experiment_id: str, split: str = "val") -> str | None:
        """Artefato com maior score na divisao pedida (empate: o mais antigo)."""
        best_sha, best = None, float("-inf")
        for e in self.memory.evaluation_history(experiment_id, split=split):
            if e["mean_score"] > best:
                best, best_sha = float(e["mean_score"]), e["artifact_sha"]
        return best_sha

    def _full(self, sha: str) -> str:
        """Aceita sha completo ou prefixo (>=8 chars), como a CLI exibe."""
        return sha if len(sha) == 64 else self.memory.resolve_sha(sha)

    def diff(self, sha_a: str, sha_b: str) -> dict[str, Any]:
        a = self.memory.get_artifact(self._full(sha_a))
        b = self.memory.get_artifact(self._full(sha_b))
        return {
            "from": a.sha_short,
            "to": b.sha_short,
            "directive_changes": {
                k: {"before": v[0], "after": v[1]} for k, v in directive_diff(a.text, b.text).items()
            },
            "origin_from": a.origin,
            "origin_to": b.origin,
            "notes_to": b.notes,
        }

    # -- reversao ----------------------------------------------------------
    def rollback(
        self,
        experiment_id: str,
        target: str,
        reason: str = "",
        iteration: int | None = None,
    ) -> RollbackResult:
        """Reverte a versao ativa para ``target``.

        ``target`` aceita: sha completo, sha curto (>=8 chars) ou "previous"/"anterior".
        Nunca apaga nada.
        """
        active = self.memory.get_active(experiment_id)
        if active is None:
            raise MemoryError_(f"experimento {experiment_id} nao tem versao ativa")
        from_sha = active[0]

        versions = self.versions(experiment_id)
        if not versions:
            raise MemoryError_("nenhuma versao registrada")

        if target in ("previous", "anterior", "prev"):
            idx = next((i for i, v in enumerate(versions) if v.sha == from_sha), None)
            if idx is None or idx == 0:
                return RollbackResult(
                    experiment_id, from_sha, from_sha, reason, False,
                    "nao existe versao anterior a ativa",
                )
            to_sha = versions[idx - 1].sha
        else:
            matches = [v for v in versions if v.sha == target or v.sha.startswith(target)]
            if not matches:
                return RollbackResult(
                    experiment_id, from_sha, target, reason, False,
                    f"versao alvo nao encontrada: {target!r}",
                )
            if len(matches) > 1:
                return RollbackResult(
                    experiment_id, from_sha, target, reason, False,
                    f"prefixo ambiguo {target!r}: casa com {len(matches)} versoes",
                )
            to_sha = matches[0].sha

        if to_sha == from_sha:
            return RollbackResult(
                experiment_id, from_sha, to_sha, reason, False,
                "a versao alvo ja e a ativa (nada a fazer)",
            )

        self.memory.get_artifact(to_sha)  # valida integridade do alvo
        self.memory.set_active(experiment_id, to_sha, f"ROLLBACK: {reason or 'sem motivo declarado'}")
        if self.audit is not None:
            self.audit.record(
                "rollback",
                {
                    "experiment_id": experiment_id,
                    "from": from_sha[:12],
                    "to": to_sha[:12],
                    "reason": reason,
                },
            )
        return RollbackResult(
            experiment_id, from_sha, to_sha, reason, True,
            f"revertido de {from_sha[:12]} para {to_sha[:12]}",
        )

    def summary(self, experiment_id: str) -> dict[str, Any]:
        exp = self.memory.get_experiment(experiment_id)
        versions = self.versions(experiment_id)
        active = self.memory.get_active(experiment_id)
        decisions = self.memory.list_decisions(experiment_id)
        return {
            "experiment": {
                "id": exp.experiment_id, "name": exp.name, "status": exp.status,
                "created_at": exp.created_at, "suite_id": exp.suite_id,
                "suite_sha": (exp.suite_sha or "")[:12], "executor": exp.executor, "seed": exp.seed,
            },
            "versions": [
                {
                    "sha": v.short, "origin": v.origin, "notes": v.notes,
                    "val_score": v.last_val_score, "active": v.active,
                }
                for v in versions
            ],
            "active": (active[0][:12], active[1]) if active else None,
            "decisions": {
                "total": len(decisions),
                "accepted": sum(1 for d in decisions if d["accepted"]),
                "rejected": sum(1 for d in decisions if not d["accepted"]),
            },
            "counts": {
                "evaluations": self.memory.count("evaluations"),
                "artifacts": self.memory.count("artifacts"),
                "errors": self.memory.count("errors"),
            },
        }


__all__ = ["History", "VersionEntry", "RollbackResult"]
