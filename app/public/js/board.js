/** Componente de tabuleiro (DOM + SVG de setas). Sem dependência de engine. */

const GLIFOS = { k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟' };
const COLUNAS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

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
    this._montar();
    this._eventos();
  }

  _montar() {
    this.raiz.innerHTML = '';
    const ordem = this._ordem();
    for (const sq of ordem) {
      const arquivo = COLUNAS.indexOf(sq[0]);
      const linha = Number(sq[1]);
      const clara = (arquivo + linha) % 2 === 1;
      const casa = document.createElement('div');
      casa.className = `casa ${clara ? 'clara' : 'escura'}`;
      casa.dataset.sq = sq;
      const mostrarCoord = this.orientacao === 'w' ? linha === 1 : linha === 8;
      if (mostrarCoord) {
        casa.classList.add('coord');
        casa.dataset.coord = sq[0];
      }
      this.raiz.appendChild(casa);
    }
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
  }

  _eventos() {
    this.raiz.addEventListener('click', (ev) => {
      const casa = ev.target.closest('.casa');
      if (!casa || !this.interativo) return;
      this.onCasa?.(casa.dataset.sq);
    });
    this.raiz.addEventListener('dragstart', (ev) => {
      if (!this.interativo) return;
      const casa = ev.target.closest('.casa');
      if (!casa) return;
      ev.dataTransfer.setData('text/plain', casa.dataset.sq);
      this.onCasa?.(casa.dataset.sq, 'arraste');
    });
    this.raiz.addEventListener('dragover', (ev) => {
      if (this.interativo) ev.preventDefault();
    });
    this.raiz.addEventListener('drop', (ev) => {
      if (!this.interativo) return;
      ev.preventDefault();
      const origem = ev.dataTransfer.getData('text/plain');
      const casa = ev.target.closest('.casa');
      if (origem && casa && this._destinoValido(casa.dataset.sq)) {
        this.onCasa?.(casa.dataset.sq, 'solta', origem);
      }
    });
  }

  _destinoValido(sq) {
    return Boolean(this.destinos?.[sq]);
  }

  /** Desenha a posição a partir do FEN. */
  render(fen) {
    this.fen = fen;
    if (!fen) {
      for (const c of this.raiz.children) c.innerHTML = '';
      return;
    }
    const tabuleiro = fenParaMatriz(fen);
    for (const casa of this.raiz.children) {
      const sq = casa.dataset.sq;
      const peca = tabuleiro[sq];
      casa.innerHTML = '';
      if (peca) {
        const span = document.createElement('span');
        span.className = `peca ${peca.color === 'w' ? 'branca' : 'preta'}`;
        span.textContent = GLIFOS[peca.type];
        span.draggable = this.interativo;
        casa.appendChild(span);
      }
      casa.classList.toggle('ultimo-lance', Boolean(this.ultimo && (sq === this.ultimo.from || sq === this.ultimo.to)));
      casa.classList.toggle('em-xeque', sq === this.emXeque);
      casa.classList.toggle('origem-dica', sq === this.dicaOrigem);
      casa.classList.toggle('selecionada', sq === this.selecionada);
      const destino = this.destinos?.[sq];
      casa.classList.toggle('destino', Boolean(destino));
      casa.classList.toggle('captura', Boolean(destino && (destino.captura || peca)));
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

  /** setas: [{ de, para, cor }] em casas ('e2'), cor = 'verde' | 'vermelha' */
  setas(lista = []) {
    this.svg.innerHTML = '';
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const cores = { verde: '#81b64c', vermelha: '#fa412d', azul: '#5b8bd0' };
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
