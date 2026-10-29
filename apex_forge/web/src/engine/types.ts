export const ENGINE_VERSION = '36.0.0';

export type BiologicalSex = 'MASCULINO' | 'FEMININO';
export type TrainingLevel = 'INICIANTE' | 'INTERMEDIARIO' | 'AVANCADO';
export type EquipmentEnv = 'CALISTENIA' | 'CASA' | 'ACADEMIA';
export type EnergyGoal = 'DEFICIT_MODERADO' | 'MANUTENCAO_PERFORMANCE' | 'SUPERAVIT_MAGRO';
export type OccupationalDemand = 'SEDENTARIO_INTELECTUAL' | 'MISTO_EM_PE' | 'BRACAL_PESADO';
export type ClimateProfile = 'AMENO_CLIMATIZADO' | 'CALOR_TROPICAL_UMIDO';
export type ScheduleRegime = 'DIURNO_FIXO' | 'TURNOS_PLANTAO';

export type ExecutiveProfile =
  | 'EQUILIBRADO'
  | 'PERFECCIONISTA_RIGIDO'
  | 'IMPULSIVO_BUSCA_NOVIDADE'
  | 'ANSIOSO_EVITATIVO';

export type CommandVoice =
  | 'ADAPTATIVO'
  | 'CRISTO_BIBLIA'
  | 'GOGGINS_MUSASHI'
  | 'SENKU_FEYNMAN'
  | 'STARK_MAQUIAVEL';

export type JointRegion =
  | 'OMBRO'
  | 'COTOVELO_PUNHO'
  | 'LOMBAR'
  | 'QUADRIL'
  | 'JOELHO'
  | 'TORNOZELO_AQUILES';

export type PainKind = 'NENHUMA' | 'DOMS_MUSCULAR' | 'ARTICULAR_TENDINEA_AGUDA';

export type DayLedgerStatus = 'LOGGED_ACTIVE' | 'REST_CONFIRMED' | 'MISSING_LOG';

export type EvolutionPhase = 1 | 2 | 3 | 4 | 5;

export interface PharmacologicalFlags {
  betaBlocker: boolean;       // Bloqueia zonas por FC -> Talk Test + RPE
  glp1Agonist: boolean;       // Prioridade anticatabolica + piso proteico
  adhdStimulant: boolean;     // Desconta ruido de VFC + alerta termico
  statin: boolean;            // Alerta mialgia vs DOMS
  fluoroquinolone: boolean;   // Veto estrito de impacto / sobrecarga tendinea
}

export interface ClinicalSafetyFlags {
  parqWarning: boolean;              // Cardiopatia/dor toracica/sincope sem alta -> modo clinico protegido
  bodyNeutralMode: boolean;          // Oculta peso/calorias (protecao contra transtornos alimentares)
  interoceptiveSensitive: boolean;   // Usa ancoragem externa de olhos abertos (previne ansiedade em meditacao)
}

export interface UserProfile {
  codename: string;
  age: number;
  sex: BiologicalSex;
  weightKg: number;
  heightCm: number;
  level: TrainingLevel;
  equipment: EquipmentEnv;
  energyGoal: EnergyGoal;
  occupationalDemand: OccupationalDemand;
  climate: ClimateProfile;
  scheduleRegime: ScheduleRegime;
  executiveProfile: ExecutiveProfile;
  commandVoice: CommandVoice;
  weekdayFreeMinutes: number;
  weekendFreeMinutes: number;
  targetSleepHours: number;
  usualWakeTime: string;
  usualBedTime: string;
  primaryGoalDomain: string;
  mainSaboteur: string;
  pharma: PharmacologicalFlags;
  clinical: ClinicalSafetyFlags;
  createdAtIso: string;
}

export interface DailyCheckIn {
  bioDayId: string;
  timestampMs: number;
  sleepHours: number;
  sleepQuality: number;
  energyLevel: number;
  mentalCalm: number;
  muscularRecovery: number;
  painKind: PainKind;
  painJoints: JointRegion[];
  viralOrFeverSymptoms: boolean;
  externalLifeStressEvent: boolean;
  availableMinutesToday?: number;
  restingHrvRmssd?: number;
}

