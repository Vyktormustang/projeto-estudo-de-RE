# PLANO CIENTÍFICO — Xadrez Estilo Chess.com (v23.0.0)

**Objetivo:** Transformar o módulo de xadrez existente (engine + tabuleiro + bots + puzzles) em um ecossistema completo estilo Chess.com, 100% offline (APK WebView, Soberano e Offline por Design), em pt-BR, com base científica rigorosa em aprendizado de xadrez, neurociência da motivação e design de jogos.

---

## 1. BASE CIENTÍFICA E FONTES

### 1.1 Aprendizado de Xadrez e Expertise

| Fonte | Ano | Principais Conclusões | Aplicação no Plano |
|-------|-----|----------------------|-------------------|
| Gobet & Simon (Cognitive Psychology, 1996) | 1996 | Template Theory of Expert Memory (~50.000 chunks) | Sistema de chunks de posição, reconhecimento de padrões táticos |
| Saariluoma & Kalakoski (Memory, 1998); Campitelli & Gobet (2005) | 1998/2005 | Blindfold chess = WM visuospacial + LTM chunks | Modo visualização cega, treino de memória de tabuleiro |
| Burgoyne et al. (Intelligence, 2016, N=1.779) | 2016 | Chess skill ↔ Gf/Gsm/Gs/numerical r=.24–.35 | Métricas de progresso correlacionadas com habilidades cognitivas |
| Macnamara et al. (Psych Science, 2014, N=11.135) | 2014 | Deliberate practice: 26% games, 21% music, 18% sports | Foco em prática deliberada, não apenas jogar |
| Dunlosky et al. (Psych Science Public Interest, 2013) | 2013 | Practice testing & distributed practice = alta utilidade | Puzzles espaçados, repetição espaçada de táticas |
| Cepeda et al. (Psych Bulletin, 2006) | 2006 | ISI ótimo ~10–20% do delay de retenção | Espaçamento de revisão de aberturas e finais |
| Ericsson (The Role of Deliberate Practice) | 1993 | 10.000h regra; prática deliberada com feedback imediato | Análise pós-partida imediata, coach de erros |
| De Groot (Thought and Choice in Chess, 1946/1965) | 1946 | Mestre vs amador: busca seletiva, não mais profunda | Engine de busca seletiva por nível de bot |

### 1.2 Neurociência da Motivação e Design de Jogos

