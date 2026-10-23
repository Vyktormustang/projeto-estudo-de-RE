#Requires -Version 5.1
<#
.SYNOPSIS
    Compila a pokeemerald-expansion (todos os Pokémon Gen 1-9) no Windows.

.DESCRIPTION
    Baixa o código-fonte oficial, confere o toolchain ARM, liga o menu de debug
    e compila o .gba. Não distribui ROM nem assets: o resultado fica na sua
    máquina.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\win\build-expansion.ps1
#>
[CmdletBinding()]
param(
    [string]$Destino = "$env:USERPROFILE\pokeemerald-expansion",
    [int]$Jobs = 0,
    [switch]$SemDebug
)

$ErrorActionPreference = "Stop"
function Info($m) { Write-Host "[ok]  $m" -ForegroundColor Green }
function Passo($m) { Write-Host "[..]  $m" -ForegroundColor Cyan }
function Falha($m) { Write-Host "[!!]  $m" -ForegroundColor Red; exit 1 }

Write-Host "=== pokeemerald-expansion: build para Windows ===" -ForegroundColor White

# 1) Toolchain
Passo "Conferindo o toolchain ARM (devkitPro)..."
$gcc = Get-Command arm-none-eabi-gcc -ErrorAction SilentlyContinue
if (-not $gcc) {
    Falha @"
arm-none-eabi-gcc nao encontrado no PATH.

Instale o devkitPro (GBA Development):
  https://github.com/devkitPro/installer/releases
Depois abra o terminal 'MSYS2' do devkitPro e rode:
  pacman -Syu
  pacman -S git make python gcc
E acrescente ao PATH do Windows:
  C:\devkitPro\msys2\usr\bin
  C:\devkitPro\tools\bin
"@
}
Info "arm-none-eabi-gcc: $((& arm-none-eabi-gcc --version | Select-Object -First 1))"

$make = Get-Command make -ErrorAction SilentlyContinue
if (-not $make) { Falha "make nao encontrado. No MSYS2: pacman -S make" }
Info "make: $(& make --version | Select-Object -First 1)"

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { Falha "git nao encontrado. Instale o Git for Windows ou use 'pacman -S git'." }

# 2) Codigo-fonte
if (Test-Path (Join-Path $Destino ".git")) {
    Info "repositorio ja existe: $Destino"
    Passo "Atualizando (git pull)..."
    Push-Location $Destino
    & git pull --ff-only
    Pop-Location
} else {
    Passo "Clonando rh-hideout/pokeemerald-expansion em $Destino ..."
    & git clone --depth 1 https://github.com/rh-hideout/pokeemerald-expansion.git $Destino
    if ($LASTEXITCODE -ne 0) { Falha "git clone falhou." }
    Info "clonado"
}

Push-Location $Destino
try {
    # 3) Configuracoes do projeto (Gen 1-9 + menu de debug)
    Passo "Aplicando configuracoes (Gen 1-9, menu de debug)..."
    $cfg = Join-Path $PSScriptRoot "..\expansion\aplicar_configs.py"
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        & python $cfg --raiz .
        if ($LASTEXITCODE -ne 0) { Write-Host "[aviso] configuracao parcial" -ForegroundColor Yellow }
    } else {
        Write-Host "[aviso] python ausente; pulando ajuste fino de configs" -ForegroundColor Yellow
    }

    # 4) Build
    if ($Jobs -le 0) { $Jobs = [Environment]::ProcessorCount }
    $alvo = "modern"
    $extra = @()
    if (-not $SemDebug) { $extra += "DEBUG=1" }

    Passo "Compilando: make $alvo -j$Jobs $($extra -join ' ')  (pode levar 10-30 min)"
    & make $alvo "-j$Jobs" @extra
    if ($LASTEXITCODE -ne 0) { Falha "build falhou (veja as mensagens acima)." }

    $rom = Join-Path $Destino "pokeemerald.gba"
    if (-not (Test-Path $rom)) { Falha "o build terminou sem gerar pokeemerald.gba" }

    $info = Get-Item $rom
    Info ("ROM pronta: {0} ({1:N1} MB)" -f $info.FullName, ($info.Length / 1MB))
    Write-Host ""
    Write-Host "Abra no mGBA e comece um jogo novo." -ForegroundColor White
    if (-not $SemDebug) {
        Write-Host "Menu de debug: no menu inicial pressione SELECT (dar Pokemon/item)." -ForegroundColor White
    }
}
finally {
    Pop-Location
}
