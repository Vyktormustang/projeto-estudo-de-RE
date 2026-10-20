# Notas de trabalho (operacional)

Caderno curto: só o que preciso para retomar rápido. Explicação completa vai
para `RELATORIO_o_que_ja_sabemos.md` e `README.md` **no fim** do trabalho.

## Rodar

```bash
P=/home/user/projeto-estudo-de-RE/.venv/bin/python
$P -m pytest tests/ -q                       # 91 testes
$P ferramentas/aplicar_patch_pokebolas.py ROM.gba -o NOVA.gba --json r.json
$P ferramentas/aplicar_manifesto.py ROM.gba patches/exemplo_dados.json -o NOVA.gba
$P ferramentas/aplicar_manifesto.py ROM.gba patches/exemplo_texto.json -o NOVA.gba
```

ROM de trabalho (fora do repo, fora do git):
`/home/user/gba-re/rom/pokemon_firered_bpre_trabalho.gba`
sha256 `6035a98f…`, 16 777 216 B, `POKEMON FIRE` / `BPRE`.
Ela **pode sumir** com o ambiente: rebaixar do Drive (`14JCEJp6LFgdkzKMOtI5-l3XvowJ1SxnC`).

## Endereços confirmados (medidos)

| o quê | onde |
|---|---|
| `gSaveBlock1Ptr` / `gSaveBlock2Ptr` | `0x03005008` / `0x0300500C` |
| `encryptionKey` | `[0x0300500C]+0xF20` |
| `gBagPockets` (5 × `{ptr, cap}` de 8 B) | `0x0203988C` |
| pockets em SaveBlock1 | `+0x310` 42 · `+0x3B8` 30 · **`+0x430` 13 bolas** · `+0x464` 58 · `+0x54C` 43 |
| `GetBagItemQuantity` / `SetBagItemQuantity` | `0x08099DA0` / `0x08099DBC` |
| `GetPcItemQuantity` / `SetPcItemQuantity` | `0x08099DD8` / `0x08099DDC` (PC **não** cifra) |
| `ItemId_GetPocket` / `ItemId_GetPrice` | `0x0809A9D8` / `0x0809A900` |
| `AddBagItem` / `RemoveBagItem` | `0x0809A084` / `0x0809A1D8` |
| `ClearItemSlots` / `ResetBag` | `0x0809A274` / `0x0809A2DC` |
| `AddPCItem` (`pcItems` @`0x298`) | `0x0809A3C8` — **não é bag** |
| `gItems` (passo 0x2C) | `0x083DB028` |
| `NewGameInitData` | `0x08054A60` |
| `bl ResetBag` dentro dela (hook do patch) | `0x08054B06` |
| literal do dinheiro inicial (3000) | `0x08054B60` (lido por `0x08054AD4`) |
| espaço livre grande | `0x088001C7` 5 242 425 B · `0x08EB0B20` 1 373 408 B · `0x0871A905` 939 771 B |

## Armadilhas (cada uma já custou tempo)

- **`0x298` é `pcItems`, não bag.** `0x0809A3C8` é `AddPCItem`; `0x08099DD8/DC`
  são as versões de PC, sem cifra.
- **Desmontar em endereço errado produz lixo convincente.** `0x08099D70..9F` é
  dado; a função começa em `0x08099DA0`. Antes de concluir que "não faz sentido",
  conferir o prólogo (`push` com `lr`).
- **`0x0804C058` é boot, antes do save.** Escrita ali é sobrescrita.
  `ResetBag` zera as 5 pockets → escrever **depois** dele.
- **`0x08111374` parece chamar `ResetBag`, mas é dado.** O chamador real é só
  `0x08054B06`.
- **`bl` é relativo**: montar para o endereço de destino, nunca para `0`.
- **`achar_espaco_livre` com mínimo pequeno pega padding** (81 B em `0x081BA4E6`).
  Mínimo 4 KiB.
- **`esperado` lido da própria imagem é tautológico**: a 2ª aplicação passa.
  Usar constante (`bl ResetBag` montado).
- **Pool de literais é compartilhado?** Conferir todos os `ldr [pc]` da função
  antes de editar o valor. No dinheiro inicial, só `0x08054AD4` usa `0x08054B60`.
- **Soma de offset do `gItems`**: `base + id*0x2C + campo`. `4*0x2C = 0xB0`;
  `+0x10` = `0xE8`, não `0xD8`. A guarda do patch pegou.
- **`complemento` = soma `0xA0..0xBC`**, não `0x00..0xBC`.
- **`/tmp` e `.venv` não persistem**; o git sim.

