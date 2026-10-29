import { clamp } from './stateEngine';
import { TeachingTrackId } from './types';

export interface MasteryAttributes {
  carater: number;      // 0..100 Carater, Sabedoria Biblica, Perdao & Servico
  vigor: number;        // 0..100 Corpo, Energia & Sono
  aprendizado: number;  // 0..100 Meta-Aprendizagem, Foco & Memoria
  autogoverno: number;  // 0..100 Vontade, Regulacao Emocional & Domínio Proprio
  retorica: number;     // 0..100 Comunicacao, Escrita & Inteligencia Social
  estrategia: number;   // 0..100 Logica, Numeros, Financas & Sistemas
}

export interface SimulatorOption {
  label: string;
  isMasterChoice: boolean;
  deltas: MasteryAttributes;
  consequenceTitle: string;
  consequenceNarrative: string;
}

export interface SimulatorChapter {
  id: string;
  chapterNumber: number;
  timeHorizonLabel: string;
  title: string;
  scenarioContext: string;
  corePillarId: TeachingTrackId;
  linkedLessonId: string;
  scientificAnchor: string;
  options: [SimulatorOption, SimulatorOption, SimulatorOption, SimulatorOption];
}

export interface SimulatorRunState {
  currentChapterIndex: number;
  attributes: MasteryAttributes;
  history: {
    chapterId: string;
    chosenOptionIndex: number;
    wasMasterChoice: boolean;
  }[];
  completed: boolean;
}

export interface SimulatorFinalReport {
  score1000: number;
  masterDecisionsCount: number;
  totalChapters: number;
  rankTitle: string;
  rankSummary: string;
  weakestDimensionLabel: string;
  recommendedLessonIds: string[];
}

export const INITIAL_ZERO_ATTRIBUTES: MasteryAttributes = {
  carater: 10,
  vigor: 10,
  aprendizado: 10,
  autogoverno: 10,
  retorica: 10,
  estrategia: 10,
};

