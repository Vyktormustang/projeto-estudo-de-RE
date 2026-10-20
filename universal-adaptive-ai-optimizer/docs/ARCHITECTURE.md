# Arquitetura — Universal Adaptive AI Optimizer

## 1. Princípio organizador

O `uaao` é uma **camada externa**. Ele não é um modelo, não é um *plugin* e não
tem privilégio nenhum dentro de nenhuma plataforma. Ele faz três coisas:

1. **mede** o comportamento de um artefato textual (prompt/instrução) contra uma
   suite de tarefas com respostas verificáveis;
2. **decide**, com critérios explícitos, se uma versão nova é melhor que a atual;
3. **lembra** de tudo, de forma que a decisão seja auditável e reversível.

Isso é deliberadamente conservador. O maior risco de um projeto com esse nome é
prometer "melhora automática de IA" e entregar números não verificáveis. A
arquitetura foi desenhada para tornar essa promessa **estruturalmente impossível**:
todo número do relatório tem que apontar para uma execução real e determinística.

## 2. Fronteira de confiança (o desenho mais importante do projeto)

```
     ┌─────────────────────────── DADO NÃO CONFIÁVEL ───────────────────────────┐
     │ suites/*.json · arquivos de prompt · saídas de executor · relatórios    │
     └───────────────────────────────────┬─────────────────────────────────────┘
                                         │  UntrustedContent.wrap()
                                         │  (trunca, limpa, detecta injeção,
                                         │   NUNCA interpreta como instrução)
                                         ▼
     ┌─────────────────────────── CÓDIGO CONFIÁVEL ─────────────────────────────┐
     │ graders · compare · select · memory · report                             │
     │ (funções puras, sem rede, sem eval, sem subprocesso)                     │
     └───────────────────────────────────┬─────────────────────────────────────┘
                                         │
              ┌──────────────────────────┴───────────────────────────┐
              ▼                                                      ▼
      SafetyPolicy (frozen, imutável)                        BudgetLedger
      allow_network=False                                    chamadas/tentativas/
      allow_external_write=False                             tempo/custo
      allow_self_modification=False
              ▲
              │  lida por cli.py e optimizer.py — e por NINGUÉM que proponha,
              │  avalie ou selecione. Não existe caminho de código do
              │  otimizador até a política: não dá para afrouxar o que não se alcança.
```

## 3. Módulos e dependências

Grafo de dependência (setas = "importa"), estritamente acíclico:

```
types ─► (nada)
errors ─► (nada)
safety ─► errors
config ─► errors, safety
promptspec ─► (nada)
graders ─► errors
executors ─► errors, graders, promptspec, safety, types
taskset ─► errors, graders, safety, types
evaluate ─► errors, executors, graders, safety, types
diagnose ─► promptspec, types
propose ─► diagnose, promptspec, types
compare ─► types
select ─► compare, config, types
memory ─► errors, safety, types
history ─► errors, memory, promptspec, safety
report ─► config, evaluate, history, memory, optimizer, promptspec, select, types
optimizer ─► compare, config, diagnose, errors, evaluate, executors, history,
             memory, provenance, propose, safety, select, types
cli ─► (tudo acima)
```

**Não há ciclo.** Em particular, `select` não conhece `executors` e `graders` não
conhece `memory`: métrica não grava, seleção não executa. Isso mantém cada peça
testável isoladamente e impede que o otimizador "aprenda" a burlar a própria
medição.

### 3.1 Detalhe por módulo

