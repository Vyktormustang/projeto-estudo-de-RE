import { createInitialVault } from '../engine/stateEngine';
import { ENGINE_VERSION, VaultState } from '../engine/types';

declare global {
  interface Window {
    ForjaNative?: {
      readVault: () => string | null;
      writeVault: (json: string) => boolean;
      haptic: (kind: string) => void;
      setKeepScreenOn: (enabled: boolean) => void;
      shareText: (title: string, content: string) => void;
      getDeviceInfo: () => string;
    };
  }
}

const LOCAL_STORAGE_KEY = 'forja_apice_vault_v38';

function sanitizeLoadedVault(raw: unknown): VaultState {
  const fallback = createInitialVault();
  if (!raw || typeof raw !== 'object') return fallback;
  const obj = raw as Partial<VaultState>;
  return {
    engineVersion: ENGINE_VERSION,
    profile: obj.profile ?? null,
    currentPhase:
      obj.currentPhase === 1 ||
      obj.currentPhase === 2 ||
      obj.currentPhase === 3 ||
      obj.currentPhase === 4 ||
      obj.currentPhase === 5
        ? obj.currentPhase
        : 1,
    nextQueueSlot:
      obj.nextQueueSlot === 'A' || obj.nextQueueSlot === 'B' || obj.nextQueueSlot === 'C'
        ? obj.nextQueueSlot
        : 'A',
    lastRedZoneBioDayId: obj.lastRedZoneBioDayId ?? null,
    lastViralSymptomBioDayId: obj.lastViralSymptomBioDayId ?? null,
    checkIns: obj.checkIns && typeof obj.checkIns === 'object' ? obj.checkIns : {},
    ledger: obj.ledger && typeof obj.ledger === 'object' ? obj.ledger : {},
    workouts: Array.isArray(obj.workouts) ? obj.workouts : [],
    deliberatePractice: Array.isArray(obj.deliberatePractice) ? obj.deliberatePractice : [],
    cognitiveLogs: Array.isArray(obj.cognitiveLogs) ? obj.cognitiveLogs : [],
    teachingProgress:
      obj.teachingProgress && typeof obj.teachingProgress === 'object'
        ? (obj.teachingProgress as VaultState['teachingProgress'])
        : {},
    completedFieldMissions:
      obj.completedFieldMissions && typeof obj.completedFieldMissions === 'object'
        ? (obj.completedFieldMissions as Record<string, string>)
        : {},
    simulatorStats:
      obj.simulatorStats && typeof obj.simulatorStats === 'object'
        ? obj.simulatorStats
        : fallback.simulatorStats,
    skillBlueprints: Array.isArray(obj.skillBlueprints) ? obj.skillBlueprints : [],
    eveningReflections:
      obj.eveningReflections && typeof obj.eveningReflections === 'object'
        ? (obj.eveningReflections as VaultState['eveningReflections'])
        : {},
    decisionJournal: Array.isArray(obj.decisionJournal) ? obj.decisionJournal : [],
    chessState:
      obj.chessState && typeof obj.chessState === 'object'
        ? {
            playRating:
              typeof obj.chessState.playRating === 'number' ? obj.chessState.playRating : 800,
            puzzleRating:
              typeof obj.chessState.puzzleRating === 'number' ? obj.chessState.puzzleRating : 800,
            puzzleRushBest:
              typeof obj.chessState.puzzleRushBest === 'number'
                ? obj.chessState.puzzleRushBest
                : 0,
            visionBestScore:
              typeof obj.chessState.visionBestScore === 'number'
                ? obj.chessState.visionBestScore
                : 0,
            blindfoldWins:
              typeof obj.chessState.blindfoldWins === 'number'
                ? obj.chessState.blindfoldWins
                : 0,
            gamesPlayed:
              typeof obj.chessState.gamesPlayed === 'number' ? obj.chessState.gamesPlayed : 0,
            wins: typeof obj.chessState.wins === 'number' ? obj.chessState.wins : 0,
            losses: typeof obj.chessState.losses === 'number' ? obj.chessState.losses : 0,
            draws: typeof obj.chessState.draws === 'number' ? obj.chessState.draws : 0,
            solvedPuzzleIds: Array.isArray(obj.chessState.solvedPuzzleIds)
              ? obj.chessState.solvedPuzzleIds
              : [],
            completedAcademyIds: Array.isArray(obj.chessState.completedAcademyIds)
              ? obj.chessState.completedAcademyIds
              : [],
            completedEndgameIds: Array.isArray(obj.chessState.completedEndgameIds)
              ? obj.chessState.completedEndgameIds
              : [],
            completedRepertoireIds: Array.isArray(obj.chessState.completedRepertoireIds)
              ? obj.chessState.completedRepertoireIds
              : [],
            preferredTheme:
              obj.chessState.preferredTheme === 'CHESS_VERDE' ||
              obj.chessState.preferredTheme === 'MADEIRA_CLASSICA' ||
              obj.chessState.preferredTheme === 'OCEANO_GELO' ||
              obj.chessState.preferredTheme === 'OBSIDIANA_FORJA'
                ? obj.chessState.preferredTheme
                : 'CHESS_VERDE',
            soundEnabled:
              typeof obj.chessState.soundEnabled === 'boolean'
                ? obj.chessState.soundEnabled
                : true,
            savedGames: Array.isArray(obj.chessState.savedGames)
              ? obj.chessState.savedGames.slice(0, 20)
              : [],
            playEloCategory:
              typeof obj.chessState.playEloCategory === 'string'
                ? obj.chessState.playEloCategory
                : 'INICIANTE',
            achievements: Array.isArray(obj.chessState.achievements)
              ? obj.chessState.achievements
              : [],
            totalBrilliants:
              typeof obj.chessState.totalBrilliants === 'number'
                ? obj.chessState.totalBrilliants
                : 0,
            totalBlunders:
              typeof obj.chessState.totalBlunders === 'number'
                ? obj.chessState.totalBlunders
                : 0,
            longestWinStreak:
              typeof obj.chessState.longestWinStreak === 'number'
                ? obj.chessState.longestWinStreak
                : 0,
            currentWinStreak:
              typeof obj.chessState.currentWinStreak === 'number'
                ? obj.chessState.currentWinStreak
                : 0,
            openingsPlayed:
              typeof obj.chessState.openingsPlayed === 'object' &&
              obj.chessState.openingsPlayed !== null
                ? obj.chessState.openingsPlayed
                : {},
            dailyPuzzleLastDate:
              typeof obj.chessState.dailyPuzzleLastDate === 'string'
                ? obj.chessState.dailyPuzzleLastDate
                : undefined,
            dailyPuzzleSolved:
              typeof obj.chessState.dailyPuzzleSolved === 'boolean'
                ? obj.chessState.dailyPuzzleSolved
                : false,
            emotionalCheckIns: Array.isArray(obj.chessState.emotionalCheckIns)
              ? obj.chessState.emotionalCheckIns
              : [],
          }
        : undefined,
    contracts: Array.isArray(obj.contracts) ? obj.contracts : [],
    markUpgrades: Array.isArray(obj.markUpgrades) ? obj.markUpgrades : [],
    cookieJar: Array.isArray(obj.cookieJar) ? obj.cookieJar : [],
    mentalSessionsCount:
      typeof obj.mentalSessionsCount === 'number' ? obj.mentalSessionsCount : 0,
    resonanceSessionsCount:
      typeof obj.resonanceSessionsCount === 'number' ? obj.resonanceSessionsCount : 0,
  };
}

