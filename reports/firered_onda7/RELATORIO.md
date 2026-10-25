# Onda 7 — Correção pós-entrega: Centro POKéMON e textos fora dos .inc de mapa

Data: 2026-10-25. Motivo: o usuário reportou que **os Centros POKéMON
ficaram em inglês**. Causa raiz (CONFIRMADO): a fala da enfermeira e
outros textos compartilhados vivem em arquivos que o aplicador nunca
varria — `data/event_scripts.s` e `data/scripts/*.inc` — fora de
`data/maps/*/text.inc` e `data/text/*.inc`.

## Varredura que encontrou o problema

Sweep de TODOS os arquivos com `.string` em `data/` contra os labels de
todos os dicts: **127 blocos ainda em EN**, em 5 fontes:

| arquivo | blocos | conteúdo |
|---|---|---|
| `data/event_scripts.s` | 32 | **enfermeira do Centro POKéMON**, lojas (liquidação/elevador), PC do OAK, CARD KEY, TM/HM achado, apelido, Cable Club (boas-vindas) |
| `data/scripts/cable_club.inc` | 74 | atendentes do 2º andar do Centro (TEALA), Trade Center/Coliseu, UNION ROOM/DIRECT CORNER, minigames |
| `data/scripts/field_moves.inc` | 19 | CUT, ROCK SMASH, STRENGTH, WATERFALL, DIVE no campo |
| `data/scripts/repel.inc` | 1 | fim do efeito do REPEL |
| `data/maps/CeruleanCave_B1F` | 1 | "Mew!" (onomatopeia — fica) |

## O que foi feito

- **`traducao_mapas_onda7_ptbr.py` (novo): 124 labels** — tudo acima
  traduzido, exceto onomatopeias ("Mew!", "Gyaoo!"). "28 inches" virou
  **71 cm** (métrico). Nomes de sistemas/golpes/itens em EN (UNION
  ROOM, BERRY CRUSH, CUT, REPEL, CARD KEY…), menus citados conforme a
  UI.
- **`aplicar_traducao.py` estendido**: agora varre também
  `data/event_scripts.s` e `data/scripts/*.inc` (menos `test.inc`).
- Mystery Event (`mystery_event_club.inc`, `mystery_event_msg.s`) fica
  EN: inacessível em jogo normal (recurso de distribuição).

Aplicação: `--write` 124/124, 0 não encontrados. Rebuild com
verificação de bytes na ROM (lição do `ld | cat`): enfermeira, CUT,
REPEL e TEALA presentes; traduções anteriores intactas.

## Prova em jogo (CONFIRMADO)

Caminho real jogado: Rota 1 (13,38) → waypoints até (11,1) → Viridian
City → porta do Centro POKéMON (26,26) → balcão da enfermeira:

1. `prova_enfermeira_1.png` — “Bem-vindo ao nosso CENTRO POKéMON!”
2. `prova_enfermeira_2.png` — “Quer que eu cure os seus POKéMON…”
3. `prova_enfermeira_3.png` — “Obrigada pela espera. Restauramos a saúde…”

## Regressão E8 — PASS (todas as etapas) na ROM corrigida

## Nova build entregue (substitui a anterior no Drive)

| campo | valor |
|---|---|
| arquivo | `pokefirered_gen1-9_ptbr.gba` — 16 777 216 bytes |
| md5 | `d6fae99247f87570a054a0ae5ec092df` |
| sha256 | `e96d1a53d55e26a9e87cb2ff6bf31bd00f8c0aceb41b8e3c2a8e855c0fee1e25` |
| sha1 | `1647b619a2f36ce8cbef623e41d77805ed1ba951` |
| link | <https://drive.google.com/file/d/1E9GL7EyE5Uz1KKHdS84qXuiYQwrVoAHV/view> |

A build anterior (`a6dc773f…`, id `113SPdjP…`) foi movida para a
lixeira do Drive para não circular versão desatualizada.

## Erro de método registrado

**“Traduzi os text.inc” ≠ “traduzi todos os textos”**: scripts
compartilhados guardam `.string` em `data/event_scripts.s` e
`data/scripts/*.inc`. Varredura de cobertura deve enumerar TODOS os
arquivos com `.string` no repositório, não uma lista a priori.
