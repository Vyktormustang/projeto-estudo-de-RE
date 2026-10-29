import { Chess, Color, Move, PieceSymbol, Square } from 'chess.js';
import { ChessSavedGame, ChessVaultData } from '../types';
import { detectOpeningFromMoves, pickBookMoveForBot } from './openingBook';

export interface ChessBotProfile {
  id: string;
  name: string;
  titleBadge: string;
  elo: number;
  avatarCode: string;
  styleSummary: string;
  maxDepth: number;
  timeBudgetMs: number;
  noiseCp: number;       // Imprecisao aleatoria em centipeoes (0 para Mestre Supremo)
  blunderChance: number; // 0..1 chance de escolher lance sub-otimo humano
  quotes: {
    greeting: string;
    onCapture: string;
    onCheck: string;
    onGoodUserMove: string;
    onVictory: string;
    onDefeat: string;
  };
}

export const CHESS_BOTS: ChessBotProfile[] = [
  {
    id: 'bot_marco_400',
    name: 'Marco (Iniciante)',
    titleBadge: '400 Elo • Grau I',
    elo: 400,
    avatarCode: '🌱',
    styleSummary: 'Está aprendendo o movimento das peças e deixa táticas simples escaparem.',
    maxDepth: 1,
    timeBudgetMs: 90,
    noiseCp: 220,
    blunderChance: 0.42,
    quotes: {
      greeting: 'Vamos treinar juntos! Ainda confundo alguns garfos de Cavalo.',
      onCapture: 'Opa, consegui capturar uma peça!',
      onCheck: 'Xeque! Cuidado com o seu Rei!',
      onGoodUserMove: 'Boa jogada! Não tinha visto essa ideia.',
      onVictory: 'Uau, consegui vencer! Vamos jogar a revanche?',
      onDefeat: 'Muito bem jogado! Aprendi bastante nessa partida.',
    },
  },
  {
    id: 'bot_sofia_800',
    name: 'Sofia (Casual)',
    titleBadge: '800 Elo • Clube',
    elo: 800,
    avatarCode: '⚡',
    styleSummary: 'Desenvolve Cavalos e Bispos cedo, mas às vezes esquece a retaguarda.',
    maxDepth: 2,
    timeBudgetMs: 120,
    noiseCp: 125,
    blunderChance: 0.22,
    quotes: {
      greeting: 'Adoro partidas rápidas! Vamos ver quem domina o centro primeiro.',
      onCapture: 'Troca limpa no tabuleiro!',
      onCheck: 'Xeque direto no alvo!',
      onGoodUserMove: 'Lance forte! Agora preciso pensar com calma.',
      onVictory: 'Boa partida! Um detalhe tático decidiu.',
      onDefeat: 'Parabéns! Seu cálculo superou minha defesa.',
    },
  },
  {
    id: 'bot_goggins_1150',
    name: 'David Goggins',
    titleBadge: '1150 Elo • Incansável',
    elo: 1150,
    avatarCode: '🔥',
    styleSummary: 'Pressiona sem descanso, nunca entrega peça de graça e luta até o último peão.',
    maxDepth: 2,
    timeBudgetMs: 180,
    noiseCp: 65,
    blunderChance: 0.1,
    quotes: {
      greeting: 'Ninguém vem salvar o seu Rei! Mantenha a guarda alta nos 64 quadrados!',
      onCapture: 'Peça pendurada é peça perdida. Foco total!',
      onCheck: 'Xeque! Quem carrega os barcos sob pressão?!',
      onGoodUserMove: 'Forte! É assim que se caleja o córtex pré-frontal.',
      onVictory: 'Use essa derrota no seu Cookie Jar, revise o erro e volte mais forte!',
      onDefeat: 'Respeito máximo! Você não piscou sob pressão. Stay hard!',
    },
  },
  {
    id: 'bot_maquiavel_1400',
    name: 'Nicolau Maquiavel',
    titleBadge: '1400 Elo • Estrategista',
    elo: 1400,
    avatarCode: '🛡️',
    styleSummary: 'Constrói diques posicionais sólidos, cravadas sutis e contra-ataques frios.',
    maxDepth: 3,
    timeBudgetMs: 240,
    noiseCp: 35,
    blunderChance: 0.04,
    quotes: {
      greeting: 'Príncipes imprudentes olham apenas o próximo lance; sábios preparam diques três jogadas antes.',
      onCapture: 'Toda fraqueza desprotegida cobra seu tributo.',
      onCheck: 'Xeque! Sua fortaleza tem uma brecha.',
      onGoodUserMove: 'Astuto. Você fechou a diagonal antes da tempestade.',
      onVictory: 'A vitória sorri a quem une virtù e prevenção.',
      onDefeat: 'Excelente leitura estratégica. Você dominou o terreno antes do combate.',
    },
  },
  {
    id: 'bot_stark_1650',
    name: 'Tony Stark',
    titleBadge: '1650 Elo • Tático Mark',
    elo: 1650,
    avatarCode: '🦾',
    styleSummary: 'Aberturas agressivas, colunas abertas e cálculo tático veloz.',
    maxDepth: 3,
    timeBudgetMs: 320,
    noiseCp: 16,
    blunderChance: 0.015,
    quotes: {
      greeting: 'Protocolo de Xadrez Mark XIII online. Vamos testar sua precisão tática!',
      onCapture: 'Alvo neutralizado com eficiência limpa.',
      onCheck: 'Xeque! Meus sensores indicam turbulência no seu roque.',
      onGoodUserMove: 'Ok, admito: esse lance foi nível engenharia de ponta.',
      onVictory: 'Diagnóstico concluído: revise o lance crítico no Game Review e instale o upgrade!',
      onDefeat: 'Impressionante! Vou precisar atualizar meu motor para a próxima.',
    },
  },
  {
    id: 'bot_senku_1900',
    name: 'Senku Ishigami',
    titleBadge: '1900 Elo • Científico',
    elo: 1900,
    avatarCode: '🧪',
    styleSummary: 'dez bilhões por cento lógico: livro de aberturas amplo e zero esperança subjetiva.',
    maxDepth: 4,
    timeBudgetMs: 420,
    noiseCp: 6,
    blunderChance: 0,
    quotes: {
      greeting: 'Xadrez não tem mágica: são 10 bilhões por cento geometria, tempo e cálculo exato!',
      onCapture: 'Equação simplificada: vantagem material convertida.',
      onCheck: 'Xeque! Cada casa de fuga foi calculada.',
      onGoodUserMove: 'Heh, nada mal! Essa variante é matematicamente sólida.',
      onVictory: 'A ciência do cálculo venceu. Analise a árvore de variantes!',
      onDefeat: 'Dez bilhões por cento brilhante! Você enxergou mais fundo na árvore.',
    },
  },
  {
    id: 'bot_tesla_2150',
    name: 'Nikola Tesla',
    titleBadge: '2150 Elo • Mestre',
    elo: 2150,
    avatarCode: '⚡',
    styleSummary: 'Domínio harmônico do par de bispos, sacrifícios posicionais e finais cirúrgicos.',
    maxDepth: 4,
    timeBudgetMs: 650,
    noiseCp: 0,
    blunderChance: 0,
    quotes: {
      greeting: 'Visualize o tabuleiro inteiro em sua mente antes de tocar na peça.',
      onCapture: 'As linhas de força convergiram exatamente nesta casa.',
      onCheck: 'Xeque em ressonância direta!',
      onGoodUserMove: 'Magnífica harmonia entre suas peças.',
      onVictory: 'Estude a coordenação das torres e bispos no final.',
      onDefeat: 'Extraordinário! Sua visão espacial conduziu uma partida digna de mestre.',
    },
  },
  {
    id: 'bot_apice_2400',
    name: 'Grande Mestre FORJA',
    titleBadge: '2400 Elo • Ápice',
    elo: 2400,
    avatarCode: '👑',
    styleSummary: 'Força máxima offline: Livro ECO profundo + Busca PeSTO + Quiescence sem concessões.',
    maxDepth: 5,
    timeBudgetMs: 950,
    noiseCp: 0,
    blunderChance: 0,
    quotes: {
      greeting: 'Bem-vindo à Mesa Suprema. Cada tempo e cada peão contam.',
      onCapture: 'Conversão concreta de vantagem.',
      onCheck: 'Xeque.',
      onGoodUserMove: 'Lance de altíssima precisão.',
      onVictory: 'Partida instrutiva. Use a Revisão Completa para lapidar cada imprecisão.',
      onDefeat: 'Honra ao mérito: você superou o motor no nível máximo do FORJA!',
    },
  },
];

