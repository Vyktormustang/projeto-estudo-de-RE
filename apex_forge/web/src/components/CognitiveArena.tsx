import React, { useEffect, useRef, useState } from 'react';
import {
  Award,
  Brain,
  Calculator,
  CheckCircle2,
  Cpu,
  Grid,
  HelpCircle,
  Landmark,
  Play,
  RotateCcw,
  Scale,
  Target,
  Timer,
  Zap,
} from 'lucide-react';
import {
  CalibrationConfidencePct,
  computeBrierRoundPoints,
  generateCorsiSequence,
  generateLociDeck,
  generateLogicQuestion,
  generateNBackSequence,
  generateNumeracyQuestion,
  generateStroopTrial,
  generateTetlockCalibrationQuestion,
  generateTrailShiftingBoard,
  generateWisdomDiscernmentQuestion,
  getWordsPool,
  LociDeck,
  LogicPuzzle,
  MatrixCellSpec,
  NBackSequenceSpec,
  NumeracyPuzzle,
  StroopTrial,
  TetlockCalibrationPuzzle,
  TrailShiftingBoard,
  WisdomDiscernmentPuzzle,
} from '../engine/cognitiveGenerator';
import { CognitiveChallengeLog, CognitiveChallengeType } from '../engine/types';
import { playTacticalChime } from '../services/audioBiofeedback';
import { triggerHaptic } from '../services/vaultStorage';

interface Props {
  bioDayId: string;
  logs: CognitiveChallengeLog[];
  onSaveLog: (log: CognitiveChallengeLog) => void;
}

const MatrixCellSvg: React.FC<{ spec: MatrixCellSpec | null; size?: number }> = ({
  spec,
  size = 54,
}) => {
  if (!spec) {
    return (
      <div
        style={{
          width: size,
          height: size,
          borderRadius: 10,
          border: '2px dashed var(--amber)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--amber)',
          fontWeight: 900,
          fontSize: 18,
          background: 'rgba(245,158,11,0.08)',
        }}
      >
        ?
      </div>
    );
  }

  const positions =
    spec.count === 1
      ? [[27, 27]]
      : spec.count === 2
        ? [
            [18, 27],
            [36, 27],
          ]
        : [
            [27, 16],
            [17, 35],
            [37, 35],
          ];

  const fillStyle =
    spec.fill === 'SOLID'
      ? '#f59e0b'
      : spec.fill === 'HALF'
        ? 'rgba(6, 182, 212, 0.42)'
        : 'transparent';
  const strokeColor = spec.fill === 'HALF' ? '#22d3ee' : '#f59e0b';

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 54 54"
      style={{
        background: 'var(--bg-input)',
        borderRadius: 10,
        border: '1px solid var(--border-subtle)',
      }}
    >
      {positions.map(([cx, cy], idx) => {
        if (spec.shape === 'CIRCLE') {
          return (
            <circle
              key={idx}
              cx={cx}
              cy={cy}
              r={7}
              fill={fillStyle}
              stroke={strokeColor}
              strokeWidth="2.2"
            />
          );
        }
        if (spec.shape === 'SQUARE') {
          return (
            <rect
              key={idx}
              x={cx - 6.5}
              y={cy - 6.5}
              width={13}
              height={13}
              rx={2}
              fill={fillStyle}
              stroke={strokeColor}
              strokeWidth="2.2"
            />
          );
        }
        return (
          <polygon
            key={idx}
            points={`${cx},${cy - 7.5} ${cx - 7},${cy + 6.5} ${cx + 7},${cy + 6.5}`}
            fill={fillStyle}
            stroke={strokeColor}
            strokeWidth="2.2"
          />
        );
      })}
    </svg>
  );
};