export type MovementPattern =
  | 'PUSH_H'
  | 'PUSH_V'
  | 'PULL_H'
  | 'PULL_V'
  | 'KNEE_DOM'
  | 'HIP_DOM'
  | 'CORE_STAB'
  | 'MOBILITY_DECOMPRESS'
  | 'CARDIO_Z2'
  | 'CARDIO_VO2';

export type AnimationArchetype =
  | 'PUSH_UP'
  | 'BENCH_PRESS'
  | 'OVERHEAD_PRESS'
  | 'ROW_HORIZONTAL'
  | 'VERTICAL_PULL'
  | 'SQUAT'
  | 'SPLIT_SQUAT'
  | 'HIP_HINGE'
  | 'GLUTE_BRIDGE'
  | 'DEADBUG_CORE'
  | 'SIDE_PLANK'
  | 'MOBILITY_WALL'
  | 'CARDIO_STRIDE';

export interface ExerciseVariant {
  id: string;
  name: string;
  pattern: MovementPattern;
  animationArchetype: AnimationArchetype;
  environments: EquipmentEnv[];
  difficultyTier: 1 | 2 | 3 | 4 | 5;
  stressedJoints: JointRegion[];
  highTendonImpact: boolean;
  axialSpinalLoad: boolean;
  isCardio: boolean;
  defaultSets: number;
  repRange: [number, number];
  tempoCue: string;
  biomechanicalCue: string;
  externalFocusCue: string;          // Gabriele Wulf (2021): instrucao simples de foco no efeito externo
  musclesWorked: string[];           // Grupos musculares em portugues claro
  stepByStep: [string, string, string]; // 3 passos curtos para leigos
  commonMistakes: [string, string];  // 2 erros classicos a evitar
  zeroSkillRegression?: string;      // Degrau Zero: como comecar se nao aguenta 1 repeticao padrao
  masteryProgression?: string;       // Degrau Mestre: progressao avancada de dominio
  painSafeFallbackId?: string;
}

export interface PrescribedExercise {
  exerciseId: string;
  name: string;
  pattern: MovementPattern;
  sets: number;
  targetReps: string;
  targetRir: string;
  tempoCue: string;
  progressionAxisNote: string;
  suggestedLoadKg?: number;
  substitutedReason?: string;
}

export type ReadinessZone = 'VERDE' | 'AMARELO' | 'VERMELHO';

export interface ReadinessComputation {
  engineVersion: string;
  bioDayId: string;
  score: number;
  zone: ReadinessZone;
  volumeMultiplier: number;
  intensityRirFloor: number;
  allowHighIntensityVo2: boolean;
  allowPlyoAndHeavyEccentric: boolean;
  useTalkTestInsteadOfHr: boolean;
  maskedFatigueDetected: boolean;
  boilingFrogSlopePenalty: number;
  recoveryResidual: number;
  acuteEwma: number;
  uncoupledChronicEwma: number;
  regularizedMonotony: number;
  connectiveTissueCapPct: number;
  proteinTargetGrams: [number, number];
  waterTargetLiters: number;
  electrolyteAlert: boolean;
  caffeineCutoffTime: string;
  glassBoxReasons: string[];
  activeVetoes: string[];
}

export interface PantheonBriefing {
  mentorId:
    | 'JESUS_CRISTO'
    | 'SALOMAO_BIBLIA'
    | 'GOGGINS'
    | 'SENKU'
    | 'STARK'
    | 'DOCTOR_WHO'
    | 'TESLA'
    | 'MAQUIAVEL'
    | 'MARCO_AURELIO'
    | 'MUSASHI'
    | 'FEYNMAN'
    | 'DA_VINCI';
  mentorName: string;
  archetypeTitle: string;
  tacticalDirective: string;
  neuroMechanismNote: string;
  amccChallenge: {
    id: string;
    title: string;
    durationMin: number;
    description: string;
  };
  variableRewardUnlocked?: {
    title: string;
    scientificInsight: string;
  };
}

