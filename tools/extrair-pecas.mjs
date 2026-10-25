/**
 * Extrai as 12 peças do sprite "standard" (conjunto cburnett, CC BY-SA 3.0) para
 * arquivos SVG individuais em app/public/pecas/.
 *
 * O sprite de origem está em tools/pieces-standard.svg e viene do projeto
 * cm-chessboard (MIT), que por sua vez copia os SVG do Wikimedia Commons:
 * https://commons.wikimedia.org/wiki/Category:SVG_chess_pieces/Standard
 *
 *   node tools/extrair-pecas.mjs
 *
 * Roda sem dependências: só lê o sprite e escreve os arquivos.
 */

import fs from 'node:fs';
import path from 'node:path';

const raiz = path.resolve(new URL('..', import.meta.url).pathname);
const fonte = path.join(raiz, 'tools', 'pieces-standard.svg');
const destino = path.join(raiz, 'app', 'public', 'pecas');

const sprite = fs.readFileSync(fonte, 'utf8');
const nomes = ['wk', 'wq', 'wr', 'wb', 'wn', 'wp', 'bk', 'bq', 'br', 'bb', 'bn', 'bp'];

/** Pega o conteúdo do <g id="wk">…</g> respeitando aninhamento. */
function extrairGrupo(id) {
  const abertura = new RegExp(`<g\\b[^>]*\\bid="${id}"[^>]*>`, 'i');
  const achado = abertura.exec(sprite);
  if (!achado) throw new Error(`grupo ${id} não encontrado no sprite`);
  const inicio = achado.index + achado[0].length;
  let profundidade = 1;
  let i = inicio;
  while (i < sprite.length && profundidade > 0) {
    const abre = sprite.indexOf('<g', i);
    const fecha = sprite.indexOf('</g>', i);
    if (fecha === -1) break;
    if (abre !== -1 && abre < fecha) {
      profundidade++;
      i = abre + 2;
    } else {
      profundidade--;
      if (profundidade === 0) return { atributos: achado[0], corpo: sprite.slice(inicio, fecha) };
      i = fecha + 4;
    }
  }
  throw new Error(`grupo ${id} não fechou`);
}

fs.mkdirSync(destino, { recursive: true });

for (const id of nomes) {
  const { atributos, corpo } = extrairGrupo(id);
  // remove handles de edição do Inkscape e ids repetidos
  const limpar = (texto) => texto
    .replace(/\s+id="[^"]*"/g, '')
    .replace(/\s+inkscape:[a-z-]+="[^"]*"/g, '')
    .replace(/\s+sodipodi:[a-z-]+="[^"]*"/g, '')
    .replace(/\s+xmlns:(inkscape|sodipodi)="[^"]*"/g, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/\n\s*/g, '\n    ');
  const abre = limpar(atributos);
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<!-- Peça de xadrez "${id}" — conjunto cburnett (Wikimedia Commons), CC BY-SA 3.0.
     Origem: https://commons.wikimedia.org/wiki/Category:SVG_chess_pieces/Standard
     Gerado por tools/extrair-pecas.mjs a partir de tools/pieces-standard.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="2.5 2.5 35 35" width="35" height="35" version="1.1">
  ${abre}
    ${limpar(corpo.trim())}
  </g>
</svg>
`;
  fs.writeFileSync(path.join(destino, `${id}.svg`), svg);
  console.log(`pecas/${id}.svg  ${svg.length} bytes`);
}
console.log(`\n${nomes.length} peças escritas em ${path.relative(raiz, destino)}`);
