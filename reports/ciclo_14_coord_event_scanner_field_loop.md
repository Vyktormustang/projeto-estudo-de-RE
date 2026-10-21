# Ciclo 14 — consumidor local de eventos de coordenada e loop de campo

## Escopo e resultado

Localizar, na ROM BR, o scanner de `coordEvents`, a lógica de condição/execução e a
ligação ao processamento de campo. Resultado: o caminho principal foi confirmado por
bytes e chamadas locais. Também foi separado um segundo consumidor, específico do
acionamento de botão de força por pedregulho. Trabalho estático; não houve breakpoint
nem validação dinâmica.

ROM-base: `google_drive/Pokemon - Fire Red (BR).gba`

SHA-256: `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.

## Evidência local: percurso principal após movimento do jogador

### Entrada no processamento de campo

- A função que começa em `0x0806CAC8` constrói/consulta estado de campo e contém o
  callsite `0x0806CB58 → 0x0806D5E8`. O corpo local mostra que a chamada ocorre no
  caminho condicionado por flags do registro de entrada, antes de continuar para
  outros tratamentos do input.
- A rotina `0x0806D5E8` recebe a posição/estado e chama `0x0806D660` em
  `0x0806D5F2`. Se este indicar script iniciado, retorna sucesso; caso contrário,
  tenta as rotinas seguintes (`0x0806DA10`, `0x0806D694`, `0x0806D698` e posteriores).
- `0x0806D660` obtém x e y do objeto/posição, subtrai `7` de ambos, lê elevação e
  chama `0x0806DDC0` com o header global local (`gMapHeader`, literal apontado em
  `0x0806D684`). Se a busca devolver ponteiro não nulo, chama
  `ScriptContext_SetupScript` local `0x08069AE4` e retorna verdadeiro.

### Busca na tabela de eventos de coordenada

`0x0806DDC0` recebe `(MapHeader*, x, y, elevation)` e, conforme as instruções Thumb
locais:

1. carrega `MapHeader.events` por `+4`;
2. carrega `coordEvents` por `MapEvents+0x0C` e a contagem por `MapEvents+2`;
3. percorre a contagem, avançando `0x10` bytes por registro;
4. compara x e y de 16 bits nos offsets `+0` e `+2`;
5. compara elevação no byte `+4`, aceitando igualdade ou elevação zero;
6. para coordenadas/elevação candidatas chama `0x0806DD80`; se esta retornar
   ponteiro não nulo, devolve esse script ao chamador; se não, continua a busca.

A assinatura confere com o array já localizado no ciclo 12: os registros de evento de
coordenada são de `0x10` bytes, com x/y/elevação à frente e script no offset `+0x0C`.
Isso agora tem evidência adicional no consumidor, não apenas na tabela de dados.

### Condição e execução

`0x0806DD80` recebe um registro de evento:

- verifica o ponteiro de script em `+0x0C`;
- se o ponteiro for nulo, obtém o byte de trigger em `+6` e chama
  `0x0806E7DC`, retornando nulo;
- se trigger (`u16` em `+6`) não for zero, chama `VarGet` local `0x0806E568`,
  compara o resultado com o byte em `+8` e só retorna o ponteiro de script quando
  iguais;
- se trigger for zero, passa o ponteiro imediatamente a `RunScriptImmediately`
  local `0x08069B48` e retorna nulo. A busca continua; esse caso não é o caminho que
  devolve o script ao `SetupScript` de `0x0806D660`.

Assim, há dois resultados distintos: script de condição satisfeita é devolvido para
`ScriptContext_SetupScript`; script sem variável é iniciado imediatamente pelo
executor. Um script nulo toma um caminho especial de tratamento meteorológico. Os
nomes semânticos desse tratamento foram cruzados com upstream; endereços e fluxo acima
foram lidos na ROM local.

## Segunda rota local: pedregulho sobre botão de força

Não confundir com a busca por posição do jogador acima:

- `0x0805CE20` contém o fluxo de movimento de outro object event; após
  `0x0806DE28`, chama `0x0806DE70` em `0x0805CE54` com x/y atuais.
- `0x0806DE70` lê `gMapHeader.events->coordEvents` e a contagem, testa o
  comportamento do metatile contra `0x20`, compara coordenadas do evento deslocadas
  por `7` com as coordenadas recebidas e, para os matches, chama
  `ScriptContext_SetupScript` com o script do evento e ativa o controle de campo
  bloqueado.
- Upstream identifica essa rotina como o tratamento de ativação do botão de força
  da Victory Road por pedregulho (`HandleBoulderActivateVictoryRoadSwitch`). Essa
  identificação é cruzamento semântico; a comparação local de metatile e o caminho
  para execução do script estão confirmados na ROM.

## Cruzamento semântico upstream (não é prova local)

O checkout de referência `/tmp/pokefirered-src`, `src/field_control_avatar.c`
(blob SHA-1 `b1b6465941133b927505be92d189a7c283e4722f`; branch upstream `master`, sem
commit fixado neste trabalho), associa as rotinas estruturais a `ProcessPlayerFieldInput`,
`TryStartStepBasedScript`, `TryStartCoordEventScript`,
`GetCoordEventScriptAtPosition` e `TryRunCoordEventScript`. A ordem upstream de
`TryStartStepBasedScript` põe eventos de coordenada antes de warp, scripts diversos,
contadores de passos e repel. A ROM local confirma a prioridade estrutural: a rotina
`0x0806D5E8` chama primeiro `0x0806D660` e só então as demais rotinas. Os nomes exatos,
macros e comentários são referência cruzada; não são tratados como símbolos nativos
ou como evidência da build BR.

## Aplicação ao mapa amostrado no ciclo 12

Os três registros locais previamente extraídos para grupo 3/mapa 0 podem agora ser
lidos através do percurso comprovado: `(12,1)` e `(13,1)`, elevação 3, trigger
`0x4050`, índice `0`; `(13,2)`, trigger `0x4002`, índice `1`. O consumidor local
confirma que são comparados com a posição ajustada em `-7`, aceitam elevação igual ou
zero e, quando trigger não é zero, consultam a variável e comparam com o índice. Os
ponteiros de script continuam sendo os bytes locais já registrados no relatório do
ciclo 12; nenhum script foi executado dinamicamente neste ciclo.

## Rastro reproduzível / evidência

- ROM e endereços Thumb em `0x0806CAC8–0x0806DF34`.
- Callsite input → rotina de passos: `0x0806CB58 → 0x0806D5E8`.
- Callsite rotina de passos → início de coord event: `0x0806D5F2 → 0x0806D660`.
- Busca e decisão: `0x0806DDC0 → 0x0806DD80 → 0x0806E568` ou
  `0x08069B48`; script devolvido é entregue a `0x08069AE4`.
- Rota do pedregulho: `0x0805CE54 → 0x0806DE70`.
- A lista local de callsites usada para confirmação está em
  `reports/pokemon_firered_bpre_trabalho_callsites.tsv`.

## Limites e lacunas seguintes

- Não houve execução instrumentada, breakpoint ou traço de PC; não declarar teste em
  hardware nem validar por gameplay.
- O conteúdo dos scripts apontados pelos eventos locais ainda deve ser decodificado e
  acompanhado por comandos/alterações de estado.
- A tabela local de coord events do exemplo tem três registros; a descoberta deste
  consumidor não resolve a diferença prévia entre quatro templates locais e três
  object events no JSON upstream.
- A cobertura ampla continua aberta: warps e bg events ainda precisam de rastros
  locais; outros mapas e formatos também. Próximo passo eficiente: seguir um registro
  de coordenada do mapa amostrado através do bytecode até os efeitos sobre NPC,
  flags/vars e controle de campo, sem deixar de avançar na auditoria global.
