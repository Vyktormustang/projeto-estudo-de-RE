# E2 — dados das espécies 387–1025 (Gen 4–9)

**Data:** 2026-10-23
**ROM:** `pokefirered_modern.gba`, sha256
`79891813b622a46afe2761d33f219199ad86178c14861a43cb7ca23dbed4708b`
(16 777 216 B)
**Base:** `pret/pokefirered` @ `ce6406d` + port E1 (`apply_e1_port.py`) + gerado da E2
(`gen_species_data.py --write`)
**Build:** `make -j2 MODERN=1 CC1_DAEMONS=2` → EXIT 0
**Memória:** EWRAM 259 338 B (98,93 %), IWRAM 29 592 B (90,31 %)

---

## O que esta etapa entrega

Até a E1 as 639 espécies novas existiam só como **número e nome**: todas tinham
os mesmos stats zerados, sem tipos, sem learnset, sem evolução e com a entrada de
Pokédex vazia. A E2 gera esses dados a partir do `pokeemerald-expansion`
(referência RHH, a mesma usada pelas ROM hacks de Gen 9) e os injeta nas cinco
tabelas do FireRed:

| tabela                           | conteúdo gerado                                  |
|----------------------------------|--------------------------------------------------|
| `gSpeciesInfo[]`                 | stats base, tipos, catch rate, exp yield, EVs, itens, gênero, ovos, habilidades, cor |
| `gPokedexEntries[]`              | categoria, altura, peso, ponteiro de texto       |
| `pokedex_text_*`                 | descrição da Pokédex (4 linhas, charmap do GBA)  |
| `gEvolutionTable[][]`            | evolução (método, parâmetro, alvo)               |
| `gLevelUpLearnsets[]`            | golpes por nível (só os que o FireRed já conhece) |

## O que está CONFIRMADO

| # | Afirmação | Evidência |
|---|---|---|
| 1 | Compila e linka | `make -j2 MODERN=1 CC1_DAEMONS=2` EXIT 0; ROM com sha256 novo |
| 2 | 639 espécies com stats/tipos/catch/exp **no ROM** | `verificar_rom.py`: 639/639 conferidas byte a byte contra o gerado |
| 3 | 639 entradas de Pokédex no ROM (categoria, altura, peso, texto) | `verificar_rom.py`: 639/639 |
| 4 | 639 learnsets ligados na tabela de ponteiros | `verificar_rom.py`: 639/639 |
| 5 | 217 evoluções na tabela | `verificar_rom.py`: 217/217 |
| 6 | Boota e joga (título → novo jogo → quarto em Pallet) | `01_titulo.png`, `02_quarto_pallet.png` |
| 7 | Pokédex abre e lista até #1025 com **tipos** | `04_toc_1025.png`, `05_lista_1017_1025.png` |
| 8 | Ficha do TURTWIG (#387) mostra categoria, altura 1'04", peso 22.5 lbs e a descrição nova | `07_ficha_turtwig.png` |
| 9 | Ficha do PECHARUNT (#1025) mostra altura 1'00", peso 0.7 lbs e a descrição da Gen 9 | `08_ficha_pecharunt.png` |

## Detalhes que a evidência mostra (e o que fazer com eles)

1. **Categoria cortada na primeira palavra.** `07_ficha_turtwig.png` mostra
   “Tiny Pokémon” e não “Tiny Leaf Pokémon”. Não é erro de dados: o texto no ROM
   está completo (conferido). É o motor: em `REVISION == 0`
   (`src/pokedex_screen.c:2687`) o laço copia até o **primeiro espaço**
   (`CHAR_SPACE`). O build usa `GAME_REVISION=0`. A revisão 1 do jogo copia até
   `EOS` e mostraria a categoria inteira. Decisão: **não mexer no motor agora**;
   fica registrado para a E7 (UI), junto com a opção de buildar com
   `GAME_REVISION=1`.
2. **`No1025PECHARUNT` sem espaço.** O número da Pokédex passou a ter 4 dígitos
   na E1 (etapa 6c) e encosta no nome. Cosmético, também da E7.
3. **Contadores do índice (“Seen/Owned” 1025) estouram a caixa** em
   `04_toc_1025.png`: o layout original previa 3 dígitos. Cosmético, E7.

## Números do gerador (determinístico)

```
especies            639
habilidades_ausentes 507   (habilidade da Gen 4-9 que o FireRed não tem → ABILITY_NONE)
exp_limitado         126   (expYield é u8 no FireRed: min(255))
evos_puladas          51   (método de evolução que o FireRed não implementa)
golpes_filtrados    3123   (golpe que o FireRed não conhece → filtrado, volta na E4)
categoria_truncada     1
tipos_substituidos    48   (Fada/Aço-luz etc. ainda não existem → tipo substituto; E3)
descricao_substituida 28   (RHH usa expressão C no texto: SILVALLY, MINIOR…)
```

## Como reproduzir

```bash
# 1. dados (precisa do clone com a E1 aplicada e do RHH sparse em /tmp/fre)
python3 scripts/firered/apply_e1_port.py --pokefirered /tmp/pokefirered
python3 scripts/firered/gen_species_data.py --self-test
python3 scripts/firered/gen_species_data.py --write
python3 scripts/firered/gen_species_data.py --check      # falha se alguém editar o gerado

# 2. build
cd /tmp/pokefirered && make -j2 MODERN=1 CC1_DAEMONS=2

# 3. prova no binário (não confia no compilador)
python3 scripts/firered/verificar_rom.py --pokefirered /tmp/pokefirered

# 4. prova em jogo (precisa do core do mGBA)
export MGBA_CORE=/tmp/mgba-0.10.5/build/mgba_libretro.so
python3 scripts/firered/nav.py --rom /tmp/pokefirered/pokefirered_modern.gba \
  --map /tmp/pokefirered/pokefirered_modern.map --outdir /tmp/e2 --frames 40000 \
  --pulsos "8400:START,8900:START,9400:A,9800:A,10200:A" --auto-avancar 40000 \
  --shots 8200
```

## Erros de método desta etapa (para não repetir)

1. **Tamanho de struct medido no ROM, não no compilador.** O probe dizia
   `SpeciesInfo` = 26 B e `Evolution` = 6 B; o build usa `-mabi=apcs-gnu` e
   arredonda os containers de bitfield: **28 B** por espécie e **8 B** por
   evolução. Sem isso o verificador lia stats de outra espécie.
2. **`"` não existe no charmap do FireRed.** Descrição com aspas quebra o build
   (`no mapping exists for double quote`) → as aspas viram `'` no gerador.
3. **Escape de aspas antes da limpeza de escapes é desfeito.** O `\"` inserido
   no meio do texto era removido depois; o escape tem de ser o **último** passo.
4. **Fragmento de macro pode não terminar em vírgula** (`ALCREMIE_MISC_INFO`) →
   o campo seguinte se cola no anterior. Corrigido repondo a vírgula ao expandir.
5. **`level_up_learnsets.h` fecha cada entrada com `LEVEL_UP_END` sem vírgula**:
   inserir o include antes do `};` final coloca código dentro do inicializador.
   O bloco gerado vai depois dos `#define` do topo.
6. **`nav.py` gastava ~9 ms/frame convertendo o vídeo em Python** (100 fps).
   Agora converte só nos frames em que há PNG e a caixa de texto é detectada no
   buffer cru: **~1500 fps**, boot completo em ~20 s em vez de 6 min.
