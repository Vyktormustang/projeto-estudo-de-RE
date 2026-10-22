# Ciclo 24 — `damagecalc` local e chamada do cálculo de dano-base

**Estado:** seguido o opcode `0x05` do script comum de efeito 0 ao handler Thumb local `0x0801E59D`, à chamada `0x0803ECEC` e aos ajustes posteriores de dano observáveis no chamador. O helper de dano-base tem muitos ramos; o ciclo caracteriza sua entrada e algumas leituras iniciais, não decodifica a fórmula inteira nem todos os efeitos condicionais.

## Identidade e método

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Desmontagem local Thumb com Capstone 5.0.7 temporário em `/tmp/capstone-py`; o script `scripts/inspect_damagecalc_path.py` verifica os bytes e literais centrais sem dependências Python externas.
- Cruzamento semântico separado: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`.
- REA/Ghidra não foram usados; não houve emulação, alteração de ROM ou save.

## Do bytecode ao handler

No script apontado pelo índice 0 da tabela em `0x081D65A8`, o endereço `0x081D6931` contém opcode `0x05`. A tabela local de comandos em `0x0825011C` aponta para `0x0801E59D`; o endereço de entrada Thumb par é `0x0801E59C`. O comando seguinte é opcode `0x06`, cuja entrada local na mesma tabela é `0x0801E849`.

O handler `0x0801E59D` prepara argumentos em registradores e na stack e chama `0x0803ECEC`. Os bytes locais mostram:

- carrega os bytes battler-index dos endereços RAM `0x02023D6B` e `0x02023D6C`;
- para cada índice, calcula `índice × 0x58` e soma `0x02023BE4`, formando os dois endereços passados em `r0`/`r1`;
- carrega um halfword de `0x02023D4A` em `r2`;
- carrega um halfword de `0x02023F50` para o primeiro argumento adicional na stack;
- lê um byte em `[0x02023FE8] + 0x13` para outro argumento da stack;
- passa também os dois battler-index como argumentos adicionais;
- seleciona um halfword lateral a partir de `0x02023DDE`, usando o índice `0x02023D6C` e o helper `0x080751D8`, e entrega esse valor em `r3`;
- chama `0x0803ECEC` em `0x0801E5E0`.

A cadeia local mostra, portanto, dois registros de estado de tamanho/stride calculado `0x58`, um ID, um halfword de estado lateral e outros overrides sendo passados à rotina chamada. Os endereços e cálculos são evidência local; nomes de campos e argumentos são interpretação separada.

## Leituras iniciais no helper `0x0803ECEC`

O helper salva os argumentos e, em seus primeiros blocos, faz operações compatíveis com selecionar valores override ou obtê-los do catálogo:

- o valor adicional de power é testado; quando zero, o código calcula `moveID × 12 + 0x08250C04`, lê byte `+1` e o armazena como halfword num estado RAM;
- o argumento de tipo também é testado; no caminho zero, calcula o mesmo registro e lê byte `+2`; no caminho não zero, mascara o valor recebido com `0x3F`;
- dos dois endereços de estado recebidos em `r0`/`r1`, aparecem loads de halfwords em offsets locais `+2`, `+4`, `+8` e `+0x0A`.

As leituras posteriores incluem uma sequência extensa de ramos, acessos a itens/abilities e aritmética. Não foram reconstruídos todos os ramos nem a fórmula completa do helper; não se deve extrapolar desta amostra para todos os moves/condições.

## Ajustes e gravação no handler chamador

Depois do retorno do helper, o handler usa o resultado local em `r0` e:

1. multiplica-o pelo byte em `0x02023D71`;
2. multiplica o produto pelo byte em `0x02023FC4 + 0x0E` (endereço final `0x02023FD2`);
3. grava o resultado em `[0x02023D50]`.

Há dois ajustes condicionais adicionais no trecho local examinado:

- lê um word em `0x02023DFC + battlerIndex × 4`, testa máscara `0x200`; se passar, consulta o byte `+2` do registro do move e, quando ele vale `0x0D`, duplica o valor em `[0x02023D50]`;
- lê um byte em `0x02023E8C + attackerIndex × 0x10`, testa seu bit 7; se passar, multiplica o valor em `[0x02023D50]` por 15 e chama `0x081E4018` com divisor 10, armazenando o resultado.

Ao final, o handler carrega o cursor RAM em `0x02023D74`, adiciona 1 ao ponteiro e o grava de volta. No script amostrado, isso o leva de `0x081D6931` ao próximo opcode em `0x081D6932` (`0x06`).

## Cruzamento semântico upstream — não é prova local

No upstream fixado, o handler é denominado `Cmd_damagecalc`; ele chama `CalculateBaseDamage` com `gBattleMons`, move, side status e overrides, multiplica o retorno por `gCritMultiplier` e `gBattleScripting.dmgMultiplier`, verifica `STATUS3_CHARGED_UP` com tipo elétrico e aplica um fator por Helping Hand. A função `CalculateBaseDamage` lê power/type do move quando os overrides são zero e usa campos de stats da estrutura `BattlePokemon`.

Os padrões de instruções locais — chamada com dois ponteiros de stride `0x58`, ID/overrides na stack, leituras locais de `+1/+2`, multiplicações e condições acima — são compatíveis com esse desenho. Nomes `Cmd_damagecalc`, `CalculateBaseDamage`, `gCritMultiplier`, `Helping Hand`, `Charged Up`, `attack`, `defense` e demais campos permanecem nomes do cruzamento; os endereços, operands, loads, masks, chamadas e stores listados acima foram observados na ROM local.

Fontes upstream consultadas e hashes:

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`;
- `src/pokemon.c`: `116a470cd9ebfa226aa8d85c2eb63591e176d726837c67baaa1ac6260d50f2ec`;
- `include/pokemon.h`: `a6881fee07ae10f57ebf3ec7af1cabd2e900d8ba8d3da644313c087d16e1617e`;
- `include/battle.h`: `8942e59c543eda3776f1815c12a55f09d8c23d62a30994177c490a12af2be1f7`.

## Reprodução e lacunas

```bash
python scripts/inspect_damagecalc_path.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O script valida o hash, dispatch local dos opcodes 5/6, bytes do handler, literais, parte da chamada e loads do helper. Isso não equivale a teste dinâmico nem a cobertura de todos os ramos.

Próximo passo: analisar o handler local `0x0801E849` (opcode `0x06`) e mapear como ele modifica `[0x02023D50]`/flags de resultado; depois seguir `adjustnormaldamage`, animação e atualização de HP. Continuam desconhecidos outros caminhos de dano, callers e a fórmula integral do helper.
