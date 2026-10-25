/**
 * Teste do núcleo de análise com o motor REAL (Stockfish via Node).
 *
 *   node tests/review.test.mjs            # roda as partidas de teste
 *   node tests/review.test.mjs --verbose  # imprime a revisão completa
 *
 * Valida: parsing UCI, expected points, classificação, precisão, explicações.
 */

import { createRequire } from 'node:module';
import assert from 'node:assert/strict';
import { Chess } from 'chess.js';
import { parseInfo, makeLineStore, parseBestMove } from '../public/js/uci.js';
import { buildReview, material, describeMove, pvToSan, CLASS_INFO } from '../public/js/review.js';

const require = createRequire(import.meta.url);

/** Usa o MESMO build que o app roda no navegador: lite, single-thread, sem SharedArrayBuffer. */
const ENGINE_PATH = require.resolve('stockfish/bin/stockfish-19-lite-single.js');
const verbose = process.argv.includes('--verbose');
const CLASS_KEYS = Object.keys(CLASS_INFO);

// ------------------------------------------------------------------ engine

const engine = require('stockfish')(ENGINE_PATH, onLine);
let pending = null;
let readyCb = null;

function onLine(line) {
  if (line.startsWith('readyok')) { readyCb?.(); return; }
  if (line.startsWith('bestmove')) {
    const done = pending;
    pending = null;
    done?.resolve(parseBestMove(line));
    return;
  }
  const info = parseInfo(line);
  if (info) pending?.store.add(info);
}

function cmd(c) { engine.processCommand(c); }

function go({ fen, depth = 12, multipv = 3 }) {
  return new Promise((resolve, reject) => {
    const store = makeLineStore();
    const timer = setTimeout(() => reject(new Error('timeout do engine')), 60000);
    pending = {
      store,
      resolve: (bm) => { clearTimeout(timer); resolve({ lines: store.lines(), best: bm }); },
    };
    cmd(`setoption name MultiPV value ${multipv}`);
    cmd(`position fen ${fen}`);
    cmd(`go depth ${depth}`);
  });
}

/**
 * O Stockfish em WASM descarta comandos enviados antes do módulo subir.
 * Por isso: insiste com "isready" até receber "readyok".
 */
function waitReady() {
  return new Promise((resolve, reject) => {
    let tries = 0;
    let done = false;
    readyCb = () => { done = true; resolve(); };
    const tick = () => {
      if (done) return;
      if (tries++ > 300) return reject(new Error('engine não respondeu a isready'));
      cmd('uci'); // o WASM descarta os primeiros comandos; mandar os dois acelera o boot
      cmd('isready');
      setTimeout(tick, 100);
    };
    tick();
  });
}

async function analysePgn(pgn, { depth = 12, multipv = 3 } = {}) {
  const chess = new Chess();
  chess.loadPgn(pgn);
  const history = chess.history({ verbose: true });
  let fens;
  if (chess.getHeaders().FEN) {
    const first = new Chess(chess.getHeaders().FEN);
    fens = [first.fen(), ...history.map((m) => m.after)];
  } else {
    fens = [history[0].before, ...history.map((m) => m.after)];
  }
  const positions = [];
  for (const fen of fens) {
    const turn = fen.split(' ')[1];
    const { lines } = await go({ fen, depth, multipv });
    positions.push({ fen, turn, lines });
  }
  return positions;
}

// ------------------------------------------------------------------ partidas

