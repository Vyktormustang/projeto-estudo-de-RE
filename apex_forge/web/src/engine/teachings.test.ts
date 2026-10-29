import { describe, expect, it } from 'vitest';
import { buildZeroSkillYouthVault } from './demoScenario';
import {
  applySimulatorChoice,
  createInitialSimulatorRun,
  evaluateFinalMasteryReport,
  SIMULATOR_CHAPTERS,
} from './masterySimulator';
import { buildPantheonBriefing, PANTHEON_CODEX } from './pantheonEngine';
import {
  createBlueprintFromTemplate,
  createCustomSkillBlueprint,
  evaluateFeynmanSocraticAudit,
  PRESET_SKILL_TEMPLATES,
} from './skillForgeEngine';
import { addDaysToBioDay, prescribeDayPlan } from './stateEngine';
import {
  computeUpdatedTeachingProgress,
  getDueTeachingsForDay,
  getLessonById,
  getLessonFieldMission,
  getLessonMasteryTier,
  getLessonZeroStep,
  selectDailyRecommendedTeaching,
  TEACHING_TRACKS,
  TEACHINGS_CATALOG,
} from './teachingsCatalog';
import { TeachingProgressEntry } from './types';

describe('FORJA v22.0.0 — Auditoria da Edição Soberana 300 (200 + 80 Soberanas + 20 Volume IV, 10 Pilares × 30 Lições, Radar 10D, 4C/ID & Simulador 12 Capítulos)', () => {
  it('1. Catálogo possui 300 ensinamentos em 10 Pilares Universais (30 por pilar: 20 canônicas + 8 soberanas + 2 Volume IV)', () => {
    expect(TEACHING_TRACKS).toHaveLength(10);
    expect(TEACHINGS_CATALOG).toHaveLength(300);

    expect(TEACHING_TRACKS[0].id).toBe('CRISTO_EVANGELHOS');
    expect(TEACHING_TRACKS[1].id).toBe('SABEDORIA_BIBLICA');

    const ids = new Set<string>();
    const titles = new Set<string>();
    const globalTierCounts = { 1: 0, 2: 0, 3: 0, 4: 0 };

    for (const track of TEACHING_TRACKS) {
      const inTrack = TEACHINGS_CATALOG.filter((l) => l.trackId === track.id);
      expect(inTrack).toHaveLength(30);

      const trackTierCounts = { 1: 0, 2: 0, 3: 0, 4: 0 };
      for (const l of inTrack) {
        const tier = getLessonMasteryTier(l);
        trackTierCounts[tier]++;
        globalTierCounts[tier]++;
      }
      expect(trackTierCounts).toEqual({ 1: 5, 2: 5, 3: 5, 4: 15 });
    }

    expect(globalTierCounts).toEqual({ 1: 50, 2: 50, 3: 50, 4: 150 });

    for (const lesson of TEACHINGS_CATALOG) {
      expect(ids.has(lesson.id)).toBe(false);
      expect(titles.has(lesson.title)).toBe(false);
      ids.add(lesson.id);
      titles.add(lesson.title);

      expect(getLessonById(lesson.id)?.id).toBe(lesson.id);
      expect(lesson.coreEssence.length).toBeGreaterThan(60);
      expect(lesson.whyItWorksMechanism.length).toBeGreaterThan(50);
      expect(lesson.practicalActionToday.length).toBeGreaterThan(30);
      expect(getLessonZeroStep(lesson).length).toBeGreaterThan(25);
      expect(getLessonFieldMission(lesson).length).toBeGreaterThan(25);
      expect(lesson.scientificSource.length).toBeGreaterThan(15);
      expect(lesson.dilemmaOptions).toHaveLength(4);
      expect(new Set(lesson.dilemmaOptions).size).toBe(4);
      expect([0, 1, 2, 3]).toContain(lesson.correctOptionIndex);
      expect(lesson.feedbackCorrect.length).toBeGreaterThan(20);
      expect(lesson.feedbackTrap.length).toBeGreaterThan(20);
    }
  });

  it('2. Motor de Repetição Espaçada segue progressão 1d -> 3d -> 7d -> 21d e recupera em 1d após erro', () => {
    const d0 = '2026-10-26';
    const lid = TEACHINGS_CATALOG[0].id;
    expect(lid).toBe('cristo_01_casa_na_rocha');

    const p1 = computeUpdatedTeachingProgress(undefined, true, d0, lid);
    expect(p1.masteryLevel).toBe(1);
    expect(p1.nextReviewBioDayId).toBe(addDaysToBioDay(d0, 1));

    const d1 = addDaysToBioDay(d0, 1);
    const p2 = computeUpdatedTeachingProgress(p1, true, d1, lid);
    expect(p2.masteryLevel).toBe(2);
    expect(p2.nextReviewBioDayId).toBe(addDaysToBioDay(d1, 3));

    const d2 = addDaysToBioDay(d1, 3);
    const p3 = computeUpdatedTeachingProgress(p2, true, d2, lid);
    expect(p3.masteryLevel).toBe(3);
    expect(p3.nextReviewBioDayId).toBe(addDaysToBioDay(d2, 7));

    const d3 = addDaysToBioDay(d2, 7);
    const p4 = computeUpdatedTeachingProgress(p3, true, d3, lid);
    expect(p4.masteryLevel).toBe(4);
    expect(p4.nextReviewBioDayId).toBe(addDaysToBioDay(d3, 21));

    const pFail = computeUpdatedTeachingProgress(p4, false, '2026-12-01', lid);
    expect(pFail.masteryLevel).toBe(0);
    expect(pFail.timesCompleted).toBe(5);
    expect(pFail.nextReviewBioDayId).toBe('2026-12-02');
  });

  it('3. Andaime Progressivo 4C/ID destrava todas as 50 lições de Grau I antes do Grau II (iniciando pela Casa na Rocha)', () => {
    const map: Record<string, TeachingProgressEntry> = {};
    const d0 = '2026-10-26';

    const firstRec = selectDailyRecommendedTeaching(map, d0);
    expect(firstRec.lesson.id).toBe('cristo_01_casa_na_rocha');

    for (let step = 0; step < 50; step++) {
      const rec = selectDailyRecommendedTeaching(map, d0);
      expect(getLessonMasteryTier(rec.lesson)).toBe(1);
      map[rec.lesson.id] = computeUpdatedTeachingProgress(undefined, true, d0, rec.lesson.id);
    }

    // A 51a licao inedita avanca exatamente para o Grau II (Artifice)!
    const rec51 = selectDailyRecommendedTeaching(map, d0);
    expect(getLessonMasteryTier(rec51.lesson)).toBe(2);

    const tomorrow = addDaysToBioDay(d0, 1);
    expect(getDueTeachingsForDay(map, tomorrow).length).toBeGreaterThanOrEqual(1);
    const recTomorrow = selectDailyRecommendedTeaching(map, tomorrow, 'VERDE');
    expect(recTomorrow.reasonTag).toContain('Revisão Espaçada');
  });

  it('4. Panteão de 12 Mestres inclui Jesus Cristo e Sabedoria Bíblica com subordinação clínica intacta em Zona Vermelha', () => {
    expect(PANTHEON_CODEX).toHaveLength(12);
    expect(PANTHEON_CODEX[0].id).toBe('JESUS_CRISTO');
    expect(PANTHEON_CODEX[1].id).toBe('SALOMAO_BIBLIA');

    const zeroVault = buildZeroSkillYouthVault();
    const prof = { ...zeroVault.profile!, commandVoice: 'CRISTO_BIBLIA' as const };
    const bioDay = Object.keys(zeroVault.checkIns)[0];
    const normalCheckIn = {
      ...zeroVault.checkIns[bioDay],
      sleepHours: 8,
      sleepQuality: 6,
      energyLevel: 6,
      mentalCalm: 6,
      muscularRecovery: 6,
    };

    const planGreen = prescribeDayPlan(prof, normalCheckIn, zeroVault);
    const b1 = buildPantheonBriefing(prof, { ...normalCheckIn, bioDayId: '2026-10-26' }, planGreen.readiness, zeroVault);
    const b2 = buildPantheonBriefing(prof, { ...normalCheckIn, bioDayId: '2026-10-27' }, planGreen.readiness, zeroVault);
    expect(['JESUS_CRISTO', 'SALOMAO_BIBLIA']).toContain(b1.mentorId);
    expect(['JESUS_CRISTO', 'SALOMAO_BIBLIA']).toContain(b2.mentorId);

    // Zona Vermelha por sintoma viral subordina o comando a repouso sabio (Marcos 6:31) sem bravata
    const viralCheckIn = { ...normalCheckIn, viralOrFeverSymptoms: true };
    const planRed = prescribeDayPlan(prof, viralCheckIn, zeroVault);
    expect(planRed.readiness.zone).toBe('VERMELHO');
    const bRed = buildPantheonBriefing(prof, viralCheckIn, planRed.readiness, zeroVault);
    expect(bRed.mentorId).toBe('JESUS_CRISTO');
    expect(bRed.tacticalDirective).toContain('Mc 6:31');
  });

  it('5. Simulador Vivo "Do Jovem Sem Habilidade ao Mestre" (12 capítulos, 6 atributos com Caráter + 2.000 trajetórias fuzz)', () => {
    expect(SIMULATOR_CHAPTERS).toHaveLength(12);
    const chapIds = new Set<string>();

    for (const ch of SIMULATOR_CHAPTERS) {
      expect(chapIds.has(ch.id)).toBe(false);
      chapIds.add(ch.id);
      expect(getLessonById(ch.linkedLessonId)).toBeDefined();
      expect(ch.options).toHaveLength(4);
      expect(new Set(ch.options.map((o) => o.label)).size).toBe(4);
      const masters = ch.options.filter((o) => o.isMasterChoice);
      expect(masters).toHaveLength(1);
    }

    // Trajetoria Perfeita (12/12 escolhas de Mestre)
    let perfectState = createInitialSimulatorRun();
    for (const ch of SIMULATOR_CHAPTERS) {
      const masterIdx = ch.options.findIndex((o) => o.isMasterChoice) as 0 | 1 | 2 | 3;
      perfectState = applySimulatorChoice(perfectState, masterIdx);
    }
    expect(perfectState.completed).toBe(true);
    expect(perfectState.attributes.carater).toBe(100);
    const perfectReport = evaluateFinalMasteryReport(perfectState);
    expect(perfectReport.masterDecisionsCount).toBe(12);
    expect(perfectReport.score1000).toBe(1000);
    expect(perfectReport.rankTitle).toContain('Rocha');

    // Fuzzing de 2.000 trajetorias aleatorias: zero NaN e limites [0, 100] / [0, 1000]
    let seed = 777;
    for (let run = 0; run < 2000; run++) {
      let st = createInitialSimulatorRun();
      for (let c = 0; c < SIMULATOR_CHAPTERS.length; c++) {
        seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
        const pick = (seed % 4) as 0 | 1 | 2 | 3;
        st = applySimulatorChoice(st, pick);
      }
      expect(st.completed).toBe(true);
      for (const v of Object.values(st.attributes)) {
        expect(Number.isFinite(v)).toBe(true);
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(100);
      }
      const rep = evaluateFinalMasteryReport(st);
      expect(Number.isFinite(rep.score1000)).toBe(true);
      expect(rep.score1000).toBeGreaterThanOrEqual(0);
      expect(rep.score1000).toBeLessThanOrEqual(1000);
      expect(rep.recommendedLessonIds.length).toBeGreaterThanOrEqual(1);
    }
  });

  it('6. Construtor Universal 4C/ID (6 Modelos + Personalizado) & Auditor Socrático Chi–Feynman (0..100%)', () => {
    expect(PRESET_SKILL_TEMPLATES).toHaveLength(6);
    for (const tpl of PRESET_SKILL_TEMPLATES) {
      const bp = createBlueprintFromTemplate(tpl.id, '2026-10-26');
      expect(bp.steps).toHaveLength(4);
      expect(bp.oracle30DayProof.length).toBeGreaterThan(20);
      expect(bp.zeroStep2Min.length).toBeGreaterThan(15);
    }

    const customBp = createCustomSkillBlueprint({ skillName: 'Eletrônica Embarcada' }, '2026-10-26');
    expect(customBp.skillName).toBe('Eletrônica Embarcada');
    expect(customBp.steps).toHaveLength(4);

    const highClarity = evaluateFeynmanSocraticAudit({
      conceptName: 'Juros Compostos',
      childExplanation:
        'Juros compostos acontecem quando o rendimento de cada mês passa a somar no monte principal e também gera novos rendimentos nos meses seguintes.',
      whyAndBoundary:
        'Funciona porque a base cresce exponencialmente a cada ciclo; porém falha e trabalha contra você quando existe dívida cara ou interrupção precoce.',
      concreteAnalogy:
        'Funciona igual a uma bola de neve descendo a montanha que cresce mais a cada volta completa.',
    });
    expect(highClarity.clarityScorePct).toBeGreaterThanOrEqual(90);
    expect(highClarity.passed).toBe(true);

    const lowClarity = evaluateFeynmanSocraticAudit({
      conceptName: 'Algo',
      childExplanation: 'tipo assim sei lá',
      whyAndBoundary: 'curto',
      concreteAnalogy: '',
    });
    expect(lowClarity.clarityScorePct).toBeLessThan(40);
    expect(lowClarity.passed).toBe(false);
    expect(lowClarity.gapsToFix.length).toBeGreaterThanOrEqual(2);
  });
});
