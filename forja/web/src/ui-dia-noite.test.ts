/**
 * ui-dia-noite.test.ts — a UI realmente pinta o ciclo de dia e noite?
 *
 * O módulo `dia-noite.ts` pode estar perfeito e a tela continuar preta: estes
 * testes rodam `main.ts` num DOM real (jsdom), exercitam os controles e leem as
 * propriedades CSS que chegam ao cartão do céu. É o meio-termo honesto entre
 * "testei a função" e "vi no aparelho".
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

type CeuApi = {
  minutos: () => number;
  definir: (m: number) => void;
  fase: () => string;
};

/** Instala o documento mínimo que `main.ts` espera e importa o módulo. */
async function montarApp(): Promise<{ doc: Document; ceu: CeuApi }> {
  document.body.innerHTML = '<div id="app"></div>';
  vi.resetModules();
  await import('./main');
  const ceu = (globalThis as unknown as { __forja_ceu?: CeuApi }).__forja_ceu;
  if (!ceu) throw new Error('main.ts não expôs __forja_ceu');
  return { doc: document, ceu };
}

function corDoCartao(doc: Document): string {
  const el = doc.querySelector<HTMLElement>('#ceu');
  return el?.style.getPropertyValue('--ceu-fundo') ?? '';
}

describe('UI do ciclo de dia e noite (jsdom)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    localStorage.clear();
  });

  it('monta o cartão do céu com hora, fase e luminosidade', async () => {
    const { doc } = await montarApp();
    expect(doc.querySelector('#ceu')).toBeTruthy();
    expect(doc.querySelector('#ceu-hora')?.textContent).toMatch(/^\d{2}:\d{2}$/);
    expect(doc.querySelector('#ceu-fase')?.textContent).not.toBe('—');
    expect(doc.querySelector('#ceu-lum')?.textContent).toMatch(/^\d+%$/);
    expect(doc.querySelector('#ceu-proxima')?.textContent).toMatch(/min|h/);
  });

  it('pinta paleta diferente para dia e para noite', async () => {
    const { doc, ceu } = await montarApp();

    ceu.definir(12 * 60); // meio-dia
    const dia = corDoCartao(doc);
    expect(doc.querySelector('#ceu-fase')?.textContent).toBe('Dia');

    ceu.definir(21 * 60); // noite
    const noite = corDoCartao(doc);
    expect(doc.querySelector('#ceu-fase')?.textContent).toBe('Noite');

    expect(dia).toBeTruthy();
    expect(noite).toBeTruthy();
    expect(dia).not.toBe(noite);
  });

  it('percorre as cinco fases pelo relógio', async () => {
    const { doc, ceu } = await montarApp();
    const vistos: string[] = [];
    for (const [minuto, esperado] of [
      [120, 'Madrugada'],
      [300, 'Amanhecer'],
      [720, 'Dia'],
      [1080, 'Entardecer'],
      [1260, 'Noite'],
    ] as const) {
      ceu.definir(minuto);
      const rotulo = doc.querySelector('#ceu-fase')?.textContent ?? '';
      expect(rotulo).toBe(esperado);
      vistos.push(corDoCartao(doc));
    }
    // pelo menos três paletas distintas entre as cinco fases
    expect(new Set(vistos).size).toBeGreaterThanOrEqual(3);
  });

  it('os botões +1h / −1h / Agora mexem no relógio', async () => {
    const { doc, ceu } = await montarApp();
    ceu.definir(600); // 10:00
    expect(doc.querySelector('#ceu-hora')?.textContent).toBe('10:00');

    doc.querySelector<HTMLButtonElement>('#ceu-mais')?.click();
    expect(doc.querySelector('#ceu-hora')?.textContent).toBe('11:00');

    doc.querySelector<HTMLButtonElement>('#ceu-menos')?.click();
    doc.querySelector<HTMLButtonElement>('#ceu-menos')?.click();
    expect(doc.querySelector('#ceu-hora')?.textContent).toBe('09:00');

    doc.querySelector<HTMLButtonElement>('#ceu-agora')?.click();
    expect(doc.querySelector('#ceu-hora')?.textContent).toMatch(/^\d{2}:\d{2}$/);
  });

  it('o marcador anda ao longo do dia', async () => {
    const { doc, ceu } = await montarApp();
    ceu.definir(0);
    const inicio = doc.querySelector<HTMLElement>('#ceu-marcador')?.style.left;
    ceu.definir(12 * 60);
    const meio = doc.querySelector<HTMLElement>('#ceu-marcador')?.style.left;
    ceu.definir(18 * 60);
    const tarde = doc.querySelector<HTMLElement>('#ceu-marcador')?.style.left;

    expect(inicio).toBe('0%');
    expect(meio).toBe('50%');
    expect(tarde).toBe('75%');
  });

  it('o opacidade do sol acompanha a luminosidade', async () => {
    const { doc, ceu } = await montarApp();
    ceu.definir(12 * 60);
    const dia = Number(doc.querySelector<HTMLElement>('#ceu-sol')?.style.opacity);
    ceu.definir(2 * 60);
    const madrugada = Number(doc.querySelector<HTMLElement>('#ceu-sol')?.style.opacity);
    expect(dia).toBeGreaterThan(madrugada);
  });
});
