/**
 * dia-noite.test.ts — ciclo de dia e noite do FORJA v40.
 *
 * Cada teste aqui trava um comportamento que a UI depende; quebrar um deles é
 * regressão visível (paleta errada, salto na virada do dia, hora mal formatada).
 */
import { describe, expect, it } from 'vitest';
import {
  avancar,
  faseDe,
  fimDaFase,
  FRONTEIRAS,
  horaFormatada,
  inicioDaFase,
  luminosidade,
  minutosAteProximaFase,
  minutosDaData,
  minutosDe,
  minutosDecorridos,
  normalizarMinutos,
  PALETAS,
  paletaDe,
  rotuloFase,
  type Fase,
} from './dia-noite';

describe('normalização do relógio', () => {
  it('aceita minutos válidos sem mudar', () => {
    expect(normalizarMinutos(0)).toBe(0);
    expect(normalizarMinutos(725)).toBe(725);
    expect(normalizarMinutos(1439)).toBe(1439);
  });

  it('dá a volta no dia (positivo e negativo)', () => {
    expect(normalizarMinutos(1440)).toBe(0);
    expect(normalizarMinutos(1500)).toBe(60);
    expect(normalizarMinutos(-1)).toBe(1439);
    expect(normalizarMinutos(-1440)).toBe(0);
  });

  it('não propaga lixo (NaN, Infinity, string, null)', () => {
    expect(normalizarMinutos(NaN)).toBe(0);
    expect(normalizarMinutos(Infinity)).toBe(0);
    expect(normalizarMinutos('12:00')).toBe(0);
    expect(normalizarMinutos(null)).toBe(0);
    expect(normalizarMinutos(undefined)).toBe(0);
  });

  it('converte hora/minuto de relógio', () => {
    expect(minutosDe(0, 0)).toBe(0);
    expect(minutosDe(6, 30)).toBe(390);
    expect(minutosDe(23, 59)).toBe(1439);
    expect(minutosDe(25)).toBe(60); // 01:00 do dia seguinte
    expect(minutosDe(-1)).toBe(1380); // 23:00
  });
});

describe('fases do dia', () => {
  const casos: Array<[number, Fase]> = [
    [0, 'madrugada'],
    [239, 'madrugada'],
    [240, 'amanhecer'], // 04:00
    [359, 'amanhecer'],
    [360, 'dia'], // 06:00
    [1019, 'dia'],
    [1020, 'entardecer'], // 17:00
    [1139, 'entardecer'],
    [1140, 'noite'], // 19:00
    [1379, 'noite'],
    [1380, 'madrugada'], // 23:00
    [1439, 'madrugada'],
  ];

  it.each(casos)('minuto %i é %s', (minuto, fase) => {
    expect(faseDe(minuto)).toBe(fase);
  });

  it('fronteira pertence à fase que começa nela', () => {
    expect(faseDe(FRONTEIRAS.dia)).toBe('dia');
    expect(faseDe(FRONTEIRAS.dia - 1)).toBe('amanhecer');
    expect(faseDe(FRONTEIRAS.noite)).toBe('noite');
    expect(faseDe(FRONTEIRAS.noite - 1)).toBe('entardecer');
  });

  it('início e fim de fase são coerentes com faseDe', () => {
    const fases: Fase[] = ['madrugada', 'amanhecer', 'dia', 'entardecer', 'noite'];
    for (const f of fases) {
      expect(faseDe(inicioDaFase(f))).toBe(f);
      // um minuto antes do fim ainda é a mesma fase
      expect(faseDe(fimDaFase(f) - 1)).toBe(f);
    }
  });

  it('cada fase tem rótulo em pt-BR não vazio', () => {
    const fases: Fase[] = ['madrugada', 'amanhecer', 'dia', 'entardecer', 'noite'];
    for (const f of fases) {
      expect(rotuloFase(f).length).toBeGreaterThan(2);
    }
  });
});

