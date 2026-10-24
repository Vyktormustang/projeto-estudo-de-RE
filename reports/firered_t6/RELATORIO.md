# T6 — Pokédex 100% PT-BR (1.026 descrições + 978 categorias)

Data: 2026-10-24 · ROM provada: `b144409b64e659907c8d3237c5255462` (muda a cada rebuild)

## O que foi traduzido

| Alvo | Arquivo no clone | Entradas | Dicionário |
|---|---|---|---|
| Descrições gen 1-3 (FireRed clássico) | `src/data/pokemon/pokedex_text_fr.h` | 387/387 | `traducao_dex_fr_ptbr.py` |
| Descrições gen 4-9 (espécies novas) | `src/data/pokemon/pokedex_text_gen4_9.h` | 639/639 | `traducao_dex_gen49_ptbr.py` |
| Categorias ("SEED POKéMON" → "SEMENTE POKéMON") | `pokedex_entries.h` + `pokedex_entries_gen4_9.h` | 759 únicas / 978 aplicações | `traducao_categorias_ptbr.py` |

Convenções: linhas ≤42 colunas (máx. 4), categorias ≤11 chars (`u8[12]`),
unidades imperiais convertidas para métricas (°F→graus Celsius, mph→km/h,
ft→m, lb→kg), golpes/BERRIES/POKé BALL em inglês (decisão do usuário),
espécies em CAPS, "Pokemon" sem acento no corpo do texto (limite do charmap
não atrapalha: "é" existe; grafia segue o padrão das etapas anteriores).

## Correções de ferramenta/código nesta etapa

1. **`aplicar_traducao.py`**: regex multilinha agora atravessa diretivas de
   pré-processador (`#if REVISION == 0 … #endif` em Chikorita/Tyranitar).
2. **Ajuste de código versionado** (novo bloco `AJUSTES_CODIGO`):
   `src/pokedex_screen.c` imprimia a descrição em y=8 numa janela de 56 px
   com fonte de 14 px/linha — a 4ª linha era cortada (bug herdado do port,
   visível também em inglês). Com y=0, 4×14 = 56 px cabem exatos.
3. **`verificar_rom.py`**: o decodificador lia o `charmap.txt` deixando os
   kana (seção JP) sobrescreverem os acentos PT-BR da T1 que reutilizam os
   mesmos bytes, e o regex rejeitava linhas com comentário `@ …`; a
   comparação agora também normaliza aspas curvas dos dois lados.

## Prova em jogo (mGBA headless, screenshots neste diretório)

1. `01_registro_pidgey_categoria.png` — captura real de um PIDGEY na Rota 1
   (MASTER BALL injetada via `savestate.py`): tela de registro mostra
   “POKéMON de floresta”, categoria **AVEZINHA POKéMON** e descrição PT-BR.
2. `02_habitat_campo_turtwig.png` — tela de habitats (“POKéMON de campo”)
   com TURTWIG №387 capturado (dex nacional ligada via `savestate.py dex`).
3. `03_ficha_turtwig_4linhas.png` — ficha do TURTWIG com categoria
   **Folhinha POKéMON** e descrição em **4 linhas completas** (prova do
   ajuste de código: antes a 4ª linha “murcha se ele tem sede.” sumia).

## Regressão

`bash scripts/firered/rodar_regressao.sh` → **PASS (todas as etapas)**,
incluindo `verificar_rom` na ROM real (639 espécies, stats, golpes,
evoluções, habilidades, sprites) e as provas E4/E5/E7 em jogo.

Pendências conhecidas (fora do escopo T6, vão para T8): HT/WT da ficha em
pés/libras e rótulos residuais da tela da dex em inglês de baixa visibilidade.
