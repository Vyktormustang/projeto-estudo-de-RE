"""Carregamento e validacao de suites de tarefas (JSON).

Todo conteudo de suite e **dado nao confiavel**: pode vir de um repositorio, de
um arquivo recebido ou de um Drive compartilhado. Portanto:

  * nao ha ``import``/``eval``/deserializacao de objetos Python -- apenas JSON;
  * cada texto passa por ``UntrustedContent`` (truncagem, limpeza de controle,
    deteccao de padroes de injecao) e o resultado e **reportado**, nao obedecido;
  * a suite e validada contra um esquema e *pinada por hash* para que o
    experimento registre exatamente qual conjunto foi usado.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .errors import TaskError
from .graders import GRADERS
from .safety import UntrustedContent
from .types import SPLITS, TaskCase, TaskSuite


@dataclass
class SuiteLoadReport:
    """Resultado da inspecao de confiabilidade da suite."""

    path: str
    cases: int = 0
    warnings: list[str] = field(default_factory=list)
    injection_flags: list[dict[str, Any]] = field(default_factory=list)
    truncated: list[str] = field(default_factory=list)
    split_counts: dict[str, int] = field(default_factory=dict)

    @property
    def suspicious(self) -> bool:
        return bool(self.injection_flags) or bool(self.warnings)

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "cases": self.cases,
            "warnings": self.warnings,
            "injection_patterns_detected": len(self.injection_flags),
            "injection_flags": self.injection_flags[:20],
            "truncated_inputs": self.truncated,
            "split_counts": self.split_counts,
        }


_REQUIRED_CASE_FIELDS = ("id", "input", "expected", "grader")


def load_suite(path: str | Path, max_untrusted_chars: int = 20_000) -> tuple[TaskSuite, SuiteLoadReport]:
    """Carrega um arquivo JSON de suite e devolve (suite, relatorio)."""
    p = Path(path)
    if not p.exists():
        raise TaskError(f"Suite nao encontrada: {p}")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TaskError(f"JSON invalido em {p}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise TaskError("Suite deve ser um objeto JSON com 'suite_id', 'version' e 'cases'.")
    return build_suite(raw, source=str(p), max_untrusted_chars=max_untrusted_chars)


def build_suite(
    raw: Mapping[str, Any], source: str = "<memory>", max_untrusted_chars: int = 20_000
) -> tuple[TaskSuite, SuiteLoadReport]:
    """Constroi a suite a partir de um mapeamento, validando campo a campo."""
    report = SuiteLoadReport(path=source)

    suite_id = str(raw.get("suite_id") or "").strip()
    version = str(raw.get("version") or "").strip()
    if not suite_id:
        raise TaskError(f"{source}: 'suite_id' obrigatorio")
    if not version:
        raise TaskError(f"{source}: 'version' obrigatorio")

    raw_cases = raw.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise TaskError(f"{source}: 'cases' deve ser uma lista nao vazia")

    cases: list[TaskCase] = []
    seen: set[str] = set()

    for idx, rc in enumerate(raw_cases):
        where = f"{source}[cases][{idx}]"
        if not isinstance(rc, Mapping):
            raise TaskError(f"{where}: cada caso deve ser um objeto")
        for fieldname in _REQUIRED_CASE_FIELDS:
            if fieldname not in rc:
                raise TaskError(f"{where}: campo obrigatorio ausente: {fieldname!r}")
        case_id = str(rc["id"]).strip()
        if not case_id:
            raise TaskError(f"{where}: 'id' vazio")
        if case_id in seen:
            raise TaskError(f"{where}: id duplicado {case_id!r} (ids devem ser unicos)")
        seen.add(case_id)

        grader = str(rc["grader"]).strip()
        if grader not in GRADERS:
            raise TaskError(
                f"{where}: grader desconhecido {grader!r}. Disponiveis: {sorted(GRADERS)}"
            )

        tags = tuple(str(t) for t in (rc.get("tags") or ()))
        splits = [s for s in SPLITS if f"split:{s}" in tags]
        if len(splits) != 1:
            raise TaskError(
                f"{where}: o caso precisa de exatamente uma tag 'split:<{'|'.join(SPLITS)}', "
                f"encontrado {splits or 'nenhuma'}"
            )

        # --- tratamento de conteudo nao confiavel --------------------------
        untrusted = UntrustedContent.wrap(
            str(rc["input"]), source=f"{source}#{case_id}", max_chars=max_untrusted_chars
        )
        if untrusted.is_suspicious:
            report.injection_flags.append(
                {
                    "case_id": case_id,
                    "source": untrusted.source,
                    "patterns": list(untrusted.injection_suspected),
                    "action": "tratado como dado; o executor decide pela politica do prompt",
                }
            )
        if untrusted.truncated:
            report.truncated.append(case_id)

        weight = float(rc.get("weight", 1.0))
        if weight <= 0:
            raise TaskError(f"{where}: 'weight' deve ser > 0 (recebido {weight})")

        cases.append(
            TaskCase(
                case_id=case_id,
                input=untrusted.text,
                expected=rc["expected"],
                grader=grader,
                params=dict(rc.get("params") or {}),
                tags=tags,
                critical=bool(rc.get("critical", False)),
                weight=weight,
                note=str(rc.get("note") or ""),
            )
        )

    metric_weights = raw.get("metric_weights") or {}
    if not isinstance(metric_weights, Mapping):
        raise TaskError(f"{source}: 'metric_weights' deve ser um objeto")

    suite = TaskSuite(
        suite_id=suite_id,
        version=version,
        cases=tuple(cases),
        description=str(raw.get("description") or ""),
        metric_weights={str(k): float(v) for k, v in metric_weights.items()},
    )

    report.cases = len(cases)
    report.split_counts = {s: len(suite.by_split(s)) for s in SPLITS}

    # --- avisos metodologicos ---------------------------------------------
    for split in ("train", "val"):
        if report.split_counts.get(split, 0) == 0:
            report.warnings.append(
                f"divisao '{split}' vazia: o ciclo de otimizacao precisa de dados "
                f"de '{'treino' if split=='train' else 'validacao'}'."
            )
    if report.split_counts.get("holdout", 0) == 0:
        report.warnings.append("sem 'holdout': nao havera confirmacao final independente.")
    if not any(c.critical for c in cases):
        report.warnings.append(
            "nenhum caso marcado critical=True: a protecao contra regressao fica mais fraca."
        )
    unseen = {c.grader for c in cases} - set(GRADERS)
    if unseen:  # pragma: no cover - ja validado por caso
        report.warnings.append(f"graders sem implementacao: {sorted(unseen)}")

    return suite, report


def validate_suite(suite: TaskSuite) -> list[str]:
    """Checagens de sanidade que nao impedem a carga, mas afetam a conclusao."""
    problems: list[str] = []
    ids = [c.case_id for c in suite.cases]
    if len(ids) != len(set(ids)):
        problems.append("ids duplicados")
    for split in ("train", "val"):
        if not suite.by_split(split):
            problems.append(f"divisao '{split}' vazia")
    for c in suite.cases:
        if c.grader not in GRADERS:
            problems.append(f"{c.case_id}: grader inexistente {c.grader}")
    return problems


def save_suite(suite: TaskSuite, path: str | Path) -> Path:
    """Persiste a suite em JSON (formato identico ao de entrada)."""
    payload = {
        "suite_id": suite.suite_id,
        "version": suite.version,
        "description": suite.description,
        "metric_weights": dict(suite.metric_weights),
        "cases": [
            {
                "id": c.case_id,
                "input": c.input,
                "expected": c.expected,
                "grader": c.grader,
                "params": dict(c.params),
                "tags": list(c.tags),
                "critical": c.critical,
                "weight": c.weight,
                "note": c.note,
            }
            for c in suite.cases
        ],
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def suites_dir() -> Path:
    return Path(__file__).resolve().parent / "suites"


def list_builtin_suites() -> list[Path]:
    return sorted(suites_dir().glob("*.json"))


def load_all_builtin(max_untrusted_chars: int = 20_000) -> list[tuple[TaskSuite, SuiteLoadReport]]:
    out = []
    for path in list_builtin_suites():
        out.append(load_suite(path, max_untrusted_chars=max_untrusted_chars))
    return out


def merge_suites(suites: Iterable[TaskSuite], suite_id: str, version: str) -> TaskSuite:
    """Concatena suites num unico conjunto (usado pelo runner multi-suite)."""
    cases: list[TaskCase] = []
    seen: set[str] = set()
    weights: dict[str, float] = {}
    for s in suites:
        for c in s.cases:
            key = f"{s.suite_id}:{c.case_id}"
            if key in seen:
                raise TaskError(f"id duplicado apos merge: {key}")
            seen.add(key)
            cases.append(
                TaskCase(
                    case_id=key,
                    input=c.input,
                    expected=c.expected,
                    grader=c.grader,
                    params=c.params,
                    tags=c.tags,
                    critical=c.critical,
                    weight=c.weight,
                    note=c.note,
                )
            )
        weights.update(s.metric_weights)
    return TaskSuite(
        suite_id=suite_id, version=version, cases=tuple(cases),
        description="merge de " + ", ".join(s.suite_id for s in suites),
        metric_weights=weights,
    )


__all__ = [
    "SuiteLoadReport",
    "load_suite",
    "build_suite",
    "validate_suite",
    "save_suite",
    "suites_dir",
    "list_builtin_suites",
    "load_all_builtin",
    "merge_suites",
]
