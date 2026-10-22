# Ciclo 27 — animação de ataque e atualização local de HP

**Estado:** foram seguidos estaticamente os opcodes `0x09`–`0x0C` da tabela local até os handlers `0x0801F441`, `0x0801F589`, `0x0801F5A9` e `0x0801F685`. Os handlers de animação/healthbar mostram espera por flags de execução e avanços distintos do cursor; o handler de dados HP altera estruturas locais, com caminho separado para substitute e casos de cura/dano. A rotina de `0x0C` é extensa e este relatório não a considera exaustivamente reconstruída.

## Identidade, ferramentas e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Desmontagem Thumb local com Capstone 5.0.7 temporário em `/tmp/capstone-py`; `scripts/inspect_battle_anim_hp_updates.py` valida dispatch, bytes e literais selecionados.
- A árvore upstream `pret/pokefirered` está fixada em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; rótulos semânticos abaixo são cruzamentos, não prova local.
- REA e Ghidra não foram usados; não houve teste dinâmico/emulador nem alteração da ROM.

## Bytecode e dispatch local

No script de efeito 0, o trecho em `0x081D6931` começa `05 06 07 09 0A`; nesse recorte estão presentes os opcodes `0x09` e `0x0A`. A tabela de handlers em `0x0825011C` contém:

| Opcode | Ponteiro Thumb local | Instruções em |
|---|---:|---:|
| `0x09` | `0x0801F441` | `0x0801F440` |
| `0x0A` | `0x0801F589` | `0x0801F588` |
| `0x0B` | `0x0801F5A9` | `0x0801F5A8` |
| `0x0C` | `0x0801F685` | `0x0801F684` |

Os opcodes `0x0B`/`0x0C` foram rastreados a partir da tabela local; não aparecem no trecho de bytecode citado acima.

## Evidência local — opcode `0x09`

O handler lê uma word em `0x02023BC8`; se não for zero, retorna sem avançar o cursor `0x02023D74`. Caso contrário, testa bit `0x80` em `0x02023DD0`. Se ativo, compara o halfword em `0x02023D4A` com `0x90` e `0xA4`; nos outros valores, chama `0x08017520` usando `cursor + 1`, carrega `0x081D89F1` no cursor e incrementa bytes em `0x02023FC4 + 0x18` e `+0x19`.

No outro caminho, calcula `moveId × 12 + 0x08250C04` e testa bits `0x08`, `0x20` e `0x01` do byte `+6`. Se algum desses bits estiver ativo e o byte `0x02023FC4 + 0x19` for não-zero, incrementa o cursor em 1 e retorna. Em seguida, testa `0x02023DCC & 0x29`; se não zero, avança temporariamente para `cursor + 1`, chama `0x08017520` e grava `0x081D89F1` no cursor.

No caminho que não tomou esses desvios, grava o byte de `0x02023D6B` em `0x02023BC4`, carrega o halfword do move, um byte em `0x02024020 + 0x18`, a word em `0x02023D50`, a byte `+0x2B` do registro calculado em `0x02023BE4 + index × 0x58` e um endereço calculado a partir de `0x02023E0C`. Chama `0x0800E1FC`, incrementa os bytes de `0x02024020 + 0x18` e `+0x19`, chama `0x08017248` e incrementa o cursor em 1. A identidade dos campos/calls não é inferida só dos nomes de registradores ou de endereços.

## Evidência local — opcode `0x0A`

O handler lê a word em `0x02023BC8`. Se não-zero, retorna sem alterar o cursor. Se zero, incrementa `0x02023D74` em 1 e retorna. Não há leitura de operand inline nesse recorte local.

## Evidência local — opcode `0x0B`

Se `0x02023BC8` estiver ocupado, o handler retorna sem avançar. Se `0x02023DCC & 0x29` não for zero, pula o processamento e incrementa o cursor em 2. Caso contrário, lê o byte do comando em `cursor + 1`, chama `0x08016E24` e grava o byte retornado em `0x02023BC4`.

Com o battler selecionado, testa a word do registro em `0x02023BE4 + index × 0x58 + 0x50` com máscara `0x01000000`; consulta também um byte em `0x02023E0C + index × 0x1C + 0x0A` e o bit `0x100` da word em `0x02023DD0`. No ramo em que essas condições são satisfeitas, chama `0x080173AC` com imediato `0x80` e o índice. Nos demais ramos, lê dano em `0x02023D50`, compara com `0x2710` (10.000), limita o valor usado se for maior, e chama `0x0800E5EC`. Depois chama `0x08017248` e `0x080751C4`; um teste subsequente lê uma word em `0x03004F90` e pode definir bit 0 no byte `0x02023D74 + 5`. O cursor é incrementado em 2.

