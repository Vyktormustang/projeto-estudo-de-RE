# T7 — Onda 4: Saffron, Rotas Marítimas, Cinnabar e Liga Pokémon (PT-BR)

Data: 2026-10-24 · Etapa: T7 (VYK-44) · Onda 4 de 6

## Escopo aplicado (CONFIRMADO no código e na ROM)

Dicionário: `scripts/firered/traducao_mapas_onda4_ptbr.py` — **600 labels**.
Aplicação: `aplicar_traducao.py --write` → 592 aplicadas + 8 já ok, 0 labels não
encontrados, nenhum aviso novo de largura.

Mapas cobertos nesta onda:

- **Saffron City** completa: cidade, casas, Centro Pokémon, Mart, casa da
  Imitadora (Copycat), Dojô de Luta, Ginásio da Sabrina, Clube de Fãs de
  Treinadores, casa do Sr. Psíquico.
- **Silph Co. 1F–11F** (todos os andares, incl. Card Key, Lapras e Giovanni).
- **Rotas marítimas**: Rota 19, Rota 20 (+ tutor de Rock Slide), Rota 21
  Norte/Sul, Rota 23.
- **Ilhas Seafoam B4F** (placas de correnteza).
- **Cinnabar Island**: cidade (incl. eventos do Bill pós-liga), Mart, Centro
  Pokémon, Laboratório Pokémon (4 salas, incl. ressuscitador de fósseis e tutor
  de Metronome), Ginásio do Blaine com o quiz completo, Mansão Pokémon
  1F/2F/3F/B1F (diários de Mewtwo).
- **Estrada da Vitória 1F/2F/3F** (+ tutor de Double-Edge).
- **Platô Índigo**: Centro Pokémon da Liga, salas de Lorelei, Bruno, Agatha,
  Lance, sala do Campeão (rival + Oak) e Hall da Fama.

Labels pulados de propósito (texto japonês não usado em jogo): Cue Ball da
Rota 21, `Gyaoo` (Moltres antigo), vitória JP do rival, interruptores JP da
Mansão, 4 sobras JP do Silph Co. — mesma regra das ondas anteriores.

Observação: `ViridianCity_Gym` (listado originalmente nesta onda) já estava em
PT-BR — foi coberto por onda anterior; verificado no `text.inc` e excluído.

## Decisões de tradução (seguem o glossário do plano)

- QUATRO DA ELITE, ESTRADA DA VITÓRIA, HALL DA FAMA, MANSÃO POKéMON,
  LABORATÓRIO POKéMON, ILHAS SEAFOAM, SALA UNIÃO.
- Nomes de golpes/itens/espécies em inglês (decisão do usuário): ROCK SLIDE,
  METRONOME, DOUBLE-EDGE, FIRE BLAST, BURN HEAL, X ATTACK, TRI-PASS,
  VOLCANOBADGE, EARTHBADGE etc.
- Doutor dos fósseis mantém o falar quebrado do original ("Eu ser doutor
  importante") — estilo preservado.

## Provas em jogo (CONFIRMADO, screenshots)

ROM: `pokefirered_modern.gba` md5 `e2874bfc26154edab75d47482bb87819`
(T1–T6 + Ondas 1–4). Emulador: mGBA 0.10.5 libretro headless.

1. **Saffron City** — voo via mapa (cursor validado na RAM: célula (14,6),
   MAPSEC 0x62), caminhada até (40,39) e leitura da placa:
   “CASA DO SR. PSÍQUICO” → `prova_saffron_sr_psiquico.png`.
2. **Cinnabar Island** — voo via mapa (célula (4,14), MAPSEC 0x60), caminhada
   até (10,10) e leitura da placa: “LABORATÓRIO POKéMON” →
   `prova_cinnabar_laboratorio.png`.

Células novas calibradas no mapa de voo: **Saffron (14,6)**, **Cinnabar (4,14)**
(partindo da Rota 1 (4,10)); flags WORLD_MAP novas: Saffron `0x89A`,
Cinnabar `0x898` — precisam estar ligadas ANTES de abrir o mapa de voo.

## Regressão E8 (CONFIRMADO)

`rodar_regressao.sh` na ROM nova: **PASS em todas as etapas** (5 self-tests,
verificar_rom, E4 golpes, E5 habilidade, E7 encontro+captura). Estado
`/tmp/e4estado/rota1.bin` regenerado para a ROM nova antes das provas.

## Próximo

- Onda 5: Ilhas Sevii (One–Seven Island e interiores).
- Onda 6: mapas de sistema/multiplayer + sobras.
