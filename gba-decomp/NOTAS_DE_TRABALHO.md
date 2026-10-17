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

### 16.3 Estados salvos nao servem como banco de teste

`salvar_estado` -> `carregar_estado` do mGBA produziu estados **inertes** pelo
menos duas vezes (`/tmp/overworld.state`, `/tmp/p4_04800.state`): o jogo nao
responde a nenhum botao depois de carregar (nem a ROM controle), embora a IRQ
continue rodando. Regra: **validar qualquer estado pela resposta a um botao**
antes de usa-lo; na duvida, rodar continuo desde o boot (custa ~1 min por
12 000 quadros, mas e' confiavel).
