# chess.com — análise da **jogabilidade** no site

> **Escopo:** o *site* (web) do chess.com, do ponto de vista de **jogabilidade** — regras efetivamente
> implementadas, ciclo de vida da partida, relógio, entrada de lances, empates/fins, variantes, rating,
> assistência de interface e integridade (fair play). **Fora do escopo:** preços, marketing, app mobile
> (comparado só onde a diferença muda a jogabilidade).
>
> **Coleta:** 2026-10-25 (UTC). **Método:** páginas de produto (`/play/*`, `/analysis`, `/puzzles`,
> `/variants`) + Central de Ajuda oficial (`support.chess.com`) + documentos legais (`/legal/fair-play`,
> `/cheating`). Fóruns e blogs só entram marcados como **PROVÁVEL/HIPÓTESE**.
>
> **Contrato de verdade do projeto:** `CONFIRMADO` = fonte oficial explícita · `PROVÁVEL` = fonte
> secundária/relato consistente · `INFERIDO` = dedução técnica a partir de evidência · `DESCONHECIDO`
> = não publicado.
>
> **Ressalva importante:** o produto muda com frequência (a própria Central de Ajuda tem artigos
> atualizados em 2026). Tudo aqui tem data e fonte; revalidar antes de usar como especificação.

---

## 1. Sumário executivo (o que define a jogabilidade do site)

1. **Três regimes de jogo com regras operacionais diferentes:** *Live* (relógio contínuo, servidor
   arbitra e cronometra), *Daily* (uma jogada por dias, com **lances condicionais** e **férias**) e
   *Bots* (partida local contra motor, **sem** as restrições de fair play).
2. O relógio é **arbitrado pelo servidor**, e **todo lance custa no mínimo 0,1 s** — inclusive
   pre-moves. Isso é regra de jogo, não detalhe de UI: define se você "flaga" em posições ganhas.
3. **Pre-move** (Live) e **lance condicional** (Daily) são mecanismos distintos: o primeiro é
   "meu lance, independente do que o adversário fizer"; o segundo é "se ele jogar X, eu jogo Y".
4. Empates são em boa parte **automáticos**: repetição tripla encerra sozinha (Live **e** Daily),
   regra dos 50 lances idem, material insuficiente idem — inclusive um caso de interpretação própria
   (rei + 2 cavalos × rei = empate no site).
5. **Abandono é uma condição de fim de partida**, com timers por categoria: 15 s (bullet), 20 s
   (blitz), 60 s (rapid) para o primeiro lance; reconexão = `10% × base + 40 × incremento`,
   mínimo 30 s e máximo 3 min; posição perdida ⇒ 15 s; desconexão dupla ⇒ 15 s.
6. **Abortar ≠ desistir:** abort só existe antes do primeiro lance e não conta resultado; uso abusivo
   desabilita o recurso temporariamente.
7. **Variantes mudam a condição de vitória** (3-Check, King of the Hill, Duck Chess, Crazyhouse,
   Bughouse, Fog of War, Atomic, Chess960, 4-player) — e quase todas são **só web**.
8. **Rating é Glicko com RD**, em pools separados por formato/variante; a incerteza (RD) sobe com
   inatividade, então o primeiro jogo após pausa mexe muito o número.
9. **Fair play é regra de jogo**: em Live, nenhuma assistência externa; em Daily, livros/base de
   abertura são permitidos, engine e tablebase não. O próprio contrato proíbe extensões que analisam
   posições — o que delimita o que é "jogabilidade legítima".
10. **Acessibilidade já faz parte do núcleo**: Focus Mode, controle por **voz** (web, inglês), atalhos
    de teclado, tamanho de tabuleiro, notação figurina/texto.

---

## 2. Arquitetura de produto: onde a jogabilidade acontece

