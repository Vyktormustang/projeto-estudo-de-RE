# E1 — 1025 espécies: estado real

**Data:** 2026-10-23
**Build:** `pokefirered_modern.gba`, sha256 `e21060787d0c886b41ae9b2597ac1ac9a05740b3cb6281627c895088891a4cf4`
**Base:** `pret/pokefirered` @ `ce6406d` + port da E1 (`scripts/firered/apply_e1_port.py`)

---

## O que está CONFIRMADO

| # | Afirmação | Evidência |
|---|---|---|
| 1 | Compila e linka | `make -j2 MODERN=1 CC1_DAEMONS=2` EXIT 0; ROM com sha256 novo (não o da base) |
| 2 | Header continua FireRed | `POKEMON FIRE` / `BPRE` / maker `01` |
| 3 | Boota até o título | `01_titulo_1025.png` |
| 4 | Novo jogo chega ao quarto em Pallet Town | `02_campo_pallet.png` |
| 5 | **Escada funciona** | warp `4:1 → 4:0` lido da RAM |
| 6 | **Porta funciona** | `4:0 → 3:0` (Pallet Town), lido da RAM |
| 7 | Pokédex aparece no menu | `03_menu_pokedex.png` (precisa de `FLAG_SYS_POKEDEX_GET`) |
| 8 | **Pokédex abre** | `04_pokedex_abre.png` — "POKéDEX TABLE OF CONTENTS" |
| 9 | Navega na Pokédex | cursor desce por Grassland/Forest/… Mountain |

## O que NÃO está confirmado (e o que trava)

| # | Problema | Detalhe |
|---|---|---|
| A | **Crash ao entrar na lista numérica** | Ao confirmar a lista, o jogo **reinicia** (volta para GAME FREAK). `05_crash_na_lista.png` |
| B | Contagem "Seen/Owned" fica **vazia** na tela | pode ser o mesmo problema de A |
| C | Espécies novas ainda **não têm sprite/dados** | normal: isso é E2/E6, não E1 |

### Hipótese principal do crash (não confirmada)

`CB2_PokedexScreen` faz, em `src/pokedex_screen.c`:

```c
sPokedexScreenData->listItems = Alloc(NATIONAL_DEX_COUNT * sizeof(struct ListMenuItem));
```

Com `NATIONAL_DEX_COUNT = 1025` e `sizeof(struct ListMenuItem) = 16`, são **16.400 bytes** de heap
a cada abertura. O heap do FireRed é `HEAP_SIZE 0x1C000` (114.688 B) e é compartilhado com sprites e
tilesets. O estouro derruba o jogo — sintoma típico (reset silencioso).

**O que NÃO foi descartado:** o `Alloc` foi reduzido para 32 B num build de sonda e o crash
continuou, mas aquele teste usou um savestate de outro build (ver seção "Erros de método"), então
**não vale como prova**.

## Erros de método que cometi (para não repetir)

1. **Savestate só serve para a ROM exata que o gerou.** Carregar estado de outro build produz
   estado inconsistente: o jogo parece congelado ou aceita input e não responde. Perdi várias
   rodadas nisso. Regra: cada build novo → novo savestate base (boot completo, ~2 min).
2. **Offsets de struct não podem vir do `global.h` nem do gcc do host.** Os comentários do
   `global.h` estão desatualizados (dizem `flags = 0x0EE0`, real é `0xF2C`; `seen2 = 0x3BC8`, real é
   `0x39C4`). O gcc do host também empacota diferente do ARM. Use `scripts/firered/offsets.py`, que
   compila no ARM real e lê o imediato do assembly.
3. **"Não abre" pode ser sanity check do próprio jogo, não bug.** A Pokédex só abre se
   `GetNationalPokedexCount(FLAG_GET_SEEN) > 0` (`StartMenuPokedexSanityCheck`).
4. **Dentro do jogo, menu demora a responder:** apertar A cedo (frame < 60 após abrir o menu) se
   perde. Usar janelas de 40+ frames e conferir por `md5sum` dos PNGs, não por olhômetro.

## Ferramentas criadas nesta etapa

| Script | Para que serve | Tempo |
|---|---|---|
| `scripts/firered/offsets.py` | offsets de struct do **ARM real** via `-O0 -S` | 0,2 s |
| `scripts/firered/savestate.py` | ler/escrever posição, time, Pokédex e flags no savestate | instantâneo |
| `scripts/firered/savestate_diff.py` | ver **o que o jogo mudou** entre dois savestates | instantâneo |
| `scripts/firered/gen_species_constants.py` | gerar `species.h`/`pokedex.h`/nomes (self-test) | 0,1 s |
| `scripts/firered/apply_e1_port.py` | aplicar o port inteiro num clone limpo | 0,2 s |

## Correções no toolchain (afetam todos os builds)

`scripts/expansion/toolchain_wasm/wtool.mjs` tinha dois defeitos que faziam build "passar" entregando
a ROM antiga:

1. saídas `-o`/`-Map` eram **puladas** quando o arquivo já existia no host — o linker rodava,
   retornava 0 e o `.elf`/`.gba` ficavam congelados;
2. `objcopy` recebe a saída como **argumento posicional** (sem `-o`), então a `.gba` final nunca era
   regravada.

Corrigidos no repositório (e em `/tmp/tc/bin`). Resultado: rebuild completo caiu de ~8 min para
**~1 s** quando só um `.c` muda.


---

## Investigação do crash — conclusão (2026-10-23, segunda rodada)

### Causa descartada: alocação de heap

