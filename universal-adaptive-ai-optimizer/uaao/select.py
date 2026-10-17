"""Modulo 5 - Selecao com protecao contra regressoes.

Politica (todos os criterios precisam passar; o candidato e ACUSADO, nao aceito
por media):

  1. NENHUM caso critical=True pode falhar no candidato.
  2. Melhoria media no conjunto de VALIDACAO >= ``min_improvement``.
  3. Nenhuma metrica (grader) pode cair mais que ``max_metric_regression``.
  4. Nenhum caso pode cair mais que ``per_case_regression_tolerance``.
  5. Se ``require_significance``: teste de sinais com p < alpha E media > 0.
  6. Fracao de casos melhorados >= ``min_improved_fraction``.

Se qualquer criterio falhar, o candidato e rejeitado com MOTIVO EXPLICITO, e o
motivo e gravado na memoria. Rejeitar e a acao padrao: aceitar exige evidencia.
"""

from __future__ import annotations

from typing import Any

from .compare import Comparison, is_improvement_significant, regression_evidence
from .config import SelectionCriteria
from .types import Decision, EvalResult


def check_critical(findings: list[str], baseline: EvalResult, candidate: EvalResult, crit: SelectionCriteria) -> dict[str, Any]:
    """Criterio 1: nenhuma falha critica nova."""
    base_fail = set(baseline.critical_failures())
    cand_fail = set(candidate.critical_failures())
    new_fail = sorted(cand_fail - base_fail)
    # So vira FINDING (bloqueante) quando o criterio esta ativo. Se o usuario
    # desativou explicitamente a guarda, a informacao fica no checks_json para
    # auditoria, mas nao impede a aceitacao -- antes disto, desativar o criterio
    # era inutil porque o finding era adicionado de qualquer forma.
    if crit.block_on_critical_regression and new_fail:
        findings.append(
            f"{len(new_fail)} caso(s) critico(s) passaram a falhar: {', '.join(new_fail[:5])}"
        )
    return {
        "critical_before": sorted(base_fail),
        "critical_after": sorted(cand_fail),
        "new_critical_failures": new_fail,
        "blocking": bool(crit.block_on_critical_regression and new_fail),
    }


def check_improvement(findings: list[str], comp: Comparison, crit: SelectionCriteria) -> dict[str, Any]:
    """Criterio 2: ganho medio minimo na validacao."""
    ok = comp.mean_delta >= crit.min_improvement
    if not ok:
        findings.append(
            f"ganho medio {comp.mean_delta:+.4f} abaixo do minimo exigido "
            f"{crit.min_improvement:+.4f}"
        )
    return {"mean_delta": comp.mean_delta, "min_improvement": crit.min_improvement, "ok": ok}


def check_metric_regression(findings: list[str], comp: Comparison, crit: SelectionCriteria) -> dict[str, Any]:
    """Criterio 3: nenhuma metrica pode despencar."""
    deltas = comp.metric_deltas()
    bad = {k: v for k, v in deltas.items() if v < -abs(crit.max_metric_regression) - 1e-12}
    if bad:
        findings.append(
            "metrica(s) com regressao: "
            + ", ".join(f"{k} {v:+.4f}" for k, v in sorted(bad.items()))
        )
    return {"metric_deltas": deltas, "violations": bad, "ok": not bad}


def check_per_case_regression(findings: list[str], comp: Comparison, crit: SelectionCriteria) -> dict[str, Any]:
    """Criterio 4: nenhum caso individual pode cair alem da tolerancia."""
    tol = abs(crit.per_case_regression_tolerance)
    worst = min((d.delta for d in comp.deltas), default=0.0)
    offenders = [d for d in comp.deltas if d.delta < -tol - 1e-12]
    if offenders:
        findings.append(
            f"{len(offenders)} caso(s) regrediram alem da tolerancia {tol:g} "
            f"(pior: {worst:+.4f})"
        )
    return {
        "worst_case_delta": round(worst, 6),
        "tolerance": tol,
        "offenders": [d.case_id for d in offenders][:10],
        "ok": not offenders,
    }


