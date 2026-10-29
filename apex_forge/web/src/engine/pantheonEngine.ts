import {
  DailyCheckIn,
  PantheonBriefing,
  ReadinessComputation,
  UserProfile,
  VaultState,
} from './types';

function deterministicHash(seed: string): number {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4294967295;
}

const VARIABLE_MASTERY_INSIGHTS: Array<{ title: string; scientificInsight: string }> = [
  {
    title: 'Sinal de Plasticidade no aMCC Detectado',
    scientificInsight:
      'Touroutoglou et al. (Cortex, 2020): cada vez que você executa uma ação planejada apesar da resistência subjetiva inicial, o Córtex Cingulado Médio Anterior recalibra para baixo o custo percebido de esforços futuros.',
  },
  {
    title: 'Circuito Pré-Frontal Anti-Desamparo Ativado',
    scientificInsight:
      'Maier & Watkins: exercer controle comportamental voluntário sob estresse ativa projeções do vmPFC que inibem o núcleo da rafe dorsal, criando imunização neural para crises futuras.',
  },
  {
    title: 'Contraste Dopaminérgico Preservado (Schultz RPE)',
    scientificInsight:
      'Ao ancorar satisfação no próprio esforço técnico — e não em recompensas fáceis previsíveis — seus receptores D2 mantêm sensibilidade tônica elevada sem rebote hedônico.',
  },
  {
    title: 'Remodelação Silenciosa de Colágeno e Mitocôndrias',
    scientificInsight:
      'Enquanto ganhos neurais aparecem em dias, cada sessão consistente abaixo do limiar de lesão deposita matriz extracelular tendínea e densidade capilar que sustentarão cargas de elite nos próximos meses.',
  },
];

