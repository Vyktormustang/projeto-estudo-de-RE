/**
 * Servidor local do Xadrez Studio.
 *
 * - serve o app (public/)
 * - serve as bibliotecas de node_modules (chess.js e Stockfish) em /vendor
 * - API para salvar/abrir partidas na biblioteca (dados/jogos.json)
 * - proxy opcional para a API pública do chess.com (funciona quando há internet)
 *
 * Uso: node server.mjs  (ou PORT=4000 node server.mjs)
 */

import http from 'node:http';
import { readFile, writeFile, mkdir, rename } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.join(ROOT, 'public');
const DADOS = path.join(ROOT, 'dados');
const ARQUIVO_JOGOS = path.join(DADOS, 'jogos.json');
const PORT = Number(process.env.PORT || 3000);
const HOST = process.env.HOST || '0.0.0.0';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.wasm': 'application/wasm',
  '.woff2': 'font/woff2',
};

/** Bibliotecas servidas a partir de node_modules (instaladas com npm install). */
const VENDOR = {
  '/vendor/stockfish/stockfish-19-lite-single.js': 'node_modules/stockfish/bin/stockfish-19-lite-single.js',
  '/vendor/stockfish/stockfish-19-lite-single.wasm': 'node_modules/stockfish/bin/stockfish-19-lite-single.wasm',
  '/vendor/stockfish/stockfish-19.js': 'node_modules/stockfish/bin/stockfish-19.js',
  '/vendor/stockfish/stockfish-19.wasm': 'node_modules/stockfish/bin/stockfish-19.wasm',
};

function send(res, status, body, type = 'application/json; charset=utf-8') {
  res.writeHead(status, {
    'Content-Type': type,
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Origin': '*',
  });
  res.end(body);
}

async function sendFile(res, filePath) {
  try {
    const data = await readFile(filePath);
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Cache-Control': ext === '.wasm' ? 'public, max-age=86400' : 'no-store',
      // O build single-thread do Stockfish não precisa de SharedArrayBuffer,
      // então não isolamos a página (COOP/COEP) — menos atrito no preview.
      'Cross-Origin-Resource-Policy': 'cross-origin',
    });
    res.end(data);
  } catch {
    send(res, 404, JSON.stringify({ erro: 'arquivo não encontrado', caminho: filePath }));
  }
}

async function lerJogos() {
  try {
    const txt = await readFile(ARQUIVO_JOGOS, 'utf8');
    const lista = JSON.parse(txt);
    return Array.isArray(lista) ? lista : [];
  } catch {
    return [];
  }
}

async function gravarJogos(lista) {
  await mkdir(DADOS, { recursive: true });
  const tmp = `${ARQUIVO_JOGOS}.tmp`;
  await writeFile(tmp, JSON.stringify(lista, null, 2), 'utf8');
  await rename(tmp, ARQUIVO_JOGOS);
}

function lerCorpo(req, limite = 2 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    let total = 0;
    const partes = [];
    req.on('data', (chunk) => {
      total += chunk.length;
      if (total > limite) {
        reject(new Error('corpo grande demais'));
        req.destroy();
        return;
      }
      partes.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(partes).toString('utf8')));
    req.on('error', reject);
  });
}

/** API pública do chess.com (usada pelo botão "importar do chess.com"). */
async function importarChessCom(user, limite) {
  const base = 'https://api.chess.com/pub';
  const buscar = async (url) => {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 10000);
    try {
      const resp = await fetch(url, {
        signal: ctrl.signal,
        headers: { 'User-Agent': 'xadrez-studio/1.0 (uso pessoal)' },
      });
      if (!resp.ok) throw new Error(`chess.com respondeu ${resp.status}`);
      return await resp.json();
    } finally {
      clearTimeout(timer);
    }
  };
  const arquivos = await buscar(`${base}/player/${encodeURIComponent(user)}/games/archives`);
  const ultimos = (arquivos.archives || []).slice(-2).reverse();
  const jogos = [];
  for (const url of ultimos) {
    const mes = await buscar(url);
    for (const jogo of mes.games || []) {
      if (!jogo.pgn) continue;
      const brancas = jogo.white?.username || '?';
      const pretas = jogo.black?.username || '?';
      const resultado = `${jogo.white?.result || '?'}/${jogo.black?.result || '?'}`;
      jogos.push({
        pgn: jogo.pgn,
        url: jogo.url,
        classe: jogo.time_class,
        regras: jogo.rules,
        data: jogo.end_time,
        brancas,
        pretas,
        resultado,
        // PGNs do chess.com vêm com os headers; a revisão usa os dois lados
        resumo: `${brancas} × ${pretas} — ${resultado}`,
      });
    }
    if (jogos.length >= limite) break;
  }
  return jogos.sort((a, b) => (b.data || 0) - (a.data || 0)).slice(0, limite);
}

