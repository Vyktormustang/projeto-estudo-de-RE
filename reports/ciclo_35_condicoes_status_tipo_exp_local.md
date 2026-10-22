# Ciclo 35 — handlers locais `0x21`–`0x23`: condições e máquina de estados

**Estado:** `0x21` lê máscara, seletor de inversão e destino inline; `0x22` compara um byte contra dois campos do registro escolhido; `0x23` inicia uma máquina local de sete estados, com dispatch indexado e retorno final condicionado a um word global. O handler `0x23` é extenso: o relatório cobre o prólogo, dispatch e saída terminal, não a implementação integral dos sete estados.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset do arquivo + `0x08000000`. Dispatch e bytes conferidos diretamente; desmontagem Thumb via Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Upstream `pret/pokefirered` fixado em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, usado somente para rótulos e semântica cruzada.
- REA/Ghidra não foram usados; não houve validação dinâmica nem alteração da ROM. A análise de `0x23` é deliberadamente parcial devido à extensão da rotina.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x21` | `0x08021989` | `0x08021988` |
| `0x22` | `0x08021A0D` | `0x08021A0C` |
| `0x23` | `0x08021A69` | `0x08021A68` |

## Evidência local — opcode `0x21`

- Lê `cursor+1`, passa o byte por `0x08016E24` e grava o resultado em `0x02023BC4`.
- Lê uma máscara u32 little-endian de `cursor+2..cursor+5`, um byte de condição em `cursor+6` e um destino u32 little-endian em `cursor+7..cursor+10`.
- Lê um word em `0x02023DFC + battler×4` e calcula AND com a máscara. Se `cursor+6` for não-zero, AND igual a zero redireciona `0x02023D74` ao destino inline; AND não-zero avança o cursor em 11. Se `cursor+6` for zero, AND não-zero redireciona; AND zero avança em 11.

Portanto, localmente o byte `cursor+6` inverte qual resultado do teste leva ao salto. O handler consome 11 bytes quando não salta.

## Evidência local — opcode `0x22`

- Mapeia `cursor+1` com `0x08016E24`; lê o byte de comparação em `cursor+2` e remonta o destino u32 little-endian de `cursor+3..cursor+6`.
- Calcula a base `0x02023BE4 + battler×0x58` e compara o byte `cursor+2` com os bytes nos offsets `+0x21` e `+0x22`.
- Se qualquer comparação for igual, substitui o word `0x02023D74` pelo destino inline; se ambas forem diferentes, avança o cursor em 7.

## Evidência local — opcode `0x23` (recorte parcial)

### Entrada e dispatch de estados

- Lê o seletor em `cursor+1`, chama `0x08016E24` e grava o byte resultante em `0x02023D6D`.
- Usa `(byte & 2) >> 1` para selecionar um byte em `0x02023F4E + índice`, mantido em registrador durante o fluxo observado.
- Lê o byte `0x02023FC4+0x1C` (`0x02023FE0`) como índice de dispatch. Se for maior que 6, chama o epílogo interno em `0x080223DA`, retornando sem executar a tabela nesse percurso.
- A tabela local de destinos começa em `0x08021AC8` e contém sete words: `0x08021AE4`, `0x08021B50`, `0x08021C6A`, `0x08021F78`, `0x0802207C`, `0x08022368` e `0x080223B0` (índices 0–6). O caminho observado em `0x08021B50` percorre índices 0–5 com stride de 100 bytes, chama `0x0803FBE8` em mais de um offset e usa a tabela `0x0825E45C`; a finalidade completa dessas leituras não é nomeada localmente aqui.

### Saída terminal observada

No destino `0x080223B0`, o handler testa a word `0x02023BC8`. Se não-zero, retorna sem avançar o cursor. Se zero, usa o byte de `0x02023D6D` para selecionar `0x02023BE4 + índice×0x58`, zera o halfword em `+0x2E` e o byte em `+0x20`, e avança a word de cursor `0x02023D74` em 2 antes de retornar.

As escritas e o dispatch acima são evidência local. Não atribuo nomes aos sete estados nem descrevo como completo o processamento de experiência; ainda faltam os destinos intermediários e seus callers/dados concretos.

## Cruzamento semântico upstream — separado da prova local

Na tabela upstream `gBattleScriptingCommandsTable`, os índices `0x21`, `0x22` e `0x23` são `Cmd_jumpifstatus3condition`, `Cmd_jumpiftype` e `Cmd_getexp`. A fonte interpreta `0x21` como teste de status3 com condição de inversão, `0x22` como teste dos tipos do battler e `0x23` como distribuição de experiência em uma máquina de estados. A fonte descreve sete estados, além de party, controladores e mensagens. Essas denominações explicam o código, mas não são símbolos recuperados da ROM local; em particular, este relatório não valida todos os estados de `0x23` contra a ROM.

Fonte cruzada: `src/battle_script_commands.c`, SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_condition_exp_commands.py
python scripts/inspect_battle_condition_exp_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador confirma hash, dispatch, padrões e destinos da tabela local de estados; não executa batalha nem valida toda a máquina de experiência. Pendem a análise dos estados intermediários de `0x23`, os efeitos dinâmicos, callers e amostras concretas dos operands de `0x21`/`0x22`. O recorte é parcial e não representa cobertura global.
