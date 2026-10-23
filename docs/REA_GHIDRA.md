# REA + Ghidra — preparação das ferramentas de RE

> **Escopo deste documento.** Como instalar, configurar e **verificar** o REA
> (CLI/MCP de engenharia reversa) e o **Ghidra 12.1.4** usados nas próximas
> fases deste projeto, incluindo o JDK exigido pelos dois. Nada aqui depende da
> ROM comercial: a verificação usa uma **imagem ARM sintética**.
>
> Regra do projeto: fato ≠ hipótese. Cada item abaixo está marcado como
> **CONFIRMADO** (executado e observado), **PROVÁVEL** ou **PENDENTE**.

---

## 1. Resumo (o que é cada peça)

| Peça | Papel | Versão fixada | Por quê essa versão |
|---|---|---|---|
| **REA** (`rea-agents`) | CLI + servidor MCP que orquestra a análise (inspect/function/decompile, snapshots, evidência JSON) | **6.7.0** | release atual do `morluto/rea` (tag `rea-agents-6.7.0`, publicada em 18/10/2026; `npm view rea-agents dist-tags` → `latest: 6.7.0`) |
| **Ghidra** | engine nativa usada pelo provider `ghidra` do REA (análise, decompilação) | **12.1.4 PUBLIC** | o REA 6.7.0 **valida explicitamente a série 12.1.x**; a 12.2 (lançada em 22/10/2026) é rejeitada |
| **JDK (Temurin)** | compila os scripts Java do Ghidra (incluindo a bridge do REA) e é exigido pelo próprio REA | **21.0.13+9** (LTS) | Ghidra 12.1.4 declara `application.java.min=21` e `application.java.max=` vazio (aceita ≥ 21); REA aceita “64-bit full JDK 21 or newer” |

**Ponto crítico:** Ghidra e REA exigem um **JDK completo** (com `bin/javac`),
não uma JRE. O REA classifica o runtime olhando se existe
`$JAVA_HOME/bin/javac`; sem ele o doctor responde `runtime only` e o provider
fica **indisponível**.

---

## 2. Instalação automatizada (recomendada)

```bash
bash scripts/setup_re_tools.sh              # instala REA + JDK 21 + Ghidra 12.1.4
bash scripts/setup_re_tools.sh --dry-run    # só mostra o plano
bash scripts/setup_re_tools.sh --help       # todas as opções
```

O que o script faz:

1. **REA** — `npm install --global --prefix ~/.local rea-agents@6.7.0`
   (binário em `~/.local/bin/rea`).
2. **JDK** — baixa o Temurin **21.0.13+9** (Linux x64) do release oficial da
   Adoptium, confere o SHA-256 publicado em `.sha256.txt` e extrai em
   `~/.local/opt/re-tools/jdk-21.0.13+9`.
3. **Ghidra** — baixa o zip oficial `ghidra_12.1.4_PUBLIC_20260921.zip`,
   confere o **SHA-256 fixo**
   `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`
   (publicado nas release notes oficiais) e extrai em
   `~/.local/opt/re-tools/ghidra_12.1.4_PUBLIC`.
4. Escreve `~/.local/opt/re-tools/env.sh` com `JAVA_HOME`,
   `GHIDRA_INSTALL_DIR` e `PATH`.
5. Roda as verificações e resume o resultado (inclusive `rea doctor`).

Nada é instalado **dentro do repositório** e o script **não usa sudo**.

Opções úteis:

| Opção | Quando usar |
|---|---|
| `--prefix DIR` | instalar em outro lugar (ou `RE_TOOLS_DIR=...`) |
| `--jdk-home DIR` | você já tem um JDK 21+ extraído (ex.: `/usr/lib/jvm/temurin-21`) |
| `--ghidra-dir DIR` | você já tem o Ghidra 12.1.x extraído |
| `--ghidra-zip ARQ` / `--jdk-tarball ARQ` | instalação **offline**: baixe você mesmo os arquivos oficiais e passe o caminho |
| `--skip-rea` / `--skip-jdk` / `--skip-ghidra` | pular etapas |
| `--verify-only` | não instala nada, só diagnostica |
| `--strict` | sai com código 1 se a verificação falhar |

Depois de instalar:

