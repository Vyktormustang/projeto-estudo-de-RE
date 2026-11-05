# SpeakNatural 🎙️

**Treine a sua pronúncia do inglês para soar natural de verdade.**

O app mostra uma frase do dia a dia em inglês. Você toca no microfone, lê em voz alta,
toca de novo para parar — e alguns segundos depois **cada palavra aparece colorida**:

| Cor | Nota | Significado |
|---|---|---|
| 🟩 Verde | 0,85 a 1,00 | você falou certo |
| 🟨 Amarelo | 0,50 a 0,84 | ficou perto, quase certo |
| 🟥 Vermelho | menos de 0,50 | som errado ou palavra que você pulou |

Toque em qualquer palavra colorida e o app abre os **sons** dela (em IPA), mostrando
**o som esperado x o som que ele ouviu** (ex.: esperado `iː`, ouvido `ɪ`) e uma
**dica em português** para corrigir. Tem botão para **ouvir a frase com voz nativa**
(voz do próprio celular/PC), **tentar de novo**, **próxima frase** — e uma aba
**Histórico** com as **palavras que mais te derrubam**.

> **Como funciona por baixo:** o servidor roda no **seu computador** (Python) e usa
> apenas modelos **open source e gratuitos**. Nada de conta, nada de chave de API,
> nada de nuvem paga. O áudio é analisado, as notas são salvas num banco SQLite local
> e o arquivo de áudio é **apagado na hora**.

---

## Índice

