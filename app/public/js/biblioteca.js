/** Modo "Biblioteca": partidas salvas no computador. */

import { Chess } from 'chess.js';
import { toast, el, fmtData } from './util.js';
import { CLASS_INFO } from './review.js';

export class Biblioteca {
  constructor() {
    this.jogos = [];
    document.getElementById('btn-recarregar').addEventListener('click', () => this.carregar());
  }

  async carregar() {
    const grade = document.getElementById('lista-biblioteca');
    grade.innerHTML = '<p class="vazio">carregando…</p>';
    try {
      const resp = await fetch('/api/jogos');
      if (!resp.ok) throw new Error(`servidor respondeu ${resp.status}`);
      this.jogos = await resp.json();
      this._render();
    } catch (err) {
      grade.innerHTML = '';
      grade.appendChild(el('p', { class: 'vazio' },
        `Não consegui ler a biblioteca (${err.message}). O servidor está rodando?`));
    }
  }

  _render() {
    const grade = document.getElementById('lista-biblioteca');
    grade.innerHTML = '';
    if (!this.jogos.length) {
      grade.appendChild(el('p', { class: 'vazio' },
        'Nenhuma partida salva ainda. Jogue contra o bot ou analise um PGN — tudo o que você revisar fica aqui.'));
      return;
    }
    for (const jogo of this.jogos) {
      grade.appendChild(this._cartao(jogo));
    }
  }

  _cartao(jogo) {
    const cartao = el('div', { class: 'cartao-jogo' });
    const titulo = jogo.titulo || `${jogo.brancas || '?'} × ${jogo.pretas || '?'}`;
    cartao.appendChild(el('h3', {}, titulo));

    const lances = this._contarLances(jogo.pgn);
    const meta = [jogo.resultado || '*', `${lances} lances`, fmtData(jogo.data), jogo.origem === 'bot' ? 'contra bot' : null]
      .filter(Boolean).join(' · ');
    cartao.appendChild(el('div', { class: 'meta' }, meta));

    if (jogo.revisao?.accuracy) {
      const { white, black } = jogo.revisao.accuracy;
      const info = [];
      if (white != null) info.push(`brancas ${white}%`);
      if (black != null) info.push(`pretas ${black}%`);
      if (info.length) cartao.appendChild(el('div', { class: 'meta' }, `precisão: ${info.join(' · ')}`));
      if (jogo.revisao.counts) {
        const linhas = el('div', { class: 'classes' });
        for (const [chave, n] of Object.entries(jogo.revisao.counts)) {
          if (!n) continue;
          const c = CLASS_INFO[chave];
          if (!c) continue;
          linhas.appendChild(el('span', { class: 'chip-classe' },
            el('i', { style: `background:${c.color}` }), `${c.label} `, el('b', {}, String(n))));
        }
        cartao.appendChild(linhas);
      }
    }

    const acoes = el('div', { class: 'acoes' });
    const revisar = el('button', { class: 'principal' }, 'Revisar');
    revisar.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('xadrez:analisar', { detail: { pgn: jogo.pgn } }));
    });
    const copiar = el('button', {}, 'Copiar PGN');
    copiar.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(jogo.pgn);
        toast('PGN copiado.');
      } catch {
        toast('O navegador bloqueou a cópia.', 'erro');
      }
    });
    const excluir = el('button', {}, 'Excluir');
    excluir.addEventListener('click', async () => {
      if (!confirm('Excluir esta partida da biblioteca?')) return;
      try {
        await fetch(`/api/jogos/${jogo.id}`, { method: 'DELETE' });
        toast('Partida excluída.');
        this.carregar();
      } catch {
        toast('Não consegui excluir.', 'erro');
      }
    });
    acoes.append(revisar, copiar, excluir);
    cartao.appendChild(acoes);
    return cartao;
  }

  _contarLances(pgn) {
    try {
      const c = new Chess();
      c.loadPgn(pgn);
      return c.history().length;
    } catch {
      return '?';
    }
  }
}
