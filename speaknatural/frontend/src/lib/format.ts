/** Formatação e textos em português (funções puras, testadas em format.test.ts). */

import type { WordColor } from './types';

export function toPercent(score: number): number {
  const clamped = Math.max(0, Math.min(1, Number.isFinite(score) ? score : 0));
  return Math.round(clamped * 100);
}

export function colorForScore(score: number): WordColor {
  if (score >= 0.85) return 'green';
  if (score >= 0.5) return 'yellow';
  return 'red';
}

export function colorLabel(color: WordColor): string {
  switch (color) {
    case 'green':
      return 'Bom';
    case 'yellow':
      return 'Quase';
    default:
      return 'Ajustar';
  }
}

export function scoreMessage(score: number): string {
  const percent = toPercent(score);
  if (percent >= 90) return 'Excelente! Soou bem natural.';
  if (percent >= 80) return 'Muito bom! Faltou pouco para ficar perfeito.';
  if (percent >= 65) return 'Bom caminho. Repita as palavras em amarelo.';
  if (percent >= 45) return 'Está evoluindo. Vá devagar nas palavras em vermelho.';
  return 'Vamos com calma: ouça a referência e repita a frase devagar.';
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatSeconds(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

export function phonemeDisplay(symbol: string | null): string {
  if (!symbol) return '—';
  return symbol;
}

export function pluralAttempts(count: number): string {
  return count === 1 ? '1 tentativa' : `${count} tentativas`;
}

export function pluralDays(count: number): string {
  return count === 1 ? '1 dia seguido' : `${count} dias seguidos`;
}

export interface RawToken {
  word: string;
  trailing: string;
}

/**
 * Divide a frase em palavras + a pontuação que vem logo depois de cada uma.
 * "I'm fine, thanks!" -> [{word:"I'm",trailing:""},{word:"fine",trailing:","},{word:"thanks",trailing:"!"}]
 * A pontuação fica separada para podermos colorir só a palavra.
 */
export function tokenizeSentence(text: string): RawToken[] {
  const tokens: RawToken[] = [];
  const regex = /[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*/g;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(text)) !== null) {
    let trailing = '';
    for (let index = match.index + match[0].length; index < text.length; index += 1) {
      const char = text[index];
      if ('.,!?;:…'.includes(char)) {
        trailing += char;
      } else {
        break;
      }
    }
    tokens.push({ word: match[0].replace(/’/g, "'"), trailing });
  }
  return tokens;
}
