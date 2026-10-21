# Roteiro — compreensão funcional da ROM

**Estado atualizado:** 2026-10-21

## Correção de escopo

Os ciclos 01–10 são uma fatia vertical do loop de jogo e do menu nativo de pausa.
Eles documentam callback/task scheduling, montagem do menu, Bolsa, Salvar, Opções,
Sair e abertura/retorno da equipe. **Não constituem compreensão total do código do
jogo** nem permitem afirmar que já sabemos construir qualquer cutscene ou alterar
qualquer NPC.

A ROM contém múltiplos megabytes de código e milhares de funções. “Compreensão
integral” literal não é um critério finito verificável em poucos ciclos. Para manter
a atividade prática, a meta será um **atlas de workflows modificáveis**: para cada
pergunta (por exemplo, inserir um NPC ou acionar uma cena), identificar dados de
entrada, condição/trigger, dispatcher, funções nativas, estado persistente, retorno,
como editar e como validar. Manter fatos do binário local separados dos nomes
cruzados com upstream.

## Trilhas de trabalho

| Trilha | Perguntas que deve responder | Estado |
|---|---|---|
| Loop, tarefas e callbacks | Como uma atualização por frame e uma task chegam ao handler? | Coberta em ciclos anteriores. |
| Menu de pausa e seus destinos | Como abrir/fechar e retornar de menus comuns? | Coberta para a rota testada; submenus ainda podem faltar. |
| Script engine | Como os bytes de um script selecionam comandos e como executam/esperam/retornam? | Em andamento; tabela local identificada no ciclo 11. |
| NPC/object events | Como templates entram no mapa; spawn/remove/hide/move; local IDs; gráficos e movement type? | Em andamento; handlers add/remove mapeados no ciclo 11, templates locais pendentes. |
| Triggers e cutscenes | Como interação, coordenada, gatilho de mapa ou evento automático inicia uma cena; como ela termina? | Pendente. |
| Flags, vars e progressão | Como condicionar/registrar cenas e estados permanentes? | Pendente como workflow. |
| Batalhas e ações de campo | Como os scripts disparam batalhas, field moves e callbacks de retorno? | Pendente. |
| Mapas e transições | Warps, map headers, layouts, conexão de mapas e carregamento de eventos. | Pendente. |
| Assets e apresentação | Como texto, gráficos NPC, movimentos e efeitos são associados aos dados? | Pendente. |

## Sequência recomendada

1. **Ciclo 11 — Script commands/NPC:** confirmar a tabela de bytecodes na ROM e os handlers add/remove/move; relatório `reports/ciclo_11_script_commands_npc_spawn_remove.md`.
2. **Ciclo 12 — Dados de mapa e templates:** mapear no binário local um map header e seus `MapEvents`/templates; responder o que precisa ser criado para um NPC realmente novo.
3. **Ciclo 13 — Um workflow de cutscene end-to-end:** mapear trigger → script → comandos e condições → estado final. Escolher uma cena simples e reprodutível; se o usuário indicar “cutscene X”, substituir a amostra pela cena pedida.
4. **Ciclo 14 — Receita de modificação/validação:** testar em cópia de ROM/estado, explicar IDs únicos, assets/script pointer/flags e como reverter. Sem gravar sobre ROM/save originais.
5. Em seguida, repetir o modelo para batalhas, movimentos de campo, warps e outros gêneros conforme prioridade.

## Critério de conclusão realista

A atividade pode ser considerada operacionalmente útil quando cada workflow prioritário tiver:

- caminho e dados confirmados no binário local;
- precondições (mapa, local ID, flags/vars, estado da partida);
- forma de edição e consequências de persistência;
- exemplo reproduzível e validação no mGBA, com limites explícitos;
- nomes upstream apresentados separadamente e identificados pelo blob consultado.

Isso não equivale a nomear/descompilar todas as funções da ROM. Antes de cada novo ciclo, declarar quais workflows faltam e reestimar com base na complexidade encontrada; não usar porcentagem sem inventário/critério de cobertura.
