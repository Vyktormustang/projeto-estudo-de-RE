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
      globalThis.__buscas = (globalThis.__buscas || 0) + 1;
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
// finge um celular de 8 núcleos: é o que o app vê em hardware real e o que
// habilita o pool de análise em paralelo
Object.defineProperty(window.navigator, 'hardwareConcurrency', { value: 8, configurable: true });
Object.defineProperty(window.navigator, 'deviceMemory', { value: 8, configurable: true });
// no Node 22 existe um `navigator` global (2 núcleos aqui): o app tem que enxergar
// o navegador, então trocamos o global pelo do jsdom
Object.defineProperty(globalThis, 'navigator', { value: window.navigator, configurable: true });
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

await teste('a revisão roda em paralelo com orçamento de tempo', async () => {
  const revisao = window.xadrez.analise;
  assert.ok(revisao.pool, 'pool de motores criado');
  assert.equal(revisao.pool.tamanho, 3, 'até 3 motores em paralelo');
  assert.ok(revisao.pool.motores.length >= 2, `pool com ${revisao.pool.motores.length} motores`);
  assert.equal(revisao.perfil.depth, 14, 'Automática usa depth 14');
  assert.ok(revisao.perfil.movetime >= 120 && revisao.perfil.movetime <= 1300, 'teto de tempo por posição');
  assert.match($('#info-revisao').textContent, /depth 14/);
  assert.match($('#info-revisao').textContent, /2 linhas por posição/);
  assert.match($('#dica-analise').textContent, /núcleo/i);
});

await teste('perfis de análise respeitam piso, teto e tamanho da partida', async () => {
  const { perfilDeAnalise, estimarSegundos, PERFIS_ANALISE } = await import('../public/js/engine.js');
  const auto = perfilDeAnalise('auto', 80, 3);
  assert.equal(auto.depth, 14, 'partida curta: depth 14');
  assert.ok(auto.movetime >= 120 && auto.movetime <= 1200);
  const autolonga = perfilDeAnalise('auto', 300, 3);
  assert.equal(autolonga.depth, 12, 'partida longa desce para depth 12');
  assert.ok(autolonga.movetime < auto.movetime, 'mais posições = menos tempo por posição');
  assert.ok(autolonga.movetime >= 120, 'respeita o piso mínimo');
  const rapida = perfilDeAnalise('12', 80, 3);
  assert.equal(rapida.depth, 12);
  assert.ok(rapida.movetime <= auto.movetime, 'rápida não passa da automática');
  assert.equal(perfilDeAnalise('18', 10, 1).depth, 18);
  assert.equal(perfilDeAnalise('desconhecido', 10, 1).escolha, 'auto');
  assert.ok(PERFIS_ANALISE.auto.profundidades.length === 2);
  assert.ok(estimarSegundos(80, auto) > 0);
});

await teste('revisar de novo o mesmo PGN não repete buscas (cache)', async () => {
  const revisao = window.xadrez.analise;
  const cacheAntes = revisao.pool.acertosCache;
  const buscasAntes = globalThis.__buscas || 0;
  clicar('#btn-revisar');
  await esperar(() => revisao.pool.acertosCache > cacheAntes, { descricao: 'acertos de cache' });
  await esperar(() => revisao.revisando === false, { descricao: 'fim da revisão' });
  assert.equal(globalThis.__buscas || 0, buscasAntes, 'nenhuma busca nova no motor');
});