## Três tipos de patch, três verificações

| patch | arquivo | verificação | provado? |
|---|---|---|---|
| lógica (99 Poké Bolas no jogo novo) | `ferramentas/aplicar_patch_pokebolas.py` | emulação do stub + `GetBagItemQuantity` + `ItemId_GetPocket` | sim, no emulador |
| dado (preço 200→1, dinheiro 3000→999999) | `patches/exemplo_dados.json` | `ItemId_GetPrice` do jogo | sim, no emulador |
| texto (POKé BOLA→BOLA NOVA) | `patches/exemplo_texto.json` | decodificação com o charset da §9.5 | **não por emulação** |
| **comportamento** (limite 999→99 por slot) | `patches/exemplo_limite.json` | `AddBagItem(4,10)` com 95 no slot: original soma p/ 105 e retorna 1; patchado retorna 0 e deixa 95 | sim, no emulador |

- **Não provado**: que o boot real chegue com `gBagPockets` apontado; que a tela
  exiba; **nada foi jogado** (sem emulador de console no ambiente).
- `CopyItemName` **não foi localizado** (os candidatos `0x0809A7B0`/`0x0809A7D8`
  são outros acessores de pocket) — por isso o texto é verificado por
  decodificação.
- **Dígitos medidos** (não inferidos): a ROM tem 52 strings `TMxx`
  (`CE C7 <d> <d> FF`) e os pares cobrem `A1A2` (TM01) a `A6A1` (TM50) sem
  lacuna → `0xA1..0xAA` = `'0'..'9'`. `texto.codificar("TM01")` funciona e
  há teste de ida e volta em TM00..TM50.

## Próximos passos

1. ~~Medir os dígitos~~ (feito) e ~~patch de comportamento~~ (feito, limite).
   Achar o `CopyItemName` — `ItemId_GetId`
   (`0x0809A8DC`) tem **0 chamadores** por `bl`, então ou é chamado por tabela
   indireta ou foi inlined; não insistir pelo caminho de `bl`.
2. Verificar se o limite de 99 também é usado por `MoveItem`/`SortAndCompactBagPocket`
   (o `0x3E7` pode aparecer em mais de um pool; aqui só `0x0809A0D8` usa `0x0809A0E4`).
3. Fim do trabalho: consolidar tudo em `RELATORIO` (§11 cresce) e `README`;
   aí sim atualizar o corpo do PR com o resumo.

## 12. O bug que explicava "o hook nao roda" (2026-10-17)

**Sintoma**: hooks em `0x08054B06` (NewGameInitData) e no prologo de
`ResetBag 0x0809A2DC` nunca incrementavam o contador. A conclusao anterior --
"esses pontos nao executam" -- estava **incompleta**: o contador tambem nunca
subiria se o stub carregasse o endereco errado.

**Causa**: o keystone 0.9.2 monta `ldr rX, =VALOR` com deslocamento errado
quando ha' **mais de um** literal no bloco. Medido, dissecando o stub gerado:

```
0871A908: 064c   ldr r4, [pc, #0x18]   -> 0x0203FFF0   OK
0871A90A: 0748   ldr r0, [pc, #0x1c]   -> 0x05000020   ERRADO (queria 0xDEADBEEF)
0871A90E: 0748   ldr r0, [pc, #0x1c]   -> 0x12345678   ERRADO (queria 0x05000020)
0871A910: 0749   ldr r1, [pc, #0x1c]   -> 0x34123412   ERRADO (queria 0x12345678)
```

Nao ha' erro de montagem: a ROM boota e o stub escreve no lugar errado, em
silencio. O stub de poke bolas usava **quatro** literais -- todos depois do
primeiro caíam no literal seguinte.

**Correcao**: `patch.montar_thumb_literais()` substitui cada `ldr rX, =VALOR`
por um `ldr rX, [pc, #0]` de 2 bytes, monta o corpo, calcula o pool **por
conta propria** e **confere por desmontagem** antes de devolver. Erro de
literal agora e' excecao, nao surpresa. 5 testes em `tests/test_patch.py`
cobrem: 1 literal, 3 literais, endereco 2-mod-4, sem literal, e `bl` de 4
bytes no meio (que nao pode ser confundido com marcador).

Detalhe que custou tempo: o `ldr` literal do Thumb usa `Align(PC,4)`, nao
`(PC+4)&~2`. Com alinhamento de 2 o deslocamento sai 10 (nao divisivel por 4).

