@echo off
setlocal enabledelayedexpansion

REM One-click bootstrap for Ads Data Collector V1 on Windows

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"

cd /d "%PROJECT_ROOT%"

echo [1/7] Project root: %PROJECT_ROOT%

where py >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python launcher "py" was not found.
    echo Please install Python 3.10+ and make sure the launcher is available.
    exit /b 1
)

echo [2/7] Creating virtual environment...
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo Virtual environment already exists. Reusing it.
)

set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"

echo [3/7] Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [ERROR] Failed to upgrade pip.
    exit /b 1
)

echo [4/7] Installing Python dependencies...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    exit /b 1
)

echo [5/7] Installing Playwright browser...
"%VENV_PYTHON%" -m playwright install chromium
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Playwright Chromium browser.
    exit /b 1
)

echo [6/7] Creating runtime directories...
if not exist "logs" mkdir logs
if not exist "build\output" mkdir build\output

echo [7/7] Running smoke tests...
"%VENV_PYTHON%" -m pytest -q
if %errorlevel% neq 0 (
    echo [ERROR] Smoke tests failed.
    exit /b 1
)

echo.
echo [SUCCESS] Deployment bootstrap completed.
echo.
echo Activate venv:
echo     .venv\Scripts\activate
echo.
echo Run mock mode:
echo     python main.py --platform tiktok --scraper-mode mock --storage memory
echo.
echo Run TikTok live mode:
echo     python main.py --platform tiktok --scraper-mode live --storage memory --game-name "Whiteout Survival"
echo.
echo Run Facebook live mode:
echo     python main.py --platform facebook --scraper-mode live --storage memory --game-name "Whiteout Survival"

exit /b 0
