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
consumidores de mapa iniciados nos ciclos 11–16. Ciclos 17–30 avançaram no domínio de
Pokémon/batalha: BoxMon→equipe, cálculo de stats, tabelas locais candidatas de espécie
e moves, ponteiros/listas de moves por nível, dispatch de efeitos, scripts/opcodes,
fluxo local de acerto/falha, recortes de dano, `typecalc`/efetividade, ajuste de dano,
animação, caminhos de atualização de HP, seleção de sons/mensagens, comandos de texto
e seleção por tabela. PC/armazenamento, fórmula completa de dano, demais consumidores,
persistência e outros domínios continuam pendentes.

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
- **Ciclo 23:** seguiu o comando local `0x01` do script de efeito 0 ao handler
  `0x0801DDC5`, à leitura de `ID×12` no catálogo, ao teste de acerto e ao helper que
  seleciona o avanço do cursor ou o destino de falha `0x081D695E`. Cruzamento semântico
  foi separado da evidência local. Script: `scripts/inspect_accuracy_path.py`;
  relatório: `reports/ciclo_23_accuracycheck_fluxo_acerto_falha.md`. Estático e parcial.
- **Ciclo 24:** seguiu opcode `0x05` em `0x081D6931` até o handler `0x0801E59D`,
  a chamada local `0x0803ECEC` e alguns ajustes/armazenamentos de dano; caracterizou
  entradas e leituras iniciais do helper, sem fechar sua fórmula. Script:
  `scripts/inspect_damagecalc_path.py`; relatório:
  `reports/ciclo_24_damagecalc_base_damage_local.md`. Cruzamento upstream separado,
  análise estática e parcial.
- **Ciclo 25:** seguiu opcode `0x06` até o handler local `0x0801E849`, com seleção
  do tipo, ramo STAB, tabela local candidata de 112 registros em `0x0824F050`, helper
  de modulação `0x0801E771` e ramos locais de habilidades; nomes semânticos foram
  cruzados separadamente com upstream. Script: `scripts/inspect_typecalc_path.py`;
  relatório: `reports/ciclo_25_typecalc_tipo_efetividade_local.md`. Estático e parcial.
- **Ciclo 26:** seguiu opcode `0x07` ao handler local `0x0801F105`, observando o
  fator percentual do dano, consultas a item/estado do defensor e um ramo de limite
  HP−1. Nomes de efeito/item foram cruzados separadamente com upstream. Script:
  `scripts/inspect_adjustnormaldamage.py`; relatório:
  `reports/ciclo_26_adjustnormaldamage_limites_item_estado.md`. Estático e parcial;
  acompanhado no Linear pela issue `VYK-5` do projeto Pokémon FireRed BR.
- **Ciclo 27:** seguiu localmente os handlers `0x09`/`0x0A` de animação/espera e
  `0x0B`/`0x0C` de barra e dados de HP, com offsets, flags e cursor documentados e
  nomes upstream separados. A rotina `0x0C` permanece parcial. Script:
  `scripts/inspect_battle_anim_hp_updates.py`; relatório:
  `reports/ciclo_27_animacao_atualizacao_hp_local.md`. Estático e parcial; issue
  Linear `VYK-6`.
- **Ciclo 28:** seguiu opcode `0x0E` em `0x081D6936` até `0x0801FAD1` e rastreou
  ramos representativos do handler local `0x0F` (`0x0801FBA1`), incluindo IDs crus,
  chamadas, flags e redirecionamentos de cursor. A tabela de mensagens e ramos não
  estão totalmente decodificados. Script: `scripts/inspect_result_sound_messages.py`;
  relatório: `reports/ciclo_28_efetividade_resultmessage_local.md`. Estático e parcial;
  issue Linear `VYK-7`.
- **Ciclo 29:** seguiu os handlers locais `0x10`–`0x12` (`0x0801FD51`, `0x0801FD91`,
  `0x0801FDD5`), confirmando operands u16, calls, flag de exibição, espera e cursor
  `+3`; os nomes foram cruzados separadamente com upstream. Script:
  `scripts/inspect_battle_text_commands.py`; relatório:
  `reports/ciclo_29_comandos_texto_batalha_local.md`. Estático e parcial; issue Linear
  `VYK-8`.
