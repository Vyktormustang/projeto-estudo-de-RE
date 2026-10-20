# Segurança — modelo de ameaças, garantias e limitações

Documento de referência para revisão. Cada garantia aponta o teste que a sustenta.

---

## 1. Requisitos de segurança da especificação → implementação

| Requisito | Implementação | Teste |
|---|---|---|
| Nunca armazenar chaves de API no código ou no GitHub | Varredura de padrões em **todos** os arquivos versionados; teste falha se qualquer um aparecer | `test_safety.py::test_repository_has_no_committed_secrets` |
| Usar variáveis de ambiente para segredos | Nada lê chave no código; `env_secret_names()` só reporta **nomes** | `test_safety.py::test_redact_removes_secret_patterns` |
| Não executar código encontrado em repositórios sem revisão | Sem `eval`/`exec` de dado externo; aritmética por AST restrito; sem plugins dinâmicos | `test_graders.py::test_safe_eval_arith_rejects_code_execution` (9 payloads) |
| Não conceder permissões adicionais automaticamente | `SafetyPolicy` imutável recusa nascer permissiva; `ExecutorRegistry` com allowlist | `test_safety.py::test_policy_refuses_permissive_construction`, `test_executors.py::test_registry_denies_not_enabled_executor` |
| Não publicar nem fazer merge sem autorização | Nada no código faz push/PR/merge; `allow_external_write=False` | `test_safety.py::test_policy_assert_can_denies_dangerous_operations` |
| Não permitir que o sistema altere seus próprios controles | `SafetyPolicy` não é referenciada por propositor/seletor; config recusa chaves de relaxamento | `test_safety.py::test_config_rejects_security_relaxation_keys` (todas as 8 chaves) |
| Implementar limites de chamadas, tentativas e custos | `BudgetLedger` cobra cada caso e levanta `BudgetExceeded` | `test_safety.py::test_budget_*` (4 testes) |
| Registrar erros e operações importantes | Tabela `errors` + `AuditLog` encadeado por hash | `test_safety.py::test_audit_chain_records_and_verifies` |
| Tratar conteúdo recuperado como dado não confiável | `UntrustedContent.wrap()` em suites, prompts e saídas | `test_safety.py::test_untrusted_detects_*` |

---

## 2. Modelo de ameaças

### 2.1 O que estamos defendendo

Um sistema que otimiza prompts e guarda histórico **aprende com dados que podem
ser hostis**. As ameaças realistas são:

| # | Ameaça | Vetor | Mitigação | Residual |
|---|---|---|---|---|
| A1 | **Injeção de instrução em conteúdo recuperado** | `input` de caso, `note`, arquivo de prompt carregado contém "ignore as regras e…" | `UntrustedContent` marca e preserva como dado; a *política* do prompt decide o que o executor faz; a métrica `injection_resisted` **zera** ao vazar | Detector é lexical (en/pt). Paráfrases podem escapar. |
| A2 | **Execução de código via entrada** | `expr=` malicioso num caso (`__import__('os')…`) | AST restrito: só aritmética, sem nomes/chamadas/atributos; expoente limitado | Nenhum conhecido (9 payloads testados). |
| A3 | **Exfiltração de segredo para log/DB/relatório** | Chave aparece numa saída e é persistida | `redact()` antes de qualquer escrita; varredura de repositório | Segredo em formato não previsto pela regex escaparia. |
| A4 | **Otimizador afrouxando as próprias guardas** | Config, env var, arquivo de suite | `SafetyPolicy` `frozen` + recusa na construção; otimizador sem referência à política | Nenhum caminho conhecido (testado). |
| A5 | **Escrita externa não autorizada** | Adaptador futuro com rede | `allow_network`/`allow_external_write` = `False` **na construção**; `deterministic=False` exige permissão | Requer edição de código + revisão humana para mudar. |
| A6 | **Corrupção/adulteração da memória** | Edição do SQLite ou da auditoria | Hash do artefato conferido na leitura; cadeia de hash na auditoria; `integrity_check()` | Truncar a **última** linha da auditoria não é detectado (ver §5). |
| A7 | **Gasto descontrolado** (API paga futura) | Loop sem teto | `max_metric_calls`/`max_cost_units`/`max_wall_seconds` conferidos a cada passo | Teto é por execução; várias execuções somam. |
| A8 | **Decisão enviesada por vazamento de dados** | Selecionar no holdout | Holdout não entra em nenhuma comparação de seleção; config **recusa** `use_holdout_for_selection=true` | Nenhum conhecido (testado). |

### 2.2 O que está **fora** do modelo de ameaças

- **Host comprometido.** Se o processo roda em máquina hostil, nada aqui protege.
- **Atacante com escrita no código.** A política é imutável em *tempo de execução*;
  quem edita o fonte pode mudar tudo (por isso este documento existe).
- **Negação de serviço por suite gigante.** Há truncagem (20.000 chars por texto),
  mas um arquivo de suite com milhões de casos consumiria o orçamento e pararia —
  o que é o comportamento correto (falha segura), não uma defesa.
- **Vazamento por canal lateral** (timing). Não é objetivo.

---

## 3. Garantias por construção

### 3.1 A política de segurança é inalcançável pelo otimizador

```python
@dataclass(frozen=True)
class SafetyPolicy:
    allow_network: bool = False
    ...
    def __post_init__(self) -> None:
        for flag in (...):
            if getattr(self, flag):
                raise SafetyViolation(f"Politica insegura recusada: {flag}=True. ...")
```