def check_significance(findings: list[str], comp: Comparison, crit: SelectionCriteria) -> dict[str, Any]:
    """Criterio 5: evidencia estatistica de ganho (teste de sinais exato).

    Guarda de PODER ESTATISTICO: com ``decided`` pares nao empatados, o menor p
    bicaudal alcancavel e ``2 * 0.5**decided``. Se nem o melhor caso possivel
    atinge alpha, o teste nao pode decidir nada -- e rejeitar por causa disso
    seria confundir "sem evidencia" com "sem poder". Nessa situacao o criterio
    e marcado como NAO AVALIADO (transparente no relatorio) e a decisao fica com
    os criterios de margem, nao-regressao e casos criticos.
    """
    decided = len(comp.improved) + len(comp.regressed)
    base = {
        "required": bool(crit.require_significance),
        "decided_pairs": decided,
        "min_decided_pairs": crit.min_decided_pairs,
        "sign_test_p": round(comp.sign_test_p, 6),
        "alpha": crit.significance_alpha,
        "bootstrap_ci95": [round(x, 6) for x in comp.bootstrap_ci],
    }

    if not crit.require_significance:
        return {**base, "status": "desativado", "ok": True}

    if decided == 0:
        findings.append(
            "nenhum par decidiu na validacao: sem evidencia alguma de mudanca "
            "(o candidato e equivalente ao ativo)"
        )
        return {**base, "status": "sem_pares_decididos", "ok": False}

    if decided < crit.min_decided_pairs:
        best_possible_p = 2.0 * (0.5 ** decided)
        note = (
            f"poder estatistico insuficiente: apenas {decided} par(es) decidido(s); "
            f"o menor p possivel seria {best_possible_p:.4f}. Decisao tomada por margem "
            "+ nao-regressao + guarda de casos criticos."
        )
        return {
            **base,
            "status": "nao_avaliado_poder_insuficiente",
            "best_possible_p": round(best_possible_p, 6),
            "ok": True,
            "note": note,
        }

    ok = is_improvement_significant(comp, alpha=crit.significance_alpha)
    if not ok:
        findings.append(
            f"sem evidencia estatistica: p={comp.sign_test_p:.4f} "
            f"(alpha={crit.significance_alpha}, {decided} pares decididos), "
            f"media {comp.mean_delta:+.4f}"
        )
    return {**base, "status": "avaliado", "ok": ok}


def check_improved_fraction(findings: list[str], comp: Comparison, crit: SelectionCriteria) -> dict[str, Any]:
    """Criterio 6: exige amplitude da melhoria, nao so a media."""
    n = len(comp.deltas) or 1
    frac = len(comp.improved) / n
    ok = frac >= crit.min_improved_fraction
    if not ok:
        findings.append(
            f"fracao de casos melhorados {frac:.2%} abaixo do minimo "
            f"{crit.min_improved_fraction:.2%}"
        )
    return {"improved_fraction": round(frac, 6), "min": crit.min_improved_fraction, "ok": ok}


def accept_candidate(
    baseline: EvalResult,
    candidate: EvalResult,
    comp: Comparison,
    criteria: SelectionCriteria,
) -> Decision:
    """Aplica todos os criterios. Retorna uma ``Decision`` auditavel."""
    findings: list[str] = []
    checks: dict[str, Any] = {}
    checks["critical"] = check_critical(findings, baseline, candidate, criteria)
    checks["improvement"] = check_improvement(findings, comp, criteria)

    # Curto-circuito: falha critica e bloqueante por definicao.
    if checks["critical"]["blocking"]:
        return Decision(
            accepted=False,
            reason="BLOQUEADO: falha em caso critico -> " + "; ".join(findings),
            checks={
                **checks,
                "regression_evidence": regression_evidence(comp),
                "policy": "critical_block",
            },
        )

    checks["metric_regression"] = check_metric_regression(findings, comp, criteria)
    checks["per_case_regression"] = check_per_case_regression(findings, comp, criteria)
    checks["significance"] = check_significance(findings, comp, criteria)
    checks["improved_fraction"] = check_improved_fraction(findings, comp, criteria)

    accepted = not findings
    reason = (
        f"ACEITO: ganho medio {comp.mean_delta:+.4f} em '{comp.split}' "
        f"(p={comp.sign_test_p:.4f}, {len(comp.improved)} melhoram / {len(comp.regressed)} pioram)"
        if accepted
        else "REJEITADO: " + "; ".join(findings)
    )
    checks["regression_evidence"] = regression_evidence(comp)
    return Decision(accepted=accepted, reason=reason, checks=checks)


def explain_criteria(criteria: SelectionCriteria) -> list[str]:
    """Texto humano dos criterios vigentes (vai para o relatorio)."""
    return [
        f"melhoria media minima na validacao: {criteria.min_improvement:+.4f}",
        f"falha critica bloqueia: {'sim' if criteria.block_on_critical_regression else 'NAO'}",
        f"regressao maxima por metrica: {criteria.max_metric_regression:g}",
        f"tolerancia de regressao por caso: {criteria.per_case_regression_tolerance:g}",
        f"exige significancia (alpha={criteria.significance_alpha}): "
        f"{'sim' if criteria.require_significance else 'NAO'}",
        f"minimo de pares decididos para o teste de sinais valer: {criteria.min_decided_pairs} "
        "(abaixo disso o criterio vira 'nao avaliado' por falta de poder estatistico, "
        "e a decisao fica com margem + nao-regressao + guarda critica)",
        f"fracao minima de casos melhorados: {criteria.min_improved_fraction:.0%}",
        f"holdout usado para selecao: {'SIM (invalido)' if criteria.use_holdout_for_selection else 'nao'}",
    ]


__all__ = [
    "accept_candidate",
    "check_critical",
    "check_improvement",
    "check_metric_regression",
    "check_per_case_regression",
    "check_significance",
    "check_improved_fraction",
    "explain_criteria",
]
