# Ciclo 10 — Salvar: confirmação SIM e retorno ao campo

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Resultado

Completei o caminho complementar ao cancelamento do ciclo 06. Depois que o
texto termina de imprimir, o menu SIM/NÃO aparece com **SIM** selecionado por
padrão. A confirma SIM, a rotina executa a gravação, apresenta `A salvou o
jogo.` e encerra a task de diálogo. O resultado é **retorno ao campo sem
reabrir a pausa**, diferentemente de B/NÃO, que retorna à pausa.

```text
ID 4 / 0x083A7364 → 0x0806F4E9
  → 0x0806F5A4 prepara o diálogo e a callback interna
  → 0x0806F648 executa a callback atual do diálogo
  → após a impressão, SIM fica selecionado; A confirma
  → mensagem de salvamento; o callback do diálogo conclui
  → resultado 1 em 0x0806F5C8 segue para 0x0806F604
  → limpeza do diálogo, restauração de help e desbloqueio do campo
  → retorno 1 encerra a task da pausa; campo ativo, sem menu
```

## Evidência local da ROM

- O registro ID 4 em `0x083A7364` aponta para `0x0806F4E9`. O fluxo interno
  `0x0806F5A4` prepara o diálogo, e `0x0806F5C8` chama o runner `0x0806F648`.
  O runner aguarda o printer e invoca o callback armazenado em `0x03000FA4`.
- A rotina de resultado em `0x0806F5C8` compara o retorno do runner. Resultado
  1 brancha para `0x0806F604`; resultado 2 continua pelo tratamento CANCEL
  `0x0806F5E4`, que redesenha a pausa e restaura o input. Resultado 3 também vai
  ao encerramento terminal, mas não ocorreu no teste positivo.
- `0x0806F604` limpa a janela de diálogo por `0x0810F260(0, 1)`, executa as
  rotinas locais `0x080696C0`, `0x0806994C` e `0x0812B248`, retorna 1 e encerra o
  callback da task. Não há redesenho da pausa nesse caminho.
- O número de retorno é compatível com o ramo `SAVECB_RETURN_OKAY` do fonte
  upstream. A indicação visual `A salvou o jogo.` confirma que o teste chegou
  ao resultado positivo; a sequência estática por si só não identifica a
  mensagem de sucesso.

## Validação visual no mGBA

Usei `scripts/gba_libretro_emu.py` com mGBA 0.10.5, restaurando
`google_drive/viridian_masterball.state`. Esperei até SIM/NÃO estar visível,
com SIM selecionado, e então pressionei A. O mGBA mostrou `SALVANDO... NÃO
DESLIGUE O CONSOLE.`, depois `A salvou o jogo.` e por fim o campo sem a pausa.
A ROM-base conservou o SHA-256 acima.

- `reports/ciclo_10_sim_selecionado.png` — menu SIM/NÃO, SIM selecionado.
- `reports/ciclo_10_jogo_salvo.png` — mensagem positiva após a gravação.
- `reports/ciclo_10_retorno_campo.png` — campo depois de terminar o fluxo.

Não passei `--save-file`; portanto, o arquivo `.sav` original não foi carregado
nem escrito pelo driver. A operação foi observada no estado de emulação e não
foi validada como gravação persistente em arquivo ou hardware. Sem PC trace ou
breakpoints.

## Cruzamento com upstream — nomes, não prova local

O fluxo corresponde semanticamente a `StartMenuSaveCallback`, `StartCB_Save1`,
`StartCB_Save2`, `RunSaveDialogCB`, `SaveDialogCB_AskSaveHandleInput`,
`SaveDialogCB_DoSave`, `SaveDialogCB_PrintSaveResult` e
`SAVECB_RETURN_OKAY` em `pret/pokefirered/src/start_menu.c`, blob
`88cc377cea556d3663aa5ea5f5bd4537cb29ea72`. Os nomes são cruzamento; callbacks,
branches e o retorno visual foram verificados na ROM local. O tarball upstream
veio de `master`, sem commit fixado.