| Rota | Papel na jogabilidade | Estado |
|---|---|---|
| `/play/online` | Matchmaking Live; criação de desafio; amistoso; torneios | CONFIRMADO (página) |
| `/play/online/new` | Criação de desafio (tipo, rating, cor, link) | CONFIRMADO |
| `/play/computer` | Partida contra bots, com assistências opcionais | CONFIRMADO |
| `/play/daily` | Partida por correspondência (1–14 dias/lance) | CONFIRMADO |
| `/variants` ("4 Player & Variants") | Hub de variantes | CONFIRMADO |
| `/analysis` | Revisão de partida, variações, retry de erro, montar posição | CONFIRMADO |
| `/puzzles`, `/puzzles/rush`, `/puzzles/battle`, `/daily` | Treino tático com formato de "jogo" (tempo, vidas, rating) | CONFIRMADO |
| `/settings/live`, `/settings/daily`, `/settings/accessibility` | Parametrização que **altera** a jogabilidade | CONFIRMADO |

**Snapshot de escala no momento da coleta** (volátil, não é regra): `316.317` jogando / `27.045.131`
partidas no dia, na página `/play/online`.

---

## 3. Tipos de partida e o que muda em cada um

### 3.1 Live (bullet / blitz / rapid)

A categoria **não** depende de quanto tempo a partida durou, e sim do tempo **nominal** disponível:

```
Tempo total disponível (min) = base (min) + 40 × incremento (s) / 60        # 40 lances nominais (FIDE)
bullet: < 3 min   ·   blitz: 3 ≤ t < 10   ·   rapid: 10 ≤ t < 60
```

| Controle | Total disponível | Categoria |
|---|---|---|
| 1+0 | 1 min | Bullet |
| 2+1 | 2,67 min | Bullet |
| 3+0 | 3 min | Blitz |
| 3+2 | 4,33 min | Blitz |
| 5+0 | 5 min | Blitz |
| 10+0 | 10 min | Rapid |
| 15+10 | 21,67 min | Rapid |
| 30+0 | 30 min | Rapid |

`CONFIRMADO` (fórmula e limites na Central de Ajuda; tabela derivada por cálculo — a aritmética é
minha, os limites são do site). Observação: um artigo de termos diz "rapid = mais de 10 min"; a
Central de Ajuda de ratings diz "10 minutos e mais". **Adoto ≥ 10 ⇒ Rapid.**

### 3.2 Daily (correspondência)

- Relógio **por lance** (1, 3, 5, 7, 14 dias etc.), não por partida; pode haver vários dias de banco.
- **Lances condicionais** ("se ele jogar X, respondo Y") — mecanismo que **não existe** em Live.
- **Férias (vacation)**: pausa **todos** os jogos diários ao mesmo tempo; conta mínima de 24 h por
  ativação; 7 dias iniciais; acúmulo em 1º e 15º de cada mês (1 dia Basic / 1,5 dia premium); teto de
  15 dias (Basic) e 30 (premium).
- **Proteção automática de tempo (premium):** com < 90 min restantes em qualquer jogo diário, o modo
  férias liga sozinho; checagem **1×/hora** (logo, o pausamento pode acontecer com 90 ou com ~30 min).
- **Takeback**: só em Daily **não ranqueado** (não existe em Live).
- **Auto-claim de vitória por tempo**: ajuste existente em `/settings/daily` — você pode *não* vencer
  por estouro do adversário (`PROVÁVEL`, fórum + referência à página de settings).

### 3.3 Contra bots (`/play/computer`)

Grupos de bots observados: *The Cryptids (5), New to Chess (5), Beginner (15), Intermediate (15),
Advanced (20), Master (10), Adaptive (5), Athletes (15), Musicians (6), Creators (36), Top Players
(22), Personalities (14), Visualization (25), Engine (25)*.

Controles: sem relógio, 1+1, 2+1, 3+2, 5+5, 10, 15+10, 30, 20, 60.
Assistências ligáveis: **Bot Chat, Hints, Evaluation Bar, Threat Arrows, Suggestion Arrows, Move
Feedback, Engine, Takebacks** — todas **proibidas** em Live contra humanos.