export function loadVault(): VaultState {
  try {
    if (typeof window !== 'undefined' && window.ForjaNative?.readVault) {
      const nativeJson = window.ForjaNative.readVault();
      if (nativeJson && nativeJson.trim().length > 2) {
        const parsed = JSON.parse(nativeJson);
        return sanitizeLoadedVault(parsed);
      }
    }
  } catch {
    // Fallback para localStorage
  }

  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      const webJson = window.localStorage.getItem(LOCAL_STORAGE_KEY);
      if (webJson) {
        const parsed = JSON.parse(webJson);
        const clean = sanitizeLoadedVault(parsed);
        if (window.ForjaNative?.writeVault) {
          window.ForjaNative.writeVault(JSON.stringify(clean));
        }
        return clean;
      }
    }
  } catch {
    // Retorna cofre inicial limpo
  }

  return createInitialVault();
}

export function saveVault(vault: VaultState): boolean {
  const stamped: VaultState = {
    ...vault,
    engineVersion: ENGINE_VERSION,
  };
  const serialized = JSON.stringify(stamped);
  let ok = false;

  try {
    if (typeof window !== 'undefined' && window.ForjaNative?.writeVault) {
      ok = Boolean(window.ForjaNative.writeVault(serialized));
    }
  } catch {
    ok = false;
  }

  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(LOCAL_STORAGE_KEY, serialized);
      ok = true;
    }
  } catch {
    // Ignora quota se cofre nativo salvou
  }

  return ok;
}

