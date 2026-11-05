"""Configuracao central do SpeakNatural.

Tudo pode ser mudado por variavel de ambiente, sem tocar no codigo.
Os valores padrao foram escolhidos para rodar bem em um PC comum
(CPU only, 8 GB de RAM).
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

#: Pasta do backend ( .../speaknatural/backend )
BACKEND_DIR = Path(__file__).resolve().parent.parent

#: Pasta onde ficam banco SQLite, audios temporarios e cache de modelos.
DATA_DIR = Path(os.environ.get("SN_DATA_DIR", BACKEND_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

#: Pasta de audios temporarios enviados pelo app (apagados logo apos analise).
TMP_DIR = DATA_DIR / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

#: Banco SQLite.
DB_PATH = Path(os.environ.get("SN_DB_PATH", DATA_DIR / "speaknatural.db"))

#: URL do SQLAlchemy.
DATABASE_URL = os.environ.get("SN_DATABASE_URL", f"sqlite:///{DB_PATH}")


# ---------------------------------------------------------------------------
# Servidor
# ---------------------------------------------------------------------------

HOST = os.environ.get("SN_HOST", "0.0.0.0")
PORT = int(os.environ.get("SN_PORT", "8000"))

#: CORS. "*" e proposital: o servidor roda na sua rede local (LAN) e o app
#: Android acessa por http://192.168.x.x:8000. Nao ha nada sensivel exposto
#: alem do seu proprio banco de treino. Para restringir, use por exemplo:
#:   SN_CORS_ORIGINS="http://localhost:5173,http://192.168.0.50:8000"
_origins = os.environ.get("SN_CORS_ORIGINS", "*").strip()
CORS_ORIGINS = ["*"] if _origins == "*" else [o.strip() for o in _origins.split(",") if o.strip()]


# ---------------------------------------------------------------------------
# Modelos de IA (open source, sem chave de API)
# ---------------------------------------------------------------------------

#: Transcricao (rapido, ingles, CPU int8). "small.en" e o pedido no escopo.
WHISPER_MODEL = os.environ.get("SN_WHISPER_MODEL", "small.en")
WHISPER_DEVICE = os.environ.get("SN_WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.environ.get("SN_WHISPER_COMPUTE_TYPE", "int8")
WHISPER_BEAM_SIZE = int(os.environ.get("SN_WHISPER_BEAM_SIZE", "1"))

#: Reconhecimento de fonemas IPA.
PHONEME_MODEL = os.environ.get("SN_PHONEME_MODEL", "facebook/wav2vec2-xlsr-53-espeak-cv-ft")

#: Idioma para o phonemizer / espeak-ng.
PHONEMIZER_LANGUAGE = os.environ.get("SN_PHONEMIZER_LANGUAGE", "en-us")

#: Pasta onde o espeak-ng foi instalado, caso ele NAO esteja no PATH.
#: Windows (padrao do instalador): C:\Program Files\eSpeak NG
ESPEAK_PATH = os.environ.get("SN_ESPEAK_PATH", "").strip()

#: Se "1", usa modelos falsos deterministicos (dev/testes, sem baixar 2 GB).
#: NUNCA ligue isso no uso real: os scores passam a ser simulados.
FAKE_MODELS = os.environ.get("SN_FAKE_MODELS", "0") == "1"

#: Se "1", nao baixa/roda modelos e responde 503 explicativo quando faltar algo.
#: (Util em CI para testar a API sem GPU/CPU pesada.)
DISABLE_MODELS = os.environ.get("SN_DISABLE_MODELS", "0") == "1"


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

#: Todo audio e convertido para 16 kHz mono (exigencia do wav2vec2 / whisper).
TARGET_SAMPLE_RATE = 16_000
TARGET_CHANNELS = 1

#: Duracao minima aceita (segundos) - abaixo disso devolvemos "audio curto".
MIN_AUDIO_SECONDS = float(os.environ.get("SN_MIN_AUDIO_SECONDS", "0.6"))

#: Duracao maxima (segundos) - protege o servidor de arquivos gigantes.
MAX_AUDIO_SECONDS = float(os.environ.get("SN_MAX_AUDIO_SECONDS", "60"))

#: Tamanho maximo do upload (bytes). 12 MB cobre 60 s de webm/ogg com folga.
MAX_UPLOAD_BYTES = int(os.environ.get("SN_MAX_UPLOAD_BYTES", str(12 * 1024 * 1024)))

#: Abaixo deste RMS (0..1) consideramos a gravacao "silencio".
SILENCE_RMS_THRESHOLD = float(os.environ.get("SN_SILENCE_RMS", "0.004"))

#: Caminho do ffmpeg (use SN_FFMPEG_BIN se ele nao estiver no PATH).
FFMPEG_BIN = os.environ.get("SN_FFMPEG_BIN", "ffmpeg")


# ---------------------------------------------------------------------------
# Pontuacao (as faixas de cor pedidas no escopo)
# ---------------------------------------------------------------------------

GREEN_MIN = 0.85   # >= 0.85  -> verde   (correto)
YELLOW_MIN = 0.50  # 0.50..0.84 -> amarelo (parcial)
                   # < 0.50   -> vermelho (errado / palavra faltando)

#: Similaridade considerada "som parecido" (ex.: ɪ vs iː).
NEAR_SOUND_SCORE = 0.65

#: Penalidade de buraco (som esperado que nao foi ouvido, ou som extra) no
#: alinhamento Needleman-Wunsch. Quanto mais negativo, mais o algoritmo evita
#: pular sons. -0.55 funciona bem para IPA (ver scoring.py).
GAP_PENALTY = -0.55

#: Versao do motor de pontuacao. Vai gravada no historico para voce saber com
#: qual formula cada tentativa foi avaliada.
ENGINE_VERSION = "1.0.0"
