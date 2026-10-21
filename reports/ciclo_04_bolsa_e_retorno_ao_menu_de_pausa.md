# Ciclo 04 — input da Bolsa → retorno por B ao menu de pausa

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Resultado

Fechado o caminho iniciado no callback `0x08126EB0`: o ROM passa um callback de
tarefa localizado em `0x0811FB28` à inicialização da Bolsa; o input B é
normalizado para o código 2, dispara a rota de encerramento com fade, e instala
o callback de retorno `0x080568A9`. No retorno ao campo, um callback configura o
desenho da pausa; depois do fade-in, o ROM cria novamente a task de input do
menu. O caminho foi confirmado estaticamente e observado visualmente no mGBA.

```text
0x08126EB0
  → 0x0811EA44 configura estado + callbacks
  → SetMainCallback2(0x0811EBD1)
  → inicialização da Bolsa cria task com callback 0x0811FB29
  → input B: 0x0811FEFC retorna 2
  → 0x0811FB28 → 0x0811FD88 → 0x0811FA78
  → fade-out; task troca para callback 0x0811FAB5
  → depois do fade: SetMainCallback2(0x080568A9), limpa recursos
  → 0x080568A8 grava FieldCallback2 = 0x0807E3BD e chama 0x080567DC
  → restauração do campo e callback de retorno
  → 0x0807E3BC → 0x0806F1D4 configura FieldCallback2 = 0x0806F1B9
  → desenho da pausa; fade-in por 0x0807E3A0
  → task 0x0807E378 cria a task 0x0806F281 (input da pausa), prioridade 0x50
```

## Evidência local da ROM

### 1. Callback da Bolsa e task de input

Em `0x08126EB0`, o ROM prepara os argumentos na pilha e chama `0x0811EA44`.
Os words literais do chamador incluem:

- `0x0811FB29` — ponteiro Thumb armazenado no estado alocado da Bolsa como
  callback de task;
- `0x080568A9` — ponteiro Thumb passado como callback de retorno;
- os argumentos iniciais de localização/bolso são zero neste caminho.

A inicialização em `0x0811EA44` grava os callbacks no estado da Bolsa e, ao
concluir, registra `0x0811EBD1` por `SetMainCallback2` (`0x08000544`). A rotina
`0x0811EBD0` executa a inicialização por estados. Na etapa de criação da task,
`0x0811EDB4–0x0811EDC6` carrega o callback armazenado e chama `CreateTask`
(`0x0807741C`). Assim, o ponteiro de callback recebido em `0x08126EB0` chega ao
scheduler de tasks.

A rotina em `0x0811FB28` corresponde funcionalmente ao handler de input da
Bolsa: recebe `taskId`, espera enquanto fade/link impede input, processa mudança
de bolso e despacha o resultado do input. Identificação do nome como
`Task_BagMenu_HandleInput` é cruzamento com upstream, não símbolo presente na
ROM.

### 2. Rota local do botão B

A função `0x0811FEFC` consulta os bits de input de `gMain`. Para B, o bit `0x2`
passa pela máscara `0x3` e a função retorna o código 2. A rotina chamadora
`0x0811FB28` compara o resultado com 2 e segue para `0x0811FB78`, que chama
`0x0811FD88`.

Para a localização de campo usada por este callback, `0x0811FD88` segue o caso
geral de encerramento: limpa o item especial para `ITEM_NONE` (a atribuição de
nome é confirmada pelo fonte upstream), prepara a task para saída e chama
`0x0811FA78`. Esta rotina inicia o fade e substitui o callback atual da task
pelo ponteiro Thumb `0x0811FAB5`. O código em `0x0811FAB4` aguarda o término do
fade; se não houver callback de saída específico, instala o callback de retorno
da Bolsa com `SetMainCallback2`, libera recursos e destrói a task.

No caminho iniciado por `0x08126EB0`, o callback de retorno observado na ROM é
`0x080568A9` (código em `0x080568A8`). Portanto, a identidade e a transição
crucial do callback de retorno não dependem apenas do nome upstream.

### 3. Restauração do campo e reabertura da pausa

`0x080568A8` chama `0x080569BC`, grava o ponteiro Thumb `0x0807E3BD` em
`0x03005024` e chama `0x080567DC`. O disassembly local de `0x0807E3BC` mostra
que ele chama `0x0806F1D4` e retorna zero. `0x0806F1D4` zera os dois bytes de
estado de desenho em `0x020370FF` e grava `0x0806F1B9` em `0x03005024`.

O código em `0x0806F1B8` chama `0x0806F01C` repetidamente para preparar o menu;
quando o desenho termina, chama `0x0807E3A0`. Esta rotina inicia o fade-in,
cria a task callback `0x0807E379` com prioridade `0x50` e bloqueia os controles
do jogador. A função de task em `0x0807E378` aguarda o fim do fade, destrói a
si própria e cria outra task com callback `0x0806F281`, também prioridade
`0x50`. Esse é o handler de input do menu de pausa identificado no ciclo 02.

A atribuição funcional dos callbacks de campo aos nomes abaixo foi cruzada com
o fonte upstream. A reabertura também foi observada no emulador, sem depender
apenas dessa correspondência de nomes.

## Validação no emulador

Usado o driver libretro do repositório com mGBA 0.10.5 e o estado
`google_drive/viridian_masterball.state` (sem carregar nem sobrescrever o save
original). Sequência: START abriu o menu nativo; DOWN + A abriu a Bolsa; B saiu
da Bolsa. O frame final mostrou o menu de pausa novamente aberto, com o cursor
na opção Bolsa.

- `reports/ciclo_04_bolsa_aberta.png` — tela da Bolsa antes de B.
- `reports/ciclo_04_b_bolsa_retorno_pause.png` — menu nativo de pausa após B.

Esta é confirmação visual de execução no mGBA, não um PC trace: o driver atual
não oferece breakpoint/trace de PC. Não houve teste em hardware real.

## Cruzamento upstream e limites

Os nomes de alto nível foram usados apenas como referência e separados das
observações no binário:

- `src/item_menu.c`, blob `8f52ead00ec1e34df74dadb71aa23439d507b073`: cruza
  `CB2_BagMenuFromStartMenu`, `Task_BagMenu_HandleInput` e o fluxo de fade/saída;
- `src/overworld.c`, blob `339014da46ae8543143edc99ab72bf7496203a0d`: cruza
  `CB2_ReturnToFieldWithOpenMenu` e o callback de retorno;
- `src/start_menu.c`, blob `88cc377cea556d3663aa5ea5f5bd4537cb29ea72`: cruza
  `SetUpReturnToStartMenu`, `FieldCB2_DrawStartMenu` e
  `Task_StartMenuHandleInput`;
- `src/field_fadetransition.c`, blob
  `f392a06d5c05966441ab448fec9f5a06c908c489`: cruza
  `FieldCB_ReturnToFieldOpenStartMenu` e o fade de reabertura.

Os endereços, ponteiros Thumb, gravações, chamadas e branches descritos acima
foram verificados na ROM-base. Os nomes C não devem ser lidos como símbolos
extraídos do binário.

## Fechamento do ciclo

**Fechado:** callback inicial da Bolsa → task de input → resultado local do B →
fade/limpeza → callback de retorno → restauração do campo → desenho e input do
menu de pausa novamente ativos.

**Pendente fora do escopo desta trilha:** PC trace com debugger e validação em
hardware real. Não é necessário seguir outras opções do menu para demonstrar
este retorno por B.
