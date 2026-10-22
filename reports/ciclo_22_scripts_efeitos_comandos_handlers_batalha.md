# Ciclo 22 — Scripts de efeitos, despacho de comandos e handlers locais

**Estado:** dois destinos da tabela de efeitos foram seguidos como bytecode local, e o despacho de bytecodes para handlers Thumb foi localizado e conferido com exemplos. A leitura é estática: não houve execução de batalha nem validação de resultado em emulador. Os nomes dos scripts/comandos citados abaixo são cruzamentos semânticos upstream; endereços, bytes, operands, ponteiros e operações descritas como locais vêm da ROM BR.

## Identidade e método

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Bytes locais e desmontagem Thumb via Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Script reprodutível sem dependências externas: `scripts/inspect_battle_effect_scripts.py`.
- Cruzamento separado com `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; não prova proveniência ou equivalência integral da ROM.
- REA e Ghidra não foram usados; não houve escrita na ROM/save.

## Despacho local de comandos de script

A rotina local em `0x08015A0C` lê o endereço apontado por `0x02023D74`, carrega o byte no início desse buffer, multiplica o opcode por quatro, soma a base literal `0x0825011C` e carrega a word escolhida. O resultado é passado ao trampoline local em `0x081E3BA8`, cujo código é `BX r0` (`00 47`). Assim, a ROM contém um caminho observável **opcode do bytecode → ponteiro de handler → transferência indireta de controle**. A tabela local candidata ocupa `[0x0825011C, 0x082504FC)`: 248 words apontam para dentro da ROM; a word seguinte, `0x00006421`, não é endereço da ROM. O limite é uma inferência estrutural pela sequência de ponteiros, não um símbolo/limite exportado.

Pares confirmados diretamente por words na tabela local:

| Opcode | Handler Thumb armazenado |
|---:|---:|
| `0x00` | `0x0801D761` |
| `0x01` | `0x0801DDC5` |
| `0x21` | `0x08021989` |
| `0x28` | `0x08022651` |
| `0x2A` | `0x08022711` |
| `0x2E` | `0x08022979` |
| `0x35` | `0x08022B1D` |

Foi conferido no disassembly que três handlers realizam as operações compatíveis com os operands dos scripts amostrados:

- O handler selecionado por `0x28`, em `0x08022650`, lê os quatro bytes após o opcode e grava o endereço resultante no word apontado por `0x02023D74`. É o caminho local de alteração do cursor para um endereço absoluto.
- O handler de `0x2E`, em `0x08022978`, carrega um endereço de quatro bytes e um byte imediato, grava esse byte no endereço indicado e avança o cursor em seis bytes.
- O handler de `0x2A`, em `0x08022710`, lê condição, endereço de halfword, valor u16 e destino; avança doze bytes e entra numa comparação/ramificação local. O trecho inclui uma dispatch interna das variantes de comparação.
- O handler de `0x35`, em `0x08022B1C`, lê endereço u32 e máscara u32, aplica OR ao word daquele endereço e avança nove bytes.

Isso estabelece handler local para os comandos amostrados. Não foram percorridos os 248 handlers, nem todos os comandos referenciados pelos scripts.

## Exemplo local: efeito ID 0

A word `effectId 0` em `0x081D65A8` contém `0x081D6900`. A ROM nessa entrada começa:

```text
VA          Bytes                                      Observação local
081D6900    2A 01 4A 3D 02 02 39 00 26 69 1D 08       opcode 2A; compara halfword em 02023D4A com 0039;
                                                        destino 081D6926
081D690C    21 00 00 00 04 00 01 26 69 1D 08          opcode 21; sequência de operandos e destino 081D6926
081D6917    35 D0 3D 02 02 00 00 04 00                opcode 35; endereço 02023DD0, máscara 00000400
081D6920    2E D2 3F 02 02 02                         opcode 2E; endereço 02023FD2, byte 02
081D6926    00 01 ...                                 entrada comum: opcodes 00 e 01
```

Os primeiros dois comandos carregam o mesmo destino `0x081D6926`; se o fluxo não tomar esses desvios, seguem `0x35` e `0x2E`. Os bytes e a aritmética local são observáveis, independentemente dos rótulos upstream. O endereço `0x02023D4A` coincide com o literal usado no despacho de move do ciclo 21, mas aqui é apenas o endereço operandado pelo comando.

## Exemplo local: efeito ID 125

A word de índice 125 na tabela `0x081D65A8` contém `0x081D7977`. O início local é:

```text
VA          Bytes                                      Observação local
081D7977    2E 85 3E 02 02 03                         escreve byte 03 em 02023E85
081D797D    28 00 69 1D 08                            o comando seguinte muda cursor para 081D6900
```

O handler de `0x2E` recebe o endereço `0x02023E85` e byte `0x03`; o handler de `0x28` recebe o destino `0x081D6900`, que é a entrada observada para efeito ID 0. Portanto, a ligação local é efeito 125 → script `0x081D7977` → escrita de byte → script `0x081D6900`, sem depender de nome de move ou nome de efeito.

## Cruzamento semântico upstream — não é evidência local

No commit upstream fixado, a tabela `gBattleScriptsForMoveEffects` em `data/battle_scripts_1.s` associa o índice 0 a `BattleScript_EffectHit` e o índice 125 (constante `EFFECT_THAW_HIT`) ao `BattleScript_EffectThawHit`. Esse script de índice 125 usa `setmoveeffect MOVE_EFFECT_BURN` e segue com `goto BattleScript_EffectHit`. A fonte upstream define `MOVE_EFFECT_BURN` como 3; o macro `setmoveeffect` escreve no seletor de efeito secundário. Os bytes locais de índice 125 são compatíveis com esse fluxo, mas, localmente, só ficam provados o destino, o byte gravado e os opcodes/operands.

As macros upstream em `asm/macros/battle_script.inc` atribuem `0x2A` a `jumpifhalfword`, `0x21` ao teste de status pertinente, `0x35` a `orword`, `0x2E` a `setbyte` e `0x28` a `goto`. Os opcodes locais correspondem aos handlers observados acima; nomes e semântica de alto nível permanecem cruzamento, não rótulos locais confirmados.

## Verificação e limites

```bash
python scripts/inspect_battle_effect_scripts.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O script verifica o hash da ROM, os dois ponteiros de efeito, os bytes iniciais amostrados, a sequência candidata de 248 ponteiros de comandos, os pares opcode→handler citados, os literais do dispatcher e o trampoline `BX r0`. Não cobre interpretação completa dos comandos nem comportamento dinâmico.

Próximos passos neste recorte:

1. seguir handlers selecionados adiante até as rotinas de batalha que alteram estado, calculam dano e produzem texto/animação; confirmar retornos e consumo do cursor;
2. comparar mais índices/entradas de efeito e procurar IDs fora dos limites candidatos e demais callers;
3. continuar a auditoria ampla de outras camadas da ROM, sem tratar o motor de batalhas ou os scripts aqui amostrados como cobertura global.
