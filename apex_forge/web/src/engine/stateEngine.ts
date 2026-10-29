import { selectExerciseForPattern } from './exerciseCatalog';
import { buildPantheonBriefing } from './pantheonEngine';
import {
  DailyCheckIn,
  ENGINE_VERSION,
  EvolutionPhase,
  JointRegion,
  MovementPattern,
  PrescribedDayPlan,
  PrescribedExercise,
  ReadinessComputation,
  ReadinessZone,
  UserProfile,
  VaultState,
  WorkoutSessionLog,
} from './types';

export function clamp(val: number, min: number, max: number): number {
  if (!Number.isFinite(val)) return min;
  return Math.min(max, Math.max(min, val));
}

export function parseTimeMinutes(hhmm: string, fallbackMinutes: number): number {
  const m = /^(\d{1,2}):(\d{2})$/.exec((hhmm || '').trim());
  if (!m) return fallbackMinutes;
  const h = Number(m[1]);
  const mins = Number(m[2]);
  if (!Number.isFinite(h) || !Number.isFinite(mins) || h < 0 || h > 23 || mins < 0 || mins > 59) {
    return fallbackMinutes;
  }
  return h * 60 + mins;
}

export function formatMinutesToHHMM(totalMinutes: number): string {
  const norm = ((Math.round(totalMinutes) % 1440) + 1440) % 1440;
  const hh = String(Math.floor(norm / 60)).padStart(2, '0');
  const mm = String(norm % 60).padStart(2, '0');
  return `${hh}:${mm}`;
}

/**
 * Wake-to-Sleep Biological Day ID: evita o bug da meia-noite.
 * O dia biologico so vira 3h antes do horario habitual de despertar.
 */