| Módulo | Entrada | Saída | Invariante |
|---|---|---|---|
| `promptspec` | texto do prompt | `dict[str, str]` de diretivas | Chave/valor fora do schema é **ignorado**, nunca "quase válido". |
| `graders` | `(output, expected, params)` | `(score∈[0,1], passed, details)` | Função pura; erro vira `GraderError` tipado; segurança é binária. |
| `executors` | `(PromptArtifact, TaskCase)` | `str` | Determinístico; erro vira `ExecutorError`; allowlist explícita. |
| `evaluate` | artefato + suite + split | `EvalResult` | Erro de caso **nunca** propaga: vira score 0 + `error`. Cada caso cobra do ledger. |
| `diagnose` | `EvalResult` de treino | `Diagnosis` | Só a divisão de treino é lida. Causa desconhecida não gera ação. |
| `propose` | `Diagnosis` | `[Proposal]` | Todo candidato é justificável e schema-legal; seleção diversa por rodízio. |
| `compare` | 2 `EvalResult` | `Comparison` | Exige **a mesma** suite (senão `ValueError`): comparação pareada ou nada. |
| `select` | baseline + candidato + `Comparison` | `Decision` | Todos os critérios cumulativos + motivo textual + evidência completa em `checks`. |
| `memory` | objetos de domínio | linhas SQLite | Escrita transacional, `redact()` sempre, hash conferido na leitura. |
| `history` | `Memory` | versões/rollback | Append-only: reversão move ponteiro, nunca apaga. |
| `report` | `OptimizationRun` | MD + JSON | Afirma só o medido; seção obrigatória de limitações. |
| `optimizer` | config + suite + executor | `OptimizationRun` | Original imutável; seleção só na validação; holdout intocado até o fim. |

## 4. Modelo de dados (SQLite)

```
experiments ────┬──► artifacts ────┬──► active_artifact (ponteiro de versão)
                │                  └──► (parent_sha: linhagem até a semente)
                ├──► iterations ──► (diagnosis_json, proposals_json, outcome)
                ├──► evaluations ──► case_results (score por caso/grader)
                ├──► decisions     (aceito?, motivo, checks_json, split)
                ├──► errors        (escopo, mensagem, iteração)
                └──► reports       (tipo, caminho)
```

`active_artifact` é o **único** estado mutável de "qual é a versão boa agora".
Todo o resto é histórico imutável. Reverter = uma linha atualizada em
`active_artifact` + um evento na auditoria. Por isso rollback é seguro e barato.

**Migrações**: `PRAGMA user_version` + tabela `MIGRATIONS`. Um banco criado por
uma versão anterior continua válido (testado: a coluna `weight` foi adicionada
assim).

## 5. O ciclo, em termos de informação

```
BASELINE      seed reavaliado em train/val/holdout → 3 EvalResult, active=seed
   │
   ▼
DIAGNÓSTICO   EvalResult(train) → clusters {causa, casos, peso}
   │            pesos: soma de pesos dos casos × 1.25 se crítico
   ▼
GERAÇÃO       clusters → grupos de diretiva → operadores → ≤N candidatos
   │            rodízio entre classes (cirúrgico/combinação/varredura/valor/prosa)
   ▼
TESTE         candidato → EvalResult(val)   [cobra orçamento por caso]
   │
   ▼
COMPARAÇÃO    pareado por case_id: deltas, teste de sinais exato, IC bootstrap
   │
   ▼
SELEÇÃO       1) nenhum caso crítico novo falhando
   │          2) ganho médio ≥ min_improvement
   │          3) nenhuma métrica cai > max_metric_regression
   │          4) nenhum caso cai > per_case_regression_tolerance
   │          5) significância (com guarda de poder estatístico)
   │          6) fração mínima de casos melhorados
   │          → aceito: vira ativo | rejeitado: motivo gravado
   ▼
REGISTRO      decisão + avaliação + artefato + iteração + auditoria (hash chain)
   │
   └──► próxima iteração parte do ativo atual (re-diagnostica)
   │
   ▼
HOLDOUT       campeão medido uma vez, na divisão intocada; divergência é reportada
```

## 6. Decisões de projeto e o que as motivou

### 6.1 Por que o executor é determinístico

