/**
 * Núcleo de análise de partidas — funções PURAS (sem DOM, sem worker).
 *
 * Roda no navegador e no Node (usado pelos testes em app/tests/).
 * Recebe as avaliações do motor já coletadas e devolve:
 *   - expectativa por lance (expected points) e perda
 *   - classificação de cada lance (mesma escala que os apps de xadrez usam)
 *   - precisão por lado
 *   - explicação em português, gerada a partir de fatos verificáveis
 *     (material, peças atacadas, linha principal do motor, fase do jogo)
 *
 * Nada aqui "chuta" texto genérico: cada frase é amarrada a um fato calculado.
 */

import { Chess } from 'chess.js';

const PIECE_VALUE = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 };
const PIECE_NAME_PT = {
  p: 'peão', n: 'cavalo', b: 'bispo', r: 'torre', q: 'dama', k: 'rei',
};
const PIECE_NAME_PLURAL = {
  p: 'peões', n: 'cavalos', b: 'bispos', r: 'torres', q: 'damas', k: 'reis',
};

export const CLASS_INFO = {
  brilliant: { label: 'Brilhante', short: '!!', color: '#1baca6', rank: 0 },
  great: { label: 'Ótimo', short: '!', color: '#5c8bb0', rank: 1 },
  best: { label: 'Melhor', short: '★', color: '#81b64c', rank: 2 },
  excellent: { label: 'Excelente', short: '✓', color: '#96bc4b', rank: 3 },
  good: { label: 'Bom', short: '✓', color: '#96af8b', rank: 4 },
  book: { label: 'Livro', short: '📖', color: '#a88865', rank: 5 },
  inaccuracy: { label: 'Imprecisão', short: '?!', color: '#f7c631', rank: 6 },
  mistake: { label: 'Erro', short: '?', color: '#ffa459', rank: 7 },
  miss: { label: 'Oportunidade perdida', short: '×', color: '#ff7769', rank: 8 },
  blunder: { label: 'Erro grave', short: '??', color: '#fa412d', rank: 9 },
};

// ---------------------------------------------------------------- utilidades

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

/** Converte um score UCI (perspectiva de quem joga) para a perspectiva das brancas. */
export function toWhiteScore(score, turn) {
  if (!score) return { cp: 0 };
  if (score.mate != null) return { mate: turn === 'w' ? score.mate : -score.mate };
  const cp = score.cp ?? 0;
  return { cp: turn === 'w' ? cp : -cp };
}

/**
 * Probabilidade de as brancas pontuarem (vitória = 1, empate = 0,5).
 * Modelo logístico usado por engines/plataformas para "expected points".
 */
export function expectedPointsWhite(whiteScore) {
  if (!whiteScore) return 0.5;
  if (whiteScore.mate != null) return whiteScore.mate > 0 ? 1 : 0;
  const cp = clamp(whiteScore.cp ?? 0, -1000, 1000);
  const wc = 2 / (1 + Math.exp(-0.00368208 * cp)) - 1; // -1..1
  return (1 + wc) / 2;
}

export function formatEval(whiteScore) {
  if (!whiteScore) return '0.00';
  if (whiteScore.mate != null) {
    const n = Math.abs(whiteScore.mate);
    return `${whiteScore.mate > 0 ? '+' : '-'}M${n}`;
  }
  const cp = whiteScore.cp ?? 0;
  const v = cp / 100;
  return `${v > 0 ? '+' : ''}${v.toFixed(2)}`;
}

export function formatEvalPt(whiteScore, turn = 'w') {
  if (!whiteScore) return 'equilíbrio';
  if (whiteScore.mate != null) {
    const n = Math.abs(whiteScore.mate);
    return whiteScore.mate > 0
      ? `mate em ${n} para as brancas`
      : `mate em ${n} para as pretas`;
  }
  const cp = whiteScore.cp ?? 0;
  const abs = Math.abs(cp);
  const side = cp > 0 ? 'brancas' : 'pretas';
  if (abs < 25) return 'posição equilibrada';
  if (abs < 90) return `leve vantagem das ${side}`;
  if (abs < 200) return `vantagem clara das ${side}`;
  if (abs < 450) return `vantagem decisiva das ${side}`;
  return `posição ganha para as ${side}`;
}

