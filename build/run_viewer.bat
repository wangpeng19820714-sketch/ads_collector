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

set "ADS_VIEWER_HOST=127.0.0.1"
set "ADS_VIEWER_PORT=8787"

echo Starting Ads Viewer at http://%ADS_VIEWER_HOST%:%ADS_VIEWER_PORT% ...
"%VENV_PYTHON%" dashboard.py
exit /b %errorlevel%

