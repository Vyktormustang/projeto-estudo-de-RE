import { useCallback, useEffect, useMemo, useState } from 'react';
import { ApiError, api } from '../lib/api';
import { formatSeconds, scoreMessage, tokenizeSentence, toPercent } from '../lib/format';
import { MAX_RECORD_MS, useRecorder } from '../lib/recorder';
import { getPreferredLevel, setPreferredLevel } from '../lib/settings';
import { speakEnglish, stopSpeaking } from '../lib/speech';
import { LEVEL_LABEL } from '../lib/types';
import type { AnalyzeResponse, Level, Sentence, WordScore } from '../lib/types';
import { Banner } from './Banner';
import { MicIcon, NextIcon, PlayIcon, RefreshIcon, StopIcon } from './Icons';
import { ScoreRing } from './ScoreRing';
import { WordSheet } from './WordSheet';

interface PracticeTabProps {
  onOpenSettings: () => void;
}

type LevelFilter = Level | 'all';

const LEVEL_OPTIONS: { value: LevelFilter; label: string }[] = [
  { value: 'all', label: 'Todas' },
  { value: 'easy', label: 'Fácil' },
  { value: 'medium', label: 'Médio' },
  { value: 'hard', label: 'Difícil' },
];

const MIN_RECORD_MS = 700;

