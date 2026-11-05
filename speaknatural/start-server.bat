@echo off
rem ===========================================================================
rem  SpeakNatural - inicia o servidor local no Windows
rem  Basta dar DUPLO CLIQUE neste arquivo. Ele faz tudo:
rem    1. confere se o Python 3.11+ esta instalado
rem    2. cria o ambiente virtual (.venv) na primeira vez
rem    3. instala as dependencias (a primeira vez baixa ~2,5 GB: va tomar um cafe)
rem    4. mostra o IP do seu PC (use no celular)
rem    5. sobe o servidor em http://0.0.0.0:8000
rem  Observacao: os textos aqui sao sem acento de proposito, para nao quebrar
rem  em janelas de Prompt antigas do Windows.
rem ===========================================================================
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>nul
title SpeakNatural - servidor local
cd /d "%~dp0"

echo.
echo ==================================================
echo    SpeakNatural - servidor local de pronuncia
echo ==================================================
echo.

rem ------------------------------ 1. Python ---------------------------------
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    python --version >nul 2>nul
    if not errorlevel 1 (
        echo [ERRO] Seu Python e mais antigo que o 3.11.
        echo        Instale o Python 3.11 ou 3.12 em https://www.python.org/downloads/
        echo        IMPORTANTE: marque a caixa "Add python.exe to PATH" durante a instalacao.
        echo.
        pause
        exit /b 1
    )
    echo [ERRO] Python nao encontrado neste computador.
    echo.
    echo   1^) Baixe em https://www.python.org/downloads/
    echo   2^) Na instalacao, MARQUE "Add python.exe to PATH"
    echo   3^) Feche e abra de novo este arquivo
    echo.
    pause
    exit /b 1
)
for /f "delims=" %%v in ('%PY% -c "import platform;print(platform.python_version())"') do set "PYVER=%%v"
echo [ok] Python encontrado: %PYVER%

rem --------------------------- 2. Ambiente virtual ---------------------------
cd backend
if not exist ".venv\Scripts\python.exe" (
    echo [..] Criando o ambiente virtual pela primeira vez...
    %PY% -m venv .venv
    if errorlevel 1 goto :erro_venv
)
set "VENV_PY=.venv\Scripts\python.exe"

rem ---------------------------- 3. Dependencias -----------------------------
set "STAMP=.venv\requirements-instaladas.txt"
if exist "%STAMP%" (
    fc /b requirements.txt "%STAMP%" >nul 2>nul
    if not errorlevel 1 goto :deps_ok
)
echo.
echo [..] Instalando as dependencias do Python.
echo      AVISO: a primeira vez baixa cerca de 2,5 GB (PyTorch, faster-whisper...).
echo      Pode levar de 5 a 30 minutos dependendo da sua internet. Tenha paciencia.
echo.
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :erro_pip
copy /y requirements.txt "%STAMP%" >nul
:deps_ok
echo [ok] Dependencias prontas.

rem ------------------ 4. Programas externos (ffmpeg/espeak) -----------------
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo.
    echo [AVISO] O ffmpeg NAO foi encontrado no PATH.
    echo         O app funciona, mas a conversao de audio fica pior.
    echo         Instale com:  winget install Gyan.FFmpeg
    echo         (depois feche e abra este arquivo de novo)
)
where espeak-ng >nul 2>nul
if errorlevel 1 (
    echo.
    echo [AVISO] O espeak-ng NAO foi encontrado no PATH.
    echo         O app usa um dicionario interno de fonemas ^(um pouco menos preciso^).
    echo         Para instalar: baixe o .msi em https://github.com/espeak-ng/espeak-ng/releases
)

rem ------------------------------- 5. IP ------------------------------------
echo.
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } ^| Select-Object -ExpandProperty IPAddress) -join '  '"') do echo [info] IP deste PC na rede: %%i
echo [info] No celular, use:  http://IP-ACIMA:8000   ^(tela "Servidor" do app^)
echo.

rem ----------------------------- 6. Servidor --------------------------------
echo ==================================================
echo   Servidor no ar. NAO FECHE ESTA JANELA.
echo   No PC, abra:  http://localhost:8000
echo   Documentacao: http://localhost:8000/docs
echo   Para parar: feche esta janela ou aperte Ctrl+C
echo ==================================================
echo.
"%VENV_PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
echo [aviso] O servidor foi encerrado. Se isso nao foi voce, veja a mensagem acima.
pause
exit /b 0

:erro_venv
echo.
echo [ERRO] Nao consegui criar o ambiente virtual.
echo        Tente: apague a pasta backend\.venv e rode este arquivo de novo.
pause
exit /b 1

:erro_pip
echo.
echo [ERRO] A instalacao das dependencias falhou.
echo        Causas comuns: internet caiu, disco cheio ou Python sem permissao.
echo        Tente rodar de novo; se persistir, apague backend\.venv e repita.
pause
exit /b 1
