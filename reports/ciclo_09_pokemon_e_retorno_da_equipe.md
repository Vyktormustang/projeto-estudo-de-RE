# Ciclo 09 — Pokémon e retorno do menu da equipe

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**SHA-256:** `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`

## Resultado

A ação **Pokémon** inicia o menu de equipe por callback2, não como janela dentro
da task da pausa. O menu da equipe recebe A para escolher e B para cancelar;
no caminho padrão de cancelamento, a task da equipe fecha seus recursos, espera
sua etapa de saída e restaura o callback Thumb `0x080568A9`. Esse é o mesmo
retorno ao campo com pausa aberta já visto nos ciclos 04 e 07. O mGBA confirmou
visualmente a tela de equipe e, após B, a pausa reaberta.

```text
ID 0 / registro 0x083A7344 → callback Thumb 0x0806F411 (código 0x0806F410)
  → aguarda fade; prepara a transição e instala callback2 0x0810275D
  → callback de entrada 0x0810275C configura menu de equipe
  → instala callback2 de execução 0x081024D5
  → task de interação em 0x0810287D (código 0x0810287C)
  → B: testa bit 0x0002 em newKeys; grava estado de saída 1 em +1
  → estado 1 fecha recursos e encerra task; instala callback2 0x08102859
  → callback de saída aguarda a etapa de fade e instala 0x080568A9
  → retorno ao campo e reconstrução da pausa
```

## Evidência local da ROM

- O registro de ação ID 0 em `0x083A7344` contém `0x0806F411`. No código
  `0x0806F410`, enquanto o fade está ativo, a rotina retorna 0. No caminho sem
  fade, executa chamadas locais `0x08054E90(0x29)`, `0x0807B004`, `0x0806EF18`
  e `0x080563F0`, instala `0x0810275D` via `SetMainCallback2` (`0x08000544`)
  e retorna 1 para encerrar a task da pausa.
- `0x0810275C` chama a inicialização local `0x0810250C`, configura os registradores
  de vídeo, instala callback2 `0x081024D5` e define o contexto de ajuda com
  argumento 4. O endereço instalado tem bit Thumb 1; o código começa em
  `0x081024D4`.
- A task criada durante a inicialização usa o callback Thumb `0x0810287D`, cujo
  código começa em `0x0810287C`. Seu dispatcher usa o estado byte `+1` da
  estrutura de menu. Na rotina de input, `0x08102A2A` lê as teclas novas de
  `gMain+0x2E`; o teste de B usa a máscara `0x0002` em `0x08102B14`. Se ativo,
  o código grava o estado 1 em `+1` (`0x08102B1E–0x08102B22`).
- A tabela de estados local encaminha estado 1 para `0x081028FC`. Essa rotina
  limpa os recursos do menu, carrega `0x08102859` do literal em `0x0810292C`,
  instala-o com `SetMainCallback2` e destrói a task via `0x08077508`.
- O callback de saída começa em `0x08102858`. Ele consulta
  `0x08102798`; enquanto o resultado for zero, retorna sem trocar callback2.
  Quando a condição se completa, carrega `0x080568A9` do literal em
  `0x08102878` e o instala por `0x08000544`. O callback então segue a rota de
  retorno ao campo com pausa documentada no ciclo 04. Essa identificação de
  etapa de espera/fade é consistente com as instruções locais e com a tela
  observada; não foi obtido PC trace dinâmico.

O caminho documentado é o cancelamento B no contexto normal de campo. Selecionar
um Pokémon com A pode abrir o submenu de ações ou executar uma ação de campo e
não foi coberto neste ciclo.

## Validação visual no mGBA

Usei `scripts/gba_libretro_emu.py`, mGBA 0.10.5, e
`google_drive/viridian_masterball.state`, sem `--save-file`. Sequência: START,
A para abrir Pokémon, B para cancelar. A primeira captura mostra a equipe com a
mensagem de seleção/cancelamento; a segunda mostra o menu de pausa reaberto.

- `reports/ciclo_09_pokemon_party_aberto.png` — menu de equipe aberto.
- `reports/ciclo_09_b_volta_pausa_pokemon.png` — retorno à pausa após B.

A ROM-base manteve o SHA-256 registrado. Validação visual apenas; sem PC trace,
breakpoints ou teste em hardware real.

## Cruzamento com upstream — nomes, não prova local

Os nomes correspondentes em `pret/pokefirered` são `StartMenuPokemonCallback`
em `start_menu.c`, blob `88cc377cea556d3663aa5ea5f5bd4537cb29ea72`,
`CB2_PartyMenuFromStartMenu`, `InitPartyMenu` e `Task_HandleChooseMonInput` em
`party_menu.c`, blob `7f3a881e6c56773aee03da475c9a1adc50530223`, e
`CB2_ReturnToFieldWithOpenMenu` em `overworld.c`, blob
`339014da46ae8543143edc99ab72bf7496203a0d`. Os arquivos vêm de `master`, sem
commit fixado; nomes são cruzamento semântico. Endereços, máscaras, stores,
branches e callback literal foram conferidos na ROM local.
