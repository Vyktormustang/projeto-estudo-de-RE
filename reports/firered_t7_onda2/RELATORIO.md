# T7 — Onda 2: Rota 3 → S.S. Anne (PT-BR)

Data: 2026-10-24 · Etapa: T7 (VYK-44) · Status: **CONFIRMADO em jogo**

## O que foi traduzido

Dicionário `scripts/firered/traducao_mapas_onda2_ptbr.py` com **498 labels** cobrindo
**56 mapas**:

| Área | Mapas |
| --- | --- |
| Rota 3 / Rota 4 | Route3, Route4, Route4_PokemonCenter_1F |
| Monte Lua | MtMoon_1F, MtMoon_B2F |
| Cerulean | cidade, Gym, BikeShop, Mart, PokemonCenter_1F, House1-5 |
| Rotas 24/25 | Route24, Route25, Route25_SeaCottage (BILL) |
| Rota 5 / Creche | Route5, Route5_SouthEntrance, Route5_PokemonDayCare, UndergroundPath_SouthEntrance |
| Rota 6 | Route6, Route6_NorthEntrance |
| Vermilion | cidade, Gym, PokemonFanClub, PokemonCenter_1F, Mart, House1-3 |
| S.S. Anne | 22 mapas (Deck, corredores, 18 cabines, CaptainsOffice, Kitchen) |

Labels pulados (japonês não usado no jogo — sem referência em nenhum `scripts.inc`):
`CeruleanCity_Text_RivalVictory`, `CeruleanCity_BikeShop_Text_GermanFoldableBicyleFinallyOnMarket`,
`Route5_PokemonDayCare_Text_WantMeToTakeALookAtYours`, `Route5_PokemonDayCare_Text_CantAcceptMonWithHM`,
`VermilionCity_Gym_Text_AnotherSwitchInTrash`, `SSAnne_2F_Corridor_Text_RivalVictory`.

## Aplicação e build

- `aplicar_traducao.py --write`: **498/498 labels aplicados, 0 não encontrados**, 0 erros
  de validação (placeholders, charmap e largura ≤36/40 conferidos).
- Rebuild `make MODERN=1` OK. ROM `pokefirered_modern.gba`
  md5 `d7125d6120de5199ed8eebee92e98eba` (o hash varia entre builds; o artefato é o que conta).

## Provas em jogo (mGBA headless, screenshots reais)

Como os savestates ficam na Rota 1, as provas usaram FLY (POKéMON com o golpe + flags
`FLAG_BADGE03_GET` e `FLAG_WORLD_MAP_*` ligadas via `savestate.py`) para alcançar Cerulean
e Vermilion no jogo rodando.

| # | PNG | O que mostra |
| --- | --- | --- |
| 1 | `prova1_cerulean_placa_cidade.png` | Placa de Cerulean: “Uma Aura Azul e Misteriosa a Envolve” |
| 2 | `prova2_cerulean_placa_ginasio.png` | Placa do ginásio: “GINÁSIO POKéMON DE CERULEAN CITY / LÍDER: MISTY” |
| 3 | `prova3_vermilion_npc_ssanne.png` | NPC de Vermilion: “Você viu o S.S. ANNE atracado no porto?” |

## Regressão E8

`rodar_regressao.sh` no build novo: **PASS em todas as etapas** (self-tests, verificar_rom,
E4 golpes, E5 habilidade, E7 encontro+captura Gen 9).

## Extra

`setup_ambiente.sh` ganhou o passo 9/9: reaplica fonte T1 + todas as traduções e rebuilda —
religar o `/tmp` agora deixa a ROM já em PT-BR (antes o clone voltava em inglês).

## Próximo

Onda 3 (Celadon → Fuchsia), depois Saffron/E4, Sevii e textos de sistema.
