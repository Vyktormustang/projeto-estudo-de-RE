import { createBlueprintFromTemplate } from './skillForgeEngine';
import { addDaysToBioDay, advanceQueueSlot, computeBioDayId, createInitialVault } from './stateEngine';
import { ENGINE_VERSION, UserProfile, VaultState } from './types';

export function buildDemoVault(): VaultState {
  const vault = createInitialVault();
  const todayBio = computeBioDayId(new Date(), null);
  const startBio = addDaysToBioDay(todayBio, -18);

  const profile: UserProfile = {
    codename: 'Operador V-01',
    age: 29,
    sex: 'MASCULINO',
    weightKg: 81,
    heightCm: 178,
    level: 'INTERMEDIARIO',
    equipment: 'CASA',
    energyGoal: 'MANUTENCAO_PERFORMANCE',
    occupationalDemand: 'SEDENTARIO_INTELECTUAL',
    climate: 'CALOR_TROPICAL_UMIDO',
    scheduleRegime: 'DIURNO_FIXO',
    executiveProfile: 'IMPULSIVO_BUSCA_NOVIDADE',
    commandVoice: 'ADAPTATIVO',
    weekdayFreeMinutes: 45,
    weekendFreeMinutes: 65,
    targetSleepHours: 7.5,
    usualWakeTime: '06:30',
    usualBedTime: '22:45',
    primaryGoalDomain: 'Engenharia Reversa, Arquitetura Android & Foco Profundo',
    mainSaboteur: 'Hiperfoco noturno atravessando o horário de sono',
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
    createdAtIso: `${startBio}T08:00:00.000Z`,
  };

  vault.profile = profile;
  vault.currentPhase = 2;
  vault.mentalSessionsCount = 9;

  let slot: 'A' | 'B' | 'C' = 'A';
  for (let i = 0; i < 18; i++) {
    const day = addDaysToBioDay(startBio, i);
    const wave = Math.sin(i * 0.65);
    const sleepH = Number((7.3 + wave * 0.55).toFixed(1));
    const q = Math.min(7, Math.max(4, Math.round(5.6 + wave)));

    vault.checkIns[day] = {
      bioDayId: day,
      timestampMs: Date.now() - (18 - i) * 86400000,
      sleepHours: sleepH,
      sleepQuality: q,
      energyLevel: q,
      mentalCalm: Math.min(7, Math.max(4, q - (i % 5 === 0 ? 1 : 0))),
      muscularRecovery: q,
      painKind: i % 4 === 2 ? 'DOMS_MUSCULAR' : 'NENHUMA',
      painJoints: [],
      viralOrFeverSymptoms: false,
      externalLifeStressEvent: i === 9,
    };

    if (i % 3 !== 2) {
      const isPivot = i === 9;
      const dur = isPivot ? 15 : 42;
      const rpe = isPivot ? 5 : 7;
      const au = dur * rpe;
      vault.ledger[day] = {
        bioDayId: day,
        status: 'LOGGED_ACTIVE',
        internalLoadAu: au,
        usedMinimumFloor: isPivot,
      };
      vault.workouts.push({
        id: `demo_w_${i}`,
        bioDayId: day,
        timestampMs: Date.now() - (18 - i) * 86400000 + 3600000,
        queueSlot: isPivot ? 'PIVOT_15M' : slot,
        durationMinutes: dur,
        sessionRpe: rpe,
        internalLoadAu: au,
        sets: [
          { exerciseId: 'push_db_floor_or_bench', loadKg: 24, reps: 10 + Math.floor(i / 6), rir: 2 },
          { exerciseId: 'pull_one_arm_db_row', loadKg: 26, reps: 11, rir: 2 },
        ],
        completedAmccChallenge: i % 2 === 0,
        engineVersion: ENGINE_VERSION,
      });
      if (!isPivot) slot = advanceQueueSlot(slot);
    } else {
      vault.ledger[day] = {
        bioDayId: day,
        status: 'REST_CONFIRMED',
        internalLoadAu: 0,
        usedMinimumFloor: false,
      };
    }
  }

  // Insere check-in de hoje pronto para inspecao imediata
  vault.checkIns[todayBio] = {
    bioDayId: todayBio,
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
  };

  vault.nextQueueSlot = slot;

  vault.deliberatePractice = [
    {
      id: 'dp_demo_1',
      bioDayId: addDaysToBioDay(todayBio, -5),
      timestampMs: Date.now() - 5 * 86400000,
      subSkill: 'Injeção Smali & Preservação de Registradores DEX',
      objectiveOracleCriteria: 'Zero VerifyError no ART Android 14 + MD5 validado',
      durationMinutes: 45,
      attemptsCount: 4,
      errorsCount: 1,
      feynmanPass: true,
      keyCorrectionNote:
        'Isolar registradores locais acima de v4 evita colisão com argumentos p0..p2 em métodos não-estáticos.',
      nextReviewBioDayId: addDaysToBioDay(todayBio, 2),
    },
    {
      id: 'dp_demo_2',
      bioDayId: addDaysToBioDay(todayBio, -2),
      timestampMs: Date.now() - 2 * 86400000,
      subSkill: 'Modelagem Bayesiana Ortogonal sem Dupla Contagem',
      objectiveOracleCriteria: '10.000 iterações de fuzzing sem NaN nem violação clínica',
      durationMinutes: 50,
      attemptsCount: 3,
      errorsCount: 0,
      feynmanPass: true,
      keyCorrectionNote:
        'Extrair o resíduo ortogonal de recuperação em relação à EWMA aguda impede punir fadiga esperada duas vezes.',
      nextReviewBioDayId: addDaysToBioDay(todayBio, 5),
    },
  ];

  vault.cognitiveLogs = [
    {
      id: 'cog_demo_1',
      bioDayId: addDaysToBioDay(todayBio, -4),
      timestampMs: Date.now() - 4 * 86400000,
      challengeType: 'LOGICA_MATRIZES',
      score: 840,
      accuracyPct: 88,
      avgReactionMs: 6400,
      difficultyTier: 2,
    },
    {
      id: 'cog_demo_2',
      bioDayId: addDaysToBioDay(todayBio, -1),
      timestampMs: Date.now() - 86400000,
      challengeType: 'CORSI_VISUOESPACIAL',
      score: 870,
      accuracyPct: 86,
      maxSpanOrStreak: 6,
      difficultyTier: 2,
    },
  ];

  vault.teachingProgress = {
    cristo_01_casa_na_rocha: {
      lessonId: 'cristo_01_casa_na_rocha',
      masteryLevel: 4,
      timesCompleted: 4,
      lastStudiedBioDayId: addDaysToBioDay(todayBio, -1),
      nextReviewBioDayId: addDaysToBioDay(todayBio, 20),
      lastCorrect: true,
    },
    biblia_01_proverbios_dominio_proprio: {
      lessonId: 'biblia_01_proverbios_dominio_proprio',
      masteryLevel: 3,
      timesCompleted: 3,
      lastStudiedBioDayId: addDaysToBioDay(todayBio, -3),
      nextReviewBioDayId: addDaysToBioDay(todayBio, 4),
      lastCorrect: true,
    },
    garra_01_regra40_governador: {
      lessonId: 'garra_01_regra40_governador',
      masteryLevel: 2,
      timesCompleted: 2,
      lastStudiedBioDayId: addDaysToBioDay(todayBio, -4),
      nextReviewBioDayId: addDaysToBioDay(todayBio, -1), // Pronta para revisao espacada hoje!
      lastCorrect: true,
    },
    ciencia_01_primeiros_principios: {
      lessonId: 'ciencia_01_primeiros_principios',
      masteryLevel: 3,
      timesCompleted: 3,
      lastStudiedBioDayId: addDaysToBioDay(todayBio, -2),
      nextReviewBioDayId: addDaysToBioDay(todayBio, 5),
      lastCorrect: true,
    },
    estrategia_01_maquiavel_diques: {
      lessonId: 'estrategia_01_maquiavel_diques',
      masteryLevel: 4,
      timesCompleted: 4,
      lastStudiedBioDayId: addDaysToBioDay(todayBio, -1),
      nextReviewBioDayId: addDaysToBioDay(todayBio, 20),
      lastCorrect: true,
    },
  };

  vault.contracts = [
    {
      id: 'ift_1',
      triggerSituation: 'SE der 22h00 e eu ainda estiver diante da tela compilando código',
      shieldedAction: 'ENTÃO fecho o terminal em 90s e inicio 5 min de respiração 0.1 Hz.',
      machiavelliPreCommitment: 'Carregador do celular fica fora do quarto desde as 20h.',
      timesTriggered: 6,
      active: true,
    },
    {
      id: 'ift_2',
      triggerSituation: 'SE o dia atrasar e sobrarem menos de 15 minutos livres',
      shieldedAction: 'ENTÃO aciono o Piso Inegociável de 5 minutos (vmPFC) em vez de fazer zero.',
      machiavelliPreCommitment: 'Par de halteres ou espaço livre já preparado ao lado da porta.',
      timesTriggered: 3,
      active: true,
    },
  ];

  vault.markUpgrades = [
    {
      id: 'mk_1',
      bioDayId: addDaysToBioDay(todayBio, -6),
      versionLabel: 'Mark 1.2',
      failureWhatHappened: 'Dormi apenas 5h30 porque tomei café às 16h30.',
      rootCause: 'Meia-vida da cafeína bloqueou receptores de adenosina até 01h da manhã.',
      systemPatchInstalled: 'Alarme fixo de corte absoluto de cafeína 10h antes de deitar (12h45).',
    },
  ];

  vault.cookieJar = [
    {
      id: 'cj_1',
      bioDayId: addDaysToBioDay(todayBio, -9),
      title: 'Pivô Doctor Who de 15m Sustentado sob Caos',
      hardContext:
        'Mesmo com imprevisto severo no trabalho, executei 15 min cirúrgicos e mantive o elo neural intacto.',
      autoGenerated: true,
    },
    {
      id: 'cj_2',
      bioDayId: addDaysToBioDay(todayBio, -3),
      title: 'Desafio aMCC Concluído Sem Hesitação',
      hardContext:
        'Mantive 3 segundos exatos de descida controlada na última série sem negociar com a queimação.',
      autoGenerated: true,
    },
  ];

  vault.skillBlueprints = [
    {
      ...createBlueprintFromTemplate('tpl_programacao_logica', startBio),
      feynmanAuditsCount: 2,
      bestFeynmanClarityScore: 93,
    },
  ];
  vault.skillBlueprints[0].steps[0].completed = true;
  vault.skillBlueprints[0].steps[1].completed = true;

  const yestBio = addDaysToBioDay(todayBio, -1);
  vault.decisionJournal = [
    {
      id: 'dec_demo_0',
      bioDayId: addDaysToBioDay(todayBio, -8),
      timestampMs: Date.now() - 8 * 86_400_000,
      decisionTitle: 'Trocar uso de celular na cama por leitura física + horário fixo 22h30',
      towerCostEstimate: 'Zero custo financeiro; deixar carregador na sala todas as noites',
      solomonThirdPerson:
        'Diria ao meu melhor amigo que 45 min a mais de sono profundo multiplicam o foco inteiro.',
      preMortemGuardrail:
        'Esquecer despertador; trava: despertador simples dedicado fora do celular.',
      preservesCharacter: true,
      zeroRuinRisk: true,
      futureSelf101010: true,
      confidencePct: 85,
      maturityScore100: 98,
      verdict: 'AVANCAR_COM_TRAVAS',
      resolvedOutcome: 'SUCESSO',
      outcomeLessonLearned: 'Sono estabilizou em 3 noites e energia matinal subiu de 4 para 6.',
      resolvedBioDayId: yestBio,
      brierScore: 0.0225,
    },
    {
      id: 'dec_demo_1',
      bioDayId: yestBio,
      timestampMs: Date.now() - 86_400_000,
      decisionTitle: 'Assumir certificação técnica exigente mantendo reserva financeira intacta',
      towerCostEstimate: '7h/semana de estudo focado por 16 semanas + taxa paga à vista sem dívida',
      solomonThirdPerson:
        'Eu diria ao meu melhor amigo para reservar o bloco das 06h30 antes de abrir mensagens.',
      preMortemGuardrail:
        'Falharia por exaustão noturna; trava: estudar sempre pela manhã com celular em outro cômodo.',
      preservesCharacter: true,
      zeroRuinRisk: true,
      futureSelf101010: true,
      confidencePct: 70,
      maturityScore100: 100,
      verdict: 'AVANCAR_COM_TRAVAS',
    },
  ];
  vault.eveningReflections = {
    [yestBio]: {
      bioDayId: yestBio,
      timestampMs: Date.now() - 36000000,
      gratitudeNote: 'Saúde intacta e foco ininterrupto na sessão matinal.',
      lessonLearnedToday: 'Cortar notificações antes das 10h dobrou a velocidade de resolução.',
      tomorrowTopPriority: 'Concluir 45 min de prática deliberada + Treino no Sinal Verde.',
      releasedResentment: true,
    },
  };
  vault.chessState = {
    playRating: 1320,
    puzzleRating: 1460,
    puzzleRushBest: 14,
    visionBestScore: 22,
    completedAcademyIds: [
      'acad_chess_01_abertura_ouro',
      'acad_chess_02_metodo_cct',
    ],
    completedEndgameIds: [
      'end_01_escada_duas_torres',
      'end_04_oposicao_direta_peao',
    ],
    gamesPlayed: 9,
    wins: 6,
    losses: 2,
    draws: 1,
    solvedPuzzleIds: [
      'puz_01_corredor_basico',
      'puz_02_beijo_da_dama',
      'puz_03_mate_arabe',
      'puz_04_garfo_real_cavalo',
      'puz_13_mate_opera_morphy',
    ],
    preferredTheme: 'CHESS_VERDE',
    soundEnabled: true,
    savedGames: [
      {
        id: 'chess_demo_1',
        bioDayId: yestBio,
        timestampMs: Date.now() - 48_000_000,
        opponentName: 'David Goggins',
        opponentElo: 1150,
        userColor: 'w',
        result: 'VITORIA',
        terminationReason: 'Xeque-mate',
        timeControlLabel: 'Rápido 10 | 0',
        openingEco: 'C50',
        openingName: 'Abertura Italiana',
        movesCount: 17,
        pgn: '1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7 8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7 14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8#',
        userAccuracyPct: 96.4,
        brilliantCount: 1,
        blunderCount: 0,
        rated: true,
        ratingDelta: 14,
      },
    ],
    playEloCategory: 'INTERMEDIARIO',
    achievements: ['ach_first_win', 'ach_club_player'],
    totalBrilliants: 3,
    totalBlunders: 1,
    longestWinStreak: 3,
    currentWinStreak: 1,
    openingsPlayed: {
      C50: { played: 3, wins: 2, draws: 0, losses: 1 },
    },
    dailyPuzzleLastDate: undefined,
    dailyPuzzleSolved: false,
    emotionalCheckIns: [],
  };

  return vault;
}

