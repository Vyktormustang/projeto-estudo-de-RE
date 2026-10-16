"""Hierarquia de excecoes do UA AO.

Regra: toda falha esperada tem um tipo proprio, para que o loop de otimizacao
possa distingir "erro do candidato" (vira dado de diagnostico) de "erro do
sistema" (aborta o experimento com seguranca).
"""

from __future__ import annotations


class UaaoError(Exception):
    """Base de todas as excecoes do projeto."""


# --------------------------------------------------------------------------
# Erros de infraestrutura / configuracao -> abortam o experimento
# --------------------------------------------------------------------------
class ConfigError(UaaoError):
    """Configuracao ausente, malformada ou insegura."""


class SafetyViolation(UaaoError):
    """Uma guarda de seguranca foi acionada.

    Nunca deve ser capturada silenciosamente: indica tentativa de operacao
    proibida (rede, escrita externa, auto-modificacao, vazamento de segredo).
    """


class BudgetExceeded(UaaoError):
    """Teto de chamadas, tentativas, custo ou tempo foi atingido."""

    def __init__(self, kind: str, limit: float, used: float) -> None:
        self.kind, self.limit, self.used = kind, limit, used
        super().__init__(
            f"Orcamento '{kind}' esgotado: usado={used:g} limite={limit:g}"
        )


class PermissionDenied(SafetyViolation):
    """Operacao nao autorizada pela politica de permissoes vigente."""


# --------------------------------------------------------------------------
# Erros de dados / execucao -> viram resultado de avaliacao (score 0)
# --------------------------------------------------------------------------
class TaskError(UaaoError):
    """Erro ao carregar/validar uma suite de tarefas."""


class ExecutorError(UaaoError):
    """Falha do executor ao processar um caso. Contabilizada, nao fatal."""


class GraderError(UaaoError):
    """Falha do avaliador (grader) de um caso. Contabilizada, nao fatal."""


class RegistryError(UaaoError):
    """Adapter/executor solicitado nao existe ou nao esta disponivel."""


class MemoryError_(UaaoError):
    """Falha de persistencia (SQLite) ou integridade da memoria."""
