# Plano — Tradução PT-BR do FireRed Gen 1-9

Traduzir para português do Brasil a ROM entregue na E9 (base `pret/pokefirered`
com as 9 gerações), **sem quebrar nada** do que foi provado em E0-E9.

## Decisões de tradução (padrão do projeto)

| o quê | decisão | motivo |
|---|---|---|
| Nomes de espécies | **inglês** (Pikachu, Lechonk…) | nomes oficiais são mundiais, nunca traduzidos |
| Nomes de golpes | **inglês** (Tackle, Thunderbolt…) | decisão do usuário (estética), 2026-10-24 |
| Nomes de habilidades | **inglês** (consistência com golpes) | idem |
| Nomes de itens | **inglês** (Potion, Ultra Ball…) | decisão do usuário (estética), 2026-10-24 |
| Descrições de golpes/itens/habilidades | **PT-BR** | prosa acompanha o resto do jogo |
| Nomes de lugares | **manter** (Pallet Town, Rota 1 traduz "Route"→"Rota") | consistência com mapas/placas |
| Diálogos, menus, batalha, descrições | **PT-BR integral** | objetivo do projeto |
| Acentos | suporte completo, inclusive **ã õ Ã Õ** (não existem na fonte original — ver T1) | português de verdade |

**Limites rígidos de tamanho** (campo fixo na ROM): espécie 10, golpe 16,
habilidade 12, item 14 caracteres. Tradução que não cabe → abreviar.

## Volume medido (base da estimativa)

| fonte de texto | volume |
|---|---|
| Diálogos de mapas (`data/maps/*/text.inc`) | ~9.020 linhas `.string` |
| Textos de sistema (`data/text/`, `data/scripts/`) | ~3.884 linhas |
| Strings da engine (`src/strings.c` + 39 outros `.c`) | ~1.324 + espalhadas |
| Golpes (nome+descrição) | 823 |
| Habilidades (nome+descrição) | 321 |
| Itens (nome+descrição) | ~375 |
| Pokédex (categoria já E7; descrição por espécie) | 1.025 |

## Etapas

- **T1 — Fundação: fonte + ferramentas.** Adicionar ã/õ/Ã/Õ às 4 fontes
  latinas reaproveitando glifos que o PT não usa (Ì→Ã, ì→ã, ò→õ, Œ→Õ):
  pixel art composto programaticamente (base + til do ñ), charmap.txt,
  tabelas de largura em `src/text.c`. Ferramentas: validador de charset e
  comprimento. **Prova:** intro do jogo traduzida com ã/õ renderizando.
- **T2 — Interface:** menus, bolsa, save, opções, telas de UI
  (`src/strings.c` e afins).
- **T3 — Batalha:** mensagens de batalha ("X used Y!" → "X usou Y!").
- **T4 — Itens:** só as DESCRIÇÕES (nomes ficam em inglês — decisão do
  usuário).
- **T5 — Golpes + habilidades:** só as DESCRIÇÕES (nomes ficam em inglês —
  decisão do usuário).
- **T6 — Pokédex:** descrições das 1.025 espécies.
- **T7 — História:** diálogos dos 430 mapas, em ondas (Kanto por regiões;
  Sevii Islands por último).
- **T8 — Regressão + entrega:** `rodar_regressao.sh` verde na ROM traduzida,
  nova build no Drive, documentação.

Cada etapa: muda → compila → prova em jogo (screenshot) → commit → Linear.

## Status

- **T1 — CONCLUÍDA (2026-10-24):** fonte com ã/õ/Ã/Õ nas 4 fontes latinas, charmap, larguras, ferramentas (`aplicar_fonte_ptbr.py`, `aplicar_traducao.py`) e intro do jogo traduzida — provas em `reports/firered_t1/`.
- **T2 — EM ANDAMENTO (onda 1 concluída: 255 strings de src/strings.c + save.inc; provas em reports/firered_t2/).**