export function buildPantheonBriefing(
  profile: UserProfile,
  checkIn: DailyCheckIn,
  readiness: ReadinessComputation,
  vault: VaultState,
): PantheonBriefing {
  const isRed = readiness.zone === 'VERMELHO';
  const isYellow = readiness.zone === 'AMARELO';
  const timeTight =
    (checkIn.availableMinutesToday ?? profile.weekdayFreeMinutes) <= 22;
  const highStress = checkIn.mentalCalm <= 3 || checkIn.externalLifeStressEvent;

  // Check if yesterday had a missed log or relapse
  const totalWorkouts = vault.workouts.length;

  // 1. Choose Safe Daily aMCC Micro-Friction Challenge (NEVER violates clinical/joint vetoes!)
  let amccChallenge: PantheonBriefing['amccChallenge'];
  if (isRed || checkIn.viralOrFeverSymptoms) {
    amccChallenge = {
      id: 'amcc_sleep_blackout',
      title: 'Corte Frio de Estímulo 45 min Antes do Sono',
      durationMin: 5,
      description:
        'Frieza cirúrgica hoje: desligar telas hiperestimulantes 45 min antes do horário-alvo de dormir e preparar o dia seguinte em silêncio.',
    };
  } else if (profile.executiveProfile === 'IMPULSIVO_BUSCA_NOVIDADE') {
    amccChallenge = {
      id: 'amcc_zero_phone_transition',
      title: 'Ignição de 120s Sem Negociação Digital',
      durationMin: 2,
      description:
        'Antes de iniciar o treino ou estudo, coloque o celular fora do alcance visual e execute os primeiros 2 minutos em silêncio absoluto.',
    };
  } else if (highStress) {
    amccChallenge = {
      id: 'amcc_cold_focus_posture',
      title: '5 Minutos de Imobilidade Calma / Respiração Controlada',
      durationMin: 5,
      description:
        'Quando o impulso mandar correr para distrações rápidas, sustente 5 minutos de cadência autonômica sem fugir do desconforto.',
    };
  } else {
    amccChallenge = {
      id: 'amcc_strict_last_set_cadence',
      title: 'Cadência Cirúrgica na Última Série (3s Excêntrica)',
      durationMin: 4,
      description:
        'Na última série principal do dia, mantenha 3 segundos exatos de descida controlada sem roubar postura quando o músculo arder.',
    };
  }

  // 2. Intermittent Variable Reinforcement (p = 0.28 only when effort history > 0)
  const rpeRoll = deterministicHash(`${checkIn.bioDayId}:${totalWorkouts}:${vault.currentPhase}`);
  const variableRewardUnlocked =
    totalWorkouts >= 1 && rpeRoll < 0.28
      ? VARIABLE_MASTERY_INSIGHTS[
          Math.floor(rpeRoll * 100) % VARIABLE_MASTERY_INSIGHTS.length
        ]
      : undefined;

  // 3. Contextual Mentor Selection (respecting user voice preference + acute bottleneck)
  if (isRed) {
    if (profile.commandVoice === 'CRISTO_BIBLIA') {
      return {
        mentorId: 'JESUS_CRISTO',
        mentorName: 'Jesus Cristo (Marcos 6:31 & 1 Coríntios 6:19)',
        archetypeTitle: 'Mordomia do Templo & Repouso Sábio (Zona Vermelha)',
        tacticalDirective:
          '“Vinde vós, aqui à parte, e repousai um pouco” (Mc 6:31). Forçar o corpo doente ou lesionado por orgulho não é fé, é imprudência. Hoje os sinais clínicos apontam Zona Vermelha: honre seu corpo com recuperação ativa limpa, hidratação e sono no horário certo para voltar inteiro amanhã.',
        neuroMechanismNote:
          'Proteção Alostática & Imunológica: respeitar o freio autonômico preserva tecido conjuntivo, miocárdio e controle pré-frontal.',
        amccChallenge,
        variableRewardUnlocked,
      };
    }
    return {
      mentorId: 'GOGGINS',
      mentorName: 'David Goggins × Musashi',
      archetypeTitle: 'Disciplina Fria de Recuperação (Zero Ego)',
      tacticalDirective:
        'Qualquer amador estoura o próprio tendão ou sistema imune tentando provar que é durão. Hoje os dados mostram alerta Vermelho. Encare o espelho sem desculpa: sua missão hoje é recuperação ativa limpa, hidratação e sono no horário cravado para voltar letal amanhã.',
      neuroMechanismNote:
        'Proteção Alostática: suprimir o impulso de treinar por ansiedade/ego exige alto controle inibitório do córtex pré-frontal dorsolateral.',
      amccChallenge,
      variableRewardUnlocked,
    };
  }

  if (timeTight) {
    return {
      mentorId: 'DOCTOR_WHO',
      mentorName: 'The Doctor (Doctor Who)',
      archetypeTitle: 'Pivot Tático Lateral Sob Pressão de Tempo',
      tacticalDirective:
        'A agenda explodiu e sobraram poucos minutos? Ótimo — pânico é desperdício de processamento. Reavaliamos o cenário: densidade máxima, descanso curto agonista-antagonista e zero tempo perdido. Dezoito minutos executados com genialidade batem duas horas adiadas.',
      neuroMechanismNote:
        'Reavaliação Cognitiva (Blascovich & Mendes): converter ameaça de tempo em desafio tático aumenta débito cardíaco eficiente sem vasoconstrição de pânico.',
      amccChallenge,
      variableRewardUnlocked,
    };
  }

  if (highStress && profile.commandVoice === 'ADAPTATIVO') {
    return {
      mentorId: 'MARCO_AURELIO',
      mentorName: 'Marco Aurélio × Maquiavel',
      archetypeTitle: 'Dicotomia do Controle & Diques Contra a Fortuna',
      tacticalDirective:
        'Estresse externo elevado detectado (carga alostática ativa). Separe imediatamente o que está fora do seu comando do próximo passo físico e técnico que depende 100% de você. Reduzimos o volume acessório para blindar seu sistema nervoso sem quebrar a corrente.',
      neuroMechanismNote:
        'Stults-Kolehmainen (2014): estresse psicológico consome capacidade real de recuperação muscular em até 96h; ajustar volume preserva ganhos sem burnout.',
      amccChallenge,
      variableRewardUnlocked,
    };
  }

  switch (profile.commandVoice) {
    case 'CRISTO_BIBLIA':
      return {
        mentorId: isYellow || highStress ? 'SALOMAO_BIBLIA' : 'JESUS_CRISTO',
        mentorName:
          isYellow || highStress
            ? 'Sabedoria Bíblica (Provérbios, Tiago & Paulo)'
            : 'Jesus Cristo — O Mestre dos Mestres',
        archetypeTitle:
          isYellow || highStress
            ? 'Domínio Próprio, Paz Interior & Renovação da Mente (Pv 16:32 • Fp 4:6–8)'
            : 'A Casa Edificada na Rocha & Fiel no Pouco (Mt 7:24 • Lc 16:10)',
        tacticalDirective:
          isYellow || highStress
            ? '"Melhor é o que governa o seu espírito do que o que toma uma cidade" (Provérbios 16:32). Hoje o foco não é vaidade nem pressa: acalme a mente ("basta a cada dia o seu próprio mal" — Mt 6:34), guarde a palavra e cumpra sua parte com sobriedade e constância.'
            : '"Todo aquele que ouve estas minhas palavras e as pratica será comparado a um homem prudente que edificou a sua casa sobre a rocha" (Mateus 7:24). Não busque aplauso externo hoje: pratique em secreto com excelência, seja fiel no pouco e use sua força para servir e edificar.',
        neuroMechanismNote:
          'Motivação Intrínseca & Propósito Transcendente (Kasser & Ryan; Cohen et al., N = 488.765; Worthington): ancorar o esforço em caráter, perdão e serviço reduz cortisol reativo e sustenta consistência inabalável.',
        amccChallenge,
        variableRewardUnlocked,
      };

    case 'GOGGINS_MUSASHI':
      return {
        mentorId: isYellow ? 'MUSASHI' : 'GOGGINS',
        mentorName: isYellow ? 'Miyamoto Musashi' : 'David Goggins',
        archetypeTitle: isYellow
          ? 'Economia Letal — Nada Que Seja Inútil'
          : 'Regra dos 40% Calibrada & Calejamento do aMCC',
        tacticalDirective: isYellow
          ? 'Prontidão moderada hoje: corte qualquer movimento ansioso ou volume de vaidade. Entre, execute cada repetição com postura impecável e saia mais forte do que entrou.'
          : 'Todas as travas fisiológicas estão Verdes. Quando a mente pedir para negociar na metade da série, lembre-se: esse primeiro alarme é governança psicológica de conforto, não seu limite celular real. Execute até o RIR prescrito com técnica fria.',
        neuroMechanismNote:
          'Modelo Psicobiológico de Marcora + aMCC: tolerar esforço voluntário dentro da margem biomecânica segura eleva o teto de percepção de esforço.',
        amccChallenge,
        variableRewardUnlocked,
      };

    case 'SENKU_FEYNMAN':
      return {
        mentorId: totalWorkouts % 2 === 0 ? 'SENKU' : 'FEYNMAN',
        mentorName:
          totalWorkouts % 2 === 0
            ? 'Senku Ishigami (Primeiros Princípios)'
            : 'Richard Feynman (Anti-Autoengano)',
        archetypeTitle:
          totalWorkouts % 2 === 0
            ? 'Árvore Tecnológica — 10 Bilhões % Determinístico'
            : 'Primeira Regra: Não Engane a Si Mesmo',
        tacticalDirective:
          totalWorkouts % 2 === 0
            ? 'Do cidadão comum ao alto nível não existe milagre: existe termodinâmica, síntese proteica, mielinização e soma diária de 1 passo verificável por vez. Siga os números da sessão de hoje.'
            : 'Não confunda estar ocupado ou suado com evoluir. Na barra, meça amplitude e controle real; no estudo, meça o que você consegue resolver sem olhar a resposta.',
        neuroMechanismNote:
          'Ericsson & Bjork: feedback objetivo de erro elimina a ilusão de fluência e força reconsolidação sináptica real.',
        amccChallenge,
        variableRewardUnlocked,
      };

    case 'STARK_MAQUIAVEL':
      return {
        mentorId: totalWorkouts % 2 === 0 ? 'STARK' : 'MAQUIAVEL',
        mentorName:
          totalWorkouts % 2 === 0
            ? 'Tony Stark (Engenharia Mark N+1)'
            : 'Nicolau Maquiavel (Verità Effettuale)',
        archetypeTitle:
          totalWorkouts % 2 === 0
            ? 'Telemetria & Iteração Contínua Sem Culpa'
            : 'Virtù Sobre a Fortuna — Arquitetura de Ambiente',
        tacticalDirective:
          totalWorkouts % 2 === 0
            ? 'Trate seu corpo e sua rotina como um protótipo de engenharia de alta precisão. Colete os dados da sessão de hoje e ajuste o parafuso que falhou ontem — zero drama, 100% upgrade.'
            : 'Não confie na sua força de vontade das 22h30: governe a realidade efetiva. Deixe água, treino e bloqueio de distrações travados agora enquanto sua mente está fria.',
        neuroMechanismNote:
          'Gollwitzer (642 testes): pré-compromissos condicionais Se-Então transferem o gatilho da ação do córtex pré-frontal fatigável para pistas automáticas do ambiente.',
        amccChallenge,
        variableRewardUnlocked,
      };

    case 'ADAPTATIVO':
    default: {
      const rotation: Array<PantheonBriefing['mentorId']> = [
        'JESUS_CRISTO',
        'GOGGINS',
        'SENKU',
        'SALOMAO_BIBLIA',
        'STARK',
        'TESLA',
        'MAQUIAVEL',
        'DA_VINCI',
      ];
      const pick = rotation[totalWorkouts % rotation.length];
      if (pick === 'JESUS_CRISTO') {
        return {
          mentorId: 'JESUS_CRISTO',
          mentorName: 'Jesus Cristo — O Mestre dos Mestres',
          archetypeTitle: 'A Casa na Rocha, Fiel no Pouco & Grandeza pelo Serviço',
          tacticalDirective:
            '"Quem é fiel no mínimo também é fiel no muito" (Lucas 16:10). Não faça nada hoje para parecer grande diante de olhos alheios: construa sua fundação em secreto sobre a rocha da prática real, guarde o coração limpo de amargura e torne sua força útil ao próximo.',
          neuroMechanismNote:
            'Propósito Transcendente & Liderança Servidora (Eva et al., 2019; Meta-análise de 32 anos, N = 488.765): alinhar disciplina diária a propósito maior eleva resiliência autonômica e saúde de longo prazo.',
          amccChallenge,
          variableRewardUnlocked,
        };
      }
      if (pick === 'SALOMAO_BIBLIA') {
        return {
          mentorId: 'SALOMAO_BIBLIA',
          mentorName: 'Sabedoria Bíblica (Provérbios & Romanos 12:2)',
          archetypeTitle: 'Governar o Próprio Espírito & Renovar a Mente',
          tacticalDirective:
            '"Não vos conformeis com este século, mas transformai-vos pela renovação da vossa mente" (Romanos 12:2). A diligência silenciosa de hoje vence qualquer atalho apressado (Provérbios 21:5). Execute com domínio próprio e gratidão.',
          neuroMechanismNote:
            'Reestruturação Cognitiva + Gratidão (Beck; Emmons & McCullough, 2003): renovar padrões de pensamento e cultivar gratidão melhoram qualidade do sono e adesão ao treino.',
          amccChallenge,
          variableRewardUnlocked,
        };
      }
      if (pick === 'TESLA') {
        return {
          mentorId: 'TESLA',
          mentorName: 'Nikola Tesla',
          archetypeTitle: 'Simulação Mental Pré-Execução & Foco Isolado',
          tacticalDirective:
            'Antes de tocar no peso ou abrir o material complexo de hoje, simule por 90 segundos a execução perfeita do início ao fim. Corte o ruído externo e opere em bloco único.',
          neuroMechanismNote:
            'Equivalência Funcional Visuomotora (g = 0.75 em meta-análises): ensaio mental pré-ativa redes pré-motoras e reduz ansiedade de estado.',
          amccChallenge,
          variableRewardUnlocked,
        };
      }
      if (pick === 'DA_VINCI') {
        return {
          mentorId: 'DA_VINCI',
          mentorName: 'Leonardo da Vinci (Saper Vedere)',
          archetypeTitle: 'Equilíbrio Polímata — Força, Clareza e Precisão',
          tacticalDirective:
            'Observe a qualidade fina do movimento e da atenção hoje. O ápice humano exige um corpo potente sustentando uma mente observadora, curiosa e inabalável.',
          neuroMechanismNote:
            'Integração Sensório-Motora & BDNF: exercício aeróbico/resistido eleva fatores neurotróficos que potencializam a consolidação cognitiva nas horas seguintes.',
          amccChallenge,
          variableRewardUnlocked,
        };
      }
      if (pick === 'SENKU') {
        return {
          mentorId: 'SENKU',
          mentorName: 'Senku Ishigami',
          archetypeTitle: 'Roteiro Científico Passo a Passo',
          tacticalDirective:
            'Cada série controlada e cada bloco de foco hoje destrava o próximo nó da sua Árvore Tecnológica biológica. Dez bilhões por cento de foco no processo.',
          neuroMechanismNote:
            'Teoria da Autodeterminação (SDT): visibilidade clara de competência adquirida alimenta motivação autônoma duradoura.',
          amccChallenge,
          variableRewardUnlocked,
        };
      }
      if (pick === 'STARK') {
        return {
          mentorId: 'STARK',
          mentorName: 'Tony Stark',
          archetypeTitle: 'Protocolo Mark N+1 em Operação',
          tacticalDirective:
            'Sistemas calibrados e prontidão validada. Execute o protocolo do dia, registre a telemetria real em 1 toque e deixe o motor calcular o próximo salto.',
          neuroMechanismNote:
            'Ciclo Fechado de Feedback: autorregulação por RIR previne overreaching mantendo estímulo mecânico ótimo.',
          amccChallenge,
          variableRewardUnlocked,
        };
      }
      return {
        mentorId: 'GOGGINS',
        mentorName: 'David Goggins',
        archetypeTitle: 'Forja Diária Controlada — Sem Atalhos',
        tacticalDirective:
          'Prontidão Verde confirmada. Ninguém vem fazer as repetições nem estudar por você hoje. Entre focado, respeite a técnica até o fim e adicione mais uma prova real ao seu Cookie Jar.',
        neuroMechanismNote:
          'Autoeficácia de Bandura + aMCC: provas reais de execução difícil são a fonte #1 de confiança inabalável sob pressão.',
        amccChallenge,
        variableRewardUnlocked,
      };
    }
  }
}

