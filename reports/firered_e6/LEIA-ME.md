# E6 — Sprites, ícones, pegadas e cries das 639 espécies novas

> **O que mudou na prática:** até a E5, o Orthworm existia em batalha como
> **nome + barra de HP + mensagem** e um espaço vazio no lugar do bicho. Os
> screenshots da E5 mostram isso (`reports/firered_e5/02_earth_eater.png` tinha
> a mensagem do Earth Eater e nenhum Pokémon). Agora ele aparece — em batalha,
> no menu do time e na ficha.

| item | valor |
|---|---|
| ROM | `pokefirered_modern.gba` |
| md5 | `60b49820a269a8b94f46702f702dd337` |
| sha256 | `501748fd24a677dc13f74c816e84d6581b0ad050f1c74fb73a107a33088103c0` |
| Tamanho | 16 777 216 B no arquivo (ROM usada **11 429 664 B**, 34,06 %) |
| EWRAM | 259 358 B (98,94 %) — +4 B sobre a E5 |
| Espécies com gráfico | **639 de 639** (antes: 0) |

---

## 1. O que a etapa entrega

| arquivo | o que tem |
|---|---|
| `graphics/pokemon/<pasta>/` | 639 pastas novas com `front.png`, `back.png`, `normal.pal`, `shiny.pal`, `icon.png`, `footprint.png` |
| `src/data/graphics/pokemon_gen4_9.h` | os `INCBIN` dos assets (`.4bpp.lz`, `.gbapal.lz`, `icon.4bpp`, `footprint.1bpp`) |
| `include/graphics_gen4_9.h` | os `extern` correspondentes |
| `front_pic_table.h`, `back_pic_table.h` | `SPECIES_SPRITE(ORTHWORM, gMonFrontPic_Orthworm)` ×639 (frente e costas) |
| `front_pic_coordinates.h`, `back_pic_coordinates.h` | `.size` (largura×altura em tiles) e `.y_offset` de cada sprite |
| `palette_table.h`, `shiny_palette_table.h` | paleta normal e shiny |
| `footprint_table.h` | pegada da ficha |
| `src/pokemon_icon.c` | `gMonIconTable` + `gMonIconPaletteIndices` (ícone do time) |
| `sound/cry_tables.inc` | `cry` e `cry_reverse` para as 639 posições |

Também entra o **port do `u16`** (`apply_e6_port.py`), que é pré-requisito e está
explicado na seção 3.

## 2. Como foi provado (tudo conferido no binário e na tela)

| # | prova | evidência |
|---|---|---|
| 1 | **O Orthworm selvagem aparece em batalha** e usa o próprio sprite | `01_sprite_orthworm_bulldoze.png` — `SYLVEON used BULLDOZE!` com o Orthworm desenhado |
| 2 | **O Sylveon aparece de costas** (sprite traseiro, o outro conjunto da tabela) | `03_sylveon_de_costas.png` |
| 3 | **A habilidade e o sprite juntos**: `Wild ORTHWORM's EARTH EATER made BULLDOZE useless!` com as duas imagens na tela; HP 84→84 | `02_earth_eater_com_sprite.png` |
| 4 | **Ícone no menu do time** (Orthworm, Pecharunt, Sylveon) | `04_icone_menu_time.png`, `08_icone_pecharunt.png`, `09_icone_sylveon.png` |
| 5 | **Ficha completa** com sprite de frente, tipo e dex | `05_resumo_orthworm.png` (STEEL), `06_resumo_turtwig.png` (GRASS), `07_resumo_garchomp.png` (DRAGON/GROUND) |
| 6 | **As 639 apontam para gráfico de verdade no ROM** | `verificar_rom.py`: `E6 ok: 639 espécies com sprite, costas, paleta, shiny, ícone, pegada e coordenada (passo 4 B)` |
| 7 | **Sem regressão nas mecânicas** | `prova_habilidades_e5.py`: 84→72 / 84→84 / 84→0 (igual à E5); `prova_golpes_e4.py`: 3/3 rodadas |

A prova 6 lê o **ponteiro de cada entrada** das 6 tabelas dentro do ROM e exige
que caia em `0x08000000-0x09FFFFFF`. Antes da E6 todos eram `0x00000000`
(`{NULL, 0, 0}`), que é justamente o "espaço vazio" que aparecia na tela.

## 3. As decisões que valem registro

### 3.1 O `u8` da habilidade não cabia mais — e truncava em silêncio

Esta é a descoberta mais importante da etapa, e ela **não** é sobre sprites.

A E5 deixou 321 habilidades e ordenou os IDs **por uso** para que as "usadas"
cabessem abaixo de 256 (o campo `abilities[2]` era `u8`). Isso funcionou porque o
parser não enxergava as espécies montadas por macro. Quando ele passou a
enxergar, o conjunto de usadas subiu de 172 para **229** — e 18 espécies ficaram
com o byte truncado:

