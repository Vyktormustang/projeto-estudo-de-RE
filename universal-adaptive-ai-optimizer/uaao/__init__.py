"""Universal Adaptive AI Optimizer (UA AO).

Camada EXTERNA de otimizacao de instrucoes/prompts para assistentes de IA.

O que este projeto e
--------------------
Um sistema de experimentacao que: avalia um artefato de prompt com metricas
objetivas, diagnostica falhas, gera candidatos, testa, compara de forma pareada
e aceita/rejeita sob criterios predefinidos -- registrando tudo em memoria
persistente (SQLite) com historico, motivos e reversao.

O que este projeto NAO e
------------------------
  * Nao modifica pesos de modelos, memoria interna nem instrucoes de plataformas
    externas: nao existe API/mecanismo para isso aqui, e o projeto nao afirma o
    contrario.
  * Nao chama LLM algum nesta versao (decisao explicita do usuario: modo
    deterministico). Os executores sao locais e reproduziveis.
  * Nao acessa a rede: a politica de seguranca e imutavel e proibe.

Portanto os numeros que ele produz medem o LOOP DE OTIMIZACAO e a CONFORMIDADE
DE POLITICA no executor de referencia -- nunca a qualidade de um modelo real.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
