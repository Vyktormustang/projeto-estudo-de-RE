"""Consistencia entre a documentacao e o codigo.

Contexto: o README afirmou por varias horas que as suites tinham "51 casos: 32
treino / 13 validacao / 6 holdout" quando o correto era 50 / 27 / 14 / 9. Nenhum
teste olhava para texto de documentacao. Estes testes olham.

Eles chamam `tools/check_docs.py`, que LE os numeros escritos nos documentos e
confere cada um contra a fonte de verdade (codigo, suites, banco de evidencia
gerado por uma execucao real e a coleta do pytest). Se alguem editar a doc sem
atualizar o numero, ou mudar o codigo sem atualizar a doc, o teste falha.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "check_docs.py"


def _carrega_auditor() -> "object":
    """Importa tools/check_docs.py (nao e um pacote instalavel)."""
    spec = importlib.util.spec_from_file_location("uaao_check_docs", TOOL)
    assert spec and spec.loader, f"nao consegui carregar {TOOL}"
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["uaao_check_docs"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def test_documentacao_bate_com_o_codigo() -> None:
    """Toda afirmacao numerica da doc tem de ser verdadeira."""
    mod = _carrega_auditor()
    checks = mod.run_checks(quick=False)
    falhas = [f"{origem}: {afirmacao} -> {detalhe}" for origem, afirmacao, ok, detalhe in checks.failures]
    assert not falhas, "afirmacoes da documentacao divergem da realidade:\n  " + "\n  ".join(falhas)


def test_auditoria_cobre_um_minimo_de_afirmacoes() -> None:
    """Guarda contra o auditor virar no-op (ex.: um regex que deixou de casar).

    Sem isto, apagar uma checagem faria o teste acima passar por vacuidade.
    """
    mod = _carrega_auditor()
    checks = mod.run_checks(quick=False)
    assert len(checks.results) >= 20, (
        f"apenas {len(checks.results)} afirmacoes conferidas; esperado >= 20"
    )


def test_auditor_acusa_afirmacao_falsa(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prova que o auditor *falha* quando a doc mente (teste do proprio teste)."""
    mod = _carrega_auditor()
    falso = tmp_path / "README.md"
    falso.write_text(
        "suites agregadas (51 casos: 32 treino / 13 validação / 6 holdout):\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "README", falso)
    checks = mod.Checks()
    mod.check_suite_counts(checks)
    falhas = [r for r in checks.results if not r[2]]
    assert falhas, "o auditor aceitou a contagem errada (51/32/13/6)"
    assert "51" in falhas[0][3] or "51" in falhas[0][1], f"detalhe inesperado: {falhas[0]}"
    # e a checagem homonima no TEST_REPORT continua passando (o arquivo real nao mudou)
    assert any(ok for _, _, ok, _ in checks.results)
