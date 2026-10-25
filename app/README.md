# Xadrez Studio

App pessoal de xadrez que roda **na sua máquina**, no navegador: jogar contra o Stockfish,
analisar partidas e — o foco — **entender cada lance em português**.

```
cd app
npm install
npm start          # http://localhost:3000
```

Também existe como **APK** para Android (mesma interface, motor e biblioteca dentro do
aparelho): veja [android/README.md](../android/README.md).

Não precisa de conta, não envia nada para servidor nenhum: o motor (Stockfish compilado para
WebAssembly) roda no seu navegador e as partidas ficam em `dados/jogos.json`.

A interface segue o **layout do chess.com** como referência visual (topo escuro com abas, barra
de avaliação ao lado do tabuleiro, linhas de jogador com avatar e relógio, navegação inferior no
celular) — desenho e código próprios, sem copiar assets de lá.

**O tabuleiro ocupa a tela**: o lado dele não é fixo, sai da altura da janela
(`--cromo-jogar`/`--cromo-analisar` descontam topo, linhas de jogador e barra de ações), então em
monitor grande ele cresce até 980 px, em notebook baixo ele encolhe para caber sem rolagem, e no
celular vai de ponta a ponta (a barra de avaliação vira uma faixa de 5 px sobre a borda esquerda).
O painel lateral tem altura da janela e rola por dentro; `100dvh` é usado onde existe para a barra
de endereço do celular não cortar o tabuleiro. As peças são o conjunto
*standard*/cburnett do Wikimedia Commons (CC BY-SA 3.0, crédito em `public/pecas/LEIA-ME.txt`).

---

## O que dá para fazer

### Jogar (`Jogar`)

- **Bots de 250 a 3200**, ajustáveis no slider ou por atalhos (Iniciante 400 … Motor 3000).
  Até 1320 a fraqueza vem de `Skill Level` baixo + profundidade curta; acima disso o próprio
  Stockfish limita por `UCI_Elo` (1320–3190).
- **Escolha de cor** (brancas, pretas, aleatório) e **tempo**: sem relógio, 3+2, 5+3, 10+0, 15+10.
- **Assistências ligáveis**: barra de avaliação, dica (seta do melhor lance), desfazer lance e
  feedback a cada lance.
- Ao terminar, a partida é salva na biblioteca e há um botão para abrir a revisão completa.

### Analisar (`Analisar`)

- Cole um **PGN**, arraste um arquivo `.pgn`, ou **importe do chess.com** pelo usuário
  (`/api/chesscom` — precisa de internet no servidor; se falhar, cole o PGN).
- A revisão analisa **todas as posições** (2 linhas por posição, em até 3 motores em paralelo) e
  devolve:
  - **selo de classificação sobre a peça** que se moveu — o `??`, o `!`, o `★` do game review,
    na cor da classe, escalando junto com a casa (SVG); no modo Jogar o mesmo selo marca o seu
    último lance quando o feedback está ligado,
  - **precisão** por lado (0–100%),
  - **classificação de cada lance**: Brilhante, Ótimo, Melhor, Excelente, Bom, Livro,
    Imprecisão, Erro, Oportunidade perdida, Erro grave,
  - **gráfico de avaliação** clicável,
  - **explicação em português** do lance selecionado, com o que ele faz, qual era o melhor,
    o que o adversário ganha e uma dica acionável,
  - até **3 linhas do motor** no painel (avaliação + continuação) para conferir.

Navegação: ← → no teclado, botões ⏮ ◀ ▶ ⏭, e clique direto na lista de lances ou no gráfico.

### Biblioteca (`Biblioteca`)

Partidas salvas em `dados/jogos.json`, com precisão e contagem de classes quando já revisadas.
Dá para revisar de novo, copiar o PGN ou excluir.

---

## Como a análise funciona (sem caixa-preta)

Toda decisão vem de avaliação do motor e de fatos calculados sobre a posição — não há texto
gerado por LLM nem "achismo".

1. **Expectativa (expected points).** Cada avaliação em centipawns vira probabilidade de ponto:
   `wc = 2/(1+e^(−0,00368208·cp)) − 1` (cp limitado a ±1000) e `EP = (1+wc)/2`.
   Mate vale 1 ou 0. Isso evita que "vantagem de +9 numa posição já ganha" conte como erro enorme.
