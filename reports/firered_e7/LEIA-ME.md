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