export interface PrescribedDayPlan {
  bioDayId: string;
  queueSlot: 'A' | 'B' | 'C' | 'RECUPERACAO_ATIVA';
  sessionTitle: string;
  estimatedMinutes: number;
  minimumFloor5Min: {
    title: string;
    steps: string[];
  };
  doctorWho15MinPivot: {
    title: string;
    exercises: PrescribedExercise[];
  };
  exercises: PrescribedExercise[];
  mentalProtocol: {
    id: string;
    title: string;
    durationMin: number;
    mode:
      | 'RESPIRACAO_01HZ'
      | 'SUSPIRO_FISIOLOGICO'
      | 'EXTEROCEPTIVO_OLHOS_ABERTOS'
      | 'CAMARA_TESLA'
      | 'DESFUSAO_ACT';
    instructions: string[];
  };
  readiness: ReadinessComputation;
  pantheon: PantheonBriefing;
}

export interface LoggedSet {
  exerciseId: string;
  loadKg: number;
  reps: number;
  rir: number;
}

export interface WorkoutSessionLog {
  id: string;
  bioDayId: string;
  timestampMs: number;
  queueSlot: 'A' | 'B' | 'C' | 'RECUPERACAO_ATIVA' | 'PISO_MINIMO_5M' | 'PIVOT_15M';
  durationMinutes: number;
  sessionRpe: number;
  internalLoadAu: number;
  sets: LoggedSet[];
  completedAmccChallenge: boolean;
  engineVersion: string;
}

export interface DayLedgerEntry {
  bioDayId: string;
  status: DayLedgerStatus;
  internalLoadAu: number;
  usedMinimumFloor: boolean;
}

export interface DeliberatePracticeLog {
  id: string;
  bioDayId: string;
  timestampMs: number;
  subSkill: string;
  objectiveOracleCriteria: string;
  durationMinutes: number;
  attemptsCount: number;
  errorsCount: number;
  feynmanPass: boolean;
  keyCorrectionNote: string;
  nextReviewBioDayId: string;
}

export type CognitiveChallengeType =
  | 'STROOP_INIBICAO'
  | 'LOGICA_MATRIZES'
  | 'CORSI_VISUOESPACIAL'
  | 'PALACIO_LOCI'
  | 'NUMERACIA_FERMI'
  | 'DISCERNIMENTO_SABEDORIA'
  | 'CALIBRACAO_TETLOCK'
  | 'NBACK_ATUALIZACAO'
  | 'FLEXIBILIDADE_TRAIL'
  | 'FLANKER_ATENCAO'
  | 'GO_NOGO_INIBICAO'
  | 'DUAL_N_BACK'
  | 'ATTENTION_CONTROL'
  | 'REACTION_TIME'
  | 'WORKING_MEMORY_SPAN';

export interface CognitiveChallengeLog {
  id: string;
  bioDayId: string;
  timestampMs: number;
  challengeType: CognitiveChallengeType;
  score: number;              // 0 .. 1000 padronizado
  accuracyPct: number;        // 0 .. 100
  avgReactionMs?: number;     // Tempo medio de resposta em ms
  maxSpanOrStreak?: number;   // Span atingido (Corsi / Loci) ou sequencia logica
  difficultyTier: 1 | 2 | 3;
}

export interface IfThenContract {
  id: string;
  triggerSituation: string;
  shieldedAction: string;
  machiavelliPreCommitment: string;
  timesTriggered: number;
  active: boolean;
}

export interface MarkUpgradeEntry {
  id: string;
  bioDayId: string;
  versionLabel: string;
  failureWhatHappened: string;
  rootCause: string;
  systemPatchInstalled: string;
}

export interface CookieJarVictory {
  id: string;
  bioDayId: string;
  title: string;
  hardContext: string;
  autoGenerated: boolean;
}

export type TeachingTrackId =
  | 'CRISTO_EVANGELHOS'
  | 'SABEDORIA_BIBLICA'
  | 'GARRA_AUTODOMINIO'
  | 'APRENDIZAGEM_MEMORIA'
  | 'COMUNICACAO_SOCIAL'
  | 'LOGICA_NUMERACIA'
  | 'CIENCIA_PRIMEIROS_PRINCIPIOS'
  | 'ESTRATEGIA_SISTEMAS'
  | 'ANTIVIES_DECISAO'
  | 'CORPO_LONGEVIDADE';