export const SIMULATOR_CHAPTERS: SimulatorChapter[] = [
  {
    id: 'cap_01_quarto_marco_zero',
    chapterNumber: 1,
    timeHorizonLabel: 'Dia 1 • O Despertar no Zero',
    title: 'O Quarto do Marco Zero & o Único Talento',
    scenarioContext:
      'Você tem zero habilidades desenvolvidas: está fora de forma, atrasado nos estudos, tímido, sem reserva financeira e com o celular apitando vídeos curtos. Ao pensar em tudo que precisa aprender, bate vergonha e vontade de enterrar seu potencial por medo. O que você faz nos próximos 10 minutos?',
    corePillarId: 'CRISTO_EVANGELHOS',
    linkedLessonId: 'cristo_02_fiel_no_pouco_talentos',
    scientificAnchor: 'Lucas 16:10 ("Fiel no pouco") + Sirois & Pychyl (2013): Vencer a Fuga Emocional',
    options: [
      {
        label:
          'Montar um cronograma perfeito de 12 horas por dia para "começar segunda que vem" e abrir vídeos curtos hoje.',
        isMasterChoice: false,
        deltas: { carater: -2, vigor: -2, aprendizado: 0, autogoverno: -4, retorica: 0, estrategia: -2 },
        consequenceTitle: 'Armadilha da Casa na Areia',
        consequenceNarrative:
          'Ouvir e planejar sem praticar nada hoje é edificar na areia (Mt 7:26). Na segunda, a meta de 12h parece impossível e você trava de novo.',
      },
      {
        label:
          'Olhar no espelho, xingar a si mesmo de inútil por 20 minutos achando que culpa pesada gera disciplina.',
        isMasterChoice: false,
        deltas: { carater: -2, vigor: 0, aprendizado: 0, autogoverno: -5, retorica: -2, estrategia: 0 },
        consequenceTitle: 'Curto-Circuito da Vergonha',
        consequenceNarrative:
          'Vergonha paralisa e faz enterrar o talento na terra (Mt 25:25), aumentando a busca impulsiva por anestesia nas telas.',
      },
      {
        label:
          'Ser "fiel no mínimo" em secreto (Lc 16:10): cortar a culpa, guardar o celular longe, tomar luz natural + água e cumprir 2 minutos reais agora (arrumar a mesa + 1 página + 1 série inclinada).',
        isMasterChoice: true,
        deltas: { carater: 12, vigor: 11, aprendizado: 9, autogoverno: 13, retorica: 5, estrategia: 9 },
        consequenceTitle: '1º Tijolo na Rocha & Ignição do vmPFC',
        consequenceNarrative:
          'Ao honrar o pequeno começo sem esperar aplauso nem perfeição, você venceu a inércia emocional e ligou o controle pré-frontal!',
      },
      {
        label:
          'Tentar aprender 6 áreas ao mesmo tempo com 15 abas abertas e música alta até travar de exaustão.',
        isMasterChoice: false,
        deltas: { carater: 0, vigor: -3, aprendizado: -3, autogoverno: 1, retorica: 0, estrategia: -3 },
        consequenceTitle: 'Colapso da Memória de Trabalho',
        consequenceNarrative:
          'Tentar carregar tudo de uma vez estoura o limite de 4 blocos da memória curta (Cowan) sem concluir nada.',
      },
    ],
  },
  {
    id: 'cap_02_parede_estudo',
    chapterNumber: 2,
    timeHorizonLabel: 'Semana 2 • A Primeira Habilidade Difícil',
    title: 'A Muralha do "Parece Grego Para Mim"',
    scenarioContext:
      'Você escolheu dominar sua primeira habilidade técnica difícil do zero (ex: matemática/programação/inglês). Nos primeiros 15 minutos, os termos parecem impossíveis e você não consegue resolver o exercício sozinho. Qual protocolo você aplica?',
    corePillarId: 'APRENDIZAGEM_MEMORIA',
    linkedLessonId: 'estrategia_06_exemplos_resolvidos_degrau_zero',
    scientificAnchor: 'Sweller & Cooper (1985): Exemplo Resolvido + Evocação Ativa (Rowland, 2014)',
    options: [
      {
        label:
          'Grifar o texto inteiro com 4 cores de marca-texto e reler 5 vezes seguidas sem fechar o livro.',
        isMasterChoice: false,
        deltas: { carater: 0, vigor: 0, aprendizado: -2, autogoverno: 2, retorica: 0, estrategia: -1 },
        consequenceTitle: 'Ilusão de Fluência Passiva',
        consequenceNarrative:
          'Dunlosky et al. (2013) provaram que grifar e reler têm baixíssima utilidade: o texto parece familiar aberto na sua frente, mas na hora da prova dá branco.',
      },
      {
        label:
          'Estudar passo a passo 1 Exemplo Resolvido entendendo o porquê de cada linha, fechar o material, resolver 1 problema gêmeo no papel e explicar com palavras simples.',
        isMasterChoice: true,
        deltas: { carater: 6, vigor: 4, aprendizado: 15, autogoverno: 9, retorica: 9, estrategia: 10 },
        consequenceTitle: 'Andaime 4C/ID + Teste de Feynman Ativados',
        consequenceNarrative:
          'Iniciantes aprendem até 6x mais rápido com Exemplo Resolvido seguido de evocação ativa sem olhar (Sweller & Cooper). O primeiro Chunk neural sólido nasceu!',
      },
      {
        label:
          'Concluir que "não tenho talento para exatas/técnica" e trocar de assunto a cada 3 dias.',
        isMasterChoice: false,
        deltas: { carater: -3, vigor: 0, aprendizado: -5, autogoverno: -4, retorica: 0, estrategia: -3 },
        consequenceTitle: 'Síndrome do Eterno Iniciante',
        consequenceNarrative:
          'Confundir falta temporária de Chunks neurais com "falta de dom" condena você a abandonar toda área antes da colheita (Gl 6:9).',
      },
      {
        label:
          'Copiar a resposta pronta da internet sem ler para sentir que terminou rápido.',
        isMasterChoice: false,
        deltas: { carater: -5, vigor: 0, aprendizado: -4, autogoverno: -3, retorica: 0, estrategia: -2 },
        consequenceTitle: 'Autoengano & Zero Mielinização',
        consequenceNarrative:
          'Sem esforço honesto de recuperação na memória, nenhuma sinapse nova é fortalecida.',
      },
    ],
  },
  {
    id: 'cap_03_corpo_degrau_zero',
    chapterNumber: 3,
    timeHorizonLabel: 'Mês 1 • O Hardware Físico',
    title: 'Vergonha na Barra & Dor de Iniciante',
    scenarioContext:
      'No treino físico, você ainda não aguenta fazer 1 barra fixa nem 5 flexões no chão, enquanto pessoas ao lado fazem 15 repetições fáceis. A tentação é desistir por vergonha ou jogar o corpo de mau jeito até falhar tudo. Como você treina?',
    corePillarId: 'CORPO_LONGEVIDADE',
    linkedLessonId: 'corpo_06_postura_movimento_base',
    scientificAnchor: 'Escada Biomecânica de Alavanca + Reserva RIR 2 (Robinson/Schoenfeld, 2024)',
    options: [
      {
        label:
          'Ajustar a alavanca com humildade sábia (flexão inclinada em banco/mesa + remada inclinada), foco externo e parar deixando 2 repetições limpas na reserva (RIR 2).',
        isMasterChoice: true,
        deltas: { carater: 8, vigor: 17, aprendizado: 7, autogoverno: 11, retorica: 4, estrategia: 9 },
        consequenceTitle: 'Adaptação Neural Limpa & Tendões Íntegros',
        consequenceNarrative:
          'Em 4 semanas, seu sistema nervoso sincroniza unidades motoras sem inflamar ombro ou cotovelo. Você desce a inclinação degrau por degrau e conquista suas primeiras flexões no chão!',
      },
      {
        label:
          'Forçar repetições tortas todo santo dia até a falha total, tomando energético às 22h.',
        isMasterChoice: false,
        deltas: { carater: -2, vigor: -8, aprendizado: -3, autogoverno: 1, retorica: 0, estrategia: -5 },
        consequenceTitle: 'Tendinite + Sono Destruído',
        consequenceNarrative:
          'Músculos adaptam rápido, mas tendões têm pouca vascularização (Magnusson/Kjaer). Uma dor no ombro para você por 3 semanas.',
      },
      {
        label:
          'Desistir do treino físico dizendo que "vou focar só na mente, corpo não importa".',
        isMasterChoice: false,
        deltas: { carater: -2, vigor: -6, aprendizado: -4, autogoverno: -3, retorica: -2, estrategia: -2 },
        consequenceTitle: 'Queda de BDNF e Energia Cerebral',
        consequenceNarrative:
          'Corpo e mente formam uma unidade viva: sem movimento vigoroso, caem o BDNF hipocampal e sua disposição à tarde.',
      },
      {
        label:
          'Fazer 3 horas de corrida exaustiva num único domingo e passar os outros 6 dias imóvel.',
        isMasterChoice: false,
        deltas: { carater: 0, vigor: -4, aprendizado: 0, autogoverno: -2, retorica: 0, estrategia: -3 },
        consequenceTitle: 'Pico Agudo de Carga Sem Base Crônica',
        consequenceNarrative:
          'Picos esporádicos geram dor tardia severa e risco articular sem construir mitocôndrias sustentáveis (Seiler 80/20).',
      },
    ],
  },
  {
    id: 'cap_04_arena_social',
    chapterNumber: 4,
    timeHorizonLabel: 'Mês 2 • Palavra, Leme da Língua & Limites',
    title: 'Coração a 130 BPM Diante da Sala',
    scenarioContext:
      'Surge sua primeira chance real de apresentar uma ideia para pessoas mais experientes — e, na véspera, conhecidos provocam você com deboche para largar sua disciplina. Suas mãos suam. Qual combinação você executa?',
    corePillarId: 'COMUNICACAO_SOCIAL',
    linkedLessonId: 'com_02_clareza_piramide_argumento',
    scientificAnchor: 'Tiago 1:19 & Pv 15:1 + Jamieson (Adrenalina Aliada) + van Gelder (Mapa de Argumento)',
    options: [
      {
        label:
          'Fingir doença para faltar à apresentação e ceder aos colegas para agradar o grupo.',
        isMasterChoice: false,
        deltas: { carater: -5, vigor: -2, aprendizado: -2, autogoverno: -6, retorica: -6, estrategia: -4 },
        consequenceTitle: 'Espírito de Covardia & Esquiva',
        consequenceNarrative:
          'Cada fuga ensina à amígdala que falar em público era mortal, dobrando o medo na próxima oportunidade.',
      },
      {
        label:
          'Explodir aos gritos com os colegas na véspera e ir apresentar sem estrutura nenhuma.',
        isMasterChoice: false,
        deltas: { carater: -5, vigor: 0, aprendizado: 0, autogoverno: -4, retorica: -5, estrategia: -3 },
        consequenceTitle: 'Língua Sem Freio (Tiago 3:5)',
        consequenceNarrative:
          'A palavra dura suscita a ira (Pv 15:1) e drena sua energia mental justamente na véspera do momento decisivo.',
      },
      {
        label:
          'Usar resposta branda e firme para dizer "não" na véspera, reler o batimento rápido como prontidão e abrir a fala direto pela Conclusão em 1 frase + 2 Provas concretas.',
        isMasterChoice: true,
        deltas: { carater: 10, vigor: 6, aprendizado: 9, autogoverno: 12, retorica: 20, estrategia: 11 },
        consequenceTitle: 'Domínio do Leme & Clareza Magnética',
        consequenceNarrative:
          'Manso e firme nos limites + cristalino no raciocínio: os veteranos escutam você com respeito imediato!',
      },
      {
        label:
          'Decorar palavras difíceis que você não entende para parecer superior.',
        isMasterChoice: false,
        deltas: { carater: -3, vigor: 0, aprendizado: -1, autogoverno: 0, retorica: -3, estrategia: -2 },
        consequenceTitle: 'Vaidade de Aparência',
        consequenceNarrative:
          'Na primeira pergunta simples da banca, o castelo de jargão desmonta. Verdade simples sempre vence afetação.',
      },
    ],
  },
  {
    id: 'cap_05_numeros_recursos',
    chapterNumber: 5,
    timeHorizonLabel: 'Mês 4 • Mordomia, Números & Armadilhas',
    title: 'Os Primeiros R$ 1.800 & o Canto da Sereia',
    scenarioContext:
      'Graças à sua diligência (Pv 21:5), você conquista seus primeiros R$ 1.800! No mesmo dia aparecem duas tentações: (A) parcelar um item caro de ostentação a 9% ao mês; ou (B) jogar tudo numa "dica secreta que dobra (+100%) sua chance!". Como um Mestre decide?',
    corePillarId: 'LOGICA_NUMERACIA',
    linkedLessonId: 'num_05_soberania_financeira_reserva',
    scientificAnchor: 'Gigerenzer (Frequências Naturais) + Regra dos 72 + Lusardi + Provérbios 21:5',
    options: [
      {
        label:
          'Parcelar o item de ostentação a 9% ao mês para "mostrar aos outros que venceu".',
        isMasterChoice: false,
        deltas: { carater: -3, vigor: 0, aprendizado: 0, autogoverno: -4, retorica: 0, estrategia: -8 },
        consequenceTitle: 'Servidão pela Regra dos 72',
        consequenceNarrative:
          'A 9% ao mês, a dívida dobra em 8 meses (72 ÷ 9 = 8) — "o que toma emprestado é servo do que empresta" (Pv 22:7).',
      },
      {
        label:
          'Apostar tudo na "dica que aumenta +100% a chance" buscando riqueza apressada.',
        isMasterChoice: false,
        deltas: { carater: -3, vigor: 0, aprendizado: -2, autogoverno: -4, retorica: 0, estrategia: -9 },
        consequenceTitle: 'Ruína da Pressa (Provérbios 21:5)',
        consequenceNarrative:
          'A chance real subiu de 1 em 500 para 2 em 500 — 498 em 500 perderam tudo. "Os planos do precipitado levam certamente à penúria".',
      },
      {
        label:
          'Examinar com Frequências Naturais e Regra dos 72, guardar 80% na Reserva de Paz e investir uma fração prudente em livros/ferramentas de trabalho honesto.',
        isMasterChoice: true,
        deltas: { carater: 9, vigor: 5, aprendizado: 10, autogoverno: 10, retorica: 5, estrategia: 20 },
        consequenceTitle: 'Mordomia Prudente & Soberania',
        consequenceNarrative:
          'Com colchão de segurança + ferramentas que elevam sua utilidade ao próximo, você conquista paz mental e liberdade de negociação!',
      },
      {
        label:
          'Não anotar nada e deixar o dinheiro sumir em pequenos gastos automáticos.',
        isMasterChoice: false,
        deltas: { carater: -2, vigor: 0, aprendizado: -1, autogoverno: -2, retorica: 0, estrategia: -4 },
        consequenceTitle: 'Vazamento Invisível de Fermi',
        consequenceNarrative:
          'Pequenos gastos impulsivos de R$ 20/dia drenam R$ 600 no mês sem construir autonomia.',
      },
    ],
  },
  {
    id: 'cap_06_plato_falha',
    chapterNumber: 6,
    timeHorizonLabel: 'Mês 6 • O Ferro Afia o Ferro',
    title: 'O Platô Brutal, o Erro & a Correção Dura',
    scenarioContext:
      'Sua evolução parece estagnar e um mentor experiente aponta sem rodeios uma falha séria no seu projeto. O orgulho dói na hora. O que separa o tolo do sábio neste exato minuto?',
    corePillarId: 'SABEDORIA_BIBLICA',
    linkedLessonId: 'biblia_05_ferro_afia_ferro_conselho',
    scientificAnchor: 'Provérbios 9:8–9 & 27:17 ("O ferro afia o ferro") + Mateus 7:3–5 + Ericsson',
    options: [
      {
        label:
          'Ficar ofendido, procurar amigos bajuladores que digam que você já é perfeito e continuar repetindo o mesmo jeito.',
        isMasterChoice: false,
        deltas: { carater: -6, vigor: 1, aprendizado: -3, autogoverno: -2, retorica: -3, estrategia: -2 },
        consequenceTitle: ' Platô do Ego Intocável',
        consequenceNarrative:
          'Quem rejeita correção leal troca crescimento real por carinho falso no ego — e estaciona no nível mediano para sempre.',
      },
      {
        label:
          'Esconder o erro e culpar três colegas pelas costas.',
        isMasterChoice: false,
        deltas: { carater: -9, vigor: 0, aprendizado: -4, autogoverno: -4, retorica: -6, estrategia: -4 },
        consequenceTitle: 'A Trave no Próprio Olho (Mateus 7:3)',
        consequenceNarrative:
          'Transferir culpa destrói seu caráter e sua credibilidade (Ethos) diante de toda pessoa séria.',
      },
      {
        label:
          'Tirar primeiro a trave do próprio olho, agradecer a correção leal ("dá instrução ao sábio e se fará mais sábio" — Pv 9:9) e atacar o ponto cego com 20 min diários de Prática Deliberada.',
        isMasterChoice: true,
        deltas: { carater: 12, vigor: 7, aprendizado: 15, autogoverno: 11, retorica: 12, estrategia: 12 },
        consequenceTitle: 'Ferro Afiado para o Nível Superior!',
        consequenceNarrative:
          'Sua humildade ensinável conquista a admiração do mentor e destrava um salto técnico que meses no piloto automático jamais dariam!',
      },
      {
        label:
          'Largar toda a área após 6 meses de suor só por causa de um tropeço.',
        isMasterChoice: false,
        deltas: { carater: -4, vigor: -2, aprendizado: -6, autogoverno: -6, retorica: -2, estrategia: -5 },
        consequenceTitle: 'Abandono Antes da Colheita',
        consequenceNarrative:
          'Você jogou fora 6 meses de construção neural justamente onde a maioria desiste.',
      },
    ],
  },
  {
    id: 'cap_07_tempestade_caos',
    chapterNumber: 7,
    timeHorizonLabel: 'Ano 1 • A Chuva e os Ventos',
    title: 'A Semana Impossível: Tudo Ao Mesmo Tempo',
    scenarioContext:
      'Estoura uma semana pesada com prazos acumulados, imprevisto familiar e ansiedade sobre o futuro — sobrando apenas 35 minutos livres no dia. Como atravessar a tempestade sem desabar?',
    corePillarId: 'ESTRATEGIA_SISTEMAS',
    linkedLessonId: 'cristo_04_basta_a_cada_dia_paz',
    scientificAnchor: 'Mateus 6:34 ("Basta a cada dia o seu mal") + Goldratt (Gargalo) + Piso Mínimo',
    options: [
      {
        label:
          'Cortar o sono para 3h por noite sofrendo por antecipação pelo ano inteiro.',
        isMasterChoice: false,
        deltas: { carater: -2, vigor: -10, aprendizado: -6, autogoverno: -4, retorica: -4, estrategia: -6 },
        consequenceTitle: 'Colapso por Ansiedade & Privação de Sono',
        consequenceNarrative:
          'Sem sono profundo, o córtex pré-frontal desliga e você leva 3 horas para fazer o que faria em 30 minutos descansado.',
      },
      {
        label:
          'Chutar o balde ("já que não dá para fazer 1h perfeita, vou zerar tudo por um mês").',
        isMasterChoice: false,
        deltas: { carater: -4, vigor: -7, aprendizado: -5, autogoverno: -7, retorica: -2, estrategia: -5 },
        consequenceTitle: 'Armadilha do Tudo-ou-Nada',
        consequenceNarrative:
          'Trinta dias de zero quebram o ritmo circadiano; bastava fidelidade no pouco para preservar toda a construção.',
      },
      {
        label:
          'Viver um dia de cada vez em paz (Mt 6:34), proteger o sono, atacar o Gargalo nº 1 sem celular e manter corpo/memória vivos com o Piso Mínimo de 5–15 min + gratidão.',
        isMasterChoice: true,
        deltas: { carater: 10, vigor: 15, aprendizado: 12, autogoverno: 13, retorica: 10, estrategia: 14 },
        consequenceTitle: 'Paz Sob Tempestade & Antifragilidade',
        consequenceNarrative:
          'Enquanto os ansiosos entram em colapso, sua mente renovada atravessa o furacão serena e inteira!',
      },
      {
        label:
          'Ficar pulando de 3 em 3 minutos entre WhatsApp, planilha e estudo em pânico.',
        isMasterChoice: false,
        deltas: { carater: 0, vigor: -3, aprendizado: -5, autogoverno: -2, retorica: -2, estrategia: -5 },
        consequenceTitle: 'Paralisia por Resíduo de Atenção',
        consequenceNarrative:
          'Trocas frenéticas de contexto reduzem sua precisão cognitiva em até 40% (Sophie Leroy).',
      },
    ],
  },
  {
    id: 'cap_08_prova_polimata',
    chapterNumber: 8,
    timeHorizonLabel: 'Ano 2 • Domínio Intelectual',
    title: 'O Desafio Inédito: Aprender o Desconhecido em 14 Dias',
    scenarioContext:
      'Surge uma missão multidisciplinar que nenhum curso pronto ensina inteira (misturando técnica nova, números, pessoas e decisão sob incerteza). Como acionar sua Máquina Universal de Aprender?',
    corePillarId: 'CIENCIA_PRIMEIROS_PRINCIPIOS',
    linkedLessonId: 'aprend_06_arquitetura_4cid_transferencia',
    scientificAnchor: 'Primeiros Princípios + Transferência Analógica (Gentner) + Steelman + Harvard BATNA',
    options: [
      {
        label:
          'Recusar a missão dizendo que "ninguém me deu uma apostila pronta disso".',
        isMasterChoice: false,
        deltas: { carater: -3, vigor: 0, aprendizado: -4, autogoverno: -5, retorica: -4, estrategia: -6 },
        consequenceTitle: 'Talento Enterrado por Medo',
        consequenceNarrative:
          'Os maiores problemas reais não têm manual pronto — pertencem a quem constrói o mapa pelos fundamentos.',
      },
      {
        label:
          'Fingir que já sabe tudo sem estudar nada e calar quem discordar.',
        isMasterChoice: false,
        deltas: { carater: -6, vigor: 0, aprendizado: -5, autogoverno: -4, retorica: -8, estrategia: -7 },
        consequenceTitle: 'Soberba que Precede a Ruína (Provérbios 16:18)',
        consequenceNarrative:
          'Sem humildade epistêmica nem Pré-Morte, o primeiro ponto cego derruba o projeto.',
      },
      {
        label:
          'Desmontar por Primeiros Princípios em micro-sub-habilidades (4C/ID), transferir analogias de áreas que já domina, estimar por Taxa-Base/Fermi e ouvir o Homem de Aço da equipe.',
        isMasterChoice: true,
        deltas: { carater: 8, vigor: 9, aprendizado: 16, autogoverno: 11, retorica: 14, estrategia: 15 },
        consequenceTitle: 'Polimatia Desbloqueada!',
        consequenceNarrative:
          'Sua Base Absoluta funcionou como chave-mestra: em duas semanas você entrega uma solução sólida onde especialistas estreitos travaram!',
      },
      {
        label:
          'Ficar no canto esperando que outros carreguem o peso por você.',
        isMasterChoice: false,
        deltas: { carater: -4, vigor: 0, aprendizado: -2, autogoverno: -4, retorica: -4, estrategia: -4 },
        consequenceTitle: 'Omissão Diante do Chamado',
        consequenceNarrative:
          'Quem foge da responsabilidade nas horas decisivas nunca amadurece.',
      },
    ],
  },
  {
    id: 'cap_09_fornalha_perdao_integridade',
    chapterNumber: 9,
    timeHorizonLabel: 'O Crisol do Coração • Caráter na Fornalha',
    title: 'Traição, Amargura & o Atalho Corrupto',
    scenarioContext:
      'Quando seu sucesso começa a aparecer, alguém em quem você confiava age com inveja e injustiça contra você — e, ao mesmo tempo, oferecem um "esquema sujo" para você se vingar e lucrar fácil por fora. Esta é a prova que destrói pessoas brilhantes por dentro. O que você escolhe?',
    corePillarId: 'CRISTO_EVANGELHOS',
    linkedLessonId: 'cristo_05_perdao_setenta_vezes_sete',
    scientificAnchor: 'Jesus Cristo (Mt 18:21–22 & Mt 10:16) + José (Gn 39–50:20) + Worthington (Meta-análise Perdão)',
    options: [
      {
        label:
          'Aceitar o esquema corrupto e dedicar seus próximos anos a alimentar ódio e vingança.',
        isMasterChoice: false,
        deltas: { carater: -15, vigor: -6, aprendizado: -4, autogoverno: -10, retorica: -6, estrategia: -8 },
        consequenceTitle: 'Ruína Moral & Veneno Autoinfligido',
        consequenceNarrative:
          'A corrupção destrói sua fundação e o rancor crônico mantém seu sistema cardiovascular e sua mente presos ao agressor.',
      },
      {
        label:
          'Ficar amargurado e cínico dizendo "todo ser humano é podre, nunca mais ajudo ninguém".',
        isMasterChoice: false,
        deltas: { carater: -8, vigor: -4, aprendizado: -2, autogoverno: -5, retorica: -7, estrategia: -3 },
        consequenceTitle: 'Prisão da Amargura',
        consequenceNarrative:
          'Fechar o coração na amargura pune a você mesmo e apaga seu propósito.',
      },
      {
        label:
          'Recusar 100% o atalho desonesto como José (Gn 39), liberar o perdão cancelando o ódio interno para manter a mente limpa (Mt 18), mas estabelecer limites prudentes daqui em diante ("prudentes como as serpentes e simples como as pombas" — Mt 10:16).',
        isMasterChoice: true,
        deltas: { carater: 18, vigor: 8, aprendizado: 6, autogoverno: 14, retorica: 10, estrategia: 10 },
        consequenceTitle: 'Coração Livre, Limpo e Incorruptível!',
        consequenceNarrative:
          'Meta-análises de Worthington e Harvard provam: soltar o rancor devolve paz, energia e esperança — enquanto sua integridade intacta com limites sábios torna você inatacável!',
      },
      {
        label:
          'Ser ingênuo sem discernimento e entregar suas senhas e recursos de novo para quem continua agindo de má-fé.',
        isMasterChoice: false,
        deltas: { carater: 0, vigor: -2, aprendizado: -2, autogoverno: -2, retorica: -2, estrategia: -8 },
        consequenceTitle: 'Falta da Prudência de Mateus 10:16',
        consequenceNarrative:
          'Perdoar de coração nunca significou abandonar a sabedoria e a mordomia responsável.',
      },
    ],
  },
  {
    id: 'cap_10_bonanca_jose_margem',
    chapterNumber: 10,
    timeHorizonLabel: 'Ano 1,5 • Os Anos de Fartura',
    title: 'O Teste da Bonança: Euforia ou o Celeiro de José?',
    scenarioContext:
      'Seus primeiros frutos grandes chegaram: sua renda dobrou, sua saúde está forte e surgem ofertas de parcelamentos luxuosos e apostas "imperdíveis" prometendo enriquecimento mágico sem margem de segurança. Como você governa os anos de fartura?',
    corePillarId: 'SABEDORIA_BIBLICA',
    linkedLessonId: 'biblia_11_jose_sete_anos_reserva',
    scientificAnchor: 'Gênesis 41:34 (Quinto de José) + Carroll (QJE, 1997) + Graham (Margem de Segurança)',
    options: [
      {
        label:
          'Inflar imediatamente todos os custos fixos para consumir 100% da nova renda contando que nunca haverá crise.',
        isMasterChoice: false,
        deltas: { carater: -3, vigor: 0, aprendizado: 0, autogoverno: -6, retorica: 0, estrategia: -10 },
        consequenceTitle: 'Armadilha da Corrida dos Ratos',
        consequenceNarrative:
          'Na primeira oscilação econômica ou imprevisto familiar, seus custos altos sufocam sua paz e sua liberdade.',
      },
      {
        label:
          'Colocar toda a reserva num esquema alavancado de "ganho garantido" baseado em 2 vídeos de internet (N = 2).',
        isMasterChoice: false,
        deltas: { carater: -4, vigor: -2, aprendizado: -4, autogoverno: -6, retorica: 0, estrategia: -14 },
        consequenceTitle: 'Ruína Não-Ergódica & Lei dos Pequenos Números',
        consequenceNarrative:
          'Multiplicar por zero uma única vez apaga anos de trabalho honesto (Pv 28:20; Kelly, 1956).',
      },
      {
        label:
          'Aplicar o Celeiro de José (Gn 41:34) + Margem de Segurança 2×: estocar primeiro a reserva anticíclica intocável nos tempos bons, manter custos enxutos, agradecer sem soberba e investir com prudência!',
        isMasterChoice: true,
        deltas: { carater: 10, vigor: 6, aprendizado: 8, autogoverno: 10, retorica: 6, estrategia: 14 },
        consequenceTitle: 'Governança Inabalável nos 7 Anos de Fartura!',
        consequenceNarrative:
          'Enquanto os impulsivos quebram na primeira seca, seu celeiro cheio garante serenidade para proteger sua família e aproveitar oportunidades reais!',
      },
      {
        label:
          'Viver em avareza paralisante, recusando até cuidar da própria saúde ou ajudar quem realmente precisa.',
        isMasterChoice: false,
        deltas: { carater: -8, vigor: -4, aprendizado: 0, autogoverno: -2, retorica: -4, estrategia: -2 },
        consequenceTitle: 'Escravo do Medo, Não Mordomo Sábio',
        consequenceNarrative:
          'Dinheiro é escudo e ferramenta de serviço, nunca um ídolo para aprisionar a alma (Mt 6:24).',
      },
    ],
  },
  {
    id: 'cap_11_muralha_neemias_mansidao',
    chapterNumber: 11,
    timeHorizonLabel: 'Ano 2 • Ataque no Muro',
    title: 'O Vale de Ono: Provocações, Inveja & Grande Obra',
    scenarioContext:
      'Sua evolução agora é visível: você lidera um projeto crucial, mas críticos barulhentos mandam provocações públicas tentando arrastá-lo para brigas de ego e distrações diárias bem na reta final da entrega. Como você responde?',
    corePillarId: 'SABEDORIA_BIBLICA',
    linkedLessonId: 'biblia_12_neemias_grande_obra_foco',
    scientificAnchor: 'Neemias 6:3 + Mateus 5:5 (Mansidão / Praus) + Shah et al. (JPSP, 2002 Goal Shielding)',
    options: [
      {
        label:
          'Descer do muro furioso e gastar a semana inteira trocando insultos e sarcasmo nas redes.',
        isMasterChoice: false,
        deltas: { carater: -8, vigor: -4, aprendizado: -3, autogoverno: -10, retorica: -8, estrategia: -8 },
        consequenceTitle: 'Emboscada do Vale de Ono Bem-Sucedida',
        consequenceNarrative:
          'Seus sabotadores venceram sem esforço: fizeram você parar a própria obra e perder a razão no grito.',
      },
      {
        label:
          'Abandonar a liderança e esconder-se porque descobriu que quem constrói algo relevante recebe críticas.',
        isMasterChoice: false,
        deltas: { carater: -4, vigor: -3, aprendizado: -2, autogoverno: -6, retorica: -6, estrategia: -6 },
        consequenceTitle: 'Paralisia pelo Medo de Desagradar',
        consequenceNarrative:
          'Quem exige aprovação unânime nunca edifica nada duradouro.',
      },
      {
        label:
          'Unir a blindagem de Neemias ("Estou fazendo uma grande obra e não posso descer" — Ne 6:3) à mansidão firme (Mt 5:5): acionar 3 Suspiros Fisiológicos, ignorar provocações vazias, colher conselhos independentes da equipe leal e entregar a muralha pronta!',
        isMasterChoice: true,
        deltas: { carater: 12, vigor: 8, aprendizado: 8, autogoverno: 12, retorica: 12, estrategia: 10 },
        consequenceTitle: 'Muralha Erguida em Tempo Recorde!',
        consequenceNarrative:
          'Força sob rédea firme e foco blindado: enquanto o ruído passou como vento, a sua obra concreta falou mais alto que mil discursos!',
      },
      {
        label:
          'Cercar-se apenas de bajuladores que proíbem qualquer alerta técnico real sobre o projeto.',
        isMasterChoice: false,
        deltas: { carater: -5, vigor: 0, aprendizado: -6, autogoverno: -3, retorica: -5, estrategia: -9 },
        consequenceTitle: 'Cegueira de Groupthink (Janis, 1972)',
        consequenceNarrative:
          'Ignorar provocações de má-fé é sabedoria; calar alertas técnicos honestos da própria equipe é orgulho perigoso.',
      },
    ],
  },
  {
    id: 'cap_12_consagracao_rocha_servico',
    chapterNumber: 12,
    timeHorizonLabel: 'A Consagração Final • O Mestre Completo',
    title: 'O Teste do Topo: Vaidade ou Grandeza no Servir?',
    scenarioContext:
      'Olhe de onde você saiu: era um jovem sem nenhuma habilidade no Quarto do Marco Zero — e hoje domina seu corpo, sua mente, sua palavra, seus recursos e sua área técnica! Agora jovens perdidos olham para você, e o mundo oferece o trono da arrogância. Qual é o seu destino final?',
    corePillarId: 'CRISTO_EVANGELHOS',
    linkedLessonId: 'cristo_06_lideranca_servidora_agape',
    scientificAnchor: 'Jesus Cristo (Marcos 10:42–45 • João 13 • Mateus 7:24) + Eva et al. (2019) + Propósito (N = 488.765)',
    options: [
      {
        label:
          'Olhar os iniciantes com desprezo, usar sua força só para alimentar o próprio ego e achar que é autossuficiente.',
        isMasterChoice: false,
        deltas: { carater: -14, vigor: 0, aprendizado: -4, autogoverno: -6, retorica: -8, estrategia: -5 },
        consequenceTitle: 'Queda pela Soberba no Topo',
        consequenceNarrative:
          '"A soberba precede a ruína, e a altivez do espírito precede a queda" (Pv 16:18). Sem amor nem serviço, toda conquista fica oca.',
      },
      {
        label:
          'Acomodar-se achando que já não precisa aprender nem vigiar mais nada.',
        isMasterChoice: false,
        deltas: { carater: -4, vigor: -5, aprendizado: -6, autogoverno: -5, retorica: -2, estrategia: -4 },
        consequenceTitle: 'Ferrugem da Complacência',
        consequenceNarrative:
          '"Aquele, pois, que cuida estar em pé, olhe não caia" (1 Coríntios 10:12). Maestria é chama viva cultivada todo dia.',
      },
      {
        label:
          'Seguir o Maior Mestre que pisou na Terra ("Quem quiser tornar-se grande entre vós, será esse o que vos sirva" — Mc 10:43): manter humildade vigilante sobre a Rocha, usar toda a sua força e sabedoria para proteger, ensinar e levantar outros que hoje estão no zero!',
        isMasterChoice: true,
        deltas: { carater: 20, vigor: 8, aprendizado: 8, autogoverno: 10, retorica: 12, estrategia: 10 },
        consequenceTitle: 'Consagração Suprema: Mestre Edificado Sobre a Rocha!',
        consequenceNarrative:
          'Você completou a travessia inteira: saiu do zero absoluto e uniu excelência técnica, vigor físico e lucidez mental à maior grandeza que existe — caráter incorruptível, humildade e amor que serve e transforma vidas!',
      },
      {
        label:
          'Viver apenas buscando aplauso em vitrines digitais.',
        isMasterChoice: false,
        deltas: { carater: -8, vigor: -2, aprendizado: -3, autogoverno: -5, retorica: -3, estrategia: -3 },
        consequenceTitle: 'Escravo de Aplauso Passageiro (Mateus 6:2)',
        consequenceNarrative:
          'Quem vive da vaidade das esquinas perde a paz interior no primeiro dia em que a plateia muda de assunto.',
      },
    ],
  },
];