// ============================================================================
// TABELAS PESTO TAPERED EVALUATION (RONALD FRIEDERICH) — MEIO-JOGO & FINAL
// Orientadas da perspectiva das Brancas: indice 0 = a8 ... indice 63 = h1
// ============================================================================
const MG_VALUE: Record<PieceSymbol, number> = {
  p: 82,
  n: 337,
  b: 365,
  r: 477,
  q: 1025,
  k: 20000,
};

const EG_VALUE: Record<PieceSymbol, number> = {
  p: 94,
  n: 281,
  b: 297,
  r: 512,
  q: 936,
  k: 20000,
};

const PHASE_WEIGHT: Record<PieceSymbol, number> = {
  p: 0,
  n: 1,
  b: 1,
  r: 2,
  q: 4,
  k: 0,
};

const MG_PAWN_TABLE = [
  0, 0, 0, 0, 0, 0, 0, 0,
  98, 134, 61, 95, 68, 126, 34, -11,
  -6, 7, 26, 31, 65, 56, 25, -20,
  -14, 13, 6, 21, 23, 12, 17, -23,
  -27, -2, -5, 12, 17, 6, 10, -25,
  -26, -4, -4, -10, 3, 3, 33, -12,
  -35, -1, -20, -23, -15, 24, 38, -22,
  0, 0, 0, 0, 0, 0, 0, 0,
];

const EG_PAWN_TABLE = [
  0, 0, 0, 0, 0, 0, 0, 0,
  178, 173, 158, 134, 147, 132, 165, 187,
  94, 100, 85, 67, 56, 53, 82, 84,
  32, 24, 13, 5, -2, 4, 17, 17,
  13, 9, -3, -7, -7, -8, 3, -1,
  4, 7, -6, 1, 0, -5, -1, -8,
  13, 8, 8, 10, 13, 0, 2, -7,
  0, 0, 0, 0, 0, 0, 0, 0,
];

const MG_KNIGHT_TABLE = [
  -167, -89, -34, -49, 61, -97, -15, -107,
  -73, -41, 72, 36, 23, 62, 7, -17,
  -47, 60, 37, 65, 84, 129, 73, 44,
  -9, 17, 19, 53, 37, 69, 18, 22,
  -13, 4, 16, 13, 28, 19, 21, -8,
  -23, -9, 12, 10, 19, 17, 25, -16,
  -29, -53, -12, -3, -1, 18, -14, -19,
  -105, -21, -58, -33, -17, -28, -19, -23,
];

const EG_KNIGHT_TABLE = [
  -58, -38, -13, -28, -31, -27, -63, -99,
  -25, -8, -25, -2, -9, -25, -24, -52,
  -24, -20, 10, 9, -1, -9, -19, -41,
  -17, 3, 22, 22, 22, 11, 8, -18,
  -18, -6, 16, 25, 16, 17, 4, -18,
  -23, -3, -1, 15, 10, -3, -20, -22,
  -42, -20, -10, -5, -2, -20, -23, -44,
  -29, -51, -23, -15, -22, -18, -50, -64,
];

const MG_BISHOP_TABLE = [
  -29, 4, -82, -37, -25, -42, 7, -8,
  -26, 16, -18, -13, 30, 59, 18, -47,
  -16, 37, 43, 40, 35, 50, 37, -2,
  -4, 5, 19, 50, 37, 37, 7, -2,
  -6, 13, 13, 26, 34, 12, 10, 4,
  0, 15, 15, 15, 14, 27, 18, 10,
  4, 15, 16, 0, 7, 21, 33, 1,
  -33, -3, -14, -21, -13, -12, -39, -21,
];

const EG_BISHOP_TABLE = [
  -14, -21, -11, -8, -7, -9, -17, -24,
  -8, -4, 7, -12, -3, -13, -4, -14,
  2, -8, 0, -1, -2, 6, 0, 4,
  -3, 9, 12, 9, 14, 10, 3, 2,
  -6, 3, 13, 19, 7, 10, -3, -9,
  -12, -3, 8, 10, 13, 3, -7, -15,
  -14, -18, -7, -1, 4, -9, -15, -27,
  -23, -9, -23, -5, -9, -16, -5, -17,
];

const MG_ROOK_TABLE = [
  32, 42, 32, 51, 63, 9, 31, 43,
  27, 32, 58, 62, 80, 67, 26, 44,
  -5, 19, 26, 36, 17, 45, 61, 16,
  -24, -11, 7, 26, 24, 35, -8, -20,
  -36, -26, -12, -1, 9, -7, 6, -23,
  -45, -25, -16, -17, 3, 0, -5, -33,
  -44, -16, -20, -9, -1, 11, -6, -71,
  -19, -13, 1, 17, 16, 7, -37, -26,
];

const EG_ROOK_TABLE = [
  13, 10, 18, 15, 12, 12, 8, 5,
  11, 13, 13, 11, -3, 3, 8, 3,
  7, 7, 7, 5, 4, -3, -5, -3,
  4, 3, 13, 1, 2, 1, -1, 2,
  3, 5, 8, 4, -5, -6, -8, -11,
  -4, 0, -5, -1, -7, -12, -8, -16,
  -6, -6, 0, 2, -9, -9, -11, -3,
  -9, 2, 3, -1, -5, -13, 4, -20,
];

const MG_QUEEN_TABLE = [
  -28, 0, 29, 12, 59, 44, 43, 45,
  -24, -39, -5, 1, -16, 57, 28, 54,
  -13, -17, 7, 8, 29, 56, 47, 57,
  -27, -27, -16, -16, -1, 17, -2, 1,
  -9, -26, -9, -10, -2, -4, 3, -3,
  -14, 2, -11, -2, -5, 2, 14, 5,
  -35, -8, 11, 2, 8, 15, -3, 1,
  -1, -18, -9, 10, -15, -25, -31, -50,
];

const EG_QUEEN_TABLE = [
  -9, 22, 22, 27, 27, 19, 10, 20,
  -17, 20, 32, 41, 58, 25, 30, 0,
  -20, 6, 9, 49, 47, 35, 19, 9,
  3, 22, 24, 45, 57, 40, 57, 36,
  -18, 28, 19, 47, 31, 34, 39, 23,
  -16, -27, 15, 6, 9, 17, 10, 5,
  -22, -23, -30, -16, -16, -23, -36, -32,
  -33, -28, -22, -43, -5, -32, -20, -41,
];

const MG_KING_TABLE = [
  -65, 23, 16, -15, -56, -34, 2, 13,
  29, -1, -20, -7, -8, -4, -38, -29,
  -9, 24, 2, -16, -20, 6, 22, -22,
  -17, -20, -12, -27, -30, -25, -14, -36,
  -49, -1, -27, -39, -46, -44, -33, -51,
  -14, -14, -22, -46, -44, -30, -15, -27,
  1, 7, -8, -64, -43, -16, 9, 8,
  -15, 36, 12, -54, 8, -28, 24, 14,
];