| Fonte | Ano | Conclusão | Aplicação |
|-------|-----|-----------|-----------|
| David Goggins (Can't Hurt Mindset) | — | Cookie Jar, 40% Rule, accountability | Sistema de "Cookie Jar" de vitórias, lembretes de resistência |
| Kappes & Oettingen (WOOP) | 2011 | Wish-Outcome-Obstacle-Plan | Definição de meta ELO com obstáculos identificados |
| Milkman (Temptation Bundling) | 2013 | Combinar prazer com tarefa difícil | Xadrez + áudio motivacional (voz Goggins/Cristo) |
| Fujita et al. (JPSP, 2006) | 2006 | High-level construal aumenta autocontrole | Visão de longo prazo (maestria) vs curto prazo (vitória) |
| Lieberman (Affect Labeling) | — | Nomear emoções reduz amígdala | Check-in emocional antes/ depois de partidas ranqueadas |
| Gross & Thompson (Reappraisal) | — | Reapreciação cognitiva d=0.55 | Reframe de derrotas como aprendizado |

### 1.3 Design de Interfaces de Jogos (Chess.com como referência funcional)

Funcionalidades essenciais do Chess.com a replicar (adaptado para offline):
- Tabuleiro interativo com arrastar-e-soltar
- Relógio de xadrez (bullet, blitz, rápido, clássico)
- Partidas contra bots com ELO variável
- Partidas 2 jogadores local (mesmo dispositivo)
- Puzzles táticos diários com rating
- Histórico e replay de partidas
- Análise de posição (engine integrada)
- Sistema de ranqueamento ELO
- Conquistas / Achievements
- Abertura de partidas (Opening Explorer)
- Modo Chess960 (Fischer Random)
- Notificação de xeque, xeque-mate, empate, rendição

---

## 2. ESCOPO v23.0.0 — XADREZ COMPLETO

### 2.1 Funcionalidades a Implementar

| ID | Funcionalidade | Descrição | Base Científica |
|----|---------------|-----------|-----------------|
| X-01 | **Sistema ELO Ranqueado** | Cálculo de ELO após cada partida (vs bot e vs local), categorias (Iniciante, Clube, Especialista, Mestre, Grão-Mestre) | Macnamara deliberate practice; feedback imediato |
| X-02 | **Partidas 2 Jogadores Local** | Dois jogadores no mesmo dispositivo, trocando de lado, relógio opcional | De Groot (escolha de lances sob pressão) |
| X-03 | **Histórico Completo de Partidas** | Salvamento no vault local: FEN, lances SAN, resultado, duração, ELO antes/depois | Ericsson (feedback imediato para melhoria) |
| X-04 | **Replay de Partidas** | Navegação lance-a-lance por partidas salvas, com análise de engine | Gobet (reconhecimento de padrões via repetição) |
| X-05 | **Análise Pós-Partida** | Relatório completo: precisão, lances imprecisos/erros/falhas, melhor lance alternativo, coach de texto em pt-BR | Ericsson (feedback imediato); De Groot (busca seletiva) |
| X-06 | **Opening Explorer** | Explorador de aberturas com estatísticas de vitória/empate/derrota por ECO | Cepeda (espaçamento de revisão) |
| X-07 | **Puzzles Diários com Rating** | Puzzle do dia, rating de puzzles separado, temas táticos (garfo, espeto, mate, etc.) | Dunlosky (practice testing distribuído) |
| X-08 | **Conquistas / Achievements** | Medalhas por vitórias, sequências, puzzles resolvidos, openings jogados, etc. | Goggins (Cookie Jar); Milkman (temptation bundling) |
| X-09 | **Estatísticas do Jogador** | Vitórias, derrotas, empates, precisão média, ELO pico, abertura favorita, peça mais perdida | Macnamara (métricas de prática deliberada) |
| X-10 | **Modo Visualização Cega** | Tabuleiro sem peças, jogar por memória de coordenadas | Saariluoma & Kalakoski (blindfold chess) |
| X-11 | **Check-in Emocional** | Antes/ depois de partidas ranqueadas, label de emoção, reappraisal | Lieberman (affect labeling); Gross (reappraisal) |
| X-12 | **Sons e Haptica** | Som de movimento, captura, xeque, mate, relógio; vibração em eventos | Áudio biofeedback existente |

### 2.2 Não-Escopo (versão offline)

- Multiplayer online (requer servidor — fora do escopo offline/sóberano)
- IA de nível GM (stockfish completo — engine interno é suficiente para níveis até ~1800)
- Transmissão ao vivo de partidas

---

## 3. ARQUITETURA TÉCNICA

### 3.1 Camadas

```
Camada de Apresentação (React + CSS)
  ├── ChessArenaTab — layout principal, navegação entre modos
  ├── ChessBoardView — tabuleiro interativo (já existente, estender)
  ├── ChessGamePanel — relógio, placar, controle de partida
  ├── ChessHistoryPanel — histórico e replay
  ├── ChessStatsPanel — estatísticas do jogador
  ├── ChessPuzzlePanel — puzzles diários
  ├── ChessAchievementsPanel — conquistas
  └── ChessOpeningExplorer — explorador de aberturas

Camada de Lógica (engine existente)
  ├── chessEngine.ts — engine, bots, análise, ELO
  ├── openingBook.ts — aberturas ECO
  ├── puzzlesCatalog.ts — puzzles táticos
  └── chessTrainingSuite.ts — Chess960, exercícios

Camada de Persistência (vaultStorage)
  ├── ChessVaultData — partidas salvadas, estatísticas, ELO, conquistas
  └── LocalStorage — JSON serializado
```

### 3.2 Sistema ELO

Fórmula Elo padrão (FIDE):
```
R_new = R_old + K × (S - E)
E = 1 / (1 + 10^((R_opponent - R_player) / 400))
K = 40 (iniciante < 1500), 20 (intermediário), 10 (avançado > 2000)
```

Categorias:
- < 800: Iniciante
- 800–1199: Clube
- 1200–1599: Intermediário
- 1600–1999: Avançado
- 2000–2299: Especialista
- 2300–2499: Mestre
- 2500+: Grão-Mestre

### 3.3 Persistência

Estender `ChessVaultData` em `types.ts` com:
- `chessElo: number`
- `chessGamesPlayed: number`
- `chessWins/Draws/Losses`
- `chessBestElo: number`
- `chessGames: ChessSavedGame[]`
- `chessAchievements: string[]`
- `chessPuzzleRating: number`
- `chessOpeningStats: Record<ECO, {played, wins, draws, losses}>`

---

## 4. CRITÉRIOS DE ACEITAÇÃO

1. **tsc --noEmit: 0 erros**
2. **vitest: todos os testes passando** (incluindo novos testes de xadrez)
3. **APK v23.0 construído, ZIPALIGN_OK, assinado v1+v2+v3**
4. **Partida completa vs bot funciona**: jogar → mover → xeque-mate → ELO atualizado → partida salva no vault
5. **Partida 2 jogadores local funciona**: dois jogadores no mesmo dispositivo
6. **Replay funciona**: navegar por partida salva lance-a-lance
7. **Análise pós-partida funciona**: relatório de precisão + erros + coach pt-BR
8. **Puzzles diários funcionam**: puzzle do dia com rating separado
9. **Conquistas funcionam**: desbloqueio por vitórias/sequências
10. **Opening Explorer funciona**: navegar por aberturas com estatísticas
11. **Todos os textos em pt-BR**
12. **Funciona 100% offline** (sem servidor)

---

## 5. ETAPAS DE IMPLEMENTAÇÃO

### Fase 1 — Sistema ELO e Persistência (X-01, X-03)
- Estender types.ts com dados de xadrez
- Implementar cálculo ELO e categorias
- Salvar partidas automaticamente no vault

### Fase 2 — Partidas 2 Jogadores e Replay (X-02, X-04)
- Modo local 2 jogadores (alternar cor, relógio compartilhado)
- Replay de partidas salvas

### Fase 3 — Análise Pós-Partida e Opening Explorer (X-05, X-06)
- Relatório de precisão, erros, coach pt-BR
- Explorador de aberturas com estatísticas

### Fase 4 — Puzzles e Conquistas (X-07, X-08)
- Puzzle do dia com rating
- Sistema de conquistas/medalhas

### Fase 5 — Estatísticas, Visualização Cega e Polish (X-09, X-10, X-11, X-12)
- Dashboard de estatísticas
- Modo blindfold
- Check-in emocional
- Sons e haptica

### Fase 6 — Build, Testes e Release
- tsc, vitest, vite build
- APK v23.0
- Commit e push

---

## 6. RISCOS E MITIGAÇÕES

| Risco | Mitigação |
|-------|-----------|
| Engine de xadrez fraco para bots altos | Limitar bots a ~1800 ELO; usar profundidade seletiva |
| Perda de dados do vault | Backup automático antes de gravações |
| UI não responsiva em telas pequenas | CSS mobile-first, tabuleiro redimensionável |
| Pseudoscience em claims de aprendizado | Todas as claims citam fontes verificadas; nenhuma cura milagrosa |

---

**Próximo passo:** Iniciar Fase 1 — Sistema ELO e Persistência.