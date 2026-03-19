@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"

set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment not found.
    echo Please run build\build.bat first.
    exit /b 1
)

set "PLATFORM=%~1"
if "%PLATFORM%"=="" set "PLATFORM=tiktok"

set "SCRAPER_MODE=%~2"
if "%SCRAPER_MODE%"=="" set "SCRAPER_MODE=live"

set "GAME_NAME=%~3"
if "%GAME_NAME%"=="" set "GAME_NAME=Whiteout Survival"

echo Running scraper with Postgres storage...
echo Platform: %PLATFORM%
echo Scraper mode: %SCRAPER_MODE%
echo Game name: %GAME_NAME%

echo Checking postgres connection and ensuring target database exists...
"%VENV_PYTHON%" init_postgres.py
if %errorlevel% neq 0 (
    exit /b %errorlevel%
)

"%VENV_PYTHON%" main.py --platform %PLATFORM% --scraper-mode %SCRAPER_MODE% --storage postgres --game-name "%GAME_NAME%"
exit /b %errorlevel%
