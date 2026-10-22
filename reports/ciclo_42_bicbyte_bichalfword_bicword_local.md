# Ciclo 42 — handlers locais `0x36`–`0x38`: BIC de byte, halfword e word

**Estado:** os três handlers limpam bits no valor apontado aplicando AND com o complemento de uma máscara inline da mesma largura. Gravam o resultado no mesmo endereço e avançam o cursor em 6, 7 ou 9 bytes conforme a largura.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset no arquivo + `0x08000000`. Dispatch, instruções, operands e literais de cursor conferidos diretamente; desmontagem Thumb estática com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Cross-reference apenas para nomes/semântica: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, `src/battle_script_commands.c` (SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`).
- REA/Ghidra não foram usados. Não houve execução dinâmica, alteração da ROM, validação de alinhamento/endereço indireto, nem busca de callers concretos.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x36` | `0x08022B61` | `0x08022B60` |
| `0x37` | `0x08022B8D` | `0x08022B8C` |
| `0x38` | `0x08022BC5` | `0x08022BC4` |

## Evidência local — opcode `0x36`

- `cursor+1..cursor+4`: endereço u32 little-endian do byte alvo.
- `cursor+5`: máscara u8.
- Lê o byte, aplica `valor & ~máscara` (instrução `BICS`) e grava com `STRB` no endereço original.
- Avança a word-cursor `0x02023D74` em 6 e retorna.

## Evidência local — opcode `0x37`

- `cursor+1..cursor+4`: endereço u32 little-endian do halfword alvo.
- `cursor+5..cursor+6`: máscara u16 little-endian.
- Lê u16, aplica `valor & ~máscara` e grava com `STRH`.
- Avança `0x02023D74` em 7 e retorna.

## Evidência local — opcode `0x38`

- `cursor+1..cursor+4`: endereço u32 little-endian da word alvo.
- `cursor+5..cursor+8`: máscara u32 little-endian.
- Lê u32, aplica `valor & ~máscara` e grava com `STR`.
- Avança `0x02023D74` em 9 e retorna.

Os três caminhos são in-place e sem branches condicionais ou chamadas observadas. Em cada largura, os bits da máscara são limpos; os demais bits da unidade lida permanecem conforme a operação local.

## Cruzamento semântico upstream — separado da prova local

A tabela upstream nomeia `0x36`, `0x37` e `0x38` como `Cmd_bicbyte`, `Cmd_bichalfword` e `Cmd_bicword`. A implementação upstream também usa AND com complemento da máscara e avanços de 6, 7 e 9 bytes. Os opcodes locais, loads/stores, operands e endereços foram confirmados na ROM; os nomes upstream não são símbolos recuperados da ROM BR.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_bic_commands.py
python scripts/inspect_battle_bic_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador valida SHA-256, dispatch, padrões Thumb, literais do cursor e operations/offsets destacados. Não executa os handlers nem valida os endereços que o bytecode fornece. Permanecem pendentes callers concretos, produtores/consumidores dos operands e validação dinâmica. Este recorte não representa cobertura global; o handler `0x23` e muitos subsistemas ainda têm lacunas.
