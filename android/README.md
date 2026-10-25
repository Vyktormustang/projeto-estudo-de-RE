# APK do Xadrez Studio

O mesmo app de `app/`, empacotado para Android. Roda **offline**: motor de xadrez,
regras, análise e biblioteca ficam dentro do aparelho.

## Baixar e instalar

1. Baixe `xadrez-studio-1.0.apk` na release:
   **https://github.com/Vyktormustang/projeto-estudo-de-RE/releases/tag/apk-v1.0**
2. Confira o arquivo (opcional, mas recomendado):
   `xadrez-studio-1.0.apk.sha256` → `7d51866a6c52a91bded5e51c8ef28c4da22ae74777b138b34ee6616474eed3f5`
   *(muda a cada build; o hash publicado na release é a referência)*
3. No aparelho, abra o arquivo baixado e permita **"instalar de fontes desconhecidas"**
   para o navegador/gerenciador de arquivos.
4. Requisitos: **Android 8.0 (API 26)** ou superior, com **WebView atualizado**
   (o motor é WebAssembly e os módulos são ES6).

O app é assinado com chave própria (não vem da Play Store). Se você instalar uma
versão nova por cima, o Android aceita porque a chave é a mesma; se a chave mudar,
é preciso desinstalar antes.

## O que funciona sem internet

| Recurso | Offline |
|---|---|
| Jogar contra o bot (250–3200), relógio, dicas, desfazer | ✅ |
| Revisão de PGN colado/arquivo, precisão, classes, explicações | ✅ |
| Biblioteca de partidas | ✅ (`localStorage` do WebView) |
| Importar partidas do chess.com | ❌ precisa de internet |

Partidas ficam na memória do app; limpar os dados do app apaga a biblioteca.
Exporte o PGN antes (botão **Copiar PGN** na Biblioteca).

## Como o APK é construído

Não há Gradle: o build é `aapt2 → javac → d8 → zipalign → apksigner`, em
[`build.sh`](build.sh). Ele foi desenhado para rodar no runner do GitHub
(`.github/workflows/apk.yml`), porque o ambiente de desenvolvimento não tem JDK/SDK.

```
android/
├── AndroidManifest.xml          pacote br.com.xadrezstudio, minSdk 26, alvo 34
├── java/br/com/xadrezstudio/
│   ├── MainActivity.java        WebView + servidor local
│   └── ServidorLocal.java       HTTP só em 127.0.0.1 (para wasm funcionar)
├── res/mipmap-*/ic_launcher.png ícone (gerado por icone/gerar.py)
├── servidor/                    Stockfish 19 lite single-thread (js + wasm) + licença
├── icone/gerar.py               desenha o ícone em 5 densidades (PNG puro em Python)
└── build.sh                     build completo
```

### Detalhes que importam

- **Por que um servidor HTTP dentro do app:** o WebView não consegue buscar o
  `.wasm` do Stockfish por `file://` (origem opaca). Servindo os assets em
  `http://127.0.0.1:<porta>` tudo se comporta como no navegador: módulos ES,
  Web Worker e WebAssembly. O servidor escuta **apenas no loopback**, recusa
  caminhos com `..` e tenta as portas 8791–8810.
- **Assets:** `app/public` é copiado para `assets/www` (via `aapt2 -A`), mais o
  Stockfish de `android/servidor`. Total ~2,1 MB de assets, APK final ~1,3 MB.
- **Assinatura:** keystore gerada no primeiro build e guardada no **cache do
  Actions** (`apk-keystore-v1`); nunca vai para o repositório. Para assinar
  localmente, defina `android/keystore/xadrez.keystore` (o script reaproveita).
- **Armazenamento:** o app é aberto com `?armazenamento=local`, então a
  biblioteca usa `localStorage` em vez do `dados/jogos.json` do servidor.
  A importação do chess.com tenta a API direto do WebView.

## Compilar você mesmo

Com JDK 17 e Android SDK (build-tools + platform 34):

```bash
./android/build.sh          # gera dist/xadrez-studio-1.0.apk + .sha256 + build/apk-info.txt
```

Ou dispare o workflow **APK** em *Actions* (execução manual disponível), que
roda os testes do app e publica a release.

## Verificação feita no build

O log de cada build fica em `build/apk-info.txt` e vai como artifact:

```
APK: xadrez-studio-1.0.apk (1.3M, 1269 KB)
sha256: 7d51866a...
SDK: build-tools 37.0.0 · android-36 · minSdk 26 alvo 34
entradas no APK: 27
badging: package='br.com.xadrezstudio' versionName='1.0' label='Xadrez Studio'
         launchable-activity: br.com.xadrezstudio.MainActivity
assinatura: V3.0 Signer · CN=Xadrez Studio · SHA-256 18e3d2b6...
```

E o workflow falha o build se faltar `classes.dex`, `assets/www/index.html` ou o
`.wasm` do Stockfish.

## Limites conhecidos

- **Não foi testado em aparelho físico** por quem gerou o build: o APK é verificado
  (assinatura, manifest, conteúdo), mas o primeiro teste em celular é seu.
- Sem Play Store, sem atualização automática: versão nova = baixar e instalar por cima.
- Aparelho muito antigo ou com WebView desatualizado pode não rodar o WebAssembly —
  nesse caso use a versão web (`npm start`).
- A importação do chess.com dentro do app depende do CORS da API deles; se falhar,
  cole o PGN (exportado do site) na aba Analisar.
