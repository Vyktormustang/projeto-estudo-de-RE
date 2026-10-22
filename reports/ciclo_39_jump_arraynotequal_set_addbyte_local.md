# Ciclo 39 — handlers locais `0x2D`–`0x2F`: array desigual, set byte e add byte

**Estado:** `0x2D` compara duas regiões byte a byte e usa destino inline se detectar diferença; `0x2E` grava um byte imediato em endereço inline indireto; `0x2F` soma um byte imediato ao conteúdo de um endereço indireto e grava o byte resultante.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset no arquivo + `0x08000000`. Dispatch e instruções conferidos diretamente; desmontagem Thumb estática com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Cross-reference apenas para nomes/semântica: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, `src/battle_script_commands.c` (SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`).
- REA/Ghidra não foram usados. Não houve execução dinâmica, alteração da ROM nem validação dos endereços indiretos. Não foram identificados callers concretos nesta fatia.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x2D` | `0x080228F5` | `0x080228F4` |
| `0x2E` | `0x08022979` | `0x08022978` |
| `0x2F` | `0x080229A1` | `0x080229A0` |

## Evidência local — opcode `0x2D`

Os operands lidos a partir do cursor são:

| Offset | Uso observado |
|---:|---|
| `+1..+4` | endereço u32 little-endian da primeira região |
| `+5..+8` | endereço u32 little-endian da segunda região |
| `+9` | tamanho u8 |
| `+10..+13` | destino u32 little-endian em caso de diferença |

O handler compara bytes correspondentes nos dois endereços. Mantém um contador de pares iguais e avança ambos os endereços e o índice até o tamanho. Se o total de bytes iguais for diferente do tamanho, substitui o cursor pelo destino inline; se todos forem iguais, avança o cursor original em 14. Para tamanho zero não percorre dados e toma o avanço `+14`. Não há chamada a helper.

## Evidência local — opcode `0x2E`

Lê um endereço u32 little-endian em `cursor+1..cursor+4` e um byte imediato em `cursor+5`; grava o byte imediato no endereço apontado e soma 6 à word-cursor `0x02023D74`. Não há comparação nem chamada.

## Evidência local — opcode `0x2F`

Lê o mesmo formato de operands do `0x2E`: endereço u32 em `cursor+1..cursor+4` e byte imediato em `cursor+5`. Lê o byte no endereço apontado, soma o imediato e grava o resultado com `STRB` no mesmo endereço; o armazenamento mantém os 8 bits baixos. Em seguida soma 6 à word-cursor `0x02023D74`. Não há chamada a helper.

## Cruzamento semântico upstream — separado da prova local

A tabela upstream nomeia `0x2D`, `0x2E` e `0x2F` como `Cmd_jumpifarraynotequal`, `Cmd_setbyte` e `Cmd_addbyte`. O código upstream também descreve o `0x2D` como salto quando pelo menos um par de bytes difere, e os outros dois como gravação e adição de byte. Os offsets, leitura/comparação e escritas foram conferidos localmente; esses nomes não são símbolos recuperados da ROM BR.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_byte_array_mutations.py
python scripts/inspect_battle_byte_array_mutations.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador valida SHA-256, dispatch, padrões Thumb, endereço local do cursor e operandos destacados. Não emula os handlers, não valida validade/alinhamento dos endereços dos scripts e não demonstra quais regiões reais são passadas. Permanecem pendentes callers concretos, produtores/consumidores desses operands e validação dinâmica. Este recorte não equivale a cobertura global; o handler `0x23` e outros subsistemas continuam com lacunas.
