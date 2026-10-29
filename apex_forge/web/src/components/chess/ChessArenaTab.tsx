import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Chess, Color, Move, PieceSymbol, Square, validateFen } from 'chess.js';
import {
  ChessBoardThemeId,
  ChessSavedGame,
  ChessVaultData,
  VaultState,
} from '../../engine/types';
import {
  CHESS_BOTS,
  ChessBotProfile,
  EngineSearchLine,
  FullGameReviewReport,
  MOVE_BADGES,
  MoveClassification,
  analyzePositionMultiPv,
  chooseBotMove,
  computeEloDelta,
  computeEloCategory,
  computeChessPlayerStats,
  computeMaterialSummary,
  evaluatePositionWhiteCp,
  explainMoveCoachPt,
  getAvailableAchievements,
  getUnlockedAchievements,
  runFullGameReview,
  sideHasMatingMaterial,
  CHESS_ACHIEVEMENTS,
} from '../../engine/chess/chessEngine';
import {
  OPENING_BOOK_LINES,
  detectOpeningFromMoves,
} from '../../engine/chess/openingBook';
import {
  CHESS_PUZZLES_CATALOG,
  ChessPuzzleSpec,
  getDailyPuzzleForDate,
  pickNextRatedPuzzle,
} from '../../engine/chess/puzzlesCatalog';
import {
  CHESS_ACADEMY_LESSONS,
  CHESS_ENDGAME_DRILLS,
  EndgameDrillSpec,
  InteractiveChessLesson,
  generateChess960Position,
} from '../../engine/chess/chessTrainingSuite';
import { playChessSound } from '../../services/audioBiofeedback';
import { triggerHaptic } from '../../services/vaultStorage';
import { BoardArrowSpec, ChessBoardView, SquareBadgeOverlay } from './ChessBoardView';
import { CHESS_BOARD_THEMES, ChessPieceSvg } from './ChessPiecesSvg';

interface TimeControlPreset {
  id: string;
  category: 'Bullet' | 'Blitz' | 'Rápido' | 'Clássico' | 'Livre';
  label: string;
  initialMs: number;
  incrementMs: number;
}

const TIME_CONTROLS: TimeControlPreset[] = [
  { id: 'bullet_1_0', category: 'Bullet', label: '1 | 0', initialMs: 60_000, incrementMs: 0 },
  { id: 'bullet_2_1', category: 'Bullet', label: '2 | 1', initialMs: 120_000, incrementMs: 1_000 },
  { id: 'blitz_3_0', category: 'Blitz', label: '3 | 0', initialMs: 180_000, incrementMs: 0 },
  { id: 'blitz_3_2', category: 'Blitz', label: '3 | 2', initialMs: 180_000, incrementMs: 2_000 },
  { id: 'blitz_5_0', category: 'Blitz', label: '5 | 0', initialMs: 300_000, incrementMs: 0 },
  { id: 'rapid_10_0', category: 'Rápido', label: '10 | 0', initialMs: 600_000, incrementMs: 0 },
  { id: 'rapid_15_10', category: 'Rápido', label: '15 | 10', initialMs: 900_000, incrementMs: 10_000 },
  { id: 'classic_30_0', category: 'Clássico', label: '30 | 0', initialMs: 1_800_000, incrementMs: 0 },
  { id: 'unlimited', category: 'Livre', label: 'Sem Relógio ∞', initialMs: 0, incrementMs: 0 },
];

const OPERA_GAME_SAN = [
  'e4', 'e5', 'Nf3', 'd6', 'd4', 'Bg4', 'dxe5', 'Bxf3', 'Qxf3', 'dxe5',
  'Bc4', 'Nf6', 'Qb3', 'Qe7', 'Nc3', 'c6', 'Bg5', 'b5', 'Nxb5', 'cxb5',
  'Bxb5+', 'Nbd7', 'O-O-O', 'Rd8', 'Rxd7', 'Rxd7', 'Rd1', 'Qe6', 'Bxd7+', 'Nxd7',
  'Qb8+', 'Nxb8', 'Rd8#',
];

