# Pesquisa técnica — o que foi examinado, aproveitado e recusado

**Método.** Clonei os quatro repositórios citados em 2026-10-16
(`--depth 1`), li README, código-fonte e configuração de dependências, e verifiquei
o que caberia na arquitetura. **Nenhuma biblioteca foi instalada**: quando um
conceito foi adotado, ele foi reimplementado sem dependências. Abaixo está o
motivo de cada decisão, com a evidência.

---

## 1. GEPA — `github.com/gepa-ai/gepa`

**Licença:** MIT. **Versão examinada:** 0.1.4. **Fonte:** clone local + documentação
oficial em `gepa-ai.github.io/gepa/guides/quickstart/`.

### O que ele é
Framework de otimização de *parâmetros textuais* (prompts, código, arquiteturas)
por reflexão com LLM + busca evolutiva com seleção eficiente tipo Pareto. O README
cita "90x mais barato", "35x mais rápido que RL", "100–500 avaliações vs. 5.000–25.000+".

### Evidência relevante para a decisão

| Achado | Evidência no repositório |
|---|---|
| **Núcleo sem dependências** | `pyproject.toml` → `dependencies = []`; os extras (`litellm`, `datasets`, `mlflow`, `wandb`) ficam em `[project.optional-dependencies]`. |
| **Protocolo de aceitação explicitamente separado** | `src/gepa/strategies/acceptance.py` (66 linhas): `AcceptanceCriterion.should_accept(proposal, state) -> bool`, com `StrictImprovementAcceptance` (padrão) e `ImprovementOrEqualAcceptance`. |
| **Seleção de candidato abstraída** | `src/gepa/strategies/candidate_selector.py` (82 linhas): `ParetoCandidateSelector`, `CurrentBestCandidateSelector`, `EpsilonGreedyCandidateSelector`, `TopKParetoCandidateSelector`. |
| **Política de avaliação isolada** | `src/gepa/strategies/eval_policy.py` (64 linhas): `FullEvaluationPolicy.get_eval_batch / get_best_program / get_valset_score`. |
| **Contrato de adaptador enxuto** | `src/gepa/core/adapter.py`: `EvaluationBatch(outputs, scores, trajectories, objective_scores)` e `ProposalFn(candidate, reflective_dataset, components_to_update)`. |
| **Separação treino/validação explícita** | Docstring de `optimize`: "valset: ... used for tracking Pareto scores"; `trainset` orienta a reflexão, `valset` decide. |
| **Propositor plugável sem LLM** | `custom_candidate_proposer` é aceito no lugar do padrão baseado em reflexão. |

### Decisão: **adotar os conceitos, não a dependência**

Adotado (com atribuição nos docstrings):

1. **Critério de aceitação como objeto próprio**, com `should_accept` e motivo de
   rejeição → virou `uaao/select.py::accept_candidate` + `Decision` (com
   `checks` detalhado, mais rico que um booleano).
2. **Seleção diversa em vez de greedy** → virou `HeuristicProposer._diverse_select`
   (rodízio entre classes de operador). Motivo prático: com greedy-por-prefixo, o
   operador mais poderoso nunca era testado e o ciclo estagnava em 0.857.
3. **Treino para diagnosticar, validação para selecionar** → implementado
   literalmente: `diagnose` lê só `train`; `accept_candidate` compara só `val`;
   `holdout` só aparece no fim.

**Não adotado:** a dependência `gepa` em si. Motivo: o propositor padrão precisa de
um `reflection_lm` (ex.: `"openai/gpt-5"`), ou seja, de um LLM e de rede — nenhum
dos dois disponível, e o usuário escolheu explicitamente o modo determinístico.
Instalar 70 MB de código para usar `dependencies = []` não se justifica. O
`custom_candidate_proposer` do GEPA provou que um propositor sem LLM é uma
extensão legítima do desenho, não uma gambiarra.

**O que ficou de fora:** fronteira de Pareto por instância
(`frontier_type='instance'|'objective'|'hybrid'|'cartesian'`) e o operador de
*merge* entre candidatos (`src/gepa/proposer/merge.py`, 404 linhas). Valiosos se o
número de casos de validação crescer; hoje a validação é pequena e o ganho não
compensaria a complexidade.