export function triggerHaptic(kind: 'light' | 'medium' | 'heavy' | 'success' = 'light'): void {
  try {
    if (typeof window !== 'undefined' && window.ForjaNative?.haptic) {
      window.ForjaNative.haptic(kind);
      return;
    }
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      navigator.vibrate(kind === 'success' ? [25, 40, 45] : kind === 'heavy' ? 35 : 15);
    }
  } catch {
    // Ignorado
  }
}

export function setWakeLock(enabled: boolean): void {
  try {
    if (typeof window !== 'undefined' && window.ForjaNative?.setKeepScreenOn) {
      window.ForjaNative.setKeepScreenOn(enabled);
    }
  } catch {
    // Ignorado
  }
}

export function isRunningInsideApk(): boolean {
  return Boolean(typeof window !== 'undefined' && window.ForjaNative);
}

async function computeChecksumHex(payload: string): Promise<string> {
  try {
    if (typeof crypto !== 'undefined' && crypto.subtle) {
      const buf = new TextEncoder().encode(payload);
      const digest = await crypto.subtle.digest('SHA-256', buf);
      return Array.from(new Uint8Array(digest))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');
    }
  } catch {
    // Fallback deterministico offline
  }
  let h = 0x811c9dc5;
  for (let i = 0; i < payload.length; i++) {
    h ^= payload.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return `fnv1a_${(h >>> 0).toString(16).padStart(8, '0')}`;
}

export interface BackupEnvelope {
  app: 'FORJA_SISTEMA_DO_APICE';
  engineVersion: string;
  exportedAtIso: string;
  checksum: string;
  vaultJson: string;
}

export async function exportBackupEnvelope(vault: VaultState): Promise<string> {
  const vaultJson = JSON.stringify(vault);
  const checksum = await computeChecksumHex(vaultJson);
  const envelope: BackupEnvelope = {
    app: 'FORJA_SISTEMA_DO_APICE',
    engineVersion: ENGINE_VERSION,
    exportedAtIso: new Date().toISOString(),
    checksum,
    vaultJson,
  };
  return JSON.stringify(envelope, null, 2);
}

export async function importBackupEnvelope(rawText: string): Promise<{
  ok: boolean;
  vault?: VaultState;
  error?: string;
}> {
  try {
    const parsed = JSON.parse(rawText) as Partial<BackupEnvelope> & Partial<VaultState>;
    if (parsed.app === 'FORJA_SISTEMA_DO_APICE' && typeof parsed.vaultJson === 'string') {
      const expected = await computeChecksumHex(parsed.vaultJson);
      if (parsed.checksum && parsed.checksum !== expected) {
        return {
          ok: false,
          error: 'Integridade violada: o checksum criptográfico SHA-256 do backup não confere.',
        };
      }
      const vault = sanitizeLoadedVault(JSON.parse(parsed.vaultJson));
      return { ok: true, vault };
    }
    if (typeof parsed.engineVersion === 'string') {
      return { ok: true, vault: sanitizeLoadedVault(parsed) };
    }
    return { ok: false, error: 'Formato de arquivo não reconhecido pelo motor FORJA v3.0.' };
  } catch {
    return { ok: false, error: 'JSON inválido ou corrompido.' };
  }
}

export async function shareOrDownloadBackup(vault: VaultState): Promise<void> {
  const content = await exportBackupEnvelope(vault);
  const dateTag = new Date().toISOString().slice(0, 10);
  const filename = `forja_apice_backup_${dateTag}.json`;

  if (typeof window !== 'undefined' && window.ForjaNative?.shareText) {
    window.ForjaNative.shareText(filename, content);
    return;
  }

  const blob = new Blob([content], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
