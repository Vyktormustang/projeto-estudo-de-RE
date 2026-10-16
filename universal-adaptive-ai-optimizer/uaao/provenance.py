"""Proveniencia: o que exatamente rodou, quando e em que ambiente.

Registra data, versao do codigo, commit do git e ambiente, para que qualquer
numero no relatorio seja reproduzivel. A leitura do commit do git e feita
**por arquivo** (``.git/HEAD`` + refs), sem subprocess -- coerente com a
politica de seguranca que proibe executar processos.
"""

from __future__ import annotations

import hashlib
import platform
import sys
from pathlib import Path
from typing import Any

from .types import utcnow

CODE_VERSION = "0.1.0"


def _read_text_safe(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def git_commit(start: Path | None = None) -> str:
    """Commit HEAD lido dos arquivos do .git (sem executar git)."""
    d = (start or Path(__file__).resolve())
    for parent in [d, *d.parents]:
        head = parent / ".git" / "HEAD"
        if not head.exists():
            continue
        content = _read_text_safe(head)
        if not content:
            return ""
        if content.startswith("ref:"):
            ref = content.split("ref:", 1)[1].strip()
            ref_file = parent / ".git" / ref
            sha = _read_text_safe(ref_file)
            if shas := ref_file.parent.glob(f"{ref_file.name}*"):
                pass
            if sha:
                return sha.splitlines()[0]
            # ref pode estar empacotada em packed-refs
            packed = _read_text_safe(parent / ".git" / "packed-refs") or ""
            for line in packed.splitlines():
                if line.endswith(ref) and not line.startswith("#"):
                    return line.split()[0]
            return ""
        return content.splitlines()[0]
    return ""


def environment_fingerprint() -> dict[str, Any]:
    """Ambiente de execucao (sem qualquer dado sensivel)."""
    return {
        "uaao_version": CODE_VERSION,
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": __import__("os").cpu_count(),
        "sqlite": __import__("sqlite3").sqlite_version,
        "gpu": "nenhuma detectada (projeto nao usa GPU)",
    }


def run_context(config_json: dict[str, Any], seed: int, executor: str) -> dict[str, Any]:
    """Bloco de proveniencia gravado com cada experimento."""
    env = environment_fingerprint()
    payload = {
        "timestamp_utc": utcnow(),
        "code_version": CODE_VERSION,
        "git_commit": git_commit(),
        "executor": executor,
        "seed": seed,
        "environment": env,
        "config": config_json,
    }
    payload["context_digest"] = hashlib.sha256(
        repr(sorted(payload.items())).encode("utf-8")
    ).hexdigest()[:16]
    return payload


__all__ = ["CODE_VERSION", "git_commit", "environment_fingerprint", "run_context"]
