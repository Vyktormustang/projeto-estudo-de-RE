# Ciclo 41 — handlers locais `0x33`–`0x35`: OR de byte, halfword e word

**Estado:** os três handlers fazem OR bit a bit entre o conteúdo de um endereço inline indireto e um imediato do mesmo tamanho; escrevem o resultado no próprio endereço e avançam o cursor conforme a largura do immediate. Não há ramo condicional nem chamada a helper observados.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset no arquivo + `0x08000000`. Dispatch, instruções, operands e literais de cursor conferidos diretamente; desmontagem Thumb estática com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Cross-reference apenas para nomes/semântica: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, `src/battle_script_commands.c` (SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`).
- REA/Ghidra não foram usados. Não houve execução dinâmica, alteração da ROM, validação de alinhamento/endereço indireto, nem busca de callers concretos.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x33` | `0x08022AB9` | `0x08022AB8` |
| `0x34` | `0x08022AE5` | `0x08022AE4` |
| `0x35` | `0x08022B1D` | `0x08022B1C` |

## Evidência local — opcode `0x33`

- `cursor+1..cursor+4`: endereço u32 little-endian do byte alvo.
- `cursor+5`: imediato u8.
- Lê o byte do endereço, aplica OR com o imediato e grava de volta com `STRB`.
- Soma 6 à word-cursor `0x02023D74` e retorna.

## Evidência local — opcode `0x34`

- `cursor+1..cursor+4`: endereço u32 little-endian do halfword alvo.
- `cursor+5..cursor+6`: imediato u16 little-endian.
- Lê u16 no endereço, aplica OR e grava o resultado com `STRH`.
- Soma 7 à word-cursor `0x02023D74` e retorna.

## Evidência local — opcode `0x35`

- `cursor+1..cursor+4`: endereço u32 little-endian da word alvo.
- `cursor+5..cursor+8`: imediato u32 little-endian.
- Lê u32 no endereço, aplica OR e grava de volta com `STR`.
- Soma 9 à word-cursor `0x02023D74` e retorna.

Os três handlers são in-place: os valores existentes não são substituídos sem condição; cada resultado é o OR entre o valor lido e o imediato. Não há outra escrita de estado observada além do endereço alvo e da atualização do cursor.

## Cruzamento semântico upstream — separado da prova local

A tabela upstream nomeia `0x33`, `0x34` e `0x35` como `Cmd_orbyte`, `Cmd_orhalfword` e `Cmd_orword`. O código upstream também os descreve como OR de valores da largura correspondente e os avanços de 6, 7 e 9 bytes. Os opcodes locais, literais, larguras de load/store e offsets foram conferidos na ROM; os nomes upstream não são símbolos recuperados da ROM BR.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_bitwise_commands.py
python scripts/inspect_battle_bitwise_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador valida SHA-256, dispatch, padrões Thumb, literais do cursor e operações/offsets destacados. Não executa handlers nem valida os endereços que o bytecode fornece. Permanecem pendentes callers concretos, produtores/consumidores dos operands e validação dinâmica. Este recorte não representa cobertura global; o handler `0x23` e muitos subsistemas ainda têm lacunas.