| espécie | habilidade certa | o que ficou gravado |
|---|---|---|
| PALAFIN | `ZERO_TO_HERO` (299) | 43 |
| TATSUGIRI | `COMMANDER` (300) | 44 |
| TERAPAGOS | `TERASHIFT` (309) | 53 |

O `verificar_rom.py` acusou as 18 na hora. A correção definitiva foi **alargar o
campo para `u16`** (`apply_e6_port.py`), o que é seguro porque a habilidade
**não é gravada no save**: `GetMonAbility()` deriva de
`gSpeciesInfo[species].abilities[abilityNum]` a cada batalha.

O problema não era só o campo. Havia uma **corrente de `u8`** por onde o ID
passava, e cada elo só se revelava num caminho diferente do motor:

| símbolo | onde | o que quebrava |
|---|---|---|
| `SpeciesInfo.abilities[2]` | `pokemon.h` | dado da espécie (o truncamento acima) |
| `BattlePokemon.ability` | `pokemon.h` | a habilidade dentro da batalha |
| `GetAbilityBySpecies`/`GetMonAbility` | `pokemon.h`, `pokemon.c` | o retorno truncava antes de chegar |
| `AbilityBattleEffects(..., u16 ability, ...)` | `battle_util.h`, `battle_util.c` | **o `switch` das habilidades** — com ID 298 truncado para 42, o Earth Eater simplesmente não era encontrado |
| `gLastUsedAbility` | `battle.h`, `battle_main.c` | é o valor que o `case ABILITYEFFECT_ABSORBING` lê |
| `BattleMsgData.lastAbility`, `abilities[4]` | `battle_message.h` | nome da habilidade na mensagem |
| `sBattlerAbilities[]` | `battle_message.c` | idem |
| `BattleHistory.abilities[]` | `battle.h` | AI |
| `RecordAbilityBattle` | `battle_ai_script_commands` | idem |
| `monAbility`, `abilityAtk`, `ability` locais | 4 arquivos | Skill Swap, Heal Bell, encontro |

**Como esse erro se apresentou:** a prova da E5, que passava, começou a
**reprovar** depois dos sprites (84→0 em vez de 84→84). O sprite não tinha
culpa — o port do `u16` tinha esquecido o parâmetro do `AbilityBattleEffects`.
A lição: *uma prova que passa e depois falha é a ferramenta mais valiosa que
existe; o instinto de "foi o sprite" custou 2 builds.*

### 3.2 `anim_front.png` é 64×**128**: o corte tem de ser no PNG

419 das 639 espécies do RHH só têm `anim_front.png` (dois quadros, 64×128). O
FireRed lê 64×64. O corte é feito **no PNG**, com o módulo novo
`png_indexado.py`, porque o build converte o PNG na hora
(`%.4bpp: %.png`) — cortar o `.4bpp` depois não adianta.

### 3.3 O ícone: 6 paletas no RHH, 3 no FireRed (e são as mesmas 0-2)

O FireRed tem 3 paletas de ícone; o RHH tem 6. Comparei as cores: as `pal0..2`
do RHH são **idênticas** às 3 do FireRed. Então para índice 0-2 basta copiar; as
**12** espécies com índice 3-5 têm as cores remapeadas para a paleta mais
próxima (perde fidelidade, não quebra).

### 3.4 A pasta do gráfico não é sempre o nome da espécie

`TATSUGIRI_CURLY` mora em `tatsugiri`, `OGERPON_TEAL` em `ogerpon`,
`AEGISLASH` em `aegislash` (e a forma padrão é `_SHIELD`, não `_BLADE`). A busca
é: nome exato → nome da família (sem sufixo) → prefixo mais longo. Sem isso 61
espécies ficavam sem sprite.

### 3.5 `##` do preprocessador vindo do RHH

O RHH escreve `gMonFrontPic_Vivillon ##PokeBall`: o `##` é concatenação **dentro
da macro da família**, e o parser devolve o texto cru. Escrito num header comum
dá `stray '##' in program` — **8 mil erros** e o `data.o` saía com 664 bytes.

### 3.6 O cry é provisório (e está dito)

O formato de importação de cry do FireRed é outro e são 639 amostras. Nesta onda
cada espécie nova recebe o cry da espécie de **mesmo tipo primário** com a dex
mais próxima (≤386). **Não é o cry oficial.** Está listado como pendência.

## 4. Armadilhas que custaram tempo

1. **O `make` não acusou o `data.o` vazio.** A regra do Makefile termina em
   `| cat -`, e o `cat` retorna 0 mesmo quando o `cc1` falha. O resultado é um
   `data.o` de 664 bytes, um link com 10 mil `undefined reference` e um
   `EXIT=2` que aponta para o lugar errado. **Sempre conferir o tamanho do
   `data.o`** (~377 KB) quando aparecerem símbolos `gMon*` indefinidos.