export function computeBioDayId(now: Date, profile?: UserProfile | null): string {
  const wakeMins = profile ? parseTimeMinutes(profile.usualWakeTime, 390) : 390; // default 06:30
  const rolloverMins = ((wakeMins - 180) + 1440) % 1440; // ex: 03:30
  const localMins = now.getHours() * 60 + now.getMinutes();
  const adjusted = new Date(now.getTime());
  if (rolloverMins < 720 && localMins < rolloverMins) {
    adjusted.setDate(adjusted.getDate() - 1);
  }
  const y = adjusted.getFullYear();
  const m = String(adjusted.getMonth() + 1).padStart(2, '0');
  const d = String(adjusted.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function addDaysToBioDay(bioDayId: string, deltaDays: number): string {
  const [y, m, d] = bioDayId.split('-').map(Number);
  const dt = new Date(Date.UTC(y || 2026, (m || 1) - 1, d || 1, 12, 0, 0));
  dt.setUTCDate(dt.getUTCDate() + deltaDays);
  return dt.toISOString().slice(0, 10);
}

export function diffBioDays(earlier: string, later: string): number {
  const [y1, m1, d1] = earlier.split('-').map(Number);
  const [y2, m2, d2] = later.split('-').map(Number);
  const t1 = Date.UTC(y1 || 2026, (m1 || 1) - 1, d1 || 1);
  const t2 = Date.UTC(y2 || 2026, (m2 || 1) - 1, d2 || 1);
  return Math.round((t2 - t1) / 86400000);
}

/**
 * Massa de referencia ajustada para evitar prescricao absurda de proteina em IMC > 27.
 */
export function computeAdjustedProteinMassKg(weightKg: number, heightCm: number): number {
  const safeW = clamp(weightKg, 35, 250);
  const hMeters = clamp(heightCm, 130, 230) / 100;
  const bmi = safeW / (hMeters * hMeters);
  if (bmi <= 27) return safeW;
  const idealAt25 = 25 * hMeters * hMeters;
  return idealAt25 + 0.25 * (safeW - idealAt25);
}

export function computeBioenergeticsAndHydration(profile: UserProfile) {
  const refKg = computeAdjustedProteinMassKg(profile.weightKg, profile.heightCm);
  const highProteinNeed =
    profile.energyGoal === 'DEFICIT_MODERADO' ||
    profile.pharma.glp1Agonist ||
    profile.age >= 50;

  const lowMult = highProteinNeed ? 1.8 : 1.6;
  const highMult = highProteinNeed ? 2.2 : 2.0;
  const proteinTargetGrams: [number, number] = [
    Math.round(refKg * lowMult),
    Math.round(refKg * highMult),
  ];

  let liters = clamp(profile.weightKg, 35, 200) * 0.035;
  if (profile.climate === 'CALOR_TROPICAL_UMIDO') liters += 0.6;
  if (profile.occupationalDemand === 'BRACAL_PESADO') liters += 0.5;
  if (profile.occupationalDemand === 'MISTO_EM_PE') liters += 0.25;
  const waterTargetLiters = Math.round(clamp(liters, 2.0, 5.2) * 10) / 10;

  const bedMins = parseTimeMinutes(profile.usualBedTime, 22 * 60 + 30);
  const cutoffMins = bedMins - 10 * 60; // 10h antes do sono (farmacocinetica da cafeina)
  const caffeineCutoffTime = formatMinutesToHHMM(cutoffMins);

  return {
    proteinTargetGrams,
    waterTargetLiters,
    caffeineCutoffTime,
    electrolyteAlert:
      profile.climate === 'CALOR_TROPICAL_UMIDO' ||
      profile.occupationalDemand === 'BRACAL_PESADO',
  };
}

/**
 * Detector objetivo Anti-Goodhart: detecta queda real de rendimento neuromuscular
 * mesmo se o usuario mentir 7/7 no check-in subjetivo.
 */
export function detectObjectiveMaskedFatigue(workouts: WorkoutSessionLog[]): boolean {
  if (workouts.length < 3) return false;
  const sorted = [...workouts].sort((a, b) => a.timestampMs - b.timestampMs);
  const byEx: Record<string, number[]> = {};

  for (const w of sorted.slice(-8)) {
    const bestPerEx: Record<string, number> = {};
    for (const s of w.sets) {
      if (s.reps <= 0) continue;
      const effLoad = Math.max(1, s.loadKg || 1);
      const e1rm = effLoad * (1 + (s.reps + clamp(s.rir, 0, 5)) / 30);
      bestPerEx[s.exerciseId] = Math.max(bestPerEx[s.exerciseId] ?? 0, e1rm);
    }
    for (const [exId, val] of Object.entries(bestPerEx)) {
      if (!byEx[exId]) byEx[exId] = [];
      byEx[exId].push(val);
    }
  }

  for (const series of Object.values(byEx)) {
    if (series.length >= 3) {
      const n = series.length;
      const e0 = series[n - 3];
      const e1 = series[n - 2];
      const e2 = series[n - 1];
      // Queda monotônica consecutiva (>= 2.5% por sessão) E perda acumulada >= 6% no e1RM
      if (e1 <= e0 * 0.975 && e2 <= e1 * 0.975 && e2 <= e0 * 0.94) {
        return true;
      }
    }
  }
  return false;
}

/**
 * Calcula EWMA desacoplada (aguda t-6..t vs cronica t-34..t-7) +
 * Monotonia regularizada de Foster sem explosao sigma=0 + imputacao conservadora de MISSING_LOG.
 */
export function computeWorkloadMetrics(
  bioDayId: string,
  profile: UserProfile,
  vault: VaultState,
) {
  const seedDailyLoad =
    (profile.level === 'INICIANTE' ? 95 : profile.level === 'INTERMEDIARIO' ? 165 : 240) +
    (profile.occupationalDemand === 'BRACAL_PESADO' ? 75 : profile.occupationalDemand === 'MISTO_EM_PE' ? 30 : 0);

  const createdBioDay = (profile.createdAtIso || bioDayId).slice(0, 10);
  const lambdaA = 2 / (7 + 1);   // 0.25
  const lambdaC = 2 / (28 + 1);  // ~0.068965

  let ewmaC = seedDailyLoad;
  const loads35: number[] = [];

  for (let offset = -34; offset <= 0; offset++) {
    const day = addDaysToBioDay(bioDayId, offset);
    const entry = vault.ledger[day];
    let dayLoad: number;

    if (day < createdBioDay) {
      dayLoad = seedDailyLoad * 0.85;
    } else if (!entry || entry.status === 'MISSING_LOG') {
      // Dia atual ainda nao executado = 0 ate treinar; dias passados sem log = imputacao conservadora!
      dayLoad = offset === 0 ? 0 : seedDailyLoad * 0.4;
    } else if (entry.status === 'REST_CONFIRMED') {
      dayLoad = 0;
    } else {
      dayLoad = clamp(entry.internalLoadAu, 0, 1800);
    }

    loads35.push(dayLoad);
    if (offset <= -7) {
      ewmaC = dayLoad * lambdaC + (1 - lambdaC) * ewmaC;
    }
  }

  let ewmaA = ewmaC;
  const last7 = loads35.slice(-7);
  for (const l of last7) {
    ewmaA = l * lambdaA + (1 - lambdaA) * ewmaA;
  }

  // Regularized Foster Monotony (excludes pure Z1 light walks < 100 AU from high-strain trap)
  const sum7 = last7.reduce((a, b) => a + b, 0);
  const mean7 = sum7 / 7;
  const variance7 = last7.reduce((acc, v) => acc + (v - mean7) ** 2, 0) / 7;
  const c0 = 65; // Regularizador que impede divisao por zero em caminhadas constantes!
  const rawMonotony = mean7 / Math.sqrt(variance7 + c0 * c0);
  const regularizedMonotony = sum7 > 1200 ? Math.round(rawMonotony * 100) / 100 : Math.min(1.2, Math.round(rawMonotony * 100) / 100);

  return {
    acuteEwma: Math.round(ewmaA * 10) / 10,
    uncoupledChronicEwma: Math.round(Math.max(40, ewmaC) * 10) / 10,
    regularizedMonotony,
    sum7,
    seedDailyLoad,
  };
}

function rawSubjectiveScore0to100(c: DailyCheckIn, targetSleepHours: number): number {
  const sleepRatio = clamp(c.sleepHours / clamp(targetSleepHours, 5.5, 10), 0.35, 1.12);
  const sleepHrsPts = clamp(((sleepRatio - 0.45) / (1.0 - 0.45)) * 100, 0, 100);
  const qSleep = ((clamp(c.sleepQuality, 1, 7) - 1) / 6) * 100;
  const qEnergy = ((clamp(c.energyLevel, 1, 7) - 1) / 6) * 100;
  const qCalm = ((clamp(c.mentalCalm, 1, 7) - 1) / 6) * 100;
  const qMusc = ((clamp(c.muscularRecovery, 1, 7) - 1) / 6) * 100;

  return (
    0.32 * sleepHrsPts +
    0.16 * qSleep +
    0.20 * qEnergy +
    0.16 * qCalm +
    0.16 * qMusc
  );
}

/**
 * Estimador Ortogonal Bayesiano de Prontidao v3.0
 */
export function computeReadiness(
  profile: UserProfile,
  checkIn: DailyCheckIn,
  vault: VaultState,
): ReadinessComputation {
  const glassBoxReasons: string[] = [];
  const activeVetoes: string[] = [];
  const bio = computeBioenergeticsAndHydration(profile);
  const wl = computeWorkloadMetrics(checkIn.bioDayId, profile, vault);

  const absScore = rawSubjectiveScore0to100(checkIn, profile.targetSleepHours);

  // 1. Empirical Bayes 60-day healthy baseline (prevents Cold-Start sigma=0 explosion!)
  const historicalScores: number[] = [];
  for (let off = -60; off <= -1; off++) {
    const dId = addDaysToBioDay(checkIn.bioDayId, off);
    const past = vault.checkIns[dId];
    if (past && !past.viralOrFeverSymptoms) {
      historicalScores.push(rawSubjectiveScore0to100(past, profile.targetSleepHours));
    }
  }

  const priorMean = 72;
  const priorSd = 11.5; // equivalente a sigma >= 0.75 na escala 1..7
  const n = historicalScores.length;
  const sampleMean = n > 0 ? historicalScores.reduce((a, b) => a + b, 0) / n : priorMean;
  const sampleVar =
    n > 1
      ? historicalScores.reduce((acc, x) => acc + (x - sampleMean) ** 2, 0) / (n - 1)
      : priorSd * priorSd;

  const k = 6;
  const shrunkMean = (n * sampleMean + k * priorMean) / (n + k);
  const shrunkSd = Math.max(9.0, Math.sqrt((n * sampleVar + k * priorSd * priorSd) / (n + k)));
  const zScore = clamp((absScore - shrunkMean) / shrunkSd, -3.0, 2.5);
  const relScore = clamp(72 + zScore * 14, 10, 98);

  // 2. Orthogonal Recovery Residual (evita tripla contagem entre carga EWMA e fadiga subjetiva!)
  const loadRatio = wl.acuteEwma / Math.max(40, wl.uncoupledChronicEwma);
  const expectedDipFromLoad = clamp((loadRatio - 1.0) * 14, -6, 18);
  const expectedSubjective = clamp(shrunkMean - expectedDipFromLoad, 35, 88);
  const recoveryResidual = Math.round((absScore - expectedSubjective) * 10) / 10;

  // Dual-Anchor blend (45% fisiologica absoluta + 55% baseline Bayesiana)
  let composite = 0.45 * absScore + 0.55 * relScore;

  // Penalize ONLY uncompensated overload (evita penalizar 3x o mesmo treino!)
  if (loadRatio > 1.38 && recoveryResidual < 0) {
    const spikePen = clamp((loadRatio - 1.38) * 22, 0, 14);
    composite -= spikePen;
    glassBoxReasons.push(
      `Pico agudo de carga detectado (EWMA ${loadRatio.toFixed(2)}x) com recuperação abaixo do esperado.`,
    );
  }

  if (wl.regularizedMonotony > 1.85) {
    composite -= 7;
    glassBoxReasons.push(
      `Monotonia de carga elevada (${wl.regularizedMonotony.toFixed(2)}): inserindo variação protetiva.`,
    );
  }

  // 3. Anti-Boiling-Frog: penalidade por inclinacao descendente sustentada em 7 dias
  const recent7: number[] = [];
  for (let off = -6; off <= 0; off++) {
    const dId = addDaysToBioDay(checkIn.bioDayId, off);
    const c = off === 0 ? checkIn : vault.checkIns[dId];
    if (c) recent7.push(rawSubjectiveScore0to100(c, profile.targetSleepHours));
  }
  let boilingFrogSlopePenalty = 0;
  if (recent7.length >= 5) {
    const m = recent7.length;
    const xMean = (m - 1) / 2;
    const yMean = recent7.reduce((a, b) => a + b, 0) / m;
    let num = 0;
    let den = 0;
    for (let i = 0; i < m; i++) {
      num += (i - xMean) * (recent7[i] - yMean);
      den += (i - xMean) ** 2;
    }
    const slope = den > 0 ? num / den : 0;
    if (slope < -1.8 && absScore < 68) {
      boilingFrogSlopePenalty = Math.round(clamp(Math.abs(slope) * 2.5, 4, 12));
      composite -= boilingFrogSlopePenalty;
      glassBoxReasons.push(
        `Tendência acumulada de queda nos últimos 7 dias (-${boilingFrogSlopePenalty} pts anti-esgotamento silencioso).`,
      );
    }
  }

  // Crise aguda externa (Carga Alostatica Unificada - Stults-Kolehmainen 2014)
  if (checkIn.externalLifeStressEvent) {
    composite -= 10;
    glassBoxReasons.push(
      'Evento de estresse externo agudo ativo: orçamento alostático ajustado para preservar recuperação em 96h.',
    );
  }

  // 4. Connective Tissue 90-Day Rate-Limiter (assimetria musculo vs tendao)
  const daysSinceStart = Math.max(
    0,
    diffBioDays((profile.createdAtIso || checkIn.bioDayId).slice(0, 10), checkIn.bioDayId),
  );
  const connectiveTissueCapPct = daysSinceStart < 90 && profile.level === 'INICIANTE' ? 6.0 : 10.0;

  // 5. Anti-Goodhart Objective Masked Fatigue
  const maskedFatigueDetected = detectObjectiveMaskedFatigue(vault.workouts);
  if (maskedFatigueDetected) {
    composite = Math.min(composite, 68);
    glassBoxReasons.push(
      'Auditoria objetiva: queda consecutiva de rendimento na barra detectada — volume contido para supercompensação.',
    );
  }

  // 6. Hard Clinical, Pharmacological & Post-Viral Vetoes (Camada 1)
  let forceZone: ReadinessZone | null = null;
  let allowHighIntensityVo2 = true;
  let allowPlyoAndHeavyEccentric = true;

  if (checkIn.viralOrFeverSymptoms) {
    forceZone = 'VERMELHO';
    allowHighIntensityVo2 = false;
    allowPlyoAndHeavyEccentric = false;
    composite = Math.min(composite, 25);
    activeVetoes.push('VETO MÉDICO PÓS-VIRAL/FEBRE: alta intensidade bloqueada para proteção cardiopulmonar.');
  }

  // Rampa pos-viral de 5 dias mesmo apos cessar febre
  if (!checkIn.viralOrFeverSymptoms && vault.lastViralSymptomBioDayId) {
    const dViral = diffBioDays(vault.lastViralSymptomBioDayId, checkIn.bioDayId);
    if (dViral > 0 && dViral <= 5) {
      forceZone = forceZone === 'VERMELHO' ? 'VERMELHO' : 'AMARELO';
      allowHighIntensityVo2 = false;
      composite = Math.min(composite, 66);
      activeVetoes.push(
        `RAMPA PÓS-VIRAL (Dia ${dViral}/5): retorno progressivo submáximo obrigatório.`,
      );
    }
  }

  if (checkIn.sleepHours < 4.5) {
    forceZone = 'VERMELHO';
    allowHighIntensityVo2 = false;
    composite = Math.min(composite, 38);
    activeVetoes.push(
      `PRIVACÃO AGUDA DE SONO (${checkIn.sleepHours}h < 4.5h): veto automático contra lesão e pico de cortisol.`,
    );
  } else if (checkIn.sleepHours < 5.8) {
    if (!forceZone) forceZone = 'AMARELO';
    allowHighIntensityVo2 = false;
    composite = Math.min(composite, 68);
    glassBoxReasons.push(`Sono reduzido (${checkIn.sleepHours}h): HIIT suspenso e volume reduzido.`);
  }

  if (profile.clinical.parqWarning) {
    allowHighIntensityVo2 = false;
    activeVetoes.push('MODO CLÍNICO PROTEGIDO (PAR-Q+): intensidade máxima e falha concêntrica bloqueadas.');
  }

  if (profile.pharma.fluoroquinolone) {
    allowPlyoAndHeavyEccentric = false;
    activeVetoes.push('ALERTA FLUOROQUINOLONA: impacto, sprints e sobrecarga excêntrica tendínea bloqueados.');
  }

  if (checkIn.painKind === 'ARTICULAR_TENDINEA_AGUDA' && checkIn.painJoints.length > 0) {
    allowPlyoAndHeavyEccentric = false;
    activeVetoes.push(
      `VETO BIOMECÂNICO LOCAL (${checkIn.painJoints.join(', ')}): vetores dolorosos substituídos por variantes indolores.`,
    );
  }

  if (profile.pharma.statin && checkIn.muscularRecovery <= 3) {
    glassBoxReasons.push(
      'Uso de estatina + dor muscular elevada: diferencie DOMS normal de mialgia medicamentosa persistente.',
    );
  }

  const score = Math.round(clamp(composite, 5, 99));
  let zone: ReadinessZone =
    forceZone ?? (score >= 74 ? 'VERDE' : score >= 48 ? 'AMARELO' : 'VERMELHO');

  // 7. Continuous Proportional Volume Multiplier + Post-Red Hysteresis Damping!
  let volumeMultiplier =
    zone === 'VERMELHO'
      ? 0.35
      : clamp(0.55 + ((score - 48) / (92 - 48)) * 0.50, 0.55, 1.05);

  if (profile.energyGoal === 'DEFICIT_MODERADO' || profile.pharma.glp1Agonist) {
    volumeMultiplier *= 0.82; // Murphy & Koehler 2022 / GLP-1 anticatabolic recovery adjustment
    glassBoxReasons.push(
      profile.pharma.glp1Agonist
        ? 'Protocolo Anticatabólico GLP-1 ativo: volume enxuto (-18%) mantendo tensão mecânica e proteína alta.'
        : 'Déficit energético ativo: volume ajustado (-18%) mantendo intensidade na barra para preservar massa magra.',
    );
  }

  if (profile.occupationalDemand === 'BRACAL_PESADO') {
    volumeMultiplier *= 0.82;
    glassBoxReasons.push(
      'Ajuste Paradoxo Ocupacional (Holtermann): volume ortopédico reduzido para compensar jornada física.',
    );
  }

  // Hysteresis anti-Bang-Bang: dia imediatamente apos VERMELHO tem teto suave de 0.78
  if (
    zone !== 'VERMELHO' &&
    vault.lastRedZoneBioDayId &&
    diffBioDays(vault.lastRedZoneBioDayId, checkIn.bioDayId) === 1
  ) {
    volumeMultiplier = Math.min(volumeMultiplier, 0.78);
    allowHighIntensityVo2 = false;
    glassBoxReasons.push(
      'Amortecimento pós-alerta Vermelho (histerese): reentrada progressiva a 78% hoje para evitar efeito pingue-pongue.',
    );
  }

  // Detraining / Hiatus Ramp-Back (se ficou >= 7 dias sem sessao ativa)
  if (vault.workouts.length > 0) {
    const lastWorkout = vault.workouts[vault.workouts.length - 1];
    const daysOff = diffBioDays(lastWorkout.bioDayId, checkIn.bioDayId);
    if (daysOff >= 7 && zone !== 'VERMELHO') {
      const rampFactor = daysOff >= 21 ? 0.62 : daysOff >= 12 ? 0.72 : 0.82;
      volumeMultiplier = Math.min(volumeMultiplier, rampFactor);
      glassBoxReasons.push(
        `Rampa de Reentrada Pós-Hiato (${daysOff} dias sem sessão): volume em ${Math.round(
          rampFactor * 100,
        )}% para evitar DOMS incapacitante.`,
      );
    }
  }

  volumeMultiplier = Math.round(clamp(volumeMultiplier, 0.3, 1.05) * 100) / 100;

  let intensityRirFloor = zone === 'VERDE' ? 2 : zone === 'AMARELO' ? 3 : 4;
  if (profile.level === 'INICIANTE' || profile.clinical.parqWarning) {
    intensityRirFloor = Math.max(intensityRirFloor, 3);
  }

  if (glassBoxReasons.length === 0 && activeVetoes.length === 0) {
    glassBoxReasons.push(
      'Homeostase e recuperação alinhadas: sinal verde para progressão controlada nos 5 eixos.',
    );
  }

  return {
    engineVersion: ENGINE_VERSION,
    bioDayId: checkIn.bioDayId,
    score,
    zone,
    volumeMultiplier,
    intensityRirFloor,
    allowHighIntensityVo2: allowHighIntensityVo2 && zone === 'VERDE' && vault.currentPhase >= 3,
    allowPlyoAndHeavyEccentric,
    useTalkTestInsteadOfHr: profile.pharma.betaBlocker,
    maskedFatigueDetected,
    boilingFrogSlopePenalty,
    recoveryResidual,
    acuteEwma: wl.acuteEwma,
    uncoupledChronicEwma: wl.uncoupledChronicEwma,
    regularizedMonotony: wl.regularizedMonotony,
    connectiveTissueCapPct,
    proteinTargetGrams: bio.proteinTargetGrams,
    waterTargetLiters: bio.waterTargetLiters,
    electrolyteAlert: bio.electrolyteAlert,
    caffeineCutoffTime: bio.caffeineCutoffTime,
    glassBoxReasons,
    activeVetoes,
  };
}

function slotPatterns(slot: 'A' | 'B' | 'C', allowVo2: boolean): MovementPattern[] {
  if (slot === 'A') {
    return ['KNEE_DOM', 'PUSH_H', 'PULL_H', 'CORE_STAB'];
  }
  if (slot === 'B') {
    return ['HIP_DOM', 'PUSH_V', 'PULL_V', 'CARDIO_Z2'];
  }
  return ['KNEE_DOM', 'PULL_H', 'PUSH_H', allowVo2 ? 'CARDIO_VO2' : 'CARDIO_Z2'];
}

function buildProgressionAxisNote(
  profile: UserProfile,
  rirFloor: number,
  capPct: number,
  isCardio: boolean,
  useTalkTest: boolean,
): string {
  if (isCardio) {
    return useTalkTest
      ? 'Betabloqueador ativo: ignore batimentos por minuto — guie 100% pelo Teste da Fala e RPE.'
      : profile.climate === 'CALOR_TROPICAL_UMIDO'
      ? 'Calor/umidade: compense o desvio cardiovascular mantendo o esforço percebido constante + água/eletrólitos.'
      : 'Distribuição Polarizada 80/20 (Seiler): mantenha disciplina estrita na zona alvo.';
  }
  if (profile.equipment === 'CALISTENIA') {
    return `5 Eixos Calistenia: suba 1–2 reps mantendo cadência até o topo da faixa antes de avançar alavanca (RIR ≥ ${rirFloor}).`;
  }
  if (profile.equipment === 'CASA') {
    return `5 Eixos Casa: se o próximo par de halteres saltar >10%, progrida primeiro em pausas/repetições (teto tendíneo ≤ ${capPct}%/sem).`;
  }
  return `Dupla Progressão Academia: ao atingir o topo de reps em todas as séries com RIR ${rirFloor}, suba 2,5–5% na próxima sessão (teto ≤ ${capPct}%/sem).`;
}

/**
 * Gera o Plano Diario Completo respeitando estritamente a Lei de Conservacao do Tempo (sem roubar sono!)
 */
export function prescribeDayPlan(
  profile: UserProfile,
  checkIn: DailyCheckIn,
  vault: VaultState,
): PrescribedDayPlan {
  const readiness = computeReadiness(profile, checkIn, vault);
  const pantheon = buildPantheonBriefing(profile, checkIn, readiness, vault);

  const rawBudget = clamp(
    checkIn.availableMinutesToday ?? profile.weekdayFreeMinutes,
    10,
    180,
  );
  const mentalDuration = rawBudget <= 20 ? 3 : 5;
  const physicalBudget = Math.max(8, rawBudget - mentalDuration);

  const vetoedJoints =
    checkIn.painKind === 'ARTICULAR_TENDINEA_AGUDA'
      ? new Set<JointRegion>(checkIn.painJoints)
      : new Set<JointRegion>();

  const blockTendon =
    !readiness.allowPlyoAndHeavyEccentric ||
    profile.pharma.fluoroquinolone ||
    readiness.connectiveTissueCapPct <= 6.0;

  const reduceAxial =
    profile.occupationalDemand === 'BRACAL_PESADO' || vetoedJoints.has('LOMBAR');

  let queueSlot: PrescribedDayPlan['queueSlot'] = vault.nextQueueSlot;
  let sessionTitle = '';
  let exercises: PrescribedExercise[] = [];

  if (readiness.zone === 'VERMELHO') {
    queueSlot = 'RECUPERACAO_ATIVA';
    sessionTitle = checkIn.viralOrFeverSymptoms
      ? 'Protocolo de Repouso Clínico & Regulação Vagal'
      : 'Sessão Regenerativa — Descompressão & Fluxo Sanguíneo';

    if (!checkIn.viralOrFeverSymptoms) {
      const mobPatterns: MovementPattern[] = ['MOBILITY_DECOMPRESS', 'CORE_STAB', 'CARDIO_Z2'];
      exercises = mobPatterns.map((pat) => {
        const { variant } = selectExerciseForPattern(pat, profile.equipment, 'INICIANTE', vetoedJoints, true, true);
        return {
          exerciseId: variant.id,
          name: variant.name,
          pattern: pat,
          sets: variant.isCardio ? 1 : 2,
          targetReps: variant.isCardio ? '12–15 min leve' : `${variant.repRange[0]}`,
          targetRir: variant.isCardio ? 'Zona 1 regenerativa (fala fácil)' : 'Esforço leve 0% dor',
          tempoCue: variant.tempoCue,
          progressionAxisNote: 'Objetivo hoje: restaurar tônus parassimpático e nutrir articulações.',
        };
      });
    }
  } else {
    const slotNames = {
      A: 'Sessão A — Base Inferior, Empurrar & Puxar Horizontal',
      B: 'Sessão B — Cadeia Posterior, Vertical & Base Aeróbica Z2',
      C: 'Sessão C — Full-Body Integrado & Estímulo Polarizado',
    };
    sessionTitle = slotNames[vault.nextQueueSlot];
    const patterns = slotPatterns(vault.nextQueueSlot, readiness.allowHighIntensityVo2);

    // Respeita a Lei de Conservacao do Tempo: ajusta numero de exercicios e series para caber em physicalBudget!
    const maxExercises = physicalBudget < 20 ? 2 : physicalBudget < 32 ? 3 : patterns.length;
    const chosenPatterns = patterns.slice(0, maxExercises);

    exercises = chosenPatterns.map((pat) => {
      const { variant, substitutedReason } = selectExerciseForPattern(
        pat,
        profile.equipment,
        profile.level,
        vetoedJoints,
        blockTendon,
        reduceAxial,
      );

      let sets = Math.max(1, Math.round(variant.defaultSets * readiness.volumeMultiplier));
      if (physicalBudget < 25 && !variant.isCardio) {
        sets = Math.min(sets, 2);
      }

      const cardioMinutes = Math.max(10, Math.min(25, Math.round(physicalBudget * 0.38)));
      const targetReps = variant.isCardio
        ? pat === 'CARDIO_VO2'
          ? '4x 3 min forte / 2.5 min leve'
          : `${cardioMinutes} min contínuos`
        : `${variant.repRange[0]}–${variant.repRange[1]}`;

      const targetRir = variant.isCardio
        ? readiness.useTalkTestInsteadOfHr
          ? pat === 'CARDIO_VO2'
            ? 'RPE 8.5 (fala 1–2 palavras)'
            : 'Teste da Fala: frases completas (RPE 3–4)'
          : pat === 'CARDIO_VO2'
          ? 'Zona 4–5 (~90% VO2max / RPE 8.5–9)'
          : 'Zona 2 (<2 mmol/L lactato / conversa fluente)'
        : profile.level === 'INICIANTE'
        ? `RIR Técnico ${readiness.intensityRirFloor} (pare na 1ª perda de postura)`
        : `RIR ${readiness.intensityRirFloor} (RPE ${10 - readiness.intensityRirFloor})`;

      return {
        exerciseId: variant.id,
        name: variant.name,
        pattern: pat,
        sets: variant.isCardio && pat === 'CARDIO_Z2' ? 1 : sets,
        targetReps,
        targetRir,
        tempoCue: variant.tempoCue,
        progressionAxisNote: buildProgressionAxisNote(
          profile,
          readiness.intensityRirFloor,
          readiness.connectiveTissueCapPct,
          variant.isCardio,
          readiness.useTalkTestInsteadOfHr,
        ),
        substitutedReason,
      };
    });
  }

  // Estimativa realista de duracao (garantindo <= rawBudget!)
  const estPhys =
    exercises.length === 0
      ? 5
      : Math.min(
          physicalBudget,
          exercises.reduce((acc, ex) => acc + (ex.pattern.startsWith('CARDIO') ? 14 : ex.sets * 3), 4),
        );

  // Doctor Who 15-Minute Emergency Bodyweight Pivot
  const pivotEx1 = selectExerciseForPattern('KNEE_DOM', 'CALISTENIA', profile.level, vetoedJoints, true, true);
  const pivotEx2 = selectExerciseForPattern('PUSH_H', 'CALISTENIA', profile.level, vetoedJoints, true, true);
  const pivotEx3 = selectExerciseForPattern('PULL_H', 'CALISTENIA', profile.level, vetoedJoints, true, true);

  const doctorWho15MinPivot = {
    title: 'Pivot Tático 15 min (Supersérie Densidade Zero Desculpa)',
    exercises: [pivotEx1, pivotEx2, pivotEx3].map(({ variant, substitutedReason }) => ({
      exerciseId: variant.id,
      name: variant.name,
      pattern: variant.pattern,
      sets: 2,
      targetReps: `${variant.repRange[0]}–${variant.repRange[1]}`,
      targetRir: `RIR ${Math.max(2, readiness.intensityRirFloor)}`,
      tempoCue: 'Supersérie contínua (30s transição)',
      progressionAxisNote: 'Modo Contingência Doctor Who: preserva sinal neural e metabolismo em 15 min.',
      substitutedReason,
    })),
  };

  // Unbreakable 5-Minute Minimum Floor (vmPFC Behavioral Control + Habit Chain Preservation)
  const minimumFloor5Min = {
    title: 'Piso Mínimo Inquebrável — 5 Minutos (Elo Neural Intacto)',
    steps: checkIn.viralOrFeverSymptoms
      ? [
          '2 min de respiração lenta sentado ou deitado sem telas',
          'Beber 400 ml de água com calma',
          'Confirmar horário protegido de sono de hoje',
        ]
      : [
          '90 segundos de mobilidade articular sem dor (escápulas + quadril)',
          '1 série controlada de Agachamento ou Isometria + 1 série de Empurrar/Prancha',
          '90 segundos de regulação autonômica (expiração prolongada)',
        ],
  };

  // Safe Mental Protocol Selection (respecting Farias et al. 2020 interoceptive safety!)
  let mentalProtocol: PrescribedDayPlan['mentalProtocol'];
  if (profile.clinical.interoceptiveSensitive) {
    mentalProtocol = {
      id: 'mental_exteroceptive_grounding',
      title: 'Ancoragem Exteroceptiva de Olhos Abertos (Segurança Anti-Ansiedade)',
      durationMin: mentalDuration,
      mode: 'EXTEROCEPTIVO_OLHOS_ABERTOS',
      instructions: [
        'Mantenha os olhos ABERTOS focados em um ponto fixo externo (evita hipervigilância cardíaca interna).',
        'Acompanhe o guia sonoro/visual na cadência suave 4s entrada / 6s saída sem forçar pulmões.',
        'Nomeie mentalmente 3 detalhes geométricos reais no ambiente e a única ação concreta a seguir.',
      ],
    };
  } else if (checkIn.mentalCalm <= 3 || checkIn.externalLifeStressEvent) {
    mentalProtocol = {
      id: 'mental_physio_sigh_act',
      title: 'Descompressão Autonômica Rápida + Desfusão ACT',
      durationMin: mentalDuration,
      mode: 'SUSPIRO_FISIOLOGICO',
      instructions: [
        'Dupla inspiração nasal (enche alvéolos + pequeno topo extra) seguida de expiração longa e solta pela boca.',
        'Desfusão Cognitiva (Hayes): observe o pensamento estressor como "apenas texto na tela mental", sem discutir com ele.',
        'Direcione 100% da atenção motora para os próximos 10 minutos sob seu controle.',
      ],
    };
  } else {
    mentalProtocol = {
      id: 'mental_resonance_01hz',
      title: 'Biofeedback de Frequência de Ressonância (~0,1 Hz / 5,5 resp/min)',
      durationMin: mentalDuration,
      mode: 'RESPIRACAO_01HZ',
      instructions: [
        'Inspire suavemente pelo nariz por 4,5 segundos expandindo as costelas baixas.',
        'Expire de forma contínua e silenciosa por 6,0 segundos (maximiza tônus vagal e amplitude de VFC).',
        'Nos 60 segundos finais, execute a Câmara Tesla: visualize em 1ª pessoa sua execução técnica perfeita hoje.',
      ],
    };
  }

  return {
    bioDayId: checkIn.bioDayId,
    queueSlot,
    sessionTitle,
    estimatedMinutes: Math.min(rawBudget, estPhys + mentalDuration),
    minimumFloor5Min,
    doctorWho15MinPivot,
    exercises,
    mentalProtocol,
    readiness,
    pantheon,
  };
}

/**
 * Avalia criterios transparentes para progressao nas 5 Fases (Ignicao -> Consolidacao 66d -> Intensificacao -> Alta Performance -> Apice)
 */
export function evaluateEvolutionPhase(vault: VaultState): {
  phase: EvolutionPhase;
  phaseName: string;
  activeDaysCount: number;
  consistencyPctLast14d: number;
  nextUnlockRequirement: string;
} {
  const entries = Object.values(vault.ledger);
  const activeDaysCount = entries.filter(
    (e) => e.status === 'LOGGED_ACTIVE' || e.usedMinimumFloor,
  ).length;

  const confirmedDays = entries.filter((e) => e.status !== 'MISSING_LOG').length;
  const dpCount = vault.deliberatePractice.length;

  let phase: EvolutionPhase = 1;
  if (activeDaysCount >= 180 && dpCount >= 40) phase = 5;
  else if (activeDaysCount >= 95 && dpCount >= 20) phase = 4;
  else if (activeDaysCount >= 55 && dpCount >= 8) phase = 3;
  else if (activeDaysCount >= 18 && dpCount >= 2) phase = 2;

  const names: Record<EvolutionPhase, string> = {
    1: 'Fase I — Ignição & Ritmo Circadiano',
    2: 'Fase II — Consolidação Neural (Rumo aos 66 Dias)',
    3: 'Fase III — Intensificação Polarizada 80/20 & MAC',
    4: 'Fase IV — Alta Performance & Prática Deliberada',
    5: 'Fase V — Ápice Sustentável & Autonomia Intrínseca',
  };

  const reqs: Record<EvolutionPhase, string> = {
    1: `Acumular 18 dias ativos (${activeDaysCount}/18) + 2 blocos auditados de Prática Deliberada (${dpCount}/2).`,
    2: `Cruzar a mediana científica de hábito: 55 dias ativos (${activeDaysCount}/55) + 8 blocos de Prática Deliberada (${dpCount}/8).`,
    3: `Atingir 95 dias ativos (${activeDaysCount}/95) + 20 blocos de Prática Deliberada (${dpCount}/20) sem lesão.`,
    4: `Consolidar 180 dias ativos (${activeDaysCount}/180) + 40 blocos de Prática Deliberada (${dpCount}/40).`,
    5: 'Nível Máximo Alcançado: foco em maestria multi-anual, longevidade articular e estado de Flow.',
  };

  const consistencyPctLast14d =
    confirmedDays === 0
      ? 100
      : Math.round(clamp((activeDaysCount / Math.max(1, entries.length)) * 100, 0, 100));

  return {
    phase,
    phaseName: names[phase],
    activeDaysCount,
    consistencyPctLast14d,
    nextUnlockRequirement: reqs[phase],
  };
}

export function advanceQueueSlot(current: 'A' | 'B' | 'C'): 'A' | 'B' | 'C' {
  return current === 'A' ? 'B' : current === 'B' ? 'C' : 'A';
}

export function createInitialVault(): VaultState {
  return {
    engineVersion: ENGINE_VERSION,
    profile: null,
    currentPhase: 1,
    nextQueueSlot: 'A',
    lastRedZoneBioDayId: null,
    lastViralSymptomBioDayId: null,
    checkIns: {},
    ledger: {},
    workouts: [],
    deliberatePractice: [],
    cognitiveLogs: [],
    teachingProgress: {},
    completedFieldMissions: {},
    simulatorStats: {
      bestScore: 0,
      completedRuns: 0,
      lastRankTitle: 'Marco Zero',
      lastCompletedBioDayId: '',
    },
    skillBlueprints: [],
    eveningReflections: {},
    decisionJournal: [],
    chessState: {
      playRating: 800,
      playEloCategory: 'INICIANTE',
      puzzleRating: 800,
      puzzleRushBest: 0,
      visionBestScore: 0,
      blindfoldWins: 0,
      gamesPlayed: 0,
      wins: 0,
      losses: 0,
      draws: 0,
      solvedPuzzleIds: [],
      completedAcademyIds: [],
      completedEndgameIds: [],
      completedRepertoireIds: [],
      preferredTheme: 'CHESS_VERDE',
      soundEnabled: true,
      savedGames: [],
      achievements: [],
      totalBrilliants: 0,
      totalBlunders: 0,
      longestWinStreak: 0,
      currentWinStreak: 0,
      openingsPlayed: {},
      dailyPuzzleLastDate: undefined,
      dailyPuzzleSolved: false,
      emotionalCheckIns: [],
    },
    contracts: [],
    markUpgrades: [],
    cookieJar: [],
    resonanceSessionsCount: 0,
  };
}