const servidor = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const rota = decodeURIComponent(url.pathname);

  // ---------------------------------------------------------------- API
  if (rota.startsWith('/api/')) {
    try {
      if (rota === '/api/saude') {
        const temMotor = existsSync(path.join(ROOT, VENDOR['/vendor/stockfish/stockfish-19-lite-single.wasm']));
        return send(res, 200, JSON.stringify({ ok: true, motor: temMotor, versao: 1 }));
      }

      if (rota === '/api/jogos' && req.method === 'GET') {
        const lista = await lerJogos();
        return send(res, 200, JSON.stringify(lista));
      }

      if (rota === '/api/jogos' && req.method === 'POST') {
        const corpo = JSON.parse(await lerCorpo(req));
        if (!corpo?.pgn) return send(res, 400, JSON.stringify({ erro: 'pgn obrigatório' }));
        const lista = await lerJogos();
        // mesma partida (mesmo PGN) não vira duplicata: atualiza o registro existente
        const existente = lista.find((j) => j.pgn === corpo.pgn);
        const id = corpo.id || existente?.id
          || `j${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
        const registro = {
          id,
          pgn: corpo.pgn,
          titulo: corpo.titulo || 'Partida sem título',
          brancas: corpo.brancas || '',
          pretas: corpo.pretas || '',
          resultado: corpo.resultado || '*',
          origem: corpo.origem || 'manual',
          data: new Date().toISOString(),
          revisao: corpo.revisao || null,
          relatorio: corpo.relatorio || null,
        };
        const idx = lista.findIndex((j) => j.id === id);
        if (idx >= 0) lista[idx] = registro;
        else lista.unshift(registro);
        await gravarJogos(lista);
        return send(res, 200, JSON.stringify(registro));
      }

      if (rota.startsWith('/api/jogos/') && req.method === 'DELETE') {
        const id = rota.split('/').pop();
        const lista = await lerJogos();
        const nova = lista.filter((j) => j.id !== id);
        await gravarJogos(nova);
        return send(res, 200, JSON.stringify({ ok: true, removidos: lista.length - nova.length }));
      }

      if (rota === '/api/chesscom' && req.method === 'GET') {
        const user = url.searchParams.get('usuario');
        const limite = Number(url.searchParams.get('limite') || 20);
        if (!user) return send(res, 400, JSON.stringify({ erro: 'informe ?usuario=' }));
        const jogos = await importarChessCom(user, limite);
        return send(res, 200, JSON.stringify({ usuario: user, total: jogos.length, jogos }));
      }

      return send(res, 404, JSON.stringify({ erro: 'rota de API desconhecida' }));
    } catch (err) {
      return send(res, 502, JSON.stringify({
        erro: 'falha na API',
        detalhe: err.message,
        dica: 'sem internet no servidor? cole o PGN da partida em vez de importar',
      }));
    }
  }

  // ------------------------------------------------------------- vendor
  if (VENDOR[rota]) return sendFile(res, path.join(ROOT, VENDOR[rota]));

  // ------------------------------------------------------------ estático
  const relativo = rota === '/' ? 'index.html' : rota.replace(/^\/+/, '');
  const destino = path.join(PUBLIC, relativo);
  if (!destino.startsWith(PUBLIC)) return send(res, 403, 'proibido', 'text/plain');
  if (existsSync(destino)) return sendFile(res, destino);

  // fallback do SPA
  return sendFile(res, path.join(PUBLIC, 'index.html'));
});

servidor.listen(PORT, HOST, () => {
  console.log(`Xadrez Studio em http://localhost:${PORT} (bind ${HOST})`);
  if (!existsSync(path.join(ROOT, 'node_modules'))) {
    console.warn('⚠ node_modules ausente — rode "npm install" para ter motor e regras.');
  }
});
