/**
 * main.ts — UI mínima do build de canário.
 *
 * Propósito deste arquivo nesta versão: provar que o pipeline
 * (TypeScript → Vite → assets → APK assinado) funciona ponta a ponta,
 * exercitando código real do núcleo (`forja.ts`) dentro do WebView.
 * A UI definitiva do v39.0 substitui este arquivo quando o fonte do v38
 * entrar no repositório — o núcleo e os testes permanecem.
 */
import './style.css';
import {
  categoriaElo,
  CHAVE_COFRE,
  cofreVazio,
  novoElo,
  registrarPartida,
  sanearCofre,
  type Cofre,
  type Resultado,
} from './forja';

declare const __FORJA_VERSAO__: string;
declare const __FORJA_COMMIT__: string;
declare const __FORJA_BUILD_TIME__: string;

const VERSAO = typeof __FORJA_VERSAO__ === 'string' ? __FORJA_VERSAO__ : '39.0.0';
const COMMIT = typeof __FORJA_COMMIT__ === 'string' ? __FORJA_COMMIT__ : 'local';
const BUILD = typeof __FORJA_BUILD_TIME__ === 'string' ? __FORJA_BUILD_TIME__ : new Date().toISOString();

function carregarCofre(): Cofre {
  try {
    const cru = localStorage.getItem(CHAVE_COFRE);
    return cru ? sanearCofre(JSON.parse(cru)) : cofreVazio();
  } catch {
    return cofreVazio();
  }
}

function salvarCofre(c: Cofre): void {
  try {
    localStorage.setItem(CHAVE_COFRE, JSON.stringify(c));
  } catch {
    /* WebView sem storage: o app continua funcionando em memória */
  }
}

let cofre = carregarCofre();

const raiz = document.querySelector<HTMLDivElement>('#app');
if (!raiz) throw new Error('#app não encontrado');

raiz.innerHTML = `
  <main class="tela">
    <header class="marca">
      <div class="brasa" aria-hidden="true"></div>
      <div>
        <h1>Forja</h1>
        <p class="sub">Sistema do Ápice · v${VERSAO} · build de canário</p>
      </div>
    </header>

    <section class="cartao">
      <h2>Pipeline de APK</h2>
      <div class="linha"><span>Application ID</span><span class="mono">br.forja.apice</span></div>
      <div class="linha"><span>Versão</span><span class="mono">${VERSAO}</span></div>
      <div class="linha"><span>Commit</span><span class="mono">${COMMIT.slice(0, 12)}</span></div>
      <div class="linha"><span>Build (UTC)</span><span class="mono">${BUILD.replace('T', ' ').slice(0, 19)}</span></div>
      <div class="linha"><span>Rede</span><span>0 permissões · offline</span></div>
    </section>

    <section class="cartao">
      <h2>Núcleo do xadrez — Elo (testado)</h2>
      <div class="elo">
        <strong id="elo-valor">—</strong>
        <span id="elo-cat" class="sub">—</span>
      </div>
      <div class="linha"><span>Placar</span><span id="placar">—</span></div>
      <div class="linha"><span>Adversário simulado</span><span class="mono">1500</span></div>
      <div class="botoes" style="margin-top:12px">
        <button class="vitoria" data-res="vitoria">Vitória</button>
        <button data-res="empate">Empate</button>
        <button class="derrota" data-res="derrota">Derrota</button>
      </div>
    </section>

    <div class="aviso">
      Este APK é um <strong>build de canário</strong>: existe para validar o
      pipeline de compilação e assinatura no GitHub Actions. A UI completa do
      v38 será restaurada assim que o código-fonte entrar no repositório.
    </div>

    <footer>
      FORJA · br.forja.apice · 100% offline, sem permissão de rede<br />
      Dados do Cofre ficam no localStorage do aparelho.
    </footer>
  </main>
`;

const eloValor = document.querySelector<HTMLElement>('#elo-valor');
const eloCat = document.querySelector<HTMLElement>('#elo-cat');
const placar = document.querySelector<HTMLElement>('#placar');

function pintar(): void {
  if (eloValor) eloValor.textContent = String(cofre.eloXadrez);
  if (eloCat) eloCat.textContent = categoriaElo(cofre.eloXadrez);
  if (placar) {
    placar.textContent = `${cofre.vitorias}V · ${cofre.empates}E · ${cofre.derrotas}D`;
  }
}

raiz.querySelectorAll<HTMLButtonElement>('button[data-res]').forEach((btn) => {
  btn.addEventListener('click', () => {
    const res = btn.dataset.res as Resultado;
    const { delta } = novoElo(cofre.eloXadrez, 1500, res);
    cofre = registrarPartida(cofre, 1500, res);
    salvarCofre(cofre);
    pintar();
    btn.textContent = `${res === 'vitoria' ? 'Vitória' : res === 'empate' ? 'Empate' : 'Derrota'} ${delta >= 0 ? '+' : ''}${delta}`;
    window.setTimeout(() => {
      btn.textContent = res === 'vitoria' ? 'Vitória' : res === 'empate' ? 'Empate' : 'Derrota';
    }, 900);
  });
});

pintar();
