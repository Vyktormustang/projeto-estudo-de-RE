"""Erros de negocio com mensagem pronta em portugues.

O frontend mostra `message` direto na tela. `code` serve para o app decidir o
que fazer (ex.: "audio_too_short" -> pedir para gravar de novo).
"""

from __future__ import annotations


class AnalysisError(Exception):
    """Erro que vira uma resposta JSON padrao {detail, code}."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


# --- Catalogo de mensagens (mantenha tudo em portugues, sem jargao) ---------

ERR_NO_SENTENCE = AnalysisError(
    "sentence_not_found",
    "Não encontrei essa frase no servidor. Toque em “Nova frase” e tente outra vez.",
    404,
)

ERR_EMPTY_AUDIO = AnalysisError(
    "empty_audio",
    "Nenhum áudio chegou ao servidor. Segure o botão do microfone e leia a frase.",
    400,
)

ERR_AUDIO_TOO_SHORT = AnalysisError(
    "audio_too_short",
    "A gravação ficou curta demais. Espere o microfone abrir, leia a frase inteira e só então pare.",
    422,
)

ERR_AUDIO_TOO_LONG = AnalysisError(
    "audio_too_long",
    "A gravação passou de 60 segundos. Leia só a frase mostrada, em uma única gravação.",
    413,
)

ERR_UPLOAD_TOO_BIG = AnalysisError(
    "upload_too_big",
    "O arquivo de áudio é grande demais. Grave uma frase curta (até 60 segundos).",
    413,
)

ERR_SILENCE = AnalysisError(
    "no_speech",
    "Não consegui ouvir nada na gravação. Chegue mais perto do microfone e fale um pouco mais alto.",
    422,
)

ERR_CONVERT = AnalysisError(
    "audio_convert_failed",
    "Não consegui preparar o áudio. Verifique se o ffmpeg está instalado (veja o README) e tente de novo.",
    500,
)

ERR_FFMPEG_MISSING = AnalysisError(
    "ffmpeg_missing",
    "O ffmpeg não está instalado no PC do servidor. Instale e reinicie o servidor (passo 1.2 do README).",
    500,
)

ERR_MODELS_LOADING = AnalysisError(
    "models_unavailable",
    "O modelo de pronúncia ainda não está pronto no servidor. Na primeira vez ele baixa ~2 GB; "
    "aguarde alguns minutos e tente de novo. Se persistir, veja “Problemas comuns” no README.",
    503,
)

ERR_MODELS_DISABLED = AnalysisError(
    "models_disabled",
    "O servidor está rodando com SN_DISABLE_MODELS=1 (modo somente API). "
    "Reinicie sem essa variável para analisar pronúncia de verdade.",
    503,
)

ERR_ANALYSIS_FAILED = AnalysisError(
    "analysis_failed",
    "Algo deu errado ao analisar o áudio. Tente gravar de novo; se repetir, reinicie o servidor.",
    500,
)