> Isso separa, no próprio produto, "modo treino" (assistido) de "modo jogo" (puro). É a distinção que
> a política de fair play formaliza: *"não se aplica a partidas contra bots"*.

### 3.4 Variantes — mudam a condição de vitória

| Variante | Delta de regra (o que muda na jogabilidade) |
|---|---|
| **Chess960 / Fischer Random** | Peças de trás embaralhadas (960 posições); roque redefinido |
| **Crazyhouse** | Peça capturada vira sua e pode ser **dropada** em casa vazia (peão não na 1ª/8ª) |
| **Bughouse** | 4 jogadores, 2 tabuleiros, duplas; peça capturada no seu tabuleiro vai para o parceiro |
| **3-Check** | Vence quem der **3 xeques** (xeque duplo conta 1); mate também vence |
| **King of the Hill** | Rei em `d4/e4/d5/e5` vence na hora; mate também |
| **Fog of War** | Casas fora do alcance das suas peças ficam cobertas (informação oculta) |
| **Atomic** | Captura gera explosão que remove peças adjacentes |
| **Duck Chess** | Cada turno = lance + mover o pato; pato bloqueia (cavalo pula); **não há xeque/mate**: vence quem captura o rei; **empatar por afogamento dá vitória a quem está afogado** |
| **4-Player** | Tabuleiro de 4; rating próprio (Glicko-2 no servidor de variantes) |

`CONFIRMADO` (Central de Ajuda + artigos de termos). **Disponibilidade:** a Central de Ajuda afirma
que, com exceção de Chess960, as variantes são **somente no site** (não no app).

### 3.5 Puzzles como "jogo"

- **Puzzle Rush:** 3 ou 5 min; **3 erros encerram**; dificuldade cresce; rating **não** é afetado.
  Modo *Survival*: sem limite de tempo.
- **Puzzle Battle:** 3 min, contra outro jogador, **mesma sequência** de puzzles, rating próprio,
  temporadas mensais.
- **Daily Puzzle:** 5 vidas ("hearts"), renova à meia-noite local, **streak** exige solução em até 48 h.
- **Basic:** 3 puzzles ranqueados/dia + 1 Rush + 1 Battle.

---

## 4. Ciclo de vida de uma partida Live (máquina de estados)

```
[busca/criação] → [sala] → (primeiro lance?) ──não──→ [ABORTADA]  (não conta resultado)
                                │sim
                                ▼
                        [em jogo: relógio do lado da vez]
                     ┌──────────┼───────────────┬───────────────┐
                     ▼          ▼               ▼               ▼
              [lance normal][premove][desconexão][lance do adversário]
                     │          │         │               │
                     └──────────┴─────────┘               │
                                ▼                          │
                    [fim: mate/afogamento/tempo/           │
                     abandono/desistência/acordo/          │
                     repetição/material/50 lances] ◄────────┘
```

| Evento | Regra operacional | Nível |
|---|---|---|
| 1º lance ausente | Aborta após **15 s (bullet), 20 s (blitz), 60 s (rapid)** | CONFIRMADO |
| Histórico ruim (abortos/desconexões/stall) | Em vez de abortar, o jogo é **perdido por abandono** | CONFIRMADO |
| Abortar | Só **antes** do 1º lance; depois vira *Resign*; não aparece no histórico; uso frequente ⇒ recurso desabilitado temporariamente | CONFIRMADO |
| Desistir (resign) | Encerra imediatamente; pode haver confirmação (*Confirm Resign/Draw*) | CONFIRMADO |
| Desconexão | Reconectar em `10% × base + 40 × incremento`, **mín. 30 s, máx. 3 min** | CONFIRMADO |
| Posição perdida (≈ −3,5 ou pior) ao desconectar | Abandono em **15 s**, independente do controle | CONFIRMADO |
| Desconexão dos dois | Timer de **15 s**; sem retorno ⇒ **dupla derrota técnica** (empate/abortada, sem rating, fora do arquivo) | CONFIRMADO |
| Stall no início | > metade do tempo-base num lance nos **10 primeiros lances** ⇒ abandono | PROVÁVEL (fórum + artigo) |
| Restart de servidor / fim de Arena | Partidas em curso são **abortadas** | CONFIRMADO |

