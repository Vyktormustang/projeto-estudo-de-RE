# Plano de implementação (conciso)

Deliverable 2 da solicitação: o plano seguido para a primeira versão funcional.
Está escrito no formato "decisões que foram tomadas", para que a revisão possa
discordar de pontos concretos.

## 1. Restrições de partida (verificadas, não supostas)

| Restrição | Como foi verificada |
|---|---|
| Sem chave/chamada de LLM disponível | tentativa de conexão (`curl` → `000`), varredura de variáveis de ambiente |
| Sem GPU | `nvidia-smi` ausente; 2 vCPU / 3.8 GiB RAM |
| Rede limitada a PyPI/npm/GitHub | teste de alcance por host |
| Conector GitHub **não** disponível como ferramenta | `list_connector_tools("github")` → `unsupported` |
| Google Drive disponível | `list_connector_tools("google_drive")` → `enabled` |
| `pytest` ausente; PEP 668 bloqueia instalação global | `pip3 install --user pytest` recusado |

Consequência direta: **modo determinístico**. Sem LLM, um "avaliador por IA" seria
fabricação de resultado. A especificação já pedia preferir testes determinísticos.

## 2. Escopo da v1

**Dentro:** os 10 módulos pedidos, o ciclo de 8 etapas, memória SQLite com
histórico e reversão, critérios de aceitação, proteção contra regressão,
relatórios, limites/custos/tentativas/permissões, CLI, testes de aceitação.

**Fora (explícito):** nenhum adaptador de LLM/API real; nenhuma modificação de
pesos; nenhuma escrita em plataforma externa; nada de paralelismo; sem banco
remoto; sem upload automático para o Drive.

## 3. Sequência executada

| Etapa | Entrega | Status |
|---|---|---|
| 1 | **Ambiente e repositório examinados** — capacidades reais, limites, licenças | ✅ (tabela §1) |
| 2 | **Plano** — este documento | ✅ |
| 3 | **Primeira versão funcional** — 27 arquivos, runtime stdlib-only | ✅ |
| 4 | **Testes executados** — 297 testes, 12 módulos | ✅ (`docs/TEST_REPORT.md` §2) |
| 5 | **Problemas corrigidos** — 19 defeitos reais | ✅ (`docs/TEST_REPORT.md` §4) |
| 6 | **Documentação** — README pt-BR + 4 documentos técnicos | ✅ |
| 7 | **Arquitetura, dependências, limitações e custos** — `docs/ARCHITECTURE.md`, README | ✅ |
| 8 | **Relatório de testes e mudanças** — `docs/TEST_REPORT.md` | ✅ |
| 9 | **Mudanças apresentadas para revisão** — PR (sem merge) | ✅ |
| 10 | **Nada publicado/mesclado sem autorização** | ✅ (nenhum merge, nenhum push a `main`) |

## 4. Ordem de construção dentro do código

A ordem foi escolhida para que cada camada só dependesse de camadas já testadas:

1. **Contratos e segurança** — `types`, `errors`, `safety` (política imutável,
   orçamento, auditoria, redação, conteúdo não confiável). Sem isso, qualquer
   código seguinte herdaria decisões de confiança erradas.
2. **Formato de prompt + métricas** — `promptspec` (o *espaço de busca* é um
   schema fechado) e `graders` (métricas objetivas + aritmética segura).
3. **Execução e suites** — `executors` (módulo 1 e 9), `taskset` (carregamento,
   validação, splits train/val/holdout).
4. **Avaliação** — `evaluate` (módulo 2): erro vira caso com score 0, nunca
   exceção silenciosa; contabilidade de orçamento por caso.
5. **Diagnóstico e proposta** — `diagnose`, `propose` (módulo 3). Só leem treino.
6. **Comparação e seleção** — `compare`, `select` (módulos 4 e 5): pareado por
   caso, teste de sinais exato, IC bootstrap com semente fixa, 6 critérios.
7. **Memória e histórico** — `memory`, `provenance`, `history` (módulos 6 e 7).
8. **Relatório e ciclo** — `report`, `optimizer` (módulo 8 + orquestração).
9. **Configuração e CLI** — `config` (módulo 10) e `cli` (interface).
10. **Testes e documentação** — 297 testes, 5 documentos.

## 5. Decisões estruturais (e o que elas custaram)

| Decisão | Motivo | Custo assumido |
|---|---|---|
| Artefato otimizado = **contrato de diretivas** (`CHAVE = valor`), não texto livre | Torna a comparação auditável e o executor determinístico | O espaço de busca é finito; não descobre redações novas |
| **Executor de referência determinístico** em vez de mock de LLM | Honestidade: sem LLM, números de LLM seriam inventados | Só mede o maquinário, não a qualidade de um modelo real |
| **Zero dependências de runtime** | Auditoria, reprodutibilidade, custo R$ 0, sem risco de cadeia de suprimentos | Reinventar ~6 utilidades que uma lib daria |
| **Hipóteses determinísticas** (GEPA/DSPy/Self-Refine/TRL recusados como dependência) | Nenhum deles funciona sem LLM/GPU; todos trazem peso desnecessário | Perde-se o "refletor" generativo |
| Separação estrita **treino / validação / holdout** | É o que separa "melhorou na validação" de "melhorou de verdade" | Menos dados por divisão → menos poder estatístico |
| **Rejeitar por padrão** (aceitar exige evidência) | Um falso aceito acumula erro silencioso; um falso rejeitado é reversível | Ciclo converge mais devagar |
| Reversão **aditiva** (move ponteiro, nunca apaga) | Requisito de auditabilidade + histórico | Banco cresce (irrelevante nesta escala) |

## 6. Critérios de pronto (definidos antes de codar)

1. `pytest` verde **com o número real reportado**, incluindo falhas se houver.
2. O ciclo real produz melhora **confirmada em holdout** que nunca participou da
   seleção — ou o relatório diz que não produziu.
3. Toda decisão (aceita ou rejeitada) recuperável do SQLite com motivo.
4. `rollback` funcional sobre um experimento real, não só em teste unitário.
5. Auditoria verificável; segredo nunca em arquivo versionado.
6. Nenhuma afirmação de capacidade inexistente no README (LLM, pesos, rede).

Todos foram cumpridos; evidências em `docs/TEST_REPORT.md` e `docs/evidencias/`.

## 7. Próximos passos sugeridos (não executados por decisão de escopo)

1. **Adaptador de modelo real** (módulo 9): implementar `Executor`, ajustar
   `costs` e revisar `SECURITY.md` §6 antes de habilitar rede.
2. **Refletor por LLM** no propositor (inspirado em GEPA/Self-Refine), mantendo o
   schema como contrato de validade.
3. **Fronteira de Pareto por instância** quando a validação crescer.
4. **Paralelismo controlado** de avaliações, com o orçamento passando a ser
   thread-safe.
5. **Assinatura externa da auditoria** (hash final publicado), fechando a
   limitação do truncamento.
