# android_re — toolkit de Engenharia Reversa de APK

Trilha do projeto para **compreender funcionalidades de apps Android** (DEX + resources + bibliotecas nativas),
aplicando o mesmo contrato de verdade do `gba-re`: **FATO / INFERÊNCIA / HIPÓTESE** rotulados, tudo
reproduzível por comando, nada de "achismo" no relatório.

> **Status desta trilha:** pipeline funcionando e validado (`self-test` OK). O APK-alvo (xadrez) **ainda não
> está disponível**: o arquivo do Drive é outro app (ver §1). A análise do site do chess.com, que serve de
> especificação de referência da jogabilidade, está em [`../pesquisa/chesscom/jogabilidade.md`](../pesquisa/chesscom/jogabilidade.md).

---

## 1. Achado sobre o arquivo do Drive (evidência, não opinião)

O arquivo `uptodown-com.chess.apk` (15.560.578 B, sha256 `dc885921fc2d141a53906675bd555f6f5d3705119f37f892d3edf3e61b342550`)
**não é** um app de xadrez:

| Campo | Valor observado |
|---|---|
| package | `com.uptodown` |
| app_name | **Uptodown App Store** |
| versionName / versionCode | 7.41 / 741 |
| minSdk / targetSdk | 23 / 36 |
| main activity | `com.uptodown.activities.MainActivity` |
| assinatura | `CN=Uptodown Technologies SL`, O/U=Uptodown, Málaga/ES — RSA PKCS#1 v1.5 |
| ocorrências de "chess" no DEX | **1** (substring de `chesScroll`) |

Ou seja: baixou-se a **loja** Uptodown, não o jogo. Provável causa: a página do Uptodown embrulha o
download atrás de uma página de oferta que entrega o próprio app da loja. O pipeline foi executado nele
de qualquer forma para (a) validar o toolkit em binário real e (b) documentar o que existe hoje.

Relatórios gerados: `reports/triage.md`, `components.md`, `permissions.md`, `code_map.md`, `strings.md`,
`native.md`, `features.md` + JSONs equivalentes e `native/*.disasm.txt`.

---

## 2. Uso

```bash
# ambiente (venv local, fora do git)
python3 -m venv .venv && . .venv/bin/activate
pip install androguard pypcode pyelftools capstone

# validação do toolkit (sem APK)
python3 scripts/apkre.py self-test

# análise completa de um APK
python3 scripts/apkre.py all --apk caminho.apk --out reports

# subcomandos isolados
python3 scripts/apkre.py triage      --apk a.apk --out reports   # hashes, manifest, SDK, assinatura, censo, entropia
python3 scripts/apkre.py components  --apk a.apk --out reports   # activities/services/receivers/providers, exported, deep links
python3 scripts/apkre.py permissions --apk a.apk --out reports   # permissões + risco + indícios de uso no DEX
python3 scripts/apkre.py code        --apk a.apk --out reports   # DEX→classes/pacotes, fingerprint de SDKs
python3 scripts/apkre.py strings     --apk a.apk --out reports   # URLs/domínios/e-mails/padrões de segredo
python3 scripts/apkre.py native      --apk a.apk --out reports   # ELF: exports JNI→Java, imports, disasm amostral
python3 scripts/apkre.py features    --apk a.apk --out reports --rules rules
```

Saída é **sempre** um par `.json` (dado bruto, para diff/CI) + `.md` (leitura humana). O JSON é a fonte
de verdade; o `.md` é derivado.

### `rules/` — funcionalidades por regra
`rules/*.json` descrevem "funcionalidade → padrões a procurar". O grau de confiança é calculado:
**CONFIRMADO** (≥3 indícios independentes) · **PROVÁVEL** (1–2) · **AUSENTE** (0).
O ruleset `chess` já incluso procura: motor UCI/Stockfish, FEN, PGN, modos (puzzle/lição/blitz/bullet),
renderização de tabuleiro, rating/Elo.

---

## 3. Leitura do relatório (o que cada seção prova)

