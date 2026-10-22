# Ciclo 32 — transições locais de status e faint (`0x18`–`0x1A`)

**Estado:** a ROM confirma os handlers `0x18`–`0x1A` na tabela local. `0x18` usa um seletor de battler e um byte de estado para limpar bits de um dos dois halfwords do registro; `0x19` tem dois modos, condiciona a rota principal a presença/HP e modifica cursor e marcadores; `0x1A` espera um word de controle liberar antes de chamar duas rotinas e avançar o cursor. A interpretação nominal fica na seção de cruzamento upstream.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`. Bytes/dispatch foram conferidos diretamente; desmontagem Thumb com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- `pret/pokefirered` fixado em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, usado somente para nomes e interpretação cruzada.
- REA/Ghidra não foram usados; não houve teste dinâmico nem alteração da ROM. O handler `0x19` é longo; o fluxo principal e transições visíveis foram seguidos, mas todos os sub-ramos de contadores, condições especiais e chamadas ainda não foram identificados em termos locais.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x18` | `0x08021231` | `0x08021230` |
| `0x19` | `0x080212AD` | `0x080212AC` |
| `0x1A` | `0x080215A1` | `0x080215A0` |

## Evidência local — opcode `0x18`

1. Lê o byte `cursor+1` (`cursor` em `0x02023D74`), passa-o a `0x08016E24` e grava o retorno no byte `0x02023BC4`.
2. Lê o byte `0x02023E82+3` como índice. Se `<=6`, seleciona um word na tabela `0x0825053C` por `índice×4` e limpa os bits indicados no word em `0x02023BE4 + battler×0x58 + 0x4C`. Se `>6`, a seleção usa a mesma tabela e limpa o word em `0x02023BE4 + battler×0x58 + 0x50`. A operação local é `old_value & ~mask`.
3. Zera `0x02023E82+3`, avança `0x02023D74` em 2 e zera o byte `0x02023FC4+0x16` (`0x02023FDA`). Retorna.

O código local mostra a bifurcação por índice e os offsets gravados; o que esses halfwords e índices representam nominalmente é cross-reference.

## Evidência local — opcode `0x19`

O handler lê `cursor[2]` (`cursor` em `0x02023D74`) e tem dois caminhos estruturais:

### `cursor[2] != 0`

- Mapeia `cursor[1]` por `0x08016E24` e grava o byte resultante em `0x02023BC4`.
- Forma uma máscara a partir do byte selecionado e da tabela `0x0825E45C`; compara essa máscara com a word `0x02023DD0`. Se o bit correspondente estiver ausente, o caminho comum em `0x0802158C` avança o cursor em 7.
- Se o bit estiver presente, remonta em little-endian o word nos bytes `cursor+3..cursor+6`, chama `0x0801756C` e grava o valor de 32 bits no word do cursor. Em seguida, uma chamada a `0x080751C4` seleciona um bit; o código limpa o bit `0x0200` de um halfword na região indexada a partir de `0x02023DDE` e retorna pelo epílogo, sem o incremento comum de 7.

### `cursor[2] == 0`

- Compara `cursor[1]` a 1. O valor 1 seleciona bytes locais `0x02023D6B`/`0x02023D6C` em uma ordem, grava o battler ativo em `0x02023BC4` e escolhe o ponteiro inicial `0x081D8674`. Outros valores invertem a seleção e escolhem `0x081D8684`.
- Usa o byte ativo para testar a máscara correspondente da tabela `0x0825E45C` contra o byte `0x02023D70`. Quando o bit testado está presente, ou quando o halfword de HP em `0x02023BE4 + battler×0x58 + 0x28` não é zero, segue ao incremento comum do cursor em 7.
- Quando o bit não está presente e esse halfword é zero, ORa a máscara de battler (deslocada em 28) na word `0x02023DD0`, chama `0x08017520` com `cursor+7` e grava o ponteiro selecionado (`0x081D8674` ou `0x081D8684`) na word do cursor. O restante do handler tem ramos adicionais: consulta outros bits/bytes, modifica words e bytes de estado, faz chamadas auxiliares e, em alguns caminhos, troca novamente o destino do cursor. Um destino constante observado nesse trecho é `0x081D8C6C`; não foi possível nomear localmente todos os sub-ramos.

Além do caminho de avanço `+7`, a ROM mostra redirecionamentos do cursor por words montados ou ponteiros escolhidos, e uma chamada usada antes de salvar `cursor+7`. As chamadas diretas observadas no handler incluem `0x08016E24`, `0x0801756C`, `0x080751C4`, `0x08017520`, `0x0802E228`, `0x0803FBE8`, `0x0800DFF0` e `0x08017248`. As funções auxiliares não foram renomeadas como fato local.

## Evidência local — opcode `0x1A`

- Se a word `0x02023BC8` for não-zero, retorna sem alterar o cursor.
- Caso contrário, mapeia `cursor+1` com `0x08016E24` e grava o byte retornado em `0x02023BC4`.
- Chama `0x0800E134` com argumento inicial zero, depois chama `0x08017248` com o byte em `0x02023BC4`.
- Avança a word em `0x02023D74` em 2 e retorna. O handler não consome mais operandos nesse caminho.

## Cruzamento semântico upstream — separado da prova local

Na `gBattleScriptingCommandsTable` da fonte fixada, `0x18`–`0x1A` correspondem a `Cmd_clearstatusfromeffect`, `Cmd_tryfaintmon` e `Cmd_dofaintanimation`. A fonte upstream interpreta os campos de registro como status1/status2 e flags de efeitos; chama o helper do opcode `0x19` de `GetBattlerForBattleScript`, identifica destinos como scripts de faint e descreve ramificações de faint do atacante/alvo, side-status, contadores, Destiny Bond e Grudge. Para `0x1A`, upstream descreve a espera dos controladores e uma animação de faint. Esses rótulos e explicações não são símbolos da ROM local; as evidências locais são endereços, bytes, comparações, masks, chamadas e escritas descritos acima.

Fonte cruzada: `src/battle_script_commands.c`, SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`.

## Reprodução e itens em aberto

```bash
python -m py_compile scripts/inspect_battle_faint_status_commands.py
python scripts/inspect_battle_faint_status_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador confirma hash, dispatch, sequências Thumb e literais-chave. Não executa batalha nem prova o efeito dinâmico. Pendem a nomeação local de campos/auxiliares, o rastreio integral dos sub-ramos do `0x19`, callers/bytes concretos e validação dinâmica. Este recorte é parcial e não declara cobertura global.
