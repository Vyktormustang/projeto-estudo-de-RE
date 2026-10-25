# APK do Xadrez Studio

O mesmo app de `app/`, empacotado para Android. Roda **offline**: motor de xadrez,
regras, análise e biblioteca ficam dentro do aparelho.

## Baixar e instalar

**O APK fica no Google Drive, não no GitHub.**

- Arquivo: **<https://drive.google.com/file/d/1tXSVTCwu07ykM8X-idlw9rNwPdFM1Sbx/view>**
- Pasta (APK + checksum): **<https://drive.google.com/drive/folders/1-xOz3IsCInEwniaoNbLWc9XdsYX0_Yen>**
- Versão atual: **1.8** (`versionCode 9`) — instala **por cima** das anteriores, sem desinstalar
- `sha256`: `b1b531febd79417f33c9794db77e1b8f82a4dd17264e8fdb40ce3fad74decabf`
- Tamanho: 1.330.074 bytes · 41 entradas no APK

1. Baixe `xadrez-studio-1.8.apk`.
2. Confira o arquivo (opcional): baixe também `xadrez-studio-1.3.apk.sha256` e compare —
   `sha256sum xadrez-studio-1.8.apk`. O hash muda a cada build; o valor válido é sempre o
   do `.sha256` que está na mesma pasta do Drive.
3. No aparelho, abra o arquivo baixado e permita **"instalar de fontes desconhecidas"**
   para o navegador/gerenciador de arquivos.
4. Requisitos: **Android 8.0 (API 26)** ou superior, com **WebView atualizado**
   (o motor é WebAssembly e os módulos são ES6).

O app é assinado com chave própria (não vem da Play Store). O certificado atual —
que é o que permite instalar uma versão nova por cima, sem desinstalar — é:

```
CN=Xadrez Studio, OU=Uso pessoal, O=Xadrez Studio, L=Belem, ST=Para, C=BR
SHA-256: 89E0:FAD2:17BB:41C9:B730:E2C7:6668:0B66:C2CB:BD21:D3A4:5BCC:6B30:09CF:4D0F:234A
```

Esse certificado é reaproveitado entre builds pelo cache do Actions (chave
`apk-keystore-v2`), então versões novas instalam por cima sem desinstalar.

Para conferir no aparelho (ou no PC, com `apksigner`):
`apksigner verify --print-certs xadrez-studio-1.8.apk`.

## O que mudou na 1.8 (tabuleiro em tela cheia, traço original)

* **Peças de volta ao conjunto cburnett** (`standard`, Wikimedia, CC BY-SA 3.0): traço fino e
  detalhado, o desenho que o app usava até a 1.6. O conjunto próprio da 1.7 (silhueta cheia) saiu,
  junto com o gerador `tools/gerar-pecas.mjs` — o crédito e a licença voltam a valer e estão em
  `app/public/pecas/LEIA-ME.txt`.
* **Tabuleiro ocupando a tela de verdade**: caiu o teto de 980 px (que segurava o tabuleiro em
  monitores altos) e o *cromo* encolheu — avatar 30 px, botões da barra de ações 34 px, folgas de
  4 px e `main` com 8 px de respiro. O lado do tabuleiro passa a ser a **altura toda da janela menos
  o cromo**, e só é limitado pela largura que sobra ao lado do painel.
* No celular continua de ponta a ponta (100vw), e em tela deitada o cromo é 108/146 px.

## O que mudou na 1.7 (peças desenhadas aqui) — revertido na 1.8

* Conjunto de peças próprio, no espírito do *Neo*: silhueta cheia com contorno grosso. Funcionava,
  mas o traço do cburnett agradou mais — o desenho próprio saiu na 1.8 e o gerador foi removido.

## O que mudou na 1.6 (arrastar a peça com o dedo, de verdade)

* **Causa raiz do arraste que não funcionava no celular**: `.casa` tinha `touch-action: manipulation`.
  Com isso o navegador tratava o movimento do dedo como rolagem e mandava `pointercancel` no meio
  do gesto, então a peça voltava para a casa. Agora é `touch-action: none` na casa (o
  `.tabuleiro-wrap` já tinha), e a rolagem da página continua funcionando fora do tabuleiro.
