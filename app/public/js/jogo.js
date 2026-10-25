/** Modo "Jogar": partida contra o Stockfish com assistências opcionais. */

import { Chess } from '../vendor/chess.js';
import { motor, motorAjuda } from './engine.js';
import { Tabuleiro } from './board.js';
import { toast, el, fmtTempo, nomeNivel } from './util.js';
import { salvarJogo } from './armazenamento.js';
import {
  expectedPointsWhite, toWhiteScore, classifyMove, explainMove, formatEval, CLASS_INFO,
} from './review.js';

const PECAS_PROMOCAO = [
  ['q', 'Dama'], ['r', 'Torre'], ['b', 'Bispo'], ['n', 'Cavalo'],
];

export class ModoJogo {
  constructor({ aoTerminar } = {}) {
    this.aoTerminar = aoTerminar;
    this.tabuleiro = new Tabuleiro(
      document.getElementById('tab-jogar'),
      document.getElementById('setas-jogar'),
      { orientacao: 'w', interativo: false, onCasa: (sq, tipo, origem) => this._aoClicar(sq, tipo, origem) },
    );
    this.chess = new Chess();
    this.config = { nivel: 1200, cor: 'w', tempo: { base: 0, inc: 0 }, assist: {} };
    this.humano = 'w';
    this.emAndamento = false;
    this.botPensando = false;
    this.relogios = { w: 0, b: 0 };
    this.resultado = null;
    this.analiseAntes = null;
    this._ligarBotoes();
    this._renderizarTudo();
  }

  _ligarBotoes() {
    document.getElementById('btn-comecar').addEventListener('click', () => {
      this.iniciar(this._lerConfig());
    });
    document.getElementById('btn-abandonar').addEventListener('click', () => this._encerrarVisual());
    document.getElementById('btn-novo-jogo')?.addEventListener('click', () => this._encerrarVisual());
    document.getElementById('btn-revanche')?.addEventListener('click', () => {
      this._esconderResultado();
      this.iniciar(this.config);
    });
    document.getElementById('btn-revisar-fim')?.addEventListener('click', () => {
      this._esconderResultado();
      this.aoTerminar?.(this.chess.pgn());
    });
    document.getElementById('btn-fechar-resultado')?.addEventListener('click', () => this._esconderResultado());
    document.getElementById('btn-girar')?.addEventListener('click', () => {
      this.tabuleiro.setOrientacao(this.tabuleiro.orientacao === 'w' ? 'b' : 'w');
      this._pintarJogadores();
    });
    document.getElementById('btn-dica').addEventListener('click', () => this.pedirDica());
    document.getElementById('btn-desfazer').addEventListener('click', () => this.desfazer());
    document.getElementById('btn-desistir').addEventListener('click', () => this.desistir());
    document.getElementById('btn-analisar-partida').addEventListener('click', () => {
      this.aoTerminar?.(this.chess.pgn());
    });

    const nivel = document.getElementById('nivel');
    const texto = document.getElementById('nivel-texto');
    const desc = document.getElementById('nivel-desc');
    const atualizar = () => {
      texto.textContent = nomeNivel(Number(nivel.value));
      desc.textContent = this._descricaoNivel(Number(nivel.value));
      for (const b of document.querySelectorAll('#presets-nivel button')) {
        b.classList.toggle('ativo', Number(b.dataset.nivel) === Number(nivel.value));
      }
    };
    nivel.addEventListener('input', atualizar);
    for (const b of document.querySelectorAll('#presets-nivel button')) {
      b.addEventListener('click', () => { nivel.value = b.dataset.nivel; atualizar(); });
    }
    atualizar();

    for (const grupo of ['cor-jogo', 'tempo-jogo']) {
      for (const b of document.querySelectorAll(`#${grupo} button`)) {
        b.addEventListener('click', () => {
          for (const outro of document.querySelectorAll(`#${grupo} button`)) outro.classList.remove('ativo');
          b.classList.add('ativo');
        });
      }
    }
  }

