import { Chess } from 'chess.js';

export interface OpeningLineSpec {
  eco: string;
  namePt: string;
  movesSan: string[];
  ideaPt: string;
  whiteWinPct: number;
  drawPct: number;
  blackWinPct: number;
}

export interface DetectedOpening {
  eco: string;
  namePt: string;
  ideaPt: string;
  matchedPlyCount: number;
  isExactBookPosition: boolean;
  nextBookCandidates: {
    san: string;
    openingNamePt: string;
    eco: string;
    whiteWinPct: number;
    drawPct: number;
    blackWinPct: number;
  }[];
}

export const OPENING_BOOK_LINES: OpeningLineSpec[] = [
  {
    eco: 'B00',
    namePt: 'Abertura do Peão do Rei',
    movesSan: ['e4'],
    ideaPt: 'Controla d5 e f5 imediatamente e abre diagonais para Dama e Bispo de f1.',
    whiteWinPct: 38,
    drawPct: 32,
    blackWinPct: 30,
  },
  {
    eco: 'C40',
    namePt: 'Jogo Aberto (Duplo Peão do Rei)',
    movesSan: ['e4', 'e5'],
    ideaPt: 'Simetria clássica central: luta imediata pelo centro e desenvolvimento rápido.',
    whiteWinPct: 39,
    drawPct: 33,
    blackWinPct: 28,
  },
  {
    eco: 'C23',
    namePt: 'Abertura do Bispo',
    movesSan: ['e4', 'e5', 'Bc4'],
    ideaPt: 'Aponta imediatamente para f7 mantendo flexibilidade para f4 ou Cf3.',
    whiteWinPct: 40,
    drawPct: 31,
    blackWinPct: 29,
  },
  {
    eco: 'C44',
    namePt: 'Ataque do Cavalo do Rei',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6'],
    ideaPt: 'Brancas atacam e5 e Pretas defendem desenvolvendo o Cavalo natural.',
    whiteWinPct: 39,
    drawPct: 34,
    blackWinPct: 27,
  },
  {
    eco: 'C50',
    namePt: 'Abertura Italiana',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4'],
    ideaPt: 'Mira diretamente o ponto vulnerável f7 e prepara o roque curto rápido.',
    whiteWinPct: 40,
    drawPct: 32,
    blackWinPct: 28,
  },
  {
    eco: 'C53',
    namePt: 'Italiana: Giuoco Piano',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Bc5', 'c3', 'Nf6', 'd4'],
    ideaPt: 'Constrói centro clássico ideal com c3 + d4 pressionando o Bispo de c5.',
    whiteWinPct: 41,
    drawPct: 33,
    blackWinPct: 26,
  },
  {
    eco: 'C54',
    namePt: 'Italiana: Giuoco Pianissimo',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Bc5', 'c3', 'Nf6', 'd3'],
    ideaPt: 'Manobra posicional moderna favorita dos Grandes Mestres para preparar d4 no momento exato.',
    whiteWinPct: 38,
    drawPct: 37,
    blackWinPct: 25,
  },
  {
    eco: 'C51',
    namePt: 'Gambito Evans',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Bc5', 'b4'],
    ideaPt: 'Sacrifica o peão b4 para ganhar tempo explosivo sobre c3, d4 e a diagonal a3-f8.',
    whiteWinPct: 43,
    drawPct: 26,
    blackWinPct: 31,
  },
  {
    eco: 'C55',
    namePt: 'Defesa dos Dois Cavalos',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Nf6'],
    ideaPt: 'Contra-ataca ativamente o peão de e4 em vez de desenvolver passivamente.',
    whiteWinPct: 39,
    drawPct: 31,
    blackWinPct: 30,
  },
  {
    eco: 'C57',
    namePt: 'Ataque Fegatello (Fried Liver)',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Nf6', 'Ng5', 'd5', 'exd5', 'Nxd5', 'Nxf7'],
    ideaPt: 'Sacrifício tático fulminante em f7 para arrastar o Rei preto ao centro.',
    whiteWinPct: 46,
    drawPct: 22,
    blackWinPct: 32,
  },
  {
    eco: 'C60',
    namePt: 'Abertura Espanhola (Ruy López)',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bb5'],
    ideaPt: 'Pressiona indiretamente o defensor de e5, preparando roque e domínio central duradouro.',
    whiteWinPct: 40,
    drawPct: 36,
    blackWinPct: 24,
  },
  {
    eco: 'C65',
    namePt: 'Ruy López: Defesa Berlim ("Muro de Berlim")',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'Nf6'],
    ideaPt: 'Sólida muralha estratégica popularizada por Kramnik contra Kasparov em 2000.',
    whiteWinPct: 35,
    drawPct: 44,
    blackWinPct: 21,
  },
  {
    eco: 'C78',
    namePt: 'Ruy López: Defesa Morphy (Linha Principal)',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6', 'Ba4', 'Nf6', 'O-O'],
    ideaPt: 'Questiona o Bispo branco mantendo flexibilidade para Be7 e b5.',
    whiteWinPct: 39,
    drawPct: 37,
    blackWinPct: 24,
  },
  {
    eco: 'C45',
    namePt: 'Abertura Escocesa',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'd4', 'exd4', 'Nxd4'],
    ideaPt: 'Abre imediatamente o centro e evita linhas longas da Espanhola.',
    whiteWinPct: 40,
    drawPct: 33,
    blackWinPct: 27,
  },
  {
    eco: 'C42',
    namePt: 'Defesa Petroff (Russa)',
    movesSan: ['e4', 'e5', 'Nf3', 'Nf6'],
    ideaPt: 'Contra-ataque simétrico sólido buscando igualdade estrutural limpa.',
    whiteWinPct: 35,
    drawPct: 45,
    blackWinPct: 20,
  },
  {
    eco: 'C47',
    namePt: 'Abertura dos Quatro Cavalos',
    movesSan: ['e4', 'e5', 'Nf3', 'Nc6', 'Nc3', 'Nf6'],
    ideaPt: 'Desenvolvimento clássico harmônico das quatro peças menores antes dos Bispos.',
    whiteWinPct: 37,
    drawPct: 39,
    blackWinPct: 24,
  },
  {
    eco: 'C25',
    namePt: 'Abertura Vienense',
    movesSan: ['e4', 'e5', 'Nc3'],
    ideaPt: 'Protege e4 e mantém a opção agressiva f4 aberta.',
    whiteWinPct: 41,
    drawPct: 30,
    blackWinPct: 29,
  },
  {
    eco: 'C30',
    namePt: 'Gambito do Rei',
    movesSan: ['e4', 'e5', 'f4'],
    ideaPt: 'Clássico romântico: entrega f4 para desviar o peão central preto e abrir a coluna f.',
    whiteWinPct: 42,
    drawPct: 24,
    blackWinPct: 34,
  },
  {
    eco: 'B20',
    namePt: 'Defesa Siciliana',
    movesSan: ['e4', 'c5'],
    ideaPt: 'A resposta mais combativa contra 1.e4: luta por d4 criando jogo assimétrico.',
    whiteWinPct: 37,
    drawPct: 30,
    blackWinPct: 33,
  },
  {
    eco: 'B50',
    namePt: 'Siciliana Aberta',
    movesSan: ['e4', 'c5', 'Nf3', 'd6', 'd4', 'cxd4', 'Nxd4', 'Nf6', 'Nc3'],
    ideaPt: 'Brancas ganham espaço e desenvolvimento; Pretas obtêm coluna c semiaberta e maioria central.',
    whiteWinPct: 38,
    drawPct: 31,
    blackWinPct: 31,
  },
  {
    eco: 'B90',
    namePt: 'Siciliana: Variante Najdorf',
    movesSan: ['e4', 'c5', 'Nf3', 'd6', 'd4', 'cxd4', 'Nxd4', 'Nf6', 'Nc3', 'a6'],
    ideaPt: 'Arma lendária de Fischer e Kasparov: controla b5 e prepara expansão com e5 ou b5.',
    whiteWinPct: 37,
    drawPct: 32,
    blackWinPct: 31,
  },
  {
    eco: 'B70',
    namePt: 'Siciliana: Variante do Dragão',
    movesSan: ['e4', 'c5', 'Nf3', 'd6', 'd4', 'cxd4', 'Nxd4', 'Nf6', 'Nc3', 'g6'],
    ideaPt: 'Fianqueto explosivo em g7 mirando toda a grande diagonal até b2/a1.',
    whiteWinPct: 40,
    drawPct: 27,
    blackWinPct: 33,
  },
  {
    eco: 'B33',
    namePt: 'Siciliana: Variante Sveshnikov',
    movesSan: ['e4', 'c5', 'Nf3', 'Nc6', 'd4', 'cxd4', 'Nxd4', 'Nf6', 'Nc3', 'e5'],
    ideaPt: 'Aceita a casa d5 enfraquecida em troca de jogo dinâmico ativo sobre o Cavalo branco.',
    whiteWinPct: 36,
    drawPct: 36,
    blackWinPct: 28,
  },
  {
    eco: 'B22',
    namePt: 'Siciliana: Variante Alapin (2.c3)',
    movesSan: ['e4', 'c5', 'c3'],
    ideaPt: 'Prepara d4 com peões para construir centro sólido contra a Siciliana.',
    whiteWinPct: 38,
    drawPct: 34,
    blackWinPct: 28,
  },
  {
    eco: 'B23',
    namePt: 'Siciliana Fechada',
    movesSan: ['e4', 'c5', 'Nc3', 'Nc6', 'g3'],
    ideaPt: 'Evita teoria pesada e prepara ataque na ala do Rei com f4.',
    whiteWinPct: 38,
    drawPct: 31,
    blackWinPct: 31,
  },
  {
    eco: 'C00',
    namePt: 'Defesa Francesa',
    movesSan: ['e4', 'e6', 'd4', 'd5'],
    ideaPt: 'Estrutura resiliente que desafia o centro branco imediatamente e contra-ataca em c5.',
    whiteWinPct: 38,
    drawPct: 34,
    blackWinPct: 28,
  },
  {
    eco: 'C02',
    namePt: 'Francesa: Variante do Avanço',
    movesSan: ['e4', 'e6', 'd4', 'd5', 'e5', 'c5', 'c3', 'Nc6'],
    ideaPt: 'Brancas ganham espaço com e5; Pretas bombardeiam a base da cadeia em d4.',
    whiteWinPct: 38,
    drawPct: 31,
    blackWinPct: 31,
  },
  {
    eco: 'B10',
    namePt: 'Defesa Caro-Kann',
    movesSan: ['e4', 'c6', 'd4', 'd5'],
    ideaPt: 'Sólida como rocha: contesta o centro sem prender o Bispo de casas claras c8.',
    whiteWinPct: 37,
    drawPct: 36,
    blackWinPct: 27,
  },
  {
    eco: 'B12',
    namePt: 'Caro-Kann: Variante do Avanço',
    movesSan: ['e4', 'c6', 'd4', 'd5', 'e5', 'Bf5'],
    ideaPt: 'Pretas tiram o Bispo para f5 antes de fechar a porta com e6.',
    whiteWinPct: 38,
    drawPct: 34,
    blackWinPct: 28,
  },
  {
    eco: 'B01',
    namePt: 'Defesa Escandinava',
    movesSan: ['e4', 'd5', 'exd5', 'Qxd5', 'Nc3', 'Qa5'],
    ideaPt: 'Liquida o peão e4 no lance 1 criando estrutura sólida Caro-Eslava.',
    whiteWinPct: 41,
    drawPct: 31,
    blackWinPct: 28,
  },
  {
    eco: 'B07',
    namePt: 'Defesa Pirc',
    movesSan: ['e4', 'd6', 'd4', 'Nf6', 'Nc3', 'g6'],
    ideaPt: 'Hipermoderna: convida o centro branco para contra-golpear à distância.',
    whiteWinPct: 41,
    drawPct: 29,
    blackWinPct: 30,
  },
  {
    eco: 'B02',
    namePt: 'Defesa Alekhine',
    movesSan: ['e4', 'Nf6', 'e5', 'Nd5'],
    ideaPt: 'Provoca o avanço prematuro dos peões brancos para atacá-los depois.',
    whiteWinPct: 42,
    drawPct: 30,
    blackWinPct: 28,
  },
  {
    eco: 'A40',
    namePt: 'Abertura do Peão da Dama',
    movesSan: ['d4'],
    ideaPt: 'Domínio estratégico protegido pela Dama desde o lance 1.',
    whiteWinPct: 39,
    drawPct: 35,
    blackWinPct: 26,
  },
  {
    eco: 'D00',
    namePt: 'Jogo Fechado (Duplo Peão da Dama)',
    movesSan: ['d4', 'd5'],
    ideaPt: 'Equilíbrio sólido central com luta estratégica por c4 e e4.',
    whiteWinPct: 39,
    drawPct: 36,
    blackWinPct: 25,
  },
  {
    eco: 'D06',
    namePt: 'Gambito da Dama',
    movesSan: ['d4', 'd5', 'c4'],
    ideaPt: 'Oferece temporariamente o peão lateral c4 para dominar o centro com e4.',
    whiteWinPct: 41,
    drawPct: 36,
    blackWinPct: 23,
  },
  {
    eco: 'D30',
    namePt: 'Gambito da Dama Recusado',
    movesSan: ['d4', 'd5', 'c4', 'e6', 'Nc3', 'Nf6'],
    ideaPt: 'Pilar clássico dos Campeões Mundiais: defende d5 mantendo solidez central.',
    whiteWinPct: 39,
    drawPct: 39,
    blackWinPct: 22,
  },
  {
    eco: 'D20',
    namePt: 'Gambito da Dama Aceito',
    movesSan: ['d4', 'd5', 'c4', 'dxc4'],
    ideaPt: 'Cede temporariamente o centro para desenvolver rápido e golpear com c5.',
    whiteWinPct: 40,
    drawPct: 36,
    blackWinPct: 24,
  },
  {
    eco: 'D10',
    namePt: 'Defesa Eslava',
    movesSan: ['d4', 'd5', 'c4', 'c6'],
    ideaPt: 'Sustenta d5 com peão mantendo aberta a diagonal do Bispo de c8.',
    whiteWinPct: 38,
    drawPct: 38,
    blackWinPct: 24,
  },
  {
    eco: 'D43',
    namePt: 'Defesa Semi-Eslava',
    movesSan: ['d4', 'd5', 'c4', 'c6', 'Nf3', 'Nf6', 'Nc3', 'e6'],
    ideaPt: 'Triângulo sólido de peões pronto para explodir em dxc4 e b5 (Meran/Botvinnik).',
    whiteWinPct: 37,
    drawPct: 39,
    blackWinPct: 24,
  },
  {
    eco: 'D02',
    namePt: 'Sistema London',
    movesSan: ['d4', 'd5', 'Bf4', 'Nf6', 'e3'],
    ideaPt: 'Sistema universal piramidal: fácil de aprender, super sólido e perigoso na ala do Rei.',
    whiteWinPct: 40,
    drawPct: 34,
    blackWinPct: 26,
  },
  {
    eco: 'A45',
    namePt: 'Defesa Índia',
    movesSan: ['d4', 'Nf6'],
    ideaPt: 'Impede 2.e4 imediato mantendo máxima flexibilidade estrutural.',
    whiteWinPct: 38,
    drawPct: 35,
    blackWinPct: 27,
  },
  {
    eco: 'E60',
    namePt: 'Defesa Índia do Rei',
    movesSan: ['d4', 'Nf6', 'c4', 'g6', 'Nc3', 'Bg7', 'e4', 'd6'],
    ideaPt: 'Favorita de Kasparov e Fischer: permite centro branco para lançar tempestade na ala do Rei.',
    whiteWinPct: 40,
    drawPct: 29,
    blackWinPct: 31,
  },
  {
    eco: 'D80',
    namePt: 'Defesa Grünfeld',
    movesSan: ['d4', 'Nf6', 'c4', 'g6', 'Nc3', 'd5'],
    ideaPt: 'Golpeia o centro branco imediatamente combinando pressão de peças e peão c5.',
    whiteWinPct: 37,
    drawPct: 37,
    blackWinPct: 26,
  },
  {
    eco: 'E20',
    namePt: 'Defesa Nimzo-Índia',
    movesSan: ['d4', 'Nf6', 'c4', 'e6', 'Nc3', 'Bb4'],
    ideaPt: 'Obra-prima de Nimzowitsch: crava c3 para controlar e4 sem ocupar com peões.',
    whiteWinPct: 37,
    drawPct: 40,
    blackWinPct: 23,
  },
  {
    eco: 'E12',
    namePt: 'Defesa Índia da Dama',
    movesSan: ['d4', 'Nf6', 'c4', 'e6', 'Nf3', 'b6'],
    ideaPt: 'Controle hipermoderno das casas centrais claras e4 e d5 via Bb7.',
    whiteWinPct: 37,
    drawPct: 42,
    blackWinPct: 21,
  },
  {
    eco: 'E00',
    namePt: 'Abertura Catalã',
    movesSan: ['d4', 'Nf6', 'c4', 'e6', 'g3', 'd5', 'Bg2'],
    ideaPt: 'Combina o Gambito da Dama com pressão posicional eterna do Bispo em g2.',
    whiteWinPct: 41,
    drawPct: 39,
    blackWinPct: 20,
  },
  {
    eco: 'A80',
    namePt: 'Defesa Holandesa',
    movesSan: ['d4', 'f5'],
    ideaPt: 'Luta assimétrica pela casa e4 desde o primeiro lance.',
    whiteWinPct: 42,
    drawPct: 29,
    blackWinPct: 29,
  },
  {
    eco: 'A10',
    namePt: 'Abertura Inglesa',
    movesSan: ['c4'],
    ideaPt: 'Controla d5 pelos flancos com alta riqueza transpositiva.',
    whiteWinPct: 39,
    drawPct: 36,
    blackWinPct: 25,
  },
  {
    eco: 'A04',
    namePt: 'Abertura Réti / Ataque Índio do Rei',
    movesSan: ['Nf3', 'd5', 'g3'],
    ideaPt: 'Desenvolve os flancos antes de definir a estrutura central de peões.',
    whiteWinPct: 39,
    drawPct: 37,
    blackWinPct: 24,
  },
];

