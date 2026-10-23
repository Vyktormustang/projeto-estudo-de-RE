<#
.SYNOPSIS
    Importa uma ROM de GBA no Ghidra (ARMv4T) já com o mapa de memória do GBA,
    cabeçalho validado, rótulos do projeto e seeds ARM/Thumb. Versão Windows do
    scripts/ghidra_import_gba.sh.

.DESCRIPTION
    Roda o analyzeHeadless.bat com:
      -processor ARM:LE:32:v4t
      -loader BinaryLoader -loader-baseAddr 0x08000000 -loader-blockName GBA_ROM
      -scriptPath scripts\ghidra_scripts
      -preScript  GbaPrepareProgram.java pre  <evidências>
      -postScript GbaPrepareProgram.java post <evidências>

    Antes de importar, valida o cabeçalho da ROM. Usa o script Python do projeto
    quando houver Python disponível (py/python); se não houver, faz uma
    validação mínima em PowerShell.

.PARAMETER Rom
    Caminho da ROM (.gba). Obrigatório.

.PARAMETER ProjectDir
    Onde criar o projeto Ghidra. Padrão: %LOCALAPPDATA%\re-tools\ghidra-projects

.PARAMETER EvidenceDir
    Onde gravar os JSONs/logs. Padrão: <repo>\reports\ghidra

.PARAMETER NoAnalysis
    Importa e roda os scripts sem auto-análise (rápido; bom para testar).

.PARAMETER Mirrors
    Também mapeia os mirrors de barramento 0x0A/0x0C/0x0E.

.PARAMETER Reuse
    Reabre o programa existente (-process) em vez de reimportar.

.PARAMETER AllowInvalidHeader
    Segue mesmo se o cabeçalho não validar (ROM hack/trim).

.PARAMETER DryRun
    Só mostra o comando.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\win\ghidra_import_gba.ps1 -Rom "C:\roms\FireRed.gba"

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\win\ghidra_import_gba.ps1 -Rom "C:\roms\FireRed.gba" -NoAnalysis

.NOTES
    Não foi executado no ambiente de desenvolvimento (Linux, sem PowerShell).
    A validação "de verdade" do cabeçalho vem do scripts/gba_rom_header.py
    (testado com --self-test); a validação em PowerShell é só um plano B.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Rom,
    [string]$ProjectDir = '',
    [string]$ProjectName = '',
    [string]$EvidenceDir = '',
    [int]$AnalysisTimeout = 1800,
    [switch]$NoAnalysis,
    [switch]$Mirrors,
    [switch]$Reuse,
    [switch]$AllowInvalidHeader,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# --- caminhos ---------------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$GhidraScripts = Join-Path $RepoRoot 'scripts\ghidra_scripts'
$HeaderScript  = Join-Path $RepoRoot 'scripts\gba_rom_header.py'

if (-not $ProjectDir)  { $ProjectDir = Join-Path $env:LOCALAPPDATA 're-tools\ghidra-projects' }
if (-not $EvidenceDir) { $EvidenceDir = Join-Path $RepoRoot 'reports\ghidra' }
if (-not $ProjectName) { $ProjectName = '' }

function Write-Step([string]$m) { Write-Host "[ghidra-import] $m" -ForegroundColor Cyan }
function Write-Warn2([string]$m){ Write-Host "[ghidra-import] AVISO: $m" -ForegroundColor Yellow }
function Fail([string]$m) { Write-Host "[ghidra-import] ERRO: $m" -ForegroundColor Red; exit 1 }

$RomFull = (Resolve-Path -LiteralPath $Rom -ErrorAction SilentlyContinue)
if (-not $RomFull) { Fail "ROM não encontrada: $Rom" }
$RomFull = $RomFull.Path
if (-not (Test-Path -LiteralPath $RomFull -PathType Leaf)) { Fail "não é um arquivo: $RomFull" }

$size = (Get-Item -LiteralPath $RomFull).Length
if ($size -le 0) { Fail "arquivo vazio: $RomFull" }
$sha = (Get-FileHash -LiteralPath $RomFull -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $ProjectName) { $ProjectName = "gba_$($sha.Substring(0,8))" }

