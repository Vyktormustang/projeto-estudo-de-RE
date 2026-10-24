# T7 — Onda 3 da tradução de diálogos (Lavender → Celadon → Fuchsia)

**Data:** 2026-10-24 · **Issue:** VYK-44 · **Status:** CONFIRMADO (provas abaixo)

## Escopo

933 labels de texto traduzidos para PT-BR em 83 mapas (+4 labels gerais
`Text_Substitute*` do tutor de Fuchsia), cobrindo o trecho Lavender → Celadon →
Fuchsia da campanha:

- **Rotas 7–18** + guaritas (EastEntrance/WestEntrance/NorthEntrance 1F e 2F),
  Caminho Subterrâneo leste-oeste, casa do GURU DA PESCA (Rota 12),
  casa da FLY/HM02 (Rota 16).
- **Rock Tunnel** (1F e B1F) e **Rota 10** + Centro Pokémon.
- **Lavender Town** completa: Torre Pokémon (1F–7F), Casa Voluntária,
  Avaliador de Nomes, Centro, Mart, casas.
- **Celadon City** completa: Loja de Departamentos (1F–5F + terraço),
  Mansão Celadon (Condominiums), Ginásio da Erika, Cassino (Game Corner) +
  sala de prêmios, Esconderijo da Equipe Rocket (B1F–B4F + elevador, incl.
  Giovanni), Hotel, Restaurante, Centro.
- **Fuchsia City** completa: Ginásio do Koga, placas do zoológico, Casa do
  Guarda (Warden), Zona do Safári (entrada, escritório, áreas Centro/1/2/3,
  casas de descanso e Casa Secreta/HM03), Deletador de Golpes, irmão do Guru
  da Pesca (GOOD ROD).

JP/não referenciados mantidos (fora de escopo, mesma regra das ondas 1–2).
Nomes de golpes, itens, espécies, TMs/HMs e cidades permanecem em inglês
(decisão de projeto); diálogos 100% PT-BR.

## Aplicação e build

- Dicionário: `scripts/firered/traducao_mapas_onda3_ptbr.py` (933 labels,
  validador de placeholders/charmap/largura embutido).
- `aplicar_traducao.py --pokefirered /tmp/pokefirered --write`:
  **933/933 aplicados, 0 não encontrados, 0 erros de largura**.
- Rebuild `make MODERN=1` OK → `pokefirered_modern.gba`
  md5 `d37910ca98b558e9b7081abbc775513a`.
- Nota de método: `data/event_scripts.s` precisa de `touch` após editar
  `text.inc` (o make não rastreia os `.inc` incluídos).

## Provas em jogo (FLY até cada cidade, ROM recompilada)

| # | PNG | O que mostra |
| --- | --- | --- |
| 1 | `prova1_lavender_placa_casa_voluntaria.png` | Lavender Town: placa "CASA VOLUNTÁRIA POKéMON DE LAVENDER" |
| 2 | `prova2_celadon_placa_dicas_treinador.png` | Celadon City: placa DICAS DE TREINADOR ("GUARD SPEC. protege os POKéMON de golpes que reduzem atributos") |
| 3 | `prova3_fuchsia_placa_casa_do_guarda.png` | Fuchsia City: placa "ZONA DO SAFÁRI / CASA DO GUARDA" |

## Regressão

`rodar_regressao.sh` na ROM nova: **PASS em todas as etapas**
(self-tests, verificar_rom E2–E7, E4 golpes, E5 habilidade, E7 encontro Gen 9).

## Aprendizados de método (para as próximas ondas)

- No mapa de voo, o cursor indexa `sRegionMapSections_Kanto` **sem offset**:
  Rota 1 ocupa (4,9)-(4,10); Lavender (18,6), Celadon (11,6), Fuchsia (12,12).
- Tap de **2 frames** (`"20-21:RIGHT"`) move 1 célula; tap de 1 frame
  (`"20:RIGHT"`) move 2.
- Validar a célula antes do A lendo `sMapCursor` (ponteiro EWRAM em
  `0x0203AEB0` neste build): campos `x,y` e `selectedMapsec`.
- `nav.py --rota` precisa de `--map` para ler a posição na ROM recompilada
  (offset de `gSaveBlock1Ptr` muda entre builds).
