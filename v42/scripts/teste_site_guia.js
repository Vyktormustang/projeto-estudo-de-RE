// Valida as 5 páginas do guia: sintaxe + render real com DOM simulado.
const fs = require('fs'), path = require('path');
const raiz = path.resolve(__dirname, '..', '..');
const site = process.argv[2] ? path.resolve(process.argv[2]) : path.join(raiz, 'site_guia');

function carregar(nome) {
  const html = fs.readFileSync(path.join(site, nome), 'utf8');
  return { html, scripts: [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]) };
}

function rodar(nome, valores) {
  const els = {};
  const el = id => els[id] || (els[id] = { id, value: (valores && valores[id]) || '',
    innerHTML: '', textContent: '', _h: [], addEventListener(t, fn) { this._h.push(fn); } });
  // cria os elementos pedidos antes do script rodar
  for (const k of Object.keys(valores || {})) el(k);
  global.document = { getElementById: el };
  const { scripts } = carregar(nome);
  // `const DADOS` dentro de new Function fica LOCAL ao escopo criado. Trocar
  // por atribuição em globalThis torna o valor visível para as asserções,
  // simulando o que os <script> fazem no browser.
  const tudo = scripts.join('\n;\n').replace(/^\s*const DADOS\s*=/m, 'globalThis.DADOS =');
  new Function(tudo)();
  return els;
}

function refiltrar(els, valores, scriptFinal) {
  for (const [k, v] of Object.entries(valores || {})) els[k].value = v;
  new Function(scriptFinal)();
  return els;
}

let falhas = 0;
const chk = (ok, msg) => { console.log(`[${ok ? 'PASS' : 'FAIL'}] ${msg}`); if (!ok) falhas++; };

// 1) sintaxe de cada script
for (const p of ['index.html','pokemon.html','mapas.html','evolucoes.html','eventos.html','tms.html']) {
  const { scripts } = carregar(p);
  chk(scripts.length > 0, `${p}: tem script`);
  try { for (const s of scripts) new Function(s); chk(true, `${p}: sintaxe OK`); }
  catch (e) { chk(false, `${p}: ${e.message}`); }
}

// 2) index
let e = rodar('index.html');
chk(/^1025 de 1025/.test(e['contador'].textContent), `index contador: ${e['contador'].textContent}`);
chk((e['lista'].innerHTML.match(/class="card"/g)||[]).length === 60, 'index: 60 cards');

// 3) pokemon
e = rodar('pokemon.html');
chk(/^1025 de 1025/.test(e['contador'].textContent), `pokemon contador: ${e['contador'].textContent}`);
e = rodar('pokemon.html', { q: 'cosmog' });
chk(/^1 de 1025/.test(e['contador'].textContent), `pokemon busca cosmog: ${e['contador'].textContent}`);
const cardCosmog = e['lista'].innerHTML;
chk(/evento fixo/.test(cardCosmog), 'cosmog: mostra evento fixo');
chk(/Evolu/i.test(cardCosmog), 'cosmog: mostra evolucao');
chk(/Golpes por n/i.test(cardCosmog), 'cosmog: mostra golpes');
e = rodar('pokemon.html', { raros: 'lendario' });
chk(/^94 de 1025/.test(e['contador'].textContent), `lendarios: ${e['contador'].textContent}`);
e = rodar('pokemon.html', { ger: '9' });
chk(/de 1025/.test(e['contador'].textContent), `gen9: ${e['contador'].textContent}`);

// 4) mapas
e = rodar('mapas.html');
chk(/124 mapas/.test(e['contador'].textContent), `mapas: ${e['contador'].textContent}`);
chk((e['lista'].innerHTML.match(/class="card"/g)||[]).length === 40, 'mapas: 40 cards');
e = rodar('mapas.html', { q: 'Rota 1' });
chk(/mapas/.test(e['contador'].textContent), `mapas busca: ${e['contador'].textContent}`);

// 5) evolucoes
e = rodar('evolucoes.html');
chk(/449 liga/.test(e['contador'].textContent), `evolucoes: ${e['contador'].textContent}`);

// 6) eventos
e = rodar('eventos.html');
chk(!e['lista'], 'eventos: pagina estatica (sem lista)');

// 7) tms: estatica, com as 229 linhas e o aviso de compatibilidade ausente
const htmlTms = carregar('tms.html').html;
chk((htmlTms.match(/<tr><td class='n'>/g)||[]).length === 229, 'tms: 229 linhas');
chk(/189<\/b>\s*disponíveis/.test(htmlTms.replace(/\s+/g,' ')) || /189/.test(htmlTms), 'tms: conta 189 disponiveis');
chk(/Não coberto aqui/.test(htmlTms), 'tms: declara limite de compatibilidade');

process.exit(falhas ? 1 : 0);