export function PracticeTab({ onOpenSettings }: PracticeTabProps) {
  const [sentences, setSentences] = useState<Sentence[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [level, setLevel] = useState<LevelFilter>(() => getPreferredLevel());
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [openWord, setOpenWord] = useState<WordScore | null>(null);
  const [dismissedWarnings, setDismissedWarnings] = useState<string[]>([]);

  const recorder = useRecorder();

  const loadSentences = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await api.sentences();
      setSentences(data.sentences);
    } catch (error) {
      setLoadError(error instanceof ApiError ? error.message : 'Não consegui carregar as frases.');
      setSentences(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSentences();
    return () => {
      void stopSpeaking();
    };
  }, [loadSentences]);

  const list = useMemo(() => {
    if (!sentences) return [];
    return level === 'all' ? sentences : sentences.filter((sentence) => sentence.level === level);
  }, [sentences, level]);

  const current: Sentence | null = list.length > 0 ? list[Math.min(index, list.length - 1)] : null;

  const resetAttempt = useCallback(() => {
    setResult(null);
    setAnalysisError(null);
    setDismissedWarnings([]);
    recorder.reset();
  }, [recorder]);

  const changeLevel = (next: LevelFilter) => {
    setLevel(next);
    setPreferredLevel(next);
    setIndex(0);
    resetAttempt();
  };

  const handleMic = async () => {
    if (!current || analyzing) return;

    if (recorder.isRecording) {
      recorder.stop();
      return;
    }

    resetAttempt();
    setSpeechError(null);

    const recording = await recorder.start(); // resolve quando o usuário para
    if (!recording) return;

    if (recording.durationMs < MIN_RECORD_MS) {
      setAnalysisError(
        'A gravação ficou curta demais (menos de 1 segundo). Toque no microfone, leia a frase inteira e toque de novo para parar.',
      );
      return;
    }

    setAnalyzing(true);
    try {
      const analysis = await api.analyze(recording.blob, current.id);
      setResult(analysis);
      setDismissedWarnings([]);
    } catch (error) {
      setAnalysisError(error instanceof ApiError ? error.message : 'Não consegui analisar o áudio.');
    } finally {
      setAnalyzing(false);
    }
  };

  const nextSentence = () => {
    if (list.length === 0) return;
    resetAttempt();
    setIndex((previous) => (previous + 1) % list.length);
  };

  const playReference = async () => {
    if (!current) return;
    setSpeechError(null);
    const text = result?.sentence_text ?? current.text;
    const error = await speakEnglish(text, { rate: 0.9 });
    if (error) setSpeechError(error);
  };

  if (loading) {
    return (
      <div className="practice">
        <div className="skeleton skeleton--card" />
        <p className="muted center">Carregando as frases do servidor...</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="practice">
        <Banner
          tone="error"
          title="Servidor indisponível"
          action={
            <div className="banner__buttons">
              <button type="button" className="button button--primary button--small" onClick={() => void loadSentences()}>
                <RefreshIcon size={18} /> Tentar de novo
              </button>
              <button type="button" className="button button--ghost button--small" onClick={onOpenSettings}>
                Abrir configurações
              </button>
            </div>
          }
        >
          {loadError}
        </Banner>
        <p className="muted small">
          Dica: no celular, o endereço do servidor precisa ser o IP do PC na mesma rede Wi‑Fi
          (ex.: <code>http://192.168.0.15:8000</code>).
        </p>
      </div>
    );
  }

  if (!current) {
    return (
      <div className="practice">
        <Banner tone="warning" title="Sem frases neste nível">
          Escolha outro nível para começar a praticar.
        </Banner>
        <div className="level-selector">
          {LEVEL_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`chip ${level === option.value ? 'chip--active' : ''}`}
              onClick={() => changeLevel(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

  const tokens = tokenizeSentence(current.text);
  const visibleWarnings = (result?.warnings ?? []).filter((warning) => !dismissedWarnings.includes(warning));
  const isRecording = recorder.isRecording;
  const isBusy = recorder.status === 'requesting' || recorder.status === 'processing' || analyzing;

  return (
    <div className="practice">
      {/* ---------------- seletor de nível ---------------- */}
      <div className="level-selector" role="group" aria-label="Nível de dificuldade">
        {LEVEL_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`chip ${level === option.value ? 'chip--active' : ''}`}
            aria-pressed={level === option.value}
            onClick={() => changeLevel(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* ---------------- cartão da frase ---------------- */}
      <section className="card sentence-card" aria-live="polite">
        <header className="sentence-card__header">
          <span className={`badge badge--${current.level}`}>{LEVEL_LABEL[current.level]}</span>
          <span className="muted small">
            {index + 1} de {list.length}
          </span>
        </header>

        {result ? (
          <>
            <p className="sentence-card__words" lang="en">
              {tokens.map((token, tokenIndex) => {
                const word = result.words[tokenIndex];
                if (!word) {
                  return <span key={`${token.word}-${tokenIndex}`}>{token.word} </span>;
                }
                return (
                  <span key={`${token.word}-${tokenIndex}`}>
                    <button
                      type="button"
                      className={`word word--${word.color}`}
                      onClick={() => setOpenWord(word)}
                      title={`${toPercent(word.score)}% — toque para ver os sons`}
                    >
                      {token.word}
                    </button>
                    {token.trailing ? <span className="sentence-card__punct">{token.trailing}</span> : null}{' '}
                  </span>
                );
              })}
            </p>
            <p className="sentence-card__hint">Toque em qualquer palavra para ver os sons.</p>
          </>
        ) : (
          <>
            <p className="sentence-card__text" lang="en">
              {current.text}
            </p>
            <p className="sentence-card__hint">{current.focus}</p>
          </>
        )}

        <div className="legend" aria-label="Legenda das cores">
          <span className="legend__item legend__item--green">correto</span>
          <span className="legend__item legend__item--yellow">quase</span>
          <span className="legend__item legend__item--red">ajustar</span>
        </div>
      </section>

      {/* ---------------- resultado ---------------- */}
      {result ? (
        <section className="card result-card">
          <div className="result-card__score">
            <ScoreRing score={result.overall_score} color={result.overall_color} />
            <div>
              <h2 className="result-card__message">{scoreMessage(result.overall_score)}</h2>
              <p className="muted small">
                {result.words.length} palavras · {result.duration_seconds.toFixed(1)}s de fala
              </p>
              {result.transcript ? (
                <p className="muted small">
                  O que eu entendi: <span lang="en">“{result.transcript}”</span>
                </p>
              ) : (
                <p className="muted small">Não entendi nenhuma palavra nesta gravação.</p>
              )}
            </div>
          </div>

          {visibleWarnings.length > 0 ? (
            <Banner
              tone={result.warnings.some((w) => w.includes('demonstração')) ? 'info' : 'warning'}
              title="Observações"
              onClose={() => setDismissedWarnings(result.warnings)}
            >
              <span className="banner__list">
                {visibleWarnings.map((warning) => (
                  <span key={warning}>{warning}</span>
                ))}
              </span>
            </Banner>
          ) : null}
        </section>
      ) : null}

      {/* ---------------- erros ---------------- */}
      {recorder.error ? (
        <Banner tone="error" title="Microfone" onClose={recorder.reset}>
          {recorder.error}
        </Banner>
      ) : null}
      {analysisError ? (
        <Banner tone="error" title="Não deu para analisar" onClose={() => setAnalysisError(null)}>
          {analysisError}
        </Banner>
      ) : null}
      {speechError ? (
        <Banner tone="warning" title="Voz de referência" onClose={() => setSpeechError(null)}>
          {speechError}
        </Banner>
      ) : null}

      {/* ---------------- controles ---------------- */}
      <div className="controls">
        {isBusy ? (
          <div className="controls__busy">
            <span className="spinner" aria-hidden="true" />
            <span>{analyzing ? 'Analisando sua pronúncia...' : 'Preparando o microfone...'}</span>
          </div>
        ) : result ? (
          <div className="controls__row">
            <button type="button" className="button button--primary" onClick={() => void playReference()}>
              <PlayIcon size={20} /> Ouvir referência
            </button>
            <button type="button" className="button button--ghost" onClick={resetAttempt}>
              <RefreshIcon size={20} /> Tentar de novo
            </button>
            <button type="button" className="button button--secondary" onClick={nextSentence}>
              <NextIcon size={20} /> Próxima frase
            </button>
          </div>
        ) : (
          <>
            <button
              type="button"
              className={`mic-button ${isRecording ? 'mic-button--recording' : ''}`}
              onClick={() => void handleMic()}
              aria-label={isRecording ? 'Parar gravação' : 'Gravar minha leitura'}
            >
              {isRecording ? <StopIcon size={38} /> : <MicIcon size={40} />}
              {isRecording ? <span className="mic-button__timer">{formatSeconds(recorder.elapsedMs)}</span> : null}
            </button>
            <p className="controls__hint">
              {isRecording
                ? 'Gravando... toque para parar'
                : 'Toque no microfone e leia a frase em voz alta'}
            </p>
            <p className="controls__sub">
              Máximo de {MAX_RECORD_MS / 1000} segundos · microfone só grava quando você toca
            </p>
            <div className="controls__row controls__row--compact">
              <button type="button" className="button button--ghost button--small" onClick={() => void playReference()}>
                <PlayIcon size={18} /> Ouvir primeiro
              </button>
              <button type="button" className="button button--ghost button--small" onClick={nextSentence}>
                <NextIcon size={18} /> Outra frase
              </button>
            </div>
          </>
        )}
      </div>

      {openWord ? <WordSheet word={openWord} onClose={() => setOpenWord(null)} /> : null}
    </div>
  );
}
