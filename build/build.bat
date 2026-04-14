@echo off
setlocal enabledelayedexpansion

REM One-click bootstrap for Ads Data Collector V1 on Windows

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"

cd /d "%PROJECT_ROOT%"

set "PIP_NO_INDEX="
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "ALL_PROXY="
set "GIT_HTTP_PROXY="
set "GIT_HTTPS_PROXY="
set "PLAYWRIGHT_LOCAL_BROWSERS_PATH=%PROJECT_ROOT%\.playwright-browsers"
set "PLAYWRIGHT_DEFAULT_BROWSERS_PATH=%LocalAppData%\ms-playwright"
set "PLAYWRIGHT_BROWSERS_PATH=%PLAYWRIGHT_LOCAL_BROWSERS_PATH%"
set "PLAYWRIGHT_BROWSER_READY="

echo [1/7] Project root: %PROJECT_ROOT%

set "PYTHON_BOOTSTRAP="
set "PYTHON_BOOTSTRAP_ARGS="
set "ENSUREPIP_BUNDLE_DIR="

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_BOOTSTRAP=py"
    set "PYTHON_BOOTSTRAP_ARGS=-3"
)

if not defined PYTHON_BOOTSTRAP (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        python --version >nul 2>nul
        if %errorlevel% equ 0 (
            set "PYTHON_BOOTSTRAP=python"
        )
    )
)

if not defined PYTHON_BOOTSTRAP if exist "C:\Program Files\Lenovo\Lenovo.PFMService\app\nlpService\Python\Python310\python.exe" (
    set "PYTHON_BOOTSTRAP=C:\Program Files\Lenovo\Lenovo.PFMService\app\nlpService\Python\Python310\python.exe"
)

if not defined PYTHON_BOOTSTRAP if exist "C:\Program Files\Lenovo\Lenovo.PFMService\app\nlpService\Python\Python312\python.exe" (
    set "PYTHON_BOOTSTRAP=C:\Program Files\Lenovo\Lenovo.PFMService\app\nlpService\Python\Python312\python.exe"
)

if not defined PYTHON_BOOTSTRAP (
    echo [ERROR] No usable Python runtime was found.
    echo Install Python 3.10+ or add it to PATH, then rerun this script.
    exit /b 1
)

for /f "usebackq delims=" %%I in (`call "%PYTHON_BOOTSTRAP%" %PYTHON_BOOTSTRAP_ARGS% -c "import ensurepip, pathlib; print(pathlib.Path(ensurepip.__file__).resolve().parent / '_bundled')"`) do set "ENSUREPIP_BUNDLE_DIR=%%I"
if not defined ENSUREPIP_BUNDLE_DIR (
    echo [ERROR] Could not locate the bundled ensurepip wheels.
    exit /b 1
)

echo Using Python bootstrap: %PYTHON_BOOTSTRAP% %PYTHON_BOOTSTRAP_ARGS%

for /d %%D in ("%PLAYWRIGHT_DEFAULT_BROWSERS_PATH%\chromium-*") do (
    if exist "%%~fD\chrome-win64\chrome.exe" (
        set "PLAYWRIGHT_BROWSERS_PATH=%PLAYWRIGHT_DEFAULT_BROWSERS_PATH%"
        set "PLAYWRIGHT_BROWSER_READY=1"
    )
)

if not defined PLAYWRIGHT_BROWSER_READY (
    for /d %%D in ("%PLAYWRIGHT_LOCAL_BROWSERS_PATH%\chromium-*") do (
        if exist "%%~fD\chrome-win64\chrome.exe" (
            set "PLAYWRIGHT_BROWSERS_PATH=%PLAYWRIGHT_LOCAL_BROWSERS_PATH%"
            set "PLAYWRIGHT_BROWSER_READY=1"
        )
    )
)

echo [2/7] Creating virtual environment...
if not exist ".venv\Scripts\python.exe" (
    call "%PYTHON_BOOTSTRAP%" %PYTHON_BOOTSTRAP_ARGS% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo Virtual environment already exists. Reusing it.
    ".venv\Scripts\python.exe" -m pip --version >nul 2>nul
    if %errorlevel% neq 0 (
        echo Existing virtual environment is missing pip. Recreating it...
        rmdir /s /q ".venv"
        call "%PYTHON_BOOTSTRAP%" %PYTHON_BOOTSTRAP_ARGS% -m venv .venv
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to recreate virtual environment.
            exit /b 1
        )
    )
)

set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"

echo [3/7] Checking pip...
".venv\Scripts\python.exe" -m pip --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Virtual environment pip is missing. Bootstrapping pip...
    call "%PYTHON_BOOTSTRAP%" %PYTHON_BOOTSTRAP_ARGS% -m pip --python ".venv" install --no-index --find-links "%ENSUREPIP_BUNDLE_DIR%" pip setuptools
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to bootstrap pip into the virtual environment.
        exit /b 1
    )
)
"%VENV_PYTHON%" -m pip --version
if %errorlevel% neq 0 (
    echo [ERROR] Pip is still unavailable after bootstrap.
    exit /b 1
)

echo [4/7] Installing Python dependencies...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    exit /b 1
)

echo [5/7] Installing Playwright browser...
if defined PLAYWRIGHT_BROWSER_READY (
    echo Reusing existing Playwright browser from %PLAYWRIGHT_BROWSERS_PATH%
) else (
    "%VENV_PYTHON%" -m playwright install chromium
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Playwright Chromium browser.
        exit /b 1
    )
)

echo [6/7] Creating runtime directories...
if not exist "logs" mkdir logs
if not exist "build\output" mkdir build\output
if not exist "%PLAYWRIGHT_LOCAL_BROWSERS_PATH%" mkdir "%PLAYWRIGHT_LOCAL_BROWSERS_PATH%"

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
