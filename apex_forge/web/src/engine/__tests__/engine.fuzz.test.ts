import { describe, expect, it } from 'vitest';
import { EXERCISE_CATALOG } from '../exerciseCatalog';
import {
  addDaysToBioDay,
  advanceQueueSlot,
  computeBioDayId,
  createInitialVault,
  prescribeDayPlan,
} from '../stateEngine';
import {
  DailyCheckIn,
  EquipmentEnv,
  JointRegion,
  UserProfile,
  VaultState,
} from '../types';

function makeProfile(overrides: Partial<UserProfile> = {}): UserProfile {
  return {
    codename: 'Operador Teste',
    age: 30,
    sex: 'MASCULINO',
    weightKg: 78,
    heightCm: 176,
    level: 'INICIANTE',
    equipment: 'CASA',
    energyGoal: 'MANUTENCAO_PERFORMANCE',
    occupationalDemand: 'SEDENTARIO_INTELECTUAL',
    climate: 'CALOR_TROPICAL_UMIDO',
    scheduleRegime: 'DIURNO_FIXO',
    executiveProfile: 'EQUILIBRADO',
    commandVoice: 'ADAPTATIVO',
    weekdayFreeMinutes: 45,
    weekendFreeMinutes: 60,
    targetSleepHours: 7.5,
    usualWakeTime: '06:30',
    usualBedTime: '22:30',
    primaryGoalDomain: 'Engenharia Reversa & Algoritmos',
    mainSaboteur: 'Celular tarde da noite',
    pharma: {
      betaBlocker: false,
      glp1Agonist: false,
      adhdStimulant: false,
      statin: false,
      fluoroquinolone: false,
    },
    clinical: {
      parqWarning: false,
      bodyNeutralMode: false,
      interoceptiveSensitive: false,
    },
    createdAtIso: '2026-10-01T08:00:00.000Z',
    ...overrides,
  };
}

function makeCheckIn(bioDayId: string, overrides: Partial<DailyCheckIn> = {}): DailyCheckIn {
  return {
    bioDayId,
    timestampMs: Date.now(),
    sleepHours: 7.5,
    sleepQuality: 6,
    energyLevel: 6,
    mentalCalm: 6,
    muscularRecovery: 6,
    painKind: 'NENHUMA',
    painJoints: [],
    viralOrFeverSymptoms: false,
    externalLifeStressEvent: false,
    ...overrides,
  };
}

