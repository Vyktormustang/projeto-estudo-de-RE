# Ciclo 06 — callback Salvar e retorno do diálogo cancelado

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Resultado

Segui a opção **Salvar** como segundo tipo de callback do menu de pausa. Ao
contrário da Bolsa, selecionar Salvar não troca imediatamente o callback2 do
jogo nem sai para outro menu: a task do menu continua viva e troca o callback
interno de `sStartMenuCallback` em etapas. Cancelar o diálogo retorna ao próprio
menu nativo de pausa.

```text
ID 4 → callback 0x0806F4E9
  → 0x0806F4E8 grava 0x0806F5A5 em 0x020370F0; retorna 0
  → 0x0806F1F0 continua executando a mesma task
  → 0x0806F5A4 prepara contexto/help/save; grava 0x0806F5C9; retorna 0
  → 0x0806F5C8 chama runner de diálogo 0x0806F648
  → resultado CANCEL (2): limpa diálogo, redesenha a pausa,
    restaura help, reinstala 0x0806F281; retorna 0
  → input da pausa fica ativo de novo
```

## Evidência local da ROM

- O registro ID 4 em `0x083A7364` contém o callback Thumb `0x0806F4E9` (código
  em `0x0806F4E8`). Essa função grava o ponteiro Thumb `0x0806F5A5` em
  `0x020370F0` e retorna zero.
- O dispatcher de task `0x0806F1F0` invoca o callback em `0x020370F0` por
  `0x081E3BA8`. Retorno zero mantém a task; retorno um encerra-a. Assim, a
  transição inicial para a rotina seguinte do Save permanece no mesmo menu.
- A rotina local `0x0806F5A4` chama `0x0812B234`, `0x0812B1F0` e `0x0806F624`,
  grava o ponteiro Thumb `0x0806F5C9` em `0x020370F0` e retorna zero.
- `0x0806F5C8` chama `0x0806F648`, que consulta o estado do printer e, quando
  está pronto, lê o callback em `0x03000FA4` e o invoca por `0x081E3BA8`.
  `0x0806F624` prepara esse callback e zera o byte em `0x03000FA9`. Nomes
  simbólicos para esses campos são inferidos por cruzamento com upstream.
- Em `0x0806F5C8`, resultado 2 segue o branch para `0x0806F5E4`: chama
  `0x0810F260(0, 0)` para limpar a janela de diálogo, chama
  `0x0806F14C` para redesenhar o menu sincronamente, chama `0x0812B248`, grava
  `0x0806F281` em `0x020370F0` e retorna zero. O handler de input da pausa
  volta, portanto, sem destruir a task.
- Resultados 1 e 3 seguem `0x0806F604`, limpam o diálogo, desbloqueiam controles,
  restauram contexto e retornam um; a task chamadora termina. O destino visual
  após os resultados terminais não foi o foco deste ciclo.

O fonte upstream identifica essas etapas como `StartMenuSaveCallback`,
`StartCB_Save1`, `StartCB_Save2`, `RunSaveDialogCB` e o caso
`SAVECB_RETURN_CANCEL`. Os nomes são apenas cruzamento; os endereços, stores,
branches e chamadas listados acima são observações locais na ROM.

## Diferença para a rota da Bolsa

Na rota da Bolsa, o callback de ação aguarda fade, destrói recursos do menu e
instala outro callback2 (`0x08126EB0`); B mais tarde retorna ao campo por
`0x080568A9` e reconstrói a pausa. No fluxo Salvar, a pergunta é conduzida por
callback interno à task existente. O caso de cancelamento redesenha a pausa
localmente e reativa seu handler `0x0806F281`, sem reconstruir o overworld.

## Validação no mGBA

Usei `scripts/gba_libretro_emu.py` com o core mGBA 0.10.5 e o estado
`google_drive/viridian_masterball.state`, sem passar `--save-file` nem confirmar
uma gravação. Sequência: START; três DOWN até Salvar; A; dois B. O primeiro avançou do texto
da pergunta para o diálogo SIM/NÃO; o segundo escolheu/cancelou para NÃO. A tela
final voltou ao menu nativo, com Salvar selecionado.

- `reports/ciclo_06_pergunta_salvar_sim_nao.png` — diálogo SIM/NÃO antes da
  confirmação negativa.
- `reports/ciclo_06_cancelamento_volta_pausa.png` — menu de pausa depois do
  cancelamento.

Confirmação visual apenas, sem PC trace e sem validação em hardware real.

## Cruzamento upstream

`pret/pokefirered/src/start_menu.c`, blob
`88cc377cea556d3663aa5ea5f5bd4537cb29ea72`. O fonte é referência para os nomes
C e os estados semânticos do diálogo; não substitui o disassembly da ROM.
