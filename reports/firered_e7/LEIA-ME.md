# E7 — capturas de tela (Rota 1)

ROM: `pokefirered_modern.gba`, md5 **`fb49a1ac2c466b71504a9d7978391165`**
(16 777 216 B). Estado de partida: `/tmp/e7cap2/captura/com_bolas.bin`
(savestate da Rota 1 com 20 Poké Balls na pocket de bolas).

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
| `04_teclado_apelido.png` | 3300 | teclado "LECHONK's nickname?" (é aqui que o roteiro fecha com START) |
| `05_de_volta_rota1.png` | 4400 | de volta à grama da Rota 1, time com 2 Pokémon |

## Defeito conhecido (onda 2)

Logo depois do "Gotcha!", o jogo abre a **ficha da dex da espécie nova** e ela mostra
`No800`, nome `??????????` e `HT/WT ???`. Motivo encontrado: a ficha é aberta pelo
caminho "categoria" (`DexScreen_LookUpCategoryBySpecies`), e
`src/data/pokemon/pokedex_categories.h` — as páginas de *habitat* (Grassland, Forest…)
— **continua com as 386 espécies vanilla**. Espécie que não está em nenhuma página
deixa categoria/página/cursor com valor antigo, e a tela imprime outra espécie.
O número/altura/peso **não** vêm de `gPokedexEntries` (que já tem #915 correto:
categoria "Hog", 5 dm, 102 hg) — o problema é só a tabela de habitats não gerada.
