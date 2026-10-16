# Universal Adaptive AI Optimizer (`uaao`)

**Camada externa de otimização de instruções/prompts para assistentes de IA**, por
experimentação, avaliação objetiva, memória persistente e reuso de resultados
comprovados.

> **Resumo de uma linha:** o `uaao` roda ciclos fechados de
> `BASELINE → AVALIAÇÃO → DIAGNÓSTICO → GERAÇÃO DE CANDIDATOS → TESTE → COMPARAÇÃO → SELEÇÃO → REGISTRO`,
> aceitando um prompt novo **somente** se ele passar em critérios predefinidos —
> e guarda tudo (prompt, métricas, motivos, erros, versões) em SQLite, com reversão.

---

## ⚠️ Leia isto primeiro: o que este projeto **não** faz

Afirmações não verificadas são o principal risco deste tipo de projeto, então
começamos pelo que é falso:

| Não faz | Por quê |
|---|---|
| ❌ **Não modifica pesos** de modelos | Não existe API/mecanismo para isso aqui. Nenhum treino, nenhum fine-tuning, nenhuma GPU. |
| ❌ **Não altera a memória interna nem as instruções** de plataformas externas | Isso exigiria uma API de escrita da plataforma. O `uaao` produz *artefatos de prompt* que **você** aplica onde quiser. |
| ❌ **Não chama LLM algum** (nesta versão) | Decisão explícita do usuário: modo *determinístico*. Não havia chave nem conectividade para APIs de modelo no ambiente de desenvolvimento, e o projeto **não embarca** esse código. |
| ❌ **Não acessa a rede** | Política de segurança imutável: `allow_network=False`. |
| ❌ **Não publica, não faz merge, não escreve em serviço externo** | `allow_external_write=False`; backup em Drive é **manual** (comando `export`). |

### O que os números deste projeto medem (e o que não medem)

O `uaao` avalia prompts contra um **executor de referência determinístico**
(`policy_reference_v1`) que lê a política declarada no prompt e obedece a ela de
forma literal. As métricas (formato, precisão, ambiguidade, honestidade,
resistência a injeção) são calculadas por *graders* determinísticos.

- ✅ **Mede:** se o loop de otimização encontra mudanças de política que produzem
  diferença **mensurável, reproduzível e confirmada em holdout**; e se os critérios
  de aceitação **rejeitam** candidatos ruins (inclusive os que melhoram a média).
- ❌ **Não mede:** a qualidade de GPT, Claude, Gemini ou qualquer LLM. **Estes
  números não autorizam** a frase "o prompt melhorou o assistente em X%".

Essa separação é o ponto central do projeto: **primeiro** construir e provar o
maquinário de medição, **depois** plugar um modelo real — que é justamente o
ponto de extensão isolado no módulo 9 (`uaao/executors.py`).

---

## Sumário

