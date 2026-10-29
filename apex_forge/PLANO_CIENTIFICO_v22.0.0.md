# PLANO CIENTÍFICO — v22.0.0 (FORJA APICE)

**Princípio standing:** "primeiro monte um plano pra chegar a isso, quero a base definitiva"  
**Regra absoluta:** zero erros, zero pseudociência. Toda afirmação cita fonte primária verificável.  
**Instrução standing:** "CONTINUE IMPLEMENTANDO ENSINAMENTOS"

---

## 1. ESTADO ATUAL (v21.0.0)

| Módulo | Estado | Detalhe |
|--------|--------|---------|
| Lições soberanas | 80 / 10 pilares | 4 por pilar x 10 pilares (Grau IV • Polimata) |
| Volume II (Bicentenary) | 40 lições | 4 por pilar x 10 pilares (Grau II-III) |
| Volume I (Canônicas) | 160 lições | 16 por pilar x 10 pilares (Grau I-II) |
| Total lições catálogo | 280 | 28 por pilar |
| Balanço por grau | 50/50/50/130 | Tier 4 sobressai |
| Exercícios físicos | ~25 | Iniciante (~15) + Intermediário (10) |
| Desafios cognitivos | 8 tipos | 4 originais + 4 novos (v21) |
| Xadrez (XADREZ 2.0) | 100% core parity | FIDE, 8 bots, ECO, CAPS, puzzles, Chess960 |
| ENGINE_VERSION | 21.0.0 | APK v21.0 assinado v2+v3, ZIPALIGN_OK |

---

## 2. PROPOSTA v22.0.0 — "Volume IV: Síntese Transdisciplinar"

### Objetivo principal
Adicionar **20 novas lições (2 por pilar × 10 pilares)** como **Volume IV — Síntese Transdisciplinar**, elevando o catálogo de 280 para **300 lições totais (30 por pilar)**. Cada lição do Volume IV integra conceitos de múltiplos pilares, aplicando o aprendizado de forma integrada e transdisciplinar.

### 2.1 Estrutura do Volume IV (20 lições, Grau IV)

Cada pilar recebe 2 lições novas que conectam o tema do pilar com pelo menos outro pilar, promovendo síntese transdisciplinar:

| Pilar | Lição 1 | Lição 2 | Integração transdisciplinar |
|-------|---------|---------|----------------------------|
| Cristo & Evangelhos | Serviço + Ciência | Perdão + Neurociência | Servir como prática científica; perdão e regulação emocional |
| Sabedoria Bíblica | Provérbios + Lógica | Eclesiastes + Estatística | Sabedoria bíblica e raciocínio lógico; vanidade e dados |
| Garra & Autodomínio | Goggins + Hábitos | Disciplina + Sono | Autodomínio e formação de hábitos; sono e performance |
| Aprendizagem & Memória | Feynman + Xadrez | Espaçamento + Música | Ensinar através do xadrez; repetição espaçada em artes |
| Comunicação & Social | Covey + Negociação | Sinergia + Trabalho em equipe | Comunicação não-violenta; sinergia em grupos |
| Lógica & Numeracia | Kahneman + Decisão | Bayes + Evidência | Vieses cognitivos em decisões de vida; atualização bayesiana |
| Ciência & Primeiros Princípios | Musk + Engenharia | Popper + Falsificação | Primeiros princípios em engenharia; método científico diário |
| Estratégia & Sistemas | Maquiaveli + Jogo | Sun Tzu + Sistemas | Estratégia em jogos; pensamento sistêmico |
| Antivieses & Decisão | Tetlock + Previsão | Confirmação + Ciência | Superprevisão em ciência; viés de confirmação na pesquisa |
| Corpo & Longevidade | Paluch + Movimento | Isométrico + Pressão | Passos e longevidade; exercício isométrico e saúde cardiovascular |

### 2.2 Base científica para cada lição

Cada lição cita pelo menos 2 fontes primárias verificáveis, integrando o pilar principal com o pilar secundário. Exemplo de estrutura:

- **coreEssence:** Síntese dos dois pilares
- **scientificSource:** Duas fontes primárias (uma de cada pilar)
- **zeroStepExample:** Ação integrada
- **fieldMission:** Missão que aplica ambos os domínios
- **dilemmaPrompt:** Dilema que exige equilíbrio entre os dois domínios

### 2.3 Atualização de balanço

Novo balanço: 50/50/50/150 (tiers 1-3 mantêm 50 cada, tier 4 sobe de 130 para 150 com as 20 novas lições do Volume IV).

Total: 300 lições, 30 por pilar.

---

## 3. MELHORIAS AUXILIARES v22.0.0

### 3.1 Áudio Biofeedback (audioBiofeedback.ts)
Verificar se o serviço de áudio está funcional e integrar com os desafios cognitivos (feedback sonoro para acertos/erros).

### 3.2 Vault Storage (vaultStorage.ts)
Verificar integridade do armazenamento de progresso de lições e exercícios.

### 3.3 Testes
Adicionar testes para as 20 novas lições do Volume IV (verificação de unicidade de IDs, títulos, fontes científicas, dilemas).

---

## 4. CRITÉRIOS DE ACEITAÇÃO v22.0.0

1. `tsc --noEmit`: 0 erros
2. `vitest run`: 100% dos testes passando
3. `vite build`: todos chunks < 500 kB
4. Catálogo: exatamente 300 lições, 30 por pilar, balanço 50/50/50/150
5. Todas as 20 novas lições têm: ID único, título único, fonte científica verificável, dilema com 4 opções, índice de resposta correta válido
6. APK: Forja_Apice_v22.0.apk, ZIPALIGN_OK, v2+v3 assinado
7. Git: commit e push em `arena/99fae7df-projeto-estudo-de-re`

---

## 5. ORDEM DE IMPLEMENTAÇÃO

1. Adicionar 20 lições do Volume IV a teachingsSovereignty40.ts (ou novo arquivo teachingsVolume4.ts)
2. Atualizar teachingsCatalog.ts para incluir as novas lições
3. Atualizar testes para 300 lições e balanço 50/50/50/150
4. tsc + vitest → corrigir erros
5. vite build → verificar chunks
6. build APK v22.0 → verificar ZIPALIGN + assinatura
7. git commit + push

---

## 6. FONTES CIENTÍFICAS CENTRAIS (v22.0.0)

Todas verificáveis, já utilizadas ou novas:

- Mateus 6:33; McCullough et al. (2002) — Serviço e gratidão
- Witvliet et al. (2001) — Perdão e fisiologia
- Provérbios 2:6; Stanovich & West (2000) — Sabedoria e raciocínio
- Eclesiastes 1:2; Kahneman & Tversky (1979) — Vaidade e vieses
- Goggins (2018); Lally et al. (2010) — Autodomínio e formação de hábitos
- Walker (2017); Paluch et al. (2022) — Sono e passos/longevidade
- Feynman (1985); Gobet & Simon (1996) — Ensinar e template theory em xadrez
- Cepeda et al. (2006); Dallaway (2022) — Espaçamento em artes/música
- Covey (1989); Fisher & Ury (1981) — Comunicação e negociação
- Kahneman (2011); Tetlock (2015) — Vieses e superprevisão
- Popper (1934); Musk (entrevistas) — Falsificação e primeiros princípios
- Maquiaveli (1513); Sun Tzu (século VI a.C.) — Estratégia e sistemas
- Edwards et al. (2023); Leong et al. (2015) — Isométrico e força/longevidade

---

*Plano elaborado em 2026-10-28. Base científica: estudos primários verificáveis, zero pseudociência.*