export function createInitialSimulatorRun(): SimulatorRunState {
  return {
    currentChapterIndex: 0,
    attributes: { ...INITIAL_ZERO_ATTRIBUTES },
    history: [],
    completed: false,
  };
}

export function applySimulatorChoice(
  state: SimulatorRunState,
  optionIndex: 0 | 1 | 2 | 3,
): SimulatorRunState {
  if (state.completed || state.currentChapterIndex >= SIMULATOR_CHAPTERS.length) {
    return state;
  }

  const chapter = SIMULATOR_CHAPTERS[state.currentChapterIndex];
  const opt = chapter.options[optionIndex];

  const nextAttributes: MasteryAttributes = {
    carater: clamp(state.attributes.carater + opt.deltas.carater, 0, 100),
    vigor: clamp(state.attributes.vigor + opt.deltas.vigor, 0, 100),
    aprendizado: clamp(state.attributes.aprendizado + opt.deltas.aprendizado, 0, 100),
    autogoverno: clamp(state.attributes.autogoverno + opt.deltas.autogoverno, 0, 100),
    retorica: clamp(state.attributes.retorica + opt.deltas.retorica, 0, 100),
    estrategia: clamp(state.attributes.estrategia + opt.deltas.estrategia, 0, 100),
  };

  const nextIdx = state.currentChapterIndex + 1;

  return {
    currentChapterIndex: nextIdx,
    attributes: nextAttributes,
    history: [
      ...state.history,
      {
        chapterId: chapter.id,
        chosenOptionIndex: optionIndex,
        wasMasterChoice: opt.isMasterChoice,
      },
    ],
    completed: nextIdx >= SIMULATOR_CHAPTERS.length,
  };
}

