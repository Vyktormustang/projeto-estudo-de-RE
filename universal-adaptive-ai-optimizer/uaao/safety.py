"""Camada de seguranca do UA AO.

Principios implementados (cada um com teste correspondente):

1. **Controles de seguranca imutaveis.** ``SafetyPolicy`` e ``frozen=True`` e so
   pode nascer de ``SafetyPolicy.hardened()``. Nenhuma configuracao, arquivo de
   tarefa ou candidato consegue altera-la -- tentativas levantam
   ``SafetyViolation``. (tests/test_safety.py)
2. **Limites de chamadas, tentativas e custo.** ``BudgetLedger`` contabiliza e
   interrompe ao estourar (``BudgetExceeded``).
3. **Trilha de auditoria a prova de adulteracao.** ``AuditLog`` grava JSONL com
   encadeamento de hash: remover/editar uma linha quebra a verificacao.
4. **Redacao de segredos.** Nada entra em log, banco ou relatorio sem passar por
   ``redact``; ha varredura de segredos no repositorio nos testes.
5. **Conteudo nao confiavel.** Todo texto vindo de arquivo/suite/repositorio e
   embrulhado em ``UntrustedContent``: e *dado*, nunca instrucao.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .errors import BudgetExceeded, PermissionDenied, SafetyViolation

# ---------------------------------------------------------------------------
# 1. Politica de seguranca imutavel
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SafetyPolicy:
    """Postura de seguranca do processo. Imutavel por construcao.

    Os campos sao deliberadamente conservadores. O sistema de otimizacao
    (``optimizer``, ``propose``, ``select``) **nao tem referencia a esta classe**
    e portanto nao pode alterar nada aqui: a politica e lida apenas pela camada
    de execucao e pelo CLI.
    """

    allow_network: bool = False
    allow_external_write: bool = False
    allow_self_modification: bool = False
    allow_code_execution: bool = False
    allow_subprocess: bool = False
    max_untrusted_chars: int = 20_000

    def __post_init__(self) -> None:
        # Bloqueia reativacao de capacidades perigosas em tempo de construcao.
        # Isto e a barreira que torna o objeto seguro mesmo se alguem tentar
        # instancia-lo com valores permissivos.
        for flag in (
            "allow_network",
            "allow_external_write",
            "allow_self_modification",
            "allow_code_execution",
            "allow_subprocess",
        ):
            if getattr(self, flag):
                raise SafetyViolation(
                    f"Politica insegura recusada: {flag}=True. "
                    "O UA AO opera offline, sem escrita externa e sem "
                    "auto-modificacao. Para executar acoes externas, use uma "
                    "ferramenta de sessao com aprovacao humana explicita."
                )

    @classmethod
    def hardened(cls) -> "SafetyPolicy":
        """Unica forma suportada de obter a politica."""
        return cls()

    def assert_can(self, operation: str) -> None:
        allowed = {
            "read_local": True,
            "write_local": True,
            "sqlite": True,
            "network": self.allow_network,
            "external_write": self.allow_external_write,
            "self_modification": self.allow_self_modification,
            "code_execution": self.allow_code_execution,
            "subprocess": self.allow_subprocess,
        }
        if operation not in allowed:
            raise PermissionDenied(f"Operacao desconhecida: {operation!r}")
        if not allowed[operation]:
            raise PermissionDenied(
                f"Politica de seguranca proibe '{operation}'. "
                "Nenhuma permissao e concedida automaticamente."
            )

    def fingerprint(self) -> str:
        payload = {
            k: getattr(self, k)
            for k in (
                "allow_network",
                "allow_external_write",
                "allow_self_modification",
                "allow_code_execution",
                "allow_subprocess",
            )
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 2. Orcamentos
# ---------------------------------------------------------------------------
@dataclass
class BudgetLedger:
    """Contabiliza consumo e interrompe ao atingir o teto.

    Tambem acumula *custo potencial*: em modo deterministico o custo real e 0,
    mas o ledger estima quanto custaria se o mesmo numero de chamadas fosse
    feito via API paga (ver ``Config.cost_model``), para que o limite de custo
    ja exista e seja testado antes de qualquer adaptador de LLM ser plugado.
    """

    max_metric_calls: int
    max_retries: int
    max_wall_seconds: float
    max_cost_units: float
    cost_per_call: float = 0.0

    metric_calls: int = 0
    retries: int = 0
    cost_units: float = 0.0
    _t0: float = field(default_factory=time.monotonic, repr=False)
    calls_log: list[dict[str, Any]] = field(default_factory=list, repr=False)

    # -- cobranca ----------------------------------------------------------
    def charge_call(self, label: str, amount: int = 1) -> None:
        if self.metric_calls + amount > self.max_metric_calls:
            raise BudgetExceeded("metric_calls", self.max_metric_calls, self.metric_calls)
        self.metric_calls += amount
        self.cost_units += amount * self.cost_per_call
        if self.cost_units > self.max_cost_units:
            raise BudgetExceeded("cost_units", self.max_cost_units, self.cost_units)
        self.calls_log.append({"label": label, "amount": amount, "t": round(self.elapsed, 3)})

    def charge_retry(self, label: str) -> None:
        if self.retries + 1 > self.max_retries:
            raise BudgetExceeded("retries", self.max_retries, self.retries)
        self.retries += 1
        self.calls_log.append({"label": f"retry:{label}", "amount": 0, "t": round(self.elapsed, 3)})

    def check_wall_clock(self) -> None:
        if self.elapsed > self.max_wall_seconds:
            raise BudgetExceeded("wall_seconds", self.max_wall_seconds, self.elapsed)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._t0

    def snapshot(self) -> dict[str, Any]:
        return {
            "metric_calls": self.metric_calls,
            "max_metric_calls": self.max_metric_calls,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "cost_units": round(self.cost_units, 6),
            "max_cost_units": self.max_cost_units,
            "elapsed_s": round(self.elapsed, 3),
            "max_wall_seconds": self.max_wall_seconds,
        }

    def remaining(self) -> int:
        return max(0, self.max_metric_calls - self.metric_calls)


# ---------------------------------------------------------------------------
# 3. Trilha de auditoria encadeada por hash
# ---------------------------------------------------------------------------
class AuditLog:
    """Log append-only em JSONL com encadeamento ``prev_hash -> hash``.

    Cada registro carrega o hash do anterior, tornando qualquer edicao ou
    remocao detectavel por ``verify()``.
    """

    GENESIS = "0" * 64

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # -- leitura -----------------------------------------------------------
    def _last_hash(self) -> str:
        if not self.path.exists():
            return self.GENESIS
        last = self.GENESIS
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last = json.loads(line)["hash"]
        return last

    @staticmethod
    def _digest(prev: str, payload: Mapping[str, Any]) -> str:
        return hashlib.sha256(
            (prev + json.dumps(payload, sort_keys=True, ensure_ascii=False)).encode("utf-8")
        ).hexdigest()

    # -- escrita -----------------------------------------------------------
    def record(self, event: str, data: Mapping[str, Any] | None = None) -> dict[str, Any]:
        prev = self._last_hash()
        payload = redact(dict(data or {}))
        entry = {
            "seq": self._count(),
            "event": event,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "data": payload,
        }
        entry["prev_hash"] = prev
        entry["hash"] = self._digest(prev, {k: v for k, v in entry.items() if k != "hash"})
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        return entry

    def _count(self) -> int:
        if not self.path.exists():
            return 0
        with self.path.open("r", encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    out.append(json.loads(line))
        return out

    def verify(self) -> tuple[bool, str]:
        """Recalcula a cadeia. Retorna (ok, mensagem)."""
        prev = self.GENESIS
        for i, entry in enumerate(self.entries()):
            body = {k: v for k, v in entry.items() if k != "hash"}
            if entry.get("prev_hash") != prev:
                return False, f"encadeamento quebrado no registro {i} (prev_hash)"
            if self._digest(prev, body) != entry.get("hash"):
                return False, f"conteudo adulterado no registro {i} (hash)"
            prev = entry["hash"]
        return True, f"cadeia integra ({len(self.entries())} registros)"


# ---------------------------------------------------------------------------
# 4. Redacao de segredos
# ---------------------------------------------------------------------------
# Padroes de credenciais que NUNCA podem aparecer em log/DB/relatorio.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsk-[A-Za-z0-9\-_]{16,}\b"),               # OpenAI-style
    re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{16,}\b"),           # Anthropic
    re.compile(r"\bAIza[0-9A-Za-z\-_]{30,}\b"),              # Google API key
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),           # GitHub token
    re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),                  # Hugging Face
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-._~+/]{12,}=*"),
)

# Nomes de variaveis de ambiente cujo *valor* nunca deve ser exposto.
SENSITIVE_ENV_HINTS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def redact(value: Any) -> Any:
    """Substitui segredos por ``[REDACTED]`` recursivamente.

    Aplicado antes de qualquer persistencia (SQLite, JSONL, relatorio).
    """
    if isinstance(value, str):
        out = value
        for pat in _SECRET_PATTERNS:
            out = pat.sub("[REDACTED]", out)
        return out
    if isinstance(value, Mapping):
        return {
            k: ("[REDACTED]" if _is_sensitive_key(str(k)) else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    return value


def _is_sensitive_key(key: str) -> bool:
    up = key.upper()
    return any(hint in up for hint in SENSITIVE_ENV_HINTS)


def scan_for_secrets(text: str) -> list[str]:
    """Retorna descricoes dos segredos encontrados (nunca os valores)."""
    hits = []
    for pat in _SECRET_PATTERNS:
        for m in pat.finditer(text):
            hits.append(f"padrao {pat.pattern[:28]}... em offset {m.start()}")
    return hits


def env_secret_names() -> list[str]:
    """Nomes (nao valores) de variaveis de ambiente sensiveis definidas."""
    return sorted(k for k in os.environ if _is_sensitive_key(k))


# ---------------------------------------------------------------------------
# 5. Conteudo nao confiavel
# ---------------------------------------------------------------------------
# Heuristicas de tentativa de injecao de instrucao em conteudo recuperado.
# Cobre ingles E portugues: o corpus do projeto e pt-BR, e um detector so-ingles
# deixaria passar a maioria das tentativas reais (falha encontrada em teste e
# corrigida aqui). LIMITE CONHECIDO: e uma heuristica lexical -- nao substitui
# um classificador, e ataques parafraseados podem escapar. Ver docs/SECURITY.md.
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    # ingles
    re.compile(r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)"),
    re.compile(r"(?i)\bdisregard\s+(the\s+)?(previous|prior|above|system)"),
    re.compile(r"(?i)\b(you\s+are\s+now|from\s+now\s+on\s+you)\b"),
    re.compile(r"(?i)\b(reveal|print|show|dump)\s+(the\s+)?(system\s*)?(prompt|instructions?|secret|api\s*key)"),
    re.compile(r"(?i)\boverride\s+(the\s+)?(safety|security|guardrails?|policy)"),
    # portugues (o corpus declarado do projeto)
    re.compile(r"(?i)\b(ignore|ignorar|desconsidere|desconsiderar|esqueca|esquecer)\s+"
               r"(as\s+|todas\s+as\s+|o\s+|a\s+|os\s+)?"
               r"(instrucoes|instruções|regras|orientacoes|orientações|diretrizes|ordens|"
               r"tudo|todos|prompt|contexto|comandos)"),
    re.compile(r"(?i)\binstrucoes?\s+(anteriores|acima|previas|do\s+sistema)\b"),
    re.compile(r"(?i)\b(revele|revelar|mostre|mostrar|exponha|expor|imprima|imprimir|liste)\s+"
               r"(o\s+|as\s+|a\s+)?(prompt|instrucoes|instruções|regras|segredo|senha|chave)"),
    re.compile(r"(?i)\b(voce\s+agora\s+e|a\s+partir\s+de\s+agora\s+voce|agora\s+voce\s+e)\b"),
    re.compile(r"(?i)\b(sobrescreva|anule|desative|contorne|burle)\s+(as\s+)?"
               r"(regras|restricoes|restrições|seguranca|segurança|politica|política|guardas)\b"),
    re.compile(r"(?i)\bmodo\s+sem\s+restricoes?\b|\bsem\s+restricoes\b|\bsem\s+filtros?\b"),
    # genericos
    re.compile(r"(?i)\bexfiltrat\w*|\bcurl\s+http"),
    re.compile(r"(?i)<<\s*system\s*>>|\[/?INST\]|<\|im_start\|>"),
)


@dataclass(frozen=True)
class UntrustedContent:
    """Texto de origem externa, explicitamente marcado como DADO.

    Nenhum componente do UA AO interpreta este texto como instrucao. O executor
    deterministico opera sobre o *input do caso* apenas pelo que a politica
    (prompt) permite, e o conteudo e truncado e higienizado antes do uso.
    """

    text: str
    source: str
    truncated: bool = False
    injection_suspected: tuple[str, ...] = ()
    byte_len: int = 0

    @classmethod
    def wrap(cls, text: str, source: str, max_chars: int = 20_000) -> "UntrustedContent":
        raw = text or ""
        # Remove caracteres de controle (exceto \n e \t) que poderiam ofuscar
        # a inspecao humana dos dados.
        cleaned = "".join(
            ch for ch in raw if ch in ("\n", "\t") or ord(ch) >= 32 or ch == "\r"
        )
        truncated = len(cleaned) > max_chars
        cleaned = cleaned[:max_chars]
        hits = tuple(
            m.group(0)[:60] for pat in _INJECTION_PATTERNS for m in pat.finditer(cleaned)
        )
        return cls(
            text=cleaned,
            source=source,
            truncated=truncated,
            injection_suspected=hits,
            byte_len=len(raw.encode("utf-8")),
        )

    @property
    def is_suspicious(self) -> bool:
        return bool(self.injection_suspected)


def wrap_many(
    items: Iterable[tuple[str, str]], max_chars: int = 20_000
) -> list[UntrustedContent]:
    return [
        UntrustedContent.wrap(text, source, max_chars=max_chars)
        for text, source in items
    ]


__all__ = [
    "SafetyPolicy",
    "BudgetLedger",
    "AuditLog",
    "UntrustedContent",
    "redact",
    "scan_for_secrets",
    "env_secret_names",
    "wrap_many",
]
