# Ciclo 28 — opcode local `0x0E` e caminhos de `resultmessage`

**Estado:** segui o opcode `0x0E` do bytecode amostrado até seu handler, e usei a tabela local para inspecionar também o handler `0x0F`, que seleciona mensagens de resultado. A ROM confirma testes do byte de resultado, chamadas locais de som/mensagem, cursores e destinos de scripts. Os identificadores nominais das flags, sons e mensagens são apenas cruzamentos com o upstream fixado. Não houve validação dinâmica; os caminhos não cobrem todos os estados possíveis.

## Identidade, ferramentas e proveniência

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Desmontagem Thumb local com Capstone 5.0.7 temporário em `/tmp/capstone-py`; verificador auxiliar `scripts/inspect_result_sound_messages.py`.
- Fonte `pret/pokefirered` fixada no commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, usada apenas para cruzar nomes/semântica.
- REA e Ghidra não foram usados; nenhuma batalha foi executada.

## Bytecode e dispatch local

No intervalo lido em `0x081D6931`, a ROM contém bytes `05 06 07 09 0A 0E ...`; o `0x0E` aparece em `0x081D6936`. A tabela de handlers local em `0x0825011C` contém `0x0E→0x0801FAD1` (código alinhado em `0x0801FAD0`) e `0x0F→0x0801FBA1` (código alinhado em `0x0801FBA0`). O handler `0x0F` é examinado pelo dispatch; não se presume que ele seja o próximo comando imediato do trecho observado.

## Evidência local — opcode `0x0E`

O handler lê a word em `0x02023BC8`. Se não-zero, retorna sem avançar o cursor. Caso contrário, copia o byte de `0x02023D6C` para `0x02023BC4` e lê o byte de resultado em `0x02023DCC`.

- Se bit `0x01` estiver ativo, salta a seleção de som.
- Senão, remove bit `0x01` (`flags & 0xFE`) e compara o resultado com `0x02`, `0x04`, `0x08`, `0x10`, `0x20`, `0x40` e `0x80` em diferentes ramos.
- Em ramos selecionados, chama `0x0800E9C4` com `r0=0` e IDs imediatos `0x0E`, `0x0C` ou `0x0D`; em seguida chama `0x08017248` com o battler armazenado em `0x02023BC4`.
- Ramos associados localmente a valores como `0x08`, `0x20` e combinação `0x28` podem evitar a chamada de som.
- O caminho sem controller ocupado incrementa `0x02023D74` em 1 e retorna. Se o controller estiver ocupado, não avança.

A ROM confirma os valores testados, chamadas e IDs imediatos. Nomear os IDs como sons de efetividade ou atribuir os bits aos estados de batalha é cruzamento semântico.

## Evidência local — opcode `0x0F`

Se `0x02023BC8` não for zero, o handler retorna sem avançar. Caso contrário, lê o byte de resultado em `0x02023DCC` e usa o ponteiro local `0x083FE514` em um dos caminhos que consulta o byte `0x02023E82 + 6`; a rotina obtém um halfword indexado e prepara a rota de mensagem. O byte `0x02023E82 + 7` é definido como `1` nos caminhos comuns antes da seleção de resultado.

O handler mascara/examina bits do byte de resultado e contém ramos com imediatos locais `0xDE`, `0xDD`, `0xDA`, `0x99`, `0x1B` e `0xE5`. Os caminhos comuns com mensagem passam o imediato e o byte em `0x02023D6B` ao helper `0x080173AC`, depois incrementam `0x02023D74` em 1. Um ramo sem string zera o byte `0x02023E82 + 7` e segue ao avanço comum.

Três ramos especiais alteram o byte de resultado e redirecionam o script após chamar `0x08017544`:

- o ramo local que testa o valor `0x10` limpa bits por máscaras `0xEF`, `0xFD` e `0xFB` e grava `0x081D8FE4` no cursor `0x02023D74`;
- o ramo que testa `0x40` conserva `flags & 0x3F` e grava `0x081D8FDD` no cursor;
- o ramo que testa `0x80` lê o halfword do registro selecionado em `0x02023BE4 + index × 0x58 + 0x2E`, grava-o em `0x02023D68`, copia o índice para `0x02023D6F`, conserva `flags & 0x3F` e grava `0x081D9641` no cursor.

No caminho especial de `0x0F`, não ocorre o incremento linear comum depois do redirecionamento. A função também contém uma consulta a tabela em `0x083FE514`; seu layout completo e todos os casos de índice não foram reconstruídos aqui.

## Cruzamento upstream — rótulos, não prova local

Na árvore fixada, os índices `0x0E` e `0x0F` são `Cmd_effectivenesssound` e `Cmd_resultmessage`. A fonte associa os testes do handler `0x0E` às flags missed/super-effective/not-very-effective/no-effect/failed e aos sons correspondentes. O handler `0x0F` seleciona mensagens de falha, efetividade, crítico/KO, Endure e Focus Band, entre outras; os caminhos especiais podem empilhar o cursor e saltar para scripts próprios.

As constantes de `MOVE_RESULT_*` são bits do byte (incluindo `MISSED=0x01`, `SUPER_EFFECTIVE=0x02`, `NOT_VERY_EFFECTIVE=0x04`, `DOESNT_AFFECT_FOE=0x08`, `ONE_HIT_KO=0x10`, `FAILED=0x20`, `FOE_ENDURED=0x40`, `FOE_HUNG_ON=0x80`). Os imediatos de mensagem observados localmente coincidem com IDs simbólicos no upstream, mas esse mapeamento não é apresentado como nome nativo encontrado na ROM.

Arquivo upstream consultado (SHA-256):

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`.
- `include/constants/battle.h`: `b9d0493af4629d450050637e9aace63b684b282f841bed2a0d97b1d71e9d55e3`;
- `include/constants/battle_string_ids.h`: `4766f2d31c75a31c0cc2e2dfc7be80b9887820ca3153aabdfb93cb2c3419f246`;
- `include/constants/battle_script_commands.h`: `2365a9d5581325edcf41bf654ebbe70df6dea89defdf4f51bb0c962637444b30`.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_result_sound_messages.py
python scripts/inspect_result_sound_messages.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador checa hash, dispatch, bytes de entrada, operações representativas e literais/destinos. Não prova todas as rotas nem valida som ou mensagem em execução. Permanecem pendentes a decodificação completa da tabela em `0x083FE514`, o seguimento dos scripts de desvio e os handlers posteriores ao opcode `0x0F`. Análise permanece estática e parcial.
