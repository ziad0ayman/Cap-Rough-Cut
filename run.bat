@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

if "%~1"=="" (
    echo ==========================================================
    echo 🎬 CapRoughCut - Automatic AI Video Rough Cut
    echo ==========================================================
    echo 1) Launch Web Interface (Recommended)
    echo 2) Run directly via Command Line
    set /p choice="Choose (1 or 2): "
    if "%choice%"=="2" (
        set /p videopath="Drag and drop your video file here and press Enter: "
        caproughcut "%videopath%" --mode studio
    ) else (
        python app.py
    )
) else (
    caproughcut %*
)