---

## 2. DSPy — `github.com/stanfordnlp/dspy`

**Licença:** MIT.

### O que ele é
Framework para programar (não "promptar") sistemas com LLM: assinaturas tipadas
(`"question -> answer"`), módulos (`ChainOfThought`, `Predict`) e otimizadores
(`dspy.GEPA`, `MIPROv2`, `BootstrapFewShot`).

### Evidência

| Achado | Evidência |
|---|---|
| Métrica é uma função do usuário sobre `(example, pred)` | Documentação oficial do `dspy.GEPA`: `def metric_with_feedback(example, pred, trace=None)`, retornando `dspy.Prediction(score=..., feedback=...)`. |
| Feedback textual é insumo do otimizador | O guia do GEPA enfatiza "feedback metrics that provide textual explanations, not just scores". |
| Exemplos com entradas separadas | `dspy.Example(question=..., answer=...).with_inputs("question")`. |
| Otimizadores exigem LM configurado | `dspy.configure(lm=dspy.LM(...))` é pré-requisito de qualquer otimizador. |

### Decisão: **adotar o contrato de métrica, não o framework**

Adotado: a ideia de que a métrica é **por tarefa e definida pelo usuário**, e não
uma pontuação genérica. No `uaao` isso é `graders.py` (15 graders) + a escolha do
grader **dentro do caso da suite** — o candidato não escolhe como será avaliado,
o que é uma garantia mais forte que a do DSPy (lá a métrica é do programa).

Também adotado o conceito de *separar entrada de rótulo*: `TaskCase.input` vs
`TaskCase.expected`, com `split` em tags — o sistema nunca passa `expected` ao
executor (verificado por construção: `run_case(executor, prompt, case)` só entrega
o caso, e o executor lê `case.input`).

**Não adotado:** o framework. Dependências de `dspy` incluem `litellm`, `optuna`,
`pydantic`, `datasets`, `ujson`, etc. — e todo otimizador real exige um LM.
Usar `dspy` sem LM configurado não roda nada. Custo/benefício desfavorável para
uma camada que precisa ser auditável e offline.

**O que ficou de fora:** `BootstrapFewShot` (seleção automática de exemplos
poucos-para-muitos). Interessante, mas exige pool de demonstrações e um LM para
gerá-las.

---

## 3. Self-Refine — `github.com/madaan/self-refine`

**Licença:** Apache-2.0.

### O que ele é
Código de **pesquisa** que acompanha o paper *Self-Refine: Iterative Refinement
with Self-Feedback* (arXiv 2303.17651). O laço é: gerar → dar feedback → refinar →
repetir, usando **o mesmo LLM** para tudo.

### Evidência

| Achado | Evidência |
|---|---|
| É um conjunto de experimentos, não uma biblioteca | `src/acronym/{run,task_iterate,feedback,task_init}.py`, `src/commongen/{run,eval,feedback}.py`, `src/gsm8k/`, `colabs/` — cada tarefa tem seu próprio `run.py`. |
| Cada tarefa tem seu próprio avaliador | `src/*/eval.py` por dataset (acro, commongen, gsm, ...). |
| Exige LLM em todas as etapas | `run.py` de cada tarefa importa e chama um modelo (`gpt-4`, etc.). |
| Feedback vem do próprio modelo | `feedback.py` faz o LLM criticar a própria saída. |

### Decisão: **adotar a forma do laço, recusar o mecanismo**

Adotado: a **estrutura** gerar → *feedback* → refinar, que no `uaao` é
`diagnose → propose → evaluate → select`. A diferença é de fonte de sinal:

| | Self-Refine | `uaao` |
|---|---|---|
| Quem dá o feedback | o mesmo LLM | graders determinísticos sobre casos de treino |
| Reprodutível? | não (amostragem) | sim (assinatura verificada) |
| Precisa de modelo? | sim | não |

O `uaao` é, nesse sentido, um "Self-Refine com feedback objetivo". Isso é
justamente o que a especificação pediu: "testes determinísticos sempre que
possível, em vez de depender exclusivamente de um avaliador baseado em IA".

**Não adotado:** o repositório em si (não é empacotável; é experimento por
tarefa). Instalar não traria nenhuma função reutilizável.