```bash
source ~/.local/opt/re-tools/env.sh    # ou: source scripts/re_env.sh
bash scripts/re_tools_check.sh         # diagnóstico completo
bash scripts/rea_ghidra_smoke.sh       # teste ponta-a-ponta (imagem sintética)
```

> **`rea setup`** (registrar o MCP nos agentes) é interativo e **não** é
> executado pelo script. Rode quando quiser integrar com Claude Code/Codex/etc.;
> para uso via CLI nada disso é necessário.

---

## 3. Instalação manual (sem o script)

### 3.1 JDK 21 (Temurin, Linux x64)

```bash
mkdir -p ~/.local/opt/re-tools && cd ~/.local/opt/re-tools
base=https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9
file=OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz
curl -fLO "$base/$file"
curl -fLO "$base/$file.sha256.txt"
sha256sum -c "$file.sha256.txt"
tar -xzf "$file"
export JAVA_HOME="$PWD/jdk-21.0.13+9"
"$JAVA_HOME/bin/javac" -version   # tem que responder "javac 21.0.13"
```

### 3.2 Ghidra 12.1.4

```bash
cd ~/.local/opt/re-tools
url=https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip
curl -fLO "$url"
echo "ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db  ghidra_12.1.4_PUBLIC_20260921.zip" | sha256sum -c -
unzip -q ghidra_12.1.4_PUBLIC_20260921.zip
export GHIDRA_INSTALL_DIR="$PWD/ghidra_12.1.4_PUBLIC"
```

Confira a instalação:

```bash
grep -E 'application.version|application.release.name|application.java.min' \
  "$GHIDRA_INSTALL_DIR/Ghidra/application.properties"
# application.java.min=21
# application.release.name=PUBLIC
# application.version=12.1.4
```

### 3.3 REA

```bash
npm install --global --prefix ~/.local rea-agents@6.7.0
export PATH="$HOME/.local/bin:$PATH"
rea --version    # 6.7.0
```

### 3.4 macOS / Windows

O script cobre **Linux x86_64**. Nas outras plataformas:

- **macOS**: use o Temurin 21 para `x64`/`aarch64` (mesmo release da Adoptium) e o
  mesmo zip do Ghidra (ele traz o decompilador em
  `Ghidra/Features/Decompiler/os/mac_x86_64` ou `mac_arm_64`). Exporte
  `JAVA_HOME` e `GHIDRA_INSTALL_DIR` manualmente.
- **Windows**: Ghidra roda nativamente, mas o REA fala com ele em modo
  **P0 (experimental/read-only)** e **não aceita `raw-binary`** — ou seja, a
  integração REA→Ghidra **não funciona para a ROM de GBA no Windows nativo**.
  Guia dedicado: **[`WINDOWS.md`](WINDOWS.md)** (GUI, scripts `.ps1` e WSL).

---

## 4. Verificação (o que deve aparecer)

### 4.1 `scripts/re_tools_check.sh`

Com tudo instalado, a saída termina em:

```
-- REA --
  [ OK   ] node 22.x
  [ OK   ] rea 6.7.0 (...)
-- JDK --
  [ OK   ] java: openjdk version "21.0.13" ...
  [ OK   ] javac: javac 21.0.13
-- Ghidra --
  [ OK   ] versão: 12.1.4 (java.min=21)
  [ OK   ] analyzeHeadless executável
  [ OK   ] decompilador nativo: .../linux_x86_64/decompile
  [ OK   ] formato do binário: ELF 64-bit x86-64
-- rea doctor (provider ghidra) --
healthy=True provider_ghidra_available=True version=12.1.4
RESULTADO: stack RE pronto (REA + Ghidra + JDK).
```

Código de saída: `0` = pronto, `1` = falta algo (a mensagem diz o quê).

### 4.2 `scripts/rea_ghidra_smoke.sh`

Gera uma imagem ARM32 **sintética** (256 B, base `0x08000000`, sem nada da ROM)
e roda o REA com o provider Ghidra em modo `raw-binary`:

```
rea inspect  <img> --target-format raw-binary --architecture arm --entry-point 0x8000000 --provider ghidra
rea function <img> 0x8000000 ...
rea function <img> 0x800002c ...
```

