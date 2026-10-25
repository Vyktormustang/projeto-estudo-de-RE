/** Utilidades de UCI compartilhadas pelo app (worker) e pelos testes (Node). */

export function parseInfo(line) {
  if (!line.startsWith('info ')) return null;
  if (line.includes('bound')) return null; // linhas de limite superior/inferior não são avaliações finais
  const depth = num(line, / depth (\d+)/);
  if (depth == null) return null;
  const multipv = num(line, / multipv (\d+)/) ?? 1;
  const mateMatch = line.match(/ score mate (-?\d+)/);
  const cpMatch = line.match(/ score cp (-?\d+)/);
  const pvMatch = line.match(/ pv (.+)$/);
  if (!mateMatch && !cpMatch && !pvMatch) return null;
  return {
    depth,
    multipv,
    score: mateMatch ? { mate: Number(mateMatch[1]) } : cpMatch ? { cp: Number(cpMatch[1]) } : null,
    pv: pvMatch ? pvMatch[1].trim().split(/\s+/) : [],
    nodes: num(line, / nodes (\d+)/),
    nps: num(line, / nps (\d+)/),
    time: num(line, / time (\d+)/),
  };
}

function num(line, re) {
  const m = line.match(re);
  return m ? Number(m[1]) : null;
}

/** Guarda só a linha mais profunda de cada multipv. */
export function makeLineStore() {
  const byMultipv = new Map();
  return {
    add(info) {
      const prev = byMultipv.get(info.multipv);
      if (!prev || info.depth >= prev.depth) byMultipv.set(info.multipv, info);
    },
    lines() {
      return [...byMultipv.values()]
        .sort((a, b) => a.multipv - b.multipv)
        .map((l) => ({ cp: l.score?.cp, mate: l.score?.mate, pv: l.pv, depth: l.depth }));
    },
    clear() { byMultipv.clear(); },
  };
}

export function parseBestMove(line) {
  const m = line.match(/^bestmove\s+(\S+)(?:\s+ponder\s+(\S+))?/);
  if (!m) return null;
  return { move: m[1], ponder: m[2] || null };
}
