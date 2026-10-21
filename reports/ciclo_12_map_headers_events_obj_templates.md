# Ciclo 12 — MapHeader, eventos e templates de objeto (ROM local)

**Data:** 2026-10-21
**ROM:** `google_drive/Pokemon - Fire Red (BR).gba`
**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`
**Tamanho:** `0x01000000` bytes (16 MiB)

## Objetivo e resultado

Continuar a etapa de formatos/estruturas do roteiro, agora comprovando o caminho
local **grupo/número do mapa → MapHeader → MapEvents → templates de objeto**. A
análise cobre um mapa como amostra estrutural, não como limite do inventário. O
resultado explica o que os comandos `addobject` e `removeobject` realmente
consomem e quais dados são necessários para declarar um evento de objeto.

## Evidência local: lookup e estrutura

### Lookup do mapa

- A rotina local em `0x08055238` recebe dois índices, multiplica cada um por quatro,
  lê primeiro um ponteiro de grupo e depois o ponteiro do mapa dentro desse grupo.
  O literal usado como tabela de grupos é `0x083526A8`.
- Caminho concreto na ROM:
  - tabela `0x083526A8`, grupo `3` → vetor de mapas `0x083522F4`;
  - vetor + índice `0` → header `0x08350618`;
  - os quatro primeiros ponteiros do header são layout `0x082DD4C0`, eventos
    `0x0871A6A4`, scripts de mapa `0x0816545A` e conexões `0x0835276C`.
- O índice 3 / mapa 0 é chamado `PalletTown` no `map_groups.json` upstream
  consultado. Isso é um rótulo cruzado; o código local prova os índices e
  endereços, não o nome textual do mapa.
- Em `0x082DD4C0`, os primeiros campos lidos como largura e altura são 24 e 20;
  os campos seguintes apontam para border `0x082DD0F8`, grade `0x082DD100` e dois
  tilesets `0x082D4A94` e `0x082D4AAC`. São dados do layout, separados dos eventos.

### Caminho local usado pelo spawn de objeto

- `0x0805FD5C` procura template por local ID e par grupo/número do mapa.
- Para o mapa atual, compara os bytes de localização no bloco corrente e usa o
  conjunto de templates da área `+0x8E0` do bloco de save; a contagem vem dos
  eventos do header atual.
- Para outro mapa, chama `0x08055238`; em seguida, lê o campo `MapHeader + 4`
  (ponteiro de eventos), o ponteiro de templates em `MapEvents + 4` e a contagem
  `MapEvents + 0`.
- `0x0805FDB0` percorre a quantidade informada de registros com passo `0x18` e
  compara o primeiro byte do registro com o local ID procurado.
- `0x0805E898` usa esse lookup antes de criar a instância; se não há template,
  retorna o sentinela `0x10` sem instanciar. Se encontra, segue pelo caminho de
  criação local `0x08063C10`/`0x0805E72C`.

Essa leitura local fecha a condição que faltava no ciclo 11: `addobject` recupera
um template do mapa indicado e instancia-o; não fornece um registro novo.

## Exemplo de dados concretos no mapa local (grupo 3, mapa 0)

O `MapEvents` em `0x0871A6A4` começa com quatro contagens e quatro ponteiros:

| Tipo | Contagem | Início local |
|---|---:|---:|
| templates de objeto | 4 | `0x0871A5C0` |
| warps | 3 | `0x0871A620` |
| eventos de coordenada | 3 | `0x0871A638` |
| eventos de fundo | 5 | `0x0871A668` |

Os registros de templates têm passo local `0x18`, também usado pela rotina de
lookup. Interpretados segundo os campos do formato cruzado com upstream, os quatro
registros locais são:

| Local ID | Graphics ID bruto | X,Y | Elevação | Movimento bruto | Script local | Flag |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | `0x17` | 3,10 | 3 | `0x02` | `0x0816575C` | `0` |
| 2 | `0x1B` | 13,17 | 3 | `0x02` | `0x0816582F` | `0` |
| 3 | `0x47` | 10,8 | 3 | `0x07` | `0x00000000` | `0x002C` |
| 4 | `0x33` | 7,10 | 0 | `0x10` | `0x08800000` | `0` |

O ponteiro `0x08800000` cai dentro da ROM (offset de arquivo `0x00800000`) e há
bytes nesse local; não é um ponteiro nulo. O conteúdo/execução desse script ainda
não foi analisado.

Como exemplo de arrays vizinhos, os três eventos de coordenada contêm localmente:

- `(12,1)`, elevação 3, condição `var 0x4050 == 0`, script `0x081655ED`;
- `(13,1)`, elevação 3, condição `var 0x4050 == 0`, script `0x081655F9`;
- `(13,2)`, elevação 3, condição `var 0x4002 == 1`, script `0x0816587B`.

Os dados dão as coordenadas, valores e ponteiros. Os nomes cruzados do upstream
associam `0x4050` à variável de cena de Pallet Town e `0x4002` a `VAR_TEMP_2`;
a semântica local completa dessas condições e scripts fica para o rastreio do
sistema de scripts. Os warps e eventos de fundo também possuem arrays próprios;
a leitura integral de seus consumidores não é concluída neste ciclo.

## Nomes e layouts cruzados com upstream — não são prova local

A partir de `global.fieldmap.h` e `asm/macros/map.inc` do upstream, os formatos
correspondentes são `MapHeader`, `MapEvents`, `ObjectEventTemplate`, `WarpEvent`,
`CoordEvent` e `BgEvent`; o template normal possui local ID, graphics ID, kind,
coordenadas, elevação, movimento/faixas, dados de treinador, ponteiro de script e
flag. O `map_groups.json` associa grupo 3/mapa 0 a `PalletTown`. `event_objects.h`
associa os IDs de gráficos 23, 27, 71 e 51, respectivamente, a Woman 1, Fat Man,
Prof. Oak e GBA Kid. Esses nomes são apenas cruzamento semântico; os bytes locais
registrados na tabela anterior não dependem desses nomes.

Há uma diferença observável: o `PalletTown/map.json` upstream consultado declara
3 templates de objeto, mas a ROM local tem contagem 4 e contém o registro local ID
4 / graphics `0x33`. Não atribuo a causa (diferença de revisão, patch ou conteúdo
adicional) sem outra confirmação. O registro adicional é evidência de que os dados
da ROM BR precisam ser inventariados localmente em vez de simplesmente copiados do
upstream.

Blobs de upstream (checkout `master` sem commit fixado): `overworld.c`
`339014da46ae8543143edc99ab72bf7496203a0d`, `event_object_movement.c`
`8e82824d376d566dbff5ac863f1013d10ad5ec8b`, `global.fieldmap.h`
`e2828ec0cb1439718e830fbef4366770b3b77b1c`, `data/maps/map_groups.json`
`8c382f504d208286161903244772c93138cd7662`, `data/maps/PalletTown/map.json`
`802d32dc6de7688fe2de8c833d4e040d9137f6c1`, `asm/macros/map.inc`
`83ef472c926ce767c9133ab9bd6922280b38bb2d` e
`include/constants/event_objects.h` `9d8c514f9e2d634d40d215bf657f33041c55c28e`.

## Consequência prática para alteração de NPC

Um novo NPC estático precisa de um registro de template no array apontado por
`MapEvents.objectEvents`, além de contagem e ponteiro coerentes. O registro precisa
usar local ID não conflitante e valores válidos para graphics, coordenadas,
elevação, movimento, script e flag. Só depois o bytecode pode usar `addobject`
para instanciá-lo; para remover a instância e fazê-la reaparecer, os comandos do
ciclo 11 atuam sobre o mesmo local ID/mapa.

A estrutura local observada tem registros de template de `0x18` bytes; a cópia de
save para templates ocupa 64 posições na região `SaveBlock1 + 0x8E0` que o helper
local de `setobjectxyperm` percorre. Isso não significa que qualquer mapa possa
exibir 64 atores simultaneamente. A alocação de templates/atores ativos tem
restrições adicionais e deve ser auditada antes de uma modificação. Nenhum dado foi
alterado nesta análise; não é seguro editar o array diretamente sem tratar espaço,
ponteiros e checksums/validação da ROM.

## Reprodução local

O extrator em `scripts/inspect_map_event_graph.py` percorre a cadeia acima a partir
de uma tabela de grupos e índices informados, sem atribuir nomes upstream. A amostra
foi conferida com:

```bash
python3 scripts/inspect_map_event_graph.py \
  'google_drive/Pokemon - Fire Red (BR).gba' \
  --group-table 0x083526A8 --group 3 --map-num 0
```

A saída JSON temporária foi comparada aos endereços e campos descritos neste
relatório; `python3 -m py_compile scripts/inspect_map_event_graph.py` também passou.

## Limites e continuação

Este ciclo confirma uma cadeia estrutural local e uma amostra de mapa, mas não
cataloga os 46+ grupos nem valida dinamicamente a execução dos scripts. Próximas
passagens da etapa de dados: rastrear o parser/consumidores de scripts de mapa,
warps, eventos de coordenada e eventos de fundo; conferir outros mapas e variantes;
mapear carregadores de layouts/tilesets e depois continuar a cobertura sistemática
dos demais sistemas prevista no roteiro geral.