As evidências (JSON) vão para `reports/re_tools/`. Códigos de saída:
`0` passou · `1` falhou · `3` pré-requisitos ausentes.

---

## 5. Uso no projeto (ROM de GBA)

> A ROM **não** está no repositório (regra do projeto). Coloque a sua cópia em
> `rom/` (já ignorado pelo git).

### 5.1 Caminho rápido (REA, raw-binary)

```bash
source scripts/re_env.sh
mkdir -p reports/rea

rea inspect rom/sua_rom.gba \
    --target-format raw-binary --architecture arm --entry-point 0x8000000 \
    --provider ghidra --format json > reports/rea/inspect.json

rea function rom/sua_rom.gba 0x08000A38 \
    --target-format raw-binary --architecture arm --entry-point 0x8000000 \
    --provider ghidra --format json > reports/rea/setgpureg.json
```

O arquivo inteiro é mapeado a partir de `0x08000000` e o Ghidra cria uma função
`entry` nesse endereço antes da auto-análise (comportamento documentado do REA
para alvos raw).

**Limite importante (HIPÓTESE a validar na Fase 2):** nessa lane o REA fixa a
linguagem em `ARM:LE:32:v7`. O GBA é **ARMv4T**. Instruções ARM comuns decodificam,
mas:

- código **Thumb** não é alternado automaticamente (o GBA usa Thumb em quase todo
  o jogo — `bx`/`blx` para endereço ímpar não são seguidos pela lane raw);
- instruções ARMv5+ (ex.: `blx`, `clz`) podem aparecer indevidamente em bytes que
  são dados.

Para análise completa e fiel da ROM, use o Ghidra diretamente (abaixo).

### 5.2 Caminho fiel (Ghidra com ARMv4T)

Pela GUI: `File > Import File…` → selecione a ROM → *Language* `ARM:LE:32:v4t`
→ *Options* do `BinaryLoader`: base `0x08000000` → OK → analisar.

Por linha de comando, use o importador do projeto — ele monta o comando acima
**mais** o mapa de memória do GBA, os rótulos e as seeds ARM/Thumb:

```bash
bash scripts/ghidra_import_gba.sh rom/sua_rom.gba
# equivalência (gerada por --dry-run):
#   analyzeHeadless <dir-projetos> gba_<sha8> -import rom/sua_rom.gba \
#     -processor ARM:LE:32:v4t \
#     -loader BinaryLoader -loader-baseAddr 0x08000000 -loader-blockName GBA_ROM \
#     -scriptPath scripts/ghidra_scripts \
#     -preScript GbaPrepareProgram.java pre reports/ghidra \
#     -postScript GbaPrepareProgram.java post reports/ghidra \
#     -overwrite -analysisTimeoutPerFile 1800 -max-cpu N \
#     -log reports/ghidra/analyzeHeadless.log -scriptlog reports/ghidra/ghidra_scripts.log
```

Todas essas opções foram conferidas no `support/analyzeHeadlessREADME.md` da
instalação local (inclusive o Exemplo 18 com `BinaryLoader` +
`-loader-baseAddr`) e no código-fonte oficial da tag `Ghidra_12.1.4_build`.
Detalhes, evidências e limites: **[`docs/GHIDRA_IMPORT.md`](GHIDRA_IMPORT.md)**.

### 5.3 Mapa de memória do GBA (referência GBATEK)

| Região | Endereço | Tamanho |
|---|---|---|
| BIOS | `0x00000000` | 16 KB |
| EWRAM | `0x02000000` | 256 KB |
| IWRAM | `0x03000000` | 32 KB |
| I/O | `0x04000000` | 1 KB |
| Palette | `0x05000000` | 1 KB |
| VRAM | `0x06000000` | 96 KB |
| OAM | `0x07000000` | 1 KB |
| ROM | `0x08000000` | até 32 MB |

Endereços já provados neste projeto (ver `README.md`): `SetGpuReg @ 0x08000A38`,
array da mochila `@ 0x020258B8` (4 B/slot, `{id:u16, qty:u16}`).
O smoke test usa esse mesmo `0x020258B8` como literal carregado por `ldr`.

### 5.4 Desempenho

