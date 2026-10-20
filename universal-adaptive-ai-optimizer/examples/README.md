# Exemplos

Dois arquivos, e uma regra que vale a pena entender antes de copiá-los.

## `config.example.json`

Configuração completa do `uaao`, com **todos** os campos válidos preenchidos com
os valores padrão. Copie e ajuste.

```bash
python -m uaao run --workdir .uaao --config examples/config.example.json \
    --suite calc_v1 --iterations 3
```

**Não use chaves `_comentario` ou similares:** o carregador de configuração
**recusa chaves desconhecidas** (`ConfigError`) de propósito. Campo silencioso é
onde o erro se esconde, então a config não tem "modo tolerante". Comentários,
portanto, ficam aqui, não no JSON.

Observações por bloco:

- `db_path`, `reports_dir`, `audit_path` são resolvidos a partir do `--workdir`
  (ou do arquivo de config, quando absolutos). O `.gitignore` já ignora `.uaao/`.
- `limits.max_candidates_per_iteration` é o teto de candidatos **testados** por
  iteração; a proposta seleciona por rodízio entre classes de operador para que
  nenhuma hipótese seja sistematicamente descartada por esse teto.
- `costs.cost_per_metric_call = 0.0` é o valor correto hoje (executor local
  determinístico). Ao plugar uma API paga, atualize este campo — o teto
  `max_cost_units` passa a valer automaticamente.
- `selection.min_decided_pairs = 8`: com menos pares decididos é impossível
  atingir `p < 0.05`, então o critério de significância é marcado como
  **não avaliado** (em vez de reprovar ou aprovar silenciosamente).
- `selection.use_holdout_for_selection = false` é **obrigatório**: `true` é
  recusado na carga. O holdout existe para confirmar, não para escolher.

**Chaves de segurança são recusadas aqui.** `allow_network`,
`allow_external_write`, `allow_self_modification`, `allow_code_execution`,
`allow_subprocess`, `safety_policy`, `permissions`, `disable_safety`,
`bypass_guardrails`, `trust_all_content` → erro na hora de carregar (testado em
`tests/test_safety.py::test_config_rejects_security_relaxation_keys`). A política
de segurança mora em `uaao/safety.py` e é imutável por construção.

Variáveis de ambiente sobrepõem o arquivo, com `__` separando seções:

```bash
UAAO_LIMITS__MAX_ITERATIONS=3 UAAO_SELECTION__MIN_IMPROVEMENT=0.05 \
    python -m uaao run --workdir .uaao --suite calc_v1
```

## `prompt_exemplo.txt`

Exemplo de *prompt semente* (o "prompt original" que o ciclo deve preservar e
tentar melhorar), no formato de diretivas que o executor de referência entende:

```
ON_AMBIGUOUS = guess
ON_MISSING_TOOL = fabricate
LANGUAGE = auto
```

```bash
python -m uaao run --workdir .uaao --prompt examples/prompt_exemplo.txt \
    --suite calc_v1 --suite ambiguity_v1 --iterations 6
```

O arquivo é carregado como **dado** (via `UntrustedContent`: truncado, limpo de
caracteres de controle e inspecionado por padrões de injeção). Ele é gravado byte
a byte como artefato semente e **nunca** é alterado: cada melhoria é um artefato
novo com `parent_sha` apontando para o anterior.

Sugestão de leitura: rode esse exemplo e observe o **primeiro** relatório. O valor
didático está menos no prompt final e mais em ver as rejeições com motivo
(por exemplo, `LANGUAGE=auto` bloqueado por regressão em caso crítico).
