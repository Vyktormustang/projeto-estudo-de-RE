/**
 * Teste do armazenamento no modo do APK (localStorage, sem servidor).
 *   node tests/armazenamento.test.mjs
 */

import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';

// O APK abre a página com ?armazenamento=local
const dom = new JSDOM('', { url: 'http://127.0.0.1:8791/index.html?armazenamento=local' });
globalThis.location = dom.window.location;
globalThis.localStorage = dom.window.localStorage;

const { listarJogos, salvarJogo, excluirJogo, modoArmazenamento } = await import('../public/js/armazenamento.js');

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

console.log('\n▶ Armazenamento offline');

await teste('detecta o modo local pela URL', () => {
  assert.equal(modoArmazenamento(), 'local');
});

await teste('começa vazio', async () => {
  assert.deepEqual(await listarJogos(), []);
});

await teste('salva e lista', async () => {
  await salvarJogo({ pgn: '1. e4 e5 *', titulo: 'A', resultado: '*', origem: 'bot' });
  const lista = await listarJogos();
  assert.equal(lista.length, 1);
  assert.equal(lista[0].titulo, 'A');
  assert.ok(lista[0].id, 'gerou id');
  assert.ok(lista[0].data, 'carimbou data');
});

await teste('mesmo PGN não duplica (atualiza)', async () => {
  await salvarJogo({ pgn: '1. e4 e5 *', titulo: 'A revisada', revisao: { accuracy: { white: 80, black: 70 } } });
  const lista = await listarJogos();
  assert.equal(lista.length, 1, 'continua com 1 registro');
  assert.equal(lista[0].titulo, 'A revisada');
  assert.equal(lista[0].revisao.accuracy.white, 80);
});

await teste('segunda partida entra na frente', async () => {
  await salvarJogo({ pgn: '1. d4 d5 *', titulo: 'B' });
  const lista = await listarJogos();
  assert.equal(lista.length, 2);
  assert.equal(lista[0].titulo, 'B');
});

await teste('exclui pelo id', async () => {
  const lista = await listarJogos();
  await excluirJogo(lista[0].id);
  const depois = await listarJogos();
  assert.equal(depois.length, 1);
  assert.equal(depois[0].titulo, 'A revisada');
});

await teste('persiste no localStorage (sobrevive a recarregar)', async () => {
  const bruto = dom.window.localStorage.getItem('xadrez-studio:jogos');
  assert.ok(bruto && bruto.includes('A revisada'));
});

console.log(falhas ? `\n✗ ${falhas} falha(s)` : '\n✓ armazenamento offline ok');
process.exit(falhas ? 1 : 0);
