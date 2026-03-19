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

echo Running mock scraper...
echo Platform: %PLATFORM%

"%VENV_PYTHON%" main.py --platform %PLATFORM% --scraper-mode mock --storage memory
exit /b %errorlevel%

