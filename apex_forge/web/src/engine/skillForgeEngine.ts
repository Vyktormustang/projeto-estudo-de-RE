import { clamp } from './stateEngine';
import { SkillBlueprint, SkillBlueprintStep } from './types';

export interface SkillTemplateSpec {
  id: string;
  skillName: string;
  categoryLabel: string;
  oracle30DayProof: string;
  zeroStep2Min: string;
  analogicalBridge: string;
  preMortemSaboteur: string;
  stepDescriptions: [string, string, string, string];
}

export interface FeynmanAuditInput {
  conceptName: string;
  childExplanation: string;       // Como explicaria sem jargao para um jovem de 12 anos?
  whyAndBoundary: string;         // Por que funciona (causa) e onde falha/quebra?
  concreteAnalogy: string;        // Ponte analogica com algo do mundo fisico
}

export interface FeynmanAuditResult {
  clarityScorePct: number;        // 0..100
  passed: boolean;                // >= 70%
  verdictTitle: string;
  strengths: string[];
  gapsToFix: string[];
  synthesizedNote: string;
}

export const PRESET_SKILL_TEMPLATES: SkillTemplateSpec[] = [
  {
    id: 'tpl_programacao_logica',
    skillName: 'Programação & Resolução de Problemas do Zero',
    categoryLabel: 'Tecnologia & Engenharia',
    oracle30DayProof:
      'Construir do zero, sem copiar código pronto, 1 aplicação funcional completa (com variáveis, laços, funções e tratamento de erro) e explicar cada linha em voz alta.',
    zeroStep2Min:
      'Abrir o editor/caderno, ler 1 função curta de 8 linhas e prever no papel qual será a saída antes de rodar.',
    analogicalBridge:
      'Um programa é como uma receita de oficina mecânica: variáveis são gavetas etiquetadas, funções são ferramentas reutilizáveis e "if/else" são bifurcações na estrada.',
    preMortemSaboteur:
      'Assistir a horas de vídeo-aula passiva sem digitar nem errar sozinho ("Tutorial Hell"). Escudo: para cada 10 min de exemplo, 20 min codando de tela fechada.',
    stepDescriptions: [
      'Degrau 1 (Exemplo Resolvido): Dissecar 5 códigos curtos linha por linha prevendo a saída no papel antes de executar.',
      'Degrau 2 (Blocos Sem Olhar): Escrever sozinho variáveis, condicionais, laços e funções simples sem consultar guia.',
      'Degrau 3 (Prática Entrelaçada): Resolver 10 desafios curtos misturando listas, texto e lógica e caçar os próprios bugs.',
      'Degrau 4 (Prova Real & Serviço): Criar 1 ferramenta útil para resolver um problema real seu ou de alguém próximo.',
    ],
  },
  {
    id: 'tpl_ingles_funcional',
    skillName: 'Inglês Funcional & Leitura Técnica do Zero',
    categoryLabel: 'Idiomas & Acesso Global',
    oracle30DayProof:
      'Ler 1 artigo ou documentação em inglês compreendendo 85%+ da ideia central e falar por 3 minutos contínuos apresentando quem você é e o que estuda.',
    zeroStep2Min:
      'Revisar 5 frases reais em voz alta (evocação ativa) focando em blocos de palavras inteiros ("chunks"), nunca palavras soltas.',
    analogicalBridge:
      'Aprender idioma não é decorar dicionário (peças soltas de motor), é montar frases-bloco prontas para rodar na rua desde o Dia 1.',
    preMortemSaboteur:
      'Vergonha de pronunciar errado na frente dos outros. Escudo: treinar 3 min em voz alta sozinho no quarto todo dia antes de conversar.',
    stepDescriptions: [
      'Degrau 1 (Exemplo Resolvido): Dominar as 300 estruturas/frases de maior frequência ouvindo e repetindo em voz alta.',
      'Degrau 2 (Blocos Sem Olhar): Traduzir mentalmente do português para o inglês 15 frases úteis do cotidiano sem olhar cola.',
      'Degrau 3 (Prática Entrelaçada): Ler parágrafos reais curtos (com áudio) e resumir em 2 frases faladas o que entendeu.',
      'Degrau 4 (Prova Real & Serviço): Gravar 3 minutos contínuos explicando um tema da sua área em inglês claro.',
    ],
  },
  {
    id: 'tpl_matematica_exatas',
    skillName: 'Matemática & Raciocínio Quantitativo do Zero',
    categoryLabel: 'Ciências Exatas & Lógica',
    oracle30DayProof:
      'Resolver uma bateria mista de 15 problemas (frações, proporção, porcentagem, equações de 1º/2º grau e probabilidade básica) com >= 85% de acerto no papel.',
    zeroStep2Min:
      'Estudar 1 Exemplo Resolvido explicando por que um termo mudou de lado e resolver 1 conta gêmea no papel sem calculadora.',
    analogicalBridge:
      'Uma equação é uma balança fiel de dois pratos (Pv 11:1): tudo o que você faz no prato esquerdo precisa fazer igual no direito para manter o equilíbrio.',
    preMortemSaboteur:
      'Pular a base de frações e sinais por pressa e travar lá na frente. Escudo: domínio 100% do tijolo anterior antes de subir.',
    stepDescriptions: [
      'Degrau 1 (Exemplo Resolvido): Dominar operações, frações e proporções dissecando passo a passo exemplos resolvidos.',
      'Degrau 2 (Blocos Sem Olhar): Resolver porcentagens, juros e equações de 1º grau no papel com livro fechado.',
      'Degrau 3 (Prática Entrelaçada): Resolver listas misturadas onde você precisa descobrir sozinho qual ferramenta aplicar.',
      'Degrau 4 (Prova Real & Serviço): Ensinar no quadro/papel 3 temas matemáticos para um colega iniciante sem gaguejar.',
    ],
  },
  {
    id: 'tpl_oratoria_comunicacao',
    skillName: 'Oratória, Escrita Clara & Presença Social',
    categoryLabel: 'Palavra & Liderança',
    oracle30DayProof:
      'Explicar qualquer ideia complexa em 2 minutos usando Conclusão + 2 Provas + Exemplo, mantendo voz calma, postura firme e escuta ativa sob perguntas difíceis.',
    zeroStep2Min:
      'Gravar 60 segundos de áudio no celular respondendo "Qual é a ideia central que aprendi hoje?" sem rodeios.',
    analogicalBridge:
      'Falar bem é como construir uma ponte: a conclusão logo na 1ª frase mostra a outra margem; as 2 provas são os pilares que sustentam a travessia.',
    preMortemSaboteur:
      'Falar rápido demais olhando para o chão quando o coração acelera. Escudo: pausa respiratória consciente de 2 segundos antes da 1ª frase.',
    stepDescriptions: [
      'Degrau 1 (Exemplo Resolvido): Analisar 3 falas curtas excelentes identificando Tese inicial, Provas e Fechamento.',
      'Degrau 2 (Blocos Sem Olhar): Estruturar em 3 tópicos no papel e falar por 90s em pé olhando para um ponto fixo.',
      'Degrau 3 (Prática Entrelaçada): Treinar resposta calma a 5 perguntas inesperadas usando Perguntas Calibradas e Homem de Aço.',
      'Degrau 4 (Prova Real & Serviço): Apresentar uma aula ou proposta real para um grupo ajudando genuinamente quem ouve.',
    ],
  },
  {
    id: 'tpl_financas_trabalho',
    skillName: 'Soberania Financeira & Habilidade Profissional Útil',
    categoryLabel: 'Mordomia & Recursos',
    oracle30DayProof:
      'Mapear 100% das entradas/saídas, estancar vazamentos impulsivos, iniciar Reserva de Paz automática e entregar 1 serviço/projeto real que resolva dor concreta.',
    zeroStep2Min:
      'Anotar cada centavo do dia em 60 segundos e perguntar "Isto constrói liberdade ou vaidade?".',
    analogicalBridge:
      'Finanças funcionam como uma caixa-d’água: antes de aumentar o cano de entrada, vede os furos no fundo para que toda gota acumule nível seguro.',
    preMortemSaboteur:
      'Comprar por impulso quando estiver cansado na sexta à noite. Escudo: regra obrigatória de esperar 72 horas antes de qualquer compra não-essencial.',
    stepDescriptions: [
      'Degrau 1 (Exemplo Resolvido): Auditar 30 dias de gastos reais separando Essencial, Ferramenta Produtiva e Vazamento de Vaidade.',
      'Degrau 2 (Blocos Sem Olhar): Automatizar separação da Reserva de Paz no dia exato em que o recurso entra.',
      'Degrau 3 (Prática Entrelaçada): Comparar taxas reais pela Regra dos 72 + Custo de Oportunidade antes de qualquer decisão.',
      'Degrau 4 (Prova Real & Serviço): Entregar 1 solução prática excelente que gere valor real e legítimo ao próximo.',
    ],
  },
  {
    id: 'tpl_autodidatismo_leitura',
    skillName: 'Leitura Profunda, Síntese & Estudo de Alto Nível',
    categoryLabel: 'Meta-Aprendizagem',
    oracle30DayProof:
      'Ler e fichar 2 livros densos ou editais técnicos extraindo modelos mentais aplicáveis e acertando >= 85% em revisão espaçada de 7 dias sem reler o texto.',
    zeroStep2Min:
      'Ler 2 páginas com lápis na mão, fechar o livro e escrever 1 única frase resumindo a tese do autor com suas próprias palavras.',
    analogicalBridge:
      'Ler sem evocar é jogar água numa peneira; fechar o livro e explicar no papel é fundir o ferro no molde permanente da memória.',
    preMortemSaboteur:
      'Grifar páginas no piloto automático com sono pensando em outra coisa. Escudo: blocos curtos de 25 min seguidos de 3 min de resumo de livro fechado.',
    stepDescriptions: [
      'Degrau 1 (Exemplo Resolvido): Inspecionar sumário e perguntas-guia antes de ler e resumir cada seção em 1 frase sem olhar.',
      'Degrau 2 (Blocos Sem Olhar): Transformar os conceitos centrais em perguntas de Evocação Ativa (+1d, +3d, +7d).',
      'Degrau 3 (Prática Entrelaçada): Conectar ideias de 2 capítulos ou livros distintos buscando onde concordam e onde divergem.',
      'Degrau 4 (Prova Real & Serviço): Escrever um guia claro de 1 página capaz de ensinar o tema a qualquer iniciante.',
    ],
  },
];

