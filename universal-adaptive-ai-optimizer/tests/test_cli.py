"""Testes da interface de linha de comando (fluxo real do usuario)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from uaao.cli import main


@pytest.fixture
def work(tmp_path):
    d = tmp_path / "work"
    d.mkdir()
    return str(d)


def run_cli(argv, capsys):
    code = main(argv)
    out = capsys.readouterr()
    return code, out.out + out.err


def test_doctor_reports_capabilities(work, capsys):
    code, out = run_cli(["doctor", "--workdir", work], capsys)
    assert code == 0
    assert "politica de seguranca" in out
    assert "allow_network" in out and "False" in out
    assert "policy_reference_v1" in out
    assert "NAO disponiveis" in out  # honestidade sobre LLM


def test_suites_lists_and_validates(work, capsys):
    code, out = run_cli(["suites", "--workdir", work], capsys)
    assert code == 0
    assert "calc_v1" in out and "safety_v1" in out
    assert "sha=" in out


def test_run_full_flow_writes_reports_and_memory(work, capsys):
    code, out = run_cli([
        "run", "--workdir", work,
        "--suite", "calc_v1", "--suite", "honesty_v1",
        "--iterations", "3",
    ], capsys)
    assert code == 0, out
    assert "experimento" in out
    assert "val  final" in out
    assert "relatorio" in out
    assert (Path(work) / "uaao_memory.sqlite3").exists()
    assert list((Path(work) / "reports").glob("*.md"))
    assert list((Path(work) / "reports").glob("*.json"))


def test_run_then_versions_history_and_show(work, capsys):
    assert main(["run", "--workdir", work, "--suite", "calc_v1", "--iterations", "3"]) == 0
    capsys.readouterr()

    code, out = run_cli(["versions", "--workdir", work, "--experiment", "latest"], capsys)
    assert code == 0 and "versoes de" in out and "ATIVA" in out

    code, out = run_cli(["history", "--workdir", work, "--experiment", "latest", "--timeline"], capsys)
    assert code == 0
    payload = json.loads(out[: out.index("\nlinha do tempo")])
    assert payload["experiment"]["status"] == "finished"
    assert "linha do tempo" in out

    code, out = run_cli(["show", "--workdir", work, "--experiment", "latest"], capsys)
    assert code == 0 and "experiment" in out


def test_rollback_flow(work, capsys):
    assert main(["run", "--workdir", work, "--suite", "calc_v1", "--iterations", "3"]) == 0
    capsys.readouterr()
    code, out = run_cli([
        "rollback", "--workdir", work, "--experiment", "latest",
        "--to", "previous", "--reason", "teste de reversao",
    ], capsys)
    assert code == 0 and "revertido" in out


def test_rollback_to_garbage_fails_with_code_1(work, capsys):
    assert main(["run", "--workdir", work, "--suite", "calc_v1", "--iterations", "2"]) == 0
    capsys.readouterr()
    code, out = run_cli(["rollback", "--workdir", work, "--experiment", "latest",
                         "--to", "deadbeef"], capsys)
    assert code == 1 and "nao encontrada" in out


def test_diff_flow(work, capsys):
    assert main(["run", "--workdir", work, "--suite", "calc_v1", "--iterations", "3"]) == 0
    capsys.readouterr()
    code, out = run_cli(["versions", "--workdir", work, "--experiment", "latest"], capsys)
    # casa apenas linhas no formato "  [i] <sha> ...", ignorando avisos entre colchetes
    shas = re.findall(r"^\s*\[\d+\]\s+([0-9a-f]{8,})", out, flags=re.M)
    assert len(shas) >= 2, out
    code, out = run_cli(["diff", "--workdir", work, "--a", shas[0], "--b", shas[-1]], capsys)
    assert code == 0
    payload = json.loads(out)
    assert payload["from"] and payload["to"]


def test_verify_audit_ok(work, capsys):
    assert main(["run", "--workdir", work, "--suite", "calc_v1", "--iterations", "2"]) == 0
    capsys.readouterr()
    code, out = run_cli(["verify-audit", "--workdir", work], capsys)
    assert code == 0 and "OK" in out


def test_verify_audit_detects_removed_middle_entry(work, capsys):
    """Remover um registro do MEIO quebra o encadeamento e e detectado."""
    assert main(["run", "--workdir", work, "--suite", "calc_v1", "--iterations", "2"]) == 0
    capsys.readouterr()
    audit = Path(work) / "audit" / "audit.jsonl"
    lines = audit.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 3
    middle = len(lines) // 2
    audit.write_text("\n".join(lines[:middle] + lines[middle + 1:]) + "\n", encoding="utf-8")
    code, out = run_cli(["verify-audit", "--workdir", work], capsys)
    assert code == 1 and "FALHA" in out


def test_verify_audit_detects_edited_entry(work, capsys):
    assert main(["run", "--workdir", work, "--suite", "calc_v1", "--iterations", "2"]) == 0
    capsys.readouterr()
    audit = Path(work) / "audit" / "audit.jsonl"
    lines = audit.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[1])
    rec["data"]["adulterado"] = True
    lines[1] = json.dumps(rec, sort_keys=True)
    audit.write_text("\n".join(lines) + "\n", encoding="utf-8")
    code, out = run_cli(["verify-audit", "--workdir", work], capsys)
    assert code == 1 and "FALHA" in out


def test_export_for_manual_backup(work, capsys):
    assert main(["run", "--workdir", work, "--suite", "honesty_v1", "--iterations", "2"]) == 0
    capsys.readouterr()
    out_file = Path(work) / "backup.json"
    code, out = run_cli(["export", "--workdir", work, "--experiment", "latest",
                         "--out", str(out_file)], capsys)
    assert code == 0 and out_file.exists()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["experiment"]["name"]
    assert "export_context" in payload
    assert "Google Drive" in out  # instrucao explicita de envio manual


def test_unknown_suite_returns_error(work, capsys):
    code, out = run_cli(["run", "--workdir", work, "--suite", "nao_existe", "--iterations", "1"], capsys)
    assert code == 1 and "nao encontrada" in out


def test_invalid_config_key_refused_by_cli(work, tmp_path, capsys):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"allow_network": True}), encoding="utf-8")
    code, out = run_cli(["run", "--workdir", work, "--config", str(cfg),
                         "--suite", "calc_v1", "--iterations", "1"], capsys)
    assert code == 1 and "seguranca" in out.lower()


def test_no_significance_flag_accepted(work, capsys):
    code, out = run_cli(["run", "--workdir", work, "--suite", "calc_v1",
                         "--iterations", "2", "--no-significance"], capsys)
    assert code == 0, out


def test_parser_requires_subcommand(capsys):
    with pytest.raises(SystemExit):
        main([])
