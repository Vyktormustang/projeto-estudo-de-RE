/** Utilidades de interface compartilhadas. */

export function toast(mensagem, tipo = 'ok', ms = 4200) {
  const caixa = document.getElementById('toasts');
  if (!caixa) return;
  const el = document.createElement('div');
  el.className = `toast ${tipo === 'erro' ? 'erro' : ''}`;
  el.textContent = mensagem;
  caixa.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(6px)';
    el.style.transition = '.25s';
    setTimeout(() => el.remove(), 260);
  }, ms);
}

export function el(tag, attrs = {}, ...filhos) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') node.className = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k === 'text') node.textContent = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'dataset') Object.assign(node.dataset, v);
    else node.setAttribute(k, v);
  }
  for (const f of filhos.flat()) {
    if (f == null || f === false) continue;
    node.appendChild(typeof f === 'string' ? document.createTextNode(f) : f);
  }
  return node;
}

export function fmtTempo(segundos) {
  if (segundos == null) return '—';
  const s = Math.max(0, Math.ceil(segundos));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, '0')}`;
}

export function fmtData(iso) {
  if (!iso) return '';
  const d = typeof iso === 'number' ? new Date(iso * 1000) : new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
}

export const NOMES_NIVEL = [
  [400, 'Iniciante'], [800, 'Casual'], [1200, 'Intermediário'],
  [1600, 'Clube'], [2000, 'Avançado'], [2500, 'Mestre'], [3000, 'Motor'],
];

export function nomeNivel(nivel) {
  let nome = 'Iniciante';
  for (const [n, label] of NOMES_NIVEL) if (nivel >= n) nome = label;
  if (nivel >= 2900) nome = 'Motor';
  return `${nome} ${Math.round(nivel)}`;
}

/** Descarrega um texto como arquivo. */
export function baixar(nome, texto, tipo = 'text/plain') {
  const blob = new Blob([texto], { type: tipo });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nome;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
