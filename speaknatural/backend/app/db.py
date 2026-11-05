"""SQLite + SQLAlchemy: conexao, sessao e criacao das tabelas."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    """Base declarativa de todos os modelos."""


# check_same_thread=False: o FastAPI pode atender em threads diferentes.
# pool_pre_ping: sobrevive a reinicios do arquivo SQLite.
engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:  # pragma: no cover
    """WAL + foreign keys: menos travamento com o app aberto e dados consistentes."""
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Cria as tabelas (idempotente). Chamado no startup da aplicacao."""
    from . import models  # noqa: F401  (registra os mapeamentos)

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """Dependencia do FastAPI: uma sessao por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