  _descricaoNivel(n) {
    if (n < 700) return 'erra de propósito com frequência: bom para aprender sem pressão.';
    if (n < 1100) return 'vê táticas simples, mas deixa passar combinações de dois lances.';
    if (n < 1500) return 'castiga peças penduradas e forma planos curtos.';
    if (n < 1900) return 'defende bem, calcula táticas e aproveita erros posicionais.';
    if (n < 2400) return 'força de clube forte: exige plano e precisão.';
    if (n < 2900) return 'nível de mestre: praticamente sem erros táticos.';
    return 'motor em força total — use para testar ideias, não para ganhar.';
  }

  _lerConfig() {
    const nivel = Number(document.getElementById('nivel').value);
    const corBt = document.querySelector('#cor-jogo button.ativo');
    let cor = corBt?.dataset.cor || 'w';
    if (cor === 'r') cor = Math.random() < 0.5 ? 'w' : 'b';
    const tempoBt = document.querySelector('#tempo-jogo button.ativo');
    const tempoStr = tempoBt?.dataset.tempo || '0';
    const [base, inc] = tempoStr === '0' ? [0, 0] : tempoStr.split('+').map(Number);
    return {
      nivel,
      cor,
      tempo: { base, inc },
      assist: {
        avaliacao: document.getElementById('ass-aval').checked,
        dica: document.getElementById('ass-dica').checked,
        desfazer: document.getElementById('ass-desfazer').checked,
        feedback: document.getElementById('ass-feedback').checked,
      },
    };
  }

  iniciar(config) {
    this.config = config;
    this.humano = config.cor;
    this.chess = new Chess();
    this.relogios = { w: config.tempo.base, b: config.tempo.base };
    this.resultado = null;
    this.analiseAntes = null;
    this.emAndamento = true;
    this.botPensando = false;
    this.tabuleiro.setOrientacao(this.humano);
    this.tabuleiro.setInterativo(true);
    this.tabuleiro.limparSelecao();
    this.tabuleiro.setas([]);
    this.tabuleiro.marcarUltimo(null, null);
    this.tabuleiro.marcarClasse(null);
    this._esconderResultado();
    document.getElementById('config-jogo').hidden = true;
    document.getElementById('jogo-ativo').hidden = false;
    document.getElementById('acoes-tabuleiro').hidden = false;
    document.getElementById('feedback-jogar').hidden = true;
    document.getElementById('titulo-jogo').textContent = `vs ${nomeNivel(config.nivel)}`;
    this._pintarJogadores();
    document.getElementById('btn-dica').disabled = !config.assist.dica;
    document.getElementById('btn-desfazer').disabled = !config.assist.desfazer;
    this._renderizarTudo();
    this._iniciarRelogio();
    if (this.humano === 'b') {
      setTimeout(() => this._vezDoBot().then(() => this._analisarParaAjuda()), 250);
    }
    else {
      this._definirStatus('sua vez', 'sua-vez');
      this._analisarParaAjuda();
    }
  }

  get base() {
    return this.config.tempo.base;
  }

  // ------------------------------------------------------------- relógio

  _iniciarRelogio() {
    clearInterval(this._timer);
    if (!this.base) {
      document.getElementById('relogio-w').textContent = '—';
      document.getElementById('relogio-b').textContent = '—';
      return;
    }
    this._ultimoTick = performance.now();
    this._timer = setInterval(() => {
      if (!this.emAndamento) return;
      const agora = performance.now();
      const dt = (agora - this._ultimoTick) / 1000;
      this._ultimoTick = agora;
      const vez = this.chess.turn();
      this.relogios[vez] = Math.max(0, this.relogios[vez] - dt);
      this._pintarRelogios();
      if (this.relogios[vez] <= 0) {
        this._finalizarPorTempo(vez);
      }
    }, 200);
    this._pintarRelogios();
  }

