"""Interface de linha de comando.

    python -m uaao doctor
    python -m uaao suites
    python -m uaao run --suite calc_v1 --iterations 3
    python -m uaao versions --experiment exp-xxxx
    python -m uaao rollback --experiment exp-xxxx --to previous --reason "..."
    python -m uaao diff --a <sha> --b <sha>
    python -m uaao show --experiment exp-xxxx
    python -m uaao export --experiment exp-xxxx --out backup.json
    python -m uaao verify-audit

Codigos de saida: 0 sucesso, 1 erro tratado, 2 erro de uso.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import Config
from .errors import UaaoError
from .executors import default_registry
from .history import History
from .memory import Memory
from .optimizer import Optimizer, load_seed_prompt
from .provenance import environment_fingerprint, git_commit, run_context
from .report import write_reports
from .safety import AuditLog, SafetyPolicy, env_secret_names, scan_for_secrets
from .taskset import list_builtin_suites, load_suite, merge_suites, validate_suite


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _default_paths(args: argparse.Namespace) -> tuple[Config, Path]:
    root = Path(args.workdir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    cfg = Config.load(args.config).resolved(root)
    return cfg, root


def _load_suite(name_or_path: str):
    p = Path(name_or_path)
    if p.exists():
        return load_suite(p)
    builtin = {f.stem: f for f in list_builtin_suites()}
    if name_or_path in builtin:
        return load_suite(builtin[name_or_path])
    raise UaaoError(
        f"suite {name_or_path!r} nao encontrada. Embutidas: {sorted(builtin)}"
    )


def _multi_suite(names: list[str], suite_id: str = "merged") -> tuple[object, list]:
    suites, reports = [], []
    for n in names:
        s, r = _load_suite(n)
        suites.append(s)
        reports.append(r)
    if len(suites) == 1:
        return suites[0], reports
    return merge_suites(suites, suite_id=suite_id, version="merged-1"), reports


# --------------------------------------------------------------------------
# comandos
# --------------------------------------------------------------------------
def cmd_doctor(args: argparse.Namespace) -> int:
    """Diagnostico honesto do ambiente e das capacidades efetivas."""
    print("== UA AO - diagnostico do ambiente ==")
    for k, v in environment_fingerprint().items():
        print(f"  {k:16s}: {v}")
    print(f"  {'git_commit':16s}: {git_commit() or '(nao detectado)'}")
    print(f"  {'uaao_version':16s}: {__version__}")

    policy = SafetyPolicy.hardened()
    print("\n== politica de seguranca (imutavel) ==")
    print(f"  allow_network          : {policy.allow_network}")
    print(f"  allow_external_write   : {policy.allow_external_write}")
    print(f"  allow_self_modification: {policy.allow_self_modification}")
    print(f"  allow_subprocess       : {policy.allow_subprocess}")
    print(f"  fingerprint            : {policy.fingerprint()}")

    print("\n== adaptadores de execucao disponiveis ==")
    reg = default_registry()
    for info in reg.available():
        print(f"  - {info.name} v{info.version} (deterministico={info.deterministic})")
        print(f"      {info.description}")

    print("\n== capacidades ausentes (declaradas, nao testadas como disponiveis) ==")
    keys = env_secret_names()
    print(f"  variaveis de ambiente sensiveis definidas: {keys or 'nenhuma'}")
    print("  chamadas a API de LLM: NAO disponiveis neste ambiente")
    print("    (nenhuma chave de modelo configurada; hosts de API nao alcancaveis)")
    print("  -> por isso o sistema opera com executores deterministicos locais.")

    print("\n== suites embutidas ==")
    for path in list_builtin_suites():
        try:
            suite, report = load_suite(path)
            problems = validate_suite(suite)
            status = "ok" if not problems else f"ATENCAO: {problems}"
            print(
                f"  - {suite.suite_id} v{suite.version}: {len(suite.cases)} casos "
                f"({report.split_counts}) sha={suite.sha_short} [{status}]"
            )
            if report.injection_flags:
                print(
                    f"      {len(report.injection_flags)} caso(s) com padrao de injecao "
                    "embutido (intencional em suites de seguranca; tratado como dado)"
                )
        except UaaoError as exc:
            print(f"  - {path.name}: ERRO {exc}")
            return 1

    print("\n== segredos no diretorio de trabalho ==")
    hits = []
    for f in Path(".").rglob("*"):
        if f.is_file() and f.suffix in (".py", ".md", ".json", ".toml", ".txt", ".cfg"):
            if any(part in (".git", ".venv", "node_modules") for part in f.parts):
                continue
            try:
                found = scan_for_secrets(f.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if found:
                hits.append((str(f), found))
    print(f"  arquivos com padrao de segredo: {len(hits)}")
    for path, found in hits[:10]:
        print(f"    - {path}: {found[:2]}")
    print("\ndiagnostico concluido.")
    return 0


def cmd_suites(args: argparse.Namespace) -> int:
    for path in list_builtin_suites():
        suite, report = load_suite(path)
        problems = validate_suite(suite)
        print(f"{suite.suite_id} v{suite.version}  sha={suite.sha_short}")
        print(f"  arquivo: {path}")
        print(f"  casos  : {len(suite.cases)}  splits: {report.split_counts}")
        print(f"  criticos: {sum(1 for c in suite.cases if c.critical)}")
        grads = sorted({c.grader for c in suite.cases})
        print(f"  graders: {', '.join(grads)}")
        if report.warnings:
            for w in report.warnings:
                print(f"  AVISO: {w}")
        if problems:
            print(f"  PROBLEMAS: {problems}")
        print()
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg, root = _default_paths(args)
    if args.iterations is not None:
        cfg.limits.max_iterations = int(args.iterations)
    if args.max_metric_calls is not None:
        cfg.limits.max_metric_calls = int(args.max_metric_calls)
    if args.seed is not None:
        cfg.random_seed = int(args.seed)
    if args.no_significance:
        cfg.selection.require_significance = False
    cfg.validate()

    suite, reports = _multi_suite(args.suite)
    for r in reports:
        if r.warnings:
            for w in r.warnings:
                print(f"[aviso de suite] {w}", file=sys.stderr)
        if r.injection_flags:
            print(
                f"[suite] {len(r.injection_flags)} caso(s) com padrao de injecao embutido "
                "-> tratados como DADO (a decisao fica com a politica do prompt)",
                file=sys.stderr,
            )

    registry = default_registry(enabled=cfg.enabled_executors)
    executor = registry.get(args.executor or cfg.default_executor)
    memory = Memory(cfg.db_path)
    audit = AuditLog(cfg.audit_path)

    policy = SafetyPolicy.hardened()
    policy.assert_can("write_local")

    seed = load_seed_prompt(args.prompt)
    print(f"suite    : {suite.suite_id} v{suite.version} (sha {suite.sha_short})")
    print(f"executor : {executor.name} (deterministico={executor.deterministic})")
    print(f"semente  : {seed.sha_short}")
    print(f"limites  : iteracoes={cfg.limits.max_iterations}, "
          f"candidatos/iter={cfg.limits.max_candidates_per_iteration}, "
          f"chamadas={cfg.limits.max_metric_calls}, tempo={cfg.limits.max_wall_seconds}s")
    print()

    optimizer = Optimizer(cfg, suite, executor, memory, audit=audit, policy=policy)
    try:
        kind = getattr(suite, "suite_id", "suite")
        run = optimizer.run(
            seed, name=args.name or f"opt-{kind}",
            experiment_id=args.resume_experiment, resume=bool(args.resume_experiment),
        )
    except UaaoError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    for it in run.iterations:
        print(f"--- iteracao {it.index} ---")
        print(f"  diagnostico: {it.diagnosis.passed_cases}/{it.diagnosis.total_cases} passam no treino")
        for c in it.diagnosis.clusters[:4]:
            print(f"    - {c.kind}: {c.size} caso(s) -> grupo '{c.directive_group or 'sem acao'}'")
        print(f"  candidatos: {it.n_proposals}")
        for o in it.outcomes:
            print(
                f"    [{'ACEITO' if o.accepted else 'rejeitado'}] {o.proposal.artifact.sha_short} "
                f"{o.proposal.operator} val={o.val_result.mean_score:.4f} :: {o.decision.reason[:110]}"
            )

    print()
    print(f"experimento   : {run.experiment_id}")
    print(f"encerramento  : {run.stopped_reason}")
    print(f"val  baseline : {run.baseline_val.mean_score:.4f}")
    print(f"val  final    : {run.final_val.mean_score:.4f}  ({run.final_val.mean_score - run.baseline_val.mean_score:+.4f})")
    if run.holdout_baseline and run.holdout_final:
        print(f"holdout       : {run.holdout_baseline.mean_score:.4f} -> {run.holdout_final.mean_score:.4f} "
              f"({run.holdout_final.mean_score - run.holdout_baseline.mean_score:+.4f})")
    print(f"candidatos    : {run.tested_count()} testados, {run.accepted_count()} aceitos")
    print(f"determinismo  : {'confirmado' if run.determinism_ok else run.determinism_ok}")
    print(f"orcamento     : {run.ledger_snapshot}")

    paths = write_reports(run, suite.suite_id, suite.sha, cfg, memory, History(memory, audit),
                          cfg.reports_dir, suite_names=list(args.suite))
    for kind, p in paths.items():
        print(f"relatorio {kind:8s}: {p}")
    return 0


def cmd_versions(args: argparse.Namespace) -> int:
    cfg, _ = _default_paths(args)
    memory = Memory(cfg.db_path)
    hist = History(memory, AuditLog(cfg.audit_path))
    exp = args.experiment
    if exp == "latest":
        exps = memory.list_experiments(limit=1)
        if not exps:
            print("nenhum experimento registrado", file=sys.stderr)
            return 1
        exp = exps[0].experiment_id
    versions = hist.versions(exp)
    if not versions:
        print(f"nenhuma versao para {exp}", file=sys.stderr)
        return 1
    print(f"versoes de {exp}:")
    for i, v in enumerate(versions):
        score = f"{v.last_val_score:.4f}" if v.last_val_score is not None else "  n/d "
        mark = "*ATIVA*" if v.active else "       "
        print(f"  [{i}] {v.short} {mark} val={score} origem={v.origin:8s} {v.notes}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    cfg, _ = _default_paths(args)
    memory = Memory(cfg.db_path)
    hist = History(memory, AuditLog(cfg.audit_path))
    exp = args.experiment
    if exp == "latest":
        exps = memory.list_experiments(limit=1)
        if not exps:
            print("nenhum experimento registrado", file=sys.stderr)
            return 1
        exp = exps[0].experiment_id
    print(json.dumps(hist.summary(exp), ensure_ascii=False, indent=2))
    if args.timeline:
        print("\nlinha do tempo:")
        for e in hist.timeline(exp):
            extra = ""
            if e["type"] == "decision":
                extra = f"aceito={e['accepted']} :: {e['reason'][:90]}"
            elif e["type"] == "evaluation":
                extra = f"{e['split']} mean={e['mean_score']:.4f}"
            elif e["type"] == "error":
                extra = f"{e['scope']}: {e['message'][:80]}"
            print(f"  {e['at']} {e['type']:11s} {extra}")
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    cfg, _ = _default_paths(args)
    memory = Memory(cfg.db_path)
    hist = History(memory, AuditLog(cfg.audit_path))
    exp = args.experiment
    if exp == "latest":
        exps = memory.list_experiments(limit=1)
        if not exps:
            print("nenhum experimento registrado", file=sys.stderr)
            return 1
        exp = exps[0].experiment_id
    result = hist.rollback(exp, args.to, reason=args.reason or "")
    print(("OK: " if result.ok else "NAO FOI POSSIVEL: ") + result.message)
    return 0 if result.ok else 1


def cmd_diff(args: argparse.Namespace) -> int:
    cfg, _ = _default_paths(args)
    memory = Memory(cfg.db_path)
    hist = History(memory, AuditLog(cfg.audit_path))
    try:
        d = hist.diff(args.a, args.b)
    except UaaoError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(d, ensure_ascii=False, indent=2))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    cfg, _ = _default_paths(args)
    memory = Memory(cfg.db_path)
    exp = args.experiment
    if exp == "latest":
        exps = memory.list_experiments(limit=1)
        if not exps:
            print("nenhum experimento registrado", file=sys.stderr)
            return 1
        exp = exps[0].experiment_id
    print(json.dumps(History(memory).summary(exp), ensure_ascii=False, indent=2))
    reports = memory.list_reports(exp)
    if reports:
        print("\nrelatorios:")
        for r in reports:
            print(f"  [{r['kind']}] {r['path']}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Exporta o experimento em JSON (para backup manual no Drive)."""
    cfg, _ = _default_paths(args)
    memory = Memory(cfg.db_path)
    exp = args.experiment
    if exp == "latest":
        exps = memory.list_experiments(limit=1)
        if not exps:
            print("nenhum experimento registrado", file=sys.stderr)
            return 1
        exp = exps[0].experiment_id
    payload = memory.export_experiment(exp)
    payload["export_context"] = run_context(cfg.to_json(), cfg.random_seed, cfg.default_executor)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"exportado: {out} ({out.stat().st_size} bytes)")
    print("Envie manualmente ao Google Drive se desejar backup (o sistema nao escreve externo).")
    return 0


