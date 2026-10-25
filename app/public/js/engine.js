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
  constructor(url = URL_PADRAO, { hash = 32, reserva = URL_RESERVA } = {}) {
    this.url = url;
    this.urlReserva = reserva;
    this.hash = hash;
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
    if (!ok && this.urlReserva && this.url !== this.urlReserva) {
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
      this.enviar(`setoption name Hash value ${this.hash}`);
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
        // com os dois limites o Stockfish para no primeiro que chegar: piso de
        // qualidade (profundidade) e teto de tempo (posição patológica)
        this.enviar(movetime ? `go depth ${depth} movetime ${movetime}` : `go depth ${depth}`);
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

/** Instância única do bot. */
export const motor = new Motor(URL_PADRAO, { hash: 24 });

/**
 * Motor separado para as assistências do modo Jogar (barra de avaliação, dica,
 * feedback). Antes era o mesmo motor do bot e a análise da minha vez entrava na
 * mesma fila do lance do bot — o bot só respondia depois dela terminar.
 */
export const motorAjuda = new Motor(URL_PADRAO, { hash: 12 });

/**
 * Quantos Stockfish rodar em paralelo na revisão de partida.
 * Um worker por núcleo livre, no máximo 3 (cada um carrega o wasm e um hash).
 */
export function tamanhoDoPool() {
  const nav = typeof navigator !== 'undefined' ? navigator : {};
  const nucleos = nav.hardwareConcurrency || 4;
  const memoria = nav.deviceMemory || 4;          // GB aproximados (Chrome/WebView)
  const porMemoria = memoria >= 6 ? 3 : memoria >= 4 ? 2 : 1;
  const porNucleo = nucleos >= 4 ? 3 : nucleos >= 2 ? 2 : 1;
  return Math.max(1, Math.min(3, porMemoria, porNucleo));
}

/**
 * Pool de motores para analisar várias posições ao mesmo tempo.
 * Cada `Motor` tem seu próprio Worker: o ganho é praticamente linear até 3.
 */
export class PoolAnalise {
  constructor({ tamanho = tamanhoDoPool(), hash = 12 } = {}) {
    this.tamanho = Math.max(1, tamanho);
    this.hash = hash;
    this.motores = [];
    this.falhas = 0;
    this.acertosCache = 0;
    // posições já analisadas nesta sessão: FEN + nº de linhas → { depth, lines }
    this.cache = new Map();
  }

  /** Chave do cache: mesma posição e mesmas linhas; profundidade é comparada. */
  static chave(fen, multipv) {
    return `${fen}|${multipv}`;
  }

  motor(indice = 0) {
    if (!this.motores[indice]) {
      this.motores[indice] = new Motor(URL_PADRAO, { hash: this.hash, reserva: null });
    }
    return this.motores[indice];
  }

  async preparar() {
    const lista = Array.from({ length: this.tamanho }, (_, i) => this.motor(i));
    const oks = await Promise.all(lista.map((m) => m.iniciar().catch(() => false)));
    const prontos = oks.filter(Boolean).length;
    if (!prontos) throw new Error(lista[0].erro || 'motor indisponível');
    // se algum worker não subiu, trabalha só com os que subiram
    this.tamanho = prontos;
    return prontos;
  }

  /**
   * Analisa `fens` distribuindo as posições entre os workers.
   * `opcoes(i)` devolve { depth, movetime, multipv } para a posição i;
   * `aoProgredir(feitas, total, indice)` é chamado a cada posição concluída.
   */
  async analisarTodas(fens, opcoes, { aoProgredir = null, cancelado = null, usarCache = true } = {}) {
    const prontos = await this.preparar();
    const resultados = new Array(fens.length);
    let proxima = 0;
    let feitas = 0;

    const trabalhar = async (indiceMotor) => {
      const m = this.motor(indiceMotor);
      for (;;) {
        if (cancelado?.()) return;
        const i = proxima++;
        if (i >= fens.length) return;
        const cfg = typeof opcoes === 'function' ? opcoes(i) : opcoes;
        const multipv = cfg.multipv || 2;

        // reanálise da mesma posição (outra partida com a mesma abertura, ou
        // mudar a profundidade para baixo) não precisa do motor de novo
        const chave = PoolAnalise.chave(fens[i], multipv);
        const guardado = usarCache ? this.cache.get(chave) : null;
        if (guardado && guardado.depth >= (cfg.depth || 0)) {
          this.acertosCache++;
          resultados[i] = { fen: fens[i], lines: guardado.lines, best: null, cache: true };
          feitas++;
          aoProgredir?.(feitas, fens.length, i);
          continue;
        }

        try {
          const resposta = await m.analisar({
            fen: fens[i],
            depth: cfg.depth,
            movetime: cfg.movetime || 0,
            multipv,
          });
          resultados[i] = { fen: fens[i], lines: resposta.lines, best: resposta.best };
          if (usarCache) {
            // guarda até resultado vazio (posição de mate): repetir não muda nada
            if (this.cache.size > 4000) this.cache.clear();
            this.cache.set(chave, { depth: cfg.depth, lines: resposta.lines || [] });
          }
        } catch (err) {
          this.falhas++;
          resultados[i] = { fen: fens[i], lines: [], best: null, erro: err.message };
        }
        feitas++;
        aoProgredir?.(feitas, fens.length, i);
      }
    };

    await Promise.all(Array.from({ length: prontos }, (_, i) => trabalhar(i)));
    if (cancelado?.()) throw new Error('cancelado');
    return resultados;
  }

  parar() {
    for (const m of this.motores) {
      try { m.worker?.terminate?.(); } catch { /* ok */ }
    }
    this.motores = [];
  }
}

/**
 * Orçamento de análise: profundidade desejada + teto de tempo por posição,
 * distribuído entre os workers.
 *
 * O MultiPV é o maior vilão do tempo: nesta mesma máquina, depth 14 custa
 * ~389 ms com MultiPV 3 e ~55 ms com MultiPV 2 (o Stockfish refaz a busca para
 * cada linha). A revisão só usava a 3ª linha para exibir, então caiu para 2.
 *
 * `profundidades: [curta, longa]` — em partidas muito longas o modo automático
 * desce um degrau para não passar do orçamento.
 */
export const PERFIS_ANALISE = {
  auto: { rotulo: 'Automática', profundidades: [14, 12], orcamento: 60, minMs: 120, maxMs: 1200 },
  12: { rotulo: 'Rápida', profundidades: [12], orcamento: 25, minMs: 80, maxMs: 400 },
  16: { rotulo: 'Profunda', profundidades: [16], orcamento: 150, minMs: 250, maxMs: 2000 },
  18: { rotulo: 'Máxima', profundidades: [18], orcamento: 300, minMs: 400, maxMs: 4000 },
};

export function perfilDeAnalise(escolha, totalPosicoes, workers = 1) {
  const chave = PERFIS_ANALISE[escolha] ? String(escolha) : 'auto';
  const perfil = PERFIS_ANALISE[chave];
  const n = Math.max(1, totalPosicoes);
  const w = Math.max(1, workers);
  const depth = chave === 'auto'
    ? (n <= 120 ? perfil.profundidades[0] : perfil.profundidades[1])
    : perfil.profundidades[0];
  const porPosicao = (perfil.orcamento * 1000 * w) / n;
  const movetime = Math.round(Math.min(perfil.maxMs, Math.max(perfil.minMs, porPosicao)));
  return {
    escolha: chave,
    depth,
    movetime,
    workers: w,
    orcamento: perfil.orcamento,
    rotulo: perfil.rotulo,
  };
}

/** Estimativa grosseira do tempo de parede da revisão, para mostrar na tela. */
export function estimarSegundos(totalPosicoes, perfil) {
  return Math.round((totalPosicoes * perfil.movetime) / 1000 / Math.max(1, perfil.workers));
}