2. **Perda por lance.** `perda = EP(antes, de quem jogou) − EP(depois, de quem jogou)`.
3. **Classificação** (mesmas faixas que os apps de xadrez usam, em expected points):

   | Classe | Perda |
   |---|---|
   | Melhor | 0 |
   | Excelente | até 0,02 |
   | Bom | até 0,05 |
   | Imprecisão | até 0,10 |
   | Erro | até 0,20 |
   | Erro grave | acima de 0,20 |

   Ajustes por cima da tabela:
   - **mate**: deixar de ter mate forçado e permitir mate do adversário ⇒ erro grave;
     ter mate e não jogar mate ⇒ oportunidade perdida; jogar mate ⇒ sempre "Melhor";
   - **Ótimo**: era o único lance que mantinha a posição (`altGap ≥ 0,15` para o 2º melhor);
   - **Brilhante**: o lance entrega material (a linha do motor mostra você cedendo ≥ 1 ponto)
     e a posição continua boa;
   - **Livro**: só nos 4 primeiros lances, e apenas para lances de abertura conhecidos.
4. **Precisão.** Por lance: `103,17·e^(−0,04354·ΔEP%) − 3,17`, limitado a 0–100; a nota do lado é
   a média dos lances. É uma **estimativa** — cada plataforma usa uma fórmula própria.
5. **Explicação.** A frase é montada a partir de fatos: mate forçado, captura imediata disponível
   (melhor captura com recaptura mais barata), peças mal defendidas, material ganho na linha
   principal, tipo de lance (captura, xeque, roque, promoção, garfo, desenvolvimento, centro) e a
   fase da partida. Se o motor não vê nada concreto, a explicação diz isso em vez de inventar.

---

## Estrutura

```
app/
├── server.mjs              servidor HTTP: estático, /vendor, /api/jogos, /api/chesscom
├── public/
│   ├── index.html          as três telas
│   ├── styles.css          tema escuro estilo chess.com, responsivo
│   ├── pecas/              12 peças SVG (cburnett, CC BY-SA 3.0) + licença
│   └── js/
│       ├── main.js         abas, estado do motor, ponte entre modos
│       ├── jogo.js         partida contra o bot (relógio, dicas, undo, feedback)
│       ├── analise.js      revisão, gráfico, navegação, explicações
│       ├── biblioteca.js   partidas salvas
│       ├── board.js        tabuleiro (DOM + peças SVG + setas; toque e arraste)
│       ├── engine.js       Stockfish em Web Worker: bot, assistência e pool paralelo
│       ├── uci.js          parser de UCI (compartilhado com os testes)
│       ├── armazenamento.js  partidas: JSON no servidor ou localStorage no APK
│       ├── review.js       núcleo puro: expected points, classes, explicações
│       └── ../vendor/chess.js   regras (vendored, também usado pelo APK)
├── tests/
│   ├── review.test.mjs     análise real com Stockfish (3 partidas + unitários)
│   └── ui.smoke.mjs        interface em jsdom com motor falso
└── dados/jogos.json        sua biblioteca (não versionada)
```

O servidor serve o Stockfish direto de `node_modules` em `/vendor`. O **chess.js** é vendorizado
em `public/vendor/chess.js` porque o APK não tem `npm` — é o único arquivo de biblioteca no repo.
No APK, o Stockfish (lite single-thread) vem de `android/servidor/`.

## Testes

```
cd app
npm test                         # análise com o motor real (~4 s)
node tests/ui.smoke.mjs          # interface sem navegador (jsdom + motor falso)
node tests/armazenamento.test.mjs # biblioteca offline (modo do APK)
```

`review.test.mjs` roda três partidas (mate do pastor, miniatura de Lazard, e uma posição com
mate em 1 ignorado) e verifica classes, precisão, explicações e o resgate de PGN com `FEN`.
`ui.smoke.mjs` sobe a página em jsdom com um motor falso que responde UCI, joga `e4`, revisa um
PGN, navega com o teclado e confere a biblioteca — e cobre o pool paralelo, os perfis de análise
(profundidade/teto de tempo), o cache de posições e o motor separado da assistência. Ele também guarda as regressões da 1.1: partida
que já começa sozinha, peças como `<img>` SVG, lance resolvido **por coordenada** (inclusive com o
tabuleiro girado), overlay de promoção escondido e conferência de todo `getElementById` do JS
contra o HTML.

## Escopo e limites (honestos)

- **Não é um clone do chess.com**: a semelhança é de layout; não tem contas, rating, online nem
  torneios. O "app mobile" é o APK deste mesmo código.
- **Precisão e classes são aproximações** das faixas públicas; o objetivo é consistência interna.
- **"Brilhante" é heurística** (sacrifício + avaliação), não a definição exata de outra plataforma.
- **Sem LLM**: se o motor não produz um fato, a explicação não inventa motivo.
- A importação do chess.com depende de internet no computador que roda o servidor.

## Licença

Código próprio: MIT. Dependências mantêm suas licenças — Stockfish é **GPL-3.0** (usado como
programa separado, via Web Worker), chess.js é BSD-2-Clause e as peças (cburnett/Wikimedia) são
**CC BY-SA 3.0**, com crédito em `public/pecas/LEIA-ME.txt`.
