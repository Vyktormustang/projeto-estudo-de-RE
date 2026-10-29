# FORJA — Sistema do Ápice `v13.0.0`
## *A Edição do Grande Mestre — Suíte Soberana de Xadrez Estilo Chess.com (100% Offline)*

---

## 1. Visão Geral da Evolução `v13.0.0`

A versão **`13.0.0` (`versionCode: 1300`, pacote `br.forja.apice`)** integra à arquitetura científica e espiritual da FORJA (`160` lições simétricas `40/40/40/40`, 9 esportes mentais com a Tríade Executiva de Miyake, Tribunal Fechado de Brier e Forja Física com RIR/EWMA) uma **Suíte Completa de Xadrez Estilo Chess.com 100% Soberana e Offline**, sem depender de nenhum servidor externo.

---

## 2. Paridade Funcional 100% Estilo Chess.com & Regras Oficiais FIDE

### 2.1. Regras Oficiais FIDE Completas
- **Movimentação e Especiais:** Roque curto (`O-O`) e longo (`O-O-O`), captura *En Passant* (incluindo xeque-mate *en passant*!), promoção e **subpromoção tática** (`Dama`, `Cavalo`, `Torre`, `Bispo`).
- **Desfechos Oficiais:** Xeque-mate, empate por afogamento (*stalemate*), empate por tripla repetição (com hash Zobrist de 64 bits incremental), regra dos 50 lances, material insuficiente (`R vs R`, `R+B vs R`, `R+C vs R`) e **Artigo 6.9 da FIDE em Queda de Seta** (se o tempo de um jogador acaba mas o adversário não possui material capaz de aplicar mate, a partida é declarada **Empate** em vez de derrota!).
- **Ações de Partida:** Proposta realista de empate avaliada pelo Bot conforme avaliação centipeão e fase do jogo, abandono com confirmação de segurança, revanche instantânea e histórico salvo no Cofre.

### 2.2. Experiência Visual & Tátil Estilo Chess.com
- **Peças Vetoriais Neo-Staunton SVG:** Nitidez infinita em qualquer resolução Android, sem requisições de rede.
- **4 Temas Clássicos de Tabuleiro:**
  1. **Verde Torneio (Chess.com):** `#ebecd0` / `#739552` com destaque de lance `#f5f682` / `#b9ca43`
  2. **Nogueira Imperial:** `#f0d9b5` / `#b58863`
  3. **Oceano Ártico:** `#dee3e6` / `#788a94`
  4. **Obsidiana & Ouro FORJA:** `#dcd6c8` / `#4a4746`
- **Duplo Modo de Jogada:** Arrastar-e-soltar (*Drag-and-Drop* com peça flutuante e `touch-action: none` sem conflito de rolagem) + Toque-para-Mover (*Tap-to-Move*), pontos translúcidos para casas livres e anéis externos para capturas.
- **Pré-Lance (*Premove*):** Permite engatilhar seu próximo lance no turno do Bot com destaque coral, disparando automaticamente em `0 ms` assim que o adversário joga.
- **Setas Táticas & Marcação de Casas:** Modo Seta no celular e botão direito no desktop para desenhar setas vetoriais de cálculo sobre o tabuleiro.
- **Síntese Acústica WebAudio & Haptics:** Sons percussivos distintos de madeira para lance, captura, roque, xeque, promoção, acerto tático e fim de jogo.

### 2.3. Motor Soberano PeSTO + Negamax Alpha-Beta Zero-Alocação (`0x88`)
- **Avaliação Híbrida Tapered Eval (PeSTO):** Interpolação contínua entre tabelas posicionais de Meio-Jogo (`MG`) e Final (`EG`), bônus de par de Bispos, penalidade de peões dobrados e heurística *Mop-Up* de canto para conduzir mates elementares no final.
- **Busca Tática Acelerada (`0x88` + Zobrist `BigInt` TT):** Iterative Deepening Negamax com poda Alpha-Beta, Quiescence Search *Fail-Soft* com evasões completas de xeque, Tabela de Transposição Zobrist de 64 bits com normalização de distância de mate, ordenação MVV-LVA e *Killer Heuristic*.
- **8 Personalidades Calibradas (`400` a `2400` Elo):**
  1. `🌱 Marco (Iniciante)` — **400 Elo**
  2. `⚡ Sofia (Casual)` — **800 Elo**
  3. `🔥 David Goggins` — **1150 Elo**
  4. `🦊 Nicolau Maquiavel` — **1400 Elo**
  5. `🧪 Senku Ishigami` — **1650 Elo**
  6. `⚡ Nikola Tesla` — **1900 Elo**
  7. `⏳ O Doutor` — **2150 Elo**
  8. `👑 Magnus Soberano` — **2400 Elo**