const EG_KING_TABLE = [
  -74, -35, -18, -18, -11, 15, 4, -17,
  -12, 17, 14, 17, 17, 38, 23, 11,
  10, 17, 23, 15, 20, 45, 44, 13,
  -8, 22, 24, 27, 26, 33, 26, 3,
  -18, -4, 21, 24, 27, 23, 9, -11,
  -19, -3, 11, 21, 23, 16, 7, -9,
  -27, -11, 4, 13, 14, 4, -5, -17,
  -53, -34, -21, -11, -28, -14, -24, -43,
];

const MG_PST: Record<PieceSymbol, number[]> = {
  p: MG_PAWN_TABLE,
  n: MG_KNIGHT_TABLE,
  b: MG_BISHOP_TABLE,
  r: MG_ROOK_TABLE,
  q: MG_QUEEN_TABLE,
  k: MG_KING_TABLE,
};

const EG_PST: Record<PieceSymbol, number[]> = {
  p: EG_PAWN_TABLE,
  n: EG_KNIGHT_TABLE,
  b: EG_BISHOP_TABLE,
  r: EG_ROOK_TABLE,
  q: EG_QUEEN_TABLE,
  k: EG_KING_TABLE,
};

const MATE_SCORE = 29000;
const MATE_THRESHOLD = 28800;

function toTtScore(score: number, ply: number): number {
  if (score > MATE_THRESHOLD) return score + ply;
  if (score < -MATE_THRESHOLD) return score - ply;
  return score;
}

function fromTtScore(score: number, ply: number): number {
  if (score > MATE_THRESHOLD) return score - ply;
  if (score < -MATE_THRESHOLD) return score + ply;
  return score;
}

interface InternalMove0x88 {
  color: Color;
  from: number;
  to: number;
  piece: PieceSymbol;
  captured?: PieceSymbol;
  promotion?: PieceSymbol;
  flags: number;
}

interface ChessInternal0x88 {
  _board: ({ type: PieceSymbol; color: Color } | undefined)[];
  _turn: Color;
  _halfMoves: number;
  _hash: bigint;
  _moves: (opts?: { legal?: boolean }) => InternalMove0x88[];
  _makeMove: (m: InternalMove0x88) => void;
  _undoMove: () => InternalMove0x88 | null;
  _isKingAttacked: (color: Color) => boolean;
  _incPositionCount: (hash: bigint) => void;
  _decPositionCount: (hash: bigint) => void;
  _getPositionCount: (hash: bigint) => number;
}

const FILES_STR = 'abcdefgh';
function ox88ToLan(m: InternalMove0x88): string {
  const f1 = FILES_STR[m.from & 7];
  const r1 = 8 - (m.from >> 4);
  const f2 = FILES_STR[m.to & 7];
  const r2 = 8 - (m.to >> 4);
  return `${f1}${r1}${f2}${r2}${m.promotion ?? ''}`;
}

function fastPush(raw: ChessInternal0x88, m: InternalMove0x88): void {
  raw._makeMove(m);
  raw._incPositionCount(raw._hash);
}

function fastPop(raw: ChessInternal0x88): void {
  const h = raw._hash;
  raw._undoMove();
  raw._decPositionCount(h);
}

/**
 * Avaliacao puramente material + posicional PeSTO direto sobre o tabuleiro 0x88 (zero alocacoes!).
 */
function evaluateStaticBoardWhiteCp(chess: Chess): number {
  const raw = chess as unknown as ChessInternal0x88;
  const board0x88 = raw._board;
  let mgWhite = 0;
  let egWhite = 0;
  let mgBlack = 0;
  let egBlack = 0;
  let phase = 0;

  let whiteBishops = 0;
  let blackBishops = 0;
  const whitePawnFiles = [0, 0, 0, 0, 0, 0, 0, 0];
  const blackPawnFiles = [0, 0, 0, 0, 0, 0, 0, 0];
  let wKingRow = 7;
  let wKingCol = 4;
  let bKingRow = 0;
  let bKingCol = 4;

  for (let i = 0; i <= 119; i++) {
    if (i & 0x88) {
      i += 7;
      continue;
    }
    const cell = board0x88[i];
    if (!cell) continue;
    const r = i >> 4;
    const c = i & 7;
    const p = cell.type;
    phase += PHASE_WEIGHT[p];

    if (cell.color === 'w') {
      const sqIdx = (r << 3) | c;
      mgWhite += MG_VALUE[p] + MG_PST[p][sqIdx];
      egWhite += EG_VALUE[p] + EG_PST[p][sqIdx];
      if (p === 'b') whiteBishops++;
      else if (p === 'p') whitePawnFiles[c]++;
      else if (p === 'k') {
        wKingRow = r;
        wKingCol = c;
      }
    } else {
      const mirroredIdx = ((7 - r) << 3) | c;
      mgBlack += MG_VALUE[p] + MG_PST[p][mirroredIdx];
      egBlack += EG_VALUE[p] + EG_PST[p][mirroredIdx];
      if (p === 'b') blackBishops++;
      else if (p === 'p') blackPawnFiles[c]++;
      else if (p === 'k') {
        bKingRow = r;
        bKingCol = c;
      }
    }
  }

  // Par de Bispos
  if (whiteBishops >= 2) {
    mgWhite += 30;
    egWhite += 45;
  }
  if (blackBishops >= 2) {
    mgBlack += 30;
    egBlack += 45;
  }

  // Penalidade de peoes dobrados
  for (let f = 0; f < 8; f++) {
    if (whitePawnFiles[f] > 1) {
      mgWhite -= (whitePawnFiles[f] - 1) * 14;
      egWhite -= (whitePawnFiles[f] - 1) * 18;
    }
    if (blackPawnFiles[f] > 1) {
      mgBlack -= (blackPawnFiles[f] - 1) * 14;
      egBlack -= (blackPawnFiles[f] - 1) * 18;
    }
  }

  const clampedPhase = Math.min(24, phase);
  const mgScore = mgWhite - mgBlack;
  const egScore = egWhite - egBlack;
  let score = Math.round((mgScore * clampedPhase + egScore * (24 - clampedPhase)) / 24);

  // Heuristica Mop-Up de Final: empurra o Rei solitario para a borda e aproxima o Rei vencedor
  if (clampedPhase <= 6 && Math.abs(score) >= 330) {
    const centerDist = (r: number, c: number) =>
      Math.max(Math.abs(3.5 - r), Math.abs(3.5 - c));
    const kingsManhattan = Math.abs(wKingRow - bKingRow) + Math.abs(wKingCol - bKingCol);
    if (score > 0) {
      const mopUp = Math.round(centerDist(bKingRow, bKingCol) * 16 + (14 - kingsManhattan) * 5);
      score += mopUp;
    } else {
      const mopUp = Math.round(centerDist(wKingRow, wKingCol) * 16 + (14 - kingsManhattan) * 5);
      score -= mopUp;
    }
  }

  return score;
}

export function evaluatePositionWhiteCp(chess: Chess): number {
  if (chess.isCheckmate()) {
    return chess.turn() === 'w' ? -MATE_SCORE : MATE_SCORE;
  }
  if (chess.isDraw()) {
    return 0;
  }
  return evaluateStaticBoardWhiteCp(chess);
}

function evaluateSideToMove(chess: Chess): number {
  const whiteCp = evaluateStaticBoardWhiteCp(chess);
  return chess.turn() === 'w' ? whiteCp : -whiteCp;
}

const MVV_WEIGHT: Record<PieceSymbol, number> = {
  p: 100,
  n: 320,
  b: 330,
  r: 500,
  q: 950,
  k: 10000,
};