A ROM mostra limites, chamadas, flags e operandos; identificar a primeira rota como mensagem de dano ao substitute e a segunda como atualização da barra de HP é cruzamento upstream.

## Evidência local — opcode `0x0C`

O handler retorna sem avançar se `0x02023BC8` estiver ocupado. Seleciona um byte de tipo: lê `0x02023FE8 + 0x13`; se zero, ou se o bit `0x40` estiver ativo, usa o byte `+2` do registro `moveId × 12 + 0x08250C04`; senão usa o valor dinâmico mascarado com `0x3F`. Se `0x02023DCC & 0x29` não for zero, o fluxo pula a atualização principal e termina pelo bloco alternativo descrito abaixo.

No caminho principal, o byte do comando em `cursor + 1` passa por `0x08016E24` e o retorno é escrito em `0x02023BC4`. O código consulta o status no registro `0x02023BE4 + battler × 0x58 + 0x50`, o marcador em `0x02023DD0`, e a estrutura indexada em `0x02023E0C + battler × 0x1C`, incluindo o byte `+0x0A`.

- Quando a rota de substitute é selecionada, compara o valor `+0x0A` com o dano em `0x02023D50`. Atualiza campos em `0x02023ECC + battler × 0x14 + 4`, subtrai o dano do byte/valor de substitute ou usa o valor restante, e grava o resultado local em `0x02023D54`. Se o valor de substitute chegar a zero, o handler incrementa o cursor em 2, chama `0x08017544`, carrega `0x081D9526` em `0x02023D74` e retorna.
- Na rota de HP normal, se o valor de dano em `0x02023D50` for negativo, soma-o ao halfword HP em `battle-record + 0x28` e limita ao halfword `+0x2C`. Para dano não-negativo, o código testa e possivelmente limpa máscara de hit-marker, atualiza registros indexados por battler, compara HP atual ao dano, subtrai-o ou grava zero, e atualiza valor de HP efetivamente alterado. Há ramos por tipo selecionado e por move ID `0x00DC`; alguns gravam dados físicos/especiais e IDs de battler em arrays/estruturas locais. Esses subramos não foram totalmente enumerados.
- No caminho de resultado sem efeito, a rotina resolve o battler a partir do comando; se o word em `0x02023ECC + battler × 0x14 + 4` estiver zero, grava `0x0000FFFF`. Esse caminho também avança o cursor em 2.

As rotas, constantes cruas, offsets e gravações acima são observações da ROM; não constituem reconstrução completa do layout dos arrays nem de todos os estados possíveis. Em vários pontos há chamada a controlador/helper local cuja implementação não foi seguida neste ciclo.

## Cruzamento semântico upstream — separado da evidência local

No `gBattleScriptingCommandsTable` da fonte fixada, os índices `0x09`–`0x0C` são, respectivamente, `Cmd_attackanimation`, `Cmd_waitanimation`, `Cmd_healthbarupdate` e `Cmd_datahpupdate`. O fonte associa os ramos do handler `0x09` a flag de não animação, exceções para Transform/Substitute, alvo do move e pausa; `0x0A` espera o controller; `0x0B` envia atualização de barra/diálogo para substitute; e `0x0C` altera HP, substitute, dano registrado e dados enviados ao controller. Esses nomes são úteis para orientar leitura, mas as afirmações locais deste relatório permanecem ancoradas nos bytes/desvios/endereço acima.

Arquivos upstream usados (SHA-256):

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`;
- `include/battle.h`: `8942e59c543eda3776f1816e9b40229b5d30e02842e587e3851a1d708ece1292b`;
- `include/constants/battle.h`: `b9d0493af4629d450050637e9aace63b684b282f841bed2a0d97b1d71e9d55e3`.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_anim_hp_updates.py
python scripts/inspect_battle_anim_hp_updates.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador auxilia na reprodução de hash, dispatch e trechos/literais. Ele não substitui a leitura da desmontagem, não valida os ramos em runtime e não confirma todos os campos/tabelas. Falta percorrer completamente a rotina `0x0C`, testar comportamento em batalha e seguir comandos posteriores (`0x0D` em diante) e seus consumidores. O ciclo é acompanhado no Linear pela issue `VYK-6`; nenhuma cobertura global é afirmada.
