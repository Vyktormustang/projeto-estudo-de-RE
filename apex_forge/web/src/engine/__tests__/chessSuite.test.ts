import { Chess, Square, PieceSymbol, validateFen } from 'chess.js';
import { describe, expect, it } from 'vitest';
import {
  CHESS_BOTS,
  MOVE_BADGES,
  analyzePositionMultiPv,
  chooseBotMove,
  computeEloDelta,
  computeMaterialSummary,
  evaluatePositionWhiteCp,
  explainMoveCoachPt,
  runFullGameReview,
  sideHasMatingMaterial,
} from '../chess/chessEngine';
import {
  OPENING_BOOK_LINES,
  detectOpeningFromMoves,
  pickBookMoveForBot,
} from '../chess/openingBook';
import {
  CHESS_PUZZLES_CATALOG,
  getDailyPuzzleForDate,
  pickNextRatedPuzzle,
} from '../chess/puzzlesCatalog';
import {
  ALL_64_SQUARES,
  CHESS_ACADEMY_LESSONS,
  CHESS_ENDGAME_DRILLS,
  EMPTY_BOARD_FEN,
  generateChess960Position,
} from '../chess/chessTrainingSuite';
import { computePolymathRadar } from '../polymathRadarEngine';
import { createInitialVault } from '../stateEngine';
import { ENGINE_VERSION } from '../types';