describe('Motor Psicofisiologico & Neuro-Motivacional v3.0 — Auditoria Deterministica', () => {
  it('1. Evita explosao de Z-Score em Cold-Start com variancia zero', () => {
    const vault = createInitialVault();
    const profile = makeProfile();
    vault.profile = profile;

    for (let i = 0; i < 6; i++) {
      const d = addDaysToBioDay('2026-10-01', i);
      vault.checkIns[d] = makeCheckIn(d, {
        sleepHours: 7.5,
        sleepQuality: 5,
        energyLevel: 5,
        mentalCalm: 5,
        muscularRecovery: 5,
      });
    }

    const day7 = makeCheckIn('2026-10-07', {
      sleepHours: 7.0,
      sleepQuality: 4,
      energyLevel: 4,
      mentalCalm: 5,
      muscularRecovery: 4,
    });
    const plan = prescribeDayPlan(profile, day7, vault);
    expect(Number.isFinite(plan.readiness.score)).toBe(true);
    expect(plan.readiness.zone).not.toBe('VERMELHO');
  });

  it('2. Elimina singularidade sigma=0 na Monotonia de Foster para caminhadas diarias constantes', () => {
    const vault = createInitialVault();
    const profile = makeProfile();
    vault.profile = profile;

    for (let i = -7; i <= -1; i++) {
      const d = addDaysToBioDay('2026-10-20', i);
      vault.ledger[d] = {
        bioDayId: d,
        status: 'LOGGED_ACTIVE',
        internalLoadAu: 90, // 30 min x RPE 3 identicos todos os dias (sigma = 0!)
        usedMinimumFloor: false,
      };
    }

    const plan = prescribeDayPlan(profile, makeCheckIn('2026-10-20'), vault);
    expect(Number.isFinite(plan.readiness.regularizedMonotony)).toBe(true);
    expect(plan.readiness.regularizedMonotony).toBeLessThanOrEqual(1.2);
  });

  it('3. Detecta deriva cronica (Sapo Fervendo) em queda progressiva de 7 dias', () => {
    const vault = createInitialVault();
    const profile = makeProfile();
    vault.profile = profile;

    const vals = [7, 6, 6, 5, 4, 3];
    vals.forEach((v, idx) => {
      const d = addDaysToBioDay('2026-10-10', idx);
      vault.checkIns[d] = makeCheckIn(d, {
        sleepHours: 4.8 + (6 - idx) * 0.4,
        sleepQuality: v,
        energyLevel: v,
        mentalCalm: v,
        muscularRecovery: v,
      });
    });

    const today = makeCheckIn('2026-10-16', {
      sleepHours: 5.0,
      sleepQuality: 3,
      energyLevel: 3,
      mentalCalm: 3,
      muscularRecovery: 3,
    });
    const plan = prescribeDayPlan(profile, today, vault);
    expect(plan.readiness.boilingFrogSlopePenalty).toBeGreaterThan(0);
  });

  it('4. Detector Anti-Goodhart: captura fadiga mascarada quando usuario mente 7/7 mas cai reps na barra', () => {
    const vault = createInitialVault();
    const profile = makeProfile({ level: 'INTERMEDIARIO', equipment: 'ACADEMIA' });
    vault.profile = profile;

    const repsSeq = [10, 8, 6]; // Queda consecutiva real com mesma carga!
    repsSeq.forEach((reps, i) => {
      const d = addDaysToBioDay('2026-10-01', i * 3);
      vault.workouts.push({
        id: `w_${i}`,
        bioDayId: d,
        timestampMs: 1700000000000 + i * 86400000,
        queueSlot: 'A',
        durationMinutes: 45,
        sessionRpe: 8,
        internalLoadAu: 360,
        sets: [{ exerciseId: 'push_barbell_bench', loadKg: 80, reps, rir: 1 }],
        completedAmccChallenge: true,
        engineVersion: '3.0.0',
      });
    });

    const lyingCheckIn = makeCheckIn('2026-10-10', {
      sleepHours: 8,
      sleepQuality: 7,
      energyLevel: 7,
      mentalCalm: 7,
      muscularRecovery: 7,
    });
    const plan = prescribeDayPlan(profile, lyingCheckIn, vault);
    expect(plan.readiness.maskedFatigueDetected).toBe(true);
    expect(plan.readiness.zone).toBe('AMARELO');
  });

  it('5. Travas farmacologicas: Betabloqueador, GLP-1 em IMC alto e Fluoroquinolona', () => {
    const vault = createInitialVault();
    const profile = makeProfile({
      weightKg: 138,
      heightCm: 170, // IMC ~47.7 -> deve ajustar massa de referencia de proteina!
      level: 'AVANCADO',
      pharma: {
        betaBlocker: true,
        glp1Agonist: true,
        adhdStimulant: false,
        statin: true,
        fluoroquinolone: true,
      },
    });
    vault.profile = profile;
    vault.currentPhase = 4;

    const plan = prescribeDayPlan(profile, makeCheckIn('2026-10-20'), vault);
    expect(plan.readiness.useTalkTestInsteadOfHr).toBe(true);
    expect(plan.readiness.allowPlyoAndHeavyEccentric).toBe(false);
    // Sem ajuste de IMC, 138 * 2.2 daria 304g absurdos; com ajuste fica racional (< 225g)!
    expect(plan.readiness.proteinTargetGrams[1]).toBeLessThan(225);
    expect(plan.readiness.proteinTargetGrams[0]).toBeGreaterThan(130);

    // Zero exercicio com alto impacto tendineo permitido sob fluoroquinolona
    for (const ex of plan.exercises) {
      const def = EXERCISE_CATALOG.find((c) => c.id === ex.exerciseId)!;
      expect(def.highTendonImpact).toBe(false);
    }
  });

  it('6. Bifurcacao de dor articular aguda: veta 100% dos vetores que estressam OMBRO', () => {
    const vault = createInitialVault();
    const profile = makeProfile({ equipment: 'ACADEMIA', level: 'INTERMEDIARIO' });
    vault.profile = profile;

    for (const slot of ['A', 'B', 'C'] as const) {
      vault.nextQueueSlot = slot;
      const plan = prescribeDayPlan(
        profile,
        makeCheckIn('2026-10-20', {
          painKind: 'ARTICULAR_TENDINEA_AGUDA',
          painJoints: ['OMBRO'],
        }),
        vault,
      );
      for (const ex of plan.exercises) {
        const def = EXERCISE_CATALOG.find((c) => c.id === ex.exerciseId)!;
        expect(def.stressedJoints.includes('OMBRO')).toBe(false);
      }
    }
  });

  it('7. Trava Pos-Viral + Histerese Anti-Bang-Bang + subordinacao do Goggins em estado Vermelho', () => {
    const vault = createInitialVault();
    const profile = makeProfile({ commandVoice: 'GOGGINS_MUSASHI' });
    vault.profile = profile;
    vault.currentPhase = 4;

    // Dia 1: Febre/sintoma viral -> VERMELHO imediato e Goggins exige recuperacao fria (zero treino pesado)
    const viralDay = makeCheckIn('2026-10-10', { viralOrFeverSymptoms: true });
    const planViral = prescribeDayPlan(profile, viralDay, vault);
    expect(planViral.readiness.zone).toBe('VERMELHO');
    expect(planViral.exercises.length).toBe(0);
    expect(planViral.pantheon.tacticalDirective.toLowerCase()).toContain('recuperação');

    // Dia 2: Febre passou e usuario se sente otimo -> ainda em rampa pos-viral + histerese pos-Vermelho!
    vault.lastViralSymptomBioDayId = '2026-10-10';
    vault.lastRedZoneBioDayId = '2026-10-10';
    const dayAfter = makeCheckIn('2026-10-11', {
      viralOrFeverSymptoms: false,
      sleepHours: 8.5,
      sleepQuality: 7,
      energyLevel: 7,
      mentalCalm: 7,
      muscularRecovery: 7,
    });
    const planAfter = prescribeDayPlan(profile, dayAfter, vault);
    expect(planAfter.readiness.zone).toBe('AMARELO');
    expect(planAfter.readiness.allowHighIntensityVo2).toBe(false);
    expect(planAfter.readiness.volumeMultiplier).toBeLessThanOrEqual(0.78);
  });

  it('8. Lei de Conservacao do Tempo, Segurança Interoceptiva e Dia Biologico pós-meia-noite', () => {
    const profile = makeProfile({
      usualWakeTime: '06:30',
      clinical: { parqWarning: false, bodyNeutralMode: false, interoceptiveSensitive: true },
    });
    const vault = createInitialVault();

    // 01:15 da madrugada ainda pertence ao dia biologico anterior!
    const lateNight = new Date(2026, 9, 25, 1, 15, 0); // 2026-10-25 01:15 local
    expect(computeBioDayId(lateNight, profile)).toBe('2026-10-24');

    for (const mins of [12, 18, 25, 40, 75]) {
      const plan = prescribeDayPlan(
        profile,
        makeCheckIn('2026-10-25', { availableMinutesToday: mins }),
        vault,
      );
      expect(plan.estimatedMinutes).toBeLessThanOrEqual(mins);
      expect(plan.mentalProtocol.mode).toBe('EXTEROCEPTIVO_OLHOS_ABERTOS');
    }
  });

  it('9. Fuzzing Caotico de 10.000 dias simulados — Zero NaN, Zero Infinity, Zero quebra de invariantes', () => {
    let seed = 133742;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };

    const envs: EquipmentEnv[] = ['CALISTENIA', 'CASA', 'ACADEMIA'];
    const joints: JointRegion[] = [
      'OMBRO',
      'COTOVELO_PUNHO',
      'LOMBAR',
      'QUADRIL',
      'JOELHO',
      'TORNOZELO_AQUILES',
    ];

    const vault: VaultState = createInitialVault();
    let curDay = '2026-01-01';

    for (let step = 0; step < 10000; step++) {
      const profile = makeProfile({
        age: Math.floor(16 + rand() * 68),
        weightKg: rand() < 0.02 ? Number.NaN : 40 + rand() * 160,
        heightCm: 145 + rand() * 55,
        equipment: envs[Math.floor(rand() * envs.length)],
        weekdayFreeMinutes: Math.floor(10 + rand() * 110),
        pharma: {
          betaBlocker: rand() < 0.2,
          glp1Agonist: rand() < 0.2,
          adhdStimulant: rand() < 0.2,
          statin: rand() < 0.2,
          fluoroquinolone: rand() < 0.15,
        },
        clinical: {
          parqWarning: rand() < 0.15,
          bodyNeutralMode: rand() < 0.2,
          interoceptiveSensitive: rand() < 0.25,
        },
      });
      vault.profile = profile;

      const painJoints = rand() < 0.25 ? [joints[Math.floor(rand() * joints.length)]] : [];
      const checkIn = makeCheckIn(curDay, {
        sleepHours: rand() < 0.02 ? Number.POSITIVE_INFINITY : rand() * 11,
        sleepQuality: Math.ceil(rand() * 7),
        energyLevel: Math.ceil(rand() * 7),
        mentalCalm: Math.ceil(rand() * 7),
        muscularRecovery: Math.ceil(rand() * 7),
        painKind: painJoints.length > 0 ? 'ARTICULAR_TENDINEA_AGUDA' : 'NENHUMA',
        painJoints,
        viralOrFeverSymptoms: rand() < 0.05,
        externalLifeStressEvent: rand() < 0.15,
      });

      const plan = prescribeDayPlan(profile, checkIn, vault);

      expect(Number.isFinite(plan.readiness.score)).toBe(true);
      expect(plan.readiness.score).toBeGreaterThanOrEqual(5);
      expect(plan.readiness.score).toBeLessThanOrEqual(99);
      expect(Number.isFinite(plan.readiness.volumeMultiplier)).toBe(true);
      expect(plan.readiness.volumeMultiplier).toBeGreaterThanOrEqual(0.3);
      expect(plan.readiness.volumeMultiplier).toBeLessThanOrEqual(1.05);
      expect(Number.isFinite(plan.readiness.acuteEwma)).toBe(true);
      expect(Number.isFinite(plan.readiness.regularizedMonotony)).toBe(true);

      // Joint veto + Fluoroquinolone tendon-veto invariants must hold across ALL 10,000 chaotic days!
      for (const ex of plan.exercises) {
        const def = EXERCISE_CATALOG.find((c) => c.id === ex.exerciseId)!;
        if (checkIn.painKind === 'ARTICULAR_TENDINEA_AGUDA') {
          for (const j of painJoints) {
            expect(def.stressedJoints.includes(j)).toBe(false);
          }
        }
        if (profile.pharma.fluoroquinolone || !plan.readiness.allowPlyoAndHeavyEccentric) {
          expect(def.highTendonImpact).toBe(false);
        }
      }

      // Record state & advance day
      vault.checkIns[curDay] = checkIn;
      if (plan.readiness.zone === 'VERMELHO') vault.lastRedZoneBioDayId = curDay;
      if (checkIn.viralOrFeverSymptoms) vault.lastViralSymptomBioDayId = curDay;

      if (rand() < 0.72 && !checkIn.viralOrFeverSymptoms) {
        const load = Math.round(25 * (3 + rand() * 6));
        vault.ledger[curDay] = {
          bioDayId: curDay,
          status: 'LOGGED_ACTIVE',
          internalLoadAu: load,
          usedMinimumFloor: rand() < 0.1,
        };
        vault.nextQueueSlot = advanceQueueSlot(vault.nextQueueSlot);
      } else if (rand() < 0.5) {
        vault.ledger[curDay] = {
          bioDayId: curDay,
          status: 'REST_CONFIRMED',
          internalLoadAu: 0,
          usedMinimumFloor: false,
        };
      }
      // Keep vault bounded in long fuzz run
      curDay = addDaysToBioDay(curDay, 1);
    }
  });
});