---

## 5. Relógio: a regra mais "subestimada"

- **Todo lance custa ≥ 0,1 s** do seu tempo — inclusive pre-moves: *"você precisa de mais de 0,1 s
  no relógio para qualquer lance passar"*. Consequência prática: com 0,6 s e mate forçado em 7, você
  pode flagar.
- **Incremento** soma após o lance; o relógio **do lado da vez** corre; estouro = derrota **salvo**
  material insuficiente do adversário (⇒ empate).
- **Aviso de tempo baixo** (som) é opcional (`Low-Time Warning`).
- **Esconder rating do adversário** durante a partida é opcional (`Hide ratings during the game`).
- `INFERIDO` **Arquitetura:** o relógio é autoridade do servidor (todos os textos de abandono falam em
  "movimento que não chegou ao servidor ⇒ relógio continuou correndo"). Isso implica que **o cliente
  não decide** o resultado por tempo; ele apenas desenha uma estimativa local e reconcilia.

---

## 6. Entrada de lances: como o tabuleiro aceita comandos

### 6.1 Métodos e salvaguardas (configuráveis)

| Ajuste | Efeito na jogabilidade |
|---|---|
| **Move Method** | `Drag or click` (peça gruda no cursor) · `Drag pieces` (ignora clique simples) · `Click squares` (origem→destino) |
| **Castling Method** | `Normal` (não roca se você clicar na torre com o rei selecionado — evita roque acidental) · `Legacy` (roca) |
| **Show Legal Moves** | Pontos nas casas legais da peça selecionada |
| **Highlight Move** | Destaca as casas do lance |
| **Always Promote to Queen** | Auto-dama; `Alt` desabilita temporariamente (**PROVÁVEL**) |
| **Confirm Resign/Draw** | Pede confirmação antes de desistir/pedir empate |
| **Piece Notation** | figurina ou texto |
| **Coordinates** | dentro / fora / nenhuma |
| **White Always on Bottom** | orientação fixa ou "você sempre embaixo" |
| **Piece Animation** | Slow/Medium/Fast/Natural/Arcade (Arcade exige mais GPU) |

### 6.2 Teclado e mouse

| Ação | Comando | Nível |
|---|---|---|
| Virar tabuleiro | `X` | CONFIRMADO |
| Focus Mode | `Z` | CONFIRMADO |
| Lance anterior / próximo | `←` / `→` | CONFIRMADO |
| Primeiro / último lance | `↑` / `↓` | CONFIRMADO |
| Destacar casa | clique direito (vermelho) · `Ctrl`/`Shift`+direito (verde) · `Alt`+direito (azul) | CONFIRMADO |
| Seta | arrastar com botão direito (amarelo padrão; `Ctrl` vermelho, `Alt` azul, `Shift` verde) | CONFIRMADO |
| Setas/destaques | **só no site** (não no app); em Live exige ligar *Right Button Draw Arrows and Highlights* | CONFIRMADO |

### 6.3 Voz (acessibilidade, web, **inglês**)

Segurar **espaço** e falar. Comandos: lances (inclusive capturas e roque — *"castle king side"*, não
"short castle"), **resign**, **offer draw**, aceitar/recusar empate, pedir/aceitar revanche, aceitar
desafio, **novo jogo**. Retorno em áudio: de quem é a vez, lance do adversário, oferta de empate,
resultado, **"auto-resign at the start if no move is made"**, **reconnecting**. Requer microfone.

### 6.4 Focus Mode
Expande o tabuleiro e esconde chat/rating/menus; sobram **tabuleiro, relógios, draw e resign**.

---

## 7. Pre-move × lance condicional (não confundir)

