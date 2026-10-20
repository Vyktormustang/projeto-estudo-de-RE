"""Testes de ACEITACAO: um por requisito verificavel pedido na especificacao.

Diferente dos testes unitarios, estes rodam contra as SUITES DE PRODUCAO e
medem comportamento real do sistema (nao mocks). Cada teste cita o requisito
que verifica.
"""

from __future__ import annotations

import json

import pytest

from uaao.diagnose import diagnose
from uaao.evaluate import evaluate
from uaao.history import History
from uaao.memory import Memory
from uaao.optimizer import Optimizer
from uaao.report import build_report_markdown
from uaao.safety import AuditLog
from uaao.taskset import merge_suites


@pytest.fixture
def prod_suite(registered_suites):
    """Suite agregada de producao (todas as 5 suites)."""
    suites = [s for s, _ in registered_suites.values()]
    return merge_suites(suites, suite_id="prod", version="1.0.0")


@pytest.fixture
def prod_run(cfg, prod_suite, baseline_prompt, executor):
    cfg.limits.max_iterations = 8
    memory = Memory(cfg.db_path)
    audit = AuditLog(cfg.audit_path)
    opt = Optimizer(cfg, prod_suite, executor, memory, audit=audit)
    run = opt.run(baseline_prompt, name="aceitacao")
    return run, prod_suite, memory, audit


# --------------------------------------------------------------------------
# REQUISITO 1: "Calculos e tarefas com respostas verificaveis"
# --------------------------------------------------------------------------
def test_req_calculos_verificaveis(prod_run, registered_suites, executor):
    """Os casos de calculo tem valor esperado calculado, nao arbitrado.

    Verificamos que: (a) a suite contem casos de calculo; (b) o valor esperado
    de cada um e exatamente o que a aritmetica produz; (c) o sistema aprende a
    satisfazer esse contrato partindo do baseline.
    """
    from uaao.graders import safe_eval_arith
    from uaao.types import PromptArtifact

    run, _, _, _ = prod_run
    suite, _ = registered_suites["calc_v1"]
    assert suite.cases, "suite de calculo vazia"

    # (b) o valor esperado bate com a aritmetica
    for case in suite.cases:
        expr = next(
            line.split("=", 1)[1]
            for line in case.input.splitlines()
            if line.startswith("expr=")
        )
        raw = safe_eval_arith(expr)
        numeric_sub = [g for g in case.expected if g["grader"] == "numeric_exact"]
        assert numeric_sub, case.case_id
        target = numeric_sub[0]["expected"]
        assert target == pytest.approx(raw, abs=0.005), case.case_id

    # (c) houve aprendizado real desse contrato
    baseline = evaluate(PromptArtifact(text=run.seed_artifact.text, origin="seed"),
                        suite, executor, split="val")
    final = evaluate(run.final_artifact, suite, executor, split="val")
    assert final.mean_score > baseline.mean_score
    assert final.mean_score == pytest.approx(1.0)


# --------------------------------------------------------------------------
# REQUISITO 2: "Respostas a pedidos ambiguos"
# --------------------------------------------------------------------------
def test_req_pedidos_ambiguos(prod_run, registered_suites, executor):
    """O sistema descobre que, em pedido ambiguo, o correto e perguntar."""
    from uaao.types import PromptArtifact

    run, _, _, _ = prod_run
    suite, _ = registered_suites["ambiguity_v1"]
    assert all(c.critical for c in suite.cases), "ambiguidade deve ser critica"

    baseline = evaluate(PromptArtifact(text=run.seed_artifact.text, origin="seed"),
                        suite, executor, split="val")
    final = evaluate(run.final_artifact, suite, executor, split="val")
    assert baseline.mean_score == pytest.approx(0.0)
    assert final.mean_score == pytest.approx(1.0)
    assert baseline.critical_failures() and not final.critical_failures()

    # a saida final realmente pergunta
    out = executor.execute(run.final_artifact, suite.by_split("val")[0])
    assert "?" in out and "AMBIGUIDADE" in out.upper()


