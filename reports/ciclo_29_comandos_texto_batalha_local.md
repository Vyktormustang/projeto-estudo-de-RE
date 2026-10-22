# Ciclo 29 — comandos locais de texto `0x10`–`0x12`

**Estado:** foram seguidos os opcodes `0x10`, `0x11` e `0x12` da tabela local até os handlers em `0x0801FD50`, `0x0801FD90` e `0x0801FDD4`. A ROM confirma a leitura de operands u16, chamadas a helpers, atualização de uma flag de exibição e avanço de cursor de três bytes; o opcode `0x12` também mantém um contador halfword e espera por um limite. Os nomes de comandos e a semântica nominal do operand vêm do cruzamento upstream, não de símbolos locais.

## Proveniência e ferramentas

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset do arquivo + `0x08000000`.
- Desmontagem Thumb local com Capstone 5.0.7 temporário em `/tmp/capstone-py`; conferência auxiliar em `scripts/inspect_battle_text_commands.py`.
- A fonte upstream consultada é `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; nomes são cruzamento semântico.
- REA e Ghidra não foram usados; não houve execução de batalha/emulador.

## Dispatch local

A tabela em `0x0825011C` contém os ponteiros Thumb:

| Opcode | Ponteiro | Código começa em |
|---|---:|---:|
| `0x10` | `0x0801FD51` | `0x0801FD50` |
| `0x11` | `0x0801FD91` | `0x0801FD90` |
| `0x12` | `0x0801FDD5` | `0x0801FDD4` |

O relatório descreve os handlers a partir da ROM; a tabela upstream é usada apenas para seus nomes correspondentes.

## Evidência local — opcode `0x10`

O handler lê a word em `0x02023BC8`; se não-zero, retorna sem avançar. Caso contrário, lê os bytes `cursor + 1` e `cursor + 2`, combina-os little-endian em um valor de 16 bits e chama `0x080173AC` com esse valor e o byte lido de `0x02023D6B`. Depois incrementa `0x02023D74` em 3 e define o byte `0x02023E82 + 7` como 1.

## Evidência local — opcode `0x11`

A rotina copia o byte de `0x02023D6B` para `0x02023BC4`, lê e combina os bytes `cursor + 1`/`+2`, chama `0x0800E3EC` com argumento inicial zero e o halfword, e chama `0x08017248` com o byte copiado. Em seguida avança o cursor em 3 e define `0x02023E82 + 7` como 1. No recorte local não há teste inicial de `0x02023BC8` equivalente ao dos opcodes `0x10`/`0x12`.

## Evidência local — opcode `0x12`

A rotina retorna sem alterar o cursor quando a word `0x02023BC8` não é zero. Caso esteja livre, verifica o byte `0x02023E82 + 7`:

- Se zero, incrementa o cursor `0x02023D74` em 3 e retorna.
- Se diferente de zero, lê o halfword inline em `cursor + 1`/`+2`, incrementa o halfword em `0x02023E7C` e compara o contador atualizado ao operand. Enquanto o contador for menor que o operand, retorna sem avanço. Quando o contador é igual ou maior, zera o halfword `0x02023E7C`, avança o cursor em 3, limpa `0x02023E82 + 7` e retorna.

A ROM confirma o fluxo de sincronização e as operações numéricas; não houve medição dinâmica do tempo nem validação da unidade do operand.

## Cruzamento upstream — nomes e rótulos

Na tabela `gBattleScriptingCommandsTable` da fonte fixada, os índices `0x10`, `0x11` e `0x12` são `Cmd_printstring`, `Cmd_printselectionstring` e `Cmd_waitmessage`. A fonte interpreta o halfword `cursor + 1` como ID de string para `0x10`/`0x11` e como tempo de espera para `0x12`; associa `0x080173AC` à preparação de texto, `0x0800E3EC` à emissão de uma string de seleção, e o byte de offset 7 em `gBattleCommunication` a `MSG_DISPLAY`. Esses nomes explicam os caminhos locais, mas permanecem cruzamento externo.

Arquivo upstream consultado (SHA-256):

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`;
- `include/constants/battle_script_commands.h`: `2365a9d5581325edcf41bf654ebbe70df6dea89defdf4f51bb0c962637444b30`.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_text_commands.py
python scripts/inspect_battle_text_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador checa hash, ponteiros locais, sequências Thumb, literais, combinações de operand e cursor. Não valida execução de texto, efeitos do controller nem compatibilidade completa da fonte upstream. Ficam pendentes os handlers seguintes, consumidores adicionais de `MSG_DISPLAY`, codificação/uso completo das strings e testes dinâmicos. Não se afirma cobertura global.