describe('FORJA v23.0.0 — Suíte Soberana Chess.com 2.0 (FIDE + Chess960 #0–#959 + CAPS Review + 36 Problemas + Visão + 8 Finais + 6 Aulas)', () => {
  it('mantém ENGINE_VERSION = 23.0.0 e inicializa chessState v17 no Vault', () => {
    expect(ENGINE_VERSION).toBe('23.0.0');
    const v = createInitialVault();
    expect(v.chessState).toBeDefined();
    expect(v.chessState?.playRating).toBe(800);
    expect(v.chessState?.puzzleRating).toBe(800);
    expect(v.chessState?.visionBestScore).toBe(0);
    expect(v.chessState?.completedAcademyIds).toEqual([]);
    expect(v.chessState?.completedEndgameIds).toEqual([]);
    expect(v.chessState?.preferredTheme).toBe('CHESS_VERDE');
  });

  it('valida todas as regras oficiais FIDE: roque, en passant com mate, promoção/subpromoção, afogamento, tripla repetição e material insuficiente', () => {
    // 1. Roque curto e longo
    const gCastle = new Chess('r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1');
    expect(gCastle.move('O-O-O')?.san).toBe('O-O-O');
    expect(gCastle.move('O-O')?.san).toBe('O-O');

    // 2. Captura En Passant dando Xeque-Mate imediato!
    const gEp = new Chess('6rb/3N2kp/6pp/5pP1/2B5/6K1/8/8 w - f6 0 1');
    const epMove = gEp.move({ from: 'g5', to: 'f6' });
    expect(epMove).not.toBeNull();
    expect(gEp.isCheckmate()).toBe(true);

    // 3. Subpromoção para Cavalo com Garfo Real
    const gPromo = new Chess('8/2q1P3/5k2/8/8/8/6PP/6K1 w - - 0 1');
    const nPromo = gPromo.move({ from: 'e7', to: 'e8', promotion: 'n' });
    expect(nPromo?.san).toBe('e8=N+');
    expect(gPromo.inCheck()).toBe(true);

    // 4. Afogamento (Stalemate)
    const gStale = new Chess('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1');
    expect(gStale.isStalemate()).toBe(true);
    expect(gStale.isDraw()).toBe(true);

    // 5. Tripla repetição FIDE
    const gRep = new Chess();
    for (let i = 0; i < 2; i++) {
      gRep.move('Nf3');
      gRep.move('Nf6');
      gRep.move('Ng1');
      gRep.move('Ng8');
    }
    expect(gRep.isThreefoldRepetition()).toBe(true);

    // 6. Material insuficiente FIDE (Rei + Bispo vs Rei)
    const gInsuff = new Chess('8/8/4k3/8/8/4K3/5B2/8 w - - 0 1');
    expect(gInsuff.isInsufficientMaterial()).toBe(true);
  });

  it('aplica corretamente o Artigo 6.9 da FIDE para material de mate em queda de seta (sideHasMatingMaterial)', () => {
    expect(sideHasMatingMaterial(new Chess('4k3/8/8/8/8/8/4P3/4K3 w - - 0 1'), 'w')).toBe(true);
    expect(sideHasMatingMaterial(new Chess('4k3/8/8/8/8/8/4P3/4K3 w - - 0 1'), 'b')).toBe(false);
    expect(sideHasMatingMaterial(new Chess('4k3/8/8/8/8/8/5N2/4K3 w - - 0 1'), 'w')).toBe(false);
    expect(sideHasMatingMaterial(new Chess('4k3/8/8/8/8/8/4BB2/4K3 w - - 0 1'), 'w')).toBe(true);
    // Dois bispos na MESMA cor de casa não dão mate forçado sozinhos
    expect(sideHasMatingMaterial(new Chess('4k3/8/8/8/8/3B4/4B3/4K3 w - - 0 1'), 'w')).toBe(false);
  });

  it('contabiliza exatamente peças capturadas, saldo material e variação Elo', () => {
    const g = new Chess();
    g.move('e4');
    g.move('d5');
    g.move('exd5');
    const mat = computeMaterialSummary(g);
    expect(mat.capturedByWhite).toEqual(['p']);
    expect(mat.capturedByBlack).toEqual([]);
    expect(mat.whiteAdvantagePts).toBe(1);

    const winVsHigher = computeEloDelta(1000, 1400, 1);
    const winVsLower = computeEloDelta(1400, 1000, 1);
    expect(winVsHigher).toBeGreaterThan(winVsLower);
    expect(computeEloDelta(1200, 1200, 0.5)).toBe(0);
  });

  it('valida 100% das 48 aberturas do Livro ECO (A00–E60) e o seletor de livro para Bots', () => {
    expect(OPENING_BOOK_LINES.length).toBeGreaterThanOrEqual(45);
    for (const line of OPENING_BOOK_LINES) {
      const g = new Chess();
      for (const san of line.movesSan) {
        const m = g.move(san);
        expect(m, `Lance inválido ${san} na abertura ${line.eco} ${line.namePt}`).not.toBeNull();
      }
    }

    const ruy = detectOpeningFromMoves(['e4', 'e5', 'Nf3', 'Nc6', 'Bb5']);
    expect(ruy.eco).toBe('C60');
    expect(ruy.namePt).toContain('Ruy López');

    const bookChess = new Chess();
    bookChess.move('e4');
    bookChess.move('e5');
    bookChess.move('Nf3');
    const bookMove = pickBookMoveForBot(bookChess, 1600, 42);
    expect(bookMove).not.toBeNull();
  });

  it('valida os 8 Bots calibrados (400–2400 Elo) e a geração de lances legais sob pressão', () => {
    expect(CHESS_BOTS).toHaveLength(8);
    expect(CHESS_BOTS[0].elo).toBe(400);
    expect(CHESS_BOTS[CHESS_BOTS.length - 1].elo).toBe(2400);

    for (let i = 1; i < CHESS_BOTS.length; i++) {
      expect(CHESS_BOTS[i].elo).toBeGreaterThan(CHESS_BOTS[i - 1].elo);
    }

    const midFen = 'r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7';
    for (const bot of [CHESS_BOTS[0], CHESS_BOTS[3], CHESS_BOTS[7]]) {
      const choice = chooseBotMove(midFen, bot, [], 123);
      expect(choice).not.toBeNull();
      const sim = new Chess(midFen);
      expect(
        sim.move({
          from: choice!.from,
          to: choice!.to,
          promotion: choice!.promotion,
        }),
      ).not.toBeNull();
    }
  });

  it('valida todos os 36 problemas táticos contra chess.js e contra o motor Alpha-Beta (100% precisão)', () => {
    expect(CHESS_PUZZLES_CATALOG.length).toBe(36);

    for (const p of CHESS_PUZZLES_CATALOG) {
      expect(validateFen(p.fen).ok).toBe(true);
      const g = new Chess(p.fen);
      for (const lan of p.solutionLan) {
        const m = g.move({
          from: lan.slice(0, 2) as Square,
          to: lan.slice(2, 4) as Square,
          promotion: lan[4] as PieceSymbol | undefined,
        });
        expect(m, `Lance ilegal ${lan} em ${p.id}`).not.toBeNull();
      }
      if (p.themeTagPt.includes('Mate em')) {
        expect(g.isCheckmate(), `${p.id} deveria terminar em xeque-mate`).toBe(true);
      }

      const depth = p.solutionLan.length >= 7 ? 7 : 4;
      const top = analyzePositionMultiPv(p.fen, {
        maxDepth: depth,
        multiPv: 1,
        timeBudgetMs: 1200,
      })[0];
      expect(top?.moveLan, `Motor divergiu em ${p.id}`).toBe(p.solutionLan[0]);
    }

    const daily = getDailyPuzzleForDate('2026-10-26');
    expect(daily.id).toBeTruthy();
    const rated = pickNextRatedPuzzle(1200, [daily.id], daily.id);
    expect(rated.id).not.toBe(daily.id);
  }, 20_000);

  it('executa Revisão Completa da Partida (CAPS Accuracy % + 9 Selos + Comentários do Treinador)', () => {
    expect(Object.keys(MOVE_BADGES)).toHaveLength(9);

    // Mate do Louco / Capivarada rápida para testar TEORIA, CAPIVARADA e MELHOR
    const g = new Chess();
    for (const san of ['e4', 'e5', 'Bc4', 'Nc6', 'Qh5', 'Nf6', 'Qxf7#']) {
      g.move(san);
    }
    const report = runFullGameReview(g.history({ verbose: true }));
    expect(report.moves).toHaveLength(7);
    expect(report.whiteAccuracyPct).toBeGreaterThanOrEqual(80);
    expect(report.blackAccuracyPct).toBeLessThan(report.whiteAccuracyPct);
    expect(report.countsWhite.TEORIA).toBeGreaterThanOrEqual(2);
    expect(report.countsBlack.CAPIVARADA).toBeGreaterThanOrEqual(1);

    const bestLine = analyzePositionMultiPv(
      '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1',
      { maxDepth: 2, multiPv: 1, timeBudgetMs: 120 },
    )[0];
    expect(explainMoveCoachPt('6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1', bestLine)).toContain(
      'xeque-mate',
    );
  });

  it('integra o progresso enxadrístico (partidas + problemas resolvidos) ao Radar Polímata 10D', () => {
    const baseVault = createInitialVault();
    const baseRadar = computePolymathRadar(baseVault);

    const chessVault = createInitialVault();
    chessVault.chessState = {
      ...chessVault.chessState!,
      gamesPlayed: 8,
      wins: 6,
      solvedPuzzleIds: ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'],
    };
    const nextRadar = computePolymathRadar(chessVault);

    const baseLogica = baseRadar.axes.find((a) => a.trackId === 'LOGICA_NUMERACIA')!.score100;
    const nextLogica = nextRadar.axes.find((a) => a.trackId === 'LOGICA_NUMERACIA')!.score100;
    const baseEstrat = baseRadar.axes.find((a) => a.trackId === 'ESTRATEGIA_SISTEMAS')!.score100;
    const nextEstrat = nextRadar.axes.find((a) => a.trackId === 'ESTRATEGIA_SISTEMAS')!.score100;

    expect(nextLogica).toBeGreaterThan(baseLogica);
    expect(nextEstrat).toBeGreaterThan(baseEstrat);
    expect(evaluatePositionWhiteCp(new Chess())).toBe(0);
  });

  it('valida todas as 960 posições oficiais Chess960 / Freestyle (Scharnagl #0–#959, #518 = Clássico FIDE)', () => {
    const seen = new Set<string>();
    for (let id = 0; id < 960; id++) {
      const pos = generateChess960Position(id);
      expect(pos.id).toBe(id);
      expect(validateFen(pos.fen).ok).toBe(true);
      seen.add(pos.backRankUpper);

      const r1 = pos.backRankUpper.indexOf('R');
      const r2 = pos.backRankUpper.lastIndexOf('R');
      const k = pos.backRankUpper.indexOf('K');
      const b1 = pos.backRankUpper.indexOf('B');
      const b2 = pos.backRankUpper.lastIndexOf('B');
      expect(r1).toBeLessThan(k);
      expect(k).toBeLessThan(r2);
      expect((b1 % 2) !== (b2 % 2)).toBe(true);

      const g = new Chess(pos.fen);
      expect(g.moves().length).toBeGreaterThanOrEqual(18);
      expect(g.moves().length).toBeLessThanOrEqual(20);
    }
    expect(seen.size).toBe(960);
    expect(generateChess960Position(518).backRankUpper).toBe('RNBQKBNR');

    // Revisão CAPS em partida Chess960 / FEN Customizado (não deve rotular lance 1 como TEORIA)
    const c960 = new Chess(generateChess960Position(42).fen);
    c960.move(c960.moves()[0]);
    c960.move(c960.moves()[0]);
    const rev960 = runFullGameReview(c960.history({ verbose: true }));
    expect(rev960.moves).toHaveLength(2);
    expect(rev960.countsWhite.TEORIA).toBe(0);
    expect(rev960.countsBlack.TEORIA).toBe(0);
  });

  it('valida o Centro de Treinamento v15.0 (Visão 64 casas, 8 Finais vs Motor e 6 Aulas Interativas Guiadas)', () => {
    expect(ALL_64_SQUARES).toHaveLength(64);
    expect(validateFen(EMPTY_BOARD_FEN).ok).toBe(true);

    expect(CHESS_ENDGAME_DRILLS).toHaveLength(8);
    for (const drill of CHESS_ENDGAME_DRILLS) {
      expect(validateFen(drill.fen).ok).toBe(true);
      const g = new Chess(drill.fen);
      expect(g.turn()).toBe(drill.userColor);
      expect(g.moves().length).toBeGreaterThan(0);
      // Garante zero capturas falsas no inicio do exercicio de final!
      const mat = computeMaterialSummary(g, drill.fen);
      expect(mat.capturedByWhite).toEqual([]);
      expect(mat.capturedByBlack).toEqual([]);
    }

    expect(CHESS_ACADEMY_LESSONS).toHaveLength(6);
    for (const lesson of CHESS_ACADEMY_LESSONS) {
      expect(lesson.steps.length).toBeGreaterThanOrEqual(2);
      for (const step of lesson.steps) {
        expect(validateFen(step.fen).ok).toBe(true);
        for (const lan of step.expectedLan) {
          const g = new Chess(step.fen);
          const m = g.move({
            from: lan.slice(0, 2) as Square,
            to: lan.slice(2, 4) as Square,
            promotion: lan[4] as PieceSymbol | undefined,
          });
          expect(m, `Lance inválido ${lan} na aula ${lesson.id}`).not.toBeNull();
          if (step.autoReplyLan) {
            const r = g.move({
              from: step.autoReplyLan.slice(0, 2) as Square,
              to: step.autoReplyLan.slice(2, 4) as Square,
              promotion: step.autoReplyLan[4] as PieceSymbol | undefined,
            });
            expect(r, `Auto-resposta inválida ${step.autoReplyLan} em ${lesson.id}`).not.toBeNull();
          }
        }
      }
    }
  });
});
