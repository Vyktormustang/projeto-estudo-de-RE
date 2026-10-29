import { PieceSymbol, Square } from 'chess.js';

export const EMPTY_BOARD_FEN = '4k3/8/8/8/8/8/8/4K3 w - - 0 1';

export const ALL_64_SQUARES: Square[] = (() => {
  const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] as const;
  const out: Square[] = [];
  for (let r = 1; r <= 8; r++) {
    for (const f of files) {
      out.push(`${f}${r}` as Square);
    }
  }
  return out;
})();

export interface Chess960Setup {
  id: number; // 0..959 (#518 = Posicao Classica FIDE)
  scharnaglId: number; // 0..959 (#518 = Posicao Classica FIDE)
  backRankUpper: string;
  fen: string;
  isClassical518: boolean;
}

const KNIGHT_PAIRS_5: [number, number][] = [
  [0, 1],
  [0, 2],
  [0, 3],
  [0, 4],
  [1, 2],
  [1, 3],
  [1, 4],
  [2, 3],
  [2, 4],
  [3, 4],
];

/**
 * Gerador Bijetivo Oficial de Scharnagl (0..959) para Xadrez Aleatorio de Fischer (Chess960).
 * Garante matematicamente:
 *  - Bispos em cores opostas
 *  - Rei estritamente entre as duas Torres
 *  - #518 = RNBQKBNR (Posicao Inicial Classica FIDE)
 */
export function generateChess960Position(rawId: number): Chess960Setup {
  const id = ((Math.floor(rawId) % 960) + 960) % 960;
  const rank: (PieceSymbol | null)[] = Array(8).fill(null);

  // 1. Bispo de casa clara (b1=1, d1=3, f1=5, h1=7)
  const n1 = id % 4;
  const q1 = Math.floor(id / 4);
  rank[2 * n1 + 1] = 'b';

  // 2. Bispo de casa escura (a1=0, c1=2, e1=4, g1=6)
  const n2 = q1 % 4;
  const q2 = Math.floor(q1 / 4);
  rank[2 * n2] = 'b';

  // 3. Dama em uma das 6 casas vazias restantes
  const n3 = q2 % 6;
  const q3 = Math.floor(q2 / 6); // 0..9
  const emptyAfterBishops: number[] = [];
  for (let i = 0; i < 8; i++) {
    if (!rank[i]) emptyAfterBishops.push(i);
  }
  rank[emptyAfterBishops[n3]] = 'q';

  // 4. Dois Cavalos entre as 5 casas vazias restantes (Tabela KRN de Scharnagl)
  const emptyAfterQueen: number[] = [];
  for (let i = 0; i < 8; i++) {
    if (!rank[i]) emptyAfterQueen.push(i);
  }
  const [kIdx1, kIdx2] = KNIGHT_PAIRS_5[q3];
  rank[emptyAfterQueen[kIdx1]] = 'n';
  rank[emptyAfterQueen[kIdx2]] = 'n';

  // 5. Torre - Rei - Torre nas 3 ultimas casas vazias
  const finalThree: number[] = [];
  for (let i = 0; i < 8; i++) {
    if (!rank[i]) finalThree.push(i);
  }
  rank[finalThree[0]] = 'r';
  rank[finalThree[1]] = 'k';
  rank[finalThree[2]] = 'r';

  const lower = rank.join('');
  const upper = lower.toUpperCase();

  // Direitos de roque compativeis com chess.js padrao quando Rei esta em e1/e8 e Torres em a1/h1
  let castle = '';
  if (rank[4] === 'k') {
    if (rank[7] === 'r') castle += 'K';
    if (rank[0] === 'r') castle += 'Q';
    if (rank[7] === 'r') castle += 'k';
    if (rank[0] === 'r') castle += 'q';
  }
  if (!castle) castle = '-';

  const fen = `${lower}/pppppppp/8/8/8/8/PPPPPPPP/${upper} w ${castle} - 0 1`;

  return {
    id,
    scharnaglId: id,
    backRankUpper: upper,
    fen,
    isClassical518: id === 518,
  };
}

// ============================================================================
// TREINADOR DE FINAIS ESSENCIAIS (JOGAR E CONVERTER CONTRA O MOTOR 2400 ELO!)
// ============================================================================
export interface EndgameDrillSpec {
  id: string;
  titlePt: string;
  categoryPt: string;
  difficultyLabel: string;
  fen: string;
  userColor: 'w' | 'b';
  goalType: 'WIN' | 'HOLD_DRAW';
  maxTargetMoves: number;
  principleSummaryPt: string;
  stepByStepHintPt: string;
}

