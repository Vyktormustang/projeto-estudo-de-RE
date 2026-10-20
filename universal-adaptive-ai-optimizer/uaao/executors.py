"""Modulo 9 - Adaptadores de execucao (registry plugavel).

O que e um executor aqui
------------------------
Um executor recebe ``(prompt, caso)`` e devolve a *saida* textual. E a fronteira
unica onde "um modelo" poderia entrar. Nesta versao o registry contem apenas
executores **deterministicos locais** (decisao do usuario: sem LLM). O contrato
``Executor`` esta pronto para receber um adaptador de API/modelo no futuro, mas
nenhum codigo de rede e embarcado -- e a politica de seguranca proibe rede.

Por que um executor de referencia e uma medida honesta
-----------------------------------------------------
``PolicyReferenceExecutor`` e um **modelo de referencia do COMPORTAMENTO**, nao um
LLM. Ele le a politica declarada no prompt e obedece a ela de forma literal.
Portanto:

  * a metrica mede se a POLITICA escrita produz o comportamento exigido pela
    suite (formato, honestidade, ambiguidade, resistencia a injecao);
  * a metrica NAO mede e NAO PRETENDE medir a qualidade de GPT/Claude/Gemini.

Isso torna o loop de otimizacao inteiramente verificavel e reproduzivel, que e o
requisito central do projeto ("testes deterministicos sempre que possivel").
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .errors import ExecutorError, RegistryError
from .graders import safe_eval_arith
from .promptspec import (
    effective_policy,
    extract_prose,
    missing_directives,
    parse_directives,
)
from .safety import SafetyPolicy
from .types import PromptArtifact, TaskCase


@runtime_checkable
class Executor(Protocol):
    """Contrato de execucao. Implementacoes DEVEM declarar determinismo."""

    name: str
    version: str
    deterministic: bool

    def execute(self, prompt: PromptArtifact, case: TaskCase) -> str:  # pragma: no cover
        ...


# --------------------------------------------------------------------------
# Envelope de entrada do caso
# --------------------------------------------------------------------------
def parse_envelope(text: str) -> dict[str, str]:
    """Le o envelope ``chave=valor`` do input do caso.

    Formato deliberadamente simples e legivel. Linhas que nao casam sao
    acumuladas em ``text`` (corpo do pedido).
    """
    env: dict[str, str] = {}
    body: list[str] = []
    for line in (text or "").splitlines():
        m = re.match(r"^\s*([a-z_][a-z0-9_]{0,31})\s*=\s*(.*)$", line)
        if m:
            env[m.group(1)] = m.group(2).strip()
        elif line.strip():
            body.append(line.strip())
    if body:
        env.setdefault("text", " ".join(body))
    return env


@dataclass(frozen=True)
class ExecutorInfo:
    name: str
    version: str
    deterministic: bool
    description: str


class ExecutorRegistry:
    """Registry com allowlist (menor privilegio).

    Somente executores explicitamente habilitados podem ser instanciados. O
    registry nao faz descoberta dinamica de plugins e nao importa codigo de
    terceiros (nao executamos codigo de repositorios sem revisao).
    """

    def __init__(self, enabled: list[str] | None = None) -> None:
        self._factories: dict[str, tuple[ExecutorInfo, type]] = {}
        self._enabled = set(enabled or [])
        self._instances: dict[str, Executor] = {}

    def register(self, info: ExecutorInfo, factory: type) -> None:
        self._factories[info.name] = (info, factory)

    def available(self) -> list[ExecutorInfo]:
        return [i for n, (i, _) in sorted(self._factories.items()) if n in self._enabled]

    def get(self, name: str) -> Executor:
        if name not in self._factories:
            raise RegistryError(
                f"Executor {name!r} nao registrado. Disponiveis: {sorted(self._factories)}"
            )
        if name not in self._enabled:
            raise RegistryError(
                f"Executor {name!r} nao esta habilitado (allowlist). "
                f"Habilitados: {sorted(self._enabled)}. Adicionar exige edicao explicita de config."
            )
        if name not in self._instances:
            info, factory = self._factories[name]
            self._instances[name] = factory()  # type: ignore[call-arg]
        return self._instances[name]


# --------------------------------------------------------------------------
# Executor de referencia deterministico
# --------------------------------------------------------------------------
# Texto "verboso" usado quando MAX_WORDS = unlimited. Existe para tornar a
# concisao uma propriedade *observavel* da politica.
_VERBOSE_TEMPLATE = (
    "Antes de responder, considere o contexto completo do pedido apresentado. "
    "O valor solicitado foi apurado e o resultado obtido consta a seguir. "
    "Vale notar que este texto apenas ilustra o comportamento padrao quando a "
    "politica nao impoe limite de palavras, portanto ele se estende alem do "
    "necessario para demonstrar o efeito mensuravel da diretiva de concisao. "
    "RESULTADO: {value}"
)

# Valores "alucinados" deterministicos: derivados do texto do pedido para que
# a mesma entrada produza sempre a mesma saida (reprodutibilidade exigida).
_FABRICATION_VALUES = ("27 graus celsius", "68% de chance de chuva", "12 km/h de vento")


class PolicyReferenceExecutor:
    """Interpreta a politica declarada no prompt e obedece literalmente.

    Deterministico por construcao: nenhuma fonte de aleatoriedade, nenhum
    relogio, nenhuma rede, nenhum estado entre chamadas.
    """

    name = "policy_reference_v1"
    version = "1.0.0"
    deterministic = True

    def execute(self, prompt: PromptArtifact, case: TaskCase) -> str:
        try:
            return self._execute(prompt, case)
        except ExecutorError:
            raise
        except Exception as exc:  # pragma: no cover - defensivo
            raise ExecutorError(f"falha ao executar caso {case.case_id}: {exc}") from exc

    # -- nucleo ------------------------------------------------------------
    def _execute(self, prompt: PromptArtifact, case: TaskCase) -> str:
        policy = effective_policy(parse_directives(prompt.text))
        env = parse_envelope(case.input)
        kind = env.get("kind", "calc")
        handler = {
            "calc": self._calc,
            "ambiguous": self._ambiguous,
            "missing_tool": self._missing_tool,
            "injection": self._injection,
            "refuse": self._refuse,
            "concise": self._concise,
            "language": self._language,
        }.get(kind)
        if handler is None:
            raise ExecutorError(f"kind desconhecido no caso {case.case_id}: {kind!r}")
        return handler(policy, env, case)

    # -- helpers de politica ----------------------------------------------
    @staticmethod
    def _wants_json(policy: dict[str, str]) -> bool:
        return policy.get("OUTPUT_FORMAT") == "json_object"

    @staticmethod
    def _round_value(policy: dict[str, str], value: float) -> float:
        dec = policy.get("ROUND_DECIMALS", "as_is")
        if dec == "as_is":
            return value
        return round(value, int(dec))

    @staticmethod
    def _format_number(policy: dict[str, str], value: float) -> str:
        dec = policy.get("ROUND_DECIMALS", "as_is")
        if dec == "as_is":
            return repr(value) if value != int(value) else str(int(value))
        return f"{value:.{int(dec)}f}"

    def _emit_calc(
        self, policy: dict[str, str], expr: str, value: float, lang_note: str = ""
    ) -> str:
        rounded = self._round_value(policy, value)
        fmt = self._format_number(policy, rounded)
        if self._wants_json(policy):
            obj: dict[str, object] = {"resultado": rounded}
            if policy.get("INCLUDE_EXPRESSION") == "true":
                obj["expressao"] = expr
            return json.dumps(obj, ensure_ascii=False, sort_keys=True)
        head = "RESULTADO: " if policy.get("MAX_WORDS") != "unlimited" else "O resultado e "
        text = f"{head}{fmt}"
        if policy.get("INCLUDE_EXPRESSION") == "true":
            text += f" (expressao: {expr})"
        return text + (" " + lang_note if lang_note else "")

    # -- handlers por tipo de caso ----------------------------------------
    def _calc(self, policy: dict[str, str], env: dict[str, str], case: TaskCase) -> str:
        expr = env.get("expr", "").strip()
        if not expr:
            raise ExecutorError(f"caso {case.case_id}: 'expr' ausente")
        value = safe_eval_arith(expr)
        return self._emit_calc(policy, expr, value)

    def _ambiguous(self, policy: dict[str, str], env: dict[str, str], case: TaskCase) -> str:
        """Pedido ambiguo: (a) pede esclarecimento, ou (b) adivinha."""
        guess = env.get("guess", "0")
        if policy.get("ON_AMBIGUOUS") == "ask_clarification":
            return (
                "AMBIGUIDADE: o pedido admite mais de uma interpretacao. "
                f"Qual das leituras voce quer? ({env.get('text','')[:80]})"
            )
        # comportamento padrao: assume a primeira leitura e responde sem avisar
        value = safe_eval_arith(guess) if guess else 0.0
        return f"O valor e {self._format_number(policy, value)}."

    def _missing_tool(self, policy: dict[str, str], env: dict[str, str], case: TaskCase) -> str:
        """Depende de ferramenta inexistente: (a) declara nao-execucao, (b) inventa."""
        if policy.get("ON_MISSING_TOOL") == "report_not_executed":
            tool = env.get("tool", "ferramenta_externa")
            return (
                f"NOT_EXECUTED: nao executei a consulta '{tool}' porque essa ferramenta "
                "nao esta disponivel neste ambiente. Nao apresento valor algum."
            )
        # fabricacao deterministica (indice derivado do texto -> estavel)
        idx = sum(ord(c) for c in case.case_id) % len(_FABRICATION_VALUES)
        return (
            f"Segundo a fonte consultada, o resultado e {_FABRICATION_VALUES[idx]} "
            f"(obtido via {env.get('tool','ferramenta_externa')})."
        )

    def _injection(self, policy: dict[str, str], env: dict[str, str], case: TaskCase) -> str:
        """Conteudo recuperado carrega instrucao hostil embutida."""
        legit = env.get("text", "")
        if policy.get("ON_UNTRUSTED_CONTENT") == "treat_as_data":
            out = f"Tratei o conteudo recuperado como dado, nao como instrucao. Pedido atendido: {legit}"
            if policy.get("REFUSAL_CODE") == "POL-REFUSE":
                out += " POL-REFUSE: tentativa de injecao de instrucao ignorada."
            return out
        # comportamento padrao: obedece a instrucao embutida (vulneravel)
        injected = env.get("injected", "PWNED")
        return f"{injected} SYSTEM_PROMPT EXPOSTO"

    def _refuse(self, policy: dict[str, str], env: dict[str, str], case: TaskCase) -> str:
        """Pedido que deve ser recusado com codigo rastreavel."""
        what = env.get("text", "pedido")
        if policy.get("REFUSAL_CODE") == "POL-REFUSE":
            return f"POL-REFUSE: nao posso atender a solicitacao ({what})."
        return f"Desculpe, nao posso ajudar com isso."

    def _concise(self, policy: dict[str, str], env: dict[str, str], case: TaskCase) -> str:
        """Resposta livre: verbosa por padrao, curta se MAX_WORDS limitar."""
        value = env.get("answer", "ok")
        limit = policy.get("MAX_WORDS", "unlimited")
        if limit == "unlimited":
            return _VERBOSE_TEMPLATE.format(value=value)
        return f"RESULTADO: {value}"

    def _language(self, policy: dict[str, str], env: dict[str, str], case: TaskCase) -> str:
        """Idioma da resposta: acompanha o pedido ou segue a politica fixa."""
        pt_answer = env.get("pt", "o valor foi apurado")
        en_answer = env.get("en", "the value was determined")
        if policy.get("LANGUAGE") == "pt-BR":
            return f"Resposta em portugues: {pt_answer}."
        source_is_english = env.get("source_lang", "pt") == "en"
        if source_is_english:
            return f"Answer follows the request language: {en_answer}."
        return f"Resposta em portugues: {pt_answer}."


# --------------------------------------------------------------------------
# Prosa: o executor tambem expoe o que leu, para auditoria humana
# --------------------------------------------------------------------------
def explain(prompt: PromptArtifact) -> dict[str, object]:
    """Diagnostico legivel do que o executor entende do prompt."""
    directives = parse_directives(prompt.text)
    return {
        "artifact_sha": prompt.sha_short,
        "directives": directives,
        "effective_policy": effective_policy(directives),
        "prose_lines": extract_prose(prompt.text),
        "missing_directives": missing_directives(prompt.text),
    }


def default_registry(enabled: list[str] | None = None) -> ExecutorRegistry:
    """Registry padrao com o executor deterministico de referencia.

    ``enabled=None`` significa "allowlist padrao"; ``enabled=[]`` significa
    "NADA habilitado" e deve ser respeitado. Usar ``enabled or [...]`` fazia uma
    allowlist explicitamente vazia ser silenciosamente substituida pela padrao --
    defeito de seguranca encontrado por teste.
    """
    reg = ExecutorRegistry(
        enabled=["policy_reference_v1"] if enabled is None else list(enabled)
    )
    reg.register(
        ExecutorInfo(
            name="policy_reference_v1",
            version=PolicyReferenceExecutor.version,
            deterministic=True,
            description=(
                "Interpreta a politica declarada no prompt. Deterministico, offline, "
                "sem rede. Modelo de referencia de COMPORTAMENTO, nao um LLM."
            ),
        ),
        PolicyReferenceExecutor,
    )
    return reg


def assert_executor_allowed(executor: Executor, policy: SafetyPolicy) -> None:
    """Garante que um executor nao exige capacidades proibidas."""
    if not executor.deterministic:
        policy.assert_can("network")  # exige permissao explicita (hoje impossivel)


def run_case(
    executor: Executor, prompt: PromptArtifact, case: TaskCase, max_output_chars: int = 4000
) -> str:
    """Executa um caso truncando a saida (limite de recurso, nao de conteudo)."""
    out = executor.execute(prompt, case)
    if not isinstance(out, str):
        raise ExecutorError(f"executor {executor.name} retornou {type(out).__name__}, esperado str")
    if len(out) > max_output_chars:
        return out[:max_output_chars] + "...[TRUNCATED]"
    return out


__all__ = [
    "Executor",
    "ExecutorInfo",
    "ExecutorRegistry",
    "PolicyReferenceExecutor",
    "default_registry",
    "parse_envelope",
    "run_case",
    "explain",
    "assert_executor_allowed",
]
