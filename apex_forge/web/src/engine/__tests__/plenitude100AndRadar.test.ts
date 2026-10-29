import { describe, expect, it } from 'vitest';
import {
  computeBrierRoundPoints,
  generateNBackSequence,
  generateTetlockCalibrationQuestion,
  generateTrailShiftingBoard,
  generateWisdomDiscernmentQuestion,
} from '../cognitiveGenerator';
import {
  computeRealLifeCalibrationSummary,
  evaluateRealDecision,
  resolveRealDecisionOutcome,
} from '../decisionTribunalEngine';
import { buildDemoVault, buildZeroSkillYouthVault } from '../demoScenario';
import { computePolymathRadar } from '../polymathRadarEngine';
import { createBlueprintFromTemplate, evaluateFeynmanSocraticAudit } from '../skillForgeEngine';
import { createInitialVault } from '../stateEngine';
import {
  computeUpdatedTeachingProgress,
  getLessonById,
  getLessonFieldMission,
  getLessonMasteryTier,
  getLessonZeroStep,
  selectDailyRecommendedTeaching,
  TEACHING_TRACKS,
  TEACHINGS_CATALOG,
} from '../teachingsCatalog';
import { MasteryTier, TeachingProgressEntry, TeachingTrackId } from '../types';

describe('FORJA v23.0.0 — Edição Soberana 300 Lições (10 Pilares × 30 Lições), Tríade de Miyake (Trail B) & Ciclo Brier Real', () => {
  it('1. Valida exatamente 300 lições (10 Pilares × 30 Lições) e simetria por grau (50/50/50/150)', () => {
    expect(TEACHING_TRACKS.length).toBe(10);
    expect(TEACHINGS_CATALOG.length).toBe(300);

    const seenIds = new Set<string>();
    const countsByTrack = new Map<TeachingTrackId, number>();
    const countsByTier = new Map<MasteryTier, number>();

    for (const lesson of TEACHINGS_CATALOG) {
      expect(seenIds.has(lesson.id)).toBe(false);
      seenIds.add(lesson.id);

      countsByTrack.set(lesson.trackId, (countsByTrack.get(lesson.trackId) ?? 0) + 1);
      const tier = getLessonMasteryTier(lesson);
      countsByTier.set(tier, (countsByTier.get(tier) ?? 0) + 1);

      expect(lesson.title.trim().length).toBeGreaterThan(5);
      expect(lesson.coreEssence.trim().length).toBeGreaterThan(40);
      expect(lesson.scientificSource.trim().length).toBeGreaterThan(15);
      expect(getLessonZeroStep(lesson).trim().length).toBeGreaterThan(15);
      expect(getLessonFieldMission(lesson).trim().length).toBeGreaterThan(15);
      expect(lesson.dilemmaOptions.length).toBe(4);
      expect(lesson.correctOptionIndex).toBeGreaterThanOrEqual(0);
      expect(lesson.correctOptionIndex).toBeLessThan(4);
      expect(getLessonById(lesson.id)?.id).toBe(lesson.id);
    }

    for (const track of TEACHING_TRACKS) {
      expect(countsByTrack.get(track.id)).toBe(30);
    }
    expect(countsByTier.get(1)).toBe(50);
    expect(countsByTier.get(2)).toBe(50);
    expect(countsByTier.get(3)).toBe(50);
    expect(countsByTier.get(4)).toBe(150);
  });

  it('2. Balanceamento Polímata 360° (Round-Robin): primeiras 10 recomendações cobrem todos os 10 Pilares', () => {
    for (const zone of ['VERDE', 'AMARELO', 'VERMELHO'] as const) {
      const progress: Record<string, TeachingProgressEntry> = {};
      const visitedTracks = new Set<TeachingTrackId>();
      const curDay = '2026-10-26';

      for (let i = 0; i < 10; i++) {
        const rec = selectDailyRecommendedTeaching(progress, curDay, zone);
        if (i === 0) {
          expect(rec.lesson.id).toBe('cristo_01_casa_na_rocha');
        }
        visitedTracks.add(rec.lesson.trackId);
        progress[rec.lesson.id] = computeUpdatedTeachingProgress(
          undefined,
          true,
          curDay,
          rec.lesson.id,
        );
      }

      expect(visitedTracks.size).toBe(10);
    }
  });

  it('3. Radar Polímata 10D e Detector de Gargalo (Goldratt) sem NaN em cofres vazios, demo e plenos', () => {
    const emptyVault = createInitialVault();
    const emptyRadar = computePolymathRadar(emptyVault);
    expect(emptyRadar.axes.length).toBe(10);
    expect(Number.isFinite(emptyRadar.harmonyIndex100)).toBe(true);
    expect(emptyRadar.meanScore100).toBeGreaterThanOrEqual(4);

    const zeroYouth = buildZeroSkillYouthVault();
    const demoVault = buildDemoVault();
    const youthRadar = computePolymathRadar(zeroYouth);
    const demoRadar = computePolymathRadar(demoVault);

    expect(demoRadar.meanScore100).toBeGreaterThan(youthRadar.meanScore100);
    expect(demoRadar.strongestAxis.score100).toBeGreaterThanOrEqual(demoRadar.weakestAxis.score100);
    expect(Object.keys(demoVault.eveningReflections ?? {}).length).toBeGreaterThanOrEqual(1);
    expect(Object.keys(zeroYouth.eveningReflections ?? {}).length).toBeGreaterThanOrEqual(1);
  });

  it('4. Regra Quadrática Estrita de Brier (Tetlock) + 1.000 sementes fuzz em Sabedoria e Calibração', () => {
    const pRight95 = computeBrierRoundPoints(true, 95).roundPoints;
    const pRight75 = computeBrierRoundPoints(true, 75).roundPoints;
    const pRight55 = computeBrierRoundPoints(true, 55).roundPoints;
    const pWrong55 = computeBrierRoundPoints(false, 55).roundPoints;
    const pWrong75 = computeBrierRoundPoints(false, 75).roundPoints;
    const pWrong95 = computeBrierRoundPoints(false, 95).roundPoints;

    // Monotonicidade estrita da Regra de Brier
    expect(pRight95).toBeGreaterThan(pRight75);
    expect(pRight75).toBeGreaterThan(pRight55);
    expect(pRight55).toBeGreaterThan(pWrong55);
    expect(pWrong55).toBeGreaterThan(pWrong75);
    expect(pWrong75).toBeGreaterThan(pWrong95);
    expect(pWrong95).toBe(0);

    const bp = createBlueprintFromTemplate('tpl_programacao_ia', '2026-10-26');
    expect(bp.steps.length).toBe(4);

    const deep = evaluateFeynmanSocraticAudit({
      conceptName: 'Algoritmo',
      childExplanation:
        'Um algoritmo é uma sequência clara e ordenada de passos que transforma dados de entrada em uma resposta confiável.',
      whyAndBoundary:
        'Funciona porque elimina adivinhação a cada etapa; porém trava ou erra quando recebe dados corrompidos fora da condição prevista.',
      concreteAnalogy:
        'Funciona igual a uma receita de bolo testada onde cada ingrediente entra na ordem exata.',
    });
    expect(deep.passed).toBe(true);
    expect(deep.clarityScorePct).toBeGreaterThanOrEqual(85);

    for (let s = 1; s <= 1000; s++) {
      const diff = (((s - 1) % 3) + 1) as 1 | 2 | 3;
      const t = generateWisdomDiscernmentQuestion(s * 977, diff);
      expect(t.options.length).toBe(4);
      expect(new Set(t.options).size).toBe(4);
      expect(t.correctIndex).toBeGreaterThanOrEqual(0);
      expect(t.correctIndex).toBeLessThan(4);

      const cal = generateTetlockCalibrationQuestion(s * 1319, diff);
      expect(cal.options.length).toBe(2);
      expect(cal.options[0]).not.toBe(cal.options[1]);
      expect([0, 1]).toContain(cal.correctIndex);
      expect(cal.explanation.length).toBeGreaterThan(20);
    }
  });

  it('5. 8ª Disciplina N-Back Executivo (1/2/3-Back) + Tribunal de Decisão Real (Lucas 14:28 × Salomão × Klein)', () => {
    for (let s = 1; s <= 500; s++) {
      const diff = (((s - 1) % 3) + 1) as 1 | 2 | 3;
      const nb = generateNBackSequence(s * 733, diff);
      expect(nb.nBack).toBe(diff);
      expect(nb.items.length).toBe(14);
      const realMatches = nb.items.slice(nb.nBack).filter((x) => x.isTargetMatch).length;
      expect(realMatches).toBeGreaterThanOrEqual(3);
      for (let i = 0; i < nb.items.length; i++) {
        if (i < nb.nBack) {
          expect(nb.items[i].isTargetMatch).toBe(false);
        } else {
          expect(nb.items[i].isTargetMatch).toBe(
            nb.items[i].symbol === nb.items[i - nb.nBack].symbol,
          );
        }
      }
    }

    const vetoEthics = evaluateRealDecision({
      decisionTitle: 'Ganho rápido escondendo defeito do cliente',
      towerCostEstimate: 'Baixo custo imediato',
      solomonThirdPerson: 'Diria para não fazer porque destrói o nome',
      preMortemGuardrail: 'Se descoberto, destrói a reputação',
      preservesCharacter: false,
      zeroRuinRisk: true,
      futureSelf101010: false,
      confidencePct: 85,
    });
    expect(vetoEthics.verdict).toBe('VETO_PRUDENCIAL');

    const vetoRuin = evaluateRealDecision({
      decisionTitle: 'Alavancar 100% da reserva de emergência num único ativo volátil',
      towerCostEstimate: '100% da liquidez familiar',
      solomonThirdPerson: 'Nunca arrisque o teto da família',
      preMortemGuardrail: 'Queda de 50% forçaria dívida cara',
      preservesCharacter: true,
      zeroRuinRisk: false,
      futureSelf101010: false,
      confidencePct: 85,
    });
    expect(vetoRuin.verdict).toBe('VETO_PRUDENCIAL');

    const wiseDecision = evaluateRealDecision({
      decisionTitle: 'Dedicar 6h semanais a mestrado profissional sem comprometer reserva',
      towerCostEstimate: '6h semanais às 06h00 por 18 meses + parcela dentro de 8% da renda',
      solomonThirdPerson: 'Eu aconselharia meu melhor amigo a testar a rotina por 3 semanas antes',
      preMortemGuardrail: 'Cansaço à noite; trava: estudar de manhã antes do expediente',
      preservesCharacter: true,
      zeroRuinRisk: true,
      futureSelf101010: true,
      confidencePct: 70,
    });
    expect(wiseDecision.verdict).toBe('AVANCAR_COM_TRAVAS');
    expect(wiseDecision.maturityScore100).toBeGreaterThanOrEqual(85);
  });

  it('6. 9ª Disciplina Trilha Alternada 1-A-2-B (Miyake Shifting) + Ciclo Pós-Resultado de Brier Real', () => {
    for (let s = 1; s <= 500; s++) {
      const diff = (((s - 1) % 3) + 1) as 1 | 2 | 3;
      const board = generateTrailShiftingBoard(s * 919, diff);
      const expectedNodes = diff === 1 ? 12 : diff === 2 ? 16 : 20;
      expect(board.totalNodes).toBe(expectedNodes);
      expect(board.cells.length).toBe(expectedNodes);
      expect(board.targetSequence.length).toBe(expectedNodes);

      const seenOrders = new Set(board.cells.map((c) => c.sequenceOrder));
      const seenLabels = new Set(board.cells.map((c) => c.label));
      expect(seenOrders.size).toBe(expectedNodes);
      expect(seenLabels.size).toBe(expectedNodes);

      for (let ord = 0; ord < expectedNodes; ord++) {
        const hit = board.cells.find((c) => c.sequenceOrder === ord);
        expect(hit).toBeDefined();
        expect(hit?.kind).toBe(ord % 2 === 0 ? 'NUMBER' : 'LETTER');
      }
    }

    const demo = buildDemoVault();
    const openRec = demo.decisionJournal![1];
    const resolvedGood = resolveRealDecisionOutcome(
      openRec,
      'SUCESSO',
      'Rotina matinal funcionou sem comprometer sono.',
      '2026-10-26',
    );
    expect(resolvedGood.brierScore).toBeCloseTo(0.09, 4);

    const resolvedMiss = resolveRealDecisionOutcome(
      { ...openRec, confidencePct: 85 },
      'FALHA',
      'Excesso de confiança no prazo inicial.',
      '2026-10-26',
    );
    expect(resolvedMiss.brierScore).toBeCloseTo(0.7225, 4);

    const calGood = computeRealLifeCalibrationSummary([demo.decisionJournal![0], resolvedGood]);
    const calOverconfident = computeRealLifeCalibrationSummary([resolvedMiss]);
    expect(calGood.resolvedCount).toBe(2);
    expect(calGood.meanBrierScore).toBeLessThan(0.14);
    expect(calGood.calibrationScore100).toBeGreaterThan(calOverconfident.calibrationScore100);
  });
});
