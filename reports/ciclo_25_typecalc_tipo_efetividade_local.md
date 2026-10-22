# Ciclo 25 — `typecalc`: tipo, STAB e tabela local de efetividade

**Estado:** rastreado estaticamente o opcode `0x06` do bytecode já amostrado, seu handler local, a seleção do tipo do movimento, o ajuste do dano por STAB, a consulta à tabela terminada localmente em `0x0824F050` e um helper de modulação. A ROM fornece os bytes e operações descritos; nomes como `Cmd_typecalc`, `Levitate` e `Wonder Guard` são identificações cruzadas com a fonte upstream fixada, não símbolos recuperados da ROM. Não houve execução em batalha nem cobertura integral dos ramos da rotina.

## Identidade, ferramentas e proveniência

- ROM lida sem alterações: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset do arquivo + `0x08000000`.
- Desmontagem local Thumb com Capstone 5.0.7 temporário em `/tmp/capstone-py`; conferência estática com `scripts/inspect_typecalc_path.py`.
- A árvore `pret/pokefirered`, temporária em `/tmp/pokefirered-pinned/`, está fixada no commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; usada somente para cruzamento de rótulos/semântica. Nenhum nome do upstream é tratado como prova isolada do conteúdo da ROM.
- REA e Ghidra não foram usados; esta etapa não foi validada em emulador. Capstone serve aqui para desmontar instruções Thumb, não substitui REA/Ghidra.

## Bytecode e dispatch observados na ROM

O índice 0 da tabela de scripts local (`0x081D65A8`) aponta para `0x081D6900`. No fluxo linear amostrado, o opcode de cálculo de dano `0x05` começa em `0x081D6931`; o byte seguinte, em `0x081D6932`, é `0x06`. A tabela local de comandos em `0x0825011C` contém no índice `0x06` o ponteiro Thumb `0x0801E849`; o código começa no endereço alinhado `0x0801E848`.

A ROM contém, a partir de `0x081D6932`, a sequência de bytes `06 07 09 0A`. A tabela local associa também `0x07` a `0x0801F105`, `0x09` a `0x0801F441` e `0x0A` a `0x0801F589`. Este relatório não desmonta esses handlers; a identificação nominal a seguir vem apenas do cruzamento upstream.

## Evidência local: seleção de tipo e STAB

No início do handler local (`0x0801E848`):

1. O halfword corrente em `0x02023D4A` é comparado com `0x00A5`. Se igual, o caminho salta para o bloco que incrementa o cursor local `0x02023D74` e retorna, sem executar o lookup de tipo mostrado abaixo.
2. Caso contrário, lê-se um byte em `0x02023FE8 + 0x13`. Se diferente de zero, o valor é mascarado com `0x3F` e usado como tipo. Se for zero, o código calcula `moveId × 12 + 0x08250C04` e lê o byte no offset `+2` do registro candidato de movimento.
3. O handler calcula o endereço do registro do atacante a partir de `0x02023BE4 + battlerIndex × 0x58`. Compara o tipo selecionado com os bytes do registro nos offsets `+0x21` e `+0x22`. Se qualquer um coincide, lê o dano em `0x02023D50`, multiplica por 15, chama `0x081E4018` com divisor 10 e grava o retorno em `0x02023D50`. A ROM confirma esse ramo e essa aritmética; a expansão do acrônimo STAB é cruzamento semântico.

## Evidência local: tabela e helper de efetividade

A rotina percorre registros de três bytes a partir de `0x0824F050`, avançando o índice em 3. Para cada registro não especial, compara o byte `+0` com o tipo selecionado; se igual, compara o byte `+1` com os bytes de tipo `+0x21` e `+0x22` do registro calculado para o defensor. O segundo tipo só é processado quando difere do primeiro. Em cada correspondência, passa o byte `+2` ao helper local de endereço Thumb `0x0801E771` (instruções em `0x0801E770`).

O conteúdo local observado ocupa 112 registros, intervalo candidato `[0x0824F050, 0x0824F1A0)`. O registro de índice 108 é `FE FE 00`; o índice 111 é `FF FF 00`. O código testa o primeiro byte contra `0xFF` para encerrar e trata `0xFE` por um ramo separado que consulta estado do registro do defensor. Os bytes dos registros são observação direta; chamá-los de tabela de efetividade e nomear o marcador `FORESIGHT` são cruzamentos upstream.

