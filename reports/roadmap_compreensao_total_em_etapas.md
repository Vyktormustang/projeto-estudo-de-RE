# Roteiro — compreensão abrangente da ROM em etapas

**Estado atualizado:** 2026-10-21
**ROM-base:** `google_drive/Pokemon - Fire Red (BR).gba`
**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Objetivo e correção de escopo

O objetivo é compreender **a ROM de forma abrangente, sistema por sistema**, para
poder explicar seu funcionamento e realizar análises/modificações com fundamento.
Cutscenes e NPCs são exemplos de perguntas práticas, não limites nem definição do
escopo. A investigação deve continuar por todo o código, dados, recursos e conexões
entre sistemas que forem identificados.

Os ciclos 01–10 documentaram sobretudo o loop de jogo e uma fatia do menu de pausa;
não representam conclusão nem cobertura ampla. O ciclo 11 começou o motor de scripts
e os comandos de object events. O upstream serve para sugerir nomes e semântica; a
ROM local continua sendo a fonte de prova para endereços, layout e comportamento
nesta revisão.

“Total” será perseguido por cobertura auditável, não por um percentual inventado:
construir inventários de regiões de código e dados, classificar cada componente,
seguir relações entre eles e manter explicitamente os itens desconhecidos. O escopo
não será encerrado depois de responder aos exemplos citados.

## Etapas de cobertura

### Etapa 0 — Base reproduzível e mapa do artefato

- Fixar hash, tamanho, revisão e limites de ROM; documentar o mapeamento entre
  offsets no arquivo e endereços GBA.
- Reunir inventário de ferramentas, scripts, saídas existentes e limitações do
  emulador/ambiente.
- Separar evidência local, inferência estática, validação dinâmica e comparação com
  upstream, com níveis de confiança explícitos.

**Estado:** hash e artefatos de análise já existem; consolidar/inventariar durante
as próximas etapas.

### Etapa 1 — Inventário global de código e dados

- Identificar regiões executáveis, tabelas de ponteiros, dados comprimidos e áreas
  não classificadas.
- Auditar o catálogo de funções, limites de função, chamadas/referências cruzadas,
  vetores de entrada e código sem callers óbvios.
- Agrupar funções em módulos/sistemas; deixar endereços e nomes incertos marcados
  como hipóteses, em vez de forçar identificação.

**Estado:** há desassemblagem e callgraph preliminares no workspace; cobertura,
qualidade dos limites e regiões não classificadas ainda precisam de auditoria.

### Etapa 2 — Fundamentos de execução e estado

- Boot, inicialização, interrupções, loop por frame, tasks/callbacks, entrada,
  temporização, carregamento de módulos e transições.
- Modelo de memória, estruturas globais, alocação, save blocks, SRAM/flash e
  consequências de persistência.
- Correlacionar cada fluxo com referências a funções e dados, não apenas com nomes
  emprestados de outra build.

**Estado:** loop/task scheduler parcialmente estudados em ciclos anteriores; restante
pendente.

### Etapa 3 — Formatos, tabelas e carregadores

Mapear como a ROM representa e carrega, conforme existirem nesta build:

- mapas, headers, conexões, warps, layouts, scripts e eventos;
- NPC/object-event templates, gráficos, movimentos e identificadores;
- texto, codificações, tabelas de nomes e mensagens;
- sprites, paletas, tiles, animações, efeitos visuais e áudio;
- dados de Pokémon, golpes, itens, treinadores, encontros e outros catálogos;
- formatos comprimidos, ponteiros, terminadores e regras de seleção.

Para cada formato: evidência de bytes local, estrutura proposta, referências que o
consomem e uma amostra validada. Não assumir que um layout upstream é idêntico sem
conferência local.

**Estado:** parcial. Ciclos 12–13 confirmaram o lookup de grupos,
`MapHeader → MapEvents`, layout, arrays de evento e tabela/dispatch de scripts de
header em uma amostra local. `scripts/inspect_map_event_graph.py` permite repetir a
extração por índices. Ainda faltam outros mapas, consumidores de warps/coordenadas/
fundo, carregadores completos e os demais formatos/catálogos.

### Etapa 4 — Passes sistemáticos por subsistema

Cada subsistema recebe uma ficha própria: entrada e chamadas, estruturas/dados,
fluxo normal, estados/condições, erros/retornos, interações com outros sistemas,
modos de alteração e validação. Cobertura inicial (a ampliar quando o inventário
revelar novos domínios):

