# Ciclo 36 — handlers locais `0x24`–`0x26`: contagem, limpeza e contador

**Estado:** `0x24` aguarda um word de controle, percorre duas áreas de seis registros e, em um caminho condicional, conta posições de battler e decide entre destino inline e cursor `+5`. `0x25` delega a limpeza a uma rotina local e avança `+1`. `0x26` copia um byte inline para um endereço global e avança `+2`. Nomes e interpretações upstream estão separados.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset do arquivo + `0x08000000`. Dispatch e bytes conferidos diretamente; desmontagem Thumb com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Upstream `pret/pokefirered` fixado em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, utilizado apenas para nomes e interpretação cruzada.
- REA/Ghidra não foram usados; não houve execução dinâmica nem alteração da ROM. O handler `0x24` foi seguido estaticamente pelos loops e ramos principais, mas a identidade semântica dos seletores e flags vem do cross-reference.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x24` | `0x080223F9` | `0x080223F8` |
| `0x25` | `0x080225D9` | `0x080225D8` |
| `0x26` | `0x080225F1` | `0x080225F0` |

## Evidência local — opcode `0x24`

1. Lê a word `0x02023BC8`; se não-zero, retorna sem avançar o cursor.
2. Em caso zero, percorre índices 0–5 com stride de `0x64` bytes a partir de `0x02024284`. Para cada registro, chama `0x0803FBE8` com seletores imediatos `0x0B`, `0x2D` e, nos ramos que passam pelos dois primeiros testes, `0x39`; soma o último retorno a um acumulador u16.
3. Repete uma varredura equivalente usando `0x0202402C` como endereço-base fixo. Se o acumulador de cada varredura for zero, ORa respectivamente `0x02` e `0x01` no byte `0x02023E8A`.
4. Se `0x02023E8A` estiver não-zero, ou o bit `0x02` não estiver ativo na word `0x02022B4C`, segue ao caminho que soma 5 à word de cursor `0x02023D74`.
5. No ramo restante, percorre duas sequências de índices pares/ímpares até o byte de contagem em `0x02023BCC`. Testa bits deslocados a partir de `0x01000000` contra a word `0x02023DD0` e examina bytes em blocos de stride `0x28` baseados em `0x02023ECC`, acumulando dois contadores locais. Se o bit `0x40` estiver ativo em `0x02022B4C`, redireciona ao destino u32 inline em `cursor+1..cursor+4` quando a soma dos contadores for maior que 1; sem esse bit, redireciona quando ambos os contadores forem não-zero. Nos demais casos, avança o cursor em 5.

As chamadas diretas observadas na rotina são para `0x0803FBE8`; os argumentos/offsets acima são os valores locais, sem atribuição local de nomes de campos. Os ramos que não aguardam o word de controle sempre escolhem entre o endereço inline de quatro bytes e o avanço `+5` descrito.

## Evidência local — opcode `0x25` e rotina chamada

O wrapper em `0x080225D8` chama `0x08022598` e incrementa `0x02023D74` em 1.

Na rotina local `0x08022598`, foram observadas as seguintes escritas antes do retorno:

- `0` em `0x02023DCC`;
- `1` em `0x02023FC4+0x0E` e em `0x02023D71`;
- `0` em `0x02023E82+3` e `0x02023E82+6`;
- limpa os bits `0x0040` e `0x4000` da word `0x02023DD0`: primeiro aplica `0xFFFFFFBF` (via `1 - 0x42`) e depois AND com a máscara literal `0xFFFFBFFF`.

## Evidência local — opcode `0x26`

Lê o byte `cursor+1`, grava-o em `0x02023D72`, soma 2 à word do cursor `0x02023D74` e retorna. O handler não chama outra rotina.

## Cruzamento semântico upstream — separado da prova local

Na tabela upstream `gBattleScriptingCommandsTable`, `0x24`, `0x25` e `0x26` são `Cmd_checkteamslost`, `Cmd_movevaluescleanup` e `Cmd_setmultihit`. A implementação upstream interpreta `0x24` como soma de HP elegível nas duas parties e, em batalhas link, teste de posições vazias para determinar se usa o ponteiro inline; chama a rotina de `0x08022598` `MoveValuesCleanUp`; e interpreta o byte de `0x26` como o contador de golpes. Esses nomes não são símbolos da ROM local; a evidência local é a estrutura de loops, os seletores crus, os endereços, bits, chamadas e cursor registrados acima.

Fonte cruzada: `src/battle_script_commands.c`, SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`.

## Reprodução e limites

```bash
python -m py_compile scripts/inspect_battle_team_cleanup_commands.py
python scripts/inspect_battle_team_cleanup_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador confirma hash, dispatch, padrões Thumb e literais destacados. Não emula batalha nem valida os resultados retornados por `0x0803FBE8`. Permanecem pendentes a semântica local dos seletores, callers concretos, interação dinâmica entre os ramos de `0x24` e o restante da tabela de comandos. O recorte é parcial e não declara cobertura global.
