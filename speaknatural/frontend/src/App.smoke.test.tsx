/**
 * Teste de fumaça: renderiza o App inteiro no servidor (sem navegador)
 * para garantir que nenhuma tela quebra ao abrir (import errado, variável
 * indefinida, JSX inválido...).
 *
 * Não testa interação: isso é feito manualmente no celular/PC.
 */

import { renderToString } from 'react-dom/server';
import { beforeAll, describe, expect, it } from 'vitest';
import App from './App';

beforeAll(() => {
  const store = new Map<string, string>();
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => void store.set(key, value),
      removeItem: (key: string) => void store.delete(key),
      clear: () => store.clear(),
      key: (index: number) => Array.from(store.keys())[index] ?? null,
      get length() {
        return store.size;
      },
    },
  });
});

describe('App', () => {
  it('renderiza a aba Praticar sem erro', () => {
    const html = renderToString(<App />);
    expect(html).toContain('SpeakNatural');
    expect(html).toContain('Praticar');
    expect(html).toContain('Histórico');
    expect(html).toContain('Servidor');
  });

  it('mostra o estado de carregamento das frases', () => {
    const html = renderToString(<App />);
    expect(html).toContain('Carregando as frases');
  });
});