def cmd_verify_audit(args: argparse.Namespace) -> int:
    cfg, _ = _default_paths(args)
    audit = AuditLog(cfg.audit_path)
    ok, msg = audit.verify()
    print(("OK: " if ok else "FALHA: ") + msg)
    print(f"arquivo: {audit.path}")
    return 0 if ok else 1


# --------------------------------------------------------------------------
# parser
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="uaao",
        description="Universal Adaptive AI Optimizer - camada externa de otimizacao de prompts.",
    )
    p.add_argument("--version", action="version", version=f"uaao {__version__}")

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--config", default=None, help="arquivo JSON de configuracao")
        sp.add_argument("--workdir", default=".", help="diretorio base de dados/relatorios")

    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("doctor", help="diagnostico do ambiente e das capacidades reais")
    common(sp)
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("suites", help="lista e valida as suites embutidas")
    common(sp)
    sp.set_defaults(func=cmd_suites)

    sp = sub.add_parser("run", help="executa o ciclo de otimizacao")
    common(sp)
    sp.add_argument("--suite", action="append", required=True, help="nome ou caminho (repetivel p/ merge)")
    sp.add_argument("--prompt", default=None, help="arquivo com o prompt original")
    sp.add_argument("--iterations", type=int, default=None)
    sp.add_argument("--max-metric-calls", type=int, default=None)
    sp.add_argument("--seed", type=int, default=None)
    sp.add_argument("--executor", default=None)
    sp.add_argument("--name", default=None)
    sp.add_argument("--no-significance", action="store_true", help="nao exigir teste de sinais")
    sp.add_argument("--resume-experiment", default=None, help="retoma um experimento interrompido")
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("versions", help="lista versoes de um experimento")
    common(sp)
    sp.add_argument("--experiment", default="latest")
    sp.set_defaults(func=cmd_versions)

    sp = sub.add_parser("history", help="resumo e linha do tempo")
    common(sp)
    sp.add_argument("--experiment", default="latest")
    sp.add_argument("--timeline", action="store_true")
    sp.set_defaults(func=cmd_history)

    sp = sub.add_parser("rollback", help="reverte para uma versao anterior (nada e apagado)")
    common(sp)
    sp.add_argument("--experiment", default="latest")
    sp.add_argument("--to", required=True, help="sha, prefixo de sha ou 'previous'")
    sp.add_argument("--reason", default="")
    sp.set_defaults(func=cmd_rollback)

    sp = sub.add_parser("diff", help="diferenca de politica entre duas versoes")
    common(sp)
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.set_defaults(func=cmd_diff)

    sp = sub.add_parser("show", help="resumo de um experimento")
    common(sp)
    sp.add_argument("--experiment", default="latest")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("export", help="exporta o experimento para JSON (backup manual)")
    common(sp)
    sp.add_argument("--experiment", default="latest")
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_export)

    sp = sub.add_parser("verify-audit", help="verifica a integridade da trilha de auditoria")
    common(sp)
    sp.set_defaults(func=cmd_verify_audit)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except UaaoError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        print("interrompido pelo usuario", file=sys.stderr)
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
