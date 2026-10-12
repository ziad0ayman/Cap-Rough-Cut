@echo off
chcp 65001 >nul
title CapRoughCut - Windows Setup

cd /d "%~dp0"

echo ==========================================================
echo 🚀 Installing CapRoughCut for Windows...
echo ==========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10 or newer from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

echo 1. Creating Python virtual environment (.venv)...
python -m venv .venv

echo 2. Activating virtual environment...
call .venv\Scripts\activate.bat

echo 3. Upgrading pip...
python -m pip install --upgrade pip

echo 4. Installing dependencies...
pip install -r requirements.txt

echo 5. Installing CapRoughCut in editable mode...
pip install -e .

if not exist ".env" (
    if exist ".env.example" (
        echo 6. Creating initial .env configuration...
        copy .env.example .env >nul
    )
)

echo.
echo ==========================================================
echo ✅ Setup complete!
echo You can now double-click "Start_CapRoughCut.bat" to run the app.
echo Don't forget to put your GEMINI_API_KEY inside the .env file!
echo ==========================================================
pause
