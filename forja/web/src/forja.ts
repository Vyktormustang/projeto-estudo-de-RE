/**
 * forja.ts — núcleo determinístico do FORJA (sem DOM, 100% testável).
 *
 * Tudo aqui é função pura: entra estado, sai estado. É o que o vitest cobre
 * em `forja.test.ts` e o que o harness de regressão usa para provar que um
 * "fix" não quebrou o que já funcionava.
 */

/** Versão exibida na UI. Sobrescrita em build pelo vite (define). */
export const VERSAO_FALLBACK = '39.0.0';

export type Resultado = 'vitoria' | 'empate' | 'derrota';

/** Pontos do resultado na fórmula Elo (FIDE). */
export const PONTOS: Record<Resultado, number> = {
  vitoria: 1,
  empate: 0.5,
  derrota: 0,
};

/**
 * Fator K (plano científico v23, §3.2):
 *   K = 40 para < 1500 (aprendiz), 20 para intermediário, 10 para > 2000.
 */
export function fatorK(elo: number): number {
  if (elo < 1500) return 40;
  if (elo <= 2000) return 20;
  return 10;
}

/** Probabilidade esperada de vitória do jogador (0..1). */
export function eloEsperado(eloJogador: number, eloAdversario: number): number {
  return 1 / (1 + Math.pow(10, (eloAdversario - eloJogador) / 400));
}

/**
 * ELO após uma partida. `R_new = R_old + K × (S − E)`.
 * Arredonda para inteiro e nunca desce abaixo de 100 (piso de sanidade).
 */
export function novoElo(
  eloJogador: number,
  eloAdversario: number,
  resultado: Resultado,
): { elo: number; delta: number; esperado: number } {
  if (!Number.isFinite(eloJogador) || !Number.isFinite(eloAdversario)) {
    throw new Error('ELO inválido: precisa ser número finito');
  }
  const esperado = eloEsperado(eloJogador, eloAdversario);
  const bruto = eloJogador + fatorK(eloJogador) * (PONTOS[resultado] - esperado);
  const elo = Math.max(100, Math.round(bruto));
  return { elo, delta: elo - eloJogador, esperado };
}

/** Faixas de categoria (plano v23, §3.2). */
export function categoriaElo(elo: number): string {
  if (elo < 800) return 'Iniciante';
  if (elo < 1200) return 'Clube';
  if (elo < 1600) return 'Intermediário';
  if (elo < 2000) return 'Avançado';
  if (elo < 2300) return 'Especialista';
  if (elo < 2500) return 'Mestre';
  return 'Grão-Mestre';
}

/** Precisão de uma partida a partir de erros (0..100). Determinística. */
export function precisao(
  lances: number,
  imprecisoes: number,
  erros: number,
  falhas: number,
): number {
  if (lances <= 0) return 100;
  const perda = imprecisoes * 0.5 + erros * 1 + falhas * 2;
  const bruto = 100 - (perda / lances) * 100;
  return Math.max(0, Math.min(100, Math.round(bruto * 10) / 10));
}

/**
 * Repetição espaçada (Cepeda et al. 2006): ISI ótimo = 10–20% do atraso
 * de retenção desejado. Devolve o intervalo em dias (mínimo 1).
 */
export function intervaloRevisao(diasDeRetencao: number): number {
  const alvo = Math.round(diasDeRetencao * 0.15);
  return Math.max(1, alvo);
}

/**
 * SM-2 simplificado para as lições do Panteão.
 * `qualidade` 0..5. Retorna o novo intervalo (dias) e o fator de facilidade.
 */
export function sm2(
  qualidade: number,
  repeticoes: number,
  facilidade: number,
  intervaloDias: number,
): { repeticoes: number; facilidade: number; intervalo: number } {
  const q = Math.max(0, Math.min(5, Math.round(qualidade)));
  const ef = Math.max(
    1.3,
    facilidade + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)),
  );
  if (q < 3) {
    return { repeticoes: 0, facilidade: ef, intervalo: 1 };
  }
  const reps = repeticoes + 1;
  const intervalo =
    reps === 1 ? 1 : reps === 2 ? 6 : Math.max(1, Math.round(intervaloDias * ef));
  return { repeticoes: reps, facilidade: Number(ef.toFixed(2)), intervalo };
}

/** Chave estável de persistência (o Cofre guarda JSON no localStorage). */
export const CHAVE_COFRE = 'forja:vault:v1';

export interface Cofre {
  versao: number;
  eloXadrez: number;
  melhorElo: number;
  vitorias: number;
  empates: number;
  derrotas: number;
  licoesConcluidas: string[];
  conquistas: string[];
}

export function cofreVazio(): Cofre {
  return {
    versao: 1,
    eloXadrez: 1200,
    melhorElo: 1200,
    vitorias: 0,
    empates: 0,
    derrotas: 0,
    licoesConcluidas: [],
    conquistas: [],
  };
}

/** Migra/valida um Cofre vindo do disco (nunca confia no JSON do disco). */
export function sanearCofre(bruto: unknown): Cofre {
  const base = cofreVazio();
  if (typeof bruto !== 'object' || bruto === null) return base;
  const o = bruto as Partial<Cofre>;
  const num = (v: unknown, padrao: number): number =>
    typeof v === 'number' && Number.isFinite(v) ? v : padrao;
  const lista = (v: unknown): string[] =>
    Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string') : [];
  return {
    versao: 1,
    eloXadrez: num(o.eloXadrez, base.eloXadrez),
    melhorElo: num(o.melhorElo, base.melhorElo),
    vitorias: num(o.vitorias, 0),
    empates: num(o.empates, 0),
    derrotas: num(o.derrotas, 0),
    licoesConcluidas: lista(o.licoesConcluidas),
    conquistas: lista(o.conquistas),
  };
}

/** Registra o resultado de uma partida no Cofre (imutável). */
export function registrarPartida(
  cofre: Cofre,
  eloAdversario: number,
  resultado: Resultado,
): Cofre {
  const { elo } = novoElo(cofre.eloXadrez, eloAdversario, resultado);
  return {
    ...cofre,
    eloXadrez: elo,
    melhorElo: Math.max(cofre.melhorElo, elo),
    vitorias: cofre.vitorias + (resultado === 'vitoria' ? 1 : 0),
    empates: cofre.empates + (resultado === 'empate' ? 1 : 0),
    derrotas: cofre.derrotas + (resultado === 'derrota' ? 1 : 0),
  };
}
