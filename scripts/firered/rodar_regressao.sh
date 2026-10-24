#!/usr/bin/env bash
# Regressão E8: um comando, imprime PASS/FAIL por etapa e falha se qualquer
# uma falhar. Pressupõe o ambiente religado por setup_ambiente.sh
# (clone em /tmp/pokefirered, toolchain em /tmp/tc, core em /tmp/mgba-0.10.5).
#
# Uso:  bash scripts/firered/rodar_regressao.sh
# Windows: rodar dentro do WSL (ver docs/FIRERED.md, bloco PowerShell/WSL).
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
export PATH="/tmp/tc/bin:$PATH"
export MGBA_CORE="${MGBA_CORE:-/tmp/mgba-0.10.5/build/mgba_libretro.so}"
export PF_OFFSETS="${PF_OFFSETS:-/tmp/pf_offsets.json}"

FALHAS=0
rodar() {  # rodar "nome" comando...
  local nome="$1"; shift
  if "$@" >/tmp/regressao_passo.log 2>&1; then
    echo "PASS  $nome"
  else
    echo "FAIL  $nome  (últimas linhas:)"
    tail -5 /tmp/regressao_passo.log | sed 's/^/      /'
    FALHAS=$((FALHAS + 1))
  fi
}

# self-tests (não precisam de ROM nem toolchain)
rodar "self-test gen_species_data (evoluções 2c)" python3 "$AQUI/gen_species_data.py" --self-test
rodar "self-test verificar_rom (E2-E7)"           python3 "$AQUI/verificar_rom.py" --self-test
rodar "self-test savestate"                        python3 "$AQUI/savestate.py" --self-test
rodar "self-test gen_trainer_parties"              python3 "$AQUI/gen_trainer_parties.py" --self-test
rodar "self-test gen_pokedex_categories"           python3 "$AQUI/gen_pokedex_categories.py" --self-test

# conferência estática do binário (fonte da verdade: ROM compilada)
rodar "verificar_rom na ROM real"                  python3 "$AQUI/verificar_rom.py" --pokefirered /tmp/pokefirered

# provas dinâmicas (emulador headless)
rodar "E4 golpes modernos em batalha (6 rodadas)"  python3 "$AQUI/prova_golpes_e4.py"
rodar "E5 habilidade moderna (Earth Eater 3/3)"    python3 "$AQUI/prova_habilidades_e5.py" --prova
rodar "E7 encontro+captura de Gen 9 na Rota 1"     python3 "$AQUI/prova_encontros_e7.py" --prova --tentativas 12 --capturar --shots /tmp/regressao_shots

echo
if [ "$FALHAS" -eq 0 ]; then
  echo "REGRESSÃO: PASS (todas as etapas)"
else
  echo "REGRESSÃO: FAIL ($FALHAS etapa(s))"
fi
exit "$FALHAS"
