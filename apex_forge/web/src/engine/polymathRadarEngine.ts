import { clamp } from './stateEngine';
import { TEACHING_TRACKS, TEACHINGS_CATALOG } from './teachingsCatalog';
import { TeachingTrackId, VaultState } from './types';

export interface PillarRadarAxis {
  trackId: TeachingTrackId;
  shortLabel: string;
  fullTitle: string;
  studiedLessons: number;
  totalLessons: number;
  fieldMissionsDone: number;
  score100: number;           // 0..100
}

export interface PolymathRadarReport {
  axes: PillarRadarAxis[];    // Exatamente 10 eixos na ordem de TEACHING_TRACKS
  meanScore100: number;       // Media global 0..100
  harmonyIndex100: number;    // Penaliza desequilibrio severo entre pilares (Goldratt)
  strongestAxis: PillarRadarAxis;
  weakestAxis: PillarRadarAxis;
}

export function computePolymathRadar(vault: VaultState): PolymathRadarReport {
  const progress = vault.teachingProgress ?? {};
  const missions = vault.completedFieldMissions ?? {};
  const cogLogs = vault.cognitiveLogs ?? [];
  const reflectionsCount = Object.keys(vault.eveningReflections ?? {}).length;
  const workoutsCount = vault.workouts.length;
  const practiceCount = vault.deliberatePractice.length;
  const blueprintsCount = (vault.skillBlueprints ?? []).length;
  const decisionsCount = (vault.decisionJournal ?? []).length;
  const contractsCount = vault.contracts.length;
  const markCount = vault.markUpgrades.length;
  const cookiesCount = vault.cookieJar.length;

  const resolvedDecisionsCount = (vault.decisionJournal ?? []).filter((d) =>
    Boolean(d.resolvedOutcome),
  ).length;
  const chessGamesCount = vault.chessState?.gamesPlayed ?? 0;
  const chessPuzzlesCount = vault.chessState?.solvedPuzzleIds.length ?? 0;
  const chessVisionBest = vault.chessState?.visionBestScore ?? 0;
  const chessAcademyCount = vault.chessState?.completedAcademyIds?.length ?? 0;
  const chessEndgamesCount = vault.chessState?.completedEndgameIds?.length ?? 0;
  const chessRepertoireCount = vault.chessState?.completedRepertoireIds?.length ?? 0;
  const chessBlindfoldWins = vault.chessState?.blindfoldWins ?? 0;
  const resonanceCount = vault.resonanceSessionsCount ?? 0;

  const behavioralBonusFor = (trackId: TeachingTrackId): number => {
    switch (trackId) {
      case 'CRISTO_EVANGELHOS':
        return Math.min(15, reflectionsCount * 3 + (vault.simulatorStats?.completedRuns ?? 0) * 5);
      case 'SABEDORIA_BIBLICA':
        return Math.min(15, reflectionsCount * 3 + contractsCount * 2.5 + decisionsCount * 3);
      case 'GARRA_AUTODOMINIO':
        return Math.min(
          15,
          cookiesCount * 2.5 +
            workoutsCount * 1.2 +
            resonanceCount * 1.5 +
            cogLogs.filter((c) => c.challengeType === 'FLEXIBILIDADE_TRAIL').length * 2,
        );
      case 'APRENDIZAGEM_MEMORIA':
        return Math.min(
          15,
          practiceCount * 3 +
            blueprintsCount * 4 +
            chessAcademyCount * 1.5 +
            chessRepertoireCount * 1.2 +
            chessBlindfoldWins * 2.5 +
            (chessVisionBest >= 15 ? 2 : 0) +
            cogLogs.filter(
              (c) =>
                c.challengeType === 'PALACIO_LOCI' ||
                c.challengeType === 'CORSI_VISUOESPACIAL' ||
                c.challengeType === 'NBACK_ATUALIZACAO' ||
                c.challengeType === 'FLEXIBILIDADE_TRAIL',
            ).length *
              2.5,
        );
      case 'COMUNICACAO_SOCIAL':
        return Math.min(15, practiceCount * 2 + (vault.simulatorStats?.completedRuns ?? 0) * 5);
      case 'LOGICA_NUMERACIA':
        return Math.min(
          15,
          cogLogs.filter(
            (c) =>
              c.challengeType === 'NUMERACIA_FERMI' ||
              c.challengeType === 'LOGICA_MATRIZES' ||
              c.challengeType === 'CALIBRACAO_TETLOCK',
          ).length *
            3 +
            chessPuzzlesCount * 0.8 +
            chessGamesCount * 1.2,
        );
      case 'CIENCIA_PRIMEIROS_PRINCIPIOS':
        return Math.min(15, blueprintsCount * 4 + markCount * 3 + practiceCount * 2);
      case 'ESTRATEGIA_SISTEMAS':
        return Math.min(
          15,
          contractsCount * 3 +
            markCount * 3 +
            reflectionsCount * 2 +
            chessGamesCount * 1.5 +
            chessEndgamesCount * 2 +
            chessRepertoireCount * 1.5 +
            chessBlindfoldWins * 2,
        );
      case 'ANTIVIES_DECISAO':
        return Math.min(
          15,
          decisionsCount * 3 +
            resolvedDecisionsCount * 2.5 +
            cogLogs.filter(
              (c) =>
                c.challengeType === 'DISCERNIMENTO_SABEDORIA' ||
                c.challengeType === 'CALIBRACAO_TETLOCK' ||
                c.challengeType === 'STROOP_INIBICAO',
            ).length * 2.5,
        );
      case 'CORPO_LONGEVIDADE':
        return Math.min(
          15,
          workoutsCount * 2 +
            Object.keys(vault.checkIns).length * 0.8 +
            resonanceCount * 1.2,
        );
    }
  };

  const axes: PillarRadarAxis[] = TEACHING_TRACKS.map((track) => {
    const lessons = TEACHINGS_CATALOG.filter((l) => l.trackId === track.id);
    const totalLessons = Math.max(1, lessons.length);
    let studiedLessons = 0;
    let masteryPoints = 0;
    let fieldMissionsDone = 0;

    for (const l of lessons) {
      const p = progress[l.id];
      if (p) {
        studiedLessons++;
        // Estudar ja concede 0.55 do peso da licao; subir ate masteryLevel 4 completa 1.0
        masteryPoints += 0.55 + (Math.min(4, Math.max(0, p.masteryLevel)) / 4) * 0.45;
      }
      if (missions[l.id]) {
        fieldMissionsDone++;
      }
    }

    const lessonScore65 = (masteryPoints / totalLessons) * 65;
    const missionScore20 = (fieldMissionsDone / totalLessons) * 20;
    const behaviorScore15 = behavioralBonusFor(track.id);

    const raw = lessonScore65 + missionScore20 + behaviorScore15;
    return {
      trackId: track.id,
      shortLabel: track.shortLabel.replace(/^\d+\.\s*/, ''),
      fullTitle: track.title,
      studiedLessons,
      totalLessons,
      fieldMissionsDone,
      score100: Math.round(clamp(raw, 4, 100)),
    };
  });

  const meanScore100 = Math.round(
    axes.reduce((acc, a) => acc + a.score100, 0) / Math.max(1, axes.length),
  );

  const sortedAsc = [...axes].sort((a, b) => a.score100 - b.score100);
  const weakestAxis = sortedAsc[0];
  const strongestAxis = sortedAsc[sortedAsc.length - 1];

  // Indice de Harmonia Polimata: combina a media com o elo mais fraco (evita especialista manco)
  const harmonyIndex100 = Math.round(clamp(meanScore100 * 0.65 + weakestAxis.score100 * 0.35, 0, 100));

  return {
    axes,
    meanScore100,
    harmonyIndex100,
    strongestAxis,
    weakestAxis,
  };
}