function scoreMoveOrdering0x88(
  m: InternalMove0x88,
  lan: string,
  ttBestLan?: string,
  killerLan?: string,
): number {
  if (ttBestLan && lan === ttBestLan) return 100_000;
  let s = 0;
  if (m.captured) {
    s += 10_000 + MVV_WEIGHT[m.captured] * 10 - MVV_WEIGHT[m.piece];
  }
  if (m.promotion) {
    s += 8_000 + MVV_WEIGHT[m.promotion];
  }
  if (killerLan && lan === killerLan) {
    s += 4_500;
  }
  // BITS.KSIDE_CASTLE = 32, BITS.QSIDE_CASTLE = 64
  if (m.flags & 96) {
    s += 500;
  }
  return s;
}

interface TTEntry {
  depth: number;
  score: number;
  flag: 'EXACT' | 'LOWER' | 'UPPER';
  bestLan: string;
}

export interface EngineSearchLine {
  moveSan: string;
  moveLan: string;
  from: Square;
  to: Square;
  promotion?: PieceSymbol;
  evalWhiteCp: number;
  mateInMoves: number | null; // Positivo = Brancas dao mate em N; Negativo = Pretas dao mate em N
  pvSan: string[];
}

class SearchContext {
  tt = new Map<bigint, TTEntry>();
  killers: string[] = [];
  nodes = 0;
  deadlineMs = 0;
  aborted = false;
}

function quiescence(
  chess: Chess,
  alpha: number,
  beta: number,
  ply: number,
  ctx: SearchContext,
  qDepth: number,
): number {
  ctx.nodes++;
  if ((ctx.nodes & 511) === 0 && performance.now() >= ctx.deadlineMs) {
    ctx.aborted = true;
    return 0;
  }

  const raw = chess as unknown as ChessInternal0x88;
  const inCheck = raw._isKingAttacked(raw._turn);

  if (!inCheck) {
    const standPat = evaluateSideToMove(chess);
    if (standPat >= beta) return standPat;
    let best = standPat;
    if (standPat > alpha) alpha = standPat;
    if (qDepth >= 5) return best;

    const captures = raw
      ._moves()
      .filter((m) => Boolean(m.captured || m.promotion));
    if (captures.length === 0) return best;

    captures.sort(
      (a, b) =>
        scoreMoveOrdering0x88(b, '') - scoreMoveOrdering0x88(a, ''),
    );
    for (const m of captures) {
      const gain =
        (m.captured ? MVV_WEIGHT[m.captured] : 0) +
        (m.promotion ? MVV_WEIGHT[m.promotion] : 0) +
        200;
      if (standPat + gain < alpha) continue;

      fastPush(raw, m);
      const score = -quiescence(chess, -beta, -alpha, ply + 1, ctx, qDepth + 1);
      fastPop(raw);
      if (ctx.aborted) return 0;

      if (score > best) best = score;
      if (score >= beta) return best;
      if (score > alpha) alpha = score;
    }
    return best;
  }

  // Em xeque: obrigado a testar todas as evasoes legais (detecta xeque-mate na folha!)
  const evasions = raw._moves();
  if (evasions.length === 0) {
    return -(MATE_SCORE - ply);
  }
  if (qDepth >= 5) {
    return evaluateSideToMove(chess);
  }

  evasions.sort(
    (a, b) => scoreMoveOrdering0x88(b, '') - scoreMoveOrdering0x88(a, ''),
  );
  let best = -Infinity;
  for (const m of evasions) {
    fastPush(raw, m);
    const score = -quiescence(chess, -beta, -alpha, ply + 1, ctx, qDepth + 1);
    fastPop(raw);
    if (ctx.aborted) return 0;

    if (score > best) best = score;
    if (score >= beta) return best;
    if (score > alpha) alpha = score;
  }

  return best;
}

function negamax(
  chess: Chess,
  depth: number,
  ply: number,
  alpha: number,
  beta: number,
  ctx: SearchContext,
): number {
  ctx.nodes++;
  if ((ctx.nodes & 511) === 0 && performance.now() >= ctx.deadlineMs) {
    ctx.aborted = true;
    return 0;
  }

  const raw = chess as unknown as ChessInternal0x88;

  if (
    ply > 0 &&
    (raw._halfMoves >= 100 || raw._getPositionCount(raw._hash) >= 3)
  ) {
    return 0;
  }

  const inCheck = raw._isKingAttacked(raw._turn);
  const effDepth = inCheck && ply < 6 ? depth + 1 : depth;

  if (effDepth <= 0) {
    return quiescence(chess, alpha, beta, ply, ctx, 0);
  }

  const key = raw._hash;
  const ttHit = ctx.tt.get(key);
  const origAlpha = alpha;

  if (ttHit && ttHit.depth >= effDepth && ply > 0) {
    const ttScore = fromTtScore(ttHit.score, ply);
    if (ttHit.flag === 'EXACT') return ttScore;
    if (ttHit.flag === 'LOWER' && ttScore > alpha) alpha = ttScore;
    else if (ttHit.flag === 'UPPER' && ttScore < beta) beta = ttScore;
    if (alpha >= beta) return ttScore;
  }

  const moves = raw._moves();
  if (moves.length === 0) {
    return inCheck ? -(MATE_SCORE - ply) : 0;
  }

  const killer = ctx.killers[ply];
  const decorated = moves.map((m) => {
    const lan = ox88ToLan(m);
    return {
      m,
      lan,
      ord: scoreMoveOrdering0x88(m, lan, ttHit?.bestLan, killer),
    };
  });
  decorated.sort((a, b) => b.ord - a.ord);

  let bestScore = -Infinity;
  let bestLan = decorated[0].lan;

  for (const item of decorated) {
    fastPush(raw, item.m);
    const score = -negamax(chess, effDepth - 1, ply + 1, -beta, -alpha, ctx);
    fastPop(raw);
    if (ctx.aborted) return 0;

    if (score > bestScore) {
      bestScore = score;
      bestLan = item.lan;
    }
    if (score > alpha) {
      alpha = score;
    }
    if (alpha >= beta) {
      if (!item.m.captured) {
        ctx.killers[ply] = item.lan;
      }
      break;
    }
  }

  if (ctx.tt.size > 60_000) {
    ctx.tt.clear();
  }
  const flag: TTEntry['flag'] =
    bestScore <= origAlpha ? 'UPPER' : bestScore >= beta ? 'LOWER' : 'EXACT';
  ctx.tt.set(key, {
    depth: effDepth,
    score: toTtScore(bestScore, ply),
    flag,
    bestLan,
  });

  return bestScore;
}

function extractPvSan(
  fen: string,
  firstMove: Move,
  tt: Map<bigint, TTEntry>,
  maxLen = 5,
): string[] {
  const sim = new Chess(fen);
  const pv: string[] = [];
  const first = sim.move({
    from: firstMove.from,
    to: firstMove.to,
    promotion: firstMove.promotion,
  });
  if (!first) return [];
  pv.push(first.san);

  for (let i = 1; i < maxLen; i++) {
    if (sim.isGameOver()) break;
    const rawSim = sim as unknown as ChessInternal0x88;
    const hit = tt.get(rawSim._hash);
    if (!hit) break;
    const legal = sim.moves({ verbose: true }).find((m) => m.lan === hit.bestLan);
    if (!legal) break;
    sim.move(legal);
    pv.push(legal.san);
  }
  return pv;
}

function scoreToMateMoves(scoreWhiteCp: number): number | null {
  const abs = Math.abs(scoreWhiteCp);
  if (abs < MATE_SCORE - 100) return null;
  const plies = Math.max(1, MATE_SCORE - abs);
  const fullMoves = Math.ceil(plies / 2);
  return scoreWhiteCp > 0 ? fullMoves : -fullMoves;
}

/**
 * Analisa as melhores linhas (Multi-PV) de qualquer posicao FEN dentro de um orcamento estrito de tempo.
 */
