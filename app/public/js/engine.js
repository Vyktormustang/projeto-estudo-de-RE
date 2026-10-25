/**
 * Wrapper do Stockfish rodando em Web Worker (build lite single-thread, sem
 * SharedArrayBuffer). Serializa os pedidos: um `go` por vez.
 */

import { parseInfo, makeLineStore, parseBestMove } from './uci.js';

const URL_PADRAO = '/vendor/stockfish/stockfish-19-lite-single.js';
/** Build mais pesado (multithread), usado só se o lite não subir. */
const URL_RESERVA = '/vendor/stockfish/stockfish-19.js';

/**
 * Traduz um nível "de humano" (250–3200) em parâmetros do Stockfish.
 * Até 1320 o motor só aceita UCI_Elo=1320, então a fraqueza vem de Skill Level
 * e de profundidade baixa. Acima disso o próprio UCI_Elo limita.
 */
export function forcaDoNivel(nivel) {
  const n = Math.max(250, Math.min(3200, Number(nivel) || 1200));
  if (n >= 1320) {
    return {
      elo: Math.min(3190, n),
      skill: 20,
      depth: n >= 2200 ? 14 : n >= 1700 ? 12 : 10,
      movetime: n >= 2200 ? 1200 : 600,
    };
  }
  const t = (n - 250) / (1320 - 250); // 0..1
  return {
    elo: 1320,
    skill: Math.round(t * 9), // 0..9
    depth: Math.max(1, Math.round(1 + t * 6)), // 1..7
    movetime: 200,
  };
}

export class Motor {
  constructor(url = URL_PADRAO) {
    this.url = url;
    this.urlReserva = URL_RESERVA;
    this.worker = null;
    this.pronto = false;
    this.erro = null;
    this.fila = Promise.resolve();
    this.trabalho = null;
    this.parado = false;
  }

  async iniciar(timeoutMs = 25000) {
    if (this.pronto) return true;
    // uma única subida por vez: interface e assistências pedem o motor juntas
    if (!this._subindo) {
      this._subindo = this._subirTudo(timeoutMs).finally(() => { this._subindo = null; });
    }
    return this._subindo;
  }

  async _subirTudo(timeoutMs) {
    const ok = await this._subir(this.url, timeoutMs);
    if (!ok && this.url !== this.urlReserva) {
      // segunda tentativa com o build completo antes de desistir
      this.worker?.terminate?.();
      this.erro = null;
      return this._subir(this.urlReserva, timeoutMs);
    }
    return ok;
  }

  async _subir(url, timeoutMs) {
    this.url = url;
    this.worker = new Worker(url);
    this.worker.onerror = (ev) => {
      this.erro = ev.message || 'falha ao carregar o motor';
      this.pronto = false;
      this._rejeitarTrabalho(this.erro);
    };
    this.worker.onmessage = ({ data }) => this._aoReceber(String(data));

    const inicio = Date.now();
    await new Promise((resolve) => {
      const tentar = () => {
        if (this.pronto || this.erro) return resolve();
        if (Date.now() - inicio > timeoutMs) {
          this.erro = 'o motor não respondeu (tempo esgotado)';
          return resolve();
        }
        this.enviar('uci');
        this.enviar('isready');
        setTimeout(tentar, 250);
      };
      tentar();
    });
    if (this.pronto) {
      this.enviar('setoption name Hash value 64');
      this.enviar('setoption name UCI_LimitStrength value false');
      this.enviar('setoption name Skill Level value 20');
    }
    return this.pronto;
  }

  enviar(cmd) {
    this.worker?.postMessage(cmd);
  }

  _aoReceber(linha) {
    if (linha.startsWith('readyok')) {
      this.pronto = true;
      return;
    }
    if (linha.startsWith('uciok')) return;
    if (linha.startsWith('info ')) {
      const info = parseInfo(linha);
      if (info && this.trabalho) this.trabalho.linhas.add(info);
      return;
    }
    if (linha.startsWith('bestmove')) {
      const t = this.trabalho;
      this.trabalho = null;
      if (!t) return;
      const bm = parseBestMove(linha);
      t.resolver({
        best: bm?.move || null,
        ponder: bm?.ponder || null,
        lines: t.linhas.lines(),
        cancelado: this.parado,
      });
      this.parado = false;
    }
  }

  _rejeitarTrabalho(msg) {
    const t = this.trabalho;
    this.trabalho = null;
    t?.rejeitar?.(new Error(msg));
  }

  /** Executa uma análise; devolve as linhas (multipv) e o melhor lance. */
  analisar({ fen, depth = 14, multipv = 3, movetime = 0, nivel = null }) {
    const execucao = async () => {
      if (!this.pronto && !(await this.iniciar())) {
        throw new Error(this.erro || 'motor indisponível');
      }
      return new Promise((resolve, reject) => {
        this.trabalho = { linhas: makeLineStore(), resolver: resolve, rejeitar: reject };
        if (nivel != null) {
          const f = forcaDoNivel(nivel);
          this.enviar('setoption name UCI_LimitStrength value true');
          this.enviar(`setoption name UCI_Elo value ${f.elo}`);
          this.enviar(`setoption name Skill Level value ${f.skill}`);
          depth = f.depth;
          movetime = movetime || f.movetime;
        } else {
          this.enviar('setoption name UCI_LimitStrength value false');
          this.enviar('setoption name Skill Level value 20');
        }
        this.enviar(`setoption name MultiPV value ${multipv}`);
        this.enviar(`position fen ${fen}`);
        this.enviar(movetime ? `go movetime ${movetime}` : `go depth ${depth}`);
        this.tempoLimite = setTimeout(() => {
          if (this.trabalho) {
            this.enviar('stop');
            setTimeout(() => {
              if (this.trabalho) this._rejeitarTrabalho('o motor demorou demais para responder');
            }, 3000);
          }
        }, Math.max(8000, movetime * 4 + depth * 1200));
      }).finally(() => clearTimeout(this.tempoLimite));
    };
    const proximo = this.fila.then(execucao, execucao);
    this.fila = proximo.catch(() => {});
    return proximo;
  }

  /** Jogada do bot, com força limitada pelo nível. */
  async jogar({ fen, nivel }) {
    const f = forcaDoNivel(nivel);
    const r = await this.analisar({
      fen,
      depth: f.depth,
      movetime: f.movetime,
      multipv: 1,
      nivel,
    });
    return r;
  }

  parar() {
    if (!this.trabalho) return;
    this.parado = true;
    this.enviar('stop');
  }
}

/** Instância única usada pelo app. */
export const motor = new Motor();
