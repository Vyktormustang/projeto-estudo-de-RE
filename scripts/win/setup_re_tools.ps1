<#
.SYNOPSIS
    Prepara as ferramentas de RE do projeto no Windows (PowerShell):
    Eclipse Temurin JDK 21 + Ghidra 12.1.4 PUBLIC + REA (rea-agents 6.7.0).

.DESCRIPTION
    Equivalente ao scripts/setup_re_tools.sh (que só roda em Linux/macOS).

    O que ele faz:
      1. JDK 21 (Temurin)  -> via winget; se não houver winget, baixa da API
                              oficial da Adoptium (com conferência de SHA-256).
      2. Ghidra 12.1.4     -> zip oficial da NSA, SHA-256 fixo conferido.
      3. REA 6.7.0         -> npm install -g rea-agents@6.7.0.
      4. Variáveis de usuário: JAVA_HOME, GHIDRA_INSTALL_DIR e PATH.
      5. Verificação final (java, javac, ghidra, rea, rea doctor).

    Nada é instalado dentro do repositório. Tudo fica em %LOCALAPPDATA%\re-tools
    (ou no -Prefix que você passar).

.PARAMETER Prefix
    Pasta de instalação. Padrão: %LOCALAPPDATA%\re-tools

.PARAMETER JdkHome
    Use um JDK 21 já instalado (ex.: "C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot").

.PARAMETER GhidraDir
    Use um Ghidra 12.1.x já extraído.

.PARAMETER GhidraZip
    Use um zip oficial do Ghidra já baixado (o SHA-256 continua sendo conferido).

.PARAMETER SkipRea / SkipJdk / SkipGhidra
    Pula etapas.

.PARAMETER VerifyOnly
    Não instala nada; só roda as verificações.

.PARAMETER DryRun
    Mostra o plano sem baixar/instalar nada.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\win\setup_re_tools.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\win\setup_re_tools.ps1 -VerifyOnly

.NOTES
    Requisitos: Windows 10/11 x64, PowerShell 5.1+, Node.js 22.19+/24.11+/26+,
    curl ou Invoke-WebRequest, ~1,5 GB livres.

    Este script NÃO foi executado no ambiente de desenvolvimento do projeto
    (Linux, sem PowerShell). A lógica foi revisada à mão e a validação de
    cabeçalho reaproveita scripts/gba_rom_header.py (testado com --self-test).
#>
[CmdletBinding()]
param(
    [string]$Prefix = (Join-Path $env:LOCALAPPDATA 're-tools'),
    [string]$JdkHome = '',
    [string]$GhidraDir = '',
    [string]$GhidraZip = '',
    [switch]$SkipRea,
    [switch]$SkipJdk,
    [switch]$SkipGhidra,
    [switch]$VerifyOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# --- versões fixadas (as mesmas do script Linux) ----------------------------
$ReaVersion       = '6.7.0'
$GhidraVersion    = '12.1.4'
$GhidraDirName    = "ghidra_${GhidraVersion}_PUBLIC"
$GhidraZipName    = "ghidra_${GhidraVersion}_PUBLIC_20260921.zip"
$GhidraUrl        = "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GhidraVersion}_build/$GhidraZipName"
$GhidraSha256     = 'ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db'
$JdkMajor         = 21
$AdoptiumApiList  = 'https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jdk&os=windows&vendor=eclipse'

$script:Failures = 0
$script:CacheDir = Join-Path $Prefix '.cache'

# --- saída ------------------------------------------------------------------
function Write-Step([string]$Message) { Write-Host "[setup-re] $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message)   { Write-Host "  [ OK   ] $Message" -ForegroundColor Green }
function Write-Warn2([string]$Message){ Write-Host "  [AVISO ] $Message" -ForegroundColor Yellow; $script:Failures++ }
function Write-Bad([string]$Message)  { Write-Host "  [FALHA ] $Message" -ForegroundColor Red; $script:Failures++ }

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-Download([string]$Url, [string]$Path) {
    if ((Test-Path $Path) -and ((Get-Item $Path).Length -gt 0)) {
        Write-Step "cache: $Path"
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) | Out-Null
    Write-Step "baixando: $Url"
    if ($DryRun) { Write-Step "[dry-run] salvaria em $Path"; return }
    $tmp = "$Path.part"
    if ($PSVersionTable.PSVersion.Major -lt 6) {
        Invoke-WebRequest -Uri $Url -OutFile $tmp -UseBasicParsing
    } else {
        Invoke-WebRequest -Uri $Url -OutFile $tmp
    }
    Move-Item -Force $tmp $Path
}

function Assert-Sha256([string]$Path, [string]$Expected, [string]$Label) {
    if ($DryRun) { Write-Step "[dry-run] conferiria SHA-256 de $Path"; return }
    $actual = (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected.ToLowerInvariant()) {
        throw "$Label`: SHA-256 divergente.`n  esperado: $Expected`n  obtido:   $actual`n  arquivo:  $Path`nApague o arquivo e baixe de novo da fonte oficial."
    }
    Write-Step "$Label`: SHA-256 confere"
}

function Test-Jdk([string]$Home) {
    if ([string]::IsNullOrWhiteSpace($Home)) { return $false }
    return (Test-Path (Join-Path $Home 'bin\javac.exe')) -and (Test-Path (Join-Path $Home 'bin\java.exe'))
}

function Test-Ghidra([string]$Dir) {
    if ([string]::IsNullOrWhiteSpace($Dir)) { return $false }
    return (Test-Path (Join-Path $Dir 'Ghidra\application.properties')) -and
           (Test-Path (Join-Path $Dir 'support\analyzeHeadless.bat'))
}

function Get-GhidraVersion([string]$Dir) {
    $props = Join-Path $Dir 'Ghidra\application.properties'
    if (-not (Test-Path $props)) { return 'ausente' }
    $line = Select-String -Path $props -Pattern '^application\.version=' | Select-Object -First 1
    if (-not $line) { return 'desconhecido' }
    return ($line.Line -split '=', 2)[1].Trim()
}

# --- JDK --------------------------------------------------------------------
function Find-WingetJdk {
    $roots = @(
        'C:\Program Files\Eclipse Adoptium',
        'C:\Program Files\Eclipse Foundation',
        'C:\Program Files\Microsoft\jdk'
    )
    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        $candidate = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-Jdk $_.FullName } |
            Sort-Object Name -Descending |
            Select-Object -First 1
        if ($candidate) { return $candidate.FullName }
    }
    return $null
}

