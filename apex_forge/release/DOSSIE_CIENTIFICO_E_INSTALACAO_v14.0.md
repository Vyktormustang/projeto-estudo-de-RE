# FORJA — Sistema do Ápice v14.0.0
## *A Edição do Bicentenário Polímata 200 & Xadrez Chess.com Completo 2.0*

---

## 1. Identidade Criptográfica & Binário Android (`APK`)

| Parâmetro Técnico | Valor Verificado |
| :--- | :--- |
| **Arquivo Entregue** | `Forja_Apice_v14.0.apk` |
| **Pacote Android (`applicationId`)** | `br.forja.apice` |
| **Versão (`versionName` / `versionCode`)** | `14.0.0` (`1400`) |
| **Compatibilidade Android** | `minSdkVersion 24` (Android 7.0) até `targetSdkVersion 34` (Android 14/15) |
| **Tamanho Exato do Binário** | `447.605 bytes` (`~437,1 KB`) |
| **Hash `SHA-256`** | `5cef9b632bcf9cb218d694c4d2ed045be98465e5ba6167c26a8a3277105b9b08` |
| **Hash `MD5`** | `702c9107a14eb59aec6455a933c2d602` |
| **Alinhamento & Empacotamento** | `zipalign -p 4` (`ZIPALIGN_OK`) + `resources.arsc` `ZIP_STORED` (descomprimido) |
| **Assinatura Criptográfica** | APK Signature Schemes `v2 + v3` (`apksigner verify` OK) |
| **Certificado X.509 (`SHA-256`)** | `7776d91f738ac3463768a0e62673a319f1b1ec07cd94bdb1d7115f341edd92b5` (atualização direta sobre `v11.0–v13.0` preservando 100% do Cofre!) |
| **Permissões de Rede** | **ZERO (`0`)** — 100% Soberano, Offline e Privado por Design (`https://forja.local/*`) |

---

## 2. O Que Há de Novo na `v14.0.0`

### I. Academia do Bicentenário Polímata (`200 Lições Canônicas — Simetria 50/50/50/50`)
Expansão integral da Árvore da Base Absoluta de `160` para **`200` lições interativas** (`+40` lições canônicas inéditas no Volume II `forja-codex-vol2`), mantendo **simetria matemática perfeita**:
- **10 Pilares Universais × 20 Lições = 200 Lições** (`5` de Grau I • Marco Zero, `5` de Grau II • Artífice, `5` de Grau III • Estrategista, `5` de Grau IV • Mestre Polímata em cada Pilar = **`50 / 50 / 50 / 50`**):
  1. **Jesus Cristo & Os Evangelhos (`20`):** *Lava-Pés (João 13)*, *O Bom Pastor (João 10)*, *O Jugo Suave (Mateus 11:28–30)* e *A Parábola das Dez Virgens (Mateus 25:1–13)*.
  2. **Sabedoria Bíblica (`20`):** *O Ferro Aguça o Ferro (Provérbios 27:17)*, * Neemias: A Espada e a Colher de Pedreiro (Neemias 4)*, *Daniel na Babilônia (Daniel 1:8; 6:10)* e *Remindo o Tempo (Salmo 90:12; Efésios 5:15–16)*.
  3. **Corpo, Força & Saúde (`20`):** *Dose Diária de Passos & Longevidade (Paluch et al., Lancet Public Health 2022)*, *Treino Unilateral & Déficit Bilateral*, *Rigidez Tendínea & Isometria Pesada* e *Periodização Ondulatória Diária Autoregulada (DUP)*.
  4. **Mente, Foco & Memória (`20`):** *Intenções de Implementação Se–Então (Gollwitzer & Sheeran, 2006 — $d = 0,65$)*, *Teoria de Chunks & Templates de Mestres (Gobet & Simon, 1996)*, *Razão Ótima Espaçamento/Retenção (Cepeda et al., 2006/2008)* e *Metacognição Online & Monitoramento de Erro*.
  5. **Comunicação & Persuasão (`20`):** *Comunicação Assertiva Estruturada (DESC)*, *Tomada de Perspectiva Cognitiva em Negociação (Galinsky et al., 2008)*, *Retórica Deliberativa Clássica* e *Comunicação de Risco Transparente*.
  6. **Lógica, Matemática & Finanças (`20`):** *Aritmética Modular & Invariantes de Paridade*, *Teoria dos Grafos & Caminhos Ótimos (Euler/Dijkstra)*, *Diversificação & Fronteira de Markowitz* e *Teoria da Informação & Entropia de Shannon*.
  7. **Aprendizado Acelerado (`20`):** *Prática Mental & Simulação Motora (Driskell et al., 1994)*, *Feedback Orientado à Tarefa (Kluger & DeNisi, 1996)*, *Decomposição de Sub-Habilidades Críticas* e *Transferência Distante por Princípios Profundos (Barnett & Ceci, 2002)*.
  8. **Domínio Emocional & Estoicismo (`20`):** *Aceitação Radical vs. Sofrimento Secundário*, *A Cidadela Interior de Marco Aurélio*, *Autocompaixão Disciplinada sem Autoindulgência (Neff, 2003)* e *Equanimidade sob Incerteza Extrema*.
  9. **Caráter, Virtude & Liderança (`20`):** *Pontualidade & Honra à Palavra Empenhada*, *Coragem Moral Diante da Conformidade de Grupo*, *Mordomia Intergeracional* e *Magnanimidade na Vitória & Firmeza na Adversidade*.
  10. **Estratégia, Xadrez & Sistemas (`20`):** *A Tríade do Método CCT no Xadrez (Xeques, Capturas e Ameaças)*, *Profilaxia Enxadrística & Pensamento Preventivo (Nimzowitsch)*, *A Lei dos Finais de Capablanca (Oposição, Quadrado & Lucena)* e *Teoria de Jogos Sequenciais & Indução Reversa (Zermelo / von Neumann)*.

