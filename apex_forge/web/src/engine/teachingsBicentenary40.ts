import { MasteryTier, TeachingLesson } from './types';

/**
 * VOLUME II DO CODICE POLIMATA — EDICAO DO BICENTENARIO (v14.0.0)
 * 40 Licoes Ineditas (4 por Pilar x 10 Pilares, Graus I a IV = +10 por Grau),
 * elevando a Academia de 160 para 200 Licoes Simetricas (50/50/50/50).
 */
export const TEACHINGS_BICENTENARY_40: TeachingLesson[] = [
  // =========================================================================
  // PILAR 1: ENSINAMENTOS DE JESUS CRISTO (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'cristo_17_jugo_suave_descanso_alma',
    trackId: 'CRISTO_EVANGELHOS',
    trackTitle: 'Ensinamentos de Jesus Cristo: A Rocha, Perdão & Serviço',
    masteryTier: 1,
    title: 'O Jugo Suave de Cristo vs. O Fardo Esmagador da Vaidade',
    subtitle: 'Trabalhar duro em paz interior em vez de se destruir por aprovação',
    mentorName: 'Jesus Cristo (Mateus 11:28–30)',
    scientificSource:
      'Mateus 11:28–30; Maslach & Leiter (World Psychiatry, 2016 — Burnout e conflito de valores); Ryan & Deci (Self-Determination Theory, 2017)',
    readTimeSec: 65,
    recommendedZone: 'VERMELHO',
    coreEssence:
      'Jesus convida os exaustos: "Vinde a mim, todos os que estais cansados e oprimidos, e eu vos aliviarei. Tomai sobre vós o meu jugo e aprendei de mim, que sou manso e humilde de coração, e encontrareis descanso para a vossa alma" (Mateus 11:28–29). Note que Cristo não oferece preguiça nem ausência de jugo — o jugo é uma canga de madeira talhada sob medida para puxar arado em dupla! O que esmaga o ser humano não é o trabalho honesto com propósito, mas o fardo da soberba, da culpa e de tentar provar valor próprio sozinho.',
    whyItWorksMechanism:
      'A pesquisa clínica sobre esgotamento (Maslach & Leiter, World Psychiatry, 2016) demonstra que o burnout severo não nasce apenas de horas trabalhadas, mas de atrito crônico de valores, isolamento e insegurança de ego. Quando a mente descansa em humildade e sentido transcendente (SDT, Ryan & Deci, 2017), o sistema nervoso sai da hipervigilância defensiva e sustenta esforço por décadas.',
    zeroStepExample:
      'Sentindo-se esmagado hoje por querer resolver a vida inteira num único dia? Pare 60 segundos, solte os ombros, entregue a ansiedade de "provar algo aos outros" e cumpra apenas o dever simples de hoje em paz.',
    practicalActionToday:
      'Separe o "peso real da tarefa" do "peso imaginário do orgulho": execute sua obrigação com mansidão e constância, sem dramatizar nem se chicotear.',
    fieldMission:
      'Antes de dormir hoje, escreva 1 cobrança de vaidade/comparação que você vai depor no chão para carregar apenas o dever real de amanhã.',
    dilemmaPrompt:
      'Um jovem iniciante tenta mudar de vida movido por raiva de si mesmo e obsessão de humilhar quem duvidou dele, mas trava exausto em duas semanas. O que Mateus 11:28–30 e a ciência do burnout revelam?',
    dilemmaOptions: [
      'O jugo da vaidade e da autocondenação drena o sistema nervoso; a constância verdadeira nasce da mansidão e humildade de coração — trabalhar firme em paz interior, sem precisar provar superioridade.',
      'A única solução para o cansaço mental é abandonar todas as responsabilidades da vida.',
      'Ódio próprio e comparação constante são os combustíveis mais saudáveis no longo prazo.',
      'Descanso da alma significa nunca aprender nada exigente.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Sabedoria libertadora! O jugo com Cristo não elimina o cultivo da terra, mas retira o desespero do orgulho ferido e devolve paz à alma enquanto você trabalha.',
    feedbackTrap:
      'Tentar puxar o arado da vida movido por vaidade e angústia quebra qualquer ser humano; humildade gera vigor duradouro.',
  },
  {
    id: 'cristo_18_viuva_pobre_duas_moedas',
    trackId: 'CRISTO_EVANGELHOS',
    trackTitle: 'Ensinamentos de Jesus Cristo: A Rocha, Perdão & Serviço',
    masteryTier: 2,
    title: 'As Duas Moedas da Viúva Pobre: Proporção de Entrega vs. Exibição de Sobra',
    subtitle: 'Deus e a realidade medem o peso da entrega pela inteireza do coração, não pelo volume de vitrine',
    mentorName: 'Jesus Cristo (Marcos 12:41–44 • Lucas 21:1–4)',
    scientificSource:
      'Marcos 12:41–44; Dunn, Aknin & Norton (Science, 2008 — Spending Money on Others Promotes Happiness); Aknin et al. (JPSP, 2013 — Estudo em 136 países)',
    readTimeSec: 65,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Assentado diante da arca do tesouro, Jesus observa ricos lançando grandes quantias do que lhes sobrava, até que uma viúva pobre deposita duas pequeninas moedas (*lepta*). Cristo chama os discípulos e inverte toda a contabilidade das aparências: "Em verdade vos digo que esta pobre viúva lançou mais do que todos... porque todos deram do que lhes sobejava, mas esta, da sua pobreza, lançou tudo o que tinha" (Marcos 12:43–44). Nunca despreze seu começo pequeno quando a entrega é inteira!',
    whyItWorksMechanism:
      'Elizabeth Dunn, Lara Aknin e Michael Norton publicaram na revista Science (2008) e em 136 países (JPSP, 2013) que a generosidade proporcional — mesmo em quantias modestas ou tempo dedicado a ajudar alguém quando se tem pouco — ativa circuitos de recompensa intrínseca e bem-estar duradouro, libertando a mente da mentalidade de escassez e inveja.',
    zeroStepExample:
      'Ainda tem poucos recursos financeiros ou técnicos hoje? Não espere "ficar rico um dia" para ser generoso e íntegro: ofereça hoje seus 15 minutos, sua atenção leal ou seu auxílio honesto com inteireza total.',
    practicalActionToday:
      'Pare de comparar o tamanho bruto do seu resultado atual com o de quem já está no ano 10; meça a sinceridade proporcional do esforço que você entregou hoje.',
    fieldMission:
      'Pratique hoje 1 gesto concreto de generosidade proporcional (de tempo, ajuda prática ou recurso) sem alarde, vencendo a mentalidade de avareza.',
    dilemmaPrompt:
      'Um iniciante pensa: "Como hoje tenho pouco dinheiro e pouco conhecimento, não vale a pena ajudar ninguém nem dar meu máximo até eu ser grande". O que Marcos 12:41–44 e Dunn et al. (Science, 2008) ensinam?',
    dilemmaOptions: [
      'Apenas grandes fortunas exibidas em público têm valor moral ou impacto real.',
      'A grandeza real está na proporção e inteireza da entrega onde você está hoje; esperar "sobrar" para agir com excelência e generosidade apenas treina o hábito da omissão.',
      'Quem começa pequeno deve esconder qualquer esforço até ficar famoso.',
      'Generosidade proporcional empobrece a mente e aumenta a ansiedade.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Olhar do Mestre! Duas pequenas moedas entregues com alma inteira pesam mais na balança eterna do que sobras lançadas por vaidade.',
    feedbackTrap:
      'Quem não entrega o melhor com o pouco que tem hoje também só entregará sobras frias se um dia tiver muito.',
  },
  {
    id: 'cristo_19_dez_virgens_azeite_reserva',
    trackId: 'CRISTO_EVANGELHOS',
    trackTitle: 'Ensinamentos de Jesus Cristo: A Rocha, Perdão & Serviço',
    masteryTier: 3,
    title: 'As Dez Virgens & O Azeite na Vasilha: O Preparo Que Ninguém Pode Emprestar',
    subtitle: 'Caráter, saúde e competência real não podem ser transferidos por pix à meia-noite',
    mentorName: 'Jesus Cristo (Mateus 25:1–13)',
    scientificSource:
      'Mateus 25:1–13; Ericsson, Krampe & Tesch-Römer (Psychological Review, 1993 — Acúmulo intransferível de prática deliberada)',
    readTimeSec: 70,
    recommendedZone: 'AMARELO',
    coreEssence:
      'Na Parábola das Dez Virgens (Mateus 25:1–13), todas as dez tinham lâmpadas bonitas por fora e esperavam o mesmo esposo — mas cinco eram néscias (levaram só a lâmpada vazia de reserva) e cinco eram prudentes (levaram azeite extra nas vasilhas). À meia-noite soou o grito, e as despreparadas imploraram: "Dai-nos do vosso azeite!". A resposta das prudentes revela uma lei implacável da realidade: **existem reservas interiores que ninguém consegue dividir nem emprestar na hora da crise!**',
    whyItWorksMechanism:
      'A ciência da perícia (Ericsson et al., Psychological Review, 1993) mostra que mielinização neural, condicionamento cardiovascular, paz moral e domínio técnico são adaptações biológicas acumuladas gota a gota ao longo de meses. Quando a oportunidade única ou a emergência bate à porta à meia-noite, aparência externa ("a lâmpada bonita") apaga em segundos sem o azeite oculto do preparo prévio.',
    zeroStepExample:
      'Deposite hoje "1 colher de azeite" na sua vasilha invisível: 20 minutos de estudo real, sono digno ou reserva guardada quando ainda não há nenhuma emergência gritando.',
    practicalActionToday:
      'Pergunte-se com brutal honestidade: "Estou polindo apenas a lâmpada por fora ou estou enchendo a vasilha de competência e caráter por dentro?".',
    fieldMission:
      'Acumule hoje preparo real em 1 habilidade crítica para que, quando a porta abrir de surpresa, você já esteja pronto.',
    dilemmaPrompt:
      'Dois jovens querem a mesma oportunidade rara. Um cuida apenas do currículo estético esperando estudar "só se for chamado"; o outro acumula competência diária silenciosa meses antes. Quando o chamado surge para o dia seguinte, o que Mateus 25:1–13 ensina?',
    dilemmaOptions: [
      'Competência profunda e caráter podem ser emprestados de um amigo em 10 minutos na véspera.',
      'Ter uma lâmpada bonita por fora dispensa qualquer combustível interno.',
      'À meia-noite da oportunidade ou da crise não há tempo de comprar preparo atrasado: só entra pela porta quem acumulou azeite real na vasilha durante os dias comuns.',
      'Preparar-se com antecedência é desperdício porque imprevistos nunca acontecem.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Prudência vigilante! Ninguém pode emprestar condicionamento, sabedoria ou comunhão na hora H — encha sua vasilha hoje.',
    feedbackTrap:
      'Deixar para buscar azeite depois que o clamor da meia-noite já soou encontra sempre a porta fechada.',
  },
  {
    id: 'cristo_20_toalha_bacia_identidade_segura',
    trackId: 'CRISTO_EVANGELHOS',
    trackTitle: 'Ensinamentos de Jesus Cristo: A Rocha, Perdão & Serviço',
    masteryTier: 4,
    title: 'A Toalha e a Bacia (João 13): Só Quem Sabe Quem É Consegue Servir Sem Medo',
    subtitle: 'A arrogância nasce da insegurança; a verdadeira autoridade curva-se para elevar os seus',
    mentorName: 'Jesus Cristo (João 13:1–17)',
    scientificSource:
      'João 13:3–5, 12–17; Owens, Johnson & Mitchell (Organization Science, 2013 — Expressed Humility in Organizations); Ou et al. (ASQ, 2014 — Humildade de CEOs)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Repare na engrenagem psicológica extraordinária registrada pelo apóstolo João na última ceia: **"Sabendo Jesus que o Pai tinha depositado nas suas mãos todas as coisas, e que havia saído de Deus e ia para Deus, levantou-se da ceia, tirou as vestes e, tomando uma toalha, cingiu-se... e começou a lavar os pés aos discípulos"** (João 13:3–5). Enquanto os discípulos inseguros brigavam para ver quem parecia maior, Aquele que detinha toda a autoridade tomou a toalha do servo!',
    whyItWorksMechanism:
      'Bradley Owens et al. (Organization Science, 2013) e Amy Ou et al. (Administrative Science Quarterly, 2014) provaram em dezenas de organizações que líderes inseguros usam arrogância e distância para esconder fragilidade, travando o aprendizado da equipe; já líderes com identidade interior sólida praticam Humildade Expressa — ouvem, ensinam pelo exemplo e destravam o máximo engajamento e desempenho coletivo.',
    zeroStepExample:
      'Hoje, faça voluntariamente uma tarefa simples e necessária em casa ou no trabalho (limpar, organizar, destravar um iniciante) sem achar que "isso está abaixo de mim".',
    practicalActionToday:
      'Substitua qualquer disputa de vaidade hoje pela postura de João 13:3–5: identidade tranquila que lidera pelo exemplo concreto de serviço.',
    fieldMission:
      'Eleve o padrão de um ambiente hoje arregaçando as mangas primeiro naquilo que todos estavam empurrando para o outro.',
    dilemmaPrompt:
      'Em uma equipe, um líder recém-promovido recusa ajudar em tarefas práticas achando que perderá respeito se "pegar na massa". O que João 13:3–15 e Owens et al. (Organization Science, 2013) revelam?',
    dilemmaOptions: [
      'Recusar tarefas simples realmente prova força interior inabalável.',
      'A necessidade de parecer intocável denuncia insegurança de ego; quem tem identidade firme não teme tomar a toalha pelo exemplo, conquistando autoridade moral genuína e alta coesão na equipe.',
      'Liderar significa humilhar subordinados para manter distância.',
      'Humildade em liderança reduz a qualidade técnica das entregas.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Autoridade suprema! Só quem sabe perfeitamente quem é não precisa de pedestal artificial para liderar.',
    feedbackTrap:
      'Arrogância é armadura de papelão de quem tem medo de parecer pequeno; a verdadeira grandeza edifica pelo exemplo.',
  },

  // =========================================================================
  // PILAR 2: SABEDORIA DA BIBLIA (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'biblia_17_guardar_coracao_fontes_vida',
    trackId: 'SABEDORIA_BIBLICA',
    trackTitle: 'Sabedoria da Bíblia: Provérbios, Domínio Próprio & Metanoia',
    masteryTier: 1,
    title: 'Guarda o Teu Coração: Controle das Portas de Entrada da Mente',
    subtitle: 'O que você alimenta pelos olhos e ouvidos governa suas decisões amanhã',
    mentorName: 'Rei Salomão (Provérbios 4:23–27)',
    scientificSource:
      'Provérbios 4:23–27; Miyake et al. (Cognitive Psychology, 2000 — Inibição Executiva); Bargh & Morsella (Priming ambiental e atenção)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Provérbios 4:23 ordena com precisão estratégica: "Sobre tudo o que se deve guardar, guarda o teu coração, porque dele procedem as fontes da vida... Os teus olhos olhem direitos, e as tuas pálpebras olhem diretamente diante de ti. Pondera a vereda de teus pés". No hebraico bíblico, "coração" (*lev*) abrange mente, vontade, atenção e afeições. Quem deixa as portas da atenção escancaradas ao lixo digital, inveja e dispersão contamina a nascente inteira.',
    whyItWorksMechanism:
      'O modelo clássico das funções executivas de Miyake et al. (Cognitive Psychology, 2000) demonstra que o Controle Inibitório começa no filtro perceptual: cada estímulo hiperdopaminérgico ou hostil admitido consome memória de trabalho por resíduo atencional. Proteger a "nascente" na entrada custa 10 vezes menos energia do que lutar contra impulsos depois que já invadiram a mente.',
    zeroStepExample:
      'Nos primeiros 30 minutos após acordar hoje, não entregue seus olhos a feeds caóticos: beba água, respire na luz natural e leia 1 princípio construtivo.',
    practicalActionToday:
      'Feche 1 "porta de contaminação" do seu celular hoje (silencie notificações inúteis ou remova 1 gatilho que rouba sua paz e foco).',
    fieldMission:
      'Proteja a primeira e a última meia hora do seu dia hoje contra consumo reativo de tela, guardando a fonte da sua atenção.',
    dilemmaPrompt:
      'Um estudante consome 2 horas de vídeos curtos agitados, brigas e fofocas antes de estudar, e depois reclama que "não nasceu com boa concentração". O que Provérbios 4:23–25 e a neurociência executiva apontam?',
    dilemmaOptions: [
      'O que você assiste antes de estudar não deixa nenhum resíduo na memória de trabalho.',
      'Apenas genética explica a falta de foco após horas de hiperestimulação.',
      'Faltou guardar as portas da mente: poluir a atenção logo cedo sobrecarrega o controle inibitório e turva as fontes das quais brotam foco e decisão.',
      'Assistir vídeos agitados descansa o córtex pré-frontal.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Vigilância na nascente! Quem guarda o que entra pelos olhos e ouvidos preserva clareza limpa para o que realmente importa.',
    feedbackTrap:
      'Não existe foco limpo brotando de uma fonte voluntariamente poluída a cada manhã; guarde as portas de entrada.',
  },
  {
    id: 'biblia_18_jetro_moises_delegacao_sustentavel',
    trackId: 'SABEDORIA_BIBLICA',
    trackTitle: 'Sabedoria da Bíblia: Provérbios, Domínio Próprio & Metanoia',
    masteryTier: 2,
    title: 'O Conselho de Jetro a Moisés (Êxodo 18): Centralizar Tudo É Caminho de Colapso',
    subtitle: '"Não é bom o que fazes; totalmente desfalecerás, assim tu como este povo"',
    mentorName: 'Jetro & Moisés (Êxodo 18:13–24)',
    scientificSource:
      'Êxodo 18:13–24; Hackman (Leading Teams: Setting the Stage for Great Performances, Harvard, 2002); Yukl & Fu (Leadership Quarterly, 1999 — Delegação eficaz)',
    readTimeSec: 65,
    recommendedZone: 'AMARELO',
    coreEssence:
      'Moisés atendia o povo sozinho desde a manhã até o pôr do sol enquanto uma fila gigante se desgastava esperando. Seu sogro Jetro observou a cena e deu a primeira aula documentada de arquitetura de gestão da história: **"Não é bom o que fazes. Totalmente desfalecerás, assim tu como este povo... isto é pesado demais para ti; tu só não o podes fazer"** (Êxodo 18:17–18). A solução de Jetro: (1) Ensinar princípios claros a todos; (2) Formar líderes capazes, tementes a Deus, íntegros e inimigos da avareza; (3) Reservar a si apenas as causas graves!',
    whyItWorksMechanism:
      'J. Richard Hackman (Harvard, 2002) e Yukl & Fu (1999) comprovaram que líderes centralizadores ("só fica bom se eu fizer tudo") criam dois desastres simultâneos: esgotam a si mesmos e infantilizam a equipe/família! Delegar com critérios claros de caráter + regras explícitas liberta sua mente estratégica e desenvolve autonomia real nas pessoas ao redor.',
    zeroStepExample:
      'Está tentando carregar sozinho tarefas domésticas, familiares ou de equipe que outros já têm idade e capacidade para assumir? Ensine o padrão uma vez com paciência e compartilhe a responsabilidade.',
    practicalActionToday:
      'Identifique 1 tarefa recorrente que você centraliza por mania de controle e estruture uma regra simples para dividi-la ou automatizá-la.',
    fieldMission:
      'Aplique a Tríade de Jetro hoje: explique o critério claro (por que e como fazer), confie a execução proporcional e guarde sua energia nobre para o gargalo principal.',
    dilemmaPrompt:
      'Um gestor ou chefe de família trabalha 15 horas por dia refazendo tudo sozinho, vive irritado e ninguém ao redor aprende a resolver nada. Qual é o diagnóstico exato de Jetro em Êxodo 18:17–22?',
    dilemmaOptions: [
      'Centralizar 100% das decisões pequenas é prova admirável de heroísmo.',
      'Recusar estruturar regras claras e formar pessoas confiáveis condena tanto o líder quanto o grupo à exaustão ("desfalecerás tu e o povo"); liderar exige ensinar princípios e distribuir carga por escalão.',
      'Delegar significa jogar tarefas sem nenhum critério para pessoas desonestas.',
      'A única saída é dormir menos para continuar atendendo a fila inteira sozinho.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Sabedoria milenar de gestão! Carregar o mundo nas costas sem ensinar nem estruturar não é virtude — é gargalo que sufoca a todos.',
    feedbackTrap:
      'Heroísmo centralizador quebra o líder e paralisa a equipe; ensine a lei clara e forme pessoas íntegras.',
  },
  {
    id: 'biblia_19_habacuque_alegria_figueira_seca',
    trackId: 'SABEDORIA_BIBLICA',
    trackTitle: 'Sabedoria da Bíblia: Provérbios, Domínio Próprio & Metanoia',
    masteryTier: 3,
    title: 'A Fé da Figueira Seca (Habacuque 3): Constância Quando o Resultado Atrasa',
    subtitle: 'Permaneça inabalável mesmo na estação em que o curral e os campos parecem vazios',
    mentorName: 'Profeta Habacuque (Habacuque 3:17–19)',
    scientificSource:
      'Habacuque 3:17–19; Frankl (Em Busca de Sentido, 1946); Park (Psychological Bulletin, 2010 — Making Meaning in Stressful Life Events)',
    readTimeSec: 65,
    recommendedZone: 'VERMELHO',
    coreEssence:
      'Qualquer pessoa sorri e mantém a disciplina na semana em que tudo dá certo, o dinheiro entra e os elogios chovem. O teste real de estatura espiritual e mental está em Habacuque 3:17–18: **"Porquanto, ainda que a figueira não floresça, nem haja fruto na vide; o produto da oliveira minta, e os campos não produzam mantimento... todavia, eu me alegrarei no Senhor!"**. Na economia antiga, perder figo, uva, azeite, trigo e rebanho era colapso total — e mesmo ali o profeta ancora sua paz acima das circunstâncias!',
    whyItWorksMechanism:
      'Viktor Frankl observou nos campos de concentração e Crystal Park revisou em Psychological Bulletin (2010) que indivíduos cujo sentido de vida depende exclusivamente de recompensas externas imediatas colapsam na primeira seca prolongada; já quem possui **Sentido Global Incondicional** mantém agência moral, dignidade e constância atravessando qualquer inverno até a próxima colheita.',
    zeroStepExample:
      'Está atravessando um mês "seco" em que você estuda, trabalha direito e o fruto visível ainda não apareceu? Proíba a murmuração hoje: cumpra seu dever com dignidade serena.',
    practicalActionToday:
      'Desacople hoje sua fidelidade aos princípios do placar de curto prazo: faça o que é reto porque é reto, com ou sem aplauso imediato.',
    fieldMission:
      'Em meio a 1 frustração ou demora atual, substitua a reclamação por gratidão firme pelo que permanece inabalável.',
    dilemmaPrompt:
      'Um jovem dedica-se honestamente por 4 semanas, mas enfrenta um imprevisto externo e pensa: "Já que não colhi rápido, vou chutar o balde e largar minha disciplina". O que Habacuque 3:17–19 e Park (2010) ensinam?',
    dilemmaOptions: [
      'Fidelidade que só dura enquanto há recompensa imediata é contrato frágil; ancorar seu propósito e alegria numa rocha acima da estação seca preserva seus pés firmes até a colheita chegar.',
      'Realmente só vale a pena ter caráter nos meses de fartura fácil.',
      'Chutar o balde na crise acelera a recuperação dos resultados.',
      'Invernos e atrasos nunca acontecem na vida de pessoas competentes.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Pés como os da corça nos lugares altos! Quem não vende seus princípios na seca reina quando a chuva volta.',
    feedbackTrap:
      'Condicionar seu caráter ao clima favorável da semana torna você refém de qualquer vento contrário.',
  },
  {
    id: 'biblia_20_bereanos_nobreza_verificacao',
    trackId: 'SABEDORIA_BIBLICA',
    trackTitle: 'Sabedoria da Bíblia: Provérbios, Domínio Próprio & Metanoia',
    masteryTier: 4,
    title: 'A Nobreza dos Bereanos (Atos 17): Mente Aberta Com Verificação Diária nas Fontes',
    subtitle: 'Nem credulidade ingênua que engole tudo, nem cinismo fechado que rejeita tudo',
    mentorName: 'Lucas & Paulo (Atos 17:10–12 • 1 Tessalonicenses 5:21)',
    scientificSource:
      'Atos 17:11; 1 Tessalonicenses 5:21; Wineburg & McGrew (Teachers College Record, Stanford, 2019 — Lateral Reading and Fact-Checking)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Em Atos 17:11, Lucas registra um elogio intelectual e espiritual raríssimo aos moradores de Bereia: eles **"foram mais nobres do que os que estavam em Tessalônica, porque de bom grado receberam a palavra, examinando cada dia nas Escrituras se estas coisas eram assim"**! Veja a dupla hélice da nobreza mental: (1) *Receber de bom grado* (humildade aberta para ouvir sem preconceito); (2) *Examinar todos os dias na fonte primária* se aquilo é verdade mesmo ("Examinai tudo. Retende o bem", 1 Ts 5:21)!',
    whyItWorksMechanism:
      'Sam Wineburg e Sarah McGrew (Universidade Stanford, 2019) testaram historiadores PhDs, universitários e verificadores profissionais diante de afirmações persuasivas: quase todos caíam em retórica bonita quando liam apenas o próprio discurso do autor, exceto quem praticava **Verificação Direta na Fonte Primária**! O espírito bereano une abertura receptiva com auditoria rigorosa da verdade.',
    zeroStepExample:
      'Ouviu uma promessa milagrosa de saúde, dinheiro ou doutrina hoje? Não engula por emoção nem xingue no impulso: abra a fonte original e confira se os dados são reais!',
    practicalActionToday:
      'Aplique o filtro bereano de duas etapas a qualquer conselho importante hoje: escute com respeito atento E verifique na fonte primária antes de adotar.',
    fieldMission:
      'Confronte 1 crença repetida "de ouvir dizer" indo ler diretamente o texto ou estudo primário ainda hoje.',
    dilemmaPrompt:
      'Diante de um orador carismático fazendo afirmações fortes, a maioria se divide em dois extremos: os fanáticos que acreditam sem checar nada e os cínicos que fecham os ouvidos sem escutar. Qual é o padrão superior de Atos 17:11 e Stanford (Wineburg & McGrew, 2019)?',
    dilemmaOptions: [
      'Acreditar automaticamente em quem tiver a voz mais confiante e mais seguidores.',
      'Rejeitar qualquer ideia nova em 3 segundos para nunca precisar estudar.',
      'Combinar abertura respeitosa para escutar com exame rigoroso nas fontes primárias para verificar se os fatos realmente procedem, retendo apenas o que é verdadeiro.',
      'Compartilhar informações urgentes primeiro e deixar para checar depois.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Nobreza intelectual e espiritual bereana! Ouvidos abertos sem arrogância, mente afiada conferindo a verdade na fonte.',
    feedbackTrap:
      'Tanto a credulidade cega quanto o cinismo fechado são preguiça mental; examine tudo na fonte e retenha o bem.',
  },

  // =========================================================================
  // PILAR 3: GARRA & AUTODOMINIO (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'garra_17_intencoes_se_entao_gollwitzer',
    trackId: 'GARRA_AUTODOMINIO',
    trackTitle: 'Autogoverno, Regulação Emocional & Garra',
    masteryTier: 1,
    title: 'Protocolo "Se–Então" (Gollwitzer): Programando Reflexos de Ação',
    subtitle: 'Meta vaga perde para o cansaço; gatilho pré-programado dispara no automático',
    mentorName: 'Peter Gollwitzer & David Goggins',
    scientificSource:
      'Gollwitzer & Sheeran (Advances in Experimental Social Psychology, 2006 — Meta-análise de 94 estudos, N = 8.461, d = 0,65)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Dizer "amanhã vou estudar mais e comer melhor" é uma simples intenção de meta — e falha assim que bate o cansaço das 19h. Peter Gollwitzer descobriu a Intenção de Implementação no formato exato **"SE [situação/gatilho X acontecer], ENTÃO [executarei imediatamente a ação específica Y]"**: você delega o disparo da ação a uma pista concreta do ambiente antes da preguiça argumentar!',
    whyItWorksMechanism:
      'Na meta-análise monumental de 94 testes independentes (N = 8.461), Gollwitzer e Sheeran (2006) comprovaram tamanho de efeito médio-alto d = 0,65 no cumprimento de metas e d = 0,77 para blindar a ação contra distrações! Neurologicamente, o plano "Se–Então" cria uma associação direta pista-resposta nos gânglios da base e córtex pré-motor, reduzindo drasticamente o esforço deliberativo na hora H.',
    zeroStepExample:
      'Em vez de "vou treinar hoje", escreva exatamente: "SE eu desligar o computador às 18h00, ENTÃO calçarei o tênis imediatamente e farei os primeiros 5 minutos".',
    practicalActionToday:
      'Crie agora 2 regras "SE [pista exata], ENTÃO [ação imediata]" — uma para iniciar sua tarefa principal e outra para bloquear sua maior distração.',
    fieldMission:
      'Execute hoje pelo menos 1 gatilho "SE–ENTÃO" sem permitir nem 3 segundos de debate mental quando a pista acontecer.',
    dilemmaPrompt:
      'Dois iniciantes querem criar o hábito da leitura diária. O Aluno A promete "Vou tentar ler todo dia". O Aluno B define: "SE eu terminar de escovar os dentes às 21h30, ENTÃO sentarei na cadeira e lerei 4 páginas". Segundo Gollwitzer & Sheeran (94 estudos, d = 0,65), por que B vence?',
    dilemmaOptions: [
      'Porque escovar os dentes melhora magicamente a velocidade ocular.',
      'Porque a estrutura "SE [pista concreta] -> ENTÃO [ação exata]" pré-vincula o gatilho ambiental à resposta motora, disparando a ação sem depender de força de vontade no cansaço.',
      'Porque ler apenas 4 páginas nunca gera hábito nenhum.',
      'Os dois têm exatamente a mesma taxa estatística de sucesso.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Engenharia comportamental exata! Você tira a decisão das mãos do humor das 21h30 e a entrega a um reflexo pré-programado.',
    feedbackTrap:
      'Intenções vagas evaporam sob fadiga; converta toda meta importante em código executável "SE [pista], ENTÃO [ação]".',
  },
  {
    id: 'garra_18_pote_biscoitos_memoria_autobiografica',
    trackId: 'GARRA_AUTODOMINIO',
    trackTitle: 'Autogoverno, Regulação Emocional & Garra',
    masteryTier: 2,
    title: 'O "Pote de Vitórias" Autobiográfico: Resgatando Provas sob Dor',
    subtitle: 'Como memórias reais de superação amortecem o cortisol no meio da tempestade',
    mentorName: 'David Goggins & Mauricio Delgado',
    scientificSource:
      'Speer, Bhanji & Delgado (Neuron, 2014 — Evocação autobiográfica e amortecimento de cortisol); Bandura (1997 — Mastery Experiences)',
    readTimeSec: 65,
    recommendedZone: 'AMARELO',
    coreEssence:
      'Quando a dor aperta no quilômetro 120 ou diante de uma prova assustadora, o cérebro grita que você é fraco. David Goggins criou o "Cookie Jar" (Pote de Biscoitos): um arquivo mental de dias difíceis REAIS em que você tinha tudo para desistir, mas continuou e venceu — mesmo que tenha sido uma vitória humilde! Não é frase vazia de espelho; é prova factual arquivada da sua própria história.',
    whyItWorksMechanism:
      'Speer, Bhanji e Delgado publicaram na revista Neuron (2014) que evocar memórias autobiográficas autênticas ativa circuitos estriatais e pré-frontais (vmPFC) que amortecem significativamente o pico de cortisol diante de um estressor agudo! E Albert Bandura (1997) demonstrou que a fonte nº 1 de autoeficácia é a "Experiência de Domínio" passada — lembrar fatos concretos que você já superou.',
    zeroStepExample:
      'Acha que não tem grandes feitos? Anote 3 momentos simples em que você estava cansado ou com medo, mas cumpriu sua palavra mesmo assim — esse é o seu primeiro estoque real!',
    practicalActionToday:
      'Escreva 3 "provas reais de superação" da sua própria trajetória para consultar sempre que a voz da desistência aparecer.',
    fieldMission:
      'Conquiste hoje 1 vitória difícil proposital (terminar uma série/estudo sem cortar caminho) especificamente para depositar mais 1 ficha real no seu arquivo.',
    dilemmaPrompt:
      'No meio de uma semana pesada, sua mente diz "Eu nunca dou conta de nada". Qual resposta aplica a neurociência de Speer & Delgado (Neuron, 2014) e Bandura?',
    dilemmaOptions: [
      'Repetir frases mágicas desconectadas da realidade fingindo que já é bilionário.',
      'Concordar com o pensamento derrotista e desistir da semana inteira.',
      'Evocar 2 ou 3 memórias autobiográficas concretas de dias difíceis que você JÁ atravessou no passado, reativando o controle pré-frontal e amortecendo a resposta de estresse.',
      'Consumir açúcar e redes sociais para esquecer o problema.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Neurobiologia aplicada na veia! Fatos reais da sua própria superação calam a mentira do pânico agudo e reativam o córtex pré-frontal.',
    feedbackTrap:
      'Afirmações falsas não convencem um cérebro assustado; arquive e resgate provas concretas de batalhas reais que você já venceu.',
  },
  {
    id: 'garra_19_fadiga_decisoria_descanso_estrategico',
    trackId: 'GARRA_AUTODOMINIO',
    trackTitle: 'Autogoverno, Regulação Emocional & Garra',
    masteryTier: 3,
    title: 'Vigilância Sequencial & Micro-Pausas: Protegendo a Qualidade Decisória',
    subtitle: 'Trabalhar 4 horas seguidas sem pausa degrada o julgamento sem você perceber',
    mentorName: 'Marco Aurélio & Patricia Albulescu',
    scientificSource:
      'Danziger, Levav & Avnaim-Pesso (PNAS, 2011 — Decisões sequenciais); Albulescu et al. (PLOS ONE, 2022 — Meta-análise de micro-pausas, k = 22)',
    readTimeSec: 65,
    recommendedZone: 'AMARELO',
    coreEssence:
      'Muitos confundem garra com ficar 5 horas sentado encarando a tela até cometer erros grosseiros por exaustão atencional. Quando tomamos dezenas de decisões em sequência ininterrupta, o cérebro escorrega silenciosamente para o "padrão preguiçoso" (negar, adiar ou chutar). Inserir micro-pausas deliberadas longe de telas restaura a precisão executiva.',
    whyItWorksMechanism:
      'O estudo clássico sobre decisões judiciais sequenciais (Danziger et al., PNAS, 2011) mostrou queda abrupta na análise individualizada ao longo de blocos ininterruptos, revertida imediatamente após pausas restauradoras; e a meta-análise de Albulescu et al. (PLOS ONE, 2022, 22 estudos) confirmou que micro-pausas de 2 a 10 minutos (sem redes sociais!) elevam o vigor (d = 0,36) e reduzem a fadiga (d = 0,35).',
    zeroStepExample:
      'A cada 50 minutos de estudo intenso, levante-se por 5 minutos, beba água, olhe pela janela para longe (horizonte) e respire fundo SEM tocar no celular!',
    practicalActionToday:
      'Nunca tome uma decisão financeira, relacional ou estratégica crítica no fim de 3 horas seguidas de desgaste: faça primeiro uma pausa física de 5–10 minutos.',
    fieldMission:
      'Aplique hoje 2 blocos focados separados por uma micro-pausa limpa (água + caminhada curta + visão distante, zero tela).',
    dilemmaPrompt:
      'Durante uma pausa de 5 minutos entre blocos de estudo pesado, o que realmente restaura a vigilância executiva segundo Albulescu et al. (PLOS ONE, 2022)?',
    dilemmaOptions: [
      'Levantar da cadeira, hidratar-se, alongar o corpo e olhar para um ponto distante sem telas, permitindo descompressão real da memória de trabalho.',
      'Abrir vídeos curtos frenéticos por "apenas 5 minutos" enchendo o cérebro de novos estímulos.',
      'Pular todas as pausas por 6 horas seguidas para mostrar dureza.',
      'Entrar em discussões polêmicas em grupos de mensagem.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Recuperação cirúrgica! Pausa com tela não é pausa para o córtex pré-frontal — movimento leve, água e horizonte devolvem precisão limpa.',
    feedbackTrap:
      'Trocar a tela do estudo pela tela de vídeos curtos mantém a fadiga atencional alta e destrói o bloco seguinte.',
  },
  {
    id: 'garra_20_autodistanciamento_terceira_pessoa_kross',
    trackId: 'GARRA_AUTODOMINIO',
    trackTitle: 'Autogoverno, Regulação Emocional & Garra',
    masteryTier: 4,
    title: 'Autodistanciamento em 3ª Pessoa (Ethan Kross): Comandando a Si Mesmo pelo Nome',
    subtitle: 'Trocar "Eu estou perdido" pelo seu próprio nome cria distância executiva imediata',
    mentorName: 'Marco Aurélio, David Goggins & Ethan Kross',
    scientificSource:
      'Kross, Bruehlman-Senecal, Park et al. (Journal of Personality and Social Psychology, 2014 — Self-Talk as a Regulatory Mechanism); Moser et al. (Scientific Reports, 2017 — EEG/fMRI)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Já reparou que você dá conselhos brilhantes e calmos para um amigo em crise, mas quando a crise é SUA você se afoga na ansiedade? Em *Meditações*, Marco Aurélio falava consigo mesmo em 2ª pessoa ("Lembra-te, Marco..."), e David Goggins interpela "Goggins" pelo sobrenome no meio do sofrimento! Ethan Kross (Universidade de Michigan, *JPSP*, 2014) provou em 7 estudos que **falar consigo mesmo usando seu próprio nome ou "você"** em vez de "eu" ativa instantaneamente o modo conselheiro sábio!',
    whyItWorksMechanism:
      'Nos exames de fMRI e eletroencefalografia (Moser & Kross, *Scientific Reports*, 2017), substituir "Por que EU estou tão ansioso?" por "[Seu Nome], qual é o próximo passo limpo que VOCÊ precisa dar agora?" reduziu a hiperativação da amígdala em **menos de 1 segundo**, sem exigir esforço cognitivo extra, e elevou significativamente a qualidade de falas públicas sob pressão!',
    zeroStepExample:
      'Na próxima onda de raiva, medo ou desânimo hoje, chame-se mentalmente pelo próprio nome: "[Seu Nome], respire fundo — o que um estrategista faria nos próximos 5 minutos?".',
    practicalActionToday:
      'Troque hoje todo monólogo interno em 1ª pessoa ("eu não vou dar conta") por comando calmo em 2ª/3ª pessoa pelo seu nome.',
    fieldMission:
      'Use o Autodistanciamento Linguístico de Kross antes de 1 decisão difícil, treino exigente ou partida sob pressão de relógio hoje.',
    dilemmaPrompt:
      'Nos 7 experimentos de Ethan Kross et al. (JPSP, 2014) e neuroimagem de Moser et al. (2017), o que aconteceu quando participantes sob estresse social trocaram "eu" pelo próprio nome no diálogo interno?',
    dilemmaOptions: [
      'A ansiedade dobrou porque falar o próprio nome gera confusão de identidade.',
      'Não houve nenhuma diferença mensurável no cérebro nem no desempenho.',
      'Só funcionou para atores profissionais de teatro.',
      'Criou distância psicológica imediata, reduziu a reatividade da amígdala em menos de 1 segundo e melhorou objetivamente o desempenho sob pressão e a clareza pós-evento.',
    ],
    correctOptionIndex: 3,
    feedbackCorrect:
      'Alavanca neurocognitiva cirúrgica! Um ajuste de uma única palavra tira você do redemoinho emocional e o coloca na cadeira do comandante.',
    feedbackTrap:
      'Mergulhar em "eu, meu medo, minha dor" cola sua lente no incêndio; dê um passo atrás chamando-se pelo nome como um mentor firme.',
  },

  // =========================================================================
  // PILAR 4: APRENDIZAGEM & MEMORIA (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'aprend_17_razao_urea_espacamento_cepeda',
    trackId: 'APRENDIZAGEM_MEMORIA',
    trackTitle: 'Meta-Aprendizagem: Aprender Qualquer Habilidade do Zero',
    masteryTier: 1,
    title: 'A Lei de Cepeda (10% a 20%): A Matemática Exata da Revisão Espaçada',
    subtitle: 'Estudar tudo na véspera apaga em 7 dias; espaçar no intervalo certo fixa por anos',
    mentorName: 'Senku Ishigami & Nicholas Cepeda',
    scientificSource:
      'Cepeda, Pashler, Vul, Wixted & Rohrer (Psychological Bulletin, 2006 — 317 experimentos; Psychological Science, 2008, N = 1.354)',
    readTimeSec: 65,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Todo iniciante pergunta: "Depois de estudar algo hoje, em quantos dias devo revisar para não esquecer?". Após analisar 317 experimentos e testar mais de 1.350 pessoas por até 1 ano, Nicholas Cepeda e Harold Pashler descobriram uma proporção matemática surpreendente: o intervalo ideal entre a 1ª sessão e a revisão fica entre **10% e 20% do tempo pelo qual você deseja lembrar**!',
    whyItWorksMechanism:
      'Em Cepeda et al. (Psychological Science, 2008), a retenção seguiu uma curva em U invertido conforme o espaçamento: revisar 5 minutos depois gera "ilusão de fluência" sem esforço de reconstrução sináptica; demorar demais apaga o traço. Revisar em ~10%–20% da meta (ex: quer lembrar em 10 dias -> revise em 1–2 dias; quer lembrar em 6 meses -> revise em 2–4 semanas após as revisões iniciais!) maximiza a reconsolidação de longo prazo.',
    zeroStepExample:
      'Aprendeu um conceito novo hoje? Não releia 10 vezes seguidas agora! Feche o caderno, revise amanhã (+1 dia), depois em +4 dias, depois em +14 dias.',
    practicalActionToday:
      'Divida 1 hora de estudo de hoje em dois blocos espaçados (30 min hoje + 30 min daqui a 2 dias) em vez de empilhar tudo numa maratona única.',
    fieldMission:
      'Conclua hoje as revisões espaçadas pendentes da Academia antes de abrir matérias novas, respeitando a janela ótima de reconsolidação.',
    dilemmaPrompt:
      'Você tem uma prova importante daqui a 30 dias e dispõe de duas sessões de estudo para um tema difícil. Segundo Cepeda et al. (2006, 2008), quando agendar a 2ª sessão após estudar hoje?',
    dilemmaOptions: [
      'Estudar a 2ª sessão imediatamente na hora seguinte para aproveitar que "está fresco".',
      'Agendar a 2ª sessão entre 3 e 6 dias depois (10% a 20% do horizonte de 30 dias), forçando reconstrução ativa da memória no ponto ótimo.',
      'Deixar a 2ª sessão para os últimos 5 minutos antes de entrar na sala de prova.',
      'Nunca revisar nenhum conteúdo já lido.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Precisão científica! A janela de 10%–20% exige esforço real de recuperação justamente quando a memória começaria a desbotar, blindando o traço neural.',
    feedbackTrap:
      'Repetir na mesma hora engana você com familiaridade rasa; espaçar na razão ótima multiplica a retenção pelo mesmo tempo investido.',
  },
  {
    id: 'aprend_18_teoria_templates_gobet_simon',
    trackId: 'APRENDIZAGEM_MEMORIA',
    trackTitle: 'Meta-Aprendizagem: Aprender Qualquer Habilidade do Zero',
    masteryTier: 2,
    title: 'Teoria dos Templates (Gobet & Simon): Como Grandes Mestres Enxergam o Todo',
    subtitle: 'Você não nasce com memória fotográfica — constrói moldes mentais com encaixes rápidos',
    mentorName: 'Herbert Simon (Nobel), Fernand Gobet & Garry Kasparov',
    scientificSource:
      'Gobet & Simon (Cognitive Psychology, 1996, 31, 1–40 — Templates in Chess Memory); Chase & Simon (1973)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Um Grande Mestre olha para um tabuleiro de xadrez por 5 segundos e reconstrói quase todas as 25 peças sem erro — mas se as peças forem espalhadas de forma aleatória e ilegal, ele lembra quase tão pouco quanto um iniciante! Por quê? Porque mestres não têm "câmera fotográfica mágica": segundo Gobet e Simon (1996), através de prática deliberada eles evoluem pequenos blocos (*chunks*) em **Templates** — estruturas maiores (~12 peças fixas + "gavetas variáveis" preenchidas em menos de 1 segundo) já ligadas aos planos estratégicos!',
    whyItWorksMechanism:
      'Em Cognitive Psychology (1996), Gobet e Simon demonstraram com o modelo CHREST que, à medida que um estudante domina padrões recorrentes (estruturas de peões, faturas contábeis, circuitos elétricos ou diagnósticos médicos), a rede de discriminação perceptual funde dezenas de elementos isolados num único "Template" na memória de longo prazo, contornando o gargalo estreito da memória de trabalho!',
    zeroStepExample:
      'Ao resolver um problema de xadrez ou matemática hoje, não decore "lance e4"; nomeie o PADRÃO inteiro (ex: "Isto é um Garfo Real em c7" ou "Isto é a Ponte de Lucena").',
    practicalActionToday:
      'Estude hoje 2 padrões clássicos na aba XADREZ (Problemas ou Finais) dando nome explícito à estrutura geométrica para gravar o Template na memória.',
    fieldMission:
      'Ao estudar qualquer área hoje, pergunte: "Qual é o esqueleto fixo deste problema e quais detalhes são apenas variáveis trocáveis?".',
    dilemmaPrompt:
      'Por que um Grande Mestre reconstrói em 5 segundos uma posição real de partida, mas perde quase toda a vantagem em tabuleiros com peças jogadas ao acaso (Gobet & Simon, 1996)?',
    dilemmaOptions: [
      'Porque Grandes Mestres dependem de sorte visual que some em posições estranhas.',
      'Porque a maestria humana funciona por reconhecimento de padrões significativos armazenados em Chunks e Templates na memória de longo prazo — algo que qualquer pessoa pode construir estudando estruturas reais.',
      'Porque posições reais têm menos peças do que posições aleatórias.',
      'Porque apenas quem nasce com QI acima de 180 consegue memorizar tabuleiros.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Chave da maestria universal! Todo especialista — no xadrez, medicina, código ou engenharia — enxerga rápido porque construiu uma biblioteca viva de Templates.',
    feedbackTrap:
      'Ninguém vira mestre decorando peças soltas; agrupe sempre o conhecimento em padrões estruturais conectados a planos de ação.',
  },
  {
    id: 'aprend_19_efeito_protege_aprender_ensinando',
    trackId: 'APRENDIZAGEM_MEMORIA',
    trackTitle: 'Meta-Aprendizagem: Aprender Qualquer Habilidade do Zero',
    masteryTier: 3,
    title: 'O Efeito Protégé (Nestojko & Bjork): Estudar Como Quem Vai Dar Aula Amanhã',
    subtitle: 'A simples expectativa de ensinar alguém reorganiza a hierarquia inteira da memória',
    mentorName: 'Sêneca ("Docendo Discimus") & Robert Bjork',
    scientificSource:
      'Nestojko, Bui, Kornell & Bjork (Memory & Cognition, 2014 — Expecting to teach enhances learning and organization of knowledge); Fiorella & Mayer (Contemporary Educational Psychology, 2013)',
    readTimeSec: 65,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Há dois mil anos Sêneca escreveu: *Homines, dum docent, discunt* — "Os homens, enquanto ensinam, aprendem". No laboratório de memória da UCLA, Nestojko, Kornell e Robert Bjork (2014) deram exatamente o mesmo texto e o mesmo tempo para dois grupos: metade estudou para fazer uma prova; a outra metade estudou sabendo que teria de **ensinar o conteúdo a outro aluno**. Mesmo antes de dar a aula, o grupo que estudou para ensinar organizou melhor as ideias centrais e acertou significativamente mais!',
    whyItWorksMechanism:
      'Fiorella e Mayer (2013) demonstraram que quando estudamos apenas "para passar na prova", acumulamos fragmentos soltos; quando estudamos com mentalidade de professor (**Efeito Protégé**), o cérebro busca automaticamente a espinha dorsal lógica, antecipa dúvidas difíceis e traduz jargões confusos em exemplos cristalinos — e o ganho duplica quando você realmente explica o conteúdo em voz alta sem consultar o texto!',
    zeroStepExample:
      'Antes de abrir qualquer livro ou aula hoje, declare: "Daqui a 25 minutos eu vou explicar este tema em 3 minutos como se estivesse ensinando meu irmão mais novo do zero!".',
    practicalActionToday:
      'Estude seu bloco principal hoje com "mentalidade de professor" e, ao terminar, dê uma mini-aula de 2 minutos em voz baixa (para alguém real ou para uma cadeira vazia).',
    fieldMission:
      'Ensine hoje 1 princípio aprendido na FORJA para uma pessoa real (ou grave/escreva uma explicação limpa de 5 linhas sem olhar o material).',
    dilemmaPrompt:
      'No experimento clássico de Nestojko, Bui, Kornell & Bjork (Memory & Cognition, 2014), por que os alunos que estudaram esperando ensinar superaram os que estudaram esperando apenas uma prova, mesmo com tempo idêntico?',
    dilemmaOptions: [
      'Porque a expectativa de ensinar ativa codificação estrutural profunda: o cérebro separa ideias principais de detalhes secundários e organiza conexões lógicas coerentes.',
      'Porque quem vai ensinar recebe textos mais fáceis do que quem faz prova.',
      'Porque estudar para prova desliga o hipocampo.',
      'Ensinar só ajuda depois que você já tem doutorado na área.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Efeito Protégé ativado! Quem aprende para ensinar domina duas vezes.',
    feedbackTrap:
      'Estudar apenas para "decorar e despejar na prova" gera conhecimento quebradiço; estude sempre pronto para ensinar com clareza.',
  },
  {
    id: 'aprend_20_transferencia_xadrez_cognicao_burgoyne',
    trackId: 'APRENDIZAGEM_MEMORIA',
    trackTitle: 'Meta-Aprendizagem: Aprender Qualquer Habilidade do Zero',
    masteryTier: 4,
    title: 'Xadrez, Raciocínio Fluido & A Ponte da Transferência Deliberada',
    subtitle: 'O que a ciência real diz sobre o xadrez como laboratório cognitivo e estratégico',
    mentorName: 'José Raúl Capablanca & Alexander Burgoyne',
    scientificSource:
      'Burgoyne, Sala, Gobet, Macnamara, Campitelli & Hambrick (Intelligence, 2016, N = 1.779); Sala & Gobet (Educational Research Review, 2016, 24 estudos)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Sem misticismo nem exageros: o que a ciência de ponta descobriu sobre o xadrez? Na maior meta-análise já feita (Burgoyne et al., Intelligence, 2016, N = 1.779), a habilidade enxadrística correlaciona-se significativamente com Raciocínio Fluido (r = .24; chegando a r = .32 em jovens e iniciantes!), Memória de Trabalho (r = .25), Velocidade de Processamento (r = .24) e Habilidade Numérica (r = .35). Mas há um segredo crucial: jogar no automático transfere pouco — a transferência para a vida real explode quando você extrai deliberadamente os princípios (gestão de relógio, profilaxia, cálculo de variantes e revisão fria de erros)!',
    whyItWorksMechanism:
      'Sala e Gobet (2016) mostraram ganhos moderados em matemática (d = 0,38) e cognição geral (d = 0,34) em estudantes, destacando que a "transferência distante" exige **ponte metacognitiva explícita** (Salomon & Perkins, 1989 — *High-Road Transfer*): usar o tabuleiro como simulador consciente para treinar inibição do impulso (não tocar na peça sem checar ameaças), orçamento de tempo e análise pós-partida sem ego!',
    zeroStepExample:
      'Ao jogar 1 partida rápida hoje na aba XADREZ, aplique uma regra para a vida inteira: antes de agir, pare 5 segundos e pergunte "Qual é a melhor resposta do outro se eu fizer isto?".',
    practicalActionToday:
      'Jogue 1 partida ou resolva 3 problemas táticos hoje e rode a Revisão Completa CAPS anotando qual hábito mental da partida se repete nas suas decisões do dia a dia (pressa, medo ou excesso de confiança).',
    fieldMission:
      'Use o tabuleiro da FORJA hoje como espelho metacognitivo: identifique 1 erro de impulsividade no jogo e corrija o mesmo padrão numa decisão real do seu trabalho/estudo.',
    dilemmaPrompt:
      'Segundo as meta-análises de Burgoyne et al. (Intelligence, 2016) e Sala & Gobet (2016), como transformar o treino de xadrez num multiplicador real para estudos, finanças e estratégia de vida?',
    dilemmaOptions: [
      'Jogar dezenas de partidas impulsivas de 1 minuto com raiva sem nunca revisar um único erro.',
      'Acreditar que basta mover peças distraído para virar gênio em qualquer matéria sem estudar aquela matéria.',
      'Usar o xadrez como laboratório deliberado de cálculo, gestão de tempo, profilaxia ("o que o outro planeja?") e auditoria fria pós-partida, construindo pontes explícitas para decisões reais.',
      'Abandonar todo treino mental porque nenhuma habilidade exige raciocínio fluido.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Visão científica impecável! Zero mito e 100% transferência deliberada (*High-Road Transfer*): o tabuleiro vira academia viva de disciplina executiva e estratégia.',
    feedbackTrap:
      'Repetição impulsiva sem revisão não educa o julgamento; extraia conscientemente o princípio estratégico de cada partida analisada.',
  },

  // =========================================================================
  // PILAR 5: COMUNICACAO & INTELIGENCIA SOCIAL (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'comun_17_escuta_segunda_camada_perguntas',
    trackId: 'COMUNICACAO_SOCIAL',
    trackTitle: 'Retórica, Escrita Clara, Negociação & Inteligência Social',
    masteryTier: 1,
    title: 'A Magia das Perguntas de Seguimento: Escutar na Segunda Camada',
    subtitle: 'Quem é tímido ou iniciante ganha carisma instantâneo sabendo perguntar com interesse real',
    mentorName: 'Sócrates & Alison Wood Brooks (Harvard)',
    scientificSource:
      'Huang, Yeomans, Brooks, Minson & Gino (Journal of Personality and Social Psychology, 2017 — It Doesn’t Hurt to Ask)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Um jovem tímido trava nas conversas achando que precisa contar histórias mirabolantes para ser admirado. A ciência de Harvard provou exatamente o oposto! Em centenas de conversas reais analisadas palavra por palavra, as pessoas mais queridas, confiáveis e influentes foram aquelas que fizeram **Perguntas de Seguimento** (*Follow-up Questions*): perguntas que pegam o que o outro acabou de dizer e aprofundam um degrau com curiosidade genuína!',
    whyItWorksMechanism:
      'Huang, Yeomans, Brooks et al. (JPSP, 2017) demonstraram em 3 estudos experimentais que perguntas de seguimento sinalizam responsividade ativa — provando ao cérebro do interlocutor que você realmente ouviu, processou e se importou, sem mudar o assunto de volta para o próprio umbigo ("comigo aconteceu igual...").',
    zeroStepExample:
      'Quando alguém disser hoje "A semana foi corrida no trabalho", não responda "A minha também!"; pergunte com interesse sincero: "O que pegou mais pesado por lá essa semana?".',
    practicalActionToday:
      'Em 2 conversas hoje, segure o impulso de puxar o assunto para você e faça 1 pergunta de seguimento sobre o que a outra pessoa acabou de contar.',
    fieldMission:
      'Pratique hoje a "Regra das 2 Camadas": ouça a resposta inicial de alguém e faça mais 1 pergunta sincera aprofundando aquela resposta antes de falar de si.',
    dilemmaPrompt:
      'Um iniciante quer causar ótima impressão numa conversa importante, mas tem medo de não ter histórias impressionantes para contar. Segundo Huang & Brooks (Harvard, JPSP 2017), qual atitude gera maior simpatia e confiança imediata?',
    dilemmaOptions: [
      'Interromper a outra pessoa a cada frase para tentar parecer mais inteligente.',
      'Ficar mudo olhando para o chão com respostas de uma sílaba só.',
      'Mudar de assunto bruscamente a cada 30 segundos como um interrogatório policial.',
      'Ouvir com atenção genuína e fazer perguntas de seguimento conectadas ao que o outro acabou de compartilhar, demonstrando presença e responsividade.',
    ],
    correctOptionIndex: 3,
    feedbackCorrect:
      'Inteligência social imediata! Você tira o holofote ansioso de cima de si mesmo e entrega à outra pessoa o raro presente de ser verdadeiramente ouvida.',
    feedbackTrap:
      'Tentar impressionar falando só de si afasta as pessoas; curiosidade genuína com perguntas de seguimento constrói pontes sólidas.',
  },
  {
    id: 'comun_18_efeito_pratfall_vulnerabilidade_competente',
    trackId: 'COMUNICACAO_SOCIAL',
    trackTitle: 'Retórica, Escrita Clara, Negociação & Inteligência Social',
    masteryTier: 2,
    title: 'O Efeito Pratfall (Aronson): Competência Real Sem Máscara de Perfeição Robótica',
    subtitle: 'Por que admitir com naturalidade um pequeno tropeço aumenta a confiança em quem é competente',
    mentorName: 'Elliot Aronson & Tony Stark',
    scientificSource:
      'Aronson, Willerman & Floyd (Psychonomic Science, 1966 — The Effect of a Pratfall on Increasing Interpersonal Attractiveness)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Muitos tentam ganhar respeito fingindo que nunca erram, nunca derrubam café e sabem absolutamente todas as respostas — e acabam parecendo falsos, distantes e antipáticos! No célebre experimento de Elliot Aronson (1966), um candidato altamente competente que resolveu 92% das questões difíceis e no final derrubou uma xícara de café com bom humor foi avaliado como **significativamente mais confiável e admirado** do que o candidato idêntico que tentou parecer um robô infalível!',
    whyItWorksMechanism:
      'Atenção à condição exata descoberta por Aronson (1966): para alguém desleixado e incompetente, errar piora a imagem; mas para alguém **visivelmente preparado e competente**, reconhecer com tranquilidade "neste ponto específico ainda vou checar" ou rir de um pequeno tropeço humano destrói a barreira defensiva dos ouvintes e prova honestidade radical!',
    zeroStepExample:
      'Se alguém fizer uma pergunta técnica cuja resposta exata você não sabe hoje, não enrole nem invente: diga com firmeza serena "Os dados A e B eu tenho aqui; o ponto C vou conferir na fonte e te retorno às 15h".',
    practicalActionToday:
      'Combine preparo técnico rigoroso com honestidade humana limpa: zero blefe quando não souber um detalhe e zero drama se cometer um pequeno deslize.',
    fieldMission:
      'Troque hoje a máscara tensa de "sabe-tudo" pela credibilidade inabalável de quem domina sua base e admite limites com transparência.',
    dilemmaPrompt:
      'Durante uma apresentação excelente e bem preparada, você tropeça numa palavra ou recebe uma pergunta fora do escopo. Segundo Elliot Aronson (Psychonomic Science, 1966 — Efeito Pratfall), qual reação aumenta sua credibilidade?',
    dilemmaOptions: [
      'Lidar com naturalidade serena e transparência ("Boa pergunta, vou checar o número exato e enviar até o fim da tarde"), unindo alta competência real a autenticidade humana.',
      'Inventar um número falso na hora com cara séria para fingir onisciência.',
      'Entrar em pânico achando que um pequeno tropeço arruinou 100% do trabalho.',
      'Ir sem estudar nada esperando que errar tudo gere simpatia.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Carisma autêntico! Competência sólida + honestidade sem máscara gera confiança imediata que nenhum "perfeitinho artificial" alcança.',
    feedbackTrap:
      'Blefar destrói a confiança ao ser descoberto, e despreparo sem competência não ativa o Efeito Pratfall; seja excelente e verdadeiro.',
  },
  {
    id: 'comun_19_perspectiva_cognitiva_galinsky',
    trackId: 'COMUNICACAO_SOCIAL',
    trackTitle: 'Retórica, Escrita Clara, Negociação & Inteligência Social',
    masteryTier: 3,
    title: 'Tomada de Perspectiva Cognitiva (Galinsky): Entrar na Cabeça do Outro',
    subtitle: 'Por que entender a lógica e as restrições do outro vence a empatia puramente emocional',
    mentorName: 'Nicolau Maquiavel & Adam Galinsky',
    scientificSource:
      'Galinsky, Maddux, Gilin & White (Psychological Science, 2008, 19(4), 378–384 — Why It Pays to Get Inside the Head of Your Opponent)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Em uma negociação difícil — salário, compra, contrato ou conflito familiar — o que funciona melhor: sentir pena emocional do outro (empatia afetiva) ou mapear friamente o que ele mais valoriza, o que ele teme e quais restrições apertam o lado dele (tomada de perspectiva cognitiva)? Em 3 experimentos clássicos na *Psychological Science* (2008), Adam Galinsky provou uma descoberta fascinante: **entrar cognitivamente na cabeça do outro** descobriu acordos criativos que ninguém mais enxergava, gerando mais valor para AMBOS os lados!',
    whyItWorksMechanism:
      'Galinsky et al. (2008) mostraram que a empatia puramente emocional muitas vezes leva a concessões apressadas que prejudicam seu próprio resultado sem achar soluções estruturais, enquanto focar só em si gera impasse cego. Já a Tomada de Perspectiva Cognitiva mapeia a função de utilidade do interlocutor ("O que custa pouco para mim, mas resolve a maior dor dele?"), destravando trocas ganha-ganha de alta precisão.',
    zeroStepExample:
      'Antes de pedir algo a alguém hoje, escreva em 1 linha: "Qual é o maior problema ou cobrança que ESSA pessoa precisa resolver hoje, e como minha proposta facilita a vida dela?".',
    practicalActionToday:
      'Prepare 1 conversa ou negociação mapeando os interesses, medos e restrições reais da outra parte antes de apresentar seu argumento.',
    fieldMission:
      'Num impasse hoje, descubra 1 moeda de troca assimétrica (algo simples para você entregar que tenha alto valor para a necessidade real do outro).',
    dilemmaPrompt:
      'Nos experimentos de negociação de Galinsky, Maddux, Gilin & White (Psychological Science, 2008), qual grupo fechou o maior número de acordos ocultos lucrativos para ambos os lados?',
    dilemmaOptions: [
      'Quem olhou exclusivamente para o próprio interesse ignorando o outro lado.',
      'Quem sentiu apenas emoção/pena e cedeu tudo sem analisar os termos.',
      'Quem praticou Tomada de Perspectiva Cognitiva ("entrar na cabeça do outro" para compreender seus interesses, prioridades e restrições reais).',
      'Quem usou ameaças e ultimatos nos primeiros 2 minutos.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Estratégia negociadora de mestre! Compreender com exatidão como o outro pensa e quais pressões ele sofre revela pontes invisíveis aos impulsivos.',
    feedbackTrap:
      'Nem egoísmo cego nem concessão emocional resolvem impasses complexos; mapeie cognitivamente os incentivos e dores do outro lado.',
  },
  {
    id: 'comun_20_retorica_crise_calma_contagiosa',
    trackId: 'COMUNICACAO_SOCIAL',
    trackTitle: 'Retórica, Escrita Clara, Negociação & Inteligência Social',
    masteryTier: 4,
    title: 'Contágio Fisiológico sob Crise: Baixar o Tom para Comandar o Caos',
    subtitle: 'Em emergências, a cadência da sua voz regula o sistema nervoso de toda a equipe',
    mentorName: 'Doctor Who & Capitão Chesley "Sully" Sullenberger',
    scientificSource:
      'Barsade (Administrative Science Quarterly, 2002 — The Ripple Effect: Emotional Contagion); Neumann & Strack (JPSP, 2000 — Contágio vocal)',
    readTimeSec: 65,
    recommendedZone: 'AMARELO',
    coreEssence:
      'Quando os dois motores do voo US Airways 1549 apagaram a 850 metros de altitude sobre Nova York, a gravação da cabine do Capitão Sullenberger entrou para a história da aviação: zero grito, cadência pausada, frases curtas ("My aircraft" / "We’re gonna be in the Hudson"). Quando todos ao redor entram em pânico, quem reduz a velocidade da fala em 20% e baixa o tom da voz torna-se instantaneamente o centro gravitacional da sala.',
    whyItWorksMechanism:
      'Neumann & Strack (JPSP, 2000) provaram o "Contágio Vocal Automático": o cérebro humano espelha inconscientemente a frequência acústica e a cadência respiratória da voz dominante no ambiente. E Sigal Barsade (Yale/Wharton, ASQ, 2002) demonstrou em grupos reais de trabalho que a calma regulada propaga cooperação e reduz conflito e erro operacional em toda a equipe.',
    zeroStepExample:
      'Se alguém falar alto ou afobado com você hoje, faça o oposto exato do reflexo comum: solte o ar devagar e responda num tom 20% mais calmo, firme e pausado.',
    practicalActionToday:
      'Diante de qualquer imprevisto hoje, seja o "amortecedor térmico" do ambiente: voz baixa, fatos claros e próximo passo concreto.',
    fieldMission:
      'Em um momento de pressa ou tensão coletiva hoje, recuse amplificar a agitação e estabilize o grupo pela serenidade firme da sua fala.',
    dilemmaPrompt:
      'Um erro urgente estoura no trabalho/família e duas pessoas começam a falar alto e atropelado. Segundo Barsade (2002) e Neumann & Strack (2000), como um líder polímata estabiliza a execução?',
    dilemmaOptions: [
      'Gritar ainda mais alto que os dois para mostrar quem manda.',
      'Reduzir deliberadamente a velocidade e o volume agudo da própria voz, usar frases curtas orientadas à ação e induzir regulação por contágio vocal.',
      'Sair da sala batendo a porta e deixar o caos explodir.',
      'Falar o mais rápido possível despejando dez ordens confusas.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Presença de comando pura! Como o Doctor no olho do furacão ou Sully na cabine: voz firme e pausada devolve o córtex pré-frontal a toda a sala.',
    feedbackTrap:
      'Responder à agitação com mais agitação multiplica erros em cascata; governe o ritmo da sala governando primeiro sua voz.',
  },

  // =========================================================================
  // PILAR 6: LOGICA, NUMERACIA & RECURSOS (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'logica_17_ilusao_eficiencia_reciproca_larrick',
    trackId: 'LOGICA_NUMERACIA',
    trackTitle: 'Lógica, Matemática Mental, Probabilidade & Finanças',
    masteryTier: 1,
    title: 'A Ilusão da Eficiência Linear (Larrick & Soll): Onde Mora o Maior Desperdício',
    subtitle: 'Cortar metade de um ralo gigante economiza 5x mais do que polir o que já é enxuto',
    mentorName: 'Richard Larrick & Jack Soll (Duke)',
    scientificSource:
      'Larrick & Soll (Science, 2008, 320, 1593–1594 — The MPG Illusion: Misunderstanding Fuel Efficiency)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Pergunta clássica publicada na revista *Science* (2008): para rodar 1.000 km, o que economiza MAIS combustível — trocar um caminhão que faz **5 km/L por um de 10 km/L**, ou trocar um carro econômico que faz **20 km/L por um super-híbrido de 50 km/L**? Quase todo mundo chuta "de 20 para 50!", mas a conta real choca: de 5 para 10 km/L cai de 200L para 100L (**economiza 100 litros!**); de 20 para 50 km/L cai de 50L para 20L (**economiza só 30 litros!**)!',
    whyItWorksMechanism:
      'Larrick e Soll (Science, 2008) demonstraram que o cérebro raciocina linearmente sobre taxas recíprocas (km/L, páginas/hora), errando feio onde atacar! A lição universal para dinheiro e tempo: **consertar seu PIOR ralo ineficiente (o gasto mais gordo ou a hora mais desperdiçada) rende 3 a 5 vezes mais resultado real do que tentar hiper-otimizar o que já funciona bem!**',
    zeroStepExample:
      'Em vez de passar 1 hora caçando R$ 2 de desconto no café, olhe primeiro para as suas 2 maiores despesas fixas mensais (ou seus 2 maiores ralos de horas da semana) — ali está o "5 km/L para 10 km/L"!',
    practicalActionToday:
      'Converta sempre taxas enganosas em consumo real total (reais/mês ou horas perdidas/semana) e ataque primeiro o maior ralo bruto.',
    fieldMission:
      'Corte pela metade 1 grande desperdício recorrente de tempo ou dinheiro hoje antes de perder energia otimizando migalhas.',
    dilemmaPrompt:
      'Para percorrer 1.000 km por mês, qual troca economiza MAIS litros reais de combustível no fim do mês segundo Larrick & Soll (Science, 2008)?',
    dilemmaOptions: [
      'Subir de 25 km/L para 50 km/L (de 40 litros para 20 litros = 20 litros poupados).',
      'As duas trocas economizam exatamente a mesma quantidade de litros.',
      'Subir de 5 km/L para 10 km/L (de 200 litros para 100 litros = 100 litros poupados — cinco vezes mais economia real atacando o pior ralo!).',
      'Subir de 50 km/L para 100 km/L (de 20 litros para 10 litros = 10 litros poupados).',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Matemática afiada! Converta sempre para consumo absoluto: atacar o ralo mais pesado entrega ganhos gigantescos imediatos.',
    feedbackTrap:
      'A Ilusão de Eficiência faz as pessoas polirem migalhas enquanto um vazamento cinco vezes maior drena o tanque.',
  },
  {
    id: 'logica_18_falacia_conjunccao_confiabilidade_serie',
    trackId: 'LOGICA_NUMERACIA',
    trackTitle: 'Lógica, Matemática Mental, Probabilidade & Finanças',
    masteryTier: 2,
    title: 'Multiplicação de Probabilidades & Confiabilidade em Série ($0{,}9^6 = 53\\%$)',
    subtitle: 'Quanto mais condições precisam dar certo juntas, menor a chance do plano sobreviver',
    mentorName: 'Amos Tversky, Claude Shannon & Robert Lusser',
    scientificSource:
      'Tversky & Kahneman (Psychological Review, 1983 — Extensional versus Intuitive Reasoning: The Conjunction Fallacy); Lei de Confiabilidade em Série de Lusser',
    readTimeSec: 65,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Imagine um plano mirabolante que depende de **6 etapas seguidas**, e cada etapa tem **90% de chance** de dar certo — parece "quase garantido (90%)", não é? Faça a conta real de probabilidades independentes em série: $0{,}90 \times 0{,}90 \times 0{,}90 \times 0{,}90 \times 0{,}90 \times 0{,}90 = \mathbf{0{,}53}$ (**apenas 53%, praticamente cara ou coroa!**). Se forem 10 etapas de 80%, cai para **10,7%**!',
    whyItWorksMechanism:
      'Tversky e Kahneman (Psychological Review, 1983) provaram na Falácia da Conjunção que histórias cheias de detalhes específicos parecem mais plausíveis ao cérebro, embora matematicamente **cada condição "E" adicionada SÓ POSSA DIMINUIR a probabilidade final** ($P(A \cap B) \le P(A)$)! E na engenharia de foguetes (Lei de Lusser), sistemas simples com menos elos em série falham drasticamente menos.',
    zeroStepExample:
      'Se sua rotina matinal depende de 7 coisas perfeitas acontecerem sem atraso para você conseguir estudar, simplifique para depender de apenas **1 ou 2 passos diretos**!',
    practicalActionToday:
      'Enxugue 1 plano complicado seu cortando etapas desnecessárias em série: quanto menos "SE tudo isto der certo junto", mais blindada é a execução.',
    fieldMission:
      'Calcule hoje a probabilidade real multiplicada de um projeto seu e substitua elos frágeis em série por planos simples e independentes.',
    dilemmaPrompt:
      'Um projeto depende obrigatoriamente de 5 aprovações independentes seguidas, cada uma com 80% de chance de sucesso. Qual é a chance real aproximada de todo o projeto passar sem travar (Lei de Lusser / Multiplicação de Probabilidades)?',
    dilemmaOptions: [
      'Continua sendo 80%, porque a média das cinco etapas é 80%.',
      'Cerca de 33% (0,8 × 0,8 × 0,8 × 0,8 × 0,8 = 0,327), provando que encadear muitas condições necessárias derruba rapidamente a chance global.',
      'Sobe para 100% porque cinco vezes 80% passa de 100%.',
      'Exatamente 95%, pois histórias detalhadas são sempre mais prováveis.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Raciocínio probabilístico cirúrgico! Simplicidade estrutural não é só estética — é matemática pura de confiabilidade.',
    feedbackTrap:
      'Esquecer de multiplicar probabilidades em série é o motivo pelo qual planos cheios de "e se tudo der certo" quebram toda semana.',
  },
  {
    id: 'logica_19_coincidencias_diaconis_mosteller',
    trackId: 'LOGICA_NUMERACIA',
    trackTitle: 'Lógica, Matemática Mental, Probabilidade & Finanças',
    masteryTier: 3,
    title: 'A Lei dos Números Verdadeiramente Grandes: Desmistificando Coincidências',
    subtitle: 'Com milhões de eventos por dia, o "um em um milhão" acontece toda tarde!',
    mentorName: 'Persi Diaconis & Frederick Mosteller (Harvard/Stanford)',
    scientificSource:
      'Diaconis & Mosteller (Journal of the American Statistical Association, 1989 — Methods for Studying Coincidences)',
    readTimeSec: 65,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Numa sala com apenas **23 pessoas**, qual a chance de duas fazerem aniversário no exato mesmo dia e mês? A intuição chuta "uns 6%", mas a matemática exata prova **50,7%** (com 57 pessoas, passa de **99%**)! Os estatísticos de Harvard e Stanford Persi Diaconis e Frederick Mosteller (JASA, 1989) formularam a **Lei dos Números Verdadeiramente Grandes**: com amostra grande o suficiente, eventos aparentemente espantosos têm certeza matemática de acontecer todos os dias — sem sinal místico, superstição ou conspiração!',
    whyItWorksMechanism:
      'Nosso cérebro comete dois erros combinados (Diaconis & Mosteller, 1989): ignora os milhões de momentos comuns em que nada incomum aconteceu (denominador gigantesco) e calcula a chance de 1 par específico em vez de todos os pares possíveis ($23 \times 22 / 2 = 253$ pares de comparação!). Isso protege você contra charlatães que acertam chutes por volume e contra superstições financeiras!',
    zeroStepExample:
      'Viu um "guru" que acertou uma previsão famosa? Lembre-se de Diaconis: se 10.000 palpiteiros chutam todo ano, dezenas acertarão 5 vezes seguidas por puro sorteio combinatório!',
    practicalActionToday:
      'Nunca trate uma coincidência isolada ou sequência curta de sorte como prova de habilidade sobrenatural ou "sinal mágico" para arriscar dinheiro.',
    fieldMission:
      'Audite hoje 1 narrativa impressionante perguntando: "Quantas tentativas totais existiram fora da câmera para que essa coincidência aparecesse?".',
    dilemmaPrompt:
      'Um analista envia boletins gratuitos apostando "alta" para 5.000 pessoas e "baixa" para outras 5.000; após 4 rodadas dividindo os grupos, 625 pessoas receberam 4 acertos seguidos perfeitos e acham que ele é um profeta infalível. O que Diaconis & Mosteller (JASA, 1989) ensinam?',
    dilemmaOptions: [
      'Acertar 4 vezes seguidas para um subgrupo filtrado é consequência matemática trivial de grandes números e seleção pós-fato, exigindo verificar histórico completo auditado.',
      'Quatro acertos seguidos provam matematicamente dom sobrenatural infalível.',
      'Em uma sala com 30 pessoas é quase impossível duas fazerem aniversário no mesmo dia.',
      'Probabilidade combinatória nunca produz coincidências no mundo real.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Imunidade total contra truques de salão e falsos profetas financeiros! Quem domina combinatória enxerga o truque por trás do palco.',
    feedbackTrap:
      'Olhar apenas o acerto selecionado sem contar o universo total de chutes é o golpe mais antigo contra leigos em probabilidade.',
  },
  {
    id: 'logica_20_lei_de_little_teoria_filas',
    trackId: 'LOGICA_NUMERACIA',
    trackTitle: 'Lógica, Matemática Mental, Probabilidade & Finanças',
    masteryTier: 4,
    title: 'A Lei de Little ($L = \\lambda W$) & Teoria das Filas: Por Que Abrir 10 Projetos Trava Todos',
    subtitle: 'Quer terminar na metade do tempo? Corte pela metade o número de frentes abertas!',
    mentorName: 'John D. C. Little (MIT) & Tony Stark',
    scientificSource:
      'Little (Operations Research, 1961 — A Proof for the Queuing Formula: L = λW); Kingman (1961 — Equação de Espera Não Linear em Filas)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Em 1961, John Little (MIT) provou um teorema matematicamente inviolável para qualquer fábrica, hospital, processador ou rotina humana: **Tempo Médio para Concluir ($W$) = Itens em Aberto ao Mesmo Tempo ($L$) ÷ Taxa Real de Entrega ($\\lambda$)**. Tradução direta para a sua vida: se você conclui 2 projetos por semana ($\\lambda = 2$) e abre **10 projetos simultâneos ($L = 10$)**, cada projeto levará **5 semanas** se arrastando! Se limitar suas frentes abertas a **2 ($L = 2$)**, cada um fica pronto em **1 semana**, sem trabalhar nem 1 minuto a mais!',
    whyItWorksMechanism:
      'Além da Lei de Little ($W = L / \\lambda$), a fórmula de Kingman (1961) demonstra que o tempo de espera em fila explode proporcionalmente a $u / (1 - u)$, onde $u$ é a lotação do sistema: passar de 80% de ocupação ($0{,}8/0{,}2 = 4$) para 95% ($0{,}95/0{,}05 = 19$) multiplica os atrasos quase por **5 vezes**! Limitar o *Work In Progress* (WIP) libera velocidade instantânea.',
    zeroStepExample:
      'Está com 8 abas, 4 livros pela metade e 5 cursos abertos ao mesmo tempo? Congele 4 agora mesmo e feche **1 inteiro até o fim** antes de puxar o próximo!',
    practicalActionToday:
      'Defina um limite rígido de frentes em aberto (*WIP Limit* = no máximo 2 projetos ativos): proibido abrir o nº 3 sem encerrar ou arquivar 1 antes.',
    fieldMission:
      'Aplique a Lei de Little hoje: conclua e feche definitivamente 1 pendência aberta antes de iniciar qualquer frente nova.',
    dilemmaPrompt:
      'Uma equipe (ou estudante) entrega em média 2 tarefas grandes por semana, mas mantém 12 tarefas abertas pela metade ao mesmo tempo e reclama que tudo demora 6 semanas para sair. Pela Lei de Little (Operations Research, 1961: W = L / λ), qual alavanca reduz imediatamente o tempo de atravessamento sem exaustão?',
    dilemmaOptions: [
      'Abrir mais 8 tarefas novas ao mesmo tempo para subir para 20 frentes abertas.',
      'Limitar estritamente o Trabalho em Aberto (WIP = L) para 2 frentes simultâneas, derrubando o tempo médio de conclusão de 6 semanas para 1 semana e eliminando custo de troca de contexto.',
      'Trocar de tarefa a cada 5 minutos para dar sensação de movimento.',
      'A quantidade de projetos abertos ao mesmo tempo não afeta o prazo de entrega.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Engenharia operacional do MIT! Pare de começar dez coisas e passe a TERMINAR — a matemática de Little trabalha a seu favor na hora.',
    feedbackTrap:
      'Acumular dezenas de projetos abertos pela metade infla o numerador L e paralisa a velocidade de entrega.',
  },

  // =========================================================================
  // PILAR 7: CIENCIA & PRIMEIROS PRINCIPIOS (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'ciencia_17_caderno_laboratorio_observacao',
    trackId: 'CIENCIA_PRIMEIROS_PRINCIPIOS',
    trackTitle: 'Primeiros Princípios, Método Científico & Gargalos',
    masteryTier: 1,
    title: 'O Diário de Campo Científico: Medir no Papel Vence a Memória Enganosa',
    subtitle: 'O que não é registrado com dados objetivos vira autoengano em 48 horas',
    mentorName: 'Senku Ishigami & Michael Faraday',
    scientificSource:
      'Tweney (Faraday and the Nature of the Physical World, 1985); Harkin et al. (Psychological Bulletin, 2016 — Meta-análise de automonitoramento, N = 19.951, d = 0,40)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Michael Faraday saiu de aprendiz encadernador quase sem escola formal para se tornar um dos maiores cientistas experimentais da história — numerando pacientemente mais de 16.000 parágrafos de observações no seu Diário de Laboratório! Como Senku em *Dr. Stone*, o cientista não diz "acho que dormi bem e estudei bastante": ele **mede e anota** horas reais, cargas reais e erros reais.',
    whyItWorksMechanism:
      'Na gigantesca meta-análise de Benjamin Harkin et al. (Psychological Bulletin, 2016, 138 estudos, N = 19.951), o simples ato de **monitorar e registrar objetivamente o progresso** gerou avanço significativo nas metas (d = 0,40) — e foi ainda mais forte quando o registro era escrito/físico ou visível em painel! Medir destrói a névoa da memória seletiva.',
    zeroStepExample:
      'Hoje, registre com honestidade total seu check-in na FORJA (horas reais de sono, prontidão, sessões feitas) sem arredondar para bonito.',
    practicalActionToday:
      'Meça 1 variável da sua vida que você estava apenas "chutando de cabeça" (gastos da semana, minutos líquidos estudados ou passos caminhados).',
    fieldMission:
      'Mantenha registro 100% fiel hoje: zero maquiagem de números — trate sua rotina como um laboratório onde a verdade dos dados é sagrada.',
    dilemmaPrompt:
      'Uma pessoa jura que "estuda o dia inteiro e come super pouco", mas quando cronometra e anota tudo por 3 dias descobre apenas 38 minutos líquidos de estudo e vários beliscos esquecidos. O que Harkin et al. (Psychological Bulletin, 2016) comprovam?',
    dilemmaOptions: [
      'Anotar dados piora o desempenho porque tira a espontaneidade.',
      'A memória humana sem registro sofre distorção otimista; o automonitoramento objetivo (d = 0,40) revela os fatos reais e corrige a rota imediatamente.',
      'É melhor confiar em impressões vagas do que em cronômetros e registros.',
      'Só cientistas em laboratórios caros precisam registrar resultados.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Rigor digno de Faraday e Senku! A realidade medida com honestidade é o único ponto de partida possível para evoluir 10 bilhões por cento.',
    feedbackTrap:
      'Impressões vagas mentem para proteger o conforto; números honestos no diário libertam a melhoria real.',
  },
  {
    id: 'ciencia_18_invariantes_leis_conservacao_noether',
    trackId: 'CIENCIA_PRIMEIROS_PRINCIPIOS',
    trackTitle: 'Primeiros Princípios, Método Científico & Gargalos',
    masteryTier: 2,
    title: 'O Princípio dos Invariantes (Noether & Pólya): Caçar o Que NÃO Muda no Caos',
    subtitle: 'Em todo sistema complexo existe uma lei de conservação que desmascara o impossível',
    mentorName: 'Emmy Noether, Richard Feynman & George Pólya',
    scientificSource:
      'Noether (Nachrichten von der Gesellschaft der Wissenschaften zu Göttingen, 1918 — Invariantes e Leis de Conservação); Pólya (How to Solve It, Princeton, 1945)',
    readTimeSec: 65,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Em 1918, a matemática Emmy Noether provou um dos teoremas mais belos da história da física: toda simetria profunda da natureza gera uma **Lei de Conservação (um Invariante)** — energia não surge do nada, quantidade de movimento se conserva! E George Pólya ensinou que a maneira mais rápida de resolver um problema aparentemente impossível (no xadrez, na engenharia ou nas finanças) é perguntar: **"No meio de todas essas trocas confusas, QUAL grandeza permanece estritamente constante?"**!',
    whyItWorksMechanism:
      'Exemplo clássico no tabuleiro de xadrez: um Bispo que começa nas casas claras **JAMAIS** pisará numa casa escura em 100 lances (cor da casa é o invariante do Bispo!); um Cavalo troca obrigatoriamente a cor da casa a **cada salto** (paridade)! Na vida real, todo dia tem exatamente 24h (invariante de tempo) e contabilidade dobrada exige entradas = saídas + variação de caixa (invariante financeiro) — qualquer promessa que viole o invariante é impossível!',
    zeroStepExample:
      'Antes de acreditar em uma dieta mágica, investimento milagroso ou cronograma irreal hoje, teste o invariante básico: "A soma das horas/recursos fecha matematicamente ou viola a conservação?".',
    practicalActionToday:
      'Ao analisar 1 problema hoje (no xadrez, orçamento ou rotina), identifique primeiro qual é a restrição/invariante fixa que nenhum malabarismo consegue burlar.',
    fieldMission:
      'Use a paridade e os invariantes geométricos hoje na aba XADREZ (cor das casas dos Bispos e saltos de Cavalo) e no fechamento das suas 24 horas.',
    dilemmaPrompt:
      'Alguém tenta cobrir um tabuleiro de xadrez sem os dois cantos opostos brancos (restam 32 casas pretas e 30 brancas) usando 31 peças de dominó, onde CADA dominó cobre sempre 1 casa branca + 1 preta. Usando o Princípio dos Invariantes (Pólya, 1945), o que você conclui em 5 segundos sem testar combinações?',
    dilemmaOptions: [
      'É matematicamente impossível: como o invariante de cada dominó é cobrir 1 casa clara e 1 escura, 31 dominós exigem obrigatoriamente 31 claras e 31 escuras — jamais 30 e 32!',
      'Basta girar os dominós por 10 horas até achar um jeito.',
      'Invariantes só funcionam em aceleradores de partículas, nunca em problemas práticos.',
      'Com força de vontade suficiente é possível fazer 31 igual a 30.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Elegância científica suprema! Um invariante enxergado em 5 segundos poupa dez horas de tentativa cega no impossível.',
    feedbackTrap:
      'Tentar vencer na marra o que viola uma lei de conservação desperdiça energia preciosa; cheque sempre o invariante primeiro.',
  },
  {
    id: 'ciencia_19_ordens_magnitude_aproximacao_sucessiva',
    trackId: 'CIENCIA_PRIMEIROS_PRINCIPIOS',
    trackTitle: 'Primeiros Princípios, Método Científico & Gargalos',
    masteryTier: 3,
    title: 'Aproximações Sucessivas: Construa o Esqueleto Bruto Antes de Lixar os Milímetros',
    subtitle: 'Capturar o termo dominante de 80% no dia 1 vence perfeccionistas parados no rascunho',
    mentorName: 'Senku Ishigami, Tony Stark & Sanjoy Mahajan (MIT)',
    scientificSource:
      'Mahajan (Street-Fighting Mathematics: The Art of Educated Guessing and Opportunistic Problem Solving, MIT Press, 2010)',
    readTimeSec: 65,
    recommendedZone: 'VERDE',
    coreEssence:
      'Como físicos do MIT e engenheiros como Tony Stark constroem sistemas complexos tão rápido enquanto perfeccionistas travam na página 1? Pelo método das **Aproximações Sucessivas**: primeiro você resolve apenas o **termo de 1ª ordem** (o esqueleto grosseiro que responde por 80% do efeito — a armadura Mark I funcional na caverna!), testa na realidade, e SÓ DEPOIS adiciona as correções finas de 2ª e 3ª ordem (aerodinâmica, pintura, decimais)!',
    whyItWorksMechanism:
      'Sanjoy Mahajan (MIT Press, 2010) demonstra que calcular cinco casas decimais num modelo cujo termo principal está errado produz "lixo com precisão cirúrgica". Construir em passes sucessivos (Passe 1: estrutura bruta ponta a ponta; Passe 2: correção dos erros reais medidos; Passe 3: lapidação fina) garante entrega funcional desde cedo e impede gastar semanas polindo partes que nem seriam usadas!',
    zeroStepExample:
      'Precisa escrever um texto, código ou plano hoje? Faça em 15 minutos o "Esqueleto Feio Completo" do início ao fim antes de corrigir uma única vírgula da linha 1!',
    practicalActionToday:
      'Separe estritamente a fase de Construção de 1ª Ordem (levantar a estrutura inteira funcionando) da fase de Refinamento de 2ª Ordem hoje.',
    fieldMission:
      'Destrave hoje 1 tarefa empacada entregando primeiro a versão funcional de 1ª ordem ("Mark I") em vez de esperar a perfeição imaginária.',
    dilemmaPrompt:
      'Um estudante gasta 4 horas escolhendo a fonte e decorando o título da página 1 de um projeto de 10 páginas, e entrega o trabalho incompleto. Como o método de Aproximações Sucessivas (Mahajan, MIT 2010) resolve isso?',
    dilemmaOptions: [
      'Gastar 8 horas escolhendo cores melhores para o título antes de escrever o conteúdo.',
      'Desistir de qualquer polimento final mesmo depois que o projeto estiver pronto.',
      'Resolver primeiro o termo dominante de 1ª ordem (estruturar o esqueleto funcional completo das 10 páginas ponta a ponta) e só depois refinar estilo e detalhes em passes sucessivos.',
      'Começar pela última palavra da página 10 de trás para frente.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Engenharia ágil de primeira grandeza! Esqueleto funcional de pé primeiro, lapidação fina depois.',
    feedbackTrap:
      'Polir detalhes de 3ª ordem antes de levantar a estrutura de 1ª ordem é a receita clássica da paralisia perfeccionista.',
  },
  {
    id: 'ciencia_20_simulacao_mental_visuoespacial_tesla',
    trackId: 'CIENCIA_PRIMEIROS_PRINCIPIOS',
    trackTitle: 'Primeiros Princípios, Método Científico & Gargalos',
    masteryTier: 4,
    title: 'Bancada de Simulação Visuoespacial: Girar Sistemas Inteiros na Mente',
    subtitle: 'Treinar a tela visuoespacial do cérebro para prever falhas antes de tocar na peça',
    mentorName: 'Nikola Tesla & Roger Shepard',
    scientificSource:
      'Shepard & Metzler (Science, 1971 — Mental Rotation of Three-Dimensional Objects); Kosslyn, Ganis & Thompson (Nature Reviews Neuroscience, 2001); Uttal et al. (Psychological Bulletin, 2013 — Treinabilidade espacial, g = 0,47)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Nikola Tesla visualizava motores de corrente alternada girando em sua mente com tamanha nitidez espacial que detectava desequilíbrios mecânicos antes de usinar o metal. Isso é dom sobrenatural proibido a mortais? **NÃO!** Shepard & Metzler (*Science*, 1971) mediram a rotação mental 3D em milissegundos, e a meta-análise de David Uttal et al. (*Psychological Bulletin*, 2013, 217 estudos) provou que a inteligência espacial é **altamente treinável (g = 0,47), duradoura e transfere para ciência, engenharia e cirurgia**!',
    whyItWorksMechanism:
      'Stephen Kosslyn (*Nature Reviews Neuroscience*, 2001) demonstrou por neuroimagem que a simulação visuoespacial recruta áreas parietais e visuais primárias reais como um "rascunho geométrico interno". Treinar cálculo de variantes a 3 lances no xadrez sem mexer as peças e rotação mental no Córtex expande diretamente a precisão desse simulador interno!',
    zeroStepExample:
      'Na aba XADREZ hoje, escolha 1 problema tático e visualize na mente onde CADA peça estará após 2 lances inteiros ANTES de tocar na tela!',
    practicalActionToday:
      'Exercite seu simulador espacial hoje: resolva 1 bateria de Rotação Mental no Córtex ou 1 treino de Visão de Coordenadas + Cálculo sem arrastar peças.',
    fieldMission:
      'Antes de executar uma tarefa prática hoje (arrumar espaço, montar algo, codificar ou jogar), simule a sequência inteira de olhos fechados por 45 segundos.',
    dilemmaPrompt:
      'Um estudante acha que "não nasceu com boa visão espacial para geometria, engenharia ou xadrez". O que a meta-análise de 217 estudos de Uttal et al. (Psychological Bulletin, 2013) comprova cientificamente?',
    dilemmaOptions: [
      'Habilidades visuoespaciais são fixas no nascimento e jamais mudam com treino.',
      'A capacidade visuoespacial e de rotação mental é maleável, melhora significativamente com prática deliberada (g = 0,47) e transfere ganhos reais para áreas STEM e resolução de problemas.',
      'Simular movimentos na mente gasta a visão e prejudica o aprendizado.',
      'É melhor mexer peças no chute sem nunca tentar visualizar antes.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Mente de Tesla desmistificada pela neurociência! O laboratório visuoespacial parietal se fortalece cada vez que você gira estruturas e calcula lances na mente.',
    feedbackTrap:
      'Rotular-se "sem jeito espacial" ignora 217 estudos científicos: visualização estruturada é músculo cognitivo treinável.',
  },

  // =========================================================================
  // PILAR 8: ESTRATEGIA, SISTEMAS & EXECUCAO (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'estrat_17_regra_dois_minutos_atrito_zero',
    trackId: 'ESTRATEGIA_SISTEMAS',
    trackTitle: 'Estratégia Realista, Exemplos Resolvidos & Execução',
    masteryTier: 1,
    title: 'Engenharia de Atrito Ambiental: A Regra dos 20 Segundos',
    subtitle: 'Deixe o hábito bom a 1 passo de distância e o vício trancado a 4 passos',
    mentorName: 'Tony Stark, Richard Thaler (Nobel) & Angela Duckworth',
    scientificSource:
      'Thaler & Sunstein (Nudge, 2008 — Arquitetura de Escolha); Duckworth, Gendler & Gross (Perspectives on Psychological Science, 2016 — Situational Self-Control)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Quem acha que os mais disciplinados do mundo vencem brigando com tentações na cara o dia inteiro erra feio! Angela Duckworth e James Gross (2016) provaram que o autocontrole de elite é **Situacional**: você desenha o quarto na noite anterior para que o hábito certo tenha **atrito quase zero** (caderno aberto na página certa, caneta em cima, tênis ao lado da cama) e o hábito ruim tenha **alto atrito** (celular carregando em outro cômodo)!',
    whyItWorksMechanism:
      'A Economia Comportamental (Thaler, Nobel 2017) mostra que meros 20 segundos extras de esforço físico reduzem drasticamente comportamentos impulsivos automáticos, enquanto remover os primeiros 20 segundos de preparação dobra a taxa de início de tarefas importantes quando você está com sono ou cansado.',
    zeroStepExample:
      'Hoje à noite, antes de deitar, deixe sua garrafa de água cheia e o material do 1º bloco de amanhã já abertos sobre a mesa — zero procura pela manhã!',
    practicalActionToday:
      'Remova 2 passos de atrito do seu hábito prioritário hoje E adicione 2 passos de atrito (ex: tirar da tela inicial ou deixar longe da mesa) ao seu maior ladrão de tempo.',
    fieldMission:
      'Prepare fisicamente sua "bancada de lançamento" de amanhã hoje à noite em menos de 3 minutos.',
    dilemmaPrompt:
      'Um estudante dorme com o celular desbloqueado no travesseiro e deixa os livros enterrados no fundo do armário trancado; de manhã, sempre rola redes sociais em vez de estudar. Segundo Duckworth, Gendler & Gross (2016), qual é a correção mais inteligente?',
    dilemmaOptions: [
      'Continuar com o celular no travesseiro e se xingar por não ter força de vontade sobre-humana.',
      'Inverter a arquitetura de atrito do ambiente: deixar o celular fora do alcance da cama e deixar o livro/caderno já aberto sobre a mesa na noite anterior.',
      'Desistir de estudar pela manhã para sempre.',
      'Comprar cinco livros novos e guardá-los também no fundo do armário.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Arquitetura digna da oficina de Stark! Não gaste força de vontade vencendo obstáculos que um ajuste físico de 30 segundos elimina para sempre.',
    feedbackTrap:
      'Confiar apenas em força de vontade bruta num ambiente desenhado para sabotar você é perder energia à toa.',
  },
  {
    id: 'estrat_18_profilaxia_nimzowitsch_antecipacao',
    trackId: 'ESTRATEGIA_SISTEMAS',
    trackTitle: 'Estratégia Realista, Exemplos Resolvidos & Execução',
    masteryTier: 2,
    title: 'Profilaxia Estratégica (Nimzowitsch): Cortar a Crise Antes que Ela Exista',
    subtitle: 'O amador apaga incêndios heroicamente; o estrategista retira o fósforo na véspera',
    mentorName: 'Aron Nimzowitsch, Maquiavel & Doctor Who',
    scientificSource:
      'Nimzowitsch (Meu Sistema, 1925 — Profilaxia); Maquiavel (O Príncipe, Cap. III — Diagnóstico precoce da tísica); Gollwitzer & Sheeran (2006)',
    readTimeSec: 65,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'No clássico imortal *Meu Sistema* (1925), o Grande Mestre Aron Nimzowitsch revolucionou o xadrez com a **Profilaxia**: antes de lançar seu próprio ataque, pergunte **"Qual é a ameaça ou plano que está prestes a nascer contra mim nos próximos 2 passos?"** e neutralize-o com um lance calmo e preventivo (como criar a janela `h6` para o Rei)! Cinco séculos antes, Maquiavel escreveu a mesma lei: no começo, o mal é difícil de notar mas **fácil de curar**; se deixado crescer até todos verem, fica fácil de notar e quase impossível de curar!',
    whyItWorksMechanism:
      'A psicologia da autorregulação prospectiva (Duckworth et al., 2016; Gollwitzer, 2006) confirma que intervir **antes** do ponto crítico (fazer cópia de segurança antes do aparelho quebrar, revisar cláusula antes de assinar, descansar antes da lesão tendínea) exige 10% do esforço de consertar uma catástrofe consumada.',
    zeroStepExample:
      'Olhe para as próximas 48 horas da sua semana e pergunte como num tabuleiro: "Onde está o furo óbvio que vai dar dor de cabeça na sexta-feira se eu não fizer um ajuste de 5 minutos hoje?".',
    practicalActionToday:
      'Execute hoje 1 "lance profilático" na sua vida (backup dos dados da FORJA, revisão de conta, preparo antecipado) E pratique a Lição de Profilaxia na aba XADREZ!',
    fieldMission:
      'Neutralize hoje 1 problema previsível enquanto ele ainda é minúsculo, antes que vire urgência.',
    dilemmaPrompt:
      'O que une o conceito de Profilaxia de Aron Nimzowitsch no xadrez à máxima médica citada por Maquiavel no Capítulo III de O Príncipe?',
    dilemmaOptions: [
      'Esperar o desastre acontecer para ganhar aplausos apagando o incêndio.',
      'Atacar de olhos fechados ignorando completamente as ameaças do adversário e do ambiente.',
      'Antecipar ameaças emergentes enquanto ainda são pequenas e neutralizá-las preventivamente com baixo custo, impedindo que a crise ganhe força.',
      'Ficar paralisado com medo de agir e nunca desenvolver nenhuma peça.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Visão de Grande Mestre! As crises mais bem vencidas da sua vida serão aquelas que nunca chegaram a explodir porque você jogou `h6` três lances antes.',
    feedbackTrap:
      'Viver apenas apagando incêndios urgentes é sintoma de zero pensamento profilático; olhe dois lances à frente.',
  },
  {
    id: 'estrat_19_arquitetura_modular_relojoeiros_simon',
    trackId: 'ESTRATEGIA_SISTEMAS',
    trackTitle: 'Estratégia Realista, Exemplos Resolvidos & Execução',
    masteryTier: 3,
    title: 'Os Dois Relojoeiros de Herbert Simon: Salvar Pontos de Controle Modulares',
    subtitle: 'Por que montar sub-módulos estáveis vence por 4.000 a 1 quem tenta fazer tudo de uma vez',
    mentorName: 'Herbert Simon (Nobel) & Tony Stark',
    scientificSource:
      'Simon (Proceedings of the American Philosophical Society, 1962, 106(6), 467–482 — The Architecture of Complexity)',
    readTimeSec: 65,
    recommendedZone: 'AMARELO',
    coreEssence:
      'No clássico imortal *A Arquitetura da Complexidade* (1962), o Nobel Herbert Simon conta a parábola de dois relojoeiros que montavam relógios de 1.000 peças: **Tempus** montava as 1.000 peças numa sequência única — se o telefone tocasse na peça 990, o relógio inteiro desmontava na mesa e voltava ao zero! Já **Hora** montava **subconjuntos estáveis de 10 peças**: se o telefone tocasse, perdia no máximo 5 pecinhas, jamais os subconjuntos prontos! Simon calculou: com apenas 1% de chance de interrupção por peça, **Hora produz 4.000 relógios para cada 1 de Tempus**!',
    whyItWorksMechanism:
      'No mundo real cheio de interrupções (família, emergências, cansaço), projetos monolíticos gigantes ("só vale se eu tiver 5 horas ininterruptas!") quebram toda semana como o relógio de Tempus! Quando você divide qualquer meta em **módulos autocontidos de 20 minutos que travam no lugar assim que concluídos** (1 função testada, 1 ficha resumida, 1 lição fechada), nenhuma interrupção destrói seu avanço acumulado.',
    zeroStepExample:
      'Ao estudar ou trabalhar hoje, feche "pontos de salvamento" a cada 20–25 minutos (1 resumo salvo, 1 exercício concluído, 1 módulo gravado) que fiquem 100% prontos mesmo se alguém chamar você.',
    practicalActionToday:
      'Quebre seu maior projeto atual em subconjuntos independentes "estilo Hora" para nunca perder a manhã inteira quando surgir uma interrupção.',
    fieldMission:
      'Elimine hoje a desculpa "não começo porque não tenho 3 horas livres": monte e trave 2 módulos limpos de 20 minutos.',
    dilemmaPrompt:
      'Na matemática da Parábola de Tempus e Hora de Herbert Simon (1962), por que o relojoeiro Hora prosperou enquanto Tempus faliu tendo exatamente a mesma habilidade manual?',
    dilemmaOptions: [
      'Porque Hora construía sub-módulos intermediários estáveis ("pontos de salvamento"), de modo que qualquer interrupção externa custava apenas minutos locais em vez de desmontar o projeto inteiro.',
      'Porque Hora nunca atendia clientes nem tinha imprevistos.',
      'Porque relógios sem peças internas funcionam melhor.',
      'Porque projetos gigantes só dão certo quando feitos de uma tacada só sem salvar etapas.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Arquitetura da Complexidade de Nobel! Construa a vida em blocos modulares travados — imprevistos só arranham os últimos 5 minutos, nunca sua obra.',
    feedbackTrap:
      'Depender de dias perfeitos sem interrupções transforma você em Tempus: um único telefonema derruba tudo de volta à estaca zero.',
  },
  {
    id: 'estrat_20_portas_reversiveis_velocidade_assimetrica',
    trackId: 'ESTRATEGIA_SISTEMAS',
    trackTitle: 'Estratégia Realista, Exemplos Resolvidos & Execução',
    masteryTier: 4,
    title: 'Portas de Mão Única vs. Mão Dupla: Velocidade Assimétrica nas Decisões',
    subtitle: 'Frear fundo no irreversível e decidir em minutos tudo o que pode ser desfeito',
    mentorName: 'Tony Stark & Kathleen Eisenhardt (Stanford)',
    scientificSource:
      'Eisenhardt (Academy of Management Journal, 1989 — Making Fast Strategic Decisions in High-Velocity Environments); Teoria de Opções Reais (Dixit & Pindyck, Princeton, 1994)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'O erro mais caro dos lentos é tratar toda escolha como um casamento vitalício; o erro mais caro dos imprudentes é tratar decisões vitais como troca de camisa! Separe instantaneamente toda decisão em dois tipos: **Tipo 1 (Porta de Mão Única — Irreversível ou caríssima de desfazer:** casar, assinar dívida longa, cirurgia eletiva, quebrar confiança ética) -> **exija calma, dados frios e noite de sono**; **Tipo 2 (Porta de Mão Dupla — Reversível:** testar um método de estudo, publicar um protótipo, mudar layout, experimentar um horário) -> **decida com 70% dos dados em minutos e corrija andando!**',
    whyItWorksMechanism:
      'Kathleen Eisenhardt (Stanford, AMJ 1989) e Dixit & Pindyck (Princeton, 1994 — *Investment Under Uncertainty*) demonstraram que quando uma ação é facilmente reversível, o custo da demora supera de longe o custo de testar e voltar atrás; já quando há irreversibilidade alta, o valor matemático de esperar mais informação é imenso!',
    zeroStepExample:
      'Travado há 3 dias escolhendo qual caderno, linguagem inicial ou horário de treino testar? É Porta de Mão Dupla: escolha em 60 segundos hoje, teste 7 dias e ajuste se precisar!',
    practicalActionToday:
      'Classifique todas as pendências da sua lista hoje como [T1 Irreversível = Prudência Máxima] ou [T2 Reversível = Decisão Imediata em 2 Minutos].',
    fieldMission:
      'Destrave hoje 2 decisões reversíveis que estavam paradas por perfeccionismo E proteja 1 decisão irreversível contra pressa emocional.',
    dilemmaPrompt:
      'Uma pessoa gasta duas semanas angustiada escolhendo qual modelo de planilha gratuita testar (reversível em 5 minutos), mas assina um financiamento de 5 anos em 10 minutos por empolgação na loja (irreversível). Qual princípio de Dixit & Pindyck (1994) e Eisenhardt (1989) foi invertido?',
    dilemmaOptions: [
      'Deveria demorar dois meses para escolher a planilha gratuita e assinar o financiamento em 3 segundos.',
      'Toda decisão da vida deve levar exatamente o mesmo número de horas.',
      'Inverteu completamente a Reversibilidade: decisões reversíveis (Portas de Mão Dupla) exigem teste rápido e leve, enquanto compromissos irreversíveis (Portas de Mão Única) exigem freio deliberado e auditoria rigorosa.',
      'Nunca devemos testar nada reversível nem assinar nenhum contrato.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Calibração executiva perfeita! Rápido como raio no que é reversível, sólido como rocha no que é permanente.',
    feedbackTrap:
      'Usar processo pesado em escolhas reversíveis gera paralisia; usar pressa impulsiva no irreversível cobra anos de pedágio.',
  },

  // =========================================================================
  // PILAR 9: ANTIVIES & JULGAMENTO CRITICO (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'antivies_17_efeito_holofote_medo_julgamento',
    trackId: 'ANTIVIES_DECISAO',
    trackTitle: 'Antivieses, Julgamento Crítico & Calibração',
    masteryTier: 1,
    title: 'O Efeito Holofote (Gilovich): Ninguém Está Olhando Tanto Para o Seu Erro',
    subtitle: 'Destrave a timidez de iniciante descobrindo que cada pessoa só pensa em si mesma',
    mentorName: 'Thomas Gilovich (Cornell)',
    scientificSource:
      'Gilovich, Medvec & Savitsky (Journal of Personality and Social Psychology, 2000 — The Spotlight Effect in Social Judgment)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Quantos jovens deixam de ir treinar, tirar uma dúvida na aula, falar em público ou praticar inglês porque morrem de medo: "Todo mundo vai reparar que sou iniciante e rir de mim!"? Thomas Gilovich colocou estudantes com uma camiseta constrangedora numa sala cheia e mediu quantos realmente notaram: os alunos juravam que ~50% da sala tinha reparado, quando na verdade **menos da metade disso sequer notou**! É o **Efeito Holofote**.',
    whyItWorksMechanism:
      'Em JPSP (2000), Gilovich, Medvec e Savitsky demonstraram que como nós vivemos 24h dentro da nossa própria cabeça, projetamos erroneamente que há um holofote de teatro apontado para cada gaguejada ou erro nosso — esquecendo que 95% das pessoas ao redor estão ocupadas demais preocupadas com os próprios boletos e inseguranças!',
    zeroStepExample:
      'Com vergonha de fazer uma pergunta básica ou treinar como iniciante hoje? Lembre-se de Gilovich: em 5 minutos todo mundo já esqueceu, mas a habilidade que você ganha fica para o resto da vida!',
    practicalActionToday:
      'Faça hoje 1 coisa construtiva que você vinha evitando por "vergonha do que vão pensar" (tirar dúvida, treinar, gravar um teste de fala ou mostrar seu trabalho).',
    fieldMission:
      'Aceite parecer iniciante com leveza hoje para poder ser mestre amanhã — desligando o holofote imaginário.',
    dilemmaPrompt:
      'Um iniciante evita praticar conversação ou ir treinar porque sente que toda a sala está observando e julgando cada movimento dele. O que os experimentos de Gilovich, Medvec & Savitsky (JPSP, 2000) provam?',
    dilemmaOptions: [
      'Realmente todas as pessoas da sala passam o dia inteiro analisando e anotando nossos pequenos erros.',
      'Superestimamos em cerca do dobro o quanto os outros reparam em nossos tropeços (Efeito Holofote), pois cada pessoa está absorvida nas próprias preocupações.',
      'A única solução é nunca tentar nada novo na frente de ninguém.',
      'Só devemos agir quando tivermos certeza de acertar 100% na primeira tentativa.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Liberdade imediata! Quando você descobre que ninguém está com uma lupa apontada para você, sobra coragem para praticar e evoluir rápido.',
    feedbackTrap:
      'O holofote gigante existe apenas dentro da sua imaginação egocêntrica; dê o passo sem medo de parecer aprendiz.',
  },
  {
    id: 'antivies_18_erro_atribuicao_fundamental_ross',
    trackId: 'ANTIVIES_DECISAO',
    trackTitle: 'Antivieses, Julgamento Crítico & Calibração',
    masteryTier: 2,
    title: 'O Erro Fundamental de Atribuição (Lee Ross): Inverter a Lente Dupla',
    subtitle: 'Quando eu atraso foi o trânsito; quando o outro atrasa "ele é irresponsável"',
    mentorName: 'Lee Ross (Stanford)',
    scientificSource:
      'Ross (Advances in Experimental Social Psychology, 1977, 10, 173–220 — The Intuitive Psychologist and His Shortcomings); Jones & Nisbett (1971)',
    readTimeSec: 65,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Lee Ross (Stanford, 1977) batizou uma das distorções mais universais da mente humana: quando **OUTRA PESSOA** tropeça, nosso cérebro culpa automaticamente o caráter dela ("é preguiçoso, maldoso, incompetente") ignorando o contexto; quando **NÓS** cometemos o exato mesmo tropeço, culpamos automaticamente o contexto ("dormi mal, o sistema travou, ninguém avisou") protegendo nosso ego!',
    whyItWorksMechanism:
      'Jones e Nisbett (1971) mostraram a causa perceptual: quando olhamos o outro, a pessoa ocupa todo o nosso campo visual e suas pressões invisíveis ficam ocultas; quando olhamos para nós, enxergamos apenas os obstáculos na nossa frente! O Polímata **inverte deliberadamente essa equação**: seja generoso investigando o contexto/sistema quando julgar o outro, e seja rigoroso assumindo responsabilidade própria quando julgar a si mesmo!',
    zeroStepExample:
      'Alguém respondeu seco ou atrasou algo hoje? Antes de rotular "pessoa ruim", pergunte por 5 segundos: "Que pressão invisível ou falha de processo pode estar acontecendo do lado de lá?".',
    practicalActionToday:
      'Pratique a Inversão de Ross hoje: zero desculpas circunstanciais para seus próprios deveres + investigação serena das causas sistêmicas antes de condenar alguém.',
    fieldMission:
      'Substitua hoje 1 julgamento apressado de caráter alheio por uma pergunta objetiva de diagnóstico ("Aconteceu algum imprevisto no processo?").',
    dilemmaPrompt:
      'Quando um colega erra uma entrega pela primeira vez, você pensa "Ele é desleixado"; no dia seguinte você comete o mesmo erro e pensa "Foi só porque meu dia estava caótico". Como Lee Ross (1977) define esse fenômeno e como corrigi-lo?',
    dilemmaOptions: [
      'Erro Fundamental de Atribuição: superestimar falhas de personalidade nos outros e circunstâncias em nós; corrige-se investigando o contexto/processo no erro alheio e cobrando responsabilidade no próprio agir.',
      'Sinal de inteligência superior que nunca precisa ser revisado.',
      'Prova de que nossos erros nunca têm consequência real.',
      'A melhor correção é culpar o trânsito pelos erros de todo mundo e nunca consertar nada.',
    ],
    correctOptionIndex: 0,
    feedbackCorrect:
      'Justiça cognitiva impecável! Rigor consigo mesmo e diagnóstico lúcido do contexto com o próximo evitam conflitos inúteis e consertam sistemas reais.',
    feedbackTrap:
      'Ser advogado indulgente de si mesmo e juiz implacável dos outros destrói a liderança e cega o autodesenvolvimento.',
  },
  {
    id: 'antivies_19_vies_omissao_inercia_status_quo',
    trackId: 'ANTIVIES_DECISAO',
    trackTitle: 'Antivieses, Julgamento Crítico & Calibração',
    masteryTier: 3,
    title: 'Viés de Omissão & Status Quo: "Não Decidir" Já É Escolher o Pior Cenário',
    subtitle: 'Por que o cérebro perdoa desastres causados pela paralisia mais do que pequenos riscos de agir',
    mentorName: 'Jonathan Baron & Richard Zeckhauser (Harvard)',
    scientificSource:
      'Ritov & Baron (Journal of Behavioral Decision Making, 1990 — Reluctance to Vaccinate: Omission Bias); Samuelson & Zeckhauser (Journal of Risk and Uncertainty, 1988 — Status Quo Bias)',
    readTimeSec: 65,
    recommendedZone: 'AMARELO',
    coreEssence:
      'Se ficar parado num hábito ruim dá **20% de risco de dano grave** e mudar de rota dá apenas **2% de risco**, qualquer computador escolhe mudar na hora — mas milhões de seres humanos ficam parados! Ilana Ritov e Jonathan Baron (1990) provaram o **Viés de Omissão**: o cérebro sente culpa muito maior por um erro vindo de uma **ação nova** do que por um desastre 10 vezes maior vindo de **cruzar os braços e deixar como está** (*Status Quo*, Samuelson & Zeckhauser, 1988)!',
    whyItWorksMechanism:
      'Moral e matematicamente na física da realidade, **continuar parado no caminho atual É UMA ESCOLHA ATIVA todos os dias**, com todas as suas consequências acumuladas (sedentarismo silencioso, inflação corroendo dinheiro parado, dente sem tratar, carreira estagnada)! Quando você coloca o "Custo de Não Fazer Nada em 3 Anos" na mesma balança, o feitiço da inércia quebra.',
    zeroStepExample:
      'Adiando um check-up, conversa necessária ou início de estudo por medo de desconforto? Escreva no papel: "Se eu não fizer NADA pelos próximos 2 anos, qual é o dano garantido que estou assinando hoje?".',
    practicalActionToday:
      'Julgue hoje a inércia com o mesmo rigor com que julga uma ação nova: calcule explicitamente o risco acumulado da omissão.',
    fieldMission:
      'Quebre hoje 1 inércia antiga onde o "deixar como está" estava cobrando pedágio invisível na sua saúde, mente ou finanças.',
    dilemmaPrompt:
      'Uma pessoa mantém seu dinheiro perdendo poder de compra garantido todo ano e adia exames preventivos porque tem medo de "tomar uma atitude e errar". O que Ritov & Baron (1990) e Samuelson & Zeckhauser (1988) revelam?',
    dilemmaOptions: [
      'Não tomar nenhuma decisão isenta o ser humano das consequências matemáticas da realidade.',
      'Sempre que houver 1% de risco numa ação, é melhor aceitar 50% de perda ficando parado.',
      'Viés de Omissão e Status Quo: a mente trata a paralisia como "neutra", esquecendo que não agir é uma decisão ativa que frequentemente carrega perda muito maior do que agir com prudência.',
      'Mudar qualquer coisa por mero tédio diário sem critério é sempre superior.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Despertar estratégico! Na realidade não existe botão de pausa neutro: ficar parado na trilha errada é caminhar para trás.',
    feedbackTrap:
      'Esconder-se atrás da omissão para não sentir desconforto de decidir cobra juros compostos contra você.',
  },
  {
    id: 'antivies_20_realismo_ingenuo_ponto_cego_pronin',
    trackId: 'ANTIVIES_DECISAO',
    trackTitle: 'Antivieses, Julgamento Crítico & Calibração',
    masteryTier: 4,
    title: 'Realismo Ingênuo & O Ponto Cego do Viés (Emily Pronin): Auditar a Própria Lente',
    subtitle: 'Saber o nome de 20 vieses nos outros não imuniza ninguém — porque o viés opera fora da consciência',
    mentorName: 'Emily Pronin (Princeton) & Lee Ross',
    scientificSource:
      'Pronin, Lin & Ross (Personality and Social Psychology Bulletin, 2002 — The Bias Blind Spot); West, Meserve & Stanovich (JPSP, 2012 — Inteligência não reduz o ponto cego!)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Eis a armadilha final até dos mais inteligentes: estudar pensamento crítico e passar a enxergar vieses em **todo mundo ao redor**, jurando "Eu enxergo a realidade pura como ela é; quem discorda de mim ou não tem dados ou tem má-fé!" (**Realismo Ingênuo**). Emily Pronin (Princeton, 2002) e Stanovich (JPSP, 2012) provaram algo humilhante: **pessoas com alto QI sofrem um Ponto Cego do Viés (*Bias Blind Spot*) TÃO GRANDE ou MAIOR que a média**!',
    whyItWorksMechanism:
      'Por que até gênios caem nisso (Pronin, 2002)? Pela **Ilusão da Introspecção**: como os vieses operam de forma inconsciente, quando você olha "para dentro de si procurando preconceito" você não vê nada ("minha intenção parece limpa!") e conclui que é neutro! O único antídoto real nunca é "olhar os próprios sentimentos" — é submeter-se a **regras externas cegas, dados objetivos, Revisão do Motor e contraditório leal**!',
    zeroStepExample:
      'Assim como no Xadrez você aceita humildemente quando o Motor mostra que seu "lance genial" era na verdade uma Capivarada (`??`), aceite dados objetivos quando contradisserem sua opinião favorita!',
    practicalActionToday:
      'Proíba a frase "eu sou imune a vieses": confie em protocolos externos (Tribunal de Brier, números escritos e fontes primárias) em vez da sensação interna de certeza.',
    fieldMission:
      'Identifique hoje 1 assunto em que você tinha 100% de certeza emocional e pergunte honestamente: "Que prova factual concreta me faria mudar de ideia aqui?".',
    dilemmaPrompt:
      'Por que os experimentos de Emily Pronin (2002) e West, Meserve & Stanovich (JPSP, 2012) descobriram que pessoas muito inteligentes continuam caindo no Ponto Cego do Viés quando confiam apenas na autoanálise interna?',
    dilemmaOptions: [
      'Porque pessoas inteligentes não sabem ler gráficos.',
      'Porque vieses cognitivos nunca acontecem com quem estuda psicologia.',
      'Porque toda discordância humana prova má-fé do outro lado.',
      'Porque os vieses atuam abaixo da consciência (Ilusão de Introspecção): procurar viés "sentindo a própria mente" sempre dá negativo, exigindo ferramentas externas objetivas, métricas e contraditório real.',
    ],
    correctOptionIndex: 3,
    feedbackCorrect:
      'Humildade epistêmica máxima! O Polímata não confia na vaidade da própria lente — confia na balança calibrada dos fatos e protocolos.',
    feedbackTrap:
      'Achar-se imune ao autoengano por ser inteligente é exatamente a porta de entrada para os maiores erros de pessoas brilhantes.',
  },

  // =========================================================================
  // PILAR 10: HARDWARE HUMANO & LONGEVIDADE (LICOES 17 A 20 • GRAUS I–IV)
  // =========================================================================
  {
    id: 'corpo_17_dose_resposta_passos_lancet_paluch',
    trackId: 'CORPO_LONGEVIDADE',
    trackTitle: 'Fisiologia Inteligente: Força, Fôlego, Sono & Energia',
    masteryTier: 1,
    title: 'A Verdadeira Curva dos Passos Diários (Lancet 2022): Sem Mitos dos 10.000',
    subtitle: 'Sair de 3.500 para 7.000–9.000 passos por dia já corta a mortalidade quase pela metade',
    mentorName: 'Amanda Paluch (Steps for Health Collaborative)',
    scientificSource:
      'Paluch et al. (The Lancet Public Health, 2022, 7(3), e219–e228 — Meta-análise de 15 coortes internacionais, N = 47.471, 297.837 pessoas-ano)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'De onde veio o número mágico "10.000 passos"? De uma campanha publicitária japonesa de um pedômetro em 1965 (*Manpo-kei*), não de um laboratório! Quando a colaboração mundial liderada por Amanda Paluch reuniu 15 grandes coortes com **47.471 pessoas** no *The Lancet Public Health* (2022), a verdade científica foi muito mais encorajadora para quem começa do zero: sair do sedentarismo (~3.500 passos) para **6.000–8.000 passos** (acima de 60 anos) ou **8.000–10.000 passos** (abaixo de 60 anos) reduziu a mortalidade por todas as causas em **40% a 53%**!',
    whyItWorksMechanism:
      'A curva dose-resposta é fortíssima nos primeiros milhares de passos extras! Adicionar apenas 20 a 30 minutos de caminhada distribuídos pelo dia (~2.500 a 3.500 passos a mais) ativa a bomba muscular da panturrilha, limpa glicose e triglicerídeos circulantes sem estressar articulações nem exigir academia cara.',
    zeroStepExample:
      'Está totalmente sedentário hoje? Não desista achando "10 mil ou nada": faça 2 caminhadas simples de 12 minutos hoje (manhã e fim de tarde) — o salto inicial entrega o maior retorno por minuto!',
    practicalActionToday:
      'Some hoje pelo menos 20 minutos extras de caminhada a pé (indo resolver algo a pé, subindo escada ou andando após refeição).',
    fieldMission:
      'Alcance hoje a faixa protetora de movimento diário sem ficar sentado mais de 90 minutos ininterruptos.',
    dilemmaPrompt:
      'Um iniciante sedentário (~3.000 passos/dia) desiste de caminhar porque acha que "se não bater 10.000 passos todo dia não adianta nada". O que a meta-análise de Paluch et al. (The Lancet Public Health, 2022, N = 47.471) demonstra?',
    dilemmaOptions: [
      'Abaixo de 10.000 passos exatos o benefício cardiovascular realmente é zero.',
      'O maior ganho proporcional acontece logo ao sair do sedentarismo (subir de ~3.500 para 5.800–8.000+ passos já reduz a mortalidade em 40%–53%), sem qualquer regra de tudo-ou-nada.',
      'Caminhar mais de 4.000 passos faz mal para adultos jovens.',
      'Apenas maratonas acima de 30 km trazem benefício mensurável à longevidade.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Ciência pura sem terrorismo fitness! Cada bloco de 2.000 passos que tira você da cadeira colhe dividendos biológicos gigantescos.',
    feedbackTrap:
      'O mito do "10 mil ou nada" paralisa quem mais ganharia saúde com 25 minutos diários de caminhada firme.',
  },
  {
    id: 'corpo_18_fisiologia_ocular_foco_infinito',
    trackId: 'CORPO_LONGEVIDADE',
    trackTitle: 'Fisiologia Inteligente: Força, Fôlego, Sono & Energia',
    masteryTier: 2,
    title: 'Fisiologia Ocular & Infinito Óptico: Protegendo Seus Olhos na Era das Telas',
    subtitle: 'Encarar tela a 35 cm contrai o músculo ciliar sem trégua e corta as piscadas por 3',
    mentorName: 'Kathryn Rose & James Wolffsohn',
    scientificSource:
      'Sheppard & Wolffsohn (BMJ Open Ophthalmology, 2018 — Digital Eye Strain); Rose et al. (Ophthalmology, 2008 — Outdoor Activity Reduces Prevalence of Myopia)',
    readTimeSec: 60,
    recommendedZone: 'QUALQUER',
    coreEssence:
      'Um erro silencioso de quem estuda horas a fio: esquecer que os olhos usam um músculo real (**músculo ciliar**) que fica **contraído continuamente** para focar objetos a menos de 50 cm, enquanto só relaxa completamente quando você olha para longe (acima de **6 metros — o infinito óptico**)! Pior: diante de telas, nossa taxa natural de piscadas despenca de ~15–18 para apenas **~5 piscadas por minuto**, ressecando o filme lacrimal e gerando dor de cabeça que parece "cansaço mental"!',
    whyItWorksMechanism:
      'Sheppard e Wolffsohn (*BMJ Open Ophthalmology*, 2018) documentam os mecanismos da Fadiga Ocular Digital, e o grande estudo de Kathryn Rose et al. (*Ophthalmology*, 2008) mostrou que tempo diário ao ar livre (luz natural + visão de longa distância) protege a saúde refrativa ocular. Relaxar o músculo ciliar a cada 20–30 minutos olhando o horizonte distante por 20–30 segundos preserva nitidez e elimina cefaleia tensional de estudo.',
    zeroStepExample:
      'Agora mesmo, ao terminar esta lição, tire os olhos da tela por 20 segundos, olhe para o objeto mais distante pela janela (>6 metros) e dê 5 piscadas completas e suaves!',
    practicalActionToday:
      'Mantenha o celular/monitor a pelo menos 40–50 cm dos olhos com brilho compatível ao ambiente, e relaxe o foco no horizonte distante a cada bloco de estudo.',
    fieldMission:
      'Proteja seu hardware visual hoje combinando distância ergonômica de leitura + pausas de foco a mais de 6 metros + tempo ao ar livre.',
    dilemmaPrompt:
      'Após 2 horas estudando com o rosto a 25 cm do celular sem parar, um estudante sente ardência ocular, visão turva ao levantar a cabeça e dor frontal. Qual é a causa fisiológica e o ajuste correto (Sheppard & Wolffsohn, 2018)?',
    dilemmaOptions: [
      'O cérebro gastou todos os neurônios do dia; a única saída é parar de ler livros.',
      'Espasmo de acomodação do músculo ciliar em foco curto somado à queda de ~66% na taxa de piscadas; corrige-se afastando a tela (40–50 cm), piscando completamente e olhando a >6 metros regularmente.',
      'Aproximar a tela para 12 cm do nariz para forçar menos os olhos.',
      'Apagar todas as luzes do quarto e colocar o brilho da tela em 100% no escuro.',
    ],
    correctOptionIndex: 1,
    feedbackCorrect:
      'Manutenção fina do hardware visual! Quem vai ler e calcular por 70 anos trata os olhos como lentes de precisão.',
    feedbackTrap:
      'Travar o músculo ciliar a 25 cm no escuro gera fadiga evitável que derruba o rendimento intelectual.',
  },
  {
    id: 'corpo_19_potencia_muscular_velocidade_fibra',
    trackId: 'CORPO_LONGEVIDADE',
    trackTitle: 'Fisiologia Inteligente: Força, Fôlego, Sono & Energia',
    masteryTier: 3,
    title: 'Potência Muscular (Força × Velocidade): Blindando Fibras Rápidas e Reflexos',
    subtitle: 'Com a idade perdemos velocidade o dobro mais rápido que força — treine intenção ágil',
    mentorName: 'Claudio Gil Araújo & Roger Fielding',
    scientificSource:
      'Reid & Fielding (Exercise and Sport Sciences Reviews, 2012 — Muscle Power and Aging); Araújo et al. (European Journal of Preventive Cardiology / CLINIMEX — Potência muscular relativa e sobrevida)',
    readTimeSec: 65,
    recommendedZone: 'VERDE',
    coreEssence:
      'Existe uma diferença vital entre **Força** (empurrar algo pesado bem devagar) e **Potência** (**Força × Velocidade** — produzir força rápido, como levantar-se da cadeira com agilidade, subir degraus firmes ou recuperar o equilíbrio num tropeço!). A fisiologia descobriu que as fibras musculares rápidas (Tipo II) atrofiam muito antes das lentas se nunca forem recrutadas — e a Potência Muscular prediz independência funcional e longevidade até melhor que a força lenta isolada!',
    whyItWorksMechanism:
      'Reid e Fielding (2012) e a coorte brasileira CLINIMEX liderada por Claudio Gil Araújo demonstraram que treinar a fase concêntrica ("a subida" do agachamento ou flexão) com **intenção rápida e controlada**, seguida por uma descida (excêntrica) calma de 2 segundos, recruta unidades motoras de alto limiar sem precisar de cargas perigosas nas articulações!',
    zeroStepExample:
      'Na sua série de agachamentos ou flexões hoje (após aquecer bem!), desça controlando em 2 segundos e SUBA com firmeza e velocidade limpa, mantendo postura perfeita.',
    practicalActionToday:
      'Aplique "descida controlada de 2s + subida ágil intencional" nas repetições técnicas do seu treino de força na aba FORJA hoje (sempre respeitando RIR 2!).',
    fieldMission:
      'Preserve suas fibras rápidas hoje combinando controle total na descida com intenção vigorosa na subida, zero tranco articular.',
    dilemmaPrompt:
      'Como treinar Potência Muscular com total segurança articular segundo Reid & Fielding (2012) para proteger fibras Tipo II e reflexos motores ao longo da vida?',
    dilemmaOptions: [
      'Aposentar qualquer movimento ágil depois dos 25 anos e mover-se sempre em câmera lenta.',
      'Jogar pesos máximos acima da capacidade com a coluna torta e sem aquecimento.',
      'Após aquecimento dinâmico, controlar a fase de descida com estabilidade (2s) e executar a subida com intenção rápida e técnica limpa, mantendo repetições na reserva (RIR).',
      'Fazer apenas alongamento passivo sentado sem nunca contrair músculos.',
    ],
    correctOptionIndex: 2,
    feedbackCorrect:
      'Biomecânica inteligente! Descida controlada protege o tendão; subida intencional acorda os neurônios motores rápidos.',
    feedbackTrap:
      'Nem tranco descontrolado nem lentidão eterna: una controle excêntrico com intenção concêntrica limpa.',
  },
  {
    id: 'corpo_20_reserva_cognitiva_bdnf_aerobico',
    trackId: 'CORPO_LONGEVIDADE',
    trackTitle: 'Fisiologia Inteligente: Força, Fôlego, Sono & Energia',
    masteryTier: 4,
    title: 'Exercício Aeróbico, BDNF & Crescimento Real do Hipocampo',
    subtitle: 'Corpo e mente são um único órgão integrado: caminhar vigoroso faz o centro da memória crescer',
    mentorName: 'Kirk Erickson & Arthur Kramer',
    scientificSource:
      'Erickson, Voss, Prakash et al. (PNAS, 2011, 108(7), 3017–3022 — Exercise training increases size of hippocampus and improves memory, N = 120 RCT)',
    readTimeSec: 70,
    recommendedZone: 'VERDE',
    coreEssence:
      'Durante décadas acreditou-se que o cérebro adulto só encolhia inevitavelmente ano após ano (~1%–2% por ano no hipocampo após os 55 anos). Em um ensaio clínico controlado histórico publicado na *PNAS* (2011), Kirk Erickson e Arthur Kramer dividiram 120 adultos e provaram por ressonância magnética de alta resolução: **3 sessões semanais de caminhada aeróbica moderada AUMENTARAM o volume do hipocampo anterior em +2%**, revertendo de 1 a 2 anos de envelhecimento cerebral e melhorando a memória espacial!',
    whyItWorksMechanism:
      'No estudo da PNAS (2011), o ganho real de volume hipocampal esteve diretamente ligado à elevação sérica de **BDNF (*Brain-Derived Neurotrophic Factor*)** — literalmente o "adubo neurotrófico" que estimula angiogênese, sinaptogênese e sobrevivência de novos neurônios no giro denteado! Quando você une **exercício aeróbico (que libera BDNF)** com **desafio cognitivo exigente (Academia, Córtex e Xadrez, que guiam onde fixar as novas sinapses)**, você atinge o ápice da neuroplasticidade humana!',
    zeroStepExample:
      'Faça hoje a dupla de ouro da neuroplasticidade: 25–30 minutos de caminhada/cardio em Zona 2 seguidos por 1 lição profunda ou partida pensada na FORJA!',
    practicalActionToday:
      'Trate seu treino aeróbico de hoje não apenas como gasto calórico, mas como dose direta de BDNF para blindar seu hipocampo e sua memória.',
    fieldMission:
      'Complete hoje o ciclo fechado Corpo + Córtex da FORJA: movimento aeróbico oxigenando o cérebro + desafio intelectual consolidando novas conexões.',
    dilemmaPrompt:
      'No ensaio clínico randomizado de 1 ano de Erickson et al. (PNAS, 2011), o que aconteceu na ressonância magnética cerebral do grupo que praticou caminhada aeróbica moderada 3x por semana?',
    dilemmaOptions: [
      'O volume do hipocampo diminuiu mais rápido que no grupo sedentário.',
      'Não houve nenhuma diferença mensurável nem em BDNF nem em memória.',
      'Apenas os músculos das pernas mudaram, pois o cérebro adulto não possui plasticidade estrutural.',
      'O hipocampo anterior AUMENTOU de volume em cerca de +2% (revertendo 1–2 anos de perda etária), acompanhado de maiores níveis de BDNF e melhor memória espacial.',
    ],
    correctOptionIndex: 3,
    feedbackCorrect:
      'Coroação da Edição do Bicentenário (Lição 200/200)! Corpo ativo regando o cérebro com BDNF, mente afiada forjando sinapses e caráter firmado na Rocha — a síntese completa do Polímata!',
    feedbackTrap:
      'Separar corpo e intelecto é um erro biológico; movimento aeróbico + estudo deliberado constroem juntos um cérebro resiliente por toda a vida.',
  },
];

export const BICENTENARY_40_TIER_MAP: Record<string, MasteryTier> = Object.fromEntries(
  TEACHINGS_BICENTENARY_40.map((lesson) => [lesson.id, lesson.masteryTier ?? 1]),
) as Record<string, MasteryTier>;