describe('luminosidade', () => {
  it('é máximo no meio do dia e mínimo na madrugada', () => {
    expect(luminosidade(12 * 60)).toBeCloseTo(1, 5);
    expect(luminosidade(2 * 60)).toBeCloseTo(0.18, 5);
    expect(luminosidade(21 * 60)).toBeCloseTo(0.2, 5); // 19:00=0.22 -> 23:00=0.18
  });

  it('fica sempre dentro de 0..1 em todo o dia', () => {
    for (let m = 0; m < 1440; m++) {
      const l = luminosidade(m);
      expect(l).toBeGreaterThanOrEqual(0);
      expect(l).toBeLessThanOrEqual(1);
    }
  });

  it('não salta na virada da meia-noite nem nas fronteiras', () => {
    // nenhuma diferença de um minuto para o outro passa de 5% da escala
    let anterior = luminosidade(0);
    for (let m = 1; m <= 1440; m++) {
      const atual = luminosidade(m % 1440);
      expect(Math.abs(atual - anterior)).toBeLessThan(0.05);
      anterior = atual;
    }
  });

  it('clareia no amanhecer e escurece no entardecer', () => {
    expect(luminosidade(5 * 60)).toBeGreaterThan(luminosidade(4 * 60));
    expect(luminosidade(6 * 60)).toBeGreaterThan(luminosidade(5 * 60));
    expect(luminosidade(18 * 60)).toBeLessThan(luminosidade(17 * 60));
    expect(luminosidade(19 * 60)).toBeLessThan(luminosidade(18 * 60));
  });
});

describe('paletas', () => {
  it('toda fase tem as quatro cores em hex válido', () => {
    const fases: Fase[] = ['madrugada', 'amanhecer', 'dia', 'entardecer', 'noite'];
    for (const f of fases) {
      const p = PALETAS[f];
      for (const cor of [p.fundo, p.texto, p.destaque, p.superficie]) {
        expect(cor).toMatch(/^#[0-9a-f]{6}$/i);
      }
    }
  });

  it('a noite é mais escura que o dia (comparação por luminância)', () => {
    const lum = (hex: string): number => {
      const n = parseInt(hex.slice(1), 16);
      const r = (n >> 16) & 0xff;
      const g = (n >> 8) & 0xff;
      const b = n & 0xff;
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    expect(lum(paletaDe(12 * 60).fundo)).toBeGreaterThan(lum(paletaDe(21 * 60).fundo));
  });

  it('paletaDe segue a fase do instante', () => {
    expect(paletaDe(12 * 60)).toEqual(PALETAS.dia);
    expect(paletaDe(21 * 60)).toEqual(PALETAS.noite);
  });
});

describe('avanço do relógio e utilitários', () => {
  it('avançar cruza a virada do dia', () => {
    expect(avancar(1380, 120)).toBe(60); // 23:00 + 2h = 01:00
    expect(avancar(10, -20)).toBe(1430);
  });

  it('avançar aceita delta inválido como zero', () => {
    expect(avancar(100, NaN)).toBe(100);
    expect(avancar(100, Infinity)).toBe(100);
  });

  it('minutosDaData lê o relógio real da data', () => {
    expect(minutosDaData(new Date(2026, 10, 7, 6, 30))).toBe(390);
    expect(minutosDaData(new Date(2026, 10, 7, 0, 0))).toBe(0);
  });

  it('horaFormatada devolve HH:MM com zero à esquerda', () => {
    expect(horaFormatada(0)).toBe('00:00');
    expect(horaFormatada(390)).toBe('06:30');
    expect(horaFormatada(1439)).toBe('23:59');
    expect(horaFormatada(60 + 5)).toBe('01:05');
  });

  it('minutosAteProximaFase aponta a fronteira seguinte', () => {
    expect(minutosAteProximaFase(0)).toBe(240); // 00:00 -> 04:00
    expect(minutosAteProximaFase(360)).toBe(660); // 06:00 -> 17:00
    expect(minutosAteProximaFase(1379)).toBe(1); // 22:59 -> 23:00
    expect(minutosAteProximaFase(1439)).toBe(241); // 23:59 -> 04:00
  });

  it('minutosDecorridos converte tempo real e respeita a velocidade', () => {
    expect(minutosDecorridos(60_000)).toBe(1); // 1 min real = 1 min de jogo
    expect(minutosDecorridos(60_000, 60)).toBe(60);
    expect(minutosDecorridos(-5)).toBe(0);
    expect(minutosDecorridos(NaN)).toBe(0);
    expect(minutosDecorridos(60_000, 0)).toBe(1); // velocidade inválida cai em 1
  });
});