export type ChessEndgameDrill = EndgameDrillSpec;

export const CHESS_ENDGAME_DRILLS: EndgameDrillSpec[] = [
  {
    id: 'end_01_escada_duas_torres',
    titlePt: '1. Escada Linear (2 Torres vs Rei)',
    categoryPt: 'Mate Elementar • Grau I',
    difficultyLabel: 'Iniciante',
    fen: '4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1',
    userColor: 'w',
    goalType: 'WIN',
    maxTargetMoves: 15,
    principleSummaryPt:
      'Uma Torre corta a fileira como uma barreira elétrica enquanto a outra empurra o Rei fileira por fileira até a 8ª.',
    stepByStepHintPt:
      'Alterne Ta4 → Th5 → Ta6 → Th7 → Ta8#! Se o Rei inimigo encostar numa Torre, transfira-a para o outro flanco sem perder o corte.',
  },
  {
    id: 'end_02_dama_e_rei',
    titlePt: '2. Dama + Rei vs Rei Solitário',
    categoryPt: 'Mate Elementar • Grau I',
    difficultyLabel: 'Iniciante',
    fen: '4k3/8/8/8/8/8/8/3QK3 w - - 0 1',
    userColor: 'w',
    goalType: 'WIN',
    maxTargetMoves: 18,
    principleSummaryPt:
      'Posicione a Dama a um "salto de Cavalo" do Rei adversário para encolher a caixa até o canto — CUIDADO apenas com o afogamento no canto!',
    stepByStepHintPt:
      'Quando o Rei preto ficar preso na última fileira (ex: g8/h8), mantenha a Dama na 7ª ou coluna f deixando 2 casas até aproximar seu Rei para o beijo fatal!',
  },
  {
    id: 'end_03_torre_e_rei_caixa',
    titlePt: '3. Torre + Rei vs Rei (Método da Caixa)',
    categoryPt: 'Mate Fundamental • Grau II',
    difficultyLabel: 'Essencial',
    fen: '4k3/8/8/8/8/8/8/4K2R w K - 0 1',
    userColor: 'w',
    goalType: 'WIN',
    maxTargetMoves: 28,
    principleSummaryPt:
      'A Torre sozinha não dá mate: ela corta o tabuleiro e o SEU Rei avança para tomar a oposição e aplicar o xeque-mate na borda!',
    stepByStepHintPt:
      '1) Corte o Rei preto com Th4/Th5; 2) Aproxime seu Rei; 3) Quando os Reis ficarem frente a frente em oposição, dê xeque lateral com a Torre!',
  },
  {
    id: 'end_04_oposicao_direta_peao',
    titlePt: '4. Rei + Peão vs Rei (Lei da Oposição)',
    categoryPt: 'Final de Peões • Grau II',
    difficultyLabel: 'Clássico',
    fen: '4k3/8/8/8/8/4K3/4P3/8 w - - 0 1',
    userColor: 'w',
    goalType: 'WIN',
    maxTargetMoves: 22,
    principleSummaryPt:
      'Regra de Ouro de Capablanca: o Rei SEMPRE avança NA FRENTE do peão! Nunca empurre o peão cedo demais.',
    stepByStepHintPt:
      'Jogue 1.Rd4! (ou Rf4) subindo com o Rei até a 6ª fileira (d6/e6/f6) ANTES de avançar o peão e2-e4-e5-e6-e7-e8=D!',
  },
  {
    id: 'end_05_peao_distante_isca',
    titlePt: '5. O Peão Passado Distante (Isca Real)',
    categoryPt: 'Final de Peões • Grau III',
    difficultyLabel: 'Intermediário',
    fen: '8/5pkp/6p1/P7/8/6P1/5PKP/8 w - - 0 1',
    userColor: 'w',
    goalType: 'WIN',
    maxTargetMoves: 30,
    principleSummaryPt:
      'O peão passado na coluna a funciona como um ímã: enquanto o Rei preto corre até a ala da dama para capturá-lo, seu Rei invade e devora a ala do rei!',
    stepByStepHintPt:
      'Avance a5-a6 forçando o Rei preto a se afastar de f7/g6/h7, e marche com seu Rei pelo centro rumo a f4-e5-f6!',
  },
  {
    id: 'end_06_ponte_de_lucena',
    titlePt: '6. A Ponte de Lucena (1634)',
    categoryPt: 'Final de Torres • Grau III',
    difficultyLabel: 'Mestre',
    fen: '1K1k4/1P6/8/8/8/8/2r5/3R4 w - - 0 1',
    userColor: 'w',
    goalType: 'WIN',
    maxTargetMoves: 20,
    principleSummaryPt:
      'A posição mais importante de todos os finais de Torre! Construa uma "ponte" na 4ª fileira para escudar seu Rei contra os xeques verticais e coroar b8=D.',
    stepByStepHintPt:
      '1.Td4+! Re7 2.Ra7! Tc1 3.Rb6! Tb1+ 4.Rc6! Tc1+ 5.Rb5! Tb1+ 6.Tb4! ("A Ponte" que escuda seu Rei e garante b8=D!).',
  },
  {
    id: 'end_07_fortaleza_philidor_empate',
    titlePt: '7. Defesa de Philidor (Segurar o Empate!)',
    categoryPt: 'Defesa Técnica • Grau IV',
    difficultyLabel: 'Avançado',
    fen: '4k3/R7/8/3KP3/8/8/8/4r3 b - - 0 1',
    userColor: 'b',
    goalType: 'HOLD_DRAW',
    maxTargetMoves: 18,
    principleSummaryPt:
      'Você está de Pretas com 1 peão a menos! Corte a 6ª fileira (3ª das Pretas: Te6!) impedindo o Rei branco de avançar; assim que o peão avançar para e6, vá para e1 dar xeques eternos por trás!',
    stepByStepHintPt:
      'Jogue 1...Te6!! mantendo a barreira na 6ª fileira. Só saia para a 1ª fileira no exato instante em que as Brancas jogarem e5-e6!',
  },
  {
    id: 'end_08_par_de_bispos',
    titlePt: '8. Par de Bispos vs Rei Solitário',
    categoryPt: 'Coordenação Geométrica • Grau IV',
    difficultyLabel: 'Grande Mestre',
    fen: '4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1',
    userColor: 'w',
    goalType: 'WIN',
    maxTargetMoves: 35,
    principleSummaryPt:
      'Dois Bispos lado a lado erguem uma muralha diagonal intransponível! Empurre o Rei ao canto com ajuda ativa do seu próprio Rei.',
    stepByStepHintPt:
      'Centralize os dois Bispos lado a lado (ex: d4 e e4), avance o Rei branco em conjunto e feche o cerco num dos cantos!',
  },
];

