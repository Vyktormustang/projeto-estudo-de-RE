import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from '../lib/api';
import { formatDate, pluralAttempts, pluralDays, toPercent } from '../lib/format';
import { LEVEL_LABEL } from '../lib/types';
import type { HistoryResponse, Level } from '../lib/types';
import { Banner } from './Banner';
import { RefreshIcon } from './Icons';

interface HistoryTabProps {
  /** Quando a aba fica visível, recarregamos para mostrar a última tentativa. */
  active: boolean;
  onGoToPractice: () => void;
}

function levelLabel(level: string): string {
  return LEVEL_LABEL[level as Level] ?? level;
}

export function HistoryTab({ active, onGoToPractice }: HistoryTabProps) {
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await api.history(40));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não consegui carregar o histórico.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (active) {
      void load();
    }
  }, [active, load]);

  return (
    <div className="history">
      <div className="section-title">
        <h2>Seu progresso</h2>
        <button type="button" className="icon-button" onClick={() => void load()} aria-label="Atualizar histórico">
          <RefreshIcon size={20} />
        </button>
      </div>

      {error ? (
        <Banner tone="error" title="Histórico indisponível" action={
          <button type="button" className="button button--primary button--small" onClick={() => void load()}>
            Tentar de novo
          </button>
        }>
          {error}
        </Banner>
      ) : null}

      {loading && !data ? <div className="skeleton skeleton--card" /> : null}

      {data ? (
        <>
          <div className="stats">
            <div className="stat-card">
              <strong>{data.total_attempts}</strong>
              <span>{pluralAttempts(data.total_attempts)}</span>
            </div>
            <div className="stat-card">
              <strong>{toPercent(data.average_score)}%</strong>
              <span>média geral</span>
            </div>
            <div className="stat-card">
              <strong>{data.streak_days}</strong>
              <span>{pluralDays(data.streak_days)}</span>
            </div>
          </div>

          {data.total_attempts === 0 ? (
            <div className="empty-state">
              <p>Você ainda não gravou nenhuma frase.</p>
              <button type="button" className="button button--primary" onClick={onGoToPractice}>
                Começar a praticar
              </button>
            </div>
          ) : (
            <>
              <section className="card">
                <h3 className="card__title">Palavras mais difíceis</h3>
                <p className="muted small">
                  Ordenadas pela sua média. Toque em “Praticar” e repita as frases com essas palavras.
                </p>
                <ul className="hard-words">
                  {data.hard_words.map((word) => {
                    const percent = toPercent(word.average_score);
                    const tone = percent >= 85 ? 'green' : percent >= 50 ? 'yellow' : 'red';
                    return (
                      <li key={`${word.normalized}-${word.level}`} className="hard-word">
                        <div className="hard-word__top">
                          <span className="hard-word__word" lang="en">
                            {word.display}
                          </span>
                          <span className={`badge badge--${word.level}`}>{levelLabel(word.level)}</span>
                          <span className={`hard-word__score hard-word__score--${tone}`}>{percent}%</span>
                        </div>
                        <div className="bar">
                          <span className={`bar__fill bar__fill--${tone}`} style={{ width: `${Math.max(percent, 3)}%` }} />
                        </div>
                        <span className="muted tiny">
                          {pluralAttempts(word.attempts)} · melhor {toPercent(word.best_score)}% · última{' '}
                          {toPercent(word.last_score)}%
                        </span>
                      </li>
                    );
                  })}
                  {data.hard_words.length === 0 ? <li className="muted small">Nada por aqui ainda.</li> : null}
                </ul>
              </section>

              <section className="card">
                <h3 className="card__title">Últimas tentativas</h3>
                <ul className="attempts">
                  {data.attempts.map((attempt) => {
                    const percent = toPercent(attempt.overall_score);
                    const tone = percent >= 85 ? 'green' : percent >= 50 ? 'yellow' : 'red';
                    return (
                      <li key={attempt.id} className="attempt">
                        <span className={`attempt__dot attempt__dot--${tone}`} aria-hidden="true" />
                        <div className="attempt__text">
                          <span lang="en">{attempt.sentence_text}</span>
                          <span className="muted tiny">
                            {formatDate(attempt.created_at)} · {levelLabel(attempt.level)}
                          </span>
                        </div>
                        <span className={`attempt__score attempt__score--${tone}`}>{percent}%</span>
                      </li>
                    );
                  })}
                </ul>
              </section>
            </>
          )}
        </>
      ) : null}
    </div>
  );
}
