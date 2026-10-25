/**
 * Smoke test da interface, sem navegador: jsdom + um "motor falso" que responde
 * UCI usando o chess.js. Verifica se o app monta, joga, revisa e navega.
 *
 *   node tests/ui.smoke.mjs
 */

import fs from 'node:fs';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { Chess } from 'chess.js';

const html = fs.readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');
const dom = new JSDOM(html, { url: 'http://localhost:3000/', pretendToBeVisual: true });

// ---------------------------------------------------------------- ambiente
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
globalThis.CustomEvent = window.CustomEvent;
globalThis.HTMLElement = window.HTMLElement;
globalThis.Element = window.Element;
globalThis.Node = window.Node;
globalThis.requestAnimationFrame = (fn) => setTimeout(() => fn(Date.now()), 16);
globalThis.location = window.location;
globalThis.localStorage = window.localStorage;
window.Element.prototype.scrollIntoView = function () {};

/** Worker falso: responde UCI com um lance legal do chess.js. */
class MotorFalso {
  constructor() {
    this.onmessage = null;
    this.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
    this.multipv = 1;
    this.contador = 0;
  }

  postMessage(cmd) {
    setTimeout(() => this._tratar(cmd), 0);
  }

  _emitir(texto) {
    this.onmessage?.({ data: texto });
  }

  _tratar(cmd) {
    if (cmd === 'uci') return this._emitir('uciok');
    if (cmd === 'isready') return this._emitir('readyok');
    if (cmd.startsWith('setoption name MultiPV value')) {
      this.multipv = Number(cmd.split(' ').pop());
      return;
    }
    if (cmd.startsWith('position fen ')) {
      this.fen = cmd.slice('position fen '.length);
      return;
    }
    if (cmd.startsWith('go')) {
      const jogo = new Chess(this.fen);
      const lances = jogo.moves({ verbose: true });
      if (!lances.length) return this._emitir('bestmove (none)');
      // "melhor" lance = último da lista (determinístico, mas não sempre o primeiro)
      const escolhido = lances[(lances.length + this.contador) % lances.length];
      this.contador++;
      for (let i = 1; i <= this.multipv; i++) {
        const mv = lances[(i - 1) % lances.length];
        const perda = (i - 1) * 45;
        this._emitir(
          `info depth 12 seldepth 14 multipv ${i} score cp ${20 - perda} nodes 50000 nps 400000 time 90 pv ${mv.from}${mv.to}${mv.promotion || ''} `,
        );
      }
      setTimeout(() => this._emitir(`bestmove ${escolhido.from}${escolhido.to}${escolhido.promotion || ''}`), 1);
      return;
    }
    if (cmd === 'stop') { /* nada */ }
  }
}

globalThis.Worker = MotorFalso;

const jogosSalvos = [];
globalThis.fetch = async (url, opcoes = {}) => {
  const rota = String(url);
  const responder = (corpo, status = 200) => ({
    ok: status < 400,
    status,
    json: async () => corpo,
    text: async () => JSON.stringify(corpo),
  });
  if (rota.startsWith('/api/jogos')) {
    if (opcoes.method === 'POST') {
      const dados = JSON.parse(opcoes.body);
      const registro = { id: `j${jogosSalvos.length + 1}`, ...dados, data: new Date().toISOString() };
      jogosSalvos.unshift(registro);
      return responder(registro);
    }
    if (opcoes.method === 'DELETE') return responder({ ok: true });
    return responder(jogosSalvos);
  }
  return responder({ erro: 'rota não mockada: ' + rota }, 404);
};

// ------------------------------------------------------------------- util

const esperar = async (condicao, { timeout = 15000, descricao = 'condição' } = {}) => {
  const inicio = Date.now();
  while (Date.now() - inicio < timeout) {
    if (await condicao()) return true;
    await new Promise((r) => setTimeout(r, 50));
  }
  throw new Error(`tempo esgotado esperando ${descricao}`);
};

const $ = (sel) => window.document.querySelector(sel);
const $$ = (sel) => [...window.document.querySelectorAll(sel)];
const clicar = (sel) => {
  const node = typeof sel === 'string' ? $(sel) : sel;
  assert.ok(node, `elemento ${sel} existe`);
  node.click();
};

let falhas = 0;
const teste = async (nome, fn) => {
  try {
    await fn();
    console.log(`  ✓ ${nome}`);
  } catch (err) {
    falhas++;
    console.error(`  ✗ ${nome}\n     ${err.message}`);
  }
};

// ------------------------------------------------------------------ testes

console.log('\n▶ Carregamento do app');
await import('../public/js/main.js');

