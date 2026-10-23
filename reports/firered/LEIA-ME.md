# Capturas — FireRed com Pokémon Gen 1–9

ROM: `pokefirered_expansion_gen1-9.gba`
sha256 `890c0d06c3cf9f3709c372f81a9d6499d3eee2d23eece08de529006556870744`

Todas as imagens foram geradas com mGBA (libretro, `scripts/expansion/boot_test.py`)
e `MGBA_CORE` apontando para o `.so` compilado localmente.

| arquivo | frame | o que mostra |
|---|---|---|
| `01_titulo_firered.png` | 8400 | tela de título **POKÉMON FIRE RED VERSION**, ©2004 Game Freak |
| `02_intro.png` | 3600 | sequência de introdução (GAME FREAK) |
| `03_quarto_pallet.png` | 42000 | **novo jogo dentro do quarto em Pallet Town**, texto “...Okay! It's time to go!” |
| `04_pallet_texto.png` | 31500 | o mesmo mapa antes, com “It's a POKéMON brand moving and delivery service.” |

| `05_encontro_starly.png` | Rota 1 | **“You encountered a wild Starly!”** — Pokémon de Gen 4 selvagem, em jogo |
| `06_batalha.png` | Rota 1 | batalha em andamento: Raticate (jogador) vs Starly selvagem |

## Como essas capturas foram feitas (reproduzível)

1. Rodar a intro e o prólogo até o quarto (`boot_test.py` / `nav.py --script`).
2. Abrir o **debug menu** com `R + START` e usar
   *Utilities → Warp to map warp* → grupo **037**, mapa **019** (Rota 1).
   (Atalho necessário porque a porta da casa é sólida — ver `docs/FIRERED.md`.)
3. Dá um Pokémon inicial pelo debug: *Give → Pokémon (Basic)*.
4. Andar até a grama (tiles em `y=6` do layout) e esperar o encontro.

Tudo isso está automatizado em `scripts/firered/nav.py`, que sabe:
ler a posição do jogador da RAM, avançar textos sozinho e dirigir o menu
numérico de warp.

## Prova dos Pokémon novos (nível de binário)

A tabela de encontro da Rota 1 foi lida direto do `.gba`, no endereço do símbolo
`sRoute1_FireRed_LandMons` do ELF:

```
slot  0: Lv3-3 SPECIES_PIDGEY
slot  1: Lv3-3 SPECIES_STARLY
slot  2: Lv3-3 SPECIES_STUFFUL
slot  3: Lv3-3 SPECIES_PIDOVE
slot  4: Lv2-2 SPECIES_PIDGEY
...
```

E a Rota 22:

```
slot  1: Lv3-3 SPECIES_PANCHAM
slot  2: Lv4-4 SPECIES_TANDEMAUS
slot  3: Lv4-4 SPECIES_CLOBBOPUS
```

Isso prova que o ROM **contém** os Pokémon das Gens 2–9 nas rotas de Kanto.
O que ainda falta fotografar é uma **batalha selvagem real** — veja
`docs/FIRERED.md`, seção “O que é PROVÁVEL”.