O helper local `0x0801E770` lê o byte multiplicador recebido, multiplica por ele o valor de `0x02023D50`, divide o produto por 10 através da chamada `0x081E4018` e grava o quociente. Se o quociente resultar zero e o multiplicador for diferente de zero, grava 1. Em seguida, compara o multiplicador com `0`, `5` e `20` e atualiza bits do byte em `0x02023DCC`; os outros valores seguem sem essas três atualizações condicionais. Na ramificação de multiplicador zero, a sequência local faz OR com `0x08` e AND com `0xFB` e `0xFD` antes de gravar, o que define o bit 3 e limpa os bits 2 e 1. Os nomes dos bits e os rótulos dos multiplicadores não são deduzidos apenas desses imediatos.

## Ramos locais associados a habilidades

- No ramo anterior à tabela, o código calcula o registro do defensor (`0x02023BE4 + index × 0x58`), lê o byte `+0x20`, compara com `0x1A` e também exige tipo selecionado `4`. Se ambas as condições passam, altera o byte de resultado em `0x02023DCC`, zera halfwords indexados por battler em `0x02023DA0` e `0x02023DA8`, grava um valor de mensagem em `0x02023E82 + 6` e chama `0x080C71D0`. O caminho normal da tabela é então contornado.
- Após o scan da tabela, há outro teste do byte `+0x20` do registro do defensor contra `0x19`. A rotina chama `0x0802A224`, verifica o retorno e consulta o byte de poder no registro do movimento em `0x08250C04 + moveId × 12 + 1`; em condições adicionais, altera o byte de resultado, os mesmos históricos indexados e a mensagem, e chama `0x080C71D0`.
- O código também testa o bit `0x08` em `0x02023DCC`; quando definido, grava `1` em um byte associado ao registro do atacante. O handler termina incrementando `0x02023D74` e retornando.

São fatos locais os offsets, comparações, branches, chamadas e gravações acima. A descrição completa das condições aninhadas de `0x0802A224`, a interpretação dos bytes de mensagem e todas as consequências dos bits permanecem fora do recorte. Não se generaliza comportamento não percorrido.

## Cruzamento upstream — nomenclatura, não evidência local

Na árvore fixada, o índice `0x06` da tabela `gBattleScriptingCommandsTable` é `Cmd_typecalc`, e o índice `0x07` é `Cmd_adjustnormaldamage`; os índices `0x09` e `0x0A` são `Cmd_attackanimation` e `Cmd_waitanimation`. A correspondência de opcode e função é compatível com a tabela de ponteiros observada localmente.

A fonte upstream identifica o registro de 12 bytes como `BattleMove`; `+2` é o tipo e `+1` é o poder. `GET_MOVE_TYPE` usa `dynamicMoveType & DYNAMIC_TYPE_MASK` quando o byte dinâmico não é zero, senão usa o tipo do registro de movimento. `Cmd_typecalc` compara o move corrente com `MOVE_STRUGGLE` (165), aplica o fator 15/10 quando o atacante tem o tipo, consulta a tabela `gTypeEffectiveness` em grupos de 3 bytes, e trata `ABILITY_LEVITATE` (26) com `TYPE_GROUND` (4) e `ABILITY_WONDER_GUARD` (25). Esses identificadores explicam os padrões locais 0xA5, 0x1A, 0x19 e 4; são rótulos cruzados, não nomes encontrados na ROM.

A declaração upstream dá tamanho 336 bytes a `gTypeEffectiveness`; isso coincide com o trecho local delimitado pelo stride, sentinela e terminador acima (`112 × 3`). A tabela local foi inspecionada diretamente. A coincidência de tamanho e os padrões de código sustentam a correspondência, mas o array da fonte não é substituto da leitura dos bytes da ROM.

Arquivos upstream consultados (SHA-256):

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`;
- `include/battle_main.h`: `22ee8ad8174831ae7cb0c8c1ac2946011a88e2aedb5c621901f67a37a444630c`;
- `include/battle.h`: `8942e59c543eda3776f1816e9b40229b5d30e02842e587e3851a1d708ece1292b`;
- `include/constants/abilities.h`: `1c1b93de5d5ff65d8b3066e9b40229b5d30e02842e587e3851a1d708ece1292b`;
- `include/constants/moves.h`: `79d5b93423006c25e6ee47355b15f403b2534616fd6b638e1755e5886d378194`;
- `include/constants/battle.h`: `b9d0493af4629d450050637e9aace63b684b282f841bed2a0d97b1d71e9d55e3`.

## Reprodução, validação e lacunas

```bash
python scripts/inspect_typecalc_path.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador checa o hash da ROM, ponteiros locais do dispatch, sequência de bytecode, padrões de instrução, literais e os 112 registros/sentinelas. É uma validação estática auxiliar, não execução nem prova de todos os caminhos. Ficam pendentes a leitura dos detalhes completos de `0x0802A224`, a inspeção do handler `0x07` já apontado para `0x0801F105` e o seguimento dos comandos de animação/atualização de HP. A cobertura do sistema de batalha e da ROM continua parcial.
