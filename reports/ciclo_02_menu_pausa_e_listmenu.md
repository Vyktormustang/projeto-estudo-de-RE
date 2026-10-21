# Ciclo 02 — processamento do menu de pausa e distinção do `ListMenu`

**Data:** 2026-10-21

**ROM:** `google_drive/Pokemon - Fire Red (BR).gba` — SHA-256
`6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`, igual ao
inventário e ao Ciclo 01.

## Resultado principal

O caminho de entrada do menu nativo de pausa observado nesta ROM **não chama**
`ListMenu_ProcessInput` (`0x08107078`). O handler de pausa lê os bits de input
diretamente, navega pelo buffer de itens ordenados e consulta a tabela de ações.
O caminho ListMenu abaixo é outro fluxo encontrado na ROM; não há evidência que
o conecte à lista do menu de pausa.

## Handler do menu de pausa

### Navegação e confirmação

No handler `0x0806F280`:

- Lê `gMain + 0x2E` (`gMain` em `0x030030F0`) para obter os novos botões.
- Trata `0x40` e `0x80` nos ramos de navegação vertical, e testa `0x000A`
  (B/START) para o caminho de fechamento.
- Na confirmação A (`0x0001`), chama `0x080722CC(5)` e `0x0806F3CC` antes de
  aceitar a opção.
- Obtém o índice de cursor do byte `0x020370F4`; usa esse índice no buffer que
  começa em `0x020370F6` para recuperar o ID do item que está sendo exibido.
- Calcula `0x083A7344 + itemId * 8 + 4`, carrega o callback daquela entrada e
  grava o ponteiro em `0x020370F0`. Em seguida chama `0x0806F394`, que compara
  esse callback com callbacks especiais e faz tratamento adicional.

A tabela `0x083A7344` tem entradas de 8 bytes (ponteiro de texto + ponteiro de
callback) e inclui, entre outros, os callbacks nativos de Pokédex, Pokémon,
Bolsa, Treinador, Salvar, Opções e Sair já registrados em
`reports/mod_menu_any_item_spec.md`.

No ramo B/START, o código chama `0x0806EF18`, `0x080F7998` e `0x0806FEA0`.
Esses endereços são as chamadas observadas no fechamento; seus nomes semânticos
não foram inferidos aqui.

### Preparação/estado do menu

`0x0806F01C` é um dispatcher com seis estados (0–5), guardados no byte apontado
pelo literal em `0x0806F038`. O ramo em `0x0806F0A4` chama `0x0806EF44`, a rotina
que imprime as opções a partir da tabela. `0x0806F14C` zera dois bytes de estado
e repete o dispatcher até ele indicar conclusão.

No ramo em `0x0806F5E4`, o fluxo chama `0x0806F14C` e depois grava o ponteiro
Thumb `0x0806F281` em `0x020370F0` (`0x0806F280` é o endereço de código). Isso
liga a preparação do menu ao handler de navegação acima. A chamada indireta que
consome esse ponteiro em cada frame ainda não foi localizada; por isso o elo
completo de despacho de frame não é declarado fechado.

## `ListMenu`: fluxo separado observado

### API e retorno do processamento

`ListMenu_ProcessInput`, em `0x08107078`, recebe o ID da task da lista e recupera
o registro em `gTasks` (`0x03005090`, stride `0x28`). A partir de `gMain + 0x2E`:

- A (`0x0001`) retorna o ID do item sob o cursor;
- B (`0x0002`) retorna `-2`;
- nenhum item escolhido retorna `-1`;
- direções usam os bits mantidos em `gMain + 0x30` e a configuração de
  navegação guardada na estrutura da lista.

`ListMenuInit` (`0x08106FF8`) chama a inicialização interna em `0x08107348`.
Ela cria uma task com callback `0x08106ECC` e prioridade 0, copia o template e
inicializa os campos do menu no registro da task. O chamador recebe o ID dessa
task para processá-la.

### Exemplo de chamador — sem atribuir contexto indevido

A rotina em `0x08046AB8` cria uma janela a partir do template
`0x0825F7F4`, copia o template ListMenu em `0x0825F814` e chama
`ListMenuInit` em `0x08046AE4`. Em seguida cria uma task com callback
`0x080469FC` (ponteiro Thumb `0x080469FD`), prioridade 3, e grava o ID da task
ListMenu em `task.data[0]` (`+8`) e o ID da janela em `task.data[1]` (`+0xA`).

Esse callback chama `ListMenu_ProcessInput` em `0x08046A10`, destrói a task da
lista via `0x0810713C` e encerra a task proprietária via `0x08077508`. O array
referenciado pelo template, em `0x0825F7FC`, contém três linhas com IDs `0`, `1`
e `5`. É um fluxo concreto de ListMenu, mas a finalidade específica da tela não
foi confirmada e **não há elo encontrado com o menu de pausa**.

## Fatos, inferências e lacunas

**Confirmado estaticamente:**

- O handler de pausa `0x0806F280` acessa diretamente os botões e a tabela de
  ações; ele não chama `0x08107078`.
- Cursor, buffer de ordem e ponteiro de callback envolvidos nesse handler estão
  em `0x020370F4`, `0x020370F6` e `0x020370F0`, respectivamente.
- Há outro fluxo que chama `ListMenuInit` e `ListMenu_ProcessInput`; ele usa um
  template de três linhas com IDs `0, 1, 5`.

**Ainda não provado:**

- Qual ponto de despacho por frame chama o ponteiro instalado em `0x020370F0`.
- Onde e como o callback selecionado em `0x020370F0` é efetivamente invocado
  após `0x0806F394`.
- O contexto de tela específico do ListMenu de três linhas em `0x08046AB8`.
- A validação dinâmica/PC trace do handler de pausa nesta ROM.

## Próximo passo

Seguir o despacho indireto que chama `0x0806F280` e fechar um único caminho de
seleção (por exemplo, `Bolsa`): desde o item selecionado, passando pelo callback
armazenado, até o callback de ação. Depois, validar esse trajeto com trace de PC
no emulador, se o ambiente atual permitir.

## Aditivo — fechamento no ciclo 03

O ponto de despacho e a execução do callback foram fechados estaticamente no
`reports/ciclo_03_menu_pausa_ate_bolsa.md`: `0x0806F1F0` chama o ponteiro em
`0x020370F0` por `0x081E3BA8`; para a opção Bolsa, o callback `0x0806F481`
instala `0x08126EB0` via `SetMainCallback2` e retorna sucesso. A validação
pendente é dinâmica, não mais a localização estática do caminho.