function formatClockMs(ms: number): string {
  const clamped = Math.max(0, ms);
  if (clamped < 20_000) {
    const secs = Math.floor(clamped / 1000);
    const tenths = Math.floor((clamped % 1000) / 100);
    const mins = Math.floor(secs / 60);
    const remS = secs % 60;
    return `${mins}:${String(remS).padStart(2, '0')}.${tenths}`;
  }
  const totalSec = Math.ceil(clamped / 1000);
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

const STANDARD_START_FEN =
  'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const EMPTY_BOARD_FEN = '8/8/8/8/8/8/8/8 w - - 0 1';
const ALL_64_SQUARES: Square[] = (() => {
  const out: Square[] = [];
  const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
  for (let r = 1; r <= 8; r++) {
    for (const f of files) {
      out.push(`${f}${r}` as Square);
    }
  }
  return out;
})();

function ensureChessVault(v?: ChessVaultData): ChessVaultData {
  return {
    playRating: v?.playRating ?? 800,
    playEloCategory: v?.playEloCategory ?? 'INICIANTE',
    puzzleRating: v?.puzzleRating ?? 800,
    puzzleRushBest: v?.puzzleRushBest ?? 0,
    visionBestScore: v?.visionBestScore ?? 0,
    gamesPlayed: v?.gamesPlayed ?? 0,
    wins: v?.wins ?? 0,
    losses: v?.losses ?? 0,
    draws: v?.draws ?? 0,
    solvedPuzzleIds: v?.solvedPuzzleIds ?? [],
    completedAcademyIds: v?.completedAcademyIds ?? [],
    completedEndgameIds: v?.completedEndgameIds ?? [],
    preferredTheme: v?.preferredTheme ?? 'CHESS_VERDE',
    soundEnabled: v?.soundEnabled ?? true,
    savedGames: v?.savedGames ?? [],
    achievements: v?.achievements ?? [],
    totalBrilliants: v?.totalBrilliants ?? 0,
    totalBlunders: v?.totalBlunders ?? 0,
    longestWinStreak: v?.longestWinStreak ?? 0,
    currentWinStreak: v?.currentWinStreak ?? 0,
    openingsPlayed: v?.openingsPlayed ?? {},
    dailyPuzzleLastDate: v?.dailyPuzzleLastDate,
    dailyPuzzleSolved: v?.dailyPuzzleSolved ?? false,
    emotionalCheckIns: v?.emotionalCheckIns ?? [],
  };
}

interface ChessArenaTabProps {
  vault: VaultState;
  bioDayId: string;
  onUpdateVault: (updater: (prev: VaultState) => VaultState) => void;
}

type MainSubTab = 'JOGAR' | 'REVISAO' | 'PROBLEMAS' | 'TREINAR' | 'ANALISE';
type PuzzleMode = 'RANQUEADO' | 'DIARIO' | 'CORRIDA';
type TrainSubMode = 'VISAO' | 'FINAIS' | 'AULAS';

export const ChessArenaTab: React.FC<ChessArenaTabProps> = ({
  vault,
  bioDayId,
  onUpdateVault,
}) => {
  const chessData = useMemo(() => ensureChessVault(vault.chessState), [vault.chessState]);
  const [subTab, setSubTab] = useState<MainSubTab>('JOGAR');
  const [arrowDrawMode, setArrowDrawMode] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  const emitChessAudio = useCallback(
    (
      kind:
        | 'MOVE'
        | 'CAPTURE'
        | 'CHECK'
        | 'CASTLE'
        | 'PROMOTE'
        | 'GAME_END'
        | 'PUZZLE_OK'
        | 'ILLEGAL',
    ) => {
      if (chessData.soundEnabled) {
        playChessSound(kind);
      }
      if (kind === 'CHECK' || kind === 'GAME_END' || kind === 'PUZZLE_OK') {
        triggerHaptic('medium');
      } else {
        triggerHaptic('light');
      }
    },
    [chessData.soundEnabled],
  );

  const playSoundForVerboseMove = useCallback(
    (m: Move, afterGame: Chess) => {
      if (afterGame.isGameOver()) {
        emitChessAudio('GAME_END');
      } else if (afterGame.inCheck()) {
        emitChessAudio('CHECK');
      } else if (m.promotion) {
        emitChessAudio('PROMOTE');
      } else if (m.flags.includes('k') || m.flags.includes('q')) {
        emitChessAudio('CASTLE');
      } else if (m.captured) {
        emitChessAudio('CAPTURE');
      } else {
        emitChessAudio('MOVE');
      }
    },
    [emitChessAudio],
  );

  const showToast = (msg: string) => {
    setCopyFeedback(msg);
    window.setTimeout(() => setCopyFeedback(null), 2200);
  };

  // ==========================================================================
  // 1. ESTADO DO MODO JOGAR (CLASSICO + CHESS960 + POSICAO CUSTOM + 8 BOTS + 2P)
  // ==========================================================================
  const [playOpponentKind, setPlayOpponentKind] = useState<'BOT' | 'LOCAL_2P'>('BOT');
  const [playVariant, setPlayVariant] = useState<'CLASSICO' | 'CHESS960'>('CLASSICO');
  const [chess960Id, setChess960Id] = useState<number>(518);
  const [matchStartFen, setMatchStartFen] = useState<string>(STANDARD_START_FEN);
  const [activeEndgameDrill, setActiveEndgameDrill] =
    useState<EndgameDrillSpec | null>(null);
  const [showEndgameHint, setShowEndgameHint] = useState<boolean>(false);
  const lastSavedGameIdRef = useRef<string | null>(null);

  const [selectedBotId, setSelectedBotId] = useState<string>(CHESS_BOTS[1].id); // Sofia 800 default
  const [colorChoice, setColorChoice] = useState<'w' | 'b' | 'random'>('w');
  const [ratedMatch, setRatedMatch] = useState<boolean>(true);
  const [timeControlId, setTimeControlId] = useState<string>('rapid_10_0');

  const selectedBot: ChessBotProfile = useMemo(
    () => CHESS_BOTS.find((b) => b.id === selectedBotId) ?? CHESS_BOTS[1],
    [selectedBotId],
  );
  const selectedTimeControl: TimeControlPreset = useMemo(
    () => TIME_CONTROLS.find((t) => t.id === timeControlId) ?? TIME_CONTROLS[5],
    [timeControlId],
  );

  const [matchActive, setMatchActive] = useState<boolean>(false);
  const [gameSessionId, setGameSessionId] = useState<number>(0);
  const [userColor, setUserColor] = useState<Color>('w');
  const [boardOrientation, setBoardOrientation] = useState<Color>('w');
  const [playMovesVerbose, setPlayMovesVerbose] = useState<Move[]>([]);
  const [viewPlyIdx, setViewPlyIdx] = useState<number | null>(null); // null = ao vivo
  const [whiteClockMs, setWhiteClockMs] = useState<number>(600_000);
  const [blackClockMs, setBlackClockMs] = useState<number>(600_000);
  const whiteClockRef = useRef<number>(600_000);
  const blackClockRef = useRef<number>(600_000);
  const [premove, setPremove] = useState<{
    from: Square;
    to: Square;
    promotion?: PieceSymbol;
  } | null>(null);
  const [botQuote, setBotQuote] = useState<string>(CHESS_BOTS[1].quotes.greeting);
  const [botThinking, setBotThinking] = useState<boolean>(false);
  const [coachHint, setCoachHint] = useState<{
    from: Square;
    to: Square;
    comment: string;
  } | null>(null);
  const [resignConfirm, setResignConfirm] = useState<boolean>(false);
  const [gameOverBanner, setGameOverBanner] = useState<{
    result: 'VITORIA' | 'DERROTA' | 'EMPATE';
    headline: string;
    reason: string;
    eloDelta: number;
  } | null>(null);

  const liveGame = useMemo(() => {
    const g = new Chess(matchStartFen);
    for (const m of playMovesVerbose) {
      g.move({ from: m.from, to: m.to, promotion: m.promotion });
    }
    return g;
  }, [matchStartFen, playMovesVerbose]);

  const displayedPlayFen = useMemo(() => {
    if (viewPlyIdx === null) return liveGame.fen();
    if (viewPlyIdx < 0) return matchStartFen;
    return playMovesVerbose[viewPlyIdx]?.after ?? liveGame.fen();
  }, [viewPlyIdx, playMovesVerbose, liveGame, matchStartFen]);

  const displayedPlayChess = useMemo(
    () => new Chess(displayedPlayFen),
    [displayedPlayFen],
  );

  const playMaterial = useMemo(
    () => computeMaterialSummary(displayedPlayChess, matchStartFen),
    [displayedPlayChess, matchStartFen],
  );

  const playOpening = useMemo(() => {
    if (activeEndgameDrill) {
      return {
        eco: 'FINAL',
        namePt: activeEndgameDrill.titlePt,
        ideaPt: activeEndgameDrill.principleSummaryPt,
        matchedPlyCount: 0,
        isExactBookPosition: false,
        nextBookCandidates: [],
      };
    }
    if (matchStartFen !== STANDARD_START_FEN) {
      return {
        eco: playVariant === 'CHESS960' ? `960 #${chess960Id}` : 'FEN',
        namePt:
          playVariant === 'CHESS960'
            ? `Fischer Random Chess960 (#${chess960Id})`
            : 'Posição Personalizada',
        ideaPt: '',
        matchedPlyCount: 0,
        isExactBookPosition: false,
        nextBookCandidates: [],
      };
    }
    return detectOpeningFromMoves(playMovesVerbose.map((m) => m.san));
  }, [activeEndgameDrill, matchStartFen, playVariant, chess960Id, playMovesVerbose]);

  const liveAssistedEval = useMemo(() => {
    if (ratedMatch && matchActive) return { cp: 0, mate: null as number | null };
    const cp = evaluatePositionWhiteCp(displayedPlayChess);
    return {
      cp,
      mate: displayedPlayChess.isCheckmate()
        ? displayedPlayChess.turn() === 'w'
          ? -1
          : 1
        : null,
    };
  }, [ratedMatch, matchActive, displayedPlayChess]);

  // Finalizacao canonica FIDE + persistencia no Vault
  const finalizePlayMatch = useCallback(
    (
      outcomeWhite: 1 | 0.5 | 0,
      reasonPt: string,
      finalMoves: Move[],
    ) => {
      setMatchActive(false);
      setBotThinking(false);
      setPremove(null);
      setResignConfirm(false);

      const userScore: 1 | 0.5 | 0 =
        outcomeWhite === 0.5
          ? 0.5
          : (outcomeWhite === 1 && userColor === 'w') ||
              (outcomeWhite === 0 && userColor === 'b')
            ? 1
            : 0;

      const resultLabel: 'VITORIA' | 'DERROTA' | 'EMPATE' =
        userScore === 1 ? 'VITORIA' : userScore === 0 ? 'DERROTA' : 'EMPATE';

      const oppElo = playOpponentKind === 'BOT' ? selectedBot.elo : chessData.playRating;
      const isCustomNon960 =
        matchStartFen !== STANDARD_START_FEN && playVariant !== 'CHESS960';
      const isRated =
        playOpponentKind === 'BOT' &&
        ratedMatch &&
        !activeEndgameDrill &&
        !isCustomNon960;
      const delta = isRated
        ? computeEloDelta(chessData.playRating, oppElo, userScore)
        : 0;

      if (playOpponentKind === 'BOT') {
        setBotQuote(
          userScore === 1
            ? selectedBot.quotes.onDefeat
            : userScore === 0
              ? selectedBot.quotes.onVictory
              : 'Empate justo! Grande batalha estratégica.',
        );
      }

      const pgnChess = new Chess(matchStartFen);
      for (const mv of finalMoves) {
        pgnChess.move({ from: mv.from, to: mv.to, promotion: mv.promotion });
      }
      const op =
        matchStartFen === STANDARD_START_FEN
          ? detectOpeningFromMoves(finalMoves.map((m) => m.san))
          : {
              eco: activeEndgameDrill
                ? 'FINAL'
                : playVariant === 'CHESS960'
                  ? `960#${chess960Id}`
                  : 'FEN',
              namePt: activeEndgameDrill
                ? activeEndgameDrill.titlePt
                : playVariant === 'CHESS960'
                  ? `Chess960 Scharnagl #${chess960Id}`
                  : 'Posição Personalizada',
            };

      const drillSuccess = Boolean(
        activeEndgameDrill &&
          ((activeEndgameDrill.goalType === 'WIN' && resultLabel === 'VITORIA') ||
            (activeEndgameDrill.goalType === 'HOLD_DRAW' &&
              (resultLabel === 'EMPATE' || resultLabel === 'VITORIA'))),
      );

      const newGameId = `chess_${Date.now()}`;
      lastSavedGameIdRef.current = newGameId;

      const savedRecord: ChessSavedGame = {
        id: newGameId,
        bioDayId,
        timestampMs: Date.now(),
        opponentName:
          playOpponentKind === 'BOT' ? selectedBot.name : '2 Jogadores Local',
        opponentElo: oppElo,
        userColor,
        result: resultLabel,
        terminationReason: reasonPt,
        timeControlLabel: `${selectedTimeControl.category} ${selectedTimeControl.label}`,
        openingEco: op.eco,
        openingName: op.namePt,
        movesCount: Math.ceil(finalMoves.length / 2),
        pgn: pgnChess.pgn(),
        rated: isRated,
        ratingDelta: delta,
      };

      onUpdateVault((prev) => {
        const cur = ensureChessVault(prev.chessState);
        const prevEndgames = cur.completedEndgameIds ?? [];
        const nextEndgames =
          drillSuccess &&
          activeEndgameDrill &&
          !prevEndgames.includes(activeEndgameDrill.id)
            ? [...prevEndgames, activeEndgameDrill.id]
            : prevEndgames;

        // Sequência de vitórias
        let nextWinStreak = resultLabel === 'VITORIA' ? (cur.currentWinStreak ?? 0) + 1 : 0;
        let nextLongestStreak = Math.max(cur.longestWinStreak ?? 0, nextWinStreak);

        // Nova classificação ELO
        const nextRating = Math.max(100, cur.playRating + delta);
        const nextCategory = computeEloCategory(nextRating);

        // Contar abertura jogada (apenas partidas ranqueadas padrão)
        const nextOpenings = { ...(cur.openingsPlayed ?? {}) };
        if (isRated && op.eco && op.eco !== 'FINAL' && !op.eco.startsWith('960')) {
          const existing = nextOpenings[op.eco] ?? { played: 0, wins: 0, draws: 0, losses: 0 };
          nextOpenings[op.eco] = {
            played: existing.played + 1,
            wins: existing.wins + (resultLabel === 'VITORIA' ? 1 : 0),
            draws: existing.draws + (resultLabel === 'EMPATE' ? 1 : 0),
            losses: existing.losses + (resultLabel === 'DERROTA' ? 1 : 0),
          };
        }

        // Conquistas recém-desbloqueadas
        const previouslyUnlocked = new Set(cur.achievements ?? []);
        const newlyUnlocked = getUnlockedAchievements({
          ...cur,
          playRating: nextRating,
          wins: cur.wins + (resultLabel === 'VITORIA' ? 1 : 0),
          losses: cur.losses + (resultLabel === 'DERROTA' ? 1 : 0),
          draws: cur.draws + (resultLabel === 'EMPATE' ? 1 : 0),
          gamesPlayed: cur.gamesPlayed + 1,
          currentWinStreak: nextWinStreak,
          longestWinStreak: nextLongestStreak,
          savedGames: [savedRecord, ...cur.savedGames].slice(0, 25),
        });
        const nextAchievements = [...previouslyUnlocked];
        for (const achId of newlyUnlocked) {
          if (!previouslyUnlocked.has(achId)) {
            nextAchievements.push(achId);
          }
        }

        return {
          ...prev,
          chessState: {
            ...cur,
            playRating: nextRating,
            playEloCategory: nextCategory,
            gamesPlayed: cur.gamesPlayed + 1,
            wins: cur.wins + (resultLabel === 'VITORIA' ? 1 : 0),
            losses: cur.losses + (resultLabel === 'DERROTA' ? 1 : 0),
            draws: cur.draws + (resultLabel === 'EMPATE' ? 1 : 0),
            currentWinStreak: nextWinStreak,
            longestWinStreak: nextLongestStreak,
            achievements: nextAchievements,
            openingsPlayed: nextOpenings,
            completedEndgameIds: nextEndgames,
            savedGames: [savedRecord, ...cur.savedGames].slice(0, 25),
          },
        };
      });

      const headline = drillSuccess
        ? `🏆 Final Dominado! (${activeEndgameDrill?.titlePt})`
        : playOpponentKind === 'LOCAL_2P'
          ? outcomeWhite === 1
            ? 'Vitória das Brancas!'
            : outcomeWhite === 0
              ? 'Vitória das Pretas!'
              : 'Partida Empatada!'
          : resultLabel === 'VITORIA'
            ? 'Vitória Soberana!'
            : resultLabel === 'DERROTA'
              ? 'Vitória de ' + selectedBot.name
              : 'Empate Oficial FIDE';

      setGameOverBanner({
        result: resultLabel,
        headline,
        reason: reasonPt,
        eloDelta: delta,
      });
    },
    [
      userColor,
      playOpponentKind,
      selectedBot,
      chessData.playRating,
      ratedMatch,
      matchStartFen,
      playVariant,
      chess960Id,
      activeEndgameDrill,
      bioDayId,
      selectedTimeControl,
      onUpdateVault,
    ],
  );

  const checkAndHandleTerminal = useCallback(
    (afterChess: Chess, updatedMoves: Move[]): boolean => {
      if (afterChess.isCheckmate()) {
        const winnerWhite = afterChess.turn() === 'b' ? 1 : 0;
        finalizePlayMatch(winnerWhite, 'Xeque-mate', updatedMoves);
        return true;
      }
      if (afterChess.isStalemate()) {
        finalizePlayMatch(0.5, 'Empate por Afogamento (Rei sem lances legais)', updatedMoves);
        return true;
      }
      if (afterChess.isThreefoldRepetition()) {
        finalizePlayMatch(0.5, 'Empate por Tripla Repetição FIDE', updatedMoves);
        return true;
      }
      if (afterChess.isInsufficientMaterial()) {
        finalizePlayMatch(0.5, 'Empate por Material Insuficiente FIDE', updatedMoves);
        return true;
      }
      if (afterChess.isDrawByFiftyMoves()) {
        finalizePlayMatch(0.5, 'Empate pela Regra dos 50 Lances FIDE', updatedMoves);
        return true;
      }
      if (
        activeEndgameDrill &&
        activeEndgameDrill.goalType === 'HOLD_DRAW' &&
        updatedMoves.length >= activeEndgameDrill.maxTargetMoves * 2 &&
        Math.abs(evaluatePositionWhiteCp(afterChess)) < 400
      ) {
        finalizePlayMatch(
          0.5,
          `Fortaleza teórica sustentada por ${activeEndgameDrill.maxTargetMoves} lances contra 2400 Elo!`,
          updatedMoves,
        );
        return true;
      }
      return false;
    },
    [finalizePlayMatch, activeEndgameDrill],
  );

  const startNewPlayMatch = () => {
    const startFen =
      activeEndgameDrill
        ? activeEndgameDrill.fen
        : playVariant === 'CHESS960'
          ? generateChess960Position(chess960Id).fen
          : STANDARD_START_FEN;

    const chosenColor: Color = activeEndgameDrill
      ? activeEndgameDrill.userColor
      : colorChoice === 'random'
        ? Math.random() < 0.5
          ? 'w'
          : 'b'
        : colorChoice;

    setMatchStartFen(startFen);
    setUserColor(chosenColor);
    setBoardOrientation(chosenColor);
    setPlayMovesVerbose([]);
    setViewPlyIdx(null);
    setPremove(null);
    setCoachHint(null);
    setResignConfirm(false);
    setGameOverBanner(null);
    lastSavedGameIdRef.current = null;
    whiteClockRef.current = selectedTimeControl.initialMs;
    blackClockRef.current = selectedTimeControl.initialMs;
    setWhiteClockMs(selectedTimeControl.initialMs);
    setBlackClockMs(selectedTimeControl.initialMs);
    setBotQuote(selectedBot.quotes.greeting);
    setGameSessionId((s) => s + 1);
    setMatchActive(true);
    emitChessAudio('MOVE');
  };

  const launchPlayFromCustomFen = (targetFen: string, labelToast: string) => {
    const vf = validateFen(targetFen);
    if (!vf.ok) {
      showToast('Posição FEN inválida para iniciar partida.');
      return;
    }
    const probe = new Chess(targetFen);
    if (probe.isGameOver()) {
      showToast('Esta posição já está encerrada no tabuleiro.');
      return;
    }
    const sideToPlay = probe.turn();
    setPlayOpponentKind('BOT');
    setPlayVariant('CLASSICO');
    setActiveEndgameDrill(null);
    setShowEndgameHint(false);
    setRatedMatch(false);
    setTimeControlId('unlimited');
    setMatchStartFen(targetFen);
    setUserColor(sideToPlay);
    setBoardOrientation(sideToPlay);
    setPlayMovesVerbose([]);
    setViewPlyIdx(null);
    setPremove(null);
    setCoachHint(null);
    setResignConfirm(false);
    setGameOverBanner(null);
    lastSavedGameIdRef.current = null;
    whiteClockRef.current = 0;
    blackClockRef.current = 0;
    setWhiteClockMs(0);
    setBlackClockMs(0);
    setBotQuote(`Posição carregada! Você joga de ${sideToPlay === 'w' ? 'Brancas' : 'Pretas'}.`);
    setGameSessionId((s) => s + 1);
    setMatchActive(true);
    setSubTab('JOGAR');
    showToast(labelToast);
    emitChessAudio('MOVE');
  };

  const launchEndgameDrillMatch = (drill: EndgameDrillSpec) => {
    const gmBot = CHESS_BOTS[CHESS_BOTS.length - 1]; // 2400 Elo defesa tenaz
    setPlayOpponentKind('BOT');
    setSelectedBotId(gmBot.id);
    setPlayVariant('CLASSICO');
    setActiveEndgameDrill(drill);
    setShowEndgameHint(false);
    setRatedMatch(false);
    setTimeControlId('unlimited');
    setMatchStartFen(drill.fen);
    setUserColor(drill.userColor);
    setBoardOrientation(drill.userColor);
    setPlayMovesVerbose([]);
    setViewPlyIdx(null);
    setPremove(null);
    setCoachHint(null);
    setResignConfirm(false);
    setGameOverBanner(null);
    lastSavedGameIdRef.current = null;
    whiteClockRef.current = 0;
    blackClockRef.current = 0;
    setWhiteClockMs(0);
    setBlackClockMs(0);
    setBotQuote(
      drill.goalType === 'WIN'
        ? `Desafio Técnico: converta este final vencido contra minha defesa máxima!`
        : `Desafio de Fortaleza: segure o empate preciso contra minha pressão!`,
    );
    setGameSessionId((s) => s + 1);
    setMatchActive(true);
    setSubTab('JOGAR');
    emitChessAudio('MOVE');
  };

  // Relogio Digital Fischer FIDE (tick livre de efeitos colaterais em setState + Art. 6.9 FIDE!)
  useEffect(() => {
    if (!matchActive || selectedTimeControl.initialMs <= 0) return;
    let lastTick = performance.now();

    const timer = window.setInterval(() => {
      const now = performance.now();
      const dt = now - lastTick;
      lastTick = now;

      const activeTurn = liveGame.turn();
      if (activeTurn === 'w') {
        const next = Math.max(0, whiteClockRef.current - dt);
        whiteClockRef.current = next;
        setWhiteClockMs(next);
        if (next <= 0) {
          window.clearInterval(timer);
          const blackCanMate = sideHasMatingMaterial(liveGame, 'b');
          if (blackCanMate) {
            finalizePlayMatch(0, 'Queda de Seta (Tempo esgotado das Brancas)', playMovesVerbose);
          } else {
            finalizePlayMatch(
              0.5,
              'Empate FIDE Art. 6.9 (Tempo esgotado contra Material Insuficiente)',
              playMovesVerbose,
            );
          }
          emitChessAudio('GAME_END');
        }
      } else {
        const next = Math.max(0, blackClockRef.current - dt);
        blackClockRef.current = next;
        setBlackClockMs(next);
        if (next <= 0) {
          window.clearInterval(timer);
          const whiteCanMate = sideHasMatingMaterial(liveGame, 'w');
          if (whiteCanMate) {
            finalizePlayMatch(1, 'Queda de Seta (Tempo esgotado das Pretas)', playMovesVerbose);
          } else {
            finalizePlayMatch(
              0.5,
              'Empate FIDE Art. 6.9 (Tempo esgotado contra Material Insuficiente)',
              playMovesVerbose,
            );
          }
          emitChessAudio('GAME_END');
        }
      }
    }, 100);

    return () => window.clearInterval(timer);
  }, [
    matchActive,
    gameSessionId,
    selectedTimeControl.initialMs,
    liveGame,
    playMovesVerbose,
    finalizePlayMatch,
    emitChessAudio,
  ]);

  const executePlayMove = useCallback(
    (from: Square, to: Square, promotion?: PieceSymbol): boolean => {
      if (!matchActive) return false;
      // Reconstrói histórico completo desde matchStartFen para deteccao exata de tripla repeticao!
      const fullGame = new Chess(matchStartFen);
      for (const mv of playMovesVerbose) {
        fullGame.move({ from: mv.from, to: mv.to, promotion: mv.promotion });
      }
      let moved: Move | null = null;
      try {
        moved = fullGame.move({ from, to, promotion });
      } catch {
        moved = null;
      }
      if (!moved) {
        emitChessAudio('ILLEGAL');
        return false;
      }

      // Acréscimo Fischer ao jogador que acabou de jogar
      if (selectedTimeControl.initialMs > 0 && selectedTimeControl.incrementMs > 0) {
        if (moved.color === 'w') {
          whiteClockRef.current += selectedTimeControl.incrementMs;
          setWhiteClockMs(whiteClockRef.current);
        } else {
          blackClockRef.current += selectedTimeControl.incrementMs;
          setBlackClockMs(blackClockRef.current);
        }
      }

      const nextMoves = [...playMovesVerbose, moved];
      setPlayMovesVerbose(nextMoves);
      setViewPlyIdx(null);
      setCoachHint(null);
      playSoundForVerboseMove(moved, fullGame);

      checkAndHandleTerminal(fullGame, nextMoves);
      return true;
    },
    [
      matchActive,
      matchStartFen,
      playMovesVerbose,
      selectedTimeControl,
      playSoundForVerboseMove,
      checkAndHandleTerminal,
      emitChessAudio,
    ],
  );

  // Turno automatico do Bot + execucao automatica de Pre-Lance do usuario!
  useEffect(() => {
    if (!matchActive || playOpponentKind !== 'BOT') return;
    const turn = liveGame.turn();

    // Se voltou a ser a vez do usuario e existe Pre-Lance engatilhado, dispara imediatamente!
    if (turn === userColor && premove) {
      const pm = premove;
      setPremove(null);
      executePlayMove(pm.from, pm.to, pm.promotion);
      return;
    }

    if (turn === userColor) return;

    setBotThinking(true);
    const thinkDelay = Math.min(480, Math.max(180, selectedBot.timeBudgetMs));
    const handle = window.setTimeout(() => {
      const sanHist = playMovesVerbose.map((m) => m.san);
      const choice = chooseBotMove(liveGame.fen(), selectedBot, sanHist);
      setBotThinking(false);
      if (!choice) return;

      const fullGame = new Chess(matchStartFen);
      for (const mv of playMovesVerbose) {
        fullGame.move({ from: mv.from, to: mv.to, promotion: mv.promotion });
      }
      let moved: Move | null = null;
      try {
        moved = fullGame.move({
          from: choice.from,
          to: choice.to,
          promotion: choice.promotion,
        });
      } catch {
        moved = null;
      }
      if (!moved) return;

      if (selectedTimeControl.initialMs > 0 && selectedTimeControl.incrementMs > 0) {
        if (moved.color === 'w') {
          whiteClockRef.current += selectedTimeControl.incrementMs;
          setWhiteClockMs(whiteClockRef.current);
        } else {
          blackClockRef.current += selectedTimeControl.incrementMs;
          setBlackClockMs(blackClockRef.current);
        }
      }

      if (fullGame.inCheck()) {
        setBotQuote(selectedBot.quotes.onCheck);
      } else if (moved.captured) {
        setBotQuote(selectedBot.quotes.onCapture);
      } else if (choice.isBook) {
        const op = detectOpeningFromMoves([...sanHist, moved.san]);
        setBotQuote(`Teoria clássica: ${op.namePt} (${op.eco}).`);
      }

      const nextMoves = [...playMovesVerbose, moved];
      setPlayMovesVerbose(nextMoves);
      setViewPlyIdx(null);
      playSoundForVerboseMove(moved, fullGame);
      checkAndHandleTerminal(fullGame, nextMoves);
    }, thinkDelay);

    return () => window.clearTimeout(handle);
  }, [
    matchActive,
    gameSessionId,
    playOpponentKind,
    matchStartFen,
    liveGame,
    userColor,
    premove,
    selectedBot,
    playMovesVerbose,
    selectedTimeControl,
    executePlayMove,
    playSoundForVerboseMove,
    checkAndHandleTerminal,
  ]);

  const handleOfferDraw = () => {
    if (!matchActive) return;
    if (playOpponentKind === 'LOCAL_2P') {
      finalizePlayMatch(0.5, 'Empate por Acordo Mútuo', playMovesVerbose);
      emitChessAudio('GAME_END');
      return;
    }
    if (playMovesVerbose.length < 16) {
      setBotQuote('Ainda estamos no começo da batalha! Vamos jogar mais alguns lances.');
      showToast(`${selectedBot.name} recusou o empate (muito cedo).`);
      return;
    }
    const botSign = userColor === 'w' ? -1 : 1;
    const botAdvCp = evaluatePositionWhiteCp(liveGame) * botSign;
    if (botAdvCp <= 35 && Math.abs(botAdvCp) <= 95) {
      finalizePlayMatch(0.5, 'Empate por Acordo Mútuo', playMovesVerbose);
      emitChessAudio('GAME_END');
    } else {
      setBotQuote(
        botAdvCp > 35
          ? 'Minha posição é promissora — vou continuar pressionando!'
          : 'Ainda há recursos táticos na posição — siga jogando!',
      );
      showToast(`${selectedBot.name} recusou a proposta de empate.`);
    }
  };

  const handleRequestCoachHint = () => {
    if (!matchActive || ratedMatch) return;
    const lines = analyzePositionMultiPv(liveGame.fen(), {
      maxDepth: 3,
      timeBudgetMs: 260,
      multiPv: 1,
    });
    if (lines[0]) {
      setCoachHint({
        from: lines[0].from,
        to: lines[0].to,
        comment: explainMoveCoachPt(liveGame.fen(), lines[0]),
      });
    }
  };

  const handleUndoMoveAssisted = () => {
    if (!matchActive || ratedMatch || playMovesVerbose.length === 0) return;
    const popCount =
      playOpponentKind === 'BOT' && playMovesVerbose.length >= 2 ? 2 : 1;
    setPlayMovesVerbose((prev) => prev.slice(0, prev.length - popCount));
    setViewPlyIdx(null);
    setCoachHint(null);
  };

  // ==========================================================================
  // 2. ESTADO DO MODO REVISAO DE PARTIDA (CAPS % + 9 SELOS + GRAFICO + RETRY)
  // ==========================================================================
  const [reviewReport, setReviewReport] = useState<FullGameReviewReport | null>(null);
  const [reviewPlyIdx, setReviewPlyIdx] = useState<number>(0);
  const [retryState, setRetryState] = useState<{
    active: boolean;
    solved: boolean;
    message: string;
  } | null>(null);

  const launchGameReviewFromMoves = useCallback(
    (moves: Move[], savedGameId?: string | null, savedUserColor?: Color) => {
      if (moves.length === 0) return;
      const report = runFullGameReview(moves);
      setReviewReport(report);
      setReviewPlyIdx(0);
      setRetryState(null);
      setSubTab('REVISAO');

      const targetId =
        savedGameId === undefined ? lastSavedGameIdRef.current : savedGameId;
      const side = savedUserColor ?? userColor;
      if (targetId) {
        const acc =
          side === 'w' ? report.whiteAccuracyPct : report.blackAccuracyPct;
        const counts =
          side === 'w' ? report.countsWhite : report.countsBlack;
        onUpdateVault((prev) => {
          const cur = ensureChessVault(prev.chessState);
          return {
            ...prev,
            chessState: {
              ...cur,
              savedGames: cur.savedGames.map((g) =>
                g.id === targetId
                  ? {
                      ...g,
                      userAccuracyPct: acc,
                      brilliantCount: counts.BRILHANTE,
                      blunderCount: counts.CAPIVARADA,
                    }
                  : g,
              ),
            },
          };
        });
      }
    },
    [userColor, onUpdateVault],
  );

  const launchReviewFromSavedGame = (sg: ChessSavedGame) => {
    try {
      const c = new Chess();
      c.loadPgn(sg.pgn);
      const hist = c.history({ verbose: true });
      if (hist.length > 0) {
        setBoardOrientation(sg.userColor);
        launchGameReviewFromMoves(hist, sg.id, sg.userColor);
      }
    } catch {
      showToast('Não foi possível carregar o PGN selecionado.');
    }
  };

  const loadOperaImmortalForReview = () => {
    const c = new Chess();
    for (const san of OPERA_GAME_SAN) c.move(san);
    launchGameReviewFromMoves(c.history({ verbose: true }), null);
  };

  const activeReviewedMove = useMemo(() => {
    if (!reviewReport || reviewReport.moves.length === 0) return null;
    const clamped = Math.max(0, Math.min(reviewReport.moves.length - 1, reviewPlyIdx));
    return reviewReport.moves[clamped];
  }, [reviewReport, reviewPlyIdx]);

  const reviewBoardFen = useMemo(() => {
    if (!activeReviewedMove) return new Chess().fen();
    if (retryState?.active && !retryState.solved) {
      return activeReviewedMove.fenBefore;
    }
    return activeReviewedMove.fenAfter;
  }, [activeReviewedMove, retryState]);

  const reviewArrows = useMemo<BoardArrowSpec[]>(() => {
    if (!activeReviewedMove) return [];
    if (retryState?.active && !retryState.solved) return [];
    const arrows: BoardArrowSpec[] = [];
    if (
      activeReviewedMove.bestFrom !== activeReviewedMove.playedFrom ||
      activeReviewedMove.bestTo !== activeReviewedMove.playedTo
    ) {
      arrows.push({
        from: activeReviewedMove.bestFrom,
        to: activeReviewedMove.bestTo,
        color: '#81b64c',
        opacity: 0.9,
      });
    }
    if (
      activeReviewedMove.classification === 'IMPRECISAO' ||
      activeReviewedMove.classification === 'ERRO' ||
      activeReviewedMove.classification === 'CAPIVARADA'
    ) {
      arrows.push({
        from: activeReviewedMove.playedFrom,
        to: activeReviewedMove.playedTo,
        color: '#fa412d',
        opacity: 0.72,
      });
    }
    return arrows;
  }, [activeReviewedMove, retryState]);

  const reviewBadgeOverlay = useMemo<SquareBadgeOverlay | null>(() => {
    if (!activeReviewedMove || (retryState?.active && !retryState.solved)) {
      return null;
    }
    const meta = MOVE_BADGES[activeReviewedMove.classification];
    return {
      square: activeReviewedMove.playedTo,
      symbol: meta.symbol,
      bgColor: meta.colorHex,
    };
  }, [activeReviewedMove, retryState]);

  // ==========================================================================
  // 3. ESTADO DO MODO PROBLEMAS TATICOS + DIARIO + PUZZLE RUSH (3 MIN / 3 VIDAS)
  // ==========================================================================
  const [puzzleMode, setPuzzleMode] = useState<PuzzleMode>('RANQUEADO');
  const [activePuzzle, setActivePuzzle] = useState<ChessPuzzleSpec>(() =>
    pickNextRatedPuzzle(chessData.puzzleRating, chessData.solvedPuzzleIds),
  );
  const [puzzleChessFen, setPuzzleChessFen] = useState<string>(() => activePuzzle.fen);
  const [puzzleStepIdx, setPuzzleStepIdx] = useState<number>(0);
  const [puzzleStatus, setPuzzleStatus] = useState<
    'SOLVING' | 'SOLVED' | 'FAILED'
  >('SOLVING');
  const [puzzleHintSq, setPuzzleHintSq] = useState<{
    from: Square;
    to: Square;
  } | null>(null);
  const [puzzleLastMove, setPuzzleLastMove] = useState<{
    from: Square;
    to: Square;
  } | null>(null);
  const [puzzleEloChange, setPuzzleEloChange] = useState<number | null>(null);

  // Estado Puzzle Rush (Corrida de Problemas: 3 minutos / 3 erros)
  const [rushActive, setRushActive] = useState<boolean>(false);
  const [rushTimeLeftMs, setRushTimeLeftMs] = useState<number>(180_000);
  const rushDeadlineRef = useRef<number>(0);
  const puzzleTimerRef = useRef<number | null>(null);
  const [rushScore, setRushScore] = useState<number>(0);
  const [rushStrikes, setRushStrikes] = useState<number>(0);
  const [rushQueueIdx, setRushQueueIdx] = useState<number>(0);
  const rushSortedCatalog = useMemo(
    () => [...CHESS_PUZZLES_CATALOG].sort((a, b) => a.rating - b.rating),
    [],
  );

  const loadPuzzleSpec = useCallback((spec: ChessPuzzleSpec) => {
    if (puzzleTimerRef.current !== null) {
      window.clearTimeout(puzzleTimerRef.current);
      puzzleTimerRef.current = null;
    }
    setActivePuzzle(spec);
    setPuzzleChessFen(spec.fen);
    setPuzzleStepIdx(0);
    setPuzzleStatus('SOLVING');
    setPuzzleHintSq(null);
    setPuzzleLastMove(null);
    setPuzzleEloChange(null);
  }, []);

  useEffect(() => {
    return () => {
      if (puzzleTimerRef.current !== null) {
        window.clearTimeout(puzzleTimerRef.current);
      }
    };
  }, []);

  const puzzleOrientation: Color = useMemo(() => {
    const c = new Chess(activePuzzle.fen);
    return c.turn();
  }, [activePuzzle]);

  const finishPuzzleRush = useCallback(
    (finalScore: number) => {
      setRushActive(false);
      emitChessAudio('GAME_END');
      onUpdateVault((prev) => {
        const cur = ensureChessVault(prev.chessState);
        return {
          ...prev,
          chessState: {
            ...cur,
            puzzleRushBest: Math.max(cur.puzzleRushBest, finalScore),
          },
        };
      });
    },
    [emitChessAudio, onUpdateVault],
  );

  useEffect(() => {
    if (!rushActive) return;
    const id = window.setInterval(() => {
      const rem = Math.max(0, rushDeadlineRef.current - performance.now());
      setRushTimeLeftMs(rem);
      if (rem <= 0) {
        window.clearInterval(id);
        setPuzzleStatus('FAILED');
        finishPuzzleRush(rushScore);
      }
    }, 100);
    return () => window.clearInterval(id);
  }, [rushActive, rushScore, finishPuzzleRush]);

  const startPuzzleRush = () => {
    setPuzzleMode('CORRIDA');
    setRushScore(0);
    setRushStrikes(0);
    setRushQueueIdx(0);
    rushDeadlineRef.current = performance.now() + 180_000;
    setRushTimeLeftMs(180_000);
    setRushActive(true);
    loadPuzzleSpec(rushSortedCatalog[0]);
  };

  const handlePuzzleUserMove = (
    from: Square,
    to: Square,
    promotion?: PieceSymbol,
  ): boolean => {
    if (puzzleStatus !== 'SOLVING') return false;
    const g = new Chess(puzzleChessFen);
    let moved: Move | null = null;
    try {
      moved = g.move({ from, to, promotion });
    } catch {
      moved = null;
    }
    if (!moved) return false;

    const expectedLan = activePuzzle.solutionLan[puzzleStepIdx];
    const isCorrect = moved.lan === expectedLan || g.isCheckmate();

    if (!isCorrect) {
      emitChessAudio('ILLEGAL');
      if (puzzleMode === 'CORRIDA' && rushActive) {
        const nextStrikes = rushStrikes + 1;
        setRushStrikes(nextStrikes);
        if (nextStrikes >= 3) {
          setPuzzleStatus('FAILED');
          finishPuzzleRush(rushScore);
        } else {
          const nextIdx = (rushQueueIdx + 1) % rushSortedCatalog.length;
          setRushQueueIdx(nextIdx);
          loadPuzzleSpec(rushSortedCatalog[nextIdx]);
        }
        return false;
      }

      // Modo Ranqueado / Diario: penaliza rating uma vez ao errar
      if (puzzleEloChange === null && puzzleMode === 'RANQUEADO') {
        const delta = computeEloDelta(
          chessData.puzzleRating,
          activePuzzle.rating,
          0,
          28,
        );
        setPuzzleEloChange(delta);
        onUpdateVault((prev) => {
          const cur = ensureChessVault(prev.chessState);
          return {
            ...prev,
            chessState: {
              ...cur,
              puzzleRating: Math.max(100, cur.puzzleRating + delta),
            },
          };
        });
      }
      setPuzzleStatus('FAILED');
      return false;
    }

    // Lance tatico EXATO!
    setPuzzleChessFen(g.fen());
    setPuzzleLastMove({ from: moved.from, to: moved.to });
    setPuzzleHintSq(null);

    const nextIdxAfterUser = puzzleStepIdx + 1;
    if (nextIdxAfterUser >= activePuzzle.solutionLan.length || g.isCheckmate()) {
      emitChessAudio('PUZZLE_OK');
      setPuzzleStatus('SOLVED');

      if (puzzleMode === 'CORRIDA' && rushActive) {
        const newScore = rushScore + 1;
        setRushScore(newScore);
        onUpdateVault((prev) => {
          const cur = ensureChessVault(prev.chessState);
          const mergedSolved = cur.solvedPuzzleIds.includes(activePuzzle.id)
            ? cur.solvedPuzzleIds
            : [...cur.solvedPuzzleIds, activePuzzle.id];
          return {
            ...prev,
            chessState: {
              ...cur,
              solvedPuzzleIds: mergedSolved,
              puzzleRushBest: Math.max(cur.puzzleRushBest, newScore),
            },
          };
        });
        puzzleTimerRef.current = window.setTimeout(() => {
          const nextQ = (rushQueueIdx + 1) % rushSortedCatalog.length;
          setRushQueueIdx(nextQ);
          loadPuzzleSpec(rushSortedCatalog[nextQ]);
        }, 480);
      } else {
        const delta =
          puzzleEloChange === null
            ? Math.max(
                4,
                computeEloDelta(chessData.puzzleRating, activePuzzle.rating, 1, 28),
              )
            : 0;
        if (puzzleEloChange === null) setPuzzleEloChange(delta);

        onUpdateVault((prev) => {
          const cur = ensureChessVault(prev.chessState);
          const mergedSolved = cur.solvedPuzzleIds.includes(activePuzzle.id)
            ? cur.solvedPuzzleIds
            : [...cur.solvedPuzzleIds, activePuzzle.id];
          return {
            ...prev,
            chessState: {
              ...cur,
              puzzleRating: cur.puzzleRating + delta,
              solvedPuzzleIds: mergedSolved,
            },
          };
        });
      }
      return true;
    }

    playSoundForVerboseMove(moved, g);
    setPuzzleStepIdx(nextIdxAfterUser);

    // Resposta automatica do oponente no problema multi-lance!
    const oppLan = activePuzzle.solutionLan[nextIdxAfterUser];
    puzzleTimerRef.current = window.setTimeout(() => {
      const g2 = new Chess(g.fen());
      const oppFrom = oppLan.slice(0, 2) as Square;
      const oppTo = oppLan.slice(2, 4) as Square;
      const oppPromo = oppLan[4] as PieceSymbol | undefined;
      const oppMove = g2.move({ from: oppFrom, to: oppTo, promotion: oppPromo });
      if (oppMove) {
        setPuzzleChessFen(g2.fen());
        setPuzzleLastMove({ from: oppMove.from, to: oppMove.to });
        setPuzzleStepIdx(nextIdxAfterUser + 1);
        playSoundForVerboseMove(oppMove, g2);
      }
    }, 320);

    return true;
  };

  // ==========================================================================
  // 3.5 ESTADO DO MODO TREINAR (VISAO 30S + 8 FINAIS + 6 AULAS INTERATIVAS)
  // ==========================================================================
  const [trainMode, setTrainMode] = useState<TrainSubMode>('VISAO');

  // --- A) Visao de Coordenadas 30s (Estilo Chess.com Vision) ---
  const [visionActive, setVisionActive] = useState<boolean>(false);
  const [visionTimeLeftMs, setVisionTimeLeftMs] = useState<number>(30_000);
  const visionDeadlineRef = useRef<number>(0);
  const visionScoreRef = useRef<number>(0);
  const [visionScore, setVisionScore] = useState<number>(0);
  const [visionMisses, setVisionMisses] = useState<number>(0);
  const [visionTargetSq, setVisionTargetSq] = useState<Square>('e4');
  const [visionPerspective, setVisionPerspective] = useState<'w' | 'b' | 'mixed'>('w');
  const [visionBoardSide, setVisionBoardSide] = useState<Color>('w');
  const [visionShowPieces, setVisionShowPieces] = useState<boolean>(false);
  const [visionHideCoords, setVisionHideCoords] = useState<boolean>(false);
  const [visionFeedback, setVisionFeedback] = useState<{
    sq: Square;
    ok: boolean;
  } | null>(null);

  const pickRandomVisionTarget = useCallback(
    (excludeSq?: Square) => {
      const pool = ALL_64_SQUARES.filter((s) => s !== excludeSq);
      const next = pool[Math.floor(Math.random() * pool.length)];
      setVisionTargetSq(next);
      if (visionPerspective === 'mixed') {
        setVisionBoardSide(Math.random() < 0.5 ? 'w' : 'b');
      } else {
        setVisionBoardSide(visionPerspective);
      }
    },
    [visionPerspective],
  );

  const finishVisionDrill = useCallback(
    (finalScore: number) => {
      setVisionActive(false);
      emitChessAudio('GAME_END');
      onUpdateVault((prev) => {
        const cur = ensureChessVault(prev.chessState);
        return {
          ...prev,
          chessState: {
            ...cur,
            visionBestScore: Math.max(cur.visionBestScore ?? 0, finalScore),
          },
        };
      });
    },
    [emitChessAudio, onUpdateVault],
  );

  useEffect(() => {
    if (!visionActive) return;
    const id = window.setInterval(() => {
      const rem = Math.max(0, visionDeadlineRef.current - performance.now());
      setVisionTimeLeftMs(rem);
      if (rem <= 0) {
        window.clearInterval(id);
        finishVisionDrill(visionScoreRef.current);
      }
    }, 80);
    return () => window.clearInterval(id);
  }, [visionActive, finishVisionDrill]);

  const startVisionDrill = () => {
    visionScoreRef.current = 0;
    setVisionScore(0);
    setVisionMisses(0);
    setVisionFeedback(null);
    visionDeadlineRef.current = performance.now() + 30_000;
    setVisionTimeLeftMs(30_000);
    pickRandomVisionTarget();
    setVisionActive(true);
    emitChessAudio('MOVE');
  };

  const handleVisionSquareTap = (sq: Square) => {
    if (!visionActive) return;
    if (sq === visionTargetSq) {
      const next = visionScoreRef.current + 1;
      visionScoreRef.current = next;
      setVisionScore(next);
      setVisionFeedback({ sq, ok: true });
      emitChessAudio('PUZZLE_OK');
      pickRandomVisionTarget(sq);
    } else {
      setVisionMisses((m) => m + 1);
      setVisionFeedback({ sq, ok: false });
      emitChessAudio('ILLEGAL');
    }
  };

  // --- B) Academia Interativa de Xadrez (6 Aulas Passo a Passo) ---
  const [activeLesson, setActiveLesson] = useState<InteractiveChessLesson>(
    CHESS_ACADEMY_LESSONS[0],
  );
  const [lessonStepIdx, setLessonStepIdx] = useState<number>(0);
  const [lessonStepSolved, setLessonStepSolved] = useState<boolean>(false);
  const [lessonBoardFen, setLessonBoardFen] = useState<string>(
    CHESS_ACADEMY_LESSONS[0].steps[0].fen,
  );
  const [lessonCoachMsg, setLessonCoachMsg] = useState<string>(
    CHESS_ACADEMY_LESSONS[0].steps[0].instructionPt,
  );
  const [lessonHintSq, setLessonHintSq] = useState<{
    from: Square;
    to: Square;
  } | null>(null);

  const selectAcademyLesson = (lesson: InteractiveChessLesson) => {
    setActiveLesson(lesson);
    setLessonStepIdx(0);
    setLessonStepSolved(false);
    setLessonBoardFen(lesson.steps[0].fen);
    setLessonCoachMsg(lesson.steps[0].instructionPt);
    setLessonHintSq(null);
  };

  const handleAcademyMove = (
    from: Square,
    to: Square,
    promotion?: PieceSymbol,
  ): boolean => {
    if (lessonStepSolved) return false;
    const step = activeLesson.steps[lessonStepIdx];
    if (!step) return false;
    const g = new Chess(step.fen);
    let m: Move | null = null;
    try {
      m = g.move({ from, to, promotion });
    } catch {
      m = null;
    }
    if (!m) return false;

    if (!step.expectedLan.includes(m.lan)) {
      emitChessAudio('ILLEGAL');
      setLessonCoachMsg(
        `${m.san} não aplica o princípio pedido neste passo — releia a instrução acima ou peça uma dica!`,
      );
      return false;
    }

    setLessonBoardFen(g.fen());
    setLessonStepSolved(true);
    setLessonHintSq(null);
    setLessonCoachMsg(`✅ ${step.successCoachPt}`);
    emitChessAudio('PUZZLE_OK');

    // Se concluiu o ultimo passo da aula, registra no Cofre!
    if (lessonStepIdx >= activeLesson.steps.length - 1) {
      onUpdateVault((prev) => {
        const cur = ensureChessVault(prev.chessState);
        const done = cur.completedAcademyIds ?? [];
        if (done.includes(activeLesson.id)) return prev;
        return {
          ...prev,
          chessState: {
            ...cur,
            completedAcademyIds: [...done, activeLesson.id],
          },
        };
      });
    }
    return true;
  };

  // ==========================================================================
  // 4. ESTADO DO MODO EXPLORADOR ECO & ANALISE MULTI-PV + IMPORT/EXPORT PGN/FEN
  // ==========================================================================
  const [analysisRootFen, setAnalysisRootFen] = useState<string>(new Chess().fen());
  const [analysisMoves, setAnalysisMoves] = useState<Move[]>([]);
  const [analysisOrientation, setAnalysisOrientation] = useState<Color>('w');
  const [openingFilter, setOpeningFilter] = useState<string>('');
  const [importText, setImportText] = useState<string>('');
  const [showImportBox, setShowImportBox] = useState<boolean>(false);

  const analysisChess = useMemo(() => {
    const g = new Chess(analysisRootFen);
    for (const m of analysisMoves) {
      g.move({ from: m.from, to: m.to, promotion: m.promotion });
    }
    return g;
  }, [analysisRootFen, analysisMoves]);

  const analysisFen = analysisChess.fen();

  const multiPvLines = useMemo<EngineSearchLine[]>(() => {
    if (subTab !== 'ANALISE') return [];
    if (analysisChess.isGameOver()) return [];
    return analyzePositionMultiPv(analysisFen, {
      maxDepth: 3,
      timeBudgetMs: 220,
      multiPv: 3,
    });
  }, [subTab, analysisChess, analysisFen]);

  const analysisOpening = useMemo(() => {
    if (analysisRootFen !== new Chess().fen()) {
      return {
        eco: 'FEN',
        namePt: 'Posição Personalizada FEN',
        ideaPt: 'Analise as 3 melhores linhas do motor abaixo.',
        matchedPlyCount: 0,
        isExactBookPosition: false,
        nextBookCandidates: [],
      };
    }
    return detectOpeningFromMoves(analysisMoves.map((m) => m.san));
  }, [analysisRootFen, analysisMoves]);

  const analysisArrows = useMemo<BoardArrowSpec[]>(() => {
    const colors = ['#81b64c', '#3b82f6', '#a855f7'];
    return multiPvLines.map((l, idx) => ({
      from: l.from,
      to: l.to,
      color: colors[idx] ?? '#81b64c',
      opacity: idx === 0 ? 0.88 : 0.55,
    }));
  }, [multiPvLines]);

  const handleAnalysisMove = (
    from: Square,
    to: Square,
    promotion?: PieceSymbol,
  ): boolean => {
    const g = new Chess(analysisFen);
    let m: Move | null = null;
    try {
      m = g.move({ from, to, promotion });
    } catch {
      m = null;
    }
    if (!m) return false;
    setAnalysisMoves((prev) => [...prev, m!]);
    playSoundForVerboseMove(m, g);
    return true;
  };

  const handleImportFenOrPgn = () => {
    const raw = importText.trim();
    if (!raw) return;
    const vf = validateFen(raw);
    if (vf.ok) {
      setAnalysisRootFen(raw);
      setAnalysisMoves([]);
      setShowImportBox(false);
      setImportText('');
      showToast('Posição FEN carregada com sucesso!');
      return;
    }
    try {
      const c = new Chess();
      c.loadPgn(raw);
      const hist = c.history({ verbose: true });
      const headerFen = c.getHeaders().FEN;
      setAnalysisRootFen(hist[0]?.before ?? headerFen ?? STANDARD_START_FEN);
      setAnalysisMoves(hist);
      setShowImportBox(false);
      setImportText('');
      showToast('Partida PGN importada com sucesso!');
    } catch {
      showToast('Formato FEN ou PGN inválido — verifique a notação.');
    }
  };

  // ==========================================================================
  // COMPONENTES VISUAIS AUXILIARES (BARRA DE JOGADOR + CAPTURAS + RELOGIO)
  // ==========================================================================
  const renderPlayerBar = (side: Color) => {
    const isBotSide = playOpponentKind === 'BOT' && side !== userColor;
    const name = isBotSide
      ? `${selectedBot.avatarCode} ${selectedBot.name}`
      : playOpponentKind === 'LOCAL_2P'
        ? side === 'w'
          ? '♔ Jogador Brancas'
          : '♚ Jogador Pretas'
        : `🛡️ Você (FORJA)`;
    const elo = isBotSide ? selectedBot.elo : chessData.playRating;
    const captured =
      side === 'w'
        ? playMaterial.capturedByWhite
        : playMaterial.capturedByBlack;
    const oppColor: Color = side === 'w' ? 'b' : 'w';
    const netAdv =
      side === 'w'
        ? playMaterial.whiteAdvantagePts
        : -playMaterial.whiteAdvantagePts;
    const clockMs = side === 'w' ? whiteClockMs : blackClockMs;
    const isTurnActive = matchActive && liveGame.turn() === side;
    const isLowTime =
      selectedTimeControl.initialMs > 0 && clockMs > 0 && clockMs < 20_000;

    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '7px 10px',
          borderRadius: '10px',
          background: isTurnActive
            ? 'rgba(129, 182, 76, 0.14)'
            : 'rgba(255, 255, 255, 0.04)',
          border: isTurnActive
            ? '1px solid rgba(129, 182, 76, 0.55)'
            : '1px solid rgba(255, 255, 255, 0.09)',
          maxWidth: '470px',
          margin: '0 auto',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc' }}>
              {name}
            </span>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '1px 6px',
                borderRadius: '999px',
                background: 'rgba(255,255,255,0.1)',
                color: '#cbd5e1',
              }}
            >
              {elo}
            </span>
            {isBotSide && botThinking && (
              <span style={{ fontSize: '10px', color: '#81b64c', fontWeight: 700 }}>
                • calculando...
              </span>
            )}
          </div>
          {/* Pecas Capturadas + Saldo Material (+3, +5...) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '2px', minHeight: '16px' }}>
            {captured.map((p, idx) => (
              <div key={`${p}-${idx}`} style={{ width: '14px', height: '14px' }}>
                <ChessPieceSvg color={oppColor} type={p} />
              </div>
            ))}
            {netAdv > 0 && (
              <span
                style={{
                  fontSize: '10.5px',
                  fontWeight: 800,
                  color: '#94a3b8',
                  marginLeft: '4px',
                }}
              >
                +{netAdv}
              </span>
            )}
          </div>
        </div>

        {/* Relogio Digital FIDE */}
        {selectedTimeControl.initialMs > 0 && (
          <div
            style={{
              padding: '5px 10px',
              borderRadius: '7px',
              fontFamily: 'monospace',
              fontSize: '15px',
              fontWeight: 900,
              background: isLowTime
                ? '#b91c1c'
                : isTurnActive
                  ? '#f8fafc'
                  : '#1e293b',
              color: isLowTime
                ? '#ffffff'
                : isTurnActive
                  ? '#0f172a'
                  : '#94a3b8',
              minWidth: '68px',
              textAlign: 'right',
              boxShadow: isTurnActive ? '0 2px 8px rgba(0,0,0,0.35)' : undefined,
            }}
          >
            {formatClockMs(clockMs)}
          </div>
        )}
      </div>
    );
  };

  const topBarColor: Color = boardOrientation === 'w' ? 'b' : 'w';
  const bottomBarColor: Color = boardOrientation;

  const lastPlayedMoveHighlight = useMemo(() => {
    const idx =
      viewPlyIdx === null ? playMovesVerbose.length - 1 : viewPlyIdx;
    if (idx < 0 || !playMovesVerbose[idx]) return null;
    return {
      from: playMovesVerbose[idx].from,
      to: playMovesVerbose[idx].to,
    };
  }, [playMovesVerbose, viewPlyIdx]);

  const chessStats = useMemo(() => computeChessPlayerStats(chessData), [chessData]);
  const unlockedAchIds = useMemo(() => getUnlockedAchievements(chessData), [chessData]);
  const availableAchievements = useMemo(() => getAvailableAchievements(chessData), [chessData]);

  const categoryColors: Record<string, string> = {
    INICIANTE: '#fca5a5',
    CLUBE: '#fcd34d',
    INTERMEDIARIO: '#86efac',
    AVANCADO: '#67e8f9',
    ESPECIALISTA: '#d8b4fe',
    MESTRE: '#f472b6',
    GRAO_MESTRE: '#fbbf24',
  };

  const categoryLabels: Record<string, string> = {
    INICIANTE: 'Iniciante',
    CLUBE: 'Clube',
    INTERMEDIARIO: 'Intermediário',
    AVANCADO: 'Avançado',
    ESPECIALISTA: 'Especialista',
    MESTRE: 'Mestre',
    GRAO_MESTRE: 'Grão-Mestre',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingBottom: '24px' }}>
      {/* Cabecalho Soberano Estilo Chess.com */}
      <div
        className="glass-card"
        style={{
          padding: '12px 14px',
          background:
            'linear-gradient(135deg, rgba(24, 34, 22, 0.95), rgba(15, 23, 42, 0.96))',
          border: '1px solid rgba(129, 182, 76, 0.4)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '8px',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#81b64c', letterSpacing: '0.8px' }}>
              ARENA SOBERANA FIDE & CHESS960 • 100% OFFLINE
            </div>
            <h2 style={{ margin: '2px 0 0', fontSize: '17px', fontWeight: 900, color: '#f8fafc' }}>
              ♟️ Xadrez Grande Mestre 2.0
            </h2>
          </div>

          <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
            <div
              style={{
                padding: '4px 8px',
                borderRadius: '8px',
                background: 'rgba(129,182,76,0.16)',
                border: '1px solid rgba(129,182,76,0.35)',
                fontSize: '11px',
                fontWeight: 800,
                color: '#d9f99d',
              }}
            >
              ⚔️ Elo {chessData.playRating}
            </div>
            <div
              style={{
                padding: '4px 8px',
                borderRadius: '8px',
                background: 'rgba(245,158,11,0.16)',
                border: '1px solid rgba(245,158,11,0.35)',
                fontSize: '11px',
                fontWeight: 800,
                color: '#fde68a',
              }}
            >
              🧩 Tática {chessData.puzzleRating}
            </div>
            <div
              style={{
                padding: '4px 8px',
                borderRadius: '8px',
                background: 'rgba(239,68,68,0.16)',
                border: '1px solid rgba(239,68,68,0.35)',
                fontSize: '11px',
                fontWeight: 800,
                color: '#fecaca',
              }}
            >
              🔥 Rush {chessData.puzzleRushBest}
            </div>
            <div
              style={{
                padding: '4px 8px',
                borderRadius: '8px',
                background: 'rgba(56,189,248,0.16)',
                border: '1px solid rgba(56,189,248,0.35)',
                fontSize: '11px',
                fontWeight: 800,
                color: '#bae6fd',
              }}
            >
              👁️ Visão {chessData.visionBestScore ?? 0}
            </div>
          </div>
        </div>

        {/* Navegacao dos 5 Pilares Chess.com 2.0 */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: '5px',
            marginTop: '10px',
          }}
        >
          {(
            [
              { id: 'JOGAR', label: '⚔️ Jogar' },
              { id: 'REVISAO', label: '🔍 Revisão' },
              { id: 'PROBLEMAS', label: '🧩 Tática' },
              { id: 'TREINAR', label: '🎓 Treinar' },
              { id: 'ANALISE', label: '📖 Análise' },
            ] as const
          ).map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setSubTab(t.id)}
              style={{
                padding: '8px 2px',
                borderRadius: '8px',
                border:
                  subTab === t.id
                    ? '1px solid #81b64c'
                    : '1px solid rgba(255,255,255,0.1)',
                background:
                  subTab === t.id ? '#81b64c' : 'rgba(255,255,255,0.05)',
                color: subTab === t.id ? '#0f172a' : '#e2e8f0',
                fontSize: '11px',
                fontWeight: 800,
                cursor: 'pointer',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Barra Rapida de Tema, Seta e Som */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '6px',
            marginTop: '9px',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', gap: '4px', alignItems: 'center', flexWrap: 'wrap' }}>
            {(Object.keys(CHESS_BOARD_THEMES) as ChessBoardThemeId[]).map((thId) => {
              const spec = CHESS_BOARD_THEMES[thId];
              const active = chessData.preferredTheme === thId;
              return (
                <button
                  key={thId}
                  type="button"
                  title={spec.namePt}
                  onClick={() =>
                    onUpdateVault((prev) => ({
                      ...prev,
                      chessState: {
                        ...ensureChessVault(prev.chessState),
                        preferredTheme: thId,
                      },
                    }))
                  }
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '3px 7px',
                    borderRadius: '6px',
                    border: active
                      ? '1.5px solid #81b64c'
                      : '1px solid rgba(255,255,255,0.14)',
                    background: active ? 'rgba(129,182,76,0.2)' : 'rgba(0,0,0,0.25)',
                    color: '#e2e8f0',
                    fontSize: '10px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  <span
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '2px',
                      background: `linear-gradient(135deg, ${spec.lightSq} 50%, ${spec.darkSq} 50%)`,
                      display: 'inline-block',
                    }}
                  />
                  {thId === 'CHESS_VERDE'
                    ? 'Verde'
                    : thId === 'MADEIRA_CLASSICA'
                      ? 'Madeira'
                      : thId === 'OCEANO_GELO'
                        ? 'Oceano'
                        : 'Obsidiana'}
                </button>
              );
            })}
          </div>

          <div style={{ display: 'flex', gap: '5px' }}>
            <button
              type="button"
              onClick={() => setArrowDrawMode((v) => !v)}
              style={{
                padding: '3px 8px',
                borderRadius: '6px',
                border: arrowDrawMode
                  ? '1px solid #f59e0b'
                  : '1px solid rgba(255,255,255,0.14)',
                background: arrowDrawMode
                  ? 'rgba(245,158,11,0.25)'
                  : 'rgba(255,255,255,0.06)',
                color: arrowDrawMode ? '#fde68a' : '#cbd5e1',
                fontSize: '10.5px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              🎯 Seta {arrowDrawMode ? 'ON' : 'OFF'}
            </button>

            <button
              type="button"
              onClick={() =>
                onUpdateVault((prev) => {
                  const cur = ensureChessVault(prev.chessState);
                  return {
                    ...prev,
                    chessState: { ...cur, soundEnabled: !cur.soundEnabled },
                  };
                })
              }
              style={{
                padding: '3px 8px',
                borderRadius: '6px',
                border: '1px solid rgba(255,255,255,0.14)',
                background: 'rgba(255,255,255,0.06)',
                color: '#cbd5e1',
                fontSize: '10.5px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              {chessData.soundEnabled ? '🔊 Som' : '🔇 Mudo'}
            </button>
          </div>
        </div>
      </div>

      {copyFeedback && (
        <div
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            background: 'rgba(34, 197, 94, 0.2)',
            border: '1px solid rgba(34, 197, 94, 0.5)',
            color: '#bbf7d0',
            fontSize: '12px',
            fontWeight: 700,
            textAlign: 'center',
          }}
        >
          {copyFeedback}
        </div>
      )}

      {/* ==================================================================== */}
      /* PAINEL DE ESTATÍSTICAS E CONQUISTAS ESTILO CHESS.COM                  */
      {/* ==================================================================== */}
      <div className="glass-card" style={{ padding: '12px 14px' }}>
        <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#81b64c', letterSpacing: '0.8px', marginBottom: '8px' }}>
          📊 Seu Perfil de Xadrez SOBERANO
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '10px' }}>
          <div style={{ flex: 1, minWidth: '120px', padding: '8px 10px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Categoria ELO</div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '15px',
                fontWeight: 900,
                color: categoryColors[chessStats.category] ?? '#f8fafc',
                marginTop: '3px',
              }}
            >
              <span style={{ background: categoryColors[chessStats.category] ?? '#f8fafc', color: '#0f172a', padding: '1px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 900 }}>
                {categoryLabels[chessStats.category]}
              </span>
              <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>{chessStats.currentRating} Elo</span>
            </div>
            <div style={{ fontSize: '9.5px', color: '#64748b', marginTop: '3px' }}>
              {chessStats.currentRating < 2500
                ? `+${2500 - chessStats.currentRating} para Grão-Mestre`
                : 'Você é Grão-Mestre!'}
            </div>
          </div>
          <div style={{ flex: 1, minWidth: '120px', padding: '8px 10px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Partidas</div>
            <div style={{ display: 'flex', gap: '6px', fontSize: '13px', fontWeight: 800, color: '#f8fafc', marginTop: '3px' }}>
              <span style={{ color: '#86efac' }}>{chessStats.wins} V</span>
              <span style={{ color: '#94a3b8' }}>{chessStats.draws} E</span>
              <span style={{ color: '#fca5a5' }}>{chessStats.losses} D</span>
            </div>
            <div style={{ fontSize: '9.5px', color: '#64748b', marginTop: '3px' }}>
              {chessStats.gamesPlayed} jogadas • {chessStats.winRatePct}% aproveitamento
            </div>
          </div>
          <div style={{ flex: 1, minWidth: '120px', padding: '8px 10px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Sequência</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', fontSize: '16px', fontWeight: 900, color: '#fde68a', marginTop: '3px' }}>
              <span>{chessStats.currentWinStreak}</span>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>{chessStats.currentWinStreak === 1 ? 'vitória' : 'vitórias'}</span>
            </div>
            <div style={{ fontSize: '9.5px', color: '#64748b', marginTop: '3px' }}>
              Recorde: {chessStats.longestWinStreak} seguidas
            </div>
          </div>
        </div>

        {/* Conquistas */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '6px' }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: '#81b64c', marginBottom: '6px', marginRight: 'auto' }}>Conquistas</div>
          {unlockedAchIds.length > 0 ? (
            unlockedAchIds.map((id) => {
              const spec = CHESS_ACHIEVEMENTS.find((a) => a.id === id);
              return (
                <button
                  key={id}
                  type="button"
                  title={spec ? `${spec.title}: ${spec.descriptionPt}` : id}
                  disabled
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    padding: '6px 9px',
                    borderRadius: '8px',
                    border: '1px solid rgba(129,182,76,0.35)',
                    background: 'rgba(129,182,76,0.15)',
                    color: '#f8fafc',
                    fontSize: '11px',
                    fontWeight: 800,
                    cursor: 'default',
                  }}
                >
                  <span style={{ fontSize: '14px' }}>{spec ? spec.icon : '🏅'}</span>
                  <span>{spec ? spec.title : id}</span>
                </button>
              );
            })
          ) : (
            <span style={{ fontSize: '11px', color: '#94a3b8', fontStyle: 'italic' }}>Nenhuma conquista ainda. Jogue e vença!</span>
          )}
          {availableAchievements.slice(0, 4).map((spec) => (
            <button
              key={spec.id}
              type="button"
              title={spec.conditionPt}
              disabled
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '6px 9px',
                borderRadius: '8px',
                border: '1px solid rgba(255,255,255,0.08)',
                background: 'rgba(255,255,255,0.04)',
                color: '#94a3b8',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'default',
                opacity: 0.5,
              }}
            >
              <span style={{ fontSize: '14px', opacity: 0.4 }}>❓</span>
              <span style={{ opacity: 0.6 }}>{spec.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ==================================================================== */}
      {/* MODO 1: JOGAR (VS 8 BOTS + 2P LOCAL + CHESS960 + FINAIS + RELOGIOS)  */}
      {/* ==================================================================== */}
      {subTab === 'JOGAR' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Painel de Orientacao quando estiver jogando um Treino de Final */}
          {activeEndgameDrill && (
            <div
              className="glass-card"
              style={{
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                padding: '10px 12px',
                border: '1px solid rgba(245, 158, 11, 0.5)',
                background: 'rgba(40, 28, 12, 0.9)',
                boxSizing: 'border-box',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                <div style={{ fontSize: '12px', fontWeight: 900, color: '#fde68a' }}>
                  👑 {activeEndgameDrill.titlePt}
                </div>
                <div style={{ display: 'flex', gap: '5px' }}>
                  <button
                    type="button"
                    onClick={() => setShowEndgameHint((v) => !v)}
                    style={navBtnStyle}
                  >
                    💡 Método
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveEndgameDrill(null);
                      setMatchActive(false);
                      setMatchStartFen(STANDARD_START_FEN);
                      setPlayMovesVerbose([]);
                    }}
                    style={navBtnStyle}
                  >
                    ✖ Sair do Final
                  </button>
                </div>
              </div>
              <div style={{ fontSize: '11.5px', color: '#fef3c7', marginTop: '4px', lineHeight: 1.4 }}>
                {activeEndgameDrill.principleSummaryPt}
              </div>
              {showEndgameHint && (
                <div
                  style={{
                    marginTop: '6px',
                    padding: '6px 8px',
                    borderRadius: '6px',
                    background: 'rgba(255,255,255,0.08)',
                    fontSize: '11px',
                    color: '#a5f3fc',
                  }}
                >
                  🎯 <strong>Roteiro Técnico:</strong> {activeEndgameDrill.stepByStepHintPt}
                </div>
              )}
            </div>
          )}

          {/* Balao de Fala do Bot */}
          {playOpponentKind === 'BOT' && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 12px',
                borderRadius: '10px',
                background: 'rgba(30, 41, 59, 0.82)',
                border: '1px solid rgba(255,255,255,0.1)',
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                boxSizing: 'border-box',
              }}
            >
              <div
                style={{
                  fontSize: '24px',
                  width: '38px',
                  height: '38px',
                  borderRadius: '10px',
                  background: 'rgba(255,255,255,0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {selectedBot.avatarCode}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#81b64c' }}>
                  {selectedBot.name} • {selectedBot.titleBadge}
                </div>
                <div style={{ fontSize: '12px', color: '#e2e8f0', lineHeight: 1.35 }}>
                  “{botQuote}”
                </div>
              </div>
            </div>
          )}

          {/* Barra Superior do Oponente */}
          {renderPlayerBar(topBarColor)}

          {/* Tabuleiro Oficial */}
          <ChessBoardView
            fen={displayedPlayFen}
            orientation={boardOrientation}
            themeId={chessData.preferredTheme}
            interactive={matchActive && viewPlyIdx === null}
            allowedMoveColor={playOpponentKind === 'BOT' ? userColor : 'both'}
            allowPremove={playOpponentKind === 'BOT'}
            premove={premove}
            onSetPremove={setPremove}
            lastMove={lastPlayedMoveHighlight}
            hintSquares={
              coachHint ? { from: coachHint.from, to: coachHint.to } : null
            }
            engineArrows={
              coachHint
                ? [
                    {
                      from: coachHint.from,
                      to: coachHint.to,
                      color: '#22d3ee',
                      opacity: 0.9,
                    },
                  ]
                : []
            }
            showEvalBar={!ratedMatch || !matchActive}
            evalWhiteCp={liveAssistedEval.cp}
            mateInMoves={liveAssistedEval.mate}
            arrowDrawMode={arrowDrawMode}
            onMove={executePlayMove}
          />

          {/* Barra Inferior do Jogador */}
          {renderPlayerBar(bottomBarColor)}

          {/* Detector de Abertura ECO Ao Vivo */}
          {playMovesVerbose.length > 0 && (
            <div
              style={{
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                padding: '6px 10px',
                borderRadius: '8px',
                background: 'rgba(213, 164, 125, 0.12)',
                border: '1px solid rgba(213, 164, 125, 0.3)',
                fontSize: '11.5px',
                color: '#fed7aa',
                boxSizing: 'border-box',
              }}
            >
              📖 <strong>{playOpening.eco}</strong> — {playOpening.namePt}
            </div>
          )}

          {/* Dica do Mestre (Modo Amistoso) */}
          {coachHint && (
            <div
              style={{
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                padding: '9px 12px',
                borderRadius: '9px',
                background: 'rgba(34, 211, 238, 0.13)',
                border: '1px solid rgba(34, 211, 238, 0.42)',
                color: '#cffafe',
                fontSize: '12px',
                boxSizing: 'border-box',
              }}
            >
              💡 <strong>Treinador FORJA:</strong> {coachHint.comment}
            </div>
          )}

          {/* Banner Pos-Partida com Botao Direto para Revisao Estilo Chess.com! */}
          {gameOverBanner && (
            <div
              className="glass-card"
              style={{
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                padding: '14px',
                border: '1.5px solid #81b64c',
                background: 'rgba(20, 32, 22, 0.95)',
                textAlign: 'center',
                boxSizing: 'border-box',
              }}
            >
              <div style={{ fontSize: '16px', fontWeight: 900, color: '#f8fafc' }}>
                {gameOverBanner.headline}
              </div>
              <div style={{ fontSize: '12px', color: '#cbd5e1', marginTop: '3px' }}>
                {gameOverBanner.reason}
                {gameOverBanner.eloDelta !== 0 && (
                  <strong
                    style={{
                      marginLeft: '6px',
                      color: gameOverBanner.eloDelta > 0 ? '#86efac' : '#fca5a5',
                    }}
                  >
                    ({gameOverBanner.eloDelta > 0 ? '+' : ''}
                    {gameOverBanner.eloDelta} Elo)
                  </strong>
                )}
              </div>

              <div
                style={{
                  display: 'flex',
                  gap: '8px',
                  justifyContent: 'center',
                  marginTop: '10px',
                  flexWrap: 'wrap',
                }}
              >
                <button
                  type="button"
                  onClick={() => launchGameReviewFromMoves(playMovesVerbose)}
                  style={{
                    padding: '9px 14px',
                    borderRadius: '8px',
                    border: 'none',
                    background: '#81b64c',
                    color: '#0f172a',
                    fontWeight: 900,
                    fontSize: '12.5px',
                    cursor: 'pointer',
                  }}
                >
                  🔍 Revisão da Partida (CAPS %)
                </button>
                <button
                  type="button"
                  onClick={startNewPlayMatch}
                  style={{
                    padding: '9px 14px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.2)',
                    background: 'rgba(255,255,255,0.08)',
                    color: '#f8fafc',
                    fontWeight: 800,
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  🔄 Revanche
                </button>
              </div>
            </div>
          )}

          {/* Lista Navegavel de Lances SAN + Controles de Partida */}
          {playMovesVerbose.length > 0 && (
            <div
              className="glass-card"
              style={{
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                padding: '10px',
                boxSizing: 'border-box',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  gap: '6px',
                  overflowX: 'auto',
                  paddingBottom: '6px',
                  fontSize: '12px',
                }}
              >
                {Array.from(
                  { length: Math.ceil(playMovesVerbose.length / 2) },
                  (_, pairIdx) => {
                    const wIdx = pairIdx * 2;
                    const bIdx = wIdx + 1;
                    const wm = playMovesVerbose[wIdx];
                    const bm = playMovesVerbose[bIdx];
                    const activeIdx =
                      viewPlyIdx === null ? playMovesVerbose.length - 1 : viewPlyIdx;
                    return (
                      <div
                        key={pairIdx}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '3px',
                          flexShrink: 0,
                          padding: '2px 5px',
                          borderRadius: '6px',
                          background: 'rgba(255,255,255,0.04)',
                        }}
                      >
                        <span style={{ color: '#64748b', fontWeight: 700 }}>
                          {pairIdx + 1}.
                        </span>
                        <button
                          type="button"
                          onClick={() =>
                            setViewPlyIdx(
                              wIdx === playMovesVerbose.length - 1 ? null : wIdx,
                            )
                          }
                          style={{
                            border: 'none',
                            borderRadius: '4px',
                            padding: '2px 5px',
                            cursor: 'pointer',
                            fontWeight: 800,
                            fontSize: '12px',
                            background:
                              activeIdx === wIdx
                                ? '#81b64c'
                                : 'transparent',
                            color: activeIdx === wIdx ? '#0f172a' : '#f8fafc',
                          }}
                        >
                          {wm.san}
                        </button>
                        {bm && (
                          <button
                            type="button"
                            onClick={() =>
                              setViewPlyIdx(
                                bIdx === playMovesVerbose.length - 1 ? null : bIdx,
                              )
                            }
                            style={{
                              border: 'none',
                              borderRadius: '4px',
                              padding: '2px 5px',
                              cursor: 'pointer',
                              fontWeight: 800,
                              fontSize: '12px',
                              background:
                                activeIdx === bIdx
                                  ? '#81b64c'
                                  : 'transparent',
                              color: activeIdx === bIdx ? '#0f172a' : '#cbd5e1',
                            }}
                          >
                            {bm.san}
                          </button>
                        )}
                      </div>
                    );
                  },
                )}
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '5px',
                  marginTop: '6px',
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button
                    type="button"
                    onClick={() => setViewPlyIdx(-1)}
                    style={navBtnStyle}
                  >
                    ⏮
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setViewPlyIdx((cur) => {
                        const base =
                          cur === null ? playMovesVerbose.length - 1 : cur;
                        return Math.max(-1, base - 1);
                      })
                    }
                    style={navBtnStyle}
                  >
                    ◀
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setViewPlyIdx((cur) => {
                        if (cur === null) return null;
                        const next = cur + 1;
                        return next >= playMovesVerbose.length - 1 ? null : next;
                      })
                    }
                    style={navBtnStyle}
                  >
                    ▶
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewPlyIdx(null)}
                    style={navBtnStyle}
                  >
                    ⏭ Ao Vivo
                  </button>
                </div>

                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() =>
                      setBoardOrientation((o) => (o === 'w' ? 'b' : 'w'))
                    }
                    style={navBtnStyle}
                  >
                    🔄 Girar
                  </button>
                  {!ratedMatch && matchActive && (
                    <>
                      <button
                        type="button"
                        onClick={handleRequestCoachHint}
                        style={navBtnStyle}
                      >
                        💡 Dica
                      </button>
                      <button
                        type="button"
                        onClick={handleUndoMoveAssisted}
                        style={navBtnStyle}
                      >
                        ↩️ Voltar
                      </button>
                    </>
                  )}
                  {matchActive && (
                    <>
                      <button
                        type="button"
                        onClick={handleOfferDraw}
                        style={navBtnStyle}
                      >
                        🤝 Empate
                      </button>
                      {!resignConfirm ? (
                        <button
                          type="button"
                          onClick={() => setResignConfirm(true)}
                          style={{ ...navBtnStyle, color: '#fca5a5' }}
                        >
                          🏳️ Abandonar
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => {
                            const winWhite =
                              playOpponentKind === 'LOCAL_2P'
                                ? liveGame.turn() === 'w'
                                  ? 0
                                  : 1
                                : userColor === 'w'
                                  ? 0
                                  : 1;
                            finalizePlayMatch(
                              winWhite,
                              'Abandono',
                              playMovesVerbose,
                            );
                            emitChessAudio('GAME_END');
                          }}
                          style={{
                            ...navBtnStyle,
                            background: '#dc2626',
                            color: '#fff',
                          }}
                        >
                          Confirmar Abandono
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Painel de Configuracao de Nova Partida (Bots, Tempo Fischer, Cor, Modo) */}
          {!matchActive && (
            <div
              className="glass-card"
              style={{
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                padding: '14px',
                boxSizing: 'border-box',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 900, color: '#f8fafc' }}>
                ⚙️ Configurar Partida Estilo Chess.com
              </div>

              {/* Variante Oficial: Classico FIDE vs Chess960 / Freestyle */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '6px' }}>
                  VARIANTE OFICIAL FIDE:
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setPlayVariant('CLASSICO');
                      setActiveEndgameDrill(null);
                      setMatchStartFen(STANDARD_START_FEN);
                      setPlayMovesVerbose([]);
                    }}
                    style={subModeBtnStyle(playVariant === 'CLASSICO' && !activeEndgameDrill)}
                  >
                    ♟️ Clássico FIDE (#518)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setPlayVariant('CHESS960');
                      setActiveEndgameDrill(null);
                      const rnd = Math.floor(Math.random() * 960);
                      setChess960Id(rnd);
                      setMatchStartFen(generateChess960Position(rnd).fen);
                      setPlayMovesVerbose([]);
                    }}
                    style={subModeBtnStyle(playVariant === 'CHESS960')}
                  >
                    🎲 Chess960 / Freestyle
                  </button>
                </div>

                {playVariant === 'CHESS960' && (
                  <div
                    style={{
                      marginTop: '7px',
                      padding: '8px 10px',
                      borderRadius: '8px',
                      background: 'rgba(129,182,76,0.1)',
                      border: '1px solid rgba(129,182,76,0.32)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '8px',
                      flexWrap: 'wrap',
                    }}
                  >
                    <div style={{ fontSize: '11.5px', color: '#e2e8f0' }}>
                      Scharnagl <strong>#{chess960Id}</strong> • Fileira:{' '}
                      <code style={{ color: '#d9f99d', fontWeight: 900 }}>
                        {generateChess960Position(chess960Id).backRankUpper}
                      </code>
                    </div>
                    <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                      <input
                        type="number"
                        min={0}
                        max={959}
                        value={chess960Id}
                        onChange={(e) => {
                          const v = Math.max(
                            0,
                            Math.min(959, Number(e.target.value) || 0),
                          );
                          setChess960Id(v);
                          setMatchStartFen(generateChess960Position(v).fen);
                          setPlayMovesVerbose([]);
                        }}
                        style={{
                          width: '58px',
                          padding: '4px 6px',
                          borderRadius: '6px',
                          border: '1px solid rgba(255,255,255,0.2)',
                          background: '#0f172a',
                          color: '#f8fafc',
                          fontSize: '11px',
                          fontWeight: 800,
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => {
                          const rnd = Math.floor(Math.random() * 960);
                          setChess960Id(rnd);
                          setMatchStartFen(generateChess960Position(rnd).fen);
                          setPlayMovesVerbose([]);
                        }}
                        style={navBtnStyle}
                      >
                        🎲 Sortear
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Modo: vs Bot ou 2 Jogadores Local */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                <button
                  type="button"
                  onClick={() => setPlayOpponentKind('BOT')}
                  style={{
                    padding: '8px',
                    borderRadius: '8px',
                    border:
                      playOpponentKind === 'BOT'
                        ? '1.5px solid #81b64c'
                        : '1px solid rgba(255,255,255,0.12)',
                    background:
                      playOpponentKind === 'BOT'
                        ? 'rgba(129,182,76,0.2)'
                        : 'rgba(255,255,255,0.04)',
                    color: '#f8fafc',
                    fontWeight: 800,
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  🤖 Contra Personalidades IA
                </button>
                <button
                  type="button"
                  onClick={() => setPlayOpponentKind('LOCAL_2P')}
                  style={{
                    padding: '8px',
                    borderRadius: '8px',
                    border:
                      playOpponentKind === 'LOCAL_2P'
                        ? '1.5px solid #81b64c'
                        : '1px solid rgba(255,255,255,0.12)',
                    background:
                      playOpponentKind === 'LOCAL_2P'
                        ? 'rgba(129,182,76,0.2)'
                        : 'rgba(255,255,255,0.04)',
                    color: '#f8fafc',
                    fontWeight: 800,
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  👥 2 Jogadores (Passa-e-Joga)
                </button>
              </div>

              {/* Selecao dos 8 Bots (400 a 2400 Elo) */}
              {playOpponentKind === 'BOT' && (
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '6px' }}>
                    ESCOLHA SEU ADVERSÁRIO (400 – 2400 ELO):
                  </div>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(2, 1fr)',
                      gap: '6px',
                    }}
                  >
                    {CHESS_BOTS.map((b) => {
                      const sel = b.id === selectedBotId;
                      return (
                        <button
                          key={b.id}
                          type="button"
                          onClick={() => {
                            setSelectedBotId(b.id);
                            setBotQuote(b.quotes.greeting);
                          }}
                          style={{
                            padding: '8px',
                            borderRadius: '9px',
                            textAlign: 'left',
                            border: sel
                              ? '1.5px solid #81b64c'
                              : '1px solid rgba(255,255,255,0.1)',
                            background: sel
                              ? 'rgba(129,182,76,0.18)'
                              : 'rgba(255,255,255,0.03)',
                            cursor: 'pointer',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '12px', fontWeight: 800, color: '#f8fafc' }}>
                              {b.avatarCode} {b.name}
                            </span>
                            <span
                              style={{
                                fontSize: '10.5px',
                                fontWeight: 900,
                                color: '#81b64c',
                              }}
                            >
                              {b.elo}
                            </span>
                          </div>
                          <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '2px' }}>
                            {b.styleSummary}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Controle de Tempo Oficial FIDE / Chess.com */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '6px' }}>
                  RITMO DE JOGO (RELÓGIO FISCHER):
                </div>
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  {TIME_CONTROLS.map((tc) => {
                    const sel = tc.id === timeControlId;
                    return (
                      <button
                        key={tc.id}
                        type="button"
                        onClick={() => setTimeControlId(tc.id)}
                        style={{
                          padding: '6px 9px',
                          borderRadius: '7px',
                          border: sel
                            ? '1.5px solid #81b64c'
                            : '1px solid rgba(255,255,255,0.12)',
                          background: sel
                            ? 'rgba(129,182,76,0.22)'
                            : 'rgba(255,255,255,0.04)',
                          color: sel ? '#ecfccb' : '#cbd5e1',
                          fontSize: '11px',
                          fontWeight: 800,
                          cursor: 'pointer',
                        }}
                      >
                        {tc.category} {tc.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Cor & Ranqueada vs Assistida */}
              {playOpponentKind === 'BOT' && (
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    {(
                      [
                        { id: 'w', label: '♔ Brancas' },
                        { id: 'random', label: '🎲 Sorteio' },
                        { id: 'b', label: '♚ Pretas' },
                      ] as const
                    ).map((c) => (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => setColorChoice(c.id)}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '7px',
                          border:
                            colorChoice === c.id
                              ? '1.5px solid #81b64c'
                              : '1px solid rgba(255,255,255,0.12)',
                          background:
                            colorChoice === c.id
                              ? 'rgba(129,182,76,0.2)'
                              : 'rgba(255,255,255,0.04)',
                          color: '#f8fafc',
                          fontSize: '11px',
                          fontWeight: 800,
                          cursor: 'pointer',
                        }}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={() => setRatedMatch((r) => !r)}
                    style={{
                      padding: '6px 10px',
                      borderRadius: '7px',
                      border: ratedMatch
                        ? '1px solid #f59e0b'
                        : '1px solid #22d3ee',
                      background: ratedMatch
                        ? 'rgba(245,158,11,0.16)'
                        : 'rgba(34,211,238,0.16)',
                      color: ratedMatch ? '#fde68a' : '#a5f3fc',
                      fontSize: '11px',
                      fontWeight: 800,
                      cursor: 'pointer',
                    }}
                  >
                    {ratedMatch
                      ? '🏆 Partida Ranqueada (Vale Elo)'
                      : '🎓 Modo Treinador (Dica + Voltar)'}
                  </button>
                </div>
              )}

              <button
                type="button"
                onClick={startNewPlayMatch}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '10px',
                  border: 'none',
                  background: '#81b64c',
                  color: '#0f172a',
                  fontSize: '14px',
                  fontWeight: 900,
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(129, 182, 76, 0.4)',
                }}
              >
                ♟️ INICIAR PARTIDA AGORA
              </button>

              {/* Historico de Partidas Salvas para Reabrir na Revisao */}
              {chessData.savedGames.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '6px' }}>
                    HISTÓRICO RECENTE ({chessData.wins}V • {chessData.draws}E • {chessData.losses}D):
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    {chessData.savedGames.slice(0, 5).map((sg) => (
                      <div
                        key={sg.id}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '6px 9px',
                          borderRadius: '8px',
                          background: 'rgba(255,255,255,0.03)',
                          border: '1px solid rgba(255,255,255,0.08)',
                          fontSize: '11px',
                        }}
                      >
                        <div>
                          <strong
                            style={{
                              color:
                                sg.result === 'VITORIA'
                                  ? '#86efac'
                                  : sg.result === 'DERROTA'
                                    ? '#fca5a5'
                                    : '#fde68a',
                            }}
                          >
                            {sg.result}
                          </strong>{' '}
                          vs {sg.opponentName} ({sg.movesCount} lances • {sg.openingEco})
                          {typeof sg.userAccuracyPct === 'number' && (
                            <span
                              style={{
                                marginLeft: '5px',
                                padding: '1px 5px',
                                borderRadius: '4px',
                                background: 'rgba(129,182,76,0.2)',
                                color: '#d9f99d',
                                fontWeight: 800,
                                fontSize: '10px',
                              }}
                            >
                              {sg.userAccuracyPct.toFixed(1)}% CAPS
                              {sg.brilliantCount ? ` • ${sg.brilliantCount}!!` : ''}
                            </span>
                          )}
                        </div>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard?.writeText(sg.pgn);
                              showToast('PGN copiado para a área de transferência!');
                            }}
                            style={navBtnStyle}
                            title="Copiar PGN"
                          >
                            📋 PGN
                          </button>
                          <button
                            type="button"
                            onClick={() => launchReviewFromSavedGame(sg)}
                            style={{
                              padding: '4px 8px',
                              borderRadius: '6px',
                              border: '1px solid #81b64c',
                              background: 'rgba(129,182,76,0.18)',
                              color: '#d9f99d',
                              fontSize: '10.5px',
                              fontWeight: 800,
                              cursor: 'pointer',
                            }}
                          >
                            🔍 Revisar
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODO 2: REVISAO DE PARTIDA COMPLETA (CAPS % + 9 SELOS + GRAFICO)     */}
      {/* ==================================================================== */}
      {subTab === 'REVISAO' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {!reviewReport ? (
            <div
              className="glass-card"
              style={{
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                padding: '18px',
                textAlign: 'center',
                boxSizing: 'border-box',
              }}
            >
              <div style={{ fontSize: '15px', fontWeight: 900, color: '#f8fafc' }}>
                🔍 Revisão de Partida Estilo Chess.com
              </div>
              <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.5 }}>
                Calcula a <strong>Precisão CAPS (%)</strong> das Brancas e Pretas, classifica cada
                lance nos 9 selos oficiais (<code>!! Brilhante</code> até <code>?? Capivarada</code>),
                desenha o gráfico de vantagem e permite corrigir seus erros no tabuleiro!
              </p>
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
                {playMovesVerbose.length > 0 && (
                  <button
                    type="button"
                    onClick={() => launchGameReviewFromMoves(playMovesVerbose)}
                    style={{
                      padding: '10px 14px',
                      borderRadius: '8px',
                      border: 'none',
                      background: '#81b64c',
                      color: '#0f172a',
                      fontWeight: 900,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    🔍 Revisar Partida Atual
                  </button>
                )}
                <button
                  type="button"
                  onClick={loadOperaImmortalForReview}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: '1px solid #26c2a3',
                    background: 'rgba(38, 194, 163, 0.16)',
                    color: '#99f6e4',
                    fontWeight: 800,
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  ⚡ Demonstrar na Imortal da Ópera (Morphy, 1858)
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Placar CAPS de Precisao (%) Brancas vs Pretas */}
              <div
                className="glass-card"
                style={{
                  maxWidth: '470px',
                  width: '100%',
                  margin: '0 auto',
                  padding: '12px',
                  boxSizing: 'border-box',
                }}
              >
                <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 800, textAlign: 'center' }}>
                  📖 {reviewReport.openingEco} — {reviewReport.openingNamePt}
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '10px',
                    marginTop: '8px',
                  }}
                >
                  <div
                    style={{
                      padding: '10px',
                      borderRadius: '9px',
                      background: 'rgba(255,255,255,0.92)',
                      color: '#0f172a',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontSize: '10.5px', fontWeight: 800 }}>♔ BRANCAS • PRECISÃO</div>
                    <div style={{ fontSize: '24px', fontWeight: 900 }}>
                      {reviewReport.whiteAccuracyPct.toFixed(1)}%
                    </div>
                  </div>
                  <div
                    style={{
                      padding: '10px',
                      borderRadius: '9px',
                      background: '#1e293b',
                      border: '1px solid rgba(255,255,255,0.18)',
                      color: '#f8fafc',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontSize: '10.5px', fontWeight: 800 }}>♚ PRETAS • PRECISÃO</div>
                    <div style={{ fontSize: '24px', fontWeight: 900 }}>
                      {reviewReport.blackAccuracyPct.toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Grafico Interativo SVG de Vantagem Lance a Lance */}
                <div style={{ marginTop: '10px' }}>
                  <svg
                    viewBox={`0 0 ${Math.max(100, reviewReport.moves.length * 10)} 56`}
                    style={{
                      width: '100%',
                      height: '54px',
                      borderRadius: '6px',
                      background: '#1e293b',
                      cursor: 'pointer',
                      display: 'block',
                    }}
                    onClick={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      const ratio = (e.clientX - rect.left) / Math.max(1, rect.width);
                      const idx = Math.min(
                        reviewReport.moves.length - 1,
                        Math.max(0, Math.floor(ratio * reviewReport.moves.length)),
                      );
                      setReviewPlyIdx(idx);
                      setRetryState(null);
                    }}
                  >
                    <line
                      x1="0"
                      y1="28"
                      x2={Math.max(100, reviewReport.moves.length * 10)}
                      y2="28"
                      stroke="rgba(255,255,255,0.22)"
                      strokeWidth="1"
                    />
                    <polygon
                      fill="#f1f5f9"
                      points={[
                        `0,56`,
                        ...reviewReport.moves.map((rm, idx) => {
                          const x = idx * 10 + 5;
                          const clamped = Math.max(-900, Math.min(900, rm.evalAfterWhiteCp));
                          const y = 28 - (clamped / 900) * 25;
                          return `${x},${y.toFixed(1)}`;
                        }),
                        `${reviewReport.moves.length * 10},56`,
                      ].join(' ')}
                    />
                    <line
                      x1={reviewPlyIdx * 10 + 5}
                      y1="0"
                      x2={reviewPlyIdx * 10 + 5}
                      y2="56"
                      stroke="#81b64c"
                      strokeWidth="2.5"
                    />
                  </svg>
                </div>
              </div>

              {/* Tabuleiro de Revisao com Selo Flutuante + Setas do Treinador */}
              <ChessBoardView
                fen={reviewBoardFen}
                orientation={boardOrientation}
                themeId={chessData.preferredTheme}
                interactive={Boolean(retryState?.active && !retryState.solved)}
                allowedMoveColor={activeReviewedMove?.color ?? 'both'}
                lastMove={
                  activeReviewedMove && !(retryState?.active && !retryState.solved)
                    ? {
                        from: activeReviewedMove.playedFrom,
                        to: activeReviewedMove.playedTo,
                      }
                    : null
                }
                engineArrows={reviewArrows}
                badgeOverlay={reviewBadgeOverlay}
                showEvalBar={true}
                evalWhiteCp={activeReviewedMove?.evalAfterWhiteCp ?? 0}
                mateInMoves={null}
                arrowDrawMode={arrowDrawMode}
                onMove={(from, to, promo) => {
                  if (!activeReviewedMove || !retryState?.active) return false;
                  const g = new Chess(activeReviewedMove.fenBefore);
                  let m: Move | null = null;
                  try {
                    m = g.move({ from, to, promotion: promo });
                  } catch {
                    m = null;
                  }
                  if (!m) return false;
                  if (m.san === activeReviewedMove.bestSan || g.isCheckmate()) {
                    emitChessAudio('PUZZLE_OK');
                    setRetryState({
                      active: true,
                      solved: true,
                      message: `Excelente! ${m.san} era exatamente o melhor lance!`,
                    });
                    return true;
                  }
                  emitChessAudio('ILLEGAL');
                  setRetryState({
                    active: true,
                    solved: false,
                    message: `${m.san} ainda não é o melhor recurso — tente encontrar um lance mais forte!`,
                  });
                  return false;
                }}
              />

              {/* Card do Treinador + Controles de Navegacao da Revisao */}
              {activeReviewedMove && (
                <div
                  className="glass-card"
                  style={{
                    maxWidth: '470px',
                    width: '100%',
                    margin: '0 auto',
                    padding: '12px',
                    boxSizing: 'border-box',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          padding: '3px 8px',
                          borderRadius: '999px',
                          background: MOVE_BADGES[activeReviewedMove.classification].colorHex,
                          color: '#fff',
                          fontSize: '12px',
                          fontWeight: 900,
                        }}
                      >
                        {MOVE_BADGES[activeReviewedMove.classification].symbol}{' '}
                        {MOVE_BADGES[activeReviewedMove.classification].labelPt}
                      </span>
                      <strong style={{ fontSize: '14px', color: '#f8fafc' }}>
                        {activeReviewedMove.moveNumber}
                        {activeReviewedMove.color === 'w' ? '. ' : '... '}
                        {activeReviewedMove.playedSan}
                      </strong>
                    </div>

                    {(activeReviewedMove.classification === 'IMPRECISAO' ||
                      activeReviewedMove.classification === 'ERRO' ||
                      activeReviewedMove.classification === 'CAPIVARADA') && (
                      <button
                        type="button"
                        onClick={() =>
                          setRetryState({
                            active: true,
                            solved: false,
                            message: 'Jogue no tabuleiro o melhor lance para corrigir este momento!',
                          })
                        }
                        style={{
                          padding: '4px 9px',
                          borderRadius: '7px',
                          border: '1px solid #f59e0b',
                          background: 'rgba(245,158,11,0.2)',
                          color: '#fde68a',
                          fontSize: '11px',
                          fontWeight: 800,
                          cursor: 'pointer',
                        }}
                      >
                        🎯 Tentar Melhor
                      </button>
                    )}
                  </div>

                  <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#cbd5e1', lineHeight: 1.45 }}>
                    {retryState?.active ? retryState.message : activeReviewedMove.coachCommentPt}
                  </p>

                  <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      onClick={() =>
                        launchPlayFromCustomFen(
                          reviewBoardFen,
                          'Posição da revisão carregada contra o Motor!',
                        )
                      }
                      style={{
                        ...navBtnStyle,
                        border: '1px solid rgba(56,189,248,0.45)',
                        color: '#bae6fd',
                      }}
                    >
                      ⚔️ Jogar desta Posição vs Motor
                    </button>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={() => {
                        setReviewPlyIdx(0);
                        setRetryState(null);
                      }}
                      style={navBtnStyle}
                    >
                      ⏮ Início
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setReviewPlyIdx((i) => Math.max(0, i - 1));
                        setRetryState(null);
                      }}
                      style={navBtnStyle}
                    >
                      ◀ Anterior
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setReviewPlyIdx((i) =>
                          Math.min(reviewReport.moves.length - 1, i + 1),
                        );
                        setRetryState(null);
                      }}
                      style={{
                        ...navBtnStyle,
                        background: '#81b64c',
                        color: '#0f172a',
                      }}
                    >
                      Próximo ▶
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        // Salta direto para o proximo momento critico (!!, !, ?!, ?, ??)
                        const nextCrit = reviewReport.moves.findIndex(
                          (m, idx) =>
                            idx > reviewPlyIdx &&
                            ['BRILHANTE', 'GRANDE', 'IMPRECISAO', 'ERRO', 'CAPIVARADA'].includes(
                              m.classification,
                            ),
                        );
                        if (nextCrit >= 0) {
                          setReviewPlyIdx(nextCrit);
                          setRetryState(null);
                        }
                      }}
                      style={navBtnStyle}
                    >
                      ⚡ Lance-Chave
                    </button>
                  </div>

                  {/* Matriz Completa dos 9 Selos Chess.com */}
                  <div
                    style={{
                      marginTop: '12px',
                      borderTop: '1px solid rgba(255,255,255,0.09)',
                      paddingTop: '8px',
                      display: 'grid',
                      gridTemplateColumns: '1fr auto 1fr',
                      rowGap: '4px',
                      fontSize: '11px',
                    }}
                  >
                    {(
                      [
                        'BRILHANTE',
                        'GRANDE',
                        'MELHOR',
                        'EXCELENTE',
                        'BOM',
                        'TEORIA',
                        'IMPRECISAO',
                        'ERRO',
                        'CAPIVARADA',
                      ] as MoveClassification[]
                    ).map((cls) => {
                      const b = MOVE_BADGES[cls];
                      return (
                        <React.Fragment key={cls}>
                          <div style={{ textAlign: 'right', paddingRight: '10px', fontWeight: 800, color: '#f8fafc' }}>
                            {reviewReport.countsWhite[cls]}
                          </div>
                          <div style={{ textAlign: 'center', fontWeight: 800, color: b.colorHex }}>
                            {b.symbol} {b.labelPt}
                          </div>
                          <div style={{ textAlign: 'left', paddingLeft: '10px', fontWeight: 800, color: '#cbd5e1' }}>
                            {reviewReport.countsBlack[cls]}
                          </div>
                        </React.Fragment>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODO 3: PROBLEMAS TATICOS + PROBLEMA DIARIO + PUZZLE RUSH            */}
      {/* ==================================================================== */}
      {subTab === 'PROBLEMAS' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div
            className="glass-card"
            style={{
              maxWidth: '470px',
              width: '100%',
              margin: '0 auto',
              padding: '10px',
              boxSizing: 'border-box',
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
              <button
                type="button"
                onClick={() => {
                  setRushActive(false);
                  setPuzzleMode('RANQUEADO');
                  loadPuzzleSpec(
                    pickNextRatedPuzzle(
                      chessData.puzzleRating,
                      chessData.solvedPuzzleIds,
                    ),
                  );
                }}
                style={subModeBtnStyle(puzzleMode === 'RANQUEADO')}
              >
                🎯 Ranqueado
              </button>
              <button
                type="button"
                onClick={() => {
                  setRushActive(false);
                  setPuzzleMode('DIARIO');
                  loadPuzzleSpec(getDailyPuzzleForDate(bioDayId));
                }}
                style={subModeBtnStyle(puzzleMode === 'DIARIO')}
              >
                📅 Diário
              </button>
              <button
                type="button"
                onClick={startPuzzleRush}
                style={subModeBtnStyle(puzzleMode === 'CORRIDA')}
              >
                🔥 Puzzle Rush
              </button>
            </div>

            {puzzleMode === 'CORRIDA' && (
              <div
                style={{
                  marginTop: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '6px 10px',
                  borderRadius: '8px',
                  background: 'rgba(239, 68, 68, 0.14)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  fontSize: '12px',
                  fontWeight: 900,
                }}
              >
                <span style={{ color: '#fde68a' }}>🔥 Acertos: {rushScore}</span>
                <span style={{ color: '#fca5a5' }}>
                  {'❤️'.repeat(Math.max(0, 3 - rushStrikes))}
                  {'🖤'.repeat(Math.min(3, rushStrikes))}
                </span>
                <span style={{ fontFamily: 'monospace', color: '#fff' }}>
                  ⏱ {formatClockMs(rushTimeLeftMs)}
                </span>
              </div>
            )}

            <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 900, color: '#f8fafc' }}>
                  {activePuzzle.titlePt}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                  {activePuzzle.themeTagPt} • Rating {activePuzzle.rating}
                </div>
              </div>
              <span
                style={{
                  padding: '4px 8px',
                  borderRadius: '7px',
                  background: puzzleOrientation === 'w' ? '#f8fafc' : '#1e293b',
                  color: puzzleOrientation === 'w' ? '#0f172a' : '#f8fafc',
                  border: '1px solid rgba(255,255,255,0.2)',
                  fontSize: '11px',
                  fontWeight: 900,
                }}
              >
                {puzzleOrientation === 'w' ? '♔ Jogam Brancas' : '♚ Jogam Pretas'}
              </span>
            </div>
          </div>

          <ChessBoardView
            fen={puzzleChessFen}
            orientation={puzzleOrientation}
            themeId={chessData.preferredTheme}
            interactive={puzzleStatus === 'SOLVING'}
            allowedMoveColor={new Chess(puzzleChessFen).turn()}
            lastMove={puzzleLastMove}
            hintSquares={puzzleHintSq}
            arrowDrawMode={arrowDrawMode}
            onMove={handlePuzzleUserMove}
          />

          <div
            className="glass-card"
            style={{
              maxWidth: '470px',
              width: '100%',
              margin: '0 auto',
              padding: '12px',
              boxSizing: 'border-box',
            }}
          >
            {puzzleStatus === 'SOLVING' && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '12px', color: '#cbd5e1', fontWeight: 700 }}>
                  Encontre a sequência vencedora! (Passo{' '}
                  {Math.floor(puzzleStepIdx / 2) + 1} de{' '}
                  {Math.ceil(activePuzzle.solutionLan.length / 2)})
                </span>
                {puzzleMode !== 'CORRIDA' && (
                  <button
                    type="button"
                    onClick={() => {
                      const lan = activePuzzle.solutionLan[puzzleStepIdx];
                      if (lan) {
                        setPuzzleHintSq({
                          from: lan.slice(0, 2) as Square,
                          to: lan.slice(0, 2) as Square,
                        });
                      }
                    }}
                    style={navBtnStyle}
                  >
                    💡 Dica de Peça
                  </button>
                )}
              </div>
            )}

            {puzzleStatus === 'SOLVED' && (
              <div>
                <div style={{ fontSize: '14px', fontWeight: 900, color: '#86efac' }}>
                  ✅ Problema Resolvido com Precisão!{' '}
                  {puzzleEloChange !== null && puzzleEloChange > 0 && `(+${puzzleEloChange} Elo)`}
                </div>
                <p style={{ margin: '5px 0 10px', fontSize: '12px', color: '#e2e8f0', lineHeight: 1.45 }}>
                  {activePuzzle.coachExplanationPt}
                </p>
                {puzzleMode !== 'CORRIDA' && (
                  <button
                    type="button"
                    onClick={() =>
                      loadPuzzleSpec(
                        pickNextRatedPuzzle(
                          chessData.puzzleRating,
                          chessData.solvedPuzzleIds,
                          activePuzzle.id,
                        ),
                      )
                    }
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      border: 'none',
                      background: '#81b64c',
                      color: '#0f172a',
                      fontWeight: 900,
                      fontSize: '12.5px',
                      cursor: 'pointer',
                    }}
                  >
                    Próximo Problema ▶
                  </button>
                )}
              </div>
            )}

            {puzzleStatus === 'FAILED' && (
              <div>
                <div style={{ fontSize: '14px', fontWeight: 900, color: '#fca5a5' }}>
                  {puzzleMode === 'CORRIDA'
                    ? `🏁 Fim da Corrida! Placar: ${rushScore} acertos`
                    : `❌ Lance Impreciso ${puzzleEloChange ? `(${puzzleEloChange} Elo)` : ''}`}
                </div>
                <p style={{ margin: '5px 0 10px', fontSize: '12px', color: '#cbd5e1' }}>
                  {puzzleMode === 'CORRIDA'
                    ? activePuzzle.coachExplanationPt
                    : 'Cuidado com contra-ataques ou defesas ocultas — tente novamente ou veja a explicação!'}
                </p>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {puzzleMode === 'CORRIDA' ? (
                    <button
                      type="button"
                      onClick={startPuzzleRush}
                      style={{
                        flex: 1,
                        padding: '9px',
                        borderRadius: '8px',
                        border: 'none',
                        background: '#81b64c',
                        color: '#0f172a',
                        fontWeight: 900,
                        cursor: 'pointer',
                      }}
                    >
                      🔥 Nova Corrida (3:00)
                    </button>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => {
                          setPuzzleStatus('SOLVING');
                        }}
                        style={{
                          flex: 1,
                          padding: '9px',
                          borderRadius: '8px',
                          border: 'none',
                          background: '#81b64c',
                          color: '#0f172a',
                          fontWeight: 900,
                          cursor: 'pointer',
                        }}
                      >
                        🔄 Tentar de Novo
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          const g = new Chess(activePuzzle.fen);
                          for (const lan of activePuzzle.solutionLan) {
                            g.move({
                              from: lan.slice(0, 2) as Square,
                              to: lan.slice(2, 4) as Square,
                              promotion: lan[4] as PieceSymbol | undefined,
                            });
                          }
                          setPuzzleChessFen(g.fen());
                          setPuzzleStatus('SOLVED');
                        }}
                        style={navBtnStyle}
                      >
                        👁️ Ver Solução
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODO 3.5: TREINAR (VISAO 30S + 8 FINAIS VS MOTOR + 6 AULAS GUIADAS)  */}
      {/* ==================================================================== */}
      {subTab === 'TREINAR' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div
            className="glass-card"
            style={{
              maxWidth: '470px',
              width: '100%',
              margin: '0 auto',
              padding: '10px',
              boxSizing: 'border-box',
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
              <button
                type="button"
                onClick={() => setTrainMode('VISAO')}
                style={subModeBtnStyle(trainMode === 'VISAO')}
              >
                👁️ Visão 30s
              </button>
              <button
                type="button"
                onClick={() => {
                  setVisionActive(false);
                  setTrainMode('FINAIS');
                }}
                style={subModeBtnStyle(trainMode === 'FINAIS')}
              >
                👑 Finais ({(chessData.completedEndgameIds ?? []).length}/8)
              </button>
              <button
                type="button"
                onClick={() => {
                  setVisionActive(false);
                  setTrainMode('AULAS');
                }}
                style={subModeBtnStyle(trainMode === 'AULAS')}
              >
                🎓 Aulas ({(chessData.completedAcademyIds ?? []).length}/6)
              </button>
            </div>
          </div>

          {/* SUB-MODO A: TREINADOR DE VISAO DE COORDENADAS 30S (ESTILO CHESS.COM VISION) */}
          {trainMode === 'VISAO' && (
            <>
              <div
                className="glass-card"
                style={{
                  maxWidth: '470px',
                  width: '100%',
                  margin: '0 auto',
                  padding: '12px',
                  boxSizing: 'border-box',
                  textAlign: 'center',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <div style={{ fontSize: '12px', fontWeight: 900, color: '#bae6fd' }}>
                    👁️ Visão de Tabuleiro • Recorde: {chessData.visionBestScore ?? 0}
                  </div>
                  <div style={{ fontSize: '12px', fontFamily: 'monospace', fontWeight: 900, color: '#f8fafc' }}>
                    ✅ {visionScore} • ❌ {visionMisses} • ⏱ {formatClockMs(visionTimeLeftMs)}
                  </div>
                </div>

                {visionActive ? (
                  <div
                    style={{
                      margin: '10px 0 4px',
                      padding: '10px',
                      borderRadius: '10px',
                      background: 'rgba(129, 182, 76, 0.2)',
                      border: '2px solid #81b64c',
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: 800, color: '#cbd5e1' }}>
                      TOQUE IMEDIATAMENTE NA CASA ({visionBoardSide === 'w' ? '♔ Visão Brancas' : '♚ Visão Pretas'}):
                    </div>
                    <div
                      style={{
                        fontSize: '34px',
                        fontWeight: 900,
                        color: '#ffffff',
                        letterSpacing: '2px',
                        lineHeight: 1.15,
                      }}
                    >
                      {visionTargetSq}
                    </div>
                  </div>
                ) : (
                  <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ fontSize: '11.5px', color: '#cbd5e1', lineHeight: 1.4 }}>
                      Automatize as 64 coordenadas como um Grande Mestre (Gobet & Simon, 1996): localize o máximo de casas em <strong>30 segundos</strong>!
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '5px', flexWrap: 'wrap' }}>
                      {(
                        [
                          { id: 'w', label: '♔ Brancas' },
                          { id: 'b', label: '♚ Pretas' },
                          { id: 'mixed', label: '🎲 Alternado' },
                        ] as const
                      ).map((p) => (
                        <button
                          key={p.id}
                          type="button"
                          onClick={() => {
                            setVisionPerspective(p.id);
                            if (p.id !== 'mixed') setVisionBoardSide(p.id);
                          }}
                          style={subModeBtnStyle(visionPerspective === p.id)}
                        >
                          {p.label}
                        </button>
                      ))}
                      <button
                        type="button"
                        onClick={() => setVisionShowPieces((v) => !v)}
                        style={subModeBtnStyle(visionShowPieces)}
                      >
                        {visionShowPieces ? '♟️ Com Peças' : '⬜ Sem Peças'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setVisionHideCoords((v) => !v)}
                        style={subModeBtnStyle(visionHideCoords)}
                      >
                        {visionHideCoords ? '🙈 Cego (Sem Bordas)' : '🔤 Com Bordas'}
                      </button>
                    </div>
                    <button
                      type="button"
                      onClick={startVisionDrill}
                      style={{
                        padding: '10px',
                        borderRadius: '8px',
                        border: 'none',
                        background: '#81b64c',
                        color: '#0f172a',
                        fontWeight: 900,
                        fontSize: '13px',
                        cursor: 'pointer',
                      }}
                    >
                      ⚡ INICIAR SPRINT DE VISÃO (30s)
                    </button>
                  </div>
                )}
              </div>

              <ChessBoardView
                fen={visionShowPieces ? STANDARD_START_FEN : EMPTY_BOARD_FEN}
                orientation={visionBoardSide}
                themeId={chessData.preferredTheme}
                interactive={visionActive}
                hideCoordinates={visionHideCoords}
                hidePieces={!visionShowPieces}
                badgeOverlay={
                  visionFeedback
                    ? {
                        square: visionFeedback.sq,
                        symbol: visionFeedback.ok ? '✓' : '✕',
                        bgColor: visionFeedback.ok ? '#16a34a' : '#dc2626',
                      }
                    : null
                }
                onSquareTap={visionActive ? handleVisionSquareTap : undefined}
                onMove={() => false}
              />
            </>
          )}

          {/* SUB-MODO B: 8 FINAIS ESSENCIAIS CONTRA O MOTOR 2400 ELO */}
          {trainMode === 'FINAIS' && (
            <div
              className="glass-card"
              style={{
                maxWidth: '470px',
                width: '100%',
                margin: '0 auto',
                padding: '12px',
                boxSizing: 'border-box',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 900, color: '#fde68a' }}>
                👑 Finais Fundamentais vs Defesa Máxima (2400 Elo)
              </div>
              <div style={{ fontSize: '11.5px', color: '#cbd5e1', lineHeight: 1.4 }}>
                Capablanca ensinava: estude primeiro os finais! Converta vitórias técnicas ou segure fortalezas teóricas jogando ao vivo contra o motor.
              </div>
              {CHESS_ENDGAME_DRILLS.map((drill) => {
                const done = (chessData.completedEndgameIds ?? []).includes(drill.id);
                return (
                  <div
                    key={drill.id}
                    style={{
                      padding: '10px',
                      borderRadius: '9px',
                      background: done
                        ? 'rgba(129, 182, 76, 0.12)'
                        : 'rgba(255,255,255,0.04)',
                      border: done
                        ? '1px solid rgba(129, 182, 76, 0.45)'
                        : '1px solid rgba(255,255,255,0.1)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '6px' }}>
                      <div style={{ fontSize: '12.5px', fontWeight: 900, color: '#f8fafc' }}>
                        {done ? '✅ ' : '♟️ '}
                        {drill.titlePt}
                      </div>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 800,
                          padding: '2px 6px',
                          borderRadius: '999px',
                          background: 'rgba(255,255,255,0.1)',
                          color: '#fde68a',
                        }}
                      >
                        {drill.difficultyLabel}
                      </span>
                    </div>
                    <div style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '4px', lineHeight: 1.38 }}>
                      {drill.principleSummaryPt}
                    </div>
                    <div style={{ marginTop: '7px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '10.5px', color: '#94a3b8', fontWeight: 700 }}>
                        Meta: {drill.goalType === 'WIN' ? 'Dar Xeque-Mate' : 'Segurar o Empate'} ({drill.userColor === 'w' ? '♔ Brancas' : '♚ Pretas'})
                      </span>
                      <button
                        type="button"
                        onClick={() => launchEndgameDrillMatch(drill)}
                        style={{
                          padding: '5px 10px',
                          borderRadius: '7px',
                          border: 'none',
                          background: '#81b64c',
                          color: '#0f172a',
                          fontWeight: 900,
                          fontSize: '11px',
                          cursor: 'pointer',
                        }}
                      >
                        ⚔️ Praticar no Tabuleiro
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* SUB-MODO C: 6 AULAS INTERATIVAS GUIADAS PASSO A PASSO */}
          {trainMode === 'AULAS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div
                className="glass-card"
                style={{
                  maxWidth: '470px',
                  width: '100%',
                  margin: '0 auto',
                  padding: '12px',
                  boxSizing: 'border-box',
                }}
              >
                <div style={{ display: 'flex', gap: '5px', overflowX: 'auto', paddingBottom: '6px' }}>
                  {CHESS_ACADEMY_LESSONS.map((les, idx) => {
                    const done = (chessData.completedAcademyIds ?? []).includes(les.id);
                    const sel = les.id === activeLesson.id;
                    return (
                      <button
                        key={les.id}
                        type="button"
                        onClick={() => selectAcademyLesson(les)}
                        style={{
                          flexShrink: 0,
                          padding: '5px 9px',
                          borderRadius: '7px',
                          border: sel
                            ? '1.5px solid #81b64c'
                            : '1px solid rgba(255,255,255,0.12)',
                          background: sel
                            ? 'rgba(129,182,76,0.22)'
                            : 'rgba(255,255,255,0.04)',
                          color: '#f8fafc',
                          fontSize: '11px',
                          fontWeight: 800,
                          cursor: 'pointer',
                        }}
                      >
                        {done ? '✅ ' : ''}Aula {idx + 1}
                      </button>
                    );
                  })}
                </div>

                <div style={{ marginTop: '6px' }}>
                  <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#81b64c' }}>
                    {activeLesson.tierLabel} • Passo {lessonStepIdx + 1}/{activeLesson.steps.length}
                  </div>
                  <div style={{ fontSize: '13.5px', fontWeight: 900, color: '#f8fafc', marginTop: '2px' }}>
                    {activeLesson.titlePt}
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#cbd5e1', marginTop: '3px', lineHeight: 1.4 }}>
                    {activeLesson.conceptSummaryPt}
                  </div>
                  <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '3px', fontStyle: 'italic' }}>
                    📚 {activeLesson.scientificNotePt}
                  </div>
                </div>
              </div>

              <ChessBoardView
                fen={lessonBoardFen}
                orientation={new Chess(activeLesson.steps[lessonStepIdx].fen).turn()}
                themeId={chessData.preferredTheme}
                interactive={!lessonStepSolved}
                allowedMoveColor={new Chess(activeLesson.steps[lessonStepIdx].fen).turn()}
                hintSquares={lessonHintSq}
                arrowDrawMode={arrowDrawMode}
                onMove={handleAcademyMove}
              />

              <div
                className="glass-card"
                style={{
                  maxWidth: '470px',
                  width: '100%',
                  margin: '0 auto',
                  padding: '12px',
                  boxSizing: 'border-box',
                }}
              >
                <div
                  style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    color: lessonStepSolved ? '#86efac' : '#fde68a',
                    lineHeight: 1.45,
                  }}
                >
                  {lessonCoachMsg}
                </div>
                <div style={{ marginTop: '9px', display: 'flex', justifyContent: 'space-between', gap: '6px' }}>
                  {!lessonStepSolved ? (
                    <button
                      type="button"
                      onClick={() => {
                        const lan = activeLesson.steps[lessonStepIdx]?.expectedLan[0];
                        if (lan) {
                          setLessonHintSq({
                            from: lan.slice(0, 2) as Square,
                            to: lan.slice(2, 4) as Square,
                          });
                        }
                      }}
                      style={navBtnStyle}
                    >
                      💡 Mostrar Casa Alvo
                    </button>
                  ) : lessonStepIdx < activeLesson.steps.length - 1 ? (
                    <button
                      type="button"
                      onClick={() => {
                        const nextIdx = lessonStepIdx + 1;
                        setLessonStepIdx(nextIdx);
                        setLessonStepSolved(false);
                        setLessonBoardFen(activeLesson.steps[nextIdx].fen);
                        setLessonCoachMsg(activeLesson.steps[nextIdx].instructionPt);
                        setLessonHintSq(null);
                      }}
                      style={{
                        width: '100%',
                        padding: '9px',
                        borderRadius: '8px',
                        border: 'none',
                        background: '#81b64c',
                        color: '#0f172a',
                        fontWeight: 900,
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      Próximo Passo da Aula ▶
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        const curIdx = CHESS_ACADEMY_LESSONS.findIndex(
                          (l) => l.id === activeLesson.id,
                        );
                        const nextLesson =
                          CHESS_ACADEMY_LESSONS[
                            (curIdx + 1) % CHESS_ACADEMY_LESSONS.length
                          ];
                        selectAcademyLesson(nextLesson);
                      }}
                      style={{
                        width: '100%',
                        padding: '9px',
                        borderRadius: '8px',
                        border: 'none',
                        background: '#81b64c',
                        color: '#0f172a',
                        fontWeight: 900,
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      🏆 Aula Concluída! Ir para Próxima Aula ▶
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODO 4: ANALISE MULTI-PV + EXPLORADOR DE ABERTURAS ECO + PGN/FEN     */}
      {/* ==================================================================== */}
      {subTab === 'ANALISE' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <ChessBoardView
            fen={analysisFen}
            orientation={analysisOrientation}
            themeId={chessData.preferredTheme}
            interactive={true}
            allowedMoveColor="both"
            lastMove={
              analysisMoves.length > 0
                ? {
                    from: analysisMoves[analysisMoves.length - 1].from,
                    to: analysisMoves[analysisMoves.length - 1].to,
                  }
                : null
            }
            engineArrows={analysisArrows}
            showEvalBar={true}
            evalWhiteCp={
              multiPvLines[0]?.evalWhiteCp ??
              evaluatePositionWhiteCp(analysisChess)
            }
            mateInMoves={multiPvLines[0]?.mateInMoves ?? null}
            arrowDrawMode={arrowDrawMode}
            onMove={handleAnalysisMove}
          />

          {/* Painel Multi-PV (3 Melhores Linhas em Tempo Real) */}
          <div
            className="glass-card"
            style={{
              maxWidth: '470px',
              width: '100%',
              margin: '0 auto',
              padding: '12px',
              boxSizing: 'border-box',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '6px' }}>
              <span style={{ fontSize: '12px', fontWeight: 900, color: '#81b64c' }}>
                🧠 Motor Multi-PV (3 Linhas Principais)
              </span>
              <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() =>
                    setAnalysisMoves((prev) => prev.slice(0, prev.length - 1))
                  }
                  style={navBtnStyle}
                >
                  ↩️ Voltar
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setAnalysisRootFen(new Chess().fen());
                    setAnalysisMoves([]);
                  }}
                  style={navBtnStyle}
                >
                  ♻️ Resetar
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setAnalysisOrientation((o) => (o === 'w' ? 'b' : 'w'))
                  }
                  style={navBtnStyle}
                >
                  🔄 Girar
                </button>
                <button
                  type="button"
                  onClick={() => setShowImportBox((v) => !v)}
                  style={navBtnStyle}
                >
                  📥 Importar FEN/PGN
                </button>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard?.writeText(analysisFen);
                    showToast('FEN copiado para a área de transferência!');
                  }}
                  style={navBtnStyle}
                >
                  📋 FEN
                </button>
                <button
                  type="button"
                  onClick={() =>
                    launchPlayFromCustomFen(
                      analysisFen,
                      'Posição do Explorador carregada contra o Motor!',
                    )
                  }
                  style={{
                    ...navBtnStyle,
                    border: '1px solid rgba(129,182,76,0.55)',
                    color: '#d9f99d',
                  }}
                >
                  ⚔️ Jogar daqui
                </button>
              </div>
            </div>

            {showImportBox && (
              <div style={{ marginBottom: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <textarea
                  value={importText}
                  onChange={(e) => setImportText(e.target.value)}
                  placeholder="Cole aqui qualquer código FEN ou partida PGN completa..."
                  rows={3}
                  style={{
                    width: '100%',
                    borderRadius: '8px',
                    padding: '8px',
                    background: '#0f172a',
                    color: '#f8fafc',
                    border: '1px solid rgba(255,255,255,0.2)',
                    fontSize: '11.5px',
                    boxSizing: 'border-box',
                  }}
                />
                <button
                  type="button"
                  onClick={handleImportFenOrPgn}
                  style={{
                    padding: '8px',
                    borderRadius: '7px',
                    border: 'none',
                    background: '#81b64c',
                    color: '#0f172a',
                    fontWeight: 900,
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  Carregar no Tabuleiro
                </button>
              </div>
            )}

            {multiPvLines.length === 0 ? (
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                Posição encerrada ({analysisChess.isCheckmate() ? 'Xeque-mate' : 'Empate'}).
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {multiPvLines.map((line, idx) => {
                  const scoreStr =
                    line.mateInMoves !== null
                      ? `M${Math.abs(line.mateInMoves)}`
                      : `${line.evalWhiteCp >= 0 ? '+' : ''}${(
                          line.evalWhiteCp / 100
                        ).toFixed(2)}`;
                  return (
                    <div
                      key={line.moveLan}
                      onClick={() =>
                        handleAnalysisMove(line.from, line.to, line.promotion)
                      }
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 8px',
                        borderRadius: '7px',
                        background: 'rgba(255,255,255,0.04)',
                        cursor: 'pointer',
                        fontSize: '11.5px',
                      }}
                    >
                      <span
                        style={{
                          padding: '2px 6px',
                          borderRadius: '5px',
                          fontFamily: 'monospace',
                          fontWeight: 900,
                          background:
                            line.evalWhiteCp >= 0 ? '#f8fafc' : '#1e293b',
                          color: line.evalWhiteCp >= 0 ? '#0f172a' : '#f8fafc',
                          minWidth: '46px',
                          textAlign: 'center',
                        }}
                      >
                        {scoreStr}
                      </span>
                      <span style={{ color: '#e2e8f0', fontWeight: 700 }}>
                        #{idx + 1} {line.pvSan.join(' ')}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Explorador de Aberturas ECO (48 Aberturas + Continuacoes Teoricas) */}
          <div
            className="glass-card"
            style={{
              maxWidth: '470px',
              width: '100%',
              margin: '0 auto',
              padding: '12px',
              boxSizing: 'border-box',
            }}
          >
            <div style={{ fontSize: '12.5px', fontWeight: 900, color: '#fed7aa' }}>
              📖 {analysisOpening.eco} — {analysisOpening.namePt}
            </div>
            <div style={{ fontSize: '11.5px', color: '#cbd5e1', marginTop: '3px' }}>
              {analysisOpening.ideaPt}
            </div>

            {analysisOpening.nextBookCandidates.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <div style={{ fontSize: '10.5px', fontWeight: 800, color: '#94a3b8', marginBottom: '5px' }}>
                  CONTINUAÇÕES DE MESTRE NESTA POSIÇÃO:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  {analysisOpening.nextBookCandidates.slice(0, 5).map((cand) => (
                    <button
                      key={cand.san}
                      type="button"
                      onClick={() => {
                        const g = new Chess(analysisFen);
                        const m = g.move(cand.san);
                        if (m) {
                          setAnalysisMoves((prev) => [...prev, m]);
                          playSoundForVerboseMove(m, g);
                        }
                      }}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '6px 9px',
                        borderRadius: '7px',
                        border: '1px solid rgba(255,255,255,0.1)',
                        background: 'rgba(255,255,255,0.04)',
                        color: '#f8fafc',
                        fontSize: '11.5px',
                        cursor: 'pointer',
                      }}
                    >
                      <span>
                        <strong>{cand.san}</strong> — {cand.openingNamePt} ({cand.eco})
                      </span>
                      <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                        ♔{cand.whiteWinPct}% • ={cand.drawPct}% • ♚{cand.blackWinPct}%
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Busca na Enciclopedia Completa de 48 Aberturas ECO */}
            <div style={{ marginTop: '12px', borderTop: '1px solid rgba(255,255,255,0.09)', paddingTop: '10px' }}>
              <input
                type="text"
                value={openingFilter}
                onChange={(e) => setOpeningFilter(e.target.value)}
                placeholder="🔎 Buscar abertura ECO (ex: Siciliana, Ruy Lopez, Londres, Catalã)..."
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.16)',
                  background: '#0f172a',
                  color: '#f8fafc',
                  fontSize: '11.5px',
                  boxSizing: 'border-box',
                  marginBottom: '8px',
                }}
              />
              <div
                style={{
                  maxHeight: '190px',
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '5px',
                }}
              >
                {OPENING_BOOK_LINES.filter((op) => {
                  const strip = (s: string) =>
                    s
                      .normalize('NFD')
                      .replace(/[\u0300-\u036f]/g, '')
                      .toLowerCase();
                  const q = strip(openingFilter.trim());
                  if (!q) return true;
                  return (
                    strip(op.namePt).includes(q) || strip(op.eco).includes(q)
                  );
                }).map((op) => (
                  <button
                    key={`${op.eco}-${op.namePt}`}
                    type="button"
                    onClick={() => {
                      const g = new Chess();
                      for (const s of op.movesSan) g.move(s);
                      setAnalysisRootFen(new Chess().fen());
                      setAnalysisMoves(g.history({ verbose: true }));
                      emitChessAudio('MOVE');
                    }}
                    style={{
                      textAlign: 'left',
                      padding: '7px 9px',
                      borderRadius: '7px',
                      border: '1px solid rgba(255,255,255,0.08)',
                      background: 'rgba(255,255,255,0.03)',
                      color: '#e2e8f0',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ fontSize: '11.5px', fontWeight: 800 }}>
                      <span style={{ color: '#81b64c' }}>{op.eco}</span> • {op.namePt}
                    </div>
                    <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '2px' }}>
                      {op.movesSan.join(' ')}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const navBtnStyle: React.CSSProperties = {
  padding: '5px 9px',
  borderRadius: '6px',
  border: '1px solid rgba(255,255,255,0.15)',
  background: 'rgba(255,255,255,0.06)',
  color: '#e2e8f0',
  fontSize: '11px',
  fontWeight: 800,
  cursor: 'pointer',
};

function subModeBtnStyle(active: boolean): React.CSSProperties {
  return {
    padding: '7px 6px',
    borderRadius: '7px',
    border: active ? '1.5px solid #81b64c' : '1px solid rgba(255,255,255,0.1)',
    background: active ? 'rgba(129,182,76,0.22)' : 'rgba(255,255,255,0.04)',
    color: active ? '#ecfccb' : '#cbd5e1',
    fontSize: '11.5px',
    fontWeight: 800,
    cursor: 'pointer',
  };
}