export function analyzePositionMultiPv(
  fen: string,
  options: { maxDepth?: number; timeBudgetMs?: number; multiPv?: number } = {},
): EngineSearchLine[] {
  const maxDepth = options.maxDepth ?? 3;
  const timeBudgetMs = options.timeBudgetMs ?? 300;
  const multiPv = options.multiPv ?? 3;

  const root = new Chess(fen);
  const legalMoves = root.moves({ verbose: true });
  if (legalMoves.length === 0) return [];

  const turnSign = root.turn() === 'w' ? 1 : -1;
  const ctx = new SearchContext();
  ctx.deadlineMs = performance.now() + timeBudgetMs;

  let scoredMoves: { move: Move; sideScore: number }[] = legalMoves.map((m) => ({
    move: m,
    sideScore: 0,
  }));

  const rawRoot = root as unknown as ChessInternal0x88;
  const rawRootMoves = rawRoot._moves();
  const rootMap = new Map(rawRootMoves.map((rm) => [ox88ToLan(rm), rm]));

  for (let d = 1; d <= maxDepth; d++) {
    const iterScores: { move: Move; sideScore: number }[] = [];
    // Ordena pela iteracao anterior para acelerar cortes alpha-beta
    const ordered = [...scoredMoves].sort((a, b) => b.sideScore - a.sideScore);

    for (const item of ordered) {
      let alphaFloor = -MATE_SCORE - 50;
      if (iterScores.length >= multiPv) {
        iterScores.sort((a, b) => b.sideScore - a.sideScore);
        alphaFloor = iterScores[multiPv - 1].sideScore - 1;
      }
      const rm = rootMap.get(item.move.lan)!;
      fastPush(rawRoot, rm);
      const s = -negamax(root, d - 1, 1, -MATE_SCORE - 50, -alphaFloor, ctx);
      fastPop(rawRoot);
      if (ctx.aborted && d > 1) break;
      iterScores.push({ move: item.move, sideScore: s });
    }

    if (!ctx.aborted || d === 1) {
      scoredMoves = iterScores;
      scoredMoves.sort((a, b) => b.sideScore - a.sideScore);
      if (
        scoredMoves.length >= multiPv &&
        scoredMoves[multiPv - 1].sideScore > MATE_THRESHOLD
      ) {
        break;
      }
    }
    if (ctx.aborted || performance.now() >= ctx.deadlineMs) break;
  }

  scoredMoves.sort((a, b) => b.sideScore - a.sideScore);

  return scoredMoves.slice(0, multiPv).map(({ move, sideScore }) => {
    const evalWhiteCp = sideScore * turnSign;
    return {
      moveSan: move.san,
      moveLan: move.lan,
      from: move.from,
      to: move.to,
      promotion: move.promotion,
      evalWhiteCp,
      mateInMoves: scoreToMateMoves(evalWhiteCp),
      pvSan: extractPvSan(fen, move, ctx.tt, 5),
    };
  });
}

/**
 * Escolhe o lance de um Bot calibrado pelo Elo, Livro de Aberturas ECO e personalidade.
 */
export function chooseBotMove(
  fen: string,
  bot: ChessBotProfile,
  moveHistorySan: string[] = [],
  seed = Date.now(),
): { moveSan: string; from: Square; to: Square; promotion?: PieceSymbol; isBook: boolean } | null {
  const chess = new Chess(fen);
  const legal = chess.moves({ verbose: true });
  if (legal.length === 0) return null;
  if (legal.length === 1) {
    return {
      moveSan: legal[0].san,
      from: legal[0].from,
      to: legal[0].to,
      promotion: legal[0].promotion,
      isBook: false,
    };
  }

  // Reconstrói historico se disponivel para checar Livro de Aberturas ECO
  if (moveHistorySan.length >= 0 && moveHistorySan.length <= 12) {
    const replay = new Chess();
    let ok = true;
    for (const san of moveHistorySan) {
      try {
        replay.move(san);
      } catch {
        ok = false;
        break;
      }
    }
    if (ok && replay.fen().split(' ')[0] === fen.split(' ')[0]) {
      const bookSan = pickBookMoveForBot(replay, bot.elo, seed);
      if (bookSan) {
        const hit = legal.find((m) => m.san === bookSan);
        if (hit) {
          return {
            moveSan: hit.san,
            from: hit.from,
            to: hit.to,
            promotion: hit.promotion,
            isBook: true,
          };
        }
      }
    }
  }

  const lines = analyzePositionMultiPv(fen, {
    maxDepth: bot.maxDepth,
    timeBudgetMs: bot.timeBudgetMs,
    multiPv: Math.min(6, legal.length),
  });

  if (lines.length === 0) {
    const fallback = legal[0];
    return {
      moveSan: fallback.san,
      from: fallback.from,
      to: fallback.to,
      promotion: fallback.promotion,
      isBook: false,
    };
  }

  // RNG deterministico leve para ruido de Elo baixo/medio
  let rng = (seed ^ 0x9e3779b9) >>> 0;
  const rand01 = () => {
    rng = (Math.imul(rng, 1664525) + 1013904223) >>> 0;
    return rng / 4294967296;
  };

  if (bot.blunderChance > 0 && rand01() < bot.blunderChance && lines.length >= 2) {
    const pickIdx = Math.min(lines.length - 1, 1 + Math.floor(rand01() * (lines.length - 1)));
    const chosen = lines[pickIdx];
    return {
      moveSan: chosen.moveSan,
      from: chosen.from,
      to: chosen.to,
      promotion: chosen.promotion,
      isBook: false,
    };
  }

  if (bot.noiseCp > 0 && lines.length >= 2) {
    const turnSign = chess.turn() === 'w' ? 1 : -1;
    let bestNoisy = lines[0];
    let bestNoisyVal = -Infinity;
    for (const l of lines) {
      const ownCp = l.evalWhiteCp * turnSign;
      const jitter = (rand01() - 0.5) * 2 * bot.noiseCp;
      if (ownCp + jitter > bestNoisyVal) {
        bestNoisyVal = ownCp + jitter;
        bestNoisy = l;
      }
    }
    return {
      moveSan: bestNoisy.moveSan,
      from: bestNoisy.from,
      to: bestNoisy.to,
      promotion: bestNoisy.promotion,
      isBook: false,
    };
  }

  const top = lines[0];
  return {
    moveSan: top.moveSan,
    from: top.from,
    to: top.to,
    promotion: top.promotion,
    isBook: false,
  };
}

// ============================================================================
// REGRAS OFICIAIS FIDE DE MATERIAL DE MATE NO TEMPO & SALDO DE CAPTURAS
// ============================================================================
export function sideHasMatingMaterial(chess: Chess, side: Color): boolean {
  const board = chess.board();
  let pawns = 0;
  let rooksOrQueens = 0;
  let knights = 0;
  let lightBishops = 0;
  let darkBishops = 0;

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const cell = board[r][c];
      if (!cell || cell.color !== side) continue;
      if (cell.type === 'p') pawns++;
      else if (cell.type === 'q' || cell.type === 'r') rooksOrQueens++;
      else if (cell.type === 'n') knights++;
      else if (cell.type === 'b') {
        if ((r + c) % 2 === 0) lightBishops++;
        else darkBishops++;
      }
    }
  }

  if (pawns > 0 || rooksOrQueens > 0) return true;
  if (lightBishops > 0 && darkBishops > 0) return true;
  if ((lightBishops + darkBishops >= 1) && knights >= 1) return true;
  if (knights >= 2) return true; // FIDE permite mate ajudado com 2 cavalos se adversario tiver material
  return false;
}

export interface MaterialBalanceSummary {
  capturedByWhite: PieceSymbol[]; // Pecas pretas capturadas pelas Brancas
  capturedByBlack: PieceSymbol[]; // Pecas brancas capturadas pelas Pretas
  whiteAdvantagePts: number;      // Ex.: +3 se Brancas tem 1 Cavalo a mais, -5 se Pretas tem 1 Torre a mais
}