* Arraste mais robusto: ignora um segundo dedo durante o gesto, limpa fantasma/realces em
  `lostpointercapture` (troca de aba, tela bloqueada) e mantém a peça elevada ~28 px acima do dedo
  para não ficar escondida por ele.
* Toque-toque continua funcionando, e o clique sintético que vem depois do gesto é ignorado
  (`pointerdown` já resolve seleção/lance) — sem lance duplicado.
* Acabamento no padrão chess.com: sombra leve nas peças, aro interno no tabuleiro, zebra na lista
  de lances e o lance atual com fundo `#4a4744`.
* `ui.smoke.mjs` agora com **33 verificações**, incluindo três específicas de arraste no dedo
  (touch-action correto, segundo dedo ignorado, perda de captura limpa o gesto).

## O que mudou na 1.5 (tabuleiro ocupando a tela)

* **Layout dirigido pela altura da janela**, como no chess.com: o lado do tabuleiro é
  `min(100dvh - cromo, 980px)`, onde o *cromo* (topo + linhas de jogador + barra de ações, e no
  Analisar também navegação + gráfico) é descontado por aba. No desktop o conjunto tabuleiro +
  painel fica centralizado e **cabe na tela sem rolagem**; antes havia um teto de 1060 px que
  deixava faixas vazias nas laterais e um tabuleiro pequeno.
* **Celular de ponta a ponta**: sem margem lateral, tabuleiro colado nas bordas (canto vivo, como
  no app), barra de avaliação reduzida a 5 px sobre a borda esquerda do tabuleiro, linhas de
  jogador e barra de ações com respiro de 10 px.
* **Deitado** (pouca altura): o tabuleiro é limitado pela janela e o resto rola.
* Painel lateral com altura da janela e rolagem interna (`position: sticky` no desktop).
* Coordenadas do tabuleiro acompanham o tamanho (`clamp(10px, 1.5vmin, 16px)`), em vez de 11 px fixos.
* Teste novo no `ui.smoke.mjs` (30 verificações) trava o orçamento de altura e o fim do teto antigo.

## O que mudou na 1.4 (classificação em cima da peça)

* **Selo da classe do lance sobre a peça**, como no game review: círculo com o símbolo
  (`??`, `?`, `?!`, `✓`, `★`, `!`, `!!`, `📖`) no canto da casa de destino, na cor da classe,
  desenhado em SVG (escala junto com a casa em qualquer tela) e com o fundo/texto ajustados
  para manter contraste nos selos amarelos e laranja.
* No **Analisar**, o selo acompanha a navegação (lista, setas do teclado, botões, gráfico) e
  desaparece na posição inicial. No **Jogar**, o mesmo selo marca o seu último lance quando o
  feedback está ligado, e é limpo ao desfazer ou começar outra partida.
* Z-index e `pointer-events: none` mantidos: o selo não intercepta o toque — o lance continua
  resolvido pela geometria da casa.

## O que mudou na 1.3 (velocidade da análise)

* **Revisão em paralelo**: até 3 Stockfish em Web Workers (`PoolAnalise`), um por núcleo livre,
  limitado pela memória do aparelho (`hardwareConcurrency`/`deviceMemory`).
* **2 linhas por posição em vez de 3**: medido com o mesmo build no PC, depth 14 custa ~389 ms
  com MultiPV 3 e ~55 ms com MultiPV 2 — o Stockfish refaz a busca para cada linha, e a 3ª linha
  só era exibida no relatório.
* **Cache em memória** por FEN: revisar de novo a mesma partida (ou outra com a mesma abertura)
  não consulta o motor.
* **Perfis**: Automática (depth 14, desce para 12 em partidas longas), Rápida (12),
  Profunda (16), Máxima (18) — com teto de tempo por posição e partida longa distribuída
  no orçamento. A tela mostra núcleos usados, ETA e o tempo final da revisão.
