# Ciclo 15 — rastro local de um evento de coordenada até uma cena com NPC

## Resultado e limites

Foi seguido um dos eventos de coordenada do mapa do ciclo 12 desde o registro até o
bytecode, as rotinas de comando e as mudanças de estado/atores. A ROM local contém
uma cena de campo que, conforme o lado de entrada, inicia diálogo, instancia um
object event, move jogador e NPC, altera variáveis/flags e prepara uma transição de
mapa. A análise é estática; não houve execução instrumentada nem validação por
jogabilidade.

ROM-base: `google_drive/Pokemon - Fire Red (BR).gba`

SHA-256: `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.

## Nó de entrada: dados locais de evento → script

No `MapEvents` local em `0x0871A6A4`, o ciclo 12 leu três registros de coordenada. Os
dois usados neste rastro são:

| Posição do mapa | Elevação | Gatilho/índice | Script local |
|---|---:|---|---:|
| `(12,1)` | `3` | `0x4050 == 0` | `0x081655ED` |
| `(13,1)` | `3` | `0x4050 == 0` | `0x081655F9` |

O ciclo 14 confirmou que o consumidor local compara posição/elevação, chama `VarGet`
para gatilhos não nulos e instala o ponteiro devolvido com `ScriptContext_SetupScript`.
Assim, a relação entre esses dois registros e os dois inícios de bytecode abaixo não é
inferida do upstream: os ponteiros estão nos dados da ROM e o scanner local foi
confirmado.

### Entradas de bytecode conferidas na ROM

```text
0x081655ED: 69 | 16 01 40 00 00 | 05 05 56 16 08 | 02
0x081655F9: 69 | 16 01 40 01 00 | 05 05 56 16 08 | 02
```

Leitura dos campos, usando os handlers da tabela local de comandos (`0x0815F9B4`):

1. `0x69` chama o handler local `0x0806B6DC` (cruzado com o comando `lockall`);
2. `0x16` chama `0x0806A390`, que lê dois halfwords, resolve o primeiro por
   `0x0806E454` e grava o segundo: os dados locais são var `0x4001` = `0` na
   entrada `0x081655ED` e var `0x4001` = `1` na entrada `0x081655F9`;
3. `0x05` chama `0x08069FB0`, consome o ponteiro imediato e muda o cursor do
   contexto: ambos saltam para `0x08165605`;
4. `0x02` é o terminador que segue o salto no fluxo linear.

O valor `0x4001` aqui é operando de **setvar**. Mais adiante o mesmo valor numérico
aparece em um comando **setflag**; variável e flag são namespaces diferentes e não
devem ser confundidos.

## Script comum `0x08165605`: efeitos locais

O fluxo principal permanece contíguo até `0x081656B7` (`end`). Os bytes e handlers
locais suportam o seguinte resumo (operandos numéricos são os observados na ROM):

1. Define `0x8004 = 0` e `0x8005 = 2`; executa o comando `special` com ID `0x0174`;
   define text color bruto `0`; espera 30; inicia BGM `0x012E`.
2. Carrega mensagem `0x0817D72C`, executa o standard script `4` e fecha a mensagem;
   espera 85; aplica movimentos ao local ID `0x00FF` (jogador), espera o movimento,
   toca SE `0x0015`, aplica outro movimento ao jogador, espera e aguarda mais 30.
3. Executa `addobject` para local ID `3`. O handler local `0x0806B3B0` lê o
   operando, passa-o por `VarGet` e chama `0x0805E898`; os ciclos 11–12 confirmaram
   que esse serviço procura um template de evento existente antes de instanciar.
   O template local ID 3 já inventariado em `0x0871A5F0` tem graphics bruto `0x47`,
   coordenadas `(10,8)`, elevação `3` e flag `0x002C`.
4. Compara var `0x4001` com `0` e `1`; as instruções condicionais (`0x21` + `0x07`)
   selecionam uma de duas rotinas curtas de movimento do NPC:
   - valor `0`: alvo `0x081656B8`, que aplica ao local ID 3 o fluxo em `0x081656F2`;
   - valor `1`: alvo `0x081656C3`, que aplica ao local ID 3 o fluxo em `0x081656FB`.
5. Carrega a mensagem em `0x0817D74A`, chama novamente o standard script `4`, fecha
   a caixa e aguarda. Mais dois testes do mesmo valor selecionam pares diferentes de
   fluxos de movimento para NPC e jogador:
   - `0`: alvo `0x081656CE`, movimentos em `0x08165705` (local ID 3) e
     `0x08165731` (jogador `0xFF`);
   - `1`: alvo `0x081656E0`, movimentos em `0x08165719` (local ID 3) e
     `0x08165744` (jogador `0xFF`).
   Cada bloco termina em `return` e volta ao script principal.
6. Abre porta nas coordenadas `(16,13)`, espera a animação, aplica os movimentos
   locais `0x0816572E` ao ID 3 e `0x08165758` ao jogador, espera, fecha a porta e
   espera novamente.
7. Escreve var `0x4055 = 1`, limpa flag `0x002B`, escreve var `0x4050 = 1`, define
   flag `0x002C` e define flag `0x4001`. Em seguida, a instrução local `warp` contém
   destino grupo `4`, mapa `3`, warp ID `0xFF`, coordenadas `(6,12)`; seguem
   `waitstate`, `releaseall` e `end`.

A busca local na tabela de grupos `0x083526A8` resolve grupo 4/mapa 3 pelo vetor
`0x083523FC` ao header `0x08350DA4`. Esse endereço/índice é evidência local. O nome
“laboratório do Professor Oak” é apenas o rótulo cruzado upstream para esse índice.

## Texto local recuperado

Os operandos do script apontam a `0x0817D72C` e `0x0817D74A`. O probe do decodificador
`gba_poketext.py`, com o remapeamento empírico local `notes_charset_remap_br.json`,
recupera:

- `0x0817D72C`: `OAK`, byte de controle ainda não classificado `0xF0`, “Ei! Espere!”
  e “Não saia!”;
- `0x0817D74A`: “Não é seguro! POKéMON selvagens vivem na grama alta! Você prescisa de
  um POKéMON para te proteger. Já sei! Venha comigo!” (a grafia “prescisa” está nos
  bytes decodificados da ROM).

A presença de `0xF0` é preservada como controle desconhecido; não foi transformada em
pontuação ou texto sem evidência. O terminador e o limite completo da segunda string
foram vistos no probe. Isso confirma localmente que os ponteiros usados durante a
cena apontam para texto em português, não apenas para nomes de textos do upstream.

## Encadeamento e transições de estado

```text
coord event (12,1) ou (13,1), elevation 3, VarGet(0x4050) == 0
  → 0x081655ED / 0x081655F9
  → setvar 0x4001 = 0 / 1; lockall; goto 0x08165605
  → diálogo + movimentos + addobject localID 3
  → setvar 0x4050 = 1; flags 0x002B/0x002C/0x4001
  → warp grupo 4, mapa 3, (6,12); waitstate; releaseall