---

## 4. TRL — `github.com/huggingface/trl`

**Licença:** Apache-2.0. **Versão examinada:** a do `main` em 2026-10-16.

### O que ele é
"Train transformers with reinforcement learning": SFT, DPO, GRPO, PPO, reward
modeling — **ajuste de pesos** de modelos.

### Evidência

```
[project]
dependencies = [
  "accelerate>=1.10.1", "datasets>=4.7.0", "huggingface_hub>=0.34.0",
  "jinja2", "numpy>=1.26.0", "packaging>20.0", "pandas>=2.1.1",
  "psutil>=5.9.4", "pyarrow>=21.0.0", "pyyaml>=6.0.1",
  "torch>=2.6.0",          # torch.accelerator, FSDP2
  "transformers>=4.56.2",
]
```

### Decisão: **recusado por completo — incompatível por definição**

Quatro motivos independentes, qualquer um deles suficiente:

1. **Faz exatamente o que a especificação proíbe** ("Não afirme que pode modificar
   os pesos... sem uma API ou mecanismo que permita isso"). O `uaao` não tem peso
   nenhum para ajustar; é camada externa.
2. **Exige GPU e memória que o ambiente não tem.** Verificado: **2 vCPU, 3,8 GB de
   RAM, nenhuma GPU** (`nvidia-smi` ausente). `torch>=2.6` sozinho ocupa mais que
   a RAM disponível na instalação.
3. **Sem conectividade com o Hugging Face Hub.** Testado: `huggingface.co` →
   inalcançável (só `pypi.org`, `github.com`, `registry.npmjs.org` respondem).
   Não haveria como baixar pesos base.
4. **Custo e tempo desproporcionais** ao objetivo verificável da v1 (provar o
   maquinário de medição).

Instalar TRL seria adicionar ~2 GB de dependências para não usar nada. A decisão
fica registrada aqui justamente para que ninguém "resolva" instalar depois sem
reler isto.

---

## 5. Síntese

| Projeto | Conceito aproveitado | Dependência instalada | Motivo da recusa |
|---|---|---|---|
| GEPA | aceitação como protocolo; diversidade na seleção; treino≠validação | ❌ | propositor padrão exige LLM/rede |
| DSPy | métrica por tarefa; entrada≠rótulo | ❌ | stack pesada; otimizadores exigem LM |
| Self-Refine | forma do laço gerar→feedback→refinar | ❌ | é código de pesquisa, não biblioteca |
| TRL | — | ❌ | ajusta pesos; sem GPU nem Hub; fora de escopo |

**Total de dependências de runtime do `uaao`: zero.**

### O que a pesquisa mudou, concretamente, no projeto

1. O critério de aceitação virou um objeto auditável com motivo, em vez de um
   `if score > best` (influência do `AcceptanceCriterion` do GEPA).
2. O propositor passou a garantir **diversidade estrutural** na seleção de
   candidatos (influência da seleção tipo Pareto do GEPA) — corrigiu uma
   estagnação real em 0.857.
3. A separação das três divisões ficou **explícita no código** e testada
   (`test_decisions_only_use_validation_split`, `test_holdout_confirms_the_improvement`)
   em vez de ser só uma boa intenção.
4. O diagnóstico ganhou justificativa obrigatória por candidato (influência do
   *reflective dataset* do GEPA e do feedback do Self-Refine) — no `uaao` o
   "texto de reflexão" é uma frase determinística com os casos que a sustentam.

### Direções que a literatura sugere e que ficaram fora da v1

- **Busca por fronteira de Pareto por instância** (GEPA): natural quando houver
  muitas instâncias de validação com desempenho heterogêneo.
- ***Merge* de candidatos** (GEPA): combinar dois prompts que funcionam em
  subconjuntos diferentes. Hoje o operador `combine_groups` é uma versão grosseira
  disso.
- **Reflexão por LLM** (GEPA/Self-Refine/DSPy): é a extensão de maior valor
  assim que houver um modelo acessível — e a arquitetura já tem o ponto de
  entrada isolado (`Executor` no módulo 9 + `HeuristicProposer` trocável).
- **Few-shot bootstrap** (DSPy): exigiria pool de exemplos e um modelo.
