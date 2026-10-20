#!/usr/bin/env python3
"""Auditoria automatica das afirmacoes numericas da documentacao.

Por que este arquivo existe: em 2026-10-16 o README afirmava "51 casos: 32 treino
/ 13 validacao / 6 holdout" quando o correto era 50 / 27 / 14 / 9. Nenhum teste
cobria texto de documentacao, entao o erro ficou publicado ate uma revisao manual.
Este script fecha essa lacuna: ele LE os numeros escritos no README e nos docs e
confere cada um contra a fonte de verdade (codigo, suites, banco de evidencia).

Cada checagem le um numero *do documento* por expressao regular -- nao ha
valor esperado codificado aqui. Se alguem editar a doc, a checagem acompanha; se
a doc divergir do codigo, ela falha.

Uso:
    python tools/check_docs.py            # auditoria completa (inclui pytest)
    python tools/check_docs.py --quick    # pula a coleta de testes (rapido)

Saida: uma linha por afirmacao, com [OK]/[FALHA]; exit code 1 se algo divergir.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from uaao.graders import GRADERS  # noqa: E402
from uaao.safety import (  # noqa: E402  (privados: ferramenta de auditoria interna)
    _INJECTION_PATTERNS,
    _SECRET_PATTERNS,
    UntrustedContent,
)
from uaao.taskset import load_all_builtin  # noqa: E402

README = ROOT / "README.md"
DOCS = ROOT / "docs"
EVIDENCIA_DIR = DOCS / "evidencias"


class Checks:
    """Coletor de resultados: cada afirmacao verificada vira uma linha."""

    def __init__(self) -> None:
        self.results: list[tuple[str, str, bool, str]] = []

    def check(self, origem: str, afirmacao: str, ok: bool, detalhe: str = "") -> None:
        self.results.append((origem, afirmacao, ok, detalhe))

    @property
    def failures(self) -> list[tuple[str, str, bool, str]]:
        return [r for r in self.results if not r[2]]

    def report(self) -> int:
        largura = max(len(f"{o}: {a}") for o, a, _, _ in self.results) if self.results else 0
        for origem, afirmacao, ok, detalhe in self.results:
            marca = "[OK  ]" if ok else "[FALHA]"
            rotulo = f"{origem}: {afirmacao}"
            print(f"{marca} {rotulo:<{largura}}  {detalhe}")
        print()
        if self.failures:
            print(f"AUDITORIA FALHOU: {len(self.failures)} de {len(self.results)} "
                  f"afirmacoes divergem da realidade.")
            return 1
        print(f"AUDITORIA OK: {len(self.results)} afirmacoes conferidas contra "
              f"codigo, suites, banco de evidencia e coleta de testes.")
        return 0


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _find(pattern: str, text: str, origem: str, checks: Checks, rotulo: str) -> list[str] | None:
    m = re.search(pattern, text, re.S)
    if not m:
        checks.check(origem, rotulo, False, "afirmacao nao encontrada na doc (foi reescrita?)")
        return None
    return list(m.groups())


def _num(raw: str) -> float:
    """Converte numero da doc: aceita 0.0816 (doc) e 1.234,56 (pt-BR)."""
    raw = raw.strip()
    if "," in raw:  # formato pt-BR
        return float(raw.replace(".", "").replace(",", "."))
    return float(raw)


def _int_pt(raw: str) -> int:
    """Inteiro em pt-BR: "20.000" e vinte mil (o ponto e' separador de milhar)."""
    return int(raw.replace(".", "").replace(",", ""))


def _dig(dados: dict[str, Any], caminho: str) -> Any:
    """Acessa run["baseline"]["val"] a partir de "baseline.val"."""
    atual: Any = dados
    for parte in caminho.split("."):
        atual = atual[parte]
    return atual


# ---------------------------------------------------------------------------
# 1. Composicao das suites
# ---------------------------------------------------------------------------
def check_suite_counts(checks: Checks) -> None:
    total = train = val = hold = 0
    for suite, _rep in load_all_builtin():
        total += len(suite.cases)
        train += len(suite.by_split("train"))
        val += len(suite.by_split("val"))
        hold += len(suite.by_split("holdout"))
    real = (total, train, val, hold)

    fontes = [
        (README, r"\((\d+) casos: (\d+) treino / (\d+) valida[çc][ãa]o / (\d+) holdout\)",
         "composicao das suites"),
        (DOCS / "TEST_REPORT.md",
         r"Composi[çc][ãa]o das 5 suites \((\d+) casos\): \*\*(\d+) treino / (\d+) valida[çc][ãa]o / (\d+) holdout\*\*",
         "composicao das suites"),
    ]
    for path, pattern, rotulo in fontes:
        grupos = _find(pattern, _read(path), path.name, checks, rotulo)
        if grupos:
            doc = tuple(int(g) for g in grupos)
            checks.check(path.name, rotulo, doc == real,
                         f"doc={doc} real={real}" if doc != real else f"{real[0]} casos {real[1:]}")


# ---------------------------------------------------------------------------
# 2. Numeros da execucao de evidencia (README x banco de evidencia)
# ---------------------------------------------------------------------------
def _load_evidence() -> tuple[Path, dict[str, Any]]:
    arquivos = sorted(EVIDENCIA_DIR.glob("*.json"))
    if not arquivos:
        raise FileNotFoundError(f"nenhuma evidencia em {EVIDENCIA_DIR}")
    return arquivos[-1], json.loads(_read(arquivos[-1]))


def check_evidence_numbers(checks: Checks) -> None:
    path, ev = _load_evidence()
    run = ev["run"]
    texto = _read(README)

    linhas = [
        (r"\| Treino \|[^|]*\| ([\d.]+) \| \*\*([\d.]+)\*\* \| \+([\d.]+) \|",
         ("baseline.train", "final.train"), "linha de treino"),
        (r"\| \*\*Valida[çc][ãa]o\*\* \|[^|]*\| ([\d.]+) \| \*\*([\d.]+)\*\* \| \*\*\+([\d.]+)\*\* \|",
         ("baseline.val", "final.val"), "linha de validacao"),
        (r"\| \*\*Holdout\*\* \|[^|]*\| ([\d.]+) \| \*\*([\d.]+)\*\* \| \*\*\+([\d.]+)\*\* \|",
         ("baseline.holdout", "final.holdout"), "linha de holdout"),
    ]
    for pattern, (kb, kf), rotulo in linhas:
        grupos = _find(pattern, texto, "README.md", checks, f"{rotulo} (evidencia {path.stem})")
        if not grupos:
            continue
        b_doc, f_doc, d_doc = (_num(g) for g in grupos)
        b_real, f_real = _dig(run, kb), _dig(run, kf)
        ok = (round(b_doc, 4) == round(b_real, 4) and round(f_doc, 4) == round(f_real, 4)
              and abs(d_doc - (f_real - b_real)) < 0.0001)
        checks.check("README.md", f"{rotulo} (evidencia {path.stem})", ok,
                     f"doc={b_doc}/{f_doc}/{d_doc} real={round(b_real,4)}/"
                     f"{round(f_real,4)}/{round(f_real-b_real,4)}")

    grupos = _find(r"(\d+) candidatos testados, \*\*(\d+) aceitos, (\d+) rejeitados",
                   texto, "README.md", checks, "contagem de candidatos")
    if grupos:
        tested, acc, rej = (int(g) for g in grupos)
        ok = (tested == run["candidates_tested"] and acc == run["candidates_accepted"]
              and rej == tested - acc)
        checks.check("README.md", "contagem de candidatos", ok,
                     f"doc={tested}/{acc}/{rej} real={run['candidates_tested']}/"
                     f"{run['candidates_accepted']}/{run['candidates_tested']-run['candidates_accepted']}")

    grupos = _find(r"(\d+) chamadas de m[ée]trica", texto, "README.md", checks, "chamadas de metrica")
    if grupos:
        doc = int(grupos[0])
        real = ev["ledger"]["metric_calls"]
        checks.check("README.md", "chamadas de metrica", doc == real, f"doc={doc} real={real}")

    tr = _read(DOCS / "TEST_REPORT.md")
    grupos = _find(r"\| Or[çc]amento \| [^|]*\| (\d+) de (\d+) chamadas", tr,
                   "TEST_REPORT.md", checks, "orcamento do relatorio de testes")
    if grupos:
        doc, teto = (int(g) for g in grupos)
        ok = doc == ev["ledger"]["metric_calls"] and teto == ev["ledger"]["max_metric_calls"]
        checks.check("TEST_REPORT.md", "orcamento do relatorio de testes", ok,
                     f"doc={doc}/{teto} real={ev['ledger']['metric_calls']}/{ev['ledger']['max_metric_calls']}")


# ---------------------------------------------------------------------------
# 3. Contagens estruturais citadas na doc
# ---------------------------------------------------------------------------
def check_structure_counts(checks: Checks) -> None:
    import sqlite3
    import tempfile

    from uaao.memory import Memory

    with tempfile.TemporaryDirectory() as tmp:
        mem = Memory(str(Path(tmp) / "auditoria.sqlite3"))
        tabelas = [r[0] for r in mem._connect().execute(
            "select name from sqlite_master where type='table' and name not like 'sqlite_%'")]

    casos = [
        (README, r"(\d+) graders objetivos", len(GRADERS), "graders registrados"),
        (README, r"(\d+) tabelas, WAL", len(tabelas), "tabelas no SQLite"),
        (DOCS / "SECURITY.md", r"As (\d+) heur[íi]sticas", len(_INJECTION_PATTERNS),
         "padroes de injecao"),
        (DOCS / "SECURITY.md", r"(\d+) padr[õo]es \(`sk-`", len(_SECRET_PATTERNS),
         "padroes de segredo"),
    ]
    for path, pattern, real, rotulo in casos:
        grupos = _find(pattern, _read(path), path.name, checks, rotulo)
        if grupos:
            doc = int(grupos[0])
            checks.check(path.name, rotulo, doc == real,
                         f"doc={doc} real={real}" if doc != real else f"{real}")

    # truncagem declarada nos docs x default do codigo
    doc_seg = _read(DOCS / "SECURITY.md")
    doc_arq = _read(DOCS / "ARCHITECTURE.md")
    import inspect

    real = inspect.signature(UntrustedContent.wrap).parameters["max_chars"].default
    grupos = _find(r"truncagem \((\d+\.\d+) chars por texto\)", doc_seg, "SECURITY.md", checks,
                   "limite de truncagem")
    if grupos:
        doc = _int_pt(grupos[0])
        checks.check("SECURITY.md", "limite de truncagem", doc == real, f"doc={doc} real={real}")
    # ARCHITECTURE.md nao repete o numero (so descreve "trunca"); se um dia repetir,
    # esta checagem passa a valer automaticamente.
    if m := re.search(r"(\d+\.\d+) chars por texto", doc_arq):
        doc = _int_pt(m.group(1))
        checks.check("ARCHITECTURE.md", "limite de truncagem", doc == real, f"doc={doc} real={real}")

    # output_head gravado no SQLite x afirmacao do SECURITY.md
    src = _read(ROOT / "uaao" / "memory.py")
    m = re.search(r"redact\(\(c\.output or \"\"\)\[:(\d+)\]\)", src)
    real_head = int(m.group(1)) if m else -1
    grupos = _find(r"output_head`* grava (\d+) caracteres", doc_seg, "SECURITY.md", checks,
                   "output_head gravado")
    if grupos:
        doc = _int_pt(grupos[0])
        checks.check("SECURITY.md", "output_head gravado", doc == real_head, f"doc={doc} real={real_head}")

    # payloads maliciosos no teste de aritmetica segura
    arvore = ast.parse(_read(ROOT / "tests" / "test_graders.py"))
    real_payloads = 0
    for node in ast.walk(arvore):
        if isinstance(node, ast.FunctionDef) and node.name == "test_safe_eval_arith_rejects_code_execution":
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and dec.args
                        and isinstance(dec.args[1], (ast.List, ast.Tuple))):
                    real_payloads = len(dec.args[1].elts)
    for ocorrencia in re.finditer(r"\((\d+) payloads", doc_seg):
        doc = int(ocorrencia.group(1))
        checks.check("SECURITY.md", "payloads maliciosos testados",
                     doc == real_payloads, f"doc={doc} real={real_payloads}")

    # dependencias de runtime
    pyproject = _read(ROOT / "pyproject.toml")
    m = re.search(r"(?m)^dependencies = \[(.*?)\]", pyproject)
    deps = [d for d in (m.group(1).split(",") if m else []) if d.strip()]
    readme = _read(README)
    checks.check("pyproject.toml", "zero dependencias de runtime", not deps,
                 "dependencies = []" if not deps else f"encontrado: {deps}")
    checks.check("README.md", "afirma zero de runtime",
                 "**Runtime: zero.**" in readme or "runtime stdlib-only" in readme.lower(),
                 "declaracao presente" if "**Runtime: zero.**" in readme else "declaracao ausente")


