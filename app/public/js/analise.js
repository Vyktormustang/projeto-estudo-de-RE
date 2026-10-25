/** Modo "Analisar": revisão completa com classificação e explicação de cada lance. */

import { Chess } from '../vendor/chess.js';
import { PoolAnalise, tamanhoDoPool, perfilDeAnalise, estimarSegundos } from './engine.js';
import { Tabuleiro } from './board.js';
import { toast, el } from './util.js';
import { importarChessCom } from './armazenamento.js';
import {
  buildReview, CLASS_INFO, expectedPointsWhite, formatEval, pvToSan, describeMove,
} from './review.js';

const ORDEM_CLASSES = ['brilliant', 'great', 'best', 'excellent', 'good', 'book', 'inaccuracy', 'mistake', 'miss', 'blunder'];

export class ModoAnalise {
  constructor() {
    this.tabuleiro = new Tabuleiro(
      document.getElementById('tab-analise'),
      document.getElementById('setas-analise'),
      { orientacao: 'w', interativo: false },
    );
    this.review = null;
    this.indice = -1; // -1 = posição inicial; i = depois do lance i
    this.pgn = '';
    this.cancelar = false;
    this.revisando = false;
    this._ligar();
    this.tabuleiro.render('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
    this._explicarModoAnalise();
  }

  _ligar() {
    document.getElementById('btn-revisar').addEventListener('click', () => this.revisar());
    document.getElementById('btn-exemplo').addEventListener('click', () => {
      document.getElementById('pgn').value = EXEMPLO;
      this.revisar();
    });
    document.getElementById('btn-importar').addEventListener('click', () => this.importarChessCom());
    document.getElementById('arquivo-pgn').addEventListener('change', (ev) => this._lerArquivo(ev));
    document.getElementById('nav-inicio').addEventListener('click', () => this.irPara(-1));
    document.getElementById('nav-voltar').addEventListener('click', () => this.irPara(this.indice - 1));
    document.getElementById('nav-avancar').addEventListener('click', () => this.irPara(this.indice + 1));
    document.getElementById('nav-fim').addEventListener('click', () => this.irPara(this.review ? this.review.moves.length - 1 : -1));
    document.getElementById('nav-girar').addEventListener('click', () => {
      this.tabuleiro.setOrientacao(this.tabuleiro.orientacao === 'w' ? 'b' : 'w');
    });
    document.addEventListener('keydown', (ev) => {
      if (document.getElementById('view-analisar').hidden) return;
      if (ev.target?.matches?.('input, textarea, select')) return;
      if (ev.key === 'ArrowLeft') { this.irPara(this.indice - 1); ev.preventDefault(); }
      if (ev.key === 'ArrowRight') { this.irPara(this.indice + 1); ev.preventDefault(); }
      if (ev.key === 'Home') { this.irPara(-1); ev.preventDefault(); }
      if (ev.key === 'End' && this.review) { this.irPara(this.review.moves.length - 1); ev.preventDefault(); }
    });
    window.addEventListener('xadrez:analisar', (ev) => {
      const { pgn } = ev.detail;
      document.getElementById('pgn').value = pgn;
      document.querySelector('.aba[data-aba="analisar"]')?.click();
      this.revisar();
    });
    document.getElementById('pgn').addEventListener('dragover', (ev) => ev.preventDefault());
    document.getElementById('pgn').addEventListener('drop', async (ev) => {
      ev.preventDefault();
      const arquivo = ev.dataTransfer.files?.[0];
      if (!arquivo) return;
      document.getElementById('pgn').value = await arquivo.text();
      toast(`PGN carregado: ${arquivo.name}`);
    });
  }

  async _lerArquivo(ev) {
    const arquivo = ev.target.files?.[0];
    if (!arquivo) return;
    const texto = await arquivo.text();
    ev.target.value = '';
    window.dispatchEvent(new CustomEvent('xadrez:analisar', { detail: { pgn: texto } }));
    toast(`PGN carregado: ${arquivo.name}`);
  }

  async importarChessCom() {
    const usuario = document.getElementById('user-chesscom').value.trim();
    if (!usuario) return toast('Digite o usuário do chess.com.', 'erro');
    const caixa = document.getElementById('lista-chesscom');
    caixa.hidden = false;
    caixa.innerHTML = 'buscando partidas…';
    try {
      const dados = await importarChessCom(usuario, 15);
      if (!dados.jogos?.length) {
        caixa.innerHTML = 'Nenhuma partida encontrada.';
        return;
      }
      caixa.innerHTML = '';
      for (const jogo of dados.jogos) {
        const rotulo = `${jogo.brancas} × ${jogo.pretas} — ${jogo.classe || ''} ${jogo.resultado || ''}`;
        const b = el('button', { title: 'carregar este PGN' }, rotulo);
        b.addEventListener('click', () => {
          document.getElementById('pgn').value = jogo.pgn;
          caixa.hidden = true;
          this.revisar();
        });
        caixa.appendChild(b);
      }
    } catch (err) {
      caixa.innerHTML = '';
      caixa.appendChild(el('p', { class: 'dica' },
        `Não deu para importar agora (${err.message}). Cole o PGN exportado do chess.com.`));
    }
  }

  _explicarModoAnalise() {
    const dica = document.getElementById('dica-analise');
    if (!dica) return;
    const nucleos = tamanhoDoPool();
    dica.textContent = nucleos > 1
      ? `Analisa ${nucleos} posições ao mesmo tempo (${nucleos} núcleos) e 2 linhas por posição — `
        + 'é o que deixa a revisão várias vezes mais rápida.'
      : 'Analisa uma posição por vez (o aparelho informou 1 núcleo livre). 2 linhas por posição.';
  }

  async revisar() {
    if (this.revisando) {
      this.cancelar = true;
      return;
    }
    const pgn = document.getElementById('pgn').value.trim();
    if (!pgn) return toast('Cole um PGN (ou use "Carregar exemplo").', 'erro');

    let chess;
    try {
      chess = new Chess();
      chess.loadPgn(pgn);
      if (!chess.history().length) throw new Error('PGN sem lances');
    } catch (err) {
      return toast(`PGN inválido: ${err.message}`, 'erro');
    }

    this.pgn = pgn;
    this.revisando = true;
    this.cancelar = false;
    const botao = document.getElementById('btn-revisar');
    botao.textContent = 'Cancelar';
    botao.classList.add('secundario');

    const escolha = document.getElementById('profundidade').value;
    const historico = chess.history({ verbose: true });
    const inicio = chess.getHeaders().FEN || historico[0].before;
    const fens = [inicio, ...historico.map((m) => m.after)];

    // análise em paralelo: um Stockfish por núcleo livre, orçamento de tempo
    // por posição (o MultiPV 3 custava ~5x mais que 2 na mesma profundidade)
    const workers = tamanhoDoPool();
    const perfil = perfilDeAnalise(escolha, fens.length, workers);
    this.perfil = perfil;
    this.pool ??= new PoolAnalise({ tamanho: workers });
    const inicioMs = Date.now();
    this._progresso(0, fens.length,
      `preparando ${perfil.workers} motor(es) · ~${estimarSegundos(fens.length, perfil)} s`);

    try {
      const respostas = await this.pool.analisarTodas(
        fens,
        () => ({ depth: perfil.depth, movetime: perfil.movetime, multipv: 2 }),
        {
          cancelado: () => this.cancelar,
          aoProgredir: (feitas, total) => {
            const decorrido = (Date.now() - inicioMs) / 1000;
            const resta = feitas ? Math.max(0, (decorrido / feitas) * (total - feitas)) : 0;
            this._progresso(feitas, total,
              `${feitas} de ${total} · ~${Math.ceil(resta)} s restantes · ${perfil.workers} núcleo(s)`);
          },
        },
      );

      const posicoes = respostas.map((r, i) => ({
        fen: fens[i],
        turn: fens[i].split(' ')[1],
        lines: r.lines || [],
      }));

      const review = buildReview({ pgn, positions: posicoes });
      review.segundos = Math.max(1, Math.round((Date.now() - inicioMs) / 1000));
      review.perfil = perfil;
      this.review = review;
      this._renderRelatorio();
      this.irPara(-1);
      this._mostrarGrafico();
      toast(`Revisão pronta em ${review.segundos} s: ${review.moves.length} lances analisados.`);
    } catch (err) {
      if (err.message === 'cancelado') toast('Revisão cancelada.');
      else toast(`Falha na revisão: ${err.message}`, 'erro');
    } finally {
      this.revisando = false;
      document.getElementById('progresso').hidden = true;
      botao.textContent = 'Revisar partida';
      botao.classList.remove('secundario');
    }
  }

  _progresso(feito, total, texto) {
    const caixa = document.getElementById('progresso');
    caixa.hidden = false;
    document.getElementById('progresso-barra').style.width = `${Math.round((feito / total) * 100)}%`;
    document.getElementById('progresso-texto').textContent = texto;
  }

  _renderRelatorio() {
    const r = this.review;
    document.getElementById('relatorio').hidden = false;
    document.getElementById('acc-brancas').textContent = r.accuracy.white != null ? `${r.accuracy.white}%` : '—';
    document.getElementById('acc-pretas').textContent = r.accuracy.black != null ? `${r.accuracy.black}%` : '—';

    // nomes/precisão nas linhas de jogador em volta do tabuleiro
    const nome = (chave, padrao) => (r.headers?.[chave] || padrao || '').trim();
    const escrever = (id, texto) => {
      const node = document.getElementById(id);
      if (node) node.textContent = texto;
    };
    escrever('nome-brancas', nome('White', 'Brancas'));
    escrever('nome-pretas', nome('Black', 'Pretas'));
    escrever('precisao-brancas', r.accuracy.white != null ? `${r.accuracy.white}% de precisão` : '');
    escrever('precisao-pretas', r.accuracy.black != null ? `${r.accuracy.black}% de precisão` : '');

    const classes = document.getElementById('contagem-classes');
    classes.innerHTML = '';
    for (const chave of ORDEM_CLASSES) {
      const n = r.counts[chave];
      if (!n) continue;
      const info = CLASS_INFO[chave];
      classes.appendChild(el('span', { class: 'chip-classe' },
        el('i', { style: `background:${info.color}` }), `${info.label} `, el('b', {}, String(n))));
    }

    document.getElementById('resumo-partida').textContent = r.summary.text;

    const info = document.getElementById('info-revisao');
    if (info) {
      info.textContent = r.perfil
        ? `${r.moves.length} lances · depth ${r.perfil.depth} · 2 linhas por posição · `
          + `${r.perfil.workers} núcleo(s) em paralelo · ${r.segundos} s`
        : '';
    }

    const lista = document.getElementById('lances-analise');
    lista.innerHTML = '';
    for (let i = 0; i < r.moves.length; i += 2) {
      const brancas = r.moves[i];
      const pretas = r.moves[i + 1];
      lista.appendChild(el('li', {}, el('span', { class: 'num' }, `${brancas.moveNumber}.`)));
      lista.appendChild(el('li', {}, this._botaoLance(brancas, i)));
      lista.appendChild(el('li', {}, pretas ? this._botaoLance(pretas, i + 1) : el('span', {})));
    }
  }

  _botaoLance(lance, indice) {
    const info = CLASS_INFO[lance.class];
    const b = el('button', { class: 'lance', dataset: { indice: String(indice) } },
      el('span', { class: 'classe', style: `background:${info.color}` }, info.short),
      lance.san,
    );
    b.addEventListener('click', () => this.irPara(indice));
    return b;
  }

  irPara(indice) {
    if (!this.review) return;
    const total = this.review.moves.length;
    const alvo = Math.max(-1, Math.min(total - 1, indice));
    this.indice = alvo;
    const fen = alvo < 0 ? this.review.initialFen : this.review.moves[alvo].fenAfter;
    this.tabuleiro.render(fen);
    const lance = alvo >= 0 ? this.review.moves[alvo] : null;
    this.tabuleiro.marcarUltimo(lance?.from, lance?.to);
    this.tabuleiro.marcarXeque(new Chess(fen).inCheck() ? this._casaDoRei(fen) : null);
    this.tabuleiro.setas(this._setasDoLance(alvo));
    document.getElementById('lance-atual').textContent = lance
      ? `${lance.moveNumber}${lance.color === 'w' ? '.' : '...'} ${lance.san}`
      : 'posição inicial';

    for (const b of document.querySelectorAll('#lances-analise .lance')) {
      b.classList.toggle('atual', Number(b.dataset.indice) === alvo);
    }
    document.querySelector('#lances-analise .lance.atual')?.scrollIntoView({ block: 'nearest' });

    const brancas = expectedPointsWhite(lance ? lance.evalAfterWhite : this.review.moves[0].evalBeforeWhite);
    this._barra(brancas);
    this._marcarGrafico(alvo);
    this._explicar(alvo);
  }

  _casaDoRei(fen) {
    const c = new Chess(fen);
    const cor = c.turn();
    for (const linha of c.board()) {
      for (const casa of linha) if (casa && casa.type === 'k' && casa.color === cor) return casa.square;
    }
    return null;
  }

  _setasDoLance(alvo) {
    if (alvo < 0) return [];
    const lance = this.review.moves[alvo];
    const setas = [{ de: lance.from, para: lance.to, cor: 'azul' }];
    const melhor = lance.linesBefore?.[0]?.pv?.[0];
    if (melhor && melhor !== lance.from + lance.to + (lance.promotion || '')) {
      setas.push({ de: melhor.slice(0, 2), para: melhor.slice(2, 4), cor: 'verde' });
    }
    return setas;
  }

  _barra(epBrancas) {
    const barra = document.querySelector('#aval-analise .preenchimento');
    if (barra) barra.style.height = `${Math.round((epBrancas ?? 0.5) * 100)}%`;
  }

  _explicar(alvo) {
    const caixa = document.getElementById('explicacao');
    caixa.innerHTML = '';
    if (alvo < 0) {
      caixa.appendChild(el('p', { class: 'dica' }, 'Posição inicial. Use ▶ ou clique num lance.'));
      return;
    }
    const lance = this.review.moves[alvo];
    const info = CLASS_INFO[lance.class];
    const explicacao = lance.explanation;

    caixa.appendChild(el('h4', {},
      `${lance.moveNumber}${lance.color === 'w' ? '.' : '...'} ${lance.san}`,
      el('span', { class: 'badge-classe', style: `background:${info.color}` }, info.label),
    ));
    caixa.appendChild(el('p', { class: 'texto' }, explicacao.text));

    const modoLeve = document.getElementById('modo-leve').checked;
    if (explicacao.tips?.length && !modoLeve) {
      const ul = el('ul', {});
      for (const dica of explicacao.tips) ul.appendChild(el('li', {}, `💡 ${dica}`));
      caixa.appendChild(ul);
    }

    const detalhes = [];
    detalhes.push(`Avaliação antes: ${formatEval(lance.evalBeforeWhite)} · depois: ${formatEval(lance.evalAfterWhite)}`);
    if (lance.explanation.bestSan && lance.explanation.bestSan !== lance.san) {
      detalhes.push(`Melhor lance: ${lance.explanation.bestSan}`);
    }
    caixa.appendChild(el('p', { class: 'dica' }, detalhes.join(' · ')));

    const linhas = modoLeve ? [] : (lance.linesBefore || []).slice(0, 3);
    if (linhas.length) {
      const bloco = el('div', { class: 'linhas-motor' });
      linhas.forEach((linha, i) => {
        const avalia = formatEval({ cp: linha.cp, mate: linha.mate });
        const san = pvToSan(lance.fenBefore, linha.pv, 5);
        bloco.appendChild(el('div', {},
          el('b', {}, i === 0 ? `★ ${avalia}` : avalia),
          el('span', {}, san.join(' ') || linha.pv.slice(0, 5).join(' ')),
        ));
      });
      caixa.appendChild(bloco);
    }

    if (this.review.summary?.worst?.some((m) => m.ply === lance.ply)) {
      caixa.appendChild(el('p', { class: 'dica' }, '⚠ Este está entre os piores momentos da partida.'));
    }
  }

  _mostrarGrafico() {
    const svg = document.getElementById('grafico-analise');
    const r = this.review;
    if (!r) return;
    const pontos = [];
    for (const lance of r.moves) {
      const ep = expectedPointsWhite(lance.evalBeforeWhite ?? { cp: 0 });
      pontos.push(ep);
    }
    pontos.push(expectedPointsWhite(r.moves.at(-1).evalAfterWhite ?? { cp: 0 }));

    const largura = 100;
    const altura = 40;
    const passo = pontos.length > 1 ? largura / (pontos.length - 1) : largura;
    const coords = pontos.map((ep, i) => [i * passo, altura - ep * altura]);
    const linha = coords.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');

    svg.innerHTML = '';
    const area = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    area.setAttribute('d', `${linha} L${largura},${altura} L0,${altura} Z`);
    area.setAttribute('fill', 'rgba(241,243,245,.13)');
    svg.appendChild(area);

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', linha);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', '#81b64c');
    path.setAttribute('stroke-width', '1.2');
    path.setAttribute('vector-effect', 'non-scaling-stroke');
    svg.appendChild(path);

    const meio = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    meio.setAttribute('x1', '0'); meio.setAttribute('x2', String(largura));
    meio.setAttribute('y1', String(altura / 2)); meio.setAttribute('y2', String(altura / 2));
    meio.setAttribute('stroke', 'rgba(255,255,255,.18)');
    meio.setAttribute('stroke-dasharray', '1 1');
    svg.appendChild(meio);

    const cursor = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    cursor.setAttribute('id', 'cursor-grafico');
    cursor.setAttribute('y1', '0'); cursor.setAttribute('y2', String(altura));
    cursor.setAttribute('stroke', '#f0b429');
    cursor.setAttribute('stroke-width', '1');
    svg.appendChild(cursor);

    svg.onclick = (ev) => {
      const rect = svg.getBoundingClientRect();
      const x = (ev.clientX - rect.left) / rect.width;
      const idx = Math.round(x * (pontos.length - 1)) - 1;
      this.irPara(idx);
    };
    svg.style.cursor = 'pointer';
  }

  _marcarGrafico(alvo) {
    const cursor = document.getElementById('cursor-grafico');
    if (!cursor || !this.review) return;
    const total = this.review.moves.length;
    const x = ((alvo + 1) / total) * 100;
    cursor.setAttribute('x1', String(Math.max(0, Math.min(100, x))));
    cursor.setAttribute('x2', String(Math.max(0, Math.min(100, x))));
  }
}

const EXEMPLO = `[Event "Opera Game (Paris, 1858)"]
[Site "Paris FRA"]
[Date "1858.??.??"]
[White "Paul Morphy"]
[Black "Duke Karl / Count Isouard"]
[Result "1-0"]

1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7
8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7
14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0`;