// ============================================================================
// ACADEMIA GUIADA INTERATIVA DE XADREZ (DO MARCO ZERO A ESTRATEGIA DE MESTRE)
// ============================================================================
export interface InteractiveChessStep {
  fen: string;
  instructionPt: string;
  expectedLan: string[]; // Aceita qualquer lance equivalente da lista (ex: e2e4 ou d2d4)
  autoReplyLan?: string;
  successCoachPt: string;
  wrongMoveCoachPt?: string;
}

export interface InteractiveChessLesson {
  id: string;
  titlePt: string;
  tierLabel: string;
  conceptSummaryPt: string;
  scientificNotePt: string;
  steps: InteractiveChessStep[];
}

export type ChessAcademyLesson = InteractiveChessLesson;

export const CHESS_ACADEMY_LESSONS: InteractiveChessLesson[] = [
  {
    id: 'acad_chess_01_abertura_ouro',
    titlePt: '1. Os 3 Princípios de Ouro da Abertura',
    tierLabel: 'Grau I • Marco Zero',
    conceptSummaryPt:
      'Nunca decore 20 lances cegos antes de dominar as 3 leis universais: (1) Ocupe o Centro, (2) Desenvolva Cavalos e Bispos, (3) Faça o Roque cedo!',
    scientificNotePt:
      'Gobet & Simon (1996): Mestres constroem templates de abertura em torno da harmonia central e segurança do Rei.',
    steps: [
      {
        fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
        instructionPt:
          'Passo 1/3 — Domine o centro imediatamente avançando o peão do Rei duas casas (e2-e4)!',
        expectedLan: ['e2e4'],
        successCoachPt:
          'Perfeito! 1.e4 controla d5 e f5 e abre linhas imediatas para o Bispo de f1 e a Dama.',
      },
      {
        fen: 'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 2',
        instructionPt:
          'Passo 2/3 — Desenvolva o Bispo para uma diagonal ativa mirando f7 (Bf1-c4)!',
        expectedLan: ['f1c4'],
        successCoachPt:
          'Excelente! Bc4 desenvolve peça menor apontando para o ponto mais frágil das Pretas (f7) e libera e1-g1.',
      },
      {
        fen: 'r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4',
        instructionPt:
          'Passo 3/3 — Coloque seu Rei em segurança e ative a Torre fazendo o Roque Curto (Re1-g1)!',
        expectedLan: ['e1g1'],
        successCoachPt:
          'Domínio completo! Em apenas 4 lances você controlou o centro, desenvolveu peças e abrigou o Rei!',
      },
    ],
  },
  {
    id: 'acad_chess_02_metodo_cct',
    titlePt: '2. O Algoritmo Mental CCT (Xeques, Capturas, Ameaças)',
    tierLabel: 'Grau I • Cálculo Limpo',
    conceptSummaryPt:
      'Para nunca mais entregar peças nem perder vitórias imediatas, examine SEMPRE nesta ordem estrita antes de tocar na peça: 1º Xeques, 2º Capturas, 3º Ameaças (seus E do adversário!).',
    scientificNotePt:
      'Burgoyne et al. (Intelligence, 2016): O cálculo estruturado acopla memória de trabalho (r=.25) à velocidade executiva.',
    steps: [
      {
        fen: 'r1bqk1nr/pppp1ppp/2n5/2b1p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
        instructionPt:
          'Passo 1/2 — Aplique o filtro #1 (Xeques!): encontre o xeque que é captura E xeque-mate imediato!',
        expectedLan: ['h5f7'],
        successCoachPt:
          'Exato! Dxf7# passa pelo filtro #1 (Xeque) e encerra a partida na hora!',
      },
      {
        fen: 'r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 3 3',
        instructionPt:
          'Passo 2/2 — Agora olhe pelos olhos das Pretas (Galinsky 2008): as Brancas ameaçam Dxf7#! Defenda f7 bloqueando com g7-g6!',
        expectedLan: ['g7g6'],
        successCoachPt:
          'Brilhante! 3...g6 bloqueia a diagonal da Dama contra f7 e ganha tempo atacando a Dama branca!',
      },
    ],
  },
  {
    id: 'acad_chess_03_triade_tatica',
    titlePt: '3. A Tríade Tática: Garfo, Cravada & Espeto',
    tierLabel: 'Grau II • Artífice Tático',
    conceptSummaryPt:
      '90% das partidas até 1800 Elo são decididas por ataques duplos (Garfos) e alinhamentos geométricos (Cravadas e Espetos).',
    scientificNotePt:
      'Reconhecimento de geometria relacional ataque-defesa (McGregor & Howes, Memory & Cognition, 2002).',
    steps: [
      {
        fen: 'r3k2r/ppp2ppp/8/3N4/8/8/PPP2PPP/4K3 w kq - 0 1',
        instructionPt:
          'Passo 1/3 (Garfo) — Use o Cavalo em d5 para atacar simultaneamente o Rei em e8 e a Torre em a8!',
        expectedLan: ['d5c7'],
        successCoachPt:
          'Garfo real perfeito! Cc7+ obriga o Rei a se mover e captura a Torre em a8.',
      },
      {
        fen: 'r1bqkbnr/ppp2ppp/2n5/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3',
        instructionPt:
          'Passo 2/3 (Cravada Absoluta) — Crave o Cavalo de c6 contra o Rei preto em e8 desenvolvendo o Bispo para b5 (Bf1-b5)!',
        expectedLan: ['f1b5'],
        successCoachPt:
          'Cravada absoluta perfeita! O Cavalo em c6 está proibido pelas regras de sair da diagonal b5-e8, deixando o peão e5 indefeso!',
      },
      {
        fen: '3q4/8/8/3k4/8/8/5PPP/1R4K1 w - - 0 1',
        instructionPt:
          'Passo 3/3 (Espeto / Raio-X) — Dê xeque na coluna d alinhando o Rei preto na frente da Dama preta!',
        expectedLan: ['b1d1'],
        successCoachPt:
          'Espeto cirúrgico! Td1+ obriga o Rei a sair da coluna e entrega a Dama em d8!',
      },
    ],
  },
  {
    id: 'acad_chess_04_profilaxia_nimzowitsch',
    titlePt: '4. Profilaxia & Respiro do Rei (Luft)',
    tierLabel: 'Grau III • Estrategista',
    conceptSummaryPt:
      'Aron Nimzowitsch ensinou a pergunta suprema da estratégia: "O que meu adversário quer fazer se eu passasse a vez?" Neutralize o golpe antes que ele exista!',
    scientificNotePt:
      'Tomada de perspectiva cognitiva estratégica (Galinsky, Maddux, Gilin & White, Psychological Science, 2008).',
    steps: [
      {
        fen: '3r2k1/5ppp/8/8/8/8/5PPP/2R3K1 b - - 0 1',
        instructionPt:
          'Passo 1/2 — Você está de Pretas e as Brancas ameaçam Tc8! Crie imediatamente uma "janela de respiro" (Luft) para o Rei com h7-h6 ou g7-g6!',
        expectedLan: ['h7h6', 'g7g6'],
        successCoachPt:
          'Profilaxia impecável! Um simples lance de peão cria a casa de fuga h7/g7 e anula para sempre o mate do corredor!',
      },
      {
        fen: 'r1bq1rk1/ppp2ppp/2np1n2/2b1p1B1/2B1P3/2NP1N2/PPP2PPP/R2Q1RK1 b - - 0 7',
        instructionPt:
          'Passo 2/2 — As Brancas querem saltar Cd5 esmagando f6! Impeça Cd5 e questione o Bispo jogando h7-h6!',
        expectedLan: ['h7h6', 'c8e6'],
        successCoachPt:
          'Visão posicional limpa! Você neutralizou a pressão sobre f6 antes que Cd5 entrasse com força.',
      },
    ],
  },
  {
    id: 'acad_chess_05_sacrificios_classicos',
    titlePt: '5. Sacrifícios Clássicos contra o Roque (Presente de Grego)',
    tierLabel: 'Grau III • Ataque ao Rei',
    conceptSummaryPt:
      'Quando você tem Bispo em d3/c4, Cavalo pronto para g5 e Dama pronta para h5 sem Cavalo defensor em f6, o sacrifício Bxh7+!! destrói a fortaleza real!',
    scientificNotePt:
      'Templates táticos de ataque ao roque (Gobet & Clarkson, 2004).',
    steps: [
      {
        fen: 'r1bq1rk1/ppp2ppp/2n1p3/3pP3/3P4/2PB1N2/PP3PPP/R1BQK2R w KQ - 0 8',
        instructionPt:
          'Passo 1/2 — Não há Cavalo preto em f6! Detone o escudo do Rei preto com o Presente de Grego: Bd3xh7+!',
        expectedLan: ['d3h7'],
        successCoachPt:
          'Bxh7+!! atrai o Rei preto para fora da proteção! Após 1...Rxh7 segue Cg5+!',
      },
      {
        fen: 'r1bq1r2/ppp2ppk/2n1p3/3pP3/3P4/2P2N2/PP3PPP/R1BQK2R w KQ - 0 9',
        instructionPt:
          'Passo 2/2 — Continue o ataque com tempo dando xeque de Cavalo em g5 (Cf3-g5+) abrindo a diagonal da Dama para h5!',
        expectedLan: ['f3g5'],
        successCoachPt:
          'Ataque devastador! Cg5+ seguido de Dh5 cria ameaças letais de mate em h7!',
      },
    ],
  },
  {
    id: 'acad_chess_06_oposicao_e_regra_quadrado',
    titlePt: '6. Maestria nos Finais: Oposição & Regra do Quadrado',
    tierLabel: 'Grau IV • Polímata dos Finais',
    conceptSummaryPt:
      'José Raúl Capablanca recomendava estudar o xadrez de trás para frente (começando pelos finais!). Quem domina a Oposição de Reis sabe exatamente quando trocar todas as peças.',
    scientificNotePt:
      'Cálculo exato por invariantes de paridade no final de partida.',
    steps: [
      {
        fen: '8/4k3/8/8/3KP3/8/8/8 w - - 0 1',
        instructionPt:
          'Passo 1/2 (Oposição Direta) — Avance seu Rei na frente do peão tomando a Oposição Frontal contra Re7 (Rd4-e5)!',
        expectedLan: ['d4e5'],
        successCoachPt:
          'Exato!! 1.Re5! toma a oposição direta frente a frente com Re7, forçando o Rei preto a ceder passagem para d6 ou f6!',
      },
      {
        fen: '7k/8/8/p7/8/8/5K2/8 w - - 0 1',
        instructionPt:
          'Passo 2/2 (Regra do Quadrado) — O peão preto em a5 está a 4 casas de a1 (quadrado a5-e5-e1-a1). Entre imediatamente no quadrado jogando Rf2-e3!',
        expectedLan: ['f2e3', 'f2e2', 'f2e1'],
        successCoachPt:
          'Domínio matemático! Ao pisar na coluna e dentro do quadrado, seu Rei alcança o peão a tempo e garante o empate!',
      },
    ],
  },
];
