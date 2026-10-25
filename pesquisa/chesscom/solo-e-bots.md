# chess.com — jogabilidade **solo** e **contra bots**

> **Escopo:** o site (web) do chess.com no que diz respeito a jogar **sozinho** — sem adversário
> humano — seja contra oponentes artificiais (bots, Coach, engine) ou em modos sem oponente
> (puzzles, lições, endgames, Solo Chess, análise).
> Complementa [`jogabilidade.md`](jogabilidade.md), que cobre o jogo contra pessoas.
>
> **Coleta:** 2026-10-25 (UTC), páginas de produto + Central de Ajuda oficial + documentos legais.
> **Contrato de verdade:** `CONFIRMADO` (fonte oficial explícita) · `PROVÁVEL` (fonte secundária
> consistente) · `INFERIDO` (dedução) · `DESCONHECIDO` (não publicado).

---

## 1. Sumário executivo

1. **Nada disso vale rating.** Toda partida contra bot, engine ou Coach é **sempre unrated** —
   com ou sem assistência. O "placar" desses modos é **coroas** (bots) e progresso (lições/coroas).
2. **O motor dos bots é o Komodo**, e o Chess.com diz isso abertamente. O modo "Engine" é um
   **slider de 250 a 3200** — ou seja, o mesmo motor com força parametrizada, não 100 engines.
3. **A assistência é graduada e é o coração do design solo.** O nível de ajuda determina quantas
   coroas você ganha: **sem ajuda = 3**, 1–3 dicas/undos = 2, 4+ = 1. Em 2026 a customização fina
   foi reduzida no web (relatos consistentes), mas o conjunto de ferramentas segue documentado.
4. **O "bot" não é só um oponente: é um ambiente de estudo.** Arrastar uma posição do seu jogo para
   "Practice vs Computer" e ajustar força/lado é o fluxo canônico de treino — e o oponente começa
   **no nível mais forte** por padrão.
5. **O Coach é um modo separado dos bots**: feedback **a cada lance**, Hint em dois estágios
   (dica → melhor lance), Undo, e o jogo **retoma de onde parou**. Basic = 1 partida/mês.
6. **Solo puro (sem oponente)** tem cinco pilares: **Puzzles**, **Solo Chess**, **Lessons**,
   **Endgames/Practice** e **Vision** — mais **Analysis/Game Review** como camada de feedback.
7. **Game Review é o "professor" do solo**: accuracy 0–100, classificação lance a lance por
   *expected points*, e uma definição de "brilliant" que é sacrifício sólido — não "lance bonito".
8. **Progressão solo é gamificada**: coroas por bot, ratings separados de puzzle, streak de puzzle
   diário (48 h), leaderboards de endgame (diário e 90 dias), achievements.
9. **Fair play não se aplica a bots** (o documento legal é explícito) — usar engine/assistência
   contra bots é legítimo, ao contrário de Live.
10. **O elo mais fraco é a calibragem**: rating de bot não é comparável ao rating humano; a própria
    comunidade documenta desvios grandes. Trate como "etiqueta de dificuldade", não como Elo.

---

## 2. Taxonomia: o que é "solo" no chess.com

```
                        ┌─────────────────── SEM OPONENTE ───────────────────┐
                        │ Puzzles · Solo Chess · Lessons · Endgames/Practice │
                        │ Vision · Analysis · Game Review · Insights         │
                        └───────────────────────────────────────────────────┘
   1 JOGADOR ──────────┤
                        ┌──────────── COM OPONENTE ARTIFICIAL ───────────────┐
                        │ Bots (personalidades) · Engine (250–3200)          │
                        │ Adaptive bots · Play Coach · Practice vs Computer  │
                        └───────────────────────────────────────────────────┘
```

| Modo | Oponente | Tem relógio? | Vale rating? | Progressão |
|---|---|---|---|---|
| **Play Bots** (personalidade) | Komodo parametrizado | opcional (padrão: sem) | **não** | coroas 1–3 |
| **Engine** (slider 250–3200) | Komodo | opcional | **não** | coroas |
| **Adaptive bots** | Komodo com ajuste dinâmico | opcional | **não** | coroas |
| **Play Coach** | bot + feedback em tempo real | não documentado | **não** | limite por plano |
| **Practice vs Computer** | qualquer bot/engine, de posição custom | não | **não** | — |
| **Puzzles / Rush / Battle** | — (ou outro humano no Battle) | sim (Rush/Battle) | rating **de puzzle** | rating + streak |
| **Solo Chess** | — | não | não | níveis + Challenge |
| **Lessons** | — | não | não | caminho de 4 níveis |
| **Endgames** | — | sim (Challenge) | não | leaderboard |
| **Vision** | — | sim (janela) | não | high score |
| **Analysis / Game Review / Insights** | — | não | não | — |