await teste('módulos montam e expõem window.xadrez', async () => {
  assert.ok(window.xadrez, 'window.xadrez existe');
  assert.ok(window.xadrez.jogo && window.xadrez.analise && window.xadrez.biblioteca);
});

await teste('motor "sobe" e o cabeçalho mostra pronto', async () => {
  await esperar(() => $('#status-motor').classList.contains('ok'), { descricao: 'motor pronto' });
  assert.match($('#status-motor').textContent, /pronto/i);
});

await teste('o tabuleiro desenha 64 casas', async () => {
  assert.equal($$('#tab-jogar .casa').length, 64);
  assert.equal($$('#tab-analise .casa').length, 64);
});

await teste('a partida começa sozinha e o tabuleiro já está interativo', async () => {
  assert.equal(window.xadrez.jogo.emAndamento, true, 'partida em andamento ao abrir');
  assert.equal(window.xadrez.jogo.tabuleiro.interativo, true, 'tabuleiro aceitando toque');
  assert.equal($('#config-jogo').hidden, true, 'configuração recolhida');
  assert.equal($('#acoes-tabuleiro').hidden, false, 'barra de ações visível');
});

await teste('as peças são imagens SVG, uma por casa ocupada', async () => {
  const pecas = $$('#tab-jogar .peca');
  assert.equal(pecas.length, 32);
  assert.ok(pecas.every((p) => p.tagName === 'IMG'), 'todas são <img>');
  assert.ok(pecas.every((p) => /^pecas\/[wb][kqrbnp]\.svg$/.test(p.getAttribute('src'))), 'src de peça válido');
  for (const cor of ['w', 'b']) {
    for (const tipo of ['k', 'q', 'r', 'b', 'n', 'p']) {
      assert.ok(fs.existsSync(new URL(`../public/pecas/${cor}${tipo}.svg`, import.meta.url)), `pecas/${cor}${tipo}.svg existe`);
    }
  }
});

console.log('\n▶ Revisão de partida');

const PGN = `[Event "Teste de interface"]
[White "Brancas"]
[Black "Pretas"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0`;

await teste('revisar um PGN gera relatório', async () => {
  clicar('.aba[data-aba="analisar"]');
  assert.equal($('#view-analisar').hidden, false, 'aba de análise visível');
  $('#pgn').value = PGN;
  clicar('#btn-revisar');
  await esperar(() => !$('#relatorio').hidden, { descricao: 'relatório visível' });
  assert.match($('#acc-brancas').textContent, /%/);
  assert.match($('#acc-pretas').textContent, /%/);
  assert.ok($('#resumo-partida').textContent.length > 30, 'resumo tem texto');
  assert.ok($$('#lances-analise .lance').length >= 7, 'lista de lances preenchida');
  assert.ok($$('#contagem-classes .chip-classe').length > 0, 'contagem de classes');
});

await teste('clicar num lance mostra explicação e setas', async () => {
  const botoes = $$('#lances-analise .lance');
  clicar(botoes[botoes.length - 1]);
  const caixa = $('#explicacao');
  assert.ok(caixa.querySelector('h4'), 'tem título');
  assert.ok(caixa.querySelector('p.texto').textContent.length > 20, 'tem texto explicativo');
  assert.ok($$('#setas-analise line').length >= 1, 'seta desenhada');
  assert.match($('#lance-atual').textContent, /Qxf7#/);
});

await teste('navegação por teclado e gráfico', async () => {
  const antes = $('#lance-atual').textContent;
  window.document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'ArrowLeft' }));
  await new Promise((r) => setTimeout(r, 50));
  assert.notEqual($('#lance-atual').textContent, antes);
  assert.ok($$('#grafico-analise path').length >= 2, 'gráfico com área e linha');
});

await teste('revisão é salva na biblioteca', async () => {
  assert.ok(jogosSalvos.length >= 1, 'POST /api/jogos foi chamado');
  assert.ok(jogosSalvos[0].revisao?.accuracy, 'guarda a precisão');
});

console.log('\n▶ Jogar contra o bot');

await teste('começar partida e jogar e4', async () => {
  clicar('.aba[data-aba="jogar"]');
  $('#nivel').value = '800';
  clicar('#btn-comecar');
  assert.equal($('#jogo-ativo').hidden, false);
  assert.equal($$('#tab-jogar .peca').length, 32, '32 peças no tabuleiro');

  clicar('#tab-jogar .casa[data-sq="e2"]');
  clicar('#tab-jogar .casa[data-sq="e4"]');
  await esperar(() => window.xadrez.jogo.chess.history().length >= 2, { descricao: 'bot responder' });
  assert.equal(window.xadrez.jogo.chess.history()[0], 'e4');
});

