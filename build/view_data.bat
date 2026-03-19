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

set "LIMIT=%~1"
if "%LIMIT%"=="" set "LIMIT=20"

echo Viewing latest %LIMIT% records from Postgres...
"%VENV_PYTHON%" view_data.py --limit %LIMIT%
exit /b %errorlevel%

