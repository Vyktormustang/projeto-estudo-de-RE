/**
 * dia-noite.ts — ciclo de dia e noite do FORJA v40 (puro, determinístico, testável).
 *
 * Regras de projeto:
 *  - **Sem `Date` aqui dentro.** A hora do dia é um instante que o chamador
 *    passa; só `minutosDaData()` toca relógio real. Assim o módulo é testável e
 *    o app decide de onde vem o tempo (relógio do aparelho ou minutos de estudo).
 *  - **Sem tela.** Só números: fase, luminosidade, paleta. Quem pinta é o CSS.
 *  - **Relógio canônico:** minutos desde a meia-noite, 0..1439.
 *
 * Fronteiras do dia:
 *
 *   00:00–04:00  madrugada    (a mais escura)
 *   04:00–06:00  amanhecer    (clareia)
 *   06:00–17:00  dia          (luz cheia)
 *   17:00–19:00  entardecer   (escurece, dourado)
 *   19:00–23:00  noite        (azul profundo)
 *   23:00–24:00  madrugada
 */

/** Minutos desde a meia-noite. */
export type MinutosDoDia = number;

export type Fase = 'madrugada' | 'amanhecer' | 'dia' | 'entardecer' | 'noite';

/** Fronteiras em minutos desde a meia-noite. */
export const FRONTEIRAS = {
  amanhecer: 4 * 60, // 04:00
  dia: 6 * 60, // 06:00
  entardecer: 17 * 60, // 17:00
  noite: 19 * 60, // 19:00
  madrugada: 23 * 60, // 23:00
  fimDoDia: 24 * 60, // 24:00
} as const;

/** Normaliza qualquer número (ou lixo) para um minuto válido de 0..1439. */
export function normalizarMinutos(minutos: unknown): MinutosDoDia {
  const n = typeof minutos === 'number' && Number.isFinite(minutos) ? minutos : 0;
  const m = Math.round(n) % 1440;
  // `-1440 % 1440` dá `-0` em JS; o `+ 0` normaliza para 0 (Object.is distingue).
  const w = m < 0 ? m + 1440 : m;
  return w + 0;
}

/** Minutos desde a meia-noite a partir de hora e minuto de relógio. */
export function minutosDe(hora: number, minuto = 0): MinutosDoDia {
  const h = Number.isFinite(hora) ? Math.trunc(hora) : 0;
  const mi = Number.isFinite(minuto) ? Math.trunc(minuto) : 0;
  return normalizarMinutos(h * 60 + mi);
}

/** Fase do dia para um instante. A fronteira pertence à fase que começa nela. */
export function faseDe(minutos: MinutosDoDia): Fase {
  const m = normalizarMinutos(minutos);
  if (m < FRONTEIRAS.amanhecer) return 'madrugada';
  if (m < FRONTEIRAS.dia) return 'amanhecer';
  if (m < FRONTEIRAS.entardecer) return 'dia';
  if (m < FRONTEIRAS.noite) return 'entardecer';
  if (m < FRONTEIRAS.madrugada) return 'noite';
  return 'madrugada';
}

/** Minuto em que a fase começa (madrugada começa 23:00). */
export function inicioDaFase(fase: Fase): MinutosDoDia {
  switch (fase) {
    case 'madrugada':
      return FRONTEIRAS.madrugada;
    case 'amanhecer':
      return FRONTEIRAS.amanhecer;
    case 'dia':
      return FRONTEIRAS.dia;
    case 'entardecer':
      return FRONTEIRAS.entardecer;
    case 'noite':
      return FRONTEIRAS.noite;
  }
}

/** Minuto em que a fase termina (início da próxima). */
export function fimDaFase(fase: Fase): MinutosDoDia {
  switch (fase) {
    case 'madrugada':
      return FRONTEIRAS.amanhecer;
    case 'amanhecer':
      return FRONTEIRAS.dia;
    case 'dia':
      return FRONTEIRAS.entardecer;
    case 'entardecer':
      return FRONTEIRAS.noite;
    case 'noite':
      return FRONTEIRAS.madrugada;
  }
}

/**
 * Luminosidade de referência por fase (0 = breu, 1 = meio-dia).
 * São os patamares da curva; as transições são interpoladas.
 */
const LUMINOSIDADE: Record<Fase, number> = {
  madrugada: 0.18,
  amanhecer: 0.62,
  dia: 1,
  entardecer: 0.58,
  noite: 0.22,
};

/**
 * Keyframes da curva (minuto, luminosidade), em ordem crescente e circular.
 * O dia "fecha" em 24:00 com o mesmo valor de 00:00 — sem degrau na virada.
 */
const KEYFRAMES: ReadonlyArray<readonly [MinutosDoDia, number]> = [
  [0, 0.18],
  [4 * 60, 0.18], //  04:00 ainda escuro
  [6 * 60, 1], //  06:00 luz cheia
  [17 * 60, 1], //  17:00 começa a cair
  [19 * 60, 0.22], // 19:00 noite
  [23 * 60, 0.18], // 23:00 madrugada
  [24 * 60, 0.18],
];

