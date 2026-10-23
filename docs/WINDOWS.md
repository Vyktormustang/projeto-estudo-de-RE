# Windows — o que fazer quando "bash não é reconhecido"

> **Sintoma:** ao rodar `bash scripts/setup_re_tools.sh` no Windows aparece
> *"bash não é reconhecido como um comando interno ou externo"* (cmd) ou
> *"The term 'bash' is not recognized"* (PowerShell).
>
> **Causa:** `bash` é o terminal do Linux. O Windows tem **PowerShell** e **cmd**;
> os scripts deste repositório foram escritos para Linux/macOS. Isso **não** é
> erro do projeto — é diferença de sistema operacional.

---

## 1. Escolha o caminho

| Caminho | Serve para | Dificuldade | O que funciona |
|---|---|---|---|
| **A. Ghidra na GUI** (sem script) | abrir a ROM e olhar o código | ⭐ fácil | Ghidra completo |
| **B. Scripts PowerShell** (novos) | automatizar instalação + import | ⭐⭐ médio | Ghidra completo; REA pela metade¹ |
| **C. WSL** (Ubuntu dentro do Windows) | fluxo completo do repositório | ⭐⭐⭐ | tudo, inclusive REA + Ghidra |

¹ **Limite importante:** no Windows nativo o REA conversa com o Ghidra em modo
**P0 (somente leitura)** e **não aceita** `--target-format raw-binary`. Como a ROM
de GBA é analisada justamente como raw-binary ARM, a integração
REA → Ghidra **não funciona no Windows nativo**. O Ghidra sozinho funciona
normalmente. Para ter os dois, use WSL (caminho C).

---

## 2. Caminho A — Ghidra na interface gráfica (o mais simples)

### 2.1 Instalar o Java 21 (obrigatório)

Abra o **PowerShell** (botão direito no menu Iniciar → *Terminal* ou
*Windows PowerShell*) e cole:

```powershell
winget install --exact --id EclipseAdoptium.Temurin.21.JDK --accept-source-agreements --accept-package-agreements
```

Sem `winget`? Baixe em <https://adoptium.net/temurin/releases/?os=windows&version=21&package=jdk>
(o arquivo `.msi` x64). **Precisa ser JDK (com `javac`), não JRE.**

### 2.2 Baixar o Ghidra 12.1.4

```powershell
cd $env:USERPROFILE\Downloads
curl.exe -L -o ghidra_12.1.4.zip "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip"
Get-FileHash .\ghidra_12.1.4.zip -Algorithm SHA256
```

O hash **deve** ser:

```
DDAC49F903DA9D5BAC833E5CC79395098B9C33CFD3279BE5F31BD00387D2D4DB
```

Se não bater, apague e baixe de novo do link oficial.

### 2.3 Extrair e abrir

```powershell
Expand-Archive .\ghidra_12.1.4.zip -DestinationPath $env:USERPROFILE\tools
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"   # ajuste a versão
& "$env:USERPROFILE\tools\ghidra_12.1.4_PUBLIC\ghidraRun.bat"
```

