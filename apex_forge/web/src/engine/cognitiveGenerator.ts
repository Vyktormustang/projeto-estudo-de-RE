export interface StroopColorSpec {
  id: 'VERMELHO' | 'AZUL' | 'VERDE' | 'AMARELO';
  label: string;
  hex: string;
}

export const STROOP_COLORS: StroopColorSpec[] = [
  { id: 'VERMELHO', label: 'VERMELHO', hex: '#ef4444' },
  { id: 'AZUL', label: 'AZUL', hex: '#3b82f6' },
  { id: 'VERDE', label: 'VERDE', hex: '#10b981' },
  { id: 'AMARELO', label: 'AMARELO', hex: '#f59e0b' },
];

export interface StroopTrial {
  rule: 'COR_DA_TINTA' | 'SIGNIFICADO_PALAVRA';
  wordText: string;
  inkHex: string;
  options: string[];
  correctIndex: number;
}

export interface MatrixCellSpec {
  shape: 'CIRCLE' | 'SQUARE' | 'TRIANGLE';
  count: 1 | 2 | 3;
  fill: 'OUTLINE' | 'HALF' | 'SOLID';
}

export interface LogicPuzzle {
  kind: 'SEQUENCE' | 'DEDUCTION' | 'RAVEN_MATRIX';
  prompt: string;
  matrixGrid?: (MatrixCellSpec | null)[]; // 9 posicoes (indice 8 = null)
  matrixOptions?: MatrixCellSpec[];       // 4 opcoes visuais se kind === 'RAVEN_MATRIX'
  textOptions?: string[];                 // 4 opcoes de texto se SEQUENCE / DEDUCTION
  correctIndex: number;                   // 0..3
  explanation: string;
}

export interface LociPair {
  stationIndex: number;
  stationName: string;
  stationCue: string;
  targetWord: string;
}

export interface LociDeck {
  pairs: LociPair[];
  interferencePrompt: string;
  interferenceOptions: string[];
  interferenceCorrectIndex: number;
}

function nextRand(state: { s: number }): number {
  state.s = (Math.imul(state.s, 1664525) + 1013904223) >>> 0;
  return state.s / 4294967296;
}

function shuffleWithState<T>(arr: T[], state: { s: number }): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(nextRand(state) * (i + 1));
    const tmp = copy[i];
    copy[i] = copy[j];
    copy[j] = tmp;
  }
  return copy;
}

export function generateStroopTrial(seed: number, difficulty: 1 | 2 | 3): StroopTrial {
  const st = { s: (seed ^ 0x9e3779b9) >>> 0 };
  const wordIdx = Math.floor(nextRand(st) * 4);
  // Forca conflito incongruente em 80% das rodadas
  let inkIdx = Math.floor(nextRand(st) * 4);
  if (inkIdx === wordIdx && nextRand(st) < 0.85) {
    inkIdx = (wordIdx + 1 + Math.floor(nextRand(st) * 3)) % 4;
  }

  // Em dificuldade 2-3 alterna regra executiva (Task Switching + Inibicao)
  const switchProb = difficulty === 1 ? 0.15 : difficulty === 2 ? 0.38 : 0.5;
  const rule: StroopTrial['rule'] =
    nextRand(st) < switchProb ? 'SIGNIFICADO_PALAVRA' : 'COR_DA_TINTA';

  const targetLabel =
    rule === 'COR_DA_TINTA' ? STROOP_COLORS[inkIdx].label : STROOP_COLORS[wordIdx].label;

  const options = shuffleWithState(
    STROOP_COLORS.map((c) => c.label),
    st,
  );
  const correctIndex = options.indexOf(targetLabel);

  return {
    rule,
    wordText: STROOP_COLORS[wordIdx].label,
    inkHex: STROOP_COLORS[inkIdx].hex,
    options,
    correctIndex,
  };
}

const DEDUCTION_BANK: Array<{
  prompt: string;
  correct: string;
  wrongs: [string, string, string];
  explanation: string;
}> = [
  {
    prompt:
      'Regra: "Sempre que o servidor entra em sobrecarga, o alarme térmico dispara." Hoje o alarme térmico NÃO disparou. O que é logicamente garantido?',
    correct: 'O servidor não entrou em sobrecarga.',
    wrongs: [
      'O servidor entrou em sobrecarga leve.',
      'O sensor térmico está desligado.',
      'Nada pode ser concluído com certeza.',
    ],
    explanation:
      'Modus Tollens (Se P → Q; não Q, logo não P): se a sobrecarga exigisse o alarme e ele não tocou, a sobrecarga não ocorreu.',
  },
  {
    prompt:
      'Regra: "Todos os engenheiros da equipe Alfa dominam C++. Alguns membros da equipe Alfa sabem Rust." Qual afirmação é obrigatoriamente verdadeira?',
    correct: 'Há pelo menos alguém que domina C++ e também sabe Rust.',
    wrongs: [
      'Todos que sabem C++ sabem Rust.',
      'Nenhum membro fora da Alfa sabe Rust.',
      'Todos da equipe Alfa sabem Rust.',
    ],
    explanation:
      'Como alguns membros da Alfa sabem Rust e 100% da Alfa domina C++, essa interseção sabe ambos.',
  },
  {
    prompt:
      'Em uma fila de corrida: Bruno chegou antes de Carlos. Daniel chegou depois de Ana, mas antes de Bruno. Quem chegou em 2º lugar?',
    correct: 'Daniel',
    wrongs: ['Bruno', 'Ana', 'Carlos'],
    explanation:
      'Ordem transitiva exata: Ana (1º) → Daniel (2º) → Bruno (3º) → Carlos (4º).',
  },
  {
    prompt:
      'Premissa: "Se um treino viola a trava articular, ele é bloqueado." Sabemos que o treino X foi bloqueado. O que podemos afirmar com certeza?',
    correct: 'Não é possível garantir que violou a trava articular (pode ter sido bloqueado por febre).',
    wrongs: [
      'Com certeza violou a trava articular.',
      'Com certeza não havia febre.',
      'Nenhum exercício do catálogo é seguro.',
    ],
    explanation:
      'Evita a Falácia da Afirmação do Consequente: P → Q e Q verdadeiro não obrigam P (outras causas também geram Q).',
  },
  {
    prompt:
      'Em uma gaveta escura há 6 meias pretas e 6 meias brancas misturadas. Qual é o MENOR número de meias que você precisa retirar sem olhar para garantir 1 par da mesma cor?',
    correct: '3 meias',
    wrongs: ['2 meias', '4 meias', '7 meias'],
    explanation:
      'Princípio da Casa dos Pombos: como só existem 2 cores, ao puxar 3 unidades pelo menos duas terão obrigatoriamente a mesma cor.',
  },
  {
    prompt:
      'Três caixas têm etiquetas TROCADAS (nenhuma diz a verdade): [Parafusos], [Pregos] e [Mista]. Você tira 1 peça da caixa etiquetada [Mista] e vê um Parafuso. O que há na caixa etiquetada [Parafusos]?',
    correct: 'Apenas Pregos',
    wrongs: ['Mista', 'Apenas Parafusos', 'Impossível saber com 1 retirada'],
    explanation:
      'Como [Mista] mente e saiu Parafuso, ela é [Apenas Parafusos]. A etiqueta [Pregos] não pode ser Pregos, logo é Mista; sobra [Apenas Pregos] na caixa [Parafusos]!',
  },
  {
    prompt:
      'Uma bactéria dobra de população a cada minuto e enche um frasco inteiro em exatos 60 minutos. Em quantos minutos o frasco estava pela METADE?',
    correct: '59 minutos',
    wrongs: ['30 minutos', '45 minutos', '58 minutos'],
    explanation:
      'Crescimento exponencial base 2: se ela dobra a cada minuto e fica 100% cheia no minuto 60, um minuto antes (59) estava exatamente em 50%.',
  },
  {
    prompt:
      '5 máquinas fabricam 5 peças em 5 minutos. Em quantos minutos 100 máquinas fabricam 100 peças trabalhando no mesmo ritmo?',
    correct: '5 minutos',
    wrongs: ['100 minutos', '20 minutos', '1 minuto'],
    explanation:
      'Desarmando a intuição linear impulsiva (Sistema 1 de Kahneman): cada máquina individual leva 5 minutos para produzir 1 peça.',
  },
];