export function evaluateFinalMasteryReport(state: SimulatorRunState): SimulatorFinalReport {
  const { carater, vigor, aprendizado, autogoverno, retorica, estrategia } = state.attributes;
  const avgAttr = (carater + vigor + aprendizado + autogoverno + retorica + estrategia) / 6;
  const masterDecisionsCount = state.history.filter((h) => h.wasMasterChoice).length;
  const decisionRatio = masterDecisionsCount / SIMULATOR_CHAPTERS.length;

  const score1000 = Math.round(clamp(avgAttr * 6 + decisionRatio * 400, 0, 1000));

  let rankTitle = 'Grau I — Aprendiz em Despertar';
  let rankSummary =
    'Você já percebeu algumas armadilhas, mas ainda cai em atalhos emocionais, vaidade ou impulsividade. Comece pelos tijolos de Grau I sobre a Rocha!';

  if (masterDecisionsCount === SIMULATOR_CHAPTERS.length) {
    rankTitle = 'Grau IV — Mestre Polímata Edificado Sobre a Rocha';
    rankSummary =
      'Travessia impecável nos 12 crisóis! Você uniu os ensinamentos de Jesus Cristo e da Sabedoria Bíblica à ciência da aprendizagem, domínio próprio, retórica, lógica e saúde física.';
  } else if (masterDecisionsCount >= 9) {
    rankTitle = 'Grau III — Estrategista de Caráter Firme';
    rankSummary =
      'Base muito forte! Falta apenas blindar 1 ou 2 pontos cegos para alcançar plenitude sob pressão.';
  } else if (masterDecisionsCount >= 6) {
    rankTitle = 'Grau II — Artífice em Construção';
    rankSummary =
      'Boa evolução a partir do zero! Estude as lições recomendadas abaixo para fortalecer onde houve tropeço.';
  }

  const dims: { key: keyof MasteryAttributes; label: string; fallbackLesson: string }[] = [
    {
      key: 'carater',
      label: 'Caráter, Sabedoria Bíblica & Serviço',
      fallbackLesson: 'cristo_01_casa_na_rocha',
    },
    {
      key: 'vigor',
      label: 'Hardware Físico & Energia',
      fallbackLesson: 'corpo_06_postura_movimento_base',
    },
    {
      key: 'aprendizado',
      label: 'Máquina de Aprender & Memória',
      fallbackLesson: 'estrategia_06_exemplos_resolvidos_degrau_zero',
    },
    {
      key: 'autogoverno',
      label: 'Domínio Próprio & Emoção',
      fallbackLesson: 'biblia_01_proverbios_dominio_proprio',
    },
    {
      key: 'retorica',
      label: 'Palavra, Língua & Inteligência Social',
      fallbackLesson: 'biblia_03_tiago_freio_da_lingua',
    },
    {
      key: 'estrategia',
      label: 'Lógica, Mordomia & Recursos',
      fallbackLesson: 'num_05_soberania_financeira_reserva',
    },
  ];

  dims.sort((a, b) => state.attributes[a.key] - state.attributes[b.key]);
  const weakestDimensionLabel = dims[0].label;

  const missedLessons = state.history
    .map((h, idx) => (!h.wasMasterChoice ? SIMULATOR_CHAPTERS[idx]?.linkedLessonId : null))
    .filter((x): x is string => Boolean(x));

  const recommendedLessonIds =
    missedLessons.length > 0
      ? missedLessons.slice(0, 3)
      : [
          'cristo_06_lideranca_servidora_agape',
          'biblia_06_jose_davi_proposito_fornalha',
          'aprend_06_arquitetura_4cid_transferencia',
        ];

  return {
    score1000,
    masterDecisionsCount,
    totalChapters: SIMULATOR_CHAPTERS.length,
    rankTitle,
    rankSummary,
    weakestDimensionLabel,
    recommendedLessonIds,
  };
}
