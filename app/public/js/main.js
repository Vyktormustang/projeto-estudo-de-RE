/** Ponto de entrada: abas, estado do motor e ligação entre os modos. */

import { motor } from './engine.js';
import { ModoJogo } from './jogo.js';
import { ModoAnalise } from './analise.js';
import { Biblioteca } from './biblioteca.js';
import { toast } from './util.js';
import { salvarJogo, modoArmazenamento } from './armazenamento.js';

export const VERSAO = '1.1';

const abas = document.querySelectorAll('.aba');
const views = {
  jogar: document.getElementById('view-jogar'),
  analisar: document.getElementById('view-analisar'),
  biblioteca: document.getElementById('view-biblioteca'),
};

function abrir(nome) {
  for (const b of abas) {
    const ativa = b.dataset.aba === nome;
    b.classList.toggle('ativa', ativa);
    b.setAttribute('aria-selected', String(ativa));
  }
  for (const [chave, view] of Object.entries(views)) {
    view.hidden = chave !== nome;
  }
  if (nome === 'biblioteca') biblioteca.carregar();
  if (window.innerWidth < 900) window.scrollTo({ top: 0, behavior: 'smooth' });
}

for (const b of abas) b.addEventListener('click', () => abrir(b.dataset.aba));

const jogo = new ModoJogo({
  aoTerminar: (pgn) => {
    window.dispatchEvent(new CustomEvent('xadrez:analisar', { detail: { pgn } }));
  },
});
const analise = new ModoAnalise();
const biblioteca = new Biblioteca();

// ------------------------------------------------------------- estado motor

const status = document.getElementById('status-motor');
const statusTexto = status.querySelector('.texto');

function definirStatusMotor(texto, classe = '') {
  statusTexto.textContent = `motor: ${texto}`;
  status.className = `status-motor ${classe}`;
}

definirStatusMotor('iniciando…');
motor.iniciar().then((ok) => {
  if (ok) {
    definirStatusMotor('Stockfish pronto', 'ok');
  } else {
    definirStatusMotor('indisponível', 'erro');
    toast('O motor não subiu neste aparelho: dá para mover as peças, mas o bot e a análise ficam parados. '
      + `Detalhe: ${motor.erro || 'erro desconhecido'}.`, 'erro', 9000);
  }
});

// Partida pronta ao abrir: o tabuleiro já responde ao toque, sem precisar
// achar o botão "começar" (foi a maior queixa da primeira versão).
try {
  jogo.iniciarPadrao();
} catch (err) {
  toast(`Não consegui começar a partida: ${err.message}`, 'erro', 9000);
}

// deixa a revisão salvar na biblioteca automaticamente quando terminar
const revisarOriginal = analise.revisar.bind(analise);
analise.revisar = async (...args) => {
  await revisarOriginal(...args);
  if (analise.review) {
    try {
      await salvarJogo({
        pgn: analise.pgn,
        titulo: tituloDoPgn(analise.pgn),
        brancas: analise.review.headers.White || '',
        pretas: analise.review.headers.Black || '',
        resultado: analise.review.headers.Result || '*',
        origem: 'analise',
        revisao: {
          accuracy: analise.review.accuracy,
          counts: analise.review.counts,
          summary: analise.review.summary.text,
        },
      });
    } catch { /* biblioteca é opcional */ }
  }
};

function tituloDoPgn(pgn) {
  const get = (tag) => pgn.match(new RegExp(`\\[${tag} "([^"]*)"\\]`))?.[1];
  const brancas = get('White');
  const pretas = get('Black');
  if (brancas && pretas) return `${brancas} × ${pretas}`;
  return get('Event') || 'Partida analisada';
}

// atalhos globais
document.addEventListener('keydown', (ev) => {
  if (ev.key.toLowerCase() === 'f' && ev.altKey) {
    ev.preventDefault();
    jogo.tabuleiro.setOrientacao(jogo.tabuleiro.orientacao === 'w' ? 'b' : 'w');
  }
});

// diagnóstico (aba Biblioteca): usado para saber o que roda no aparelho
const diagnostico = document.getElementById('diagnostico');
if (diagnostico) {
  const ua = navigator.userAgent || '';
  const chrome = /Chrome\/(\d+)/.exec(ua)?.[1];
  diagnostico.textContent = [
    `Xadrez Studio v${VERSAO}`,
    `armazenamento: ${modoArmazenamento() === 'local' ? 'aparelho (localStorage)' : 'servidor local'}`,
    chrome ? `WebView/Chrome ${chrome}` : 'navegador não identificado',
    `wasm: ${typeof WebAssembly === 'object' ? 'sim' : 'não'}`,
    `tela: ${window.innerWidth}×${window.innerHeight}`,
  ].join(' · ');
}

window.xadrez = { jogo, analise, biblioteca, motor, versao: VERSAO };
