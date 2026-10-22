# Ciclo 23 — `accuracycheck`: fluxo local de acerto, falha e cursor

**Estado:** aprofundado o caminho amostrado do efeito ID 0, do bytecode de precisão até a seleção local entre continuar o script e saltar para o endereço de falha. A ROM confirma uma rotina grande de cálculo e helpers, mas não foram percorridos todos os ramos nem a cadeia posterior até dano/efeitos visuais. Continua sendo análise estática.

## Identidade, ferramentas e separação de evidência

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Desmontagem Thumb local com Capstone 5.0.7 instalado temporariamente em `/tmp/capstone-py`; bytes e verificações reproduzíveis por `scripts/inspect_accuracy_path.py`.
- A árvore upstream `pret/pokefirered` foi baixada temporariamente, fixada no commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, e consultada somente para sugerir nomenclatura/semântica.
- Não foram usados REA ou Ghidra, não houve execução em emulador e nenhum byte da ROM/save foi alterado.

## Bytecode e dispatch local

O índice 0 da tabela de scripts (`0x081D65A8`) aponta localmente para `0x081D6900`. O bytecode de precisão começa em `0x081D6927`:

```text
01 5E 69 1D 08 00 00
```

A tabela local de comandos em `0x0825011C` associa opcode `0x01` ao handler Thumb `0x0801DDC5`. Os operands inline são um endereço de desvio `0x081D695E` e um halfword `0x0000`. O bytecode seguinte, no caminho linear, começa em `0x081D692E` com opcodes `02 03 04 05 ...`; o destino `0x081D695E` também começa com bytes `02 03 ...`.

A ROM local confirma o cursor do bytecode pelo endereço RAM `0x02023D74`. Em `0x0801DDC4–0x0801DDDA`, o handler obtém os bytes `+5` e `+6` do comando e combina-os num halfword. Essa é a leitura local do operand `0x0000`; a identificação nominal do operand é cruzamento separado.

## Caminho observado dentro do handler

No handler local `0x0801DDC5`, o valor `0x0000` segue por uma comparação em `0x0801DF0C`. Se igual a zero, o código lê um halfword do endereço RAM `0x02023D4A` e usa o resultado em `r6`. Isso mostra na ROM que esse valor sentinela seleciona outro ID carregado de RAM; a nomeação desse ID como move corrente é compatível com outros acessos locais/cross-check, mas o endereço e a leitura são a evidência direta.

O código forma endereços de registro com `ID × 12 + 0x08250C04`. No caminho disassemblado, há loads dos bytes `+2` (`0x0801DF3E`) e `+3` (`0x0801DFCA`). O handler continua por várias decisões/ajustes e faz chamadas locais, incluindo `0x08044EC8` e `0x081E4684`; imediatamente antes da segunda chamada, o código carrega o imediato decimal 100. O retorno é incrementado e comparado com o valor calculado, com desvio local para `0x0801E1BA` em um dos resultados. Esses são fatos de instrução; os nomes matemáticos dos helpers e o significado nominal do campo vêm do cruzamento upstream.

No caminho em que a comparação local não passa, o código em `0x0801E168–0x0801E170` lê um byte de `0x02023DCC`, aplica OR com `1` e escreve o byte de volta. Em seguida, os ramos convergem para a chamada local em `0x0801E1BA–0x0801E1C0`, que fornece o deslocamento `7` e o ID ao helper `0x0801DB10`.

O helper `0x0801DB10` usa o cursor em `0x02023D74`, calcula `cursor + deslocamento` e verifica o byte em `0x02023DCC` mascarado por `0x29`. Quando a máscara é zero, o endereço candidato é o avanço linear; quando não é zero, o helper lê uma word do comando atual a partir de `cursor + 1` e usa essa word como endereço candidato. Nos caminhos verificados, o estado de falha recém-marcado (bit 0) está incluído na máscara `0x29`, de modo que o handler de precisão pode selecionar o destino inline `0x081D695E`; no caminho sem esses bits, o candidato é `cursor + 7`, isto é, `0x081D692E`. Há outros helpers/condições no percurso, por isso não se generaliza esse comportamento a todos os estados possíveis.

Isso localiza, na ROM, a escolha de fluxo em torno do teste de precisão: **continuação após o comando ou uso do destino armazenado no próprio bytecode**. A RAM `0x02023DCC` é descrita pelo endereço e operações locais, sem atribuição de nome local não verificado.

## Cruzamento semântico upstream — não é evidência local

No upstream fixado, o opcode `0x01` é `accuracycheck`; o operand zero é `ACC_CURR_MOVE`. `Cmd_accuracycheck` trata o cálculo de acerto e `JumpIfMoveFailed` decide entre cursor linear e ponteiro do bytecode. Isso é compatível com o fluxo local acima. O script `BattleScript_EffectHit` prossegue, após o comando, para comandos de ataque, redução de PP, cálculo crítico e cálculo de dano; a ROM local contém a sequência dos bytes/opcodes, e a tabela local fornece handlers `0x02→0x0801E1D9`, `0x03→0x0801E22D`, `0x04→0x0801E409` e `0x05→0x0801E59D`.

No mesmo upstream, `struct BattleMove` nomeia `+2` como `type` e `+3` como `accuracy`. Uso esses termos apenas como correspondência proposta; os offsets e loads locais acima são independentes desses nomes.

Arquivos upstream consultados e hashes:

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`;
- `data/battle_scripts_1.s`: `27e9c39f3147b05e5ba2ed36ca0c89fcdc9b26718778083bd362c582de800034`;
- `asm/macros/battle_script.inc`: `cd13b8392cf0cf2e7f56e18861e6269a1461c32271c75674a193ac3d39c241c4`;
- `include/pokemon.h`: `a6881fee07ae10f57ebf3ec7af1cabd2e900d8ba8d3da644313c087d16e1617e`.

## Reprodução, testes e lacunas

```bash
python scripts/inspect_accuracy_path.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O script valida hash, bytes de comando, destinations, handler IDs, literais locais e trechos de instrução usados acima. Não substitui a leitura do disassembly nem valida comportamento emulado. A bateria de self-tests passou para os nove scripts com o Capstone temporário no `PYTHONPATH`.

Próximo recorte: seguir o handler local `0x0801E59D` selecionado por opcode `0x05` (cálculo de dano), e relacionar seus loads/calls às operações da ROM; depois seguir comandos posteriores de tipo, animação e atualizações de HP. Cobertura do motor de batalha, da tabela de efeitos e da ROM inteira continua parcial.