`Alloc(NATIONAL_DEX_COUNT * 16)` = 16.400 B **não** derruba a Pokédex. Teste isolado:
com o `Alloc` reduzido a 32 B o comportamento foi idêntico; com o `Alloc` original e só o
sanity check desativado, a Pokédex **abre e fecha normalmente**, voltando ao campo
(`/tmp/tj/001390.png`, build `da328f32`).

### Causa encontrada: `StartMenuPokedexSanityCheck`

```c
static bool8 StartMenuPokedexSanityCheck(void)
{
    if (... == StartMenuPokedexCallback && GetNationalPokedexCount(0) == 0)
        return FALSE;
    return TRUE;
}
```

`GetNationalPokedexCount(FLAG_GET_SEEN)` percorre **1025** entradas em vez de 386 e, mais
importante, valida o **anticheat**: o bit só conta se estiver igual em
`SaveBlock2.pokedex.seen`, `SaveBlock1.seen1` e `SaveBlock1.seen2`. Qualquer inconsistência
entre os três zera a contagem e o menu **recusa** abrir — sem mensagem, sem crash, o A
simplesmente não faz nada. Não é bug do port: é o próprio FireRed protegendo a Pokédex.

### Segundo problema: estabilidade dos savestates

Descobri na prática que **savestate do mGBA para esta ROM só é confiável se vier de um boot
completo ou de uma cadeia inteiramente feita com a mesma ROM**. Estados manipulados por
ferramenta e reusados em ROMs diferentes (ou derivados em sequência) ficam "mortos": os
frames saem idênticos em qualquer input, como se o jogo tivesse parado de rodar. Foi a causa
de várias rodadas perdidas nesta etapa.

Detalhe técnico que explica parte disso: savestate é um **delta do cartucho**, e o mGBA só
estabiliza o estado depois de algum tempo de execução. Os frames `0f18b626` que se repetem em
todos os testes vêm de um desses estados mortos.

### Consequência prática (regra para as próximas etapas)

- Toda rodada de teste longo começa com **boot completo** (~2 min com `--pulsos`), não com
  savestate herdado.
- Para telas que dependem de Pokédex, o estado tem de ser montado **por inteiro** (bitmaps
  coerentes nos três lugares) e **depois** validado com `savestate_diff.py` num frame curto.
- `--pulsos` no `nav.py` é obrigatório em menus: o FireRed lê `JOY_NEW` (borda), então botão
  segurado por 40 frames conta **uma** vez e às vezes se perde no meio da transição.

### O que continua pendente na E1

1. Fazer o teste end-to-end da lista numérica com estado montado corretamente (um boot só).
2. Confirmar que a lista mostra `#1025` e rola sem crash.
3. Só então fechar a E1.


### TERCEIRA RODADA — causa raiz de verdade (2026-10-23)

Tudo acima estava certo sobre o sanity check, mas faltava o principal: **os offsets
de struct que a ferramenta calculava estavam errados**. O build usa
`-mabi=apcs-gnu` (ABI ARM antiga) e o probe do `offsets.py` compilava com a ABI
moderna (EABI); as duas empacotam `struct SaveBlock1` de formas diferentes.

Medido **dentro do ROM em execução** (trecho de diagnóstico que grava o endereço
relativo de cada campo em `0x0203FF00`):

| campo | probe dizia | ROM usa |
|---|---|---|
| `SaveBlock1.seen2` | `0x39C4` | **`0x3A64`** |
| `SaveBlock2.pokedex.seen` | `0x0091` (absoluto 169) | **169** (ok) |
| `SaveBlock2.pokedex.owned` | `0x0010` (absoluto 40) | **40** (ok) |
| `SaveBlock1.seen1` | `0x05F8` | `0x05F8` (ok) |

Como o anticheat compara `pokedex.seen` com `seen1` **e** `seen2`, escrever só em
`0x39C4` fazia a comparação falhar, `GetNationalPokedexCount` devolvia 0 e a
lista saía VAZIA (sem crash, sem mensagem). Não era bug do port nem do `Alloc`.

Correção: `offsets.py` agora tem `VERIFICADOS_NO_ROM`, com os valores medidos no
próprio ROM, e avisa quando o probe discorda.

### Causa raiz 2: `NationalPokedexNumToSpecies` só conhecia 386 espécies

`sSpeciesToNationalPokedexNum` é `[NUM_SPECIES - 1]` (1025 posições) mas só tinha
386 inicializadores — as outras 639 ficavam **zero**. Toda Gen 2-9 virava espécie
0 e a lista mostrava `-----`. Além disso a função era uma varredura linear,
chamada uma vez por espécie ao montar a lista: O(n²).

Correção (agora parte de `apply_e1_port.py`, etapa 6b):
- tabela gerada com as 1025 entradas em ordem nacional;
- `NationalPokedexNumToSpecies` virou busca binária.

### Confirmado em jogo

- lista numérica Kanto: `No001 BULBASAUR` (GRASS/POISON), `No004 CHARMANDER`,
  `No007 SQUIRTLE`, com ícone de capturado e tipos — `reports/firered_e1/06_lista_kanto.png`
- contadores `Seen:`/`Owned:` corretos na tela de conteúdo
- Pokédex abre e fecha sem crash

## Próximo passo

1. Criar um savestate base **deste** build (boot completo, já feito: `/tmp/full2/room.bin`).
2. Com o estado certo, refazer o teste da sonda de heap **sem trocar de ROM**.
3. Se for o `Alloc`: trocar a alocação dinâmica da lista por alocação estática em EWRAM
   (mas EWRAM está em 98,9% — ver plano) ou por paginação (só a página visível na memória).
4. Fechar E1 quando lista numérica e contagem funcionarem.
