# T7 — Onda 6: textos de sistema (data/text/*.inc) em PT-BR

Data: 2026-10-24 · Etapa T7 (VYK-44) · Base: `pret/pokefirered` MODERN=1

## Status

- **Bloco A (FECHADO)**: 211 labels de sistema aplicados.
- **Bloco B (FECHADO)**: `trainers.inc` — 237 labels de revanche do
  VS SEEKER aplicados (dicionário total da onda: 448). Único pulado:
  `Route21_North_Text_CueBallRematchIntro` (100% JP, unused).
- **Bloco C (FECHADO)**: `fame_checker.inc` (127 labels) +
  `help_system.inc` (359 labels) — **ONDA 6 COMPLETA** (dicionário final:
  934 labels).

## Bloco C — fame_checker.inc + help_system.inc

**fame_checker.inc** (205 blocos; 127 traduzidos, 78 = nomes próprios de
cidade/pessoa que ficam em EN e não precisam de entrada):

- 95 locais de origem (campo centralizado de 84 px, FONT_SMALL):
  LABORATÓRIO, LIGA POKéMON, GINÁSIO PEWTER/CERULEAN/…, MONTE LUA,
  MUSEU DE PEWTER, ZONA DO SAFÁRI, PLATÔ ÍNDIGO, TORRE POKéMON,
  ESCONDERIJO, DEPÓSITO ROCKET, CÂNION SEVAULT etc.
- 96 fontes da informação: PLACA, ASSISTENTE, JORNAL POKéMON, MULHER,
  HOMEM, SENHOR(A), RAPAZ, GAROTINHA/GAROTINHO, LUTADOR, EQUIPE ROCKET,
  REVISTA, CIENTISTA, FOTO (nomes próprios mantidos).
- 14 matérias do JORNAL POKéMON (BROCK…SR. FUJI) em PT-BR.

**help_system.inc** (369 blocos; 359 traduzidos, 1 JP pulado, 9
mantidos idênticos: OT, ITEM, PP, FNT, POKé BALLS, POKéDEX, TM, HM,
POKéMON): saudação, menus, 60+ perguntas/respostas, instruções passo a
passo ({CIRCLE_n}), glossário de termos e a Tabela de Tipos completa
(68 blocos gerados programaticamente; listas de tipos em EN, como a UI).
Nomes de menu citados conferidos no `strings.c` traduzido (RESUMO,
TROCAR, GUARDA-ITENS, CORREIO, DESISTIR, ATRIBUTOS, LENTA/MÉDIA/RÁPIDA,
TROCA/FIXO, “HELP”/“LR”/“L=A” etc.).

Provas em jogo (CONFIRMADO): botão R na Rota 1 →
“Saudações! Este é o Sistema de AJUDA…” (`prova_help_saudacao.png`) e
menu “O que devo fazer nesta situação?/Como faço isto?/O que significa
este termo?/SAIR” + descrição (`prova_help_menu.png`).
fame_checker: strings PT-BR localizadas nos bytes da ROM compilada
(JORNAL POK…, MUSEU DE PEWTER, LUTADOR, ASSISTENTE) — a UI do FAME
CHECKER exige entradas desbloqueadas por eventos; prova visual fica
para a varredura T8.

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

## Fechamento da Onda 6

ROM final da onda: md5 `ef6e69335df6a4b8a8ec77d80986203d` (T1-T6 + Ondas
1-6). Regressão E8 **PASS em todas as etapas** nesta ROM após o Bloco C.