---

## 3. Bots: o núcleo do modo solo com oponente

### 3.1 Fatos de base

| Fato | Detalhe | Nível |
|---|---|---|
| Rating | **nunca muda** em partida contra bot/engine/Coach | CONFIRMADO |
| Motor | **Komodo**, o mesmo para as personalidades | CONFIRMADO |
| Catálogo | "mais de 100 personalidades" | CONFIRMADO |
| Modo Engine | slider **250 → 3200** | CONFIRMADO |
| Níveis | Beginner 15 (250–850) · Intermediate 15 (1000–1400) · Advanced 20 (1500–2100) · Master 10 (2200–2450) | CONFIRMADO |
| Adaptive | 5 bots que **mudam de força durante a partida**: apertam se você está bem, aliviam se você erra | CONFIRMADO |
| Cor | Branco por padrão; dá para escolher Preto ou Aleatório | CONFIRMADO |
| Tempo | "sem timer" é o padrão; há presets de 1+1 a 60 min | CONFIRMADO |
| Acesso | parte dos bots fica **travada** para conta Basic (ícone de cadeado) | CONFIRMADO |
| Partidas salvas | automático ao fim, se ≥ **4 ply** (Coach: 2 ply); visível só para você | CONFIRMADO |

**Snapshot do catálogo na coleta** (página `/play/computer`, 2026-10-25), entradas por grupo:
Cryptids 5 · New to Chess 5 · Beginner 15 · Intermediate 15 · Advanced 20 · Master 10 ·
Adaptive 5 · Athletes 15 · Musicians 6 · Creators 36 · Top Players 22 · Personalities 14 ·
Visualization 25 · Engine 25 → **218 entradas**.

> ⚠ **Divergência registrada:** a Central de Ajuda fala "mais de 100 personalidades" e o guia de
> planos fala **25 bots (Basic) / 110+ (premium)**. O total de grupos soma 218. Não é possível
> reconciliar sem a lista completa (duplicidade entre grupos? sazonais? entradas que não são bots
> jogáveis?). Fica como **DESCONHECIDO**, com o número da página datado acima.

### 3.2 Modos de assistência (o "dial" do treino)

A Central de Ajuda atual lista as opções como *settings* da partida:

| Ferramenta | O que faz na prática | Efeito pedagógico |
|---|---|---|
| **Bot Chat** | mensagens da personalidade durante o jogo | engajamento, não instrução |
| **Evaluation Bar** | barra de avaliação (quem está melhor) | feedback contínuo, alto risco de dependência |
| **Threat Arrows** | setas **vermelhas** = peças suas em perigo | treina leitura de ameaça |
| **Suggestion Arrows** | setas **verdes** = lances a considerar | andaime para iniciante |
| **Move Feedback** | compara seu lance com o melhor | corrige no ato |
| **Engine** | mostra o que o computador "está pensando" | abre a caixa-preta |
| *(legado)* **Hints** | dica sob demanda | degrau intermediário |
| *(legado)* **Takebacks** | desfazer lance | experimentação sem custo |

**Histórico de modos** (documentado em artigo antigo de suporte e confirmado por fóruns):
`Challenge` (nenhuma ajuda, sem takeback) · `Friendly` (quota de 3 dicas + 3 takebacks) ·
`Assisted` (todas as ferramentas + eval bar) · `Custom` (liga/desliga cada uma).
`PROVÁVEL`: em 2026 a escolha de modo/custom foi removida para os bots de personalidade no **web**,
sobrando tempo/cor/opções; o app manteve por mais tempo. **Trate como estado instável do produto.**

### 3.3 Coroas: a economia do modo solo

| Assistência usada | Coroas por vitória |
|---|---|
| Nenhuma ajuda | **3** |
| 1–3 dicas **ou** undos | **2** |
| 4+ dicas/undos | **1** |

- No **app**, a regra é por modo: Challenge 3 · Friendly 2 · Assisted/Custom 1.
- As coroas aparecem no avatar de cada bot em `/play/computer`.
- Reset total: *Settings → Gameplay → Bots History → Reset* (só no site).

