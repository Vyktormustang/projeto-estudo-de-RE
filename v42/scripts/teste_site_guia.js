// Simula o DOM mínimo e roda a lógica de render do guia
const fs = require('fs');
const path = require('path');
const raiz = path.resolve(__dirname, '..', '..');
const site = process.argv[2] ? path.resolve(process.argv[2]) : path.join(raiz, 'site_guia');
const html = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
const m = html.match(/<script>([\s\S]*)<\/script>/);

const els = {};
function el(id){ if(!els[id]) els[id]={id,value:'',innerHTML:'',textContent:'',
  addEventListener(){}, }; return els[id]; }
global.document = { getElementById: el };

// roda o script real (com o JSON completo embutido)
eval(m[1]);

const total = els['contador'].textContent;
if (!/^1025 de 1025/.test(total)) { console.error('[FAIL] contador inesperado: ' + total); process.exit(1); }
console.log('[PASS] contador:', total);
const nCards = (els['lista'].innerHTML.match(/class="card"/g)||[]).length;
if (nCards !== 60) { console.error('[FAIL] cards: ' + nCards); process.exit(1); }
console.log('[PASS] cards renderizados: ' + nCards);

// busca por nome
els['q'].value = 'cosmog';
eval(m[1]);
if (!/^1 de 1025/.test(els['contador'].textContent)) { console.error('[FAIL] busca cosmog'); process.exit(1); }
console.log('[PASS] busca "cosmog" -> ' + els['contador'].textContent);
const card = els['lista'].innerHTML;
if (!/evento fixo/.test(card)) { console.error('[FAIL] cosmog sem evento fixo'); process.exit(1); }
if (!/Evolução/.test(card)) { console.error('[FAIL] cosmog sem evolucao'); process.exit(1); }
console.log('[PASS] cosmog mostra evento fixo + evolucao');

// filtro lendário
els['q'].value=''; els['raros'].value='lendario';
eval(m[1]);
if (!/^94 de 1025/.test(els['contador'].textContent)) { console.error('[FAIL] filtro lendario: ' + els['contador'].textContent); process.exit(1); }
console.log('[PASS] so lendarios -> ' + els['contador'].textContent);
