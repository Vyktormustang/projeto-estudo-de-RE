# Ciclo 20 — Tabela de ponteiros de learnsets e consumo por nível

**Estado:** rastreamento estático local de uma tabela de 412 ponteiros, seus destinos u16 terminados em `0xFFFF`, e dois consumidores que selecionam entradas por espécie/nível. Também foi seguido um helper que grava o move escolhido e consulta um campo no registro de move. Não é análise completa do catálogo ou do motor de batalha.

## Identidade e ferramentas

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`; 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Análise local: Capstone 5.0.7 temporário em `/tmp/capstone-py`, bytes Python e `callgraph/edges.tsv` para referências BL estáticas. Script reprodutível sem dependências externas: `scripts/inspect_level_up_learnsets.py`.
- REA/Ghidra e Java continuam ausentes; não houve execução dinâmica, nem modificação da ROM/save.
- Cruzamento upstream separado: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`.

## Tabela local de ponteiros

Uma sequência word-aligned de ponteiros é referenciada pelas rotinas locais de leitura em `0x0803E9E0` e `0x0803EA88`. Sua base é `0x0825D7B4` (offset `0x25D7B4`). Os consumidores calculam `species × 4` e carregam o ponteiro da posição correspondente.

A verificação dos bytes locais mostra:

- 412 palavras u32, intervalo `[0x0825D7B4, 0x0825DE24)`;
- destinos monotonicamente não-decrescentes entre `0x08257494` e `0x08259738`;
- 411 destinos únicos; índices 0 e 1 apontam ambos para `0x08257494`; nenhum outro par de entradas é duplicado;
- no word u32 imediatamente depois da sequência, em `0x0825DE24`, há zero;
- cada destino único inicia palavras u16 que terminam em `0xFFFF` antes do próximo destino único; para o último destino, o terminador foi encontrado dentro dos 0x100 bytes examinados;
- 4.036 palavras precedem os terminadores, distribuídas entre listas únicas com comprimentos de 1 a 18.

O destino inicial coincide com o fim exclusivo da região candidata de SpeciesInfo do ciclo 19 (`0x08257494`). O destino final é `0x08259738`. A tabela sustenta uma organização por índices e destinos, mas não estabelece por si só a identidade semântica de cada índice.

Reprodução:

```bash
python scripts/inspect_level_up_learnsets.py
```

O script verifica o hash da ROM, os 412 ponteiros, monotonicidade, limites de cada destino único até terminador e resume amostras. Não escreve no artefato.

## Consumidores locais e formato observado

### Busca de entradas por espécie e nível — `0x0803E9E0`

O código local:

1. lê a espécie pelo accessor `0x0803FD44` com seletor `0x0B`;
2. obtém um nível pelo helper `0x0803E830`;
3. carrega a tabela base `0x0825D7B4`, indexa por `species × 4` e dereferencia o destino;
4. percorre halfwords, usando máscara `0xFE00` para comparar a parte alta da palavra com `nível << 9` e máscara `0x01FF` para extrair a parte baixa;
5. termina no valor sentinela local `0xFFFF`; entradas elegíveis são passadas aos helpers locais `0x0803E8B0` e, conforme o retorno/ramo, `0x0803EC40`.

`0x0803E9A4` é chamado de `0x0803E8B0` e, no caminho observado, escreve o ID do move em um dos quatro slots `mon + 0x0C + slot×2`. Para preencher PP, calcula `move × 12`, soma a base local apontada por literal `0x08250C04` e lê byte `+4`. Isso demonstra no código local um registro de move com stride de 12 bytes e o consumo de um campo no offset `+4`; ainda não determina o tamanho completo nem o limite final desse catálogo.

### Seleção de move na rotina `0x0803EA88`

Também indexa `0x0825D7B4` por espécie, lê o nível do registro por accessor e percorre halfwords da lista. Compara a porção `0xFE00` com o nível deslocado em 9; em caso de igualdade, mascara `0x01FF` e passa o resultado ao wrapper local `0x0803E89C`. Se não houver correspondência, avança no buffer até a condição de parada. A ROM contém referências BL de `0x0803E89C` para `0x0803E8B0`, e chamadas a `0x0803EA88` em `0x08024398`, `0x08045608`, `0x080CE748`, `0x081265BC` e `0x081266A0`; os nomes desses chamadores continuam desconhecidos localmente.

As duas rotinas indexam a tabela diretamente por espécie sem uma comparação de faixa visível antes da carga. Isso é uma observação restrita aos caminhos disassemblados, não prova de ausência de validação em todos os callers.

## Cruzamento semântico — não é evidência local

No upstream fixado, `include/constants/pokemon.h` define `LEVEL_UP_MOVE_ID = 0x01FF`, `LEVEL_UP_MOVE_LV = 0xFE00` e `LEVEL_UP_END = 0xFFFF`; `src/data/pokemon/level_up_learnsets.h` define `LEVEL_UP_MOVE(lvl, move) = (lvl << 9) | move`. O padrão de máscaras/terminador das instruções locais e as palavras da região local são compatíveis com esse encoding. O upstream também contém funções de aprendizado de moves de nível semelhantes; uso esses nomes somente como hipóteses de cruzamento, não como prova de que a ROM BR veio dessa árvore.

No mesmo upstream, a tabela correspondente chama-se `gLevelUpLearnsets`, e o helper que adiciona um move usa registros `BattleMove`. Os achados locais acima independem desses nomes: a base, strides, loads, máscaras e branches foram observados na ROM BR.

Hashes upstream usados:

- `include/constants/pokemon.h`: `9cabd203100ae7246bc595b7295e7e04145f6292abfab83c3bd0597a2cfbcfb5`;
- `src/data/pokemon/level_up_learnsets.h`: `d6563a88fa893d1433a02027cb13ba9574a6828a96b1a730b1d767fd7c5a0cc6`;
- `src/pokemon.c`: `116a470cd9ebfa226aa8d85c2eb63591e176d726837c67baaa1ac6260d50f2ec`.

## Verificações e limitações

- `scripts/inspect_level_up_learnsets.py` passou; encontrou 412 ponteiros, 411 destinos únicos e 411 listas terminadas.
- A bateria `bash scripts/run_all_tests.sh` inicialmente falhou em três self-tests por Capstone ausente do `PYTHONPATH`; reexecutada com `PYTHONPATH=/tmp/capstone-py`, os nove self-tests passaram. Isso não substitui teste dinâmico da ROM.
- Não foram decodificados todos os IDs de move, nem identificados localmente os grupos de batalha/efeitos; não foi provado o vínculo índice→nome de espécie na ROM BR.

## Próximo recorte

1. Mapear limites/stride e campos de mais registros na tabela local de moves a partir de `0x08250C04`; seguir referências aos consumidores.
2. Localizar tabela de dispatch de efeitos e ligar uma amostra de IDs a handlers efetivamente chamados na ROM local.
3. Rastrear uso de learnsets em criação, evolução, creche e relearner por callers locais; sem declarar esses fluxos equivalentes antes de segui-los.
4. Continuar em paralelo os demais consumidores de SpeciesInfo, encontros selvagens, batalha e outros subsistemas ainda desconhecidos.

A cobertura continua parcial e estática; nenhum resultado deste ciclo autoriza uma expansão ou alteração da ROM.
