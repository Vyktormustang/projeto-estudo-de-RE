#!/usr/bin/env bash
# =============================================================================
# build_apk.sh — FORJA: empacota o app web (dist) em APK assinado.
#
# Pipeline (sem Gradle, só Android build-tools):
#   1. aapt2 compile/link  -> base.apk (manifest + resources + assets/www)
#   2. javac               -> classes do shell WebView
#   3. d8                  -> classes.dex
#   4. zip                 -> classes.dex entra na raiz do APK
#   5. zipalign -p 4       -> alinhamento (exigido por Android 11+ em arm64)
#   6. apksigner           -> assinatura v1+v2+v3 com o keystore do CI
#
# Entradas (env ou flags):
#   --dist DIR            pasta com o build do Vite (default: forja/web/dist)
#   --version-name X.Y.Z  (default: 39.0.0)
#   --version-code N      (default: 3900)
#   --out ARQUIVO.apk     (default: forja/dist/Forja_Apice_vX.Y.Z.apk)
#   --ks ARQ --ks-pass P --ks-key-alias A [--key-pass P]
#
# Exigidos no ambiente: ANDROID_HOME (ou ANDROID_SDK_ROOT), JDK (javac),
# build-tools (aapt2, d8, zipalign, apksigner) e platform (android.jar).
# =============================================================================
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORJA="$(cd "$AQUI/.." && pwd)"
REPO="$(cd "$FORJA/.." && pwd)"

DIST="$FORJA/web/dist"
VERSAO_NOME="39.0.0"
VERSAO_CODIGO="3900"
SAIDA=""
KS=""
KS_PASS=""
KEY_ALIAS="forja"
KEY_PASS=""

passo() { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }
falhar() { printf '\033[1;31m[ERRO] %s\033[0m\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --dist) DIST="$2"; shift 2 ;;
    --version-name) VERSAO_NOME="$2"; shift 2 ;;
    --version-code) VERSAO_CODIGO="$2"; shift 2 ;;
    --out) SAIDA="$2"; shift 2 ;;
    --ks) KS="$2"; shift 2 ;;
    --ks-pass) KS_PASS="$2"; shift 2 ;;
    --ks-key-alias) KEY_ALIAS="$2"; shift 2 ;;
    --key-pass) KEY_PASS="$2"; shift 2 ;;
    -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) falhar "argumento desconhecido: $1" ;;
  esac
done

[ -n "$SAIDA" ] || SAIDA="$FORJA/dist/Forja_Apice_v${VERSAO_NOME}.apk"
[ -d "$DIST" ] || falhar "dist inexistente: $DIST (rode 'npm run build' antes)"
[ -f "$DIST/index.html" ] || falhar "$DIST/index.html não encontrado — build do Vite falhou?"

SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
[ -n "$SDK" ] || falhar "ANDROID_HOME/ANDROID_SDK_ROOT não definido"
[ -d "$SDK" ] || falhar "SDK inexistente: $SDK"

BT="$(ls -d "$SDK"/build-tools/*/ 2>/dev/null | sort -V | tail -1 || true)"
[ -n "$BT" ] || falhar "build-tools não encontrado em $SDK/build-tools"
BT="${BT%/}"
ANDROID_JAR="$(ls -d "$SDK"/platforms/android-*/android.jar 2>/dev/null | sort -V | tail -1 || true)"
if [ -z "$ANDROID_JAR" ]; then
  ANDROID_JAR="$(ls -d "$SDK"/platforms/android-*/ 2>/dev/null | sort -V | tail -1)/android.jar"
fi
[ -f "$ANDROID_JAR" ] || falhar "android.jar não encontrado em $SDK/platforms (instale platform 34)"

AAPT2="$BT/aapt2"; D8="$BT/d8"; ZIPALIGN="$BT/zipalign"; APKSIGNER="$BT/apksigner"
for bin in "$AAPT2" "$D8" "$ZIPALIGN" "$APKSIGNER"; do
  [ -x "$bin" ] || falhar "build-tool ausente: $bin"
done
command -v javac >/dev/null || falhar "javac ausente (instale um JDK)"

echo "[forja] SDK=$SDK"
echo "[forja] build-tools=$(basename "$BT")"
echo "[forja] android.jar=$ANDROID_JAR"
echo "[forja] versão=$VERSAO_NOME ($VERSAO_CODIGO)"
java -version 2>&1 | head -1

TRAB="$(mktemp -d)"
trap 'rm -rf "$TRAB"' EXIT
mkdir -p "$TRAB/compiled" "$TRAB/gen" "$TRAB/classes" "$TRAB/dex" "$TRAB/assets"

# ---------------------------------------------------------------- 0) ícones
passo "0/6 ícones do launcher"
if [ ! -f "$FORJA/android/res/mipmap-xxxhdpi/ic_launcher.png" ]; then
  python3 "$AQUI/make_icon.py" --out "$FORJA/android/res"
fi

