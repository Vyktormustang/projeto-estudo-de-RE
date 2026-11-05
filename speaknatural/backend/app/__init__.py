"""SpeakNatural - backend (FastAPI).

Pacote raiz da aplicacao. Nada aqui deve importar modelos pesados
(torch / faster-whisper) no carregamento: os modelos sao carregados
preguicosamente (lazy) em app/services, para o servidor subir em ~1s.
"""

__version__ = "1.0.0"
