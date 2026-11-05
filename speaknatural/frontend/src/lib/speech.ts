/**
 * Voz de referência ("ouvir a frase como um nativo"). Tudo offline, nada de API paga.
 *
 * Dois motores, escolhidos automaticamente:
 *
 *  1. NO APK (Android): plugin nativo @capacitor-community/text-to-speech, que fala
 *     com o motor de voz do Android (Google Text-to-Speech). Precisa dele porque o
 *     WebView do Android NÃO implementa o speechSynthesis do navegador.
 *
 *  2. NO NAVEGADOR (PC): Web Speech API (`window.speechSynthesis`), escolhendo a
 *     melhor voz em inglês instalada (en-US, de preferência "Natural"/"Google").
 *
 * Em qualquer um dos casos, se o aparelho não tiver voz em inglês, devolvemos uma
 * mensagem em português explicando o que instalar (em vez de falhar em silêncio).
 */

import { Capacitor } from '@capacitor/core';
import { TextToSpeech } from '@capacitor-community/text-to-speech';

export interface SpeakOptions {
  rate?: number; // 1 = normal; 0.85–0.9 = um pouco mais devagar (bom para treinar)
  lang?: string;
}

const NO_ENGLISH_VOICE =
  'Este aparelho não tem voz em inglês instalada. No Android: instale o “Google Text-to-Speech” ' +
  'e depois Ajustes › Sistema › Idiomas › Saída de texto para fala › instale “English (United States)”.';

const SPEAK_FAILED =
  'Não consegui tocar a voz de referência. Verifique o volume do aparelho e a voz em inglês instalada.';

export function isNativeApp(): boolean {
  try {
    return typeof Capacitor?.isNativePlatform === 'function' && Capacitor.isNativePlatform();
  } catch {
    return false;
  }
}

export function isSpeechSupported(): boolean {
  if (isNativeApp()) {
    return true; // o plugin nativo cuida disso
  }
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

/* -------------------------------------------------------------------------- */
/*  Motor nativo (APK)                                                        */
/* -------------------------------------------------------------------------- */

function pickEnglishLanguage(languages: string[]): string | null {
  const english = languages.filter((language) => language.toLowerCase().startsWith('en'));
  if (english.length === 0) {
    return null;
  }
  const us = english.find((language) => language.replace('-', '_').toLowerCase().startsWith('en_us'));
  return us ?? english[0];
}

async function speakNative(text: string, rate: number): Promise<string | null> {
  try {
    await TextToSpeech.stop().catch(() => undefined);
  } catch {
    // se não havia nada tocando, seguimos
  }

  let language = 'en-US';
  try {
    const { languages } = await TextToSpeech.getSupportedLanguages();
    const chosen = pickEnglishLanguage(languages ?? []);
    if (!chosen) {
      return NO_ENGLISH_VOICE;
    }
    language = chosen;
  } catch {
    // sem lista de idiomas: tentamos en-US direto
  }

  try {
    await TextToSpeech.speak({
      text,
      lang: language,
      rate,
      pitch: 1.0,
      volume: 1.0,
      category: 'ambient',
    });
    return null;
  } catch {
    // segunda tentativa: rate padrão (alguns motores rejeitam taxas extremas)
    try {
      await TextToSpeech.speak({ text, lang: language, pitch: 1.0, volume: 1.0 });
      return null;
    } catch {
      return SPEAK_FAILED;
    }
  }
}

/* -------------------------------------------------------------------------- */
/*  Motor do navegador                                                        */
/* -------------------------------------------------------------------------- */

export function listVoices(): SpeechSynthesisVoice[] {
  if (!isSpeechSupported() || isNativeApp()) {
    return [];
  }
  try {
    return window.speechSynthesis.getVoices();
  } catch {
    return [];
  }
}

export function pickEnglishVoice(voices: SpeechSynthesisVoice[] = listVoices()): SpeechSynthesisVoice | null {
  const english = voices.filter((voice) => voice.lang.toLowerCase().startsWith('en'));
  if (english.length === 0) {
    return null;
  }
  const score = (voice: SpeechSynthesisVoice): number => {
    let value = 0;
    const lang = voice.lang.toLowerCase();
    if (lang === 'en-us' || lang === 'en_us') value += 60;
    else if (lang.startsWith('en-gb') || lang.startsWith('en_')) value += 40;
    else value += 20;
    const name = voice.name.toLowerCase();
    if (name.includes('google')) value += 25;
    if (name.includes('natural') || name.includes('neural')) value += 30;
    if (name.includes('samantha') || name.includes('aria') || name.includes('jenny')) value += 15;
    if (voice.localService) value += 5;
    return value;
  };
  return [...english].sort((a, b) => score(b) - score(a))[0] ?? null;
}

/** Espera a lista de vozes carregar (no Chrome ela chega de forma assíncrona). */
export function waitForVoices(timeoutMs = 1500): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    if (!isSpeechSupported() || isNativeApp()) {
      resolve([]);
      return;
    }
    const synthesis = window.speechSynthesis;
    const existing = synthesis.getVoices();
    if (existing.length > 0) {
      resolve(existing);
      return;
    }
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      synthesis.onvoiceschanged = null;
      resolve(synthesis.getVoices());
    };
    synthesis.onvoiceschanged = finish;
    window.setTimeout(finish, timeoutMs);
  });
}

async function speakWeb(text: string, rate: number, lang: string): Promise<string | null> {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    return 'Este navegador não tem voz sintetizada. No celular, use o APK do SpeakNatural.';
  }

  const voices = await waitForVoices();
  const voice = pickEnglishVoice(voices);

  window.speechSynthesis.cancel(); // evita falas sobrepostas

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = voice?.lang ?? lang;
  utterance.rate = rate;
  utterance.pitch = 1;
  utterance.volume = 1;
  if (voice) {
    utterance.voice = voice;
  }

  return new Promise<string | null>((resolve) => {
    let settled = false;
    const finish = (message: string | null) => {
      if (settled) return;
      settled = true;
      resolve(message);
    };
    utterance.onend = () => finish(null);
    utterance.onerror = (event) => {
      const reason = (event as SpeechSynthesisErrorEvent).error;
      if (reason === 'interrupted' || reason === 'canceled') {
        finish(null);
      } else if (reason === 'not-allowed') {
        finish('O navegador bloqueou o áudio. Toque na tela e tente de novo.');
      } else {
        finish(SPEAK_FAILED);
      }
    };
    try {
      window.speechSynthesis.speak(utterance);
    } catch {
      finish(SPEAK_FAILED);
    }
    // Rede de segurança: alguns navegadores não disparam onend.
    window.setTimeout(() => finish(null), Math.max(4000, text.length * 90 + 2000));
  });
}

/* -------------------------------------------------------------------------- */
/*  API pública                                                              */
/* -------------------------------------------------------------------------- */

/** Fala o texto em inglês. Devolve uma mensagem de erro em português (ou null). */
export async function speakEnglish(text: string, options: SpeakOptions = {}): Promise<string | null> {
  const { rate = 0.9, lang = 'en-US' } = options;
  const trimmed = text.trim();
  if (!trimmed) {
    return null;
  }
  if (isNativeApp()) {
    return speakNative(trimmed, rate);
  }
  return speakWeb(trimmed, rate, lang);
}

export async function stopSpeaking(): Promise<void> {
  if (isNativeApp()) {
    try {
      await TextToSpeech.stop();
    } catch {
      // nada tocando
    }
    return;
  }
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}
