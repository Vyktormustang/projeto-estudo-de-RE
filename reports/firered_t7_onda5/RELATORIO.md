# T7 — Onda 5: diálogos das Ilhas Sevii em PT-BR

Data: 2026-10-24 · Etapa T7 (VYK-44) · Base: `pret/pokefirered` MODERN=1

## Escopo

Dicionário `scripts/firered/traducao_mapas_onda5_ptbr.py` com **691 labels**
cobrindo os `text.inc` dos mapas das Ilhas Sevii (One a Seven Island):

- **One Island**: cidade, casas, Pokémon Center (Celio/Rede), Treasure Beach,
  Kindle Road, Ember Spa, Mt. Ember.
- **Two Island**: cidade, PC, casa, Cape Brink, Joyful Game Corner.
- **Three Island**: cidade, Bond Bridge, Berry Forest, port/vila.
- **Four Island**: cidade completa (creche, Lorelei, Icefall Cave etc.).
- **Five Island**: cidade, PC, casas, Meadow, Water Labyrinth, Lost Cave
  (salas 1/4/10), Resort Gorgeous (+ casa da Selphy), Memorial Pillar,
  Rocket Warehouse.
- **Six Island**: cidade, PC, Mart, casa, Green Path, Dotted Hole (Sapphire),
  Water Path (+ casas), Ruin Valley, Outcast Island, Pattern Bush.
- **Seven Island**: cidade, PC, Mart, House (sala de batalha), Trainer Tower
  (lobby/terraço/placas), Sevault Canyon (+ entrada e casa), Tanoby Key,
  Tanoby Ruins.

Pulados de propósito (JP/unused, regra do projeto): `FiveIsland_House1_JPText_…`,
`FiveIsland_Meadow_Text_DoorNeedsTwoPasswords`,
`FiveIsland_WaterLabyrinth_Text_YouveComeBackForTheEgg`,
`TrainerTower_Lobby_Text_HereAreTheResults` e `SevenIsland_TrainerTower_Text_LooksLike…/IsOpen…` (JP).

## Aplicação e build

- `aplicar_traducao.py --write`: **684 aplicadas, 7 já ok, 0 labels não
  encontrados, 0 problemas** (1 aviso de largura corrigido quebrando linha).
- Rebuild `make MODERN=1` OK → ROM `pokefirered_modern.gba`
  md5 `e6b44b3181cb4020fc5be2835847e03f`.

## Prova em jogo (CONFIRMADO)

Rota da prova: estado base Rota 1 → FLY p/ Vermilion (flag 0x895 + badge 0x822)
→ vars `VAR_MAP_SCENE_VERMILION_CITY=3` e
`VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F=1` (Tri Pass) → píer (24,32) →
balsa SEAGALLOP → One Island (mapa 32:4 → 3:12).

| Prova | Arquivo |
| --- | --- |
| Menu da balsa em PT-BR ("Gostaria de embarcar numa balsa SEAGALLOP?") | `prova_menu_seagallop.png` |
| NPC de One Island: "Oi, fazendo turismo, é? O clima quente daqui não é ótimo?" | `prova_npc_one_island.png` |
| Placa: "ONE ISLAND / Amigos se Reúnem na Ilha do Nó" | `prova_placa_one_island.png` |

## Regressão E8

`rodar_regressao.sh` na ROM nova: **PASS em todas as etapas**
(self-tests, verificar_rom, E4 golpes, E5 habilidade, E7 encontro Gen 9).

## Sobras conhecidas (vão para a Onda 6 / T8)

- `data/text/seagallop.inc` (ex.: "All aboard SEAGALLOP HI-SPEED …") e
  `text.inc` dos harbors — textos de sistema da balsa, fora do escopo
  por-mapa desta onda.
- Blocos com `#ifdef` no meio e sobras de baixa visibilidade (T8).

## Receita Sevii (para reuso)

1. `prova_golpes_e4.py --preparar-estado` (rota1.bin da ROM atual).
2. `savestate.py … pokemon --slot 0 --species 18 --level 50 --moves 19`,
   `flag --set 0x822 0x895`, `var --id 0x407E --valor 3`,
   `var --id 0x4076 --valor 1`.
3. FLY até VERMILION (célula 14,9; sec 0x5D) — receita da Onda 4.
4. Vermilion: descer pela coluna x=23 até y=20, leste até x=36, descer
   x=36 até y=28, oeste até x=24, descer até (24,32) — evita NPCs e os
   triggers de bilhete em x=22-23.
5. Falar DOWN com o marinheiro (24,33) → menu Tri Pass → opção 0 =
   ONE ISLAND → ~4000 frames de viagem → harbor 32:4 → warp (8,2) → cidade.
