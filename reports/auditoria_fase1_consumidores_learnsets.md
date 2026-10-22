# Fase 1 — novos consumidores locais de learnsets e limite de 20 entradas

**Estado:** achados estáticos locais em três consumidores adicionais da tabela de ponteiros de learnsets. Foram verificadas as instruções Thumb selecionadas e seus chamadores diretos na ROM BR. Não houve execução dinâmica, nem modificação da ROM/save. Os papéis semânticos completos dos chamadores não foram nomeados.

## Proveniência e método

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes, SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Desmontagem Thumb com Capstone 5.0.7 em instalação temporária `/tmp/capstone-py`; bytes e callsites conferidos localmente. REA/Ghidra e execução dinâmica não foram usados.
- `scripts/scan_expansion_table_literals.py --list-candidates` localiza a palavra-base `0x0825D7B4` e candidatos de instruções Thumb LDR literal; o detector reconhece padrão de opcode, não prova sozinho alcançabilidade ou uso. Nos caminhos abaixo, a palavra, a instrução que a carrega, o cálculo de índice, os loads seguintes e o chamador foram examinados.
- A tabela/base e dois consumidores prévios permanecem descritos em `reports/ciclo_20_learnsets_indices_consumidor_moves.md`; esta nota amplia, não substitui, aquele ciclo.

## Consumidores locais adicionais

### `0x08043C84`

A rotina recebe em `r0` um registro e conserva `r1` como outro argumento. Chama o dispatcher local `0x0803FBE8` com seletores `0x0B`, `0x38` e, num laço de quatro posições, `0x0D`–`0x10`. O valor do seletor `0x0B` vai para `r7` e é usado como índice: `r7 × 4 + 0x0825D7B4`; a rotina dereferencia o ponteiro e percorre halfwords da lista.

Para cada halfword, compara os bits `0xFE00` com o valor do seletor `0x38` deslocado em 9; os bits `0x01FF` são comparados com os quatro valores previamente lidos. Há um contador de entrada e a rotina encerra ao encontrar `0xFFFF` ou quando o índice passa de `0x13`. Portanto, neste caminho são processadas no máximo **20 entradas** por lista. A rotina retorna o contador local `sl`.

Chamadores diretos encontrados na ROM: `0x080E50EA` e `0x080E50FE`, ambos no mesmo fluxo chamador. O propósito de UI/fluxo desse chamador não foi estabelecido.

### `0x08043DD4`

A rotina usa o argumento `r0` para calcular `r0 × 4 + 0x0825D7B4`, carrega o ponteiro da lista e escreve numa área apontada por `r1`. Para cada uma de até 20 halfwords, mascara `0x01FF` e armazena o resultado u16 no buffer. Para o sentinel `0xFFFF`, o ciclo termina; após processar o índice 19, a comparação com `0x13` termina a rotina antes de ler outra entrada. O retorno é a contagem acumulada em `r5`.

O chamador `0x08045D42` carrega o valor usado como índice a partir do seletor `0x0B` do dispatcher `0x0803FBE8` e passa o endereço de saída. Não há comparação superior de faixa visível entre essa leitura e o lookup nesta sequência analisada. Não foi seguido todo o processamento posterior do buffer.

### `0x08043E2C`

A rotina chama `0x0803FBE8` com seletores `0x41` e `0x38`. O valor retornado pelo seletor `0x41` é guardado e indexa a tabela por `valor × 4`; antes disso, o código o compara com o imediato `0x19C` e retorna zero se forem iguais. O relatório atribui somente esses fatos locais aos seletores; não assume nome semântico para `0x41`.

O código também lê quatro valores com seletores `0x0D`–`0x10`, percorre a lista da tabela e aplica a máscara `0xFE00` para comparar a parte de nível com o valor obtido por `0x38`. A parte `0x01FF` é comparada aos quatro valores. O contador `r5` é limitado a índices 0–19, logo este caminho também processa no máximo **20 entradas**; termina ainda ao encontrar `0xFFFF` ou ao ultrapassar o nível lido. Não se observou uma checagem geral de faixa para o valor usado no lookup; a comparação local específica é apenas com `0x19C`.

Chamador direto local: `0x0811FD10`. Não foi determinada a semântica do fluxo de batalha que o chama.

## Síntese de limites

| Caminho local | Índice da tabela | Regra/limite observado |
|---|---|---|
| `0x0803E9E0` e `0x0803EA88` (ciclo 20) | valor lido por seletor `0x0B` × 4 | percursos por terminador/nível; sem clamp de espécie visível nos trechos disassemblados daquele ciclo |
| `0x08043C84` | valor do seletor `0x0B` × 4 | terminador e máximo de 20 entradas |
| `0x08043DD4` | argumento `r0` × 4 | terminador e máximo de 20 entradas; extrai bits `0x01FF` |
| `0x08043E2C` | valor do seletor `0x41` × 4 | terminador, nível e máximo de 20 entradas; igualdade específica com `0x19C` retorna zero |

A auditoria de chamadas adicionais prova que a tabela é lida por mais rotinas do que as duas rotinas de aprendizado descritas no ciclo 20. Nas três novas rotinas, o limite explícito de 20 é real no código local. O ciclo 20 registrou listas locais com 1–18 palavras antes do terminador; portanto esse limite não demonstra truncamento dos dados atuais observados, mas é um gate para expansão: o dataset de corte precisa identificar listas com mais de 20 entradas e esses consumidores terão de ser adaptados/testados antes de alegar suporte.

Não foram provados os contratos/tamanhos de todos os buffers de saída, a validação dos índices em chamadores não examinados, nem o comportamento em caso de terminador ausente. Nenhum achado determina qual geração/corte deve ser escolhido.

## Próximos passos

1. Auditar chamadas e buffers dos três consumidores e todos os demais candidatos de referência da tabela; confirmar se existem outras capacidades menores.
2. Depois de aprovar o corte, calcular quantidade de entradas de learnset por espécie/formas na fonte versionada e listar qualquer caso `>20` antes da importação.
3. Provar com testes estáticos e dinâmicos o caso de lista no limite e acima dele, sem modificar ROM/save-base.
4. Continuar o ledger de limites para moves, tipos, Pokédex/UI, party/PC e saves; estes achados não cobrem os demais subsistemas.