# --------------------------------------------------------------------------
# REQUISITO 3: "Honestidade sobre ferramentas e testes nao executados"
# --------------------------------------------------------------------------
def test_req_honestidade_ferramentas(prod_run, registered_suites, executor):
    """O sistema passa a declarar NAO EXECUCAO em vez de inventar resultado."""
    from uaao.types import PromptArtifact

    run, _, _, _ = prod_run
    suite, _ = registered_suites["honesty_v1"]

    baseline = evaluate(PromptArtifact(text=run.seed_artifact.text, origin="seed"),
                        suite, executor, split="val")
    # o baseline FABRICA: este e o defeito que o ciclo precisa corrigir
    baseline_out = executor.execute(PromptArtifact(text=run.seed_artifact.text, origin="seed"),
                                    suite.by_split("val")[0])
    assert "NOT_EXECUTED" not in baseline_out

    final = evaluate(run.final_artifact, suite, executor, split="val")
    assert baseline.mean_score == pytest.approx(0.0)
    assert final.mean_score == pytest.approx(1.0)
    final_out = executor.execute(run.final_artifact, suite.by_split("val")[0])
    assert "NOT_EXECUTED" in final_out
    # e nao afirma ter consultado fonte nenhuma
    assert "segundo a fonte" not in final_out.lower()


def test_req_honestidade_do_proprio_relatorio(prod_run, registered_suites, cfg):
    """O relatorio declara o que NAO foi executado (nao superestima o resultado)."""
    run, suite, memory, audit = prod_run
    md = build_report_markdown(run, suite.suite_id, suite.sha, cfg, memory, History(memory, audit))
    assert "Limitacoes e o que NAO foi executado" in md
    assert "NAO foi medido" in md
    assert "GPT" in md and "Claude" in md  # diz explicitamente que nao mediu esses
    assert "nenhuma chamada de API" in md.lower() or "Nenhuma chamada de API" in md


# --------------------------------------------------------------------------
# REQUISITO 4: "Regressoes entre versoes"
# --------------------------------------------------------------------------
def test_req_regressao_entre_versoes(prod_run, registered_suites, executor):
    """Candidatos que quebram casos criticos sao BLOQUEADOS, mesmo ganhando media."""
    from uaao.compare import compare
    from uaao.config import SelectionCriteria
    from uaao.evaluate import evaluate
    from uaao.promptspec import set_directive
    from uaao.select import accept_candidate
    from uaao.types import PromptArtifact

    run, _, _, _ = prod_run
    prod = merge_suites([s for s, _ in registered_suites.values()], "p", "1")

    # candidato que "melhora" o formato de calculo mas reintroduz fabricacao
    regressed_text = set_directive(run.final_artifact.text, "ON_MISSING_TOOL", "fabricate")
    regressed = PromptArtifact(text=regressed_text, origin="mutation")

    baseline_val = evaluate(run.final_artifact, prod, executor, split="val")
    cand_val = evaluate(regressed, prod, executor, split="val")
    comp = compare(baseline_val, cand_val)
    decision = accept_candidate(baseline_val, cand_val, comp, SelectionCriteria())
    assert not decision.accepted
    assert "BLOQUEADO" in decision.reason
    assert decision.checks["critical"]["new_critical_failures"]


def test_req_regressao_por_metrica(prod_run, registered_suites, executor):
    """Queda numa metrica especifica tambem reprova o candidato."""
    from uaao.compare import compare
    from uaao.config import SelectionCriteria
    from uaao.evaluate import evaluate
    from uaao.promptspec import set_directive
    from uaao.select import accept_candidate
    from uaao.types import PromptArtifact

    run, _, _, _ = prod_run
    prod = merge_suites([s for s, _ in registered_suites.values()], "p", "1")
    worse = PromptArtifact(text=set_directive(run.final_artifact.text, "LANGUAGE", "auto"))
    base = evaluate(run.final_artifact, prod, executor, split="val")
    cand = evaluate(worse, prod, executor, split="val")
    decision = accept_candidate(base, cand, compare(base, cand), SelectionCriteria())
    assert not decision.accepted
    assert decision.checks["metric_regression"]["violations"]
    assert "language" in decision.checks["metric_regression"]["violations"]


def test_req_nenhuma_regressao_aceita_no_historico(prod_run, memory=None):
    """Auditoria: nenhuma decisao REGISTRADA como aceita pode ter regressao critica."""
    run, _, mem, _ = prod_run
    accepted = [d for d in mem.list_decisions(run.experiment_id) if d["accepted"]]
    assert accepted
    for d in accepted:
        checks = json.loads(d["checks_json"])
        assert not checks["critical"]["new_critical_failures"], d["candidate_sha"]


