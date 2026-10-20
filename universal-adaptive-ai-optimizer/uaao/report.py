"""Modulo 8 - Relatorios de resultados.

Gera:
  * ``<experimento>.md``  - relatorio legivel (humano);
  * ``<experimento>.json``- o mesmo conteudo em dado estruturado (para diffs e
    para backup no Google Drive).

Regra editorial: o relatorio afirma SOMENTE o que foi medido. Toda secao de
numeros cita o comando que reproduz a medicao, e ha uma secao explicita de
limitacoes e de "o que NAO foi executado".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import Config
from .evaluate import metric_table
from .history import History
from .memory import Memory
from .optimizer import OptimizationRun
from .promptspec import directive_diff
from .select import explain_criteria
from .types import EvalResult


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def _delta_arrow(d: float) -> str:
    if d > 1e-9:
        return f"+{d:.4f} ▲"
    if d < -1e-9:
        return f"{d:.4f} ▼"
    return "0.0000 ="


def _split_table(run: OptimizationRun) -> str:
    rows = [
        "| Divisao | Baseline | Final | Delta | Funcao metodologica |",
        "|---|---|---|---|---|",
    ]
    def cell(ev: EvalResult | None) -> str:
        return f"{ev.mean_score:.4f}" if ev else "n/d"

    pairs = [
        ("treino", run.baseline_train, run.final_train, "orienta o diagnostico"),
        ("validacao", run.baseline_val, run.final_val, "DECIDE a selecao"),
        ("holdout", run.holdout_baseline, run.holdout_final, "confirmacao final (nao usado na selecao)"),
    ]
    for name, b, f, role in pairs:
        if b is None and f is None:
            rows.append(f"| {name} | n/d | n/d | n/d | {role} |")
            continue
        delta = (f.mean_score - b.mean_score) if (b and f) else 0.0
        rows.append(f"| {name} | {cell(b)} | {cell(f)} | {_delta_arrow(delta)} | {role} |")
    return "\n".join(rows)


def _metrics_table(baseline: EvalResult, final: EvalResult) -> str:
    b = {r["metric"]: r for r in metric_table(baseline)}
    f = {r["metric"]: r for r in metric_table(final)}
    rows = [
        "| Metrica (grader) | Casos | Baseline | Final | Delta |",
        "|---|---|---|---|---|",
    ]
    for name in sorted(set(b) | set(f)):
        rb, rf = b.get(name), f.get(name)
        sb = rb["mean_score"] if rb else 0.0
        sf = rf["mean_score"] if rf else 0.0
        n = (rf or rb)["cases"]  # type: ignore[index]
        rows.append(f"| `{name}` | {n} | {sb:.4f} | {sf:.4f} | {_delta_arrow(sf - sb)} |")
    return "\n".join(rows)


def _iterations_section(run: OptimizationRun) -> str:
    if not run.iterations:
        return "_Nenhuma iteracao executada._"
    out: list[str] = []
    for it in run.iterations:
        out.append(f"### Iteracao {it.index}")
        out.append("")
        d = it.diagnosis
        out.append(
            f"- **Diagnostico (treino):** {d.passed_cases}/{d.total_cases} casos passam "
            f"(taxa de falha {_pct(d.failure_rate)})."
        )
        if d.clusters:
            out.append("- **Causas identificadas:**")
            for c in d.clusters:
                target = f" → diretiva do grupo `{c.directive_group}`" if c.directive_group else " → _sem acao automatica_"
                out.append(f"  - `{c.kind}`: {c.size} caso(s){target}")
        else:
            out.append("- Sem falhas na treino: nada a corrigir.")
        if d.notes:
            for n in d.notes:
                out.append(f"- _Nota:_ {n}")
        out.append(f"- **Candidatos gerados:** {it.n_proposals}")
        out.append("")
        if it.outcomes:
            out.append("| Candidato | Operador | Score val | Veredito | Motivo |")
            out.append("|---|---|---|---|---|")
            for o in it.outcomes:
                verdict = "ACEITO" if o.accepted else "rejeitado"
                reason = o.decision.reason.replace("|", "/")
                if len(reason) > 220:
                    reason = reason[:217] + "..."
                out.append(
                    f"| `{o.proposal.artifact.sha_short}` | `{o.proposal.operator}` | "
                    f"{o.val_result.mean_score:.4f} | {verdict} | {reason} |"
                )
            out.append("")
            out.append("<details><summary>Justificativa de cada candidato</summary>")
            out.append("")
            for o in it.outcomes:
                out.append(f"- `{o.proposal.artifact.sha_short}` ({o.proposal.operator}): {o.proposal.rationale}")
            out.append("")
            out.append("</details>")
        out.append("")
    return "\n".join(out)


def _decisions_table(memory: Memory, experiment_id: str) -> str:
    decisions = memory.list_decisions(experiment_id)
    if not decisions:
        return "_Nenhuma decisao registrada._"
    rows = [
        "| # | Iter. | Baseline | Candidato | Aceito | Motivo |",
        "|---|---|---|---|---|---|",
    ]
    for i, d in enumerate(decisions, 1):
        reason = str(d["reason"]).replace("|", "/")
        if len(reason) > 160:
            reason = reason[:157] + "..."
        rows.append(
            f"| {i} | {d['iteration']} | `{d['baseline_sha'][:12]}` | "
            f"`{d['candidate_sha'][:12]}` | {'sim' if d['accepted'] else 'nao'} | {reason} |"
        )
    return "\n".join(rows)


def _prompt_diff_section(run: OptimizationRun) -> str:
    changes = directive_diff(run.seed_artifact.text, run.final_artifact.text)
    lines = []
    if not changes:
        lines.append("Nenhuma diretiva mudou (o prompt final e equivalente ao original).")
    else:
        lines.append("| Diretiva | Antes | Depois |")
        lines.append("|---|---|---|")
        for key, (before, after) in sorted(changes.items()):
            lines.append(f"| `{key}` | `{before if before is not None else '(ausente)'}` | `{after if after is not None else '(ausente)'}` |")
    return "\n".join(lines)


def _errors_section(memory: Memory, experiment_id: str) -> str:
    errors = memory.list_errors(experiment_id)
    if not errors:
        return "_Nenhum erro registrado._"
    rows = ["| Iter. | Escopo | Mensagem |", "|---|---|---|"]
    for e in errors:
        msg = str(e["message"]).replace("|", "/")[:200]
        rows.append(f"| {e['iteration']} | `{e['scope']}` | {msg} |")
    return "\n".join(rows)


def build_report_json(
    run: OptimizationRun, suite_id: str, suite_sha: str, config: Config, memory: Memory,
    history: History,
) -> dict[str, Any]:
    return {
        "report_version": 1,
        "experiment_id": run.experiment_id,
        "name": run.name,
        "suite": {"suite_id": suite_id, "sha": suite_sha, "cases": len(run.baseline_val.cases) + 0},
        "executor": run.baseline_val.executor,
        "stopped_reason": run.stopped_reason,
        "scores": {
            "baseline": {
                "train": run.baseline_train.mean_score,
                "val": run.baseline_val.mean_score,
                "holdout": run.holdout_baseline.mean_score if run.holdout_baseline else None,
            },
            "final": {
                "train": run.final_train.mean_score,
                "val": run.final_val.mean_score,
                "holdout": run.holdout_final.mean_score if run.holdout_final else None,
            },
        },
        "run": run.to_json(),
        "criteria": explain_criteria(config.selection),
        "versions": history.summary(run.experiment_id),
        "metrics": {
            "baseline_val": metric_table(run.baseline_val),
            "final_val": metric_table(run.final_val),
        },
        "determinism": {
            "ok": run.determinism_ok,
            "signatures": list(run.determinism_signatures),
        },
        "ledger": run.ledger_snapshot,
        "context": run.context,
        "config": config.to_json(),
        "errors": memory.list_errors(run.experiment_id),
    }


def build_report_markdown(
    run: OptimizationRun, suite_id: str, suite_sha: str, config: Config,
    memory: Memory, history: History, suite_names: list[str] | None = None,
) -> str:
    delta_val = run.final_val.mean_score - run.baseline_val.mean_score
    v = history.summary(run.experiment_id)
    lines: list[str] = []
    a = lines.append

    a(f"# Relatorio de otimizacao — `{run.experiment_id}`")
    a("")
    a(f"- **Experimento:** {run.name}")
    a(f"- **Suite:** `{suite_id}` (sha `{suite_sha[:12]}`, {len(run.baseline_val.cases)} casos na validacao)")
    a(f"- **Executor:** `{run.baseline_val.executor}` (deterministico, offline)")
    a(f"- **Encerramento:** {run.stopped_reason}")
    a(f"- **Prompt original preservado:** `{run.seed_artifact.sha_short}` (imutavel na memoria)")
    a(f"- **Prompt ativo ao final:** `{run.final_artifact.sha_short}`")
    a(f"- **Gerado em:** {run.context.get('timestamp_utc', 'n/d')} | commit `{(run.context.get('git_commit') or 'n/d')[:12]}` | seed `{config.random_seed}`")
    a("")

    a("## 1. Resultado medido")
    a("")
    a("| Metrica | Valor |")
    a("|---|---|")
    a(f"| Score de validacao (baseline) | {run.baseline_val.mean_score:.4f} |")
    a(f"| Score de validacao (final) | {run.final_val.mean_score:.4f} |")
    a(f"| Delta de validacao | {_delta_arrow(delta_val)} |")
    if run.holdout_baseline and run.holdout_final:
        dh = run.holdout_final.mean_score - run.holdout_baseline.mean_score
        a(f"| Delta de holdout (confirmacao) | {_delta_arrow(dh)} |")
    a(f"| Candidatos testados | {run.tested_count()} |")
    a(f"| Candidatos aceitos | {run.accepted_count()} |")
    a(f"| Determinismo verificado | {'sim' if run.determinism_ok else ('nao' if run.determinism_ok is False else 'nao verificado')} |")
    a("")
    if delta_val > 0:
        a(
            f"> O prompt final obteve **{delta_val:+.4f}** de score na validacao "
            f"({_pct(run.baseline_val.mean_score)} → {_pct(run.final_val.mean_score)})."
        )
    elif abs(delta_val) < 1e-9:
        a("> Nao houve mudanca mensuravel de score na validacao: nenhum candidato superou os criterios.")
    else:
        a(f"> ATENCAO: houve PIORA de {delta_val:.4f} — o experimento deve ser tratado como falha de metrica.")
    a("")

    a("## 2. Metodologia aplicada")
    a("")
    a(_split_table(run))
    a("")
    a("Criterios de aceitacao vigentes:")
    a("")
    for c in explain_criteria(config.selection):
        a(f"- {c}")
    a("")

    a("## 3. Mudancas no prompt")
    a("")
    a(_prompt_diff_section(run))
    a("")
    a("<details><summary>Prompt final completo</summary>")
    a("")
    a("```")
    a(run.final_artifact.text.rstrip())
    a("```")
    a("")
    a("</details>")
    a("")
    a("<details><summary>Prompt original (baseline, preservado)</summary>")
    a("")
    a("```")
    a(run.seed_artifact.text.rstrip())
    a("```")
    a("")
    a("</details>")
    a("")

    a("## 4. Metricas por tarefa")
    a("")
    a(_metrics_table(run.baseline_val, run.final_val))
    a("")

    a("## 5. Ciclo iterativo (diagnostico → candidatos → selecao)")
    a("")
    a(_iterations_section(run))
    a("")

    a("## 6. Registro de decisoes (auditoria)")
    a("")
    a(_decisions_table(memory, run.experiment_id))
    a("")

    a("## 7. Erros e intercorrencias")
    a("")
    a(_errors_section(memory, run.experiment_id))
    a("")

    a("## 8. Versoes e reversao")
    a("")
    a(f"- Versoes registradas: **{len(v['versions'])}**")
    a(f"- Decisoes: {v['decisions']['total']} ({v['decisions']['accepted']} aceitas, {v['decisions']['rejected']} rejeitadas)")
    if v["active"]:
        a(f"- Versao ativa: `{v['active'][0]}`")
    a("")
    a("Para reverter a qualquer momento (nada e apagado):")
    a("")
    a("```bash")
    a(f"python -m uaao rollback --experiment {run.experiment_id} --to previous \\")
    a('    --reason "descricao do motivo"')
    a("```")
    a("")

    a("## 9. Orcamento consumido")
    a("")
    a("| Recurso | Usado | Limite |")
    a("|---|---|---|")
    for label, key in (
        ("Chamadas de metrica", "metric_calls"),
        ("Tentativas (retries)", "retries"),
        ("Custo (unidades)", "cost_units"),
    ):
        a(f"| {label} | {run.ledger_snapshot.get(key)} | {run.ledger_snapshot.get('max_' + key)} |")
    a(f"| Tempo de parede (s) | {run.ledger_snapshot.get('elapsed_s')} | {run.ledger_snapshot.get('max_wall_seconds')} |")
    a("")

    a("## 10. Limitacoes e o que NAO foi executado")
    a("")
    a("Esta secao existe para impedir leitura indevida dos numeros acima.")
    a("")
    a("**O que foi medido:** comportamento de um **executor de referencia deterministico**")
    a("(`policy_reference_v1`) que le a politica declarada no prompt e obedece literalmente")
    a("a ela. As metricas (formato, precisao, ambiguidade, honestidade, injecao) sao")
    a("calculadas por graders deterministicos sobre a saida.")
    a("")
    a("**O que NAO foi medido:** desempenho de GPT, Claude, Gemini, Llama ou qualquer LLM.")
    a("Nenhuma chamada de API de modelo foi feita — nao havia chave nem conectividade para")
    a("isso neste ambiente. Portanto estes numeros **nao** autorizam afirmacoes do tipo")
    a('"o prompt melhorou o assistente em X%". A evidencia aqui e: o loop de otimizacao')
    a("encontra mudancas de politica que produzem diferenca mensuravel e reproduzivel de")
    a("comportamento no executor de referencia, sob criterios de aceitacao explicitos.")
    a("")
    a("**Nao executado:**")
    a("- nenhuma avaliacao com juiz LLM (nao ha modelo acessivel);")
    a("- nenhum ajuste de pesos / fine-tuning (fora de escopo e sem GPU);")
    a("- nenhuma escrita em servico externo (politica de seguranca: `allow_external_write=False`);")
    a("- nenhum teste de carga, nem medicao de latencia de API.")
    a("")
    a("**Como reproduzir exatamente estes numeros:**")
    a("")
    a("```bash")
    names = suite_names or [suite_id]
    suites_arg = " ".join(f"--suite {n}" for n in names)
    a(f"python -m uaao run --workdir <copia do diretorio de trabalho> \\")
    a(f"    {suites_arg} \\")
    a(f"    --iterations {config.limits.max_iterations} --seed {config.random_seed}")
    a("```")
    a("")
    a(f"_Assinatura de determinismo da validacao final: `{(run.final_val.signature_short)}`._")
    a("")
    return "\n".join(lines).rstrip() + "\n"


def write_reports(
    run: OptimizationRun, suite_id: str, suite_sha: str, config: Config,
    memory: Memory, history: History, out_dir: str | Path,
    suite_names: list[str] | None = None,
) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / f"{run.experiment_id}.md"
    json_path = out / f"{run.experiment_id}.json"

    md = build_report_markdown(run, suite_id, suite_sha, config, memory, history,
                               suite_names=suite_names)
    payload = build_report_json(run, suite_id, suite_sha, config, memory, history)

    # Redacao final: nada de segredo entra em arquivo, mesmo que apareca em saida.
    from .safety import redact

    md = redact(md)
    payload = redact(payload)

    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    memory.record_report(run.experiment_id, "markdown", str(md_path))
    memory.record_report(run.experiment_id, "json", str(json_path))
    return {"markdown": md_path, "json": json_path}


__all__ = ["build_report_markdown", "build_report_json", "write_reports"]
