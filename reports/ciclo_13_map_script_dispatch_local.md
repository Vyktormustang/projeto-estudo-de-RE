# Ciclo 13 — Dispatch local de scripts associados ao mapa

**Data:** 2026-10-21

**ROM:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Objetivo

Estender a cadeia do ciclo 12 pelo consumidor de `MapHeader.mapScripts`: confirmar
na ROM como um tipo de script é localizado, como tabelas condicionais são avaliadas
e quais caminhos executam scripts de mapa. Trata-se de um pedaço do motor de eventos;
não encerra a cobertura de scripts nem das demais regiões/sistemas do jogo.

## Evidência direta da ROM local

### Localizador da tabela de tipos

- `0x08069B80` carrega o header do mapa atual (`0x02036DFC`) e obtém o ponteiro no
offset `+8`. Se nulo ou se o primeiro byte for zero, retorna sem script.
- Compara cada byte de tipo com o argumento. Se não coincide, avança cinco bytes;
  se coincide, avança um byte e lê o ponteiro Thumb de 32 bits seguinte.
- `0x08069BC0` usa esse localizador e, se recebe ponteiro não nulo, chama o executor
  imediato `0x08069B48`. Esse executor inicializa um contexto local de script,
  instala o bytecode e chama `0x08069804` repetidamente até o executor retornar
  zero.
- `0x08069BD8` consulta tabelas condicionais: lê dois operandos de 16 bits; se o
  primeiro for zero, encerra. Caso contrário, chama o leitor local de variáveis
  (`0x0806E568`) para cada operando. Se os resultados forem iguais, devolve o
  ponteiro de script de 32 bits seguinte; se não, salta os quatro bytes do
  ponteiro e examina a próxima linha.
- A implementação local de `VarGet` em `0x0806E568` chama `0x0806E454`. Para IDs
  até `0x3FFF`, o helper retorna ponteiro nulo e `VarGet` devolve o próprio
  operando: portanto valores imediatos como `2` não são confundidos com a variável
  `0x4050`.

### Chamadores locais e tags

| Endereço local | Tag passada/consultada | Caminho observado |
|---:|---:|---|
| `0x08069C38` | `1` | procura a entrada e executa imediatamente |
| `0x08069C44` | `3` | procura a entrada e executa imediatamente |
| `0x08069C50` | `5` | procura a entrada e executa imediatamente |
| `0x08069C5C` | `7` | procura a entrada e executa imediatamente |
| `0x08069C68` | `6` | procura a entrada e executa imediatamente |
| `0x08069C74` | `2` | ignora o caminho quando um byte de estado local vale 3; busca a tabela condicional e, se obtém ponteiro, chama a configuração de script em `0x08069AE4` e retorna sucesso |
| `0x08069C9C` | `4` | busca tabela condicional; se obtém ponteiro, executa imediatamente |

A associação dos números a nomes (`ON_LOAD`, `ON_TRANSITION`, `ON_FRAME_TABLE`,
`ON_WARP_INTO_MAP_TABLE`, `ON_RESUME`, `ON_DIVE_WARP`, `ON_RETURN_TO_FIELD`) é
cruzada com `constants/map_scripts.h` upstream. O binário local comprova os números,
os dispatchers e seus caminhos; não se usa a tabela de nomes upstream como prova
de endereço local.

### Dados concretos ligados ao header local do ciclo 12

O `MapHeader` do grupo 3/mapa 0 contém `mapScripts = 0x0816545A`. Os bytes locais
da tabela são:

```text
03 65 54 16 08 | 02 CE 54 16 08 | 00
```

Lidos segundo o parser local: tag `3` aponta para `0x08165465`; tag `2` aponta para
`0x081654CE`; byte zero encerra a tabela. A tabela condicional em `0x081654CE` é:

```text
50 40 | 02 00 | D8 54 16 08 | 00 00
```

Logo, a ROM local armazena uma linha `operando 0x4050 == operando 0x0002` que leva
a `0x081654D8`, seguida pelo terminador zero. O helper local de variáveis acima
confirma que `0x4050` é buscado como variável e `0x0002` é valor imediato. Assim,
no caminho de tag 2, quando a condição bate, o handler fornece `0x081654D8` ao
setup de script não imediato.

O mapa contém ainda tags 3 e 2, não tags 1/4/5/6/7. A lista de entradas local está
alinhada ao formato observado pelo scanner; o tipo de execução é determinado pelos
chamadores, não somente pelo byte da entrada.

### Consequência para o modelo de eventos

A ROM mantém mecanismos distintos que podem iniciar scripts ligados ao mesmo mapa:

1. tags no campo `mapScripts` do header, despachadas no carregamento/transição,
   retorno, frame ou warp conforme seus consumidores;
2. eventos de coordenada, cujos registros no ciclo 12 têm suas próprias
   coordenadas, condição e ponteiro, e ainda aguardam a análise local do scanner;
3. interação com objeto, evento de fundo e outros caminhos do campo, também a
   mapear em suas respectivas rotinas consumidoras.

Portanto, encontrar um ponteiro de script no mapa não basta para saber quando ele
roda: é preciso identificar se o ponteiro vem do dispatcher de header, de uma
condição de frame/warp, de um evento de coordenada ou de interação.

## Nomes cruzados com upstream — não são prova local

O `script.c` upstream organiza os mesmos tipos de operação como busca de script de
header, execução imediata, checagem de tabelas condicionais e setup da execução por
frame. Em `data/maps/PalletTown/scripts.inc`, o mapa cruza a tag 3 com a rotina de
transição e a tag 2 com um `map_script_2` condicionado pela cena. Isso é útil para
atribuir nomes e propósito provável aos ponteiros locais, mas a evidência das
chamadas, tags, bytes e endereços acima foi obtida da ROM BR.

Blobs consultados no checkout upstream `master` não fixado: `src/script.c`
`d0433bdda062b138e53d1a1d3184b4566ad7d9dc`, `data/maps/PalletTown/scripts.inc`
`1384b7d6c6bb5d2b93538ebaf5e92defde2d41e5` e `include/constants/map_scripts.h`
`1353de360cf1e00b6efbb26ec59c4822c99b59bf`.

## Reprodutibilidade e limites

O extrator `scripts/inspect_map_event_graph.py` foi estendido para listar as
entradas de `mapScripts` e decodificar linhas condicionais para tags 2 e 4. A
amostra do grupo 3/mapa 0 retorna tags 3 e 2, e a linha `0x4050`, `2`,
`0x081654D8`. Não executei o script no emulador nem provoquei a condição em jogo.

Próximo recorte: localizar e confirmar localmente o consumidor dos eventos de
coordenada (inclusive ordem de precedência e ajuste entre coordenadas do jogador e
do mapa), então seguir os demais dispatchers de interação/warp/fundo. Em paralelo,
o inventário global ainda precisa ser auditado para cobrir todos os outros módulos
da ROM; esta amostra não fecha a etapa nem limita o escopo total.
