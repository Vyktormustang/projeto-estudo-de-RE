/**
 * Gera as 12 peças do Xadrez Studio em SVG (conjunto próprio, desenho nosso).
 *
 *   node tools/gerar-pecas.mjs            # grava app/public/pecas/*.svg
 *   node tools/gerar-pecas.mjs --previa   # também escreve /tmp/pecas-previa.svg
 *
 * Estilo: silhueta cheia com contorno grosso, sem gradiente — o mesmo espírito
 * do conjunto "Neo" do chess.com, mas desenhado aqui do zero (nada copiado:
 * nem os arquivos, nem os paths deles).
 *
 * Como o contorno fica limpo: cada peça é montada com formas simples (círculo,
 * elipse, retângulo, path). Elas são desenhadas duas vezes:
 *   1. passe de contorno — só traço, bem grosso;
 *   2. passe de preenchimento — as mesmas formas, em ordem inversa.
 * Assim o preenchimento cobre o traço "de dentro" das formas vizinhas e o
 * resultado é uma silhueta única, sem costura aparente entre as partes.
 */

import fs from 'node:fs';
import path from 'node:path';

const LADO = 45;

const CORES = {
  w: { corpo: '#FFFFFF', linha: '#2B2926', detalhe: '#2B2926' },
  b: { corpo: '#312E2B', linha: '#12110F', detalhe: '#F2EFEA' },
};

// --------------------------------------------------------------- primitivas

const n = (v) => Number(v.toFixed(2));
const circulo = (cx, cy, r) => ({ t: 'circle', cx, cy, r });
const elipse = (cx, cy, rx, ry) => ({ t: 'ellipse', cx, cy, rx, ry });
const ret = (x, y, w, h, rx = 0) => ({ t: 'rect', x, y, w, h, rx });
const caminho = (d) => ({ t: 'path', d });

function formaSvg(f) {
  if (f.t === 'circle') return `<circle cx="${n(f.cx)}" cy="${n(f.cy)}" r="${n(f.r)}"/>`;
  if (f.t === 'ellipse') return `<ellipse cx="${n(f.cx)}" cy="${n(f.cy)}" rx="${n(f.rx)}" ry="${n(f.ry)}"/>`;
  if (f.t === 'rect') {
    const rx = f.rx ? ` rx="${n(f.rx)}"` : '';
    return `<rect x="${n(f.x)}" y="${n(f.y)}" width="${n(f.w)}" height="${n(f.h)}"${rx}/>`;
  }
  return `<path d="${f.d}"/>`;
}

/** Silhueta: traço grosso + preenchimento por cima (ordem inversa). */
function silhueta(formas, cor) {
  const traco = formas.map(formaSvg).join('');
  const corpo = [...formas].reverse().map(formaSvg).join('');
  return `<g stroke="${cor.linha}" stroke-width="2.3" stroke-linejoin="round" stroke-linecap="round" fill="none">${traco}</g>`
    + `<g fill="${cor.corpo}" stroke="none">${corpo}</g>`;
}

/** Detalhe (olho, fenda, linha da coroa) desenhado por cima da silhueta. */
function detalhe(conteudo, cor, espessura = 1.15) {
  return `<g fill="${cor.detalhe}" stroke="${cor.detalhe}" stroke-width="${espessura}" stroke-linecap="round" stroke-linejoin="round">${conteudo}</g>`;
}

// ------------------------------------------------------------------- peças

const BASE = ret(10.6, 36.4, 23.8, 5.2, 2.4);
const COLO = ret(13.6, 33.3, 17.8, 3.6, 1.6);

function peao(cor) {
  const formas = [
    BASE,
    COLO,
    caminho('M16.8 34.2c1.3-4.7 2.2-8.3 2.4-12.5h6.6c.2 4.2 1.1 7.8 2.4 12.5z'),
    circulo(22.5, 14.4, 6.1),
  ];
  return silhueta(formas, cor);
}

function torre(cor) {
  const formas = [
    BASE,
    ret(12.9, 32.9, 19.2, 4.2, 1.6),
    caminho('M15.4 33.6 16.5 16.6h12l1.1 17z'),
    caminho('M15.2 16.8V9.5c0-.7.6-1.3 1.3-1.3h3.1v3.4h2.4V8.2h5v3.4h2.4V8.2h3.1c.7 0 1.3.6 1.3 1.3v7.3z'),
  ];
  return silhueta(formas, cor);
}

function bispo(cor) {
  const formas = [
    BASE,
    COLO,
    caminho('M17.4 33.8c1.3-4.2 2.7-7.4 3.5-10.6h3.2c.8 3.2 2.2 6.4 3.5 10.6z'),
    caminho('M22.5 9.8c3.7 4.4 5.5 8.1 5.5 11a5.5 5.5 0 0 1-11 0c0-2.9 1.8-6.6 5.5-11z'),
    circulo(22.5, 7.4, 1.85),
  ];
  return silhueta(formas, cor)
    // corte diagonal da mitra, como no bispo do chess.com
    + detalhe('<path d="M25.6 14.2 22.2 20.4" fill="none"/>', cor, 1.8);
}