**Prova de que injecao funciona** (`rom_plumb3` -> `probe_reset2`): o branch de
reset em `0x08000000` foi redirecionado para um stub ARM em espaco livre
(`0x0871A908`) que incrementa `0x02037F00` e trava com `b .`. Resultado lido do
emulador: **contador = 1** e CPU travada por 90 quadros. Primeira prova dura de
que codigo injetado em espaco livre executa nesta ROM.

**Armadilha que mascarou tudo antes**: `0x02037F00` e' EWRAM e o init do jogo
faz memset nela. Contador escrito antes do init **volta a zero**. Para
instrumentar o boot, o stub tem de travar a CPU (`b .`) depois de contar, ou
usar endereco que o init nao zera.

**O que isso reabre**: `0x08054B06` continua sem contador mesmo com stub
correto (medido com `rom_cnt.gba`), entao *esse* ponto segue nao executado.
Mas `ResetBag` tem **dois** chamadores -- `0x08054B06` e `0x08111374` -- e os 6
chamadores de `ClearItemSlots` foram instrumentados juntos em `rom_quem.gba`:
nenhum contador subiu no fluxo de jogo novo. A bag e' inicializada por outro
caminho, ainda nao localizado.

## 13. A resposta: qual campo da' poke bolas (MEDIDO EM JOGO)

**Campo**: `SaveBlock1 + 0x430` (pocket de Poke Balls), slot 0.

```
+0x430 + 4*n + 0  u16 itemId     -> 4 = POKe BOLA
+0x430 + 4*n + 2  u16 quantidade -> qtd XOR (*(u32*)(SaveBlock2+0xF20) & 0xFFFF)
```

**Como o XOR foi descoberto (nao deduzido)**: com a mochila vazia, todos os 5
slots das 5 pockets liam `00 00 04 85`, isto e', itemId 0 e quantidade
`0x8504`. A chave de cifra naquele instante era `0x0E078504` -- a metade baixa
e' exatamente `0x8504`. Ou seja: slot vazio guarda `0 ^ (chave & 0xFFFF)`, nao
zero. Gravar 99 "cru" teria dado quantidade lida = `99 ^ 0x8504`, um numero
absurdo.

**Prova em jogo** (`evidencias/mochila_pokebola_99.png`): com o jogo rodando no
overworld, escrevi `itemId=4`, `qtd=99^0x8504`, abri o menu (START) -> BOLSA ->
duas vezes DIREITA. A tela mostra **"POKe BOLA x 99"** na pocket "POKe BOLAS",
com a descricao do item. Nenhuma outra escrita foi feita.

**Estado salvo**: `/tmp/overworld.state` (528 448 B) permite repetir o
experimento em ~6 s em vez de ~190 s (`emulador_console.salvar_estado` /
`carregar_estado`, novos).

## 14. O patch de ROM automatico ainda NAO fecha (honesto)

Tentei 5 caminhos para injetar a escrita sem intervencao do emulador. Todos
**medidos como nao executados** ou sem efeito:

| ponto | o que era | resultado |
|---|---|---|
| `0x08054B06` | `bl ResetBag` em NewGameInitData | contador 0 (com stub correto) |
| `0x08111374` | 2o chamador de ResetBag | contador 0 |
| 6 chamadores de `ClearItemSlots` | inclui `0x0809A2EA`, dentro de ResetBag | contador 0 |
| 13 chamadores de `GetBagItemQuantity` | leitura de quantidade | contador 0 ao abrir a mochila |
| 28 `bl` do modulo da mochila (0x08099E00-0x0809A300) | desenho/consulta da bolsa | 1 disparo, nao relacionado a bolsa |
| 12 `bl` da UI (0x081085xx/0x08108Exx/0x081096xx) | UI que usa `gBagPockets` | nenhum |
| entry de `0x08000844` / `0x0800080C` | supostos VBlank/HBlank | nao chamados |

**O que ficou medido no caminho**:

- A tabela de callbacks de IRQ fica em **`0x03007438`** (literal do `IntrMain`)
  e as entradas apontam para **IWRAM** (`0x03001FC4`, `0x0300150C`, ...), nao
  para ROM. Logo, nao da' para hookar IRQ por arquivo.
- `IntrMain` esta' em **`0x08000248`** e e' copiado inteiro para IWRAM em
  `0x03003580` (>0x400 bytes identicos, medido byte a byte). Qualquer `bl` que
  eu inserir nesse bloco aponta certo em ROM e errado na copia -- **nao hookar
  o bloco copiado**.
- A UI da mochila **nao chama `GetBagItemQuantity`** (medido: nenhum dos 13
  call-sites disparou com a bolsa aberta e navegada). Ela le' o slot direto.