1. scripts/eventos/bytecode, variáveis, flags e progressão;
2. campo, mapas, transições, movimento do jogador e colisão;
3. NPCs/object events e entidades especiais;
4. batalhas, IA, treinadores, captura e callbacks de campo;
5. party, PC/armazenamento, Pokédex e evolução;
6. Bolsa, itens, lojas e efeitos de itens;
7. menus, interface, controles e telas auxiliares;
8. comunicação/link, Mystery Gift e recursos de conectividade presentes na build;
9. renderização, sprites, animações, áudio, efeitos e texto;
10. salvamento, configurações, inicialização e continuidade da partida;
11. demais módulos identificados no inventário global, sem tratá-los como fora de
    escopo por não aparecerem nos exemplos.

**Estado:** pausa parcialmente coberta; motor de bytecode, handlers NPC e dados/
consumidores de mapa iniciados nos ciclos 11–16; demais domínios e passes pendentes.

### Etapa 5 — Ligações entre sistemas e rastros completos

Rastrear fluxos representativos ponta a ponta para entender as junções, não apenas
funções isoladas: gatilho → script → comandos → atores/dados → mudança de flags ou
save → transição/retorno. Cutscenes e adição/remoção de NPCs são exemplos úteis de
rastro, ao lado de batalhas, itens, warps e outros fluxos que o inventário revelar.

**Estado:** ciclos 12–16 ligaram header, despachantes, eventos de coordenada e de
fundo, interações por campo e duas cenas aos efeitos locais sobre atores, texto,
vars/flags e warp. A rota de botão de força por pedregulho também foi separada.
Ainda faltam warps em profundidade, outros mapas, subsistemas e validação dinâmica;
esses rastros são amostras, não substitutos dos passes abrangentes por sistema.

### Etapa 6 — Validação e auditoria de cobertura

- Usar emulação/controlada quando possível para validar hipóteses, registrando
  estado inicial, ações, observações e limites; separar teste dinâmico de inferência
  estática.
- Manter um ledger por região/função/tabela: desconhecido → localizado →
  classificado → cruzado com referências → comportamento analisado → validado.
- Revisar sistematicamente regiões sem classificação, funções sem propósito
  conhecido, tabelas sem consumidor identificado e hipóteses não testadas.
- Encerrar cada etapa com lista de lacunas, evidência e próximo recorte; não alegar
  conclusão global enquanto houver domínios relevantes não inventariados.

## Estado atual e próximo passo

- **Ciclos 01–10:** loop e menu de pausa, um subconjunto do jogo.
- **Ciclo 11:** tabela local de comandos de script e handlers de NPC para spawn,
  remoção, movimento e visibilidade; análise estática. Relatório:
  `reports/ciclo_11_script_commands_npc_spawn_remove.md`.
- **Ciclo 12:** lookup local de mapa, `MapHeader`, `MapEvents` e templates do grupo
  3/mapa 0; parser reutilizável em `scripts/inspect_map_event_graph.py`. Um registro
  local difere da amostra upstream; diferença preservada como questão em aberto.
  Relatório: `reports/ciclo_12_map_headers_events_obj_templates.md`.
- **Ciclo 13:** parser local de `MapHeader.mapScripts`, despachantes de tipos e
  tabela condicional de frame/warp; relatório `reports/ciclo_13_map_script_dispatch_local.md`.
- **Ciclo 14:** confirmou na ROM local o scanner/condicionador de eventos de
  coordenada e sua chamada prioritária no processamento de campo após passo; separou
  a rota de botão de força por pedregulho. Análise estática, sem validação dinâmica.
  Relatório: `reports/ciclo_14_coord_event_scanner_field_loop.md`.
- **Ciclo 15:** seguiu os dois gatilhos Oak locais até um script compartilhado,
  diálogos, caminhos alternativos de movimento, spawn de template ID 3, mudanças de
  vars/flags e warp; nomes de cena separados como cruzamento upstream. Estático.
  Relatório: `reports/ciclo_15_pallet_oak_coord_cutscene_trace.md`.
- **Ciclo 16:** caracterizou localmente o scanner de BgEvents, os caminhos de
  interação/placa e a cadeia tag 3 → estado de object event → coord event
  `0x0816587B`; decodificou mensagens locais e separou nomes upstream. Estático.
  Relatório: `reports/ciclo_16_eventos_bg_signlady_interacao.md`.
- **Próximo:** revisar inventário/callgraph e iniciar um passe fora de mapas/scripts
  (ex.: batalha, equipe/PC, dados de Pokémon ou save), mantendo warp/conexões e
  amostras de outros mapas como lacunas explícitas.

Não há uma estimativa confiável de ciclos para a cobertura total antes de auditar o
inventário global e as regiões sem classificação. É claramente um trabalho longo,
provavelmente de muitas etapas; qualquer estimativa anterior de poucos ciclos refere-se
apenas a produzir um primeiro rastro prático, não ao objetivo amplo de compreensão.