# ---------------------------------------------------------------------------
# 4. Contagem de defeitos documentados
# ---------------------------------------------------------------------------
def check_defect_count(checks: Checks) -> None:
    tr = _read(DOCS / "TEST_REPORT.md")
    grupos = _find(r"\*\*(\d+) defeitos reais do produto\*\*", tr, "TEST_REPORT.md", checks,
                   "defeitos reais documentados")
    if not grupos:
        return
    doc = int(grupos[0])
    secao = tr.split("## 4.")[1].split("## 5.")[0]
    numeros = [int(m.group(1)) for m in re.finditer(r"(?m)^\|\s*(\d+)\s*\|", secao)]
    ok = numeros == list(range(1, doc + 1))
    checks.check("TEST_REPORT.md", "defeitos reais documentados", ok,
                 f"doc={doc} linhas na tabela={len(numeros)}"
                 + ("" if ok else " (numeracao nao sequencial)"))


# ---------------------------------------------------------------------------
# 5. Links locais da documentacao
# ---------------------------------------------------------------------------
def check_links(checks: Checks) -> None:
    arquivos = [README, *(DOCS.glob("*.md")), *(ROOT / "examples").glob("*.md")]
    quebrados: list[str] = []
    total = 0
    for arq in arquivos:
        for m in re.finditer(r"\[([^\]]+)\]\(([^)#\s]+)\)", _read(arq)):
            alvo = m.group(2)
            if alvo.startswith(("http://", "https://", "mailto:")):
                continue
            total += 1
            destino = (arq.parent / alvo).resolve()
            if not destino.exists():
                quebrados.append(f"{arq.relative_to(ROOT)} -> {alvo}")
    checks.check("docs", "links locais resolvem", not quebrados,
                 f"{total} links verificados" + ("; QUEBRADOS: " + ", ".join(quebrados) if quebrados else ""))


