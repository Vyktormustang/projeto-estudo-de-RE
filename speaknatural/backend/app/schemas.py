"""Contratos JSON da API (Pydantic v2).

Estes modelos geram automaticamente a documentacao OpenAPI em /docs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Color = Literal["green", "yellow", "red"]
Level = Literal["easy", "medium", "hard"]


class Sentence(BaseModel):
    id: str = Field(examples=["m07"])
    text: str = Field(examples=["Could you speak a little more slowly, please?"])
    level: Level
    #: Dica curta em portugues sobre o que treinar nesta frase.
    focus: str
    #: Marca recursos de fala natural usados (contração, linking, gonna...).
    tags: list[str] = Field(default_factory=list)
    #: Numero de palavras "de conteudo" + total, para a UI mostrar dificuldade.
    word_count: int


class SentenceList(BaseModel):
    level: Level | None = None
    total: int
    sentences: list[Sentence]


class PhonemeDetail(BaseModel):
    """Um som dentro de uma palavra."""

    expected: str | None = Field(
        default=None,
        description="Simbolo IPA esperado (null quando foi um som extra que você falou)",
        examples=["iː"],
    )
    heard: str | None = Field(
        default=None,
        description="Simbolo IPA ouvido pelo modelo (null quando o som não apareceu)",
        examples=["ɪ"],
    )
    score: float = Field(ge=0.0, le=1.0, examples=[0.65])
    #: Explicacao curta em portugues (vazia quando o som esta correto).
    tip: str = ""


class WordScore(BaseModel):
    text: str = Field(examples=["speak"])
    normalized: str
    score: float = Field(ge=0.0, le=1.0, examples=[0.72])
    color: Color
    #: 0.0 = não falada / 1.0 = reconhecida pela transcrição.
    presence: float = Field(ge=0.0, le=1.0)
    phonemes: list[PhonemeDetail] = Field(default_factory=list)
    #: Dica em portugues para a palavra inteira.
    tip: str = ""


class AnalyzeResponse(BaseModel):
    attempt_id: int
    sentence_id: str
    sentence_text: str
    level: Level
    transcript: str = Field(description="O que o reconhecedor entendeu da sua fala")
    overall_score: float = Field(ge=0.0, le=1.0)
    overall_color: Color
    words: list[WordScore]
    duration_seconds: float
    created_at: datetime
    #: Avisos em portugues (ex.: gravacao com ruido, modelo em modo demo).
    warnings: list[str] = Field(default_factory=list)


class AttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sentence_id: str
    sentence_text: str
    level: str
    overall_score: float
    created_at: datetime


class HardWord(BaseModel):
    normalized: str
    display: str
    level: str
    attempts: int
    average_score: float
    best_score: float
    last_score: float


class HistoryResponse(BaseModel):
    total_attempts: int
    average_score: float
    best_score: float
    streak_days: int
    attempts: list[AttemptSummary]
    hard_words: list[HardWord]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    database: str
    ffmpeg: bool
    whisper: str
    phonemes: str
    fake_models: bool
    messages: list[str] = Field(default_factory=list)
    server_time: datetime


class ApiError(BaseModel):
    """Formato padrao de erro (sempre com mensagem em portugues)."""

    detail: str = Field(examples=["O áudio ficou curto demais. Segure o botão e leia a frase inteira."])
    code: str = Field(examples=["audio_too_short"])