const STANDARD_COUNTS: Record<Exclude<PieceSymbol, 'k'>, number> = {
  q: 1,
  r: 2,
  b: 2,
  n: 2,
  p: 8,
};

const DISPLAY_PTS: Record<PieceSymbol, number> = {
  q: 9,
  r: 5,
  b: 3,
  n: 3,
  p: 1,
  k: 0,
};

export function computeMaterialSummary(
  chess: Chess,
  initialFen?: string,
): MaterialBalanceSummary {
  const board = chess.board();
  const wAlive: Record<PieceSymbol, number> = { q: 0, r: 0, b: 0, n: 0, p: 0, k: 0 };
  const bAlive: Record<PieceSymbol, number> = { q: 0, r: 0, b: 0, n: 0, p: 0, k: 0 };

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const cell = board[r][c];
      if (!cell) continue;
      if (cell.color === 'w') wAlive[cell.type]++;
      else bAlive[cell.type]++;
    }
  }

  let wBase: Record<Exclude<PieceSymbol, 'k'>, number> = STANDARD_COUNTS;
  let bBase: Record<Exclude<PieceSymbol, 'k'>, number> = STANDARD_COUNTS;

  if (initialFen && !initialFen.startsWith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')) {
    try {
      const startBoard = new Chess(initialFen).board();
      wBase = { q: 0, r: 0, b: 0, n: 0, p: 0 };
      bBase = { q: 0, r: 0, b: 0, n: 0, p: 0 };
      for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
          const cell = startBoard[r][c];
          if (!cell || cell.type === 'k') continue;
          if (cell.color === 'w') wBase[cell.type]++;
          else bBase[cell.type]++;
        }
      }
    } catch {
      wBase = STANDARD_COUNTS;
      bBase = STANDARD_COUNTS;
    }
  }

  const capturedByWhite: PieceSymbol[] = [];
  const capturedByBlack: PieceSymbol[] = [];
  const order: Exclude<PieceSymbol, 'k'>[] = ['q', 'r', 'b', 'n', 'p'];

  for (const p of order) {
    const missingBlack = Math.max(0, bBase[p] - bAlive[p]);
    for (let i = 0; i < missingBlack; i++) capturedByWhite.push(p);

    const missingWhite = Math.max(0, wBase[p] - wAlive[p]);
    for (let i = 0; i < missingWhite; i++) capturedByBlack.push(p);
  }

  const wPoints = order.reduce((s, p) => s + wAlive[p] * DISPLAY_PTS[p], 0);
  const bPoints = order.reduce((s, p) => s + bAlive[p] * DISPLAY_PTS[p], 0);

  return {
    capturedByWhite,
    capturedByBlack,
    whiteAdvantagePts: wPoints - bPoints,
  };
}

export function computeEloDelta(
  playerRating: number,
  opponentRating: number,
  resultScore: 1 | 0.5 | 0,
  kFactor = 32,
): number {
  const expected = 1 / (1 + Math.pow(10, (opponentRating - playerRating) / 400));
  return Math.round(kFactor * (resultScore - expected));
}

/**
 * Categoria de ELO estilo Chess.com.
 * Limites alinhados com distribuições reais de FIDE/Chess.com para ajuste offline.
 */
export function computeEloCategory(rating: number): ChessVaultData['playEloCategory'] {
  if (rating < 800) return 'INICIANTE';
  if (rating < 1200) return 'CLUBE';
  if (rating < 1600) return 'INTERMEDIARIO';
  if (rating < 2000) return 'AVANCADO';
  if (rating < 2300) return 'ESPECIALISTA';
  if (rating < 2500) return 'MESTRE';
  return 'GRAO_MESTRE';
}

export interface ChessAchievementSpec {
  id: string;
  title: string;
  descriptionPt: string;
  icon: string;
  conditionPt: string;
  // Avalia se o jogador desbloqueou a conquista dado o estado atual do vault
  unlocked: (vault: ChessVaultData) => boolean;
}

export const CHESS_ACHIEVEMENTS: ChessAchievementSpec[] = [
  {
    id: 'ach_first_win',
    title: 'Primeira Vitória',
    descriptionPt: 'Venceu sua primeira partida no FORJA Xadrez.',
    icon: '🏆',
    conditionPt: 'Vença qualquer partida (contra bot ou jogador local).',
    unlocked: (v) => v.wins >= 1,
  },
  {
    id: 'ach_hat_trick',
    title: 'Triplete',
    descriptionPt: 'Venceu 3 partidas seguidas.',
    icon: '🔥',
    conditionPt: 'Sequência atual de vitórias >= 3.',
    unlocked: (v) => (v.currentWinStreak ?? 0) >= 3,
  },
  {
    id: 'ach_club_player',
    title: 'Jogador de Clube',
    descriptionPt: 'Alcançou ELO 1200.',
    icon: '🎯',
    conditionPt: 'playRating >= 1200.',
    unlocked: (v) => v.playRating >= 1200,
  },
  {
    id: 'ach_expert',
    title: 'Especialista',
    descriptionPt: 'Alcançou ELO 2000.',
    icon: '🎖️',
    conditionPt: 'playRating >= 2000.',
    unlocked: (v) => v.playRating >= 2000,
  },
  {
    id: 'ach_grandmaster',
    title: 'Grão-Mestre',
    descriptionPt: 'Alcançou ELO 2500.',
    icon: '👑',
    conditionPt: 'playRating >= 2500.',
    unlocked: (v) => v.playRating >= 2500,
  },
  {
    id: 'ach_puzzle_solver',
    title: 'Resolvedor de Puzzles',
    descriptionPt: 'Resolveu 10 puzzles táticos.',
    icon: '🧩',
    conditionPt: 'solvedPuzzleIds.length >= 10.',
    unlocked: (v) => (v.solvedPuzzleIds ?? []).length >= 10,
  },
  {
    id: 'ach_brilliant',
    title: 'Lance Brilhante',
    descriptionPt: 'Fez um lance classificado como Brilhante (!!).',
    icon: '✨',
    conditionPt: 'totalBrilliants >= 1.',
    unlocked: (v) => (v.totalBrilliants ?? 0) >= 1,
  },
  {
    id: 'ach_goggins',
    title: 'Mentalidade Goggins',
    descriptionPt: 'Venceu uma partida contra o bot David Goggins (1150 ELO).',
    icon: '🔥',
    conditionPt: 'savedGames tem vitória contra bot_sofia_800 ou bot_goggins_1150.',
    unlocked: (v) =>
      (v.savedGames ?? []).some(
        (g) => g.result === 'VITORIA' && (g.opponentName.includes('Goggins') || g.opponentName.includes('Sofia')),
      ),
  },
  {
    id: 'ach_blitz_king',
    title: 'Rei do Blitz',
    descriptionPt: 'Venceu 5 partidas de blitz (3|0 ou 5|0).',
    icon: '⚡',
    conditionPt: 'savedGames com resultado VITORIA e timeControlLabel blitz >= 5.',
    unlocked: (v) =>
      (v.savedGames ?? []).filter(
        (g) =>
          g.result === 'VITORIA' &&
          (g.timeControlLabel === '3 | 0' || g.timeControlLabel === '5 | 0'),
      ).length >= 5,
  },
  {
    id: 'ach_undefeated',
    title: 'Invicto',
    descriptionPt: 'Jogou 10 partidas sem nenhuma derrota.',
    icon: '🛡️',
    conditionPt: 'gamesPlayed >= 10 e losses === 0.',
    unlocked: (v) => v.gamesPlayed >= 10 && v.losses === 0,
  },
  {
    id: 'ach_comeback',
    title: 'Virada Épica',
    descriptionPt: 'Venceu estando em desvantagem material.',
    icon: '📈',
    conditionPt: 'savedGames com VITORIA onde material estava negativo em algum ponto.',
    unlocked: (v) =>
      (v.savedGames ?? []).some((g) => g.result === 'VITORIA' && (g.brilliantCount ?? 0) >= 1),
  },
];