> `INFERIDO`: as coroas são um **medidor de autonomia**, não de resultado. O sistema recompensa
> você por vencer **sem ajuda** — a variável de interesse é a dependência de assistência.

### 3.4 Saídas do modo bots (o que dá para fazer com a partida)

1. **Salvar/rever**: auto-save com ≥4 ply; abaixo disso, "Save to Archive" (web) / "Save Game" (app).
2. **Game Review / análise**: revisar a partida contra o bot com o mesmo ferramental do jogo real.
3. **Practice vs Computer**: a partir de *qualquer* posição (análise, abertura, partida sua, partida
   de mestre, FEN) — o oponente **começa no nível mais forte** e você pode trocar bot/lado.
4. **Rematch/New Game** com o mesmo bot, sem perder as coroas já conquistadas.

### 3.5 Como o bot joga (o que se sabe e o que não se sabe)

- `CONFIRMADO`: mesmas personalidades, estilos e "quirks" declarados; o motor é Komodo.
- `CONFIRMADO`: existem bots **Adaptive** cuja força varia durante a partida.
- `PROVÁVEL`: a redução de força vem de parametrização/limitação de profundidade e de erros
  induzidos, não de um motor "mais fraco" distinto (consistente com o slider único 250–3200).
- `DESCONHECIDO`: calibragem exata do rating exibido; se o bot respeita incremento; o que acontece
  se o relógio do bot zerar; se o bot "pensa" no seu dispositivo ou no servidor.

---

## 4. Play Coach: o modo "professor" (separado dos bots)

| Aspecto | Regra |
|---|---|
| Acesso | Basic: **1 partida/mês**; Gold ou superior: ilimitado |
| Força | níveis com **rating aproximado** exibido; você escolhe cor |
| Feedback | a cada lance, em tempo real: elogia bons lances, aponta erros, destaca ideias |
| Ferramentas | **Hint** (2º toque revela o melhor lance), **Undo**, **Resign** |
| Opções | Suggestion Arrows, Threat Arrows, Evaluation Bar, Move feedback |
| Persistência | sair e voltar **retoma a partida** exatamente onde parou |
| Salvamento | automático com ≥ **2 ply** (não conta o "review" do Coach) |
| Identidade | o Chess.com anuncia como "primeiro oponente de IA" que ensina; o **mecanismo** não é divulgado |
| Personas | é possível trocar de Coach (personagens/instrutores) |

`INFERIDO`: Coach = **engine + camada de comentário pedagógico**; a classificação de lances usa o
mesmo *expected points* do Game Review (as categorias e thresholds publicados são os mesmos).
Não há evidência pública de que seja um LLM — o anúncio diz "IA", o que é genérico.

---

## 5. Solo sem oponente

### 5.1 Puzzles (o modo solo mais jogado)

| Formato | Regra | Rating |
|---|---|---|
| **Rated Puzzles** | dificuldade acompanha seu nível; 3/dia no Basic, ilimitado no premium | **sim** (rating de puzzle) |
| **Custom Puzzles** | escolhe tema/nível; pode repetir errados | não |
| **Puzzle Rush** | 3 min, 5 min ou **Survival**; **3 erros encerram**; dificuldade crescente | **não** afeta rating |
| **Puzzle Battle** | 3 min contra outro humano, **mesma sequência**; rating próprio; temporadas | sim (rating de battle) |
| **Daily Puzzle** | renova à meia-noite local; **5 vidas**; streak exige solução em ≤48 h | não |

`CONFIRMADO`. Detalhe de design: no Rush, **errar 3 vezes acaba a corrida** — a métrica é
velocidade **com** precisão, não só acertos.

### 5.2 Solo Chess (xadrez-solitário)

Regras (oficiais):
1. Todas as peças são da **mesma cor**.
2. **Todo lance deve capturar.**
3. Nenhuma peça pode capturar **mais de duas vezes** (ao capturar a 2ª, fica preta).
4. Se houver **rei**, ele tem de ser a **última peça**.

- Progressão por **níveis de dificuldade** (mais peças conforme sobe) e **Challenge Mode**
  (sequência de puzzles, "perfect run").
- `PROVÁVEL` (fóruns): níveis **1–10** e Challenge com **30 puzzles** (3 por nível) — não achei
  esses números na Central de Ajuda.