export type MasteryTier = 1 | 2 | 3 | 4;

export interface TeachingLesson {
  id: string;
  trackId: TeachingTrackId;
  trackTitle: string;
  masteryTier?: MasteryTier;      // 1=Marco Zero, 2=Artifice, 3=Estrategista, 4=Polimata
  title: string;
  subtitle: string;
  mentorName: string;
  scientificSource: string;
  readTimeSec: number;
  recommendedZone?: ReadinessZone | 'QUALQUER';
  coreEssence: string;            // Explicacao direta e cristalina para qualquer pessoa
  whyItWorksMechanism: string;    // Elaborative Interrogation: por que funciona no cerebro/corpo
  zeroStepExample?: string;       // Worked Example (Sweller): exemplo concreto de Degrau Zero
  practicalActionToday: string;   // Acao concreta imediata de 1 minuto
  fieldMission?: string;          // Missao verificavel de transferencia para a vida real
  dilemmaPrompt: string;          // Cenario pratico da vida real (Debiasing / Active Recall)
  dilemmaOptions: [string, string, string, string];
  correctOptionIndex: 0 | 1 | 2 | 3;
  feedbackCorrect: string;
  feedbackTrap: string;
}

export interface SimulatorStats {
  bestScore: number;
  completedRuns: number;
  lastRankTitle: string;
  lastCompletedBioDayId: string;
}

export interface SkillBlueprintStep {
  id: string;
  tier: 1 | 2 | 3 | 4;
  stageLabel: string;
  actionDescription: string;
  completed: boolean;
}

export interface SkillBlueprint {
  id: string;
  skillName: string;
  categoryLabel: string;
  oracle30DayProof: string;       // Lucas 14:28 + Ericsson: prova objetiva verificavel em 30d
  zeroStep2Min: string;           // Sweller + vmPFC: piso de 2 min para dias caoticos
  analogicalBridge: string;       // Gentner (2003): ponte com algo que ja domina
  preMortemSaboteur: string;      // Klein + Pv 22:3: obstaculo nº 1 previsto + escudo
  steps: [SkillBlueprintStep, SkillBlueprintStep, SkillBlueprintStep, SkillBlueprintStep];
  feynmanAuditsCount: number;
  bestFeynmanClarityScore: number;
  createdBioDayId: string;
}

export interface TeachingProgressEntry {
  lessonId: string;
  masteryLevel: 0 | 1 | 2 | 3 | 4; // 0=em revisao, 1=1d, 2=3d, 3=7d, 4=Dominado (21d+)
  timesCompleted: number;
  lastStudiedBioDayId: string;
  nextReviewBioDayId: string;
  lastCorrect: boolean;
}

export interface EveningReflectionEntry {
  bioDayId: string;
  timestampMs: number;
  gratitudeNote: string;          // 1 Ts 5:18 + Emmons & McCullough (2003)
  lessonLearnedToday: string;     // Di Stefano et al. (HBS, +22.8%) + Sl 139:23
  tomorrowTopPriority: string;    // Scullin et al. (JEP:G 2018, d=0.63 — descarregamento pre-sono)
  releasedResentment: boolean;    // Efesios 4:26 ("Nao se ponha o sol sobre a vossa ira")
}

export interface RealDecisionRecord {
  id: string;
  bioDayId: string;
  timestampMs: number;
  decisionTitle: string;
  towerCostEstimate: string;      // Lucas 14:28 — custo real em tempo/dinheiro/energia
  solomonThirdPerson: string;     // Grossmann & Kross (2014) — conselho a um grande amigo
  preMortemGuardrail: string;     // Klein (2007) — causa de falha prevista + trava instalada
  preservesCharacter: boolean;    // Mateus 16:26 & Pv 11:1
  zeroRuinRisk: boolean;          // Kelly (1956) & Peters (2019)
  futureSelf101010: boolean;      // Hershfield (2011) — honra o Eu de 10 meses / 10 anos
  confidencePct: 55 | 70 | 85;    // Fischhoff (1975) — congelamento ex-ante anti-retrospectiva
  maturityScore100: number;
  verdict: 'AVANCAR_COM_TRAVAS' | 'REFORCAR_ANTES_DE_AGIR' | 'VETO_PRUDENCIAL';
  resolvedOutcome?: 'SUCESSO' | 'FALHA'; // Fechamento pos-desfecho (Tetlock 2015; Di Stefano 2014)
  outcomeLessonLearned?: string;
  resolvedBioDayId?: string;
  brierScore?: number;            // (p - o)^2 em [0..1], menor = mais calibrado
}

