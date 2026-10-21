# Ciclo 11 — Script commands e ciclo de vida de NPCs (base local)

**Data:** 2026-10-21

**ROM:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Escopo e resultado

Este é o primeiro ciclo fora do menu de pausa. A tabela local de comandos de
script foi identificada por seus ponteiros no inicializador; entradas de remover,
adicionar, mover e ocultar/mostrar NPCs foram ligadas a handlers locais. A
conclusão prática mais importante: `addobject` não cria um template novo — ele
procura um template existente para aquele local ID no mapa e tenta instanciá-lo.
A parte de como inserir um template novo no banco de eventos do mapa fica para o
próximo ciclo.

## Evidência direta da ROM local

### Tabela de comandos e inicialização

- Em `0x08069A80`, os três literais carregados são: contexto `0x03000EB0`, início
  de tabela `0x0815F9B4` e limite `0x0815FD08`. A função passa esses valores a
  `0x080697AC`. A extensão entre início e limite é `0x354` bytes, ou 213 entradas
  de 4 bytes; `0x0815FD08` é a entrada sentinela fora do intervalo executável.
- Os ponteiros nos índices 0x53–0x59 e 0x63 da tabela apontam para código Thumb
  local. A separação por opcodes que o upstream dá a esses índices bate com o
  comportamento observado nos respectivos handlers locais, abaixo.

| Opcode | Ponteiro Thumb na tabela | Código local | Efeito observado na ROM |
|---:|---:|---:|---|
| `0x53` | `0x0806B359` | `0x0806B358` | Lê um local ID por `0x080698F8`/`0x0806E568`, obtém dois bytes de mapa do contexto em `0x03005008` e chama `0x0805E4C8`. |
| `0x54` | `0x0806B381` | `0x0806B380` | Lê local ID e dois bytes seguintes do bytecode; chama `0x0805E4C8` com os três valores. |
| `0x55` | `0x0806B3B1` | `0x0806B3B0` | Lê local ID e mapa atual do contexto; chama `0x0805E898`. |
| `0x56` | `0x0806B3D9` | `0x0806B3D8` | Lê local ID e dois bytes de mapa do bytecode; chama `0x0805E898`. |
| `0x57` | `0x0806B409` | `0x0806B408` | Handler de mudança de coordenadas runtime (cross-check do nome em upstream). |
| `0x58` | `0x0806B4F1` | `0x0806B4F0` | Lê local ID e bytes de mapa; chama `0x0805F314` com flag 0. |
| `0x59` | `0x0806B521` | `0x0806B520` | Lê local ID e bytes de mapa; chama `0x0805F314` com flag 1. |
| `0x63` | `0x0806B471` | `0x0806B470` | Lê local ID e coordenadas; chama `0x080550D8`. |

- `0x0805E4C8` resolve o objeto pelos três campos recebidos; se há instância,
  executa a sequência local de remoção/limpeza. Portanto, `0x53` e `0x54` chegam
  ao mesmo serviço, variando apenas de onde vêm os bytes de mapa.
- `0x0805E898` chama primeiro `0x0805FD5C` com o local ID e o par de mapa. Se a
  procura não encontra registro, retorna antes da etapa de criação; se encontra,
  continua por `0x08063C10` e `0x0805E72C`. Isso sustenta localmente que `addobject`
  reusa um template local existente — não fornece gráficos nem cria um template
  arbitrário por si só.
- `0x080550D8` percorre 64 registros de stride `0x18`, começando no ponteiro
  carregado do global e deslocado por `0x8E0`. Quando o primeiro byte do registro
  corresponde ao local ID, grava as coordenadas nos halfwords `+4` e `+6`. Esse
  caminho é distinto da mudança runtime do handler `0x57`: é a atualização da
  posição-template usada por `0x63`.
- Os handlers `0x58` e `0x59` diferem por uma flag 0/1 passada aos helpers locais;
  o nome upstream indica mostrar/ocultar, mas o nome sozinho não é evidência do
  binário. O caminho não remove o registro via `0x0805E4C8`.

### Receita segura que já dá para inferir

- **Remover temporariamente:** usar opcode 0x53 com local ID resolvido como
  variável; o comando atua no mapa atual. A variante 0x54 aceita os bytes do mapa
  explicitamente.
- **Reaparecer NPC previsto no mapa:** usar opcode 0x55 para mapa atual ou 0x56
  para mapa explícito, mas somente depois de assegurar que o mesmo local ID tem
  template de evento no mapa. A chamada local de spawn faz lookup antes de criar.
- **Mover persistentemente o template:** opcode 0x63 (local ID, X, Y) chega ao
  atualizador de coordenadas-template em `0x080550D8`; o comando 0x57 é outro
  handler e segue o caminho runtime.
- **Adicionar um NPC realmente novo:** ainda falta localizar/editar o registro
  `ObjectEventTemplate` no conjunto de eventos e ligar local ID, gráficos,
  movimento e script. Não se deve dizer que `addobject` sozinho faz isso.

## Nomes e exemplos cruzados com upstream — não tratados como prova local

No `pret/pokefirered` consultado, os opcodes correspondem a `removeobject`,
`removeobjectat`, `addobject`, `addobjectat`, `setobjectxy`, `showobjectat`,
`hideobjectat` e `setobjectxyperm`. A separação entre objeto runtime e template
persistente aparece em `event_object_movement.c` e `global.fieldmap.h`.

Como padrão de cena no upstream, `data/maps/PalletTown/scripts.inc` posiciona
Oak por `setobjectxyperm` e o instancia por `addobject`; mais tarde usa
`removeobject`. `PalletTown_ProfessorOaksLab/scripts.inc` usa o mesmo padrão para
Oak/Rival e os itens-objeto dos iniciais. São exemplos úteis de fluxo, mas ainda
não foram vinculados aos bytes/eventos da ROM local neste ciclo.

Blobs consultados, todos de `master` sem commit fixado: `scrcmd.c`
`97b695ee2f6fca80a3b78f52f6a444f696fe5814`, `event_object_movement.c`
`8e82824d376d566dbff5ac863f1013d10ad5ec8b`, `script.c`
`d0433bdda062b138e53d1a1d3184b4566ad7d9dc`, `data/script_cmd_table.inc`
`c5d112d9ea66d258d5a372dda89b9ad96ed2b1e1` e `global.fieldmap.h`
`e2828ec0cb1439718e830fbef4366770b3b77b1c`. As atribuições semânticas são
referência upstream; os endereços e chamadas da seção anterior vieram do
binário local.

## Limites e próximo passo

Análise estática apenas; nenhum script de NPC foi executado dinamicamente neste
ciclo. Próximo passo: mapear localmente `MapHeader → MapEvents → ObjectEventTemplate`
e os scripts associados. Um rastro de cutscene ou de NPC pode servir como teste
ponta a ponta desse modelo, mas é somente uma amostra: a investigação continua pelos
demais sistemas e regiões da ROM, conforme o roteiro de cobertura total.
