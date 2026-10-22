# Ciclo 44 — handlers locais de batalha `0x3C`–`0x3E`

## Escopo e método

Análise estática da ROM BR `google_drive/Pokemon - Fire Red (BR).gba`, 16 MiB, SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`. Os endereços, bytes, acessos à memória e dispatch abaixo foram conferidos na ROM local. O verificador reproduzível é `scripts/inspect_battle_return_end_commands.py`.

A desmontagem Thumb foi feita com Capstone temporário (`PYTHONPATH=/tmp/capstone-py`); isso é análise estática, não execução. Não foram usados REA nem Ghidra neste ciclo. O script confirma o hash, o dispatch, assinaturas de instruções e literais; não é um emulador nem prova de alcançabilidade de cada caminho.

## Evidência local

A tabela local de comandos começa em `0x0825011C`; os três ponteiros Thumb são:

| Opcode | Ponteiro na tabela | Início de instrução | Evidência local resumida |
|---|---:|---:|---|
| `0x3C` | `0x08022CC1` | `0x08022CC0` | chama `0x0801756C` e retorna; não lê operand inline |
| `0x3D` | `0x08022CCD` | `0x08022CCC` | grava três bytes de estado e retorna; não lê operand inline |
| `0x3E` | `0x08022CED` | `0x08022CEC` | grava dois bytes de estado e retorna; não lê operand inline |

### `0x3C`

O handler em `0x08022CC0` chama `0x0801756C` e retorna. A rotina chamada executa, localmente, esta sequência:

1. Lê uma word de `0x02023FF4` e a trata como ponteiro; desse objeto lê outra word no offset `+8`.
2. Nesse segundo ponteiro, lê um byte no offset `+0x20`, subtrai 1 e grava de volta como byte.
3. Usa o byte decrementado como índice: lê uma word em `base + 4 × índice`.
4. Grava a word obtida em `0x02023D74`.

A sequência de instruções não testa se o contador está zerado antes do decremento. Se estiver zero, a operação de 8 bits produz `0xFF` e o índice calculado é `0xFF`; se tal estado é alcançável/legítimo não foi estabelecido. Os nomes dos objetos apontados por `0x02023FF4` e dos campos não são deduzidos apenas pelos endereços locais.

### `0x3D`

O handler grava, nesta ordem:

- byte `0` em `0x02023DCC`;
- byte `0` em `0x02023BC4`;
- byte `0x0B` em `0x02023BE3`;
- retorna.

Não há leitura de operand inline nem alteração explícita de `0x02023D74` nesse handler.

### `0x3E`

O handler grava:

- byte `0` em `0x02023BC4`;
- byte `0x0B` em `0x02023BE3`;
- retorna.

Diferentemente de `0x3D`, não zera `0x02023DCC`. Também não lê operand inline nem altera explicitamente `0x02023D74`.

## Cross-reference upstream — não é prova local

No checkout `pret/pokefirered` fixado no commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, a tabela de `src/battle_script_commands.c` chama os opcodes `0x3C`, `0x3D` e `0x3E` de `Cmd_return`, `Cmd_end` e `Cmd_end2`. O código upstream associa `Cmd_return` a `BattleScriptPop`; para os outros dois, mostra alterações de estado correspondentes, incluindo limpeza de flags/battler e seleção de `B_ACTION_TRY_FINISH`.

Hashes upstream consultados: `src/battle_script_commands.c` — `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`; `src/battle_util.c` — `87cf810eb2d58361d1beb1537b3bd71c9160a77c2a17d703399f6ed373bb5720`. Esses rótulos e a interpretação dos campos são cross-reference; as afirmações locais acima vêm dos bytes e acessos observados na ROM BR.

## Limites e próximos passos

Este recorte cobre somente três handlers e algumas instruções da rotina chamada por `0x3C`. Não determina a validade do contador de retorno em todos os callers, o significado local definitivo dos campos escritos por `0x3D`/`0x3E`, nem o ciclo completo do interpretador. Não houve validação dinâmica; a cobertura da ROM continua parcial, sem alegação de conclusão global.
