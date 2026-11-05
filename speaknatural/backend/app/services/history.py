"""Gravacao e leitura do historico (SQLite).

Duas coisas acontecem quando uma analise termina:
  1. gravamos a tentativa inteira (frase + nota + notas por palavra);
  2. atualizamos `word_stats`, que e o resumo usado na aba Historico
     ("palavras mais dificeis").
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Attempt, AttemptWord, WordStat
from .analyzer import AnalysisOutput
from .text import normalize_word

logger = logging.getLogger(__name__)


def save_attempt(
    db: Session,
    sentence: dict[str, Any],
    analysis: AnalysisOutput,
    transcript: str,
) -> Attempt:
    """Grava a tentativa e atualiza os agregados. Devolve o Attempt salvo."""
    attempt = Attempt(
        sentence_id=sentence["id"],
        sentence_text=sentence["text"],
        level=sentence["level"],
        transcript=transcript[:600],
        overall_score=analysis.overall_score,
        duration_seconds=analysis.duration_seconds,
        engine_version=analysis.engine_version,
    )
    for position, word in enumerate(analysis.words):
        attempt.words.append(
            AttemptWord(
                position=position,
                text=word.text,
                normalized=word.normalized or normalize_word(word.text),
                score=word.score,
                color=word.color,
                presence=word.presence,
                phonemes=[
                    {
                        "expected": p.expected,
                        "heard": p.heard,
                        "score": p.score,
                        "tip": p.tip,
                    }
                    for p in word.phonemes
                ],
            )
        )
    db.add(attempt)
    _update_word_stats(db, sentence["level"], analysis)
    db.commit()
    db.refresh(attempt)
    logger.info(
        "Tentativa #%s salva (frase %s, nota %.2f)",
        attempt.id, attempt.sentence_id, attempt.overall_score,
    )
    return attempt


def _update_word_stats(db: Session, level: str, analysis: AnalysisOutput) -> None:
    for word in analysis.words:
        normalized = word.normalized or normalize_word(word.text)
        if not normalized:
            continue
        stat = db.scalar(
            select(WordStat).where(WordStat.normalized == normalized, WordStat.level == level)
        )
        if stat is None:
            stat = WordStat(
                normalized=normalized,
                display=word.text,
                level=level,
                attempts=0,
                total_score=0.0,
                best_score=0.0,
                last_score=0.0,
            )
            db.add(stat)
        stat.attempts += 1
        stat.total_score += word.score
        stat.best_score = max(stat.best_score, word.score)
        stat.last_score = word.score


def attempts_list(db: Session, limit: int = 30) -> list[Attempt]:
    return list(
        db.scalars(select(Attempt).order_by(Attempt.created_at.desc(), Attempt.id.desc()).limit(limit))
    )


def totals(db: Session) -> tuple[int, float, float]:
    """(quantidade de tentativas, media, melhor nota)."""
    row = db.execute(
        select(func.count(Attempt.id), func.avg(Attempt.overall_score), func.max(Attempt.overall_score))
    ).one()
    count = int(row[0] or 0)
    average = round(float(row[1] or 0.0), 4)
    best = round(float(row[2] or 0.0), 4)
    return count, average, best


def streak_days(db: Session) -> int:
    """Dias consecutivos treinando (conta a partir de hoje ou de ontem)."""
    dates = db.scalars(select(Attempt.created_at).order_by(Attempt.created_at.desc())).all()
    if not dates:
        return 0
    unique_days: list[date] = []
    for moment in dates:
        day = moment.date() if hasattr(moment, "date") else moment
        if day not in unique_days:
            unique_days.append(day)
    today = date.today()
    streak = 0
    expected = today if unique_days[0] == today else today - timedelta(days=1)
    for day in unique_days:
        if day == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        elif day < expected:
            break
    return streak


def hardest_words(db: Session, limit: int = 12, level: str | None = None) -> list[WordStat]:
    """Palavras com pior media (e pelo menos 1 tentativa)."""
    query = select(WordStat).where(WordStat.attempts >= 1)
    if level:
        query = query.where(WordStat.level == level)
    rows = list(db.scalars(query))
    rows.sort(key=lambda stat: (stat.average_score, -stat.last_score, -stat.attempts))
    return rows[:limit]