export interface PantheonCodexEntry {
  id: PantheonBriefing['mentorId'];
  name: string;
  title: string;
  domain: string;
  neuroAnchor: string;
  maxim: string;
}

export const PANTHEON_CODEX: PantheonCodexEntry[] = [
  {
    id: 'JESUS_CRISTO',
    name: 'Jesus Cristo',
    title: 'O Mestre dos Mestres — A Rocha, o Perdão & a Grandeza no Servir',
    domain: 'Caráter Incorruptível, Amor Ágape, Humildade Forte & Propósito Eterno',
    neuroAnchor:
      'Liderança Servidora (Eva et al., 2019) + Perdão Clínico (Worthington) + Propósito e Longevidade (N = 488.765)',
    maxim:
      '"Quem quiser tornar-se grande entre vós, será esse o que vos sirva" (Marcos 10:43) — edifique sua vida sobre a rocha da prática fiel em secreto, perdoe para não carregar veneno e seja prudente como a serpente e simples como a pomba.',
  },
  {
    id: 'SALOMAO_BIBLIA',
    name: 'Sabedoria Bíblica (Salomão, Tiago & Paulo)',
    title: 'Domínio Próprio, Diligência, Freio da Língua & Metanoia',
    domain: 'Sabedoria Prática das Escrituras (Provérbios, Eclesiastes, Tiago e Epístolas)',
    neuroAnchor:
      'Controle Inibitório Pré-Frontal + Renovação Cognitiva (Romanos 12:2 / Beck) + Gratidão (Emmons & McCullough)',
    maxim:
      '"Melhor é o que governa o seu espírito do que o que toma uma cidade" (Provérbios 16:32) — pois Deus não nos deu espírito de covardia, mas de poder, de amor e de domínio próprio (2 Timóteo 1:7).',
  },
  {
    id: 'GOGGINS',
    name: 'David Goggins',
    title: 'Tenacidade aMCC, Regra dos 40% & Cookie Jar',
    domain: 'Fricção Voluntária Segura & Tolerância ao Desconforto',
    neuroAnchor: 'Plasticidade do aMCC (Touroutoglou et al., 2020) + Autoeficácia (Bandura)',
    maxim: 'Quando a mente pede arrego por conforto, você está em 40% — mas na Zona Vermelha clínica, a verdadeira disciplina fria é recuperar sem ego.',
  },
  {
    id: 'SENKU',
    name: 'Senku Ishigami',
    title: ' Empirismo Radical 10 Bilhões % & Alavanca 1 mm',
    domain: 'Método Científico & Consistência Incremental',
    neuroAnchor: 'Feedback Bayesiano Empírico + Curva de Hábito de 66 Dias',
    maxim: 'Zero misticismo: meça entrada e saída, empilhe 1 milímetro verificável por dia e a física garante o topo.',
  },
  {
    id: 'STARK',
    name: 'Tony Stark',
    title: 'Engenharia Iterativa Mark N+1 (Sem Culpa)',
    domain: 'Post-Mortem de Falhas & Upgrade de Sistema',
    neuroAnchor: 'Reavaliação Cognitiva Pré-Frontal (elimina efeito What-the-Hell)',
    maxim: 'Falhou hoje? Não faça drama: isole o bug estrutural da Mark atual e instale o patch mecânico na Mark N+1.',
  },
  {
    id: 'DOCTOR_WHO',
    name: 'Doctor Who',
    title: 'Pivô Temporal Assimétrico sob Caos Agudo',
    domain: 'Improvisação Estratégica & Preservação de Agência',
    neuroAnchor: 'Controle vmPFC → Rafe Dorsal contra Desamparo Aprendido (Maier & Watkins)',
    maxim: 'Quando o plano de 60 minutos explode, 5 a 15 minutos cirúrgicos salvam a linha temporal inteira.',
  },
  {
    id: 'TESLA',
    name: 'Nikola Tesla',
    title: 'Câmara de Simulação Mental Multissensorial',
    domain: 'Ensaio Corticomotor PETTLEP & Pré-Ativação',
    neuroAnchor: 'Imagética Motora Funcional (g = 0.75) + Recrutamento Pré-Motor',
    maxim: 'Construa, teste sob estresse e corrija a execução inteira no córtex antes do primeiro movimento físico.',
  },
  {
    id: 'MAQUIAVEL',
    name: 'Nicolau Maquiavel',
    title: 'Virtù vs. Fortuna — Diques Antes da Cheia',
    domain: 'Arquitetura de Ambiente & Pré-Compromisso',
    neuroAnchor: 'Intenções de Implementação Se-Então (Gollwitzer, 642 testes, d = 0.65)',
    maxim: 'A força de vontade às 22h é fraca; vença a tentação às 08h construindo diques físicos onde a sabotagem costuma inundar.',
  },
  {
    id: 'MARCO_AURELIO',
    name: 'Marco Aurélio',
    title: 'Cidadela Interna & Dicotomia do Controle',
    domain: 'Regulação Autonômica & Desfusão sob Crise',
    neuroAnchor: 'Freio Vagal 0.1 Hz + Desfusão Cognitiva MAC/ACT (SMD = −1.33)',
    maxim: 'Separe o evento externo da sua resposta fisiológica; governe a expiração e o julgamento permanece intacto.',
  },
  {
    id: 'MUSASHI',
    name: 'Miyamoto Musashi',
    title: 'Dokkōdō — Economia Absoluta de Movimento',
    domain: 'Precisão Biomecânica & Foco Monoponto',
    neuroAnchor: 'Eficiência Neuromuscular + Supressão de Ruído Motor',
    maxim: 'Não faça nada inútil: cada repetição deve ter trajetória limpa, tensão deliberada e zero vaidade.',
  },
  {
    id: 'FEYNMAN',
    name: 'Richard Feynman',
    title: 'Detector Anti-Autoengano & Síntese Pura',
    domain: 'Aprendizado Profundo & Auditoria de Maestria',
    neuroAnchor: 'Prática Deliberada no Domínio Real (Ericsson; Sala & Gobet, 2023)',
    maxim: 'O primeiro princípio é não enganar a si mesmo — e você é a pessoa mais fácil de enganar.',
  },
  {
    id: 'DA_VINCI',
    name: 'Leonardo da Vinci',
    title: 'Mente-Corpo Integrados (Saper Vedere)',
    domain: 'Sinergia Aeróbica-Cognitiva & Curiosidade Intrínseca',
    neuroAnchor: 'BDNF Hipocampal Induzido pelo Exercício + Teoria da Autodeterminação (SDT)',
    maxim: 'O movimento vigoroso nutre a clareza do intelecto, e a curiosidade sustentada impede a ferrugem da alma.',
  },
];

