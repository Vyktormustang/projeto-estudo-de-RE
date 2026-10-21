# Ciclo 08 — Sair e fechamento da pausa

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Resultado

A ação **Sair** fecha a pausa no contexto de campo atual. A rotina de ação não
instala outro callback2 nem grava um callback de retorno: ela limpa elementos
auxiliares, fecha a janela da pausa, descongela/libera o controle do jogador e
retorna sucesso. O dispatcher de task então encerra a task de input. No mGBA,
a tela final voltou ao campo, sem o menu de pausa.

```text
ID 6 / registro 0x083A7374 → callback Thumb 0x0806F541 (código 0x0806F540)
  → 0x0806EF18: limpeza condicional da janela de estatísticas da Zona Safari
  → 0x080F7998: limpeza da janela de ajuda
  → 0x0806FEA0: fecha a janela da pausa e libera controles do campo
  → retorna 1 ao dispatcher da task
  → task de input é encerrada; o campo fica ativo, sem reconstruir a pausa
```

## Evidência local da ROM

- A entrada ID 6 da tabela de ações, em `0x083A7374`, contém o ponteiro Thumb
  `0x0806F541`. O código em `0x0806F540` chama, nessa ordem, `0x0806EF18`,
  `0x080F7998` e `0x0806FEA0`; depois retorna 1.
- `0x0806EF18` chama `0x080A0E90`; se a condição consultada for verdadeira,
  remove uma janela e libera seus recursos. O caminho condicional é consistente
  com a limpeza de estatísticas Safari; o nome é cruzado com upstream.
- `0x080F7998` delega a limpeza auxiliar a `0x08112EDC` com argumento 2.
- `0x0806FEA0` reproduz, localmente, as etapas de fechamento: chama o helper de
  som associado ao índice 5, obtém/processa o ID da janela do menu, remove a
  janela, chama helpers de movimento/descongelamento e libera os controles do
  jogador. A identificação desses helpers pelos nomes C é apenas cruzamento.
- Diferentemente da ação Opções, `0x0806F540` não chama
  `SetMainCallback2` (`0x08000544`) nem grava `gMain.savedCallback`. O retorno 1
  encerra o callback de ação na task já descrita nos ciclos anteriores; não há
  caminho de reconstrução do menu.

## Validação visual no mGBA

Usei `scripts/gba_libretro_emu.py`, mGBA 0.10.5, e
`google_drive/viridian_masterball.state`, sem `--save-file`. Sequência: START,
cinco DOWN até Sair, A. A primeira captura mostra Sair selecionado; a segunda
mostra o campo com a pausa fechada.

- `reports/ciclo_08_sair_selecionado.png` — item Sair selecionado.
- `reports/ciclo_08_sair_fecha_pausa.png` — campo após fechar a pausa.

A ROM-base manteve o SHA-256 registrado. Validação visual apenas, sem PC trace,
breakpoints ou teste em hardware real.

## Cruzamento com upstream — nomes, não prova local

O código local corresponde semanticamente a `StartMenuExitCallback`,
`DestroySafariZoneStatsWindow`, `DestroyHelpMessageWindow_` e `CloseStartMenu`
em `pret/pokefirered/src/start_menu.c`, blob
`88cc377cea556d3663aa5ea5f5bd4537cb29ea72`. Os nomes auxiliam a leitura; os
ponteiros, ordem das chamadas, ausência de troca de callback2 e retorno 1 foram
conferidos na ROM local. Upstream veio de `master`, sem commit fixado.