// ------------------------------------------------------------- material/peças

export function material(fen) {
  const board = fen.split(' ')[0];
  let white = 0, black = 0;
  for (const ch of board) {
    const lower = ch.toLowerCase();
    if (!PIECE_VALUE[lower] || lower === 'k') continue;
    if (ch === lower) black += PIECE_VALUE[lower];
    else white += PIECE_VALUE[lower];
  }
  return { white, black, diff: white - black };
}

function boardPieces(chess) {
  const out = [];
  for (const row of chess.board()) {
    for (const sq of row) if (sq) out.push(sq);
  }
  return out;
}

/**
 * Peças de `color` atacadas pelo adversário e mal defendidas.
 * Heurística: sem defensor, ou defensor mais barato que a peça atacada.
 */
export function hangingPieces(fen, color) {
  const chess = new Chess(fen);
  return hangingPiecesOn(chess, color);
}

function hangingPiecesOn(chess, color) {
  const enemy = color === 'w' ? 'b' : 'w';
  const out = [];
  for (const sq of boardPieces(chess)) {
    if (sq.color !== color || sq.type === 'k') continue;
    let attackers = [];
    let defenders = [];
    try {
      attackers = chess.attackers(sq.square, enemy);
      defenders = chess.attackers(sq.square, color);
    } catch { continue; }
    if (!attackers.length) continue;
    const value = PIECE_VALUE[sq.type];
    const cheapestAttacker = Math.min(
      ...attackers.map((a) => {
        const p = chess.get(a);
        return p ? PIECE_VALUE[p.type] : 99;
      }),
    );
    const undefended = defenders.length === 0;
    const winningCapture = cheapestAttacker < value;
    if (undefended || winningCapture) {
      out.push({
        square: sq.square,
        type: sq.type,
        name: PIECE_NAME_PT[sq.type],
        value,
        undefended,
        attackers: attackers.length,
        defenders: defenders.length,
      });
    }
  }
  return out.sort((a, b) => b.value - a.value);
}

/** Peças inimigas atacadas por uma casa (para detectar garfo). */
function attackedTargets(chess, fromSquare, color) {
  const p = chess.get(fromSquare);
  if (!p) return [];
  const enemy = color === 'w' ? 'b' : 'w';
  const targets = [];
  for (const sq of boardPieces(chess)) {
    if (sq.color !== enemy || sq.type === 'k') continue;
    let attackers = [];
    try { attackers = chess.attackers(sq.square, color); } catch { continue; }
    if (!attackers.includes(fromSquare)) continue;
    const defenders = chess.attackers(sq.square, enemy);
    const value = PIECE_VALUE[sq.type];
    const lowValue = PIECE_VALUE[p.type];
    if (value >= 3 && (defenders.length === 0 || value > lowValue)) {
      targets.push({ square: sq.square, type: sq.type, name: PIECE_NAME_PT[sq.type], value });
    }
  }
  return targets.sort((a, b) => b.value - a.value);
}

/** Converte uma sequência UCI em SAN, parando no primeiro lance ilegal. */
export function pvToSan(fen, pv = [], max = 6) {
  const chess = new Chess(fen);
  const san = [];
  for (const uci of pv.slice(0, max)) {
    try {
      const mv = chess.move({
        from: uci.slice(0, 2),
        to: uci.slice(2, 4),
        promotion: uci[4] || undefined,
      });
      san.push(mv.san);
    } catch { break; }
  }
  return san;
}

/** Delta de material no fim de uma linha (positivo = brancas ganharam). */
export function pvMaterialDelta(fen, pv = []) {
  const chess = new Chess(fen);
  const before = material(fen).diff;
  for (const uci of pv.slice(0, 12)) {
    try {
      chess.move({ from: uci.slice(0, 2), to: uci.slice(2, 4), promotion: uci[4] || undefined });
    } catch { break; }
  }
  return material(chess.fen()).diff - before;
}

/**
 * Melhor captura imediata disponível para quem tem o lance.
 * Ganho aproximado = valor da peça capturada menos o valor da recaptura mais barata.
 */
