# Ciclo 03 — item do menu de pausa → callback Bolsa

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Resultado

Fechei estaticamente a sequência de uma seleção real do menu nativo de pausa,
seguindo o item **Bolsa** até a instalação do callback de abertura da Bolsa:

```text
loop de frames
  → callback2 0x08078B9C
  → RunTasks 0x08077578
  → task50_startmenu 0x0806F168
  → follow-up Task_StartMenuHandleInput 0x0806F1F0
  → sStartMenuCallback = StartCB_HandleInput 0x0806F280
  → A seleciona o ID 2; tabela 0x083A7344 fornece 0x0806F481
  → fade; Task_StartMenuHandleInput chama 0x0806F481 por BX R0
  → StartMenuBagCallback instala 0x08126EB0 com SetMainCallback2
  → callback retorna TRUE; task do menu é destruída
```

O nome simbólico das rotinas foi conferido com `pret/pokefirered/src/start_menu.c`
(commit/blob `88cc377cea556d3663aa5ea5f5bd4537cb29ea72`). Os endereços e a
sequência principal abaixo foram conferidos no disassembly da ROM-base; a fonte
upstream é uma referência auxiliar de nomes, não substitui essa evidência.

## Evidência por etapa

### 1. Task de desenho e follow-up

`0x0806F258` inicia `0x0806F188` com o ponteiro Thumb `0x0806F1F1` como função de
follow-up. `0x0806F188` limpa os dois bytes de estado do desenho, cria uma task
com prioridade `0x50` e callback Thumb `0x0806F169` (código em `0x0806F168`), e
registra o follow-up via `0x080775E8`.

A task inicial executa o dispatcher de desenho `0x0806F01C` por meio de
`0x0806F168`. Quando o dispatcher retorna 1, chama `0x0807761C`, que recupera o
follow-up armazenado na task e o instala como callback ativo. Isso corresponde
ao fluxo `task50_startmenu` → `Task_StartMenuHandleInput`.

### 2. Handler de input e chamada do callback selecionado

A função `0x0806F1F0` usa `gTasks[taskId].data[0]` como estado:

- Estado 0: verifica a condição de Union Room; grava o ponteiro Thumb
  `0x0806F281` em `0x020370F0` e incrementa o estado.
- Estado 1: carrega o ponteiro de `0x020370F0`, chama `0x081E3BA8` (`BX R0`) e,
  se o callback retornar 1, destrói a task com `0x08077508`.

O callback inicialmente instalado é `0x0806F280` (`StartCB_HandleInput`). Esse
handler lê `gMain + 0x2E`, processa as direções/A/B/START e, em A, obtém o ID do
item selecionado pelo cursor (`0x020370F4`) e buffer de ordem (`0x020370F6`).
Busca o callback no registro de 8 bytes da tabela `0x083A7344` e grava o
ponteiro em `0x020370F0`.

### 3. Seleção da Bolsa

A leitura direta da tabela confirma a entrada de ID 2:

- Registro: `0x083A7354`.
- Callback guardado no campo `+4`: `0x0806F481` (código em `0x0806F480`).

Depois de armazenar o callback escolhido, o handler chama `0x0806F394`. O
corpo compara o ponteiro com as ações especiais Salvar/Sair/Retirar da Safari;
para Bolsa (e outras ações que deixam o overworld), chama o encerramento do
task de efeito `0x080CCB68` e inicia o fade pelo caminho `0x0807A818(1, 0)`.
O handler de input retorna sem encerrar a task; ela continua sendo executada
pelo scheduler de tasks do ciclo 01.

### 4. Execução de `StartMenuBagCallback`

No ciclo de task seguinte, `0x0806F1F0` chama indiretamente `0x0806F481` por
`BX R0`. Essa função:

1. consulta o byte de estado de fade (`0x02037AB8 + 7`) e retorna 0 enquanto o
   fade ainda estiver ativo;
2. quando o fade termina, chama `0x0807B004`, `0x0806EF18` e `0x080563F0` para
   a sequência de som/limpeza;
3. carrega o ponteiro Thumb `0x08126EB1` e chama `0x08000544` (`SetMainCallback2`);
4. retorna 1; o chamador `0x0806F1F0` então encerra a task do menu.

O destino efetivo do callback é `0x08126EB0`. No fonte upstream, o nome
correspondente é `CB2_BagMenuFromStartMenu`; a rotina local nesse endereço
inicializa a transição para a interface da Bolsa.

## O que foi fechado e o que falta

**Fechado estaticamente:** o ponto que chama o ponteiro em `0x020370F0`; a
invocação do callback selecionado; o comportamento de retorno que mantém a task
ativa durante o fade; e a transição da opção Bolsa para o callback
`0x08126EB0`.

**Não feito neste ciclo:** PC trace/diff dinâmico no emulador. Também não foi
seguida a navegação interna da Bolsa após a entrada em `0x08126EB0`.

**Próximo passo estreito:** seguir `0x08126EB0` até a task/rotina que processa o
input dentro da Bolsa e documentar somente como B retorna ao overworld com o
menu de pausa reaberto. Depois disso, comparar um segundo item apenas se ele
revelar um caminho de controle diferente (por exemplo, Salvar).
