"""Configuracao de limites, custos, tentativas e permissoes.

Ordem de precedencia (a ultima NAO consegue afrouxar a primeira):

    defaults  <  arquivo JSON  <  variaveis de ambiente UAAO_*

A ``SafetyPolicy`` (rede, escrita externa, auto-modificacao) **nao** e
configuravel: mora em ``uaao.safety`` e e imutavel. Este modulo apenas le a
politica e recusa qualquer chave que tente altera-la.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Mapping

from .errors import ConfigError, SafetyViolation
from .safety import SafetyPolicy

ENV_PREFIX = "UAAO_"

# Chaves que tentariam afrouxar a seguranca. Rejeitadas explicitamente.
FORBIDDEN_KEYS = {
    "allow_network",
    "allow_external_write",
    "allow_self_modification",
    "allow_code_execution",
    "allow_subprocess",
    "safety_policy",
    "permissions",
    "disable_safety",
    "bypass_guardrails",
    "trust_all_content",
}


@dataclass
class Limits:
    """Tetos duros de execucao."""

    max_iterations: int = 5
    max_candidates_per_iteration: int = 6
    max_metric_calls: int = 5000
    max_retries: int = 3
    max_wall_seconds: float = 900.0
    max_case_output_chars: int = 4000


@dataclass
class CostModel:
    """Modelo de custo para que o limite ja exista *antes* de plugar uma API.

    Em modo deterministico o custo real e R$ 0. Os campos abaixo permitem
    simular o custo de uma futura integracao de LLM e validar o teto
    (``max_cost_units``) de forma testavel hoje.
    """

    max_cost_units: float = 100.0
    # custo por chamada de metrica, em "unidades de custo" (adimensional)
    cost_per_metric_call: float = 0.0
    # referencia informativa (nao usada para cobranca automatica)
    reference_usd_per_1k_calls: float = 0.0


@dataclass
class SelectionCriteria:
    """Criterios de aceitacao e protecao contra regressao."""

    # ganho minimo no conjunto de VALIDACAO para aceitar automaticamente
    min_improvement: float = 0.02
    # tolerancia de queda por caso individual (regressao pontual permitida)
    per_case_regression_tolerance: float = 0.0
    # nenhum caso marcado critical=True pode falhar
    block_on_critical_regression: bool = True
    # exige que o ganho seja estatisticamente sustentavel (teste de sinais)
    require_significance: bool = True
    significance_alpha: float = 0.05
    # Poder estatistico: o teste de sinais exato so tem resolucao util quando ha
    # pares suficientes. Com n pares decididos, o menor p bicaudal possivel e
    # 2*(1/2^n). Para n<6 e IMPOSSIVEL atingir p<0.05, e para n<8 a decisao fica
    # dominada por 1-2 casos. Abaixo deste limiar o teste vira "nao avaliado"
    # (registrado como tal, nunca como aprovacao) e a decisao passa a depender
    # da margem de ganho + nao-regressao + guarda de casos criticos.
    # Este limiar existe para nao transformar falta de poder em rejeicao falsa.
    min_decided_pairs: int = 8
    # exige que QUALQUER metrica (grader) nao caia mais que isto
    max_metric_regression: float = 0.0
    # fracao minima de casos que precisam melhorar (evita ganho de 1 caso so)
    min_improved_fraction: float = 0.0
    # protege o holdout: nunca usado para selecionar
    use_holdout_for_selection: bool = False


@dataclass
class Config:
    """Configuracao completa, com caminhos resolvidos."""

    limits: Limits = field(default_factory=Limits)
    costs: CostModel = field(default_factory=CostModel)
    selection: SelectionCriteria = field(default_factory=SelectionCriteria)
    db_path: str = "uaao_memory.sqlite3"
    reports_dir: str = "reports"
    audit_path: str = "audit/audit.jsonl"
    default_executor: str = "policy_reference_v1"
    random_seed: int = 1729
    # allowlist de executores/adaptadores habilitados (principio do menor privilegio)
    enabled_executors: list[str] = field(default_factory=lambda: ["policy_reference_v1"])
    metadata: dict[str, Any] = field(default_factory=dict)

    # -- politica imutavel (nao configuravel) ------------------------------
    @property
    def safety(self) -> SafetyPolicy:
        return SafetyPolicy.hardened()

    # -- carregamento ------------------------------------------------------
    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        data: dict[str, Any] = {}
        if path is not None:
            p = Path(path)
            if not p.exists():
                raise ConfigError(f"Arquivo de configuracao nao encontrado: {p}")
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ConfigError(f"JSON invalido em {p}: {exc}") from exc
            if not isinstance(data, dict):
                raise ConfigError("Configuracao deve ser um objeto JSON.")
        data = cls._merge_env(data)
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Config":
        cls._reject_forbidden(data)
        cfg = cls()
        for key, value in data.items():
            if key in ("limits", "costs", "selection"):
                cls._merge_section(cfg, key, value)
            elif hasattr(cfg, key):
                setattr(cfg, key, value)
            else:
                raise ConfigError(
                    f"Chave de configuracao desconhecida: {key!r}. "
                    "Erro proposital: nao aceitamos campos silenciosos."
                )
        cfg.validate()
        return cfg

    @staticmethod
    def _merge_section(cfg: "Config", name: str, value: Any) -> None:
        if not isinstance(value, Mapping):
            raise ConfigError(f"'{name}' deve ser um objeto.")
        section = getattr(cfg, name)
        valid = {f.name for f in fields(section)}
        for k, v in value.items():
            if k not in valid:
                raise ConfigError(f"Chave desconhecida em '{name}': {k!r}")
            setattr(section, k, v)

    @staticmethod
    def _reject_forbidden(data: Mapping[str, Any], _path: str = "") -> None:
        for key, value in data.items():
            here = f"{_path}.{key}" if _path else str(key)
            if key in FORBIDDEN_KEYS:
                raise SafetyViolation(
                    f"Configuracao '{here}' tenta alterar controles de seguranca. "
                    "Recusado: o sistema nao pode afrouxar as proprias guardas."
                )
            if isinstance(value, Mapping):
                Config._reject_forbidden(value, here)

    @classmethod
    def _merge_env(cls, data: Mapping[str, Any]) -> dict[str, Any]:
        """Aplica ``UAAO_LIMITS__MAX_ITERATIONS=3`` por cima do arquivo."""
        out: dict[str, Any] = dict(data)
        for env_key, raw in os.environ.items():
            if not env_key.startswith(ENV_PREFIX):
                continue
            path = env_key[len(ENV_PREFIX) :].lower()
            if path in {k.lower() for k in FORBIDDEN_KEYS}:
                raise SafetyViolation(
                    f"Variavel de ambiente {env_key} tenta alterar controles de seguranca."
                )
            parts = [p for p in path.split("__") if p]
            if len(parts) == 2 and parts[0] in ("limits", "costs", "selection"):
                section = dict(out.get(parts[0]) or {})
                section[parts[1]] = cls._coerce(raw)
                out[parts[0]] = section
            elif len(parts) == 1:
                out[parts[0]] = cls._coerce(raw)
        return out

    @staticmethod
    def _coerce(raw: str) -> Any:
        lowered = raw.strip().lower()
        if lowered in ("true", "false"):
            return lowered == "true"
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        if raw.strip().startswith("[") or raw.strip().startswith("{"):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        return raw

    # -- validacao ---------------------------------------------------------
    def validate(self) -> None:
        if self.limits.max_iterations < 1:
            raise ConfigError("limits.max_iterations deve ser >= 1")
        if self.limits.max_metric_calls < 1:
            raise ConfigError("limits.max_metric_calls deve ser >= 1")
        if self.limits.max_candidates_per_iteration < 1:
            raise ConfigError("limits.max_candidates_per_iteration deve ser >= 1")
        if self.limits.max_wall_seconds <= 0:
            raise ConfigError("limits.max_wall_seconds deve ser > 0")
        if self.costs.max_cost_units < 0:
            raise ConfigError("costs.max_cost_units deve ser >= 0")
        if self.selection.min_improvement < 0:
            raise ConfigError("selection.min_improvement deve ser >= 0")
        if not (0 < self.selection.significance_alpha < 1):
            raise ConfigError("selection.significance_alpha deve estar em (0,1)")
        if self.selection.use_holdout_for_selection:
            raise ConfigError(
                "selection.use_holdout_for_selection=True invalida a metodologia: "
                "o holdout existe para confirmacao final, nao para selecao."
            )
        if not self.enabled_executors:
            raise ConfigError("enabled_executors nao pode ser vazio")

    # -- utilitarios -------------------------------------------------------
    def ledger(self) -> "Any":
        from .safety import BudgetLedger

        return BudgetLedger(
            max_metric_calls=self.limits.max_metric_calls,
            max_retries=self.limits.max_retries,
            max_wall_seconds=self.limits.max_wall_seconds,
            max_cost_units=self.costs.max_cost_units,
            cost_per_call=self.costs.cost_per_metric_call,
        )

    def resolved(self, base: str | Path) -> "Config":
        """Devolve copia com caminhos resolvidos relativos a ``base``."""
        import copy

        base = Path(base)
        cfg = copy.deepcopy(self)
        cfg.db_path = str((base / self.db_path).resolve())
        cfg.reports_dir = str((base / self.reports_dir).resolve())
        cfg.audit_path = str((base / self.audit_path).resolve())
        return cfg

    def to_json(self) -> dict[str, Any]:
        return {
            "limits": self.limits.__dict__,
            "costs": self.costs.__dict__,
            "selection": self.selection.__dict__,
            "db_path": self.db_path,
            "reports_dir": self.reports_dir,
            "audit_path": self.audit_path,
            "default_executor": self.default_executor,
            "random_seed": self.random_seed,
            "enabled_executors": list(self.enabled_executors),
            "safety_policy_fingerprint": self.safety.fingerprint(),
        }


__all__ = ["Config", "Limits", "CostModel", "SelectionCriteria", "FORBIDDEN_KEYS"]