  _pintarRelogios() {
    const vez = this.chess.turn();
    const brancas = document.getElementById('relogio-w');
    const pretas = document.getElementById('relogio-b');
    if (!this.base) {
      brancas.textContent = '—';
      pretas.textContent = '—';
    } else {
      brancas.textContent = fmtTempo(this.relogios.w);
      pretas.textContent = fmtTempo(this.relogios.b);
    }
    document.getElementById('jogador-topo')?.classList.toggle('ativo', this.emAndamento && this.base > 0 && vez !== this.humano);
    document.getElementById('jogador-base')?.classList.toggle('ativo', this.emAndamento && this.base > 0 && vez === this.humano);
  }

  /** Quem está em cima/embaixo do tabuleiro e com que nome. */
  _pintarJogadores() {
    const humanoBrancas = this.humano === 'w';
    document.getElementById('nome-b').textContent = 'Stockfish';
    document.getElementById('rating-b').textContent = String(this.config.nivel);
    document.getElementById('nome-w').textContent = 'Você';
    const avatar = (id, cor) => {
      const caixa = document.getElementById(id);
      if (caixa) caixa.innerHTML = `<img src="pecas/${cor}k.svg" alt="">`;
    };
    avatar('avatar-topo', humanoBrancas ? 'b' : 'w');
    avatar('avatar-base', this.humano);
    this._pintarRelogios();
  }

  _finalizarPorTempo(quemEstourou) {
    const vencedor = quemEstourou === 'w' ? 'b' : 'w';
    const humanoVenceu = vencedor === this.humano;
    this._finalizar(
      humanoVenceu ? 'Você ganhou: o bot estourou o tempo.' : 'Você perdeu: seu tempo acabou.',
      humanoVenceu ? '1-0' : '0-1',
    );
  }

  // -------------------------------------------------------------- lances

  _aoClicar(sq, tipo, origem) {
    // arraste solto fora de um destino legal: desfaz a seleção
    if (tipo === 'cancelar') {
      this.selecionada = null;
      this.destinos = {};
      this.tabuleiro.limparSelecao();
      return;
    }
    if (!this.emAndamento || this.botPensando || this.chess.turn() !== this.humano) return;
    const peca = this.chess.get(sq);
    const origemEfetiva = tipo === 'solta' ? origem : null;

    if (origemEfetiva) {
      this._tentarLance(origemEfetiva, sq);
      return;
    }

    if (this.selecionada && sq !== this.selecionada && this.destinos[sq]) {
      this._tentarLance(this.selecionada, sq);
      return;
    }

    if (peca && peca.color === this.humano) {
      if (this.selecionada === sq) {
        this.selecionada = null;
        this.destinos = {};
        this.tabuleiro.limparSelecao();
        return;
      }
      this.selecionada = sq;
      this.destinos = {};
      for (const mv of this.chess.moves({ square: sq, verbose: true })) {
        this.destinos[mv.to] = { captura: Boolean(mv.captured) || mv.flags.includes('e') };
      }
      this.tabuleiro.selecionar(sq, this.destinos);
      return;
    }
    this.selecionada = null;
    this.destinos = {};
    this.tabuleiro.limparSelecao();
  }

  _tentarLance(de, para) {
    const peca = this.chess.get(de);
    if (!peca) return;
    const precisaPromover = peca.type === 'p' && (para[1] === '8' || para[1] === '1');
    if (precisaPromover) {
      this._pedirPromocao(de, para);
      return;
    }
    this._executarLance(de, para, null);
  }

  _pedirPromocao(de, para) {
    const caixa = document.getElementById('promo-jogar');
    caixa.innerHTML = '';
    caixa.hidden = false;
    for (const [tipo, nome] of PECAS_PROMOCAO) {
      const b = el('button', { title: `promover a ${nome}` });
      b.appendChild(el('img', {
        src: `pecas/${this.humano}${tipo}.svg`, alt: nome, draggable: 'false',
      }));
      b.addEventListener('click', () => {
        caixa.hidden = true;
        this._executarLance(de, para, tipo);
      });
      caixa.appendChild(b);
    }
    const cancelar = el('button', { class: 'cancelar', title: 'cancelar' }, '✕');
    cancelar.addEventListener('click', () => { caixa.hidden = true; });
    caixa.appendChild(cancelar);
  }