* **Motor separado para as assistências** do modo Jogar: antes a análise da sua vez entrava na
  mesma fila do lance do bot, e o bot só respondia depois dela — agora não atrapalha mais.
  A assistência também só roda se a barra de avaliação ou o feedback estiverem ligados.
* Hash enxuto por worker (12–24 MB) para caber em celular.

## O que mudou na 1.2

* **Arrastar peças** com o dedo, com a caneta e com o mouse (Pointer Events): tocar seleciona,
  mover levanta a peça, soltar na casa legal executa o lance; a peça flutuante fica acima do
  dedo, a origem fica esvaziada e a casa sob o dedo ganha realce. Soltar fora de um destino legal
  desmarca; o toque curto continua valendo (tap-tap).
* `touch-action: none` no tabuleiro — arrastar peça não rola mais a página no meio do gesto.
* Ícones das abas e da barra de ações em **SVG** (antes eram glifos Unicode), marca com o cavalo
  branco sobre o quadrado verde e relógio no tamanho do chess.com.
* **Cartão de fim de jogo** com *Revanche*, *Analisar* e *ver o tabuleiro*.
* `ui.smoke.mjs` cobre arraste no dedo, arraste no mouse, soltura inválida, tap-tap e o cartão de
  resultado — 21 verificações de interface.

## O que mudou na 1.1

A 1.0 abria, mas **não deixava mover as peças**. Causa encontrada: o overlay de
promoção (`#promo-jogar`) tinha `display: flex` no CSS, o que vence o atributo
`hidden` do HTML — sobrava uma camada invisível cobrindo o tabuleiro inteiro e os
toques nunca chegavam às casas. Os testes em jsdom não pegavam porque chamam
`.click()` direto na casa, sem hit-testing.

Além da correção:

* `[hidden] { display: none !important }` no CSS (fecha essa classe de bug de vez);
* a casa é resolvida pela **geometria** do tabuleiro (8×8), não pelo elemento sob o dedo;
* arrastar com o mouse e tocar-para-selecionar/toque-para-mover no celular;
* a partida **começa sozinha** ao abrir (antes era preciso achar "Começar partida");
* interface refeita com referência no chess.com: topo escuro, abas, barra de avaliação
  ao lado do tabuleiro, linhas de jogador com avatar e relógio, barra de ações
  (girar/desfazer/dica/desistir) e navegação inferior no celular;
* peças em **SVG** (conjunto cburnett, CC BY-SA 3.0 — ver `app/public/pecas/LEIA-ME.txt`)
  no lugar dos glifos Unicode;
* caminhos relativos (`styles.css`, `js/main.js`, `pecas/`), então o app abre mesmo se o
  servidor local cair para `file://`;
* "Sobre / diagnóstico" na Biblioteca mostra versão, WebView, wasm e modo de armazenamento.

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

Ou dispare o workflow **APK** em *Actions*, que roda os testes, compila e verifica.
**O workflow não publica o arquivo** — ele só guarda os logs do build (7 dias). Isso é
proposital: binário não fica no GitHub. Para pegar o APK de um build do CI sem ter JDK/SDK
na máquina, o caminho usado foi um branch órfão temporário (`apk-transfer`) que é clonado
e apagado em seguida; se precisar repetir, recrie a etapa no workflow, baixe, rode o
upload e apague o branch de novo.

## Verificação feita no build

O log de cada build fica em `build/apk-info.txt` e vai como artifact:

```
APK: xadrez-studio-1.0.apk (1.3M, 1269 KB)
sha256: <hash do build>
SDK: build-tools 37.0.0 · android-36 · minSdk 26 alvo 34
entradas no APK: 27
badging: package='br.com.xadrezstudio' versionName='1.0' label='Xadrez Studio'
         launchable-activity: br.com.xadrezstudio.MainActivity
assinatura: V3.0 Signer · CN=Xadrez Studio · SHA-256 <certificado>
```

O **certificado** (não o hash do APK) é o que precisa ficar estável entre builds — é ele
que permite instalar por cima. Ele fica no cache do Actions, chave `apk-keystore-v1`.

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