```

A mudança `0x4050: 0 → 1` encerra a condição usada por esses dois eventos na
próxima consulta; esta consequência decorre diretamente do comparador do ciclo 14 e
do `setvar` no bytecode local. A associação provável dos dois scripts às entradas
“left/right”, dos locais 3 ao Professor Oak, das variáveis a cenas nomeadas e das
flags a ocultar Oak/evitar troca de música vem do cruzamento upstream abaixo. Os
bytes locais comprovam os operandos, decisões e chamadas, não esses nomes.

Também é relevante a reutilização numérica de `0x4001`: nas entradas, o opcode `0x16`
o trata como variável de direção temporária; no final, o opcode `0x29` o entrega ao
serviço de flags. O opcode determina o namespace. Upstream chama a variável de
`VAR_TEMP_1` e a flag especial de `FLAG_DONT_TRANSITION_MUSIC`.

## Cruzamento upstream — nomes e intenção, não prova local

O checkout de referência `pret/pokefirered`, branch `master` sem commit fixado,
alinha os bytes/estrutura aos rótulos `PalletTown_EventScript_OakTriggerLeft`,
`...Right` e `...OakTrigger`, bem como às rotinas auxiliares de entrada e condução
até o laboratório. Também associa os operandos a `VAR_TEMP_1`,
`VAR_MAP_SCENE_PALLET_TOWN_OAK` (`0x4050`),
`VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB` (`0x4055`),
`FLAG_HIDE_OAK_IN_HIS_LAB` (`0x002B`), `FLAG_HIDE_OAK_IN_PALLET_TOWN` (`0x002C`) e
`FLAG_DONT_TRANSITION_MUSIC` (`0x4001`). A tabela de grupos nomeia o destino local
grupo 4/mapa 3 como `PalletTown_ProfessorOaksLab`. Esses nomes explicam a provável
intenção; a seção anterior continua sendo a evidência da ROM BR.

Blobs upstream (todos de `master`, sem commit fixado): `data/maps/PalletTown/scripts.inc`
`1384b7d6c6bb5d2b93538ebaf5e92defde2d41e5`, `data/maps/PalletTown/map.json`
`802d32dc6de7688fe2de8c833d4e040d9137f6c1`, `data/maps/map_groups.json`
`8c382f504d208286161903244772c93138cd7662`, `src/scrcmd.c`
`97b695ee2f6fca80a3b78f52f6a444f696fe5814`, `data/script_cmd_table.inc`
`c5d112d9ea66d258d5a372dda89b9ad96ed2b1e1`, `include/constants/vars.h`
`5c7bbf8a3356606af13e744ac24de806c1b0869e` e `include/constants/flags.h`
`d800adf1e18d1e466a16bc543f6b3c52d60fc6aa`.

## Reprodutibilidade e lacunas

- Bytes de entrada: `0x081655ED–0x08165604`; fluxo de script comum e auxiliares:
  `0x08165605–0x081656F1`; fluxos de movimento apontados por ele em
  `0x081656F2–0x0816575B`. O script seguinte começa em `0x0816575C`; texto nas
  regiões apontadas acima.
- Os handlers usados foram lidos pela tabela local em `0x0815F9B4`; referências
  centrais: `0x0806B6DC` (`0x69`), `0x0806A390` (`0x16`), `0x08069FB0` (`0x05`),
  `0x0806A520` (`0x21`), `0x0806A028` (`0x07`), `0x0806B3B0` (`0x55`),
  `0x0806B200` (`0x4F`), `0x0806AA64` (`0x39`), `0x0806A82C` (`0x29`) e
  `0x0806A840` (`0x2A`).
- O intervalo de movimentos foi apontado pelo bytecode, mas seus opcodes individuais
  ainda não foram decodificados localmente; o evento de coordenada distinto em
  `(13,2)` / `0x0816587B`, os eventos de fundo e os consumidores de warp também
  seguem pendentes.
- Não se alegou que os rótulos upstream pertençam à build BR, nem que a cena tenha
  sido reproduzida no emulador ou em hardware. O rastro fecha esta amostra prática,
  não a cobertura total do código/dados da ROM.
