import { MasteryTier, TeachingLesson, ReadinessZone } from './types';

/**
 * CODICE POLIMATA — VOLUME IV: SÍNTESE TRANSDISCIPLINAR (v22.0.0)
 * 20 Licoes de Sintese Transdisciplinar (2 por Pilar x 10 Pilares, Grau IV • Polimata),
 * elevando a Academia de 280 para 300 Licoes (30 por pilar).
 * Cada licao integra pelo menos dois pilares, promovendo aplicacao integrada.
 * Todo estudo cientifico citado possui fonte primaria verificavel.
 * Zero pseudociencia.
 */
export const TEACHINGS_VOLUME_4: TeachingLesson[] = [
  // =========================================================================
  // PILAR 1: CRISTO_EVANGELHOS — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Servico + Ciencia; Perdão + Neurociencia
  // =========================================================================
  {
    id: 'cristo_29_servico_ciencia_evidencia',
    trackId: 'CRISTO_EVANGELHOS',
    trackTitle: 'Ensinamentos de Jesus Cristo: A Rocha, Perdão & Serviço',
    masteryTier: 4,
    title: 'Servir com Evidência: Amor ao Próximo Fundamentado na Ciência',
    subtitle: 'Quando o servir bíblico encontra a evidência científica',
    mentorName: 'Jesus Cristo (Mateus 25:31-46) / Eva et al. (2019)',
    scientificSource:
      'Mateus 25:31-46; Eva et al. (Leadership Quarterly, 2019 — liderança servidora e performance); Post et al. (International Journal of Behavioral Medicine, 2013 — voluntariado e saúde)',
    readTimeSec: 80,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Jesus ensina que servir ao próximo é servir a Ele mesmo. A ciência confirma: o serviço ao próximo não é apenas nobre — é mensuravelmente benéfico. Voluntariado e atos de serviço estão ligados a menor depressão, maior bem-estar e até maior longevidade. Servir com evidência significa fazer o bem de forma eficaz, não apenas intencional.',
    whyItWorksMechanism:
    'Eva et al. (2019) mostram que liderança servidora melhora engajamento e performance de equipes. Post et al. (2013) demonstram que voluntariado regular prediz melhores resultados de saúde mental e física. O serviço ativa circuitos de recompensa cerebral e reduz isolamento social.',
    zeroStepExample:
    'Hoje, identifique uma necessidade concreta de alguém próximo e aja para atendê-la, não por sentimento, mas por decisão baseada em evidência de que isso beneficia ambos.',
    practicalActionToday:
    'Faça uma ação de serviço concreta para alguém, registrando antes e depois como você se sentiu e qual impacto teve.',
    fieldMission:
    'Por 7 dias, execute uma ação de serviço por dia e registre o impacto observado (não apenas a intenção).',
    dilemmaPrompt:
    'Você tem recursos limitados (tempo e dinheiro). Servir com evidência significa distribuir igualmente a todos, ou significa direcionar onde o impacto mensurável é maior?',
    dilemmaOptions: [
      'Dividir igualmente, independentemente do impacto.',
      'Ajudar apenas quem você conhece pessoalmente.',
      'Direcionar recursos onde a evidência mostra maior impacto mensurável.',
      'Não ajudar ninguém para evitar escolher.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Servir com inteligência: usar evidência para maximizar o impacto do bem.',
    feedbackTrap:
    'Boas intenções sem eficácia são apenas boas intenções.',
  },
  {
    id: 'cristo_30_perdao_neurociencia_liberacao',
    trackId: 'CRISTO_EVANGELHOS',
    trackTitle: 'Ensinamentos de Jesus Cristo: A Rocha, Perdão & Serviço',
    masteryTier: 4,
    title: 'Perdoar com Neurociência: Liberação que Muda o Cérebro',
    subtitle: 'O perdão como reconfiguração cerebral, não apenas ato moral',
    mentorName: 'Jesus Cristo (Lucas 23:34) / Witvliet et al. (2001)',
    scientificSource:
      'Lucas 23:34; Witvliet et al. (Cognition & Emotion, 2001 — perdão e resposta fisiológica); Worthington & Scherer (2004 — modelo REACH)',
    readTimeSec: 75,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Jesus perdoou os seus crucificadores. O perdão não é apenas um mandamento moral — é uma reconfiguração cerebral. Quando perdoamos, reduzimos a ativação da amígdala (medo/ameaça) e fortalecemos o vmPFC (regulação emocional). Perdoar é, literalmente, mudar a própria biologia.',
    whyItWorksMechanism:
    'Witvliet et al. (2001) mostraram que lembrar ofensas com rancor aumenta pressão arterial e tensão muscular, enquanto perdoar reduz essas respostas. O modelo REACH de Worthington fornece um framework estruturado para o perdão.',
    zeroStepExample:
    'Quando lembrar de uma ofensa hoje, note as sensações físicas no seu corpo (peito apertado, mandíbula tensa) e respire profundamente três vezes.',
    practicalActionToday:
    'Escreva o nome de alguém que você precisa perdoar e anote uma qualidade boa dessa pessoa, por menor que seja.',
    fieldMission:
    'Por 5 dias, sempre que uma memória de ofensa surgir, observe as sensações físicas e respire conscientemente por 1 minuto.',
    dilemmaPrompt:
    'Alguém te machucou profundamente e não pede desculpas. Perdoar com neurociência significa esquecer o que aconteceu, ou significa mudar sua resposta biológica à memória do evento?',
    dilemmaOptions: [
      'Esquecer completamente e agir como se nada tivesse acontecido.',
      'Manter o rancor como proteção contra nova dor.',
      'Mudar sua resposta biológica à memória (perdoar) sem esquecer o fato.',
      'Exigir desculpas públicas antes de considerar o perdão.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Perdão neurocientífico: mudar sua resposta ao evento, não apagar o evento.',
    feedbackTrap:
    'Esquecer é impossível e não é o objetivo; transformar a resposta é.',
  },

  // =========================================================================
  // PILAR 2: SABEDORIA_BIBLICA — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Provérbios + Lógica; Eclesiastes + Estatística
  // =========================================================================
  {
    id: 'salomao_29_proverbios_logica_decision',
    trackId: 'SABEDORIA_BIBLICA',
    trackTitle: 'Sabedoria Bíblica: Provérbios, Eclesiastes & Jó',
    masteryTier: 4,
    title: 'Provérbios e Lógica: Decisão Sábia como Raciocínio Estruturado',
    subtitle: 'A sabedoria bíblica encontra o raciocínio lógico formal',
    mentorName: 'Rei Salomão (Provérbios 3:13-18) / Stanovich & West (2000)',
    scientificSource:
      'Provérbios 3:13-18; Stanovich & West (Psychonomic Bulletin & Review, 2000 — racionalidade e pensamento lógico); Grossmann (2017 — raciocínio sábio)',
    readTimeSec: 80,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Provérbios personifica a sabedoria como algo mais precioso que ouro e prata. A sabedoria bíblica não é intuição mística — é raciocínio estruturado, disciplinado e aplicável. A lógica formal é a ferramenta que torna a sabedoria operacional nas decisões cotidianas.',
    whyItWorksMechanism:
    'Stanovich e West (2000) mostram que o pensamento lógico e a racionalidade são habilidades mensuráveis que predizem melhores decisões de vida. Grossmann (2017) define raciocínio sábio como combinação de humildade intelectual e perspectiva de longo prazo.',
    zeroStepExample:
    'Antes de tomar uma decisão hoje, escreva as premissas (o que você sabe com certeza) e a conclusão (o que você quer decidir), verificando se a conclusão segue logicamente.',
    practicalActionToday:
    'Escolha uma decisão que você tomará hoje e escreva o raciocínio lógico passo a passo que a fundamenta.',
    fieldMission:
    'Por 7 dias, registre decisões importantes e avalie se o raciocínio por trás delas é logicamente válido.',
    dilemmaPrompt:
    'Você tem duas boas opções de carreira. Sabedoria lógica significa escolher baseada apenas em sentimento, ou significa estruturar os prós e contras de forma sistemática?',
    dilemmaOptions: [
      'Escolher baseada apenas no sentimento do momento.',
      'Escolher baseada apenas no que os outros dizem.',
      'Estruturar prós e contras de forma sistemática e lógica.',
      'Adiar a decisão indefinidamente.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Sabedoria aplicada: estrutura lógica com humildade intelectual.',
    feedbackTrap:
    'Sentimento sem estrutura é impulso; estrutura sem sentimento é frio.',
  },
  {
    id: 'salomao_30_eclesiastes_estatistica_vaidade',
    trackId: 'SABEDORIA_BIBLICA',
    trackTitle: 'Sabedoria Bíblica: Provérbios, Eclesiastes & Jó',
    masteryTier: 4,
    title: 'Eclesiastes e Estatística: A Vaidade dos Dados sem Contexto',
    subtitle: 'Números sem sabedoria são apenas ruído',
    mentorName: 'Rei Salomão (Eclesiastes 1:2-11) / Tversky & Kahneman (1974)',
    scientificSource:
      'Eclesiastes 1:2-11; Tversky & Kahneman (Science, 1974 — heurísticas e vieses); Gigerenzer (2002 — frequências naturais)',
    readTimeSec: 75,
    recommendedZone: 'AMARELO',
    coreEssence:
    '\"Vaidade de vaidades, tudo é vaidade.\" Eclesiastes alerta que acumular conhecimento sem propósito é vazio. Da mesma forma, dados estatísticos sem sabedoria interpretativa são apenas ruído. Estatística sem contexto leva a conclusões enganosas.',
    whyItWorksMechanism:
    'Tversky e Kahneman (1974) demonstram que dados numéricos ativam vieses cognitivos quando não interpretados com cuidado. Gigerenzer (2002) mostra que frequências naturais são mais compreensíveis que probabilidades abstratas.',
    zeroStepExample:
    'Quando ver uma estatística hoje, pergunte: \"Qual é o contexto? Quem coletou? Qual é a taxa base?\" antes de aceitar a conclusão.',
    practicalActionToday:
    'Escolha uma estatística que você viu nas notícias hoje e investigue sua fonte e contexto.',
    fieldMission:
    'Por 5 dias, sempre que encontrar um dado estatístico, questione a taxa base e o contexto antes de formar uma opinião.',
    dilemmaPrompt:
    'Um estudo diz que 90% das pessoas bem-sucedidas acordam às 5h. Estatística com sabedoria significa acordar às 5h imediatamente, ou significa questionar se correlação implica causalidade?',
    dilemmaOptions: [
      'Acordar às 5h porque 90% dos bem-sucedidos fazem isso.',
      'Ignorar completamente a estatística.',
      'Questionar se correlação implica causalidade e buscar contexto.',
      'Acordar às 5h apenas porque o estudo disse, sem questionar.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Estatística com sabedoria: contexto e causalidade antes da ação.',
    feedbackTrap:
    'Correlação não é causalidade; dados sem contexto são perigosos.',
  },

  // =========================================================================
  // PILAR 3: GARRA_AUTODOMINIO — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Goggins + Hábitos; Disciplina + Sono
  // =========================================================================
  {
    id: 'goggins_29_habitos_autodominio_formacao',
    trackId: 'GARRA_AUTODOMINIO',
    trackTitle: 'Garra e Autodomínio: Mentalidade de David Goggins',
    masteryTier: 4,
    title: 'Garra na Formação de Hábitos: O 40% Aplica-se à Rotina',
    subtitle: 'Disciplina não é evento, é sistema de repetição',
    mentorName: 'David Goggins / Lally et al. (2010)',
    scientificSource:
      'Goggins (Can\'t Hurt Me, 2018); Lally et al. (European Journal of Social Psychology, 2010 — formação de hábitos, 59-66 dias); Wood & Neal (2007 — hábitos e contexto)',
    readTimeSec: 80,
    recommendedZone: 'VERMELHO',
    coreEssence:
    'Goggins diz que quando você pensa que acabou, usou apenas 40%. O mesmo vale para hábitos: quando você acha que já estabeleceu um hábito, provavelmente está nos primeiros 40% do caminho. Formar um hábito exige 59-66 dias de repetição consistente, não algumas semanas.',
    whyItWorksMechanism:
    'Lally et al. (2010) mostraram que a formação automática de hábitos leva em média 66 dias (variando de 18 a 254 dias). Wood e Neal (2007) mostram que hábitos dependem de contexto estável e repetição consistente.',
    zeroStepExample:
    'Escolha UM hábito hoje e comprometa-se a fazê-lo por 66 dias, não por uma semana.',
    practicalActionToday:
    'Escreva um hábito que quer formar, a data de início e a meta de 66 dias.',
    fieldMission:
    'Por 66 dias, execute o hábito escolhido diariamente, registrando cada dia.',
    dilemmaPrompt:
    'Você tenta formar um hábito de exercício diário. Depois de 2 semanas, sente que já é hábito. A Regra dos 40% aplicada a hábitos significa parar porque já está formado, ou significa continuar porque está nos primeiros 40%?',
    dilemmaOptions: [
      'Parar porque já parece automático.',
      'Continuar sabendo que a formação real leva 59-66 dias.',
      'Mudar o hábito completamente porque está chato.',
      'Desistir porque é muito difícil.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
    'Formação de hábitos exige persistência além do conforto inicial.',
    feedbackTrap:
    'A sensação de automatização precoce é ilusão; o hábito real leva meses.',
  },
  {
    id: 'goggins_30_sono_performance_disciplina',
    trackId: 'GARRA_AUTODOMINIO',
    trackTitle: 'Garra e Autodomínio: Mentalidade de David Goggins',
    masteryTier: 4,
    title: 'Sono como Disciplina: O Descanso que Fortalece a Mente',
    subtitle: 'Dormir bem não é preguiça, é estratégia de elite',
    mentorName: 'David Goggins / Walker (2017)',
    scientificSource:
      'Goggins (Can\'t Hurt Me, 2018); Walker (Why We Sleep, 2017); Scullin et al. (2018 — descarregamento pré-sono, d=0.63)',
    readTimeSec: 75,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Goggins treina duro, mas entende que o sono é quando o cérebro se reconfigura. Dormir 7-9 horas não é fraqueza — é disciplina estratégica. A privação de sono prejudica julgamento, reatividade emocional e tomada de decisão mais que o álcool em níveis legais.',
    whyItWorksMechanism:
    'Walker (2017) explica que o sono consolida memórias, remove toxinas metabólicas e restaura a função cognitiva. Scullin et al. (2018) mostram d=0.63 para descarregamento pré-sono melhorando o desempenho no dia seguinte.',
    zeroStepExample:
    'Hoje à noite, estabeleça um horário para dormir e desligue telas 30 minutos antes.',
    practicalActionToday:
    'Escreva 3 tarefas para amanhã antes de dormir (descarregamento pré-sono) e durma no horário estabelecido.',
    fieldMission:
    'Por 7 dias, durma no mesmo horário e pratique descarregamento pré-sono todas as noites.',
    dilemmaPrompt:
    'Você tem um prazo importante amanhã. Sono como disciplina significa trabalhar a noite toda, ou significa dormir bem e usar o descarregamento pré-sono para performar melhor?',
    dilemmaOptions: [
      'Trabalhar a noite toda sem dormir.',
      'Dormir 4 horas e trabalhar o resto.',
      'Dormir bem (7-9h) e usar descarregamento pré-sono para organizar a mente.',
      'Desistir do prazo por causa do cansaço.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Disciplina estratégica: sono de qualidade vence privação.',
    feedbackTrap:
    'Privação de sono parece produtividade, mas é deterioração cognitiva.',
  },

  // =========================================================================
  // PILAR 4: APRENDIZAGEM_MEMORIA — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Feynman + Xadrez; Espaçamento + Música
  // =========================================================================
  {
    id: 'dunlosky_29_feynman_xadrez_ensinar_por_jogos',
    trackId: 'APRENDIZAGEM_MEMORIA',
    trackTitle: 'Aprendizagem e Memória: Técnicas Baseadas em Evidência',
    masteryTier: 4,
    title: 'Ensinar Xadrez para Aprender: A Técnica de Feynman Aplicada',
    subtitle: 'Se você não consegue explicar uma abertura de xadrez, não a conhece',
    mentorName: 'Richard Feynman / Gobet & Simon (1996)',
    scientificSource:
      'Feynman (Surely You\'re Joking, 1985); Gobet & Simon (Cognitive Psychology, 1996 — teoria de templates em xadrez); Nestojko et al. (2014 — expectativa de ensinar)',
    readTimeSec: 80,
    recommendedZone: 'VERDE',
    coreEssence:
    'Feynman dizia: se você não consegue explicar algo simplesmente, não entendeu. Aplique isso ao xadrez: tente explicar uma abertura ou tática para alguém. Se você não consegue simplificar, não dominou o conceito. O xadrez é um laboratório perfeito para a Técnica de Feynman.',
    whyItWorksMechanism:
    'Gobet e Simon (1996) mostram que mestres de xadrez possuem ~50,000 templates (padrões) na memória. Nestojko et al. (2014) mostram que esperar ensinar melhora organização e retenção. Ensinar revela lacunas que o estudo silencioso esconde.',
    zeroStepExample:
    'Escolha uma tática de xadrez que você conhece e tente explicá-la em voz alta para alguém em menos de 2 minutos.',
    practicalActionToday:
    'Escolha um conceito de xadrez ou de qualquer domínio e grave um áudio explicando-o simplesmente.',
    fieldMission:
    'Por 10 dias, ensine um conceito diferente para alguém (ou grave para si mesmo).',
    dilemmaPrompt:
    'Você quer dominar uma abertura de xadrez. Técnica de Feynman significa jogar a abertura repetidamente sem entender, ou significa explicá-la para alguém e preencher as lacunas?',
    dilemmaOptions: [
      'Jogar repetidamente sem entender a teoria.',
      'Ler teoria sem tentar aplicar.',
      'Explicar a abertura para alguém e revisar onde falhar na explicação.',
      'Pedir para alguém jogar por você.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Ensinar revela o que você realmente sabe vs o que acha que sabe.',
    feedbackTrap:
    'Repetição sem compreensão é apenas repetição.',
  },
  {
    id: 'dunlosky_30_espacamento_musica_repeticao',
    trackId: 'APRENDIZAGEM_MEMORIA',
    trackTitle: 'Aprendizagem e Memória: Técnicas Baseadas em Evidência',
    masteryTier: 4,
    title: 'Repetição Espaçada em Música: O Cérebro Aprende em Intervalos',
    subtitle: 'Praticar um instrumento com espaçamento supera maratonas',
    mentorName: 'Cepeda et al. (2006) / Dunlosky et al. (2013)',
    scientificSource:
      'Cepeda et al. (Psych Bulletin, 2006 — ISI ótimo 10-20% do atraso); Dunlosky et al. (2013 — prática distribuída = alta utilidade); Ericsson et al. (1993 — prática deliberada)',
    readTimeSec: 75,
    recommendedZone: 'VERDE',
    coreEssence:
    'Músicos que praticam em sessões curtas espaçadas ao longo de semanas superam aqueles que fazem maratonas de prática. O espaçamento permite a consolidação da memória procedural. Praticar 20 minutos por dia por 7 dias é melhor que 2h40m em um único dia.',
    whyItWorksMechanism:
    'Cepeda et al. (2006) mostram que o intervalo ótimo entre revisões é cerca de 10-20% do tempo de retenção desejado. Dunlosky et al. (2013) classificam prática distribuída como de alta utilidade. Ericsson et al. (1993) mostra que prática deliberada com feedback é superior à repetição mecânica.',
    zeroStepExample:
    'Se você está aprendendo algo novo hoje, pratique por 20 minutos e retorne em 3 dias, não amanhã.',
    practicalActionToday:
    'Escolha uma habilidade que está aprendendo e programe revisões em 1 dia, 3 dias e 7 dias.',
    fieldMission:
    'Por 2 semanas, pratique uma habilidade usando espaçamento (1d, 3d, 7d, 14d).',
    dilemmaPrompt:
    'Você quer aprender uma música difícil no violão. Espaçamento significa praticar 3 horas seguidas hoje, ou significa praticar 20 minutos por dia por várias semanas?',
    dilemmaOptions: [
      'Praticar 3 horas seguidas hoje (maratona).',
      'Não praticar até sentir inspiração.',
      'Praticar 20 minutos por dia com espaçamento entre sessões.',
      'Praticar apenas nos finais de semana.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Espaçamento com prática deliberada vence maratonas.',
    feedbackTrap:
    'Maratonas criam ilusão de progresso; espaçamento gera retenção real.',
  },

  // =========================================================================
  // PILAR 5: COMUNICACAO_SOCIAL — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Covey + Negociação; Sinergia + Trabalho em equipe
  // =========================================================================
  {
    id: 'covey_29_comunicacao_nao_violenta_negociacao',
    trackId: 'COMUNICACAO_SOCIAL',
    trackTitle: 'Comunicação e Relações: Escuta, Empatia & Negociação',
    masteryTier: 4,
    title: 'Comunicação Não-Violenta e Negociação: Empatia como Estratégia',
    subtitle: 'Ouvir para entender é a melhor tática de negociação',
    mentorName: 'Stephen Covey (1989) / Rosenberg (2003)',
    scientificSource:
      'Covey (The 7 Habits, 1989); Rosenberg (Nonviolent Communication, 2003); Fisher & Ury (Getting to Yes, 1981)',
    readTimeSec: 80,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Covey ensina: busque primeiro entender, depois ser entendido. Rosenberg adiciona: comunique necessidades sem julgamento. Fisher e Ury completam: negocie sobre interesses, não posições. Comunicação não-violenta é a base de toda negociação bem-sucedida.',
    whyItWorksMechanism:
    'Rosenberg (2003) mostra que comunicação sem julgamento reduz defensividade e abre espaço para cooperação. Fisher e Ury (1981) demonstram que focar em interesses (não posições) gera acordos duradouros.',
    zeroStepExample:
    'Em uma conversa difícil hoje, antes de responder, pergunte: \"Qual é a necessidade não dita por trás do que essa pessoa está dizendo?\"',
    practicalActionToday:
    'Em um desacordo hoje, identifique a necessidade legítima da outra parte antes de apresentar sua posição.',
    fieldMission:
    'Por 5 dias, aplique comunicação não-violenta em todos os desacordos.',
    dilemmaPrompt:
    'Você está negociando um preço. Comunicação não-violenta significa ceder a tudo para manter a paz, ou significa entender as necessidades do outro e buscar acordo onde ambos ganham?',
    dilemmaOptions: [
      'Ceder a tudo para evitar conflito.',
      'Impor sua posição sem ouvir o outro.',
      'Entender as necessidades do outro e buscar acordo mútuo.',
      'Abandonar a negociação.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Negociação baseada em interesses, não em posições ou cedência.',
    feedbackTrap:
    'Ceder por medo de conflito não é empatia; é submissão.',
  },
  {
    id: 'covey_30_sinergia_equipe_diversidade',
    trackId: 'COMUNICACAO_SOCIAL',
    trackTitle: 'Comunicação e Relações: Escuta, Empatia & Negociação',
    masteryTier: 4,
    title: 'Sinergia em Equipes: Diversidade como Motor de Inovação',
    subtitle: '1+1=3 quando perspectivas diferentes colaboram',
    mentorName: 'Stephen Covey (1989) / Page (2007)',
    scientificSource:
      'Covey (The 7 Habits, 1989); Page (The Difference, 2007 — diversidade cognitiva); Rock & Grant (2016 — diversidade e performance)',
    readTimeSec: 80,
    recommendedZone: 'VERDE',
    coreEssence:
    'Sinergia significa que o todo é maior que a soma das partes. Equipes com diversidade cognitiva (diferentes formas de pensar, diferentes backgrounds) resolvem problemas complexos melhor que equipes homogêneas de especialistas. A diferença não é obstáculo — é matéria-prima.',
    whyItWorksMechanism:
    'Scott Page (2007) demonstra matematicamente que grupos diversos superam grupos de especialistas homogêneos em problemas complexos. Rock e Grant (2016) mostram que diversidade melhora inovação e performance organizacional.',
    zeroStepExample:
    'Em um problema que você está resolvendo hoje, peça a opinião de alguém que pensa completamente diferente de você.',
    practicalActionToday:
    'Convide alguém com perspectiva diferente para fazer brainstorming sobre um problema seu.',
    fieldMission:
    'Por 2 semanas, colabore ativamente com alguém que pensa diferente de você em um projeto.',
    dilemmaPrompt:
    'Sua equipe discorda sobre como resolver um problema. Sinergia significa escolher a ideia do líder, ou significa combinar elementos de diferentes ideias para criar algo novo?',
    dilemmaOptions: [
      'Seguir a ideia do líder sem questionar.',
      'Escolher por votação da maioria.',
      'Combinar elementos de diferentes ideias para criar solução superior.',
      'Cada pessoa seguir sua própria ideia separadamente.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Sinergia é criar algo novo a partir da diferença, não escolher um lado.',
    feedbackTrap:
    'Harmonia forçada (todos concordarem) suprime a diversidade que gera inovação.',
  },


  // =========================================================================
  // PILAR 6: LOGICA_NUMERACIA — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Kahneman + Decisão; Bayes + Evidência
  // =========================================================================
  {
    id: 'kahneman_29_vieses_decisao_vida_real',
    trackId: 'LOGICA_NUMERACIA',
    trackTitle: 'Lógica e Numeracia: Pensamento Rápido e Devagar',
    masteryTier: 4,
    title: 'Vieses Cognitivos em Decisões de Vida Real: Quando a Intuição Falha',
    subtitle: 'Reconhecer vieses nas grandes decisões, não apenas nas pequenas',
    mentorName: 'Daniel Kahneman (2011) / Tetlock (2015)',
    scientificSource:
      'Kahneman (Thinking, Fast and Slow, 2011); Tetlock (Superforecasting, 2015); Gilovich et al. (1985 — viés do ponto quente na tomada de decisão)',
    readTimeSec: 80,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Kahneman documentou dezenas de vieses cognitivos que afetam decisões cotidianas. O ponto crucial é: esses vieses não afetam apenas escolhas triviais — afetam decisões de carreira, relacionamentos, investimentos e saúde. Reconhecer um vies é o primeiro passo; neutralizá-lo requer sistema 2 ativo.',
    whyItWorksMechanism:
    'Kahneman (2011) mostra que o Sistema 1 usa heurísticas que levam a vieses sistemáticos. Tetlock (2015) mostra que superprevisores neutralizam vieses através de atualização frequente e busca ativa de evidências contrárias.',
    zeroStepExample:
    'Antes de uma decisão importante hoje, escreva: \"Qual vies cognitivo pode estar afetando meu julgamento aqui?\"',
    practicalActionToday:
    'Escolha uma decisão importante que tomará nos próximos dias e liste 3 vieses que podem afetá-la.',
    fieldMission:
    'Por 7 dias, registre decisões importantes e identifique o vies cognitivo mais provável em cada uma.',
    dilemmaPrompt:
    'Você está decidindo mudar de cidade para um emprego melhor. Vieses cognitivos significa seguir o primeiro impulso (Sistema 1), ou significa usar o Sistema 2 para analisar prós, contras e alternativas?',
    dilemmaOptions: [
      'Seguir o primeiro impulso sem analisar.',
      'Não decidir por medo de vieses.',
      'Usar o Sistema 2 para analisar sistematicamente antes de decidir.',
      'Pedir para alguém decidir por você.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Reconhecer vieses e usar pensamento deliberado para decidir.',
    feedbackTrap:
    'Acreditar que você está imune a vieses é o maior vies de todos.',
  },
  {
    id: 'kahneman_30_bayes_evidencia_atualizacao',
    trackId: 'LOGICA_NUMERACIA',
    trackTitle: 'Lógica e Numeracia: Pensamento Rápido e Devagar',
    masteryTier: 4,
    title: 'Atualização Bayesiana na Vida: Mudar de Ideia com Novas Evidências',
    subtitle: 'Sua crença inicial não é um contrato vitalício',
    mentorName: 'Bayes (1763) / Tetlock & Gardner (2015)',
    scientificSource:
      'Bayes (1763 — teorema de Bayes); Tetlock & Gardner (Superforecasting, 2015); Kahneman & Tversky (1972 — atualização insuficiente)',
    readTimeSec: 75,
    recommendedZone: 'AMARELO',
    coreEssence:
    'O teorema de Bayes fornece a matemática para atualizar crenças com novas evidências. Sua crença inicial (probabilidade anterior) deve ser ajustada à medida que novos dados aparecem. Mudar de ideia não é fraqueza — é racionalidade bayesiana em ação.',
    whyItWorksMechanism:
    'O teorema de Bayes (1763) mostra como atualizar probabilidades com novas evidências. Tetlock e Gardner (2015) mostram que superprevisores atualizam crenças frequentemente e incrementalmente, não apenas quando forçados.',
    zeroStepExample:
    'Hoje, pegue uma crença forte que você tem e pergunte: \"Que evidência faria eu mudar de ideia sobre isso?\"',
    practicalActionToday:
    'Escolha uma crença e escreva quais evidências específicas mudariam sua opinião.',
    fieldMission:
    'Por 14 dias, sempre que formar uma opinião forte, registre o que a faria mudar.',
    dilemmaPrompt:
    'Você acredita fortemente em algo, mas novas evidências contradizem. Atualização bayesiana significa ignorar as evidências para manter a crença, ou significa ajustar a crença proporcionalmente às novas evidências?',
    dilemmaOptions: [
      'Ignorar evidências e manter a crença original.',
      'Mudar completamente a crença a cada nova evidência.',
      'Ajustar a crença proporcionalmente à força das novas evidências.',
      'Não ter crenças para não precisar mudá-las.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Atualização bayesiana é ajustar crenças com evidência, não dogmatismo.',
    feedbackTrap:
    'Não atualizar crenças diante de evidência é teimosia, não lealdade.',
  },

  // =========================================================================
  // PILAR 7: CIENCIA_PRIMEIROS_PRINCIPIOS — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Musk + Engenharia; Popper + Falsificação
  // =========================================================================
  {
    id: 'musk_29_primeiros_principios_engenharia',
    trackId: 'CIENCIA_PRIMEIROS_PRINCIPIOS',
    trackTitle: 'Ciência e Primeiros Princípios: Pensar como um Cientista',
    masteryTier: 4,
    title: 'Primeiros Princípios em Engenharia: Desconstruir Problemas Complexos',
    subtitle: 'Não aceite \"é assim que se faz\" — questione o fundamento',
    mentorName: 'Elon Musk / Aristoteles (Metafísica)',
    scientificSource:
      'Musk (entrevistas, 2012-2024 — primeiros princípios em foguetes e baterias); Aristoteles (Metafísica, século IV a.C.); Feynman (1965 — O Caráter da Lei Física)',
    readTimeSec: 80,
    recommendedZone: 'VERDE',
    coreEssence:
    'Musk usou primeiros princípios para questionar por que foguetes custam milhões e construiu foguetes reutilizáveis. O mesmo se aplica a qualquer problema: desconstrua até as verdades fundamentais e reconstrua a partir daí. Não aceite tradição como justificativa.',
    whyItWorksMechanism:
    'Aristóteles definiu primeiros princípios como a base de todo conhecimento. Feynman (1965) enfatizou que a ciência avança questionando suposições, não aceitando autoridade. Primeiros princípios evitam a armadilha da tradição cega.',
    zeroStepExample:
    'Escolha uma crença sobre dinheiro ou carreira hoje e pergunte: \"Qual é a verdade fundamental, e qual é apenas tradição?\"',
    practicalActionToday:
    'Escolha um problema que você está enfrentando e quebre-o em seus componentes mais básicos, sem assumir nada.',
    fieldMission:
    'Por 2 semanas, aplique primeiros princípios em um problema importante por semana.',
    dilemmaPrompt:
    'Você quer mudar de carreira mas acha que é \"muito tarde\". Primeiros princípios significa aceitar a limitação, ou significa quebrar a crença em componentes (habilidades, tempo, recursos) e reconstruir um plano?',
    dilemmaOptions: [
      'Aceitar que é tarde demais e não tentar.',
      'Ignorar a idade e mudar sem planejamento.',
      'Desconstruir a crença em componentes reais e reconstruir um plano baseado em fatos.',
      'Esperar o momento perfeito que nunca chega.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Primeiros princípios substituem suposições por fatos verificáveis.',
    feedbackTrap:
    'A tradição diz \"é assim que se faz\"; primeiros princípios perguntam \"por que?\".',
  },
  {
    id: 'musk_30_popper_falsificacao_vida_diaria',
    trackId: 'CIENCIA_PRIMEIROS_PRINCIPIOS',
    trackTitle: 'Ciência e Primeiros Princípios: Pensar como um Cientista',
    masteryTier: 4,
    title: 'Falsificação na Vida Diária: Tente Provar que Está Errado',
    subtitle: 'A ciência avança tentando se refutar, não se confirmar',
    mentorName: 'Karl Popper (1934) / Tetlock (2015)',
    scientificSource:
      'Popper (A Lógica da Descoberta Científica, 1934); Tetlock (Superforecasting, 2015); Wason (1960 — tarefa de seleção)',
    readTimeSec: 75,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Popper propôs que uma teoria é científica se puder ser provada falsa. Aplicado à vida: não busque confirmação para suas crenças; busque ativamente evidências que as contradigam. Isso é o oposto do viés de confirmação.',
    whyItWorksMechanism:
    'Popper (1934) estabeleceu a falsificabilidade como critério de demarcação científica. Tetlock (2015) mostra que superprevisores buscam ativamente informações que contradizem suas crenças. Wason (1960) mostra que pessoas tendem a buscar confirmação, não falsificação.',
    zeroStepExample:
    'Hoje, pegue uma opinião forte que você tem e procure ativamente por 3 razões pelas quais ela pode estar errada.',
    practicalActionToday:
    'Escreva uma opinião forte e liste evidências que a contradizem.',
    fieldMission:
    'Por 10 dias, toda vez que formar uma opinião forte, procure ativamente por evidências contrárias.',
    dilemmaPrompt:
    'Você tem uma teoria sobre por que seu projeto está falhando. Falsificação significa ignorar críticas e focar no positivo, ou significa buscar ativamente evidências que sua teoria está errada?',
    dilemmaOptions: [
      'Ignorar críticas e focar apenas no positivo.',
      'Achar que está errado em tudo e desistir.',
      'Buscar ativamente evidências que sua teoria está errada para testá-la.',
      'Esperar que alguém aponte seus erros sem você procurar.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'A ciência avança tentando se provar errada, não se provar certa.',
    feedbackTrap:
    'O viés de confirmação faz você ver apenas o que já acredita.',
  },

  // =========================================================================
  // PILAR 8: ESTRATEGIA_SISTEMAS — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Maquiaveli + Jogo; Sun Tzu + Sistemas
  // =========================================================================
  {
    id: 'machiavelli_29_estrategia_jogo_teoria',
    trackId: 'ESTRATEGIA_SISTEMAS',
    trackTitle: 'Estratégia e Sistemas: Maquiaveli, Sun Tzu & Jogos',
    masteryTier: 4,
    title: 'Estratégia em Jogos de Vida Real: Maquiaveli e Teoria dos Jogos',
    subtitle: 'Saber quando cooperar e quando competir',
    mentorName: 'Nicolau Maquiaveli (O Príncipe, 1513) / Von Neumann & Morgenstern (1944)',
    scientificSource:
      'Maquiaveli (1513); Von Neumann & Morgenstern (Theory of Games and Economic Behavior, 1944); Nash (1950 — equilíbrio de Nash)',
    readTimeSec: 80,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Maquiaveli ensina que o príncipe deve saber quando ser leão (força) e quando ser raposa (astúcia). A teoria dos jogos formaliza isso: em algumas situações, cooperação é a melhor estratégia; em outras, competição. Saber distinguir é a chave do pensamento estratégico.',
    whyItWorksMechanism:
    'Von Neumann e Morgenstern (1944) fundaram a teoria dos jogos. Nash (1950) mostrou o equilíbrio de Nash — situação onde nenhum jogador pode melhorar mudando unilateralmente. Axelrod (1984) mostrou cooperação como estratégia estável em jogos repetidos.',
    zeroStepExample:
    'Em uma situação competitiva hoje, pergunte: \"Cooperar ou competir aqui gera melhor resultado a longo prazo?\"',
    practicalActionToday:
    'Identifique uma situação de conflito hoje e avalie se cooperação ou competição é mais vantajosa.',
    fieldMission:
    'Por 7 dias, registre situações de conflito e avalie cooperação vs competição.',
    dilemmaPrompt:
    'Você está em uma competição onde só um pode vencer. Estratégia significa competir a todo custo, ou significa reconhecer quando cooperação (mesmo com competidores) beneficia ambos?',
    dilemmaOptions: [
      'Competir a todo custo, mesmo que prejudique o outro.',
      'Cooperar sempre, mesmo que o outro explore.',
      'Avaliar quando cooperação beneficia ambos a longo prazo.',
      'Desistir da competição.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Pensamento estratégico: avaliar cooperação vs competição por contexto.',
    feedbackTrap:
    'Competição cega destrói valor; cooperação cega convida exploração.',
  },
  {
    id: 'machiavelli_30_pensamento_sistemas_sun_tzu',
    trackId: 'ESTRATEGIA_SISTEMAS',
    trackTitle: 'Estratégia e Sistemas: Maquiaveli, Sun Tzu & Jogos',
    masteryTier: 4,
    title: 'Pensamento Sistêmico: Sun Tzu e a Interconexão de Tudo',
    subtitle: 'Entender o sistema inteiro, não apenas a parte visível',
    mentorName: 'Sun Tzu (A Arte da Guerra, século VI a.C.) / Senge (1990)',
    scientificSource:
      'Sun Tzu (século VI a.C.); Senge (The Fifth Discipline, 1990 — pensamento sistêmico); Meadows (2008 — Thinking in Systems)',
    readTimeSec: 75,
    recommendedZone: 'VERDE',
    coreEssence:
    'Sun Tzu ensina que conhecer o terreno é essencial para vencer. O pensamento sistêmico moderno (Senge, Meadows) expande isso: entender não apenas o terreno, mas todo o sistema — suas interconexões, feedback loops e consequências não intencionais.',
    whyItWorksMechanism:
    'Senge (1990) desenvolveu o pensamento sistêmico como disciplina para entender complexidade. Meadows (2008) mostra que sistemas têm propriedades emergentes que não podem ser entendidas analisando partes isoladamente.',
    zeroStepExample:
    'Ao enfrentar um problema hoje, pergunte: \"Quais são as consequências não intencionais da minha solução proposta?\"',
    practicalActionToday:
    'Escolha um problema e mapeie pelo menos 3 conexões entre ele e outras áreas da sua vida.',
    fieldMission:
    'Por 5 dias, analise problemas pensando em consequências de segundo e terceiro nível.',
    dilemmaPrompt:
    'Você quer resolver um problema rapidamente. Pensamento sistêmico significa aplicar a solução mais óbvia, ou significa considerar como essa solução afeta todo o sistema ao redor?',
    dilemmaOptions: [
      'Aplicar a solução mais óbvia sem considerar consequências.',
      'Não agir por medo de consequências.',
      'Considerar consequências de segundo e terceiro nível antes de agir.',
      'Delegar a decisão para alguém else.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Pensamento sistêmico: ver interconexões e consequências não intencionais.',
    feedbackTrap:
    'Soluções rápidas ignoram complexidade e criam novos problemas.',
  },

  // =========================================================================
  // PILAR 9: ANTIVIES_DECISAO — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Tetlock + Previsão; Confirmação + Ciência
  // =========================================================================
  {
    id: 'tetlock_29_previsao_ciencia_atualizacao',
    trackId: 'ANTIVIES_DECISAO',
    trackTitle: 'Antivieses e Tomada de Decisão: Tetlock, Kahneman & Taleb',
    masteryTier: 4,
    title: 'Superprevisão na Ciência: Atualizar Crenças com Novas Evidências',
    subtitle: 'Cientistas bons são superprevisores de si mesmos',
    mentorName: 'Philip Tetlock (2015) / Kuhn (1962 — revoluções científicas)',
    scientificSource:
      'Tetlock (Superforecasting, 2015); Kuhn (The Structure of Scientific Revolutions, 1962); Popper (1934 — falsificabilidade)',
    readTimeSec: 80,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Superprevisores não têm bola de cristal — eles atualizam crenças com mais frequência e precisão. Na ciência, isso significa estar disposto a abandonar uma teoria quando as evidências mudam. Kuhn mostrou que revoluções científicas acontecem quando o paradigma dominante não explica mais os dados.',
    whyItWorksMechanism:
    'Tetlock (2015) mostra que superprevisores atualizam crenças incrementalmente e frequentemente. Kuhn (1962) mostra que ciência avança através de mudanças de paradigma quando evidências acumuladas contradizem a teoria vigente.',
    zeroStepExample:
    'Hoje, pegue uma crença científica ou de saúde que você tem e pergunte: \"Que evidência faria eu mudar de ideia?\"',
    practicalActionToday:
    'Escolha uma crença e escreva quais evidências específicas a fariam mudar.',
    fieldMission:
    'Por 14 dias, registre opiniões e atualize-as com novas informações.',
    dilemmaPrompt:
    'Novas evidências científicas contradizem algo que você acredita. Superprevisão significa ignorar as evidências, ou significa atualizar sua crença proporcionalmente?',
    dilemmaOptions: [
      'Ignorar evidências e manter a crença original.',
      'Mudar completamente a crença a cada novo estudo.',
      'Atualizar a crença proporcionalmente à força das evidências.',
      'Não ter crenças sobre ciência.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Superprevisão científica é atualizar crenças com evidência.',
    feedbackTrap:
    'Ignorar evidências científicas é negação, não lealdade.',
  },
  {
    id: 'tetlock_30_viés_confirmação_pesquisa',
    trackId: 'ANTIVIES_DECISAO',
    trackTitle: 'Antivieses e Tomada de Decisão: Tetlock, Kahneman & Taleb',
    masteryTier: 4,
    title: 'Viés de Confirmação na Pesquisa: Buscar Evidência Contrária',
    subtitle: 'A ciência avança procurando o que está errado, não o que está certo',
    mentorName: 'Popper (1934) / Wason (1960)',
    scientificSource:
      'Popper (A Lógica da Descoberta Científica, 1934); Wason (Quarterly Journal of Experimental Psychology, 1960 — tarefa de seleção); Tetlock (2015)',
    readTimeSec: 75,
    recommendedZone: 'AMARELO',
    coreEssence:
    'O viés de confirmação faz você buscar apenas informações que confirmam o que já acredita. Na ciência, isso é fatal: você deve buscar ativamente evidências que contradigam sua hipótese. Se você só procura confirmação, você nunca aprenderá nada novo.',
    whyItWorksMechanism:
    'Wason (1960) mostrou que pessoas tendem a buscar confirmação em vez de falsificação. Popper (1934) estabeleceu que ciência avança tentando refutar, não confirmar. Tetlock (2015) mostra que superprevisores buscam ativamente evidências contrárias.',
    zeroStepExample:
    'Hoje, pegue uma opinião forte que você tem e escreva o melhor argumento possível contra ela.',
    practicalActionToday:
    'Em uma discussão hoje, resuma a posição do outro tão bem que ele diga: \"Você entendeu melhor do que eu mesmo.\"',
    fieldMission:
    'Por 7 dias, pratique buscar evidências contrárias em todas as opiniões fortes.',
    dilemmaPrompt:
    'Você discorda fortemente de alguém. Viés de confirmação significa buscar apenas provas que você está certo, ou significa apresentar a versão mais forte do argumento oposto?',
    dilemmaOptions: [
      'Buscar apenas provas que confirmam sua opinião.',
      'Concordar com o outro para evitar conflito.',
      'Apresentar a versão mais forte do argumento oposto antes de responder.',
      'Ignorar o argumento do outro completamente.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Buscar evidência contrária é a base do pensamento científico.',
    feedbackTrap:
    'Derrotar um argumento fraco prova nada.',
  },

  // =========================================================================
  // PILAR 10: CORPO_LONGEVIDADE — Volume IV (Lic. 29-30, Grau IV)
  // Sintese: Paluch + Movimento; Isométrico + Pressão
  // =========================================================================
  {
    id: 'paluch_29_movimento_longevidade_sistemico',
    trackId: 'CORPO_LONGEVIDADE',
    trackTitle: 'Corpo e Longevidade: Exercício, Sono & Hábitos de Saúde',
    masteryTier: 4,
    title: 'Movimento Sistêmico: Como Exercício Afeta Todo o Corpo',
    subtitle: 'Não é apenas músculos — é cérebro, coração e metabolismo',
    mentorName: 'Paluch et al. (2022) / Ratey (2008)',
    scientificSource:
      'Paluch et al. (The Lancet Public Health, 2022, N=47,471 — passos e mortalidade); Ratey (Spark, 2008 — exercício e cérebro); Edwards et al. (2023 — isométrico e pressão arterial)',
    readTimeSec: 80,
    recommendedZone: 'QUALQUER',
    coreEssence:
    'Exercício não é apenas para músculos. Paluch et al. (2022) mostram que passos diários reduzem mortalidade por todas as causas. Ratey (2008) mostra que exercício melhora diretamente função cerebral. O corpo é um sistema — exercício em uma parte beneficia todo o sistema.',
    whyItWorksMechanism:
    'Paluch et al. (2022) analisaram 47,471 pessoas mostrando benefício de mortalidade com passos diários até ponto de platô. Ratey (2008) demonstra que exercício aumenta BDNF (fator neurotrófico) e melhora cognição.',
    zeroStepExample:
    'Hoje, adicione 10 minutos de movimento ao seu dia, mesmo que seja apenas caminhar dentro de casa.',
    practicalActionToday:
    'Defina uma meta de passos diários realista baseada no seu nível atual, não em um número arbitrário.',
    fieldMission:
    'Por 2 semanas, aumente gradualmente seus passos diários até atingir uma meta sustentável.',
    dilemmaPrompt:
    'Você quer melhorar sua saúde. Movimento sistêmico significa focar apenas em um tipo de exercício, ou significa reconhecer que qualquer movimento beneficia todo o sistema corporal?',
    dilemmaOptions: [
      'Focar apenas em musculação.',
      'Não fazer nada porque não pode fazer tudo.',
      'Reconhecer que qualquer movimento beneficia o sistema todo.',
      'Fazer exercício intenso todos os dias sem descanso.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Qualquer movimento beneficia o sistema corporal inteiro.',
    feedbackTrap:
    'Focar em um tipo de exercício ignora a interconexão do corpo.',
  },
  {
    id: 'paluch_30_isometrico_saude_cardiovascular_sistemica',
    trackId: 'CORPO_LONGEVIDADE',
    trackTitle: 'Corpo e Longevidade: Exercício, Sono & Hábitos de Saúde',
    masteryTier: 4,
    title: 'Exercício Isométrico e Saúde Cardiovascular Sistêmica',
    subtitle: 'Contração sem movimento, benefício para todo o corpo',
    mentorName: 'Edwards et al. (2023) / Cornelissen & Smart (2013)',
    scientificSource:
      'Edwards et al. (British Journal of Sports Medicine, 2023, 270 RCTs, N=15,827); Cornelissen & Smart (JAHA, 2013 — exercício e pressão arterial)',
    readTimeSec: 75,
    recommendedZone: 'AMARELO',
    coreEssence:
    'Exercício isométrico (contração muscular sem movimento articular) produz a maior redução de pressão arterial entre todos os tipos de exercício — quase o dobro do aeróbico tradicional. Isso não é apenas sobre músculos; é sobre saúde cardiovascular sistêmica.',
    whyItWorksMechanism:
    'Edwards et al. (2023) analisaram 270 RCTs com 15,827 participantes. Exercício isométrico reduziu pressão arterial em -8.24/-4.00 mmHg. Cornelissen e Smart (2013) mostram benefícios cardiovasculares do exercício resistido.',
    zeroStepExample:
    'Hoje, faça uma prancha de joelhos por 20-30 segundos, respirando normalmente.',
    practicalActionToday:
    'Adicione 2 séries de prancha isométrica ou agachamento estático na parede ao seu dia.',
    fieldMission:
    'Por 2 semanas, faça exercício isométrico 3 vezes por semana.',
    dilemmaPrompt:
    'Você quer reduzir pressão arterial. Exercício isométrico significa ficar parado sem fazer nada, ou significa contração muscular sustentada sem movimento articular?',
    dilemmaOptions: [
      'Ficar completamente parado sem fazer exercício.',
      'Apenas exercício aeróbico intenso.',
      'Contração muscular sustentada sem movimento (prancha, agachamento na parede).',
      'Apenas alongamento passivo.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
    'Isométrico é contração sem movimento, poderoso para pressão arterial.',
    feedbackTrap:
    'Ficar parado sem engajar o músculo não é exercício isométrico.',
  },
];

export const VOLUME_4_TIER_MAP: Record<string, MasteryTier> = Object.fromEntries(
  TEACHINGS_VOLUME_4.map((lesson) => [lesson.id, lesson.masteryTier ?? 1]),
) as Record<string, MasteryTier>;
