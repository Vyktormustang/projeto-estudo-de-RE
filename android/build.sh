#!/usr/bin/env bash
#
# Compila o APK do Xadrez Studio SEM Gradle.
#
#   ./android/build.sh
#
# Entradas:  android/AndroidManifest.xml, android/res, android/java, android/servidor,
#            app/public (copiado para assets/www)
# Saída:     dist/xadrez-studio-<versão>.apk  (+ .sha256)
#
# Requer: JDK 17+, Android SDK build-tools (aapt2, d8, zipalign, apksigner) e
# platform android-34. No ambiente local esses itens podem não existir; o
# workflow .github/workflows/apk.yml roda a mesma coisa no runner do GitHub.
#
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID="$RAIZ/android"
CONSTRUCAO="$RAIZ/build/apk"
DIST="$RAIZ/dist"
VERSAO="1.0"
NOME="xadrez-studio-${VERSAO}"
MIN_SDK=26
ALVO_SDK=34

log() { printf '\n\033[1;32m==>\033[0m %s\n' "$*"; }
erro() { printf '\n\033[1;31mERRO:\033[0m %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- ferramentas
achar_sdk() {
  for candidato in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}" "$HOME/Android/Sdk" \
                   "$HOME/Library/Android/sdk" /usr/lib/android-sdk /opt/android-sdk; do
    if [ -n "$candidato" ] && [ -d "$candidato/build-tools" ]; then
      echo "$candidato"; return 0
    fi
  done
  return 1
}

SDK="$(achar_sdk)" || erro "Android SDK não encontrado (defina ANDROID_HOME)."
BUILD_TOOLS="$(ls -1 "$SDK/build-tools" | sort -V | tail -1)"
BT="$SDK/build-tools/$BUILD_TOOLS"
PLATAFORMA="$(ls -1 "$SDK/platforms" | grep -E "^android-($ALVO_SDK|[3-9][0-9])$" | sort -V | tail -1)"
JAR_ANDROID="$SDK/platforms/$PLATAFORMA/android.jar"
[ -f "$JAR_ANDROID" ] || erro "android.jar não encontrado em $SDK/platforms (instale platform $ALVO_SDK)."

for ferr in aapt2 d8 zipalign apksigner; do
  [ -x "$BT/$ferr" ] || erro "faltou $ferr em $BT"
done
command -v javac >/dev/null || erro "javac não encontrado (instale JDK 17+)."

log "SDK: $SDK · build-tools $BUILD_TOOLS · $PLATAFORMA"

# ------------------------------------------------------------------- limpeza
rm -rf "$CONSTRUCAO"
mkdir -p "$CONSTRUCAO"/{res,gen,classes,dex,assets/www} "$DIST"

# ------------------------------------------------------- 1) site dentro do APK
log "copiando o app web (app/public → assets/www)"
cp -R "$RAIZ/app/public/." "$CONSTRUCAO/assets/www/"
# o APK não tem servidor: tira o que só existe no modo servidor
rm -rf "$CONSTRUCAO/assets/www/vendor/stockfish"
mkdir -p "$CONSTRUCAO/assets/www/vendor/stockfish"
cp "$RAIZ/android/servidor/stockfish-19-lite-single.js" \
   "$RAIZ/android/servidor/stockfish-19-lite-single.wasm" \
   "$CONSTRUCAO/assets/www/vendor/stockfish/"
rm -f "$CONSTRUCAO/assets/www/js/main.js.bak"
du -sh "$CONSTRUCAO/assets/www"

# ---------------------------------------------- 2) recursos (aapt2 compile+link)
log "compilando recursos (aapt2)"
"$BT/aapt2" compile --dir "$ANDROID/res" -o "$CONSTRUCAO/res/recursos.zip"

"$BT/aapt2" link \
  -o "$CONSTRUCAO/base.apk" \
  -I "$JAR_ANDROID" \
  --manifest "$ANDROID/AndroidManifest.xml" \
  --java "$CONSTRUCAO/gen" \
  --min-sdk-version "$MIN_SDK" \
  --target-sdk-version "$ALVO_SDK" \
  --version-code 1 --version-name "$VERSAO" \
  -A "$CONSTRUCAO/assets" \
  "$CONSTRUCAO/res/recursos.zip"

# ------------------------------------------------------------------ 3) javac
log "compilando java"
mapfile -t FONTES < <(find "$ANDROID/java" "$CONSTRUCAO/gen" -name '*.java')
javac -source 17 -target 17 -encoding UTF-8 -Xlint:-options \
  -bootclasspath "$JAR_ANDROID" -classpath "$JAR_ANDROID" \
  -d "$CONSTRUCAO/classes" "${FONTES[@]}" 2>&1 | grep -v "bootstrap class path" || true
test -f "$CONSTRUCAO/classes/br/com/xadrezstudio/MainActivity.class" \
  || erro "compilação Java não produziu MainActivity.class"

# --------------------------------------------------------------------- 4) d8
log "convertendo para dex (d8)"
mapfile -t CLASSES < <(find "$CONSTRUCAO/classes" -name '*.class')
"$BT/d8" --release --min-api "$MIN_SDK" --lib "$JAR_ANDROID" \
  --output "$CONSTRUCAO/dex" "${CLASSES[@]}"
ls -la "$CONSTRUCAO/dex"

# ------------------------------------------------------- 5) dex + assets no APK
log "empacotando dex e assets"
cp "$CONSTRUCAO/base.apk" "$CONSTRUCAO/nao-alinhado.apk"
(cd "$CONSTRUCAO/dex" && zip -q -X "$CONSTRUCAO/nao-alinhado.apk" classes.dex)
(cd "$CONSTRUCAO/assets" && zip -q -X -r "$CONSTRUCAO/nao-alinhado.apk" www)

# ----------------------------------------------------------- 6) alinhar e assinar
log "alinhando (zipalign) e assinando (apksigner)"
"$BT/zipalign" -p -f 4 "$CONSTRUCAO/nao-alinhado.apk" "$CONSTRUCAO/alinhado.apk"

KS="$ANDROID/keystore/xadrez.keystore"
if [ ! -f "$KS" ]; then
  log "gerando keystore de assinatura (guarde este arquivo: sem ele não há atualização)"
  mkdir -p "$(dirname "$KS")"
  keytool -genkeypair -v -keystore "$KS" -alias xadrez -keyalg RSA -keysize 2048 \
    -validity 10000 -storepass xadrezstudio -keypass xadrezstudio \
    -dname "CN=Xadrez Studio, OU=Uso pessoal, O=Xadrez Studio, L=Belem, ST=Para, C=BR" >/dev/null
fi

"$BT/apksigner" sign \
  --ks "$KS" --ks-key-alias xadrez \
  --ks-pass pass:xadrezstudio --key-pass pass:xadrezstudio \
  --min-sdk-version "$MIN_SDK" \
  --out "$DIST/$NOME.apk" "$CONSTRUCAO/alinhado.apk"

"$BT/apksigner" verify --print-certs "$DIST/$NOME.apk"

# ------------------------------------------------------------------ 7) resumo
(cd "$DIST" && sha256sum "$NOME.apk" > "$NOME.apk.sha256")
TAMANHO="$(du -h "$DIST/$NOME.apk" | cut -f1)"
log "APK pronto: dist/$NOME.apk ($TAMANHO)"
cat "$DIST/$NOME.apk.sha256"