export type ChessBoardThemeId = 'CHESS_VERDE' | 'MADEIRA_CLASSICA' | 'OCEANO_GELO' | 'OBSIDIANA_FORJA';

export interface ChessSavedGame {
  id: string;
  bioDayId: string;
  timestampMs: number;
  opponentName: string;
  opponentElo: number;
  userColor: 'w' | 'b';
  result: 'VITORIA' | 'DERROTA' | 'EMPATE';
  terminationReason: string;
  timeControlLabel: string;
  openingEco: string;
  openingName: string;
  movesCount: number;
  pgn: string;
  userAccuracyPct?: number;
  brilliantCount?: number;
  blunderCount?: number;
  rated: boolean;
  ratingDelta: number;
}

export interface ChessVaultData {
  playRating: number;
  playEloCategory: 'INICIANTE' | 'CLUBE' | 'INTERMEDIARIO' | 'AVANCADO' | 'ESPECIALISTA' | 'MESTRE' | 'GRAO_MESTRE';
  puzzleRating: number;
  puzzleRushBest: number;
  visionBestScore?: number;
  blindfoldWins?: number;
  gamesPlayed: number;
  wins: number;
  losses: number;
  draws: number;
  solvedPuzzleIds: string[];
  completedAcademyIds?: string[];
  completedEndgameIds?: string[];
  completedRepertoireIds?: string[];
  preferredTheme: ChessBoardThemeId;
  soundEnabled: boolean;
  savedGames: ChessSavedGame[];
  achievements: string[];
  totalBrilliants: number;
  totalBlunders: number;
  longestWinStreak: number;
  currentWinStreak: number;
  openingsPlayed: Record<string, { played: number; wins: number; draws: number; losses: number }>;
  dailyPuzzleLastDate?: string;
  dailyPuzzleSolved?: boolean;
  emotionalCheckIns: Array<{
    bioDayId: string;
    timestampMs: number;
    before: 'FOCADO' | 'ANSIOSO' | 'CANSADO' | 'CONFIANTE' | 'IRRITADO' | 'CALMO';
    after?: 'FOCADO' | 'ANSIOSO' | 'CANSADO' | 'CONFIANTE' | 'IRRITADO' | 'CALMO';
    result?: 'VITORIA' | 'DERROTA' | 'EMPATE';
  }>;
}

export interface VaultState {
  engineVersion: string;
  profile: UserProfile | null;
  currentPhase: EvolutionPhase;
  nextQueueSlot: 'A' | 'B' | 'C';
  lastRedZoneBioDayId: string | null;
  lastViralSymptomBioDayId: string | null;
  checkIns: Record<string, DailyCheckIn>;
  ledger: Record<string, DayLedgerEntry>;
  workouts: WorkoutSessionLog[];
  deliberatePractice: DeliberatePracticeLog[];
  cognitiveLogs?: CognitiveChallengeLog[];
  teachingProgress?: Record<string, TeachingProgressEntry>;
  completedFieldMissions?: Record<string, string>;
  simulatorStats?: SimulatorStats;
  skillBlueprints?: SkillBlueprint[];
  eveningReflections?: Record<string, EveningReflectionEntry>;
  decisionJournal?: RealDecisionRecord[];
  chessState?: ChessVaultData;
  contracts: IfThenContract[];
  markUpgrades: MarkUpgradeEntry[];
  cookieJar: CookieJarVictory[];
  mentalSessionsCount?: number;
  resonanceSessionsCount?: number;
}
