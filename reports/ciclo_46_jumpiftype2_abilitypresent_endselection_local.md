# Ciclo 46 — handlers locais de batalha `0x42`–`0x44`

## Escopo e método

Análise estática da ROM BR `google_drive/Pokemon - Fire Red (BR).gba`, 16 MiB, SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`. Dispatches, bytes Thumb, literais e acessos à memória abaixo foram conferidos na ROM local. Verificador: `scripts/inspect_battle_jumpiftype2_abilitypresent_endselection.py`.

Capstone 5.0.7 temporário em `/tmp/capstone-py` foi usado para desmontagem estática. Não houve validação dinâmica nem uso de REA/Ghidra neste ciclo. O verificador confirma hash, dispatch, assinaturas e literais; não prova alcançabilidade de todos os ramos.

## Dispatch local

A tabela local começa em `0x0825011C`:

| Opcode | Ponteiro Thumb na tabela | Início da instrução |
|---|---:|---:|
| `0x42` | `0x08022D71` | `0x08022D70` |
| `0x43` | `0x08022DCD` | `0x08022DCC` |
| `0x44` | `0x08022E19` | `0x08022E18` |

## Evidência da ROM local

### `0x42`

1. Lê o byte `cursor+1`, chama `0x08016E24` e normaliza o retorno a byte; esse resultado é usado como índice `i`.
2. Lê o byte de comparação `cursor+2`.
3. Calcula `0x02023BE4 + i × 0x58` e compara o byte inline com os bytes nos offsets `+0x21` e `+0x22`.
4. Se qualquer comparação for igual, remonta o destino u32 little-endian de `cursor+3..+6` e grava-o em `0x02023D74`. Se ambas forem diferentes, avança o cursor em 7.

A forma do teste coincide com a do opcode local `0x22`, documentado no ciclo 35; isso é uma comparação de instruções locais, não uma atribuição de nome semântico. O helper `0x08016E24` foi observado também em ciclos anteriores; esta fatia não reabre sua tabela de mapeamento.

### `0x43`

O handler lê o seletor em `cursor+1` e chama `0x08019F18` com `r0=0x13`, `r1=0`, `r2=seletor`, `r3=0` e argumento de stack zero.

- Se o retorno for zero, soma 6 ao cursor em `0x02023D74`.
- Se o retorno for não-zero, remonta um destino u32 little-endian de `cursor+2..+5` e grava-o em `0x02023D74`.

A rotina chamada não foi seguida até o fim neste ciclo; seus efeitos colaterais além do valor de retorno permanecem desconhecidos. A decisão de cursor/ramo acima é local e observável no handler.

### `0x44`

Lê o byte em `0x02023D6B` e a word apontada por `0x02023FE8`. Calcula `word[0x02023FE8] + byte[0x02023D6B] + 0x54`, grava byte `1` nesse endereço e retorna. Não lê operand inline nem contém chamada local; o handler não atualiza explicitamente `0x02023D74`.

## Cross-reference upstream — não é prova local

A tabela consultada em `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, nomeia `0x42`, `0x43` e `0x44` como `Cmd_jumpiftype2`, `Cmd_jumpifabilitypresent` e `Cmd_endselectionscript`, respectivamente. Esses nomes e a interpretação são cross-reference; os endereços, comparações, chamadas, gravações e desvios acima vêm da ROM BR.

## Limites e continuidade

Não foram determinados o significado local definitivo dos campos lidos/escritos por `0x43`/`0x44`, os efeitos internos completos de `0x08019F18`, nem a alcançabilidade de cada condição. O restante da tabela de comandos e os estados intermediários de `0x23` continuam pendentes. Esta é uma fatia parcial, sem alegação de cobertura global.