- **Ciclo 30:** seguiu handlers `0x13`/`0x14` (`0x0801FE31`/`0x0801FE85`), observando
  pointer u32 inline, seleção local de halfword por índice e cursor `+5`; rótulos de
  tabela/seleção foram cruzados separadamente com upstream. Script:
  `scripts/inspect_battle_table_text_commands.py`; relatório:
  `reports/ciclo_30_tabelas_texto_selecao_local.md`. Estático e parcial; issue Linear
  `VYK-9`.
- **Ciclo 31:** seguiu os handlers locais `0x15`–`0x17` (`0x08021125`, `0x08021211`,
  `0x08021221`): seleção de chance condicional, chamadas ao helper compartilhado,
  comparação aleatória e caminho alternativo do cursor `+1`. Nomes e semântica de
  efeitos foram cruzados separadamente com upstream. Script:
  `scripts/inspect_battle_effect_chance_commands.py`; relatório:
  `reports/ciclo_31_efeitos_opcodes_batalha_local.md`. Estático e parcial; issue Linear
  `VYK-10`.
- **Ciclo 32:** seguiu handlers locais `0x18`–`0x1A` (`0x08021231`, `0x080212AD`,
  `0x080215A1`), registrando a limpeza condicional de words por máscara, ramificações
  de estado/faint, cursor e chamadas. Os nomes upstream estão separados; o `0x19` ainda
  tem sub-ramos sem identificação local completa. Script:
  `scripts/inspect_battle_faint_status_commands.py`; relatório:
  `reports/ciclo_32_transicoes_status_e_faint_local.md`. Estático e parcial; issue
  Linear `VYK-11`.
- **Ciclo 33:** seguiu `0x1B`–`0x1D` (`0x080215DD`, `0x08021641`, `0x080216B9`):
  zero condicional de word e chamadas; operands inline u32; teste de máscara/HP; e cursor
  `+2`, `+10` ou destino inline. Nomes upstream estão separados. Script:
  `scripts/inspect_battle_status_jump_commands.py`; relatório:
  `reports/ciclo_33_handlers_status_jump_local.md`. Estático e parcial; issue Linear
  `VYK-12`.
- **Ciclo 34:** seguiu `0x1E`–`0x20` (`0x08021731`, `0x08021819`, `0x08021891`):
  consultas/comparação local, máscara de lado, seis comparadores, operands inline e
  redirecionamentos do cursor. Nomes upstream separados. Script:
  `scripts/inspect_battle_condition_commands.py`; relatório:
  `reports/ciclo_34_condicoes_ability_side_stat_local.md`. Estático e parcial; issue
  Linear `VYK-13`.
- **Ciclo 35:** seguiu `0x21`–`0x23` (`0x08021989`, `0x08021A0D`, `0x08021A69`):
  teste local com inversão e destino inline, comparação dos dois bytes de registro,
  e prólogo/dispatch/saída terminal de máquina de sete estados. O `0x23` permanece
  parcialmente analisado; nomes upstream estão separados. Script:
  `scripts/inspect_battle_condition_exp_commands.py`; relatório:
  `reports/ciclo_35_condicoes_status_tipo_exp_local.md`. Estático e parcial; issue Linear
  `VYK-14`.
- **Ciclo 36:** seguiu localmente `0x24`–`0x26` (`0x080223F9`, `0x080225D9`,
  `0x080225F1`): duas varreduras de seis registros e decisão de cursor/destino inline;
  rotina local de limpeza com campos e bits alterados; e leitura de byte inline para
  armazenamento. Nomes/semântica upstream separados. Script:
  `scripts/inspect_battle_team_cleanup_commands.py`; relatório:
  `reports/ciclo_36_checkteams_cleanup_multihit_local.md`. Estático e parcial; issue
  Linear `VYK-15`.