/**
 * Constroi um Cofre calibrado exatamente para a Persona Zero:
 * Um jovem de 18 anos com ZERO habilidades fisicas, tecnicas, sociais ou financeiras,
 * iniciando no Grau I (Marco Zero) da Base Absoluta com Calistenia peso do corpo.
 */
export function buildZeroSkillYouthVault(): VaultState {
  const vault = createInitialVault();
  const todayBio = computeBioDayId(new Date(), null);

  const profile: UserProfile = {
    codename: 'Aprendiz Marco Zero',
    age: 18,
    sex: 'MASCULINO',
    weightKg: 68,
    heightCm: 173,
    level: 'INICIANTE',
    equipment: 'CALISTENIA',
    energyGoal: 'SUPERAVIT_MAGRO',
    occupationalDemand: 'SEDENTARIO_INTELECTUAL',
    climate: 'CALOR_TROPICAL_UMIDO',
    scheduleRegime: 'DIURNO_FIXO',
    executiveProfile: 'ANSIOSO_EVITATIVO',
    commandVoice: 'ADAPTATIVO',
    weekdayFreeMinutes: 30,
    weekendFreeMinutes: 45,
    targetSleepHours: 8,
    usualWakeTime: '06:30',
    usualBedTime: '22:30',
    primaryGoalDomain: 'Construir a Base Absoluta do Zero em Todas as Áreas',
    mainSaboteur: 'Fuga para vídeos curtos por insegurança de não saber por onde começar',
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
    createdAtIso: `${todayBio}T07:00:00.000Z`,
  };

  vault.profile = profile;
  vault.currentPhase = 1;
  vault.checkIns[todayBio] = {
    bioDayId: todayBio,
    timestampMs: Date.now(),
    sleepHours: 7.5,
    sleepQuality: 5,
    energyLevel: 5,
    mentalCalm: 4,
    muscularRecovery: 6,
    painKind: 'NENHUMA',
    painJoints: [],
    viralOrFeverSymptoms: false,
    externalLifeStressEvent: false,
  };

  vault.contracts = [
    {
      id: 'ift_zero_1',
      triggerSituation:
        'SE eu travar diante de algo que não sei fazer e sentir vontade de fugir para o celular',
      shieldedAction:
        'ENTÃO corto a culpa e executo apenas o Degrau Zero de 2 minutos (1 exemplo resolvido ou 1 série inclinada).',
      machiavelliPreCommitment: 'Celular fica em outro cômodo durante meus blocos de 15–25 min.',
      timesTriggered: 0,
      active: true,
    },
    {
      id: 'ift_zero_2',
      triggerSituation: 'SE o dia sair do controle e eu achar que "já perdi o dia"',
      shieldedAction:
        'ENTÃO cumpro o Piso Mínimo de 5 minutos + 1 Lição de 60s da Base Absoluta antes de dormir.',
      machiavelliPreCommitment: 'Meta mínima inegociável para nunca zerar dois dias seguidos.',
      timesTriggered: 0,
      active: true,
    },
  ];

  vault.cookieJar = [
    {
      id: 'cj_zero_start',
      bioDayId: todayBio,
      title: 'Saída da Inércia — Dia 1 no Marco Zero',
      hardContext:
        'Assumi responsabilidade radical pela minha evolução partindo do zero absoluto, sem vergonha de usar o Degrau Zero.',
      autoGenerated: true,
    },
  ];

  vault.skillBlueprints = [createBlueprintFromTemplate('tpl_matematica_exatas', todayBio)];
  const yestZero = addDaysToBioDay(todayBio, -1);
  vault.eveningReflections = {
    [yestZero]: {
      bioDayId: yestZero,
      timestampMs: Date.now() - 36000000,
      gratitudeNote: 'Decidi dar um basta na inércia e recomeçar com humildade sobre a Rocha.',
      lessonLearnedToday: 'Não preciso fazer tudo de uma vez — basta ser fiel no pouco hoje.',
      tomorrowTopPriority: 'Cumprir meu Degrau Zero de 2 min + estudar a Lição #1 da Base Absoluta.',
      releasedResentment: true,
    },
  };

  return vault;
}

