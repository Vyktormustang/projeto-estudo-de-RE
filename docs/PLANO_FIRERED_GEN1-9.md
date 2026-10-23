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
| E1 | Constantes e limites: 1025 espécies | a fazer |
| E2 | Gerador de dados de espécie | a fazer |
| E3 | Tipo Fada + split físico/especial | a fazer |
| E4 | Movimentos | a fazer |
| E5 | Habilidades | a fazer |
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

### E1 — Constantes e limites: 1025 espécies

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

### E3 — Tipo Fada e split físico/especial

**Objetivo:** as duas mecânicas modernas que mudam o resultado da batalha.

**Escopo**

- `TYPE_FAIRY = 0x17`, tabela de efetividade 18×18 (`gTypeEffectivenessTable`).
- Nomes/cores de tipo na UI (`gTypeNames`, paletas) e STAB.
- Split físico/especial **por movimento**: campo na `struct BattleMove` do FireRed, preenchido a
  partir da categoria real do movimento. Movimentos que já existiam mantêm o comportamento correto
  da 3ª geração quando ele difere do moderno — decisão registrada abaixo.

**Aceite**

- Fada × Dragão = 2×; Fada × Aço = 0,5×; Dragão × Fada = 0× (teste unitário no código).
- Físico usa Attack/Defense; especial usa SpAttack/SpDefense (teste em batalha real).
- Batalha de Kanto sem regressão.

**Risco:** médio. A tabela de tipos é usada em vários pontos (`src/battle_script_commands.c`,
`src/pokemon.c`, `src/battle_util.c`).

---

### E4 — Movimentos

**Objetivo:** de 355 para 919 movimentos, dos quais ~150 com efeito próprio.

**Estratégia em três ondas** (não tentar tudo de uma vez)

1. **Dados** — constantes, nomes, tipo, poder, precisão, PP, categoria, flags. Mecânico, gerado por
   script, sem tocar em lógica.
2. **Motor por classe** — dano puro, status, multi-hit, recuo, dreno, prioridade, clima/terreno.
   Cada classe é um único ponto de código no `battle_script_commands.c`, cobrindo dezenas de moves.
3. **Casos especiais** — os moves que precisam de script próprio, portados um a um com teste.

**Aceite**

- Todo movimento tem dados válidos (nome, tipo, poder, PP, categoria).
- Move sem implementação cai em **fallback seguro** (dano neutro) em vez de travar a batalha.
- Teste de fumaça: 200 batalhas com moves aleatórios, nenhuma trava.

**Risco:** alto — é a maior etapa. Por isso as três ondas: a onda 1 já deixa o jogo "completo" aos
olhos do jogador; a onda 3 pode continuar depois da entrega.

---

### E5 — Habilidades

**Objetivo:** de 78 para ~310.

**Escopo**

- Constantes + tabela de nomes/descrições.
- `GetBattlerAbility` e pontos de gancho por classe: imunidade, boost de tipo, clima, ao entrar em
  campo, ao levar dano, ao atacar, ao trocar.
- Prioridade: as que aparecem em Kanto primeiro (Intimidate, Levitate, Sturdy, Static, Synchronize,
  Blaze/Torrent/Overgrow…), depois as modernas.

**Aceite**

- Toda espécie tem habilidade válida atribuída (checado pelo script do E1).
- Intimidate reduz Attack ao entrar; Levitate é imune a Golpe Terrestre; uma habilidade de Gen 9
  funciona.

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

## Registro de decisões

| Data | Decisão | Motivo |
|---|---|---|
| 2026-10-23 | Base = `pret/pokefirered` commit `ce6406d` | Pedido explícito; fork anterior rejeitado |
| 2026-10-23 | IDs 1–386 congelados | Não quebrar encontros/saves/conteúdo de Kanto |
| 2026-10-23 | Dados gerados por script, nunca à mão | 1025 espécies × 20 campos não é editável à mão |
| 2026-10-23 | EWRAM tratado como recurso escasso (98,87% cheio) | Medido no linker, não estimado |