export function generateLogicQuestion(seed: number, difficulty: 1 | 2 | 3): LogicPuzzle {
  const st = { s: (seed ^ 0x85ebca6b) >>> 0 };
  const roll = nextRand(st);

  // 1) MATRIZ VISUAL 3x3 ESTILO RAVEN (~36% das questoes)
  if (roll < 0.36) {
    const shapes = shuffleWithState<MatrixCellSpec['shape']>(['CIRCLE', 'SQUARE', 'TRIANGLE'], st);
    const counts = shuffleWithState<MatrixCellSpec['count']>([1, 2, 3], st);
    const fills = shuffleWithState<MatrixCellSpec['fill']>(['OUTLINE', 'HALF', 'SOLID'], st);

    const shiftS = 1 + Math.floor(nextRand(st) * 2);
    const shiftC = 1 + Math.floor(nextRand(st) * 2);
    const shiftF = difficulty === 1 ? 0 : 1 + Math.floor(nextRand(st) * 2);

    const fullCells: MatrixCellSpec[] = [];
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        fullCells.push({
          shape: shapes[(r + c * shiftS) % 3],
          count: counts[(r * shiftC + c) % 3],
          fill: fills[(r + c * shiftF) % 3],
        });
      }
    }

    const answer = fullCells[8];
    const grid: (MatrixCellSpec | null)[] = [...fullCells.slice(0, 8), null];

    const keyOf = (m: MatrixCellSpec) => `${m.shape}_${m.count}_${m.fill}`;
    const distractors: MatrixCellSpec[] = [];
    const candidates: MatrixCellSpec[] = [
      { shape: shapes[0], count: answer.count, fill: answer.fill },
      { shape: shapes[1], count: answer.count, fill: answer.fill },
      { shape: answer.shape, count: ((answer.count % 3) + 1) as 1 | 2 | 3, fill: answer.fill },
      {
        shape: answer.shape,
        count: (((answer.count + 1) % 3) + 1) as 1 | 2 | 3,
        fill: fills[(fills.indexOf(answer.fill) + 1) % 3],
      },
      {
        shape: shapes[(shapes.indexOf(answer.shape) + 1) % 3],
        count: ((answer.count % 3) + 1) as 1 | 2 | 3,
        fill: answer.fill,
      },
    ];

    const used = new Set<string>([keyOf(answer)]);
    for (const cand of candidates) {
      const k = keyOf(cand);
      if (!used.has(k) && distractors.length < 3) {
        used.add(k);
        distractors.push(cand);
      }
    }

    const matrixOptions = shuffleWithState([answer, ...distractors], st);
    const correctIndex = matrixOptions.findIndex((o) => keyOf(o) === keyOf(answer));

    return {
      kind: 'RAVEN_MATRIX',
      prompt: 'Matriz Lógica 3×3: qual peça completa o canto inferior direito respeitando linha e coluna?',
      matrixGrid: grid,
      matrixOptions,
      correctIndex,
      explanation:
        'Em cada linha e coluna, forma geométrica, quantidade (1–3) e preenchimento seguem distribuição latina sem repetição indevida.',
    };
  }

  // 2) DEDUCAO FORMAL / SILOGISMO (~32% das questoes)
  if (roll < 0.68) {
    const item = DEDUCTION_BANK[Math.floor(nextRand(st) * DEDUCTION_BANK.length)];
    const textOptions = shuffleWithState([item.correct, ...item.wrongs], st);
    return {
      kind: 'DEDUCTION',
      prompt: item.prompt,
      textOptions,
      correctIndex: textOptions.indexOf(item.correct),
      explanation: item.explanation,
    };
  }

  // 3) SEQUENCIA ALGEBRICA / DIFERENCA DE 2ª ORDEM (~32% das questoes)
  const subType = Math.floor(nextRand(st) * 3);
  let seq: number[] = [];
  let ans = 0;
  let explanation = '';

  if (subType === 0) {
    // Diferenca de 2a ordem: d, d+k, d+2k, d+3k, d+4k
    const start = 2 + Math.floor(nextRand(st) * 8);
    const d0 = 2 + Math.floor(nextRand(st) * 4);
    const stepK = difficulty === 1 ? 2 : 3 + Math.floor(nextRand(st) * 3);
    seq = [start];
    let cur = start;
    for (let i = 0; i < 4; i++) {
      cur += d0 + i * stepK;
      seq.push(cur);
    }
    ans = cur + d0 + 4 * stepK;
    explanation = `Os saltos crescem de +${stepK} em +${stepK}: próximo salto é +${d0 + 4 * stepK} = ${ans}.`;
  } else if (subType === 1) {
    // Operacao dupla alternada: x2 + c
    const start = 2 + Math.floor(nextRand(st) * 4);
    const addC = 1 + Math.floor(nextRand(st) * 3);
    seq = [start];
    let cur = start;
    for (let i = 0; i < 4; i++) {
      cur = i % 2 === 0 ? cur * 2 : cur + addC;
      seq.push(cur);
    }
    ans = cur * 2;
    explanation = `Padrão alternado (×2, depois +${addC}): como o último passo foi +${addC}, agora aplica-se ×2 → ${ans}.`;
  } else {
    // Soma dos dois anteriores deslocada (Fibonacci generalizado)
    const a = 2 + Math.floor(nextRand(st) * 4);
    const b = 3 + Math.floor(nextRand(st) * 5);
    seq = [a, b, a + b, a + 2 * b, 2 * a + 3 * b];
    ans = 3 * a + 5 * b;
    explanation = `Cada termo é a soma exata dos dois anteriores (${seq[3]} + ${seq[4]} = ${ans}).`;
  }

  const deltas = [-4, -2, 2, 3, 5, -6];
  const wrongSet = new Set<number>();
  for (const d of shuffleWithState(deltas, st)) {
    const candidate = ans + d;
    if (candidate > 0 && candidate !== ans && wrongSet.size < 3) {
      wrongSet.add(candidate);
    }
  }
  const textOptions = shuffleWithState(
    [String(ans), ...Array.from(wrongSet).map(String)],
    st,
  );

  return {
    kind: 'SEQUENCE',
    prompt: `Descubra o próximo número da sequência:  ${seq.join('  →  ')}  →  ?`,
    textOptions,
    correctIndex: textOptions.indexOf(String(ans)),
    explanation,
  };
}

