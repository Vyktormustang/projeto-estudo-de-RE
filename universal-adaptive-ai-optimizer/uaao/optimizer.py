"""Ciclo automatico de otimizacao.

    BASELINE -> AVALIACAO -> DIAGNOSTICO -> GERACAO DE CANDIDATOS ->
    TESTE -> COMPARACAO -> SELECAO -> REGISTRO

Regras metodologicas aplicadas pelo orquestrador:

  * O prompt original NUNCA e modificado: ele e gravado como artefato semente e
    permanece imutavel na memoria. Melhorias sao *novos* artefatos.
  * Treino orienta o diagnostico; validacao decide a selecao; o holdout so e
    tocado no final, para confirmacao independente.
  * Aceitacao apenas por criterio predefinido (``select.accept_candidate``).
    Todo candidato testado -- aceito ou rejeitado -- e registrado com o motivo.
  * Orcamentos (chamadas, tentativas, tempo, custo) sao conferidos a cada passo;
    estourar o teto interrompe o ciclo de forma limpa, preservando os resultados
    ja obtidos ("recuperacao apos falhas").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .compare import Comparison, compare
from .config import Config
from .diagnose import Diagnosis, diagnose
from .errors import BudgetExceeded, UaaoError
from .evaluate import evaluate
from .executors import Executor
from .history import History
from .memory import Memory
from .provenance import run_context
from .propose import HeuristicProposer, Proposal
from .safety import AuditLog, BudgetLedger, SafetyPolicy
from .select import accept_candidate
from .types import CaseResult, Decision, EvalResult, PromptArtifact, TaskSuite


@dataclass
class CandidateOutcome:
    """Tudo que aconteceu com um candidato: teste, comparacao e veredito."""

    proposal: Proposal
    val_result: EvalResult
    comparison: Comparison
    decision: Decision
    accepted: bool
    already_tested: bool = False
    from_cache: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "sha": self.proposal.artifact.sha_short,
            "operator": self.proposal.operator,
            "rationale": self.proposal.rationale,
            "targets": list(self.proposal.targets),
            "val_score": round(self.val_result.mean_score, 6),
            "accepted": self.accepted,
            "reason": self.decision.reason,
            "comparison": self.comparison.to_json(),
            "already_tested": self.already_tested,
            "from_cache": self.from_cache,
        }


@dataclass
class CycleIteration:
    index: int
    diagnosis: Diagnosis
    n_proposals: int
    outcomes: list[CandidateOutcome] = field(default_factory=list)
    accepted_sha: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "iteration": self.index,
            "diagnosis": self.diagnosis.to_json(),
            "n_proposals": self.n_proposals,
            "accepted_sha": self.accepted_sha[:12] if self.accepted_sha else None,
            "outcomes": [o.to_json() for o in self.outcomes],
        }


@dataclass
class OptimizationRun:
    experiment_id: str
    name: str
    seed_artifact: PromptArtifact
    final_artifact: PromptArtifact
    iterations: list[CycleIteration]
    baseline_val: EvalResult
    baseline_train: EvalResult
    final_val: EvalResult
    final_train: EvalResult
    holdout_baseline: EvalResult | None
    holdout_final: EvalResult | None
    stopped_reason: str
    ledger_snapshot: dict[str, Any]
    determinism_ok: bool | None = None
    determinism_signatures: tuple[str, ...] = ()
    proposer_coverage: tuple[str, ...] = ()
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def improved(self) -> bool:
        return self.final_val.mean_score > self.baseline_val.mean_score + 1e-12

    def accepted_count(self) -> int:
        return sum(1 for it in self.iterations for o in it.outcomes if o.accepted)

    def tested_count(self) -> int:
        return sum(1 for it in self.iterations for o in it.outcomes)

    def to_json(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "seed_sha": self.seed_artifact.sha_short,
            "final_sha": self.final_artifact.sha_short,
            "stopped_reason": self.stopped_reason,
            "baseline": {
                "train": round(self.baseline_train.mean_score, 6),
                "val": round(self.baseline_val.mean_score, 6),
                "holdout": round(self.holdout_baseline.mean_score, 6) if self.holdout_baseline else None,
            },
            "final": {
                "train": round(self.final_train.mean_score, 6),
                "val": round(self.final_val.mean_score, 6),
                "holdout": round(self.holdout_final.mean_score, 6) if self.holdout_final else None,
            },
            "delta_val": round(self.final_val.mean_score - self.baseline_val.mean_score, 6),
            "delta_holdout": (
                round(self.holdout_final.mean_score - self.holdout_baseline.mean_score, 6)
                if self.holdout_final and self.holdout_baseline else None
            ),
            "candidates_tested": self.tested_count(),
            "candidates_accepted": self.accepted_count(),
            "iterations": [i.to_json() for i in self.iterations],
            "ledger": self.ledger_snapshot,
            "determinism_ok": self.determinism_ok,
            "determinism_signatures": list(self.determinism_signatures),
            "proposer_coverage": list(self.proposer_coverage),
            "context": self.context,
        }


class Optimizer:
    """Orquestra o ciclo. Nao contem logica de metrica (isso e evaluate/select)."""

    def __init__(
        self,
        config: Config,
        suite: TaskSuite,
        executor: Executor,
        memory: Memory,
        audit: AuditLog | None = None,
        policy: SafetyPolicy | None = None,
    ) -> None:
        self.config = config
        self.suite = suite
        self.executor = executor
        self.memory = memory
        self.audit = audit
        self.policy = policy or SafetyPolicy.hardened()
        self.history = History(memory, audit=audit)
        self.ledger: BudgetLedger = config.ledger()
        self._eval_cache: dict[tuple[str, str], EvalResult] = {}

    # ------------------------------------------------------------------
    # Avaliacao com cache em processo + reconstrucao opcional da memoria
    # ------------------------------------------------------------------
    def _evaluate(
        self, experiment_id: str, artifact: PromptArtifact, split: str, iteration: int | None
    ) -> EvalResult:
        key = (artifact.sha, split)
        if key in self._eval_cache:
            return self._eval_cache[key]
        result = evaluate(
            artifact, self.suite, self.executor, split=split,
            seed=self.config.random_seed, ledger=self.ledger,
            max_output_chars=self.config.limits.max_case_output_chars,
        )
        self._eval_cache[key] = result
        self.memory.save_evaluation(experiment_id, result, iteration=iteration)
        return result

    def _try_evaluate(
        self, experiment_id: str, artifact: PromptArtifact, split: str, iteration: int | None = None
    ) -> EvalResult | None:
        """Avalia; devolve None se o orcamento acabar (nunca um resultado inventado)."""
        try:
            return self._evaluate(experiment_id, artifact, split, iteration)
        except BudgetExceeded as exc:
            self.memory.record_error(experiment_id, iteration, "orcamento", str(exc))
            return None

    def _cached_or_evaluate(
        self, experiment_id: str, artifact: PromptArtifact, split: str, iteration: int | None
    ) -> tuple[EvalResult, bool]:
        """Retorna (resultado, veio_da_memoria). Evita repagar avaliacoes em resume."""
        key = (artifact.sha, split)
        if key in self._eval_cache:
            return self._eval_cache[key], True
        rebuilt = self._reconstruct(experiment_id, artifact, split)
        if rebuilt is not None:
            self._eval_cache[key] = rebuilt
            return rebuilt, True
        return self._evaluate(experiment_id, artifact, split, iteration), False

    def _reconstruct(self, experiment_id: str, artifact: PromptArtifact, split: str) -> EvalResult | None:
        """Reconstroi um EvalResult ja gravado (usado ao retomar um experimento).

        As SAIDAS ficam truncadas em 300 caracteres na memoria; scores, vereditos
        e metadados sao exatos. Sinalizamos isso nos detalhes para nao confundir
        com uma execucao nova.
        """
        meta = self.memory.latest_evaluation(experiment_id, artifact.sha, split)
        if meta is None:
            return None
        rows = self.memory.case_drilldown(experiment_id, artifact.sha, split)
        if len(rows) != meta["metric_calls"]:
            return None  # registro incompleto: prefere reexecutar
        def _weight(row: Any) -> float:
            # Bancos antigos (pre-migracao) podem nao ter a coluna 'weight'.
            try:
                return float(row["weight"] or 1.0)
            except (IndexError, KeyError, TypeError):
                return 1.0

        cases = tuple(
            CaseResult(
                case_id=r["case_id"],
                output=r["output_head"] or "",
                score=float(r["score"]),
                passed=bool(r["passed"]),
                grader=r["grader"],
                details={"reconstructed_from_memory": True},
                error=r["error"],
                critical=bool(r["critical"]),
                weight=_weight(r),
            )
            for r in rows
        )
        return EvalResult(
            artifact_sha=artifact.sha,
            suite_sha=meta["suite_sha"] or self.suite.sha,
            split=split,
            cases=cases,
            executor=meta["executor"],
            seed=int(meta["seed"] or 0),
            started_at=meta["created_at"],
            duration_ms=int(meta["duration_ms"] or 0),
            metric_calls=int(meta["metric_calls"] or 0),
        )

    # ------------------------------------------------------------------
    # Ciclo
    # ------------------------------------------------------------------
    def run(
        self,
        seed_artifact: PromptArtifact,
        name: str = "optimization",
        experiment_id: str | None = None,
        resume: bool = False,
    ) -> OptimizationRun:
        if self.audit is not None:
            self.audit.record(
                "run_start",
                {
                    "name": name,
                    "suite": self.suite.suite_id,
                    "suite_sha": self.suite.sha[:12],
                    "seed_sha": seed_artifact.sha_short,
                    "executor": self.executor.name,
                    "safety_fingerprint": self.policy.fingerprint(),
                    "resume": resume,
                },
            )

        context = run_context(self.config.to_json(), self.config.random_seed, self.executor.name)
        stopped_reason = "concluido"
        iterations: list[CycleIteration] = []
        determinism_ok: bool | None = None
        determinism_sigs: tuple[str, ...] = ()
        proposal_ops: list[str] = []

        # Pre-condicao honesta: sem orcamento para medir o baseline, o resultado
        # nao teria significado. Falha ANTES de criar o experimento.
        minimum = len(self.suite.by_split("train")) + len(self.suite.by_split("val"))
        if not resume and self.ledger.max_metric_calls < minimum:
            raise UaaoError(
                f"orcamento insuficiente: {self.ledger.max_metric_calls} chamadas para um "
                f"baseline que exige {minimum} (treino+validacao). Ajuste "
                "limits.max_metric_calls."
            )

        # ---------------- BASELINE ----------------
        if resume and experiment_id:
            exp = self.memory.get_experiment(experiment_id)
            active = self.memory.get_active(experiment_id)
            if active is None:
                raise UaaoError(f"experimento {experiment_id} sem versao ativa: nao ha o que retomar")
            current = self.memory.get_artifact(active[0])
            baseline_train, _ = self._cached_or_evaluate(experiment_id, seed_artifact, "train", 0)
            baseline_val, _ = self._cached_or_evaluate(experiment_id, seed_artifact, "val", 0)
            holdout_baseline, _ = self._cached_or_evaluate(experiment_id, seed_artifact, "holdout", 0)
            current_val, _ = self._cached_or_evaluate(experiment_id, current, "val", None)
            start_iteration = len(self.memory.list_iterations(experiment_id))
        else:
            experiment_id = self.memory.start_experiment(
                name=name, suite_sha=self.suite.sha, suite_id=self.suite.suite_id,
                suite_version=self.suite.version, executor=self.executor.name,
                seed=self.config.random_seed, config=self.config.to_json(),
                safety_fp=self.policy.fingerprint(), git_commit=context["git_commit"],
                notes="prompt original preservado como artefato semente",
                experiment_id=experiment_id,
            )
            # A ordem importa: o experimento precisa existir antes do artefato
            # (a tabela 'artifacts' tem chave estrangeira para 'experiments').
            self.memory.save_artifact(seed_artifact, experiment_id)
            self.memory.set_active(experiment_id, seed_artifact.sha, "BASELINE: prompt original")

            baseline_train = self._evaluate(experiment_id, seed_artifact, "train", 0)
            baseline_val = self._evaluate(experiment_id, seed_artifact, "val", 0)
            holdout_baseline = (
                self._evaluate(experiment_id, seed_artifact, "holdout", 0)
                if self.suite.by_split("holdout") else None
            )
            current = seed_artifact
            current_val = baseline_val
            start_iteration = 0

        assert experiment_id is not None
        active_sha = current.sha
        budget_exhausted = False
        # Motivo de parada por ORCAMENTO, separado do motivo por plateau: sem
        # isto o aviso de plateau sobrescrevia o de orcamento no relatorio
        # (defeito encontrado em teste).
        budget_stop: str | None = None
        train_result: EvalResult | None = None

        # ---------------- LOOP ----------------
        try:
            for index in range(start_iteration, self.config.limits.max_iterations):
                self.ledger.check_wall_clock()
                if self.ledger.remaining() <= 0:
                    budget_stop = "orcamento de chamadas de metrica esgotado"
                    budget_exhausted = True
                    break

                # DIAGNOSTICO (somente treino)
                train_result = self._evaluate(experiment_id, current, "train", index)
                diagnosis = diagnose(train_result)

                # GERACAO
                proposer = HeuristicProposer(
                    max_candidates=self.config.limits.max_candidates_per_iteration
                )
                tested = {o.proposal.artifact.sha for it in iterations for o in it.outcomes}
                proposals = proposer.propose(current, diagnosis, seen_shas=tested)
                proposal_ops.extend(p.operator for p in proposals)
                iteration = CycleIteration(index=index, diagnosis=diagnosis, n_proposals=len(proposals))

                if not proposals:
                    stopped_reason = "nenhum candidato novo a testar (espaco esgotado)"
                    self.memory.save_iteration(
                        experiment_id, index, diagnosis.to_json(), [], outcome="sem_candidatos"
                    )
                    iterations.append(iteration)
                    break

                accepted_this_iteration = False

                # TESTE + COMPARACAO + SELECAO
                for proposal in proposals:
                    if self.ledger.remaining() <= 0:
                        stopped_reason = "orcamento esgotado durante o teste de candidatos"
                        break
                    try:
                        val_result, from_cache = self._cached_or_evaluate(
                            experiment_id, proposal.artifact, "val", index
                        )
                    except BudgetExceeded as exc:
                        self.memory.record_error(experiment_id, index, "orcamento", str(exc))
                        budget_stop = f"orcamento excedido ao testar candidatos: {exc}"
                        budget_exhausted = True
                        break

                    comp = compare(current_val, val_result, seed=self.config.random_seed)
                    decision = accept_candidate(
                        baseline=current_val, candidate=val_result, comp=comp,
                        criteria=self.config.selection,
                    )
                    # Persiste TODO candidato testado, aceito ou nao: o requisito
                    # pede que prompts rejeitados tambem fiquem auditaveis. Sem
                    # isto o artefato ativo poderia nem existir na memoria
                    # (defeito encontrado pelo teste de retomada/reversao).
                    self.memory.save_artifact(proposal.artifact, experiment_id)
                    outcome = CandidateOutcome(
                        proposal=proposal, val_result=val_result, comparison=comp,
                        decision=decision, accepted=decision.accepted, from_cache=from_cache,
                    )
                    iteration.outcomes.append(outcome)
                    self.memory.save_decision(
                        experiment_id, index, current.sha, proposal.artifact.sha, decision, split="val"
                    )
                    if self.audit is not None:
                        self.audit.record(
                            "decision",
                            {
                                "experiment_id": experiment_id, "iteration": index,
                                "candidate": proposal.artifact.sha_short,
                                "operator": proposal.operator,
                                "accepted": decision.accepted,
                                "reason": decision.reason,
                                "val_delta": comp.mean_delta,
                                "p_value": round(comp.sign_test_p, 6),
                            },
                        )

                    if decision.accepted and not accepted_this_iteration:
                        # Reavaliacao na VALIDACAO ja foi feita; promovemos a ativa.
                        current = proposal.artifact
                        active_sha = current.sha
                        current_val = val_result
                        accepted_this_iteration = True
                        iteration.accepted_sha = current.sha
                        self.memory.set_active(experiment_id, current.sha, f"ACEITO na iteracao {index}: {decision.reason}")
                        # Apos aceitar, re-diagnostica (a proxima iteracao parte do novo ativo).
                        break

                self.memory.save_iteration(
                    experiment_id, index, diagnosis.to_json(),
                    [o.to_json() for o in iteration.outcomes],
                    outcome="aceito" if accepted_this_iteration else "nenhum_candidato_aceito",
                )
                iterations.append(iteration)

                if not accepted_this_iteration:
                    if budget_stop is None:
                        stopped_reason = (
                            f"iteracao {index}: nenhum candidato passou nos criterios (plateau)"
                        )
                    break

        except BudgetExceeded as exc:
            budget_stop = f"orcamento excedido: {exc}"
            budget_exhausted = True
            self.memory.record_error(experiment_id, None, "orcamento", str(exc))
        except UaaoError as exc:
            stopped_reason = f"erro do sistema: {type(exc).__name__}: {exc}"
            self.memory.record_error(experiment_id, None, "sistema", str(exc))
            self.memory.finish_experiment(experiment_id, status="failed", notes=stopped_reason)
            raise

        if budget_stop is not None:
            stopped_reason = budget_stop

        # ---------------- REGISTRO FINAL ----------------
        # Se o orcamento acabou, nao inventamos um resultado final: reaproveitamos
        # a ultima medicao REAL do artefato ativo e dizemos isso no relatorio.
        final_train = self._try_evaluate(experiment_id, current, "train") or train_result or baseline_train
        final_val = self._try_evaluate(experiment_id, current, "val") or current_val
        holdout_final = (
            self._try_evaluate(experiment_id, current, "holdout")
            if self.suite.by_split("holdout") else None
        )
        if budget_exhausted and (final_train is baseline_train or final_val is current_val):
            stopped_reason += (
                " | avaliacao final incompleta: os numeros finais vem da ultima medicao "
                "real do artefato ativo (nao de uma reexecucao pos-orcamento)"
            )

        # Prova de determinismo: mesma entrada -> mesma assinatura.
        try:
            from .evaluate import check_determinism

            determinism_ok, determinism_sigs = check_determinism(
                current, self.suite, self.executor, split="val", repeats=2,
                max_output_chars=self.config.limits.max_case_output_chars,
            )
        except Exception:  # pragma: no cover - nao deve falhar; nao inventamos resultado
            determinism_ok, determinism_sigs = None, ()

        # Se o holdout confirmar, finaliza; se nao, NAO mentimos: registramos a divergencia.
        if holdout_baseline is not None and holdout_final is not None:
            delta_val = final_val.mean_score - baseline_val.mean_score
            delta_hold = holdout_final.mean_score - holdout_baseline.mean_score
            if delta_val > 0 and delta_hold <= 0:
                stopped_reason += (
                    f" | AVISO: o ganho nao se replicou no holdout "
                    f"(val {delta_val:+.4f} vs holdout {delta_hold:+.4f}) -> possivel overfit de validacao"
                )
                self.memory.record_error(
                    experiment_id, None, "metodologia",
                    f"ganho nao replicado no holdout: val={delta_val:+.4f} holdout={delta_hold:+.4f}",
                )

        self.memory.finish_experiment(
            experiment_id,
            status="interrupted" if budget_exhausted else "finished",
            notes=stopped_reason if budget_exhausted else "",
        )
        if self.audit is not None:
            self.audit.record(
                "run_end",
                {
                    "experiment_id": experiment_id,
                    "stopped_reason": stopped_reason,
                    "active_sha": active_sha[:12],
                    "final_val": round(final_val.mean_score, 6),
                    "ledger": self.ledger.snapshot(),
                },
            )

        return OptimizationRun(
            experiment_id=experiment_id,
            name=name,
            seed_artifact=seed_artifact,
            final_artifact=current,
            iterations=iterations,
            baseline_val=baseline_val,
            baseline_train=baseline_train,
            final_val=final_val,
            final_train=final_train,
            holdout_baseline=holdout_baseline,
            holdout_final=holdout_final,
            stopped_reason=stopped_reason,
            ledger_snapshot=self.ledger.snapshot(),
            determinism_ok=determinism_ok,
            determinism_signatures=tuple(determinism_sigs),
            proposer_coverage=tuple(sorted(set(proposal_ops))),
            context=context,
        )


def load_seed_prompt(path: str | Path | None = None) -> PromptArtifact:
    """Carrega o prompt original de um arquivo, ou usa o template minimo.

    O texto carregado e tratado como DADO: e preservado byte a byte como
    artefato semente e nunca reinterpretado como instrucao para o sistema.
    """
    from .safety import UntrustedContent

    if path is None:
        from .propose import empty_prompt_template

        return empty_prompt_template()
    p = Path(path)
    if not p.exists():
        raise UaaoError(f"prompt semente nao encontrado: {p}")
    untrusted = UntrustedContent.wrap(p.read_text(encoding="utf-8"), source=str(p))
    return PromptArtifact(
        text=untrusted.text, origin="seed",
        notes=f"prompt original preservado de {p.name}"
        + (" [ATENCAO: padroes de injecao detectados no texto]" if untrusted.is_suspicious else ""),
    )


__all__ = ["Optimizer", "OptimizationRun", "CycleIteration", "CandidateOutcome", "load_seed_prompt"]
