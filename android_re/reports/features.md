# Funcionalidades inferidas (por regras)

Confiança: **CONFIRMADO** = ≥3 indícios independentes · **PROVÁVEL** = 1–2 · **AUSENTE** = nenhum.

| grupo | funcionalidade | status | exemplo de evidência |
|---|---|---|---|
| generic | Comunicação HTTP(S) | CONFIRMADO |  To see where this was allocated, set the OkHttpClient logge |
| generic | Compras no app | AUSENTE | — |
| generic | Login/contas | CONFIRMADO | AccountManager cannot be null |
| generic | Persistência local | CONFIRMADO |  DataStore running in process  |
| generic | Áudio/vídeo | CONFIRMADO | EXTRA_START_PLAYBACK |
| generic | Notificações push | CONFIRMADO | Lcom/google/firebase/messaging/FirebaseMessaging; |
| generic | Instalação de APK (sideload) | CONFIRMADO | Landroid/content/pm/PackageInstaller$Session; |
| generic | Conteúdo web embutido | CONFIRMADO | , downloadUrl= |
| chess | Motor de xadrez (UCI/Stockfish/nativo) | CONFIRMADO | America/St_Lucia |
| chess | Notação FEN | CONFIRMADO | (?:(?:(?:[a-zA-Z0-9[ -퟿豈-﷏ﷰ-￯𐀀-🿽𠀀-𯿽𰀀-𿿽񀀀-񏿽񐀀-񟿽񠀀-񯿽񰀀-񿿽򀀀-򏿽򐀀-򟿽򠀀-򯿽򰀀 |
| chess | Notação PGN | AUSENTE | — |
| chess | Modos de jogo (vs CPU, online, puzzles, lições) | CONFIRMADO | (?:alley\|annex\|arcade\|ave[.]?\|avenue\|alameda\|bayou\|beach\|ben |
| chess | Renderização de tabuleiro | CONFIRMADO | $clipboard |
| chess | Rating/Elo | CONFIRMADO |  batteryVelocity |