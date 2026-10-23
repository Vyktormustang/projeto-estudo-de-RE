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

## Próximo passo

1. Criar um savestate base **deste** build (boot completo, já feito: `/tmp/full2/room.bin`).
2. Com o estado certo, refazer o teste da sonda de heap **sem trocar de ROM**.
3. Se for o `Alloc`: trocar a alocação dinâmica da lista por alocação estática em EWRAM
   (mas EWRAM está em 98,9% — ver plano) ou por paginação (só a página visível na memória).
4. Fechar E1 quando lista numérica e contagem funcionarem.
