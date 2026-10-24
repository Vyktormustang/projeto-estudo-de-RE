# E7 — capturas de tela (Rota 1)

ROM: `pokefirered_modern.gba`, md5 **`821f35a7805fa2738576a33b6682c1b2`**
(16 777 216 B). Estado de partida: savestate da Rota 1 (`/tmp/e4estado/rota1.bin`,
gerado por `prova_golpes_e4.py --preparar-estado`) com 20 Poké Balls na pocket de bolas.

**Savestate só vale na ROM exata que o gerou.** Toda mudança no jogo muda o md5 e o
estado congela ou cai na tela errada; depois de qualquer build, refaça
`python3 scripts/firered/prova_golpes_e4.py --preparar-estado`.

Reprodução automática, sem editar a ROM:

```
python3 scripts/firered/prova_encontros_e7.py --prova --tentativas 12 --capturar --shots /tmp/e7shots
```

Saída da rodada que gerou estas imagens:

```
  tentativa 0: selvagem 19
  tentativa 1: selvagem 16
  tentativa 2: selvagem 915 (nova)
encontros: 3 batalhas, especies [16, 19, 915]
  novas (>= 387): [915]
  Gen 9 (>= 906): [915]
tentando capturar a especie 915...
  time antes: 1 -> depois: 2
  time final: [700, 915]
APROVADO
```

O time final `[700, 915]` é Sylveon (700, o inicial da prova) + **Lechonk (915)**,
lido de `gPlayerParty` na EWRAM — não da mensagem na tela.