  _executarLance(de, para, promocao) {
    let mv;
    try {
      mv = this.chess.move({ from: de, to: para, promotion: promocao || 'q' });
    } catch {
      this.tabuleiro.limparSelecao();
      return;
    }
    this.selecionada = null;
    this.destinos = {};
    this.tabuleiro.limparSelecao();
    this.tabuleiro.setas([]);
    this.tabuleiro.marcarDica(null);
    if (this.base) this.relogios[this.humano] += this.config.tempo.inc;
    this._posLance(mv);
    if (this._checarFim()) return;

    const semFeedback = !this.config.assist.feedback;
    this._vezDoBot({ semFeedback }).then(() => {
      if (this.emAndamento && this.chess.turn() === this.humano) this._analisarParaAjuda();
    });
  }

  _posLance(mv) {
    this.tabuleiro.marcarUltimo(mv.from, mv.to);
    this.tabuleiro.render(this.chess.fen());
    this.tabuleiro.marcarXeque(this.chess.inCheck() ? this._casaDoRei(this.chess.turn()) : null);
    this._pintarRelogios();
    this._renderizarLances();
  }

  _casaDoRei(cor) {
    for (const linha of this.chess.board()) {
      for (const casa of linha) {
        if (casa && casa.type === 'k' && casa.color === cor) return casa.square;
      }
    }
    return null;
  }

  async _vezDoBot({ semFeedback = false } = {}) {
    if (!this.emAndamento) return;
    this.botPensando = true;
    this.tabuleiro.setInterativo(false);
    this._definirStatus('bot pensando…', 'pensando');
    const fen = this.chess.fen();
    const antes = this.analiseAntes;
    let resposta;
    try {
      resposta = await motor.jogar({ fen, nivel: this.config.nivel });
    } catch (err) {
      this.botPensando = false;
      this.tabuleiro.setInterativo(true);
      this._definirStatus('erro no motor', 'fim');
      toast(`Motor falhou: ${err.message}`, 'erro');
      return;
    }
    if (!this.emAndamento) return;
    const lance = resposta.best;
    if (!lance) {
      this.botPensando = false;
      return;
    }
    let mv;
    try {
      mv = this.chess.move({ from: lance.slice(0, 2), to: lance.slice(2, 4), promotion: lance[4] || 'q' });
    } catch {
      this.botPensando = false;
      return;
    }
    if (this.base) this.relogios[mv.color] += this.config.tempo.inc;
    this._posLance(mv);
    this.botPensando = false;
    this.tabuleiro.setInterativo(true);

    // barra de avaliação + feedback do seu último lance
    this._atualizarAvaliacao(resposta.lines, mv.color);
    if (!semFeedback && antes) this._mostrarFeedback(antes, resposta, mv);

    if (this._checarFim()) return;
    this._definirStatus('sua vez', 'sua-vez');
  }

  _atualizarAvaliacao(lines, corDoLance) {
    const linha = lines?.[0];
    if (!linha || !this.config.assist.avaliacao) return;
    const brancas = expectedPointsWhite(toWhiteScore({ cp: linha.cp, mate: linha.mate }, corDoLance));
    this._pintarBarra('aval-jogar', brancas);
  }

  _pintarBarra(id, epBrancas) {
    const barra = document.querySelector(`#${id} .preenchimento`);
    if (barra) barra.style.height = `${Math.round(epBrancas * 100)}%`;
  }