| | **Pre-move** (Live) | **Lance condicional** (Daily) |
|---|---|---|
| Premissa | Seu lance vale **independente** do lance do adversário | Você declara **qual** lance dele dispara o seu |
| Custo de tempo | **0,1 s por pre-move** | não custa tempo extra (relógio é por lance/dia) |
| Quantidade | Site: **até 5** pre-moves (Central de Ajuda, 2026) — artigos de termos dizem "quantos quiser"; ver §13 | Várias linhas/variantes |
| Se ilegal | **cancelado**, você joga outro lance | a linha simplesmente não dispara |
| Onde | Só Live; precisa ligar *Enable Premoves* | Só Daily; botão *Conditional Moves* na vez do adversário |
| Mobile | 1 por vez (iOS); Android tem opção "múltiplos" (post oficial do suporte, 2024) | **Indisponível no app** (só web) |

> A divergência "5 × ilimitado" é **real e documentada em duas páginas oficiais** — trato no §13.

---

## 8. Como a partida termina (matriz completa)

| Condição | Comportamento no site | Divergência vs FIDE |
|---|---|---|
| **Xeque-mate** | Vitória imediata | — |
| **Afogamento (stalemate)** | Empate | — (exceto Duck Chess, onde **vence quem está afogado**) |
| **Estouro de tempo** | Derrota, **salvo** se o adversário tem material insuficiente ⇒ empate | FIDE: derrota, com exceções de "posição morta" |
| **Material insuficiente** | Empate automático. Casos: K×K, K+B×K, K+N×K, e **K+2N×K** no site | FIDE considera K+2N×K "não forçado, mas possível" — o site opta por empate |
| **Repetição tripla** | **Automática**, em Live **e** Daily | FIDE exige **reclamação** |
| **Regra dos 50 lances** | Automática | FIDE: reclamável |
| **75 lances / repetição quíntupla** | Não implementadas (a automática de 3 já encerra antes) | FIDE 9.6: automáticas |
| **Acordo mútuo** | Proposta de empate; **não pode ser retirada**; recusada implicitamente ao mover | Alinhado à FIDE (9.1) |
| **Desistência** | Encerra na hora | — |
| **Abandono** | Ver §4 (timers, dupla derrota) | Não existe OTB |
| **Aborto** | Só antes do 1º lance; sem resultado | Não existe OTB |

---

## 9. Fair play como parte da jogabilidade

Regras que **alteram o que você pode fazer durante a partida** `CONFIRMADO` (`/legal/fair-play`,
`/cheating`, artigos de suporte):

- Todos os lances devem ser seus; **nenhuma** ajuda de terceiros (nem treinador nem amigo).
- **Live:** nenhuma assistência externa de qualquer tipo.
- **Daily:** livros e base de abertura (inclusive o Explorer do site) **são permitidos** para partidas
  standard/temáticas — mas **análise com engine** desses recursos e **tablebases** são proibidas.
- **Proibido** software/engine/extensões/plugins que analisem posições durante o jogo, e "blunder
  checking" automatizado de partidas em andamento.
- Proibido manipular rating, arranjar resultados, multi-conta sem aprovação (o limite documentado é
  **2 contas com autorização**), e abandonar/desconectar de má-fé.
- Consequências: **fechamento da conta**, vitória atribuída aos adversários e, em casos extremos,
  **restauração de pontos** de até 100 partidas ou 3 meses. Detecção: "mais de 100 fatores de
  gameplay" + revisão humana; relatórios públicos mensais (ex.: **123 mil contas** fechadas em
  agosto/2025, 16 titulados).
- `HIPÓTESE` (blog de usuário, **não** oficial): existência de um ambiente/browser de segurança
  dedicado ("Proctor") e monitoramento por câmera em eventos com prêmio. Não confirmado em fonte
  oficial nesta coleta.

---

## 10. Rating e pareamento

- **Glicko com RD** (rating deviation) — `CONFIRMADO`. RD alto (novato/inativo) ⇒ variações grandes;
  RD baixo ⇒ variações pequenas. Inatividade **aumenta** o RD.
