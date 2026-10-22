# Roteiro — compreensão abrangente da ROM em etapas

**Estado atualizado:** 2026-10-22
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
extração por índices. Ciclos 17–20 iniciaram os dados de Pokémon: accessors de equipe
e BoxMon, conversão para equipe, cálculo de stats, região candidata de 412 registros
de espécie e consumidores locais de campos em +6/+7 e +0x16/+0x17. O ciclo 20 localizou
uma tabela de 412 ponteiros em `0x0825D7B4`, validou 411 destinos únicos terminados em
`0xFFFF` e rastreou consumidores por espécie/nível até uma leitura de PP em registro
de move com stride 12. Os limites do catálogo de moves e os handlers ainda faltam.
Permanecem pendentes encontros e os demais consumidores/catálogos; também outros mapas,
consumidores de warps/coordenadas/fundo e carregadores completos.

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
consumidores de mapa iniciados nos ciclos 11–16. Ciclos 17–22 avançaram no domínio de
Pokémon/batalha: BoxMon→equipe, cálculo de stats, tabelas locais candidatas de espécie
e moves, ponteiros/listas de moves por nível, dispatch de efeitos e alguns scripts/
handlers de comandos de batalha. PC/armazenamento, fluxos completos de combate, demais
consumidores, persistência e outros domínios continuam pendentes.

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
- **Ciclo 17:** iniciou a camada de dados de Pokémon fora de mapas/scripts. Na ROM
  local, confirmou os dois accessors de equipe com 34 casos, os helpers BoxMon com
  tabelas de 84 GET/81 SET, offsets e os caminhos de cifragem/checksum; nomes de
  campos foram separados como cruzamento upstream. Estático, sem Ghidra/REA
  disponíveis na sessão e sem validação dinâmica. Relatório:
  `reports/ciclo_17_boxmon_party_acesso_dados_pokemon.md`.
- **Ciclo 18:** seguiu `BoxMonToMon`-like → cálculo local de stats → tabelas em
  `0x08254784` (base de espécies, stride 0x1C) e `0x08253AE4` (experiência). Uma
  amostra ID 1, os offsets de base stats/growth rate e a curva selecionada foram
  conferidos em bytes locais. Relatório: `reports/ciclo_18_tabela_especies_e_calculo_stats.md`.
- **Ciclo 19:** encontrou evidência para 412 strides de `0x1C` em `0x08254784`,
  zeros em `+0x1A..+0x1B` nos índices 1–411, e uma quebra de padrão em `0x08257494`;
  decodificou consumidores locais dos offsets `+6/+7` e `+0x16/+0x17`. Words u16 e
  `0xFFFF` após a região são compatíveis com learnsets, mas o xref/agrupamento por
  espécie segue não provado localmente. Script: `scripts/inspect_species_table.py`;
  relatório: `reports/ciclo_19_limite_dados_especies_tipos_habilidades.md`.
- **Ciclo 20:** localizou em `0x0825D7B4` uma tabela local de 412 ponteiros e 411
  destinos únicos para listas u16 terminadas em `0xFFFF`; rastreou consumidores em
  `0x0803E9E0` e `0x0803EA88`, comparações por nível/máscara e escrita de move com
  leitura de PP em registros de stride 12 a partir de `0x08250C04`. A interpretação
  como learnsets depende do cruzamento upstream, separado da evidência local. Script:
  `scripts/inspect_level_up_learnsets.py`; relatório:
  `reports/ciclo_20_learnsets_indices_consumidor_moves.md`.
- **Ciclo 21:** caracterizou a região candidata de 355 registros em `0x08250C04`
  (stride 12), leituras locais em `+0`, `+1`, `+4`, `+6`, `+8` e uma rotina local
  que indexa `0x081D65A8` pelo byte `+0` e grava o ponteiro selecionado em RAM.
  Foram observados 214 ponteiros candidatos de efeitos; o máximo local do byte `+0`
  é 213. Script: `scripts/inspect_move_catalog.py`; relatório:
  `reports/ciclo_21_catalogo_moves_dispatch_efeitos.md`. Estático: não seguiu handlers
  individuais nem valida comportamento dinâmico.
- **Ciclo 22:** seguiu os índices 0 e 125 da tabela de efeitos até bytecodes locais,
  confirmou o dispatcher por opcode em `0x08015A0C`, uma sequência candidata de 248
  ponteiros em `0x0825011C` e handlers para opcodes amostrados (`0x28`, `0x2A`,
  `0x2E`, `0x35`). Cruzamento semântico upstream foi separado dos bytes/handlers
  locais. Script: `scripts/inspect_battle_effect_scripts.py`; relatório:
  `reports/ciclo_22_scripts_efeitos_comandos_handlers_batalha.md`. Estático, sem
  executar batalha nem percorrer todos os handlers.
- **Próximo:** seguir handlers nativos selecionados até alterações completas de estado,
  dano, texto e animação; rastrear retorno/cursor e validar em emulação se possível.
  Investigar offsets de move e consumidores ainda desconhecidos, e continuar a
  auditoria ampla de espécie, creche/evolução, PC/armazenamento e outros domínios.
  Estes rastros não representam cobertura global.

Não há uma estimativa confiável de ciclos para a cobertura total antes de auditar o
inventário global e as regiões sem classificação. É claramente um trabalho longo,
provavelmente de muitas etapas; qualquer estimativa anterior de poucos ciclos refere-se
apenas a produzir um primeiro rastro prático, não ao objetivo amplo de compreensão.
