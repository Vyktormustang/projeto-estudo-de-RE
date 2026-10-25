# Funcionalidades inferidas (por regra)

Confiança: **CONFIRMADO** = score >= 4 (classe de API vale 2, string vale 1) · **PROVÁVEL** = 1-3 · **AUSENTE** = 0.

Corpus: 142267 strings, 22373 classes.

| grupo | funcionalidade | status | score | melhor evidência |
|---|---|---|---|---|
| generic | Comunicação HTTP(S) | CONFIRMADO | 4 | 110 HttpURLConnection "Response is stale" |
| generic | Compras no app | AUSENTE | 0 | — |
| generic | Login/contas | CONFIRMADO | 4 | AccountManager cannot be null |
| generic | Persistência local | CONFIRMADO | 51 | androidx.sqlite.db.SupportSQLiteOpenHelper |
| generic | Áudio/vídeo | CONFIRMADO | 61 | androidx.leanback.media.MediaPlayerAdapter |
| generic | Notificações push | CONFIRMADO | 23 | com.google.firebase.messaging.FirebaseMessaging |
| generic | Instalação de APK (sideload) | CONFIRMADO | 6 | Landroid/content/pm/PackageInstaller$Session; |
| generic | Conteúdo web embutido | CONFIRMADO | 7 | , downloadUrl= |
| generic | Firebase presente | CONFIRMADO | 48 |  is not an instance of com.google.firebase.components.ComponentRegistrar |
| generic | Jetpack Compose | CONFIRMADO | 784 | androidx.compose.ui.platform.AbstractComposeView |
| generic | Checagem de root/integridade | PROVÁVEL | 2 | , isRooted= |
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