- **`triage.md`** — identidade não forjável: sha256 do APK, package, versão, SDK, certificado. É o "DNA"
  do binário; qualquer conclusão depois disso é ancorada nesses hashes.
- **`components.md`** — superfície de ataque e de funcionalidade: componentes **exportados sem
  permissão**, deep links (`scheme://host/path`) que terceiros podem acionar, providers expostos.
- **`permissions.md`** — capacidade declarada × evidência de uso no DEX (evita "permissão declarada e
  nunca usada" e detecta "usa API sensível sem permissão declarada").
- **`code_map.md`** — tamanho do código, SDKs (Compose, Firebase, OkHttp, billing, Unity...), áreas
  quentes (instalação, rede, licença, proteção).
- **`strings.md`** — infraestrutura de rede e vazamentos de configuração (chaves, buckets, endpoints).
- **`native.md`** — `.so`, símbolos exportados, **entradas JNI traduzidas para `pacote.Classe#método`**
  (é por aí que se chega ao motor de xadrez, se ele for nativo).
- **`features.md`** — inferência de funcionalidades com nível de confiança.

---

## 3.1 Precisão do matcher de funcionalidades (o que ele **não** faz)

Vale registrar o histórico, porque é o tipo de erro que contamina relatório de RE: a primeira versão
casava substring pura e produzia falso-positivo absurdo — `rating` casando `batteryVelocity`,
`solution` casando `DownResolution`, `Java_` casando `JAVA_CONSUMER` (ou seja: "Motor de xadrez:
CONFIRMADO" num APK que não tem xadrez). Correções aplicadas:

1. **Fronteira de token** para padrão curto (≤4 chars) ou todo minúsculo: `fen` não casa `definition`.
2. **CamelCase/identificador** (ex.: `BoardView`, `getBuyIntent`) continua casando como fragmento.
3. **Strings implausíveis descartadas** (payload de regex/JSON >160 chars) e **classe vale 2**, string vale 1.
4. `AUSENTE` **não** é prova de inexistência — pode estar em código nativo/ofuscado. É hipótese nula, não laudo.

Resultado no APK disponível (ruleset `chess`, corpus 142.267 strings / 22.373 classes): **12 de 13
regras AUSENTE**, o que corrobora de forma independente o achado do §1 (não é app de xadrez).

## 4. Ghidra (decompilação real) — plano e bloqueio

`ghidra/headless_run.sh` está pronto para rodar `analyzeHeadless` com um script de export. Ele **não
rodou neste ambiente**, e a razão é objetiva:

- `java` não existe no sandbox e não há repositório APT acessível (rede liberada só para GitHub API,
  npm e PyPI; `deb.debian.org` e os hosts de *release assets* do GitHub respondem bloqueado).
- O pypi **não** distribui Ghidra. Existe `pyghidra`, mas é só bindings: exige uma instalação local do
  Ghidra; e `jdk4py` (JDK via PyPI) também não está no índice permitido.

Enquanto isso, a análise nativa usa **capstone** (ARM64) para disassembly amostral — que é o mesmo
backend que o Ghidra usaria para instruções, mas **sem** decompilação para pseudo-C, sem
propagação de tipos e sem renomeação. Portanto: **nada de conclusões "decompiladas" até o Ghidra rodar.**

Rodando localmente (com JDK 21+ e Ghidra 11/12 descompactado):

```bash
export GHIDRA_HOME=/opt/ghidra_PUBLIC
bash ghidra/headless_run.sh lib/arm64-v8a/libalgummotor.so
```

---

## 5. Regras de convivência

1. **APK nunca entra no git** (`.gitignore` cobre `*.apk`, `*.aab`, `google_drive/`).
2. Relatório é derivado do binário: sempre citar `sha256` do APK analisado.
3. Não declarar "existe/é usado" sem apontar o indício (classe, string, símbolo).
4. O que é dedução vai marcado como **INFERIDO** — inclusive arquitetura, que nunca é "vista".
