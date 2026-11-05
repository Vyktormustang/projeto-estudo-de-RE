/**
 * Endereço do servidor + preferências, salvos no próprio aparelho.
 *
 * Regra:
 *  - No APK (Android) o app é um arquivo local: precisa do IP do PC
 *    (ex.: http://192.168.0.15:8000). É esse valor que fica salvo aqui.
 *  - No navegador do PC, se você abriu o app pelo próprio servidor
 *    (http://localhost:8000), usamos a MESMA origem (string vazia = relativo).
 *  - Se preferir apontar o navegador para outro PC, salve o endereço também.
 */

import type { Level } from './types';

const SERVER_KEY = 'speaknatural.serverUrl';
const THEME_KEY = 'speaknatural.theme';
const LEVEL_KEY = 'speaknatural.level';

/** Endereço sugerido quando o usuário abre a tela "Servidor" pela 1ª vez. */
export const DEFAULT_SERVER_URL = 'http://192.168.0.100:8000';

export type ThemeChoice = 'auto' | 'light' | 'dark';

export function isNativeApp(): boolean {
  const capacitor = (window as unknown as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor;
  if (capacitor && typeof capacitor.isNativePlatform === 'function') {
    return capacitor.isNativePlatform();
  }
  // Fallback: dentro do APK o esquema é https://localhost (padrão do Capacitor)
  return typeof window !== 'undefined' && window.location?.protocol === 'https:' && window.location?.hostname === 'localhost';
}

export function getServerUrl(): string {
  const stored = localStorage.getItem(SERVER_KEY)?.trim();
  if (stored) {
    return stored;
  }
  if (isNativeApp()) {
    return DEFAULT_SERVER_URL;
  }
  // Navegador servido pela própria API (ou proxy do Vite): mesma origem.
  return '';
}

export function setServerUrl(url: string): void {
  const clean = url.trim().replace(/\/+$/, '');
  if (clean) {
    localStorage.setItem(SERVER_KEY, clean);
  } else {
    localStorage.removeItem(SERVER_KEY);
  }
}

/** Junta o endereço base com o caminho da API. */
export function joinUrl(base: string, path: string): string {
  if (!base) {
    return path;
  }
  return `${base.replace(/\/+$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
}

/**
 * Valida o texto digitado na tela "Servidor".
 * Aceita "192.168.0.15:8000", "http://192.168.0.15:8000" e "https://meu-pc:8000".
 */
export function normalizeServerUrl(input: string): string {
  const raw = input.trim();
  if (!raw) {
    return '';
  }
  const withScheme = /^https?:\/\//i.test(raw) ? raw : `http://${raw}`;
  let url: URL;
  try {
    url = new URL(withScheme);
  } catch {
    return '';
  }
  const port = url.port || '8000';
  return `${url.protocol}//${url.hostname}:${port}`;
}

export function isValidServerUrl(input: string): boolean {
  const normalized = normalizeServerUrl(input);
  if (!normalized) {
    return false;
  }
  try {
    const url = new URL(normalized);
    return url.hostname.length > 0;
  } catch {
    return false;
  }
}

export function getThemeChoice(): ThemeChoice {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === 'light' || stored === 'dark' || stored === 'auto') {
    return stored;
  }
  return 'auto';
}

export function setThemeChoice(choice: ThemeChoice): void {
  localStorage.setItem(THEME_KEY, choice);
  applyTheme(choice);
}

export function applyTheme(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === 'auto') {
    root.removeAttribute('data-theme');
  } else {
    root.setAttribute('data-theme', choice);
  }
}

export function getPreferredLevel(): Level | 'all' {
  const stored = localStorage.getItem(LEVEL_KEY);
  if (stored === 'easy' || stored === 'medium' || stored === 'hard') {
    return stored;
  }
  return 'all';
}

export function setPreferredLevel(level: Level | 'all'): void {
  localStorage.setItem(LEVEL_KEY, level);
}
