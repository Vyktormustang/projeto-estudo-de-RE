# Ciclo 26 — opcode `0x07`: ajuste aleatório, itens e limite de HP

**Estado:** o opcode local `0x07` foi seguido da tabela de comandos até o handler Thumb `0x0801F105` (código em `0x0801F104–0x0801F2A0`). A ROM mostra o fator pseudoaleatório aplicado ao dano, consultas locais de item/estado e um ramo que limita dano a HP−1. A leitura é estática e parcial: endereços, comparações e gravações são evidência local; nomes e papéis de estruturas são cruzamentos com a fonte upstream fixada.

## Identidade, ferramentas e proveniência

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Desmontagem Thumb local com Capstone 5.0.7 temporário em `/tmp/capstone-py`; validação auxiliar por `scripts/inspect_adjustnormaldamage.py`.
- Cruzamento com `pret/pokefirered` fixado no commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, sem substituir inspeção local.
- REA e Ghidra não foram usados; não houve execução de batalha/emulador nem alteração da ROM.

## Bytecode e dispatch local

A tabela de scripts local tem índice 0 em `0x081D65A8`, apontando para `0x081D6900`. No segmento amostrado, os bytes a partir de `0x081D6931` são `05 06 07 09 0A`; portanto o opcode `0x07` está em `0x081D6933`. A tabela local de comandos em `0x0825011C` contém no índice `0x07` o ponteiro Thumb `0x0801F105`, para instruções a partir de `0x0801F104`.

A ROM também aponta `0x09→0x0801F441`, `0x0A→0x0801F589`, `0x0B→0x0801F5A9` e `0x0C→0x0801F685`. Esses handlers não foram analisados neste ciclo.

## Evidência local: ajuste do dano

O handler chama `0x08044EC8`, mantém os quatro bits baixos do retorno (`& 0x0F`) e calcula `100 − valor`. Se a word de dano em `0x02023D50` não for zero, multiplica o dano por esse fator, divide por 100 através de `0x081E4018` e grava o quociente. Se o dano anterior era não-zero e o quociente ficou zero, grava 1. Se a word de dano já era zero, salta a multiplicação e preserva zero.

Isso descreve diretamente as instruções locais: resultado truncado em escala percentual entre os fatores gerados por `100 − (retorno & 15)`, divisão inteira local e piso de 1 apenas para dano inicialmente não-zero. O rótulo “multiplicador aleatório 85%–100%” vem do cruzamento de fonte abaixo.

## Evidência local: item e estado do defensor

O índice do defensor é lido em `0x02023D6C`. O handler forma `0x02023BE4 + index × 0x58` e lê o halfword no offset `+0x2E`, comparando-o com `0x00AF`.

- Se igual a `0xAF`, calcula `0x02023F54 + index × 0x1C` e lê bytes nos offsets `+7` e `+0x1A`.
- Caso contrário, passa o halfword a `0x0809A924` e `0x0809A948` em chamadas distintas, usando os retornos como bytes subsequentes do fluxo local.
- Grava o índice do defensor no byte `0x02023D6F`.
- Quando o byte de efeito obtido vale `0x27`, o handler chama `0x08044EC8`, divide o retorno por 100 via `0x081E4684` e compara o resultado ao parâmetro de efeito. Se o teste passa, chama `0x080C7208` com índice e efeito; depois define bit `0x80` no byte `0x02023ECC + index × 0x14`.

As chamadas auxiliares e o significado dos registros não são identificados somente pelo endereço. Os valores imediatos e a aritmética de stride acima são observados na ROM.

## Evidência local: evitar dano letal e atualizar resultado

Antes de testar efeitos do movimento, o handler lê a word em `0x02023BE4 + target × 0x58 + 0x50`, aplica a máscara `0x01000000` e, se o bit estiver ativo, salta para o incremento do cursor. Se não estiver ativo, calcula o registro de movimento como `moveId × 12 + 0x08250C04`, lê o byte `+0` e compara com `0x65`.

