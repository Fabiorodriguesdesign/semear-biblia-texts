@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo SEMEAR BIBLIA - REGERAR PT EM UTF-8
echo.
echo Este processo vai substituir somente:
echo   pt\extras\JUB
echo   pt\extras\1EN
echo.
echo TOM nao sera alterado.
echo.

py -3.12 REGERAR_PT_UTF8.py "%~dp0."

if errorlevel 1 (
    echo.
    echo ERRO. Envie um print desta janela.
    pause
    exit /b 1
)

echo.
echo Textos PT regenerados corretamente em UTF-8.
echo Volte ao GitHub Desktop para fazer o commit.
pause