| arquivo | frame | o que mostra |
|---|---|---|
| `01_lechonk_selvagem_rota1.png` | encontro | **LECHONK (Gen 9, #915)** selvagem na Rota 1, nível 3 |
| `02_pokeball_selecionada.png` | 1500 | bolsa na pocket **POKé BALLS**, "POKé BALL is selected" |
| `03_gotcha_lechonk_capturado.png` | 2400 | **"Gotcha! LECHONK was caught!"** |
| `04_ficha_dex_lechonk.png` | 2900 | **ficha da dex: `No915 LECHONK`, "Hog POKéMON", HT 1'08", WT 22.5 lbs.** e o texto da espécie |
| `05_teclado_apelido.png` | 3300 | teclado "LECHONK's nickname?" (é aqui que o roteiro fecha com START) |
| `06_de_volta_rota1.png` | 4400 | de volta à grama da Rota 1, time com 2 Pokémon |

## Defeito da ficha da dex — corrigido nesta rodada

Antes, ao capturar uma espécie nova, a ficha abria com `No800`, nome `??????????` e
`HT/WT ???`. A causa **não** era `gPokedexEntries` (que já tinha #915 = "Hog", 5 dm,
102 hg): era `src/data/pokemon/pokedex_categories.h`, as páginas de **habitat** da dex,
que continuavam com as 386 espécies vanilla. `DexScreen_LookUpCategoryBySpecies(915)`
não achava a espécie e devolvia "não achei" **sem** mexer em
`category`/`pageNum`/`categoryCursorPosInPage` — a tela desenhava a espécie que estava
no cursor antigo.

Conserto: `scripts/firered/gen_pokedex_categories.py` gera as páginas que faltavam
(`pokedex_categories_gen4_9.h`), sem tocar nas 386 vanilla. O habitat das novas é uma
**HIPÓTESE**: um classificador Naive Bayes treinado nos tipos das 386 vanilla (o jogo
não tem habitat oficial depois da Gen 3). Lechonk caiu em Grassland, junto de Fuecoco.

Conferência no binário: `verificar_rom.py` agora percorre os ponteiros de
`gDexCategories` no ROM e exige as 1025 espécies:
`E7 ok: ... as 4 ordens da dex e as 9 páginas de habitat com 1025 entradas`.


---

## Onda 2b — treinadores com espécies Gen 4-9 (2026-10-24)

ROM: md5 **`a44251245f49682a6c56396f32d90b14`** (inclui também os habitats da onda 2a).

`scripts/firered/gen_trainer_parties.py` (self-test 7 casos) troca **481 dos 1650
slots** de treinador por espécies novas (Gen 4: 108, 5: 163, 6: 59, 7: 58, 8: 20,
9: 73). Política: slot 0 nunca muda; times de golpes à mão (líderes, rival,
Elite 4) ficam intactos; a substituta tem o mesmo tipo primário e o BST mais
próximo (teto 570), escolhida por hash determinístico. A semelhança de
tipo/força é HIPÓTESE de balanceamento; o funcionamento em jogo é CONFIRMADO:

| arquivo | frame | o que mostra |
|---|---|---|
| `07_rick_enviou_kricketot.png` | 1400 | **"BUG CATCHER RICK sent out KRICKETOT!"** na Floresta de Viridian |
| `08_batalha_kricketot_gen4.png` | 1600 | batalha contra KRICKETOT (#401, Gen 4) nível 6 |
| `09_floresta_apos_vitoria.png` | 3000 | de volta ao overworld ao lado do Rick depois da vitória |

Log da RAM durante a luta: `b1 esp= 13` (Weedle, 1º mon vanilla intacto) e depois
`b1 esp= 401 nv= 6 tipos=(6, 6)` — KRICKETOT entregue pelo próprio jogo.

Conferência no binário: `verificar_rom.py` percorre `gTrainers` (passo medido no
ROM: entradas de 8 B/16 B, espécie no offset 4) e exige espécies válidas e o
mesmo número de trocas marcado no fonte (`GERADO(e7-treinadores)` = 481).

Como chegou lá (reprodutível): `nav.py --rota` com fuga automática de batalha
(`gMain.inBattle`, ciclo B,B,DOWN,RIGHT,A) — Rota 1 → Viridian (var `0x4051`=2
destrava o velhinho) → Rota 2 → Floresta, 38 waypoints, e a visão do Rick
dispara a batalha de treinador de verdade (nada é injetado no time dele).


---

## Nota sobre cores (2026-10-24)

Os PNGs deste relatório foram **regerados** depois de um conserto no conversor
de cores do `nav.py`: o framebuffer do core é **RGB565** (medido: branco puro =
`0xFFFF`), mas o vermelho era lido deslocado 1 bit (bits 10-14 em vez de
11-15). O bit alto do verde vazava para o vermelho e as capturas saíam
pastel/rosadas — era defeito **da régua, não do jogo** (a ROM sempre esteve
certa; paletas no ROM conferidas pela E6). Relatórios antigos (E1-E6) ainda têm
o tom antigo; continuam válidos como prova de comportamento (texto, formas,
HP), só a cor está deslocada.


---

## Onda 2c — evoluções modernas no motor vanilla (2026-10-24)

ROM desta onda: md5 `7fcfdf53cc541f8dd571436ba8887759`.

**O problema:** até a onda 2b só evoluções por nível funcionavam de fato — as
10 `EVO_ITEM` geradas tinham **item 0** (nunca disparam), 7 eram `EVO_TRADE`
(impossível jogando solo), amizade saía como "nível 0" (formato novo do RHH:
`EVO_LEVEL 0` + `CONDITIONS({IF_MIN_FRIENDSHIP,...})`), e **nenhuma evolução
cruzada** existia (Magneton→Magnezone, Eevee→Leafeon... o gerador só olhava
espécies 387+; os `#if P_GEN_x_CROSS_EVOS` dentro de `EVOLUTION(...)` ainda
engoliam Kleavor, Sylveon, Gallade e Froslass).

**Política de mapeamento (gen_species_data.py, auditável no header gerado):**

| método moderno | vira no FireRed |
|---|---|
| amizade (qualquer variante, incl. Sylveon) | `EVO_FRIENDSHIP` (limiar 220 do motor) |
| pedra que existe (Fire/Water/Thunder/Leaf/Moon/Sun) | `EVO_ITEM` com a própria pedra |
| pedra moderna | pedra equivalente: Dusk→Moon, Dawn/Shiny→Sun, Ice→Water |
| troca (com ou sem item) | `EVO_LEVEL 37` |
| nível com condição (hora, gênero, clima...) | `EVO_LEVEL` no mesmo nível |
| sem equivalente (golpe, local, 999 moedas...) | `EVO_LEVEL 36` |

Conflitos resolvidos por linha: alvo duplicado fica com a entrada "melhor"
(Magneton tem Magnezone por local E por Thunder Stone → fica a pedra); gatilho
repetido degrada para nível (Eevee já usa Water Stone p/ Vaporeon → Glaceon
vira nível 36). Linhas vanilla são re-emitidas INTACTAS na frente dos anexos
cross-gen (conteúdo original preservado). `EVOS_PER_MON` 5→8 (Eevee usa 8).

**Conferência no binário (`verificar_rom.py`, self-test 11/11):** 233 espécies
novas com evolução, zero trocas, zero item 0; amostras Eevee (8 entradas),
Magneton, Kirlia→Gallade (Sun Stone), Riolu, Boldore conferidas byte a byte.

**Prova em jogo (as 3 mecânicas):**

| # | imagem | o que mostra |
|---|---|---|
| 10 | `10_thunderstone_no_magneton.png` | THUNDERSTONE usada no MAGNETON (bolsa vanilla) |
| 11 | `11_magneton_virou_magnezone.png` | "Congratulations! Your MAGNETON evolved into MAGNEZONE!" (RAM: 82→462) |
| 12 | `12_riolu_virou_lucario_amizade.png` | amizade 252 + level up → LUCARIO (RAM: 447→448) |
| 13 | `13_boldore_virou_gigalith_nv37.png` | troca mapeada p/ nível: Boldore nv37 → GIGALITH (RAM: 525→526) |

Nota de fidelidade vanilla: o FRLG só permite evoluir para fora da dex de
Kanto depois da **National Dex** (guardas em `pokemon.c`/`evolution_scene.c`/
`party_menu.c`, mantidas intactas) — igual ao jogo original com Gen 2. O
savestate de prova já tem a Nacional ligada; o jogador real a recebe do Oak.
