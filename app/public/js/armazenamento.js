/**
 * Persistência das partidas.
 *
 * Duas implementações com a mesma cara:
 *  - **servidor** (rodando `npm start`): arquivos em `dados/jogos.json`;
 *  - **local** (APK / arquivo aberto direto): `localStorage` do navegador.
 *
 * O modo é escolhido sozinho: no APK a página é aberta com `?armazenamento=local`;
 * no navegador, se a API do servidor não responder, cai para o modo local.
 */

const CHAVE = 'xadrez-studio:jogos';
let modo = null;

/** Decide o modo na primeira chamada (e não no import, para funcionar em teste). */
function modoAtual() {
  if (modo) return modo;
  const loc = typeof location !== 'undefined' ? location : { search: '', protocol: 'http:' };
  const forcado = loc.search.includes('armazenamento=local') || loc.protocol === 'file:';
  modo = forcado ? 'local' : 'servidor';
  return modo;
}

export function modoArmazenamento() {
  return modoAtual();
}

function lerLocal() {
  try {
    const bruto = localStorage.getItem(CHAVE);
    const lista = bruto ? JSON.parse(bruto) : [];
    return Array.isArray(lista) ? lista : [];
  } catch {
    return [];
  }
}

function gravarLocal(lista) {
  try {
    localStorage.setItem(CHAVE, JSON.stringify(lista));
  } catch {
    /* sem espaço ou sem permissão: a partida fica só na sessão */
  }
  return lista;
}

function novoId() {
  return `j${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

export async function listarJogos() {
  if (modoAtual() === 'servidor') {
    try {
      const resp = await fetch('/api/jogos');
      if (!resp.ok) throw new Error(String(resp.status));
      return await resp.json();
    } catch {
      modo = 'local';
    }
  }
  return lerLocal();
}

export async function salvarJogo(jogo) {
  if (modoAtual() === 'servidor') {
    try {
      const resp = await fetch('/api/jogos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jogo),
      });
      if (!resp.ok) throw new Error(String(resp.status));
      return await resp.json();
    } catch {
      modo = 'local';
    }
  }
  const lista = lerLocal();
  const existente = lista.find((j) => j.pgn === jogo.pgn);
  const registro = {
    id: existente?.id || jogo.id || novoId(),
    ...existente,
    ...jogo,
    data: new Date().toISOString(),
  };
  gravarLocal([registro, ...lista.filter((j) => j.id !== registro.id)]);
  return registro;
}

export async function excluirJogo(id) {
  if (modoAtual() === 'servidor') {
    try {
      const resp = await fetch(`/api/jogos/${id}`, { method: 'DELETE' });
      if (!resp.ok) throw new Error(String(resp.status));
      return await resp.json();
    } catch {
      modo = 'local';
    }
  }
  const lista = lerLocal();
  const sobrou = lista.filter((j) => j.id !== id);
  gravarLocal(sobrou);
  return { ok: true, removidos: lista.length - sobrou.length };
}

/**
 * Partidas do chess.com. Primeiro tenta o proxy do servidor local (que resolve
 * CORS); se não houver servidor, tenta a API pública direto do navegador.
 */
export async function importarChessCom(usuario, limite = 15) {
  if (modoAtual() === 'servidor') {
    try {
      const resp = await fetch(`/api/chesscom?usuario=${encodeURIComponent(usuario)}&limite=${limite}`);
      const dados = await resp.json();
      if (resp.ok) return dados;
      throw new Error(dados.detalhe || dados.erro || 'falha no proxy');
    } catch {
      /* segue para a tentativa direta */
    }
  }
  return await direto(usuario, limite);
}

async function direto(usuario, limite) {
  const base = 'https://api.chess.com/pub';
  const cabecalho = { Accept: 'application/json' };
  const buscar = async (url) => {
    const resp = await fetch(url, { headers: cabecalho });
    if (!resp.ok) throw new Error(`chess.com respondeu ${resp.status}`);
    return await resp.json();
  };
  const arquivos = await buscar(`${base}/player/${encodeURIComponent(usuario)}/games/archives`);
  const jogos = [];
  for (const url of (arquivos.archives || []).slice(-2).reverse()) {
    const mes = await buscar(url);
    for (const jogo of mes.games || []) {
      if (!jogo.pgn) continue;
      jogos.push({
        pgn: jogo.pgn,
        url: jogo.url,
        classe: jogo.time_class,
        data: jogo.end_time,
        brancas: jogo.white?.username || '?',
        pretas: jogo.black?.username || '?',
        resultado: `${jogo.white?.result || '?'}/${jogo.black?.result || '?'}`,
      });
    }
    if (jogos.length >= limite) break;
  }
  return { usuario, total: jogos.length, jogos: jogos.slice(0, limite) };
}
