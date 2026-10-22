# Ciclo 19 — Limite dos registros de espécie e consumidores de tipos/habilidades

**Estado:** rastreamento estático local, com um script de reprodução. Foi determinada uma região candidata de 412 registros e encontrados consumidores locais de campos usados como tipos e habilidades. Não é prova de que todo sistema de Pokémon esteja coberto nem de que seja seguro expandir a tabela.

## Identidade, ferramentas e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes, SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Mapeamento: `VA GBA = offset de arquivo + 0x08000000`.
- Capstone 5.0.7 instalado temporariamente em `/tmp/capstone-py`; decodificação Thumb e leitura direta de bytes Python. Script independente sem dependência externa: `scripts/inspect_species_table.py`.
- REA/Ghidra não disponíveis como ferramentas ligadas ao agente; Java/Ghidra ausentes. Sem execução em emulador, alteração de ROM/save, ou validação runtime.
- Cruzamento semântico somente com `pret/pokefirered` fixado em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; não é prova de equivalência da build BR.

## Extensão da região — evidência local

A rotina já estudada em `0x0803E47C` calcula `species × 7 × 4` e usa stride `0x1C` a partir da base `0x08254784` (offset `0x254784`). O helper em `0x0803E7C4` usa a mesma base/stride e lê o byte `+0x13`.

A conferência sequencial da ROM local mostra:

- registro de índice 0 em `0x08254784`: todos os 28 bytes zero;
- índices 1–411: 411 registros completos no stride `0x1C`; em todos, bytes `+0x1A..+0x1B` são zero;
- índice 411 começa em `0x08257478`; seu fim exclusivo e o início da estrutura seguinte são `0x08257494` (offset `0x257494`);
- imediatamente depois do limite candidato há palavras u16 little-endian `0221 082D 0E49 1416 1E4D 1E4F 284B 32E6 404A 4EEB 5C4C FFFF ...`. A sucessão de palavras e terminadores `0xFFFF` difere do padrão estável dos registros de 28 bytes.

Assim, o intervalo local candidato é `[0x08254784, 0x08257494)`, ou `412 × 0x1C` bytes. Essa é uma conclusão estrutural forte pela repetição do registro e quebra observada; ainda não encontrei, neste ciclo, a referência local ao limite como constante nem provei todos os caminhos que indexam a tabela. Portanto, **não** é uma autorização para acrescentar espécies nem um limite garantido para todos os consumidores.

Reprodução:

```bash
python scripts/inspect_species_table.py
```

O script confere SHA-256, 412 strides, o registro zero, o padrão de padding e imprime bytes/palavras no limite candidato; a contagem 412 está declarada como hipótese evidencial, não como regra geral.

## Campos de tipos e habilidades — consumidores locais

O código usa a mesma multiplicação por 28 para selecionar o registro. As seguintes leituras são visíveis na ROM local:

- `0x0804FC6E–0x0804FC80`: indexa `0x08254784 + species × 0x1C`, carrega bytes em `+6` e `+7` e compara cada um com um valor de tipo recebido. Isto comprova o consumo de dois bytes por espécie nesse caminho; os nomes “tipo 1/2” são a interpretação cruzada, não rótulos presentes nos bytes de instrução.
- `0x08040D38–0x08040D6C`: indexa a mesma tabela; o ramo selecionado por um argumento lê `+0x16` ou `+0x17` e grava o byte num destino apontado por literal. Isto comprova duas posições consumidas para a habilidade. A interpretação como slot de habilidade vem do padrão estrutural/upstream.
- `0x0803F730–0x0803F786`: índice por stride `0x1C` e leitura de `+0x10`, com testes/ramificações. O campo é mais um consumidor da tabela; no upstream correspondente, esse offset é o gender ratio, mas o relatório não atribui uma semântica local além do que as instruções provam.
- `0x0803E47C`: consome os seis bytes iniciais (já documentado no ciclo 18); `0x0803E7C4` consome `+0x13` para escolher a curva de experiência.

Esses caminhos mostram que preservar apenas os seis base stats é insuficiente para alterar registros de espécie: offsets consultados por outros subsistemas também participam do comportamento. Não foram rastreados todos os possíveis campos nem todos os consumidores.

## Dados seguintes e cruzamento upstream

A região que começa em `0x08257494` tem estrutura de palavras u16 e terminadores `0xFFFF` na própria ROM. No upstream fixado, `include/constants/pokemon.h` define `LEVEL_UP_END` como `0xFFFF`, e `src/data/pokemon/level_up_learnsets.h` codifica movimentos de nível como `(lvl << 9) | move`. Isso torna a região local **compatível com dados de learnset**, mas a identidade exata e o agrupamento por espécie continuam pendentes de xref para a tabela de ponteiros/consumidor local. Não chamar isso de learnsets BR definitivamente identificados sem esse rastreamento.

O cruzamento do header upstream `struct SpeciesInfo` atribui `types` a `+0x06`, `abilities` a `+0x16`, `genderRatio` a `+0x10`, growth rate a `+0x13` e termina os campos em `+0x19` (tamanho de dados 26 bytes). A ROM local usa stride 28 e tem zeros em `+0x1A..+0x1B` para os 411 registros não-zero examinados. A causa desses dois bytes extras não está confirmada.

No mesmo upstream, `SPECIES_DEOXYS` tem ID 410, `SPECIES_CHIMECHO` ID 411 e `SPECIES_EGG` ID 412. Essa coincidência de IDs reforça a interpretação do recorte, mas não substitui bytes/xrefs locais nem prova que a ROM BR foi compilada daquele código.

Arquivos upstream usados apenas no cruzamento:

- `include/pokemon.h`, SHA-256 `a6881fee07ae10f57ebf3ec7af1cabd2e900d8ba8d3da644313c087d16e1617e`;
- `include/constants/pokemon.h`, SHA-256 `9cabd203100ae7246bc595b7295e7e04145f6292abfab83c3bd0597a2cfbcfb5`;
- `include/constants/species.h`, SHA-256 `ec3f9f9c2717dcd453aa7a27506c32e1e6ca067864534dee494695d74344c51a`;
- `src/data/pokemon/level_up_learnsets.h`, arquivo usado para a macro de codificação (hash não anexado neste ciclo).

## Lacunas e continuação

1. Achar e validar localmente a tabela de ponteiros de learnsets, um consumidor que indexe por espécie e a regra de terminação; só então atribuir os blocos subsequentes a espécies.
2. Rastrear os acessos locais restantes a `SpeciesInfo`, incluindo yield de EV, itens, catch rate, amizade/egg cycles e grupos de ovos; os usos upstream indicam perguntas, não achados locais.
3. Localizar a tabela/dispatch de golpes e seguir uma rota completa dado de espécie → learnset → golpe → efeito de batalha.
4. Auditar verificações de faixa de todos os consumidores antes de qualquer hipótese de expansão/modificação.
5. Seguir depois encontros selvagens, treinamento e demais subsistemas; esta fatia não conclui a cobertura de Pokémon nem da ROM.

Não houve validação dinâmica. Nenhum nome upstream foi promovido a fato local sem bytes ou instruções locais correspondentes.
