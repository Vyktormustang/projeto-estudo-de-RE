# Ciclo 40 — handlers locais `0x30`–`0x32`: subbyte e cópias de array

**Estado:** `0x30` subtrai um byte imediato do byte apontado e avança `+6`; `0x31` copia um número u8 de bytes entre dois endereços inline e avança `+10`; `0x32` copia bytes de uma origem usando um byte de índice-base indireto e avança `+14`.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset no arquivo + `0x08000000`. Dispatch, operandos, instruções e literais conferidos diretamente; desmontagem Thumb estática com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Cross-reference apenas para nomes/semântica: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, `src/battle_script_commands.c` (SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`).
- REA/Ghidra não foram usados. Não houve execução dinâmica, alteração da ROM, validação dos endereços indiretos ou investigação de callers concretos nesta fatia.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x30` | `0x080229CD` | `0x080229CC` |
| `0x31` | `0x080229F9` | `0x080229F8` |
| `0x32` | `0x08022A4D` | `0x08022A4C` |

## Evidência local — opcode `0x30`

Lê o endereço u32 little-endian em `cursor+1..cursor+4`, lê o byte imediato em `cursor+5`, lê o byte atual do endereço apontado, subtrai o imediato e grava o resultado com `STRB` no mesmo endereço. A gravação preserva os 8 bits baixos (aritmética observada módulo 256). Depois soma 6 à word-cursor `0x02023D74`. Não chama helper.

## Evidência local — opcode `0x31`

Operands:

| Offset | Uso observado |
|---:|---|
| `+1..+4` | endereço u32 little-endian de destino |
| `+5..+8` | endereço u32 little-endian de origem |
| `+9` | comprimento u8 |

Inicializa índice local em zero; enquanto índice `< comprimento`, lê um byte de `origem+índice`, grava em `destino+índice` e incrementa o índice. Para comprimento zero, o loop é ignorado. Em todos os casos, soma 10 à word-cursor `0x02023D74`. Não chama helper. A cópia é uma sequência local de loads/stores byte a byte; sobreposição entre origem e destino não foi testada dinamicamente.

## Evidência local — opcode `0x32`

Operands:

| Offset | Uso observado |
|---:|---|
| `+1..+4` | endereço u32 little-endian de destino |
| `+5..+8` | endereço u32 little-endian de origem |
| `+9..+12` | endereço u32 little-endian de um byte de índice-base |
| `+13` | comprimento u8 |

Para cada índice `i` de 0 a `comprimento-1`, lê o byte em `endereço_indice`, calcula `índice_base+i`, lê `origem+índice_base+i` e grava o byte em `destino+i`. O byte do endereço de índice-base é carregado dentro do loop, não antes dele. Comprimento zero não executa a cópia. O cursor é avançado em 14, inclusive quando o tamanho é zero. Não chama helper.

## Cruzamento semântico upstream — separado da prova local

A tabela upstream nomeia `0x30`, `0x31` e `0x32` como `Cmd_subbyte`, `Cmd_copyarray` e `Cmd_copyarraywithindex`. As implementações upstream também descrevem subtração byte, cópia linear e cópia com índice-base. Os endereços, larguras, ordem de leituras/escritas e avanços acima são evidência local; os nomes não são símbolos recuperados da ROM BR.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_copy_mutation_commands.py
python scripts/inspect_battle_copy_mutation_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador confirma SHA-256, dispatch, padrões Thumb, operandos, cursor e literais. Não executa a ROM nem valida endereços/overlap fornecidos pelo bytecode. Permanecem pendentes callers concretos, produtores/consumidores desses operands e validação dinâmica. Este recorte não representa cobertura global; `0x23` e muitos subsistemas ainda têm lacunas.