  _mostrarFeedback(antes, resposta, lanceBot) {
    const linhaAntes = antes.lines?.[0];
    const linhaDepois = resposta.lines?.[0];
    if (!linhaAntes || !linhaDepois) return;
    const eu = this.humano;
    const epAntesBrancas = expectedPointsWhite(toWhiteScore({ cp: linhaAntes.cp, mate: linhaAntes.mate }, eu));
    const epDepoisBrancas = expectedPointsWhite(toWhiteScore({ cp: linhaDepois.cp, mate: linhaDepois.mate }, lanceBot.color));
    const epAntes = eu === 'w' ? epAntesBrancas : 1 - epAntesBrancas;
    const epDepois = eu === 'w' ? epDepoisBrancas : 1 - epDepoisBrancas;
    const loss = Math.max(0, epAntes - epDepois);

    const registro = this.chess.history({ verbose: true });
    const meu = registro[registro.length - 2] || registro[registro.length - 1];
    const bestSan = antes.lines?.[0]?.pv?.[0]
      ? (() => {
        const c = new Chess(meu.before);
        const u = antes.lines[0].pv[0];
        try { return c.move({ from: u.slice(0, 2), to: u.slice(2, 4), promotion: u[4] || undefined }).san; } catch { return null; }
      })()
      : null;
    const isBest = bestSan === meu.san;

    const altGap = (() => {
      if (!antes.lines || antes.lines.length < 2) return 0;
      const b = expectedPointsWhite(toWhiteScore({ cp: antes.lines[0].cp, mate: antes.lines[0].mate }, meu.color));
      const s = expectedPointsWhite(toWhiteScore({ cp: antes.lines[1].cp, mate: antes.lines[1].mate }, meu.color));
      return Math.max(0, b - s);
    })();

    const classe = classifyMove({
      loss, isBest, altGap, sacrifice: false, epBefore: epAntes, epAfter: epDepois,
      ply: 0, bookish: false, deliversMate: meu.san.includes('#'),
    });
    const explicacao = explainMove(
      {
        san: meu.san,
        color: eu,
        fenBefore: meu.before,
        fenAfter: meu.after,
        class: classe,
        loss,
        evalBeforeWhite: toWhiteScore({ cp: linhaAntes.cp, mate: linhaAntes.mate }, eu),
        evalAfterWhite: toWhiteScore({ cp: linhaDepois.cp, mate: linhaDepois.mate }, lanceBot.color),
      },
      { linesBefore: antes.lines, linesAfter: resposta.lines },
    );
    const info = CLASS_INFO[classe];
    this.tabuleiro.marcarClasse({
      casa: meu.to, simbolo: info.short, cor: info.color, rotulo: `${info.label} — ${meu.san}`,
    });
    const caixa = document.getElementById('feedback-jogar');
    caixa.hidden = false;
    caixa.className = `feedback ${['inaccuracy', 'mistake', 'blunder', 'miss'].includes(classe) ? 'ruim' : ''}`;
    caixa.innerHTML = '';
    const titulo = el('b', {}, `${meu.san} — ${info.label}`);
    if (info.color) titulo.style.color = info.color;
    caixa.appendChild(titulo);
    caixa.appendChild(el('span', {}, explicacao.text));
    if (explicacao.tips.length) {
      caixa.appendChild(el('span', { class: 'dica', style: 'display:block;margin-top:.3rem' }, `💡 ${explicacao.tips[0]}`));
    }
    if (this.config.assist.avaliacao) this._pintarBarra('aval-jogar', epDepoisBrancas);
  }

  async _analisarParaAjuda() {
    // sem barra de avaliação e sem feedback não há para que analisar
    if (!this.config.assist.avaliacao && !this.config.assist.feedback) return;
    const fen = this.chess.fen();
    try {
      // motor separado do bot: a análise da minha vez não atrasa mais o lance dele
      const resposta = await motorAjuda.analisar({ fen, depth: 10, multipv: 2 });
      if (this.chess.fen() === fen) {
        this.analiseAntes = resposta;
        if (this.config.assist.avaliacao) {
          const ep = expectedPointsWhite(toWhiteScore({ cp: resposta.lines[0]?.cp, mate: resposta.lines[0]?.mate }, this.chess.turn()));
          this._pintarBarra('aval-jogar', ep);
        }
      }
    } catch { /* silencioso: assistência é opcional */ }
  }