- **Ciclo 37:** seguiu localmente `0x27`–`0x29` (`0x08022609`, `0x08022651`,
  `0x08022671`): decremento condicional com cursor/destino inline, salto por ponteiro
  u32 e seis comparações de byte com endereços indiretos e destino condicional. Os
  nomes upstream estão separados da prova local. Script:
  `scripts/inspect_battle_jump_byte_commands.py`; relatório:
  `reports/ciclo_37_decrement_goto_jumpifbyte_local.md`. Estático e parcial; issue
  Linear `VYK-16`.
- **Ciclo 38:** seguiu localmente `0x2A`–`0x2C` (`0x08022711`, `0x080227B9`,
  `0x0802286D`): leituras indiretas de halfword/word, seis comparadores e saltos
  condicionais, além de comparação de arrays por tamanho u8. Nomes upstream separados
  da evidência local. Script: `scripts/inspect_battle_wide_array_commands.py`;
  relatório: `reports/ciclo_38_jumpifwide_and_array_local.md`. Estático e parcial; issue
  Linear `VYK-17`.
- **Ciclo 39:** seguiu localmente `0x2D`–`0x2F` (`0x080228F5`, `0x08022979`,
  `0x080229A1`): comparação de regiões byte a byte com salto por desigualdade; escrita
  de byte via endereço inline; adição byte com armazenamento truncado a 8 bits. Nomes
  upstream separados da evidência local. Script:
  `scripts/inspect_battle_byte_array_mutations.py`; relatório:
  `reports/ciclo_39_jump_arraynotequal_set_addbyte_local.md`. Estático e parcial; issue
  Linear `VYK-18`.
- **Ciclo 40:** seguiu localmente `0x30`–`0x32` (`0x080229CD`, `0x080229F9`,
  `0x08022A4D`): subtração byte com truncamento, cópia linear de bytes e cópia com
  índice-base indireto. Nomes upstream separados da evidência local. Script:
  `scripts/inspect_battle_copy_mutation_commands.py`; relatório:
  `reports/ciclo_40_subbyte_copyarray_copyindexed_local.md`. Estático e parcial; issue
  Linear `VYK-19`.
- **Ciclo 41:** seguiu localmente `0x33`–`0x35` (`0x08022AB9`, `0x08022AE5`,
  `0x08022B1D`): OR in-place de byte, halfword e word, com operands e avanços do cursor
  registrados. Nomes upstream separados da evidência local. Script:
  `scripts/inspect_battle_bitwise_commands.py`; relatório:
  `reports/ciclo_41_orbyte_orhalfword_orword_local.md`. Estático e parcial; issue
  Linear `VYK-20`.
- **Ciclo 42:** seguiu localmente `0x36`–`0x38` (`0x08022B61`, `0x08022B8D`,
  `0x08022BC5`): operações BIC in-place em byte, halfword e word, com máscaras,
  endereços e avanços do cursor registrados. Nomes upstream separados da evidência
  local. Script: `scripts/inspect_battle_bic_commands.py`; relatório:
  `reports/ciclo_42_bicbyte_bichalfword_bicword_local.md`. Estático e parcial; issue
  Linear `VYK-21`.
- **Ciclo 43:** seguiu localmente `0x39`–`0x3B` (`0x08022C09`, `0x08022C49`,
  `0x08022C69`): contador com espera/limite, espera por word de controle e seleção de
  battler com chamadas locais para packet/controller helpers. A rota de `0x0800D9EC`
  continua parcial. Nomes upstream separados da evidência local. Script:
  `scripts/inspect_battle_pause_healthbar_commands.py`; relatório:
  `reports/ciclo_43_pause_wait_healthbar_local.md`. Estático e parcial; issue Linear
  `VYK-22`.
