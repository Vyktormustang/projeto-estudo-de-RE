"""Tabelas do SQLite.

Tres tabelas simples e normalizadas, faceis de estender depois
(conversa, contas de usuario, etc. entram como tabelas novas):

    attempts        uma tentativa de leitura (uma frase, uma data)
    attempt_words   uma linha por palavra da frase, com score e cor
    word_stats      agregado por palavra (para "palavras mais dificeis")
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    """Agora, em UTC com timezone (evita confusao de fuso no histórico)."""
    return datetime.now(timezone.utc)


class Attempt(Base):
    """Uma tentativa: a frase, o audio transcrito, a nota geral e a data."""

    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sentence_id: Mapped[str] = mapped_column(String(16), index=True)
    sentence_text: Mapped[str] = mapped_column(String(400))
    level: Mapped[str] = mapped_column(String(16), index=True)
    transcript: Mapped[str] = mapped_column(String(600), default="")
    overall_score: Mapped[float] = mapped_column(Float, index=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    engine_version: Mapped[str] = mapped_column(String(16), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    words: Mapped[list["AttemptWord"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="AttemptWord.position",
        lazy="selectin",
    )


class AttemptWord(Base):
    """Score de UMA palavra dentro de UMA tentativa."""

    __tablename__ = "attempt_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String(80))
    normalized: Mapped[str] = mapped_column(String(80), index=True)
    score: Mapped[float] = mapped_column(Float)
    color: Mapped[str] = mapped_column(String(8))  # green | yellow | red
    #: Detalhe dos fonemas (lista de {expected, heard, score, tip}) em JSON.
    phonemes: Mapped[list] = mapped_column(JSON, default=list)
    #: 0.0 = palavra nao falada, 0.5 = parecida, 1.0 = reconhecida.
    presence: Mapped[float] = mapped_column(Float, default=1.0)

    attempt: Mapped[Attempt] = relationship(back_populates="words")


class WordStat(Base):
    """Agregado por palavra: quantas vezes foi lida e a media das notas.

    Esta tabela e o que alimenta a aba "Historico -> palavras mais dificeis".
    Ela e atualizada a cada analise (upsert).
    """

    __tablename__ = "word_stats"
    __table_args__ = (UniqueConstraint("normalized", "level", name="uq_word_level"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    normalized: Mapped[str] = mapped_column(String(80), index=True)
    display: Mapped[str] = mapped_column(String(80))
    level: Mapped[str] = mapped_column(String(16), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    best_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_score: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    @property
    def average_score(self) -> float:
        return round(self.total_score / self.attempts, 4) if self.attempts else 0.0