function makeSteps(descriptions: [string, string, string, string], prefix: string): [
  SkillBlueprintStep,
  SkillBlueprintStep,
  SkillBlueprintStep,
  SkillBlueprintStep,
] {
  const labels = [
    'Grau I • Exemplo Resolvido',
    'Grau II • Evocação Sem Cola',
    'Grau III • Prática Entrelaçada',
    'Grau IV • Prova Real & Ensino',
  ];
  return [0, 1, 2, 3].map((idx) => ({
    id: `${prefix}_s${idx + 1}`,
    tier: (idx + 1) as 1 | 2 | 3 | 4,
    stageLabel: labels[idx],
    actionDescription: descriptions[idx],
    completed: false,
  })) as [SkillBlueprintStep, SkillBlueprintStep, SkillBlueprintStep, SkillBlueprintStep];
}

export function createBlueprintFromTemplate(
  templateId: string,
  bioDayId: string,
): SkillBlueprint {
  const tpl =
    PRESET_SKILL_TEMPLATES.find((t) => t.id === templateId) ?? PRESET_SKILL_TEMPLATES[0];
  const uid = `bp_${tpl.id}_${Date.now()}`;
  return {
    id: uid,
    skillName: tpl.skillName,
    categoryLabel: tpl.categoryLabel,
    oracle30DayProof: tpl.oracle30DayProof,
    zeroStep2Min: tpl.zeroStep2Min,
    analogicalBridge: tpl.analogicalBridge,
    preMortemSaboteur: tpl.preMortemSaboteur,
    steps: makeSteps(tpl.stepDescriptions, uid),
    feynmanAuditsCount: 0,
    bestFeynmanClarityScore: 0,
    createdBioDayId: bioDayId,
  };
}

