import { describe, expect, it } from 'vitest';
import {
  colorForScore,
  colorLabel,
  formatSeconds,
  pluralAttempts,
  pluralDays,
  scoreMessage,
  toPercent,
  tokenizeSentence,
} from './format';

describe('notas', () => {
  it('converte 0..1 em porcentagem', () => {
    expect(toPercent(0.856)).toBe(86);
    expect(toPercent(1)).toBe(100);
    expect(toPercent(0)).toBe(0);
    expect(toPercent(Number.NaN)).toBe(0);
  });

  it('usa as faixas de cor do escopo', () => {
    expect(colorForScore(0.85)).toBe('green');
    expect(colorForScore(0.84)).toBe('yellow');
    expect(colorForScore(0.5)).toBe('yellow');
    expect(colorForScore(0.49)).toBe('red');
  });

  it('tem rótulos em português', () => {
    expect(colorLabel('green')).toBe('Bom');
    expect(colorLabel('yellow')).toBe('Quase');
    expect(colorLabel('red')).toBe('Ajustar');
  });

  it('dá uma mensagem diferente por faixa', () => {
    expect(scoreMessage(0.95)).toContain('Excelente');
    expect(scoreMessage(0.5)).toContain('evoluindo');
    expect(scoreMessage(0.1)).toContain('calma');
  });
});

describe('tokenizeSentence', () => {
  it('separa palavras e pontuação', () => {
    expect(tokenizeSentence("I'm fine, thanks!")).toEqual([
      { word: "I'm", trailing: '' },
      { word: 'fine', trailing: ',' },
      { word: 'thanks', trailing: '!' },
    ]);
  });

  it('mantém contrações com apóstrofo tipográfico', () => {
    expect(tokenizeSentence('She shouldn’t’ve said that.')).toEqual([
      { word: 'She', trailing: '' },
      { word: "shouldn't've", trailing: '' },
      { word: 'said', trailing: '' },
      { word: 'that', trailing: '.' },
    ]);
  });

  it('lida com frase vazia', () => {
    expect(tokenizeSentence('')).toEqual([]);
  });
});

describe('formatação', () => {
  it('formata segundos como m:ss', () => {
    expect(formatSeconds(0)).toBe('0:00');
    expect(formatSeconds(65_000)).toBe('1:05');
  });

  it('pluraliza em português', () => {
    expect(pluralAttempts(1)).toBe('1 tentativa');
    expect(pluralAttempts(3)).toBe('3 tentativas');
    expect(pluralDays(1)).toBe('1 dia seguido');
    expect(pluralDays(4)).toBe('4 dias seguidos');
  });
});