2. **`make -j2` + arquivos gerados no mesmo segundo.** Um `.o` pode sair com
   mtime igual ao do header gerado e não ser recompilado. Quando o resultado
   parecer impossível, `make clean`.
3. **O último elemento do array não tem vírgula.** Inserir depois dele sem pôr
   a vírgula dá `assignment of read-only location` (o compilador acha que o
   próximo token é um índice).
4. **O include do arquivo de INCBIN tem de ser relativo ao próprio arquivo.**
   `src/data.c` e `src/graphics.c` incluem `data/graphics/pokemon.h`: um caminho
   `data/graphics/...` resolve para dentro de `src/data/graphics/` a partir do
   segundo. Correto: `#include "pokemon_gen4_9.h"`.
5. **INCBIN duplicado.** O fallback aponta para `gMonFootprint_Bulbasaur`, que
   **já existe** no clone. Gerar outro com o mesmo nome dá `redefinition` e o
   linker perde a tabela inteira. O gerador agora consulta o que o clone já
   define antes de emitir.
6. **`struct MonCoords` tem 2 bytes de campo e 4 no ROM.** O GCC do build usa
   `-mabi=apcs-gnu` (struct ocupa múltiplo de 4); o `offsets.py` compila com
   outro compilador e responde 2. O `verificar_rom.py` agora **mede o passo no
   ROM** (2/4/8) em vez de supor — mesma técnica já usada para os golpes.
7. **O `nav.py` lia o HP no lugar errado.** `BattlePokemon.ability` virou `u16`,
   então `hp`/`level`/`maxHP` andaram 2 bytes e o passo foi de 0x58 para 0x5C.
   Agora o `nav.py` aceita `--offsets` (JSON do `offsets.py`) e o
   `PF_OFFSETS`; sem ele, usa o layout antigo.

## 5. Limitações honestas

| item | estado |
|---|---|
| Cries oficiais das 639 | **não** — provisório por tipo (seção 3.6) |
| Animação de entrada/ataque própria | **não** — só o primeiro quadro do `anim_front` |
| Formas alternativas (Alolan, Hisuian, Megas…) | **não** — só a forma padrão de cada espécie |
| Sprites de overworld (seguir o jogador) | **não** — o FireRed não usa |
| EWRAM | 98,94 % — **restam ~2,7 KB**; a E7 precisa olhar isso antes de crescer |

## 6. Como reproduzir

```bash
# 1. ambiente (inclui E1…E6 e compila)
bash scripts/firered/setup_ambiente.sh

# 2. só a parte da E6, num clone já preparado
python3 scripts/firered/apply_e6_port.py --pokefirered /tmp/pokefirered
python3 scripts/firered/gen_sprite_data.py --pokefirered /tmp/pokefirered \
    --reference /tmp/fre --write
python3 scripts/firered/gen_sprite_data.py --pokefirered /tmp/pokefirered \
    --reference /tmp/fre --check      # falha se alguém editar o gerado

# 3. build
cd /tmp/pokefirered && make -j2 MODERN=1 CC1_DAEMONS=2

# 4. conferência no binário (não confia no compilador)
python3 scripts/firered/verificar_rom.py --pokefirered /tmp/pokefirered

# 5. prova em jogo
export MGBA_CORE=/tmp/mgba-0.10.5/build/mgba_libretro.so
python3 scripts/firered/offsets.py --pokefirered /tmp/pokefirered \
    --json > /tmp/pf_offsets.json
python3 scripts/firered/prova_habilidades_e5.py --prova --shots /tmp/e6shots
```

## 7. Erros de método (para não repetir)

1. **Não testei o pipeline num `/tmp` limpo antes de rodar.** O
   `setup_ambiente.sh` quebrou na E5 porque `src/data/abilities.h` não estava na
   lista de sparse-checkout do RHH. Agora existe o `checar_dependencias.py`, que
   roda no passo 0 e falha em 1 s (antes: 10 min).
2. **Confiei no `EXIT=0` do `make`.** Ver a armadilha 1: o `| cat -` mascara o
   erro do compilador. O `settings` do build agora confere o `.o` gerado.
3. **Achei que o problema era o sprite.** Era o `u8` do parâmetro do
   `AbilityBattleEffects`. Quando uma prova antiga quebra, o primeiro suspeito é
   **o que mudou por último no motor**, não o que está sendo testado.
4. **`offsets.py` sem `-mabi=apcs-gnu`.** Medir struct com a ABI errada é pior
   que não medir: o número parece válido. A regra do projeto (medir no ROM) já
   existia; foi ignorada aqui por uma struct de 2 bytes.