await teste('a assistência do modo Jogar usa um motor separado do bot', async () => {
  const { motor, motorAjuda } = await import('../public/js/engine.js');
  assert.notEqual(motor, motorAjuda, 'instâncias diferentes');
  assert.equal(window.xadrez.motor, motor, 'o bot continua no motor principal');
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

await teste('a classificação do lance aparece em cima da peça', async () => {
  const { CLASS_INFO } = await import('../public/js/review.js');
  const revisao = window.xadrez.analise;
  const botoes = $$('#lances-analise .lance');
  clicar(botoes[botoes.length - 1]);

  const lance = revisao.review.moves.at(-1);
  const selos = $$('#tab-analise .marca-classe');
  assert.equal(selos.length, 1, 'um selo por vez, no último lance');
  const selo = selos[0];
  assert.ok(selo.closest('.casa')?.dataset.sq === lance.to,
    `selo na casa de destino (${lance.to})`);
  assert.equal(selo.tagName.toLowerCase(), 'svg', 'selo é SVG: escala com a casa');
  assert.match(selo.getAttribute('aria-label'), new RegExp(CLASS_INFO[lance.class].label),
    'rótulo acessível com a classe');

  const info = CLASS_INFO[lance.class];
  assert.equal(selo.querySelector('circle').getAttribute('fill'), info.color, 'cor da classe');
  assert.equal(selo.querySelector('text').textContent, info.short, 'símbolo da classe');
  assert.equal(selo.parentElement.lastElementChild, selo, 'desenhado por cima da peça');

  clicar('#nav-inicio');
  assert.equal($$('#tab-analise .marca-classe').length, 0, 'posição inicial não tem selo');

  clicar('#nav-avancar');
  const primeiro = revisao.review.moves[0];
  const seloPrimeiro = $('#tab-analise .marca-classe');
  assert.ok(seloPrimeiro, 'volta a mostrar o selo ao navegar');
  assert.equal(seloPrimeiro.closest('.casa').dataset.sq, primeiro.to, 'segue o lance ' + primeiro.san);
  assert.equal(seloPrimeiro.querySelector('text').textContent, CLASS_INFO[primeiro.class].short);
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

  // o feedback depende da análise da posição antes do lance: espera ela existir
  await esperar(() => window.xadrez.jogo.analiseAntes, { descricao: 'análise inicial do modo Jogar' });
  clicar('#tab-jogar .casa[data-sq="e2"]');
  clicar('#tab-jogar .casa[data-sq="e4"]');
  await esperar(() => window.xadrez.jogo.chess.history().length >= 2, { descricao: 'bot responder' });
  assert.equal(window.xadrez.jogo.chess.history()[0], 'e4');
});

await teste('no modo Jogar o selo marca o seu lance', async () => {
  const jogo = window.xadrez.jogo;
  await esperar(() => $$('#tab-jogar .marca-classe').length === 1, { descricao: 'selo no lance' });
  const selo = $('#tab-jogar .marca-classe');
  const historico = jogo.chess.history({ verbose: true });
  assert.equal(selo.closest('.casa').dataset.sq, historico[0].to, 'selo no lance jogado (e4)');
  assert.ok(selo.querySelector('text').textContent.length >= 1, 'símbolo visível');
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
  assert.ok(/\.resultado:not\(\[hidden\]\)/.test(css), 'cartão de fim de jogo também é guardado');
  assert.ok(!/\.resultado\s*\{[^}]*display:/.test(css), 'cartão não define display fora do :not([hidden])');
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

console.log('\n▶ Arrastar peças (ponteiro)');

// jsdom não tem PointerEvent: um MouseEvent com pointerId/pointerType resolve
const ponteiro = (tipo, x, y, pointerType = 'touch') => {
  const ev = new window.MouseEvent(tipo, {
    clientX: x, clientY: y, bubbles: true, cancelable: true,
  });
  Object.defineProperty(ev, 'pointerId', { value: 7 });
  Object.defineProperty(ev, 'pointerType', { value: pointerType });
  return ev;
};
const tabuleiroDeTeste = () => {
  clicar('.aba[data-aba="jogar"]');
  clicar('#btn-comecar');
  const raiz = $('#tab-jogar');
  raiz.getBoundingClientRect = () => ({ left: 0, top: 0, width: 800, height: 800, right: 800, bottom: 800 });
  return raiz;
};
const casa = (sq) => $(`#tab-jogar .casa[data-sq="${sq}"]`);

await teste('arrastar com o dedo e soltar na casa legal faz o lance', async () => {
  const raiz = tabuleiroDeTeste();
  casa('d2').dispatchEvent(ponteiro('pointerdown', 350, 650));
  assert.ok(casa('d2').classList.contains('selecionada'), 'peça selecionada no toque');

  casa('d2').dispatchEvent(ponteiro('pointermove', 350, 460));
  assert.ok($('.peca-arrastando'), 'peça flutuante acompanhando o dedo');
  assert.ok(casa('d2').classList.contains('arrastando-origem'), 'origem esvaziada durante o arraste');

  raiz.dispatchEvent(ponteiro('pointerup', 350, 450));
  await esperar(() => window.xadrez.jogo.chess.history().includes('d4'), { descricao: 'lance d4' });
  assert.equal(window.xadrez.jogo.chess.history()[0], 'd4');
  assert.equal($('.peca-arrastando'), null, 'fantasma removido ao soltar');
  assert.ok(!casa('d2').classList.contains('arrastando-origem'), 'realce do arraste limpo');
});

await teste('arrastar e soltar fora de destino legal desmarca a peça', async () => {
  const raiz = tabuleiroDeTeste();
  casa('c2').dispatchEvent(ponteiro('pointerdown', 250, 650));
  casa('c2').dispatchEvent(ponteiro('pointermove', 250, 350));
  raiz.dispatchEvent(ponteiro('pointerup', 250, 350));
  assert.ok(!casa('c2').classList.contains('selecionada'), 'peça desmarcada');
  assert.equal($('.peca-arrastando'), null, 'fantasma removido');
  assert.deepEqual(window.xadrez.jogo.chess.history(), [], 'nenhum lance executado');
});

await teste('toque curto seleciona, segundo toque joga (tap-tap segue funcionando)', async () => {
  const raiz = tabuleiroDeTeste();
  casa('e2').dispatchEvent(ponteiro('pointerdown', 450, 650));
  raiz.dispatchEvent(ponteiro('pointerup', 450, 650));
  assert.ok(casa('e2').classList.contains('selecionada'), 'toque curto mantém a seleção');

  casa('e4').dispatchEvent(ponteiro('pointerdown', 450, 450));
  raiz.dispatchEvent(ponteiro('pointerup', 450, 450));
  await esperar(() => window.xadrez.jogo.chess.history().includes('e4'), { descricao: 'lance e4 por toque' });
  assert.equal(window.xadrez.jogo.chess.history()[0], 'e4');
});

await teste('arrastar também funciona com o mouse', async () => {
  const raiz = tabuleiroDeTeste();
  casa('g1').dispatchEvent(ponteiro('pointerdown', 650, 750, 'mouse'));
  casa('g1').dispatchEvent(ponteiro('pointermove', 550, 550, 'mouse'));   // f3
  raiz.dispatchEvent(ponteiro('pointerup', 550, 550, 'mouse'));
  await esperar(() => window.xadrez.jogo.chess.history().includes('Nf3'), { descricao: 'lance Nf3' });
});

console.log('\n▶ Fim de jogo');

await teste('desistir abre o cartão de resultado e a revanche reinicia', async () => {
  clicar('.aba[data-aba="jogar"]');
  clicar('#btn-comecar');
  clicar('#btn-desistir');
  assert.equal($('#resultado-jogo').hidden, false, 'cartão visível');
  assert.match($('#resultado-titulo').textContent, /perdeu/i);
  assert.equal(window.xadrez.jogo.emAndamento, false);

  clicar('#btn-revanche');
  assert.equal($('#resultado-jogo').hidden, true, 'cartão escondido na revanche');
  assert.equal(window.xadrez.jogo.emAndamento, true, 'nova partida em andamento');
  assert.equal($$('#tab-jogar .peca').length, 32, 'tabuleiro reiniciado');
});

console.log('\n▶ Biblioteca');

await teste('biblioteca lista as partidas salvas', async () => {
  clicar('.aba[data-aba="biblioteca"]');
  await esperar(() => $$('#lista-biblioteca .cartao-jogo').length > 0, { descricao: 'cartões' });
  assert.ok($('#lista-biblioteca').textContent.includes('precisão') || $$('#lista-biblioteca .cartao-jogo').length >= 1);
});

console.log(falhas ? `\n✗ ${falhas} teste(s) falharam` : '\n✓ interface ok');
process.exit(falhas ? 1 : 0);