- Pools **separados** por formato: bullet, blitz, rapid, daily, cada variante, puzzle, Puzzle Battle.
- Pareamento Live usa **faixas de rating** configuráveis: *Incoming* (quem pode me desafiar),
  *Outgoing* (quem eu posso enfrentar), com opção de ignorar faixas para amigos.
- **Multi-game (premium)**: jogar várias partidas Live simultâneas, com *Auto switch* levando você à
  partida com **menos tempo restante** após cada lance — decisão de UX que **muda a gestão de tempo**.
- `PROVÁVEL`: no servidor de variantes, rating inicial 1500 / RD 120 (relato consistente em fórum).

---

## 11. Web × app: onde a jogabilidade muda de verdade

| Recurso | Web | App |
|---|---|---|
| Pre-moves | múltiplos (até 5) | iOS: 1 · Android: opção 1/múltiplos |
| Setas/destaques com botão direito | sim | **não** |
| Lances condicionais (Daily) | sim | **não** |
| Controle por voz | sim (inglês) | não documentado |
| Maioria das variantes | sim | **não** (exceto Chess960) |
| Atalhos `X`/`Z`/setas | sim | — |

---

## 12. Leitura técnica (o que a jogabilidade revela da implementação)

Rótulo geral: **INFERIDO** (dedução a partir de documentos oficiais; sem inspeção do cliente nesta
coleta — isso fica para a fase de RE do APK, §14).

1. **Servidor autoritativo** para legalidade, relógio e resultado: o texto de abandono diz que um lance
   que não chegou ao servidor "nunca aconteceu" e o relógio continuou. Logo, o cliente é renderizador +
   coletor de intenção.
2. **Pre-move é fila no cliente com replay otimista**: o lance aparece em vermelho antes de ser legal;
   se a posição invalidar, é descartado (rollback). O custo fixo de 0,1 s é **política de servidor**
   para desincentivar flag-prevention infinita.
3. **Tabuleiro renderizado em canvas** (não DOM por casa): evidência indireta — extensões de terceiros
   tiveram que se adaptar a "canvas element usage" e a mudanças de seletor. Afeta qualquer automação:
   não há árvore DOM por casa para raspar.
4. **Transporte em tempo real** (WebSocket) + eventos de estado (turno, clocks, ofertas).
5. **Detecção de fair play em duas camadas**: client-side (presença de extensões/processos) e
   **estatística server-side** (probabilidade de performance). Os detalhes são deliberadamente secretos
   ⇒ `DESCONHECIDO` por design.
6. **Anti-abuso acoplado a UX**: limites de aborto, cooldown de 5 min para contas sinalizadas
   (política de esportividade) — regras sociais implementadas como rate limits.

---

## 13. Divergências, lacunas e como resolver (testes propostos)

| # | Questão | Situação | Como verificar |
|---|---|---|---|
| 1 | Máximo de pre-moves no site hoje | **5** (Central de Ajuda) × **ilimitado** (artigos de termos/blogs) | Teste controlado: numa partida Live própria, enfileirar 6+ pre-moves e contar quantos executam; registrar com data |
| 2 | Stall nos 10 primeiros lances (metade do tempo ⇒ abandono) | `PROVÁVEL` (fórum) | Reproduzir com dois clientes e tempo controlado |
| 3 | Auto-claim de vitória por tempo em Daily (`/settings/daily`) | `PROVÁVEL` | Inspecionar a página de settings autenticado e testar |
| 4 | "Proctor"/monitoramento por câmera | `HIPÓTESE` (blog) | Só fonte oficial (anúncio/legal) confirma |
| 5 | Thresholds exatos de abandono fora da fórmula publicada | Parcial | Série de testes com relógios controlados |
| 6 | 75 lances / quíntupla | Não implementadas (inferência forte) | Construir posição e contar |
| 7 | Rating inicial por pool | `DESCONHECIDO` oficialmente | Conta nova por formato, observar 1º jogo |

---

## 14. Checklist de jogabilidade para o **APK de xadrez** (ponte com a fase de RE binária)