Ajuste o caminho do JDK conforme o que o `winget` instalou (veja em
`C:\Program Files\Eclipse Adoptium\`).

### 2.4 Importar a ROM (os 4 cliques que importam)

1. `File → Import File…` e escolha sua ROM `.gba`.
2. Na janela **Import**, clique no **`?`** ao lado de *Language* e escolha
   **`ARM:LE:32:v4t`** (não aceite o padrão).
3. Clique em **Options** (botão ao lado do formato) → `Block Name`: `GBA_ROM`,
   **`Base Address`: `08000000`**.
4. **OK** → **Import** → na pergunta seguinte, **Yes** para analisar.

> Por que `v4t`: o GBA é ARMv4T. O modo Thumb (usado na maior parte do código)
> só é seguido corretamente nessa variante.

### 2.5 Criar os blocos de memória (para ponteiros resolverem)

`Window → Memory Map` → botão direito → *Add Memory Block* (ou `M`):

| Nome | Start | Length | Permissões |
|---|---|---|---|
| `GBA_EWRAM_256K` | `02000000` | `40000` | RW |
| `GBA_IWRAM_32K` | `03000000` | `8000` | RW |
| `GBA_IO_REGISTERS` | `04000000` | `400` | RW |
| `GBA_PALETTE_RAM` | `05000000` | `400` | RW |
| `GBA_VRAM_96K` | `06000000` | `18000` | RW |
| `GBA_OAM` | `07000000` | `400` | RW |

Sem isso, `ldr r0, =0x020258B8` aparece como "address not in memory".

### 2.6 Rotular o que o projeto já provou

`G` (Go To) → digite o endereço → `L` (Label) → nome:

| Endereço | Nome |
|---|---|
| `08000000` | `gba_cart_header` |
| `020258B8` | `gBagSlots_slot0` |
| `08000A38` | `SetGpuReg` |
| `04000130` | `REG_KEYINPUT` |
| `03003118` | `gKeysMirror_HIPOTESE` |

> Os três primeiros são **fatos** do projeto (README/HANDOFF). O último é
> **hipótese**: o HANDOFF registra que ele zera em certas cenas.

---

## 3. Caminho B — scripts PowerShell (automatiza A)

Dois scripts novos, equivalentes aos `.sh`:

```
scripts\win\setup_re_tools.ps1       instala JDK 21 + Ghidra 12.1.4 + REA 6.7.0
scripts\win\ghidra_import_gba.ps1    importa a ROM com ARMv4T + mapa + rótulos
```

Na pasta do repositório, no PowerShell:

```powershell
# 1) ver o plano sem instalar nada
powershell -ExecutionPolicy Bypass -File scripts\win\setup_re_tools.ps1 -DryRun

# 2) instalar (baixa ~800 MB)
powershell -ExecutionPolicy Bypass -File scripts\win\setup_re_tools.ps1

# 3) FECHE e abra o PowerShell de novo (para pegar JAVA_HOME/PATH)

# 4) importar a ROM
powershell -ExecutionPolicy Bypass -File scripts\win\ghidra_import_gba.ps1 -Rom "C:\roms\sua_rom.gba"

# 5) testar sem a ROM (gera uma ROM sintética de 32 KB)
powershell -ExecutionPolicy Bypass -File scripts\win\setup_re_tools.ps1 -VerifyOnly
```

Se já tem as coisas instaladas:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\win\setup_re_tools.ps1 `
    -JdkHome "C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot" `
    -GhidraDir "C:\tools\ghidra_12.1.4_PUBLIC" -SkipRea
```

O que o `setup_re_tools.ps1` faz:

1. **JDK 21** — tenta `winget`; se não houver, baixa da **API oficial da
   Adoptium** e confere o SHA-256 que vem no mesmo JSON.
2. **Ghidra 12.1.4** — zip oficial da NSA com **SHA-256 fixo** (o mesmo do
   script Linux).
3. **REA 6.7.0** — `npm install -g rea-agents@6.7.0` (precisa do Node.js 22 LTS).
4. Define `JAVA_HOME`, `GHIDRA_INSTALL_DIR` e o `PATH` **do usuário**.
5. Verifica tudo e roda `rea doctor`.

Nada é instalado dentro do repositório: vai para `%LOCALAPPDATA%\re-tools`.

> **Transparência:** esses dois `.ps1` foram escritos e revisados, mas **não
> puderam ser executados** no ambiente onde o projeto é desenvolvido (Linux, sem
> PowerShell). Se algo falhar, o caminho A (GUI) sempre funciona e é o plano B.

---

## 3.5 Caminho B2 — sem JDK: PyGhidra (só Java runtime)

O Ghidra oficial exige **JDK completo** (com `javac`) no launcher. Se você só
tem Java 21+ de runtime (ou nenhum Java ainda), use o motor PyGhidra — ele roda
o import, o mapa de memória, a análise e o **decompilador** sem `javac`:

```powershell
# 1) Java 21+ runtime (se ainda não tiver). O JDK também serve.
winget install --exact --id EclipseAdoptium.Temurin.21.JRE --accept-source-agreements --accept-package-agreements

# 2) PyGhidra
py -m pip install pyghidra

# 3) Ghidra 12.1.4 (só extrair; não precisa rodar ghidraRun)
cd $env:USERPROFILE\Downloads
curl.exe -L -o ghidra_12.1.4.zip "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip"

# 4) variáveis e import (motor detectado sozinho)
$env:GHIDRA_INSTALL_DIR = "$env:USERPROFILE\tools\ghidra_12.1.4_PUBLIC"
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jre-21.0.13.9-hotspot"
py scripts\ghidra_prepare_pyghidra.py C:\roms\sua_rom.gba
```

Para abrir o resultado na interface gráfica depois, é preciso o **JDK** (a GUI
também passa pelo `LaunchSupport -jdk_home`). Sem JDK, o resultado fica nos
JSONs de evidência e no projeto Ghidra salvo — que pode ser aberto em outra
máquina com JDK.

> **Confirmado neste projeto:** o motor PyGhidra foi executado com Java 25
> *runtime only* e descompilou a função de entrada da ROM sintética
> (`docs/GHIDRA_IMPORT.md` §8).

## 4. Caminho C — WSL (para ter REA + Ghidra juntos)

Se você quer o fluxo completo do projeto (REA conversando com o Ghidra), precisa
de um Linux. No Windows 11 isso é nativo:

```powershell
wsl --install -d Ubuntu
```

Reinicie, abra o **Ubuntu** no menu Iniciar e, dentro dele:

```bash
sudo apt update && sudo apt install -y curl unzip python3
git clone https://github.com/Vyktormustang/projeto-estudo-de-RE.git
cd projeto-estudo-de-RE
bash scripts/setup_re_tools.sh
bash scripts/re_tools_check.sh
bash scripts/ghidra_import_gba.sh rom/sua_rom.gba
```

Coloque a ROM em `rom/` (essa pasta é ignorada pelo git). Se a pasta do projeto
estiver no Windows (`C:`), ela aparece no WSL em `/mnt/c/...` — funciona, só é
um pouco mais lento.

GUI do Ghidra dentro do WSL: no **Windows 11** o WSLg mostra a janela
automaticamente (`"$GHIDRA_INSTALL_DIR/ghidraRun"`). No Windows 10 precisaria de
um servidor X — nesse caso use o caminho A para a GUI e o WSL para automação.

---

## 5. Resumo em uma tabela

| Você quer… | Faça |
|---|---|
| só abrir a ROM e olhar | **Caminho A** (Ghidra GUI) |
| automatizar instalação no Windows | **Caminho B** (`setup_re_tools.ps1`) |
| REA + Ghidra juntos | **Caminho C** (WSL) |
| testar sem a ROM | `scripts\win\ghidra_import_gba.ps1` + ROM sintética, ou `make_synthetic_arm_image.py --gba-rom` (precisa Python) |

---

## 6. Erros comuns no Windows

| Mensagem | Causa | Solução |
|---|---|---|
| `bash não é reconhecido` | Windows | este documento (A, B ou C) |
| `... não pode ser carregado porque a execução de scripts foi desabilitada` | ExecutionPolicy | rode com `powershell -ExecutionPolicy Bypass -File ...` |
| `npm não encontrado` | Node.js ausente | instale o Node 22 LTS em <https://nodejs.org> |
| `Unable to prompt user for JDK path` | Ghidra sem JDK | instale o Temurin 21 (JDK, não JRE) |
| `JAVA_HOME ... unsupported java version` | apontou para JRE ou JDK < 21 | aponte para o JDK 21 |
| import mostra `address not in memory` | faltam os blocos do GBA | seção 2.5 |
| código Thumb aparecendo como dados | linguagem errada | use `ARM:LE:32:v4t` (seção 2.4) |
| Ghidra muito lento / sem memória | ROM de 16 MB | aumente `-Xmx` em `support\analyzeHeadless.bat` ou analise por partes |

---

## 7. Referências

- Adoptium (JDK 21): <https://adoptium.net/temurin/releases/>
- Ghidra 12.1.4: <https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build>
- Node.js LTS: <https://nodejs.org>
- Guia do stack Linux: [`REA_GHIDRA.md`](REA_GHIDRA.md)
- Guia do importador: [`GHIDRA_IMPORT.md`](GHIDRA_IMPORT.md)
