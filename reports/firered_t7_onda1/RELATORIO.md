# T7 — Diálogos dos mapas em PT-BR — Onda 1 (Pallet → Pewter)

Data: 2026-10-24 · Etapa Linear: VYK-44 · ROM alvo: `pokefirered_modern.gba` (pret/pokefirered, MODERN=1)

## O que foi feito (CONFIRMADO)

Tradução integral dos diálogos dos **30 mapas** do trecho Pallet Town → Pewter City
(arquivos `data/maps/<mapa>/text.inc`), aplicada por dicionário versionado:

- `scripts/firered/traducao_mapas_onda1_ptbr.py` — **320 labels** (blocos de texto),
  cobrindo 1.140 diretivas `.string` dos 30 mapas da onda.
- Aplicador: `scripts/firered/aplicar_traducao.py` (nova função `aplicar_mapas`),
  com validação automática de: placeholders idênticos (multiset), caracteres dentro
  do charmap, e largura visível por linha (aviso >36, erro >40; `{PLAYER}`/`{RIVAL}`
  contam 7, `{STR_VAR_*}` contam 10).

### Mapas da onda

| Área | Mapas |
|---|---|
| Pallet Town | PalletTown, PlayersHouse 1F/2F, ProfessorOaksLab, RivalsHouse |
| Rota 1 / Rota 22 | Route1, Route22 (+NorthEntrance: sem text.inc) |
| Viridian City | ViridianCity, Gym, House, Mart, PokemonCenter 1F, School (2F: sem text.inc) |
| Rota 2 / Floresta | Route2, EastBuilding, House, ViridianForest N/S Entrance, ViridianForest |
| Pewter City | PewterCity, Gym, House1, House2, Mart, Museum 1F/2F, PokemonCenter 1F (2F: sem text.inc) |

Resultado do aplicador: **317 aplicadas, 3 já idênticas, 0 labels não encontrados (de 320)**.

### Melhorias de infraestrutura nesta etapa

1. Regex do bloco `label:: .string` agora aceita indentação por TAB (Route22 usa TAB;
   os demais usam 4 espaços).
2. Regex de placeholders agora aceita minúsculas/símbolos (`{PAUSE 0xFE}` etc.).

## Casos especiais

- **`PalletTown_RivalsHouse_Text_ThereYouGoAllDone` ficou em inglês**: o bloco tem
  `#ifdef BUGFIX` no meio e não casa no regex do aplicador. Registrado para a T8.
- 3 textos em japonês (não usados pelo jogo: 2 em Route22 e 3 em PewterCity, rival RB /
  NPC cortado das berries) e `"?????"`/placas JP unused **não foram traduzidos**, por
  decisão de projeto (conteúdo inacessível).
- `PewterCity_Gym_Text_BrockDefeat`: o original em inglês já estoura o buffer
  `gDisplayedStringBattle` (comentário no próprio pret). A tradução manteve
  comprimento equivalente ao original.

## Glossário aplicado (consistência com T1-T6)

MOM→MAMÃE · Gramps→vovô · "Smell you later!"→"Até nunca!" · BAG→BOLSA ·
OAK'S PARCEL→ENCOMENDA DO OAK · TRAINER→TREINADOR · AIDE→AJUDANTE ·
GYM→GINÁSIO · LEADER→LÍDER · BADGE→INSÍGNIA · POKéMON LEAGUE→LIGA POKéMON ·
ELITE FOUR→QUATRO DE ELITE · TRAINER TIPS→DICAS DE TREINADOR ·
VIRIDIAN FOREST→FLORESTA DE VIRIDIAN · MT. MOON→MONTE LUA ·
RUNNING SHOES→TÊNIS DE CORRIDA · tall grass→capim.
Nomes de **cidades/rotas (em placas), espécies, golpes, itens, TMs/HMs e insígnias
permanecem em inglês** (decisão do usuário).

## Prova em jogo (CONFIRMADO — ROM md5 `36fcad36c2437433c276e8d702ca025e`)

| Arquivo | O que mostra |
|---|---|
| `prova_placa_lab_oak.png` | Placa "LABORATÓRIO POKéMON DO OAK" (PalletTown) |
| `prova_placa_pallet.png` | Placa "PALLET TOWN / Tons da sua jornada o aguardam!" |
| `prova_placa_rota1.png` | Placa "ROTA 1 / PALLET TOWN - VIRIDIAN CITY" |
| `prova_dialogo_npc_rota1.png` | Diálogo multipágina do vendedor do MART (Rota 1) em PT-BR |

Savestates regenerados após o rebuild (`prova_golpes_e4.py --preparar-estado`),
pois savestate só vale na ROM exata.

## Regressão

`bash scripts/firered/rodar_regressao.sh` → **PASS em todas as etapas**
(self-tests, verificar_rom na ROM real, E4 golpes, E5 habilidade, E7 encontro+captura Gen 9).

## Próximas ondas (VYK-44 continua In Progress)

Onda 2: Cerulean→Vermilion · Onda 3: Celadon→Fuchsia · Onda 4: Saffron→Elite 4 ·
Onda 5: Ilhas Sevii · Onda 6: textos de sistema (`data/text`, `data/scripts`).