  async pedirDica() {
    if (!this.emAndamento || this.botPensando || this.chess.turn() !== this.humano) return;
    const fen = this.chess.fen();
    const caixa = document.getElementById('feedback-jogar');
    caixa.hidden = false;
    caixa.className = 'feedback';
    caixa.textContent = 'analisando a melhor continuação…';
    try {
      const { lines } = await motorAjuda.analisar({ fen, depth: 13, movetime: 1500, multipv: 2 });
      if (this.chess.fen() !== fen) return;
      const melhor = lines[0];
      if (!melhor?.pv?.length) return;
      const de = melhor.pv[0].slice(0, 2);
      const para = melhor.pv[0].slice(2, 4);
      const san = (() => {
        const c = new Chess(fen);
        try { return c.move({ from: de, to: para, promotion: melhor.pv[0][4] || undefined }).san; } catch { return melhor.pv[0]; }
      })();
      this.tabuleiro.setas([{ de, para, cor: 'verde' }]);
      this.tabuleiro.marcarDica(de);
      caixa.innerHTML = '';
      caixa.appendChild(el('b', {}, `Sugestão: ${san}`));
      caixa.appendChild(el('span', {}, `Avaliação ${formatEval(toWhiteScore({ cp: melhor.cp, mate: melhor.mate }, this.chess.turn()))}. `
        + `Continuação: ${melhor.pv.slice(0, 4).join(' ')}`));
    } catch (err) {
      caixa.textContent = `Não consegui calcular a dica: ${err.message}`;
    }
  }

  desfazer() {
    if (!this.emAndamento || this.botPensando) return;
    if (!this.config.assist.desfazer) return;
    if (this.chess.history().length < 1) return;
    // volta até ser de novo a vez do humano, desfazendo também o lance do bot
    this.chess.undo();
    if (this.chess.turn() !== this.humano && this.chess.history().length) this.chess.undo();
    if (this.chess.turn() !== this.humano && this.chess.history().length) this.chess.undo();
    this.tabuleiro.setas([]);
    this.tabuleiro.marcarDica(null);
    const ultimo = this.chess.history({ verbose: true }).at(-1);
    this.tabuleiro.marcarUltimo(ultimo?.from, ultimo?.to);
    this.tabuleiro.marcarClasse(null);
    this.tabuleiro.render(this.chess.fen());
    this.tabuleiro.limparSelecao();
    document.getElementById('feedback-jogar').hidden = true;
    this._renderizarLances();
    this._definirStatus('sua vez', 'sua-vez');
    this._analisarParaAjuda();
  }

  desistir() {
    if (!this.emAndamento) return;
    const humano = this.humano === 'w' ? 'Brancas' : 'Pretas';
    this._finalizar(`Você desistiu (${humano}). O bot venceu.`, this.humano === 'w' ? '0-1' : '1-0');
  }

  _checarFim() {
    if (!this.chess.isGameOver()) return false;
    let texto;
    let resultado = '*';
    if (this.chess.isCheckmate()) {
      const vencedor = this.chess.turn() === 'w' ? 'b' : 'w';
      const euGanhei = vencedor === this.humano;
      texto = euGanhei ? 'Xeque-mate: você venceu!' : 'Xeque-mate: o bot venceu.';
      resultado = vencedor === 'w' ? '1-0' : '0-1';
    } else if (this.chess.isStalemate()) {
      texto = 'Empate por afogamento (rei sem lances legais).';
      resultado = '1/2-1/2';
    } else if (this.chess.isThreefoldRepetition()) {
      texto = 'Empate por repetição tripla.';
      resultado = '1/2-1/2';
    } else if (this.chess.isInsufficientMaterial()) {
      texto = 'Empate por material insuficiente.';
      resultado = '1/2-1/2';
    } else {
      texto = 'Empate.';
      resultado = '1/2-1/2';
    }
    this._finalizar(texto, resultado);
    return true;
  }

  _finalizar(texto, resultado) {
    if (!this.emAndamento) return;
    this.emAndamento = false;
    this.resultado = resultado;
    clearInterval(this._timer);
    this.tabuleiro.setInterativo(false);
    this.tabuleiro.setas([]);
    this._definirStatus(texto, 'fim');
    this._mostrarResultado(texto, resultado);
    toast(texto);
    const btn = document.getElementById('btn-analisar-partida');
    btn.disabled = false;
    document.getElementById('btn-dica').disabled = true;
    document.getElementById('btn-desfazer').disabled = true;
    this._salvarPartida(resultado, texto);
  }