function smoothstep(x: number): number {
  const t = Math.max(0, Math.min(1, x));
  return t * t * (3 - 2 * t);
}

/**
 * Luminosidade contínua em 0..1 — interpolação suave entre os keyframes.
 *
 * Não existe salto ao cruzar 06:00 ou 19:00: a curva atravessa os valores com
 * smoothstep, então a UI pode animar a paleta sem "piscar".
 */
export function luminosidade(minutos: MinutosDoDia): number {
  const m = normalizarMinutos(minutos);
  for (let i = 0; i < KEYFRAMES.length - 1; i++) {
    const [m0, l0] = KEYFRAMES[i];
    const [m1, l1] = KEYFRAMES[i + 1];
    if (m >= m0 && m <= m1) {
      if (m1 === m0) return l1;
      return l0 + (l1 - l0) * smoothstep((m - m0) / (m1 - m0));
    }
  }
  // Inalcançável com keyframes cobrindo 0..1440; mantido por segurança.
  return LUMINOSIDADE[faseDe(m)];
}

/** Paleta de cada fase — o CSS consome estas variáveis. */
export interface Paleta {
  /** Cor de fundo principal (CSS color). */
  fundo: string;
  /** Cor do texto principal. */
  texto: string;
  /** Cor de destaque (brasa/forja). */
  destaque: string;
  /** Cor de superfície (cartões). */
  superficie: string;
}

export const PALETAS: Record<Fase, Paleta> = {
  madrugada: {
    fundo: '#07070c',
    texto: '#c9c9d6',
    destaque: '#7a4a2a',
    superficie: '#0e0e16',
  },
  amanhecer: {
    fundo: '#2a1e26',
    texto: '#eadfd6',
    destaque: '#e08a4a',
    superficie: '#3a2a30',
  },
  dia: {
    fundo: '#14161c',
    texto: '#f2efe9',
    destaque: '#ff8c3a',
    superficie: '#1e2129',
  },
  entardecer: {
    fundo: '#1f1620',
    texto: '#f0ddd0',
    destaque: '#ff6b2c',
    superficie: '#2b2029',
  },
  noite: {
    fundo: '#0a0d1a',
    texto: '#cfd6e8',
    destaque: '#c8642a',
    superficie: '#121728',
  },
};

/** Paleta da fase num instante. */
export function paletaDe(minutos: MinutosDoDia): Paleta {
  return PALETAS[faseDe(minutos)];
}

/** Rótulo em pt-BR para a UI. */
export function rotuloFase(fase: Fase): string {
  switch (fase) {
    case 'madrugada':
      return 'Madrugada';
    case 'amanhecer':
      return 'Amanhecer';
    case 'dia':
      return 'Dia';
    case 'entardecer':
      return 'Entardecer';
    case 'noite':
      return 'Noite';
  }
}

/** Avança o relógio em `deltaMinutos` (aceita negativo: volta no tempo). */
export function avancar(minutos: MinutosDoDia, deltaMinutos: number): MinutosDoDia {
  const d = Number.isFinite(deltaMinutos) ? deltaMinutos : 0;
  return normalizarMinutos(normalizarMinutos(minutos) + d);
}

/**
 * Minutos de relógio a partir de uma data — **única** porta de entrada de
 * tempo real. Separada de propósito: o resto do módulo é puro e testável.
 */
export function minutosDaData(d: Date): MinutosDoDia {
  return normalizarMinutos(d.getHours() * 60 + d.getMinutes());
}

/** `HH:MM` a partir de minutos do dia (para exibir na UI). */
export function horaFormatada(minutos: MinutosDoDia): string {
  const m = normalizarMinutos(minutos);
  const h = Math.floor(m / 60);
  const mi = m % 60;
  return `${String(h).padStart(2, '0')}:${String(mi).padStart(2, '0')}`;
}

/** Minutos até a próxima mudança de fase (> 0), para a UI dizer "o dia nasce em X". */
export function minutosAteProximaFase(minutos: MinutosDoDia): number {
  const m = normalizarMinutos(minutos);
  const fronteiras = [
    FRONTEIRAS.amanhecer,
    FRONTEIRAS.dia,
    FRONTEIRAS.entardecer,
    FRONTEIRAS.noite,
    FRONTEIRAS.madrugada,
  ];
  const distancias = fronteiras
    .map((f) => (f - m + 1440) % 1440)
    .filter((d) => d > 0);
  return distancias.length ? Math.min(...distancias) : 0;
}

/**
 * Segundos de "hora do jogo" por segundo real, para o app poder acelerar o
 * ciclo de forma controlada (1 = tempo real). Valor usado na UI do v40.
 */
export const VELOCIDADE_PADRAO = 1;

/** Minutos de jogo decorridos a partir de milissegundos reais. */
export function minutosDecorridos(msReais: number, velocidade = VELOCIDADE_PADRAO): number {
  const ms = Number.isFinite(msReais) ? Math.max(0, msReais) : 0;
  const v = Number.isFinite(velocidade) && velocidade > 0 ? velocidade : 1;
  return (ms / 1000) * (v / 60); // 60 s reais = 1 min de jogo com v = 1
}