export function generateCorsiSequence(
  length: number,
  gridSize: number,
  seed: number,
): number[] {
  const st = { s: (seed ^ 0xc2b2ae35) >>> 0 };
  const totalCells = gridSize * gridSize;
  const indices = Array.from({ length: totalCells }, (_, i) => i);
  const shuffled = shuffleWithState(indices, st);
  return shuffled.slice(0, Math.min(length, totalCells));
}

const LOCI_STATIONS: Array<{ name: string; cue: string }> = [
  { name: '1. Portão de Ferro', cue: 'Imagine o som metálico pesado na entrada' },
  { name: '2. Fonte de Pedra', cue: 'Água gelada espirrando no pátio' },
  { name: '3. Escadaria de Mármore', cue: 'Degraus largos iluminados por tochas' },
  { name: '4. Mesa da Forja', cue: 'Bigorna incandescente soltando faíscas' },
  { name: '5. Biblioteca Circular', cue: 'Estantes altas com cheiro de couro antigo' },
  { name: '6. Observatório de Vidro', cue: 'Telescópio apontado para o céu estrelado' },
  { name: '7. Jardim Suspenso', cue: 'Vento forte balançando árvores douradas' },
  { name: '8. Cofre Subterrâneo', cue: 'Porta blindada giratória no subsolo' },
  { name: '9. Ponte de Cristal', cue: 'Passarela transparente sobre um abismo' },
  { name: '10. Trono do Ápice', cue: 'Sala silenciosa no ponto mais alto da torre' },
];

const LOCI_WORDS = [
  'Bússola',
  'Martelo',
  'Relâmpago',
  'Ampulheta',
  'Escudo',
  'Telescópio',
  'Corvo',
  'Diamante',
  'Âncora',
  'Engrenagem',
  'Lanterna',
  'Chave',
  'Espada',
  'Microscópio',
  'coroa',
  'Pêndulo',
  'Águia',
  'Sino',
  'Cristal',
  'Tridente',
].map((w) => w.charAt(0).toUpperCase() + w.slice(1));

export function generateLociDeck(difficulty: 1 | 2 | 3, seed: number): LociDeck {
  const st = { s: (seed ^ 0x27d4eb2f) >>> 0 };
  const count = difficulty === 1 ? 5 : difficulty === 2 ? 7 : 9;
  const words = shuffleWithState(LOCI_WORDS, st).slice(0, count);

  const pairs: LociPair[] = words.map((word, idx) => ({
    stationIndex: idx,
    stationName: LOCI_STATIONS[idx].name,
    stationCue: LOCI_STATIONS[idx].cue,
    targetWord: word,
  }));

  const a = 34 + Math.floor(nextRand(st) * 45);
  const b = 13 + Math.floor(nextRand(st) * 19);
  const diff = a - b;
  const opts = shuffleWithState(
    [String(diff), String(diff + 2), String(diff - 3), String(diff + 10)],
    st,
  );

  return {
    pairs,
    interferencePrompt: `Filtro Anti-Repetição Curta (limpa o loop fonológico antes da evocação real): quanto é ${a} − ${b}?`,
    interferenceOptions: opts,
    interferenceCorrectIndex: opts.indexOf(String(diff)),
  };
}

export function getWordsPool(): string[] {
  return [...LOCI_WORDS];
}

export interface NumeracyPuzzle {
  category: 'REGRA_72' | 'BAYES_GIGERENZER' | 'ASSIMETRIA_PERDA' | 'FERMI_ESCALA';
  prompt: string;
  options: [string, string, string, string];
  correctIndex: 0 | 1 | 2 | 3;
  mentalShortcut: string;
}

