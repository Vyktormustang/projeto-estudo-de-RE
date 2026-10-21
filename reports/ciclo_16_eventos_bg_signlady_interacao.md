# Ciclo 16 — eventos de fundo, interação com placas e estado da Senhora da Placa

## Resultado

Confirmei na ROM local o formato/consumidor de `BgEvent`, dois caminhos de
interação distintos e uma cadeia de estado ligando a tabela `mapScripts`, o evento
de fundo de dicas e o evento de coordenada em `(13,2)`. A amostra do mapa contém
cinco eventos de fundo, todos com tipo bruto zero, e scripts locais legíveis. Análise
estática; não houve reprodução dinâmica.

ROM-base: `google_drive/Pokemon - Fire Red (BR).gba`

SHA-256: `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.

## Consumidor local: busca de BgEvent

A função Thumb `0x0806DEEC` recebe header e posição. O disassembly local confirma:

1. `MapHeader+4` → `MapEvents`;
2. `MapEvents+0x10` → ponteiro do array de eventos de fundo e `MapEvents+3` →
   contagem;
3. percorre a contagem com stride `0x0C` (cálculo local `i * 12`);
4. compara x/y de 16 bits nos offsets `+0`/`+2` e elevação no byte `+4`, aceitando
   elevação igual ou zero;
5. retorna o endereço do registro correspondente, ou nulo.

O código consumidor usa byte `+5` como espécie/tipo e word `+8` como união/ponteiro
associado. A ROM local amostrada confirma, portanto, registros de 12 bytes com
`x, y, elevação, tipo, ... , ponteiro`; o nome de estrutura `BgEvent` e a interpretação
semântica da união são cruzamentos, enquanto os offsets e stride vieram do binário.

### Dois caminhos de uso no campo

**Interação do jogador (`0x0806CEA0` → `0x0806CEE0`):**

- O caller local `0x0806CC84` chega a `0x0806CEA0` por uma ramificação do registro
  de entrada; no contexto cruzado com `ProcessPlayerFieldInput`, é o caminho do
  botão A.
- `0x0806CEA0` obtém um script e, se não nulo, chama `ScriptContext_SetupScript`
  (`0x08069AE4`) e retorna sucesso.
- `0x0806CEE0` tenta, nesta ordem, evento de objeto (`0x0806CFF4`), evento de fundo
  (`0x0806D0E4`), comportamento do metatile (`0x0806D1F0`) e água (`0x0806D548`).
  A rotina `0x0806D0E4` busca pelo scanner `0x0806DEEC`, usa o tipo em `+5` para
  dispatch e lê o ponteiro em `+8`. Se o script do registro for nulo, segue um
  caminho de mensagem padrão; tipos específicos também têm tratamento próprio.
- A associação a objetos, BgEvents, metatile e água está demonstrada pela ordem de
  chamadas local; os nomes de “interação” e “botão A” são corroborados pelo fonte
  upstream, não incorporados como símbolos nativos da ROM.

**Caminhar contra uma placa (`0x0806D964` → `0x0806D928` → `0x0806DEEC`):**

- Há um caminho independente chamado por `0x0806CC12`. Ele consulta comportamento
  do metatile/orientação e, para o caso compatível com placa roteirizada, busca o
  BgEvent na mesma coordenada.
- `0x0806D928` devolve o ponteiro do evento ou um ponteiro de mensagem padrão quando
  o campo de script é nulo; o chamador passa pelo configurador local `0x0806D908`.
- O fonte upstream chama esse fluxo de caminhar contra uma placa. A ROM local
  comprova os testes, consulta e configuração do script; não houve teste de
  movimento em emulador neste ciclo.

## Cinco registros locais de fundo

O array do mapa amostrado está em `0x0871A668`, contagem local 5. Interpretando os
campos pelo acesso direto do consumidor, os registros são:

| Coordenada | Elevação | Tipo bruto (`+5`) | Script local |
|---|---:|---:|---:|
| `(16,16)` | `0` | `0` | `0x08165838` |
| `(4,7)` | `0` | `0` | `0x08165850` |
| `(13,7)` | `0` | `0` | `0x08165859` |
| `(9,11)` | `0` | `0` | `0x08165862` |
| `(5,14)` | `0` | `0` | `0x0816586B` |

Todos têm ponteiro de script não nulo e o tipo bruto zero. Os scripts locais fazem:

- `0x08165838`: `lockall`; zera `0x8004`/`0x8005`; `special 0x0173`; carrega texto
  `0x0817D866`, chama standard script `4`, `releaseall`, `end`.
- `0x08165850`, `0x08165859` e `0x08165862`: carregam, respectivamente, os textos
  `0x0817D87F`, `0x0817D88A` e `0x0817D895`, chamam standard script `3` e terminam.
- `0x0816586B`: `lockall`; carrega texto `0x081B1CC1`; chama standard script `4`;
  escreve var `0x4070 = 1`; `releaseall`, `end`.

Os probes do decodificador local de texto, com remapeamentos empíricos de
`notes_charset_remap_br.json`, recuperam:

- `0x0817D866`: “LAB. DE PESQUISA POKéMON”;
- `0x0817D87F`: “CASA DE {BUF}01”;
- `0x0817D88A`: “CASA DE {BUF}06”;
- `0x0817D895`: “VILA PALLET — Onde a sua jornada começa!”;
- `0x081B1CC1`: “DICAS DE INSTRUTOR — O START abre o MENU!”.

`{BUF}` e `{FB}` são marcadores de controle preservados, não texto decifrado.
Upstream associa os quatro primeiros registros a placas do laboratório/casas/placa
da cidade e o último a dicas de treinador; a ROM BR confirma coordenadas, bytes,
ponteiros e conteúdo de texto, mas não os nomes simbólicos do JSON upstream.

## Evento de coordenada `(13,2)` e cadeia de estado anterior

O terceiro registro de coordenada já identificado no ciclo 12 é `(13,2)`, elevação
3, variável `0x4002 == 1`, script `0x0816587B`. O ciclo 14 confirmou que o consumidor
compara esse valor e instala o ponteiro; agora o bytecode foi seguido:

- Em `0x0816587B`: `lockall`; aplica movimentos apontados por `0x081A75EB` ao local
  ID 1 e `0x081A75E7` ao jogador (`0xFF`); `waitmovement 0`; chama
  `0x08165894`; `releaseall`; `end`.
- Em `0x08165894`: define cores de texto brutas, carrega `0x081B1D0B`, chama
  standard script `4`, fecha a mensagem, espera 20; define flag `0x083E`; escreve
  var `0x4070 = 1` e var `0x4002 = 0`; chama specials `0x0170` e `0x0171`; ativa
  modo de mensagem de placa; carrega `0x081B1D51`, chama standard script `4`,
  desativa o modo de placa e retorna.
- Probes locais: `0x081B1D0B` → “Olha, olha! Eu copiei o que dizia em uma das
  DICAS DE TREINADOR!”; `0x081B1D51` → “DICAS DE TREINADOR! START abre o MENU!”.
  O texto local é evidência dos bytes, com controles preservados conforme o
  decodificador.

A cadeia que prepara o valor `0x4002` também é localmente rastreável. O `MapHeader`
usa tabela `mapScripts` em `0x0816545A`; conforme o ciclo 13, a tag `3` aponta para
`0x08165465`. O bytecode dessa rotina e seus auxiliares mostra:

1. em `0x08165465`, define world-map flag `0x0890`, testa flag `0x0291`, pode chamar
   `0x08165488`, compara var `0x4070` com `0` e `1` e chama `0x081654A8` ou
   `0x081654A2`; o fluxo termina em `end`;
2. `0x081654A8` testa novamente flag `0x0291`; no caminho de queda define
   coordenadas permanentes para o local ID 1 em `(5,15)` e tipo de movimento bruto
   `7`, depois retorna;
3. no ramo para `0x081654BD`, define o local ID 1 em `(12,2)`, tipo de movimento
   bruto `8`, escreve `0x4002 = 1` e retorna;
4. `0x08165488` testa flag `0x083E` e var `0x4070` antes de escrever o estado de
   cena; o código é um produtor adicional de estado que se combina com a
   ramificação de posição acima.

`0x0806B470` é o handler local do comando `0x63` (mudança permanente de coordenadas,
identificado no ciclo 11); assim, as escritas `(5,15)` e `(12,2)` não são apenas
valores de script soltos: chegam ao atualizador de posição permanente de template.
A rotina local `0x0806B628` lê local ID e tipo, e chama o serviço `0x08055114` para
o comando `0x65` de movimento.

Isso fecha o encadeamento estrutural:

```text
MapHeader.mapScripts tag 3 → 0x08165465
  → estado/flags e posição do local ID 1
  → em um ramo, var 0x4002 = 1
  → coord event local (13,2), elevation 3, condição 0x4002 == 1
  → 0x0816587B / 0x08165894
  → movimentos, texto de dicas, flag 0x083E, var 0x4070 = 1, var 0x4002 = 0