# --- localizar Ghidra / Java ------------------------------------------------
$Ghidra = $env:GHIDRA_INSTALL_DIR
if (-not $Ghidra -or -not (Test-Path (Join-Path $Ghidra 'support\analyzeHeadless.bat'))) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 're-tools\ghidra_12.1.4_PUBLIC'),
        (Join-Path $env:USERPROFILE 're-tools\ghidra_12.1.4_PUBLIC')
    )
    $found = $candidates | Where-Object { Test-Path (Join-Path $_ 'support\analyzeHeadless.bat') } | Select-Object -First 1
    if (-not $found) {
        Fail "Ghidra não encontrado. Rode scripts\win\setup_re_tools.ps1 ou defina GHIDRA_INSTALL_DIR."
    }
    $Ghidra = $found
}
$Headless = Join-Path $Ghidra 'support\analyzeHeadless.bat'

if (-not $env:JAVA_HOME -or -not (Test-Path (Join-Path $env:JAVA_HOME 'bin\javac.exe'))) {
    Write-Warn2 "JAVA_HOME não aponta para um JDK completo (com javac). O analyzeHeadless pode falhar."
    Write-Warn2 "Rode scripts\win\setup_re_tools.ps1 ou defina JAVA_HOME para o JDK 21."
}

# --- 1) validação do cabeçalho ---------------------------------------------
function Find-Python {
    foreach ($candidate in @('py', 'python', 'python3')) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) { return $candidate }
    }
    return $null
}

function Test-HeaderWithPython([string]$Python) {
    $jsonPath = Join-Path $EvidenceDir 'rom_header.json'
    New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
    $args = @($HeaderScript, $RomFull, '--out', $jsonPath)
    if (-not $AllowInvalidHeader) { $args += '--require-valid' }
    if ($Python -eq 'py') { $args = @('-3') + $args }
    & $Python @args | Out-Host
    return ($LASTEXITCODE -eq 0)
}

function Test-HeaderFallback {
    Write-Warn2 'Python não encontrado: usando validação mínima em PowerShell'
    $bytes = [System.IO.File]::ReadAllBytes($RomFull)
    if ($bytes.Length -lt 0xC0) { return $false }

    $sum = 0
    for ($i = 0xA0; $i -le 0xBC; $i++) { $sum += [int]$bytes[$i] }
    $expected = (-($sum + 0x19)) -band 0xFF
    $stored = [int]$bytes[0xBD]
    $fixedOk = ([int]$bytes[0xB2] -eq 0x96)

    $title = -join ($bytes[0xA0..0xAB] | ForEach-Object {
        if ($_ -ge 0x20 -and $_ -lt 0x7F) { [char]$_ } else { '.' } })
    $word = [BitConverter]::ToUInt32($bytes, 0)
    $target = $null
    if (($word -shr 24) -eq 0xEA) {
        $imm = [int64]($word -band 0xFFFFFF)
        if (($imm -band 0x800000) -ne 0) { $imm -= 0x1000000 }
        $target = (0x08000000 + 8 + ($imm * 4)) -band 0xFFFFFFFF
    }

    Write-Host ("  título:      {0}" -f $title)
    Write-Host ("  byte 0xB2:   0x{0:X2} ({1})" -f $bytes[0xB2], $(if ($fixedOk) { 'OK' } else { 'FALHA' }))
    Write-Host ("  complemento: 0x{0:X2} (esperado 0x{1:X2}) -> {2}" -f $stored, $expected, $(if ($stored -eq $expected) { 'OK' } else { 'FALHA' }))
    if ($null -ne $target) {
        Write-Host ("  entrada:     0x{0:X8} -> 0x{1:X8}" -f $word, $target)
    } else {
        Write-Host ("  entrada:     0x{0:X8} (não é um B ARM)" -f $word)
    }
    return ($fixedOk -and ($stored -eq $expected) -and ($null -ne $target))
}

Write-Step "rom:     $RomFull ($size bytes, sha256 $($sha.Substring(0,16))...)"
Write-Step 'validando cabeçalho'
$python = Find-Python
if ($python) {
    if (-not (Test-HeaderWithPython $python)) {
        if ($AllowInvalidHeader) { Write-Warn2 'cabeçalho inválido; seguindo por causa de -AllowInvalidHeader' }
        else { Fail "cabeçalho inválido (use -AllowInvalidHeader se for intencional). Detalhes: $EvidenceDir\rom_header.json" }
    }
} else {
    if (-not (Test-HeaderFallback)) {
        if ($AllowInvalidHeader) { Write-Warn2 'cabeçalho inválido; seguindo por causa de -AllowInvalidHeader' }
        else { Fail 'cabeçalho inválido (use -AllowInvalidHeader se for intencional)' }
    }
}

# --- 2) comando do analyzeHeadless -----------------------------------------
New-Item -ItemType Directory -Force -Path $EvidenceDir, $ProjectDir | Out-Null

