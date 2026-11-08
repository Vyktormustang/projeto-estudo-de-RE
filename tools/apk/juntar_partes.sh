#!/usr/bin/env bash
# Remonta um arquivo grande dividido em partes (<100 MiB cada) para o Drive.
#
# A rede do sandbox não alcança nenhum espelho de APK, e o conector do Drive
# recusa arquivos acima de 100 MiB. O caminho é: você divide aqui, sobe as
# partes, e este script remonta + confere o SHA-256.
#
# Aceita os três formatos comuns de divisão:
#   file.001 file.002 ...     (split, 7-Zip "split to volumes", HJSplit)
#   file.part1.rar (só nomes) (não descompacta .rar — só .001/.partN crus)
#   file.zip.001 ...          (7-Zip)
#
# Uso: bash juntar_partes.sh <diretório_com_as_partes> [saida] [sha256_esperado]
set -uo pipefail
DIR="${1:?uso: juntar_partes.sh <dir_das_partes> [saida] [sha256]}"
[ -d "$DIR" ] || { echo "[ERRO] diretório não existe: $DIR"; exit 2; }

# escolhe a maior família de partes (evita juntar dois arquivos diferentes)
mapfile -t CAND < <(find "$DIR" -maxdepth 1 -type f \
  \( -regextype posix-extended -regex '.*\.(00[1-9]|0[1-9][0-9]|[1-9][0-9][0-9])' \
     -o -regex '.*\.part[0-9]+' \) -printf '%f\n' | sort)
[ "${#CAND[@]}" -gt 0 ] || { echo "[ERRO] nenhuma parte (*.001, *.part1) em $DIR"; exit 2; }

# agrupa por prefixo (tudo antes do sufixo numérico)
declare -A POR_PREFIXO=()
for f in "${CAND[@]}"; do
  pre=$(echo "$f" | sed -E 's/\.(00[0-9]|0[0-9]{2}|[0-9]{3}|part[0-9]+)$//')
  POR_PREFIXO["$pre"]=$(( ${POR_PREFIXO["$pre"]:-0} + 1 ))
done
PREFIXO=$(for k in "${!POR_PREFIXO[@]}"; do echo "${POR_PREFIXO[$k]} $k"; done | sort -rn | head -1 | cut -d' ' -f2-)
N=${POR_PREFIXO[$PREFIXO]}
echo "[partes] padrão '$PREFIXO' com $N arquivo(s)"

SAIDA="${2:-$DIR/$PREFIXO}"
[ -e "$SAIDA" ] && { echo "[ERRO] saída já existe: $SAIDA"; exit 2; }

# ordena numericamente pelo sufixo, não alfabeticamente (evita 1,10,2 na ordem errada)
num_de() { echo "$1" | grep -oE '[0-9]+$'; }
# SÓ arquivos com sufixo numérico: o glob "$PREFIXO"* também casaria com o
# arquivo original já dividido, e o resultado sairia com o dobro do tamanho
# (aconteceu no teste: 3 000 000 B em vez de 1 500 000 B).
mapfile -t ORDENADAS < <(for f in "${CAND[@]}"; do
  case "$f" in
    "$PREFIXO"[0-9]*|"$PREFIXO".[0-9]*|"$PREFIXO".part[0-9]*|"$PREFIXO"*.part[0-9]*)
      echo "$(num_de "$f") $DIR/$f" ;;
  esac
done | sort -n | cut -d' ' -f2-)

: > "$SAIDA"
for f in "${ORDENADAS[@]}"; do
  echo "  + $(basename "$f") ($(stat -c%s "$f") B)"
  cat "$f" >> "$SAIDA" || { echo "[ERRO] falha ao anexar $f"; exit 1; }
done
TAM=$(stat -c%s "$SAIDA")
echo "[ok] $SAIDA — $TAM bytes ($(numfmt --to=iec "$TAM" 2>/dev/null || echo "$TAM"))"

if [ -n "${3:-}" ]; then
  OBTIDO=$(sha256sum "$SAIDA" | cut -d' ' -f1)
  echo "[sha256] esperado: $3"
  echo "[sha256] obtido  : $OBTIDO"
  [ "$OBTIDO" = "$3" ] && echo "[OK] íntegro" || { echo "[FALHOU] SHA-256 não confere — partes faltando ou corrompidas"; exit 1; }
fi
# confere se é zip/APK de fato
if command -v file >/dev/null; then file "$SAIDA"; fi