- [Instalação](#instalação)
- [Uso em 60 segundos](#uso-em-60-segundos)
- [Arquitetura (módulos 1–10)](#arquitetura-módulos-110)
- [Configuração](#configuração)
- [Ciclo automático](#ciclo-automático)
- [Memória, histórico e reversão](#memória-histórico-e-reversão)
- [Limites, custos e concorrência de recursos](#limites-custos-e-concorrência-de-recursos)
- [Segurança](#segurança)
- [Pesquisa técnica (GEPA, DSPy, Self-Refine, TRL)](#pesquisa-técnica)
- [Testes](#testes)
- [Resultados medidos](#resultados-medidos)
- [Limitações conhecidas](#limitações-conhecidas)
- [Google Drive (backup manual)](#google-drive-backup-manual)
- [Como plugar um modelo real depois](#como-plugar-um-modelo-real-depois)

---

## Instalação

**Requisitos:** Python ≥ 3.10. Nada mais.

```bash
cd universal-adaptive-ai-optimizer

# Opção A: usar direto, sem instalar nada
python3 -m uaao doctor

# Opção B: instalar (recomendado para o comando `uaao`)
pip install -e .
uaao doctor
```

### Dependências

**Runtime: zero.** O núcleo usa apenas a biblioteca padrão (`sqlite3`, `json`,
`hashlib`, `ast`, `re`, `statistics`, `argparse`). Isso mantém **custo R$ 0**,
elimina risco de *supply-chain* e faz o sistema rodar em qualquer máquina.

**Desenvolvimento:** `pytest` (opcional, para rodar os 297 testes).

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest tests/ -q
```

---

## Uso em 60 segundos

```bash
# 1. Verificar ambiente, política de segurança e capacidades REAIS
python -m uaao doctor

# 2. Listar e validar as suites embutidas
python -m uaao suites

# 3. Rodar o ciclo completo (todas as 5 suites), com relatório
mkdir -p .uaao
python -m uaao run --workdir .uaao \
    --suite calc_v1 --suite honesty_v1 --suite ambiguity_v1 \
    --suite safety_v1 --suite style_v1 \
    --iterations 12

# 4. Consultar o que aconteceu
python -m uaao versions  --workdir .uaao --experiment latest
python -m uaao history   --workdir .uaao --experiment latest --timeline
python -m uaao show      --workdir .uaao --experiment latest

# 5. Reverter para uma versão anterior (nada é apagado)
python -m uaao rollback  --workdir .uaao --experiment latest \
    --to previous --reason "revisar antes de aplicar"

# 6. Confirmar que a trilha de auditoria não foi adulterada
python -m uaao verify-audit --workdir .uaao

# 7. Exportar JSON para backup manual (Drive)
python -m uaao export    --workdir .uaao --experiment latest --out backup.json
```

Toda saída de artefato fica sob `--workdir`: banco `uaao_memory.sqlite3`,
`reports/<experimento>.md`, `reports/<experimento>.json`, `audit/audit.jsonl`.

---

## Arquitetura (módulos 1–10)

Cada módulo pedido na especificação existe como arquivo separado, com contrato
explícito e testes próprios:

| # | Módulo | Arquivo | Responsabilidade |
|---|---|---|---|
| 1 | Execução de tarefas de teste | `uaao/executors.py` | Registry com *allowlist* + executor determinístico que interpreta a política do prompt. |
| 2 | Avaliação com métricas por tarefa | `uaao/evaluate.py` + `uaao/graders.py` | 15 graders objetivos (`json_fields`, `numeric_exact`, `honesty`, `ambiguity_handling`, `injection_resisted`, `composite`, …). Erro nunca vira exceção silenciosa: vira caso com score 0 + `error`. |
| 3 | Geração de candidatos | `uaao/propose.py` | 5 classes de operador (cirúrgico, combinação, varredura, busca de valor, hipótese em prosa) com justificativa por candidato e seleção **diversa** por rodízio. |
| 4 | Comparação entre versões | `uaao/compare.py` | Comparação **pareada por caso**, teste de sinais exato, IC bootstrap com semente fixa, tabela de deltas por métrica. |
| 5 | Seleção com proteção contra regressão | `uaao/select.py` | 6 critérios cumulativos (crítico, margem, métrica, caso, significância, amplitude). Rejeita por padrão: aceitar exige evidência. |
| 6 | Memória persistente em SQLite | `uaao/memory.py` | 9 tabelas, WAL + `synchronous=FULL`, migrações incrementais, verificação de integridade por hash, redação de segredos. |
| 7 | Histórico e versionamento | `uaao/history.py` | Linhagem até a semente, linha do tempo unificada, `diff` entre versões, **rollback** que não apaga nada. |
| 8 | Relatórios de resultados | `uaao/report.py` | Markdown + JSON, com seção obrigatória de limitações e do que **não** foi executado. |
| 9 | Adaptadores opcionais p/ modelos e APIs | `uaao/executors.py` (`Executor` Protocol, `ExecutorRegistry`) | Interface pronta para um adaptador de API/modelo. **Nenhum código de rede embarcado** (ver "Como plugar um modelo real depois"). |
| 10 | Configuração de limites, custos, tentativas e permissões | `uaao/config.py` + `uaao/safety.py` | `Limits`, `CostModel`, `SelectionCriteria`, `SafetyPolicy` imutável, `BudgetLedger`. |

Documentos de apoio: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) ·
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
[`docs/RESEARCH.md`](docs/RESEARCH.md) ·
[`docs/SECURITY.md`](docs/SECURITY.md) ·
[`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) ·
evidência da execução real em [`docs/evidencias/`](docs/evidencias/) ·
exemplos em [`examples/`](examples/)

### Fluxo de dados

```
TaskSuite (train/val/holdout)
        │
        ├─ train ──► diagnose ──► clusters de falha ──► propositor ──► candidatos
        │                                                                  │
        └─ val ─────► evaluate(candidato) ⇄ evaluate(ativo) ──► compare ────┤
                                                                           ▼
                                                        select.accept_candidate
                                                     (guarda crítica + margem +
                                                      não-regressão + significância)
                                                                           │
                                            aceito ──► vira o novo ativo ───┤
                                            rejeitado ──► motivo gravado ───┤
                                                                           ▼
                                          holdout: confirmação final (nunca usado na seleção)
```

---

## Configuração

Precedência: `defaults` < `arquivo JSON` < `variáveis de ambiente UAAO_*`.

```bash
python -m uaao run --config examples/config.example.json --suite calc_v1
UAAO_LIMITS__MAX_ITERATIONS=3 UAAO_SELECTION__MIN_IMPROVEMENT=0.05 python -m uaao run ...
```

Exemplo (`examples/config.example.json`):

```json
{
  "limits": {
    "max_iterations": 12,
    "max_candidates_per_iteration": 6,
    "max_metric_calls": 5000,
    "max_retries": 3,
    "max_wall_seconds": 900
  },
  "costs": { "max_cost_units": 100.0, "cost_per_metric_call": 0.0 },
  "selection": {
    "min_improvement": 0.02,
    "block_on_critical_regression": true,
    "require_significance": true,
    "significance_alpha": 0.05,
    "min_decided_pairs": 8,
    "per_case_regression_tolerance": 0.0,
    "max_metric_regression": 0.0
  },
  "db_path": "uaao_memory.sqlite3",
  "reports_dir": "reports",
  "audit_path": "audit/audit.jsonl",
  "random_seed": 1729
}
```

**Chaves de segurança são recusadas por construção.** Um arquivo ou variável de
ambiente que tente `allow_network`, `allow_external_write`,
`allow_self_modification`, `allow_code_execution`, `allow_subprocess` ou
`use_holdout_for_selection=true` **aborta com erro** (`SafetyViolation`) — o
sistema não pode afrouxar as próprias guardas.

---

## Ciclo automático

1. **BASELINE** — o prompt original é gravado como artefato imutável e avaliado
   em treino/validação/holdout. Ele **nunca é modificado**; melhorias são artefatos
   novos com `parent_sha` apontando para o anterior.
2. **DIAGNÓSTICO** — falhas da **divisão de treino** são classificadas em causas
   (formato, precisão, ambiguidade, fabricação, injeção, idioma, concisão…), com
   os casos que sustentam cada conclusão. Causas não reconhecidas **não** geram ação.
3. **GERAÇÃO** — operadores de mutação propõem candidatos a partir do diagnóstico,
   cada um com justificativa textual. A seleção é por rodízio de classes, para que
   nenhuma hipótese forte seja sistematicamente descartada pelo teto de candidatos.
4. **TESTE + COMPARAÇÃO** — cada candidato é avaliado na **validação** e comparado
   de forma pareada com o ativo.
5. **SELEÇÃO** — aceito só se passar em **todos** os critérios. Rejeitado sai com
   motivo explícito.
6. **REGISTRO** — decisão, avaliações, candidato (aceito **ou** rejeitado),
   iterações e erros vão para o SQLite; tudo é encadeado na trilha de auditoria.
7. **HOLDOUT** — ao final, o campeão é medido na divisão que **nunca** participou
   da seleção. Se o ganho não replicar, o relatório diz isso explicitamente
   (possível *overfit* de validação).

Os três critérios que mais "seguram" candidatos, na prática:

- **guarda crítica** — nenhum caso `critical=true` (honestidade, ambiguidade,
  segurança) pode passar a falhar, **nem** que a média suba;
- **não-regressão por métrica e por caso** — ganho médio não compra perda local;
- **significância** — teste de sinais exato, com uma guarda de **poder
  estatístico**: com poucos pares decididos o teste é marcado como *não avaliado*
  (nunca como aprovação silenciosa), porque com `n < 6` é impossível atingir
  `p < 0.05` e rejeitar por isso confundiria "sem evidência" com "sem poder".

---

## Memória, histórico e reversão

O SQLite guarda **exatamente** o que a especificação pede:

| Requisito | Onde |
|---|---|
| Identificador e versão do experimento | `experiments` (id, nome, suite, versão, sha, status, seed, commit) |
| Prompt utilizado | `artifacts` (texto integral + hash + proveniência) |
| Conjunto de testes e métricas | `evaluations` (suite_sha, split, executor) + `case_results` (score por caso e grader) |
| Erros encontrados | `errors` (escopo, mensagem, iteração) |
| Candidatos rejeitados **e** aceitos | `decisions` (todos, com motivo) + `artifacts` (o texto de cada um) |
| Motivos das decisões | `decisions.reason` + `decisions.checks_json` (evidência completa) |
| Data, modelo e configuração | `experiments.created_at/config_json/executor` + contexto no relatório (commit, Python, plataforma) |

**Reversão**: `rollback` move o ponteiro `active_artifact`. As versões continuam
todas lá, indexadas por `parent_sha`, com a linhagem completa até a semente.
Reversão é **aditiva**, nunca destrutiva — e também é auditada.

```bash
python -m uaao versions --experiment latest          # lista com score de validação
python -m uaao diff --a 938ef38acc6b --b bff3d9c20461  # o que mudou na política
python -m uaao rollback --experiment latest --to previous --reason "..."
```

---

## Limites, custos e concorrência de recursos

`BudgetLedger` cobra **cada** chamada de métrica e interrompe ao estourar:

| Limite | Efeito |
|---|---|
| `max_metric_calls` | Aborta o ciclo limpamente; resultados parciais reais continuam no relatório. |
| `max_retries` | Teto de tentativas (para adaptadores com falha transitória). |
| `max_wall_seconds` | Interrompe por tempo. |
| `max_cost_units` | **Já existe e é testado hoje**, antes de qualquer API paga ser plugada. |

Se o orçamento acabar, o experimento é marcado `interrupted`, o motivo é gravado,
e o relatório informa que os números finais vêm da **última medição real** — nunca
de uma reexecução imaginária pós-orçamento. E o ciclo pode ser **retomado**:

```bash
python -m uaao run --workdir .uaao --suite calc_v1 \
    --resume-experiment exp-xxxxxxxx
```

**Custo real hoje: R$ 0,00.** Sem rede, sem API, sem GPU. O `CostModel` existe
para que o teto seja validado *antes* de haver custo (ver `docs/SECURITY.md`).

---

## Segurança

Resumo; detalhes em [`docs/SECURITY.md`](docs/SECURITY.md).

- **Controles de segurança imutáveis.** `SafetyPolicy` é `frozen` e recusa ser
  construída com capacidades perigosas. O otimizador **não tem referência** a ela:
  não existe caminho de código para o sistema alterar as próprias guardas.
- **Segredos**: apenas via variáveis de ambiente. O código nunca lê chaves;
  `redact()` limpa log/DB/relatório e há um teste que varre **o repositório
  inteiro** procurando padrões de credencial (está passando: 0 ocorrências).
- **Conteúdo não confiável**: suites, arquivos e prompts carregados passam por
  `UntrustedContent` (truncagem, limpeza de caracteres de controle, detecção de
  padrões de injeção em **inglês e português**). É *dado*, nunca instrução.
- **Sem `eval` de dado externo**: a aritmética usa um avaliador de AST restrito
  que rejeita nomes, chamadas, atributos e expoentes abusivos.
- **Sem execução de código de terceiros**: nenhum plugin dinâmico, nenhum
  `pip install` em tempo de execução, nenhum `import` de repositório.
- **Trilha de auditoria** JSONL encadeada por hash — `verify-audit` detecta
  edição e remoção de registros (limitações declaradas no doc).

---

## Pesquisa técnica

Consultei a documentação oficial e o código-fonte dos quatro projetos citados.
Resumo do veredito (análise completa em [`docs/RESEARCH.md`](docs/RESEARCH.md)):

| Projeto | Licença | O que foi aproveitado | Instalado? |
|---|---|---|---|
| **GEPA** | MIT | *Zero deps*. Protocolo de aceitação (`should_accept(proposal, state)`), seleção por diversidade, **separação treino (reflexão) / validação (seleção)**. | ❌ Não (exige LLM para refletir) |
| **DSPy** | MIT | Contrato de *métrica* por tarefa (`metric(example, pred)`) e a noção de assinatura tipada. | ❌ Não (dependências pesadas) |
| **Self-Refine** | Apache-2.0 | O laço gerar → *feedback* → refinar, que aqui roda com **diagnóstico determinístico** em vez de LLM. | ❌ Não (código de pesquisa) |
| **TRL** | Apache-2.0 | **Nada.** Ajusta pesos (SFT/DPO/RL) e exige `torch>=2.6`: incompatível com o escopo e com o ambiente (sem GPU). | ❌ Não |

Nenhuma biblioteca foi instalada — os conceitos foram reimplementados sem
dependências, e o motivo está documentado caso a caso.

---

## Testes

```bash
.venv/bin/python -m pytest tests/ -v
```

**297 testes, 297 passando** (`pytest` 9.1.1, Python 3.11.2, ~6 s). Inclui os
testes de aceitação exigidos na especificação:

| Requisito da especificação | Arquivo/tese |
|---|---|
| Cálculos e tarefas com respostas verificáveis | `test_graders.py`, `test_acceptance.py::test_req_calculos_verificaveis` |
| Respostas a pedidos ambíguos | `test_acceptance.py::test_req_pedidos_ambiguos` |
| Honestidade sobre ferramentas e testes não executados | `test_acceptance.py::test_req_honestidade_ferramentas` |
| Regressões entre versões | `test_compare_select.py`, `test_acceptance.py::test_req_regressao_*` |
| Persistência da memória | `test_memory.py`, `test_acceptance.py::test_req_persistencia_da_memoria` |
| Recuperação após falhas | `test_optimizer_cycle.py::test_budget_exhaustion_*`, `test_req_recuperacao_apos_falha` |
| Reversão de alterações | `test_history_rollback.py`, `test_acceptance.py::test_req_reversao` |

Relatório detalhado — incluindo **os defeitos reais que os testes encontraram e
como foram corrigidos** — em [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md).

---

## Resultados medidos

Execução real deste repositório (duas vezes, resultados idênticos), com as 5
suites agregadas (51 casos: 32 treino / 13 validação / 6 holdout):

| Divisão | Papel | Baseline | Final | Δ |
|---|---|---|---|---|
| Treino | orienta o diagnóstico | 0.0816 | **1.0000** | +0.9184 |
| **Validação** | **decide a seleção** | 0.0897 | **1.0000** | **+0.9103** |
| **Holdout** | **confirmação independente** | 0.1085 | **1.0000** | **+0.8915** |

- 13 candidatos testados, **6 aceitos, 7 rejeitados com motivo registrado**;
- 403 chamadas de métrica, ~0,2 s de tempo de parede, **custo R$ 0,00**;
- determinismo verificado (duas execuções → mesma assinatura `ff7702dbc2a6`);
- as diretivas descobertas foram `OUTPUT_FORMAT=json_object`,
  `ROUND_DECIMALS=2`, `ON_AMBIGUOUS=ask_clarification`,
  `ON_MISSING_TOOL=report_not_executed`, `ON_UNTRUSTED_CONTENT=treat_as_data`,
  `LANGUAGE=pt-BR`, `MAX_WORDS=40`, `REFUSAL_CODE=POL-REFUSE`.

Candidatos rejeitados são o resultado mais informativo: `LANGUAGE=auto` foi
**bloqueado** por falha em casos críticos; `MAX_WORDS=unlimited` caiu de 1.0000
para 0.9744 com **regressão na métrica `max_words`**; `ON_AMBIGUOUS=guess` caiu
para 0.8718. Veja tudo em `reports/<experimento>.md`.

> Reprodução: `python -m uaao run --workdir .uaao --suite calc_v1 --suite honesty_v1 --suite ambiguity_v1 --suite safety_v1 --suite style_v1 --iterations 12`

---

## Limitações conhecidas

Declaradas de propósito — todas verificáveis no código:

1. **Não mede LLM real.** É o limite central e está no topo deste README.
2. **O conjunto de hipóteses é finito e humano.** O propositor não *inventa*
   diretivas: ele testa valores de um schema declarado (`uaao/promptspec.py`) e
   hipóteses de uma tabela (`PREFERRED_VALUES`). O que o sistema **prova** é o
   maquinário de *seleção e verificação* (rejeitou 7 de 13 candidatos, incluindo
   um que melhorava a média), não a descoberta de algo inédito.
3. **O diagnóstico cobre classes de falha previstas.** Causa não reconhecida vira
   `falha_nao_classificada` e **não** gera ação automática — por desenho, para não
   propor mudanças às cegas.
4. **Suites pequenas têm pouco poder estatístico.** O critério de significância é
   marcado como *não avaliado* nesses casos (nunca como aprovado), e a decisão
   fica com margem + não-regressão + guarda crítica. Documentado em
   `docs/TEST_REPORT.md`.
5. **A cadeia de auditoria não detecta truncamento no fim do arquivo.** Hash
   encadeado sem âncora externa não percebe a remoção da *última* linha
   (remover do meio ou editar, sim). Mitigação sugerida: publicar o hash final
   fora do arquivo.
6. **Detecção de injeção é lexical** (regex en/pt). Ataques parafraseados podem
   escapar. É uma heurística de triagem, não um classificador.
7. **Um adaptador de API pago ainda não existe** (decisão de escopo). O modelo de
   custo, os limites e o protocolo estão prontos e testados.

---

## Google Drive (backup manual)

O conector do Google Drive **está disponível** nesta sessão (upload, criação de
arquivo, permissões). Ainda assim o `uaao` **não escreve** no Drive: a política
proíbe escrita externa e não há como auditar isso de dentro do código.

Fluxo recomendado (explícito, com revisão humana):

```bash
python -m uaao export --experiment latest --out backup.json
```

Depois envie `backup.json` e/ou `reports/*.md` pelo conector de Drive, de forma
consciente. **Não use o Drive como banco transacional** e **não envie dados
sensíveis** — o `export` já passa por `redact()`, mas a triagem humana continua
sendo sua.

---

## Como plugar um modelo real depois

O ponto de extensão é **único e pequeno**: implemente o Protocol `Executor`.

```python
from uaao.executors import ExecutorInfo  # e registre em um ExecutorRegistry

class MeuAdaptadorDeAPI:
    name = "openai_x"          # aparece no relatório e na memória
    version = "1.0.0"
    deterministic = False      # <<< isto exige permissão EXPLÍCITA de rede
    # execute(self, prompt, case) -> str
```

O que muda (e já está previsto):

1. `deterministic = False` → `assert_executor_allowed` exige `allow_network`.
   Hoje a `SafetyPolicy` recusa isso por construção: a decisão de ligar a rede é
   **sua**, numa revisão consciente — não um efeito colateral de configuração.
2. A chave vem de variável de ambiente (`OPENAI_API_KEY`), **nunca** do repositório.
3. Ajuste `costs.cost_per_metric_call` e `costs.max_cost_units` para o preço real:
   o teto passa a valer automaticamente.
4. `max_retries` cobre falhas transitórias; a taxa de erro vira dado de
   diagnóstico (`erro_de_execucao`), sem contaminar os scores.
5. Considere `require_significance` com `min_decided_pairs` adequado ao tamanho da
   validação, e **mantenha um holdout intocado** — é o que separa "melhorou na
   validação" de "melhorou de verdade".

Enquanto isso, todo o resto (memória, critérios, relatórios, reversão, limites)
já está exercitado e provado pelos testes.

---

## Estrutura do repositório

```
universal-adaptive-ai-optimizer/
├── README.md                  ← você está aqui
├── pyproject.toml             ← zero dependências de runtime
├── uaao/                      ← pacote (núcleo, stdlib apenas)
│   ├── safety.py              ← política imutável, orçamentos, auditoria, redação
│   ├── config.py              ← limites, custos, critérios (recusa chaves inseguras)
│   ├── types.py               ← tipos de domínio imutáveis
│   ├── graders.py             ← 15 métricas objetivas + AST aritmético seguro
│   ├── executors.py           ← módulo 9: registry + executor determinístico
│   ├── evaluate.py            ← módulo 2
│   ├── diagnose.py            ← diagnóstico a partir do treino
│   ├── propose.py             ← módulo 3
│   ├── compare.py             ← módulo 4
│   ├── select.py              ← módulo 5
│   ├── memory.py              ← módulo 6 (SQLite)
│   ├── history.py             ← módulo 7 (versionamento/rollback)
│   ├── report.py              ← módulo 8
│   ├── optimizer.py           ← o ciclo
│   ├── cli.py / __main__.py   ← interface de linha de comando
│   └── suites/*.json          ← 5 suites (geradas e verificadas)
├── tools/make_suites.py       ← gerador+verificador das suites
├── tests/                     ← 297 testes
├── docs/                      ← ARCHITECTURE, RESEARCH, SECURITY, TEST_REPORT
└── examples/                  ← config de exemplo
```

## Licença

MIT (ver `LICENSE`).