await teste('lista de lances do jogo é atualizada', async () => {
  assert.ok($$('#lances-jogar .lance').length >= 2);
});

await teste('dica desenha seta', async () => {
  if (!window.xadrez.jogo.emAndamento) return; // partida pode ter acabado
  clicar('#btn-dica');
  await esperar(() => $$('#setas-jogar line').length >= 1, { descricao: 'seta da dica' });
});

console.log('\n▶ Regressões da v1.1 (tabuleiro tocável)');

await teste('lance resolvido pela geometria, não pelo elemento tocado', async () => {
  clicar('.aba[data-aba="jogar"]');
  $('#nivel').value = '800';
  clicar('#btn-comecar');
  const raiz = $('#tab-jogar');
  // jsdom não calcula layout: damos um retângulo de 800×800 para a conta 8×8
  raiz.getBoundingClientRect = () => ({ left: 0, top: 0, width: 800, height: 800, right: 800, bottom: 800 });
  const tab = window.xadrez.jogo.tabuleiro;

  assert.equal(tab._casaDoPonto(450, 650), 'e2', 'centro de e2');
  assert.equal(tab._casaDoPonto(450, 450), 'e4', 'centro de e4');
  assert.equal(tab._casaDoPonto(-5, 10), null, 'fora do tabuleiro');
  assert.equal(tab._casaDoPonto(10, 10), 'a8', 'canto superior esquerdo');

  const tocar = (x, y) => raiz.dispatchEvent(new window.MouseEvent('click', {
    clientX: x, clientY: y, bubbles: true, cancelable: true,
  }));
  tocar(450, 650); // peça de e2
  assert.ok($('#tab-jogar .casa[data-sq="e2"]').classList.contains('selecionada'), 'e2 selecionada');
  assert.ok($$('#tab-jogar .casa.destino').length > 0, 'destinos marcados');
  tocar(450, 450); // solta/lance em e4
  await esperar(() => window.xadrez.jogo.chess.history().includes('e4'), { descricao: 'lance e4' });
  assert.equal(window.xadrez.jogo.chess.history()[0], 'e4');
});

await teste('lance com tabuleiro girado continua na casa certa', async () => {
  const tab = window.xadrez.jogo.tabuleiro;
  tab.setOrientacao('b');
  assert.equal(tab._casaDoPonto(450, 650), 'd7', 'com pretas embaixo, y alto é a 7ª fileira');
  assert.equal(tab._casaDoPonto(50, 50), 'h1', 'canto superior esquerdo passa a ser h1');
  tab.setOrientacao('w');
});

await teste('overlay de promoção escondido não cobre o tabuleiro', async () => {
  const promo = $('#promo-jogar');
  assert.ok(promo.hasAttribute('hidden'), 'promoção começa oculta');
  const css = fs.readFileSync(new URL('../public/styles.css', import.meta.url), 'utf8')
    .replace(/\/\*[\s\S]*?\*\//g, '');   // sem comentários: eles citam seletores
  assert.match(css, /\[hidden\]\s*\{\s*display:\s*none\s*!important/, 'regra global [hidden] presente');
  assert.ok(!/\.promocao\s*\{[^}]*display:\s*flex/.test(css), 'display do overlay é guardado por :not([hidden])');
  assert.ok(/\.promocao:not\(\[hidden\]\)/.test(css), 'overlay só aparece quando visível');
});

await teste('todo id usado pelo JS existe no HTML', async () => {
  const arquivos = ['main.js', 'jogo.js', 'analise.js', 'biblioteca.js', 'board.js', 'util.js'];
  const faltando = [];
  for (const arquivo of arquivos) {
    const fonte = fs.readFileSync(new URL(`../public/js/${arquivo}`, import.meta.url), 'utf8');
    for (const m of fonte.matchAll(/getElementById\('([^']+)'\)/g)) {
      if (!window.document.getElementById(m[1])) faltando.push(`${arquivo}: #${m[1]}`);
    }
  }
  assert.deepEqual(faltando, []);
});

console.log('\n▶ Biblioteca');

await teste('biblioteca lista as partidas salvas', async () => {
  clicar('.aba[data-aba="biblioteca"]');
  await esperar(() => $$('#lista-biblioteca .cartao-jogo').length > 0, { descricao: 'cartões' });
  assert.ok($('#lista-biblioteca').textContent.includes('precisão') || $$('#lista-biblioteca .cartao-jogo').length >= 1);
});

console.log(falhas ? `\n✗ ${falhas} teste(s) falharam` : '\n✓ interface ok');
process.exit(falhas ? 1 : 0);