export function createCustomSkillBlueprint(
  params: {
    skillName: string;
    categoryLabel?: string;
    oracle30DayProof?: string;
    zeroStep2Min?: string;
    analogicalBridge?: string;
    preMortemSaboteur?: string;
  },
  bioDayId: string,
): SkillBlueprint {
  const cleanName = params.skillName.trim() || 'Nova Habilidade Fundamental';
  const uid = `bp_custom_${Date.now()}`;
  const descriptions: [string, string, string, string] = [
    `Degrau 1: Estudar 3 exemplos resolvidos básicos de "${cleanName}" entendendo o porquê de cada passo.`,
    `Degrau 2: Executar os movimentos/exercícios fundamentais de "${cleanName}" sozinho, sem olhar material de consulta.`,
    `Degrau 3: Praticar cenários variados e misturados de "${cleanName}" corrigindo imediatamente cada erro encontrado.`,
    `Degrau 4: Cumprir a Prova Real de 30 dias de "${cleanName}" e ensinar os fundamentos com clareza simples a um iniciante.`,
  ];

  return {
    id: uid,
    skillName: cleanName,
    categoryLabel: params.categoryLabel?.trim() || 'Domínio Personalizado',
    oracle30DayProof:
      params.oracle30DayProof?.trim() ||
      `Executar um projeto ou demonstração completa de ${cleanName} do zero sem consultar anotações.`,
    zeroStep2Min:
      params.zeroStep2Min?.trim() ||
      `Praticar 2 minutos do bloco mais básico de ${cleanName} sem celular por perto.`,
    analogicalBridge:
      params.analogicalBridge?.trim() ||
      `Funciona como erguer uma casa tijolo por tijolo: primeiro a base firme, depois as paredes.`,
    preMortemSaboteur:
      params.preMortemSaboteur?.trim() ||
      `Querer pular para o avançado na Semana 1 e desanimar. Escudo: honrar o Degrau Zero diário.`,
    steps: makeSteps(descriptions, uid),
    feynmanAuditsCount: 0,
    bestFeynmanClarityScore: 0,
    createdBioDayId: bioDayId,
  };
}