1. [O que você vai precisar](#1-o-que-você-vai-precisar)
2. [Mapa das pastas](#2-mapa-das-pastas)
3. [PASSO 1 — Instalar os programas no PC](#3-passo-1--instalar-os-programas-no-pc)
4. [PASSO 2 — Iniciar o servidor](#4-passo-2--iniciar-o-servidor)
5. [PASSO 3 — Testar no PC](#5-passo-3--testar-no-pc)
6. [PASSO 4 — Descobrir o IP do PC (e liberar o firewall)](#6-passo-4--descobrir-o-ip-do-pc-e-liberar-o-firewall)
7. [PASSO 5 — Subir o projeto para o GitHub](#7-passo-5--subir-o-projeto-para-o-github)
8. [PASSO 6 — Gerar o APK no GitHub (sem Android Studio)](#8-passo-6--gerar-o-apk-no-github-sem-android-studio)
9. [PASSO 7 — Instalar o APK no celular](#9-passo-7--instalar-o-apk-no-celular)
10. [PASSO 8 — Configurar o endereço do servidor no app](#10-passo-8--configurar-o-endereço-do-servidor-no-app)
11. [PASSO 9 — Usar o app](#11-passo-9--usar-o-app)
12. [Problemas comuns e como resolver](#12-problemas-comuns-e-como-resolver)
13. [Como a nota é calculada (transparência)](#13-como-a-nota-é-calculada-transparência)
14. [Limitações que você precisa saber](#14-limitações-que-você-precisa-saber)
15. [Para quem quiser mexer no código](#15-para-quem-quiser-mexer-no-código)
16. [Privacidade](#16-privacidade)
17. [Checklist final](#17-checklist-final)

---

## 1. O que você vai precisar

**No computador:**

* Windows 10/11 (64 bits) — ou Linux/macOS, os passos mudam pouco.
* **8 GB de RAM** (4 GB funciona, mas com paciência) e **5 GB livres** em disco.
* Internet para a primeira instalação (baixa ~2,5 GB de bibliotecas e ~1,7 GB de modelos).
* Python 3.11 ou 3.12, ffmpeg e espeak-ng — os três são gratuitos e vamos instalar juntos.
* O computador e o celular **no mesmo Wi‑Fi**.

**No celular:**

* Android 6 ou superior (o APK é gerado no GitHub; **iOS não é suportado** nesta versão).
* Um microfone (o do próprio celular serve).

**Tempo estimado na primeira vez:** 40 a 60 minutos (a maior parte é download).

---

## 2. Mapa das pastas

```
projeto-estudo-de-RE/
├── start-server.bat                ← atalho: duplo clique aqui (Windows)
├── start-server.sh                 ← atalho: ./start-server.sh (Linux/macOS)
├── .github/workflows/build-apk.yml ← gera o APK no GitHub (sem Android Studio)
└── speaknatural/
    ├── README.md                   ← este arquivo
    ├── start-server.bat            ← o script de verdade (Windows)
    ├── start-server.sh             ← o script de verdade (Linux/macOS)
    ├── docs/
    │   ├── API.md                  ← documentação da API (para curiosos)
    │   └── ARQUITETURA.md          ← como o código está organizado
    ├── backend/                    ← servidor Python (FastAPI + IA)
    │   ├── requirements.txt        ← versões exatas das bibliotecas
    │   ├── app/
    │   │   ├── main.py             ← onde tudo começa (API)
    │   │   ├── config.py           ← ajustes (modelos, limites, cores)
    │   │   ├── db.py               ← SQLite
    │   │   ├── models.py           ← tabelas (tentativas, palavras, estatísticas)
    │   │   ├── schemas.py          ← formato do JSON da API
    │   │   ├── api/                ← rotas: health, sentences, analyze, history
    │   │   ├── data/               ← as 40 frases + dicionário de fonemas de reserva
    │   │   └── services/           ← o "cérebro"
    │   │       ├── audio.py        ← converte áudio com ffmpeg, checa silêncio
    │   │       ├── asr.py          ← faster-whisper (o que você falou)
    │   │       ├── phoneme_recognizer.py ← wav2vec2 (os sons IPA)
    │   │       ├── g2p.py          ← fonemas esperados (espeak-ng)
    │   │       ├── align.py        ← alinhamento Needleman-Wunsch
    │   │       ├── scoring.py      ← fórmula das notas e das cores
    │   │       ├── tips.py         ← dicas em português
    │   │       └── analyzer.py     ← junta tudo
    │   ├── tests/                  ← 26 testes automáticos
    │   └── tools/                  ← gerador do dicionário de fonemas
    └── frontend/                   ← app React + Vite + TypeScript
        ├── package.json            ← versões exatas das dependências
        ├── capacitor.config.ts     ← configuração do APK
        ├── resources/              ← arte do ícone + gerador de ícones
        ├── src/                    ← telas: Praticar, Histórico, Servidor
        └── android/                ← projeto Android (já gerado e versionado)
```

> **Importante:** o `node_modules`, o `dist` e o `.venv` **não** estão no repositório
> (são gerados automaticamente) e já estão no `.gitignore`.

---

## 3. PASSO 1 — Instalar os programas no PC

### 1.1 Python 3.11 ou 3.12

1. Abra o navegador e vá em **https://www.python.org/downloads/**
2. Clique no botão amarelo **“Download Python 3.12.x”**.
3. Abra o arquivo baixado (`python-3.12.x-amd64.exe`).
4. ⚠️ **Na PRIMEIRA tela, marque a caixinha “Add python.exe to PATH”** (embaixo).
   Sem isso o servidor não acha o Python.
5. Clique em **“Install Now”** e espere. No fim, clique em **Close**.

**Conferir:** aperte a tecla Windows, digite `cmd` e abra o **Prompt de Comando**. Digite:

```bat
python --version
```

Tem que aparecer algo como `Python 3.12.7`. Se aparecer “não é reconhecido”, veja
[Problemas comuns](#12-problemas-comuns-e-como-resolver) (item 1).

### 1.2 ffmpeg (converte o áudio do celular)

**Opção A — mais rápida (Windows 10/11 com winget):**

No Prompt de Comando:

```bat
winget install Gyan.FFmpeg
```

Aceite os avisos. Depois **feche e abra o Prompt de novo** e confira:

```bat
ffmpeg -version
```

**Opção B — manual (se o winget não existir):**

1. Baixe **https://www.gyan.dev/ffmpeg/builds/** → arquivo `ffmpeg-release-essentials.zip`.
2. Extraia para `C:\ffmpeg` (dentro deve ficar `C:\ffmpeg\bin\ffmpeg.exe`).
3. Aperte Windows, digite `ambiente` e abra **“Editar as variáveis de ambiente do sistema”**.
4. Clique em **Variáveis de Ambiente** → na lista de baixo (**Path**) → **Editar** → **Novo**
   → digite `C:\ffmpeg\bin` → **OK** nas três janelas.
5. Feche e abra o Prompt de novo e rode `ffmpeg -version`.

> Sem o ffmpeg o app ainda funciona (usa um modo de emergência), mas só aceita áudio WAV.
> Instale: vale muito a pena.

### 1.3 espeak-ng (gera os fonemas “esperados”)

1. Abra **https://github.com/espeak-ng/espeak-ng/releases**
2. Na versão mais recente, clique em **Assets** e baixe o arquivo que termina em
   **`-x64.msi`** (ex.: `espeak-ng-1.51-x64.msi`).
3. Execute o instalador → **Next** até **Install** → **Finish**.
4. Feche e abra o Prompt de novo e confira:

```bat
where espeak-ng
```

Deve mostrar o caminho do `espeak-ng.exe`.

> **Sem o espeak-ng o app funciona** — ele usa um dicionário interno de fonemas
> (menos preciso) e mostra um aviso na tela.
>
> Se o instalador **não** colocou o espeak-ng no PATH, o servidor avisa isso na tela
> “Servidor” do app. Para resolver, rode o servidor apontando a pasta (Prompt, dentro de
> `speaknatural\backend`):
>
> ```bat
> set SN_ESPEAK_PATH=C:\Program Files\eSpeak NG
> ..\start-server.bat
> ```
>
> (ou adicione `C:\Program Files\eSpeak NG` ao `Path` do Windows e reabra o Prompt)

<details>
<summary><strong>Instalar no Linux (Ubuntu/Debian)</strong></summary>

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip ffmpeg espeak-ng
python3.11 --version
```
</details>

<details>
<summary><strong>Instalar no macOS</strong></summary>

Primeiro instale o Homebrew (https://brew.sh). Depois:

```bash
brew install python@3.12 ffmpeg espeak-ng
python3.12 --version
```
</details>

---

## 4. PASSO 2 — Iniciar o servidor

1. Abra a pasta do projeto (a que tem o `start-server.bat`).
2. **Dê dois cliques em `start-server.bat`.**
   * Também vale dois cliques no `start-server.bat` que está dentro de `speaknatural\`.
3. Vai abrir uma **janela preta**. Só na primeira vez ela faz isto (pode demorar bastante):

   ```
   [ok] Python encontrado: 3.12.7
   [..] Criando o ambiente virtual pela primeira vez...
   [..] Instalando as dependencias do Python.
        AVISO: a primeira vez baixa cerca de 2,5 GB...
   ```

   ☕ **Isso demora de 10 a 40 minutos** dependendo da internet. Não feche a janela.
   Se ela parecer “parada”, está baixando.

4. Quando terminar, aparece algo assim:

   ```
   [info] IP deste PC na rede: 192.168.0.15
   ==================================================
     Servidor no ar. NAO FECHE ESTA JANELA.
     No PC, abra:  http://localhost:8000
   ==================================================
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   ```

   ✅ **Anote o IP que apareceu** — você vai usar no celular.

5. Da segunda vez em diante, é só dar dois cliques: o servidor sobe em **~2 segundos**.

> **Deixe essa janela aberta sempre que for usar o app no celular.** Fechar a janela =
> desligar o servidor. Para parar: `Ctrl + C` ou simplesmente feche a janela.

<details>
<summary><strong>Linux / macOS</strong></summary>

```bash
chmod +x start-server.sh   # só na primeira vez
./start-server.sh
```
</details>

---

## 5. PASSO 3 — Testar no PC

Com o servidor no ar:

1. Abra o navegador e vá em **http://localhost:8000/health**

   Deve aparecer um texto parecido com:

   ```json
   {"status":"ok","version":"1.0.0","database":"sqlite","ffmpeg":true,
    "whisper":"small.en: nao carregado","phonemes":"...: nao carregado", ...}
   ```

   * `"ffmpeg": true` → ótimo. Se estiver `false`, revise o passo 1.2.
   * `"nao carregado"` nos modelos é **normal**: eles carregam na primeira análise.

2. (Opcional) Veja a documentação da API em **http://localhost:8000/docs**

### Quer usar o app no navegador do PC também?

Duas opções:

* **Sem instalar nada:** baixe o artifact **`speaknatural-web`** no GitHub (passo 6),
  descompacte dentro de `speaknatural/frontend/` de forma que fique
  `speaknatural/frontend/dist/index.html`, reinicie o servidor e abra
  **http://localhost:8000/**.
* **Com Node.js instalado** (para desenvolvimento): abra outra janela do Prompt,
  entre em `speaknatural\frontend` e rode `npm install` e depois `npm run dev`; abra
  **http://localhost:5173**.

> No navegador do PC, o microfone só funciona em `localhost` ou HTTPS — é uma regra
> de segurança dos navegadores. No APK funciona sempre.

---

## 6. PASSO 4 — Descobrir o IP do PC (e liberar o firewall)

O celular não enxerga “localhost”. Ele precisa do **IP do PC na rede Wi‑Fi**.

**Windows:** abra o Prompt e digite:

```bat
ipconfig
```

Procure a linha **“Endereço IPv4”** do seu Wi‑Fi (ex.: `192.168.0.15`). Ignore
`127.0.0.1` e endereços que começam com `169.254`.

**macOS:** `ipconfig getifaddr en0`
**Linux:** `ip addr show` ou `hostname -I`

> O script `start-server.bat` já mostra esse IP ao iniciar — é só copiar de lá.

### Firewall do Windows

Na **primeira vez** que o servidor sobe, o Windows pergunta:

> “Permitir que o Python se comunique nestas redes?”

Marque **Redes privadas** e clique em **Permitir acesso**. Se você fechou essa janela
sem querer:

1. Menu Iniciar → **Segurança do Windows** → **Firewall e proteção de rede**
2. **Permitir um aplicativo pelo firewall** → **Alterar configurações**
3. Procure **Python** (marque **Privada**) → **OK**

---

## 7. PASSO 5 — Subir o projeto para o GitHub

Você só precisa disto **uma vez**, para o GitHub gerar o APK para você.

### Se o projeto já está num repositório seu no GitHub

Pule para o **PASSO 6**. (Este projeto já está versionado — o workflow está em
`.github/workflows/build-apk.yml`.)

### Se você quer uma cópia sua

**Jeito mais simples (sem instalar nada):**

1. Entre em **https://github.com** e crie uma conta gratuita.
2. Clique em **+** (canto superior direito) → **New repository**.
3. Nome: `speaknatural` → marque **Public** → **Create repository**.
4. Na página que aparece, clique no link **“uploading an existing file”**.
5. **Arraste** as pastas `backend`, `frontend`, `docs`, `speaknatural` inteira (com os
   arquivos `start-server.*`) e a pasta oculta `.github`.
   * ⚠️ **Não arraste** `node_modules`, `dist`, `.venv` nem `backend/data`: são pesados
     e não são necessários (o `.gitignore` já os ignora se você usar Git).
   * No Windows, para ver a pasta `.github`: aba **Exibir** → marque **Itens ocultos**.
6. Escreva “SpeakNatural” na caixa de mensagem e clique em **Commit changes**.

**Jeito recomendado para o dia a dia:** instale o **GitHub Desktop**
(https://desktop.github.com), faça *Add local repository* e depois *Push origin* — ele
respeita o `.gitignore` automaticamente e é muito mais seguro.

> O workflow **precisa** estar em `.github/workflows/build-apk.yml` na **raiz** do
> repositório. Se ele não aparecer na aba *Actions*, o arquivo foi enviado para a
> pasta errada.

---

## 8. PASSO 6 — Gerar o APK no GitHub (sem Android Studio)

1. No seu repositório, clique na aba **Actions** (topo).
2. Na lista da esquerda, clique em **“SpeakNatural — APK”**.
3. Clique no botão **“Run workflow”** (direita) → mantenha a branch `main` →
   **Run workflow** (verde).
4. Atualize a página: aparece um item amarelo 🟡 rodando. Ele passa por:
   Node → JDK 17 → Android SDK → testes → build do APK (**5 a 8 minutos**).
5. Quando ficar **verde ✅**, clique no item → role até o fim da página →
   seção **Artifacts**:
   * **`speaknatural-apk`** → é o APK (o que você quer).
   * **`speaknatural-web`** → a versão para abrir no navegador do PC (opcional).
6. Baixe o `.zip`, e **descompacte**. Dentro está o `app-debug.apk`
   (e `SpeakNatural-1.0.0-debug.apk`, o mesmo arquivo com nome bonito).

### 🎁 Atalho: link direto do APK (mais fácil no celular)

Além do artifact, o workflow publica o APK numa **Release** do repositório. É o jeito
mais rápido de instalar: **o link abre no celular e baixa o `.apk` direto** (não precisa
de zip, nem de conta).

1. No seu repositório, clique em **Releases** (coluna da direita, na página inicial).
2. Abra a release **“SpeakNatural v1.0.0 — APK”**.
3. Na seção **Assets**, toque em **`SpeakNatural-1.0.0-debug.apk`** — o download começa.
4. Vá para o [PASSO 7](#9-passo-7--instalar-o-apk-no-celular).

> ⚠️ O APK debug é assinado com uma chave de teste do Android. É **normal** o Android
> avisar “app de fonte desconhecida”. Para uso pessoal, é exatamente assim que deve ser.
>
> Se o workflow falhar, veja [Problemas comuns](#12-problemas-comuns-e-como-resolver) (item 12).

---

## 9. PASSO 7 — Instalar o APK no celular

1. Envie o `app-debug.apk` para o celular de **qualquer** jeito:
   * **mais fácil:** abra o link da **Release** (veja o atalho no PASSO 6) no próprio
     celular e baixe o `.apk` — o arquivo cai na pasta *Downloads*;
   * Google Drive;
   * WhatsApp para você mesmo, como **documento**;
   * cabo USB, arrastando para a pasta *Downloads*.
2. No celular, toque no arquivo `.apk`.
3. O Android vai pedir **“Permitir instalar aplicativos desconhecidos”**:
   toque em **Configurações**, ative para o app que está abrindo o arquivo
   (Arquivos/Drive/Chrome) e volte.
4. Toque em **Instalar**. Se aparecer **“Play Protect não reconhece este app”** →
   **Instalar mesmo assim**.
5. Abra o **SpeakNatural** (ícone roxo com microfone).

Na primeira abertura, o app **vai pedir permissão de microfone** quando você tocar no
microfone — toque em **Permitir** (ou **Durante o uso do app**).

---

## 10. PASSO 8 — Configurar o endereço do servidor no app

1. No app, toque na aba **“Servidor”** (canto inferior direito).
2. No campo **“Endereço do servidor”**, digite o IP do PC do **PASSO 4**, assim:

   ```
   http://192.168.0.15:8000
   ```

   (troque `192.168.0.15` pelo IP que apareceu no seu PC — **não** esqueça o `http://`
   e o `:8000` no fim).
3. Toque em **Salvar endereço**.
4. Toque em **Testar conexão**.

   ✅ **Deu certo quando aparece uma faixa verde “Conectado!”** com a linha
   `Servidor 1.0.0 · http://192.168.0.15:8000`, `ffmpeg: instalado` etc.

   ❌ Se aparecer “Não consegui falar com o servidor”: veja o
   [Problemas comuns](#12-problemas-comuns-e-como-resolver) (itens 5 a 8).

O endereço fica salvo no celular — você só configura **uma vez**.

---

## 11. PASSO 9 — Usar o app

**Aba Praticar:**

1. Escolha o nível: **Fácil**, **Médio**, **Difícil** (ou **Todas**).
   As frases trazem fala natural de verdade: `I wanna…`, `gonna`, `should've`,
   `whatcha`, e palavras ligadas (`pick me up at the…`).
2. Leia a frase. Se quiser, toque em **“Ouvir primeiro”** para ouvir a voz de referência.
3. Toque no **botão redondo do microfone** 🎤 → leia a frase em voz alta →
   toque de novo no botão (vira ⏹) para parar.
4. Aguarde o botão girar em **“Analisando sua pronúncia...”**.
   *Na primeira vez pode levar 1 a 3 minutos* (o servidor baixa e carrega os modelos).
   Depois disso, cada frase leva de 3 a 20 segundos.
5. A frase volta **colorida**:
   * **Toque em uma palavra** → abre os sons dela: `Esperado /iː/` → `Você falou /ɪ/`,
     nota do som e **dica em português**.
   * **Ouvir referência** → voz nativa da frase.
   * **Tentar de novo** → grava outra vez a mesma frase.
   * **Próxima frase** → passa para a seguinte.
6. Embaixo da frase aparecem **avisos** (áudio baixo, ruído, ffmpeg faltando...).

**Aba Histórico:**

* Quantas tentativas você já fez, sua média e quantos dias seguidos está praticando.
* **Palavras mais difíceis**: ordenadas pela sua média, com barra de progresso.
  Comece por elas: toque em **Praticar** e repita frases com essas palavras.
* **Últimas tentativas**: frase, data e nota.

**Aba Servidor:**

* Endereço do PC, **Testar conexão**, tema claro/escuro e o passo a passo do IP.

💡 **Dicas de treino:** grave em um lugar silencioso, fale a ~20 cm do microfone,
não leia “soletrando” — leia como se estivesse conversando. Repita a mesma frase 3
vezes: verde em tudo é o sinal de que dominou.

---

## 12. Problemas comuns e como resolver

### Servidor / instalação

**1. “python não é reconhecido como nome de programa”**

* Reinstale o Python marcando **“Add python.exe to PATH”**, ou
* adicione manualmente `C:\Users\SEU_USUARIO\AppData\Local\Programs\Python\Python312`
  e `...\Python312\Scripts` ao `Path` (Variáveis de Ambiente), ou
* rode com o comando `py` no lugar de `python`.

**2. A janela do `start-server.bat` fecha na hora**
Rode clicando com o botão direito → **Executar como administrador**, ou abra o Prompt
na pasta e digite `start-server.bat` para ver a mensagem de erro completa.

**3. “A instalação das dependências falhou”**
Internet caiu, disco cheio ou antivírus bloqueando. Libere espaço (5 GB), desative
temporariamente o antivírus, apague `speaknatural\backend\.venv` e rode de novo.

**4. O servidor sobe mas `/health` mostra `"ffmpeg": false`**
O ffmpeg não está no PATH. Rode `ffmpeg -version` no Prompt; se não funcionar, refaça o
passo 1.2 (ou defina `SN_FFMPEG_BIN` com o caminho completo do `ffmpeg.exe`).

### Celular não conecta

**5. “Não consegui falar com o servidor” (app)**

Checklist, na ordem:
1. A janela preta do servidor está **aberta e sem erro**?
2. O celular está no **mesmo Wi‑Fi** do PC (não no 4G, não num Wi‑Fi “visitante")?
3. O endereço está com `http://` **e** `:8000`? Ex.: `http://192.168.0.15:8000`
   (sem barra no fim, sem “www”, sem espaço).
4. O IP mudou? Reinicie o servidor e compare com o IP mostrado na janela.
   (Dica: no roteador, fixe o IP do PC para não mudar.)
5. Firewall liberado? Veja o passo 4.
6. Teste no navegador **do celular**: abra `http://192.168.0.15:8000/health`.
   Se o navegador do celular mostra o JSON, o problema é só o campo do app.
   Se não mostra, é rede/firewall.

**6. Testei no navegador do celular e não abriu nada**
* O PC está com a rede marcada como **“Pública”** no Windows? Mude para **Privada**
  (Configurações → Rede e Internet → Wi‑Fi → propriedades → perfil de rede).
* Roteadores com “isolamento de clientes/AP isolation” bloqueiam PC↔celular:
  desligue essa opção no painel do roteador.
* Teste `ping 192.168.0.15` de outro aparelho.

**7. “Servidor encontrado, mas o endereço da API está errado”**
Você digitou uma porta errada (ex.: `:8080`). O padrão é `:8000`.

**8. Mudou o IP / mudou de rede**
Abra **Servidor** no app, corrija o endereço e toque em **Salvar endereço**.

**9. A porta 8000 está ocupada**
Outro programa usa a porta. No Prompt (pasta `speaknatural\backend`):

```bat
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

e no app use `http://IP:8080`.

### Análise / notas

**10. “O modelo de pronúncia ainda não está pronto no servidor” (503)**
A primeira análise baixa ~1,7 GB de modelos. Espere alguns minutos e tente de novo.
Se continuar: verifique internet/proxy, e olhe a janela do servidor (mostra o erro real).
Para baixar antes de usar o celular, rode uma análise de teste no PC
(`http://localhost:8000/docs` → `POST /analyze` → *Try it out*).

**11. “Não consegui ouvir nada na gravação” / “ficou curta demais”**
Grave pelo menos 1 segundo, fale mais alto e mais perto do microfone. Evite gravar
com música/ventilador perto.

**12. O workflow do GitHub falhou**
* Abra o run vermelho e veja qual passo falhou.
* `npm ci` falhou → o `package-lock.json` não foi enviado; envie-o.
* `gradlew` “Permission denied” → o passo já roda `chmod +x`; se persistir, garanta que
  o arquivo `speaknatural/frontend/android/gradlew` está no repositório.
* “SDK location not found” → o passo do Android SDK precisa rodar antes do Gradle
  (já está no workflow); rode o workflow de novo.
* Erro de memória no Gradle → rode novamente; o runner tem 7 GB.

**13. O APK não instala**
* “App não instalado” → desinstale a versão anterior e tente de novo.
* “Bloqueado por política” → Configurações → Segurança → **Fontes desconhecidas**
  para o app que está abrindo o arquivo.
* Android muito antigo (< 6.0) não é suportado.

**14. O app abre em branco no celular**
Normalmente é a versão web não copiada. Rode no PC, dentro de `speaknatural\frontend`:
`npm run build` e depois `npx cap sync android`, e gere o APK novamente pelo workflow.

**15. “Não consegui tocar a voz de referência”**
O Android precisa de um motor de voz com inglês: instale o **Google Text-to-Speech**
(Play Store) → Configurações → Sistema → Idiomas → Saída de texto para fala →
instale a voz **English (United States)**. No iPhone/navegador, veja as vozes do sistema.
O resto do app funciona sem isso.

**16. As notas parecem injustas / muito duras**
* O áudio da análise é o do **microfone do celular** (com compressão). Grave perto e
  em silêncio.
* Palavras muito curtas (`a`, `of`, `to`) são naturalmente instáveis.
* Se o aviso “dicionário embutido de fonemas” aparecer, instale o **espeak-ng** para
  ganhar precisão.
* Compare sempre com **Ouvir referência**: a nota é sobre os **sons**, não sobre o
  sotaque.

**17. O servidor fica lento / o PC trava**
É CPU pura. Feche outros programas pesados. Para acelerar, use um modelo menor
(menos preciso) antes de iniciar o servidor:

```bat
set SN_WHISPER_MODEL=base.en
start-server.bat
```

**18. Quero apagar meu histórico**
Feche o servidor e apague `speaknatural\backend\data\speaknatural.db`
(na próxima vez ele cria um banco vazio).

---

## 13. Como a nota é calculada (transparência)

Nada de “caixa-preta”. Para cada palavra:

1. **Fonemas esperados** — a palavra é convertida em sons IPA pelo **espeak-ng**
   (`speak` → `s p iː k`).
2. **Fonemas ouvidos** — o modelo **wav2vec2** (`facebook/wav2vec2-xlsr-53-espeak-cv-ft`)
   lê o trecho de áudio daquela palavra e devolve os sons IPA que ele reconheceu.
3. **Alinhamento (Needleman-Wunsch)** — as duas sequências são alinhadas som a som,
   como no alinhamento de DNA, permitindo detectar som **faltando** ou **sobrando**.
4. **Nota dos sons** — soma das similaridades ÷ tamanho da maior sequência:

   ```
   phoneme_score = Σ similaridade / max(nº esperados, nº ouvidos)
   ```

   | Comparação | Nota |
   |---|---|
   | som idêntico | 1,00 |
   | som parecido (`ɪ`↔`iː`, `ə`↔`ʌ`, `θ`↔`t`, `ɹ`↔`r`…) | 0,65 |
   | outra vogal | 0,30 |
   | outra consoante | 0,20 |
   | som ausente | 0,00 |

5. **Presença** — o **faster-whisper** (`small.en`, CPU int8) transcreve a gravação:
   palavra certa = 1,0 · parecida = 0,5 · não falada = 0,0.
6. **Nota da palavra** = `0,75 × nota_dos_sons + 0,25 × presença`
   (palavras de 1–2 sons, como “a” e “of”, usam 50/50 porque quase não há áudio para analisar).
   Palavra não falada fica travada em ≤ 0,25 → **vermelha**.
7. **Nota geral** = média das palavras **ponderada pelo número de sons** —
   errar “working” pesa mais que errar “a”.

As faixas de cor são exatamente as pedidas: **≥0,85 verde · 0,50–0,84 amarelo · <0,50 vermelho**.

A fórmula completa, com comentários linha a linha, está em
`backend/app/services/scoring.py` e `backend/app/services/align.py`.

---

## 14. Limitações que você precisa saber

1. **É CPU, não GPU.** Numa primeira análise, com modelos já baixados, conte **3–20 s**
   por frase (PC comum). A primeira análise é a mais lenta.
2. **A primeira execução baixa ~2,5 GB de bibliotecas e ~1,7 GB de modelos.** Precisa
   de internet uma vez; depois funciona offline (a voz de referência continua sendo a
   do aparelho).
3. **A nota é uma estimativa automática**, não um professor. Ela erra em palavras muito
   curtas, com ruído de fundo ou microfone ruim. Use como guia de treino.
4. **Sem autenticação.** O servidor é para a **sua rede local**. Não abra a porta 8000
   para a internet.
5. **Um aparelho/uma análise por vez** (proteção de memória: ~1,5 GB por análise).
6. **iOS não está incluído** (o APK é Android). A versão web funciona em qualquer
   navegador moderno.
7. **O APK é “debug”** (assinado com chave de teste). Para publicar na Play Store seria
   preciso assinar com uma chave própria — fora do escopo desta fase.
8. **Extensões futuras já preparadas:** modo conversa, contas de usuário e nuvem
   **não** existem, mas o banco (tabelas separadas), as rotas (pastas por assunto) e os
   serviços (um arquivo por etapa) estão organizados para recebê-los sem reescrever nada.

---

## 15. Para quem quiser mexer no código

### Backend (Python 3.11)

```bash
cd speaknatural/backend
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q                  # 26 testes (não baixam modelos)
python tools/gen_fallback_phonemes.py  # regenera o dicionário de reserva
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Testar **sem baixar os modelos** (útil em PC fraco/CI):

```bash
SN_FAKE_MODELS=1 uvicorn app.main:app --port 8000     # Windows: set SN_FAKE_MODELS=1
```

### Frontend (Node 20+)

```bash
cd speaknatural/frontend
npm install
npm run dev          # http://localhost:5173 (proxy automático para :8000)
npm test             # testes unitários (vitest)
npm run typecheck    # TypeScript
npm run build        # dist/
```

### APK localmente (opcional)

```bash
cd speaknatural/frontend
npm run build
npx cap sync android
cd android && ./gradlew assembleDebug     # precisa de JDK 17 + Android SDK
# APK em: android/app/build/outputs/apk/debug/app-debug.apk
```

### Trocar/adicionar frases

Edite `backend/app/data/sentences.py` (um dicionário por frase). Rode
`python tools/gen_fallback_phonemes.py` para atualizar o dicionário de reserva.
Recarregue o app — as frases vêm da API.

### Ajustar a “severidade” das notas

Em `backend/app/config.py`: `GREEN_MIN`, `YELLOW_MIN`, `NEAR_SOUND_SCORE`,
`GAP_PENALTY`. Ou pelas variáveis `SN_MIN_AUDIO_SECONDS`, `SN_SILENCE_RMS` etc.
(veja `docs/API.md`).

---

## 16. Privacidade

* O áudio vai **do seu celular para o seu PC**, pela sua própria rede Wi‑Fi.
* O arquivo de áudio é **apagado do disco** logo depois da análise (em `finally`,
  mesmo quando a análise falha).
* O que fica salvo é só **texto**: frase, notas por palavra, sons, data — num arquivo
  SQLite em `backend/data/speaknatural.db`.
* **Nenhuma conta, nenhum login, nenhuma chave de API, nenhum serviço pago.**
* Os modelos (faster-whisper, wav2vec2) são baixados uma única vez do Hugging Face e
  ficam em cache no seu PC; a partir daí, tudo roda offline.

---

## 17. Checklist final

Faça nesta ordem — cada linha tem que dar ✅ antes da próxima:

- [ ] **1.** Python 3.11/3.12 instalado com “Add python.exe to PATH” → `python --version` funciona
- [ ] **2.** `ffmpeg -version` funciona no Prompt
- [ ] **3.** `where espeak-ng` mostra um caminho (sem ele funciona, mas com menos precisão)
- [ ] **4.** Dois cliques em `start-server.bat` → mensagem “Servidor no ar”
- [ ] **5.** Abrir `http://localhost:8000/health` no PC → `"status":"ok"` e `"ffmpeg":true`
- [ ] **6.** Anotar o IP do PC mostrado na janela do servidor (`192.168.x.x`)
- [ ] **7.** Firewall liberado para o Python em **Redes privadas**
- [ ] **8.** Código no seu GitHub (com `.github/workflows/build-apk.yml` na raiz)
- [ ] **9.** Actions → **SpeakNatural — APK** → **Run workflow** → run **verde ✅**
- [ ] **10.** Baixar o artifact **speaknatural-apk** e descompactar `app-debug.apk`
- [ ] **11.** Instalar o APK no celular (permitir “fontes desconhecidas”)
- [ ] **12.** Abrir o app → aba **Servidor** → digitar `http://IP-DO-PC:8000` → **Salvar endereço**
- [ ] **13.** **Testar conexão** → faixa verde “Conectado!”
- [ ] **14.** Aba **Praticar** → permissão de microfone **Permitir** → gravar uma frase fácil
- [ ] **15.** Ver a frase colorida, tocar numa palavra e ler a dica
- [ ] **16.** Aba **Histórico** → a tentativa aparece lá com a nota

Pronto. A partir daqui, o seu treino é: **mesma frase até ficar tudo verde**, e
**começar sempre pelas palavras mais difíceis do histórico**. 🎯
