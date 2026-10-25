/**
 * Componente de tabuleiro: 64 casas em DOM, peças em SVG e setas de dica.
 *
 * Entrada do usuário (o que importa para o app funcionar no celular):
 *  - toque  → seleciona a peça; toque no destino → lance (clique/clique);
 *  - mouse  → arrastar e soltar, além de clique/clique.
 *
 * O alvo é sempre resolvido pela **geometria** da casa (divisão do retângulo do
 * tabuleiro em 8×8), com o `event.target` só como atalho. Assim, se algum
 * elemento (peça, marcador de destino, seta) estiver por cima, o lance continua
 * funcionando — foi exatamente esse tipo de sobreposição que travou a primeira
 * versão publicada.
 */

const COLUNAS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
const NOME_PECA = {
  k: 'rei', q: 'dama', r: 'torre', b: 'bispo', n: 'cavalo', p: 'peão',
};

export class Tabuleiro {
  constructor(raiz, svg, { orientacao = 'w', interativo = false, onCasa = null } = {}) {
    this.raiz = raiz;
    this.svg = svg;
    this.orientacao = orientacao;
    this.interativo = interativo;
    this.onCasa = onCasa;
    this.fen = null;
    this.selecionada = null;
    this.destinos = {};
    this.ultimo = null;
    this.emXeque = null;
    this.dicaOrigem = null;
    this._arraste = null;
    this._suprimirClique = false;
    this._montar();
    this._eventos();
  }

  // ------------------------------------------------------------- montagem

  _montar() {
    this.raiz.innerHTML = '';
    for (const sq of this._ordem()) {
      const arquivo = COLUNAS.indexOf(sq[0]);
      const linha = Number(sq[1]);
      const clara = (arquivo + linha) % 2 === 1;
      const casa = document.createElement('div');
      casa.className = `casa ${clara ? 'clara' : 'escura'}`;
      casa.dataset.sq = sq;
      // coordenadas nas bordas: colunas embaixo, linhas à esquerda
      const coluna = this.orientacao === 'w' ? linha === 1 : linha === 8;
      const fileira = this.orientacao === 'w' ? sq[0] === 'a' : sq[0] === 'h';
      if (coluna) { casa.classList.add('coord'); casa.dataset.file = sq[0]; }
      if (fileira) { casa.classList.add('coord-linha'); casa.dataset.rank = sq[1]; }
      this.raiz.appendChild(casa);
    }
    this.raiz.style.cursor = this.interativo ? 'pointer' : 'default';
  }

  _ordem() {
    const linhas = this.orientacao === 'w' ? [8, 7, 6, 5, 4, 3, 2, 1] : [1, 2, 3, 4, 5, 6, 7, 8];
    const colunas = this.orientacao === 'w' ? COLUNAS : [...COLUNAS].reverse();
    const out = [];
    for (const l of linhas) for (const c of colunas) out.push(`${c}${l}`);
    return out;
  }

  setOrientacao(cor) {
    this.orientacao = cor;
    this._montar();
    this.render(this.fen);
  }

  setInterativo(v) {
    this.interativo = Boolean(v);
    this.raiz.style.cursor = this.interativo ? 'pointer' : 'default';
    if (!this.interativo) this.limparSelecao();
  }

  // -------------------------------------------------------------- entrada

