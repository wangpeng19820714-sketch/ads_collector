@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"
set "PLAYWRIGHT_BROWSERS_PATH=%LocalAppData%\ms-playwright"
for /d %%D in ("%PLAYWRIGHT_BROWSERS_PATH%\chromium-*") do (
    if exist "%%~fD\chrome-win64\chrome.exe" goto :browser_ready
)
set "PLAYWRIGHT_BROWSERS_PATH=%PROJECT_ROOT%\.playwright-browsers"
:browser_ready

set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment not found.
    echo Please run build\build.bat first.
    exit /b 1
)

set "GAME_NAME=%~1"
if "%GAME_NAME%"=="" set "GAME_NAME=Whiteout Survival"

echo Running TikTok live scraper...
echo Game name: %GAME_NAME%

"%VENV_PYTHON%" main.py --platform tiktok --scraper-mode live --storage memory --game-name "%GAME_NAME%"
exit /b %errorlevel%

