"""SpeakNatural - ponto de entrada da API.

Rodar:
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

Documentacao interativa (OpenAPI):  http://localhost:8000/docs
Se o frontend ja foi compilado (frontend/dist), o mesmo endereco serve o app:
    http://localhost:8000/
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import routes_analyze, routes_health, routes_history, routes_sentences
from .config import CORS_ORIGINS, DATA_DIR
from .db import init_db
from .services.errors import AnalysisError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("speaknatural")

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Cria as tabelas na subida do servidor."""
    init_db()
    logger.info("Banco pronto em %s", DATA_DIR / "speaknatural.db")
    logger.info("Documentação da API: http://localhost:8000/docs")
    yield
    logger.info("Servidor encerrado.")


app = FastAPI(
    title="SpeakNatural API",
    version=__version__,
    summary="Treino de pronúncia do inglês com nota por palavra e por som",
    description=(
        "Servidor local (roda no seu PC, sem chave de API) que analisa a pronúncia do inglês.\n\n"
        "**Fluxo:** `GET /sentences` → o app grava a sua voz → `POST /analyze` (multipart) → "
        "o app pinta cada palavra de verde/amarelo/vermelho → `GET /history`.\n\n"
        "Erros voltam sempre no formato `{detail, code}`, com `detail` em português."
    ),
    lifespan=lifespan,
    contact={"name": "SpeakNatural"},
    openapi_tags=[
        {"name": "sistema", "description": "Saúde do servidor"},
        {"name": "frases", "description": "Lista de frases de prática"},
        {"name": "análise", "description": "Análise de pronúncia"},
        {"name": "histórico", "description": "Tentativas salvas"},
    ],
)

# CORS liberado: o app roda em outro "site" (file:// no APK, localhost:5173 no
# dev, ou o IP do PC). Sem isso o navegador bloqueia o POST do áudio.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(AnalysisError)
async def _analysis_error_handler(_request: Request, exc: AnalysisError) -> JSONResponse:
    """Converte nossos erros de negocio em JSON com mensagem em portugues."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Mensagem amigavel quando falta o audio ou o sentence_id no formulario."""
    missing = [str(err.get("loc", ["?"])[-1]) for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Pedido incompleto: " + ", ".join(missing) + ". "
            "Envie o arquivo 'audio' e o campo 'sentence_id'.",
            "code": "validation_error",
        },
    )


app.include_router(routes_health.router)
app.include_router(routes_sentences.router)
app.include_router(routes_analyze.router)
app.include_router(routes_history.router)


if FRONTEND_DIST.is_dir() and (FRONTEND_DIST / "index.html").exists():
    # Serve o app web compilado na mesma porta (conveniente no PC).
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="app-web")
else:

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, object]:
        """Sem frontend compilado, mostra um resumo e os atalhos."""
        return {
            "app": "SpeakNatural",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
            "sentences": "/sentences",
            "analyze": "POST /analyze",
            "history": "/history",
            "dica": "Compile o frontend (cd frontend && npm install && npm run build) "
            "para abrir o app nesta mesma porta.",
        }