export const CognitiveArena: React.FC<Props> = ({ bioDayId, logs, onSaveLog }) => {
  const [selectedGame, setSelectedGame] = useState<CognitiveChallengeType>('LOGICA_MATRIZES');
  const [difficulty, setDifficulty] = useState<1 | 2 | 3>(2);
  const [lastSummary, setLastSummary] = useState<{
    title: string;
    score: number;
    detail: string;
  } | null>(null);

  // ================= 1. STROOP STATE =================
  const [stroopActive, setStroopActive] = useState(false);
  const [stroopRound, setStroopRound] = useState(0);
  const [stroopCorrect, setStroopCorrect] = useState(0);
  const [stroopTrial, setStroopTrial] = useState<StroopTrial | null>(null);
  const stroopStartMs = useRef<number>(0);
  const stroopRts = useRef<number[]>([]);
  const STROOP_TOTAL = 16;

  // ================= 2. LOGIC & MATRICES STATE =================
  const [logicActive, setLogicActive] = useState(false);
  const [logicRound, setLogicRound] = useState(0);
  const [logicCorrect, setLogicCorrect] = useState(0);
  const [logicPuzzle, setLogicPuzzle] = useState<LogicPuzzle | null>(null);
  const [logicFeedback, setLogicFeedback] = useState<{
    ok: boolean;
    explanation: string;
  } | null>(null);
  const logicStartMs = useRef<number>(0);
  const logicRts = useRef<number[]>([]);
  const LOGIC_TOTAL = 8;

  // ================= 3. CORSI VISUOSPACIAL STATE =================
  const [corsiActive, setCorsiActive] = useState(false);
  const [corsiReverse, setCorsiReverse] = useState(true);
  const [corsiPhase, setCorsiPhase] = useState<'SHOWING' | 'INPUT'>('SHOWING');
  const [corsiSpan, setCorsiSpan] = useState(3);
  const [corsiMaxSpan, setCorsiMaxSpan] = useState(0);
  const [corsiSeq, setCorsiSeq] = useState<number[]>([]);
  const [corsiHighlight, setCorsiHighlight] = useState<number | null>(null);
  const [corsiUserClicks, setCorsiUserClicks] = useState<number[]>([]);
  const corsiTimersRef = useRef<number[]>([]);

  // ================= 4. METHOD OF LOCI (MEMORY PALACE) STATE =================
  const [lociPhase, setLociPhase] = useState<'IDLE' | 'ENCODE' | 'INTERFERENCE' | 'RECALL'>('IDLE');
  const [lociDeck, setLociDeck] = useState<LociDeck | null>(null);
  const [lociEncodeIdx, setLociEncodeIdx] = useState(0);
  const [lociRecallIdx, setLociRecallIdx] = useState(0);
  const [lociCorrectCount, setLociCorrectCount] = useState(0);
  const [lociRecallChoices, setLociRecallChoices] = useState<string[]>([]);
  const [lociMathError, setLociMathError] = useState(false);

  // ================= 5. NUMERACY, BAYES & FERMI STATE =================
  const [numActive, setNumActive] = useState(false);
  const [numRound, setNumRound] = useState(0);
  const [numCorrect, setNumCorrect] = useState(0);
  const [numPuzzle, setNumPuzzle] = useState<NumeracyPuzzle | null>(null);
  const [numFeedback, setNumFeedback] = useState<{ ok: boolean; shortcut: string } | null>(null);
  const numStartMs = useRef<number>(0);
  const numRts = useRef<number[]>([]);
  const NUM_TOTAL = 6;

  // ================= 6. DISCERNIMENTO, ANTIVIESES & SABEDORIA STATE =================
  const [wisActive, setWisActive] = useState(false);
  const [wisRound, setWisRound] = useState(0);
  const [wisCorrect, setWisCorrect] = useState(0);
  const [wisPuzzle, setWisPuzzle] = useState<WisdomDiscernmentPuzzle | null>(null);
  const [wisFeedback, setWisFeedback] = useState<{ ok: boolean; anchor: string } | null>(null);
  const wisStartMs = useRef<number>(0);
  const wisRts = useRef<number[]>([]);
  const WIS_TOTAL = 5;

  // ================= 7. CALIBRACAO BAYESIANA & BRIER (TETLOCK) STATE =================
  const [calActive, setCalActive] = useState(false);
  const [calRound, setCalRound] = useState(0);
  const [calCorrect, setCalCorrect] = useState(0);
  const [calPointsSum, setCalPointsSum] = useState(0);
  const [calPickedIdx, setCalPickedIdx] = useState<0 | 1 | null>(null);
  const [calPuzzle, setCalPuzzle] = useState<TetlockCalibrationPuzzle | null>(null);
  const [calFeedback, setCalFeedback] = useState<{
    ok: boolean;
    confidence: CalibrationConfidencePct;
    roundPoints: number;
    explanation: string;
  } | null>(null);
  const calStartMs = useRef<number>(0);
  const calRts = useRef<number[]>([]);
  const CAL_TOTAL = 6;

  // --- Estado Jogo 8: Atualizacao Executiva N-Back (Kirchner, 1958; Baddeley, 2000) ---
  const [nBackActive, setNBackActive] = useState(false);
  const [nBackData, setNBackData] = useState<NBackSequenceSpec | null>(null);
  const [nBackIndex, setNBackIndex] = useState(0);
  const [nBackCorrect, setNBackCorrect] = useState(0);
  const [nBackScoredCount, setNBackScoredCount] = useState(0);
  const [nBackLastHit, setNBackLastHit] = useState<boolean | null>(null);
  const nBackStartMs = useRef<number>(0);
  const nBackRts = useRef<number[]>([]);

  // --- Estado Jogo 9: Trilha Alternada 1-A-2-B (Miyake Shifting, 2000; Trail Making B) ---
  const [trailActive, setTrailActive] = useState(false);
  const [trailBoard, setTrailBoard] = useState<TrailShiftingBoard | null>(null);
  const [trailNextOrder, setTrailNextOrder] = useState(0);
  const [trailErrors, setTrailErrors] = useState(0);
  const trailStartMs = useRef<number>(0);

  const clearCorsiTimers = () => {
    for (const id of corsiTimersRef.current) {
      window.clearTimeout(id);
    }
    corsiTimersRef.current = [];
  };

  useEffect(() => {
    return () => {
      clearCorsiTimers();
    };
  }, []);

  const recordFinishedChallenge = (
    challengeType: CognitiveChallengeType,
    score: number,
    accuracyPct: number,
    detail: string,
    avgReactionMs?: number,
    maxSpanOrStreak?: number,
  ) => {
    const cleanScore = Math.max(0, Math.min(1000, Math.round(score)));
    playTacticalChime('VICTORY');
    triggerHaptic('success');

    onSaveLog({
      id: `cog_${Date.now()}`,
      bioDayId,
      timestampMs: Date.now(),
      challengeType,
      score: cleanScore,
      accuracyPct: Math.round(accuracyPct),
      avgReactionMs: avgReactionMs ? Math.round(avgReactionMs) : undefined,
      maxSpanOrStreak,
      difficultyTier: difficulty,
    });

    const titles: Record<CognitiveChallengeType, string> = {
      STROOP_INIBICAO: 'Controle Inibitório Stroop',
      LOGICA_MATRIZES: 'Raciocínio Lógico & Matrizes',
      CORSI_VISUOESPACIAL: 'Memória Visuoespacial Corsi',
      PALACIO_LOCI: 'Palácio da Memória (Loci)',
      NUMERACIA_FERMI: 'Matemática Mental & Probabilidade',
      DISCERNIMENTO_SABEDORIA: 'Discernimento, Antivieses & Sabedoria',
      CALIBRACAO_TETLOCK: 'Superprevisão & Calibração de Brier',
      NBACK_ATUALIZACAO: 'Memória de Trabalho N-Back Executivo',
      FLEXIBILIDADE_TRAIL: 'Trilha Alternada 1-A-2-B (Shifting)',
      FLANKER_ATENCAO: 'Flanker — Atenção Seletiva & Inibição',
      GO_NOGO_INIBICAO: 'Go/No-Go — Inibição de Resposta',
      DUAL_N_BACK: 'Dual N-Back — Memória de Trabalho Dupla',
      ATTENTION_CONTROL: 'Controle de Atenção (Posner Cueing)',
      REACTION_TIME: 'Tempo de Reação Simples & de Escolha',
      WORKING_MEMORY_SPAN: 'Span de Memória de Trabalho (Operation Span)',
    };
    setLastSummary({
      title: titles[challengeType],
      score: cleanScore,
      detail,
    });
  };

  // ---------------- STROOP HANDLERS ----------------
  const startStroop = () => {
    setLastSummary(null);
    stroopRts.current = [];
    setStroopRound(1);
    setStroopCorrect(0);
    setStroopActive(true);
    setStroopTrial(generateStroopTrial(Date.now(), difficulty));
    stroopStartMs.current = performance.now();
  };

  const answerStroop = (optIdx: number) => {
    if (!stroopTrial) return;
    const rt = performance.now() - stroopStartMs.current;
    stroopRts.current.push(rt);
    const isOk = optIdx === stroopTrial.correctIndex;
    triggerHaptic(isOk ? 'light' : 'heavy');
    const nextCorrect = stroopCorrect + (isOk ? 1 : 0);
    setStroopCorrect(nextCorrect);

    if (stroopRound >= STROOP_TOTAL) {
      setStroopActive(false);
      const avgRt =
        stroopRts.current.reduce((a, b) => a + b, 0) / Math.max(1, stroopRts.current.length);
      const acc = (nextCorrect / STROOP_TOTAL) * 100;
      const speedBonus = Math.max(0, 1450 - avgRt) * 0.35;
      const score = acc * 6.2 + (acc >= 70 ? speedBonus : 0);
      recordFinishedChallenge(
        'STROOP_INIBICAO',
        score,
        acc,
        `Precisão: ${Math.round(acc)}% (${nextCorrect}/${STROOP_TOTAL}) • Tempo Médio: ${Math.round(avgRt)} ms`,
        avgRt,
      );
      return;
    }

    const nextR = stroopRound + 1;
    setStroopRound(nextR);
    setStroopTrial(generateStroopTrial(Date.now() + nextR * 97, difficulty));
    stroopStartMs.current = performance.now();
  };

  // ---------------- LOGIC & MATRICES HANDLERS ----------------
  const startLogic = () => {
    setLastSummary(null);
    logicRts.current = [];
    setLogicRound(1);
    setLogicCorrect(0);
    setLogicFeedback(null);
    setLogicActive(true);
    setLogicPuzzle(generateLogicQuestion(Date.now(), difficulty));
    logicStartMs.current = performance.now();
  };

  const answerLogic = (optIdx: number) => {
    if (!logicPuzzle || logicFeedback) return;
    const rt = performance.now() - logicStartMs.current;
    logicRts.current.push(rt);
    const ok = optIdx === logicPuzzle.correctIndex;
    triggerHaptic(ok ? 'medium' : 'heavy');
    setLogicCorrect((c) => c + (ok ? 1 : 0));
    setLogicFeedback({ ok, explanation: logicPuzzle.explanation });
  };

  const nextLogicStep = () => {
    if (logicRound >= LOGIC_TOTAL) {
      setLogicActive(false);
      setLogicFeedback(null);
      const avgRt =
        logicRts.current.reduce((a, b) => a + b, 0) / Math.max(1, logicRts.current.length);
      const acc = (logicCorrect / LOGIC_TOTAL) * 100;
      const speedFactor = Math.max(0, 16000 - avgRt) * 0.018;
      const score = acc * 7.4 + (acc >= 60 ? speedFactor : 0);
      recordFinishedChallenge(
        'LOGICA_MATRIZES',
        score,
        acc,
        `Acertos: ${logicCorrect}/${LOGIC_TOTAL} (${Math.round(acc)}%) • Tempo Médio: ${(
          avgRt / 1000
        ).toFixed(1)}s`,
        avgRt,
      );
      return;
    }
    const nextR = logicRound + 1;
    setLogicRound(nextR);
    setLogicFeedback(null);
    setLogicPuzzle(generateLogicQuestion(Date.now() + nextR * 313, difficulty));
    logicStartMs.current = performance.now();
  };

  // ---------------- CORSI VISUOSPACIAL HANDLERS ----------------
  const playCorsiSequence = (spanLen: number) => {
    clearCorsiTimers();
    const gridSize = difficulty === 3 ? 4 : 3;
    const seq = generateCorsiSequence(spanLen, gridSize, Date.now() + spanLen * 41);
    setCorsiSeq(seq);
    setCorsiUserClicks([]);
    setCorsiHighlight(null);
    setCorsiPhase('SHOWING');

    const stepMs = difficulty === 1 ? 720 : difficulty === 2 ? 580 : 460;
    seq.forEach((cellIdx, i) => {
      const tOn = window.setTimeout(() => {
        setCorsiHighlight(cellIdx);
        triggerHaptic('light');
      }, i * stepMs + 250);
      const tOff = window.setTimeout(() => {
        setCorsiHighlight(null);
      }, i * stepMs + stepMs * 0.72 + 250);
      corsiTimersRef.current.push(tOn, tOff);
    });

    const tReady = window.setTimeout(
      () => {
        setCorsiHighlight(null);
        setCorsiPhase('INPUT');
      },
      seq.length * stepMs + 340,
    );
    corsiTimersRef.current.push(tReady);
  };

  const startCorsi = () => {
    setLastSummary(null);
    const startLen = difficulty === 1 ? 3 : 4;
    setCorsiSpan(startLen);
    setCorsiMaxSpan(0);
    setCorsiActive(true);
    playCorsiSequence(startLen);
  };

  const handleCorsiCellTap = (cellIdx: number) => {
    if (!corsiActive || corsiPhase !== 'INPUT') return;
    triggerHaptic('light');
    const targetOrder = corsiReverse ? [...corsiSeq].reverse() : corsiSeq;
    const pos = corsiUserClicks.length;

    if (cellIdx !== targetOrder[pos]) {
      // Fim da rodada: registra maior span alcancado!
      setCorsiActive(false);
      const best = Math.max(corsiMaxSpan, pos >= 2 ? pos : corsiSpan - 1);
      const score = Math.min(1000, best * (corsiReverse ? 145 : 120));
      const acc = Math.min(100, Math.round((best / 7) * 100));
      recordFinishedChallenge(
        'CORSI_VISUOESPACIAL',
        score,
        acc,
        `Span Máximo ${corsiReverse ? 'Inverso' : 'Direto'}: ${best} blocos consecutivos`,
        undefined,
        best,
      );
      return;
    }

    const updated = [...corsiUserClicks, cellIdx];
    setCorsiUserClicks(updated);

    if (updated.length === targetOrder.length) {
      const achieved = targetOrder.length;
      setCorsiMaxSpan(achieved);
      if (achieved >= 8) {
        setCorsiActive(false);
        recordFinishedChallenge(
          'CORSI_VISUOESPACIAL',
          1000,
          100,
          `Domínio Máximo Atingido: 8 blocos ${corsiReverse ? 'em Ordem Inversa!' : 'consecutivos!'}`,
          undefined,
          achieved,
        );
        return;
      }
      const nextSpan = achieved + 1;
      setCorsiSpan(nextSpan);
      playCorsiSequence(nextSpan);
    }
  };

  // ---------------- METHOD OF LOCI HANDLERS ----------------
  const buildLociRecallOptions = (deck: LociDeck, idx: number) => {
    const correctWord = deck.pairs[idx].targetWord;
    const pool = getWordsPool().filter((w) => w !== correctWord);
    const picks: string[] = [correctWord];
    let step = (idx * 7 + 3) % pool.length;
    while (picks.length < 4) {
      const cand = pool[step % pool.length];
      if (!picks.includes(cand)) picks.push(cand);
      step += 5;
    }
    return picks.sort();
  };

  const startLoci = () => {
    setLastSummary(null);
    const deck = generateLociDeck(difficulty, Date.now());
    setLociDeck(deck);
    setLociEncodeIdx(0);
    setLociRecallIdx(0);
    setLociCorrectCount(0);
    setLociPhase('ENCODE');
  };

  const handleLociAnswer = (word: string) => {
    if (!lociDeck) return;
    const isOk = word === lociDeck.pairs[lociRecallIdx].targetWord;
    triggerHaptic(isOk ? 'medium' : 'heavy');
    const nextCorrect = lociCorrectCount + (isOk ? 1 : 0);
    setLociCorrectCount(nextCorrect);

    if (lociRecallIdx + 1 >= lociDeck.pairs.length) {
      const total = lociDeck.pairs.length;
      const acc = (nextCorrect / total) * 100;
      const score = acc * (8.5 + difficulty * 0.5);
      setLociPhase('IDLE');
      recordFinishedChallenge(
        'PALACIO_LOCI',
        score,
        acc,
        `Evocação no Palácio: ${nextCorrect}/${total} estações lembradas na ordem exata (${Math.round(acc)}%)`,
        undefined,
        nextCorrect,
      );
      return;
    }

    const nextIdx = lociRecallIdx + 1;
    setLociRecallIdx(nextIdx);
    setLociRecallChoices(buildLociRecallOptions(lociDeck, nextIdx));
  };

  const startNumeracy = () => {
    setLastSummary(null);
    setNumFeedback(null);
    setNumCorrect(0);
    setNumRound(1);
    numRts.current = [];
    setNumPuzzle(generateNumeracyQuestion(Date.now(), difficulty));
    numStartMs.current = performance.now();
    setNumActive(true);
  };

  const handleNumeracyAnswer = (idx: number) => {
    if (!numPuzzle || numFeedback) return;
    const rt = Math.max(200, Math.round(performance.now() - numStartMs.current));
    numRts.current.push(rt);
    const isOk = idx === numPuzzle.correctIndex;
    triggerHaptic(isOk ? 'light' : 'heavy');
    setNumFeedback({ ok: isOk, shortcut: numPuzzle.mentalShortcut });
    if (isOk) setNumCorrect((c) => c + 1);
  };

  const advanceNumeracy = () => {
    const finalCorrect = numCorrect;
    if (numRound >= NUM_TOTAL) {
      setNumActive(false);
      setNumFeedback(null);
      const acc = (finalCorrect / NUM_TOTAL) * 100;
      const avgRt =
        numRts.current.reduce((a, b) => a + b, 0) / Math.max(1, numRts.current.length);
      const speedBonus = Math.max(0, Math.min(200, (14000 - avgRt) / 70));
      const score = acc * (7.2 + difficulty * 0.4) + (finalCorrect > 0 ? speedBonus : 0);
      recordFinishedChallenge(
        'NUMERACIA_FERMI',
        score,
        acc,
        `Numeracia & Probabilidade: ${finalCorrect}/${NUM_TOTAL} exatos • Tempo médio ${(avgRt / 1000).toFixed(1)}s`,
        Math.round(avgRt),
        finalCorrect,
      );
      return;
    }

    const nextR = numRound + 1;
    setNumRound(nextR);
    setNumFeedback(null);
    setNumPuzzle(generateNumeracyQuestion(Date.now() + nextR * 131, difficulty));
    numStartMs.current = performance.now();
  };

  // ---------------- DISCERNIMENTO & SABEDORIA HANDLERS ----------------
  const startWisdom = () => {
    setLastSummary(null);
    wisRts.current = [];
    setWisRound(1);
    setWisCorrect(0);
    setWisFeedback(null);
    setWisActive(true);
    setWisPuzzle(generateWisdomDiscernmentQuestion(Date.now(), difficulty));
    wisStartMs.current = performance.now();
  };

  const handleWisdomAnswer = (idx: number) => {
    if (!wisPuzzle || wisFeedback) return;
    const rt = Math.max(300, Math.round(performance.now() - wisStartMs.current));
    wisRts.current.push(rt);
    const isOk = idx === wisPuzzle.correctIndex;
    triggerHaptic(isOk ? 'light' : 'heavy');
    setWisFeedback({ ok: isOk, anchor: wisPuzzle.principleAnchor });
    if (isOk) setWisCorrect((c) => c + 1);
  };

  const advanceWisdom = () => {
    const finalCorrect = wisCorrect;
    if (wisRound >= WIS_TOTAL) {
      setWisActive(false);
      setWisFeedback(null);
      const acc = (finalCorrect / WIS_TOTAL) * 100;
      const avgRt =
        wisRts.current.reduce((a, b) => a + b, 0) / Math.max(1, wisRts.current.length);
      const speedBonus = Math.max(0, Math.min(180, (16000 - avgRt) / 85));
      const score = acc * (7.4 + difficulty * 0.4) + (finalCorrect > 0 ? speedBonus : 0);
      recordFinishedChallenge(
        'DISCERNIMENTO_SABEDORIA',
        score,
        acc,
        `Discernimento Crítico: ${finalCorrect}/${WIS_TOTAL} exatos • Tempo médio ${(avgRt / 1000).toFixed(1)}s`,
        Math.round(avgRt),
        finalCorrect,
      );
      return;
    }

    const nextR = wisRound + 1;
    setWisRound(nextR);
    setWisFeedback(null);
    setWisPuzzle(generateWisdomDiscernmentQuestion(Date.now() + nextR * 197, difficulty));
    wisStartMs.current = performance.now();
  };

  // ---------------- CALIBRACAO & BRIER (TETLOCK) HANDLERS ----------------
  const startCalibration = () => {
    setLastSummary(null);
    calRts.current = [];
    setCalRound(1);
    setCalCorrect(0);
    setCalPointsSum(0);
    setCalPickedIdx(null);
    setCalFeedback(null);
    setCalActive(true);
    setCalPuzzle(generateTetlockCalibrationQuestion(Date.now(), difficulty));
    calStartMs.current = performance.now();
  };

  const handleCalibrationCommit = (confidence: CalibrationConfidencePct) => {
    if (!calPuzzle || calPickedIdx === null || calFeedback) return;
    const rt = Math.max(300, Math.round(performance.now() - calStartMs.current));
    calRts.current.push(rt);
    const isOk = calPickedIdx === calPuzzle.correctIndex;
    const { roundPoints } = computeBrierRoundPoints(isOk, confidence);
    triggerHaptic(isOk ? 'light' : 'heavy');
    if (isOk) setCalCorrect((c) => c + 1);
    setCalPointsSum((s) => s + roundPoints);
    setCalFeedback({
      ok: isOk,
      confidence,
      roundPoints,
      explanation: calPuzzle.explanation,
    });
  };

  const advanceCalibration = () => {
    if (calRound >= CAL_TOTAL) {
      setCalActive(false);
      setCalFeedback(null);
      setCalPickedIdx(null);
      const acc = (calCorrect / CAL_TOTAL) * 100;
      const avgRt =
        calRts.current.reduce((a, b) => a + b, 0) / Math.max(1, calRts.current.length);
      recordFinishedChallenge(
        'CALIBRACAO_TETLOCK',
        calPointsSum,
        acc,
        `Calibração de Brier: ${calCorrect}/${CAL_TOTAL} acertos • Pontuação calibrada ${Math.min(1000, calPointsSum)}/1000`,
        Math.round(avgRt),
        calCorrect,
      );
      return;
    }

    const nextR = calRound + 1;
    setCalRound(nextR);
    setCalPickedIdx(null);
    setCalFeedback(null);
    setCalPuzzle(generateTetlockCalibrationQuestion(Date.now() + nextR * 251, difficulty));
    calStartMs.current = performance.now();
  };

  const bestScoreFor = (type: CognitiveChallengeType): number => {
    const matching = logs.filter((l) => l.challengeType === type);
    return matching.length > 0 ? Math.max(...matching.map((m) => m.score)) : 0;
  };

  // ---------------- N-BACK EXECUTIVO HANDLERS ----------------
  const startNBack = () => {
    setLastSummary(null);
    nBackRts.current = [];
    const seq = generateNBackSequence(Date.now(), difficulty);
    setNBackData(seq);
    setNBackIndex(0);
    setNBackCorrect(0);
    setNBackScoredCount(0);
    setNBackLastHit(null);
    setNBackActive(true);
    nBackStartMs.current = performance.now();
  };

  const handleNBackStep = (userSaysMatch: boolean | null) => {
    if (!nBackData) return;
    const { nBack, items } = nBackData;
    const current = items[nBackIndex];
    let nextCorrect = nBackCorrect;
    let nextScored = nBackScoredCount;

    if (nBackIndex >= nBack && userSaysMatch !== null) {
      const rt = Math.max(180, Math.round(performance.now() - nBackStartMs.current));
      nBackRts.current.push(rt);
      const ok = userSaysMatch === current.isTargetMatch;
      triggerHaptic(ok ? 'light' : 'heavy');
      if (ok) nextCorrect += 1;
      nextScored += 1;
      setNBackCorrect(nextCorrect);
      setNBackScoredCount(nextScored);
      setNBackLastHit(ok);
    }

    if (nBackIndex + 1 >= items.length) {
      setNBackActive(false);
      const acc = (nextCorrect / Math.max(1, nextScored)) * 100;
      const avgRt =
        nBackRts.current.reduce((a, b) => a + b, 0) / Math.max(1, nBackRts.current.length);
      const speedBonus = Math.max(0, Math.min(180, (2400 - avgRt) / 10));
      const score = acc * (7.2 + nBack * 0.45) + (acc >= 65 ? speedBonus : 0);
      recordFinishedChallenge(
        'NBACK_ATUALIZACAO',
        score,
        acc,
        `${nBack}-Back Executivo: ${nextCorrect}/${nextScored} exatos (${Math.round(acc)}%) • ${Math.round(avgRt)} ms`,
        Math.round(avgRt),
        nextCorrect,
      );
      return;
    }

    setNBackIndex((i) => i + 1);
    nBackStartMs.current = performance.now();
  };

  // ---------------- TRAIL MAKING B (SHIFTING) HANDLERS ----------------
  const startTrail = () => {
    setLastSummary(null);
    const board = generateTrailShiftingBoard(Date.now(), difficulty);
    setTrailBoard(board);
    setTrailNextOrder(0);
    setTrailErrors(0);
    setTrailActive(true);
    trailStartMs.current = performance.now();
  };

  const handleTrailTap = (sequenceOrder: number) => {
    if (!trailBoard || !trailActive) return;
    if (sequenceOrder < trailNextOrder) return; // ja concluido

    if (sequenceOrder !== trailNextOrder) {
      triggerHaptic('heavy');
      setTrailErrors((e) => e + 1);
      return;
    }

    triggerHaptic('light');
    const nextOrd = trailNextOrder + 1;
    if (nextOrd >= trailBoard.totalNodes) {
      setTrailActive(false);
      const totalMs = Math.max(1500, Math.round(performance.now() - trailStartMs.current));
      const avgPerNodeMs = Math.round(totalMs / trailBoard.totalNodes);
      const totalClicks = trailBoard.totalNodes + trailErrors;
      const acc = (trailBoard.totalNodes / Math.max(1, totalClicks)) * 100;
      const speedBonus = Math.max(0, Math.min(240, (2200 - avgPerNodeMs) / 6));
      const score = acc * (7.0 + difficulty * 0.35) + (acc >= 75 ? speedBonus : 0);
      recordFinishedChallenge(
        'FLEXIBILIDADE_TRAIL',
        score,
        acc,
        `Trilha 1-A-2-B (${trailBoard.totalNodes} nós): ${(totalMs / 1000).toFixed(1)}s • ${trailErrors} erro(s) de alternância`,
        avgPerNodeMs,
        trailBoard.totalNodes,
      );
      return;
    }

    setTrailNextOrder(nextOrd);
  };

  const isAnyRunning =
    stroopActive ||
    logicActive ||
    corsiActive ||
    lociPhase !== 'IDLE' ||
    numActive ||
    wisActive ||
    calActive ||
    nBackActive ||
    trailActive;

  return (
    <div className="card card-amber">
      <div className="section-header">
        <div>
          <div className="section-kicker">
            Arena Cognitiva Interativa • Psicometria &amp; Neurociência
          </div>
          <h2 className="section-title">Desafios de Raciocínio, Reflexo &amp; Memória</h2>
        </div>
        <Brain size={22} color="var(--amber)" />
      </div>

      <p className="muted" style={{ marginTop: 0, marginBottom: 12 }}>
        Sprints curtos de <strong>60 a 90 segundos</strong> que treinam estratégias reais de
        memorização (<em>Método de Loci</em> — <em>Neuron</em>, 2017) e medem sua velocidade lógica,
        foco inibitório e memória espacial sem gerar fadiga pré-treino (Dallaway et al., 2022).
      </p>

      {/* SELETOR DOS 4 DESAFIOS INTERATIVOS */}
      {!isAnyRunning && (
        <>
          <div className="grid-2" style={{ marginBottom: 12 }}>
            {[
              {
                id: 'LOGICA_MATRIZES' as const,
                title: 'Lógica & Matrizes 3×3',
                sub: 'Dedução rápida, sequências e Raven',
                Icon: Cpu,
              },
              {
                id: 'STROOP_INIBICAO' as const,
                title: 'Reflexo Stroop (ms)',
                sub: 'Foco sob conflito e velocidade',
                Icon: Zap,
              },
              {
                id: 'CORSI_VISUOESPACIAL' as const,
                title: 'Memória Espacial Corsi',
                sub: 'Grade luminosa direta e reversa',
                Icon: Grid,
              },
              {
                id: 'PALACIO_LOCI' as const,
                title: 'Palácio da Memória',
                sub: 'Técnica dos campeões mundiais',
                Icon: Landmark,
              },
              {
                id: 'NUMERACIA_FERMI' as const,
                title: 'Cálculo & Probabilidade',
                sub: 'Regra dos 72, Bayes e Escala Fermi',
                Icon: Calculator,
              },
              {
                id: 'DISCERNIMENTO_SABEDORIA' as const,
                title: 'Discernimento & Sabedoria',
                sub: 'Antivieses, Falácias e Prudência',
                Icon: Scale,
              },
              {
                id: 'CALIBRACAO_TETLOCK' as const,
                title: 'Calibração de Certeza (Brier)',
                sub: 'Superprevisão 55%–95% vs. Dunning-Kruger',
                Icon: Target,
              },
              {
                id: 'NBACK_ATUALIZACAO' as const,
                title: 'Memória N-Back (1/2/3-Back)',
                sub: 'Atualização executiva em fluxo contínuo',
                Icon: Timer,
              },
              {
                id: 'FLEXIBILIDADE_TRAIL' as const,
                title: 'Trilha Alternada 1-A-2-B (Shifting)',
                sub: 'Flexibilidade cognitiva e alternância rápida (Miyake, 2000)',
                Icon: RotateCcw,
              },
            ].map(({ id, title, sub, Icon }, idx, arr) => {
              const active = selectedGame === id;
              const best = bestScoreFor(id);
              const spanFull = idx === arr.length - 1 && arr.length % 2 === 1;
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => {
                    triggerHaptic('light');
                    setSelectedGame(id);
                  }}
                  style={{
                    gridColumn: spanFull ? '1 / -1' : undefined,
                    textAlign: 'left',
                    padding: 12,
                    borderRadius: 14,
                    background: active ? 'var(--amber-soft)' : 'var(--bg-elevated)',
                    border: active
                      ? '1.5px solid var(--amber)'
                      : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 4,
                    }}
                  >
                    <Icon size={18} color={active ? 'var(--amber)' : 'var(--cyan)'} />
                    {best > 0 && (
                      <span className="mono" style={{ fontSize: 11, color: '#34d399' }}>
                        Rec: {best}
                      </span>
                    )}
                  </div>
                  <div style={{ fontWeight: 800, fontSize: 13.5 }}>{title}</div>
                  <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>
                    {sub}
                  </div>
                </button>
              );
            })}
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 8,
              marginBottom: 14,
            }}
          >
            <span className="muted" style={{ fontSize: 12.5, fontWeight: 700 }}>
              Nível de Complexidade:
            </span>
            <div className="chip-row">
              {[
                { lv: 1 as const, label: '1 • Base' },
                { lv: 2 as const, label: '2 • Tático' },
                { lv: 3 as const, label: '3 • Ápice' },
              ].map((d) => (
                <button
                  key={d.lv}
                  type="button"
                  className={`chip ${difficulty === d.lv ? 'chip-active' : ''}`}
                  onClick={() => setDifficulty(d.lv)}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {selectedGame === 'CORSI_VISUOESPACIAL' && (
            <label className="check-toggle" style={{ marginBottom: 12 }}>
              <input
                type="checkbox"
                checked={corsiReverse}
                onChange={(e) => setCorsiReverse(e.target.checked)}
              />
              <div>
                <strong>Modo Ordem INVERSA (Backwards Corsi — Recomendado)</strong>
                <div className="muted">
                  Toque nos blocos de trás para frente: exige rotação ativa na memória de trabalho!
                </div>
              </div>
            </label>
          )}

          {lastSummary && (
            <div
              style={{
                padding: 13,
                borderRadius: 12,
                background: 'var(--emerald-soft)',
                border: '1px solid rgba(16,185,129,0.4)',
                marginBottom: 14,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>
                  <Award size={15} style={{ verticalAlign: 'middle' }} /> {lastSummary.title}
                </strong>
                <span className="badge badge-green">{lastSummary.score} pts</span>
              </div>
              <div className="muted" style={{ marginTop: 4, color: '#d1fae5' }}>
                {lastSummary.detail}
              </div>
            </div>
          )}

          <button
            type="button"
            className="btn btn-primary btn-block"
            onClick={() => {
              triggerHaptic('medium');
              if (selectedGame === 'STROOP_INIBICAO') startStroop();
              else if (selectedGame === 'LOGICA_MATRIZES') startLogic();
              else if (selectedGame === 'CORSI_VISUOESPACIAL') startCorsi();
              else if (selectedGame === 'NUMERACIA_FERMI') startNumeracy();
              else if (selectedGame === 'DISCERNIMENTO_SABEDORIA') startWisdom();
              else if (selectedGame === 'CALIBRACAO_TETLOCK') startCalibration();
              else if (selectedGame === 'NBACK_ATUALIZACAO') startNBack();
              else if (selectedGame === 'FLEXIBILIDADE_TRAIL') startTrail();
              else startLoci();
            }}
          >
            <Play size={17} /> Iniciar Desafio Agora
          </button>
        </>
      )}

      {/* ================= JOGO 1 ATIVO: STROOP ================= */}
      {stroopActive && stroopTrial && (
        <div
          style={{
            padding: 16,
            borderRadius: 14,
            background: 'var(--bg-elevated)',
            textAlign: 'center',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="badge badge-cyan">
              Rodada {stroopRound}/{STROOP_TOTAL}
            </span>
            <button
              type="button"
              className="chip"
              style={{ padding: '3px 9px', fontSize: 11 }}
              onClick={() => setStroopActive(false)}
            >
              <RotateCcw size={11} /> Sair
            </button>
          </div>

          <div
            style={{
              padding: '7px 12px',
              borderRadius: 999,
              display: 'inline-block',
              fontWeight: 800,
              fontSize: 12.5,
              background:
                stroopTrial.rule === 'COR_DA_TINTA' ? 'var(--amber-soft)' : 'var(--violet-soft)',
              color: stroopTrial.rule === 'COR_DA_TINTA' ? 'var(--amber)' : '#c4b5fd',
              marginBottom: 16,
            }}
          >
            {stroopTrial.rule === 'COR_DA_TINTA'
              ? 'TOQUE NA COR DA TINTA (Ignore o que está escrito!)'
              : 'TOQUE NO SIGNIFICADO ESCRITO (Ignore a cor da tinta!)'}
          </div>

          <div
            style={{
              fontSize: 36,
              fontWeight: 900,
              letterSpacing: '0.06em',
              color: stroopTrial.inkHex,
              padding: '22px 0',
              userSelect: 'none',
            }}
          >
            {stroopTrial.wordText}
          </div>

          <div className="grid-2" style={{ marginTop: 10 }}>
            {stroopTrial.options.map((opt, idx) => (
              <button
                key={opt}
                type="button"
                className="btn btn-ghost"
                style={{ fontWeight: 800, minHeight: 50 }}
                onClick={() => answerStroop(idx)}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ================= JOGO 2 ATIVO: LOGICA & MATRIZES ================= */}
      {logicActive && logicPuzzle && (
        <div style={{ padding: 14, borderRadius: 14, background: 'var(--bg-elevated)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="badge badge-cyan">
              Questão {logicRound}/{LOGIC_TOTAL}
            </span>
            <button
              type="button"
              className="chip"
              style={{ padding: '3px 9px', fontSize: 11 }}
              onClick={() => setLogicActive(false)}
            >
              <RotateCcw size={11} /> Sair
            </button>
          </div>

          <div style={{ fontSize: 14.5, fontWeight: 700, marginBottom: 14, lineHeight: 1.5 }}>
            {logicPuzzle.prompt}
          </div>

          {logicPuzzle.kind === 'RAVEN_MATRIX' && logicPuzzle.matrixGrid && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 56px)',
                gap: 8,
                justifyContent: 'center',
                marginBottom: 16,
              }}
            >
              {logicPuzzle.matrixGrid.map((cell, idx) => (
                <MatrixCellSvg key={idx} spec={cell} size={56} />
              ))}
            </div>
          )}

          {logicPuzzle.kind === 'RAVEN_MATRIX' && logicPuzzle.matrixOptions ? (
            <div className="grid-4" style={{ marginBottom: 12 }}>
              {logicPuzzle.matrixOptions.map((opt, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="btn btn-ghost"
                  disabled={Boolean(logicFeedback)}
                  style={{ padding: 8, height: 'auto' }}
                  onClick={() => answerLogic(idx)}
                >
                  <MatrixCellSvg spec={opt} size={50} />
                </button>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {logicPuzzle.textOptions?.map((txt, idx) => (
                <button
                  key={idx}
                  type="button"
                  disabled={Boolean(logicFeedback)}
                  className="btn btn-ghost"
                  style={{ justifyContent: 'flex-start', textAlign: 'left', height: 'auto' }}
                  onClick={() => answerLogic(idx)}
                >
                  <span className="mono" style={{ color: 'var(--amber)', marginRight: 6 }}>
                    {String.fromCharCode(65 + idx)}.
                  </span>{' '}
                  {txt}
                </button>
              ))}
            </div>
          )}

          {logicFeedback && (
            <div
              style={{
                marginTop: 14,
                padding: 12,
                borderRadius: 12,
                background: logicFeedback.ok ? 'var(--emerald-soft)' : 'var(--crimson-soft)',
                border: `1px solid ${logicFeedback.ok ? 'var(--emerald)' : 'var(--crimson)'}`,
              }}
            >
              <strong style={{ color: logicFeedback.ok ? '#34d399' : '#fca5a5' }}>
                {logicFeedback.ok ? '✓ Raciocínio Exato!' : '✗ Armadilha Detectada — Veja a Regra:'}
              </strong>
              <div style={{ fontSize: 13, marginTop: 4 }}>{logicFeedback.explanation}</div>
              <button
                type="button"
                className="btn btn-primary btn-block"
                style={{ marginTop: 10 }}
                onClick={nextLogicStep}
              >
                {logicRound >= LOGIC_TOTAL ? 'Ver Pontuação Final' : 'Próximo Desafio →'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ================= JOGO 3 ATIVO: CORSI VISUOESPACIAL ================= */}
      {corsiActive && (
        <div
          style={{
            padding: 16,
            borderRadius: 14,
            background: 'var(--bg-elevated)',
            textAlign: 'center',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span className="badge badge-cyan">Span Atual: {corsiSpan} blocos</span>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <span className="badge badge-yellow">
                {corsiReverse ? 'INVERSA' : 'DIRETA'}
              </span>
              <button
                type="button"
                className="chip"
                style={{ padding: '3px 9px', fontSize: 11 }}
                onClick={() => {
                  clearCorsiTimers();
                  setCorsiActive(false);
                }}
              >
                <RotateCcw size={11} /> Sair
              </button>
            </div>
          </div>

          <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 14 }}>
            {corsiPhase === 'SHOWING'
              ? 'Observe atentamente a sequência luminosa...'
              : corsiReverse
                ? `Toque na ORDEM INVERSA (do último ao primeiro)! (${corsiUserClicks.length}/${corsiSeq.length})`
                : `Repita na mesma ordem! (${corsiUserClicks.length}/${corsiSeq.length})`}
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${difficulty === 3 ? 4 : 3}, 66px)`,
              gap: 10,
              justifyContent: 'center',
              margin: '0 auto 12px',
            }}
          >
            {Array.from({ length: difficulty === 3 ? 16 : 9 }, (_, idx) => {
              const lit = corsiHighlight === idx;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleCorsiCellTap(idx)}
                  style={{
                    width: 66,
                    height: 66,
                    borderRadius: 14,
                    border: lit
                      ? '2px solid #fbbf24'
                      : '1px solid rgba(255,255,255,0.12)',
                    background: lit
                      ? 'radial-gradient(circle, #f59e0b 0%, #d97706 100%)'
                      : 'var(--bg-input)',
                    boxShadow: lit ? '0 0 22px rgba(245,158,11,0.65)' : 'none',
                    cursor: corsiPhase === 'INPUT' ? 'pointer' : 'default',
                    transition: 'all 0.12s ease',
                  }}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* ================= JOGO 4 ATIVO: PALACIO DA MEMORIA (LOCI) ================= */}
      {lociPhase !== 'IDLE' && lociDeck && (
        <div style={{ padding: 16, borderRadius: 14, background: 'var(--bg-elevated)' }}>
          {lociPhase === 'ENCODE' && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span className="badge badge-cyan">
                  Estação {lociEncodeIdx + 1} de {lociDeck.pairs.length}
                </span>
                <span className="muted" style={{ fontSize: 12 }}>
                  Crie uma cena viva e absurda!
                </span>
              </div>

              <div
                style={{
                  padding: 16,
                  borderRadius: 14,
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-strong)',
                  textAlign: 'center',
                  marginBottom: 14,
                }}
              >
                <div className="section-kicker">{lociDeck.pairs[lociEncodeIdx].stationName}</div>
                <div className="muted" style={{ fontSize: 12.5, marginBottom: 10 }}>
                  {lociDeck.pairs[lociEncodeIdx].stationCue}
                </div>
                <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--amber)' }}>
                  {lociDeck.pairs[lociEncodeIdx].targetWord}
                </div>
                <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
                  Visualize <strong>{lociDeck.pairs[lociEncodeIdx].targetWord}</strong> interagindo
                  fisicamente neste local!
                </div>
              </div>

              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={() => {
                  triggerHaptic('light');
                  if (lociEncodeIdx + 1 < lociDeck.pairs.length) {
                    setLociEncodeIdx((i) => i + 1);
                  } else {
                    setLociPhase('INTERFERENCE');
                  }
                }}
              >
                {lociEncodeIdx + 1 < lociDeck.pairs.length
                  ? 'Próxima Estação do Palácio →'
                  : 'Ir para Teste de Retenção Real →'}
              </button>
            </>
          )}

          {lociPhase === 'INTERFERENCE' && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
                  <Timer size={13} style={{ verticalAlign: 'middle' }} /> Etapa Científica de
                  Desbloqueio Hipocampal
                </div>
                <button
                  type="button"
                  className="chip"
                  style={{ padding: '3px 9px', fontSize: 11 }}
                  onClick={() => setLociPhase('IDLE')}
                >
                  <RotateCcw size={11} /> Sair
                </button>
              </div>
              <p style={{ fontSize: 14, fontWeight: 700 }}>{lociDeck.interferencePrompt}</p>
              {lociMathError && (
                <div style={{ fontSize: 12.5, color: '#fca5a5', marginBottom: 8 }}>
                  Calcule o resultado exato da subtração para avançar à evocação!
                </div>
              )}
              <div className="grid-2">
                {lociDeck.interferenceOptions.map((opt, optIdx) => (
                  <button
                    key={opt}
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => {
                      if (optIdx !== lociDeck.interferenceCorrectIndex) {
                        triggerHaptic('heavy');
                        setLociMathError(true);
                        return;
                      }
                      triggerHaptic('light');
                      setLociMathError(false);
                      setLociRecallIdx(0);
                      setLociRecallChoices(buildLociRecallOptions(lociDeck, 0));
                      setLociPhase('RECALL');
                    }}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </>
          )}

          {lociPhase === 'RECALL' && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span className="badge badge-green">
                  Evocação {lociRecallIdx + 1}/{lociDeck.pairs.length}
                </span>
                <span className="mono muted" style={{ fontSize: 12 }}>
                  Acertos: {lociCorrectCount}
                </span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                Caminhe mentalmente até esta estação:
              </div>
              <h3 className="section-title" style={{ margin: '4px 0 4px' }}>
                {lociDeck.pairs[lociRecallIdx].stationName}
              </h3>
              <div className="muted" style={{ marginBottom: 14, fontSize: 12.5 }}>
                ({lociDeck.pairs[lociRecallIdx].stationCue}) — Qual objeto você deixou aqui?
              </div>

              <div className="grid-2">
                {lociRecallChoices.map((word) => (
                  <button
                    key={word}
                    type="button"
                    className="btn btn-ghost"
                    style={{ fontWeight: 800 }}
                    onClick={() => handleLociAnswer(word)}
                  >
                    {word}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* ================= JOGO 5 ATIVO: NUMERACIA, BAYES & FERMI ================= */}
      {numActive && numPuzzle && (
        <div style={{ padding: 16, borderRadius: 14, background: 'var(--bg-elevated)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="badge badge-cyan">
              Questão {numRound}/{NUM_TOTAL}
            </span>
            <button
              type="button"
              className="chip"
              style={{ padding: '3px 9px', fontSize: 11 }}
              onClick={() => setNumActive(false)}
            >
              <RotateCcw size={11} /> Sair
            </button>
          </div>

          <div
            style={{
              padding: 13,
              borderRadius: 12,
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              fontSize: 14,
              fontWeight: 600,
              lineHeight: 1.5,
              marginBottom: 12,
            }}
          >
            {numPuzzle.prompt}
          </div>

          <div className="grid-2" style={{ marginBottom: 10 }}>
            {numPuzzle.options.map((opt, idx) => {
              let bg = 'var(--bg-input)';
              let border = '1px solid var(--border-subtle)';
              if (numFeedback) {
                if (idx === numPuzzle.correctIndex) {
                  bg = 'var(--emerald-soft)';
                  border = '1.5px solid var(--emerald)';
                }
              }
              return (
                <button
                  key={opt}
                  type="button"
                  disabled={Boolean(numFeedback)}
                  onClick={() => handleNumeracyAnswer(idx)}
                  style={{
                    padding: '11px 10px',
                    borderRadius: 12,
                    background: bg,
                    border,
                    color: 'var(--text-primary)',
                    fontWeight: 800,
                    fontSize: 13.5,
                    cursor: numFeedback ? 'default' : 'pointer',
                  }}
                >
                  {opt}
                </button>
              );
            })}
          </div>

          {numFeedback && (
            <div
              style={{
                padding: 12,
                borderRadius: 12,
                background: numFeedback.ok ? 'var(--emerald-soft)' : 'var(--crimson-soft)',
                border: numFeedback.ok
                  ? '1px solid rgba(16,185,129,0.4)'
                  : '1px solid rgba(239,68,68,0.4)',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: 13, marginBottom: 4 }}>
                {numFeedback.ok ? '✓ Raciocínio Exato!' : '✗ Olhe o Atalho Mental:'}
              </div>
              <div style={{ fontSize: 12.8, marginBottom: 10 }}>{numFeedback.shortcut}</div>
              <button type="button" className="btn btn-primary btn-block" onClick={advanceNumeracy}>
                {numRound >= NUM_TOTAL ? 'Concluir Bateria Numérica' : 'Próximo Cálculo →'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ================= JOGO 6 ATIVO: DISCERNIMENTO, ANTIVIESES & SABEDORIA ================= */}
      {wisActive && wisPuzzle && (
        <div style={{ padding: 16, borderRadius: 14, background: 'var(--bg-elevated)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="badge badge-cyan">
              Julgamento {wisRound}/{WIS_TOTAL}
            </span>
            <button
              type="button"
              className="chip"
              style={{ padding: '3px 9px', fontSize: 11 }}
              onClick={() => setWisActive(false)}
            >
              <RotateCcw size={11} /> Sair
            </button>
          </div>

          <div
            style={{
              padding: 13,
              borderRadius: 12,
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              fontSize: 14,
              fontWeight: 600,
              lineHeight: 1.5,
              marginBottom: 12,
            }}
          >
            {wisPuzzle.prompt}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 10 }}>
            {wisPuzzle.options.map((opt, idx) => {
              let bg = 'var(--bg-input)';
              let border = '1px solid var(--border-subtle)';
              if (wisFeedback && idx === wisPuzzle.correctIndex) {
                bg = 'var(--emerald-soft)';
                border = '1.5px solid var(--emerald)';
              }
              return (
                <button
                  key={opt}
                  type="button"
                  disabled={Boolean(wisFeedback)}
                  onClick={() => handleWisdomAnswer(idx)}
                  style={{
                    textAlign: 'left',
                    padding: '11px 12px',
                    borderRadius: 12,
                    background: bg,
                    border,
                    color: 'var(--text-primary)',
                    fontWeight: 700,
                    fontSize: 13.2,
                    lineHeight: 1.45,
                    cursor: wisFeedback ? 'default' : 'pointer',
                  }}
                >
                  {opt}
                </button>
              );
            })}
          </div>

          {wisFeedback && (
            <div
              style={{
                padding: 12,
                borderRadius: 12,
                background: wisFeedback.ok ? 'var(--emerald-soft)' : 'var(--crimson-soft)',
                border: wisFeedback.ok
                  ? '1px solid rgba(16,185,129,0.4)'
                  : '1px solid rgba(239,68,68,0.4)',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: 13, marginBottom: 4 }}>
                {wisFeedback.ok ? '✓ Discernimento Certeiro!' : '✗ Armadilha Detectada:'}
              </div>
              <div style={{ fontSize: 12.8, marginBottom: 10 }}>{wisFeedback.anchor}</div>
              <button type="button" className="btn btn-primary btn-block" onClick={advanceWisdom}>
                {wisRound >= WIS_TOTAL ? 'Concluir Bateria de Sabedoria' : 'Próximo Caso →'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ================= JOGO 7 ATIVO: CALIBRACAO BAYESIANA & BRIER (TETLOCK) ================= */}
      {calActive && calPuzzle && (
        <div style={{ padding: 16, borderRadius: 14, background: 'var(--bg-elevated)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="badge badge-cyan">
              Previsão {calRound}/{CAL_TOTAL} • Acumulado {calPointsSum} pts
            </span>
            <button
              type="button"
              className="chip"
              style={{ padding: '3px 9px', fontSize: 11 }}
              onClick={() => setCalActive(false)}
            >
              <RotateCcw size={11} /> Sair
            </button>
          </div>

          <div
            style={{
              padding: 13,
              borderRadius: 12,
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              fontSize: 14,
              fontWeight: 600,
              lineHeight: 1.5,
              marginBottom: 12,
            }}
          >
            {calPuzzle.statement}
          </div>

          <div className="section-kicker" style={{ marginBottom: 6 }}>
            Passo 1: Escolha sua hipótese
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
            {calPuzzle.options.map((opt, idx) => {
              const selected = calPickedIdx === idx;
              let bg = selected ? 'var(--amber-soft)' : 'var(--bg-input)';
              let border = selected
                ? '1.5px solid var(--amber)'
                : '1px solid var(--border-subtle)';
              if (calFeedback && idx === calPuzzle.correctIndex) {
                bg = 'var(--emerald-soft)';
                border = '1.5px solid var(--emerald)';
              }
              return (
                <button
                  key={opt}
                  type="button"
                  disabled={Boolean(calFeedback)}
                  onClick={() => {
                    triggerHaptic('light');
                    setCalPickedIdx(idx as 0 | 1);
                  }}
                  style={{
                    textAlign: 'left',
                    padding: '11px 12px',
                    borderRadius: 12,
                    background: bg,
                    border,
                    color: 'var(--text-primary)',
                    fontWeight: 700,
                    fontSize: 13.2,
                    lineHeight: 1.45,
                    cursor: calFeedback ? 'default' : 'pointer',
                  }}
                >
                  {opt}
                </button>
              );
            })}
          </div>

          {!calFeedback && calPickedIdx !== null && (
            <div style={{ marginBottom: 10 }}>
              <div className="section-kicker" style={{ marginBottom: 6, color: 'var(--amber)' }}>
                Passo 2: Qual é o seu Grau Honesto de Certeza? (Regra de Brier)
              </div>
              <div className="grid-3">
                {[
                  { pct: 55 as const, label: '55%', sub: 'Dúvida Honesta' },
                  { pct: 75 as const, label: '75%', sub: 'Provável' },
                  { pct: 95 as const, label: '95%', sub: 'Certeza Alta' },
                ].map((c) => (
                  <button
                    key={c.pct}
                    type="button"
                    className="btn btn-ghost"
                    style={{ flexDirection: 'column', padding: '8px 6px', gap: 2 }}
                    onClick={() => handleCalibrationCommit(c.pct)}
                  >
                    <strong style={{ fontSize: 14, color: 'var(--amber)' }}>{c.label}</strong>
                    <span style={{ fontSize: 10.5 }} className="muted">
                      {c.sub}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {calFeedback && (
            <div
              style={{
                padding: 12,
                borderRadius: 12,
                background: calFeedback.ok ? 'var(--emerald-soft)' : 'var(--crimson-soft)',
                border: calFeedback.ok
                  ? '1px solid rgba(16,185,129,0.4)'
                  : '1px solid rgba(239,68,68,0.4)',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: 13, marginBottom: 4 }}>
                {calFeedback.ok
                  ? `✓ Acertou com ${calFeedback.confidence}% de certeza (+${calFeedback.roundPoints} pts)!`
                  : calFeedback.confidence === 95
                    ? `✗ Armadilha Dunning-Kruger: erro com 95% de certeza (+${calFeedback.roundPoints} pts)!`
                    : `✗ Errou, mas a humildade de ${calFeedback.confidence}% salvou +${calFeedback.roundPoints} pts!`}
              </div>
              <div style={{ fontSize: 12.8, marginBottom: 10 }}>{calFeedback.explanation}</div>
              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={advanceCalibration}
              >
                {calRound >= CAL_TOTAL ? 'Concluir Calibração de Brier' : 'Próxima Previsão →'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ================= JOGO 8 ATIVO: N-BACK EXECUTIVO ================= */}
      {nBackActive && nBackData && (
        <div
          style={{
            padding: 16,
            borderRadius: 14,
            background: 'var(--bg-elevated)',
            textAlign: 'center',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="badge badge-cyan">
              {nBackData.nBack}-Back • Passo {nBackIndex + 1}/{nBackData.items.length}
            </span>
            <button
              type="button"
              className="chip"
              style={{ padding: '3px 9px', fontSize: 11 }}
              onClick={() => setNBackActive(false)}
            >
              <RotateCcw size={11} /> Sair
            </button>
          </div>

          <div className="muted" style={{ fontSize: 12.5, marginBottom: 10 }}>
            Regra: este símbolo é <strong>IGUAL</strong> ao que apareceu{' '}
            <strong>
              {nBackData.nBack} {nBackData.nBack === 1 ? 'passo' : 'passos'} atrás
            </strong>
            ?
          </div>

          <div
            className="mono"
            style={{
              width: 96,
              height: 96,
              margin: '0 auto 12px',
              borderRadius: 18,
              border: '2px solid var(--cyan)',
              background: 'var(--cyan-soft)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 44,
              fontWeight: 900,
              color: '#67e8f9',
            }}
          >
            {nBackData.items[nBackIndex].symbol}
          </div>

          {nBackLastHit !== null && nBackIndex > nBackData.nBack && (
            <div
              style={{
                fontSize: 12,
                fontWeight: 700,
                marginBottom: 10,
                color: nBackLastHit ? '#34d399' : '#fca5a5',
              }}
            >
              {nBackLastHit ? '✓ Última resposta exata!' : '✗ Atenção ao fluxo anterior'}
            </div>
          )}

          {nBackIndex < nBackData.nBack ? (
            <button
              type="button"
              className="btn btn-primary btn-block"
              onClick={() => handleNBackStep(null)}
            >
              Memorizar Letra #{nBackIndex + 1} e Avançar →
            </button>
          ) : (
            <div className="grid-2">
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => handleNBackStep(true)}
              >
                IGUAL ({nBackData.nBack}-Back)
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => handleNBackStep(false)}
              >
                DIFERENTE
              </button>
            </div>
          )}
        </div>
      )}

      {/* ================= JOGO 9 ATIVO: TRILHA ALTERNADA 1-A-2-B (SHIFTING) ================= */}
      {trailActive && trailBoard && (
        <div
          style={{
            padding: 14,
            borderRadius: 14,
            background: 'var(--bg-elevated)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span className="badge badge-cyan">
              Trilha 1-A-2-B • {trailNextOrder}/{trailBoard.totalNodes} concluídos
            </span>
            <button
              type="button"
              className="chip"
              style={{ padding: '3px 9px', fontSize: 11 }}
              onClick={() => setTrailActive(false)}
            >
              <RotateCcw size={11} /> Sair
            </button>
          </div>

          <div className="muted" style={{ fontSize: 12.5, marginBottom: 10 }}>
            Alterne sem errar: <strong>1 → A → 2 → B → 3 → C...</strong> • Próximo alvo:{' '}
            <strong style={{ color: '#67e8f9' }}>
              {trailNextOrder % 2 === 0 ? 'NÚMERO' : 'LETRA'}
            </strong>{' '}
            {trailErrors > 0 && (
              <span style={{ color: '#fca5a5' }}>({trailErrors} erro(s))</span>
            )}
          </div>

          <div className="grid-4" style={{ gap: 8 }}>
            {trailBoard.cells.map((node) => {
              const done = node.sequenceOrder < trailNextOrder;
              return (
                <button
                  key={node.cellIndex}
                  type="button"
                  disabled={done}
                  onClick={() => handleTrailTap(node.sequenceOrder)}
                  className="mono"
                  style={{
                    minHeight: 52,
                    borderRadius: 12,
                    fontWeight: 900,
                    fontSize: 18,
                    cursor: done ? 'default' : 'pointer',
                    background: done ? 'var(--emerald-soft)' : 'rgba(15, 23, 42, 0.8)',
                    color: done
                      ? '#34d399'
                      : node.kind === 'NUMBER'
                        ? '#fde68a'
                        : '#67e8f9',
                    border: done
                      ? '1px solid rgba(16,185,129,0.45)'
                      : '1px solid var(--border-subtle)',
                    opacity: done ? 0.52 : 1,
                  }}
                >
                  {done ? '✓' : node.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* HISTORICO RESUMIDO */}
      {logs.length > 0 && !isAnyRunning && (
        <div
          style={{
            marginTop: 14,
            paddingTop: 12,
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: 12.5,
          }}
        >
          <span className="muted">
            <CheckCircle2 size={13} color="var(--emerald)" style={{ verticalAlign: 'middle' }} />{' '}
            {logs.length} baterias cognitivas registradas
          </span>
          <span className="mono" style={{ color: 'var(--amber)', fontWeight: 700 }}>
            Média:{' '}
            {Math.round(logs.slice(-5).reduce((a, b) => a + b.score, 0) / Math.min(5, logs.length))}{' '}
            pts
          </span>
        </div>
      )}
    </div>
  );
};
