# Ciclo 34 — condições locais `0x1E`–`0x20`

**Estado:** a ROM confirma três handlers condicionais com operands e redirecionamentos distintos. `0x1E` escolhe entre duas consultas auxiliares ou uma comparação direta de byte; `0x1F` seleciona um halfword por lado e testa uma máscara; `0x20` despacha seis modos de comparação sobre um byte de registro. Os fatos locais e os nomes/semântica upstream permanecem separados.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset do arquivo + `0x08000000`. Dispatch e bytes foram conferidos diretamente; desmontagem Thumb com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Upstream `pret/pokefirered` fixado em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, usado só para nomes e interpretação cruzada.
- REA/Ghidra não foram usados; não houve execução dinâmica nem alteração da ROM.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x1E` | `0x08021731` | `0x08021730` |
| `0x1F` | `0x08021819` | `0x08021818` |
| `0x20` | `0x08021891` | `0x08021890` |

## Evidência local — opcode `0x1E`

O handler lê de `0x02023D74` um seletor em `cursor+1`, um byte em `cursor+2` e um endereço u32 little-endian em `cursor+3..cursor+6`.

- Se o seletor for `8`, chama `0x08019F18` com imediato `0x0D`, o byte de `0x02023D6B` e o byte de `cursor+2` (demais argumentos zero). Se o retorno for zero, avança o cursor em 7. Se não, grava o byte de `cursor+2` em `0x02023D6A`, redireciona o cursor ao endereço inline, usa `retorno-1` e o byte salvo em chamada a `0x080C71D0`, e grava `retorno-1` em `0x02023FC4+0x15`.
- Se o seletor for `9`, faz chamada análoga a `0x08019F18`, mas com imediato `0x0C`; os ramos de retorno e gravações são equivalentes.
- Para outros valores do seletor, passa `cursor+1` a `0x08016E24`; compara o byte `cursor+2` ao byte `0x02023BE4 + battler×0x58 + 0x20`. Em igualdade, salva esse byte em `0x02023D6A`, grava o destino inline no cursor, chama `0x080C71D0` com o battler e o byte, e grava o battler em `0x02023FC4+0x15`. Se diferentes, avança o cursor em 7.

O handler consome 7 bytes quando não redireciona (opcode + seletor + byte + destino de 4 bytes). Endereços de helpers e campos acima são locais; seus nomes e propósitos não são inferidos apenas desses bytes.

## Evidência local — opcode `0x1F`

- Se `cursor+1` for `1`, usa o byte `0x02023D6B`; para qualquer outro valor, usa `0x02023D6C`. Em ambos os casos chama `0x080751D8` e usa o bit menos significativo do retorno como índice `0`/`1`.
- Lê uma máscara u16 little-endian de `cursor+2..cursor+3` e um destino u32 little-endian de `cursor+4..cursor+7`.
- Lê o halfword em `0x02023DDE + índice×2` e faz AND com a máscara. Se não-zero, grava o destino inline no word de cursor `0x02023D74`; caso contrário, avança o cursor em 8.

## Evidência local — opcode `0x20`

- Mapeia o byte `cursor+1` com `0x08016E24`.
- Usa o byte `cursor+3` como deslocamento para ler um byte em `0x02023BE4 + battler×0x58 + 0x18 + deslocamento`.
- O byte `cursor+2` seleciona uma entrada de uma tabela local de seis destinos de código em `0x080218D0`. Valores maiores que 5 seguem diretamente ao caminho falso.
- As seis rotinas comparam o byte lido com o byte `cursor+4`, em ordem: igual; diferente; maior; menor; bits em comum; nenhum bit em comum. O teste de comparação bem-sucedido soma 1 ao acumulador local; se o acumulador for não-zero, o handler lê um destino u32 de `cursor+5..cursor+8` e substitui o cursor por esse destino. Caso contrário (inclusive modo >5), avança o cursor em 9.

## Cruzamento semântico upstream — separado da prova local

Na tabela upstream `gBattleScriptingCommandsTable`, os índices `0x1E`, `0x1F` e `0x20` são `Cmd_jumpifability`, `Cmd_jumpifsideaffecting` e `Cmd_jumpifstat`. A fonte interpreta os seletores `8`/`9` como referências a lados relativos ao atacante; as chamadas locais de `0x1E` como busca de habilidade e registro de habilidade; `0x1F` como teste de flags de lado; e os modos de `0x20` como comparações de stat stages. Essas denominações não são símbolos locais da ROM BR.

Fonte cruzada: `src/battle_script_commands.c`, SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_condition_commands.py
python scripts/inspect_battle_condition_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador confirma identidade/hash, dispatch, padrões Thumb e literais-chave. Não executa batalha, não valida resultados reais de consulta/comparação e não enumera todos os scripts/callers concretos. Permanecem pendentes a ligação desses handlers a callers reais, a validação dinâmica e outros comandos/subsistemas. Este recorte é estático e parcial; não declara cobertura global.