export function generateNumeracyQuestion(seed: number, difficulty: 1 | 2 | 3): NumeracyPuzzle {
  const st = { s: (seed ^ 0x517cc1b7) >>> 0 };
  const roll = Math.floor(nextRand(st) * 4);

  if (roll === 0) {
    const rates = difficulty === 1 ? [6, 8, 12] : difficulty === 2 ? [4, 6, 9, 12, 18] : [3, 4, 8, 9, 12, 18, 24];
    const rate = rates[Math.floor(nextRand(st) * rates.length)];
    const periods = 72 / rate;
    const unit = rate >= 9 && nextRand(st) < 0.5 ? 'meses' : 'anos';
    const rateLabel = unit === 'meses' ? `${rate}% ao mês` : `${rate}% ao ano`;
    const correct = `${periods} ${unit}`;
    const rawDistractors = [
      `${periods + 3} ${unit}`,
      `${Math.max(1, periods - 2)} ${unit}`,
      `${periods * 2} ${unit}`,
      `${periods + 6} ${unit}`,
    ].filter((x) => x !== correct);
    const uniqueDistractors = Array.from(new Set(rawDistractors)).slice(0, 3);
    const options = shuffleWithState([correct, ...uniqueDistractors], st) as [
      string,
      string,
      string,
      string,
    ];
    return {
      category: 'REGRA_72',
      prompt: `Regra dos 72 (Juros Compostos): um capital ou dívida crescendo a ${rateLabel} dobra de tamanho em aproximadamente quanto tempo?`,
      options,
      correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
      mentalShortcut: `Atalho mental: 72 ÷ ${rate} = ${periods} ${unit}.`,
    };
  }

  if (roll === 1) {
    const cases: { tp: number; fp: number; totalPop: number }[] = [
      { tp: 10, fp: 10, totalPop: 100 },
      { tp: 10, fp: 30, totalPop: 200 },
      { tp: 15, fp: 5, totalPop: 100 },
      { tp: 5, fp: 20, totalPop: 200 },
      { tp: 9, fp: 21, totalPop: 300 },
      { tp: 16, fp: 4, totalPop: 100 },
    ];
    const c = cases[Math.floor(nextRand(st) * cases.length)];
    const alarms = c.tp + c.fp;
    const pct = Math.round((c.tp / alarms) * 100);
    const correct = `${c.tp} em ${alarms} (${pct}%)`;
    const candidates = [
      `${alarms} em ${alarms} (100%)`,
      `${c.fp} em ${c.totalPop} (${Math.round((c.fp / c.totalPop) * 100)}%)`,
      `${Math.max(1, c.tp - 2)} em 100 (95%)`,
      `1 em ${c.totalPop} (1%)`,
    ].filter((x) => x !== correct);
    const uniqueDistractors = Array.from(new Set(candidates)).slice(0, 3);
    const options = shuffleWithState([correct, ...uniqueDistractors], st) as [
      string,
      string,
      string,
      string,
    ];
    return {
      category: 'BAYES_GIGERENZER',
      prompt: `Frequências Naturais: em ${c.totalPop} alertas analisados, o detector acerta ${c.tp} casos reais, mas também dispara ${c.fp} alarmes falsos (total = ${alarms} apitos). Quando ele apita, qual é a chance real de ser verdadeiro?`,
      options,
      correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
      mentalShortcut: `Some todos os apitos (${c.tp} reais + ${c.fp} falsos = ${alarms}): ${c.tp} em ${alarms} = ${pct}%.`,
    };
  }

  if (roll === 2) {
    const pairs = [
      { loss: 20, rest: 80, gain: 25 },
      { loss: 50, rest: 50, gain: 100 },
      { loss: 60, rest: 40, gain: 150 },
      { loss: 75, rest: 25, gain: 300 },
      { loss: 80, rest: 20, gain: 400 },
    ];
    const p = pairs[Math.floor(nextRand(st) * pairs.length)];
    const correct = `+${p.gain}%`;
    const candidates = [`+${p.loss}%`, `+${p.loss + 10}%`, `+${p.gain + 50}%`, `+${Math.max(5, p.loss - 5)}%`].filter(
      (x) => x !== correct,
    );
    const uniqueDistractors = Array.from(new Set(candidates)).slice(0, 3);
    const options = shuffleWithState([correct, ...uniqueDistractors], st) as [
      string,
      string,
      string,
      string,
    ];
    return {
      category: 'ASSIMETRIA_PERDA',
      prompt: `Assimetria de Risco: se R$ 100 sofrem queda de ${p.loss}% (caindo para R$ ${p.rest}), quantos % de ganho sobre os R$ ${p.rest} são necessários para voltar aos R$ 100?`,
      options,
      correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
      mentalShortcut: `Você precisa recuperar R$ ${p.loss} partindo de uma base menor (R$ ${p.rest}): ${p.loss} ÷ ${p.rest} = +${p.gain}%!`,
    };
  }

  // roll === 3: FERMI_ESCALA
  const dailyChoices = [
    { minPerDay: 20, days: 30, hours: 10 },
    { minPerDay: 30, days: 30, hours: 15 },
    { minPerDay: 40, days: 30, hours: 20 },
    { minPerDay: 45, days: 40, hours: 30 },
    { minPerDay: 60, days: 30, hours: 30 },
  ];
  const f = dailyChoices[Math.floor(nextRand(st) * dailyChoices.length)];
  const correct = `${f.hours} horas`;
  const candidates = [
    `${Math.max(2, Math.floor(f.hours / 3))} horas`,
    `${f.hours + 8} horas`,
    `${f.hours * 3} horas`,
    `${f.hours + 15} horas`,
  ].filter((x) => x !== correct);
  const uniqueDistractors = Array.from(new Set(candidates)).slice(0, 3);
  const options = shuffleWithState([correct, ...uniqueDistractors], st) as [
    string,
    string,
    string,
    string,
  ];
  return {
    category: 'FERMI_ESCALA',
    prompt: `Escala de Fermi: redirecionar ${f.minPerDay} minutos por dia de distração para estudo focado durante ${f.days} dias acumula quantas horas líquidas de prática?`,
    options,
    correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
    mentalShortcut: `${f.minPerDay} min × ${f.days} dias = ${f.minPerDay * f.days} min ÷ 60 = ${f.hours} horas inteiras!`,
  };
}

export interface WisdomDiscernmentPuzzle {
  category:
    | 'VIES_SOBREVIVENCIA'
    | 'CUSTO_AFUNDADO'
    | 'PARADOXO_SALOMAO'
    | 'FALACIA_LOGICA'
    | 'PRUDENCIA_CARATER'
    | 'SEGUNDA_ORDEM_RUINA';
  prompt: string;
  options: [string, string, string, string];
  correctIndex: 0 | 1 | 2 | 3;
  principleAnchor: string;
}