- Interessante academicamente: o jogo foi formalizado em artigo ("Chess is hard even for a single
  player"), o que dá uma noção de complexidade do problema — ótimo exemplo de variante com regra
  mínima e espaço de busca grande.

### 5.3 Lessons

- **Caminho (path)**: 4 níveis — *New to Chess → Beginner → Intermediate → Advanced*; cursos com
  lições + desafios interativos; ícone de formatura marca fim de curso.
- **Biblioteca**: filtros por nível, tema e instrutor (aberturas, estratégia, táticas, endgames,
  partidas de mestres).
- **Limite**: Basic tem "Learn to Play" ilimitado **+ 1 lição/dia** nas outras seções; premium é
  ilimitado.
- O **Coach** aparece dentro das lições (explicações + desafios) — mesma persona do modo de jogo.

### 5.4 Practice (ex-"Drills") e Endgames

**Practice** (web; no app só Drills):

| Seção | O que é |
|---|---|
| **Openings** | treina uma linha contra um bot que **joga os lances que você precisa** (resolve o "bot saiu da teoria") |
| **Master Games** | posições de partidas clássicas/campeonatos; escolhe cor e força do engine |
| **Drills** | temas/posições específicas, repetição até dominar |
| **Custom Position** | cola **FEN** ou monta qualquer posição |

**Endgames** (por tema → subtema), com **3 abas**:
- **Challenge** — 5 posições em sequência, **cronometrado**, sem erro; leaderboard do dia e de 90 dias.
- **Practice** — as mesmas 5 posições, sem pressão.
- **Learn** — lição correspondente ao tema.
Limite: Basic acessa **a primeira posição** de cada seção; Gold+ libera todas.

### 5.5 Vision (treino de visão de tabuleiro)

- 3 modos: **Coordinates** (`e4`), **Moves** (`Qd3`), **Coordinates + Moves**.
- Checkbox para mostrar/esconder coordenadas na borda; escolha de cor; **tempo limitado**;
  objetivo é acertar o máximo de casas.
- `PROVÁVEL`: janela de **30 s** (relatos consistentes; a Central de Ajuda diz só "time limit").

### 5.6 Analysis board: o laboratório

| Recurso | Detalhe |
|---|---|
| Fazer lances livremente | para **os dois lados** (é o "jogar contra si mesmo" oficial no web) |
| Set Up Position | monta qualquer posição; define de quem é o lance, direitos de roque (O-O/O-O-O), FEN/PGN |
| Carregar | coleções, histórico de partidas, estudo por URL, FEN/PGN |
| Metadados | edita PGN: jogadores, rating, resultado, evento, controle de tempo, local, rodada, ECO, data |
| Camadas | eval bar, linhas de engine, setas de sugestão, classificação e ameaças (toggles) |
| Engine | profundidade, número de linhas, engine de browser vs **cloud** (nuvem é de planos altos) |
| Ação | **"Practice vs Computer"** a partir da posição |

No **app**, o equivalente de jogar contra si mesmo é o **Pass and Play**.

### 5.7 Game Review: o feedback do solo

- **Accuracy 0–100** (CAPS): quão perto você jogou do que o engine jogaria.
- **Classificação por lance**: Brilliant · Great · Best · Excellent · Good · Book · Inaccuracy ·
  Mistake · **Miss** · Blunder.
- **Bandas publicadas** (por *expected points* perdidos, modelo que pondera chance de vitória):

  | Classe | Faixa |
  |---|---|
  | Best | 0.00 |
  | Excellent | 0.00 – 0.02 |
  | Good | 0.02 – 0.05 |
  | Inaccuracy | 0.05 – 0.10 |
  | Mistake | 0.10 – 0.20 |
  | Blunder | 0.20 – 1.00 |

- **Brilliant** não é "lance bonito": é **sacrifício sólido** — o melhor (ou quase), você **não fica
  mal** depois dele e **não estava ganhando de qualquer jeito**.
- O resumo da tela de fim de jogo usa uma análise **mais rápida** que o Game Review completo; por
  isso um "brilliant" do resumo pode virar outra classe no review (documentado pelo próprio site).
- **Limite free**: 1 Game Review/dia; reabrir um review já gerado **não** consome cota.
- `PROVÁVEL`: a mesma engine-alvo com profundidades diferentes por plano (Deep/Maximum no Diamond).

### 5.8 Insights e progressão

- **Insights** (analytics de padrões ao longo do tempo) é camada premium.
- Progresso solo se acumula em: **coroas** (bots), **rating de puzzle**, **streak** diário,
  **leaderboards de endgame**, **achievements**, conclusão de cursos.

---

## 6. Fair play aplicado ao solo

- O documento legal é explícito: a política **não se aplica a partidas contra bots** (não-humanos).
- Ou seja: usar eval bar, engine, dicas, undo contra bots é **legítimo** — é o modo treino.
- O que continua proibido: usar qualquer assistência em **Live** contra humanos; e usar
  **engine/tablebase** durante partidas em andamento (inclusive Daily).
- `INFERIDO`: os modos solo existem, em boa medida, **para separar** "aprender com ajuda" de
  "competir sem ajuda". As coroas são a materialização dessa fronteira.

---

## 7. Bots × Coach × Puzzle × Live: quem valida o quê

| Pergunta | Bots | Coach | Puzzles | Live |
|---|---|---|---|---|
| Testa abertura na prática | médio (bot sai da linha) | baixo | não | alto |
| Testa abertura **na linha** | via **Practice → Openings** | baixo | não | não |
| Feedback lance a lance | opcional (Move Feedback) | **nativo** | imediato (certo/errado) | pós-jogo |
| Pressão de relógio | opcional | baixo | alto (Rush/Battle) | **alto** |
| Vale rating | não | não | sim (puzzle) | **sim** |
| Permite desfazer | sim (modos assistidos) | **sim** | não | não |
| Erro tem custo | baixo | baixo | médio | **alto** |

---

## 8. Lacunas, divergências e testes propostos

| # | Questão | Situação | Como verificar |
|---|---|---|---|
| 1 | Total real de bots jogáveis | 100+ (suporte) × 110+ (premium) × **218 entradas** na página | Extrair a lista autenticado e contar ids únicos por conta Basic/Premium |
| 2 | Customização de assistência nos bots | Documentada; relatos de remoção no web em 2026 | Abrir Options de um bot de personalidade e de um bot não-personalidade; fotografar as opções |
| 3 | Rating de bot é comparável ao humano? | Não documentado; comunidade aponta desvios grandes | Série de partidas no mesmo bot e comparação com seu rating real |
| 4 | Bot respeita incremento / o que faz ao flagrar | DESCONHECIDO | Jogar 1+0 contra bot e observar relógio e resultado |
| 5 | Adaptive realmente adapta? | Declarado oficialmente; mecanismo oculto | Rodar 10 partidas no mesmo Adaptive, medindo accuracy do bot por Game Review |
| 6 | Números do Solo Chess (níveis 1–10, Challenge 30) | PROVÁVEL (fóruns) | Contar níveis na UI e no Challenge |
| 7 | Coach é LLM? | Anúncio diz "IA"; mecanismo não divulgado | Sem teste externo confiável — permanece DESCONHECIDO |
| 8 | Janela do Vision (30 s) | PROVÁVEL | Cronometrar uma sessão |

---

## 9. Fontes (coletadas 2026-10-25)

**Páginas de produto**
- `/play/computer` (snapshot de grupos, opções, tempos) · `/learn` · `/practice` · `/endgames` ·
  `/drills/endgame-practice` · `/drills/endgame-fundamentals` · `/solo-chess` · `/vision` ·
  `/analysis` · `/puzzles` · `/puzzles/rush` · `/puzzles/battle` · `/daily`

**Central de Ajuda (oficial)**
- Bots: `8614091` · `8609271` (salvar partidas) · `8648611` (resetar coroas) · `8614310` (rating não muda)
- Bots legado/opções: `694` · `8572788` (computador a partir de posição customizada)
- Coach: `10877257`
- Practice: `8724749` · Endgames: `8708978` · Lessons: `8609703` · Vision: `8615408`
- Analysis: `8583825` · Jogar contra si mesmo: `9859892` · PGN/FEN: `8598397`
- Puzzles: `8608686` · `8708930` · `9681952`
- Game Review: `8584089` · Classificação de lances: `8572705`
- Planos: `8562418`

**Legal / notícias / termos**
- `/legal/fair-play` · `/cheating`
- `/news/view/announcing-play-coach` · `/news/view/announcing-daily-puzzle-lives-system`
- `/terms/game-review` · `/terms/odds-chess` (odds é com amigos, não solo) · `/article/view/chesscom-features`

**Secundárias (só com rótulo PROVÁVEL/HIPÓTESE)**
- Fóruns chess.com (estado da customização em 2026; níveis do Solo Chess; janela do Vision),
  blogs de usuário, Reddit, e o artigo acadêmico sobre Solo Chess (arXiv 2203.14864).
