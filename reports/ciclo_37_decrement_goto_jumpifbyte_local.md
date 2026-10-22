# Ciclo 37 — handlers locais `0x27`–`0x29`: decremento, salto e comparação de byte

**Estado:** `0x27` decrementa um byte de estado e escolhe entre destino inline e cursor `+5`; `0x28` carrega diretamente um destino u32 inline para o cursor; `0x29` consome 10 bytes de operandos (avanço total `+11`, incluindo o opcode), lê um byte por endereço indireto, aplica uma de seis comparações e, quando a condição local é verdadeira, substitui o cursor pelo segundo destino inline.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset no arquivo + `0x08000000`. Dispatch e operandos conferidos diretamente; desmontagem Thumb estática com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Cross-reference apenas para nomes/semântica: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, `src/battle_script_commands.c` (SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`).
- REA/Ghidra não foram usados. Não houve execução dinâmica, comparação de traces, nem alteração da ROM. A semântica dos endereços apontados por scripts e seus callers concretos não foi resolvida nesta fatia.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x27` | `0x08022609` | `0x08022608` |
| `0x28` | `0x08022651` | `0x08022650` |
| `0x29` | `0x08022671` | `0x08022670` |

## Evidência local — opcode `0x27`

- Lê o byte `0x02023D72`, subtrai 1 e grava o resultado no mesmo endereço (gravação byte, portanto preserva apenas os 8 bits baixos).
- Se o byte após a subtração for zero, soma 5 à word-cursor `0x02023D74` e retorna.
- Se não for zero, lê quatro bytes little-endian de `cursor+1..cursor+4`, monta um u32 e grava esse valor como novo cursor. O handler não chama outra rotina.
- Consequência aritmética direta do código: valor original 1 vira 0 e toma `+5`; valor original 0 sofre wrap no byte para `0xFF` e segue o ramo do destino inline. Isso descreve as instruções, não a intenção do contador.

## Evidência local — opcode `0x28`

Lê os quatro bytes little-endian em `cursor+1..cursor+4`, monta o u32 e o grava imediatamente em `0x02023D74`. Não há teste, chamada nem caminho local de avanço `+5` observado.

## Evidência local — opcode `0x29`

Lê os operands antes do dispatch da comparação:

| Offset relativo ao cursor original | Uso observado |
|---:|---|
| `+1` | byte de seleção da operação |
| `+2..+5` | endereço u32 little-endian do byte a consultar |
| `+6` | byte de comparação |
| `+7..+10` | destino u32 little-endian usado se a condição for verdadeira |

O handler primeiro grava `cursor+11` como cursor padrão. Se o seletor for maior que 5, retorna nesse cursor sem carregar o byte apontado. Para seletores 0–5, lê o byte no primeiro endereço e, conforme a comparação, pode substituir o cursor pelo destino de `+7..+10`:

| Seletor cru | Condição local que troca o cursor para o segundo destino |
|---:|---|
| `0` | byte apontado = byte `+6` |
| `1` | byte apontado ≠ byte `+6` |
| `2` | byte apontado > byte `+6` (comparação unsigned) |
| `3` | byte apontado < byte `+6` (comparação unsigned) |
| `4` | AND entre byte apontado e byte `+6` é não-zero |
| `5` | AND entre byte apontado e byte `+6` é zero |

Quando a condição selecionada é falsa, o cursor permanece em `cursor+11`. Não há chamada a helper nesse handler.

## Cruzamento semântico upstream — separado da prova local

A tabela upstream nomeia `0x27`, `0x28` e `0x29` como `Cmd_decrementmultihit`, `Cmd_goto` e `Cmd_jumpifbyte`. A implementação upstream usa o byte de `0x02023D72` como contador de golpes, define `goto` como leitura do ponteiro inline e associa os seletores `0..5` a igualdade, desigualdade, maior, menor, bits comuns e ausência de bits comuns. Os padrões de decremento, offsets e ramos registrados acima foram confirmados localmente; os nomes não são símbolos recuperados da ROM BR.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_jump_byte_commands.py
python scripts/inspect_battle_jump_byte_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador valida SHA-256, dispatch, assinaturas Thumb, literais globais e destinos da jump table local. Não valida o conteúdo dos endereços fornecidos pelos scripts nem simula a máquina de batalha. Permanecem pendentes os callers concretos, a origem dos valores/códigos de comparação e a relação dinâmica desses saltos com os handlers anteriores. Este recorte não equivale a cobertura global; `0x23` também segue com estados intermediários sem análise completa.