- Contadores em EWRAM escritos no boot sao **apagados pelo memset do init**.
  Para instrumentar o boot, o stub tem de travar a CPU (`b .`) depois de contar
  -- foi assim que `probe_reset2` provou contador = 1.
- Stub ARM exige endereco **alinhado a 4**; `achar_espaco_livre(...,
  alinhamento=4)`. Com `alinhamento=2` (padrao) o codigo ARM nao roda.

## 16. `BL` do Thumb no ARM7TDMI: ±4 MiB (e por que metade dos hooks "nao disparava")

**Medido.** O `bl` do Thumb no ARM7TDMI tem **22 bits de deslocamento**
(`S` + `imm10` + `imm11`, vezes 2) e alcanca **so' ±4 MiB**. O keystone 0.9.2
monta e o capstone desmonta esse salto na forma do Thumb-2 (`bl` de 32 bits,
±16 MiB) --- e **nenhum dos dois avisa**. Resultado: um `bl` "para `0x0871A906`"
a partir de `0x080004A6` vira, no silicio, um salto para `0x0831A906` (4 MiB
antes), que e' lixo. Foi essa a causa de uma serie de "o hook nao roda".

Decodificador correto, usado para conferir tudo:

```python
def bl_armv4t(hw1, hw2, pc):
    s = (hw1 >> 10) & 1
    off = ((s << 21) | ((hw1 & 0x3FF) << 11) | (hw2 & 0x7FF)) << 1
    if s:
        off -= 1 << 23
    return pc + 4 + off        # alcance: +/- 4 MiB
```

Consequencias praticas:

- **Nunca** injetar codigo a mais de 4 MiB do ponto de hook usando `bl`.
  `ferramentas/injetar_c.py` agora tem `conferir_alcance()` e **recusa** o patch.
- O espaco livre grande desta ROM (`0x0871A906`, ~940 kB) esta' a 7,1 MiB do
  loop principal. Para usa-lo, o stub fica **perto do hook** (padding
  `0x080000C0`, 64 bytes livres) e chama o codigo por um **thunk**:

  ```
  push {r0, r1, r2, r3, lr}
  ldr  r3, =destino|1
  bl   thunk            ; o `bl` seta lr com o bit Thumb ligado
  pop  {r0, r1, r2, r3}
  bl   original
  pop  {pc}
  thunk: bx r3
  ```

  O idioma "classico" `mov lr, pc; bx r3` **nao funciona** no Thumb do
  ARM7TDMI: a leitura de PC devolve o endereco com o **bit 0 zerado**, entao o
  `bx lr` do destino voltaria em estado ARM. O `bl` seta o bit.
- Toda chamada indireta gerada pelo `zig cc -mcpu=arm7tdmi` tambem sai nesse
  formato (`ldr r0,=fn|1; bl thunk; bx r0`) --- conferido por desmontagem.

### 16.1 A prova de que o stub roda

`rom_marca_c3.gba`: stub em `0x080000C0`, codigo em `0x0871A908`
(`*(u32*)0x02037F00 += 1`), `--reexecutar 0x08000890`. Rodando **desde o boot,
sem estado salvo**, o contador sobe ~1 por quadro:

| quadro | 600 | 1 800 | 3 600 | 7 200 | 12 000 |
|---|---|---|---|---|---|
| contador | 570 | 1 761 | 3 467 | 6 959 | 11 588 |

Ou seja: o hook em `0x080004A6` (`bl 0x08000890`, a espera de VBlank do
`AgbMain`) e' alcancado praticamente todo quadro, e o caminho
hook -> stub -> thunk -> codigo C -> chamada original -> retorno esta' correto.

### 16.2 O que ainda NAO funciona: entrar no jogo

Medido no emulador (mGBA libretro), com a ROM original e com as patchadas:

- O jogo boota, passa por copyright/GAME FREAK, anima a intro e chega ao
  "PRESS START" (VRAM `a5a949e7`).
- As teclas **chegam ao jogo**: `KEYINPUT` (0x04000130) vai a `f703` com START
  e o `gMain` do jogo fica com `heldKeys` (0x03003118) = `newKeys`
  (0x0300311C) = `0x0008`.
- Mesmo assim nenhuma tela muda: START/A/B/direcional no titulo nao abrem o
  menu, e o callback ativo continua sendo o da intro (`0x08078BB5`); os outros
  dois vistos no ciclo sao `0x080EC9ED` e `0x080EC5A5`.
- Forcar `heldKeys`/`newKeys` para `0x0008` todo quadro via codigo injetado
  (`rom_forca.gba`) **tambem nao muda nada**.
