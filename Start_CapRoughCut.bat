@echo off
chcp 65001 >nul
title CapRoughCut - Automatic Rough Cut

cd /d "%~dp0"

echo ==========================================================
echo 🎬 CapRoughCut - Automatic AI Video Rough Cut Generator
echo ==========================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment not detected in .venv or venv.
    echo Trying system python...
)

echo Starting CapRoughCut Web UI...
python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] An error occurred while running CapRoughCut.
    pause
)