function Install-Jdk {
    if ($JdkHome -and (Test-Jdk $JdkHome)) { Write-Step "usando -JdkHome: $JdkHome"; return $JdkHome }
    if (Test-Jdk $env:JAVA_HOME)           { Write-Step "usando JAVA_HOME atual: $env:JAVA_HOME"; return $env:JAVA_HOME }

    if ($DryRun) {
        Write-Step "[dry-run] instalaria o Temurin JDK $JdkMajor (winget ou Adoptium)"
        return $null
    }

    if (Test-Command 'winget') {
        Write-Step "instalando Temurin JDK $JdkMajor via winget"
        try {
            & winget install --exact --id EclipseAdoptium.Temurin.21.JDK `
                --accept-source-agreements --accept-package-agreements --silent | Out-Host
        } catch {
            Write-Warn2 "winget falhou: $($_.Exception.Message)"
        }
        $found = Find-WingetJdk
        if ($found) { return $found }
        Write-Warn2 "winget não instalou/encontrou o JDK; tentando download direto"
    }

    # Fallback: API oficial da Adoptium (binário + checksum no mesmo JSON)
    try {
        $list = Invoke-RestMethod -Uri $AdoptiumApiList -Headers @{ 'User-Agent' = 'gba-re-setup' }
        $asset = $list | Select-Object -First 1
        if (-not $asset) { throw 'API da Adoptium não retornou pacotes' }
        $url = $asset.binary.package.link
        $sha = $asset.binary.package.checksum
        $file = Join-Path $script:CacheDir ([System.IO.Path]::GetFileName($url))
        Invoke-Download $url $file
        Assert-Sha256 $file $sha "Temurin JDK"
        $target = Join-Path $Prefix ("jdk-" + ($asset.release_name -replace '[^\w\.\-]', '_'))
        Write-Step "extraindo JDK em $target"
        if (Test-Path $target) { Remove-Item -Recurse -Force $target }
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Expand-Archive -Path $file -DestinationPath $target -Force
        $inner = Get-ChildItem -Path $target -Directory | Select-Object -First 1
        if ($inner -and (Test-Jdk $inner.FullName)) { return $inner.FullName }
        if (Test-Jdk $target) { return $target }
        throw "zip do JDK extraído, mas bin\javac.exe não apareceu"
    } catch {
        Write-Warn2 "download do JDK falhou: $($_.Exception.Message)"
        Write-Host "    Baixe manualmente em https://adoptium.net/temurin/releases/?os=windows&version=21&package=jdk" -ForegroundColor Yellow
        Write-Host "    e rode de novo com: -JdkHome `"C:\caminho\jdk-21...`"" -ForegroundColor Yellow
        return $null
    }
}

# --- Ghidra -----------------------------------------------------------------
function Install-Ghidra {
    if ($GhidraDir) {
        if (-not (Test-Ghidra $GhidraDir)) { throw "-GhidraDir $GhidraDir não parece uma instalação do Ghidra (falta support\analyzeHeadless.bat)" }
        Write-Step "usando -GhidraDir: $GhidraDir"
        return $GhidraDir
    }
    if (Test-Ghidra $env:GHIDRA_INSTALL_DIR) {
        Write-Step "usando GHIDRA_INSTALL_DIR atual: $env:GHIDRA_INSTALL_DIR"
        return $env:GHIDRA_INSTALL_DIR
    }

    $dir = Join-Path $Prefix $GhidraDirName
    if (Test-Ghidra $dir) { Write-Step "Ghidra já instalado: $dir"; return $dir }

    if ($DryRun) {
        Write-Step "[dry-run] baixaria $GhidraUrl e extrairia em $Prefix"
        return $dir
    }

    $zip = if ($GhidraZip) { $GhidraZip } else { Join-Path $script:CacheDir $GhidraZipName }
    if (-not $GhidraZip) { Invoke-Download $GhidraUrl $zip }
    Assert-Sha256 $zip $GhidraSha256 "Ghidra $GhidraVersion"

    Write-Step "extraindo Ghidra em $Prefix"
    New-Item -ItemType Directory -Force -Path $Prefix | Out-Null
    Expand-Archive -Path $zip -DestinationPath $Prefix -Force
    if (-not (Test-Ghidra $dir)) { throw "extração não produziu $dir" }
    return $dir
}

# --- REA --------------------------------------------------------------------
function Install-Rea {
    if (Test-Command 'rea') {
        $current = (& rea --version) 2>$null
        if ($current -eq $ReaVersion) { Write-Step "REA já instalado: $current"; return }
        Write-Step "REA em versão diferente ($current); instalando $ReaVersion"
    }
    if (-not (Test-Command 'npm')) { throw "npm não encontrado. Instale o Node.js 22 LTS (https://nodejs.org) e rode de novo." }
    if ($DryRun) { Write-Step "[dry-run] npm install -g rea-agents@$ReaVersion"; return }

    Write-Step "instalando rea-agents@$ReaVersion"
    & npm install --global "rea-agents@$ReaVersion" | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "npm falhou com código $LASTEXITCODE" }
}