  _eventos() {
    this.raiz.addEventListener('click', (ev) => {
      if (!this.interativo) return;
      if (this._suprimirClique) {         // o clique veio do fim de um arraste
        this._suprimirClique = false;
        return;
      }
      const sq = this._casaDoEvento(ev);
      if (sq) this.onCasa?.(sq);
    });

    // arrastar com mouse (no toque, o clique/clique é mais previsível e não
    // rouba a rolagem da página)
    this.raiz.addEventListener('pointerdown', (ev) => {
      if (!this.interativo || ev.pointerType === 'touch') return;
      if (ev.button !== 0) return;
      const sq = this._casaDoEvento(ev);
      if (!sq) return;
      this._arraste = { origem: sq, x: ev.clientX, y: ev.clientY, ativo: false, fantasma: null };
    });

    this.raiz.addEventListener('pointermove', (ev) => {
      const a = this._arraste;
      if (!a) return;
      const dist = Math.hypot(ev.clientX - a.x, ev.clientY - a.y);
      if (!a.ativo && dist < 6) return;
      if (!a.ativo) {
        const peca = this._pecaEm(a.origem);
        if (!peca) { this._arraste = null; return; }
        a.ativo = true;
        a.fantasma = document.createElement('img');
        a.fantasma.className = 'peca-arrastando';
        a.fantasma.src = peca.src;
        a.fantasma.alt = '';
        document.body.appendChild(a.fantasma);
        this.raiz.style.cursor = 'grabbing';
      }
      a.fantasma.style.left = `${ev.clientX}px`;
      a.fantasma.style.top = `${ev.clientY}px`;
      if (ev.cancelable) ev.preventDefault();
    });

    const soltar = (ev) => {
      const a = this._arraste;
      this._arraste = null;
      this.raiz.style.cursor = this.interativo ? 'pointer' : 'default';
      if (!a) return;
      if (!a.ativo) return;                    // foi só um clique
      a.fantasma?.remove();
      this._suprimirClique = true;
      setTimeout(() => { this._suprimirClique = false; }, 400);
      const destino = this._casaDoPonto(ev.clientX, ev.clientY);
      if (destino && destino !== a.origem && this._destinoValido(destino)) {
        this.onCasa?.(destino, 'solta', a.origem);
      }
    };
    this.raiz.addEventListener('pointerup', soltar);
    this.raiz.addEventListener('pointercancel', () => {
      this._arraste?.fantasma?.remove();
      this._arraste = null;
      this.raiz.style.cursor = this.interativo ? 'pointer' : 'default';
    });
  }

  _pecaEm(sq) {
    return this.raiz.querySelector(`.casa[data-sq="${sq}"] .peca`);
  }

  /** Casa a partir do elemento alvo (rápido) ou da posição do ponteiro. */
  _casaDoEvento(ev) {
    const alvo = ev.target?.closest?.('.casa');
    if (alvo?.dataset?.sq) return alvo.dataset.sq;
    return this._casaDoPonto(ev.clientX, ev.clientY);
  }

  /** Casa a partir de coordenadas de tela; null se o tabuleiro não tem layout. */
  _casaDoPonto(x, y) {
    if (typeof x !== 'number' || typeof y !== 'number') return null;
    const r = this.raiz.getBoundingClientRect?.();
    if (!r || !r.width || !r.height) return null;
    const col = Math.floor(((x - r.left) / r.width) * 8);
    const lin = Math.floor(((y - r.top) / r.height) * 8);
    if (col < 0 || col > 7 || lin < 0 || lin > 7) return null;
    const arquivo = this.orientacao === 'w' ? col : 7 - col;
    const fileira = this.orientacao === 'w' ? 8 - lin : lin + 1;
    return `${COLUNAS[arquivo]}${fileira}`;
  }

  _destinoValido(sq) {
    return Boolean(this.destinos?.[sq]);
  }

  // --------------------------------------------------------------- desenho