function rainha(cor) {
  const formas = [
    BASE,
    COLO,
    caminho('M16.2 34c1.9-7.4 3.2-13.6 4.4-16.4h3.8c1.2 2.8 2.5 9 4.4 16.4z'),
    ret(16.8, 15.2, 11.4, 3.4, 1.2),
    caminho('M16.6 15.8 17.5 9.4l2.9 4.4 2.1-6.6 2.1 6.6 2.9-4.4.9 6.4z'),
    circulo(17.5, 8.6, 1.2),
    circulo(22.5, 6.4, 1.3),
    circulo(27.5, 8.6, 1.2),
  ];
  return silhueta(formas, cor);
}

function rei(cor) {
  const formas = [
    BASE,
    COLO,
    caminho('M14.6 33.8c1.8-5.6 3.2-10 4-14.4h7.8c.8 4.4 2.2 8.8 4 14.4z'),
    caminho('M16.2 34c1.9-7.4 3.2-13.6 4.4-16.4h3.8c1.2 2.8 2.5 9 4.4 16.4z'),
    ret(16.6, 14.6, 11.8, 3.6, 1.2),
    caminho('M17.2 15.2 17.9 9.8l3.2 3.6 1.4-5.4 1.4 5.4 3.2-3.6.7 5.4z'),
    ret(21.4, 3.2, 2.2, 6.6, 0.7),
    ret(19, 5.2, 7, 2.1, 0.7),
  ];
  return silhueta(formas, cor)
    + detalhe('<circle cx="22.5" cy="17" r="1" stroke="none"/>', cor);   // joia da coroa
}

function cavalo(cor) {
  // Perfil montado por partes; o passe de contorno + preenchimento unem tudo.
  const formas = [
    BASE,
    // pescoço: do peito (esquerda) até a garupa (direita)
    caminho('M22.8 19.4c-3.2 3.6-5 8.2-4.8 13.2l.1 4.2h17.4l-.3-7.6c-.3-4.2-1.8-7.6-4.4-9.8z'),
    // crânio
    circulo(26.2, 15.4, 5.8),
    // focinho comprido, em cunha, apontando para baixo à esquerda
    caminho('M20.2 13.6 11.6 21.2l1.8 3.6 8.6-4.8 3-3.2z'),
    // queixo/mandíbula fechando o focinho
    caminho('M14.2 24.2l9.4-5.2 1.2 3-8.4 5z'),
    // orelha
    caminho('M23 10.4 24.2 4.6l3 6z'),
  ];
  return silhueta(formas, cor)
    + detalhe('<circle cx="21.4" cy="15.8" r="1.1" stroke="none"/>', cor)        // olho
    + detalhe('<circle cx="13.6" cy="22.6" r=".95" stroke="none"/>', cor)        // narina
    + detalhe('<path d="M30.6 19.6c1 1.8 1.4 4 1.4 6.4" fill="none"/>', cor, 1.1)  // crina
    + detalhe('<path d="M31.8 20.4c.9 1.8 1.3 3.9 1.3 6.2" fill="none" opacity=".5"/>', cor, 1);
}

const DESENHOS = { p: peao, r: torre, n: cavalo, b: bispo, q: rainha, k: rei };

// ---------------------------------------------------------------- montagem

function svgPeca(tipo, cor) {
  const corpo = DESENHOS[tipo](CORES[cor]);
  return `<?xml version="1.0" encoding="UTF-8"?>
<!-- Peça de xadrez "${cor}${tipo}" do Xadrez Studio — desenho próprio, gerado por
     tools/gerar-pecas.mjs. Sem código nem arte de terceiros. -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${LADO} ${LADO}" width="${LADO}" height="${LADO}">
${corpo}
</svg>
`;
}

const destino = path.join(import.meta.dirname, '..', 'app', 'public', 'pecas');
let escritos = 0;
for (const cor of ['w', 'b']) {
  for (const tipo of Object.keys(DESENHOS)) {
    fs.writeFileSync(path.join(destino, `${cor}${tipo}.svg`), svgPeca(tipo, cor));
    escritos++;
  }
}
console.log(`✓ ${escritos} peças geradas em ${path.relative(process.cwd(), destino)}`);

// prévia (fora do repositório): peças claras e escuras nas duas cores de casa
if (process.argv.includes('--previa')) {
  const ordem = ['k', 'q', 'r', 'b', 'n', 'p'];
  const L = 70;
  const partes = [];
  for (const cor of ['w', 'b']) {
    ordem.forEach((tipo, i) => {
      const x = i * L;
      const y = cor === 'w' ? 0 : L;
      const clara = (i + (cor === 'w' ? 0 : 1)) % 2 === 0;
      partes.push(`<rect x="${x}" y="${y}" width="${L}" height="${L}" fill="${clara ? '#ebecd0' : '#739552'}"/>`);
      const interno = fs.readFileSync(path.join(destino, `${cor}${tipo}.svg`), 'utf8')
        .replace(/^[\s\S]*?<svg[^>]*>/, '').replace('</svg>', '');
      partes.push(`<g transform="translate(${x + L * 0.04},${y + L * 0.04}) scale(${(L * 0.92) / LADO})">${interno}</g>`);
    });
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${L * ordem.length}" height="${L * 2}" viewBox="0 0 ${L * ordem.length} ${L * 2}">${partes.join('')}</svg>`;
  fs.writeFileSync('/tmp/pecas-previa.svg', svg);
  console.log('✓ prévia em /tmp/pecas-previa.svg');
}