Como o objetivo do projeto é *compreender funcionalidades de um app de xadrez*, esta análise do site
serve de **especificação de referência**. Ao analisar o APK (pipeline `android_re/`, ver
`android_re/README.md`), procurar nesta ordem:

**A. Regras e motor**
- [ ] Existe motor próprio (`.so` com nomes tipo `stockfish`, `engine`, `eval`)? UCI? `bestmove`, `go depth`?
- [ ] Ou é motor remoto (URLs/WebSocket de análise)?
- [ ] Notação FEN/PGN implementada? (indício: strings `fen`, `pgn`, `[Event `)
- [ ] Perft/testes de legalidade embutidos? (`perft`, `CastlingRights`)

**B. Relógio e ciclo de partida**
- [ ] Classes de clock (`Clock`, `TimeControl`, `Increment`), onde o clock vive (foreground service?)
- [ ] Pre-move local (`premove`) e rollback
- [ ] Estado de abandono/`resign`/`draw`/`rematch` — mapear máquina de estados

**C. Interface de tabuleiro**
- [ ] `BoardView`/Canvas próprio, temas, coordenadas, setas/destaques
- [ ] Acessibilidade (TalkBack, controle por voz, atalhos de teclado)

**D. Modos e monetização**
- [ ] Puzzles/rush/battle, lições, análise pós-jogo (ProGuard-obfuscado?)
- [ ] Billing/IAP, ads, telemetria (rede + IDs)

**E. Confiança/integridade**
- [ ] Detecção de root/emulador, integridade de APK, ofuscação (mover para Ghidra nos `.so`)

**Comandos (pipeline já pronto neste repo):**

```bash
python3 android_re/scripts/apkre.py self-test
python3 android_re/scripts/apkre.py all   --apk <seu_xadrez>.apk --out android_re/reports
python3 android_re/scripts/apkre.py features --apk <...> --rules android_re/rules   # inclui ruleset "chess"
# decompilação nativa real (quando houver Java+Ghidra no ambiente):
bash android_re/ghidra/headless_run.sh <lib.so|classes.dex>
```

---

## 15. Fontes (coletadas 2026-10-25)

**Produto**
- https://www.chess.com/play/online · https://www.chess.com/play/computer ·
  https://www.chess.com/play/daily · https://www.chess.com/variants ·
  https://www.chess.com/analysis · https://www.chess.com/puzzles · https://www.chess.com/puzzles/rush ·
  https://www.chess.com/puzzles/battle · https://www.chess.com/daily

**Central de Ajuda (suporte oficial)**
- Tempo/ratings: `/8591239`(n/d) · `/8705367` (ratings por formato) · `/8566476` (Glicko/RD)
- Pre-move: `8562432` · Takeback: `8594400` · Aborto: `8609759` · Abandono: `8593801` · `8615100`
- Empates: `8572743` · Material insuficiente: `8705277` · `8557986`
- Settings Live: `8614003` · Conditional moves: `8583792` · Vacation: `8583943` · `8708621` · `8705438`
- Variantes: `8583983` · Duck Chess: `8615411` · Voz: `12872404` · Focus Mode: `8588088`
- Fair play: `8568369` · `8583921` · Contas desabilitadas: `9862558` · Setas/destaques: `702`
- Puzzles: `8608686` · `8708930` · Pontos de puzzle: `9681952`

**Legal / integridade**
- https://www.chess.com/legal/fair-play · https://www.chess.com/cheating

**Termos/artigos de referência**
- `/terms/chess-time-controls` · `/terms/premove-chess` · `/terms/chess-variants` · `/terms/blitz-chess` ·
  `/terms/bullet-chess` · `/article/view/chesscom-features` · `/article/view/chess-variants` ·
  `/news/view/announcing-daily-puzzle-lives-system` · `/blog/FairPlay/fair-play-update-august-2025`

**Secundárias (usadas só com rótulo PROVÁVEL/HIPÓTESE)**
- Fóruns chess.com, X `@chesscomsupport` (2024-02-14), defkey (atalhos), blogs de usuário.