# ---------------------------------------------------------------------------
# 6. Contagem de testes x o que a doc afirma
# ---------------------------------------------------------------------------
def _collect_counts() -> tuple[dict[str, int], int]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q",
         "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True,
    )
    por_arquivo: dict[str, int] = {}
    for linha in proc.stdout.splitlines():
        m = re.match(r"^tests/(test_[a-z_]+\.py): (\d+)$", linha.strip())
        if m:
            por_arquivo[m.group(1)] = int(m.group(2))
    return por_arquivo, sum(por_arquivo.values())


def check_test_counts(checks: Checks, quick: bool) -> None:
    texto = _read(README)
    if not quick:
        por_arquivo, total = _collect_counts()
        if not por_arquivo:
            checks.check("tests", "coleta de testes", False, "pytest nao retornou contagens")
            return
        grupos = _find(r"\*\*(\d+) testes, (\d+) passando\*\*", texto, "README.md", checks,
                       "total de testes")
        if grupos:
            doc_total, doc_pass = (int(g) for g in grupos)
            checks.check("README.md", "total de testes", doc_total == total,
                         f"doc={doc_total} coletados={total} (doc diz {doc_pass} passando)")

        tr = _read(DOCS / "TEST_REPORT.md")
        linhas = re.findall(r"(?m)^\| `(test_[a-z_]+\.py)` \| (\d+) \|", tr)
        divergentes = [(nome, int(n), por_arquivo.get(nome))
                       for nome, n in linhas if por_arquivo.get(nome) != int(n)]
        checks.check("TEST_REPORT.md", "contagem por arquivo de teste", not divergentes,
                     f"{len(linhas)} arquivos conferidos" if not divergentes
                     else f"divergentes: {divergentes}")
        grupos = _find(r"\| \*\*Total\*\* \| \*\*(\d+)\*\*", tr, "TEST_REPORT.md", checks,
                       "total no relatorio de testes")
        if grupos:
            checks.check("TEST_REPORT.md", "total no relatorio de testes",
                         int(grupos[0]) == total, f"doc={grupos[0]} coletados={total}")

        # a arvore de arquivos citada no README (secao "Estrutura do repositorio")
        grupos = _find(r"tests/ +[^\n]*?(\d+) testes", texto, "README.md", checks,
                       "arvore de arquivos do README")
        if grupos:
            checks.check("README.md", "arvore de arquivos do README",
                         int(grupos[0]) == total, f"doc={grupos[0]} coletados={total}")


# ---------------------------------------------------------------------------
def run_checks(quick: bool = False) -> Checks:
    checks = Checks()
    check_suite_counts(checks)
    check_evidence_numbers(checks)
    check_structure_counts(checks)
    check_defect_count(checks)
    check_links(checks)
    check_test_counts(checks, quick)
    return checks


def main() -> int:
    ap = argparse.ArgumentParser(description="Audita as afirmacoes numericas da documentacao.")
    ap.add_argument("--quick", action="store_true",
                    help="pula a coleta do pytest (nao confere contagens de teste)")
    args = ap.parse_args()
    print("== auditoria da documentacao do uaao ==")
    print(f"   raiz: {ROOT}")
    print()
    return run_checks(quick=args.quick).report()


if __name__ == "__main__":
    raise SystemExit(main())
