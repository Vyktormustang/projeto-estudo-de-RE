"""Especificacao do artefato otimizado (o "prompt") e seu schema de diretivas.

DECISAO DE PROJETO (honestidade metodologica)
---------------------------------------------
Sem LLM acessivel, o UA AO otimiza *instrucoes/politicas declarativas* que sao
interpretadas por um **executor de referencia deterministico** (``executors.py``).
Isto NAO mede a qualidade de GPT/Claude/Gemini. Mede:

  * se o loop de otimizacao (baseline -> diagnostico -> proposta -> selecao)
    realmente encontra melhorias mensuraveis e reproduziveis; e
  * se a politica escrita torna um comportamento *verificavel* (formato,
    tratamento de ambiguidade, honestidade sobre ferramentas, resistencia a
    injecao de instrucao).

O contrato e explicito: o texto do prompt e a fonte da verdade; as diretivas
``CHAVE = valor`` sao extraidas dele. Mudar o texto muda o comportamento de
forma observavel -- e portanto mensuravel.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

# --------------------------------------------------------------------------
# Schema das diretivas (o "espaco de busca" e estritamente este)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DirectiveSpec:
    key: str
    values: tuple[str, ...]
    default: str
    group: str
    description: str

    def is_legal(self, value: str) -> bool:
        return value in self.values


DIRECTIVE_SCHEMA: tuple[DirectiveSpec, ...] = (
    DirectiveSpec(
        key="OUTPUT_FORMAT",
        values=("free_text", "json_object"),
        default="free_text",
        group="formato",
        description="Contrato de saida. 'json_object' exige JSON valido com chaves fixas.",
    ),
    DirectiveSpec(
        key="ROUND_DECIMALS",
        values=("as_is", "0", "2", "4"),
        default="as_is",
        group="precisao",
        description="Casas decimais do resultado numerico.",
    ),
    DirectiveSpec(
        key="INCLUDE_EXPRESSION",
        values=("false", "true"),
        default="false",
        group="formato",
        description="Se a expressao de origem deve acompanhar o resultado.",
    ),
    DirectiveSpec(
        key="ON_AMBIGUOUS",
        values=("guess", "ask_clarification"),
        default="guess",
        group="ambiguidade",
        description="Pedido ambiguo: adivinhar ou pedir esclarecimento explicito.",
    ),
    DirectiveSpec(
        key="ON_MISSING_TOOL",
        values=("fabricate", "report_not_executed"),
        default="fabricate",
        group="honestidade",
        description="Ferramenta indisponivel: inventar resultado ou declarar nao execucao.",
    ),
    DirectiveSpec(
        key="ON_UNTRUSTED_CONTENT",
        values=("obey", "treat_as_data"),
        default="obey",
        group="seguranca",
        description="Instrucoes embutidas em conteudo recuperado: obedecer ou tratar como dado.",
    ),
    DirectiveSpec(
        key="LANGUAGE",
        values=("auto", "pt-BR"),
        default="auto",
        group="idioma",
        description="Idioma da resposta.",
    ),
    DirectiveSpec(
        key="MAX_WORDS",
        values=("unlimited", "40", "25"),
        default="unlimited",
        group="concisao",
        description="Teto de palavras da resposta livre.",
    ),
    DirectiveSpec(
        key="REFUSAL_CODE",
        values=("none", "POL-REFUSE"),
        default="none",
        group="seguranca",
        description="Codigo emitido ao recusar conteudo hostil/malicioso.",
    ),
)

SCHEMA_BY_KEY: dict[str, DirectiveSpec] = {d.key: d for d in DIRECTIVE_SCHEMA}

# Valores "bons" conhecidos por diretiva, usados como *hipoteses* pelo propositor.
# Nao sao verdades embutidas: sao sugestoes que ainda precisam passar no val.
PREFERRED_VALUES: dict[str, str] = {
    "OUTPUT_FORMAT": "json_object",
    "ROUND_DECIMALS": "2",
    "INCLUDE_EXPRESSION": "true",
    "ON_AMBIGUOUS": "ask_clarification",
    "ON_MISSING_TOOL": "report_not_executed",
    "ON_UNTRUSTED_CONTENT": "treat_as_data",
    "LANGUAGE": "pt-BR",
    "MAX_WORDS": "40",
    "REFUSAL_CODE": "POL-REFUSE",
}

# Grupo de diretiva -> classe de falha que a sugere (usada por propose.py).
GROUP_FOR_FAILURE: dict[str, str] = {
    "formato_invalido": "formato",
    "precisao_err": "precisao",
    "ambiguidade_nao_sinalizada": "ambiguidade",
    "fabricacao": "honestidade",
    "injecao_obedecida": "seguranca",
    "idioma_errado": "idioma",
    "excesso_palavras": "concisao",
    "expressao_ausente": "formato",
    "recusa_sem_codigo": "seguranca",
}

# --------------------------------------------------------------------------
# Parser / renderizador
# --------------------------------------------------------------------------
_DIRECTIVE_LINE = re.compile(r"^\s*([A-Z][A-Z0-9_]{2,31})\s*=\s*(.+?)\s*$")
_COMMENT = re.compile(r"^\s*#")
# Linhas de prosa aceitam "PROSE:" ou texto simples que nao seja diretiva.
_PROSE_PREFIX = re.compile(r"^\s*(PROSE|INSTRUCAO|INSTRUCTION|NOTA)\s*:\s*(.*)$", re.I)


def parse_directives(text: str) -> dict[str, str]:
    """Extrai ``CHAVE = valor`` do texto.

    Tolerante: ignora chaves fora do schema e normaliza valores booleanos.
    Nao levanta excecao -- o texto do prompt e dado, nao codigo.
    """
    out: dict[str, str] = {}
    for line in (text or "").splitlines():
        if _COMMENT.match(line):
            continue
        m = _DIRECTIVE_LINE.match(line)
        if not m:
            continue
        key, value = m.group(1).strip(), m.group(2).strip()
        if key not in SCHEMA_BY_KEY:
            continue  # chave desconhecida: ignorada (nao vira comportamento)
        out[key] = value
    return out


def effective_policy(directives: Mapping[str, str]) -> dict[str, str]:
    """Aplica defaults do schema a um conjunto de diretivas ausentes."""
    policy = {d.key: d.default for d in DIRECTIVE_SCHEMA}
    for k, v in directives.items():
        spec = SCHEMA_BY_KEY.get(k)
        if spec and spec.is_legal(v):
            policy[k] = v
    return policy


def invalid_directives(directives: Mapping[str, str]) -> dict[str, str]:
    """Retorna diretorias legais no schema mas com valor invalido."""
    bad: dict[str, str] = {}
    for k, v in directives.items():
        spec = SCHEMA_BY_KEY.get(k)
        if spec and not spec.is_legal(v):
            bad[k] = v
    return bad


def extract_prose(text: str) -> list[str]:
    """Linhas de prosa (nao-diretivas, nao-comentarios)."""
    out: list[str] = []
    for line in (text or "").splitlines():
        if not line.strip() or _COMMENT.match(line) or _DIRECTIVE_LINE.match(line):
            continue
        m = _PROSE_PREFIX.match(line)
        out.append((m.group(2) if m else line).strip())
    return out


def render(prose: Iterable[str], directives: Mapping[str, str], header: str = "") -> str:
    """Renderiza um prompt canonico: cabecalho, prosa e diretivas ordenadas."""
    lines: list[str] = []
    if header:
        lines.append(f"# {header}")
        lines.append("")
    for p in prose:
        if p.strip():
            lines.append(f"PROSE: {p.strip()}")
    if lines:
        lines.append("")
    lines.append("# --- diretivas de politica ---")
    for spec in DIRECTIVE_SCHEMA:  # ordem estavel -> diff legivel e hash estavel
        if spec.key in directives:
            lines.append(f"{spec.key} = {directives[spec.key]}")
    return "\n".join(lines).rstrip() + "\n"


def set_directive(text: str, key: str, value: str) -> str:
    """Insere/atualiza uma diretiva preservando prosa e comentarios."""
    spec = SCHEMA_BY_KEY.get(key)
    if spec is None:
        raise ValueError(f"diretiva desconhecida: {key}")
    if not spec.is_legal(value):
        raise ValueError(f"valor invalido para {key}: {value!r} (legais: {spec.values})")
    out: list[str] = []
    replaced = False
    for line in text.splitlines():
        m = _DIRECTIVE_LINE.match(line)
        if m and m.group(1).strip() == key:
            out.append(f"{key} = {value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out).rstrip() + "\n"


def remove_directive(text: str, key: str) -> str:
    out = [
        line
        for line in text.splitlines()
        if not (_DIRECTIVE_LINE.match(line) and _DIRECTIVE_LINE.match(line).group(1).strip() == key)
    ]
    return "\n".join(out).rstrip() + "\n"


def add_prose(text: str, sentence: str) -> str:
    return text.rstrip() + f"\nPROSE: {sentence.strip()}\n"


def missing_directives(text: str) -> list[str]:
    present = set(parse_directives(text))
    return [d.key for d in DIRECTIVE_SCHEMA if d.key not in present]


def directive_diff(a: str, b: str) -> dict[str, tuple[str | None, str | None]]:
    """Diferenca de politica entre dois prompts: {chave: (antes, depois)}."""
    pa, pb = parse_directives(a), parse_directives(b)
    keys = sorted(set(pa) | set(pb))
    return {k: (pa.get(k), pb.get(k)) for k in keys if pa.get(k) != pb.get(k)}


__all__ = [
    "DirectiveSpec",
    "DIRECTIVE_SCHEMA",
    "SCHEMA_BY_KEY",
    "PREFERRED_VALUES",
    "GROUP_FOR_FAILURE",
    "parse_directives",
    "effective_policy",
    "invalid_directives",
    "extract_prose",
    "render",
    "set_directive",
    "remove_directive",
    "add_prose",
    "missing_directives",
    "directive_diff",
]