- **Ciclo 44:** seguiu localmente `0x3C`–`0x3E` (`0x08022CC0`, `0x08022CCC`,
  `0x08022CEC`): retorno via stack local com decremento de contador, e dois handlers
  que limpam/gravam bytes de estado distintos. Os nomes upstream (`Cmd_return`,
  `Cmd_end`, `Cmd_end2`) e a interpretação dos campos estão separados da prova local.
  O helper de retorno não verifica localmente contador zero; alcançabilidade não
  estabelecida. Script: `scripts/inspect_battle_return_end_commands.py`; relatório:
  `reports/ciclo_44_return_end_local.md`. Estático e parcial; issue Linear `VYK-23`.
- **Ciclo 45:** seguiu localmente `0x3F`–`0x41` (`0x08022D04`, `0x0801DBA0`,
  `0x08022D40`): restauração de script e seleção de callback por stack; condição baseada
  em byte de registro e bit de flag de tabela, com salto inline; e push do cursor de
  retorno seguido de destino inline. Nomes upstream (`Cmd_end3`,
  `Cmd_jumpifaffectedbyprotect`, `Cmd_call`) e interpretação permanecem cross-reference.
  Limites dos stacks não foram estabelecidos. Script:
  `scripts/inspect_battle_end3_protect_call_commands.py`; relatório:
  `reports/ciclo_45_end3_protect_call_local.md`. Estático e parcial; issue Linear `VYK-24`.
- **Ciclo 46:** seguiu localmente `0x42`–`0x44` (`0x08022D70`, `0x08022DCC`,
  `0x08022E18`): comparação de tipos nos offsets `+0x21/+0x22` de registro indexado,
  chamada condicional com destino inline e gravação de byte em endereço calculado.
  Nomes upstream (`Cmd_jumpiftype2`, `Cmd_jumpifabilitypresent`,
  `Cmd_endselectionscript`) estão separados da evidência local; efeitos internos de
  `0x08019F18` permanecem parciais. Script:
  `scripts/inspect_battle_jumpiftype2_abilitypresent_endselection.py`; relatório:
  `reports/ciclo_46_jumpiftype2_abilitypresent_endselection_local.md`. Estático e parcial;
  issue Linear `VYK-25`.
- **Prioridade atual — expansão de espécies/moves/tipos:** executar Fases 0–1 do plano
  `reports/plano_expansao_pokemon_geracoes.md`: congelar corte/escopo e auditar somente
  leitura tabelas, consumidores, limites, save/party/PC, espaço e assets. As tabelas locais
  candidatas de 412 espécies, 355 moves, 412 ponteiros de learnsets e 112 registros de
  typecalc foram revalidadas; auditoria preliminar identificou três consumidores de learnsets
  adicionais com cap de 20 entradas, limites numéricos de moves/tipos e três leitores typechart
  adicionais. Entradas candidatas de scripts de efeito agora confirmam bytes `0x4A` e `0xA6`
  em limites de comando compatíveis com os macros upstream; registros candidatos de move
  apontam para ambas. No `0xA6`, o LCG local admite índice 112 e lê o registro seguinte, mas o
  rejeita por `+2 = 0xCC`; consequência runtime ainda não testada. Relatórios/verificadores:
  `reports/auditoria_fase1_consumidores_learnsets.md`,
  `reports/auditoria_fase1_limites_moves_tipos.md`,
  `reports/auditoria_fase1_consumidor_typechart_secundario.md`,
  `scripts/inspect_typechart_bounds.py` e `scripts/inspect_typechart_script_references.py`.
  Isso não autoriza expansão. Issue Linear `VYK-27`.
- **Trilha de RE de opcodes pausada no backlog:** `VYK-26`, handlers locais `0x45`–`0x47`.
  Retomar depois ou em paralelo quando priorizado; estados intermediários de `0x23`,
  caminhos de dano/callers/consumidores e demais domínios continuam desconhecidos.
  Estes rastros não representam cobertura global.

Não há uma estimativa confiável de ciclos para a cobertura total antes de auditar o
inventário global e as regiões sem classificação. É claramente um trabalho longo,
provavelmente de muitas etapas; qualquer estimativa anterior de poucos ciclos refere-se
apenas a produzir um primeiro rastro prático, não ao objetivo amplo de compreensão.