# ------------------------------------------------------- 1) web -> assets/www
passo "1/6 copiando build web para assets/www"
rm -rf "$TRAB/assets/www"
mkdir -p "$TRAB/assets/www"
cp -R "$DIST/." "$TRAB/assets/www/"
[ -f "$TRAB/assets/www/index.html" ] || falhar "index.html sumiu na cópia de assets"
du -sh "$TRAB/assets/www"

# -------------------------------------------------- 2) aapt2 compile + link
passo "2/6 aapt2 compile res/"
"$AAPT2" compile --dir "$FORJA/android/res" -o "$TRAB/compiled/res.zip"

passo "2/6 aapt2 link -> base.apk"
"$AAPT2" link \
  -o "$TRAB/base.apk" \
  -I "$ANDROID_JAR" \
  --manifest "$FORJA/android/AndroidManifest.xml" \
  -A "$TRAB/assets" \
  --java "$TRAB/gen" \
  --min-sdk-version 24 \
  --target-sdk-version 34 \
  --version-code "$VERSAO_CODIGO" \
  --version-name "$VERSAO_NOME" \
  --auto-add-overlay \
  "$TRAB/compiled/res.zip"

# ----------------------------------------------------- 3) javac (shell Java)
passo "3/6 javac do shell WebView"
find "$FORJA/android/java" -name '*.java' > "$TRAB/fontes.txt"
find "$TRAB/gen" -name '*.java' >> "$TRAB/fontes.txt"
[ -s "$TRAB/fontes.txt" ] || falhar "nenhum .java encontrado"
javac -encoding UTF-8 -source 8 -target 8 -nowarn -Xlint:-options \
  -classpath "$ANDROID_JAR" -d "$TRAB/classes" @"$TRAB/fontes.txt"

# ------------------------------------------------------------- 4) d8 -> dex
passo "4/6 d8 -> classes.dex"
find "$TRAB/classes" -name '*.class' > "$TRAB/classes.txt"
"$D8" --release --min-api 24 --lib "$ANDROID_JAR" --output "$TRAB/dex" @"$TRAB/classes.txt"
[ -f "$TRAB/dex/classes.dex" ] || falhar "d8 não gerou classes.dex"

passo "4/6 inserindo classes.dex no APK"
cp "$TRAB/base.apk" "$TRAB/nao_assinado.apk"
( cd "$TRAB/dex" && zip -q -X "$TRAB/nao_assinado.apk" classes.dex )
unzip -l "$TRAB/nao_assinado.apk" | grep -q 'classes.dex' || falhar "classes.dex fora do APK"

# ----------------------------------------------------------- 5) zipalign
passo "5/6 zipalign -p 4"
"$ZIPALIGN" -p -f 4 "$TRAB/nao_assinado.apk" "$TRAB/alinhado.apk"
"$ZIPALIGN" -c -p 4 "$TRAB/alinhado.apk" >/dev/null || falhar "verificação de zipalign falhou"

# ----------------------------------------------------------- 6) assinatura
passo "6/6 apksigner (v1+v2+v3)"
mkdir -p "$(dirname "$SAIDA")"
[ -n "$KS" ] || falhar "keystore não informado (--ks)"
[ -f "$KS" ] || falhar "keystore inexistente: $KS"
[ -n "$KS_PASS" ] || falhar "--ks-pass vazio"
ASSINAR=( "$APKSIGNER" sign
  --ks "$KS" --ks-pass "pass:$KS_PASS" --ks-key-alias "$KEY_ALIAS"
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true
  --min-sdk-version 24 --out "$SAIDA" "$TRAB/alinhado.apk" )
if [ -n "$KEY_PASS" ]; then
  ASSINAR=( "$APKSIGNER" sign
    --ks "$KS" --ks-pass "pass:$KS_PASS" --key-pass "pass:$KEY_PASS" --ks-key-alias "$KEY_ALIAS"
    --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true
    --min-sdk-version 24 --out "$SAIDA" "$TRAB/alinhado.apk" )
fi
"${ASSINAR[@]}"

passo "verificação final"
"$APKSIGNER" verify --verbose --print-certs "$SAIDA" | sed -n '1,12p'
"$ZIPALIGN" -c -p 4 "$SAIDA" >/dev/null && echo "ZIPALIGN_OK"
TAM="$(stat -c %s "$SAIDA")"
SHA="$(sha256sum "$SAIDA" | cut -d' ' -f1)"
MD5="$(md5sum "$SAIDA" | cut -d' ' -f1)"
echo
echo "APK:      $SAIDA"
echo "Tamanho:  $TAM bytes"
echo "SHA-256:  $SHA"
echo "MD5:      $MD5"
echo "Versão:   $VERSAO_NOME ($VERSAO_CODIGO)"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "apk_path=$SAIDA"
    echo "apk_sha256=$SHA"
    echo "apk_md5=$MD5"
    echo "apk_size=$TAM"
    echo "version_name=$VERSAO_NOME"
    echo "version_code=$VERSAO_CODIGO"
  } >> "$GITHUB_OUTPUT"
fi
