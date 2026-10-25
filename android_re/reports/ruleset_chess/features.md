# Funcionalidades inferidas (por regra)

Confiança: **CONFIRMADO** = score >= 4 (classe de API vale 2, string vale 1) · **PROVÁVEL** = 1-3 · **AUSENTE** = 0.

Corpus: 142267 strings, 22373 classes.

| grupo | funcionalidade | status | score | melhor evidência |
|---|---|---|---|---|
| chess | Motor UCI (bestmove/uciok) | AUSENTE | 0 | — |
| chess | Motor em biblioteca nativa | AUSENTE | 0 | — |
| chess | FEN (posição serializada) | AUSENTE | 0 | — |
| chess | PGN (notação de partida) | AUSENTE | 0 | — |
| chess | Relógio/incremento | AUSENTE | 0 | — |
| chess | Pre-move | AUSENTE | 0 | — |
| chess | Renderização do tabuleiro | AUSENTE | 0 | — |
| chess | Geração de lances/legalidade | AUSENTE | 0 | — |
| chess | Puzzles/táticas | AUSENTE | 0 | — |
| chess | Lições/curso | AUSENTE | 0 | — |
| chess | Jogo online (matchmaking/socket) | AUSENTE | 0 | — |
| chess | Rating/Elo/Glicko | AUSENTE | 0 | — |
| chess | Análise pós-jogo/avaliação | AUSENTE | 0 | — |

> Evidência detalhada (classe × string) em `features.json`. AUSENTE **não** prova que a funcionalidade não existe: pode estar em código nativo/ofuscado.