```

Os números, ramificações, ponteiros e operandos acima vêm da ROM. Upstream chama o
local ID 1 de “Sign Lady”, o evento de `PalletTown_EventScript_SignLadyTrigger`,
`0x4070` de variável de cena da placa, `0x4002` de `VAR_TEMP_2`, flag `0x083E` de
`FLAG_OPENED_START_MENU`, e os specials de `SetWalkingIntoSignVars` /
`DisableMsgBoxWalkaway`. Esses nomes explicam a intenção provável, mas são
cruzamentos, não símbolos provados na build BR.

## Evidência e reprodutibilidade

- ROM: SHA-256 registrado no início.
- Array BgEvent: `0x0871A668`, cinco registros locais.
- Scanner: `0x0806DEEC`; consumidores: `0x0806D0E4` e `0x0806D928`.
- Caller de interação: `0x0806CC84 → 0x0806CEA0 → 0x0806CEE0 → 0x0806D0E4`;
  caminho de placa ao caminhar: `0x0806CC12 → 0x0806D964 → 0x0806D928`.
- Scripts relevantes: `0x08165465`, `0x081654A8`, `0x0816586B`, `0x0816587B` e
  `0x08165894`; os handlers foram resolvidos pela tabela local de bytecodes em
  `0x0815F9B4`.
- Upstream consultado somente para cruzamento: `src/field_control_avatar.c`
  `b1b6465941133b927505be92d189a7c283e4722f`, `data/maps/PalletTown/scripts.inc`
  `1384b7d6c6bb5d2b93538ebaf5e92defde2d41e5`, `data/maps/PalletTown/map.json`
  `802d32dc6de7688fe2de8c833d4e040d9137f6c1`, `include/constants/vars.h`
  `5c7bbf8a3356606af13e744ac24de806c1b0869e` e `include/constants/flags.h`
  `d800adf1e18d1e466a16bc543f6b3c52d60fc6aa`. Checkout upstream `master` não
  fixado.

## Lacunas e próximo passo

- Todos os cinco BgEvents desta amostra têm tipo bruto zero; orientações específicas,
  eventos de item escondido e demais ramos do dispatch precisam de amostras locais
  apropriadas. Nenhum script de placa foi acionado no jogo durante esta análise.
- Warps, conexões e outras regiões/mapas ainda não foram auditados de forma
  sistemática; os ciclos 11–16 são passes iniciais por alguns caminhos de campo.
- A cobertura ampla inclui batalha, equipe/PC, dados de Pokémon, inventário, save,
  renderização, áudio, conectividade e outros domínios identificados no inventário.
  O próximo passo é revisar inventário/callgraph para escolher um desses domínios e
  manter warps/variantes de mapa como lacunas registradas, sem restringir a RE a este
  mapa ou a cutscenes.
