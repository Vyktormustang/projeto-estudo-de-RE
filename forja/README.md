# FORJA — Sistema do Ápice · infraestrutura de build (v39.0.0)

Este diretório é a **fábrica do APK** `br.forja.apice`: app web (TypeScript)
empacotado num shell Android WebView **100% offline, sem nenhuma permissão**.

```
forja/
├── web/                 app TypeScript + Vite (núcleo testado com vitest)
│   ├── src/forja.ts     Elo, precisão, SM-2, Cofre — funções puras
│   └── src/main.ts      UI (atualmente: build de canário)
├── android/             shell WebView (manifest, MainActivity, ícones)
├── tools/
│   ├── build_apk.sh     aapt2 → javac → d8 → zip → zipalign → apksigner
│   └── make_icon.py     gera os ícones PNG sem dependências
├── signing/             keystore de assinatura (ver README local)
└── version.json         versionName / versionCode usados pelo CI
```

## O que o CI faz (`.github/workflows/forja-apk.yml`)

A cada push que toque em `forja/**` (ou `workflow_dispatch`):

1. `npm ci` → `tsc --noEmit` → `vitest run` → `vite build`
2. aapt2 compila recursos e linka o manifesto, embutindo `web/dist` em `assets/www`
3. javac + d8 geram `classes.dex`
4. `zipalign -p 4` e `apksigner` assinam (v1 + v2 + v3)
5. Fumaça: confere `AndroidManifest.xml`, `classes.dex`, `resources.arsc`,
   `assets/www/index.html` e **dump de permissões (deve ser vazio)**
6. Publica o artifact `forja-apk-<versão>` e cria/atualiza a Release
   (`forja-v<versão>` na `main`; `forja-v<versão>-canario` em branch de trabalho)

## Rodar localmente

```bash
# 1) app web
cd forja/web && npm ci && npm run typecheck && npm test && npm run build

# 2) APK (precisa de JDK + Android SDK com build-tools 34 e platform 34)
export ANDROID_HOME=/caminho/do/android-sdk
bash forja/tools/build_apk.sh \
  --dist forja/web/dist \
  --version-name 39.0.0 --version-code 3900 \
  --ks forja/signing/forja.p12 --ks-pass forja-ci-offline-2026 \
  --ks-key-alias forja --key-pass forja-ci-offline-2026 \
  --out forja/dist/Forja_Apice_v39.0.0.apk
```

O script imprime SHA-256, MD5, tamanho e roda `apksigner verify` no final.
Sem Gradle, sem Android Studio — só build-tools.

## Instalação no aparelho

1. Baixe o APK na aba **Releases** (ou no artifact da run do Actions).
2. Android 7.0+ (minSdk 24, target 34). Permita "instalar de fontes desconhecidas".
3. **Instalação limpa:** o certificado do v39 é novo, então não há atualização
   por cima do v38 — desinstale o anterior. Exporte o Cofre (JSON) antes, se
   quiser preservar progresso.

## Status honesto

- ✅ Pipeline de APK provado ponta a ponta no CI (build + assinatura + verificação)
- ✅ Núcleo do xadrez (Elo, categorias, precisão, SM-2, Cofre) implementado com
  20 testes determinísticos
- ⏳ **A UI/conteúdo do v38 não está aqui**: o Drive só tem APKs. O próximo passo
  é trazer o código-fonte do app para `forja/web/src/` — aí a UI completa volta e
  o fix do v38 entra com teste de regressão (ver `forja/FIX_v39.md`)
