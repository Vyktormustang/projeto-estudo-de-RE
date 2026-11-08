/**
 * Gravação do microfone com MediaRecorder.
 *
 * Cuidados que evitam 90% dos problemas no celular:
 *  - escolher um formato suportado (Android grava webm/opus, iPhone grava mp4);
 *  - parar TODAS as faixas (senão o ícone de microfone fica aceso e a próxima
 *    gravação falha);
 *  - limite de 30 s por gravação (mantém a análise rápida);
 *  - mensagens de erro em português para permissão negada, sem microfone etc.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export type RecorderStatus = 'idle' | 'requesting' | 'recording' | 'processing';

export interface RecordingResult {
  blob: Blob;
  mimeType: string;
  durationMs: number;
}

/** Limite de segurança: uma frase nunca passa disso. */
export const MAX_RECORD_MS = 30_000;

const CANDIDATE_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/ogg',
  'audio/mp4',
  'audio/mp4;codecs=mp4a.40.2',
  'audio/aac',
  'audio/wav',
];

export function pickMimeType(): string {
  if (typeof MediaRecorder === 'undefined') {
    return '';
  }
  for (const type of CANDIDATE_TYPES) {
    try {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    } catch {
      // alguns WebViews lançam exceção: seguimos para o próximo
    }
  }
  return '';
}

export function microphoneErrorMessage(error: unknown): string {
  const name = (error as { name?: string })?.name ?? '';
  switch (name) {
    case 'NotAllowedError':
    case 'PermissionDeniedError':
    case 'SecurityError':
      return (
        'O microfone está bloqueado. Libere a permissão de microfone para o SpeakNatural ' +
        '(no Android: Ajustes › Apps › SpeakNatural › Permissões › Microfone).'
      );
    case 'NotFoundError':
    case 'DevicesNotFoundError':
      return 'Não encontrei um microfone neste aparelho. Conecte um microfone e tente de novo.';
    case 'NotReadableError':
    case 'TrackStartError':
      return 'O microfone está sendo usado por outro app. Feche o outro app e tente de novo.';
    case 'OverconstrainedError':
      return 'O microfone não aceitou a configuração pedida. Tente novamente.';
    default:
      return 'Não consegui abrir o microfone. Verifique as permissões do app e tente de novo.';
  }
}

export function useRecorder() {
  const [status, setStatus] = useState<RecorderStatus>('idle');
  const [elapsedMs, setElapsedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef(0);
  const timerRef = useRef<number | null>(null);
  const resolveRef = useRef<((value: RecordingResult | null) => void) | null>(null);
  const autoStopRef = useRef<number | null>(null);

  const cleanup = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (autoStopRef.current !== null) {
      window.clearTimeout(autoStopRef.current);
      autoStopRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    recorderRef.current = null;
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const stop = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      setStatus('processing');
      recorder.stop();
    }
  }, []);

  const start = useCallback(async (): Promise<RecordingResult | null> => {
    setError(null);

    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setError(
        'Este navegador não permite gravar áudio. Abra o app no Chrome do Android ou no computador ' +
          'usando http://localhost:8000.',
      );
      return null;
    }
    if (typeof MediaRecorder === 'undefined') {
      setError('Seu navegador não suporta gravação de áudio (MediaRecorder). Atualize o Chrome/WebView.');
      return null;
    }

    setStatus('requesting');
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
    } catch (permissionError) {
      setStatus('idle');
      setError(microphoneErrorMessage(permissionError));
      return null;
    }

    const mimeType = pickMimeType();
    let recorder: MediaRecorder;
    try {
      recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
    } catch {
      stream.getTracks().forEach((track) => track.stop());
      setStatus('idle');
      setError('Não consegui iniciar a gravação neste aparelho. Tente reiniciar o app.');
      return null;
    }

    streamRef.current = stream;
    recorderRef.current = recorder;
    chunksRef.current = [];
    startedAtRef.current = Date.now();
    setElapsedMs(0);

    const result = new Promise<RecordingResult | null>((resolve) => {
      resolveRef.current = resolve;
    });

    recorder.ondataavailable = (event: BlobEvent) => {
      if (event.data && event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    recorder.onerror = () => {
      setError('A gravação falhou no meio. Tente de novo.');
      setStatus('idle');
      resolveRef.current?.(null);
      resolveRef.current = null;
      cleanup();
    };

    recorder.onstop = () => {
      const durationMs = Date.now() - startedAtRef.current;
      const type = recorder.mimeType || mimeType || 'audio/webm';
      const blob = new Blob(chunksRef.current, { type });
      cleanup();
      setStatus('idle');
      resolveRef.current?.(blob.size > 0 ? { blob, mimeType: type, durationMs } : null);
      resolveRef.current = null;
    };

    recorder.start(250); // envia pedaços a cada 250 ms (mais seguro no celular)
    setStatus('recording');

    timerRef.current = window.setInterval(() => {
      setElapsedMs(Date.now() - startedAtRef.current);
    }, 100);

    autoStopRef.current = window.setTimeout(() => {
      if (recorderRef.current && recorderRef.current.state === 'recording') {
        recorderRef.current.stop();
      }
    }, MAX_RECORD_MS);

    return result;
  }, [cleanup]);

  const reset = useCallback(() => setError(null), []);

  return { status, elapsedMs, error, start, stop, reset, isRecording: status === 'recording' };
}