### II. Suíte Soberana de Xadrez Estilo Chess.com 2.0 (`100% Core Parity`)
- **5 Sub-Modos Completos (`JOGAR | REVISAO | PROBLEMAS | TREINAR | ANALISE`):**
  1. **Variante Oficial `Chess960 / Freestyle` (`Scharnagl #0–#959`):** Gerador bijetivo completo das `960` posições iniciais oficiais de Bobby Fischer (`#518 = RNBQKBNR`), com sorteio instantâneo, seletor numérico `#0–#959`, visualização da fileira inicial e exportação/importação PGN compatível com `[SetUp "1"]` + `[FEN "..."]`.
  2. **Centro `🎓 TREINAR` (3 Módulos Interativos):**
     - **👁️ Visão de Coordenadas 30s (*Vision*):** Sprint cronometrado de 30 segundos para automatizar as 64 casas na visão das Brancas, das Pretas ou Alternada, com ou sem peças e modo cego sem bordas, gravando o recorde pessoal no Cofre.
     - **👑 8 Finais Essenciais Jogáveis vs Motor (`2400 Elo`):** *Escada Linear (2 Torres)*, *Dama + Rei*, *Torre + Rei (Caixa)*, *Rei + Peão (Oposição)*, *Peão Passado Distante (Isca)*, *Ponte de Lucena (1634)*, *Fortaleza de Philidor (Segurar o Empate)* e *Par de Bispos vs Rei* — jogáveis ao vivo até o mate ou sustentação teórica da fortaleza!
     - **🎓 6 Aulas Guiadas Passo a Passo no Tabuleiro:** *Princípios de Ouro da Abertura*, *Método CCT*, *Tríade Tática (Garfo, Cravada, Espeto)*, *Profilaxia de Nimzowitsch*, *Sacrifícios Clássicos (Presente de Grego)* e *Oposição & Regra do Quadrado*, com validação lance a lance, dicas visuais e comentários do Treinador.
  3. **36 Problemas Táticos Verificados por Motor + Puzzle Rush 3 min:** Expansão de `24` para `36` problemas (`puz_01`–`puz_36`), incluindo *Presente de Grego*, *Mate de Boden*, *Moinho de Vento (Torre + Bispo)*, * Promoção Menor para Cavalo*, *Ponte de Lucena*, *Regra do Quadrado*, *Oposição Direta* e *Zugzwang Recíproco* — 100% validados lance a lance contra `chess.js` e contra o motor Alpha-Beta.
  4. **Jogar da Posição contra o Motor (`Play from FEN`):** Em qualquer lance da **Revisão CAPS** ou em qualquer abertura/FEN do **Explorador ECO**, um toque em `⚔️ Jogar desta Posição vs Motor` carrega imediatamente a posição viva contra o Bot escolhido.
  5. **Histórico Enriquecido com Precisão `CAPS %` + Selos `!!` + Cópia `📋 PGN` + Atalho Diário na Aba `COMANDO`:** A precisão calculada na Revisão fica gravada na partida salva e o painel diário exibe o resumo vivo de Elo, Tática, Visão 30s e Finais Dominados.

---

## 3. Base Científica Primária Verificada (`v14.0.0`)

1. **Gobet, F., & Simon, H. A. (1996).** *Templates in chess memory: A mechanism for recalling several boards.* **Cognitive Psychology**, 31(1), 1–40.
2. **Burgoyne, A. P., Sala, G., Gobet, F., Macnamara, B. N., Campitelli, G., & Hambrick, D. Z. (2016/2018).** *The relationship between cognitive ability and chess skill: A comprehensive meta-analysis.* **Intelligence**, 59, 72–83 ($N = 1.779$).
3. **Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006 / 2008).** *Distributed practice in verbal recall tasks: A review and quantitative synthesis.* **Psychological Bulletin**, 132(3), 354–380 (317 experimentos) & **Psychological Science**, 19(11), 1095–1102.
4. **Gollwitzer, P. M., & Sheeran, P. (2006).** *Implementation intentions and goal achievement: A meta-analysis of effects and processes.* **Advances in Experimental Social Psychology**, 38, 69–119 (94 estudos, $N = 8.461$, $d = 0,65$).
5. **Paluch, A. E., et al. (2022).** *Daily steps and all-cause mortality: A meta-analysis of 15 international cohorts.* **The Lancet Public Health**, 7(3), e219–e228 ($N = 47.471$, `HR = 0,47–0,60`).
6. **Galinsky, A. D., Maddux, W. W., Gilin, D., & White, J. B. (2008).** *Why it pays to get inside the head of your opponent: The differential effects of perspective taking and empathy in negotiations.* **Psychological Science**, 19(4), 378–384.

---

## 4. Instruções Rápidas de Instalação no Android

1. Baixe `Forja_Apice_v14.0.apk` no seu celular Android.
2. Toque no arquivo `.apk` baixado (caso já possua `v11.0`, `v12.0` ou `v13.0` instalada, basta clicar em **Atualizar** — a assinatura X.509 idêntica preserva todo o seu histórico, treinos, ratings e lições!).
3. Abra o **FORJA v14.0**, explore a **Árvore de 200 Lições** na aba `PANTEÃO` e a suíte **Xadrez Chess.com 2.0** (`Clássico + Chess960 + Visão 30s + 8 Finais + 6 Aulas + 36 Problemas + Revisão CAPS`) na aba `XADREZ`!
