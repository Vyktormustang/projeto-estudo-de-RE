# Ciclo 33 — handlers locais `0x1B`–`0x1D`: limpeza e saltos por status

**Estado:** os três handlers foram confirmados na tabela local. `0x1B` aguarda um word de controle, zera um word do registro selecionado e chama rotinas auxiliares antes de avançar em 2. `0x1C` e `0x1D` leem um seletor, uma máscara de 32 bits e um destino de 32 bits; testam campos distintos do registro e avançam em 10 ou substituem o cursor pelo destino inline. As interpretações nominais estão separadas como cross-reference.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset do arquivo + `0x08000000`. Bytes e dispatch conferidos diretamente; desmontagem Thumb com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Upstream `pret/pokefirered` fixado em `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, usado somente para nomes e explicação cruzada.
- REA/Ghidra não foram usados; não houve execução dinâmica nem alteração da ROM.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x1B` | `0x080215DD` | `0x080215DC` |
| `0x1C` | `0x08021641` | `0x08021640` |
| `0x1D` | `0x080216B9` | `0x080216B8` |

## Evidência local — opcode `0x1B`

1. Lê a word `0x02023BC8`. Se diferente de zero, retorna sem alterar o cursor.
2. Caso contrário, lê `cursor+1` (`cursor` em `0x02023D74`), chama `0x08016E24` e grava o byte retornado em `0x02023BC4`.
3. Calcula o endereço `0x02023BE4 + battler×0x58 + 0x4C`, zera o word nesse endereço e passa seu endereço na pilha a `0x0800DFF0`, junto dos argumentos em registradores `(0, 0x28, 0, 4)`.
4. Chama `0x08017248` com o byte de `0x02023BC4`, chama `0x08012BC8`, avança `0x02023D74` em 2 e retorna.

## Evidência local — opcodes `0x1C` e `0x1D`

Os dois handlers têm a mesma estrutura local, mas selecionam offsets de word distintos:

1. Lê `cursor+1`, chama `0x08016E24` e mantém o byte retornado como índice de battler.
2. Remonta little-endian a máscara u32 de `cursor+2..cursor+5` e o destino u32 de `cursor+6..cursor+9`.
3. Seleciona um word em `0x02023BE4 + battler×0x58 + offset`, aplica a máscara e testa o resultado. Para `0x1C`, `offset=0x4C`; para `0x1D`, `offset=0x50`.
4. Se o AND for não-zero, lê o halfword em `0x02023BE4 + battler×0x58 + 0x28`. Somente se esse halfword também for não-zero grava o destino inline no word `0x02023D74` e retorna. Nos demais casos, soma 10 ao word de cursor e retorna.

Assim, localmente os handlers têm operands de tamanho total 10 bytes (opcode + seletor + dois words), e o cursor é redirecionado para o valor inline ou avança `+10`. A ROM prova os campos e condições numéricas; não identifica seus nomes simbólicos.

## Cruzamento semântico upstream — separado da prova local

Na `gBattleScriptingCommandsTable` da revisão upstream fixada, os índices `0x1B`, `0x1C` e `0x1D` correspondem a `Cmd_cleareffectsonfaint`, `Cmd_jumpifstatus` e `Cmd_jumpifstatus2`. A implementação upstream chama a rotina associada a `0x08012BC8` `FaintClearSetData`, interpreta os offsets `+0x4C`/`+0x50` como `status1`/`status2`, o halfword `+0x28` como HP e a condição como teste do status com HP não-zero. Esses nomes explicam os padrões locais, mas não são símbolos recuperados da ROM BR.

Fonte cruzada: `src/battle_script_commands.c`, SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`.

## Reprodução e limites

```bash
python -m py_compile scripts/inspect_battle_status_jump_commands.py
python scripts/inspect_battle_status_jump_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador confirma hash, dispatch, assinaturas Thumb e literais. Não valida efeitos em emulação, efeitos das chamadas auxiliares, nem todos os scripts que fornecem máscaras/destinos. Permanecem pendentes callers e operands concretos, semântica de campos comprovada localmente e validação dinâmica. Este recorte é parcial; não declara cobertura global.