- **Relógios Digitais Fischer + 2 Jogadores Local:** Presets `Bullet (1|0, 2|1)`, `Blitz (3|0, 3|2, 5|0)`, `Rápido (10|0, 15|10)`, `Clássico (30|0)` e `Sem Relógio`, com precisão de décimos de segundo abaixo de 20s, mais modo **2 Jogadores (Passa-e-Joga)** e **Modo Treinador Assistido** (Barra de Avaliação ao vivo + Dica Explicada + Voltar Lance).

### 2.4. Revisão Completa da Partida (*Game Review* — CAPS `%` + 9 Selos)
- **Precisão CAPS (`0% – 100%`)** para Brancas e Pretas baseada na queda de probabilidade esperada de vitória lance a lance.
- **Todos os 9 Selos Oficiais Estilo Chess.com:**
  - `!!` **Brilhante** (sacrifício tático calculado em casa defendida mantendo vantagem)
  - `!` **Grande Lance** (único recurso forte que salva ou decide a partida)
  - `★` **Melhor Lance** | `✓` **Excelente** | `👍` **Bom** | `📖` **Teoria (Livro ECO)**
  - `?!` **Imprecisão** | `?` **Erro** | `??` **Capivarada**
- **Gráfico Interativo SVG de Vantagem + Botão "🎯 Tentar Melhor":** Permite clicar em qualquer momento crítico e refazer o erro diretamente no tabuleiro até achar o lance de mestre, além de incluir a **Partida Imortal da Ópera (Paul Morphy, Paris, 1858)** pronta para demonstração imediata.

### 2.5. Problemas Táticos, Problema Diário & Puzzle Rush + Explorador ECO (`49` Aberturas)
- **24 Problemas Táticos 100% Verificados por Motor:** De Mate do Corredor (`480` Elo) até Mate de Morphy, Legado Completo de Philidor em 4 lances, Subpromoção para Cavalo (`e8=C+!`), Tesouras de Boden, Mate de Légal, Porcos Cegos de Nimzowitsch e Xeque-Mate *En Passant* (`2260` Elo).
- **🔥 Corrida de Problemas (*Puzzle Rush* — 3 Minutos / 3 Vidas ❤️❤️❤️)** + **📅 Problema Diário Determinístico**.
- **📖 Análise Multi-PV (3 Linhas Simultâneas) & Enciclopédia ECO (`49` Aberturas `A00`–`E60`) + Importação/Exportação `PGN` e `FEN`**.
- **Integração Direta ao Radar Polímata 10D:** Partidas e problemas resolvidos alimentam automaticamente os eixos **Lógica & Numeracia** e **Estratégia & Sistemas**.

---

## 3. Ficha Criptográfica & Instalação Android (`Forja_Apice_v13.0.apk`)

| Propriedade | Valor Verificado |
| :--- | :--- |
| **Arquivo APK** | `Forja_Apice_v13.0.apk` |
| **Application ID** | `br.forja.apice` |
| **Versão** | `13.0.0` (`versionCode: 1300`) |
| **Android Compatível** | Android 7.0 Nougat (`API 24`) até Android 14/15 (`API 34+`) |
| **Permissões de Rede** | **ZERO** (`100% Offline Soberano`) |
| **Tamanho do Pacote** | `390.169 bytes` (`~382 KB`) |
| **SHA-256 do APK** | `006e0598ef44aa4c1ba3aabdbb3408eabfa0282258b5e7a456b3a889b12ff16b` |
| **MD5 do APK** | `bb7a0075065206b84f6c3de7175410b7` |
| **Certificado X.509 (SHA-256)** | `7776d91f738ac3463768a0e62673a319f1b1ec07cd94bdb1d7115f341edd92b5` (Esquemas v2 + v3) |

### Como Instalar ou Atualizar sem Perder Dados
1. Baixe `Forja_Apice_v13.0.apk` no seu celular Android.
2. Toque no arquivo `.apk` (como o certificado X.509 é idêntico ao das versões anteriores, você pode **atualizar diretamente por cima da `v12.0` / `v11.0`** mantendo todo o seu histórico e Cofre intactos!).
3. Abra o app e toque no ícone **👑 Xadrez** na barra inferior para entrar imediatamente na Arena Grande Mestre!
