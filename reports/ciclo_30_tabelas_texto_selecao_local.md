# Ciclo 30 — opcodes locais `0x13`/`0x14` e seleção por tabela

**Estado:** segui os opcodes `0x13` e `0x14` da tabela local aos handlers `0x0801FE31` e `0x0801FE85`. Ambos leem um pointer u32 inline, selecionam um halfword com um byte local de índice multiplicado por 2, acionam caminhos distintos de texto/seleção e avançam o cursor em cinco bytes. Os nomes upstream são cruzamento, não símbolos recuperados da ROM.

## Identidade e ferramentas

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Desmontagem Thumb local com Capstone 5.0.7 temporário em `/tmp/capstone-py`; verificações auxiliares em `scripts/inspect_battle_table_text_commands.py`.
- Fonte upstream `pret/pokefirered` fixada em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, usada somente para cruzar nomes e estrutura.
- REA/Ghidra não foram usados; não houve execução dinâmica nem alteração da ROM.

## Dispatch local

A tabela em `0x0825011C` contém `0x13→0x0801FE31` (instruções em `0x0801FE30`) e `0x14→0x0801FE85` (instruções em `0x0801FE84`). Ambos os handlers primeiro leem a word em `0x02023BC8`; se não-zero, retornam sem avançar o cursor `0x02023D74`.

## Evidência local comum aos dois handlers

A partir da word apontada pelo cursor, cada handler lê bytes nos offsets `+1`, `+2`, `+3` e `+4`, combina-os little-endian como valor de 32 bits e usa esse valor como base. Lê também um byte em `0x02023E82 + 5`, multiplica-o por 2 e soma o deslocamento ao pointer-base. Em seguida carrega um halfword do endereço resultante.

A estrutura local é compatível com um endereço inline seguido de seleção de elemento u16: o código prova montagem de quatro bytes, uso de índice local vezes dois e `LDRH`; o layout/propósito nominal são cross-reference.

## Opcode `0x13`

Após carregar o halfword selecionado, o handler lê o byte em `0x02023D6B` e chama `0x080173AC` com esse byte e o halfword. Depois incrementa `0x02023D74` em 5 e define como 1 o byte `0x02023E82 + 7`. Se a word de `0x02023BC8` estiver ocupada, não executa essas operações.

## Opcode `0x14`

Após carregar o halfword selecionado, copia o byte de `0x02023D6B` para `0x02023BC4`, chama `0x0800E3EC` com argumento inicial zero e o halfword, e chama `0x08017248` com o battler copiado. Então incrementa o cursor em 5 e define `0x02023E82 + 7` como 1. Também retorna sem operar se `0x02023BC8` estiver ocupado.

## Cruzamento semântico upstream — separado

Na tabela `gBattleScriptingCommandsTable` upstream, os índices são `Cmd_printfromtable` (`0x13`) e `Cmd_printselectionstringfromtable` (`0x14`). O código-fonte descreve o pointer inline como endereço de uma sequência de u16, usa `gBattleCommunication[MULTISTRING_CHOOSER]` como índice e, respectivamente, prepara uma string ou envia uma string de seleção ao battler atacante. Os offsets simbólicos upstream `MULTISTRING_CHOOSER=5` e `MSG_DISPLAY=7` coincidem com os bytes `+5` e `+7` observados na ROM. Esta identificação é compatível com o código local, mas os nomes continuam sendo do upstream.

Arquivos upstream consultados (SHA-256):

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`;
- `include/constants/battle_script_commands.h`: `2365a9d5581325edcf41bf654ebbe70df6dea89defdf4f51bb0c962637444b30`.

## Reprodução e limites

```bash
python -m py_compile scripts/inspect_battle_table_text_commands.py
python scripts/inspect_battle_table_text_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador auxilia na confirmação do hash, dispatch, padrões Thumb e literais. Não valida conteúdo dos elementos apontados em uso nem efeitos observados em execução. Permanecem pendentes a amostragem de call sites/ponteiros concretos, consumidores adicionais do estado de texto e os handlers seguintes. A análise é estática e parcial; não se declara cobertura global.