export function bestImmediateCapture(fen) {
  const chess = new Chess(fen);
  let best = null;
  for (const mv of chess.moves({ verbose: true })) {
    if (!mv.captured) continue;
    const probe = new Chess(fen);
    probe.move({ from: mv.from, to: mv.to, promotion: mv.promotion });
    const recaptures = probe.attackers(mv.to, mv.color === 'w' ? 'b' : 'w');
    const cheapestRecapture = recaptures.length
      ? Math.min(...recaptures.map((sq) => {
        const piece = probe.get(sq);
        return piece ? PIECE_VALUE[piece.type] : 99;
      }))
      : 0;
    const gain = PIECE_VALUE[mv.captured] - cheapestRecapture;
    if (gain >= 1 && (!best || gain > best.gain)) {
      best = {
        gain,
        san: mv.san,
        square: mv.to,
        captured: mv.captured,
        capturedName: PIECE_NAME_PT[mv.captured],
      };
    }
  }
  return best;
}

function listPt(items) {
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  return `${items.slice(0, -1).join(', ')} e ${items[items.length - 1]}`;
}

/** Artigo definido para nomes de peça: o cavalo, a torre... */
export function definite(pieceName) {
  return `${['torre', 'dama'].includes(pieceName) ? 'a' : 'o'} ${pieceName}`;
}

function materialPt(v) {
  const n = Math.abs(v);
  const uni = { 1: ['um peão', 'peões'], 3: ['uma peça menor', 'peças menores'], 5: ['uma torre', 'torres'], 9: ['uma dama', 'damas'] };
  const key = [9, 5, 3, 1].find((k) => n >= k) || 1;
  return n === key ? uni[key][0] : `${n} ${uni[key][1]}`;
}