$programName = Split-Path -Leaf $RomFull
$cmdArgs = @($ProjectDir, $ProjectName)

if ($Reuse) {
    $cmdArgs += @('-process', $programName)
} else {
    $cmdArgs += @(
        '-import', $RomFull,
        '-processor', 'ARM:LE:32:v4t',
        '-loader', 'BinaryLoader',
        '-loader-baseAddr', '0x08000000',
        '-loader-blockName', 'GBA_ROM',
        '-overwrite'
    )
}

$preArgs = @('pre', $EvidenceDir)
if ($Mirrors) { $preArgs += '--mirrors' }

$cmdArgs += @(
    '-scriptPath', $GhidraScripts,
    '-preScript', 'GbaPrepareProgram.java'
) + $preArgs + @(
    '-postScript', 'GbaPrepareProgram.java', 'post', $EvidenceDir,
    '-analysisTimeoutPerFile', "$AnalysisTimeout",
    '-log', (Join-Path $EvidenceDir 'analyzeHeadless.log'),
    '-scriptlog', (Join-Path $EvidenceDir 'ghidra_scripts.log')
)
if ($NoAnalysis) { $cmdArgs += '-noanalysis' }
if ($env:NUMBER_OF_PROCESSORS) { $cmdArgs += @('-max-cpu', "$env:NUMBER_OF_PROCESSORS") }

Write-Step "projeto:    $ProjectDir\$ProjectName"
Write-Step "evidências: $EvidenceDir"
Write-Host 'COMANDO:'
Write-Host ("  `"{0}`" {1}" -f $Headless, (($cmdArgs | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }) -join ' '))

if ($DryRun) { Write-Step 'dry-run: nada foi importado'; exit 0 }

# --- 3) executar ------------------------------------------------------------
$start = Get-Date
& $Headless @cmdArgs 2>&1 | Tee-Object -FilePath (Join-Path $EvidenceDir 'analyzeHeadless.console.log') | Out-Host
$status = $LASTEXITCODE
$elapsed = [int]((Get-Date) - $start).TotalSeconds

if ($status -ne 0) {
    Write-Warn2 "analyzeHeadless terminou com código $status (veja $EvidenceDir\analyzeHeadless.console.log)"
    exit 1
}
Write-Step "analyzeHeadless OK em ${elapsed}s"

# --- 4) verificações de saída ----------------------------------------------
$preJson  = Join-Path $EvidenceDir 'gba_prepare_pre.json'
$postJson = Join-Path $EvidenceDir 'gba_prepare_post.json'
$failed = $false

if (-not (Test-Path $preJson)) { Write-Warn2 "pre-script não gerou $preJson"; $failed = $true }
if (-not (Test-Path $postJson)) { Write-Warn2 "post-script não gerou $postJson"; $failed = $true }

if (Test-Path $postJson) {
    try {
        $post = Get-Content -Raw -Path $postJson | ConvertFrom-Json
        $a = $post.analysis
        Write-Step ("funções: {0} | símbolos: {1} | refs (destino/fonte): {2}/{3}" -f `
            $a.function_count, $a.symbol_count, $a.reference_destination_count, $a.reference_source_count)
        if ($a.anchors_found) { Write-Step ("âncoras: " + ($a.anchors_found -join ', ')) }
        if ($a.anchors_missing) { Write-Warn2 ("âncoras ausentes: " + ($a.anchors_missing -join ', ')) }
    } catch {
        Write-Warn2 "não foi possível ler $postJson : $($_.Exception.Message)"
        $failed = $true
    }
}

if (Test-Path $preJson) {
    if ($python) {
        Write-Step 'cross-check do cabeçalho (Python x Ghidra)'
        $cmpArgs = @($HeaderScript, $RomFull, '--compare', $preJson)
        if ($python -eq 'py') { $cmpArgs = @('-3') + $cmpArgs }
        & $python @cmpArgs | Out-Host
        if ($LASTEXITCODE -ne 0) { $failed = $true }
    } else {
        Write-Warn2 'sem Python: cross-check do cabeçalho não executado'
    }
}

if ($failed) { exit 1 }

Write-Step 'IMPORT CONCLUÍDO'
Write-Host "  GUI:        `"$Ghidra\ghidraRun.bat`"  -> projeto $ProjectName"
Write-Host "  evidências: $EvidenceDir\{rom_header,gba_prepare_pre,gba_prepare_post}.json"
exit 0