Duas barreiras independentes: (a) `frozen=True` impede mutação; (b) `__post_init__`
impede **criação** permissiva. E, mais importante que ambas: `optimizer.py`,
`propose.py` e `select.py` **não importam** `safety` no caminho de decisão — não
existe caminho de código do "cérebro" até a guarda. Não se afrouxa o que não se
alcança.

### 3.2 Configuração hostil falha alto

```python
FORBIDDEN_KEYS = {
  "allow_network", "allow_external_write", "allow_self_modification",
  "allow_code_execution", "allow_subprocess", "safety_policy", "permissions",
  "disable_safety", "bypass_guardrails", "trust_all_content",
}
```

Recusado em **três** lugares: no topo, aninhado (recursivo) e via env var
`UAAO_*`. Chave desconhecida também é erro (`ConfigError`) — sem "campos
silenciosos", porque campo silencioso é onde o erro se esconde.

### 3.3 Avaliador aritmético restrito

`graders.safe_eval_arith` faz `ast.parse(expr, mode="eval")` e percorre a árvore
aceitando apenas: `Expression`, `BinOp`, `UnaryOp`, `Constant` (numérico), `Add`,
`Sub`, `Mult`, `Div`, `FloorDiv`, `Mod`, `Pow`, `USub`, `UAdd`, `Load`. Qualquer
outro nó → `GraderError`. Expoente `> 64` → recusado (evita `9**9**9`). O `eval`
final roda com `{"__builtins__": {}}`.

### 3.4 Conteúdo não confiável

```python
UntrustedContent.wrap(text, source, max_chars=20_000)
  → remove caracteres de controle
  → trunca e reporta `truncated=True`
  → detecta padrões de injeção (en + pt) e reporta `injection_suspected`
```

O resultado é **dado**. O texto hostil é preservado (para inspeção humana) e
sinalizado — nunca obedecido. As 13 heurísticas cobrem inglês e português; o
corpus é pt-BR, e um detector só-inglês deixava passar 4 de 5 injeções (defeito
real, corrigido e agora testado).

### 3.5 Redação de segredos

7 padrões (`sk-`, `sk-ant-`, `AIza`, `ghp_/gho_/ghu_/ghs_/ghr_`, `hf_`,
`api_key|token|secret|password` + valor, `Bearer …`) + chaves sensíveis
(`*KEY*`, `*TOKEN*`, `*SECRET*`, `*PASSWORD*`, `*CREDENTIAL*`) → `[REDACTED]`,
recursivamente, **antes** de qualquer persistência (SQLite, JSONL, MD, JSON).

---

## 4. Auditoria

`AuditLog` grava JSONL append-only com encadeamento:

```
entry[i].prev_hash == entry[i-1].hash
entry[i].hash     == sha256(prev_hash + json(entry_sem_hash))
```

`verify()` recalcula a cadeia inteira. Detecta:

- ✅ editar o conteúdo de qualquer registro (`test_audit_detects_tampering`)
- ✅ remover um registro do meio (`test_cli.py::test_verify_audit_detects_removed_middle_entry`)

---

## 5. Limitações declaradas (para não haver surpresa)

1. **Truncamento no fim da auditoria não é detectado.** Remover as últimas N
   linhas deixa uma cadeia válida — limitação inerente a hash encadeado sem
   âncora externa. *Mitigação:* publicar/anotar periodicamente o hash final em
   local que o atacante não controle (um commit, um e-mail, outro sistema).
2. **Detecção de injeção é lexical.** Regex en/pt, não classificador semântico.
   Serve para triagem e como sinal; não é fronteira de segurança por si só. A
   defesa real é a política do prompt + a métrica binária `injection_resisted`.
3. **A redação depende do formato.** Segredo em formato fora dos 7 padrões passa.
   Por isso o princípio é: **não coloque segredo em dado que o sistema processa.**
4. **`redact()` no `case_results.output_head` grava 300 caracteres.** Suficiente
   para auditoria do veredito; não é cópia integral da saída (limite de volume).
5. **Sem criptografia em repouso.** O SQLite é texto claro (com segredos
   redigidos). Se o diretório de trabalho for sensível, use disco criptografado.
6. **Isolamento do executor.** O executor determinístico não executa código, mas
   um adaptador futuro com rede/sandbox mudaria o modelo de ameaças — deve
   reabrir este documento antes de ser habilitado.

---

## 6. Checklist para plugar um adaptador de modelo real

Antes de escrever a primeira linha de rede:

- [ ] Releia §2 e §5 — o modelo de ameaças muda (novo vetor: conteúdo do provedor
      contém instrução; dado do usuário sai da máquina).
- [ ] Chave **somente** em variável de ambiente; nunca em config, suite ou log.
- [ ] Confirme que a política segue `allow_network=False`: habilitar é uma decisão
      **consciente e revisável**, não um efeito colateral.
- [ ] `deterministic=False` no executor → `assert_executor_allowed` passa a exigir
      a permissão (falha hoje, por desenho).
- [ ] Ajuste `costs.cost_per_metric_call` e `costs.max_cost_units` ao preço real;
      valide o teto com um teste antes de rodar em escala.
- [ ] `max_retries` para falhas transitórias; garanta que erro de API **não**
      gere score parcial silencioso (hoje vira `error` + score 0, auditável).
- [ ] Revise o que sai da máquina: as suites podem conter dados internos. Envie o
      mínimo necessário.
- [ ] Reavalie `require_significance` / `min_decided_pairs` para o tamanho da sua
      validação — e **mantenha um holdout intocado**.