- A ROM tem ~16 MB; a auto-análise completa no Ghidra é **pesada** (memória e
  tempo). Neste sandbox há 3,8 GB de RAM e 2 vCPU — trate análise completa como
  job demorado (dezenas de minutos) e prefira analisar funções específicas
  (`rea function <addr>`) ou usar `--snapshot` para reaproveitar sessões.
- O REA mantém **um Program por sessão**; `--snapshot` acelera consultas
  repetidas sobre o mesmo binário.

---

## 6. Arquivos criados neste repositório

| Arquivo | Função |
|---|---|
| `scripts/setup_re_tools.sh` | instalador (REA + JDK + Ghidra), idempotente, com SHA-256 e modo offline |
| `scripts/re_env.sh` | `source` para exportar `JAVA_HOME`, `GHIDRA_INSTALL_DIR` e `PATH` |
| `scripts/re_tools_check.sh` | diagnóstico + resumo do `rea doctor` (exit 0/1) |
| `scripts/make_synthetic_arm_image.py` | gera a imagem ARM32 sintética + `--self-test` (Capstone) |
| `scripts/rea_ghidra_smoke.sh` | teste ponta-a-ponta REA + Ghidra sobre a imagem sintética |
| `scripts/ghidra_import_gba.sh` | importa a ROM no Ghidra (ARMv4T + mapa do GBA + seeds) e valida |
| `scripts/ghidra_scripts/GbaPrepareProgram.java` | pre/post-script do import (blocos, cabeçalho, rótulos, seeds) |
| `scripts/gba_rom_header.py` | leitor de cabeçalho independente + `--compare` com o Ghidra |
| `reports/re_tools/` | evidências geradas pelo smoke test (JSON, sha256) |
| `.github/workflows/re-tools.yml` | CI manual (`workflow_dispatch`) que roda setup + check + smoke com internet normal |
| `scripts/win/setup_re_tools.ps1` | instalador para Windows (JDK 21 + Ghidra + REA) |
| `scripts/win/ghidra_import_gba.ps1` | importador para Windows (ARMv4T + mapa + rótulos) |
| `docs/WINDOWS.md` | guia Windows: GUI, PowerShell e WSL |

Todos os scripts foram passados no `bash -n` e no `shellcheck` (0.11.0, nível
style) e testados nos modos em que o ambiente permite (ver §7). O workflow
`.github/workflows/re-tools.yml` **não foi executado aqui** (ele existe
justamente para validar o caminho completo num runner com rede liberada —
dispare-o em *Actions → CI - RE tools → Run workflow*).

---

## 7. Estado real neste ambiente (evidência, sem enfeite)

O sandbox usado para preparar isto tem **acesso de rede restrito**: `github.com`,
`codeload.github.com`, `api.github.com`, `registry.npmjs.org` e `pypi.org`.
A CDN de **assets** do GitHub (`release-assets.githubusercontent.com`), para onde
todo `…/releases/download/…` redireciona, está **bloqueada** (erro de TLS).
Consequência: os dois downloads oficiais de ~208 MB (JDK) e ~570 MB (Ghidra) não
completam daqui.

