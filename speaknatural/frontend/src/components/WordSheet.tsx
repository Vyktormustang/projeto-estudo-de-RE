import { useEffect, useState } from 'react';
import { colorLabel, toPercent } from '../lib/format';
import { speakEnglish, stopSpeaking } from '../lib/speech';
import type { WordScore } from '../lib/types';
import { CloseIcon, SpeakerIcon } from './Icons';

interface WordSheetProps {
  word: WordScore;
  onClose: () => void;
}

/**
 * Painel que abre ao tocar em uma palavra: mostra a palavra dividida em sons,
 * o som esperado x o som ouvido, a nota de cada som e uma dica em português.
 */
export function WordSheet({ word, onClose }: WordSheetProps) {
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    document.body.classList.add('sheet-open');
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.classList.remove('sheet-open');
      void stopSpeaking();
    };
  }, [onClose]);

  const playWord = async () => {
    setSpeechError(null);
    setSpeaking(true);
    const error = await speakEnglish(word.text, { rate: 0.75 });
    setSpeaking(false);
    if (error) setSpeechError(error);
  };

  const wrongSounds = word.phonemes.filter((phoneme) => phoneme.score < 0.999);

  return (
    <div className="sheet" role="dialog" aria-modal="true" aria-label={`Detalhes da palavra ${word.text}`}>
      <button type="button" className="sheet__backdrop" onClick={onClose} aria-label="Fechar" />
      <div className="sheet__panel">
        <header className="sheet__header">
          <div>
            <p className="sheet__eyebrow">Detalhes da palavra</p>
            <h2 className="sheet__title">{word.text}</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Fechar detalhes">
            <CloseIcon size={22} />
          </button>
        </header>

        <div className={`word-score word-score--${word.color}`}>
          <strong>{toPercent(word.score)}%</strong>
          <span>{colorLabel(word.color)}</span>
          {word.presence === 0 ? <em>não apareceu na gravação</em> : null}
        </div>

        <p className="sheet__tip">{word.tip}</p>

        <button type="button" className="button button--ghost button--small" onClick={playWord} disabled={speaking}>
          <SpeakerIcon size={18} />
          {speaking ? 'Tocando...' : 'Ouvir esta palavra'}
        </button>
        {speechError ? <p className="sheet__speech-error">{speechError}</p> : null}

        <h3 className="sheet__section-title">Som por som</h3>

        {word.phonemes.length === 0 ? (
          <p className="sheet__empty">
            Não consegui detalhar os sons desta palavra. Grave de novo falando um pouco mais alto — ou toque em
            “Ouvir esta palavra” para praticar.
          </p>
        ) : (
          <ul className="phoneme-list">
            {word.phonemes.map((phoneme, index) => {
              const soundColor =
                phoneme.score >= 0.85 ? 'green' : phoneme.score >= 0.5 ? 'yellow' : 'red';
              return (
                <li key={`${phoneme.expected ?? 'extra'}-${phoneme.heard ?? 'miss'}-${index}`} className="phoneme-row">
                  <div className="phoneme-row__sounds">
                    <div className="phoneme-box">
                      <span className="phoneme-box__label">Esperado</span>
                      <span className="phoneme-box__symbol">/{phoneme.expected ?? '—'}/</span>
                    </div>
                    <span className="phoneme-row__arrow" aria-hidden="true">
                      →
                    </span>
                    <div className={`phoneme-box phoneme-box--${soundColor}`}>
                      <span className="phoneme-box__label">Você falou</span>
                      <span className="phoneme-box__symbol">
                        {phoneme.heard ? `/${phoneme.heard}/` : 'não saiu'}
                      </span>
                    </div>
                    <span className={`phoneme-pill phoneme-pill--${soundColor}`}>{toPercent(phoneme.score)}%</span>
                  </div>
                  {phoneme.tip ? <p className="phoneme-row__tip">{phoneme.tip}</p> : null}
                </li>
              );
            })}
          </ul>
        )}

        {wrongSounds.length === 0 && word.phonemes.length > 0 ? (
          <p className="sheet__all-good">Todos os sons desta palavra ficaram bons. Repita para fixar!</p>
        ) : null}

        <button type="button" className="button button--primary sheet__done" onClick={onClose}>
          Entendi
        </button>
      </div>
    </div>
  );
}
