# Ciclo 05 — montagem, ordem e desenho do menu nativo de pausa

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Resultado

Fechei a construção da lista nativa antes do input já documentado nos ciclos
02–04. A ROM seleciona uma das listas de IDs conforme o contexto, grava a ordem
em RAM e usa o mesmo registro de ação para obter o texto ao desenhar e o callback
ao confirmar um item.

```text
0x0806F01C (máquina de estados de desenho)
  → 0x0806ED54 (seleciona modo/contexto)
  → monta sStartMenuOrder + sNumStartMenuItems
  → cria janela usando a contagem
  → desenha os IDs em ordem, consultando 0x083A7344
  → inicializa cursor sobre essa ordem
  → 0x0806F280 usa cursor + ordem para buscar callback no mesmo registro
```

## Dados locais observados

- Cursor: `0x020370F4`.
- Contagem de itens: `0x020370F5`.
- Ordem: começa em `0x020370F6`; os endereços até `0x020370FE` acomodam nove
  bytes. O estado de desenho começa em `0x020370FF`.
- Registro de ação: `0x083A7344`, stride de 8 bytes; word `+0` é ponteiro de
  texto e word `+4` é ponteiro Thumb de callback. A entrada de Bolsa já
  confirmada é ID 2, texto em `0x0871A2E7` e callback `0x0806F481`.

Valores de callback locais observados nos nove registros:

| ID | Callback Thumb | Nome lógico cruzado com upstream |
|---:|---:|---|
| 0 | `0x0806F411` | Pokédex |
| 1 | `0x0806F44D` | Pokémon |
| 2 | `0x0806F481` | Bolsa |
| 3 | `0x0806F4B5` | Jogador |
| 4 | `0x0806F4E9` | Salvar |
| 5 | `0x0806F4FD` | Opções |
| 6 | `0x0806F541` | Sair |
| 7 | `0x0806F555` | Retirar-se da Safari Zone |
| 8 | `0x0806F56D` | Jogador em contexto de Link |

Os ponteiros e o stride vêm da ROM. Os nomes da última coluna são apenas o
cruzamento com `StartMenuOption`/`sStartMenuActionTable` do fonte upstream.

## Construção da ordem

`0x0806ED54` zera a contagem e seleciona o builder conforme o estado de Link,
Union Room, Safari Zone ou campo normal. O caminho do campo normal está em
`0x0806EDB0`: consulta as flags `0x829` e `0x828` e, se ativas, acrescenta
respectivamente os IDs 0 e 1; em seguida acrescenta sempre `2, 3, 4, 5, 6`.

Os builders locais dos outros contextos acrescentam:

- Safari Zone: `7, 0, 1, 2, 3, 5, 6`;
- Link: `1, 2, 8, 5, 6`;
- Union Room: `1, 2, 3, 5, 6`.

O helper `0x0806ED94` encaminha o buffer, o ponteiro de contagem e o novo ID a
`0x0806FEC8`. O helper local grava o ID na posição atual e incrementa a
contagem; não há verificação de capacidade nesse trecho.

## Desenho e sincronização com input

`0x0806F01C` despacha seis estados via tabela local a partir de `0x0806F040`:

1. inicializa o desenho;
2. chama `0x0806ED54` para montar a lista;
3. carrega o frame e cria a janela com a contagem atual;
4. desenha estatísticas adicionais se o contexto Safari pedir;
5. chama `0x0806EF44` para imprimir até duas linhas por passo;
6. inicializa o cursor e termina o desenho.

A rotina de impressão `0x0806EF44` lê os IDs de `0x020370F6` e consulta
`0x083A7344` para obter os textos. Os IDs 3 e 8 recebem formatação especial de
nome do jogador. O handler de input `0x0806F280`, documentado no ciclo 02,
consulta o mesmo buffer de ordem e o registro de ações para selecionar o
callback. Logo, a posição visual do item e o callback escolhido são ligados
pelo ID que está no buffer, não por uma segunda ordem implícita.

## Implicação para mudanças futuras

A ordem e a tabela têm papéis diferentes: acrescentar um ID à ordem decide onde
o item aparece, enquanto o registro indexado pelo ID determina texto e ação.
O buffer observado comporta nove IDs, e o helper de append não valida o limite;
uma extensão precisa manter contagem, buffer, registro de texto/callback e
cursor coerentes. Não concluí que a ROM tenha espaço para um décimo ID: isso
exigiria expandir ou reaproveitar um ID de forma deliberada. Nenhuma ROM foi
alterada neste ciclo.

## Cruzamento upstream e limites

O fonte `pret/pokefirered/src/start_menu.c`, blob
`88cc377cea556d3663aa5ea5f5bd4537cb29ea72`, fornece os nomes convencionais e
confirma as listas condicionais. O binário local fornece os endereços, os
valores da tabela, o uso dos buffers e a ausência de checagem de capacidade no
helper observado. Os nomes C não são símbolos extraídos da ROM.

## Fechamento

**Fechado:** seleção do builder por contexto, ordem normal/Safari/Link/Union
Room, dados RAM, tabela de texto/callback e ligação entre renderização e input.
**Não feito:** patch de menu ou PC trace. A análise do menu nativo agora cobre
entrada, seleção de Bolsa, retorno por B e construção/desenho da lista.