export function generateWisdomDiscernmentQuestion(
  seed: number,
  difficulty: 1 | 2 | 3,
): WisdomDiscernmentPuzzle {
  const st = { s: (seed ^ 0x517cc1b7) >>> 0 };
  const poolSize = difficulty === 1 ? 4 : 6;
  const roll = Math.floor(nextRand(st) * poolSize);

  if (roll === 0) {
    const totals = [200, 500, 1000, 2000];
    const total = totals[Math.floor(nextRand(st) * totals.length)];
    const winners = difficulty === 3 ? 2 : 1;
    const silent = total - winners;
    const correct = `Viés de Sobrevivência: faltam os ${silent} em ${total} que fizeram o mesmo e quebraram em silêncio.`;
    const distractors = [
      `Prova definitiva: se deu certo para ${winners}, dará certo para 100% de quem copiar.`,
      'Lei dos Grandes Números: amostras de 1 caso provam causalidade universal.',
      'Efeito Halo: quem fala com confiança no vídeo não sofre risco estatístico.',
    ];
    const options = shuffleWithState([correct, ...distractors], st) as [
      string,
      string,
      string,
      string,
    ];
    return {
      category: 'VIES_SOBREVIVENCIA',
      prompt: `Em uma área arriscada, ${total} iniciantes abandonaram os fundamentos e apostaram tudo no escuro: ${silent} faliram calados e ${winners} teve sorte e viralizou dizendo "estudar fundamentos é inútil!". Qual é o diagnóstico exato?`,
      options,
      correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
      principleAnchor: `Abraham Wald (1943): sempre exija o denominador invisível (${winners}/${total}) antes de copiar sobreviventes de roleta.`,
    };
  }

  if (roll === 1) {
    const months = [6, 12, 18, 24][Math.floor(nextRand(st) * 4)];
    const futureLoss = [300, 600, 900][Math.floor(nextRand(st) * 3)];
    const correct = `Ignorar os ${months} meses já passados (irrecuperáveis) e decidir apenas pelo melhor retorno futuro das próximas horas.`;
    const distractors = [
      `Gastar mais ${futureLoss} horas no erro só para "honrar" os ${months} meses já perdidos.`,
      'Dobrar a teimosia sem mudar o método para não admitir que o caminho inicial falhou.',
      'Parar de estudar qualquer coisa na vida para nunca mais errar.',
    ];
    const options = shuffleWithState([correct, ...distractors], st) as [
      string,
      string,
      string,
      string,
    ];
    return {
      category: 'CUSTO_AFUNDADO',
      prompt: `Você investiu ${months} meses num método comprovadamente furado que exigirá mais ${futureLoss} horas sem dar resultado, enquanto existe outro caminho superior disponível hoje. Qual é a decisão racional?`,
      options,
      correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
      principleAnchor: 'Falácia do Custo Afundado (Arkes & Blumer, 1985; Thaler): tempo passado já foi pago; só o futuro entra na conta.',
    };
  }

  if (roll === 2) {
    const names = ['Lucas', 'Marina', 'Rafael', 'Helena'];
    const person = names[Math.floor(nextRand(st) * names.length)];
    const correct = `Distanciar-se em 3ª pessoa ("O que um mestre sábio aconselharia ${person} a fazer agora?") antes de responder.`;
    const distractors = [
      'Responder no primeiro segundo de raiva em 1ª pessoa para "desabafar tudo".',
      'Ruminar a ofensa por 4 horas seguidas aumentando a adrenalina.',
      'Fingir que o problema não existe e tomar decisões impulsivas à meia-noite.',
    ];
    const options = shuffleWithState([correct, ...distractors], st) as [
      string,
      string,
      string,
      string,
    ];
    return {
      category: 'PARADOXO_SALOMAO',
      prompt: `${person} recebeu uma provocação injusta e precisa tomar uma decisão séria em 5 minutos com o coração acelerado. Qual técnica comprovada destrava sabedoria imediata?`,
      options,
      correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
      principleAnchor: 'Paradoxo de Salomão (Grossmann & Kross, Psychological Science, 2014) + Pv 16:32: a 3ª pessoa corta a cegueira emocional.',
    };
  }

  if (roll === 3) {
    const correct =
      'Falácia Ad Hominem + Espantalho: atacou a pessoa e distorceu a tese em vez de refutar os dados apresentados.';
    const distractors = [
      'Argumento dedutivo válido: quem fala mais alto vence logicamente o debate.',
      'Inferência Forte de Platt: xingar o interlocutor elimina hipóteses científicas.',
      'Princípio da Caridade (Steelman): resumiu a posição alheia melhor que o autor.',
    ];
    const options = shuffleWithState([correct, ...distractors], st) as [
      string,
      string,
      string,
      string,
    ];
    return {
      category: 'FALACIA_LOGICA',
      prompt: `Em uma análise técnica, alguém propõe: "Devemos revisar o freio antes de acelerar". O outro responde: "Você é novato demais e quer que a empresa pare para sempre!". Qual erro lógico ocorreu?`,
      options,
      correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
      principleAnchor: 'Mapa de Argumento (van Gelder) + Homem de Aço: ataque sempre o argumento real com dados, nunca caricaturas ou pessoas.',
    };
  }

  if (roll === 4) {
    const correct =
      'Ouvir com gratidão a correção leal baseada em fatos e desconfiar da bajulação que pede atalho sem verificação.';
    const distractors = [
      'Afastar quem aponta erros técnicos com respeito e cercar-se apenas de bajuladores.',
      'Entregar recursos e senhas sem contrato para quem elogiou seu talento.',
      'Guardar rancor eterno de qualquer mentor que corrija sua postura.',
    ];
    const options = shuffleWithState([correct, ...distractors], st) as [
      string,
      string,
      string,
      string,
    ];
    return {
      category: 'PRUDENCIA_CARATER',
      prompt: `Dois conhecidos falam com você: o primeiro elogia exageradamente seu ego e pede dinheiro rápido sem garantia; o segundo, em particular, mostra um erro real no seu projeto e como consertá-lo. Como age a Sabedoria?`,
      options,
      correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
      principleAnchor: 'Provérbios 27:6 & 29:5 + Mateus 10:16: "Leais são as feridas feitas pelo amigo", enquanto a lisonja arma rede aos passos.',
    };
  }

  // roll === 5: SEGUNDA_ORDEM_RUINA
  const ruinPct = [15, 20, 25][Math.floor(nextRand(st) * 3)];
  const gainPct = [40, 60, 80][Math.floor(nextRand(st) * 3)];
  const correct =
    'Rejeitar risco de ruína total: num sistema repetido, multiplicar tudo por zero uma única vez apaga todos os ganhos anteriores.';
  const distractors = [
    `Apostar 100% da reserva repetidas vezes porque +${gainPct}% parece maior que ${ruinPct}%.`,
    'Olhar apenas o ganho imediato de 1ª ordem dos primeiros 5 minutos.',
    'Remover todas as travas de segurança sem saber para que foram criadas.',
  ];
  const options = shuffleWithState([correct, ...distractors], st) as [
    string,
    string,
    string,
    string,
  ];
  return {
    category: 'SEGUNDA_ORDEM_RUINA',
    prompt: `Uma aposta repetida oferece chance de ganhar +${gainPct}%, mas ${ruinPct}% de chance de perda total irreversível (-100% da sua reserva ou reputação). Pela matemática não-ergódica e 2ª ordem, qual é a regra certa?`,
    options,
    correctIndex: options.indexOf(correct) as 0 | 1 | 2 | 3,
    principleAnchor: 'Critério de Kelly (1956) & Ole Peters (Nature Physics, 2019): sobrevivência (risco zero de ruína) precede qualquer multiplicação.',
  };
}

// ============================================================================
// 7. CALIBRACAO BAYESIANA & PONTUACAO DE BRIER (TETLOCK SUPERFORECASTING)
// ============================================================================

export type CalibrationConfidencePct = 55 | 75 | 95;

export interface TetlockCalibrationPuzzle {
  category:
    | 'TAXA_BASE_AMOSTRA'
    | 'REGRESSAO_MEDIA'
    | 'JUROS_INFLACAO_REAL'
    | 'FISIOLOGIA_EVIDENCIA';
  statement: string;
  options: [string, string];
  correctIndex: 0 | 1;
  explanation: string;
}

/**
 * Calcula pontos de calibracao baseados na Regra Quadratica Estrita de Brier (1950):
 * Brier = (p - outcome)^2, onde outcome = 1 se acertou e 0 se errou.
 * - Acertar com 95%: Brier = 0.0025 -> +166 pts (Premio maximo por certeza bem fundada)
 * - Acertar com 75%: Brier = 0.0625 -> +146 pts
 * - Acertar com 55%: Brier = 0.2025 -> +118 pts
 * - Errar com 55% (Humildade honesta): Brier = 0.3025 -> +95 pts (Protege contra chute arrogante!)
 * - Errar com 75%: Brier = 0.5625 -> +48 pts
 * - Errar com 95% (Arrogancia Dunning-Kruger): Brier = 0.9025 -> +0 pts!
 */
export function computeBrierRoundPoints(
  wasCorrect: boolean,
  confidencePct: CalibrationConfidencePct,
): { roundPoints: number; brierError: number } {
  const p = confidencePct / 100;
  const outcome = wasCorrect ? 1 : 0;
  const brierError = Number(((p - outcome) * (p - outcome)).toFixed(4));
  // Mapeia Brier [0.0025 .. 0.9025] -> [167 .. 0] para que 6 rodadas somem ate ~1000 pts
  const normalized = Math.max(0, (0.9025 - brierError) / 0.9);
  const roundPoints = Math.round(normalized * 167);
  return { roundPoints, brierError };
}