# --- variáveis de ambiente --------------------------------------------------
function Set-EnvVar([string]$Name, [string]$Value) {
    if ($DryRun) { Write-Step "[dry-run] definiria $Name=$Value"; return }
    [Environment]::SetEnvironmentVariable($Name, $Value, 'User')
    Set-Item -Path "Env:$Name" -Value $Value
    Write-Step "$Name = $Value"
}

function Add-ToUserPath([string]$Dir) {
    if ($DryRun) { Write-Step "[dry-run] adicionaria $Dir ao PATH"; return }
    $current = [Environment]::GetEnvironmentVariable('Path', 'User')
    $parts = @()
    if ($current) { $parts = $current -split ';' | Where-Object { $_ } }
    if ($parts -notcontains $Dir) {
        $new = (@($parts) + $Dir) -join ';'
        [Environment]::SetEnvironmentVariable('Path', $new, 'User')
        Write-Step "PATH (usuário) += $Dir"
    }
    if (($env:Path -split ';') -notcontains $Dir) { $env:Path = "$env:Path;$Dir" }
}

# --- verificação ------------------------------------------------------------
function Test-ReaDoctor([string]$Ghidra) {
    if (-not (Test-Command 'rea')) { Write-Bad "comando rea não encontrado no PATH"; return }
    try {
        $json = & rea doctor --provider ghidra --json 2>$null | Out-String
        $doc = $json | ConvertFrom-Json
        $prov = $doc.providerInspections | Where-Object { $_.id -eq 'ghidra' } | Select-Object -First 1
        if ($prov -and $prov.available) {
            Write-Ok "rea doctor: provider ghidra disponível (versão $($prov.providerVersion))"
        } else {
            Write-Bad "rea doctor: provider ghidra indisponível"
            foreach ($check in ($prov.checks | Where-Object { -not $_.ok })) {
                Write-Host "           $($check.name): $($check.detail)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Warn2 "não foi possível interpretar o rea doctor: $($_.Exception.Message)"
    }
}

function Invoke-Verify([string]$Jdk, [string]$Ghidra) {
    Write-Step "== verificação =="
    if (Test-Jdk $Jdk) {
        Write-Ok "javac: $((& (Join-Path $Jdk 'bin\javac.exe') -version) 2>&1)"
    } else {
        Write-Bad "JDK completo (com javac) não encontrado"
    }
    if (Test-Ghidra $Ghidra) {
        $version = Get-GhidraVersion $Ghidra
        Write-Ok "Ghidra $version em $Ghidra"
        if ($version -like '12.1.*') { Write-Ok "série 12.1.x (aceita pelo REA 6.7.0)" }
        else { Write-Bad "Ghidra $version fora da série 12.1.x" }
        if (Test-Path (Join-Path $Ghidra 'Ghidra\Features\Decompiler\os\win_x86_64\decompile.exe')) {
            Write-Ok "decompilador nativo Windows presente"
        } else {
            Write-Warn2 "decompilador nativo Windows não encontrado (instalação incompleta?)"
        }
    } else {
        Write-Bad "Ghidra não encontrado"
    }
    if (Test-Command 'rea') {
        Write-Ok "rea $((& rea --version) 2>$null)"
        Test-ReaDoctor $Ghidra
    } else {
        Write-Bad "comando rea não encontrado (feche e abra o terminal de novo após instalar)"
    }
}

# --- main -------------------------------------------------------------------
Write-Host ''
Write-Host '=== Preparação das ferramentas de RE (REA + Ghidra) — Windows ===' -ForegroundColor Cyan
Write-Step "destino: $Prefix"
if ($DryRun) { Write-Step 'modo dry-run: nada será baixado/instalado' }

if (-not $VerifyOnly) {
    if (-not $SkipJdk) {
        Write-Step '== JDK 21 (Temurin) =='
        $jdk = Install-Jdk
    }
    if (-not $SkipGhidra) {
        Write-Step '== Ghidra 12.1.4 =='
        $ghidra = Install-Ghidra
    }
    if (-not $SkipRea) {
        Write-Step '== REA 6.7.0 =='
        Install-Rea
    }
}

$jdkFinal = if ($jdk) { $jdk } elseif (Test-Jdk $JdkHome) { $JdkHome } elseif (Test-Jdk $env:JAVA_HOME) { $env:JAVA_HOME } else { $null }
$ghidraFinal = if ($ghidra) { $ghidra } elseif ($GhidraDir) { $GhidraDir } elseif (Test-Ghidra $env:GHIDRA_INSTALL_DIR) { $env:GHIDRA_INSTALL_DIR } else { Join-Path $Prefix $GhidraDirName }

if (-not $VerifyOnly -and -not $DryRun) {
    Write-Step '== variáveis de ambiente do usuário =='
    if ($jdkFinal) { Set-EnvVar 'JAVA_HOME' $jdkFinal; Add-ToUserPath (Join-Path $jdkFinal 'bin') }
    if (Test-Ghidra $ghidraFinal) { Set-EnvVar 'GHIDRA_INSTALL_DIR' $ghidraFinal; Add-ToUserPath (Join-Path $ghidraFinal 'support') }
}

Invoke-Verify $jdkFinal $ghidraFinal

Write-Host ''
if ($script:Failures -eq 0) {
    Write-Host 'RESULTADO: stack pronto.' -ForegroundColor Green
} else {
    Write-Host "RESULTADO: $($script:Failures) pendência(s)." -ForegroundColor Yellow
}
Write-Host ''
Write-Host 'Próximos passos:'
Write-Host '  1) FECHE e abra um novo PowerShell (para pegar JAVA_HOME/PATH).'
Write-Host '  2) bash scripts/ghidra_import_gba.sh ...  -> no Windows use:'
Write-Host '     powershell -ExecutionPolicy Bypass -File scripts\win\ghidra_import_gba.ps1 -Rom "C:\caminho\sua_rom.gba"'
Write-Host '  3) GUI do Ghidra:'
Write-Host "     `"$ghidraFinal\ghidraRun.bat`""
Write-Host ''
Write-Host 'Atenção: no Windows o REA fala com o Ghidra em modo P0 (somente leitura) e'
Write-Host 'NÃO aceita raw-binary ARM. Para o fluxo REA+Ghida com ROM de GBA, use WSL'
Write-Host '(veja docs\WINDOWS.md).'

if ($script:Failures -gt 0) { exit 1 }
exit 0