/**
 * Retorna as conquistas desbloqueadas com base no estado atual do vault.
 */
export function getUnlockedAchievements(vault: ChessVaultData): string[] {
  return CHESS_ACHIEVEMENTS.filter((a) => a.unlocked(vault)).map((a) => a.id);
}

/**
 * Retorna as conquistas disponíveis (não desbloqueadas) com seus specs.
 */
export function getAvailableAchievements(vault: ChessVaultData): ChessAchievementSpec[] {
  const unlockedIds = new Set(getUnlockedAchievements(vault));
  return CHESS_ACHIEVEMENTS.filter((a) => !unlockedIds.has(a.id));
}

/**
 * Calcula estatísticas agregadas do jogador de xadrez.
 */
export interface ChessPlayerStats {
  gamesPlayed: number;
  wins: number;
  losses: number;
  draws: number;
  winRatePct: number;
  drawRatePct: number;
  lossRatePct: number;
  currentRating: number;
  bestRating: number;
  category: ChessVaultData['playEloCategory'];
  totalBrilliants: number;
  totalBlunders: number;
  longestWinStreak: number;
  currentWinStreak: number;
  puzzleRating: number;
  achievementsCount: number;
  favoriteOpening?: { eco: string; name: string; played: number; winRatePct: number };
}

export function computeChessPlayerStats(vault: ChessVaultData): ChessPlayerStats {
  const games = vault.gamesPlayed;
  const wins = vault.wins;
  const losses = vault.losses;
  const draws = vault.draws;
  const winRate = games > 0 ? Math.round((wins / games) * 100) : 0;
  const drawRate = games > 0 ? Math.round((draws / games) * 100) : 0;
  const lossRate = games > 0 ? Math.round((losses / games) * 100) : 0;

  // Melhor ELO alcançado (a partir do histórico de jogos salvos)
  let bestRating = vault.playRating;
  for (const g of (vault.savedGames ?? []) as ChessSavedGame[]) {
    const after = g.ratingDelta ? vault.playRating - g.ratingDelta : vault.playRating;
    if (after > bestRating) bestRating = after;
  }

  // Abertura favorita
  let favoriteOpening: ChessPlayerStats['favoriteOpening'];
  const openings = vault.openingsPlayed ?? {};
  let bestPlayed = 0;
  for (const [eco, stats] of Object.entries(openings) as [string, { played: number; wins: number; draws: number; losses: number }][]) {
    if (stats.played > bestPlayed) {
      bestPlayed = stats.played;
      favoriteOpening = {
        eco,
        name: eco, // pode ser aprimorado com openingBook
        played: stats.played,
        winRatePct: stats.played > 0 ? Math.round((stats.wins / stats.played) * 100) : 0,
      };
    }
  }

  return {
    gamesPlayed: games,
    wins,
    losses,
    draws,
    winRatePct: winRate,
    drawRatePct: drawRate,
    lossRatePct: lossRate,
    currentRating: vault.playRating,
    bestRating,
    category: vault.playEloCategory,
    totalBrilliants: vault.totalBrilliants ?? 0,
    totalBlunders: vault.totalBlunders ?? 0,
    longestWinStreak: vault.longestWinStreak ?? 0,
    currentWinStreak: vault.currentWinStreak ?? 0,
    puzzleRating: vault.puzzleRating,
    achievementsCount: getUnlockedAchievements(vault).length,
    favoriteOpening,
  };
}

// ============================================================================
// TREINADOR DE XADREZ (COACH HINT) & GAME REVIEW COMPLETO ESTILO CHESS.COM
// ============================================================================
export type MoveClassification =
  | 'BRILHANTE'
  | 'GRANDE'
  | 'MELHOR'
  | 'EXCELENTE'
  | 'BOM'
  | 'TEORIA'
  | 'IMPRECISAO'
  | 'ERRO'
  | 'CAPIVARADA';

export interface MoveBadgeMeta {
  code: MoveClassification;
  symbol: string;
  labelPt: string;
  colorHex: string;
}

export const MOVE_BADGES: Record<MoveClassification, MoveBadgeMeta> = {
  BRILHANTE: { code: 'BRILHANTE', symbol: '!!', labelPt: 'Brilhante', colorHex: '#26c2a3' },
  GRANDE: { code: 'GRANDE', symbol: '!', labelPt: 'Grande Lance', colorHex: '#5c8bb0' },
  MELHOR: { code: 'MELHOR', symbol: '★', labelPt: 'Melhor Lance', colorHex: '#81b64c' },
  EXCELENTE: { code: 'EXCELENTE', symbol: '✓', labelPt: 'Excelente', colorHex: '#96bc4b' },
  BOM: { code: 'BOM', symbol: '👍', labelPt: 'Bom', colorHex: '#95af8a' },
  TEORIA: { code: 'TEORIA', symbol: '📖', labelPt: 'Teoria (Livro)', colorHex: '#d5a47d' },
  IMPRECISAO: { code: 'IMPRECISAO', symbol: '?!', labelPt: 'Imprecisão', colorHex: '#f7c631' },
  ERRO: { code: 'ERRO', symbol: '?', labelPt: 'Erro', colorHex: '#ffa459' },
  CAPIVARADA: { code: 'CAPIVARADA', symbol: '??', labelPt: 'Capivarada', colorHex: '#fa412d' },
};

export function explainMoveCoachPt(fenBefore: string, bestLine: EngineSearchLine): string {
  const sim = new Chess(fenBefore);
  const moveObj = sim
    .moves({ verbose: true })
    .find((m) => m.lan === bestLine.moveLan);

  if (!moveObj) {
    return `Melhor continuação calculada: ${bestLine.moveSan}.`;
  }

  const pieceNames: Record<PieceSymbol, string> = {
    p: 'o Peão',
    n: 'o Cavalo',
    b: 'o Bispo',
    r: 'a Torre',
    q: 'a Dama',
    k: 'o Rei',
  };

  if (bestLine.mateInMoves !== null) {
    return `Sequência forçada de xeque-mate em ${Math.abs(bestLine.mateInMoves)} lance(s) começando por ${bestLine.moveSan}!`;
  }
  if (moveObj.flags.includes('k') || moveObj.flags.includes('q')) {
    return `${bestLine.moveSan} coloca o Rei em segurança no roque e conecta as Torres!`;
  }
  if (moveObj.promotion) {
    return `${bestLine.moveSan} promove o peão passado convertendo vantagem decisiva!`;
  }
  if (moveObj.captured) {
    return `${bestLine.moveSan} captura material (${pieceNames[moveObj.captured]}) mantendo iniciativa segura (${bestLine.pvSan.slice(0, 3).join(' → ')}).`;
  }
  if (moveObj.san.includes('+')) {
    return `${bestLine.moveSan} aplica xeque direto ganhando tempo sobre o Rei adversário!`;
  }
  if (['d4', 'd5', 'e4', 'e5'].includes(moveObj.to)) {
    return `${bestLine.moveSan} luta pelo controle direto do centro com ${pieceNames[moveObj.piece]}.`;
  }
  return `${bestLine.moveSan} melhora a atividade de ${pieceNames[moveObj.piece]} preparando ${bestLine.pvSan.slice(1, 3).join(' → ') || 'pressão posicional'}.`;
}

export interface ReviewedMoveItem {
  plyIndex: number;          // 0-based
  moveNumber: number;        // 1, 1, 2, 2...
  color: Color;
  playedSan: string;
  playedFrom: Square;
  playedTo: Square;
  bestSan: string;
  bestFrom: Square;
  bestTo: Square;
  fenBefore: string;
  fenAfter: string;
  evalBeforeWhiteCp: number;
  evalAfterWhiteCp: number;
  cpLoss: number;
  classification: MoveClassification;
  coachCommentPt: string;
}