function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`;
}

const PHASE_ARTIGO = { abertura: 'a abertura', 'meio-jogo': 'o meio-jogo', final: 'o final' };

function phaseOf(chess) {
  const pieces = boardPieces(chess).length;
  const fullmove = Number(chess.fen().split(' ')[5]) || 1;
  if (fullmove <= 10 && pieces >= 26) return 'abertura';
  if (pieces <= 12 || fullmove >= 45) return 'final';
  return 'meio-jogo';
}

/** Descreve o que um lance faz, em termos concretos. */
export function describeMove(fenBefore, uciOrSan) {
  const chess = new Chess(fenBefore);
  let mv;
  try {
    mv = /^[a-h][1-8][a-h][1-8][qrbn]?$/.test(uciOrSan)
      ? chess.move({ from: uciOrSan.slice(0, 2), to: uciOrSan.slice(2, 4), promotion: uciOrSan[4] || undefined })
      : chess.move(uciOrSan);
  } catch {
    return null;
  }
  const enemy = mv.color === 'w' ? 'b' : 'w';
  const facts = {
    san: mv.san,
    piece: mv.piece,
    pieceName: PIECE_NAME_PT[mv.piece],
    capture: Boolean(mv.captured),
    capturedName: mv.captured ? PIECE_NAME_PT[mv.captured] : null,
    capturedValue: mv.captured ? PIECE_VALUE[mv.captured] : 0,
    check: chess.isCheck(),
    mate: chess.isCheckmate(),
    castle: mv.san === 'O-O' || mv.san === 'O-O-O',
    promotion: Boolean(mv.promotion),
    enPassant: mv.flags?.includes('e') || false,
    fork: [],
    attacksQueen: false,
    hangsAfter: [],
    givesMaterial: 0,
    opensCenter: ['d4', 'e4', 'd5', 'e5'].includes(mv.to),
    develops: mv.color === 'w'
      ? ['b1', 'c1', 'f1', 'g1'].includes(mv.from)
      : ['b8', 'c8', 'f8', 'g8'].includes(mv.from),
  };
  facts.fork = attackedTargets(chess, mv.to, mv.color);
  const q = chess.board().flat().find((p) => p && p.type === 'q' && p.color === enemy);
  if (q) {
    try {
      const atk = chess.attackers(q.square, mv.color);
      facts.attacksQueen = atk.includes(mv.to);
    } catch { /* ignora */ }
  }
  facts.hangsAfter = hangingPiecesOn(chess, mv.color);
  const matBefore = material(fenBefore).diff;
  const matAfter = material(chess.fen()).diff;
  facts.givesMaterial = mv.color === 'w' ? matBefore - matAfter : matAfter - matBefore;

  // frases curtas sobre o lance
  const reasons = [];
  if (facts.mate) reasons.push('dá xeque-mate');
  else if (facts.check) reasons.push('dá xeque');
  if (mv.captured) {
    reasons.push(`captura ${definite(facts.capturedName)}`);
  }
  if (facts.castle) reasons.push('põe o rei em segurança e ativa a torre');
  if (facts.promotion) reasons.push('promove o peão');
  if (facts.fork.length >= 2) {
    reasons.push(`cria um garfo: ataca ${listPt(facts.fork.slice(0, 2).map((t) => `${definite(t.name)} em ${t.square}`))}`);
  } else if (facts.fork.length === 1) {
    reasons.push(`ataca ${definite(facts.fork[0].name)} em ${facts.fork[0].square}`);
  } else if (facts.attacksQueen) {
    reasons.push('ataca a dama');
  }
  if (!reasons.length && facts.develops) reasons.push(`desenvolve ${definite(facts.pieceName)}`);
  if (!reasons.length && facts.opensCenter) reasons.push('disputa o centro');

  facts.reasons = reasons;
  return facts;
}

// --------------------------------------------------------------- pontuação

function epForMover(whiteEp, color) {
  return color === 'w' ? whiteEp : 1 - whiteEp;
}

/**
 * Classifica um lance.
 * `loss` = expectativa perdida (0..1) na ótica de quem jogou.
 */
export function classifyMove({ loss, isBest, altGap, sacrifice, epBefore, epAfter, ply, bookish, deliversMate }) {
  // Ordem importa: mate -> livro -> perdas grandes -> lances bons.
  const l = Math.max(0, loss);
  if (deliversMate) return sacrifice ? 'brilliant' : 'best';
  if (isBest || l <= 0.005) {
    if (bookish) return 'book';
    if (sacrifice && epBefore < 0.92 && epAfter >= 0.5) return 'brilliant';
    if (altGap >= 0.15) return 'great';
    return 'best';
  }
  if (l > 0.2) {
    // "Oportunidade perdida": havia ganho claro e o lance deixou escapar.
    if (epBefore >= 0.85 && epAfter < 0.75) return 'miss';
    return 'blunder';
  }
  if (l > 0.1) return 'mistake';
  if (l > 0.05) return 'inaccuracy';
  if (bookish) return 'book';
  if (l <= 0.02) return 'excellent';
  return 'good';
}

const BOOK_SAN_1 = new Set(['e4', 'd4', 'Nf3', 'c4', 'g3', 'b3', 'f4', 'Nc3', 'e3', 'd3']);
const BOOK_SAN_2 = new Set(['e5', 'c5', 'e6', 'c6', 'd5', 'Nf6', 'g6', 'd6', 'Nc6', 'b6']);

function isBookish(san, ply) {
  if (ply === 0) return BOOK_SAN_1.has(san);
  if (ply === 1) return BOOK_SAN_2.has(san);
  if (ply === 2) return ['Bb5', 'Bc4', 'd4', 'Nf3', 'c4', 'g3', 'b3', 'Nc3', 'Be2', 'Bd3'].includes(san);
  if (ply === 3) return ['Nf6', 'Nc6', 'd5', 'e6', 'c5', 'g6', 'd6', 'Be7', 'Bb4', 'Bc5'].includes(san);
  return false;
}

// ---------------------------------------------------------- precisão do lado

function moveAccuracy(epBeforeMover, epAfterMover) {
  const winBefore = epBeforeMover * 100;
  const winAfter = epAfterMover * 100;
  const drop = Math.max(0, winBefore - winAfter);
  const acc = 103.1668 * Math.exp(-0.04354 * drop) - 3.1669;
  return clamp(acc, 0, 100);
}

// ------------------------------------------------------------- explicação

/** Mate a favor (>0), contra (<0) ou null, na ótica de `color`. */
export function mateFor(score, color) {
  if (!score || score.mate == null) return null;
  const favor = color === 'w' ? score.mate > 0 : score.mate < 0;
  return favor ? Math.abs(score.mate) : -Math.abs(score.mate);
}

/**
 * Regras duras de mate que se sobrepõem à perda de expectativa:
 *   - deixar de ter mate garantido e permitir mate do adversário => erro grave;
 *   - ter mate forçado e não jogar mate => oportunidade perdida.
 */
export function applyMateOverrides(cls, { evalBefore, evalAfter, mover, playedMate }) {
  const before = mateFor(evalBefore, mover);
  const after = mateFor(evalAfter, mover);
  if (playedMate) return cls;
  if (after != null && after < 0 && (before == null || before > 0)) return 'blunder';
  if (before != null && before > 0 && (after == null || after < 0)) return 'miss';
  return cls;
}

/**
 * Explica um lance já classificado.
 * Cada frase vem de um fato calculado: mate forçado, material ganho/perdido na
 * linha principal, peça mal defendida, tipo de lance (captura, roque, garfo...).
 */
export function explainMove(record, ctx = {}) {
  const { linesBefore = [], linesAfter = [] } = ctx;
  const { fenBefore, fenAfter, color: mover } = record;
  const facts = describeMove(fenBefore, record.san);
  const bestLine = linesBefore[0];
  const bestSan = bestLine ? pvToSan(fenBefore, bestLine.pv, 1)[0] : null;
  const bestFacts = bestSan && bestSan !== record.san ? describeMove(fenBefore, bestSan) : null;
  const bestPvSan = bestLine ? pvToSan(fenBefore, bestLine.pv, 4) : [];
  const pvAfter = linesAfter[0]?.pv ?? [];
  const punishSan = pvToSan(fenAfter, pvAfter, 4);
  const playedIsBest = !bestSan || bestSan === record.san;

  const mateAgainst = mateFor(record.evalAfterWhite, mover);
  const mateDrop = mateAgainst != null && mateAgainst < 0;
  const immediate = bestImmediateCapture(fenAfter);

  const headlineByClass = {
    brilliant: 'Sacrifício que funciona',
    great: 'O único lance que mantinha a vantagem',
    best: 'Melhor lance',
    excellent: 'Excelente lance',
    good: 'Lance sólido',
    book: 'Lance de livro',
    inaccuracy: 'Imprecisão',
    mistake: 'Erro',
    miss: 'Oportunidade perdida',
    blunder: 'Erro grave',
  };
  const headline = headlineByClass[record.class] || 'Lance';
  const parts = [];
  const tips = [];
  const isBad = ['inaccuracy', 'mistake', 'miss', 'blunder'].includes(record.class);

  const whyBest = () => {
    if (!bestFacts) return '';
    if (bestFacts.mate) return 'dá mate';
    const r = bestFacts.reasons.filter((x) => !x.startsWith('cria um garfo'));
    return r.length ? r.slice(0, 2).join(' e ') : '';
  };

  if (!isBad) {
    if (facts?.mate) parts.push('É mate: a partida termina aqui.');
    else if (facts?.reasons?.length) parts.push(`O lance ${facts.reasons.slice(0, 2).join(' e ')}.`);

    if (record.class === 'brilliant') {
      parts.push('Você entrega material de propósito e a compensação se sustenta: a linha principal devolve a vantagem.');
    } else if (record.class === 'great') {
      parts.push('Era praticamente o único lance que mantinha a vantagem.');
    }

    if (record.class === 'book') {
      // lance de teoria: não faz sentido comparar com a preferência do motor
    } else if (!playedIsBest && bestSan) {
      const why = whyBest();
      parts.push(`O motor preferia ${bestSan}${why ? ` (${why})` : ''}, mas a diferença é pequena.`);
    } else if (bestPvSan.length >= 2 && record.class !== 'book' && !facts?.mate) {
      parts.push(`A continuação recomendada é ${bestPvSan.slice(0, 3).join(' ')}.`);
    }

    if (!facts?.mate) {
      const evalAfter = record.evalAfterWhite;
      const losing = mover === 'w' ? evalAfter?.cp < -200 : evalAfter?.cp > 200;
      if (losing && evalAfter?.mate == null) {
        parts.push(`A posição segue difícil para você (${formatEval(evalAfter)}).`);
      }
    }
  } else {
    // 1) consequência concreta do lance jogado
    const mateLost = record.class === 'miss' ? mateFor(record.evalBeforeWhite, mover) : null;
    if (mateLost != null && mateLost > 0) {
      parts.push(`Você tinha mate em ${mateLost}${bestSan ? ` com ${bestSan}` : ''} e deixou passar.`);
    } else if (mateDrop) {
      parts.push(
        `O lance permite mate em ${Math.abs(mateAgainst)}${punishSan.length ? ` (${punishSan.slice(0, 2).join(' ')})` : ''}.`,
      );
    } else {
      const problems = [];
      const worst = facts?.hangsAfter?.[0];
      const samePiece = worst && immediate && worst.square === immediate.square;
      if (immediate) {
        problems.push(
          `o adversário captura ${definite(immediate.capturedName)} em ${immediate.square} com ${immediate.san}, ganhando ${materialPt(immediate.gain)}`,
        );
      } else if (worst) {
        problems.push(
          `${worst.undefended ? 'deixa' : 'entrega'} ${definite(worst.name)} em ${worst.square}${worst.undefended ? ' sem defesa' : ' para uma captura vantajosa'}`,
        );
      }
      if (!immediate && punishSan.length && record.loss > 0.05) {
        problems.push(`a continuação ${punishSan.slice(0, 2).join(' ')} deixa o adversário confortável`);
      }
      if (samePiece) {
        // a mesma peça já foi citada acima; não repete
      }
      if (problems.length) parts.push(`O problema: ${listPt(problems.slice(0, 2))}.`);
      else if (record.loss > 0.05) {
        parts.push(`A avaliação sai de ${formatEval(record.evalBeforeWhite)} para ${formatEval(record.evalAfterWhite)}.`);
      }
    }

    // 2) a alternativa concreta (a não ser que já tenha sido citada como mate perdido)
    if (bestSan && !playedIsBest && !(mateLost != null && mateLost > 0)) {
      const why = whyBest();
      parts.push(`O melhor era ${bestSan}${why ? ` — ${why}` : ''}.`);
    }

    // 3) dica acionável
    if (record.class === 'blunder' || record.class === 'mistake') {
      if (facts?.hangsAfter?.length) tips.push('Antes de mover, conte quem defende a peça atacada: peça sem defesa é material perdido.');
      if (mateDrop) tips.push('Com o rei exposto, liste todos os xeques do adversário antes de qualquer outro lance.');
      if (immediate) tips.push('Quando uma peça sua é capturável, calcule a recaptura antes de escolher o lance.');
    }
    if (record.class === 'miss') {
      tips.push(`Havia um ganho forçado com ${bestSan || 'outro lance'}: treine reconhecer esse padrão mais rápido.`);
    }
  }

  if (!parts.length) parts.push(`Avaliação depois do lance: ${formatEvalPt(record.evalAfterWhite)}.`);

  return {
    headline,
    text: parts.join(' '),
    tips,
    bestSan,
    bestPvSan,
    punishPv: punishSan,
    facts,
    mateDrop,
    immediate,
  };
}

// ---------------------------------------------------------------- revisão

/**
 * Monta a revisão completa.
 *
 * @param {object} opts
 * @param {string} opts.pgn             PGN da partida
 * @param {Array}  opts.positions       [{ fen, turn, lines:[{cp,mate,pv}] }] para cada posição 0..N
 * @param {object} [opts.headers]
 * @returns {{moves, summary, accuracy, counts, pgn, headers, initialFen}}
 */
export function buildReview({ pgn, positions = [], headers = {} }) {
  const chess = new Chess();
  let parsedHeaders = { ...headers };
  let startFen = null;
  try {
    chess.loadPgn(pgn);
    parsedHeaders = { ...chess.getHeaders(), ...headers };
    startFen = chess.history({ verbose: true })[0]?.before ?? null;
  } catch (err) {
    throw new Error(`PGN inválido: ${err.message}`);
  }

  const history = chess.history({ verbose: true });
  if (!history.length) throw new Error('PGN sem lances.');

  const startPosition = startFen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  const fens = [startPosition, ...history.map((m) => m.after)];

  const scoreAt = (i) => {
    const pos = positions[i];
    if (!pos?.lines?.length) return null;
    return toWhiteScore(pos.lines[0], pos.turn || (i % 2 === 0 ? 'w' : 'b'));
  };

  const epAt = (i) => {
    const s = scoreAt(i);
    return s ? expectedPointsWhite(s) : null;
  };

  const moves = history.map((mv, i) => {
    const epBefore = epAt(i);
    const epAfter = epAt(i + 1);
    const mover = mv.color;
    const epB = epBefore == null ? null : epForMover(epBefore, mover);
    const epA = epAfter == null ? null : epForMover(epAfter, mover);
    const loss = epB == null || epA == null ? 0 : Math.max(0, epB - epA);

    const linesBefore = positions[i]?.lines || [];
    const linesAfter = positions[i + 1]?.lines || [];
    const bestUci = linesBefore[0]?.pv?.[0];
    const playedUci = mv.from + mv.to + (mv.promotion || '');
    const isBest = bestUci ? bestUci === playedUci : loss <= 0.005;

    let altGap = 0;
    if (linesBefore.length > 1) {
      const turn = positions[i]?.turn || (i % 2 === 0 ? 'w' : 'b');
      const bestEp = epForMover(expectedPointsWhite(toWhiteScore(linesBefore[0], turn)), mover);
      const secondEp = epForMover(expectedPointsWhite(toWhiteScore(linesBefore[1], turn)), mover);
      altGap = Math.max(0, bestEp - secondEp);
    }

    // Sacrifício = a linha de resposta do motor mostra você entregando material
    // sem perder a avaliação (o clássico "material a menos, posição melhor").
    const pvAfterFirst = positions[i + 1]?.lines?.[0]?.pv || [];
    const deltaPv = pvAfterFirst.length ? pvMaterialDelta(mv.after, pvAfterFirst, 8) : 0;
    const lossForMover = mover === 'w' ? deltaPv : -deltaPv;
    const sacrifice = lossForMover <= -1 && !mv.san.includes('#');

    let cls = classifyMove({
      loss,
      isBest,
      altGap,
      sacrifice,
      epBefore: epB ?? 0.5,
      epAfter: epA ?? 0.5,
      ply: i,
      bookish: isBookish(mv.san, i),
      deliversMate: mv.san.includes('#'),
    });
    cls = applyMateOverrides(cls, {
      evalBefore: scoreAt(i),
      evalAfter: scoreAt(i + 1),
      mover,
      playedMate: mv.san.includes('#'),
    });

    const accuracy = epB == null || epA == null ? null : moveAccuracy(epB, epA);

    const record = {
      ply: i,
      moveNumber: Math.floor(i / 2) + 1,
      color: mover,
      san: mv.san,
      from: mv.from,
      to: mv.to,
      promotion: mv.promotion || null,
      fenBefore: mv.before,
      fenAfter: mv.after,
      phase: phaseOf(new Chess(mv.before)),
      class: cls,
      loss,
      accuracy,
      evalBeforeWhite: scoreAt(i),
      evalAfterWhite: scoreAt(i + 1),
      bestSan: linesBefore[0] ? pvToSan(mv.before, linesBefore[0].pv, 1)[0] : null,
      bestPvSan: linesBefore[0] ? pvToSan(mv.before, linesBefore[0].pv, 5) : [],
      linesBefore,
      linesAfter,
    };
    record.explanation = explainMove(record, { linesBefore, linesAfter });
    return record;
  });

  const counts = {};
  for (const key of Object.keys(CLASS_INFO)) counts[key] = 0;
  for (const m of moves) counts[m.class] = (counts[m.class] || 0) + 1;

  const accFor = (color) => {
    const list = moves.filter((m) => m.color === color && m.accuracy != null);
    if (!list.length) return null;
    const avg = list.reduce((s, m) => s + m.accuracy, 0) / list.length;
    return Math.round(avg * 10) / 10;
  };

  const summary = buildSummary(moves, counts, accFor);

  return {
    pgn: chess.pgn(),
    headers: parsedHeaders,
    initialFen: startPosition,
    moves,
    counts,
    accuracy: { white: accFor('w'), black: accFor('b') },
    summary,
    finalFen: fens[fens.length - 1],
  };
}

/** Um sacrifício = o lance entrega material e a peça pode ser capturada. */
function detectSacrifice(fenBefore, uci) {
  const before = material(fenBefore).diff;
  const chess = new Chess(fenBefore);
  const color = chess.turn();
  try {
    chess.move({ from: uci.slice(0, 2), to: uci.slice(2, 4), promotion: uci[4] || undefined });
  } catch { return false; }
  const after = material(chess.fen()).diff;
  const gave = color === 'w' ? before - after : after - before;
  if (gave < 1) return false;
  const mover = color;
  const hanging = hangingPiecesOn(chess, mover);
  // a peça sacrificada precisa poder ser capturada de fato
  return hanging.length > 0 && gave >= 1;
}

function buildSummary(moves, counts, accFor) {
  const bad = (m) => ['blunder', 'mistake', 'miss'].includes(m.class);
  const byPhase = { abertura: [], 'meio-jogo': [], final: [] };
  for (const m of moves) if (byPhase[m.phase]) byPhase[m.phase].push(m);
  const worstPhase = Object.entries(byPhase)
    .map(([phase, list]) => ({ phase, errors: list.filter(bad).length, total: list.length }))
    .sort((a, b) => b.errors - a.errors)[0];

  const worst = [...moves].filter(bad).sort((a, b) => b.loss - a.loss).slice(0, 3);
  const materialErrors = moves.filter(
    (m) => bad(m) && (m.explanation?.facts?.hangsAfter?.length || 0) > 0,
  ).length;
  const mateErrors = moves.filter((m) => bad(m) && m.explanation?.mateDrop).length;

  const lines = [];
  const wAcc = accFor('w');
  const bAcc = accFor('b');
  if (wAcc != null && bAcc != null) {
    lines.push(`Precisão: brancas ${wAcc}% · pretas ${bAcc}%.`);
  }

  const perSide = (color) => {
    const list = moves.filter((m) => m.color === color);
    const bits = [];
    const cnt = (c) => list.filter((m) => m.class === c).length;
    if (cnt('blunder')) bits.push(plural(cnt('blunder'), 'erro grave', 'erros graves'));
    if (cnt('mistake')) bits.push(plural(cnt('mistake'), 'erro', 'erros'));
    if (cnt('miss')) bits.push(plural(cnt('miss'), 'oportunidade perdida', 'oportunidades perdidas'));
    if (cnt('inaccuracy')) bits.push(plural(cnt('inaccuracy'), 'imprecisão', 'imprecisões'));
    return { bits, total: list.filter(bad).length };
  };
  const w = perSide('w');
  const b = perSide('b');
  const nameWhite = moves.length ? 'Brancas' : 'Brancas';
  if (w.total === 0 && b.total === 0) {
    lines.push('Nenhum erro grave na partida — jogo limpo do começo ao fim.');
  } else {
    const fmt = (side, r) => `${side}: ${r.bits.length ? r.bits.join(', ') : 'sem erros relevantes'}`;
    lines.push(`${fmt(nameWhite, w)} · ${fmt('Pretas', b)}.`);
    const worstSide = w.total >= b.total ? 'brancas' : 'pretas';
    if (Math.abs(w.total - b.total) >= 2) {
      lines.push(`O jogo se decidiu pelos erros das ${worstSide}.`);
    }
  }
  if (worstPhase && worstPhase.errors > 0) {
    lines.push(`A fase mais custosa foi ${PHASE_ARTIGO[worstPhase.phase]} (${plural(worstPhase.errors, 'erro', 'erros')}).`);
  }
  if (materialErrors > 0) {
    lines.push(`${plural(materialErrors, 'erro envolveu', 'erros envolveram')} material mal protegido — o padrão mais fácil de corrigir.`);
  }
  if (mateErrors > 0) {
    lines.push(`${plural(mateErrors, 'erro deixou', 'erros deixaram')} o rei exposto a mate.`);
  }
  if (worst.length) {
    lines.push(`Piores momentos: ${worst.map((m) => `${m.moveNumber}${m.color === 'w' ? '.' : '...'} ${m.san}`).join(', ')}.`);
  }
  return { text: lines.join(' '), worst, byPhase, worstPhase: worstPhase?.phase ?? null };
}
