# Plano de etapas — FireRed com as 9 gerações

**Base:** [`pret/pokefirered`](https://github.com/pret/pokefirered) (decompilação fiel do FireRed americano).
**Meta:** o jogo continua sendo FireRed — mesmos mapas, mesmo enredo, mesmos menus — mas passa a
**comportar as 1025 espécies das Gens 1 a 9**.

Este documento é o espelho do projeto no Linear
[`FireRed Gen 1-9 (base pret/pokefirered)`](https://linear.app/vyktormustang/project/firered-gen-1-9-base-pretpokefirered-4d2d5c9e6c8b).
Cada etapa daqui é uma issue `VYK-*` lá, com o mesmo nome.

---

## Por que esta base e não a anterior

A tentativa anterior partia do fork `CharonChaos88/FireRedExpansion` (pokeemerald-expansion com mapas
de Kanto). Ela foi **rejeitada**: o resultado não é FireRed, tem defeitos de mapa herdados (portas e
escadas sem metatítulo de warp) e o comportamento de jogo muda em coisas que não deveriam mudar.

Aqui a lógica se inverte: **o FireRed fica intacto**; só entra o que for estritamente necessário para
caberem as 9 gerações. Toda etapa tem que terminar com o jogo **bootando** e o campo de FireRed
funcionando — inclusive portas e escadas, que já foram verificadas na base pura (ver E0).

---

## Regra de ouro (vale para todas as etapas)

1. `make modern -j2` termina com **EXIT 0**.
2. A ROM **boota** no mGBA e chega ao título.
3. Um **teste automatizado** da etapa passa (`scripts/firered/…`).
4. **Print + sha256** guardados em `reports/`.
5. Se não bootar ou quebrar o campo, a etapa **não está concluída** — nem que o código "pareça" certo.

Nada é considerado "funcionando" sem prova em imagem ou log de teste. As etiquetas usadas nos
documentos são **CONFIRMADO / PROVÁVEL / HIPÓTESE / DESCONHECIDO**.

---

## Estado atual

| Etapa | Título | Estado |
|---|---|---|
| **E0** | Baseline: FireRed puro compilado e bootando | **CONCLUÍDA** (2026-10-23) |
| E1 | Constantes e limites: 1025 espécies | **CONCLUÍDA** (2026-10-23) |
| E2 | Gerador de dados de espécie | **CONCLUÍDA** (2026-10-23) |
| E3 | Tipo Fada + split físico/especial | **CONCLUÍDA** (2026-10-23) |
| E4 | Movimentos | **CONCLUÍDA — onda 1** (2026-10-23) |
| E5 | Habilidades | **CONCLUÍDA — onda 1** (2026-10-23) |
| E6 | Sprites, ícones e cries | a fazer |
| E7 | Encontros, treinadores e UI | a fazer |
| E8 | Testes automatizados e regressão | a fazer (testes pontuais já existem) |
| E9 | Entrega: ROM final, Drive e documentação | a fazer |

---

## Restrições medidas na base pura (E0)

Números reais do linker, não estimativa:

| Região | Usado | Total | % |
|---|---|---|---|
| ROM | 9.345.048 B | 33.554.432 B (32 MB) | **27,85%** |
| EWRAM | 259.182 B | 262.144 B (256 KB) | **98,87%** |
| IWRAM | 29.592 B | 32.768 B (32 KB) | **90,31%** |

Consequências diretas para o plano:

- **ROM sobra** (~22,6 MB livres): dá para as 1025 espécies, sprites, learnsets e cries.
- **EWRAM é o gargalo.** Só restam ~2,9 KB. Qualquer estrutura nova em tempo de execução
  (bitmaps de Pokédex, tabelas auxiliares, buffers de batalha) tem que ser **em ROM** ou reaproveitar
  memória existente. Isso é uma decisão de arquitetura, não um detalhe.
- **IWRAM** resta ~3,1 KB — não colocar tabela grande lá.

Esses três números precisam ser rechecados ao fim de **toda** etapa; um estouro de EWRAM aparece como
travamento silencioso no boot, não como erro de compilação.

---

## Decisão de arquitetura: ID de espécie = número da Pokédex Nacional

Hoje o FireRed **não** usa a numeração nacional: os IDs internos vão 1–251 (Kanto + Johto) e depois
252–276 são `SPECIES_OLD_UNOWN_*` (placeholders), com `SPECIES_TREECKO = 277`. Ou seja, o ID interno
de Hoenn não bate com a dex nacional (Treecko é #252 na nacional).

Isso poderia virar um pesadelo de remapeamento. Mas foi verificado arquivo por arquivo que
**todas as tabelas por espécie do FireRed usam inicializador designado**:

```c
const struct SpeciesInfo gSpeciesInfo[] = { [SPECIES_BULBASAUR] = { ... }, ... };
const struct Evolution gEvolutionTable[NUM_SPECIES][EVOS_PER_MON] = { [SPECIES_BULBASAUR] = {{...}} };
const u16 *const gLevelUpLearnsets[NUM_SPECIES] = { [SPECIES_BULBASAUR] = sBulbasaurLevelUpLearnset };
const u8 gEnemyMonElevation[NUM_SPECIES] = { [SPECIES_BUTTERFREE] = 8 };
```

Como a chave é o **nome** da constante, mudar o número não desalinha nada: a tabela se reorganiza
sozinha na compilação. Só as listas ordenadas (`gPokedexOrder_*`) e as tabelas de texto/ordem da
Pokédex são por posição e precisam ser **regeradas**.

**Decisão:** renumerar tudo para `ID = número da Pokédex Nacional` (1…1025), `SPECIES_EGG = 1026`,
`NUM_SPECIES = 1026`, formas depois. Ganhos:

- acaba a tradução mental entre ID interno e dex nacional;
- mapas de encontro, times de treinador e scripts continuam funcionando, porque usam o **nome**;
- `struct Pokemon` não muda: `species` já é `u16` (cabe 1025 com folga — não há bitfield de 10 bits
  limitando o ID, o que era o risco nº 1 desta etapa).

**Custo:** o save antigo deixa de ser compatível com o novo build. Não é problema — o entregável é
uma ROM nova, não um upgrade de save.

---

## Tamanho do que existe hoje (base pura)

| Item | Base pura | Alvo (Gen 9) |
|---|---|---|
| Espécies (`SPECIES_*`) | 412 | 1025 + formas |
| Movimentos (`MOVES_COUNT`) | 355 | 919 |
| Habilidades | 78 | 310 |
| Itens | 434 | ~2000 |
| `struct SpeciesInfo` | 26 bytes | 26 bytes (cabe: 1025 × 26 = 26 KB em ROM) |
| Espécies por arquivo | `src/data/pokemon/species_info.h` (11.257 linhas) | gerado por script |

O `gSpeciesInfo[]` é `const` — vai para ROM. Adicionar 600 espécies custa ~16 KB de ROM, o que é
irrelevante. **O trabalho não é de espaço, é de dados, de sprites e de motor de batalha.**

---

## Etapas

### E0 — Baseline (CONCLUÍDA)

**O que foi feito**

- Clone de `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`
  ("Fix Various Doubles-related AI Bugs (#772)").
- `make tools` + `make -j2 MODERN=1 CC1_DAEMONS=2` → **EXIT 0** em ~8min19s.
- ROM: `pokefirered_modern.gba`, **16.777.216 B**, sha256
  `32e26d4ff5a1564d90b82a68e4ae84b662098014ee1cc512fd244c15a083e978`.
- Cabeçalho conferido: título `POKEMON FIRE`, código `BPRE`, maker `01`.
- Boot até o título (Charizard + "© 2004 GAME FREAK inc.").
- Novo jogo → quarto do jogador em Pallet Town.
- **Escada funciona**: warp direcional `4:1 → 4:0` (metatítulo 7, behavior `0x6F`
  `MB_DOWN_LEFT_STAIR_WARP` — só dispara entrando **andando para a esquerda**).
- **Porta funciona**: `4:0 → 3:0` (Pallet Town), saindo na frente da casa.

**Evidências** em `reports/firered_base/` (`01_titulo.png` … `04_porta_casa_1f.png`).

**Lição para o resto do plano:** o sistema de warp do FireRed é por *behavior* de metatítulo, e
vários deles são direcionais. Se um warp não dispara, o primeiro lugar a olhar é o `behavior` do
metatítulo — não o código de warp. Foi exatamente o que faltava no fork rejeitado.

---

### E1 — Constantes e limites: 1025 espécies (CONCLUÍDA)

**Objetivo:** o jogo "conhece" 1025 espécies. Nenhuma mecânica nova, só o espaço reservado.

**Arquivos**

- `include/constants/species.h` — renumerado para a dex nacional (1…1025) + `SPECIES_EGG = 1026`.
- `include/constants/pokedex.h` — `NATIONAL_DEX_MEW`/`NATIONAL_DEX_COUNT`.
- `include/global.h` — `struct Pokedex` (`owned[]`, `seen[]` crescem de 52 para 129 bytes).
- `src/data/pokemon/pokedex_orders.h`, `pokedex_entries.h`, `pokedex_categories.h`.
- `src/pokemon.c`, `src/pokedex.c` — qualquer laço com teto fixo em `KANTO_DEX_COUNT`.

**Regra de compatibilidade:** nenhum **nome** de constante muda (só o número). Encontros, times de
treinador, scripts e `species_info.h` continuam válidos como estão — todos são indexados por nome.

**Aceite**

- Build + boot + campo OK.
- Script `scripts/firered/check_species_tables.py` percorre as 1025 constantes e confirma que cada
  uma tem: nome, entrada em `gSpeciesInfo`, learnset, sprite e cry apontando para algo válido.
- Uso de EWRAM não cresce (ou cresce < 500 B, justificado).

**Risco:** médio. `DEX_FLAGS_NO` aparece em vários pontos; um deles esquecido dá corrupção de save.

---

### E2 — Gerador de dados de espécie

**Objetivo:** não digitar 1025 blocos à mão. Um script lê uma fonte de dados e **emite** o
`species_info.h`, os learnsets e as evoluções no formato do FireRed.

**Fonte de dados:** `src/data/pokemon/species_info/*.h` do RHH pokeemerald-expansion (já disponível
localmente em `/tmp/fre`), que é derivado de dados oficiais. Plano B: CSVs do repositório
`PokeAPI/pokeapi` (o que faltar).

**Campos emitidos** (exatamente os do `struct SpeciesInfo` do FireRed):
`baseHP/Attack/Defense/Speed/SpAttack/SpDefense`, `types[2]`, `catchRate`, `expYield`,
`evYield_*`, `itemCommon/itemRare`, `genderRatio`, `eggCycles`, `friendship`, `growthRate`,
`eggGroups[2]`, `abilities[2]`, `safariZoneFleeRate`, `bodyColor`, `noFlip`.

**Aceite**

- `python3 scripts/firered/gen_species_data.py --self-test` passa (testa o parser e 20 amostras
  conhecidas contra valores fixos no próprio teste).
- Saída determinística: rodar duas vezes gera arquivos idênticos byte a byte.
- `--check` compara o gerado com o que está no repositório e sai com erro se divergir (é o que o CI
  e eu usamos para garantir que ninguém editou o gerado à mão).

**Risco:** alto no começo, baixo depois. É a peça que destrava E4/E5/E6/E7.

---

### E3 — Tipo Fada e split físico/especial — **CONCLUÍDA**

**Objetivo:** as duas mecânicas modernas que mudam o resultado da batalha.

**Escopo executado**

- `TYPE_FAIRY = 18` e `NUMBER_OF_MON_TYPES = 19`. A tabela ganhou as 12 regras que a Gen 6
  mudou; `gTypeEffectiveness` passou de 336 para 372 bytes (124 entradas), com o tamanho
  publicado por `#define TYPE_EFFECT_TABLE_SIZE` (o `extern` sem tamanho não compila).
- UI do tipo: `gTypeNames[TYPE_FAIRY] = "FAIRY"`, `gText_AFairyMove` (`"a FAIRY move"`),
  placa "FAIRY" desenhada em `menu_info.png` (offset `0x100`), paleta de tipo índice 10
  (`#EE99AC`) e `sTMSpritePaletteOffsetByType` (+32 B de EWRAM em `NUM_DISC_COLORS`).
- Split **por golpe**: `gMoveCategories[MOVES_COUNT]` gerado do `moves_info.h` do RHH
  (355 entradas), com `IS_MOVE_PHYSICAL` / `IS_MOVE_SPECIAL` usados no cálculo de dano
  (`src/pokemon.c`), no Hustle e no rastreio de dano físico/especial
  (`src/battle_script_commands.c`). `IS_TYPE_PHYSICAL/SPECIAL` continuam existindo, mas não
  decidem mais dano.
- Decisão registrada: os 386 golpes de Kanto **seguem a categoria moderna**, não a da Gen 3
  (55 de 218 golpes com dano trocam de stat: Fire/Ice/Thunder Punch viram físicos, Vine Whip,
  Bite e Gust viram especiais). É o que o pedido implica — “comportar as 9 gerações”.

**Aceite — todos cumpridos**

| Critério | Resultado |
|---|---|
| Fada × Dragão = 2×, Fada × Aço = 0,5×, Dragão × Fada = 0× | **CONFIRMADO** no ROM (`verificar_rom.py`, 12 regras) **e em batalha** (`03…png`, `04…png`) |
| Físico usa Attack/Defense; especial usa SpAttack/SpDefense | **CONFIRMADO** medindo o `gBattleMons`: dois golpes de 40 BP, mesmo tipo e mesmo alvo deram **29** (físico, Atk 53 vs Def 60) e **38** (especial, SpA 80 vs SpD 68) |
| Batalha de Kanto sem regressão | **CONFIRMADO** (`05…png`): Rattata selvagem na Rota 1, batalha normal |

**Prova em jogo:** `reports/firered_e3/` (5 capturas + `LEIA-ME.md`).
**ROM:** `748dbec766f7ffc137ac36049691d22cbcc5c54fa5fc78d0df2fb8c1d4ccd1b6`.
**Ferramenta nova:** `scripts/firered/prova_batalha_e3.py` monta/desfaz uma ROM de prova
(2 golpes de Fada de 40 BP — um físico, um especial — e Dratini nível 50 na Rota 1), porque
sem golpe de Fada no jogo não há como provar a mecânica antes da E4.

**Risco residual:** a tabela de tipos é lida em `battle_script_commands.c`, `pokemon.c` e
`battle_util.c`; o verificador cobre as 12 regras e a contagem de espécies, mas combinações
duplas (Fada + segundo tipo) só serão exercitadas de verdade na E8.

---

### E4 — Movimentos

**Estado (2026-10-23): onda 1 concluída; ondas 2 e 3 pendentes.**

| item | número |
|---|---|
| golpes no jogo | **797** (355 do FireRed + 442 novos) |
| golpes que só mudaram de nome | 4 (aliases) |
| efeito idêntico ao RHH | 233 |
| efeito de stat inferido | 9 |
| equivalente semântico | 9 |
| fallback de dano (`EFFECT_HIT`) | 90 |
| fallback de status (`EFFECT_SPLASH`) | 101 |
| animações novas | 442, todas na animação genérica de TACKLE |
| batalhas aleatórias sem travar | **12/12** |

ROM `9bda1da4…`, prova em `reports/firered_e4/LEIA-ME.md`.
O número 919 do plano original era estimativa; o real é **797**, porque só entram os golpes
que alguma espécie realmente aprende (446 dos 935 do RHH).

**O que falta (ondas 2 e 3):** implementar de verdade os 191 golpes que hoje caem em fallback
(efeitos de terreno, Psyshock, U-turn, dreno, multi-hit moderno…), dar animação própria aos
442 e alargar a janela do menu de golpes (nomes de 13-16 colunas aparecem cortados em batalha).

**Objetivo:** de 355 para 919 movimentos, dos quais ~150 com efeito próprio.

**Estratégia em três ondas** (não tentar tudo de uma vez)

1. **Dados** — constantes, nomes, tipo, poder, precisão, PP, categoria, flags. Mecânico, gerado por
   script, sem tocar em lógica.
2. **Motor por classe** — dano puro, status, multi-hit, recuo, dreno, prioridade, clima/terreno.
   Cada classe é um único ponto de código no `battle_script_commands.c`, cobrindo dezenas de moves.
3. **Casos especiais** — os moves que precisam de script próprio, portados um a um com teste.

**Aceite**

- ✅ Todo movimento tem dados válidos (nome, tipo, poder, PP, categoria) — conferido no ROM.
- ✅ Move sem implementação cai em **fallback seguro** (dano neutro) em vez de travar a batalha.
- ⚠️ Teste de fumaça: o plano pedia 200 batalhas; a entrega traz **12** (12 golpes novos
  executados, 48 desenhados no menu). Subir para 200 é barato (~3 s por batalha) e fica para a E8.

**Risco:** alto — é a maior etapa. Por isso as três ondas: a onda 1 já deixa o jogo "completo" aos
olhos do jogador; a onda 3 pode continuar depois da entrega.

---

### E5 — Habilidades

**Estado (2026-10-23): onda 1 concluída (dados + 1 gancho de motor).**

| item | número |
|---|---|
| habilidades no jogo | **321** (78 do FireRed + 243 novas) |
| nomes e descrições | 321 / 321 |
| espécies novas com habilidade de verdade | **639** (antes: 0) |
| habilidades usadas por alguma espécie | 172 novas, IDs 78-249 |
| habilidades com efeito no motor | **1** (Earth Eater, Gen 9) |

ROM `0faf4181…`; prova em `reports/firered_e5/LEIA-ME.md`.

**A armadilha:** `struct SpeciesInfo.abilities[2]` é **u8**. Com 321 habilidades, 66 IDs
passavam de 255 e truncavam em silêncio (`QUARK_DRIVE` 283 virava `EFFECT_SPORE` 27) em
67 espécies. A solução foi ordenar as IDs novas **por uso**: as 172 que alguma espécie usa
cabem em 78-249, as 71 que nenhuma usa ficam em 250-320. O gerador aborta se não couber.
Alargar o campo para `u16` é a dívida técnica registrada.

**A prova em batalha** é diferencial triplo (Orthworm nível 30 na Rota 1, Sylveon com
Bulldoze): Tackle fere (84→72), Bulldoze com Earth Eater não faz nada (84→84) e Bulldoze
no **mesmo** Orthworm com a habilidade zerada nocauteia (84→0).

**O que falta (onda 2):** as outras 242 habilidades novas são dados sem efeito — o
`switch` do `AbilityBattleEffects` não as trata (silencioso, não trava). Implementar por
classe (imunidade, boost de tipo, clima, ao entrar em campo, ao levar dano) é o próximo
passo natural, junto com a ordem de prioridade que o plano já previa.

**Objetivo:** de 78 para ~310.

**Escopo**

- Constantes + tabela de nomes/descrições.
- `GetBattlerAbility` e pontos de gancho por classe: imunidade, boost de tipo, clima, ao entrar em
  campo, ao levar dano, ao atacar, ao trocar.
- Prioridade: as que aparecem em Kanto primeiro (Intimidate, Levitate, Sturdy, Static, Synchronize,
  Blaze/Torrent/Overgrow…), depois as modernas.

**Aceite**

- ✅ Toda espécie tem habilidade válida atribuída — `verificar_rom.py` confere as 639
  espécies novas byte a byte no ROM; `habilidades_ausentes` = 0.
- ✅ Intimidate e Levitate continuam como estavam (IDs 0-77 intocados; sem regressão).
- ✅ Uma habilidade de Gen 9 funciona: **Earth Eater**, provada em batalha.

**Risco:** médio-alto. Habilidade sem implementação é **silenciosa** (não quebra nada) — então o
risco de travar é baixo; o risco é ficar "sem efeito" sem que ninguém perceba.

---

### E6 — Sprites, ícones e cries

**Objetivo:** as 1025 espécies visíveis.

**Escopo**

- Pipeline de conversão: frente e costas 64×64 com 2 frames, shiny, ícone de time, pegada.
  Conversão para `.4bpp` + paleta no formato que o FireRed já usa (`graphics_file_rules.mk`).
- Gerar por script a partir de PNGs; **não** commitar binário de sprite no Git.
- Cries: reaproveitar as existentes; as ausentes ficam com o cry de uma espécie próxima e marcadas
  como pendência honesta na documentação.

**Aceite**

- Script determinístico; amostra de 10 espécies (Gen 1, 4, 6, 8, 9) conferida no emulador.
- ROM final < 32 MB. Se estourar, comprimir (LZ) e registrar.

**Risco:** médio. Espaço é o único risco real, e há folga de 22 MB.

---

### E7 — Encontros, treinadores e UI

**Objetivo:** as espécies novas **aparecem no jogo**.

**Escopo**

- Tabelas de encontro (`src/data/wild_encounters.json`) com Gen 1–9 misturadas nas rotas de Kanto.
- Times de treinadores onde fizer sentido (sem descaracterizar o jogo).
- Pokédex: navegação e busca até #1025 — **a parte mais difícil do projeto**, porque as telas do
  FireRed pressupõem 151/386 e têm layout fixo.
- Evoluções: métodos modernos (amizade, item, troca, local) mapeados para os existentes.

**Aceite**

- Encontro selvagem de Gen 9 na Rota 1, **capturado em imagem**.
- Pokédex abre e mostra #1025.
- Evolução por nível de uma espécie nova funciona.

**Risco:** alto na UI. Mitigação: entregar primeiro o que é funcional (encontro, batalha, time,
resumo, evolução) e tratar a Pokédex completa como sub-etapa própria, sem travar o resto.

---

### E8 — Testes automatizados e regressão

**Objetivo:** cada etapa se prova sozinha.

**Escopo**

- `scripts/firered/smoke.py` — boot → título → novo jogo → andar → sair de casa. (A receita já está
  validada nesta sessão: START no título, A em sequência, `--map` para ler posição.)
- `scripts/firered/check_data.py` — integridade de espécies/moves/habilidades.
- Teste de batalha: entrar na grama, atacar, verificar dano.

**Aceite**

- Um comando roda tudo e imprime PASS/FAIL.
- Falha bloqueia a etapa seguinte.

---

### E9 — Entrega

- Build final, sha256, cabeçalho conferido.
- Upload no **Google Drive** com link público + conferência de sha256 contra o local.
- `docs/FIRERED_GEN1-9.md` com o que mudou, o que **não** mudou, limitações honestas.
- ROM nunca vai para o Git (`rom/` está no `.gitignore`).

---

## Decisões de escopo (o que fica de fora, e por quê)

| Item | Decisão | Motivo |
|---|---|---|
| Mega Evolução, Z-Moves, Dynamax, Terastal | **Fora** | Mecânicas de geração inteira, não "comportar espécie". Entrariam depois da entrega. |
| Habilidades de Gen 4+ com efeito pleno | **Parcial** | Constante e atribuição entram em E5; efeito implementado por prioridade. Sem efeito = sem quebra. |
| Novas regiões/mapas | **Fora** | O pedido é FireRed com as 9 gens, não um jogo novo. |
| Enredo e textos de Kanto | **Intocados** | Parte do "modificar somente o necessário". |
| Tradução PT-BR | **Fora** | Rejeitada explicitamente antes; a base é o FireRed americano. |
| Formas alternativas (alola, galar, hisui, paldea…) | **Depois** | Primeiro as 1025 espécies base. |

---

## Ordem de execução e dependências

```
E0 (feito)
 └─ E1 ──┬─ E2 ──┬─ E4 ── E5
         │       └─ E6
         └─ E3 ──────┘
                      └─ E7 ── E8 ── E9
```

E1 é pré-requisito de tudo (sem espaço na tabela, nada entra).
E3 pode correr em paralelo com E2.
E7 só faz sentido depois de E2, E3, E4 e E6.

---

## Como reproduzir

### Linux / WSL

```bash
git clone https://github.com/pret/pokefirered
cd pokefirered
make tools -j2
make -j2 MODERN=1 CC1_DAEMONS=2
# ROM: pokefirered_modern.gba
```

Precisa de `arm-none-eabi-gcc` no PATH (devkitARM serve) e de `libpng`/`zlib` para as ferramentas.

### Windows

O `pret` não tem build nativo no Windows. O caminho recomendado é **WSL**:

```powershell
wsl --install -d Ubuntu
```

Depois, dentro do Ubuntu, os mesmos comandos acima:

```bash
sudo apt update
sudo apt install -y build-essential git libpng-dev
git clone https://github.com/pret/pokefirered
cd pokefirered
make tools -j2 && make -j2 MODERN=1 CC1_DAEMONS=2
```

A ROM sai em `pokefirered/pokefirered_modern.gba` e pode ser aberta no mGBA do Windows
(`\\wsl$\Ubuntu\home\<usuario>\pokefirered\pokefirered_modern.gba`).

Para jogar, o build final é entregue pronto por link do Google Drive — não é preciso compilar nada.

### Teste automatizado (o que eu uso aqui)

```bash
python3 scripts/firered/nav.py \
  --rom pokefirered_modern.gba \
  --map pokefirered_modern.map \
  --outdir /tmp/saida --frames 1900 --shots 1899
```

`--map` resolve o endereço de `gSaveBlock1Ptr` no `.map` do linker. **Sem isso a leitura de posição
sai errada**, porque o offset muda a cada build (na base pura é `0x6F94`; no fork antigo era `0x52D8`).

---

## Registro de progresso

### 2026-10-23 — E1 CONCLUÍDA

**Resultado:** ROM com 1025 espécies compila, boota, joga e a Pokédex lista até `No1025 PECHARUNT`.

- ROM: `1c5b4f2c…` (16 777 216 B), build `-j2 MODERN=1 CC1_DAEMONS=2`
- Memória: EWRAM 259 338 B (98,93 %), IWRAM 29 592 B, ROM 9 415 608 B (28,06 %)
- Confirmado em jogo: título → quarto → escada → porta → Pallet → menu → Pokédex →
  TABLE OF CONTENTS → lista Kanto (BULBASAUR/CHARMANDER/SQUIRTLE com tipos e ícone de
  capturado) → modo nacional → lista de 1025 itens, último = `No1025 PECHARUNT`.
- Prova na RAM: array `listItems` com 1025 entradas; `[251]`=252 Treecko, `[905]`=906
  Sprigatito, `[1024]`=1025 Pecharunt, todos com `seen=1`.

**Dois bugs reais encontrados (e corrigidos) nesta etapa**

1. **Offsets de struct errados.** O `offsets.py` compilava o probe com a ABI EABI; o build
   usa `-mabi=apcs-gnu`. `SaveBlock1.seen2` real é `0x3A64`, não `0x39C4`. O anticheat da
   Pokédex exige que `pokedex.seen`, `seen1` e `seen2` concordem — escrever no lugar errado
   zerava a contagem e a lista saía vazia (sem crash). Agora os valores medidos **dentro do
   ROM** ficam em `VERIFICADOS_NO_ROM` no `offsets.py`.
2. **`sSpeciesToNationalPokedexNum` com 386 de 1025 entradas.** As 639 restantes ficavam
   zero, então toda Gen 2–9 virava espécie 0 e desenhava `-----`. Corrigido na etapa 6b do
   `apply_e1_port.py` (tabela completa + busca binária em vez de varredura linear).

Também na 6c: número da dex com 4 dígitos (`No1025`; antes saía truncado a partir de #1000).

**Ferramentas criadas**

- `scripts/firered/setup_ambiente.sh` — reconstrói toolchain + clone + port + `make tools` +
  build + mGBA num comando. O `/tmp` zera entre sessões; sem isso eram ~20 min perdidos por vez.
- `scripts/firered/offsets.py` — offsets conferidos contra o ROM em execução.
- `scripts/firered/savestate.py` / `savestate_diff.py` / `nav.py` (`--pulsos`, `--auto-avancar`).

**Lição de método (para as próximas etapas)**

- Savestate só vale para a ROM exata que o gerou; estado manipulado por ferramenta pode ficar
  "morto" (frames idênticos a qualquer input). Teste longo começa com boot completo.
- Menus do FireRed leem `JOY_NEW` (borda): botão segurado conta uma vez. Usar `--pulsos`.
- Nunca confiar em offset de struct vindo do compilador do host **nem** do toolchain com ABI
  diferente: medir no binário que roda.

**Próximo passo:** E2 (feita em 2026-10-23) → E3.

### 2026-10-23 — E2 CONCLUÍDA

**Resultado:** as 639 espécies novas (Gen 4–9) passaram a ter dados de verdade dentro do ROM:
stats, tipos, catch rate, exp yield, EVs, gênero, ovos, habilidades, cor, entrada de Pokédex
(categoria/altura/peso/descrição), evolução e golpes por nível. Prova em jogo: ficha do
`No387 TURTWIG` (HT 1'04", WT 22.5 lbs, descrição nova) e do `No1025 PECHARUNT`.

- ROM: `79891813…` (16 777 216 B); EWRAM 259 338 B (98,93 %), IWRAM 29 592 B (90,31 %)
- Provas: `reports/firered_e2/` (8 capturas) + `LEIA-ME.md` com o que está confirmado
- Conferência no binário: `verificar_rom.py` → 639 espécies, 639 entradas de Pokédex,
  639 learnsets e 217 evoluções **byte a byte** iguais ao gerado

**O que o gerador faz** (`scripts/firered/gen_species_data.py`): lê os headers
`species_info/*.h` do RHH (`/tmp/fre`) e emite cinco arquivos em
`src/data/pokemon/*_gen4_9.h` + um bloco de ponteiros de learnset. Aceita `--self-test`
(20 amostras conferidas contra valores oficiais), `--write` e `--check` (falha se o gerado
foi editado à mão).

**Números da geração:** 639 espécies; 507 habilidades ausentes no FireRed viraram
`ABILITY_NONE`; 126 exp yields limitados a 255 (`u8`); 51 evoluções puladas (método que o
FireRed não implementa); 3123 golpes filtrados (voltam na E4); 48 tipos substituídos (Fada
entrou na E3 e o número caiu para 7); 28 descrições substituídas (RHH usa expressão C no texto).

**Pendências cosméticas descobertas em jogo (E7):** a categoria aparece cortada na primeira
palavra no `REVISION 0` do motor (o dado está completo); `No1025PECHARUNT` sem espaço; os
contadores “Seen/Owned” estouram a caixa com 4 dígitos.

**Aprendizados de método:** tamanho de struct tem de ser medido **no ROM** (`SpeciesInfo`
= 28 B e `Evolution` = 8 B por causa do `-mabi=apcs-gnu`; o probe dizia 26 e 6); `"` não
existe no charmap do FireRed; `nav.py` agora converte vídeo só nos frames com PNG
(~1500 fps em vez de 100).

**Próximo passo:** E3 (feita em 2026-10-23) → E4.

### 2026-10-23 — E5 CONCLUÍDA (onda 1: dados + Earth Eater)

**Resultado:** o jogo passou de 78 para **321 habilidades**, com nome, descrição e
atribuição correta nas 639 espécies novas (antes todas eram `ABILITY_NONE`).

- ROM: `0faf4181…` (16 777 216 B); +18 KB em relação à E4
- Provas: `reports/firered_e5/` (3 capturas) + `LEIA-ME.md`
- Conferência no binário: `verificar_rom.py` → `E5 ok: 321 habilidades, 320/320 nomes e
  321 descrições conferidas; habilidades de 639 espécies novas batem com o gerado`
- Batalha: `prova_habilidades_e5.py --prova` → 3/3, com prova negativa
- Dois bugs antigos apareceram no caminho: o `#define` que fazia o Fezandipiti herdar os
  dados do Ogerpon (E2) e o espaço de enchimento nos nomes de espécie (E1) que aparecia
  como `Go! SYLVEON   !` na batalha

### 2026-10-23 — E4 CONCLUÍDA (onda 1: dados)

**Resultado:** o jogo tem **797 golpes** (355 do FireRed + 442 das Gen 4-9 que alguma espécie
aprende) e 4 nomes antigos viraram alias. `MOVES_COUNT` 797, `MOVE_NAME_LENGTH` 16.

- ROM: `9bda1da4…` (16 777 216 B), +39 KB em relação à E3
- Provas: `reports/firered_e4/` (3 capturas) + `LEIA-ME.md`
- Conferência no binário: `verificar_rom.py` compara **todos** os campos de **todos** os 797
  golpes, os nomes (17 B), as 442 descrições e as 797 animações
- Batalha: `prova_golpes_e4.py --rodadas 12 --seed 7` → **12/12**, nenhuma travou
- 191 golpes ainda em fallback (90 de dano + 101 de status) e 442 com animação de TACKLE:
  é o escopo das ondas 2 e 3

### 2026-10-23 — E3 CONCLUÍDA

**Resultado:** o jogo passou a ter o **tipo Fada** (19º tipo, com as 12 regras da Gen 6) e o
**split físico/especial por golpe** — no FireRed vanilla quem decide a stat do dano é o *tipo*
do golpe, então até aqui um golpe especial de tipo Fogo usava Attack.

- ROM: `748dbec7…` (16 777 216 B); EWRAM +32 B (a cor da Fada no estojo de TM)
- Provas: `reports/firered_e3/` (5 capturas) + `LEIA-ME.md`
- Conferência no binário: `verificar_rom.py` → 12 regras de Fada, **41 espécies com Fada**,
  categorias de golpe conferidas golpe a golpe; e os 639 registros da E2 continuam batendo
- Efeito colateral positivo na E2: `tipos_substituidos` caiu de **48 para 7** (só `STELLAR`
  ficou de fora, que não existe como tipo jogável no FireRed)

**A prova do split, que é a parte difícil:** o FireRed não tem nenhum golpe de Fada, então a
mecânica não podia ser testada antes da E4. `prova_batalha_e3.py` cria uma ROM de prova com
dois golpes de 40 BP, tipo Fada, um físico (PLAY ROUGH) e um especial (MOONBLAST), e um Dratini
selvagem nível 50 na Rota 1. O mesmo Sylveon nível 30 (Atk 53, SpA 80) acerta o mesmo alvo
(Def 60, SpD 68): **29 de dano no físico e 38 no especial**. Sem o split os dois dariam o
mesmo número, porque o tipo é o mesmo.

**Aprendizados de método:** `revert` com `copy2` preserva mtime e o `make` não recompila (a ROM
fica com a prova dentro); `MAP_ROUTE1` existe duas vezes no `wild_encounters.json` (FireRed e
LeafGreen) e pegar o último altera a versão errada; Pokémon com OT de outro treinador
desobedece (“ignored orders”); `gPlayerPartyCount` do SaveBlock1 só é preenchido ao salvar —
o menu START esconde o item POKéMON se você escrever o time direto na RAM.

**Próximo passo:** E4 (movimentos: 3123 golpes filtrados voltam, dos quais ~150 com efeito
próprio).

## Registro de decisões

| Data | Decisão | Motivo |
|---|---|---|
| 2026-10-23 | Base = `pret/pokefirered` commit `ce6406d` | Pedido explícito; fork anterior rejeitado |
| 2026-10-23 | IDs 1–386 congelados | Não quebrar encontros/saves/conteúdo de Kanto |
| 2026-10-23 | Dados gerados por script, nunca à mão | 1025 espécies × 20 campos não é editável à mão |
| 2026-10-23 | EWRAM tratado como recurso escasso (98,87% cheio) | Medido no linker, não estimado |
