#!/usr/bin/env bash
# Atalho da raiz do repositório: chama o script de verdade em speaknatural/.
# Tanto faz rodar ./start-server.sh aqui ou speaknatural/start-server.sh.
exec "$(dirname "$0")/speaknatural/start-server.sh" "$@"