export function generateTetlockCalibrationQuestion(
  seed: number,
  difficulty: 1 | 2 | 3,
): TetlockCalibrationPuzzle {
  const st = { s: (seed ^ 0x9e3779b9) >>> 0 };
  const poolSize = difficulty === 1 ? 3 : 4;
  const roll = Math.floor(nextRand(st) * poolSize);

  if (roll === 0) {
    const smallN = [3, 4, 5][Math.floor(nextRand(st) * 3)];
    const bigN = [1200, 2500, 5000][Math.floor(nextRand(st) * 3)];
    const correct = `A clínica pequena (${smallN} casos/mês), pois amostras minúsculas sofrem variância extrema (Lei dos Pequenos Números).`;
    const wrong = `O grande hospital (${bigN} casos/mês), pois mais volume gera mais oscilações percentuais extremas.`;
    const swap = nextRand(st) < 0.5;
    const options: [string, string] = swap ? [wrong, correct] : [correct, wrong];
    return {
      category: 'TAXA_BASE_AMOSTRA',
      statement: `Em um determinado mês, um local registrou 80% de sucesso cirúrgico (muito acima da média nacional de 50%). Onde esse extremo de 80% tem MAIOR probabilidade matemática de acontecer por puro acaso?`,
      options,
      correctIndex: swap ? 1 : 0,
      explanation:
        'Tversky & Kahneman (1971): quanto MENOR o tamanho da amostra (N), maiores são os desvios extremos por sorte ou azar.',
    };
  }

  if (roll === 1) {
    const score = [98, 99, 100][Math.floor(nextRand(st) * 3)];
    const correct =
      'Regressão estatística natural à média: desempenhos extremos de sorte tendem a voltar ao centro na tentativa seguinte.';
    const wrong =
      'Prova causal de que elogiar destrói a técnica e gritar melhora imediatamente a habilidade motora.';
    const swap = nextRand(st) < 0.5;
    const options: [string, string] = swap ? [wrong, correct] : [correct, wrong];
    return {
      category: 'REGRESSAO_MEDIA',
      statement: `Um aprendiz faz uma tentativa espetacular rara (${score}/100), recebe um elogio e na tentativa seguinte faz 78/100. Outro vai péssimo (30/100), leva bronca e na tentativa seguinte sobe para 62/100. Qual fenômeno explica isso?`,
      options,
      correctIndex: swap ? 1 : 0,
      explanation:
        'Descoberta clássica de Daniel Kahneman com instrutores de voo: extremos incluem sorte/azar pontual e regredirão à média independentemente de grito ou elogio.',
    };
  }

  if (roll === 2) {
    const nomPct = [8, 10, 12][Math.floor(nextRand(st) * 3)];
    const infPct = nomPct + 3;
    const correct =
      'Empobreceu em poder de compra real (~3% mais pobre), apesar de ver mais dinheiro nominal na conta.';
    const wrong = `Enriqueceu ${nomPct}% em poder de compra, pois o saldo nominal subiu sem perdas.`;
    const swap = nextRand(st) < 0.5;
    const options: [string, string] = swap ? [wrong, correct] : [correct, wrong];
    return {
      category: 'JUROS_INFLACAO_REAL',
      statement: `Seu patrimônio subiu +${nomPct}% nominais no ano, enquanto a inflação da cesta de vida subiu ${infPct}% no mesmo período. O que aconteceu na realidade física?`,
      options,
      correctIndex: swap ? 1 : 0,
      explanation:
        'Shafir, Diamond & Tversky (QJE, 1997 — Ilusão Monetária): retorno real exige descontar a inflação ((1 + nominal)/(1 + inflação) - 1 < 0).',
    };
  }

  const lossPct = [2, 3][Math.floor(nextRand(st) * 2)];
  const correct =
    'Falso: meta-análises mostram ZERO melhora de humor pelo açúcar (com aumento de fadiga em 30–60 min), enquanto 2% de desidratação já reduz atenção executiva.';
  const wrong =
    'Verdadeiro: refrigerante açucarado sustenta foco por 3 horas e o cérebro só sente falta de água acima de 8% de desidratação.';
  const swap = nextRand(st) < 0.5;
  const options: [string, string] = swap ? [wrong, correct] : [correct, wrong];
  return {
    category: 'FISIOLOGIA_EVIDENCIA',
    statement: `Julgue pela literatura científica: "Tomar açúcar puro dá um pico sustentado de bom humor e foco de 2h, e perder ${lossPct}% de água corporal no calor ainda não afeta o cérebro."`,
    options,
    correctIndex: swap ? 1 : 0,
    explanation:
      'Mantantzis et al. (2019, k=31: mito do sugar rush; aumenta fadiga) + Wittbrodt & Millard-Stafford (2018, k=33: 2% de desidratação já degrada cognição).',
  };
}

// ============================================================================
// 8. MEMORIA OPERACIONAL N-BACK ATUALIZAVEL (KIRCHNER 1958 / MIYAKE 2000)
// ============================================================================

export interface NBackTrialItem {
  stepIndex: number;
  symbol: string;
  gridPos: number; // 0..8
  isTargetMatch: boolean; // Igual ao item de N passos atras (simbolo)
}

export interface NBackSequenceSpec {
  nBack: 1 | 2 | 3;
  items: NBackTrialItem[];
}

const NBACK_SYMBOLS = ['Δ', 'Ω', 'Σ', 'Φ', 'Ψ', 'Λ'];

/**
 * Gera uma sequencia deterministica balanceada (~35%-45% alvos verdadeiros) para 1-Back, 2-Back ou 3-Back.
 */
export function generateNBackSequence(
  seed: number,
  difficulty: 1 | 2 | 3,
  totalItems = 14,
): NBackSequenceSpec {
  const st = { s: (seed ^ 0x85ebca6b) >>> 0 };
  const nBack = difficulty;
  const items: NBackTrialItem[] = [];

  for (let i = 0; i < totalItems; i++) {
    if (i < nBack) {
      const sym = NBACK_SYMBOLS[Math.floor(nextRand(st) * NBACK_SYMBOLS.length)];
      const pos = Math.floor(nextRand(st) * 9);
      items.push({ stepIndex: i, symbol: sym, gridPos: pos, isTargetMatch: false });
      continue;
    }

    const forceMatch = nextRand(st) < 0.42;
    const refSym = items[i - nBack].symbol;
    let chosenSym = refSym;
    if (!forceMatch) {
      const others = NBACK_SYMBOLS.filter((s) => s !== refSym);
      chosenSym = others[Math.floor(nextRand(st) * others.length)];
    }
    const pos = forceMatch
      ? items[i - nBack].gridPos
      : Math.floor(nextRand(st) * 9);
    items.push({
      stepIndex: i,
      symbol: chosenSym,
      gridPos: pos,
      isTargetMatch: chosenSym === refSym,
    });
  }

  // Garante pelo menos 3 alvos reais na bateria e revalida invariante em cascata (zero descompasso em i + nBack)
  for (let i = nBack; i < totalItems; i++) {
    for (let k = nBack; k < totalItems; k++) {
      items[k].isTargetMatch = items[k].symbol === items[k - nBack].symbol;
    }
    if (items.slice(nBack).filter((x) => x.isTargetMatch).length >= 3) break;
    if (!items[i].isTargetMatch) {
      items[i].symbol = items[i - nBack].symbol;
      items[i].gridPos = items[i - nBack].gridPos;
    }
  }

  for (let k = 0; k < totalItems; k++) {
    items[k].isTargetMatch = k >= nBack && items[k].symbol === items[k - nBack].symbol;
  }

  return { nBack, items };
}