# --------------------------------------------------------------------------
# REQUISITO 5: "Persistencia da memoria"
# --------------------------------------------------------------------------
def test_req_persistencia_da_memoria(prod_run, cfg):
    """Tudo que o requisito pede fica gravado e sobrevive a reabertura."""
    run, suite, mem, _ = prod_run
    eid = run.experiment_id
    del mem  # fecha o objeto; reabrimos do zero

    m2 = Memory(cfg.db_path)
    ok, msg = m2.integrity_check()
    assert ok, msg

    # identificador e versao do experimento
    exp = m2.get_experiment(eid)
    assert exp.experiment_id == eid and exp.suite_version and exp.executor
    # prompt utilizado (texto integral, byte a byte)
    seed = m2.get_artifact(run.seed_artifact.sha)
    assert seed.text == run.seed_artifact.text
    # conjunto de testes e metricas
    assert suite.sha and m2.evaluation_history(eid)
    # candidatos aceitos e rejeitados
    decisions = m2.list_decisions(eid)
    assert any(d["accepted"] for d in decisions) and any(not d["accepted"] for d in decisions)
    # motivos das decisoes
    assert all(d["reason"] for d in decisions)
    # erros encontrados
    assert isinstance(m2.list_errors(eid), list)
    # data, modelo e configuracao
    row = m2.get_experiment(eid)
    assert row.created_at and row.seed is not None
    assert exp.suite_id


def test_req_consulta_de_historico(prod_run, cfg, tmp_path, capsys):
    """O historico e consultavel pela CLI, com linha do tempo."""
    run, _, _, _ = prod_run
    from uaao.cli import main

    # A CLI resolve caminhos relativos ao --workdir; passamos um config com os
    # caminhos absolutos usados pelo experimento para apontar ao mesmo banco.
    cfg_file = tmp_path / "cli_config.json"
    cfg_file.write_text(json.dumps({
        "db_path": cfg.db_path, "audit_path": cfg.audit_path, "reports_dir": cfg.reports_dir,
    }), encoding="utf-8")

    code = main(["history", "--workdir", str(tmp_path), "--config", str(cfg_file),
                 "--experiment", run.experiment_id, "--timeline"])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "linha do tempo" in out
    assert "decision" in out and "evaluation" in out
    assert run.experiment_id in out


# --------------------------------------------------------------------------
# REQUISITO 6: "Recuperacao apos falhas"
# --------------------------------------------------------------------------
def test_req_recuperacao_apos_falha(cfg, prod_suite, baseline_prompt, executor):
    """Interrompe por orcamento e retoma do ponto correto, sem perder o historico."""
    cfg.limits.max_iterations = 20
    cfg.limits.max_metric_calls = 120
    memory = Memory(cfg.db_path)
    audit = AuditLog(cfg.audit_path)
    opt = Optimizer(cfg, prod_suite, executor, memory, audit=audit)
    first = opt.run(baseline_prompt, name="falha")
    assert "orcamento" in first.stopped_reason
    assert memory.get_experiment(first.experiment_id).status == "interrupted"

    # nova sessao retoma
    cfg.limits.max_metric_calls = 5000
    cfg.limits.max_iterations = 20
    memory2 = Memory(cfg.db_path)
    opt2 = Optimizer(cfg, prod_suite, executor, memory2, audit=AuditLog(cfg.audit_path))
    resumed = opt2.run(baseline_prompt, name="falha",
                       experiment_id=first.experiment_id, resume=True)
    assert resumed.experiment_id == first.experiment_id
    assert resumed.final_val.mean_score >= first.final_val.mean_score
    ok, msg = AuditLog(cfg.audit_path).verify()
    assert ok, msg
    assert memory2.get_experiment(first.experiment_id).status == "finished"


def test_req_executor_quebrado_nao_derruba_o_ciclo(cfg, toy_suite, baseline_prompt):
    """Falha de executor e por CASO: vira dado de diagnostico, nao excecao fatal.

    Recurso de recuperacao: um adaptador defeituoso nao invalida a memoria nem
    deixa o sistema num estado meio-escrito; todo caso fica marcado com erro.
    """
    from uaao.errors import UaaoError

    class ExplodingExecutor:
        name, version, deterministic = "boom", "1", True

        def execute(self, prompt, case):
            raise UaaoError("falha simulada de infraestrutura")

    memory = Memory(cfg.db_path)
    opt = Optimizer(cfg, toy_suite, ExplodingExecutor(), memory, audit=AuditLog(cfg.audit_path))
    run = opt.run(baseline_prompt, name="boom")

    assert run.baseline_val.error_count == len(run.baseline_val.cases)
    assert run.baseline_val.mean_score == 0.0
    assert all(c.error for c in run.final_val.cases)
    # o diagnostico classifica corretamente como problema de infraestrutura
    kinds = set(run.iterations[0].diagnosis.cluster_kinds()) if run.iterations else set()
    assert "erro_de_execucao" in kinds
    # e nada foi aceito (nao ha como melhorar com um executor quebrado)
    assert run.accepted_count() == 0
    ok, msg = AuditLog(cfg.audit_path).verify()
    assert ok, msg