export interface FullGameReviewReport {
  moves: ReviewedMoveItem[];
  whiteAccuracyPct: number;
  blackAccuracyPct: number;
  countsWhite: Record<MoveClassification, number>;
  countsBlack: Record<MoveClassification, number>;
  openingEco: string;
  openingNamePt: string;
}

function cpToWinProbPct(cpFromMoverPerspective: number): number {
  const clamped = Math.max(-1500, Math.min(1500, cpFromMoverPerspective));
  return 100 / (1 + Math.pow(10, -clamped / 400));
}

function emptyCounts(): Record<MoveClassification, number> {
  return {
    BRILHANTE: 0,
    GRANDE: 0,
    MELHOR: 0,
    EXCELENTE: 0,
    BOM: 0,
    TEORIA: 0,
    IMPRECISAO: 0,
    ERRO: 0,
    CAPIVARADA: 0,
  };
}

/**
 * Executa a Revisao Completa da Partida estilo Chess.com (CAPS Precision + Selos de Lance).
 */
export function runFullGameReview(verboseMoves: Move[]): FullGameReviewReport {
  const sanList = verboseMoves.map((m) => m.san);
  const isStandardStart =
    !verboseMoves[0] ||
    verboseMoves[0].before.startsWith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR');
  const opening = isStandardStart
    ? detectOpeningFromMoves(sanList)
    : {
        eco: '960/FEN',
        namePt: 'Chess960 / Posição Personalizada',
        matchedPlyCount: 0,
      };

  const countsWhite = emptyCounts();
  const countsBlack = emptyCounts();
  const whiteMoveAccuracies: number[] = [];
  const blackMoveAccuracies: number[] = [];
  const reviewed: ReviewedMoveItem[] = [];

  for (let i = 0; i < verboseMoves.length; i++) {
    const m = verboseMoves[i];
    const moverSign = m.color === 'w' ? 1 : -1;
    const prefixUpToHere = sanList.slice(0, i + 1);
    const bookCheck = isStandardStart
      ? detectOpeningFromMoves(prefixUpToHere)
      : opening;
    const isBookMove =
      isStandardStart && i < 12 && bookCheck.matchedPlyCount === i + 1;

    // Melhor lance antes da jogada
    const topBefore = analyzePositionMultiPv(m.before, {
      maxDepth: 2,
      timeBudgetMs: 32,
      multiPv: 2,
    });
    const bestLine = topBefore[0];
    const secondLine = topBefore[1];

    const evalBeforeWhiteCp = bestLine
      ? bestLine.evalWhiteCp
      : evaluatePositionWhiteCp(new Chess(m.before));

    // Avaliacao apos o lance realmente jogado
    const afterChess = new Chess(m.after);
    let evalAfterWhiteCp = evaluatePositionWhiteCp(afterChess);
    if (!afterChess.isGameOver()) {
      const topAfter = analyzePositionMultiPv(m.after, {
        maxDepth: 2,
        timeBudgetMs: 26,
        multiPv: 1,
      });
      if (topAfter[0]) {
        evalAfterWhiteCp = topAfter[0].evalWhiteCp;
      }
    }

    const bestMoverCp = evalBeforeWhiteCp * moverSign;
    const playedMoverCp =
      bestLine && bestLine.moveLan === m.lan ? bestMoverCp : evalAfterWhiteCp * moverSign;

    const cpLoss = Math.max(0, Math.round(bestMoverCp - playedMoverCp));
    const winBefore = cpToWinProbPct(bestMoverCp);
    const winAfter = cpToWinProbPct(playedMoverCp);
    const winDrop = Math.max(0, winBefore - winAfter);

    // Formula exponencial estilo CAPS Chess.com por lance
    const moveAcc = Math.max(
      0,
      Math.min(100, 103.1668 * Math.exp(-0.04354 * winDrop) - 3.1669),
    );
    if (m.color === 'w') whiteMoveAccuracies.push(moveAcc);
    else blackMoveAccuracies.push(moveAcc);

    let classification: MoveClassification = 'BOM';
    if (isBookMove) {
      classification = 'TEORIA';
    } else if (bestLine && m.lan === bestLine.moveLan) {
      // Verifica se foi sacrificio tatico (entregou peca valiosa em casa atacada mantendo clara vantagem!)
      const movedVal = DISPLAY_PTS[m.piece];
      const capVal = m.captured ? DISPLAY_PTS[m.captured] : 0;
      const oppColor: Color = m.color === 'w' ? 'b' : 'w';
      const isSquareDefendedByOpp = afterChess.isAttacked(m.to, oppColor);
      const onlyMoveGap =
        secondLine ? bestMoverCp - secondLine.evalWhiteCp * moverSign : 0;

      if (movedVal >= 3 && movedVal > capVal && isSquareDefendedByOpp && playedMoverCp >= 120) {
        classification = 'BRILHANTE';
      } else if (onlyMoveGap >= 190 && playedMoverCp >= -40) {
        classification = 'GRANDE';
      } else {
        classification = 'MELHOR';
      }
    } else if (winDrop <= 2.2 || cpLoss <= 18) {
      classification = 'EXCELENTE';
    } else if (winDrop <= 5.5 || cpLoss <= 45) {
      classification = 'BOM';
    } else if (winDrop <= 11.5 || cpLoss <= 95) {
      classification = 'IMPRECISAO';
    } else if (winDrop <= 21.5 || cpLoss <= 210) {
      classification = 'ERRO';
    } else {
      classification = 'CAPIVARADA';
    }

    if (m.color === 'w') countsWhite[classification]++;
    else countsBlack[classification]++;

    let coachCommentPt = '';
    if (classification === 'TEORIA') {
      coachCommentPt = `Lance teórico de abertura (${bookCheck.namePt}).`;
    } else if (classification === 'BRILHANTE') {
      coachCommentPt = `Brilhante! Sacrifício tático calculado com precisão (${m.san})!`;
    } else if (classification === 'GRANDE') {
      coachCommentPt = `Grande achado! ${m.san} era o único lance forte na posição.`;
    } else if (classification === 'MELHOR' || classification === 'EXCELENTE') {
      coachCommentPt = bestLine
        ? explainMoveCoachPt(m.before, bestLine)
        : `Lance preciso mantendo a posição sólida.`;
    } else if (classification === 'BOM') {
      coachCommentPt = bestLine
        ? `Lance sólido; ${bestLine.moveSan} era ligeiramente mais ativo.`
        : `Bom lance prático.`;
    } else {
      coachCommentPt = bestLine
        ? `${MOVE_BADGES[classification].labelPt}: ${m.san} permitiu queda na posição. Melhor era ${bestLine.moveSan} — ${explainMoveCoachPt(m.before, bestLine)}`
        : `Queda posicional detectada neste lance.`;
    }

    reviewed.push({
      plyIndex: i,
      moveNumber: Math.floor(i / 2) + 1,
      color: m.color,
      playedSan: m.san,
      playedFrom: m.from,
      playedTo: m.to,
      bestSan: bestLine?.moveSan ?? m.san,
      bestFrom: bestLine?.from ?? m.from,
      bestTo: bestLine?.to ?? m.to,
      fenBefore: m.before,
      fenAfter: m.after,
      evalBeforeWhiteCp,
      evalAfterWhiteCp,
      cpLoss,
      classification,
      coachCommentPt,
    });
  }

  const avg = (arr: number[]) =>
    arr.length === 0
      ? 100
      : Math.round((arr.reduce((a, b) => a + b, 0) / arr.length) * 10) / 10;

  return {
    moves: reviewed,
    whiteAccuracyPct: avg(whiteMoveAccuracies),
    blackAccuracyPct: avg(blackMoveAccuracies),
    countsWhite,
    countsBlack,
    openingEco: opening.eco,
    openingNamePt: opening.namePt,
  };
}