const GAMES = [
  {
    name: 'Mate do pastor — erro em Nf6, mate final',
    pgn: `[Event "Teste"]
[White "Brancas"]
[Black "Pretas"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0`,
    expect: (r) => {
      const nf6 = r.moves.find((m) => m.san === 'Nf6');
      assert.ok(nf6, 'achou Nf6');
      assert.equal(nf6.class, 'blunder', `Nf6 deve ser erro grave (foi ${nf6.class})`);
      assert.match(nf6.explanation.text, /mate/i, 'a explicação de Nf6 avisa do mate');
      const mate = r.moves.at(-1);
      assert.equal(mate.san, 'Qxf7#');
      assert.equal(mate.class, 'best', 'mate é sempre melhor lance');
      assert.match(mate.explanation.text, /mate/i, 'explicação do mate');
      assert.ok(r.summary.text.length > 20, 'resumo gerado');
      assert.ok(r.accuracy.white > 0 && r.accuracy.white <= 100, 'precisão das brancas no intervalo');
    },
  },
  {
    name: 'Lazard — sacrifício de cavalo em Ne3',
    pgn: `[Event "Teste"]
[White "Brancas"]
[Black "Pretas"]
[Result "0-1"]

1. d4 Nf6 2. Nd2 e5 3. dxe5 Ng4 4. h3 Ne3 5. fxe3 Qh4+ 6. g3 Qxg3# 0-1`,
    expect: (r) => {
      assert.equal(r.moves.length, 12, 'leu os 12 lances');
      for (const m of r.moves) {
        assert.ok(m.explanation?.text?.length > 20, `explicação de ${m.san} tem conteúdo`);
        assert.ok(CLASS_KEYS.includes(m.class), `classe válida em ${m.san}: ${m.class}`);
      }
      const sac = r.moves.find((m) => m.san === 'Ne3');
      assert.ok(['brilliant', 'best', 'great'].includes(sac.class), `Ne3 bem avaliado (foi ${sac.class})`);
      assert.ok(r.moves.some((m) => ['blunder', 'mistake', 'miss', 'inaccuracy'].includes(m.class)), 'achou erro');
    },
  },
  {
    name: 'Oportunidade perdida — mate em 1 ignorado (PGN com FEN)',
    pgn: `[Event "Teste"]
[SetUp "1"]
[FEN "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"]
[White "Brancas"]
[Black "Pretas"]

1. Rb1 h6 2. Rb8# 1-0`,
    expect: (r) => {
      const rb1 = r.moves[0];
      assert.equal(rb1.san, 'Rb1');
      assert.equal(rb1.class, 'miss', `Rb1 devia ser oportunidade perdida (foi ${rb1.class})`);
      assert.match(rb1.explanation.text, /melhor era|mate/i, 'explicação aponta o mate perdido');
      assert.equal(r.moves.at(-1).class, 'best', 'mate executado é melhor lance');
    },
  },
];

// ------------------------------------------------------------------ runner

await waitReady();
cmd('uci');
cmd('setoption name Hash value 64');

let failures = 0;
for (const game of GAMES) {
  process.stdout.write(`\n▶ ${game.name}\n`);
  try {
    const t0 = Date.now();
    const positions = await analysePgn(game.pgn);
    const review = buildReview({ pgn: game.pgn, positions });
    game.expect(review);
    console.log(`  ok — ${review.moves.length} lances em ${Date.now() - t0} ms`);
    console.log(`  precisão: brancas ${review.accuracy.white}% · pretas ${review.accuracy.black}%`);
    console.log(`  classes: ${Object.entries(review.counts).filter(([, v]) => v).map(([k, v]) => `${k}=${v}`).join(' ')}`);
    console.log(`  resumo: ${review.summary.text}`);
    if (verbose) {
      for (const m of review.moves) {
        console.log(`  ${m.moveNumber}${m.color === 'w' ? '.' : '...'} ${m.san.padEnd(7)} ${m.class.padEnd(11)} ${m.explanation.text}`);
      }
    }
  } catch (err) {
    failures++;
    console.error(`  FALHOU: ${err.message}`);
  }
}

// testes unitários rápidos (sem engine)
{
  const start = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  assert.deepEqual(material(start), { white: 39, black: 39, diff: 0 });
  const d = describeMove(start, 'e2e4');
  assert.equal(d.san, 'e4');
  assert.equal(d.opensCenter, true);
  assert.deepEqual(pvToSan('r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4', ['f1c4']), [], 'lance ilegal é ignorado');
  console.log('\n✓ testes unitários passaram');
}

console.log(failures ? `\n✗ ${failures} partida(s) falharam` : '\n✓ todas as partidas passaram');
process.exit(failures ? 1 : 0);