def test_req_erro_de_sistema_e_registrado_e_propaga(cfg, toy_suite, baseline_prompt, executor):
    """Erro real de sistema: registra na memoria, marca 'failed' e NAO engole a excecao."""
    from uaao.errors import UaaoError

    memory = Memory(cfg.db_path)

    def boom(*args, **kwargs):
        raise UaaoError("falha simulada de persistencia")

    memory.save_decision = boom  # type: ignore[assignment]
    opt = Optimizer(cfg, toy_suite, executor, memory, audit=AuditLog(cfg.audit_path))
    with pytest.raises(UaaoError):
        opt.run(baseline_prompt, name="boom")

    eid = memory.list_experiments()[0].experiment_id
    assert memory.get_experiment(eid).status == "failed"
    assert any(e["scope"] == "sistema" for e in memory.list_errors(eid))
    # as avaliacoes ja feitas antes da falha continuam na memoria
    assert memory.evaluation_history(eid)


# --------------------------------------------------------------------------
# REQUISITO 7: "Reversao de alteracoes"
# --------------------------------------------------------------------------
def test_req_reversao(prod_run, cfg):
    """Reverter restaura exatamente o comportamento anterior e preserva a historia."""
    run, suite, _, _ = prod_run
    memory = Memory(cfg.db_path)
    hist = History(memory, audit=AuditLog(cfg.audit_path))

    # comportamento ANTES da reversao
    from uaao.evaluate import evaluate

    class E:
        pass

    from uaao.executors import default_registry

    executor = default_registry().get("policy_reference_v1")
    before = evaluate(run.final_artifact, suite, executor, split="val", ledger=None).mean_score

    result = hist.rollback(run.experiment_id, run.seed_artifact.sha, reason="teste de aceitacao")
    assert result.ok

    active_sha, _ = memory.get_active(run.experiment_id)
    assert active_sha == run.seed_artifact.sha
    after_score = evaluate(memory.get_artifact(active_sha), suite, executor, split="val",
                           ledger=None).mean_score
    assert after_score == pytest.approx(run.baseline_val.mean_score)
    assert after_score < before

    # nada foi apagado: as versoes continuam disponiveis
    versions = hist.versions(run.experiment_id)
    assert len(versions) >= 2
    assert any(v.sha == run.final_artifact.sha for v in versions)
    # e da para voltar de novo
    again = hist.rollback(run.experiment_id, run.final_artifact.sha, reason="reaplicar")
    assert again.ok
    assert memory.get_active(run.experiment_id)[0] == run.final_artifact.sha


# --------------------------------------------------------------------------
# REQUISITO 8: nao afirmar o que nao foi medido
# --------------------------------------------------------------------------
def test_req_nao_inventar_capacidades(prod_run, cfg):
    """Os numeros do relatorio sao rastreaveis ate uma execucao real, com assinatura."""
    run, suite, memory, audit = prod_run
    # a assinatura de determinismo e um hash de saidas REAIS
    assert run.final_val.deterministic_signature()
    assert run.final_val.cases, "sem casos avaliados nao ha numero legitimo"
    assert run.determinism_ok is True
    # o relatorio JSON guarda o contexto de execucao (data, commit, ambiente)
    assert run.context["environment"]["python"]
    # e NAO declara nenhum ganho em modelo de linguagem
    for it in run.iterations:
        for outcome in it.outcomes:
            assert "LLM" not in outcome.decision.reason


def test_req_execucao_offline_sem_rede(prod_run):
    """Nenhuma parte do ciclo toca a rede (politica imutavel)."""
    from uaao.safety import SafetyPolicy

    policy = SafetyPolicy.hardened()
    assert policy.allow_network is False
    with pytest.raises(Exception):
        policy.assert_can("network")
    run, _, _, _ = prod_run
    assert run.ledger_snapshot["cost_units"] == 0.0  # custo real zero
