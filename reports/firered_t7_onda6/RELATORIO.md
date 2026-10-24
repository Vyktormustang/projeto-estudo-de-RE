# T7 — Onda 6: textos de sistema (data/text/*.inc) em PT-BR

Data: 2026-10-24 · Etapa T7 (VYK-44) · Base: `pret/pokefirered` MODERN=1

## Status

- **Bloco A (FECHADO)**: 211 labels de sistema aplicados.
- **Bloco B (FECHADO)**: `trainers.inc` — 237 labels de revanche do
  VS SEEKER aplicados (dicionário total da onda: 448). Único pulado:
  `Route21_North_Text_CueBallRematchIntro` (100% JP, unused).
- **Bloco C (PENDENTE)**: `fame_checker.inc` (334) e `help_system.inc`
  (369) — próximos sub-blocos desta onda.

## Bloco B — trainers.inc (revanches do VS SEEKER)

Todos os `*RematchIntro` de Rotas 3-25, PONTE NUGGET (Rota 24) e Ilhas
Sevii (Kindle Road, Treasure Beach, Bond Bridge, Water Labyrinth, Resort
Gorgeous, Memorial Pillar, Outcast Island, Green Path, Water Path, Ruin
Valley, Trainer Tower externa, Canyon Sevault e Ruínas Tanoby).

Prova em jogo (CONFIRMADO): receita nova de VS SEEKER —
`savestate.py` agora escreve a pocket de KEY ITEMS, o item registrado no
SELECT (`campo --nome s1_registeredItem`) e o contador
`s1_rematchStepCounter=100`; flag 0x602 = GAMER HUGO (id 258) derrotado;
voo p/ VERMILION, Rota 11 (16,16), SELECT → animação do VS SEEKER
(Hugo passa a `MOVEMENT_TYPE_RAISE_HAND_AND_STOP`), A →
“Vitória, derrota ou empate! / Hora da nossa revanche!”
(`prova_vsseeker_hugo_rota11.png`).

Observação de método (medido, não presumido): o comentário `/*0x638*/`
de `trainerRematchStepCounter` no `global.h` está desatualizado após a
Pokédex Gen 9 — o offset real medido pelo `offsets.py` é **0x686**.

## Mudança de ferramenta

`aplicar_traducao.py` agora varre também `data/text/*.inc` (além de
`data/maps/*/text.inc`). Fora do novo glob: `new_game_intro.inc` e
`save.inc` (cópia integral via `traducao/`) e `braille.inc` (braille é o
sistema de escrita dos puzzles — não se traduz).

## Escopo do Bloco A (`traducao_mapas_onda6_ptbr.py`, 211 labels)

- `seagallop.inc` — embarque da balsa ("Todos a bordo…").
- `white_out.inc` — apagão/cura da MAMÃE e do CENTRO POKéMON.
- `surf.inc`, `itemfinder.inc`, `pc.inc`, `poke_mart.inc` (questionário
  MYSTERY GIFT), `obtain_item.inc`, `pc_transfer.inc` (mon → BOX),
  `aide.inc` (assistentes do OAK), `sign_lady.inc` (placa DICAS DE
  TREINADOR de Pallet), `route23.inc` (guarda das insígnias),
  `day_care.inc` (creche de Four Island), `safari_zone.inc` (labels EN),
  `trainer_card.inc` (impressora do Cassino + adesivos de Four Island),
  `pokedex_rating.inc` (avaliação do OAK), `ingame_trade.inc` (trocas),
  `flavor_text.inc` (objetos de fundo), `pokedude.inc` (Teachy TV).
- Sobras legítimas de mapas: Caverna do Diglett (2 entradas) e cronômetro
  da Torre dos Treinadores (`{V1}m {V2}.{V3}s`).

**Pulados por regra (JP/unused):** `eon_ticket.inc` e
`competitive_brothers.inc` (100% JP, eventos de Hoenn), partes JP de
`safari_zone.inc`/`day_care.inc`/`flavor_text.inc`, e ~60 labels JP
residuais nos mapas (RivalVictory JP, BodySlam JP de Four Island etc.).

## Aplicação e build

- `aplicar_traducao.py --write`: **211 aplicadas, 0 labels não
  encontrados, 0 problemas**.
- Rebuild OK → ROM md5 `16dc965ebc82d840a32026152011a382`.

## Prova em jogo (CONFIRMADO)

Rota 1 → Pallet Town, placa de DICAS DE TREINADOR (labels do
`sign_lady.inc`, Onda 6):

| Prova | Arquivo |
| --- | --- |
| NPC: "Leia, leia!" | `prova_npc_leia.png` |
| Placa: "DICAS DE TREINADOR" | `prova_placa_dicas.png` |
| Placa: "Aperte START para abrir o MENU!" | `prova_placa_start_menu.png` |

## Regressão E8

`rodar_regressao.sh` na ROM nova: **PASS em todas as etapas**.