Sem LLM acessível no ambiente, havia duas opções honestas: (a) *mockar* um
modelo e reportar números inventados — inaceitável; (b) construir um executor
determinístico **declaradamente de referência**, cujo comportamento é uma função
verificável do prompt. Escolhemos (b), com uma consequência importante: o que se
mede é a **cadeia de medição e decisão**, que é a parte difícil e reutilizável.
Quando um adaptador de modelo real entrar (módulo 9), toda essa cadeia já estará
provada — muda apenas quem produz a saída.

### 6.2 Por que comparar pareado, e não por média

Média de dois conjuntos diferentes mistura efeito do prompt com efeito da
amostra. O `compare` exige a mesma `suite_sha` e casa caso a caso; ganhos e
perdas são contados por **direção**, o que alimenta o teste de sinais. Sem isso,
"0.62 > 0.60" não significaria nada.

### 6.3 Por que a guarda de casos críticos é bloqueante

Um prompt que passa a inventar dados meteorológicos mas acerta o formato dos
cálculos pode ter média melhor. Se isso fosse aceitável, o sistema otimizaria na
direção errada — e o faria de forma silenciosa e cumulativa. A guarda é
bloqueante por desenho, e a decisão registra quais casos dispararam.

### 6.4 Por que a guarda de poder estatístico existe

Com `n` pares decididos, o menor `p` bicaudal possível é `2·0.5^n`. Para `n ≤ 5`
é **impossível** atingir `p < 0.05`. Rejeitar nessa situação confundiria "não há
evidência" com "não há poder para detectar". O critério então é marcado como
`nao_avaliado_poder_insuficiente` — registrado com transparência, nunca como
aprovação silenciosa — e a decisão recai nos critérios de margem,
não-regressão e guarda crítica. Defeito real: antes disso, o ciclo estagnava na
segunda iteração com 14 casos de validação.

### 6.5 Por que a seleção de candidatos é por rodízio

Cortar a lista de candidatos pelo início fazia o operador mais poderoso
(`full_sweep`) nunca ser testado com teto pequeno — o ciclo parava em 0.857 tendo
na mão um candidato capaz de chegar a 1.0. Rodízio entre classes garante que
cada família de hipótese entre na bancada, o que é a mesma intuição de
diversidade que aparece na seleção tipo Pareto do GEPA.

## 7. Como estender

| Quero… | Onde mexer | Cuidado |
|---|---|---|
| Um modelo/API real | Implementar `Executor` e registrar no `ExecutorRegistry` | `deterministic=False` exige `allow_network` explícito (hoje recusado por construção). Chave só por env var. Ajustar `costs`. |
| Uma métrica nova | Adicionar função em `graders.GRADERS` | Devolver score em `[0,1]`; levantar `GraderError` em falha; escrever teste de contrato. |
| Novas diretivas | `promptspec.DIRECTIVE_SCHEMA` | O schema **é** o espaço de busca: valores legais precisam ser explícitos. |
| Um tipo de tarefa novo | Novo `kind` no envelope + handler no executor + suite JSON | Rodar `tools/make_suites.py --check-only` para provar que o alvo atinge 1.0. |
| Um novo critério de aceitação | `select.accept_candidate` | Manter o padrão "rejeitar por falta de evidência"; nunca relaxar guarda crítica por padrão. |
| Outra política de busca | `HeuristicProposer._generate` | Cada candidato precisa de justificativa textual (vai para o relatório). |

## 8. O que este desenho explicitamente **não** cobre

- **Otimização multiobjetivo com Pareto real** (por instância). Implementamos
  diversidade *estrutural* na proposta, não fronteira de Pareto por exemplo. É o
  próximo passo natural se o número de casos crescer.
- **Paralelismo.** A execução é sequencial; o orçamento assume isso. Um executor
  remoto pediria concorrência com controle de gasto — hoje fora de escopo.
- **Reescrita livre do prompt por LLM.** O propositor só mexe em diretivas de um
  schema. Um "refletor" LLM exigiria um modelo, que não temos, e abriria a
  questão de validar texto livre contra o schema.
