# Ciclo 45 — handlers locais de batalha `0x3F`–`0x41`

## Escopo e método

Análise estática da ROM BR `google_drive/Pokemon - Fire Red (BR).gba`, 16 MiB, SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`. Os dispatches, bytes Thumb, literais e acessos à memória abaixo foram conferidos na ROM local. Verificador: `scripts/inspect_battle_end3_protect_call_commands.py`.

Capstone 5.0.7 foi instalado temporariamente em `/tmp/capstone-py` e usado para desmontagem estática. Não houve execução dinâmica nem uso de REA/Ghidra neste ciclo. O verificador só confirma hash, dispatch, assinaturas e literais; não prova que estados específicos sejam alcançáveis.

## Dispatch local

A tabela local começa em `0x0825011C`:

| Opcode | Ponteiro Thumb na tabela | Início da instrução |
|---|---:|---:|
| `0x3F` | `0x08022D05` | `0x08022D04` |
| `0x40` | `0x0801DBA1` | `0x0801DBA0` |
| `0x41` | `0x08022D41` | `0x08022D40` |

## Evidência da ROM local

### `0x3F` — restauração de script e seleção de callback

O handler em `0x08022D04` chama `0x0801756C`, já observado no ciclo 44. Em seguida, pela word apontada em `0x02023FF4`, lê outro ponteiro no offset `+0x0C`.

- Nesse objeto, lê o byte `+0x20`. Se for diferente de zero, subtrai 1 e grava o byte de volta; se já for zero, deixa-o em zero.
- Usa o byte resultante como índice de words a partir do ponteiro do objeto (`base + 4 × índice`).
- Grava a word selecionada em `0x03004F84` e retorna.

O handler não verifica localmente que o slot selecionado é válido quando o contador é zero; nesse caso lê o slot de índice zero. O significado/correção desse slot é desconhecido localmente. A chamada inicial a `0x0801756C` decrementa e usa o contador do outro stack, conforme documentado em `reports/ciclo_44_return_end_local.md`.

### `0x40` — teste condicional e salto inline

O handler consulta, em ordem:

1. byte em `0x02023E8C + byte[0x02023D6C] × 0x10`; testa o bit 7 desse byte;
2. halfword em `0x02023D4A`, usado como índice de registros de stride `0x0C` a partir de `0x08250C04`; testa o bit `0x02` do byte no offset `+8` do registro selecionado.

Se qualquer teste falhar, incrementa o cursor em `0x02023D74` em 5 e retorna. Se ambos passarem:

- faz OR de `0x01` no byte `0x02023DCC`;
- chama `0x0801DB10` com `r0=5`, `r1=0`;
- grava byte `1` em `0x02023E88` e retorna.

Na chamada acima, o helper `0x0801DB10` testa `[0x02023DCC] & 0x29`. Como o handler acabou de definir o bit 0, esse teste é não-zero. Nesse ramo, o helper zera dois halfwords indexados pelo byte `0x02023D6C` — em `0x02023DA0 + índice × 2` e `0x02023DA8 + índice × 2` —, monta uma word little-endian com os bytes inline do cursor `+1..+4` e a grava em `0x02023D74`. Portanto, nesse caminho local, o cursor recebe o destino inline; no caminho de falha, avança 5. O propósito semântico dos campos zerados não é atribuído apenas pelos endereços.

### `0x41` — empilha retorno e transfere o cursor

O handler em `0x08022D40` calcula `cursor + 5` e chama `0x08017520`. Esse helper obtém, por meio da word em `0x02023FF4`, o ponteiro no offset `+8`; incrementa o byte contador no offset `+0x20`; e grava o endereço de retorno em uma word no índice antigo (`base + 4 × contador_antigo`). Em seguida, o handler monta uma word little-endian dos quatro bytes inline `cursor+1..+4` e grava-a em `0x02023D74`.

O helper não contém verificação local de limite antes de incrementar o contador/escrever o slot. Se há callers ou estados que podem exceder a capacidade do array não foi determinado.

## Cross-reference upstream — não é prova local

A tabela consultada em `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, nomeia `0x3F`, `0x40` e `0x41` como `Cmd_end3`, `Cmd_jumpifaffectedbyprotect` e `Cmd_call`, respectivamente. Esses nomes e a interpretação funcional são cross-reference; os testes de bits, endereços, writes, calls e cursores descritos acima são observações da ROM BR.

## Limites e continuidade

A fatia não estabelece alcançabilidade dos limites/estados dos dois stacks, nem os significados locais definitivos dos campos `0x02023D6C`, `0x02023DCC`, `0x02023DA0`, `0x02023DA8`, `0x02023E8C` ou `0x02023E88`. As rotinas `0x0802A3F8`/`0x08019F18` do ramo alternativo de `0x0801DB10` não são percorridas por esta chamada específica após a OR local do bit 0, mas permanecem não analisadas noutros callers. Cobertura parcial; sem alegação de compreensão global.