export interface TrailNodeItem {
  cellIndex: number;
  label: string;         // '1', 'A', '2', 'B', ...
  sequenceOrder: number; // 0..totalNodes-1
  kind: 'NUMBER' | 'LETTER';
}

export interface TrailShiftingBoard {
  difficulty: 1 | 2 | 3;
  totalNodes: number;
  columns: 4;
  targetSequence: string[]; // ['1', 'A', '2', 'B', ...]
  cells: TrailNodeItem[];   // Embaralhado deterministicamente na grade
}

const TRAIL_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];

/**
 * 9a Disciplina Cognitiva: Trail Making Test Part B Executivo (Reitan, 1958; Arbuthnott & Frank, 2000).
 * Completa a Triade de Funcoes Executivas de Miyake et al. (Cognitive Psychology, 2000):
 * 1) Inibicao (Stroop), 2) Atualizacao (N-Back), 3) Alternancia de Conjunto Mental / Shifting (1-A-2-B-3-C).
 */
export function generateTrailShiftingBoard(
  seed: number,
  difficulty: 1 | 2 | 3,
): TrailShiftingBoard {
  const st = { s: (seed ^ 0xc2b2ae35) >>> 0 };
  const pairsCount = difficulty === 1 ? 6 : difficulty === 2 ? 8 : 10;
  const totalNodes = pairsCount * 2;
  const targetSequence: string[] = [];
  const orderedItems: Omit<TrailNodeItem, 'cellIndex'>[] = [];

  for (let p = 0; p < pairsCount; p++) {
    const numLabel = String(p + 1);
    const letLabel = TRAIL_LETTERS[p];
    targetSequence.push(numLabel, letLabel);
    orderedItems.push(
      { label: numLabel, sequenceOrder: p * 2, kind: 'NUMBER' },
      { label: letLabel, sequenceOrder: p * 2 + 1, kind: 'LETTER' },
    );
  }

  // Embaralhamento Fisher-Yates deterministico sem colisoes
  const shuffled = [...orderedItems];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(nextRand(st) * (i + 1));
    const tmp = shuffled[i];
    shuffled[i] = shuffled[j];
    shuffled[j] = tmp;
  }

  // Evita que '1' e 'A' fiquem colados nos indices 0 e 1 triviais
  if (shuffled[0].sequenceOrder === 0 && shuffled[1].sequenceOrder === 1) {
    const swapIdx = Math.min(shuffled.length - 1, 5);
    const tmp = shuffled[1];
    shuffled[1] = shuffled[swapIdx];
    shuffled[swapIdx] = tmp;
  }

  const cells: TrailNodeItem[] = shuffled.map((item, idx) => ({
    ...item,
    cellIndex: idx,
  }));

  return {
    difficulty,
    totalNodes,
    columns: 4,
    targetSequence,
    cells,
  };
}


// ============================================================================
// NOVOS DESAFIOS COGNITIVOS v16.0.0 — Flanker & Go/No-Go
// ============================================================================

/** Tarefa de Flanker (Eriksen, 1974): controle inibitório e atenção seletiva.
 * O alvo é a seta do centro; as setas laterais são distractores congruentes ou incongruentes. */
export interface FlankerTrial {
  congruent: boolean;
  direction: 'LEFT' | 'RIGHT';
  options: string[]; // ['ESQUERDA', 'DIREITA']
  correctIndex: number;
}

export function generateFlankerTrial(seed: number, difficulty: 1 | 2 | 3): FlankerTrial {
  const st = { s: seed >>> 0 };
  const next = () => { st.s = (Math.imul(st.s, 1664525) + 1013904223) >>> 0; return st.s / 4294967296; };
  const dir = next() < 0.5 ? 'LEFT' : 'RIGHT';
  const congruent = next() < 0.5;
  const centerArrow = dir === 'LEFT' ? '←' : '→';
  const flankerArrow = congruent ? centerArrow : (dir === 'LEFT' ? '→' : '←');
  const stimulus = `${flankerArrow}${centerArrow}${flankerArrow}`;
  const correctIndex = dir === 'LEFT' ? 0 : 1;

  return {
    congruent,
    direction: dir,
    options: ['ESQUERDA', 'DIREITA'],
    correctIndex,
  };
}

/** Tarefa Go/No-Go: inibição de resposta. Aperte para "Go", não aperte para "No-Go". */
export interface GoNoGoTrial {
  isGo: boolean;
  stimulus: string;
  options: string[]; // ['APERTAR', 'NAO_APERTAR']
  correctIndex: number;
}

export function generateGoNoGoTrial(seed: number, difficulty: 1 | 2 | 3): GoNoGoTrial {
  const st = { s: seed >>> 0 };
  const next = () => { st.s = (Math.imul(st.s, 1664525) + 1013904223) >>> 0; return st.s / 4294967296; };
  // ~70% Go, ~30% No-Go para criar pressão de inibição
  const isGo = next() < 0.7;
  const stimulus = isGo ? '○' : '✕';
  const correctIndex = isGo ? 0 : 1;

  return {
    isGo,
    stimulus,
    options: ['APERTAR', 'NAO_APERTAR'],
    correctIndex,
  };
}









// ============================================================================
// NOVOS DESAFIOS COGNITIVOS v17.0.0 — Dual N-Back & Attention Control
// ============================================================================

/**
 * Dual N-Back (Jaeggi et al., 2008): memoria de trabalho dupla (visual + auditivo simulado).
 * O usuário deve lembrar se a posicao na grade (visual) ou o simbolo (auditivo simulado)
 * se repetem de N passos atras.
 */
export interface DualNBackTrial {
  stepIndex: number;
  visualPos: number;   // 0..8 na grade 3x3
  audioSymbol: string; // 'A' | 'B' | 'C' | 'D' (simulado por texto)
  isVisualTarget: boolean;  // posicao igual a N passos atras
  isAudioTarget: boolean;   // simbolo igual a N passos atras
  isEitherTarget: boolean;  // qualquer um dos dois
}

