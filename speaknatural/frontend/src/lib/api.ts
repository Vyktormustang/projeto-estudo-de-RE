/**
 * Cliente da API do SpeakNatural.
 *
 * Todas as mensagens de erro saem daqui já em português e prontas para a tela.
 * Códigos de erro do backend (campo `code`): sentence_not_found, empty_audio,
 * audio_too_short, audio_too_long, upload_too_big, no_speech,
 * audio_convert_failed, ffmpeg_missing, models_unavailable, models_disabled.
 */

import { getServerUrl, joinUrl } from './settings';
import type { AnalyzeResponse, HealthResponse, HistoryResponse, Level, SentenceList } from './types';

/** Erro com mensagem amigável + código (para a UI decidir o que fazer). */
export class ApiError extends Error {
  code: string;
  offline: boolean;

  constructor(message: string, code = 'error', offline = false) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.offline = offline;
  }
}

const OFFLINE_MESSAGE =
  'Não consegui falar com o servidor. Verifique se o servidor está ligado no PC e se o endereço ' +
  'em “Servidor” está correto (o celular precisa estar no mesmo Wi-Fi).';

interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: BodyInit | null;
  timeoutMs?: number;
  signal?: AbortSignal;
  /** Força um endereço (usado no botão "Testar conexão"). */
  baseUrl?: string;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body = null, timeoutMs = 30_000, signal, baseUrl } = options;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const abortAll = () => controller.abort();
  signal?.addEventListener('abort', abortAll);

  let response: Response;
  try {
    response = await fetch(joinUrl(baseUrl ?? getServerUrl(), path), {
      method,
      body,
      signal: controller.signal,
      headers: method === 'POST' ? undefined : { Accept: 'application/json' },
    });
  } catch (error) {
    if (signal?.aborted) {
      throw new ApiError('Envio cancelado.', 'aborted');
    }
    if ((error as Error)?.name === 'AbortError') {
      throw new ApiError(
        'O servidor demorou demais para responder. Na primeira análise ele baixa os modelos de IA ' +
          '(~2 GB); aguarde e tente de novo. Se repetir, veja “Problemas comuns” no README.',
        'timeout',
        true,
      );
    }
    throw new ApiError(OFFLINE_MESSAGE, 'offline', true);
  } finally {
    window.clearTimeout(timer);
    signal?.removeEventListener('abort', abortAll);
  }

  if (!response.ok) {
    let detail = `O servidor respondeu com erro ${response.status}.`;
    let code = `http_${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: unknown; code?: unknown };
      if (typeof payload.detail === 'string' && payload.detail.trim()) {
        detail = payload.detail;
      }
      if (typeof payload.code === 'string') {
        code = payload.code;
      }
    } catch {
      // resposta sem JSON (proxy, 502...): mantém a mensagem genérica
    }
    if (response.status === 404 && code.startsWith('http_')) {
      detail = 'Servidor encontrado, mas o endereço da API está errado. Confira o endereço em “Servidor”.';
    }
    throw new ApiError(detail, code, response.status >= 500);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError('O servidor respondeu em um formato inesperado.', 'bad_json');
  }
}

export const api = {
  health(): Promise<HealthResponse> {
    return request<HealthResponse>('/health', { timeoutMs: 8_000 });
  },

  /** Testa um endereço digitado, sem precisar salvar antes. */
  healthAt(baseUrl: string): Promise<HealthResponse> {
    return request<HealthResponse>('/health', { timeoutMs: 8_000, baseUrl });
  },

  sentences(level?: Level): Promise<SentenceList> {
    const query = level ? `?level=${level}` : '';
    return request<SentenceList>(`/sentences${query}`);
  },

  history(limit = 30): Promise<HistoryResponse> {
    return request<HistoryResponse>(`/history?limit=${limit}`);
  },

  /**
   * Envia o áudio gravado.
   * timeout de 5 min: a primeira análise carrega/baixa os modelos (~2 GB).
   */
  analyze(audio: Blob, sentenceId: string, signal?: AbortSignal): Promise<AnalyzeResponse> {
    const form = new FormData();
    form.append('audio', audio, `leitura.${extensionFor(audio.type)}`);
    form.append('sentence_id', sentenceId);
    return request<AnalyzeResponse>('/analyze', {
      method: 'POST',
      body: form,
      timeoutMs: 300_000,
      signal,
    });
  },
};

export function extensionFor(mimeType: string): string {
  const type = (mimeType || '').split(';')[0].trim().toLowerCase();
  if (type.includes('ogg')) return 'ogg';
  if (type.includes('mp4') || type.includes('m4a') || type.includes('aac')) return 'm4a';
  if (type.includes('wav')) return 'wav';
  if (type.includes('mpeg') || type.includes('mp3')) return 'mp3';
  return 'webm';
}
