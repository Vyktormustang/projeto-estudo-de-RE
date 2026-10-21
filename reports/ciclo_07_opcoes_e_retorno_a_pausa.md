# Ciclo 07 — Opções e retorno à pausa

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Resultado

A opção **Opções** abandona a task de input do menu de pausa e inicia outro
menu por `SetMainCallback2`. Antes da troca, a ação guarda em
`gMain.savedCallback` o callback Thumb `0x080568A9`, que retorna ao campo
reabrindo a pausa. B na tela Opções é aceito pela mesma saída que A; o fluxo
faz fade-out, grava as configurações em memória, restaura esse callback e
encerra a task do menu Opções. No mGBA, o resultado visual voltou à pausa, com
Opções ainda selecionado.

```text
ID 5 / registro 0x083A736C → callback Thumb 0x0806F4FD (código 0x0806F4FC)
  → aguarda o fade; prepara a saída do menu de pausa
  → SetMainCallback2(0x08088389)
  → grava 0x080568A9 em gMain+8 (0x030030F8); retorna 1
  → inicialização local 0x08088388; callback de montagem 0x08088455
  → callback state machine 0x08088454, estados 0–9
  → cria task com callback Thumb 0x08088781 (código 0x08088780)
  → input A ou B retorna código 1; avança loadState para 3
  → fade-out e rotina local 0x08088B00
  → SetMainCallback2(*(u32 *)0x030030F8) = 0x080568A9
  → retorno ao campo e reconstrução da pausa
```

## Evidência local da ROM

- O registro de ação ID 5 em `0x083A736C` guarda `0x0806F4FD`. Em
  `0x0806F4FC`, se o fade está ativo, a rotina retorna 0. No caminho sem fade,
  chama as rotinas locais `0x0807B004`, `0x0806EF18` e `0x080563F0`, instala
  callback2 `0x08088389` via `0x08000544`, grava `0x080568A9` em
  `0x030030F8` e retorna 1 para encerrar a task de input da pausa.
- `0x08088388` verifica o campo `+8` da estrutura em `0x030030F0`; se estiver
  nulo, grava ali o fallback `0x080568A9`. Aloca uma estrutura de `0x14` bytes,
  inicializa os estados/opções e, ao final, instala `0x08088455` como callback2.
  O estado do menu é acessado pelo ponteiro global em `0x0300500C`.
- `0x08088454` despacha os estados de montagem. No estado seguinte ao 9, a
  rotina `0x08088514` cria uma task com o callback Thumb `0x08088781` e instala
  `0x0808835D` (código em `0x0808835C`) como callback2 para execução das tasks.
- A task local `0x08088780` processa o `loadState` no byte `+0x10` da estrutura.
  No estado de input, chama `0x080888C0`. Essa rotina testa as teclas B e A e
  retorna 1 para qualquer uma delas; a tabela de dispatch em `0x080887F4`
  encaminha esse resultado para a transição que incrementa `loadState`.
- Os estados seguintes iniciam o fade-out, aguardam o término e chamam
  `0x08088B00`. Essa rotina grava `0x0807DF65` em `0x03005020`, lê
  `gMain.savedCallback` em `0x030030F8` e passa o ponteiro a `SetMainCallback2`
  (`0x08000544`). Também copia os valores atuais das opções para a estrutura de
  save em RAM, libera buffers/janelas e destrói a task. Não houve gravação de
  arquivo de save durante o teste.
- O callback restaurado `0x080568A9` corresponde ao caminho observado no ciclo
  04: após limpar o bit Thumb, `0x080568A8` segue por `0x080567DC` e
  `0x0806F1D4`, reconstruindo o menu de pausa e reativando o input.

## Validação visual no mGBA

Usei `scripts/gba_libretro_emu.py`, mGBA 0.10.5, e
`google_drive/viridian_masterball.state`, sem `--save-file`. Sequência: START,
quatro DOWN até Opções, A para abrir e B para voltar. A primeira captura mostra
a tela nativa de opções; a segunda mostra a pausa reaberta com Opções selecionado.

- `reports/ciclo_07_opcoes_abertas.png` — tela de Opções aberta.
- `reports/ciclo_07_retorno_pausa.png` — retorno à pausa após B.

Validação visual apenas: o driver não fornece PC trace/breakpoints e não houve
teste em hardware real. A ROM-base não foi alterada.

## Cruzamento com upstream — nomes, não prova local

O disassembly, ponteiros, stores, branches e resultado de emulação acima foram
conferidos na ROM local. Para facilitar a leitura, os nomes C correspondentes
no upstream `pret/pokefirered` são `StartMenuOptionCallback` em `start_menu.c` e
`CB2_OptionsMenuFromStartMenu`, `CB2_OptionMenu`, `Task_OptionMenu`,
`OptionMenu_ProcessInput` e `CloseAndSaveOptionMenu` em `option_menu.c`. O retorno
`0x080568A9` cruza com `CB2_ReturnToFieldWithOpenMenu` em `overworld.c`. Os blobs
consultados são, respectivamente, `88cc377cea556d3663aa5ea5f5bd4537cb29ea72`,
`0b55a34ffd8869e3c616553108e1487c9db657df` e
`339014da46ae8543143edc99ab72bf7496203a0d`. O tarball veio de `master`, sem
commit fixado; esses nomes são referência semântica e não substituem a evidência
local.