- Chamar a rotina de novo jogo (`0x08056644`, que chama `NewGameInitData`)
  pelo hook, aos 1 600 quadros, zera `gMain.callback2` e deixa a tela parada.
- **Nao esta' provado** se a causa e' o hack de traducao (o titulo do BR pode
  estar quebrado) ou o core libretro. Fica registrado como bloqueio aberto.

O que ja' foi descartado como causa (medido em 2026-10-17):

- **A ROM nao esta' corrompida**: MD5 local `4ec27a4b580a5a883ba66f924810cbd7`
  e' identico ao `md5Checksum` que o Drive informa para o arquivo.
- **O binario do core nao e' o problema**: compilei o mGBA 0.10.5 do fonte
  (`/tmp/mgba-src/build/mgba_libretro.so`, sem shim de glibc) e o
  comportamento e' identico (titulo nao responde ao START).
- **Nao e' ordem de escrita das teclas**: forcar `heldKeys`/`newKeys` em
  `0x080004A2` (antes da chamada de callback do quadro) tambem nao muda nada.
- **Nao e' o `mov lr,pc`**: o stub agora usa `bl thunk; bx r3` e o contador
  prova que o codigo roda.
- O usuario confirmou que a mesma ROM **abre o menu normalmente em outro
  emulador** -- entao a divergencia esta' no nosso harness/core, nao no jogo.

