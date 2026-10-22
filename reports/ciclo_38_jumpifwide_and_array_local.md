# Ciclo 38 — handlers locais `0x2A`–`0x2C`: comparações halfword/word e arrays

**Estado:** `0x2A` lê um halfword por endereço indireto e compara com um imediato u16; `0x2B` faz operação análoga para uma word u32; ambos usam seis condições locais e um destino inline. `0x2C` compara byte a byte dois arrays por um tamanho u8 e salta ao destino inline apenas se todos os bytes forem iguais.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset no arquivo + `0x08000000`. Dispatch, instruções e tabelas locais conferidos diretamente; desmontagem Thumb estática com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Cross-reference apenas para nomes/semântica: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, `src/battle_script_commands.c` (SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`).
- REA/Ghidra não foram usados. Não houve execução dinâmica, alteração da ROM ou validação de validade/alinhamento dos endereços recebidos como operands. Não foram identificados callers concretos nesta fatia.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x2A` | `0x08022711` | `0x08022710` |
| `0x2B` | `0x080227B9` | `0x080227B8` |
| `0x2C` | `0x0802286D` | `0x0802286C` |

## Evidência local — opcode `0x2A`

O cursor lê estes operands e avança 12 bytes no caminho padrão:

| Offset | Uso observado |
|---:|---|
| `+1` | seletor u8 |
| `+2..+5` | endereço u32 little-endian de um halfword a ler |
| `+6..+7` | valor u16 little-endian |
| `+8..+11` | destino u32 little-endian |

Armazena `cursor+12` como cursor antes de despachar. Seletor maior que 5 retorna sem ler o halfword. Para seletores 0–5, lê `u16` em `*(u16 *)endereço`; quando a condição é verdadeira, troca o cursor para o destino inline. Se falsa, deixa `cursor+12`.

| Seletor | Condição local para trocar ao destino |
|---:|---|
| `0` | halfword = valor |
| `1` | halfword ≠ valor |
| `2` | halfword > valor (unsigned) |
| `3` | halfword < valor (unsigned) |
| `4` | AND dos dois u16 é não-zero |
| `5` | AND dos dois u16 é zero |

Não há chamada a helper; a dispatch é por jump table local em `0x08022760`.

## Evidência local — opcode `0x2B`

O cursor lê os operands e avança 14 bytes no caminho padrão:

| Offset | Uso observado |
|---:|---|
| `+1` | seletor u8 |
| `+2..+5` | endereço u32 little-endian de uma word a ler |
| `+6..+9` | valor u32 little-endian |
| `+10..+13` | destino u32 little-endian |

Armazena `cursor+14` antes do dispatch. Seletor maior que 5 retorna sem ler a word. Para seletores 0–5, lê `u32` no endereço indireto e usa a mesma família de seis condições do `0x2A`, em largura de 32 bits. Condição verdadeira substitui o cursor pelo destino inline; falsa mantém `cursor+14`. A jump table local começa em `0x08022814`. Nenhum helper é chamado.

## Evidência local — opcode `0x2C`

Lê três operands antes do loop:

| Offset | Uso observado |
|---:|---|
| `+1..+4` | endereço u32 little-endian do primeiro array |
| `+5..+8` | endereço u32 little-endian do segundo array |
| `+9` | tamanho u8 |
| `+10..+13` | destino u32 little-endian se todos os bytes coincidirem |

Compara os arrays byte a byte, avançando os dois endereços e um índice local. No primeiro par desigual, grava `cursor+14` e retorna. Se o índice alcançar o tamanho sem divergência, grava o destino inline. Portanto tamanho zero também alcança o caminho de igualdade, pois a comparação inicial do índice com tamanho encerra o loop e os valores são iguais. Não há chamada a helper.

## Cruzamento semântico upstream — separado da prova local

A tabela upstream nomeia `0x2A`, `0x2B` e `0x2C` como `Cmd_jumpifhalfword`, `Cmd_jumpifword` e `Cmd_jumpifarrayequal`. O código upstream interpreta os operands como ponteiros/valores de comparação e define o array como igual quando todos os bytes do comprimento indicado correspondem. Os offsets, larguras de leitura, condições e atualizações de cursor descritos acima foram observados na ROM local; os nomes não são símbolos recuperados da ROM BR.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_wide_array_commands.py
python scripts/inspect_battle_wide_array_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador valida SHA-256, dispatch, padrões Thumb, literais do cursor e destinos das jump tables. Não simula os handlers nem valida os endereços/valores fornecidos nos scripts. Permanecem pendentes callers concretos, origem dos selectors e valores, significado dos campos apontados e validação dinâmica. Este recorte não equivale a cobertura global; há estados não analisados no handler `0x23` e muitos outros subsistemas sem cobertura.
