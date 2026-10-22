# Ciclo 43 — handlers locais `0x39`–`0x3B`: pausa, espera e atualização

**Estado:** `0x39` aguarda uma word de controle zerar, incrementa um halfword global e só consome seu operand u16 quando o contador alcança o limite; `0x3A` aguarda a mesma word e avança um byte; `0x3B` escolhe um byte de battler por operand, monta um buffer local, chama duas rotinas e avança dois bytes.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset no arquivo + `0x08000000`. Dispatch, instruções, chamadas e literais conferidos diretamente; desmontagem Thumb estática com Capstone 5.0.7 temporário em `/tmp/capstone-py`.
- Cross-reference apenas para nomes/semântica: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, `src/battle_script_commands.c` (SHA-256 `3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3`).
- REA/Ghidra não foram usados. Não houve execução dinâmica nem alteração da ROM. A rota local de `0x0800D8B0` quando bit `0x02` está ativo passa a `0x0800D9EC` e não foi seguida até o fim; callers concretos também permanecem pendentes.

## Dispatch local

Na tabela `0x0825011C`:

| Opcode | Ponteiro Thumb | Instruções em |
|---|---:|---:|
| `0x39` | `0x08022C09` | `0x08022C08` |
| `0x3A` | `0x08022C49` | `0x08022C48` |
| `0x3B` | `0x08022C69` | `0x08022C68` |

## Evidência local — opcode `0x39`

- Lê a word em `0x02023BC8`. Se não-zero, retorna sem alterar contador ou cursor.
- Se zero, lê o u16 little-endian em `cursor+1..cursor+2`; incrementa o halfword em `0x02023E7C` e grava-o de volta.
- Se o contador incrementado for unsigned menor que o operand u16, retorna sem mover o cursor.
- Caso contrário, zera o halfword em `0x02023E7C`, soma 3 à word-cursor `0x02023D74` e retorna.

## Evidência local — opcode `0x3A`

Lê a word em `0x02023BC8`. Se não-zero, retorna sem avançar. Se zero, soma 1 à word-cursor `0x02023D74`. Não lê operand inline nem chama rotina.

## Evidência local — opcode `0x3B`

- Lê o byte `cursor+1`. Se zero, copia o byte de `0x02023D6C` para `0x02023BC4`; se não-zero, copia o byte de `0x02023D6B` para `0x02023BC4`.
- Lê o halfword em `0x02023D50` e chama `0x0800E5EC` com `r0=0`, `r1=halfword`. Na rotina local, `0x0800E5EC` escreve quatro bytes em `0x02022874`: `0x18`, `0`, byte baixo e byte alto do halfword; chama `0x0800D8B0` com `r0=0`, `r1=0x02022874`, `r2=4`.
- No helper `0x0800D8B0`, se bit `0x02` da word `0x02022B4C` não estiver ativo, os quatro bytes são copiados para `0x02022BC4 + (byte[0x02023BC4] × 0x200)`. Se o bit estiver ativo, o helper segue para `0x0800D9EC` (não analisado até o fim neste ciclo).
- Lê o byte em `0x02023BC4` e chama `0x08017248`. Localmente, essa rotina usa bit `0x02` de `0x02022B4C` para escolher entre uma máscara alta (tabela em `0x0825E45C` deslocada em 28 bits) e a máscara da tabela sem deslocamento; ORa o resultado na word `0x02023BC8`. Os primeiros valores da tabela conferidos são `1, 2, 4, 8, ...`.
- Por fim soma 2 à word-cursor `0x02023D74` e retorna.

Os efeitos acima são endereços, immediates, cópias e operações observados localmente. Não atribuo nomes locais a `0x02023D6B/6C`, ao halfword `0x02023D50` ou aos buffers. As chamadas diretas observadas são `0x0800E5EC` e `0x08017248`; o primeiro chama `0x0800D8B0`, que pode chamar `0x0800D9EC` conforme o bit indicado.

## Cruzamento semântico upstream — separado da prova local

A tabela upstream nomeia `0x39`, `0x3A` e `0x3B` como `Cmd_pause`, `Cmd_waitstate` e `Cmd_healthbar_update`. A implementação upstream interpreta o u16 de `0x39` como limite do pause counter, `0x3A` como espera por conclusão dos controllers e `0x3B` como seleção attacker/target seguida de emissão de atualização da barra de HP e marcação do battler. Esses nomes e a interpretação são cross-reference; localmente foram confirmados primeiro os bytes, ramos, ponteiros, rotinas chamadas e escritas listados acima.

## Reprodução e lacunas

```bash
python -m py_compile scripts/inspect_battle_pause_healthbar_commands.py
python scripts/inspect_battle_pause_healthbar_commands.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O verificador valida SHA-256, dispatch, assinaturas Thumb, chamadas diretas, literais e partes relevantes dos helpers. Não executa comandos, não valida os endereços indiretos fornecidos pelo bytecode e não percorre o caminho completo de `0x0800D9EC`. Este recorte não representa cobertura global; estados de `0x23`, demais comandos/callers e outros subsistemas continuam pendentes.