export function detectOpeningFromMoves(sanHistory: string[]): DetectedOpening {
  if (sanHistory.length === 0) {
    const rootNext = OPENING_BOOK_LINES.filter((l) => l.movesSan.length === 1).map((l) => ({
      san: l.movesSan[0],
      openingNamePt: l.namePt,
      eco: l.eco,
      whiteWinPct: l.whiteWinPct,
      drawPct: l.drawPct,
      blackWinPct: l.blackWinPct,
    }));
    return {
      eco: 'A00',
      namePt: 'Posição Inicial FIDE',
      ideaPt: 'Domine o centro (e4/d4/c4/Cf3), desenvolva Cavalos e Bispos e faça o roque cedo.',
      matchedPlyCount: 0,
      isExactBookPosition: true,
      nextBookCandidates: rootNext,
    };
  }

  let bestMatch: OpeningLineSpec | null = null;
  for (const line of OPENING_BOOK_LINES) {
    if (line.movesSan.length > sanHistory.length) continue;
    let matches = true;
    for (let i = 0; i < line.movesSan.length; i++) {
      if (line.movesSan[i] !== sanHistory[i]) {
        matches = false;
        break;
      }
    }
    if (matches && (!bestMatch || line.movesSan.length > bestMatch.movesSan.length)) {
      bestMatch = line;
    }
  }

  // Candidatos de livro a partir da sequencia exata atual
  const seenSan = new Set<string>();
  const nextBookCandidates: DetectedOpening['nextBookCandidates'] = [];
  for (const line of OPENING_BOOK_LINES) {
    if (line.movesSan.length <= sanHistory.length) continue;
    let prefixOk = true;
    for (let i = 0; i < sanHistory.length; i++) {
      if (line.movesSan[i] !== sanHistory[i]) {
        prefixOk = false;
        break;
      }
    }
    if (prefixOk) {
      const nextSan = line.movesSan[sanHistory.length];
      if (!seenSan.has(nextSan)) {
        seenSan.add(nextSan);
        nextBookCandidates.push({
          san: nextSan,
          openingNamePt: line.namePt,
          eco: line.eco,
          whiteWinPct: line.whiteWinPct,
          drawPct: line.drawPct,
          blackWinPct: line.blackWinPct,
        });
      }
    }
  }

  if (!bestMatch) {
    return {
      eco: 'A00',
      namePt: 'Abertura Irregular / Fora do Livro',
      ideaPt: 'Siga os primeiros princípios: desenvolva peças menores, proteja o Rei e controle o centro.',
      matchedPlyCount: 0,
      isExactBookPosition: false,
      nextBookCandidates,
    };
  }

  const isExactBookPosition =
    bestMatch.movesSan.length === sanHistory.length || nextBookCandidates.length > 0;

  return {
    eco: bestMatch.eco,
    namePt: bestMatch.namePt,
    ideaPt: bestMatch.ideaPt,
    matchedPlyCount: bestMatch.movesSan.length,
    isExactBookPosition,
    nextBookCandidates,
  };
}

export function pickBookMoveForBot(
  chess: Chess,
  botElo: number,
  seed: number,
): string | null {
  // Bots muito iniciantes saem cedo do livro para parecerem naturais
  const maxBookPly = botElo < 600 ? 2 : botElo < 1100 ? 4 : botElo < 1600 ? 7 : 12;
  const hist = chess.history();
  if (hist.length >= maxBookPly) return null;

  const detected = detectOpeningFromMoves(hist);
  if (detected.nextBookCandidates.length === 0) return null;

  const legalMoves = new Set(chess.moves());
  const validBookSans = detected.nextBookCandidates
    .map((c) => c.san)
    .filter((san) => legalMoves.has(san));

  if (validBookSans.length === 0) return null;
  const idx = Math.abs(seed + hist.length * 37) % validBookSans.length;
  return validBookSans[idx];
}
