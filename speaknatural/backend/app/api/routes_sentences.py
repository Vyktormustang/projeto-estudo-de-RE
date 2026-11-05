"""GET /sentences?level=easy|medium|hard - lista das ~40 frases embutidas."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from ..data.sentences import LEVELS, by_level
from ..schemas import Sentence, SentenceList

router = APIRouter(tags=["frases"])


@router.get(
    "/sentences",
    response_model=SentenceList,
    summary="Lista as frases de prática (filtro opcional por nível)",
)
def list_sentences(
    level: Literal["easy", "medium", "hard"] | None = Query(
        default=None,
        description="Filtra por nível. Vazio = todos os níveis.",
    ),
) -> SentenceList:
    if level is not None and level not in LEVELS:
        raise HTTPException(status_code=422, detail="Nível inválido. Use easy, medium ou hard.")

    items = by_level(level)
    return SentenceList(
        level=level,
        total=len(items),
        sentences=[Sentence(**item) for item in items],
    )
