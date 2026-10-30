import { describe, expect, it } from 'vitest';
import {
  categoriaElo,
  cofreVazio,
  eloEsperado,
  fatorK,
  intervaloRevisao,
  novoElo,
  precisao,
  registrarPartida,
  sanearCofre,
  sm2,
} from './forja';

describe('Elo', () => {
  it('K vale 40 abaixo de 1500, 20 até 2000 e 10 acima', () => {
    expect(fatorK(1200)).toBe(40);
    expect(fatorK(1500)).toBe(20);
    expect(fatorK(2000)).toBe(20);
    expect(fatorK(2001)).toBe(10);
  });

  it('esperado é 0.5 contra ELO igual e cresce com a diferença', () => {
    expect(eloEsperado(1500, 1500)).toBeCloseTo(0.5, 6);
    expect(eloEsperado(1700, 1500)).toBeGreaterThan(0.5);
    expect(eloEsperado(1300, 1500)).toBeLessThan(0.5);
  });

  it('vitória soma exatamente K×(1−E), arredondado', () => {
    const r = novoElo(1500, 1500, 'vitoria');
    expect(r.esperado).toBeCloseTo(0.5, 6);
    expect(r.elo).toBe(1510); // K=20, +10
    expect(r.delta).toBe(10);
  });

  it('derrota contra igual tira o mesmo tanto', () => {
    expect(novoElo(1500, 1500, 'derrota').elo).toBe(1490);
  });

  it('empate contra igual não muda o ELO', () => {
    expect(novoElo(1500, 1500, 'empate').elo).toBe(1500);
  });

  it('vencer favorito rende pouco; perder para azarão custa muito', () => {
    const venceFavorito = novoElo(2000, 1500, 'vitoria').delta;
    const perdeAzarao = novoElo(2000, 1500, 'derrota').delta;
    expect(venceFavorito).toBeGreaterThan(0);
    expect(venceFavorito).toBeLessThan(5);
    expect(perdeAzarao).toBeLessThan(-10);
  });

  it('nunca cai abaixo do piso de 100', () => {
    expect(novoElo(100, 2800, 'derrota').elo).toBe(100);
  });

  it('rejeita ELO não numérico', () => {
    expect(() => novoElo(Number.NaN, 1500, 'vitoria')).toThrow(/ELO inválido/);
  });
});

describe('Categorias', () => {
  it('respeita as fronteiras do plano v23', () => {
    expect(categoriaElo(799)).toBe('Iniciante');
    expect(categoriaElo(800)).toBe('Clube');
    expect(categoriaElo(1200)).toBe('Intermediário');
    expect(categoriaElo(1600)).toBe('Avançado');
    expect(categoriaElo(2000)).toBe('Especialista');
    expect(categoriaElo(2300)).toBe('Mestre');
    expect(categoriaElo(2500)).toBe('Grão-Mestre');
  });
});

describe('Precisão', () => {
  it('partida sem erro é 100%', () => {
    expect(precisao(40, 0, 0, 0)).toBe(100);
  });

  it('cada falha pesa 2, erro 1 e imprecisão 0.5', () => {
    expect(precisao(10, 0, 0, 1)).toBe(80);
    expect(precisao(10, 0, 1, 0)).toBe(90);
    expect(precisao(10, 1, 0, 0)).toBe(95);
  });

  it('nunca fica negativa', () => {
    expect(precisao(2, 10, 10, 10)).toBe(0);
  });

  it('sem lances devolve 100 (estado inicial)', () => {
    expect(precisao(0, 0, 0, 0)).toBe(100);
  });
});

describe('Repetição espaçada', () => {
  it('ISI fica em ~15% do atraso de retenção', () => {
    expect(intervaloRevisao(100)).toBe(15);
    expect(intervaloRevisao(7)).toBe(1);
  });

  it('SM-2: acerto aumenta facilidade e intervalo', () => {
    const r1 = sm2(5, 0, 2.5, 0);
    expect(r1.repeticoes).toBe(1);
    expect(r1.intervalo).toBe(1);
    const r2 = sm2(5, r1.repeticoes, r1.facilidade, r1.intervalo);
    expect(r2.intervalo).toBe(6);
    const r3 = sm2(5, r2.repeticoes, r2.facilidade, r2.intervalo);
    expect(r3.intervalo).toBeGreaterThanOrEqual(6);
  });

  it('SM-2: erro reinicia a repetição e piso de facilidade é 1.3', () => {
    const r = sm2(0, 5, 1.3, 30);
    expect(r.repeticoes).toBe(0);
    expect(r.intervalo).toBe(1);
    expect(r.facilidade).toBeGreaterThanOrEqual(1.3);
  });
});

describe('Cofre', () => {
  it('sanear ignora lixo do disco e devolve estrutura válida', () => {
    const c = sanearCofre({ eloXadrez: 'x', vitorias: 3, conquistas: [1, 'a'] });
    expect(c.eloXadrez).toBe(1200);
    expect(c.vitorias).toBe(3);
    expect(c.conquistas).toEqual(['a']);
  });

  it('sanear de null/undefined devolve cofre vazio', () => {
    expect(sanearCofre(null)).toEqual(cofreVazio());
    expect(sanearCofre(undefined)).toEqual(cofreVazio());
  });

  it('registrarPartida atualiza ELO, melhor ELO e placar', () => {
    const c = registrarPartida(cofreVazio(), 1200, 'vitoria');
    expect(c.vitorias).toBe(1);
    expect(c.eloXadrez).toBeGreaterThan(1200);
    expect(c.melhorElo).toBe(c.eloXadrez);
  });

  it('registrarPartida não muta o cofre original', () => {
    const antes = cofreVazio();
    registrarPartida(antes, 1200, 'derrota');
    expect(antes.derrotas).toBe(0);
  });
});
