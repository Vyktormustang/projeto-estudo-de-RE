# Ciclo 31 — seleção de efeitos de batalha: opcodes locais `0x15`–`0x17`

**Estado:** segui os três índices da tabela de comandos até seus handlers locais. `0x15` lê estado de batalha e chance de efeito, aplica caminhos condicionais e chama um helper compartilhado; `0x16` e `0x17` são wrappers desse helper com argumentos diferentes. Os rótulos “efeito primário/secundário” e as interpretações nominais de campos aparecem apenas no cruzamento upstream.

## Identidade, proveniência e ferramentas

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Mapeamento usado: VA GBA = offset de arquivo + `0x08000000`.
- Dispatch e bytes Thumb lidos da ROM; desmontagem com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Upstream `pret/pokefirered` fixado em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, usado só para cruzamento semântico.
- REA/Ghidra não foram usados. Não houve execução dinâmica nem alteração da ROM.

## Dispatch local

A tabela local em `0x0825011C` contém estes ponteiros Thumb:

| Opcode | Ponteiro no dispatch | Início de instruções |
|---|---:|---:|
| `0x15` | `0x08021125` | `0x08021124` |
| `0x16` | `0x08021211` | `0x08021210` |
| `0x17` | `0x08021221` | `0x08021220` |

Os três caminhos não consomem operandos inline visíveis: `0x15` avança o cursor em uma posição somente em um ramo de falha; os wrappers `0x16`/`0x17` delegam ao helper `0x0801FF20`, sem escrita direta do cursor nos próprios wrappers.

## Evidência local — opcode `0x15`

O handler começa em `0x08021124`. Os endereços de memória abaixo são os valores de literais efetivamente carregados pelo código local, não símbolos locais:

1. Lê o byte em `0x02023D6B`, multiplica-o por `0x58`, soma a base `0x02023BE4` e lê o byte no deslocamento `+0x20` do registro resultante. Se esse byte for `0x20`, busca a chance como byte `+5` de um registro na base `0x08250C04`; o índice para esse registro vem do halfword `0x02023D4A`, com cálculo local equivalente a índice × 12. O valor de chance é multiplicado por 2. Se o byte examinado não for `0x20`, repete a seleção de registro e lê o byte `+5`, sem dobrá-lo.
2. Lê o byte `0x02023E82+3`. Se seu bit `0x80` estiver ativo, examina também `0x02023DCC & 0x29`. Quando essa máscara resulta em zero, limpa o bit `0x80` do byte em `0x02023E82+3`, chama `0x0801FF20(0, 0x80)` e segue à limpeza final, sem passar pelo sorteio.
3. Nos demais caminhos, chama `0x08044EC8`, transforma o retorno para 16 bits, chama `0x081E4684` com divisor `100` e compara o resultado com a chance selecionada. A comparação local deixa passar valores menores ou iguais à chance. Para aplicar, exige também byte não-zero em `0x02023E82+3` e `(0x02023DCC & 0x29) == 0`. Se a chance for maior que `99`, chama `0x0801FF20(0, 0x80)`; caso contrário, chama `0x0801FF20(0, 0)`.
4. Se os testes do caminho sorteado não passarem, incrementa em 1 a word apontada por `0x02023D74`. Todos os caminhos convergem para zerar `0x02023E82+3` e `0x02023E82+0x16`, e então retornam. Nos caminhos que chamam `0x0801FF20`, o handler `0x15` não faz incremento direto do cursor; qualquer redirecionamento/avanço subsequente fica delegado ao helper.

A ROM prova os endereços, strides, comparações, máscaras, argumentos e escritas acima. Ela não fornece, por si só, os nomes “attacker”, “ability”, “move effect”, “secondary chance” ou a intenção de cada flag. Tampouco este recorte caracteriza todos os efeitos do helper `0x0801FF20` ou todos os callers desses opcodes.

## Evidência local — opcodes `0x16` e `0x17`

- `0x16` (`0x08021210`) chama `0x0801FF20` com `r0=1`, `r1=0`, e retorna.
- `0x17` (`0x08021220`) chama o mesmo endereço com `r0=0`, `r1=0`, e retorna.
- Nos dois wrappers, não há leitura de operandos nem ajuste direto de cursor/estado além da preparação dos argumentos e da chamada. Efeitos indiretos da chamada não são atribuídos aos wrappers sem análise própria do helper.

## Cruzamento semântico upstream — não é prova local

Na tabela `gBattleScriptingCommandsTable` de `pret/pokefirered`, os índices `0x15`–`0x17` chamam-se `Cmd_seteffectwithchance`, `Cmd_seteffectprimary` e `Cmd_seteffectsecondary`. A implementação upstream interpreta o campo de offset `+0x20` no registro selecionado como habilidade Serene Grace; o byte `+5` do registro de move como `secondaryEffectChance`; o bit `0x80` como `MOVE_EFFECT_CERTAIN`; e o helper `0x0801FF20` como `SetMoveEffect(primary, certain)`. Essa nomenclatura e interpretação explicam a estrutura local, mas não foram encontradas como símbolos na ROM brasileira.

Arquivos upstream consultados (SHA-256):

- `src/battle_script_commands.c`: `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`;
- `include/constants/battle_script_commands.h`: `2365a9d5581325edcf41bf654ebbe70df6dea89defdf4f51bb0c962637444b30`.

## Reprodução e limites

```bash
python -m py_compile scripts/inspect_battle_effect_chance_commands.py
python scripts/inspect_battle_effect_chance_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador confirma identidade/hash da ROM, entradas do dispatch, padrões Thumb e literais destacados; não emula uma batalha, valida resultados do sorteio ou comprova a interpretação semântica upstream. Permanecem em aberto o comportamento completo do helper compartilhado, os sites de chamada reais em scripts de efeito, os efeitos de cada byte/flag no contexto total, demais handlers e a validação dinâmica. Esta é uma amostra estática, não uma afirmação de cobertura global.