  _mostrarResultado(texto, resultado) {
    const caixa = document.getElementById('resultado-jogo');
    if (!caixa) return;
    const eu = this.humano;
    let titulo = 'Empate';
    if (resultado === '1-0') titulo = eu === 'w' ? 'Você venceu!' : 'Você perdeu';
    else if (resultado === '0-1') titulo = eu === 'b' ? 'Você venceu!' : 'Você perdeu';
    document.getElementById('resultado-titulo').textContent = titulo;
    document.getElementById('resultado-sub').textContent = `${texto} · ${resultado}`;
    caixa.hidden = false;
  }

  _esconderResultado() {
    const caixa = document.getElementById('resultado-jogo');
    if (caixa) caixa.hidden = true;
  }

  async _salvarPartida(resultado, motivo) {
    const headers = {
      Event: 'Treino contra o bot (Xadrez Studio)',
      Site: 'Xadrez Studio',
      Date: new Date().toISOString().slice(0, 10),
      White: this.humano === 'w' ? 'Você' : `Bot ${this.config.nivel}`,
      Black: this.humano === 'b' ? 'Você' : `Bot ${this.config.nivel}`,
      Result: resultado,
    };
    const copia = new Chess();
    copia.loadPgn(this.chess.pgn());
    for (const [k, v] of Object.entries(headers)) copia.setHeader(k, v);
    const pgn = copia.pgn();
    try {
      await salvarJogo({
        pgn,
        titulo: `Você × ${nomeNivel(this.config.nivel)}`,
        brancas: headers.White,
        pretas: headers.Black,
        resultado,
        origem: 'bot',
        observacao: motivo,
      });
      toast('Partida salva na biblioteca.');
    } catch {
      toast('Não consegui salvar a partida.', 'erro');
    }
  }

  /** Abre a configuração de novo jogo (encerra a partida em andamento). */
  _encerrarVisual() {
    this.emAndamento = false;
    this.botPensando = false;
    clearInterval(this._timer);
    document.getElementById('config-jogo').hidden = false;
    document.getElementById('jogo-ativo').hidden = true;
    document.getElementById('acoes-tabuleiro').hidden = true;
    document.getElementById('feedback-jogar').hidden = true;
    this._esconderResultado();
    document.getElementById('titulo-jogo').textContent = 'Nova partida';
    this.tabuleiro.setInterativo(false);
    this.tabuleiro.setas([]);
  }

  /**
   * Partida pronta para jogar logo que o app abre (é o que o usuário espera:
   * tabuleiro vivo, sem precisar procurar o botão "começar").
   */
  iniciarPadrao() {
    if (this.emAndamento) return;
    this.iniciar(this._lerConfig());
  }

  _definirStatus(texto, tipo) {
    const selo = document.getElementById('selo-status');
    if (selo) {
      selo.textContent = texto;
      selo.className = `selo ${tipo || ''}`;
    }
    const linha = document.getElementById('status-jogo');
    if (linha) {
      linha.textContent = texto;
      linha.className = `status-jogo ${tipo || ''}`;
    }
  }

  _renderizarLances() {
    const lista = document.getElementById('lances-jogar');
    lista.innerHTML = '';
    const historico = this.chess.history();
    for (let i = 0; i < historico.length; i += 2) {
      lista.appendChild(el('li', {}, el('span', { class: 'num' }, `${i / 2 + 1}.`)));
      lista.appendChild(el('li', {}, el('span', { class: 'lance' }, historico[i])));
      lista.appendChild(el('li', {}, el('span', { class: 'lance' }, historico[i + 1] || '')));
    }
    lista.scrollTop = lista.scrollHeight;
  }

  _renderizarTudo() {
    this.tabuleiro.render(this.chess.fen());
    this._renderizarLances();
    this._pintarRelogios();
  }
}