export function generateDualNBackSequence(
  seed: number,
  difficulty: 1 | 2 | 3,
  totalItems = 12,
): { nBack: number; items: DualNBackTrial[] } {
  const st = { s: (seed ^ 0x1c7d9e4f) >>> 0 };
  const nBack = difficulty === 1 ? 1 : difficulty === 2 ? 2 : 3;
  const positions = [0, 1, 2, 3, 4, 5, 6, 7, 8];
  const audioSymbols = ['A', 'B', 'C', 'D'];
  const items: DualNBackTrial[] = [];

  for (let i = 0; i < totalItems; i++) {
    if (i < nBack) {
      items.push({
        stepIndex: i,
        visualPos: positions[Math.floor(Math.random() * positions.length)],
        audioSymbol: audioSymbols[Math.floor(Math.random() * audioSymbols.length)],
        isVisualTarget: false,
        isAudioTarget: false,
        isEitherTarget: false,
      });
      continue;
    }

    const forceVisual = Math.random() < 0.35;
    const forceAudio = Math.random() < 0.35;

    const refVisual = items[i - nBack].visualPos;
    const refAudio = items[i - nBack].audioSymbol;

    const visualPos = forceVisual ? refVisual : positions[Math.floor(Math.random() * positions.length)];
    const audioSymbol = forceAudio ? refAudio : audioSymbols[Math.floor(Math.random() * audioSymbols.length)];

    const isVisualTarget = visualPos === refVisual;
    const isAudioTarget = audioSymbol === refAudio;
    const isEitherTarget = isVisualTarget || isAudioTarget;

    items.push({
      stepIndex: i,
      visualPos,
      audioSymbol,
      isVisualTarget,
      isAudioTarget,
      isEitherTarget,
    });
  }

  // Garante pelo menos 2 alvos de cada tipo
  for (let i = nBack; i < totalItems; i++) {
    if (items.filter((x) => x.isVisualTarget).length < 2) {
      items[i].visualPos = items[i - nBack].visualPos;
      items[i].isVisualTarget = true;
      items[i].isEitherTarget = items[i].isVisualTarget || items[i].isAudioTarget;
    }
    if (items.filter((x) => x.isAudioTarget).length < 2) {
      items[i].audioSymbol = items[i - nBack].audioSymbol;
      items[i].isAudioTarget = true;
      items[i].isEitherTarget = items[i].isVisualTarget || items[i].isAudioTarget;
    }
  }

  return { nBack, items };
}

/**
 * Attention Control / Posner Cueing Task: atencao seletiva e inibicao de retorno.
 * O alvo aparece apos um sinal (cue) valido ou invalido; mede o custo de desviar atencao.
 */
export interface AttentionControlTrial {
  cueValid: boolean;      // o sinal aponta para o lado correto?
  targetSide: 'LEFT' | 'RIGHT';
  targetSymbol: string;   // '*' ou '+'
  options: string[];      // ['ESQUERDA', 'DIREITA']
  correctIndex: number;
  distractorPresent: boolean; // distractor no lado oposto?
}

export function generateAttentionControlTrial(
  seed: number,
  difficulty: 1 | 2 | 3,
): AttentionControlTrial {
  const st = { s: (seed ^ 0x5f3759df) >>> 0 };
  const next = () => { st.s = (Math.imul(st.s, 1664525) + 1013904223) >>> 0; return st.s / 4294967296; };

  const targetSide = next() < 0.5 ? 'LEFT' : 'RIGHT';
  // Dificuldade maior -> mais cues invalidos e distractors
  const cueValidProb = difficulty === 1 ? 0.8 : difficulty === 2 ? 0.6 : 0.45;
  const cueValid = next() < cueValidProb;
  const distractorPresent = difficulty >= 2 && next() < 0.5;

  const targetSymbol = next() < 0.5 ? '*' : '+';
  const correctIndex = targetSide === 'LEFT' ? 0 : 1;

  return {
    cueValid,
    targetSide,
    targetSymbol,
    options: ['ESQUERDA', 'DIREITA'],
    correctIndex,
    distractorPresent,
  };
}






// ============================================================================
// NOVOS DESAFIOS COGNITIVOS v18.0.0 — Reaction Time & Working Memory Span
// ============================================================================

/**
 * Reaction Time Task: tempo de reação simples e de escolha.
 * Mede a velocidade de processamento psicomotor e inibição de resposta prematura.
 */
export interface ReactionTimeTrial {
  trialType: 'SIMPLE' | 'CHOICE';
  stimulus: string;          // '●' ou 'A'/'B'
  correctResponse: string;   // 'APERTAR' ou 'ESQUERDA'/'DIREITA'
  options: string[];
  correctIndex: number;
  goSignalColor: string;     // '#ef4444' vermelho para aguardar, '#10b981' verde para ir
}

export function generateReactionTimeTrial(
  seed: number,
  difficulty: 1 | 2 | 3,
): ReactionTimeTrial {
  const st = { s: (seed ^ 0x9e3779b9) >>> 0 };
  const next = () => { st.s = (Math.imul(st.s, 1664525) + 1013904223) >>> 0; return st.s / 4294967296; };

  const isSimple = difficulty === 1 || next() < 0.6;

  if (isSimple) {
    // Reaction Time Simples: espere o sinal verde, aperte rápido
    return {
      trialType: 'SIMPLE',
      stimulus: '●',
      correctResponse: 'APERTAR',
      options: ['APERTAR', 'NAO_APERTAR'],
      correctIndex: 0,
      goSignalColor: '#10b981',
    };
  }

  // Reaction Time de Escolha: estímulo A ou B, resposta correspondente
  const stimulusChar = next() < 0.5 ? 'A' : 'B';
  const correctIndex = stimulusChar === 'A' ? 0 : 1;

  return {
    trialType: 'CHOICE',
    stimulus: stimulusChar,
    correctResponse: stimulusChar === 'A' ? 'ESQUERDA' : 'DIREITA',
    options: ['ESQUERDA', 'DIREITA'],
    correctIndex,
    goSignalColor: '#10b981',
  };
}

/**
 * Working Memory Span (Operation Span / Reading Span): memoria de trabalho com processamento simultaneo.
 * O usuario deve lembrar itens enquanto resolve operacoes matemáticas intermediarias.
 */
export interface WorkingMemorySpanItem {
  stepIndex: number;
  operation: string;         // '3 + 4 =' ou '7 - 2 ='
  operationCorrect: boolean; // se o resultado mostrado está correto
  memoryItem: string;        // palavra para memorizar
  memoryPosition: number;    // posicao na sequencia de memoria
}

export interface WorkingMemorySpanSequence {
  totalItems: number;
  items: WorkingMemorySpanItem[];
  recallWords: string[];     // palavras para recordar na ordem correta
}

export function generateWorkingMemorySpan(
  seed: number,
  difficulty: 1 | 2 | 3,
): WorkingMemorySpanSequence {
  const st = { s: (seed ^ 0x85ebca6b) >>> 0 };
  const next = () => { st.s = (Math.imul(st.s, 1664525) + 1013904223) >>> 0; return st.s / 4294967296; };

  const setSize = difficulty === 1 ? 3 : difficulty === 2 ? 5 : 7;
  const words = [
    'Casa', 'Livro', 'Lua', 'Sol', 'Flor', 'Rio', 'Pedra', 'Fogo', 'Árvore', 'Pássaro',
    'Relógio', 'Espelho', 'Chave', 'Caneta', 'Copos', 'Pão', 'Vela', 'Linha', 'Sino', 'Porta',
  ];

  const items: WorkingMemorySpanItem[] = [];
  const recallWords: string[] = [];

  for (let i = 0; i < setSize; i++) {
    const a = 1 + Math.floor(next() * 9);
    const b = 1 + Math.floor(next() * 9);
    const correctResult = a + b;
    const showCorrect = next() < 0.7;
    const shownResult = showCorrect ? correctResult : correctResult + (1 + Math.floor(next() * 4));

    const word = words[i % words.length];
    recallWords.push(word);

    items.push({
      stepIndex: i,
      operation: `${a} + ${b} = ${shownResult}`,
      operationCorrect: showCorrect,
      memoryItem: word,
      memoryPosition: i,
    });
  }

  return { totalItems: setSize, items, recallWords };
}