Sugestoes para quem for continuar: (a) comparar com o que o RetroArch faz de
diferente (input poll por quadro, `retro_set_controller_port_device` antes do
load, audio batch de verdade); (b) pedir um save state do usuario feito em
outro emulador e testar; (c) investigar se o core esta' entregando a IRQ de
VBlank no meio do quadro (o `IF` fica em 0x0001 e o CPSR tem I=0, mas nenhum
handler e' visto).

### 16.3 Estados salvos nao servem como banco de teste

`salvar_estado` -> `carregar_estado` do mGBA produziu estados **inertes** pelo
menos duas vezes (`/tmp/overworld.state`, `/tmp/p4_04800.state`): o jogo nao
responde a nenhum botao depois de carregar (nem a ROM controle), embora a IRQ
continue rodando. Regra: **validar qualquer estado pela resposta a um botao**
antes de usa-lo; na duvida, rodar continuo desde o boot (custa ~1 min por
12 000 quadros, mas e' confiavel).

## 17. O "titulo travado" era erro nosso de medicao (2026-10-17) -- RESOLVIDO

A §16.2 esta' **superada**. O jogo sai do titulo no nosso harness, com o
nosso core, desde sempre -- quem estava errado era a leitura dos campos.

### 17.1 Os offsets certos do `gMain` (base `0x030030F0`)

Conferidos com o `include/main.h` do pret/pokefirered e com o comportamento
medido quadro a quadro:

| offset | endereco | campo |
|---|---|---|
| +0x00 | `0x030030F0` | callback1 |
| **+0x04** | **`0x030030F4`** | **callback2** |
| +0x08 | `0x030030F8` | savedCallback |
| +0x0C | `0x030030FC` | **vblankCallback** (o nosso antigo "cb2"!) |
| +0x24 | `0x03003114` | vblankCounter2 |
| +0x28 | `0x03003118` | heldKeysRaw |
| +0x2A | `0x0300311A` | newKeysRaw |
| +0x2C | `0x0300311C` | heldKeys |
| **+0x2E** | **`0x0300311E`** | **newKeys** (o que `JOY_NEW` testa) |
| +0x438 | `0x03003528` | state |

Consequencia: ficam **invalidados** os experimentos que forcavam campos --
`rom_forca.gba`/`rom_forca2.gba` escreviam heldKeysRaw/heldKeys e nunca o
`newKeys`, e o `rom_menu.gba` gravou `0x0800C689` no **vblankCallback**, nao
no `callback2`. As conclusoes "o jogo ignora o input" e "o despachante nao
usa o gMain" nasceram dai'.

### 17.2 A maquina do titulo, medida

`gTasks` em `0x03005090`: 16 tarefas x 40 B (`func`, `isActive`, depois
`s16 data[16]` em +8). Funcoes medidas nesta ROM:

- `Task_TitleScreenMain` = `0x08078C25` -- data[0]=cena, data[1]=estado
- tarefa do timer = `0x08078BED` (data[0] sobe 1/quadro ate' 2700)
- `CB2_TitleScreenRun` (callback2) = `0x08078B9D`; VBlankCB do titulo
  (vblankCallback) = `0x08078BB5`

Sem aperto, o ciclo completo funciona: titulo entra na cena RUN (3) aos
~1730 quadros, fica 2700 quadros (o timer), vai para RESTART (4) aos ~4200,
volta para copyright/intro e recomeca (RUN de novo aos ~6050). **Nada esta'
travado**: e' o loop de atracao do jogo.

### 17.3 Teste de controle (o P0 da PESQUISA)

A homebrew `keyinput_rom.py` do projeto gba-harness (codigo **revisado**
antes de rodar: monta a ROM por tabela de instrucoes ARM) no NOSSO harness:
sem botao, os 10 pixels ficam pretos; segurando START, o pixel 3 acende
(`evidencias/controle_keyinput_start.png`). A cadeia
agenda -> `input_state` -> KEYINPUT -> VRAM -> framebuffer sempre funcionou.

O gba-harness em si nao foi importado: ele exige Python 3.12 (`type X = ...`)
e o sandbox e' 3.11.2 (`SyntaxError` conferido). A revisao do
`libretro_port.py` dele achou mesmo assim 2 bugs latentes nossos, ja'
corrigidos em `emulador_console.py` com 4 testes novos
(`tests/test_emulador_console.py`; suite: **104 passed**):

- `GET_CAN_DUPE` escrevia `c_int` (4 B) onde a ABI pede `bool` (1 B);
- `GET_VARIABLE` tratava `struct retro_variable*` como buffer de texto e
  escrevia sobre o ponteiro da chave (devolvendo 1 sempre).

Nenhum dos dois era a causa do "travamento"; sao corrupcao real mesmo assim.
O libretro.py tambem nao precisou ser executado: o controle + a timeline
isolaram a causa.

### 17.4 A navegacao que funciona (e a licao sobre hash de VRAM)

`ferramentas/ir_ao_menu.py` (repetido 2x, quadros identicos -- deterministico):

- cena RUN alcancada no quadro **1730** (`evidencias/titulo_press_start.png`);
- A apertado: no quadro **1733**, KEYINPUT=`03fe`, `newKeys`=1 (um quadro
  so') e a cena salta (3,1) -> (5,0) CRY **no mesmo quadro**;
- (5,2) aos ~1830 (espera de 90 + fade); tarefa do titulo morre aos **1870**
  e o callback2 vira `0x0800C301`, depois `0x0812EB11`; primeira tela
  fotografada depois disso: a pagina CONTROLE
  (`evidencias/apos_titulo_controle.png`);
- com pulsos de A a cada 200 quadros, o jogo atravessa a intro inteira ate'
  a tela de nomear o jogador (`evidencias/intro_nome_jogador.png`, ~6500).

Por que um START so' aos 1500 "nao fazia nada": aos 1500 a cena ainda e' 2
(FADEIN), e aperto nas cenas 0-2 **pula para a RUN** -- falta o segundo
aperto, ja' na RUN. E o hash de VRAM nao enxerga nada disso: na RUN a VRAM
e' constante (quem anima e' paleta/sprite), e fade e' paleta pura. Regra
nova: **tela se julga por PNG/framebuffer, nunca por hash de VRAM**.

**Nao provado**: se entre os quadros 1860-1875 aparece a lista do menu
principal ("NOVO JOGO") -- nao amostramos quadro a quadro ali; e os nomes
`CB2_InitMainMenu`/`CB2_MainMenu` para `0x0800C301`/`0x0812EB11` sao
inferidos do pret, sem desmontagem nesta ROM ainda.

## 18. Overworld alcancado: boot -> quarto (2026-10-20, sessao seguinte) (ferramentas `ir_ao_overworld.py` + `validar_estado_overworld.py`)

**Resultado**: a navegação agora vai do boot ate' o **quarto do jogador**
(em ~1 min de relogio, 6955 quadros), e o estado salvo nesse ponto foi
**validado vivo** num processo novo. Evidencias: `evidencias/overworld_quarto.png`
e `overworld_val_*.png`.

### 18.1 Linha do tempo medida (deterministica: 3 execucoes identicas)

- q.1870 sai do titulo com callback2 `0x0800C2D5` (transitorio; na §17 a
  amostragem pegou `0x0800C301` -- amostras diferentes da mesma transicao).
- q.1885 -> `0x0812EB11` (dialogos: paginas de CONTROLE + fala do professor
  + escolha de sexo): avanca com pulso de A a cada 45 quadros.
- q.4540 -> `0x0809FB71`: **tela de nomear #1** (jogador);
  q.5365: **#2** (rival). Total na intro: 96 pulsos de A.
- q.6595 -> `0x080565B5`, estavel por 240+ quadros => overworld (confirmado
  pelo comportamento, ver 18.3; o nome `CB2_Overworld` do pret e' inferido,
  sem desmontagem nesta ROM).

### 18.2 START na tela de nomear NAO confirma (bug da 1a versao)

No pret (`src/naming_screen.c`), `INPUT_START` chama apenas
`MoveCursorToOKButton()`; quem confirma e' **A sobre o botao OK**. A primeira
versao esperou a saida so' com START e queimou 357 s ate' o limite. Corrigido:
A digita a letra, START vai ao OK, A confirma (com teto por tentativa).

### 18.3 SaveBlock1 e' via ponteiro, NAO endereco fixo (corrige nota antiga)

No overworld, `[0x03005008]` (`gSaveBlock1Ptr`) = **`0x0202557C`** e
`[0x0300500C]` = `0x020245D8`: **+0x38** em relacao aos `0x02025544`/
`0x020245A0` medidos em sessoes anteriores (lidos naquele contexto a partir
dos mesmos ponteiros -- o buffer muda com o contexto, ex.: Quest Log).
A `0x02025544` fixo esta' **tudo zerado** aqui. **Regra: sempre
`ler_u32(0x03005008)` antes de tocar no SaveBlock1** (idem 0x50 0C p/ o 2).
`ferramentas/ir_ao_overworld.py` ja' faz isso; usos antigos de endereco fixo
devem ser revistos antes de reusar.
Medido via ponteiro no spawn: `pos=(6,6)`, `location=(grupo 4, mapa 1,
warp -1)` -- quarto do jogador (PNG confere).

### 18.4 Estado salvo VALIDADO (o contraste com a §16.3)

`salvar_estado` gerou 528.448 bytes (fora do repo). Num processo novo,
`ferramentas/validar_estado_overworld.py`: BAIXO (6,6)->(6,8),
DIREITA ->(9,8), START abre o menu (BOLSA/SALVAR/OPCOES/SAIR -- sem
POKeMON/POKeDEX ainda), B fecha e o framebuffer volta **byte-identico**
(hash `890d5737` antes e depois). Entao estados gerados *deste* jeito
(boot continuo ate' o overworld) sao reutilizaveis; na duvida, a propria
ferramenta refaz o caminho em ~1 min. O arquivo de estado nao vai para o
Git (contém a RAM com a ROM embutida por referencia de execucao; e nao
persiste entre sessoes -- regenerar quando precisar).

**Nao provado**: nomes pret dos tres callbacks (`0x0812EB11`,
`0x0809FB71`, `0x080565B5`) seguem inferidos pelo comportamento; e por que
o buffer do SaveBlock1 varia (+0x38) nao foi investigado -- so' medido.

## 19. Do quarto ao inicial (ferramenta `ir_ao_inicial.py`, 2026-10-20)

**Resultado**: boot -> inicial -> batalha do rival -> fora do lab numa
ferramenta so' (199 s na execucao `--do-boot`); tambem roda do estado do
quarto. Evidencias `evidencias/inicial_*.png` (batalha, time com o
Bulbasaur "A" nv6 22/22 carregado de um estado salvo).

### 19.1 Movimento tile a tile e as armadilhas de warp (tudo medido)

Primitiva que funciona: segurar a direcao **ate' `pos` mudar** (amostra a
cada 2 quadros), soltar -- segurar 20 quadros anda 2 tiles. Bloqueio pode
ser NPC andando (a moca da placa em Pallet): esperar 50 q e repetir.
- **Warp tem atraso**: pisar na escada (10,2) do quarto so' troca o mapa
  durante o **passo seguinte** (a 1a versao leu o mapa cedo demais e
  achou que nada tinha acontecido);
- **a porta da casa so' dispara descendo a partir do tapete** (4,8)->sul;
  andar na horizontal pela fileira 8 nao sai (conferido por PNG em cima
  do tapete sem warp). Sair da casa repoe o jogador 1 tile ao sul da
  porta ((6,7) -> (6,8));
- rota da cerca: a fileira y=10 ao sul da casa bate na cerca/placa --
  o caminho e' pela frente das casas (y=8) ate' x=11, subir ate' (11,2),
  andar para (12,2) e subir ao gatilho **(12,1)**;
- coordenadas do pret conferidas na pratica: escada (10,2), bolas do lab
  em (8,4)/(9,4)/(10,4), gatilhos de saida do lab (5..7,8), porta do lab
  em Pallet (16,13). Aproximar-se do Oak no lab abre o dialogo da
  escolha **antes** de poder andar ate' as bolas (script move o jogador
  para (6,4) -- o "passo para cima" misterioso da 1a tentativa).

### 19.2 Onde o time mora DE VERDADE durante o jogo

A 1a versao leu `partyCount` em SB1+0x34 (offset do pret) e viu 0 sempre,
mesmo depois da escolha -- o menu POKeMON e a tela do time provavam o
contrario. Varredura por assinatura (apelido "A"=BB FF... em +8, OT "A"
em +20, nv/HP plausiveis) achou a estrutura viva em **`0x02024284`** e o
byte de contagem em **`0x02024029`** (0->1 isolado no diff
antes/depois; o flip foi reconfirmado na execucao unificada). Ou seja:
durante o jogo valem os simbolos soltos `gPlayerParty[Count]`; os campos
+0x34/+0x38 do SaveBlock1 ficaram zerados o tempo todo (devem ser
preenchidos ao salvar no cartucho -- NAO provado).
Bases do SaveBlock medidas nesta sessao: SB1ptr em {02025538, 02025544,
0202557C, 02025580}, com SB1-SB2 sempre `0xFA4` -- os ponteiros se movem
juntos; offsets relativos valem, endereco absoluto nao (regra da §18.3).

### 19.3 Batalha do rival por A

`callback2` na batalha: `0x080565B5` -> `0x080565A9` -> `0x08010509` ->
**`0x08011101`** (estavel em batalha) -> volta a `0x080565B5`. Com A a
cada 60 q (LUTAR -> 1o golpe), a execucao em etapas terminou nv5 19/19 e
a unificada do boot **nv6 22/22** (subiu = venceu ao menos esta). O
desfecho varia com o RNG; o progresso continuou nas duas -- nao
registramos frame a frame quem venceu a 1a.

**Nao provado**: o apelido do Pokemon usa o mesmo `callback2 0x0809FB71`
da intro (provado), mas se e' a mesma FUNCAO ou duas com o mesmo
comportamento, nao desmontamos; especie do inicial nao foi lida da
estrutura (os dados da caixa sao cifrados) -- foi confirmada pela foto
do time; e o papel dos campos +0x34/+0x38 no salvamento real segue
hipotese.

## 20. Caixa cifrada do Pokemon: leitura E escrita provadas (`gbadecomp/pokemon.py`, 2026-10-20)

Fecha o "nao provado" de especie da §19: os 48 bytes seguros decifram com
XOR `personalidade ^ otId` por u32, subestruturas permutadas por
`personalidade % 24` (tabela do pret `GetSubstruct`, copiada em
`pokemon.ORDEM`), checksum = soma dos 24 u16 decifrados. Biblioteca
`gbadecomp/pokemon.py` + `tests/test_pokemon.py` (6 testes, sem emulador,
sobre os bytes reais) + ferramentas `mostrar_time.py` e `dar_golpe.py`.

### 20.1 Prova cruzada em dois especimes (o mesmo Bulbasaur, 2 execucoes)

Nos dois: checksum bate, especie=1, golpes=(33,45,0,0) PP (35,40) e os
atributos gravados pelo jogo **recomputam exatamente** dos IVs decifrados
(formula da ger. 3, natureza = personalidade % 25). E os dados contam a
historia que a §19.3 nao sabia: a execucao em etapas **perdeu** a batalha
do rival (EXP travado em 135 = minimo do nv5 "medio lento", EVs todos 0,
amizade 69), e a do boot **venceu** (EXP 204 = 135+69, EV de Vel=1 --
rendimento do Charmander -- nv6, amizade 76). `otId` identico nas duas
(0x10BCD3DB): o caminho deterministico da intro produz o mesmo treinador.

### 20.2 Escrita segura provada em jogo

`dar_golpe.py` pos o golpe 73 no slot vazio (posicao 3) com PP 10:
decifra -> altera -> recifra -> checksum novo -> escreve 100 bytes ->
salva estado NOVO (o de entrada intocado). Num processo novo, o time
mostra o Bulbasaur normal (nada de Bad Egg) e a pagina GOLPES do resumo
lista o terceiro golpe -- evidencias `golpe_time.png`/`golpe_golpes.png`
("SEMENTE SUGA?" na traducao do hack, PP10/10, junto de INVESTIDA e
ROSNAR). Serializar sem editar e' byte-identico ao original (teste).

**Nao provado**: editar especie/IVs/nivel (o jogo so' recalcula atributos
em eventos proprios -- nao testamos o que acontece ate' la'); persistir
pelo SALVAR do menu (nao executado); o mesmo formato nas caixas do PC
(a struct de caixa e' a mesma no pret, mas nao lemos nenhuma caixa
ainda); e o significado do u16 em +0x1E ("unknown" no pret, 0 nos dois
especimes).
