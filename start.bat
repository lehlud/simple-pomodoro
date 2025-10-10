@echo off
setlocal enabledelayedexpansion

REM Set DIR to the folder containing this script
set "DIR=%~dp0"
REM Remove trailing backslash if present
if "%DIR:~-1%"=="\" set "DIR=%DIR:~0,-1%"

REM Check for required commands
set "missing="
for %%C in (python powershell) do (
    where %%C >nul 2>&1
    if errorlevel 1 (
        echo %%C is required to run this script
        set "missing=1"
    )
)
if defined missing (
    exit /b 1
)

REM Set up virtual environment if it doesn't exist
if not exist "%DIR%\venv\" (
    python -m venv "%DIR%\venv"
    "%DIR%\venv\Scripts\python.exe" -m pip install art windows-curses
    echo.
)

REM Run the Python script with all passed arguments
"%DIR%\venv\Scripts\python.exe" "%DIR%\start.py" %*