  /** Desenha a posição a partir do FEN. */
  render(fen) {
    this.fen = fen;
    const tabuleiro = fen ? fenParaMatriz(fen) : {};
    for (const casa of this.raiz.children) {
      const sq = casa.dataset.sq;
      casa.textContent = '';
      const peca = tabuleiro[sq];
      if (peca) {
        const img = document.createElement('img');
        img.className = `peca ${peca.color === 'w' ? 'branca' : 'preta'}`;
        img.src = `pecas/${peca.color}${peca.type}.svg`;
        img.alt = '';
        img.draggable = false;
        img.setAttribute('aria-hidden', 'true');
        casa.appendChild(img);
      }
      const destino = this.destinos?.[sq];
      if (destino) {
        const marca = document.createElement('i');
        marca.className = 'alvo';
        casa.appendChild(marca);
      }
      casa.classList.toggle('ultimo-lance', Boolean(this.ultimo && (sq === this.ultimo.from || sq === this.ultimo.to)));
      casa.classList.toggle('em-xeque', sq === this.emXeque);
      casa.classList.toggle('origem-dica', sq === this.dicaOrigem);
      casa.classList.toggle('selecionada', sq === this.selecionada);
      casa.classList.toggle('destino', Boolean(destino));
      casa.classList.toggle('captura', Boolean(destino && (destino.captura || peca)));
      if (peca) {
        casa.setAttribute('aria-label', `${NOME_PECA[peca.type]} ${peca.color === 'w' ? 'branco' : 'preto'} em ${sq}`);
      } else {
        casa.removeAttribute('aria-label');
      }
    }
  }

  selecionar(sq, destinos = {}) {
    this.selecionada = sq;
    this.destinos = destinos;
    this.render(this.fen);
  }

  limparSelecao() {
    this.selecionada = null;
    this.destinos = {};
    this.render(this.fen);
  }

  marcarUltimo(from, to) {
    this.ultimo = from && to ? { from, to } : null;
    this.render(this.fen);
  }

  marcarXeque(sq) {
    this.emXeque = sq;
    this.render(this.fen);
  }

  marcarDica(sq) {
    this.dicaOrigem = sq;
    this.render(this.fen);
  }

  /** setas: [{ de, para, cor }] em casas ('e2'), cor = 'verde' | 'vermelha' | 'azul' */
  setas(lista = []) {
    this.svg.innerHTML = '';
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const cores = { verde: '#81b64c', vermelha: '#e0403c', azul: '#5b8bd0' };
    for (const [nome, cor] of Object.entries(cores)) {
      const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
      marker.setAttribute('id', `ponta-${nome}`);
      marker.setAttribute('markerWidth', '4');
      marker.setAttribute('markerHeight', '4');
      marker.setAttribute('refX', '2.4');
      marker.setAttribute('refY', '2');
      marker.setAttribute('orient', 'auto');
      const poli = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      poli.setAttribute('points', '0,0 4,2 0,4');
      poli.setAttribute('fill', cor);
      marker.appendChild(poli);
      defs.appendChild(marker);
    }
    this.svg.appendChild(defs);

    for (const seta of lista) {
      const { de, para, cor = 'verde' } = seta;
      const [x1, y1] = this._centro(de);
      const [x2, y2] = this._centro(para);
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', x1); line.setAttribute('y1', y1);
      line.setAttribute('x2', x2); line.setAttribute('y2', y2);
      line.setAttribute('stroke', cores[cor] || cor);
      line.setAttribute('stroke-width', '0.16');
      line.setAttribute('stroke-linecap', 'round');
      line.setAttribute('opacity', '0.92');
      line.setAttribute('marker-end', `url(#ponta-${cor in cores ? cor : 'verde'})`);
      this.svg.appendChild(line);
    }
  }

  _centro(sq) {
    const arquivo = COLUNAS.indexOf(sq[0]);
    const linha = Number(sq[1]);
    const x = this.orientacao === 'w' ? arquivo + 0.5 : 8 - arquivo - 0.5;
    const y = this.orientacao === 'w' ? 8 - linha + 0.5 : linha - 0.5;
    return [x, y];
  }
}

/** FEN -> { e4: {type:'p', color:'w'}, ... } */
export function fenParaMatriz(fen) {
  const out = {};
  const [posicao] = fen.split(' ');
  const linhas = posicao.split('/');
  linhas.forEach((linha, i) => {
    let arquivo = 0;
    const numero = 8 - i;
    for (const ch of linha) {
      if (/\d/.test(ch)) {
        arquivo += Number(ch);
      } else {
        const color = ch === ch.toUpperCase() ? 'w' : 'b';
        out[`${COLUNAS[arquivo]}${numero}`] = { type: ch.toLowerCase(), color };
        arquivo++;
      }
    }
  });
  return out;
}