O código prossegue ao teste de HP quando o byte é `0x65`, ou quando pelo menos um dos dois bits locais seguintes está ativo:

- bit `0x02` do primeiro byte em `0x02023E8C + target × 0x10`;
- bit `0x80` do primeiro byte em `0x02023ECC + target × 0x14`.

Então lê o halfword HP em `battle-record + 0x28` e compara com o dano em `0x02023D50`. Se HP for maior que o dano, não altera o dano nesse bloco. Caso contrário, grava `HP − 1` no dano. Depois:

- se o bit `0x02` de `0x02023E8C + target × 0x10` estiver ativo, faz OR de `0x40` no byte `0x02023DCC`;
- se não estiver, mas o bit `0x80` de `0x02023ECC + target × 0x14` estiver ativo, faz OR de `0x80` em `0x02023DCC` e grava o halfword de item lido do registro do defensor (`+0x2E`) em `0x02023D68`.

No caminho comum, incrementa a word de cursor `0x02023D74` e retorna. Os testes mostram ramos e estado gravado; não demonstram isoladamente todos os efeitos posteriores das flags ou dos helpers.

## Cruzamento upstream — nomes e semântica propostos

Na árvore fixada, o índice `0x07` de `gBattleScriptingCommandsTable` é `Cmd_adjustnormaldamage`. Seu corpo chama a rotina inline `ApplyRandomDmgMultiplier`, busca efeito e parâmetro de efeito do item do defensor, trata Enigma Berry, consulta Focus Band e aplica a condição de False Swipe/Endure/Focus Band para limitar dano letal. A sequência e os imediatos locais conferem com essa fonte.

O mesmo upstream nomeia os valores: `0xAF` como `ITEM_ENIGMA_BERRY` (175), `0x27` como `HOLD_EFFECT_FOCUS_BAND` (39), `0x65` como `EFFECT_FALSE_SWIPE` (101), bit `0x01000000` como `STATUS2_SUBSTITUTE`, bit `0x02` como o bit `endured` do registro `gProtectStructs`, e bit `0x80` no primeiro byte de `gSpecialStatuses` como `focusBanded`. Os bits `0x40` e `0x80` em `0x02023DCC` correspondem, no cruzamento, aos resultados `MOVE_RESULT_FOE_ENDURED` e `MOVE_RESULT_FOE_HUNG_ON`. Os endereços, operações, strides e valores crus foram confirmados localmente; os identificadores simbólicos continuam sendo nomes do upstream.

Arquivos upstream consultados (SHA-256):

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`;
- `include/battle.h`: `8942e59c543eda3776f1816e9b40229b5d30e02842e587e3851a1d708ece1292b`;
- `include/constants/battle.h`: `b9d0493af4629d450050637e9aace63b684b282f841bed2a0d97b1d71e9d55e3`;
- `include/constants/battle_move_effects.h`: `fa15e285903818cc3cc7ecb2ca32c11d8317b14d261ca2d1caf44e614b53828a`;
- `include/constants/hold_effects.h`: `e763fdbbef19ba6999a7151094cf26734323414237ebb1afcf2f453f65c2f661`;
- `include/constants/items.h`: `af17276346eaecc5a10ac60f14b22c33332ec8c6fb0ec82895bdc3649b678138`.

## Reexecução, Linear e lacunas

```bash
python -m py_compile scripts/inspect_adjustnormaldamage.py
python scripts/inspect_adjustnormaldamage.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador confere hash, ponteiros, sequência de bytecode, trechos de instruções e literais locais; não é execução dinâmica. O ciclo está registrado no projeto Linear **Pokémon FireRed BR — compreensão abrangente da ROM**, issue **VYK-5** (`Ciclo 26 — rastrear o handler local do opcode 0x07`).

Pendente: analisar os handlers de animação `0x09`/`0x0A` e de atualização de HP `0x0B`/`0x0C`, seguir outros consumidores das flags de dano e ampliar o inventário para além destes recortes. Não se afirma cobertura global.