/**
 * Avalia deterministicamente o Exame Socratico de Feynman + Autoexplicacao de Chi
 * (Chi et al., 1989/1994; Bisra et al., 2018, k=64, g=0.55):
 * Mede simplicidade livre de muletas vagas, presenca de mecanismo causal, fronteira de falha e analogia fisica.
 */
export function evaluateFeynmanSocraticAudit(input: FeynmanAuditInput): FeynmanAuditResult {
  const concept = input.conceptName.trim() || 'Conceito Estudado';
  const exp = input.childExplanation.trim();
  const why = input.whyAndBoundary.trim();
  const ana = input.concreteAnalogy.trim();

  const strengths: string[] = [];
  const gapsToFix: string[] = [];
  let score = 0;

  // 1. Explicacao simples (ate 38 pts)
  const expWords = exp.split(/\s+/).filter(Boolean);
  if (expWords.length >= 12) {
    score += 28;
    strengths.push('Explicação articulada com substância suficiente para uma criança entender.');
  } else if (expWords.length >= 6) {
    score += 16;
    gapsToFix.push('Expanda um pouco a explicação simples (use pelo menos 12 palavras claras mostrando o que a ideia faz).');
  } else {
    gapsToFix.push('A explicação simples está curta demais — descreva em linguagem comum o que o conceito realmente faz.');
  }

  const vaguePattern = /\b(tipo assim|sei l[aá]|basicamente isso|coisa tal|etc e tal)\b/i;
  if (expWords.length >= 6 && !vaguePattern.test(exp)) {
    score += 10;
  } else if (vaguePattern.test(exp)) {
    gapsToFix.push('Remova muletas vagas ("tipo assim", "sei lá") — elas escondem lacunas exatas de compreensão.');
  }

  // 2. Mecanismo Causal + Fronteira de Falha (ate 37 pts — Chi Self-Explanation)
  const whyWords = why.split(/\s+/).filter(Boolean);
  const causalPattern =
    /\b(porque|pois|causa|gera|produz|quando|ent[aã]o|portanto|depende|obriga|impede|for[cç]a)\b/i;
  const boundaryPattern =
    /\b(falha|erro|quebra|limite|exceto|n[aã]o funciona|perigo|se faltar|sem|excesso)\b/i;

  if (whyWords.length >= 10 && causalPattern.test(why)) {
    score += 22;
    strengths.push('Mecanismo de causa e efeito explicitado com clareza (Efeito Chi de Autoexplicação).');
  } else {
    score += whyWords.length >= 6 ? 10 : 0;
    gapsToFix.push('Explique explicitamente a CAUSA usando conectores ("funciona porque...", "quando X muda, Y acontece").');
  }

  if (boundaryPattern.test(why)) {
    score += 15;
    strengths.push('Fronteira de falha mapeada — você sabe exatamente onde e quando a regra quebra.');
  } else {
    gapsToFix.push('Adicione o limite de validade: em qual condição esse conceito falha ou não se aplica?');
  }

  // 3. Ponte Analogica (ate 25 pts — Gentner 2003)
  const anaWords = ana.split(/\s+/).filter(Boolean);
  const analogyPattern = /\b(como|igual|feito|parece|funciona tal qual|ponte|alavanca|caixa|motor|casa|semente|filtro)\b/i;
  if (anaWords.length >= 7 && analogyPattern.test(ana)) {
    score += 25;
    strengths.push('Ponte analógica concreta construída (multiplica transferência para problemas inéditos — Gentner, 2003).');
  } else if (anaWords.length >= 5) {
    score += 15;
    strengths.push('Analogia registrada para ancorar a memória de longo prazo.');
  } else {
    gapsToFix.push('Crie uma analogia física simples ("Isso funciona como uma alavanca / filtro / semente porque...").');
  }

  const clarityScorePct = clamp(Math.round(score), 0, 100);
  const passed = clarityScorePct >= 70;

  let verdictTitle = 'Lacuna Detectada — Lapide Antes de Avançar';
  if (clarityScorePct >= 90) {
    verdictTitle = 'Cristalino Nível Feynman — Domínio Real Confirmado!';
  } else if (clarityScorePct >= 70) {
    verdictTitle = 'Aprovado no Exame Socrático — Base Sólida!';
  }

  const synthesizedNote = `[Feynman ${clarityScorePct}% • ${concept}] Definição limpa: ${exp || '-'} | Causa & Limite: ${why || '-'} | Analogia: ${ana || '-'}`;

  return {
    clarityScorePct,
    passed,
    verdictTitle,
    strengths,
    gapsToFix,
    synthesizedNote,
  };
}