| Item | Estado | Evidência |
|---|---|---|
| REA 6.7.0 instalado e funcional | **CONFIRMADO** | `rea --version` → `6.7.0`; `rea --help` lista `inspect`, `function`, `decompile`, `doctor`, `setup` etc. |
| Ghidra 12.1.4 PUBLIC extraído e reconhecido pelo REA | **CONFIRMADO** | `rea doctor` aprova `ghidra`, `ghidra-version=12.1.4`, `ghidra-headless`, `ghidra-native_decompiler` |
| Proveniência do Ghidra instalado | **CONFIRMADO** | `application.revision.ghidra=8b6bbb857accdfa20dc5b2f5dea471178c2e9fbc` = commit da tag oficial `Ghidra_12.1.4_build` (conferido em `api.github.com`) |
| Decompilador nativo | **CONFIRMADO** | `…/os/linux_x86_64/decompile` = ELF 64-bit x86-64; o REA valida “reports elf x86_64, which matches linux/x64” |
| **JDK 21 completo** | **PENDENTE (não instalável aqui)** | não existe `javac` na máquina; `jdk4py` (PyPI) é um *jlink runtime* sem `jdk.compiler` |
| `rea doctor` com JDK ausente | **CONFIRMADO** | `ghidra-java: ok=false, code=unsupported_version, detail="25.0.2; 64-bit; runtime only; … accepted a 64-bit full JDK 21 or newer"` → `provider_ghidra_available=false` |
| Ghidra recusa JRE | **CONFIRMADO** | `support/analyzeHeadless` com `JAVA_HOME` apontando para a JRE: `WARNING: JAVA_HOME environment specifies unsupported java version` + `ERROR: Unable to prompt user for JDK path, no TTY detected.` |
| Smoke test REA→Ghidra | **PENDENTE** | bloqueado pelo JDK acima; o script sai com código **3** e mensagem explícita |
| Sintaxe de raw-binary aceita pelo REA | **CONFIRMADO** | `rea inspect … --target-format raw-binary --architecture arm --entry-point 0x8000000 --provider ghidra` chega ao provider e falha só no runtime: `code=provider_unavailable`, `runtime_missing`, “Select a 64-bit full JDK 21 or newer on PATH, or set JAVA_HOME …” |
| Lane correta para GBA | **CONFIRMADO** | o próprio REA informa que “headerless raw-binary analysis requires the Ghidra adapter with a caller-supplied architecture and entry point” (Hopper/IDA/Kuna recusam raw-binary) |

**Nota de proveniência:** como a CDN de releases está bloqueada, o Ghidra usado
neste sandbox veio de um **espelho público** (`Chaborsz/Ghidra-12.1.4-Workspace`)
do **mesmo build oficial** — conferido pelo `application.revision.ghidra`
(commit da tag oficial) e por `application.release.name=PUBLIC`. Ainda assim,
isso **não** é uma verificação criptográfica do zip oficial: trate como
“sandbox apenas”. O `scripts/setup_re_tools.sh` **não** usa espelho nenhum —
ele baixa da NSA/GitHub e confere o SHA-256 oficial.

### O que falta para fechar (na sua máquina, com internet normal)

```bash
git pull
bash scripts/setup_re_tools.sh        # ~800 MB de download; ~1,5 GB em disco
bash scripts/re_tools_check.sh        # esperado: exit 0, provider_ghidra_available=True
bash scripts/rea_ghidra_smoke.sh      # esperado: exit 0, evidências em reports/re_tools/
```

Se você já tem JDK 21+ e/ou Ghidra 12.1.4:

```bash
bash scripts/setup_re_tools.sh --jdk-home /caminho/do/jdk-21 \
     --ghidra-dir /caminho/ghidra_12.1.4_PUBLIC --skip-rea
```

---

## 8. Troubleshooting

| Sintoma | Causa provável | Correção |
|---|---|---|
| `comando rea não encontrado` | `~/.local/bin` fora do `PATH` | `source scripts/re_env.sh` |
| doctor: `runtime only` / `accepted a 64-bit full JDK` | `JAVA_HOME` aponta para JRE | instale o **JDK** Temurin 21 e aponte `JAVA_HOME` para ele |
| Ghidra: `unsupported java version` | JDK < 21 **ou** JRE | use JDK ≥ 21 completo |
| doctor: `versão 12.2.0 fora da série 12.1.x` | Ghidra 12.2 | use 12.1.4 (pin do projeto) |
| `npm` reclama de permissão | prefixo global do sistema | use `--prefix ~/.local` (padrão do script) |
| download falha atrás de proxy/firewall | CDN de releases bloqueada | baixe manualmente e use `--ghidra-zip` / `--jdk-tarball` |
| `skill:identity` em `config_drift` | skill do REA não registrada | opcional: `rea setup` (não afeta a CLI) |
| pouca RAM na análise da ROM | auto-análise de 16 MB de código | analise funções específicas ou aumente a RAM |

---

## 9. Referências oficiais

- REA — <https://github.com/morluto/rea> · release `rea-agents-6.7.0`
- Ghidra — <https://github.com/NationalSecurityAgency/ghidra> · release
  `Ghidra_12.1.4_build` (SHA-256 do zip nas release notes)
- Eclipse Temurin 21 — <https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.13%2B9>
- GBATEK (mapa de memória/registradores do GBA) — Martin Korth
