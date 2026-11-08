"""GET /history - tentativas anteriores + palavras mais dificeis."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import AttemptSummary, HardWord, HistoryResponse
from ..services import history

router = APIRouter(tags=["histórico"])


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Histórico de tentativas e as palavras que mais te derrubam",
)
def read_history(
    limit: int = Query(default=30, ge=1, le=200, description="Quantas tentativas retornar"),
    hard_words: int = Query(default=12, ge=1, le=50, description="Quantas palavras difíceis retornar"),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    total, average, best = history.totals(db)
    return HistoryResponse(
        total_attempts=total,
        average_score=average,
        best_score=best,
        streak_days=history.streak_days(db),
        attempts=[AttemptSummary.model_validate(a) for a in history.attempts_list(db, limit)],
        hard_words=[
            HardWord(
                normalized=stat.normalized,
                display=stat.display,
                level=stat.level,
                attempts=stat.attempts,
                average_score=stat.average_score,
                best_score=round(stat.best_score, 4),
                last_score=round(stat.last_score, 4),
            )
            for stat in history.hardest_words(db, hard_words)
        ],
    )
